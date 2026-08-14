"""Immutable semantic messages for explicit claim-relinquishment agreement."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from ..models import NegotiationAction


ProposalId = Tuple[float, str, str, str, str]


class ProposalResponse(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class ProtocolState(str, Enum):
    NO_PROPOSAL = "NO_PROPOSAL"
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    PROPOSAL_PENDING = "PROPOSAL_PENDING"
    PROPOSAL_REJECTED = "PROPOSAL_REJECTED"
    AGREEMENT_ESTABLISHED = "AGREEMENT_ESTABLISHED"
    SOURCE_CLAIM_INVALID = "SOURCE_CLAIM_INVALID"
    PROTOCOL_BLOCKED = "PROTOCOL_BLOCKED"
    PROTOCOL_DISAGREEMENT = "PROTOCOL_DISAGREEMENT"


@dataclass(frozen=True)
class ClaimRelinquishmentProposal:
    proposal_id: ProposalId
    sender_id: str
    receiver_id: str
    yielding_vehicle_id: str
    priority_vehicle_id: str
    proposed_action: NegotiationAction
    source_negotiation_timestamp: float
    source_claim_timestamp: Optional[float]
    regulatory_profile: str
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    shared_conflict_zone_ids: Tuple[str, ...]
    protocol_state: ProtocolState = ProtocolState.PROPOSAL_CREATED


@dataclass(frozen=True)
class ClaimRelinquishmentResponse:
    proposal_id: ProposalId
    sender_id: str
    receiver_id: str
    response: ProposalResponse
    source_negotiation_timestamp: float
    regulatory_profile: str


@dataclass(frozen=True)
class ClaimAgreementRecord:
    proposal_id: ProposalId
    yielding_vehicle_id: str
    priority_vehicle_id: str
    proposal_sender_id: str
    proposal_receiver_id: str
    response_sender_id: str
    response_type: ProposalResponse
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    regulatory_profile: str
    source_negotiation_timestamp: float
    source_claim_timestamp: Optional[float]
    agreement_status: ProtocolState = ProtocolState.AGREEMENT_ESTABLISHED


@dataclass(frozen=True)
class NegotiatedPrecedenceOverlay:
    original_claim: Tuple[str, str]
    agreement_status: ProtocolState
    overlay_effect: Optional[str]
    proposal: Optional[ClaimRelinquishmentProposal]
    response: Optional[ClaimRelinquishmentResponse]
    agreement: Optional[ClaimAgreementRecord]
    participants: Tuple[str, str]
    regulatory_profile: Optional[str]
    source_timestamp: Optional[float]
    diagnostic: Optional[str]


@dataclass(frozen=True)
class ProtocolEvaluation:
    state: ProtocolState
    agreement_complete: bool
    original_regulatory_precedence_graph: Tuple[Tuple[str, str], ...]
    effective_coordination_graph: Tuple[Tuple[str, str], ...]
    negotiated_agreement_overlay: NegotiatedPrecedenceOverlay


@dataclass(frozen=True)
class JointNegotiationProtocolSnapshot:
    timestamp: float
    regulatory_profile: str
    communication_model: str
    original_regulatory_precedence_graph: Tuple[Tuple[str, str], ...]
    per_claim_evaluations: Tuple[ProtocolEvaluation, ...]
    completed_agreements: Tuple[ClaimAgreementRecord, ...]
    pending_proposals: Tuple[ClaimRelinquishmentProposal, ...]
    rejected_proposals: Tuple[ClaimRelinquishmentProposal, ...]
    blocked_protocol_items: Tuple[ProtocolEvaluation, ...]
    protocol_disagreements: Tuple[ProtocolEvaluation, ...]
    negotiated_precedence_overlays: Tuple[NegotiatedPrecedenceOverlay, ...]
    effective_coordination_graph: Tuple[Tuple[str, str], ...]
