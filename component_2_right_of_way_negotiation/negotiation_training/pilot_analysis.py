"""Threshold-free descriptive analysis for the two-replication pilot."""

# Import mean, median, stdev, variance from statistics for the operations below.
from statistics import mean, median, stdev, variance


# Paired difference summary using the inputs and processing steps below.
# Input values: the supplied values.
# Output: a dictionary containing count, mean, median, minimum, maximum, negative_count, zero_count,
# positive_count.
def paired_difference_summary(values):
    # Set values to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # values.
    values = tuple(float(value) for value in values)
    # Return a dictionary containing count, mean, median, minimum, maximum, negative_count, zero_count,
    # positive_count to the caller.
    return {
        # Store the number of entries in values under 'count'.
        # Store the result of mean(values) under 'mean'.
        # Store the result of median(values) under 'median'.
        "count": len(values), "mean": mean(values), "median": median(values),
        # Store the minimum of values under 'minimum'.
        # Store the maximum of values under 'maximum'.
        "minimum": min(values), "maximum": max(values),
        # Store the sum of a lazy sequence of value is less than 0 for value in values under 'negative_count'.
        "negative_count": sum(value < 0 for value in values),
        # Store the sum of a lazy sequence of value equals 0 for value in values under 'zero_count'.
        "zero_count": sum(value == 0 for value in values),
        # Store the sum of a lazy sequence of value is greater than 0 for value in values under 'positive_count'.
        "positive_count": sum(value > 0 for value in values),
    }


# Two replication sample statistics using the inputs and processing steps below.
# Input values: the supplied values.
# Output: a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation.
# Processing: select branches using the stated conditions.
def two_replication_sample_statistics(values):
    # Set values to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # values.
    values = tuple(float(value) for value in values)
    # Run this branch when the number of entries in values differs from 2.
    if len(values) != 2:
        # Raise ValueError with the text 'EXACTLY_TWO_VARIANCE_PROBE_VALUES_REQUIRED' to stop this execution path.
        raise ValueError("EXACTLY_TWO_VARIANCE_PROBE_VALUES_REQUIRED")
    # Return a dictionary containing values, sample_mean, sample_variance_n_minus_1, sample_standard_deviation to
    # the caller.
    return {"values": values, "sample_mean": mean(values),
            # Store the result of variance(values) under 'sample_variance_n_minus_1'.
            "sample_variance_n_minus_1": variance(values),
            # Store the result of stdev(values) under 'sample_standard_deviation'.
            "sample_standard_deviation": stdev(values)}
