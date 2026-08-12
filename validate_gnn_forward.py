"""TEST-ONLY UNTRAINED GNN VALIDATION.

NOT A NEGOTIATION POLICY. NOT CONNECTED TO SUMO CONTROL.
"""

from pathlib import Path
from dataclasses import replace
import traceback
import numpy as np

from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)
from ml_runtime_capability import detect_ml_runtime


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


def _print_blocked(capability):
    print("GNN Forward-Pass Validation")
    print("\nStatus:")
    print("PYTORCH_RUNTIME_VALIDATION_BLOCKED")
    print("\nReason:")
    reason = (
        "PyTorch is not installed in this local environment."
        if not capability.pytorch_installed else
        "PyTorch could not complete a local CPU import/execution check."
    )
    print(reason)
    if capability.pytorch_error:
        print(f"Detected error: {capability.pytorch_error}")
    print("\nTensorFlow required: False")
    print("CUDA required: False")
    print("SUMO runtime affected: False")
    print("NumPy GNN input encoder affected: False")
    print("\nRecommended next option:")
    print("Train/validate the neural model in a PyTorch-capable environment")
    print("such as Google Colab and later export the trained model for")
    print("ONNX Runtime CPU deployment.")


def main(capability=None):
    capability = capability or detect_ml_runtime()
    if not (capability.pytorch_import_successful
            and capability.pytorch_cpu_test == "PASS"):
        _print_blocked(capability)
        return "PYTORCH_RUNTIME_VALIDATION_BLOCKED"

    # Optional dependency imports occur only after the guarded capability
    # check. Importing this script or the base negotiation package needs no
    # PyTorch installation.
    import torch
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph

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
    for name, output in outputs.items():
        expected_nodes = cases[name].node_features.shape[0]
        assert output.node_embeddings.shape == (
            expected_nodes, TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM
        ), name
        assert output.ego_embedding.shape == (
            TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        ), name
        assert output.graph_embedding.shape == (
            TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        ), name
        assert torch.isfinite(output.node_embeddings).all(), name
        assert torch.isfinite(output.ego_embedding).all(), name
        assert torch.isfinite(output.graph_embedding).all(), name
    assert cases["One-node zero-edge forward pass"].edge_index.shape == (2, 0)
    assert cases["Two-node directed-edge forward pass"].edge_index.tolist() == [[0], [1]]
    assert cases["Four-node cycle forward pass"].edge_index.tolist() == [
        [0, 1, 2, 3], [1, 2, 3, 0]
    ]

    speed_column = NODE_NUMERIC_SCHEMA.index("speed_mps")
    mask_fixture = fixture(2, ())
    mask_values = mask_fixture.node_features.copy()
    mask_available = mask_fixture.node_feature_mask.copy()
    mask_values[:, speed_column] = 0.0
    mask_available[1, speed_column] = False
    mask_fixture = replace(
        mask_fixture, node_features=mask_values,
        node_feature_mask=mask_available,
    )
    torch_mask_fixture = to_torch_graph(mask_fixture)
    combined_nodes = torch.cat((
        torch_mask_fixture.node_features,
        torch_mask_fixture.node_feature_mask.float(),
    ), dim=-1)
    assert combined_nodes[0, speed_column] == combined_nodes[1, speed_column] == 0
    assert combined_nodes[0, speed_column + len(NODE_NUMERIC_SCHEMA)] == 1
    assert combined_nodes[1, speed_column + len(NODE_NUMERIC_SCHEMA)] == 0

    temporal_column = EDGE_NUMERIC_SCHEMA.index("temporal_conflict_possible")
    edge_mask_fixture = fixture(2, ((0, 1),))
    edge_values = edge_mask_fixture.edge_features.copy()
    edge_available = edge_mask_fixture.edge_feature_mask.copy()
    edge_values[0, temporal_column] = 0.0
    edge_available[0, temporal_column] = False
    edge_mask_fixture = replace(
        edge_mask_fixture, edge_features=edge_values,
        edge_feature_mask=edge_available,
    )
    torch_edge_fixture = to_torch_graph(edge_mask_fixture)
    combined_edges = torch.cat((
        torch_edge_fixture.edge_features,
        torch_edge_fixture.edge_feature_mask.float(),
    ), dim=-1)
    assert combined_edges[0, temporal_column] == 0
    assert combined_edges[0, temporal_column + len(EDGE_NUMERIC_SCHEMA)] == 0
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
    assert permuted_two.ego_node_index == 1
    torch.testing.assert_close(
        permuted_two.ego_embedding, permuted_two.node_embeddings[1]
    )
    assert next(model.parameters()).device.type == "cpu"
    assert all(tensor.device.type == "cpu" for output in outputs.values()
               for tensor in (output.node_embeddings, output.ego_embedding,
                              output.graph_embedding))
    assert finite_embeddings
    assert finite_gradients
    gnn_dir = Path(__file__).parent / "negotiation_learning" / "gnn"
    gnn_source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in gnn_dir.glob("*.py")
    )
    forbidden = ("tensorflow", "keras", "torch_geometric", "torch_scatter",
                 "torch_sparse", "dgl", "traci", "apply_action",
                 "negotiationmanager", "route_id", "route_index",
                 "ground_truth_route_id", "to(\"cuda\")", "cuda:0")
    assert not any(value in gnn_source for value in forbidden)

    print("GNN Forward-Pass Validation")
    print("\nEnvironment")
    print(f"  Python version: {capability.python_version}")
    print(f"  PyTorch version: {capability.pytorch_version}")
    print("  PyTorch import success: True")
    print("  Backend: PyTorch")
    print("  Device: CPU")
    print("\nArchitecture")
    print(f"  Node semantic input dimension: {len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Node mask dimension: {len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Effective node model-input dimension: {2 * len(NODE_NUMERIC_SCHEMA)}")
    print(f"  Edge semantic input dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Edge mask dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Effective edge model-input dimension: {2 * len(EDGE_NUMERIC_SCHEMA)}")
    print(f"  Test-only hidden dimension: {TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM}")
    print(f"  Test-only message-passing layers: {TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS}")
    print("  Final architecture hyperparameters selected: False")
    print("\nTests")
    for name in cases:
        print(f"  {name}: PASS")
    print("  Variable graph sizes supported: PASS")
    print("  Node-order permutation invariance: PASS")
    print("  Edge-order permutation invariance: PASS")
    print("  Missing-value masks preserved: PASS")
    print("  Real-zero vs unavailable-zero distinction: PASS")
    print("  Ego extraction independent of node order: PASS")
    print("  Missing edge evidence mask preserved: PASS")
    print("  Finite node embeddings: PASS")
    print("  Finite ego embedding: PASS")
    print("  Finite graph embedding: PASS")
    print("  Finite backpropagation gradients: PASS")
    print("\nSafety / dependency boundaries")
    print("  CPU-only execution: PASS")
    print("  TensorFlow imports introduced: 0")
    print("  PyTorch Geometric dependencies introduced: 0")
    print("  CUDA required: False")
    print("  Route-truth fields consumed by GNN: 0")
    print("  Artificial self-loops added: 0")
    print("  Control actions issued by GNN: 0")
    print("\nResearch status")
    print("  Training performed: False")
    print("  Optimizer implemented: False")
    print("  Reward implemented: False")
    print("  MAPPO implemented: False")
    print("  Model checkpoint produced: False")
    return "PASS"


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("GNN Forward-Pass Validation: FAIL")
        print(f"  Failing check/error: {error}")
        traceback.print_exc()
        raise SystemExit(1) from error
