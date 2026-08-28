"""Deterministic rolling one-front-vehicle-per-approach presentation demand."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelDemand:
    approach: str
    movement_path_id: str
    sequence_index: int


APPROACH_PATHS = {
    # Phase 1: E-left/N-left (rule-resolved).
    # Phase 2: E-straight/N-straight/S-right/W-left (training manifest MAPPO).
    # Phase 3: E-right/N-right/S-straight/W-right (rule-resolved).
    # Phase 4: S-left/W-straight (rule-resolved).
    "N": ("N_IN_0_LEFT", "N_IN_0_STRAIGHT", "N_IN_0_RIGHT"),
    "E": ("E_IN_0_LEFT", "E_IN_0_STRAIGHT", "E_IN_0_RIGHT"),
    "S": ("S_IN_0_RIGHT", "S_IN_0_STRAIGHT", "S_IN_0_LEFT"),
    "W": ("W_IN_0_LEFT", "W_IN_0_RIGHT", "W_IN_0_STRAIGHT"),
}

# Simultaneous admission with a fixed order; subsequent waves are admitted
# only after the prior wave clears all four rolling approach slots.
INITIAL_ADMISSION_SECONDS = {"N": 0.0, "E": 0.0, "S": 0.0, "W": 0.0}
ADMISSION_ORDER = ("N", "E", "S", "W")
ADMISSION_WAVES = (("N", "E"), ("N", "E", "S", "W"),
                   ("N", "E", "S", "W"), ("S", "W"))


def build_default_schedule():
    """Use all 12 movements in four predeclared actor-safe phases."""
    return {approach: tuple(PanelDemand(approach, path, index)
                            for index, path in enumerate(paths))
            for approach, paths in APPROACH_PATHS.items()}


def validate_schedule(schedule):
    demands = tuple(item for rows in schedule.values() for item in rows)
    if set(schedule) != set(APPROACH_PATHS):
        raise ValueError("PANEL_SCHEDULE_APPROACH_SET_INVALID")
    if len(demands) != 12 or len({x.movement_path_id for x in demands}) != 12:
        raise ValueError("PANEL_SCHEDULE_MUST_USE_12_UNIQUE_LEGAL_MOVEMENTS")
    if any(item.approach != item.movement_path_id[0] for item in demands):
        raise ValueError("PANEL_SCHEDULE_APPROACH_PATH_MISMATCH")
    return schedule
