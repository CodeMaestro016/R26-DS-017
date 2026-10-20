"""CPU-only edge-aware MPNN forward and gradient validation."""

# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import EdgeAwareMPNNEncoder, to_torch_graph from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
# Import EdgeAwareMessagePassingLayer from negotiation_learning.gnn.message_passing for the operations below.
from negotiation_learning.gnn.message_passing import EdgeAwareMessagePassingLayer
# Import EncodedGraphObservation from negotiation_learning.tensor_encoding.models for the operations below.
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
# Import CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from
# negotiation_learning.tensor_encoding.schemas for the operations below.
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


# Set TEST_REPRODUCIBILITY_SEED to 20260812.
TEST_REPRODUCIBILITY_SEED = 20260812
# Set TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM to 16.
TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM = 16
# Set TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS to 2.
TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS = 2


# Encoded using the inputs and processing steps below.
# Input node_ids: the supplied node ids.
# Input edges: the supplied edges.
# Input ego_id: the identifier of the ego vehicle.
# Input node_values: the supplied node values.
# Input node_masks: the supplied node masks.
# Input edge_values: the supplied edge values.
# Input edge_masks: the supplied edge masks.
# Output: the result of EncodedGraphObservation(ego_id, a tuple built from node_ids, node_values, node_masks,
# edge_index, edge_values,...).
def encoded(node_ids, edges, ego_id="A", node_values=None, node_masks=None,
            # Declare edge_values, edge_masks as input parameters.
            edge_values=None, edge_masks=None):
    # Set (n, m) to a tuple containing the number of entries in node_ids, the number of entries in edges.
    n, m = len(node_ids), len(edges)
    # Set node_values to a zero-filled tensor with the requested shape when node_values is the same object as
    # None, otherwise node_values.
    node_values = (np.zeros((n, len(NODE_NUMERIC_SCHEMA)), np.float32)
                   # Evaluate node_values is the same object as None as part of the enclosing expression.
                   if node_values is None else node_values)
    # Set node_masks to the result of np.ones_like(node_values) when node_masks is the same object as None,
    # otherwise node_masks.
    node_masks = (np.ones_like(node_values, dtype=np.bool_)
                  # Evaluate node_masks is the same object as None as part of the enclosing expression.
                  if node_masks is None else node_masks)
    # Set edge_values to a zero-filled tensor with the requested shape when edge_values is the same object as
    # None, otherwise edge_values.
    edge_values = (np.zeros((m, len(EDGE_NUMERIC_SCHEMA)), np.float32)
                   # Evaluate edge_values is the same object as None as part of the enclosing expression.
                   if edge_values is None else edge_values)
    # Set edge_masks to the result of np.ones_like(edge_values) when edge_masks is the same object as None,
    # otherwise edge_masks.
    edge_masks = (np.ones_like(edge_values, dtype=np.bool_)
                  # Evaluate edge_masks is the same object as None as part of the enclosing expression.
                  if edge_masks is None else edge_masks)
    # Set index to a dictionary of name mapped to position for (position, name) in index/value pairs from
    # node_ids.
    index = {name: position for position, name in enumerate(node_ids)}
    # Set edge_index to np.asarray([(index[source], index[target]) for source, target in edges],...
    edge_index = np.asarray(
        # Supply a list of a tuple containing index at source, index at target for (source, target) in edges to
        # np.asarray.
        [(index[source], index[target]) for source, target in edges],
        # Supply dtype as np.int64.
        dtype=np.int64,
    # Supply the negative of 1 to np.asarray([(index[source], index[target]) for source, target in edges],
    # dtype=np.int64).reshape.
    ).reshape(-1, 2).T
    # Return the result of EncodedGraphObservation(ego_id, a tuple built from node_ids, node_values, node_masks,
    # edge_index, edge_values,...) to the caller.
    return EncodedGraphObservation(
        # Supply a tuple built from node_ids to EncodedGraphObservation.
        ego_id, tuple(node_ids), node_values, node_masks, edge_index,
        # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


# Apply pytest.fixture as a decorator to configure the following definition.
@pytest.fixture
# Model using the inputs and processing steps below.
# Output: the result of EdgeAwareMPNNEncoder(len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),...().
def model():
    # Call torch.manual_seed with the supplied arguments.
    torch.manual_seed(TEST_REPRODUCIBILITY_SEED)
    # Return the result of EdgeAwareMPNNEncoder(len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),...() to the
    # caller.
    return EdgeAwareMPNNEncoder(
        # Supply the number of entries in NODE_NUMERIC_SCHEMA to EdgeAwareMPNNEncoder.
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        # Supply TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        # Supply TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS,
    ).eval()


# Assert shapes using the inputs and processing steps below.
# Input output: the supplied output.
# Input nodes: the supplied nodes.
# Output: no explicit value; normal completion returns None.
def assert_shapes(output, nodes):
    # Require output.node_embeddings.shape equals a tuple containing nodes, TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM;
    # otherwise raise AssertionError.
    assert output.node_embeddings.shape == (
        # Include TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM in this tuple.
        nodes, TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM
    )
    # Require output.ego_embedding.shape equals a tuple containing TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM; otherwise
    # raise AssertionError.
    assert output.ego_embedding.shape == (TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,)
    # Require output.graph_embedding.shape equals a tuple containing TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM;
    # otherwise raise AssertionError.
    assert output.graph_embedding.shape == (TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,)
    # Require the result of torch.isfinite(output.node_embeddings).all(); otherwise raise AssertionError.
    assert torch.isfinite(output.node_embeddings).all()


# Check one node zero edge without self loop using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_one_node_zero_edge_without_self_loop(model):
    # Set graph to the result of to_torch_graph(the result of encoded(a tuple containing the text 'A', an empty
    # tuple)).
    graph = to_torch_graph(encoded(("A",), ()))
    # Require graph.edge_index.shape equals a tuple containing 2, 0; otherwise raise AssertionError.
    assert graph.edge_index.shape == (2, 0)
    # Set output to the result of model(graph).
    output = model(graph)
    # Call assert_shapes with the supplied arguments.
    assert_shapes(output, 1)


# Check two node edge preserves yielding to priority direction using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_two_node_edge_preserves_yielding_to_priority_direction(model):
    # Set graph to the result of to_torch_graph(the result of encoded(a tuple containing the text 'A', the text
    # 'B', a tuple containing a tuple...).
    graph = to_torch_graph(encoded(("A", "B"), (("A", "B"),)))
    # Require the result of graph.edge_index.tolist() equals a list containing a list containing 0, a list
    # containing 1; otherwise raise AssertionError.
    assert graph.edge_index.tolist() == [[0], [1]]
    # Call assert_shapes with the supplied arguments.
    assert_shapes(model(graph), 2)


# Check four node cycle forward is finite using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_four_node_cycle_forward_is_finite(model):
    # Set graph to the result of encoded(a tuple containing the text 'A', the text 'B', the text 'C', the text
    # 'D', a tuple containing a...).
    graph = encoded(("A", "B", "C", "D"), (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Call assert_shapes with the supplied arguments.
    assert_shapes(model(to_torch_graph(graph)), 4)


# Check masks preserve real zero vs unavailable zero using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_masks_preserve_real_zero_vs_unavailable_zero():
    # Set values to a zero-filled tensor with the requested shape.
    values = np.zeros((2, len(NODE_NUMERIC_SCHEMA)), np.float32)
    # Set masks to the result of np.ones_like(values).
    masks = np.ones_like(values, dtype=np.bool_)
    # Set speed to the result of NODE_NUMERIC_SCHEMA.index(the text 'speed_mps').
    speed = NODE_NUMERIC_SCHEMA.index("speed_mps")
    # Set masks[1, speed] to False.
    masks[1, speed] = False
    # Set graph to the result of to_torch_graph(the result of encoded(a tuple containing the text 'A', the text
    # 'B', an empty tuple)).
    graph = to_torch_graph(encoded(("A", "B"), (), node_values=values,
                                   # Supply node_masks as masks.
                                   node_masks=masks))
    # Set combined to the tensors concatenated by torch.cat.
    combined = torch.cat((graph.node_features,
                          # Supply dim as the negative of 1.
                          graph.node_feature_mask.float()), dim=-1)
    # Require combined at (0, speed) equals combined at (1, speed); equals 0; otherwise raise AssertionError.
    assert combined[0, speed] == combined[1, speed] == 0
    # Require combined at (0, speed + len(NODE_NUMERIC_SCHEMA)) equals 1; otherwise raise AssertionError.
    assert combined[0, speed + len(NODE_NUMERIC_SCHEMA)] == 1
    # Require combined at (1, speed + len(NODE_NUMERIC_SCHEMA)) equals 0; otherwise raise AssertionError.
    assert combined[1, speed + len(NODE_NUMERIC_SCHEMA)] == 0


# Check edge missing evidence mask is preserved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_edge_missing_evidence_mask_is_preserved():
    # Set values to a zero-filled tensor with the requested shape.
    values = np.zeros((1, len(EDGE_NUMERIC_SCHEMA)), np.float32)
    # Set masks to the result of np.ones_like(values).
    masks = np.ones_like(values, dtype=np.bool_)
    # Set temporal to the result of EDGE_NUMERIC_SCHEMA.index(the text 'temporal_conflict_possible').
    temporal = EDGE_NUMERIC_SCHEMA.index("temporal_conflict_possible")
    # Set masks[0, temporal] to False.
    masks[0, temporal] = False
    # Set graph to the result of to_torch_graph(the result of encoded(a tuple containing the text 'A', the text
    # 'B', a tuple containing a tuple...).
    graph = to_torch_graph(encoded(("A", "B"), (("A", "B"),),
                                   # Supply edge_values as values.
                                   # Supply edge_masks as masks.
                                   edge_values=values, edge_masks=masks))
    # Require graph.edge_features at (0, temporal) equals 0; otherwise raise AssertionError.
    assert graph.edge_features[0, temporal] == 0
    # Require graph.edge_feature_mask at (0, temporal) equals 0; otherwise raise AssertionError.
    assert graph.edge_feature_mask[0, temporal] == 0


# Check node order permutation preserves graph and ego embeddings using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_node_order_permutation_preserves_graph_and_ego_embeddings(model):
    # Set values to the result of np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, the
    # negative of 1).
    values = np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, -1)
    # Set first to the result of encoded(a tuple containing the text 'A', the text 'B', the text 'C', a tuple
    # containing a tuple...).
    first = encoded(("A", "B", "C"), (("A", "B"), ("B", "C")),
                    # Supply node_values as values.
                    node_values=values)
    # Set second to the result of encoded(a tuple containing the text 'C', the text 'A', the text 'B', a tuple
    # containing a tuple...).
    second = encoded(("C", "A", "B"), (("B", "C"), ("A", "B")),
                     # Supply node_values as values at [2, 0, 1].
                     node_values=values[[2, 0, 1]])
    # Set (a, b) to a tuple containing the result of model(the result of to_torch_graph(first)), the result of
    # model(the result of...
    a, b = model(to_torch_graph(first)), model(to_torch_graph(second))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(a.graph_embedding, b.graph_embedding)
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(a.ego_embedding, b.ego_embedding)


# Check edge order permutation preserves outputs using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_edge_order_permutation_preserves_outputs(model):
    # Set edge_values to the result of np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, the
    # negative of 1).
    edge_values = np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, -1)
    # Set first to the result of encoded(a tuple containing the text 'A', the text 'B', the text 'C', a tuple
    # containing a tuple...).
    first = encoded(("A", "B", "C"), (("A", "C"), ("B", "C")),
                    # Supply edge_values as edge_values.
                    edge_values=edge_values)
    # Set second to the result of encoded(a tuple containing the text 'A', the text 'B', the text 'C', a tuple
    # containing a tuple...).
    second = encoded(("A", "B", "C"), (("B", "C"), ("A", "C")),
                     # Supply edge_values as edge_values at [1, 0].
                     edge_values=edge_values[[1, 0]])
    # Set (a, b) to a tuple containing the result of model(the result of to_torch_graph(first)), the result of
    # model(the result of...
    a, b = model(to_torch_graph(first)), model(to_torch_graph(second))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(a.node_embeddings, b.node_embeddings)
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(a.graph_embedding, b.graph_embedding)


# Check ego is selected by identity when not first using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_ego_is_selected_by_identity_when_not_first(model):
    # Set output to the result of model(the result of to_torch_graph(the result of encoded(a tuple containing 'B',
    # 'A', 'C', an empty...).
    output = model(to_torch_graph(encoded(("B", "A", "C"), (), ego_id="A")))
    # Require output.ego_node_index equals 1; otherwise raise AssertionError.
    assert output.ego_node_index == 1
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(output.ego_embedding, output.node_embeddings[1])


# Check cpu device and finite gradient flow using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_cpu_device_and_finite_gradient_flow(model):
    # Require next(model.parameters()).device.type equals the text 'cpu'; otherwise raise AssertionError.
    assert next(model.parameters()).device.type == "cpu"
    # Set output to the result of model(the result of to_torch_graph(the result of encoded(a tuple containing 'A',
    # 'B', a tuple...).
    output = model(to_torch_graph(encoded(("A", "B"), (("A", "B"),))))
    # Set unit_test_only_gradient_scalar to the result of output.node_embeddings.sum().
    unit_test_only_gradient_scalar = output.node_embeddings.sum()
    # Backpropagate gradients from unit_test_only_gradient_scalar.
    unit_test_only_gradient_scalar.backward()
    # Require output.device equals the text 'cpu'; otherwise raise AssertionError.
    assert output.device == "cpu"
    # Require whether every item is true in a lazy sequence of parameter.grad is a different object from None and
    # the result of torch.isfinite(parameter.grad).all() for parameter in the result of model.parameters();
    # otherwise raise AssertionError.
    assert all(parameter.grad is not None and torch.isfinite(parameter.grad).all()
               # Evaluate the result of model.parameters() as part of the enclosing expression.
               for parameter in model.parameters())


# Check route truth outside encoded graph cannot affect output using the setup, calls, and assertions below.
# Input model: the supplied model.
# Output: no explicit value; normal completion returns None.
def test_route_truth_outside_encoded_graph_cannot_affect_output(model):
    # Set graph to the result of encoded(a tuple containing the text 'A', the text 'B', a tuple containing a tuple
    # containing the text...).
    graph = encoded(("A", "B"), (("A", "B"),))
    # Set output_before to model(to_torch_graph(graph)).graph_embedding.
    output_before = model(to_torch_graph(graph)).graph_embedding
    # Set external_truth to a dictionary containing route_id, route_index, ground_truth_route_id.
    external_truth = {"route_id": "x", "route_index": 99,
                      "ground_truth_route_id": "y"}
    # Update external_truth with the supplied entries.
    external_truth.update({"route_id": "opposite", "route_index": -1})
    # Set output_after to model(to_torch_graph(graph)).graph_embedding.
    output_after = model(to_torch_graph(graph)).graph_embedding
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(output_before, output_after)


# Check gnn source has no tensorflow geometric traci or policy dependencies using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_gnn_source_has_no_tensorflow_geometric_traci_or_policy_dependencies():
    # Set source_dir to Path(__file__).parents at 1 joined with the path segment 'negotiation_learning' joined with the path segment
    # 'gnn'.
    source_dir = Path(__file__).parents[1] / "negotiation_learning" / "gnn"
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of source_dir.glob(the text '*.py') as part of the enclosing
                       # expression.
                       for path in source_dir.glob("*.py"))
    # Set forbidden to a tuple containing the text 'tensorflow', the text 'keras', the text 'torch_geometric', the
    # text 'torch_scatter', the text...
    forbidden = ("tensorflow", "keras", "torch_geometric", "torch_scatter",
                 "torch_sparse", "traci", "apply_action", "negotiationmanager")
    # Require the negation of whether any item is true in a lazy sequence of name belongs to source for name in
    # forbidden; otherwise raise AssertionError.
    assert not any(name in source for name in forbidden)


# Check messages use source target edge and sum at priority target using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_messages_use_source_target_edge_and_sum_at_priority_target():
    # Set layer to the result of EdgeAwareMessagePassingLayer().
    layer = EdgeAwareMessagePassingLayer(hidden_dim=1)

    # Define CaptureMessage to group the state and operations declared below.
    # Base classes: torch.nn.Module.
    # Instances expose the attributes and methods implemented in this class.
    class CaptureMessage(torch.nn.Module):
        # Initialize the instance attributes and collaborators used by the operations below.
        # Output: no explicit value; normal completion returns None.
        def __init__(self):
            # Call super().__init__ with the supplied arguments.
            # Set self.received to None.
            super().__init__(); self.received = None

        # Forward using the inputs and processing steps below.
        # Input values: the supplied values.
        # Output: values at (:, :1) plus values at (:, 1:2) plus values at (:, 2:3).
        def forward(self, values):
            # Set self.received to the result of values.detach().clone().
            self.received = values.detach().clone()
            # Return values at (:, :1) plus values at (:, 1:2) plus values at (:, 2:3) to the caller.
            return values[:, :1] + values[:, 1:2] + values[:, 2:3]

    # Define CaptureUpdate to group the state and operations declared below.
    # Base classes: torch.nn.Module.
    # Instances expose the attributes and methods implemented in this class.
    class CaptureUpdate(torch.nn.Module):
        # Initialize the instance attributes and collaborators used by the operations below.
        # Output: no explicit value; normal completion returns None.
        def __init__(self):
            # Call super().__init__ with the supplied arguments.
            # Set self.received to None.
            super().__init__(); self.received = None

        # Forward using the inputs and processing steps below.
        # Input values: the supplied values.
        # Output: values at (:, :1).
        def forward(self, values):
            # Set self.received to the result of values.detach().clone().
            self.received = values.detach().clone()
            # Return values at (:, :1) to the caller.
            return values[:, :1]

    # Set (message, update) to a tuple containing the result of CaptureMessage(), the result of CaptureUpdate().
    message, update = CaptureMessage(), CaptureUpdate()
    # Set (layer.message_function, layer.update_function) to a tuple containing message, update.
    layer.message_function, layer.update_function = message, update
    # Set nodes to a tensor built from a list containing a list containing 2.0, a list containing 5.0, a list
    # containing 7.0.
    nodes = torch.tensor([[2.0], [5.0], [7.0]])
    # Set edge_state to a tensor built from a list containing a list containing 11.0.
    edge_state = torch.tensor([[11.0]])
    # Call layer with the supplied arguments.
    layer(nodes, edge_state, torch.tensor([[0], [1]], dtype=torch.long))
    # Require the result of message.received.tolist() equals a list containing a list containing 2.0, 5.0, 11.0;
    # otherwise raise AssertionError.
    assert message.received.tolist() == [[2.0, 5.0, 11.0]]
    # Edge 0->1 aggregates only at priority target 1. Nodes 0 and 2 have no
    # incoming messages and therefore receive SUM's exact additive identity.
    # Require the result of update.received[:, 1].tolist() equals a list containing 0.0, 18.0, 0.0; otherwise
    # raise AssertionError.
    assert update.received[:, 1].tolist() == [0.0, 18.0, 0.0]
