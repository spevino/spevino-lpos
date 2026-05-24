"""
Motion Tracker for Spevino Surveillance
Uses ByteTrack for multi-object tracking across video frames.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import numpy as np

from detector import Detection


@dataclass
class Track:
    """Represents a tracked object across frames."""
    track_id: int
    class_id: int
    class_name: str
    latest_detection: Detection
    trajectory: List[Tuple[float, float]] = field(default_factory=list)
    velocity: Tuple[float, float] = (0.0, 0.0)  # pixels per frame
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    frame_count: int = 0
    is_confirmed: bool = False
    
    @property
    def duration_seconds(self) -> float:
        """Time since first seen."""
        delta = self.latest_detection.timestamp if hasattr(self.latest_detection, 'timestamp') else self.frame_count
        return delta / 30.0  # Assume 30fps if no timestamp
    
    def update(self, detection: Detection):
        """Update track with new detection."""
        self.latest_detection = detection
        self.last_seen = datetime.now()
        self.frame_count += 1
        
        # Append center point to trajectory
        center = detection.center
        self.trajectory.append(center)
        
        # Keep trajectory limited
        if len(self.trajectory) > 60:  # ~2 seconds at 30fps
            self.trajectory.pop(0)
        
        # Update velocity based on last few positions
        if len(self.trajectory) >= 2:
            prev = self.trajectory[-2]
            curr = self.trajectory[-1]
            self.velocity = (curr[0] - prev[0], curr[1] - prev[1])


@dataclass
class TrackState:
    """Current state of all tracks."""
    tracks: Dict[int, Track] = field(default_factory=dict)
    frame_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class ByteTrackTracker:
    """
    ByteTrack-based multi-object tracker.
    
    ByteTrack is a multi-object tracker that uses a two-stage association
    approach with both high and low confidence detections.
    """
    
    def __init__(
        self,
        track_thresh: float = 0.5,
        track_buffer: int = 30,
        match_thresh: float = 0.8,
        min_box_area: int = 100,
        max_time_since_update: int = 30
    ):
        """
        Initialize ByteTrack tracker.
        
        Args:
            track_thresh: Detection confidence threshold for tracking
            track_buffer: Number of frames to keep lost tracks
            match_thresh: IOU threshold for matching detections to tracks
            min_box_area: Minimum bounding box area
            max_time_since_update: Max frames since last update before removal
        """
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.min_box_area = min_box_area
        self.max_time_since_update = max_time_since_update
        
        self._tracks: Dict[int, Track] = {}
        self._next_id = 1
        self._frame_count = 0
        self._tracked_classes = {0}  # Track persons by default
        
        # Initialize ByteTrack if available
        self._byte_tracker = None
        self._initialize_tracker()
    
    def _initialize_tracker(self):
        """Initialize the underlying ByteTrack implementation."""
        try:
            from bytetracker import BYTETracker as ByteTrackImpl
            self._byte_tracker = ByteTrackImpl(
                track_thresh=self.track_thresh,
                track_buffer=self.track_buffer,
                match_thresh=self.match_thresh,
                min_box_area=self.min_box_area
            )
        except ImportError:
            # Fall back to simple association tracker
            self._byte_tracker = None
    
    def update(self, detections: List[Detection], frame_timestamp: Optional[datetime] = None) -> Dict[int, Track]:
        """
        Update tracker with new detections from current frame.
        
        Args:
            detections: List of detections from current frame
            frame_timestamp: Optional timestamp for the frame
            
        Returns:
            Dictionary mapping track_id to Track objects
        """
        self._frame_count += 1
        
        if not detections:
            # No detections - mark all tracks as lost
            for track in self._tracks.values():
                track.lost_frames = getattr(track, 'lost_frames', 0) + 1
            return self._get_active_tracks()
        
        # Prepare detections in ByteTrack format if available
        if self._byte_tracker is not None:
            return self._update_bytetrack(detections)
        else:
            return self._update_simple(detections)
    
    def _update_bytetrack(self, detections: List[Detection]) -> Dict[int, Track]:
        """Update using ByteTrack implementation."""
        # Convert detections to ByteTrack format
        # ByteTrack expects (x1, y1, x2, y2, score, cls) for each detection
        dets = []
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            dets.append([
                x1, y1, x2, y2, det.confidence, det.class_id
            ])
        
        if not dets:
            return self._get_active_tracks()
        
        # Run ByteTrack
        # Note: Actual implementation depends on ByteTrack API
        # This is a simplified version
        tracked_stracks = []
        lost_stracks = []
        
        # Frame processing would happen here
        # The actual API call to ByteTrack would be:
        # tracked_stracks, lost_stracks = self._byte_tracker.update(np.array(dets))
        
        return self._get_active_tracks()
    
    def _update_simple(self, detections: List[Detection]) -> Dict[int, Track]:
        """Simple IOU-based association when ByteTrack unavailable."""
        # Build cost matrix based on IOU
        matched_tracks = set()
        
        for det in detections:
            best_iou = 0
            best_track_id = None
            
            # Find best matching track
            for track_id, track in self._tracks.items():
                if track_id in matched_tracks:
                    continue
                if track.class_id != det.class_id:
                    continue
                    
                iou = self._compute_iou(track.latest_detection.bbox, det.bbox)
                if iou > best_iou and iou > 0.3:  # IOU threshold
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                det.track_id = best_track_id
                self._tracks[best_track_id].update(det)
                matched_tracks.add(best_track_id)
            else:
                # Create new track
                track_id = self._next_id
                self._next_id += 1
                
                det.track_id = track_id
                self._tracks[track_id] = Track(
                    track_id=track_id,
                    class_id=det.class_id,
                    class_name=det.class_name,
                    latest_detection=det
                )
                self._tracks[track_id].trajectory.append(det.center)
        
        # Remove old tracks
        self._cleanup_tracks()
        
        return self._get_active_tracks()
    
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
    
    def _cleanup_tracks(self):
        """Remove tracks that haven't been updated recently."""
        to_remove = []
        
        for track_id, track in self._tracks.items():
            if hasattr(track, 'lost_frames') and track.lost_frames > self.max_time_since_update:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self._tracks[track_id]
    
    def _get_active_tracks(self) -> Dict[int, Track]:
        """Get only tracks that are actively being updated."""
        active = {}
        for track_id, track in self._tracks.items():
            lost_frames = getattr(track, 'lost_frames', 0)
            if lost_frames <= self.max_time_since_update:
                active[track_id] = track
        return active
    
    def get_person_tracks(self) -> Dict[int, Track]:
        """Get all active person tracks."""
        return {
            tid: track for tid, track in self._get_active_tracks().items()
            if track.class_id == 0
        }
    
    def get_track_state(self) -> TrackState:
        """Get current state of all tracks."""
        return TrackState(
            tracks=self._get_active_tracks(),
            frame_count=self._frame_count
        )