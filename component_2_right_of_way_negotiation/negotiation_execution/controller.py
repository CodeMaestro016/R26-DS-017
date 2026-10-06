"""SUMO-consistent stopping constraints for precedence-blocked vehicles."""

import math
from .models import SpeedConstraintRecord


class ExecutionConstraintError(ValueError):
    pass


SUMO_SPEED_MODE_SAFE_SPEED_BIT = 0
SUMO_SPEED_MODE_MAX_ACCELERATION_BIT = 1
SUMO_SPEED_MODE_MAX_DECELERATION_BIT = 2
SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT = 3
SUMO_PROCESS_TRACI_SPEED_CONTROL = "SUMO_PROCESS_TRACI_SPEED_CONTROL"


def speed_mode_enforcement(speed_mode):
    """Interpret SUMO's non-inverted safety bits without changing the mask."""
    mode = int(speed_mode)
    return {
        "safe_speed": bool(mode & (1 << SUMO_SPEED_MODE_SAFE_SPEED_BIT)),
        "max_acceleration": bool(
            mode & (1 << SUMO_SPEED_MODE_MAX_ACCELERATION_BIT)),
        "max_deceleration": bool(
            mode & (1 << SUMO_SPEED_MODE_MAX_DECELERATION_BIT)),
        "junction_priority": bool(
            mode & (1 << SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT)),
    }


def stopping_speed_cap(distance_to_zone_entry, comfortable_deceleration_mps2):
    """Continuous-time diagnostic reference, not live SUMO authority."""
    distance = float(distance_to_zone_entry)
    deceleration = float(comfortable_deceleration_mps2)
    if distance < 0.0:
        raise ExecutionConstraintError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    return math.sqrt(2.0 * deceleration * distance)


continuous_kinematic_reference_cap = stopping_speed_cap


def sumo_euler_comfortable_brake_gap(current_speed_mps,
                                      comfortable_deceleration_mps2,
                                      simulation_step_seconds):
    """Audit SUMO's semi-implicit Euler brake gap with zero headway."""
    speed = float(current_speed_mps)
    deceleration = float(comfortable_deceleration_mps2)
    step = float(simulation_step_seconds)
    if not math.isfinite(speed) or speed < 0.0:
        raise ExecutionConstraintError("CURRENT_SPEED_INVALID")
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    if not math.isfinite(step) or step <= 0.0:
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    delta_v = deceleration * step
    steps = int(speed / delta_v)
    return step * (
        steps * speed - delta_v * steps * (steps + 1) / 2.0)


def comfortable_minimum_next_speed(current_speed_mps,
                                    comfortable_deceleration_mps2,
                                    simulation_step_seconds):
    speed = float(current_speed_mps)
    deceleration = float(comfortable_deceleration_mps2)
    step = float(simulation_step_seconds)
    if not math.isfinite(speed) or speed < 0.0:
        raise ExecutionConstraintError("CURRENT_SPEED_INVALID")
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    if not math.isfinite(step) or step <= 0.0:
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    return max(0.0, speed - deceleration * step)


def build_sumo_native_speed_constraint(
        vehicle_id, conflict_zone_id, distance_to_zone_entry,
        comfortable_deceleration_mps2, current_speed_mps,
        simulation_step_seconds, action_step_length_seconds,
        sumo_stop_speed_mps, native_sumo_speed_without_traci_mps,
        speed_mode):
    """Build a TraCI request; SUMO remains the live feasibility authority."""
    distance = float(distance_to_zone_entry)
    if distance < 0.0 or not math.isfinite(distance):
        raise ExecutionConstraintError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    step, action_step = map(float, (simulation_step_seconds,
                                   action_step_length_seconds))
    if step <= 0.0 or not math.isfinite(step):
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    if action_step <= 0.0 or not math.isfinite(action_step):
        raise ExecutionConstraintError("ACTION_STEP_INVALID")
    speed, deceleration = map(float, (current_speed_mps,
                                     comfortable_deceleration_mps2))
    stop_speed = float(sumo_stop_speed_mps)
    native_speed = float(native_sumo_speed_without_traci_mps)
    if not all(math.isfinite(value) for value in (stop_speed, native_speed)):
        raise ExecutionConstraintError("SUMO_NATIVE_SPEED_UNAVAILABLE")
    continuous = stopping_speed_cap(distance, deceleration)
    brake_gap = sumo_euler_comfortable_brake_gap(speed, deceleration, step)
    comfortable_minimum = comfortable_minimum_next_speed(
        speed, deceleration, step)
    requested = min(native_speed, stop_speed)
    enforcement = speed_mode_enforcement(speed_mode)
    return SpeedConstraintRecord(
        vehicle_id, conflict_zone_id, distance, deceleration, speed,
        requested, True,
        {"feasibility_model": "SUMO_NATIVE_CAR_FOLLOWING_STOP_SPEED",
         "integration_model": "SUMO_SEMI_IMPLICIT_EULER",
         "continuous_equation_role": "DIAGNOSTIC_REFERENCE_ONLY",
         "comfortable_minimum_role": "DIAGNOSTIC_REFERENCE_ONLY",
         "runtime_authority": SUMO_PROCESS_TRACI_SPEED_CONTROL,
         "precommand_python_feasibility_rejection": "False",
         "emergency_deceleration_used_for_precedence": "False",
         "arbitrary_margin_meters": "0",
         "arbitrary_time_margin_seconds": "0", "numeric_tolerance": "0"},
        step, action_step, continuous, brake_gap, stop_speed,
        comfortable_minimum, native_speed, requested, None,
        "SUMO_SEMI_IMPLICIT_EULER",
        "DELEGATED_TO_SUMO_NATIVE_SPEED_MODE_ENFORCEMENT",
        None, None, enforcement["max_deceleration"],
        enforcement["safe_speed"], enforcement["max_acceleration"],
        enforcement["junction_priority"], SUMO_PROCESS_TRACI_SPEED_CONTROL,
        False, int(speed_mode))


def build_speed_constraint(vehicle_id, conflict_zone_id,
                           distance_to_zone_entry,
                           comfortable_deceleration_mps2, current_speed_mps):
    # Retained for non-live continuous-reference unit checks. Physical SUMO
    # replay uses ``build_sumo_native_speed_constraint``.
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
