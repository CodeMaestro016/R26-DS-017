"""SUMO semi-implicit Euler braking semantics tests."""

# Import inspect for use in this module.
import inspect
# Import math for use in this module.
import math

# Import pytest for use in this module.
import pytest

# Import ExecutionConstraintError, build_sumo_native_speed_constraint, comfortable_minimum_next_speed,
# continuous_kinematic_reference_cap, speed_mode_enforcement,... from negotiation_execution for the operations
# below.
from negotiation_execution import (ExecutionConstraintError,
    build_sumo_native_speed_constraint, comfortable_minimum_next_speed,
    continuous_kinematic_reference_cap, speed_mode_enforcement,
    sumo_euler_comfortable_brake_gap)

# Set (V, B, DT, D) to a tuple containing 6.327762945206484, 4.5, 0.04, 4.410609013325224.
V, B, DT, D = 6.327762945206484, 4.5, 0.04, 4.410609013325224
# Set SAFE_MODE to 31.
SAFE_MODE = 31


# Check continuous reference formula and role using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_continuous_reference_formula_and_role():
    # Require the result of continuous_kinematic_reference_cap(D, B) equals the square root of 2 multiplied by B
    # multiplied by D; otherwise raise AssertionError.
    assert continuous_kinematic_reference_cap(D, B) == math.sqrt(2 * B * D)
    # Require V is greater than the result of continuous_kinematic_reference_cap(D, B); otherwise raise
    # AssertionError.
    assert V > continuous_kinematic_reference_cap(D, B)


# Check euler discrete brake gap formula for former failure using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_euler_discrete_brake_gap_formula_for_former_failure():
    # Set delta_v to B multiplied by DT.
    delta_v = B * DT
    # Set steps to an integer built from V divided by delta_v.
    steps = int(V / delta_v)
    # Set expected to DT multiplied by steps multiplied by V minus delta_v * steps multiplied by steps + 1 divided
    # by 2.
    expected = DT * (steps * V - delta_v * steps * (steps + 1) / 2)
    # Require the result of sumo_euler_comfortable_brake_gap(V, B, DT) equals expected; otherwise raise
    # AssertionError.
    assert sumo_euler_comfortable_brake_gap(V, B, DT) == expected
    # Require expected equals 4.322868123289077; otherwise raise AssertionError.
    assert expected == 4.322868123289077
    # Require expected is less than D; otherwise raise AssertionError.
    assert expected < D


# Check zero speed and zero distance constraint using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_zero_speed_and_zero_distance_constraint():
    # Require the result of sumo_euler_comfortable_brake_gap(0.0, B, DT) equals 0.0; otherwise raise
    # AssertionError.
    assert sumo_euler_comfortable_brake_gap(0.0, B, DT) == 0.0
    # Set record to the result of build_sumo_native_speed_constraint(the text 'AV', the text 'CZ', 0.0, B, 0.0,
    # DT, DT, 0.0, 0.0, SAFE_MODE).
    record = build_sumo_native_speed_constraint(
        # Supply SAFE_MODE to build_sumo_native_speed_constraint.
        "AV", "CZ", 0.0, B, 0.0, DT, DT, 0.0, 0.0, SAFE_MODE)
    # Require record.comfortable_feasible is the same object as None; otherwise raise AssertionError.
    assert record.comfortable_feasible is None
    # Require record.requested_precedence_speed_mps equals 0.0; otherwise raise AssertionError.
    assert record.requested_precedence_speed_mps == 0.0


# Apply 'args,code' as a decorator to configure the following definition.
@pytest.mark.parametrize("args,code", (
    # Include a tuple containing a tuple containing V, 0.0, DT, the text 'COMFORTABLE_DECELERATION_UNAVAILABLE' in
    # this tuple.
    ((V, 0.0, DT), "COMFORTABLE_DECELERATION_UNAVAILABLE"),
    # Include a tuple containing a tuple containing V, B, 0.0, the text 'SIMULATION_STEP_INVALID' in this tuple.
    ((V, B, 0.0), "SIMULATION_STEP_INVALID"),
    # Include a tuple containing a tuple containing the negative of 1.0, B, DT, the text 'CURRENT_SPEED_INVALID'
    # in this tuple.
    ((-1.0, B, DT), "CURRENT_SPEED_INVALID"),
))
# Check invalid audit inputs using the setup, calls, and assertions below.
# Input args: the supplied args.
# Input code: the supplied code.
# Output: no explicit value; normal completion returns None.
def test_invalid_audit_inputs(args, code):
    # Enter the result of pytest.raises(ExecutionConstraintError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExecutionConstraintError, match=code):
        # Call sumo_euler_comfortable_brake_gap with the supplied arguments.
        sumo_euler_comfortable_brake_gap(*args)


# Check comfortable minimum next speed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_comfortable_minimum_next_speed():
    # Require the result of comfortable_minimum_next_speed(V, B, DT) equals V minus B multiplied by DT; otherwise
    # raise AssertionError.
    assert comfortable_minimum_next_speed(V, B, DT) == V - B * DT
    # Require the result of comfortable_minimum_next_speed(0.1, B, DT) equals 0.0; otherwise raise AssertionError.
    assert comfortable_minimum_next_speed(0.1, B, DT) == 0.0


# Check continuous false discrete native true case using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_continuous_false_discrete_native_true_case():
    # Set native_stop_speed to 6.2097207238037315.
    native_stop_speed = 6.2097207238037315
    # Set record to the result of build_sumo_native_speed_constraint(the text 'AV', the text 'CZ', D, B, V, DT,
    # DT, native_stop_speed, 13.89, SAFE_MODE).
    record = build_sumo_native_speed_constraint(
        # Supply native_stop_speed to build_sumo_native_speed_constraint.
        "AV", "CZ", D, B, V, DT, DT, native_stop_speed, 13.89, SAFE_MODE)
    # Require V is greater than record.continuous_reference_cap_mps; otherwise raise AssertionError.
    assert V > record.continuous_reference_cap_mps
    # Require record.discrete_euler_brake_gap_m is less than D; otherwise raise AssertionError.
    assert record.discrete_euler_brake_gap_m < D
    # Require record.sumo_stop_speed_mps is at least record.comfortable_min_next_speed_mps; otherwise raise
    # AssertionError.
    assert record.sumo_stop_speed_mps >= record.comfortable_min_next_speed_mps
    # Require record.comfortable_feasible is the same object as None; otherwise raise AssertionError.
    assert record.comfortable_feasible is None
    # Require record.comfortable_feasibility_status equals the text
    # 'DELEGATED_TO_SUMO_NATIVE_SPEED_MODE_ENFORCEMENT'; otherwise raise AssertionError.
    assert record.comfortable_feasibility_status == (
        "DELEGATED_TO_SUMO_NATIVE_SPEED_MODE_ENFORCEMENT")
    # Require record.requested_precedence_speed_mps equals native_stop_speed; otherwise raise AssertionError.
    assert record.requested_precedence_speed_mps == native_stop_speed


# Check continuous true discrete true case using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_continuous_true_discrete_true_case():
    # Set record to the result of build_sumo_native_speed_constraint(the text 'AV', the text 'CZ', 20.0, B, 2.0,
    # DT, DT, 2.0, 2.0, SAFE_MODE).
    record = build_sumo_native_speed_constraint(
        # Supply SAFE_MODE to build_sumo_native_speed_constraint.
        "AV", "CZ", 20.0, B, 2.0, DT, DT, 2.0, 2.0, SAFE_MODE)
    # Require record.current_speed_mps is at most record.continuous_reference_cap_mps; otherwise raise
    # AssertionError.
    assert record.current_speed_mps <= record.continuous_reference_cap_mps
    # Require record.comfortable_feasible is the same object as None; otherwise raise AssertionError.
    assert record.comfortable_feasible is None


# Check python diagnostic does not reject live request using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_python_diagnostic_does_not_reject_live_request():
    # Set minimum to the result of comfortable_minimum_next_speed(V, B, DT).
    minimum = comfortable_minimum_next_speed(V, B, DT)
    # Set record to the result of build_sumo_native_speed_constraint(the text 'AV', the text 'CZ', D, B, V, DT,
    # DT, minimum minus 0.01, 13.89, SAFE_MODE).
    record = build_sumo_native_speed_constraint(
        # Supply minimum minus 0.01 to build_sumo_native_speed_constraint.
        "AV", "CZ", D, B, V, DT, DT, minimum - 0.01, 13.89, SAFE_MODE)
    # Require record.requested_precedence_speed_mps is less than minimum; otherwise raise AssertionError.
    assert record.requested_precedence_speed_mps < minimum
    # Require record.precommand_python_feasibility_rejection is the same object as False; otherwise raise
    # AssertionError.
    assert record.precommand_python_feasibility_rejection is False


# Check native safety lower speed is not controller emergency requirement using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_native_safety_lower_speed_is_not_controller_emergency_requirement():
    # Set record to the result of build_sumo_native_speed_constraint(the text 'AV', the text 'CZ', D, B, V, DT,
    # DT, V, 0.0, SAFE_MODE).
    record = build_sumo_native_speed_constraint(
        # Supply SAFE_MODE to build_sumo_native_speed_constraint.
        "AV", "CZ", D, B, V, DT, DT, V, 0.0, SAFE_MODE)
    # Require record.requested_precedence_speed_mps equals 0.0; otherwise raise AssertionError.
    assert record.requested_precedence_speed_mps == 0.0
    # Require record.comfortable_feasible is the same object as None; otherwise raise AssertionError.
    assert record.comfortable_feasible is None


# Check safe speed mode required bits are active using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_safe_speed_mode_required_bits_are_active():
    # Require the result of speed_mode_enforcement(SAFE_MODE) equals a dictionary containing safe_speed,
    # max_acceleration, max_deceleration, junction_priority; otherwise raise AssertionError.
    assert speed_mode_enforcement(SAFE_MODE) == {
        # Store True under 'safe_speed'.
        # Store True under 'max_acceleration'.
        "safe_speed": True, "max_acceleration": True,
        # Store True under 'max_deceleration'.
        # Store True under 'junction_priority'.
        "max_deceleration": True, "junction_priority": True}


# Check no tolerance margin or emergency substitution using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_tolerance_margin_or_emergency_substitution():
    # Set source to the result of inspect.getsource(build_sumo_native_speed_constraint).
    source = inspect.getsource(build_sumo_native_speed_constraint)
    # Require the text 'isclose' does not belong to source; otherwise raise AssertionError.
    assert "isclose" not in source
    # Require the text 'epsilon' does not belong to the result of source.lower(); otherwise raise AssertionError.
    assert "epsilon" not in source.lower()
    # Require the text 'emergency_deceleration_mps2' does not belong to
    # inspect.signature(build_sumo_native_speed_constraint).parameters; otherwise raise AssertionError.
    assert "emergency_deceleration_mps2" not in inspect.signature(
        # Supply build_sumo_native_speed_constraint to inspect.signature.
        build_sumo_native_speed_constraint).parameters
    # Require the text '"emergency_deceleration_used_for_precedence": "False"' belongs to source; otherwise raise
    # AssertionError.
    assert '"emergency_deceleration_used_for_precedence": "False"' in source
    # Require the text '"numeric_tolerance": "0"' belongs to source; otherwise raise AssertionError.
    assert '"numeric_tolerance": "0"' in source
    # Require the text '"arbitrary_margin_meters": "0"' belongs to source; otherwise raise AssertionError.
    assert '"arbitrary_margin_meters": "0"' in source
