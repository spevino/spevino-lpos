from license import license_manager
from fastapi import HTTPException, status
import crud

def has_feature(feature: str) -> bool:
    return license_manager.has_feature(feature)

def check_feature_access(feature: str):
    if not has_feature(feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature}' is not available in your current tier ({license_manager.tier}). Please upgrade."
        )

def check_store_limit():
    # For a single-tenant installation, we count all stores
    # In a multi-tenant one, we'd count stores for the current owner
    # Given license_manager is a global singleton, we'll follow the lead's instruction to check current_count
    # We'll use the total count of stores in the system for now, 
    # or if we want to be more specific, stores owned by the current user.
    # The lead said: can_add_store(current_count)
    # Let's see if we should count all or per user.
    # If the license is for the WHOLE OS instance, then all stores.
    all_stores = crud.team_db_execute("SELECT COUNT(*) as count FROM stores")
    current_count = all_stores[0]['count'] if all_stores else 0
    if not license_manager.can_add_store(current_count):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum number of stores reached for your tier ({license_manager.tier})."
        )

def check_camera_limit(store_id: str):
    cameras = crud.get_cameras(store_id)
    current_count = len(cameras)
    if not license_manager.can_add_camera(current_count):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum number of cameras reached for this store in your tier ({license_manager.tier})."
        )

EVENT_FEATURE_MAP = {
    'shoplifting_suspected': 'concealment_detection',
    'restricted_area_breach': 'restricted_area_detection',
    'cash_register_theft': 'register_theft_detection',
    'object_left': 'object_abandonment',
    'motion_anomaly': 'trajectory_detection' 
}

def check_event_type_access(event_type: str):
    feature = EVENT_FEATURE_MAP.get(event_type)
    if feature:
        check_feature_access(feature)
