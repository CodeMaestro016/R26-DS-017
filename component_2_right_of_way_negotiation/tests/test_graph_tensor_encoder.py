"""Deterministic NumPy-only GNN-input encoding tests."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from negotiation_learning.tensor_encoding import (
    EDGE_NUMERIC_SCHEMA, GraphTensorEncoder, GraphTensorEncodingError,
    NODE_NUMERIC_SCHEMA,
)


def node(is_ego=False, speed=3.0, observed=True):
    return {
        "is_ego": is_ego, "speed_mps": speed,
        "max_acceleration_mps2": 2.0,
        "comfortable_deceleration_mps2": 4.5,
        "max_speed_mps": 13.89,
        "observation_confidence": 1.0,
        "is_currently_observed": observed,
        "observation_age_seconds": 0.0,
    }


def remote_node():
    return {
        "is_ego": False, "speed_mps": None,
        "max_acceleration_mps2": None,
        "comfortable_deceleration_mps2": None,
        "max_speed_mps": None, "observation_confidence": None,
        "is_currently_observed": None, "observation_age_seconds": None,
    }


def edge(source, target, origin="LOCAL", relations=("RIGHT",), physical=True):
    return {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "edge_origin": origin, "relative_approaches": relations,
        "physical_reachability_evidence": ({
            "temporal_conflict_possible": False,
            "evaluations": ({"target_earliest_reachable_entry_time_s": 2.0},),
        } if physical else None),
        "applicable_rule_ids": ("DE-STVO-8-1",),
        "source_sections": ("§ 8",), "regulatory_profile": "PROFILE",
        "shared_conflict_zone_ids": ("ZONE_ID",),
        "target_candidate_path_ids": ("PATH_ID",),
        "conflict_types": ("CROSSING",),
    }


def observation(node_ids, edges, features=None):
    features = features or tuple(
        node(node_id == node_ids[0]) for node_id in node_ids
    )
    index = {name: position for position, name in enumerate(node_ids)}
    return {
        "ego_id": node_ids[0], "node_ids": tuple(node_ids),
        "node_features": tuple(features),
        "edge_index": tuple((index[item["yielding_vehicle_id"]],
                             index[item["priority_vehicle_id"]]) for item in edges),
        "edge_features": tuple(edges),
        "hard_constraint_evidence": {"cycle_detected": len(edges) == 4},
        "learning_features": {},
        "metadata": {"graph_scope": "JOINT_LOCAL_V2V",
                     "communication_model": "IDEAL_SAME_STEP_V2V"},
    }


def test_empty_graph_shapes_and_read_only_numpy_dtypes():
    encoded = GraphTensorEncoder().encode(observation(("A",), ()))
    assert encoded.node_features.shape == (1, len(NODE_NUMERIC_SCHEMA))
    assert encoded.node_feature_mask.shape == encoded.node_features.shape
    assert encoded.edge_index.shape == (2, 0)
    assert encoded.edge_features.shape == (0, len(EDGE_NUMERIC_SCHEMA))
    assert encoded.edge_feature_mask.shape == encoded.edge_features.shape
    assert encoded.node_features.dtype == np.float32
    assert encoded.node_feature_mask.dtype == np.bool_
    assert encoded.edge_index.dtype == np.int64
    assert encoded.edge_features.dtype == np.float32
    assert encoded.node_features.flags.writeable is False


@pytest.mark.parametrize("count", (1, 2, 3))
def test_variable_graph_sizes_without_padding(count):
    ids = tuple(chr(ord("A") + position) for position in range(count))
    edges = tuple(edge(ids[position], ids[position + 1])
                  for position in range(count - 1))
    encoded = GraphTensorEncoder().encode(observation(ids, edges))
    assert encoded.node_features.shape[0] == count
    assert encoded.edge_features.shape[0] == max(0, count - 1)


def test_four_node_cycle_has_exact_directed_edge_index_and_metadata():
    edges = tuple(edge(a, b, "COMMUNICATED") for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")
    ))
    encoded = GraphTensorEncoder().encode(observation(("A", "B", "C", "D"), edges))
    assert encoded.node_features.shape == (4, len(NODE_NUMERIC_SCHEMA))
    assert encoded.edge_features.shape == (4, len(EDGE_NUMERIC_SCHEMA))
    assert encoded.edge_index.tolist() == [[0, 1, 2, 3], [1, 2, 3, 0]]
    assert encoded.hard_constraint_metadata["cycle_detected"] is True


def test_canonical_encoding_is_input_order_invariant():
    first = observation(("C", "A", "B"), (
        edge("B", "C"), edge("A", "B"),
    ), features=(node(False, 3.0), node(True, 1.0), node(False, 2.0)))
    second = observation(("B", "C", "A"), (
        edge("A", "B"), edge("B", "C"),
    ), features=(node(False, 2.0), node(False, 3.0), node(True, 1.0)))
    a, b = GraphTensorEncoder().encode(first), GraphTensorEncoder().encode(second)
    assert a.node_ids == b.node_ids == ("A", "B", "C")
    for name in ("node_features", "node_feature_mask", "edge_index",
                 "edge_features", "edge_feature_mask"):
        assert np.array_equal(getattr(a, name), getattr(b, name))


def test_stopped_zero_and_unavailable_zero_are_distinguished_by_mask():
    encoded = GraphTensorEncoder().encode(observation(
        ("A", "B"), (), features=(node(True, speed=0.0), remote_node())
    ))
    speed_column = NODE_NUMERIC_SCHEMA.index("speed_mps")
    assert encoded.node_features[:, speed_column].tolist() == [0.0, 0.0]
    assert encoded.node_feature_mask[:, speed_column].tolist() == [True, False]


def test_v2v_only_participant_stays_masked_without_global_lookup():
    encoded = GraphTensorEncoder().encode(observation(
        ("A", "B", "C"), (edge("A", "B"), edge("B", "C", "COMMUNICATED", physical=False)),
        features=(node(True), node(False), remote_node()),
    ))
    assert encoded.node_features[2, 1:].tolist() == [0.0] * 7
    assert encoded.node_feature_mask[2, 1:].tolist() == [False] * 7
    availability = EDGE_NUMERIC_SCHEMA.index("physical_reachability_evidence_available")
    assert encoded.edge_features[1, availability] == 0.0
    assert encoded.edge_feature_mask[1, availability]


def test_relative_approach_multihot_and_origin_one_hot_are_nonordinal():
    encoded = GraphTensorEncoder().encode(observation(
        ("A", "B"), (edge("A", "B", "LOCAL_AND_COMMUNICATED",
                                 ("RIGHT", "ONCOMING")),)
    ))
    names = encoded.edge_feature_names
    assert encoded.edge_features[0, names.index("edge_origin__LOCAL_AND_COMMUNICATED")] == 1
    assert encoded.edge_features[0, names.index("relative_approach__RIGHT")] == 1
    assert encoded.edge_features[0, names.index("relative_approach__ONCOMING")] == 1
    assert encoded.categorical_encoding_metadata["relative_approaches"]["ordinal_meaning"] is False


def test_missing_relative_approach_is_zero_and_masked_not_guessed():
    encoded = GraphTensorEncoder().encode(observation(
        ("A", "B"), (edge("A", "B", relations=()),)
    ))
    columns = [index for index, name in enumerate(encoded.edge_feature_names)
               if name.startswith("relative_approach__")]
    assert encoded.edge_features[0, columns].tolist() == [0.0] * 4
    assert encoded.edge_feature_mask[0, columns].tolist() == [False] * 4


def test_nonfinite_available_feature_raises_explicit_error_and_counts_it():
    invalid = node(True); invalid["speed_mps"] = float("nan")
    encoder = GraphTensorEncoder()
    with pytest.raises(GraphTensorEncodingError, match="NONFINITE_AVAILABLE_FEATURE"):
        encoder.encode(observation(("A",), (), features=(invalid,)))
    assert encoder.validation_summary()["nonfinite_available_feature_errors"] == 1


def test_route_truth_and_prediction_probability_cannot_change_encoding():
    base = observation(("A", "B"), (edge("A", "B"),))
    changed = deepcopy(base)
    changed["route_id"] = "secret"; changed["route_index"] = 99
    changed["ground_truth_route_id"] = "secret_truth"
    changed["intention_probabilities"] = {"RIGHT": 0.001}
    a, b = GraphTensorEncoder().encode(base), GraphTensorEncoder().encode(changed)
    for name in ("node_features", "node_feature_mask", "edge_index",
                 "edge_features", "edge_feature_mask"):
        assert np.array_equal(getattr(a, name), getattr(b, name))


def test_tensor_package_has_no_tensorflow_pytorch_or_control_side_effects(monkeypatch):
    package = Path(__file__).parents[1] / "negotiation_learning" / "tensor_encoding"
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in package.glob("*.py"))
    forbidden_imports = ("import tensorflow", "from tensorflow", "import keras",
                         "from keras", "import torch", "from torch")
    assert not any(value in source for value in forbidden_imports)
    calls = []
    try:
        import traci
        monkeypatch.setattr(traci.vehicle, "setSpeed", lambda *args: calls.append(args))
    except Exception:
        pass
    GraphTensorEncoder().encode(observation(("A",), ()))
    assert calls == []
