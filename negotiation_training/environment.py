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

    def __init__(self, action_provider):
        self.action_provider = action_provider
        self.paths = MapPathManager()
        self.zones = ConflictZoneManager(self.paths)
        self.planner = ConflictZoneExecutionPlanner(self.paths, self.zones)
        self._active_zone_markers = {}

    def reset(self):
        self._active_zone_markers = {}

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
        environment, observations = SUMOEnv(use_gui=False), ObservationManager()
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
        branch = plan0 = None
        zone_states, cleared = {}, set()
        commands, command_audit, command_mode, constraints = [], {}, {}, []
        entry_events, clear_events, completion_events = [], [], []
        native_events, batches, encoded_shapes = [], [], []
        plan_count = 0
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

                if branch is None:
                    snapshots = PhysicalBranchReplayRunner._pipeline_step(
                        states, now, observations, entry_monitor, predictor,
                        graph_manager, occupancy, rules, negotiation, claim_bus,
                        encoder)
                    edges = self._edge_union(snapshots)
                    if edges:
                        enumerator = JointNegotiationBranchEnumerator(self.planner)
                        source_id = (specification.scenario_id, now,
                                     "COUPLED_JOINT_NEGOTIATION_CONTEXT")
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
                            plan0 = branch.execution_plan
                            zone_states = PhysicalBranchReplayRunner._zone_definitions(
                                self, states, movements,
                                branch.effective_precedence_graph)
                            for snapshot in snapshots:
                                encoded = observations.get_ldm(
                                    snapshot["ego_id"]).current_encoded_graph_observation
                                encoded_shapes.append((
                                    tuple(encoded.node_features.shape),
                                    tuple(encoded.edge_features.shape),
                                    tuple(encoded.edge_index.shape)))
                            batch_id = (episode_id, now, "JOINT_NEGOTIATION_BATCH")
                            factors = self._factor_records(
                                branch, batch_id, tuple(encoded_shapes))
                            batches.append((batch_id, now, source_id, factors))

                if branch is not None:
                    zone_observations = PhysicalBranchReplayRunner._observe_zones(
                        self, states, movements, zone_states, now, entry_events,
                        clear_events, cleared)
                    plan = self.planner.plan(
                        source_snapshot_id=branch.source_snapshot_id,
                        effective_coordination_graph=branch.effective_precedence_graph,
                        active_vehicle_ids=tuple(sorted(states)),
                        movement_path_by_vehicle=movements, timestamp=now,
                        source_protocol_state=branch.branch_status,
                        cleared_vehicle_zones=tuple(sorted(cleared)))
                    plan_count += 1
                    step_records = PhysicalBranchReplayRunner._apply_control(
                        plan, states, zone_observations, now, commands,
                        command_audit, command_mode, SIM_TIME_STEP)
                    constraints.extend(step_records)
            if branch is None:
                raise PhysicalReplayError("SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED")
            demand_records = ledger.finalize_episode(EPISODE_DURATION_SECONDS)
            measures = measure_vehicle_travel_times(
                demand_records, EPISODE_DURATION_SECONDS)
            team_time = total_team_travel_time_seconds(measures)
            reward = raw_team_reward(team_time)
            final_batches = []
            for batch_id, timestamp, source_id, factors in batches:
                factor_ids = tuple(item.decision_event_id for item in factors)
                proposer = tuple(item for item in factors if item.role == "PROPOSER")
                responder = tuple(item for item in factors if item.role == "RESPONDER")
                final_batches.append(CoupledNegotiationDecisionBatch(
                    batch_id, episode_id, specification.scenario_id, timestamp,
                    source_id, tuple(item.decision_event_id for item in proposer),
                    tuple(item.decision_event_id for item in proposer),
                    branch.proposer_assignment.proposals_created,
                    tuple(item.decision_event_id for item in responder),
                    tuple(item.decision_event_id for item in responder),
                    (source_id, "PROTOCOL_RESOLUTION"),
                    (source_id, branch.effective_precedence_graph),
                    plan0.plan_id, 0.0, EPISODE_DURATION_SECONDS, None,
                    "EPISODE_TERMINATED", reward, factors,
                    tuple(encoded_shapes),
                    (sum(shape[0][0] for shape in encoded_shapes),
                     encoded_shapes[0][0][1] if encoded_shapes else 0),
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
                "COMPLETE",
                {"collision_free": True, "blocked_zone_invariant": True,
                 "safe_sumo_speed_mode": True, "reward_reconciled": True},
                {"action_provider": self.action_provider.selection_rule,
                 "outcome_data_used": False, "fresh_sumo_process": True,
                 "fresh_ldm_state": True, "fresh_protocol_bus": True,
                 "fresh_demand_ledger": True, "optimizer_instances": 0,
                 "backward_calls": 0, "parameter_updates": 0})
        finally:
            environment.close()
