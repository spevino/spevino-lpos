import subprocess
import uuid
import datetime
import bcrypt

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def execute(sql):
    print(f"Executing: {sql}")
    subprocess.run(["team-db", sql], check=True)

# 1. Create Owner
owner_id = str(uuid.uuid4())
hashed_pwd = get_password_hash("password123")
execute(f"""
    INSERT INTO users (id, email, phone, name, role, hashed_password, created_at)
    VALUES ('{owner_id}', 'owner@example.com', '+1234567890', 'Store Owner', 'owner', '{hashed_pwd}', '{datetime.datetime.utcnow().isoformat()}')
""")

# 2. Create Store
store_id = str(uuid.uuid4())
execute(f"""
    INSERT INTO stores (id, owner_id, name, address, latitude, longitude, created_at)
    VALUES ('{store_id}', '{owner_id}', 'QuickMart #42', '123 Main St, Austin TX 78701', 30.2672, -97.7431, '{datetime.datetime.utcnow().isoformat()}')
""")

# 3. Create Camera
camera_id = str(uuid.uuid4())
execute(f"""
    INSERT INTO cameras (id, store_id, name, rtsp_url, location_hint, status)
    VALUES ('{camera_id}', '{store_id}', 'Entrance', 'rtsp://admin:password@192.168.1.100:554/live', 'entrance', 'online')
""")

# 4. Create Example Events
execute(f"""
    INSERT INTO events (id, camera_id, store_id, event_type, confidence, description, zone_type, created_at)
    VALUES ('{str(uuid.uuid4())}', '{camera_id}', '{store_id}', 'restricted_area_breach', 0.92, 'Unauthorized back room entry', 'back_room', '{datetime.datetime.utcnow().isoformat()}')
""")

execute(f"""
    INSERT INTO events (id, camera_id, store_id, event_type, confidence, description, zone_type, register_id, created_at)
    VALUES ('{str(uuid.uuid4())}', '{camera_id}', '{store_id}', 'cash_register_theft', 0.85, 'Unauthorized drawer open', 'point_of_sale', 'REG-001', '{datetime.datetime.utcnow().isoformat()}')
""")

print("Seeding complete.")
print(f"Owner Email: owner@example.com")
print(f"Owner Password: password123")
