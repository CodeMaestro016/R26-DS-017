"""Untrained CPU CTDE interfaces for claim-level negotiation.

CTDE is supported by Yu et al., *The Surprising Effectiveness of PPO in
Cooperative, Multi-Agent Games* (2021), arXiv:2103.01955, and Lowe et al.,
*Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments*
(NeurIPS 2017). Set aggregation follows Zaheer et al., *Deep Sets*
(NeurIPS 2017), arXiv:1703.06114. No PPO implementation is present here.
"""

from dataclasses import dataclass
from typing import Tuple

import torch
from torch import nn


TRAINING_ONLY = "TRAINING_ONLY"
NOT_AVAILABLE_TO_DEPLOYED_ACTOR = "NOT_AVAILABLE_TO_DEPLOYED_ACTOR"
PARAMETER_SHARING_STATUS = "ARCHITECTURE_CHOICE_REQUIRES_ABLATION"


@dataclass(frozen=True)
class ActorForwardInput:
    ego_id: str
    counterparty_id: str
    ego_embedding: torch.Tensor
    local_graph_embedding: torch.Tensor
    claim_representation: torch.Tensor
    action_feasibility_mask: torch.Tensor
    provenance: "ActorInputProvenance"


@dataclass(frozen=True)
class ActorInputProvenance:
    ego_ldm: str
    same_step_v2v_graph: str
    mpnn_encoding: str
    deterministic_regulatory_evidence: str


@dataclass(frozen=True)
class ActorForwardOutput:
    unmasked_action_logits: torch.Tensor
    action_feasibility_mask: torch.Tensor
    masked_action_distribution_inputs: Tuple[torch.Tensor, torch.Tensor]


class DecentralizedNegotiationActor(nn.Module):
    """Local claim-logit interface; dimensions must be selected explicitly."""

    def __init__(self, input_dim, action_count):
        super().__init__()
        if not isinstance(input_dim, int) or input_dim <= 0:
            raise ValueError("input_dim must be an explicit positive integer")
        if action_count != 2:
            raise ValueError("ACTION_COUNT_MUST_MATCH_CLAIM_SEMANTIC_VOCABULARY")
        self.input_dim = input_dim
        self.action_count = action_count
        self.logit_head = nn.Linear(input_dim, action_count)
        self.to(torch.device("cpu"))

    def forward(self, actor_input):
        if not isinstance(actor_input.provenance, ActorInputProvenance):
            raise TypeError("ACTOR_INPUT_PROVENANCE_REQUIRED")
        tensors = (
            actor_input.ego_embedding, actor_input.local_graph_embedding,
            actor_input.claim_representation,
        )
        if any(value.device.type != "cpu" for value in tensors):
            raise ValueError("CPU_DEVICE_REQUIRED")
        combined = torch.cat(tensors, dim=-1)
        if combined.shape[-1] != self.input_dim:
            raise ValueError("ACTOR_INPUT_DIMENSION_MISMATCH")
        mask = actor_input.action_feasibility_mask
        if mask.dtype is not torch.bool or mask.shape[-1] != self.action_count:
            raise ValueError("BOOLEAN_ACTION_MASK_REQUIRED")
        logits = self.logit_head(combined)
        # The future distribution owns framework-specific masking. Step 5E
        # deliberately carries exact logits and Boolean feasibility separately.
        return ActorForwardOutput(logits, mask, (logits, mask))


class CentralizedCriticInputBuilder:
    """TRAINING_ONLY Deep-Sets SUM over legitimate per-agent representations."""

    availability = (TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR)
    aggregation = "SUM"

    @staticmethod
    def build(per_agent_representations):
        if per_agent_representations.ndim < 2:
            raise ValueError("AGENT_SET_DIMENSION_REQUIRED")
        if per_agent_representations.shape[-2] < 1:
            raise ValueError("AT_LEAST_ONE_AGENT_REQUIRED")
        if per_agent_representations.device.type != "cpu":
            raise ValueError("CPU_DEVICE_REQUIRED")
        return per_agent_representations.sum(dim=-2)


class CentralizedNegotiationCritic(nn.Module):
    """TRAINING_ONLY scalar state-value head; never exposed to the actor."""

    availability = (TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR)

    def __init__(self, input_dim):
        super().__init__()
        if not isinstance(input_dim, int) or input_dim <= 0:
            raise ValueError("input_dim must be an explicit positive integer")
        self.input_dim = input_dim
        self.value_head = nn.Linear(input_dim, 1)
        self.to(torch.device("cpu"))

    def forward(self, joint_training_representation):
        if joint_training_representation.device.type != "cpu":
            raise ValueError("CPU_DEVICE_REQUIRED")
        if joint_training_representation.shape[-1] != self.input_dim:
            raise ValueError("CRITIC_INPUT_DIMENSION_MISMATCH")
        return self.value_head(joint_training_representation)
