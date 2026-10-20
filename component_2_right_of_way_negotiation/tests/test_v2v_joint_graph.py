"""Regression tests for decentralized same-step joint graph assembly."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import pytest for use in this module.
import pytest

# Import JointLocalPrecedenceGraphAssembler, NegotiationEnvironment, NegotiationStatus, PrecedenceClaimMessage,
# RegulatoryPrecedenceGraphBuilder, V2VPrecedenceClaimBus from negotiation_learning for the operations below.
from negotiation_learning import (
    JointLocalPrecedenceGraphAssembler, NegotiationEnvironment,
    NegotiationStatus, PrecedenceClaimMessage,
    RegulatoryPrecedenceGraphBuilder, V2VPrecedenceClaimBus,
)
# Import GraphObservationBuilder from negotiation_learning.observation_builder for the operations below.
from negotiation_learning.observation_builder import GraphObservationBuilder


# Set PROFILE to the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
PROFILE = "DE_STVO_UNCONTROLLED_4WAY_V1"


# Claim using the inputs and processing steps below.
# Input sender: the supplied sender.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Input timestamp: the supplied timestamp.
# Input profile: the supplied profile.
# Output: the result of PrecedenceClaimMessage(sender, timestamp, yielding, priority, a tuple containing the text
# 'DE-STVO-8-1', a tuple...).
def claim(sender, yielding, priority, timestamp=7.0, profile=PROFILE):
    # Return the result of PrecedenceClaimMessage(sender, timestamp, yielding, priority, a tuple containing the
    # text 'DE-STVO-8-1', a tuple...) to the caller.
    return PrecedenceClaimMessage(
        # Supply a tuple containing the text 'DE-STVO-8-1' to PrecedenceClaimMessage.
        sender, timestamp, yielding, priority, ("DE-STVO-8-1",),
        # Supply a tuple containing the text 'CROSSING' to PrecedenceClaimMessage.
        ("§ 8",), profile, ("ZONE",), ("CROSSING",),
        # Supply a tuple containing formatted text built from the embedded values to PrecedenceClaimMessage.
        (f"{priority}_PATH",), timestamp, timestamp, 0.0,
    )


# Edge using the inputs and processing steps below.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
# source_sections,...
def edge(yielding, priority):
    # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
    # source_sections,... to the caller.
    return {
        # Store yielding under 'yielding_vehicle_id'.
        # Store priority under 'priority_vehicle_id'.
        "yielding_vehicle_id": yielding, "priority_vehicle_id": priority,
        # Store a tuple containing the text 'DE-STVO-8-1' under 'applicable_rule_ids'.
        # Store a tuple containing the text '§ 8' under 'source_sections'.
        "applicable_rule_ids": ("DE-STVO-8-1",), "source_sections": ("§ 8",),
        # Store PROFILE under 'regulatory_profile'.
        # Store an empty tuple under 'target_candidate_path_ids'.
        "regulatory_profile": PROFILE, "target_candidate_path_ids": (),
        # Store a tuple containing the text 'RIGHT' under 'relative_approaches'.
        # Store 7.0 under 'timestamp'.
        "relative_approaches": ("RIGHT",), "timestamp": 7.0,
        # Store a tuple containing the text 'ZONE' under 'shared_conflict_zone_ids'.
        # Store a tuple containing the text 'CROSSING' under 'conflict_types'.
        "shared_conflict_zone_ids": ("ZONE",), "conflict_types": ("CROSSING",),
        # Store True under 'spatial_conflict_possible'.
        "spatial_conflict_possible": True,
    }


# Local graph using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Output: a dictionary containing node_ids, precedence_edges, unresolved_relations.
def local_graph(ego, yielding, priority):
    # Set nodes to a tuple built from the sorted values from a set containing ego, yielding, priority.
    nodes = tuple(sorted({ego, yielding, priority}))
    # Set edges to a tuple containing the result of edge(yielding, priority).
    edges = (edge(yielding, priority),)
    # Return a dictionary containing node_ids, precedence_edges, unresolved_relations to the caller.
    return {"node_ids": nodes, "precedence_edges": edges,
            # Store an empty tuple under 'unresolved_relations'.
            "unresolved_relations": (),
            # Evaluate the result of RegulatoryPrecedenceGraphBuilder.analyse(nodes, edges) as part of the
            # enclosing expression.
            **RegulatoryPrecedenceGraphBuilder.analyse(nodes, edges)}


# Empty local using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Output: a dictionary containing node_ids, precedence_edges, unresolved_relations.
def empty_local(ego):
    # Return a dictionary containing node_ids, precedence_edges, unresolved_relations to the caller.
    return {"node_ids": (ego,), "precedence_edges": (),
            # Store an empty tuple under 'unresolved_relations'.
            "unresolved_relations": (),
            # Evaluate the result of RegulatoryPrecedenceGraphBuilder.analyse(a tuple containing ego, an empty
            # tuple) as part of the enclosing expression.
            **RegulatoryPrecedenceGraphBuilder.analyse((ego,), ())}


# Assemble using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input local: the supplied local.
# Input messages: the supplied messages.
# Output: the result of JointLocalPrecedenceGraphAssembler().assemble(ego, 7.0, local, messages).
def assemble(ego, local, messages):
    # Return the result of JointLocalPrecedenceGraphAssembler().assemble(ego, 7.0, local, messages) to the caller.
    return JointLocalPrecedenceGraphAssembler().assemble(ego, 7.0, local, messages)


# Keys using the inputs and processing steps below.
# Input result: the supplied result.
# Output: a tuple built from a lazy sequence of a tuple containing item at 'yielding_vehicle_id', item at
# 'priority_vehicle_id' for item in result at 'joint_precedence_edges'.
def keys(result):
    # Return a tuple built from a lazy sequence of a tuple containing item at 'yielding_vehicle_id', item at
    # 'priority_vehicle_id' for item in result at 'joint_precedence_edges' to the caller.
    return tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                 # Evaluate result at 'joint_precedence_edges' as part of the enclosing expression.
                 for item in result["joint_precedence_edges"])


# Check one local claim remains independently inspectable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_one_local_claim_remains_independently_inspectable():
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), an empty tuple).
    result = assemble("A", local_graph("A", "A", "B"), ())
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B'; otherwise
    # raise AssertionError.
    assert keys(result) == (("A", "B"),)
    # Require a tuple built from a lazy sequence of a tuple containing item['yielding_vehicle_id'],
    # item['priority_vehicle_id'] for item in result at 'local_precedence_edges' equals keys from keys; otherwise
    # raise AssertionError.
    assert tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                 # Evaluate result at 'local_precedence_edges' as part of the enclosing expression.
                 for item in result["local_precedence_edges"]) == keys(result)
    # Require result at 'communicated_precedence_edges' equals an empty tuple; otherwise raise AssertionError.
    assert result["communicated_precedence_edges"] == ()


# Check v2 valid mutual voluntary claims are negotiable not disagreement using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_v2_valid_mutual_voluntary_claims_are_negotiable_not_disagreement():
    # Set a to the result of replace(the result of claim(the text 'A', the text 'A', the text 'B')).
    a=replace(claim("A","A","B"),applicable_rule_ids=("DE-STVO-11-3",),
        # Supply source_sections as a tuple containing the text '§ 11'.
        # Supply negotiation_eligible_ambiguity as True.
        source_sections=("§ 11",),negotiation_eligible_ambiguity=True)
    # Set b to the result of replace(a).
    b=replace(a,sender_id="B",yielding_vehicle_id="B",priority_vehicle_id="A")
    # Set result to the result of JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble(the text 'A', 7.0,
    # the result of empty_local(the text 'A'), a tuple containing a, b).
    result=JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble("A",7.,empty_local("A"),(a,b))
    # Require the negation of result at 'communicated_disagreements'; otherwise raise AssertionError.
    assert not result["communicated_disagreements"]
    # Require result at 'negotiation_eligible_ambiguities' equals a tuple containing a tuple containing the text
    # 'A', the text 'B'; otherwise raise AssertionError.
    assert result["negotiation_eligible_ambiguities"]==(("A","B"),)
    # Require the result of NegotiationEnvironment.classify_status(result) is the same object as
    # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE; otherwise raise AssertionError.
    assert NegotiationEnvironment.classify_status(result) is NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE
    # Import MAPPOBehaviorActionProvider from negotiation_training.mappo_provider for the operations below.
    from negotiation_training.mappo_provider import MAPPOBehaviorActionProvider
    # Set factors to the result of MAPPOBehaviorActionProvider._eligible_factors(a tuple containing the text 'A',
    # the text 'B', result at 'joint_precedence_edges', the text...).
    factors=MAPPOBehaviorActionProvider._eligible_factors(("A","B"),
        # Supply result at 'joint_precedence_edges' to MAPPOBehaviorActionProvider._eligible_factors.
        result["joint_precedence_edges"], "NEGOTIATION_REQUIRED_REGULATORY_CYCLE")
    # Require the number of entries in factors equals 2 and whether every item is true in a lazy sequence of
    # mask.feasibility equals (True, True) for (_, mask) in factors; otherwise raise AssertionError.
    assert len(factors)==2 and all(mask.feasibility==(True,True) for _,mask in factors)


# Apply dict(source_conflict_graph_timestamp=6.0) as a decorator to configure the following definition.
@pytest.mark.parametrize("changes", [dict(timestamp=6.),dict(source_conflict_graph_timestamp=6.),
    # Supply shared_conflict_zone_ids as an empty tuple.
    # Supply applicable_rule_ids as an empty tuple.
    # Supply sender_id as the text 'unrelated'.
    dict(shared_conflict_zone_ids=()),dict(applicable_rule_ids=()),dict(sender_id="unrelated"),
    # Supply source_observation_age_seconds as None.
    # Supply source_observation_age_seconds as a floating-point number built from the text 'nan'.
    dict(source_observation_age_seconds=None),dict(source_observation_age_seconds=float("nan")),
    # Supply applicable_rule_ids as a tuple containing the text 'UNSUPPORTED_RULE'.
    dict(applicable_rule_ids=("UNSUPPORTED_RULE",))])
# Check v2 missing or incompatible source cannot be negotiated using the setup, calls, and assertions below.
# Input changes: the supplied changes.
# Output: no explicit value; normal completion returns None.
def test_v2_missing_or_incompatible_source_cannot_be_negotiated(changes):
    # Set message to the result of replace(the result of claim(the text 'B', the text 'B', the text 'A')).
    message=replace(claim("B","B","A"),**changes)
    # Set result to the result of JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble(the text 'A', 7.0,
    # the result of empty_local(the text 'A'), a tuple containing message).
    result=JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble("A",7.,empty_local("A"),(message,))
    # Require result at 'source_snapshot_mismatches' and the negation of result at 'joint_precedence_edges';
    # otherwise raise AssertionError.
    assert result["source_snapshot_mismatches"] and not result["joint_precedence_edges"]


# Check v2 mandatory local peer reciprocal is blocked even with one received claim using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_v2_mandatory_local_peer_reciprocal_is_blocked_even_with_one_received_claim():
    # Set result to the result of JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble(the text 'A', 7.0,
    # the result of local_graph(the text 'A', the text 'A', the text 'B'), a tuple...).
    result=JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble("A",7.,
        # Supply the result of local_graph(the text 'A', the text 'A', the text 'B') to
        # JointLocalPrecedenceGraphAssembler(runtime_v2=True).assemble.
        local_graph("A","A","B"),(claim("B","B","A"),))
    # Require the result of NegotiationEnvironment.classify_status(result) is the same object as
    # NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT; otherwise raise AssertionError.
    assert NegotiationEnvironment.classify_status(result) is NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT


# Check duplicate claims merge and preserve all supporting senders using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_duplicate_claims_merge_and_preserve_all_supporting_senders():
    # Set messages to a tuple containing the result of claim(the text 'A', the text 'A', the text 'B'), the result
    # of claim(the text 'B', the text...
    messages = (claim("A", "A", "B"), claim("B", "A", "B"))
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), messages).
    result = assemble("A", local_graph("A", "A", "B"), messages)
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B'; otherwise
    # raise AssertionError.
    assert keys(result) == (("A", "B"),)
    # Require result at 'duplicate_claims_merged' equals 2; otherwise raise AssertionError.
    assert result["duplicate_claims_merged"] == 2
    # Require result['joint_precedence_edges'][0] at 'supporting_sender_ids' equals a tuple containing the text
    # 'A', the text 'B'; otherwise raise AssertionError.
    assert result["joint_precedence_edges"][0]["supporting_sender_ids"] == ("A", "B")
    # Require result['joint_precedence_edges'][0] at 'edge_origin' equals the text 'LOCAL_AND_COMMUNICATED';
    # otherwise raise AssertionError.
    assert result["joint_precedence_edges"][0]["edge_origin"] == "LOCAL_AND_COMMUNICATED"


# Check fixed point expands connected component without hop limit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_fixed_point_expands_connected_component_without_hop_limit():
    # Set messages to a tuple built from a lazy sequence of the result of claim(a, a, b) for (a, b) in a tuple
    # containing a tuple containing 'D', 'E', a tuple containing 'C', 'D', a tuple containing 'B', 'C', a tuple
    # containing...
    messages = tuple(claim(a, a, b) for a, b in (
        # Include a tuple containing the text 'D', the text 'E' in this tuple.
        ("D", "E"), ("C", "D"), ("B", "C"), ("X", "Y")
    ))
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), messages).
    result = assemble("A", local_graph("A", "A", "B"), messages)
    # Require result at 'joint_node_ids' equals a tuple containing the text 'A', the text 'B', the text 'C', the
    # text 'D', the text 'E'; otherwise raise AssertionError.
    assert result["joint_node_ids"] == ("A", "B", "C", "D", "E")
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B', a tuple
    # containing the text 'B', the text 'C', a tuple...; otherwise raise AssertionError.
    assert keys(result) == (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"))
    # Require the number of entries in result at 'ignored_unconnected_claims' equals 1; otherwise raise
    # AssertionError.
    assert len(result["ignored_unconnected_claims"]) == 1


# Check four av cycle is reconstructed independently by every member using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_four_av_cycle_is_reconstructed_independently_by_every_member():
    # Set local to a dictionary containing A, B, C, D.
    local = {
        # Store the result of local_graph(the text 'A', the text 'A', the text 'B') under 'A'.
        "A": local_graph("A", "A", "B"),
        # Store the result of local_graph(the text 'B', the text 'B', the text 'C') under 'B'.
        "B": local_graph("B", "B", "C"),
        # Store the result of local_graph(the text 'C', the text 'C', the text 'D') under 'C'.
        "C": local_graph("C", "C", "D"),
        # Store the result of local_graph(the text 'D', the text 'D', the text 'A') under 'D'.
        "D": local_graph("D", "D", "A"),
    }
    # Set bus to the result of V2VPrecedenceClaimBus().
    bus = V2VPrecedenceClaimBus()
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(7.0)
    # Iterate over a tuple containing the text 'A', the text 'B', the text 'C', the text 'D', binding each item to
    # sender.
    for sender in ("A", "B", "C", "D"):
        # Set (source, target) to a tuple containing local[sender]['precedence_edges'][0] at
        # 'yielding_vehicle_id', local[sender]['precedence_edges'][0] at...
        source, target = local[sender]["precedence_edges"][0]["yielding_vehicle_id"], local[sender]["precedence_edges"][0]["priority_vehicle_id"]
        # Call bus.publish with the supplied arguments.
        bus.publish(claim(sender, source, target))
    # Call bus.freeze_step with the supplied arguments.
    bus.freeze_step(7.0)
    # Set expected to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the
    # text 'B', the text 'C', a tuple...
    expected = (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"))
    # Iterate over a tuple containing the text 'A', the text 'B', the text 'C', the text 'D', binding each item to
    # ego.
    for ego in ("A", "B", "C", "D"):
        # Set result to the result of assemble(ego, local at ego, the result of bus.current_messages(7.0, ego)).
        result = assemble(ego, local[ego], bus.current_messages(7.0, ego))
        # Require keys from keys equals expected; otherwise raise AssertionError.
        assert keys(result) == expected
        # Require result at 'cycle_detected' is the same object as True; otherwise raise AssertionError.
        assert result["cycle_detected"] is True
        # Require result at 'cycle_members' equals a tuple containing the text 'A', the text 'B', the text 'C',
        # the text 'D'; otherwise raise AssertionError.
        assert result["cycle_members"] == ("A", "B", "C", "D")
        # Require result at 'strongly_connected_components' equals a tuple containing a tuple containing the text
        # 'A', the text 'B', the text 'C', the text 'D'; otherwise raise AssertionError.
        assert result["strongly_connected_components"] == (("A", "B", "C", "D"),)


# Check partial information never invents missing edge using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_partial_information_never_invents_missing_edge():
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), a tuple...).
    result = assemble("A", local_graph("A", "A", "B"), (claim("B", "B", "C"),))
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B', a tuple
    # containing the text 'B', the text 'C'; otherwise raise AssertionError.
    assert keys(result) == (("A", "B"), ("B", "C"))
    # Require the text 'D' does not belong to result at 'joint_node_ids'; otherwise raise AssertionError.
    assert "D" not in result["joint_node_ids"]


# Check opposite claims are preserved and diagnosed not voted away using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_opposite_claims_are_preserved_and_diagnosed_not_voted_away():
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), a tuple...).
    result = assemble("A", local_graph("A", "A", "B"), (
        # Include the result of claim(the text 'A', the text 'A', the text 'B') in this tuple.
        claim("A", "A", "B"), claim("B", "B", "A"),
    ))
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B', a tuple
    # containing the text 'B', the text 'A'; otherwise raise AssertionError.
    assert keys(result) == (("A", "B"), ("B", "A"))
    # Require result['communicated_disagreements'][0] at 'diagnostic' equals the text
    # 'COMMUNICATED_PRECEDENCE_DISAGREEMENT'; otherwise raise AssertionError.
    assert result["communicated_disagreements"][0]["diagnostic"] == "COMMUNICATED_PRECEDENCE_DISAGREEMENT"
    # Require the result of NegotiationEnvironment.classify_status(result) is the same object as
    # NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT; otherwise raise AssertionError.
    assert NegotiationEnvironment.classify_status(result) is NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT


# Check profile and source mismatches are not authoritative using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_profile_and_source_mismatches_are_not_authoritative():
    # Set bad_profile to the result of claim(the text 'B', the text 'B', the text 'C').
    bad_profile = claim("B", "B", "C", profile="OTHER_JURISDICTION")
    # Set stale to the result of claim(the text 'B', the text 'B', the text 'D').
    stale = claim("B", "B", "D", timestamp=6.0)
    # Set result to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), a tuple...).
    result = assemble("A", local_graph("A", "A", "B"), (bad_profile, stale))
    # Require keys from keys equals a tuple containing a tuple containing the text 'A', the text 'B'; otherwise
    # raise AssertionError.
    assert keys(result) == (("A", "B"),)
    # Require the number of entries in result at 'regulatory_profile_mismatches' equals 1; otherwise raise
    # AssertionError.
    assert len(result["regulatory_profile_mismatches"]) == 1
    # Require the number of entries in result at 'source_snapshot_mismatches' equals 1; otherwise raise
    # AssertionError.
    assert len(result["source_snapshot_mismatches"]) == 1


# Check bus never reuses previous step messages using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_bus_never_reuses_previous_step_messages():
    # Set bus to the result of V2VPrecedenceClaimBus().
    bus = V2VPrecedenceClaimBus()
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(7.0)
    # Call bus.publish with the supplied arguments.
    bus.publish(claim("A", "A", "B"))
    # Call bus.freeze_step with the supplied arguments.
    bus.freeze_step(7.0)
    # Require the number of entries in the result of bus.current_messages(7.0) equals 1; otherwise raise
    # AssertionError.
    assert len(bus.current_messages(7.0)) == 1
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(8.0)
    # Call bus.freeze_step with the supplied arguments.
    bus.freeze_step(8.0)
    # Require the result of bus.current_messages(8.0) equals an empty tuple; otherwise raise AssertionError.
    assert bus.current_messages(8.0) == ()
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError):
        # Call bus.current_messages with the supplied arguments.
        bus.current_messages(7.0)


# Check message and ego processing order are invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_message_and_ego_processing_order_are_invariant():
    # Set claims to a list containing the result of claim(the text 'B', the text 'B', the text 'C'), the result of
    # claim(the text 'C', the text...
    claims = [claim("B", "B", "C"), claim("C", "C", "D"), claim("D", "D", "A")]
    # Set forward to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A',
    # the text 'B'), claims).
    forward = assemble("A", local_graph("A", "A", "B"), claims)
    # Set reverse to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A',
    # the text 'B'), a tuple built...).
    reverse = assemble("A", local_graph("A", "A", "B"), tuple(reversed(claims)))
    # Iterate over a tuple containing the text 'joint_node_ids', the text 'joint_precedence_edges', the text
    # 'cycle_detected', the text..., binding each item to field.
    for field in ("joint_node_ids", "joint_precedence_edges", "cycle_detected",
                  "strongly_connected_components"):
        # Require forward at field equals reverse at field; otherwise raise AssertionError.
        assert forward[field] == reverse[field]
    # Set outputs to an empty dictionary.
    outputs = {}
    # Set locals_by_ego to a dictionary containing A, B.
    locals_by_ego = {"A": local_graph("A", "A", "B"), "B": local_graph("B", "B", "C")}
    # Iterate over a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text
    # 'B', the text 'A', binding each item to order.
    for order in (("A", "B"), ("B", "A")):
        # Set bus to the result of V2VPrecedenceClaimBus().
        # Call bus.begin_step with the supplied arguments.
        bus = V2VPrecedenceClaimBus(); bus.begin_step(7.0)
        # Iterate over order, binding each item to sender.
        for sender in order:
            # Set e to locals_by_ego[sender]['precedence_edges'] at 0.
            e = locals_by_ego[sender]["precedence_edges"][0]
            # Call bus.publish with the supplied arguments.
            bus.publish(claim(sender, e["yielding_vehicle_id"], e["priority_vehicle_id"]))
        # Call bus.freeze_step with the supplied arguments.
        bus.freeze_step(7.0)
        # Set outputs[order] to a dictionary of ego mapped to keys from keys for ego in order.
        outputs[order] = {ego: keys(assemble(ego, locals_by_ego[ego], bus.current_messages(7.0))) for ego in order}
    # Require outputs['A', 'B'] at 'A' equals outputs['B', 'A'] at 'A'; otherwise raise AssertionError.
    assert outputs[("A", "B")]["A"] == outputs[("B", "A")]["A"]
    # Require outputs['A', 'B'] at 'B' equals outputs['B', 'A'] at 'B'; otherwise raise AssertionError.
    assert outputs[("A", "B")]["B"] == outputs[("B", "A")]["B"]


# Check message schema has no route truth and probability is irrelevant using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_message_schema_has_no_route_truth_and_probability_is_irrelevant():
    # Set fields to a set built from PrecedenceClaimMessage.__dataclass_fields__.
    fields = set(PrecedenceClaimMessage.__dataclass_fields__)
    # Require the result of fields.isdisjoint(a set containing the text 'route_id', the text 'route_index', the
    # text 'ground_truth_route_id',...); otherwise raise AssertionError.
    assert fields.isdisjoint({"route_id", "route_index", "ground_truth_route_id",
                              "intention_probability"})
    # Set original to the result of claim(the text 'A', the text 'A', the text 'B').
    original = claim("A", "A", "B")
    # Require replace(original, source_observation_age_seconds=9.0).yielding_vehicle_id equals
    # original.yielding_vehicle_id; otherwise raise AssertionError.
    assert replace(original, source_observation_age_seconds=9.0).yielding_vehicle_id == original.yielding_vehicle_id


# Check changing route truth does not change sender local claim using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_changing_route_truth_does_not_change_sender_local_claim():
    # Import local_fixture from tests.test_negotiation_learning for the operations below.
    from tests.test_negotiation_learning import local_fixture
    # Set first to the result of local_fixture().
    first = local_fixture()
    # Set local to the result of RegulatoryPrecedenceGraphBuilder().build(first).
    local = RegulatoryPrecedenceGraphBuilder().build(first)
    # Set first_message to the result of RegulatoryPrecedenceGraphBuilder.claim_messages(first, local, 2.0).
    first_message = RegulatoryPrecedenceGraphBuilder.claim_messages(first, local, 2.0)
    # Update first.tracks['B'] with the supplied entries.
    first.tracks["B"].update({
        # Store the text 'contradictory_new_route' under 'route_id'.
        # Store the negative of 100 under 'route_index'.
        "route_id": "contradictory_new_route", "route_index": -100,
        "ground_truth_route_id": "contradictory_new_truth",
    })
    # Set second_local to the result of RegulatoryPrecedenceGraphBuilder().build(first).
    second_local = RegulatoryPrecedenceGraphBuilder().build(first)
    # Set second_message to the result of RegulatoryPrecedenceGraphBuilder.claim_messages(first, second_local,
    # 2.0).
    second_message = RegulatoryPrecedenceGraphBuilder.claim_messages(
        # Supply second_local to RegulatoryPrecedenceGraphBuilder.claim_messages.
        first, second_local, 2.0
    )
    # Require first_message equals second_message; otherwise raise AssertionError.
    assert first_message == second_message


# Define ObservationLDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class ObservationLDM:
    # Set ego_id to the text 'A'.
    ego_id = "A"
    # Set tracks to a dictionary containing A.
    tracks = {"A": {"speed": 1.0, "last_observed_time": 7.0}}


# Check graph observation consumes joint graph and has no control calls using the setup, calls, and assertions
# below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_graph_observation_consumes_joint_graph_and_has_no_control_calls(monkeypatch):
    # Set calls to an empty list.
    calls = []
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Import traci for use in this module.
        import traci
        # Call monkeypatch.setattr with the supplied arguments.
        monkeypatch.setattr(traci.vehicle, "setSpeed", lambda *args: calls.append(args))
    # Handle Exception using the recovery steps below.
    except Exception:
        # Keep this block syntactically valid without performing an operation.
        pass
    # Set joint to the result of assemble(the text 'A', the result of local_graph(the text 'A', the text 'A', the
    # text 'B'), a tuple...).
    joint = assemble("A", local_graph("A", "A", "B"), (claim("B", "B", "C"),))
    # Set observation to the result of GraphObservationBuilder().build(ObservationLDM(), 7.0, joint).to_dict().
    observation = GraphObservationBuilder().build(ObservationLDM(), 7.0, joint).to_dict()
    # Require observation at 'node_ids' equals a tuple containing the text 'A', the text 'B', the text 'C';
    # otherwise raise AssertionError.
    assert observation["node_ids"] == ("A", "B", "C")
    # Require the number of entries in observation at 'edge_index' equals 2; otherwise raise AssertionError.
    assert len(observation["edge_index"]) == 2
    # Require observation['metadata'] at 'graph_scope' equals the text 'JOINT_LOCAL_V2V'; otherwise raise
    # AssertionError.
    assert observation["metadata"]["graph_scope"] == "JOINT_LOCAL_V2V"
    # Require observation['metadata'] at 'communication_model' equals the text 'IDEAL_SAME_STEP_V2V'; otherwise
    # raise AssertionError.
    assert observation["metadata"]["communication_model"] == "IDEAL_SAME_STEP_V2V"
    # Require calls equals an empty list; otherwise raise AssertionError.
    assert calls == []
