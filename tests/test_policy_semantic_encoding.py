"""Step 5F.1 deterministic claim/proposal/protocol encoding tests."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyContextBuilder,
)
from negotiation_learning.models import NegotiationAction
from negotiation_learning.protocol import ClaimRelinquishmentProposal, ProtocolState
from negotiation_learning.semantic_encoding import (
    CLAIM_COLUMNS, PROTOCOL_STATE_COLUMNS, NegotiationSemanticFeatureEncoder,
    PolicySemanticEncodingError,
)
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


TEST_ONLY_NON_OPERATIONAL_VALUE = 4


def graph(node_ids=("A", "B"), edges=(("A", "B"),), ego="B",
          node_values=None, node_masks=None, edge_values=None, edge_masks=None):
    node_values = (np.arange(len(node_ids) * len(NODE_NUMERIC_SCHEMA),
                             dtype=np.float32).reshape(len(node_ids), -1)
                   if node_values is None else node_values)
    node_masks = (np.ones_like(node_values, dtype=np.bool_)
                  if node_masks is None else node_masks)
    edge_values = (np.arange(len(edges) * len(EDGE_NUMERIC_SCHEMA),
                             dtype=np.float32).reshape(
                                 len(edges), len(EDGE_NUMERIC_SCHEMA)
                             )
                   if edge_values is None else edge_values)
    edge_masks = (np.ones_like(edge_values, dtype=np.bool_)
                  if edge_masks is None else edge_masks)
    index = {name: position for position, name in enumerate(node_ids)}
    edge_index = np.asarray([(index[a], index[b]) for a, b in edges],
                            dtype=np.int64).reshape(-1, 2).T
    return EncodedGraphObservation(
        ego, tuple(node_ids), node_values, node_masks, edge_index,
        edge_values, edge_masks, NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )


def proposal():
    return ClaimRelinquishmentProposal(
        (1.0, "A", "B", "B", "A"), "B", "A", "A", "B",
        NegotiationAction.RELINQUISH_CLAIM, 1.0, 1.0,
        "DE_STVO_UNCONTROLLED_4WAY_V1", ("RULE",), ("SECTION",), ("ZONE",),
    )


def test_exact_counterparty_and_directed_edge_are_selected_by_identity():
    encoded = NegotiationSemanticFeatureEncoder().encode_claim(
        graph(("B", "A"), (("A", "B"),)), "B", ("A", "B")
    )
    assert encoded.counterparty_id == "A"
    assert encoded.claim_identity == ("A", "B")
    assert encoded.column_names == CLAIM_COLUMNS
    assert encoded.semantic_values.shape == (
        len(NODE_NUMERIC_SCHEMA) + len(EDGE_NUMERIC_SCHEMA),
    )
    assert encoded.model_input.shape == (2 * len(CLAIM_COLUMNS),)


def test_node_and_edge_order_permutations_preserve_claim_semantics():
    node_values = np.arange(3 * len(NODE_NUMERIC_SCHEMA), dtype=np.float32).reshape(3, -1)
    edge_values = np.arange(2 * len(EDGE_NUMERIC_SCHEMA), dtype=np.float32).reshape(2, -1)
    first = graph(("A", "B", "C"), (("A", "B"), ("C", "B")),
                  node_values=node_values, edge_values=edge_values)
    second = graph(("C", "B", "A"), (("C", "B"), ("A", "B")),
                   node_values=node_values[[2, 1, 0]],
                   edge_values=edge_values[[1, 0]])
    encoder = NegotiationSemanticFeatureEncoder()
    a = encoder.encode_claim(first, "B", ("A", "B"))
    b = encoder.encode_claim(second, "B", ("A", "B"))
    np.testing.assert_array_equal(a.semantic_values, b.semantic_values)
    np.testing.assert_array_equal(a.availability_mask, b.availability_mask)


@pytest.mark.parametrize("case,code", (
    ("ego", "EGO_NOT_PARTICIPANT_IN_CLAIM"),
    ("node", "CLAIM_COUNTERPARTY_NODE_NOT_FOUND"),
    ("edge", "CLAIM_EDGE_NOT_FOUND"),
    ("wrong_direction", "CLAIM_EDGE_NOT_FOUND"),
))
def test_invalid_claim_mapping_fails_categorically(case, code):
    current, ego, claim = graph(), "B", ("A", "B")
    if case == "ego": ego = "C"
    elif case == "node": current = graph(("B",), (), node_values=np.zeros((1, len(NODE_NUMERIC_SCHEMA)), np.float32))
    elif case == "edge": current = graph(edges=())
    elif case == "wrong_direction": current = graph(edges=(("B", "A"),))
    with pytest.raises(PolicySemanticEncodingError, match=code):
        NegotiationSemanticFeatureEncoder().encode_claim(current, ego, claim)


def test_ambiguous_node_and_edge_fail_instead_of_selecting_first():
    duplicate_node = graph(("A", "A", "B"), (("A", "B"),))
    with pytest.raises(PolicySemanticEncodingError, match="NODE_AMBIGUOUS"):
        NegotiationSemanticFeatureEncoder().encode_claim(
            duplicate_node, "B", ("A", "B")
        )
    duplicate_edge = graph(edges=(("A", "B"), ("A", "B")))
    with pytest.raises(PolicySemanticEncodingError, match="EDGE_AMBIGUOUS"):
        NegotiationSemanticFeatureEncoder().encode_claim(
            duplicate_edge, "B", ("A", "B")
        )


def test_real_zero_and_unavailable_zero_remain_distinct():
    values = np.zeros((2, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    masks = np.ones_like(values, dtype=np.bool_)
    unavailable_masks = masks.copy(); unavailable_masks[0, 1] = False
    encoder = NegotiationSemanticFeatureEncoder()
    real = encoder.encode_claim(graph(node_values=values, node_masks=masks),
                                "B", ("A", "B"))
    missing = encoder.encode_claim(
        graph(node_values=values, node_masks=unavailable_masks), "B", ("A", "B")
    )
    assert real.semantic_values[1] == missing.semantic_values[1] == 0
    assert real.model_input[len(CLAIM_COLUMNS) + 1] == 1
    assert missing.model_input[len(CLAIM_COLUMNS) + 1] == 0


def test_proposal_reuses_claim_encoding_and_keeps_id_metadata_only():
    encoder, current = NegotiationSemanticFeatureEncoder(), graph()
    claim = encoder.encode_claim(current, "A", ("A", "B"))
    proposed = encoder.encode_proposal(current, "A", proposal())
    np.testing.assert_array_equal(claim.model_input, proposed.model_input)
    assert proposed.proposal_id == proposal().proposal_id
    assert proposed.model_input.shape == claim.model_input.shape


def test_protocol_enum_is_exhaustive_unique_one_hot_identity():
    encoder = NegotiationSemanticFeatureEncoder()
    results = [encoder.encode_protocol_state(state, responder_required=True)
               for state in ProtocolState]
    assert len(PROTOCOL_STATE_COLUMNS) == len(ProtocolState)
    assert set(PROTOCOL_STATE_COLUMNS) == {
        f"protocol.{state.value}" for state in ProtocolState
    }
    assert all(item.semantic_values.sum() == 1 for item in results)
    assert all(item.availability_mask.all() for item in results)
    assert len({tuple(item.semantic_values) for item in results}) == len(results)
    assert all(set(item.semantic_values).issubset({0.0, 1.0}) for item in results)


def test_unknown_and_missing_responder_protocol_state_are_rejected():
    encoder = NegotiationSemanticFeatureEncoder()
    with pytest.raises(PolicySemanticEncodingError, match="UNSUPPORTED_PROTOCOL_STATE"):
        encoder.encode_protocol_state("UNSUPPORTED")
    with pytest.raises(PolicySemanticEncodingError, match="RESPONDER_PROTOCOL_STATE_REQUIRED"):
        encoder.encode_protocol_state(None, responder_required=True)
    not_applicable = encoder.encode_protocol_state(None)
    assert not not_applicable.availability_mask.any()
    assert not not_applicable.semantic_values.any()


def test_arrays_are_copied_read_only_and_repeat_is_deterministic():
    current = graph()
    encoder = NegotiationSemanticFeatureEncoder()
    first = encoder.encode_claim(current, "B", ("A", "B"))
    saved = first.semantic_values.copy()
    current.node_features.setflags(write=True); current.node_features[0, 0] = -123
    np.testing.assert_array_equal(first.semantic_values, saved)
    with pytest.raises(ValueError): first.semantic_values[0] = 99
    second = encoder.encode_claim(graph(), "B", ("A", "B"))
    np.testing.assert_array_equal(saved, second.semantic_values)


def test_schema_mismatch_is_explicit():
    current = replace(graph(), node_feature_names=("WRONG",) * len(NODE_NUMERIC_SCHEMA))
    with pytest.raises(PolicySemanticEncodingError, match="SOURCE_NODE_SCHEMA_MISMATCH"):
        NegotiationSemanticFeatureEncoder().encode_claim(current, "B", ("A", "B"))


def test_real_policy_context_uses_derived_semantic_encodings():
    current, encoder = graph(), NegotiationSemanticFeatureEncoder()
    gnn = EdgeAwareMPNNEncoder(
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        TEST_ONLY_NON_OPERATIONAL_VALUE, 1,
    )(to_torch_graph(current))
    claim = encoder.encode_claim(current, "B", ("A", "B"))
    proposer = NegotiationPolicyContextBuilder.build(
        NegotiationDecisionRole.PROPOSER, "GRAPH", 1.0, gnn, claim,
        (True, True), "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )
    assert proposer.claim_or_proposal_representation.shape == (2 * len(CLAIM_COLUMNS),)
    assert proposer.protocol_state_representation is None
    proposed = encoder.encode_proposal(current, "A", proposal())
    protocol = encoder.encode_protocol_state(ProtocolState.PROPOSAL_PENDING, True)
    responder = NegotiationPolicyContextBuilder.build(
        NegotiationDecisionRole.RESPONDER, "GRAPH", 1.0, gnn, proposed,
        (True, True), "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
        protocol,
    )
    assert responder.protocol_state_representation.shape == (
        2 * len(PROTOCOL_STATE_COLUMNS),
    )


def test_encoder_is_numpy_only_and_excludes_identifier_numeric_features():
    root = Path(__file__).parents[1] / "negotiation_learning" / "semantic_encoding"
    source = "\n".join(path.read_text().lower() for path in root.glob("*.py"))
    assert "import torch" not in source and "from torch" not in source
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "parse", "hash(", "random", "normalize")
    assert not any(item in source for item in forbidden)
