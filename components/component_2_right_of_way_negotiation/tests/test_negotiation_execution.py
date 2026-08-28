from dataclasses import FrozenInstanceError

import pytest

from conflict import ConflictZoneManager, MapPathManager
from negotiation_execution import (ConflictZoneExecutionPlanner,
    ExecutionConstraintError, build_speed_constraint, stopping_speed_cap)


def planner():
    paths = MapPathManager()
    return ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))


def test_yielding_to_priority_ready_set_uses_outgoing_edges():
    result = planner().plan(
        source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    assert result.ready_vehicle_ids == ("B",)
    assert result.blocked_vehicle_ids == ("A",)
    assert result.constraints[0].yielding_vehicle_id == "A"
    assert result.constraints[0].priority_vehicle_id == "B"


def test_cycle_blocks_every_ready_vehicle_and_is_order_invariant():
    kwargs = dict(source_snapshot_id=("s",), active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    first = planner().plan(effective_coordination_graph=(("A", "B"), ("B", "A")), **kwargs)
    second = planner().plan(effective_coordination_graph=(("B", "A"), ("A", "B")), **kwargs)
    assert first == second
    assert first.graph_status == "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
    assert first.ready_vehicle_ids == ()


def test_zone_clearance_releases_without_delay():
    p = planner()
    kwargs = dict(source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="AGREEMENT_ESTABLISHED")
    blocked = p.plan(**kwargs)
    zone = blocked.constraints[0].conflict_zone_id
    released = p.plan(**kwargs, cleared_vehicle_zones=(("B", zone),))
    assert released.vehicle_permissions[0].permission_status == "PERMITTED"
    assert "A" in released.ready_vehicle_ids


def test_stopping_envelope_uses_exact_kinematics_and_no_margin():
    assert stopping_speed_cap(0.0, 4.5) == 0.0
    assert stopping_speed_cap(2.0, 4.5) == pytest.approx((18.0) ** 0.5)
    record = build_speed_constraint("A", "Z", 2.0, 4.5, 1.0)
    assert record.provenance["equation"] == "v_cap=sqrt(2*b*d_entry)"
    assert record.provenance["arbitrary_margin_meters"] == "0"
    with pytest.raises(ExecutionConstraintError,
                       match="EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE"):
        build_speed_constraint("A", "Z", 1.0, 4.5, 4.0)


def test_missing_deceleration_and_negative_distance_rejected():
    with pytest.raises(ExecutionConstraintError,
                       match="COMFORTABLE_DECELERATION_UNAVAILABLE"):
        stopping_speed_cap(1.0, 0.0)
    with pytest.raises(ExecutionConstraintError,
                       match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        stopping_speed_cap(-1.0, 4.5)


def test_execution_records_are_immutable():
    result = planner().plan(
        source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    with pytest.raises(FrozenInstanceError):
        result.graph_status = "CHANGED"
