"""Focused evaluator contracts, never a change to operational acceptance."""
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
# Import torch for use in this module.
import torch
# Import DEADLOCK_DURATION_SECONDS from config for the operations below.
from config import DEADLOCK_DURATION_SECONDS
# Import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, classify from post_training_evaluation.models for the
# operations below.
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, classify
# Import schedule_payload, source_identities from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import schedule_payload, source_identities
# Import CASES_V1 as CASES, BY_ID, frozen_cases from targeted_validation.cases for the operations below.
from targeted_validation.cases import CASES_V1 as CASES, BY_ID, frozen_cases
# Import models, runner from targeted_validation for the operations below.
from targeted_validation import models, runner
# Import PanelTelemetry, STOP_PREFIX from targeted_validation.metrics for the operations below.
from targeted_validation.metrics import PanelTelemetry, STOP_PREFIX
# Import build_payload, report from targeted_validation.reporting for the operations below.
from targeted_validation.reporting import build_payload, report

# Check exact six cases six episodes and budgets using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_six_cases_six_episodes_and_budgets():
    # Require a list of c.case_id for c in CASES equals a list of formatted text built from the embedded values
    # for i in the integer range defined by 1, 7; otherwise raise AssertionError.
    assert [c.case_id for c in CASES] == [f"PV-{i:02d}" for i in range(1, 7)]
    # Require the sum of a lazy sequence of the number of entries in c.methods for c in CASES equals 6; otherwise
    # raise AssertionError.
    assert sum(len(c.methods) for c in CASES) == 6
    # Require the sum of a lazy sequence of c.budget_seconds multiplied by len(c.methods) for c in CASES equals
    # 570; otherwise raise AssertionError.
    assert sum(c.budget_seconds * len(c.methods) for c in CASES) == 570
    # Require BY_ID['PV-02'].methods equals a tuple containing the text 'PROPOSED_MAPPO', the text 'RULES_ONLY';
    # otherwise raise AssertionError.
    assert BY_ID["PV-02"].methods == ("PROPOSED_MAPPO", "RULES_ONLY")
    # Require a list of c.scenario_id for c in CASES sliced by :-1 equals a list containing the text
    # 'rule_resolved_two', the text 'regulatory_cycle', the text 'multiple_left_turns', the text...; otherwise
    # raise AssertionError.
    assert [c.scenario_id for c in CASES[:-1]] == ["rule_resolved_two", "regulatory_cycle", "multiple_left_turns", "congested_four_approach", "four_way_simultaneous"]

# Check dense exact predeclared schedule not random easier substitute using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_dense_exact_predeclared_schedule_not_random_easier_substitute():
    # Import get_scenario from runtime_simulation.scenarios for the operations below.
    from runtime_simulation.scenarios import get_scenario
    # Set schedule to the result of BY_ID['PV-04'].schedule().
    schedule = BY_ID["PV-04"].schedule()
    # Require schedule equals the result of get_scenario('congested_four_approach').schedule(); otherwise raise
    # AssertionError.
    assert schedule == get_scenario("congested_four_approach").schedule()
    # Require a dictionary of a mapped to the number of entries in rows for (a, rows) in key/value pairs from
    # schedule equals the result of dict.fromkeys(the text 'NESW', 4); otherwise raise AssertionError.
    assert {a: len(rows) for a, rows in schedule.items()} == dict.fromkeys("NESW", 4)
    # Require the number of entries in a set of r.movement_path_id for rows in values from schedule equals 12;
    # otherwise raise AssertionError.
    assert len({r.movement_path_id for rows in schedule.values() for r in rows}) == 12
    # Require a list of r.scheduled_departure_seconds for r in schedule at 'N' equals a list containing 0, 1.5, 3,
    # 4.5; otherwise raise AssertionError.
    assert [r.scheduled_departure_seconds for r in schedule["N"]] == [0, 1.5, 3, 4.5]
    # Require BY_ID['PV-04'].scenario().continuous; otherwise raise AssertionError.
    assert BY_ID["PV-04"].scenario().continuous

# Check panel freeze tamper and source change rejected using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_panel_freeze_tamper_and_source_change_rejected(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Require the result of models.prepare(tmp_path) equals frozen; otherwise raise AssertionError.
    assert models.prepare(tmp_path) == frozen
    # Require frozen['manifest'] at 'policy_sha256' equals EXPECTED_POLICY_HASH; equals the result of
    # file_hash(POLICY); otherwise raise AssertionError.
    assert frozen["manifest"]["policy_sha256"] == EXPECTED_POLICY_HASH == file_hash(POLICY)
    # Set value to the decoded data produced by json.loads from the text read from (tmp_path / 'manifest.json').
    value = json.loads((tmp_path / "manifest.json").read_text())
    # Set value['manifest']['cases'][3]['vehicle_count'] to 4.
    value["manifest"]["cases"][3]["vehicle_count"] = 4
    # Write the supplied text to (tmp_path / 'manifest.json').
    (tmp_path / "manifest.json").write_text(json.dumps(value))
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="CHECKSUM"):
        # Call models.prepare with the supplied arguments.
        models.prepare(tmp_path)

# Telemetry using the inputs and processing steps below.
# Output: the result of PanelTelemetry(the result of BY_ID['PV-01'].schedule()).
def telemetry():
    # Return the result of PanelTelemetry(the result of BY_ID['PV-01'].schedule()) to the caller.
    return PanelTelemetry(BY_ID["PV-01"].schedule(), budget_seconds=60, expected_panel_sources=models.panel_sources())

# Fake world using the inputs and processing steps below.
# Output: a tuple containing t, ids, states, paths, zones, api, life.
def fake_world():
    # Set t to the result of telemetry().
    t = telemetry()
    # Set ids to a tuple built from t.waits.
    ids = tuple(t.waits)
    # Set states to a dictionary of v mapped to a dictionary built from the supplied values for v in ids.
    states = {v: dict(lane_id="in", lane_position=1., position=(0., 0.), speed=0., comfortable_deceleration_mps2=4.5) for v in ids}
    # Set paths to the result of SimpleNamespace().
    paths = SimpleNamespace(paths={p: SimpleNamespace(incoming_lane_id="in") for p in t.movements.values()})
    # Set zones to the result of SimpleNamespace().
    zones = SimpleNamespace(zone_record=lambda *args: None)
    # Set api to the result of SimpleNamespace().
    api = SimpleNamespace(simulation=SimpleNamespace(getStartingTeleportIDList=lambda: (), getCollisions=lambda: ()))
    # Set life to the result of SimpleNamespace().
    life = SimpleNamespace(departed_vehicle_ids=ids, arrived_vehicle_ids=())
    # Return a tuple containing t, ids, states, paths, zones, api, life to the caller.
    return t, ids, states, paths, zones, api, life

# Step using the inputs and processing steps below.
# Input t: the supplied t.
# Input ids: the supplied ids.
# Input states: the supplied states.
# Input paths: the supplied paths.
# Input zones: the supplied zones.
# Input api: the supplied api.
# Input life: the supplied life.
# Input now: the time used for this operation.
# Output: no explicit value; normal completion returns None.
def step(t, ids, states, paths, zones, api, life, now):
    # Set t.frame_decisions to a dictionary of v mapped to a tuple containing the text 'SAFE_HOLD', the text
    # 'MISSING_OR_STALE_LOCAL_COORDINATION', the text 'HELD_BEFORE_ZONE' for v in ids.
    t.frame_decisions = {v: ("SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE") for v in ids}
    # Call t.observe with the supplied arguments.
    t.observe(now, states, life, t.movements, paths, zones, api)

# Check deadlock uses existing threshold and requires stationary all held using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_deadlock_uses_existing_threshold_and_requires_stationary_all_held():
    # Set (t, ids, states, paths, zones, api, life) to the result of fake_world().
    t, ids, states, paths, zones, api, life = fake_world()
    # Advance step using its configured step operation.
    step(t, ids, states, paths, zones, api, life, .04)
    # Set life.departed_vehicle_ids to an empty tuple.
    life.departed_vehicle_ids = ()
    # Advance step using its configured step operation.
    step(t, ids, states, paths, zones, api, life, DEADLOCK_DURATION_SECONDS)
    # Require t.termination_reason is the same object as None; otherwise raise AssertionError.
    assert t.termination_reason is None
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "DEADLOCK_CONFIRMED"):
        # Advance step using its configured step operation.
        step(t, ids, states, paths, zones, api, life, DEADLOCK_DURATION_SECONDS + .08)
    # Set (runtime, error) to the result of t.finalize_runtime(a dictionary containing metrics, STOP_PREFIX plus
    # the text 'DEADLOCK_CONFIRMED').
    runtime, error = t.finalize_runtime({"metrics": {}}, STOP_PREFIX + "DEADLOCK_CONFIRMED")
    # Require error is the same object as None; otherwise raise AssertionError.
    assert error is None
    # Set m to the result of t.result(runtime).
    m = t.result(runtime)
    # Require m at 'deadlock_observed' and the negation of m at 'timeout'; otherwise raise AssertionError.
    assert m["deadlock_observed"] and not m["timeout"]
    # Require the result of classify(m, a dictionary containing valid) equals the text 'SAFE_DEGRADATION';
    # otherwise raise AssertionError.
    assert classify(m, {"valid": True}) == "SAFE_DEGRADATION"

# Apply pytest.mark.parametrize('change', ('future_demand', 'clearing', 'moving', 'position_progress',... as a
# decorator to configure the following definition.
@pytest.mark.parametrize("change", ("future_demand", "clearing", "moving", "position_progress", "permission"))
# Check no premature deadlock stop using the setup, calls, and assertions below.
# Input change: the supplied change.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_no_premature_deadlock_stop(change):
    # Set (t, ids, states, paths, zones, api, life) to the result of fake_world().
    t, ids, states, paths, zones, api, life = fake_world()
    # Advance step using its configured step operation.
    step(t, ids, states, paths, zones, api, life, .04)
    # Set life.departed_vehicle_ids to an empty tuple.
    life.departed_vehicle_ids = ()
    # Run this branch when change equals the text 'future_demand'.
    if change == "future_demand":
        # Delete t.departures[ids[0]] from its containing namespace or collection.
        del t.departures[ids[0]]
    # Run this branch when change equals the text 'clearing'.
    if change == "clearing":
        # Set states[ids[0]]['lane_id'] to the text 'out'.
        states[ids[0]]["lane_id"] = "out"
    # Run this branch when change equals the text 'moving'.
    if change == "moving":
        # Set states[ids[0]]['speed'] to 1.0.
        states[ids[0]]["speed"] = 1.
    # Run this branch when change equals the text 'position_progress'.
    if change == "position_progress":
        # Set states[ids[0]]['lane_position'] to 2.0.
        states[ids[0]]["lane_position"] = 2.
    # Set t.frame_decisions to a dictionary of v mapped to a tuple containing the text 'SAFE_HOLD', the text
    # 'MISSING', the text 'HELD_BEFORE_ZONE' for v in ids.
    t.frame_decisions = {v: ("SAFE_HOLD", "MISSING", "HELD_BEFORE_ZONE") for v in ids}
    # Run this branch when change equals the text 'permission'.
    if change == "permission":
        # Set t.frame_decisions[ids[0]] to a tuple containing the text 'PERMITTED', the text
        # 'VALID_ADMISSION_LOCK', the text 'COMMITTED_TO_ENTER'.
        t.frame_decisions[ids[0]] = ("PERMITTED", "VALID_ADMISSION_LOCK", "COMMITTED_TO_ENTER")
    # Call t.observe with the supplied arguments.
    t.observe(30., states, life, t.movements, paths, zones, api)
    # Require t.termination_reason is the same object as None; otherwise raise AssertionError.
    assert t.termination_reason is None

# Apply pytest.mark.parametrize('reason', ('ALL_COMPLETED', 'UNSAFE_FAILURE', 'DEADLOCK_CONFIRMED')) as a
# decorator to configure the following definition.
@pytest.mark.parametrize("reason", ("ALL_COMPLETED", "UNSAFE_FAILURE", "DEADLOCK_CONFIRMED"))
# Check only exact evaluator stop is handled using the setup, calls, and assertions below.
# Input reason: the supplied reason.
# Output: no explicit value; normal completion returns None.
def test_only_exact_evaluator_stop_is_handled(reason):
    # Set t to the result of telemetry().
    t = telemetry()
    # Set t.termination_reason to reason.
    t.termination_reason = reason
    # Require t.finalize_runtime({}, STOP_PREFIX + reason) at 1 is the same object as None; otherwise raise
    # AssertionError.
    assert t.finalize_runtime({}, STOP_PREFIX + reason)[1] is None
    # Require t.finalize_runtime({}, 'actual runtime failure') at 1 equals the text 'actual runtime failure';
    # otherwise raise AssertionError.
    assert t.finalize_runtime({}, "actual runtime failure")[1] == "actual runtime failure"

# Check hard budget unsafe classification and no event rate na using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_hard_budget_unsafe_classification_and_no_event_rate_na():
    # Set t to the result of telemetry().
    t = telemetry()
    # Call t.finalize_runtime with the supplied arguments.
    t.finalize_runtime({"metrics": {}}, None)
    # Require t.termination_reason equals the text 'HARD_TIME_BUDGET'; otherwise raise AssertionError.
    assert t.termination_reason == "HARD_TIME_BUDGET"
    # Require t.result({}) at 'fallback_rate' is the same object as None; otherwise raise AssertionError.
    assert t.result({})["fallback_rate"] is None
    # Call t.finalize_runtime with the supplied arguments.
    t.finalize_runtime({"metrics": {"blocked_zone_violations": 1}}, "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    # Set m to the result of t.result(a dictionary containing metrics).
    m = t.result({"metrics": {"blocked_zone_violations": 1}}, aborted=True)
    # Require t.termination_reason equals the text 'UNSAFE_FAILURE' and the result of classify(m, a dictionary
    # containing valid, the text 'error') equals the text 'UNSAFE_FAILURE'; otherwise raise AssertionError.
    assert t.termination_reason == "UNSAFE_FAILURE" and classify(m, {"valid": True}, "error") == "UNSAFE_FAILURE"

# Check observed collision stops without manufacturing physical collision using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_observed_collision_stops_without_manufacturing_physical_collision():
    # Set (t, ids, states, paths, zones, api, life) to the result of fake_world().
    t, ids, states, paths, zones, api, life = fake_world()
    # Set api.simulation.getCollisions to a callback that returns a tuple containing the result of
    # SimpleNamespace().
    api.simulation.getCollisions = lambda: (SimpleNamespace(collider="A", victim="B", type="mock_evidence"),)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "UNSAFE_FAILURE"):
        # Advance step using its configured step operation.
        step(t, ids, states, paths, zones, api, life, .04)
    # Require t.collisions equals 1 and t.termination_reason equals the text 'UNSAFE_FAILURE'; otherwise raise
    # AssertionError.
    assert t.collisions == 1 and t.termination_reason == "UNSAFE_FAILURE"
    # Require the result of classify(the result of t.result(an empty dictionary), a dictionary containing valid)
    # equals the text 'UNSAFE_FAILURE'; otherwise raise AssertionError.
    assert classify(t.result({}), {"valid": True}) == "UNSAFE_FAILURE"

# Check completed ledger immediately stops with true reason using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_completed_ledger_immediately_stops_with_true_reason():
    # Set (t, ids, states, paths, zones, api, life) to the result of fake_world().
    t, ids, states, paths, zones, api, life = fake_world()
    # Advance step using its configured step operation.
    step(t, ids, states, paths, zones, api, life, .04)
    # Set life.departed_vehicle_ids to an empty tuple.
    life.departed_vehicle_ids = ()
    # Set life.arrived_vehicle_ids to ids.
    life.arrived_vehicle_ids = ids
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match=STOP_PREFIX + "ALL_COMPLETED"):
        # Advance step using its configured step operation.
        step(t, ids, {}, paths, zones, api, life, .08)
    # Require the result of classify(the result of t.result(an empty dictionary), a dictionary containing valid)
    # equals the text 'PASS'; otherwise raise AssertionError.
    assert classify(t.result({}), {"valid": True}) == "PASS"

# Check result checksum corruption is rejected using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_result_checksum_corruption_is_rejected(tmp_path):
    # Import write_json from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import write_json
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Set directory to tmp_path joined with the path segment 'runs' joined with the path segment 'record'.
    directory = tmp_path / "runs" / "record"
    # Set record to a dictionary built from the supplied values.
    record = dict(suite="panel", classification="SAFE_DEGRADATION")
    # Call write_json with the supplied arguments.
    write_json(directory / "result.json", record)
    # Call write_json with the supplied arguments.
    write_json(directory / "result.sha256.json", dict(result_hash="tampered"))
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match="RESULT_CHECKSUM"):
        # Call models.records with the supplied arguments.
        models.records(tmp_path)

# Check runtime guard real bundle blocks training critic global and preserves e5 using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then handle the specified errors.
def test_runtime_guard_real_bundle_blocks_training_critic_global_and_preserves_e5():
    # Import IntegrityGuard from post_training_evaluation.integrity for the operations below.
    from post_training_evaluation.integrity import IntegrityGuard
    # Import _load_bundle from negotiation_training.final_selection for the operations below.
    from negotiation_training.final_selection import _load_bundle
    # Import ConflictZoneExecutionPlanner from negotiation_execution for the operations below.
    from negotiation_execution import ConflictZoneExecutionPlanner
    # Set (_, bundle) to the result of _load_bundle(POLICY).
    _, bundle = _load_bundle(POLICY)
    # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding each item
    # to module.
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        # Call module.eval with the supplied arguments.
        module.eval()
    # Set guard to the result of IntegrityGuard().
    guard = IntegrityGuard()
    # Call guard.bind with the supplied arguments.
    guard.bind(bundle)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Iterate over a tuple containing a callback that returns the result of torch.tensor(1.0,
        # requires_grad=True).backward(), a callback that..., binding each item to operation.
        for operation in (lambda: torch.tensor(1., requires_grad=True).backward(),
                          # Include a callback that returns the result of bundle.proposer_actor.train() in this
                          # tuple.
                          lambda: bundle.proposer_actor.train(),
                          # Include a callback that returns the result of bundle.centralized_critic.forward(None)
                          # in this tuple.
                          lambda: bundle.centralized_critic.forward(None),
                          # Include a callback that returns the result of ConflictZoneExecutionPlanner.plan(None,
                          # None) in this tuple.
                          lambda: ConflictZoneExecutionPlanner.plan(None, None),
                          # Include a callback that returns the result of
                          # torch.optim.Adam(bundle.gnn.parameters()).step() in this tuple.
                          lambda: torch.optim.Adam(bundle.gnn.parameters()).step()):
            # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
            with pytest.raises(RuntimeError, match="INTEGRITY_BREACH"):
                # Call operation with the supplied arguments.
                operation()
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Set result to the result of guard.finish(a dictionary built from the supplied values).
        result = guard.finish(dict(decentralized_execution=True, centralized_execution_graph_used_for_control=False,
            # Supply metrics as a dictionary built from the supplied values.
            # Supply maximum_negotiation_participants as 4.
            metrics=dict(maximum_negotiation_participants=4)))
    # Require the negation of result at 'valid' and result at 'policy_hash_unchanged' and result at
    # 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert not result["valid"] and result["policy_hash_unchanged"] and result["parameter_updates"] == 0

# Apply pytest.mark.parametrize('participants', (4, 5)) as a decorator to configure the following definition.
@pytest.mark.parametrize("participants", (4, 5))
# Check guard enforces queue head limit using the setup, calls, and assertions below.
# Input participants: the supplied participants.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_guard_enforces_queue_head_limit(participants):
    # Import IntegrityGuard from post_training_evaluation.integrity for the operations below.
    from post_training_evaluation.integrity import IntegrityGuard
    # Import _load_bundle from negotiation_training.final_selection for the operations below.
    from negotiation_training.final_selection import _load_bundle
    # Set (_, bundle) to the result of _load_bundle(POLICY).
    _, bundle = _load_bundle(POLICY)
    # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding each item
    # to module.
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        # Call module.eval with the supplied arguments.
        module.eval()
    # Set guard to the result of IntegrityGuard().
    guard = IntegrityGuard()
    # Call guard.bind with the supplied arguments.
    guard.bind(bundle)
    # Set result to the result of guard.finish(a dictionary built from the supplied values).
    result = guard.finish(dict(decentralized_execution=True, centralized_execution_graph_used_for_control=False,
        # Supply metrics as a dictionary built from the supplied values.
        # Supply maximum_negotiation_participants as participants.
        metrics=dict(maximum_negotiation_participants=participants)))
    # Require result at 'valid' equals participants is at most 4; otherwise raise AssertionError.
    assert result["valid"] == (participants <= 4)
    # Require result at 'centralized_critic_runtime_calls' equals result at 'optimizer_steps'; equals result at
    # 'training_operations'; equals 0; otherwise raise AssertionError.
    assert result["centralized_critic_runtime_calls"] == result["optimizer_steps"] == result["training_operations"] == 0

# Check reports preserve failure classes and traceability using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_reports_preserve_failure_classes_and_traceability(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Set runs to a list of a dictionary built from the supplied values for (cid, status) in a tuple containing a
    # tuple containing the text 'PV-01', the text 'PASS', a tuple containing the text 'PV-04', the text...
    runs = [dict(scenario_id=BY_ID[cid].scenario_id, method="PROPOSED_MAPPO", classification=status,
        # Supply metrics as an empty dictionary.
        # Supply integrity as an empty dictionary.
        # Supply run_id as cid.
        metrics={}, integrity={}, run_id=cid) for cid, status in (("PV-01", "PASS"), ("PV-04", "SAFE_DEGRADATION"), ("PV-05", "UNSAFE_FAILURE"))]
    # Set payload to the result of build_payload(frozen, runs).
    payload = build_payload(frozen, runs)
    # Require a set of e at 'classification' for e in payload at 'cases' equals a set containing the text
    # 'NOT_RUN', the text 'PASS', the text 'SAFE_DEGRADATION', the text 'UNSAFE_FAILURE'; otherwise raise
    # AssertionError.
    assert {e["classification"] for e in payload["cases"]} == {"NOT_RUN", "PASS", "SAFE_DEGRADATION", "UNSAFE_FAILURE"}
    # Require the number of entries in payload at 'limitations' equals 2; otherwise raise AssertionError.
    assert len(payload["limitations"]) == 2
    # Require payload['traceability'][2] at 'evidence_cases' equals a tuple containing the text 'PV-04A', the text
    # 'PV-04B'; otherwise raise AssertionError.
    assert payload["traceability"][2]["evidence_cases"] == ("PV-04A", "PV-04B")
    # Require payload['traceability'][2] at 'status' equals the text 'IMPLEMENTED; MEASUREMENT_PENDING'; otherwise
    # raise AssertionError.
    assert payload["traceability"][2]["status"] == "IMPLEMENTED; MEASUREMENT_PENDING"
    # Require the negation of payload at 'complete'; otherwise raise AssertionError.
    assert not payload["complete"]
    # Call report with the supplied arguments.
    report(tmp_path)
    # Set html to the text read from (tmp_path / 'latest/TARGETED_VALIDATION_REPORT.html').
    html = (tmp_path / "latest/TARGETED_VALIDATION_REPORT.html").read_text()
    # Require the text 'NOT_RUN' belongs to html and the text 'N/A' belongs to html and the text 'PANEL FEEDBACK
    # TRACEABILITY' belongs to html; otherwise raise AssertionError.
    assert "NOT_RUN" in html and "N/A" in html and "PANEL FEEDBACK TRACEABILITY" in html

# Check fault checks current infrastructure pass using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_fault_checks_current_infrastructure_pass(tmp_path):
    # Set saved to the result of runner.faults(tmp_path, the result of models.prepare(tmp_path)).
    saved = runner.faults(tmp_path, models.prepare(tmp_path))
    # Require saved at 'classification' equals the text 'PASS'; otherwise raise AssertionError.
    assert saved["classification"] == "PASS"
    # Require a set of t at 'fault' for t in saved at 'tests' is at least a set containing the text
    # 'missing_required_coordination', the text 'stale_coordination'; otherwise raise AssertionError.
    assert {t["fault"] for t in saved["tests"]} >= {"missing_required_coordination", "stale_coordination"}
    # Require whether every item is true in a lazy sequence of t at 'permission' equals the text 'SAFE_HOLD' for t
    # in saved at 'tests'; otherwise raise AssertionError.
    assert all(t["permission"] == "SAFE_HOLD" for t in saved["tests"])

# Check wrapper reuses runtime and paired exact demand using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_wrapper_reuses_runtime_and_paired_exact_demand(monkeypatch, tmp_path):
    # Set captured to an empty list.
    captured = []
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner, "run_episode", lambda *args, **kw: captured.append((args, kw)))
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Iterate over BY_ID['PV-02'].methods, binding each item to method.
    for method in BY_ID["PV-02"].methods:
        # Call runner.execute with the supplied arguments.
        runner.execute(BY_ID["PV-02"], method, frozen, tmp_path)
    # Require captured[0][1] at 'schedule' equals captured[1][1] at 'schedule'; otherwise raise AssertionError.
    assert captured[0][1]["schedule"] == captured[1][1]["schedule"]
    # Require runner.run_episode is a different object from None; otherwise raise AssertionError.
    assert runner.run_episode is not None
    # Require the text 'setSpeed' does not belong to the result of inspect.getsource(runner); otherwise raise
    # AssertionError.
    assert "setSpeed" not in inspect.getsource(runner)

# Check exact replay restores schedule method seed and budget using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_exact_replay_restores_schedule_method_seed_and_budget(monkeypatch, tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen = models.prepare(tmp_path)
    # Set case to BY_ID at 'PV-04'.
    case = BY_ID["PV-04"]
    # Set rid to the text '20261008T010101000000Z_abcdef01'.
    rid = "20261008T010101000000Z_abcdef01"
    # Set action_seed to an integer built from digest((frozen['manifest']['protocol_id'], case.scenario_id, None,
    # 'PROPOSED_MAPPO')) sliced by :16 modulo 2 raised to the power 31.
    action_seed = int(digest((frozen["manifest"]["protocol_id"], case.scenario_id, None, "PROPOSED_MAPPO"))[:16], 16) % (2**31)
    # Set prior to a dictionary built from the supplied values.
    prior = dict(run_id=rid, scenario_id=case.scenario_id, method="PROPOSED_MAPPO", suite="panel", policy_action_seed=action_seed)
    # Set directory to tmp_path joined with the path segment 'runs' divided by rid.
    directory = tmp_path / "runs" / rid
    # Create the directory requested by directory.
    directory.mkdir(parents=True)
    # Write the supplied text to (directory / 'provenance.json').
    (directory / "provenance.json").write_text(json.dumps(dict(schedule=schedule_payload(case.schedule()), policy_action_seed=action_seed)))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner, "records", lambda root, suite="panel": [prior] if suite == "panel" else [])
    # Set calls to an empty list.
    calls = []
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner, "execute", lambda *args, **kw: calls.append((args, kw)))
    # Call runner.replay with the supplied arguments.
    runner.replay("PV-04", tmp_path, run_id=rid, gui=True)
    # Require calls[0][0][0].budget_seconds equals 180; otherwise raise AssertionError.
    assert calls[0][0][0].budget_seconds == 180
    # Require calls[0][1] at 'schedule' equals the result of case.schedule(); otherwise raise AssertionError.
    assert calls[0][1]["schedule"] == case.schedule()
    # Require calls[0][1] at 'replay_of' equals rid and calls[0][1] at 'gui'; otherwise raise AssertionError.
    assert calls[0][1]["replay_of"] == rid and calls[0][1]["gui"]
