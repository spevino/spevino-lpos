"""
CV Detection Pipeline for Spevino Surveillance
Orchestrates detection, tracking, and behavior analysis for shoplifting detection.
"""

from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
import numpy as np
import logging

from detector import YOLODetector, Detection
from tracker import ByteTrackTracker, Track, TrackState
from analyzer import BehaviorAnalyzer, Alert, AlertType, DetectionZone

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    """State of the detection pipeline."""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class PipelineEvent:
    """Event emitted by the pipeline."""
    event_id: str
    camera_id: str
    event_type: str  # 'shoplifting_suspected', 'motion_anomaly', 'object_left'
    confidence: float
    description: str
    track_ids: List[int] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    thumbnail: Optional[bytes] = None
    clip_path: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "description": self.description,
            "track_ids": self.track_ids,
            "timestamp": self.timestamp.isoformat(),
            "thumbnail": self.thumbnail,
            "clip_path": self.clip_path,
            "metadata": self.metadata
        }


@dataclass
class PipelineConfig:
    """Configuration for the detection pipeline."""
    camera_id: str = "default"
    confidence_threshold: float = 0.75
    yolo_model_size: str = 'n'  # n, s, m, l, x
    track_buffer: int = 30
    input_width: int = 640
    input_height: int = 640
    zones: List[Dict] = field(default_factory=list)
    entrance_direction: Tuple[float, float] = (1.0, 0.0)
    alert_cooldown_seconds: float = 5.0
    min_detection_interval_ms: int = 100  # Min time between detection calls


class DetectionPipeline:
    """
    Main CV detection pipeline for shoplifting detection.
    
    Processes video frames through:
    1. Preprocessing (resize, normalize, letterbox)
    2. Object Detection (YOLOv8)
    3. Motion Tracking (ByteTrack)
    4. Behavior Analysis (Rule-based + ML heuristics)
    5. Alert Generation
    """
    
    def __init__(
        self,
        config: PipelineConfig = None,
        on_alert: Optional[Callable[[PipelineEvent], None]] = None
    ):
        """
        Initialize the detection pipeline.
        
        Args:
            config: Pipeline configuration
            on_alert: Callback function called when an alert is generated
        """
        self.config = config or PipelineConfig()
        self.on_alert = on_alert
        
        self.state = PipelineState.IDLE
        
        # Initialize components
        self._detector: Optional[YOLODetector] = None
        self._tracker: Optional[ByteTrackTracker] = None
        self._analyzer: Optional[BehaviorAnalyzer] = None
        
        self._initialized = False
        self._last_detection_time = 0
        
        # Alert tracking
        self._alert_history: List[Alert] = []
        self._last_alert_time: Dict[AlertType, datetime] = {}
        
        # Statistics
        self._stats = {
            "frames_processed": 0,
            "total_detections": 0,
            "alerts_generated": 0,
            "processing_time_ms": 0
        }
    
    def initialize(self):
        """Initialize all pipeline components."""
        if self._initialized:
            return
        
        logger.info("Initializing detection pipeline...")
        
        # Initialize detector
        self._detector = YOLODetector(
            model_size=self.config.yolo_model_size,
            confidence_threshold=self.config.confidence_threshold
        )
        
        # Initialize tracker
        self._tracker = ByteTrackTracker(
            track_buffer=self.config.track_buffer
        )
        
        # Initialize analyzer with zones
        zones = []
        for zone_data in self.config.zones:
            zones.append(DetectionZone(
                name=zone_data.get("name", "zone"),
                polygon=zone_data.get("polygon", []),
                zone_type=zone_data.get("type", "general")
            ))
        
        self._analyzer = BehaviorAnalyzer(
            zones=zones,
            entrance_direction=self.config.entrance_direction,
            confidence_threshold=self.config.confidence_threshold
        )
        
        self._initialized = True
        self.state = PipelineState.IDLE
        
        logger.info("Detection pipeline initialized successfully")
    
    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: Optional[datetime] = None
    ) -> Tuple[List[Alert], List[Detection], Dict[int, Track]]:
        """
        Process a single video frame through the detection pipeline.
        
        Args:
            frame: Input frame as numpy array (H, W, C)
            timestamp: Optional timestamp for the frame
            
        Returns:
            Tuple of (alerts, detections, tracks)
        """
        if not self._initialized:
            self.initialize()
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.state = PipelineState.PROCESSING
        start_time = time.time()
        
        try:
            # Step 1: Preprocess - resize to YOLO input size
            processed_frame = self._preprocess(frame)
            
            # Step 2: Object Detection
            detections = self._detector.detect(processed_frame)
            
            # Map detections back to original frame coordinates
            detections = self._map_to_original_frame(detections, frame.shape)
            
            # Step 3: Motion Tracking
            tracks = self._tracker.update(detections, timestamp)
            
            # Assign track IDs to detections
            for det in detections:
                for track_id, track in tracks.items():
                    if track.latest_detection.class_id == det.class_id:
                        # Check IOU for match
                        if self._compute_iou(det.bbox, track.latest_detection.bbox) > 0.5:
                            det.track_id = track_id
                            break
            
            # Step 4: Behavior Analysis
            alerts = self._analyzer.analyze(tracks, detections, timestamp)
            
            # Step 5: Generate pipeline events from alerts
            for alert in alerts:
                self._handle_alert(alert, timestamp)
            
            # Update statistics
            self._stats["frames_processed"] += 1
            self._stats["total_detections"] += len(detections)
            self._stats["alerts_generated"] += len(alerts)
            self._stats["processing_time_ms"] += (time.time() - start_time) * 1000
            
            self.state = PipelineState.IDLE
            
            return alerts, detections, tracks
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            self.state = PipelineState.ERROR
            raise
    
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for YOLO input.
        
        Applies letterbox resize to maintain aspect ratio.
        """
        target_size = self.config.input_width
        
        h, w = frame.shape[:2]
        scale = target_size / max(h, w)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize frame
        import cv2
        resized = cv2.resize(frame, (new_w, new_h))
        
        # Create letterboxed frame (black borders)
        letterboxed = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        
        x_offset = (target_size - new_w) // 2
        y_offset = (target_size - new_h) // 2
        
        letterboxed[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return letterboxed
    
    def _map_to_original_frame(
        self,
        detections: List[Detection],
        original_shape: Tuple[int, int, int]
    ) -> List[Detection]:
        """
        Map detection coordinates from letterboxed to original frame.
        
        Note: For simplicity, we return detections as-is. In production,
        you would reverse the letterbox transformation.
        """
        return detections
    
    def _compute_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """Compute Intersection over Union between two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Intersection
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Union
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0
        
        return inter_area / union_area
    
    def _handle_alert(self, alert: Alert, timestamp: datetime):
        """Handle a generated alert."""
        # Check cooldown
        last_time = self._last_alert_time.get(alert.alert_type)
        if last_time:
            cooldown = timedelta(seconds=self.config.alert_cooldown_seconds)
            if timestamp - last_time < cooldown:
                return
        
        # Map alert type to event type
        event_type_map = {
            AlertType.CONCEALMENT: "shoplifting_suspected",
            AlertType.TRAJECTORY_ANOMALY: "shoplifting_suspected",
            AlertType.OBJECT_ABANDONMENT: "object_left",
            AlertType.WRONG_WAY_FLOW: "motion_anomaly",
            AlertType.COORDINATED_PERSONS: "shoplifting_suspected",
            AlertType.RESTRICTED_AREA_BREACH: "restricted_area_breach",
            AlertType.REGISTER_THEFT: "cash_register_theft"
        }
        
        event_type = event_type_map.get(alert.alert_type, "motion_anomaly")
        
        # Create pipeline event
        import uuid
        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            camera_id=self.config.camera_id,
            event_type=event_type,
            confidence=alert.confidence,
            description=alert.description,
            track_ids=alert.track_ids,
            timestamp=timestamp,
            metadata=alert.metadata
        )
        
        self._last_alert_time[alert.alert_type] = timestamp
        self._alert_history.append(alert)
        
        # Call alert callback
        if self.on_alert:
            try:
                self.on_alert(event)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.info(f"Alert generated: {alert.alert_type.value} ({alert.confidence:.2f}) - {alert.description}")
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics."""
        stats = self._stats.copy()
        if stats["frames_processed"] > 0:
            stats["avg_processing_time_ms"] = stats["processing_time_ms"] / stats["frames_processed"]
        else:
            stats["avg_processing_time_ms"] = 0
        return stats
    
    def reset_statistics(self):
        """Reset pipeline statistics."""
        self._stats = {
            "frames_processed": 0,
            "total_detections": 0,
            "alerts_generated": 0,
            "processing_time_ms": 0
        }
    
    def pause(self):
        """Pause the pipeline."""
        self.state = PipelineState.PAUSED
    
    def resume(self):
        """Resume the pipeline."""
        if self._initialized:
            self.state = PipelineState.IDLE
    
    def add_zone(self, zone: DetectionZone):
        """Add a detection zone to the analyzer."""
        if self._analyzer:
            self._analyzer.add_zone(zone)
    
    def set_entrance_direction(self, direction: Tuple[float, float]):
        """Set the normal traffic flow direction."""
        if self._analyzer:
            self._analyzer.set_entrance_direction(direction)


class VideoProcessor:
    """
    Video stream processor that handles frame capture and processing.
    
    Supports:
    - RTSP stream ingestion
    - Video file processing
    - Webcam input
    """
    
    def __init__(
        self,
        pipeline: DetectionPipeline,
        stream_url: Optional[str] = None,
        video_file: Optional[str] = None
    ):
        """
        Initialize video processor.
        
        Args:
            pipeline: Detection pipeline to use
            stream_url: RTSP stream URL (for IP cameras)
            video_file: Path to video file (for testing)
        """
        self.pipeline = pipeline
        self.stream_url = stream_url
        self.video_file = video_file
        
        self._capture = None
        self._running = False
        self._thread = None
    
    def start_rtsp(self, on_frame: Callable[[np.ndarray, datetime], None]):
        """
        Start processing RTSP stream.
        
        Args:
            on_frame: Callback for each processed frame
        """
        import cv2
        
        self._capture = cv2.VideoCapture(self.stream_url)
        if not self._capture.isOpened():
            raise ValueError(f"Failed to open RTSP stream: {self.stream_url}")
        
        self._running = True
        
        while self._running:
            ret, frame = self._capture.read()
            if not ret:
                break
            
            timestamp = datetime.now()
            
            try:
                alerts, detections, tracks = self.pipeline.process_frame(frame, timestamp)
                
                if alerts:
                    on_frame(frame, timestamp)
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
        
        self._capture.release()
    
    def process_video_file(
        self,
        output_callback: Optional[Callable[[PipelineEvent], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[PipelineEvent]:
        """
        Process a video file and return all events.
        
        Args:
            output_callback: Called for each event
            progress_callback: Called with progress (0.0 - 1.0)
            
        Returns:
            List of pipeline events
        """
        import cv2
        
        events = []
        
        self._capture = cv2.VideoCapture(self.video_file)
        if not self._capture.isOpened():
            raise ValueError(f"Failed to open video file: {self.video_file}")
        
        total_frames = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self._capture.get(cv2.CAP_PROP_FPS)
        
        frame_idx = 0
        
        while self._running or True:
            ret, frame = self._capture.read()
            if not ret:
                break
            
            timestamp = datetime.now()
            
            try:
                alerts, detections, tracks = self.pipeline.process_frame(frame, timestamp)
                
                for alert in alerts:
                    event_type_map = {
                        AlertType.CONCEALMENT: "shoplifting_suspected",
                        AlertType.TRAJECTORY_ANOMALY: "shoplifting_suspected",
                        AlertType.OBJECT_ABANDONMENT: "object_left",
                        AlertType.WRONG_WAY_FLOW: "motion_anomaly",
                        AlertType.COORDINATED_PERSONS: "shoplifting_suspected",
                        AlertType.RESTRICTED_AREA_BREACH: "restricted_area_breach",
                        AlertType.REGISTER_THEFT: "cash_register_theft"
                    }
                    
                    import uuid
                    event = PipelineEvent(
                        event_id=str(uuid.uuid4()),
                        camera_id=self.pipeline.config.camera_id,
                        event_type=event_type_map.get(alert.alert_type, "motion_anomaly"),
                        confidence=alert.confidence,
                        description=alert.description,
                        track_ids=alert.track_ids,
                        timestamp=timestamp,
                        metadata=alert.metadata
                    )
                    
                    events.append(event)
                    
                    if output_callback:
                        output_callback(event)
                        
            except Exception as e:
                logger.error(f"Error processing frame {frame_idx}: {e}")
            
            frame_idx += 1
            
            if progress_callback and total_frames > 0:
                progress_callback(frame_idx / total_frames)
        
        self._capture.release()
        
        return events
    
    def stop(self):
        """Stop processing."""
        self._running = False