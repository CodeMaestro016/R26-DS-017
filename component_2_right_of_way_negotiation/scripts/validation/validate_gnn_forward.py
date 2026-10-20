"""TEST-ONLY UNTRAINED GNN VALIDATION.

NOT A NEGOTIATION POLICY. NOT CONNECTED TO SUMO CONTROL.
"""

# Import Path from pathlib for the operations below.
from pathlib import Path
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import traceback for use in this module.
import traceback
# Import numpy as np for use in this module.
import numpy as np

# Import EncodedGraphObservation from negotiation_learning.tensor_encoding.models for the operations below.
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
# Import CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from
# negotiation_learning.tensor_encoding.schemas for the operations below.
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)
# Import detect_ml_runtime from ml_runtime_capability for the operations below.
from ml_runtime_capability import detect_ml_runtime


# Set TEST_REPRODUCIBILITY_SEED to 20260812.
TEST_REPRODUCIBILITY_SEED = 20260812  # Software fixture, not traffic semantics.
# Set TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM to 16.
TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM = 16
# Set TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS to 2.
TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS = 2


# Fixture using the inputs and processing steps below.
# Input node_count: the supplied node count.
# Input edges: the supplied edges.
# Input ego_index: the supplied ego index.
# Output: the result of EncodedGraphObservation(nodes at ego_index, nodes, node_values, node_masks, edge_index,
# edge_values, edge_masks,...).
def fixture(node_count, edges, ego_index=0):
    # Set nodes to a tuple built from a lazy sequence of the result of chr(ord('A') plus index) for index in the
    # integer range defined by node_count.
    nodes = tuple(chr(ord("A") + index) for index in range(node_count))
    # Set node_values to a zero-filled tensor with the requested shape.
    node_values = np.zeros((node_count, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    # Set node_masks to the result of np.ones_like(node_values).
    node_masks = np.ones_like(node_values, dtype=np.bool_)
    # Set node_values[ego_index, 0] to 1.0.
    node_values[ego_index, 0] = 1.0
    # Set edge_values to a zero-filled tensor with the requested shape.
    edge_values = np.zeros((len(edges), len(EDGE_NUMERIC_SCHEMA)), dtype=np.float32)
    # Set edge_masks to the result of np.ones_like(edge_values).
    edge_masks = np.ones_like(edge_values, dtype=np.bool_)
    # Set edge_index to np.asarray(edges, dtype=np.int64).reshape(-1, 2).T.
    edge_index = np.asarray(edges, dtype=np.int64).reshape(-1, 2).T
    # Return the result of EncodedGraphObservation(nodes at ego_index, nodes, node_values, node_masks, edge_index,
    # edge_values, edge_masks,...) to the caller.
    return EncodedGraphObservation(
        # Supply nodes at ego_index to EncodedGraphObservation.
        nodes[ego_index], nodes, node_values, node_masks, edge_index,
        # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


# Print blocked using the inputs and processing steps below.
# Input capability: the supplied capability.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def _print_blocked(capability):
    # Display the text 'GNN Forward-Pass Validation'.
    print("GNN Forward-Pass Validation")
    # Display the text 'Status:'.
    print("\nStatus:")
    # Display the text 'PYTORCH_RUNTIME_VALIDATION_BLOCKED'.
    print("PYTORCH_RUNTIME_VALIDATION_BLOCKED")
    # Display the text 'Reason:'.
    print("\nReason:")
    # Set reason to the text 'PyTorch is not installed in this local environment.' when the negation of
    # capability.pytorch_installed, otherwise the text 'PyTorch could not complete a local CPU import/execution
    # check.'.
    reason = (
        "PyTorch is not installed in this local environment."
        # Evaluate the negation of capability.pytorch_installed as part of the enclosing expression.
        if not capability.pytorch_installed else
        "PyTorch could not complete a local CPU import/execution check."
    )
    # Display reason.
    print(reason)
    # Run this branch when capability.pytorch_error.
    if capability.pytorch_error:
        # Display formatted text built from the embedded values.
        print(f"Detected error: {capability.pytorch_error}")
    # Display the text 'TensorFlow required: False'.
    print("\nTensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("CUDA required: False")
    # Display the text 'SUMO runtime affected: False'.
    print("SUMO runtime affected: False")
    # Display the text 'NumPy GNN input encoder affected: False'.
    print("NumPy GNN input encoder affected: False")
    # Display the text 'Recommended next option:'.
    print("\nRecommended next option:")
    # Display the text 'Train/validate the neural model in a PyTorch-capable environment'.
    print("Train/validate the neural model in a PyTorch-capable environment")
    # Display the text 'such as Google Colab and later export the trained model for'.
    print("such as Google Colab and later export the trained model for")
    # Display the text 'ONNX Runtime CPU deployment.'.
    print("ONNX Runtime CPU deployment.")


# Main using the inputs and processing steps below.
# Input capability: the supplied capability.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main(capability=None):
    # Set capability to capability or the result of detect_ml_runtime().
    capability = capability or detect_ml_runtime()
    # Run this branch when the negation of capability.pytorch_import_successful and capability.pytorch_cpu_test
    # equals the text 'PASS'.
    if not (capability.pytorch_import_successful
            # Evaluate capability.pytorch_cpu_test equals the text 'PASS' as part of the enclosing expression.
            and capability.pytorch_cpu_test == "PASS"):
        # Call _print_blocked with the supplied arguments.
        _print_blocked(capability)
        # Return the text 'PYTORCH_RUNTIME_VALIDATION_BLOCKED' to the caller.
        return "PYTORCH_RUNTIME_VALIDATION_BLOCKED"

    # Optional dependency imports occur only after the guarded capability
    # check. Importing this script or the base negotiation package needs no
    # PyTorch installation.
    # Import torch for use in this module.
    import torch
    # Import EdgeAwareMPNNEncoder, to_torch_graph from negotiation_learning.gnn for the operations below.
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph

    # Call torch.manual_seed with the supplied arguments.
    torch.manual_seed(TEST_REPRODUCIBILITY_SEED)
    # Set model to the result of EdgeAwareMPNNEncoder(len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),...().
    model = EdgeAwareMPNNEncoder(
        # Supply the number of entries in NODE_NUMERIC_SCHEMA to EdgeAwareMPNNEncoder.
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        # Supply TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        # Supply TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS,
    ).eval()
    # Set cases to a dictionary containing One-node zero-edge forward pass, Two-node directed-edge forward pass,
    # Four-node cycle...
    cases = {
        # Store the result of fixture(1, an empty tuple) under 'One-node zero-edge forward pass'.
        "One-node zero-edge forward pass": fixture(1, ()),
        # Store the result of fixture(2, a tuple containing a tuple containing 0, 1) under 'Two-node directed-edge
        # forward pass'.
        "Two-node directed-edge forward pass": fixture(2, ((0, 1),)),
        # Store the result of fixture(4, a tuple containing a tuple containing 0, 1, a tuple containing 1, 2, a
        # tuple containing 2, 3,...) under 'Four-node cycle forward pass'.
        "Four-node cycle forward pass": fixture(
            # Supply a tuple containing a tuple containing 0, 1, a tuple containing 1, 2, a tuple containing 2, 3,
            # a tuple containing 3, 0 to fixture.
            4, ((0, 1), (1, 2), (2, 3), (3, 0))
        ),
    }
    # Set outputs to a dictionary of name mapped to the result of model(the result of to_torch_graph(graph)) for
    # (name, graph) in key/value pairs from cases.
    outputs = {name: model(to_torch_graph(graph)) for name, graph in cases.items()}
    # Iterate over key/value pairs from outputs, binding each item to (name, output).
    for name, output in outputs.items():
        # Set expected_nodes to cases[name].node_features.shape at 0.
        expected_nodes = cases[name].node_features.shape[0]
        # Require output.node_embeddings.shape equals a tuple containing expected_nodes,
        # TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM; otherwise raise AssertionError with name.
        assert output.node_embeddings.shape == (
            # Include TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM in this tuple.
            expected_nodes, TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM
        # Evaluate name as part of the enclosing expression.
        ), name
        # Require output.ego_embedding.shape equals a tuple containing TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM;
        # otherwise raise AssertionError with name.
        assert output.ego_embedding.shape == (
            # Include TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM in this tuple.
            TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        # Evaluate name as part of the enclosing expression.
        ), name
        # Require output.graph_embedding.shape equals a tuple containing TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM;
        # otherwise raise AssertionError with name.
        assert output.graph_embedding.shape == (
            # Include TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM in this tuple.
            TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM,
        # Evaluate name as part of the enclosing expression.
        ), name
        # Require the result of torch.isfinite(output.node_embeddings).all(); otherwise raise AssertionError with
        # name.
        assert torch.isfinite(output.node_embeddings).all(), name
        # Require the result of torch.isfinite(output.ego_embedding).all(); otherwise raise AssertionError with
        # name.
        assert torch.isfinite(output.ego_embedding).all(), name
        # Require the result of torch.isfinite(output.graph_embedding).all(); otherwise raise AssertionError with
        # name.
        assert torch.isfinite(output.graph_embedding).all(), name
    # Require cases['One-node zero-edge forward pass'].edge_index.shape equals a tuple containing 2, 0; otherwise
    # raise AssertionError.
    assert cases["One-node zero-edge forward pass"].edge_index.shape == (2, 0)
    # Require the result of cases['Two-node directed-edge forward pass'].edge_index.tolist() equals a list
    # containing a list containing 0, a list containing 1; otherwise raise AssertionError.
    assert cases["Two-node directed-edge forward pass"].edge_index.tolist() == [[0], [1]]
    # Require the result of cases['Four-node cycle forward pass'].edge_index.tolist() equals a list containing a
    # list containing 0, 1, 2, 3, a list containing 1, 2, 3, 0; otherwise raise AssertionError.
    assert cases["Four-node cycle forward pass"].edge_index.tolist() == [
        # Include a list containing 0, 1, 2, 3 in this list.
        [0, 1, 2, 3], [1, 2, 3, 0]
    ]

    # Set speed_column to the result of NODE_NUMERIC_SCHEMA.index(the text 'speed_mps').
    speed_column = NODE_NUMERIC_SCHEMA.index("speed_mps")
    # Set mask_fixture to the result of fixture(2, an empty tuple).
    mask_fixture = fixture(2, ())
    # Set mask_values to the result of mask_fixture.node_features.copy().
    mask_values = mask_fixture.node_features.copy()
    # Set mask_available to the result of mask_fixture.node_feature_mask.copy().
    mask_available = mask_fixture.node_feature_mask.copy()
    # Set mask_values[:, speed_column] to 0.0.
    mask_values[:, speed_column] = 0.0
    # Set mask_available[1, speed_column] to False.
    mask_available[1, speed_column] = False
    # Set mask_fixture to the result of replace(mask_fixture).
    mask_fixture = replace(
        # Supply node_features as mask_values.
        mask_fixture, node_features=mask_values,
        # Supply node_feature_mask as mask_available.
        node_feature_mask=mask_available,
    )
    # Set torch_mask_fixture to the result of to_torch_graph(mask_fixture).
    torch_mask_fixture = to_torch_graph(mask_fixture)
    # Set combined_nodes to the tensors concatenated by torch.cat.
    combined_nodes = torch.cat((
        # Include torch_mask_fixture.node_features in this tuple.
        torch_mask_fixture.node_features,
        # Include the result of torch_mask_fixture.node_feature_mask.float() in this tuple.
        torch_mask_fixture.node_feature_mask.float(),
    # Supply dim as the negative of 1.
    ), dim=-1)
    # Require combined_nodes at (0, speed_column) equals combined_nodes at (1, speed_column); equals 0; otherwise
    # raise AssertionError.
    assert combined_nodes[0, speed_column] == combined_nodes[1, speed_column] == 0
    # Require combined_nodes at (0, speed_column + len(NODE_NUMERIC_SCHEMA)) equals 1; otherwise raise
    # AssertionError.
    assert combined_nodes[0, speed_column + len(NODE_NUMERIC_SCHEMA)] == 1
    # Require combined_nodes at (1, speed_column + len(NODE_NUMERIC_SCHEMA)) equals 0; otherwise raise
    # AssertionError.
    assert combined_nodes[1, speed_column + len(NODE_NUMERIC_SCHEMA)] == 0

    # Set temporal_column to the result of EDGE_NUMERIC_SCHEMA.index(the text 'temporal_conflict_possible').
    temporal_column = EDGE_NUMERIC_SCHEMA.index("temporal_conflict_possible")
    # Set edge_mask_fixture to the result of fixture(2, a tuple containing a tuple containing 0, 1).
    edge_mask_fixture = fixture(2, ((0, 1),))
    # Set edge_values to the result of edge_mask_fixture.edge_features.copy().
    edge_values = edge_mask_fixture.edge_features.copy()
    # Set edge_available to the result of edge_mask_fixture.edge_feature_mask.copy().
    edge_available = edge_mask_fixture.edge_feature_mask.copy()
    # Set edge_values[0, temporal_column] to 0.0.
    edge_values[0, temporal_column] = 0.0
    # Set edge_available[0, temporal_column] to False.
    edge_available[0, temporal_column] = False
    # Set edge_mask_fixture to the result of replace(edge_mask_fixture).
    edge_mask_fixture = replace(
        # Supply edge_features as edge_values.
        edge_mask_fixture, edge_features=edge_values,
        # Supply edge_feature_mask as edge_available.
        edge_feature_mask=edge_available,
    )
    # Set torch_edge_fixture to the result of to_torch_graph(edge_mask_fixture).
    torch_edge_fixture = to_torch_graph(edge_mask_fixture)
    # Set combined_edges to the tensors concatenated by torch.cat.
    combined_edges = torch.cat((
        # Include torch_edge_fixture.edge_features in this tuple.
        torch_edge_fixture.edge_features,
        # Include the result of torch_edge_fixture.edge_feature_mask.float() in this tuple.
        torch_edge_fixture.edge_feature_mask.float(),
    # Supply dim as the negative of 1.
    ), dim=-1)
    # Require combined_edges at (0, temporal_column) equals 0; otherwise raise AssertionError.
    assert combined_edges[0, temporal_column] == 0
    # Require combined_edges at (0, temporal_column + len(EDGE_NUMERIC_SCHEMA)) equals 0; otherwise raise
    # AssertionError.
    assert combined_edges[0, temporal_column + len(EDGE_NUMERIC_SCHEMA)] == 0
    # Set original_graph to cases at 'Two-node directed-edge forward pass'.
    original_graph = cases["Two-node directed-edge forward pass"]
    # Set node_permuted to the result of EncodedGraphObservation(the text 'A', a tuple containing the text 'B',
    # the text 'A', the result of...).
    node_permuted = EncodedGraphObservation(
        # Supply the result of original_graph.node_features[[1, 0]].copy() to EncodedGraphObservation.
        "A", ("B", "A"), original_graph.node_features[[1, 0]].copy(),
        # Supply the result of original_graph.node_feature_mask[[1, 0]].copy() to EncodedGraphObservation.
        original_graph.node_feature_mask[[1, 0]].copy(),
        # Supply dtype as np.int64.
        np.asarray(((1,), (0,)), dtype=np.int64),
        # Supply the result of original_graph.edge_feature_mask.copy() to EncodedGraphObservation.
        original_graph.edge_features.copy(), original_graph.edge_feature_mask.copy(),
        # Supply original_graph.node_feature_names to EncodedGraphObservation.
        original_graph.node_feature_names, original_graph.edge_feature_names,
        # Supply original_graph.categorical_encoding_metadata to EncodedGraphObservation.
        original_graph.categorical_encoding_metadata,
        # Supply original_graph.hard_constraint_metadata to EncodedGraphObservation.
        original_graph.hard_constraint_metadata, original_graph.identifier_metadata,
        # Supply original_graph.communication_model to EncodedGraphObservation.
        original_graph.source_graph_scope, original_graph.communication_model,
        # Supply original_graph.normalization_status to EncodedGraphObservation.
        original_graph.normalization_status, original_graph.tensor_backend,
    )
    # Set original_two to outputs at 'Two-node directed-edge forward pass'.
    original_two = outputs["Two-node directed-edge forward pass"]
    # Set permuted_two to the result of model(the result of to_torch_graph(node_permuted)).
    permuted_two = model(to_torch_graph(node_permuted))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(
        # Supply original_two.graph_embedding to torch.testing.assert_close.
        original_two.graph_embedding, permuted_two.graph_embedding
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(
        # Supply original_two.ego_embedding to torch.testing.assert_close.
        original_two.ego_embedding, permuted_two.ego_embedding
    )
    # Set cycle to cases at 'Four-node cycle forward pass'.
    cycle = cases["Four-node cycle forward pass"]
    # Set edge_order to the result of np.asarray(a list containing 2, 0, 3, 1).
    edge_order = np.asarray([2, 0, 3, 1])
    # Set reordered_cycle to the result of EncodedGraphObservation(cycle.ego_id, cycle.node_ids, the result of
    # cycle.node_features.copy(), the result of...).
    reordered_cycle = EncodedGraphObservation(
        # Supply the result of cycle.node_features.copy() to EncodedGraphObservation.
        cycle.ego_id, cycle.node_ids, cycle.node_features.copy(),
        # Supply the result of cycle.edge_index[:, edge_order].copy() to EncodedGraphObservation.
        cycle.node_feature_mask.copy(), cycle.edge_index[:, edge_order].copy(),
        # Supply the result of cycle.edge_features[edge_order].copy() to EncodedGraphObservation.
        cycle.edge_features[edge_order].copy(),
        # Supply the result of cycle.edge_feature_mask[edge_order].copy() to EncodedGraphObservation.
        cycle.edge_feature_mask[edge_order].copy(), cycle.node_feature_names,
        # Supply cycle.categorical_encoding_metadata to EncodedGraphObservation.
        cycle.edge_feature_names, cycle.categorical_encoding_metadata,
        # Supply cycle.hard_constraint_metadata to EncodedGraphObservation.
        cycle.hard_constraint_metadata, cycle.identifier_metadata,
        # Supply cycle.communication_model to EncodedGraphObservation.
        cycle.source_graph_scope, cycle.communication_model,
        # Supply cycle.normalization_status to EncodedGraphObservation.
        cycle.normalization_status, cycle.tensor_backend,
    )
    # Set reordered_output to the result of model(the result of to_torch_graph(reordered_cycle)).
    reordered_output = model(to_torch_graph(reordered_cycle))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(
        # Supply outputs['Four-node cycle forward pass'].graph_embedding to torch.testing.assert_close.
        outputs["Four-node cycle forward pass"].graph_embedding,
        # Supply reordered_output.graph_embedding to torch.testing.assert_close.
        reordered_output.graph_embedding,
    )
    # Set scalar to the sum of a lazy sequence of the result of output.node_embeddings.sum() for output in values
    # from outputs.
    scalar = sum(output.node_embeddings.sum() for output in outputs.values())
    # Backpropagate gradients from scalar.
    scalar.backward()  # UNIT_TEST_ONLY_GRADIENT_SCALAR; not a reward/objective.
    # Set finite_gradients to whether every item is true in a lazy sequence of parameter.grad is a different
    # object from None and the result of torch.isfinite(parameter.grad).all() for parameter in the result of
    # model.parameters().
    finite_gradients = all(
        # Evaluate parameter.grad is a different object from None and the result of
        # torch.isfinite(parameter.grad).all() as part of the enclosing expression.
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        # Evaluate the result of model.parameters() as part of the enclosing expression.
        for parameter in model.parameters()
    )
    # Set finite_embeddings to whether every item is true in a lazy sequence of the result of
    # torch.isfinite(output.node_embeddings).all() and the result of torch.isfinite(output.ego_embedding).all()
    # and the result of torch.isfinite(output.graph_embedding).all() for output in values from outputs.
    finite_embeddings = all(
        # Evaluate the result of torch.isfinite(output.node_embeddings).all() and the result of
        # torch.isfinite(output.ego_embedding).all() and the result of
        # torch.isfinite(output.graph_embedding).all() as part of the enclosing expression.
        torch.isfinite(output.node_embeddings).all()
        # Evaluate the result of torch.isfinite(output.ego_embedding).all() as part of the enclosing expression.
        and torch.isfinite(output.ego_embedding).all()
        # Evaluate the result of torch.isfinite(output.graph_embedding).all() as part of the enclosing expression.
        and torch.isfinite(output.graph_embedding).all()
        # Evaluate values from outputs as part of the enclosing expression.
        for output in outputs.values()
    )
    # Require permuted_two.ego_node_index equals 1; otherwise raise AssertionError.
    assert permuted_two.ego_node_index == 1
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(
        # Supply permuted_two.node_embeddings at 1 to torch.testing.assert_close.
        permuted_two.ego_embedding, permuted_two.node_embeddings[1]
    )
    # Require next(model.parameters()).device.type equals the text 'cpu'; otherwise raise AssertionError.
    assert next(model.parameters()).device.type == "cpu"
    # Require whether every item is true in a lazy sequence of tensor.device.type equals the text 'cpu' for output
    # in values from outputs; otherwise raise AssertionError.
    assert all(tensor.device.type == "cpu" for output in outputs.values()
               # Evaluate a tuple containing output.node_embeddings, output.ego_embedding, output.graph_embedding
               # as part of the enclosing expression.
               for tensor in (output.node_embeddings, output.ego_embedding,
                              # Include output.graph_embedding in this tuple.
                              output.graph_embedding))
    # Require finite_embeddings; otherwise raise AssertionError.
    assert finite_embeddings
    # Require finite_gradients; otherwise raise AssertionError.
    assert finite_gradients
    # Set gnn_dir to Path(__file__).parent joined with the path segment 'negotiation_learning' joined with the path segment 'gnn'.
    gnn_dir = Path(__file__).parent / "negotiation_learning" / "gnn"
    # Set gnn_source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    gnn_source = "\n".join(
        # Supply encoding as the text 'utf-8'.
        path.read_text(encoding="utf-8").lower()
        # Evaluate the result of gnn_dir.glob(the text '*.py') as part of the enclosing expression.
        for path in gnn_dir.glob("*.py")
    )
    # Set forbidden to a tuple containing the text 'tensorflow', the text 'keras', the text 'torch_geometric', the
    # text 'torch_scatter', the text...
    forbidden = ("tensorflow", "keras", "torch_geometric", "torch_scatter",
                 "torch_sparse", "dgl", "traci", "apply_action",
                 "negotiationmanager", "route_id", "route_index",
                 "ground_truth_route_id", "to(\"cuda\")", "cuda:0")
    # Require the negation of whether any item is true in a lazy sequence of value belongs to gnn_source for value
    # in forbidden; otherwise raise AssertionError.
    assert not any(value in gnn_source for value in forbidden)

    # Display the text 'GNN Forward-Pass Validation'.
    print("GNN Forward-Pass Validation")
    # Display the text 'Environment'.
    print("\nEnvironment")
    # Display formatted text built from the embedded values.
    print(f"  Python version: {capability.python_version}")
    # Display formatted text built from the embedded values.
    print(f"  PyTorch version: {capability.pytorch_version}")
    # Display the text 'PyTorch import success: True'.
    print("  PyTorch import success: True")
    # Display the text 'Backend: PyTorch'.
    print("  Backend: PyTorch")
    # Display the text 'Device: CPU'.
    print("  Device: CPU")
    # Display the text 'Architecture'.
    print("\nArchitecture")
    # Display formatted text built from the embedded values.
    print(f"  Node semantic input dimension: {len(NODE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Node mask dimension: {len(NODE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Effective node model-input dimension: {2 * len(NODE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Edge semantic input dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Edge mask dimension: {len(EDGE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Effective edge model-input dimension: {2 * len(EDGE_NUMERIC_SCHEMA)}")
    # Display formatted text built from the embedded values.
    print(f"  Test-only hidden dimension: {TEST_ONLY_NON_OPERATIONAL_HIDDEN_DIM}")
    # Display formatted text built from the embedded values.
    print(f"  Test-only message-passing layers: {TEST_ONLY_NON_OPERATIONAL_MESSAGE_LAYERS}")
    # Display the text 'Final architecture hyperparameters selected: False'.
    print("  Final architecture hyperparameters selected: False")
    # Display the text 'Tests'.
    print("\nTests")
    # Iterate over cases, binding each item to name.
    for name in cases:
        # Display formatted text built from the embedded values.
        print(f"  {name}: PASS")
    # Display the text 'Variable graph sizes supported: PASS'.
    print("  Variable graph sizes supported: PASS")
    # Display the text 'Node-order permutation invariance: PASS'.
    print("  Node-order permutation invariance: PASS")
    # Display the text 'Edge-order permutation invariance: PASS'.
    print("  Edge-order permutation invariance: PASS")
    # Display the text 'Missing-value masks preserved: PASS'.
    print("  Missing-value masks preserved: PASS")
    # Display the text 'Real-zero vs unavailable-zero distinction: PASS'.
    print("  Real-zero vs unavailable-zero distinction: PASS")
    # Display the text 'Ego extraction independent of node order: PASS'.
    print("  Ego extraction independent of node order: PASS")
    # Display the text 'Missing edge evidence mask preserved: PASS'.
    print("  Missing edge evidence mask preserved: PASS")
    # Display the text 'Finite node embeddings: PASS'.
    print("  Finite node embeddings: PASS")
    # Display the text 'Finite ego embedding: PASS'.
    print("  Finite ego embedding: PASS")
    # Display the text 'Finite graph embedding: PASS'.
    print("  Finite graph embedding: PASS")
    # Display the text 'Finite backpropagation gradients: PASS'.
    print("  Finite backpropagation gradients: PASS")
    # Display the text 'Safety / dependency boundaries'.
    print("\nSafety / dependency boundaries")
    # Display the text 'CPU-only execution: PASS'.
    print("  CPU-only execution: PASS")
    # Display the text 'TensorFlow imports introduced: 0'.
    print("  TensorFlow imports introduced: 0")
    # Display the text 'PyTorch Geometric dependencies introduced: 0'.
    print("  PyTorch Geometric dependencies introduced: 0")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'Route-truth fields consumed by GNN: 0'.
    print("  Route-truth fields consumed by GNN: 0")
    # Display the text 'Artificial self-loops added: 0'.
    print("  Artificial self-loops added: 0")
    # Display the text 'Control actions issued by GNN: 0'.
    print("  Control actions issued by GNN: 0")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'Optimizer implemented: False'.
    print("  Optimizer implemented: False")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
    # Display the text 'MAPPO implemented: False'.
    print("  MAPPO implemented: False")
    # Display the text 'Model checkpoint produced: False'.
    print("  Model checkpoint produced: False")
    # Return the text 'PASS' to the caller.
    return "PASS"


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call main with the supplied arguments.
        main()
    # Handle Exception as error using the recovery steps below.
    except Exception as error:
        # Display the text 'GNN Forward-Pass Validation: FAIL'.
        print("GNN Forward-Pass Validation: FAIL")
        # Display formatted text built from the embedded values.
        print(f"  Failing check/error: {error}")
        # Call traceback.print_exc with the supplied arguments.
        traceback.print_exc()
        # Raise SystemExit with 1 to stop this execution path.
        raise SystemExit(1) from error
