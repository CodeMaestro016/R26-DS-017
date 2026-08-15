"""Immutable authoritative compiled-map geometry contracts."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple


@dataclass(frozen=True)
class IntersectionGeometryContext:
    network_identity: str
    junction_id: str
    center_xy: Tuple[float, float]
    coordinate_frame: str
    net_offset: Tuple[float, float]
    converted_boundary: Tuple[float, float, float, float]
    original_boundary: Tuple[float, float, float, float]
    projection_parameter: str
    derivation_method: str
    movement_path_ids_used: Tuple[str, ...]
    provenance: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))

