"""Stable tensor-column identities; categorical order implies no ranking."""

NODE_NUMERIC_SCHEMA = (
    "is_ego",
    "speed_mps",
    "max_acceleration_mps2",
    "comfortable_deceleration_mps2",
    "max_speed_mps",
    "observation_confidence",
    "is_currently_observed",
    "observation_age_seconds",
)

RELATIVE_APPROACH_CATEGORIES = (
    "RIGHT", "LEFT", "ONCOMING", "SAME_APPROACH",
)

EDGE_ORIGIN_CATEGORIES = (
    "LOCAL", "COMMUNICATED", "LOCAL_AND_COMMUNICATED",
)

EDGE_NUMERIC_SCHEMA = tuple(
    f"edge_origin__{category}" for category in EDGE_ORIGIN_CATEGORIES
) + tuple(
    f"relative_approach__{category}" for category in RELATIVE_APPROACH_CATEGORIES
) + (
    "physical_reachability_evidence_available",
    "temporal_conflict_possible",
)

CATEGORICAL_ENCODING_METADATA = {
    "edge_origin": {
        "encoding": "ONE_HOT_SET_MEMBERSHIP",
        "categories": EDGE_ORIGIN_CATEGORIES,
        "ordinal_meaning": False,
    },
    "relative_approaches": {
        "encoding": "MULTI_HOT_SET_MEMBERSHIP",
        "categories": RELATIVE_APPROACH_CATEGORIES,
        "ordinal_meaning": False,
    },
    "conflict_types": {
        "encoding": "DEFERRED_CATEGORICAL_SCHEMA_NOT_FIXED",
    },
}
