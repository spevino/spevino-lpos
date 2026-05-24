# Spevino LP-OS Camera Integration Guide
## Connecting any RTSP-capable camera system

### Compatible Cameras
Spevino works with **any camera that supports RTSP** (Real-Time Streaming Protocol):

| Brand | Protocol | Notes |
|-------|----------|-------|
| **Hikvision** | `rtsp://user:pass@ip:554/Streaming/Channels/101` | ONVIF compatible |
| **Dahua** | `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0` | ONVIF compatible |
| **Reolink** | `rtsp://user:pass@ip:554/h264Preview_01_main` | |
| **Amcrest** | `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0` | |
| **Axis** | `rtsp://user:pass@ip:554/axis-media/media.amp` | |
| **Ubiquiti** | `rtsp://user:pass@ip:554/video` | |
| **Generic ONVIF** | `rtsp://user:pass@ip:554/onvif1` | |
| **USBCam / Webcam** | `0` (device index) | Direct connect |
| **Video File** | `/path/to/video.mp4` | For testing |

### Minimum Requirements
- **Resolution:** 720p (1280x720), 1080p recommended
- **Framerate:** 15 FPS minimum
- **Protocol:** RTSP over TCP
- **Night Vision:** Required for 24h stores/gas stations

### Recommended Camera Placements

```
                    STORE LAYOUT
┌─────────────────────────────────────────┐
│  [CAM 1] ← Entrance                    │
│                                         │
│  Aisle 1     Aisle 2     Aisle 3       │
│  [CAM 2]     [CAM 3]     [CAM 4]       │
│                                         │
│  Staff Only          [CAM 5 ← Registers]│
│  [CAM 6]             ═══║═══║═══       │
│  ───────────         Checkout          │
│  Back Room                              │
│  [CAM 7]                                │
└─────────────────────────────────────────┘
```

| Camera | Location | Focus | Detection Zones |
|--------|----------|-------|-----------------|
| CAM 1 | Entrance | Who comes in/out | `entrance`, `exit` |
| CAM 2-4 | Aisles | Customer behavior | `retail_floor`, `high_value` |
| CAM 5 | Checkout | Cash register | `point_of_sale` |
| CAM 6 | Staff area | Restricted access | `staff_only` |
| CAM 7 | Back room | Restricted access | `back_room`, `loading_dock` |

### Adding a Camera

**Via Dashboard:**
1. Go to Stores → Select your store
2. Click "Add Camera"
3. Enter: Name, RTSP URL, Location Hint
4. Draw detection zones on the preview
5. Save

**Via API:**
```bash
curl -X POST http://localhost:8000/stores/{store_id}/cameras \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Entrance Camera",
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",
    "location_hint": "entrance",
    "config": "{\"zones\":[{\"name\":\"Door\",\"polygon\":[[100,100],[200,100],[200,300],[100,300]],\"zone_type\":\"entrance\"}]}"
  }'
```

### Detection Zone Configuration

Zones are JSON polygons. Each zone has a type that determines what the system watches for:

```json
{
  "zones": [
    {
      "name": "Front Door",
      "polygon": [[100,100], [300,100], [300,400], [100,400]],
      "zone_type": "entrance"
    },
    {
      "name": "Register 1",
      "polygon": [[400,200], [500,200], [500,350], [400,350]],
      "zone_type": "point_of_sale"
    },
    {
      "name": "Staff Office",
      "polygon": [[600,50], [750,50], [750,200], [600,200]],
      "zone_type": "staff_only"
    }
  ]
}
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to camera" | Check RTSP URL format, ensure camera is on same network, verify credentials |
| "No detections" | Check camera angle, increase confidence threshold, ensure zones are configured |
| "Too many false alerts" | Increase confidence threshold (>0.85), tighten detection zones |
| "Stream disconnects" | Camera may need RTSP over TCP (add `?tcp` to URL), check network stability |
| "Low FPS" | Reduce resolution on camera settings, use substream for analysis |