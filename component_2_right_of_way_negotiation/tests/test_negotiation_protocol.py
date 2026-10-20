"""Deterministic Step 5E.1 proposal/response protocol tests."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import permutations from itertools for the operations below.
from itertools import permutations

# Import pytest for use in this module.
import pytest

# Import NegotiationClaimBuilder, NegotiationStatus from negotiation_learning for the operations below.
from negotiation_learning import NegotiationClaimBuilder, NegotiationStatus
# Import ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProposalResponse, ProtocolSemanticError,
# ProtocolState, agreement_complete, deterministic_proposal_id from negotiation_learning.protocol for the
# operations below.
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationProtocolBus, ProposalResponse,
    ProtocolSemanticError, ProtocolState, agreement_complete,
    deterministic_proposal_id,
)


# Set PROFILE to the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
PROFILE = "DE_STVO_UNCONTROLLED_4WAY_V1"
# Set NOW to 1.0.
NOW = 1.0


# Edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Input probability: the supplied probability.
# Output: value.
# Processing: select branches using the stated conditions.
def edge(source, target, probability=None):
    # Set value to a dictionary containing yielding_vehicle_id, priority_vehicle_id, timestamp,
    # regulatory_profile,...
    value = {
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
        # Set value['intention_weighted_conflict_probability'] to probability.
        value["intention_weighted_conflict_probability"] = probability
    # Return value to the caller.
    return value


# Owned claim using the inputs and processing steps below.
# Input owner: the supplied owner.
# Input edges: the supplied edges.
# Output: a tuple containing result, result.ego_precedence_claims at 0.
def owned_claim(owner, edges):
    # Set result to the result of NegotiationClaimBuilder().build(owner, a dictionary containing
    # joint_precedence_edges,...).
    result = NegotiationClaimBuilder().build(
        # Store a tuple built from edges under 'joint_precedence_edges'.
        owner, {"joint_precedence_edges": tuple(edges)},
        # Supply NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value to NegotiationClaimBuilder().build.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        # Supply True to the enclosing expression.
        True, True,
    )
    # Return a tuple containing result, result.ego_precedence_claims at 0 to the caller.
    return result, result.ego_precedence_claims[0]


# Proposal for using the inputs and processing steps below.
# Input source: the supplied source.
# Input owner: the supplied owner.
# Input edges: the supplied edges.
# Output: a tuple containing edges, proposal.
def proposal_for(source="A", owner="B", edges=None):
    # Set edges to edges or a tuple containing the result of edge(source, owner).
    edges = edges or (edge(source, owner),)
    # Set (claim_set, claim) to the result of owned_claim(owner, edges).
    claim_set, claim = owned_claim(owner, edges)
    # Set proposal to the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # claim_set.policy_authority).
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        # Supply claim_set.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    # Return a tuple containing edges, proposal to the caller.
    return edges, proposal


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


# Check accept establishes overlay but preserves original graph using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_accept_establishes_overlay_but_preserves_original_graph():
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set result to the result of evaluate(edges, a tuple containing proposal, the result of
    # response_for(proposal, the text 'ACCEPT')).
    result = evaluate(edges, (proposal, response_for(proposal, "ACCEPT")))
    # Require the result of agreement_complete(result); otherwise raise AssertionError.
    assert agreement_complete(result)
    # Require result.original_regulatory_precedence_graph equals a tuple containing a tuple containing the text
    # 'A', the text 'B'; otherwise raise AssertionError.
    assert result.original_regulatory_precedence_graph == (("A", "B"),)
    # Require result.effective_coordination_graph equals an empty tuple; otherwise raise AssertionError.
    assert result.effective_coordination_graph == ()
    # Require result.negotiated_agreement_overlay.overlay_effect equals the text
    # 'CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT'; otherwise raise AssertionError.
    assert result.negotiated_agreement_overlay.overlay_effect == (
        "CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT"
    )


# Check proposal alone is pending and does not change edge using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_proposal_alone_is_pending_and_does_not_change_edge():
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set result to the result of evaluate(edges, a tuple containing proposal).
    result = evaluate(edges, (proposal,))
    # Require result.state is the same object as ProtocolState.PROPOSAL_PENDING; otherwise raise AssertionError.
    assert result.state is ProtocolState.PROPOSAL_PENDING
    # Require the negation of the result of agreement_complete(result); otherwise raise AssertionError.
    assert not agreement_complete(result)
    # Require result.effective_coordination_graph equals a tuple containing a tuple containing the text 'A', the
    # text 'B'; otherwise raise AssertionError.
    assert result.effective_coordination_graph == (("A", "B"),)


# Check reject never establishes agreement or overlay using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_reject_never_establishes_agreement_or_overlay():
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set result to the result of evaluate(edges, a tuple containing proposal, the result of
    # response_for(proposal, the text 'REJECT')).
    result = evaluate(edges, (proposal, response_for(proposal, "REJECT")))
    # Require result.state is the same object as ProtocolState.PROPOSAL_REJECTED; otherwise raise AssertionError.
    assert result.state is ProtocolState.PROPOSAL_REJECTED
    # Require the negation of the result of agreement_complete(result); otherwise raise AssertionError.
    assert not agreement_complete(result)
    # Require result.negotiated_agreement_overlay.overlay_effect is the same object as None; otherwise raise
    # AssertionError.
    assert result.negotiated_agreement_overlay.overlay_effect is None


# Check wrong owner and wrong counterparty are rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_wrong_owner_and_wrong_counterparty_are_rejected():
    # Set (claim_set, obligation) to the result of owned_claim(the text 'B', a tuple containing the result of
    # edge(the text 'A', the text 'B')).
    claim_set, obligation = owned_claim("B", (edge("A", "B"),))
    # Import PrecedenceClaim, ClaimRole from negotiation_learning.claim_semantics for the operations below.
    from negotiation_learning.claim_semantics import PrecedenceClaim, ClaimRole
    # Set wrong to the result of PrecedenceClaim(the text 'A', the text 'B', the text 'A', the text 'B',
    # ClaimRole.EGO_IS_PRIORITY,...).
    wrong = PrecedenceClaim(
        # Supply ClaimRole.EGO_IS_PRIORITY to PrecedenceClaim.
        "A", "B", "A", "B", ClaimRole.EGO_IS_PRIORITY,
        # Supply obligation.applicable_rule_ids to PrecedenceClaim.
        obligation.applicable_rule_ids, obligation.source_sections,
        # Supply obligation.source_snapshot_timestamp to PrecedenceClaim.
        obligation.shared_conflict_zone_ids, obligation.source_snapshot_timestamp,
        # Supply obligation.hard_constraint_evidence to PrecedenceClaim.
        obligation.hard_constraint_evidence,
    )
    # Enter the result of pytest.raises(ProtocolSemanticError) and run the enclosed operations within that
    # context.
    with pytest.raises(ProtocolSemanticError, match="SENDER_DOES_NOT_OWN"):
        # Call ClaimRelinquishmentProtocol.create_proposal with the supplied arguments.
        ClaimRelinquishmentProtocol.create_proposal(
            # Supply claim_set.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
            wrong, NOW, PROFILE, claim_set.policy_authority,
        )
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set invalid to the result of replace(proposal).
    invalid = replace(
        # Supply receiver_id as the text 'C'.
        proposal, receiver_id="C",
        # Supply proposal_id as the result of deterministic_proposal_id(NOW, the text 'A', the text 'B', the text
        # 'B', the text 'C').
        proposal_id=deterministic_proposal_id(NOW, "A", "B", "B", "C"),
    )
    # Set result to the result of evaluate(edges, a tuple containing invalid).
    result = evaluate(edges, (invalid,))
    # Require result.negotiated_agreement_overlay.diagnostic equals the text 'INVALID_COUNTERPARTY'; otherwise
    # raise AssertionError.
    assert result.negotiated_agreement_overlay.diagnostic == "INVALID_COUNTERPARTY"


# Check wrong proposal reference and disagreement do not vote using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_wrong_proposal_reference_and_disagreement_do_not_vote():
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set accept to the result of response_for(proposal, the text 'ACCEPT').
    accept = response_for(proposal, "ACCEPT")
    # Set wrong to the result of replace(accept).
    wrong = replace(accept, proposal_id=(NOW, "X", "Y", "Y", "X"))
    # Require evaluate(edges, (proposal, wrong)).negotiated_agreement_overlay.diagnostic equals the text
    # 'RESPONSE_PROPOSAL_MISMATCH'; otherwise raise AssertionError.
    assert evaluate(edges, (proposal, wrong)).negotiated_agreement_overlay.diagnostic == (
        "RESPONSE_PROPOSAL_MISMATCH"
    )
    # Set reject to the result of response_for(proposal, the text 'REJECT').
    reject = response_for(proposal, "REJECT")
    # Set result to the result of evaluate(edges, a tuple containing proposal, accept, reject).
    result = evaluate(edges, (proposal, accept, reject))
    # Require result.state is the same object as ProtocolState.PROTOCOL_DISAGREEMENT; otherwise raise
    # AssertionError.
    assert result.state is ProtocolState.PROTOCOL_DISAGREEMENT


# Check source claim disappearance timestamp and profile mismatch block using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_source_claim_disappearance_timestamp_and_profile_mismatch_block():
    # Set (edges, proposal) to the result of proposal_for().
    edges, proposal = proposal_for()
    # Set accept to the result of response_for(proposal, the text 'ACCEPT').
    accept = response_for(proposal, "ACCEPT")
    # Set gone to the result of evaluate(an empty tuple, a tuple containing proposal, accept).
    gone = evaluate((), (proposal, accept))
    # Set stale to the result of evaluate(a tuple containing the result of replace_dict(edges at 0), a tuple
    # containing proposal, accept).
    stale = evaluate((replace_dict(edges[0], timestamp=2.0),), (proposal, accept))
    # Set profile to the result of replace(accept).
    profile = replace(accept, regulatory_profile="OTHER_PROFILE")
    # Set mismatch to the result of evaluate(edges, a tuple containing proposal, profile).
    mismatch = evaluate(edges, (proposal, profile))
    # Require gone.state is the same object as stale.state; is the same object as
    # ProtocolState.SOURCE_CLAIM_INVALID; otherwise raise AssertionError.
    assert gone.state is stale.state is ProtocolState.SOURCE_CLAIM_INVALID
    # Require mismatch.state is the same object as ProtocolState.PROTOCOL_BLOCKED; otherwise raise AssertionError.
    assert mismatch.state is ProtocolState.PROTOCOL_BLOCKED


# Replace dict using the inputs and processing steps below.
# Input value: the supplied value.
# Input updates: the supplied updates.
# Output: result.
def replace_dict(value, **updates):
    # Set result to a dictionary built from value.
    # Update result with the supplied entries.
    # Return result to the caller.
    result = dict(value); result.update(updates); return result


# Check four way cycle only owned claim can be proposed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_four_way_cycle_only_owned_claim_can_be_proposed():
    # Set cycle to a tuple built from a lazy sequence of the result of edge(a, b) for (a, b) in a tuple containing
    # a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple containing...
    cycle = tuple(edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Set (claim_set, claim) to the result of owned_claim(the text 'A', cycle).
    claim_set, claim = owned_claim("A", cycle)
    # Set proposal to the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # claim_set.policy_authority).
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        # Supply claim_set.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    # Set result to the result of evaluate(cycle, a tuple containing proposal, the result of
    # response_for(proposal, the text 'ACCEPT')).
    result = evaluate(cycle, (proposal, response_for(proposal, "ACCEPT")))
    # Require a tuple containing proposal.yielding_vehicle_id, proposal.priority_vehicle_id equals a tuple
    # containing the text 'D', the text 'A'; otherwise raise AssertionError.
    assert (proposal.yielding_vehicle_id, proposal.priority_vehicle_id) == ("D", "A")
    # Require a tuple containing the text 'A', the text 'B' belongs to
    # result.original_regulatory_precedence_graph; otherwise raise AssertionError.
    assert ("A", "B") in result.original_regulatory_precedence_graph
    # Require a tuple containing the text 'A', the text 'B' belongs to result.effective_coordination_graph;
    # otherwise raise AssertionError.
    assert ("A", "B") in result.effective_coordination_graph
    # Require a set built from result.original_regulatory_precedence_graph equals a set containing a tuple
    # containing the text 'A', the text 'B', a tuple containing the text 'B', the text 'C', a tuple...; otherwise
    # raise AssertionError.
    assert set(result.original_regulatory_precedence_graph) == {
        # Include a tuple containing the text 'A', the text 'B' in this set.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    }


# Check multiple claim agreement is pair specific using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_multiple_claim_agreement_is_pair_specific():
    # Set edges to a tuple containing the result of edge(the text 'A', the text 'B'), the result of edge(the text
    # 'C', the text 'B').
    edges = (edge("A", "B"), edge("C", "B"))
    # Set (claim_set, _) to the result of owned_claim(the text 'B', edges).
    claim_set, _ = owned_claim("B", edges)
    # Set claim to the next item from a lazy sequence of item for item in claim_set.ego_precedence_claims; retain
    # entries satisfying item.counterparty_id equals the text 'A'.
    claim = next(item for item in claim_set.ego_precedence_claims
                 # Evaluate item.counterparty_id equals the text 'A' as part of the enclosing expression.
                 if item.counterparty_id == "A")
    # Set proposal to the result of ClaimRelinquishmentProtocol.create_proposal(claim, NOW, PROFILE,
    # claim_set.policy_authority).
    proposal = ClaimRelinquishmentProtocol.create_proposal(
        # Supply claim_set.policy_authority to ClaimRelinquishmentProtocol.create_proposal.
        claim, NOW, PROFILE, claim_set.policy_authority,
    )
    # Set result to the result of evaluate(edges, a tuple containing proposal, the result of
    # response_for(proposal, the text 'ACCEPT')).
    result = evaluate(edges, (proposal, response_for(proposal, "ACCEPT")))
    # Require result.effective_coordination_graph equals a tuple containing a tuple containing the text 'C', the
    # text 'B'; otherwise raise AssertionError.
    assert result.effective_coordination_graph == (("C", "B"),)


# Check message claim and vehicle order are invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_message_claim_and_vehicle_order_are_invariant():
    # Set cycle to a tuple built from a lazy sequence of the result of edge(a, b) for (a, b) in a tuple containing
    # a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple containing...
    cycle = tuple(edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Set (_, proposal) to the result of proposal_for(the text 'D', the text 'A', cycle).
    _, proposal = proposal_for("D", "A", cycle)
    # Set accept to the result of response_for(proposal, the text 'ACCEPT').
    accept = response_for(proposal, "ACCEPT")
    # Set first to the result of evaluate(cycle, a tuple containing proposal, accept).
    first = evaluate(cycle, (proposal, accept))
    # Set second to the result of evaluate(a tuple built from the reverse traversal of cycle, a tuple containing
    # accept, proposal).
    second = evaluate(tuple(reversed(cycle)), (accept, proposal))
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Independent consumers in different vehicle-loop orders see one frozen set.
    # Set bus to the result of NegotiationProtocolBus().
    # Call bus.begin_step with the supplied arguments.
    bus = NegotiationProtocolBus(); bus.begin_step(NOW)
    # Call bus.publish with the supplied arguments.
    bus.publish(accept); bus.publish(proposal); bus.publish(proposal)
    # Call bus.freeze_step with the supplied arguments.
    bus.freeze_step(NOW)
    # Set snapshots to a dictionary of ego mapped to the result of evaluate(cycle, the result of
    # bus.current_messages(NOW)) for ego in a tuple containing the text 'D', the text 'C', the text 'B', the text
    # 'A'.
    snapshots = {
        # Evaluate the result of evaluate(cycle, the result of bus.current_messages(NOW)) as part of the enclosing
        # expression.
        ego: evaluate(cycle, bus.current_messages(NOW))
        # Evaluate a tuple containing the text 'D', the text 'C', the text 'B', the text 'A' as part of the
        # enclosing expression.
        for ego in ("D", "C", "B", "A")
    }
    # Require the number of entries in a set built from values from snapshots equals 1; otherwise raise
    # AssertionError.
    assert len(set(snapshots.values())) == 1


# Check probabilities actor logits and route truth cannot define agreement using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_probabilities_actor_logits_and_route_truth_cannot_define_agreement():
    # Set (low_edges, proposal) to the result of proposal_for().
    low_edges, proposal = proposal_for(edges=(edge("A", "B", 0.01),))
    # Set high_edges to a tuple containing the result of edge(the text 'A', the text 'B', 0.99).
    high_edges = (edge("A", "B", 0.99),)
    # Set pending_low to the result of evaluate(low_edges, a tuple containing proposal).
    pending_low = evaluate(low_edges, (proposal,))
    # Set pending_high to the result of evaluate(high_edges, a tuple containing proposal).
    pending_high = evaluate(high_edges, (proposal,))
    # Set external to a dictionary containing route_id, route_index, ground_truth_route_id, actor_logits.
    external = {"route_id": "x", "route_index": 99,
                # Store the text 'y' under 'ground_truth_route_id'.
                # Store a tuple containing 999, the negative of 999 under 'actor_logits'.
                "ground_truth_route_id": "y", "actor_logits": (999, -999)}
    # Update external with the supplied entries.
    external.update({"actor_logits": (-999, 999)})
    # Require pending_low equals pending_high; otherwise raise AssertionError.
    assert pending_low == pending_high
    # Require pending_low.state is the same object as ProtocolState.PROPOSAL_PENDING; otherwise raise
    # AssertionError.
    assert pending_low.state is ProtocolState.PROPOSAL_PENDING


# Check keep claim creates no proposal and no automatic response policy using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_keep_claim_creates_no_proposal_and_no_automatic_response_policy():
    # Set edges to a tuple containing the result of edge(the text 'A', the text 'B').
    edges = (edge("A", "B"),)
    # Set result to the result of evaluate(edges, an empty tuple).
    result = evaluate(edges, ())
    # Require result.state is the same object as ProtocolState.NO_PROPOSAL; otherwise raise AssertionError.
    assert result.state is ProtocolState.NO_PROPOSAL
    # Import RESPONSE_POLICY_STATUS from negotiation_learning.protocol for the operations below.
    from negotiation_learning.protocol import RESPONSE_POLICY_STATUS
    # Require RESPONSE_POLICY_STATUS equals the text 'RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION';
    # otherwise raise AssertionError.
    assert RESPONSE_POLICY_STATUS == "RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION"
