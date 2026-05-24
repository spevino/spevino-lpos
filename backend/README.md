# Backend Service

**Owner:** Backend / SMS Engineer

## Overview
FastAPI-based REST API + WebSocket server. Handles:
- User authentication (JWT)
- Store and camera CRUD
- Event persistence and retrieval
- Twilio SMS alert dispatch
- WebSocket push to dashboard

## Tech Stack
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy 2.x
- **Database:** SQLite + Turso
- **SMS:** Twilio Python SDK
- **Auth:** python-jose (JWT RS256)
- **WS:** FastAPI WebSocket + redis-pubsub

## Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── stores.py
│   │   │   ├── cameras.py
│   │   │   ├── events.py
│   │   │   ├── alerts.py
│   │   │   └── dashboard.py
│   │   └── ws.py              # WebSocket handlers
│   ├── core/
│   │   ├── config.py          # Settings from env
│   │   ├── security.py        # JWT, password hashing
│   │   └── database.py        # DB connection
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/
│   │   ├── sms_service.py     # Twilio integration
│   │   ├── event_service.py   # Event creation logic
│   │   └── camera_service.py  # Camera heartbeat, config
│   └── main.py
├── requirements.txt
├── Dockerfile
└── README.md (this file)
```

## Environment Variables
```bash
DATABASE_URL=libsql://spevino-db.turso.io
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+15551234567
JWT_SECRET_KEY=/path/to/jwt-private.pem  # RS256 private key
JWT_PUBLIC_KEY=/path/to/jwt-public.pem
```

## API Endpoints (see full docs at /docs)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET/POST /api/v1/stores`
- `GET/POST /api/v1/stores/{store_id}/cameras`
- `GET /api/v1/events`
- `GET /api/v1/alerts`
- `GET /api/v1/dashboard/stats`
- `WS /ws/alerts/{user_id}`

## Local Dev
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Docker
```bash
docker build -t spevino/backend .
docker run -p 8000:8000 spevino/backend
```