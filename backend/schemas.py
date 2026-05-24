from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    phone: str
    name: str
    role: Optional[str] = "owner"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Store schemas
class StoreBase(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StoreCreate(StoreBase):
    pass

class Store(StoreBase):
    id: str
    owner_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Camera schemas
class CameraBase(BaseModel):
    name: str
    rtsp_url: str
    location_hint: Optional[str] = None
    config: Optional[str] = None

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: str
    store_id: str
    status: str
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

# Event schemas
class EventBase(BaseModel):
    camera_id: str
    store_id: str
    event_type: str
    confidence: float
    description: str
    zone_type: Optional[str] = None
    register_id: Optional[str] = None
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Alert schemas
class AlertBase(BaseModel):
    event_id: str
    user_id: str
    channel: str

class Alert(AlertBase):
    id: str
    status: str
    sent_at: Optional[datetime] = None
    twilio_sid: Optional[str] = None

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
