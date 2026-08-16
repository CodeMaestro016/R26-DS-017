"""Dedicated real-SUMO replay for negotiation-to-traffic causal validation."""

from dataclasses import replace
from itertools import combinations

import traci

from config import (AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS,
                    SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG)
from conflict import (ConflictGraphManager, ConflictZoneManager,
                      ConflictZoneOccupancyAssessor, MapPathManager)
from conflict_entry_monitor import ConflictEntryMonitor
from environment import SUMOEnv
from experimentation import ScenarioRole
from negotiation_learning import (GraphTensorEncoder,
    JointNegotiationBranchEnumerator, NegotiationEnvironment,
    V2VPrecedenceClaimBus)
from negotiation_objective import (measure_vehicle_travel_times,
    raw_team_reward, total_team_travel_time_seconds)
from negotiation_scenarios.models import NegotiationScenarioSpecification
from negotiation_scenarios.runner import derive_existing_route_id
from observation import ObservationManager
from predictor import IntentionPredictor
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger
from traffic_rules import TrafficRuleEngine

from .controller import (ExecutionConstraintError,
                         build_sumo_native_speed_constraint)
from .planner import ConflictZoneExecutionPlanner
from .replay_models import (ACTION_SOURCE, PhysicalBranchReplaySpecification,
    PhysicalNegotiationBranchReplayTrace, PreBranchPhysicalStateFingerprint)


PAIR_SELECTION_METHOD = (
    "FIRST_CANONICAL_EXECUTABLE_PAIR_WITH_DIFFERENT_EXECUTION_SEMANTICS")


class PhysicalReplayError(RuntimeError):
    def __init__(self, code, evidence=None):
        super().__init__(code)
        self.code, self.evidence = code, evidence


def execution_semantics(branch):
    plan = branch.execution_plan
    permissions = tuple(sorted(
        (item.vehicle_id, item.conflict_zone_id, item.permission_status,
         item.blocking_vehicle_ids) for item in plan.vehicle_permissions))
    return plan.ready_vehicle_ids, plan.blocked_vehicle_ids, permissions


def select_causal_branch_pair(branches):
    """Select before replay using identity and execution semantics only."""
    eligible = tuple(sorted((item for item in branches if item.graph_executable),
                            key=lambda item: item.branch_id))
    for first, second in combinations(eligible, 2):
        if (first.effective_precedence_graph != second.effective_precedence_graph
                and execution_semantics(first) != execution_semantics(second)):
            return first, second
    raise PhysicalReplayError("EXECUTABLE_BRANCH_PAIR_NOT_AVAILABLE")


def _specification(payload, scenario_id):
    from joint_negotiation_validation import as_tuple
    item = next(value for value in payload["scenario_specifications"]
                if as_tuple(value["scenario_id"]) == scenario_id)
    return NegotiationScenarioSpecification(
        scenario_id, item["scenario_family"], tuple(item["movement_path_ids"]),
        tuple(item["approach_ids"]), tuple(item["vehicle_roles"]),
        tuple(tuple(value) for value in item["expected_regulatory_topology"]),
        item["expected_negotiation_status"], item["synchronization_method"],
        tuple(item["scheduled_spawn_steps"]), tuple(item["scheduled_spawn_times"]),
        item["network_identity"], item["vehicle_type_identity"],
        item["regulatory_profile"], item["perception_configuration_identity"],
        item["intention_model_identity"], item["generation_basis"], item["provenance"])


def build_replay_specifications(evidence, pair):
    scenario = _specification(evidence["payload"], evidence["scenario_id"])
    manifest = evidence["design"]["manifests"][ScenarioRole.TRAINING]
    result = []
    for label, branch in zip(("A", "B"), pair):
        replay_id = ("PHYSICAL_BRANCH_REPLAY_V1", scenario.scenario_id,
                     label, branch.branch_id)
        result.append(PhysicalBranchReplaySpecification(
            replay_id, scenario.scenario_id, manifest.manifest_id,
            scenario.scenario_id, branch.branch_id, evidence["source_snapshot_id"],
            evidence["timestamp"], scenario.movement_path_ids,
            scenario.scheduled_spawn_steps, scenario.scheduled_spawn_times,
            scenario.network_identity, scenario.vehicle_type_identity,
            scenario.regulatory_profile, scenario.perception_configuration_identity,
            scenario.intention_model_identity, SIM_TIME_STEP,
            EPISODE_DURATION_SECONDS, ACTION_SOURCE,
            {"pair_selection_method": PAIR_SELECTION_METHOD,
             "pair_selected_before_outcomes": True,
             "new_replay_seed": False, "validation_role_executions": 0,
             "held_out_role_executions": 0}))
    return scenario, tuple(result)


class PhysicalBranchReplayRunner:
    COMMAND_ARGUMENTS = (
        "-c", str(SUMO_CONFIG), "--step-length", str(SIM_TIME_STEP),
        "--no-step-log", "true", "--collision.action", "warn",
        "--duration-log.disable", "true")

    def __init__(self, evidence):
        self.evidence = evidence
        self.paths = MapPathManager()
        self.zones = ConflictZoneManager(self.paths)
        self.planner = ConflictZoneExecutionPlanner(self.paths, self.zones)

    def run(self, replay_specification, scenario):
        if "--random" in self.COMMAND_ARGUMENTS:
            raise PhysicalReplayError("RANDOMIZED_SUMO_REPLAY_FORBIDDEN")
        environment = SUMOEnv(use_gui=False)
        observations = ObservationManager()
        entry_monitor = ConflictEntryMonitor()
        predictor = IntentionPredictor()
        graph_manager = ConflictGraphManager(self.paths, self.zones)
        occupancy = ConflictZoneOccupancyAssessor(self.paths, self.zones)
        rules = TrafficRuleEngine(self.paths)
        negotiation = NegotiationEnvironment()
        claim_bus = V2VPrecedenceClaimBus()
        encoder = GraphTensorEncoder()
        ledger = VehicleDemandLedger()
        movement_by_vehicle = {f"SCENARIO_AV_{index}": path_id for index, path_id
                               in enumerate(scenario.movement_path_ids)}
        for index, scheduled in enumerate(scenario.scheduled_spawn_times):
            vehicle_id = f"SCENARIO_AV_{index}"
            ledger.register_scheduled_vehicle(
                vehicle_id, scheduled, DemandScheduleSource.INITIAL_SIMULATION_DEMAND,
                {"movement_path_id": movement_by_vehicle[vehicle_id]},
                {"source": "FROZEN_NEGOTIATION_SCENARIO_SCHEDULE"})
        pending = list(zip(scenario.scheduled_spawn_steps,
                           scenario.movement_path_ids, range(len(scenario.movement_path_ids))))
        branch = None
        fingerprint = None
        initial_plan = None
        plan_history, constraints, commands, realized = [], [], [], []
        ready_transitions, blocked_transitions = [], []
        entry_events, clear_events, completion_events = [], [], []
        actual_departures, cleared, zone_states = [], set(), {}
        previous_ready = previous_blocked = None
        collision_events, native_interventions = [], []
        command_audit, command_mode = {}, {}
        try:
            environment.start()
            sumo_version = tuple(traci.getVersion())
            simulation_step = float(traci.simulation.getDeltaT())
            if simulation_step != SIM_TIME_STEP:
                raise PhysicalReplayError("SIMULATION_STEP_CONFIGURATION_MISMATCH")
            if ("--step-method.ballistic" in self.COMMAND_ARGUMENTS or
                    "step-method.ballistic" in SUMO_CONFIG.read_text(
                        encoding="utf-8")):
                raise PhysicalReplayError(
                    "UNEXPECTED_SUMO_INTEGRATION_METHOD_FOR_EULER_CONTROLLER")
            route_by_path = {path_id: derive_existing_route_id(self.paths, path_id)
                             for path_id in scenario.movement_path_ids}
            while environment.step_count < EPISODE_STEPS:
                due = [item for item in pending if item[0] <= environment.step_count]
                for _, path_id, index in due:
                    vehicle_id = f"SCENARIO_AV_{index}"
                    traci.vehicle.add(vehicle_id, route_by_path[path_id], AV_TYPE_ID,
                                      departSpeed="max", departLane="free",
                                      departPos="base")
                    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)
                    observations.get_or_create_ldm(vehicle_id)
                    pending.remove((_, path_id, index))
                states = environment.step()
                now = environment.current_time
                for vehicle_id, audit in tuple(command_audit.items()):
                    if vehicle_id not in states:
                        continue
                    (previous_time, previous_speed, comfortable_deceleration,
                     comfortable_minimum, requested, mode) = audit
                    current_speed = states[vehicle_id]["speed"]
                    realized_deceleration = (
                        previous_speed - current_speed) / simulation_step
                    if realized_deceleration <= comfortable_deceleration:
                        classification = "WITHIN_COMFORTABLE_BOUND"
                    elif (mode == "PRECEDENCE_SPEED_CAP" and
                          requested < comfortable_minimum):
                        classification = (
                            "PRECEDENCE_CONTROLLER_COMFORTABLE_BOUND_VIOLATION")
                        raise PhysicalReplayError(
                            "PRECEDENCE_CONTROLLER_REQUIRES_EMERGENCY_DECELERATION",
                            (vehicle_id, previous_time, requested,
                             comfortable_minimum))
                    else:
                        classification = "NATIVE_SUMO_SAFETY_INTERVENTION"
                    realized.append((now, vehicle_id, previous_speed,
                                     current_speed, realized_deceleration,
                                     comfortable_deceleration, mode,
                                     classification))
                for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                    if ledger.get_vehicle_record(vehicle_id):
                        ledger.record_actual_departure(vehicle_id, now)
                        actual_departures.append((vehicle_id, now))
                for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                    if ledger.get_vehicle_record(vehicle_id):
                        ledger.record_service_completion(vehicle_id, now)
                        completion_events.append((vehicle_id, now))
                colliding = tuple(sorted(traci.simulation.getCollidingVehiclesIDList()))
                if colliding:
                    collision_events.append((now, colliding))
                emergency = tuple(sorted(
                    traci.simulation.getEmergencyStoppingVehiclesIDList()))
                if emergency:
                    native_interventions.append((now, "SUMO_EMERGENCY_STOP_EVENT",
                                                 emergency,
                                                 tuple((item, command_mode.get(
                                                     item, "RELEASED_TO_SUMO"))
                                                       for item in emergency)))
                for vehicle_id, state in sorted(states.items()):
                    if state["accel"] <= -state["emergency_deceleration_mps2"]:
                        native_interventions.append((
                            now, "ACTUAL_EMERGENCY_DECELERATION_REACHED",
                            vehicle_id, state["accel"],
                            state["comfortable_deceleration_mps2"],
                            state["emergency_deceleration_mps2"],
                            command_mode.get(vehicle_id, "RELEASED_TO_SUMO")))

                if branch is None:
                    context = self._pipeline_step(
                        states, now, observations, entry_monitor, predictor,
                        graph_manager, occupancy, rules, negotiation, claim_bus, encoder)
                    if now == replay_specification.source_decision_timestamp:
                        branch, fingerprint = self._reproduce_branch(
                            replay_specification, scenario, states, environment.step_count,
                            context, movement_by_vehicle)
                        initial_plan = branch.execution_plan
                        if initial_plan.graph_status != "EXECUTABLE":
                            raise PhysicalReplayError("EXPECTED_EXECUTABLE_BRANCH_NOT_EXECUTABLE")
                        zone_states = self._zone_definitions(states, movement_by_vehicle,
                                                            branch.original_precedence_graph)
                        previous_ready, previous_blocked = (), ()
                    elif now > replay_specification.source_decision_timestamp:
                        raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED")

                if branch is not None:
                    zone_observations = self._observe_zones(
                        states, movement_by_vehicle, zone_states, now,
                        entry_events, clear_events, cleared)
                    active = tuple(sorted(states))
                    plan = self.planner.plan(
                        source_snapshot_id=replay_specification.source_snapshot_id,
                        effective_coordination_graph=branch.effective_precedence_graph,
                        active_vehicle_ids=active,
                        movement_path_by_vehicle=movement_by_vehicle, timestamp=now,
                        source_protocol_state=branch.branch_status,
                        cleared_vehicle_zones=tuple(sorted(cleared)))
                    plan_history.append((now, plan.plan_id, plan.ready_vehicle_ids,
                                         plan.blocked_vehicle_ids))
                    if plan.ready_vehicle_ids != previous_ready:
                        ready_transitions.append((now, plan.ready_vehicle_ids))
                        previous_ready = plan.ready_vehicle_ids
                    if plan.blocked_vehicle_ids != previous_blocked:
                        blocked_transitions.append((now, plan.blocked_vehicle_ids))
                        previous_blocked = plan.blocked_vehicle_ids
                    try:
                        step_constraints = self._apply_control(
                            plan, states, zone_observations, now, commands,
                            command_audit, command_mode, simulation_step)
                    except PhysicalReplayError as error:
                        detail = dict(error.evidence or {})
                        detail.update({
                            "branch_id": branch.branch_id,
                            "pre_branch_fingerprint": fingerprint,
                            "effective_precedence_graph": branch.effective_precedence_graph,
                            "initial_ready_vehicle_ids": initial_plan.ready_vehicle_ids,
                            "speed_constraint_records_before_failure": tuple(constraints),
                            "speed_command_records_before_failure": tuple(commands),
                            "entry_events_before_failure": tuple(entry_events),
                            "clear_events_before_failure": tuple(clear_events),
                            "native_sumo_interventions_before_failure": tuple(
                                native_interventions),
                            "realized_deceleration_before_failure": tuple(realized),
                        })
                        raise PhysicalReplayError(error.code, detail) from error
                    constraints.extend(step_constraints)
            if branch is None:
                raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED")
            if collision_events:
                raise PhysicalReplayError("PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED",
                                          tuple(collision_events))
            records = ledger.finalize_episode(replay_specification.episode_end_time)
            measurements = measure_vehicle_travel_times(
                records, replay_specification.episode_end_time)
            team_time = total_team_travel_time_seconds(measurements)
            permissions = tuple(sorted(
                (item.vehicle_id, item.conflict_zone_id, item.permission_status,
                 item.blocking_vehicle_ids) for item in initial_plan.vehicle_permissions))
            return PhysicalNegotiationBranchReplayTrace(
                replay_specification.replay_id, scenario.scenario_id, branch.branch_id,
                replay_specification.source_snapshot_id, fingerprint,
                branch.effective_precedence_graph, initial_plan.plan_id,
                initial_plan.ready_vehicle_ids, permissions, tuple(plan_history),
                tuple(constraints), tuple(commands), tuple(realized),
                tuple(ready_transitions),
                tuple(blocked_transitions), tuple(entry_events), tuple(clear_events),
                tuple(completion_events), tuple((f"SCENARIO_AV_{i}", value)
                    for i, value in enumerate(scenario.scheduled_spawn_times)),
                tuple(actual_departures), replay_specification.episode_end_time,
                team_time, raw_team_reward(team_time), 0, 0,
                tuple(native_interventions),
                "NATIVE_SUMO_SAFETY_ACTIVE_NOT_BYPASSED",
                "PHYSICAL_BRANCH_REPLAY_COMPLETED", sumo_version,
                self.COMMAND_ARGUMENTS, ACTION_SOURCE,
                {"safe_speed_mode": SAFE_SUMO_SPEED_MODE,
                 "environment_route_metadata_used": True,
                 "actor_route_truth_fields": 0,
                 "reward_components_added": 0,
                 "new_seed": False})
        finally:
            environment.close()

    @staticmethod
    def _pipeline_step(states, now, observations, entry_monitor, predictor,
                       graph_manager, occupancy, rules, negotiation, claim_bus,
                       encoder):
        observations.update(states, now)
        truth = {vehicle_id: state.get("route_id", "")
                 for vehicle_id, state in states.items()}
        for ego_id in states:
            ldm = observations.get_ldm(ego_id)
            if ldm is not None:
                entry_monitor.update_ldm(ldm, now, predictor, truth)
        claim_bus.begin_step(now)
        local = {}
        for ego_id in states:
            ldm = observations.get_ldm(ego_id)
            if ldm is None or not ldm.in_approach_zone:
                continue
            ldm.current_conflict_graph = graph_manager.build_local_graph(ldm, now)
            ldm.current_temporal_assessment = occupancy.assess_ldm(ldm, now)
            ldm.current_regulatory_assessment = rules.assess_ldm(ldm, now)
            local[ego_id], messages = negotiation.build_local_claims(ldm, now)
            for message in messages: claim_bus.publish(message)
        claim_bus.freeze_step(now)
        snapshots = []
        for ego_id in sorted(local):
            ldm = observations.get_ldm(ego_id)
            snapshot = negotiation.build_snapshot(
                ldm, now, claim_bus.current_messages(now, receiver_id=ego_id),
                local[ego_id])
            ldm.current_encoded_graph_observation = encoder.encode(
                snapshot["graph_observation"])
            snapshots.append(snapshot)
        return tuple(snapshots)

    def _reproduce_branch(self, specification, scenario, states, step_index,
                          snapshots, movements):
        expected = tuple(self.evidence["edges"])
        actual_by_edge = {}
        for snapshot in snapshots:
            for edge in snapshot["joint_precedence_edges"]:
                key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                if key in {tuple(item) for item in
                           self.evidence["branches"][0].original_precedence_graph}:
                    actual_by_edge[key] = edge
        expected_graph = self.evidence["branches"][0].original_precedence_graph
        if tuple(sorted(actual_by_edge)) != expected_graph:
            raise PhysicalReplayError("SOURCE_NEGOTIATION_CONTEXT_NOT_REPRODUCED",
                                      tuple(sorted(actual_by_edge)))
        actual_edges = tuple(actual_by_edge[key] for key in sorted(actual_by_edge))
        enumerator = JointNegotiationBranchEnumerator(self.planner)
        branches = enumerator.enumerate(
            scenario_id=scenario.scenario_id,
            source_snapshot_id=specification.source_snapshot_id,
            original_edges=actual_edges, active_vehicle_ids=tuple(sorted(states)),
            timestamp=specification.source_decision_timestamp,
            regulatory_profile=scenario.regulatory_profile,
            negotiation_status=scenario.expected_negotiation_status,
            movement_path_by_vehicle=movements)
        branch = next((item for item in branches
                       if item.branch_id == specification.branch_id), None)
        if branch is None:
            raise PhysicalReplayError("FROZEN_JOINT_BRANCH_NOT_REPRODUCED")
        factors = enumerator.eligible_factors(
            active_vehicle_ids=tuple(sorted(states)), original_edges=actual_edges,
            negotiation_status=scenario.expected_negotiation_status)
        fingerprint = PreBranchPhysicalStateFingerprint(
            scenario.scenario_id, specification.source_decision_timestamp,
            step_index, tuple(sorted(states)),
            tuple((vehicle_id, state["position"][0], state["position"][1],
                   state["speed"], state["accel"], state["lane_id"],
                   state["lane_position"], state["road_id"], state["length"],
                   state["width"], state["max_acceleration_mps2"],
                   state["comfortable_deceleration_mps2"],
                   state["emergency_deceleration_mps2"], state["max_speed_mps"])
                  for vehicle_id, state in sorted(states.items())),
            expected_graph, specification.source_snapshot_id,
            tuple((item[0].yielding_vehicle_id, item[0].priority_vehicle_id)
                  for item in factors),
            tuple(((item[0].yielding_vehicle_id, item[0].priority_vehicle_id),
                   tuple(item[1].feasibility)) for item in factors),
            scenario.regulatory_profile, scenario.network_identity)
        return branch, fingerprint

    def _zone_definitions(self, states, movements, original_graph):
        definitions = {}
        for yielding, priority in original_graph:
            first, second = movements[yielding], movements[priority]
            record = self.zones.zone_record(
                first, states[yielding]["width"], second, states[priority]["width"])
            if record is None:
                raise PhysicalReplayError("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED")
            definitions[(yielding, record["zone_id"])] = (
                first, record["first_path_distance_interval"])
            definitions[(priority, record["zone_id"])] = (
                second, record["second_path_distance_interval"])
        return definitions

    def _observe_zones(self, states, movements, definitions, now,
                       entry_events, clear_events, cleared):
        observations = {}
        for key, (path_id, interval) in definitions.items():
            vehicle_id, zone_id = key
            state = states.get(vehicle_id)
            if state is None:
                continue
            progress, _, error = self.paths.resolve_front_bumper_path_progress(
                state, self.paths.paths[path_id])
            if error:
                raise PhysicalReplayError(error, (vehicle_id, zone_id, now))
            occupancy_state, error = ConflictZoneOccupancyAssessor.occupancy_state(
                progress, interval, state["length"])
            if error: raise PhysicalReplayError(error)
            previous = observations.get(key)
            observations[key] = {
                "state": occupancy_state, "progress": progress,
                "distance_to_entry": max(0.0, interval[0] - progress),
                "distance_to_clear": max(0.0, interval[1] + state["length"] - progress)}
            marker = getattr(self, "_active_zone_markers", None)
            if marker is None:
                marker = self._active_zone_markers = {}
            prior = marker.get(key, "BEFORE_ZONE")
            if occupancy_state == "CURRENTLY_OCCUPYING" and prior == "BEFORE_ZONE":
                entry_events.append((now, vehicle_id, zone_id, progress))
            if occupancy_state == "CLEARED_ZONE" and prior != "CLEARED_ZONE":
                clear_events.append((now, vehicle_id, zone_id, progress))
                cleared.add((vehicle_id, zone_id))
            marker[key] = occupancy_state
        return observations

    @staticmethod
    def _apply_control(plan, states, zone_observations, now, command_records,
                       command_audit, command_mode, simulation_step):
        by_vehicle, records = {}, []
        blocked_permissions = {(item.vehicle_id, item.conflict_zone_id)
                               for item in plan.vehicle_permissions
                               if item.permission_status == "BLOCKED_BY_PRECEDENCE"}
        for vehicle_id, zone_id in sorted(blocked_permissions):
            evidence = zone_observations[(vehicle_id, zone_id)]
            if evidence["state"] != "BEFORE_ZONE":
                raise PhysicalReplayError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
                                          (vehicle_id, zone_id, now))
            state = states[vehicle_id]
            try:
                action_step = float(traci.vehicle.getActionStepLength(vehicle_id))
                sumo_stop_speed = float(traci.vehicle.getStopSpeed(
                    vehicle_id, state["speed"], evidence["distance_to_entry"]))
                native_speed = float(
                    traci.vehicle.getSpeedWithoutTraCI(vehicle_id))
                record = build_sumo_native_speed_constraint(
                    vehicle_id, zone_id, evidence["distance_to_entry"],
                    state["comfortable_deceleration_mps2"], state["speed"],
                    simulation_step, action_step, sumo_stop_speed, native_speed)
            except ExecutionConstraintError as error:
                raise PhysicalReplayError(error.args[0], {
                    "timestamp": now, "vehicle_id": vehicle_id,
                    "conflict_zone_id": zone_id,
                    "current_speed_mps": state["speed"],
                    "distance_to_zone_entry_m": evidence["distance_to_entry"],
                    "comfortable_deceleration_mps2": state[
                        "comfortable_deceleration_mps2"],
                    "emergency_deceleration_mps2": state[
                        "emergency_deceleration_mps2"],
                    "max_acceleration_mps2": state["max_acceleration_mps2"],
                    "max_speed_mps": state["max_speed_mps"],
                    "simulation_step_seconds": simulation_step,
                    "action_step_length_seconds": action_step,
                    "sumo_stop_speed_mps": sumo_stop_speed,
                    "native_sumo_speed_without_traci_mps": native_speed,
                    "comfortable_min_next_speed_mps": max(
                        0.0, state["speed"] -
                        state["comfortable_deceleration_mps2"] *
                        simulation_step),
                }) from error
            records.append(replace(record, provenance={
                **dict(record.provenance), "timestamp": repr(now)}))
            by_vehicle.setdefault(vehicle_id, []).append(record.requested_speed_cap_mps)
        for vehicle_id in sorted(states):
            if vehicle_id in by_vehicle:
                cap = min(by_vehicle[vehicle_id])
                traci.vehicle.setSpeed(vehicle_id, cap)
                command_records.append((now, vehicle_id, "PRECEDENCE_SPEED_CAP", cap))
                governing = min(
                    (item for item in records if item.vehicle_id == vehicle_id),
                    key=lambda item: item.requested_precedence_speed_mps)
                command_audit[vehicle_id] = (
                    now, states[vehicle_id]["speed"],
                    states[vehicle_id]["comfortable_deceleration_mps2"],
                    governing.comfortable_min_next_speed_mps, cap,
                    "PRECEDENCE_SPEED_CAP")
                command_mode[vehicle_id] = "PRECEDENCE_CONSTRAINED"
            else:
                traci.vehicle.setSpeed(vehicle_id, -1.0)
                command_records.append((now, vehicle_id, "RELEASE_TO_SUMO", -1.0))
                state = states[vehicle_id]
                command_audit[vehicle_id] = (
                    now, state["speed"],
                    state["comfortable_deceleration_mps2"],
                    max(0.0, state["speed"] -
                        state["comfortable_deceleration_mps2"] * simulation_step),
                    -1.0, "RELEASE_TO_SUMO")
                command_mode[vehicle_id] = "RELEASED_TO_SUMO"
            if traci.vehicle.getSpeedMode(vehicle_id) != SAFE_SUMO_SPEED_MODE:
                raise PhysicalReplayError("SAFE_SUMO_SPEED_MODE_CHANGED")
        return tuple(records)


def run_identical_condition_replays(evidence):
    pair = select_causal_branch_pair(evidence["branches"])
    scenario, specifications = build_replay_specifications(evidence, pair)
    runner = PhysicalBranchReplayRunner(evidence)
    first = runner.run(specifications[0], scenario)
    # A new runner prevents zone-marker or other branch-local state leakage.
    second = PhysicalBranchReplayRunner(evidence).run(specifications[1], scenario)
    if first.pre_branch_state_fingerprint != second.pre_branch_state_fingerprint:
        raise PhysicalReplayError(
            "IDENTICAL_INITIAL_CONDITION_REPLAY_DIVERGED_BEFORE_BRANCH")
    return pair, specifications, (first, second)
