from types import MappingProxyType

import numpy as np
import pytest

from negotiation_learning.claim_semantics import ClaimRole, PolicyAuthority, PrecedenceClaim
from negotiation_learning.mappo_interface.models import (
    NegotiationDecisionRole, PolicyDecisionProvenance,
)
from negotiation_learning.models import NegotiationAction
from negotiation_learning.protocol import NegotiationResponseAction
from negotiation_learning.protocol.message_models import ProtocolState
from negotiation_learning.protocol.state_machine import ClaimRelinquishmentProtocol
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA
from negotiation_learning.transitions import (
    ActorObservationSnapshot, CentralizedTrainingObservationSnapshot,
    DecisionEpochReason,
    NegotiationDecisionEpochTracker, NegotiationTransitionTracker,
    TransitionSemanticError, TransitionStatus, reconstruct_actor_context,
    reconstruct_critic_input,
)


def graph(ego="B"):
    return EncodedGraphObservation(
        ego, ("A", "B"), np.zeros((2, 8), np.float32),
        np.ones((2, 8), bool), np.array([[0], [1]], np.int64),
        np.zeros((1, 9), np.float32), np.ones((1, 9), bool),
        tuple(NODE_NUMERIC_SCHEMA), tuple(EDGE_NUMERIC_SCHEMA), {}, {}, {},
        "LOCAL_JOINT_PRECEDENCE_GRAPH", "IDEAL_SAME_STEP_V2V",
        "NOT_APPLIED", "NUMPY",
    )


def snapshot(ego="B", role=NegotiationDecisionRole.PROPOSER, proposal=None,
             protocol_state=None, mask=(True, True), claim=("A", "B")):
    return ActorObservationSnapshot(
        ("snapshot", ego, role.value, claim, getattr(proposal, "proposal_id", None)),
        1.0, graph(ego), role, claim, "A" if ego == "B" else "B", proposal,
        protocol_state, (("KEEP_CLAIM", "RELINQUISH_CLAIM") if
        role is NegotiationDecisionRole.PROPOSER else
        ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")), mask,
        "DE_STVO", "IDEAL_SAME_STEP_V2V",
        PolicyDecisionProvenance("obs", "graph", "mpnn", "semantic", "mask"),
    )


def emit(tracker, t=1.0, lifecycle=("claim", 1.0), mask=(True, True),
         role=NegotiationDecisionRole.PROPOSER, proposal=None, parent=None,
         claim=("A", "B")):
    snap = snapshot("B" if role is NegotiationDecisionRole.PROPOSER else "A",
                    role, proposal, ProtocolState.PROPOSAL_PENDING if proposal else None,
                    mask, claim)
    return tracker.emit(
        ego_id=snap.graph_observation.ego_id, role=role,
        counterparty_id=snap.counterparty_id, claim_identity=claim,
        lifecycle_identity=lifecycle,
        proposal_id=getattr(proposal, "proposal_id", None),
        parent_decision_event_id=parent, timestamp=t,
        reason=(DecisionEpochReason.NEW_NEGOTIABLE_PRECEDENCE_CLAIM if proposal is None
                else DecisionEpochReason.NEW_PENDING_RELINQUISHMENT_PROPOSAL),
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        protocol_state=snap.protocol_state, policy_authority="POLICY_AUTHORIZED",
        action_names=snap.action_names, hard_mask=mask, actor_snapshot=snap,
        regulatory_profile="DE_STVO", communication_model="IDEAL_SAME_STEP_V2V",
        provenance={"source": "TEST"},
    )


def claim():
    return PrecedenceClaim(
        "B", "A", "A", "B", ClaimRole.EGO_IS_PRIORITY, ("RULE",),
        ("SECTION",), ("ZONE",), 1.0, MappingProxyType({}),
    )


def test_unchanged_claim_timestamp_does_not_reemit():
    tracker = NegotiationDecisionEpochTracker()
    assert emit(tracker, 1.0) is not None
    assert emit(tracker, 2.0) is None


def test_new_lifecycle_and_mask_change_reemit():
    tracker = NegotiationDecisionEpochTracker()
    assert emit(tracker) is not None
    tracker.close_subject(NegotiationDecisionRole.PROPOSER, "B", ("A", "B"))
    assert emit(tracker, 2.0, ("claim", 2.0)).decision_epoch_reason is DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED
    assert emit(tracker, 3.0, ("claim", 2.0), (True, False)) is not None


def test_multiple_claims_order_independent():
    def ids(order):
        tracker = NegotiationDecisionEpochTracker()
        return {emit(tracker, 1.0, ("life", c), claim=c).decision_event_id for c in order}
    claims = (("A", "B"), ("C", "B"), ("B", "C"), ("D", "A"))
    assert ids(claims) == ids(reversed(claims))


def test_snapshot_is_immutable_copy():
    source = graph()
    snap = snapshot()
    assert not snap.graph_observation.node_features.flags.writeable
    with pytest.raises(ValueError):
        snap.graph_observation.node_features[0, 0] = 1
    assert snap.graph_observation.node_features is not source.node_features


def test_keep_resolves_same_step_without_proposal():
    epochs = NegotiationDecisionEpochTracker(); epoch = emit(epochs)
    transitions = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    opened = transitions.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, snapshot())
    resolved = transitions.apply_action(opened.transition_id, 1.0)
    assert resolved.transition_status is TransitionStatus.RESOLVED_CLAIM_RETAINED
    assert resolved.elapsed_seconds == 0.0
    assert resolved.proposal_id is None


def test_relinquish_and_exact_accept_causal_chain():
    epoch_tracker = NegotiationDecisionEpochTracker(); proposer = emit(epoch_tracker)
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    opened = tracker.open_transition(proposer, NegotiationAction.RELINQUISH_CLAIM.value, snapshot())
    waiting = tracker.apply_action(opened.transition_id, 1.0, claim=claim(), regulatory_profile="DE_STVO")
    proposal = waiting.immediate_action_consequence.semantic_message
    responder = emit(epoch_tracker, 1.0, ("proposal", proposal.proposal_id),
                     role=NegotiationDecisionRole.RESPONDER, proposal=proposal,
                     parent=proposer.decision_event_id)
    assert tracker.associate_responder_decision(proposal.proposal_id, responder.decision_event_id) == proposer.decision_event_id
    response_transition = tracker.open_transition(
        responder, NegotiationResponseAction.ACCEPT_RELINQUISHMENT.value,
        snapshot("A", NegotiationDecisionRole.RESPONDER, proposal,
                 ProtocolState.PROPOSAL_PENDING),
    )
    response_waiting = tracker.apply_action(
        response_transition.transition_id, 1.0, proposal=proposal,
        regulatory_profile="DE_STVO",
    )
    response = response_waiting.immediate_action_consequence.semantic_message
    evaluation = tracker.protocol.evaluate(
        ({"yielding_vehicle_id": "A", "priority_vehicle_id": "B", "timestamp": 1.0},),
        (proposal, response), 1.0, "DE_STVO",
    )
    resolved = tracker.observe_protocol_evaluation(proposal.proposal_id, evaluation, 1.0)
    assert len(resolved) == 2
    assert all(item.transition_status is TransitionStatus.RESOLVED_AGREEMENT_ESTABLISHED for item in resolved)


@pytest.mark.parametrize("state,status", [
    (ProtocolState.PROPOSAL_REJECTED, TransitionStatus.RESOLVED_PROPOSAL_REJECTED),
    (ProtocolState.SOURCE_CLAIM_INVALID, TransitionStatus.RESOLVED_SOURCE_CLAIM_INVALID),
    (ProtocolState.PROTOCOL_BLOCKED, TransitionStatus.RESOLVED_PROTOCOL_BLOCKED),
    (ProtocolState.PROTOCOL_DISAGREEMENT, TransitionStatus.RESOLVED_PROTOCOL_DISAGREEMENT),
])
def test_protocol_resolution_categories(state, status):
    class Evaluation: pass
    epoch = emit(NegotiationDecisionEpochTracker())
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    opened = tracker.open_transition(epoch, NegotiationAction.RELINQUISH_CLAIM.value, snapshot())
    waiting = tracker.apply_action(opened.transition_id, 1.0, claim=claim(), regulatory_profile="DE_STVO")
    proposal_id = waiting.proposal_id; evaluation = Evaluation(); evaluation.state = state
    result = tracker.observe_protocol_evaluation(proposal_id, evaluation, 2.0)
    assert result[0].transition_status is status
    assert result[0].elapsed_seconds == 1.0


def test_negative_duration_and_duplicate_resolution_rejected():
    epoch = emit(NegotiationDecisionEpochTracker(), 2.0)
    tracker = NegotiationTransitionTracker(ClaimRelinquishmentProtocol())
    opened = tracker.open_transition(epoch, NegotiationAction.KEEP_CLAIM.value, snapshot())
    with pytest.raises(TransitionSemanticError, match="NEGATIVE_TRANSITION_DURATION"):
        tracker.apply_action(opened.transition_id, 1.0)
    resolved = tracker.apply_action(opened.transition_id, 2.0)
    with pytest.raises(TransitionSemanticError, match="DUPLICATE_TRANSITION_RESOLUTION"):
        tracker.resolve_transition(resolved.transition_id, resolved.transition_status, 2.0, "AGAIN")


def test_transition_has_no_reward_or_ppo_fields():
    fields = NegotiationTransitionTracker.__module__
    from negotiation_learning.transitions.models import NegotiationTransition
    names = NegotiationTransition.__dataclass_fields__
    assert "reward" not in names
    assert not ({"return_value", "advantage", "gae", "ppo_ratio"} & set(names))


def test_gnn_semantic_actor_and_critic_replay():
    import torch
    from negotiation_learning.ctde import (
        CentralizedNegotiationCritic, DecentralizedNegotiationActor,
        DecentralizedNegotiationResponseActor,
    )
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder
    from negotiation_learning.mappo_interface import RoleAwareNegotiationPolicy

    # TEST_ONLY_NON_OPERATIONAL_VALUE architecture dimensions.
    torch.manual_seed(7)
    gnn = EdgeAwareMPNNEncoder(8, 9, 5, 1)
    snap = snapshot()
    context1, output1, semantic1, protocol1 = reconstruct_actor_context(snap, gnn)
    context2, output2, semantic2, protocol2 = reconstruct_actor_context(snap, gnn)
    assert np.array_equal(semantic1.model_input, semantic2.model_input)
    assert protocol1 is protocol2 is None
    assert torch.equal(output1.ego_embedding, output2.ego_embedding)
    input_dim = context1.ego_embedding.numel() + context1.local_graph_embedding.numel() + context1.claim_or_proposal_representation.numel()
    policy = RoleAwareNegotiationPolicy(
        DecentralizedNegotiationActor(input_dim, 2),
        DecentralizedNegotiationResponseActor(input_dim + 18, 2),
    )
    forward1, dist1 = policy.distribution_for(context1)
    forward2, dist2 = policy.distribution_for(context2)
    assert torch.equal(forward1.unmasked_action_logits, forward2.unmasked_action_logits)
    assert torch.equal(dist1.probabilities, dist2.probabilities)
    assert torch.equal(context1.action_feasibility_mask, context2.action_feasibility_mask)

    centralized = CentralizedTrainingObservationSnapshot(
        ("critic", 1.0), 1.0, (snap,), ("B",), "SUM",
        {"scope": "TRAINING_ONLY"},
    )
    critic_input1 = reconstruct_critic_input(centralized, gnn)
    critic_input2 = reconstruct_critic_input(centralized, gnn)
    critic = CentralizedNegotiationCritic(critic_input1.shape[-1])
    assert torch.equal(critic_input1, critic_input2)
    assert torch.isfinite(critic(critic_input1)).all()


def test_actor_replay_signature_excludes_centralized_state():
    import inspect
    from negotiation_learning.transitions.replay import reconstruct_actor_context
    assert tuple(inspect.signature(reconstruct_actor_context).parameters) == (
        "snapshot", "gnn_encoder",
    )


def test_responder_proposal_protocol_and_actor_replay():
    import torch
    from negotiation_learning.ctde import (
        DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
    )
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder
    from negotiation_learning.mappo_interface import RoleAwareNegotiationPolicy

    protocol = ClaimRelinquishmentProtocol()
    proposal = protocol.create_proposal(
        claim(), 1.0, "DE_STVO",
        PolicyAuthority.POLICY_AUTHORIZED,
    )
    responder_snapshot = snapshot(
        "A", NegotiationDecisionRole.RESPONDER, proposal,
        ProtocolState.PROPOSAL_PENDING,
    )
    torch.manual_seed(8)
    gnn = EdgeAwareMPNNEncoder(8, 9, 5, 1)
    context1, output1, subject1, protocol1 = reconstruct_actor_context(responder_snapshot, gnn)
    context2, output2, subject2, protocol2 = reconstruct_actor_context(responder_snapshot, gnn)
    assert subject1.proposal_id == proposal.proposal_id
    assert np.array_equal(subject1.model_input, subject2.model_input)
    assert np.array_equal(protocol1.model_input, protocol2.model_input)
    assert torch.equal(output1.graph_embedding, output2.graph_embedding)
    responder_dim = sum(item.numel() for item in (
        context1.ego_embedding, context1.local_graph_embedding,
        context1.claim_or_proposal_representation,
        context1.protocol_state_representation,
    )) + 2
    policy = RoleAwareNegotiationPolicy(
        DecentralizedNegotiationActor(44, 2),
        DecentralizedNegotiationResponseActor(responder_dim, 2),
    )
    logits1, distribution1 = policy.distribution_for(context1)
    logits2, distribution2 = policy.distribution_for(context2)
    assert torch.equal(logits1.unmasked_action_logits, logits2.unmasked_action_logits)
    assert torch.equal(distribution1.probabilities, distribution2.probabilities)


def test_reject_consequence_and_simultaneous_proposal_isolation():
    protocol = ClaimRelinquishmentProtocol()
    proposal1 = protocol.create_proposal(claim(), 1.0, "DE_STVO", PolicyAuthority.POLICY_AUTHORIZED)
    other_claim = PrecedenceClaim(
        "D", "C", "C", "D", ClaimRole.EGO_IS_PRIORITY, (), (), (), 1.0,
        MappingProxyType({}),
    )
    proposal2 = protocol.create_proposal(other_claim, 1.0, "DE_STVO", PolicyAuthority.POLICY_AUTHORIZED)
    tracker = NegotiationTransitionTracker(protocol)
    tracker.associate_proposal(proposal1.proposal_id, ("proposer", 1))
    tracker.associate_proposal(proposal2.proposal_id, ("proposer", 2))
    assert tracker.associate_responder_decision(proposal1.proposal_id, ("responder", 1)) == ("proposer", 1)
    assert tracker.associate_responder_decision(proposal2.proposal_id, ("responder", 2)) == ("proposer", 2)
    assert tracker.proposal_to_responder[proposal1.proposal_id] != tracker.proposal_to_responder[proposal2.proposal_id]

    epochs = NegotiationDecisionEpochTracker()
    responder = emit(epochs, role=NegotiationDecisionRole.RESPONDER,
                     proposal=proposal1, parent=("proposer", 1))
    opened = tracker.open_transition(
        responder, NegotiationResponseAction.REJECT_RELINQUISHMENT.value,
        snapshot("A", NegotiationDecisionRole.RESPONDER, proposal1,
                 ProtocolState.PROPOSAL_PENDING),
    )
    waiting = tracker.apply_action(opened.transition_id, 1.0,
                                   proposal=proposal1, regulatory_profile="DE_STVO")
    response = waiting.immediate_action_consequence.semantic_message
    assert response.response.value == "REJECT"
    assert response.proposal_id == proposal1.proposal_id
