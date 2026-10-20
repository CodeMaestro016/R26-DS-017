# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ConflictZoneExecutionPlanner, ExecutionConstraintError, build_speed_constraint, stopping_speed_cap from
# negotiation_execution for the operations below.
from negotiation_execution import (ConflictZoneExecutionPlanner,
    ExecutionConstraintError, build_speed_constraint, stopping_speed_cap)


# Planner using the inputs and processing steps below.
# Output: the result of ConflictZoneExecutionPlanner(paths, the result of ConflictZoneManager(paths)).
def planner():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Return the result of ConflictZoneExecutionPlanner(paths, the result of ConflictZoneManager(paths)) to the
    # caller.
    return ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))


# Check yielding to priority ready set uses outgoing edges using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_yielding_to_priority_ready_set_uses_outgoing_edges():
    # Set result to the result of planner().plan().
    result = planner().plan(
        # Supply source_snapshot_id as a tuple containing the text 's'.
        # Supply effective_coordination_graph as a tuple containing a tuple containing the text 'A', the text 'B'.
        source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B'.
        active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'W_IN_0_LEFT' under 'B'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'NO_PROPOSAL'.
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    # Require result.ready_vehicle_ids equals a tuple containing the text 'B'; otherwise raise AssertionError.
    assert result.ready_vehicle_ids == ("B",)
    # Require result.blocked_vehicle_ids equals a tuple containing the text 'A'; otherwise raise AssertionError.
    assert result.blocked_vehicle_ids == ("A",)
    # Require result.constraints[0].yielding_vehicle_id equals the text 'A'; otherwise raise AssertionError.
    assert result.constraints[0].yielding_vehicle_id == "A"
    # Require result.constraints[0].priority_vehicle_id equals the text 'B'; otherwise raise AssertionError.
    assert result.constraints[0].priority_vehicle_id == "B"


# Check cycle blocks every ready vehicle and is order invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_cycle_blocks_every_ready_vehicle_and_is_order_invariant():
    # Set kwargs to a dictionary built from the supplied values.
    kwargs = dict(source_snapshot_id=("s",), active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'W_IN_0_LEFT' under 'B'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'NO_PROPOSAL'.
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    # Set first to the result of planner().plan().
    first = planner().plan(effective_coordination_graph=(("A", "B"), ("B", "A")), **kwargs)
    # Set second to the result of planner().plan().
    second = planner().plan(effective_coordination_graph=(("B", "A"), ("A", "B")), **kwargs)
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Require first.graph_status equals the text 'EXECUTION_BLOCKED_PRECEDENCE_CYCLE'; otherwise raise
    # AssertionError.
    assert first.graph_status == "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
    # Require first.ready_vehicle_ids equals an empty tuple; otherwise raise AssertionError.
    assert first.ready_vehicle_ids == ()


# Check zone clearance releases without delay using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_zone_clearance_releases_without_delay():
    # Set p to the result of planner().
    p = planner()
    # Set kwargs to a dictionary built from the supplied values.
    kwargs = dict(source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B'.
        active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'W_IN_0_LEFT' under 'B'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'AGREEMENT_ESTABLISHED'.
        timestamp=1.0, source_protocol_state="AGREEMENT_ESTABLISHED")
    # Set blocked to the result of p.plan().
    blocked = p.plan(**kwargs)
    # Set zone to blocked.constraints[0].conflict_zone_id.
    zone = blocked.constraints[0].conflict_zone_id
    # Set released to the result of p.plan().
    released = p.plan(**kwargs, cleared_vehicle_zones=(("B", zone),))
    # Require released.vehicle_permissions[0].permission_status equals the text 'PERMITTED'; otherwise raise
    # AssertionError.
    assert released.vehicle_permissions[0].permission_status == "PERMITTED"
    # Require the text 'A' belongs to released.ready_vehicle_ids; otherwise raise AssertionError.
    assert "A" in released.ready_vehicle_ids


# Check stopping envelope uses exact kinematics and no margin using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stopping_envelope_uses_exact_kinematics_and_no_margin():
    # Require the result of stopping_speed_cap(0.0, 4.5) equals 0.0; otherwise raise AssertionError.
    assert stopping_speed_cap(0.0, 4.5) == 0.0
    # Require the result of stopping_speed_cap(2.0, 4.5) equals the result of pytest.approx(18.0 raised to the
    # power 0.5); otherwise raise AssertionError.
    assert stopping_speed_cap(2.0, 4.5) == pytest.approx((18.0) ** 0.5)
    # Set record to the result of build_speed_constraint(the text 'A', the text 'Z', 2.0, 4.5, 1.0).
    record = build_speed_constraint("A", "Z", 2.0, 4.5, 1.0)
    # Require record.provenance at 'equation' equals the text 'v_cap=sqrt(2*b*d_entry)'; otherwise raise
    # AssertionError.
    assert record.provenance["equation"] == "v_cap=sqrt(2*b*d_entry)"
    # Require record.provenance at 'arbitrary_margin_meters' equals the text '0'; otherwise raise AssertionError.
    assert record.provenance["arbitrary_margin_meters"] == "0"
    # Enter the result of pytest.raises(ExecutionConstraintError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExecutionConstraintError,
                       # Supply match as the text 'EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE'.
                       match="EXECUTION_CONSTRAINT_NOT_PHYSICALLY_FEASIBLE"):
        # Call build_speed_constraint with the supplied arguments.
        build_speed_constraint("A", "Z", 1.0, 4.5, 4.0)


# Check missing deceleration and negative distance rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_missing_deceleration_and_negative_distance_rejected():
    # Enter the result of pytest.raises(ExecutionConstraintError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExecutionConstraintError,
                       # Supply match as the text 'COMFORTABLE_DECELERATION_UNAVAILABLE'.
                       match="COMFORTABLE_DECELERATION_UNAVAILABLE"):
        # Call stopping_speed_cap with the supplied arguments.
        stopping_speed_cap(1.0, 0.0)
    # Enter the result of pytest.raises(ExecutionConstraintError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExecutionConstraintError,
                       # Supply match as the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'.
                       match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        # Call stopping_speed_cap with the supplied arguments.
        stopping_speed_cap(-1.0, 4.5)


# Check execution records are immutable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_execution_records_are_immutable():
    # Set result to the result of planner().plan().
    result = planner().plan(
        # Supply source_snapshot_id as a tuple containing the text 's'.
        # Supply effective_coordination_graph as a tuple containing a tuple containing the text 'A', the text 'B'.
        source_snapshot_id=("s",), effective_coordination_graph=(("A", "B"),),
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B'.
        active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'W_IN_0_LEFT' under 'B'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT", "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'NO_PROPOSAL'.
        timestamp=1.0, source_protocol_state="NO_PROPOSAL")
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set result.graph_status to the text 'CHANGED'.
        result.graph_status = "CHANGED"
