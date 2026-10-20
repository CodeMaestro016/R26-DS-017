"""Frozen protocol, semantic baseline, measurement and provenance contracts."""
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import METHODS, SEEDS, classify, digest, file_hash, POLICY, EXPECTED_POLICY_HASH from
# post_training_evaluation.models for the operations below.
from post_training_evaluation.models import METHODS, SEEDS, classify, digest, file_hash, POLICY, EXPECTED_POLICY_HASH
# Import SCENARIOS, CONTINUOUS, FUNCTIONAL, demand, schedule_payload, restore_schedule, manifest, prepare from
# post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import (SCENARIOS, CONTINUOUS, FUNCTIONAL, demand,
    schedule_payload, restore_schedule, manifest, prepare)
# Import fcfs_action, FCFSProvider, RulesOnlyProvider from post_training_evaluation.baselines for the operations
# below.
from post_training_evaluation.baselines import fcfs_action, FCFSProvider, RulesOnlyProvider
# Import statistics, inversion_rate, Telemetry from post_training_evaluation.metrics for the operations below.
from post_training_evaluation.metrics import statistics, inversion_rate, Telemetry
# Import summary, aggregate, load_runs from post_training_evaluation.aggregation for the operations below.
from post_training_evaluation.aggregation import summary, aggregate, load_runs
# Import evaluate_faults from post_training_evaluation.faults for the operations below.
from post_training_evaluation.faults import evaluate_faults
# Import IntegrityGuard from post_training_evaluation.integrity for the operations below.
from post_training_evaluation.integrity import IntegrityGuard
# Import replay from post_training_evaluation.replay for the operations below.
from post_training_evaluation.replay import replay
# Import _load_bundle from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import _load_bundle
# Import PanelDeterministicInferenceProvider from runtime_simulation.inference for the operations below.
from runtime_simulation.inference import PanelDeterministicInferenceProvider
# Import validate_presentation_schedule from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import validate_presentation_schedule
# Import STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
from config import STOPPED_SPEED_THRESHOLD_MPS

# Check frozen scope and matrix using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_frozen_scope_and_matrix():
    # Set value to the result of manifest().
    value = manifest()
    # Require the result of file_hash(POLICY) equals EXPECTED_POLICY_HASH; otherwise raise AssertionError.
    assert file_hash(POLICY) == EXPECTED_POLICY_HASH
    # Require the number of entries in FUNCTIONAL equals 5 and the number of entries in CONTINUOUS equals 5;
    # otherwise raise AssertionError.
    assert len(FUNCTIONAL) == 5 and len(CONTINUOUS) == 5
    # Require a list of a tuple containing x.vehicle_count, x.headway_seconds, x.budget_seconds for x in
    # CONTINUOUS equals a list containing a tuple containing 8, 2.0, 240.0, a tuple containing 12, 1.75, 300.0, a
    # tuple containing 16, 1.5, 360.0, a...; otherwise raise AssertionError.
    assert [(x.vehicle_count, x.headway_seconds, x.budget_seconds) for x in CONTINUOUS] == [
        # Include a tuple containing 12, 1.75, 300.0 in this list.
        (8, 2., 240.), (12, 1.75, 300.), (16, 1.5, 360.), (24, 1., 480.), (32, .75, 600.)]
    # Import V1_DIAGNOSTIC_SEEDS from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import V1_DIAGNOSTIC_SEEDS
    # Require SEEDS equals a tuple containing 1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003;
    # otherwise raise AssertionError.
    assert SEEDS == (1103,2207,3301,4409,5501,6607,7703,8807,9901,11003)
    # Require the negation of a set built from SEEDS intersected with a set built from V1_DIAGNOSTIC_SEEDS;
    # otherwise raise AssertionError.
    assert not set(SEEDS) & set(V1_DIAGNOSTIC_SEEDS)
    # Require value['sumo_options'] at 'time_to_teleport' equals the negative of 1; otherwise raise
    # AssertionError.
    assert value["sumo_options"]["time_to_teleport"] == -1
    # Require value at 'waiting_speed_threshold_mps' equals STOPPED_SPEED_THRESHOLD_MPS; otherwise raise
    # AssertionError.
    assert value["waiting_speed_threshold_mps"] == STOPPED_SPEED_THRESHOLD_MPS
    # Require the text 'real deployment' belongs to value at 'out_of_scope'; otherwise raise AssertionError.
    assert "real deployment" in value["out_of_scope"]
    # Require 3 multiplied by the number of entries in FUNCTIONAL plus len(CONTINUOUS) multiplied by len(SEEDS)
    # equals 165; otherwise raise AssertionError.
    assert 3 * (len(FUNCTIONAL) + len(CONTINUOUS) * len(SEEDS)) == 165

# Apply pytest.mark.parametrize('scenario', CONTINUOUS) as a decorator to configure the following definition.
@pytest.mark.parametrize("scenario", CONTINUOUS)
# Check seeded balanced legal demand and paired methods using the setup, calls, and assertions below.
# Input scenario: the supplied scenario.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_seeded_balanced_legal_demand_and_paired_methods(scenario):
    # Set schedules to a list of the result of demand(scenario, 101) for _ in METHODS.
    schedules = [demand(scenario, 101) for _ in METHODS]
    # Set hashes to a set of the result of digest(the result of schedule_payload(x)) for x in schedules.
    hashes = {digest(schedule_payload(x)) for x in schedules}
    # Require the number of entries in hashes equals 1; otherwise raise AssertionError.
    assert len(hashes) == 1
    # Require the result of digest(the result of schedule_payload(the result of demand(scenario, 101))) differs
    # from the result of digest(the result of schedule_payload(the result of demand(scenario, 202))); otherwise
    # raise AssertionError.
    assert digest(schedule_payload(demand(scenario, 101))) != digest(schedule_payload(demand(scenario, 202)))
    # Set schedule to the result of validate_presentation_schedule(schedules at 0).
    schedule = validate_presentation_schedule(schedules[0], allow_repeated_movements=True)
    # Require a set built from schedule equals a set built from the text 'NESW'; otherwise raise AssertionError.
    assert set(schedule) == set("NESW")
    # Require the sum of the result of map(len, values from schedule) equals scenario.vehicle_count; otherwise
    # raise AssertionError.
    assert sum(map(len, schedule.values())) == scenario.vehicle_count
    # Iterate over key/value pairs from schedule, binding each item to (a, rows).
    for a, rows in schedule.items():
        # Set counts to a list of the sum of a lazy sequence of the result of x.movement_path_id.endswith(m) for x
        # in rows for m in a tuple containing the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT'.
        counts = [sum(x.movement_path_id.endswith(m) for x in rows) for m in ("LEFT", "RIGHT", "STRAIGHT")]
        # Require the maximum of counts minus the minimum of counts is at most 1; otherwise raise AssertionError.
        assert max(counts) - min(counts) <= 1
        # Require whether every item is true in a lazy sequence of x.scheduled_departure_seconds equals i
        # multiplied by scenario.headway_seconds for (i, x) in index/value pairs from rows; otherwise raise
        # AssertionError.
        assert all(x.scheduled_departure_seconds == i * scenario.headway_seconds for i, x in enumerate(rows))
    # Require the result of restore_schedule(the result of schedule_payload(schedule)) equals schedule; otherwise
    # raise AssertionError.
    assert restore_schedule(schedule_payload(schedule)) == schedule

# Check manifest is exclusive and rejects tampering using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_manifest_is_exclusive_and_rejects_tampering(tmp_path):
    # Set original to the result of prepare(tmp_path).
    original = prepare(tmp_path)
    # Require the result of prepare(tmp_path) equals original; otherwise raise AssertionError.
    assert prepare(tmp_path) == original
    # Set payload to the decoded data produced by json.loads from the text read from (tmp_path / 'manifest.json').
    payload = json.loads((tmp_path / "manifest.json").read_text())
    # Set payload['manifest']['seeds'] to a list containing 1.
    payload["manifest"]["seeds"] = [1]
    # Write the supplied text to (tmp_path / 'manifest.json').
    (tmp_path / "manifest.json").write_text(json.dumps(payload))
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="MANIFEST_MISMATCH"):
        # Call prepare with the supplied arguments.
        prepare(tmp_path)

# Check fcfs relinquishes only authorized priority claim and honors masks using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_fcfs_relinquishes_only_authorized_priority_claim_and_honors_masks():
    # Require the result of fcfs_action(the text 'PROPOSER', a tuple containing the text 'early', the text 'late',
    # a dictionary...) equals 1; otherwise raise AssertionError.
    assert fcfs_action("PROPOSER", ("early", "late"), {"early":1.,"late":2.}, (True,True)) == 1
    # Require the result of fcfs_action(the text 'PROPOSER', a tuple containing the text 'early', the text 'late',
    # a dictionary...) equals 0; otherwise raise AssertionError.
    assert fcfs_action("PROPOSER", ("early", "late"), {"early":1.,"late":2.}, (True,False)) == 0
    # Require the result of fcfs_action(the text 'PROPOSER', a tuple containing the text 'late', the text 'early',
    # a dictionary...) equals 0; otherwise raise AssertionError.
    assert fcfs_action("PROPOSER", ("late", "early"), {"early":1.,"late":2.}, (True,True)) == 0
    # Require the result of fcfs_action(the text 'RESPONDER', a tuple containing the text 'early', the text
    # 'late', an empty dictionary,...) equals 0; otherwise raise AssertionError.
    assert fcfs_action("RESPONDER", ("early","late"), {}, (True,True)) == 0
    # Require the result of fcfs_action(the text 'PROPOSER', a tuple containing the text 'a', the text 'b', a
    # dictionary containing a,...) equals 1; otherwise raise AssertionError.
    assert fcfs_action("PROPOSER", ("a","b"), {"a":1.,"b":1.}, (True,True)) == 1

# Check rules only never invents an outcome using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_rules_only_never_invents_an_outcome():
    # Require the result of RulesOnlyProvider.select_joint_actions(None) is the same object as None; otherwise
    # raise AssertionError.
    assert RulesOnlyProvider.select_joint_actions(None, negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE") is None

# Check p95 empty and aborted values using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_p95_empty_and_aborted_values():
    # Require statistics([0.0, 10.0, 20.0]) at 'p95' equals the result of pytest.approx(19.0); otherwise raise
    # AssertionError.
    assert statistics([0.,10.,20.])["p95"] == pytest.approx(19.)
    # Require statistics([]) at 'mean' is the same object as None; otherwise raise AssertionError.
    assert statistics([])["mean"] is None
    # Set telemetry to the result of Telemetry(the result of demand(FUNCTIONAL at 0, None)).
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    # Set result to the result of telemetry.result(a dictionary containing actual_simulation_time_seconds).
    result = telemetry.result({"actual_simulation_time_seconds":10.}, aborted=True)
    # Require result at 'total_team_travel_time_seconds' is the same object as None; otherwise raise
    # AssertionError.
    assert result["total_team_travel_time_seconds"] is None
    # Require result at 'mean_travel_time_seconds' is the same object as None; otherwise raise AssertionError.
    assert result["mean_travel_time_seconds"] is None
    # Require result at 'completion_rate' equals 0.0; otherwise raise AssertionError.
    assert result["completion_rate"] == 0.
    # Require result['per_approach_mean_waiting_time_seconds'] at 'N' is the same object as None; otherwise raise
    # AssertionError.
    assert result["per_approach_mean_waiting_time_seconds"]["N"] is None

# Check exposure uses scheduled clock and censors unfinished using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exposure_uses_scheduled_clock_and_censors_unfinished():
    # Set telemetry to the result of Telemetry(the result of demand(FUNCTIONAL at 0, None)).
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    # Call telemetry.ledger.record_actual_departure with the supplied arguments.
    telemetry.ledger.record_actual_departure("PANEL_AV_N_01", 2.)
    # Set telemetry.departures['PANEL_AV_N_01'] to 2.0.
    telemetry.departures["PANEL_AV_N_01"] = 2.
    # Call telemetry.ledger.record_service_completion with the supplied arguments.
    telemetry.ledger.record_service_completion("PANEL_AV_N_01", 8.)
    # Set telemetry.completions['PANEL_AV_N_01'] to 8.0.
    telemetry.completions["PANEL_AV_N_01"] = 8.
    # Set result to the result of telemetry.result(a dictionary containing actual_simulation_time_seconds).
    result = telemetry.result({"actual_simulation_time_seconds":10.})
    # Require result at 'total_team_travel_time_seconds' equals 18.0; otherwise raise AssertionError.
    assert result["total_team_travel_time_seconds"] == 18. # 8 completed + 10 censored
    # Require result at 'mean_travel_time_seconds' equals 8.0; otherwise raise AssertionError.
    assert result["mean_travel_time_seconds"] == 8. # includes two-second insertion delay
    # Require result at 'traffic_exposure_censored' and result at 'completion_rate' equals 0.5; otherwise raise
    # AssertionError.
    assert result["traffic_exposure_censored"] and result["completion_rate"] == .5

# Check conflicting only inversions ties and unserved pairs using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_conflicting_only_inversions_ties_and_unserved_pairs():
    # Set arrivals to a dictionary containing a, b, c.
    arrivals = {"a":1., "b":2., "c":1.}
    # Set service to a dictionary containing a, b, c.
    service = {"a":4., "b":3., "c":4.}
    # Require the result of inversion_rate(arrivals, service, a list containing a tuple containing 'a', 'b')
    # equals a tuple containing 1.0, 1, 1; otherwise raise AssertionError.
    assert inversion_rate(arrivals, service, [("a","b")]) == (1.,1,1)
    # Require the result of inversion_rate(arrivals, service, a list containing a tuple containing 'a', 'c')
    # equals a tuple containing 0.0, 0, 1; otherwise raise AssertionError.
    assert inversion_rate(arrivals, service, [("a","c")]) == (0.,0,1)
    # Require the result of inversion_rate(arrivals, a dictionary containing a, a list containing a tuple
    # containing 'a', 'b') equals a tuple containing None, 0, 0; otherwise raise AssertionError.
    assert inversion_rate(arrivals, {"a":4.}, [("a","b")]) == (None,0,0)

# Apply pytest.mark.parametrize('metric, integrity, error, expected', [({'unfinished_vehicles': 0},... as a
# decorator to configure the following definition.
@pytest.mark.parametrize("metric, integrity, error, expected", [
    # Store 0 under 'unfinished_vehicles'.
    # Store True under 'valid'.
    ({"unfinished_vehicles":0}, {"valid":True}, None, "PASS"),
    # Store 1 under 'unfinished_vehicles'.
    # Store True under 'valid'.
    ({"unfinished_vehicles":1}, {"valid":True}, None, "SAFE_DEGRADATION"),
    # Store 1 under 'collision_count'.
    # Store True under 'valid'.
    ({"collision_count":1}, {"valid":True}, "collision", "UNSAFE_FAILURE"),
    # Store 1 under 'blocked_zone_violation_count'.
    # Store True under 'valid'.
    ({"blocked_zone_violation_count":1}, {"valid":True}, "zone", "UNSAFE_FAILURE"),
    # Store False under 'valid'.
    ({}, {"valid":False}, None, "INVALID_EXPERIMENT"),
    # Store a floating-point number built from the text 'nan' under 'mean'.
    # Store True under 'valid'.
    ({"mean":float("nan")}, {"valid":True}, None, "INVALID_EXPERIMENT"),
    # Store True under 'valid'.
    ({}, {"valid":True}, "unexplained abort", "INVALID_EXPERIMENT")])
# Check classification using the setup, calls, and assertions below.
# Input metric: the supplied metric.
# Input integrity: the supplied integrity.
# Input error: the supplied error.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_classification(metric, integrity, error, expected):
    # Require the result of classify(metric, integrity, error) equals expected; otherwise raise AssertionError.
    assert classify(metric, integrity, error) == expected

# Check inference timing threshold and no calls na using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_inference_timing_threshold_and_no_calls_na():
    # Set telemetry to the result of Telemetry(the result of demand(FUNCTIONAL at 0, None)).
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    # Call telemetry.inference with the supplied arguments.
    telemetry.inference(20_000_000)
    # Call telemetry.inference with the supplied arguments.
    telemetry.inference(60_000_000)
    # Call telemetry.execution with the supplied arguments.
    telemetry.execution(1_000_000, None)
    # Set result to the result of telemetry.result(a dictionary containing actual_simulation_time_seconds).
    result = telemetry.result({"actual_simulation_time_seconds":10.})
    # Require result at 'mappo_inference_mean_ms' equals 40.0; otherwise raise AssertionError.
    assert result["mappo_inference_mean_ms"] == 40.
    # Require result at 'mappo_inference_fraction_exceeding_40ms' equals 0.5; otherwise raise AssertionError.
    assert result["mappo_inference_fraction_exceeding_40ms"] == .5
    # Set baseline to the result of Telemetry(the result of demand(FUNCTIONAL at 0, None)).
    baseline = Telemetry(demand(FUNCTIONAL[0], None), proposed=False)
    # Call baseline.inference with the supplied arguments.
    baseline.inference(60_000_000)
    # Require baseline.result({'actual_simulation_time_seconds': 10.0}) at 'mappo_inference_mean_ms' is the same
    # object as None; otherwise raise AssertionError.
    assert baseline.result({"actual_simulation_time_seconds":10.})["mappo_inference_mean_ms"] is None

# Check all controlled faults hold and reject entry using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_all_controlled_faults_hold_and_reject_entry():
    # Set results to the result of evaluate_faults().
    results = evaluate_faults()
    # Require the number of entries in results equals 4 and whether every item is true in a lazy sequence of r at
    # 'passed' for r in results; otherwise raise AssertionError.
    assert len(results) == 4 and all(r["passed"] for r in results)

# Check statistics reproducible with n1 na and missing values using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_statistics_reproducible_with_n1_na_and_missing_values():
    # Require the result of summary(a list containing 1.0, 2.0, 3.0) equals the result of summary(a list
    # containing 1.0, 2.0, 3.0); otherwise raise AssertionError.
    assert summary([1.,2.,3.]) == summary([1.,2.,3.])
    # Require summary([1.0]) at 'ci95' is the same object as None; otherwise raise AssertionError.
    assert summary([1.])["ci95"] is None
    # Require summary([None]) at 'n' equals 0; otherwise raise AssertionError.
    assert summary([None])["n"] == 0
    # Require summary([1.0, 2.0, 3.0]) at 'standard_deviation' equals 1.0; otherwise raise AssertionError.
    assert summary([1.,2.,3.])["standard_deviation"] == 1.

# Check integrity guards all runtime operations and tensor updates using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then handle the specified errors.
def test_integrity_guards_all_runtime_operations_and_tensor_updates():
    # Set (_, bundle) to the result of _load_bundle(POLICY).
    _, bundle = _load_bundle(POLICY)
    # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding each item
    # to module.
    for module in (bundle.gnn,bundle.proposer_actor,bundle.responder_actor):
        # Call module.eval with the supplied arguments.
        module.eval()
    # Set optimizer to the result of torch.optim.Adam(the result of bundle.proposer_actor.parameters()).
    optimizer = torch.optim.Adam(bundle.proposer_actor.parameters())
    # Set guard to the result of IntegrityGuard().
    guard = IntegrityGuard()
    # Call guard.bind with the supplied arguments.
    guard.bind(bundle)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
        with pytest.raises(RuntimeError, match="backward_calls"):
            # Backpropagate gradients from torch.tensor(1.0, requires_grad=True).
            torch.tensor(1.,requires_grad=True).backward()
        # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
        with pytest.raises(RuntimeError, match="optimizer_steps"):
            # Advance optimizer using its configured step operation.
            optimizer.step()
        # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
        with pytest.raises(RuntimeError, match="training_operations"):
            # Call bundle.proposer_actor.train with the supplied arguments.
            bundle.proposer_actor.train()
        # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
        with pytest.raises(RuntimeError, match="centralized_critic_runtime_calls"):
            # Call bundle.centralized_critic with the supplied arguments.
            bundle.centralized_critic(torch.zeros(1))
        # Call next(bundle.proposer_actor.parameters()).add_ with the supplied arguments.
        next(bundle.proposer_actor.parameters()).add_(1.)
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Set result to the result of guard.finish(a dictionary containing decentralized_execution,
        # centralized_execution_graph_used_for_control,...).
        result = guard.finish({"decentralized_execution":True,
            # Store False under 'centralized_execution_graph_used_for_control'.
            "centralized_execution_graph_used_for_control":False,
            # Store a dictionary containing maximum_negotiation_participants under 'metrics'.
            # Store 4 under 'maximum_negotiation_participants'.
            "metrics":{"maximum_negotiation_participants":4}})
    # Require the negation of result at 'valid' and result at 'parameter_updates' equals 1; otherwise raise
    # AssertionError.
    assert not result["valid"] and result["parameter_updates"] == 1
    # Require result at 'policy_hash_unchanged'; otherwise raise AssertionError.
    assert result["policy_hash_unchanged"]

# Check replay rejects path traversal without touching sumo using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_replay_rejects_path_traversal_without_touching_sumo():
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="RUN_ID"):
        # Call replay with the supplied arguments.
        replay("../selected_policy.pt")

# Check same shared runtime is used by quantitative wrapper using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_same_shared_runtime_is_used_by_quantitative_wrapper():
    # Import inspect for use in this module.
    import inspect
    # Import runner from post_training_evaluation for the operations below.
    from post_training_evaluation import runner
    # Import runner as panel from runtime_simulation for the operations below.
    from runtime_simulation import runner as panel
    # Require runner.run_runtime_simulation is the same object as panel.run_runtime_simulation; otherwise raise
    # AssertionError.
    assert runner.run_runtime_simulation is panel.run_runtime_simulation
    # Set source to the result of inspect.getsource(runner).
    source = inspect.getsource(runner)
    # Require the text 'persist_presentation=False' belongs to source; otherwise raise AssertionError.
    assert "persist_presentation=False" in source
    # Require the text 'DecentralizedEgoExecutionController(' does not belong to source; otherwise raise
    # AssertionError.
    assert "DecentralizedEgoExecutionController(" not in source

# Check waiting approach gap and emergency evidence only incoming period using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_waiting_approach_gap_and_emergency_evidence_only_incoming_period():
    # Set schedule to the result of demand(CONTINUOUS at 0, 101).
    schedule = demand(CONTINUOUS[0], 101)
    # Set t to the result of Telemetry(schedule).
    t = Telemetry(schedule)
    # Import MapPathManager, ConflictZoneManager from conflict for the operations below.
    from conflict import MapPathManager, ConflictZoneManager
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set ids to a list of formatted text built from the embedded values for a in the text 'NESW'.
    ids = [f"PANEL_AV_{a}_01" for a in "NESW"]
    # Set states to a dictionary of v mapped to a dictionary containing lane_id, speed, accel,
    # comfortable_deceleration_mps2 for v in ids.
    states = {v:{"lane_id":paths.paths[t.movements[v]].incoming_lane_id,
        # Store 0.0 when the result of v.endswith(the text 'N_01'), otherwise 1.0 under 'speed'.
        "speed":0. if v.endswith("N_01") else 1.,
        # Store the negative of 7.0 under 'accel'.
        # Store 4.5 under 'comfortable_deceleration_mps2'.
        "accel":-7., "comfortable_deceleration_mps2":4.5} for v in ids}
    # Set api to the result of SimpleNamespace().
    api = SimpleNamespace(simulation=SimpleNamespace(getCollisions=lambda:(),
        # Supply getStartingTeleportIDList as a callback that returns an empty tuple.
        getStartingTeleportIDList=lambda:()))
    # Set life to the result of SimpleNamespace().
    life = SimpleNamespace(departed_vehicle_ids=ids,arrived_vehicle_ids=())
    # Call t.observe with the supplied arguments.
    t.observe(.04,states,life,t.movements,paths,zones,api)
    # Set states[ids[0]]['lane_id'] to paths.paths[t.movements[ids[0]]].internal_lane_ids at 0.
    states[ids[0]]["lane_id"] = paths.paths[t.movements[ids[0]]].internal_lane_ids[0]
    # Set life.departed_vehicle_ids to an empty tuple.
    life.departed_vehicle_ids = ()
    # Call t.observe with the supplied arguments.
    t.observe(.08,states,life,t.movements,paths,zones,api)
    # Set result to the result of t.result(a dictionary containing actual_simulation_time_seconds).
    result = t.result({"actual_simulation_time_seconds":.08})
    # Require result at 'maximum_waiting_time_seconds' equals 0.04; otherwise raise AssertionError.
    assert result["maximum_waiting_time_seconds"] == .04
    # Require result at 'approach_waiting_time_gap_seconds' equals 0.04; otherwise raise AssertionError.
    assert result["approach_waiting_time_gap_seconds"] == .04
    # Require result at 'native_emergency_braking_events' equals 4; otherwise raise AssertionError.
    assert result["native_emergency_braking_events"] == 4 # contiguous, no double count
    # Require result['vehicle_measurements'][ids[0]] at 'service_seconds' equals 0.08; otherwise raise
    # AssertionError.
    assert result["vehicle_measurements"][ids[0]]["service_seconds"] == .08

# Check report does not fabricate missing metrics and creates six plots using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_report_does_not_fabricate_missing_metrics_and_creates_six_plots(tmp_path):
    # Import report from post_training_evaluation.reporting for the operations below.
    from post_training_evaluation.reporting import report
    # Import write_json from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import write_json
    # Set frozen to the result of prepare(tmp_path).
    frozen = prepare(tmp_path)
    # Set telemetry to the result of Telemetry(the result of demand(CONTINUOUS at 0, 101)).
    telemetry = Telemetry(demand(CONTINUOUS[0],101))
    # Set m to the result of telemetry.result(a dictionary containing actual_simulation_time_seconds).
    m = telemetry.result({"actual_simulation_time_seconds":5.},aborted=True)
    # Set record to a dictionary containing run_id, suite, method, scenario_id, seed, manifest_hash,
    # schedule_hash,...
    record = {"run_id":"test", "suite":"smoke", "method":"PROPOSED_MAPPO", "scenario_id":"normal", "seed":101,
        # Store frozen at 'manifest_hash' under 'manifest_hash'.
        # Store the result of digest(the result of schedule_payload(the result of demand(CONTINUOUS at 0, 101)))
        # under 'schedule_hash'.
        "manifest_hash":frozen["manifest_hash"],"schedule_hash":digest(schedule_payload(demand(CONTINUOUS[0],101))),
        # Store the text 'INVALID_EXPERIMENT' under 'classification'.
        # Store the text 'abort' under 'error'.
        # Store m under 'metrics'.
        "classification":"INVALID_EXPERIMENT","error":"abort", "metrics":m,
        # Store a dictionary containing valid, policy_hash_unchanged, decentralized_execution,
        # centralized_critic_runtime_calls under 'integrity'.
        # Store False under 'valid'.
        # Store True under 'policy_hash_unchanged'.
        # Store True under 'decentralized_execution'.
        "integrity":{"valid":False,"policy_hash_unchanged":True,"decentralized_execution":True,
        # Store the text 'python run_post_training_evaluation.py --replay test --gui' under 'replay_command'.
        # Store 0 under 'centralized_critic_runtime_calls'.
        "centralized_critic_runtime_calls":0},"replay_command":"python run_post_training_evaluation.py --replay test --gui"}
    # Set directory to tmp_path joined with the path segment 'runs/test'.
    directory = tmp_path / "runs/test"
    # Call write_json with the supplied arguments.
    write_json(directory / "result.json",record)
    # Call write_json with the supplied arguments.
    write_json(directory / "result.sha256.json", {"result_hash":digest(record)})
    # Set provenance to a dictionary containing schedule_hash, schedule.
    provenance = {"schedule_hash":record["schedule_hash"],"schedule":schedule_payload(demand(CONTINUOUS[0],101))}
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.json", provenance)
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.sha256.json", {"provenance_hash":digest(provenance)})
    # Set result to the result of report(tmp_path, the text 'smoke').
    result = report(tmp_path,"smoke")
    # Require the negation of result at 'complete_final_matrix'; otherwise raise AssertionError.
    assert not result["complete_final_matrix"]
    # Require the number of entries in a list built from the result of (tmp_path / 'latest/plots').glob('*.png')
    # equals 6; otherwise raise AssertionError.
    assert len(list((tmp_path / "latest/plots").glob("*.png"))) == 6
    # Set text to the text read from (tmp_path / 'latest/POST_TRAINING_EVALUATION_REPORT.html').
    text = (tmp_path / "latest/POST_TRAINING_EVALUATION_REPORT.html").read_text()
    # Require the text 'SMOKE_NOT_FINAL' belongs to text and the text 'N/A' belongs to text and the text 'abort'
    # belongs to text; otherwise raise AssertionError.
    assert "SMOKE_NOT_FINAL" in text and "N/A" in text and "abort" in text
    # Require whether (tmp_path / 'latest/PAPER_TABLES.md') is an existing file; otherwise raise AssertionError.
    assert (tmp_path / "latest/PAPER_TABLES.md").is_file()

# Check paired aggregation rejects different demands using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_paired_aggregation_rejects_different_demands():
    # Set frozen to a dictionary containing manifest_hash, manifest.
    frozen={"manifest_hash":"hash","manifest":{"scope":"test","out_of_scope":[]}}
    # Set base to a dictionary containing suite, scenario_id, seed, classification, metrics, method,
    # schedule_hash.
    base={"suite":"final","scenario_id":"normal","seed":101,"classification":"PASS",
        # Store an empty dictionary under 'metrics'.
        # Store the text 'PROPOSED_MAPPO' under 'method'.
        # Store the text 'a' under 'schedule_hash'.
        "metrics":{},"method":"PROPOSED_MAPPO","schedule_hash":"a"}
    # Set other to a dictionary containing method, schedule_hash.
    other={**base,"method":"RULE_PLUS_FCFS","schedule_hash":"b"}
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match="PAIRED_DEMAND"):
        # Call aggregate with the supplied arguments.
        aggregate([base,other], frozen,"final")

# Check smoke has separate fixed budget and same paired demand using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_smoke_has_separate_fixed_budget_and_same_paired_demand(monkeypatch, tmp_path):
    # Import runner, aggregation, reporting, faults from post_training_evaluation for the operations below.
    from post_training_evaluation import runner, aggregation, reporting, faults
    # Import SMOKE_BUDGET_SECONDS from post_training_evaluation.scenarios for the operations below.
    from post_training_evaluation.scenarios import SMOKE_BUDGET_SECONDS
    # Set calls to an empty list.
    calls = []
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner, "prepare", lambda root:{"manifest_hash":"smoke"})
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(aggregation, "load_runs", lambda *args:[])
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner, "run_episode", lambda s, seed, method, frozen, **kw:
        # Evaluate the result of calls.append(a tuple containing s, seed, method, the result of digest(the result
        # of...) as part of the enclosing expression.
        calls.append((s, seed, method, digest(schedule_payload(kw["schedule"])))))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(faults, "evaluate_faults", lambda:[])
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(reporting, "report", lambda *args, **kw:None)
    # Write the supplied text to (tmp_path / 'manifest.json').
    (tmp_path / "manifest.json").write_text("{}")
    # Call runner.run_suite with the supplied arguments.
    runner.run_suite("smoke", tmp_path)
    # Require the number of entries in calls equals 9 and whether every item is true in a lazy sequence of
    # s.budget_seconds equals SMOKE_BUDGET_SECONDS; equals 90.0 for (s, *_) in calls; otherwise raise
    # AssertionError.
    assert len(calls) == 9 and all(s.budget_seconds == SMOKE_BUDGET_SECONDS == 90. for s, *_ in calls)
    # Iterate over a tuple containing 0, 3, 6, binding each item to index.
    for index in (0,3,6):
        # Require the number of entries in a set of x at 3 for x in calls sliced by index:index + 3 equals 1;
        # otherwise raise AssertionError.
        assert len({x[3] for x in calls[index:index+3]}) == 1
    # Require a list of s.budget_seconds for s in CONTINUOUS equals a list containing 240.0, 300.0, 360.0, 480.0,
    # 600.0; otherwise raise AssertionError.
    assert [s.budget_seconds for s in CONTINUOUS] == [240.,300.,360.,480.,600.]

# Check replay preserves saved method budget and schedule using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_replay_preserves_saved_method_budget_and_schedule(monkeypatch, tmp_path):
    # Import importlib for use in this module.
    import importlib
    # Set module to the result of importlib.import_module(the text 'post_training_evaluation.replay').
    module = importlib.import_module("post_training_evaluation.replay")
    # Import write_json from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import write_json
    # Set frozen to a dictionary containing manifest_hash.
    frozen = {"manifest_hash":"same"}
    # Set run_id to the text '20261006T010101000000Z_abcdef01'.
    run_id = "20261006T010101000000Z_abcdef01"
    # Set saved to a dictionary containing manifest_hash, schedule, scenario, method, seed.
    saved = {"manifest_hash":"same", "schedule":schedule_payload(demand(CONTINUOUS[2],101)),
        # Store CONTINUOUS[2].__dict__ under 'scenario'.
        # Store the text 'RULES_ONLY' under 'method'.
        # Store 101 under 'seed'.
        "scenario":CONTINUOUS[2].__dict__, "method":"RULES_ONLY", "seed":101}
    # Set saved['schedule_hash'] to the result of digest(saved at 'schedule').
    saved["schedule_hash"] = digest(saved["schedule"])
    # Set directory to tmp_path joined with the path segment 'runs' divided by run_id.
    directory = tmp_path / "runs" / run_id
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.json",saved)
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.sha256.json",{"provenance_hash":digest(saved)})
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(module,"prepare",lambda root:frozen)
    # Set captured to an empty dictionary.
    captured = {}
    # Execute using the inputs and processing steps below.
    # Input scenario: the supplied scenario.
    # Input seed: the random seed supplied to this operation.
    # Input method: the supplied method.
    # Input manifest: the supplied manifest.
    # Input kwargs: the supplied kwargs.
    # Output: no explicit value; normal completion returns None.
    def execute(scenario,seed,method,manifest,**kwargs):
        # Update captured with the supplied entries.
        captured.update(scenario=scenario,seed=seed,method=method,kwargs=kwargs)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(module,"run_episode",execute)
    # Call module.replay with the supplied arguments.
    module.replay(run_id,root=tmp_path,gui=True)
    # Require captured at 'method' equals the text 'RULES_ONLY' and captured at 'seed' equals 101; otherwise raise
    # AssertionError.
    assert captured["method"] == "RULES_ONLY" and captured["seed"] == 101
    # Require captured['scenario'].budget_seconds equals 360.0; otherwise raise AssertionError.
    assert captured["scenario"].budget_seconds == 360.
    # Require the result of digest(the result of schedule_payload(captured['kwargs'] at 'schedule')) equals saved
    # at 'schedule_hash'; otherwise raise AssertionError.
    assert digest(schedule_payload(captured["kwargs"]["schedule"])) == saved["schedule_hash"]
    # Require captured['kwargs'] at 'replay_of' equals run_id and captured['kwargs'] at 'gui'; otherwise raise
    # AssertionError.
    assert captured["kwargs"]["replay_of"] == run_id and captured["kwargs"]["gui"]

# Check nonfinite metrics are invalid and archived as na using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_nonfinite_metrics_are_invalid_and_archived_as_na():
    # Import normalize_nonfinite, canonical from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import normalize_nonfinite, canonical
    # Set metrics to a dictionary containing travel, timing.
    metrics = {"travel":float("inf"), "timing":[float("nan"),1.]}
    # Require the result of classify(metrics, a dictionary containing valid) equals the text 'INVALID_EXPERIMENT';
    # otherwise raise AssertionError.
    assert classify(metrics,{"valid":True}) == "INVALID_EXPERIMENT"
    # Set normalized to the result of normalize_nonfinite(metrics).
    normalized = normalize_nonfinite(metrics)
    # Require normalized equals a dictionary containing travel, timing; otherwise raise AssertionError.
    assert normalized == {"travel":None,"timing":[None,1.]}
    # Require the text 'null' belongs to the result of canonical(normalized); otherwise raise AssertionError.
    assert "null" in canonical(normalized)
