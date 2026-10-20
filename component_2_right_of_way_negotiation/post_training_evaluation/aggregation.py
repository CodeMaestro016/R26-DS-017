"""Reproducible descriptive and paired statistics; no hypothesis tests."""
# Import Counter from collections for the operations below.
from collections import Counter
# Import mean, median, stdev from statistics for the operations below.
from statistics import mean, median, stdev
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import json for use in this module.
import json
# Import random for use in this module.
import random
# Import numpy as np for use in this module.
import numpy as np
# Import digest, finite, METHODS, SEEDS from .models for the operations below.
from .models import digest, finite, METHODS, SEEDS
# Import SCENARIOS from .scenarios for the operations below.
from .scenarios import SCENARIOS

# Set METRICS to a tuple containing the text 'collision_count', the text 'blocked_zone_violation_count', the text
# 'unsafe_episode', the text...
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
    "ego_execution_mean_ms", "ego_execution_p95_ms", "mappo_negotiation_events",
    "mappo_outcomes_accepted", "mappo_outcomes_rejected_by_safety_shield",
    "fallback_activations", "fallback_rate", "timeout", "deadlock_observed")

# Summary using the inputs and processing steps below.
# Input values: the supplied values.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def summary(values):
    # Set values to a list of a floating-point number built from x for x in values; retain entries satisfying x is
    # a different object from None.
    values = [float(x) for x in values if x is not None]
    # Run this branch when the negation of values.
    if not values:
        # Return a dictionary containing n, mean, median, standard_deviation, ci95 to the caller.
        return {"n": 0, "mean": None, "median": None, "standard_deviation": None, "ci95": None}
    # Set ci to None.
    ci = None
    # Run this branch when the number of entries in values is greater than 1.
    if len(values) > 1:
        # Set rng to the result of random.Random(260826).
        rng = random.Random(260826)
        # Set samples to a list of the result of mean(the result of rng.choices(values)) for _ in the integer
        # range defined by 2000.
        samples = [mean(rng.choices(values, k=len(values))) for _ in range(2000)]
        # Set ci to a list built from the result of np.percentile(samples, a list containing 2.5, 97.5).
        ci = list(np.percentile(samples, [2.5, 97.5], method="linear"))
    # Return a dictionary containing n, mean, median, standard_deviation, ci95 to the caller.
    return {"n": len(values), "mean": mean(values), "median": median(values),
        # Store the result of stdev(values) when the number of entries in values is greater than 1, otherwise None
        # under 'standard_deviation'.
        # Store ci under 'ci95'.
        "standard_deviation": stdev(values) if len(values) > 1 else None, "ci95": ci}

# Load runs using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input frozen: the supplied frozen.
# Input suite: the supplied suite.
# Output: records.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def load_runs(root, frozen, suite):
    # Set records to an empty list.
    records = []
    # Iterate over the sorted values from the result of (Path(root) / 'runs').glob(the text '*/result.json'),
    # binding each item to path.
    for path in sorted((Path(root) / "runs").glob("*/result.json")):
        # Set record to the decoded data produced by json.loads from the text read from path.
        record = json.loads(path.read_text(encoding="utf-8"))
        # Run this branch when record at 'suite' differs from suite.
        if record["suite"] != suite:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set checksum to the decoded data produced by json.loads from the text read from
        # path.with_name('result.sha256.json').
        checksum = json.loads(path.with_name("result.sha256.json").read_text(encoding="utf-8"))
        # Run this branch when checksum at 'result_hash' differs from the result of digest(record) or record at
        # 'manifest_hash' differs from frozen at 'manifest_hash' or the negation of the result of finite(record).
        if checksum["result_hash"] != digest(record) or record["manifest_hash"] != frozen["manifest_hash"] or not finite(record):
            # Raise RuntimeError with the text 'ARCHIVED_RESULT_INTEGRITY_MISMATCH:' plus record at 'run_id' to
            # stop this execution path.
            raise RuntimeError("ARCHIVED_RESULT_INTEGRITY_MISMATCH:" + record["run_id"])
        # Set provenance to the decoded data produced by json.loads from the text read from
        # path.with_name('provenance.json').
        provenance = json.loads(path.with_name("provenance.json").read_text(encoding="utf-8"))
        # Set provenance_checksum to the decoded data produced by json.loads from the text read from
        # path.with_name('provenance.sha256.json').
        provenance_checksum = json.loads(path.with_name("provenance.sha256.json").read_text(encoding="utf-8"))
        # Run this branch when provenance_checksum at 'provenance_hash' differs from the result of
        # digest(provenance).
        if provenance_checksum["provenance_hash"] != digest(provenance):
            # Raise RuntimeError with the text 'ARCHIVED_PROVENANCE_MISMATCH' to stop this execution path.
            raise RuntimeError("ARCHIVED_PROVENANCE_MISMATCH")
        # Run this branch when provenance at 'schedule_hash' differs from record at 'schedule_hash' or the result
        # of digest(provenance at 'schedule') differs from record at 'schedule_hash'.
        if provenance["schedule_hash"] != record["schedule_hash"] or digest(provenance["schedule"]) != record["schedule_hash"]:
            # Raise RuntimeError with the text 'ARCHIVED_DEMAND_MISMATCH' to stop this execution path.
            raise RuntimeError("ARCHIVED_DEMAND_MISMATCH")
        # Append record to records.
        records.append(record)
    # Set keys to a list of a tuple containing r at 'scenario_id', r at 'seed', r at 'method' for r in records.
    keys = [(r["scenario_id"], r["seed"], r["method"]) for r in records]
    # Run this branch when the number of entries in a set built from keys differs from the number of entries in
    # keys.
    if len(set(keys)) != len(keys):
        # Raise RuntimeError with the text 'DUPLICATE_EXPERIMENT_KEYS: use a separate smoke output root;...' to
        # stop this execution path.
        raise RuntimeError("DUPLICATE_EXPERIMENT_KEYS: use a separate smoke output root; never select favorable reruns")
    # Return records to the caller.
    return records

# Aggregate using the inputs and processing steps below.
# Input records: the supplied records.
# Input frozen: the supplied frozen.
# Input suite: the supplied suite.
# Output: a dictionary containing schema_version, suite, evidence_classification, manifest_hash, scope,
# out_of_scope,...
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def aggregate(records, frozen, suite):
    # Set demand_hashes to an empty dictionary.
    demand_hashes = {}
    # Iterate over records, binding each item to record.
    for record in records:
        # Set key to a tuple containing record at 'scenario_id', record at 'seed'.
        key = (record["scenario_id"], record["seed"])
        # Run this branch when key belongs to demand_hashes and demand_hashes at key differs from record at
        # 'schedule_hash'.
        if key in demand_hashes and demand_hashes[key] != record["schedule_hash"]:
            # Raise RuntimeError with the text 'PAIRED_DEMAND_MISMATCH' to stop this execution path.
            raise RuntimeError("PAIRED_DEMAND_MISMATCH")
        # Set demand_hashes[key] to record at 'schedule_hash'.
        demand_hashes[key] = record["schedule_hash"]
    # Set groups to an empty list.
    groups = []
    # Iterate over SCENARIOS, binding each item to scenario.
    for scenario in SCENARIOS:
        # Iterate over METHODS, binding each item to method.
        for method in METHODS:
            # Set runs to a list of r for r in records; retain entries satisfying r at 'scenario_id' equals
            # scenario.scenario_id and r at 'method' equals method.
            runs = [r for r in records if r["scenario_id"] == scenario.scenario_id and r["method"] == method]
            # Run this branch when the negation of runs.
            if not runs:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set valid to a list of r for r in runs; retain entries satisfying r at 'classification' differs from
            # the text 'INVALID_EXPERIMENT'.
            valid = [r for r in runs if r["classification"] != "INVALID_EXPERIMENT"]
            # Append a dictionary containing scenario_id, method, vehicle_count, headway_seconds, continuous,
            # episode_count,... to groups.
            groups.append({"scenario_id": scenario.scenario_id, "method": method,
                # Store scenario.vehicle_count under 'vehicle_count'.
                # Store scenario.headway_seconds under 'headway_seconds'.
                "vehicle_count": scenario.vehicle_count, "headway_seconds": scenario.headway_seconds,
                # Store scenario.continuous under 'continuous'.
                # Store the number of entries in runs under 'episode_count'.
                "continuous": scenario.continuous, "episode_count": len(runs),
                # Store a dictionary built from the result of Counter(a lazy sequence of r at 'classification' for
                # r in runs) under 'classifications'.
                "classifications": dict(Counter(r["classification"] for r in runs)),
                # Store a dictionary of key mapped to the result of summary(a lazy sequence of key from
                # r['metrics']; use None if absent for r in valid) for key in METRICS under 'metrics'.
                "metrics": {key: summary(r["metrics"].get(key) for r in valid) for key in METRICS},
                # Store a dictionary of a mapped to the result of summary(a lazy sequence of
                # r['metrics']['per_approach_mean_waiting_time_seconds'] at a for r in valid) for a in the text
                # 'NESW' under 'per_approach_mean_waiting_time_seconds'.
                "per_approach_mean_waiting_time_seconds": {a: summary(r["metrics"][
                    # Evaluate valid as part of the enclosing expression.
                    "per_approach_mean_waiting_time_seconds"][a] for r in valid) for a in "NESW"},
                # Store the number of entries in valid under 'valid_episode_count'.
                "valid_episode_count": len(valid)})
    # Set paired to an empty list.
    paired = []
    # Iterate over SCENARIOS, binding each item to scenario.
    for scenario in SCENARIOS:
        # Iterate over METHODS sliced by 1:, binding each item to baseline.
        for baseline in METHODS[1:]:
            # Set pairs to an empty list.
            pairs = []
            # Iterate over SEEDS when scenario.continuous, otherwise a tuple containing None, binding each item to
            # seed.
            for seed in SEEDS if scenario.continuous else (None,):
                # Set rows to a dictionary of r at 'method' mapped to r for r in records; retain entries
                # satisfying r at 'scenario_id' equals scenario.scenario_id and r at 'seed' equals seed.
                rows = {r["method"]: r for r in records if r["scenario_id"] == scenario.scenario_id and r["seed"] == seed}
                # Run this branch when the text 'PROPOSED_MAPPO' does not belong to rows or baseline does not
                # belong to rows.
                if "PROPOSED_MAPPO" not in rows or baseline not in rows:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set (a, b) to a tuple containing rows at 'PROPOSED_MAPPO', rows at baseline.
                a, b = rows["PROPOSED_MAPPO"], rows[baseline]
                # Run this branch when a at 'schedule_hash' differs from b at 'schedule_hash'.
                if a["schedule_hash"] != b["schedule_hash"]:
                    # Raise RuntimeError with the text 'PAIRED_DEMAND_MISMATCH' to stop this execution path.
                    raise RuntimeError("PAIRED_DEMAND_MISMATCH")
                # Run this branch when the text 'INVALID_EXPERIMENT' does not belong to a tuple containing a at
                # 'classification', b at 'classification'.
                if "INVALID_EXPERIMENT" not in (a["classification"], b["classification"]):
                    # Append a tuple containing a at 'metrics', b at 'metrics' to pairs.
                    pairs.append((a["metrics"], b["metrics"]))
            # Set keys to a tuple containing the text 'total_team_travel_time_seconds', the text
            # 'throughput_vehicles_per_minute', the text...
            keys = ("total_team_travel_time_seconds", "throughput_vehicles_per_minute",
                    "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds")
            # Append a dictionary containing scenario_id, baseline, paired_count, relative_difference_percent,...
            # to paired.
            paired.append({"scenario_id": scenario.scenario_id, "baseline": baseline,
                # Store the number of entries in pairs under 'paired_count'.
                # Store a dictionary of key mapped to the result of summary(a lazy sequence of 100 * (a[key] -
                # b[key]) divided by b[key] for (a, b) in pairs; retain entries...) for key in keys under
                # 'relative_difference_percent'.
                "paired_count": len(pairs), "relative_difference_percent": {
                    # Evaluate the result of summary(a lazy sequence of 100 multiplied by a[key] - b[key] divided
                    # by b at key for (a, b) in pairs;...) as part of the enclosing expression.
                    key: summary(100 * (a[key] - b[key]) / b[key] for a, b in pairs
                        # Evaluate key from a; use None if absent is a different object from None and key from b;
                        # use None if absent does not belong to a tuple containing None, 0 as part of the
                        # enclosing expression.
                        if a.get(key) is not None and b.get(key) not in (None, 0)) for key in keys},
                # Store the result of summary(a lazy sequence of 100 multiplied by a['completion_rate'] minus
                # b['completion_rate'] for (a, b)...) under 'completion_rate_difference_percentage_points'.
                "completion_rate_difference_percentage_points": summary(
                    # Evaluate 100 multiplied by a at 'completion_rate' minus b at 'completion_rate' as part of
                    # the enclosing expression.
                    100 * (a["completion_rate"] - b["completion_rate"]) for a, b in pairs)})
    # Set expected to a set of a tuple containing s.scenario_id, seed, method for s in SCENARIOS.
    expected = {(s.scenario_id, seed, method) for s in SCENARIOS for seed in (
        # Evaluate SEEDS when s.continuous, otherwise a tuple containing None as part of the enclosing expression.
        SEEDS if s.continuous else (None,)) for method in METHODS}
    # Set actual to a set of a tuple containing r at 'scenario_id', r at 'seed', r at 'method' for r in records.
    actual = {(r["scenario_id"], r["seed"], r["method"]) for r in records}
    # Return a dictionary containing schema_version, suite, evidence_classification, manifest_hash, scope,
    # out_of_scope,... to the caller.
    return {"schema_version": 1, "suite": suite, "evidence_classification": (
        # Evaluate the text 'FINAL_POST_TRAINING_SYSTEM_EVALUATION' when suite equals the text 'final' and actual
        # equals expected, otherwise the text 'SMOKE_NOT_FINAL' when suite equals the text 'smoke', otherwise the
        # text 'INCOMPLETE_FINAL_MATRIX' as part of the enclosing expression.
        "FINAL_POST_TRAINING_SYSTEM_EVALUATION" if suite == "final" and actual == expected else
        # Evaluate the text 'SMOKE_NOT_FINAL' when suite equals the text 'smoke', otherwise the text
        # 'INCOMPLETE_FINAL_MATRIX' as part of the enclosing expression.
        "SMOKE_NOT_FINAL" if suite == "smoke" else "INCOMPLETE_FINAL_MATRIX"),
        # Store frozen at 'manifest_hash' under 'manifest_hash'.
        # Store frozen['manifest'] at 'scope' under 'scope'.
        "manifest_hash": frozen["manifest_hash"], "scope": frozen["manifest"]["scope"],
        # Store frozen['manifest'] at 'out_of_scope' under 'out_of_scope'.
        # Store the number of entries in records under 'episode_count'.
        "out_of_scope": frozen["manifest"]["out_of_scope"], "episode_count": len(records),
        # Store 165 under 'expected_final_episode_count'.
        # Store suite equals the text 'final' and actual equals expected under 'complete_final_matrix'.
        "expected_final_episode_count": 165, "complete_final_matrix": suite == "final" and actual == expected,
        # Store a dictionary built from the result of Counter(a lazy sequence of r at 'classification' for r in
        # records) under 'classification_counts'.
        "classification_counts": dict(Counter(r["classification"] for r in records)),
        # Store groups under 'groups'.
        # Store paired under 'paired_comparisons'.
        "groups": groups, "paired_comparisons": paired,
        # Store a Boolean built from records and whether every item is true in a lazy sequence of r['integrity']
        # at 'valid' for r in records under 'integrity_all_valid'.
        "integrity_all_valid": bool(records) and all(r["integrity"]["valid"] for r in records),
        # Store the sum of a lazy sequence of r['metrics'] at 'collision_count' for r in records under
        # 'collision_count'.
        "collision_count": sum(r["metrics"]["collision_count"] for r in records),
        # Store the sum of a lazy sequence of r['metrics'] at 'blocked_zone_violation_count' for r in records
        # under 'blocked_zone_violation_count'.
        "blocked_zone_violation_count": sum(r["metrics"]["blocked_zone_violation_count"] for r in records),
        # Store the sum of a lazy sequence of r['metrics']['unsafe_episode'] for r in records divided by the
        # number of entries in records when records, otherwise None under 'unsafe_episode_rate'.
        "unsafe_episode_rate": sum(r["metrics"]["unsafe_episode"] for r in records) / len(records) if records else None,
        # Store the sum of a lazy sequence of r['metrics'] at 'collision_free_episode' for r in records under
        # 'collision_free_episodes'.
        "collision_free_episodes": sum(r["metrics"]["collision_free_episode"] for r in records),
        # Store a Boolean built from records and whether every item is true in a lazy sequence of r['integrity']
        # at 'policy_hash_unchanged' for r in records under 'policy_hash_unchanged'.
        "policy_hash_unchanged": bool(records) and all(r["integrity"]["policy_hash_unchanged"] for r in records),
        # Store the sum of a lazy sequence of r['integrity'] at 'centralized_critic_runtime_calls' for r in
        # records under 'centralized_critic_runtime_calls'.
        "centralized_critic_runtime_calls": sum(r["integrity"]["centralized_critic_runtime_calls"] for r in records),
        # Store a Boolean built from records and whether every item is true in a lazy sequence of r['integrity']
        # at 'decentralized_execution' for r in records under 'decentralized_execution'.
        "decentralized_execution": bool(records) and all(r["integrity"]["decentralized_execution"] for r in records),
        # Store a list of a dictionary of k mapped to r at k for k in a tuple containing the text 'run_id', the
        # text 'method', the text 'scenario_id', the text 'seed', the text 'classification',... for r in records
        # under 'runs'.
        "runs": [{k: r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")} for r in records]}
