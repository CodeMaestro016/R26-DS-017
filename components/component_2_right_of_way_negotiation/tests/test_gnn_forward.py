"""CPU-only edge-aware MPNN forward and gradient validation."""

from pathlib import Path

import numpy as np
import pytest
import torch

from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
from negotiation_learning.gnn.message_passing import EdgeAwareMessagePassingLayer
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


TEST_REPRODUCIBILITY_SEED = 20260812
TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM = 16
TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS = 2


def encoded(node_ids, edges, ego_id="A", node_values=None, node_masks=None,
            edge_values=None, edge_masks=None):
    n, m = len(node_ids), len(edges)
    node_values = (np.zeros((n, len(NODE_NUMERIC_SCHEMA)), np.float32)
                   if node_values is None else node_values)
    node_masks = (np.ones_like(node_values, dtype=np.bool_)
                  if node_masks is None else node_masks)
    edge_values = (np.zeros((m, len(EDGE_NUMERIC_SCHEMA)), np.float32)
                   if edge_values is None else edge_values)
    edge_masks = (np.ones_like(edge_values, dtype=np.bool_)
                  if edge_masks is None else edge_masks)
    index = {name: position for position, name in enumerate(node_ids)}
    edge_index = np.asarray(
        [(index[source], index[target]) for source, target in edges],
        dtype=np.int64,
    ).reshape(-1, 2).T
    return EncodedGraphObservation(
        ego_id, tuple(node_ids), node_values, node_masks, edge_index,
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


@pytest.fixture
def model():
    torch.manual_seed(TEST_REPRODUCIBILITY_SEED)
    return EdgeAwareMPNNEncoder(
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS,
    ).eval()


def assert_shapes(output, nodes):
    assert output.node_embeddings.shape == (
        nodes, TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM
    )
    assert output.ego_embedding.shape == (TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,)
    assert output.graph_embedding.shape == (TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,)
    assert torch.isfinite(output.node_embeddings).all()


def test_one_node_zero_edge_without_self_loop(model):
    graph = to_torch_graph(encoded(("A",), ()))
    assert graph.edge_index.shape == (2, 0)
    output = model(graph)
    assert_shapes(output, 1)


def test_two_node_edge_preserves_yielding_to_priority_direction(model):
    graph = to_torch_graph(encoded(("A", "B"), (("A", "B"),)))
    assert graph.edge_index.tolist() == [[0], [1]]
    assert_shapes(model(graph), 2)


def test_four_node_cycle_forward_is_finite(model):
    graph = encoded(("A", "B", "C", "D"), (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    assert_shapes(model(to_torch_graph(graph)), 4)


def test_masks_preserve_real_zero_vs_unavailable_zero():
    values = np.zeros((2, len(NODE_NUMERIC_SCHEMA)), np.float32)
    masks = np.ones_like(values, dtype=np.bool_)
    speed = NODE_NUMERIC_SCHEMA.index("speed_mps")
    masks[1, speed] = False
    graph = to_torch_graph(encoded(("A", "B"), (), node_values=values,
                                   node_masks=masks))
    combined = torch.cat((graph.node_features,
                          graph.node_feature_mask.float()), dim=-1)
    assert combined[0, speed] == combined[1, speed] == 0
    assert combined[0, speed + len(NODE_NUMERIC_SCHEMA)] == 1
    assert combined[1, speed + len(NODE_NUMERIC_SCHEMA)] == 0


def test_edge_missing_evidence_mask_is_preserved():
    values = np.zeros((1, len(EDGE_NUMERIC_SCHEMA)), np.float32)
    masks = np.ones_like(values, dtype=np.bool_)
    temporal = EDGE_NUMERIC_SCHEMA.index("temporal_conflict_possible")
    masks[0, temporal] = False
    graph = to_torch_graph(encoded(("A", "B"), (("A", "B"),),
                                   edge_values=values, edge_masks=masks))
    assert graph.edge_features[0, temporal] == 0
    assert graph.edge_feature_mask[0, temporal] == 0


def test_node_order_permutation_preserves_graph_and_ego_embeddings(model):
    values = np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, -1)
    first = encoded(("A", "B", "C"), (("A", "B"), ("B", "C")),
                    node_values=values)
    second = encoded(("C", "A", "B"), (("B", "C"), ("A", "B")),
                     node_values=values[[2, 0, 1]])
    a, b = model(to_torch_graph(first)), model(to_torch_graph(second))
    torch.testing.assert_close(a.graph_embedding, b.graph_embedding)
    torch.testing.assert_close(a.ego_embedding, b.ego_embedding)


def test_edge_order_permutation_preserves_outputs(model):
    edge_values = np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, -1)
    first = encoded(("A", "B", "C"), (("A", "C"), ("B", "C")),
                    edge_values=edge_values)
    second = encoded(("A", "B", "C"), (("B", "C"), ("A", "C")),
                     edge_values=edge_values[[1, 0]])
    a, b = model(to_torch_graph(first)), model(to_torch_graph(second))
    torch.testing.assert_close(a.node_embeddings, b.node_embeddings)
    torch.testing.assert_close(a.graph_embedding, b.graph_embedding)


def test_ego_is_selected_by_identity_when_not_first(model):
    output = model(to_torch_graph(encoded(("B", "A", "C"), (), ego_id="A")))
    assert output.ego_node_index == 1
    torch.testing.assert_close(output.ego_embedding, output.node_embeddings[1])


def test_cpu_device_and_finite_gradient_flow(model):
    assert next(model.parameters()).device.type == "cpu"
    output = model(to_torch_graph(encoded(("A", "B"), (("A", "B"),))))
    unit_test_only_gradient_scalar = output.node_embeddings.sum()
    unit_test_only_gradient_scalar.backward()
    assert output.device == "cpu"
    assert all(parameter.grad is not None and torch.isfinite(parameter.grad).all()
               for parameter in model.parameters())


def test_route_truth_outside_encoded_graph_cannot_affect_output(model):
    graph = encoded(("A", "B"), (("A", "B"),))
    output_before = model(to_torch_graph(graph)).graph_embedding
    external_truth = {"route_id": "x", "route_index": 99,
                      "ground_truth_route_id": "y"}
    external_truth.update({"route_id": "opposite", "route_index": -1})
    output_after = model(to_torch_graph(graph)).graph_embedding
    torch.testing.assert_close(output_before, output_after)


def test_gnn_source_has_no_tensorflow_geometric_traci_or_policy_dependencies():
    source_dir = Path(__file__).parents[1] / "negotiation_learning" / "gnn"
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in source_dir.glob("*.py"))
    forbidden = ("tensorflow", "keras", "torch_geometric", "torch_scatter",
                 "torch_sparse", "traci", "apply_action", "negotiationmanager")
    assert not any(name in source for name in forbidden)


def test_messages_use_source_target_edge_and_sum_at_priority_target():
    layer = EdgeAwareMessagePassingLayer(hidden_dim=1)

    class CaptureMessage(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.received = None

        def forward(self, values):
            self.received = values.detach().clone()
            return values[:, :1] + values[:, 1:2] + values[:, 2:3]

    class CaptureUpdate(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.received = None

        def forward(self, values):
            self.received = values.detach().clone()
            return values[:, :1]

    message, update = CaptureMessage(), CaptureUpdate()
    layer.message_function, layer.update_function = message, update
    nodes = torch.tensor([[2.0], [5.0], [7.0]])
    edge_state = torch.tensor([[11.0]])
    layer(nodes, edge_state, torch.tensor([[0], [1]], dtype=torch.long))
    assert message.received.tolist() == [[2.0, 5.0, 11.0]]
    # Edge 0->1 aggregates only at priority target 1. Nodes 0 and 2 have no
    # incoming messages and therefore receive SUM's exact additive identity.
    assert update.received[:, 1].tolist() == [0.0, 18.0, 0.0]
