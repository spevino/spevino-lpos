"""
YOLOv8 Object Detector for Spevino Surveillance
Uses YOLOv8 for real-time object detection on video frames.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Detection:
    """Represents a detected object in a frame."""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    track_id: Optional[int] = None
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


class YOLODetector:
    """
    YOLOv8-based object detector.
    
    Supports detection of COCO classes relevant to shoplifting:
    - person (class_id=0)
    - bag (class_id=25, 26, 27)
    - backpack (class_id=24)
    - suitcase (class_id=28)
    - box (class_id=23)
    - bottle (class_id=39, 40, 41)
    """
    
    RELEVANT_CLASSES = {
        0: 'person',
        23: 'box',
        24: 'backpack',
        25: 'handbag',
        26: 'suitcase',
        27: 'handbag',
        28: 'suitcase',
        39: 'bottle',
        40: 'wine glass',
        41: 'cup',
        52: 'teddy bear',
        53: 'hair drier',
        54: 'toothbrush',
    }
    
    PERSON_CLASS_ID = 0
    BAG_CLASS_IDS = {24, 25, 26, 27}  # backpack, handbag, suitcase variants
    
    def __init__(
        self,
        model_size: str = 'n',  # n, s, m, l, x
        confidence_threshold: float = 0.5,
        device: Optional[str] = None
    ):
        """
        Initialize YOLOv8 detector.
        
        Args:
            model_size: Model variant ('n', 's', 'm', 'l', 'x')
            confidence_threshold: Minimum confidence for detections
            device: Device to run inference on ('cpu', 'cuda', etc.)
        """
        self.confidence_threshold = confidence_threshold
        
        # Lazy load to avoid import errors if ultralytics not installed
        self._model = None
        self._model_size = model_size
        self._device = device
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of the YOLOv8 model."""
        if self._initialized:
            return
            
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics package not installed. Install with: pip install ultralytics"
            )
        
        model_path = f'yolov8{self._model_size}.pt'
        self._model = YOLO(model_path)
        
        if self._device:
            self._model.to(self._device)
        
        self._initialized = True
    
    @property
    def model(self):
        """Get the YOLO model, initializing if needed."""
        if not self._initialized:
            self._initialize()
        return self._model
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run object detection on a video frame.
        
        Args:
            frame: Input frame as numpy array (H, W, C) in BGR or RGB format
            
        Returns:
            List of Detection objects for relevant classes
        """
        results = self.model(frame, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.xyxy[0][4])
                
                if class_id not in self.RELEVANT_CLASSES:
                    continue
                if confidence < self.confidence_threshold:
                    continue
                
                # Extract bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                
                detection = Detection(
                    class_id=class_id,
                    class_name=self.RELEVANT_CLASSES[class_id],
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2)
                )
                detections.append(detection)
        
        return detections
    
    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        """Filter detections to only persons."""
        detections = self.detect(frame)
        return [d for d in detections if d.class_id == self.PERSON_CLASS_ID]
    
    def detect_bags(self, frame: np.ndarray) -> List[Detection]:
        """Filter detections to only bags/personal items."""
        detections = self.detect(frame)
        return [d for d in detections if d.class_id in self.BAG_CLASS_IDS]
    
    def get_relevant_objects(self, frame: np.ndarray) -> Dict[str, List[Detection]]:
        """Get all relevant objects grouped by type."""
        detections = self.detect(frame)
        return {
            'persons': [d for d in detections if d.class_id == self.PERSON_CLASS_ID],
            'bags': [d for d in detections if d.class_id in self.BAG_CLASS_IDS],
            'objects': [d for d in detections if d.class_id not in {self.PERSON_CLASS_ID} | self.BAG_CLASS_IDS]
        }