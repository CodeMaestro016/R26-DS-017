"""Deterministic tests for the shadow Step 5A negotiation interface."""

# Import deepcopy from copy for the operations below.
from copy import deepcopy

# Import NegotiationEnvironment, NegotiationStatus, RegulatoryPrecedenceGraphBuilder from negotiation_learning for
# the operations below.
from negotiation_learning import (
    NegotiationEnvironment, NegotiationStatus,
    RegulatoryPrecedenceGraphBuilder,
)


# Raw edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id.
def raw_edge(source, target):
    # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id to the caller.
    return {"yielding_vehicle_id": source, "priority_vehicle_id": target}


# Define FakeLDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class FakeLDM:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input conflict: the supplied conflict.
    # Input temporal: the supplied temporal.
    # Input regulatory: the supplied regulatory.
    # Input tracks: the supplied tracks.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, conflict, temporal, regulatory, tracks=None):
        # Set self.ego_id to conflict at 'ego_id'.
        self.ego_id = conflict["ego_id"]
        # Set self.current_conflict_graph to conflict.
        self.current_conflict_graph = conflict
        # Set self.current_temporal_assessment to temporal.
        self.current_temporal_assessment = temporal
        # Set self.current_regulatory_assessment to regulatory.
        self.current_regulatory_assessment = regulatory
        # Set self.tracks to tracks or a dictionary containing B.
        self.tracks = tracks or {
            # Store the result of track(self.ego_id) under self.ego_id.
            # Store the result of track(the text 'B') under 'B'.
            self.ego_id: track(self.ego_id), "B": track("B"),
        }

    # Get current conflict graph using the inputs and processing steps below.
    # Output: self.current_conflict_graph.
    def get_current_conflict_graph(self):
        # Return self.current_conflict_graph to the caller.
        return self.current_conflict_graph

    # Get current temporal assessment using the inputs and processing steps below.
    # Output: self.current_temporal_assessment.
    def get_current_temporal_assessment(self):
        # Return self.current_temporal_assessment to the caller.
        return self.current_temporal_assessment

    # Get current regulatory assessment using the inputs and processing steps below.
    # Output: self.current_regulatory_assessment.
    def get_current_regulatory_assessment(self):
        # Return self.current_regulatory_assessment to the caller.
        return self.current_regulatory_assessment


# Track using the inputs and processing steps below.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input speed: the supplied speed.
# Output: a dictionary containing id, speed, max_acceleration_mps2, comfortable_deceleration_mps2,
# max_speed_mps,...
def track(vehicle_id, speed=4.0):
    # Return a dictionary containing id, speed, max_acceleration_mps2, comfortable_deceleration_mps2,
    # max_speed_mps,... to the caller.
    return {
        # Store vehicle_id under 'id'.
        # Store speed under 'speed'.
        # Store 2.0 under 'max_acceleration_mps2'.
        "id": vehicle_id, "speed": speed, "max_acceleration_mps2": 2.0,
        # Store 4.5 under 'comfortable_deceleration_mps2'.
        # Store 13.89 under 'max_speed_mps'.
        "comfortable_deceleration_mps2": 4.5, "max_speed_mps": 13.89,
        # Store 1.0 under 'confidence'.
        # Store True under 'is_observed'.
        # Store 2.0 under 'last_observed_time'.
        "confidence": 1.0, "is_observed": True, "last_observed_time": 2.0,
        # Store the text 'must_not_be_read' under 'route_id'.
        # Store 99 under 'route_index'.
        "route_id": "must_not_be_read", "route_index": 99,
        "ground_truth_route_id": "must_not_be_read_either",
    }


# Local fixture using the inputs and processing steps below.
# Input status: the supplied status.
# Input timestamp: the supplied timestamp.
# Input temporal_record: the supplied temporal record.
# Output: the result of FakeLDM(conflict, temporal, regulatory).
def local_fixture(status="EGO_MUST_YIELD", timestamp=2.0, temporal_record=None):
    # Set conflict_edge to a dictionary containing target_track_id, ego_path_id,
    # spatially_conflicting_candidate_paths,...
    conflict_edge = {
        "target_track_id": "B", "ego_path_id": "A_PATH",
        # Store a dictionary containing STRAIGHT under 'spatially_conflicting_candidate_paths'.
        "spatially_conflicting_candidate_paths": {
            "STRAIGHT": "B_PATH_STRAIGHT",
        },
        # Store a tuple containing the text 'ZONE_1' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ("ZONE_1",),
        # Store a tuple containing the text 'CROSSING' under 'conflict_types'.
        # Store True under 'spatial_conflict_possible'.
        "conflict_types": ("CROSSING",), "spatial_conflict_possible": True,
        # Store 0.9 under 'intention_weighted_conflict_probability'.
        "intention_weighted_conflict_probability": 0.9,
    }
    # Set conflict to a dictionary containing ego_id, timestamp, ego_path_id, edges.
    conflict = {"ego_id": "A", "timestamp": timestamp,
                # Store the text 'A_PATH' under 'ego_path_id'.
                # Store a tuple containing conflict_edge under 'edges'.
                "ego_path_id": "A_PATH", "edges": (conflict_edge,)}
    # Set evaluation to temporal_record or a dictionary containing target_path_id, status,
    # target_earliest_reachable_entry_time_s,...
    evaluation = temporal_record or {
        "target_path_id": "B_PATH_STRAIGHT", "status": "SPATIAL_ONLY",
        # Store 1.5 under 'target_earliest_reachable_entry_time_s'.
        "target_earliest_reachable_entry_time_s": 1.5,
        # Store True under 'target_can_stop_before_zone'.
        "target_can_stop_before_zone": True,
        "target_zone_occupancy_state": "BEFORE_ZONE",
    }
    # Set temporal to a dictionary containing ego_id, timestamp, edges.
    temporal = {"ego_id": "A", "timestamp": timestamp, "edges": ({
        # Store the text 'B' under 'target_id'.
        # Store timestamp under 'timestamp'.
        "target_id": "B", "timestamp": timestamp,
        # Store False under 'temporal_conflict_possible'.
        # Store the text 'SPATIAL_ONLY' under 'status'.
        "temporal_conflict_possible": False, "status": "SPATIAL_ONLY",
        # Store a tuple containing evaluation under 'evaluations'.
        "evaluations": (evaluation,),
    },)}
    # Set candidate to a dictionary containing target_candidate_path_id, target_candidate_manoeuvre,
    # relative_approach,...
    candidate = {
        "target_candidate_path_id": "B_PATH_STRAIGHT",
        "target_candidate_manoeuvre": "STRAIGHT", "relative_approach": "RIGHT",
        # Store a tuple containing the text 'DE-STVO-8-1' under 'applicable_rule_ids'.
        "applicable_rule_ids": ("DE-STVO-8-1",),
        # Store a tuple containing the text '§ 8' under 'source_sections'.
        # Store status under 'regulatory_status'.
        "source_sections": ("§ 8",), "regulatory_status": status,
    }
    # Set regulatory to a dictionary containing ego_id, timestamp, regulatory_profile, assessments.
    regulatory = {"ego_id": "A", "timestamp": timestamp,
                  "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
                  # Store a tuple containing a dictionary containing ego_id, target_id, timestamp,
                  # regulatory_profile, regulatory_status,... under 'assessments'.
                  "assessments": ({
                      # Store the text 'A' under 'ego_id'.
                      # Store the text 'B' under 'target_id'.
                      # Store timestamp under 'timestamp'.
                      "ego_id": "A", "target_id": "B", "timestamp": timestamp,
                      "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
                      # Store status under 'regulatory_status'.
                      "regulatory_status": status,
                      # Store a tuple containing the text 'DE-STVO-8-1' under 'applicable_rule_ids'.
                      "applicable_rule_ids": ("DE-STVO-8-1",),
                      # Store a tuple containing the text '§ 8' under 'source_sections'.
                      "source_sections": ("§ 8",),
                      # Store a tuple containing candidate under 'candidate_assessments'.
                      "candidate_assessments": (candidate,),
                  },)}
    # Return the result of FakeLDM(conflict, temporal, regulatory) to the caller.
    return FakeLDM(conflict, temporal, regulatory)


# Check one precedence edge has documented direction and no cycle using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_one_precedence_edge_has_documented_direction_and_no_cycle():
    # Set result to the result of RegulatoryPrecedenceGraphBuilder().build(the result of local_fixture()).
    result = RegulatoryPrecedenceGraphBuilder().build(local_fixture())
    # Set edge to result['precedence_edges'] at 0.
    edge = result["precedence_edges"][0]
    # Require a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id' equals a tuple
    # containing the text 'A', the text 'B'; otherwise raise AssertionError.
    assert (edge["yielding_vehicle_id"], edge["priority_vehicle_id"]) == ("A", "B")
    # Require result at 'cycle_detected' is the same object as False; otherwise raise AssertionError.
    assert result["cycle_detected"] is False
    # Require edge at 'target_candidate_path_ids' equals a tuple containing the text 'B_PATH_STRAIGHT'; otherwise
    # raise AssertionError.
    assert edge["target_candidate_path_ids"] == ("B_PATH_STRAIGHT",)
    # Require edge['physical_reachability_evidence'] at 'evaluations'; otherwise raise AssertionError.
    assert edge["physical_reachability_evidence"]["evaluations"]


# Check acyclic chain and disconnected groups have deterministic orders using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_acyclic_chain_and_disconnected_groups_have_deterministic_orders():
    # Set builder to the result of RegulatoryPrecedenceGraphBuilder().
    builder = RegulatoryPrecedenceGraphBuilder()
    # Set chain to the result of builder.analyse(a tuple containing the text 'A', the text 'B', the text 'C', a
    # tuple containing the result of...).
    chain = builder.analyse(("A", "B", "C"), (raw_edge("A", "B"), raw_edge("B", "C")))
    # Require chain at 'cycle_detected' is the same object as False; otherwise raise AssertionError.
    assert chain["cycle_detected"] is False
    # Require chain at 'yield_precedence_graph_topological_order' equals a tuple containing the text 'A', the text
    # 'B', the text 'C'; otherwise raise AssertionError.
    assert chain["yield_precedence_graph_topological_order"] == ("A", "B", "C")
    # Require chain at 'regulatory_service_order' equals a tuple containing the text 'C', the text 'B', the text
    # 'A'; otherwise raise AssertionError.
    assert chain["regulatory_service_order"] == ("C", "B", "A")
    # Set disconnected to the result of builder.analyse(a tuple containing the text 'A', the text 'B', the text
    # 'C', the text 'D', a tuple containing...).
    disconnected = builder.analyse(
        # Supply a tuple containing the result of raw_edge(the text 'A', the text 'B'), the result of raw_edge(the
        # text 'C', the text 'D') to builder.analyse.
        ("A", "B", "C", "D"), (raw_edge("A", "B"), raw_edge("C", "D"))
    )
    # Set order to disconnected at 'yield_precedence_graph_topological_order'.
    order = disconnected["yield_precedence_graph_topological_order"]
    # Require the result of order.index(the text 'A') is less than the result of order.index(the text 'B') and the
    # result of order.index(the text 'C') is less than the result of order.index(the text 'D'); otherwise raise
    # AssertionError.
    assert order.index("A") < order.index("B") and order.index("C") < order.index("D")


# Check two node and four node cycles use standard sccs using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_node_and_four_node_cycles_use_standard_sccs():
    # Set builder to the result of RegulatoryPrecedenceGraphBuilder().
    builder = RegulatoryPrecedenceGraphBuilder()
    # Set two to the result of builder.analyse(a tuple containing the text 'A', the text 'B', a tuple containing
    # the result of raw_edge(the...).
    two = builder.analyse(("A", "B"), (raw_edge("A", "B"), raw_edge("B", "A")))
    # Require two at 'cycle_detected' is the same object as True; otherwise raise AssertionError.
    assert two["cycle_detected"] is True
    # Require two at 'strongly_connected_components' equals a tuple containing a tuple containing the text 'A',
    # the text 'B'; otherwise raise AssertionError.
    assert two["strongly_connected_components"] == (("A", "B"),)
    # Set four_edges to a tuple built from a lazy sequence of the result of raw_edge(a, b) for (a, b) in a tuple
    # containing a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple
    # containing...
    four_edges = tuple(raw_edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")
    ))
    # Set four to the result of builder.analyse(a tuple containing the text 'A', the text 'B', the text 'C', the
    # text 'D', four_edges).
    four = builder.analyse(("A", "B", "C", "D"), four_edges)
    # Require four at 'cycle_members' equals a tuple containing the text 'A', the text 'B', the text 'C', the text
    # 'D'; otherwise raise AssertionError.
    assert four["cycle_members"] == ("A", "B", "C", "D")
    # Require four at 'regulatory_service_order' is the same object as None; otherwise raise AssertionError.
    assert four["regulatory_service_order"] is None
    # Set four['unresolved_relations'] to an empty tuple.
    four["unresolved_relations"] = ()
    # Require the result of NegotiationEnvironment.classify_status(four) is the same object as
    # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE; otherwise raise AssertionError.
    assert NegotiationEnvironment.classify_status(four) is (
        # Evaluate NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE as part of the enclosing expression.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE
    )


# Check no spatial edge means no active conflict even with extra track using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_no_spatial_edge_means_no_active_conflict_even_with_extra_track():
    # Set ldm to the result of local_fixture().
    ldm = local_fixture()
    # Set ldm.current_conflict_graph['edges'] to an empty tuple.
    ldm.current_conflict_graph["edges"] = ()
    # Set ldm.tracks['irrelevant'] to the result of track(the text 'irrelevant').
    ldm.tracks["irrelevant"] = track("irrelevant")
    # Set result to the result of NegotiationEnvironment().build_snapshot(ldm, 2.0).
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    # Require result at 'participant_ids' equals a tuple containing the text 'A'; otherwise raise AssertionError.
    assert result["participant_ids"] == ("A",)
    # Require result at 'negotiation_status' equals NegotiationStatus.NO_ACTIVE_CONFLICT.value; otherwise raise
    # AssertionError.
    assert result["negotiation_status"] == NegotiationStatus.NO_ACTIVE_CONFLICT.value


# Check unresolved manoeuvre is retained without guessed edge using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unresolved_manoeuvre_is_retained_without_guessed_edge():
    # Set result to the result of NegotiationEnvironment().build_snapshot(the result of local_fixture(the text
    # 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE'), 2.0).
    result = NegotiationEnvironment().build_snapshot(
        # Supply the result of local_fixture(the text 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE') to
        # NegotiationEnvironment().build_snapshot.
        local_fixture("UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"), 2.0
    )
    # Require result at 'precedence_edges' equals an empty tuple; otherwise raise AssertionError.
    assert result["precedence_edges"] == ()
    # Require result['unresolved_relations'][0] at 'regulatory_status' equals the text
    # 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE'; otherwise raise AssertionError.
    assert result["unresolved_relations"][0]["regulatory_status"] == "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"
    # Require result at 'negotiation_status' equals
    # NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value; otherwise raise AssertionError.
    assert result["negotiation_status"] == NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value


# Check route truth and prediction probability do not change structure using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_route_truth_and_prediction_probability_do_not_change_structure():
    # Set first to the result of local_fixture().
    first = local_fixture()
    # Set second to the result of deepcopy(first).
    second = deepcopy(first)
    # Update second.tracks['B'] with the supplied entries.
    second.tracks["B"].update({"route_id": "opposite", "route_index": -1,
                               "ground_truth_route_id": "opposite_truth"})
    # Set second.current_conflict_graph['edges'][0]['intention_weighted_conflict_probability'] to 0.01.
    second.current_conflict_graph["edges"][0]["intention_weighted_conflict_probability"] = 0.01
    # Set environment to the result of NegotiationEnvironment().
    environment = NegotiationEnvironment()
    # Set a to the result of environment.build_snapshot(first, 2.0).
    a = environment.build_snapshot(first, 2.0)
    # Set b to the result of environment.build_snapshot(second, 2.0).
    b = environment.build_snapshot(second, 2.0)
    # Require a at 'precedence_edges' equals b at 'precedence_edges'; otherwise raise AssertionError.
    assert a["precedence_edges"] == b["precedence_edges"]
    # Require a at 'participant_ids' equals b at 'participant_ids'; otherwise raise AssertionError.
    assert a["participant_ids"] == b["participant_ids"]


# Check stopped vehicle with unresolved nominal timing remains participant using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_stopped_vehicle_with_unresolved_nominal_timing_remains_participant():
    # Set temporal_record to a dictionary containing target_path_id, status, target_speed_mps,
    # target_earliest_reachable_entry_time_s,...
    temporal_record = {
        "target_path_id": "B_PATH_STRAIGHT", "status": "UNRESOLVED_SPEED",
        # Store 0.0 under 'target_speed_mps'.
        "target_speed_mps": 0.0,
        # Store 3.2 under 'target_earliest_reachable_entry_time_s'.
        "target_earliest_reachable_entry_time_s": 3.2,
        # Store True under 'target_can_stop_before_zone'.
        "target_can_stop_before_zone": True,
        "target_zone_occupancy_state": "BEFORE_ZONE",
        "reachability_interpretation": "UNCOMMITTED_CAN_STOP",
    }
    # Set ldm to the result of local_fixture().
    ldm = local_fixture(temporal_record=temporal_record)
    # Set ldm.tracks['B']['speed'] to 0.0.
    ldm.tracks["B"]["speed"] = 0.0
    # Set result to the result of NegotiationEnvironment().build_snapshot(ldm, 2.0).
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    # Require the text 'B' belongs to result at 'participant_ids'; otherwise raise AssertionError.
    assert "B" in result["participant_ids"]
    # Set evidence to result['precedence_edges'][0] at 'physical_reachability_evidence'.
    evidence = result["precedence_edges"][0]["physical_reachability_evidence"]
    # Require evidence['evaluations'][0] at 'target_earliest_reachable_entry_time_s' equals 3.2; otherwise raise
    # AssertionError.
    assert evidence["evaluations"][0]["target_earliest_reachable_entry_time_s"] == 3.2


# Check source timestamp mismatch is explicit using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_source_timestamp_mismatch_is_explicit():
    # Set ldm to the result of local_fixture().
    ldm = local_fixture()
    # Set ldm.current_temporal_assessment['timestamp'] to 3.0.
    ldm.current_temporal_assessment["timestamp"] = 3.0
    # Set result to the result of NegotiationEnvironment().build_snapshot(ldm, 2.0).
    result = NegotiationEnvironment().build_snapshot(ldm, 2.0)
    # Require result at 'source_snapshot_consistent' is the same object as False; otherwise raise AssertionError.
    assert result["source_snapshot_consistent"] is False
    # Require result at 'negotiation_status' equals NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value; otherwise
    # raise AssertionError.
    assert result["negotiation_status"] == NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value


# Check snapshot has no control or reward side effect interface using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def test_snapshot_has_no_control_or_reward_side_effect_interface(monkeypatch):
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
    # Set result to the result of NegotiationEnvironment().build_snapshot(the result of local_fixture(), 2.0).
    result = NegotiationEnvironment().build_snapshot(local_fixture(), 2.0)
    # Require calls equals an empty list; otherwise raise AssertionError.
    assert calls == []
    # Require result at 'control_actions_issued' equals 0; otherwise raise AssertionError.
    assert result["control_actions_issued"] == 0
    # Require result at 'available_action_schema' equals a tuple containing the text 'KEEP_CLAIM', the text
    # 'RELINQUISH_CLAIM'; otherwise raise AssertionError.
    assert result["available_action_schema"] == ("KEEP_CLAIM", "RELINQUISH_CLAIM")
    # Require the text 'reward' does not belong to result; otherwise raise AssertionError.
    assert "reward" not in result
    # Require result['graph_observation']['metadata'] at 'tensor_encoding_status' equals the text
    # 'NOT_IMPLEMENTED'; otherwise raise AssertionError.
    assert result["graph_observation"]["metadata"]["tensor_encoding_status"] == "NOT_IMPLEMENTED"
