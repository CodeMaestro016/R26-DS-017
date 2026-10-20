"""SUMO-consistent stopping constraints for precedence-blocked vehicles."""

# Import math for use in this module.
import math
# Import SpeedConstraintRecord from .models for the operations below.
from .models import SpeedConstraintRecord


# Define ExecutionConstraintError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ExecutionConstraintError(ValueError):
    # Keep this block syntactically valid without performing an operation.
    pass


# Set SUMO_SPEED_MODE_SAFE_SPEED_BIT to 0.
SUMO_SPEED_MODE_SAFE_SPEED_BIT = 0
# Set SUMO_SPEED_MODE_MAX_ACCELERATION_BIT to 1.
SUMO_SPEED_MODE_MAX_ACCELERATION_BIT = 1
# Set SUMO_SPEED_MODE_MAX_DECELERATION_BIT to 2.
SUMO_SPEED_MODE_MAX_DECELERATION_BIT = 2
# Set SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT to 3.
SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT = 3
# Set SUMO_PROCESS_TRACI_SPEED_CONTROL to the text 'SUMO_PROCESS_TRACI_SPEED_CONTROL'.
SUMO_PROCESS_TRACI_SPEED_CONTROL = "SUMO_PROCESS_TRACI_SPEED_CONTROL"


# Interpret SUMO's non-inverted safety bits without changing the mask.
# Input speed_mode: the supplied speed mode.
# Output: a dictionary containing safe_speed, max_acceleration, max_deceleration, junction_priority.
def speed_mode_enforcement(speed_mode):
    """Interpret SUMO's non-inverted safety bits without changing the mask."""
    # Set mode to an integer built from speed_mode.
    mode = int(speed_mode)
    # Return a dictionary containing safe_speed, max_acceleration, max_deceleration, junction_priority to the
    # caller.
    return {
        # Store a Boolean built from mode intersected with 1 shifted left by SUMO_SPEED_MODE_SAFE_SPEED_BIT under
        # 'safe_speed'.
        "safe_speed": bool(mode & (1 << SUMO_SPEED_MODE_SAFE_SPEED_BIT)),
        # Store a Boolean built from mode intersected with 1 shifted left by SUMO_SPEED_MODE_MAX_ACCELERATION_BIT
        # under 'max_acceleration'.
        "max_acceleration": bool(
            # Supply mode intersected with 1 shifted left by SUMO_SPEED_MODE_MAX_ACCELERATION_BIT to bool.
            mode & (1 << SUMO_SPEED_MODE_MAX_ACCELERATION_BIT)),
        # Store a Boolean built from mode intersected with 1 shifted left by SUMO_SPEED_MODE_MAX_DECELERATION_BIT
        # under 'max_deceleration'.
        "max_deceleration": bool(
            # Supply mode intersected with 1 shifted left by SUMO_SPEED_MODE_MAX_DECELERATION_BIT to bool.
            mode & (1 << SUMO_SPEED_MODE_MAX_DECELERATION_BIT)),
        # Store a Boolean built from mode intersected with 1 shifted left by SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT
        # under 'junction_priority'.
        "junction_priority": bool(
            # Supply mode intersected with 1 shifted left by SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT to bool.
            mode & (1 << SUMO_SPEED_MODE_JUNCTION_PRIORITY_BIT)),
    }


# Continuous-time diagnostic reference, not live SUMO authority.
# Input distance_to_zone_entry: the supplied distance to zone entry.
# Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
# Output: the square root of 2.0 multiplied by deceleration multiplied by distance.
# Processing: select branches using the stated conditions.
def stopping_speed_cap(distance_to_zone_entry, comfortable_deceleration_mps2):
    """Continuous-time diagnostic reference, not live SUMO authority."""
    # Set distance to a floating-point number built from distance_to_zone_entry.
    distance = float(distance_to_zone_entry)
    # Set deceleration to a floating-point number built from comfortable_deceleration_mps2.
    deceleration = float(comfortable_deceleration_mps2)
    # Run this branch when distance is less than 0.0.
    if distance < 0.0:
        # Raise ExecutionConstraintError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this
        # execution path.
        raise ExecutionConstraintError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    # Run this branch when the negation of whether deceleration contains finite numeric values or deceleration is
    # at most 0.0.
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        # Raise ExecutionConstraintError with the text 'COMFORTABLE_DECELERATION_UNAVAILABLE' to stop this
        # execution path.
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    # Return the square root of 2.0 multiplied by deceleration multiplied by distance to the caller.
    return math.sqrt(2.0 * deceleration * distance)


# Set continuous_kinematic_reference_cap to stopping_speed_cap.
continuous_kinematic_reference_cap = stopping_speed_cap


# Audit SUMO's semi-implicit Euler brake gap with zero headway.
# Input current_speed_mps: the supplied current speed mps.
# Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
# Input simulation_step_seconds: the supplied simulation step seconds.
# Output: step multiplied by steps multiplied by speed minus delta_v * steps multiplied by steps + 1 divided by
# 2.0.
# Processing: select branches using the stated conditions.
def sumo_euler_comfortable_brake_gap(current_speed_mps,
                                      # Declare comfortable_deceleration_mps2 as input parameter.
                                      comfortable_deceleration_mps2,
                                      # Declare simulation_step_seconds as input parameter.
                                      simulation_step_seconds):
    """Audit SUMO's semi-implicit Euler brake gap with zero headway."""
    # Set speed to a floating-point number built from current_speed_mps.
    speed = float(current_speed_mps)
    # Set deceleration to a floating-point number built from comfortable_deceleration_mps2.
    deceleration = float(comfortable_deceleration_mps2)
    # Set step to a floating-point number built from simulation_step_seconds.
    step = float(simulation_step_seconds)
    # Run this branch when the negation of whether speed contains finite numeric values or speed is less than 0.0.
    if not math.isfinite(speed) or speed < 0.0:
        # Raise ExecutionConstraintError with the text 'CURRENT_SPEED_INVALID' to stop this execution path.
        raise ExecutionConstraintError("CURRENT_SPEED_INVALID")
    # Run this branch when the negation of whether deceleration contains finite numeric values or deceleration is
    # at most 0.0.
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        # Raise ExecutionConstraintError with the text 'COMFORTABLE_DECELERATION_UNAVAILABLE' to stop this
        # execution path.
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    # Run this branch when the negation of whether step contains finite numeric values or step is at most 0.0.
    if not math.isfinite(step) or step <= 0.0:
        # Raise ExecutionConstraintError with the text 'SIMULATION_STEP_INVALID' to stop this execution path.
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    # Set delta_v to deceleration multiplied by step.
    delta_v = deceleration * step
    # Set steps to an integer built from speed divided by delta_v.
    steps = int(speed / delta_v)
    # Return step multiplied by steps multiplied by speed minus delta_v * steps multiplied by steps + 1 divided by
    # 2.0 to the caller.
    return step * (
        # Evaluate steps multiplied by speed minus delta_v multiplied by steps multiplied by steps plus 1 divided
        # by 2.0 as part of the enclosing expression.
        steps * speed - delta_v * steps * (steps + 1) / 2.0)


# Comfortable minimum next speed using the inputs and processing steps below.
# Input current_speed_mps: the supplied current speed mps.
# Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
# Input simulation_step_seconds: the supplied simulation step seconds.
# Output: the maximum of 0.0, speed minus deceleration multiplied by step.
# Processing: select branches using the stated conditions.
def comfortable_minimum_next_speed(current_speed_mps,
                                    # Declare comfortable_deceleration_mps2 as input parameter.
                                    comfortable_deceleration_mps2,
                                    # Declare simulation_step_seconds as input parameter.
                                    simulation_step_seconds):
    # Set speed to a floating-point number built from current_speed_mps.
    speed = float(current_speed_mps)
    # Set deceleration to a floating-point number built from comfortable_deceleration_mps2.
    deceleration = float(comfortable_deceleration_mps2)
    # Set step to a floating-point number built from simulation_step_seconds.
    step = float(simulation_step_seconds)
    # Run this branch when the negation of whether speed contains finite numeric values or speed is less than 0.0.
    if not math.isfinite(speed) or speed < 0.0:
        # Raise ExecutionConstraintError with the text 'CURRENT_SPEED_INVALID' to stop this execution path.
        raise ExecutionConstraintError("CURRENT_SPEED_INVALID")
    # Run this branch when the negation of whether deceleration contains finite numeric values or deceleration is
    # at most 0.0.
    if not math.isfinite(deceleration) or deceleration <= 0.0:
        # Raise ExecutionConstraintError with the text 'COMFORTABLE_DECELERATION_UNAVAILABLE' to stop this
        # execution path.
        raise ExecutionConstraintError("COMFORTABLE_DECELERATION_UNAVAILABLE")
    # Run this branch when the negation of whether step contains finite numeric values or step is at most 0.0.
    if not math.isfinite(step) or step <= 0.0:
        # Raise ExecutionConstraintError with the text 'SIMULATION_STEP_INVALID' to stop this execution path.
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    # Return the maximum of 0.0, speed minus deceleration multiplied by step to the caller.
    return max(0.0, speed - deceleration * step)


# Build a TraCI request; SUMO remains the live feasibility authority.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input conflict_zone_id: the supplied conflict zone id.
# Input distance_to_zone_entry: the supplied distance to zone entry.
# Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
# Input current_speed_mps: the supplied current speed mps.
# Input simulation_step_seconds: the supplied simulation step seconds.
# Input action_step_length_seconds: the supplied action step length seconds.
# Input sumo_stop_speed_mps: the supplied sumo stop speed mps.
# Input native_sumo_speed_without_traci_mps: the supplied native sumo speed without traci mps.
# Input speed_mode: the supplied speed mode.
# Output: the result of SpeedConstraintRecord(vehicle_id, conflict_zone_id, distance, deceleration, speed,
# requested, True, a dictionary...).
# Processing: select branches using the stated conditions.
def build_sumo_native_speed_constraint(
        # Declare vehicle_id, conflict_zone_id, distance_to_zone_entry as input parameters.
        vehicle_id, conflict_zone_id, distance_to_zone_entry,
        # Declare comfortable_deceleration_mps2, current_speed_mps as input parameters.
        comfortable_deceleration_mps2, current_speed_mps,
        # Declare simulation_step_seconds, action_step_length_seconds as input parameters.
        simulation_step_seconds, action_step_length_seconds,
        # Declare sumo_stop_speed_mps, native_sumo_speed_without_traci_mps as input parameters.
        sumo_stop_speed_mps, native_sumo_speed_without_traci_mps,
        # Declare speed_mode as input parameter.
        speed_mode):
    """Build a TraCI request; SUMO remains the live feasibility authority."""
    # Set distance to a floating-point number built from distance_to_zone_entry.
    distance = float(distance_to_zone_entry)
    # Run this branch when distance is less than 0.0 or the negation of whether distance contains finite numeric
    # values.
    if distance < 0.0 or not math.isfinite(distance):
        # Raise ExecutionConstraintError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this
        # execution path.
        raise ExecutionConstraintError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    # Set (step, action_step) to the result of map(float, a tuple containing simulation_step_seconds,
    # action_step_length_seconds).
    step, action_step = map(float, (simulation_step_seconds,
                                   # Include action_step_length_seconds in this tuple.
                                   action_step_length_seconds))
    # Run this branch when step is at most 0.0 or the negation of whether step contains finite numeric values.
    if step <= 0.0 or not math.isfinite(step):
        # Raise ExecutionConstraintError with the text 'SIMULATION_STEP_INVALID' to stop this execution path.
        raise ExecutionConstraintError("SIMULATION_STEP_INVALID")
    # Run this branch when action_step is at most 0.0 or the negation of whether action_step contains finite
    # numeric values.
    if action_step <= 0.0 or not math.isfinite(action_step):
        # Raise ExecutionConstraintError with the text 'ACTION_STEP_INVALID' to stop this execution path.
        raise ExecutionConstraintError("ACTION_STEP_INVALID")
    # Set (speed, deceleration) to the result of map(float, a tuple containing current_speed_mps,
    # comfortable_deceleration_mps2).
    speed, deceleration = map(float, (current_speed_mps,
                                     # Include comfortable_deceleration_mps2 in this tuple.
                                     comfortable_deceleration_mps2))
    # Set stop_speed to a floating-point number built from sumo_stop_speed_mps.
    stop_speed = float(sumo_stop_speed_mps)
    # Set native_speed to a floating-point number built from native_sumo_speed_without_traci_mps.
    native_speed = float(native_sumo_speed_without_traci_mps)
    # Run this branch when the negation of whether every item is true in a lazy sequence of whether value contains
    # finite numeric values for value in a tuple containing stop_speed, native_speed.
    if not all(math.isfinite(value) for value in (stop_speed, native_speed)):
        # Raise ExecutionConstraintError with the text 'SUMO_NATIVE_SPEED_UNAVAILABLE' to stop this execution
        # path.
        raise ExecutionConstraintError("SUMO_NATIVE_SPEED_UNAVAILABLE")
    # Set continuous to the result of stopping_speed_cap(distance, deceleration).
    continuous = stopping_speed_cap(distance, deceleration)
    # Set brake_gap to the result of sumo_euler_comfortable_brake_gap(speed, deceleration, step).
    brake_gap = sumo_euler_comfortable_brake_gap(speed, deceleration, step)
    # Set comfortable_minimum to the result of comfortable_minimum_next_speed(speed, deceleration, step).
    comfortable_minimum = comfortable_minimum_next_speed(
        # Supply deceleration to comfortable_minimum_next_speed.
        speed, deceleration, step)
    # Set requested to the minimum of native_speed, stop_speed.
    requested = min(native_speed, stop_speed)
    # Set enforcement to the result of speed_mode_enforcement(speed_mode).
    enforcement = speed_mode_enforcement(speed_mode)
    # Return the result of SpeedConstraintRecord(vehicle_id, conflict_zone_id, distance, deceleration, speed,
    # requested, True, a dictionary...) to the caller.
    return SpeedConstraintRecord(
        # Supply conflict_zone_id to SpeedConstraintRecord.
        vehicle_id, conflict_zone_id, distance, deceleration, speed,
        # Supply requested to SpeedConstraintRecord.
        requested, True,
        # Store the text 'SUMO_NATIVE_CAR_FOLLOWING_STOP_SPEED' under 'feasibility_model'.
        {"feasibility_model": "SUMO_NATIVE_CAR_FOLLOWING_STOP_SPEED",
         "integration_model": "SUMO_SEMI_IMPLICIT_EULER",
         "continuous_equation_role": "DIAGNOSTIC_REFERENCE_ONLY",
         "comfortable_minimum_role": "DIAGNOSTIC_REFERENCE_ONLY",
         # Store SUMO_PROCESS_TRACI_SPEED_CONTROL under 'runtime_authority'.
         "runtime_authority": SUMO_PROCESS_TRACI_SPEED_CONTROL,
         "precommand_python_feasibility_rejection": "False",
         "emergency_deceleration_used_for_precedence": "False",
         "arbitrary_margin_meters": "0",
         "arbitrary_time_margin_seconds": "0", "numeric_tolerance": "0"},
        # Supply action_step to SpeedConstraintRecord.
        step, action_step, continuous, brake_gap, stop_speed,
        # Supply comfortable_minimum to SpeedConstraintRecord.
        comfortable_minimum, native_speed, requested, None,
        "SUMO_SEMI_IMPLICIT_EULER",
        "DELEGATED_TO_SUMO_NATIVE_SPEED_MODE_ENFORCEMENT",
        # Supply enforcement at 'max_deceleration' to SpeedConstraintRecord.
        None, None, enforcement["max_deceleration"],
        # Supply enforcement at 'max_acceleration' to SpeedConstraintRecord.
        enforcement["safe_speed"], enforcement["max_acceleration"],
        # Supply enforcement at 'junction_priority' to SpeedConstraintRecord.
        enforcement["junction_priority"], SUMO_PROCESS_TRACI_SPEED_CONTROL,
        # Supply an integer built from speed_mode to SpeedConstraintRecord.
        False, int(speed_mode))


# Build speed constraint using the inputs and processing steps below.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input conflict_zone_id: the supplied conflict zone id.
# Input distance_to_zone_entry: the supplied distance to zone entry.
# Input comfortable_deceleration_mps2: the supplied comfortable deceleration mps2.
# Input current_speed_mps: the supplied current speed mps.
# Output: the result of SpeedConstraintRecord(vehicle_id, conflict_zone_id, a floating-point number built from
# distance_to_zone_entry, a...).
# Processing: select branches using the stated conditions.
def build_speed_constraint(vehicle_id, conflict_zone_id,
                           # Declare distance_to_zone_entry as input parameter.
                           distance_to_zone_entry,
                           # Declare comfortable_deceleration_mps2, current_speed_mps as input parameters.
                           comfortable_deceleration_mps2, current_speed_mps):
    # Retained for non-live continuous-reference unit checks. Physical SUMO
    # replay uses ``build_sumo_native_speed_constraint``.
    # Set cap to the result of stopping_speed_cap(distance_to_zone_entry, comfortable_deceleration_mps2).
    cap = stopping_speed_cap(distance_to_zone_entry,
                             # Supply comfortable_deceleration_mps2 to stopping_speed_cap.
                             comfortable_deceleration_mps2)
    # Set speed to a floating-point number built from current_speed_mps.
    speed = float(current_speed_mps)
    # Set feasible to speed is at most cap.
    feasible = speed <= cap
    # Run this branch when the negation of feasible.
    if not feasible:
        # Raise ExecutionConstraintError with the text 'EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE' to stop this
        # execution path.
        raise ExecutionConstraintError(
            "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE")
    # Return the result of SpeedConstraintRecord(vehicle_id, conflict_zone_id, a floating-point number built from
    # distance_to_zone_entry, a...) to the caller.
    return SpeedConstraintRecord(
        # Supply a floating-point number built from distance_to_zone_entry to SpeedConstraintRecord.
        vehicle_id, conflict_zone_id, float(distance_to_zone_entry),
        # Supply a floating-point number built from comfortable_deceleration_mps2 to SpeedConstraintRecord.
        float(comfortable_deceleration_mps2), speed, cap, True,
        # Store the text 'v_cap=sqrt(2*b*d_entry)' under 'equation'.
        {"equation": "v_cap=sqrt(2*b*d_entry)",
         "distance_reference": "FRONT_BUMPER_PATH_PROGRESS",
         "arbitrary_margin_meters": "0"})
