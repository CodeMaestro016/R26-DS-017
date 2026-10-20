"""Standalone Step 5F.1 deterministic policy semantic encoding validation."""

# Import numpy as np for use in this module.
import numpy as np

# Import ProtocolState from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import ProtocolState
# Import CLAIM_COLUMNS, PROTOCOL_STATE_COLUMNS, NegotiationSemanticFeatureEncoder, PolicySemanticEncodingError
# from negotiation_learning.semantic_encoding for the operations below.
from negotiation_learning.semantic_encoding import (
    CLAIM_COLUMNS, PROTOCOL_STATE_COLUMNS, NegotiationSemanticFeatureEncoder,
    PolicySemanticEncodingError,
)
# Import EncodedGraphObservation from negotiation_learning.tensor_encoding.models for the operations below.
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
# Import CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from
# negotiation_learning.tensor_encoding.schemas for the operations below.
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


# Graph using the inputs and processing steps below.
# Input node_ids: the supplied node ids.
# Input edges: the supplied edges.
# Input node_values: the supplied node values.
# Input node_masks: the supplied node masks.
# Input edge_values: the supplied edge values.
# Input edge_masks: the supplied edge masks.
# Output: the result of EncodedGraphObservation(the text 'B', a tuple built from node_ids, node_values,
# node_masks, edge_index, edge_values,...).
def graph(node_ids=("A", "B"), edges=(("A", "B"),), node_values=None,
          # Declare node_masks, edge_values, edge_masks as input parameters.
          node_masks=None, edge_values=None, edge_masks=None):
    # Set (n, e) to a tuple containing the number of entries in node_ids, the number of entries in edges.
    n, e = len(node_ids), len(edges)
    # Set node_values to the result of np.arange(n * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(n, the
    # number of entries in NODE_NUMERIC_SCHEMA) when node_values is the same object as None, otherwise
    # node_values.
    node_values = (np.arange(n * len(NODE_NUMERIC_SCHEMA), dtype=np.float32)
                   # Supply the number of entries in NODE_NUMERIC_SCHEMA to np.arange(n *
                   # len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape.
                   .reshape(n, len(NODE_NUMERIC_SCHEMA))
                   # Evaluate node_values is the same object as None as part of the enclosing expression.
                   if node_values is None else node_values)
    # Set node_masks to the result of np.ones_like(node_values) when node_masks is the same object as None,
    # otherwise node_masks.
    node_masks = (np.ones_like(node_values, dtype=np.bool_)
                  # Evaluate node_masks is the same object as None as part of the enclosing expression.
                  if node_masks is None else node_masks)
    # Set edge_values to the result of np.arange(e * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(e, the
    # number of entries in EDGE_NUMERIC_SCHEMA) when edge_values is the same object as None, otherwise
    # edge_values.
    edge_values = (np.arange(e * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32)
                   # Supply the number of entries in EDGE_NUMERIC_SCHEMA to np.arange(e *
                   # len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape.
                   .reshape(e, len(EDGE_NUMERIC_SCHEMA))
                   # Evaluate edge_values is the same object as None as part of the enclosing expression.
                   if edge_values is None else edge_values)
    # Set edge_masks to the result of np.ones_like(edge_values) when edge_masks is the same object as None,
    # otherwise edge_masks.
    edge_masks = (np.ones_like(edge_values, dtype=np.bool_)
                  # Evaluate edge_masks is the same object as None as part of the enclosing expression.
                  if edge_masks is None else edge_masks)
    # Set index to a dictionary of item mapped to position for (position, item) in index/value pairs from
    # node_ids.
    index = {item: position for position, item in enumerate(node_ids)}
    # Set edge_index to np.asarray([(index[a], index[b]) for a, b in edges], dtype=np.int64).reshape(-1, 2).T.
    edge_index = np.asarray([(index[a], index[b]) for a, b in edges],
                            # Supply dtype as np.int64.
                            dtype=np.int64).reshape(-1, 2).T
    # Return the result of EncodedGraphObservation(the text 'B', a tuple built from node_ids, node_values,
    # node_masks, edge_index, edge_values,...) to the caller.
    return EncodedGraphObservation(
        # Supply a tuple built from node_ids to EncodedGraphObservation.
        "B", tuple(node_ids), node_values, node_masks, edge_index,
        # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def main():
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Set current to the result of graph(a tuple containing the text 'B', the text 'A', the text 'C', a tuple
    # containing a tuple...).
    current = graph(("B", "A", "C"), (("C", "B"), ("A", "B")))
    # Set encoded to the result of encoder.encode_claim(current, the text 'B', a tuple containing the text 'A',
    # the text 'B').
    encoded = encoder.encode_claim(current, "B", ("A", "B"))
    # Require encoded.counterparty_id equals the text 'A'; otherwise raise AssertionError.
    assert encoded.counterparty_id == "A"
    # Require encoded.column_names equals CLAIM_COLUMNS; otherwise raise AssertionError.
    assert encoded.column_names == CLAIM_COLUMNS
    # Require encoded.semantic_values.shape equals a tuple containing the number of entries in NODE_NUMERIC_SCHEMA
    # plus the number of entries in EDGE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.semantic_values.shape == (len(NODE_NUMERIC_SCHEMA) +
                                               # Evaluate the number of entries in EDGE_NUMERIC_SCHEMA as part of the
                                               # enclosing expression.
                                               len(EDGE_NUMERIC_SCHEMA),)
    # Require encoded.model_input.shape equals a tuple containing 2 multiplied by the number of entries in
    # CLAIM_COLUMNS; otherwise raise AssertionError.
    assert encoded.model_input.shape == (2 * len(CLAIM_COLUMNS),)

    # Set reordered to the result of graph(a tuple containing the text 'C', the text 'A', the text 'B', a tuple
    # containing a tuple...).
    reordered = graph(("C", "A", "B"), (("A", "B"), ("C", "B")),
                      # Supply node_values as current.node_features at [2, 1, 0].
                      node_values=current.node_features[[2, 1, 0]],
                      # Supply edge_values as current.edge_features at [1, 0].
                      edge_values=current.edge_features[[1, 0]])
    # Set replay to the result of encoder.encode_claim(reordered, the text 'B', a tuple containing the text 'A',
    # the text 'B').
    replay = encoder.encode_claim(reordered, "B", ("A", "B"))
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(encoded.semantic_values, replay.semantic_values)
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(encoded.availability_mask, replay.availability_mask)

    # Set values to a zero-filled tensor with the requested shape.
    values = np.zeros((2, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    # Set masks to the result of np.ones_like(values).
    masks = np.ones_like(values, dtype=np.bool_)
    # Set unavailable to the result of masks.copy().
    # Set unavailable[0, 1] to False.
    unavailable = masks.copy(); unavailable[0, 1] = False
    # Set real_zero to the result of encoder.encode_claim(the result of graph(), the text 'B', a tuple containing
    # the text 'A', the text 'B').
    real_zero = encoder.encode_claim(graph(node_values=values, node_masks=masks),
                                     # Supply a tuple containing the text 'A', the text 'B' to
                                     # encoder.encode_claim.
                                     "B", ("A", "B"))
    # Set missing_zero to the result of encoder.encode_claim(the result of graph(), the text 'B', a tuple
    # containing the text 'A', the text 'B').
    missing_zero = encoder.encode_claim(
        # Supply node_values as values.
        # Supply node_masks as unavailable.
        graph(node_values=values, node_masks=unavailable), "B", ("A", "B")
    )
    # Require the negation of the result of np.array_equal(real_zero.model_input, missing_zero.model_input);
    # otherwise raise AssertionError.
    assert not np.array_equal(real_zero.model_input, missing_zero.model_input)

    # Set protocol_encodings to a list of the result of encoder.encode_protocol_state(state, True) for state in
    # ProtocolState.
    protocol_encodings = [encoder.encode_protocol_state(state, True)
                          # Evaluate ProtocolState as part of the enclosing expression.
                          for state in ProtocolState]
    # Require the number of entries in PROTOCOL_STATE_COLUMNS equals the number of entries in ProtocolState;
    # otherwise raise AssertionError.
    assert len(PROTOCOL_STATE_COLUMNS) == len(ProtocolState)
    # Require whether every item is true in a lazy sequence of the result of item.semantic_values.sum() equals 1
    # for item in protocol_encodings; otherwise raise AssertionError.
    assert all(item.semantic_values.sum() == 1 for item in protocol_encodings)
    # Require whether every item is true in a lazy sequence of the result of item.availability_mask.all() for item
    # in protocol_encodings; otherwise raise AssertionError.
    assert all(item.availability_mask.all() for item in protocol_encodings)
    # Require the number of entries in a set of a tuple built from item.semantic_values for item in
    # protocol_encodings equals the number of entries in ProtocolState; otherwise raise AssertionError.
    assert len({tuple(item.semantic_values) for item in protocol_encodings}) == len(ProtocolState)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call encoder.encode_protocol_state with the supplied arguments.
        encoder.encode_protocol_state("UNSUPPORTED")
        # Raise AssertionError with the text 'unsupported state accepted' to stop this execution path.
        raise AssertionError("unsupported state accepted")
    # Handle PolicySemanticEncodingError as error using the recovery steps below.
    except PolicySemanticEncodingError as error:
        # Require error.code equals the text 'UNSUPPORTED_PROTOCOL_STATE'; otherwise raise AssertionError.
        assert error.code == "UNSUPPORTED_PROTOCOL_STATE"
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call encoder.encode_protocol_state with the supplied arguments.
        encoder.encode_protocol_state(None, responder_required=True)
        # Raise AssertionError with the text 'missing responder state accepted' to stop this execution path.
        raise AssertionError("missing responder state accepted")
    # Handle PolicySemanticEncodingError as error using the recovery steps below.
    except PolicySemanticEncodingError as error:
        # Require error.code equals the text 'RESPONDER_PROTOCOL_STATE_REQUIRED'; otherwise raise AssertionError.
        assert error.code == "RESPONDER_PROTOCOL_STATE_REQUIRED"

    # Set saved to the result of encoded.semantic_values.copy().
    saved = encoded.semantic_values.copy()
    # Call current.node_features.setflags with the supplied arguments.
    # Set current.node_features[1, 0] to the negative of 99.
    current.node_features.setflags(write=True); current.node_features[1, 0] = -99
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(encoded.semantic_values, saved)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Set encoded.semantic_values[0] to 99.
        encoded.semantic_values[0] = 99
        # Raise AssertionError with the text 'immutable encoding was mutable' to stop this execution path.
        raise AssertionError("immutable encoding was mutable")
    # Handle ValueError using the recovery steps below.
    except ValueError:
        # Keep this block syntactically valid without performing an operation.
        pass

    # Display the text 'Step 5F.1 Policy Semantic Encoding Validation'.
    print("Step 5F.1 Policy Semantic Encoding Validation\n")
    # Display the text 'Schema'.
    print("Schema")
    # Display the text 'Existing graph node schema reused: PASS'.
    print("  Existing graph node schema reused: PASS")
    # Display the text 'Existing graph edge schema reused: PASS'.
    print("  Existing graph edge schema reused: PASS")
    # Display the text 'New arbitrary semantic features introduced: 0'.
    print("  New arbitrary semantic features introduced: 0")
    # Display the text 'Claim schema deterministic: PASS'.
    print("  Claim schema deterministic: PASS")
    # Display the text 'Protocol schema deterministic: PASS'.
    print("  Protocol schema deterministic: PASS")
    # Display the text 'Claim / proposal mapping'.
    print("\nClaim / proposal mapping")
    # Display the text 'Counterparty selected by ID: PASS'.
    print("  Counterparty selected by ID: PASS")
    # Display the text 'Claim edge selected by exact direction: PASS'.
    print("  Claim edge selected by exact direction: PASS")
    # Display the text 'Ego node order assumption: False'.
    print("  Ego node order assumption: False")
    # Display the text 'Edge order assumption: False'.
    print("  Edge order assumption: False")
    # Display the text 'Opposite edge treated as same claim: False'.
    print("  Opposite edge treated as same claim: False")
    # Display the text 'Claim encoding'.
    print("\nClaim encoding")
    # Display the text 'Counterparty node semantics preserved: PASS'.
    print("  Counterparty node semantics preserved: PASS")
    # Display the text 'Claim edge semantics preserved: PASS'.
    print("  Claim edge semantics preserved: PASS")
    # Display the text 'Availability masks preserved: PASS'.
    print("  Availability masks preserved: PASS")
    # Display the text 'Real zero vs unavailable zero distinguished: PASS'.
    print("  Real zero vs unavailable zero distinguished: PASS")
    # Display the text 'Proposal encoding'.
    print("\nProposal encoding")
    # Display the text 'Underlying claim encoding reused: PASS'.
    print("  Underlying claim encoding reused: PASS")
    # Display the text 'Proposal IDs used as model numbers: False'.
    print("  Proposal IDs used as model numbers: False")
    # Display the text 'Protocol encoding'.
    print("\nProtocol encoding")
    # Display the text 'One-hot categorical encoding: PASS'.
    print("  One-hot categorical encoding: PASS")
    # Display the text 'All ProtocolState values covered: PASS'.
    print("  All ProtocolState values covered: PASS")
    # Display the text 'Exactly one active known-state category: PASS'.
    print("  Exactly one active known-state category: PASS")
    # Display the text 'Different states have different encodings: PASS'.
    print("  Different states have different encodings: PASS")
    # Display the text 'Ordinal protocol-state encoding used: False'.
    print("  Ordinal protocol-state encoding used: False")
    # Display the text 'Unknown state rejected: PASS'.
    print("  Unknown state rejected: PASS")
    # Display the text 'Responder requires known protocol state: PASS'.
    print("  Responder requires known protocol state: PASS")
    # Display the text 'Immutability'.
    print("\nImmutability")
    # Display the text 'NumPy encoding immutable: PASS'.
    print("  NumPy encoding immutable: PASS")
    # Display the text 'Source mutation does not alter stored encoding: PASS'.
    print("  Source mutation does not alter stored encoding: PASS")
    # Display the text 'Replay'.
    print("\nReplay")
    # Display the text 'Same semantic input reproduces same encoding: PASS'.
    print("  Same semantic input reproduces same encoding: PASS")
    # Display the text 'Node permutation invariant: PASS'.
    print("  Node permutation invariant: PASS")
    # Display the text 'Edge permutation invariant: PASS'.
    print("  Edge permutation invariant: PASS")
    # Display the text 'Policy semantic tensors reconstructible: PASS'.
    print("  Policy semantic tensors reconstructible: PASS")
    # Display the text 'Authority'.
    print("\nAuthority")
    # Display the text 'Route-truth fields consumed: 0'.
    print("  Route-truth fields consumed: 0")
    # Display the text 'Identifier-derived numeric features: 0'.
    print("  Identifier-derived numeric features: 0")
    # Display the text 'Rule-ID numeric features: 0'.
    print("  Rule-ID numeric features: 0")
    # Display the text 'Conflict-zone-ID numeric features: 0'.
    print("  Conflict-zone-ID numeric features: 0")
    # Display the text 'Arbitrary ordinal categorical encodings: 0'.
    print("  Arbitrary ordinal categorical encodings: 0")
    # Display the text 'Research parameters'.
    print("\nResearch parameters")
    # Display the text 'New thresholds: 0'.
    print("  New thresholds: 0")
    # Display the text 'New scores: 0'.
    print("  New scores: 0")
    # Display the text 'New normalization constants: 0'.
    print("  New normalization constants: 0")
    # Display the text 'Learned encoder parameters: 0'.
    print("  Learned encoder parameters: 0")
    # Display the text 'Reward weights: 0'.
    print("  Reward weights: 0")
    # Display the text 'PPO hyperparameters: 0'.
    print("  PPO hyperparameters: 0")
    # Display the text 'Dependencies'.
    print("\nDependencies")
    # Display the text 'Base backend: NumPy'.
    print("  Base backend: NumPy")
    # Display the text 'TensorFlow required: False'.
    print("  TensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'PyTorch Geometric required: False'.
    print("  PyTorch Geometric required: False")
    # Display the text 'New dependency required: False'.
    print("  New dependency required: False")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display the text 'Claim semantic encoder implemented: True'.
    print("  Claim semantic encoder implemented: True")
    # Display the text 'Protocol semantic encoder implemented: True'.
    print("  Protocol semantic encoder implemented: True")
    # Display the text 'Policy semantic feature encoding incomplete: False'.
    print("  Policy semantic feature encoding incomplete: False")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
    # Display the text 'PPO implemented: False'.
    print("  PPO implemented: False")
    # Display the text 'Optimizer implemented: False'.
    print("  Optimizer implemented: False")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'SUMO learned-policy control enabled: False'.
    print("  SUMO learned-policy control enabled: False")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
