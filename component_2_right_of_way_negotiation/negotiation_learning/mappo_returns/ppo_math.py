"""Per-policy-factor PPO mathematics only; no aggregation or optimization."""

# Import math for use in this module.
import math
# Import torch for use in this module.
import torch

# Import ReturnSemanticError from .calculators for the operations below.
from .calculators import ReturnSemanticError
# Import PPOPolicyFactorSample from .models for the operations below.
from .models import PPOPolicyFactorSample


# Create policy factor sample using the inputs and processing steps below.
# Input decision_event_id: the supplied decision event id.
# Input joint_batch_id: the supplied joint batch id.
# Input ego_id: the identifier of the ego vehicle.
# Input decision_role: the supplied decision role.
# Input claim_identity: the supplied claim identity.
# Input proposal_id: the supplied proposal id.
# Input actor_observation_snapshot: the supplied actor observation snapshot.
# Input hard_action_mask: the supplied hard action mask.
# Input selected_action_index: the supplied selected action index.
# Input selected_semantic_action: the supplied selected semantic action.
# Input behavior_policy_log_probability: the supplied behavior policy log probability.
# Input return_record: the supplied return record.
# Input advantage_record: the supplied advantage record.
# Input provenance: the supplied provenance.
# Output: the result of PPOPolicyFactorSample(decision_event_id, joint_batch_id, ego_id, decision_role,
# claim_identity, proposal_id,...).
# Processing: select branches using the stated conditions.
def create_policy_factor_sample(*, decision_event_id, joint_batch_id, ego_id,
                                # Declare decision_role, claim_identity, proposal_id as input parameters.
                                decision_role, claim_identity, proposal_id,
                                # Declare actor_observation_snapshot, hard_action_mask as input parameters.
                                actor_observation_snapshot, hard_action_mask,
                                # Declare selected_action_index, selected_semantic_action as input parameters.
                                selected_action_index, selected_semantic_action,
                                # Declare behavior_policy_log_probability, return_record as input parameters.
                                behavior_policy_log_probability, return_record,
                                # Declare advantage_record, provenance as input parameters.
                                advantage_record, provenance):
    # Set mask to a tuple built from a lazy sequence of a Boolean built from item for item in hard_action_mask.
    mask = tuple(bool(item) for item in hard_action_mask)
    # Run this branch when selected_action_index is less than 0 or selected_action_index is at least the number of
    # entries in mask.
    if selected_action_index < 0 or selected_action_index >= len(mask):
        # Raise ReturnSemanticError with the text 'BEHAVIOR_ACTION_INDEX_OUT_OF_RANGE' to stop this execution
        # path.
        raise ReturnSemanticError("BEHAVIOR_ACTION_INDEX_OUT_OF_RANGE")
    # Run this branch when the negation of mask at selected_action_index.
    if not mask[selected_action_index]:
        # Raise ReturnSemanticError with the text 'BEHAVIOR_ACTION_NOT_FEASIBLE' to stop this execution path.
        raise ReturnSemanticError("BEHAVIOR_ACTION_NOT_FEASIBLE")
    # Set behavior to a floating-point number built from behavior_policy_log_probability.
    behavior = float(behavior_policy_log_probability)
    # Run this branch when the negation of whether behavior contains finite numeric values.
    if not math.isfinite(behavior):
        # Raise ReturnSemanticError with the text 'FINITE_BEHAVIOR_LOG_PROBABILITY_REQUIRED' to stop this
        # execution path.
        raise ReturnSemanticError("FINITE_BEHAVIOR_LOG_PROBABILITY_REQUIRED")
    # Return the result of PPOPolicyFactorSample(decision_event_id, joint_batch_id, ego_id, decision_role,
    # claim_identity, proposal_id,...) to the caller.
    return PPOPolicyFactorSample(
        # Supply decision_event_id to PPOPolicyFactorSample.
        decision_event_id, joint_batch_id, ego_id, decision_role,
        # Supply actor_observation_snapshot to PPOPolicyFactorSample.
        claim_identity, proposal_id, actor_observation_snapshot, mask,
        # Supply selected_semantic_action to PPOPolicyFactorSample.
        selected_action_index, selected_semantic_action, behavior,
        # Supply advantage_record.advantage_record_id to PPOPolicyFactorSample.
        return_record.return_record_id, advantage_record.advantage_record_id,
        # Supply advantage_record.advantage to PPOPolicyFactorSample.
        advantage_record.advantage, "PPO_MATHEMATICAL_FACTOR_ONLY", provenance,
    )


# Validate policy replay semantics using the inputs and processing steps below.
# Input sample: the supplied sample.
# Input action_names: the supplied action names.
# Input hard_action_mask: the supplied hard action mask.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def validate_policy_replay_semantics(sample, action_names, hard_action_mask):
    # Set mask to a tuple built from a lazy sequence of a Boolean built from item for item in hard_action_mask.
    mask = tuple(bool(item) for item in hard_action_mask)
    # Set stored_names to a tuple built from sample.actor_observation_snapshot.action_names.
    stored_names = tuple(sample.actor_observation_snapshot.action_names)
    # Run this branch when a tuple built from action_names differs from stored_names or mask differs from
    # sample.hard_action_mask.
    if tuple(action_names) != stored_names or mask != sample.hard_action_mask:
        # Raise ReturnSemanticError with the text 'POLICY_REPLAY_SEMANTICS_MISMATCH' to stop this execution path.
        raise ReturnSemanticError("POLICY_REPLAY_SEMANTICS_MISMATCH")
    # Run this branch when sample.selected_semantic_action differs from stored_names at
    # sample.selected_action_index.
    if sample.selected_semantic_action != stored_names[sample.selected_action_index]:
        # Raise ReturnSemanticError with the text 'POLICY_REPLAY_SEMANTICS_MISMATCH' to stop this execution path.
        raise ReturnSemanticError("POLICY_REPLAY_SEMANTICS_MISMATCH")


# Compute the PPO importance ratio as exp(current log probability minus behavior log probability), rejecting
# non-finite inputs.
# Input current_policy_log_probability: the supplied current policy log probability.
# Input behavior_policy_log_probability: the supplied behavior policy log probability.
# Output: the exponential of current minus behavior.
# Processing: select branches using the stated conditions.
def importance_ratio(current_policy_log_probability,
                     # Declare behavior_policy_log_probability as input parameter.
                     behavior_policy_log_probability):
    # Set current to a tensor built from current_policy_log_probability.
    current = torch.as_tensor(current_policy_log_probability, dtype=torch.float64)
    # Set behavior to a tensor built from behavior_policy_log_probability.
    behavior = torch.as_tensor(behavior_policy_log_probability, dtype=torch.float64)
    # Run this branch when the negation of the result of torch.isfinite(current).all() or the negation of the
    # result of torch.isfinite(behavior).all().
    if not torch.isfinite(current).all() or not torch.isfinite(behavior).all():
        # Raise ReturnSemanticError with the text 'FINITE_POLICY_LOG_PROBABILITIES_REQUIRED' to stop this
        # execution path.
        raise ReturnSemanticError("FINITE_POLICY_LOG_PROBABILITIES_REQUIRED")
    # Exponentiating the difference of log probabilities gives the current-to-behavior probability ratio.
    # Return the exponential of current minus behavior to the caller.
    return torch.exp(current - behavior)


# Unclipped surrogate term using the inputs and processing steps below.
# Input ratio: the supplied ratio.
# Input advantage: the advantage value used in the policy objective.
# Output: ratio multiplied by a tensor built from advantage.
def unclipped_surrogate_term(ratio, advantage):
    # Return ratio multiplied by a tensor built from advantage to the caller.
    return ratio * torch.as_tensor(advantage, dtype=ratio.dtype, device=ratio.device)


# Form the original and clipped ratio-times-advantage terms and return their elementwise minimum.
# Input ratio: the supplied ratio.
# Input advantage: the advantage value used in the policy objective.
# Input clip_epsilon: the PPO ratio clipping width.
# Output: a tuple containing unclipped, clipped, the result of torch.minimum(unclipped, clipped).
# Processing: select branches using the stated conditions.
def ppo_clipped_surrogate_terms(ratio, advantage, clip_epsilon):
    """Algebra helper only: epsilon is mandatory and has no project default."""
    # Set epsilon to a floating-point number built from clip_epsilon.
    epsilon = float(clip_epsilon)
    # Run this branch when epsilon is at most 0 or the negation of whether epsilon contains finite numeric values.
    if epsilon <= 0 or not math.isfinite(epsilon):
        # Raise ReturnSemanticError with the text 'POSITIVE_FINITE_CLIP_EPSILON_REQUIRED' to stop this execution
        # path.
        raise ReturnSemanticError("POSITIVE_FINITE_CLIP_EPSILON_REQUIRED")
    # Set advantage to a tensor built from advantage.
    advantage = torch.as_tensor(advantage, dtype=ratio.dtype, device=ratio.device)
    # Set unclipped to ratio multiplied by advantage.
    unclipped = ratio * advantage
    # Limit the ratio to [1 - epsilon, 1 + epsilon] before multiplying by advantage; the following minimum forms
    # the PPO clipped objective.
    # Set clipped to ratio bounded by the supplied limits multiplied by advantage.
    clipped = torch.clamp(ratio, 1.0 - epsilon, 1.0 + epsilon) * advantage
    # Return a tuple containing unclipped, clipped, the result of torch.minimum(unclipped, clipped) to the caller.
    return unclipped, clipped, torch.minimum(unclipped, clipped)

