"""Reusable event-driven SUMO environment for semantic negotiation actions."""

from dataclasses import replace
from time import perf_counter

import traci

from config import (AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS,
                    SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP)
from conflict import (ConflictGraphManager, ConflictZoneManager,
                      ConflictZoneOccupancyAssessor, MapPathManager)
from conflict_entry_monitor import ConflictEntryMonitor
from environment import SUMOEnv
from negotiation_execution import ConflictZoneExecutionPlanner
from negotiation_execution import CoordinationToPhysicalExecutionMapper
from negotiation_execution.replay import (PhysicalBranchReplayRunner,
                                            PhysicalReplayError)
from negotiation_learning import (GraphTensorEncoder,
    JointNegotiationBranchEnumerator, NegotiationEnvironment,
    V2VPrecedenceClaimBus)
from negotiation_learning.semantic_encoding.encoder import PROTOCOL_STATE_COLUMNS
from negotiation_learning.tensor_encoding.schemas import (
    EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA)
from negotiation_objective import (measure_vehicle_travel_times,
    raw_team_reward, total_team_travel_time_seconds)
from negotiation_scenarios.runner import derive_existing_route_id
from observation import ObservationManager
from predictor import IntentionPredictor
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger
from traffic_rules import TrafficRuleEngine

from .models import (CoupledNegotiationDecisionBatch,
                     CoupledNegotiationEpisodeRecord,
                     CoupledPolicyFactorRecord)
from .providers import PROFILING_SOURCE


class CoupledNegotiationTrainingEnvironment:
    """One fresh real-SUMO episode with event-driven semantic policy input."""

    def __init__(self, action_provider, use_gui=False):
        self.action_provider = action_provider
        self.use_gui = bool(use_gui)
        self.paths = MapPathManager()
        self.zones = ConflictZoneManager(self.paths)
        self.planner = ConflictZoneExecutionPlanner(self.paths, self.zones)
        self.physical_mapper = CoordinationToPhysicalExecutionMapper(self.zones)
        self._active_zone_markers = {}

    def reset(self):
        self._active_zone_markers = {}

    def _terminal_coordination_status(self, branch,
                                      negotiation_context_observed,
                                      unresolved_reason):
        """Keep missing semantic events fatal except for an opted-in baseline."""
        if branch is not None:
            return ("UNRESOLVED_COORDINATION_BASELINE" if unresolved_reason
                    else "COMPLETE")
        if (negotiation_context_observed and unresolved_reason and
                getattr(self.action_provider,
                        "allows_unresolved_coordination", False)):
            return "UNRESOLVED_COORDINATION_BASELINE"
        if (negotiation_context_observed and getattr(
                self.action_provider,
                "supports_event_driven_renegotiation", False)):
            return "COMPLETE"
        raise PhysicalReplayError("SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED")

    @staticmethod
    def _decision_state_identity(states, edges, cleared_vehicle_zones):
        edge_identity = tuple(sorted((edge["yielding_vehicle_id"],
                                      edge["priority_vehicle_id"])
                                     for edge in edges))
        participants = tuple(sorted({vehicle for edge in edge_identity
                                     for vehicle in edge}))
        active_participants = tuple(vehicle for vehicle in participants
                                    if vehicle in states)
        return (active_participants, edge_identity,
                tuple(sorted(cleared_vehicle_zones)))

    @staticmethod
    def _plan_invalidation_reasons(old_identity, new_identity):
        if old_identity is None or old_identity == new_identity:
            return ()
        old_participants, old_edges, old_cleared = old_identity
        new_participants, new_edges, new_cleared = new_identity
        reasons = []
        if old_participants != new_participants:
            reasons.append("ACTIVE_PARTICIPANT_SET_CHANGED")
        if old_edges != new_edges:
            reasons.append("RELEVANT_PRECEDENCE_GRAPH_CHANGED")
        if old_cleared != new_cleared:
            reasons.append("CONFLICT_ZONE_CLEARED")
        return tuple(reasons)

    @staticmethod
    def _edge_union(snapshots):
        values = {}
        for snapshot in snapshots:
            for edge in snapshot["joint_precedence_edges"]:
                key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                values[key] = edge
        return tuple(values[key] for key in sorted(values))

    @staticmethod
    def _proposer_contexts(enumerator, states, edges, specification, source_id):
        return tuple({
            "context_id": (source_id, "PROPOSER", claim.yielding_vehicle_id,
                           claim.priority_vehicle_id),
            "ego_id": claim.yielding_vehicle_id,
            "role": "PROPOSER",
            "claim_identity": (claim.yielding_vehicle_id,
                               claim.priority_vehicle_id),
            "action_names": tuple(action.value for action in mask.action_names),
            "hard_action_mask": tuple(mask.feasibility),
            "regulatory_profile": specification.regulatory_profile,
            "route_truth_policy_leakage": 0,
        } for claim, mask in enumerator.eligible_factors(
            active_vehicle_ids=tuple(sorted(states)), original_edges=edges,
            negotiation_status=specification.expected_negotiation_status))

    @staticmethod
    def _factor_records(branch, batch_id, encoded_shapes):
        results = []
        shape = encoded_shapes[0] if encoded_shapes else ((0, 0), (0,), (2, 0))
        claim_shape = (2 * (len(NODE_NUMERIC_SCHEMA) + len(EDGE_NUMERIC_SCHEMA)),)
        protocol_shape = (2 * len(PROTOCOL_STATE_COLUMNS),)
        proposer_masks = dict(branch.proposer_assignment.hard_action_masks)
        for claim, action in branch.proposer_assignment.claim_action_assignments:
            event_id = (batch_id, "PROPOSER", claim)
            mask = tuple(proposer_masks[claim])
            if action not in tuple(name for name, allowed in zip(
                    ("KEEP_CLAIM", "RELINQUISH_CLAIM"), mask) if allowed):
                raise PhysicalReplayError("BEHAVIOR_ACTION_NOT_FEASIBLE")
            results.append(CoupledPolicyFactorRecord(
                event_id, batch_id, claim[0], "PROPOSER", claim, None,
                ("KEEP_CLAIM", "RELINQUISH_CLAIM"), mask, action,
                PROFILING_SOURCE, False, shape[0], claim_shape, None,
                (batch_id, "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"),
                (batch_id, "CENTRALIZED_ADVANTAGE_PENDING_VALUE"),
                {"route_truth_policy_leakage": 0,
                 "behavior_log_probability": "NOT_FROM_MAPPO"}))
        responder_masks = dict(branch.responder_assignment.hard_response_masks)
        for proposal_id, action in branch.responder_assignment.response_action_assignments:
            mask = tuple(responder_masks[proposal_id])
            if action not in tuple(name for name, allowed in zip(
                    ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"), mask)
                    if allowed):
                raise PhysicalReplayError("BEHAVIOR_ACTION_NOT_FEASIBLE")
            claim = (proposal_id[1], proposal_id[2])
            event_id = (batch_id, "RESPONDER", proposal_id)
            results.append(CoupledPolicyFactorRecord(
                event_id, batch_id, proposal_id[4], "RESPONDER", claim,
                proposal_id, ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"),
                mask, action, PROFILING_SOURCE, False, shape[0], claim_shape,
                protocol_shape, (batch_id, "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"),
                (batch_id, "CENTRALIZED_ADVANTAGE_PENDING_VALUE"),
                {"route_truth_policy_leakage": 0,
                 "behavior_log_probability": "NOT_FROM_MAPPO"}))
        return tuple(results)

    def run_episode(self, specification, scenario_manifest_id):
        self.reset()
        started = perf_counter()
        environment = SUMOEnv(use_gui=self.use_gui)
        observations = ObservationManager()
        predictor, entry_monitor = IntentionPredictor(), ConflictEntryMonitor()
        graph_manager = ConflictGraphManager(self.paths, self.zones)
        occupancy = ConflictZoneOccupancyAssessor(self.paths, self.zones)
        rules, negotiation = TrafficRuleEngine(self.paths), NegotiationEnvironment()
        claim_bus, encoder = V2VPrecedenceClaimBus(), GraphTensorEncoder()
        ledger = VehicleDemandLedger()
        movements = {f"SCENARIO_AV_{i}": path for i, path in
                     enumerate(specification.movement_path_ids)}
        for i, scheduled in enumerate(specification.scheduled_spawn_times):
            ledger.register_scheduled_vehicle(
                f"SCENARIO_AV_{i}", scheduled,
                DemandScheduleSource.INITIAL_SIMULATION_DEMAND,
                {"movement_path_id": specification.movement_path_ids[i]},
                {"source": "FROZEN_TRAINING_MANIFEST"})
        pending = list(zip(specification.scheduled_spawn_steps,
                           specification.movement_path_ids,
                           range(len(specification.movement_path_ids))))
        branch = plan0 = physical_obligations = None
        zone_states, cleared = {}, set()
        commands, command_audit, command_mode, constraints = [], {}, {}, []
        entry_events, clear_events, completion_events = [], [], []
        native_events, batches, encoded_shapes = [], [], []
        plan_count = 0
        negotiation_context_observed = False
        unresolved_reason = None
        event_driven = bool(getattr(
            self.action_provider, "supports_event_driven_renegotiation", False))
        authoritative_state_identity = last_decision_identity = None
        diagnostics = []
        liveness = {"negotiation_decision_epochs": 0,
                    "renegotiation_events": 0,
                    "non_executable_negotiation_outcomes": 0,
                    "executable_plans": 0,
                    "safe_hold_activations": 0}
        episode_id = ("COUPLED_TRAINING_EPISODE_V1", specification.scenario_id)
        try:
            environment.start()
            routes = {path: derive_existing_route_id(self.paths, path)
                      for path in specification.movement_path_ids}
            while environment.step_count < EPISODE_STEPS:
                due = [item for item in pending if item[0] <= environment.step_count]
                for step, path, index in due:
                    vehicle_id = f"SCENARIO_AV_{index}"
                    traci.vehicle.add(vehicle_id, routes[path], AV_TYPE_ID,
                                      departSpeed="max", departLane="free",
                                      departPos="base")
                    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)
                    observations.get_or_create_ldm(vehicle_id)
                    pending.remove((step, path, index))
                states = environment.step()
                now = environment.current_time
                for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                    if ledger.get_vehicle_record(vehicle_id):
                        ledger.record_actual_departure(vehicle_id, now)
                for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                    if ledger.get_vehicle_record(vehicle_id):
                        ledger.record_service_completion(vehicle_id, now)
                        completion_events.append((vehicle_id, now))
                collision_ids = tuple(sorted(
                    traci.simulation.getCollidingVehiclesIDList()))
                if collision_ids:
                    raise PhysicalReplayError(
                        "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED",
                        (now, collision_ids))
                emergency = tuple(sorted(
                    traci.simulation.getEmergencyStoppingVehiclesIDList()))
                if emergency: native_events.append((now, emergency))

                snapshots = edges = decision_identity = None
                safe_decision_epoch = True
                fallback_authority = None
                transition_rejected = False
                zone_observations = None
                if event_driven and branch is not None:
                    zone_observations = (
                        PhysicalBranchReplayRunner._observe_zones(
                            self, states, movements, zone_states, now,
                            entry_events, clear_events, cleared))
                if event_driven:
                    snapshots = PhysicalBranchReplayRunner._pipeline_step(
                        states, now, observations, entry_monitor, predictor,
                        graph_manager, occupancy, rules, negotiation, claim_bus,
                        encoder)
                    edges = self._edge_union(snapshots)
                    decision_identity = self._decision_state_identity(
                        states, edges, cleared)
                    current_regulatory_zone_observations = {}
                    if edges:
                        current_regulatory_graph = tuple(sorted(
                            (edge["yielding_vehicle_id"],
                             edge["priority_vehicle_id"]) for edge in edges))
                        current_obligations = self.physical_mapper.map(
                            current_regulatory_graph, tuple(sorted(states)),
                            movements)
                        current_zone_states = (
                            PhysicalBranchReplayRunner._zone_definitions(
                                self, states, movements,
                                current_obligations.physical_execution_graph))
                        current_regulatory_zone_observations = (
                            PhysicalBranchReplayRunner._observe_zones(
                                self, states, movements, current_zone_states,
                                now, entry_events, clear_events, cleared))
                    material_change = (
                        branch is not None and authoritative_state_identity !=
                        decision_identity)
                    zone_currently_occupied = any(
                        item["state"] == "CURRENTLY_OCCUPYING"
                        for item in tuple((zone_observations or {}).values()) +
                        tuple(current_regulatory_zone_observations.values()))
                    safe_decision_epoch = not zone_currently_occupied
                    reasons = self._plan_invalidation_reasons(
                        authoritative_state_identity, decision_identity)
                    prior_plan_non_executable = bool(
                        plan0 is not None and
                        (plan0.graph_status != "EXECUTABLE" or
                         not plan0.ready_vehicle_ids))
                    progress_boundary = "CONFLICT_ZONE_CLEARED" in reasons
                    safe_authority_transition = (
                        not zone_currently_occupied and
                        (prior_plan_non_executable or progress_boundary))
                    if material_change and safe_authority_transition:
                        event = {"event": "PLAN_INVALIDATED", "timestamp": now,
                                 "reasons": tuple(reasons),
                                 "old_state_identity":
                                     authoritative_state_identity,
                                 "new_state_identity": decision_identity}
                        diagnostics.append(event)
                        print("PLAN_INVALIDATED " + ",".join(reasons))
                        print("RENEGOTIATION_REQUIRED")
                        liveness["renegotiation_events"] += 1
                        fallback_authority = (
                            branch, plan0, physical_obligations, zone_states,
                            authoritative_state_identity, zone_observations)
                        branch = plan0 = physical_obligations = None
                        zone_states = {}
                        zone_observations = None
                        authoritative_state_identity = None

                if branch is None:
                    if snapshots is None:
                        snapshots = PhysicalBranchReplayRunner._pipeline_step(
                            states, now, observations, entry_monitor, predictor,
                            graph_manager, occupancy, rules, negotiation,
                            claim_bus, encoder)
                        edges = self._edge_union(snapshots)
                    if decision_identity is None:
                        decision_identity = self._decision_state_identity(
                            states, edges, cleared)
                    if (edges and (not event_driven or safe_decision_epoch) and
                            (not event_driven or
                                   decision_identity != last_decision_identity)):
                        negotiation_context_observed = True
                        last_decision_identity = decision_identity
                        source_id = (specification.scenario_id, now,
                                     "COUPLED_JOINT_NEGOTIATION_CONTEXT")
                        batch_id = (episode_id, now, "JOINT_NEGOTIATION_BATCH")
                        if event_driven:
                            liveness["negotiation_decision_epochs"] += 1
                            diagnostics.append({
                                "event": "NEGOTIATION_EVENT_CREATED",
                                "timestamp": now,
                                "state_identity": decision_identity,
                                "source_snapshot_id": source_id})
                            print("NEGOTIATION_EVENT_CREATED")
                        encoded_graphs = tuple(
                            observations.get_ldm(
                                snapshot["ego_id"]
                            ).current_encoded_graph_observation
                            for snapshot in snapshots)
                        if getattr(self.action_provider,
                                   "uses_mappo_behavior_policy", False):
                            branch = self.action_provider.select_joint_actions(
                                scenario_id=specification.scenario_id,
                                episode_id=episode_id, batch_id=batch_id,
                                source_snapshot_id=source_id,
                                original_edges=edges,
                                active_vehicle_ids=tuple(sorted(states)),
                                timestamp=now,
                                regulatory_profile=specification.regulatory_profile,
                                negotiation_status=specification.expected_negotiation_status,
                                encoded_graphs=encoded_graphs)
                            if branch is not None:
                                physical_obligations = self.physical_mapper.map(
                                    branch.effective_precedence_graph,
                                    tuple(sorted(states)), movements)
                                plan0 = self.planner.plan(
                                    source_snapshot_id=branch.source_snapshot_id,
                                    effective_coordination_graph=
                                        branch.effective_precedence_graph,
                                    active_vehicle_ids=tuple(sorted(states)),
                                    movement_path_by_vehicle=movements,
                                    timestamp=now,
                                    source_protocol_state=branch.policy_status,
                                    cleared_vehicle_zones=tuple(sorted(cleared)),
                                    physical_obligation_set=physical_obligations)
                                self.action_provider.record_physical_interpretation(
                                    batch_id, physical_obligations, plan0)
                                if event_driven:
                                    fallback_plan = (fallback_authority[1]
                                                     if fallback_authority
                                                     else None)
                                    newly_blocked_ready = tuple(sorted(
                                        set(fallback_plan.ready_vehicle_ids) &
                                        set(plan0.blocked_vehicle_ids)
                                    )) if fallback_plan else ()
                                    candidate_execution_graph = (
                                        physical_obligations.
                                        physical_execution_graph)
                                    candidate_zone_states = (
                                        PhysicalBranchReplayRunner.
                                        _zone_definitions(
                                            self, states, movements,
                                            candidate_execution_graph))
                                    candidate_zone_observations = (
                                        PhysicalBranchReplayRunner._observe_zones(
                                            self, states, movements,
                                            candidate_zone_states, now,
                                            entry_events, clear_events, cleared))
                                    blocked_permissions = {
                                        (item.vehicle_id,
                                         item.conflict_zone_id)
                                        for item in plan0.vehicle_permissions
                                        if item.permission_status ==
                                        "BLOCKED_BY_PRECEDENCE"}
                                    blocked_in_or_past_zone = tuple(sorted(
                                        key for key in blocked_permissions
                                        if (key in candidate_zone_observations and
                                            candidate_zone_observations[key][
                                                "state"] != "BEFORE_ZONE")))
                                    if (newly_blocked_ready or
                                            blocked_in_or_past_zone):
                                        unsafe_vehicle_ids = tuple(sorted(
                                            set(newly_blocked_ready) |
                                            {item[0] for item in
                                             blocked_in_or_past_zone}))
                                        diagnostics.append({
                                            "event":
                                                "PLAN_NON_EXECUTABLE_TRANSITION",
                                            "timestamp": now,
                                            "reason":
                                                "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE",
                                            "vehicle_ids": unsafe_vehicle_ids,
                                            "blocked_in_or_past_zone":
                                                blocked_in_or_past_zone})
                                        print("PLAN_NON_EXECUTABLE_TRANSITION "
                                              "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE=" +
                                              repr(unsafe_vehicle_ids))
                                        print("SAFE_HOLD_ACTIVE")
                                        liveness[
                                            "non_executable_negotiation_outcomes"
                                        ] += 1
                                        liveness["safe_hold_activations"] += 1
                                        (branch, plan0, physical_obligations,
                                         zone_states,
                                         authoritative_state_identity,
                                         zone_observations) = fallback_authority
                                        authoritative_state_identity = (
                                            decision_identity)
                                        transition_rejected = True
                                    elif (plan0.graph_status == "EXECUTABLE" and
                                            plan0.ready_vehicle_ids):
                                        liveness["executable_plans"] += 1
                                        diagnostics.append({
                                            "event": "PLAN_EXECUTABLE",
                                            "timestamp": now,
                                            "ready_vehicle_ids":
                                                plan0.ready_vehicle_ids,
                                            "blocked_vehicle_ids":
                                                plan0.blocked_vehicle_ids})
                                        print("PLAN_EXECUTABLE VEHICLE_READY=" +
                                              repr(plan0.ready_vehicle_ids))
                                    else:
                                        liveness[
                                            "non_executable_negotiation_outcomes"
                                        ] += 1
                                        liveness["safe_hold_activations"] += 1
                                        diagnostics.append({
                                            "event": "PLAN_NON_EXECUTABLE",
                                            "timestamp": now,
                                            "graph_status": plan0.graph_status,
                                            "blocked_vehicle_ids":
                                                plan0.blocked_vehicle_ids})
                                        print("PLAN_NON_EXECUTABLE " +
                                              plan0.graph_status)
                                        print("SAFE_HOLD_ACTIVE VEHICLE_BLOCKED=" +
                                              repr(plan0.blocked_vehicle_ids))
                        else:
                            enumerator = JointNegotiationBranchEnumerator(self.planner)
                            possible = enumerator.enumerate(
                                scenario_id=specification.scenario_id,
                                source_snapshot_id=source_id, original_edges=edges,
                                active_vehicle_ids=tuple(sorted(states)), timestamp=now,
                                regulatory_profile=specification.regulatory_profile,
                                negotiation_status=specification.expected_negotiation_status,
                                movement_path_by_vehicle=movements)
                            executable = tuple(item for item in possible
                                               if item.graph_executable)
                            if executable:
                                factor_contexts = self._proposer_contexts(
                                    enumerator, states, edges, specification,
                                    source_id)
                                branch = self.action_provider.select_joint_actions(
                                    possible, factor_contexts)
                                if (branch is None and getattr(
                                        self.action_provider,
                                        "allows_unresolved_coordination", False)):
                                    unresolved_reason = (
                                        "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
                            elif getattr(self.action_provider,
                                         "allows_unresolved_coordination", False):
                                unresolved_reason = (
                                    "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
                        if branch is not None and not transition_rejected:
                            if event_driven:
                                authoritative_state_identity = decision_identity
                            if plan0 is None:
                                plan0 = branch.execution_plan
                            execution_graph = (
                                physical_obligations.physical_execution_graph
                                if physical_obligations is not None else
                                branch.effective_precedence_graph)
                            zone_states = PhysicalBranchReplayRunner._zone_definitions(
                                self, states, movements,
                                execution_graph)
                            for encoded in encoded_graphs:
                                encoded_shapes.append((
                                    tuple(encoded.node_features.shape),
                                    tuple(encoded.edge_features.shape),
                                    tuple(encoded.edge_index.shape)))
                            if getattr(self.action_provider,
                                       "uses_mappo_behavior_policy", False):
                                shape = (encoded_shapes[0] if encoded_shapes
                                         else ((0, 0), (0, 0), (2, 0)))
                                factors = self.action_provider.coupled_factor_records(
                                    batch_id, shape)
                            else:
                                factors = self._factor_records(
                                    branch, batch_id, tuple(encoded_shapes))
                            batches.append((batch_id, now, source_id, factors,
                                            branch, plan0))

                if branch is not None:
                    if zone_observations is None:
                        zone_observations = (
                            PhysicalBranchReplayRunner._observe_zones(
                                self, states, movements, zone_states, now,
                                entry_events, clear_events, cleared))
                    plan = self.planner.plan(
                        source_snapshot_id=branch.source_snapshot_id,
                        effective_coordination_graph=branch.effective_precedence_graph,
                        active_vehicle_ids=tuple(sorted(states)),
                        movement_path_by_vehicle=movements, timestamp=now,
                        source_protocol_state=(
                            branch.policy_status if hasattr(branch, "policy_status")
                            else branch.branch_status),
                        cleared_vehicle_zones=tuple(sorted(cleared)),
                        physical_obligation_set=physical_obligations)
                    plan_count += 1
                    step_records = PhysicalBranchReplayRunner._apply_control(
                        plan, states, zone_observations, now, commands,
                        command_audit, command_mode, SIM_TIME_STEP)
                    constraints.extend(step_records)
            completion_status = self._terminal_coordination_status(
                branch, negotiation_context_observed, unresolved_reason)
            completed_ids = {item[0] for item in completion_events}
            unfinished_vehicle_ids = tuple(sorted(
                set(movements) - completed_ids))
            if event_driven and unfinished_vehicle_ids:
                completion_status = "EPISODE_ENDED_UNFINISHED_VEHICLES"
            demand_records = ledger.finalize_episode(EPISODE_DURATION_SECONDS)
            measures = measure_vehicle_travel_times(
                demand_records, EPISODE_DURATION_SECONDS)
            team_time = total_team_travel_time_seconds(measures)
            reward = raw_team_reward(team_time)
            if getattr(self.action_provider,
                       "uses_mappo_behavior_policy", False):
                self.action_provider.finalize_episode(episode_id, reward)
            final_batches = []
            for (batch_id, timestamp, source_id, factors, batch_branch,
                 batch_plan) in batches:
                factor_ids = tuple(item.decision_event_id for item in factors)
                proposer = tuple(item for item in factors if item.role == "PROPOSER")
                responder = tuple(item for item in factors if item.role == "RESPONDER")
                final_batches.append(CoupledNegotiationDecisionBatch(
                    batch_id, episode_id, specification.scenario_id, timestamp,
                    source_id, tuple(item.decision_event_id for item in proposer),
                    tuple(item.decision_event_id for item in proposer),
                    batch_branch.proposer_assignment.proposals_created,
                    tuple(item.decision_event_id for item in responder),
                    tuple(item.decision_event_id for item in responder),
                    (source_id, "PROTOCOL_RESOLUTION"),
                    (source_id, batch_branch.effective_precedence_graph),
                    batch_plan.plan_id, 0.0, EPISODE_DURATION_SECONDS, None,
                    "EPISODE_TERMINATED", reward, factors,
                    tuple(encoded_shapes),
                    ((sum(shape[0][0] for shape in encoded_shapes),
                      encoded_shapes[0][0][1] if encoded_shapes else 0)
                     if getattr(self.action_provider,
                                "runtime_critic_enabled", True)
                     else (0, 0)),
                    {"joint_physical_consequences": 1,
                     "reward_definition": "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1"}))
            factors = tuple(item for batch in final_batches
                            for item in batch.policy_factors)
            return CoupledNegotiationEpisodeRecord(
                episode_id, specification.scenario_id, scenario_manifest_id,
                tuple(final_batches), len(factors),
                sum(item.role == "PROPOSER" for item in factors),
                sum(item.role == "RESPONDER" for item in factors),
                sum(len(item.policy_factors) > 1 for item in final_batches),
                environment.step_count, environment.current_time,
                perf_counter() - started, len(specification.movement_path_ids),
                len(completion_events),
                sum(item[2] == "PRECEDENCE_SPEED_CAP" for item in commands),
                plan_count, len(native_events), team_time, reward, reward, 0, 0,
                completion_status,
                {"collision_free": True, "blocked_zone_invariant": True,
                 "safe_sumo_speed_mode": True, "reward_reconciled": True},
                {"action_provider": self.action_provider.selection_rule,
                 "outcome_data_used": False, "fresh_sumo_process": True,
                 "fresh_ldm_state": True, "fresh_protocol_bus": True,
                 "fresh_demand_ledger": True, "optimizer_instances": 0,
                 "backward_calls": 0, "parameter_updates": 0,
                 "unresolved_coordination_reason": unresolved_reason,
                 "fabricated_negotiation_branches": 0,
                 "vehicle_id_priority_decisions": 0,
                 "neural_actor_calls": getattr(
                     self.action_provider, "neural_actor_calls", None),
                 "event_driven_renegotiation": event_driven,
                 "liveness_metrics": {
                     **liveness,
                     "scheduled_vehicles": len(movements),
                     "completed_vehicles": len(completion_events),
                     "unfinished_vehicles": len(unfinished_vehicle_ids),
                     "unfinished_vehicle_ids": unfinished_vehicle_ids,
                     "all_scheduled_vehicles_completed":
                         not unfinished_vehicle_ids},
                 "liveness_diagnostics": tuple(diagnostics)})
        finally:
            environment.close()
