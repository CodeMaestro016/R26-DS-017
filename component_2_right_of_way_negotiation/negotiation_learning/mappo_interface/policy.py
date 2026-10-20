"""Role-aware masked policy distribution; no PPO optimization or execution."""

# Import torch for use in this module.
import torch

# Import ActorForwardInput, ActorInputProvenance, DecentralizedNegotiationResponseActor, ResponseActorForwardInput
# from ..ctde for the operations below.
from ..ctde import (
    ActorForwardInput, ActorInputProvenance,
    DecentralizedNegotiationResponseActor, ResponseActorForwardInput,
)
# Import NegotiationAction from ..models for the operations below.
from ..models import NegotiationAction
# Import NegotiationResponseAction from ..protocol for the operations below.
from ..protocol import NegotiationResponseAction
# Import NegotiationDecisionRole, NegotiationPolicyDecision, ROLE_ONE_HOT from .models for the operations below.
from .models import (
    NegotiationDecisionRole, NegotiationPolicyDecision, ROLE_ONE_HOT,
)


# Set PROPOSER_ACTION_ORDER to a tuple containing NegotiationAction.KEEP_CLAIM.value,
# NegotiationAction.RELINQUISH_CLAIM.value.
PROPOSER_ACTION_ORDER = (
    # Include NegotiationAction.KEEP_CLAIM.value in this tuple.
    NegotiationAction.KEEP_CLAIM.value,
    # Include NegotiationAction.RELINQUISH_CLAIM.value in this tuple.
    NegotiationAction.RELINQUISH_CLAIM.value,
)
# Set RESPONDER_ACTION_ORDER to a tuple containing NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
# NegotiationResponseAction.REJECT_RELINQUISHMENT.value.
RESPONDER_ACTION_ORDER = (
    # Include NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value in this tuple.
    NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
    # Include NegotiationResponseAction.REJECT_RELINQUISHMENT.value in this tuple.
    NegotiationResponseAction.REJECT_RELINQUISHMENT.value,
)
# Set FINAL_POLICY_ARCHITECTURE to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
FINAL_POLICY_ARCHITECTURE = "REQUIRES_EXPERIMENTAL_SELECTION"


# Define PolicySemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class PolicySemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Exact Boolean masking via negative infinity, never a finite sentinel.
# Instances expose the attributes and methods implemented in this class.
class MaskedCategoricalPolicy:
    """Exact Boolean masking via negative infinity, never a finite sentinel."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input unmasked_logits: the supplied unmasked logits.
    # Input action_feasibility_mask: the supplied action feasibility mask.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, unmasked_logits, action_feasibility_mask):
        # Run this branch when the negation of whether unmasked_logits has type torch.Tensor.
        if not isinstance(unmasked_logits, torch.Tensor):
            # Raise TypeError with the text 'LOGITS_TENSOR_REQUIRED' to stop this execution path.
            raise TypeError("LOGITS_TENSOR_REQUIRED")
        # Run this branch when the negation of whether action_feasibility_mask has type torch.Tensor.
        if not isinstance(action_feasibility_mask, torch.Tensor):
            # Raise TypeError with the text 'ACTION_MASK_TENSOR_REQUIRED' to stop this execution path.
            raise TypeError("ACTION_MASK_TENSOR_REQUIRED")
        # Run this branch when action_feasibility_mask.dtype is a different object from torch.bool.
        if action_feasibility_mask.dtype is not torch.bool:
            # Raise PolicySemanticError with the text 'BOOLEAN_ACTION_MASK_REQUIRED' to stop this execution path.
            raise PolicySemanticError("BOOLEAN_ACTION_MASK_REQUIRED")
        # Run this branch when unmasked_logits.shape differs from action_feasibility_mask.shape.
        if unmasked_logits.shape != action_feasibility_mask.shape:
            # Raise PolicySemanticError with the text 'ACTION_MASK_SHAPE_MISMATCH' to stop this execution path.
            raise PolicySemanticError("ACTION_MASK_SHAPE_MISMATCH")
        # Run this branch when unmasked_logits.ndim is less than 1.
        if unmasked_logits.ndim < 1:
            # Raise PolicySemanticError with the text 'ACTION_DIMENSION_REQUIRED' to stop this execution path.
            raise PolicySemanticError("ACTION_DIMENSION_REQUIRED")
        # Run this branch when the negation of the result of torch.all(the result of
        # action_feasibility_mask.any()).
        if not torch.all(action_feasibility_mask.any(dim=-1)):
            # Raise PolicySemanticError with the text 'NO_FEASIBLE_POLICY_ACTION' to stop this execution path.
            raise PolicySemanticError("NO_FEASIBLE_POLICY_ACTION")
        # Set self.unmasked_logits to unmasked_logits.
        self.unmasked_logits = unmasked_logits
        # Set self.action_feasibility_mask to action_feasibility_mask.
        self.action_feasibility_mask = action_feasibility_mask
        # Set self.masked_logits to the result of torch.where(action_feasibility_mask, unmasked_logits, the result
        # of torch.full_like(unmasked_logits, the...).
        self.masked_logits = torch.where(
            # Supply action_feasibility_mask to torch.where.
            action_feasibility_mask, unmasked_logits,
            # Supply the result of torch.full_like(unmasked_logits, the negative of torch.inf) to torch.where.
            torch.full_like(unmasked_logits, -torch.inf),
        )
        # Set self.distribution to the result of torch.distributions.Categorical().
        self.distribution = torch.distributions.Categorical(logits=self.masked_logits)

    # Apply property as a decorator to configure the following definition.
    @property
    # Probabilities using the inputs and processing steps below.
    # Output: self.distribution.probs.
    def probabilities(self):
        # Return self.distribution.probs to the caller.
        return self.distribution.probs

    # Apply property as a decorator to configure the following definition.
    @property
    # Entropy using the inputs and processing steps below.
    # Output: the result of self.distribution.entropy().
    def entropy(self):
        # Return the result of self.distribution.entropy() to the caller.
        return self.distribution.entropy()

    # Sample action index using the inputs and processing steps below.
    # Input generator: the supplied generator.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def sample_action_index(self, generator=None):
        # Run this branch when generator is the same object as None.
        if generator is None:
            # Return the result of self.distribution.sample() to the caller.
            return self.distribution.sample()
        # Return the result of torch.multinomial(self.probabilities, num_samples=1,
        # generator=generator).squeeze(the negative of 1) to the caller.
        return torch.multinomial(
            # Supply num_samples as 1.
            # Supply generator as generator.
            self.probabilities, num_samples=1, generator=generator
        # Supply the negative of 1 to torch.multinomial(self.probabilities, num_samples=1,
        # generator=generator).squeeze.
        ).squeeze(-1)

    # Evaluate action index using the inputs and processing steps below.
    # Input action_index: the supplied action index.
    # Output: the result of self.distribution.log_prob(index).
    # Processing: select branches using the stated conditions.
    def evaluate_action_index(self, action_index):
        # Set index to action_index when whether action_index has type torch.Tensor, otherwise a tensor built from
        # action_index.
        index = (action_index if isinstance(action_index, torch.Tensor)
                 # Supply dtype as torch.long.
                 else torch.as_tensor(action_index, dtype=torch.long,
                                      # Supply device as self.unmasked_logits.device.
                                      device=self.unmasked_logits.device))
        # Run this branch when index.ndim differs from 0.
        if index.ndim != 0:
            # Raise PolicySemanticError with the text 'SCALAR_ACTION_INDEX_REQUIRED' to stop this execution path.
            raise PolicySemanticError("SCALAR_ACTION_INDEX_REQUIRED")
        # Set value to an integer built from the result of index.item().
        value = int(index.item())
        # Run this branch when value is less than 0 or value is at least self.unmasked_logits.shape at -1.
        if value < 0 or value >= self.unmasked_logits.shape[-1]:
            # Raise PolicySemanticError with the text 'ACTION_INDEX_OUT_OF_RANGE' to stop this execution path.
            raise PolicySemanticError("ACTION_INDEX_OUT_OF_RANGE")
        # Run this branch when the negation of a Boolean built from the result of
        # self.action_feasibility_mask[value].item().
        if not bool(self.action_feasibility_mask[value].item()):
            # Raise PolicySemanticError with the text 'ACTION_NOT_FEASIBLE_UNDER_MASK' to stop this execution
            # path.
            raise PolicySemanticError("ACTION_NOT_FEASIBLE_UNDER_MASK")
        # Return the result of self.distribution.log_prob(index) to the caller.
        return self.distribution.log_prob(index)


# Route local contexts to existing untrained role-specific actors.
# Instances expose the attributes and methods implemented in this class.
class RoleAwareNegotiationPolicy:
    """Route local contexts to existing untrained role-specific actors."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input proposer_actor: the supplied proposer actor.
    # Input responder_actor: the supplied responder actor.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, proposer_actor, responder_actor):
        # Set self.proposer_actor to proposer_actor.
        self.proposer_actor = proposer_actor
        # Set self.responder_actor to responder_actor.
        self.responder_actor = responder_actor

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Expected action names using the inputs and processing steps below.
    # Input role: the supplied role.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def expected_action_names(role):
        # Run this branch when role is the same object as NegotiationDecisionRole.PROPOSER.
        if role is NegotiationDecisionRole.PROPOSER:
            # Return PROPOSER_ACTION_ORDER to the caller.
            return PROPOSER_ACTION_ORDER
        # Run this branch when role is the same object as NegotiationDecisionRole.RESPONDER.
        if role is NegotiationDecisionRole.RESPONDER:
            # Return RESPONDER_ACTION_ORDER to the caller.
            return RESPONDER_ACTION_ORDER
        # Raise PolicySemanticError with the text 'UNSUPPORTED_NEGOTIATION_DECISION_ROLE' to stop this execution
        # path.
        raise PolicySemanticError("UNSUPPORTED_NEGOTIATION_DECISION_ROLE")

    # Distribution for using the inputs and processing steps below.
    # Input context: the supplied context.
    # Output: a tuple containing output, the result of MaskedCategoricalPolicy(output.unmasked_action_logits,
    # output.action_feasibility_mask).
    # Processing: select branches using the stated conditions.
    def distribution_for(self, context):
        # Set expected to the result of self.expected_action_names(context.decision_role).
        expected = self.expected_action_names(context.decision_role)
        # Run this branch when context.action_names differs from expected.
        if context.action_names != expected:
            # Raise PolicySemanticError with the text 'ROLE_ACTION_VOCABULARY_MISMATCH' to stop this execution
            # path.
            raise PolicySemanticError("ROLE_ACTION_VOCABULARY_MISMATCH")
        # Set provenance to the result of ActorInputProvenance(context.provenance.local_observation_identity,
        # context.provenance.local_graph_identity,...).
        provenance = ActorInputProvenance(
            # Supply context.provenance.local_observation_identity to ActorInputProvenance.
            context.provenance.local_observation_identity,
            # Supply context.provenance.local_graph_identity to ActorInputProvenance.
            context.provenance.local_graph_identity,
            # Supply context.provenance.local_mpnn_identity to ActorInputProvenance.
            context.provenance.local_mpnn_identity,
            # Supply context.provenance.hard_mask_identity to ActorInputProvenance.
            context.provenance.hard_mask_identity,
        )
        # Run this branch when context.decision_role is the same object as NegotiationDecisionRole.PROPOSER.
        if context.decision_role is NegotiationDecisionRole.PROPOSER:
            # Set output to the result of self.proposer_actor(the result of ActorForwardInput(context.ego_id,
            # context.counterparty_id, context.ego_embedding,...).
            output = self.proposer_actor(ActorForwardInput(
                # Supply context.counterparty_id to ActorForwardInput.
                context.ego_id, context.counterparty_id,
                # Supply context.local_graph_embedding to ActorForwardInput.
                context.ego_embedding, context.local_graph_embedding,
                # Supply context.claim_or_proposal_representation to ActorForwardInput.
                context.claim_or_proposal_representation,
                # Supply context.action_feasibility_mask to ActorForwardInput.
                context.action_feasibility_mask, provenance,
            ))
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Run this branch when context.proposal_id is the same object as None or
            # context.protocol_state_representation is the same object as None.
            if context.proposal_id is None or context.protocol_state_representation is None:
                # Raise PolicySemanticError with the text 'RESPONDER_PROTOCOL_CONTEXT_REQUIRED' to stop this
                # execution path.
                raise PolicySemanticError("RESPONDER_PROTOCOL_CONTEXT_REQUIRED")
            # Set role to a tensor built from ROLE_ONE_HOT at NegotiationDecisionRole.RESPONDER.
            role = torch.tensor(
                # Supply ROLE_ONE_HOT at NegotiationDecisionRole.RESPONDER to torch.tensor.
                ROLE_ONE_HOT[NegotiationDecisionRole.RESPONDER],
                # Supply dtype as context.ego_embedding.dtype.
                dtype=context.ego_embedding.dtype,
                # Supply device as context.ego_embedding.device.
                device=context.ego_embedding.device,
            )
            # Set output to the result of self.responder_actor(the result of
            # ResponseActorForwardInput(context.ego_id, context.proposal_id,...).
            output = self.responder_actor(ResponseActorForwardInput(
                # Supply context.proposal_id to ResponseActorForwardInput.
                context.ego_id, context.proposal_id,
                # Supply context.local_graph_embedding to ResponseActorForwardInput.
                context.ego_embedding, context.local_graph_embedding,
                # Supply context.claim_or_proposal_representation to ResponseActorForwardInput.
                context.claim_or_proposal_representation,
                # Supply context.protocol_state_representation to ResponseActorForwardInput.
                context.protocol_state_representation, role,
                # Supply context.action_feasibility_mask to ResponseActorForwardInput.
                context.action_feasibility_mask, provenance,
            ))
        # Return a tuple containing output, the result of MaskedCategoricalPolicy(output.unmasked_action_logits,
        # output.action_feasibility_mask) to the caller.
        return output, MaskedCategoricalPolicy(
            # Supply output.action_feasibility_mask to MaskedCategoricalPolicy.
            output.unmasked_action_logits, output.action_feasibility_mask,
        )

    # Select action using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input generator: the supplied generator.
    # Output: the result of self._decision(context, output.unmasked_action_logits, policy, index).
    def select_action(self, context, generator=None):
        # Set (output, policy) to the result of self.distribution_for(context).
        output, policy = self.distribution_for(context)
        # Set index to the result of policy.sample_action_index().
        index = policy.sample_action_index(generator=generator)
        # Return the result of self._decision(context, output.unmasked_action_logits, policy, index) to the
        # caller.
        return self._decision(context, output.unmasked_action_logits,
                              # Supply policy to self._decision.
                              policy, index)

    # Evaluate action using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input action: the supplied action.
    # Output: a tuple containing log_probability, policy.entropy.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def evaluate_action(self, context, action):
        # Set (output, policy) to the result of self.distribution_for(context).
        output, policy = self.distribution_for(context)
        # Run this branch when whether action has type str.
        if isinstance(action, str):
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set action to the result of context.action_names.index(action).
                action = context.action_names.index(action)
            # Handle ValueError as error using the recovery steps below.
            except ValueError as error:
                # Raise PolicySemanticError with the text 'ACTION_NOT_IN_ROLE_VOCABULARY' to stop this execution
                # path.
                raise PolicySemanticError("ACTION_NOT_IN_ROLE_VOCABULARY") from error
        # Set index to a tensor built from action.
        index = torch.as_tensor(action, dtype=torch.long,
                                # Supply device as output.unmasked_action_logits.device.
                                device=output.unmasked_action_logits.device)
        # Set log_probability to the result of policy.evaluate_action_index(index).
        log_probability = policy.evaluate_action_index(index)
        # Return a tuple containing log_probability, policy.entropy to the caller.
        return log_probability, policy.entropy

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Decision using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input logits: the supplied logits.
    # Input policy: the supplied policy.
    # Input index: the supplied index.
    # Output: the result of NegotiationPolicyDecision(context.ego_id, context.decision_role,
    # context.claim_identity, context.proposal_id,...).
    def _decision(context, logits, policy, index):
        # Set log_probability to the result of policy.evaluate_action_index(index).
        log_probability = policy.evaluate_action_index(index)
        # Set value to an integer built from the result of index.item().
        value = int(index.item())
        # Return the result of NegotiationPolicyDecision(context.ego_id, context.decision_role,
        # context.claim_identity, context.proposal_id,...) to the caller.
        return NegotiationPolicyDecision(
            # Supply context.claim_identity to NegotiationPolicyDecision.
            context.ego_id, context.decision_role, context.claim_identity,
            # Supply context.action_names to NegotiationPolicyDecision.
            context.proposal_id, context.action_names,
            # Supply the result of context.action_feasibility_mask.detach().clone() to NegotiationPolicyDecision.
            context.action_feasibility_mask.detach().clone(),
            # Supply the result of policy.masked_logits.detach().clone() to NegotiationPolicyDecision.
            logits.detach().clone(), policy.masked_logits.detach().clone(),
            # Supply the result of policy.probabilities.detach().clone() to NegotiationPolicyDecision.
            policy.probabilities.detach().clone(), value,
            # Supply the result of log_probability.detach().clone() to NegotiationPolicyDecision.
            context.action_names[value], log_probability.detach().clone(),
            # Supply context.source_snapshot_timestamp to NegotiationPolicyDecision.
            policy.entropy.detach().clone(), context.source_snapshot_timestamp,
            # Supply context.provenance to NegotiationPolicyDecision.
            context.provenance,
        )
