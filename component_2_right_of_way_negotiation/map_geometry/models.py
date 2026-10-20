"""Immutable authoritative compiled-map geometry contracts."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define IntersectionGeometryContext to group the state and operations declared below.
# Declared fields: network_identity, junction_id, center_xy, coordinate_frame, net_offset, converted_boundary,
# original_boundary, projection_parameter, derivation_method, movement_path_ids_used, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class IntersectionGeometryContext:
    # Declare network_identity as str for this data structure.
    network_identity: str
    # Declare junction_id as str for this data structure.
    junction_id: str
    # Declare center_xy as Tuple[float, float] for this data structure.
    center_xy: Tuple[float, float]
    # Declare coordinate_frame as str for this data structure.
    coordinate_frame: str
    # Declare net_offset as Tuple[float, float] for this data structure.
    net_offset: Tuple[float, float]
    # Declare converted_boundary as Tuple[float, float, float, float] for this data structure.
    converted_boundary: Tuple[float, float, float, float]
    # Declare original_boundary as Tuple[float, float, float, float] for this data structure.
    original_boundary: Tuple[float, float, float, float]
    # Declare projection_parameter as str for this data structure.
    projection_parameter: str
    # Declare derivation_method as str for this data structure.
    derivation_method: str
    # Declare movement_path_ids_used as Tuple[str, ...] for this data structure.
    movement_path_ids_used: Tuple[str, ...]
    # Declare provenance as Mapping[str, str] for this data structure.
    provenance: Mapping[str, str]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))

