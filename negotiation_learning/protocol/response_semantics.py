"""Deterministic response candidates and hard feasibility for Step 5E.2."""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Tuple

from ..v2v_claim_bus import same_instant
from .message_models import ClaimRelinquishmentProposal, ProposalId, ProtocolState


class NegotiationResponseAction(str, Enum):
    ACCEPT_RELINQUISHMENT = "ACCEPT_RELINQUISHMENT"
    REJECT_RELINQUISHMENT = "REJECT_RELINQUISHMENT"


RESPONSE_ACTIONS = (
    NegotiationResponseAction.ACCEPT_RELINQUISHMENT,
    NegotiationResponseAction.REJECT_RELINQUISHMENT,
)
RESPONSE_ACTOR_ARCHITECTURE = "REQUIRES_EXPERIMENTAL_SELECTION"
RESPONSE_POLICY_INTERFACE_STATUS = "RESPONSE_POLICY_INTERFACE_IMPLEMENTED_UNTRAINED"
RESPONSE_POLICY_LEARNING_STATUS = "RESPONSE_POLICY_LEARNING_METHOD_PENDING"


@dataclass(frozen=True)
class ResponseCandidateProvenance:
    ego_ldm: str
    same_step_protocol_snapshot: str
    local_mpnn_encoding: str
    deterministic_regulatory_evidence: str


@dataclass(frozen=True)
class NegotiationResponseCandidate:
    ego_id: str
    proposal_id: ProposalId
    proposer_id: str
    counterparty_id: str
    yielding_vehicle_id: str
    priority_vehicle_id: str
    available_response_actions: Tuple[NegotiationResponseAction, ...]
    action_feasibility_mask: Tuple[bool, ...]
    infeasibility_reasons: Tuple[str | None, ...]
    regulatory_profile: str
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    source_snapshot_timestamp: float
    protocol_state: ProtocolState
    provenance: ResponseCandidateProvenance

    def __post_init__(self):
        if not all(type(item) is bool for item in self.action_feasibility_mask):
            raise TypeError("RESPONSE_FEASIBILITY_MUST_BE_EXACT_BOOLEAN")


class NegotiationResponseCandidateBuilder:
    """Build local responder choices without learned feasibility or thresholds."""

    @staticmethod
    def build(ego_id, proposal, original_edges, current_timestamp,
              regulatory_profile, source_consistent=True,
              policy_authorized=True):
        if not isinstance(proposal, ClaimRelinquishmentProposal):
            raise TypeError("VALID_PROPOSAL_REQUIRED")
        claim = (proposal.yielding_vehicle_id, proposal.priority_vehicle_id)
        existing = any((edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                       == claim for edge in original_edges)
        reason = None
        if ego_id != proposal.receiver_id or ego_id != proposal.yielding_vehicle_id:
            reason = "EGO_NOT_PROPOSAL_RECEIVER"
        elif not existing:
            reason = "SOURCE_CLAIM_NO_LONGER_VALID"
        elif proposal.regulatory_profile != regulatory_profile:
            reason = "REGULATORY_PROFILE_MISMATCH"
        elif not source_consistent:
            reason = "SOURCE_SNAPSHOT_MISMATCH"
        elif not same_instant(proposal.source_negotiation_timestamp,
                              current_timestamp):
            reason = "SOURCE_SNAPSHOT_MISMATCH"
        elif not policy_authorized:
            reason = "PROTOCOL_BLOCKED"
        feasible = reason is None
        return NegotiationResponseCandidate(
            ego_id, proposal.proposal_id, proposal.sender_id,
            proposal.receiver_id, *claim, RESPONSE_ACTIONS,
            (feasible, feasible), (reason, reason), proposal.regulatory_profile,
            proposal.applicable_rule_ids, proposal.source_sections,
            proposal.source_negotiation_timestamp, ProtocolState.PROPOSAL_PENDING,
            ResponseCandidateProvenance(
                "EGO_LDM", "CURRENT_FROZEN_SAME_STEP_PROTOCOL_SNAPSHOT",
                "CURRENT_LOCAL_MPNN_ENCODING",
                "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
            ),
        )
