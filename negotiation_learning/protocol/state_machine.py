"""Pure deterministic Step 5E.1 claim-agreement state machine."""

from ..claim_semantics import PolicyAuthority, PrecedenceClaim
from ..models import NegotiationAction
from ..v2v_claim_bus import same_instant
from .message_models import (
    ClaimAgreementRecord, ClaimRelinquishmentProposal,
    ClaimRelinquishmentResponse, NegotiatedPrecedenceOverlay, ProposalResponse,
    JointNegotiationProtocolSnapshot, ProtocolEvaluation, ProtocolState,
)


RESPONSE_POLICY_STATUS = "RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION"


class ProtocolSemanticError(ValueError):
    """A categorical semantic failure, never a score or penalty."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def deterministic_proposal_id(timestamp, yielding, priority, sender, receiver):
    """Stable semantic identity; no randomness, counter, or hash."""
    return (float(timestamp), yielding, priority, sender, receiver)


class ClaimRelinquishmentProtocol:
    """Validate proposal/response evidence without mutating regulatory truth."""

    BLOCKED_AUTHORITY = frozenset({
        "SOURCE_SNAPSHOT_MISMATCH", "REGULATORY_PROFILE_MISMATCH",
        "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "REGULATORY_INPUT_UNRESOLVED",
        "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED",
    })

    @staticmethod
    def create_proposal(claim, source_negotiation_timestamp,
                        regulatory_profile, policy_authority):
        if not isinstance(claim, PrecedenceClaim):
            raise ProtocolSemanticError("SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        if claim.ego_id != claim.priority_vehicle_id:
            raise ProtocolSemanticError("SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        if claim.counterparty_id != claim.yielding_vehicle_id:
            raise ProtocolSemanticError("INVALID_COUNTERPARTY")
        if policy_authority is not PolicyAuthority.POLICY_AUTHORIZED:
            raise ProtocolSemanticError("PROTOCOL_BLOCKED")
        proposal_id = deterministic_proposal_id(
            source_negotiation_timestamp, claim.yielding_vehicle_id,
            claim.priority_vehicle_id, claim.ego_id, claim.counterparty_id,
        )
        return ClaimRelinquishmentProposal(
            proposal_id, claim.ego_id, claim.counterparty_id,
            claim.yielding_vehicle_id, claim.priority_vehicle_id,
            NegotiationAction.RELINQUISH_CLAIM,
            float(source_negotiation_timestamp), claim.source_snapshot_timestamp,
            regulatory_profile, claim.applicable_rule_ids, claim.source_sections,
            claim.shared_conflict_zone_ids,
        )

    @staticmethod
    def create_response(proposal, responder_id, response,
                        source_negotiation_timestamp, regulatory_profile):
        if responder_id != proposal.receiver_id:
            raise ProtocolSemanticError("INVALID_COUNTERPARTY")
        response = response if isinstance(response, ProposalResponse) else ProposalResponse(response)
        return ClaimRelinquishmentResponse(
            proposal.proposal_id, responder_id, proposal.sender_id, response,
            float(source_negotiation_timestamp), regulatory_profile,
        )

    def evaluate(self, original_edges, messages, current_timestamp,
                 regulatory_profile, policy_authorized=True,
                 source_consistent=True):
        original = tuple(sorted({
            (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            for edge in original_edges
        }))
        proposals = {message for message in messages
                     if isinstance(message, ClaimRelinquishmentProposal)}
        responses = {message for message in messages
                     if isinstance(message, ClaimRelinquishmentResponse)}
        if not proposals:
            return self._result(ProtocolState.NO_PROPOSAL, original)
        if len(proposals) != 1:
            return self._result(ProtocolState.PROTOCOL_DISAGREEMENT, original,
                                diagnostic="PROTOCOL_DISAGREEMENT")
        proposal = next(iter(proposals))
        claim = (proposal.yielding_vehicle_id, proposal.priority_vehicle_id)
        matching_edges = tuple(edge for edge in original_edges if (
            edge["yielding_vehicle_id"], edge["priority_vehicle_id"]
        ) == claim)
        base = dict(original=original, proposal=proposal, claim=claim)
        expected_id = deterministic_proposal_id(
            proposal.source_negotiation_timestamp, *claim,
            proposal.sender_id, proposal.receiver_id,
        )
        if proposal.proposal_id != expected_id:
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="PROPOSAL_ID_MISMATCH")
        if proposal.sender_id != proposal.priority_vehicle_id:
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        if proposal.receiver_id != proposal.yielding_vehicle_id:
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="INVALID_COUNTERPARTY")
        if claim not in original:
            return self._result(ProtocolState.SOURCE_CLAIM_INVALID, **base,
                                diagnostic="SOURCE_CLAIM_NO_LONGER_VALID")
        if (proposal.source_claim_timestamp is None or
                not any(same_instant(proposal.source_claim_timestamp,
                                     edge.get("timestamp"))
                        for edge in matching_edges)):
            return self._result(ProtocolState.SOURCE_CLAIM_INVALID, **base,
                                diagnostic="SOURCE_CLAIM_NO_LONGER_VALID")
        if (not source_consistent or not policy_authorized or
                proposal.proposed_action is not NegotiationAction.RELINQUISH_CLAIM):
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="PROTOCOL_BLOCKED")
        if (proposal.regulatory_profile != regulatory_profile or
                not same_instant(proposal.source_negotiation_timestamp,
                                 current_timestamp)):
            diagnostic = ("AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH"
                          if proposal.regulatory_profile != regulatory_profile
                          else "SOURCE_SNAPSHOT_MISMATCH")
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic=diagnostic)
        relevant = tuple(response for response in responses
                         if response.proposal_id == proposal.proposal_id)
        if responses and not relevant:
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="RESPONSE_PROPOSAL_MISMATCH")
        if not relevant:
            return self._result(ProtocolState.PROPOSAL_PENDING, **base)
        response_types = {item.response for item in relevant}
        if len(response_types) != 1:
            return self._result(ProtocolState.PROTOCOL_DISAGREEMENT, **base,
                                diagnostic="PROTOCOL_DISAGREEMENT")
        response = sorted(relevant, key=lambda item: (
            item.sender_id, item.receiver_id, item.response.value,
        ))[0]
        if (response.sender_id != proposal.receiver_id or
                response.receiver_id != proposal.sender_id):
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="INVALID_COUNTERPARTY")
        if response.regulatory_profile != proposal.regulatory_profile:
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH")
        if not same_instant(
                current_timestamp, proposal.source_negotiation_timestamp,
                response.source_negotiation_timestamp):
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                diagnostic="SOURCE_SNAPSHOT_MISMATCH")
        if response.response is ProposalResponse.REJECT:
            return self._result(ProtocolState.PROPOSAL_REJECTED, **base,
                                response=response)
        agreement = ClaimAgreementRecord(
            proposal.proposal_id, *claim, proposal.sender_id,
            proposal.receiver_id, response.sender_id, response.response,
            proposal.applicable_rule_ids, proposal.source_sections,
            proposal.regulatory_profile, proposal.source_negotiation_timestamp,
            proposal.source_claim_timestamp,
        )
        return self._result(ProtocolState.AGREEMENT_ESTABLISHED, **base,
                            response=response, agreement=agreement)

    def evaluate_all_claims(self, original_edges, messages, current_timestamp,
                            regulatory_profile, policy_authorized=True,
                            source_consistent=True):
        """Evaluate each deterministic proposal identity independently."""
        original = tuple(sorted({
            (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            for edge in original_edges
        }))
        proposals = tuple(sorted({
            item for item in messages
            if isinstance(item, ClaimRelinquishmentProposal)
        }, key=lambda item: item.proposal_id))
        responses = tuple(item for item in messages
                          if isinstance(item, ClaimRelinquishmentResponse))
        evaluations = []
        known_ids = {item.proposal_id for item in proposals}
        for proposal in proposals:
            group = (proposal,) + tuple(
                item for item in responses
                if item.proposal_id == proposal.proposal_id
            )
            evaluations.append(self.evaluate(
                original_edges, group, current_timestamp, regulatory_profile,
                policy_authorized, source_consistent,
            ))
        # Preserve orphan response evidence as a local blocked item. ProposalId
        # contains the claim endpoints, so it remains traceable without voting
        # or contaminating a different valid negotiation.
        for proposal_id in sorted({item.proposal_id for item in responses
                                   if item.proposal_id not in known_ids}):
            claim = (proposal_id[1], proposal_id[2])
            evaluations.append(self._result(
                ProtocolState.PROTOCOL_BLOCKED, original, claim=claim,
                diagnostic="RESPONSE_PROPOSAL_MISMATCH",
            ))
        evaluations.sort(key=lambda item: (
            item.negotiated_agreement_overlay.original_claim,
            item.negotiated_agreement_overlay.proposal.proposal_id
            if item.negotiated_agreement_overlay.proposal else (),
        ))
        evaluations = tuple(evaluations)
        completed = tuple(
            item.negotiated_agreement_overlay.agreement for item in evaluations
            if item.agreement_complete
        )
        pending = tuple(
            item.negotiated_agreement_overlay.proposal for item in evaluations
            if item.state is ProtocolState.PROPOSAL_PENDING
        )
        rejected = tuple(
            item.negotiated_agreement_overlay.proposal for item in evaluations
            if item.state is ProtocolState.PROPOSAL_REJECTED
        )
        blocked = tuple(item for item in evaluations if item.state in {
            ProtocolState.PROTOCOL_BLOCKED, ProtocolState.SOURCE_CLAIM_INVALID,
        })
        disagreements = tuple(item for item in evaluations
                              if item.state is ProtocolState.PROTOCOL_DISAGREEMENT)
        agreed_claims = {
            item.negotiated_agreement_overlay.original_claim
            for item in evaluations if item.agreement_complete
        }
        effective = tuple(edge for edge in original if edge not in agreed_claims)
        return JointNegotiationProtocolSnapshot(
            float(current_timestamp), regulatory_profile,
            "IDEAL_SAME_STEP_V2V", original, evaluations, completed, pending,
            rejected, blocked, disagreements,
            tuple(item.negotiated_agreement_overlay for item in evaluations),
            effective,
        )

    @staticmethod
    def _result(state, original, proposal=None, response=None, agreement=None,
                claim=None, diagnostic=None):
        claim = claim or ((proposal.yielding_vehicle_id,
                           proposal.priority_vehicle_id) if proposal else ("", ""))
        complete = state is ProtocolState.AGREEMENT_ESTABLISHED
        effective = tuple(edge for edge in original if not (complete and edge == claim))
        overlay = NegotiatedPrecedenceOverlay(
            claim, state,
            "CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT" if complete else None,
            proposal, response, agreement,
            (claim[1], claim[0]) if claim != ("", "") else ("", ""),
            proposal.regulatory_profile if proposal else None,
            proposal.source_negotiation_timestamp if proposal else None,
            diagnostic,
        )
        return ProtocolEvaluation(state, complete, original, effective, overlay)


def agreement_complete(evaluation):
    return (evaluation.state is ProtocolState.AGREEMENT_ESTABLISHED and
            evaluation.agreement_complete and
            evaluation.negotiated_agreement_overlay.agreement is not None)
