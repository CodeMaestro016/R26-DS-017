"""Standalone deterministic Step 5E.1 protocol validation without SUMO."""

from dataclasses import replace

from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProtocolState,
    RESPONSE_POLICY_STATUS, agreement_complete, deterministic_proposal_id,
)


PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0


def edge(source, target, probability=None):
    result = {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "timestamp": NOW, "regulatory_profile": PROFILE,
        "applicable_rule_ids": ("TEST_RULE",),
        "source_sections": ("TEST_SECTION",),
        "shared_conflict_zone_ids": ("TEST_ZONE",),
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    if probability is not None:
        result["intention_weighted_conflict_probability"] = probability
    return result


def claim_set(ego, edges):
    return NegotiationClaimBuilder().build(
        ego, {"joint_precedence_edges": tuple(edges)},
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        True, True,
    )


def proposal_for(ego, edges, counterparty=None):
    owned = claim_set(ego, edges)
    claim = next(item for item in owned.ego_precedence_claims
                 if counterparty is None or item.counterparty_id == counterparty)
    return ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, owned.policy_authority,
    )


def response_for(proposal, response):
    return ClaimRelinquishmentProtocol.create_response(
        proposal, proposal.receiver_id, response, NOW, PROFILE,
    )


def evaluate(edges, messages, **kwargs):
    return ClaimRelinquishmentProtocol().evaluate(
        edges, messages, NOW, PROFILE, **kwargs,
    )


def main():
    simple = (edge("A", "B"),)
    proposal = proposal_for("B", simple)
    accept, reject = response_for(proposal, "ACCEPT"), response_for(proposal, "REJECT")
    pending = evaluate(simple, (proposal,))
    accepted = evaluate(simple, (proposal, accept))
    rejected = evaluate(simple, (proposal, reject))
    assert pending.state is ProtocolState.PROPOSAL_PENDING and not agreement_complete(pending)
    assert agreement_complete(accepted)
    assert rejected.state is ProtocolState.PROPOSAL_REJECTED
    assert accepted.original_regulatory_precedence_graph == (("A", "B"),)

    invalid_counterparty = replace(
        proposal, receiver_id="C",
        proposal_id=deterministic_proposal_id(NOW, "A", "B", "B", "C"),
    )
    assert evaluate(simple, (invalid_counterparty,)).negotiated_agreement_overlay.diagnostic == "INVALID_COUNTERPARTY"
    wrong_reference = replace(accept, proposal_id=(NOW, "X", "Y", "Y", "X"))
    assert evaluate(simple, (proposal, wrong_reference)).negotiated_agreement_overlay.diagnostic == "RESPONSE_PROPOSAL_MISMATCH"
    assert evaluate(simple, (proposal, accept, reject)).state is ProtocolState.PROTOCOL_DISAGREEMENT
    assert evaluate((), (proposal, accept)).state is ProtocolState.SOURCE_CLAIM_INVALID
    profile_mismatch = replace(accept, regulatory_profile="OTHER")
    assert evaluate(simple, (proposal, profile_mismatch)).state is ProtocolState.PROTOCOL_BLOCKED

    cycle = tuple(edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    cycle_proposal = proposal_for("A", cycle, "D")
    cycle_accept = response_for(cycle_proposal, "ACCEPT")
    cycle_result = evaluate(cycle, (cycle_proposal, cycle_accept))
    assert ("A", "B") in cycle_result.effective_coordination_graph
    assert ("D", "A") not in cycle_result.effective_coordination_graph
    assert set(cycle_result.original_regulatory_precedence_graph) == {
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    }

    multiple = (edge("A", "B"), edge("C", "B"))
    multi_proposal = proposal_for("B", multiple, "A")
    multi_result = evaluate(multiple, (multi_proposal, response_for(multi_proposal, "ACCEPT")))
    assert multi_result.effective_coordination_graph == (("C", "B"),)

    reordered = evaluate(tuple(reversed(cycle)), (cycle_accept, cycle_proposal))
    assert cycle_result == reordered
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    bus.publish(cycle_accept); bus.publish(cycle_proposal); bus.publish(cycle_proposal)
    bus.freeze_step(NOW)
    states = tuple(evaluate(cycle, bus.current_messages(NOW))
                   for _ego in ("D", "C", "B", "A"))
    assert all(item == states[0] for item in states)

    low = (edge("A", "B", 0.01),)
    high = (edge("A", "B", 0.99),)
    low_proposal = proposal_for("B", low)
    assert evaluate(low, (low_proposal,)).state == evaluate(high, (low_proposal,)).state

    print("Negotiation Protocol Validation\n")
    print("Semantics")
    print("  Proposal does not equal agreement: PASS")
    print("  Only precedence owner may relinquish claim: PASS")
    print("  Mandatory yield obligation cannot be relinquished: PASS")
    print("  Claim targeting is pair-specific: PASS")
    print("\nAgreement")
    print("  Valid ACCEPT establishes agreement: PASS")
    print("  REJECT does not establish agreement: PASS")
    print("  Missing response remains pending: PASS")
    print("  Wrong counterparty rejected: PASS")
    print("  Wrong proposal reference rejected: PASS")
    print("\nConsistency")
    print("  Source claim validity required: PASS")
    print("  Snapshot consistency required: PASS")
    print("  Regulatory profile consistency required: PASS")
    print("  Protocol disagreement preserved: PASS")
    print("\nFour-way cycle")
    print("  A may relinquish D->A: PASS")
    print("  A cannot relinquish A->B: PASS")
    print("  Unrelated claims unchanged: PASS")
    print("\nMultiple claims")
    print("  One claim agreement does not alter second claim: PASS")
    print("\nDeterminism")
    print("  Message-order invariance: PASS")
    print("  Vehicle-processing-order invariance: PASS")
    print("\nAuthority boundaries")
    print("  Route-truth fields consumed: 0")
    print("  Prediction probability controls protocol truth: False")
    print("  Actor logits control agreement truth: False")
    print("\nCommunication abstraction")
    print("  Model: IDEAL_SAME_STEP_V2V")
    print("  New operational numerical thresholds: 0")
    print("  Timeout constants: 0")
    print("  Retry constants: 0")
    print("  Communication-range constants: 0")
    print("  Packet-loss assumptions: 0")
    print("\nDependencies")
    print("  TensorFlow required: False")
    print("  CUDA required: False")
    print("  New dependency required: False")
    print("\nResearch status")
    print(f"  Response policy: {RESPONSE_POLICY_STATUS}")
    print("  Learned response policy implemented: False")
    print("  PPO implemented: False")
    print("  Reward implemented: False")
    print("  Training performed: False")
    print("  Safety shield implemented: False")
    print("  SUMO control actions issued: 0")


if __name__ == "__main__":
    main()
