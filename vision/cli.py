#!/usr/bin/env python3
"""
Spevino Vision CLI

Command-line interface for the computer vision detection pipeline.
Usage:
    python -m vision.cli --video tests/sample.mp4
    python -m vision.cli --rtsp rtsp://camera:554/stream
    python -m vision.cli --webcam
"""

import argparse
import logging
import sys
import cv2
from datetime import datetime
from pathlib import Path

from detector import YOLODetector, Detection
from tracker import ByteTrackTracker, Track
from analyzer import BehaviorAnalyzer, Alert, AlertType, DetectionZone
from pipeline import DetectionPipeline, PipelineConfig, VideoProcessor
from events import EventOutput, DetectionEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_video_file(
    video_path: str,
    camera_id: str = "test",
    confidence_threshold: float = 0.75,
    model_size: str = 'n',
    output_dir: str = None
):
    """
    Process a video file with the detection pipeline.
    
    Args:
        video_path: Path to input video file
        camera_id: Camera identifier
        confidence_threshold: Detection confidence threshold
        model_size: YOLO model size (n, s, m, l, x)
        output_dir: Optional directory for output files
    """
    logger.info(f"Processing video file: {video_path}")
    
    # Configure pipeline
    config = PipelineConfig(
        camera_id=camera_id,
        confidence_threshold=confidence_threshold,
        yolo_model_size=model_size
    )
    
    # Event handler
    events_output = EventOutput(
        camera_id=camera_id,
        store_id="test-store",
        on_event=lambda e: print(f"Event: {e.to_dict()}"),
        on_alert=lambda a: print(f"Alert: {a.to_sms_body()}")
    )
    
    # Create pipeline
    pipeline = DetectionPipeline(
        config=config,
        on_alert=lambda event: events_output.emit_event(
            event_type=event.event_type,
            confidence=event.confidence,
            description=event.description,
            metadata=event.metadata
        )
    )
    
    # Process video
    processor = VideoProcessor(pipeline=pipeline, video_file=video_path)
    
    def on_event(event):
        logger.info(f"Event: {event.event_type} ({event.confidence:.2f}) - {event.description}")
        
        # Draw on frame (for visualization)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = Path(output_dir) / f"{event.event_id[:8]}.json"
            import json
            with open(output_path, 'w') as f:
                json.dump(event.to_dict(), f, indent=2)
    
    events = processor.process_video_file(
        output_callback=on_event,
        progress_callback=lambda p: print(f"\rProgress: {p*100:.1f}%", end='', flush=True)
    )
    
    print(f"\n\nProcessing complete. Found {len(events)} events.")
    
    # Print statistics
    stats = pipeline.get_statistics()
    print(f"\nStatistics:")
    print(f"  Frames processed: {stats['frames_processed']}")
    print(f"  Total detections: {stats['total_detections']}")
    print(f"  Alerts generated: {stats['alerts_generated']}")
    print(f"  Avg processing time: {stats.get('avg_processing_time_ms', 0):.2f}ms/frame")
    
    return events


def process_webcam(camera_index: int = 0, model_size: str = 'n'):
    """
    Process webcam input with visualization.
    
    Args:
        camera_index: Webcam device index
        model_size: YOLO model size
    """
    logger.info(f"Starting webcam processing (camera {camera_index})")
    
    # Configure pipeline
    config = PipelineConfig(
        camera_id="webcam",
        confidence_threshold=0.75,
        yolo_model_size=model_size
    )
    
    pipeline = DetectionPipeline(config=config)
    pipeline.initialize()
    
    # Open webcam
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error(f"Cannot open webcam {camera_index}")
        return
    
    logger.info("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        timestamp = datetime.now()
        
        try:
            alerts, detections, tracks = pipeline.process_frame(frame, timestamp)
            
            # Draw detections on frame
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                color = (0, 255, 0) if det.class_name == 'person' else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{det.class_name} {det.confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )
            
            # Draw alerts
            for alert in alerts:
                cv2.putText(
                    frame,
                    f"ALERT: {alert.alert_type.value} ({alert.confidence:.2f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
                logger.info(f"Alert: {alert.alert_type.value} - {alert.description}")
            
            cv2.imshow("Spevino Vision", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
    
    cap.release()
    cv2.destroyAllWindows()


def process_rtsp_stream(
    rtsp_url: str,
    camera_id: str = "rtsp",
    model_size: str = 'n'
):
    """
    Process RTSP stream.
    
    Args:
        rtsp_url: RTSP stream URL
        camera_id: Camera identifier
        model_size: YOLO model size
    """
    logger.info(f"Starting RTSP stream processing: {rtsp_url}")
    
    config = PipelineConfig(
        camera_id=camera_id,
        yolo_model_size=model_size
    )
    
    pipeline = DetectionPipeline(config=config)
    
    processor = VideoProcessor(pipeline=pipeline, stream_url=rtsp_url)
    
    def on_frame(frame, timestamp):
        # Could add visualization here
        pass
    
    try:
        processor.start_rtsp(on_frame)
    except Exception as e:
        logger.error(f"RTSP processing error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Spevino Vision - Computer Vision Detection Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --video sample.mp4
  python cli.py --video sample.mp4 --model s --threshold 0.8
  python cli.py --webcam
  python cli.py --rtsp rtsp://camera:554/stream --camera-id cam1
        """
    )
    
    parser.add_argument(
        '--video',
        type=str,
        help='Path to video file for processing'
    )
    
    parser.add_argument(
        '--rtsp',
        type=str,
        help='RTSP stream URL'
    )
    
    parser.add_argument(
        '--webcam',
        action='store_true',
        help='Use webcam for processing'
    )
    
    parser.add_argument(
        '--camera-id',
        type=str,
        default='test',
        help='Camera identifier'
    )
    
    parser.add_argument(
        '--camera-index',
        type=int,
        default=0,
        help='Webcam device index (default: 0)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='n',
        choices=['n', 's', 'm', 'l', 'x'],
        help='YOLO model size (default: n)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.75,
        help='Detection confidence threshold (default: 0.75)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for events'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.video:
        process_video_file(
            video_path=args.video,
            camera_id=args.camera_id,
            confidence_threshold=args.threshold,
            model_size=args.model,
            output_dir=args.output_dir
        )
    elif args.webcam:
        process_webcam(
            camera_index=args.camera_index,
            model_size=args.model
        )
    elif args.rtsp:
        process_rtsp_stream(
            rtsp_url=args.rtsp,
            camera_id=args.camera_id,
            model_size=args.model
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()