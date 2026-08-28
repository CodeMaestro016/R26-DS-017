"""Threshold-free descriptive analysis for the two-replication pilot."""

from statistics import mean, median, stdev, variance


def paired_difference_summary(values):
    values = tuple(float(value) for value in values)
    return {
        "count": len(values), "mean": mean(values), "median": median(values),
        "minimum": min(values), "maximum": max(values),
        "negative_count": sum(value < 0 for value in values),
        "zero_count": sum(value == 0 for value in values),
        "positive_count": sum(value > 0 for value in values),
    }


def two_replication_sample_statistics(values):
    values = tuple(float(value) for value in values)
    if len(values) != 2:
        raise ValueError("EXACTLY_TWO_VARIANCE_PROBE_VALUES_REQUIRED")
    return {"values": values, "sample_mean": mean(values),
            "sample_variance_n_minus_1": variance(values),
            "sample_standard_deviation": stdev(values)}
