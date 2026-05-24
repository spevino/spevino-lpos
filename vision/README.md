# Spevino Vision - Computer Vision Detection Pipeline

Computer vision pipeline for real-time shoplifting detection in retail stores and gas stations.

## Architecture

The pipeline follows the detection stages defined in Section 6 of the Spevino architecture:

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

## Components

### detector.py
YOLOv8-based object detector. Detects COCO classes relevant to shoplifting:
- `person` (class_id=0)
- `bag`, `backpack`, `suitcase` (class_id=24-27)
- `box` (class_id=23)
- Other objects of interest

### tracker.py
ByteTrack-based multi-object tracker. Tracks detected objects across frames to build trajectories for behavior analysis.

### analyzer.py
Behavior analyzer implementing shoplifting detection rules:

| Rule | Logic | Threshold |
|------|-------|-----------|
| **Concealment** | Person + bag within 50px, bag goes behind body, person moves toward exit | 0.75 |
| **Trajectory Anomaly** | Person lingers > 15s, moves quickly toward exit | 0.75 |
| **Object Abandonment** | Object detected, no interaction > 60s | 0.75 |
| **Wrong-Way Flow** | Person moves opposite to normal traffic direction near exit | 0.75 |
| **Coordinated Persons** | 2+ persons in close proximity, one potentially blocking | 0.75 |

### pipeline.py
Main detection pipeline that orchestrates all components. Supports:
- Frame processing
- RTSP stream ingestion
- Video file processing
- Configurable detection zones

### events.py
Event output handler that formats and outputs detection events for the backend system.

## Installation

```bash
pip install -r requirements.txt
```

Core dependencies:
- `ultralytics>=8.0.0` - YOLOv8 object detection
- `opencv-python>=4.8.0` - Video processing
- `numpy>=1.24.0` - Numerical operations

## Usage

### Python API

```python
from vision import DetectionPipeline, PipelineConfig, EventOutput

# Configure pipeline
config = PipelineConfig(
    camera_id="camera-1",
    confidence_threshold=0.75,
    yolo_model_size='n'
)

# Event handler for backend integration
event_output = EventOutput(
    camera_id="camera-1",
    store_id="store-1",
    on_event=lambda e: print(f"Event: {e.id}"),
    on_alert=lambda a: send_sms(a.to_sms_body())
)

# Create pipeline
pipeline = DetectionPipeline(
    config=config,
    on_alert=lambda event: event_output.emit_event(...)
)

# Process frames
import cv2
cap = cv2.VideoCapture("video.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    alerts, detections, tracks = pipeline.process_frame(frame)
    
    for alert in alerts:
        print(f"Alert: {alert.alert_type.value} ({alert.confidence:.2f})")
```

### CLI

```bash
# Process video file
python -m vision.cli --video sample.mp4

# Process with custom model
python -m vision.cli --video sample.mp4 --model s --threshold 0.8

# Webcam processing
python -m vision.cli --webcam

# RTSP stream
python -m vision.cli --rtsp rtsp://camera:554/stream --camera-id cam1
```

### Test Demo

```bash
python -m vision.test_pipeline
```

## Detection Zones

Detection zones (ROI - Region of Interest) can be configured to define:
- Exit areas
- Aisles
- High-value merchandise areas
- Staff-only areas (exclusion zones)

Zones are defined as polygon coordinates and stored in the `cameras.config` JSON field.

## Alert Types

| Alert Type | Event Type | Description |
|------------|------------|-------------|
| `CONCEALMENT` | `shoplifting_suspected` | Person concealed item near body |
| `TRAJECTORY_ANOMALY` | `shoplifting_suspected` | Lingered then quickly exited |
| `OBJECT_ABANDONMENT` | `object_left` | Unattended object left behind |
| `WRONG_WAY_FLOW` | `motion_anomaly` | Moving against traffic flow |
| `COORDINATED_PERSONS` | `shoplifting_suspected` | Multiple persons coordinating |

## Performance

| Model | Input Size | Inference Time (CPU) | mAP |
|-------|------------|---------------------|-----|
| YOLOv8n | 640x640 | ~20ms/frame | 52.7% |
| YOLOv8s | 640x640 | ~35ms/frame | 60.0% |
| YOLOv8m | 640x640 | ~70ms/frame | 67.5% |

Recommended: YOLOv8s for real-time CPU inference, YOLOv8m for GPU inference.

## File Structure

```
vision/
├── __init__.py          # Package exports
├── detector.py          # YOLOv8 object detector
├── tracker.py           # ByteTrack motion tracker
├── analyzer.py         # Behavior analysis rules
├── pipeline.py         # Main detection pipeline
├── events.py           # Event output handlers
├── cli.py              # Command-line interface
├── test_pipeline.py    # Test and demo scripts
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Integration with Backend

The pipeline outputs events in the format expected by the Spevino backend API:

```python
from events import EventOutput

output = EventOutput(
    api_base_url="http://localhost:8000/api/v1",
    camera_id="camera-uuid",
    store_id="store-uuid",
    on_event=send_to_backend,
    on_alert=send_sms
)
```

Events are automatically:
- Deduplicated (30s window)
- Rate-limited (10 events/minute max)
- Formatted for database insertion

## Configuration

Pipeline configuration options:

```python
PipelineConfig(
    camera_id="uuid",
    confidence_threshold=0.75,      # Alert threshold
    yolo_model_size='n',          # n, s, m, l, x
    track_buffer=30,              # Frames to keep lost tracks
    input_width=640,              # YOLO input width
    input_height=640,             # YOLO input height
    zones=[],                     # Detection zones
    entrance_direction=(1.0, 0.0), # Normal traffic flow
    alert_cooldown_seconds=5.0,   # Cooldown between alerts
    min_detection_interval_ms=100  # Minimum frame interval
)
```