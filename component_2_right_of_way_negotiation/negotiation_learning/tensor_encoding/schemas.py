"""Stable tensor-column identities; categorical order implies no ranking."""

# Set NODE_NUMERIC_SCHEMA to a tuple containing the text 'is_ego', the text 'speed_mps', the text
# 'max_acceleration_mps2', the text...
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

# Set RELATIVE_APPROACH_CATEGORIES to a tuple containing the text 'RIGHT', the text 'LEFT', the text 'ONCOMING',
# the text 'SAME_APPROACH'.
RELATIVE_APPROACH_CATEGORIES = (
    "RIGHT", "LEFT", "ONCOMING", "SAME_APPROACH",
)

# Set EDGE_ORIGIN_CATEGORIES to a tuple containing the text 'LOCAL', the text 'COMMUNICATED', the text
# 'LOCAL_AND_COMMUNICATED'.
EDGE_ORIGIN_CATEGORIES = (
    "LOCAL", "COMMUNICATED", "LOCAL_AND_COMMUNICATED",
)

# Set EDGE_NUMERIC_SCHEMA to a tuple built from a lazy sequence of f'edge_origin__{category}' for category in
# EDGE_ORIGIN_CATEGORIES plus a tuple built from a lazy sequence of f'relative_approach__{category}' for category
# in RELATIVE_APPROACH_CATEGORIES plus a tuple containing the text 'physical_reachability_evidence_available', the
# text 'temporal_conflict_possible'.
EDGE_NUMERIC_SCHEMA = tuple(
    # Evaluate formatted text built from the embedded values as part of the enclosing expression.
    f"edge_origin__{category}" for category in EDGE_ORIGIN_CATEGORIES
# Evaluate a tuple built from a lazy sequence of formatted text built from the embedded values for category in
# RELATIVE_APPROACH_CATEGORIES as part of the enclosing expression.
) + tuple(
    # Evaluate formatted text built from the embedded values as part of the enclosing expression.
    f"relative_approach__{category}" for category in RELATIVE_APPROACH_CATEGORIES
# Evaluate a tuple containing the text 'physical_reachability_evidence_available', the text
# 'temporal_conflict_possible' as part of the enclosing expression.
) + (
    "physical_reachability_evidence_available",
    "temporal_conflict_possible",
)

# Set CATEGORICAL_ENCODING_METADATA to a dictionary containing edge_origin, relative_approaches, conflict_types.
CATEGORICAL_ENCODING_METADATA = {
    # Store a dictionary containing encoding, categories, ordinal_meaning under 'edge_origin'.
    "edge_origin": {
        "encoding": "ONE_HOT_SET_MEMBERSHIP",
        # Store EDGE_ORIGIN_CATEGORIES under 'categories'.
        "categories": EDGE_ORIGIN_CATEGORIES,
        # Store False under 'ordinal_meaning'.
        "ordinal_meaning": False,
    },
    # Store a dictionary containing encoding, categories, ordinal_meaning under 'relative_approaches'.
    "relative_approaches": {
        "encoding": "MULTI_HOT_SET_MEMBERSHIP",
        # Store RELATIVE_APPROACH_CATEGORIES under 'categories'.
        "categories": RELATIVE_APPROACH_CATEGORIES,
        # Store False under 'ordinal_meaning'.
        "ordinal_meaning": False,
    },
    # Store a dictionary containing encoding under 'conflict_types'.
    "conflict_types": {
        "encoding": "DEFERRED_CATEGORICAL_SCHEMA_NOT_FIXED",
    },
}
