"""Frozen protocol, semantic baseline, measurement and provenance contracts."""
from dataclasses import replace
from types import SimpleNamespace
import json
from pathlib import Path
import pytest
import torch

from final_evaluation.models import METHODS, SEEDS, classify, digest, file_hash, POLICY, EXPECTED_POLICY_HASH
from final_evaluation.scenarios import (SCENARIOS, CONTINUOUS, FUNCTIONAL, demand,
    schedule_payload, restore_schedule, manifest, prepare)
from final_evaluation.baselines import fcfs_action, FCFSProvider, RulesOnlyProvider
from final_evaluation.metrics import statistics, inversion_rate, Telemetry
from final_evaluation.aggregation import summary, aggregate, load_runs
from final_evaluation.faults import evaluate_faults
from final_evaluation.integrity import IntegrityGuard
from final_evaluation.replay import replay
from negotiation_training.final_selection import _load_bundle
from panel_demo.inference import PanelDeterministicInferenceProvider
from panel_demo.schedule import validate_presentation_schedule
from config import STOPPED_SPEED_THRESHOLD_MPS

def test_frozen_scope_and_matrix():
    value = manifest()
    assert file_hash(POLICY) == EXPECTED_POLICY_HASH
    assert len(FUNCTIONAL) == 5 and len(CONTINUOUS) == 5
    assert [(x.vehicle_count, x.headway_seconds, x.budget_seconds) for x in CONTINUOUS] == [
        (8, 2., 240.), (12, 1.75, 300.), (16, 1.5, 360.), (24, 1., 480.), (32, .75, 600.)]
    assert SEEDS == (101,202,303,404,505,606,707,808,909,1010)
    assert value["sumo_options"]["time_to_teleport"] == -1
    assert value["waiting_speed_threshold_mps"] == STOPPED_SPEED_THRESHOLD_MPS
    assert "real deployment" in value["out_of_scope"]
    assert 3 * (len(FUNCTIONAL) + len(CONTINUOUS) * len(SEEDS)) == 165

@pytest.mark.parametrize("scenario", CONTINUOUS)
def test_seeded_balanced_legal_demand_and_paired_methods(scenario):
    schedules = [demand(scenario, 101) for _ in METHODS]
    hashes = {digest(schedule_payload(x)) for x in schedules}
    assert len(hashes) == 1
    assert digest(schedule_payload(demand(scenario, 101))) != digest(schedule_payload(demand(scenario, 202)))
    schedule = validate_presentation_schedule(schedules[0], allow_repeated_movements=True)
    assert set(schedule) == set("NESW")
    assert sum(map(len, schedule.values())) == scenario.vehicle_count
    for a, rows in schedule.items():
        counts = [sum(x.movement_path_id.endswith(m) for x in rows) for m in ("LEFT", "RIGHT", "STRAIGHT")]
        assert max(counts) - min(counts) <= 1
        assert all(x.scheduled_departure_seconds == i * scenario.headway_seconds for i, x in enumerate(rows))
    assert restore_schedule(schedule_payload(schedule)) == schedule

def test_manifest_is_exclusive_and_rejects_tampering(tmp_path):
    original = prepare(tmp_path)
    assert prepare(tmp_path) == original
    payload = json.loads((tmp_path / "manifest.json").read_text())
    payload["manifest"]["seeds"] = [1]
    (tmp_path / "manifest.json").write_text(json.dumps(payload))
    with pytest.raises(RuntimeError, match="MANIFEST_MISMATCH"):
        prepare(tmp_path)

def test_fcfs_relinquishes_only_authorized_priority_claim_and_honors_masks():
    assert fcfs_action("PROPOSER", ("early", "late"), {"early":1.,"late":2.}, (True,True)) == 1
    assert fcfs_action("PROPOSER", ("early", "late"), {"early":1.,"late":2.}, (True,False)) == 0
    assert fcfs_action("PROPOSER", ("late", "early"), {"early":1.,"late":2.}, (True,True)) == 0
    assert fcfs_action("RESPONDER", ("early","late"), {}, (True,True)) == 0
    assert fcfs_action("PROPOSER", ("a","b"), {"a":1.,"b":1.}, (True,True)) == 1

def test_rules_only_never_invents_an_outcome():
    assert RulesOnlyProvider.select_joint_actions(None, negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE") is None

def test_p95_empty_and_aborted_values():
    assert statistics([0.,10.,20.])["p95"] == pytest.approx(19.)
    assert statistics([])["mean"] is None
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    result = telemetry.result({"actual_simulation_time_seconds":10.}, aborted=True)
    assert result["total_team_travel_time_seconds"] is None
    assert result["mean_travel_time_seconds"] is None
    assert result["completion_rate"] == 0.
    assert result["per_approach_mean_waiting_time_seconds"]["N"] is None

def test_exposure_uses_scheduled_clock_and_censors_unfinished():
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    telemetry.ledger.record_actual_departure("PANEL_AV_N_01", 2.)
    telemetry.departures["PANEL_AV_N_01"] = 2.
    telemetry.ledger.record_service_completion("PANEL_AV_N_01", 8.)
    telemetry.completions["PANEL_AV_N_01"] = 8.
    result = telemetry.result({"actual_simulation_time_seconds":10.})
    assert result["total_team_travel_time_seconds"] == 18. # 8 completed + 10 censored
    assert result["mean_travel_time_seconds"] == 8. # includes two-second insertion delay
    assert result["traffic_exposure_censored"] and result["completion_rate"] == .5

def test_conflicting_only_inversions_ties_and_unserved_pairs():
    arrivals = {"a":1., "b":2., "c":1.}
    service = {"a":4., "b":3., "c":4.}
    assert inversion_rate(arrivals, service, [("a","b")]) == (1.,1,1)
    assert inversion_rate(arrivals, service, [("a","c")]) == (0.,0,1)
    assert inversion_rate(arrivals, {"a":4.}, [("a","b")]) == (None,0,0)

@pytest.mark.parametrize("metric, integrity, error, expected", [
    ({"unfinished_vehicles":0}, {"valid":True}, None, "PASS"),
    ({"unfinished_vehicles":1}, {"valid":True}, None, "SAFE_DEGRADATION"),
    ({"collision_count":1}, {"valid":True}, "collision", "UNSAFE_FAILURE"),
    ({"blocked_zone_violation_count":1}, {"valid":True}, "zone", "UNSAFE_FAILURE"),
    ({}, {"valid":False}, None, "INVALID_EXPERIMENT"),
    ({"mean":float("nan")}, {"valid":True}, None, "INVALID_EXPERIMENT"),
    ({}, {"valid":True}, "unexplained abort", "INVALID_EXPERIMENT")])
def test_classification(metric, integrity, error, expected):
    assert classify(metric, integrity, error) == expected

def test_inference_timing_threshold_and_no_calls_na():
    telemetry = Telemetry(demand(FUNCTIONAL[0], None))
    telemetry.inference(20_000_000)
    telemetry.inference(60_000_000)
    telemetry.execution(1_000_000, None)
    result = telemetry.result({"actual_simulation_time_seconds":10.})
    assert result["mappo_inference_mean_ms"] == 40.
    assert result["mappo_inference_fraction_exceeding_40ms"] == .5
    baseline = Telemetry(demand(FUNCTIONAL[0], None), proposed=False)
    baseline.inference(60_000_000)
    assert baseline.result({"actual_simulation_time_seconds":10.})["mappo_inference_mean_ms"] is None

def test_all_controlled_faults_hold_and_reject_entry():
    results = evaluate_faults()
    assert len(results) == 4 and all(r["passed"] for r in results)

def test_statistics_reproducible_with_n1_na_and_missing_values():
    assert summary([1.,2.,3.]) == summary([1.,2.,3.])
    assert summary([1.])["ci95"] is None
    assert summary([None])["n"] == 0
    assert summary([1.,2.,3.])["standard_deviation"] == 1.

def test_integrity_guards_all_runtime_operations_and_tensor_updates():
    _, bundle = _load_bundle(POLICY)
    for module in (bundle.gnn,bundle.proposer_actor,bundle.responder_actor):
        module.eval()
    optimizer = torch.optim.Adam(bundle.proposer_actor.parameters())
    guard = IntegrityGuard()
    guard.bind(bundle)
    try:
        with pytest.raises(RuntimeError, match="backward_calls"):
            torch.tensor(1.,requires_grad=True).backward()
        with pytest.raises(RuntimeError, match="optimizer_steps"):
            optimizer.step()
        with pytest.raises(RuntimeError, match="training_operations"):
            bundle.proposer_actor.train()
        with pytest.raises(RuntimeError, match="centralized_critic_runtime_calls"):
            bundle.centralized_critic(torch.zeros(1))
        next(bundle.proposer_actor.parameters()).add_(1.)
    finally:
        result = guard.finish({"decentralized_execution":True,
            "centralized_execution_graph_used_for_control":False,
            "metrics":{"maximum_negotiation_participants":4}})
    assert not result["valid"] and result["parameter_updates"] == 1
    assert result["policy_hash_unchanged"]

def test_replay_rejects_path_traversal_without_touching_sumo():
    with pytest.raises(ValueError, match="RUN_ID"):
        replay("../selected_policy.pt")

def test_same_shared_runtime_is_used_by_quantitative_wrapper():
    import inspect
    from final_evaluation import runner
    from panel_demo import runner as panel
    assert runner.run_panel_demo is panel.run_panel_demo
    source = inspect.getsource(runner)
    assert "persist_presentation=False" in source
    assert "DecentralizedEgoExecutionController(" not in source

def test_waiting_approach_gap_and_emergency_evidence_only_incoming_period():
    schedule = demand(CONTINUOUS[0], 101)
    t = Telemetry(schedule)
    from conflict import MapPathManager, ConflictZoneManager
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    ids = [f"PANEL_AV_{a}_01" for a in "NESW"]
    states = {v:{"lane_id":paths.paths[t.movements[v]].incoming_lane_id,
        "speed":0. if v.endswith("N_01") else 1.,
        "accel":-7., "comfortable_deceleration_mps2":4.5} for v in ids}
    api = SimpleNamespace(simulation=SimpleNamespace(getCollisions=lambda:(),
        getStartingTeleportIDList=lambda:()))
    life = SimpleNamespace(departed_vehicle_ids=ids,arrived_vehicle_ids=())
    t.observe(.04,states,life,t.movements,paths,zones,api)
    states[ids[0]]["lane_id"] = paths.paths[t.movements[ids[0]]].internal_lane_ids[0]
    life.departed_vehicle_ids = ()
    t.observe(.08,states,life,t.movements,paths,zones,api)
    result = t.result({"actual_simulation_time_seconds":.08})
    assert result["maximum_waiting_time_seconds"] == .04
    assert result["approach_waiting_time_gap_seconds"] == .04
    assert result["native_emergency_braking_events"] == 4 # contiguous, no double count
    assert result["vehicle_measurements"][ids[0]]["service_seconds"] == .08

def test_report_does_not_fabricate_missing_metrics_and_creates_six_plots(tmp_path):
    from final_evaluation.reporting import report
    from final_evaluation.models import write_json
    frozen = prepare(tmp_path)
    telemetry = Telemetry(demand(CONTINUOUS[0],101))
    m = telemetry.result({"actual_simulation_time_seconds":5.},aborted=True)
    record = {"run_id":"test", "suite":"smoke", "method":"PROPOSED_MAPPO", "scenario_id":"normal", "seed":101,
        "manifest_hash":frozen["manifest_hash"],"schedule_hash":digest(schedule_payload(demand(CONTINUOUS[0],101))),
        "classification":"INVALID_EXPERIMENT","error":"abort", "metrics":m,
        "integrity":{"valid":False,"policy_hash_unchanged":True,"decentralized_execution":True,
        "centralized_critic_runtime_calls":0},"replay_command":"python run_final_evaluation.py --replay test --gui"}
    directory = tmp_path / "runs/test"
    write_json(directory / "result.json",record)
    write_json(directory / "result.sha256.json", {"result_hash":digest(record)})
    provenance = {"schedule_hash":record["schedule_hash"],"schedule":schedule_payload(demand(CONTINUOUS[0],101))}
    write_json(directory / "provenance.json", provenance)
    write_json(directory / "provenance.sha256.json", {"provenance_hash":digest(provenance)})
    result = report(tmp_path,"smoke")
    assert not result["complete_final_matrix"]
    assert len(list((tmp_path / "latest/plots").glob("*.png"))) == 6
    text = (tmp_path / "latest/PANEL_EVALUATION_REPORT.html").read_text()
    assert "SMOKE_NOT_FINAL" in text and "N/A" in text and "abort" in text
    assert (tmp_path / "latest/PAPER_TABLES.md").is_file()

def test_paired_aggregation_rejects_different_demands():
    frozen={"manifest_hash":"hash","manifest":{"scope":"test","out_of_scope":[]}}
    base={"suite":"final","scenario_id":"normal","seed":101,"classification":"PASS",
        "metrics":{},"method":"PROPOSED_MAPPO","schedule_hash":"a"}
    other={**base,"method":"RULE_PLUS_FCFS","schedule_hash":"b"}
    with pytest.raises(RuntimeError,match="PAIRED_DEMAND"):
        aggregate([base,other], frozen,"final")

def test_smoke_has_separate_fixed_budget_and_same_paired_demand(monkeypatch, tmp_path):
    from final_evaluation import runner, aggregation, reporting, faults
    from final_evaluation.scenarios import SMOKE_BUDGET_SECONDS
    calls = []
    monkeypatch.setattr(runner, "prepare", lambda root:{"manifest_hash":"smoke"})
    monkeypatch.setattr(aggregation, "load_runs", lambda *args:[])
    monkeypatch.setattr(runner, "run_episode", lambda s, seed, method, frozen, **kw:
        calls.append((s, seed, method, digest(schedule_payload(kw["schedule"])))))
    monkeypatch.setattr(faults, "evaluate_faults", lambda:[])
    monkeypatch.setattr(reporting, "report", lambda *args, **kw:None)
    runner.run_suite("smoke", tmp_path)
    assert len(calls) == 9 and all(s.budget_seconds == SMOKE_BUDGET_SECONDS == 90. for s, *_ in calls)
    for index in (0,3,6):
        assert len({x[3] for x in calls[index:index+3]}) == 1
    assert [s.budget_seconds for s in CONTINUOUS] == [240.,300.,360.,480.,600.]

def test_replay_preserves_saved_method_budget_and_schedule(monkeypatch, tmp_path):
    import importlib
    module = importlib.import_module("final_evaluation.replay")
    from final_evaluation.models import write_json
    frozen = {"manifest_hash":"same"}
    run_id = "20261006T010101000000Z_abcdef01"
    saved = {"manifest_hash":"same", "schedule":schedule_payload(demand(CONTINUOUS[2],101)),
        "scenario":CONTINUOUS[2].__dict__, "method":"RULES_ONLY", "seed":101}
    saved["schedule_hash"] = digest(saved["schedule"])
    directory = tmp_path / "runs" / run_id
    write_json(directory / "provenance.json",saved)
    write_json(directory / "provenance.sha256.json",{"provenance_hash":digest(saved)})
    monkeypatch.setattr(module,"prepare",lambda root:frozen)
    captured = {}
    def execute(scenario,seed,method,manifest,**kwargs):
        captured.update(scenario=scenario,seed=seed,method=method,kwargs=kwargs)
    monkeypatch.setattr(module,"run_episode",execute)
    module.replay(run_id,root=tmp_path,gui=True)
    assert captured["method"] == "RULES_ONLY" and captured["seed"] == 101
    assert captured["scenario"].budget_seconds == 360.
    assert digest(schedule_payload(captured["kwargs"]["schedule"])) == saved["schedule_hash"]
    assert captured["kwargs"]["replay_of"] == run_id and captured["kwargs"]["gui"]

def test_nonfinite_metrics_are_invalid_and_archived_as_na():
    from final_evaluation.models import normalize_nonfinite, canonical
    metrics = {"travel":float("inf"), "timing":[float("nan"),1.]}
    assert classify(metrics,{"valid":True}) == "INVALID_EXPERIMENT"
    normalized = normalize_nonfinite(metrics)
    assert normalized == {"travel":None,"timing":[None,1.]}
    assert "null" in canonical(normalized)
