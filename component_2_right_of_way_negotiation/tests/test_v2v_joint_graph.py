"""Regression tests for decentralized same-step joint graph assembly."""

from dataclasses import replace

import pytest

from negotiation_learning import (
    JointLocalPrecedenceGraphAssembler, NegotiationEnvironment,
    NegotiationStatus, PrecedenceClaimMessage,
    RegulatoryPrecedenceGraphBuilder, V2VPrecedenceClaimBus,
)
from negotiation_learning.observation_builder import GraphObservationBuilder


PROFILE = "DE_STVO_UNCONTROLLED_4WAY_V1"


def claim(sender, yielding, priority, timestamp=7.0, profile=PROFILE):
    return PrecedenceClaimMessage(
        sender, timestamp, yielding, priority, ("DE-STVO-8-1",),
        ("§ 8",), profile, ("ZONE",), ("CROSSING",),
        (f"{priority}_PATH",), timestamp, timestamp, 0.0,
    )


def edge(yielding, priority):
    return {
        "yielding_vehicle_id": yielding, "priority_vehicle_id": priority,
        "applicable_rule_ids": ("DE-STVO-8-1",), "source_sections": ("§ 8",),
        "regulatory_profile": PROFILE, "target_candidate_path_ids": (),
        "relative_approaches": ("RIGHT",), "timestamp": 7.0,
        "shared_conflict_zone_ids": ("ZONE",), "conflict_types": ("CROSSING",),
        "spatial_conflict_possible": True,
    }


def local_graph(ego, yielding, priority):
    nodes = tuple(sorted({ego, yielding, priority}))
    edges = (edge(yielding, priority),)
    return {"node_ids": nodes, "precedence_edges": edges,
            "unresolved_relations": (),
            **RegulatoryPrecedenceGraphBuilder.analyse(nodes, edges)}


def empty_local(ego):
    return {"node_ids": (ego,), "precedence_edges": (),
            "unresolved_relations": (),
            **RegulatoryPrecedenceGraphBuilder.analyse((ego,), ())}


def assemble(ego, local, messages):
    return JointLocalPrecedenceGraphAssembler().assemble(ego, 7.0, local, messages)


def keys(result):
    return tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                 for item in result["joint_precedence_edges"])


def test_one_local_claim_remains_independently_inspectable():
    result = assemble("A", local_graph("A", "A", "B"), ())
    assert keys(result) == (("A", "B"),)
    assert tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                 for item in result["local_precedence_edges"]) == keys(result)
    assert result["communicated_precedence_edges"] == ()


def test_duplicate_claims_merge_and_preserve_all_supporting_senders():
    messages = (claim("A", "A", "B"), claim("B", "A", "B"))
    result = assemble("A", local_graph("A", "A", "B"), messages)
    assert keys(result) == (("A", "B"),)
    assert result["duplicate_claims_merged"] == 2
    assert result["joint_precedence_edges"][0]["supporting_sender_ids"] == ("A", "B")
    assert result["joint_precedence_edges"][0]["edge_origin"] == "LOCAL_AND_COMMUNICATED"


def test_fixed_point_expands_connected_component_without_hop_limit():
    messages = tuple(claim(a, a, b) for a, b in (
        ("D", "E"), ("C", "D"), ("B", "C"), ("X", "Y")
    ))
    result = assemble("A", local_graph("A", "A", "B"), messages)
    assert result["joint_node_ids"] == ("A", "B", "C", "D", "E")
    assert keys(result) == (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"))
    assert len(result["ignored_unconnected_claims"]) == 1


def test_four_av_cycle_is_reconstructed_independently_by_every_member():
    local = {
        "A": local_graph("A", "A", "B"),
        "B": local_graph("B", "B", "C"),
        "C": local_graph("C", "C", "D"),
        "D": local_graph("D", "D", "A"),
    }
    bus = V2VPrecedenceClaimBus()
    bus.begin_step(7.0)
    for sender in ("A", "B", "C", "D"):
        source, target = local[sender]["precedence_edges"][0]["yielding_vehicle_id"], local[sender]["precedence_edges"][0]["priority_vehicle_id"]
        bus.publish(claim(sender, source, target))
    bus.freeze_step(7.0)
    expected = (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"))
    for ego in ("A", "B", "C", "D"):
        result = assemble(ego, local[ego], bus.current_messages(7.0, ego))
        assert keys(result) == expected
        assert result["cycle_detected"] is True
        assert result["cycle_members"] == ("A", "B", "C", "D")
        assert result["strongly_connected_components"] == (("A", "B", "C", "D"),)


def test_partial_information_never_invents_missing_edge():
    result = assemble("A", local_graph("A", "A", "B"), (claim("B", "B", "C"),))
    assert keys(result) == (("A", "B"), ("B", "C"))
    assert "D" not in result["joint_node_ids"]


def test_opposite_claims_are_preserved_and_diagnosed_not_voted_away():
    result = assemble("A", local_graph("A", "A", "B"), (
        claim("A", "A", "B"), claim("B", "B", "A"),
    ))
    assert keys(result) == (("A", "B"), ("B", "A"))
    assert result["communicated_disagreements"][0]["diagnostic"] == "COMMUNICATED_PRECEDENCE_DISAGREEMENT"
    assert NegotiationEnvironment.classify_status(result) is NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT


def test_profile_and_source_mismatches_are_not_authoritative():
    bad_profile = claim("B", "B", "C", profile="OTHER_JURISDICTION")
    stale = claim("B", "B", "D", timestamp=6.0)
    result = assemble("A", local_graph("A", "A", "B"), (bad_profile, stale))
    assert keys(result) == (("A", "B"),)
    assert len(result["regulatory_profile_mismatches"]) == 1
    assert len(result["source_snapshot_mismatches"]) == 1


def test_bus_never_reuses_previous_step_messages():
    bus = V2VPrecedenceClaimBus()
    bus.begin_step(7.0)
    bus.publish(claim("A", "A", "B"))
    bus.freeze_step(7.0)
    assert len(bus.current_messages(7.0)) == 1
    bus.begin_step(8.0)
    bus.freeze_step(8.0)
    assert bus.current_messages(8.0) == ()
    with pytest.raises(RuntimeError):
        bus.current_messages(7.0)


def test_message_and_ego_processing_order_are_invariant():
    claims = [claim("B", "B", "C"), claim("C", "C", "D"), claim("D", "D", "A")]
    forward = assemble("A", local_graph("A", "A", "B"), claims)
    reverse = assemble("A", local_graph("A", "A", "B"), tuple(reversed(claims)))
    for field in ("joint_node_ids", "joint_precedence_edges", "cycle_detected",
                  "strongly_connected_components"):
        assert forward[field] == reverse[field]
    outputs = {}
    locals_by_ego = {"A": local_graph("A", "A", "B"), "B": local_graph("B", "B", "C")}
    for order in (("A", "B"), ("B", "A")):
        bus = V2VPrecedenceClaimBus(); bus.begin_step(7.0)
        for sender in order:
            e = locals_by_ego[sender]["precedence_edges"][0]
            bus.publish(claim(sender, e["yielding_vehicle_id"], e["priority_vehicle_id"]))
        bus.freeze_step(7.0)
        outputs[order] = {ego: keys(assemble(ego, locals_by_ego[ego], bus.current_messages(7.0))) for ego in order}
    assert outputs[("A", "B")]["A"] == outputs[("B", "A")]["A"]
    assert outputs[("A", "B")]["B"] == outputs[("B", "A")]["B"]


def test_message_schema_has_no_route_truth_and_probability_is_irrelevant():
    fields = set(PrecedenceClaimMessage.__dataclass_fields__)
    assert fields.isdisjoint({"route_id", "route_index", "ground_truth_route_id",
                              "intention_probability"})
    original = claim("A", "A", "B")
    assert replace(original, source_observation_age_seconds=9.0).yielding_vehicle_id == original.yielding_vehicle_id


def test_changing_route_truth_does_not_change_sender_local_claim():
    from tests.test_negotiation_learning import local_fixture
    first = local_fixture()
    local = RegulatoryPrecedenceGraphBuilder().build(first)
    first_message = RegulatoryPrecedenceGraphBuilder.claim_messages(first, local, 2.0)
    first.tracks["B"].update({
        "route_id": "contradictory_new_route", "route_index": -100,
        "ground_truth_route_id": "contradictory_new_truth",
    })
    second_local = RegulatoryPrecedenceGraphBuilder().build(first)
    second_message = RegulatoryPrecedenceGraphBuilder.claim_messages(
        first, second_local, 2.0
    )
    assert first_message == second_message


class ObservationLDM:
    ego_id = "A"
    tracks = {"A": {"speed": 1.0, "last_observed_time": 7.0}}


def test_graph_observation_consumes_joint_graph_and_has_no_control_calls(monkeypatch):
    calls = []
    try:
        import traci
        monkeypatch.setattr(traci.vehicle, "setSpeed", lambda *args: calls.append(args))
    except Exception:
        pass
    joint = assemble("A", local_graph("A", "A", "B"), (claim("B", "B", "C"),))
    observation = GraphObservationBuilder().build(ObservationLDM(), 7.0, joint).to_dict()
    assert observation["node_ids"] == ("A", "B", "C")
    assert len(observation["edge_index"]) == 2
    assert observation["metadata"]["graph_scope"] == "JOINT_LOCAL_V2V"
    assert observation["metadata"]["communication_model"] == "IDEAL_SAME_STEP_V2V"
    assert calls == []
