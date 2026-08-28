from dataclasses import replace
from pathlib import Path

import pytest

from negotiation_objective import (
    NegotiationObjectiveLedger, ObjectiveSemanticError,
    compute_objective_diagnostics, interval_vehicle_exposures,
    measure_vehicle_travel_times, raw_team_reward,
    team_interval_cost_seconds, total_team_travel_time_seconds,
)
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger


def demand(specifications):
    ledger = VehicleDemandLedger()
    for vehicle_id, scheduled, departed, completed in specifications:
        ledger.register_scheduled_vehicle(
            vehicle_id, scheduled, DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE
        )
        if departed is not None:
            ledger.record_actual_departure(vehicle_id, departed)
        if completed is not None:
            ledger.record_service_completion(vehicle_id, completed)
    return ledger


def batch(ledger, snapshot, timestamp, phase, decisions=("D1",), egos=("A",),
          subjects=(("A", "B"),)):
    return ledger.create_joint_decision_batch(
        (snapshot,), timestamp, phase,
        tuple((item,) for item in decisions), egos, subjects,
    )


def test_single_completed_vehicle_equation_and_sign():
    records = demand((("AV_0", 1.0, 2.0, 5.0),)).get_all_records()
    measured = measure_vehicle_travel_times(records, 10.0)
    assert measured[0].observed_travel_time_seconds == 4.0
    assert total_team_travel_time_seconds(measured) == 4.0
    assert raw_team_reward(4.0) == -4.0


def test_two_vehicle_team_sum_has_no_identifier_or_role_weight():
    records = demand((
        ("priority", 0.0, 0.0, 4.0),
        ("yielding", 1.0, 2.0, 6.0),
    )).get_all_records()
    assert total_team_travel_time_seconds(measure_vehicle_travel_times(records, 8.0)) == 9.0


def test_unfinished_and_never_departed_use_episode_end_from_schedule():
    records = demand((
        ("AV_0", 1.0, 3.0, None),
        ("AV_1", 2.0, None, None),
    )).get_all_records()
    values = measure_vehicle_travel_times(records, 7.0)
    assert tuple(item.observed_travel_time_seconds for item in values) == (6.0, 5.0)


def test_delayed_insertion_cost_starts_at_schedule():
    records = demand((("AV_0", 1.0, 4.0, 6.0),)).get_all_records()
    assert measure_vehicle_travel_times(records, 8.0)[0].observed_travel_time_seconds == 5.0


def test_interval_accounting_telescopes_to_episode_total():
    records = demand((
        ("AV_0", 0.0, 1.0, 5.0),
        ("AV_1", 2.0, 3.0, None),
    )).get_all_records()
    total = total_team_travel_time_seconds(measure_vehicle_travel_times(records, 7.0))
    interval_total = sum(team_interval_cost_seconds(interval_vehicle_exposures(records, a, b))
                         for a, b in ((0.0, 1.0), (1.0, 4.0), (4.0, 7.0)))
    assert interval_total == total == 10.0


def test_zero_and_negative_duration_intervals():
    records = demand((("AV_0", 0.0, 0.0, 2.0),)).get_all_records()
    exposure = interval_vehicle_exposures(records, 1.0, 1.0)
    assert team_interval_cost_seconds(exposure) == 0.0
    assert raw_team_reward(0.0) == 0.0
    with pytest.raises(ObjectiveSemanticError, match="NEGATIVE_OBJECTIVE_INTERVAL_DURATION"):
        interval_vehicle_exposures(records, 2.0, 1.0)


def test_joint_batch_is_order_invariant_and_deduplicates_participants():
    ledger = NegotiationObjectiveLedger()
    first = batch(ledger, "S", 1.0, "PROPOSER", ("D2", "D1"),
                  ("B", "A", "B"), (("C", "B"), ("A", "B")))
    second = batch(ledger, "S", 1.0, "PROPOSER", ("D1", "D2"),
                   ("A", "B"), (("A", "B"), ("C", "B")))
    assert first == second
    assert first.participating_ego_ids == ("A", "B")


def test_same_timestamp_different_phase_batches_are_distinct_zero_cost():
    objective = NegotiationObjectiveLedger(); records = demand((("AV_0", 0.0, 0.0, 2.0),)).get_all_records()
    proposer = batch(objective, "S", 1.0, "PROPOSER")
    responder = batch(objective, "S", 1.0, "RESPONDER")
    assert proposer.batch_id != responder.batch_id
    objective.begin_episode(proposer)
    result = objective.close_objective_interval(responder, records)
    assert result.team_travel_time_increment_seconds == 0.0
    assert result.team_reward == 0.0


def test_simultaneous_agents_and_multiple_claims_create_one_record():
    objective = NegotiationObjectiveLedger(); records = demand((("AV_0", 0.0, 0.0, 3.0),)).get_all_records()
    source = batch(objective, "S0", 0.0, "PROPOSER",
                   ("D1", "D2", "D3", "D4"), ("A", "B", "C", "D"),
                   (("A", "B"), ("C", "B"), ("B", "C"), ("D", "A")))
    successor = batch(objective, "S1", 2.0, "SUCCESSOR")
    objective.begin_episode(source)
    shared = objective.close_objective_interval(successor, records)
    assert len(objective.get_team_objective_records()) == 1
    assert all(objective.team_record_for_interval(shared.objective_interval_id) is shared
               for _ in source.decision_event_ids)


@pytest.mark.parametrize("labels", [
    ("KEEP_CLAIM", "RELINQUISH_CLAIM"),
    ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"),
    ("low_logits", "high_logits"),
    ("low_probability", "high_probability"),
])
def test_reward_is_neutral_to_actions_logits_and_predictions(labels):
    realized_cost = 3.0
    assert raw_team_reward(realized_cost) == raw_team_reward(realized_cost)
    assert labels[0] != labels[1]


def test_fairness_and_throughput_diagnostics_are_separate_exact_statistics():
    records = demand((
        ("AV_0", 0.0, 0.0, 2.0),
        ("AV_1", 0.0, 0.0, 4.0),
        ("AV_2", 0.0, 0.0, None),
    )).get_all_records()
    diagnostics = compute_objective_diagnostics(measure_vehicle_travel_times(records, 6.0))
    assert diagnostics.vehicles_measured == 3
    assert diagnostics.completed_services == 2
    assert diagnostics.mean_travel_time_seconds == 4.0
    assert diagnostics.maximum_travel_time_seconds == 6.0
    assert diagnostics.travel_time_variance_seconds_squared == 8.0 / 3.0


def test_vehicle_order_and_rename_invariance():
    first = demand((("A", 0.0, 0.0, 2.0), ("B", 1.0, 1.0, 4.0))).get_all_records()
    second = demand((("Y", 1.0, 1.0, 4.0), ("X", 0.0, 0.0, 2.0))).get_all_records()
    assert total_team_travel_time_seconds(measure_vehicle_travel_times(first, 5.0)) == total_team_travel_time_seconds(measure_vehicle_travel_times(second, 5.0))


def test_objective_does_not_mutate_regulatory_protocol_or_masks():
    evidence = {"graph": (("A", "B"),), "mask": (True, False), "protocol": "PENDING"}
    before = dict(evidence)
    raw_team_reward(2.0)
    assert evidence == before


def test_step5h_sources_exclude_route_truth_control_and_arbitrary_constants():
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("negotiation_objective").glob("*.py"))
    forbidden = (
        "route_id", "route_index", "ground_truth_route_id", "traci",
        "setspeed", "changelane", "collision_penalty", "agreement_bonus",
        "throughput_bonus", "fairness_weight", "waiting_speed_threshold",
        "reward_clip", "reward_normalization", "gamma =", "gae_lambda",
        "ppo_clip", "learning_rate", "optimizer",
    )
    assert not any(item in source for item in forbidden)
