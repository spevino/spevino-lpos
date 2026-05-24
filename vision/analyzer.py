"""
Behavior Analyzer for Spevino Surveillance
Implements rule-based and ML heuristics for shoplifting detection.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import numpy as np

from detector import Detection
from tracker import Track


class AlertType(Enum):
    """Types of alerts that can be generated."""
    CONCEALMENT = "concealment"
    TRAJECTORY_ANOMALY = "trajectory_anomaly"
    OBJECT_ABANDONMENT = "object_abandonment"
    WRONG_WAY_FLOW = "wrong_way_flow"
    COORDINATED_PERSONS = "coordinated_persons"
    RESTRICTED_AREA_BREACH = "restricted_area_breach"
    REGISTER_THEFT = "register_theft"


@dataclass
class Alert:
    """Represents a detected suspicious behavior."""
    alert_type: AlertType
    confidence: float
    description: str
    track_ids: List[int] = field(default_factory=list)
    detection_ids: List[int] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert alert to dictionary for event creation."""
        return {
            "alert_type": self.alert_type.value,
            "confidence": self.confidence,
            "description": self.description,
            "track_ids": self.track_ids,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass 
class DetectionZone:
    """Defines a detection zone (ROI) for a camera."""
    name: str
    polygon: List[Tuple[int, int]]  # List of (x, y) points
    zone_type: str  # 'entrance', 'exit', 'aisle', 'high_value'
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the polygon using ray casting."""
        n = len(self.polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside


class BehaviorAnalyzer:
    """
    Analyzes tracked objects for suspicious shoplifting behaviors.
    
    Implements detection rules:
    1. Concealment: Person + bag within proximity, bag goes behind body, moves toward exit
    2. Trajectory Anomaly: Lingers in aisle >15s, moves quickly toward exit
    3. Object Abandonment: Object detected, no interaction >60s
    4. Wrong-Way Flow: Moves opposite to normal traffic direction
    5. Coordinated Persons: 2+ persons coordinate suspicious activity
    """
    
    # Thresholds
    CONCEALMENT_PROXIMITY_PX = 50  # pixels
    CONCEALMENT_BAG_BEHIND_THRESHOLD = 0.6  # bag position confidence
    LINGER_TIME_SECONDS = 15
    QUICK_EXIT_VELOCITY = 15  # pixels per frame at 30fps
    ABANDONMENT_TIME_SECONDS = 60
    COORDINATION_TIME_SECONDS = 10
    
    def __init__(
        self,
        zones: List[DetectionZone] = None,
        entrance_direction: Tuple[float, float] = (1.0, 0.0),  # Normal traffic flow
        confidence_threshold: float = 0.75
    ):
        """
        Initialize behavior analyzer.
        
        Args:
            zones: List of detection zones (ROI polygons)
            entrance_direction: Normal traffic flow direction vector
            confidence_threshold: Minimum confidence to trigger alert
        """
        self.zones = zones or []
        self.entrance_direction = entrance_direction
        self.confidence_threshold = confidence_threshold
        
        # Track history for temporal analysis
        self._track_history: Dict[int, deque] = {}
        self._object_history: deque = deque(maxlen=100)  # Recently detected objects
        self._coordinated_groups: Dict[int, List[int]] = {}  # track_id -> group member ids
        self._last_alert_time: Dict[AlertType, datetime] = {}
        
        # Cooldown between alerts of same type
        self._alert_cooldown = timedelta(seconds=5)
    
    def analyze(
        self,
        tracks: Dict[int, Track],
        detections: List[Detection],
        frame_timestamp: datetime = None
    ) -> List[Alert]:
        """
        Analyze current frame for suspicious behaviors.
        
        Args:
            tracks: Active tracks from tracker
            detections: Detections from current frame
            frame_timestamp: Current frame timestamp
            
        Returns:
            List of Alert objects for detected suspicious behaviors
        """
        if frame_timestamp is None:
            frame_timestamp = datetime.now()
        
        alerts = []
        
        # Update track history
        self._update_history(tracks, frame_timestamp)
        
        # Run each behavior detection rule
        alerts.extend(self._detect_concealment(tracks, frame_timestamp))
        alerts.extend(self._detect_trajectory_anomaly(tracks, frame_timestamp))
        alerts.extend(self._detect_object_abandonment(detections, frame_timestamp))
        alerts.extend(self._detect_wrong_way_flow(tracks, frame_timestamp))
        alerts.extend(self._detect_coordinated_persons(tracks, frame_timestamp))
        alerts.extend(self._detect_restricted_area_breach(tracks, frame_timestamp))
        alerts.extend(self._detect_register_theft(tracks, frame_timestamp))
        
        # Apply cooldown and threshold
        filtered_alerts = self._filter_alerts(alerts, frame_timestamp)
        
        return filtered_alerts
    
    def _update_history(self, tracks: Dict[int, Track], timestamp: datetime):
        """Update track history for temporal analysis."""
        for track_id, track in tracks.items():
            if track_id not in self._track_history:
                self._track_history[track_id] = deque(maxlen=120)  # ~4 seconds at 30fps
            
            self._track_history[track_id].append({
                'timestamp': timestamp,
                'position': track.latest_detection.center,
                'velocity': track.velocity,
                'bbox': track.latest_detection.bbox
            })
    
    def _detect_concealment(
        self,
        tracks: Dict[int, Track],
        timestamp: datetime
    ) -> List[Alert]:
        """
        Detect item concealment behavior.
        
        Rule: Person + bag within 50px proximity, bag goes behind body,
        person moves toward exit.
        """
        alerts = []
        
        # Get person tracks
        person_tracks = {
            tid: t for tid, t in tracks.items() 
            if t.class_id == 0 and len(t.trajectory) >= 2
        }
        
        # Get recent bags that aren't being tracked (static bags)
        recent_objects = list(self._object_history)
        
        for person_id, person_track in person_tracks.items():
            if len(person_track.trajectory) < 2:
                continue
            
            person_center = person_track.trajectory[-1]
            person_prev_center = person_track.trajectory[-2]
            
            # Calculate movement direction
            move_dir = (
                person_center[0] - person_prev_center[0],
                person_center[1] - person_prev_center[1]
            )
            
            # Check if moving toward exit (based on velocity direction)
            moving_toward_exit = move_dir[0] > 2  # Assuming exit is to the right
            
            if not moving_toward_exit:
                continue
            
            # Check for nearby objects that could be concealed
            # Look for bags in object history
            for obj_data in recent_objects[-10:]:  # Last 10 frames
                obj_center = obj_data['position']
                obj_class = obj_data.get('class_name', '')
                
                if 'bag' not in obj_class.lower() and 'box' not in obj_class.lower():
                    continue
                
                # Calculate distance
                dist = np.sqrt(
                    (person_center[0] - obj_center[0])**2 +
                    (person_center[1] - obj_center[1])**2
                )
                
                if dist < self.CONCEALMENT_PROXIMITY_PX:
                    # Check if object is now behind the person
                    # (object center is behind person based on movement direction)
                    object_behind = self._is_behind_person(
                        person_track.trajectory, obj_center
                    )
                    
                    if object_behind:
                        # Calculate confidence based on various factors
                        confidence = min(0.95, 0.5 + 0.3 * (1 - dist/50) + 0.2 * moving_toward_exit)
                        
                        if confidence >= self.confidence_threshold:
                            alerts.append(Alert(
                                alert_type=AlertType.CONCEALMENT,
                                confidence=confidence,
                                description=f"Person {person_id} concealed item near body and moving toward exit",
                                track_ids=[person_id],
                                metadata={
                                    "distance_px": dist,
                                    "object_type": obj_class
                                }
                            ))
        
        return alerts
    
    def _is_behind_person(self, trajectory: List[Tuple], obj_center: Tuple) -> bool:
        """Check if object position is behind person based on movement."""
        if len(trajectory) < 3:
            return False
        
        # Recent movement direction
        recent = trajectory[-1]
        prev = trajectory[-3]
        
        move_dir = (recent[0] - prev[0], recent[1] - prev[1])
        
        # Object is "behind" if it's in the opposite direction of movement
        # relative to the person's center
        obj_offset = (obj_center[0] - recent[0], obj_center[1] - recent[1])
        
        # Dot product negative means object is behind
        dot = move_dir[0] * obj_offset[0] + move_dir[1] * obj_offset[1]
        
        return dot < -10  # Object is behind person
    
    def _detect_trajectory_anomaly(
        self,
        tracks: Dict[int, Track],
        timestamp: datetime
    ) -> List[Alert]:
        """
        Detect trajectory anomaly (lingering + quick exit).
        
        Rule: Person enters aisle, lingers > 15s, moves quickly toward exit.
        """
        alerts = []
        
        for track_id, track in tracks.items():
            if track.class_id != 0:
                continue
            
            history = self._track_history.get(track_id, [])
            if len(history) < 30:  # Need at least 1 second at 30fps
                continue
            
            # Calculate total time in scene
            first_entry = history[0]['timestamp']
            duration = (timestamp - first_entry).total_seconds()
            
            if duration < self.LINGER_TIME_SECONDS:
                continue
            
            # Check for quick exit (sudden velocity increase toward exit)
            recent_velocities = [h['velocity'] for h in history[-10:]]
            avg_velocity = np.mean(recent_velocities, axis=0)
            velocity_magnitude = np.sqrt(avg_velocity[0]**2 + avg_velocity[1]**2)
            
            if velocity_magnitude < self.QUICK_EXIT_VELOCITY:
                continue
            
            # Check if moving toward exit (rightward in standard layout)
            moving_right = avg_velocity[0] > 5
            
            if moving_right and velocity_magnitude > self.QUICK_EXIT_VELOCITY:
                confidence = min(0.95, 0.6 + 0.2 * (duration / 60))
                
                if confidence >= self.confidence_threshold:
                    alerts.append(Alert(
                        alert_type=AlertType.TRAJECTORY_ANOMALY,
                        confidence=confidence,
                        description=f"Person {track_id} lingered {duration:.0f}s then quickly moved toward exit",
                        track_ids=[track_id],
                        metadata={
                            "linger_duration_s": duration,
                            "exit_velocity": velocity_magnitude
                        }
                    ))
        
        return alerts
    
    def _detect_object_abandonment(
        self,
        detections: List[Detection],
        timestamp: datetime
    ) -> List[Alert]:
        """
        Detect object abandonment.
        
        Rule: Object detected, no interaction > 60s, no pickup.
        """
        alerts = []
        
        # Update object history with current detections
        for det in detections:
            if det.class_id not in {0}:  # Not a person
                self._object_history.append({
                    'timestamp': timestamp,
                    'position': det.center,
                    'class_id': det.class_id,
                    'class_name': det.class_name,
                    'bbox': det.bbox
                })
        
        # Check for abandoned objects
        now = timestamp
        abandoned = []
        
        for i, obj in enumerate(list(self._object_history)):
            age = (now - obj['timestamp']).total_seconds()
            
            if age > self.ABANDONMENT_TIME_SECONDS:
                # Check if object still exists (not picked up)
                still_present = False
                for det in detections:
                    if self._compute_distance(det.center, obj['position']) < 30:
                        still_present = True
                        break
                
                if not still_present and obj not in abandoned:
                    abandoned.append(obj)
        
        for obj in abandoned:
            confidence = min(0.9, 0.5 + 0.2 * (age / 300))
            
            if confidence >= self.confidence_threshold:
                alerts.append(Alert(
                    alert_type=AlertType.OBJECT_ABANDONMENT,
                    confidence=confidence,
                    description=f"Unattended object ({obj['class_name']}) left for {age:.0f}s",
                    metadata={
                        "object_type": obj['class_name'],
                        "abandoned_duration_s": age,
                        "last_position": obj['position']
                    }
                ))
        
        return alerts
    
    def _detect_wrong_way_flow(
        self,
        tracks: Dict[int, Track],
        timestamp: datetime
    ) -> List[Alert]:
        """
        Detect wrong-way movement against normal traffic flow.
        
        Rule: Person moves opposite to normal traffic direction near exit.
        """
        alerts = []
        
        # Normalize entrance direction
        norm = np.sqrt(sum(d**2 for d in self.entrance_direction))
        if norm > 0:
            normal_dir = tuple(d/norm for d in self.entrance_direction)
        else:
            normal_dir = (1.0, 0.0)
        
        for track_id, track in tracks.items():
            if track.class_id != 0:
                continue
            
            if len(track.trajectory) < 3:
                continue
            
            # Calculate current movement direction
            recent = track.trajectory[-1]
            prev = track.trajectory[-3]
            
            move_dir = (recent[0] - prev[0], recent[1] - prev[1])
            norm_move = np.sqrt(move_dir[0]**2 + move_dir[1]**2)
            
            if norm_move < 3:  # Not moving enough
                continue
            
            move_dir = tuple(m/norm_move for m in move_dir)
            
            # Dot product: negative = opposite direction
            dot = sum(m * n for m, n in zip(move_dir, normal_dir))
            
            if dot < -0.5:  # Moving opposite to normal flow
                # Check if near exit zone
                near_exit = False
                for zone in self.zones:
                    if zone.zone_type == 'exit' and zone.contains_point(*recent):
                        near_exit = True
                        break
                
                if near_exit or not self.zones:  # If no zones defined, alert anyway
                    confidence = min(0.85, 0.6 - 0.3 * dot)  # Higher confidence for stronger opposite movement
                    
                    if confidence >= self.confidence_threshold:
                        alerts.append(Alert(
                            alert_type=AlertType.WRONG_WAY_FLOW,
                            confidence=confidence,
                            description=f"Person {track_id} moving against normal traffic flow near exit",
                            track_ids=[track_id],
                            metadata={
                                "movement_direction": move_dir,
                                "normal_direction": normal_dir
                            }
                        ))
        
        return alerts
    
    def _detect_coordinated_persons(
        self,
        tracks: Dict[int, Track],
        timestamp: datetime
    ) -> List[Alert]:
        """
        Detect coordinated activity between multiple persons.
        
        Rule: 2+ persons coordinate, one blocks camera/view.
        """
        alerts = []
        
        person_tracks = [t for tid, t in tracks.items() if t.class_id == 0]
        
        if len(person_tracks) < 2:
            return alerts
        
        # Check for persons in close proximity (potential blocking)
        for i, person1 in enumerate(person_tracks):
            for person2 in person_tracks[i+1:]:
                dist = self._compute_distance(
                    person1.latest_detection.center,
                    person2.latest_detection.center
                )
                
                # Persons very close (within 80px) might be blocking
                if dist < 80:
                    # Check if one is behind the other (blocking view)
                    if self._is_blocking_view(person1, person2):
                        confidence = min(0.88, 0.5 + 0.2 * (1 - dist/80))
                        
                        if confidence >= self.confidence_threshold:
                            alerts.append(Alert(
                                alert_type=AlertType.COORDINATED_PERSONS,
                                confidence=confidence,
                                description=f"Coordinated activity: persons {person1.track_id} and {person2.track_id} in close proximity",
                                track_ids=[person1.track_id, person2.track_id],
                                metadata={
                                    "distance_px": dist
                                }
                            ))
        
        return alerts
    
    def _is_blocking_view(self, track1: Track, track2: Track) -> bool:
        """Check if one person is blocking another's view of camera."""
        # Simple heuristic: if one person is directly between other and camera center
        # Camera center assumed at top-center of frame
        cam_center = (640, 0)  # Assume 640x480 or 1280x720
        
        # Calculate if track2 is between track1 and camera
        p1 = track1.latest_detection.center
        p2 = track2.latest_detection.center
        
        # Vector from p1 to camera
        v1 = (cam_center[0] - p1[0], cam_center[1] - p1[1])
        # Vector from p1 to p2
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        
        # Cross product to determine if p2 is between p1 and camera
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        
        return abs(cross) < 5000  # Threshold for "in between"
    
    def _compute_distance(self, p1: Tuple, p2: Tuple) -> float:
        """Compute Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _detect_restricted_area_breach(self, tracks: Dict[int, Track], timestamp: datetime) -> List[Alert]:
        """Detect persons entering restricted zones (staff_only, cash_room, back_room, loading_dock)."""
        alerts = []
        restricted_types = {'staff_only', 'cash_room', 'back_room', 'loading_dock'}
        restricted_zones = [z for z in self.zones if z.zone_type in restricted_types]
        if not restricted_zones:
            return alerts
        
        for track_id, track in tracks.items():
            if track.class_id != 0:
                continue
            center = track.latest_detection.center
            for zone in restricted_zones:
                if zone.contains_point(center[0], center[1]):
                    alerts.append(Alert(
                        alert_type=AlertType.RESTRICTED_AREA_BREACH,
                        confidence=min(0.95, 0.7 + 0.02 * track.frame_count),
                        description=f"Person {track_id} entered restricted zone: {zone.name}",
                        track_ids=[track_id],
                        metadata={'zone_name': zone.name, 'zone_type': zone.zone_type}
                    ))
        return alerts
    
    def _detect_register_theft(self, tracks: Dict[int, Track], timestamp: datetime) -> List[Alert]:
        """Detect suspicious activity at point_of_sale zones (cash register theft)."""
        alerts = []
        pos_zones = [z for z in self.zones if z.zone_type == 'point_of_sale']
        if not pos_zones:
            return alerts
        
        for track_id, track in tracks.items():
            if track.class_id != 0:
                continue
            center = track.latest_detection.center
            for zone in pos_zones:
                if zone.contains_point(center[0], center[1]) and track.frame_count > 30:
                    alerts.append(Alert(
                        alert_type=AlertType.REGISTER_THEFT,
                        confidence=0.8,
                        description=f"Suspicious activity at {zone.name}",
                        track_ids=[track_id],
                        metadata={'zone_name': zone.name}
                    ))
        return alerts
    
    def _filter_alerts(self, alerts: List[Alert], timestamp: datetime) -> List[Alert]:
        """Filter alerts based on cooldown and confidence threshold."""
        filtered = []
        
        for alert in alerts:
            # Check confidence threshold
            if alert.confidence < self.confidence_threshold:
                continue
            
            # Check cooldown
            last_time = self._last_alert_time.get(alert.alert_type)
            if last_time and (timestamp - last_time) < self._alert_cooldown:
                continue
            
            filtered.append(alert)
            self._last_alert_time[alert.alert_type] = timestamp
        
        return filtered
    
    def add_zone(self, zone: DetectionZone):
        """Add a detection zone."""
        self.zones.append(zone)
    
    def clear_zones(self):
        """Clear all detection zones."""
        self.zones = []
    
    def set_entrance_direction(self, direction: Tuple[float, float]):
        """Set the normal traffic flow direction."""
        self.entrance_direction = direction