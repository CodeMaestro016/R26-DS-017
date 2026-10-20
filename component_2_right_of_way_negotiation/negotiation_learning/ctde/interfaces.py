"""Untrained CPU CTDE interfaces for claim-level negotiation.

CTDE is supported by Yu et al., *The Surprising Effectiveness of PPO in
Cooperative, Multi-Agent Games* (2021), arXiv:2103.01955, and Lowe et al.,
*Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments*
(NeurIPS 2017). Set aggregation follows Zaheer et al., *Deep Sets*
(NeurIPS 2017), arXiv:1703.06114. No PPO implementation is present here.
"""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Tuple from typing for the operations below.
from typing import Tuple

# Import torch for use in this module.
import torch
# Import nn from torch for the operations below.
from torch import nn


# Set TRAINING_ONLY to the text 'TRAINING_ONLY'.
TRAINING_ONLY = "TRAINING_ONLY"
# Set NOT_AVAILABLE_TO_DEPLOYED_ACTOR to the text 'NOT_AVAILABLE_TO_DEPLOYED_ACTOR'.
NOT_AVAILABLE_TO_DEPLOYED_ACTOR = "NOT_AVAILABLE_TO_DEPLOYED_ACTOR"
# Set PARAMETER_SHARING_STATUS to the text 'ARCHITECTURE_CHOICE_REQUIRES_ABLATION'.
PARAMETER_SHARING_STATUS = "ARCHITECTURE_CHOICE_REQUIRES_ABLATION"
# Set RESPONSE_ACTOR_ARCHITECTURE to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
RESPONSE_ACTOR_ARCHITECTURE = "REQUIRES_EXPERIMENTAL_SELECTION"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ActorForwardInput to group the state and operations declared below.
# Declared fields: ego_id, counterparty_id, ego_embedding, local_graph_embedding, claim_representation,
# action_feasibility_mask, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ActorForwardInput:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare ego_embedding as torch.Tensor for this data structure.
    ego_embedding: torch.Tensor
    # Declare local_graph_embedding as torch.Tensor for this data structure.
    local_graph_embedding: torch.Tensor
    # Declare claim_representation as torch.Tensor for this data structure.
    claim_representation: torch.Tensor
    # Declare action_feasibility_mask as torch.Tensor for this data structure.
    action_feasibility_mask: torch.Tensor
    # Declare provenance as 'ActorInputProvenance' for this data structure.
    provenance: "ActorInputProvenance"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ActorInputProvenance to group the state and operations declared below.
# Declared fields: ego_ldm, same_step_v2v_graph, mpnn_encoding, deterministic_regulatory_evidence.
# Construction and attribute behavior follow the declared decorators and base classes.
class ActorInputProvenance:
    # Declare ego_ldm as str for this data structure.
    ego_ldm: str
    # Declare same_step_v2v_graph as str for this data structure.
    same_step_v2v_graph: str
    # Declare mpnn_encoding as str for this data structure.
    mpnn_encoding: str
    # Declare deterministic_regulatory_evidence as str for this data structure.
    deterministic_regulatory_evidence: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ActorForwardOutput to group the state and operations declared below.
# Declared fields: unmasked_action_logits, action_feasibility_mask, masked_action_distribution_inputs.
# Construction and attribute behavior follow the declared decorators and base classes.
class ActorForwardOutput:
    # Declare unmasked_action_logits as torch.Tensor for this data structure.
    unmasked_action_logits: torch.Tensor
    # Declare action_feasibility_mask as torch.Tensor for this data structure.
    action_feasibility_mask: torch.Tensor
    # Declare masked_action_distribution_inputs as Tuple[torch.Tensor, torch.Tensor] for this data structure.
    masked_action_distribution_inputs: Tuple[torch.Tensor, torch.Tensor]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ResponseActorForwardInput to group the state and operations declared below.
# Declared fields: ego_id, proposal_id, ego_embedding, local_graph_embedding, proposal_claim_representation,
# protocol_state_representation, responder_role_one_hot, action_feasibility_mask, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class ResponseActorForwardInput:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare proposal_id as tuple for this data structure.
    proposal_id: tuple
    # Declare ego_embedding as torch.Tensor for this data structure.
    ego_embedding: torch.Tensor
    # Declare local_graph_embedding as torch.Tensor for this data structure.
    local_graph_embedding: torch.Tensor
    # Declare proposal_claim_representation as torch.Tensor for this data structure.
    proposal_claim_representation: torch.Tensor
    # Declare protocol_state_representation as torch.Tensor for this data structure.
    protocol_state_representation: torch.Tensor
    # Declare responder_role_one_hot as torch.Tensor for this data structure.
    responder_role_one_hot: torch.Tensor
    # Declare action_feasibility_mask as torch.Tensor for this data structure.
    action_feasibility_mask: torch.Tensor
    # Declare provenance as 'ActorInputProvenance' for this data structure.
    provenance: "ActorInputProvenance"


# Local claim-logit interface; dimensions must be selected explicitly.
# Base classes: nn.Module.
# Instances expose the attributes and methods implemented in this class.
class DecentralizedNegotiationActor(nn.Module):
    """Local claim-logit interface; dimensions must be selected explicitly."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input input_dim: the supplied input dim.
    # Input action_count: the supplied action count.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, input_dim, action_count):
        # Call super().__init__ with the supplied arguments.
        super().__init__()
        # Run this branch when the negation of whether input_dim has type int or input_dim is at most 0.
        if not isinstance(input_dim, int) or input_dim <= 0:
            # Raise ValueError with the text 'input_dim must be an explicit positive integer' to stop this
            # execution path.
            raise ValueError("input_dim must be an explicit positive integer")
        # Run this branch when action_count differs from 2.
        if action_count != 2:
            # Raise ValueError with the text 'ACTION_COUNT_MUST_MATCH_CLAIM_SEMANTIC_VOCABULARY' to stop this
            # execution path.
            raise ValueError("ACTION_COUNT_MUST_MATCH_CLAIM_SEMANTIC_VOCABULARY")
        # Set self.input_dim to input_dim.
        self.input_dim = input_dim
        # Set self.action_count to action_count.
        self.action_count = action_count
        # Set self.logit_head to the result of nn.Linear(input_dim, action_count).
        self.logit_head = nn.Linear(input_dim, action_count)
        # Call self.to with the supplied arguments.
        self.to(torch.device("cpu"))

    # Forward using the inputs and processing steps below.
    # Input actor_input: the supplied actor input.
    # Output: the result of ActorForwardOutput(logits, mask, a tuple containing logits, mask).
    # Processing: select branches using the stated conditions.
    def forward(self, actor_input):
        # Run this branch when the negation of whether actor_input.provenance has type ActorInputProvenance.
        if not isinstance(actor_input.provenance, ActorInputProvenance):
            # Raise TypeError with the text 'ACTOR_INPUT_PROVENANCE_REQUIRED' to stop this execution path.
            raise TypeError("ACTOR_INPUT_PROVENANCE_REQUIRED")
        # Set tensors to a tuple containing actor_input.ego_embedding, actor_input.local_graph_embedding,
        # actor_input.claim_representation.
        tensors = (
            # Include actor_input.local_graph_embedding in this tuple.
            actor_input.ego_embedding, actor_input.local_graph_embedding,
            # Include actor_input.claim_representation in this tuple.
            actor_input.claim_representation,
        )
        # Run this branch when whether any item is true in a lazy sequence of value.device.type differs from the
        # text 'cpu' for value in tensors.
        if any(value.device.type != "cpu" for value in tensors):
            # Raise ValueError with the text 'CPU_DEVICE_REQUIRED' to stop this execution path.
            raise ValueError("CPU_DEVICE_REQUIRED")
        # Set combined to the tensors concatenated by torch.cat.
        combined = torch.cat(tensors, dim=-1)
        # Run this branch when combined.shape at -1 differs from self.input_dim.
        if combined.shape[-1] != self.input_dim:
            # Raise ValueError with the text 'ACTOR_INPUT_DIMENSION_MISMATCH' to stop this execution path.
            raise ValueError("ACTOR_INPUT_DIMENSION_MISMATCH")
        # Set mask to actor_input.action_feasibility_mask.
        mask = actor_input.action_feasibility_mask
        # Run this branch when mask.dtype is a different object from torch.bool or mask.shape at -1 differs from
        # self.action_count.
        if mask.dtype is not torch.bool or mask.shape[-1] != self.action_count:
            # Raise ValueError with the text 'BOOLEAN_ACTION_MASK_REQUIRED' to stop this execution path.
            raise ValueError("BOOLEAN_ACTION_MASK_REQUIRED")
        # Set logits to the result of self.logit_head(combined).
        logits = self.logit_head(combined)
        # The future distribution owns framework-specific masking. Step 5E
        # deliberately carries exact logits and Boolean feasibility separately.
        # Return the result of ActorForwardOutput(logits, mask, a tuple containing logits, mask) to the caller.
        return ActorForwardOutput(logits, mask, (logits, mask))


# Untrained local ACCEPT/REJECT logit head; never executes a response.
# Base classes: nn.Module.
# Instances expose the attributes and methods implemented in this class.
class DecentralizedNegotiationResponseActor(nn.Module):
    """Untrained local ACCEPT/REJECT logit head; never executes a response."""

    # Set ROLE_COLUMNS to a tuple containing the text 'PROPOSER', the text 'RESPONDER'.
    ROLE_COLUMNS = ("PROPOSER", "RESPONDER")

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input input_dim: the supplied input dim.
    # Input action_count: the supplied action count.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, input_dim, action_count):
        # Call super().__init__ with the supplied arguments.
        super().__init__()
        # Run this branch when the negation of whether input_dim has type int or input_dim is at most 0.
        if not isinstance(input_dim, int) or input_dim <= 0:
            # Raise ValueError with the text 'input_dim must be an explicit positive integer' to stop this
            # execution path.
            raise ValueError("input_dim must be an explicit positive integer")
        # Run this branch when action_count differs from 2.
        if action_count != 2:
            # Raise ValueError with the text 'RESPONSE_ACTION_COUNT_MUST_MATCH_VOCABULARY' to stop this execution
            # path.
            raise ValueError("RESPONSE_ACTION_COUNT_MUST_MATCH_VOCABULARY")
        # Set (self.input_dim, self.action_count) to a tuple containing input_dim, action_count.
        self.input_dim, self.action_count = input_dim, action_count
        # Set self.logit_head to the result of nn.Linear(input_dim, action_count).
        self.logit_head = nn.Linear(input_dim, action_count)
        # Call self.to with the supplied arguments.
        self.to(torch.device("cpu"))

    # Forward using the inputs and processing steps below.
    # Input actor_input: the supplied actor input.
    # Output: the result of ActorForwardOutput(logits, mask, a tuple containing logits, mask).
    # Processing: select branches using the stated conditions.
    def forward(self, actor_input):
        # Run this branch when the negation of whether actor_input.provenance has type ActorInputProvenance.
        if not isinstance(actor_input.provenance, ActorInputProvenance):
            # Raise TypeError with the text 'ACTOR_INPUT_PROVENANCE_REQUIRED' to stop this execution path.
            raise TypeError("ACTOR_INPUT_PROVENANCE_REQUIRED")
        # Set tensors to a tuple containing actor_input.ego_embedding, actor_input.local_graph_embedding,
        # actor_input.proposal_claim_representation,...
        tensors = (
            # Include actor_input.local_graph_embedding in this tuple.
            actor_input.ego_embedding, actor_input.local_graph_embedding,
            # Include actor_input.proposal_claim_representation in this tuple.
            actor_input.proposal_claim_representation,
            # Include actor_input.protocol_state_representation in this tuple.
            actor_input.protocol_state_representation,
            # Include actor_input.responder_role_one_hot in this tuple.
            actor_input.responder_role_one_hot,
        )
        # Run this branch when whether any item is true in a lazy sequence of item.device.type differs from the
        # text 'cpu' for item in tensors.
        if any(item.device.type != "cpu" for item in tensors):
            # Raise ValueError with the text 'CPU_DEVICE_REQUIRED' to stop this execution path.
            raise ValueError("CPU_DEVICE_REQUIRED")
        # Set combined to the tensors concatenated by torch.cat.
        combined = torch.cat(tensors, dim=-1)
        # Run this branch when combined.shape at -1 differs from self.input_dim.
        if combined.shape[-1] != self.input_dim:
            # Raise ValueError with the text 'RESPONSE_ACTOR_INPUT_DIMENSION_MISMATCH' to stop this execution
            # path.
            raise ValueError("RESPONSE_ACTOR_INPUT_DIMENSION_MISMATCH")
        # Run this branch when the negation of the result of torch.equal(actor_input.responder_role_one_hot, a
        # tensor built from a list containing 0.0, 1.0).
        if not torch.equal(actor_input.responder_role_one_hot,
                           # Supply a tensor built from a list containing 0.0, 1.0 to torch.equal.
                           torch.tensor([0.0, 1.0])):
            # Raise ValueError with the text 'RESPONDER_ROLE_ONE_HOT_REQUIRED' to stop this execution path.
            raise ValueError("RESPONDER_ROLE_ONE_HOT_REQUIRED")
        # Set mask to actor_input.action_feasibility_mask.
        mask = actor_input.action_feasibility_mask
        # Run this branch when mask.dtype is a different object from torch.bool or mask.shape at -1 differs from
        # self.action_count.
        if mask.dtype is not torch.bool or mask.shape[-1] != self.action_count:
            # Raise ValueError with the text 'BOOLEAN_ACTION_MASK_REQUIRED' to stop this execution path.
            raise ValueError("BOOLEAN_ACTION_MASK_REQUIRED")
        # Set logits to the result of self.logit_head(combined).
        logits = self.logit_head(combined)
        # Return the result of ActorForwardOutput(logits, mask, a tuple containing logits, mask) to the caller.
        return ActorForwardOutput(logits, mask, (logits, mask))


# TRAINING_ONLY Deep-Sets SUM over legitimate per-agent representations.
# Instances expose the attributes and methods implemented in this class.
class CentralizedCriticInputBuilder:
    """TRAINING_ONLY Deep-Sets SUM over legitimate per-agent representations."""

    # Set availability to a tuple containing TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR.
    availability = (TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR)
    # Set aggregation to the text 'SUM'.
    aggregation = "SUM"

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Build using the inputs and processing steps below.
    # Input per_agent_representations: the supplied per agent representations.
    # Output: the result of per_agent_representations.sum().
    # Processing: select branches using the stated conditions.
    def build(per_agent_representations):
        # Run this branch when per_agent_representations.ndim is less than 2.
        if per_agent_representations.ndim < 2:
            # Raise ValueError with the text 'AGENT_SET_DIMENSION_REQUIRED' to stop this execution path.
            raise ValueError("AGENT_SET_DIMENSION_REQUIRED")
        # Run this branch when per_agent_representations.shape at -2 is less than 1.
        if per_agent_representations.shape[-2] < 1:
            # Raise ValueError with the text 'AT_LEAST_ONE_AGENT_REQUIRED' to stop this execution path.
            raise ValueError("AT_LEAST_ONE_AGENT_REQUIRED")
        # Run this branch when per_agent_representations.device.type differs from the text 'cpu'.
        if per_agent_representations.device.type != "cpu":
            # Raise ValueError with the text 'CPU_DEVICE_REQUIRED' to stop this execution path.
            raise ValueError("CPU_DEVICE_REQUIRED")
        # Return the result of per_agent_representations.sum() to the caller.
        return per_agent_representations.sum(dim=-2)


# TRAINING_ONLY scalar state-value head; never exposed to the actor.
# Base classes: nn.Module.
# Instances expose the attributes and methods implemented in this class.
class CentralizedNegotiationCritic(nn.Module):
    """TRAINING_ONLY scalar state-value head; never exposed to the actor."""

    # Set availability to a tuple containing TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR.
    availability = (TRAINING_ONLY, NOT_AVAILABLE_TO_DEPLOYED_ACTOR)

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input input_dim: the supplied input dim.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, input_dim):
        # Call super().__init__ with the supplied arguments.
        super().__init__()
        # Run this branch when the negation of whether input_dim has type int or input_dim is at most 0.
        if not isinstance(input_dim, int) or input_dim <= 0:
            # Raise ValueError with the text 'input_dim must be an explicit positive integer' to stop this
            # execution path.
            raise ValueError("input_dim must be an explicit positive integer")
        # Set self.input_dim to input_dim.
        self.input_dim = input_dim
        # Set self.value_head to the result of nn.Linear(input_dim, 1).
        self.value_head = nn.Linear(input_dim, 1)
        # Call self.to with the supplied arguments.
        self.to(torch.device("cpu"))

    # Forward using the inputs and processing steps below.
    # Input joint_training_representation: the supplied joint training representation.
    # Output: the result of self.value_head(joint_training_representation).
    # Processing: select branches using the stated conditions.
    def forward(self, joint_training_representation):
        # Run this branch when joint_training_representation.device.type differs from the text 'cpu'.
        if joint_training_representation.device.type != "cpu":
            # Raise ValueError with the text 'CPU_DEVICE_REQUIRED' to stop this execution path.
            raise ValueError("CPU_DEVICE_REQUIRED")
        # Run this branch when joint_training_representation.shape at -1 differs from self.input_dim.
        if joint_training_representation.shape[-1] != self.input_dim:
            # Raise ValueError with the text 'CRITIC_INPUT_DIMENSION_MISMATCH' to stop this execution path.
            raise ValueError("CRITIC_INPUT_DIMENSION_MISMATCH")
        # Return the result of self.value_head(joint_training_representation) to the caller.
        return self.value_head(joint_training_representation)
