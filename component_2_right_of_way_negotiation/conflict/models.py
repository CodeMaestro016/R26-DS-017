"""Immutable value objects used by the conflict package."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MovementPath to group the state and operations declared below.
# Declared fields: path_id, incoming_lane_id, outgoing_lane_id, manoeuvre, centerline_geometry, internal_lane_ids.
# Construction and attribute behavior follow the declared decorators and base classes.
class MovementPath:
    # Declare path_id as str for this data structure.
    path_id: str
    # Declare incoming_lane_id as str for this data structure.
    incoming_lane_id: str
    # Declare outgoing_lane_id as str for this data structure.
    outgoing_lane_id: str
    # Declare manoeuvre as str for this data structure.
    manoeuvre: str
    # Declare centerline_geometry as Tuple[Tuple[float, float], ...] for this data structure.
    centerline_geometry: Tuple[Tuple[float, float], ...]
    # Set internal_lane_ids to an empty tuple; declare its type as Tuple[str, ...].
    internal_lane_ids: Tuple[str, ...] = ()


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ConflictRelationship to group the state and operations declared below.
# Declared fields: first_path_id, second_path_id, conflict_zone_id, conflict_type, physical_overlap,
# coordinated_conflict, geometry_type.
# Construction and attribute behavior follow the declared decorators and base classes.
class ConflictRelationship:
    # Declare first_path_id as str for this data structure.
    first_path_id: str
    # Declare second_path_id as str for this data structure.
    second_path_id: str
    # Declare conflict_zone_id as Optional[str] for this data structure.
    conflict_zone_id: Optional[str]
    # Declare conflict_type as str for this data structure.
    conflict_type: str
    # Set physical_overlap to False; declare its type as bool.
    physical_overlap: bool = False
    # Set coordinated_conflict to False; declare its type as bool.
    coordinated_conflict: bool = False
    # Set geometry_type to None; declare its type as Optional[str].
    geometry_type: Optional[str] = None


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define LocalConflictGraph to group the state and operations declared below.
# Declared fields: ego_id, timestamp, ego_path_id, nodes, edges, diagnostics, metrics, changes.
# Construction and attribute behavior follow the declared decorators and base classes.
class LocalConflictGraph:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare ego_path_id as Optional[str] for this data structure.
    ego_path_id: Optional[str]
    # Declare nodes as Tuple[str, ...] for this data structure.
    nodes: Tuple[str, ...]
    # Declare edges as Tuple[dict, ...] for this data structure.
    edges: Tuple[dict, ...]
    # Declare diagnostics as Tuple[dict, ...] for this data structure.
    diagnostics: Tuple[dict, ...]
    # Declare metrics as dict for this data structure.
    metrics: dict
    # Set changes to an empty tuple; declare its type as Tuple[dict, ...].
    changes: Tuple[dict, ...] = ()

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)
