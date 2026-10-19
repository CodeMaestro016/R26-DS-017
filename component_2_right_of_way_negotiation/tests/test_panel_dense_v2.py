"""Frozen nominal/critical separation and preservation of known limitations."""
import ast
import inspect
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest
from runtime_simulation.schedule import validate_presentation_schedule
from runtime_simulation.scenarios import get_scenario
from runtime_simulation.queue_heads import select_queue_heads
from conflict import MapPathManager
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest
from post_training_evaluation.scenarios import schedule_payload
from targeted_validation.cases import CASES, BY_ID, nominal_schedule
from targeted_validation import models, runner, v1_replay
from targeted_validation.reporting import build_payload, report

def test_seven_case_design_and_seven_episodes():
    assert [c.case_id for c in CASES] == ["PV-01", "PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05", "PV-06"]
    assert sum(len(c.methods) for c in CASES) == 7
    assert sum(c.budget_seconds * len(c.methods) for c in CASES) == 750.

def test_nominal_exact_frozen_approved_schedule_all_legal():
    expected = {"N": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"), "E": ("LEFT", "RIGHT", "STRAIGHT", "LEFT"),
                "S": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"), "W": ("STRAIGHT", "LEFT", "RIGHT", "STRAIGHT")}
    schedule = nominal_schedule()
    assert schedule == nominal_schedule()
    assert validate_presentation_schedule(schedule, allow_repeated_movements=True) == schedule
    assert {a: len(rows) for a, rows in schedule.items()} == dict.fromkeys("NESW", 4)
    paths = MapPathManager()
    for a, rows in schedule.items():
        assert tuple(row.movement_path_id for row in rows) == tuple(f"{a}_IN_0_{m}" for m in expected[a])
        assert tuple(row.scheduled_departure_seconds for row in rows) == tuple((6. if a == "W" else 0.) + i*1.5 for i in range(4))
        assert all(row.movement_path_id in paths.paths for row in rows)
    assert len({r.movement_path_id for rows in schedule.values() for r in rows}) == 12
    assert BY_ID["PV-04A"].scenario().vehicle_count == 16

def test_critical_schedule_matches_original_v1_bytes():
    frozen = models.read_checked_manifest(models.V1_ROOT)
    original = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == "PV-04")
    assert schedule_payload(BY_ID["PV-04B"].schedule()) == original["schedule"]
    assert BY_ID["PV-04B"].schedule() == get_scenario("congested_four_approach").schedule()

def test_only_physical_heads_from_sixteen_vehicles():
    paths = MapPathManager()
    schedule = nominal_schedule()
    movements, states = {}, {}
    for a, rows in schedule.items():
        for row in rows:
            v = f"PANEL_AV_{a}_{row.sequence_index+1:02d}"
            movements[v] = row.movement_path_id
            states[v] = dict(lane_id=paths.paths[row.movement_path_id].incoming_lane_id,
                lane_position=250. - row.sequence_index*8.)
    assert len(states) == 16
    heads = select_queue_heads(states, paths, movements)
    assert len(heads) == 4 and set(heads) == {f"PANEL_AV_{a}_01" for a in "NESW"}
    states.pop("PANEL_AV_N_01")
    assert "PANEL_AV_N_02" in select_queue_heads(states, paths, movements)

def test_budget_method_schedule_changes_are_rejected_before_runtime(tmp_path):
    frozen = models.prepare(tmp_path)
    case = BY_ID["PV-04A"]
    with pytest.raises(RuntimeError, match="FROZEN_PANEL_CASE_MISMATCH"):
        runner.execute(replace(case, budget_seconds=181), "PROPOSED_MAPPO", frozen, tmp_path)
    changed = case.schedule()
    changed["N"] = (replace(changed["N"][0], scheduled_departure_seconds=5.),) + changed["N"][1:]
    with pytest.raises(RuntimeError, match="REPLAY_DEMAND_MISMATCH"):
        runner.execute(case, "PROPOSED_MAPPO", frozen, tmp_path, schedule=changed)

def test_v1_writes_refused_and_e5_unchanged():
    with pytest.raises(RuntimeError, match="V1_READ_ONLY"):
        models.prepare(models.V1_ROOT)
    assert file_hash(POLICY) == EXPECTED_POLICY_HASH

def test_preserved_evidence_and_operational_sources_match():
    archive = Path("results/panel_validation_archives/v1")
    base = Path.cwd()
    inventory = json.loads((archive / "evidence_inventory.json").read_text(encoding="utf-8-sig"))
    assert inventory and all(file_hash(base / name) == expected for name, expected in inventory.items())
    frozen = models.read_checked_manifest(models.V1_ROOT)
    operational = {n: h for n, h in frozen["manifest"]["source_identities"].items()
                   if n.split("/")[0] in {"panel_demo", "runtime_simulation", "negotiation_execution", "negotiation_learning", "traffic_rules", "conflict"}}
    from naming_compat import historical_path
    assert operational and all(file_hash(historical_path(base / name)) == expected for name, expected in operational.items())

@pytest.mark.parametrize("classification", ("PASS", "SAFE_DEGRADATION", "UNSAFE_FAILURE"))
def test_two_dense_cases_honest_results_and_no_fake_mappo(tmp_path, classification):
    frozen = models.prepare(tmp_path)
    critical = next(r for r in models.records(models.V1_ROOT) if r["scenario_id"] == "congested_four_approach")
    raw = digest(critical)
    nominal = dict(scenario_id=BY_ID["PV-04A"].scenario_id, method="PROPOSED_MAPPO", classification=classification,
        metrics=dict(mappo_inference_call_count=0), integrity={}, run_id="nominal")
    data = build_payload(frozen, [nominal, dict(critical, historical_v1=True)])
    a, b = data["dense"]
    assert a["case_id"] == "PV-04A" and a["classification"] == classification
    assert b["case_id"] == "PV-04B" and b["classification"] == "SAFE_DEGRADATION"
    assert b["metrics"] == critical["metrics"] and b["run"]["run_id"] == critical["run_id"]
    assert not a["demonstrates_learned_negotiation"] and "does not demonstrate" in a["negotiation_note"]
    assert digest(critical) == raw
    assert all(e["classification"] != "PASS" for e in data["limitations"])

def test_fallback_outcome_is_never_relabelled():
    original = next(r for r in models.records(models.V1_ROOT) if r["scenario_id"] == "multiple_left_turns")
    tags = [e["execution_outcome"] for e in original["runtime_events"]]
    assert tags[0] == "MAPPO_WITH_SAFETY_FALLBACK"
    assert original["metrics"]["fallback_activations"] >= 1
    # Later direct events remain direct; an episode may contain both categories.
    assert tags == ["MAPPO_WITH_SAFETY_FALLBACK", "MAPPO_DIRECT"]

def test_existing_liveness_assertions_retained_as_strict_known_failures():
    path = Path("tests/test_ego_execution_and_dense_traffic.py")
    tree = ast.parse(path.read_text())
    names = {"test_real_congested_run_has_safe_dense_traffic_and_complete_discharge",
             "test_live_state_exports_measured_counts_and_execution_flags"}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(functions) == 2
    for f in functions:
        xfail = next(d for d in f.decorator_list if isinstance(d, ast.Call) and ast.unparse(d.func) == "pytest.mark.xfail")
        assert any(k.arg == "strict" and k.value.value is True for k in xfail.keywords)
        assert any(k.arg == "raises" and ast.unparse(k.value) == "AssertionError" for k in xfail.keywords)
        assert any(isinstance(n, ast.Assert) for n in ast.walk(f))
    fixture = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "congested_run")
    source = ast.unparse(fixture)
    assert 'metrics["collisions"]' in source.replace("'", '"') and "COMMUNICATED_PRECEDENCE_DISAGREEMENT" in source
    assert "live[" in source and "policy_hash_unchanged" in source

def test_archived_replay_selects_original_runtime_without_writing_v1(monkeypatch):
    captured = []
    monkeypatch.setattr(v1_replay, "_launch", lambda command, **kwargs: captured.append(command))
    v1_replay.replay_v1("PV-04B", models.V1_ROOT, run_id="20261008T171632326120Z_c654aaee")
    assert "PV-04" in captured[0]
    assert any("replays" in item for item in captured[0])
    assert any("runtime" in item for item in captured[0])

def test_fixture_contract_breach_cannot_be_consumed_as_expected_liveness():
    from functools import wraps
    tree = ast.parse(Path("tests/test_ego_execution_and_dense_traffic.py").read_text())
    guard = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_fixture_errors_are_not_known_liveness_failures")
    namespace = {"wraps": wraps}
    exec(compile(ast.Module(body=[guard], type_ignores=[]), "fixture_guard", "exec"), namespace)
    def corrupt_safety():
        raise AssertionError("collision or changed policy")
    with pytest.raises(RuntimeError, match="DENSE_FIXTURE_CONTRACT_BREACH"):
        namespace[guard.name](corrupt_safety)()
    assert namespace[guard.name](lambda: "validated fixture")() == "validated fixture"
