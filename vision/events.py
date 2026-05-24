"""
Event Output Module for Spevino Surveillance
Formats and outputs detection events for the backend system.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types matching the database schema."""
    SHOPLIFTING_SUSPECTED = "shoplifting_suspected"
    MOTION_ANOMALY = "motion_anomaly"
    OBJECT_LEFT = "object_left"
    RESTRICTED_AREA_BREACH = "restricted_area_breach"
    CASH_REGISTER_THEFT = "cash_register_theft"


@dataclass
class DetectionEvent:
    """
    Structured detection event for database insertion.
    
    Matches the 'events' table schema from ARCHITECTURE.md Section 4.2
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str = ""
    store_id: str = ""
    event_type: str = EventType.MOTION_ANOMALY.value
    confidence: float = 0.0
    description: str = ""
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary matching the events table schema.
        
        Returns a dictionary suitable for database insertion.
        """
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "store_id": self.store_id,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "description": self.description,
            "clip_path": self.clip_path,
            "thumbnail_path": self.thumbnail_path,
            "created_at": self.created_at.isoformat(),
            "metadata": json.dumps(self.metadata) if self.metadata else None
        }
    
    def to_api_response(self) -> dict:
        """
        Convert to API response format.
        
        Returns a dictionary suitable for API responses.
        """
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "store_id": self.store_id,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "description": self.description,
            "clip_path": self.clip_path,
            "thumbnail_path": self.thumbnail_path,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AlertPayload:
    """
    Alert payload for SMS and notification systems.
    
    Contains formatted message and metadata.
    """
    event: DetectionEvent
    store_name: str = ""
    camera_name: str = ""
    
    def to_sms_body(self) -> str:
        """
        Format as SMS message.
        
        Returns a formatted string for Twilio SMS.
        """
        emoji = "🚨"
        
        return f"""{emoji} Spevino Alert
Store: {self.store_name}
Camera: {self.camera_name}
Event: {self.event.description}
Time: {self.event.created_at.strftime('%I:%M %p %Z')}
Confidence: {self.event.confidence * 100:.0f}%"""
    
    def to_push_payload(self) -> dict:
        """
        Format as push notification payload.
        
        Returns a dictionary for push notification services.
        """
        return {
            "title": "Spevino Alert",
            "body": self.event.description,
            "data": {
                "event_id": self.event.id,
                "event_type": self.event.event_type,
                "confidence": self.event.confidence,
                "camera_id": self.event.camera_id
            }
        }


class EventOutput:
    """
    Event output handler for the CV pipeline.
    
    Handles:
    - Database insertion via backend API
    - Clip and thumbnail generation
    - Event filtering and deduplication
    - Alert dispatch to notification services
    """
    
    def __init__(
        self,
        api_base_url: Optional[str] = None,
        camera_id: str = "default",
        store_id: str = "default",
        on_event: Optional[Callable[[DetectionEvent], None]] = None,
        on_alert: Optional[Callable[[AlertPayload], None]] = None,
        max_events_per_minute: int = 10
    ):
        """
        Initialize event output handler.
        
        Args:
            api_base_url: Base URL for the backend API
            camera_id: Camera identifier
            store_id: Store identifier
            on_event: Callback for new events
            on_alert: Callback for alert dispatch (SMS/Push)
            max_events_per_minute: Rate limiting for events
        """
        self.api_base_url = api_base_url or "http://localhost:8000/api/v1"
        self.camera_id = camera_id
        self.store_id = store_id
        
        self.on_event = on_event
        self.on_alert = on_alert
        
        self.max_events_per_minute = max_events_per_minute
        self._event_timestamps: List[datetime] = []
        
        self._event_cache: Dict[str, datetime] = {}  # For deduplication
        self._cache_duration_seconds = 30
    
    def emit_event(
        self,
        event_type: str,
        confidence: float,
        description: str,
        metadata: Optional[Dict] = None,
        thumbnail: Optional[bytes] = None,
        clip_path: Optional[str] = None
    ) -> Optional[DetectionEvent]:
        """
        Emit a new detection event.
        
        Args:
            event_type: Type of event (from EventType enum)
            confidence: Confidence score (0.0 - 1.0)
            description: Human-readable description
            metadata: Additional event metadata
            thumbnail: Optional thumbnail image data
            clip_path: Optional path to video clip
            
        Returns:
            DetectionEvent if emitted, None if rate limited or deduplicated
        """
        now = datetime.now()
        
        # Rate limiting
        self._event_timestamps = [
            ts for ts in self._event_timestamps
            if (now - ts).total_seconds() < 60
        ]
        
        if len(self._event_timestamps) >= self.max_events_per_minute:
            logger.warning("Event rate limit reached, dropping event")
            return None
        
        # Deduplication check
        dedup_key = f"{event_type}:{confidence:.2f}:{description[:50]}"
        last_seen = self._event_cache.get(dedup_key)
        if last_seen and (now - last_seen).total_seconds() < self._cache_duration_seconds:
            logger.debug(f"Duplicate event suppressed: {dedup_key}")
            return None
        
        # Create event
        event = DetectionEvent(
            camera_id=self.camera_id,
            store_id=self.store_id,
            event_type=event_type,
            confidence=confidence,
            description=description,
            clip_path=clip_path,
            thumbnail_path=None,  # Would be set after thumbnail generation
            metadata=metadata or {}
        )
        
        # Record event
        self._event_timestamps.append(now)
        self._event_cache[dedup_key] = now
        
        # Call event callback
        if self.on_event:
            try:
                self.on_event(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        # Generate alert payload
        if self.on_alert and confidence >= 0.75:
            try:
                alert_payload = AlertPayload(
                    event=event,
                    store_name="Store",  # Would be resolved from store_id
                    camera_name="Camera"  # Would be resolved from camera_id
                )
                self.on_alert(alert_payload)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.info(f"Event emitted: {event_type} ({confidence:.2f}) - {description}")
        
        return event
    
    def emit_from_alerts(
        self,
        alerts: List,
        camera_name: str = "Camera",
        store_name: str = "Store"
    ) -> List[DetectionEvent]:
        """
        Convert and emit pipeline alerts as detection events.
        
        Args:
            alerts: List of Alert objects from the analyzer
            camera_name: Human-readable camera name
            store_name: Human-readable store name
            
        Returns:
            List of emitted DetectionEvent objects
        """
        from analyzer import AlertType
        
        events = []
        
        # Map alert types to event types
        type_map = {
            AlertType.CONCEALMENT: EventType.SHOPLIFTING_SUSPECTED,
            AlertType.TRAJECTORY_ANOMALY: EventType.SHOPLIFTING_SUSPECTED,
            AlertType.OBJECT_ABANDONMENT: EventType.OBJECT_LEFT,
            AlertType.WRONG_WAY_FLOW: EventType.MOTION_ANOMALY,
            AlertType.COORDINATED_PERSONS: EventType.SHOPLIFTING_SUSPECTED,
            AlertType.RESTRICTED_AREA_BREACH: EventType.RESTRICTED_AREA_BREACH,
            AlertType.REGISTER_THEFT: EventType.CASH_REGISTER_THEFT
        }
        
        for alert in alerts:
            event_type = type_map.get(alert.alert_type, EventType.MOTION_ANOMALY)
            
            event = self.emit_event(
                event_type=event_type.value,
                confidence=alert.confidence,
                description=alert.description,
                metadata={
                    "alert_type": alert.alert_type.value,
                    "track_ids": alert.track_ids,
                    **alert.metadata
                }
            )
            
            if event:
                events.append(event)
        
        return events
    
    def clear_cache(self):
        """Clear the deduplication cache."""
        self._event_cache = {}
    
    def get_recent_event_count(self, minutes: int = 5) -> int:
        """Get count of events in the last N minutes."""
        now = datetime.now()
        return sum(
            1 for ts in self._event_timestamps
            if (now - ts).total_seconds() < minutes * 60
        )


class WebhookOutput:
    """
    Output handler that sends events to a webhook endpoint.
    
    Useful for integration with external systems or testing.
    """
    
    def __init__(self, webhook_url: str, auth_token: Optional[str] = None):
        """
        Initialize webhook output.
        
        Args:
            webhook_url: URL to send events to
            auth_token: Optional Bearer token for authentication
        """
        self.webhook_url = webhook_url
        self.auth_token = auth_token
    
    async def send_event(self, event: DetectionEvent) -> bool:
        """
        Send an event to the webhook.
        
        Args:
            event: The event to send
            
        Returns:
            True if successful, False otherwise
        """
        import aiohttp
        
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        payload = event.to_api_response()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    return response.status == 200 or response.status == 201
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False
    
    def send_event_sync(self, event: DetectionEvent) -> bool:
        """
        Synchronous version of send_event.
        
        Uses requests library instead of aiohttp.
        """
        import requests
        
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        payload = event.to_api_response()
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False