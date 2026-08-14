"""Fully autonomous SUMO simulation with ONNX shadow prediction."""

from itertools import cycle
from collections import deque

import traci

from config import (
    AV_TYPE_ID,
    CONTROL_UPDATE_INTERVAL_SECONDS,
    CONFLICT_DEBUG_OUTPUT,
    DASHBOARD_API_URL,
    DASHBOARD_ENABLED,
    DASHBOARD_TIMEOUT_SECONDS,
    DASHBOARD_UPDATE_INTERVAL_SECONDS,
    EPISODE_DURATION_SECONDS,
    EPISODE_STEPS,
    INITIAL_VEHICLE_COUNT,
    MAX_APPROACH_SPEED,
    OUTPUT_DIR,
    ROUTE_IDS,
    SAFE_SUMO_SPEED_MODE,
    SENSOR_CONFIGURATION_SUMMARY,
    SHADOW_MODE,
    SPAWN_BATCH_SIZE,
    SPAWN_INTERVAL_SECONDS,
    USE_SUMO_GUI,
    VALIDATION_SCENARIO_ENABLED,
    VALIDATION_SPAWN_SCHEDULE,
)
from conflict_entry_monitor import conflict_entry_monitor
from conflict import (
    ConflictGraphManager, ConflictZoneManager, MapPathManager,
    ConflictZoneOccupancyAssessor,
    write_conflict_catalogues,
)
from environment import SUMOEnv
from evaluation import evaluator
from negotiation import NegotiationManager
from negotiation_learning import (
    GraphTensorEncoder, NegotiationEnvironment, V2VPrecedenceClaimBus,
)
from observation import observation_manager
from predictor import IntentionPredictor
from risk_assessment import risk_assessor
from traffic_rules import TrafficRuleEngine, validate_network_odd
from config import SUMO_NETWORK_FILE

try:
    import requests
except ImportError:
    requests = None


def add_autonomous_vehicle(vehicle_id, route_id):
    traci.vehicle.add(
        vehID=vehicle_id,
        routeID=route_id,
        typeID=AV_TYPE_ID,
        departSpeed="max",
        departLane="free",
        departPos="base",
    )
    # 31 keeps SUMO's normal safe-speed, acceleration, deceleration and
    # approach right-of-way checks active.
    traci.vehicle.setSpeedMode(
        vehicle_id,
        SAFE_SUMO_SPEED_MODE,
    )
    observation_manager.get_or_create_ldm(vehicle_id)


def apply_action(vehicle_id, state, action):
    current_speed = float(state.get("vel", 0.0))

    if action == "ASSERT":
        target_speed = min(
            MAX_APPROACH_SPEED,
            current_speed + 1.0,
        )
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    elif action == "YIELD":
        target_speed = max(0.0, current_speed - 1.0)
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    else:
        # A negative target releases explicit TraCI speed control and lets
        # SUMO's car-following and junction safety logic choose the speed.
        traci.vehicle.setSpeed(vehicle_id, -1.0)


def build_dashboard_payload(
    current_time,
    observations,
    current_actions,
):
    vehicles = {}
    prediction_data = {}

    for vehicle_id, state in observations.items():
        x_position, y_position = state.get(
            "pos",
            (0.0, 0.0),
        )
        vehicles[vehicle_id] = {
            "id": vehicle_id,
            "position": {
                "x": float(x_position),
                "y": float(y_position),
            },
            "speed": float(state.get("vel", 0.0)),
            "heading_degrees": float(
                state.get("angle_degrees", 0.0)
            ),
            "lane": state.get("lane_id", ""),
            "road": state.get("road_id", ""),
            "is_av": vehicle_id.startswith("AV_"),
        }

        ldm = observation_manager.get_ldm(vehicle_id)
        if ldm is not None:
            prediction_data[vehicle_id] = (
                ldm.prediction_snapshot()
            )

    return {
        "time_seconds": float(current_time),
        "vehicles": vehicles,
        "negotiation_actions": dict(current_actions),
        "evaluation_metrics": {
            "Safety_Score": evaluator.safety_score,
            "Deadlock_Rate": evaluator.deadlock_rate,
            "Throughput": evaluator.throughput,
            "Avg_AV_Speed": evaluator.avg_av_speed,
            "Total_Collisions": evaluator.total_collisions,
            "Successful_Crossings": (
                evaluator.successful_crossings
            ),
            "Avg_Travel_Time": evaluator.avg_travel_time,
        },
        "risk_data": {
            vehicle_id: risk_assessor.get_risk_data(vehicle_id)
            for vehicle_id in observations
        },
        "intention_predictions": prediction_data,
        "local_conflict_graphs": {
            vehicle_id: observation_manager.get_ldm(
                vehicle_id
            ).get_current_conflict_graph()
            for vehicle_id in observations
            if observation_manager.get_ldm(vehicle_id) is not None
            and observation_manager.get_ldm(
                vehicle_id
            ).get_current_conflict_graph() is not None
        },
        "temporal_conflict_assessments": {
            vehicle_id: observation_manager.get_ldm(
                vehicle_id
            ).get_current_temporal_assessment()
            for vehicle_id in observations
            if observation_manager.get_ldm(vehicle_id) is not None
            and observation_manager.get_ldm(
                vehicle_id
            ).get_current_temporal_assessment() is not None
        },
        "traffic_rule_assessments": {
            vehicle_id: observation_manager.get_ldm(
                vehicle_id
            ).get_current_regulatory_assessment()
            for vehicle_id in observations
            if observation_manager.get_ldm(vehicle_id) is not None
            and observation_manager.get_ldm(
                vehicle_id
            ).get_current_regulatory_assessment() is not None
        },
        "negotiation_problem_snapshots": {
            vehicle_id: observation_manager.get_ldm(
                vehicle_id
            ).get_current_negotiation_problem()
            for vehicle_id in observations
            if observation_manager.get_ldm(vehicle_id) is not None
            and observation_manager.get_ldm(
                vehicle_id
            ).get_current_negotiation_problem() is not None
        },
        "gnn_input_encoding_diagnostics": {
            vehicle_id: observation_manager.get_ldm(
                vehicle_id
            ).get_current_encoded_graph_observation().dashboard_summary()
            for vehicle_id in observations
            if observation_manager.get_ldm(vehicle_id) is not None
            and observation_manager.get_ldm(
                vehicle_id
            ).get_current_encoded_graph_observation() is not None
        },
        "prediction_mode": "SHADOW" if SHADOW_MODE else "ACTIVE",
    }


def send_to_dashboard(payload):
    if not DASHBOARD_ENABLED or requests is None:
        return
    try:
        requests.post(
            DASHBOARD_API_URL,
            json=payload,
            timeout=DASHBOARD_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        # Dashboard availability must never stop the simulation.
        return


def print_prediction_events(events):
    """Print each finalized ego-target event exactly once."""
    for update in events:
        primary = update.get("primary")
        secondary = update.get("secondary")
        primary_text = (
            f"{primary['label']} {primary['confidence']:.3f}"
            if primary is not None
            else update["primary_stage_status"]
        )
        secondary_text = (
            f"{secondary['label']} {secondary['confidence']:.3f}"
            if secondary is not None
            else update["secondary_stage_status"]
        )
        print(
            f"t={update['finalization_time']:7.2f} | "
            f"event={update['event_id']} | "
            f"ego={update['ego_id']} | "
            f"target={update['target_id']} | "
            f"primary={primary_text} | "
            f"secondary={secondary_text} | "
            f"fused={update['fused_label']} | "
            f"status={update['status']}"
        )


def main():
    print("Sensor configuration:")
    for name, value in SENSOR_CONFIGURATION_SUMMARY.items():
        print(f"  {name}: {value}")
    if not SHADOW_MODE:
        raise RuntimeError(
            "This checkpoint is intentionally shadow-only. "
            "Set SHADOW_MODE=True until conflict and safety modules exist."
        )

    predictor = IntentionPredictor()
    map_path_manager = MapPathManager()
    conflict_zone_manager = ConflictZoneManager(map_path_manager)
    conflict_graph_manager = ConflictGraphManager(
        map_path_manager, conflict_zone_manager
    )
    occupancy_assessor = ConflictZoneOccupancyAssessor(
        map_path_manager, conflict_zone_manager
    )
    traffic_rule_engine = TrafficRuleEngine(map_path_manager)
    negotiation_environment = NegotiationEnvironment()
    v2v_claim_bus = V2VPrecedenceClaimBus()
    graph_tensor_encoder = GraphTensorEncoder()
    network_odd = validate_network_odd(SUMO_NETWORK_FILE)
    if not network_odd["passed"]:
        raise RuntimeError(
            "Compiled SUMO network is incompatible with the regulatory ODD: "
            + ", ".join(network_odd["errors"])
        )
    write_conflict_catalogues(
        map_path_manager, conflict_zone_manager, OUTPUT_DIR
    )
    if CONFLICT_DEBUG_OUTPUT:
        print("Conflict map loaded:")
        print(f"  movement paths: {len(map_path_manager.paths)}")
        print(
            "  crossing/merging conflict relationships: "
            f"{len(conflict_zone_manager.zone_geometries)}"
        )
        print(f"  conflict zones: {len(conflict_zone_manager.zone_geometries)}")
    negotiation_manager = NegotiationManager()
    route_cycle = cycle(ROUTE_IDS)
    validation_schedule = deque(VALIDATION_SPAWN_SCHEDULE)

    evaluator.reset()
    observation_manager.reset()
    conflict_entry_monitor.reset()
    risk_assessor.reset()

    environment = SUMOEnv(use_gui=USE_SUMO_GUI)
    current_actions = {}
    vehicle_counter = 0
    next_spawn_time = SPAWN_INTERVAL_SECONDS
    next_control_time = 0.0
    next_dashboard_time = 0.0

    try:
        environment.start()

        if VALIDATION_SCENARIO_ENABLED:
            while validation_schedule and validation_schedule[0][0] <= 0.0:
                _, route_id = validation_schedule.popleft()
                add_autonomous_vehicle(f"AV_{vehicle_counter}", route_id)
                vehicle_counter += 1
        else:
            for _ in range(INITIAL_VEHICLE_COUNT):
                add_autonomous_vehicle(f"AV_{vehicle_counter}", next(route_cycle))
                vehicle_counter += 1

        for _ in range(EPISODE_STEPS):
            observations = environment.step()
            current_time = environment.current_time
            evaluation_route_truth = {
                vehicle_id: state.get("route_id", "")
                for vehicle_id, state in observations.items()
            }

            observation_manager.update(
                observations,
                current_time,
            )

            prediction_events = []
            for ego_id in observations:
                ldm = observation_manager.get_ldm(ego_id)
                if ldm is not None:
                    prediction_events.extend(
                        conflict_entry_monitor.update_ldm(
                            ldm,
                            current_time,
                            predictor,
                            evaluation_route_truth,
                        )
                    )
            evaluator.record_prediction_events(
                prediction_events
            )
            print_prediction_events(prediction_events)

            # Phase 1: every AV completes sender-local reasoning and publishes
            # only claims derived from its own LDM. No joint graph exists yet.
            v2v_claim_bus.begin_step(current_time)
            local_precedence_graphs = {}
            for ego_id in observations:
                ldm = observation_manager.get_ldm(ego_id)
                if ldm is not None and ldm.in_approach_zone:
                    ldm.current_conflict_graph = (
                        conflict_graph_manager.build_local_graph(
                            ldm, current_time
                        )
                    )
                    ldm.current_temporal_assessment = (
                        occupancy_assessor.assess_ldm(ldm, current_time)
                    )
                    # German-StVO reasoning is deliberately shadow-only. Its
                    # output is not passed to risk, negotiation, or control.
                    ldm.current_regulatory_assessment = (
                        traffic_rule_engine.assess_ldm(ldm, current_time)
                    )
                    local_graph, claim_messages = (
                        negotiation_environment.build_local_claims(
                            ldm, current_time
                        )
                    )
                    local_precedence_graphs[ego_id] = local_graph
                    for claim_message in claim_messages:
                        v2v_claim_bus.publish(claim_message)
                elif ldm is not None:
                    ldm.current_conflict_graph = None
                    ldm.current_temporal_assessment = None
                    ldm.current_regulatory_assessment = None
                    ldm.current_negotiation_problem = None
                    ldm.current_encoded_graph_observation = None
                    ldm.current_negotiation_protocol_state = None
                    ldm.current_negotiated_precedence_overlay = None
                    conflict_graph_manager.reset(ego_id)
                    occupancy_assessor.reset(ego_id)

            # Phase 2 starts only after every sender has published. Each AV
            # independently expands its own connected component from the same
            # immutable current-step message set, so iteration order is inert.
            v2v_claim_bus.freeze_step(current_time)
            for ego_id in observations:
                ldm = observation_manager.get_ldm(ego_id)
                if ldm is not None and ego_id in local_precedence_graphs:
                    ldm.current_negotiation_problem = (
                        negotiation_environment.build_snapshot(
                            ldm, current_time,
                            v2v_claim_bus.current_messages(
                                current_time, receiver_id=ego_id
                            ),
                            local_precedence_graphs[ego_id],
                        )
                    )
                    ldm.current_encoded_graph_observation = (
                        graph_tensor_encoder.encode(
                            ldm.current_negotiation_problem["graph_observation"]
                        )
                    )
                    # Step 5F shadow readiness only. Untrained role-aware policy
                    # interfaces do not fabricate protocol messages or act.
                    ldm.current_negotiation_protocol_state = {
                        "communication_model": "IDEAL_SAME_STEP_V2V",
                        "state": "NO_PROPOSAL",
                        "protocol_status":
                            "MULTI_PROPOSAL_PER_CLAIM_PROTOCOL_AVAILABLE_STEP_5E_2",
                        "response_policy_interface":
                            "RESPONSE_POLICY_INTERFACE_IMPLEMENTED_UNTRAINED",
                        "response_policy_learning": "PENDING_MAPPO_INTEGRATION",
                        "role_aware_policy_interface": "IMPLEMENTED_UNTRAINED_STEP_5F",
                        "control_actions_issued": 0,
                    }
                    ldm.current_negotiated_precedence_overlay = None

            if current_time + 1e-9 >= next_control_time:
                for ego_id in observations:
                    ldm = observation_manager.get_ldm(ego_id)
                    if ldm is not None and ldm.in_approach_zone:
                        risk_assessor.assess_risk(
                            ego_id,
                            ldm,
                            current_time,
                        )

                new_actions = {}
                for vehicle_id, state in observations.items():
                    ldm = observation_manager.get_ldm(vehicle_id)
                    if ldm is not None and ldm.in_approach_zone:
                        nearby_states = []
                        risk_metrics = (
                            risk_assessor.get_risk_data(vehicle_id)
                        )
                        for other_id, track in (
                            ldm.get_conflict_relevant_vehicles().items()
                        ):
                            enhanced = dict(track)
                            enhanced.update(
                                risk_metrics.get(other_id, {})
                            )
                            nearby_states.append(enhanced)

                        action = negotiation_manager.negotiate(
                            {
                                key: value for key, value in state.items()
                                if key not in {
                                    "route_id", "ground_truth_route_id",
                                    "route_index",
                                }
                            },
                            nearby_states,
                            ldm,
                        )
                    else:
                        action = "MAINTAIN"

                    new_actions[vehicle_id] = action
                    apply_action(vehicle_id, state, action)

                current_actions = new_actions
                while (
                    next_control_time
                    <= current_time + 1e-9
                ):
                    next_control_time += (
                        CONTROL_UPDATE_INTERVAL_SECONDS
                    )

            if VALIDATION_SCENARIO_ENABLED:
                while validation_schedule and validation_schedule[0][0] <= current_time + 1e-9:
                    _, route_id = validation_schedule.popleft()
                    add_autonomous_vehicle(f"AV_{vehicle_counter}", route_id)
                    vehicle_counter += 1
            elif (
                current_time + 1e-9 >= next_spawn_time
                and current_time
                < EPISODE_DURATION_SECONDS - 5.0
            ):
                for _ in range(SPAWN_BATCH_SIZE):
                    vehicle_id = f"AV_{vehicle_counter}"
                    add_autonomous_vehicle(
                        vehicle_id,
                        next(route_cycle),
                    )
                    vehicle_counter += 1
                next_spawn_time += SPAWN_INTERVAL_SECONDS

            evaluator.update(current_time, observations)

            if current_time + 1e-9 >= next_dashboard_time:
                send_to_dashboard(
                    build_dashboard_payload(
                        current_time,
                        observations,
                        current_actions,
                    )
                )
                next_dashboard_time += (
                    DASHBOARD_UPDATE_INTERVAL_SECONDS
                )

        final_events = conflict_entry_monitor.finalize_all(
            environment.current_time,
            predictor,
        )
        evaluator.record_prediction_events(final_events)
        print_prediction_events(final_events)
        evaluator.compute_metrics(environment.current_time)
        evaluator.save_prediction_log()

    finally:
        conflict_summary = conflict_graph_manager.validation_summary()
        print("\nConflict Graph validation")
        print(f"  Discovered movement paths: {len(map_path_manager.paths)}")
        print(f"  Map conflict zones: {len(conflict_zone_manager.zone_geometries)}")
        print(f"  Graphs built: {conflict_summary['graphs_built']}")
        print(
            "  Spatial conflict edges observed: "
            f"{conflict_summary['spatial_conflict_edges_observed']}"
        )
        print(
            "  Unknown-intention conservative edges: "
            f"{conflict_summary['unknown_intention_conservative_edges']}"
        )
        print(
            "  Prediction-unavailable conservative edges: "
            f"{conflict_summary['prediction_unavailable_conservative_edges']}"
        )
        print(
            "  Non-conflicting targets filtered: "
            f"{conflict_summary['non_conflicting_targets_filtered']}"
        )
        temporal_summary = occupancy_assessor.validation_summary()
        print("\nTemporal Reachability validation")
        print(
            "  Spatial edges evaluated: "
            f"{temporal_summary['spatial_edges_evaluated']}"
        )
        print(
            "  Spatially-conflicting candidate path evaluations: "
            f"{temporal_summary['candidate_path_zone_evaluations']}"
        )
        print(
            "  Nominal constant-speed temporal conflicts: "
            f"{temporal_summary['temporal_conflicts_observed']}"
        )
        print(
            "  Nominal temporal separations: "
            f"{temporal_summary['spatial_only_temporal_separations']}"
        )
        print(
            "  Currently-occupied-zone evaluations: "
            f"{temporal_summary['currently_occupied_zone_evaluations']}"
        )
        print(
            "  Cleared-zone evaluations: "
            f"{temporal_summary['cleared_zone_evaluations']}"
        )
        print(
            "  Unresolved timing evaluations: "
            f"{temporal_summary['unresolved_timing_evaluations']}"
        )
        print(
            "    Path progress unresolved: "
            f"{temporal_summary['unresolved_path_progress']}"
        )
        print(
            "    Speed unresolved: "
            f"{temporal_summary['unresolved_speed']}"
        )
        print(
            "    Vehicle state unresolved: "
            f"{temporal_summary['unresolved_vehicle_state']}"
        )
        print(
            "    No applicable evaluation: "
            f"{temporal_summary['unresolved_no_applicable_evaluation']}"
        )
        print(
            "  Candidate paths rejected by observed lane: "
            f"{temporal_summary['candidate_paths_rejected_by_observed_lane']}"
        )
        print(
            "  Candidate paths without an applicable zone: "
            f"{temporal_summary['no_applicable_zone']}"
        )
        print(
            "  Nominal timing unavailable due to zero speed: "
            f"{temporal_summary['nominal_timing_unavailable_due_to_zero_speed']}"
        )
        print(
            "  Earliest-reachability calculations: "
            f"{temporal_summary['earliest_reachability_calculations']}"
        )
        print(
            "  Stopped vehicles with finite earliest arrival: "
            f"{temporal_summary['stopped_vehicles_with_finite_earliest_arrival']}"
        )
        print(
            "  Vehicles able to stop before zone: "
            f"{temporal_summary['vehicles_able_to_stop_before_zone']}"
        )
        print(
            "  Vehicles unable to stop before zone: "
            f"{temporal_summary['vehicles_unable_to_stop_before_zone']}"
        )
        print(
            "  Physical state/dynamics unresolved: "
            f"{temporal_summary['physical_state_or_dynamics_unresolved']}"
        )
        print(
            "  Non-conflicting candidate paths excluded: "
            f"{temporal_summary['non_conflicting_candidate_paths_excluded']}"
        )
        print(
            "  Unique ego-target pairs with temporal conflict: "
            f"{temporal_summary['unique_ego_target_pairs_with_temporal_conflict']}"
        )
        rule_summary = traffic_rule_engine.validation_summary()
        print("\nTraffic Rule validation")
        print(f"  Regulatory profile: {traffic_rule_engine.context.profile_id}")
        print(f"  ODD validation passed: {network_odd['passed']}")
        print(f"  Central SUMO junction type: {network_odd['junction_type']}")
        print(
            "  Right-hand network confirmed: "
            f"{network_odd['right_hand_network_confirmed']}"
        )
        labels = (
            ("Local regulatory assessments built", "local_regulatory_assessments_built"),
            ("Spatial conflict pairs assessed", "spatial_conflict_pairs_assessed"),
            ("StVO §8 right-before-left obligations", "stvo_8_right_before_left_obligations"),
            ("StVO §9 turning/oncoming obligations", "stvo_9_turning_oncoming_obligations"),
            ("StVO §9(4) left-vs-oncoming-right obligations", "stvo_9_4_left_oncoming_right_obligations"),
            ("Ego mandatory-yield assessments", "ego_mandatory_yield_assessments"),
            ("Ego precedence-under-rule assessments", "ego_precedence_under_rule_assessments"),
            ("Manoeuvre-dependent unresolved assessments", "manoeuvre_dependent_unresolved_assessments"),
            ("Regulatory input unresolved", "regulatory_input_unresolved"),
            ("Target route-truth fields consumed", "target_route_truth_fields_consumed"),
        )
        for label, key in labels:
            print(f"  {label}: {rule_summary[key]}")
        negotiation_summary = negotiation_environment.validation_summary()
        print("\nV2V Negotiation Graph validation")
        bus_summary = v2v_claim_bus.validation_summary()
        negotiation_labels = (
            ("Local precedence claims published", "local_precedence_claims_published"),
            ("Current-step V2V messages created", "current_step_v2v_messages_created"),
            ("Joint local negotiation snapshots built", "joint_local_negotiation_snapshots_built"),
            ("Snapshots with active conflict participants", "snapshots_with_active_conflict_participants"),
            ("Messages received by local agents", "messages_received_by_local_agents"),
            ("Messages adopted into connected components", "messages_adopted_into_connected_components"),
            ("Unconnected messages ignored", "unconnected_messages_ignored"),
            ("Duplicate claims merged", "duplicate_claims_merged"),
            ("Communicated precedence disagreements", "communicated_precedence_disagreements"),
            ("Joint precedence edges", "joint_precedence_edges"),
            ("Joint graphs with expanded participant sets", "joint_graphs_with_expanded_participant_sets"),
            ("Regulatory-order-resolved joint graphs", "regulatory_order_resolved_snapshots"),
            ("Regulatory-cycle joint graphs", "regulatory_cycle_snapshots"),
            ("Unresolved-precedence snapshots", "unresolved_precedence_snapshots"),
            ("No-active-conflict snapshots", "no_active_conflict_snapshots"),
            ("Strongly connected cyclic components observed", "strongly_connected_cyclic_components_observed"),
            ("Maximum local participants before V2V expansion", "maximum_local_participants_before_v2v_expansion"),
            ("Maximum joint participants after V2V expansion", "maximum_joint_participants_after_v2v_expansion"),
            ("Source snapshot mismatches", "source_snapshot_mismatches"),
            ("Regulatory-profile mismatches", "regulatory_profile_mismatches"),
            ("Target route-truth fields consumed", "target_route_truth_fields_consumed"),
            ("Control actions issued by negotiation environment", "control_actions_issued_by_negotiation_environment"),
        )
        for label, key in negotiation_labels:
            source = bus_summary if key in bus_summary else negotiation_summary
            print(f"  {label}: {source[key]}")
        encoding_summary = graph_tensor_encoder.validation_summary()
        print("\nGNN Input Encoding validation")
        encoding_labels = (
            ("Encoded graph observations built", "encoded_graph_observations_built"),
            ("NumPy tensor backend confirmed", "numpy_tensor_backend_confirmed"),
            ("Maximum encoded nodes", "maximum_encoded_nodes"),
            ("Maximum encoded directed edges", "maximum_encoded_directed_edges"),
            ("Node feature dimension", "node_feature_dimension"),
            ("Edge feature dimension", "edge_feature_dimension"),
            ("Encoded graphs with zero edges", "encoded_graphs_with_zero_edges"),
            ("Encoded graphs with communicated-only participants", "encoded_graphs_with_communicated_only_participants"),
            ("Missing node scalar values masked", "missing_node_scalar_values_masked"),
            ("Missing edge scalar values masked", "missing_edge_scalar_values_masked"),
            ("Non-finite available feature errors", "nonfinite_available_feature_errors"),
            ("Route-truth fields consumed", "route_truth_fields_consumed"),
            ("Arbitrary ordinal categorical encodings", "arbitrary_ordinal_categorical_encodings"),
            ("TensorFlow dependencies introduced", "tensorflow_dependencies_introduced"),
            ("PyTorch dependencies introduced", "pytorch_dependencies_introduced"),
            ("Control actions issued by tensor encoder", "control_actions_issued_by_tensor_encoder"),
        )
        for label, key in encoding_labels:
            print(f"  {label}: {encoding_summary[key]}")
        environment.close()
        observation_manager.reset()
        conflict_entry_monitor.reset()
        risk_assessor.reset()
        conflict_graph_manager.reset()
        occupancy_assessor.reset()
        traffic_rule_engine.reset()
        negotiation_environment.reset()
        v2v_claim_bus.reset()
        graph_tensor_encoder.reset()


if __name__ == "__main__":
    main()
