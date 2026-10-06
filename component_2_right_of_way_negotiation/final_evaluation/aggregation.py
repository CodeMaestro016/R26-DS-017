"""Reproducible descriptive and paired statistics; no hypothesis tests."""
from collections import Counter
from statistics import mean, median, stdev
from pathlib import Path
import json
import random
import numpy as np
from .models import digest, finite, METHODS, SEEDS
from .scenarios import SCENARIOS

METRICS = ("collision_count", "blocked_zone_violation_count", "unsafe_episode",
    "total_team_travel_time_seconds", "mean_travel_time_seconds", "median_travel_time_seconds",
    "p95_travel_time_seconds", "maximum_travel_time_seconds", "throughput_vehicles_per_minute",
    "completion_rate", "mean_waiting_time_seconds", "median_waiting_time_seconds",
    "p95_waiting_time_seconds", "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds",
    "conflicting_pair_fcfs_inversion_rate", "maximum_simultaneous_active_vehicles",
    "maximum_simultaneously_moving_vehicles", "maximum_negotiation_participants",
    "negotiation_events", "mappo_decision_epochs", "rule_resolved_events", "safe_hold_activations",
    "native_emergency_braking_events", "native_emergency_stop_events",
    "mappo_inference_mean_ms", "mappo_inference_median_ms", "mappo_inference_p95_ms",
    "mappo_inference_maximum_ms", "mappo_inference_fraction_exceeding_40ms",
    "ego_execution_mean_ms", "ego_execution_p95_ms")

def summary(values):
    values = [float(x) for x in values if x is not None]
    if not values:
        return {"n": 0, "mean": None, "median": None, "standard_deviation": None, "ci95": None}
    ci = None
    if len(values) > 1:
        rng = random.Random(260826)
        samples = [mean(rng.choices(values, k=len(values))) for _ in range(2000)]
        ci = list(np.percentile(samples, [2.5, 97.5], method="linear"))
    return {"n": len(values), "mean": mean(values), "median": median(values),
        "standard_deviation": stdev(values) if len(values) > 1 else None, "ci95": ci}

def load_runs(root, frozen, suite):
    records = []
    for path in sorted((Path(root) / "runs").glob("*/result.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["suite"] != suite:
            continue
        checksum = json.loads(path.with_name("result.sha256.json").read_text(encoding="utf-8"))
        if checksum["result_hash"] != digest(record) or record["manifest_hash"] != frozen["manifest_hash"] or not finite(record):
            raise RuntimeError("ARCHIVED_RESULT_INTEGRITY_MISMATCH:" + record["run_id"])
        provenance = json.loads(path.with_name("provenance.json").read_text(encoding="utf-8"))
        provenance_checksum = json.loads(path.with_name("provenance.sha256.json").read_text(encoding="utf-8"))
        if provenance_checksum["provenance_hash"] != digest(provenance):
            raise RuntimeError("ARCHIVED_PROVENANCE_MISMATCH")
        if provenance["schedule_hash"] != record["schedule_hash"] or digest(provenance["schedule"]) != record["schedule_hash"]:
            raise RuntimeError("ARCHIVED_DEMAND_MISMATCH")
        records.append(record)
    keys = [(r["scenario_id"], r["seed"], r["method"]) for r in records]
    if len(set(keys)) != len(keys):
        raise RuntimeError("DUPLICATE_EXPERIMENT_KEYS: use a separate smoke output root; never select favorable reruns")
    return records

def aggregate(records, frozen, suite):
    demand_hashes = {}
    for record in records:
        key = (record["scenario_id"], record["seed"])
        if key in demand_hashes and demand_hashes[key] != record["schedule_hash"]:
            raise RuntimeError("PAIRED_DEMAND_MISMATCH")
        demand_hashes[key] = record["schedule_hash"]
    groups = []
    for scenario in SCENARIOS:
        for method in METHODS:
            runs = [r for r in records if r["scenario_id"] == scenario.scenario_id and r["method"] == method]
            if not runs:
                continue
            valid = [r for r in runs if r["classification"] != "INVALID_EXPERIMENT"]
            groups.append({"scenario_id": scenario.scenario_id, "method": method,
                "vehicle_count": scenario.vehicle_count, "headway_seconds": scenario.headway_seconds,
                "continuous": scenario.continuous, "episode_count": len(runs),
                "classifications": dict(Counter(r["classification"] for r in runs)),
                "metrics": {key: summary(r["metrics"].get(key) for r in valid) for key in METRICS},
                "per_approach_mean_waiting_time_seconds": {a: summary(r["metrics"][
                    "per_approach_mean_waiting_time_seconds"][a] for r in valid) for a in "NESW"},
                "valid_episode_count": len(valid)})
    paired = []
    for scenario in SCENARIOS:
        for baseline in METHODS[1:]:
            pairs = []
            for seed in SEEDS if scenario.continuous else (None,):
                rows = {r["method"]: r for r in records if r["scenario_id"] == scenario.scenario_id and r["seed"] == seed}
                if "PROPOSED_MAPPO" not in rows or baseline not in rows:
                    continue
                a, b = rows["PROPOSED_MAPPO"], rows[baseline]
                if a["schedule_hash"] != b["schedule_hash"]:
                    raise RuntimeError("PAIRED_DEMAND_MISMATCH")
                if "INVALID_EXPERIMENT" not in (a["classification"], b["classification"]):
                    pairs.append((a["metrics"], b["metrics"]))
            keys = ("total_team_travel_time_seconds", "throughput_vehicles_per_minute",
                    "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds")
            paired.append({"scenario_id": scenario.scenario_id, "baseline": baseline,
                "paired_count": len(pairs), "relative_difference_percent": {
                    key: summary(100 * (a[key] - b[key]) / b[key] for a, b in pairs
                        if a.get(key) is not None and b.get(key) not in (None, 0)) for key in keys},
                "completion_rate_difference_percentage_points": summary(
                    100 * (a["completion_rate"] - b["completion_rate"]) for a, b in pairs)})
    expected = {(s.scenario_id, seed, method) for s in SCENARIOS for seed in (
        SEEDS if s.continuous else (None,)) for method in METHODS}
    actual = {(r["scenario_id"], r["seed"], r["method"]) for r in records}
    return {"schema_version": 1, "suite": suite, "evidence_classification": (
        "FINAL_POST_TRAINING_SYSTEM_EVALUATION" if suite == "final" and actual == expected else
        "SMOKE_NOT_FINAL" if suite == "smoke" else "INCOMPLETE_FINAL_MATRIX"),
        "manifest_hash": frozen["manifest_hash"], "scope": frozen["manifest"]["scope"],
        "out_of_scope": frozen["manifest"]["out_of_scope"], "episode_count": len(records),
        "expected_final_episode_count": 165, "complete_final_matrix": suite == "final" and actual == expected,
        "classification_counts": dict(Counter(r["classification"] for r in records)),
        "groups": groups, "paired_comparisons": paired,
        "integrity_all_valid": bool(records) and all(r["integrity"]["valid"] for r in records),
        "collision_count": sum(r["metrics"]["collision_count"] for r in records),
        "blocked_zone_violation_count": sum(r["metrics"]["blocked_zone_violation_count"] for r in records),
        "unsafe_episode_rate": sum(r["metrics"]["unsafe_episode"] for r in records) / len(records) if records else None,
        "collision_free_episodes": sum(r["metrics"]["collision_free_episode"] for r in records),
        "policy_hash_unchanged": bool(records) and all(r["integrity"]["policy_hash_unchanged"] for r in records),
        "centralized_critic_runtime_calls": sum(r["integrity"]["centralized_critic_runtime_calls"] for r in records),
        "decentralized_execution": bool(records) and all(r["integrity"]["decentralized_execution"] for r in records),
        "runs": [{k: r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")} for r in records]}
