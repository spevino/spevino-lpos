from sqlalchemy import Column, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="owner")
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    stores = relationship("Store", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")

class Store(Base):
    __tablename__ = "stores"
    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="stores")
    cameras = relationship("Camera", back_populates="store")
    events = relationship("Event", back_populates="store")

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(String, primary_key=True, default=generate_uuid)
    store_id = Column(String, ForeignKey("stores.id"))
    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    location_hint = Column(String)
    status = Column(String, default="offline")
    last_seen = Column(DateTime)
    config = Column(Text) # JSON string

    store = relationship("Store", back_populates="cameras")
    events = relationship("Event", back_populates="camera")

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=generate_uuid)
    camera_id = Column(String, ForeignKey("cameras.id"))
    store_id = Column(String, ForeignKey("stores.id"))
    event_type = Column(String) # 'shoplifting_suspected', 'restricted_area_breach', 'cash_register_theft', 'motion_anomaly', 'object_left'
    confidence = Column(Float)
    description = Column(Text)
    zone_type = Column(String, nullable=True)
    register_id = Column(String, nullable=True)
    clip_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    camera = relationship("Camera", back_populates="events")
    store = relationship("Store", back_populates="events")
    alerts = relationship("Alert", back_populates="event")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("events.id"))
    user_id = Column(String, ForeignKey("users.id"))
    channel = Column(String) # 'sms', 'push', 'email'
    status = Column(String, default="pending")
    sent_at = Column(DateTime)
    twilio_sid = Column(String, nullable=True)

    event = relationship("Event", back_populates="alerts")
    user = relationship("User", back_populates="alerts")

class Config(Base):
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    value = Column(Text) # JSON-encoded value
