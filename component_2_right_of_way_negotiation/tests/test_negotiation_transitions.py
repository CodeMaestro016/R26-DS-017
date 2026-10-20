# Import MappingProxyType from types for the operations below.
from types import MappingProxyType

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest

# Import ClaimRole, PolicyAuthority, PrecedenceClaim from negotiation_learning.claim_semantics for the operations
# below.
from negotiation_learning.claim_semantics import ClaimRole, PolicyAuthority, PrecedenceClaim
# Import NegotiationDecisionRole, PolicyDecisionProvenance from negotiation_learning.mappo_interface.models for
# the operations below.
from negotiation_learning.mappo_interface.models import (
    NegotiationDecisionRole, PolicyDecisionProvenance,
)
# Import NegotiationAction from negotiation_learning.models for the operations below.
from negotiation_learning.models import NegotiationAction
# Import NegotiationResponseAction from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import NegotiationResponseAction
# Import ProtocolState from negotiation_learning.protocol.message_models for the operations below.
from negotiation_learning.protocol.message_models import ProtocolState
# Import ClaimRelinquishmentProtocol from negotiation_learning.protocol.state_machine for the operations below.
from negotiation_learning.protocol.state_machine import ClaimRelinquishmentProtocol
# Import EncodedGraphObservation from negotiation_learning.tensor_encoding.models for the operations below.
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
# Import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from negotiation_learning.tensor_encoding.schemas for the
# operations below.
from negotiation_learning.tensor_encoding.schemas import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA
# Import ActorObservationSnapshot, CentralizedTrainingObservationSnapshot, DecisionEpochReason,
# NegotiationDecisionEpochTracker, NegotiationTransitionTracker,... from negotiation_learning.transitions for the
# operations below.
from negotiation_learning.transitions import (
    ActorObservationSnapshot, CentralizedTrainingObservationSnapshot,
    DecisionEpochReason,
    NegotiationDecisionEpochTracker, NegotiationTransitionTracker,
    TransitionSemanticError, TransitionStatus, reconstruct_actor_context,
    reconstruct_critic_input,
)


# Graph using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Output: the result of EncodedGraphObservation(ego, a tuple containing the text 'A', the text 'B', a zero-filled
# tensor with the requested...).
def graph(ego="B"):
    # Return the result of EncodedGraphObservation(ego, a tuple containing the text 'A', the text 'B', a
    # zero-filled tensor with the requested...) to the caller.
    return EncodedGraphObservation(
        # Supply a zero-filled tensor with the requested shape to EncodedGraphObservation.
        ego, ("A", "B"), np.zeros((2, 8), np.float32),
        # Supply the result of np.array(a list containing a list containing 0, a list containing 1, np.int64) to
        # EncodedGraphObservation.
        np.ones((2, 8), bool), np.array([[0], [1]], np.int64),
        # Supply a zero-filled tensor with the requested shape to EncodedGraphObservation.
        np.zeros((1, 9), np.float32), np.ones((1, 9), bool),
        # Supply a tuple built from NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        tuple(NODE_NUMERIC_SCHEMA), tuple(EDGE_NUMERIC_SCHEMA), {}, {}, {},
        "LOCAL_JOINT_PRECEDENCE_GRAPH", "IDEAL_SAME_STEP_V2V",
        "NOT_APPLIED", "NUMPY",
    )


# Snapshot using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input role: the supplied role.
# Input proposal: the supplied proposal.
# Input protocol_state: the supplied protocol state.
# Input mask: the supplied mask.
# Input claim: the supplied claim.
# Output: the result of ActorObservationSnapshot(a tuple containing the text 'snapshot', ego, role.value, claim,
# the requested attribute of...).
def snapshot(ego="B", role=NegotiationDecisionRole.PROPOSER, proposal=None,
             # Declare protocol_state, mask, claim as input parameters.
             protocol_state=None, mask=(True, True), claim=("A", "B")):
    # Return the result of ActorObservationSnapshot(a tuple containing the text 'snapshot', ego, role.value,
    # claim, the requested attribute of...) to the caller.
    return ActorObservationSnapshot(
        # Supply a tuple containing the text 'snapshot', ego, role.value, claim, the requested attribute of
        # proposal to ActorObservationSnapshot.
        ("snapshot", ego, role.value, claim, getattr(proposal, "proposal_id", None)),
        # Supply the text 'A' when ego equals the text 'B', otherwise the text 'B' to ActorObservationSnapshot.
        1.0, graph(ego), role, claim, "A" if ego == "B" else "B", proposal,
        # Supply a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' when role is the same
        # object as NegotiationDecisionRole.PROPOSER, otherwise a tuple containing the text
        # 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT' to ActorObservationSnapshot.
        protocol_state, (("KEEP_CLAIM", "RELINQUISH_CLAIM") if
        # Evaluate role is the same object as NegotiationDecisionRole.PROPOSER as part of the enclosing
        # expression.
        role is NegotiationDecisionRole.PROPOSER else
        # Evaluate a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT' as part
        # of the enclosing expression.
        ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")), mask,
        "DE_STVO", "IDEAL_SAME_STEP_V2V",
        # Supply the result of PolicyDecisionProvenance(the text 'obs', the text 'graph', the text 'mpnn', the
        # text 'semantic', the text 'mask') to ActorObservationSnapshot.
        PolicyDecisionProvenance("obs", "graph", "mpnn", "semantic", "mask"),
    )


# Emit using the inputs and processing steps below.
# Input tracker: the supplied tracker.
# Input t: the supplied t.
# Input lifecycle: the supplied lifecycle.
# Input mask: the supplied mask.
# Input role: the supplied role.
# Input proposal: the supplied proposal.
# Input parent: the supplied parent.
# Input claim: the supplied claim.
# Output: the result of tracker.emit().
def emit(tracker, t=1.0, lifecycle=("claim", 1.0), mask=(True, True),
         # Declare role, proposal, parent as input parameters.
         role=NegotiationDecisionRole.PROPOSER, proposal=None, parent=None,
         # Declare claim as input parameter.
         claim=("A", "B")):
    # Set snap to the result of snapshot(the text 'B' when role is the same object as
    # NegotiationDecisionRole.PROPOSER, otherwise the...).
    snap = snapshot("B" if role is NegotiationDecisionRole.PROPOSER else "A",
                    # Supply ProtocolState.PROPOSAL_PENDING when proposal, otherwise None to snapshot.
                    role, proposal, ProtocolState.PROPOSAL_PENDING if proposal else None,
                    # Supply claim to snapshot.
                    mask, claim)
    # Return the result of tracker.emit() to the caller.
    return tracker.emit(
        # Supply ego_id as snap.graph_observation.ego_id.
        # Supply role as role.
        ego_id=snap.graph_observation.ego_id, role=role,
        # Supply counterparty_id as snap.counterparty_id.
        # Supply claim_identity as claim.
        counterparty_id=snap.counterparty_id, claim_identity=claim,
        # Supply lifecycle_identity as lifecycle.
        lifecycle_identity=lifecycle,
        # Supply proposal_id as the requested attribute of proposal.
        proposal_id=getattr(proposal, "proposal_id", None),
        # Supply parent_decision_event_id as parent.
        # Supply timestamp as t.
        parent_decision_event_id=parent, timestamp=t,
        # Supply reason as DecisionEpochReason.NEW_NEGOTIABLE_PRECEDENCE_CLAIM when proposal is the same object as
        # None, otherwise DecisionEpochReason.NEW_PENDING_RELINQUISHMENT_PROPOSAL.
        reason=(DecisionEpochReason.NEW_NEGOTIABLE_PRECEDENCE_CLAIM if proposal is None
                # Evaluate DecisionEpochReason.NEW_PENDING_RELINQUISHMENT_PROPOSAL as part of the enclosing
                # expression.
                else DecisionEpochReason.NEW_PENDING_RELINQUISHMENT_PROPOSAL),
        # Supply negotiation_status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        # Supply protocol_state as snap.protocol_state.
        # Supply policy_authority as the text 'POLICY_AUTHORIZED'.
        protocol_state=snap.protocol_state, policy_authority="POLICY_AUTHORIZED",
        # Supply action_names as snap.action_names.
        # Supply hard_mask as mask.
        # Supply actor_snapshot as snap.
        action_names=snap.action_names, hard_mask=mask, actor_snapshot=snap,
        # Supply regulatory_profile as the text 'DE_STVO'.
        # Supply communication_model as the text 'IDEAL_SAME_STEP_V2V'.
        regulatory_profile="DE_STVO", communication_model="IDEAL_SAME_STEP_V2V",
        # Store the text 'TEST' under 'source'.
        provenance={"source": "TEST"},
    )


# Claim using the inputs and processing steps below.
# Output: the result of PrecedenceClaim(the text 'B', the text 'A', the text 'A', the text 'B',
# ClaimRole.EGO_IS_PRIORITY, a tuple...).
def claim():
    # Return the result of PrecedenceClaim(the text 'B', the text 'A', the text 'A', the text 'B',
    # ClaimRole.EGO_IS_PRIORITY, a tuple...) to the caller.
    return PrecedenceClaim(
        # Supply ClaimRole.EGO_IS_PRIORITY to PrecedenceClaim.
        "B", "A", "A", "B", ClaimRole.EGO_IS_PRIORITY, ("RULE",),
        # Supply the result of MappingProxyType(an empty dictionary) to PrecedenceClaim.
        ("SECTION",), ("ZONE",), 1.0, MappingProxyType({}),
    )


# Check unchanged claim timestamp does not reemit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unchanged_claim_timestamp_does_not_reemit():
    # Set tracker to the result of NegotiationDecisionEpochTracker().
    tracker = NegotiationDecisionEpochTracker()
    # Require the result of emit(tracker, 1.0) is a different object from None; otherwise raise AssertionError.
    assert emit(tracker, 1.0) is not None
    # Require the result of emit(tracker, 2.0) is the same object as None; otherwise raise AssertionError.
    assert emit(tracker, 2.0) is None


# Check new lifecycle and mask change reemit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_new_lifecycle_and_mask_change_reemit():
    # Set tracker to the result of NegotiationDecisionEpochTracker().
    tracker = NegotiationDecisionEpochTracker()
    # Require the result of emit(tracker) is a different object from None; otherwise raise AssertionError.
    assert emit(tracker) is not None
    # Call tracker.close_subject with the supplied arguments.
    tracker.close_subject(NegotiationDecisionRole.PROPOSER, "B", ("A", "B"))
    # Require emit(tracker, 2.0, ('claim', 2.0)).decision_epoch_reason is the same object as
    # DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED; otherwise raise AssertionError.
    assert emit(tracker, 2.0, ("claim", 2.0)).decision_epoch_reason is DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED
    # Require the result of emit(tracker, 3.0, a tuple containing the text 'claim', 2.0, a tuple containing True,
    # False) is a different object from None; otherwise raise AssertionError.
    assert emit(tracker, 3.0, ("claim", 2.0), (True, False)) is not None


# Check multiple claims order independent using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_multiple_claims_order_independent():
    # Ids using the inputs and processing steps below.
    # Input order: the supplied order.
    # Output: a set of emit(tracker, 1.0, ('life', c), claim=c).decision_event_id for c in order.
    def ids(order):
        # Set tracker to the result of NegotiationDecisionEpochTracker().
        tracker = NegotiationDecisionEpochTracker()
        # Return a set of emit(tracker, 1.0, ('life', c), claim=c).decision_event_id for c in order to the caller.
        return {emit(tracker, 1.0, ("life", c), claim=c).decision_event_id for c in order}
    # Set claims to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text
    # 'C', the text 'B', a tuple...
    claims = (("A", "B"), ("C", "B"), ("B", "C"), ("D", "A"))
    # Require the result of ids(claims) equals the result of ids(the reverse traversal of claims); otherwise raise
    # AssertionError.
    assert ids(claims) == ids(reversed(claims))


# Check snapshot is immutable copy using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_snapshot_is_immutable_copy():
    # Set source to the result of graph().
    source = graph()
    # Set snap to the result of snapshot().
    snap = snapshot()
    # Require the negation of snap.graph_observation.node_features.flags.writeable; otherwise raise
    # AssertionError.
    assert not snap.graph_observation.node_features.flags.writeable
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError):
        # Set snap.graph_observation.node_features[0, 0] to 1.
        snap.graph_observation.node_features[0, 0] = 1
    # Require snap.graph_observation.node_features is a different object from source.node_features; otherwise
    # raise AssertionError.
    assert snap.graph_observation.node_features is not source.node_features


# Check keep resolves same step without proposal using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_keep_resolves_same_step_without_proposal():
    # Set epochs to the result of NegotiationDecisionEpochTracker().
    # Set epoch to the result of emit(epochs).
    epochs = NegotiationDecisionEpochTracker(); epoch = emit(epochs)
    # Set transitions to the result of NegotiationTransitionTracker(the result of ClaimRelinquishmentProtocol()).
    transitions = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    # Set opened to the result of transitions.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, the
    # result of snapshot()).
    opened = transitions.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, snapshot())
    # Set resolved to the result of transitions.apply_action(opened.transition_id, 1.0).
    resolved = transitions.apply_action(opened.transition_id, 1.0)
    # Require resolved.transition_status is the same object as TransitionStatus.RESOLVED_CLAIM_RETAINED; otherwise
    # raise AssertionError.
    assert resolved.transition_status is TransitionStatus.RESOLVED_CLAIM_RETAINED
    # Require resolved.elapsed_seconds equals 0.0; otherwise raise AssertionError.
    assert resolved.elapsed_seconds == 0.0
    # Require resolved.proposal_id is the same object as None; otherwise raise AssertionError.
    assert resolved.proposal_id is None


# Check relinquish and exact accept causal chain using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_relinquish_and_exact_accept_causal_chain():
    # Set epoch_tracker to the result of NegotiationDecisionEpochTracker().
    # Set proposer to the result of emit(epoch_tracker).
    epoch_tracker = NegotiationDecisionEpochTracker(); proposer = emit(epoch_tracker)
    # Set tracker to the result of NegotiationTransitionTracker(the result of ClaimRelinquishmentProtocol()).
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    # Set opened to the result of tracker.open_transition(proposer, NegotiationAction.RELINQUISH_CLAIM.value, the
    # result of snapshot()).
    opened = tracker.open_transition(proposer, NegotiationAction.RELINQUISH_CLAIM.value, snapshot())
    # Set waiting to the result of tracker.apply_action(opened.transition_id, 1.0).
    waiting = tracker.apply_action(opened.transition_id, 1.0, claim=claim(), regulatory_profile="DE_STVO")
    # Set proposal to waiting.immediate_action_consequence.semantic_message.
    proposal = waiting.immediate_action_consequence.semantic_message
    # Set responder to the result of emit(epoch_tracker, 1.0, a tuple containing the text 'proposal',
    # proposal.proposal_id).
    responder = emit(epoch_tracker, 1.0, ("proposal", proposal.proposal_id),
                     # Supply role as NegotiationDecisionRole.RESPONDER.
                     # Supply proposal as proposal.
                     role=NegotiationDecisionRole.RESPONDER, proposal=proposal,
                     # Supply parent as proposer.decision_event_id.
                     parent=proposer.decision_event_id)
    # Require the result of tracker.associate_responder_decision(proposal.proposal_id,
    # responder.decision_event_id) equals proposer.decision_event_id; otherwise raise AssertionError.
    assert tracker.associate_responder_decision(proposal.proposal_id, responder.decision_event_id) == proposer.decision_event_id
    # Set response_transition to the result of tracker.open_transition(responder,
    # NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value, the result of snapshot(the...).
    response_transition = tracker.open_transition(
        # Supply NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value to tracker.open_transition.
        responder, NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
        # Supply the result of snapshot(the text 'A', NegotiationDecisionRole.RESPONDER, proposal,
        # ProtocolState.PROPOSAL_PENDING) to tracker.open_transition.
        snapshot("A", NegotiationDecisionRole.RESPONDER, proposal,
                 # Supply ProtocolState.PROPOSAL_PENDING to snapshot.
                 ProtocolState.PROPOSAL_PENDING),
    )
    # Set response_waiting to the result of tracker.apply_action(response_transition.transition_id, 1.0).
    response_waiting = tracker.apply_action(
        # Supply proposal as proposal.
        response_transition.transition_id, 1.0, proposal=proposal,
        # Supply regulatory_profile as the text 'DE_STVO'.
        regulatory_profile="DE_STVO",
    )
    # Set response to response_waiting.immediate_action_consequence.semantic_message.
    response = response_waiting.immediate_action_consequence.semantic_message
    # Set evaluation to the result of tracker.protocol.evaluate(a tuple containing a dictionary containing
    # yielding_vehicle_id, priority_vehicle_id, timestamp,...).
    evaluation = tracker.protocol.evaluate(
        # Store the text 'A' under 'yielding_vehicle_id'.
        # Store the text 'B' under 'priority_vehicle_id'.
        # Store 1.0 under 'timestamp'.
        ({"yielding_vehicle_id": "A", "priority_vehicle_id": "B", "timestamp": 1.0},),
        # Supply a tuple containing proposal, response to tracker.protocol.evaluate.
        (proposal, response), 1.0, "DE_STVO",
    )
    # Set resolved to the result of tracker.observe_protocol_evaluation(proposal.proposal_id, evaluation, 1.0).
    resolved = tracker.observe_protocol_evaluation(proposal.proposal_id, evaluation, 1.0)
    # Require the number of entries in resolved equals 2; otherwise raise AssertionError.
    assert len(resolved) == 2
    # Require whether every item is true in a lazy sequence of item.transition_status is the same object as
    # TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED for item in resolved; otherwise raise AssertionError.
    assert all(item.transition_status is TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED for item in resolved)


# Apply 'state,status' as a decorator to configure the following definition.
@pytest.mark.parametrize("state,status", [
    # Include a tuple containing ProtocolState.PROPOSAL_REJECTED, TransitionStatus.RESOLVED_PROPOSAL_REJECTED in
    # this list.
    (ProtocolState.PROPOSAL_REJECTED, TransitionStatus.RESOLVED_PROPOSAL_REJECTED),
    # Include a tuple containing ProtocolState.SOURCE_CLAIM_INVALID,
    # TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID in this list.
    (ProtocolState.SOURCE_CLAIM_INVALID, TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID),
    # Include a tuple containing ProtocolState.PROTOCOL_BLOCKED, TransitionStatus.RESOLVED_PROTOCOL_BLOCKED in
    # this list.
    (ProtocolState.PROTOCOL_BLOCKED, TransitionStatus.RESOLVED_PROTOCOL_BLOCKED),
    # Include a tuple containing ProtocolState.PROTOCOL_DISAGREEMENT,
    # TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT in this list.
    (ProtocolState.PROTOCOL_DISAGREEMENT, TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT),
])
# Check protocol resolution categories using the setup, calls, and assertions below.
# Input state: the state read or updated by this operation.
# Input status: the supplied status.
# Output: no explicit value; normal completion returns None.
def test_protocol_resolution_categories(state, status):
    # Define Evaluation to group the state and operations declared below.
    # Instances expose the attributes and methods implemented in this class.
    # Keep this block syntactically valid without performing an operation.
    class Evaluation: pass
    # Set epoch to the result of emit(the result of NegotiationDecisionEpochTracker()).
    epoch = emit(NegotiationDecisionEpochTracker())
    # Set tracker to the result of NegotiationTransitionTracker(the result of ClaimRelinquishmentProtocol()).
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    # Set opened to the result of tracker.open_transition(epoch, NegotiationAction.RELINQUISH_CLAIM.value, the
    # result of snapshot()).
    opened = tracker.open_transition(epoch, NegotiationAction.RELINQUISH_CLAIM.value, snapshot())
    # Set waiting to the result of tracker.apply_action(opened.transition_id, 1.0).
    waiting = tracker.apply_action(opened.transition_id, 1.0, claim=claim(), regulatory_profile="DE_STVO")
    # Set proposal_id to waiting.proposal_id.
    # Set evaluation to the result of Evaluation().
    # Set evaluation.state to state.
    proposal_id = waiting.proposal_id; evaluation = Evaluation(); evaluation.state = state
    # Set result to the result of tracker.observe_protocol_evaluation(proposal_id, evaluation, 2.0).
    result = tracker.observe_protocol_evaluation(proposal_id, evaluation, 2.0)
    # Require result[0].transition_status is the same object as status; otherwise raise AssertionError.
    assert result[0].transition_status is status
    # Require result[0].elapsed_seconds equals 1.0; otherwise raise AssertionError.
    assert result[0].elapsed_seconds == 1.0


# Check negative duration and duplicate resolution rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_negative_duration_and_duplicate_resolution_rejected():
    # Set epoch to the result of emit(the result of NegotiationDecisionEpochTracker(), 2.0).
    epoch = emit(NegotiationDecisionEpochTracker(), 2.0)
    # Set tracker to the result of NegotiationTransitionTracker(the result of ClaimRelinquishmentProtocol()).
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    # Set opened to the result of tracker.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, the result of
    # snapshot()).
    opened = tracker.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, snapshot())
    # Enter the result of pytest.raises(TransitionSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(TransitionSemanticError, match="NEGATIVE_TRANSITION_DURATION"):
        # Call tracker.apply_action with the supplied arguments.
        tracker.apply_action(opened.transition_id, 1.0)
    # Set resolved to the result of tracker.apply_action(opened.transition_id, 2.0).
    resolved = tracker.apply_action(opened.transition_id, 2.0)
    # Enter the result of pytest.raises(TransitionSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(TransitionSemanticError, match="DUPLICATE_TRANSITION_RESOLUTION"):
        # Call tracker.resolve_transition with the supplied arguments.
        tracker.resolve_transition(resolved.transition_id, resolved.transition_status, 2.0, "AGAIN")


# Check transition has no reward or ppo fields using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_transition_has_no_reward_or_ppo_fields():
    # Set fields to NegotiationTransitionTracker.__module__.
    fields = NegotiationTransitionTracker.__module__
    # Import NegotiationTransition from negotiation_learning.transitions.models for the operations below.
    from negotiation_learning.transitions.models import NegotiationTransition
    # Set names to NegotiationTransition.__dataclass_fields__.
    names = NegotiationTransition.__dataclass_fields__
    # Require the text 'reward' does not belong to names; otherwise raise AssertionError.
    assert "reward" not in names
    # Require the negation of a set containing the text 'return_value', the text 'advantage', the text 'gae', the
    # text 'ppo_ratio' intersected with a set built from names; otherwise raise AssertionError.
    assert not ({"return_value", "advantage", "gae", "ppo_ratio"} & set(names))


# Check gnn semantic actor and critic replay using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_gnn_semantic_actor_and_critic_replay():
    # Import torch for use in this module.
    import torch
    # Import CentralizedNegotiationCritic, DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor
    # from negotiation_learning.ctde for the operations below.
    from negotiation_learning.ctde import (
        CentralizedNegotiationCritic, DecentralizedNegotiationActor,
        DecentralizedNegotiationResponseActor,
    )
    # Import EdgeAwareMPNNEncoder from negotiation_learning.gnn for the operations below.
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder
    # Import RoleAwareNegotiationPolicy from negotiation_learning.mappo_interface for the operations below.
    from negotiation_learning.mappo_interface import RoleAwareNegotiationPolicy

    # TEST_ONLY_NON_OPERATIONAL_VALUE architecture dimensions.
    # Call torch.manual_seed with the supplied arguments.
    torch.manual_seed(7)
    # Set gnn to the result of EdgeAwareMPNNEncoder(8, 9, 5, 1).
    gnn = EdgeAwareMPNNEncoder(8, 9, 5, 1)
    # Set snap to the result of snapshot().
    snap = snapshot()
    # Set (context1, output1, semantic1, protocol1) to the result of reconstruct_actor_context(snap, gnn).
    context1, output1, semantic1, protocol1 = reconstruct_actor_context(snap, gnn)
    # Set (context2, output2, semantic2, protocol2) to the result of reconstruct_actor_context(snap, gnn).
    context2, output2, semantic2, protocol2 = reconstruct_actor_context(snap, gnn)
    # Require the result of np.array_equal(semantic1.model_input, semantic2.model_input); otherwise raise
    # AssertionError.
    assert np.array_equal(semantic1.model_input, semantic2.model_input)
    # Require protocol1 is the same object as protocol2; is the same object as None; otherwise raise
    # AssertionError.
    assert protocol1 is protocol2 is None
    # Require the result of torch.equal(output1.ego_embedding, output2.ego_embedding); otherwise raise
    # AssertionError.
    assert torch.equal(output1.ego_embedding, output2.ego_embedding)
    # Set input_dim to the result of context1.ego_embedding.numel() plus the result of
    # context1.local_graph_embedding.numel() plus the result of context1.claim_or_proposal_representation.numel().
    input_dim = context1.ego_embedding.numel() + context1.local_graph_embedding.numel() + context1.claim_or_proposal_representation.numel()
    # Set policy to the result of RoleAwareNegotiationPolicy(the result of
    # DecentralizedNegotiationActor(input_dim, 2), the result of...).
    policy = RoleAwareNegotiationPolicy(
        # Supply the result of DecentralizedNegotiationActor(input_dim, 2) to RoleAwareNegotiationPolicy.
        DecentralizedNegotiationActor(input_dim, 2),
        # Supply the result of DecentralizedNegotiationResponseActor(input_dim plus 18, 2) to
        # RoleAwareNegotiationPolicy.
        DecentralizedNegotiationResponseActor(input_dim + 18, 2),
    )
    # Set (forward1, dist1) to the result of policy.distribution_for(context1).
    forward1, dist1 = policy.distribution_for(context1)
    # Set (forward2, dist2) to the result of policy.distribution_for(context2).
    forward2, dist2 = policy.distribution_for(context2)
    # Require the result of torch.equal(forward1.unmasked_action_logits, forward2.unmasked_action_logits);
    # otherwise raise AssertionError.
    assert torch.equal(forward1.unmasked_action_logits, forward2.unmasked_action_logits)
    # Require the result of torch.equal(dist1.probabilities, dist2.probabilities); otherwise raise AssertionError.
    assert torch.equal(dist1.probabilities, dist2.probabilities)
    # Require the result of torch.equal(context1.action_feasibility_mask, context2.action_feasibility_mask);
    # otherwise raise AssertionError.
    assert torch.equal(context1.action_feasibility_mask, context2.action_feasibility_mask)

    # Set centralized to the result of CentralizedTrainingObservationSnapshot(a tuple containing the text
    # 'critic', 1.0, 1.0, a tuple containing snap, a tuple containing the...).
    centralized = CentralizedTrainingObservationSnapshot(
        # Supply a tuple containing the text 'critic', 1.0 to CentralizedTrainingObservationSnapshot.
        ("critic", 1.0), 1.0, (snap,), ("B",), "SUM",
        # Store the text 'TRAINING_ONLY' under 'scope'.
        {"scope": "TRAINING_ONLY"},
    )
    # Set critic_input1 to the result of reconstruct_critic_input(centralized, gnn).
    critic_input1 = reconstruct_critic_input(centralized, gnn)
    # Set critic_input2 to the result of reconstruct_critic_input(centralized, gnn).
    critic_input2 = reconstruct_critic_input(centralized, gnn)
    # Set critic to the result of CentralizedNegotiationCritic(critic_input1.shape at -1).
    critic = CentralizedNegotiationCritic(critic_input1.shape[-1])
    # Require the result of torch.equal(critic_input1, critic_input2); otherwise raise AssertionError.
    assert torch.equal(critic_input1, critic_input2)
    # Require the result of torch.isfinite(critic(critic_input1)).all(); otherwise raise AssertionError.
    assert torch.isfinite(critic(critic_input1)).all()


# Check actor replay signature excludes centralized state using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actor_replay_signature_excludes_centralized_state():
    # Import inspect for use in this module.
    import inspect
    # Import reconstruct_actor_context from negotiation_learning.transitions.replay for the operations below.
    from negotiation_learning.transitions.replay import reconstruct_actor_context
    # Require a tuple built from inspect.signature(reconstruct_actor_context).parameters equals a tuple containing
    # the text 'snapshot', the text 'gnn_encoder'; otherwise raise AssertionError.
    assert tuple(inspect.signature(reconstruct_actor_context).parameters) == (
        "snapshot", "gnn_encoder",
    )


# Check responder proposal protocol and actor replay using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_responder_proposal_protocol_and_actor_replay():
    # Import torch for use in this module.
    import torch
    # Import DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor from negotiation_learning.ctde
    # for the operations below.
    from negotiation_learning.ctde import (
        DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
    )
    # Import EdgeAwareMPNNEncoder from negotiation_learning.gnn for the operations below.
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder
    # Import RoleAwareNegotiationPolicy from negotiation_learning.mappo_interface for the operations below.
    from negotiation_learning.mappo_interface import RoleAwareNegotiationPolicy

    # Set protocol to the result of ClaimRelinquishmentProtocol().
    protocol = ClaimRelinquishmentProtocol()
    # Set proposal to the result of protocol.create_proposal(the result of claim(), 1.0, the text 'DE_STVO',
    # PolicyAuthority.POLICY_AUTHORIZED).
    proposal = protocol.create_proposal(
        # Supply the result of claim() to protocol.create_proposal.
        claim(), 1.0, "DE_STVO",
        # Supply PolicyAuthority.POLICY_AUTHORIZED to protocol.create_proposal.
        PolicyAuthority.POLICY_AUTHORIZED,
    )
    # Set responder_snapshot to the result of snapshot(the text 'A', NegotiationDecisionRole.RESPONDER, proposal,
    # ProtocolState.PROPOSAL_PENDING).
    responder_snapshot = snapshot(
        # Supply NegotiationDecisionRole.RESPONDER to snapshot.
        "A", NegotiationDecisionRole.RESPONDER, proposal,
        # Supply ProtocolState.PROPOSAL_PENDING to snapshot.
        ProtocolState.PROPOSAL_PENDING,
    )
    # Call torch.manual_seed with the supplied arguments.
    torch.manual_seed(8)
    # Set gnn to the result of EdgeAwareMPNNEncoder(8, 9, 5, 1).
    gnn = EdgeAwareMPNNEncoder(8, 9, 5, 1)
    # Set (context1, output1, subject1, protocol1) to the result of reconstruct_actor_context(responder_snapshot,
    # gnn).
    context1, output1, subject1, protocol1 = reconstruct_actor_context(responder_snapshot, gnn)
    # Set (context2, output2, subject2, protocol2) to the result of reconstruct_actor_context(responder_snapshot,
    # gnn).
    context2, output2, subject2, protocol2 = reconstruct_actor_context(responder_snapshot, gnn)
    # Require subject1.proposal_id equals proposal.proposal_id; otherwise raise AssertionError.
    assert subject1.proposal_id == proposal.proposal_id
    # Require the result of np.array_equal(subject1.model_input, subject2.model_input); otherwise raise
    # AssertionError.
    assert np.array_equal(subject1.model_input, subject2.model_input)
    # Require the result of np.array_equal(protocol1.model_input, protocol2.model_input); otherwise raise
    # AssertionError.
    assert np.array_equal(protocol1.model_input, protocol2.model_input)
    # Require the result of torch.equal(output1.graph_embedding, output2.graph_embedding); otherwise raise
    # AssertionError.
    assert torch.equal(output1.graph_embedding, output2.graph_embedding)
    # Set responder_dim to the sum of a lazy sequence of the result of item.numel() for item in a tuple containing
    # context1.ego_embedding, context1.local_graph_embedding, context1.claim_or_proposal_representation,... plus
    # 2.
    responder_dim = sum(item.numel() for item in (
        # Include context1.local_graph_embedding in this tuple.
        context1.ego_embedding, context1.local_graph_embedding,
        # Include context1.claim_or_proposal_representation in this tuple.
        context1.claim_or_proposal_representation,
        # Include context1.protocol_state_representation in this tuple.
        context1.protocol_state_representation,
    # Supply 2 to the enclosing expression.
    )) + 2
    # Set policy to the result of RoleAwareNegotiationPolicy(the result of DecentralizedNegotiationActor(44, 2),
    # the result of...).
    policy = RoleAwareNegotiationPolicy(
        # Supply the result of DecentralizedNegotiationActor(44, 2) to RoleAwareNegotiationPolicy.
        DecentralizedNegotiationActor(44, 2),
        # Supply the result of DecentralizedNegotiationResponseActor(responder_dim, 2) to
        # RoleAwareNegotiationPolicy.
        DecentralizedNegotiationResponseActor(responder_dim, 2),
    )
    # Set (logits1, distribution1) to the result of policy.distribution_for(context1).
    logits1, distribution1 = policy.distribution_for(context1)
    # Set (logits2, distribution2) to the result of policy.distribution_for(context2).
    logits2, distribution2 = policy.distribution_for(context2)
    # Require the result of torch.equal(logits1.unmasked_action_logits, logits2.unmasked_action_logits); otherwise
    # raise AssertionError.
    assert torch.equal(logits1.unmasked_action_logits, logits2.unmasked_action_logits)
    # Require the result of torch.equal(distribution1.probabilities, distribution2.probabilities); otherwise raise
    # AssertionError.
    assert torch.equal(distribution1.probabilities, distribution2.probabilities)


# Check reject consequence and simultaneous proposal isolation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_reject_consequence_and_simultaneous_proposal_isolation():
    # Set protocol to the result of ClaimRelinquishmentProtocol().
    protocol = ClaimRelinquishmentProtocol()
    # Set proposal1 to the result of protocol.create_proposal(the result of claim(), 1.0, the text 'DE_STVO',
    # PolicyAuthority.POLICY_AUTHORIZED).
    proposal1 = protocol.create_proposal(claim(), 1.0, "DE_STVO", PolicyAuthority.POLICY_AUTHORIZED)
    # Set other_claim to the result of PrecedenceClaim(the text 'D', the text 'C', the text 'C', the text 'D',
    # ClaimRole.EGO_IS_PRIORITY, an empty...).
    other_claim = PrecedenceClaim(
        # Supply ClaimRole.EGO_IS_PRIORITY to PrecedenceClaim.
        "D", "C", "C", "D", ClaimRole.EGO_IS_PRIORITY, (), (), (), 1.0,
        # Supply the result of MappingProxyType(an empty dictionary) to PrecedenceClaim.
        MappingProxyType({}),
    )
    # Set proposal2 to the result of protocol.create_proposal(other_claim, 1.0, the text 'DE_STVO',
    # PolicyAuthority.POLICY_AUTHORIZED).
    proposal2 = protocol.create_proposal(other_claim, 1.0, "DE_STVO", PolicyAuthority.POLICY_AUTHORIZED)
    # Set tracker to the result of NegotiationTransitionTracker(protocol).
    tracker = NegotiationTransitionTracker(protocol)
    # Call tracker.associate_proposal with the supplied arguments.
    tracker.associate_proposal(proposal1.proposal_id, ("proposer", 1))
    # Call tracker.associate_proposal with the supplied arguments.
    tracker.associate_proposal(proposal2.proposal_id, ("proposer", 2))
    # Require the result of tracker.associate_responder_decision(proposal1.proposal_id, a tuple containing the
    # text 'responder', 1) equals a tuple containing the text 'proposer', 1; otherwise raise AssertionError.
    assert tracker.associate_responder_decision(proposal1.proposal_id, ("responder", 1)) == ("proposer", 1)
    # Require the result of tracker.associate_responder_decision(proposal2.proposal_id, a tuple containing the
    # text 'responder', 2) equals a tuple containing the text 'proposer', 2; otherwise raise AssertionError.
    assert tracker.associate_responder_decision(proposal2.proposal_id, ("responder", 2)) == ("proposer", 2)
    # Require tracker.proposal_to_responder at proposal1.proposal_id differs from tracker.proposal_to_responder at
    # proposal2.proposal_id; otherwise raise AssertionError.
    assert tracker.proposal_to_responder[proposal1.proposal_id] != tracker.proposal_to_responder[proposal2.proposal_id]

    # Set epochs to the result of NegotiationDecisionEpochTracker().
    epochs = NegotiationDecisionEpochTracker()
    # Set responder to the result of emit(epochs).
    responder = emit(epochs, role=NegotiationDecisionRole.RESPONDER,
                     # Supply proposal as proposal1.
                     # Supply parent as a tuple containing the text 'proposer', 1.
                     proposal=proposal1, parent=("proposer", 1))
    # Set opened to the result of tracker.open_transition(responder,
    # NegotiationResponseAction.REJECT_RELINQUISHMENT.value, the result of snapshot(the...).
    opened = tracker.open_transition(
        # Supply NegotiationResponseAction.REJECT_RELINQUISHMENT.value to tracker.open_transition.
        responder, NegotiationResponseAction.REJECT_RELINQUISHMENT.value,
        # Supply the result of snapshot(the text 'A', NegotiationDecisionRole.RESPONDER, proposal1,
        # ProtocolState.PROPOSAL_PENDING) to tracker.open_transition.
        snapshot("A", NegotiationDecisionRole.RESPONDER, proposal1,
                 # Supply ProtocolState.PROPOSAL_PENDING to snapshot.
                 ProtocolState.PROPOSAL_PENDING),
    )
    # Set waiting to the result of tracker.apply_action(opened.transition_id, 1.0).
    waiting = tracker.apply_action(opened.transition_id, 1.0,
                                   # Supply proposal as proposal1.
                                   # Supply regulatory_profile as the text 'DE_STVO'.
                                   proposal=proposal1, regulatory_profile="DE_STVO")
    # Set response to waiting.immediate_action_consequence.semantic_message.
    response = waiting.immediate_action_consequence.semantic_message
    # Require response.response.value equals the text 'REJECT'; otherwise raise AssertionError.
    assert response.response.value == "REJECT"
    # Require response.proposal_id equals proposal1.proposal_id; otherwise raise AssertionError.
    assert response.proposal_id == proposal1.proposal_id
