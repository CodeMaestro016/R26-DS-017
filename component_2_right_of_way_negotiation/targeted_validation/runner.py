"""Thin wrapper of post_training_evaluation.run_episode, never a vehicle controller."""
# Import json for use in this module.
import json
# Import re for use in this module.
import re
# Import sys for use in this module.
import sys
# Import partial from functools for the operations below.
from functools import partial
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import perf_counter from time for the operations below.
from time import perf_counter
# Import run_episode from post_training_evaluation.runner for the operations below.
from post_training_evaluation.runner import run_episode
# Import restore_schedule from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import restore_schedule
# Import evaluate_faults from post_training_evaluation.faults for the operations below.
from post_training_evaluation.faults import evaluate_faults
# Import digest, write_json from post_training_evaluation.models for the operations below.
from post_training_evaluation.models import digest, write_json
# Import CASES, BY_ID from .cases for the operations below.
from .cases import CASES, BY_ID
# Import ROOT, V1_ROOT, EVIDENCE, prepare, records, read_checked_manifest from .models for the operations below.
from .models import ROOT, V1_ROOT, EVIDENCE, prepare, records, read_checked_manifest
# Import PanelTelemetry from .metrics for the operations below.
from .metrics import PanelTelemetry

# Execute using the inputs and processing steps below.
# Input case: the supplied case.
# Input method: the supplied method.
# Input frozen: the supplied frozen.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Input gui: the supplied gui.
# Input replay_of: the supplied replay of.
# Input schedule: the supplied schedule.
# Output: the result of run_episode(the result of case.scenario(), None, method, frozen).
# Processing: select branches using the stated conditions.
def execute(case, method, frozen, root=ROOT, *, suite="panel", gui=False,
            # Declare replay_of, schedule as input parameters.
            replay_of=None, schedule=None):
    # Set entry to the next item from a lazy sequence of c for c in frozen['manifest'] at 'cases'; retain entries
    # satisfying c at 'case_id' equals case.case_id.
    entry = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == case.case_id)
    # Run this branch when method does not belong to entry at 'methods' or case.budget_seconds differs from entry
    # at 'budget_seconds' or case.scenario_id differs from entry at 'scenario_id'.
    if method not in entry["methods"] or case.budget_seconds != entry["budget_seconds"] or case.scenario_id != entry["scenario_id"]:
        # Raise RuntimeError with the text 'FROZEN_PANEL_CASE_MISMATCH' to stop this execution path.
        raise RuntimeError("FROZEN_PANEL_CASE_MISMATCH")
    # Set demand to the result of restore_schedule(entry at 'schedule') when schedule is the same object as None,
    # otherwise schedule.
    demand = restore_schedule(entry["schedule"]) if schedule is None else schedule
    # Run this branch when the result of digest(entry at 'schedule') differs from the result of digest(a
    # dictionary of a mapped to a list of vars(x) for x in rows for (a, rows) in key/value pairs...).
    if digest(entry["schedule"]) != digest({a: [vars(x) for x in rows] for a, rows in demand.items()}):
        # Raise RuntimeError with the text 'PANEL_REPLAY_DEMAND_MISMATCH' to stop this execution path.
        raise RuntimeError("PANEL_REPLAY_DEMAND_MISMATCH")
    # Return the result of run_episode(the result of case.scenario(), None, method, frozen) to the caller.
    return run_episode(case.scenario(), None, method, frozen, root=root, suite=suite,
        # Supply schedule as demand.
        # Supply gui as gui.
        # Supply replay_of as replay_of.
        schedule=demand, gui=gui, replay_of=replay_of,
        # Supply observer_factory as the result of partial(PanelTelemetry).
        # Supply budget_seconds as case.budget_seconds.
        observer_factory=partial(PanelTelemetry, budget_seconds=case.budget_seconds,
            # Supply expected_panel_sources as frozen['manifest'] at 'panel_source_identities'.
            expected_panel_sources=frozen["manifest"]["panel_source_identities"]),
        # Supply evidence_classification as EVIDENCE when suite equals the text 'panel', otherwise the text
        # 'PREFLIGHT_NOT_PANEL_CASE_EVIDENCE' when suite equals the text 'preflight', otherwise the text
        # 'TARGETED_PANEL_VALIDATION_REPLAY'.
        evidence_classification=EVIDENCE if suite == "panel" else "PREFLIGHT_NOT_PANEL_CASE_EVIDENCE" if suite == "preflight" else "TARGETED_PANEL_VALIDATION_REPLAY",
        # Declare rid as input parameter.
        replay_command_factory=lambda rid: f'& "{sys.executable}" -B run_targeted_validation.py --replay {case.case_id} --run-id {rid} --gui --output-root "{Path(root)}"')

# Faults using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input frozen: the supplied frozen.
# Input preflight: the supplied preflight.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def faults(root, frozen, *, preflight=False):
    # Set name to the text 'preflight_faults.json' when preflight, otherwise the text 'faults.json'.
    name = "preflight_faults.json" if preflight else "faults.json"
    # Set path to the result of Path(root) divided by name.
    path = Path(root) / name
    # Run this branch when whether path exists.
    if path.exists():
        # Set saved to the decoded data produced by json.loads from the text read from path.
        saved = json.loads(path.read_text())
        # Run this branch when saved at 'manifest_hash' differs from frozen at 'manifest_hash' or saved at
        # 'checksum' differs from the result of digest(saved at 'tests').
        if saved["manifest_hash"] != frozen["manifest_hash"] or saved["checksum"] != digest(saved["tests"]):
            # Raise RuntimeError with the text 'PANEL_FAULT_EVIDENCE_MISMATCH' to stop this execution path.
            raise RuntimeError("PANEL_FAULT_EVIDENCE_MISMATCH")
        # Return saved to the caller.
        return saved
    # Set tests to the result of evaluate_faults().
    tests = evaluate_faults()
    # Set value to a dictionary built from the supplied values.
    value = dict(case_id="PV-06", evidence_classification="PREFLIGHT_NOT_PANEL_CASE_EVIDENCE" if preflight else EVIDENCE,
        # Supply manifest_hash as frozen at 'manifest_hash'.
        # Supply tests as tests.
        # Supply checksum as the result of digest(tests).
        manifest_hash=frozen["manifest_hash"], tests=tests, checksum=digest(tests),
        # Supply classification as the text 'PASS' when whether every item is true in a lazy sequence of t at
        # 'passed' for t in tests, otherwise the text 'UNSAFE_FAILURE'.
        classification="PASS" if all(t["passed"] for t in tests) else "UNSAFE_FAILURE",
        # Supply scope as the text 'Controlled current controller-interface fault checks; no SUMO...'.
        scope="Controlled current controller-interface fault checks; no SUMO episode, packet network or real V2V validation; traffic metrics N/A.")
    # Call write_json with the supplied arguments.
    write_json(path, value, exclusive=True)
    # Return value to the caller.
    return value

# Preflight using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: value.
# Processing: select branches using the stated conditions.
def preflight(root=ROOT):
    # Set start to the result of perf_counter().
    start = perf_counter()
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set record to the result of execute(BY_ID at 'PV-01', the text 'PROPOSED_MAPPO', frozen, root).
    record = execute(BY_ID["PV-01"], "PROPOSED_MAPPO", frozen, root, suite="preflight")
    # Set check to the result of faults(root, frozen).
    check = faults(root, frozen, preflight=True)
    # Set wall to the result of perf_counter() minus start.
    wall = perf_counter() - start
    # Set observed to record['metrics'] at 'observed_simulation_time_seconds'.
    observed = record["metrics"]["observed_simulation_time_seconds"]
    # Conservative observed wall/sim ratio times the full budgets; no promised ETA.
    # Set max_budget to frozen['manifest'] at 'maximum_simulated_seconds'.
    max_budget = frozen["manifest"]["maximum_simulated_seconds"]
    # Set projected to record at 'wall_clock_seconds' divided by observed multiplied by max_budget when observed
    # is greater than 0, otherwise None.
    projected = record["wall_clock_seconds"] / observed * max_budget if observed > 0 else None
    # Set historical to None.
    historical = None
    # Set old_log to the result of Path(the text 'results/repair_diagnostics/component2_full_tests.log').
    old_log = Path("results/repair_diagnostics/component2_full_tests.log")
    # Run this branch when whether old_log is an existing file.
    if old_log.is_file():
        # Set raw to the bytes read from old_log.
        raw = old_log.read_bytes()
        # Set text to the result of raw.decode(the text 'utf-16' when the result of raw.startswith(b'\xff\xfe'),
        # otherwise the text 'utf-8-sig').
        text = raw.decode("utf-16" if raw.startswith(b"\xff\xfe") else "utf-8-sig")
        # Set match to the result of re.search(the text '\\d+ failed, \\d+ passed in ([\\d.]+)s', text).
        match = re.search(r"\d+ failed, \d+ passed in ([\d.]+)s", text)
        # Run this branch when match.
        if match:
            # Set historical to a dictionary built from the supplied values.
            historical = dict(source=str(old_log),
                # Supply reference as the text 'Earlier complete regression suite including a 360-s dense...'.
                reference="Earlier complete regression suite including a 360-s dense fixture; total test wall time is a conservative reference, not an isolated dense benchmark.",
                # Supply reference_wall_seconds as a floating-point number built from the result of
                # match.group(1).
                # Supply reference_simulated_seconds as 360.0.
                reference_wall_seconds=float(match.group(1)), reference_simulated_seconds=360.,
                # Supply full_budget_extrapolation_seconds as a floating-point number built from the result of
                # match.group(1) divided by 360.0 multiplied by max_budget.
                full_budget_extrapolation_seconds=float(match.group(1)) / 360. * max_budget)
            # Set projected to the maximum of projected or 0.0, historical at 'full_budget_extrapolation_seconds'.
            projected = max(projected or 0., historical["full_budget_extrapolation_seconds"])
    # Set value to a dictionary built from the supplied values.
    value = dict(evidence_classification="PREFLIGHT_NOT_PANEL_CASE_EVIDENCE", manifest_hash=frozen["manifest_hash"],
        # Supply run_id as record at 'run_id'.
        # Supply wall_clock_seconds as wall.
        # Supply observed_simulated_seconds as observed.
        run_id=record["run_id"], wall_clock_seconds=wall, observed_simulated_seconds=observed,
        # Supply projected_full_budget_wall_seconds as projected.
        projected_full_budget_wall_seconds=projected,
        # Supply historical_runtime_reference as historical.
        historical_runtime_reference=historical,
        # Supply projection_limit as the text 'One two-vehicle episode cannot predict dense per-step costs;...'.
        projection_limit="One two-vehicle episode cannot predict dense per-step costs; this extrapolation excludes workload growth and does not promise wall time.",
        # Supply requires_runtime_review as projected is the same object as None or projected is greater than
        # 1800.
        requires_runtime_review=projected is None or projected > 1800,
        # Supply runtime_integrity_valid as record['integrity'] at 'valid'.
        # Supply traffic_classification as record at 'classification'.
        runtime_integrity_valid=record["integrity"]["valid"], traffic_classification=record["classification"],
        # Supply fault_checks_passed as check at 'classification' equals the text 'PASS'.
        # Supply full_suite_automatically_started as False.
        fault_checks_passed=check["classification"] == "PASS", full_suite_automatically_started=False)
    # Set directory to the result of Path(root) joined with the path segment 'preflight' divided by record at 'run_id'.
    directory = Path(root) / "preflight" / record["run_id"]
    # Call write_json with the supplied arguments.
    write_json(directory / "preflight.json", value, exclusive=True)
    # Call write_json with the supplied arguments.
    write_json(Path(root) / "preflight/latest.json", value)
    # Import report from .reporting for the operations below.
    from .reporting import report
    # Call report with the supplied arguments.
    report(root)
    # Display the text 'PREFLIGHT:'.
    print("PREFLIGHT:", json.dumps(value, indent=2), flush=True)
    # Return value to the caller.
    return value

# Run using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def run(root=ROOT):
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set done to a dictionary of a tuple containing r at 'scenario_id', r at 'method' mapped to r for r in the
    # result of records(root).
    done = {(r["scenario_id"], r["method"]): r for r in records(root)}
    # Run this branch when the number of entries in done differs from the number of entries in the result of
    # records(root).
    if len(done) != len(records(root)):
        # Raise RuntimeError with the text 'DUPLICATE_PANEL_EPISODES: results remain visible; select a...' to stop
        # this execution path.
        raise RuntimeError("DUPLICATE_PANEL_EPISODES: results remain visible; select a new version rather than cherry-pick")
    # Iterate over CASES, binding each item to case.
    for case in CASES:
        # Iterate over case.methods, binding each item to method.
        for method in case.methods:
            # Run this branch when a tuple containing case.scenario_id, method does not belong to done.
            if (case.scenario_id, method) not in done:
                # Call execute with the supplied arguments.
                execute(case, method, frozen, root)
    # Call faults with the supplied arguments.
    faults(root, frozen)
    # Import report, print_summary from .reporting for the operations below.
    from .reporting import report, print_summary
    # Set payload to the result of report(root).
    payload = report(root)
    # Call print_summary with the supplied arguments.
    print_summary(payload)
    # Return payload to the caller.
    return payload

# Execute a case once; never rerun for a favorable outcome.
# Input case_id: the supplied case id.
# Input root: the base directory used to resolve files.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def run_case(case_id, root=ROOT):
    """Execute a case once; never rerun for a favorable outcome."""
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set case to BY_ID at case_id.
    case = BY_ID[case_id]
    # Set done to a set of a tuple containing r at 'scenario_id', r at 'method' for r in the result of
    # records(root).
    done = {(r["scenario_id"], r["method"]) for r in records(root)}
    # Iterate over case.methods, binding each item to method.
    for method in case.methods:
        # Run this branch when a tuple containing case.scenario_id, method belongs to done.
        if (case.scenario_id, method) in done:
            # Raise RuntimeError with the text 'PANEL_CASE_ALREADY_RECORDED: use replay; do not replace results'
            # to stop this execution path.
            raise RuntimeError("PANEL_CASE_ALREADY_RECORDED: use replay; do not replace results")
        # Call execute with the supplied arguments.
        execute(case, method, frozen, root)
    # Run this branch when case_id equals the text 'PV-06'.
    if case_id == "PV-06":
        # Call faults with the supplied arguments.
        faults(root, frozen)
    # Import report, print_summary from .reporting for the operations below.
    from .reporting import report, print_summary
    # Set payload to the result of report(root).
    payload = report(root)
    # Call print_summary with the supplied arguments.
    print_summary(payload)
    # Return payload to the caller.
    return payload

# Replay using the inputs and processing steps below.
# Input case_id: the supplied case id.
# Input root: the base directory used to resolve files.
# Input run_id: the supplied run id.
# Input method: the supplied method.
# Input gui: the supplied gui.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def replay(case_id, root=ROOT, *, run_id=None, method="PROPOSED_MAPPO", gui=False):
    # Historical runs retain original source identity; renamed code is not
    # silently substituted for their measured implementation.
    # Set legacy to the result of Path(the text 'results/panel_validation').
    legacy = Path("results/panel_validation")
    # Set roots to a list containing the result of Path(root).
    roots = [Path(root)]
    # Run this branch when the result of Path(root).resolve() equals the result of ROOT.resolve() and the negation
    # of whether (Path(root) / 'manifest.json') exists.
    if Path(root).resolve() == ROOT.resolve() and not (Path(root)/"manifest.json").exists():
        # Set roots to a list containing legacy joined with the path segment 'v2', legacy joined with the path segment 'v1'.
        roots = [legacy/"v2", legacy/"v1"]
    # Iterate over roots, binding each item to candidate.
    for candidate in roots:
        # Run this branch when the negation of whether (candidate / 'manifest.json') exists.
        if not (candidate/"manifest.json").exists():
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set identity to the result of read_checked_manifest(candidate).
        identity = read_checked_manifest(candidate)
        # Run this branch when whether any item is true in a lazy sequence of the result of k.startswith(the text
        # 'panel_demo/') for k in identity['manifest'] at 'source_identities'.
        if any(k.startswith("panel_demo/") for k in identity["manifest"]["source_identities"]):
            # Set chosen_case to BY_ID at 'PV-04B' if case_id == 'PV-04' else case_id.
            chosen_case = BY_ID["PV-04B" if case_id=="PV-04" else case_id]
            # Set selected to a list of r for r in the result of records(candidate) plus the result of
            # records(candidate, the text 'preflight'); retain entries satisfying r at 'scenario_id' equals
            # chosen_case.scenario_id and r['run_id'] equals run_id when...
            selected = [r for r in records(candidate)+records(candidate,"preflight")
                # Evaluate r at 'scenario_id' equals chosen_case.scenario_id and r at 'run_id' equals run_id when
                # run_id, otherwise r['method'] equals method and r['suite'] equals 'panel' as part of the
                # enclosing expression.
                if r["scenario_id"]==chosen_case.scenario_id and
                # Evaluate r at 'run_id' equals run_id when run_id, otherwise r at 'method' equals method and r at
                # 'suite' equals the text 'panel' as part of the enclosing expression.
                (r["run_id"]==run_id if run_id else r["method"]==method and r["suite"]=="panel")]
            # Run this branch when the number of entries in selected equals 1.
            if len(selected)==1:
                # Import replay as archived_replay from historical_replay for the operations below.
                from historical_replay import replay as archived_replay
                # Return the result of archived_replay(candidate, selected[0] at 'run_id') to the caller.
                return archived_replay(candidate,selected[0]["run_id"],kind="targeted",gui=gui)
            # Run this branch when selected.
            if selected:
                # Raise RuntimeError with the text 'PANEL_REPLAY_SELECT_EXACT_RUN' to stop this execution path.
                raise RuntimeError("PANEL_REPLAY_SELECT_EXACT_RUN")
    # Run this branch when case_id equals the text 'PV-04'.
    if case_id == "PV-04":
        # Set case_id to the text 'PV-04B'.
        case_id = "PV-04B"
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)  # Refuse changed code/environment rather than silently replay new behavior.
    # Set case to BY_ID at case_id.
    case = BY_ID[case_id]
    # Run this branch when case_id equals the text 'PV-06'.
    if case_id == "PV-06":
        # Return the result of evaluate_faults() to the caller.
        return evaluate_faults()
    # Set all_records to the result of records(root) plus the result of records(root, the text 'preflight') plus
    # the result of records(root, the text 'panel_replay').
    all_records = records(root) + records(root, "preflight") + records(root, "panel_replay")
    # Set selected to a list of r for r in all_records; retain entries satisfying r at 'scenario_id' equals
    # case.scenario_id and r['run_id'] equals run_id when run_id,...
    selected = [r for r in all_records if r["scenario_id"] == case.scenario_id and
                # Evaluate r at 'run_id' equals run_id when run_id, otherwise r at 'method' equals method and r at
                # 'suite' equals the text 'panel' as part of the enclosing expression.
                (r["run_id"] == run_id if run_id else r["method"] == method and r["suite"] == "panel")]
    # Run this branch when the number of entries in selected differs from 1.
    if len(selected) != 1:
        # Raise RuntimeError with the text 'PANEL_REPLAY_SELECT_EXACT_RUN: no unique matching recorded...' to stop
        # this execution path.
        raise RuntimeError("PANEL_REPLAY_SELECT_EXACT_RUN: no unique matching recorded episode")
    # Set prior to selected at 0.
    prior = selected[0]
    # Set provenance to the decoded data produced by json.loads from the text read from (Path(root) / 'runs' /
    # prior['run_id'] / 'provenance.json').
    provenance = json.loads((Path(root) / "runs" / prior["run_id"] / "provenance.json").read_text())
    # Set expected to an integer built from digest((frozen['manifest']['protocol_id'], case.scenario_id, None,
    # prior['method'])) sliced by :16 modulo 2 raised to the power 31.
    expected = int(digest((frozen["manifest"]["protocol_id"], case.scenario_id, None, prior["method"]))[:16], 16) % (2**31)
    # Run this branch when provenance at 'policy_action_seed' differs from expected or prior at
    # 'policy_action_seed' differs from expected.
    if provenance["policy_action_seed"] != expected or prior["policy_action_seed"] != expected:
        # Raise RuntimeError with the text 'PANEL_REPLAY_ACTION_SEED_MISMATCH' to stop this execution path.
        raise RuntimeError("PANEL_REPLAY_ACTION_SEED_MISMATCH")
    # Return the result of execute(case, prior at 'method', frozen, root) to the caller.
    return execute(case, prior["method"], frozen, root, suite="panel_replay", gui=gui,
        # Supply replay_of as prior at 'run_id'.
        # Supply schedule as the result of restore_schedule(provenance at 'schedule').
        replay_of=prior["run_id"], schedule=restore_schedule(provenance["schedule"]))
