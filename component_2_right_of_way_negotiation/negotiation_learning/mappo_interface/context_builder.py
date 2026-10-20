"""Build real role-aware contexts from validated deterministic encodings."""

# Import torch for use in this module.
import torch

# Import semantic_encoding_to_torch from ..ctde for the operations below.
from ..ctde import semantic_encoding_to_torch
# Import PolicySemanticEncodingError from ..semantic_encoding for the operations below.
from ..semantic_encoding import PolicySemanticEncodingError
# Import NegotiationDecisionRole, NegotiationPolicyDecisionContext, PolicyDecisionProvenance from .models for the
# operations below.
from .models import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance,
)
# Import PROPOSER_ACTION_ORDER, RESPONDER_ACTION_ORDER from .policy for the operations below.
from .policy import PROPOSER_ACTION_ORDER, RESPONDER_ACTION_ORDER


# Adapter only; semantic values are defined by Step 5F.1 encoders.
# Instances expose the attributes and methods implemented in this class.
class NegotiationPolicyContextBuilder:
    """Adapter only; semantic values are defined by Step 5F.1 encoders."""

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Build using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input graph_identity: the supplied graph identity.
    # Input source_timestamp: the supplied source timestamp.
    # Input gnn_output: the supplied gnn output.
    # Input subject_encoding: the supplied subject encoding.
    # Input action_feasibility_mask: the supplied action feasibility mask.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input communication_model: the supplied communication model.
    # Input protocol_encoding: the supplied protocol encoding.
    # Output: the result of NegotiationPolicyDecisionContext(subject_encoding.ego_id, role,
    # subject_encoding.counterparty_id,...).
    # Processing: select branches using the stated conditions.
    def build(role, graph_identity, source_timestamp, gnn_output,
              # Declare subject_encoding, action_feasibility_mask as input parameters.
              subject_encoding, action_feasibility_mask,
              # Declare regulatory_profile, communication_model as input parameters.
              regulatory_profile, communication_model,
              # Declare protocol_encoding as input parameter.
              protocol_encoding=None):
        # Set role to role when whether role has type NegotiationDecisionRole, otherwise the result of
        # NegotiationDecisionRole(role).
        role = role if isinstance(role, NegotiationDecisionRole) else NegotiationDecisionRole(role)
        # Run this branch when role is the same object as NegotiationDecisionRole.RESPONDER.
        if role is NegotiationDecisionRole.RESPONDER:
            # Run this branch when protocol_encoding is the same object as None or
            # protocol_encoding.protocol_state is the same object as None.
            if protocol_encoding is None or protocol_encoding.protocol_state is None:
                # Raise PolicySemanticEncodingError with the text 'RESPONDER_PROTOCOL_STATE_REQUIRED' to stop this
                # execution path.
                raise PolicySemanticEncodingError("RESPONDER_PROTOCOL_STATE_REQUIRED")
            # Run this branch when subject_encoding.proposal_id is the same object as None.
            if subject_encoding.proposal_id is None:
                # Raise PolicySemanticEncodingError with the text 'RESPONDER_PROPOSAL_ID_REQUIRED' to stop this
                # execution path.
                raise PolicySemanticEncodingError("RESPONDER_PROPOSAL_ID_REQUIRED")
        # Run this branch when protocol_encoding is a different object from None and
        # protocol_encoding.protocol_state is a different object from None.
        elif protocol_encoding is not None and protocol_encoding.protocol_state is not None:
            # Raise PolicySemanticEncodingError with the text 'PROPOSER_PROTOCOL_STATE_NOT_CONSUMED' to stop this
            # execution path.
            raise PolicySemanticEncodingError("PROPOSER_PROTOCOL_STATE_NOT_CONSUMED")
        # Set mask to a tensor built from a tuple built from action_feasibility_mask.
        mask = torch.as_tensor(
            # Supply dtype as torch.bool.
            # Supply device as the text 'cpu'.
            tuple(action_feasibility_mask), dtype=torch.bool, device="cpu"
        )
        # Return the result of NegotiationPolicyDecisionContext(subject_encoding.ego_id, role,
        # subject_encoding.counterparty_id,...) to the caller.
        return NegotiationPolicyDecisionContext(
            # Supply subject_encoding.counterparty_id to NegotiationPolicyDecisionContext.
            subject_encoding.ego_id, role, subject_encoding.counterparty_id,
            # Supply subject_encoding.claim_identity to NegotiationPolicyDecisionContext.
            subject_encoding.claim_identity, subject_encoding.proposal_id,
            # Supply a floating-point number built from source_timestamp to NegotiationPolicyDecisionContext.
            graph_identity, float(source_timestamp),
            # Supply the result of gnn_output.ego_embedding.detach().clone().cpu() to
            # NegotiationPolicyDecisionContext.
            gnn_output.ego_embedding.detach().clone().cpu(),
            # Supply the result of gnn_output.graph_embedding.detach().clone().cpu() to
            # NegotiationPolicyDecisionContext.
            gnn_output.graph_embedding.detach().clone().cpu(),
            # Supply the result of semantic_encoding_to_torch(subject_encoding) to
            # NegotiationPolicyDecisionContext.
            semantic_encoding_to_torch(subject_encoding),
            # Supply the result of semantic_encoding_to_torch(protocol_encoding) when protocol_encoding is a
            # different object from None, otherwise None to NegotiationPolicyDecisionContext.
            (semantic_encoding_to_torch(protocol_encoding)
             # Evaluate protocol_encoding is a different object from None as part of the enclosing expression.
             if protocol_encoding is not None else None),
            # Supply RESPONDER_ACTION_ORDER when role is the same object as NegotiationDecisionRole.RESPONDER,
            # otherwise PROPOSER_ACTION_ORDER to NegotiationPolicyDecisionContext.
            (RESPONDER_ACTION_ORDER if role is NegotiationDecisionRole.RESPONDER
             # Evaluate PROPOSER_ACTION_ORDER as part of the enclosing expression.
             else PROPOSER_ACTION_ORDER),
            # Supply mask to NegotiationPolicyDecisionContext.
            mask,
            # Supply the result of PolicyDecisionProvenance(graph_identity, subject_encoding.provenance at
            # 'source_graph_scope', the text...) to NegotiationPolicyDecisionContext.
            PolicyDecisionProvenance(
                # Supply subject_encoding.provenance at 'source_graph_scope' to PolicyDecisionProvenance.
                graph_identity, subject_encoding.provenance["source_graph_scope"],
                # Supply subject_encoding.schema_id to PolicyDecisionProvenance.
                "CURRENT_MPNN_OUTPUT", subject_encoding.schema_id,
                "DETERMINISTIC_BOOLEAN_SEMANTIC_MASK",
            ),
            # Supply communication_model to NegotiationPolicyDecisionContext.
            regulatory_profile, communication_model,
        )
