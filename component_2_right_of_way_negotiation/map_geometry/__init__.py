"""Single authoritative operational reference for compiled map geometry."""

# Import IntersectionGeometryContext from .models for the operations below.
from .models import IntersectionGeometryContext
# Import INTERSECTION_GEOMETRY_STATUS, MANUAL_INTERSECTION_CENTER_CONFIGURED, MANUAL_NET_OFFSET_APPLICATION,
# IntersectionGeometryError, derive_intersection_geometry,... from .intersection_reference for the operations
# below.
from .intersection_reference import (
    INTERSECTION_GEOMETRY_STATUS, MANUAL_INTERSECTION_CENTER_CONFIGURED,
    MANUAL_NET_OFFSET_APPLICATION, IntersectionGeometryError,
    derive_intersection_geometry, get_intersection_geometry,
    is_position_in_approach_zone,
)

# Set __all__ to a list of name for name in the result of globals(); retain entries satisfying the negation of the
# result of name.startswith(the text '_').
__all__ = [name for name in globals() if not name.startswith("_")]

