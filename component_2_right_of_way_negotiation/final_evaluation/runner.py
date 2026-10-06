"""Quantitative wrapper around the existing single SUMO control loop."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import contextlib
import json
import platform
import sys
from time import perf_counter
from functools import partial
from environment import SUMOEnv

from panel_demo.runner import run_panel_demo
from panel_demo.inference import PanelDeterministicInferenceProvider
from .baselines import FCFSProvider, RulesOnlyProvider
from .integrity import IntegrityGuard
from .metrics import Telemetry
from .models import ROOT, METHODS, SEEDS, classify, digest, write_json, finite, normalize_nonfinite
from .scenarios import SCENARIOS, CONTINUOUS, FUNCTIONAL, demand, schedule_payload, prepare, source_identities, SMOKE_BUDGET_SECONDS

def run_episode(scenario, seed, method, frozen, *, root=ROOT, suite="final", gui=False,
                schedule=None, replay_of=None):
    if method not in METHODS:
        raise ValueError("UNKNOWN_EVALUATION_METHOD")
    schedule = demand(scenario, seed) if schedule is None else schedule
    payload = schedule_payload(schedule)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    directory = Path(root) / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    provenance = {"run_id": run_id, "suite": suite, "scenario": asdict(scenario),
        "seed": seed, "method": method, "schedule": payload, "schedule_hash": digest(payload),
        "manifest_hash": frozen["manifest_hash"], "policy_sha256": frozen["manifest"]["policy_sha256"],
        "sumo_version": frozen["manifest"]["sumo_version"],
        "configuration_identities": frozen["manifest"]["source_identities"],
        "replay_of": replay_of,
        "sumo_options": {"time_to_teleport": -1, "seed": 0},
        "hardware": {"platform": platform.platform(), "processor": platform.processor(),
                     "python": platform.python_version()},
        "replay_command": f'& "{sys.executable}" -B run_final_evaluation.py --replay {run_id} --gui' + (
            f' --output-root "{Path(root)}"' if Path(root) != ROOT else "")}
    write_json(directory / "provenance.json", provenance, exclusive=True)
    write_json(directory / "provenance.sha256.json", {"provenance_hash": digest(provenance)}, exclusive=True)
    sources_before_match = source_identities() == frozen["manifest"]["source_identities"]
    observer = Telemetry(schedule, proposed=method == "PROPOSED_MAPPO")
    guard = IntegrityGuard()
    def factory(bundle):
        guard.bind(bundle)
        if method == "PROPOSED_MAPPO":
            return PanelDeterministicInferenceProvider(bundle, sampling_seed=0)
        cls = FCFSProvider if method == "RULE_PLUS_FCFS" else RulesOnlyProvider
        return cls(bundle, observer.arrivals)
    runtime = {}
    error = None
    start = perf_counter()
    with (directory / "runtime.log").open("w", encoding="utf-8") as log:
        try:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                runtime = run_panel_demo(duration_seconds=scenario.budget_seconds,
                    use_gui=gui, schedule=schedule, scenario_id=scenario.scenario_id,
                    admission_mode="INDEPENDENT_DEMAND", provider_factory=factory,
                    runtime_observer=observer, persist_presentation=False,
                    environment_factory=partial(SUMOEnv, extra_options=(
                        "--time-to-teleport", "-1", "--seed", "0", "--error-log",
                        str((directory / "sumo_warnings.log").resolve()))),
                    return_failed_result=True)
            error = runtime.get("runtime_error")
        except Exception as exc:
            error = repr(exc)
        finally:
            integrity = guard.finish(runtime)
    integrity["frozen_sources_unchanged"] = sources_before_match and source_identities() == frozen["manifest"]["source_identities"]
    integrity["valid"] = integrity["valid"] and integrity["frozen_sources_unchanged"]
    if error and ("SCOPE_BOUNDARY" in error or "INTEGRITY_BREACH" in error):
        integrity["valid"] = False
    metrics = observer.result(runtime, aborted=bool(error))
    classification = classify(metrics, integrity, error)
    if not finite(metrics):
        error = "NON_FINITE_METRICS"
        integrity["valid"] = False
        metrics = normalize_nonfinite(metrics)
    result = {"run_id": run_id, "suite": suite, "evidence_classification": (
        "SMOKE_NOT_FINAL" if suite == "smoke" else "REPLAY_NOT_FINAL" if replay_of else
        "FINAL_POST_TRAINING_SYSTEM_EVALUATION"),
        "method": method, "scenario_id": scenario.scenario_id, "seed": seed,
        "manifest_hash": frozen["manifest_hash"], "schedule_hash": digest(payload),
        "classification": classification, "error": error, "integrity": integrity,
        "metrics": metrics, "wall_clock_seconds": perf_counter() - start,
        "replay_command": provenance["replay_command"],
        "runtime_events": runtime.get("events", []),
        "actual_departure_seconds": runtime.get("actual_departure_seconds", {}),
        "insertion_delay_seconds": runtime.get("insertion_delay_seconds", {})}
    write_json(directory / "result.json", result, exclusive=True)
    write_json(directory / "result.sha256.json", {"result_hash": digest(result)}, exclusive=True)
    print(f"{run_id} {method} {scenario.scenario_id} seed={seed} {classification} "
          f"completed={metrics['total_vehicles_completed']}/{metrics['total_vehicles_scheduled']}", flush=True)
    return result

def run_suite(suite, root=ROOT):
    frozen = prepare(root)
    if suite not in {"smoke", "final"}:
        raise ValueError("UNKNOWN_SUITE")
    # Smoke: fixed sanity + fixed cycle + one normal demand seed, all methods.
    cases = ((FUNCTIONAL[0], None), (FUNCTIONAL[1], None), (CONTINUOUS[0], SEEDS[0])) if suite == "smoke" else tuple(
        (s, seed) for s in SCENARIOS for seed in (SEEDS if s.continuous else (None,)))
    from .aggregation import load_runs
    existing = load_runs(root, frozen, suite)
    done = {(r["scenario_id"], r["seed"], r["method"]) for r in existing}
    for scenario, seed in cases:
        if suite == "smoke":
            scenario = replace(scenario, budget_seconds=SMOKE_BUDGET_SECONDS)
        shared_demand = demand(scenario, seed)
        for method in METHODS:
            if (scenario.scenario_id, seed, method) in done:
                print("Reusing immutable recorded episode:", scenario.scenario_id, seed, method)
                continue
            run_episode(scenario, seed, method, frozen, root=root, suite=suite,
                        schedule=shared_demand)
    from .faults import evaluate_faults
    from .reporting import report
    faults = evaluate_faults()
    write_json(Path(root) / "fault_tests.json", {"manifest_hash": frozen["manifest_hash"], "tests": faults})
    return report(root, suite=suite)
