"""Thin guarded runtime wrapper; immutable one-attempt claims and resume."""
# Import json for use in this module.
import json
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
# Import restore_schedule, schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import restore_schedule, schedule_payload
# Import digest, write_json from post_training_evaluation.models for the operations below.
from post_training_evaluation.models import digest, write_json
# Import CASES, BY_ID from .cases for the operations below.
from .cases import CASES, BY_ID
# Import ROOT, PROTOCOL, prepare, records, classify from .models for the operations below.
from .models import ROOT, PROTOCOL, prepare, records, classify
# Import ScalabilityTelemetry from .metrics for the operations below.
from .metrics import ScalabilityTelemetry

# Persist using the inputs and processing steps below.
# Input directory: the supplied directory.
# Input value: the supplied value.
# Output: no explicit value; normal completion returns None.
def persist(directory, value):
    # Call write_json with the supplied arguments.
    write_json(directory/"study_result.json", value, exclusive=True)
    # Call write_json with the supplied arguments.
    write_json(directory/"study_result.sha256.json", dict(study_result_hash=digest(value)), exclusive=True)

# Execute using the inputs and processing steps below.
# Input case: the supplied case.
# Input frozen: the supplied frozen.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Input gui: the supplied gui.
# Input replay_of: the supplied replay of.
# Output: value.
# Processing: select branches using the stated conditions.
def execute(case, frozen, root=ROOT, *, suite="scalability", gui=False, replay_of=None):
    # Set entry to the next item from a lazy sequence of c for c in frozen['manifest'] at 'cases'; retain entries
    # satisfying c at 'case_id' equals case.case_id.
    entry = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == case.case_id)
    # Run this branch when entry at 'schedule' differs from the result of schedule_payload(the result of
    # case.schedule()) or entry at 'scenario' differs from the result of vars(the result of case.scenario()).
    if entry["schedule"] != schedule_payload(case.schedule()) or entry["scenario"] != vars(case.scenario()):
        # Raise RuntimeError with the text 'SCALABILITY_FROZEN_CASE_MISMATCH' to stop this execution path.
        raise RuntimeError("SCALABILITY_FROZEN_CASE_MISMATCH")
    # Set raw to the result of run_episode(the result of case.scenario(), None, the text 'PROPOSED_MAPPO',
    # frozen).
    raw = run_episode(case.scenario(), None, "PROPOSED_MAPPO", frozen, root=root, suite=suite,
        # Supply schedule as the result of restore_schedule(entry at 'schedule').
        # Supply gui as gui.
        # Supply replay_of as replay_of.
        schedule=restore_schedule(entry["schedule"]), gui=gui, replay_of=replay_of,
        # Supply observer_factory as the result of partial(ScalabilityTelemetry).
        observer_factory=partial(ScalabilityTelemetry,
            # Supply expected_sources as frozen['manifest'] at 'study_sources'.
            expected_sources=frozen["manifest"]["study_sources"],
            # Supply storage as frozen['manifest']['geometry'] at 'static_storage_vehicles_per_approach'.
            storage=frozen["manifest"]["geometry"]["static_storage_vehicles_per_approach"]),
        # Supply evidence_classification as PROTOCOL when suite equals the text 'scalability', otherwise the text
        # 'PREFLIGHT_NOT_SCIENTIFIC_RESULT' when suite equals the text 'preflight', otherwise the text
        # 'REPLAY_NOT_SCIENTIFIC_RESULT'.
        evidence_classification=PROTOCOL if suite == "scalability" else "PREFLIGHT_NOT_SCIENTIFIC_RESULT" if suite == "preflight" else "REPLAY_NOT_SCIENTIFIC_RESULT",
        # Declare rid as input parameter.
        replay_command_factory=lambda rid: f'& "{sys.executable}" -B run_scalability_validation.py --replay {case.case_id} --run-id {rid} --gui --output-root "{root}"')
    # Set value to a dictionary containing raw_result_hash, scenario_id, classification.
    value = {**raw, "raw_result_hash": digest(raw), "scenario_id":case.case_id,
        # Store the result of classify(raw at 'metrics', raw at 'integrity', raw at 'error') under
        # 'classification'.
        "classification": classify(raw["metrics"], raw["integrity"], raw["error"])}
    # Call persist with the supplied arguments.
    persist(Path(root)/"runs"/raw["run_id"], value)
    # Return value to the caller.
    return value

# Recover interruption using the inputs and processing steps below.
# Input case: the supplied case.
# Input root: the base directory used to resolve files.
# Input frozen: the supplied frozen.
# Output: value.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def recover_interruption(case, root, frozen):
    # Set claim to the decoded data produced by json.loads from the text read from (Path(root) / 'attempts' /
    # (case.case_id + '.json')).
    claim = json.loads((Path(root)/"attempts"/(case.case_id+".json")).read_text())
    # A fully persisted raw episode is recoverable without another SUMO launch.
    # Set candidates to an empty list.
    candidates = []
    # Import checked_json from .models for the operations below.
    from .models import checked_json
    # Iterate over the result of (Path(root) / 'runs').glob(the text '*/result.json'), binding each item to path.
    for path in (Path(root)/"runs").glob("*/result.json"):
        # Set raw to the result of checked_json(path, the text 'result_hash').
        raw = checked_json(path, "result_hash")
        # Run this branch when raw at 'suite' equals the text 'scalability' and raw at 'schedule_hash' equals the
        # result of digest(the result of schedule_payload(case.schedule())).
        if raw["suite"] == "scalability" and raw["schedule_hash"] == digest(schedule_payload(case.schedule())):
            # Append a tuple containing path.parent, raw to candidates.
            candidates.append((path.parent, raw))
    # Run this branch when the number of entries in candidates equals 1.
    if len(candidates) == 1:
        # Set (directory, raw) to candidates at 0.
        directory, raw = candidates[0]
        # Set value to a dictionary containing raw_result_hash, scenario_id, classification.
        value = {**raw, "raw_result_hash":digest(raw), "scenario_id":case.case_id,
                 # Store the result of classify(raw at 'metrics', raw at 'integrity', raw at 'error') under
                 # 'classification'.
                 "classification":classify(raw["metrics"],raw["integrity"],raw["error"])}
    # Run this branch when candidates.
    elif candidates:
        # Raise RuntimeError with the text 'AMBIGUOUS_INTERRUPTED_SCALABILITY_EVIDENCE' to stop this execution
        # path.
        raise RuntimeError("AMBIGUOUS_INTERRUPTED_SCALABILITY_EVIDENCE")
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set directory to the result of Path(root) joined with the path segment 'runs' joined with the path segment 'interrupted_'
        # plus case.case_id.
        directory = Path(root)/"runs"/("interrupted_"+case.case_id)
        # Set value to a dictionary built from the supplied values.
        value = dict(run_id=directory.name, suite="scalability", scenario_id=case.case_id,
            # Supply manifest_hash as frozen at 'manifest_hash'.
            # Supply classification as the text 'INVALID_EXPERIMENT'.
            manifest_hash=frozen["manifest_hash"], classification="INVALID_EXPERIMENT",
            # Store False under 'valid'.
            interrupted=True, metrics={}, integrity={"valid":False},
            # Supply evidence_classification as PROTOCOL.
            # Supply error as the text 'Interrupted attempt retained; no automatic retry.'.
            # Supply attempt as claim.
            evidence_classification=PROTOCOL, error="Interrupted attempt retained; no automatic retry.", attempt=claim)
    # Call persist with the supplied arguments.
    persist(directory, value)
    # Return value to the caller.
    return value

# Run using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: the result of report(root).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def run(root=ROOT):
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set done to a dictionary of r at 'scenario_id' mapped to r for r in the result of records(root).
    done = {r["scenario_id"]:r for r in records(root)}
    # Import report from .reporting for the operations below.
    from .reporting import report
    # Iterate over CASES, binding each item to case.
    for case in CASES:
        # Run this branch when case.case_id belongs to done.
        if case.case_id in done:
            # Display the text 'Reusing immutable'.
            print("Reusing immutable", case.case_id, flush=True)
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set claim to the result of Path(root) joined with the path segment 'attempts' divided by case.case_id plus the
        # text '.json'.
        claim = Path(root)/"attempts"/(case.case_id+".json")
        # Run this branch when whether claim exists.
        if claim.exists():
            # Set value to the result of recover_interruption(case, root, frozen).
            value = recover_interruption(case, root, frozen)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Call write_json with the supplied arguments.
            write_json(claim, dict(case_id=case.case_id, manifest_hash=frozen["manifest_hash"], policy="Exactly one attempt; interruption never triggers automatic re-execution."), exclusive=True)
            # Set value to the result of execute(case, frozen, root).
            value = execute(case, frozen, root)
        # Set m to value at 'metrics'.
        m = value["metrics"]
        # Display formatted text built from the embedded values.
        print(f'{case.case_id} {value["classification"]} completed={m.get("total_vehicles_completed", "N/A")}/{case.count} collisions={m.get("collision_count", "N/A")}', flush=True)
        # Call report with the supplied arguments.
        report(root)
    # Return the result of report(root) to the caller.
    return report(root)

# Preflight using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def preflight(root=ROOT):
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set path to the result of Path(root) joined with the path segment 'preflight/latest.json'.
    path = Path(root)/"preflight/latest.json"
    # Run this branch when whether path exists.
    if path.exists():
        # Display the text 'Reusing recorded preflight; not launching another episode.'.
        print("Reusing recorded preflight; not launching another episode.", flush=True)
        # Return the decoded data produced by json.loads from the text read from path to the caller.
        return json.loads(path.read_text())
    # Set start to the result of perf_counter().
    start = perf_counter()
    # Set value to the result of execute(CASES at 0, frozen, root).
    value = execute(CASES[0], frozen, root, suite="preflight")
    # Set elapsed to the result of perf_counter() minus start.
    elapsed = perf_counter()-start
    # Set observed to value['metrics'] at 'observed_simulation_time_seconds'.
    observed = value["metrics"]["observed_simulation_time_seconds"]
    # Set ratio to elapsed divided by observed when observed, otherwise None.
    ratio = elapsed/observed if observed else None
    # Use both measured plumbing and the preserved dense PV-04A runtime. Scale
    # conservatively by 40/16: dense observation is not a 40-vehicle benchmark.
    # Set reference_path to the result of Path(the text
    # 'results/panel_validation/v2/runs/20261008T175551068657Z_095c94...').
    reference_path = Path("results/panel_validation/v2/runs/20261008T175551068657Z_095c9470/result.json")
    # Set historical to None.
    historical = None
    # Run this branch when whether reference_path is an existing file.
    if reference_path.is_file():
        # Set old to the decoded data produced by json.loads from the text read from reference_path.
        old = json.loads(reference_path.read_text())
        # Set historical to a dictionary built from the supplied values.
        historical = dict(path=str(reference_path), wall_seconds=old["wall_clock_seconds"], simulated_seconds=old["metrics"]["observed_simulation_time_seconds"], workload_factor=40/16)
        # Set dense_ratio to historical at 'wall_seconds' divided by historical at 'simulated_seconds' multiplied
        # by historical at 'workload_factor'.
        dense_ratio = historical["wall_seconds"]/historical["simulated_seconds"] * historical["workload_factor"]
        # Set ratio to the maximum of ratio or 0.0, dense_ratio.
        ratio = max(ratio or 0., dense_ratio)
    # Set projected to ratio multiplied by frozen['manifest'] at 'maximum_simulated_seconds' when ratio, otherwise
    # None.
    projected = ratio*frozen["manifest"]["maximum_simulated_seconds"] if ratio else None
    # Set receipt to a dictionary built from the supplied values.
    receipt = dict(evidence_classification="PREFLIGHT_NOT_SCIENTIFIC_RESULT", run_id=value["run_id"],
        # Supply manifest_hash as frozen at 'manifest_hash'.
        # Supply wall_clock_seconds as elapsed.
        manifest_hash=frozen["manifest_hash"], wall_clock_seconds=elapsed,
        # Supply observed_simulated_seconds as observed.
        # Supply traffic_classification as value at 'classification'.
        # Supply integrity as value at 'integrity'.
        observed_simulated_seconds=observed, traffic_classification=value["classification"], integrity=value["integrity"],
        # Supply projected_full_budget_wall_seconds as projected.
        # Supply historical_dense_reference as historical.
        projected_full_budget_wall_seconds=projected, historical_dense_reference=historical,
        # Supply projection_method as the text 'Maximum of preflight wall/sim ratio and preserved PV-04A...'.
        projection_method="Maximum of preflight wall/sim ratio and preserved PV-04A wall/sim ratio * 40/16, multiplied by 1260 sim seconds. Conservative planning estimate, not a guarantee; ignores possible early stops.",
        # Supply automatic_run_allowed as projected is a different object from None and projected is at most 45
        # multiplied by 60 and value['integrity'] at 'valid'.
        # Supply full_study_started as False.
        automatic_run_allowed=projected is not None and projected <= 45*60 and value["integrity"]["valid"], full_study_started=False)
    # Call write_json with the supplied arguments.
    write_json(path, receipt, exclusive=True)
    # Import report from .reporting for the operations below.
    from .reporting import report
    # Call report with the supplied arguments.
    report(root)
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt, indent=2), flush=True)
    # Return receipt to the caller.
    return receipt

# Replay using the inputs and processing steps below.
# Input case_id: the supplied case id.
# Input root: the base directory used to resolve files.
# Input run_id: the supplied run id.
# Input gui: the supplied gui.
# Output: the result of execute(BY_ID at case_id, frozen, root).
# Processing: select branches using the stated conditions.
def replay(case_id, root=ROOT, *, run_id=None, gui=False):
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Set candidates to a list of r for r in the result of records(root) plus the result of records(root, the text
    # 'preflight'); retain entries satisfying r at 'scenario_id' equals case_id and r['run_id'] equals run_id when
    # run_id, otherwise...
    candidates = [r for r in records(root)+records(root,"preflight") if r["scenario_id"] == case_id and (r["run_id"] == run_id if run_id else r["suite"] == "scalability")]
    # Run this branch when the number of entries in candidates differs from 1 or 'interrupted' from candidates[0];
    # use None if absent.
    if len(candidates) != 1 or candidates[0].get("interrupted"):
        # Raise RuntimeError with the text 'SELECT_ONE_REPLAYABLE_RECORDED_RUN' to stop this execution path.
        raise RuntimeError("SELECT_ONE_REPLAYABLE_RECORDED_RUN")
    # Set prior to candidates at 0.
    prior = candidates[0]
    # Set expected to an integer built from digest((PROTOCOL, 'scalability_prefix_family', None,
    # 'PROPOSED_MAPPO')) sliced by :16 modulo 2 raised to the power 31.
    expected = int(digest((PROTOCOL,"scalability_prefix_family",None,"PROPOSED_MAPPO"))[:16],16)%(2**31)
    # Run this branch when prior at 'policy_action_seed' differs from expected.
    if prior["policy_action_seed"] != expected:
        # Raise RuntimeError with the text 'SCALABILITY_REPLAY_SEED_MISMATCH' to stop this execution path.
        raise RuntimeError("SCALABILITY_REPLAY_SEED_MISMATCH")
    # Return the result of execute(BY_ID at case_id, frozen, root) to the caller.
    return execute(BY_ID[case_id], frozen, root, suite="scalability_replay", replay_of=prior["run_id"], gui=gui)
