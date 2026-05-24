import os
import uuid
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to_number: str, body: str):
    if not client or not TWILIO_FROM_NUMBER:
        logger.warning(f"[MOCK SMS] To {to_number}: {body}")
        # Use a deterministic mock SID for testing
        return f"mock_sid_{uuid.uuid4().hex[:8]}"
    
    try:
        message = client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=to_number
        )
        return message.sid
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}")
        return None

import datetime

def format_alert_message(store_name: str, camera_name: str, event_type: str, confidence: float, event_id: str, zone_type: str = None, register_id: str = None):
    # Base message parts
    lines = [
        f"🚨 Spevino LP-OS Alert",
        f"Store: {store_name}",
        f"Camera: {camera_name}"
    ]
    
    # Time formatting (simplified to current time if we don't have event time, but better to use current)
    now = datetime.datetime.now().strftime("%I:%M %p")
    
    # Specific event formatting based on ARCHITECTURE.md 7.2
    event_desc = event_type.replace('_', ' ').capitalize()
    if event_type == 'restricted_area_breach':
        zone = zone_type.replace('_', ' ') if zone_type else "restricted area"
        lines.append(f"Event: {event_desc} — {zone} entry ({int(confidence * 100)}% confidence)")
    elif event_type == 'cash_register_theft':
        desc = "unauthorized void without customer" # Default logic from Architecture doc
        lines.append(f"Event: {event_desc} — {desc} ({int(confidence * 100)}% confidence)")
    else:
        lines.append(f"Event: {event_desc} ({int(confidence * 100)}% confidence)")
        
    lines.append(f"Time: {now} CST") # CST as per doc example
    lines.append(f"View: https://dashboard.spevino.com/events/{event_id}")
    
    return "\n".join(lines)
