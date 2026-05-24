# Spevino Loss Prevention Operating System — Architecture Document

## 1. Overview

Spevino is a **Loss Prevention Operating System (LP-OS)** — a real-time video surveillance platform that detects shoplifting, restricted area breaches, and suspicious behavior at retail stores and gas stations using computer vision, alerts store owners via SMS, and provides a web dashboard for live monitoring.

**Core Capabilities:**
- Ingest video streams from multiple IP cameras per location
- Detect shoplifting behavior via object detection, motion analysis, and behavioral patterns
- Detect restricted area breaches (staff-only zones, back rooms, cash rooms, loading docks)
- Detect cash register / point-of-sale theft (sweethearting, voiding transactions, drawer stealing)
- Send SMS alerts to store owners when suspicious activity is detected
- Web dashboard for live feeds, alert history, and camera management

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SPEVINO LOSS PREVENTION OS                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌─────────────────┐     ┌────────────────────────────┐  │
│  │ IP Cameras  │────▶│  Edge Processor │────▶│   Central Analytics Engine │  │
│  │ (per store) │     │  (on-prem/NVR)  │     │   (cloud-hosted)            │  │
│  └─────────────┘     └─────────────────┘     │                             │  │
│                                               │  ┌─────────────────────┐    │  │
│                                               │  │ CV Detection Engine │    │  │
│                                               │  │ - Object Detection  │    │  │
│                                               │  │ - Motion Analysis  │    │  │
│                                               │  │ - Behavior Patterns│    │  │
│                                               │  └─────────────────────┘    │  │
│                                               │                             │  │
│                                               │  ┌─────────────────────┐    │  │
│                                               │  │   Alert Manager     │    │  │
│                                               │  │   - SMS (Twilio)    │    │  │
│                                               │  │   - Push Notifications│  │  │
│                                               │  └─────────────────────┘    │  │
│                                               └────────────────────────────┘  │
│                                                                  │           │
│                                    ┌─────────────────────────────┘           │
│                                    ▼                                            │
│                         ┌─────────────────┐                                    │
│                         │  Web Dashboard  │                                    │
│                         │  (React/Next.js)│                                    │
│                         └─────────────────┘                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
IP Camera Stream
      │
      ▼
┌─────────────────┐
│  Edge Processor  │ ◀── Camera auth & stream management
│  (RTSP ingestion)│
└────────┬────────┘
         │ RTSP/HTTP
         ▼
┌─────────────────────────────────────────────────────────┐
│              Central Analytics Engine                    │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ Video Buffer │───▶│ CV Pipeline  │───▶│ Alert Gen  │ │
│  │ (Frames)     │    │ (Detection)  │    │ (Events)   │ │
│  └──────────────┘    └──────────────┘    └─────┬──────┘ │
│                                                │         │
│                                                ▼         │
│                                    ┌───────────────────┐  │
│                                    │   SQLite/Turso   │  │
│                                    │   (Persistence)  │  │
│                                    └─────────┬─────────┘  │
│                                              │            │
└──────────────────────────────────────────────┼────────────┘
                                               │
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
          ┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
          │   SMS Service   │         │  Web Dashboard  │        │  Notification   │
          │   (Twilio)      │         │  (Real-time)    │        │  Service        │
          └─────────────────┘         └─────────────────┘        └─────────────────┘
```

---

## 3. Technology Stack

### 3.1 Recommended Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Video Ingestion** | FFmpeg + OpenCV | Robust RTSP stream handling, cross-platform |
| **CV/DL Framework** | PyTorch + YOLOv8 | State-of-the-art object detection, fast inference |
| **Behavior Analysis** | Custom Python + OpenCV | Motion tracking, trajectory analysis |
| **Backend API** | FastAPI (Python) | Async, fast, auto-docs, uvicorn server |
| **Database** | SQLite + Turso | Edge-friendly, syncs to cloud, zero-config |
| **SMS Service** | Twilio API | Reliable, global SMS delivery |
| **Dashboard Frontend** | Next.js 14 + React | SSR, API routes, real-time via WebSocket |
| **Real-time Comms** | WebSocket (ws library) | Live alerts and feed updates |
| **Deployment** | Docker + Docker Compose | Consistent environments across edge/cloud |
| **Cloud Hosting** | AWS EC2 / DigitalOcean | GPU instances for CV inference |

### 3.2 Alternative Considerations

- **CV Acceleration**: NVIDIA Triton Inference Server for GPU batch inference
- **Video Storage**: AWS S3 for clip archival (optional)
- **Message Queue**: Redis Pub/Sub for scaling alert distribution
- **CDN**: Cloudflare for dashboard static asset delivery

---

## 4. Database Schema

### 4.1 Entity Relationship

```
users ─────┬───── stores (1:many)
           │
           └───── alerts (1:many)

stores ────┬───── cameras (1:many)
           │
           └───── events (1:many)

cameras ───┴───── events (1:many)
```

### 4.2 Tables

#### `users`
| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY (UUID) |
| email | TEXT | NOT NULL, UNIQUE |
| phone | TEXT | NOT NULL |
| name | TEXT | NOT NULL |
| role | TEXT | DEFAULT 'owner' |
| created_at | TEXT | ISO timestamp |

#### `stores`
| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY (UUID) |
| owner_id | TEXT | FOREIGN KEY → users.id |
| name | TEXT | NOT NULL |
| address | TEXT | |
| latitude | REAL | |
| longitude | REAL | |
| created_at | TEXT | ISO timestamp |

#### `cameras`
| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY (UUID) |
| store_id | TEXT | FOREIGN KEY → stores.id |
| name | TEXT | NOT NULL |
| rtsp_url | TEXT | NOT NULL |
| location_hint | TEXT | e.g., "entrance", "aisle_3" |
| status | TEXT | 'online' / 'offline' / 'maintenance' |
| last_seen | TEXT | ISO timestamp |
| config | TEXT | JSON — detection zones, sensitivity |

#### `events`
| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY (UUID) |
| camera_id | TEXT | FOREIGN KEY → cameras.id |
| store_id | TEXT | FOREIGN KEY → stores.id |
| event_type | TEXT | 'shoplifting_suspected' / 'restricted_area_breach' / 'cash_register_theft' / 'motion_anomaly' / 'object_left' |
| confidence | REAL | 0.0–1.0 |
| description | TEXT | Human-readable summary |
| clip_path | TEXT | Path to stored video clip (optional) |
| thumbnail_path | TEXT | Path to alert thumbnail |
| created_at | TEXT | ISO timestamp |

#### `alerts`
| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY (UUID) |
| event_id | TEXT | FOREIGN KEY → events.id |
| user_id | TEXT | FOREIGN KEY → users.id |
| channel | TEXT | 'sms' / 'push' / 'email' |
| status | TEXT | 'pending' / 'sent' / 'failed' |
| sent_at | TEXT | ISO timestamp |
| twilio_sid | TEXT | Twilio message SID (for SMS) |

#### `config`
| Column | Type | Constraints |
|--------|------|-------------|
| key | TEXT | PRIMARY KEY |
| value | TEXT | JSON-encoded value |

---

## 5. API Design

### 5.1 Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.spevino.com/api/v1`

### 5.2 Authentication
- JWT Bearer tokens in `Authorization` header
- Token lifetime: 24 hours (refresh supported)
- Roles: `owner`, `admin`

### 5.3 REST Endpoints

#### Authentication
```
POST /auth/register       → { email, phone, name, password } → { token, user }
POST /auth/login          → { email, password } → { token, user }
POST /auth/refresh        → { refresh_token } → { token }
```

#### Stores
```
GET    /stores            → [ { id, name, address, camera_count } ]
POST   /stores            → { name, address, lat, lng } → { store }
GET    /stores/{id}       → { id, name, cameras[], recent_events[] }
PUT    /stores/{id}       → { name, address }
DELETE /stores/{id}
```

#### Cameras
```
GET    /stores/{store_id}/cameras        → [ camera ]
POST   /stores/{store_id}/cameras         → { name, rtsp_url, location_hint, config }
GET    /cameras/{id}                     → { camera }
PUT    /cameras/{id}                     → { name, config, status }
DELETE /cameras/{id}
POST   /cameras/{id}/test-stream         → { status, message }
```

#### Events & Alerts
```
GET    /events                 → [ event ]  (filterable: store_id, camera_id, event_type, date_range)
GET    /events/{id}            → { event, alerts[] }
GET    /alerts                 → [ alert ]  (filterable: user_id, status, date_range)
POST   /alerts/{id}/retry      → { alert }  (retry failed SMS)
```

#### Dashboard (Aggregates)
```
GET    /dashboard/stats        → { total_stores, total_events_24h, total_alerts_24h, active_cameras }
GET    /dashboard/recent        → [ event ]  (last 20 events across all stores)
```

### 5.4 WebSocket Events

```
WS /ws/feed/{camera_id}         → Real-time motion detection overlay data
WS /ws/alerts/{user_id}        → Real-time alert notifications pushed to owner
```

### 5.5 Request/Response Examples

**POST /stores**
```json
// Request
{
  "name": "QuickMart #42",
  "address": "123 Main St, Austin TX 78701",
  "latitude": 30.2672,
  "longitude": -97.7431
}

// Response 201
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "QuickMart #42",
  "address": "123 Main St, Austin TX 78701",
  "latitude": 30.2672,
  "longitude": -97.7431,
  "owner_id": "user-uuid",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**GET /events?store_id=...&event_type=shoplifting_suspected&date_range=24h**
```json
// Response 200
{
  "events": [
    {
      "id": "evt-uuid",
      "camera_id": "cam-uuid",
      "store_id": "store-uuid",
      "event_type": "shoplifting_suspected",
      "confidence": 0.87,
      "description": "Suspected shoplifting: person concealed item near exit",
      "thumbnail_path": "/thumbnails/evt-uuid.jpg",
      "created_at": "2024-01-15T14:22:31Z"
    }
  ],
  "pagination": {
    "total": 14,
    "page": 1,
    "per_page": 20
  }
}
```

**GET /events?event_type=restricted_area_breach&date_range=24h**
```json
// Response 200
{
  "events": [
    {
      "id": "evt-uuid-2",
      "camera_id": "cam-uuid-2",
      "store_id": "store-uuid",
      "event_type": "restricted_area_breach",
      "confidence": 0.91,
      "description": "Restricted area breach: unauthorized entry to cash room",
      "zone_type": "cash_room",
      "thumbnail_path": "/thumbnails/evt-uuid-2.jpg",
      "created_at": "2024-01-15T16:05:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "page": 1,
    "per_page": 20
  }
}
```

**GET /events?event_type=cash_register_theft&date_range=24h**
```json
// Response 200
{
  "events": [
    {
      "id": "evt-uuid-3",
      "camera_id": "cam-uuid-3",
      "store_id": "store-uuid",
      "event_type": "cash_register_theft",
      "confidence": 0.83,
      "description": "Cash register theft: unauthorized void without customer present",
      "zone_type": "point_of_sale",
      "register_id": "REG-003",
      "thumbnail_path": "/thumbnails/evt-uuid-3.jpg",
      "created_at": "2024-01-15T16:45:00Z"
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "per_page": 20
  }
}
```

---

## 6. Computer Vision Pipeline

### 6.1 Detection Stages

```
Raw Frame
    │
    ▼
┌─────────────────────┐
│ Preprocessing       │ ← Resize to 640x640, normalize, letterbox
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Object Detection    │ ← YOLOv8 (COCO classes: person, bag, box, etc.)
│ (YOLOv8n / YOLOv8s) │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │ person?     │──No──▶ discard
    │ bag near    │
    │ person?     │
    └──────┬──────┘
           │ Yes
           ▼
┌─────────────────────┐
│ Motion Tracking     │ ← ByteTrack / SORT algorithm
│ (Trajectory Build)  │   Track person across frames
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Behavior Analysis   │ ← Rule-based + ML heuristics
│                     │   - Approach + reach + conceal + exit pattern
│                     │   - Object left behind detection
│                     │   - Wrong-way movement (against traffic flow)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Alert Trigger       │ ← Confidence threshold (default: 0.75)
│                     │   Generate event if threshold met
└─────────────────────┘
```

### 6.2 Behavioral Rules (Loss Prevention Detection)

| Rule | Logic |
|------|-------|
| **Concealment** | Person + bag within 50px, bag goes behind body, person moves toward exit |
| **Trajectory Anomaly** | Person enters aisle, lingers > 15s, moves quickly toward exit |
| **Object Abandonment** | Object detected, no interaction > 60s, no pickup |
| **Wrong-Way Flow** | Person moves opposite to normal traffic direction near exit |
| **Multiple Person** | 2+ persons coordinate, one blocks camera/view |
| **Restricted Area Breach** | Person enters a camera-monitored restricted zone (staff room, cash room, back area, loading dock) without authorized credentials |
| **Cash Register Theft** | Employee performs unauthorized void/refund without customer present, or opens cash drawer without a sale transaction recorded, or lingers at register with no activity for > 2 min |

### 6.3 Detection Zones

Cameras support configurable ROI (Region of Interest) masks with typed zones:

**Zone Types:**
| Zone Type | Description | Alert Behavior |
|-----------|-------------|----------------|
| `retail_floor` | Normal customer area | Standard monitoring |
| `entrance` | Entry/exit point | Monitor for shoplifting exit patterns |
| `exit` | Checkout/exit zone | Focus on concealment + exit trajectory |
| `high_value` | Jewelry, electronics, etc. | Elevated sensitivity |
| `point_of_sale` | Cash register / POS checkout lane | Cash register theft detection (sweethearting, void fraud, drawer open without sale) |
| `staff_only` | Break room, stockroom | Restricted area breach if customer detected |
| `cash_room` | Safe, register cash | Restricted area breach + high priority |
| `back_room` | Storage, receiving | Restricted area breach if non-staff detected |
| `loading_dock` | Receiving area | Restricted area breach + vehicle tracking |
| `parking_lot` | Exterior lot | Vehicle movement anomalies, drive-offs |

- Define inclusion/exclusion per zone type
- Zone type `staff_only`, `cash_room`, `back_room`, `loading_dock` trigger `restricted_area_breach` events
- Zone type `point_of_sale` triggers `cash_register_theft` events when anomalous register behavior is detected
- Stored as JSON polygon coordinates with zone type labels in `cameras.config`
- Staff credential whitelist (badge swipe, PIN) can be configured per zone to suppress false alerts
- POS zone cameras should be positioned to capture both the register and the employee's hands

---

## 7. SMS Alert System

### 7.1 Twilio Integration

```
Alert Triggered
      │
      ▼
┌─────────────────────┐
│ Alert Manager       │
│ (fastapi-bg-tasks)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Twilio REST API     │
│ POST /messages      │
│ { to, body, media } │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Store alert record  │
│ (twilio_sid, status)│
└─────────────────────┘
```

### 7.2 SMS Message Format

```
🚨 Spevino LP-OS Alert
Store: QuickMart #42
Camera: Entrance
Event: Suspected shoplifting (87% confidence)
Time: 2:34 PM CST
View: https://dashboard.spevino.com/events/evt-uuid
```

For restricted area breaches:
```
🚨 Spevino LP-OS Alert
Store: QuickMart #42
Camera: Back Room
Event: Restricted area breach — cash room entry (91% confidence)
Time: 2:34 PM CST
View: https://dashboard.spevino.com/events/evt-uuid
```

For cash register theft:
```
🚨 Spevino LP-OS Alert
Store: QuickMart #42
Camera: Register 3 (Lane 3)
Event: Cash register theft — unauthorized void without customer (83% confidence)
Time: 2:34 PM CST
View: https://dashboard.spevino.com/events/evt-uuid
```

### 7.3 Alert Throttling
- Max 1 SMS per event (no duplicate sends)
- Max 10 SMS per store per hour (configurable)
- Cooldown: 60 seconds between SMS to same phone number

---

## 8. Hardware Considerations

### 8.1 Edge Processor (On-Premises)

For each store location:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i3 8th gen | Intel i5/i7 or AMD Ryzen 5 |
| RAM | 4 GB | 8–16 GB |
| Storage | 128 GB SSD | 256+ GB SSD (clip storage) |
| GPU | None (CPU inference) | NVIDIA T4 / RTX 3060 (real-time CV) |
| Network | 10 Mbps stable | 50+ Mbps |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

**Software Stack on Edge:**
- Docker + Docker Compose
- FFmpeg (stream decoding)
- OpenCV 4.x
- YOLOv8 model (onnxruntime for CPU, or TensorRT for GPU)
- Edge Agent: Python daemon managing camera streams and local inference

### 8.2 Cloud Infrastructure

| Component | Spec | Justification |
|-----------|------|---------------|
| API Server | 2 vCPU, 4 GB RAM | FastAPI + async I/O |
| CV Worker | 4 vCPU, 16 GB RAM + GPU | Batch inference jobs |
| Database | Turso (SQLite) | Managed, distributed, zero-ops |
| SMS | Twilio Pay-as-you-go | $0.01–0.05 per SMS |

### 8.3 IP Camera Requirements

| Spec | Requirement |
|------|-------------|
| Protocol | RTSP (required) |
| Resolution | 720p minimum, 1080p recommended |
| Framerate | 15 FPS minimum |
| Night Vision | Required for 24h stores/gas stations |
| fisheye lens support | If applicable, with dewarping |

### 8.4 Network Architecture

```
Store Location
┌─────────────────────────────────────────┐
│  Router / Firewall                      │
│     │                                   │
│  ┌──┴──────────────────────┐           │
│  │ Edge Processor (Docker) │           │
│  │  - Stream grabber        │           │
│  │  - CV inference          │◀─────────┼──── IP Cameras (RTSP)
│  │  - Local clip storage    │           │
│  └───────────┬─────────────┘           │
│              │ HTTPS (TLS)              │
└──────────────┼──────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │  Cloud API   │
        │  (FastAPI)   │
        └──────────────┘
               │
               ▼
        ┌──────────────┐
        │  Web Dashboard│
        │  (Next.js)    │
        └──────────────┘
```

---

## 9. System Security

### 9.1 Authentication & Authorization
- Passwords hashed with bcrypt (cost factor 12)
- JWT with RS256 signatures
- Role-based access control: `owner` (own store only), `admin` (all stores)

### 9.2 Camera Stream Security
- RTSP credentials stored encrypted at rest
- TLS required for all API communication
- Camera config not exposed in API responses (redacted)

### 9.3 Data Privacy
- Video clips auto-deleted after 72 hours (configurable)
- Thumbnails retained for alert history
- No facial recognition (person detection only)

---

## 10. Scalability

### 10.1 Horizontal Scaling
- API servers stateless → scale behind load balancer
- CV workers pull from Redis queue → add workers as needed
- WebSocket connections sticky per user via session affinity

### 10.2 Multi-Tenant Considerations
- Tenant isolation enforced at database level
- Store ID scoping on all queries
- Rate limiting per tenant

### 10.3 Geographic Distribution
- Edge processor runs on-prem (low latency camera access)
- Cloud API region: US-East (default), EU-West (future)
- Turso replicates globally for DB access

---

## 11. Deployment Architecture

### 11.1 Docker Services

```yaml
# docker-compose.yml (per store / edge node)
services:
  edge-agent:
    image: spevino/edge-agent:latest
    devices:
      - /dev/video0  # if local camera
    volumes:
      - ./config:/app/config
      - ./clips:/app/clips
    environment:
      - API_BASE_URL=https://api.spevino.com
      - STORE_ID=uuid
      - CAMERA_IDS=c1,c2,c3

  # Cloud services (separate docker-compose)
  api:
    image: spevino/api:latest
    ports:
      - "8000:8000"

  cv-worker:
    image: spevino/cv-worker:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 11.2 CI/CD Pipeline
- GitHub Actions: lint → test → build → push to ECR/Docker Hub
- Docker image tags: `latest`, `v1.2.3`, `sha-abc123`
- Blue-green deployments for API

---

## 12. Future Considerations

| Feature | Priority | Notes |
|---------|----------|-------|
| Facial recognition | Low | Not planned — privacy concern |
| License plate detection | Medium | For gas station drive-off detection |
| Audio anomaly detection | Medium | Glass break, shouting detection |
| Apple Push Notifications | Low | iOS app integration |
| Multi-language SMS | Low | Spanish, etc. |
| Custom detection models | Medium | Customer-trained models for unique merchandise |

---

## 13. Summary

| Concern | Decision |
|---------|----------|
| **CV Framework** | YOLOv8 + OpenCV + PyTorch |
| **Backend** | FastAPI (Python) |
| **Database** | SQLite + Turso |
| **SMS** | Twilio |
| **Dashboard** | Next.js 14 + React |
| **Real-time** | WebSocket |
| **Edge** | Docker + FFmpeg |
| **Auth** | JWT (RS256) |
| **Deployment** | Docker + Docker Compose |

This architecture is designed for modularity — each component can be updated or scaled independently. The edge processor keeps camera traffic local (low bandwidth to cloud), while the cloud handles analysis coordination, alert dispatch, and the dashboard.