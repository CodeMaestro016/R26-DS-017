"""Causal action-consequence and transition lifecycle tracking."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import PolicyAuthority from ..claim_semantics for the operations below.
from ..claim_semantics import PolicyAuthority
# Import NegotiationAction from ..models for the operations below.
from ..models import NegotiationAction
# Import NegotiationResponseAction from ..protocol for the operations below.
from ..protocol import NegotiationResponseAction
# Import ProposalResponse, ProtocolState from ..protocol.message_models for the operations below.
from ..protocol.message_models import ProposalResponse, ProtocolState
# Import ContinuationClassification, ImmediateConsequenceType, NegotiationActionConsequence,
# NegotiationTransition, TransitionStatus from .models for the operations below.
from .models import (
    ContinuationClassification, ImmediateConsequenceType,
    NegotiationActionConsequence, NegotiationTransition, TransitionStatus,
)


# Define TransitionSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class TransitionSemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Set PROTOCOL_RESOLUTION to a dictionary of the supplied entries.
PROTOCOL_RESOLUTION = {
    # Store TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED under ProtocolState.AGREEMENT_ESTABLISHED.
    ProtocolState.AGREEMENT_ESTABLISHED: TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED,
    # Store TransitionStatus.RESOLVED_PROPOSAL_REJECTED under ProtocolState.PROPOSAL_REJECTED.
    ProtocolState.PROPOSAL_REJECTED: TransitionStatus.RESOLVED_PROPOSAL_REJECTED,
    # Store TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID under ProtocolState.SOURCE_CLAIM_INVALID.
    ProtocolState.SOURCE_CLAIM_INVALID: TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID,
    # Store TransitionStatus.RESOLVED_PROTOCOL_BLOCKED under ProtocolState.PROTOCOL_BLOCKED.
    ProtocolState.PROTOCOL_BLOCKED: TransitionStatus.RESOLVED_PROTOCOL_BLOCKED,
    # Store TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT under ProtocolState.PROTOCOL_DISAGREEMENT.
    ProtocolState.PROTOCOL_DISAGREEMENT: TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT,
}


# Define NegotiationTransitionTracker to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationTransitionTracker:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input protocol: the supplied protocol.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, protocol):
        # Set self.protocol to protocol.
        self.protocol = protocol
        # Set self.transitions to an empty dictionary.
        self.transitions = {}
        # Set self.proposal_to_proposer to an empty dictionary.
        self.proposal_to_proposer = {}
        # Set self.proposal_to_responder to an empty dictionary.
        self.proposal_to_responder = {}

    # Open transition using the inputs and processing steps below.
    # Input epoch: the supplied epoch.
    # Input action: the supplied action.
    # Input actor_snapshot: the supplied actor snapshot.
    # Input behavior_policy_log_probability: the supplied behavior policy log probability.
    # Input critic_snapshot: the supplied critic snapshot.
    # Input critic_value_at_collection: the supplied critic value at collection.
    # Output: item.
    # Processing: select branches using the stated conditions.
    def open_transition(self, epoch, action, actor_snapshot,
                        # Declare behavior_policy_log_probability as input parameter.
                        behavior_policy_log_probability=None,
                        # Declare critic_snapshot, critic_value_at_collection as input parameters.
                        critic_snapshot=None, critic_value_at_collection=None):
        # Set transition_id to a tuple containing the text 'TRANSITION', epoch.decision_event_id.
        transition_id = ("TRANSITION", epoch.decision_event_id)
        # Run this branch when transition_id belongs to self.transitions.
        if transition_id in self.transitions:
            # Raise TransitionSemanticError with the text 'DUPLICATE_TRANSITION' to stop this execution path.
            raise TransitionSemanticError("DUPLICATE_TRANSITION")
        # Set item to the result of NegotiationTransition(transition_id, epoch.decision_event_id,
        # epoch.parent_decision_event_id, epoch.ego_id,...).
        item = NegotiationTransition(
            # Supply epoch.parent_decision_event_id to NegotiationTransition.
            transition_id, epoch.decision_event_id, epoch.parent_decision_event_id,
            # Supply epoch.claim_identity to NegotiationTransition.
            epoch.ego_id, epoch.decision_role, epoch.claim_identity,
            # Supply epoch.decision_timestamp to NegotiationTransition.
            epoch.proposal_id, epoch.decision_timestamp,
            # Supply epoch.decision_epoch_reason to NegotiationTransition.
            epoch.decision_epoch_reason, action, None, TransitionStatus.OPEN,
            # Supply behavior_policy_log_probability to NegotiationTransition.
            None, None, None, actor_snapshot, behavior_policy_log_probability,
            # Supply critic_value_at_collection to NegotiationTransition.
            critic_snapshot, critic_value_at_collection, None, None,
            # Supply ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES to NegotiationTransition.
            ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES,
        )
        # Set self.transitions[transition_id] to item.
        self.transitions[transition_id] = item
        # Return item to the caller.
        return item

    # Apply action using the inputs and processing steps below.
    # Input transition_id: the supplied transition id.
    # Input timestamp: the supplied timestamp.
    # Input claim: the supplied claim.
    # Input proposal: the supplied proposal.
    # Input regulatory_profile: the supplied regulatory profile.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def apply_action(self, transition_id, timestamp, *, claim=None, proposal=None,
                     # Declare regulatory_profile as input parameter.
                     regulatory_profile=None):
        # Set item to self.transitions at transition_id.
        item = self.transitions[transition_id]
        # Set action to item.semantic_action.
        action = item.semantic_action
        # Set message to None.
        message = None
        # Run this branch when action equals NegotiationAction.KEEP_CLAIM.value.
        if action == NegotiationAction.KEEP_CLAIM.value:
            # Set kind to ImmediateConsequenceType.CLAIM_RETAINED.
            kind = ImmediateConsequenceType.CLAIM_RETAINED
        # Run this branch when action equals NegotiationAction.RELINQUISH_CLAIM.value.
        elif action == NegotiationAction.RELINQUISH_CLAIM.value:
            # Run this branch when claim is the same object as None.
            if claim is None:
                # Raise TransitionSemanticError with the text 'SOURCE_CLAIM_REQUIRED' to stop this execution path.
                raise TransitionSemanticError("SOURCE_CLAIM_REQUIRED")
            # Set message to the result of self.protocol.create_proposal(claim, timestamp, regulatory_profile,
            # PolicyAuthority.POLICY_AUTHORIZED).
            message = self.protocol.create_proposal(
                # Supply PolicyAuthority.POLICY_AUTHORIZED to self.protocol.create_proposal.
                claim, timestamp, regulatory_profile, PolicyAuthority.POLICY_AUTHORIZED
            )
            # Set kind to ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED.
            kind = ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED
        # Run this branch when action belongs to a set containing
        # NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
        # NegotiationResponseAction.REJECT_RELINQUISHMENT.value.
        elif action in {NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
                        # Include NegotiationResponseAction.REJECT_RELINQUISHMENT.value in this set.
                        NegotiationResponseAction.REJECT_RELINQUISHMENT.value}:
            # Run this branch when proposal is the same object as None or proposal.proposal_id differs from
            # item.proposal_id.
            if proposal is None or proposal.proposal_id != item.proposal_id:
                # Raise TransitionSemanticError with the text 'EXACT_PROPOSAL_REQUIRED' to stop this execution
                # path.
                raise TransitionSemanticError("EXACT_PROPOSAL_REQUIRED")
            # Set response to ProposalResponse.ACCEPT when the result of action.endswith(the text
            # 'ACCEPT_RELINQUISHMENT'), otherwise ProposalResponse.REJECT.
            response = (ProposalResponse.ACCEPT if action.endswith("ACCEPT_RELINQUISHMENT")
                        # Evaluate ProposalResponse.REJECT as part of the enclosing expression.
                        else ProposalResponse.REJECT)
            # Set message to the result of self.protocol.create_response(proposal, item.ego_id, response,
            # timestamp, regulatory_profile).
            message = self.protocol.create_response(
                # Supply regulatory_profile to self.protocol.create_response.
                proposal, item.ego_id, response, timestamp, regulatory_profile
            )
            # Set kind to ImmediateConsequenceType.RELINQUISHMENT_ACCEPT_RESPONSE_CREATED when response is the
            # same object as ProposalResponse.ACCEPT, otherwise
            # ImmediateConsequenceType.RELINQUISHMENT_REJECT_RESPONSE_CREATED.
            kind = (ImmediateConsequenceType.RELINQUISHMENT_ACCEPT_RESPONSE_CREATED
                    # Evaluate response is the same object as ProposalResponse.ACCEPT as part of the enclosing
                    # expression.
                    if response is ProposalResponse.ACCEPT else
                    # Evaluate ImmediateConsequenceType.RELINQUISHMENT_REJECT_RESPONSE_CREATED as part of the
                    # enclosing expression.
                    ImmediateConsequenceType.RELINQUISHMENT_REJECT_RESPONSE_CREATED)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Raise TransitionSemanticError with the text 'UNSUPPORTED_SEMANTIC_ACTION' to stop this execution
            # path.
            raise TransitionSemanticError("UNSUPPORTED_SEMANTIC_ACTION")
        # Set consequence to the result of NegotiationActionConsequence(item.decision_event_id, action,
        # item.claim_identity, the requested attribute of message, kind, a...).
        consequence = NegotiationActionConsequence(
            # Supply item.decision_event_id to NegotiationActionConsequence.
            item.decision_event_id, action, item.claim_identity,
            # Supply the requested attribute of message to NegotiationActionConsequence.
            getattr(message, "proposal_id", item.proposal_id), kind,
            # Store the text 'DETERMINISTIC_PROTOCOL' under 'authority'.
            float(timestamp), message, {"authority": "DETERMINISTIC_PROTOCOL"},
        )
        # Set status to TransitionStatus.RESOLVED_CLAIM_RETAINED when kind is the same object as
        # ImmediateConsequenceType.CLAIM_RETAINED, otherwise TransitionStatus.WAITING_FOR_PROTOCOL_RESPONSE.
        status = (TransitionStatus.RESOLVED_CLAIM_RETAINED
                  # Evaluate kind is the same object as ImmediateConsequenceType.CLAIM_RETAINED as part of the
                  # enclosing expression.
                  if kind is ImmediateConsequenceType.CLAIM_RETAINED else
                  # Evaluate TransitionStatus.WAITING_FOR_PROTOCOL_RESPONSE as part of the enclosing expression.
                  TransitionStatus.WAITING_FOR_PROTOCOL_RESPONSE)
        # Set updated to the result of replace(item).
        updated = replace(item, proposal_id=consequence.proposal_id,
                          # Supply immediate_action_consequence as consequence.
                          immediate_action_consequence=consequence,
                          # Supply transition_status as status.
                          transition_status=status)
        # Set self.transitions[transition_id] to updated.
        self.transitions[transition_id] = updated
        # Run this branch when kind is the same object as ImmediateConsequenceType.CLAIM_RETAINED.
        if kind is ImmediateConsequenceType.CLAIM_RETAINED:
            # Return the result of self.resolve_transition(transition_id, status, timestamp, the text
            # 'CLAIM_RETAINED') to the caller.
            return self.resolve_transition(transition_id, status, timestamp,
                                           "CLAIM_RETAINED")
        # Run this branch when kind is the same object as
        # ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED.
        if kind is ImmediateConsequenceType.RELINQUISHMENT_PROPOSAL_CREATED:
            # Call self.associate_proposal with the supplied arguments.
            self.associate_proposal(consequence.proposal_id, item.decision_event_id)
        # Return updated to the caller.
        return updated

    # Associate proposal using the inputs and processing steps below.
    # Input proposal_id: the supplied proposal id.
    # Input proposer_event_id: the supplied proposer event id.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def associate_proposal(self, proposal_id, proposer_event_id):
        # Set prior to proposal_id from self.proposal_to_proposer; use None if absent.
        prior = self.proposal_to_proposer.get(proposal_id)
        # Run this branch when prior is a different object from None and prior differs from proposer_event_id.
        if prior is not None and prior != proposer_event_id:
            # Raise TransitionSemanticError with the text 'PROPOSAL_CAUSAL_LINK_CONFLICT' to stop this execution
            # path.
            raise TransitionSemanticError("PROPOSAL_CAUSAL_LINK_CONFLICT")
        # Set self.proposal_to_proposer[proposal_id] to proposer_event_id.
        self.proposal_to_proposer[proposal_id] = proposer_event_id

    # Associate responder decision using the inputs and processing steps below.
    # Input proposal_id: the supplied proposal id.
    # Input responder_event_id: the supplied responder event id.
    # Output: self.proposal_to_proposer at proposal_id.
    # Processing: select branches using the stated conditions.
    def associate_responder_decision(self, proposal_id, responder_event_id):
        # Run this branch when proposal_id does not belong to self.proposal_to_proposer.
        if proposal_id not in self.proposal_to_proposer:
            # Raise TransitionSemanticError with the text 'PROPOSER_CAUSAL_LINK_NOT_FOUND' to stop this execution
            # path.
            raise TransitionSemanticError("PROPOSER_CAUSAL_LINK_NOT_FOUND")
        # Set prior to proposal_id from self.proposal_to_responder; use None if absent.
        prior = self.proposal_to_responder.get(proposal_id)
        # Run this branch when prior is a different object from None and prior differs from responder_event_id.
        if prior is not None and prior != responder_event_id:
            # Raise TransitionSemanticError with the text 'RESPONDER_CAUSAL_LINK_CONFLICT' to stop this execution
            # path.
            raise TransitionSemanticError("RESPONDER_CAUSAL_LINK_CONFLICT")
        # Set self.proposal_to_responder[proposal_id] to responder_event_id.
        self.proposal_to_responder[proposal_id] = responder_event_id
        # Return self.proposal_to_proposer at proposal_id to the caller.
        return self.proposal_to_proposer[proposal_id]

    # Observe protocol evaluation using the inputs and processing steps below.
    # Input proposal_id: the supplied proposal id.
    # Input evaluation: the supplied evaluation.
    # Input timestamp: the supplied timestamp.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def observe_protocol_evaluation(self, proposal_id, evaluation, timestamp):
        # Run this branch when evaluation.state does not belong to PROTOCOL_RESOLUTION.
        if evaluation.state not in PROTOCOL_RESOLUTION:
            # Return an empty tuple to the caller.
            return ()
        # Set affected to an empty list.
        affected = []
        # Set event_ids to a set containing proposal_id from self.proposal_to_proposer; use None if absent,
        # proposal_id from... minus a set containing None.
        event_ids = {self.proposal_to_proposer.get(proposal_id),
                     # Include proposal_id from self.proposal_to_responder; use None if absent in this set.
                     self.proposal_to_responder.get(proposal_id)} - {None}
        # Iterate over a tuple built from key/value pairs from self.transitions, binding each item to
        # (transition_id, item).
        for transition_id, item in tuple(self.transitions.items()):
            # Run this branch when item.decision_event_id belongs to event_ids.
            if item.decision_event_id in event_ids:
                # Append the result of self.resolve_transition(transition_id, PROTOCOL_RESOLUTION at
                # evaluation.state, timestamp, evaluation.state.value) to affected.
                affected.append(self.resolve_transition(
                    # Supply PROTOCOL_RESOLUTION at evaluation.state to self.resolve_transition.
                    transition_id, PROTOCOL_RESOLUTION[evaluation.state], timestamp,
                    # Supply evaluation.state.value to self.resolve_transition.
                    evaluation.state.value,
                ))
        # Return a tuple built from affected to the caller.
        return tuple(affected)

    # Resolve transition using the inputs and processing steps below.
    # Input transition_id: the supplied transition id.
    # Input status: the supplied status.
    # Input timestamp: the supplied timestamp.
    # Input reason: the supplied reason.
    # Input successor_snapshot: the supplied successor snapshot.
    # Input successor_state: the supplied successor state.
    # Output: updated.
    # Processing: select branches using the stated conditions.
    def resolve_transition(self, transition_id, status, timestamp, reason,
                           # Declare successor_snapshot, successor_state as input parameters.
                           successor_snapshot=None, successor_state=None):
        # Set item to self.transitions at transition_id.
        item = self.transitions[transition_id]
        # Run this branch when item.resolution_timestamp is a different object from None.
        if item.resolution_timestamp is not None:
            # Raise TransitionSemanticError with the text 'DUPLICATE_TRANSITION_RESOLUTION' to stop this execution
            # path.
            raise TransitionSemanticError("DUPLICATE_TRANSITION_RESOLUTION")
        # Set elapsed to a floating-point number built from timestamp minus item.decision_timestamp.
        elapsed = float(timestamp) - item.decision_timestamp
        # Run this branch when elapsed is less than 0.
        if elapsed < 0:
            # Raise TransitionSemanticError with the text 'NEGATIVE_TRANSITION_DURATION' to stop this execution
            # path.
            raise TransitionSemanticError("NEGATIVE_TRANSITION_DURATION")
        # Set updated to the result of replace(item).
        updated = replace(
            # Supply transition_status as status.
            # Supply resolution_reason as reason.
            item, transition_status=status, resolution_reason=reason,
            # Supply resolution_timestamp as a floating-point number built from timestamp.
            # Supply elapsed_seconds as elapsed.
            resolution_timestamp=float(timestamp), elapsed_seconds=elapsed,
            # Supply successor_actor_observation_snapshot as successor_snapshot.
            successor_actor_observation_snapshot=successor_snapshot,
            # Supply successor_semantic_state as successor_state.
            successor_semantic_state=successor_state,
            # Supply continuation_classification as ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES
            # when successor_snapshot is a different object from None, otherwise
            # ContinuationClassification.NEGOTIATION_SUBJECT_RESOLVED.
            continuation_classification=(
                # Evaluate ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES when successor_snapshot is
                # a different object from None, otherwise ContinuationClassification.NEGOTIATION_SUBJECT_RESOLVED
                # as part of the enclosing expression.
                ContinuationClassification.AGENT_DECISION_SEQUENCE_CONTINUES
                # Evaluate successor_snapshot is a different object from None as part of the enclosing expression.
                if successor_snapshot is not None else
                # Evaluate ContinuationClassification.NEGOTIATION_SUBJECT_RESOLVED as part of the enclosing
                # expression.
                ContinuationClassification.NEGOTIATION_SUBJECT_RESOLVED),
        )
        # Set self.transitions[transition_id] to updated.
        self.transitions[transition_id] = updated
        # Return updated to the caller.
        return updated
