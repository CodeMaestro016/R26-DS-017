"""Fixed experiment ODD and deterministic SUMO-network validation."""

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class RegulatoryContext:
    profile_id: str = "DE_STVO_UNCONTROLLED_4WAY_V1"
    jurisdiction: str = "DE"
    traffic_side: str = "RIGHT_HAND"
    intersection_control: str = "UNSIGNALIZED"
    road_priority: str = "EQUAL_ORDINARY_ROADS"
    context_type: str = "UNCONTROLLED_EQUAL_PRIORITY"


def validate_network_odd(network_file, junction_id="center"):
    """Validate actual compiled-network facts; never repair the input."""
    path = Path(network_file)
    root = ET.parse(path).getroot()
    junction = next(
        (item for item in root.findall("junction") if item.get("id") == junction_id),
        None,
    )
    if junction is None:
        return {"passed": False, "errors": ("CENTRAL_JUNCTION_NOT_FOUND",),
                "junction_id": junction_id, "network_file": str(path)}
    junction_type = junction.get("type")
    left_hand = root.get("lefthand", "false").lower() == "true"
    incoming = tuple(lane for lane in junction.get("incLanes", "").split()
                     if lane and not lane.startswith(":"))
    checks = {
        "right_hand_network_confirmed": not left_hand,
        "unsignalized": junction_type not in {"traffic_light", "traffic_light_unregulated"},
        "right_before_left": junction_type == "right_before_left",
        "four_leg_intersection": len(incoming) == 4,
    }
    errors = tuple(name.upper() for name, passed in checks.items() if not passed)
    return {
        "passed": not errors, "errors": errors, "junction_id": junction_id,
        "junction_type": junction_type, "incoming_lanes": incoming,
        "network_file": str(path), **checks,
    }
