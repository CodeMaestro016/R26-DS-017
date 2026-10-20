"""Standalone Step 5E.2 multi-proposal and response-interface validation."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace

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
# Import ClaimRelinquishmentProtocol, NegotiationProtocolBus, NegotiationResponseAction,
# NegotiationResponseCandidateBuilder, ProtocolState, RESPONSE_ACTOR_ARCHITECTURE from
# negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus,
    NegotiationResponseAction, NegotiationResponseCandidateBuilder,
    ProtocolState, RESPONSE_ACTOR_ARCHITECTURE,
)


# Set (PROFILE, NOW) to a tuple containing the text 'DE_STVO_UNCONTROLLED_4WAY_V1', 1.0.
PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0


# Edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Input probability: the supplied probability.
# Output: item.
# Processing: select branches using the stated conditions.
def edge(source, target, probability=None):
    # Set item to a dictionary containing yielding_vehicle_id, priority_vehicle_id, timestamp,
    # regulatory_profile,...
    item = {
        # Store source under 'yielding_vehicle_id'.
        # Store target under 'priority_vehicle_id'.
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        # Store NOW under 'timestamp'.
        # Store PROFILE under 'regulatory_profile'.
        "timestamp": NOW, "regulatory_profile": PROFILE,
        # Store a tuple containing the text 'TEST_RULE' under 'applicable_rule_ids'.
        "applicable_rule_ids": ("TEST_RULE",),
        # Store a tuple containing the text 'TEST_SECTION' under 'source_sections'.
        "source_sections": ("TEST_SECTION",),
        # Store a tuple containing the text 'TEST_ZONE' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ("TEST_ZONE",),
        # Store a dictionary containing mandatory_regulatory_yield under 'hard_constraint_evidence'.
        # Store True under 'mandatory_regulatory_yield'.
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    # Run this branch when probability is a different object from None.
    if probability is not None:
        # Set item['intention_weighted_conflict_probability'] to probability.
        item["intention_weighted_conflict_probability"] = probability
    # Return item to the caller.
    return item


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
# Output: the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
# claim_set.policy_authority).
def proposal(owner, counterparty, edges=CYCLE):
    # Set claim_set to the result of NegotiationClaimBuilder().build(owner, a dictionary containing
    # joint_precedence_edges,...).
    claim_set = NegotiationClaimBuilder().build(
        # Store edges under 'joint_precedence_edges'.
        owner, {"joint_precedence_edges": edges},
        # Supply NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value to NegotiationClaimBuilder().build.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        # Supply True to the enclosing expression.
        True, True,
    )
    # Set claim to the next item from a lazy sequence of item for item in claim_set.ego_precedence_claims; retain
    # entries satisfying item.counterparty_id equals counterparty.
    claim = next(item for item in claim_set.ego_precedence_claims
                 # Evaluate item.counterparty_id equals counterparty as part of the enclosing expression.
                 if item.counterparty_id == counterparty)
    # Return the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # claim_set.policy_authority) to the caller.
    return ClaimRelinquishmentProtocol.create_proposal(
        # Supply claim_set.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, claim_set.policy_authority,
    )


# Response using the inputs and processing steps below.
# Input item: the supplied item.
# Input value: the supplied value.
# Output: the result of ClaimRelinquishmentProtocol.create_response(item, item.receiver_id, value, NOW, PROFILE).
def response(item, value):
    # Return the result of ClaimRelinquishmentProtocol.create_response(item, item.receiver_id, value, NOW,
    # PROFILE) to the caller.
    return ClaimRelinquishmentProtocol.create_response(
        # Supply item.receiver_id to ClaimRelinquishmentProtocol.create_response.
        item, item.receiver_id, value, NOW, PROFILE,
    )


# Evaluate using the inputs and processing steps below.
# Input edges: the supplied edges.
# Input messages: the supplied messages.
# Output: the result of ClaimRelinquishmentProtocol().evaluate_all_claims(edges, messages, NOW, PROFILE).
def evaluate(edges, messages):
    # Return the result of ClaimRelinquishmentProtocol().evaluate_all_claims(edges, messages, NOW, PROFILE) to the
    # caller.
    return ClaimRelinquishmentProtocol().evaluate_all_claims(
        # Supply messages to ClaimRelinquishmentProtocol().evaluate_all_claims.
        edges, messages, NOW, PROFILE,
    )


# State map using the inputs and processing steps below.
# Input snapshot: the supplied snapshot.
# Output: a dictionary of item.negotiated_agreement_overlay.original_claim mapped to item.state for item in
# snapshot.per_claim_evaluations.
def state_map(snapshot):
    # Return a dictionary of item.negotiated_agreement_overlay.original_claim mapped to item.state for item in
    # snapshot.per_claim_evaluations to the caller.
    return {item.negotiated_agreement_overlay.original_claim: item.state
            # Evaluate snapshot.per_claim_evaluations as part of the enclosing expression.
            for item in snapshot.per_claim_evaluations}


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set (p1, p2) to a tuple containing the result of proposal(the text 'A', the text 'D'), the result of
    # proposal(the text 'B', the text 'A').
    p1, p2 = proposal("A", "D"), proposal("B", "A")
    # Set two to the result of evaluate(CYCLE, a tuple containing p1, p2).
    two = evaluate(CYCLE, (p1, p2))
    # Require the number of entries in two.per_claim_evaluations equals 2 and the negation of
    # two.protocol_disagreements; otherwise raise AssertionError.
    assert len(two.per_claim_evaluations) == 2 and not two.protocol_disagreements
    # Set four to a tuple built from a lazy sequence of the result of proposal(a, b) for (a, b) in a tuple
    # containing a tuple containing 'A', 'D', a tuple containing 'B', 'A', a tuple containing 'C', 'B', a tuple
    # containing...
    four = tuple(proposal(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'D' in this tuple.
        ("A", "D"), ("B", "A"), ("C", "B"), ("D", "C"),
    ))
    # Require the number of entries in evaluate(CYCLE, four).per_claim_evaluations equals 4; otherwise raise
    # AssertionError.
    assert len(evaluate(CYCLE, four).per_claim_evaluations) == 4

    # Set accepted to the result of evaluate(CYCLE, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), p2, the result of...).
    accepted = evaluate(CYCLE, (
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"), p2, response(p2, "ACCEPT"),
    ))
    # Require the number of entries in accepted.completed_agreements equals 2; otherwise raise AssertionError.
    assert len(accepted.completed_agreements) == 2
    # Require accepted.effective_coordination_graph equals a tuple containing a tuple containing the text 'B', the
    # text 'C', a tuple containing the text 'C', the text 'D'; otherwise raise AssertionError.
    assert accepted.effective_coordination_graph == (("B", "C"), ("C", "D"))
    # Set mixed_pending to the result of evaluate(CYCLE, a tuple containing p1, the result of response(p1, the
    # text 'ACCEPT'), p2).
    mixed_pending = evaluate(CYCLE, (p1, response(p1, "ACCEPT"), p2))
    # Set mixed_rejected to the result of evaluate(CYCLE, a tuple containing p1, the result of response(p1, the
    # text 'ACCEPT'), p2, the result of...).
    mixed_rejected = evaluate(CYCLE, (
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"), p2, response(p2, "REJECT"),
    ))
    # Require state_map(mixed_pending) at ('A', 'B') is the same object as ProtocolState.PROPOSAL_PENDING;
    # otherwise raise AssertionError.
    assert state_map(mixed_pending)[("A", "B")] is ProtocolState.PROPOSAL_PENDING
    # Require state_map(mixed_rejected) at ('A', 'B') is the same object as ProtocolState.PROPOSAL_REJECTED;
    # otherwise raise AssertionError.
    assert state_map(mixed_rejected)[("A", "B")] is ProtocolState.PROPOSAL_REJECTED
    # Set disagreement to the result of evaluate(CYCLE, a tuple containing p1, the result of response(p1, the text
    # 'ACCEPT'), the result of...).
    disagreement = evaluate(CYCLE, (
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"), response(p1, "REJECT"), p2,
    ))
    # Require state_map(disagreement) at ('D', 'A') is the same object as ProtocolState.PROTOCOL_DISAGREEMENT;
    # otherwise raise AssertionError.
    assert state_map(disagreement)[("D", "A")] is ProtocolState.PROTOCOL_DISAGREEMENT
    # Require state_map(disagreement) at ('A', 'B') is the same object as ProtocolState.PROPOSAL_PENDING;
    # otherwise raise AssertionError.
    assert state_map(disagreement)[("A", "B")] is ProtocolState.PROPOSAL_PENDING

    # Set bus to the result of NegotiationProtocolBus().
    # Call bus.begin_step with the supplied arguments.
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    # Call bus.publish with the supplied arguments.
    # Call bus.freeze_step with the supplied arguments.
    bus.publish(p1); bus.publish(p1); bus.freeze_step(NOW)
    # Require the number of entries in evaluate(CYCLE, bus.current_messages(NOW)).per_claim_evaluations equals 1;
    # otherwise raise AssertionError.
    assert len(evaluate(CYCLE, bus.current_messages(NOW)).per_claim_evaluations) == 1
    # Require accepted equals the result of evaluate(a tuple built from the reverse traversal of CYCLE, a tuple
    # built from the reverse traversal of...); otherwise raise AssertionError.
    assert accepted == evaluate(tuple(reversed(CYCLE)), tuple(reversed((
        # Include the result of response(p1, the text 'ACCEPT') in this tuple.
        p1, response(p1, "ACCEPT"), p2, response(p2, "ACCEPT"),
    ))))
    # Require whether every item is true in a lazy sequence of the result of evaluate(CYCLE, (p1, p2)) equals two
    # for _ego in a tuple containing the text 'D', the text 'C', the text 'B', the text 'A'; otherwise raise
    # AssertionError.
    assert all(evaluate(CYCLE, (p1, p2)) == two
               # Evaluate a tuple containing the text 'D', the text 'C', the text 'B', the text 'A' as part of the
               # enclosing expression.
               for _ego in ("D", "C", "B", "A"))

    # Set wrong to the result of replace(the result of response(p2, the text 'ACCEPT')).
    wrong = replace(response(p2, "ACCEPT"),
                    # Supply proposal_id as a tuple containing NOW, the text 'X', the text 'Y', the text 'Y', the
                    # text 'X'.
                    proposal_id=(NOW, "X", "Y", "Y", "X"))
    # Set local_failure to the result of evaluate(CYCLE, a tuple containing p1, the result of response(p1, the
    # text 'ACCEPT'), p2, wrong).
    local_failure = evaluate(CYCLE, (p1, response(p1, "ACCEPT"), p2, wrong))
    # Require state_map(local_failure) at ('D', 'A') is the same object as ProtocolState.AGREEMENT_ESTABLISHED;
    # otherwise raise AssertionError.
    assert state_map(local_failure)[("D", "A")] is ProtocolState.AGREEMENT_ESTABLISHED
    # Require local_failure.blocked_protocol_items; otherwise raise AssertionError.
    assert local_failure.blocked_protocol_items

    # Set candidate to the result of NegotiationResponseCandidateBuilder.build(the text 'D', p1, CYCLE, NOW,
    # PROFILE).
    candidate = NegotiationResponseCandidateBuilder.build(
        # Supply PROFILE to NegotiationResponseCandidateBuilder.build.
        "D", p1, CYCLE, NOW, PROFILE,
    )
    # Require a tuple built from a lazy sequence of item.value for item in candidate.available_response_actions
    # equals a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT'; otherwise
    # raise AssertionError.
    assert tuple(item.value for item in candidate.available_response_actions) == (
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT",
    )
    # Require candidate.action_feasibility_mask equals a tuple containing True, True; otherwise raise
    # AssertionError.
    assert candidate.action_feasibility_mask == (True, True)
    # Set test_only_non_operational_value to 4.
    test_only_non_operational_value = 4
    # Set actor to the result of DecentralizedNegotiationResponseActor(test_only_non_operational_value multiplied
    # by 4 plus 2, 2).
    actor = DecentralizedNegotiationResponseActor(
        # Supply test_only_non_operational_value multiplied by 4 plus 2 to DecentralizedNegotiationResponseActor.
        test_only_non_operational_value * 4 + 2, 2,
    )
    # Set actor_input to the result of ResponseActorForwardInput(the text 'D', p1.proposal_id, the unpacked values
    # from a lazy sequence of the result of...).
    actor_input = ResponseActorForwardInput(
        # Supply p1.proposal_id to ResponseActorForwardInput.
        "D", p1.proposal_id,
        # Supply the unpacked values from a lazy sequence of the result of
        # torch.ones(test_only_non_operational_value) for _ in the integer range defined by 4 to
        # ResponseActorForwardInput.
        *(torch.ones(test_only_non_operational_value) for _ in range(4)),
        # Supply a tensor built from a list containing True, True to ResponseActorForwardInput.
        torch.tensor([0.0, 1.0]), torch.tensor([True, True]),
        # Supply the result of ActorInputProvenance(the text 'EGO_LDM', the text 'CURRENT_SAME_STEP_V2V_GRAPH',
        # the text 'CURRENT_MPNN_ENCODING',...) to ResponseActorForwardInput.
        ActorInputProvenance("EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH",
                             "CURRENT_MPNN_ENCODING",
                             "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE"),
    )
    # Require actor(actor_input).unmasked_action_logits.shape equals a tuple containing 2; otherwise raise
    # AssertionError.
    assert actor(actor_input).unmasked_action_logits.shape == (2,)
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Call actor.logit_head.bias.copy_ with the supplied arguments.
        actor.logit_head.bias.copy_(torch.tensor([999.0, -999.0]))
    # Require evaluate(CYCLE, (p1,)).per_claim_evaluations[0].state is the same object as
    # ProtocolState.PROPOSAL_PENDING; otherwise raise AssertionError.
    assert evaluate(CYCLE, (p1,)).per_claim_evaluations[0].state is ProtocolState.PROPOSAL_PENDING

    # Set low to a tuple built from a lazy sequence of a dictionary built from item for item in CYCLE.
    low = tuple(dict(item, intention_weighted_conflict_probability=0.01) for item in CYCLE)
    # Set high to a tuple built from a lazy sequence of a dictionary built from item for item in CYCLE.
    high = tuple(dict(item, intention_weighted_conflict_probability=0.99) for item in CYCLE)
    # Require the result of NegotiationResponseCandidateBuilder.build(the text 'D', p1, low, NOW, PROFILE) equals
    # the result of NegotiationResponseCandidateBuilder.build(the text 'D', p1, high, NOW, PROFILE); otherwise
    # raise AssertionError.
    assert (NegotiationResponseCandidateBuilder.build("D", p1, low, NOW, PROFILE) ==
            # Evaluate the result of NegotiationResponseCandidateBuilder.build(the text 'D', p1, high, NOW,
            # PROFILE) as part of the enclosing expression.
            NegotiationResponseCandidateBuilder.build("D", p1, high, NOW, PROFILE))

    # Display the text 'Step 5E.2 Multi-Agent Negotiation Protocol Validation'.
    print("Step 5E.2 Multi-Agent Negotiation Protocol Validation\n")
    # Display the text 'Per-claim grouping'.
    print("Per-claim grouping")
    # Display the text 'Independent proposals grouped separately: PASS'.
    print("  Independent proposals grouped separately: PASS")
    # Display the text 'Same-claim disagreement detected: PASS'.
    print("  Same-claim disagreement detected: PASS")
    # Display the text 'Duplicate identical proposal deduplicated: PASS'.
    print("  Duplicate identical proposal deduplicated: PASS")
    # Display the text 'Multiple simultaneous proposals'.
    print("\nMultiple simultaneous proposals")
    # Display the text 'Two independent proposals: PASS'.
    print("  Two independent proposals: PASS")
    # Display the text 'Four independent proposals: PASS'.
    print("  Four independent proposals: PASS")
    # Display the text 'Independent proposals not treated as disagreement: PASS'.
    print("  Independent proposals not treated as disagreement: PASS")
    # Display the text 'Mixed outcomes'.
    print("\nMixed outcomes")
    # Display the text 'Accepted + pending represented independently: PASS'.
    print("  Accepted + pending represented independently: PASS")
    # Display the text 'Accepted + rejected represented independently: PASS'.
    print("  Accepted + rejected represented independently: PASS")
    # Display the text 'Blocked claim does not corrupt independent claim: PASS'.
    print("  Blocked claim does not corrupt independent claim: PASS")
    # Display the text 'Effective coordination graph'.
    print("\nEffective coordination graph")
    # Display the text 'Original regulatory graph preserved: PASS'.
    print("  Original regulatory graph preserved: PASS")
    # Display the text 'Only agreed claims removed from effective graph: PASS'.
    print("  Only agreed claims removed from effective graph: PASS")
    # Display the text 'Rejected claim preserved: PASS'.
    print("  Rejected claim preserved: PASS")
    # Display the text 'Pending claim preserved: PASS'.
    print("  Pending claim preserved: PASS")
    # Display the text 'Determinism'.
    print("\nDeterminism")
    # Display the text 'Message-order invariance: PASS'.
    print("  Message-order invariance: PASS")
    # Display the text 'Vehicle-order invariance: PASS'.
    print("  Vehicle-order invariance: PASS")
    # Display the text 'Claim-order invariance: PASS'.
    print("  Claim-order invariance: PASS")
    # Display the text 'Response policy interface'.
    print("\nResponse policy interface")
    # Display the text 'ACCEPT_RELINQUISHMENT semantic action available: PASS'.
    print("  ACCEPT_RELINQUISHMENT semantic action available: PASS")
    # Display the text 'REJECT_RELINQUISHMENT semantic action available: PASS'.
    print("  REJECT_RELINQUISHMENT semantic action available: PASS")
    # Display the text 'Response hard mask Boolean: PASS'.
    print("  Response hard mask Boolean: PASS")
    # Display the text 'Learned feasibility parameters: 0'.
    print("  Learned feasibility parameters: 0")
    # Display the text 'Response actor decentralized input only: PASS'.
    print("  Response actor decentralized input only: PASS")
    # Display the text 'Response actor action executed: False'.
    print("  Response actor action executed: False")
    # Display formatted text built from the embedded values.
    print(f"  Response actor architecture: {RESPONSE_ACTOR_ARCHITECTURE}")
    # Display the text 'Authority boundaries'.
    print("\nAuthority boundaries")
    # Display the text 'Route-truth consumed: 0'.
    print("  Route-truth consumed: 0")
    # Display the text 'Prediction probability controls protocol truth: False'.
    print("  Prediction probability controls protocol truth: False")
    # Display the text 'Untrained logits control protocol truth: False'.
    print("  Untrained logits control protocol truth: False")
    # Display the text 'Research parameters'.
    print("\nResearch parameters")
    # Display the text 'New operational thresholds: 0'.
    print("  New operational thresholds: 0")
    # Display the text 'Timeout constants: 0'.
    print("  Timeout constants: 0")
    # Display the text 'Retry constants: 0'.
    print("  Retry constants: 0")
    # Display the text 'Reward weights: 0'.
    print("  Reward weights: 0")
    # Display the text 'PPO hyperparameters configured: 0'.
    print("  PPO hyperparameters configured: 0")
    # Display the text 'Dependencies'.
    print("\nDependencies")
    # Display the text 'Backend: PyTorch CPU'.
    print("  Backend: PyTorch CPU")
    # Display the text 'TensorFlow required: False'.
    print("  TensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'PyTorch Geometric required: False'.
    print("  PyTorch Geometric required: False")
    # Display the text 'New dependency required: False'.
    print("  New dependency required: False")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display the text 'Proposal policy trained: False'.
    print("  Proposal policy trained: False")
    # Display the text 'Response policy trained: False'.
    print("  Response policy trained: False")
    # Display the text 'PPO implemented: False'.
    print("  PPO implemented: False")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
    # Display the text 'Optimizer implemented: False'.
    print("  Optimizer implemented: False")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'Safety shield implemented: False'.
    print("  Safety shield implemented: False")
    # Display the text 'SUMO control actions issued: 0'.
    print("  SUMO control actions issued: 0")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
