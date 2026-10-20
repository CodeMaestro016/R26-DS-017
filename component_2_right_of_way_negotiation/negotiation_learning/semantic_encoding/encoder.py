"""Deterministic claim/proposal and protocol-state semantic encoding."""

# Import numpy as np for use in this module.
import numpy as np

# Import ClaimRelinquishmentProposal, ProtocolState from ..protocol for the operations below.
from ..protocol import ClaimRelinquishmentProposal, ProtocolState
# Import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from ..tensor_encoding.schemas for the operations below.
from ..tensor_encoding.schemas import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA
# Import EncodedClaimOrProposalSemantics, EncodedProtocolStateSemantics from .models for the operations below.
from .models import EncodedClaimOrProposalSemantics, EncodedProtocolStateSemantics


# Set CLAIM_SCHEMA_ID to the text 'CLAIM_SEMANTIC_SCHEMA_V1'.
CLAIM_SCHEMA_ID = "CLAIM_SEMANTIC_SCHEMA_V1"
# Set PROTOCOL_SCHEMA_ID to the text 'PROTOCOL_STATE_SEMANTIC_SCHEMA_V1'.
PROTOCOL_SCHEMA_ID = "PROTOCOL_STATE_SEMANTIC_SCHEMA_V1"
# Set REGULATORY_RULE_ID_FEATURE_STATUS to the text 'NOT_INCLUDED_BASELINE_AVOIDS_REDUNDANT_ARBITRARY_VOCABULARY'.
REGULATORY_RULE_ID_FEATURE_STATUS = (
    "NOT_INCLUDED_BASELINE_AVOIDS_REDUNDANT_ARBITRARY_VOCABULARY"
)
# Set DIMENSION_STATUS to the text 'DERIVED_SCHEMA_DIMENSIONS'.
DIMENSION_STATUS = "DERIVED_SCHEMA_DIMENSIONS"
# Set SEMANTIC_ENCODING_STATUS to the text 'COMPLETE_STEP_5F_1'.
SEMANTIC_ENCODING_STATUS = "COMPLETE_STEP_5F_1"

# Set CLAIM_COLUMNS to a tuple built from a lazy sequence of formatted text built from the embedded values for
# name in NODE_NUMERIC_SCHEMA plus a tuple built from a lazy sequence of formatted text built from the embedded
# values for name in EDGE_NUMERIC_SCHEMA.
CLAIM_COLUMNS = tuple(
    # Evaluate formatted text built from the embedded values as part of the enclosing expression.
    f"counterparty_node.{name}" for name in NODE_NUMERIC_SCHEMA
# Evaluate a tuple built from a lazy sequence of formatted text built from the embedded values for name in
# EDGE_NUMERIC_SCHEMA as part of the enclosing expression.
) + tuple(
    # Evaluate formatted text built from the embedded values as part of the enclosing expression.
    f"claim_edge.{name}" for name in EDGE_NUMERIC_SCHEMA
)
# Set PROTOCOL_STATE_COLUMNS to a tuple built from a lazy sequence of formatted text built from the embedded
# values for state in ProtocolState.
PROTOCOL_STATE_COLUMNS = tuple(
    # Evaluate formatted text built from the embedded values as part of the enclosing expression.
    f"protocol.{state.value}" for state in ProtocolState
)


# Define PolicySemanticEncodingError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class PolicySemanticEncodingError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# NumPy-only stateless encoder with zero learned parameters.
# Instances expose the attributes and methods implemented in this class.
class NegotiationSemanticFeatureEncoder:
    """NumPy-only stateless encoder with zero learned parameters."""

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Validate graph schema using the inputs and processing steps below.
    # Input graph: the supplied graph.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _validate_graph_schema(graph):
        # Run this branch when a tuple built from graph.node_feature_names differs from a tuple built from
        # NODE_NUMERIC_SCHEMA.
        if tuple(graph.node_feature_names) != tuple(NODE_NUMERIC_SCHEMA):
            # Raise PolicySemanticEncodingError with the text 'SOURCE_NODE_SCHEMA_MISMATCH' to stop this execution
            # path.
            raise PolicySemanticEncodingError("SOURCE_NODE_SCHEMA_MISMATCH")
        # Run this branch when a tuple built from graph.edge_feature_names differs from a tuple built from
        # EDGE_NUMERIC_SCHEMA.
        if tuple(graph.edge_feature_names) != tuple(EDGE_NUMERIC_SCHEMA):
            # Raise PolicySemanticEncodingError with the text 'SOURCE_EDGE_SCHEMA_MISMATCH' to stop this execution
            # path.
            raise PolicySemanticEncodingError("SOURCE_EDGE_SCHEMA_MISMATCH")

    # Encode claim using the inputs and processing steps below.
    # Input graph: the supplied graph.
    # Input ego_id: the identifier of the ego vehicle.
    # Input claim_identity: the supplied claim identity.
    # Output: the result of EncodedClaimOrProposalSemantics(CLAIM_SCHEMA_ID, ego_id, counterparty, a tuple
    # containing yielding, priority, None, values,...).
    # Processing: select branches using the stated conditions.
    def encode_claim(self, graph, ego_id, claim_identity):
        # Call self._validate_graph_schema with the supplied arguments.
        self._validate_graph_schema(graph)
        # Set (yielding, priority) to a tuple built from claim_identity.
        yielding, priority = tuple(claim_identity)
        # Run this branch when ego_id does not belong to a tuple containing yielding, priority.
        if ego_id not in (yielding, priority):
            # Raise PolicySemanticEncodingError with the text 'EGO_NOT_PARTICIPANT_IN_CLAIM' to stop this
            # execution path.
            raise PolicySemanticEncodingError("EGO_NOT_PARTICIPANT_IN_CLAIM")
        # Set counterparty to priority when ego_id equals yielding, otherwise yielding.
        counterparty = priority if ego_id == yielding else yielding
        # Set matches to a list of index for (index, node_id) in index/value pairs from graph.node_ids; retain
        # entries satisfying node_id equals counterparty.
        matches = [index for index, node_id in enumerate(graph.node_ids)
                   # Evaluate node_id equals counterparty as part of the enclosing expression.
                   if node_id == counterparty]
        # Run this branch when the negation of matches.
        if not matches:
            # Raise PolicySemanticEncodingError with the text 'CLAIM_COUNTERPARTY_NODE_NOT_FOUND' to stop this
            # execution path.
            raise PolicySemanticEncodingError("CLAIM_COUNTERPARTY_NODE_NOT_FOUND")
        # Run this branch when the number of entries in matches differs from 1.
        if len(matches) != 1:
            # Raise PolicySemanticEncodingError with the text 'CLAIM_COUNTERPARTY_NODE_AMBIGUOUS' to stop this
            # execution path.
            raise PolicySemanticEncodingError("CLAIM_COUNTERPARTY_NODE_AMBIGUOUS")
        # Set node_index to a dictionary of node_id mapped to index for (index, node_id) in index/value pairs from
        # graph.node_ids.
        node_index = {node_id: index for index, node_id in enumerate(graph.node_ids)}
        # Run this branch when yielding does not belong to node_index or priority does not belong to node_index.
        if yielding not in node_index or priority not in node_index:
            # Raise PolicySemanticEncodingError with the text 'CLAIM_EDGE_NOT_FOUND' to stop this execution path.
            raise PolicySemanticEncodingError("CLAIM_EDGE_NOT_FOUND")
        # Set edge_matches to a list of position for position in the integer range defined by
        # graph.edge_index.shape at 1; retain entries satisfying a tuple built from graph.edge_index at (:,
        # position) equals a tuple containing...
        edge_matches = [position for position in range(graph.edge_index.shape[1])
                        # Evaluate a tuple built from graph.edge_index at (:, position) equals a tuple containing
                        # node_index at yielding, node_index at priority as part of the enclosing expression.
                        if tuple(graph.edge_index[:, position]) == (
                            # Include node_index at yielding in this tuple.
                            node_index[yielding], node_index[priority]
                        )]
        # Run this branch when the negation of edge_matches.
        if not edge_matches:
            # Raise PolicySemanticEncodingError with the text 'CLAIM_EDGE_NOT_FOUND' to stop this execution path.
            raise PolicySemanticEncodingError("CLAIM_EDGE_NOT_FOUND")
        # Run this branch when the number of entries in edge_matches differs from 1.
        if len(edge_matches) != 1:
            # Raise PolicySemanticEncodingError with the text 'CLAIM_EDGE_AMBIGUOUS' to stop this execution path.
            raise PolicySemanticEncodingError("CLAIM_EDGE_AMBIGUOUS")
        # Set (node_position, edge_position) to a tuple containing matches at 0, edge_matches at 0.
        node_position, edge_position = matches[0], edge_matches[0]
        # Set values to the result of np.concatenate(a tuple containing graph.node_features at node_position,
        # graph.edge_features at edge_position).
        values = np.concatenate((
            # Include graph.node_features at node_position in this tuple.
            graph.node_features[node_position], graph.edge_features[edge_position],
        ))
        # Set mask to the result of np.concatenate(a tuple containing graph.node_feature_mask at node_position,
        # graph.edge_feature_mask at...).
        mask = np.concatenate((
            # Include graph.node_feature_mask at node_position in this tuple.
            graph.node_feature_mask[node_position],
            # Include graph.edge_feature_mask at edge_position in this tuple.
            graph.edge_feature_mask[edge_position],
        ))
        # Return the result of EncodedClaimOrProposalSemantics(CLAIM_SCHEMA_ID, ego_id, counterparty, a tuple
        # containing yielding, priority, None, values,...) to the caller.
        return EncodedClaimOrProposalSemantics(
            # Supply a tuple containing yielding, priority to EncodedClaimOrProposalSemantics.
            CLAIM_SCHEMA_ID, ego_id, counterparty, (yielding, priority), None,
            # Supply a tuple built from graph.node_feature_names to EncodedClaimOrProposalSemantics.
            values, mask, CLAIM_COLUMNS, tuple(graph.node_feature_names),
            # Supply a tuple built from graph.edge_feature_names to EncodedClaimOrProposalSemantics.
            tuple(graph.edge_feature_names),
            # Supply a tuple containing a tuple built from graph.node_feature_names, a tuple built from
            # graph.edge_feature_names to EncodedClaimOrProposalSemantics.
            (tuple(graph.node_feature_names), tuple(graph.edge_feature_names)),
            # Supply graph.normalization_status to EncodedClaimOrProposalSemantics.
            graph.normalization_status,
            # Supply a dictionary containing source_graph_scope, communication_model, edge_direction,... to
            # EncodedClaimOrProposalSemantics.
            {
                # Store graph.source_graph_scope under 'source_graph_scope'.
                "source_graph_scope": graph.source_graph_scope,
                # Store graph.communication_model under 'communication_model'.
                "communication_model": graph.communication_model,
                "edge_direction": "YIELDING_TO_PRIORITY",
                # Store 0 under 'identifier_features_in_numeric_vector'.
                "identifier_features_in_numeric_vector": 0,
            },
        )

    # Encode proposal using the inputs and processing steps below.
    # Input graph: the supplied graph.
    # Input ego_id: the identifier of the ego vehicle.
    # Input proposal: the supplied proposal.
    # Output: the result of EncodedClaimOrProposalSemantics(encoded.schema_id, encoded.ego_id,
    # encoded.counterparty_id, encoded.claim_identity,...).
    # Processing: select branches using the stated conditions.
    def encode_proposal(self, graph, ego_id, proposal):
        # Run this branch when the negation of whether proposal has type ClaimRelinquishmentProposal.
        if not isinstance(proposal, ClaimRelinquishmentProposal):
            # Raise TypeError with the text 'CLAIM_RELINQUISHMENT_PROPOSAL_REQUIRED' to stop this execution path.
            raise TypeError("CLAIM_RELINQUISHMENT_PROPOSAL_REQUIRED")
        # Set encoded to the result of self.encode_claim(graph, ego_id, a tuple containing
        # proposal.yielding_vehicle_id, proposal.priority_vehicle_id).
        encoded = self.encode_claim(
            # Supply ego_id to self.encode_claim.
            graph, ego_id,
            # Supply a tuple containing proposal.yielding_vehicle_id, proposal.priority_vehicle_id to
            # self.encode_claim.
            (proposal.yielding_vehicle_id, proposal.priority_vehicle_id),
        )
        # Return the result of EncodedClaimOrProposalSemantics(encoded.schema_id, encoded.ego_id,
        # encoded.counterparty_id, encoded.claim_identity,...) to the caller.
        return EncodedClaimOrProposalSemantics(
            # Supply encoded.counterparty_id to EncodedClaimOrProposalSemantics.
            encoded.schema_id, encoded.ego_id, encoded.counterparty_id,
            # Supply encoded.claim_identity to EncodedClaimOrProposalSemantics.
            encoded.claim_identity, proposal.proposal_id,
            # Supply encoded.availability_mask to EncodedClaimOrProposalSemantics.
            encoded.semantic_values, encoded.availability_mask,
            # Supply encoded.source_node_schema to EncodedClaimOrProposalSemantics.
            encoded.column_names, encoded.source_node_schema,
            # Supply encoded.source_schema_identity to EncodedClaimOrProposalSemantics.
            encoded.source_edge_schema, encoded.source_schema_identity,
            # Supply encoded.normalization_status to EncodedClaimOrProposalSemantics.
            encoded.normalization_status,
            # Store the text 'PROPOSAL_UNDERLYING_CLAIM' under 'semantic_subject'.
            {**encoded.provenance, "semantic_subject": "PROPOSAL_UNDERLYING_CLAIM"},
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Encode protocol state using the inputs and processing steps below.
    # Input protocol_state: the supplied protocol state.
    # Input responder_required: the supplied responder required.
    # Output: the result of EncodedProtocolStateSemantics(PROTOCOL_SCHEMA_ID, state_name, values, mask,
    # PROTOCOL_STATE_COLUMNS, the text...).
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def encode_protocol_state(protocol_state, responder_required=False):
        # Run this branch when protocol_state is the same object as None.
        if protocol_state is None:
            # Run this branch when responder_required.
            if responder_required:
                # Raise PolicySemanticEncodingError with the text 'RESPONDER_PROTOCOL_STATE_REQUIRED' to stop this
                # execution path.
                raise PolicySemanticEncodingError("RESPONDER_PROTOCOL_STATE_REQUIRED")
            # Set values to a zero-filled tensor with the requested shape.
            values = np.zeros(len(PROTOCOL_STATE_COLUMNS), dtype=np.float32)
            # Set mask to a zero-filled tensor with the requested shape.
            mask = np.zeros(len(PROTOCOL_STATE_COLUMNS), dtype=np.bool_)
            # Set state_name to None.
            state_name = None
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set state to protocol_state when whether protocol_state has type ProtocolState, otherwise the
                # result of ProtocolState(protocol_state).
                state = (protocol_state if isinstance(protocol_state, ProtocolState)
                         # Evaluate the result of ProtocolState(protocol_state) as part of the enclosing
                         # expression.
                         else ProtocolState(protocol_state))
            # Handle (TypeError, ValueError) as error using the recovery steps below.
            except (TypeError, ValueError) as error:
                # Raise PolicySemanticEncodingError with the text 'UNSUPPORTED_PROTOCOL_STATE' to stop this
                # execution path.
                raise PolicySemanticEncodingError("UNSUPPORTED_PROTOCOL_STATE") from error
            # Set values to the result of np.asarray(a list of a floating-point number built from candidate is the
            # same object as state for candidate...).
            values = np.asarray(
                # Supply a list of a floating-point number built from candidate is the same object as state for
                # candidate in ProtocolState to np.asarray.
                [float(candidate is state) for candidate in ProtocolState],
                # Supply dtype as np.float32.
                dtype=np.float32,
            )
            # Set mask to the result of np.ones(the number of entries in PROTOCOL_STATE_COLUMNS).
            mask = np.ones(len(PROTOCOL_STATE_COLUMNS), dtype=np.bool_)
            # Set state_name to state.value.
            state_name = state.value
        # Return the result of EncodedProtocolStateSemantics(PROTOCOL_SCHEMA_ID, state_name, values, mask,
        # PROTOCOL_STATE_COLUMNS, the text...) to the caller.
        return EncodedProtocolStateSemantics(
            # Supply PROTOCOL_SCHEMA_ID to EncodedProtocolStateSemantics.
            PROTOCOL_SCHEMA_ID, state_name, values, mask,
            # Supply PROTOCOL_STATE_COLUMNS to EncodedProtocolStateSemantics.
            PROTOCOL_STATE_COLUMNS, "CATEGORICAL_IDENTITY_NO_NORMALIZATION",
            # Store the text 'ONE_HOT_IDENTITY' under 'encoding'.
            # Store False under 'ordinal_meaning'.
            {"encoding": "ONE_HOT_IDENTITY", "ordinal_meaning": False},
        )
