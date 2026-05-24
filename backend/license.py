"""
Spevino LP-OS License Manager
Handles subscription validation, grace periods, and system kill-switch.
If subscription is not paid → system pauses CV detections and SMS alerts.
"""

import os
import json
import time
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Config
GRACE_PERIOD_DAYS = 14  # Free trial / grace period after expiry
CHECK_INTERVAL_HOURS = 24  # How often to re-check license
LICENSE_SECRET = os.getenv("LICENSE_SECRET", "spevino-lpos-default-secret-change-me")

class LicenseStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    GRACE = "grace"
    INVALID = "invalid"
    DISABLED = "disabled"

class LicenseManager:
    """
    Manages software licensing for the Spevino LP-OS.
    
    License format: spevino-XXXX-XXXX-XXXX-XXXX
    Each license has: customer, max_stores, max_cameras, expiry_date, features
    """
    
    def __init__(self):
        self._status = LicenseStatus.DISABLED
        self._license_data: Optional[Dict] = None
        self._installed_at: Optional[datetime] = None
        self._last_check: Optional[datetime] = None
        
        # Load persisted state
        self._load_state()
        
        # Validate on startup
        self.validate()
    
    def _get_state_path(self) -> str:
        """Path to persist license state so it survives restarts."""
        return os.getenv("LICENSE_STATE_PATH", "/data/license_state.json")
    
    def _load_state(self):
        """Load persisted license state from disk."""
        try:
            path = self._get_state_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    state = json.load(f)
                    self._installed_at = datetime.fromisoformat(state.get('installed_at'))
                    self._license_data = state.get('license_data')
                    self._status = state.get('status', LicenseStatus.DISABLED)
                    logger.info(f"Loaded license state: {self._status}")
        except Exception as e:
            logger.warning(f"Could not load license state: {e}")
            self._installed_at = datetime.now()
    
    def _save_state(self):
        """Persist license state to disk."""
        try:
            path = self._get_state_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            state = {
                'installed_at': self._installed_at.isoformat() if self._installed_at else datetime.now().isoformat(),
                'license_data': self._license_data,
                'status': self._status
            }
            with open(path, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Could not save license state: {e}")
    
    def _generate_license_signature(self, data: Dict) -> str:
        """Generate HMAC signature for a license."""
        message = json.dumps(data, sort_keys=True)
        return hmac.new(
            LICENSE_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
    
    def generate_license(self, customer: str, max_stores: int, max_cameras: int, 
                         expiry_days: int = 365, features: list = None) -> str:
        """
        Generate a signed license key for a customer.
        This would be called by the licensing server, not by the deployment.
        """
        data = {
            'customer': customer,
            'max_stores': max_stores,
            'max_cameras': max_cameras,
            'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
            'features': features or ['cv_detection', 'sms_alerts', 'dashboard'],
            'issued': datetime.now().isoformat()
        }
        sig = self._generate_license_signature(data)
        # Encode as: base64(data).signature
        import base64
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        return f"spevino-{encoded}-{sig}"
    
    def validate(self, license_key: str = None) -> str:
        """
        Validate the current license. Returns status string.
        
        Priority:
        1. If valid license key → ACTIVE
        2. If no license but within grace period → GRACE
        3. If expired or invalid → EXPIRED/INVALID → system pauses
        """
        key = license_key or os.getenv("LICENSE_KEY", "")
        
        if key and key.startswith("spevino-"):
            try:
                parts = key.split('-')
                if len(parts) == 3:
                    _, encoded, sig = parts
                    import base64
                    decoded = base64.b64decode(encoded).decode()
                    data = json.loads(decoded)
                    
                    # Verify signature
                    expected_sig = self._generate_license_signature(data)
                    if hmac.compare_digest(sig, expected_sig):
                        # Check expiry
                        expiry = datetime.fromisoformat(data['expiry'])
                        if datetime.now() < expiry:
                            self._status = LicenseStatus.ACTIVE
                            self._license_data = data
                            self._save_state()
                            logger.info(f"License ACTIVE for {data['customer']} until {data['expiry']}")
                            return self._status
                        else:
                            self._status = LicenseStatus.EXPIRED
                            logger.warning(f"License EXPIRED for {data['customer']} since {data['expiry']}")
                    else:
                        self._status = LicenseStatus.INVALID
                        logger.warning("License signature INVALID")
                else:
                    self._status = LicenseStatus.INVALID
            except Exception as e:
                logger.error(f"License validation error: {e}")
                self._status = LicenseStatus.INVALID
        
        # No valid license - check grace period
        if not self._installed_at:
            self._installed_at = datetime.now()
        
        days_since_install = (datetime.now() - self._installed_at).days
        if days_since_install <= GRACE_PERIOD_DAYS:
            self._status = LicenseStatus.GRACE
            remaining = GRACE_PERIOD_DAYS - days_since_install
            logger.info(f"License in GRACE period - {remaining} days remaining")
        else:
            self._status = LicenseStatus.DISABLED
            logger.warning("License DISABLED - grace period expired")
        
        self._save_state()
        return self._status
    
    @property
    def is_active(self) -> bool:
        """Can the system run full functionality?"""
        return self._status in (LicenseStatus.ACTIVE, LicenseStatus.GRACE)
    
    @property
    def can_detect(self) -> bool:
        """Is CV detection allowed?"""
        return self._status == LicenseStatus.ACTIVE
    
    @property
    def can_alert(self) -> bool:
        """Are SMS alerts allowed?"""
        return self._status == LicenseStatus.ACTIVE
    
    def get_status_info(self) -> Dict:
        """Get full license status for API response."""
        info = {
            'status': self._status,
            'is_active': self.is_active,
            'can_detect': self.can_detect,
            'can_alert': self.can_alert,
        }
        
        if self._license_data:
            info['customer'] = self._license_data.get('customer')
            info['expiry'] = self._license_data.get('expiry')
            info['max_stores'] = self._license_data.get('max_stores')
            info['max_cameras'] = self._license_data.get('max_cameras')
            info['features'] = self._license_data.get('features')
        
        if self._status == LicenseStatus.GRACE:
            days_left = GRACE_PERIOD_DAYS - (datetime.now() - self._installed_at).days
            info['grace_days_remaining'] = max(0, days_left)
            info['message'] = f"Trial mode — {info.get('grace_days_remaining', 0)} days remaining. Enter a license key to unlock full features."
        elif self._status == LicenseStatus.DISABLED:
            info['message'] = "⚠️ Subscription expired. CV detection and SMS alerts are paused. Enter a valid license key to reactivate."
        elif self._status == LicenseStatus.ACTIVE:
            info['message'] = "✓ System active and licensed."
        
        return info

# Singleton
license_manager = LicenseManager()