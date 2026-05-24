from database import team_db_execute
import uuid
import datetime
import auth

def escape(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

# User CRUD
def get_user_by_email(email: str):
    rows = team_db_execute(f"SELECT * FROM users WHERE email = {escape(email)}")
    return rows[0] if rows else None

def get_user_by_id(user_id: str):
    rows = team_db_execute(f"SELECT * FROM users WHERE id = {escape(user_id)}")
    return rows[0] if rows else None

def create_user(user_schema):
    hashed_password = auth.get_password_hash(user_schema.password)
    user_id = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow().isoformat()
    team_db_execute(f"""
        INSERT INTO users (id, email, phone, name, role, hashed_password, created_at)
        VALUES ({escape(user_id)}, {escape(user_schema.email)}, {escape(user_schema.phone)}, 
                {escape(user_schema.name)}, {escape(user_schema.role)}, 
                {escape(hashed_password)}, {escape(created_at)})
    """)
    return get_user_by_email(user_schema.email)

# Store CRUD
def get_stores(owner_id: str):
    return team_db_execute(f"SELECT * FROM stores WHERE owner_id = {escape(owner_id)}")

def get_store(store_id: str):
    rows = team_db_execute(f"SELECT * FROM stores WHERE id = {escape(store_id)}")
    return rows[0] if rows else None

def create_store(store_schema, owner_id: str):
    store_id = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow().isoformat()
    team_db_execute(f"""
        INSERT INTO stores (id, owner_id, name, address, latitude, longitude, created_at)
        VALUES ({escape(store_id)}, {escape(owner_id)}, {escape(store_schema.name)}, 
                {escape(store_schema.address)}, {store_schema.latitude or 'NULL'}, 
                {store_schema.longitude or 'NULL'}, {escape(created_at)})
    """)
    return get_store(store_id)

# Camera CRUD
def get_cameras(store_id: str):
    return team_db_execute(f"SELECT * FROM cameras WHERE store_id = {escape(store_id)}")

def get_camera(camera_id: str):
    rows = team_db_execute(f"SELECT * FROM cameras WHERE id = {escape(camera_id)}")
    return rows[0] if rows else None

def create_camera(camera_schema, store_id: str):
    camera_id = str(uuid.uuid4())
    team_db_execute(f"""
        INSERT INTO cameras (id, store_id, name, rtsp_url, location_hint, status, config)
        VALUES ({escape(camera_id)}, {escape(store_id)}, {escape(camera_schema.name)}, 
                {escape(camera_schema.rtsp_url)}, {escape(camera_schema.location_hint)}, 
                'offline', {escape(camera_schema.config)})
    """)
    return get_camera(camera_id)

# Event CRUD
def get_events(store_id: str = None, camera_id: str = None, event_type: str = None, limit: int = 100):
    query = "SELECT * FROM events"
    filters = []
    if store_id:
        filters.append(f"store_id = {escape(store_id)}")
    if camera_id:
        filters.append(f"camera_id = {escape(camera_id)}")
    if event_type:
        filters.append(f"event_type = {escape(event_type)}")
    
    if filters:
        query += " WHERE " + " AND ".join(filters)
    
    query += f" ORDER BY created_at DESC LIMIT {limit}"
    return team_db_execute(query)

def create_event(event_schema):
    event_id = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow().isoformat()
    team_db_execute(f"""
        INSERT INTO events (id, camera_id, store_id, event_type, confidence, description, zone_type, register_id, clip_path, thumbnail_path, created_at)
        VALUES ({escape(event_id)}, {escape(event_schema.camera_id)}, {escape(event_schema.store_id)}, 
                {escape(event_schema.event_type)}, {event_schema.confidence}, {escape(event_schema.description)}, 
                {escape(event_schema.zone_type)}, {escape(event_schema.register_id)}, 
                {escape(event_schema.clip_path)}, {escape(event_schema.thumbnail_path)}, {escape(created_at)})
    """)
    # Fetch the event back (including joined store/owner info if needed, but for now just the event)
    rows = team_db_execute(f"SELECT * FROM events WHERE id = {escape(event_id)}")
    return rows[0] if rows else None

# Alert CRUD
def create_alert(event_id: str, user_id: str, channel: str):
    alert_id = str(uuid.uuid4())
    team_db_execute(f"""
        INSERT INTO alerts (id, event_id, user_id, channel, status)
        VALUES ({escape(alert_id)}, {escape(event_id)}, {escape(user_id)}, {escape(channel)}, 'pending')
    """)
    rows = team_db_execute(f"SELECT * FROM alerts WHERE id = {escape(alert_id)}")
    return rows[0] if rows else None

def update_alert_status(alert_id: str, status: str, twilio_sid: str = None):
    sent_at = datetime.datetime.utcnow().isoformat()
    team_db_execute(f"""
        UPDATE alerts SET status = {escape(status)}, twilio_sid = {escape(twilio_sid)}, sent_at = {escape(sent_at)}
        WHERE id = {escape(alert_id)}
    """)

# Dashboard Stats
def get_dashboard_stats(owner_id: str):
    since_24h = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat()
    
    # Total stores
    stores = team_db_execute(f"SELECT COUNT(*) as count FROM stores WHERE owner_id = {escape(owner_id)}")
    
    # Total events 24h
    events = team_db_execute(f"""
        SELECT COUNT(*) as count FROM events 
        JOIN stores ON events.store_id = stores.id 
        WHERE stores.owner_id = {escape(owner_id)} AND events.created_at >= {escape(since_24h)}
    """)
    
    # Total alerts 24h
    alerts = team_db_execute(f"SELECT COUNT(*) as count FROM alerts WHERE user_id = {escape(owner_id)} AND sent_at >= {escape(since_24h)}")
    
    # Active cameras
    cameras = team_db_execute(f"""
        SELECT COUNT(*) as count FROM cameras 
        JOIN stores ON cameras.store_id = stores.id 
        WHERE stores.owner_id = {escape(owner_id)} AND cameras.status = 'online'
    """)

    # Event breakdown 24h
    types = team_db_execute(f"""
        SELECT event_type, COUNT(*) as count FROM events 
        JOIN stores ON events.store_id = stores.id 
        WHERE stores.owner_id = {escape(owner_id)} AND events.created_at >= {escape(since_24h)}
        GROUP BY event_type
    """)
    
    event_breakdown_24h = {row['event_type']: row['count'] for row in types}
    
    return {
        "total_stores": stores[0]['count'] if stores else 0,
        "total_events_24h": events[0]['count'] if events else 0,
        "total_alerts_24h": alerts[0]['count'] if alerts else 0,
        "active_cameras": cameras[0]['count'] if cameras else 0,
        "event_breakdown_24h": event_breakdown_24h
    }

def get_event_with_details(event_id: str):
    # Join event with store and owner to get phone number
    rows = team_db_execute(f"""
        SELECT e.*, s.name as store_name, u.phone as owner_phone, u.id as owner_id, 
               c.name as camera_name, c.location_hint as camera_location
        FROM events e
        JOIN stores s ON e.store_id = s.id
        JOIN users u ON s.owner_id = u.id
        LEFT JOIN cameras c ON e.camera_id = c.id
        WHERE e.id = {escape(event_id)}
    """)
    return rows[0] if rows else None

def get_recent_alerts_for_user(user_id: str, minutes: int):
    since = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).isoformat()
    return team_db_execute(f"""
        SELECT * FROM alerts 
        WHERE user_id = {escape(user_id)} AND status = 'sent' AND sent_at >= {escape(since)}
    """)

def get_recent_alerts_for_store(store_id: str, hours: int):
    since = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).isoformat()
    return team_db_execute(f"""
        SELECT a.* FROM alerts a
        JOIN events e ON a.event_id = e.id
        WHERE e.store_id = {escape(store_id)} AND a.status = 'sent' AND a.sent_at >= {escape(since)}
    """)
