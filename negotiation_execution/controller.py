"""Map-derived stopping envelope for precedence-blocked vehicles."""

import math
from .models import SpeedConstraintRecord


class ExecutionConstraintError(ValueError):
    pass


def stopping_speed_cap(distance_to_zone_entry, comfortable_deceleration_mps2):
    distance = float(distance_to_zone_entry)
    deceleration = float(comfortable_deceleration_mps2)
    if distance < 0.0:
        raise ExecutionConstraintError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    return math.sqrt(2.0 * deceleration * distance)


def build_speed_constraint(vehicle_id, conflict_zone_id,
                           distance_to_zone_entry,
                           comfortable_deceleration_mps2, current_speed_mps):
    cap = stopping_speed_cap(distance_to_zone_entry,
                             comfortable_deceleration_mps2)
    speed = float(current_speed_mps)
    feasible = speed <= cap
    if not feasible:
        raise ExecutionConstraintError(
            "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE")
    return SpeedConstraintRecord(
        vehicle_id, conflict_zone_id, float(distance_to_zone_entry),
        float(comfortable_deceleration_mps2), speed, cap, True,
        {"equation": "v_cap=sqrt(2*b*d_entry)",
         "distance_reference": "FRONT_BUMPER_PATH_PROGRESS",
         "arbitrary_margin_meters": "0"})

