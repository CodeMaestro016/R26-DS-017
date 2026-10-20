"""Step 5E.2 independent per-claim grouping and response interface tests."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import NegotiationClaimBuilder, NegotiationStatus from negotiation_learning for the operations below.
from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
# Import ActorInputProvenance, DecentralizedNegotiationResponseActor, ResponseActorForwardInput from
# negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    ActorInputProvenance, DecentralizedNegotiationResponseActor,
    ResponseActorForwardInput,
)
# Import ClaimRelinquishmentProtocol, NegotiationProtocolBus, NegotiationResponseCandidateBuilder, ProtocolState
# from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus,
    NegotiationResponseCandidateBuilder, ProtocolState,
)

# Set (PROFILE, NOW) to a tuple containing the text 'DE_STVO_UNCONTROLLED_4WAY_V1', 1.0.
PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0
# Set TEST_ONLY_NON_OPERATIONAL_VALUE to 4.
TEST_ONLY_NON_OPERATIONAL_VALUE = 4


# Edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Input probability: the supplied probability.
# Output: result.
# Processing: select branches using the stated conditions.
def edge(source, target, probability=None):
    # Set result to a dictionary containing yielding_vehicle_id, priority_vehicle_id, timestamp,
    # regulatory_profile,...
    result = {
        # Store source under 'yielding_vehicle_id'.
        # Store target under 'priority_vehicle_id'.
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        # Store NOW under 'timestamp'.
        # Store PROFILE under 'regulatory_profile'.
        "timestamp": NOW, "regulatory_profile": PROFILE,
        # Store a tuple containing the text 'RULE' under 'applicable_rule_ids'.
        # Store a tuple containing the text 'SECTION' under 'source_sections'.
        "applicable_rule_ids": ("RULE",), "source_sections": ("SECTION",),
        # Store a tuple containing the text 'ZONE' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ("ZONE",),
        # Store a dictionary containing mandatory_regulatory_yield under 'hard_constraint_evidence'.
        # Store True under 'mandatory_regulatory_yield'.
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    # Run this branch when probability is a different object from None.
    if probability is not None:
        # Set result['intention_weighted_conflict_probability'] to probability.
        result["intention_weighted_conflict_probability"] = probability
    # Return result to the caller.
    return result


# Set CYCLE to a tuple built from a lazy sequence of the result of edge(a, b) for (a, b) in a tuple containing a
# tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple containing...
CYCLE = tuple(edge(a, b) for a, b in (
    # Include a tuple containing the text 'A', the text 'B' in this tuple.
    ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
))


# Proposal using the inputs and processing steps below.
# Input owner: the supplied owner.
# Input counterparty: the supplied counterparty.
# Input edges: the supplied edges.
# Output: the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE, claims.policy_authority).
def proposal(owner, counterparty, edges=CYCLE):
    # Set claims to the result of NegotiationClaimBuilder().build(owner, a dictionary containing
    # joint_precedence_edges,...).
    claims = NegotiationClaimBuilder().build(
        # Store edges under 'joint_precedence_edges'.
        owner, {"joint_precedence_edges": edges},
        # Supply NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value to NegotiationClaimBuilder().build.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        # Supply True to the enclosing expression.
        True, True,
    )
    # Set claim to the next item from a lazy sequence of item for item in claims.ego_precedence_claims; retain
    # entries satisfying item.counterparty_id equals counterparty.
    claim = next(item for item in claims.ego_precedence_claims
                 # Evaluate item.counterparty_id equals counterparty as part of the enclosing expression.
                 if item.counterparty_id == counterparty)
    # Return the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # claims.policy_authority) to the caller.
    return ClaimRelinquishmentProtocol.create_proposal(
        # Supply claims.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, claims.policy_authority,
    )


# Response using the inputs and processing steps below.
# Input item: the supplied item.
# Input value: the supplied value.
# Input profile: the supplied profile.
# Output: the result of ClaimRelinquishmentProtocol.create_response(item, item.receiver_id, value, NOW, profile).
def response(item, value, profile=PROFILE):
    # Return the result of ClaimRelinquishmentProtocol.create_response(item, item.receiver_id, value, NOW,
    # profile) to the caller.
    return ClaimRelinquishmentProtocol.create_response(
        # Supply item.receiver_id to ClaimRelinquishmentProtocol.create_response.
        item, item.receiver_id, value, NOW, profile,
    )


# Joint using the inputs and processing steps below.
# Input edges: the supplied edges.
# Input messages: the supplied messages.
# Input kwargs: the supplied kwargs.
# Output: the result of ClaimRelinquishmentProtocol().evaluate_all_claims(edges, messages, NOW, PROFILE).
def joint(edges, messages, **kwargs):
    # Return the result of ClaimRelinquishmentProtocol().evaluate_all_claims(edges, messages, NOW, PROFILE) to the
    # caller.
    return ClaimRelinquishmentProtocol().evaluate_all_claims(
        # Supply the unpacked keyword arguments as kwargs.
        edges, messages, NOW, PROFILE, **kwargs,
    )


# States using the inputs and processing steps below.
# Input snapshot: the supplied snapshot.
# Output: a dictionary of item.negotiated_agreement_overlay.original_claim mapped to item.state for item in
# snapshot.per_claim_evaluations.
def states(snapshot):
    # Return a dictionary of item.negotiated_agreement_overlay.original_claim mapped to item.state for item in
    # snapshot.per_claim_evaluations to the caller.
    return {item.negotiated_agreement_overlay.original_claim: item.state
            # Evaluate snapshot.per_claim_evaluations as part of the enclosing expression.
            for item in snapshot.per_claim_evaluations}


# Check two and four independent proposals are not disagreements using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_and_four_independent_proposals_are_not_disagreements():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set two to the result of joint(CYCLE, a tuple containing p1, p2).
    two = joint(CYCLE, (p1, p2))
    # Require the number of entries in two.per_claim_evaluations equals 2; otherwise raise AssertionError.
    assert len(two.per_claim_evaluations) == 2
    # Require the result of states(two) equals a dictionary of the supplied entries; otherwise raise
    # AssertionError.
    assert states(two) == {
        # Store ProtocolState.PROPOSAL_PENDING under ('D', 'A').
        ("D", "A"): ProtocolState.PROPOSAL_PENDING,
        # Store ProtocolState.PROPOSAL_PENDING under ('A', 'B').
        ("A", "B"): ProtocolState.PROPOSAL_PENDING,
    }
    # Set four to a tuple built from a lazy sequence of the result of proposal(owner, counterparty) for (owner,
    # counterparty) in a tuple containing a tuple containing 'A', 'D', a tuple containing 'B', 'A', a tuple
    # containing 'C', 'B', a tuple containing...
    four = tuple(proposal(owner, counterparty) for owner, counterparty in (
        # Include a tuple containing the text 'A', the text 'D' in this tuple.
        ("A", "D"), ("B", "A"), ("C", "B"), ("D", "C"),
    ))
    # Set result to the result of joint(CYCLE, four).
    result = joint(CYCLE, four)
    # Require the number of entries in result.per_claim_evaluations equals 4; otherwise raise AssertionError.
    assert len(result.per_claim_evaluations) == 4
    # Require result.protocol_disagreements equals an empty tuple; otherwise raise AssertionError.
    assert result.protocol_disagreements == ()


# Check two accepts remove only agreed claims from effective graph using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_accepts_remove_only_agreed_claims_from_effective_graph():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set result to the result of joint(CYCLE, a tuple containing p1, p2, the result of response(p1, the text
    # 'ACCEPT'), the result of...).
    result = joint(CYCLE, (p1, p2, response(p1, "ACCEPT"), response(p2, "ACCEPT")))
    # Require the number of entries in result.completed_agreements equals 2; otherwise raise AssertionError.
    assert len(result.completed_agreements) == 2
    # Require a set built from result.original_regulatory_precedence_graph equals a set built from a lazy sequence
    # of a tuple containing edge['yielding_vehicle_id'], edge['priority_vehicle_id'] for edge in CYCLE; otherwise
    # raise AssertionError.
    assert set(result.original_regulatory_precedence_graph) == set(
        # Evaluate a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id' as part of the
        # enclosing expression.
        (edge["yielding_vehicle_id"], edge["priority_vehicle_id"]) for edge in CYCLE
    )
    # Require result.effective_coordination_graph equals a tuple containing a tuple containing the text 'B', the
    # text 'C', a tuple containing the text 'C', the text 'D'; otherwise raise AssertionError.
    assert result.effective_coordination_graph == (("B", "C"), ("C", "D"))


# Apply 'second_response,expected' as a decorator to configure the following definition.
@pytest.mark.parametrize("second_response,expected", (
    # Include a tuple containing None, ProtocolState.PROPOSAL_PENDING in this tuple.
    (None, ProtocolState.PROPOSAL_PENDING),
    # Include a tuple containing the text 'REJECT', ProtocolState.PROPOSAL_REJECTED in this tuple.
    ("REJECT", ProtocolState.PROPOSAL_REJECTED),
))
# Check mixed outcomes remain independent using the setup, calls, and assertions below.
# Input second_response: the supplied second response.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_mixed_outcomes_remain_independent(second_response, expected):
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set messages to a list containing p1, p2, the result of response(p1, the text 'ACCEPT').
    messages = [p1, p2, response(p1, "ACCEPT")]
    # Run this branch when second_response.
    if second_response:
        # Append the result of response(p2, second_response) to messages.
        messages.append(response(p2, second_response))
    # Set result to the result of joint(CYCLE, messages).
    result = joint(CYCLE, messages)
    # Require states(result) at ('D', 'A') is the same object as ProtocolState.AGREEMENT_ESTABLISHED; otherwise
    # raise AssertionError.
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    # Require states(result) at ('A', 'B') is the same object as expected; otherwise raise AssertionError.
    assert states(result)[("A", "B")] is expected
    # Require a tuple containing the text 'D', the text 'A' does not belong to
    # result.effective_coordination_graph; otherwise raise AssertionError.
    assert ("D", "A") not in result.effective_coordination_graph
    # Require a tuple containing the text 'A', the text 'B' belongs to result.effective_coordination_graph;
    # otherwise raise AssertionError.
    assert ("A", "B") in result.effective_coordination_graph


# Check same proposal disagreement does not corrupt independent accept using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_same_proposal_disagreement_does_not_corrupt_independent_accept():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set result to the result of joint(CYCLE, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), the result of...).
    result = joint(CYCLE, (
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"), response(p1, "REJECT"),
        # Include the result of response(p2, the text 'ACCEPT') in this tuple.
        p2, response(p2, "ACCEPT"),
    ))
    # Require states(result) at ('D', 'A') is the same object as ProtocolState.PROTOCOL_DISAGREEMENT; otherwise
    # raise AssertionError.
    assert states(result)[("D", "A")] is ProtocolState.PROTOCOL_DISAGREEMENT
    # Require states(result) at ('A', 'B') is the same object as ProtocolState.AGREEMENT_ESTABLISHED; otherwise
    # raise AssertionError.
    assert states(result)[("A", "B")] is ProtocolState.AGREEMENT_ESTABLISHED


# Check duplicate proposal is one evaluation and same owner claims are distinct using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_duplicate_proposal_is_one_evaluation_and_same_owner_claims_are_distinct():
    # Set p to the result of proposal(the text 'A', the text 'D').
    p = proposal("A", "D")
    # Set bus to the result of NegotiationProtocolBus().
    # Call bus.begin_step with the supplied arguments.
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    # Call bus.publish with the supplied arguments.
    # Call bus.freeze_step with the supplied arguments.
    bus.publish(p); bus.publish(p); bus.freeze_step(NOW)
    # Require the number of entries in joint(CYCLE, bus.current_messages(NOW)).per_claim_evaluations equals 1;
    # otherwise raise AssertionError.
    assert len(joint(CYCLE, bus.current_messages(NOW)).per_claim_evaluations) == 1
    # Set multi to a tuple containing the result of edge(the text 'A', the text 'B'), the result of edge(the text
    # 'C', the text 'B').
    multi = (edge("A", "B"), edge("C", "B"))
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'B', the text 'A', multi), the result of
    # proposal(the text 'B', the text...
    p1, p2 = proposal("B", "A", multi), proposal("B", "C", multi)
    # Require the number of entries in joint(multi, (p1, p2)).per_claim_evaluations equals 2; otherwise raise
    # AssertionError.
    assert len(joint(multi, (p1, p2)).per_claim_evaluations) == 2


# Check order invariance for messages vehicles and claims using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_order_invariance_for_messages_vehicles_and_claims():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set messages to a tuple containing p1, the result of response(p1, the text 'ACCEPT'), p2, the result of
    # response(p2, the text 'REJECT').
    messages = (p1, response(p1, "ACCEPT"), p2, response(p2, "REJECT"))
    # Set first to the result of joint(CYCLE, messages).
    first = joint(CYCLE, messages)
    # Set second to the result of joint(a tuple built from the reverse traversal of CYCLE, a tuple built from the
    # reverse traversal of...).
    second = joint(tuple(reversed(CYCLE)), tuple(reversed(messages)))
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Set by_order to a dictionary of order mapped to a tuple built from a lazy sequence of the result of
    # joint(CYCLE, messages) for _ in order for order in a tuple containing a tuple containing the text 'A', the
    # text 'B', the text 'C', the text 'D', a tuple containing the text...
    by_order = {order: tuple(joint(CYCLE, messages) for _ in order)
                # Evaluate a tuple containing a tuple containing the text 'A', the text 'B', the text 'C', the
                # text 'D', a tuple containing the text... as part of the enclosing expression.
                for order in (("A", "B", "C", "D"), ("D", "C", "B", "A"))}
    # Require whether every item is true in a lazy sequence of item equals first for snapshots in values from
    # by_order; otherwise raise AssertionError.
    assert all(item == first for snapshots in by_order.values() for item in snapshots)


# Check orphan wrong response and disappeared claim are local only using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_orphan_wrong_response_and_disappeared_claim_are_local_only():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set wrong to the result of replace(the result of response(p2, the text 'ACCEPT')).
    wrong = replace(response(p2, "ACCEPT"),
                    # Supply proposal_id as a tuple containing NOW, the text 'X', the text 'Y', the text 'Y', the
                    # text 'X'.
                    proposal_id=(NOW, "X", "Y", "Y", "X"))
    # Set result to the result of joint(CYCLE, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), p2, wrong).
    result = joint(CYCLE, (p1, response(p1, "ACCEPT"), p2, wrong))
    # Require states(result) at ('D', 'A') is the same object as ProtocolState.AGREEMENT_ESTABLISHED; otherwise
    # raise AssertionError.
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    # Require states(result) at ('A', 'B') is the same object as ProtocolState.PROPOSAL_PENDING; otherwise raise
    # AssertionError.
    assert states(result)[("A", "B")] is ProtocolState.PROPOSAL_PENDING
    # Require whether any item is true in a lazy sequence of item.negotiated_agreement_overlay.diagnostic equals
    # the text 'RESPONSE_PROPOSAL_MISMATCH' for item in result.blocked_protocol_items; otherwise raise
    # AssertionError.
    assert any(item.negotiated_agreement_overlay.diagnostic ==
               # Evaluate result.blocked_protocol_items as part of the enclosing expression.
               "RESPONSE_PROPOSAL_MISMATCH" for item in result.blocked_protocol_items)
    # Set remaining to a tuple built from a lazy sequence of item for item in CYCLE; retain entries satisfying the
    # negation of item['yielding_vehicle_id'] == 'A' and item['priority_vehicle_id'] == 'B'.
    remaining = tuple(item for item in CYCLE if not (
        # Evaluate item at 'yielding_vehicle_id' equals the text 'A' and item at 'priority_vehicle_id' equals the
        # text 'B' as part of the enclosing expression.
        item["yielding_vehicle_id"] == "A" and item["priority_vehicle_id"] == "B"
    ))
    # Set missing to the result of joint(remaining, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), p2).
    missing = joint(remaining, (p1, response(p1, "ACCEPT"), p2))
    # Require states(missing) at ('D', 'A') is the same object as ProtocolState.AGREEMENT_ESTABLISHED; otherwise
    # raise AssertionError.
    assert states(missing)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    # Require states(missing) at ('A', 'B') is the same object as ProtocolState.SOURCE_CLAIM_INVALID; otherwise
    # raise AssertionError.
    assert states(missing)[("A", "B")] is ProtocolState.SOURCE_CLAIM_INVALID


# Check profile mismatch is claim local and global source block is global using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_profile_mismatch_is_claim_local_and_global_source_block_is_global():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set result to the result of joint(CYCLE, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), the result of...).
    result = joint(CYCLE, (
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"),
        # Supply regulatory_profile as the text 'OTHER'.
        replace(p2, regulatory_profile="OTHER"),
    ))
    # Require states(result) at ('D', 'A') is the same object as ProtocolState.AGREEMENT_ESTABLISHED; otherwise
    # raise AssertionError.
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    # Require states(result) at ('A', 'B') is the same object as ProtocolState.PROTOCOL_BLOCKED; otherwise raise
    # AssertionError.
    assert states(result)[("A", "B")] is ProtocolState.PROTOCOL_BLOCKED
    # Set globally_blocked to the result of joint(CYCLE, a tuple containing p1, p2).
    globally_blocked = joint(CYCLE, (p1, p2), source_consistent=False)
    # Require whether every item is true in a lazy sequence of item.state is the same object as
    # ProtocolState.PROTOCOL_BLOCKED for item in globally_blocked.per_claim_evaluations; otherwise raise
    # AssertionError.
    assert all(item.state is ProtocolState.PROTOCOL_BLOCKED
               # Evaluate globally_blocked.per_claim_evaluations as part of the enclosing expression.
               for item in globally_blocked.per_claim_evaluations)


# Check response candidate boolean mask and probability independence using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_response_candidate_boolean_mask_and_probability_independence():
    # Set p to the result of proposal(the text 'A', the text 'D').
    p = proposal("A", "D")
    # Set low to a tuple built from a lazy sequence of a dictionary built from item for item in CYCLE.
    low = tuple(dict(item, intention_weighted_conflict_probability=0.01)
                # Evaluate CYCLE as part of the enclosing expression.
                for item in CYCLE)
    # Set high to a tuple built from a lazy sequence of a dictionary built from item for item in CYCLE.
    high = tuple(dict(item, intention_weighted_conflict_probability=0.99)
                 # Evaluate CYCLE as part of the enclosing expression.
                 for item in CYCLE)
    # Set first to the result of NegotiationResponseCandidateBuilder.build(the text 'D', p, low, NOW, PROFILE).
    first = NegotiationResponseCandidateBuilder.build("D", p, low, NOW, PROFILE)
    # Set second to the result of NegotiationResponseCandidateBuilder.build(the text 'D', p, high, NOW, PROFILE).
    second = NegotiationResponseCandidateBuilder.build("D", p, high, NOW, PROFILE)
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Require first.action_feasibility_mask equals a tuple containing True, True; otherwise raise AssertionError.
    assert first.action_feasibility_mask == (True, True)
    # Require whether every item is true in a lazy sequence of the result of type(item) is the same object as bool
    # for item in first.action_feasibility_mask; otherwise raise AssertionError.
    assert all(type(item) is bool for item in first.action_feasibility_mask)
    # Set denied to the result of NegotiationResponseCandidateBuilder.build(the text 'C', p, CYCLE, NOW, PROFILE).
    denied = NegotiationResponseCandidateBuilder.build("C", p, CYCLE, NOW, PROFILE)
    # Require denied.action_feasibility_mask equals a tuple containing False, False; otherwise raise
    # AssertionError.
    assert denied.action_feasibility_mask == (False, False)


# Check response actor is decentralized untrained logits only using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_response_actor_is_decentralized_untrained_logits_only():
    # Set d to TEST_ONLY_NON_OPERATIONAL_VALUE.
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    # Set actor to the result of DecentralizedNegotiationResponseActor().
    actor = DecentralizedNegotiationResponseActor(input_dim=d * 4 + 2, action_count=2)
    # Set actor_input to the result of ResponseActorForwardInput(the text 'D', proposal('A', 'D').proposal_id, the
    # unpacked values from a lazy sequence of the...).
    actor_input = ResponseActorForwardInput(
        # Supply proposal('A', 'D').proposal_id to ResponseActorForwardInput.
        "D", proposal("A", "D").proposal_id,
        # Supply the unpacked values from a lazy sequence of the result of torch.ones(d) for _ in the integer
        # range defined by 4 to ResponseActorForwardInput.
        *(torch.ones(d) for _ in range(4)), torch.tensor([0.0, 1.0]),
        # Supply a tensor built from a list containing True, True to ResponseActorForwardInput.
        torch.tensor([True, True]),
        # Supply the result of ActorInputProvenance(the text 'EGO_LDM', the text 'CURRENT_SAME_STEP_V2V_GRAPH',
        # the text 'CURRENT_MPNN_ENCODING',...) to ResponseActorForwardInput.
        ActorInputProvenance("EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH",
                             "CURRENT_MPNN_ENCODING",
                             "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE"),
    )
    # Set output to the result of actor(actor_input).
    output = actor(actor_input)
    # Require output.unmasked_action_logits.shape equals a tuple containing 2; otherwise raise AssertionError.
    assert output.unmasked_action_logits.shape == (2,)
    # Require the negation of whether actor_input exposes the requested attribute; otherwise raise AssertionError.
    assert not hasattr(actor_input, "centralized_critic_input")
    # Merely changing untrained logits cannot create a protocol message/state.
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Call actor.logit_head.bias.copy_ with the supplied arguments.
        actor.logit_head.bias.copy_(torch.tensor([999.0, -999.0]))
    # Require joint(CYCLE, (proposal('A', 'D'),)).per_claim_evaluations[0].state is the same object as
    # ProtocolState.PROPOSAL_PENDING; otherwise raise AssertionError.
    assert joint(CYCLE, (proposal("A", "D"),)).per_claim_evaluations[0].state is (
        # Evaluate ProtocolState.PROPOSAL_PENDING as part of the enclosing expression.
        ProtocolState.PROPOSAL_PENDING
    )


# Check step 5e2 sources have no route truth control reward or training using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_step_5e2_sources_have_no_route_truth_control_reward_or_training():
    # Set root to Path(__file__).parents at 1.
    root = Path(__file__).parents[1]
    # Set paths to a list built from the result of (root / 'negotiation_learning' / 'protocol').glob(the text
    # '*.py').
    paths = list((root / "negotiation_learning" / "protocol").glob("*.py"))
    # Update paths to its current value plus a list containing root joined with the path segment 'negotiation_learning' divided by
    # the text 'ctde' joined with the path segment 'interfaces.py'.
    paths += [root / "negotiation_learning" / "ctde" / "interfaces.py"]
    # Set source to the result of '\n'.join(a lazy sequence of the result of path.read_text().lower() for path in
    # paths).
    source = "\n".join(path.read_text().lower() for path in paths)
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text
    # 'ground_truth_route_id', the text 'future_route',...
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "traci", "setspeed", "slowdown",
                 "setacceleration", "reward =", "torch.optim", "-1e9")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
