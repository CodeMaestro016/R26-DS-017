"""SUMO semi-implicit Euler braking semantics tests."""

import inspect
import math

import pytest

from negotiation_execution import (ExecutionConstraintError,
    build_sumo_native_speed_constraint, comfortable_minimum_next_speed,
    continuous_kinematic_reference_cap, sumo_euler_comfortable_brake_gap)

V, B, DT, D = 6.327762945206484, 4.5, 0.04, 4.410609013325224


def test_continuous_reference_formula_and_role():
    assert continuous_kinematic_reference_cap(D, B) == math.sqrt(2 * B * D)
    assert V > continuous_kinematic_reference_cap(D, B)


def test_euler_discrete_brake_gap_formula_for_former_failure():
    delta_v = B * DT
    steps = int(V / delta_v)
    expected = DT * (steps * V - delta_v * steps * (steps + 1) / 2)
    assert sumo_euler_comfortable_brake_gap(V, B, DT) == expected
    assert expected == 4.322868123289077
    assert expected < D


def test_zero_speed_and_zero_distance_constraint():
    assert sumo_euler_comfortable_brake_gap(0.0, B, DT) == 0.0
    record = build_sumo_native_speed_constraint(
        "AV", "CZ", 0.0, B, 0.0, DT, DT, 0.0, 0.0)
    assert record.comfortable_feasible
    assert record.requested_precedence_speed_mps == 0.0


@pytest.mark.parametrize("args,code", (
    ((V, 0.0, DT), "COMFORTABLE_DECELERATION_UNAVAILABLE"),
    ((V, B, 0.0), "SIMULATION_STEP_INVALID"),
    ((-1.0, B, DT), "CURRENT_SPEED_INVALID"),
))
def test_invalid_audit_inputs(args, code):
    with pytest.raises(ExecutionConstraintError, match=code):
        sumo_euler_comfortable_brake_gap(*args)


def test_comfortable_minimum_next_speed():
    assert comfortable_minimum_next_speed(V, B, DT) == V - B * DT
    assert comfortable_minimum_next_speed(0.1, B, DT) == 0.0


def test_continuous_false_discrete_native_true_case():
    native_stop_speed = 6.2097207238037315
    record = build_sumo_native_speed_constraint(
        "AV", "CZ", D, B, V, DT, DT, native_stop_speed, 13.89)
    assert V > record.continuous_reference_cap_mps
    assert record.discrete_euler_brake_gap_m < D
    assert record.sumo_stop_speed_mps >= record.comfortable_min_next_speed_mps
    assert record.comfortable_feasible
    assert record.requested_precedence_speed_mps == native_stop_speed


def test_continuous_true_discrete_true_case():
    record = build_sumo_native_speed_constraint(
        "AV", "CZ", 20.0, B, 2.0, DT, DT, 2.0, 2.0)
    assert record.current_speed_mps <= record.continuous_reference_cap_mps
    assert record.comfortable_feasible


def test_genuinely_discrete_infeasible_case():
    minimum = comfortable_minimum_next_speed(V, B, DT)
    with pytest.raises(ExecutionConstraintError, match=
                       "EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE"):
        build_sumo_native_speed_constraint(
            "AV", "CZ", D, B, V, DT, DT, minimum - 0.01, 13.89)


def test_native_safety_lower_speed_is_not_controller_emergency_requirement():
    record = build_sumo_native_speed_constraint(
        "AV", "CZ", D, B, V, DT, DT, V, 0.0)
    assert record.requested_precedence_speed_mps == 0.0
    assert record.comfortable_feasible


def test_no_tolerance_margin_or_emergency_substitution():
    source = inspect.getsource(build_sumo_native_speed_constraint)
    assert "isclose" not in source
    assert "epsilon" not in source.lower()
    assert "emergency_deceleration_mps2" not in inspect.signature(
        build_sumo_native_speed_constraint).parameters
    assert '"emergency_deceleration_used_for_precedence": "False"' in source
    assert '"numeric_tolerance": "0"' in source
    assert '"arbitrary_margin_meters": "0"' in source
