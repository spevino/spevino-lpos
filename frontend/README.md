# Frontend Dashboard

**Owner:** Frontend Developer

## Overview
Next.js 14 (App Router) dashboard for store owners to monitor live camera feeds, view alert history, and manage store/camera configuration.

## Tech Stack
- **Framework:** Next.js 14 (React 18)
- **Styling:** Tailwind CSS 3.x
- **State:** Zustand (global) + React Query (server state)
- **Real-time:** WebSocket (native) for live alerts
- **HTTP:** Axios for REST API calls
- **Icons:** Lucide React
- **Charts:** Recharts (for dashboard stats)

## Structure
```
frontend/
├── app/
│   ├── (auth)/               # Auth route group (no layout sidebar)
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/             # Main authenticated layout
│   │   ├── page.tsx          # Overview with stats
│   │   ├── stores/
│   │   │   ├── page.tsx      # Store list
│   │   │   └── [store_id]/
│   │   │       ├── page.tsx  # Store detail
│   │   │       └── cameras/
│   │   ├── events/
│   │   │   └── page.tsx      # Event history
│   │   └── alerts/
│   │       └── page.tsx      # Alert management
│   ├── layout.tsx            # Root layout
│   └── globals.css
├── components/
│   ├── ui/                   # Shared UI components (Button, Card, etc.)
│   ├── cameras/
│   │   └── CameraGrid.tsx    # Live feed grid
│   ├── alerts/
│   │   └── AlertList.tsx    # Alert feed
│   └── dashboard/
│       └── StatCard.tsx     # Stats card
├── lib/
│   ├── api.ts                # Axios instance + API helpers
│   ├── ws.ts                # WebSocket client
│   ├── store.ts             # Zustand store
│   └── utils.ts
├── requirements.txt
├── Dockerfile
└── README.md (this file)
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | Email/password login |
| `/register` | Register | New user registration |
| `/dashboard` | Overview | Stats cards, recent events, active cameras |
| `/dashboard/stores` | Stores | List of user's stores |
| `/dashboard/stores/[id]` | Store Detail | Cameras, recent events for one store |
| `/dashboard/events` | Events | Filterable event history |
| `/dashboard/alerts` | Alerts | Alert history with retry for failed SMS |

## Key Features

- **Live Camera Grid** — Display multiple RTSP streams via HLS.js or MSE
- **Real-time Alert Feed** — WebSocket pushes new alerts to top of list
- **Event Timeline** — Chronological view with thumbnails and confidence scores
- **Store/Camera Management** — Add/edit cameras, detection zones
- **Stat Cards** — Total events (24h), active cameras, SMS success rate

## API Integration

All API calls go through `lib/api.ts`:
```typescript
// Example: fetch events
const { data } = await apiClient.get('/api/v1/events', {
  params: { store_id, event_type, date_range: '24h' }
})
```

WebSocket connection in `lib/ws.ts`:
```typescript
const ws = new WebSocket(`${WS_URL}/ws/alerts/${userId}`)
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data)
  // Push to Zustand store → update alert list
}
```

## Environment Variables
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Local Dev
```bash
npm install
npm run dev   # http://localhost:3000
```

## Docker
```bash
docker build -t spevino/frontend .
docker run -p 3000:3000 spevino/frontend
```

## Design Notes

- Uses **Tailwind CSS** — utility-first, no custom CSS unless necessary
- Dark mode ready (class-based `dark:` variants)
- All API errors shown via toast notifications (react-hot-toast)
- Responsive grid for camera feeds: 1 col mobile, 2 col tablet, 3+ col desktop