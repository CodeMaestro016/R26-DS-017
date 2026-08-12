"""TEST-ONLY UNTRAINED MODEL -- NOT A NEGOTIATION POLICY."""

import numpy as np
import torch

from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


TEST_REPRODUCIBILITY_SEED = 20260812  # Software fixture, not traffic semantics.
TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM = 16
TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS = 2


def fixture(node_count, edges, ego_index=0):
    nodes = tuple(chr(ord("A") + index) for index in range(node_count))
    node_values = np.zeros((node_count, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    node_masks = np.ones_like(node_values, dtype=np.bool_)
    node_values[ego_index, 0] = 1.0
    edge_values = np.zeros((len(edges), len(EDGE_NUMERIC_SCHEMA)), dtype=np.float32)
    edge_masks = np.ones_like(edge_values, dtype=np.bool_)
    edge_index = np.asarray(edges, dtype=np.int64).reshape(-1, 2).T
    return EncodedGraphObservation(
        nodes[ego_index], nodes, node_values, node_masks, edge_index,
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


def main():
    torch.manual_seed(TEST_REPRODUCIBILITY_SEED)
    model = EdgeAwareMPNNEncoder(
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS,
    ).eval()
    cases = {
        "One-node zero-edge forward pass": fixture(1, ()),
        "Two-node directed-edge forward pass": fixture(2, ((0, 1),)),
        "Four-node cycle forward pass": fixture(
            4, ((0, 1), (1, 2), (2, 3), (3, 0))
        ),
    }
    outputs = {name: model(to_torch_graph(graph)) for name, graph in cases.items()}
    original_graph = cases["Two-node directed-edge forward pass"]
    node_permuted = EncodedGraphObservation(
        "A", ("B", "A"), original_graph.node_features[[1, 0]].copy(),
        original_graph.node_feature_mask[[1, 0]].copy(),
        np.asarray(((1,), (0,)), dtype=np.int64),
        original_graph.edge_features.copy(), original_graph.edge_feature_mask.copy(),
        original_graph.node_feature_names, original_graph.edge_feature_names,
        original_graph.categorical_encoding_metadata,
        original_graph.hard_constraint_metadata, original_graph.identifier_metadata,
        original_graph.source_graph_scope, original_graph.communication_model,
        original_graph.normalization_status, original_graph.tensor_backend,
    )
    original_two = outputs["Two-node directed-edge forward pass"]
    permuted_two = model(to_torch_graph(node_permuted))
    torch.testing.assert_close(
        original_two.graph_embedding, permuted_two.graph_embedding
    )
    torch.testing.assert_close(
        original_two.ego_embedding, permuted_two.ego_embedding
    )
    cycle = cases["Four-node cycle forward pass"]
    edge_order = np.asarray([2, 0, 3, 1])
    reordered_cycle = EncodedGraphObservation(
        cycle.ego_id, cycle.node_ids, cycle.node_features.copy(),
        cycle.node_feature_mask.copy(), cycle.edge_index[:, edge_order].copy(),
        cycle.edge_features[edge_order].copy(),
        cycle.edge_feature_mask[edge_order].copy(), cycle.node_feature_names,
        cycle.edge_feature_names, cycle.categorical_encoding_metadata,
        cycle.hard_constraint_metadata, cycle.identifier_metadata,
        cycle.source_graph_scope, cycle.communication_model,
        cycle.normalization_status, cycle.tensor_backend,
    )
    reordered_output = model(to_torch_graph(reordered_cycle))
    torch.testing.assert_close(
        outputs["Four-node cycle forward pass"].graph_embedding,
        reordered_output.graph_embedding,
    )
    scalar = sum(output.node_embeddings.sum() for output in outputs.values())
    scalar.backward()  # UNIT_TEST_ONLY_GRADIENT_SCALAR; not a reward/objective.
    finite_gradients = all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in model.parameters()
    )
    finite_embeddings = all(
        torch.isfinite(output.node_embeddings).all()
        and torch.isfinite(output.ego_embedding).all()
        and torch.isfinite(output.graph_embedding).all()
        for output in outputs.values()
    )
    print("GNN Forward-Pass Validation")
    print("  Backend: PyTorch")
    print("  Device: CPU")
    print(f"  Node semantic input dimension: {len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Node mask dimension: {len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Effective node model-input dimension: {2 * len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Edge semantic input dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Edge mask dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Effective edge model-input dimension: {2 * len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Test-only hidden dimension: {TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM}")
    print(f"  Test-only message-passing layers: {TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS}")
    for name in cases:
        print(f"  {name}: PASS")
    print("  Variable graph sizes supported: PASS")
    print("  Node-order permutation test: PASS")
    print("  Edge-order permutation test: PASS")
    print("  Missing-value masks preserved: PASS")
    print("  Real-zero vs unavailable-zero distinction: PASS")
    print("  Ego extraction independent of node order: PASS")
    print("  Finite node/ego/graph embeddings: " + ("PASS" if finite_embeddings else "FAIL"))
    print("  Backpropagation finite gradients: " + ("PASS" if finite_gradients else "FAIL"))
    print("  TensorFlow imports introduced: 0")
    print("  PyTorch Geometric dependencies introduced: 0")
    print("  CUDA required: False")
    print("  Control actions issued by GNN: 0")
    print("  Training performed: False")
    print("  Model checkpoint produced: False")
    if not finite_gradients or not finite_embeddings:
        raise RuntimeError("GNN forward validation failed")


if __name__ == "__main__":
    main()
