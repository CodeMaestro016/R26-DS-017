"""Per-policy-factor PPO mathematics only; no aggregation or optimization."""

import math
import torch

from .calculators import ReturnSemanticError
from .models import PPOPolicyFactorSample


def create_policy_factor_sample(*, decision_event_id, joint_batch_id, ego_id,
                                decision_role, claim_identity, proposal_id,
                                actor_observation_snapshot, hard_action_mask,
                                selected_action_index, selected_semantic_action,
                                behavior_policy_log_probability, return_record,
                                advantage_record, provenance):
    mask = tuple(bool(item) for item in hard_action_mask)
    if selected_action_index < 0 or selected_action_index >= len(mask):
        raise ReturnSemanticError("BEHAVIOR_ACTION_INDEX_OUT_OF_RANGE")
    if not mask[selected_action_index]:
        raise ReturnSemanticError("BEHAVIOR_ACTION_NOT_FEASIBLE")
    behavior = float(behavior_policy_log_probability)
    if not math.isfinite(behavior):
        raise ReturnSemanticError("FINITE_BEHAVIOR_LOG_PROBABILITY_REQUIRED")
    return PPOPolicyFactorSample(
        decision_event_id, joint_batch_id, ego_id, decision_role,
        claim_identity, proposal_id, actor_observation_snapshot, mask,
        selected_action_index, selected_semantic_action, behavior,
        return_record.return_record_id, advantage_record.advantage_record_id,
        advantage_record.advantage, "PPO_MATHEMATICAL_FACTOR_ONLY", provenance,
    )


def validate_policy_replay_semantics(sample, action_names, hard_action_mask):
    mask = tuple(bool(item) for item in hard_action_mask)
    stored_names = tuple(sample.actor_observation_snapshot.action_names)
    if tuple(action_names) != stored_names or mask != sample.hard_action_mask:
        raise ReturnSemanticError("POLICY_REPLAY_SEMANTICS_MISMATCH")
    if sample.selected_semantic_action != stored_names[sample.selected_action_index]:
        raise ReturnSemanticError("POLICY_REPLAY_SEMANTICS_MISMATCH")


def importance_ratio(current_policy_log_probability,
                     behavior_policy_log_probability):
    current = torch.as_tensor(current_policy_log_probability, dtype=torch.float64)
    behavior = torch.as_tensor(behavior_policy_log_probability, dtype=torch.float64)
    if not torch.isfinite(current).all() or not torch.isfinite(behavior).all():
        raise ReturnSemanticError("FINITE_POLICY_LOG_PROBABILITIES_REQUIRED")
    return torch.exp(current - behavior)


def unclipped_surrogate_term(ratio, advantage):
    return ratio * torch.as_tensor(advantage, dtype=ratio.dtype, device=ratio.device)


def ppo_clipped_surrogate_terms(ratio, advantage, clip_epsilon):
    """Algebra helper only: epsilon is mandatory and has no project default."""
    epsilon = float(clip_epsilon)
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ReturnSemanticError("POSITIVE_FINITE_CLIP_EPSILON_REQUIRED")
    advantage = torch.as_tensor(advantage, dtype=ratio.dtype, device=ratio.device)
    unclipped = ratio * advantage
    clipped = torch.clamp(ratio, 1.0 - epsilon, 1.0 + epsilon) * advantage
    return unclipped, clipped, torch.minimum(unclipped, clipped)

