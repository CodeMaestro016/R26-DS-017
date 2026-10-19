"""Causal action-consequence and transition lifecycle tracking."""

from dataclasses import replace

from ..claim_semantics import PolicyAuthority
from ..models import NegotiationAction
from ..protocol import NegotiationResponseAction
from ..protocol.message_models import ProposalResponse, ProtocolState
from .models import (
    ContinuationClassification, ImmediateConsequenceType,
    NegotiationActionConsequence, NegotiationTransition, TransitionStatus,
)


class TransitionSemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


PROTOCOL_RESOLUTION = {
    ProtocolState.AGREEMENT_ESTABLISHED: TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED,
    ProtocolState.PROPOSAL_REJECTED: TransitionStatus.RESOLVED_PROPOSAL_REJECTED,
    ProtocolState.SOURCE_CLAIM_INVALID: TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID,
    ProtocolState.PROTOCOL_BLOCKED: TransitionStatus.RESOLVED_PROTOCOL_BLOCKED,
    ProtocolState.PROTOCOL_DISAGREEMENT: TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT,
}


class NegotiationTransitionTracker:
    def __init__(self, protocol):
        self.protocol = protocol
        self.transitions = {}
        self.proposal_to_proposer = {}
        self.proposal_to_responder = {}

    def open_transition(self, epoch, action, actor_snapshot,
                        behavior_policy_log_probability=None,
                        critic_snapshot=None, critic_value_at_collection=None):
        transition_id = ("TRANSITION", epoch.decision_event_id)
        if transition_id in self.transitions:
            raise TransitionSemanticError("DUPLICATE_TRANSITION")
        item = NegotiationTransition(
            transition_id, epoch.decision_event_id, epoch.parent_decision_event_id,
            epoch.ego_id, epoch.decision_role, epoch.claim_identity,
            epoch.proposal_id, epoch.decision_timestamp,
            epoch.decision_epoch_reason, action, None, TransitionStatus.OPEN,
            None, None, None, actor_snapshot, behavior_policy_log_probability,
            critic_snapshot, critic_value_at_collection, None, None,
            ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES,
        )
        self.transitions[transition_id] = item
        return item

    def apply_action(self, transition_id, timestamp, *, claim=None, proposal=None,
                     regulatory_profile=None):
        item = self.transitions[transition_id]
        action = item.semantic_action
        message = None
        if action == NegotiationAction.KEEP_CLAIM.value:
            kind = ImmediateConsequenceType.CLAIM_RETAINED
        elif action == NegotiationAction.RELINQUISH_CLAIM.value:
            if claim is None:
                raise TransitionSemanticError("SOURCE_CLAIM_REQUIRED")
            message = self.protocol.create_proposal(
                claim, timestamp, regulatory_profile, PolicyAuthority.POLICY_AUTHORIZED
            )
            kind = ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED
        elif action in {NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
                        NegotiationResponseAction.REJECT_RELINQUISHMENT.value}:
            if proposal is None or proposal.proposal_id != item.proposal_id:
                raise TransitionSemanticError("EXACT_PROPOSAL_REQUIRED")
            response = (ProposalResponse.ACCEPT if action.endswith("ACCEPT_RELINQUISHMENT")
                        else ProposalResponse.REJECT)
            message = self.protocol.create_response(
                proposal, item.ego_id, response, timestamp, regulatory_profile
            )
            kind = (ImmediateConsequenceType.RELINQUISHMENT_ACCEPT_RESPONSE_CREATED
                    if response is ProposalResponse.ACCEPT else
                    ImmediateConsequenceType.RELINQUISHMENT_REJECT_RESPONSE_CREATED)
        else:
            raise TransitionSemanticError("UNSUPPORTED_SEMANTIC_ACTION")
        consequence = NegotiationActionConsequence(
            item.decision_event_id, action, item.claim_identity,
            getattr(message, "proposal_id", item.proposal_id), kind,
            float(timestamp), message, {"authority": "DETERMINISTIC_PROTOCOL"},
        )
        status = (TransitionStatus.RESOLVED_CLAIM_RETAINED
                  if kind is ImmediateConsequenceType.CLAIM_RETAINED else
                  TransitionStatus.WAITING_FOR_PROTOCOL_RESPONSE)
        updated = replace(item, proposal_id=consequence.proposal_id,
                          immediate_action_consequence=consequence,
                          transition_status=status)
        self.transitions[transition_id] = updated
        if kind is ImmediateConsequenceType.CLAIM_RETAINED:
            return self.resolve_transition(transition_id, status, timestamp,
                                           "CLAIM_RETAINED")
        if kind is ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED:
            self.associate_proposal(consequence.proposal_id, item.decision_event_id)
        return updated

    def associate_proposal(self, proposal_id, proposer_event_id):
        prior = self.proposal_to_proposer.get(proposal_id)
        if prior is not None and prior != proposer_event_id:
            raise TransitionSemanticError("PROPOSAL_CAUSAL_LINK_CONFLICT")
        self.proposal_to_proposer[proposal_id] = proposer_event_id

    def associate_responder_decision(self, proposal_id, responder_event_id):
        if proposal_id not in self.proposal_to_proposer:
            raise TransitionSemanticError("PROPOSER_CAUSAL_LINK_NOT_FOUND")
        prior = self.proposal_to_responder.get(proposal_id)
        if prior is not None and prior != responder_event_id:
            raise TransitionSemanticError("RESPONDER_CAUSAL_LINK_CONFLICT")
        self.proposal_to_responder[proposal_id] = responder_event_id
        return self.proposal_to_proposer[proposal_id]

    def observe_protocol_evaluation(self, proposal_id, evaluation, timestamp):
        if evaluation.state not in PROTOCOL_RESOLUTION:
            return ()
        affected = []
        event_ids = {self.proposal_to_proposer.get(proposal_id),
                     self.proposal_to_responder.get(proposal_id)} - {None}
        for transition_id, item in tuple(self.transitions.items()):
            if item.decision_event_id in event_ids:
                affected.append(self.resolve_transition(
                    transition_id, PROTOCOL_RESOLUTION[evaluation.state], timestamp,
                    evaluation.state.value,
                ))
        return tuple(affected)

    def resolve_transition(self, transition_id, status, timestamp, reason,
                           successor_snapshot=None, successor_state=None):
        item = self.transitions[transition_id]
        if item.resolution_timestamp is not None:
            raise TransitionSemanticError("DUPLICATE_TRANSITION_RESOLUTION")
        elapsed = float(timestamp) - item.decision_timestamp
        if elapsed < 0:
            raise TransitionSemanticError("NEGATIVE_TRANSITION_DURATION")
        updated = replace(
            item, transition_status=status, resolution_reason=reason,
            resolution_timestamp=float(timestamp), elapsed_seconds=elapsed,
            successor_actor_observation_snapshot=successor_snapshot,
            successor_semantic_state=successor_state,
            continuation_classification=(
                ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES
                if successor_snapshot is not None else
                ContinuationClassification.NEGOTIATION_SUBJECT_RESOLVED),
        )
        self.transitions[transition_id] = updated
        return updated
