"""Focused evaluator contracts, never a change to operational acceptance."""
import inspect
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from config import DEADLOCK_DURATION_SECONDS
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, classify
from post_training_evaluation.scenarios import schedule_payload, source_identities
from targeted_validation.cases import CASES_V1 as CASES, BY_ID, frozen_cases
from targeted_validation import models, runner
from targeted_validation.metrics import PanelTelemetry, STOP_PREFIX
from targeted_validation.reporting import build_payload, report

def test_exact_six_cases_six_episodes_and_budgets():
    assert [c.case_id for c in CASES] == [f"PV-{i:02d}" for i in range(1, 7)]
    assert sum(len(c.methods) for c in CASES) == 6
    assert sum(c.budget_seconds * len(c.methods) for c in CASES) == 570
    assert BY_ID["PV-02"].methods == ("PROPOSED_MAPPO", "RULES_ONLY")
    assert [c.scenario_id for c in CASES[:-1]] == ["rule_resolved_two", "regulatory_cycle", "multiple_left_turns", "congested_four_approach", "four_way_simultaneous"]

def test_dense_exact_predeclared_schedule_not_random_easier_substitute():
    from runtime_simulation.scenarios import get_scenario
    schedule = BY_ID["PV-04"].schedule()
    assert schedule == get_scenario("congested_four_approach").schedule()
    assert {a: len(rows) for a, rows in schedule.items()} == dict.fromkeys("NESW", 4)
    assert len({r.movement_path_id for rows in schedule.values() for r in rows}) == 12
    assert [r.scheduled_departure_seconds for r in schedule["N"]] == [0, 1.5, 3, 4.5]
    assert BY_ID["PV-04"].scenario().continuous

def test_panel_freeze_tamper_and_source_change_rejected(tmp_path):
    frozen = models.prepare(tmp_path)
    assert models.prepare(tmp_path) == frozen
    assert frozen["manifest"]["policy_sha256"] == EXPECTED_POLICY_HASH == file_hash(POLICY)
    value = json.loads((tmp_path / "manifest.json").read_text())
    value["manifest"]["cases"][3]["vehicle_count"] = 4
    (tmp_path / "manifest.json").write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match="CHECKSUM"):
        models.prepare(tmp_path)

def telemetry():
    return PanelTelemetry(BY_ID["PV-01"].schedule(), budget_seconds=60, expected_panel_sources=models.panel_sources())

def fake_world():
    t = telemetry()
    ids = tuple(t.waits)
    states = {v: dict(lane_id="in", lane_position=1., position=(0., 0.), speed=0., comfortable_deceleration_mps2=4.5) for v in ids}
    paths = SimpleNamespace(paths={p: SimpleNamespace(incoming_lane_id="in") for p in t.movements.values()})
    zones = SimpleNamespace(zone_record=lambda *args: None)
    api = SimpleNamespace(simulation=SimpleNamespace(getStartingTeleportIDList=lambda: (), getCollisions=lambda: ()))
    life = SimpleNamespace(departed_vehicle_ids=ids, arrived_vehicle_ids=())
    return t, ids, states, paths, zones, api, life

def step(t, ids, states, paths, zones, api, life, now):
    t.frame_decisions = {v: ("SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE") for v in ids}
    t.observe(now, states, life, t.movements, paths, zones, api)

def test_deadlock_uses_existing_threshold_and_requires_stationary_all_held():
    t, ids, states, paths, zones, api, life = fake_world()
    step(t, ids, states, paths, zones, api, life, .04)
    life.departed_vehicle_ids = ()
    step(t, ids, states, paths, zones, api, life, DEADLOCK_DURATION_SECONDS)
    assert t.termination_reason is None
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "DEADLOCK_CONFIRMED"):
        step(t, ids, states, paths, zones, api, life, DEADLOCK_DURATION_SECONDS + .08)
    runtime, error = t.finalize_runtime({"metrics": {}}, STOP_PREFIX + "DEADLOCK_CONFIRMED")
    assert error is None
    m = t.result(runtime)
    assert m["deadlock_observed"] and not m["timeout"]
    assert classify(m, {"valid": True}) == "SAFE_DEGRADATION"

@pytest.mark.parametrize("change", ("future_demand", "clearing", "moving", "position_progress", "permission"))
def test_no_premature_deadlock_stop(change):
    t, ids, states, paths, zones, api, life = fake_world()
    step(t, ids, states, paths, zones, api, life, .04)
    life.departed_vehicle_ids = ()
    if change == "future_demand":
        del t.departures[ids[0]]
    if change == "clearing":
        states[ids[0]]["lane_id"] = "out"
    if change == "moving":
        states[ids[0]]["speed"] = 1.
    if change == "position_progress":
        states[ids[0]]["lane_position"] = 2.
    t.frame_decisions = {v: ("SAFE_HOLD", "MISSING", "HELD_BEFORE_ZONE") for v in ids}
    if change == "permission":
        t.frame_decisions[ids[0]] = ("PERMITTED", "VALID_ADMISSION_LOCK", "COMMITTED_TO_ENTER")
    t.observe(30., states, life, t.movements, paths, zones, api)
    assert t.termination_reason is None

@pytest.mark.parametrize("reason", ("ALL_COMPLETED", "UNSAFE_FAILURE", "DEADLOCK_CONFIRMED"))
def test_only_exact_evaluator_stop_is_handled(reason):
    t = telemetry()
    t.termination_reason = reason
    assert t.finalize_runtime({}, STOP_PREFIX + reason)[1] is None
    assert t.finalize_runtime({}, "actual runtime failure")[1] == "actual runtime failure"

def test_hard_budget_unsafe_classification_and_no_event_rate_na():
    t = telemetry()
    t.finalize_runtime({"metrics": {}}, None)
    assert t.termination_reason == "HARD_TIME_BUDGET"
    assert t.result({})["fallback_rate"] is None
    t.finalize_runtime({"metrics": {"blocked_zone_violations": 1}}, "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    m = t.result({"metrics": {"blocked_zone_violations": 1}}, aborted=True)
    assert t.termination_reason == "UNSAFE_FAILURE" and classify(m, {"valid": True}, "error") == "UNSAFE_FAILURE"

def test_observed_collision_stops_without_manufacturing_physical_collision():
    t, ids, states, paths, zones, api, life = fake_world()
    api.simulation.getCollisions = lambda: (SimpleNamespace(collider="A", victim="B", type="mock_evidence"),)
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "UNSAFE_FAILURE"):
        step(t, ids, states, paths, zones, api, life, .04)
    assert t.collisions == 1 and t.termination_reason == "UNSAFE_FAILURE"
    assert classify(t.result({}), {"valid": True}) == "UNSAFE_FAILURE"

def test_completed_ledger_immediately_stops_with_true_reason():
    t, ids, states, paths, zones, api, life = fake_world()
    step(t, ids, states, paths, zones, api, life, .04)
    life.departed_vehicle_ids = ()
    life.arrived_vehicle_ids = ids
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "ALL_COMPLETED"):
        step(t, ids, {}, paths, zones, api, life, .08)
    assert classify(t.result({}), {"valid": True}) == "PASS"

def test_result_checksum_corruption_is_rejected(tmp_path):
    from post_training_evaluation.models import write_json
    frozen = models.prepare(tmp_path)
    directory = tmp_path / "runs" / "record"
    record = dict(suite="panel", classification="SAFE_DEGRADATION")
    write_json(directory / "result.json", record)
    write_json(directory / "result.sha256.json", dict(result_hash="tampered"))
    with pytest.raises(RuntimeError, match="RESULT_CHECKSUM"):
        models.records(tmp_path)

def test_runtime_guard_real_bundle_blocks_training_critic_global_and_preserves_e5():
    from post_training_evaluation.integrity import IntegrityGuard
    from negotiation_training.final_selection import _load_bundle
    from negotiation_execution import ConflictZoneExecutionPlanner
    _, bundle = _load_bundle(POLICY)
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        module.eval()
    guard = IntegrityGuard()
    guard.bind(bundle)
    try:
        for operation in (lambda: torch.tensor(1., requires_grad=True).backward(),
                          lambda: bundle.proposer_actor.train(),
                          lambda: bundle.centralized_critic.forward(None),
                          lambda: ConflictZoneExecutionPlanner.plan(None, None),
                          lambda: torch.optim.Adam(bundle.gnn.parameters()).step()):
            with pytest.raises(RuntimeError, match="INTEGRITY_BREACH"):
                operation()
    finally:
        result = guard.finish(dict(decentralized_execution=True, centralized_execution_graph_used_for_control=False,
            metrics=dict(maximum_negotiation_participants=4)))
    assert not result["valid"] and result["policy_hash_unchanged"] and result["parameter_updates"] == 0

@pytest.mark.parametrize("participants", (4, 5))
def test_guard_enforces_queue_head_limit(participants):
    from post_training_evaluation.integrity import IntegrityGuard
    from negotiation_training.final_selection import _load_bundle
    _, bundle = _load_bundle(POLICY)
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        module.eval()
    guard = IntegrityGuard()
    guard.bind(bundle)
    result = guard.finish(dict(decentralized_execution=True, centralized_execution_graph_used_for_control=False,
        metrics=dict(maximum_negotiation_participants=participants)))
    assert result["valid"] == (participants <= 4)
    assert result["centralized_critic_runtime_calls"] == result["optimizer_steps"] == result["training_operations"] == 0

def test_reports_preserve_failure_classes_and_traceability(tmp_path):
    frozen = models.prepare(tmp_path)
    runs = [dict(scenario_id=BY_ID[cid].scenario_id, method="PROPOSED_MAPPO", classification=status,
        metrics={}, integrity={}, run_id=cid) for cid, status in (("PV-01", "PASS"), ("PV-04", "SAFE_DEGRADATION"), ("PV-05", "UNSAFE_FAILURE"))]
    payload = build_payload(frozen, runs)
    assert {e["classification"] for e in payload["cases"]} == {"NOT_RUN", "PASS", "SAFE_DEGRADATION", "UNSAFE_FAILURE"}
    assert len(payload["limitations"]) == 2
    assert payload["traceability"][2]["evidence_cases"] == ("PV-04A", "PV-04B")
    assert payload["traceability"][2]["status"] == "IMPLEMENTED; MEASUREMENT_PENDING"
    assert not payload["complete"]
    report(tmp_path)
    html = (tmp_path / "latest/TARGETED_VALIDATION_REPORT.html").read_text()
    assert "NOT_RUN" in html and "N/A" in html and "PANEL FEEDBACK TRACEABILITY" in html

def test_fault_checks_current_infrastructure_pass(tmp_path):
    saved = runner.faults(tmp_path, models.prepare(tmp_path))
    assert saved["classification"] == "PASS"
    assert {t["fault"] for t in saved["tests"]} >= {"missing_required_coordination", "stale_coordination"}
    assert all(t["permission"] == "SAFE_HOLD" for t in saved["tests"])

def test_wrapper_reuses_runtime_and_paired_exact_demand(monkeypatch, tmp_path):
    captured = []
    monkeypatch.setattr(runner, "run_episode", lambda *args, **kw: captured.append((args, kw)))
    frozen = models.prepare(tmp_path)
    for method in BY_ID["PV-02"].methods:
        runner.execute(BY_ID["PV-02"], method, frozen, tmp_path)
    assert captured[0][1]["schedule"] == captured[1][1]["schedule"]
    assert runner.run_episode is not None
    assert "setSpeed" not in inspect.getsource(runner)

def test_exact_replay_restores_schedule_method_seed_and_budget(monkeypatch, tmp_path):
    frozen = models.prepare(tmp_path)
    case = BY_ID["PV-04"]
    rid = "20261008T010101000000Z_abcdef01"
    action_seed = int(digest((frozen["manifest"]["protocol_id"], case.scenario_id, None, "PROPOSED_MAPPO"))[:16], 16) % (2**31)
    prior = dict(run_id=rid, scenario_id=case.scenario_id, method="PROPOSED_MAPPO", suite="panel", policy_action_seed=action_seed)
    directory = tmp_path / "runs" / rid
    directory.mkdir(parents=True)
    (directory / "provenance.json").write_text(json.dumps(dict(schedule=schedule_payload(case.schedule()), policy_action_seed=action_seed)))
    monkeypatch.setattr(runner, "records", lambda root, suite="panel": [prior] if suite == "panel" else [])
    calls = []
    monkeypatch.setattr(runner, "execute", lambda *args, **kw: calls.append((args, kw)))
    runner.replay("PV-04", tmp_path, run_id=rid, gui=True)
    assert calls[0][0][0].budget_seconds == 180
    assert calls[0][1]["schedule"] == case.schedule()
    assert calls[0][1]["replay_of"] == rid and calls[0][1]["gui"]
