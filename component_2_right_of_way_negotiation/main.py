"""Fully autonomous SUMO simulation with ONNX shadow prediction."""

# Import cycle from itertools for the operations below.
from itertools import cycle
# Import deque from collections for the operations below.
from collections import deque

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, CONTROL_UPDATE_INTERVAL_SECONDS, CONFLICT_DEBUG_OUTPUT, DASHBOARD_API_URL, DASHBOARD_ENABLED,
# DASHBOARD_TIMEOUT_SECONDS,... from config for the operations below.
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
    VISUALIZATION_DEMO_EGO_ID,
    VISUALIZATION_ENABLED,
    VISUALIZATION_REFRESH_INTERVAL_SECONDS,
    VISUALIZATION_SENSOR_CIRCLE_POINTS,
    VISUALIZATION_SENSOR_OVERLAY_ENABLED,
    PERCEPTION_EVIDENCE_JSONL,
    SENSOR_RANGE,
    DEFAULT_PERCEPTION_PROFILE,
)
# Import conflict_entry_monitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import conflict_entry_monitor
# Import ConflictGraphManager, ConflictZoneManager, MapPathManager, ConflictZoneOccupancyAssessor,
# write_conflict_catalogues from conflict for the operations below.
from conflict import (
    ConflictGraphManager, ConflictZoneManager, MapPathManager,
    ConflictZoneOccupancyAssessor,
    write_conflict_catalogues,
)
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import evaluator from evaluation for the operations below.
from evaluation import evaluator
# Import NegotiationManager from negotiation for the operations below.
from negotiation import NegotiationManager
# Import GraphTensorEncoder, NegotiationEnvironment, V2VPrecedenceClaimBus from negotiation_learning for the
# operations below.
from negotiation_learning import (
    GraphTensorEncoder, NegotiationEnvironment, V2VPrecedenceClaimBus,
)
# Import observation_manager from observation for the operations below.
from observation import observation_manager
# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor
# Import risk_assessor from risk_assessment for the operations below.
from risk_assessment import risk_assessor
# Import TrafficRuleEngine, validate_network_odd from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine, validate_network_odd
# Import DemandScheduleSource, demand_ledger from traffic_accounting for the operations below.
from traffic_accounting import DemandScheduleSource, demand_ledger
# Import compute_objective_diagnostics, measure_vehicle_travel_times, raw_team_reward,
# total_team_travel_time_seconds from negotiation_objective for the operations below.
from negotiation_objective import (
    compute_objective_diagnostics, measure_vehicle_travel_times,
    raw_team_reward, total_team_travel_time_seconds,
)
# Import SUMO_NETWORK_FILE from config for the operations below.
from config import SUMO_NETWORK_FILE
# Import EvidenceJsonlWriter, build_evidence_snapshot, prediction_record_snapshot from debug_evidence for the
# operations below.
from debug_evidence import (
    EvidenceJsonlWriter, build_evidence_snapshot, prediction_record_snapshot,
)
# Import SumoDebugOverlay from sumo_debug_overlay for the operations below.
from sumo_debug_overlay import SumoDebugOverlay

# Attempt the enclosed operations and route matching exceptions to the handlers below.
try:
    # Import requests for use in this module.
    import requests
# Handle ImportError using the recovery steps below.
except ImportError:
    # Set requests to None.
    requests = None


# Add autonomous vehicle using the inputs and processing steps below.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input route_id: the supplied route id.
# Input scheduled_spawn_time: the supplied scheduled spawn time.
# Input schedule_source: the supplied schedule source.
# Output: no explicit value; normal completion returns None.
def add_autonomous_vehicle(vehicle_id, route_id, scheduled_spawn_time,
                           # Declare schedule_source as input parameter.
                           schedule_source):
    # Call demand_ledger.register_scheduled_vehicle with the supplied arguments.
    demand_ledger.register_scheduled_vehicle(
        # Supply scheduled_spawn_time to demand_ledger.register_scheduled_vehicle.
        vehicle_id, scheduled_spawn_time, schedule_source,
        # Store route_id under 'route_id'.
        route_metadata={"route_id": route_id},
        # Store the text 'BEFORE_TRACI_VEHICLE_ADD' under 'registration'.
        provenance={"registration": "BEFORE_TRACI_VEHICLE_ADD"},
    )
    # Add the supplied values to traci.vehicle.
    traci.vehicle.add(
        # Supply vehID as vehicle_id.
        vehID=vehicle_id,
        # Supply routeID as route_id.
        routeID=route_id,
        # Supply typeID as AV_TYPE_ID.
        typeID=AV_TYPE_ID,
        # Supply departSpeed as the text 'max'.
        departSpeed="max",
        # Supply departLane as the text 'free'.
        departLane="free",
        # Supply departPos as the text 'base'.
        departPos="base",
    )
    # 31 keeps SUMO's normal safe-speed, acceleration, deceleration and
    # approach right-of-way checks active.
    # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
    traci.vehicle.setSpeedMode(
        # Supply vehicle_id to traci.vehicle.setSpeedMode.
        vehicle_id,
        # Supply SAFE_SUMO_SPEED_MODE to traci.vehicle.setSpeedMode.
        SAFE_SUMO_SPEED_MODE,
    )
    # Call observation_manager.get_or_create_ldm with the supplied arguments.
    observation_manager.get_or_create_ldm(vehicle_id)


# Apply action using the inputs and processing steps below.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input state: the state read or updated by this operation.
# Input action: the supplied action.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def apply_action(vehicle_id, state, action):
    # Set current_speed to a floating-point number built from 'vel' from state; use 0.0 if absent.
    current_speed = float(state.get("vel", 0.0))

    # Run this branch when action equals the text 'ASSERT'.
    if action == "ASSERT":
        # Set target_speed to the minimum of MAX_APPROACH_SPEED, current_speed plus 1.0.
        target_speed = min(
            # Supply MAX_APPROACH_SPEED to min.
            MAX_APPROACH_SPEED,
            # Supply current_speed plus 1.0 to min.
            current_speed + 1.0,
        )
        # Request the specified SUMO speed using traci.vehicle.setSpeed.
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    # Run this branch when action equals the text 'YIELD'.
    elif action == "YIELD":
        # Set target_speed to the maximum of 0.0, current_speed minus 1.0.
        target_speed = max(0.0, current_speed - 1.0)
        # Request the specified SUMO speed using traci.vehicle.setSpeed.
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # A negative target releases explicit TraCI speed control and lets
        # SUMO's car-following and junction safety logic choose the speed.
        # Request the specified SUMO speed using traci.vehicle.setSpeed.
        traci.vehicle.setSpeed(vehicle_id, -1.0)


# Build dashboard payload using the inputs and processing steps below.
# Input current_time: the supplied current time.
# Input observations: the supplied observations.
# Input current_actions: the supplied current actions.
# Input intention_predictor: the supplied intention predictor.
# Input map_path_manager: the supplied map path manager.
# Input conflict_zone_manager: the supplied conflict zone manager.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def build_dashboard_payload(
    # Declare current_time as input parameter.
    current_time,
    # Declare observations as input parameter.
    observations,
    # Declare current_actions as input parameter.
    current_actions,
    # Declare intention_predictor as input parameter.
    intention_predictor=None,
    # Declare map_path_manager as input parameter.
    map_path_manager=None,
    # Declare conflict_zone_manager as input parameter.
    conflict_zone_manager=None,
):
    # Set vehicles to an empty dictionary.
    vehicles = {}
    # Set prediction_data to an empty dictionary.
    prediction_data = {}

    # Iterate over key/value pairs from observations, binding each item to (vehicle_id, state).
    for vehicle_id, state in observations.items():
        # Set (x_position, y_position) to 'pos' from state; use a tuple containing 0.0, 0.0 if absent.
        x_position, y_position = state.get(
            "pos",
            # Supply a tuple containing 0.0, 0.0 to state.get.
            (0.0, 0.0),
        )
        # Set vehicles[vehicle_id] to a dictionary containing id, position, speed, heading_degrees, lane, road,
        # is_av.
        vehicles[vehicle_id] = {
            # Store vehicle_id under 'id'.
            "id": vehicle_id,
            # Store a dictionary containing x, y under 'position'.
            "position": {
                # Store a floating-point number built from x_position under 'x'.
                "x": float(x_position),
                # Store a floating-point number built from y_position under 'y'.
                "y": float(y_position),
            },
            # Store a floating-point number built from 'vel' from state; use 0.0 if absent under 'speed'.
            "speed": float(state.get("vel", 0.0)),
            # Store a floating-point number built from 'angle_degrees' from state; use 0.0 if absent under
            # 'heading_degrees'.
            "heading_degrees": float(
                # Supply 'angle_degrees' from state; use 0.0 if absent to float.
                state.get("angle_degrees", 0.0)
            ),
            # Store 'lane_id' from state; use the text '' if absent under 'lane'.
            "lane": state.get("lane_id", ""),
            # Store 'road_id' from state; use the text '' if absent under 'road'.
            "road": state.get("road_id", ""),
            # Store the result of vehicle_id.startswith(the text 'AV_') under 'is_av'.
            "is_av": vehicle_id.startswith("AV_"),
        }

        # Set ldm to the result of observation_manager.get_ldm(vehicle_id).
        ldm = observation_manager.get_ldm(vehicle_id)
        # Run this branch when ldm is a different object from None.
        if ldm is not None:
            # Set prediction_data[vehicle_id] to a dictionary of target_id mapped to the result of
            # prediction_record_snapshot(record) for (target_id, record) in key/value pairs from
            # ldm.prediction_snapshot().
            prediction_data[vehicle_id] = {
                # Evaluate the result of prediction_record_snapshot(record) as part of the enclosing expression.
                target_id: prediction_record_snapshot(record)
                # Evaluate key/value pairs from ldm.prediction_snapshot() as part of the enclosing expression.
                for target_id, record in ldm.prediction_snapshot().items()
            }

    # Set payload to a dictionary containing time_seconds, vehicles, negotiation_actions, evaluation_metrics,
    # risk_data,...
    payload = {
        # Store a floating-point number built from current_time under 'time_seconds'.
        "time_seconds": float(current_time),
        # Store vehicles under 'vehicles'.
        "vehicles": vehicles,
        # Store a dictionary built from current_actions under 'negotiation_actions'.
        "negotiation_actions": dict(current_actions),
        # Store a dictionary containing Safety_Score, Deadlock_Rate, Throughput, Avg_AV_Speed,
        # Total_Collisions,... under 'evaluation_metrics'.
        "evaluation_metrics": {
            # Store evaluator.safety_score under 'Safety_Score'.
            "Safety_Score": evaluator.safety_score,
            # Store evaluator.deadlock_rate under 'Deadlock_Rate'.
            "Deadlock_Rate": evaluator.deadlock_rate,
            # Store evaluator.throughput under 'Throughput'.
            "Throughput": evaluator.throughput,
            # Store evaluator.avg_av_speed under 'Avg_AV_Speed'.
            "Avg_AV_Speed": evaluator.avg_av_speed,
            # Store evaluator.total_collisions under 'Total_Collisions'.
            "Total_Collisions": evaluator.total_collisions,
            # Store evaluator.successful_crossings under 'Successful_Crossings'.
            "Successful_Crossings": (
                # Evaluate evaluator.successful_crossings as part of the enclosing expression.
                evaluator.successful_crossings
            ),
            # Store evaluator.avg_travel_time under 'Avg_Travel_Time'.
            "Avg_Travel_Time": evaluator.avg_travel_time,
        },
        # Store a dictionary of vehicle_id mapped to the result of risk_assessor.get_risk_data(vehicle_id) for
        # vehicle_id in observations under 'risk_data'.
        "risk_data": {
            # Evaluate the result of risk_assessor.get_risk_data(vehicle_id) as part of the enclosing expression.
            vehicle_id: risk_assessor.get_risk_data(vehicle_id)
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
        },
        # Store prediction_data under 'intention_predictions'.
        "intention_predictions": prediction_data,
        # Store a dictionary of vehicle_id mapped to the result of
        # observation_manager.get_ldm(vehicle_id).get_current_conflict_graph() for vehicle_id in observations;
        # retain entries satisfying the result of observation_manager.get_ldm(vehicle_id) is a different object
        # from None... under 'local_conflict_graphs'.
        "local_conflict_graphs": {
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_conflict_graph() as part
            # of the enclosing expression.
            vehicle_id: observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            ).get_current_conflict_graph()
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
            # Evaluate the result of observation_manager.get_ldm(vehicle_id) is a different object from None and
            # the result of observation_manager.get_ldm(vehicle_id).get_current_conflict_graph() is a different
            # object from None as part of the enclosing expression.
            if observation_manager.get_ldm(vehicle_id) is not None
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_conflict_graph() is a
            # different object from None as part of the enclosing expression.
            and observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            # Supply None to the enclosing expression.
            ).get_current_conflict_graph() is not None
        },
        # Store a dictionary of vehicle_id mapped to the result of
        # observation_manager.get_ldm(vehicle_id).get_current_temporal_assessment() for vehicle_id in
        # observations; retain entries satisfying the result of observation_manager.get_ldm(vehicle_id) is a
        # different object from None... under 'temporal_conflict_assessments'.
        "temporal_conflict_assessments": {
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_temporal_assessment() as
            # part of the enclosing expression.
            vehicle_id: observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            ).get_current_temporal_assessment()
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
            # Evaluate the result of observation_manager.get_ldm(vehicle_id) is a different object from None and
            # the result of observation_manager.get_ldm(vehicle_id).get_current_temporal_assessment() is a
            # different object from None as part of the enclosing expression.
            if observation_manager.get_ldm(vehicle_id) is not None
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_temporal_assessment() is
            # a different object from None as part of the enclosing expression.
            and observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            # Supply None to the enclosing expression.
            ).get_current_temporal_assessment() is not None
        },
        # Store a dictionary of vehicle_id mapped to the result of
        # observation_manager.get_ldm(vehicle_id).get_current_regulatory_assessment() for vehicle_id in
        # observations; retain entries satisfying the result of observation_manager.get_ldm(vehicle_id) is a
        # different object from None... under 'traffic_rule_assessments'.
        "traffic_rule_assessments": {
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_regulatory_assessment()
            # as part of the enclosing expression.
            vehicle_id: observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            ).get_current_regulatory_assessment()
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
            # Evaluate the result of observation_manager.get_ldm(vehicle_id) is a different object from None and
            # the result of observation_manager.get_ldm(vehicle_id).get_current_regulatory_assessment() is a
            # different object from None as part of the enclosing expression.
            if observation_manager.get_ldm(vehicle_id) is not None
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_regulatory_assessment()
            # is a different object from None as part of the enclosing expression.
            and observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            # Supply None to the enclosing expression.
            ).get_current_regulatory_assessment() is not None
        },
        # Store a dictionary of vehicle_id mapped to the result of
        # observation_manager.get_ldm(vehicle_id).get_current_negotiation_problem() for vehicle_id in
        # observations; retain entries satisfying the result of observation_manager.get_ldm(vehicle_id) is a
        # different object from None... under 'negotiation_problem_snapshots'.
        "negotiation_problem_snapshots": {
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_negotiation_problem() as
            # part of the enclosing expression.
            vehicle_id: observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            ).get_current_negotiation_problem()
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
            # Evaluate the result of observation_manager.get_ldm(vehicle_id) is a different object from None and
            # the result of observation_manager.get_ldm(vehicle_id).get_current_negotiation_problem() is a
            # different object from None as part of the enclosing expression.
            if observation_manager.get_ldm(vehicle_id) is not None
            # Evaluate the result of observation_manager.get_ldm(vehicle_id).get_current_negotiation_problem() is
            # a different object from None as part of the enclosing expression.
            and observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            # Supply None to the enclosing expression.
            ).get_current_negotiation_problem() is not None
        },
        # Store a dictionary of vehicle_id mapped to the result of
        # observation_manager.get_ldm(vehicle_id).get_current_encoded_graph_observation().dashboard_summary() for
        # vehicle_id in observations; retain entries satisfying the result of
        # observation_manager.get_ldm(vehicle_id) is a different object from None... under
        # 'gnn_input_encoding_diagnostics'.
        "gnn_input_encoding_diagnostics": {
            # Evaluate the result of
            # observation_manager.get_ldm(vehicle_id).get_current_encoded_graph_observation().dashboard_summary()
            # as part of the enclosing expression.
            vehicle_id: observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            ).get_current_encoded_graph_observation().dashboard_summary()
            # Evaluate observations as part of the enclosing expression.
            for vehicle_id in observations
            # Evaluate the result of observation_manager.get_ldm(vehicle_id) is a different object from None and
            # the result of observation_manager.get_ldm(vehicle_id).get_current_encoded_graph_observation() is a
            # different object from None as part of the enclosing expression.
            if observation_manager.get_ldm(vehicle_id) is not None
            # Evaluate the result of
            # observation_manager.get_ldm(vehicle_id).get_current_encoded_graph_observation() is a different
            # object from None as part of the enclosing expression.
            and observation_manager.get_ldm(
                # Supply vehicle_id to observation_manager.get_ldm.
                vehicle_id
            # Supply None to the enclosing expression.
            ).get_current_encoded_graph_observation() is not None
        },
        # Store the text 'SHADOW' when SHADOW_MODE, otherwise the text 'ACTIVE' under 'prediction_mode'.
        "prediction_mode": "SHADOW" if SHADOW_MODE else "ACTIVE",
    }
    # Update payload with the supplied entries.
    payload.update(build_evidence_snapshot(
        # Supply current_time to build_evidence_snapshot.
        current_time,
        # Supply observations to build_evidence_snapshot.
        observations,
        # Supply observation_manager to build_evidence_snapshot.
        observation_manager,
        # Supply sensor_profile as DEFAULT_PERCEPTION_PROFILE.
        sensor_profile=DEFAULT_PERCEPTION_PROFILE,
        # Supply sensor_range as SENSOR_RANGE.
        sensor_range=SENSOR_RANGE,
        # Supply prediction_monitor as conflict_entry_monitor.
        prediction_monitor=conflict_entry_monitor,
        # Supply predictor as intention_predictor.
        predictor=intention_predictor,
        # Supply path_manager as map_path_manager.
        path_manager=map_path_manager,
        # Supply zone_manager as conflict_zone_manager.
        zone_manager=conflict_zone_manager,
    ))
    # Return payload to the caller.
    return payload


# Send to dashboard using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions, then handle the specified errors.
def send_to_dashboard(payload):
    # Run this branch when the negation of DASHBOARD_ENABLED or requests is the same object as None.
    if not DASHBOARD_ENABLED or requests is None:
        # Return no value to the caller.
        return
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call requests.post with the supplied arguments.
        requests.post(
            # Supply DASHBOARD_API_URL to requests.post.
            DASHBOARD_API_URL,
            # Supply json as payload.
            json=payload,
            # Supply timeout as DASHBOARD_TIMEOUT_SECONDS.
            timeout=DASHBOARD_TIMEOUT_SECONDS,
        )
    # Handle requests.RequestException using the recovery steps below.
    except requests.RequestException:
        # Dashboard availability must never stop the simulation.
        # Return no value to the caller.
        return


# Print each finalized ego-target event exactly once.
# Input events: the supplied events.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def print_prediction_events(events):
    """Print each finalized ego-target event exactly once."""
    # Iterate over events, binding each item to update.
    for update in events:
        # Set primary to 'primary' from update; use None if absent.
        primary = update.get("primary")
        # Set secondary to 'secondary' from update; use None if absent.
        secondary = update.get("secondary")
        # Set primary_text to formatted text built from the embedded values when primary is a different object
        # from None, otherwise update at 'primary_stage_status'.
        primary_text = (
            # Evaluate formatted text built from the embedded values when primary is a different object from None,
            # otherwise update at 'primary_stage_status' as part of the enclosing expression.
            f"{primary['label']} {primary['confidence']:.3f}"
            # Evaluate primary is a different object from None as part of the enclosing expression.
            if primary is not None
            # Evaluate update at 'primary_stage_status' as part of the enclosing expression.
            else update["primary_stage_status"]
        )
        # Set secondary_text to formatted text built from the embedded values when secondary is a different object
        # from None, otherwise update at 'secondary_stage_status'.
        secondary_text = (
            # Evaluate formatted text built from the embedded values when secondary is a different object from
            # None, otherwise update at 'secondary_stage_status' as part of the enclosing expression.
            f"{secondary['label']} {secondary['confidence']:.3f}"
            # Evaluate secondary is a different object from None as part of the enclosing expression.
            if secondary is not None
            # Evaluate update at 'secondary_stage_status' as part of the enclosing expression.
            else update["secondary_stage_status"]
        )
        # Display formatted text built from the embedded values.
        print(
            # Supply formatted text built from the embedded values to print.
            f"t={update['finalization_time']:7.2f} | "
            # Evaluate {update['event_id']} as part of the enclosing expression.
            f"event={update['event_id']} | "
            # Evaluate {update['ego_id']} as part of the enclosing expression.
            f"ego={update['ego_id']} | "
            # Evaluate {update['target_id']} as part of the enclosing expression.
            f"target={update['target_id']} | "
            # Evaluate {primary_text} as part of the enclosing expression.
            f"primary={primary_text} | "
            # Evaluate {secondary_text} as part of the enclosing expression.
            f"secondary={secondary_text} | "
            # Evaluate {update['fused_label']} as part of the enclosing expression.
            f"fused={update['fused_label']} | "
            # Evaluate {update['status']} as part of the enclosing expression.
            f"status={update['status']}"
        )


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Display the text 'Sensor configuration:'.
    print("Sensor configuration:")
    # Iterate over key/value pairs from SENSOR_CONFIGURATION_SUMMARY, binding each item to (name, value).
    for name, value in SENSOR_CONFIGURATION_SUMMARY.items():
        # Display formatted text built from the embedded values.
        print(f"  {name}: {value}")
    # Run this branch when the negation of SHADOW_MODE.
    if not SHADOW_MODE:
        # Raise RuntimeError with the text 'This checkpoint is intentionally shadow-only. Set...' to stop this
        # execution path.
        raise RuntimeError(
            "This checkpoint is intentionally shadow-only. "
            "Set SHADOW_MODE=True until conflict and safety modules exist."
        )

    # Set predictor to the result of IntentionPredictor().
    predictor = IntentionPredictor()
    # Set map_path_manager to the result of MapPathManager().
    map_path_manager = MapPathManager()
    # Set conflict_zone_manager to the result of ConflictZoneManager(map_path_manager).
    conflict_zone_manager = ConflictZoneManager(map_path_manager)
    # Set conflict_graph_manager to the result of ConflictGraphManager(map_path_manager, conflict_zone_manager).
    conflict_graph_manager = ConflictGraphManager(
        # Supply conflict_zone_manager to ConflictGraphManager.
        map_path_manager, conflict_zone_manager
    )
    # Set occupancy_assessor to the result of ConflictZoneOccupancyAssessor(map_path_manager,
    # conflict_zone_manager).
    occupancy_assessor = ConflictZoneOccupancyAssessor(
        # Supply conflict_zone_manager to ConflictZoneOccupancyAssessor.
        map_path_manager, conflict_zone_manager
    )
    # Set traffic_rule_engine to the result of TrafficRuleEngine(map_path_manager).
    traffic_rule_engine = TrafficRuleEngine(map_path_manager)
    # Set negotiation_environment to the result of NegotiationEnvironment().
    negotiation_environment = NegotiationEnvironment()
    # Set v2v_claim_bus to the result of V2VPrecedenceClaimBus().
    v2v_claim_bus = V2VPrecedenceClaimBus()
    # Set graph_tensor_encoder to the result of GraphTensorEncoder().
    graph_tensor_encoder = GraphTensorEncoder()
    # Set network_odd to the result of validate_network_odd(SUMO_NETWORK_FILE).
    network_odd = validate_network_odd(SUMO_NETWORK_FILE)
    # Run this branch when the negation of network_odd at 'passed'.
    if not network_odd["passed"]:
        # Raise RuntimeError with the text 'Compiled SUMO network is incompatible with the regulatory ODD:' plus
        # the result of ', '.join(network_odd at 'errors') to stop this execution path.
        raise RuntimeError(
            "Compiled SUMO network is incompatible with the regulatory ODD: "
            # Evaluate the result of ', '.join(network_odd at 'errors') as part of the enclosing expression.
            + ", ".join(network_odd["errors"])
        )
    # Call write_conflict_catalogues with the supplied arguments.
    write_conflict_catalogues(
        # Supply conflict_zone_manager to write_conflict_catalogues.
        map_path_manager, conflict_zone_manager, OUTPUT_DIR
    )
    # Run this branch when CONFLICT_DEBUG_OUTPUT.
    if CONFLICT_DEBUG_OUTPUT:
        # Display the text 'Conflict map loaded:'.
        print("Conflict map loaded:")
        # Display formatted text built from the embedded values.
        print(f"  movement paths: {len(map_path_manager.paths)}")
        # Display formatted text built from the embedded values.
        print(
            "  crossing/merging conflict relationships: "
            # Evaluate {len(conflict_zone_manager.zone_geometries)} as part of the enclosing expression.
            f"{len(conflict_zone_manager.zone_geometries)}"
        )
        # Display formatted text built from the embedded values.
        print(f"  conflict zones: {len(conflict_zone_manager.zone_geometries)}")
    # Set negotiation_manager to the result of NegotiationManager().
    negotiation_manager = NegotiationManager()
    # Set route_cycle to the result of cycle(ROUTE_IDS).
    route_cycle = cycle(ROUTE_IDS)
    # Set validation_schedule to the result of deque(VALIDATION_SPAWN_SCHEDULE).
    validation_schedule = deque(VALIDATION_SPAWN_SCHEDULE)

    # Call evaluator.reset with the supplied arguments.
    evaluator.reset()
    # Call observation_manager.reset with the supplied arguments.
    observation_manager.reset()
    # Call conflict_entry_monitor.reset with the supplied arguments.
    conflict_entry_monitor.reset()
    # Call risk_assessor.reset with the supplied arguments.
    risk_assessor.reset()
    # Call demand_ledger.reset with the supplied arguments.
    demand_ledger.reset()

    # Set environment to the result of SUMOEnv().
    environment = SUMOEnv(use_gui=USE_SUMO_GUI)
    # Set current_actions to an empty dictionary.
    current_actions = {}
    # Set vehicle_counter to 0.
    vehicle_counter = 0
    # Set next_spawn_time to SPAWN_INTERVAL_SECONDS.
    next_spawn_time = SPAWN_INTERVAL_SECONDS
    # Set next_control_time to 0.0.
    next_control_time = 0.0
    # Set next_dashboard_time to 0.0.
    next_dashboard_time = 0.0
    # Set next_visualization_time to 0.0.
    next_visualization_time = 0.0
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Set evidence_writer to the result of EvidenceJsonlWriter(PERCEPTION_EVIDENCE_JSONL).
        evidence_writer = EvidenceJsonlWriter(PERCEPTION_EVIDENCE_JSONL)
    # Handle OSError as error using the recovery steps below.
    except OSError as error:
        # Display formatted text built from the embedded values.
        print(f"Perception evidence logging unavailable: {error}")
        # Set evidence_writer to None.
        evidence_writer = None
    # Set overlay to the result of SumoDebugOverlay(traci).
    overlay = SumoDebugOverlay(
        # Supply traci to SumoDebugOverlay.
        traci,
        # Supply enabled as VISUALIZATION_ENABLED and USE_SUMO_GUI.
        enabled=VISUALIZATION_ENABLED and USE_SUMO_GUI,
        # Supply ego_id as VISUALIZATION_DEMO_EGO_ID.
        ego_id=VISUALIZATION_DEMO_EGO_ID,
        # Supply sensor_range as SENSOR_RANGE.
        sensor_range=SENSOR_RANGE,
        # Supply sensor_overlay as VISUALIZATION_SENSOR_OVERLAY_ENABLED.
        sensor_overlay=VISUALIZATION_SENSOR_OVERLAY_ENABLED,
        # Supply point_count as VISUALIZATION_SENSOR_CIRCLE_POINTS.
        point_count=VISUALIZATION_SENSOR_CIRCLE_POINTS,
    )

    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call environment.start with the supplied arguments.
        environment.start()

        # Run this branch when VALIDATION_SCENARIO_ENABLED.
        if VALIDATION_SCENARIO_ENABLED:
            # Repeat the following steps while validation_schedule and validation_schedule[0] at 0 is at most 0.0.
            while validation_schedule and validation_schedule[0][0] <= 0.0:
                # Set (scheduled_time, route_id) to the result of validation_schedule.popleft().
                scheduled_time, route_id = validation_schedule.popleft()
                # Call add_autonomous_vehicle with the supplied arguments.
                add_autonomous_vehicle(
                    # Supply formatted text built from the embedded values to add_autonomous_vehicle.
                    f"AV_{vehicle_counter}", route_id, scheduled_time,
                    # Supply DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE to add_autonomous_vehicle.
                    DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE,
                )
                # Update vehicle_counter to its current value plus 1.
                vehicle_counter += 1
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Iterate over the integer range defined by INITIAL_VEHICLE_COUNT, binding each item to _.
            for _ in range(INITIAL_VEHICLE_COUNT):
                # Call add_autonomous_vehicle with the supplied arguments.
                add_autonomous_vehicle(
                    # Supply formatted text built from the embedded values to add_autonomous_vehicle.
                    f"AV_{vehicle_counter}", next(route_cycle),
                    # Supply environment.current_time to add_autonomous_vehicle.
                    environment.current_time,
                    # Supply DemandScheduleSource.INITIAL_SIMULATION_DEMAND to add_autonomous_vehicle.
                    DemandScheduleSource.INITIAL_SIMULATION_DEMAND,
                )
                # Update vehicle_counter to its current value plus 1.
                vehicle_counter += 1

        # Iterate over the integer range defined by EPISODE_STEPS, binding each item to _.
        for _ in range(EPISODE_STEPS):
            # Set observations to the result of environment.step().
            observations = environment.step()
            # Set current_time to environment.current_time.
            current_time = environment.current_time
            # Call demand_ledger.record_lifecycle_events with the supplied arguments.
            demand_ledger.record_lifecycle_events(environment.lifecycle_events)
            # Set evaluation_route_truth to a dictionary of vehicle_id mapped to 'route_id' from state; use the
            # text '' if absent for (vehicle_id, state) in key/value pairs from observations.
            evaluation_route_truth = {
                # Evaluate 'route_id' from state; use the text '' if absent as part of the enclosing expression.
                vehicle_id: state.get("route_id", "")
                # Evaluate key/value pairs from observations as part of the enclosing expression.
                for vehicle_id, state in observations.items()
            }

            # Update observation_manager with the supplied entries.
            observation_manager.update(
                # Supply observations to observation_manager.update.
                observations,
                # Supply current_time to observation_manager.update.
                current_time,
            )

            # Run this branch when current_time plus 1e-09 is at least next_visualization_time.
            if current_time + 1e-9 >= next_visualization_time:
                # Update overlay with the supplied entries.
                overlay.update(observations, observation_manager)
                # Repeat the following steps while next_visualization_time is at most current_time plus 1e-09.
                while next_visualization_time <= current_time + 1e-9:
                    # Update next_visualization_time to its current value plus
                    # VISUALIZATION_REFRESH_INTERVAL_SECONDS.
                    next_visualization_time += (
                        # Evaluate VISUALIZATION_REFRESH_INTERVAL_SECONDS as part of the enclosing expression.
                        VISUALIZATION_REFRESH_INTERVAL_SECONDS
                    )

            # Set prediction_events to an empty list.
            prediction_events = []
            # Iterate over observations, binding each item to ego_id.
            for ego_id in observations:
                # Set ldm to the result of observation_manager.get_ldm(ego_id).
                ldm = observation_manager.get_ldm(ego_id)
                # Run this branch when ldm is a different object from None.
                if ldm is not None:
                    # Extend prediction_events with the result of conflict_entry_monitor.update_ldm(ldm,
                    # current_time, predictor, evaluation_route_truth).
                    prediction_events.extend(
                        # Supply the result of conflict_entry_monitor.update_ldm(ldm, current_time, predictor,
                        # evaluation_route_truth) to prediction_events.extend.
                        conflict_entry_monitor.update_ldm(
                            # Supply ldm to conflict_entry_monitor.update_ldm.
                            ldm,
                            # Supply current_time to conflict_entry_monitor.update_ldm.
                            current_time,
                            # Supply predictor to conflict_entry_monitor.update_ldm.
                            predictor,
                            # Supply evaluation_route_truth to conflict_entry_monitor.update_ldm.
                            evaluation_route_truth,
                        )
                    )
            # Call evaluator.record_prediction_events with the supplied arguments.
            evaluator.record_prediction_events(
                # Supply prediction_events to evaluator.record_prediction_events.
                prediction_events
            )
            # Call print_prediction_events with the supplied arguments.
            print_prediction_events(prediction_events)

            # Phase 1: every AV completes sender-local reasoning and publishes
            # only claims derived from its own LDM. No joint graph exists yet.
            # Call v2v_claim_bus.begin_step with the supplied arguments.
            v2v_claim_bus.begin_step(current_time)
            # Set local_precedence_graphs to an empty dictionary.
            local_precedence_graphs = {}
            # Iterate over observations, binding each item to ego_id.
            for ego_id in observations:
                # Set ldm to the result of observation_manager.get_ldm(ego_id).
                ldm = observation_manager.get_ldm(ego_id)
                # Run this branch when ldm is a different object from None and ldm.in_approach_zone.
                if ldm is not None and ldm.in_approach_zone:
                    # Set ldm.current_conflict_graph to the result of
                    # conflict_graph_manager.build_local_graph(ldm, current_time).
                    ldm.current_conflict_graph = (
                        # Evaluate the result of conflict_graph_manager.build_local_graph(ldm, current_time) as
                        # part of the enclosing expression.
                        conflict_graph_manager.build_local_graph(
                            # Supply current_time to conflict_graph_manager.build_local_graph.
                            ldm, current_time
                        )
                    )
                    # Set ldm.current_temporal_assessment to the result of occupancy_assessor.assess_ldm(ldm,
                    # current_time).
                    ldm.current_temporal_assessment = (
                        # Evaluate the result of occupancy_assessor.assess_ldm(ldm, current_time) as part of the
                        # enclosing expression.
                        occupancy_assessor.assess_ldm(ldm, current_time)
                    )
                    # German-StVO reasoning is deliberately shadow-only. Its
                    # output is not passed to risk, negotiation, or control.
                    # Set ldm.current_regulatory_assessment to the result of traffic_rule_engine.assess_ldm(ldm,
                    # current_time).
                    ldm.current_regulatory_assessment = (
                        # Evaluate the result of traffic_rule_engine.assess_ldm(ldm, current_time) as part of the
                        # enclosing expression.
                        traffic_rule_engine.assess_ldm(ldm, current_time)
                    )
                    # Set (local_graph, claim_messages) to the result of
                    # negotiation_environment.build_local_claims(ldm, current_time).
                    local_graph, claim_messages = (
                        # Evaluate the result of negotiation_environment.build_local_claims(ldm, current_time) as
                        # part of the enclosing expression.
                        negotiation_environment.build_local_claims(
                            # Supply current_time to negotiation_environment.build_local_claims.
                            ldm, current_time
                        )
                    )
                    # Set local_precedence_graphs[ego_id] to local_graph.
                    local_precedence_graphs[ego_id] = local_graph
                    # Iterate over claim_messages, binding each item to claim_message.
                    for claim_message in claim_messages:
                        # Call v2v_claim_bus.publish with the supplied arguments.
                        v2v_claim_bus.publish(claim_message)
                # Run this branch when ldm is a different object from None.
                elif ldm is not None:
                    # Set ldm.current_conflict_graph to None.
                    ldm.current_conflict_graph = None
                    # Set ldm.current_temporal_assessment to None.
                    ldm.current_temporal_assessment = None
                    # Set ldm.current_regulatory_assessment to None.
                    ldm.current_regulatory_assessment = None
                    # Set ldm.current_negotiation_problem to None.
                    ldm.current_negotiation_problem = None
                    # Set ldm.current_encoded_graph_observation to None.
                    ldm.current_encoded_graph_observation = None
                    # Set ldm.current_negotiation_protocol_state to None.
                    ldm.current_negotiation_protocol_state = None
                    # Set ldm.current_negotiated_precedence_overlay to None.
                    ldm.current_negotiated_precedence_overlay = None
                    # Call conflict_graph_manager.reset with the supplied arguments.
                    conflict_graph_manager.reset(ego_id)
                    # Call occupancy_assessor.reset with the supplied arguments.
                    occupancy_assessor.reset(ego_id)

            # One passive 25 Hz record after prediction, spatial graph, and
            # temporal occupancy all correspond to this simulation step.
            # Set evidence_snapshot to the result of build_evidence_snapshot(current_time, observations,
            # observation_manager).
            evidence_snapshot = build_evidence_snapshot(
                # Supply current_time to build_evidence_snapshot.
                current_time,
                # Supply observations to build_evidence_snapshot.
                observations,
                # Supply observation_manager to build_evidence_snapshot.
                observation_manager,
                # Supply sensor_profile as DEFAULT_PERCEPTION_PROFILE.
                sensor_profile=DEFAULT_PERCEPTION_PROFILE,
                # Supply sensor_range as SENSOR_RANGE.
                sensor_range=SENSOR_RANGE,
                # Supply prediction_monitor as conflict_entry_monitor.
                prediction_monitor=conflict_entry_monitor,
                # Supply predictor as predictor.
                predictor=predictor,
                # Supply path_manager as map_path_manager.
                path_manager=map_path_manager,
                # Supply zone_manager as conflict_zone_manager.
                zone_manager=conflict_zone_manager,
            )
            # Run this branch when evidence_writer is a different object from None.
            if evidence_writer is not None:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Call evidence_writer.write with the supplied arguments.
                    evidence_writer.write(evidence_snapshot)
                # Handle (OSError, TypeError, ValueError) as error using the recovery steps below.
                except (OSError, TypeError, ValueError) as error:
                    # Display formatted text built from the embedded values.
                    print(f"Perception evidence logging disabled: {error}")
                    # Call evidence_writer.close with the supplied arguments.
                    evidence_writer.close()
                    # Set evidence_writer to None.
                    evidence_writer = None

            # Phase 2 starts only after every sender has published. Each AV
            # independently expands its own connected component from the same
            # immutable current-step message set, so iteration order is inert.
            # Call v2v_claim_bus.freeze_step with the supplied arguments.
            v2v_claim_bus.freeze_step(current_time)
            # Iterate over observations, binding each item to ego_id.
            for ego_id in observations:
                # Set ldm to the result of observation_manager.get_ldm(ego_id).
                ldm = observation_manager.get_ldm(ego_id)
                # Run this branch when ldm is a different object from None and ego_id belongs to
                # local_precedence_graphs.
                if ldm is not None and ego_id in local_precedence_graphs:
                    # Set ldm.current_negotiation_problem to the result of
                    # negotiation_environment.build_snapshot(ldm, current_time, the result of
                    # v2v_claim_bus.current_messages(current_time),...).
                    ldm.current_negotiation_problem = (
                        # Evaluate the result of negotiation_environment.build_snapshot(ldm, current_time, the
                        # result of v2v_claim_bus.current_messages(current_time),...) as part of the enclosing
                        # expression.
                        negotiation_environment.build_snapshot(
                            # Supply current_time to negotiation_environment.build_snapshot.
                            ldm, current_time,
                            # Supply the result of v2v_claim_bus.current_messages(current_time) to
                            # negotiation_environment.build_snapshot.
                            v2v_claim_bus.current_messages(
                                # Supply receiver_id as ego_id.
                                current_time, receiver_id=ego_id
                            ),
                            # Supply local_precedence_graphs at ego_id to negotiation_environment.build_snapshot.
                            local_precedence_graphs[ego_id],
                        )
                    )
                    # Set ldm.current_encoded_graph_observation to the result of
                    # graph_tensor_encoder.encode(ldm.current_negotiation_problem at 'graph_observation').
                    ldm.current_encoded_graph_observation = (
                        # Evaluate the result of graph_tensor_encoder.encode(ldm.current_negotiation_problem at
                        # 'graph_observation') as part of the enclosing expression.
                        graph_tensor_encoder.encode(
                            # Supply ldm.current_negotiation_problem at 'graph_observation' to
                            # graph_tensor_encoder.encode.
                            ldm.current_negotiation_problem["graph_observation"]
                        )
                    )
                    # Step 5F shadow readiness only. Untrained role-aware policy
                    # interfaces do not fabricate protocol messages or act.
                    # Set ldm.current_negotiation_protocol_state to a dictionary containing communication_model,
                    # state, protocol_status, response_policy_interface,...
                    ldm.current_negotiation_protocol_state = {
                        "communication_model": "IDEAL_SAME_STEP_V2V",
                        "state": "NO_PROPOSAL",
                        "protocol_status":
                            "MULTI_PROPOSAL_PER_CLAIM_PROTOCOL_AVAILABLE_STEP_5E_2",
                        "response_policy_interface":
                            "RESPONSE_POLICY_INTERFACE_IMPLEMENTED_UNTRAINED",
                        "response_policy_learning": "PENDING_MAPPO_INTEGRATION",
                        "role_aware_policy_interface": "IMPLEMENTED_UNTRAINED_STEP_5F",
                        "semantic_encoding_status": "COMPLETE_STEP_5F_1",
                        "transition_semantics_status":
                            "IMPLEMENTED_SHADOW_ONLY_STEP_5G",
                        "scheduled_demand_accounting_status":
                            "IMPLEMENTED_STEP_5H_0",
                        "objective_formulation_status":
                            "IMPLEMENTED_SHADOW_ONLY_STEP_5H",
                        "baseline_reward_definition":
                            "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT",
                        "return_semantics_status":
                            "EXACT_UNDISCOUNTED_EPISODIC_TEAM_RETURN",
                        "advantage_semantics_status":
                            "MONTE_CARLO_RETURN_MINUS_CENTRALIZED_VALUE",
                        "ppo_math_status":
                            "INTERFACE_ONLY_NO_OPTIMIZATION",
                        "experimental_selection_framework_status":
                            "IMPLEMENTED_STEP_5J_1",
                        "controlled_pilot_design_status": "FROZEN_STEP_5J_2",
                        "pilot_training_status": "NOT_STARTED",
                        "negotiation_action_to_traffic_outcome_status":
                            "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE",
                        # Store 0 under 'selected_empirical_parameters'.
                        "selected_empirical_parameters": 0,
                        "training_status": "NOT_STARTED",
                        # Store 0 under 'control_actions_issued'.
                        "control_actions_issued": 0,
                    }
                    # Set ldm.current_negotiated_precedence_overlay to None.
                    ldm.current_negotiated_precedence_overlay = None

            # Run this branch when current_time plus 1e-09 is at least next_control_time.
            if current_time + 1e-9 >= next_control_time:
                # Iterate over observations, binding each item to ego_id.
                for ego_id in observations:
                    # Set ldm to the result of observation_manager.get_ldm(ego_id).
                    ldm = observation_manager.get_ldm(ego_id)
                    # Run this branch when ldm is a different object from None and ldm.in_approach_zone.
                    if ldm is not None and ldm.in_approach_zone:
                        # Call risk_assessor.assess_risk with the supplied arguments.
                        risk_assessor.assess_risk(
                            # Supply ego_id to risk_assessor.assess_risk.
                            ego_id,
                            # Supply ldm to risk_assessor.assess_risk.
                            ldm,
                            # Supply current_time to risk_assessor.assess_risk.
                            current_time,
                        )

                # Set new_actions to an empty dictionary.
                new_actions = {}
                # Iterate over key/value pairs from observations, binding each item to (vehicle_id, state).
                for vehicle_id, state in observations.items():
                    # Set ldm to the result of observation_manager.get_ldm(vehicle_id).
                    ldm = observation_manager.get_ldm(vehicle_id)
                    # Run this branch when ldm is a different object from None and ldm.in_approach_zone.
                    if ldm is not None and ldm.in_approach_zone:
                        # Set nearby_states to an empty list.
                        nearby_states = []
                        # Set risk_metrics to the result of risk_assessor.get_risk_data(vehicle_id).
                        risk_metrics = (
                            # Evaluate the result of risk_assessor.get_risk_data(vehicle_id) as part of the
                            # enclosing expression.
                            risk_assessor.get_risk_data(vehicle_id)
                        )
                        # Iterate over key/value pairs from ldm.get_conflict_relevant_vehicles(), binding each
                        # item to (other_id, track).
                        for other_id, track in (
                            # Evaluate key/value pairs from ldm.get_conflict_relevant_vehicles() as part of the
                            # enclosing expression.
                            ldm.get_conflict_relevant_vehicles().items()
                        ):
                            # Set enhanced to a dictionary built from track.
                            enhanced = dict(track)
                            # Update enhanced with the supplied entries.
                            enhanced.update(
                                # Supply other_id from risk_metrics; use an empty dictionary if absent to
                                # enhanced.update.
                                risk_metrics.get(other_id, {})
                            )
                            # Append enhanced to nearby_states.
                            nearby_states.append(enhanced)

                        # Set action to the result of negotiation_manager.negotiate(a dictionary of key mapped to
                        # value for (key, value) in key/value pairs from state; retain...).
                        action = negotiation_manager.negotiate(
                            # Supply a dictionary of key mapped to value for (key, value) in key/value pairs from
                            # state; retain entries satisfying key does not belong to a set containing the text
                            # 'route_id', the text... to negotiation_manager.negotiate.
                            {
                                # Evaluate key/value pairs from state as part of the enclosing expression.
                                key: value for key, value in state.items()
                                # Evaluate key does not belong to a set containing the text 'route_id', the text
                                # 'ground_truth_route_id', the text 'route_index' as part of the enclosing
                                # expression.
                                if key not in {
                                    "route_id", "ground_truth_route_id",
                                    "route_index",
                                }
                            },
                            # Supply nearby_states to negotiation_manager.negotiate.
                            nearby_states,
                            # Supply ldm to negotiation_manager.negotiate.
                            ldm,
                        )
                    # Run this alternative branch when the preceding branch does not apply.
                    else:
                        # Set action to the text 'MAINTAIN'.
                        action = "MAINTAIN"

                    # Set new_actions[vehicle_id] to action.
                    new_actions[vehicle_id] = action
                    # Call apply_action with the supplied arguments.
                    apply_action(vehicle_id, state, action)

                # Set current_actions to new_actions.
                current_actions = new_actions
                # Repeat the following steps while next_control_time is at most current_time plus 1e-09.
                while (
                    # Evaluate next_control_time is at most current_time plus 1e-09 as part of the enclosing
                    # expression.
                    next_control_time
                    # Evaluate current_time plus 1e-09 as part of the enclosing expression.
                    <= current_time + 1e-9
                ):
                    # Update next_control_time to its current value plus CONTROL_UPDATE_INTERVAL_SECONDS.
                    next_control_time += (
                        # Evaluate CONTROL_UPDATE_INTERVAL_SECONDS as part of the enclosing expression.
                        CONTROL_UPDATE_INTERVAL_SECONDS
                    )

            # Run this branch when VALIDATION_SCENARIO_ENABLED.
            if VALIDATION_SCENARIO_ENABLED:
                # Repeat the following steps while validation_schedule and validation_schedule[0] at 0 is at most
                # current_time plus 1e-09.
                while validation_schedule and validation_schedule[0][0] <= current_time + 1e-9:
                    # Set (scheduled_time, route_id) to the result of validation_schedule.popleft().
                    scheduled_time, route_id = validation_schedule.popleft()
                    # Call add_autonomous_vehicle with the supplied arguments.
                    add_autonomous_vehicle(
                        # Supply formatted text built from the embedded values to add_autonomous_vehicle.
                        f"AV_{vehicle_counter}", route_id, scheduled_time,
                        # Supply DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE to add_autonomous_vehicle.
                        DemandScheduleSource.VALIDATION_SPAWN_SCHEDULE,
                    )
                    # Update vehicle_counter to its current value plus 1.
                    vehicle_counter += 1
            # Run this branch when current_time plus 1e-09 is at least next_spawn_time and current_time is less
            # than EPISODE_DURATION_SECONDS minus 5.0.
            elif (
                # Evaluate current_time plus 1e-09 is at least next_spawn_time and current_time is less than
                # EPISODE_DURATION_SECONDS minus 5.0 as part of the enclosing expression.
                current_time + 1e-9 >= next_spawn_time
                # Evaluate current_time is less than EPISODE_DURATION_SECONDS minus 5.0 as part of the enclosing
                # expression.
                and current_time
                # Evaluate EPISODE_DURATION_SECONDS minus 5.0 as part of the enclosing expression.
                < EPISODE_DURATION_SECONDS - 5.0
            ):
                # Iterate over the integer range defined by SPAWN_BATCH_SIZE, binding each item to _.
                for _ in range(SPAWN_BATCH_SIZE):
                    # Set vehicle_id to formatted text built from the embedded values.
                    vehicle_id = f"AV_{vehicle_counter}"
                    # Call add_autonomous_vehicle with the supplied arguments.
                    add_autonomous_vehicle(
                        # Supply vehicle_id to add_autonomous_vehicle.
                        vehicle_id,
                        # Supply the next item from route_cycle to add_autonomous_vehicle.
                        next(route_cycle),
                        # Supply next_spawn_time to add_autonomous_vehicle.
                        next_spawn_time,
                        # Supply DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE to add_autonomous_vehicle.
                        DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE,
                    )
                    # Update vehicle_counter to its current value plus 1.
                    vehicle_counter += 1
                # Update next_spawn_time to its current value plus SPAWN_INTERVAL_SECONDS.
                next_spawn_time += SPAWN_INTERVAL_SECONDS

            # Update evaluator with the supplied entries.
            evaluator.update(current_time, observations, environment.lifecycle_events)

            # Run this branch when current_time plus 1e-09 is at least next_dashboard_time.
            if current_time + 1e-9 >= next_dashboard_time:
                # Call send_to_dashboard with the supplied arguments.
                send_to_dashboard(
                    # Supply the result of build_dashboard_payload(current_time, observations, current_actions,
                    # predictor, map_path_manager, conflict_zone_manager) to send_to_dashboard.
                    build_dashboard_payload(
                        # Supply current_time to build_dashboard_payload.
                        current_time,
                        # Supply observations to build_dashboard_payload.
                        observations,
                        # Supply current_actions to build_dashboard_payload.
                        current_actions,
                        # Supply predictor to build_dashboard_payload.
                        predictor,
                        # Supply map_path_manager to build_dashboard_payload.
                        map_path_manager,
                        # Supply conflict_zone_manager to build_dashboard_payload.
                        conflict_zone_manager,
                    )
                )
                # Update next_dashboard_time to its current value plus DASHBOARD_UPDATE_INTERVAL_SECONDS.
                next_dashboard_time += (
                    # Evaluate DASHBOARD_UPDATE_INTERVAL_SECONDS as part of the enclosing expression.
                    DASHBOARD_UPDATE_INTERVAL_SECONDS
                )

        # Set final_events to the result of conflict_entry_monitor.finalize_all(environment.current_time,
        # predictor).
        final_events = conflict_entry_monitor.finalize_all(
            # Supply environment.current_time to conflict_entry_monitor.finalize_all.
            environment.current_time,
            # Supply predictor to conflict_entry_monitor.finalize_all.
            predictor,
        )
        # Call evaluator.record_prediction_events with the supplied arguments.
        evaluator.record_prediction_events(final_events)
        # Call print_prediction_events with the supplied arguments.
        print_prediction_events(final_events)
        # Call evaluator.compute_metrics with the supplied arguments.
        evaluator.compute_metrics(environment.current_time)
        # Call evaluator.save_prediction_log with the supplied arguments.
        evaluator.save_prediction_log()

    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Run this branch when evidence_writer is a different object from None.
        if evidence_writer is not None:
            # Call evidence_writer.close with the supplied arguments.
            evidence_writer.close()
        # Call demand_ledger.finalize_episode with the supplied arguments.
        demand_ledger.finalize_episode(environment.current_time)
        # Set demand_summary to the result of demand_ledger.validation_summary().
        demand_summary = demand_ledger.validation_summary()
        # Display the text 'Demand Ledger validation'.
        print("\nDemand Ledger validation")
        # Iterate over a tuple containing a tuple containing the text 'Scheduled vehicles', the text
        # 'scheduled_vehicles', a tuple containing the..., binding each item to (label, key).
        for label, key in (
            # Include a tuple containing the text 'Scheduled vehicles', the text 'scheduled_vehicles' in this
            # tuple.
            ("Scheduled vehicles", "scheduled_vehicles"),
            # Include a tuple containing the text 'Actual departures recorded', the text
            # 'actual_departures_recorded' in this tuple.
            ("Actual departures recorded", "actual_departures_recorded"),
            # Include a tuple containing the text 'Service completions recorded', the text
            # 'service_completions_recorded' in this tuple.
            ("Service completions recorded", "service_completions_recorded"),
            # Include a tuple containing the text 'Scheduled but not departed at episode end', the text
            # 'scheduled_not_departed_at_episode_end' in this tuple.
            ("Scheduled but not departed at episode end", "scheduled_not_departed_at_episode_end"),
            # Include a tuple containing the text 'Departed but unfinished at episode end', the text
            # 'departed_not_completed_at_episode_end' in this tuple.
            ("Departed but unfinished at episode end", "departed_not_completed_at_episode_end"),
            # Include a tuple containing the text 'Completed services', the text 'completed_services' in this
            # tuple.
            ("Completed services", "completed_services"),
            # Include a tuple containing the text 'Accounting errors', the text 'accounting_errors' in this tuple.
            ("Accounting errors", "accounting_errors"),
        ):
            # Display formatted text built from the embedded values.
            print(f"  {label}: {demand_summary[key]}")
        # Set travel_measurements to the result of measure_vehicle_travel_times(the result of
        # demand_ledger.get_all_records(), environment.current_time).
        travel_measurements = measure_vehicle_travel_times(
            # Supply the result of demand_ledger.get_all_records() to measure_vehicle_travel_times.
            demand_ledger.get_all_records(), environment.current_time,
        )
        # Set team_cost to the result of total_team_travel_time_seconds(travel_measurements).
        team_cost = total_team_travel_time_seconds(travel_measurements)
        # Set objective_diagnostics to the result of compute_objective_diagnostics(travel_measurements).
        objective_diagnostics = compute_objective_diagnostics(travel_measurements)
        # Display the text 'Negotiation Objective validation'.
        print("\nNegotiation Objective validation")
        # Display the text 'Baseline definition: NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT'.
        print("  Baseline definition: NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT")
        # Display formatted text built from the embedded values.
        print(f"  Team travel-time cost (vehicle-seconds): {team_cost}")
        # Display formatted text built from the embedded values.
        print(f"  Raw shared team reward (negative vehicle-seconds): {raw_team_reward(team_cost)}")
        # Display formatted text built from the embedded values.
        print(f"  Vehicles measured: {objective_diagnostics.vehicles_measured}")
        # Display formatted text built from the embedded values.
        print(f"  Completed services diagnostic: {objective_diagnostics.completed_services}")
        # Display the text 'Learned policy actions issued: 0'.
        print("  Learned policy actions issued: 0")
        # Set conflict_summary to the result of conflict_graph_manager.validation_summary().
        conflict_summary = conflict_graph_manager.validation_summary()
        # Display the text 'Conflict Graph validation'.
        print("\nConflict Graph validation")
        # Display formatted text built from the embedded values.
        print(f"  Discovered movement paths: {len(map_path_manager.paths)}")
        # Display formatted text built from the embedded values.
        print(f"  Map conflict zones: {len(conflict_zone_manager.zone_geometries)}")
        # Display formatted text built from the embedded values.
        print(f"  Graphs built: {conflict_summary['graphs_built']}")
        # Display formatted text built from the embedded values.
        print(
            "  Spatial conflict edges observed: "
            # Evaluate {conflict_summary['spatial_conflict_edges_observed']} as part of the enclosing expression.
            f"{conflict_summary['spatial_conflict_edges_observed']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Unknown-intention conservative edges: "
            # Evaluate {conflict_summary['unknown_intention_conservative_edges']} as part of the enclosing
            # expression.
            f"{conflict_summary['unknown_intention_conservative_edges']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Prediction-unavailable conservative edges: "
            # Evaluate {conflict_summary['prediction_unavailable_conservative_edges']} as part of the enclosing
            # expression.
            f"{conflict_summary['prediction_unavailable_conservative_edges']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Non-conflicting targets filtered: "
            # Evaluate {conflict_summary['non_conflicting_targets_filtered']} as part of the enclosing expression.
            f"{conflict_summary['non_conflicting_targets_filtered']}"
        )
        # Set temporal_summary to the result of occupancy_assessor.validation_summary().
        temporal_summary = occupancy_assessor.validation_summary()
        # Display the text 'Temporal Reachability validation'.
        print("\nTemporal Reachability validation")
        # Display formatted text built from the embedded values.
        print(
            "  Spatial edges evaluated: "
            # Evaluate {temporal_summary['spatial_edges_evaluated']} as part of the enclosing expression.
            f"{temporal_summary['spatial_edges_evaluated']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Spatially-conflicting candidate path evaluations: "
            # Evaluate {temporal_summary['candidate_path_zone_evaluations']} as part of the enclosing expression.
            f"{temporal_summary['candidate_path_zone_evaluations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Nominal constant-speed temporal conflicts: "
            # Evaluate {temporal_summary['temporal_conflicts_observed']} as part of the enclosing expression.
            f"{temporal_summary['temporal_conflicts_observed']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Nominal temporal separations: "
            # Evaluate {temporal_summary['spatial_only_temporal_separations']} as part of the enclosing
            # expression.
            f"{temporal_summary['spatial_only_temporal_separations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Currently-occupied-zone evaluations: "
            # Evaluate {temporal_summary['currently_occupied_zone_evaluations']} as part of the enclosing
            # expression.
            f"{temporal_summary['currently_occupied_zone_evaluations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Cleared-zone evaluations: "
            # Evaluate {temporal_summary['cleared_zone_evaluations']} as part of the enclosing expression.
            f"{temporal_summary['cleared_zone_evaluations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Unresolved timing evaluations: "
            # Evaluate {temporal_summary['unresolved_timing_evaluations']} as part of the enclosing expression.
            f"{temporal_summary['unresolved_timing_evaluations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "    Path progress unresolved: "
            # Evaluate {temporal_summary['unresolved_path_progress']} as part of the enclosing expression.
            f"{temporal_summary['unresolved_path_progress']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "    Speed unresolved: "
            # Evaluate {temporal_summary['unresolved_speed']} as part of the enclosing expression.
            f"{temporal_summary['unresolved_speed']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "    Vehicle state unresolved: "
            # Evaluate {temporal_summary['unresolved_vehicle_state']} as part of the enclosing expression.
            f"{temporal_summary['unresolved_vehicle_state']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "    No applicable evaluation: "
            # Evaluate {temporal_summary['unresolved_no_applicable_evaluation']} as part of the enclosing
            # expression.
            f"{temporal_summary['unresolved_no_applicable_evaluation']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Candidate paths rejected by observed lane: "
            # Evaluate {temporal_summary['candidate_paths_rejected_by_observed_lane']} as part of the enclosing
            # expression.
            f"{temporal_summary['candidate_paths_rejected_by_observed_lane']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Candidate paths without an applicable zone: "
            # Evaluate {temporal_summary['no_applicable_zone']} as part of the enclosing expression.
            f"{temporal_summary['no_applicable_zone']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Nominal timing unavailable due to zero speed: "
            # Evaluate {temporal_summary['nominal_timing_unavailable_due_to_zero_speed']} as part of the enclosing
            # expression.
            f"{temporal_summary['nominal_timing_unavailable_due_to_zero_speed']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Earliest-reachability calculations: "
            # Evaluate {temporal_summary['earliest_reachability_calculations']} as part of the enclosing
            # expression.
            f"{temporal_summary['earliest_reachability_calculations']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Stopped vehicles with finite earliest arrival: "
            # Evaluate {temporal_summary['stopped_vehicles_with_finite_earliest_arrival']} as part of the
            # enclosing expression.
            f"{temporal_summary['stopped_vehicles_with_finite_earliest_arrival']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Vehicles able to stop before zone: "
            # Evaluate {temporal_summary['vehicles_able_to_stop_before_zone']} as part of the enclosing
            # expression.
            f"{temporal_summary['vehicles_able_to_stop_before_zone']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Vehicles unable to stop before zone: "
            # Evaluate {temporal_summary['vehicles_unable_to_stop_before_zone']} as part of the enclosing
            # expression.
            f"{temporal_summary['vehicles_unable_to_stop_before_zone']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Physical state/dynamics unresolved: "
            # Evaluate {temporal_summary['physical_state_or_dynamics_unresolved']} as part of the enclosing
            # expression.
            f"{temporal_summary['physical_state_or_dynamics_unresolved']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Non-conflicting candidate paths excluded: "
            # Evaluate {temporal_summary['non_conflicting_candidate_paths_excluded']} as part of the enclosing
            # expression.
            f"{temporal_summary['non_conflicting_candidate_paths_excluded']}"
        )
        # Display formatted text built from the embedded values.
        print(
            "  Unique ego-target pairs with temporal conflict: "
            # Evaluate {temporal_summary['unique_ego_target_pairs_with_temporal_conflict']} as part of the
            # enclosing expression.
            f"{temporal_summary['unique_ego_target_pairs_with_temporal_conflict']}"
        )
        # Set rule_summary to the result of traffic_rule_engine.validation_summary().
        rule_summary = traffic_rule_engine.validation_summary()
        # Display the text 'Traffic Rule validation'.
        print("\nTraffic Rule validation")
        # Display formatted text built from the embedded values.
        print(f"  Regulatory profile: {traffic_rule_engine.context.profile_id}")
        # Display formatted text built from the embedded values.
        print(f"  ODD validation passed: {network_odd['passed']}")
        # Display formatted text built from the embedded values.
        print(f"  Central SUMO junction type: {network_odd['junction_type']}")
        # Display formatted text built from the embedded values.
        print(
            "  Right-hand network confirmed: "
            # Evaluate {network_odd['right_hand_network_confirmed']} as part of the enclosing expression.
            f"{network_odd['right_hand_network_confirmed']}"
        )
        # Set labels to a tuple containing a tuple containing the text 'Local regulatory assessments built', the
        # text...
        labels = (
            # Include a tuple containing the text 'Local regulatory assessments built', the text
            # 'local_regulatory_assessments_built' in this tuple.
            ("Local regulatory assessments built", "local_regulatory_assessments_built"),
            # Include a tuple containing the text 'Spatial conflict pairs assessed', the text
            # 'spatial_conflict_pairs_assessed' in this tuple.
            ("Spatial conflict pairs assessed", "spatial_conflict_pairs_assessed"),
            # Include a tuple containing the text 'StVO §8 right-before-left obligations', the text
            # 'stvo_8_right_before_left_obligations' in this tuple.
            ("StVO §8 right-before-left obligations", "stvo_8_right_before_left_obligations"),
            # Include a tuple containing the text 'StVO §9 turning/oncoming obligations', the text
            # 'stvo_9_turning_oncoming_obligations' in this tuple.
            ("StVO §9 turning/oncoming obligations", "stvo_9_turning_oncoming_obligations"),
            # Include a tuple containing the text 'StVO §9(4) left-vs-oncoming-right obligations', the text
            # 'stvo_9_4_left_oncoming_right_obligations' in this tuple.
            ("StVO §9(4) left-vs-oncoming-right obligations", "stvo_9_4_left_oncoming_right_obligations"),
            # Include a tuple containing the text 'Ego mandatory-yield assessments', the text
            # 'ego_mandatory_yield_assessments' in this tuple.
            ("Ego mandatory-yield assessments", "ego_mandatory_yield_assessments"),
            # Include a tuple containing the text 'Ego precedence-under-rule assessments', the text
            # 'ego_precedence_under_rule_assessments' in this tuple.
            ("Ego precedence-under-rule assessments", "ego_precedence_under_rule_assessments"),
            # Include a tuple containing the text 'Manoeuvre-dependent unresolved assessments', the text
            # 'manoeuvre_dependent_unresolved_assessments' in this tuple.
            ("Manoeuvre-dependent unresolved assessments", "manoeuvre_dependent_unresolved_assessments"),
            # Include a tuple containing the text 'Regulatory input unresolved', the text
            # 'regulatory_input_unresolved' in this tuple.
            ("Regulatory input unresolved", "regulatory_input_unresolved"),
            # Include a tuple containing the text 'Target route-truth fields consumed', the text
            # 'target_route_truth_fields_consumed' in this tuple.
            ("Target route-truth fields consumed", "target_route_truth_fields_consumed"),
        )
        # Iterate over labels, binding each item to (label, key).
        for label, key in labels:
            # Display formatted text built from the embedded values.
            print(f"  {label}: {rule_summary[key]}")
        # Set negotiation_summary to the result of negotiation_environment.validation_summary().
        negotiation_summary = negotiation_environment.validation_summary()
        # Display the text 'V2V Negotiation Graph validation'.
        print("\nV2V Negotiation Graph validation")
        # Set bus_summary to the result of v2v_claim_bus.validation_summary().
        bus_summary = v2v_claim_bus.validation_summary()
        # Set negotiation_labels to a tuple containing a tuple containing the text 'Local precedence claims
        # published', the text...
        negotiation_labels = (
            # Include a tuple containing the text 'Local precedence claims published', the text
            # 'local_precedence_claims_published' in this tuple.
            ("Local precedence claims published", "local_precedence_claims_published"),
            # Include a tuple containing the text 'Current-step V2V messages created', the text
            # 'current_step_v2v_messages_created' in this tuple.
            ("Current-step V2V messages created", "current_step_v2v_messages_created"),
            # Include a tuple containing the text 'Joint local negotiation snapshots built', the text
            # 'joint_local_negotiation_snapshots_built' in this tuple.
            ("Joint local negotiation snapshots built", "joint_local_negotiation_snapshots_built"),
            # Include a tuple containing the text 'Snapshots with active conflict participants', the text
            # 'snapshots_with_active_conflict_participants' in this tuple.
            ("Snapshots with active conflict participants", "snapshots_with_active_conflict_participants"),
            # Include a tuple containing the text 'Messages received by local agents', the text
            # 'messages_received_by_local_agents' in this tuple.
            ("Messages received by local agents", "messages_received_by_local_agents"),
            # Include a tuple containing the text 'Messages adopted into connected components', the text
            # 'messages_adopted_into_connected_components' in this tuple.
            ("Messages adopted into connected components", "messages_adopted_into_connected_components"),
            # Include a tuple containing the text 'Unconnected messages ignored', the text
            # 'unconnected_messages_ignored' in this tuple.
            ("Unconnected messages ignored", "unconnected_messages_ignored"),
            # Include a tuple containing the text 'Duplicate claims merged', the text 'duplicate_claims_merged' in
            # this tuple.
            ("Duplicate claims merged", "duplicate_claims_merged"),
            # Include a tuple containing the text 'Communicated precedence disagreements', the text
            # 'communicated_precedence_disagreements' in this tuple.
            ("Communicated precedence disagreements", "communicated_precedence_disagreements"),
            # Include a tuple containing the text 'Joint precedence edges', the text 'joint_precedence_edges' in
            # this tuple.
            ("Joint precedence edges", "joint_precedence_edges"),
            # Include a tuple containing the text 'Joint graphs with expanded participant sets', the text
            # 'joint_graphs_with_expanded_participant_sets' in this tuple.
            ("Joint graphs with expanded participant sets", "joint_graphs_with_expanded_participant_sets"),
            # Include a tuple containing the text 'Regulatory-order-resolved joint graphs', the text
            # 'regulatory_order_resolved_snapshots' in this tuple.
            ("Regulatory-order-resolved joint graphs", "regulatory_order_resolved_snapshots"),
            # Include a tuple containing the text 'Regulatory-cycle joint graphs', the text
            # 'regulatory_cycle_snapshots' in this tuple.
            ("Regulatory-cycle joint graphs", "regulatory_cycle_snapshots"),
            # Include a tuple containing the text 'Unresolved-precedence snapshots', the text
            # 'unresolved_precedence_snapshots' in this tuple.
            ("Unresolved-precedence snapshots", "unresolved_precedence_snapshots"),
            # Include a tuple containing the text 'No-active-conflict snapshots', the text
            # 'no_active_conflict_snapshots' in this tuple.
            ("No-active-conflict snapshots", "no_active_conflict_snapshots"),
            # Include a tuple containing the text 'Strongly connected cyclic components observed', the text... in
            # this tuple.
            ("Strongly connected cyclic components observed", "strongly_connected_cyclic_components_observed"),
            # Include a tuple containing the text 'Maximum local participants before V2V expansion', the text...
            # in this tuple.
            ("Maximum local participants before V2V expansion", "maximum_local_participants_before_v2v_expansion"),
            # Include a tuple containing the text 'Maximum joint participants after V2V expansion', the text... in
            # this tuple.
            ("Maximum joint participants after V2V expansion", "maximum_joint_participants_after_v2v_expansion"),
            # Include a tuple containing the text 'Source snapshot mismatches', the text
            # 'source_snapshot_mismatches' in this tuple.
            ("Source snapshot mismatches", "source_snapshot_mismatches"),
            # Include a tuple containing the text 'Regulatory-profile mismatches', the text
            # 'regulatory_profile_mismatches' in this tuple.
            ("Regulatory-profile mismatches", "regulatory_profile_mismatches"),
            # Include a tuple containing the text 'Target route-truth fields consumed', the text
            # 'target_route_truth_fields_consumed' in this tuple.
            ("Target route-truth fields consumed", "target_route_truth_fields_consumed"),
            # Include a tuple containing the text 'Control actions issued by negotiation environment', the text...
            # in this tuple.
            ("Control actions issued by negotiation environment", "control_actions_issued_by_negotiation_environment"),
        )
        # Iterate over negotiation_labels, binding each item to (label, key).
        for label, key in negotiation_labels:
            # Set source to bus_summary when key belongs to bus_summary, otherwise negotiation_summary.
            source = bus_summary if key in bus_summary else negotiation_summary
            # Display formatted text built from the embedded values.
            print(f"  {label}: {source[key]}")
        # Set encoding_summary to the result of graph_tensor_encoder.validation_summary().
        encoding_summary = graph_tensor_encoder.validation_summary()
        # Display the text 'GNN Input Encoding validation'.
        print("\nGNN Input Encoding validation")
        # Set encoding_labels to a tuple containing a tuple containing the text 'Encoded graph observations
        # built', the text...
        encoding_labels = (
            # Include a tuple containing the text 'Encoded graph observations built', the text
            # 'encoded_graph_observations_built' in this tuple.
            ("Encoded graph observations built", "encoded_graph_observations_built"),
            # Include a tuple containing the text 'NumPy tensor backend confirmed', the text
            # 'numpy_tensor_backend_confirmed' in this tuple.
            ("NumPy tensor backend confirmed", "numpy_tensor_backend_confirmed"),
            # Include a tuple containing the text 'Maximum encoded nodes', the text 'maximum_encoded_nodes' in
            # this tuple.
            ("Maximum encoded nodes", "maximum_encoded_nodes"),
            # Include a tuple containing the text 'Maximum encoded directed edges', the text
            # 'maximum_encoded_directed_edges' in this tuple.
            ("Maximum encoded directed edges", "maximum_encoded_directed_edges"),
            # Include a tuple containing the text 'Node feature dimension', the text 'node_feature_dimension' in
            # this tuple.
            ("Node feature dimension", "node_feature_dimension"),
            # Include a tuple containing the text 'Edge feature dimension', the text 'edge_feature_dimension' in
            # this tuple.
            ("Edge feature dimension", "edge_feature_dimension"),
            # Include a tuple containing the text 'Encoded graphs with zero edges', the text
            # 'encoded_graphs_with_zero_edges' in this tuple.
            ("Encoded graphs with zero edges", "encoded_graphs_with_zero_edges"),
            # Include a tuple containing the text 'Encoded graphs with communicated-only participants', the
            # text... in this tuple.
            ("Encoded graphs with communicated-only participants", "encoded_graphs_with_communicated_only_participants"),
            # Include a tuple containing the text 'Missing node scalar values masked', the text
            # 'missing_node_scalar_values_masked' in this tuple.
            ("Missing node scalar values masked", "missing_node_scalar_values_masked"),
            # Include a tuple containing the text 'Missing edge scalar values masked', the text
            # 'missing_edge_scalar_values_masked' in this tuple.
            ("Missing edge scalar values masked", "missing_edge_scalar_values_masked"),
            # Include a tuple containing the text 'Non-finite available feature errors', the text
            # 'nonfinite_available_feature_errors' in this tuple.
            ("Non-finite available feature errors", "nonfinite_available_feature_errors"),
            # Include a tuple containing the text 'Route-truth fields consumed', the text
            # 'route_truth_fields_consumed' in this tuple.
            ("Route-truth fields consumed", "route_truth_fields_consumed"),
            # Include a tuple containing the text 'Arbitrary ordinal categorical encodings', the text
            # 'arbitrary_ordinal_categorical_encodings' in this tuple.
            ("Arbitrary ordinal categorical encodings", "arbitrary_ordinal_categorical_encodings"),
            # Include a tuple containing the text 'TensorFlow dependencies introduced', the text
            # 'tensorflow_dependencies_introduced' in this tuple.
            ("TensorFlow dependencies introduced", "tensorflow_dependencies_introduced"),
            # Include a tuple containing the text 'PyTorch dependencies introduced', the text
            # 'pytorch_dependencies_introduced' in this tuple.
            ("PyTorch dependencies introduced", "pytorch_dependencies_introduced"),
            # Include a tuple containing the text 'Control actions issued by tensor encoder', the text
            # 'control_actions_issued_by_tensor_encoder' in this tuple.
            ("Control actions issued by tensor encoder", "control_actions_issued_by_tensor_encoder"),
        )
        # Iterate over encoding_labels, binding each item to (label, key).
        for label, key in encoding_labels:
            # Display formatted text built from the embedded values.
            print(f"  {label}: {encoding_summary[key]}")
        # Call environment.close with the supplied arguments.
        environment.close()
        # Call observation_manager.reset with the supplied arguments.
        observation_manager.reset()
        # Call conflict_entry_monitor.reset with the supplied arguments.
        conflict_entry_monitor.reset()
        # Call risk_assessor.reset with the supplied arguments.
        risk_assessor.reset()
        # Call conflict_graph_manager.reset with the supplied arguments.
        conflict_graph_manager.reset()
        # Call occupancy_assessor.reset with the supplied arguments.
        occupancy_assessor.reset()
        # Call traffic_rule_engine.reset with the supplied arguments.
        traffic_rule_engine.reset()
        # Call negotiation_environment.reset with the supplied arguments.
        negotiation_environment.reset()
        # Call v2v_claim_bus.reset with the supplied arguments.
        v2v_claim_bus.reset()
        # Call graph_tensor_encoder.reset with the supplied arguments.
        graph_tensor_encoder.reset()


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
