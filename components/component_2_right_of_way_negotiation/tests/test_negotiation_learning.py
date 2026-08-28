"""Deterministic tests for the shadow Step 5A negotiation interface."""

from copy import deepcopy

from negotiation_learning import (
    NegotiationEnvironment, NegotiationStatus,
    RegulatoryPrecedenceGraphBuilder,
)


def raw_edge(source, target):
    return {"yielding_vehicle_id": source, "priority_vehicle_id": target}


class FakeLDM:
    def __init__(self, conflict, temporal, regulatory, tracks=None):
        self.ego_id = conflict["ego_id"]
        self.current_conflict_graph = conflict
        self.current_temporal_assessment = temporal
        self.current_regulatory_assessment = regulatory
        self.tracks = tracks or {
            self.ego_id: track(self.ego_id), "B": track("B"),
        }

    def get_current_conflict_graph(self):
        return self.current_conflict_graph

    def get_current_temporal_assessment(self):
        return self.current_temporal_assessment

    def get_current_regulatory_assessment(self):
        return self.current_regulatory_assessment


def track(vehicle_id, speed=4.0):
    return {
        "id": vehicle_id, "speed": speed, "max_acceleration_mps2": 2.0,
        "comfortable_deceleration_mps2": 4.5, "max_speed_mps": 13.89,
        "confidence": 1.0, "is_observed": True, "last_observed_time": 2.0,
        "route_id": "must_not_be_read", "route_index": 99,
        "ground_truth_route_id": "must_not_be_read_either",
    }


def local_fixture(status="EGO_MUST_YIELD", timestamp=2.0, temporal_record=None):
    conflict_edge = {
        "target_track_id": "B", "ego_path_id": "A_PATH",
        "spatially_conflicting_candidate_paths": {
            "STRAIGHT": "B_PATH_STRAIGHT",
        },
        "shared_conflict_zone_ids": ("ZONE_1",),
        "conflict_types": ("CROSSING",), "spatial_conflict_possible": True,
        "intention_weighted_conflict_probability": 0.9,
    }
    conflict = {"ego_id": "A", "timestamp": timestamp,
                "ego_path_id": "A_PATH", "edges": (conflict_edge,)}
    evaluation = temporal_record or {
        "target_path_id": "B_PATH_STRAIGHT", "status": "SPATIAL_ONLY",
        "target_earliest_reachable_entry_time_s": 1.5,
        "target_can_stop_before_zone": True,
        "target_zone_occupancy_state": "BEFORE_ZONE",
    }
    temporal = {"ego_id": "A", "timestamp": timestamp, "edges": ({
        "target_id": "B", "timestamp": timestamp,
        "temporal_conflict_possible": False, "status": "SPATIAL_ONLY",
        "evaluations": (evaluation,),
    },)}
    candidate = {
        "target_candidate_path_id": "B_PATH_STRAIGHT",
        "target_candidate_manoeuvre": "STRAIGHT", "relative_approach": "RIGHT",
        "applicable_rule_ids": ("DE-STVO-8-1",),
        "source_sections": ("§ 8",), "regulatory_status": status,
    }
    regulatory = {"ego_id": "A", "timestamp": timestamp,
                  "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
                  "assessments": ({
                      "ego_id": "A", "target_id": "B", "timestamp": timestamp,
                      "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
                      "regulatory_status": status,
                      "applicable_rule_ids": ("DE-STVO-8-1",),
                      "source_sections": ("§ 8",),
                      "candidate_assessments": (candidate,),
                  },)}
    return FakeLDM(conflict, temporal, regulatory)


def test_one_precedence_edge_has_documented_direction_and_no_cycle():
    result = RegulatoryPrecedenceGraphBuilder().build(local_fixture())
    edge = result["precedence_edges"][0]
    assert (edge["yielding_vehicle_id"], edge["priority_vehicle_id"]) == ("A", "B")
    assert result["cycle_detected"] is False
    assert edge["target_candidate_path_ids"] == ("B_PATH_STRAIGHT",)
    assert edge["physical_reachability_evidence"]["evaluations"]


def test_acyclic_chain_and_disconnected_groups_have_deterministic_orders():
    builder = RegulatoryPrecedenceGraphBuilder()
    chain = builder.analyse(("A", "B", "C"), (raw_edge("A", "B"), raw_edge("B", "C")))
    assert chain["cycle_detected"] is False
    assert chain["yield_precedence_graph_topological_order"] == ("A", "B", "C")
    assert chain["regulatory_service_order"] == ("C", "B", "A")
    disconnected = builder.analyse(
        ("A", "B", "C", "D"), (raw_edge("A", "B"), raw_edge("C", "D"))
    )
    order = disconnected["yield_precedence_graph_topological_order"]
    assert order.index("A") < order.index("B") and order.index("C") < order.index("D")


def test_two_node_and_four_node_cycles_use_standard_sccs():
    builder = RegulatoryPrecedenceGraphBuilder()
    two = builder.analyse(("A", "B"), (raw_edge("A", "B"), raw_edge("B", "A")))
    assert two["cycle_detected"] is True
    assert two["strongly_connected_components"] == (("A", "B"),)
    four_edges = tuple(raw_edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")
    ))
    four = builder.analyse(("A", "B", "C", "D"), four_edges)
    assert four["cycle_members"] == ("A", "B", "C", "D")
    assert four["regulatory_service_order"] is None
    four["unresolved_relations"] = ()
    assert NegotiationEnvironment.classify_status(four) is (
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE
    )


def test_no_spatial_edge_means_no_active_conflict_even_with_extra_track():
    ldm = local_fixture()
    ldm.current_conflict_graph["edges"] = ()
    ldm.tracks["irrelevant"] = track("irrelevant")
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    assert result["participant_ids"] == ("A",)
    assert result["negotiation_status"] == NegotiationStatus.NO_ACTIVE_CONFLICT.value


def test_unresolved_manoeuvre_is_retained_without_guessed_edge():
    result = NegotiationEnvironment().build_snapshot(
        local_fixture("UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"), 2.0
    )
    assert result["precedence_edges"] == ()
    assert result["unresolved_relations"][0]["regulatory_status"] == "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"
    assert result["negotiation_status"] == NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value


def test_route_truth_and_prediction_probability_do_not_change_structure():
    first = local_fixture()
    second = deepcopy(first)
    second.tracks["B"].update({"route_id": "opposite", "route_index": -1,
                               "ground_truth_route_id": "opposite_truth"})
    second.current_conflict_graph["edges"][0]["intention_weighted_conflict_probability"] = 0.01
    environment = NegotiationEnvironment()
    a = environment.build_snapshot(first, 2.0)
    b = environment.build_snapshot(second, 2.0)
    assert a["precedence_edges"] == b["precedence_edges"]
    assert a["participant_ids"] == b["participant_ids"]


def test_stopped_vehicle_with_unresolved_nominal_timing_remains_participant():
    temporal_record = {
        "target_path_id": "B_PATH_STRAIGHT", "status": "UNRESOLVED_SPEED",
        "target_speed_mps": 0.0,
        "target_earliest_reachable_entry_time_s": 3.2,
        "target_can_stop_before_zone": True,
        "target_zone_occupancy_state": "BEFORE_ZONE",
        "reachability_interpretation": "UNCOMMITTED_CAN_STOP",
    }
    ldm = local_fixture(temporal_record=temporal_record)
    ldm.tracks["B"]["speed"] = 0.0
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    assert "B" in result["participant_ids"]
    evidence = result["precedence_edges"][0]["physical_reachability_evidence"]
    assert evidence["evaluations"][0]["target_earliest_reachable_entry_time_s"] == 3.2


def test_source_timestamp_mismatch_is_explicit():
    ldm = local_fixture()
    ldm.current_temporal_assessment["timestamp"] = 3.0
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    assert result["source_snapshot_consistent"] is False
    assert result["negotiation_status"] == NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value


def test_snapshot_has_no_control_or_reward_side_effect_interface(monkeypatch):
    calls = []
    try:
        import traci
        monkeypatch.setattr(traci.vehicle, "setSpeed", lambda *args: calls.append(args))
    except Exception:
        pass
    result = NegotiationEnvironment().build_snapshot(local_fixture(), 2.0)
    assert calls == []
    assert result["control_actions_issued"] == 0
    assert result["available_action_schema"] == ("KEEP_CLAIM", "RELINQUISH_CLAIM")
    assert "reward" not in result
    assert result["graph_observation"]["metadata"]["tensor_encoding_status"] == "NOT_IMPLEMENTED"
