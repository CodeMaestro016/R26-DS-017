"""Immutable value objects used by the conflict package."""

from dataclasses import asdict, dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class MovementPath:
    path_id: str
    incoming_lane_id: str
    outgoing_lane_id: str
    manoeuvre: str
    centerline_geometry: Tuple[Tuple[float, float], ...]
    internal_lane_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ConflictRelationship:
    first_path_id: str
    second_path_id: str
    conflict_zone_id: Optional[str]
    conflict_type: str
    physical_overlap: bool = False
    coordinated_conflict: bool = False
    geometry_type: Optional[str] = None


@dataclass(frozen=True)
class LocalConflictGraph:
    ego_id: str
    timestamp: float
    ego_path_id: Optional[str]
    nodes: Tuple[str, ...]
    edges: Tuple[dict, ...]
    diagnostics: Tuple[dict, ...]
    metrics: dict
    changes: Tuple[dict, ...] = ()

    def to_dict(self):
        return asdict(self)
