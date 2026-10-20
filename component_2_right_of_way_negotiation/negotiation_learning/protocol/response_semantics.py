"""Deterministic response candidates and hard feasibility for Step 5E.2."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple

# Import same_instant from ..v2v_claim_bus for the operations below.
from ..v2v_claim_bus import same_instant
# Import ClaimRelinquishmentProposal, ProposalId, ProtocolState from .message_models for the operations below.
from .message_models import ClaimRelinquishmentProposal, ProposalId, ProtocolState


# Define NegotiationResponseAction to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class NegotiationResponseAction(str, Enum):
    # Set ACCEPT_RELINQUISHMENT to the text 'ACCEPT_RELINQUISHMENT'.
    ACCEPT_RELINQUISHMENT = "ACCEPT_RELINQUISHMENT"
    # Set REJECT_RELINQUISHMENT to the text 'REJECT_RELINQUISHMENT'.
    REJECT_RELINQUISHMENT = "REJECT_RELINQUISHMENT"


# Set RESPONSE_ACTIONS to a tuple containing NegotiationResponseAction.ACCEPT_RELINQUISHMENT,
# NegotiationResponseAction.REJECT_RELINQUISHMENT.
RESPONSE_ACTIONS = (
    # Include NegotiationResponseAction.ACCEPT_RELINQUISHMENT in this tuple.
    NegotiationResponseAction.ACCEPT_RELINQUISHMENT,
    # Include NegotiationResponseAction.REJECT_RELINQUISHMENT in this tuple.
    NegotiationResponseAction.REJECT_RELINQUISHMENT,
)
# Set RESPONSE_ACTOR_ARCHITECTURE to the text 'REQUIRES_EXPERIMENTAL_SELECTION'.
RESPONSE_ACTOR_ARCHITECTURE = "REQUIRES_EXPERIMENTAL_SELECTION"
# Set RESPONSE_POLICY_INTERFACE_STATUS to the text 'RESPONSE_POLICY_INTERFACE_IMPLEMENTED_UNTRAINED'.
RESPONSE_POLICY_INTERFACE_STATUS = "RESPONSE_POLICY_INTERFACE_IMPLEMENTED_UNTRAINED"
# Set RESPONSE_POLICY_LEARNING_STATUS to the text 'RESPONSE_POLICY_LEARNING_METHOD_PENDING'.
RESPONSE_POLICY_LEARNING_STATUS = "RESPONSE_POLICY_LEARNING_METHOD_PENDING"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ResponseCandidateProvenance to group the state and operations declared below.
# Declared fields: ego_ldm, same_step_protocol_snapshot, local_mpnn_encoding, deterministic_regulatory_evidence.
# Construction and attribute behavior follow the declared decorators and base classes.
class ResponseCandidateProvenance:
    # Declare ego_ldm as str for this data structure.
    ego_ldm: str
    # Declare same_step_protocol_snapshot as str for this data structure.
    same_step_protocol_snapshot: str
    # Declare local_mpnn_encoding as str for this data structure.
    local_mpnn_encoding: str
    # Declare deterministic_regulatory_evidence as str for this data structure.
    deterministic_regulatory_evidence: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationResponseCandidate to group the state and operations declared below.
# Declared fields: ego_id, proposal_id, proposer_id, counterparty_id, yielding_vehicle_id, priority_vehicle_id,
# available_response_actions, action_feasibility_mask, infeasibility_reasons, regulatory_profile,....
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationResponseCandidate:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare proposal_id as ProposalId for this data structure.
    proposal_id: ProposalId
    # Declare proposer_id as str for this data structure.
    proposer_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare available_response_actions as Tuple[NegotiationResponseAction, ...] for this data structure.
    available_response_actions: Tuple[NegotiationResponseAction, ...]
    # Declare action_feasibility_mask as Tuple[bool, ...] for this data structure.
    action_feasibility_mask: Tuple[bool, ...]
    # Declare infeasibility_reasons as Tuple[str | None, ...] for this data structure.
    infeasibility_reasons: Tuple[str | None, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare source_snapshot_timestamp as float for this data structure.
    source_snapshot_timestamp: float
    # Declare protocol_state as ProtocolState for this data structure.
    protocol_state: ProtocolState
    # Declare provenance as ResponseCandidateProvenance for this data structure.
    provenance: ResponseCandidateProvenance

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Run this branch when the negation of whether every item is true in a lazy sequence of type(item) is the
        # same object as bool for item in self.action_feasibility_mask.
        if not all(type(item) is bool for item in self.action_feasibility_mask):
            # Raise TypeError with the text 'RESPONSE_FEASIBILITY_MUST_BE_EXACT_BOOLEAN' to stop this execution
            # path.
            raise TypeError("RESPONSE_FEASIBILITY_MUST_BE_EXACT_BOOLEAN")


# Build local responder choices without learned feasibility or thresholds.
# Instances expose the attributes and methods implemented in this class.
class NegotiationResponseCandidateBuilder:
    """Build local responder choices without learned feasibility or thresholds."""

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Build using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input proposal: the supplied proposal.
    # Input original_edges: the supplied original edges.
    # Input current_timestamp: the supplied current timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input source_consistent: the supplied source consistent.
    # Input policy_authorized: the supplied policy authorized.
    # Output: the result of NegotiationResponseCandidate(ego_id, proposal.proposal_id, proposal.sender_id,
    # proposal.receiver_id, the unpacked values from...).
    # Processing: select branches using the stated conditions.
    def build(ego_id, proposal, original_edges, current_timestamp,
              # Declare regulatory_profile, source_consistent as input parameters.
              regulatory_profile, source_consistent=True,
              # Declare policy_authorized as input parameter.
              policy_authorized=True):
        # Run this branch when the negation of whether proposal has type ClaimRelinquishmentProposal.
        if not isinstance(proposal, ClaimRelinquishmentProposal):
            # Raise TypeError with the text 'VALID_PROPOSAL_REQUIRED' to stop this execution path.
            raise TypeError("VALID_PROPOSAL_REQUIRED")
        # Set claim to a tuple containing proposal.yielding_vehicle_id, proposal.priority_vehicle_id.
        claim = (proposal.yielding_vehicle_id, proposal.priority_vehicle_id)
        # Set existing to whether any item is true in a lazy sequence of a tuple containing
        # edge['yielding_vehicle_id'], edge['priority_vehicle_id'] equals claim for edge in original_edges.
        existing = any((edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                       # Evaluate original_edges as part of the enclosing expression.
                       == claim for edge in original_edges)
        # Set reason to None.
        reason = None
        # Run this branch when ego_id differs from proposal.receiver_id or ego_id differs from
        # proposal.yielding_vehicle_id.
        if ego_id != proposal.receiver_id or ego_id != proposal.yielding_vehicle_id:
            # Set reason to the text 'EGO_NOT_PROPOSAL_RECEIVER'.
            reason = "EGO_NOT_PROPOSAL_RECEIVER"
        # Run this branch when the negation of existing.
        elif not existing:
            # Set reason to the text 'SOURCE_CLAIM_NO_LONGER_VALID'.
            reason = "SOURCE_CLAIM_NO_LONGER_VALID"
        # Run this branch when proposal.regulatory_profile differs from regulatory_profile.
        elif proposal.regulatory_profile != regulatory_profile:
            # Set reason to the text 'REGULATORY_PROFILE_MISMATCH'.
            reason = "REGULATORY_PROFILE_MISMATCH"
        # Run this branch when the negation of source_consistent.
        elif not source_consistent:
            # Set reason to the text 'SOURCE_SNAPSHOT_MISMATCH'.
            reason = "SOURCE_SNAPSHOT_MISMATCH"
        # Run this branch when the negation of the result of same_instant(proposal.source_negotiation_timestamp,
        # current_timestamp).
        elif not same_instant(proposal.source_negotiation_timestamp,
                              # Supply current_timestamp to same_instant.
                              current_timestamp):
            # Set reason to the text 'SOURCE_SNAPSHOT_MISMATCH'.
            reason = "SOURCE_SNAPSHOT_MISMATCH"
        # Run this branch when the negation of policy_authorized.
        elif not policy_authorized:
            # Set reason to the text 'PROTOCOL_BLOCKED'.
            reason = "PROTOCOL_BLOCKED"
        # Set feasible to reason is the same object as None.
        feasible = reason is None
        # Return the result of NegotiationResponseCandidate(ego_id, proposal.proposal_id, proposal.sender_id,
        # proposal.receiver_id, the unpacked values from...) to the caller.
        return NegotiationResponseCandidate(
            # Supply proposal.proposal_id to NegotiationResponseCandidate.
            ego_id, proposal.proposal_id, proposal.sender_id,
            # Supply proposal.receiver_id to NegotiationResponseCandidate.
            proposal.receiver_id, *claim, RESPONSE_ACTIONS,
            # Supply proposal.regulatory_profile to NegotiationResponseCandidate.
            (feasible, feasible), (reason, reason), proposal.regulatory_profile,
            # Supply proposal.applicable_rule_ids to NegotiationResponseCandidate.
            proposal.applicable_rule_ids, proposal.source_sections,
            # Supply proposal.source_negotiation_timestamp to NegotiationResponseCandidate.
            proposal.source_negotiation_timestamp, ProtocolState.PROPOSAL_PENDING,
            # Supply the result of ResponseCandidateProvenance(the text 'EGO_LDM', the text
            # 'CURRENT_FROZEN_SAME_STEP_PROTOCOL_SNAPSHOT', the text...) to NegotiationResponseCandidate.
            ResponseCandidateProvenance(
                "EGO_LDM", "CURRENT_FROZEN_SAME_STEP_PROTOCOL_SNAPSHOT",
                "CURRENT_LOCAL_MPNN_ENCODING",
                "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
            ),
        )
