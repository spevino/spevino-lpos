# Spevino Loss Prevention Operating System

[![Install](https://img.shields.io/badge/Install-One--Click-blue)](install.sh)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](docker-compose.yml)

A **Loss Prevention Operating System (LP-OS)** — a real-time AI-powered surveillance platform that detects shoplifting, restricted area breaches, and cash register theft at retail stores and gas stations using computer vision. Sends SMS alerts and provides a web dashboard for live monitoring.

## 🚀 Quick Install

```bash
curl -fsSL https://github.com/spevino/spevino-lpos/raw/main/install.sh | bash
```

The installer: Installs Docker → Clones repo → Builds images → Starts services → Dashboard at **http://localhost:3000**

## 📋 Subscription

| Tier | Detection | SMS Alerts | Dashboard |
|------|-----------|------------|-----------|
| **Trial** (14 days) | ❌ Paused | ❌ Paused | ✅ |
| **Active** | ✅ | ✅ | ✅ |
| **Expired** | ❌ Paused | ❌ Paused | ✅ |

Activate: `POST /license/activate` with your license key. Without payment, the system pauses CV detection and SMS alerts.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the complete system design, including:
- Component diagrams and data flow
- Technology stack recommendations
- Database schema
- API design specifications
- CV detection pipeline
- Hardware requirements

## Project Structure

```
spevino/
├── ARCHITECTURE.md          # System architecture document
├── README.md                # This file
├── docker-compose.yml       # Main docker compose for local development
├── config/                  # Shared configuration files
│   └── docker-compose.yml   # Docker Compose for edge deployment
├── backend/                 # FastAPI backend (CV Engineer)
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core config, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic (SMS, events)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── vision/                  # Computer vision pipeline (CV Engineer)
│   ├── src/
│   │   ├── detection/      # YOLOv8 object detection
│   │   ├── tracking/      # ByteTrack/SORT motion tracking
│   │   ├── behavior/      # Behavior analysis engine
│   │   └── pipeline.py    # Main CV pipeline
│   ├── models/             # Trained model weights
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
└── frontend/                # Next.js dashboard (Frontend Developer)
    ├── app/
    │   ├── (auth)/        # Auth pages
    │   ├── dashboard/      # Main dashboard
    │   ├── stores/        # Store management
    │   └── events/        # Event viewing
    ├── components/
    ├── lib/
    ├── requirements.txt
    └── Dockerfile
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Local Development

1. **Start the backend:**
   ```bash
   cd backend
   docker build -t spevino/backend .
   docker run -p 8000:8000 spevino/backend
   ```

2. **Start the vision worker:**
   ```bash
   cd vision
   docker build -t spevino/vision .
   docker run --gpus all spevino/vision
   ```

3. **Start the frontend:**
   ```bash
   cd frontend
   docker build -t spevino/frontend .
   docker run -p 3000:3000 spevino/frontend
   ```

Or use the main `docker-compose.yml` at the root:

```bash
docker-compose up --build
```

### Edge Deployment (Per Store)

Use `config/docker-compose.yml` on the edge processor installed at each store location:

```bash
cd config
docker-compose up -d
```

## Services

### Backend API (FastAPI)
- REST API at `http://localhost:8000`
- Auto-generated docs at `http://localhost:8000/docs`
- WebSocket at `ws://localhost:8000/ws`

### Vision Pipeline (PyTorch + OpenCV)
- YOLOv8 object detection
- ByteTrack motion tracking
- Behavior analysis for shoplifting patterns and restricted area breach detection

### Frontend Dashboard (Next.js 14)
- Live camera feed viewing
- Alert history and management
- Store/camera configuration

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Turso SQLite connection string | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Yes |
| `TWILIO_PHONE_NUMBER` | Twilio sender phone | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | Yes |
| `API_BASE_URL` | Backend API base URL | Yes |

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/stores` | GET/POST | List/create stores |
| `/api/v1/cameras` | GET/POST | List/create cameras |
| `/api/v1/events` | GET | List detection events (shoplifting, restricted_area_breach, etc.) |
| `/api/v1/alerts` | GET | List sent alerts |
| `/api/v1/dashboard/stats` | GET | Dashboard aggregates |

## Team

- **Tech Lead / System Architect**: Architecture design, project scaffolding
- **Backend / SMS Engineer**: FastAPI, Twilio integration, database management
- **CV Engineer**: YOLOv8, motion tracking, behavior analysis
- **Frontend Developer**: Next.js dashboard, real-time UI

## License

Proprietary — Spevino LLC