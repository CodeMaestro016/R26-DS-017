# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError
# Import inspect for use in this module.
import inspect

# Import pytest for use in this module.
import pytest

# Import DemandLedgerSemanticError, DemandScheduleSource, SimulationLifecycleEvents, VehicleDemandLedger,
# VehicleDemandStatus from traffic_accounting for the operations below.
from traffic_accounting import (
    DemandLedgerSemanticError, DemandScheduleSource, SimulationLifecycleEvents,
    VehicleDemandLedger, VehicleDemandStatus,
)


# Register using the inputs and processing steps below.
# Input ledger: the supplied ledger.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input time: the supplied time.
# Input source: the supplied source.
# Input metadata: the supplied metadata.
# Output: the result of ledger.register_scheduled_vehicle(vehicle_id, time, source, metadata or an empty
# dictionary, a dictionary containing source).
def register(ledger, vehicle_id="AV_0", time=0.0,
             # Declare source, metadata as input parameters.
             source=DemandScheduleSource.INITIAL_SIMULATION_DEMAND, metadata=None):
    # Return the result of ledger.register_scheduled_vehicle(vehicle_id, time, source, metadata or an empty
    # dictionary, a dictionary containing source) to the caller.
    return ledger.register_scheduled_vehicle(
        # Store the text 'TEST' under 'source'.
        vehicle_id, time, source, metadata or {}, {"source": "TEST"}
    )


# Apply 'source,time' as a decorator to configure the following definition.
@pytest.mark.parametrize("source,time", [
    # Include a tuple containing DemandScheduleSource.INITIAL_SIMULATION_DEMAND, 0.0 in this list.
    (DemandScheduleSource.INITIAL_SIMULATION_DEMAND, 0.0),
    # Include a tuple containing DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE, 6.0 in this list.
    (DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE, 6.0),
    # Include a tuple containing DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE, 8.0 in this list.
    (DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE, 8.0),
])
# Check exact schedule sources are retained using the setup, calls, and assertions below.
# Input source: the supplied source.
# Input time: the supplied time.
# Output: no explicit value; normal completion returns None.
def test_exact_schedule_sources_are_retained(source, time):
    # Set ledger to the result of VehicleDemandLedger().
    ledger = VehicleDemandLedger()
    # Set record to the result of register(ledger).
    record = register(ledger, time=time, source=source)
    # Require record.scheduled_spawn_time equals time; otherwise raise AssertionError.
    assert record.scheduled_spawn_time == time
    # Require record.schedule_source is the same object as source; otherwise raise AssertionError.
    assert record.schedule_source is source


# Check delayed departure preserves both clocks using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_delayed_departure_preserves_both_clocks():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger, time=1.0)
    # Set record to the result of ledger.record_actual_departure(the text 'AV_0', 3.0).
    record = ledger.record_actual_departure("AV_0", 3.0)
    # Require a tuple containing record.scheduled_spawn_time, record.actual_departure_time equals a tuple
    # containing 1.0, 3.0; otherwise raise AssertionError.
    assert (record.scheduled_spawn_time, record.actual_departure_time) == (1.0, 3.0)
    # Require record.completion_status is the same object as VehicleDemandStatus.ACTIVE_IN_NETWORK; otherwise
    # raise AssertionError.
    assert record.completion_status is VehicleDemandStatus.ACTIVE_IN_NETWORK


# Check scheduled never departed and departed unfinished using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_scheduled_never_departed_and_departed_unfinished():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger, "AV_0", 1.0)
    # Call register with the supplied arguments.
    # Call ledger.record_actual_departure with the supplied arguments.
    register(ledger, "AV_1", 2.0); ledger.record_actual_departure("AV_1", 3.0)
    # Call ledger.finalize_episode with the supplied arguments.
    ledger.finalize_episode(10.0)
    # Require ledger.get_vehicle_record('AV_0').completion_status is the same object as
    # VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END; otherwise raise AssertionError.
    assert ledger.get_vehicle_record("AV_0").completion_status is VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END
    # Require ledger.get_vehicle_record('AV_1').completion_status is the same object as
    # VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END; otherwise raise AssertionError.
    assert ledger.get_vehicle_record("AV_1").completion_status is VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END
    # Require ledger.get_vehicle_record('AV_0').actual_departure_time is the same object as None; otherwise raise
    # AssertionError.
    assert ledger.get_vehicle_record("AV_0").actual_departure_time is None
    # Require ledger.get_vehicle_record('AV_1').service_completion_time is the same object as None; otherwise
    # raise AssertionError.
    assert ledger.get_vehicle_record("AV_1").service_completion_time is None


# Check completed vehicle has three exact clocks using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_completed_vehicle_has_three_exact_clocks():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger, time=1.0)
    # Call ledger.record_actual_departure with the supplied arguments.
    ledger.record_actual_departure("AV_0", 2.0)
    # Set record to the result of ledger.record_service_completion(the text 'AV_0', 5.0).
    record = ledger.record_service_completion("AV_0", 5.0)
    # Require a tuple containing record.scheduled_spawn_time, record.actual_departure_time,
    # record.service_completion_time equals a tuple containing 1.0, 2.0, 5.0; otherwise raise AssertionError.
    assert (record.scheduled_spawn_time, record.actual_departure_time,
            # Include record.service_completion_time in this tuple.
            record.service_completion_time) == (1.0, 2.0, 5.0)
    # Require record.completion_status is the same object as VehicleDemandStatus.SERVICE_COMPLETED; otherwise
    # raise AssertionError.
    assert record.completion_status is VehicleDemandStatus.SERVICE_COMPLETED


# Apply 'operation,code' as a decorator to configure the following definition.
@pytest.mark.parametrize("operation,code", [
    # Declare ledger as input parameter.
    (lambda ledger: ledger.record_actual_departure("AV_X", 1.0), "DEPARTURE_WITHOUT_SCHEDULE_RECORD"),
    # Declare ledger as input parameter.
    (lambda ledger: ledger.record_service_completion("AV_X", 1.0), "ARRIVAL_WITHOUT_SCHEDULE_RECORD"),
])
# Check event without schedule rejected using the setup, calls, and assertions below.
# Input operation: the supplied operation.
# Input code: the supplied code.
# Output: no explicit value; normal completion returns None.
def test_event_without_schedule_rejected(operation, code):
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match=code):
        # Call operation with the supplied arguments.
        operation(VehicleDemandLedger())


# Check arrival without departure rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_arrival_without_departure_rejected():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger)
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="ARRIVAL_WITHOUT_DEPARTURE_RECORD"):
        # Call ledger.record_service_completion with the supplied arguments.
        ledger.record_service_completion("AV_0", 1.0)


# Check invalid time orders rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_invalid_time_orders_rejected():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger, time=2.0)
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="DEPARTURE_PRECEDES_SCHEDULE"):
        # Call ledger.record_actual_departure with the supplied arguments.
        ledger.record_actual_departure("AV_0", 1.0)
    # Call ledger.record_actual_departure with the supplied arguments.
    ledger.record_actual_departure("AV_0", 3.0)
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="ARRIVAL_PRECEDES_DEPARTURE"):
        # Call ledger.record_service_completion with the supplied arguments.
        ledger.record_service_completion("AV_0", 2.0)


# Check duplicate schedule rejected and events idempotent only if exact using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_duplicate_schedule_rejected_and_events_idempotent_only_if_exact():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger)
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="DUPLICATE_SCHEDULED_VEHICLE"):
        # Call register with the supplied arguments.
        register(ledger)
    # Set first to the result of ledger.record_actual_departure(the text 'AV_0', 1.0).
    first = ledger.record_actual_departure("AV_0", 1.0)
    # Require the result of ledger.record_actual_departure(the text 'AV_0', 1.0) is the same object as first;
    # otherwise raise AssertionError.
    assert ledger.record_actual_departure("AV_0", 1.0) is first
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="CONFLICTING_DEPARTURE_EVENT"):
        # Call ledger.record_actual_departure with the supplied arguments.
        ledger.record_actual_departure("AV_0", 2.0)
    # Set completed to the result of ledger.record_service_completion(the text 'AV_0', 3.0).
    completed = ledger.record_service_completion("AV_0", 3.0)
    # Require the result of ledger.record_service_completion(the text 'AV_0', 3.0) is the same object as
    # completed; otherwise raise AssertionError.
    assert ledger.record_service_completion("AV_0", 3.0) is completed
    # Enter the result of pytest.raises(DemandLedgerSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(DemandLedgerSemanticError, match="CONFLICTING_SERVICE_COMPLETION_EVENT"):
        # Call ledger.record_service_completion with the supplied arguments.
        ledger.record_service_completion("AV_0", 4.0)


# Check same step lifecycle snapshot is consumed exactly using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_same_step_lifecycle_snapshot_is_consumed_exactly():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger)
    # Call ledger.record_lifecycle_events with the supplied arguments.
    ledger.record_lifecycle_events(SimulationLifecycleEvents(1.0, ("AV_0",), ()))
    # Call ledger.record_lifecycle_events with the supplied arguments.
    ledger.record_lifecycle_events(SimulationLifecycleEvents(2.0, (), ("AV_0",)))
    # Set record to the result of ledger.get_vehicle_record(the text 'AV_0').
    record = ledger.get_vehicle_record("AV_0")
    # Require record.actual_departure_time equals 1.0; otherwise raise AssertionError.
    assert record.actual_departure_time == 1.0
    # Require record.service_completion_time equals 2.0; otherwise raise AssertionError.
    assert record.service_completion_time == 2.0


# Check records metadata and history are immutable copies using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_records_metadata_and_history_are_immutable_copies():
    # Set metadata to a dictionary containing route_id.
    metadata = {"route_id": "audit-only"}
    # Set ledger to the result of VehicleDemandLedger().
    # Set record to the result of register(ledger).
    ledger = VehicleDemandLedger(); record = register(ledger, metadata=metadata)
    # Set metadata['route_id'] to the text 'changed'.
    metadata["route_id"] = "changed"
    # Require record.route_or_movement_metadata at 'route_id' equals the text 'audit-only'; otherwise raise
    # AssertionError.
    assert record.route_or_movement_metadata["route_id"] == "audit-only"
    # Enter the result of pytest.raises(a tuple containing TypeError, FrozenInstanceError) and run the enclosed
    # operations within that context.
    with pytest.raises((TypeError, FrozenInstanceError)):
        # Set record.scheduled_spawn_time to 9.0.
        record.scheduled_spawn_time = 9.0
    # Enter the result of pytest.raises(TypeError) and run the enclosed operations within that context.
    with pytest.raises(TypeError):
        # Set record.route_or_movement_metadata['x'] to the text 'y'.
        record.route_or_movement_metadata["x"] = "y"


# Check reset clears every record using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_reset_clears_every_record():
    # Set ledger to the result of VehicleDemandLedger().
    # Call register with the supplied arguments.
    # Call ledger.reset with the supplied arguments.
    ledger = VehicleDemandLedger(); register(ledger); ledger.reset()
    # Require the result of ledger.get_all_records() equals an empty tuple; otherwise raise AssertionError.
    assert ledger.get_all_records() == ()


# Check registration order is semantically invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_registration_order_is_semantically_invariant():
    # Result using the inputs and processing steps below.
    # Input order: the supplied order.
    # Output: the result of ledger.get_all_records().
    # Processing: iterate over the relevant records.
    def result(order):
        # Set ledger to the result of VehicleDemandLedger().
        ledger = VehicleDemandLedger()
        # Iterate over order, binding each item to vehicle_id.
        for vehicle_id in order:
            # Call register with the supplied arguments.
            register(ledger, vehicle_id, float(vehicle_id[-1]))
        # Return the result of ledger.get_all_records() to the caller.
        return ledger.get_all_records()
    # Require the result of result(a tuple containing the text 'AV_0', the text 'AV_1', the text 'AV_2') equals
    # the result of result(a tuple containing the text 'AV_2', the text 'AV_0', the text 'AV_1'); otherwise raise
    # AssertionError.
    assert result(("AV_0", "AV_1", "AV_2")) == result(("AV_2", "AV_0", "AV_1"))


# Check periodic batch vehicles share exact schedule time using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_periodic_batch_vehicles_share_exact_schedule_time():
    # Set ledger to the result of VehicleDemandLedger().
    ledger = VehicleDemandLedger()
    # Iterate over a tuple containing the text 'AV_2', the text 'AV_0', the text 'AV_1', binding each item to
    # vehicle_id.
    for vehicle_id in ("AV_2", "AV_0", "AV_1"):
        # Call register with the supplied arguments.
        register(ledger, vehicle_id, 12.0, DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE)
    # Require a set of item.scheduled_spawn_time for item in the result of ledger.get_all_records() equals a set
    # containing 12.0; otherwise raise AssertionError.
    assert {item.scheduled_spawn_time for item in ledger.get_all_records()} == {12.0}


# Check ledger contract has no actor critic or policy inputs using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ledger_contract_has_no_actor_critic_or_policy_inputs():
    # Set parameters to a set built from
    # inspect.signature(VehicleDemandLedger.register_scheduled_vehicle).parameters.
    parameters = set(inspect.signature(VehicleDemandLedger.register_scheduled_vehicle).parameters)
    # Require the result of parameters.isdisjoint(a set containing the text 'action', the text 'actor_logits', the
    # text 'critic_value', the text...); otherwise raise AssertionError.
    assert parameters.isdisjoint({"action", "actor_logits", "critic_value", "prediction_probability"})


# Check step5h0 source has no control training or objective calculation using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_step5h0_source_has_no_control_training_or_objective_calculation():
    # Import Path from pathlib for the operations below.
    from pathlib import Path
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('traffic_accounting').glob(the text '*.py') as part of the
                       # enclosing expression.
                       for path in Path("traffic_accounting").glob("*.py"))
    # Set forbidden to a tuple containing the text 'traci', the text 'setspeed', the text 'changeLane', the text
    # 'optimizer', the text 'ppo_loss',...
    forbidden = ("traci", "setspeed", "changeLane", "optimizer", "ppo_loss",
                 "advantage", "team_reward", "collision_penalty", "delay_weight",
                 "spawn_delay_threshold", "departure_timeout", "service_timeout")
    # Require the negation of whether any item is true in a lazy sequence of item.lower() belongs to source for
    # item in forbidden; otherwise raise AssertionError.
    assert not any(item.lower() in source for item in forbidden)

