"""Role-aware masked policy distribution; no PPO optimization or execution."""

import torch

from ..ctde import (
    ActorForwardInput, ActorInputProvenance,
    DecentralizedNegotiationResponseActor, ResponseActorForwardInput,
)
from ..models import NegotiationAction
from ..protocol import NegotiationResponseAction
from .models import (
    NegotiationDecisionRole, NegotiationPolicyDecision, ROLE_ONE_HOT,
)


PROPOSER_ACTION_ORDER = (
    NegotiationAction.KEEP_CLAIM.value,
    NegotiationAction.RELINQUISH_CLAIM.value,
)
RESPONDER_ACTION_ORDER = (
    NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
    NegotiationResponseAction.REJECT_RELINQUISHMENT.value,
)
FINAL_POLICY_ARCHITECTURE = "REQUIRES_EXPERIMENTAL_SELECTION"


class PolicySemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class MaskedCategoricalPolicy:
    """Exact Boolean masking via negative infinity, never a finite sentinel."""

    def __init__(self, unmasked_logits, action_feasibility_mask):
        if not isinstance(unmasked_logits, torch.Tensor):
            raise TypeError("LOGITS_TENSOR_REQUIRED")
        if not isinstance(action_feasibility_mask, torch.Tensor):
            raise TypeError("ACTION_MASK_TENSOR_REQUIRED")
        if action_feasibility_mask.dtype is not torch.bool:
            raise PolicySemanticError("BOOLEAN_ACTION_MASK_REQUIRED")
        if unmasked_logits.shape != action_feasibility_mask.shape:
            raise PolicySemanticError("ACTION_MASK_SHAPE_MISMATCH")
        if unmasked_logits.ndim < 1:
            raise PolicySemanticError("ACTION_DIMENSION_REQUIRED")
        if not torch.all(action_feasibility_mask.any(dim=-1)):
            raise PolicySemanticError("NO_FEASIBLE_POLICY_ACTION")
        self.unmasked_logits = unmasked_logits
        self.action_feasibility_mask = action_feasibility_mask
        self.masked_logits = torch.where(
            action_feasibility_mask, unmasked_logits,
            torch.full_like(unmasked_logits, -torch.inf),
        )
        self.distribution = torch.distributions.Categorical(logits=self.masked_logits)

    @property
    def probabilities(self):
        return self.distribution.probs

    @property
    def entropy(self):
        return self.distribution.entropy()

    def sample_action_index(self):
        return self.distribution.sample()

    def evaluate_action_index(self, action_index):
        index = (action_index if isinstance(action_index, torch.Tensor)
                 else torch.as_tensor(action_index, dtype=torch.long,
                                      device=self.unmasked_logits.device))
        if index.ndim != 0:
            raise PolicySemanticError("SCALAR_ACTION_INDEX_REQUIRED")
        value = int(index.item())
        if value < 0 or value >= self.unmasked_logits.shape[-1]:
            raise PolicySemanticError("ACTION_INDEX_OUT_OF_RANGE")
        if not bool(self.action_feasibility_mask[value].item()):
            raise PolicySemanticError("ACTION_NOT_FEASIBLE_UNDER_MASK")
        return self.distribution.log_prob(index)


class RoleAwareNegotiationPolicy:
    """Route local contexts to existing untrained role-specific actors."""

    def __init__(self, proposer_actor, responder_actor):
        self.proposer_actor = proposer_actor
        self.responder_actor = responder_actor

    @staticmethod
    def expected_action_names(role):
        if role is NegotiationDecisionRole.PROPOSER:
            return PROPOSER_ACTION_ORDER
        if role is NegotiationDecisionRole.RESPONDER:
            return RESPONDER_ACTION_ORDER
        raise PolicySemanticError("UNSUPPORTED_NEGOTIATION_DECISION_ROLE")

    def distribution_for(self, context):
        expected = self.expected_action_names(context.decision_role)
        if context.action_names != expected:
            raise PolicySemanticError("ROLE_ACTION_VOCABULARY_MISMATCH")
        provenance = ActorInputProvenance(
            context.provenance.local_observation_identity,
            context.provenance.local_graph_identity,
            context.provenance.local_mpnn_identity,
            context.provenance.hard_mask_identity,
        )
        if context.decision_role is NegotiationDecisionRole.PROPOSER:
            output = self.proposer_actor(ActorForwardInput(
                context.ego_id, context.counterparty_id,
                context.ego_embedding, context.local_graph_embedding,
                context.claim_or_proposal_representation,
                context.action_feasibility_mask, provenance,
            ))
        else:
            if context.proposal_id is None or context.protocol_state_representation is None:
                raise PolicySemanticError("RESPONDER_PROTOCOL_CONTEXT_REQUIRED")
            role = torch.tensor(
                ROLE_ONE_HOT[NegotiationDecisionRole.RESPONDER],
                dtype=context.ego_embedding.dtype,
                device=context.ego_embedding.device,
            )
            output = self.responder_actor(ResponseActorForwardInput(
                context.ego_id, context.proposal_id,
                context.ego_embedding, context.local_graph_embedding,
                context.claim_or_proposal_representation,
                context.protocol_state_representation, role,
                context.action_feasibility_mask, provenance,
            ))
        return output, MaskedCategoricalPolicy(
            output.unmasked_action_logits, output.action_feasibility_mask,
        )

    def select_action(self, context):
        output, policy = self.distribution_for(context)
        index = policy.sample_action_index()
        return self._decision(context, output.unmasked_action_logits,
                              policy, index)

    def evaluate_action(self, context, action):
        output, policy = self.distribution_for(context)
        if isinstance(action, str):
            try:
                action = context.action_names.index(action)
            except ValueError as error:
                raise PolicySemanticError("ACTION_NOT_IN_ROLE_VOCABULARY") from error
        index = torch.as_tensor(action, dtype=torch.long,
                                device=output.unmasked_action_logits.device)
        log_probability = policy.evaluate_action_index(index)
        return log_probability, policy.entropy

    @staticmethod
    def _decision(context, logits, policy, index):
        log_probability = policy.evaluate_action_index(index)
        value = int(index.item())
        return NegotiationPolicyDecision(
            context.ego_id, context.decision_role, context.claim_identity,
            context.proposal_id, context.action_names,
            context.action_feasibility_mask.detach().clone(),
            logits.detach().clone(), policy.masked_logits.detach().clone(),
            policy.probabilities.detach().clone(), value,
            context.action_names[value], log_probability.detach().clone(),
            policy.entropy.detach().clone(), context.source_snapshot_timestamp,
            context.provenance,
        )
