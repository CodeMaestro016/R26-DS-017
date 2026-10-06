"""Threshold-free descriptive summaries for Step 5J.3C.2B."""

from statistics import mean, median, stdev, variance


def three_replication_descriptive_statistics(values):
    values = tuple(float(value) for value in values)
    if len(values) != 3:
        raise ValueError("EXACTLY_THREE_EXTENDED_EVIDENCE_VALUES_REQUIRED")
    return {
        "values": values,
        "sample_mean": mean(values),
        "sample_variance_n_minus_1": variance(values),
        "sample_standard_deviation": stdev(values),
        "minimum": min(values), "maximum": max(values),
        "median": median(values),
    }


def exact_scenario_paired_changes(state0, state1, state2):
    maps = []
    for state in (state0, state1, state2):
        current = {repr(item["scenario_id"]): item for item in
                   state["scenario_metrics"]}
        if len(current) != len(state["scenario_metrics"]):
            raise ValueError("DUPLICATE_SCENARIO_IDENTITY")
        maps.append(current)
    if not (maps[0].keys() == maps[1].keys() == maps[2].keys()):
        raise ValueError("SCENARIO_PAIRING_IDENTITY_MISMATCH")
    return tuple({
        "scenario_id": maps[0][key]["scenario_id"],
        "delta_state0_to_state1":
            maps[1][key]["team_travel_time_seconds"] -
            maps[0][key]["team_travel_time_seconds"],
        "delta_state1_to_state2":
            maps[2][key]["team_travel_time_seconds"] -
            maps[1][key]["team_travel_time_seconds"],
        "delta_state0_to_state2":
            maps[2][key]["team_travel_time_seconds"] -
            maps[0][key]["team_travel_time_seconds"],
    } for key in maps[0])
