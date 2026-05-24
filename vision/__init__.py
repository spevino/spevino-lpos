"""
Spevino Vision Module
Computer Vision Detection Pipeline for Shoplifting Detection
"""

from detector import YOLODetector, Detection
from tracker import ByteTrackTracker, Track, TrackState
from analyzer import BehaviorAnalyzer, Alert, AlertType, DetectionZone
from pipeline import DetectionPipeline, PipelineConfig, PipelineState, PipelineEvent, VideoProcessor
from events import (
    EventOutput, 
    DetectionEvent, 
    AlertPayload, 
    EventType,
    WebhookOutput
)

__all__ = [
    # Detector
    "YOLODetector",
    "Detection",
    
    # Tracker
    "ByteTrackTracker",
    "Track",
    "TrackState",
    
    # Analyzer
    "BehaviorAnalyzer",
    "Alert",
    "AlertType",
    "DetectionZone",
    
    # Pipeline
    "DetectionPipeline",
    "PipelineConfig",
    "PipelineState",
    "PipelineEvent",
    "VideoProcessor",
    
    # Events
    "EventOutput",
    "DetectionEvent",
    "AlertPayload",
    "EventType",
    "WebhookOutput",
]

__version__ = "0.1.0"