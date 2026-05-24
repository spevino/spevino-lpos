# Provisional Patent Draft: P3
## Title: Multi-Zone Behavioral Theft Detection System for Retail Loss Prevention

### 1. Field of the Invention
The present invention relates to computer vision based retail loss prevention, and more specifically to a system that uses polygon-defined detection zones with typed classifications to detect and differentiate between customer theft (shoplifting) and employee theft (cash register theft, restricted area access) in a single unified system.

### 2. Background of the Invention
Retail loss prevention has traditionally treated customer theft (shoplifting) and employee theft (internal theft) as separate problems requiring separate systems. Customer theft is addressed by electronic article surveillance (EAS) tags and security guards. Employee theft is addressed by audits and inventory controls. No existing system uses a single camera-based platform to detect both types of theft simultaneously using zone-based behavioral analysis.

### 3. Summary of the Invention
The invention comprises a zone-based detection system that assigns typed classifications to polygon-defined regions of interest within a camera's field of view. Each zone type triggers specific behavioral detection rules. The system can simultaneously detect customers concealing merchandise (using retail_floor and entrance zones) and employees stealing from registers (using point_of_sale zones) or entering restricted areas (using staff_only, cash_room, back_room, and loading_dock zones).

Key innovations include:
*   **Zone-Typed Behavioral Detection:** Each polygon zone has a type that determines which behavioral rules apply within it, allowing a single camera to monitor multiple theft modalities simultaneously.
*   **Unified Customer+Employee Theft Platform:** The same system, hardware, and pipeline detect both external theft (shoplifting) and internal theft (employee theft) without separate configurations.
*   **Polygon-Based Contains-Point Geometry:** Uses ray-casting algorithm for efficient point-in-polygon testing to determine if a detected person is within a zone boundary.
*   **Multi-Camera Zone Configuration:** Zones are stored as JSON polygon coordinates in camera configuration, enabling per-camera detection zone customization.

### 4. Detailed Technical Description

#### 4.1 Zone Architecture
Each camera supports one or more detection zones. A zone is defined as a JSON object containing:
- `name`: Human-readable zone identifier (e.g., "Register 1", "Back Office Door")
- `polygon`: Array of (x, y) coordinate pairs defining the zone boundary
- `zone_type`: Classification determining behavioral rules

#### 4.2 Zone Types and Behaviors

| Zone Type | Description | Detection Behavior |
|-----------|-------------|-------------------|
| `retail_floor` | Normal customer area | Standard monitoring, concealment detection |
| `entrance` | Entry/exit point | Exit pattern monitoring for shoplifting |
| `exit` | Checkout/exit zone | Focused concealment + exit trajectory detection |
| `high_value` | Jewelry, electronics | Elevated sensitivity for concealment |
| `point_of_sale` | Cash register / POS | Cash register theft detection (employee) |
| `staff_only` | Break room, stockroom | Restricted area breach detection |
| `cash_room` | Safe, register cash | Restricted area breach + high priority alerting |
| `back_room` | Storage, receiving | Restricted area breach |
| `loading_dock` | Receiving area | Restricted area breach + vehicle tracking |
| `parking_lot` | Exterior lot | Vehicle movement anomalies |

#### 4.3 Point-in-Polygon Detection
The system uses the ray-casting algorithm to determine if a person's center point (x, y) falls within a zone polygon:

```python
def contains_point(x, y, polygon):
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside
```

#### 4.4 Restricted Area Breach Detection
When a tracked person's center point is detected inside any restricted zone type (staff_only, cash_room, back_room, loading_dock), the system generates a RESTRICTED_AREA_BREACH alert with confidence proportional to the time the person has been tracked (frames in scene). This provides a natural grace period for authorized employees who may briefly pass through a restricted zone entrance.

Confidence formula: `min(0.95, 0.7 + 0.02 * frame_count)`

#### 4.5 Cash Register Theft Detection
When a tracked person is detected inside a point_of_sale zone and their frame count exceeds a threshold (>30 frames, approximately 1 second at 30fps), the system generates a REGISTER_THEFT alert. The system can differentiate between:
- Customer-present scenario (person on opposite side of register = likely legitimate transaction) — lower confidence
- Employee-only scenario (person behind register with no customer present) — higher confidence
- Multiple rapid reach events into the register zone — highest suspicion

#### 4.6 Zone Configuration and Camera Placement
Zones are configured per camera and stored in the camera's config JSON field. Recommended camera placements for optimal zone coverage:
- POS cameras: Positioned to capture both the register drawer and the employee's hands
- Entrance cameras: Wide angle covering door and immediate interior
- Staff area cameras: Positioned at entry points to restricted zones
- High-value cameras: Close-up on merchandise displays

### 5. Claims (Informal)
1. A multi-zone theft detection system comprising a video camera, a computer vision processor, and a plurality of polygon-defined detection zones, each zone having a typed classification that determines which behavioral detection rules apply within its boundaries.
2. The system of Claim 1, wherein the typed classifications include a restricted zone type (staff_only, cash_room, back_room, loading_dock) that triggers a restricted area breach alert when a person track is detected within the zone polygon.
3. The system of Claim 1, wherein the typed classifications include a point_of_sale zone type that triggers a cash register theft alert when a person track is detected within the zone for longer than a threshold duration.
4. The method of Claim 1, wherein the system detects both external theft (customer shoplifting) and internal theft (employee theft) using a single unified video processing pipeline by applying different behavioral rules to different zone types.
5. The method of Claim 2, wherein restricted area breach detection includes a frame-count-based grace period that suppresses alerts for persons briefly passing through a restricted zone boundary.
6. The method of Claim 3, wherein cash register theft detection differentiates between customer-present scenarios (lower confidence) and employee-only scenarios (higher confidence) based on the relative positions of tracked persons within the point_of_sale zone.
7. The system of Claim 1, wherein zone polygons are stored as JSON coordinate arrays in camera configuration, enabling per-camera customization of detection zones without modifying the core detection pipeline.
8. The method of Claim 1, wherein the point-in-polygon test uses a ray-casting algorithm to efficiently determine person-zone intersection in real-time video processing.
9. The system of Claim 1, wherein zone types are extensible and new zone types can be added with corresponding behavioral rules without modifying the core zone detection infrastructure.
10. The system of Claim 1, wherein the same camera can simultaneously monitor multiple zone types, enabling a single camera to detect both shoplifting in retail areas and theft in restricted areas.