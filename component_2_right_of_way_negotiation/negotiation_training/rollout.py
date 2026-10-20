"""Immutable Step 5J.3B.3 behavior-rollout records and exact replay."""

# Import hashlib for use in this module.
import hashlib
# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple

# Import torch for use in this module.
import torch

# Import NegotiationDecisionRole, NegotiationPolicyDecisionContext, PolicyDecisionProvenance from
# negotiation_learning.mappo_interface for the operations below.
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MAPPOBehaviorRolloutIdentity to group the state and operations declared below.
# Declared fields: rollout_id, frozen_design_id, architecture_contract_id, optimization_contract_id,
# training_manifest_id, checkpoint_identity.
# Construction and attribute behavior follow the declared decorators and base classes.
class MAPPOBehaviorRolloutIdentity:
    # Declare rollout_id as tuple for this data structure.
    rollout_id: tuple
    # Declare frozen_design_id as tuple for this data structure.
    frozen_design_id: tuple
    # Declare architecture_contract_id as tuple for this data structure.
    architecture_contract_id: tuple
    # Declare optimization_contract_id as tuple for this data structure.
    optimization_contract_id: tuple
    # Declare training_manifest_id as tuple for this data structure.
    training_manifest_id: tuple
    # Set checkpoint_identity to the text 'STEP_5J_3B_3'; declare its type as str.
    checkpoint_identity: str = "STEP_5J_3B_3"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ActorTensorSnapshot to group the state and operations declared below.
# Declared fields: ego_embedding, graph_embedding, subject_representation, protocol_representation,
# responder_role_one_hot, action_names, hard_action_mask, ego_id, counterparty_id, decision_role, claim_identity,
# proposal_id,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ActorTensorSnapshot:
    # Declare ego_embedding as Tuple[float, ...] for this data structure.
    ego_embedding: Tuple[float, ...]
    # Declare graph_embedding as Tuple[float, ...] for this data structure.
    graph_embedding: Tuple[float, ...]
    # Declare subject_representation as Tuple[float, ...] for this data structure.
    subject_representation: Tuple[float, ...]
    # Declare protocol_representation as Optional[Tuple[float, ...]] for this data structure.
    protocol_representation: Optional[Tuple[float, ...]]
    # Declare responder_role_one_hot as Optional[Tuple[float, ...]] for this data structure.
    responder_role_one_hot: Optional[Tuple[float, ...]]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare hard_action_mask as Tuple[bool, ...] for this data structure.
    hard_action_mask: Tuple[bool, ...]
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare decision_role as str for this data structure.
    decision_role: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare source_timestamp as float for this data structure.
    source_timestamp: float
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MAPPOPolicyFactorSample to group the state and operations declared below.
# Declared fields: decision_event_id, joint_batch_id, episode_id, scenario_id, ego_id, decision_role,
# claim_identity, proposal_id, action_names, hard_action_mask, selected_action_index,
# selected_semantic_action,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MAPPOPolicyFactorSample:
    # Declare decision_event_id as tuple for this data structure.
    decision_event_id: tuple
    # Declare joint_batch_id as tuple for this data structure.
    joint_batch_id: tuple
    # Declare episode_id as tuple for this data structure.
    episode_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare decision_role as str for this data structure.
    decision_role: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare action_names as Tuple[str, ...] for this data structure.
    action_names: Tuple[str, ...]
    # Declare hard_action_mask as Tuple[bool, ...] for this data structure.
    hard_action_mask: Tuple[bool, ...]
    # Declare selected_action_index as int for this data structure.
    selected_action_index: int
    # Declare selected_semantic_action as str for this data structure.
    selected_semantic_action: str
    # Declare behavior_policy_log_probability as float for this data structure.
    behavior_policy_log_probability: float
    # Declare behavior_probability_vector as Tuple[float, ...] for this data structure.
    behavior_probability_vector: Tuple[float, ...]
    # Declare actor_observation_snapshot as ActorTensorSnapshot for this data structure.
    actor_observation_snapshot: ActorTensorSnapshot
    # Declare critic_sample_id as tuple for this data structure.
    critic_sample_id: tuple
    # Declare return_record_id as Optional[tuple] for this data structure.
    return_record_id: Optional[tuple]
    # Declare advantage_record_id as Optional[tuple] for this data structure.
    advantage_record_id: Optional[tuple]
    # Declare advantage as Optional[float] for this data structure.
    advantage: Optional[float]
    # Declare behavior_policy_source as str for this data structure.
    behavior_policy_source: str
    # Declare policy_parameter_identity as tuple for this data structure.
    policy_parameter_identity: tuple
    # Declare ppo_update_eligible as bool for this data structure.
    ppo_update_eligible: bool
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MAPPOCriticSample to group the state and operations declared below.
# Declared fields: critic_sample_id, joint_batch_id, centralized_input, value_at_collection, return_record_id,
# target_return, value_error.
# Construction and attribute behavior follow the declared decorators and base classes.
class MAPPOCriticSample:
    # Declare critic_sample_id as tuple for this data structure.
    critic_sample_id: tuple
    # Declare joint_batch_id as tuple for this data structure.
    joint_batch_id: tuple
    # Declare centralized_input as Tuple[float, ...] for this data structure.
    centralized_input: Tuple[float, ...]
    # Declare value_at_collection as float for this data structure.
    value_at_collection: float
    # Declare return_record_id as Optional[tuple] for this data structure.
    return_record_id: Optional[tuple]
    # Declare target_return as Optional[float] for this data structure.
    target_return: Optional[float]
    # Declare value_error as Optional[float] for this data structure.
    value_error: Optional[float]


# Tensor snapshot using the inputs and processing steps below.
# Input context: the supplied context.
# Output: the result of ActorTensorSnapshot(a tuple built from a lazy sequence of a floating-point number built
# from x for x in the result...).
def tensor_snapshot(context):
    # Set role to context.decision_role.value.
    role = context.decision_role.value
    # Return the result of ActorTensorSnapshot(a tuple built from a lazy sequence of a floating-point number built
    # from x for x in the result...) to the caller.
    return ActorTensorSnapshot(
        # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the result of
        # context.ego_embedding.tolist() to ActorTensorSnapshot.
        tuple(float(x) for x in context.ego_embedding.tolist()),
        # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the result of
        # context.local_graph_embedding.tolist() to ActorTensorSnapshot.
        tuple(float(x) for x in context.local_graph_embedding.tolist()),
        # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the result of
        # context.claim_or_proposal_representation.tolist() to ActorTensorSnapshot.
        tuple(float(x) for x in
              # Evaluate the result of context.claim_or_proposal_representation.tolist() as part of the enclosing
              # expression.
              context.claim_or_proposal_representation.tolist()),
        # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the result of
        # context.protocol_state_representation.tolist() when context.protocol_state_representation is a different
        # object from None, otherwise None to ActorTensorSnapshot.
        (tuple(float(x) for x in context.protocol_state_representation.tolist())
         # Evaluate context.protocol_state_representation is a different object from None as part of the enclosing
         # expression.
         if context.protocol_state_representation is not None else None),
        # Supply a tuple containing 0.0, 1.0 when role equals the text 'RESPONDER', otherwise None to
        # ActorTensorSnapshot.
        ((0.0, 1.0) if role == "RESPONDER" else None),
        # Supply a tuple built from context.action_names to ActorTensorSnapshot.
        tuple(context.action_names),
        # Supply a tuple built from a lazy sequence of a Boolean built from x for x in the result of
        # context.action_feasibility_mask.tolist() to ActorTensorSnapshot.
        tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
        # Supply context.counterparty_id to ActorTensorSnapshot.
        context.ego_id, context.counterparty_id, role,
        # Supply a tuple built from context.claim_identity to ActorTensorSnapshot.
        tuple(context.claim_identity), context.proposal_id,
        # Supply a floating-point number built from context.source_snapshot_timestamp to ActorTensorSnapshot.
        float(context.source_snapshot_timestamp),
        # Store 0 under 'route_truth_fields'.
        {"route_truth_fields": 0,
         # Store context.provenance.local_observation_identity under 'local_observation_identity'.
         "local_observation_identity": context.provenance.local_observation_identity,
         # Store context.provenance.local_graph_identity under 'local_graph_identity'.
         "local_graph_identity": context.provenance.local_graph_identity,
         # Store context.provenance.local_mpnn_identity under 'local_mpnn_identity'.
         "local_mpnn_identity": context.provenance.local_mpnn_identity,
         # Store context.provenance.semantic_subject_identity under 'semantic_subject_identity'.
         "semantic_subject_identity": context.provenance.semantic_subject_identity,
         # Store context.provenance.hard_mask_identity under 'hard_mask_identity'.
         "hard_mask_identity": context.provenance.hard_mask_identity,
         # Store context.regulatory_profile under 'regulatory_profile'.
         "regulatory_profile": context.regulatory_profile,
         # Store context.communication_model under 'communication_model'.
         "communication_model": context.communication_model})


# Context from snapshot using the inputs and processing steps below.
# Input snapshot: the supplied snapshot.
# Output: the result of NegotiationPolicyDecisionContext(snapshot.ego_id, role, snapshot.counterparty_id,
# snapshot.claim_identity, snapshot.proposal_id,...).
def context_from_snapshot(snapshot):
    # Set role to the result of NegotiationDecisionRole(snapshot.decision_role).
    role = NegotiationDecisionRole(snapshot.decision_role)
    # Set provenance to the result of PolicyDecisionProvenance(snapshot.provenance at
    # 'local_observation_identity', snapshot.provenance at...).
    provenance = PolicyDecisionProvenance(
        # Supply snapshot.provenance at 'local_observation_identity' to PolicyDecisionProvenance.
        snapshot.provenance["local_observation_identity"],
        # Supply snapshot.provenance at 'local_graph_identity' to PolicyDecisionProvenance.
        snapshot.provenance["local_graph_identity"],
        # Supply snapshot.provenance at 'local_mpnn_identity' to PolicyDecisionProvenance.
        snapshot.provenance["local_mpnn_identity"],
        # Supply snapshot.provenance at 'semantic_subject_identity' to PolicyDecisionProvenance.
        snapshot.provenance["semantic_subject_identity"],
        # Supply snapshot.provenance at 'hard_mask_identity' to PolicyDecisionProvenance.
        snapshot.provenance["hard_mask_identity"])
    # Return the result of NegotiationPolicyDecisionContext(snapshot.ego_id, role, snapshot.counterparty_id,
    # snapshot.claim_identity, snapshot.proposal_id,...) to the caller.
    return NegotiationPolicyDecisionContext(
        # Supply snapshot.counterparty_id to NegotiationPolicyDecisionContext.
        snapshot.ego_id, role, snapshot.counterparty_id,
        # Supply snapshot.claim_identity to NegotiationPolicyDecisionContext.
        snapshot.claim_identity, snapshot.proposal_id,
        # Supply snapshot.provenance at 'local_observation_identity' to NegotiationPolicyDecisionContext.
        snapshot.provenance["local_observation_identity"],
        # Supply snapshot.source_timestamp to NegotiationPolicyDecisionContext.
        snapshot.source_timestamp,
        # Supply dtype as torch.float32.
        torch.tensor(snapshot.ego_embedding, dtype=torch.float32),
        # Supply dtype as torch.float32.
        torch.tensor(snapshot.graph_embedding, dtype=torch.float32),
        # Supply dtype as torch.float32.
        torch.tensor(snapshot.subject_representation, dtype=torch.float32),
        # Supply dtype as torch.float32.
        (torch.tensor(snapshot.protocol_representation, dtype=torch.float32)
         # Evaluate snapshot.protocol_representation is a different object from None as part of the enclosing
         # expression.
         if snapshot.protocol_representation is not None else None),
        # Supply snapshot.action_names to NegotiationPolicyDecisionContext.
        snapshot.action_names,
        # Supply dtype as torch.bool.
        torch.tensor(snapshot.hard_action_mask, dtype=torch.bool), provenance,
        # Supply snapshot.provenance at 'regulatory_profile' to NegotiationPolicyDecisionContext.
        snapshot.provenance["regulatory_profile"],
        # Supply snapshot.provenance at 'communication_model' to NegotiationPolicyDecisionContext.
        snapshot.provenance["communication_model"])


# Replay without resampling; masks and log probabilities must be exact.
# Input current_policy: the supplied current policy.
# Input sample: the supplied sample.
# Output: a tuple containing distribution, current, a floating-point number built from the result of
# distribution.entropy.item(), ratio.
# Processing: select branches using the stated conditions.
def evaluate_policy_factor_sample(current_policy, sample):
    """Replay without resampling; masks and log probabilities must be exact."""
    # Set context to the result of context_from_snapshot(sample.actor_observation_snapshot).
    context = context_from_snapshot(sample.actor_observation_snapshot)
    # Run this branch when a tuple built from the result of context.action_feasibility_mask.tolist() differs from
    # sample.hard_action_mask.
    if tuple(context.action_feasibility_mask.tolist()) != sample.hard_action_mask:
        # Raise RuntimeError with the text 'MAPPO_HARD_MASK_REPLAY_MISMATCH' to stop this execution path.
        raise RuntimeError("MAPPO_HARD_MASK_REPLAY_MISMATCH")
    # Set (_, distribution) to the result of current_policy.distribution_for(context).
    _, distribution = current_policy.distribution_for(context)
    # Run this branch when a tuple built from a lazy sequence of a Boolean built from x for x in the result of
    # distribution.action_feasibility_mask.tolist() differs from sample.hard_action_mask.
    if tuple(bool(x) for x in distribution.action_feasibility_mask.tolist()) != (
            # Evaluate sample.hard_action_mask as part of the enclosing expression.
            sample.hard_action_mask):
        # Raise RuntimeError with the text 'MAPPO_HARD_MASK_REPLAY_MISMATCH' to stop this execution path.
        raise RuntimeError("MAPPO_HARD_MASK_REPLAY_MISMATCH")
    # Set log_probability to the result of distribution.evaluate_action_index(sample.selected_action_index).
    log_probability = distribution.evaluate_action_index(
        # Supply sample.selected_action_index to distribution.evaluate_action_index.
        sample.selected_action_index)
    # Set current to a floating-point number built from the result of log_probability.item().
    current = float(log_probability.item())
    # Run this branch when current differs from sample.behavior_policy_log_probability.
    if current != sample.behavior_policy_log_probability:
        # Raise RuntimeError with the text 'MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH' to stop this execution path.
        raise RuntimeError("MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH")
    # Set ratio to a floating-point number built from the result of torch.exp(torch.tensor(current -
    # sample.behavior_policy_log_probability, dtype=torch.float64)).item().
    ratio = float(torch.exp(torch.tensor(
        # Supply current minus sample.behavior_policy_log_probability to torch.tensor.
        current - sample.behavior_policy_log_probability,
        # Supply dtype as torch.float64.
        dtype=torch.float64)).item())
    # Run this branch when ratio differs from 1.0.
    if ratio != 1.0:
        # Raise RuntimeError with the text 'MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH' to stop this execution path.
        raise RuntimeError("MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH")
    # Return a tuple containing distribution, current, a floating-point number built from the result of
    # distribution.entropy.item(), ratio to the caller.
    return distribution, current, float(distribution.entropy.item()), ratio


# Parameter hash using the inputs and processing steps below.
# Input module: the supplied module.
# Output: the hexadecimal digest from digest.
# Processing: iterate over the relevant records.
def parameter_hash(module):
    # Set digest to the result of hashlib.sha256().
    digest = hashlib.sha256()
    # Iterate over key/value pairs from module.state_dict(), binding each item to (name, parameter).
    for name, parameter in module.state_dict().items():
        # Update digest with the supplied entries.
        digest.update(name.encode())
        # Update digest with the supplied entries.
        digest.update(parameter.detach().cpu().numpy().tobytes())
    # Return the hexadecimal digest from digest to the caller.
    return digest.hexdigest()
