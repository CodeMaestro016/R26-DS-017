"""Presentation-only deterministic inference over the frozen selected policy."""

from types import MappingProxyType

import torch

from negotiation_training.final_selection import FinalSelectionInferenceProvider
from negotiation_training.mappo_provider import BEHAVIOR_SOURCE
from negotiation_training.rollout import MAPPOPolicyFactorSample, tensor_snapshot


PRESENTATION_SELECTION_RULE = (
    "DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY")


class PanelDeterministicInferenceProvider(FinalSelectionInferenceProvider):
    """Select the maximum-probability feasible semantic action per factor.

    This changes presentation-time sampling only. The selected checkpoint,
    actor logits, hard masks, protocol semantics, and physical planner remain
    untouched.
    """

    selection_rule = PRESENTATION_SELECTION_RULE

    def _sample(self, context, batch_id, episode_id, scenario_id,
                critic_sample_id):
        with torch.no_grad():
            _, distribution = self.bundle.policy.distribution_for(context)
            selected_index = int(torch.argmax(
                distribution.probabilities).item())
            log_probability = distribution.evaluate_action_index(
                selected_index)
        event_id = (batch_id, context.decision_role.value, context.ego_id,
                    context.claim_identity, context.proposal_id)
        return MAPPOPolicyFactorSample(
            event_id, batch_id, episode_id, scenario_id, context.ego_id,
            context.decision_role.value, context.claim_identity,
            context.proposal_id, context.action_names,
            tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
            selected_index, context.action_names[selected_index],
            float(log_probability.item()),
            tuple(float(x) for x in
                  distribution.probabilities.tolist()),
            tensor_snapshot(context), critic_sample_id, None, None, None,
            BEHAVIOR_SOURCE, self.policy_parameter_identity, False,
            MappingProxyType({
                "stochastic_masked_sample": False,
                "argmax_used": True,
                "presentation_only": True,
                "selection_rule": PRESENTATION_SELECTION_RULE,
                "future_outcome_fields": 0,
                "route_truth_actor_fields": 0}))

    def factor_diagnostics(self, batch_id):
        return tuple({
            "decision_role": item.decision_role,
            "ego_id": item.ego_id,
            "claim_identity": item.claim_identity,
            "proposal_id": item.proposal_id,
            "action_names": item.action_names,
            "hard_action_mask": item.hard_action_mask,
            "masked_probabilities": item.behavior_probability_vector,
            "selected_action": item.selected_semantic_action,
            "selected_action_index": item.selected_action_index,
            "selection_rule": PRESENTATION_SELECTION_RULE,
        } for item in self.pending_factors
          if item.joint_batch_id == batch_id)
