# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest

# Import NegotiationObjectiveLedger, ObjectiveSemanticError, compute_objective_diagnostics,
# interval_vehicle_exposures, measure_vehicle_travel_times, raw_team_reward,... from negotiation_objective for the
# operations below.
from negotiation_objective import (
    NegotiationObjectiveLedger, ObjectiveSemanticError,
    compute_objective_diagnostics, interval_vehicle_exposures,
    measure_vehicle_travel_times, raw_team_reward,
    team_interval_cost_seconds, total_team_travel_time_seconds,
)
# Import DemandScheduleSource, VehicleDemandLedger from traffic_accounting for the operations below.
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger


# Demand using the inputs and processing steps below.
# Input specifications: the supplied specifications.
# Output: ledger.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def demand(specifications):
    # Set ledger to the result of VehicleDemandLedger().
    ledger = VehicleDemandLedger()
    # Iterate over specifications, binding each item to (vehicle_id, scheduled, departed, completed).
    for vehicle_id, scheduled, departed, completed in specifications:
        # Call ledger.register_scheduled_vehicle with the supplied arguments.
        ledger.register_scheduled_vehicle(
            # Supply DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE to ledger.register_scheduled_vehicle.
            vehicle_id, scheduled, DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE
        )
        # Run this branch when departed is a different object from None.
        if departed is not None:
            # Call ledger.record_actual_departure with the supplied arguments.
            ledger.record_actual_departure(vehicle_id, departed)
        # Run this branch when completed is a different object from None.
        if completed is not None:
            # Call ledger.record_service_completion with the supplied arguments.
            ledger.record_service_completion(vehicle_id, completed)
    # Return ledger to the caller.
    return ledger


# Batch using the inputs and processing steps below.
# Input ledger: the supplied ledger.
# Input snapshot: the supplied snapshot.
# Input timestamp: the supplied timestamp.
# Input phase: the supplied phase.
# Input decisions: the supplied decisions.
# Input egos: the supplied egos.
# Input subjects: the supplied subjects.
# Output: the result of ledger.create_joint_decision_batch(a tuple containing snapshot, timestamp, phase, a tuple
# built from a lazy sequence of a tuple...).
def batch(ledger, snapshot, timestamp, phase, decisions=("D1",), egos=("A",),
          # Declare subjects as input parameter.
          subjects=(("A", "B"),)):
    # Return the result of ledger.create_joint_decision_batch(a tuple containing snapshot, timestamp, phase, a
    # tuple built from a lazy sequence of a tuple...) to the caller.
    return ledger.create_joint_decision_batch(
        # Supply a tuple containing snapshot to ledger.create_joint_decision_batch.
        (snapshot,), timestamp, phase,
        # Supply a tuple built from a lazy sequence of a tuple containing item for item in decisions to
        # ledger.create_joint_decision_batch.
        tuple((item,) for item in decisions), egos, subjects,
    )


# Check single completed vehicle equation and sign using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_single_completed_vehicle_equation_and_sign():
    # Set records to the result of demand((('AV_0', 1.0, 2.0, 5.0),)).get_all_records().
    records = demand((("AV_0", 1.0, 2.0, 5.0),)).get_all_records()
    # Set measured to the result of measure_vehicle_travel_times(records, 10.0).
    measured = measure_vehicle_travel_times(records, 10.0)
    # Require measured[0].observed_travel_time_seconds equals 4.0; otherwise raise AssertionError.
    assert measured[0].observed_travel_time_seconds == 4.0
    # Require the result of total_team_travel_time_seconds(measured) equals 4.0; otherwise raise AssertionError.
    assert total_team_travel_time_seconds(measured) == 4.0
    # Require the result of raw_team_reward(4.0) equals the negative of 4.0; otherwise raise AssertionError.
    assert raw_team_reward(4.0) == -4.0


# Check two vehicle team sum has no identifier or role weight using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_vehicle_team_sum_has_no_identifier_or_role_weight():
    # Set records to the result of demand((('priority', 0.0, 0.0, 4.0), ('yielding', 1.0, 2.0,
    # 6.0))).get_all_records().
    records = demand((
        # Include a tuple containing the text 'priority', 0.0, 0.0, 4.0 in this tuple.
        ("priority", 0.0, 0.0, 4.0),
        # Include a tuple containing the text 'yielding', 1.0, 2.0, 6.0 in this tuple.
        ("yielding", 1.0, 2.0, 6.0),
    )).get_all_records()
    # Require the result of total_team_travel_time_seconds(the result of measure_vehicle_travel_times(records,
    # 8.0)) equals 9.0; otherwise raise AssertionError.
    assert total_team_travel_time_seconds(measure_vehicle_travel_times(records, 8.0)) == 9.0


# Check unfinished and never departed use episode end from schedule using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unfinished_and_never_departed_use_episode_end_from_schedule():
    # Set records to the result of demand((('AV_0', 1.0, 3.0, None), ('AV_1', 2.0, None,
    # None))).get_all_records().
    records = demand((
        # Include a tuple containing the text 'AV_0', 1.0, 3.0, None in this tuple.
        ("AV_0", 1.0, 3.0, None),
        # Include a tuple containing the text 'AV_1', 2.0, None, None in this tuple.
        ("AV_1", 2.0, None, None),
    )).get_all_records()
    # Set values to the result of measure_vehicle_travel_times(records, 7.0).
    values = measure_vehicle_travel_times(records, 7.0)
    # Require a tuple built from a lazy sequence of item.observed_travel_time_seconds for item in values equals a
    # tuple containing 6.0, 5.0; otherwise raise AssertionError.
    assert tuple(item.observed_travel_time_seconds for item in values) == (6.0, 5.0)


# Check delayed insertion cost starts at schedule using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_delayed_insertion_cost_starts_at_schedule():
    # Set records to the result of demand((('AV_0', 1.0, 4.0, 6.0),)).get_all_records().
    records = demand((("AV_0", 1.0, 4.0, 6.0),)).get_all_records()
    # Require measure_vehicle_travel_times(records, 8.0)[0].observed_travel_time_seconds equals 5.0; otherwise
    # raise AssertionError.
    assert measure_vehicle_travel_times(records, 8.0)[0].observed_travel_time_seconds == 5.0


# Check interval accounting telescopes to episode total using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_interval_accounting_telescopes_to_episode_total():
    # Set records to the result of demand((('AV_0', 0.0, 1.0, 5.0), ('AV_1', 2.0, 3.0, None))).get_all_records().
    records = demand((
        # Include a tuple containing the text 'AV_0', 0.0, 1.0, 5.0 in this tuple.
        ("AV_0", 0.0, 1.0, 5.0),
        # Include a tuple containing the text 'AV_1', 2.0, 3.0, None in this tuple.
        ("AV_1", 2.0, 3.0, None),
    )).get_all_records()
    # Set total to the result of total_team_travel_time_seconds(the result of
    # measure_vehicle_travel_times(records, 7.0)).
    total = total_team_travel_time_seconds(measure_vehicle_travel_times(records, 7.0))
    # Set interval_total to the sum of a lazy sequence of the result of team_interval_cost_seconds(the result of
    # interval_vehicle_exposures(records, a, b)) for (a, b) in a tuple containing a tuple containing 0.0, 1.0, a
    # tuple containing 1.0, 4.0, a tuple containing 4.0, 7.0.
    interval_total = sum(team_interval_cost_seconds(interval_vehicle_exposures(records, a, b))
                         # Evaluate a tuple containing a tuple containing 0.0, 1.0, a tuple containing 1.0, 4.0, a
                         # tuple containing 4.0, 7.0 as part of the enclosing expression.
                         for a, b in ((0.0, 1.0), (1.0, 4.0), (4.0, 7.0)))
    # Require interval_total equals total; equals 10.0; otherwise raise AssertionError.
    assert interval_total == total == 10.0


# Check zero and negative duration intervals using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_zero_and_negative_duration_intervals():
    # Set records to the result of demand((('AV_0', 0.0, 0.0, 2.0),)).get_all_records().
    records = demand((("AV_0", 0.0, 0.0, 2.0),)).get_all_records()
    # Set exposure to the result of interval_vehicle_exposures(records, 1.0, 1.0).
    exposure = interval_vehicle_exposures(records, 1.0, 1.0)
    # Require the result of team_interval_cost_seconds(exposure) equals 0.0; otherwise raise AssertionError.
    assert team_interval_cost_seconds(exposure) == 0.0
    # Require the result of raw_team_reward(0.0) equals 0.0; otherwise raise AssertionError.
    assert raw_team_reward(0.0) == 0.0
    # Enter the result of pytest.raises(ObjectiveSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(ObjectiveSemanticError, match="NEGATIVE_OBJECTIVE_INTERVAL_DURATION"):
        # Call interval_vehicle_exposures with the supplied arguments.
        interval_vehicle_exposures(records, 2.0, 1.0)


# Check joint batch is order invariant and deduplicates participants using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_joint_batch_is_order_invariant_and_deduplicates_participants():
    # Set ledger to the result of NegotiationObjectiveLedger().
    ledger = NegotiationObjectiveLedger()
    # Set first to the result of batch(ledger, the text 'S', 1.0, the text 'PROPOSER', a tuple containing the text
    # 'D2', the text 'D1',...).
    first = batch(ledger, "S", 1.0, "PROPOSER", ("D2", "D1"),
                  # Supply a tuple containing a tuple containing the text 'C', the text 'B', a tuple containing
                  # the text 'A', the text 'B' to batch.
                  ("B", "A", "B"), (("C", "B"), ("A", "B")))
    # Set second to the result of batch(ledger, the text 'S', 1.0, the text 'PROPOSER', a tuple containing the
    # text 'D1', the text 'D2',...).
    second = batch(ledger, "S", 1.0, "PROPOSER", ("D1", "D2"),
                   # Supply a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing
                   # the text 'C', the text 'B' to batch.
                   ("A", "B"), (("A", "B"), ("C", "B")))
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Require first.participating_ego_ids equals a tuple containing the text 'A', the text 'B'; otherwise raise
    # AssertionError.
    assert first.participating_ego_ids == ("A", "B")


# Check same timestamp different phase batches are distinct zero cost using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_same_timestamp_different_phase_batches_are_distinct_zero_cost():
    # Set objective to the result of NegotiationObjectiveLedger().
    # Set records to the result of demand((('AV_0', 0.0, 0.0, 2.0),)).get_all_records().
    objective = NegotiationObjectiveLedger(); records = demand((("AV_0", 0.0, 0.0, 2.0),)).get_all_records()
    # Set proposer to the result of batch(objective, the text 'S', 1.0, the text 'PROPOSER').
    proposer = batch(objective, "S", 1.0, "PROPOSER")
    # Set responder to the result of batch(objective, the text 'S', 1.0, the text 'RESPONDER').
    responder = batch(objective, "S", 1.0, "RESPONDER")
    # Require proposer.batch_id differs from responder.batch_id; otherwise raise AssertionError.
    assert proposer.batch_id != responder.batch_id
    # Call objective.begin_episode with the supplied arguments.
    objective.begin_episode(proposer)
    # Set result to the result of objective.close_objective_interval(responder, records).
    result = objective.close_objective_interval(responder, records)
    # Require result.team_travel_time_increment_seconds equals 0.0; otherwise raise AssertionError.
    assert result.team_travel_time_increment_seconds == 0.0
    # Require result.team_reward equals 0.0; otherwise raise AssertionError.
    assert result.team_reward == 0.0


# Check simultaneous agents and multiple claims create one record using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_simultaneous_agents_and_multiple_claims_create_one_record():
    # Set objective to the result of NegotiationObjectiveLedger().
    # Set records to the result of demand((('AV_0', 0.0, 0.0, 3.0),)).get_all_records().
    objective = NegotiationObjectiveLedger(); records = demand((("AV_0", 0.0, 0.0, 3.0),)).get_all_records()
    # Set source to the result of batch(objective, the text 'S0', 0.0, the text 'PROPOSER', a tuple containing the
    # text 'D1', the text...).
    source = batch(objective, "S0", 0.0, "PROPOSER",
                   # Supply a tuple containing the text 'D1', the text 'D2', the text 'D3', the text 'D4' to
                   # batch.
                   ("D1", "D2", "D3", "D4"), ("A", "B", "C", "D"),
                   # Supply a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing
                   # the text 'C', the text 'B', a tuple... to batch.
                   (("A", "B"), ("C", "B"), ("B", "C"), ("D", "A")))
    # Set successor to the result of batch(objective, the text 'S1', 2.0, the text 'SUCCESSOR').
    successor = batch(objective, "S1", 2.0, "SUCCESSOR")
    # Call objective.begin_episode with the supplied arguments.
    objective.begin_episode(source)
    # Set shared to the result of objective.close_objective_interval(successor, records).
    shared = objective.close_objective_interval(successor, records)
    # Require the number of entries in the result of objective.get_team_objective_records() equals 1; otherwise
    # raise AssertionError.
    assert len(objective.get_team_objective_records()) == 1
    # Require whether every item is true in a lazy sequence of the result of
    # objective.team_record_for_interval(shared.objective_interval_id) is the same object as shared for _ in
    # source.decision_event_ids; otherwise raise AssertionError.
    assert all(objective.team_record_for_interval(shared.objective_interval_id) is shared
               # Evaluate source.decision_event_ids as part of the enclosing expression.
               for _ in source.decision_event_ids)


# Apply 'labels' as a decorator to configure the following definition.
@pytest.mark.parametrize("labels", [
    # Include a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' in this list.
    ("KEEP_CLAIM", "RELINQUISH_CLAIM"),
    # Include a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT' in this list.
    ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"),
    # Include a tuple containing the text 'low_logits', the text 'high_logits' in this list.
    ("low_logits", "high_logits"),
    # Include a tuple containing the text 'low_probability', the text 'high_probability' in this list.
    ("low_probability", "high_probability"),
])
# Check reward is neutral to actions logits and predictions using the setup, calls, and assertions below.
# Input labels: the supplied labels.
# Output: no explicit value; normal completion returns None.
def test_reward_is_neutral_to_actions_logits_and_predictions(labels):
    # Set realized_cost to 3.0.
    realized_cost = 3.0
    # Require the result of raw_team_reward(realized_cost) equals the result of raw_team_reward(realized_cost);
    # otherwise raise AssertionError.
    assert raw_team_reward(realized_cost) == raw_team_reward(realized_cost)
    # Require labels at 0 differs from labels at 1; otherwise raise AssertionError.
    assert labels[0] != labels[1]


# Check fairness and throughput diagnostics are separate exact statistics using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_fairness_and_throughput_diagnostics_are_separate_exact_statistics():
    # Set records to the result of demand((('AV_0', 0.0, 0.0, 2.0), ('AV_1', 0.0, 0.0, 4.0), ('AV_2', 0.0, 0.0,
    # None))).get_all_records().
    records = demand((
        # Include a tuple containing the text 'AV_0', 0.0, 0.0, 2.0 in this tuple.
        ("AV_0", 0.0, 0.0, 2.0),
        # Include a tuple containing the text 'AV_1', 0.0, 0.0, 4.0 in this tuple.
        ("AV_1", 0.0, 0.0, 4.0),
        # Include a tuple containing the text 'AV_2', 0.0, 0.0, None in this tuple.
        ("AV_2", 0.0, 0.0, None),
    )).get_all_records()
    # Set diagnostics to the result of compute_objective_diagnostics(the result of
    # measure_vehicle_travel_times(records, 6.0)).
    diagnostics = compute_objective_diagnostics(measure_vehicle_travel_times(records, 6.0))
    # Require diagnostics.vehicles_measured equals 3; otherwise raise AssertionError.
    assert diagnostics.vehicles_measured == 3
    # Require diagnostics.completed_services equals 2; otherwise raise AssertionError.
    assert diagnostics.completed_services == 2
    # Require diagnostics.mean_travel_time_seconds equals 4.0; otherwise raise AssertionError.
    assert diagnostics.mean_travel_time_seconds == 4.0
    # Require diagnostics.maximum_travel_time_seconds equals 6.0; otherwise raise AssertionError.
    assert diagnostics.maximum_travel_time_seconds == 6.0
    # Require diagnostics.travel_time_variance_seconds_squared equals 8.0 divided by 3.0; otherwise raise
    # AssertionError.
    assert diagnostics.travel_time_variance_seconds_squared == 8.0 / 3.0


# Check vehicle order and rename invariance using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_vehicle_order_and_rename_invariance():
    # Set first to the result of demand((('A', 0.0, 0.0, 2.0), ('B', 1.0, 1.0, 4.0))).get_all_records().
    first = demand((("A", 0.0, 0.0, 2.0), ("B", 1.0, 1.0, 4.0))).get_all_records()
    # Set second to the result of demand((('Y', 1.0, 1.0, 4.0), ('X', 0.0, 0.0, 2.0))).get_all_records().
    second = demand((("Y", 1.0, 1.0, 4.0), ("X", 0.0, 0.0, 2.0))).get_all_records()
    # Require the result of total_team_travel_time_seconds(the result of measure_vehicle_travel_times(first, 5.0))
    # equals the result of total_team_travel_time_seconds(the result of measure_vehicle_travel_times(second,
    # 5.0)); otherwise raise AssertionError.
    assert total_team_travel_time_seconds(measure_vehicle_travel_times(first, 5.0)) == total_team_travel_time_seconds(measure_vehicle_travel_times(second, 5.0))


# Check objective does not mutate regulatory protocol or masks using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_objective_does_not_mutate_regulatory_protocol_or_masks():
    # Set evidence to a dictionary containing graph, mask, protocol.
    evidence = {"graph": (("A", "B"),), "mask": (True, False), "protocol": "PENDING"}
    # Set before to a dictionary built from evidence.
    before = dict(evidence)
    # Call raw_team_reward with the supplied arguments.
    raw_team_reward(2.0)
    # Require evidence equals before; otherwise raise AssertionError.
    assert evidence == before


# Check step5h sources exclude route truth control and arbitrary constants using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_step5h_sources_exclude_route_truth_control_and_arbitrary_constants():
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('negotiation_objective').glob(the text '*.py') as part of the
                       # enclosing expression.
                       for path in Path("negotiation_objective").glob("*.py"))
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text
    # 'ground_truth_route_id', the text 'traci', the text...
    forbidden = (
        "route_id", "route_index", "ground_truth_route_id", "traci",
        "setspeed", "changelane", "collision_penalty", "agreement_bonus",
        "throughput_bonus", "fairness_weight", "waiting_speed_threshold",
        "reward_clip", "reward_normalization", "gamma =", "gae_lambda",
        "ppo_clip", "learning_rate", "optimizer",
    )
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
