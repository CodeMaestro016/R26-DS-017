"""Fixed experiment ODD and deterministic SUMO-network validation."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define RegulatoryContext to group the state and operations declared below.
# Declared fields: profile_id, jurisdiction, traffic_side, intersection_control, road_priority, context_type.
# Construction and attribute behavior follow the declared decorators and base classes.
class RegulatoryContext:
    # Set profile_id to the text 'DE_STVO_UNCONTROLLED_4WAY_V1'; declare its type as str.
    profile_id: str = "DE_STVO_UNCONTROLLED_4WAY_V1"
    # Set jurisdiction to the text 'DE'; declare its type as str.
    jurisdiction: str = "DE"
    # Set traffic_side to the text 'RIGHT_HAND'; declare its type as str.
    traffic_side: str = "RIGHT_HAND"
    # Set intersection_control to the text 'UNSIGNALIZED'; declare its type as str.
    intersection_control: str = "UNSIGNALIZED"
    # Set road_priority to the text 'EQUAL_ORDINARY_ROADS'; declare its type as str.
    road_priority: str = "EQUAL_ORDINARY_ROADS"
    # Set context_type to the text 'UNCONTROLLED_EQUAL_PRIORITY'; declare its type as str.
    context_type: str = "UNCONTROLLED_EQUAL_PRIORITY"


# Validate actual compiled-network facts; never repair the input.
# Input network_file: the supplied network file.
# Input junction_id: the supplied junction id.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def validate_network_odd(network_file, junction_id="center"):
    """Validate actual compiled-network facts; never repair the input."""
    # Set path to the result of Path(network_file).
    path = Path(network_file)
    # Set root to the result of ET.parse(path).getroot().
    root = ET.parse(path).getroot()
    # Set junction to the next item from a lazy sequence of item for item in the result of root.findall(the text
    # 'junction'); retain entries satisfying 'id' from item; use None if absent equals junction_id.
    junction = next(
        # Supply a lazy sequence of item for item in the result of root.findall(the text 'junction'); retain
        # entries satisfying 'id' from item; use None if absent equals junction_id to next.
        (item for item in root.findall("junction") if item.get("id") == junction_id),
        # Supply None to the enclosing expression.
        None,
    )
    # Run this branch when junction is the same object as None.
    if junction is None:
        # Return a dictionary containing passed, errors, junction_id, network_file to the caller.
        return {"passed": False, "errors": ("CENTRAL_JUNCTION_NOT_FOUND",),
                # Store junction_id under 'junction_id'.
                # Store a string built from path under 'network_file'.
                "junction_id": junction_id, "network_file": str(path)}
    # Set junction_type to 'type' from junction; use None if absent.
    junction_type = junction.get("type")
    # Set left_hand to the result of root.get('lefthand', 'false').lower() equals the text 'true'.
    left_hand = root.get("lefthand", "false").lower() == "true"
    # Set incoming to a tuple built from a lazy sequence of lane for lane in the result of
    # junction.get('incLanes', '').split(); retain entries satisfying lane and the negation of
    # lane.startswith(':').
    incoming = tuple(lane for lane in junction.get("incLanes", "").split()
                     # Evaluate lane and the negation of the result of lane.startswith(the text ':') as part of
                     # the enclosing expression.
                     if lane and not lane.startswith(":"))
    # Set checks to a dictionary containing right_hand_network_confirmed, unsignalized, right_before_left,
    # four_leg_intersection.
    checks = {
        # Store the negation of left_hand under 'right_hand_network_confirmed'.
        "right_hand_network_confirmed": not left_hand,
        # Store junction_type does not belong to a set containing the text 'traffic_light', the text
        # 'traffic_light_unregulated' under 'unsignalized'.
        "unsignalized": junction_type not in {"traffic_light", "traffic_light_unregulated"},
        # Store junction_type equals the text 'right_before_left' under 'right_before_left'.
        "right_before_left": junction_type == "right_before_left",
        # Store the number of entries in incoming equals 4 under 'four_leg_intersection'.
        "four_leg_intersection": len(incoming) == 4,
    }
    # Set errors to a tuple built from a lazy sequence of the result of name.upper() for (name, passed) in
    # key/value pairs from checks; retain entries satisfying the negation of passed.
    errors = tuple(name.upper() for name, passed in checks.items() if not passed)
    # Return a dictionary containing passed, errors, junction_id, junction_type, incoming_lanes, network_file to
    # the caller.
    return {
        # Store the negation of errors under 'passed'.
        # Store errors under 'errors'.
        # Store junction_id under 'junction_id'.
        "passed": not errors, "errors": errors, "junction_id": junction_id,
        # Store junction_type under 'junction_type'.
        # Store incoming under 'incoming_lanes'.
        "junction_type": junction_type, "incoming_lanes": incoming,
        # Store a string built from path under 'network_file'.
        "network_file": str(path), **checks,
    }
