"""Thin guarded runtime wrapper; immutable one-attempt claims and resume."""
import json
import sys
from functools import partial
from pathlib import Path
from time import perf_counter
from post_training_evaluation.runner import run_episode
from post_training_evaluation.scenarios import restore_schedule, schedule_payload
from post_training_evaluation.models import digest, write_json
from .cases import CASES, BY_ID
from .models import ROOT, PROTOCOL, prepare, records, classify
from .metrics import ScalabilityTelemetry

def persist(directory, value):
    write_json(directory/"study_result.json", value, exclusive=True)
    write_json(directory/"study_result.sha256.json", dict(study_result_hash=digest(value)), exclusive=True)

def execute(case, frozen, root=ROOT, *, suite="scalability", gui=False, replay_of=None):
    entry = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == case.case_id)
    if entry["schedule"] != schedule_payload(case.schedule()) or entry["scenario"] != vars(case.scenario()):
        raise RuntimeError("SCALABILITY_FROZEN_CASE_MISMATCH")
    raw = run_episode(case.scenario(), None, "PROPOSED_MAPPO", frozen, root=root, suite=suite,
        schedule=restore_schedule(entry["schedule"]), gui=gui, replay_of=replay_of,
        observer_factory=partial(ScalabilityTelemetry,
            expected_sources=frozen["manifest"]["study_sources"],
            storage=frozen["manifest"]["geometry"]["static_storage_vehicles_per_approach"]),
        evidence_classification=PROTOCOL if suite == "scalability" else "PREFLIGHT_NOT_SCIENTIFIC_RESULT" if suite == "preflight" else "REPLAY_NOT_SCIENTIFIC_RESULT",
        replay_command_factory=lambda rid: f'& "{sys.executable}" -B run_scalability_validation.py --replay {case.case_id} --run-id {rid} --gui --output-root "{root}"')
    value = {**raw, "raw_result_hash": digest(raw), "scenario_id":case.case_id,
        "classification": classify(raw["metrics"], raw["integrity"], raw["error"])}
    persist(Path(root)/"runs"/raw["run_id"], value)
    return value

def recover_interruption(case, root, frozen):
    claim = json.loads((Path(root)/"attempts"/(case.case_id+".json")).read_text())
    # A fully persisted raw episode is recoverable without another SUMO launch.
    candidates = []
    from .models import checked_json
    for path in (Path(root)/"runs").glob("*/result.json"):
        raw = checked_json(path, "result_hash")
        if raw["suite"] == "scalability" and raw["schedule_hash"] == digest(schedule_payload(case.schedule())):
            candidates.append((path.parent, raw))
    if len(candidates) == 1:
        directory, raw = candidates[0]
        value = {**raw, "raw_result_hash":digest(raw), "scenario_id":case.case_id,
                 "classification":classify(raw["metrics"],raw["integrity"],raw["error"])}
    elif candidates:
        raise RuntimeError("AMBIGUOUS_INTERRUPTED_SCALABILITY_EVIDENCE")
    else:
        directory = Path(root)/"runs"/("interrupted_"+case.case_id)
        value = dict(run_id=directory.name, suite="scalability", scenario_id=case.case_id,
            manifest_hash=frozen["manifest_hash"], classification="INVALID_EXPERIMENT",
            interrupted=True, metrics={}, integrity={"valid":False},
            evidence_classification=PROTOCOL, error="Interrupted attempt retained; no automatic retry.", attempt=claim)
    persist(directory, value)
    return value

def run(root=ROOT):
    frozen = prepare(root)
    done = {r["scenario_id"]:r for r in records(root)}
    from .reporting import report
    for case in CASES:
        if case.case_id in done:
            print("Reusing immutable", case.case_id, flush=True)
            continue
        claim = Path(root)/"attempts"/(case.case_id+".json")
        if claim.exists():
            value = recover_interruption(case, root, frozen)
        else:
            write_json(claim, dict(case_id=case.case_id, manifest_hash=frozen["manifest_hash"], policy="Exactly one attempt; interruption never triggers automatic re-execution."), exclusive=True)
            value = execute(case, frozen, root)
        m = value["metrics"]
        print(f'{case.case_id} {value["classification"]} completed={m.get("total_vehicles_completed", "N/A")}/{case.count} collisions={m.get("collision_count", "N/A")}', flush=True)
        report(root)
    return report(root)

def preflight(root=ROOT):
    frozen = prepare(root)
    path = Path(root)/"preflight/latest.json"
    if path.exists():
        print("Reusing recorded preflight; not launching another episode.", flush=True)
        return json.loads(path.read_text())
    start = perf_counter()
    value = execute(CASES[0], frozen, root, suite="preflight")
    elapsed = perf_counter()-start
    observed = value["metrics"]["observed_simulation_time_seconds"]
    ratio = elapsed/observed if observed else None
    # Use both measured plumbing and the preserved dense PV-04A runtime. Scale
    # conservatively by 40/16: dense observation is not a 40-vehicle benchmark.
    reference_path = Path("results/panel_validation/v2/runs/20261008T175551068657Z_095c9470/result.json")
    historical = None
    if reference_path.is_file():
        old = json.loads(reference_path.read_text())
        historical = dict(path=str(reference_path), wall_seconds=old["wall_clock_seconds"], simulated_seconds=old["metrics"]["observed_simulation_time_seconds"], workload_factor=40/16)
        dense_ratio = historical["wall_seconds"]/historical["simulated_seconds"] * historical["workload_factor"]
        ratio = max(ratio or 0., dense_ratio)
    projected = ratio*frozen["manifest"]["maximum_simulated_seconds"] if ratio else None
    receipt = dict(evidence_classification="PREFLIGHT_NOT_SCIENTIFIC_RESULT", run_id=value["run_id"],
        manifest_hash=frozen["manifest_hash"], wall_clock_seconds=elapsed,
        observed_simulated_seconds=observed, traffic_classification=value["classification"], integrity=value["integrity"],
        projected_full_budget_wall_seconds=projected, historical_dense_reference=historical,
        projection_method="Maximum of preflight wall/sim ratio and preserved PV-04A wall/sim ratio * 40/16, multiplied by 1260 sim seconds. Conservative planning estimate, not a guarantee; ignores possible early stops.",
        automatic_run_allowed=projected is not None and projected <= 45*60 and value["integrity"]["valid"], full_study_started=False)
    write_json(path, receipt, exclusive=True)
    from .reporting import report
    report(root)
    print(json.dumps(receipt, indent=2), flush=True)
    return receipt

def replay(case_id, root=ROOT, *, run_id=None, gui=False):
    frozen = prepare(root)
    candidates = [r for r in records(root)+records(root,"preflight") if r["scenario_id"] == case_id and (r["run_id"] == run_id if run_id else r["suite"] == "scalability")]
    if len(candidates) != 1 or candidates[0].get("interrupted"):
        raise RuntimeError("SELECT_ONE_REPLAYABLE_RECORDED_RUN")
    prior = candidates[0]
    expected = int(digest((PROTOCOL,"scalability_prefix_family",None,"PROPOSED_MAPPO"))[:16],16)%(2**31)
    if prior["policy_action_seed"] != expected:
        raise RuntimeError("SCALABILITY_REPLAY_SEED_MISMATCH")
    return execute(BY_ID[case_id], frozen, root, suite="scalability_replay", replay_of=prior["run_id"], gui=gui)
