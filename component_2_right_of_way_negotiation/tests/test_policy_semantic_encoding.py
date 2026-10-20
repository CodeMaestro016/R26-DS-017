"""Step 5F.1 deterministic claim/proposal/protocol encoding tests."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
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
# Import NegotiationDecisionRole, NegotiationPolicyContextBuilder from negotiation_learning.mappo_interface for
# the operations below.
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyContextBuilder,
)
# Import NegotiationAction from negotiation_learning.models for the operations below.
from negotiation_learning.models import NegotiationAction
# Import ClaimRelinquishmentProposal, ProtocolState from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import ClaimRelinquishmentProposal, ProtocolState
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


# Set TEST_ONLY_NON_OPERATIONAL_VALUE to 4.
TEST_ONLY_NON_OPERATIONAL_VALUE = 4


# Graph using the inputs and processing steps below.
# Input node_ids: the supplied node ids.
# Input edges: the supplied edges.
# Input ego: the ego vehicle used in this calculation.
# Input node_values: the supplied node values.
# Input node_masks: the supplied node masks.
# Input edge_values: the supplied edge values.
# Input edge_masks: the supplied edge masks.
# Output: the result of EncodedGraphObservation(ego, a tuple built from node_ids, node_values, node_masks,
# edge_index, edge_values, edge_masks,...).
def graph(node_ids=("A", "B"), edges=(("A", "B"),), ego="B",
          # Declare node_values, node_masks, edge_values, edge_masks as input parameters.
          node_values=None, node_masks=None, edge_values=None, edge_masks=None):
    # Set node_values to the result of np.arange(len(node_ids) * len(NODE_NUMERIC_SCHEMA),
    # dtype=np.float32).reshape(the number of entries in node_ids, the negative of 1) when node_values is the same
    # object as None, otherwise node_values.
    node_values = (np.arange(len(node_ids) * len(NODE_NUMERIC_SCHEMA),
                             # Supply dtype as np.float32.
                             dtype=np.float32).reshape(len(node_ids), -1)
                   # Evaluate node_values is the same object as None as part of the enclosing expression.
                   if node_values is None else node_values)
    # Set node_masks to the result of np.ones_like(node_values) when node_masks is the same object as None,
    # otherwise node_masks.
    node_masks = (np.ones_like(node_values, dtype=np.bool_)
                  # Evaluate node_masks is the same object as None as part of the enclosing expression.
                  if node_masks is None else node_masks)
    # Set edge_values to the result of np.arange(len(edges) * len(EDGE_NUMERIC_SCHEMA),
    # dtype=np.float32).reshape(the number of entries in edges, the number of entries in EDGE_NUMERIC_SCHEMA) when
    # edge_values is the same object as None, otherwise edge_values.
    edge_values = (np.arange(len(edges) * len(EDGE_NUMERIC_SCHEMA),
                             # Supply dtype as np.float32.
                             dtype=np.float32).reshape(
                                 # Supply the number of entries in EDGE_NUMERIC_SCHEMA to np.arange(len(edges) *
                                 # len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape.
                                 len(edges), len(EDGE_NUMERIC_SCHEMA)
                             )
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
    # Set edge_index to np.asarray([(index[a], index[b]) for a, b in edges], dtype=np.int64).reshape(-1, 2).T.
    edge_index = np.asarray([(index[a], index[b]) for a, b in edges],
                            # Supply dtype as np.int64.
                            dtype=np.int64).reshape(-1, 2).T
    # Return the result of EncodedGraphObservation(ego, a tuple built from node_ids, node_values, node_masks,
    # edge_index, edge_values, edge_masks,...) to the caller.
    return EncodedGraphObservation(
        # Supply a tuple built from node_ids to EncodedGraphObservation.
        ego, tuple(node_ids), node_values, node_masks, edge_index,
        # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


# Proposal using the inputs and processing steps below.
# Output: the result of ClaimRelinquishmentProposal(a tuple containing 1.0, the text 'A', the text 'B', the text
# 'B', the text 'A', the text 'B',...).
def proposal():
    # Return the result of ClaimRelinquishmentProposal(a tuple containing 1.0, the text 'A', the text 'B', the
    # text 'B', the text 'A', the text 'B',...) to the caller.
    return ClaimRelinquishmentProposal(
        # Supply a tuple containing 1.0, the text 'A', the text 'B', the text 'B', the text 'A' to
        # ClaimRelinquishmentProposal.
        (1.0, "A", "B", "B", "A"), "B", "A", "A", "B",
        # Supply NegotiationAction.RELINQUISH_CLAIM to ClaimRelinquishmentProposal.
        NegotiationAction.RELINQUISH_CLAIM, 1.0, 1.0,
        # Supply a tuple containing the text 'SECTION' to ClaimRelinquishmentProposal.
        "DE_STVO_UNCONTROLLED_4WAY_V1", ("RULE",), ("SECTION",), ("ZONE",),
    )


# Check exact counterparty and directed edge are selected by identity using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_exact_counterparty_and_directed_edge_are_selected_by_identity():
    # Set encoded to the result of NegotiationSemanticFeatureEncoder().encode_claim(the result of graph(a tuple
    # containing the text 'B', the text 'A', a tuple containing a tuple...).
    encoded = NegotiationSemanticFeatureEncoder().encode_claim(
        # Supply the result of graph(a tuple containing the text 'B', the text 'A', a tuple containing a tuple
        # containing the text...) to NegotiationSemanticFeatureEncoder().encode_claim.
        graph(("B", "A"), (("A", "B"),)), "B", ("A", "B")
    )
    # Require encoded.counterparty_id equals the text 'A'; otherwise raise AssertionError.
    assert encoded.counterparty_id == "A"
    # Require encoded.claim_identity equals a tuple containing the text 'A', the text 'B'; otherwise raise
    # AssertionError.
    assert encoded.claim_identity == ("A", "B")
    # Require encoded.column_names equals CLAIM_COLUMNS; otherwise raise AssertionError.
    assert encoded.column_names == CLAIM_COLUMNS
    # Require encoded.semantic_values.shape equals a tuple containing the number of entries in NODE_NUMERIC_SCHEMA
    # plus the number of entries in EDGE_NUMERIC_SCHEMA; otherwise raise AssertionError.
    assert encoded.semantic_values.shape == (
        # Include the number of entries in NODE_NUMERIC_SCHEMA plus the number of entries in EDGE_NUMERIC_SCHEMA
        # in this tuple.
        len(NODE_NUMERIC_SCHEMA) + len(EDGE_NUMERIC_SCHEMA),
    )
    # Require encoded.model_input.shape equals a tuple containing 2 multiplied by the number of entries in
    # CLAIM_COLUMNS; otherwise raise AssertionError.
    assert encoded.model_input.shape == (2 * len(CLAIM_COLUMNS),)


# Check node and edge order permutations preserve claim semantics using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_node_and_edge_order_permutations_preserve_claim_semantics():
    # Set node_values to the result of np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, the
    # negative of 1).
    node_values = np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, -1)
    # Set edge_values to the result of np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, the
    # negative of 1).
    edge_values = np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, -1)
    # Set first to the result of graph(a tuple containing the text 'A', the text 'B', the text 'C', a tuple
    # containing a tuple...).
    first = graph(("A", "B", "C"), (("A", "B"), ("C", "B")),
                  # Supply node_values as node_values.
                  # Supply edge_values as edge_values.
                  node_values=node_values, edge_values=edge_values)
    # Set second to the result of graph(a tuple containing the text 'C', the text 'B', the text 'A', a tuple
    # containing a tuple...).
    second = graph(("C", "B", "A"), (("C", "B"), ("A", "B")),
                   # Supply node_values as node_values at [2, 1, 0].
                   node_values=node_values[[2, 1, 0]],
                   # Supply edge_values as edge_values at [1, 0].
                   edge_values=edge_values[[1, 0]])
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Set a to the result of encoder.encode_claim(first, the text 'B', a tuple containing the text 'A', the text
    # 'B').
    a = encoder.encode_claim(first, "B", ("A", "B"))
    # Set b to the result of encoder.encode_claim(second, the text 'B', a tuple containing the text 'A', the text
    # 'B').
    b = encoder.encode_claim(second, "B", ("A", "B"))
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(a.semantic_values, b.semantic_values)
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(a.availability_mask, b.availability_mask)


# Apply 'case,code' as a decorator to configure the following definition.
@pytest.mark.parametrize("case,code", (
    # Include a tuple containing the text 'ego', the text 'EGO_NOT_PARTICIPANT_IN_CLAIM' in this tuple.
    ("ego", "EGO_NOT_PARTICIPANT_IN_CLAIM"),
    # Include a tuple containing the text 'node', the text 'CLAIM_COUNTERPARTY_NODE_NOT_FOUND' in this tuple.
    ("node", "CLAIM_COUNTERPARTY_NODE_NOT_FOUND"),
    # Include a tuple containing the text 'edge', the text 'CLAIM_EDGE_NOT_FOUND' in this tuple.
    ("edge", "CLAIM_EDGE_NOT_FOUND"),
    # Include a tuple containing the text 'wrong_direction', the text 'CLAIM_EDGE_NOT_FOUND' in this tuple.
    ("wrong_direction", "CLAIM_EDGE_NOT_FOUND"),
))
# Check invalid claim mapping fails categorically using the setup, calls, and assertions below.
# Input case: the supplied case.
# Input code: the supplied code.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_invalid_claim_mapping_fails_categorically(case, code):
    # Set (current, ego, claim) to a tuple containing the result of graph(), the text 'B', a tuple containing the
    # text 'A', the text 'B'.
    current, ego, claim = graph(), "B", ("A", "B")
    # Run this branch when case equals the text 'ego'.
    # Set ego to the text 'C'.
    if case == "ego": ego = "C"
    # Run this branch when case equals the text 'node'.
    # Set current to the result of graph(a tuple containing the text 'B', an empty tuple).
    elif case == "node": current = graph(("B",), (), node_values=np.zeros((1, len(NODE_NUMERIC_SCHEMA)), np.float32))
    # Run this branch when case equals the text 'edge'.
    # Set current to the result of graph().
    elif case == "edge": current = graph(edges=())
    # Run this branch when case equals the text 'wrong_direction'.
    # Set current to the result of graph().
    elif case == "wrong_direction": current = graph(edges=(("B", "A"),))
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match=code):
        # Call NegotiationSemanticFeatureEncoder().encode_claim with the supplied arguments.
        NegotiationSemanticFeatureEncoder().encode_claim(current, ego, claim)


# Check ambiguous node and edge fail instead of selecting first using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_ambiguous_node_and_edge_fail_instead_of_selecting_first():
    # Set duplicate_node to the result of graph(a tuple containing the text 'A', the text 'A', the text 'B', a
    # tuple containing a tuple...).
    duplicate_node = graph(("A", "A", "B"), (("A", "B"),))
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match="NODE_AMBIGUOUS"):
        # Call NegotiationSemanticFeatureEncoder().encode_claim with the supplied arguments.
        NegotiationSemanticFeatureEncoder().encode_claim(
            # Supply duplicate_node to NegotiationSemanticFeatureEncoder().encode_claim.
            duplicate_node, "B", ("A", "B")
        )
    # Set duplicate_edge to the result of graph().
    duplicate_edge = graph(edges=(("A", "B"), ("A", "B")))
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match="EDGE_AMBIGUOUS"):
        # Call NegotiationSemanticFeatureEncoder().encode_claim with the supplied arguments.
        NegotiationSemanticFeatureEncoder().encode_claim(
            # Supply duplicate_edge to NegotiationSemanticFeatureEncoder().encode_claim.
            duplicate_edge, "B", ("A", "B")
        )


# Check real zero and unavailable zero remain distinct using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_real_zero_and_unavailable_zero_remain_distinct():
    # Set values to a zero-filled tensor with the requested shape.
    values = np.zeros((2, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    # Set masks to the result of np.ones_like(values).
    masks = np.ones_like(values, dtype=np.bool_)
    # Set unavailable_masks to the result of masks.copy().
    # Set unavailable_masks[0, 1] to False.
    unavailable_masks = masks.copy(); unavailable_masks[0, 1] = False
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Set real to the result of encoder.encode_claim(the result of graph(), the text 'B', a tuple containing the
    # text 'A', the text 'B').
    real = encoder.encode_claim(graph(node_values=values, node_masks=masks),
                                # Supply a tuple containing the text 'A', the text 'B' to encoder.encode_claim.
                                "B", ("A", "B"))
    # Set missing to the result of encoder.encode_claim(the result of graph(), the text 'B', a tuple containing
    # the text 'A', the text 'B').
    missing = encoder.encode_claim(
        # Supply node_values as values.
        # Supply node_masks as unavailable_masks.
        graph(node_values=values, node_masks=unavailable_masks), "B", ("A", "B")
    )
    # Require real.semantic_values at 1 equals missing.semantic_values at 1; equals 0; otherwise raise
    # AssertionError.
    assert real.semantic_values[1] == missing.semantic_values[1] == 0
    # Require real.model_input at len(CLAIM_COLUMNS) + 1 equals 1; otherwise raise AssertionError.
    assert real.model_input[len(CLAIM_COLUMNS) + 1] == 1
    # Require missing.model_input at len(CLAIM_COLUMNS) + 1 equals 0; otherwise raise AssertionError.
    assert missing.model_input[len(CLAIM_COLUMNS) + 1] == 0


# Check proposal reuses claim encoding and keeps id metadata only using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_proposal_reuses_claim_encoding_and_keeps_id_metadata_only():
    # Set (encoder, current) to a tuple containing the result of NegotiationSemanticFeatureEncoder(), the result
    # of graph().
    encoder, current = NegotiationSemanticFeatureEncoder(), graph()
    # Set claim to the result of encoder.encode_claim(current, the text 'A', a tuple containing the text 'A', the
    # text 'B').
    claim = encoder.encode_claim(current, "A", ("A", "B"))
    # Set proposed to the result of encoder.encode_proposal(current, the text 'A', the result of proposal()).
    proposed = encoder.encode_proposal(current, "A", proposal())
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(claim.model_input, proposed.model_input)
    # Require proposed.proposal_id equals proposal().proposal_id; otherwise raise AssertionError.
    assert proposed.proposal_id == proposal().proposal_id
    # Require proposed.model_input.shape equals claim.model_input.shape; otherwise raise AssertionError.
    assert proposed.model_input.shape == claim.model_input.shape


# Check protocol enum is exhaustive unique one hot identity using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_protocol_enum_is_exhaustive_unique_one_hot_identity():
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Set results to a list of the result of encoder.encode_protocol_state(state) for state in ProtocolState.
    results = [encoder.encode_protocol_state(state, responder_required=True)
               # Evaluate ProtocolState as part of the enclosing expression.
               for state in ProtocolState]
    # Require the number of entries in PROTOCOL_STATE_COLUMNS equals the number of entries in ProtocolState;
    # otherwise raise AssertionError.
    assert len(PROTOCOL_STATE_COLUMNS) == len(ProtocolState)
    # Require a set built from PROTOCOL_STATE_COLUMNS equals a set of formatted text built from the embedded
    # values for state in ProtocolState; otherwise raise AssertionError.
    assert set(PROTOCOL_STATE_COLUMNS) == {
        # Evaluate formatted text built from the embedded values as part of the enclosing expression.
        f"protocol.{state.value}" for state in ProtocolState
    }
    # Require whether every item is true in a lazy sequence of the result of item.semantic_values.sum() equals 1
    # for item in results; otherwise raise AssertionError.
    assert all(item.semantic_values.sum() == 1 for item in results)
    # Require whether every item is true in a lazy sequence of the result of item.availability_mask.all() for item
    # in results; otherwise raise AssertionError.
    assert all(item.availability_mask.all() for item in results)
    # Require the number of entries in a set of a tuple built from item.semantic_values for item in results equals
    # the number of entries in results; otherwise raise AssertionError.
    assert len({tuple(item.semantic_values) for item in results}) == len(results)
    # Require whether every item is true in a lazy sequence of the result of set(item.semantic_values).issubset(a
    # set containing 0.0, 1.0) for item in results; otherwise raise AssertionError.
    assert all(set(item.semantic_values).issubset({0.0, 1.0}) for item in results)


# Check unknown and missing responder protocol state are rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unknown_and_missing_responder_protocol_state_are_rejected():
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match="UNSUPPORTED_PROTOCOL_STATE"):
        # Call encoder.encode_protocol_state with the supplied arguments.
        encoder.encode_protocol_state("UNSUPPORTED")
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match="RESPONDER_PROTOCOL_STATE_REQUIRED"):
        # Call encoder.encode_protocol_state with the supplied arguments.
        encoder.encode_protocol_state(None, responder_required=True)
    # Set not_applicable to the result of encoder.encode_protocol_state(None).
    not_applicable = encoder.encode_protocol_state(None)
    # Require the negation of the result of not_applicable.availability_mask.any(); otherwise raise
    # AssertionError.
    assert not not_applicable.availability_mask.any()
    # Require the negation of the result of not_applicable.semantic_values.any(); otherwise raise AssertionError.
    assert not not_applicable.semantic_values.any()


# Check arrays are copied read only and repeat is deterministic using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_arrays_are_copied_read_only_and_repeat_is_deterministic():
    # Set current to the result of graph().
    current = graph()
    # Set encoder to the result of NegotiationSemanticFeatureEncoder().
    encoder = NegotiationSemanticFeatureEncoder()
    # Set first to the result of encoder.encode_claim(current, the text 'B', a tuple containing the text 'A', the
    # text 'B').
    first = encoder.encode_claim(current, "B", ("A", "B"))
    # Set saved to the result of first.semantic_values.copy().
    saved = first.semantic_values.copy()
    # Call current.node_features.setflags with the supplied arguments.
    # Set current.node_features[0, 0] to the negative of 123.
    current.node_features.setflags(write=True); current.node_features[0, 0] = -123
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(first.semantic_values, saved)
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    # Set first.semantic_values[0] to 99.
    with pytest.raises(ValueError): first.semantic_values[0] = 99
    # Set second to the result of encoder.encode_claim(the result of graph(), the text 'B', a tuple containing the
    # text 'A', the text 'B').
    second = encoder.encode_claim(graph(), "B", ("A", "B"))
    # Call np.testing.assert_array_equal with the supplied arguments.
    np.testing.assert_array_equal(saved, second.semantic_values)


# Check schema mismatch is explicit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_schema_mismatch_is_explicit():
    # Set current to the result of replace(the result of graph()).
    current = replace(graph(), node_feature_names=("WRONG",) * len(NODE_NUMERIC_SCHEMA))
    # Enter the result of pytest.raises(PolicySemanticEncodingError) and run the enclosed operations within that
    # context.
    with pytest.raises(PolicySemanticEncodingError, match="SOURCE_NODE_SCHEMA_MISMATCH"):
        # Call NegotiationSemanticFeatureEncoder().encode_claim with the supplied arguments.
        NegotiationSemanticFeatureEncoder().encode_claim(current, "B", ("A", "B"))


# Check real policy context uses derived semantic encodings using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_real_policy_context_uses_derived_semantic_encodings():
    # Set (current, encoder) to a tuple containing the result of graph(), the result of
    # NegotiationSemanticFeatureEncoder().
    current, encoder = graph(), NegotiationSemanticFeatureEncoder()
    # Set gnn to the result of EdgeAwareMPNNEncoder(len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),...(the
    # result of to_torch_graph(current)).
    gnn = EdgeAwareMPNNEncoder(
        # Supply the number of entries in NODE_NUMERIC_SCHEMA to EdgeAwareMPNNEncoder.
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        # Supply TEST_ONLY_NON_OPERATIONAL_VALUE to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_VALUE, 1,
    # Supply the result of to_torch_graph(current) to EdgeAwareMPNNEncoder(len(NODE_NUMERIC_SCHEMA),
    # len(EDGE_NUMERIC_SCHEMA),...
    )(to_torch_graph(current))
    # Set claim to the result of encoder.encode_claim(current, the text 'B', a tuple containing the text 'A', the
    # text 'B').
    claim = encoder.encode_claim(current, "B", ("A", "B"))
    # Set proposer to the result of NegotiationPolicyContextBuilder.build(NegotiationDecisionRole.PROPOSER, the
    # text 'GRAPH', 1.0, gnn, claim, a tuple containing True,...).
    proposer = NegotiationPolicyContextBuilder.build(
        # Supply NegotiationDecisionRole.PROPOSER to NegotiationPolicyContextBuilder.build.
        NegotiationDecisionRole.PROPOSER, "GRAPH", 1.0, gnn, claim,
        # Supply a tuple containing True, True to NegotiationPolicyContextBuilder.build.
        (True, True), "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )
    # Require proposer.claim_or_proposal_representation.shape equals a tuple containing 2 multiplied by the number
    # of entries in CLAIM_COLUMNS; otherwise raise AssertionError.
    assert proposer.claim_or_proposal_representation.shape == (2 * len(CLAIM_COLUMNS),)
    # Require proposer.protocol_state_representation is the same object as None; otherwise raise AssertionError.
    assert proposer.protocol_state_representation is None
    # Set proposed to the result of encoder.encode_proposal(current, the text 'A', the result of proposal()).
    proposed = encoder.encode_proposal(current, "A", proposal())
    # Set protocol to the result of encoder.encode_protocol_state(ProtocolState.PROPOSAL_PENDING, True).
    protocol = encoder.encode_protocol_state(ProtocolState.PROPOSAL_PENDING, True)
    # Set responder to the result of NegotiationPolicyContextBuilder.build(NegotiationDecisionRole.RESPONDER, the
    # text 'GRAPH', 1.0, gnn, proposed, a tuple containing...).
    responder = NegotiationPolicyContextBuilder.build(
        # Supply NegotiationDecisionRole.RESPONDER to NegotiationPolicyContextBuilder.build.
        NegotiationDecisionRole.RESPONDER, "GRAPH", 1.0, gnn, proposed,
        # Supply a tuple containing True, True to NegotiationPolicyContextBuilder.build.
        (True, True), "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
        # Supply protocol to NegotiationPolicyContextBuilder.build.
        protocol,
    )
    # Require responder.protocol_state_representation.shape equals a tuple containing 2 multiplied by the number
    # of entries in PROTOCOL_STATE_COLUMNS; otherwise raise AssertionError.
    assert responder.protocol_state_representation.shape == (
        # Include 2 multiplied by the number of entries in PROTOCOL_STATE_COLUMNS in this tuple.
        2 * len(PROTOCOL_STATE_COLUMNS),
    )


# Check encoder is numpy only and excludes identifier numeric features using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_encoder_is_numpy_only_and_excludes_identifier_numeric_features():
    # Set root to Path(__file__).parents at 1 joined with the path segment 'negotiation_learning' joined with the path segment
    # 'semantic_encoding'.
    root = Path(__file__).parents[1] / "negotiation_learning" / "semantic_encoding"
    # Set source to the result of '\n'.join(a lazy sequence of the result of path.read_text().lower() for path in
    # the result of...).
    source = "\n".join(path.read_text().lower() for path in root.glob("*.py"))
    # Require the text 'import torch' does not belong to source and the text 'from torch' does not belong to
    # source; otherwise raise AssertionError.
    assert "import torch" not in source and "from torch" not in source
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text
    # 'ground_truth_route_id', the text 'future_route',...
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "parse", "hash(", "random", "normalize")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
