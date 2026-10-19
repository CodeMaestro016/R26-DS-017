"""Thin wrapper of post_training_evaluation.run_episode, never a vehicle controller."""
import json
import re
import sys
from functools import partial
from pathlib import Path
from time import perf_counter
from post_training_evaluation.runner import run_episode
from post_training_evaluation.scenarios import restore_schedule
from post_training_evaluation.faults import evaluate_faults
from post_training_evaluation.models import digest, write_json
from .cases import CASES, BY_ID
from .models import ROOT, V1_ROOT, EVIDENCE, prepare, records, read_checked_manifest
from .metrics import PanelTelemetry

def execute(case, method, frozen, root=ROOT, *, suite="panel", gui=False,
            replay_of=None, schedule=None):
    entry = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == case.case_id)
    if method not in entry["methods"] or case.budget_seconds != entry["budget_seconds"] or case.scenario_id != entry["scenario_id"]:
        raise RuntimeError("FROZEN_PANEL_CASE_MISMATCH")
    demand = restore_schedule(entry["schedule"]) if schedule is None else schedule
    if digest(entry["schedule"]) != digest({a: [vars(x) for x in rows] for a, rows in demand.items()}):
        raise RuntimeError("PANEL_REPLAY_DEMAND_MISMATCH")
    return run_episode(case.scenario(), None, method, frozen, root=root, suite=suite,
        schedule=demand, gui=gui, replay_of=replay_of,
        observer_factory=partial(PanelTelemetry, budget_seconds=case.budget_seconds,
            expected_panel_sources=frozen["manifest"]["panel_source_identities"]),
        evidence_classification=EVIDENCE if suite == "panel" else "PREFLIGHT_NOT_PANEL_CASE_EVIDENCE" if suite == "preflight" else "TARGETED_PANEL_VALIDATION_REPLAY",
        replay_command_factory=lambda rid: f'& "{sys.executable}" -B run_targeted_validation.py --replay {case.case_id} --run-id {rid} --gui --output-root "{Path(root)}"')

def faults(root, frozen, *, preflight=False):
    name = "preflight_faults.json" if preflight else "faults.json"
    path = Path(root) / name
    if path.exists():
        saved = json.loads(path.read_text())
        if saved["manifest_hash"] != frozen["manifest_hash"] or saved["checksum"] != digest(saved["tests"]):
            raise RuntimeError("PANEL_FAULT_EVIDENCE_MISMATCH")
        return saved
    tests = evaluate_faults()
    value = dict(case_id="PV-06", evidence_classification="PREFLIGHT_NOT_PANEL_CASE_EVIDENCE" if preflight else EVIDENCE,
        manifest_hash=frozen["manifest_hash"], tests=tests, checksum=digest(tests),
        classification="PASS" if all(t["passed"] for t in tests) else "UNSAFE_FAILURE",
        scope="Controlled current controller-interface fault checks; no SUMO episode, packet network or real V2V validation; traffic metrics N/A.")
    write_json(path, value, exclusive=True)
    return value

def preflight(root=ROOT):
    start = perf_counter()
    frozen = prepare(root)
    record = execute(BY_ID["PV-01"], "PROPOSED_MAPPO", frozen, root, suite="preflight")
    check = faults(root, frozen, preflight=True)
    wall = perf_counter() - start
    observed = record["metrics"]["observed_simulation_time_seconds"]
    # Conservative observed wall/sim ratio times the full budgets; no promised ETA.
    max_budget = frozen["manifest"]["maximum_simulated_seconds"]
    projected = record["wall_clock_seconds"] / observed * max_budget if observed > 0 else None
    historical = None
    old_log = Path("results/repair_diagnostics/component2_full_tests.log")
    if old_log.is_file():
        raw = old_log.read_bytes()
        text = raw.decode("utf-16" if raw.startswith(b"\xff\xfe") else "utf-8-sig")
        match = re.search(r"\d+ failed, \d+ passed in ([\d.]+)s", text)
        if match:
            historical = dict(source=str(old_log),
                reference="Earlier complete regression suite including a 360-s dense fixture; total test wall time is a conservative reference, not an isolated dense benchmark.",
                reference_wall_seconds=float(match.group(1)), reference_simulated_seconds=360.,
                full_budget_extrapolation_seconds=float(match.group(1)) / 360. * max_budget)
            projected = max(projected or 0., historical["full_budget_extrapolation_seconds"])
    value = dict(evidence_classification="PREFLIGHT_NOT_PANEL_CASE_EVIDENCE", manifest_hash=frozen["manifest_hash"],
        run_id=record["run_id"], wall_clock_seconds=wall, observed_simulated_seconds=observed,
        projected_full_budget_wall_seconds=projected,
        historical_runtime_reference=historical,
        projection_limit="One two-vehicle episode cannot predict dense per-step costs; this extrapolation excludes workload growth and does not promise wall time.",
        requires_runtime_review=projected is None or projected > 1800,
        runtime_integrity_valid=record["integrity"]["valid"], traffic_classification=record["classification"],
        fault_checks_passed=check["classification"] == "PASS", full_suite_automatically_started=False)
    directory = Path(root) / "preflight" / record["run_id"]
    write_json(directory / "preflight.json", value, exclusive=True)
    write_json(Path(root) / "preflight/latest.json", value)
    from .reporting import report
    report(root)
    print("PREFLIGHT:", json.dumps(value, indent=2), flush=True)
    return value

def run(root=ROOT):
    frozen = prepare(root)
    done = {(r["scenario_id"], r["method"]): r for r in records(root)}
    if len(done) != len(records(root)):
        raise RuntimeError("DUPLICATE_PANEL_EPISODES: results remain visible; select a new version rather than cherry-pick")
    for case in CASES:
        for method in case.methods:
            if (case.scenario_id, method) not in done:
                execute(case, method, frozen, root)
    faults(root, frozen)
    from .reporting import report, print_summary
    payload = report(root)
    print_summary(payload)
    return payload

def run_case(case_id, root=ROOT):
    """Execute a case once; never rerun for a favorable outcome."""
    frozen = prepare(root)
    case = BY_ID[case_id]
    done = {(r["scenario_id"], r["method"]) for r in records(root)}
    for method in case.methods:
        if (case.scenario_id, method) in done:
            raise RuntimeError("PANEL_CASE_ALREADY_RECORDED: use replay; do not replace results")
        execute(case, method, frozen, root)
    if case_id == "PV-06":
        faults(root, frozen)
    from .reporting import report, print_summary
    payload = report(root)
    print_summary(payload)
    return payload

def replay(case_id, root=ROOT, *, run_id=None, method="PROPOSED_MAPPO", gui=False):
    # Historical runs retain original source identity; renamed code is not
    # silently substituted for their measured implementation.
    legacy = Path("results/panel_validation")
    roots = [Path(root)]
    if Path(root).resolve() == ROOT.resolve() and not (Path(root)/"manifest.json").exists():
        roots = [legacy/"v2", legacy/"v1"]
    for candidate in roots:
        if not (candidate/"manifest.json").exists():
            continue
        identity = read_checked_manifest(candidate)
        if any(k.startswith("panel_demo/") for k in identity["manifest"]["source_identities"]):
            chosen_case = BY_ID["PV-04B" if case_id=="PV-04" else case_id]
            selected = [r for r in records(candidate)+records(candidate,"preflight")
                if r["scenario_id"]==chosen_case.scenario_id and
                (r["run_id"]==run_id if run_id else r["method"]==method and r["suite"]=="panel")]
            if len(selected)==1:
                from historical_replay import replay as archived_replay
                return archived_replay(candidate,selected[0]["run_id"],kind="targeted",gui=gui)
            if selected:
                raise RuntimeError("PANEL_REPLAY_SELECT_EXACT_RUN")
    if case_id == "PV-04":
        case_id = "PV-04B"
    frozen = prepare(root)  # Refuse changed code/environment rather than silently replay new behavior.
    case = BY_ID[case_id]
    if case_id == "PV-06":
        return evaluate_faults()
    all_records = records(root) + records(root, "preflight") + records(root, "panel_replay")
    selected = [r for r in all_records if r["scenario_id"] == case.scenario_id and
                (r["run_id"] == run_id if run_id else r["method"] == method and r["suite"] == "panel")]
    if len(selected) != 1:
        raise RuntimeError("PANEL_REPLAY_SELECT_EXACT_RUN: no unique matching recorded episode")
    prior = selected[0]
    provenance = json.loads((Path(root) / "runs" / prior["run_id"] / "provenance.json").read_text())
    expected = int(digest((frozen["manifest"]["protocol_id"], case.scenario_id, None, prior["method"]))[:16], 16) % (2**31)
    if provenance["policy_action_seed"] != expected or prior["policy_action_seed"] != expected:
        raise RuntimeError("PANEL_REPLAY_ACTION_SEED_MISMATCH")
    return execute(case, prior["method"], frozen, root, suite="panel_replay", gui=gui,
        replay_of=prior["run_id"], schedule=restore_schedule(provenance["schedule"]))
