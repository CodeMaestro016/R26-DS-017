"""Immutable Step 5J.3B.3 behavior-rollout records and exact replay."""

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

import torch

from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance)


@dataclass(frozen=True)
class MAPPOBehaviorRolloutIdentity:
    rollout_id: tuple
    frozen_design_id: tuple
    architecture_contract_id: tuple
    optimization_contract_id: tuple
    training_manifest_id: tuple
    checkpoint_identity: str = "STEP_5J_3B_3"


@dataclass(frozen=True)
class ActorTensorSnapshot:
    ego_embedding: Tuple[float, ...]
    graph_embedding: Tuple[float, ...]
    subject_representation: Tuple[float, ...]
    protocol_representation: Optional[Tuple[float, ...]]
    responder_role_one_hot: Optional[Tuple[float, ...]]
    action_names: Tuple[str, ...]
    hard_action_mask: Tuple[bool, ...]
    ego_id: str
    counterparty_id: str
    decision_role: str
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    source_timestamp: float
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class MAPPOPolicyFactorSample:
    decision_event_id: tuple
    joint_batch_id: tuple
    episode_id: tuple
    scenario_id: tuple
    ego_id: str
    decision_role: str
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    action_names: Tuple[str, ...]
    hard_action_mask: Tuple[bool, ...]
    selected_action_index: int
    selected_semantic_action: str
    behavior_policy_log_probability: float
    behavior_probability_vector: Tuple[float, ...]
    actor_observation_snapshot: ActorTensorSnapshot
    critic_sample_id: tuple
    return_record_id: Optional[tuple]
    advantage_record_id: Optional[tuple]
    advantage: Optional[float]
    behavior_policy_source: str
    policy_parameter_identity: tuple
    ppo_update_eligible: bool
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class MAPPOCriticSample:
    critic_sample_id: tuple
    joint_batch_id: tuple
    centralized_input: Tuple[float, ...]
    value_at_collection: float
    return_record_id: Optional[tuple]
    target_return: Optional[float]
    value_error: Optional[float]


def tensor_snapshot(context):
    role = context.decision_role.value
    return ActorTensorSnapshot(
        tuple(float(x) for x in context.ego_embedding.tolist()),
        tuple(float(x) for x in context.local_graph_embedding.tolist()),
        tuple(float(x) for x in
              context.claim_or_proposal_representation.tolist()),
        (tuple(float(x) for x in context.protocol_state_representation.tolist())
         if context.protocol_state_representation is not None else None),
        ((0.0, 1.0) if role == "RESPONDER" else None),
        tuple(context.action_names),
        tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
        context.ego_id, context.counterparty_id, role,
        tuple(context.claim_identity), context.proposal_id,
        float(context.source_snapshot_timestamp),
        {"route_truth_fields": 0,
         "local_observation_identity": context.provenance.local_observation_identity,
         "local_graph_identity": context.provenance.local_graph_identity,
         "local_mpnn_identity": context.provenance.local_mpnn_identity,
         "semantic_subject_identity": context.provenance.semantic_subject_identity,
         "hard_mask_identity": context.provenance.hard_mask_identity,
         "regulatory_profile": context.regulatory_profile,
         "communication_model": context.communication_model})


def context_from_snapshot(snapshot):
    role = NegotiationDecisionRole(snapshot.decision_role)
    provenance = PolicyDecisionProvenance(
        snapshot.provenance["local_observation_identity"],
        snapshot.provenance["local_graph_identity"],
        snapshot.provenance["local_mpnn_identity"],
        snapshot.provenance["semantic_subject_identity"],
        snapshot.provenance["hard_mask_identity"])
    return NegotiationPolicyDecisionContext(
        snapshot.ego_id, role, snapshot.counterparty_id,
        snapshot.claim_identity, snapshot.proposal_id,
        snapshot.provenance["local_observation_identity"],
        snapshot.source_timestamp,
        torch.tensor(snapshot.ego_embedding, dtype=torch.float32),
        torch.tensor(snapshot.graph_embedding, dtype=torch.float32),
        torch.tensor(snapshot.subject_representation, dtype=torch.float32),
        (torch.tensor(snapshot.protocol_representation, dtype=torch.float32)
         if snapshot.protocol_representation is not None else None),
        snapshot.action_names,
        torch.tensor(snapshot.hard_action_mask, dtype=torch.bool), provenance,
        snapshot.provenance["regulatory_profile"],
        snapshot.provenance["communication_model"])


def evaluate_policy_factor_sample(current_policy, sample):
    """Replay without resampling; masks and log probabilities must be exact."""
    context = context_from_snapshot(sample.actor_observation_snapshot)
    if tuple(context.action_feasibility_mask.tolist()) != sample.hard_action_mask:
        raise RuntimeError("MAPPO_HARD_MASK_REPLAY_MISMATCH")
    _, distribution = current_policy.distribution_for(context)
    if tuple(bool(x) for x in distribution.action_feasibility_mask.tolist()) != (
            sample.hard_action_mask):
        raise RuntimeError("MAPPO_HARD_MASK_REPLAY_MISMATCH")
    log_probability = distribution.evaluate_action_index(
        sample.selected_action_index)
    current = float(log_probability.item())
    if current != sample.behavior_policy_log_probability:
        raise RuntimeError("MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH")
    ratio = float(torch.exp(torch.tensor(
        current - sample.behavior_policy_log_probability,
        dtype=torch.float64)).item())
    if ratio != 1.0:
        raise RuntimeError("MAPPO_BEHAVIOR_LOGPROB_REPLAY_MISMATCH")
    return distribution, current, float(distribution.entropy.item()), ratio


def parameter_hash(module):
    digest = hashlib.sha256()
    for name, parameter in module.state_dict().items():
        digest.update(name.encode())
        digest.update(parameter.detach().cpu().numpy().tobytes())
    return digest.hexdigest()
