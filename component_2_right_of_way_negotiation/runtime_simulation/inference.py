"""Presentation-only deterministic inference over the frozen selected policy."""

# Import MappingProxyType from types for the operations below.
from types import MappingProxyType

# Import torch for use in this module.
import torch

# Import FinalSelectionInferenceProvider from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import FinalSelectionInferenceProvider
# Import BEHAVIOR_SOURCE from negotiation_training.mappo_provider for the operations below.
from negotiation_training.mappo_provider import BEHAVIOR_SOURCE
# Import MAPPOPolicyFactorSample, tensor_snapshot from negotiation_training.rollout for the operations below.
from negotiation_training.rollout import MAPPOPolicyFactorSample, tensor_snapshot


# Set PRESENTATION_SELECTION_RULE to the text 'DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY'.
PRESENTATION_SELECTION_RULE = (
    "DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY")


# Select the maximum-probability feasible semantic action per factor.
# Base classes: FinalSelectionInferenceProvider.
# Instances expose the attributes and methods implemented in this class.
class PanelDeterministicInferenceProvider(FinalSelectionInferenceProvider):
    """Select the maximum-probability feasible semantic action per factor.

    This changes presentation-time sampling only. The selected checkpoint,
    actor logits, hard masks, protocol semantics, and physical planner remain
    untouched.
    """

    # Set selection_rule to PRESENTATION_SELECTION_RULE.
    selection_rule = PRESENTATION_SELECTION_RULE

    # Sample using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input batch_id: the supplied batch id.
    # Input episode_id: the supplied episode id.
    # Input scenario_id: the supplied scenario id.
    # Input critic_sample_id: the supplied critic sample id.
    # Output: the result of MAPPOPolicyFactorSample(event_id, batch_id, episode_id, scenario_id, context.ego_id,
    # context.decision_role.value,...).
    def _sample(self, context, batch_id, episode_id, scenario_id,
                # Declare critic_sample_id as input parameter.
                critic_sample_id):
        # Enter the result of torch.no_grad() and run the enclosed operations within that context.
        with torch.no_grad():
            # Set (_, distribution) to the result of self.bundle.policy.distribution_for(context).
            _, distribution = self.bundle.policy.distribution_for(context)
            # Set selected_index to an integer built from the result of
            # torch.argmax(distribution.probabilities).item().
            selected_index = int(torch.argmax(
                # Supply distribution.probabilities to torch.argmax.
                distribution.probabilities).item())
            # Set log_probability to the result of distribution.evaluate_action_index(selected_index).
            log_probability = distribution.evaluate_action_index(
                # Supply selected_index to distribution.evaluate_action_index.
                selected_index)
        # Set event_id to a tuple containing batch_id, context.decision_role.value, context.ego_id,
        # context.claim_identity, context.proposal_id.
        event_id = (batch_id, context.decision_role.value, context.ego_id,
                    # Include context.claim_identity in this tuple.
                    context.claim_identity, context.proposal_id)
        # Return the result of MAPPOPolicyFactorSample(event_id, batch_id, episode_id, scenario_id,
        # context.ego_id, context.decision_role.value,...) to the caller.
        return MAPPOPolicyFactorSample(
            # Supply context.ego_id to MAPPOPolicyFactorSample.
            event_id, batch_id, episode_id, scenario_id, context.ego_id,
            # Supply context.decision_role.value to MAPPOPolicyFactorSample.
            context.decision_role.value, context.claim_identity,
            # Supply context.action_names to MAPPOPolicyFactorSample.
            context.proposal_id, context.action_names,
            # Supply a tuple built from a lazy sequence of a Boolean built from x for x in the result of
            # context.action_feasibility_mask.tolist() to MAPPOPolicyFactorSample.
            tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
            # Supply context.action_names at selected_index to MAPPOPolicyFactorSample.
            selected_index, context.action_names[selected_index],
            # Supply a floating-point number built from the result of log_probability.item() to
            # MAPPOPolicyFactorSample.
            float(log_probability.item()),
            # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the
            # result of distribution.probabilities.tolist() to MAPPOPolicyFactorSample.
            tuple(float(x) for x in
                  # Evaluate the result of distribution.probabilities.tolist() as part of the enclosing
                  # expression.
                  distribution.probabilities.tolist()),
            # Supply the result of tensor_snapshot(context) to MAPPOPolicyFactorSample.
            tensor_snapshot(context), critic_sample_id, None, None, None,
            # Supply self.policy_parameter_identity to MAPPOPolicyFactorSample.
            BEHAVIOR_SOURCE, self.policy_parameter_identity, False,
            # Supply the result of MappingProxyType(a dictionary containing stochastic_masked_sample, argmax_used,
            # presentation_only, selection_rule,...) to MAPPOPolicyFactorSample.
            MappingProxyType({
                # Store False under 'stochastic_masked_sample'.
                "stochastic_masked_sample": False,
                # Store True under 'argmax_used'.
                "argmax_used": True,
                # Store True under 'presentation_only'.
                "presentation_only": True,
                # Store PRESENTATION_SELECTION_RULE under 'selection_rule'.
                "selection_rule": PRESENTATION_SELECTION_RULE,
                # Store 0 under 'future_outcome_fields'.
                "future_outcome_fields": 0,
                # Store 0 under 'route_truth_actor_fields'.
                "route_truth_actor_fields": 0}))

    # Factor diagnostics using the inputs and processing steps below.
    # Input batch_id: the supplied batch id.
    # Output: a tuple built from a lazy sequence of a dictionary containing decision_role, ego_id, claim_identity,
    # proposal_id, action_names, hard_action_mask,... for item in self.pending_factors;...
    def factor_diagnostics(self, batch_id):
        # Return a tuple built from a lazy sequence of a dictionary containing decision_role, ego_id,
        # claim_identity, proposal_id, action_names, hard_action_mask,... for item in self.pending_factors; retain
        # entries satisfying item.joint_batch_id equals batch_id to the caller.
        return tuple({
            # Store item.decision_role under 'decision_role'.
            "decision_role": item.decision_role,
            # Store item.ego_id under 'ego_id'.
            "ego_id": item.ego_id,
            # Store item.claim_identity under 'claim_identity'.
            "claim_identity": item.claim_identity,
            # Store item.proposal_id under 'proposal_id'.
            "proposal_id": item.proposal_id,
            # Store item.action_names under 'action_names'.
            "action_names": item.action_names,
            # Store item.hard_action_mask under 'hard_action_mask'.
            "hard_action_mask": item.hard_action_mask,
            # Store item.behavior_probability_vector under 'masked_probabilities'.
            "masked_probabilities": item.behavior_probability_vector,
            # Store item.selected_semantic_action under 'selected_action'.
            "selected_action": item.selected_semantic_action,
            # Store item.selected_action_index under 'selected_action_index'.
            "selected_action_index": item.selected_action_index,
            # Store PRESENTATION_SELECTION_RULE under 'selection_rule'.
            "selection_rule": PRESENTATION_SELECTION_RULE,
        # Evaluate self.pending_factors as part of the enclosing expression.
        } for item in self.pending_factors
          # Evaluate item.joint_batch_id equals batch_id as part of the enclosing expression.
          if item.joint_batch_id == batch_id)
