"""Deterministic rolling one-front-vehicle-per-approach presentation demand."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PanelDemand to group the state and operations declared below.
# Declared fields: approach, movement_path_id, sequence_index, scheduled_departure_seconds.
# Construction and attribute behavior follow the declared decorators and base classes.
class PanelDemand:
    # Declare approach as str for this data structure.
    approach: str
    # Declare movement_path_id as str for this data structure.
    movement_path_id: str
    # Declare sequence_index as int for this data structure.
    sequence_index: int
    # Set scheduled_departure_seconds to 0.0; declare its type as float.
    scheduled_departure_seconds: float = 0.0


# Set APPROACH_PATHS to a dictionary containing N, E, S, W.
APPROACH_PATHS = {
    # Phase 1: E-left/N-left (rule-resolved).
    # Phase 2: E-straight/N-straight/S-right/W-left (training manifest MAPPO).
    # Phase 3: E-right/N-right/S-straight/W-right (rule-resolved).
    # Phase 4: S-left/W-straight (rule-resolved).
    # Store a tuple containing the text 'N_IN_0_LEFT', the text 'N_IN_0_STRAIGHT', the text 'N_IN_0_RIGHT' under
    # 'N'.
    "N": ("N_IN_0_LEFT", "N_IN_0_STRAIGHT", "N_IN_0_RIGHT"),
    # Store a tuple containing the text 'E_IN_0_LEFT', the text 'E_IN_0_STRAIGHT', the text 'E_IN_0_RIGHT' under
    # 'E'.
    "E": ("E_IN_0_LEFT", "E_IN_0_STRAIGHT", "E_IN_0_RIGHT"),
    # Store a tuple containing the text 'S_IN_0_RIGHT', the text 'S_IN_0_STRAIGHT', the text 'S_IN_0_LEFT' under
    # 'S'.
    "S": ("S_IN_0_RIGHT", "S_IN_0_STRAIGHT", "S_IN_0_LEFT"),
    # Store a tuple containing the text 'W_IN_0_LEFT', the text 'W_IN_0_RIGHT', the text 'W_IN_0_STRAIGHT' under
    # 'W'.
    "W": ("W_IN_0_LEFT", "W_IN_0_RIGHT", "W_IN_0_STRAIGHT"),
}

# Simultaneous admission with a fixed order; subsequent waves are admitted
# only after the prior wave clears all four rolling approach slots.
# Set INITIAL_ADMISSION_SECONDS to a dictionary containing N, E, S, W.
INITIAL_ADMISSION_SECONDS = {"N": 0.0, "E": 0.0, "S": 0.0, "W": 0.0}
# Set ADMISSION_ORDER to a tuple containing the text 'N', the text 'E', the text 'S', the text 'W'.
ADMISSION_ORDER = ("N", "E", "S", "W")
# Set ADMISSION_WAVES to a tuple containing a tuple containing the text 'N', the text 'E', a tuple containing the
# text 'N', the text 'E', the text...
ADMISSION_WAVES = (("N", "E"), ("N", "E", "S", "W"),
                   # Include a tuple containing the text 'N', the text 'E', the text 'S', the text 'W' in this
                   # tuple.
                   ("N", "E", "S", "W"), ("S", "W"))


# Use all 12 movements in four predeclared actor-safe phases.
# Output: a dictionary of approach mapped to a tuple built from a lazy sequence of the result of
# PanelDemand(approach, path, index) for (index, path) in index/value pairs from paths for (approach,...
def build_default_schedule():
    """Use all 12 movements in four predeclared actor-safe phases."""
    # Return a dictionary of approach mapped to a tuple built from a lazy sequence of the result of
    # PanelDemand(approach, path, index) for (index, path) in index/value pairs from paths for (approach, paths)
    # in key/value pairs from APPROACH_PATHS to the caller.
    return {approach: tuple(PanelDemand(approach, path, index)
                            # Evaluate index/value pairs from paths as part of the enclosing expression.
                            for index, path in enumerate(paths))
            # Evaluate key/value pairs from APPROACH_PATHS as part of the enclosing expression.
            for approach, paths in APPROACH_PATHS.items()}


# Validate schedule using the inputs and processing steps below.
# Input schedule: the supplied schedule.
# Output: schedule.
# Processing: select branches using the stated conditions.
def validate_schedule(schedule):
    # Set demands to a tuple built from a lazy sequence of item for rows in values from schedule.
    demands = tuple(item for rows in schedule.values() for item in rows)
    # Run this branch when a set built from schedule differs from a set built from APPROACH_PATHS.
    if set(schedule) != set(APPROACH_PATHS):
        # Raise ValueError with the text 'PANEL_SCHEDULE_APPROACH_SET_INVALID' to stop this execution path.
        raise ValueError("PANEL_SCHEDULE_APPROACH_SET_INVALID")
    # Run this branch when the number of entries in demands differs from 12 or the number of entries in a set of
    # x.movement_path_id for x in demands differs from 12.
    if len(demands) != 12 or len({x.movement_path_id for x in demands}) != 12:
        # Raise ValueError with the text 'PANEL_SCHEDULE_MUST_USE_12_UNIQUE_LEGAL_MOVEMENTS' to stop this
        # execution path.
        raise ValueError("PANEL_SCHEDULE_MUST_USE_12_UNIQUE_LEGAL_MOVEMENTS")
    # Run this branch when whether any item is true in a lazy sequence of item.approach differs from
    # item.movement_path_id at 0 for item in demands.
    if any(item.approach != item.movement_path_id[0] for item in demands):
        # Raise ValueError with the text 'PANEL_SCHEDULE_APPROACH_PATH_MISMATCH' to stop this execution path.
        raise ValueError("PANEL_SCHEDULE_APPROACH_PATH_MISMATCH")
    # Return schedule to the caller.
    return schedule


# Validate a curated subset without changing route or science semantics.
# Input schedule: the supplied schedule.
# Input allow_repeated_movements: the supplied allow repeated movements.
# Output: schedule.
# Processing: select branches using the stated conditions.
def validate_presentation_schedule(schedule, *, allow_repeated_movements=False):
    """Validate a curated subset without changing route or science semantics."""
    # Run this branch when a set built from schedule differs from a set built from APPROACH_PATHS.
    if set(schedule) != set(APPROACH_PATHS):
        # Raise ValueError with the text 'PANEL_SCHEDULE_APPROACH_SET_INVALID' to stop this execution path.
        raise ValueError("PANEL_SCHEDULE_APPROACH_SET_INVALID")
    # Set demands to a tuple built from a lazy sequence of item for rows in values from schedule.
    demands = tuple(item for rows in schedule.values() for item in rows)
    # Set legal to a set of path for paths in values from APPROACH_PATHS.
    legal = {path for paths in APPROACH_PATHS.values() for path in paths}
    # Run this branch when the negation of demands or whether any item is true in a lazy sequence of
    # item.movement_path_id does not belong to legal for item in demands.
    if not demands or any(item.movement_path_id not in legal for item in demands):
        # Raise ValueError with the text 'PANEL_SCENARIO_MOVEMENT_NOT_LEGAL' to stop this execution path.
        raise ValueError("PANEL_SCENARIO_MOVEMENT_NOT_LEGAL")
    # Run this branch when the negation of allow_repeated_movements and the number of entries in a set of
    # item.movement_path_id for item in demands differs from the number of entries in demands.
    if not allow_repeated_movements and len({item.movement_path_id for item in demands}) != len(demands):
        # Raise ValueError with the text 'PANEL_SCENARIO_MOVEMENTS_NOT_UNIQUE' to stop this execution path.
        raise ValueError("PANEL_SCENARIO_MOVEMENTS_NOT_UNIQUE")
    # Run this branch when whether any item is true in a lazy sequence of item.approach differs from
    # item.movement_path_id at 0 for item in demands.
    if any(item.approach != item.movement_path_id[0] for item in demands):
        # Raise ValueError with the text 'PANEL_SCHEDULE_APPROACH_PATH_MISMATCH' to stop this execution path.
        raise ValueError("PANEL_SCHEDULE_APPROACH_PATH_MISMATCH")
    # Return schedule to the caller.
    return schedule
