"""Pure deterministic Step 5E.1 claim-agreement state machine."""

# Import PolicyAuthority, PrecedenceClaim from ..claim_semantics for the operations below.
from ..claim_semantics import PolicyAuthority, PrecedenceClaim
# Import NegotiationAction from ..models for the operations below.
from ..models import NegotiationAction
# Import same_instant from ..v2v_claim_bus for the operations below.
from ..v2v_claim_bus import same_instant
# Import ClaimAgreementRecord, ClaimRelinquishmentProposal, ClaimRelinquishmentResponse,
# NegotiatedPrecedenceOverlay, ProposalResponse, JointNegotiationProtocolSnapshot,... from .message_models for the
# operations below.
from .message_models import (
    ClaimAgreementRecord, ClaimRelinquishmentProposal,
    ClaimRelinquishmentResponse, NegotiatedPrecedenceOverlay, ProposalResponse,
    JointNegotiationProtocolSnapshot, ProtocolEvaluation, ProtocolState,
)


# Set RESPONSE_POLICY_STATUS to the text 'RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION'.
RESPONSE_POLICY_STATUS = "RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION"


# A categorical semantic failure, never a score or penalty.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ProtocolSemanticError(ValueError):
    """A categorical semantic failure, never a score or penalty."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Stable semantic identity; no randomness, counter, or hash.
# Input timestamp: the supplied timestamp.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Input sender: the supplied sender.
# Input receiver: the supplied receiver.
# Output: a tuple containing a floating-point number built from timestamp, yielding, priority, sender, receiver.
def deterministic_proposal_id(timestamp, yielding, priority, sender, receiver):
    """Stable semantic identity; no randomness, counter, or hash."""
    # Return a tuple containing a floating-point number built from timestamp, yielding, priority, sender, receiver
    # to the caller.
    return (float(timestamp), yielding, priority, sender, receiver)


# Validate proposal/response evidence without mutating regulatory truth.
# Instances expose the attributes and methods implemented in this class.
class ClaimRelinquishmentProtocol:
    """Validate proposal/response evidence without mutating regulatory truth."""

    # Set BLOCKED_AUTHORITY to an immutable set built from a set containing the text 'SOURCE_SNAPSHOT_MISMATCH',
    # the text 'REGULATORY_PROFILE_MISMATCH', the text...
    BLOCKED_AUTHORITY = frozenset({
        "SOURCE_SNAPSHOT_MISMATCH", "REGULATORY_PROFILE_MISMATCH",
        "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "REGULATORY_INPUT_UNRESOLVED",
        "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED",
    })

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Create proposal using the inputs and processing steps below.
    # Input claim: the supplied claim.
    # Input source_negotiation_timestamp: the supplied source negotiation timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input policy_authority: the supplied policy authority.
    # Output: the result of ClaimRelinquishmentProposal(proposal_id, claim.ego_id, claim.counterparty_id,
    # claim.yielding_vehicle_id,...).
    # Processing: select branches using the stated conditions.
    def create_proposal(claim, source_negotiation_timestamp,
                        # Declare regulatory_profile, policy_authority as input parameters.
                        regulatory_profile, policy_authority):
        # Run this branch when the negation of whether claim has type PrecedenceClaim.
        if not isinstance(claim, PrecedenceClaim):
            # Raise ProtocolSemanticError with the text 'SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM' to stop this
            # execution path.
            raise ProtocolSemanticError("SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        # Run this branch when claim.ego_id differs from claim.priority_vehicle_id.
        if claim.ego_id != claim.priority_vehicle_id:
            # Raise ProtocolSemanticError with the text 'SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM' to stop this
            # execution path.
            raise ProtocolSemanticError("SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        # Run this branch when claim.counterparty_id differs from claim.yielding_vehicle_id.
        if claim.counterparty_id != claim.yielding_vehicle_id:
            # Raise ProtocolSemanticError with the text 'INVALID_COUNTERPARTY' to stop this execution path.
            raise ProtocolSemanticError("INVALID_COUNTERPARTY")
        # Run this branch when policy_authority is a different object from PolicyAuthority.POLICY_AUTHORIZED.
        if policy_authority is not PolicyAuthority.POLICY_AUTHORIZED:
            # Raise ProtocolSemanticError with the text 'PROTOCOL_BLOCKED' to stop this execution path.
            raise ProtocolSemanticError("PROTOCOL_BLOCKED")
        # Set proposal_id to the result of deterministic_proposal_id(source_negotiation_timestamp,
        # claim.yielding_vehicle_id, claim.priority_vehicle_id,...).
        proposal_id = deterministic_proposal_id(
            # Supply source_negotiation_timestamp to deterministic_proposal_id.
            source_negotiation_timestamp, claim.yielding_vehicle_id,
            # Supply claim.priority_vehicle_id to deterministic_proposal_id.
            claim.priority_vehicle_id, claim.ego_id, claim.counterparty_id,
        )
        # Return the result of ClaimRelinquishmentProposal(proposal_id, claim.ego_id, claim.counterparty_id,
        # claim.yielding_vehicle_id,...) to the caller.
        return ClaimRelinquishmentProposal(
            # Supply claim.counterparty_id to ClaimRelinquishmentProposal.
            proposal_id, claim.ego_id, claim.counterparty_id,
            # Supply claim.yielding_vehicle_id to ClaimRelinquishmentProposal.
            claim.yielding_vehicle_id, claim.priority_vehicle_id,
            # Supply NegotiationAction.RELINQUISH_CLAIM to ClaimRelinquishmentProposal.
            NegotiationAction.RELINQUISH_CLAIM,
            # Supply a floating-point number built from source_negotiation_timestamp to
            # ClaimRelinquishmentProposal.
            float(source_negotiation_timestamp), claim.source_snapshot_timestamp,
            # Supply claim.applicable_rule_ids to ClaimRelinquishmentProposal.
            regulatory_profile, claim.applicable_rule_ids, claim.source_sections,
            # Supply claim.shared_conflict_zone_ids to ClaimRelinquishmentProposal.
            claim.shared_conflict_zone_ids,
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Create response using the inputs and processing steps below.
    # Input proposal: the supplied proposal.
    # Input responder_id: the supplied responder id.
    # Input response: the supplied response.
    # Input source_negotiation_timestamp: the supplied source negotiation timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Output: the result of ClaimRelinquishmentResponse(proposal.proposal_id, responder_id, proposal.sender_id,
    # response, a floating-point number built...).
    # Processing: select branches using the stated conditions.
    def create_response(proposal, responder_id, response,
                        # Declare source_negotiation_timestamp, regulatory_profile as input parameters.
                        source_negotiation_timestamp, regulatory_profile):
        # Run this branch when responder_id differs from proposal.receiver_id.
        if responder_id != proposal.receiver_id:
            # Raise ProtocolSemanticError with the text 'INVALID_COUNTERPARTY' to stop this execution path.
            raise ProtocolSemanticError("INVALID_COUNTERPARTY")
        # Set response to response when whether response has type ProposalResponse, otherwise the result of
        # ProposalResponse(response).
        response = response if isinstance(response, ProposalResponse) else ProposalResponse(response)
        # Return the result of ClaimRelinquishmentResponse(proposal.proposal_id, responder_id, proposal.sender_id,
        # response, a floating-point number built...) to the caller.
        return ClaimRelinquishmentResponse(
            # Supply proposal.proposal_id to ClaimRelinquishmentResponse.
            proposal.proposal_id, responder_id, proposal.sender_id, response,
            # Supply a floating-point number built from source_negotiation_timestamp to
            # ClaimRelinquishmentResponse.
            float(source_negotiation_timestamp), regulatory_profile,
        )

    # Evaluate using the inputs and processing steps below.
    # Input original_edges: the supplied original edges.
    # Input messages: the supplied messages.
    # Input current_timestamp: the supplied current timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input policy_authorized: the supplied policy authorized.
    # Input source_consistent: the supplied source consistent.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def evaluate(self, original_edges, messages, current_timestamp,
                 # Declare regulatory_profile, policy_authorized as input parameters.
                 regulatory_profile, policy_authorized=True,
                 # Declare source_consistent as input parameter.
                 source_consistent=True):
        # Set original to a tuple built from the sorted values from a set of a tuple containing
        # edge['yielding_vehicle_id'], edge['priority_vehicle_id'] for edge in original_edges.
        original = tuple(sorted({
            # Evaluate a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id' as part of
            # the enclosing expression.
            (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            # Evaluate original_edges as part of the enclosing expression.
            for edge in original_edges
        }))
        # Set proposals to a set of message for message in messages; retain entries satisfying whether message has
        # type ClaimRelinquishmentProposal.
        proposals = {message for message in messages
                     # Evaluate whether message has type ClaimRelinquishmentProposal as part of the enclosing
                     # expression.
                     if isinstance(message, ClaimRelinquishmentProposal)}
        # Set responses to a set of message for message in messages; retain entries satisfying whether message has
        # type ClaimRelinquishmentResponse.
        responses = {message for message in messages
                     # Evaluate whether message has type ClaimRelinquishmentResponse as part of the enclosing
                     # expression.
                     if isinstance(message, ClaimRelinquishmentResponse)}
        # Run this branch when the negation of proposals.
        if not proposals:
            # Return the result of self._result(ProtocolState.NO_PROPOSAL, original) to the caller.
            return self._result(ProtocolState.NO_PROPOSAL, original)
        # Run this branch when the number of entries in proposals differs from 1.
        if len(proposals) != 1:
            # Return the result of self._result(ProtocolState.PROTOCOL_DISAGREEMENT, original) to the caller.
            return self._result(ProtocolState.PROTOCOL_DISAGREEMENT, original,
                                # Supply diagnostic as the text 'PROTOCOL_DISAGREEMENT'.
                                diagnostic="PROTOCOL_DISAGREEMENT")
        # Set proposal to the next item from the result of iter(proposals).
        proposal = next(iter(proposals))
        # Set claim to a tuple containing proposal.yielding_vehicle_id, proposal.priority_vehicle_id.
        claim = (proposal.yielding_vehicle_id, proposal.priority_vehicle_id)
        # Set matching_edges to a tuple built from a lazy sequence of edge for edge in original_edges; retain
        # entries satisfying a tuple containing edge['yielding_vehicle_id'], edge['priority_vehicle_id'] equals
        # claim.
        matching_edges = tuple(edge for edge in original_edges if (
            # Include edge at 'yielding_vehicle_id' in this tuple.
            edge["yielding_vehicle_id"], edge["priority_vehicle_id"]
        # Evaluate claim as part of the enclosing expression.
        ) == claim)
        # Set base to a dictionary built from the supplied values.
        base = dict(original=original, proposal=proposal, claim=claim)
        # Set expected_id to the result of deterministic_proposal_id(proposal.source_negotiation_timestamp, the
        # unpacked values from claim, proposal.sender_id,...).
        expected_id = deterministic_proposal_id(
            # Supply proposal.source_negotiation_timestamp to deterministic_proposal_id.
            proposal.source_negotiation_timestamp, *claim,
            # Supply proposal.receiver_id to deterministic_proposal_id.
            proposal.sender_id, proposal.receiver_id,
        )
        # Run this branch when proposal.proposal_id differs from expected_id.
        if proposal.proposal_id != expected_id:
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'PROPOSAL_ID_MISMATCH'.
                                diagnostic="PROPOSAL_ID_MISMATCH")
        # Run this branch when proposal.sender_id differs from proposal.priority_vehicle_id.
        if proposal.sender_id != proposal.priority_vehicle_id:
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM'.
                                diagnostic="SENDER_DOES_NOT_OWN_PRECEDENCE_CLAIM")
        # Run this branch when proposal.receiver_id differs from proposal.yielding_vehicle_id.
        if proposal.receiver_id != proposal.yielding_vehicle_id:
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'INVALID_COUNTERPARTY'.
                                diagnostic="INVALID_COUNTERPARTY")
        # Run this branch when claim does not belong to original.
        if claim not in original:
            # Return the result of self._result(ProtocolState.SOURCE_CLAIM_INVALID) to the caller.
            return self._result(ProtocolState.SOURCE_CLAIM_INVALID, **base,
                                # Supply diagnostic as the text 'SOURCE_CLAIM_NO_LONGER_VALID'.
                                diagnostic="SOURCE_CLAIM_NO_LONGER_VALID")
        # Run this branch when proposal.source_claim_timestamp is the same object as None or the negation of
        # whether any item is true in a lazy sequence of same_instant(proposal.source_claim_timestamp,
        # edge.get('timestamp')) for edge in matching_edges.
        if (proposal.source_claim_timestamp is None or
                # Evaluate the negation of whether any item is true in a lazy sequence of the result of
                # same_instant(proposal.source_claim_timestamp, edge.get('timestamp')) for edge in matching_edges
                # as part of the enclosing expression.
                not any(same_instant(proposal.source_claim_timestamp,
                                     # Supply 'timestamp' from edge; use None if absent to same_instant.
                                     edge.get("timestamp"))
                        # Evaluate matching_edges as part of the enclosing expression.
                        for edge in matching_edges)):
            # Return the result of self._result(ProtocolState.SOURCE_CLAIM_INVALID) to the caller.
            return self._result(ProtocolState.SOURCE_CLAIM_INVALID, **base,
                                # Supply diagnostic as the text 'SOURCE_CLAIM_NO_LONGER_VALID'.
                                diagnostic="SOURCE_CLAIM_NO_LONGER_VALID")
        # Run this branch when the negation of source_consistent or the negation of policy_authorized or
        # proposal.proposed_action is a different object from NegotiationAction.RELINQUISH_CLAIM.
        if (not source_consistent or not policy_authorized or
                # Evaluate proposal.proposed_action is a different object from NegotiationAction.RELINQUISH_CLAIM
                # as part of the enclosing expression.
                proposal.proposed_action is not NegotiationAction.RELINQUISH_CLAIM):
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'PROTOCOL_BLOCKED'.
                                diagnostic="PROTOCOL_BLOCKED")
        # Run this branch when proposal.regulatory_profile differs from regulatory_profile or the negation of the
        # result of same_instant(proposal.source_negotiation_timestamp, current_timestamp).
        if (proposal.regulatory_profile != regulatory_profile or
                # Evaluate the negation of the result of same_instant(proposal.source_negotiation_timestamp,
                # current_timestamp) as part of the enclosing expression.
                not same_instant(proposal.source_negotiation_timestamp,
                                 # Supply current_timestamp to same_instant.
                                 current_timestamp)):
            # Set diagnostic to the text 'AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH' when
            # proposal.regulatory_profile differs from regulatory_profile, otherwise the text
            # 'SOURCE_SNAPSHOT_MISMATCH'.
            diagnostic = ("AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH"
                          # Evaluate proposal.regulatory_profile differs from regulatory_profile as part of the
                          # enclosing expression.
                          if proposal.regulatory_profile != regulatory_profile
                          # Supply the text 'SOURCE_SNAPSHOT_MISMATCH' to the enclosing expression.
                          else "SOURCE_SNAPSHOT_MISMATCH")
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as diagnostic.
                                diagnostic=diagnostic)
        # Set relevant to a tuple built from a lazy sequence of response for response in responses; retain entries
        # satisfying response.proposal_id equals proposal.proposal_id.
        relevant = tuple(response for response in responses
                         # Evaluate response.proposal_id equals proposal.proposal_id as part of the enclosing
                         # expression.
                         if response.proposal_id == proposal.proposal_id)
        # Run this branch when responses and the negation of relevant.
        if responses and not relevant:
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'RESPONSE_PROPOSAL_MISMATCH'.
                                diagnostic="RESPONSE_PROPOSAL_MISMATCH")
        # Run this branch when the negation of relevant.
        if not relevant:
            # Return the result of self._result(ProtocolState.PROPOSAL_PENDING) to the caller.
            return self._result(ProtocolState.PROPOSAL_PENDING, **base)
        # Set response_types to a set of item.response for item in relevant.
        response_types = {item.response for item in relevant}
        # Run this branch when the number of entries in response_types differs from 1.
        if len(response_types) != 1:
            # Return the result of self._result(ProtocolState.PROTOCOL_DISAGREEMENT) to the caller.
            return self._result(ProtocolState.PROTOCOL_DISAGREEMENT, **base,
                                # Supply diagnostic as the text 'PROTOCOL_DISAGREEMENT'.
                                diagnostic="PROTOCOL_DISAGREEMENT")
        # Set response to sorted(relevant, key=lambda item: (item.sender_id, item.receiver_id,
        # item.response.value)) at 0.
        response = sorted(relevant, key=lambda item: (
            # Include item.response.value in this tuple.
            item.sender_id, item.receiver_id, item.response.value,
        # Supply 0 to the enclosing expression.
        ))[0]
        # Run this branch when response.sender_id differs from proposal.receiver_id or response.receiver_id
        # differs from proposal.sender_id.
        if (response.sender_id != proposal.receiver_id or
                # Evaluate response.receiver_id differs from proposal.sender_id as part of the enclosing
                # expression.
                response.receiver_id != proposal.sender_id):
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'INVALID_COUNTERPARTY'.
                                diagnostic="INVALID_COUNTERPARTY")
        # Run this branch when response.regulatory_profile differs from proposal.regulatory_profile.
        if response.regulatory_profile != proposal.regulatory_profile:
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH'.
                                diagnostic="AGREEMENT_BLOCKED_REGULATORY_PROFILE_MISMATCH")
        # Run this branch when the negation of the result of same_instant(current_timestamp,
        # proposal.source_negotiation_timestamp, response.source_negotiation_timestamp).
        if not same_instant(
                # Supply proposal.source_negotiation_timestamp to same_instant.
                current_timestamp, proposal.source_negotiation_timestamp,
                # Supply response.source_negotiation_timestamp to same_instant.
                response.source_negotiation_timestamp):
            # Return the result of self._result(ProtocolState.PROTOCOL_BLOCKED) to the caller.
            return self._result(ProtocolState.PROTOCOL_BLOCKED, **base,
                                # Supply diagnostic as the text 'SOURCE_SNAPSHOT_MISMATCH'.
                                diagnostic="SOURCE_SNAPSHOT_MISMATCH")
        # Run this branch when response.response is the same object as ProposalResponse.REJECT.
        if response.response is ProposalResponse.REJECT:
            # Return the result of self._result(ProtocolState.PROPOSAL_REJECTED) to the caller.
            return self._result(ProtocolState.PROPOSAL_REJECTED, **base,
                                # Supply response as response.
                                response=response)
        # Set agreement to the result of ClaimAgreementRecord(proposal.proposal_id, the unpacked values from
        # claim, proposal.sender_id, proposal.receiver_id,...).
        agreement = ClaimAgreementRecord(
            # Supply proposal.proposal_id to ClaimAgreementRecord.
            proposal.proposal_id, *claim, proposal.sender_id,
            # Supply proposal.receiver_id to ClaimAgreementRecord.
            proposal.receiver_id, response.sender_id, response.response,
            # Supply proposal.applicable_rule_ids to ClaimAgreementRecord.
            proposal.applicable_rule_ids, proposal.source_sections,
            # Supply proposal.source_negotiation_timestamp to ClaimAgreementRecord.
            proposal.regulatory_profile, proposal.source_negotiation_timestamp,
            # Supply proposal.source_claim_timestamp to ClaimAgreementRecord.
            proposal.source_claim_timestamp,
        )
        # Return the result of self._result(ProtocolState.AGREEMENT_ESTABLISHED) to the caller.
        return self._result(ProtocolState.AGREEMENT_ESTABLISHED, **base,
                            # Supply response as response.
                            # Supply agreement as agreement.
                            response=response, agreement=agreement)

    # Evaluate each deterministic proposal identity independently.
    # Input original_edges: the supplied original edges.
    # Input messages: the supplied messages.
    # Input current_timestamp: the supplied current timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input policy_authorized: the supplied policy authorized.
    # Input source_consistent: the supplied source consistent.
    # Output: the result of JointNegotiationProtocolSnapshot(a floating-point number built from current_timestamp,
    # regulatory_profile, the text...).
    # Processing: iterate over the relevant records.
    def evaluate_all_claims(self, original_edges, messages, current_timestamp,
                            # Declare regulatory_profile, policy_authorized as input parameters.
                            regulatory_profile, policy_authorized=True,
                            # Declare source_consistent as input parameter.
                            source_consistent=True):
        """Evaluate each deterministic proposal identity independently."""
        # Set original to a tuple built from the sorted values from a set of a tuple containing
        # edge['yielding_vehicle_id'], edge['priority_vehicle_id'] for edge in original_edges.
        original = tuple(sorted({
            # Evaluate a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id' as part of
            # the enclosing expression.
            (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            # Evaluate original_edges as part of the enclosing expression.
            for edge in original_edges
        }))
        # Set proposals to a tuple built from the sorted values from a set of item for item in messages; retain
        # entries satisfying whether item has type ClaimRelinquishmentProposal.
        proposals = tuple(sorted({
            # Evaluate messages as part of the enclosing expression.
            item for item in messages
            # Evaluate whether item has type ClaimRelinquishmentProposal as part of the enclosing expression.
            if isinstance(item, ClaimRelinquishmentProposal)
        # Declare item as input parameter.
        }, key=lambda item: item.proposal_id))
        # Set responses to a tuple built from a lazy sequence of item for item in messages; retain entries
        # satisfying whether item has type ClaimRelinquishmentResponse.
        responses = tuple(item for item in messages
                          # Evaluate whether item has type ClaimRelinquishmentResponse as part of the enclosing
                          # expression.
                          if isinstance(item, ClaimRelinquishmentResponse))
        # Set evaluations to an empty list.
        evaluations = []
        # Set known_ids to a set of item.proposal_id for item in proposals.
        known_ids = {item.proposal_id for item in proposals}
        # Iterate over proposals, binding each item to proposal.
        for proposal in proposals:
            # Set group to a tuple containing proposal plus a tuple built from a lazy sequence of item for item in
            # responses; retain entries satisfying item.proposal_id equals proposal.proposal_id.
            group = (proposal,) + tuple(
                # Evaluate responses as part of the enclosing expression.
                item for item in responses
                # Evaluate item.proposal_id equals proposal.proposal_id as part of the enclosing expression.
                if item.proposal_id == proposal.proposal_id
            )
            # Append the result of self.evaluate(original_edges, group, current_timestamp, regulatory_profile,
            # policy_authorized, source_consistent) to evaluations.
            evaluations.append(self.evaluate(
                # Supply regulatory_profile to self.evaluate.
                original_edges, group, current_timestamp, regulatory_profile,
                # Supply policy_authorized to self.evaluate.
                policy_authorized, source_consistent,
            ))
        # Preserve orphan response evidence as a local blocked item. ProposalId
        # contains the claim endpoints, so it remains traceable without voting
        # or contaminating a different valid negotiation.
        # Iterate over the sorted values from a set of item.proposal_id for item in responses; retain entries
        # satisfying item.proposal_id does not belong to known_ids, binding each item to proposal_id.
        for proposal_id in sorted({item.proposal_id for item in responses
                                   # Evaluate item.proposal_id does not belong to known_ids as part of the
                                   # enclosing expression.
                                   if item.proposal_id not in known_ids}):
            # Set claim to a tuple containing proposal_id at 1, proposal_id at 2.
            claim = (proposal_id[1], proposal_id[2])
            # Append the result of self._result(ProtocolState.PROTOCOL_BLOCKED, original) to evaluations.
            evaluations.append(self._result(
                # Supply claim as claim.
                ProtocolState.PROTOCOL_BLOCKED, original, claim=claim,
                # Supply diagnostic as the text 'RESPONSE_PROPOSAL_MISMATCH'.
                diagnostic="RESPONSE_PROPOSAL_MISMATCH",
            ))
        # Call evaluations.sort with the supplied arguments.
        evaluations.sort(key=lambda item: (
            # Include item.negotiated_agreement_overlay.original_claim in this tuple.
            item.negotiated_agreement_overlay.original_claim,
            # Include item.negotiated_agreement_overlay.proposal.proposal_id when
            # item.negotiated_agreement_overlay.proposal, otherwise an empty tuple in this tuple.
            item.negotiated_agreement_overlay.proposal.proposal_id
            # Evaluate item.negotiated_agreement_overlay.proposal as part of the enclosing expression.
            if item.negotiated_agreement_overlay.proposal else (),
        ))
        # Set evaluations to a tuple built from evaluations.
        evaluations = tuple(evaluations)
        # Set completed to a tuple built from a lazy sequence of item.negotiated_agreement_overlay.agreement for
        # item in evaluations; retain entries satisfying item.agreement_complete.
        completed = tuple(
            # Evaluate item.negotiated_agreement_overlay.agreement as part of the enclosing expression.
            item.negotiated_agreement_overlay.agreement for item in evaluations
            # Evaluate item.agreement_complete as part of the enclosing expression.
            if item.agreement_complete
        )
        # Set pending to a tuple built from a lazy sequence of item.negotiated_agreement_overlay.proposal for item
        # in evaluations; retain entries satisfying item.state is the same object as
        # ProtocolState.PROPOSAL_PENDING.
        pending = tuple(
            # Evaluate item.negotiated_agreement_overlay.proposal as part of the enclosing expression.
            item.negotiated_agreement_overlay.proposal for item in evaluations
            # Evaluate item.state is the same object as ProtocolState.PROPOSAL_PENDING as part of the enclosing
            # expression.
            if item.state is ProtocolState.PROPOSAL_PENDING
        )
        # Set rejected to a tuple built from a lazy sequence of item.negotiated_agreement_overlay.proposal for
        # item in evaluations; retain entries satisfying item.state is the same object as
        # ProtocolState.PROPOSAL_REJECTED.
        rejected = tuple(
            # Evaluate item.negotiated_agreement_overlay.proposal as part of the enclosing expression.
            item.negotiated_agreement_overlay.proposal for item in evaluations
            # Evaluate item.state is the same object as ProtocolState.PROPOSAL_REJECTED as part of the enclosing
            # expression.
            if item.state is ProtocolState.PROPOSAL_REJECTED
        )
        # Set blocked to a tuple built from a lazy sequence of item for item in evaluations; retain entries
        # satisfying item.state belongs to a set containing ProtocolState.PROTOCOL_BLOCKED,...
        blocked = tuple(item for item in evaluations if item.state in {
            # Include ProtocolState.SOURCE_CLAIM_INVALID in this set.
            ProtocolState.PROTOCOL_BLOCKED, ProtocolState.SOURCE_CLAIM_INVALID,
        })
        # Set disagreements to a tuple built from a lazy sequence of item for item in evaluations; retain entries
        # satisfying item.state is the same object as ProtocolState.PROTOCOL_DISAGREEMENT.
        disagreements = tuple(item for item in evaluations
                              # Evaluate item.state is the same object as ProtocolState.PROTOCOL_DISAGREEMENT as
                              # part of the enclosing expression.
                              if item.state is ProtocolState.PROTOCOL_DISAGREEMENT)
        # Set agreed_claims to a set of item.negotiated_agreement_overlay.original_claim for item in evaluations;
        # retain entries satisfying item.agreement_complete.
        agreed_claims = {
            # Evaluate item.negotiated_agreement_overlay.original_claim as part of the enclosing expression.
            item.negotiated_agreement_overlay.original_claim
            # Evaluate item.agreement_complete as part of the enclosing expression.
            for item in evaluations if item.agreement_complete
        }
        # Set effective to a tuple built from a lazy sequence of edge for edge in original; retain entries
        # satisfying edge does not belong to agreed_claims.
        effective = tuple(edge for edge in original if edge not in agreed_claims)
        # Return the result of JointNegotiationProtocolSnapshot(a floating-point number built from
        # current_timestamp, regulatory_profile, the text...) to the caller.
        return JointNegotiationProtocolSnapshot(
            # Supply a floating-point number built from current_timestamp to JointNegotiationProtocolSnapshot.
            float(current_timestamp), regulatory_profile,
            # Supply evaluations to JointNegotiationProtocolSnapshot.
            "IDEAL_SAME_STEP_V2V", original, evaluations, completed, pending,
            # Supply disagreements to JointNegotiationProtocolSnapshot.
            rejected, blocked, disagreements,
            # Supply a tuple built from a lazy sequence of item.negotiated_agreement_overlay for item in
            # evaluations to JointNegotiationProtocolSnapshot.
            tuple(item.negotiated_agreement_overlay for item in evaluations),
            # Supply effective to JointNegotiationProtocolSnapshot.
            effective,
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Result using the inputs and processing steps below.
    # Input state: the state read or updated by this operation.
    # Input original: the supplied original.
    # Input proposal: the supplied proposal.
    # Input response: the supplied response.
    # Input agreement: the supplied agreement.
    # Input claim: the supplied claim.
    # Input diagnostic: the supplied diagnostic.
    # Output: the result of ProtocolEvaluation(state, complete, original, effective, overlay).
    def _result(state, original, proposal=None, response=None, agreement=None,
                # Declare claim, diagnostic as input parameters.
                claim=None, diagnostic=None):
        # Set claim to claim or a tuple containing proposal.yielding_vehicle_id, proposal.priority_vehicle_id when
        # proposal, otherwise a tuple containing the text '', the text ''.
        claim = claim or ((proposal.yielding_vehicle_id,
                           # Include proposal.priority_vehicle_id in this tuple.
                           proposal.priority_vehicle_id) if proposal else ("", ""))
        # Set complete to state is the same object as ProtocolState.AGREEMENT_ESTABLISHED.
        complete = state is ProtocolState.AGREEMENT_ESTABLISHED
        # Set effective to a tuple built from a lazy sequence of edge for edge in original; retain entries
        # satisfying the negation of complete and edge == claim.
        effective = tuple(edge for edge in original if not (complete and edge == claim))
        # Set overlay to the result of NegotiatedPrecedenceOverlay(claim, state, the text
        # 'CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT' when complete, otherwise...).
        overlay = NegotiatedPrecedenceOverlay(
            # Supply claim to NegotiatedPrecedenceOverlay.
            claim, state,
            # Supply the text 'CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT' when complete, otherwise None to
            # NegotiatedPrecedenceOverlay.
            "CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT" if complete else None,
            # Supply agreement to NegotiatedPrecedenceOverlay.
            proposal, response, agreement,
            # Supply a tuple containing claim at 1, claim at 0 when claim differs from a tuple containing the text
            # '', the text '', otherwise a tuple containing the text '', the text '' to
            # NegotiatedPrecedenceOverlay.
            (claim[1], claim[0]) if claim != ("", "") else ("", ""),
            # Supply proposal.regulatory_profile when proposal, otherwise None to NegotiatedPrecedenceOverlay.
            proposal.regulatory_profile if proposal else None,
            # Supply proposal.source_negotiation_timestamp when proposal, otherwise None to
            # NegotiatedPrecedenceOverlay.
            proposal.source_negotiation_timestamp if proposal else None,
            # Supply diagnostic to NegotiatedPrecedenceOverlay.
            diagnostic,
        )
        # Return the result of ProtocolEvaluation(state, complete, original, effective, overlay) to the caller.
        return ProtocolEvaluation(state, complete, original, effective, overlay)


# Agreement complete using the inputs and processing steps below.
# Input evaluation: the supplied evaluation.
# Output: evaluation.state is the same object as ProtocolState.AGREEMENT_ESTABLISHED and
# evaluation.agreement_complete and evaluation.negotiated_agreement_overlay.agreement is a different object...
def agreement_complete(evaluation):
    # Return evaluation.state is the same object as ProtocolState.AGREEMENT_ESTABLISHED and
    # evaluation.agreement_complete and evaluation.negotiated_agreement_overlay.agreement is a different object
    # from None to the caller.
    return (evaluation.state is ProtocolState.AGREEMENT_ESTABLISHED and
            # Evaluate evaluation.agreement_complete as part of the enclosing expression.
            evaluation.agreement_complete and
            # Evaluate evaluation.negotiated_agreement_overlay.agreement is a different object from None as part
            # of the enclosing expression.
            evaluation.negotiated_agreement_overlay.agreement is not None)
