# Provisional Patent Draft: P1
## Title: Unified Loss Prevention Detection Engine for Retail Surveillance

### 1. Field of the Invention
The present invention relates to computer vision (CV) based surveillance and retail loss prevention, and more specifically to a unified detection engine that combines multiple behavioral analysis algorithms into a single video processing pipeline to detect shoplifting, theft, and suspicious activity in retail environments.

### 2. Background of the Invention
Retail theft costs the global economy over $100B annually. Existing surveillance systems rely on either passive recording (requiring human review) or single-purpose detection algorithms that only look for one type of behavior (e.g., loitering). These fragmented approaches miss coordinated theft, concealment, and rapid exit patterns that characterize modern retail crime. A unified system that simultaneously analyzes multiple behavioral signals is needed.

### 3. Summary of the Invention
The invention comprises a computer vision detection pipeline that processes video frames through five stages: (1) preprocessing, (2) object detection using a deep neural network, (3) multi-object tracking across frames, (4) parallel behavioral analysis using five distinct detection rules, and (5) alert generation with confidence scoring.

Key innovations include:
*   **Parallel Behavioral Rule Engine:** Simultaneously evaluates concealment detection, trajectory anomaly analysis, object abandonment detection, wrong-way flow detection, and coordinated persons detection on the same video stream.
*   **Temporal Track History:** Maintains a per-object trajectory history (up to 120 frames) to enable velocity and direction analysis for anomaly detection.
*   **Object-Centric Concealment Detection:** Tracks proximity between person tracks and object detections (bags, boxes) to detect when an item is concealed behind a person's body.
*   **Confidence-Based Alert Thresholding:** Multi-factor confidence scoring that weights detection confidence, behavioral pattern match, and cooldown period to reduce false positives.

### 4. Detailed Technical Description

#### 4.1 System Architecture
The system processes video frames in a sequential pipeline:

```
Raw Frame → Preprocessing (640x640 letterbox) → YOLOv8 Object Detection → ByteTrack Multi-Object Tracking → Parallel Behavior Analysis → Alert Generation
```

#### 4.2 Object Detection Layer
The system employs a YOLOv8 neural network trained on the COCO dataset, filtered to detect classes relevant to loss prevention: persons (class 0), bags/backpacks (classes 24-27), boxes (class 23), and other objects of interest (bottles, cups, etc.).

Detection output format: `{class_id, class_name, confidence, bbox(x1,y1,x2,y2), center_point}`

#### 4.3 Multi-Object Tracking Layer
The ByteTrack algorithm assigns unique track IDs to each detected person across frames. Each track maintains:
- A trajectory history (last 60 positions)
- A velocity vector (pixels per frame, updated every frame)
- A frame count (total frames tracked)
- First/last seen timestamps

#### 4.4 Behavioral Detection Rules

**Rule 1: Concealment Detection**
Detects when a person takes an object (bag, box) and conceals it behind their body while moving toward an exit.
- Person-bag proximity threshold: 50 pixels
- Bag-behind-body detection: dot product of movement direction vs. bag offset is negative (bag is behind direction of travel)
- Exit-directed movement: velocity x-component > 2 pixels/frame (assuming exit is rightward)
- Confidence formula: `min(0.95, 0.5 + 0.3*(1 - distance/50) + 0.2*moving_toward_exit)`

**Rule 2: Trajectory Anomaly Detection**
Detects when a person lingers in an area for >15 seconds and then moves rapidly toward an exit.
- Linger threshold: 15 seconds in scene
- Rapid exit velocity threshold: 15 pixels/frame
- Confidence formula: `min(0.95, 0.6 + 0.2*duration/60)`

**Rule 3: Object Abandonment Detection**
Detects when a non-person object remains stationary and unattended for >60 seconds.
- Abandonment threshold: 60 seconds
- Object presence verification: checks if object still exists in current frame within 30px radius
- Confidence formula: `min(0.9, 0.5 + 0.2*age/300)`

**Rule 4: Wrong-Way Flow Detection**
Detects when a person moves opposite to the normal traffic direction, particularly near exit zones.
- Normal traffic direction: configurable vector (default: rightward, (1.0, 0.0))
- Opposite movement: dot product of movement vector and normal direction < -0.5
- Exit zone proximity: uses polygon-based zone detection
- Confidence formula: `min(0.85, 0.6 - 0.3*dot_product)`

**Rule 5: Coordinated Persons Detection**
Detects when two or more persons are in close proximity in a pattern suggesting coordinated distraction or blocking.
- Proximity threshold: 80 pixels between person centers
- Blocking detection: cross product of camera-to-person vectors determines if one person is between another and the camera
- Confidence formula: `min(0.88, 0.5 + 0.2*(1 - distance/80))`

#### 4.5 Alert Cooldown and Deduplication
All alerts pass through a cooldown filter that prevents duplicate alerts of the same type within 5 seconds. Events are rate-limited to 10 per minute and deduplicated within a 30-second sliding window by event type and description hash.

### 5. Claims (Informal)
1. A unified loss prevention detection system comprising a video ingestion module, an object detection neural network, a multi-object tracker, and a parallel behavioral analysis engine that simultaneously evaluates multiple distinct theft-detection rules on the same video stream.
2. The system of Claim 1, wherein the behavioral analysis engine comprises rules for concealment detection, trajectory anomaly detection, object abandonment detection, wrong-way flow detection, and coordinated persons detection.
3. The method of Claim 2, wherein concealment detection comprises measuring proximity between a person track and an object detection, determining if the object is positioned behind the person relative to their direction of travel, and triggering an alert when the person is moving toward an exit.
4. The method of Claim 2, wherein trajectory anomaly detection comprises measuring total time a person is present in a scene, detecting a sudden increase in velocity toward an exit direction after a period of low movement, and generating an alert when velocity exceeds a threshold.
5. The method of Claim 2, wherein wrong-way flow detection comprises defining a normal traffic direction vector, computing a dot product of a person's movement vector with the normal direction, and generating an alert when the dot product falls below a negative threshold indicating movement in the opposite direction.
6. The method of Claim 2, wherein coordinated persons detection comprises measuring inter-person distances, computing camera-to-person geometry to determine if one person is blocking another from camera view, and generating an alert when blocking behavior is detected.
7. The system of Claim 1, further comprising a confidence scoring engine that combines detection confidence, behavioral pattern confidence, and temporal factors into a composite alert confidence score.
8. The system of Claim 1, further comprising an alert cooldown and deduplication engine that prevents duplicate alerts of the same type within a configurable time window.
9. The system of Claim 1, wherein the object detection neural network is a YOLO-family model filtered to detect loss-prevention-relevant object classes.
10. The method of Claim 2, wherein object abandonment detection comprises tracking non-person object detections across frames, measuring elapsed time since last human interaction, and generating an alert when elapsed time exceeds an abandonment threshold.