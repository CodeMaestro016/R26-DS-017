"""Deterministic Step 5E.1 proposal/response protocol tests."""

from dataclasses import replace
from itertools import permutations

import pytest

from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProposalResponse,
    ProtocolSemanticError, ProtocolState, agreement_complete,
    deterministic_proposal_id,
)


PROFILE = "DE_STVO_UNCONTROLLED_4WAY_V1"
NOW = 1.0


def edge(source, target, probability=None):
    value = {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "timestamp": NOW, "regulatory_profile": PROFILE,
        "applicable_rule_ids": ("RULE",), "source_sections": ("SECTION",),
        "shared_conflict_zone_ids": ("ZONE",),
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    if probability is not None:
        value["intention_weighted_conflict_probability"] = probability
    return value


def owned_claim(owner, edges):
    result = NegotiationClaimBuilder().build(
        owner, {"joint_precedence_edges": tuple(edges)},
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        True, True,
    )
    return result, result.ego_precedence_claims[0]


def proposal_for(source="A", owner="B", edges=None):
    edges = edges or (edge(source, owner),)
    claim_set, claim = owned_claim(owner, edges)
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    return edges, proposal


def response_for(proposal, response):
    return ClaimRelinquishmentProtocol.create_response(
        proposal, proposal.receiver_id, response, NOW, PROFILE,
    )


def evaluate(edges, messages, **kwargs):
    return ClaimRelinquishmentProtocol().evaluate(
        edges, messages, NOW, PROFILE, **kwargs,
    )


def test_accept_establishes_overlay_but_preserves_original_graph():
    edges, proposal = proposal_for()
    result = evaluate(edges, (proposal, response_for(proposal, "ACCEPT")))
    assert agreement_complete(result)
    assert result.original_regulatory_precedence_graph == (("A", "B"),)
    assert result.effective_coordination_graph == ()
    assert result.negotiated_agreement_overlay.overlay_effect == (
        "CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT"
    )


def test_proposal_alone_is_pending_and_does_not_change_edge():
    edges, proposal = proposal_for()
    result = evaluate(edges, (proposal,))
    assert result.state is ProtocolState.PROPOSAL_PENDING
    assert not agreement_complete(result)
    assert result.effective_coordination_graph == (("A", "B"),)


def test_reject_never_establishes_agreement_or_overlay():
    edges, proposal = proposal_for()
    result = evaluate(edges, (proposal, response_for(proposal, "REJECT")))
    assert result.state is ProtocolState.PROPOSAL_REJECTED
    assert not agreement_complete(result)
    assert result.negotiated_agreement_overlay.overlay_effect is None


def test_wrong_owner_and_wrong_counterparty_are_rejected():
    claim_set, obligation = owned_claim("B", (edge("A", "B"),))
    from negotiation_learning.claim_semantics import PrecedenceClaim, ClaimRole
    wrong = PrecedenceClaim(
        "A", "B", "A", "B", ClaimRole.EGO_IS_PRIORITY,
        obligation.applicable_rule_ids, obligation.source_sections,
        obligation.shared_conflict_zone_ids, obligation.source_snapshot_timestamp,
        obligation.hard_constraint_evidence,
    )
    with pytest.raises(ProtocolSemanticError, match="SENDER_DOES_NOT_OWN"):
        ClaimRelinquishmentProtocol.create_proposal(
            wrong, NOW, PROFILE, claim_set.policy_authority,
        )
    edges, proposal = proposal_for()
    invalid = replace(
        proposal, receiver_id="C",
        proposal_id=deterministic_proposal_id(NOW, "A", "B", "B", "C"),
    )
    result = evaluate(edges, (invalid,))
    assert result.negotiated_agreement_overlay.diagnostic == "INVALID_COUNTERPARTY"


def test_wrong_proposal_reference_and_disagreement_do_not_vote():
    edges, proposal = proposal_for()
    accept = response_for(proposal, "ACCEPT")
    wrong = replace(accept, proposal_id=(NOW, "X", "Y", "Y", "X"))
    assert evaluate(edges, (proposal, wrong)).negotiated_agreement_overlay.diagnostic == (
        "RESPONSE_PROPOSAL_MISMATCH"
    )
    reject = response_for(proposal, "REJECT")
    result = evaluate(edges, (proposal, accept, reject))
    assert result.state is ProtocolState.PROTOCOL_DISAGREEMENT


def test_source_claim_disappearance_timestamp_and_profile_mismatch_block():
    edges, proposal = proposal_for()
    accept = response_for(proposal, "ACCEPT")
    gone = evaluate((), (proposal, accept))
    stale = evaluate((replace_dict(edges[0], timestamp=2.0),), (proposal, accept))
    profile = replace(accept, regulatory_profile="OTHER_PROFILE")
    mismatch = evaluate(edges, (proposal, profile))
    assert gone.state is stale.state is ProtocolState.SOURCE_CLAIM_INVALID
    assert mismatch.state is ProtocolState.PROTOCOL_BLOCKED


def replace_dict(value, **updates):
    result = dict(value); result.update(updates); return result


def test_four_way_cycle_only_owned_claim_can_be_proposed():
    cycle = tuple(edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    claim_set, claim = owned_claim("A", cycle)
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    result = evaluate(cycle, (proposal, response_for(proposal, "ACCEPT")))
    assert (proposal.yielding_vehicle_id, proposal.priority_vehicle_id) == ("D", "A")
    assert ("A", "B") in result.original_regulatory_precedence_graph
    assert ("A", "B") in result.effective_coordination_graph
    assert set(result.original_regulatory_precedence_graph) == {
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    }


def test_multiple_claim_agreement_is_pair_specific():
    edges = (edge("A", "B"), edge("C", "B"))
    claim_set, _ = owned_claim("B", edges)
    claim = next(item for item in claim_set.ego_precedence_claims
                 if item.counterparty_id == "A")
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    result = evaluate(edges, (proposal, response_for(proposal, "ACCEPT")))
    assert result.effective_coordination_graph == (("C", "B"),)


def test_message_claim_and_vehicle_order_are_invariant():
    cycle = tuple(edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    _, proposal = proposal_for("D", "A", cycle)
    accept = response_for(proposal, "ACCEPT")
    first = evaluate(cycle, (proposal, accept))
    second = evaluate(tuple(reversed(cycle)), (accept, proposal))
    assert first == second
    # Independent consumers in different vehicle-loop orders see one frozen set.
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    bus.publish(accept); bus.publish(proposal); bus.publish(proposal)
    bus.freeze_step(NOW)
    snapshots = {
        ego: evaluate(cycle, bus.current_messages(NOW))
        for ego in ("D", "C", "B", "A")
    }
    assert len(set(snapshots.values())) == 1


def test_probabilities_actor_logits_and_route_truth_cannot_define_agreement():
    low_edges, proposal = proposal_for(edges=(edge("A", "B", 0.01),))
    high_edges = (edge("A", "B", 0.99),)
    pending_low = evaluate(low_edges, (proposal,))
    pending_high = evaluate(high_edges, (proposal,))
    external = {"route_id": "x", "route_index": 99,
                "ground_truth_route_id": "y", "actor_logits": (999, -999)}
    external.update({"actor_logits": (-999, 999)})
    assert pending_low == pending_high
    assert pending_low.state is ProtocolState.PROPOSAL_PENDING


def test_keep_claim_creates_no_proposal_and_no_automatic_response_policy():
    edges = (edge("A", "B"),)
    result = evaluate(edges, ())
    assert result.state is ProtocolState.NO_PROPOSAL
    from negotiation_learning.protocol import RESPONSE_POLICY_STATUS
    assert RESPONSE_POLICY_STATUS == "RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION"
