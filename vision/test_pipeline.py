#!/usr/bin/env python3
"""
Spevino Vision - Test and Demo Script

Demonstrates the CV detection pipeline with mock data.
Does not require actual YOLOv8 model or video input.
"""

import numpy as np
import cv2
from datetime import datetime, timedelta
from typing import List, Tuple

from analyzer import Alert, AlertType


def create_mock_frame(width: int = 1280, height: int = 720) -> np.ndarray:
    """Create a mock video frame for testing."""
    frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    # Add some structure to make it look more like a store
    frame[:, :] = [240, 240, 240]  # Light gray background
    cv2.rectangle(frame, (100, 100), (500, 600), (200, 200, 200), -1)  # Shelf
    cv2.rectangle(frame, (700, 100), (1100, 600), (200, 200, 200), -1)  # Another shelf
    return frame


def create_mock_detections(frame_width: int = 1280, frame_height: int = 720) -> List:
    """
    Create mock detections for testing.
    
    Returns a list of mock Detection objects.
    """
    from detector import Detection, Detection as DetClass
    
    detections = []
    
    # Create 2 persons
    for i, (x, y) in enumerate([(400, 350), (800, 350)]):
        detections.append(DetClass(
            class_id=0,
            class_name='person',
            confidence=0.92,
            bbox=(x-30, y-80, x+30, y+80)
        ))
    
    # Create a bag near first person
    detections.append(DetClass(
        class_id=25,
        class_name='handbag',
        confidence=0.85,
        bbox=(380, 400, 420, 450)
    ))
    
    return detections


def create_mock_tracks() -> dict:
    """Create mock tracks for testing."""
    from tracker import Track
    from detector import Detection
    from datetime import datetime
    
    tracks = {}
    
    # Create track for person moving toward exit
    det1 = Detection(
        class_id=0,
        class_name='person',
        confidence=0.92,
        bbox=(400, 270, 460, 430)
    )
    
    track1 = Track(
        track_id=1,
        class_id=0,
        class_name='person',
        latest_detection=det1,
        trajectory=[
            (400, 350), (450, 350), (500, 350), (550, 350),
            (600, 350), (650, 350), (700, 350), (750, 350),
            (800, 350), (850, 350), (900, 350), (950, 350)
        ],
        velocity=(50, 0)  # Moving right toward exit
    )
    tracks[1] = track1
    
    # Create track for second person (static, lingers)
    det2 = Detection(
        class_id=0,
        class_name='person',
        confidence=0.89,
        bbox=(300, 270, 360, 430)
    )
    
    track2 = Track(
        track_id=2,
        class_id=0,
        class_name='person',
        latest_detection=det2,
        trajectory=[(300, 350)] * 12,  # Static position
        velocity=(0, 0)
    )
    tracks[2] = track2
    
    return tracks


def demo_behavior_analyzer():
    """Demonstrate the behavior analyzer with mock data."""
    from analyzer import BehaviorAnalyzer, DetectionZone
    
    print("=" * 60)
    print("Demo: Behavior Analyzer")
    print("=" * 60)
    
    # Create analyzer with zones
    exit_zone = DetectionZone(
        name="exit",
        polygon=[(1100, 0), (1280, 0), (1280, 720), (1100, 720)],
        zone_type="exit"
    )
    
    aisle_zone = DetectionZone(
        name="aisle1",
        polygon=[(100, 100), (500, 100), (500, 600), (100, 600)],
        zone_type="aisle"
    )
    
    analyzer = BehaviorAnalyzer(
        zones=[exit_zone, aisle_zone],
        entrance_direction=(1.0, 0.0),  # Normal traffic flows right
        confidence_threshold=0.75
    )
    
    # Test with mock tracks
    tracks = create_mock_tracks()
    detections = create_mock_detections()
    timestamp = datetime.now()
    
    # Update analyzer history for trajectory anomaly detection
    for track_id, track in tracks.items():
        for i, pos in enumerate(track.trajectory):
            # Manually populate history for testing
            pass
    
    # Run analysis
    alerts = analyzer.analyze(tracks, detections, timestamp)
    
    print(f"\nDetected {len(alerts)} alerts:")
    for alert in alerts:
        print(f"\n  Type: {alert.alert_type.value}")
        print(f"  Confidence: {alert.confidence:.2f}")
        print(f"  Description: {alert.description}")
        print(f"  Track IDs: {alert.track_ids}")
        print(f"  Metadata: {alert.metadata}")


def demo_pipeline():
    """Demonstrate the full pipeline (with mock detector output)."""
    from pipeline import PipelineConfig, DetectionPipeline, PipelineEvent
    from events import EventOutput, AlertPayload
    
    print("=" * 60)
    print("Demo: Full Detection Pipeline")
    print("=" * 60)
    
    # Configure
    config = PipelineConfig(
        camera_id="test-camera",
        confidence_threshold=0.75,
        yolo_model_size='n'
    )
    
    # Event handler
    events_output = EventOutput(
        camera_id="test-camera",
        store_id="test-store",
        on_event=lambda e: print(f"  -> Event recorded: {e.id}"),
        on_alert=lambda a: print(f"  -> SMS Alert: {a.to_sms_body()[:50]}...")
    )
    
    # Create pipeline
    pipeline = DetectionPipeline(config=config)
    
    # Note: We can't actually run process_frame without initializing the model
    # This would need the actual YOLOv8 weights to be downloaded
    
    print("\nPipeline configured but cannot process frames without YOLOv8 model.")
    print("To test with actual video, run:")
    print("  python -m vision.cli --video your_video.mp4")
    
    # Demonstrate event emission
    print("\nDemonstrating event emission:")
    event = events_output.emit_event(
        event_type="shoplifting_suspected",
        confidence=0.87,
        description="Person concealed item near exit",
        metadata={"test": True}
    )
    if event:
        print(f"  Event created: {event.id}")
        print(f"  Event type: {event.event_type}")


def demo_zone_point_check():
    """Demonstrate point-in-polygon detection."""
    from analyzer import DetectionZone
    
    print("=" * 60)
    print("Demo: Detection Zone Point Check")
    print("=" * 60)
    
    # Define a rectangular exit zone
    exit_zone = DetectionZone(
        name="exit",
        polygon=[(1000, 0), (1280, 0), (1280, 720), (1000, 720)],
        zone_type="exit"
    )
    
    # Test points
    test_points = [
        (1200, 360),  # Inside exit zone
        (500, 360),   # Outside exit zone
        (1000, 360),  # On boundary
        (640, 360),   # Center of frame
    ]
    
    print(f"\nExit zone polygon: {exit_zone.polygon}")
    print("\nPoint containment tests:")
    
    for x, y in test_points:
        inside = exit_zone.contains_point(x, y)
        status = "INSIDE" if inside else "OUTSIDE"
        print(f"  ({x}, {y}): {status}")


def demo_iou_calculation():
    """Demonstrate IOU calculation."""
    from tracker import ByteTrackTracker
    
    print("=" * 60)
    print("Demo: IOU Calculation")
    print("=" * 60)
    
    tracker = ByteTrackTracker()
    
    # Test IOU calculations
    bbox1 = (100, 100, 200, 200)
    bbox2 = (150, 150, 250, 250)
    bbox3 = (300, 300, 400, 400)
    
    iou12 = tracker._compute_iou(bbox1, bbox2)
    iou13 = tracker._compute_iou(bbox1, bbox3)
    iou23 = tracker._compute_iou(bbox2, bbox3)
    
    print(f"\nBBox1: {bbox1}")
    print(f"BBox2: {bbox2}")
    print(f"BBox3: {bbox3}")
    print(f"\nIOU(BBox1, BBox2): {iou12:.3f}")
    print(f"IOU(BBox1, BBox3): {iou13:.3f}")
    print(f"IOU(BBox2, BBox3): {iou23:.3f}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("SPEVINO VISION - Test and Demo Suite")
    print("=" * 60)
    
    try:
        demo_zone_point_check()
        print()
        
        demo_iou_calculation()
        print()
        
        demo_behavior_analyzer()
        print()
        
        demo_pipeline()
        print()
        
        print("=" * 60)
        print("All demos completed!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\nNote: Some demos require dependencies to be installed.")
        print(f"Install with: pip install -r requirements.txt")
        print(f"\nImport error: {e}")


if __name__ == "__main__":
    main()