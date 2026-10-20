"""Dedicated real-SUMO replay for negotiation-to-traffic causal validation."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import combinations from itertools for the operations below.
from itertools import combinations

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG
# from config for the operations below.
from config import (AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS,
                    SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG)
# Import ConflictGraphManager, ConflictZoneManager, ConflictZoneOccupancyAssessor, MapPathManager from conflict
# for the operations below.
from conflict import (ConflictGraphManager, ConflictZoneManager,
                      ConflictZoneOccupancyAssessor, MapPathManager)
# Import ConflictEntryMonitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import ConflictEntryMonitor
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import ScenarioRole from experimentation for the operations below.
from experimentation import ScenarioRole
# Import GraphTensorEncoder, JointNegotiationBranchEnumerator, NegotiationEnvironment, V2VPrecedenceClaimBus from
# negotiation_learning for the operations below.
from negotiation_learning import (GraphTensorEncoder,
    JointNegotiationBranchEnumerator, NegotiationEnvironment,
    V2VPrecedenceClaimBus)
# Import measure_vehicle_travel_times, raw_team_reward, total_team_travel_time_seconds from negotiation_objective
# for the operations below.
from negotiation_objective import (measure_vehicle_travel_times,
    raw_team_reward, total_team_travel_time_seconds)
# Import NegotiationScenarioSpecification from negotiation_scenarios.models for the operations below.
from negotiation_scenarios.models import NegotiationScenarioSpecification
# Import derive_existing_route_id from negotiation_scenarios.runner for the operations below.
from negotiation_scenarios.runner import derive_existing_route_id
# Import ObservationManager from observation for the operations below.
from observation import ObservationManager
# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor
# Import DemandScheduleSource, VehicleDemandLedger from traffic_accounting for the operations below.
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine

# Import ExecutionConstraintError, build_sumo_native_speed_constraint, speed_mode_enforcement from .controller for
# the operations below.
from .controller import (ExecutionConstraintError,
                         build_sumo_native_speed_constraint,
                         speed_mode_enforcement)
# Import ConflictZoneExecutionPlanner from .planner for the operations below.
from .planner import ConflictZoneExecutionPlanner
# Import ACTION_SOURCE, PhysicalBranchReplaySpecification, PhysicalNegotiationBranchReplayTrace,
# PreBranchPhysicalStateFingerprint from .replay_models for the operations below.
from .replay_models import (ACTION_SOURCE, PhysicalBranchReplaySpecification,
    PhysicalNegotiationBranchReplayTrace, PreBranchPhysicalStateFingerprint)


# Set PAIR_SELECTION_METHOD to the text 'FIRST_CANONICAL_EXECUTABLE_PAIR_WITH_DIFFERENT_EXECUTION_SEMAN...'.
PAIR_SELECTION_METHOD = (
    "FIRST_CANONICAL_EXECUTABLE_PAIR_WITH_DIFFERENT_EXECUTION_SEMANTICS")


# Define PhysicalReplayError to group the state and operations declared below.
# Base classes: RuntimeError.
# Instances expose the attributes and methods implemented in this class.
class PhysicalReplayError(RuntimeError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Input evidence: the supplied evidence.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code, evidence=None):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set (self.code, self.evidence) to a tuple containing code, evidence.
        self.code, self.evidence = code, evidence


# Execution semantics using the inputs and processing steps below.
# Input branch: the supplied branch.
# Output: a tuple containing plan.ready_vehicle_ids, plan.blocked_vehicle_ids, permissions.
def execution_semantics(branch):
    # Set plan to branch.execution_plan.
    plan = branch.execution_plan
    # Set permissions to a tuple built from the sorted values from a lazy sequence of a tuple containing
    # item.vehicle_id, item.conflict_zone_id, item.permission_status, item.blocking_vehicle_ids for item in
    # plan.vehicle_permissions.
    permissions = tuple(sorted(
        # Evaluate a tuple containing item.vehicle_id, item.conflict_zone_id, item.permission_status,
        # item.blocking_vehicle_ids as part of the enclosing expression.
        (item.vehicle_id, item.conflict_zone_id, item.permission_status,
         # Include item.blocking_vehicle_ids in this tuple.
         item.blocking_vehicle_ids) for item in plan.vehicle_permissions))
    # Return a tuple containing plan.ready_vehicle_ids, plan.blocked_vehicle_ids, permissions to the caller.
    return plan.ready_vehicle_ids, plan.blocked_vehicle_ids, permissions


# Select before replay using identity and execution semantics only.
# Input branches: the supplied branches.
# Output: a tuple containing first, second.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def select_causal_branch_pair(branches):
    """Select before replay using identity and execution semantics only."""
    # Set eligible to a tuple built from the sorted values from a lazy sequence of item for item in branches;
    # retain entries satisfying item.graph_executable.
    eligible = tuple(sorted((item for item in branches if item.graph_executable),
                            # Declare item as input parameter.
                            key=lambda item: item.branch_id))
    # Iterate over the result of combinations(eligible, 2), binding each item to (first, second).
    for first, second in combinations(eligible, 2):
        # Run this branch when first.effective_precedence_graph differs from second.effective_precedence_graph and
        # the result of execution_semantics(first) differs from the result of execution_semantics(second).
        if (first.effective_precedence_graph != second.effective_precedence_graph
                # Evaluate the result of execution_semantics(first) differs from the result of
                # execution_semantics(second) as part of the enclosing expression.
                and execution_semantics(first) != execution_semantics(second)):
            # Return a tuple containing first, second to the caller.
            return first, second
    # Raise PhysicalReplayError with the text 'EXECUTABLE_BRANCH_PAIR_NOT_AVAILABLE' to stop this execution path.
    raise PhysicalReplayError("EXECUTABLE_BRANCH_PAIR_NOT_AVAILABLE")


# Specification using the inputs and processing steps below.
# Input payload: the supplied payload.
# Input scenario_id: the supplied scenario id.
# Output: the result of NegotiationScenarioSpecification(scenario_id, item at 'scenario_family', a tuple built
# from item at 'movement_path_ids', a tuple...).
def _specification(payload, scenario_id):
    # Import as_tuple from joint_negotiation_validation for the operations below.
    from joint_negotiation_validation import as_tuple
    # Set item to the next item from a lazy sequence of value for value in payload at 'scenario_specifications';
    # retain entries satisfying the result of as_tuple(value['scenario_id']) equals scenario_id.
    item = next(value for value in payload["scenario_specifications"]
                # Evaluate the result of as_tuple(value at 'scenario_id') equals scenario_id as part of the
                # enclosing expression.
                if as_tuple(value["scenario_id"]) == scenario_id)
    # Return the result of NegotiationScenarioSpecification(scenario_id, item at 'scenario_family', a tuple built
    # from item at 'movement_path_ids', a tuple...) to the caller.
    return NegotiationScenarioSpecification(
        # Supply a tuple built from item at 'movement_path_ids' to NegotiationScenarioSpecification.
        scenario_id, item["scenario_family"], tuple(item["movement_path_ids"]),
        # Supply a tuple built from item at 'vehicle_roles' to NegotiationScenarioSpecification.
        tuple(item["approach_ids"]), tuple(item["vehicle_roles"]),
        # Supply a tuple built from a lazy sequence of a tuple built from value for value in item at
        # 'expected_regulatory_topology' to NegotiationScenarioSpecification.
        tuple(tuple(value) for value in item["expected_regulatory_topology"]),
        # Supply item at 'expected_negotiation_status' to NegotiationScenarioSpecification.
        item["expected_negotiation_status"], item["synchronization_method"],
        # Supply a tuple built from item at 'scheduled_spawn_steps' to NegotiationScenarioSpecification.
        tuple(item["scheduled_spawn_steps"]), tuple(item["scheduled_spawn_times"]),
        # Supply item at 'vehicle_type_identity' to NegotiationScenarioSpecification.
        item["network_identity"], item["vehicle_type_identity"],
        # Supply item at 'perception_configuration_identity' to NegotiationScenarioSpecification.
        item["regulatory_profile"], item["perception_configuration_identity"],
        # Supply item at 'intention_model_identity' to NegotiationScenarioSpecification.
        item["intention_model_identity"], item["generation_basis"], item["provenance"])


# Build replay specifications using the inputs and processing steps below.
# Input evidence: the supplied evidence.
# Input pair: the supplied pair.
# Output: a tuple containing scenario, a tuple built from result.
# Processing: iterate over the relevant records.
def build_replay_specifications(evidence, pair):
    # Set scenario to the result of _specification(evidence at 'payload', evidence at 'scenario_id').
    scenario = _specification(evidence["payload"], evidence["scenario_id"])
    # Set manifest to evidence['design']['manifests'] at ScenarioRole.TRAINING.
    manifest = evidence["design"]["manifests"][ScenarioRole.TRAINING]
    # Set result to an empty list.
    result = []
    # Iterate over corresponding items paired from a tuple containing the text 'A', the text 'B', pair, binding
    # each item to (label, branch).
    for label, branch in zip(("A", "B"), pair):
        # Set replay_id to a tuple containing the text 'PHYSICAL_BRANCH_REPLAY_V1', scenario.scenario_id, label,
        # branch.branch_id.
        replay_id = ("PHYSICAL_BRANCH_REPLAY_V1", scenario.scenario_id,
                     # Include branch.branch_id in this tuple.
                     label, branch.branch_id)
        # Append the result of PhysicalBranchReplaySpecification(replay_id, scenario.scenario_id,
        # manifest.manifest_id, scenario.scenario_id, branch.branch_id,...) to result.
        result.append(PhysicalBranchReplaySpecification(
            # Supply scenario.scenario_id to PhysicalBranchReplaySpecification.
            replay_id, scenario.scenario_id, manifest.manifest_id,
            # Supply evidence at 'source_snapshot_id' to PhysicalBranchReplaySpecification.
            scenario.scenario_id, branch.branch_id, evidence["source_snapshot_id"],
            # Supply scenario.movement_path_ids to PhysicalBranchReplaySpecification.
            evidence["timestamp"], scenario.movement_path_ids,
            # Supply scenario.scheduled_spawn_steps to PhysicalBranchReplaySpecification.
            scenario.scheduled_spawn_steps, scenario.scheduled_spawn_times,
            # Supply scenario.vehicle_type_identity to PhysicalBranchReplaySpecification.
            scenario.network_identity, scenario.vehicle_type_identity,
            # Supply scenario.perception_configuration_identity to PhysicalBranchReplaySpecification.
            scenario.regulatory_profile, scenario.perception_configuration_identity,
            # Supply scenario.intention_model_identity to PhysicalBranchReplaySpecification.
            scenario.intention_model_identity, SIM_TIME_STEP,
            # Supply EPISODE_DURATION_SECONDS to PhysicalBranchReplaySpecification.
            EPISODE_DURATION_SECONDS, ACTION_SOURCE,
            # Store PAIR_SELECTION_METHOD under 'pair_selection_method'.
            {"pair_selection_method": PAIR_SELECTION_METHOD,
             # Store True under 'pair_selected_before_outcomes'.
             "pair_selected_before_outcomes": True,
             # Store False under 'new_replay_seed'.
             # Store 0 under 'validation_role_executions'.
             "new_replay_seed": False, "validation_role_executions": 0,
             # Store 0 under 'held_out_role_executions'.
             "held_out_role_executions": 0}))
    # Return a tuple containing scenario, a tuple built from result to the caller.
    return scenario, tuple(result)


# Define PhysicalBranchReplayRunner to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class PhysicalBranchReplayRunner:
    # Set COMMAND_ARGUMENTS to a tuple containing the text '-c', a string built from SUMO_CONFIG, the text
    # '--step-length', a string built from...
    COMMAND_ARGUMENTS = (
        # Include a string built from SIM_TIME_STEP in this tuple.
        "-c", str(SUMO_CONFIG), "--step-length", str(SIM_TIME_STEP),
        "--no-step-log", "true", "--collision.action", "warn",
        "--duration-log.disable", "true")

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input evidence: the supplied evidence.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, evidence):
        # Set self.evidence to evidence.
        self.evidence = evidence
        # Set self.paths to the result of MapPathManager().
        self.paths = MapPathManager()
        # Set self.zones to the result of ConflictZoneManager(self.paths).
        self.zones = ConflictZoneManager(self.paths)
        # Set self.planner to the result of ConflictZoneExecutionPlanner(self.paths, self.zones).
        self.planner = ConflictZoneExecutionPlanner(self.paths, self.zones)

    # Run using the inputs and processing steps below.
    # Input replay_specification: the supplied replay specification.
    # Input scenario: the supplied scenario.
    # Output: the result of PhysicalNegotiationBranchReplayTrace(replay_specification.replay_id,
    # scenario.scenario_id, branch.branch_id,...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def run(self, replay_specification, scenario):
        # Run this branch when the text '--random' belongs to self.COMMAND_ARGUMENTS.
        if "--random" in self.COMMAND_ARGUMENTS:
            # Raise PhysicalReplayError with the text 'RANDOMIZED_SUMO_REPLAY_FORBIDDEN' to stop this execution
            # path.
            raise PhysicalReplayError("RANDOMIZED_SUMO_REPLAY_FORBIDDEN")
        # Set environment to the result of SUMOEnv().
        environment = SUMOEnv(use_gui=False)
        # Set observations to the result of ObservationManager().
        observations = ObservationManager()
        # Set entry_monitor to the result of ConflictEntryMonitor().
        entry_monitor = ConflictEntryMonitor()
        # Set predictor to the result of IntentionPredictor().
        predictor = IntentionPredictor()
        # Set graph_manager to the result of ConflictGraphManager(self.paths, self.zones).
        graph_manager = ConflictGraphManager(self.paths, self.zones)
        # Set occupancy to the result of ConflictZoneOccupancyAssessor(self.paths, self.zones).
        occupancy = ConflictZoneOccupancyAssessor(self.paths, self.zones)
        # Set rules to the result of TrafficRuleEngine(self.paths).
        rules = TrafficRuleEngine(self.paths)
        # Set negotiation to the result of NegotiationEnvironment().
        negotiation = NegotiationEnvironment()
        # Set claim_bus to the result of V2VPrecedenceClaimBus().
        claim_bus = V2VPrecedenceClaimBus()
        # Set encoder to the result of GraphTensorEncoder().
        encoder = GraphTensorEncoder()
        # Set ledger to the result of VehicleDemandLedger().
        ledger = VehicleDemandLedger()
        # Set movement_by_vehicle to a dictionary of formatted text built from the embedded values mapped to
        # path_id for (index, path_id) in index/value pairs from scenario.movement_path_ids.
        movement_by_vehicle = {f"SCENARIO_AV_{index}": path_id for index, path_id
                               # Evaluate index/value pairs from scenario.movement_path_ids as part of the
                               # enclosing expression.
                               in enumerate(scenario.movement_path_ids)}
        # Iterate over index/value pairs from scenario.scheduled_spawn_times, binding each item to (index,
        # scheduled).
        for index, scheduled in enumerate(scenario.scheduled_spawn_times):
            # Set vehicle_id to formatted text built from the embedded values.
            vehicle_id = f"SCENARIO_AV_{index}"
            # Call ledger.register_scheduled_vehicle with the supplied arguments.
            ledger.register_scheduled_vehicle(
                # Supply DemandScheduleSource.INITIAL_SIMULATION_DEMAND to ledger.register_scheduled_vehicle.
                vehicle_id, scheduled, DemandScheduleSource.INITIAL_SIMULATION_DEMAND,
                # Store movement_by_vehicle at vehicle_id under 'movement_path_id'.
                {"movement_path_id": movement_by_vehicle[vehicle_id]},
                # Store the text 'FROZEN_NEGOTIATION_SCENARIO_SCHEDULE' under 'source'.
                {"source": "FROZEN_NEGOTIATION_SCENARIO_SCHEDULE"})
        # Set pending to a list built from corresponding items paired from scenario.scheduled_spawn_steps,
        # scenario.movement_path_ids, the integer range defined...
        pending = list(zip(scenario.scheduled_spawn_steps,
                           # Supply the integer range defined by the number of entries in
                           # scenario.movement_path_ids to zip.
                           scenario.movement_path_ids, range(len(scenario.movement_path_ids))))
        # Set branch to None.
        branch = None
        # Set fingerprint to None.
        fingerprint = None
        # Set initial_plan to None.
        initial_plan = None
        # Set (plan_history, constraints, commands, realized) to a tuple containing an empty list, an empty list,
        # an empty list, an empty list.
        plan_history, constraints, commands, realized = [], [], [], []
        # Set (ready_transitions, blocked_transitions) to a tuple containing an empty list, an empty list.
        ready_transitions, blocked_transitions = [], []
        # Set (entry_events, clear_events, completion_events) to a tuple containing an empty list, an empty list,
        # an empty list.
        entry_events, clear_events, completion_events = [], [], []
        # Set (actual_departures, cleared, zone_states) to a tuple containing an empty list, an empty set, an
        # empty dictionary.
        actual_departures, cleared, zone_states = [], set(), {}
        # Set previous_ready and previous_blocked to None.
        previous_ready = previous_blocked = None
        # Set (collision_events, native_interventions) to a tuple containing an empty list, an empty list.
        collision_events, native_interventions = [], []
        # Set (command_audit, command_mode) to a tuple containing an empty dictionary, an empty dictionary.
        command_audit, command_mode = {}, {}
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call environment.start with the supplied arguments.
            environment.start()
            # Set sumo_version to a tuple built from the result of traci.getVersion().
            sumo_version = tuple(traci.getVersion())
            # Set simulation_step to a floating-point number built from the result of
            # traci.simulation.getDeltaT().
            simulation_step = float(traci.simulation.getDeltaT())
            # Run this branch when simulation_step differs from SIM_TIME_STEP.
            if simulation_step != SIM_TIME_STEP:
                # Raise PhysicalReplayError with the text 'SIMULATION_STEP_CONFIGURATION_MISMATCH' to stop this
                # execution path.
                raise PhysicalReplayError("SIMULATION_STEP_CONFIGURATION_MISMATCH")
            # Run this branch when the text '--step-method.ballistic' belongs to self.COMMAND_ARGUMENTS or the
            # text 'step-method.ballistic' belongs to the text read from SUMO_CONFIG.
            if ("--step-method.ballistic" in self.COMMAND_ARGUMENTS or
                    # Evaluate the text 'step-method.ballistic' belongs to the text read from SUMO_CONFIG as part
                    # of the enclosing expression.
                    "step-method.ballistic" in SUMO_CONFIG.read_text(
                        # Supply encoding as the text 'utf-8'.
                        encoding="utf-8")):
                # Raise PhysicalReplayError with the text
                # 'UNEXPECTED_SUMO_INTEGRATION_METHOD_FOR_EULER_CONTROLLER' to stop this execution path.
                raise PhysicalReplayError(
                    "UNEXPECTED_SUMO_INTEGRATION_METHOD_FOR_EULER_CONTROLLER")
            # Set route_by_path to a dictionary of path_id mapped to the result of
            # derive_existing_route_id(self.paths, path_id) for path_id in scenario.movement_path_ids.
            route_by_path = {path_id: derive_existing_route_id(self.paths, path_id)
                             # Evaluate scenario.movement_path_ids as part of the enclosing expression.
                             for path_id in scenario.movement_path_ids}
            # Repeat the following steps while environment.step_count is less than EPISODE_STEPS.
            while environment.step_count < EPISODE_STEPS:
                # Set due to a list of item for item in pending; retain entries satisfying item at 0 is at most
                # environment.step_count.
                due = [item for item in pending if item[0] <= environment.step_count]
                # Iterate over due, binding each item to (_, path_id, index).
                for _, path_id, index in due:
                    # Set vehicle_id to formatted text built from the embedded values.
                    vehicle_id = f"SCENARIO_AV_{index}"
                    # Add vehicle_id to traci.vehicle.
                    traci.vehicle.add(vehicle_id, route_by_path[path_id], AV_TYPE_ID,
                                      # Supply departSpeed as the text 'max'.
                                      # Supply departLane as the text 'free'.
                                      departSpeed="max", departLane="free",
                                      # Supply departPos as the text 'base'.
                                      departPos="base")
                    # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
                    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)
                    # Call observations.get_or_create_ldm with the supplied arguments.
                    observations.get_or_create_ldm(vehicle_id)
                    # Remove a tuple containing _, path_id, index from pending.
                    pending.remove((_, path_id, index))
                # Set states to the result of environment.step().
                states = environment.step()
                # Set now to environment.current_time.
                now = environment.current_time
                # Iterate over a tuple built from key/value pairs from command_audit, binding each item to
                # (vehicle_id, audit).
                for vehicle_id, audit in tuple(command_audit.items()):
                    # Run this branch when vehicle_id does not belong to states.
                    if vehicle_id not in states:
                        # Skip the rest of this loop iteration and process the next item.
                        continue
                    # Set (previous_time, previous_speed, comfortable_deceleration, comfortable_minimum,
                    # requested, mode,... to audit.
                    (previous_time, previous_speed, comfortable_deceleration,
                     # Include comfortable_minimum in this tuple.
                     comfortable_minimum, requested, mode, speed_mode,
                     # Include source_records in this tuple.
                     zone_state, source_records) = audit
                    # Set current_speed to states[vehicle_id] at 'speed'.
                    current_speed = states[vehicle_id]["speed"]
                    # Set actual_acceleration to states[vehicle_id] at 'accel'.
                    actual_acceleration = states[vehicle_id]["accel"]
                    # Run this branch when the result of traci.vehicle.getSpeedMode(vehicle_id) differs from
                    # speed_mode.
                    if traci.vehicle.getSpeedMode(vehicle_id) != speed_mode:
                        # Raise PhysicalReplayError with the text 'SAFE_SUMO_SPEED_MODE_CHANGED' to stop this
                        # execution path.
                        raise PhysicalReplayError("SAFE_SUMO_SPEED_MODE_CHANGED")
                    # Iterate over source_records, binding each item to source_record.
                    for source_record in source_records:
                        # Set index to the result of constraints.index(source_record).
                        index = constraints.index(source_record)
                        # Set constraints[index] to the result of replace(source_record).
                        constraints[index] = replace(
                            # Supply source_record to replace.
                            source_record,
                            # Supply actual_realized_next_speed_mps as current_speed.
                            actual_realized_next_speed_mps=current_speed,
                            # Supply actual_realized_acceleration_mps2 as actual_acceleration.
                            actual_realized_acceleration_mps2=actual_acceleration)
                    # Set realized_deceleration to previous_speed minus current_speed divided by simulation_step.
                    realized_deceleration = (
                        # Evaluate previous_speed minus current_speed as part of the enclosing expression.
                        previous_speed - current_speed) / simulation_step
                    # Run this branch when realized_deceleration is at most comfortable_deceleration.
                    if realized_deceleration <= comfortable_deceleration:
                        # Set classification to the text 'WITHIN_COMFORTABLE_BOUND'.
                        classification = "WITHIN_COMFORTABLE_BOUND"
                    # Run this alternative branch when the preceding branch does not apply.
                    else:
                        # Set classification to the text 'NATIVE_SUMO_SAFETY_INTERVENTION'.
                        classification = "NATIVE_SUMO_SAFETY_INTERVENTION"
                    # Append a tuple containing now, vehicle_id, previous_speed, current_speed,
                    # realized_deceleration, comfortable_deceleration, mode,... to realized.
                    realized.append((now, vehicle_id, previous_speed,
                                     # Include realized_deceleration in this tuple.
                                     current_speed, realized_deceleration,
                                     # Include comfortable_deceleration in this tuple.
                                     comfortable_deceleration, mode, requested,
                                     # Include actual_acceleration in this tuple.
                                     actual_acceleration, speed_mode, zone_state,
                                     # Include classification in this tuple.
                                     classification))
                # Iterate over environment.lifecycle_events.departed_vehicle_ids, binding each item to vehicle_id.
                for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                    # Run this branch when the result of ledger.get_vehicle_record(vehicle_id).
                    if ledger.get_vehicle_record(vehicle_id):
                        # Call ledger.record_actual_departure with the supplied arguments.
                        ledger.record_actual_departure(vehicle_id, now)
                        # Append a tuple containing vehicle_id, now to actual_departures.
                        actual_departures.append((vehicle_id, now))
                # Iterate over environment.lifecycle_events.arrived_vehicle_ids, binding each item to vehicle_id.
                for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                    # Run this branch when the result of ledger.get_vehicle_record(vehicle_id).
                    if ledger.get_vehicle_record(vehicle_id):
                        # Call ledger.record_service_completion with the supplied arguments.
                        ledger.record_service_completion(vehicle_id, now)
                        # Append a tuple containing vehicle_id, now to completion_events.
                        completion_events.append((vehicle_id, now))
                # Set colliding to a tuple built from the sorted values from the result of
                # traci.simulation.getCollidingVehiclesIDList().
                colliding = tuple(sorted(traci.simulation.getCollidingVehiclesIDList()))
                # Run this branch when colliding.
                if colliding:
                    # Append a tuple containing now, colliding to collision_events.
                    collision_events.append((now, colliding))
                    # Raise PhysicalReplayError with the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' to stop
                    # this execution path.
                    raise PhysicalReplayError(
                        "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED",
                        # Supply a tuple built from collision_events to PhysicalReplayError.
                        tuple(collision_events))
                # Set emergency to a tuple built from the sorted values from the result of
                # traci.simulation.getEmergencyStoppingVehiclesIDList().
                emergency = tuple(sorted(
                    # Supply the result of traci.simulation.getEmergencyStoppingVehiclesIDList() to sorted.
                    traci.simulation.getEmergencyStoppingVehiclesIDList()))
                # Run this branch when emergency.
                if emergency:
                    # Append a tuple containing now, the text 'SUMO_EMERGENCY_STOP_EVENT', emergency, a tuple
                    # built from a lazy sequence of a tuple... to native_interventions.
                    native_interventions.append((now, "SUMO_EMERGENCY_STOP_EVENT",
                                                 # Include emergency in this tuple.
                                                 emergency,
                                                 # Include a tuple built from a lazy sequence of a tuple containing item,
                                                 # item from command_mode; use 'RELEASED_TO_SUMO' if absent for item in
                                                 # emergency in this tuple.
                                                 tuple((item, command_mode.get(
                                                     # Supply item to command_mode.get.
                                                     item, "RELEASED_TO_SUMO"))
                                                       # Evaluate emergency as part of the enclosing expression.
                                                       for item in emergency)))
                # Iterate over the sorted values from key/value pairs from states, binding each item to
                # (vehicle_id, state).
                for vehicle_id, state in sorted(states.items()):
                    # Run this branch when state at 'accel' is at most the negative of state at
                    # 'emergency_deceleration_mps2'.
                    if state["accel"] <= -state["emergency_deceleration_mps2"]:
                        # Append a tuple containing now, the text 'ACTUAL_EMERGENCY_DECELERATION_REACHED',
                        # vehicle_id, state at 'accel', state at... to native_interventions.
                        native_interventions.append((
                            # Include now in this tuple.
                            now, "ACTUAL_EMERGENCY_DECELERATION_REACHED",
                            # Include state at 'accel' in this tuple.
                            vehicle_id, state["accel"],
                            # Include state at 'comfortable_deceleration_mps2' in this tuple.
                            state["comfortable_deceleration_mps2"],
                            # Include state at 'emergency_deceleration_mps2' in this tuple.
                            state["emergency_deceleration_mps2"],
                            # Include vehicle_id from command_mode; use the text 'RELEASED_TO_SUMO' if absent in
                            # this tuple.
                            command_mode.get(vehicle_id, "RELEASED_TO_SUMO")))

                # Run this branch when branch is the same object as None.
                if branch is None:
                    # Set context to the result of self._pipeline_step(states, now, observations, entry_monitor,
                    # predictor, graph_manager, occupancy, rules,...).
                    context = self._pipeline_step(
                        # Supply entry_monitor to self._pipeline_step.
                        states, now, observations, entry_monitor, predictor,
                        # Supply graph_manager to self._pipeline_step.
                        graph_manager, occupancy, rules, negotiation, claim_bus, encoder)
                    # Run this branch when now equals replay_specification.source_decision_timestamp.
                    if now == replay_specification.source_decision_timestamp:
                        # Set (branch, fingerprint) to the result of self._reproduce_branch(replay_specification,
                        # scenario, states, environment.step_count, context, movement_by_vehicle).
                        branch, fingerprint = self._reproduce_branch(
                            # Supply environment.step_count to self._reproduce_branch.
                            replay_specification, scenario, states, environment.step_count,
                            # Supply movement_by_vehicle to self._reproduce_branch.
                            context, movement_by_vehicle)
                        # Set initial_plan to branch.execution_plan.
                        initial_plan = branch.execution_plan
                        # Run this branch when initial_plan.graph_status differs from the text 'EXECUTABLE'.
                        if initial_plan.graph_status != "EXECUTABLE":
                            # Raise PhysicalReplayError with the text 'EXPECTED_EXECUTABLE_BRANCH_NOT_EXECUTABLE'
                            # to stop this execution path.
                            raise PhysicalReplayError("EXPECTED_EXECUTABLE_BRANCH_NOT_EXECUTABLE")
                        # Set zone_states to the result of self._zone_definitions(states, movement_by_vehicle,
                        # branch.original_precedence_graph).
                        zone_states = self._zone_definitions(states, movement_by_vehicle,
                                                            # Supply branch.original_precedence_graph to self._zone_definitions.
                                                            branch.original_precedence_graph)
                        # Set (previous_ready, previous_blocked) to a tuple containing an empty tuple, an empty
                        # tuple.
                        previous_ready, previous_blocked = (), ()
                    # Run this branch when now is greater than replay_specification.source_decision_timestamp.
                    elif now > replay_specification.source_decision_timestamp:
                        # Raise PhysicalReplayError with the text 'SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED' to
                        # stop this execution path.
                        raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED")

                # Run this branch when branch is a different object from None.
                if branch is not None:
                    # Set zone_observations to the result of self._observe_zones(states, movement_by_vehicle,
                    # zone_states, now, entry_events, clear_events, cleared).
                    zone_observations = self._observe_zones(
                        # Supply movement_by_vehicle to self._observe_zones.
                        states, movement_by_vehicle, zone_states, now,
                        # Supply entry_events to self._observe_zones.
                        entry_events, clear_events, cleared)
                    # Set active to a tuple built from the sorted values from states.
                    active = tuple(sorted(states))
                    # Set plan to the result of self.planner.plan().
                    plan = self.planner.plan(
                        # Supply source_snapshot_id as replay_specification.source_snapshot_id.
                        source_snapshot_id=replay_specification.source_snapshot_id,
                        # Supply effective_coordination_graph as branch.effective_precedence_graph.
                        effective_coordination_graph=branch.effective_precedence_graph,
                        # Supply active_vehicle_ids as active.
                        active_vehicle_ids=active,
                        # Supply movement_path_by_vehicle as movement_by_vehicle.
                        # Supply timestamp as now.
                        movement_path_by_vehicle=movement_by_vehicle, timestamp=now,
                        # Supply source_protocol_state as branch.branch_status.
                        source_protocol_state=branch.branch_status,
                        # Supply cleared_vehicle_zones as a tuple built from the sorted values from cleared.
                        cleared_vehicle_zones=tuple(sorted(cleared)))
                    # Append a tuple containing now, plan.plan_id, plan.ready_vehicle_ids,
                    # plan.blocked_vehicle_ids to plan_history.
                    plan_history.append((now, plan.plan_id, plan.ready_vehicle_ids,
                                         # Include plan.blocked_vehicle_ids in this tuple.
                                         plan.blocked_vehicle_ids))
                    # Run this branch when plan.ready_vehicle_ids differs from previous_ready.
                    if plan.ready_vehicle_ids != previous_ready:
                        # Append a tuple containing now, plan.ready_vehicle_ids to ready_transitions.
                        ready_transitions.append((now, plan.ready_vehicle_ids))
                        # Set previous_ready to plan.ready_vehicle_ids.
                        previous_ready = plan.ready_vehicle_ids
                    # Run this branch when plan.blocked_vehicle_ids differs from previous_blocked.
                    if plan.blocked_vehicle_ids != previous_blocked:
                        # Append a tuple containing now, plan.blocked_vehicle_ids to blocked_transitions.
                        blocked_transitions.append((now, plan.blocked_vehicle_ids))
                        # Set previous_blocked to plan.blocked_vehicle_ids.
                        previous_blocked = plan.blocked_vehicle_ids
                    # Attempt the enclosed operations and route matching exceptions to the handlers below.
                    try:
                        # Set step_constraints to the result of self._apply_control(plan, states,
                        # zone_observations, now, commands, command_audit, command_mode, simulation_step).
                        step_constraints = self._apply_control(
                            # Supply zone_observations to self._apply_control.
                            plan, states, zone_observations, now, commands,
                            # Supply simulation_step to self._apply_control.
                            command_audit, command_mode, simulation_step)
                    # Handle PhysicalReplayError as error using the recovery steps below.
                    except PhysicalReplayError as error:
                        # Set detail to a dictionary built from error.evidence or an empty dictionary.
                        detail = dict(error.evidence or {})
                        # Update detail with the supplied entries.
                        detail.update({
                            # Store branch.branch_id under 'branch_id'.
                            "branch_id": branch.branch_id,
                            # Store fingerprint under 'pre_branch_fingerprint'.
                            "pre_branch_fingerprint": fingerprint,
                            # Store branch.effective_precedence_graph under 'effective_precedence_graph'.
                            "effective_precedence_graph": branch.effective_precedence_graph,
                            # Store initial_plan.ready_vehicle_ids under 'initial_ready_vehicle_ids'.
                            "initial_ready_vehicle_ids": initial_plan.ready_vehicle_ids,
                            # Store a tuple built from constraints under
                            # 'speed_constraint_records_before_failure'.
                            "speed_constraint_records_before_failure": tuple(constraints),
                            # Store a tuple built from commands under 'speed_command_records_before_failure'.
                            "speed_command_records_before_failure": tuple(commands),
                            # Store a tuple built from entry_events under 'entry_events_before_failure'.
                            "entry_events_before_failure": tuple(entry_events),
                            # Store a tuple built from clear_events under 'clear_events_before_failure'.
                            "clear_events_before_failure": tuple(clear_events),
                            # Store a tuple built from native_interventions under
                            # 'native_sumo_interventions_before_failure'.
                            "native_sumo_interventions_before_failure": tuple(
                                # Supply native_interventions to tuple.
                                native_interventions),
                            # Store a tuple built from realized under 'realized_deceleration_before_failure'.
                            "realized_deceleration_before_failure": tuple(realized),
                        })
                        # Raise PhysicalReplayError with error.code to stop this execution path.
                        raise PhysicalReplayError(error.code, detail) from error
                    # Extend constraints with step_constraints.
                    constraints.extend(step_constraints)
            # Run this branch when branch is the same object as None.
            if branch is None:
                # Raise PhysicalReplayError with the text 'SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED' to stop this
                # execution path.
                raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED")
            # Run this branch when collision_events.
            if collision_events:
                # Raise PhysicalReplayError with the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' to stop this
                # execution path.
                raise PhysicalReplayError("PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED",
                                          # Supply a tuple built from collision_events to PhysicalReplayError.
                                          tuple(collision_events))
            # Set records to the result of ledger.finalize_episode(replay_specification.episode_end_time).
            records = ledger.finalize_episode(replay_specification.episode_end_time)
            # Set measurements to the result of measure_vehicle_travel_times(records,
            # replay_specification.episode_end_time).
            measurements = measure_vehicle_travel_times(
                # Supply replay_specification.episode_end_time to measure_vehicle_travel_times.
                records, replay_specification.episode_end_time)
            # Set team_time to the result of total_team_travel_time_seconds(measurements).
            team_time = total_team_travel_time_seconds(measurements)
            # Set permissions to a tuple built from the sorted values from a lazy sequence of a tuple containing
            # item.vehicle_id, item.conflict_zone_id, item.permission_status, item.blocking_vehicle_ids for item
            # in initial_plan.vehicle_permissions.
            permissions = tuple(sorted(
                # Evaluate a tuple containing item.vehicle_id, item.conflict_zone_id, item.permission_status,
                # item.blocking_vehicle_ids as part of the enclosing expression.
                (item.vehicle_id, item.conflict_zone_id, item.permission_status,
                 # Evaluate initial_plan.vehicle_permissions as part of the enclosing expression.
                 item.blocking_vehicle_ids) for item in initial_plan.vehicle_permissions))
            # Return the result of PhysicalNegotiationBranchReplayTrace(replay_specification.replay_id,
            # scenario.scenario_id, branch.branch_id,...) to the caller.
            return PhysicalNegotiationBranchReplayTrace(
                # Supply replay_specification.replay_id to PhysicalNegotiationBranchReplayTrace.
                replay_specification.replay_id, scenario.scenario_id, branch.branch_id,
                # Supply replay_specification.source_snapshot_id to PhysicalNegotiationBranchReplayTrace.
                replay_specification.source_snapshot_id, fingerprint,
                # Supply branch.effective_precedence_graph to PhysicalNegotiationBranchReplayTrace.
                branch.effective_precedence_graph, initial_plan.plan_id,
                # Supply initial_plan.ready_vehicle_ids to PhysicalNegotiationBranchReplayTrace.
                initial_plan.ready_vehicle_ids, permissions, tuple(plan_history),
                # Supply a tuple built from constraints to PhysicalNegotiationBranchReplayTrace.
                tuple(constraints), tuple(commands), tuple(realized),
                # Supply a tuple built from ready_transitions to PhysicalNegotiationBranchReplayTrace.
                tuple(ready_transitions),
                # Supply a tuple built from blocked_transitions to PhysicalNegotiationBranchReplayTrace.
                tuple(blocked_transitions), tuple(entry_events), tuple(clear_events),
                # Supply a tuple built from a lazy sequence of a tuple containing formatted text built from the
                # embedded values, value for (i, value) in index/value pairs from scenario.scheduled_spawn_times
                # to PhysicalNegotiationBranchReplayTrace.
                tuple(completion_events), tuple((f"SCENARIO_AV_{i}", value)
                    # Evaluate index/value pairs from scenario.scheduled_spawn_times as part of the enclosing
                    # expression.
                    for i, value in enumerate(scenario.scheduled_spawn_times)),
                # Supply replay_specification.episode_end_time to PhysicalNegotiationBranchReplayTrace.
                tuple(actual_departures), replay_specification.episode_end_time,
                # Supply the result of raw_team_reward(team_time) to PhysicalNegotiationBranchReplayTrace.
                team_time, raw_team_reward(team_time), 0, 0,
                # Supply a tuple built from native_interventions to PhysicalNegotiationBranchReplayTrace.
                tuple(native_interventions),
                "NATIVE_SUMO_SAFETY_ACTIVE_NOT_BYPASSED",
                # Supply sumo_version to PhysicalNegotiationBranchReplayTrace.
                "PHYSICAL_BRANCH_REPLAY_COMPLETED", sumo_version,
                # Supply self.COMMAND_ARGUMENTS to PhysicalNegotiationBranchReplayTrace.
                self.COMMAND_ARGUMENTS, ACTION_SOURCE,
                # Store SAFE_SUMO_SPEED_MODE under 'safe_speed_mode'.
                {"safe_speed_mode": SAFE_SUMO_SPEED_MODE,
                 # Store True under 'environment_route_metadata_used'.
                 "environment_route_metadata_used": True,
                 # Store 0 under 'actor_route_truth_fields'.
                 "actor_route_truth_fields": 0,
                 # Store 0 under 'reward_components_added'.
                 "reward_components_added": 0,
                 # Store False under 'new_seed'.
                 "new_seed": False})
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Call environment.close with the supplied arguments.
            environment.close()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Pipeline step using the inputs and processing steps below.
    # Input states: the supplied states.
    # Input now: the time used for this operation.
    # Input observations: the supplied observations.
    # Input entry_monitor: the supplied entry monitor.
    # Input predictor: the supplied predictor.
    # Input graph_manager: the supplied graph manager.
    # Input occupancy: the supplied occupancy.
    # Input rules: the supplied rules.
    # Input negotiation: the supplied negotiation.
    # Input claim_bus: the supplied claim bus.
    # Input encoder: the supplied encoder.
    # Input negotiation_eligible_ids: the supplied negotiation eligible ids.
    # Input movement_protocol: the supplied movement protocol.
    # Output: a tuple built from snapshots.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _pipeline_step(states, now, observations, entry_monitor, predictor,
                       # Declare graph_manager, occupancy, rules, negotiation, claim_bus as input parameters.
                       graph_manager, occupancy, rules, negotiation, claim_bus,
                       # Declare encoder, negotiation_eligible_ids, movement_protocol as input parameters.
                       encoder, negotiation_eligible_ids=None, movement_protocol=None):
        # Update observations with the supplied entries.
        observations.update(states, now)
        # Set truth to a dictionary of vehicle_id mapped to 'route_id' from state; use the text '' if absent for
        # (vehicle_id, state) in key/value pairs from states.
        truth = {vehicle_id: state.get("route_id", "")
                 # Evaluate a tuple containing vehicle_id, state as part of the enclosing expression.
                 for vehicle_id, state in states.items()}
        # Iterate over states, binding each item to ego_id.
        for ego_id in states:
            # Set ldm to the result of observations.get_ldm(ego_id).
            ldm = observations.get_ldm(ego_id)
            # Run this branch when ldm is a different object from None.
            if ldm is not None:
                # Call entry_monitor.update_ldm with the supplied arguments.
                entry_monitor.update_ldm(ldm, now, predictor, truth)
        # Call claim_bus.begin_step with the supplied arguments.
        claim_bus.begin_step(now)
        # Set local to an empty dictionary.
        local = {}
        # Set eligible to a set built from states when negotiation_eligible_ids is the same object as None,
        # otherwise a set built from negotiation_eligible_ids.
        eligible = (set(states) if negotiation_eligible_ids is None
                    # Evaluate a set built from negotiation_eligible_ids as part of the enclosing expression.
                    else set(negotiation_eligible_ids))
        # Run this branch when movement_protocol is a different object from None.
        if movement_protocol is not None:
            # Call movement_protocol.begin_step with the supplied arguments.
            movement_protocol.begin_step(now)
            # Iterate over the sorted values from eligible, binding each item to sender.
            for sender in sorted(eligible):
                # Set sender_ldm to the result of observations.get_ldm(sender).
                sender_ldm = observations.get_ldm(sender)
                # Run this branch when sender_ldm is a different object from None.
                if sender_ldm is not None:
                    # Call movement_protocol.publish with the supplied arguments.
                    movement_protocol.publish(sender, movement_protocol.author(sender_ldm, now))
        # Set reasoning_ldms to an empty dictionary.
        reasoning_ldms = {}
        # Iterate over states, binding each item to ego_id.
        for ego_id in states:
            # Run this branch when ego_id does not belong to eligible.
            if ego_id not in eligible:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set ldm to the result of observations.get_ldm(ego_id).
            ldm = observations.get_ldm(ego_id)
            # Run this branch when ldm is the same object as None or the negation of ldm.in_approach_zone.
            if ldm is None or not ldm.in_approach_zone:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when negotiation_eligible_ids is a different object from None.
            if negotiation_eligible_ids is not None:
                # Preserve full sensor/LDM histories, but trailing traffic is
                # not a negotiation node. Do not fabricate new observations.
                # Import copy for use in this module.
                import copy
                # Set ldm to the result of copy.copy(ldm).
                ldm = copy.copy(ldm)
                # Set ldm.tracks to a dictionary of key mapped to value for (key, value) in key/value pairs from
                # ldm.tracks; retain entries satisfying key belongs to eligible.
                ldm.tracks = {key: value for key, value in ldm.tracks.items()
                              # Evaluate key belongs to eligible as part of the enclosing expression.
                              if key in eligible}
            # Set reasoning_ldms[ego_id] to ldm.
            reasoning_ldms[ego_id] = ldm
            # Set ldm.current_conflict_graph to the result of graph_manager.build_local_graph(ldm, now).
            ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, now)
            # Run this branch when movement_protocol is a different object from None.
            if movement_protocol is not None:
                # Set ldm.current_conflict_graph to the result of movement_protocol.reconcile(ldm,
                # ldm.current_conflict_graph, now).
                ldm.current_conflict_graph = movement_protocol.reconcile(ldm, ldm.current_conflict_graph, now)
            # Set ldm.current_temporal_assessment to the result of occupancy.assess_ldm(ldm, now).
            ldm.current_temporal_assessment = occupancy.assess_ldm(ldm, now)
            # Set ldm.current_regulatory_assessment to the result of rules.assess_ldm(ldm, now).
            ldm.current_regulatory_assessment = rules.assess_ldm(ldm, now)
            # Set (local[ego_id], messages) to the result of negotiation.build_local_claims(ldm, now).
            local[ego_id], messages = negotiation.build_local_claims(ldm, now)
            # Iterate over messages, binding each item to message.
            # Call claim_bus.publish with the supplied arguments.
            for message in messages: claim_bus.publish(message)
        # Call claim_bus.freeze_step with the supplied arguments.
        claim_bus.freeze_step(now)
        # Set snapshots to an empty list.
        snapshots = []
        # Iterate over the sorted values from local, binding each item to ego_id.
        for ego_id in sorted(local):
            # Set ldm to reasoning_ldms at ego_id.
            ldm = reasoning_ldms[ego_id]
            # Set snapshot to the result of negotiation.build_snapshot(ldm, now, the result of
            # claim_bus.current_messages(now), local at ego_id).
            snapshot = negotiation.build_snapshot(
                # Supply receiver_id as ego_id.
                ldm, now, claim_bus.current_messages(now, receiver_id=ego_id),
                # Supply local at ego_id to negotiation.build_snapshot.
                local[ego_id])
            # Run this branch when movement_protocol is a different object from None.
            if movement_protocol is not None:
                # Set snapshot['movement_declaration_errors'] to ldm.current_movement_declaration_errors.
                snapshot["movement_declaration_errors"] = ldm.current_movement_declaration_errors
                # Set snapshot['movement_declaration_protocol'] to movement_protocol.epoch at 0.
                snapshot["movement_declaration_protocol"] = movement_protocol.epoch[0]
                # Run this branch when ldm.current_movement_declaration_errors.
                if ldm.current_movement_declaration_errors:
                    # Set snapshot['negotiation_status'] to the text
                    # 'NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED'.
                    snapshot["negotiation_status"] = "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED"
            # Set ldm.current_encoded_graph_observation to the result of encoder.encode(snapshot at
            # 'graph_observation').
            ldm.current_encoded_graph_observation = encoder.encode(
                # Supply snapshot at 'graph_observation' to encoder.encode.
                snapshot["graph_observation"])
            # Run this branch when negotiation_eligible_ids is a different object from None.
            if negotiation_eligible_ids is not None:
                # Set original_ldm to the result of observations.get_ldm(ego_id).
                original_ldm = observations.get_ldm(ego_id)
                # Iterate over a tuple containing the text 'current_conflict_graph', the text
                # 'current_temporal_assessment', the text..., binding each item to field.
                for field in ("current_conflict_graph", "current_temporal_assessment",
                              "current_regulatory_assessment", "current_negotiation_problem",
                              "current_encoded_graph_observation"):
                    # Call setattr with the supplied arguments.
                    setattr(original_ldm, field, getattr(ldm, field))
            # Append snapshot to snapshots.
            snapshots.append(snapshot)
        # Return a tuple built from snapshots to the caller.
        return tuple(snapshots)

    # Reproduce branch using the inputs and processing steps below.
    # Input specification: the supplied specification.
    # Input scenario: the supplied scenario.
    # Input states: the supplied states.
    # Input step_index: the supplied step index.
    # Input snapshots: the supplied snapshots.
    # Input movements: the supplied movements.
    # Output: a tuple containing branch, fingerprint.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _reproduce_branch(self, specification, scenario, states, step_index,
                          # Declare snapshots, movements as input parameters.
                          snapshots, movements):
        # Set expected to a tuple built from self.evidence at 'edges'.
        expected = tuple(self.evidence["edges"])
        # Set actual_by_edge to an empty dictionary.
        actual_by_edge = {}
        # Iterate over snapshots, binding each item to snapshot.
        for snapshot in snapshots:
            # Iterate over snapshot at 'joint_precedence_edges', binding each item to edge.
            for edge in snapshot["joint_precedence_edges"]:
                # Set key to a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id'.
                key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                # Run this branch when key belongs to a set of a tuple built from item for item in
                # self.evidence['branches'][0].original_precedence_graph.
                if key in {tuple(item) for item in
                           # Evaluate self.evidence['branches'][0].original_precedence_graph as part of the
                           # enclosing expression.
                           self.evidence["branches"][0].original_precedence_graph}:
                    # Set actual_by_edge[key] to edge.
                    actual_by_edge[key] = edge
        # Set expected_graph to self.evidence['branches'][0].original_precedence_graph.
        expected_graph = self.evidence["branches"][0].original_precedence_graph
        # Run this branch when a tuple built from the sorted values from actual_by_edge differs from
        # expected_graph.
        if tuple(sorted(actual_by_edge)) != expected_graph:
            # Raise PhysicalReplayError with the text 'SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED' to stop this
            # execution path.
            raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED",
                                      # Supply a tuple built from the sorted values from actual_by_edge to
                                      # PhysicalReplayError.
                                      tuple(sorted(actual_by_edge)))
        # Set actual_edges to a tuple built from a lazy sequence of actual_by_edge at key for key in the sorted
        # values from actual_by_edge.
        actual_edges = tuple(actual_by_edge[key] for key in sorted(actual_by_edge))
        # Set enumerator to the result of JointNegotiationBranchEnumerator(self.planner).
        enumerator = JointNegotiationBranchEnumerator(self.planner)
        # Set branches to the result of enumerator.enumerate().
        branches = enumerator.enumerate(
            # Supply scenario_id as scenario.scenario_id.
            scenario_id=scenario.scenario_id,
            # Supply source_snapshot_id as specification.source_snapshot_id.
            source_snapshot_id=specification.source_snapshot_id,
            # Supply original_edges as actual_edges.
            # Supply active_vehicle_ids as a tuple built from the sorted values from states.
            original_edges=actual_edges, active_vehicle_ids=tuple(sorted(states)),
            # Supply timestamp as specification.source_decision_timestamp.
            timestamp=specification.source_decision_timestamp,
            # Supply regulatory_profile as scenario.regulatory_profile.
            regulatory_profile=scenario.regulatory_profile,
            # Supply negotiation_status as scenario.expected_negotiation_status.
            negotiation_status=scenario.expected_negotiation_status,
            # Supply movement_path_by_vehicle as movements.
            movement_path_by_vehicle=movements)
        # Set branch to the next item from a lazy sequence of item for item in branches; retain entries satisfying
        # item.branch_id equals specification.branch_id.
        branch = next((item for item in branches
                       # Evaluate item.branch_id equals specification.branch_id as part of the enclosing
                       # expression.
                       if item.branch_id == specification.branch_id), None)
        # Run this branch when branch is the same object as None.
        if branch is None:
            # Raise PhysicalReplayError with the text 'FROZEN_JOINT_BRANCH_NOT_REPRODUCED' to stop this execution
            # path.
            raise PhysicalReplayError("FROZEN_JOINT_BRANCH_NOT_REPRODUCED")
        # Set factors to the result of enumerator.eligible_factors().
        factors = enumerator.eligible_factors(
            # Supply active_vehicle_ids as a tuple built from the sorted values from states.
            # Supply original_edges as actual_edges.
            active_vehicle_ids=tuple(sorted(states)), original_edges=actual_edges,
            # Supply negotiation_status as scenario.expected_negotiation_status.
            negotiation_status=scenario.expected_negotiation_status)
        # Set fingerprint to the result of PreBranchPhysicalStateFingerprint(scenario.scenario_id,
        # specification.source_decision_timestamp, step_index, a tuple built from...).
        fingerprint = PreBranchPhysicalStateFingerprint(
            # Supply specification.source_decision_timestamp to PreBranchPhysicalStateFingerprint.
            scenario.scenario_id, specification.source_decision_timestamp,
            # Supply a tuple built from the sorted values from states to PreBranchPhysicalStateFingerprint.
            step_index, tuple(sorted(states)),
            # Supply a tuple built from a lazy sequence of a tuple containing vehicle_id, state['position'] at 0,
            # state['position'] at 1, state at 'speed', state at 'accel', state at... for (vehicle_id, state) in
            # the sorted values from key/value pairs from states to PreBranchPhysicalStateFingerprint.
            tuple((vehicle_id, state["position"][0], state["position"][1],
                   # Include state at 'lane_id' in this tuple.
                   state["speed"], state["accel"], state["lane_id"],
                   # Include state at 'lane_position' in this tuple.
                   state["lane_position"], state["road_id"], state["length"],
                   # Include state at 'max_acceleration_mps2' in this tuple.
                   state["width"], state["max_acceleration_mps2"],
                   # Include state at 'comfortable_deceleration_mps2' in this tuple.
                   state["comfortable_deceleration_mps2"],
                   # Include state at 'emergency_deceleration_mps2' in this tuple.
                   state["emergency_deceleration_mps2"], state["max_speed_mps"])
                  # Evaluate the sorted values from key/value pairs from states as part of the enclosing
                  # expression.
                  for vehicle_id, state in sorted(states.items())),
            # Supply specification.source_snapshot_id to PreBranchPhysicalStateFingerprint.
            expected_graph, specification.source_snapshot_id,
            # Supply a tuple built from a lazy sequence of a tuple containing item[0].yielding_vehicle_id,
            # item[0].priority_vehicle_id for item in factors to PreBranchPhysicalStateFingerprint.
            tuple((item[0].yielding_vehicle_id, item[0].priority_vehicle_id)
                  # Evaluate factors as part of the enclosing expression.
                  for item in factors),
            # Supply a tuple built from a lazy sequence of a tuple containing a tuple containing
            # item[0].yielding_vehicle_id, item[0].priority_vehicle_id, a tuple built from... for item in factors
            # to PreBranchPhysicalStateFingerprint.
            tuple(((item[0].yielding_vehicle_id, item[0].priority_vehicle_id),
                   # Include a tuple built from item[1].feasibility in this tuple.
                   tuple(item[1].feasibility)) for item in factors),
            # Supply scenario.regulatory_profile to PreBranchPhysicalStateFingerprint.
            scenario.regulatory_profile, scenario.network_identity)
        # Return a tuple containing branch, fingerprint to the caller.
        return branch, fingerprint

    # Zone definitions using the inputs and processing steps below.
    # Input states: the supplied states.
    # Input movements: the supplied movements.
    # Input original_graph: the supplied original graph.
    # Output: definitions.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _zone_definitions(self, states, movements, original_graph):
        # Set definitions to an empty dictionary.
        definitions = {}
        # Iterate over original_graph, binding each item to (yielding, priority).
        for yielding, priority in original_graph:
            # Set (first, second) to a tuple containing movements at yielding, movements at priority.
            first, second = movements[yielding], movements[priority]
            # Set record to the result of self.zones.zone_record(first, states[yielding] at 'width', second,
            # states[priority] at 'width').
            record = self.zones.zone_record(
                # Supply states[yielding] at 'width' to self.zones.zone_record.
                first, states[yielding]["width"], second, states[priority]["width"])
            # Run this branch when record is the same object as None.
            if record is None:
                # Raise PhysicalReplayError with the text 'EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED' to stop
                # this execution path.
                raise PhysicalReplayError("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED")
            # Set definitions[yielding, record['zone_id']] to a tuple containing first, record at
            # 'first_path_distance_interval'.
            definitions[(yielding, record["zone_id"])] = (
                # Include record at 'first_path_distance_interval' in this tuple.
                first, record["first_path_distance_interval"])
            # Set definitions[priority, record['zone_id']] to a tuple containing second, record at
            # 'second_path_distance_interval'.
            definitions[(priority, record["zone_id"])] = (
                # Include record at 'second_path_distance_interval' in this tuple.
                second, record["second_path_distance_interval"])
        # Return definitions to the caller.
        return definitions

    # Observe zones using the inputs and processing steps below.
    # Input states: the supplied states.
    # Input movements: the supplied movements.
    # Input definitions: the supplied definitions.
    # Input now: the time used for this operation.
    # Input entry_events: the supplied entry events.
    # Input clear_events: the supplied clear events.
    # Input cleared: the supplied cleared.
    # Output: observations.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _observe_zones(self, states, movements, definitions, now,
                       # Declare entry_events, clear_events, cleared as input parameters.
                       entry_events, clear_events, cleared):
        # Set observations to an empty dictionary.
        observations = {}
        # Iterate over key/value pairs from definitions, binding each item to (key, (path_id, interval)).
        for key, (path_id, interval) in definitions.items():
            # Set (vehicle_id, zone_id) to key.
            vehicle_id, zone_id = key
            # Set state to vehicle_id from states; use None if absent.
            state = states.get(vehicle_id)
            # Run this branch when state is the same object as None.
            if state is None:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set (progress, _, error) to the result of self.paths.resolve_front_bumper_path_progress(state,
            # self.paths.paths at path_id).
            progress, _, error = self.paths.resolve_front_bumper_path_progress(
                # Supply self.paths.paths at path_id to self.paths.resolve_front_bumper_path_progress.
                state, self.paths.paths[path_id])
            # Run this branch when error.
            if error:
                # Raise PhysicalReplayError with error to stop this execution path.
                raise PhysicalReplayError(error, (vehicle_id, zone_id, now))
            # Set (occupancy_state, error) to the result of
            # ConflictZoneOccupancyAssessor.occupancy_state(progress, interval, state at 'length').
            occupancy_state, error = ConflictZoneOccupancyAssessor.occupancy_state(
                # Supply state at 'length' to ConflictZoneOccupancyAssessor.occupancy_state.
                progress, interval, state["length"])
            # Run this branch when error.
            # Raise PhysicalReplayError with error to stop this execution path.
            if error: raise PhysicalReplayError(error)
            # Set previous to key from observations; use None if absent.
            previous = observations.get(key)
            # Set observations[key] to a dictionary containing state, progress, distance_to_entry,
            # distance_to_clear.
            observations[key] = {
                # Store occupancy_state under 'state'.
                # Store progress under 'progress'.
                "state": occupancy_state, "progress": progress,
                # Store the maximum of 0.0, interval at 0 minus progress under 'distance_to_entry'.
                "distance_to_entry": max(0.0, interval[0] - progress),
                # Store the maximum of 0.0, interval at 1 plus state at 'length' minus progress under
                # 'distance_to_clear'.
                "distance_to_clear": max(0.0, interval[1] + state["length"] - progress)}
            # Set marker to the requested attribute of self.
            marker = getattr(self, "_active_zone_markers", None)
            # Run this branch when marker is the same object as None.
            if marker is None:
                # Set marker and self._active_zone_markers to an empty dictionary.
                marker = self._active_zone_markers = {}
            # Set prior to key from marker; use the text 'BEFORE_ZONE' if absent.
            prior = marker.get(key, "BEFORE_ZONE")
            # Run this branch when occupancy_state equals the text 'CURRENTLY_OCCUPYING' and prior equals the text
            # 'BEFORE_ZONE'.
            if occupancy_state == "CURRENTLY_OCCUPYING" and prior == "BEFORE_ZONE":
                # Append a tuple containing now, vehicle_id, zone_id, progress to entry_events.
                entry_events.append((now, vehicle_id, zone_id, progress))
            # Run this branch when occupancy_state equals the text 'CLEARED_ZONE' and prior differs from the text
            # 'CLEARED_ZONE'.
            if occupancy_state == "CLEARED_ZONE" and prior != "CLEARED_ZONE":
                # Append a tuple containing now, vehicle_id, zone_id, progress to clear_events.
                clear_events.append((now, vehicle_id, zone_id, progress))
                # Add a tuple containing vehicle_id, zone_id to cleared.
                cleared.add((vehicle_id, zone_id))
            # Set marker[key] to occupancy_state.
            marker[key] = occupancy_state
        # Return observations to the caller.
        return observations

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Apply control using the inputs and processing steps below.
    # Input plan: the supplied plan.
    # Input states: the supplied states.
    # Input zone_observations: the supplied zone observations.
    # Input now: the time used for this operation.
    # Input command_records: the supplied command records.
    # Input command_audit: the supplied command audit.
    # Input command_mode: the supplied command mode.
    # Input simulation_step: the supplied simulation step.
    # Output: a tuple built from records.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def _apply_control(plan, states, zone_observations, now, command_records,
                       # Declare command_audit, command_mode, simulation_step as input parameters.
                       command_audit, command_mode, simulation_step):
        # Set (by_vehicle, records) to a tuple containing an empty dictionary, an empty list.
        by_vehicle, records = {}, []
        # Set blocked_permissions to a set of a tuple containing item.vehicle_id, item.conflict_zone_id for item
        # in plan.vehicle_permissions; retain entries satisfying item.permission_status equals the text
        # 'BLOCKED_BY_PRECEDENCE'.
        blocked_permissions = {(item.vehicle_id, item.conflict_zone_id)
                               # Evaluate plan.vehicle_permissions as part of the enclosing expression.
                               for item in plan.vehicle_permissions
                               # Evaluate item.permission_status equals the text 'BLOCKED_BY_PRECEDENCE' as part
                               # of the enclosing expression.
                               if item.permission_status == "BLOCKED_BY_PRECEDENCE"}
        # Iterate over the sorted values from blocked_permissions, binding each item to (vehicle_id, zone_id).
        for vehicle_id, zone_id in sorted(blocked_permissions):
            # Set evidence to zone_observations at (vehicle_id, zone_id).
            evidence = zone_observations[(vehicle_id, zone_id)]
            # Run this branch when evidence at 'state' differs from the text 'BEFORE_ZONE'.
            if evidence["state"] != "BEFORE_ZONE":
                # Raise PhysicalReplayError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this
                # execution path.
                raise PhysicalReplayError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
                                          # Supply a tuple containing vehicle_id, zone_id, now to
                                          # PhysicalReplayError.
                                          (vehicle_id, zone_id, now))
            # Set state to states at vehicle_id.
            state = states[vehicle_id]
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set speed_mode to an integer built from the result of traci.vehicle.getSpeedMode(vehicle_id).
                speed_mode = int(traci.vehicle.getSpeedMode(vehicle_id))
                # Run this branch when speed_mode differs from SAFE_SUMO_SPEED_MODE.
                if speed_mode != SAFE_SUMO_SPEED_MODE:
                    # Raise PhysicalReplayError with the text 'SAFE_SUMO_SPEED_MODE_CHANGED' to stop this
                    # execution path.
                    raise PhysicalReplayError("SAFE_SUMO_SPEED_MODE_CHANGED")
                # Set enforcement to the result of speed_mode_enforcement(speed_mode).
                enforcement = speed_mode_enforcement(speed_mode)
                # Run this branch when the negation of whether every item is true in values from enforcement.
                if not all(enforcement.values()):
                    # Raise PhysicalReplayError with the text 'SUMO_SPEED_MODE_REQUIRED_ENFORCEMENT_DISABLED' to
                    # stop this execution path.
                    raise PhysicalReplayError(
                        "SUMO_SPEED_MODE_REQUIRED_ENFORCEMENT_DISABLED",
                        # Supply enforcement to PhysicalReplayError.
                        enforcement)
                # Set action_step to a floating-point number built from the result of
                # traci.vehicle.getActionStepLength(vehicle_id).
                action_step = float(traci.vehicle.getActionStepLength(vehicle_id))
                # Set sumo_stop_speed to a floating-point number built from the result of
                # traci.vehicle.getStopSpeed(vehicle_id, state at 'speed', evidence at 'distance_to_entry').
                sumo_stop_speed = float(traci.vehicle.getStopSpeed(
                    # Supply evidence at 'distance_to_entry' to traci.vehicle.getStopSpeed.
                    vehicle_id, state["speed"], evidence["distance_to_entry"]))
                # Set native_speed to a floating-point number built from the result of
                # traci.vehicle.getSpeedWithoutTraCI(vehicle_id).
                native_speed = float(
                    # Supply the result of traci.vehicle.getSpeedWithoutTraCI(vehicle_id) to float.
                    traci.vehicle.getSpeedWithoutTraCI(vehicle_id))
                # Set record to the result of build_sumo_native_speed_constraint(vehicle_id, zone_id, evidence at
                # 'distance_to_entry', state at 'comfortable_deceleration_mps2',...).
                record = build_sumo_native_speed_constraint(
                    # Supply evidence at 'distance_to_entry' to build_sumo_native_speed_constraint.
                    vehicle_id, zone_id, evidence["distance_to_entry"],
                    # Supply state at 'comfortable_deceleration_mps2' to build_sumo_native_speed_constraint.
                    state["comfortable_deceleration_mps2"], state["speed"],
                    # Supply simulation_step to build_sumo_native_speed_constraint.
                    simulation_step, action_step, sumo_stop_speed, native_speed,
                    # Supply speed_mode to build_sumo_native_speed_constraint.
                    speed_mode)
            # Handle ExecutionConstraintError as error using the recovery steps below.
            except ExecutionConstraintError as error:
                # Raise PhysicalReplayError with error.args at 0 to stop this execution path.
                raise PhysicalReplayError(error.args[0], {
                    # Store now under 'timestamp'.
                    # Store vehicle_id under 'vehicle_id'.
                    "timestamp": now, "vehicle_id": vehicle_id,
                    # Store zone_id under 'conflict_zone_id'.
                    "conflict_zone_id": zone_id,
                    # Store state at 'speed' under 'current_speed_mps'.
                    "current_speed_mps": state["speed"],
                    # Store evidence at 'distance_to_entry' under 'distance_to_zone_entry_m'.
                    "distance_to_zone_entry_m": evidence["distance_to_entry"],
                    # Store state at 'comfortable_deceleration_mps2' under 'comfortable_deceleration_mps2'.
                    "comfortable_deceleration_mps2": state[
                        "comfortable_deceleration_mps2"],
                    # Store state at 'emergency_deceleration_mps2' under 'emergency_deceleration_mps2'.
                    "emergency_deceleration_mps2": state[
                        "emergency_deceleration_mps2"],
                    # Store state at 'max_acceleration_mps2' under 'max_acceleration_mps2'.
                    "max_acceleration_mps2": state["max_acceleration_mps2"],
                    # Store state at 'max_speed_mps' under 'max_speed_mps'.
                    "max_speed_mps": state["max_speed_mps"],
                    # Store simulation_step under 'simulation_step_seconds'.
                    "simulation_step_seconds": simulation_step,
                    # Store action_step under 'action_step_length_seconds'.
                    "action_step_length_seconds": action_step,
                    # Store sumo_stop_speed under 'sumo_stop_speed_mps'.
                    "sumo_stop_speed_mps": sumo_stop_speed,
                    # Store native_speed under 'native_sumo_speed_without_traci_mps'.
                    "native_sumo_speed_without_traci_mps": native_speed,
                    # Store the maximum of 0.0, state at 'speed' minus state at 'comfortable_deceleration_mps2'
                    # multiplied by simulation_step under 'comfortable_min_next_speed_mps'.
                    "comfortable_min_next_speed_mps": max(
                        # Supply state at 'speed' minus state at 'comfortable_deceleration_mps2' multiplied by
                        # simulation_step to max.
                        0.0, state["speed"] -
                        # Evaluate state at 'comfortable_deceleration_mps2' multiplied by simulation_step as part
                        # of the enclosing expression.
                        state["comfortable_deceleration_mps2"] *
                        # Evaluate simulation_step as part of the enclosing expression.
                        simulation_step),
                # Evaluate error as part of the enclosing expression.
                }) from error
            # Append the result of replace(record) to records.
            records.append(replace(record, provenance={
                # Store the result of repr(now) under 'timestamp'.
                **dict(record.provenance), "timestamp": repr(now)}))
            # Append record.requested_speed_cap_mps to by_vehicle.setdefault(vehicle_id, []).
            by_vehicle.setdefault(vehicle_id, []).append(record.requested_speed_cap_mps)
        # Iterate over the sorted values from states, binding each item to vehicle_id.
        for vehicle_id in sorted(states):
            # Run this branch when vehicle_id belongs to by_vehicle.
            if vehicle_id in by_vehicle:
                # Set cap to the minimum of by_vehicle at vehicle_id.
                cap = min(by_vehicle[vehicle_id])
                # Set speed_mode to an integer built from the result of traci.vehicle.getSpeedMode(vehicle_id).
                speed_mode = int(traci.vehicle.getSpeedMode(vehicle_id))
                # Run this branch when speed_mode differs from SAFE_SUMO_SPEED_MODE.
                if speed_mode != SAFE_SUMO_SPEED_MODE:
                    # Raise PhysicalReplayError with the text 'SAFE_SUMO_SPEED_MODE_CHANGED' to stop this
                    # execution path.
                    raise PhysicalReplayError("SAFE_SUMO_SPEED_MODE_CHANGED")
                # Request the specified SUMO speed using traci.vehicle.setSpeed.
                traci.vehicle.setSpeed(vehicle_id, cap)
                # Append a tuple containing now, vehicle_id, the text 'PRECEDENCE_SPEED_CAP', cap to
                # command_records.
                command_records.append((now, vehicle_id, "PRECEDENCE_SPEED_CAP", cap))
                # Set governing to the minimum of a lazy sequence of item for item in records; retain entries
                # satisfying item.vehicle_id equals...
                governing = min(
                    # Supply a lazy sequence of item for item in records; retain entries satisfying
                    # item.vehicle_id equals vehicle_id to min.
                    (item for item in records if item.vehicle_id == vehicle_id),
                    # Declare item as input parameter.
                    key=lambda item: item.requested_precedence_speed_mps)
                # Set command_audit[vehicle_id] to a tuple containing now, states[vehicle_id] at 'speed',
                # states[vehicle_id] at 'comfortable_deceleration_mps2',...
                command_audit[vehicle_id] = (
                    # Include states[vehicle_id] at 'speed' in this tuple.
                    now, states[vehicle_id]["speed"],
                    # Include states[vehicle_id] at 'comfortable_deceleration_mps2' in this tuple.
                    states[vehicle_id]["comfortable_deceleration_mps2"],
                    # Include governing.comfortable_min_next_speed_mps in this tuple.
                    governing.comfortable_min_next_speed_mps, cap,
                    # Include speed_mode in this tuple.
                    "PRECEDENCE_SPEED_CAP", speed_mode, "BEFORE_ZONE",
                    # Include a tuple built from a lazy sequence of item for item in records; retain entries
                    # satisfying item.vehicle_id equals vehicle_id in this tuple.
                    tuple(item for item in records
                          # Evaluate item.vehicle_id equals vehicle_id as part of the enclosing expression.
                          if item.vehicle_id == vehicle_id))
                # Set command_mode[vehicle_id] to the text 'PRECEDENCE_CONSTRAINED'.
                command_mode[vehicle_id] = "PRECEDENCE_CONSTRAINED"
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Request the specified SUMO speed using traci.vehicle.setSpeed.
                traci.vehicle.setSpeed(vehicle_id, -1.0)
                # Append a tuple containing now, vehicle_id, the text 'RELEASE_TO_SUMO', the negative of 1.0 to
                # command_records.
                command_records.append((now, vehicle_id, "RELEASE_TO_SUMO", -1.0))
                # Set state to states at vehicle_id.
                state = states[vehicle_id]
                # Set command_audit[vehicle_id] to a tuple containing now, state at 'speed', state at
                # 'comfortable_deceleration_mps2', the maximum of 0.0, state at 'speed'...
                command_audit[vehicle_id] = (
                    # Include state at 'speed' in this tuple.
                    now, state["speed"],
                    # Include state at 'comfortable_deceleration_mps2' in this tuple.
                    state["comfortable_deceleration_mps2"],
                    # Include the maximum of 0.0, state at 'speed' minus state at 'comfortable_deceleration_mps2'
                    # multiplied by simulation_step in this tuple.
                    max(0.0, state["speed"] -
                    # Evaluate state at 'comfortable_deceleration_mps2' multiplied by simulation_step as part of
                    # the enclosing expression.
                    state["comfortable_deceleration_mps2"] * simulation_step),
                    # Include the negative of 1.0 in this tuple.
                    -1.0, "RELEASE_TO_SUMO",
                    # Include an integer built from the result of traci.vehicle.getSpeedMode(vehicle_id) in this
                    # tuple.
                    int(traci.vehicle.getSpeedMode(vehicle_id)),
                    # Include an empty tuple in this tuple.
                    "NOT_PRECEDENCE_BLOCKED", ())
                # Set command_mode[vehicle_id] to the text 'RELEASED_TO_SUMO'.
                command_mode[vehicle_id] = "RELEASED_TO_SUMO"
            # Run this branch when the result of traci.vehicle.getSpeedMode(vehicle_id) differs from
            # SAFE_SUMO_SPEED_MODE.
            if traci.vehicle.getSpeedMode(vehicle_id) != SAFE_SUMO_SPEED_MODE:
                # Raise PhysicalReplayError with the text 'SAFE_SUMO_SPEED_MODE_CHANGED' to stop this execution
                # path.
                raise PhysicalReplayError("SAFE_SUMO_SPEED_MODE_CHANGED")
        # Return a tuple built from records to the caller.
        return tuple(records)


# Run identical condition replays using the inputs and processing steps below.
# Input evidence: the supplied evidence.
# Output: a tuple containing pair, specifications, a tuple containing first, second.
# Processing: select branches using the stated conditions.
def run_identical_condition_replays(evidence):
    # Set pair to the result of select_causal_branch_pair(evidence at 'branches').
    pair = select_causal_branch_pair(evidence["branches"])
    # Set (scenario, specifications) to the result of build_replay_specifications(evidence, pair).
    scenario, specifications = build_replay_specifications(evidence, pair)
    # Set runner to the result of PhysicalBranchReplayRunner(evidence).
    runner = PhysicalBranchReplayRunner(evidence)
    # Set first to the result of runner.run(specifications at 0, scenario).
    first = runner.run(specifications[0], scenario)
    # A new runner prevents zone-marker or other branch-local state leakage.
    # Set second to the result of PhysicalBranchReplayRunner(evidence).run(specifications at 1, scenario).
    second = PhysicalBranchReplayRunner(evidence).run(specifications[1], scenario)
    # Run this branch when first.pre_branch_state_fingerprint differs from second.pre_branch_state_fingerprint.
    if first.pre_branch_state_fingerprint != second.pre_branch_state_fingerprint:
        # Raise PhysicalReplayError with the text 'IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH' to
        # stop this execution path.
        raise PhysicalReplayError(
            "IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH")
    # Return a tuple containing pair, specifications, a tuple containing first, second to the caller.
    return pair, specifications, (first, second)
