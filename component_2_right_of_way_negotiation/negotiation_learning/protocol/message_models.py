"""Immutable semantic messages for explicit claim-relinquishment agreement."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple

# Import NegotiationAction from ..models for the operations below.
from ..models import NegotiationAction


# Set ProposalId to Tuple at (float, str, str, str, str).
ProposalId = Tuple[float, str, str, str, str]


# Define ProposalResponse to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ProposalResponse(str, Enum):
    # Set ACCEPT to the text 'ACCEPT'.
    ACCEPT = "ACCEPT"
    # Set REJECT to the text 'REJECT'.
    REJECT = "REJECT"


# Define ProtocolState to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ProtocolState(str, Enum):
    # Set NO_PROPOSAL to the text 'NO_PROPOSAL'.
    NO_PROPOSAL = "NO_PROPOSAL"
    # Set PROPOSAL_CREATED to the text 'PROPOSAL_CREATED'.
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    # Set PROPOSAL_PENDING to the text 'PROPOSAL_PENDING'.
    PROPOSAL_PENDING = "PROPOSAL_PENDING"
    # Set PROPOSAL_REJECTED to the text 'PROPOSAL_REJECTED'.
    PROPOSAL_REJECTED = "PROPOSAL_REJECTED"
    # Set AGREEMENT_ESTABLISHED to the text 'AGREEMENT_ESTABLISHED'.
    AGREEMENT_ESTABLISHED = "AGREEMENT_ESTABLISHED"
    # Set SOURCE_CLAIM_INVALID to the text 'SOURCE_CLAIM_INVALID'.
    SOURCE_CLAIM_INVALID = "SOURCE_CLAIM_INVALID"
    # Set PROTOCOL_BLOCKED to the text 'PROTOCOL_BLOCKED'.
    PROTOCOL_BLOCKED = "PROTOCOL_BLOCKED"
    # Set PROTOCOL_DISAGREEMENT to the text 'PROTOCOL_DISAGREEMENT'.
    PROTOCOL_DISAGREEMENT = "PROTOCOL_DISAGREEMENT"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ClaimRelinquishmentProposal to group the state and operations declared below.
# Declared fields: proposal_id, sender_id, receiver_id, yielding_vehicle_id, priority_vehicle_id, proposed_action,
# source_negotiation_timestamp, source_claim_timestamp, regulatory_profile, applicable_rule_ids,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ClaimRelinquishmentProposal:
    # Declare proposal_id as ProposalId for this data structure.
    proposal_id: ProposalId
    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare receiver_id as str for this data structure.
    receiver_id: str
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare proposed_action as NegotiationAction for this data structure.
    proposed_action: NegotiationAction
    # Declare source_negotiation_timestamp as float for this data structure.
    source_negotiation_timestamp: float
    # Declare source_claim_timestamp as Optional[float] for this data structure.
    source_claim_timestamp: Optional[float]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare shared_conflict_zone_ids as Tuple[str, ...] for this data structure.
    shared_conflict_zone_ids: Tuple[str, ...]
    # Set protocol_state to ProtocolState.PROPOSAL_CREATED; declare its type as ProtocolState.
    protocol_state: ProtocolState = ProtocolState.PROPOSAL_CREATED


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ClaimRelinquishmentResponse to group the state and operations declared below.
# Declared fields: proposal_id, sender_id, receiver_id, response, source_negotiation_timestamp,
# regulatory_profile.
# Construction and attribute behavior follow the declared decorators and base classes.
class ClaimRelinquishmentResponse:
    # Declare proposal_id as ProposalId for this data structure.
    proposal_id: ProposalId
    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare receiver_id as str for this data structure.
    receiver_id: str
    # Declare response as ProposalResponse for this data structure.
    response: ProposalResponse
    # Declare source_negotiation_timestamp as float for this data structure.
    source_negotiation_timestamp: float
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ClaimAgreementRecord to group the state and operations declared below.
# Declared fields: proposal_id, yielding_vehicle_id, priority_vehicle_id, proposal_sender_id,
# proposal_receiver_id, response_sender_id, response_type, applicable_rule_ids, source_sections,
# regulatory_profile,....
# Construction and attribute behavior follow the declared decorators and base classes.
class ClaimAgreementRecord:
    # Declare proposal_id as ProposalId for this data structure.
    proposal_id: ProposalId
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare proposal_sender_id as str for this data structure.
    proposal_sender_id: str
    # Declare proposal_receiver_id as str for this data structure.
    proposal_receiver_id: str
    # Declare response_sender_id as str for this data structure.
    response_sender_id: str
    # Declare response_type as ProposalResponse for this data structure.
    response_type: ProposalResponse
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare source_negotiation_timestamp as float for this data structure.
    source_negotiation_timestamp: float
    # Declare source_claim_timestamp as Optional[float] for this data structure.
    source_claim_timestamp: Optional[float]
    # Set agreement_status to ProtocolState.AGREEMENT_ESTABLISHED; declare its type as ProtocolState.
    agreement_status: ProtocolState = ProtocolState.AGREEMENT_ESTABLISHED


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiatedPrecedenceOverlay to group the state and operations declared below.
# Declared fields: original_claim, agreement_status, overlay_effect, proposal, response, agreement, participants,
# regulatory_profile, source_timestamp, diagnostic.
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiatedPrecedenceOverlay:
    # Declare original_claim as Tuple[str, str] for this data structure.
    original_claim: Tuple[str, str]
    # Declare agreement_status as ProtocolState for this data structure.
    agreement_status: ProtocolState
    # Declare overlay_effect as Optional[str] for this data structure.
    overlay_effect: Optional[str]
    # Declare proposal as Optional[ClaimRelinquishmentProposal] for this data structure.
    proposal: Optional[ClaimRelinquishmentProposal]
    # Declare response as Optional[ClaimRelinquishmentResponse] for this data structure.
    response: Optional[ClaimRelinquishmentResponse]
    # Declare agreement as Optional[ClaimAgreementRecord] for this data structure.
    agreement: Optional[ClaimAgreementRecord]
    # Declare participants as Tuple[str, str] for this data structure.
    participants: Tuple[str, str]
    # Declare regulatory_profile as Optional[str] for this data structure.
    regulatory_profile: Optional[str]
    # Declare source_timestamp as Optional[float] for this data structure.
    source_timestamp: Optional[float]
    # Declare diagnostic as Optional[str] for this data structure.
    diagnostic: Optional[str]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ProtocolEvaluation to group the state and operations declared below.
# Declared fields: state, agreement_complete, original_regulatory_precedence_graph, effective_coordination_graph,
# negotiated_agreement_overlay.
# Construction and attribute behavior follow the declared decorators and base classes.
class ProtocolEvaluation:
    # Declare state as ProtocolState for this data structure.
    state: ProtocolState
    # Declare agreement_complete as bool for this data structure.
    agreement_complete: bool
    # Declare original_regulatory_precedence_graph as Tuple[Tuple[str, str], ...] for this data structure.
    original_regulatory_precedence_graph: Tuple[Tuple[str, str], ...]
    # Declare effective_coordination_graph as Tuple[Tuple[str, str], ...] for this data structure.
    effective_coordination_graph: Tuple[Tuple[str, str], ...]
    # Declare negotiated_agreement_overlay as NegotiatedPrecedenceOverlay for this data structure.
    negotiated_agreement_overlay: NegotiatedPrecedenceOverlay


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointNegotiationProtocolSnapshot to group the state and operations declared below.
# Declared fields: timestamp, regulatory_profile, communication_model, original_regulatory_precedence_graph,
# per_claim_evaluations, completed_agreements, pending_proposals, rejected_proposals, blocked_protocol_items,....
# Construction and attribute behavior follow the declared decorators and base classes.
class JointNegotiationProtocolSnapshot:
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare communication_model as str for this data structure.
    communication_model: str
    # Declare original_regulatory_precedence_graph as Tuple[Tuple[str, str], ...] for this data structure.
    original_regulatory_precedence_graph: Tuple[Tuple[str, str], ...]
    # Declare per_claim_evaluations as Tuple[ProtocolEvaluation, ...] for this data structure.
    per_claim_evaluations: Tuple[ProtocolEvaluation, ...]
    # Declare completed_agreements as Tuple[ClaimAgreementRecord, ...] for this data structure.
    completed_agreements: Tuple[ClaimAgreementRecord, ...]
    # Declare pending_proposals as Tuple[ClaimRelinquishmentProposal, ...] for this data structure.
    pending_proposals: Tuple[ClaimRelinquishmentProposal, ...]
    # Declare rejected_proposals as Tuple[ClaimRelinquishmentProposal, ...] for this data structure.
    rejected_proposals: Tuple[ClaimRelinquishmentProposal, ...]
    # Declare blocked_protocol_items as Tuple[ProtocolEvaluation, ...] for this data structure.
    blocked_protocol_items: Tuple[ProtocolEvaluation, ...]
    # Declare protocol_disagreements as Tuple[ProtocolEvaluation, ...] for this data structure.
    protocol_disagreements: Tuple[ProtocolEvaluation, ...]
    # Declare negotiated_precedence_overlays as Tuple[NegotiatedPrecedenceOverlay, ...] for this data structure.
    negotiated_precedence_overlays: Tuple[NegotiatedPrecedenceOverlay, ...]
    # Declare effective_coordination_graph as Tuple[Tuple[str, str], ...] for this data structure.
    effective_coordination_graph: Tuple[Tuple[str, str], ...]
