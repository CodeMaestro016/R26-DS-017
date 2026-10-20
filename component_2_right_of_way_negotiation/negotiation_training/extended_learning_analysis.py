"""Threshold-free descriptive summaries for Step 5J.3C.2B."""

# Import mean, median, stdev, variance from statistics for the operations below.
from statistics import mean, median, stdev, variance


# Three replication descriptive statistics using the inputs and processing steps below.
# Input values: the supplied values.
# Output: a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation,
# minimum,...
# Processing: select branches using the stated conditions.
def three_replication_descriptive_statistics(values):
    # Set values to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # values.
    values = tuple(float(value) for value in values)
    # Run this branch when the number of entries in values differs from 3.
    if len(values) != 3:
        # Raise ValueError with the text 'EXACTLY_THREE_EXTENDED_EVIDENCE_VALUES_REQUIRED' to stop this execution
        # path.
        raise ValueError("EXACTLY_THREE_EXTENDED_EVIDENCE_VALUES_REQUIRED")
    # Return a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation,
    # minimum,... to the caller.
    return {
        # Store values under 'values'.
        "values": values,
        # Store the result of mean(values) under 'sample_mean'.
        "sample_mean": mean(values),
        # Store the result of variance(values) under 'sample_variance_n_minus_1'.
        "sample_variance_n_minus_1": variance(values),
        # Store the result of stdev(values) under 'sample_standard_deviation'.
        "sample_standard_deviation": stdev(values),
        # Store the minimum of values under 'minimum'.
        # Store the maximum of values under 'maximum'.
        "minimum": min(values), "maximum": max(values),
        # Store the result of median(values) under 'median'.
        "median": median(values),
    }


# Exact scenario paired changes using the inputs and processing steps below.
# Input state0: the supplied state0.
# Input state1: the supplied state1.
# Input state2: the supplied state2.
# Output: a tuple built from a lazy sequence of a dictionary containing scenario_id, delta_state0_to_state1,
# delta_state1_to_state2, delta_state0_to_state2 for key in maps at 0.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def exact_scenario_paired_changes(state0, state1, state2):
    # Set maps to an empty list.
    maps = []
    # Iterate over a tuple containing state0, state1, state2, binding each item to state.
    for state in (state0, state1, state2):
        # Set current to a dictionary of the result of repr(item at 'scenario_id') mapped to item for item in
        # state at 'scenario_metrics'.
        current = {repr(item["scenario_id"]): item for item in
                   # Evaluate state at 'scenario_metrics' as part of the enclosing expression.
                   state["scenario_metrics"]}
        # Run this branch when the number of entries in current differs from the number of entries in state at
        # 'scenario_metrics'.
        if len(current) != len(state["scenario_metrics"]):
            # Raise ValueError with the text 'DUPLICATE_SCENARIO_IDENTITY' to stop this execution path.
            raise ValueError("DUPLICATE_SCENARIO_IDENTITY")
        # Append current to maps.
        maps.append(current)
    # Run this branch when the negation of keys from maps[0] equals keys from maps[1]; equals keys from maps[2].
    if not (maps[0].keys() == maps[1].keys() == maps[2].keys()):
        # Raise ValueError with the text 'SCENARIO_PAIRING_IDENTITY_MISMATCH' to stop this execution path.
        raise ValueError("SCENARIO_PAIRING_IDENTITY_MISMATCH")
    # Return a tuple built from a lazy sequence of a dictionary containing scenario_id, delta_state0_to_state1,
    # delta_state1_to_state2, delta_state0_to_state2 for key in maps at 0 to the caller.
    return tuple({
        # Store maps[0][key] at 'scenario_id' under 'scenario_id'.
        "scenario_id": maps[0][key]["scenario_id"],
        "delta_state0_to_state1":
            # Evaluate maps[1][key] at 'team_travel_time_seconds' minus maps[0][key] at 'team_travel_time_seconds'
            # as part of the enclosing expression.
            maps[1][key]["team_travel_time_seconds"] -
            # Evaluate maps[0][key] at 'team_travel_time_seconds' as part of the enclosing expression.
            maps[0][key]["team_travel_time_seconds"],
        "delta_state1_to_state2":
            # Evaluate maps[2][key] at 'team_travel_time_seconds' minus maps[1][key] at 'team_travel_time_seconds'
            # as part of the enclosing expression.
            maps[2][key]["team_travel_time_seconds"] -
            # Evaluate maps[1][key] at 'team_travel_time_seconds' as part of the enclosing expression.
            maps[1][key]["team_travel_time_seconds"],
        "delta_state0_to_state2":
            # Evaluate maps[2][key] at 'team_travel_time_seconds' minus maps[0][key] at 'team_travel_time_seconds'
            # as part of the enclosing expression.
            maps[2][key]["team_travel_time_seconds"] -
            # Evaluate maps[0][key] at 'team_travel_time_seconds' as part of the enclosing expression.
            maps[0][key]["team_travel_time_seconds"],
    # Evaluate maps at 0 as part of the enclosing expression.
    } for key in maps[0])
