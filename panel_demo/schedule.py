"""Deterministic rolling one-front-vehicle-per-approach presentation demand."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelDemand:
    approach: str
    movement_path_id: str
    sequence_index: int


APPROACH_PATHS = {
    # This opening mix keeps the live continuous stream moving while retaining
    # conflicting paths; later waves cover every remaining legal movement.
    "N": ("N_IN_0_RIGHT", "N_IN_0_STRAIGHT", "N_IN_0_LEFT"),
    "E": ("E_IN_0_LEFT", "E_IN_0_RIGHT", "E_IN_0_STRAIGHT"),
    "S": ("S_IN_0_RIGHT", "S_IN_0_STRAIGHT", "S_IN_0_LEFT"),
    "W": ("W_IN_0_STRAIGHT", "W_IN_0_RIGHT", "W_IN_0_LEFT"),
}


def build_default_schedule():
    """Use all 12 legal movements in a fixed evidence-backed wave order."""
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
