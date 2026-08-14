"""Build real role-aware contexts from validated deterministic encodings."""

import torch

from ..ctde import semantic_encoding_to_torch
from ..semantic_encoding import PolicySemanticEncodingError
from .models import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance,
)
from .policy import PROPOSER_ACTION_ORDER, RESPONDER_ACTION_ORDER


class NegotiationPolicyContextBuilder:
    """Adapter only; semantic values are defined by Step 5F.1 encoders."""

    @staticmethod
    def build(role, graph_identity, source_timestamp, gnn_output,
              subject_encoding, action_feasibility_mask,
              regulatory_profile, communication_model,
              protocol_encoding=None):
        role = role if isinstance(role, NegotiationDecisionRole) else NegotiationDecisionRole(role)
        if role is NegotiationDecisionRole.RESPONDER:
            if protocol_encoding is None or protocol_encoding.protocol_state is None:
                raise PolicySemanticEncodingError("RESPONDER_PROTOCOL_STATE_REQUIRED")
            if subject_encoding.proposal_id is None:
                raise PolicySemanticEncodingError("RESPONDER_PROPOSAL_ID_REQUIRED")
        elif protocol_encoding is not None and protocol_encoding.protocol_state is not None:
            raise PolicySemanticEncodingError("PROPOSER_PROTOCOL_STATE_NOT_CONSUMED")
        mask = torch.as_tensor(
            tuple(action_feasibility_mask), dtype=torch.bool, device="cpu"
        )
        return NegotiationPolicyDecisionContext(
            subject_encoding.ego_id, role, subject_encoding.counterparty_id,
            subject_encoding.claim_identity, subject_encoding.proposal_id,
            graph_identity, float(source_timestamp),
            gnn_output.ego_embedding.detach().clone().cpu(),
            gnn_output.graph_embedding.detach().clone().cpu(),
            semantic_encoding_to_torch(subject_encoding),
            (semantic_encoding_to_torch(protocol_encoding)
             if protocol_encoding is not None else None),
            (RESPONDER_ACTION_ORDER if role is NegotiationDecisionRole.RESPONDER
             else PROPOSER_ACTION_ORDER),
            mask,
            PolicyDecisionProvenance(
                graph_identity, subject_encoding.provenance["source_graph_scope"],
                "CURRENT_MPNN_OUTPUT", subject_encoding.schema_id,
                "DETERMINISTIC_BOOLEAN_SEMANTIC_MASK",
            ),
            regulatory_profile, communication_model,
        )
