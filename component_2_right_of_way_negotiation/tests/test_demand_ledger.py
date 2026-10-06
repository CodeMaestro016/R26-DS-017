from dataclasses import FrozenInstanceError
import inspect

import pytest

from traffic_accounting import (
    DemandLedgerSemanticError, DemandScheduleSource, SimulationLifecycleEvents,
    VehicleDemandLedger, VehicleDemandStatus,
)


def register(ledger, vehicle_id="AV_0", time=0.0,
             source=DemandScheduleSource.INITIAL_SIMULATION_DEMAND, metadata=None):
    return ledger.register_scheduled_vehicle(
        vehicle_id, time, source, metadata or {}, {"source": "TEST"}
    )


@pytest.mark.parametrize("source,time", [
    (DemandScheduleSource.INITIAL_SIMULATION_DEMAND, 0.0),
    (DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE, 6.0),
    (DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE, 8.0),
])
def test_exact_schedule_sources_are_retained(source, time):
    ledger = VehicleDemandLedger()
    record = register(ledger, time=time, source=source)
    assert record.scheduled_spawn_time == time
    assert record.schedule_source is source


def test_delayed_departure_preserves_both_clocks():
    ledger = VehicleDemandLedger(); register(ledger, time=1.0)
    record = ledger.record_actual_departure("AV_0", 3.0)
    assert (record.scheduled_spawn_time, record.actual_departure_time) == (1.0, 3.0)
    assert record.completion_status is VehicleDemandStatus.ACTIVE_IN_NETWORK


def test_scheduled_never_departed_and_departed_unfinished():
    ledger = VehicleDemandLedger(); register(ledger, "AV_0", 1.0)
    register(ledger, "AV_1", 2.0); ledger.record_actual_departure("AV_1", 3.0)
    ledger.finalize_episode(10.0)
    assert ledger.get_vehicle_record("AV_0").completion_status is VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END
    assert ledger.get_vehicle_record("AV_1").completion_status is VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END
    assert ledger.get_vehicle_record("AV_0").actual_departure_time is None
    assert ledger.get_vehicle_record("AV_1").service_completion_time is None


def test_completed_vehicle_has_three_exact_clocks():
    ledger = VehicleDemandLedger(); register(ledger, time=1.0)
    ledger.record_actual_departure("AV_0", 2.0)
    record = ledger.record_service_completion("AV_0", 5.0)
    assert (record.scheduled_spawn_time, record.actual_departure_time,
            record.service_completion_time) == (1.0, 2.0, 5.0)
    assert record.completion_status is VehicleDemandStatus.SERVICE_COMPLETED


@pytest.mark.parametrize("operation,code", [
    (lambda ledger: ledger.record_actual_departure("AV_X", 1.0), "DEPARTURE_WITHOUT_SCHEDULE_RECORD"),
    (lambda ledger: ledger.record_service_completion("AV_X", 1.0), "ARRIVAL_WITHOUT_SCHEDULE_RECORD"),
])
def test_event_without_schedule_rejected(operation, code):
    with pytest.raises(DemandLedgerSemanticError, match=code):
        operation(VehicleDemandLedger())


def test_arrival_without_departure_rejected():
    ledger = VehicleDemandLedger(); register(ledger)
    with pytest.raises(DemandLedgerSemanticError, match="ARRIVAL_WITHOUT_DEPARTURE_RECORD"):
        ledger.record_service_completion("AV_0", 1.0)


def test_invalid_time_orders_rejected():
    ledger = VehicleDemandLedger(); register(ledger, time=2.0)
    with pytest.raises(DemandLedgerSemanticError, match="DEPARTURE_PRECEDES_SCHEDULE"):
        ledger.record_actual_departure("AV_0", 1.0)
    ledger.record_actual_departure("AV_0", 3.0)
    with pytest.raises(DemandLedgerSemanticError, match="ARRIVAL_PRECEDES_DEPARTURE"):
        ledger.record_service_completion("AV_0", 2.0)


def test_duplicate_schedule_rejected_and_events_idempotent_only_if_exact():
    ledger = VehicleDemandLedger(); register(ledger)
    with pytest.raises(DemandLedgerSemanticError, match="DUPLICATE_SCHEDULED_VEHICLE"):
        register(ledger)
    first = ledger.record_actual_departure("AV_0", 1.0)
    assert ledger.record_actual_departure("AV_0", 1.0) is first
    with pytest.raises(DemandLedgerSemanticError, match="CONFLICTING_DEPARTURE_EVENT"):
        ledger.record_actual_departure("AV_0", 2.0)
    completed = ledger.record_service_completion("AV_0", 3.0)
    assert ledger.record_service_completion("AV_0", 3.0) is completed
    with pytest.raises(DemandLedgerSemanticError, match="CONFLICTING_SERVICE_COMPLETION_EVENT"):
        ledger.record_service_completion("AV_0", 4.0)


def test_same_step_lifecycle_snapshot_is_consumed_exactly():
    ledger = VehicleDemandLedger(); register(ledger)
    ledger.record_lifecycle_events(SimulationLifecycleEvents(1.0, ("AV_0",), ()))
    ledger.record_lifecycle_events(SimulationLifecycleEvents(2.0, (), ("AV_0",)))
    record = ledger.get_vehicle_record("AV_0")
    assert record.actual_departure_time == 1.0
    assert record.service_completion_time == 2.0


def test_records_metadata_and_history_are_immutable_copies():
    metadata = {"route_id": "audit-only"}
    ledger = VehicleDemandLedger(); record = register(ledger, metadata=metadata)
    metadata["route_id"] = "changed"
    assert record.route_or_movement_metadata["route_id"] == "audit-only"
    with pytest.raises((TypeError, FrozenInstanceError)):
        record.scheduled_spawn_time = 9.0
    with pytest.raises(TypeError):
        record.route_or_movement_metadata["x"] = "y"


def test_reset_clears_every_record():
    ledger = VehicleDemandLedger(); register(ledger); ledger.reset()
    assert ledger.get_all_records() == ()


def test_registration_order_is_semantically_invariant():
    def result(order):
        ledger = VehicleDemandLedger()
        for vehicle_id in order:
            register(ledger, vehicle_id, float(vehicle_id[-1]))
        return ledger.get_all_records()
    assert result(("AV_0", "AV_1", "AV_2")) == result(("AV_2", "AV_0", "AV_1"))


def test_periodic_batch_vehicles_share_exact_schedule_time():
    ledger = VehicleDemandLedger()
    for vehicle_id in ("AV_2", "AV_0", "AV_1"):
        register(ledger, vehicle_id, 12.0, DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE)
    assert {item.scheduled_spawn_time for item in ledger.get_all_records()} == {12.0}


def test_ledger_contract_has_no_actor_critic_or_policy_inputs():
    parameters = set(inspect.signature(VehicleDemandLedger.register_scheduled_vehicle).parameters)
    assert parameters.isdisjoint({"action", "actor_logits", "critic_value", "prediction_probability"})


def test_step5h0_source_has_no_control_training_or_objective_calculation():
    from pathlib import Path
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("traffic_accounting").glob("*.py"))
    forbidden = ("traci", "setspeed", "changeLane", "optimizer", "ppo_loss",
                 "advantage", "team_reward", "collision_penalty", "delay_weight",
                 "spawn_delay_threshold", "departure_timeout", "service_timeout")
    assert not any(item.lower() in source for item in forbidden)

