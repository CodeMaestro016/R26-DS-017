"""Single authoritative operational reference for compiled map geometry."""

from .models import IntersectionGeometryContext
from .intersection_reference import (
    INTERSECTION_GEOMETRY_STATUS, MANUAL_INTERSECTION_CENTER_CONFIGURED,
    MANUAL_NET_OFFSET_APPLICATION, IntersectionGeometryError,
    derive_intersection_geometry, get_intersection_geometry,
    is_position_in_approach_zone,
)

__all__ = [name for name in globals() if not name.startswith("_")]

