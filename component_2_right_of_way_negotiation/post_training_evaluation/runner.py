"""Quantitative wrapper around the existing single SUMO control loop."""
# Import asdict, replace from dataclasses for the operations below.
from dataclasses import asdict, replace
# Import datetime, timezone from datetime for the operations below.
from datetime import datetime, timezone
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import uuid4 from uuid for the operations below.
from uuid import uuid4
# Import contextlib for use in this module.
import contextlib
# Import json for use in this module.
import json
# Import platform for use in this module.
import platform
# Import sys for use in this module.
import sys
# Import perf_counter from time for the operations below.
from time import perf_counter
# Import partial from functools for the operations below.
from functools import partial
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv

# Import run_runtime_simulation from runtime_simulation.runner for the operations below.
from runtime_simulation.runner import run_runtime_simulation
# Import ScientificEvaluationProvider, SCIENTIFIC_SELECTION_RULE from .inference for the operations below.
from .inference import ScientificEvaluationProvider, SCIENTIFIC_SELECTION_RULE
# Import FCFSProvider, RulesOnlyProvider from .baselines for the operations below.
from .baselines import FCFSProvider, RulesOnlyProvider
# Import IntegrityGuard from .integrity for the operations below.
from .integrity import IntegrityGuard
# Import Telemetry from .metrics for the operations below.
from .metrics import Telemetry
# Import ROOT, METHODS, SEEDS, classify, digest, write_json, finite, normalize_nonfinite, file_hash,
# CONTROLLER_VERSION, SHIELD_VERSION from .models for the operations below.
from .models import ROOT, METHODS, SEEDS, classify, digest, write_json, finite, normalize_nonfinite, file_hash, CONTROLLER_VERSION, SHIELD_VERSION
# Import SCENARIOS, CONTINUOUS, FUNCTIONAL, demand, schedule_payload, prepare, source_identities,
# SMOKE_BUDGET_SECONDS from .scenarios for the operations below.
from .scenarios import SCENARIOS, CONTINUOUS, FUNCTIONAL, demand, schedule_payload, prepare, source_identities, SMOKE_BUDGET_SECONDS

# Run episode using the inputs and processing steps below.
# Input scenario: the supplied scenario.
# Input seed: the random seed supplied to this operation.
# Input method: the supplied method.
# Input frozen: the supplied frozen.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Input gui: the supplied gui.
# Input schedule: the supplied schedule.
# Input replay_of: the supplied replay of.
# Input observer_factory: the supplied observer factory.
# Input evidence_classification: the supplied evidence classification.
# Input replay_command_factory: the supplied replay command factory.
# Output: result.
# Processing: select branches using the stated conditions, then handle the specified errors.
def run_episode(scenario, seed, method, frozen, *, root=ROOT, suite="final", gui=False,
                # Declare schedule, replay_of, observer_factory as input parameters.
                schedule=None, replay_of=None, observer_factory=Telemetry,
                # Declare evidence_classification, replay_command_factory as input parameters.
                evidence_classification=None, replay_command_factory=None):
    # Import protect_v1 from .models for the operations below.
    from .models import protect_v1
    # Call protect_v1 with the supplied arguments.
    protect_v1(root)
    # Run this branch when method does not belong to METHODS.
    if method not in METHODS:
        # Raise ValueError with the text 'UNKNOWN_EVALUATION_METHOD' to stop this execution path.
        raise ValueError("UNKNOWN_EVALUATION_METHOD")
    # Set schedule to the result of demand(scenario, seed) when schedule is the same object as None, otherwise
    # schedule.
    schedule = demand(scenario, seed) if schedule is None else schedule
    # Set payload to the result of schedule_payload(schedule).
    payload = schedule_payload(schedule)
    # Set action_seed to an integer built from digest((frozen['manifest']['protocol_id'], scenario.scenario_id,
    # seed, method)) sliced by :16 modulo 2 raised to the power 31.
    action_seed = int(digest((frozen["manifest"]["protocol_id"], scenario.scenario_id,
        # Include method in this tuple.
        seed, method))[:16], 16) % (2**31)
    # Set run_id to the result of datetime.now(timezone.utc).strftime(the text '%Y%m%dT%H%M%S%fZ') plus the text
    # '_' plus uuid4().hex sliced by :8.
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    # Set directory to the result of Path(root) joined with the path segment 'runs' divided by run_id.
    directory = Path(root) / "runs" / run_id
    # Create the directory requested by directory.
    directory.mkdir(parents=True, exist_ok=False)
    # Set provenance to a dictionary containing run_id, suite, scenario, seed, method, schedule, schedule_hash,
    # manifest_hash,...
    provenance = {"run_id": run_id, "suite": suite, "scenario": asdict(scenario),
        # Store seed under 'seed'.
        # Store method under 'method'.
        # Store payload under 'schedule'.
        # Store the result of digest(payload) under 'schedule_hash'.
        "seed": seed, "method": method, "schedule": payload, "schedule_hash": digest(payload),
        # Store frozen at 'manifest_hash' under 'manifest_hash'.
        # Store frozen['manifest'] at 'policy_sha256' under 'policy_sha256'.
        "manifest_hash": frozen["manifest_hash"], "policy_sha256": frozen["manifest"]["policy_sha256"],
        # Store frozen['manifest'] at 'sumo_version' under 'sumo_version'.
        "sumo_version": frozen["manifest"]["sumo_version"],
        # Store frozen['manifest'] at 'source_identities' under 'configuration_identities'.
        "configuration_identities": frozen["manifest"]["source_identities"],
        # Store replay_of under 'replay_of'.
        "replay_of": replay_of,
        # Store action_seed under 'policy_action_seed'.
        "policy_action_seed": action_seed,
        # Store SCIENTIFIC_SELECTION_RULE when method equals the text 'PROPOSED_MAPPO', otherwise the text
        # 'DETERMINISTIC_BASELINE' under 'inference_mode'.
        "inference_mode": SCIENTIFIC_SELECTION_RULE if method == "PROPOSED_MAPPO" else "DETERMINISTIC_BASELINE",
        # Store CONTROLLER_VERSION under 'controller_version'.
        # Store SHIELD_VERSION under 'shield_version'.
        "controller_version": CONTROLLER_VERSION, "shield_version": SHIELD_VERSION,
        # Store a dictionary containing time_to_teleport, seed under 'sumo_options'.
        # Store the negative of 1 under 'time_to_teleport'.
        # Store 0 under 'seed'.
        "sumo_options": {"time_to_teleport": -1, "seed": 0},
        # Store a dictionary containing platform, processor, python under 'hardware'.
        # Store the result of platform.platform() under 'platform'.
        # Store the result of platform.processor() under 'processor'.
        "hardware": {"platform": platform.platform(), "processor": platform.processor(),
                     # Store the result of platform.python_version() under 'python'.
                     "python": platform.python_version()},
        # Store formatted text built from the embedded values plus formatted text built from the embedded values
        # when the result of Path(root) differs from ROOT, otherwise the text '' under 'replay_command'.
        "replay_command": f'& "{sys.executable}" -B run_post_training_evaluation.py --replay {run_id} --gui' + (
            # Evaluate formatted text built from the embedded values when the result of Path(root) differs from
            # ROOT, otherwise the text '' as part of the enclosing expression.
            f' --output-root "{Path(root)}"' if Path(root) != ROOT else "")}
    # Run this branch when replay_command_factory is a different object from None.
    if replay_command_factory is not None:
        # Set provenance['replay_command'] to the result of replay_command_factory(run_id).
        provenance["replay_command"] = replay_command_factory(run_id)
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.json", provenance, exclusive=True)
    # Call write_json with the supplied arguments.
    write_json(directory / "provenance.sha256.json", {"provenance_hash": digest(provenance)}, exclusive=True)
    # Set sources_before_match to the result of source_identities() equals frozen['manifest'] at
    # 'source_identities'.
    sources_before_match = source_identities() == frozen["manifest"]["source_identities"]
    # Set observer to the result of observer_factory(schedule).
    observer = observer_factory(schedule, proposed=method == "PROPOSED_MAPPO")
    # Set observer.trace_path to directory joined with the path segment 'execution_trace.jsonl'.
    observer.trace_path = directory / "execution_trace.jsonl"
    # Set guard to the result of IntegrityGuard().
    guard = IntegrityGuard()
    # Factory using the inputs and processing steps below.
    # Input bundle: the supplied bundle.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def factory(bundle):
        # Call guard.bind with the supplied arguments.
        guard.bind(bundle)
        # Run this branch when method equals the text 'PROPOSED_MAPPO'.
        if method == "PROPOSED_MAPPO":
            # Return the result of ScientificEvaluationProvider(bundle) to the caller.
            return ScientificEvaluationProvider(bundle, sampling_seed=action_seed)
        # Set cls to FCFSProvider when method equals the text 'RULE_PLUS_FCFS', otherwise RulesOnlyProvider.
        cls = FCFSProvider if method == "RULE_PLUS_FCFS" else RulesOnlyProvider
        # Return the result of cls(bundle, observer.arrivals) to the caller.
        return cls(bundle, observer.arrivals)
    # Set runtime to an empty dictionary.
    runtime = {}
    # Set error to None.
    error = None
    # Set start to the result of perf_counter().
    start = perf_counter()
    # Enter the result of (directory / 'runtime.log').open(the text 'w') as log and run the enclosed operations
    # within that context.
    with (directory / "runtime.log").open("w", encoding="utf-8") as log:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Enter the result of contextlib.redirect_stdout(log); the result of contextlib.redirect_stderr(log)
            # and run the enclosed operations within that context.
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                # Set runtime to the result of run_runtime_simulation().
                runtime = run_runtime_simulation(duration_seconds=scenario.budget_seconds,
                    # Supply use_gui as gui.
                    # Supply schedule as schedule.
                    # Supply scenario_id as scenario.scenario_id.
                    use_gui=gui, schedule=schedule, scenario_id=scenario.scenario_id,
                    # Supply admission_mode as the text 'INDEPENDENT_DEMAND'.
                    # Supply provider_factory as factory.
                    admission_mode="INDEPENDENT_DEMAND", provider_factory=factory,
                    # Supply runtime_observer as observer.
                    # Supply persist_presentation as False.
                    runtime_observer=observer, persist_presentation=False,
                    # Supply environment_factory as the result of partial(SUMOEnv).
                    # Supply extra_options as a tuple containing the text '--time-to-teleport', the text '-1', the
                    # text '--seed', the text '0', the text '--error-log', a...
                    environment_factory=partial(SUMOEnv, extra_options=(
                        "--time-to-teleport", "-1", "--seed", "0", "--error-log",
                        # Include a string built from the result of (directory / 'sumo_warnings.log').resolve() in
                        # this tuple.
                        str((directory / "sumo_warnings.log").resolve()))),
                    # Supply return_failed_result as True.
                    return_failed_result=True)
            # Set error to 'runtime_error' from runtime; use None if absent.
            error = runtime.get("runtime_error")
        # Handle Exception as exc using the recovery steps below.
        except Exception as exc:
            # Set error to the result of repr(exc).
            error = repr(exc)
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Run this branch when whether observer exposes the requested attribute.
            if hasattr(observer, "finalize_runtime"):
                # Set (runtime, error) to the result of observer.finalize_runtime(runtime, error).
                runtime, error = observer.finalize_runtime(runtime, error)
            # Set integrity to the result of guard.finish(runtime).
            integrity = guard.finish(runtime)
    # Set integrity['frozen_sources_unchanged'] to sources_before_match and the result of source_identities()
    # equals frozen['manifest'] at 'source_identities'.
    integrity["frozen_sources_unchanged"] = sources_before_match and source_identities() == frozen["manifest"]["source_identities"]
    # Set integrity['valid'] to integrity at 'valid' and integrity at 'frozen_sources_unchanged'.
    integrity["valid"] = integrity["valid"] and integrity["frozen_sources_unchanged"]
    # Run this branch when error and the text 'SCOPE_BOUNDARY' belongs to error or the text 'INTEGRITY_BREACH'
    # belongs to error.
    if error and ("SCOPE_BOUNDARY" in error or "INTEGRITY_BREACH" in error):
        # Set integrity['valid'] to False.
        integrity["valid"] = False
    # Set metrics to the result of observer.result(runtime).
    metrics = observer.result(runtime, aborted=bool(error))
    # Set classification to the result of classify(metrics, integrity, error).
    classification = classify(metrics, integrity, error)
    # Run this branch when the negation of the result of finite(metrics).
    if not finite(metrics):
        # Set error to the text 'NON_FINITE_METRICS'.
        error = "NON_FINITE_METRICS"
        # Set integrity['valid'] to False.
        integrity["valid"] = False
        # Set metrics to the result of normalize_nonfinite(metrics).
        metrics = normalize_nonfinite(metrics)
    # Set result to a dictionary containing run_id, suite, evidence_classification, method, scenario_id, seed,
    # policy_action_seed,...
    result = {"run_id": run_id, "suite": suite, "evidence_classification": evidence_classification or (
        # Evaluate the text 'REGRESSION_DIAGNOSTIC_NOT_FINAL' when suite equals the text 'diagnostic', otherwise
        # the text 'SMOKE_NOT_FINAL' when suite equals the text 'smoke', otherwise the text 'REPLAY_NOT_FINAL'
        # when replay_of, otherwise the text 'FINAL_POST_TRAINING_SYSTEM_EVALUATION' as part of the enclosing
        # expression.
        "REGRESSION_DIAGNOSTIC_NOT_FINAL" if suite == "diagnostic" else "SMOKE_NOT_FINAL" if suite == "smoke" else "REPLAY_NOT_FINAL" if replay_of else
        "FINAL_POST_TRAINING_SYSTEM_EVALUATION"),
        # Store method under 'method'.
        # Store scenario.scenario_id under 'scenario_id'.
        # Store seed under 'seed'.
        "method": method, "scenario_id": scenario.scenario_id, "seed": seed,
        # Store action_seed under 'policy_action_seed'.
        "policy_action_seed": action_seed,
        # Store provenance at 'inference_mode' under 'inference_mode'.
        "inference_mode": provenance["inference_mode"],
        # Store CONTROLLER_VERSION under 'controller_version'.
        # Store SHIELD_VERSION under 'shield_version'.
        "controller_version": CONTROLLER_VERSION, "shield_version": SHIELD_VERSION,
        # Store frozen at 'manifest_hash' under 'manifest_hash'.
        # Store the result of digest(payload) under 'schedule_hash'.
        "manifest_hash": frozen["manifest_hash"], "schedule_hash": digest(payload),
        # Store classification under 'classification'.
        # Store error under 'error'.
        # Store integrity under 'integrity'.
        "classification": classification, "error": error, "integrity": integrity,
        # Store metrics under 'metrics'.
        # Store the result of perf_counter() minus start under 'wall_clock_seconds'.
        "metrics": metrics, "wall_clock_seconds": perf_counter() - start,
        # Store provenance at 'replay_command' under 'replay_command'.
        "replay_command": provenance["replay_command"],
        # Store 'events' from runtime; use an empty list if absent under 'runtime_events'.
        "runtime_events": runtime.get("events", []),
        # Store 'actual_departure_seconds' from runtime; use an empty dictionary if absent under
        # 'actual_departure_seconds'.
        "actual_departure_seconds": runtime.get("actual_departure_seconds", {}),
        # Store 'insertion_delay_seconds' from runtime; use an empty dictionary if absent under
        # 'insertion_delay_seconds'.
        "insertion_delay_seconds": runtime.get("insertion_delay_seconds", {})}
    # Run this branch when whether observer exposes the requested attribute.
    if hasattr(observer, "termination_reason"):
        # Set result['termination_reason'] to observer.termination_reason.
        result["termination_reason"] = observer.termination_reason
    # Set result['artifact_sha256'] to a dictionary of p.name mapped to the result of file_hash(p) for p in the
    # result of directory.iterdir(); retain entries satisfying p.name belongs to a set containing the text
    # 'execution_trace.jsonl', the text...
    result["artifact_sha256"] = {p.name: file_hash(p) for p in directory.iterdir()
        # Evaluate p.name belongs to a set containing the text 'execution_trace.jsonl', the text 'runtime.log',
        # the text 'sumo_warnings.log' as part of the enclosing expression.
        if p.name in {"execution_trace.jsonl", "runtime.log", "sumo_warnings.log"}}
    # Call write_json with the supplied arguments.
    write_json(directory / "result.json", result, exclusive=True)
    # Call write_json with the supplied arguments.
    write_json(directory / "result.sha256.json", {"result_hash": digest(result)}, exclusive=True)
    # Display formatted text built from the embedded values.
    print(f"{run_id} {method} {scenario.scenario_id} seed={seed} {classification} "
          # Supply flush as True.
          f"completed={metrics['total_vehicles_completed']}/{metrics['total_vehicles_scheduled']}", flush=True)
    # Return result to the caller.
    return result

# Run suite using the inputs and processing steps below.
# Input suite: the supplied suite.
# Input root: the base directory used to resolve files.
# Output: the result of report(root).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def run_suite(suite, root=ROOT):
    # Run this branch when the negation of whether (Path(root) / 'manifest.json') is an existing file.
    if not (Path(root) / "manifest.json").is_file():
        # Raise RuntimeError with the text 'V2_MANIFEST_NOT_FROZEN: review diagnostics, then explicitly...' to
        # stop this execution path.
        raise RuntimeError("V2_MANIFEST_NOT_FROZEN: review diagnostics, then explicitly use --prepare")
    # Set frozen to the result of prepare(root).
    frozen = prepare(root)
    # Run this branch when suite does not belong to a set containing the text 'smoke', the text 'final'.
    if suite not in {"smoke", "final"}:
        # Raise ValueError with the text 'UNKNOWN_SUITE' to stop this execution path.
        raise ValueError("UNKNOWN_SUITE")
    # Smoke: fixed sanity + fixed cycle + one normal demand seed, all methods.
    # Set cases to a tuple containing a tuple containing FUNCTIONAL at 0, None, a tuple containing FUNCTIONAL at
    # 1, None, a tuple containing... when suite equals the text 'smoke', otherwise a tuple built from a lazy
    # sequence of a tuple containing s, seed for s in SCENARIOS.
    cases = ((FUNCTIONAL[0], None), (FUNCTIONAL[1], None), (CONTINUOUS[0], SEEDS[0])) if suite == "smoke" else tuple(
        # Evaluate SEEDS when s.continuous, otherwise a tuple containing None as part of the enclosing expression.
        (s, seed) for s in SCENARIOS for seed in (SEEDS if s.continuous else (None,)))
    # Import load_runs from .aggregation for the operations below.
    from .aggregation import load_runs
    # Set existing to the result of load_runs(root, frozen, suite).
    existing = load_runs(root, frozen, suite)
    # Set done to a set of a tuple containing r at 'scenario_id', r at 'seed', r at 'method' for r in existing.
    done = {(r["scenario_id"], r["seed"], r["method"]) for r in existing}
    # Iterate over cases, binding each item to (scenario, seed).
    for scenario, seed in cases:
        # Run this branch when suite equals the text 'smoke'.
        if suite == "smoke":
            # Set scenario to the result of replace(scenario).
            scenario = replace(scenario, budget_seconds=SMOKE_BUDGET_SECONDS)
        # Set shared_demand to the result of demand(scenario, seed).
        shared_demand = demand(scenario, seed)
        # Iterate over METHODS, binding each item to method.
        for method in METHODS:
            # Run this branch when a tuple containing scenario.scenario_id, seed, method belongs to done.
            if (scenario.scenario_id, seed, method) in done:
                # Display the text 'Reusing immutable recorded episode:'.
                print("Reusing immutable recorded episode:", scenario.scenario_id, seed, method)
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Call run_episode with the supplied arguments.
            run_episode(scenario, seed, method, frozen, root=root, suite=suite,
                        # Supply schedule as shared_demand.
                        schedule=shared_demand)
    # Import evaluate_faults from .faults for the operations below.
    from .faults import evaluate_faults
    # Import report from .reporting for the operations below.
    from .reporting import report
    # Set faults to the result of evaluate_faults().
    faults = evaluate_faults()
    # Call write_json with the supplied arguments.
    write_json(Path(root) / "fault_tests.json", {"manifest_hash": frozen["manifest_hash"], "tests": faults})
    # Return the result of report(root) to the caller.
    return report(root, suite=suite)
