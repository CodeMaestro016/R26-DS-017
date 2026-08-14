"""Deterministic claim/proposal and protocol-state semantic encoding."""

import numpy as np

from ..protocol import ClaimRelinquishmentProposal, ProtocolState
from ..tensor_encoding.schemas import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA
from .models import EncodedClaimOrProposalSemantics, EncodedProtocolStateSemantics


CLAIM_SCHEMA_ID = "CLAIM_SEMANTIC_SCHEMA_V1"
PROTOCOL_SCHEMA_ID = "PROTOCOL_STATE_SEMANTIC_SCHEMA_V1"
REGULATORY_RULE_ID_FEATURE_STATUS = (
    "NOT_INCLUDED_BASELINE_AVOIDS_REDUNDANT_ARBITRARY_VOCABULARY"
)
DIMENSION_STATUS = "DERIVED_SCHEMA_DIMENSIONS"
SEMANTIC_ENCODING_STATUS = "COMPLETE_STEP_5F_1"

CLAIM_COLUMNS = tuple(
    f"counterparty_node.{name}" for name in NODE_NUMERIC_SCHEMA
) + tuple(
    f"claim_edge.{name}" for name in EDGE_NUMERIC_SCHEMA
)
PROTOCOL_STATE_COLUMNS = tuple(
    f"protocol.{state.value}" for state in ProtocolState
)


class PolicySemanticEncodingError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class NegotiationSemanticFeatureEncoder:
    """NumPy-only stateless encoder with zero learned parameters."""

    @staticmethod
    def _validate_graph_schema(graph):
        if tuple(graph.node_feature_names) != tuple(NODE_NUMERIC_SCHEMA):
            raise PolicySemanticEncodingError("SOURCE_NODE_SCHEMA_MISMATCH")
        if tuple(graph.edge_feature_names) != tuple(EDGE_NUMERIC_SCHEMA):
            raise PolicySemanticEncodingError("SOURCE_EDGE_SCHEMA_MISMATCH")

    def encode_claim(self, graph, ego_id, claim_identity):
        self._validate_graph_schema(graph)
        yielding, priority = tuple(claim_identity)
        if ego_id not in (yielding, priority):
            raise PolicySemanticEncodingError("EGO_NOT_PARTICIPANT_IN_CLAIM")
        counterparty = priority if ego_id == yielding else yielding
        matches = [index for index, node_id in enumerate(graph.node_ids)
                   if node_id == counterparty]
        if not matches:
            raise PolicySemanticEncodingError("CLAIM_COUNTERPARTY_NODE_NOT_FOUND")
        if len(matches) != 1:
            raise PolicySemanticEncodingError("CLAIM_COUNTERPARTY_NODE_AMBIGUOUS")
        node_index = {node_id: index for index, node_id in enumerate(graph.node_ids)}
        if yielding not in node_index or priority not in node_index:
            raise PolicySemanticEncodingError("CLAIM_EDGE_NOT_FOUND")
        edge_matches = [position for position in range(graph.edge_index.shape[1])
                        if tuple(graph.edge_index[:, position]) == (
                            node_index[yielding], node_index[priority]
                        )]
        if not edge_matches:
            raise PolicySemanticEncodingError("CLAIM_EDGE_NOT_FOUND")
        if len(edge_matches) != 1:
            raise PolicySemanticEncodingError("CLAIM_EDGE_AMBIGUOUS")
        node_position, edge_position = matches[0], edge_matches[0]
        values = np.concatenate((
            graph.node_features[node_position], graph.edge_features[edge_position],
        ))
        mask = np.concatenate((
            graph.node_feature_mask[node_position],
            graph.edge_feature_mask[edge_position],
        ))
        return EncodedClaimOrProposalSemantics(
            CLAIM_SCHEMA_ID, ego_id, counterparty, (yielding, priority), None,
            values, mask, CLAIM_COLUMNS, tuple(graph.node_feature_names),
            tuple(graph.edge_feature_names),
            (tuple(graph.node_feature_names), tuple(graph.edge_feature_names)),
            graph.normalization_status,
            {
                "source_graph_scope": graph.source_graph_scope,
                "communication_model": graph.communication_model,
                "edge_direction": "YIELDING_TO_PRIORITY",
                "identifier_features_in_numeric_vector": 0,
            },
        )

    def encode_proposal(self, graph, ego_id, proposal):
        if not isinstance(proposal, ClaimRelinquishmentProposal):
            raise TypeError("CLAIM_RELINQUISHMENT_PROPOSAL_REQUIRED")
        encoded = self.encode_claim(
            graph, ego_id,
            (proposal.yielding_vehicle_id, proposal.priority_vehicle_id),
        )
        return EncodedClaimOrProposalSemantics(
            encoded.schema_id, encoded.ego_id, encoded.counterparty_id,
            encoded.claim_identity, proposal.proposal_id,
            encoded.semantic_values, encoded.availability_mask,
            encoded.column_names, encoded.source_node_schema,
            encoded.source_edge_schema, encoded.source_schema_identity,
            encoded.normalization_status,
            {**encoded.provenance, "semantic_subject": "PROPOSAL_UNDERLYING_CLAIM"},
        )

    @staticmethod
    def encode_protocol_state(protocol_state, responder_required=False):
        if protocol_state is None:
            if responder_required:
                raise PolicySemanticEncodingError("RESPONDER_PROTOCOL_STATE_REQUIRED")
            values = np.zeros(len(PROTOCOL_STATE_COLUMNS), dtype=np.float32)
            mask = np.zeros(len(PROTOCOL_STATE_COLUMNS), dtype=np.bool_)
            state_name = None
        else:
            try:
                state = (protocol_state if isinstance(protocol_state, ProtocolState)
                         else ProtocolState(protocol_state))
            except (TypeError, ValueError) as error:
                raise PolicySemanticEncodingError("UNSUPPORTED_PROTOCOL_STATE") from error
            values = np.asarray(
                [float(candidate is state) for candidate in ProtocolState],
                dtype=np.float32,
            )
            mask = np.ones(len(PROTOCOL_STATE_COLUMNS), dtype=np.bool_)
            state_name = state.value
        return EncodedProtocolStateSemantics(
            PROTOCOL_SCHEMA_ID, state_name, values, mask,
            PROTOCOL_STATE_COLUMNS, "CATEGORICAL_IDENTITY_NO_NORMALIZATION",
            {"encoding": "ONE_HOT_IDENTITY", "ordinal_meaning": False},
        )
