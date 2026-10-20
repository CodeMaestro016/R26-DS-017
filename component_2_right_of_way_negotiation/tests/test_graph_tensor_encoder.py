"""Deterministic NumPy-only GNN-input encoding tests."""

# Import deepcopy from copy for the operations below.
from copy import deepcopy
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest

# Import EDGE_NUMERIC_SCHEMA, GraphTensorEncoder, GraphTensorEncodingError, NODE_NUMERIC_SCHEMA from
# negotiation_learning.tensor_encoding for the operations below.
from negotiation_learning.tensor_encoding import (
    EDGE_NUMERIC_SCHEMA, GraphTensorEncoder, GraphTensorEncodingError,
    NODE_NUMERIC_SCHEMA,
)


# Node using the inputs and processing steps below.
# Input is_ego: the supplied is ego.
# Input speed: the supplied speed.
# Input observed: the supplied observed.
# Output: a dictionary containing is_ego, speed_mps, max_acceleration_mps2, comfortable_deceleration_mps2,...
def node(is_ego=False, speed=3.0, observed=True):
    # Return a dictionary containing is_ego, speed_mps, max_acceleration_mps2, comfortable_deceleration_mps2,...
    # to the caller.
    return {
        # Store is_ego under 'is_ego'.
        # Store speed under 'speed_mps'.
        "is_ego": is_ego, "speed_mps": speed,
        # Store 2.0 under 'max_acceleration_mps2'.
        "max_acceleration_mps2": 2.0,
        # Store 4.5 under 'comfortable_deceleration_mps2'.
        "comfortable_deceleration_mps2": 4.5,
        # Store 13.89 under 'max_speed_mps'.
        "max_speed_mps": 13.89,
        # Store 1.0 under 'observation_confidence'.
        "observation_confidence": 1.0,
        # Store observed under 'is_currently_observed'.
        "is_currently_observed": observed,
        # Store 0.0 under 'observation_age_seconds'.
        "observation_age_seconds": 0.0,
    }


# Remote node using the inputs and processing steps below.
# Output: a dictionary containing is_ego, speed_mps, max_acceleration_mps2, comfortable_deceleration_mps2,...
def remote_node():
    # Return a dictionary containing is_ego, speed_mps, max_acceleration_mps2, comfortable_deceleration_mps2,...
    # to the caller.
    return {
        # Store False under 'is_ego'.
        # Store None under 'speed_mps'.
        "is_ego": False, "speed_mps": None,
        # Store None under 'max_acceleration_mps2'.
        "max_acceleration_mps2": None,
        # Store None under 'comfortable_deceleration_mps2'.
        "comfortable_deceleration_mps2": None,
        # Store None under 'max_speed_mps'.
        # Store None under 'observation_confidence'.
        "max_speed_mps": None, "observation_confidence": None,
        # Store None under 'is_currently_observed'.
        # Store None under 'observation_age_seconds'.
        "is_currently_observed": None, "observation_age_seconds": None,
    }


# Edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Input origin: the supplied origin.
# Input relations: the supplied relations.
# Input physical: the supplied physical.
# Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id, edge_origin, relative_approaches,...
def edge(source, target, origin="LOCAL", relations=("RIGHT",), physical=True):
    # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id, edge_origin,
    # relative_approaches,... to the caller.
    return {
        # Store source under 'yielding_vehicle_id'.
        # Store target under 'priority_vehicle_id'.
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        # Store origin under 'edge_origin'.
        # Store relations under 'relative_approaches'.
        "edge_origin": origin, "relative_approaches": relations,
        # Store a dictionary containing temporal_conflict_possible, evaluations when physical, otherwise None
        # under 'physical_reachability_evidence'.
        "physical_reachability_evidence": ({
            # Store False under 'temporal_conflict_possible'.
            "temporal_conflict_possible": False,
            # Store a tuple containing a dictionary containing target_earliest_reachable_entry_time_s under
            # 'evaluations'.
            # Store 2.0 under 'target_earliest_reachable_entry_time_s'.
            "evaluations": ({"target_earliest_reachable_entry_time_s": 2.0},),
        # Evaluate physical as part of the enclosing expression.
        } if physical else None),
        # Store a tuple containing the text 'DE-STVO-8-1' under 'applicable_rule_ids'.
        "applicable_rule_ids": ("DE-STVO-8-1",),
        # Store a tuple containing the text '§ 8' under 'source_sections'.
        # Store the text 'PROFILE' under 'regulatory_profile'.
        "source_sections": ("§ 8",), "regulatory_profile": "PROFILE",
        # Store a tuple containing the text 'ZONE_ID' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ("ZONE_ID",),
        # Store a tuple containing the text 'PATH_ID' under 'target_candidate_path_ids'.
        "target_candidate_path_ids": ("PATH_ID",),
        # Store a tuple containing the text 'CROSSING' under 'conflict_types'.
        "conflict_types": ("CROSSING",),
    }


# Observation using the inputs and processing steps below.
# Input node_ids: the supplied node ids.
# Input edges: the supplied edges.
# Input features: the supplied features.
# Output: a dictionary containing ego_id, node_ids, node_features, edge_index, edge_features,
# hard_constraint_evidence,...
def observation(node_ids, edges, features=None):
    # Set features to features or a tuple built from a lazy sequence of the result of node(node_id == node_ids[0])
    # for node_id in node_ids.
    features = features or tuple(
        # Evaluate the result of node(node_id equals node_ids at 0) as part of the enclosing expression.
        node(node_id == node_ids[0]) for node_id in node_ids
    )
    # Set index to a dictionary of name mapped to position for (position, name) in index/value pairs from
    # node_ids.
    index = {name: position for position, name in enumerate(node_ids)}
    # Return a dictionary containing ego_id, node_ids, node_features, edge_index, edge_features,
    # hard_constraint_evidence,... to the caller.
    return {
        # Store node_ids at 0 under 'ego_id'.
        # Store a tuple built from node_ids under 'node_ids'.
        "ego_id": node_ids[0], "node_ids": tuple(node_ids),
        # Store a tuple built from features under 'node_features'.
        "node_features": tuple(features),
        # Store a tuple built from a lazy sequence of a tuple containing index at item['yielding_vehicle_id'],
        # index at item['priority_vehicle_id'] for item in edges under 'edge_index'.
        "edge_index": tuple((index[item["yielding_vehicle_id"]],
                             # Include index at item['priority_vehicle_id'] in this tuple.
                             index[item["priority_vehicle_id"]]) for item in edges),
        # Store a tuple built from edges under 'edge_features'.
        "edge_features": tuple(edges),
        # Store a dictionary containing cycle_detected under 'hard_constraint_evidence'.
        # Store the number of entries in edges equals 4 under 'cycle_detected'.
        "hard_constraint_evidence": {"cycle_detected": len(edges) == 4},
        # Store an empty dictionary under 'learning_features'.
        "learning_features": {},
        # Store a dictionary containing graph_scope, communication_model under 'metadata'.
        # Store the text 'JOINT_LOCAL_V2V' under 'graph_scope'.
        "metadata": {"graph_scope": "JOINT_LOCAL_V2V",
                     "communication_model": "IDEAL_SAME_STEP_V2V"},
    }


# Check empty graph shapes and read only numpy dtypes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_empty_graph_shapes_and_read_only_numpy_dtypes():
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', an empty tuple)).
    encoded = GraphTensorEncoder().encode(observation(("A",), ()))
    # Require encoded.node_features.shape equals a tuple containing 1, the number of entries in
    # NODE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.node_features.shape == (1, len(NODE_NUMERIC_SCHEMA))
    # Require encoded.node_feature_mask.shape equals encoded.node_features.shape; otherwise raise AssertionError.
    assert encoded.node_feature_mask.shape == encoded.node_features.shape
    # Require encoded.edge_index.shape equals a tuple containing 2, 0; otherwise raise AssertionError.
    assert encoded.edge_index.shape == (2, 0)
    # Require encoded.edge_features.shape equals a tuple containing 0, the number of entries in
    # EDGE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.edge_features.shape == (0, len(EDGE_NUMERIC_SCHEMA))
    # Require encoded.edge_feature_mask.shape equals encoded.edge_features.shape; otherwise raise AssertionError.
    assert encoded.edge_feature_mask.shape == encoded.edge_features.shape
    # Require encoded.node_features.dtype equals np.float32; otherwise raise AssertionError.
    assert encoded.node_features.dtype == np.float32
    # Require encoded.node_feature_mask.dtype equals np.bool_; otherwise raise AssertionError.
    assert encoded.node_feature_mask.dtype == np.bool_
    # Require encoded.edge_index.dtype equals np.int64; otherwise raise AssertionError.
    assert encoded.edge_index.dtype == np.int64
    # Require encoded.edge_features.dtype equals np.float32; otherwise raise AssertionError.
    assert encoded.edge_features.dtype == np.float32
    # Require encoded.node_features.flags.writeable is the same object as False; otherwise raise AssertionError.
    assert encoded.node_features.flags.writeable is False


# Apply pytest.mark.parametrize('count', (1, 2, 3)) as a decorator to configure the following definition.
@pytest.mark.parametrize("count", (1, 2, 3))
# Check variable graph sizes without padding using the setup, calls, and assertions below.
# Input count: the supplied count.
# Output: no explicit value; normal completion returns None.
def test_variable_graph_sizes_without_padding(count):
    # Set ids to a tuple built from a lazy sequence of the result of chr(ord('A') plus position) for position in
    # the integer range defined by count.
    ids = tuple(chr(ord("A") + position) for position in range(count))
    # Set edges to a tuple built from a lazy sequence of the result of edge(ids at position, ids at position + 1)
    # for position in the integer range defined by count minus 1.
    edges = tuple(edge(ids[position], ids[position + 1])
                  # Evaluate the integer range defined by count minus 1 as part of the enclosing expression.
                  for position in range(count - 1))
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(ids, edges)).
    encoded = GraphTensorEncoder().encode(observation(ids, edges))
    # Require encoded.node_features.shape at 0 equals count; otherwise raise AssertionError.
    assert encoded.node_features.shape[0] == count
    # Require encoded.edge_features.shape at 0 equals the maximum of 0, count minus 1; otherwise raise
    # AssertionError.
    assert encoded.edge_features.shape[0] == max(0, count - 1)


# Check four node cycle has exact directed edge index and metadata using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_four_node_cycle_has_exact_directed_edge_index_and_metadata():
    # Set edges to a tuple built from a lazy sequence of the result of edge(a, b, the text 'COMMUNICATED') for (a,
    # b) in a tuple containing a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C',
    # 'D', a tuple containing...
    edges = tuple(edge(a, b, "COMMUNICATED") for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")
    ))
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', the text 'B', the text 'C', the text...).
    encoded = GraphTensorEncoder().encode(observation(("A", "B", "C", "D"), edges))
    # Require encoded.node_features.shape equals a tuple containing 4, the number of entries in
    # NODE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.node_features.shape == (4, len(NODE_NUMERIC_SCHEMA))
    # Require encoded.edge_features.shape equals a tuple containing 4, the number of entries in
    # EDGE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.edge_features.shape == (4, len(EDGE_NUMERIC_SCHEMA))
    # Require the result of encoded.edge_index.tolist() equals a list containing a list containing 0, 1, 2, 3, a
    # list containing 1, 2, 3, 0; otherwise raise AssertionError.
    assert encoded.edge_index.tolist() == [[0, 1, 2, 3], [1, 2, 3, 0]]
    # Require encoded.hard_constraint_metadata at 'cycle_detected' is the same object as True; otherwise raise
    # AssertionError.
    assert encoded.hard_constraint_metadata["cycle_detected"] is True


# Check canonical encoding is input order invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_canonical_encoding_is_input_order_invariant():
    # Set first to the result of observation(a tuple containing the text 'C', the text 'A', the text 'B', a tuple
    # containing the result of...).
    first = observation(("C", "A", "B"), (
        # Include the result of edge(the text 'B', the text 'C') in this tuple.
        edge("B", "C"), edge("A", "B"),
    # Supply features as a tuple containing the result of node(False, 3.0), the result of node(True, 1.0), the
    # result of node(False, 2.0).
    ), features=(node(False, 3.0), node(True, 1.0), node(False, 2.0)))
    # Set second to the result of observation(a tuple containing the text 'B', the text 'C', the text 'A', a tuple
    # containing the result of...).
    second = observation(("B", "C", "A"), (
        # Include the result of edge(the text 'A', the text 'B') in this tuple.
        edge("A", "B"), edge("B", "C"),
    # Supply features as a tuple containing the result of node(False, 2.0), the result of node(False, 3.0), the
    # result of node(True, 1.0).
    ), features=(node(False, 2.0), node(False, 3.0), node(True, 1.0)))
    # Set (a, b) to a tuple containing the result of GraphTensorEncoder().encode(first), the result of
    # GraphTensorEncoder().encode(second).
    a, b = GraphTensorEncoder().encode(first), GraphTensorEncoder().encode(second)
    # Require a.node_ids equals b.node_ids; equals a tuple containing the text 'A', the text 'B', the text 'C';
    # otherwise raise AssertionError.
    assert a.node_ids == b.node_ids == ("A", "B", "C")
    # Iterate over a tuple containing the text 'node_features', the text 'node_feature_mask', the text
    # 'edge_index', the text 'edge_features',..., binding each item to name.
    for name in ("node_features", "node_feature_mask", "edge_index",
                 "edge_features", "edge_feature_mask"):
        # Require the result of np.array_equal(the requested attribute of a, the requested attribute of b);
        # otherwise raise AssertionError.
        assert np.array_equal(getattr(a, name), getattr(b, name))


# Check stopped zero and unavailable zero are distinguished by mask using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_stopped_zero_and_unavailable_zero_are_distinguished_by_mask():
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', the text 'B', an empty tuple)).
    encoded = GraphTensorEncoder().encode(observation(
        # Supply features as a tuple containing the result of node(True), the result of remote_node().
        # Supply speed as 0.0.
        ("A", "B"), (), features=(node(True, speed=0.0), remote_node())
    ))
    # Set speed_column to the result of NODE_NUMERIC_SCHEMA.index(the text 'speed_mps').
    speed_column = NODE_NUMERIC_SCHEMA.index("speed_mps")
    # Require the result of encoded.node_features[:, speed_column].tolist() equals a list containing 0.0, 0.0;
    # otherwise raise AssertionError.
    assert encoded.node_features[:, speed_column].tolist() == [0.0, 0.0]
    # Require the result of encoded.node_feature_mask[:, speed_column].tolist() equals a list containing True,
    # False; otherwise raise AssertionError.
    assert encoded.node_feature_mask[:, speed_column].tolist() == [True, False]


# Check v2v only participant stays masked without global lookup using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_v2v_only_participant_stays_masked_without_global_lookup():
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', the text 'B', the text 'C', a tuple...).
    encoded = GraphTensorEncoder().encode(observation(
        # Supply physical as False.
        ("A", "B", "C"), (edge("A", "B"), edge("B", "C", "COMMUNICATED", physical=False)),
        # Supply features as a tuple containing the result of node(True), the result of node(False), the result of
        # remote_node().
        features=(node(True), node(False), remote_node()),
    ))
    # Require the result of encoded.node_features[2, 1:].tolist() equals a list containing 0.0 multiplied by 7;
    # otherwise raise AssertionError.
    assert encoded.node_features[2, 1:].tolist() == [0.0] * 7
    # Require the result of encoded.node_feature_mask[2, 1:].tolist() equals a list containing False multiplied by
    # 7; otherwise raise AssertionError.
    assert encoded.node_feature_mask[2, 1:].tolist() == [False] * 7
    # Set availability to the result of EDGE_NUMERIC_SCHEMA.index(the text
    # 'physical_reachability_evidence_available').
    availability = EDGE_NUMERIC_SCHEMA.index("physical_reachability_evidence_available")
    # Require encoded.edge_features at (1, availability) equals 0.0; otherwise raise AssertionError.
    assert encoded.edge_features[1, availability] == 0.0
    # Require encoded.edge_feature_mask at (1, availability); otherwise raise AssertionError.
    assert encoded.edge_feature_mask[1, availability]


# Check relative approach multihot and origin one hot are nonordinal using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_relative_approach_multihot_and_origin_one_hot_are_nonordinal():
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', the text 'B', a tuple containing the...).
    encoded = GraphTensorEncoder().encode(observation(
        # Supply a tuple containing the result of edge(the text 'A', the text 'B', the text
        # 'LOCAL_AND_COMMUNICATED', a tuple containing the... to observation.
        ("A", "B"), (edge("A", "B", "LOCAL_AND_COMMUNICATED",
                                 # Supply a tuple containing the text 'RIGHT', the text 'ONCOMING' to edge.
                                 ("RIGHT", "ONCOMING")),)
    ))
    # Set names to encoded.edge_feature_names.
    names = encoded.edge_feature_names
    # Require encoded.edge_features at (0, names.index('edge_origin__LOCAL_AND_COMMUNICATED')) equals 1; otherwise
    # raise AssertionError.
    assert encoded.edge_features[0, names.index("edge_origin__LOCAL_AND_COMMUNICATED")] == 1
    # Require encoded.edge_features at (0, names.index('relative_approach__RIGHT')) equals 1; otherwise raise
    # AssertionError.
    assert encoded.edge_features[0, names.index("relative_approach__RIGHT")] == 1
    # Require encoded.edge_features at (0, names.index('relative_approach__ONCOMING')) equals 1; otherwise raise
    # AssertionError.
    assert encoded.edge_features[0, names.index("relative_approach__ONCOMING")] == 1
    # Require encoded.categorical_encoding_metadata['relative_approaches'] at 'ordinal_meaning' is the same object
    # as False; otherwise raise AssertionError.
    assert encoded.categorical_encoding_metadata["relative_approaches"]["ordinal_meaning"] is False


# Check missing relative approach is zero and masked not guessed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_missing_relative_approach_is_zero_and_masked_not_guessed():
    # Set encoded to the result of GraphTensorEncoder().encode(the result of observation(a tuple containing the
    # text 'A', the text 'B', a tuple containing the...).
    encoded = GraphTensorEncoder().encode(observation(
        # Supply relations as an empty tuple.
        ("A", "B"), (edge("A", "B", relations=()),)
    ))
    # Set columns to a list of index for (index, name) in index/value pairs from encoded.edge_feature_names;
    # retain entries satisfying the result of name.startswith(the text 'relative_approach__').
    columns = [index for index, name in enumerate(encoded.edge_feature_names)
               # Evaluate the result of name.startswith(the text 'relative_approach__') as part of the enclosing
               # expression.
               if name.startswith("relative_approach__")]
    # Require the result of encoded.edge_features[0, columns].tolist() equals a list containing 0.0 multiplied by
    # 4; otherwise raise AssertionError.
    assert encoded.edge_features[0, columns].tolist() == [0.0] * 4
    # Require the result of encoded.edge_feature_mask[0, columns].tolist() equals a list containing False
    # multiplied by 4; otherwise raise AssertionError.
    assert encoded.edge_feature_mask[0, columns].tolist() == [False] * 4


# Check nonfinite available feature raises explicit error and counts it using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_nonfinite_available_feature_raises_explicit_error_and_counts_it():
    # Set invalid to the result of node(True).
    # Set invalid['speed_mps'] to a floating-point number built from the text 'nan'.
    invalid = node(True); invalid["speed_mps"] = float("nan")
    # Set encoder to the result of GraphTensorEncoder().
    encoder = GraphTensorEncoder()
    # Enter the result of pytest.raises(GraphTensorEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(GraphTensorEncodingError, match="NONFINITE_AVAILABLE_FEATURE"):
        # Call encoder.encode with the supplied arguments.
        encoder.encode(observation(("A",), (), features=(invalid,)))
    # Require encoder.validation_summary() at 'nonfinite_available_feature_errors' equals 1; otherwise raise
    # AssertionError.
    assert encoder.validation_summary()["nonfinite_available_feature_errors"] == 1


# Check route truth and prediction probability cannot change encoding using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_route_truth_and_prediction_probability_cannot_change_encoding():
    # Set base to the result of observation(a tuple containing the text 'A', the text 'B', a tuple containing the
    # result of edge(the text...).
    base = observation(("A", "B"), (edge("A", "B"),))
    # Set changed to the result of deepcopy(base).
    changed = deepcopy(base)
    # Set changed['route_id'] to the text 'secret'.
    # Set changed['route_index'] to 99.
    changed["route_id"] = "secret"; changed["route_index"] = 99
    # Set changed['ground_truth_route_id'] to the text 'secret_truth'.
    changed["ground_truth_route_id"] = "secret_truth"
    # Set changed['intention_probabilities'] to a dictionary containing RIGHT.
    changed["intention_probabilities"] = {"RIGHT": 0.001}
    # Set (a, b) to a tuple containing the result of GraphTensorEncoder().encode(base), the result of
    # GraphTensorEncoder().encode(changed).
    a, b = GraphTensorEncoder().encode(base), GraphTensorEncoder().encode(changed)
    # Iterate over a tuple containing the text 'node_features', the text 'node_feature_mask', the text
    # 'edge_index', the text 'edge_features',..., binding each item to name.
    for name in ("node_features", "node_feature_mask", "edge_index",
                 "edge_features", "edge_feature_mask"):
        # Require the result of np.array_equal(the requested attribute of a, the requested attribute of b);
        # otherwise raise AssertionError.
        assert np.array_equal(getattr(a, name), getattr(b, name))


# Check tensor package has no tensorflow pytorch or control side effects using the setup, calls, and assertions
# below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_tensor_package_has_no_tensorflow_pytorch_or_control_side_effects(monkeypatch):
    # Set package to Path(__file__).parents at 1 joined with the path segment 'negotiation_learning' joined with the path segment
    # 'tensor_encoding'.
    package = Path(__file__).parents[1] / "negotiation_learning" / "tensor_encoding"
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of package.glob(the text '*.py') as part of the enclosing expression.
                       for path in package.glob("*.py"))
    # Set forbidden_imports to a tuple containing the text 'import tensorflow', the text 'from tensorflow', the
    # text 'import keras', the text 'from keras',...
    forbidden_imports = ("import tensorflow", "from tensorflow", "import keras",
                         "from keras", "import torch", "from torch")
    # Require the negation of whether any item is true in a lazy sequence of value belongs to source for value in
    # forbidden_imports; otherwise raise AssertionError.
    assert not any(value in source for value in forbidden_imports)
    # Set calls to an empty list.
    calls = []
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Import traci for use in this module.
        import traci
        # Call monkeypatch.setattr with the supplied arguments.
        monkeypatch.setattr(traci.vehicle, "setSpeed", lambda *args: calls.append(args))
    # Handle Exception using the recovery steps below.
    except Exception:
        # Keep this block syntactically valid without performing an operation.
        pass
    # Call GraphTensorEncoder().encode with the supplied arguments.
    GraphTensorEncoder().encode(observation(("A",), ()))
    # Require calls equals an empty list; otherwise raise AssertionError.
    assert calls == []
