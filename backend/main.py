from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import json
import datetime

import schemas, crud, auth, sms, license, gating

app = FastAPI(title="Spevino API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except auth.JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user['email']})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate):
    db_user = crud.get_user_by_email(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(user_schema=user)

@app.post("/auth/refresh", response_model=schemas.Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    access_token = auth.create_access_token(data={"sub": current_user['email']})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# License / Subscription Management
@app.get("/license")
def get_license_status():
    """Get current license status."""
    return license.license_manager.get_status_info()

@app.post("/license/activate")
def activate_license(key_data: dict):
    """Activate system with a license key."""
    key = key_data.get('key', '')
    if not key:
        raise HTTPException(status_code=400, detail="License key required")
    status = license.license_manager.validate(key)
    if status == license.LicenseStatus.ACTIVE:
        return {"status": "ok", "message": "License activated!", "license": license.license_manager.get_status_info()}
    elif status == license.LicenseStatus.INVALID:
        raise HTTPException(status_code=400, detail="Invalid license key")
    elif status == license.LicenseStatus.EXPIRED:
        raise HTTPException(status_code=400, detail="License expired")
    raise HTTPException(status_code=400, detail=f"Status: {status}")

# Stores
@app.get("/stores", response_model=List[schemas.Store])
def read_stores(current_user: dict = Depends(get_current_user)):
    return crud.get_stores(owner_id=current_user['id'])

@app.post("/stores", response_model=schemas.Store)
def create_store(store: schemas.StoreCreate, current_user: dict = Depends(get_current_user)):
    gating.check_store_limit()
    return crud.create_store(store_schema=store, owner_id=current_user['id'])

@app.get("/stores/{store_id}", response_model=schemas.Store)
def read_store(store_id: str, current_user: dict = Depends(get_current_user)):
    store = crud.get_store(store_id)
    if not store or store['owner_id'] != current_user['id']:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

# Cameras
@app.get("/stores/{store_id}/cameras", response_model=List[schemas.Camera])
def read_cameras(store_id: str, current_user: dict = Depends(get_current_user)):
    store = crud.get_store(store_id)
    if not store or store['owner_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_cameras(store_id=store_id)

@app.post("/stores/{store_id}/cameras", response_model=schemas.Camera)
def create_camera(store_id: str, camera: schemas.CameraCreate, current_user: dict = Depends(get_current_user)):
    store = crud.get_store(store_id)
    if not store or store['owner_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    gating.check_camera_limit(store_id)
    return crud.create_camera(camera_schema=camera, store_id=store_id)

# Events (Ingestion & Listing)
@app.get("/events", response_model=List[schemas.Event])
def read_events(store_id: Optional[str] = None, camera_id: Optional[str] = None, event_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # In a full app, we'd verify store_id belongs to current_user
    return crud.get_events(store_id=store_id, camera_id=camera_id, event_type=event_type)

@app.post("/events", response_model=schemas.Event)
async def create_event(event: schemas.EventCreate, background_tasks: BackgroundTasks):
    # Check if event type is allowed in this tier
    gating.check_event_type_access(event.event_type)

    # Find owner to check tier gating
    store = crud.get_store(event.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    owner = crud.get_user_by_id(store['owner_id']) # I'll add this to crud.py
    
    # License check — if detection is paused, reject events
    if not license.license_manager.can_detect:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail="⚠️ Subscription inactive. CV detection is paused. Please activate your license at /license/activate"
        )
    
    db_event = crud.create_event(event_schema=event)
    
    # Broadcast via WebSocket (including tier)
    status_info = license.license_manager.get_status_info()
    await manager.broadcast(json.dumps({
        "type": "new_event",
        "data": db_event,
        "tier": status_info.get('tier'),
        "tier_name": status_info.get('tier_name')
    }))

    # Trigger SMS alert if confidence is high (only if tier and license allows alerts)
    if db_event['confidence'] >= 0.75 and license.license_manager.can_alert:
        background_tasks.add_task(process_alerts, db_event['id'])
    
    return db_event

# Alerts
@app.get("/alerts")
def read_alerts(current_user: dict = Depends(get_current_user)):
    # Simple list for now
    return crud.team_db_execute(f"SELECT * FROM alerts WHERE user_id = '{current_user['id']}'")

# Dashboard
@app.get("/dashboard/stats")
def read_dashboard_stats(current_user: dict = Depends(get_current_user)):
    return crud.get_dashboard_stats(owner_id=current_user['id'])

async def process_alerts(event_id: str):
    event = crud.get_event_with_details(event_id)
    if not event:
        return
    
    owner_phone = event['owner_phone']
    owner_id = event['owner_id']
    store_id = event['store_id']
    
    if owner_phone:
        # Alert Throttling (Section 7.3)
        # 1. Cooldown: 60 seconds between SMS to same phone number
        recent_to_user = crud.get_recent_alerts_for_user(owner_id, minutes=1)
        if recent_to_user:
            print(f"Throttling alert to {owner_phone} - 60s cooldown")
            return

        # 2. Max 10 SMS per store per hour
        recent_for_store = crud.get_recent_alerts_for_store(store_id, hours=1)
        if len(recent_for_store) >= 10:
            print(f"Throttling alert for store {event['store_name']} - hourly limit reached")
            return

        # Create alert record
        db_alert = crud.create_alert(event_id=event['id'], user_id=owner_id, channel="sms")
        
        # Send SMS
        message = sms.format_alert_message(
            store_name=event['store_name'],
            camera_name=event['camera_name'] or "Unknown",
            event_type=event['event_type'],
            confidence=event['confidence'],
            event_id=event['id'],
            zone_type=event.get('zone_type'),
            register_id=event.get('register_id'),
            camera_location=event.get('camera_location')
        )
        
        twilio_sid = sms.send_sms(owner_phone, message)
        
        if twilio_sid:
            crud.update_alert_status(db_alert['id'], "sent", twilio_sid)
        else:
            crud.update_alert_status(db_alert['id'], "failed")
        
        # Notify via WebSocket too (including tier)
        status_info = license.license_manager.get_status_info()
        await manager.broadcast(json.dumps({
            "type": "new_alert",
            "data": {
                "event_id": event_id,
                "message": message
            },
            "tier": status_info.get('tier'),
            "tier_name": status_info.get('tier_name')
        }))

# WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/alerts/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
