"""Frozen nominal/critical separation and preservation of known limitations."""
# Import ast for use in this module.
import ast
# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import pytest for use in this module.
import pytest
# Import validate_presentation_schedule from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import validate_presentation_schedule
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import select_queue_heads from runtime_simulation.queue_heads for the operations below.
from runtime_simulation.queue_heads import select_queue_heads
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import POLICY, EXPECTED_POLICY_HASH, file_hash, digest from post_training_evaluation.models for the operations
# below.
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest
# Import schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import schedule_payload
# Import CASES, BY_ID, nominal_schedule from targeted_validation.cases for the operations below.
from targeted_validation.cases import CASES, BY_ID, nominal_schedule
# Import models, runner, v1_replay from targeted_validation for the operations below.
from targeted_validation import models, runner, v1_replay
# Import build_payload, report from targeted_validation.reporting for the operations below.
from targeted_validation.reporting import build_payload, report

# Check seven case design and seven episodes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_seven_case_design_and_seven_episodes():
    # Require a list of c.case_id for c in CASES equals a list containing the text 'PV-01', the text 'PV-02', the
    # text 'PV-03', the text 'PV-04A', the text 'PV-04B', the text...; otherwise raise AssertionError.
    assert [c.case_id for c in CASES] == ["PV-01", "PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05", "PV-06"]
    # Require the sum of a lazy sequence of the number of entries in c.methods for c in CASES equals 7; otherwise
    # raise AssertionError.
    assert sum(len(c.methods) for c in CASES) == 7
    # Require the sum of a lazy sequence of c.budget_seconds multiplied by len(c.methods) for c in CASES equals
    # 750.0; otherwise raise AssertionError.
    assert sum(c.budget_seconds * len(c.methods) for c in CASES) == 750.

# Check nominal exact frozen approved schedule all legal using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_nominal_exact_frozen_approved_schedule_all_legal():
    # Set expected to a dictionary containing N, E, S, W.
    expected = {"N": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"), "E": ("LEFT", "RIGHT", "STRAIGHT", "LEFT"),
                # Store a tuple containing the text 'LEFT', the text 'STRAIGHT', the text 'RIGHT', the text 'LEFT'
                # under 'S'.
                # Store a tuple containing the text 'STRAIGHT', the text 'LEFT', the text 'RIGHT', the text
                # 'STRAIGHT' under 'W'.
                "S": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"), "W": ("STRAIGHT", "LEFT", "RIGHT", "STRAIGHT")}
    # Set schedule to the result of nominal_schedule().
    schedule = nominal_schedule()
    # Require schedule equals the result of nominal_schedule(); otherwise raise AssertionError.
    assert schedule == nominal_schedule()
    # Require the result of validate_presentation_schedule(schedule) equals schedule; otherwise raise
    # AssertionError.
    assert validate_presentation_schedule(schedule, allow_repeated_movements=True) == schedule
    # Require a dictionary of a mapped to the number of entries in rows for (a, rows) in key/value pairs from
    # schedule equals the result of dict.fromkeys(the text 'NESW', 4); otherwise raise AssertionError.
    assert {a: len(rows) for a, rows in schedule.items()} == dict.fromkeys("NESW", 4)
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Iterate over key/value pairs from schedule, binding each item to (a, rows).
    for a, rows in schedule.items():
        # Require a tuple built from a lazy sequence of row.movement_path_id for row in rows equals a tuple built
        # from a lazy sequence of formatted text built from the embedded values for m in expected at a; otherwise
        # raise AssertionError.
        assert tuple(row.movement_path_id for row in rows) == tuple(f"{a}_IN_0_{m}" for m in expected[a])
        # Require a tuple built from a lazy sequence of row.scheduled_departure_seconds for row in rows equals a
        # tuple built from a lazy sequence of 6.0 if a == 'W' else 0.0 plus i * 1.5 for i in the integer range
        # defined by 4; otherwise raise AssertionError.
        assert tuple(row.scheduled_departure_seconds for row in rows) == tuple((6. if a == "W" else 0.) + i*1.5 for i in range(4))
        # Require whether every item is true in a lazy sequence of row.movement_path_id belongs to paths.paths for
        # row in rows; otherwise raise AssertionError.
        assert all(row.movement_path_id in paths.paths for row in rows)
    # Require the number of entries in a set of r.movement_path_id for rows in values from schedule equals 12;
    # otherwise raise AssertionError.
    assert len({r.movement_path_id for rows in schedule.values() for r in rows}) == 12
    # Require BY_ID['PV-04A'].scenario().vehicle_count equals 16; otherwise raise AssertionError.
    assert BY_ID["PV-04A"].scenario().vehicle_count == 16

# Check critical schedule matches original v1 bytes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_critical_schedule_matches_original_v1_bytes():
    # Set frozen to the result of models.read_checked_manifest(models.V1_ROOT).
    frozen = models.read_checked_manifest(models.V1_ROOT)
    # Set original to the next item from a lazy sequence of c for c in frozen['manifest'] at 'cases'; retain
    # entries satisfying c at 'case_id' equals the text 'PV-04'.
    original = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == "PV-04")
    # Require the result of schedule_payload(the result of BY_ID['PV-04B'].schedule()) equals original at
    # 'schedule'; otherwise raise AssertionError.
    assert schedule_payload(BY_ID["PV-04B"].schedule()) == original["schedule"]
    # Require the result of BY_ID['PV-04B'].schedule() equals the result of
    # get_scenario('congested_four_approach').schedule(); otherwise raise AssertionError.
    assert BY_ID["PV-04B"].schedule() == get_scenario("congested_four_approach").schedule()

# Check only physical heads from sixteen vehicles using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_only_physical_heads_from_sixteen_vehicles():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set schedule to the result of nominal_schedule().
    schedule = nominal_schedule()
    # Set (movements, states) to a tuple containing an empty dictionary, an empty dictionary.
    movements, states = {}, {}
    # Iterate over key/value pairs from schedule, binding each item to (a, rows).
    for a, rows in schedule.items():
        # Iterate over rows, binding each item to row.
        for row in rows:
            # Set v to formatted text built from the embedded values.
            v = f"PANEL_AV_{a}_{row.sequence_index+1:02d}"
            # Set movements[v] to row.movement_path_id.
            movements[v] = row.movement_path_id
            # Set states[v] to a dictionary built from the supplied values.
            states[v] = dict(lane_id=paths.paths[row.movement_path_id].incoming_lane_id,
                # Supply lane_position as 250.0 minus row.sequence_index multiplied by 8.0.
                lane_position=250. - row.sequence_index*8.)
    # Require the number of entries in states equals 16; otherwise raise AssertionError.
    assert len(states) == 16
    # Set heads to the result of select_queue_heads(states, paths, movements).
    heads = select_queue_heads(states, paths, movements)
    # Require the number of entries in heads equals 4 and a set built from heads equals a set of formatted text
    # built from the embedded values for a in the text 'NESW'; otherwise raise AssertionError.
    assert len(heads) == 4 and set(heads) == {f"PANEL_AV_{a}_01" for a in "NESW"}
    # Remove the requested entry from states.
    states.pop("PANEL_AV_N_01")
    # Require the text 'PANEL_AV_N_02' belongs to the result of select_queue_heads(states, paths, movements);
    # otherwise raise AssertionError.
    assert "PANEL_AV_N_02" in select_queue_heads(states, paths, movements)

# Check budget method schedule changes are rejected before runtime using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_budget_method_schedule_changes_are_rejected_before_runtime(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Set case to BY_ID at 'PV-04A'.
    case = BY_ID["PV-04A"]
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="FROZEN_PANEL_CASE_MISMATCH"):
        # Call runner.execute with the supplied arguments.
        runner.execute(replace(case, budget_seconds=181), "PROPOSED_MAPPO", frozen, tmp_path)
    # Set changed to the result of case.schedule().
    changed = case.schedule()
    # Set changed['N'] to a tuple containing the result of replace(changed['N'] at 0) plus changed['N'] sliced by
    # 1:.
    changed["N"] = (replace(changed["N"][0], scheduled_departure_seconds=5.),) + changed["N"][1:]
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="REPLAY_DEMAND_MISMATCH"):
        # Call runner.execute with the supplied arguments.
        runner.execute(case, "PROPOSED_MAPPO", frozen, tmp_path, schedule=changed)

# Check v1 writes refused and e5 unchanged using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_v1_writes_refused_and_e5_unchanged():
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="V1_READ_ONLY"):
        # Call models.prepare with the supplied arguments.
        models.prepare(models.V1_ROOT)
    # Require the result of file_hash(POLICY) equals EXPECTED_POLICY_HASH; otherwise raise AssertionError.
    assert file_hash(POLICY) == EXPECTED_POLICY_HASH

# Check preserved evidence and operational sources match using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_preserved_evidence_and_operational_sources_match():
    # Set archive to the result of Path(the text 'results/panel_validation_archives/v1').
    archive = Path("results/panel_validation_archives/v1")
    # Set base to the result of Path.cwd().
    base = Path.cwd()
    # Set inventory to the decoded data produced by json.loads from the text read from (archive /
    # 'evidence_inventory.json').
    inventory = json.loads((archive / "evidence_inventory.json").read_text(encoding="utf-8-sig"))
    # Require inventory and whether every item is true in a lazy sequence of file_hash(base / name) equals
    # expected for (name, expected) in key/value pairs from inventory; otherwise raise AssertionError.
    assert inventory and all(file_hash(base / name) == expected for name, expected in inventory.items())
    # Set frozen to the result of models.read_checked_manifest(models.V1_ROOT).
    frozen = models.read_checked_manifest(models.V1_ROOT)
    # Set operational to a dictionary of n mapped to h for (n, h) in key/value pairs from
    # frozen['manifest']['source_identities']; retain entries satisfying n.split('/') at 0 belongs to a set
    # containing the text 'panel_demo', the text...
    operational = {n: h for n, h in frozen["manifest"]["source_identities"].items()
                   # Evaluate n.split('/') at 0 belongs to a set containing the text 'panel_demo', the text
                   # 'runtime_simulation', the text 'negotiation_execution', the text... as part of the enclosing
                   # expression.
                   if n.split("/")[0] in {"panel_demo", "runtime_simulation", "negotiation_execution", "negotiation_learning", "traffic_rules", "conflict"}}
    # Import historical_path from naming_compat for the operations below.
    from naming_compat import historical_path
    # Require operational and whether every item is true in a lazy sequence of file_hash(historical_path(base /
    # name)) equals expected for (name, expected) in key/value pairs from operational; otherwise raise
    # AssertionError.
    assert operational and all(file_hash(historical_path(base / name)) == expected for name, expected in operational.items())

# Apply pytest.mark.parametrize('classification', ('PASS', 'SAFE_DEGRADATION', 'UNSAFE_FAILURE')) as a decorator
# to configure the following definition.
@pytest.mark.parametrize("classification", ("PASS", "SAFE_DEGRADATION", "UNSAFE_FAILURE"))
# Check two dense cases honest results and no fake mappo using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input classification: the supplied classification.
# Output: no explicit value; normal completion returns None.
def test_two_dense_cases_honest_results_and_no_fake_mappo(tmp_path, classification):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Set critical to the next item from a lazy sequence of r for r in the result of
    # models.records(models.V1_ROOT); retain entries satisfying r at 'scenario_id' equals the text
    # 'congested_four_approach'.
    critical = next(r for r in models.records(models.V1_ROOT) if r["scenario_id"] == "congested_four_approach")
    # Set raw to the result of digest(critical).
    raw = digest(critical)
    # Set nominal to a dictionary built from the supplied values.
    nominal = dict(scenario_id=BY_ID["PV-04A"].scenario_id, method="PROPOSED_MAPPO", classification=classification,
        # Supply metrics as a dictionary built from the supplied values.
        # Supply integrity as an empty dictionary.
        # Supply run_id as the text 'nominal'.
        # Supply mappo_inference_call_count as 0.
        metrics=dict(mappo_inference_call_count=0), integrity={}, run_id="nominal")
    # Set data to the result of build_payload(frozen, a list containing nominal, a dictionary built from
    # critical).
    data = build_payload(frozen, [nominal, dict(critical, historical_v1=True)])
    # Set (a, b) to data at 'dense'.
    a, b = data["dense"]
    # Require a at 'case_id' equals the text 'PV-04A' and a at 'classification' equals classification; otherwise
    # raise AssertionError.
    assert a["case_id"] == "PV-04A" and a["classification"] == classification
    # Require b at 'case_id' equals the text 'PV-04B' and b at 'classification' equals the text
    # 'SAFE_DEGRADATION'; otherwise raise AssertionError.
    assert b["case_id"] == "PV-04B" and b["classification"] == "SAFE_DEGRADATION"
    # Require b at 'metrics' equals critical at 'metrics' and b['run'] at 'run_id' equals critical at 'run_id';
    # otherwise raise AssertionError.
    assert b["metrics"] == critical["metrics"] and b["run"]["run_id"] == critical["run_id"]
    # Require the negation of a at 'demonstrates_learned_negotiation' and the text 'does not demonstrate' belongs
    # to a at 'negotiation_note'; otherwise raise AssertionError.
    assert not a["demonstrates_learned_negotiation"] and "does not demonstrate" in a["negotiation_note"]
    # Require the result of digest(critical) equals raw; otherwise raise AssertionError.
    assert digest(critical) == raw
    # Require whether every item is true in a lazy sequence of e at 'classification' differs from the text 'PASS'
    # for e in data at 'limitations'; otherwise raise AssertionError.
    assert all(e["classification"] != "PASS" for e in data["limitations"])

# Check fallback outcome is never relabelled using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_fallback_outcome_is_never_relabelled():
    # Set original to the next item from a lazy sequence of r for r in the result of
    # models.records(models.V1_ROOT); retain entries satisfying r at 'scenario_id' equals the text
    # 'multiple_left_turns'.
    original = next(r for r in models.records(models.V1_ROOT) if r["scenario_id"] == "multiple_left_turns")
    # Set tags to a list of e at 'execution_outcome' for e in original at 'runtime_events'.
    tags = [e["execution_outcome"] for e in original["runtime_events"]]
    # Require tags at 0 equals the text 'MAPPO_WITH_SAFETY_FALLBACK'; otherwise raise AssertionError.
    assert tags[0] == "MAPPO_WITH_SAFETY_FALLBACK"
    # Require original['metrics'] at 'fallback_activations' is at least 1; otherwise raise AssertionError.
    assert original["metrics"]["fallback_activations"] >= 1
    # Later direct events remain direct; an episode may contain both categories.
    # Require tags equals a list containing the text 'MAPPO_WITH_SAFETY_FALLBACK', the text 'MAPPO_DIRECT';
    # otherwise raise AssertionError.
    assert tags == ["MAPPO_WITH_SAFETY_FALLBACK", "MAPPO_DIRECT"]

# Check existing liveness assertions retained as strict known failures using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_existing_liveness_assertions_retained_as_strict_known_failures():
    # Set path to the result of Path(the text 'tests/test_ego_execution_and_dense_traffic.py').
    path = Path("tests/test_ego_execution_and_dense_traffic.py")
    # Set tree to the result of ast.parse(the text read from path).
    tree = ast.parse(path.read_text())
    # Set names to a set containing the text 'test_real_congested_run_has_safe_dense_traffic_and_complete_di...',
    # the text...
    names = {"test_real_congested_run_has_safe_dense_traffic_and_complete_discharge",
             "test_live_state_exports_measured_counts_and_execution_flags"}
    # Set functions to a list of n for n in tree.body; retain entries satisfying whether n has type
    # ast.FunctionDef and n.name belongs to names.
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    # Require the number of entries in functions equals 2; otherwise raise AssertionError.
    assert len(functions) == 2
    # Iterate over functions, binding each item to f.
    for f in functions:
        # Set xfail to the next item from a lazy sequence of d for d in f.decorator_list; retain entries
        # satisfying whether d has type ast.Call and ast.unparse(d.func) equals 'pytest.mark.xfail'.
        xfail = next(d for d in f.decorator_list if isinstance(d, ast.Call) and ast.unparse(d.func) == "pytest.mark.xfail")
        # Require whether any item is true in a lazy sequence of k.arg equals 'strict' and k.value.value is the
        # same object as True for k in xfail.keywords; otherwise raise AssertionError.
        assert any(k.arg == "strict" and k.value.value is True for k in xfail.keywords)
        # Require whether any item is true in a lazy sequence of k.arg equals 'raises' and ast.unparse(k.value)
        # equals 'AssertionError' for k in xfail.keywords; otherwise raise AssertionError.
        assert any(k.arg == "raises" and ast.unparse(k.value) == "AssertionError" for k in xfail.keywords)
        # Require whether any item is true in a lazy sequence of whether n has type ast.Assert for n in the result
        # of ast.walk(f); otherwise raise AssertionError.
        assert any(isinstance(n, ast.Assert) for n in ast.walk(f))
    # Set fixture to the next item from a lazy sequence of n for n in tree.body; retain entries satisfying whether
    # n has type ast.FunctionDef and n.name equals 'congested_run'.
    fixture = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "congested_run")
    # Set source to the result of ast.unparse(fixture).
    source = ast.unparse(fixture)
    # Require the text 'metrics["collisions"]' belongs to the result of source.replace(the text "'", the text '"')
    # and the text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT' belongs to source; otherwise raise AssertionError.
    assert 'metrics["collisions"]' in source.replace("'", '"') and "COMMUNICATED_PRECEDENCE_DISAGREEMENT" in source
    # Require the text 'live[' belongs to source and the text 'policy_hash_unchanged' belongs to source; otherwise
    # raise AssertionError.
    assert "live[" in source and "policy_hash_unchanged" in source

# Check archived replay selects original runtime without writing v1 using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_archived_replay_selects_original_runtime_without_writing_v1(monkeypatch):
    # Set captured to an empty list.
    captured = []
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(v1_replay, "_launch", lambda command, **kwargs: captured.append(command))
    # Call v1_replay.replay_v1 with the supplied arguments.
    v1_replay.replay_v1("PV-04B", models.V1_ROOT, run_id="20261008T171632326120Z_c654aaee")
    # Require the text 'PV-04' belongs to captured at 0; otherwise raise AssertionError.
    assert "PV-04" in captured[0]
    # Require whether any item is true in a lazy sequence of the text 'replays' belongs to item for item in
    # captured at 0; otherwise raise AssertionError.
    assert any("replays" in item for item in captured[0])
    # Require whether any item is true in a lazy sequence of the text 'runtime' belongs to item for item in
    # captured at 0; otherwise raise AssertionError.
    assert any("runtime" in item for item in captured[0])

# Check fixture contract breach cannot be consumed as expected liveness using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_fixture_contract_breach_cannot_be_consumed_as_expected_liveness():
    # Import wraps from functools for the operations below.
    from functools import wraps
    # Set tree to the result of ast.parse(the text read from
    # Path('tests/test_ego_execution_and_dense_traffic.py')).
    tree = ast.parse(Path("tests/test_ego_execution_and_dense_traffic.py").read_text())
    # Set guard to the next item from a lazy sequence of n for n in tree.body; retain entries satisfying whether n
    # has type ast.FunctionDef and n.name equals...
    guard = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_fixture_errors_are_not_known_liveness_failures")
    # Set namespace to a dictionary containing wraps.
    namespace = {"wraps": wraps}
    # Call exec with the supplied arguments.
    exec(compile(ast.Module(body=[guard], type_ignores=[]), "fixture_guard", "exec"), namespace)
    # Corrupt safety using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def corrupt_safety():
        # Raise AssertionError with the text 'collision or changed policy' to stop this execution path.
        raise AssertionError("collision or changed policy")
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="DENSE_FIXTURE_CONTRACT_BREACH"):
        # Call namespace[guard.name](corrupt_safety) with the supplied arguments.
        namespace[guard.name](corrupt_safety)()
    # Require the result of namespace[guard.name](lambda: 'validated fixture')() equals the text 'validated
    # fixture'; otherwise raise AssertionError.
    assert namespace[guard.name](lambda: "validated fixture")() == "validated fixture"
