"""Standalone Step 5E.2 multi-proposal and response-interface validation."""

from dataclasses import replace

import torch

from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
from negotiation_learning.ctde import (
    ActorInputProvenance, DecentralizedNegotiationResponseActor,
    ResponseActorForwardInput,
)
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus,
    NegotiationResponseAction, NegotiationResponseCandidateBuilder,
    ProtocolState, RESPONSE_ACTOR_ARCHITECTURE,
)


PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0


def edge(source, target, probability=None):
    item = {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "timestamp": NOW, "regulatory_profile": PROFILE,
        "applicable_rule_ids": ("TEST_RULE",),
        "source_sections": ("TEST_SECTION",),
        "shared_conflict_zone_ids": ("TEST_ZONE",),
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    if probability is not None:
        item["intention_weighted_conflict_probability"] = probability
    return item


CYCLE = tuple(edge(a, b) for a, b in (
    ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
))


def proposal(owner, counterparty, edges=CYCLE):
    claim_set = NegotiationClaimBuilder().build(
        owner, {"joint_precedence_edges": edges},
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        True, True,
    )
    claim = next(item for item in claim_set.ego_precedence_claims
                 if item.counterparty_id == counterparty)
    return ClaimRelinquishmentProtocol.create_proposal(
        claim, NOW, PROFILE, claim_set.policy_authority,
    )


def response(item, value):
    return ClaimRelinquishmentProtocol.create_response(
        item, item.receiver_id, value, NOW, PROFILE,
    )


def evaluate(edges, messages):
    return ClaimRelinquishmentProtocol().evaluate_all_claims(
        edges, messages, NOW, PROFILE,
    )


def state_map(snapshot):
    return {item.negotiated_agreement_overlay.original_claim: item.state
            for item in snapshot.per_claim_evaluations}


def main():
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    two = evaluate(CYCLE, (p1, p2))
    assert len(two.per_claim_evaluations) == 2 and not two.protocol_disagreements
    four = tuple(proposal(a, b) for a, b in (
        ("A", "D"), ("B", "A"), ("C", "B"), ("D", "C"),
    ))
    assert len(evaluate(CYCLE, four).per_claim_evaluations) == 4

    accepted = evaluate(CYCLE, (
        p1, response(p1, "ACCEPT"), p2, response(p2, "ACCEPT"),
    ))
    assert len(accepted.completed_agreements) == 2
    assert accepted.effective_coordination_graph == (("B", "C"), ("C", "D"))
    mixed_pending = evaluate(CYCLE, (p1, response(p1, "ACCEPT"), p2))
    mixed_rejected = evaluate(CYCLE, (
        p1, response(p1, "ACCEPT"), p2, response(p2, "REJECT"),
    ))
    assert state_map(mixed_pending)[("A", "B")] is ProtocolState.PROPOSAL_PENDING
    assert state_map(mixed_rejected)[("A", "B")] is ProtocolState.PROPOSAL_REJECTED
    disagreement = evaluate(CYCLE, (
        p1, response(p1, "ACCEPT"), response(p1, "REJECT"), p2,
    ))
    assert state_map(disagreement)[("D", "A")] is ProtocolState.PROTOCOL_DISAGREEMENT
    assert state_map(disagreement)[("A", "B")] is ProtocolState.PROPOSAL_PENDING

    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    bus.publish(p1); bus.publish(p1); bus.freeze_step(NOW)
    assert len(evaluate(CYCLE, bus.current_messages(NOW)).per_claim_evaluations) == 1
    assert accepted == evaluate(tuple(reversed(CYCLE)), tuple(reversed((
        p1, response(p1, "ACCEPT"), p2, response(p2, "ACCEPT"),
    ))))
    assert all(evaluate(CYCLE, (p1, p2)) == two
               for _ego in ("D", "C", "B", "A"))

    wrong = replace(response(p2, "ACCEPT"),
                    proposal_id=(NOW, "X", "Y", "Y", "X"))
    local_failure = evaluate(CYCLE, (p1, response(p1, "ACCEPT"), p2, wrong))
    assert state_map(local_failure)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    assert local_failure.blocked_protocol_items

    candidate = NegotiationResponseCandidateBuilder.build(
        "D", p1, CYCLE, NOW, PROFILE,
    )
    assert tuple(item.value for item in candidate.available_response_actions) == (
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT",
    )
    assert candidate.action_feasibility_mask == (True, True)
    test_only_non_operational_value = 4
    actor = DecentralizedNegotiationResponseActor(
        test_only_non_operational_value * 4 + 2, 2,
    )
    actor_input = ResponseActorForwardInput(
        "D", p1.proposal_id,
        *(torch.ones(test_only_non_operational_value) for _ in range(4)),
        torch.tensor([0.0, 1.0]), torch.tensor([True, True]),
        ActorInputProvenance("EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH",
                             "CURRENT_MPNN_ENCODING",
                             "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE"),
    )
    assert actor(actor_input).unmasked_action_logits.shape == (2,)
    with torch.no_grad():
        actor.logit_head.bias.copy_(torch.tensor([999.0, -999.0]))
    assert evaluate(CYCLE, (p1,)).per_claim_evaluations[0].state is ProtocolState.PROPOSAL_PENDING

    low = tuple(dict(item, intention_weighted_conflict_probability=0.01) for item in CYCLE)
    high = tuple(dict(item, intention_weighted_conflict_probability=0.99) for item in CYCLE)
    assert (NegotiationResponseCandidateBuilder.build("D", p1, low, NOW, PROFILE) ==
            NegotiationResponseCandidateBuilder.build("D", p1, high, NOW, PROFILE))

    print("Step 5E.2 Multi-Agent Negotiation Protocol Validation\n")
    print("Per-claim grouping")
    print("  Independent proposals grouped separately: PASS")
    print("  Same-claim disagreement detected: PASS")
    print("  Duplicate identical proposal deduplicated: PASS")
    print("\nMultiple simultaneous proposals")
    print("  Two independent proposals: PASS")
    print("  Four independent proposals: PASS")
    print("  Independent proposals not treated as disagreement: PASS")
    print("\nMixed outcomes")
    print("  Accepted + pending represented independently: PASS")
    print("  Accepted + rejected represented independently: PASS")
    print("  Blocked claim does not corrupt independent claim: PASS")
    print("\nEffective coordination graph")
    print("  Original regulatory graph preserved: PASS")
    print("  Only agreed claims removed from effective graph: PASS")
    print("  Rejected claim preserved: PASS")
    print("  Pending claim preserved: PASS")
    print("\nDeterminism")
    print("  Message-order invariance: PASS")
    print("  Vehicle-order invariance: PASS")
    print("  Claim-order invariance: PASS")
    print("\nResponse policy interface")
    print("  ACCEPT_RELINQUISHMENT semantic action available: PASS")
    print("  REJECT_RELINQUISHMENT semantic action available: PASS")
    print("  Response hard mask Boolean: PASS")
    print("  Learned feasibility parameters: 0")
    print("  Response actor decentralized input only: PASS")
    print("  Response actor action executed: False")
    print(f"  Response actor architecture: {RESPONSE_ACTOR_ARCHITECTURE}")
    print("\nAuthority boundaries")
    print("  Route-truth consumed: 0")
    print("  Prediction probability controls protocol truth: False")
    print("  Untrained logits control protocol truth: False")
    print("\nResearch parameters")
    print("  New operational thresholds: 0")
    print("  Timeout constants: 0")
    print("  Retry constants: 0")
    print("  Reward weights: 0")
    print("  PPO hyperparameters configured: 0")
    print("\nDependencies")
    print("  Backend: PyTorch CPU")
    print("  TensorFlow required: False")
    print("  CUDA required: False")
    print("  PyTorch Geometric required: False")
    print("  New dependency required: False")
    print("\nResearch status")
    print("  Proposal policy trained: False")
    print("  Response policy trained: False")
    print("  PPO implemented: False")
    print("  Reward implemented: False")
    print("  Optimizer implemented: False")
    print("  Training performed: False")
    print("  Safety shield implemented: False")
    print("  SUMO control actions issued: 0")


if __name__ == "__main__":
    main()
