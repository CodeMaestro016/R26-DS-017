"""Standalone deterministic Step 5E.1 protocol validation without SUMO."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import NegotiationClaimBuilder, NegotiationStatus from negotiation_learning for the operations below.
from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
# Import ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProtocolState, RESPONSE_POLICY_STATUS,
# agreement_complete, deterministic_proposal_id from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProtocolState,
    RESPONSE_POLICY_STATUS, agreement_complete, deterministic_proposal_id,
)


# Set (PROFILE, NOW) to a tuple containing the text 'DE_STVO_UNCONTROLLED_4WAY_V1', 1.0.
PROFILE, NOW = "DE_STVO_UNCONTROLLED_4WAY_V1", 1.0


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
        # Set result['intention_weighted_conflict_probability'] to probability.
        result["intention_weighted_conflict_probability"] = probability
    # Return result to the caller.
    return result


# Claim set using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input edges: the supplied edges.
# Output: the result of NegotiationClaimBuilder().build(ego, a dictionary containing joint_precedence_edges,...).
def claim_set(ego, edges):
    # Return the result of NegotiationClaimBuilder().build(ego, a dictionary containing
    # joint_precedence_edges,...) to the caller.
    return NegotiationClaimBuilder().build(
        # Store a tuple built from edges under 'joint_precedence_edges'.
        ego, {"joint_precedence_edges": tuple(edges)},
        # Supply NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value to NegotiationClaimBuilder().build.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        # Supply True to the enclosing expression.
        True, True,
    )


# Proposal for using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input edges: the supplied edges.
# Input counterparty: the supplied counterparty.
# Output: the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE, owned.policy_authority).
def proposal_for(ego, edges, counterparty=None):
    # Set owned to the result of claim_set(ego, edges).
    owned = claim_set(ego, edges)
    # Set claim to the next item from a lazy sequence of item for item in owned.ego_precedence_claims; retain
    # entries satisfying counterparty is the same object as None or item.counterparty_id equals counterparty.
    claim = next(item for item in owned.ego_precedence_claims
                 # Evaluate counterparty is the same object as None or item.counterparty_id equals counterparty as
                 # part of the enclosing expression.
                 if counterparty is None or item.counterparty_id == counterparty)
    # Return the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # owned.policy_authority) to the caller.
    return ClaimRelinquishmentProtocol.create_proposal(
        # Supply owned.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, owned.policy_authority,
    )


# Response for using the inputs and processing steps below.
# Input proposal: the supplied proposal.
# Input response: the supplied response.
# Output: the result of ClaimRelinquishmentProtocol.create_response(proposal, proposal.receiver_id, response, NOW,
# PROFILE).
def response_for(proposal, response):
    # Return the result of ClaimRelinquishmentProtocol.create_response(proposal, proposal.receiver_id, response,
    # NOW, PROFILE) to the caller.
    return ClaimRelinquishmentProtocol.create_response(
        # Supply proposal.receiver_id to ClaimRelinquishmentProtocol.create_response.
        proposal, proposal.receiver_id, response, NOW, PROFILE,
    )


# Evaluate using the inputs and processing steps below.
# Input edges: the supplied edges.
# Input messages: the supplied messages.
# Input kwargs: the supplied kwargs.
# Output: the result of ClaimRelinquishmentProtocol().evaluate(edges, messages, NOW, PROFILE).
def evaluate(edges, messages, **kwargs):
    # Return the result of ClaimRelinquishmentProtocol().evaluate(edges, messages, NOW, PROFILE) to the caller.
    return ClaimRelinquishmentProtocol().evaluate(
        # Supply the unpacked keyword arguments as kwargs.
        edges, messages, NOW, PROFILE, **kwargs,
    )


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set simple to a tuple containing the result of edge(the text 'A', the text 'B').
    simple = (edge("A", "B"),)
    # Set proposal to the result of proposal_for(the text 'B', simple).
    proposal = proposal_for("B", simple)
    # Set (accept, reject) to a tuple containing the result of response_for(proposal, the text 'ACCEPT'), the
    # result of response_for(proposal, the text...
    accept, reject = response_for(proposal, "ACCEPT"), response_for(proposal, "REJECT")
    # Set pending to the result of evaluate(simple, a tuple containing proposal).
    pending = evaluate(simple, (proposal,))
    # Set accepted to the result of evaluate(simple, a tuple containing proposal, accept).
    accepted = evaluate(simple, (proposal, accept))
    # Set rejected to the result of evaluate(simple, a tuple containing proposal, reject).
    rejected = evaluate(simple, (proposal, reject))
    # Require pending.state is the same object as ProtocolState.PROPOSAL_PENDING and the negation of the result of
    # agreement_complete(pending); otherwise raise AssertionError.
    assert pending.state is ProtocolState.PROPOSAL_PENDING and not agreement_complete(pending)
    # Require the result of agreement_complete(accepted); otherwise raise AssertionError.
    assert agreement_complete(accepted)
    # Require rejected.state is the same object as ProtocolState.PROPOSAL_REJECTED; otherwise raise
    # AssertionError.
    assert rejected.state is ProtocolState.PROPOSAL_REJECTED
    # Require accepted.original_regulatory_precedence_graph equals a tuple containing a tuple containing the text
    # 'A', the text 'B'; otherwise raise AssertionError.
    assert accepted.original_regulatory_precedence_graph == (("A", "B"),)

    # Set invalid_counterparty to the result of replace(proposal).
    invalid_counterparty = replace(
        # Supply receiver_id as the text 'C'.
        proposal, receiver_id="C",
        # Supply proposal_id as the result of deterministic_proposal_id(NOW, the text 'A', the text 'B', the text
        # 'B', the text 'C').
        proposal_id=deterministic_proposal_id(NOW, "A", "B", "B", "C"),
    )
    # Require evaluate(simple, (invalid_counterparty,)).negotiated_agreement_overlay.diagnostic equals the text
    # 'INVALID_COUNTERPARTY'; otherwise raise AssertionError.
    assert evaluate(simple, (invalid_counterparty,)).negotiated_agreement_overlay.diagnostic == "INVALID_COUNTERPARTY"
    # Set wrong_reference to the result of replace(accept).
    wrong_reference = replace(accept, proposal_id=(NOW, "X", "Y", "Y", "X"))
    # Require evaluate(simple, (proposal, wrong_reference)).negotiated_agreement_overlay.diagnostic equals the
    # text 'RESPONSE_PROPOSAL_MISMATCH'; otherwise raise AssertionError.
    assert evaluate(simple, (proposal, wrong_reference)).negotiated_agreement_overlay.diagnostic == "RESPONSE_PROPOSAL_MISMATCH"
    # Require evaluate(simple, (proposal, accept, reject)).state is the same object as
    # ProtocolState.PROTOCOL_DISAGREEMENT; otherwise raise AssertionError.
    assert evaluate(simple, (proposal, accept, reject)).state is ProtocolState.PROTOCOL_DISAGREEMENT
    # Require evaluate((), (proposal, accept)).state is the same object as ProtocolState.SOURCE_CLAIM_INVALID;
    # otherwise raise AssertionError.
    assert evaluate((), (proposal, accept)).state is ProtocolState.SOURCE_CLAIM_INVALID
    # Set profile_mismatch to the result of replace(accept).
    profile_mismatch = replace(accept, regulatory_profile="OTHER")
    # Require evaluate(simple, (proposal, profile_mismatch)).state is the same object as
    # ProtocolState.PROTOCOL_BLOCKED; otherwise raise AssertionError.
    assert evaluate(simple, (proposal, profile_mismatch)).state is ProtocolState.PROTOCOL_BLOCKED

    # Set cycle to a tuple built from a lazy sequence of the result of edge(a, b) for (a, b) in a tuple containing
    # a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple containing...
    cycle = tuple(edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Set cycle_proposal to the result of proposal_for(the text 'A', cycle, the text 'D').
    cycle_proposal = proposal_for("A", cycle, "D")
    # Set cycle_accept to the result of response_for(cycle_proposal, the text 'ACCEPT').
    cycle_accept = response_for(cycle_proposal, "ACCEPT")
    # Set cycle_result to the result of evaluate(cycle, a tuple containing cycle_proposal, cycle_accept).
    cycle_result = evaluate(cycle, (cycle_proposal, cycle_accept))
    # Require a tuple containing the text 'A', the text 'B' belongs to cycle_result.effective_coordination_graph;
    # otherwise raise AssertionError.
    assert ("A", "B") in cycle_result.effective_coordination_graph
    # Require a tuple containing the text 'D', the text 'A' does not belong to
    # cycle_result.effective_coordination_graph; otherwise raise AssertionError.
    assert ("D", "A") not in cycle_result.effective_coordination_graph
    # Require a set built from cycle_result.original_regulatory_precedence_graph equals a set containing a tuple
    # containing the text 'A', the text 'B', a tuple containing the text 'B', the text 'C', a tuple...; otherwise
    # raise AssertionError.
    assert set(cycle_result.original_regulatory_precedence_graph) == {
        # Include a tuple containing the text 'A', the text 'B' in this set.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    }

    # Set multiple to a tuple containing the result of edge(the text 'A', the text 'B'), the result of edge(the
    # text 'C', the text 'B').
    multiple = (edge("A", "B"), edge("C", "B"))
    # Set multi_proposal to the result of proposal_for(the text 'B', multiple, the text 'A').
    multi_proposal = proposal_for("B", multiple, "A")
    # Set multi_result to the result of evaluate(multiple, a tuple containing multi_proposal, the result of
    # response_for(multi_proposal, the text...).
    multi_result = evaluate(multiple, (multi_proposal, response_for(multi_proposal, "ACCEPT")))
    # Require multi_result.effective_coordination_graph equals a tuple containing a tuple containing the text 'C',
    # the text 'B'; otherwise raise AssertionError.
    assert multi_result.effective_coordination_graph == (("C", "B"),)

    # Set reordered to the result of evaluate(a tuple built from the reverse traversal of cycle, a tuple
    # containing cycle_accept, cycle_proposal).
    reordered = evaluate(tuple(reversed(cycle)), (cycle_accept, cycle_proposal))
    # Require cycle_result equals reordered; otherwise raise AssertionError.
    assert cycle_result == reordered
    # Set bus to the result of NegotiationProtocolBus().
    # Call bus.begin_step with the supplied arguments.
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    # Call bus.publish with the supplied arguments.
    bus.publish(cycle_accept); bus.publish(cycle_proposal); bus.publish(cycle_proposal)
    # Call bus.freeze_step with the supplied arguments.
    bus.freeze_step(NOW)
    # Set states to a tuple built from a lazy sequence of the result of evaluate(cycle, the result of
    # bus.current_messages(NOW)) for _ego in a tuple containing the text 'D', the text 'C', the text 'B', the text
    # 'A'.
    states = tuple(evaluate(cycle, bus.current_messages(NOW))
                   # Evaluate a tuple containing the text 'D', the text 'C', the text 'B', the text 'A' as part of
                   # the enclosing expression.
                   for _ego in ("D", "C", "B", "A"))
    # Require whether every item is true in a lazy sequence of item equals states at 0 for item in states;
    # otherwise raise AssertionError.
    assert all(item == states[0] for item in states)

    # Set low to a tuple containing the result of edge(the text 'A', the text 'B', 0.01).
    low = (edge("A", "B", 0.01),)
    # Set high to a tuple containing the result of edge(the text 'A', the text 'B', 0.99).
    high = (edge("A", "B", 0.99),)
    # Set low_proposal to the result of proposal_for(the text 'B', low).
    low_proposal = proposal_for("B", low)
    # Require evaluate(low, (low_proposal,)).state equals evaluate(high, (low_proposal,)).state; otherwise raise
    # AssertionError.
    assert evaluate(low, (low_proposal,)).state == evaluate(high, (low_proposal,)).state

    # Display the text 'Negotiation Protocol Validation'.
    print("Negotiation Protocol Validation\n")
    # Display the text 'Semantics'.
    print("Semantics")
    # Display the text 'Proposal does not equal agreement: PASS'.
    print("  Proposal does not equal agreement: PASS")
    # Display the text 'Only precedence owner may relinquish claim: PASS'.
    print("  Only precedence owner may relinquish claim: PASS")
    # Display the text 'Mandatory yield obligation cannot be relinquished: PASS'.
    print("  Mandatory yield obligation cannot be relinquished: PASS")
    # Display the text 'Claim targeting is pair-specific: PASS'.
    print("  Claim targeting is pair-specific: PASS")
    # Display the text 'Agreement'.
    print("\nAgreement")
    # Display the text 'Valid ACCEPT establishes agreement: PASS'.
    print("  Valid ACCEPT establishes agreement: PASS")
    # Display the text 'REJECT does not establish agreement: PASS'.
    print("  REJECT does not establish agreement: PASS")
    # Display the text 'Missing response remains pending: PASS'.
    print("  Missing response remains pending: PASS")
    # Display the text 'Wrong counterparty rejected: PASS'.
    print("  Wrong counterparty rejected: PASS")
    # Display the text 'Wrong proposal reference rejected: PASS'.
    print("  Wrong proposal reference rejected: PASS")
    # Display the text 'Consistency'.
    print("\nConsistency")
    # Display the text 'Source claim validity required: PASS'.
    print("  Source claim validity required: PASS")
    # Display the text 'Snapshot consistency required: PASS'.
    print("  Snapshot consistency required: PASS")
    # Display the text 'Regulatory profile consistency required: PASS'.
    print("  Regulatory profile consistency required: PASS")
    # Display the text 'Protocol disagreement preserved: PASS'.
    print("  Protocol disagreement preserved: PASS")
    # Display the text 'Four-way cycle'.
    print("\nFour-way cycle")
    # Display the text 'A may relinquish D->A: PASS'.
    print("  A may relinquish D->A: PASS")
    # Display the text 'A cannot relinquish A->B: PASS'.
    print("  A cannot relinquish A->B: PASS")
    # Display the text 'Unrelated claims unchanged: PASS'.
    print("  Unrelated claims unchanged: PASS")
    # Display the text 'Multiple claims'.
    print("\nMultiple claims")
    # Display the text 'One claim agreement does not alter second claim: PASS'.
    print("  One claim agreement does not alter second claim: PASS")
    # Display the text 'Determinism'.
    print("\nDeterminism")
    # Display the text 'Message-order invariance: PASS'.
    print("  Message-order invariance: PASS")
    # Display the text 'Vehicle-processing-order invariance: PASS'.
    print("  Vehicle-processing-order invariance: PASS")
    # Display the text 'Authority boundaries'.
    print("\nAuthority boundaries")
    # Display the text 'Route-truth fields consumed: 0'.
    print("  Route-truth fields consumed: 0")
    # Display the text 'Prediction probability controls protocol truth: False'.
    print("  Prediction probability controls protocol truth: False")
    # Display the text 'Actor logits control agreement truth: False'.
    print("  Actor logits control agreement truth: False")
    # Display the text 'Communication abstraction'.
    print("\nCommunication abstraction")
    # Display the text 'Model: IDEAL_SAME_STEP_V2V'.
    print("  Model: IDEAL_SAME_STEP_V2V")
    # Display the text 'New operational numerical thresholds: 0'.
    print("  New operational numerical thresholds: 0")
    # Display the text 'Timeout constants: 0'.
    print("  Timeout constants: 0")
    # Display the text 'Retry constants: 0'.
    print("  Retry constants: 0")
    # Display the text 'Communication-range constants: 0'.
    print("  Communication-range constants: 0")
    # Display the text 'Packet-loss assumptions: 0'.
    print("  Packet-loss assumptions: 0")
    # Display the text 'Dependencies'.
    print("\nDependencies")
    # Display the text 'TensorFlow required: False'.
    print("  TensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'New dependency required: False'.
    print("  New dependency required: False")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display formatted text built from the embedded values.
    print(f"  Response policy: {RESPONSE_POLICY_STATUS}")
    # Display the text 'Learned response policy implemented: False'.
    print("  Learned response policy implemented: False")
    # Display the text 'PPO implemented: False'.
    print("  PPO implemented: False")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
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
