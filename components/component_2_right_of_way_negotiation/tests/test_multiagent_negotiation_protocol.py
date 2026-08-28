"""Step 5E.2 independent per-claim grouping and response interface tests."""

from dataclasses import replace
from pathlib import Path

import pytest
import torch

from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
from negotiation_learning.ctde import (
    ActorInputProvenance, DecentralizedNegotiationResponseActor,
    ResponseActorForwardInput,
)
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus,
    NegotiationResponseCandidateBuilder, ProtocolState,
)

PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0
TEST_ONLY_NON_OPERATIONAL_VALUE = 4


def edge(source, target, probability=None):
    result = {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "timestamp": NOW, "regulatory_profile": PROFILE,
        "applicable_rule_ids": ("RULE",), "source_sections": ("SECTION",),
        "shared_conflict_zone_ids": ("ZONE",),
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    if probability is not None:
        result["intention_weighted_conflict_probability"] = probability
    return result


CYCLE = tuple(edge(a, b) for a, b in (
    ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
))


def proposal(owner, counterparty, edges=CYCLE):
    claims = NegotiationClaimBuilder().build(
        owner, {"joint_precedence_edges": edges},
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        True, True,
    )
    claim = next(item for item in claims.ego_precedence_claims
                 if item.counterparty_id == counterparty)
    return ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, claims.policy_authority,
    )


def response(item, value, profile=PROFILE):
    return ClaimRelinquishmentProtocol.create_response(
        item, item.receiver_id, value, NOW, profile,
    )


def joint(edges, messages, **kwargs):
    return ClaimRelinquishmentProtocol().evaluate_all_claims(
        edges, messages, NOW, PROFILE, **kwargs,
    )


def states(snapshot):
    return {item.negotiated_agreement_overlay.original_claim: item.state
            for item in snapshot.per_claim_evaluations}


def test_two_and_four_independent_proposals_are_not_disagreements():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    two = joint(CYCLE, (p1, p2))
    assert len(two.per_claim_evaluations) == 2
    assert states(two) == {
        ("D", "A"): ProtocolState.PROPOSAL_PENDING,
        ("A", "B"): ProtocolState.PROPOSAL_PENDING,
    }
    four = tuple(proposal(owner, counterparty) for owner, counterparty in (
        ("A", "D"), ("B", "A"), ("C", "B"), ("D", "C"),
    ))
    result = joint(CYCLE, four)
    assert len(result.per_claim_evaluations) == 4
    assert result.protocol_disagreements == ()


def test_two_accepts_remove_only_agreed_claims_from_effective_graph():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    result = joint(CYCLE, (p1, p2, response(p1, "ACCEPT"), response(p2, "ACCEPT")))
    assert len(result.completed_agreements) == 2
    assert set(result.original_regulatory_precedence_graph) == set(
        (edge["yielding_vehicle_id"], edge["priority_vehicle_id"]) for edge in CYCLE
    )
    assert result.effective_coordination_graph == (("B", "C"), ("C", "D"))


@pytest.mark.parametrize("second_response,expected", (
    (None, ProtocolState.PROPOSAL_PENDING),
    ("REJECT", ProtocolState.PROPOSAL_REJECTED),
))
def test_mixed_outcomes_remain_independent(second_response, expected):
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    messages = [p1, p2, response(p1, "ACCEPT")]
    if second_response:
        messages.append(response(p2, second_response))
    result = joint(CYCLE, messages)
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    assert states(result)[("A", "B")] is expected
    assert ("D", "A") not in result.effective_coordination_graph
    assert ("A", "B") in result.effective_coordination_graph


def test_same_proposal_disagreement_does_not_corrupt_independent_accept():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    result = joint(CYCLE, (
        p1, response(p1, "ACCEPT"), response(p1, "REJECT"),
        p2, response(p2, "ACCEPT"),
    ))
    assert states(result)[("D", "A")] is ProtocolState.PROTOCOL_DISAGREEMENT
    assert states(result)[("A", "B")] is ProtocolState.AGREEMENT_ESTABLISHED


def test_duplicate_proposal_is_one_evaluation_and_same_owner_claims_are_distinct():
    p = proposal("A", "D")
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    bus.publish(p); bus.publish(p); bus.freeze_step(NOW)
    assert len(joint(CYCLE, bus.current_messages(NOW)).per_claim_evaluations) == 1
    multi = (edge("A", "B"), edge("C", "B"))
    p1, p2 = proposal("B", "A", multi), proposal("B", "C", multi)
    assert len(joint(multi, (p1, p2)).per_claim_evaluations) == 2


def test_order_invariance_for_messages_vehicles_and_claims():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    messages = (p1, response(p1, "ACCEPT"), p2, response(p2, "REJECT"))
    first = joint(CYCLE, messages)
    second = joint(tuple(reversed(CYCLE)), tuple(reversed(messages)))
    assert first == second
    by_order = {order: tuple(joint(CYCLE, messages) for _ in order)
                for order in (("A", "B", "C", "D"), ("D", "C", "B", "A"))}
    assert all(item == first for snapshots in by_order.values() for item in snapshots)


def test_orphan_wrong_response_and_disappeared_claim_are_local_only():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    wrong = replace(response(p2, "ACCEPT"),
                    proposal_id=(NOW, "X", "Y", "Y", "X"))
    result = joint(CYCLE, (p1, response(p1, "ACCEPT"), p2, wrong))
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    assert states(result)[("A", "B")] is ProtocolState.PROPOSAL_PENDING
    assert any(item.negotiated_agreement_overlay.diagnostic ==
               "RESPONSE_PROPOSAL_MISMATCH" for item in result.blocked_protocol_items)
    remaining = tuple(item for item in CYCLE if not (
        item["yielding_vehicle_id"] == "A" and item["priority_vehicle_id"] == "B"
    ))
    missing = joint(remaining, (p1, response(p1, "ACCEPT"), p2))
    assert states(missing)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    assert states(missing)[("A", "B")] is ProtocolState.SOURCE_CLAIM_INVALID


def test_profile_mismatch_is_claim_local_and_global_source_block_is_global():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    result = joint(CYCLE, (
        p1, response(p1, "ACCEPT"),
        replace(p2, regulatory_profile="OTHER"),
    ))
    assert states(result)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    assert states(result)[("A", "B")] is ProtocolState.PROTOCOL_BLOCKED
    globally_blocked = joint(CYCLE, (p1, p2), source_consistent=False)
    assert all(item.state is ProtocolState.PROTOCOL_BLOCKED
               for item in globally_blocked.per_claim_evaluations)


def test_response_candidate_boolean_mask_and_probability_independence():
    p = proposal("A", "D")
    low = tuple(dict(item, intention_weighted_conflict_probability=0.01)
                for item in CYCLE)
    high = tuple(dict(item, intention_weighted_conflict_probability=0.99)
                 for item in CYCLE)
    first = NegotiationResponseCandidateBuilder.build("D", p, low, NOW, PROFILE)
    second = NegotiationResponseCandidateBuilder.build("D", p, high, NOW, PROFILE)
    assert first == second
    assert first.action_feasibility_mask == (True, True)
    assert all(type(item) is bool for item in first.action_feasibility_mask)
    denied = NegotiationResponseCandidateBuilder.build("C", p, CYCLE, NOW, PROFILE)
    assert denied.action_feasibility_mask == (False, False)


def test_response_actor_is_decentralized_untrained_logits_only():
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    actor = DecentralizedNegotiationResponseActor(input_dim=d * 4 + 2, action_count=2)
    actor_input = ResponseActorForwardInput(
        "D", proposal("A", "D").proposal_id,
        *(torch.ones(d) for _ in range(4)), torch.tensor([0.0, 1.0]),
        torch.tensor([True, True]),
        ActorInputProvenance("EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH",
                             "CURRENT_MPNN_ENCODING",
                             "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE"),
    )
    output = actor(actor_input)
    assert output.unmasked_action_logits.shape == (2,)
    assert not hasattr(actor_input, "centralized_critic_input")
    # Merely changing untrained logits cannot create a protocol message/state.
    with torch.no_grad():
        actor.logit_head.bias.copy_(torch.tensor([999.0, -999.0]))
    assert joint(CYCLE, (proposal("A", "D"),)).per_claim_evaluations[0].state is (
        ProtocolState.PROPOSAL_PENDING
    )


def test_step_5e2_sources_have_no_route_truth_control_reward_or_training():
    root = Path(__file__).parents[1]
    paths = list((root / "negotiation_learning" / "protocol").glob("*.py"))
    paths += [root / "negotiation_learning" / "ctde" / "interfaces.py"]
    source = "\n".join(path.read_text().lower() for path in paths)
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "traci", "setspeed", "slowdown",
                 "setacceleration", "reward =", "torch.optim", "-1e9")
    assert not any(item in source for item in forbidden)
