"""Reusable event-driven SUMO environment for semantic negotiation actions."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import perf_counter from time for the operations below.
from time import perf_counter

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP from config for
# the operations below.
from config import (AV_TYPE_ID, EPISODE_DURATION_SECONDS, EPISODE_STEPS,
                    SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP)
# Import ConflictGraphManager, ConflictZoneManager, ConflictZoneOccupancyAssessor, MapPathManager from conflict
# for the operations below.
from conflict import (ConflictGraphManager, ConflictZoneManager,
                      ConflictZoneOccupancyAssessor, MapPathManager)
# Import ConflictEntryMonitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import ConflictEntryMonitor
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import ConflictZoneExecutionPlanner from negotiation_execution for the operations below.
from negotiation_execution import ConflictZoneExecutionPlanner
# Import CoordinationToPhysicalExecutionMapper from negotiation_execution for the operations below.
from negotiation_execution import CoordinationToPhysicalExecutionMapper
# Import PhysicalBranchReplayRunner, PhysicalReplayError from negotiation_execution.replay for the operations
# below.
from negotiation_execution.replay import (PhysicalBranchReplayRunner,
                                            PhysicalReplayError)
# Import GraphTensorEncoder, JointNegotiationBranchEnumerator, NegotiationEnvironment, V2VPrecedenceClaimBus from
# negotiation_learning for the operations below.
from negotiation_learning import (GraphTensorEncoder,
    JointNegotiationBranchEnumerator, NegotiationEnvironment,
    V2VPrecedenceClaimBus)
# Import PROTOCOL_STATE_COLUMNS from negotiation_learning.semantic_encoding.encoder for the operations below.
from negotiation_learning.semantic_encoding.encoder import PROTOCOL_STATE_COLUMNS
# Import EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from negotiation_learning.tensor_encoding.schemas for the
# operations below.
from negotiation_learning.tensor_encoding.schemas import (
    EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA)
# Import measure_vehicle_travel_times, raw_team_reward, total_team_travel_time_seconds from negotiation_objective
# for the operations below.
from negotiation_objective import (measure_vehicle_travel_times,
    raw_team_reward, total_team_travel_time_seconds)
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

# Import CoupledNegotiationDecisionBatch, CoupledNegotiationEpisodeRecord, CoupledPolicyFactorRecord from .models
# for the operations below.
from .models import (CoupledNegotiationDecisionBatch,
                     CoupledNegotiationEpisodeRecord,
                     CoupledPolicyFactorRecord)
# Import PROFILING_SOURCE from .providers for the operations below.
from .providers import PROFILING_SOURCE


# One fresh real-SUMO episode with event-driven semantic policy input.
# Instances expose the attributes and methods implemented in this class.
class CoupledNegotiationTrainingEnvironment:
    """One fresh real-SUMO episode with event-driven semantic policy input."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input action_provider: the supplied action provider.
    # Input use_gui: the supplied use gui.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, action_provider, use_gui=False):
        # Set self.action_provider to action_provider.
        self.action_provider = action_provider
        # Set self.use_gui to a Boolean built from use_gui.
        self.use_gui = bool(use_gui)
        # Set self.paths to the result of MapPathManager().
        self.paths = MapPathManager()
        # Set self.zones to the result of ConflictZoneManager(self.paths).
        self.zones = ConflictZoneManager(self.paths)
        # Set self.planner to the result of ConflictZoneExecutionPlanner(self.paths, self.zones).
        self.planner = ConflictZoneExecutionPlanner(self.paths, self.zones)
        # Set self.physical_mapper to the result of CoordinationToPhysicalExecutionMapper(self.zones).
        self.physical_mapper = CoordinationToPhysicalExecutionMapper(self.zones)
        # Set self._active_zone_markers to an empty dictionary.
        self._active_zone_markers = {}

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._active_zone_markers to an empty dictionary.
        self._active_zone_markers = {}

    # Keep missing semantic events fatal except for an opted-in baseline.
    # Input branch: the supplied branch.
    # Input negotiation_context_observed: the supplied negotiation context observed.
    # Input unresolved_reason: the supplied unresolved reason.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _terminal_coordination_status(self, branch,
                                      # Declare negotiation_context_observed as input parameter.
                                      negotiation_context_observed,
                                      # Declare unresolved_reason as input parameter.
                                      unresolved_reason):
        """Keep missing semantic events fatal except for an opted-in baseline."""
        # Run this branch when branch is a different object from None.
        if branch is not None:
            # Return the text 'UNRESOLVED_COORDINATION_BASELINE' when unresolved_reason, otherwise the text
            # 'COMPLETE' to the caller.
            return ("UNRESOLVED_COORDINATION_BASELINE" if unresolved_reason
                    # Supply the text 'COMPLETE' to the enclosing expression.
                    else "COMPLETE")
        # Run this branch when negotiation_context_observed and unresolved_reason and the requested attribute of
        # self.action_provider.
        if (negotiation_context_observed and unresolved_reason and
                # Evaluate the requested attribute of self.action_provider as part of the enclosing expression.
                getattr(self.action_provider,
                        # Supply the text 'allows_unresolved_coordination' to the enclosing expression.
                        "allows_unresolved_coordination", False)):
            # Return the text 'UNRESOLVED_COORDINATION_BASELINE' to the caller.
            return "UNRESOLVED_COORDINATION_BASELINE"
        # Run this branch when negotiation_context_observed and the requested attribute of self.action_provider.
        if (negotiation_context_observed and getattr(
                # Supply self.action_provider to getattr.
                self.action_provider,
                # Supply the text 'supports_event_driven_renegotiation' to the enclosing expression.
                "supports_event_driven_renegotiation", False)):
            # Return the text 'COMPLETE' to the caller.
            return "COMPLETE"
        # Raise PhysicalReplayError with the text 'SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED' to stop this execution
        # path.
        raise PhysicalReplayError("SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED")

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Decision state identity using the inputs and processing steps below.
    # Input states: the supplied states.
    # Input edges: the supplied edges.
    # Input cleared_vehicle_zones: the supplied cleared vehicle zones.
    # Output: a tuple containing active_participants, edge_identity, a tuple built from the sorted values from
    # cleared_vehicle_zones.
    def _decision_state_identity(states, edges, cleared_vehicle_zones):
        # Set edge_identity to a tuple built from the sorted values from a lazy sequence of a tuple containing
        # edge['yielding_vehicle_id'], edge['priority_vehicle_id'] for edge in edges.
        edge_identity = tuple(sorted((edge["yielding_vehicle_id"],
                                      # Include edge at 'priority_vehicle_id' in this tuple.
                                      edge["priority_vehicle_id"])
                                     # Evaluate edges as part of the enclosing expression.
                                     for edge in edges))
        # Set participants to a tuple built from the sorted values from a set of vehicle for edge in
        # edge_identity.
        participants = tuple(sorted({vehicle for edge in edge_identity
                                     # Evaluate vehicle as part of the enclosing expression.
                                     for vehicle in edge}))
        # Set active_participants to a tuple built from a lazy sequence of vehicle for vehicle in participants;
        # retain entries satisfying vehicle belongs to states.
        active_participants = tuple(vehicle for vehicle in participants
                                    # Evaluate vehicle belongs to states as part of the enclosing expression.
                                    if vehicle in states)
        # Return a tuple containing active_participants, edge_identity, a tuple built from the sorted values from
        # cleared_vehicle_zones to the caller.
        return (active_participants, edge_identity,
                # Include a tuple built from the sorted values from cleared_vehicle_zones in this tuple.
                tuple(sorted(cleared_vehicle_zones)))

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Plan invalidation reasons using the inputs and processing steps below.
    # Input old_identity: the supplied old identity.
    # Input new_identity: the supplied new identity.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _plan_invalidation_reasons(old_identity, new_identity):
        # Run this branch when old_identity is the same object as None or old_identity equals new_identity.
        if old_identity is None or old_identity == new_identity:
            # Return an empty tuple to the caller.
            return ()
        # Set (old_participants, old_edges, old_cleared) to old_identity.
        old_participants, old_edges, old_cleared = old_identity
        # Set (new_participants, new_edges, new_cleared) to new_identity.
        new_participants, new_edges, new_cleared = new_identity
        # Set reasons to an empty list.
        reasons = []
        # Run this branch when old_participants differs from new_participants.
        if old_participants != new_participants:
            # Append the text 'ACTIVE_PARTICIPANT_SET_CHANGED' to reasons.
            reasons.append("ACTIVE_PARTICIPANT_SET_CHANGED")
        # Run this branch when old_edges differs from new_edges.
        if old_edges != new_edges:
            # Append the text 'RELEVANT_PRECEDENCE_GRAPH_CHANGED' to reasons.
            reasons.append("RELEVANT_PRECEDENCE_GRAPH_CHANGED")
        # Run this branch when old_cleared differs from new_cleared.
        if old_cleared != new_cleared:
            # Append the text 'CONFLICT_ZONE_CLEARED' to reasons.
            reasons.append("CONFLICT_ZONE_CLEARED")
        # Return a tuple built from reasons to the caller.
        return tuple(reasons)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Edge union using the inputs and processing steps below.
    # Input snapshots: the supplied snapshots.
    # Output: a tuple built from a lazy sequence of values at key for key in the sorted values from values.
    # Processing: iterate over the relevant records.
    def _edge_union(snapshots):
        # Set values to an empty dictionary.
        values = {}
        # Iterate over snapshots, binding each item to snapshot.
        for snapshot in snapshots:
            # Iterate over snapshot at 'joint_precedence_edges', binding each item to edge.
            for edge in snapshot["joint_precedence_edges"]:
                # Set key to a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id'.
                key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
                # Set values[key] to edge.
                values[key] = edge
        # Return a tuple built from a lazy sequence of values at key for key in the sorted values from values to
        # the caller.
        return tuple(values[key] for key in sorted(values))

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Proposer contexts using the inputs and processing steps below.
    # Input enumerator: the supplied enumerator.
    # Input states: the supplied states.
    # Input edges: the supplied edges.
    # Input specification: the supplied specification.
    # Input source_id: the supplied source id.
    # Output: a tuple built from a lazy sequence of a dictionary containing context_id, ego_id, role,
    # claim_identity, action_names, hard_action_mask,... for (claim, mask) in the result of...
    def _proposer_contexts(enumerator, states, edges, specification, source_id):
        # Return a tuple built from a lazy sequence of a dictionary containing context_id, ego_id, role,
        # claim_identity, action_names, hard_action_mask,... for (claim, mask) in the result of
        # enumerator.eligible_factors() to the caller.
        return tuple({
            # Store a tuple containing source_id, the text 'PROPOSER', claim.yielding_vehicle_id,
            # claim.priority_vehicle_id under 'context_id'.
            "context_id": (source_id, "PROPOSER", claim.yielding_vehicle_id,
                           # Include claim.priority_vehicle_id in this tuple.
                           claim.priority_vehicle_id),
            # Store claim.yielding_vehicle_id under 'ego_id'.
            "ego_id": claim.yielding_vehicle_id,
            "role": "PROPOSER",
            # Store a tuple containing claim.yielding_vehicle_id, claim.priority_vehicle_id under
            # 'claim_identity'.
            "claim_identity": (claim.yielding_vehicle_id,
                               # Include claim.priority_vehicle_id in this tuple.
                               claim.priority_vehicle_id),
            # Store a tuple built from a lazy sequence of action.value for action in mask.action_names under
            # 'action_names'.
            "action_names": tuple(action.value for action in mask.action_names),
            # Store a tuple built from mask.feasibility under 'hard_action_mask'.
            "hard_action_mask": tuple(mask.feasibility),
            # Store specification.regulatory_profile under 'regulatory_profile'.
            "regulatory_profile": specification.regulatory_profile,
            # Store 0 under 'route_truth_policy_leakage'.
            "route_truth_policy_leakage": 0,
        # Evaluate the result of enumerator.eligible_factors() as part of the enclosing expression.
        } for claim, mask in enumerator.eligible_factors(
            # Supply active_vehicle_ids as a tuple built from the sorted values from states.
            # Supply original_edges as edges.
            active_vehicle_ids=tuple(sorted(states)), original_edges=edges,
            # Supply negotiation_status as specification.expected_negotiation_status.
            negotiation_status=specification.expected_negotiation_status))

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Factor records using the inputs and processing steps below.
    # Input branch: the supplied branch.
    # Input batch_id: the supplied batch id.
    # Input encoded_shapes: the supplied encoded shapes.
    # Output: a tuple built from results.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _factor_records(branch, batch_id, encoded_shapes):
        # Set results to an empty list.
        results = []
        # Set shape to encoded_shapes at 0 when encoded_shapes, otherwise a tuple containing a tuple containing 0,
        # 0, a tuple containing 0, a tuple containing 2, 0.
        shape = encoded_shapes[0] if encoded_shapes else ((0, 0), (0,), (2, 0))
        # Set claim_shape to a tuple containing 2 multiplied by the number of entries in NODE_NUMERIC_SCHEMA plus
        # the number of entries in EDGE_NUMERIC_SCHEMA.
        claim_shape = (2 * (len(NODE_NUMERIC_SCHEMA) + len(EDGE_NUMERIC_SCHEMA)),)
        # Set protocol_shape to a tuple containing 2 multiplied by the number of entries in
        # PROTOCOL_STATE_COLUMNS.
        protocol_shape = (2 * len(PROTOCOL_STATE_COLUMNS),)
        # Set proposer_masks to a dictionary built from branch.proposer_assignment.hard_action_masks.
        proposer_masks = dict(branch.proposer_assignment.hard_action_masks)
        # Iterate over branch.proposer_assignment.claim_action_assignments, binding each item to (claim, action).
        for claim, action in branch.proposer_assignment.claim_action_assignments:
            # Set event_id to a tuple containing batch_id, the text 'PROPOSER', claim.
            event_id = (batch_id, "PROPOSER", claim)
            # Set mask to a tuple built from proposer_masks at claim.
            mask = tuple(proposer_masks[claim])
            # Run this branch when action does not belong to a tuple built from a lazy sequence of name for (name,
            # allowed) in corresponding items paired from ('KEEP_CLAIM', 'RELINQUISH_CLAIM'), mask; retain entries
            # satisfying allowed.
            if action not in tuple(name for name, allowed in zip(
                    # Supply a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' to zip.
                    ("KEEP_CLAIM", "RELINQUISH_CLAIM"), mask) if allowed):
                # Raise PhysicalReplayError with the text 'BEHAVIOR_ACTION_NOT_FEASIBLE' to stop this execution
                # path.
                raise PhysicalReplayError("BEHAVIOR_ACTION_NOT_FEASIBLE")
            # Append the result of CoupledPolicyFactorRecord(event_id, batch_id, claim at 0, the text 'PROPOSER',
            # claim, None, a tuple containing the text...) to results.
            results.append(CoupledPolicyFactorRecord(
                # Supply event_id to CoupledPolicyFactorRecord.
                event_id, batch_id, claim[0], "PROPOSER", claim, None,
                # Supply a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' to
                # CoupledPolicyFactorRecord.
                ("KEEP_CLAIM", "RELINQUISH_CLAIM"), mask, action,
                # Supply PROFILING_SOURCE to CoupledPolicyFactorRecord.
                PROFILING_SOURCE, False, shape[0], claim_shape, None,
                # Supply a tuple containing batch_id, the text 'EXACT_UNDISCOUNTED_TEAM_RETURN_V1' to
                # CoupledPolicyFactorRecord.
                (batch_id, "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"),
                # Supply a tuple containing batch_id, the text 'CENTRALIZED_ADVANTAGE_PENDING_VALUE' to
                # CoupledPolicyFactorRecord.
                (batch_id, "CENTRALIZED_ADVANTAGE_PENDING_VALUE"),
                # Store 0 under 'route_truth_policy_leakage'.
                {"route_truth_policy_leakage": 0,
                 "behavior_log_probability": "NOT_FROM_MAPPO"}))
        # Set responder_masks to a dictionary built from branch.responder_assignment.hard_response_masks.
        responder_masks = dict(branch.responder_assignment.hard_response_masks)
        # Iterate over branch.responder_assignment.response_action_assignments, binding each item to (proposal_id,
        # action).
        for proposal_id, action in branch.responder_assignment.response_action_assignments:
            # Set mask to a tuple built from responder_masks at proposal_id.
            mask = tuple(responder_masks[proposal_id])
            # Run this branch when action does not belong to a tuple built from a lazy sequence of name for (name,
            # allowed) in corresponding items paired from ('ACCEPT_RELINQUISHMENT', 'REJECT_RELINQUISHMENT'),
            # mask; retain entries satisfying allowed.
            if action not in tuple(name for name, allowed in zip(
                    # Supply a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT'
                    # to zip.
                    ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"), mask)
                    # Evaluate allowed as part of the enclosing expression.
                    if allowed):
                # Raise PhysicalReplayError with the text 'BEHAVIOR_ACTION_NOT_FEASIBLE' to stop this execution
                # path.
                raise PhysicalReplayError("BEHAVIOR_ACTION_NOT_FEASIBLE")
            # Set claim to a tuple containing proposal_id at 1, proposal_id at 2.
            claim = (proposal_id[1], proposal_id[2])
            # Set event_id to a tuple containing batch_id, the text 'RESPONDER', proposal_id.
            event_id = (batch_id, "RESPONDER", proposal_id)
            # Append the result of CoupledPolicyFactorRecord(event_id, batch_id, proposal_id at 4, the text
            # 'RESPONDER', claim, proposal_id, a tuple...) to results.
            results.append(CoupledPolicyFactorRecord(
                # Supply proposal_id at 4 to CoupledPolicyFactorRecord.
                event_id, batch_id, proposal_id[4], "RESPONDER", claim,
                # Supply a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text 'REJECT_RELINQUISHMENT' to
                # CoupledPolicyFactorRecord.
                proposal_id, ("ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT"),
                # Supply PROFILING_SOURCE to CoupledPolicyFactorRecord.
                mask, action, PROFILING_SOURCE, False, shape[0], claim_shape,
                # Supply a tuple containing batch_id, the text 'EXACT_UNDISCOUNTED_TEAM_RETURN_V1' to
                # CoupledPolicyFactorRecord.
                protocol_shape, (batch_id, "EXACT_UNDISCOUNTED_TEAM_RETURN_V1"),
                # Supply a tuple containing batch_id, the text 'CENTRALIZED_ADVANTAGE_PENDING_VALUE' to
                # CoupledPolicyFactorRecord.
                (batch_id, "CENTRALIZED_ADVANTAGE_PENDING_VALUE"),
                # Store 0 under 'route_truth_policy_leakage'.
                {"route_truth_policy_leakage": 0,
                 "behavior_log_probability": "NOT_FROM_MAPPO"}))
        # Return a tuple built from results to the caller.
        return tuple(results)

    # Run episode using the inputs and processing steps below.
    # Input specification: the supplied specification.
    # Input scenario_manifest_id: the supplied scenario manifest id.
    # Output: the result of CoupledNegotiationEpisodeRecord(episode_id, specification.scenario_id,
    # scenario_manifest_id, a tuple built from final_batches,...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def run_episode(self, specification, scenario_manifest_id):
        # Call self.reset with the supplied arguments.
        self.reset()
        # Set started to the result of perf_counter().
        started = perf_counter()
        # Set environment to the result of SUMOEnv().
        environment = SUMOEnv(use_gui=self.use_gui)
        # Set observations to the result of ObservationManager().
        observations = ObservationManager()
        # Set (predictor, entry_monitor) to a tuple containing the result of IntentionPredictor(), the result of
        # ConflictEntryMonitor().
        predictor, entry_monitor = IntentionPredictor(), ConflictEntryMonitor()
        # Set graph_manager to the result of ConflictGraphManager(self.paths, self.zones).
        graph_manager = ConflictGraphManager(self.paths, self.zones)
        # Set occupancy to the result of ConflictZoneOccupancyAssessor(self.paths, self.zones).
        occupancy = ConflictZoneOccupancyAssessor(self.paths, self.zones)
        # Set (rules, negotiation) to a tuple containing the result of TrafficRuleEngine(self.paths), the result
        # of NegotiationEnvironment().
        rules, negotiation = TrafficRuleEngine(self.paths), NegotiationEnvironment()
        # Set (claim_bus, encoder) to a tuple containing the result of V2VPrecedenceClaimBus(), the result of
        # GraphTensorEncoder().
        claim_bus, encoder = V2VPrecedenceClaimBus(), GraphTensorEncoder()
        # Set ledger to the result of VehicleDemandLedger().
        ledger = VehicleDemandLedger()
        # Set movements to a dictionary of formatted text built from the embedded values mapped to path for (i,
        # path) in index/value pairs from specification.movement_path_ids.
        movements = {f"SCENARIO_AV_{i}": path for i, path in
                     # Evaluate index/value pairs from specification.movement_path_ids as part of the enclosing
                     # expression.
                     enumerate(specification.movement_path_ids)}
        # Iterate over index/value pairs from specification.scheduled_spawn_times, binding each item to (i,
        # scheduled).
        for i, scheduled in enumerate(specification.scheduled_spawn_times):
            # Call ledger.register_scheduled_vehicle with the supplied arguments.
            ledger.register_scheduled_vehicle(
                # Supply formatted text built from the embedded values to ledger.register_scheduled_vehicle.
                f"SCENARIO_AV_{i}", scheduled,
                # Supply DemandScheduleSource.INITIAL_SIMULATION_DEMAND to ledger.register_scheduled_vehicle.
                DemandScheduleSource.INITIAL_SIMULATION_DEMAND,
                # Store specification.movement_path_ids at i under 'movement_path_id'.
                {"movement_path_id": specification.movement_path_ids[i]},
                # Store the text 'FROZEN_TRAINING_MANIFEST' under 'source'.
                {"source": "FROZEN_TRAINING_MANIFEST"})
        # Set pending to a list built from corresponding items paired from specification.scheduled_spawn_steps,
        # specification.movement_path_ids, the integer...
        pending = list(zip(specification.scheduled_spawn_steps,
                           # Supply specification.movement_path_ids to zip.
                           specification.movement_path_ids,
                           # Supply the integer range defined by the number of entries in
                           # specification.movement_path_ids to zip.
                           range(len(specification.movement_path_ids))))
        # Set branch and plan0 and physical_obligations to None.
        branch = plan0 = physical_obligations = None
        # Set (zone_states, cleared) to a tuple containing an empty dictionary, an empty set.
        zone_states, cleared = {}, set()
        # Set (commands, command_audit, command_mode, constraints) to a tuple containing an empty list, an empty
        # dictionary, an empty dictionary, an empty list.
        commands, command_audit, command_mode, constraints = [], {}, {}, []
        # Set (entry_events, clear_events, completion_events) to a tuple containing an empty list, an empty list,
        # an empty list.
        entry_events, clear_events, completion_events = [], [], []
        # Set (native_events, batches, encoded_shapes) to a tuple containing an empty list, an empty list, an
        # empty list.
        native_events, batches, encoded_shapes = [], [], []
        # Set plan_count to 0.
        plan_count = 0
        # Set negotiation_context_observed to False.
        negotiation_context_observed = False
        # Set unresolved_reason to None.
        unresolved_reason = None
        # Set event_driven to a Boolean built from the requested attribute of self.action_provider.
        event_driven = bool(getattr(
            # Supply self.action_provider to getattr.
            self.action_provider, "supports_event_driven_renegotiation", False))
        # Set authoritative_state_identity and last_decision_identity to None.
        authoritative_state_identity = last_decision_identity = None
        # Set diagnostics to an empty list.
        diagnostics = []
        # Set liveness to a dictionary containing negotiation_decision_epochs, renegotiation_events,...
        liveness = {"negotiation_decision_epochs": 0,
                    # Store 0 under 'renegotiation_events'.
                    "renegotiation_events": 0,
                    # Store 0 under 'non_executable_negotiation_outcomes'.
                    "non_executable_negotiation_outcomes": 0,
                    # Store 0 under 'executable_plans'.
                    "executable_plans": 0,
                    # Store 0 under 'safe_hold_activations'.
                    "safe_hold_activations": 0}
        # Set episode_id to a tuple containing the text 'COUPLED_TRAINING_EPISODE_V1', specification.scenario_id.
        episode_id = ("COUPLED_TRAINING_EPISODE_V1", specification.scenario_id)
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call environment.start with the supplied arguments.
            environment.start()
            # Set routes to a dictionary of path mapped to the result of derive_existing_route_id(self.paths,
            # path) for path in specification.movement_path_ids.
            routes = {path: derive_existing_route_id(self.paths, path)
                      # Evaluate specification.movement_path_ids as part of the enclosing expression.
                      for path in specification.movement_path_ids}
            # Repeat the following steps while environment.step_count is less than EPISODE_STEPS.
            while environment.step_count < EPISODE_STEPS:
                # Set due to a list of item for item in pending; retain entries satisfying item at 0 is at most
                # environment.step_count.
                due = [item for item in pending if item[0] <= environment.step_count]
                # Iterate over due, binding each item to (step, path, index).
                for step, path, index in due:
                    # Set vehicle_id to formatted text built from the embedded values.
                    vehicle_id = f"SCENARIO_AV_{index}"
                    # Add vehicle_id to traci.vehicle.
                    traci.vehicle.add(vehicle_id, routes[path], AV_TYPE_ID,
                                      # Supply departSpeed as the text 'max'.
                                      # Supply departLane as the text 'free'.
                                      departSpeed="max", departLane="free",
                                      # Supply departPos as the text 'base'.
                                      departPos="base")
                    # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
                    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)
                    # Call observations.get_or_create_ldm with the supplied arguments.
                    observations.get_or_create_ldm(vehicle_id)
                    # Remove a tuple containing step, path, index from pending.
                    pending.remove((step, path, index))
                # Set states to the result of environment.step().
                states = environment.step()
                # Set now to environment.current_time.
                now = environment.current_time
                # Iterate over environment.lifecycle_events.departed_vehicle_ids, binding each item to vehicle_id.
                for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                    # Run this branch when the result of ledger.get_vehicle_record(vehicle_id).
                    if ledger.get_vehicle_record(vehicle_id):
                        # Call ledger.record_actual_departure with the supplied arguments.
                        ledger.record_actual_departure(vehicle_id, now)
                # Iterate over environment.lifecycle_events.arrived_vehicle_ids, binding each item to vehicle_id.
                for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                    # Run this branch when the result of ledger.get_vehicle_record(vehicle_id).
                    if ledger.get_vehicle_record(vehicle_id):
                        # Call ledger.record_service_completion with the supplied arguments.
                        ledger.record_service_completion(vehicle_id, now)
                        # Append a tuple containing vehicle_id, now to completion_events.
                        completion_events.append((vehicle_id, now))
                # Set collision_ids to a tuple built from the sorted values from the result of
                # traci.simulation.getCollidingVehiclesIDList().
                collision_ids = tuple(sorted(
                    # Supply the result of traci.simulation.getCollidingVehiclesIDList() to sorted.
                    traci.simulation.getCollidingVehiclesIDList()))
                # Run this branch when collision_ids.
                if collision_ids:
                    # Raise PhysicalReplayError with the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' to stop
                    # this execution path.
                    raise PhysicalReplayError(
                        "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED",
                        # Supply a tuple containing now, collision_ids to PhysicalReplayError.
                        (now, collision_ids))
                # Set emergency to a tuple built from the sorted values from the result of
                # traci.simulation.getEmergencyStoppingVehiclesIDList().
                emergency = tuple(sorted(
                    # Supply the result of traci.simulation.getEmergencyStoppingVehiclesIDList() to sorted.
                    traci.simulation.getEmergencyStoppingVehiclesIDList()))
                # Run this branch when emergency.
                # Append a tuple containing now, emergency to native_events.
                if emergency: native_events.append((now, emergency))

                # Set snapshots and edges and decision_identity to None.
                snapshots = edges = decision_identity = None
                # Set safe_decision_epoch to True.
                safe_decision_epoch = True
                # Set fallback_authority to None.
                fallback_authority = None
                # Set transition_rejected to False.
                transition_rejected = False
                # Set zone_observations to None.
                zone_observations = None
                # Run this branch when event_driven and branch is a different object from None.
                if event_driven and branch is not None:
                    # Set zone_observations to the result of PhysicalBranchReplayRunner._observe_zones(self,
                    # states, movements, zone_states, now, entry_events, clear_events, cleared).
                    zone_observations = (
                        # Evaluate the result of PhysicalBranchReplayRunner._observe_zones(self, states,
                        # movements, zone_states, now, entry_events, clear_events, cleared) as part of the
                        # enclosing expression.
                        PhysicalBranchReplayRunner._observe_zones(
                            # Supply zone_states to PhysicalBranchReplayRunner._observe_zones.
                            self, states, movements, zone_states, now,
                            # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                            entry_events, clear_events, cleared))
                # Run this branch when event_driven.
                if event_driven:
                    # Set snapshots to the result of PhysicalBranchReplayRunner._pipeline_step(states, now,
                    # observations, entry_monitor, predictor, graph_manager, occupancy, rules,...).
                    snapshots = PhysicalBranchReplayRunner._pipeline_step(
                        # Supply entry_monitor to PhysicalBranchReplayRunner._pipeline_step.
                        states, now, observations, entry_monitor, predictor,
                        # Supply graph_manager to PhysicalBranchReplayRunner._pipeline_step.
                        graph_manager, occupancy, rules, negotiation, claim_bus,
                        # Supply encoder to PhysicalBranchReplayRunner._pipeline_step.
                        encoder)
                    # Set edges to the result of self._edge_union(snapshots).
                    edges = self._edge_union(snapshots)
                    # Set decision_identity to the result of self._decision_state_identity(states, edges,
                    # cleared).
                    decision_identity = self._decision_state_identity(
                        # Supply cleared to self._decision_state_identity.
                        states, edges, cleared)
                    # Set current_regulatory_zone_observations to an empty dictionary.
                    current_regulatory_zone_observations = {}
                    # Run this branch when edges.
                    if edges:
                        # Set current_regulatory_graph to a tuple built from the sorted values from a lazy
                        # sequence of a tuple containing edge['yielding_vehicle_id'], edge['priority_vehicle_id']
                        # for edge in edges.
                        current_regulatory_graph = tuple(sorted(
                            # Evaluate a tuple containing edge at 'yielding_vehicle_id', edge at
                            # 'priority_vehicle_id' as part of the enclosing expression.
                            (edge["yielding_vehicle_id"],
                             # Include edge at 'priority_vehicle_id' in this tuple.
                             edge["priority_vehicle_id"]) for edge in edges))
                        # Set current_obligations to the result of
                        # self.physical_mapper.map(current_regulatory_graph, a tuple built from the sorted values
                        # from states, movements).
                        current_obligations = self.physical_mapper.map(
                            # Supply current_regulatory_graph to self.physical_mapper.map.
                            current_regulatory_graph, tuple(sorted(states)),
                            # Supply movements to self.physical_mapper.map.
                            movements)
                        # Set current_zone_states to the result of
                        # PhysicalBranchReplayRunner._zone_definitions(self, states, movements,
                        # current_obligations.physical_execution_graph).
                        current_zone_states = (
                            # Evaluate the result of PhysicalBranchReplayRunner._zone_definitions(self, states,
                            # movements, current_obligations.physical_execution_graph) as part of the enclosing
                            # expression.
                            PhysicalBranchReplayRunner._zone_definitions(
                                # Supply movements to PhysicalBranchReplayRunner._zone_definitions.
                                self, states, movements,
                                # Supply current_obligations.physical_execution_graph to
                                # PhysicalBranchReplayRunner._zone_definitions.
                                current_obligations.physical_execution_graph))
                        # Set current_regulatory_zone_observations to the result of
                        # PhysicalBranchReplayRunner._observe_zones(self, states, movements, current_zone_states,
                        # now, entry_events, clear_events, cleared).
                        current_regulatory_zone_observations = (
                            # Evaluate the result of PhysicalBranchReplayRunner._observe_zones(self, states,
                            # movements, current_zone_states, now, entry_events, clear_events, cleared) as part of
                            # the enclosing expression.
                            PhysicalBranchReplayRunner._observe_zones(
                                # Supply current_zone_states to PhysicalBranchReplayRunner._observe_zones.
                                self, states, movements, current_zone_states,
                                # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                                now, entry_events, clear_events, cleared))
                    # Set material_change to branch is a different object from None and
                    # authoritative_state_identity differs from decision_identity.
                    material_change = (
                        # Evaluate branch is a different object from None and authoritative_state_identity differs
                        # from decision_identity as part of the enclosing expression.
                        branch is not None and authoritative_state_identity !=
                        # Evaluate decision_identity as part of the enclosing expression.
                        decision_identity)
                    # Set zone_currently_occupied to whether any item is true in a lazy sequence of item at
                    # 'state' equals the text 'CURRENTLY_OCCUPYING' for item in a tuple built from
                    # (zone_observations or {}).values() plus a tuple built from
                    # current_regulatory_zone_observations.values().
                    zone_currently_occupied = any(
                        # Evaluate item at 'state' equals the text 'CURRENTLY_OCCUPYING' as part of the enclosing
                        # expression.
                        item["state"] == "CURRENTLY_OCCUPYING"
                        # Evaluate a tuple built from values from (zone_observations or {}) plus a tuple built
                        # from values from current_regulatory_zone_observations as part of the enclosing
                        # expression.
                        for item in tuple((zone_observations or {}).values()) +
                        # Evaluate a tuple built from values from current_regulatory_zone_observations as part of
                        # the enclosing expression.
                        tuple(current_regulatory_zone_observations.values()))
                    # Set safe_decision_epoch to the negation of zone_currently_occupied.
                    safe_decision_epoch = not zone_currently_occupied
                    # Set reasons to the result of self._plan_invalidation_reasons(authoritative_state_identity,
                    # decision_identity).
                    reasons = self._plan_invalidation_reasons(
                        # Supply authoritative_state_identity to self._plan_invalidation_reasons.
                        authoritative_state_identity, decision_identity)
                    # Set prior_plan_non_executable to a Boolean built from plan0 is a different object from None
                    # and plan0.graph_status differs from 'EXECUTABLE' or the negation of plan0.ready_vehicle_ids.
                    prior_plan_non_executable = bool(
                        # Supply plan0 is a different object from None and plan0.graph_status differs from the
                        # text 'EXECUTABLE' or the negation of plan0.ready_vehicle_ids to bool.
                        plan0 is not None and
                        # Evaluate plan0.graph_status differs from the text 'EXECUTABLE' or the negation of
                        # plan0.ready_vehicle_ids as part of the enclosing expression.
                        (plan0.graph_status != "EXECUTABLE" or
                         # Evaluate the negation of plan0.ready_vehicle_ids as part of the enclosing expression.
                         not plan0.ready_vehicle_ids))
                    # Set progress_boundary to the text 'CONFLICT_ZONE_CLEARED' belongs to reasons.
                    progress_boundary = "CONFLICT_ZONE_CLEARED" in reasons
                    # Set safe_authority_transition to the negation of zone_currently_occupied and
                    # prior_plan_non_executable or progress_boundary.
                    safe_authority_transition = (
                        # Evaluate the negation of zone_currently_occupied and prior_plan_non_executable or
                        # progress_boundary as part of the enclosing expression.
                        not zone_currently_occupied and
                        # Evaluate prior_plan_non_executable or progress_boundary as part of the enclosing
                        # expression.
                        (prior_plan_non_executable or progress_boundary))
                    # Run this branch when material_change and safe_authority_transition.
                    if material_change and safe_authority_transition:
                        # Set event to a dictionary containing event, timestamp, reasons, old_state_identity,
                        # new_state_identity.
                        event = {"event": "PLAN_INVALIDATED", "timestamp": now,
                                 # Store a tuple built from reasons under 'reasons'.
                                 "reasons": tuple(reasons),
                                 "old_state_identity":
                                     # Evaluate authoritative_state_identity as part of the enclosing expression.
                                     authoritative_state_identity,
                                 # Store decision_identity under 'new_state_identity'.
                                 "new_state_identity": decision_identity}
                        # Append event to diagnostics.
                        diagnostics.append(event)
                        # Display the text 'PLAN_INVALIDATED' plus the result of ','.join(reasons).
                        print("PLAN_INVALIDATED " + ",".join(reasons))
                        # Display the text 'RENEGOTIATION_REQUIRED'.
                        print("RENEGOTIATION_REQUIRED")
                        # Update liveness['renegotiation_events'] to its current value plus 1.
                        liveness["renegotiation_events"] += 1
                        # Set fallback_authority to a tuple containing branch, plan0, physical_obligations,
                        # zone_states, authoritative_state_identity, zone_observations.
                        fallback_authority = (
                            # Include physical_obligations in this tuple.
                            branch, plan0, physical_obligations, zone_states,
                            # Include authoritative_state_identity in this tuple.
                            authoritative_state_identity, zone_observations)
                        # Set branch and plan0 and physical_obligations to None.
                        branch = plan0 = physical_obligations = None
                        # Set zone_states to an empty dictionary.
                        zone_states = {}
                        # Set zone_observations to None.
                        zone_observations = None
                        # Set authoritative_state_identity to None.
                        authoritative_state_identity = None

                # Run this branch when branch is the same object as None.
                if branch is None:
                    # Run this branch when snapshots is the same object as None.
                    if snapshots is None:
                        # Set snapshots to the result of PhysicalBranchReplayRunner._pipeline_step(states, now,
                        # observations, entry_monitor, predictor, graph_manager, occupancy, rules,...).
                        snapshots = PhysicalBranchReplayRunner._pipeline_step(
                            # Supply entry_monitor to PhysicalBranchReplayRunner._pipeline_step.
                            states, now, observations, entry_monitor, predictor,
                            # Supply graph_manager to PhysicalBranchReplayRunner._pipeline_step.
                            graph_manager, occupancy, rules, negotiation,
                            # Supply claim_bus to PhysicalBranchReplayRunner._pipeline_step.
                            claim_bus, encoder)
                        # Set edges to the result of self._edge_union(snapshots).
                        edges = self._edge_union(snapshots)
                    # Run this branch when decision_identity is the same object as None.
                    if decision_identity is None:
                        # Set decision_identity to the result of self._decision_state_identity(states, edges,
                        # cleared).
                        decision_identity = self._decision_state_identity(
                            # Supply cleared to self._decision_state_identity.
                            states, edges, cleared)
                    # Run this branch when edges and the negation of event_driven or safe_decision_epoch and the
                    # negation of event_driven or decision_identity differs from last_decision_identity.
                    if (edges and (not event_driven or safe_decision_epoch) and
                            # Evaluate the negation of event_driven or decision_identity differs from
                            # last_decision_identity as part of the enclosing expression.
                            (not event_driven or
                                   # Evaluate decision_identity differs from last_decision_identity as part of the
                                   # enclosing expression.
                                   decision_identity != last_decision_identity)):
                        # Set negotiation_context_observed to True.
                        negotiation_context_observed = True
                        # Set last_decision_identity to decision_identity.
                        last_decision_identity = decision_identity
                        # Set source_id to a tuple containing specification.scenario_id, now, the text
                        # 'COUPLED_JOINT_NEGOTIATION_CONTEXT'.
                        source_id = (specification.scenario_id, now,
                                     "COUPLED_JOINT_NEGOTIATION_CONTEXT")
                        # Set batch_id to a tuple containing episode_id, now, the text 'JOINT_NEGOTIATION_BATCH'.
                        batch_id = (episode_id, now, "JOINT_NEGOTIATION_BATCH")
                        # Run this branch when event_driven.
                        if event_driven:
                            # Update liveness['negotiation_decision_epochs'] to its current value plus 1.
                            liveness["negotiation_decision_epochs"] += 1
                            # Append a dictionary containing event, timestamp, state_identity, source_snapshot_id
                            # to diagnostics.
                            diagnostics.append({
                                "event": "NEGOTIATION_EVENT_CREATED",
                                # Store now under 'timestamp'.
                                "timestamp": now,
                                # Store decision_identity under 'state_identity'.
                                "state_identity": decision_identity,
                                # Store source_id under 'source_snapshot_id'.
                                "source_snapshot_id": source_id})
                            # Display the text 'NEGOTIATION_EVENT_CREATED'.
                            print("NEGOTIATION_EVENT_CREATED")
                        # Set encoded_graphs to a tuple built from a lazy sequence of
                        # observations.get_ldm(snapshot['ego_id']).current_encoded_graph_observation for snapshot
                        # in snapshots.
                        encoded_graphs = tuple(
                            # Evaluate observations.get_ldm(snapshot['ego_id']).current_encoded_graph_observation
                            # as part of the enclosing expression.
                            observations.get_ldm(
                                # Supply snapshot at 'ego_id' to observations.get_ldm.
                                snapshot["ego_id"]
                            ).current_encoded_graph_observation
                            # Evaluate snapshots as part of the enclosing expression.
                            for snapshot in snapshots)
                        # Run this branch when the requested attribute of self.action_provider.
                        if getattr(self.action_provider,
                                   # Supply the text 'uses_mappo_behavior_policy' to the enclosing expression.
                                   "uses_mappo_behavior_policy", False):
                            # Set branch to the result of self.action_provider.select_joint_actions().
                            branch = self.action_provider.select_joint_actions(
                                # Supply scenario_id as specification.scenario_id.
                                scenario_id=specification.scenario_id,
                                # Supply episode_id as episode_id.
                                # Supply batch_id as batch_id.
                                episode_id=episode_id, batch_id=batch_id,
                                # Supply source_snapshot_id as source_id.
                                source_snapshot_id=source_id,
                                # Supply original_edges as edges.
                                original_edges=edges,
                                # Supply active_vehicle_ids as a tuple built from the sorted values from states.
                                active_vehicle_ids=tuple(sorted(states)),
                                # Supply timestamp as now.
                                timestamp=now,
                                # Supply regulatory_profile as specification.regulatory_profile.
                                regulatory_profile=specification.regulatory_profile,
                                # Supply negotiation_status as specification.expected_negotiation_status.
                                negotiation_status=specification.expected_negotiation_status,
                                # Supply encoded_graphs as encoded_graphs.
                                encoded_graphs=encoded_graphs)
                            # Run this branch when branch is a different object from None.
                            if branch is not None:
                                # Set physical_obligations to the result of
                                # self.physical_mapper.map(branch.effective_precedence_graph, a tuple built from
                                # the sorted values from states, movements).
                                physical_obligations = self.physical_mapper.map(
                                    # Supply branch.effective_precedence_graph to self.physical_mapper.map.
                                    branch.effective_precedence_graph,
                                    # Supply a tuple built from the sorted values from states to
                                    # self.physical_mapper.map.
                                    tuple(sorted(states)), movements)
                                # Set plan0 to the result of self.planner.plan().
                                plan0 = self.planner.plan(
                                    # Supply source_snapshot_id as branch.source_snapshot_id.
                                    source_snapshot_id=branch.source_snapshot_id,
                                    # Supply effective_coordination_graph as branch.effective_precedence_graph.
                                    effective_coordination_graph=
                                        # Evaluate branch.effective_precedence_graph as part of the enclosing
                                        # expression.
                                        branch.effective_precedence_graph,
                                    # Supply active_vehicle_ids as a tuple built from the sorted values from
                                    # states.
                                    active_vehicle_ids=tuple(sorted(states)),
                                    # Supply movement_path_by_vehicle as movements.
                                    movement_path_by_vehicle=movements,
                                    # Supply timestamp as now.
                                    timestamp=now,
                                    # Supply source_protocol_state as branch.policy_status.
                                    source_protocol_state=branch.policy_status,
                                    # Supply cleared_vehicle_zones as a tuple built from the sorted values from
                                    # cleared.
                                    cleared_vehicle_zones=tuple(sorted(cleared)),
                                    # Supply physical_obligation_set as physical_obligations.
                                    physical_obligation_set=physical_obligations)
                                # Call self.action_provider.record_physical_interpretation with the supplied
                                # arguments.
                                self.action_provider.record_physical_interpretation(
                                    # Supply physical_obligations to
                                    # self.action_provider.record_physical_interpretation.
                                    batch_id, physical_obligations, plan0)
                                # Run this branch when event_driven.
                                if event_driven:
                                    # Set fallback_plan to fallback_authority at 1 when fallback_authority,
                                    # otherwise None.
                                    fallback_plan = (fallback_authority[1]
                                                     # Evaluate fallback_authority as part of the enclosing expression.
                                                     if fallback_authority
                                                     # Supply None to the enclosing expression.
                                                     else None)
                                    # Set newly_blocked_ready to a tuple built from the sorted values from
                                    # set(fallback_plan.ready_vehicle_ids) intersected with
                                    # set(plan0.blocked_vehicle_ids) when fallback_plan, otherwise an empty tuple.
                                    newly_blocked_ready = tuple(sorted(
                                        # Supply a set built from fallback_plan.ready_vehicle_ids intersected with
                                        # a set built from plan0.blocked_vehicle_ids to sorted.
                                        set(fallback_plan.ready_vehicle_ids) &
                                        # Evaluate a set built from plan0.blocked_vehicle_ids as part of the
                                        # enclosing expression.
                                        set(plan0.blocked_vehicle_ids)
                                    # Evaluate fallback_plan as part of the enclosing expression.
                                    )) if fallback_plan else ()
                                    # Set candidate_execution_graph to
                                    # physical_obligations.physical_execution_graph.
                                    candidate_execution_graph = (
                                        # Evaluate physical_obligations.physical_execution_graph as part of the
                                        # enclosing expression.
                                        physical_obligations.
                                        physical_execution_graph)
                                    # Set candidate_zone_states to the result of
                                    # PhysicalBranchReplayRunner._zone_definitions(self, states, movements,
                                    # candidate_execution_graph).
                                    candidate_zone_states = (
                                        # Evaluate the result of
                                        # PhysicalBranchReplayRunner._zone_definitions(self, states, movements,
                                        # candidate_execution_graph) as part of the enclosing expression.
                                        PhysicalBranchReplayRunner.
                                        _zone_definitions(
                                            # Supply movements to PhysicalBranchReplayRunner._zone_definitions.
                                            self, states, movements,
                                            # Supply candidate_execution_graph to
                                            # PhysicalBranchReplayRunner._zone_definitions.
                                            candidate_execution_graph))
                                    # Set candidate_zone_observations to the result of
                                    # PhysicalBranchReplayRunner._observe_zones(self, states, movements,
                                    # candidate_zone_states, now, entry_events, clear_events, cleared).
                                    candidate_zone_observations = (
                                        # Evaluate the result of PhysicalBranchReplayRunner._observe_zones(self,
                                        # states, movements, candidate_zone_states, now, entry_events,
                                        # clear_events, cleared) as part of the enclosing expression.
                                        PhysicalBranchReplayRunner._observe_zones(
                                            # Supply movements to PhysicalBranchReplayRunner._observe_zones.
                                            self, states, movements,
                                            # Supply candidate_zone_states to
                                            # PhysicalBranchReplayRunner._observe_zones.
                                            candidate_zone_states, now,
                                            # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                                            entry_events, clear_events, cleared))
                                    # Set blocked_permissions to a set of a tuple containing item.vehicle_id,
                                    # item.conflict_zone_id for item in plan0.vehicle_permissions; retain entries
                                    # satisfying item.permission_status equals the text 'BLOCKED_BY_PRECEDENCE'.
                                    blocked_permissions = {
                                        # Evaluate a tuple containing item.vehicle_id, item.conflict_zone_id as
                                        # part of the enclosing expression.
                                        (item.vehicle_id,
                                         # Include item.conflict_zone_id in this tuple.
                                         item.conflict_zone_id)
                                        # Evaluate plan0.vehicle_permissions as part of the enclosing expression.
                                        for item in plan0.vehicle_permissions
                                        # Evaluate item.permission_status equals the text 'BLOCKED_BY_PRECEDENCE'
                                        # as part of the enclosing expression.
                                        if item.permission_status ==
                                        "BLOCKED_BY_PRECEDENCE"}
                                    # Set blocked_in_or_past_zone to a tuple built from the sorted values from a
                                    # lazy sequence of key for key in blocked_permissions; retain entries
                                    # satisfying key in candidate_zone_observations and
                                    # candidate_zone_observations[key]['state'] !=...
                                    blocked_in_or_past_zone = tuple(sorted(
                                        # Evaluate blocked_permissions as part of the enclosing expression.
                                        key for key in blocked_permissions
                                        # Evaluate key belongs to candidate_zone_observations and
                                        # candidate_zone_observations[key] at 'state' differs from the text
                                        # 'BEFORE_ZONE' as part of the enclosing expression.
                                        if (key in candidate_zone_observations and
                                            # Evaluate candidate_zone_observations[key] at 'state' differs from the
                                            # text 'BEFORE_ZONE' as part of the enclosing expression.
                                            candidate_zone_observations[key][
                                                # Supply the text 'BEFORE_ZONE' to the enclosing expression.
                                                "state"] != "BEFORE_ZONE")))
                                    # Run this branch when newly_blocked_ready or blocked_in_or_past_zone.
                                    if (newly_blocked_ready or
                                            # Evaluate blocked_in_or_past_zone as part of the enclosing expression.
                                            blocked_in_or_past_zone):
                                        # Set unsafe_vehicle_ids to a tuple built from the sorted values from a
                                        # set built from newly_blocked_ready combined with a set of item[0] for
                                        # item in blocked_in_or_past_zone.
                                        unsafe_vehicle_ids = tuple(sorted(
                                            # Supply a set built from newly_blocked_ready combined with a set of
                                            # item at 0 for item in blocked_in_or_past_zone to sorted.
                                            set(newly_blocked_ready) |
                                            # Evaluate a set of item at 0 for item in blocked_in_or_past_zone as
                                            # part of the enclosing expression.
                                            {item[0] for item in
                                             # Evaluate blocked_in_or_past_zone as part of the enclosing expression.
                                             blocked_in_or_past_zone}))
                                        # Append a dictionary containing event, timestamp, reason, vehicle_ids,
                                        # blocked_in_or_past_zone to diagnostics.
                                        diagnostics.append({
                                            "event":
                                                "PLAN_NON_EXECUTABLE_TRANSITION",
                                            # Store now under 'timestamp'.
                                            "timestamp": now,
                                            "reason":
                                                "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE",
                                            # Store unsafe_vehicle_ids under 'vehicle_ids'.
                                            "vehicle_ids": unsafe_vehicle_ids,
                                            "blocked_in_or_past_zone":
                                                # Evaluate blocked_in_or_past_zone as part of the enclosing expression.
                                                blocked_in_or_past_zone})
                                        # Display the text 'PLAN_NON_EXECUTABLE_TRANSITION
                                        # NEW_BLOCK_NOT_SAFE_TO_ACTIVATE=' plus the result of
                                        # repr(unsafe_vehicle_ids).
                                        print("PLAN_NON_EXECUTABLE_TRANSITION "
                                              "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE=" +
                                              # Evaluate the result of repr(unsafe_vehicle_ids) as part of the
                                              # enclosing expression.
                                              repr(unsafe_vehicle_ids))
                                        # Display the text 'SAFE_HOLD_ACTIVE'.
                                        print("SAFE_HOLD_ACTIVE")
                                        # Update liveness['non_executable_negotiation_outcomes'] to its current
                                        # value plus 1.
                                        liveness[
                                            "non_executable_negotiation_outcomes"
                                        # Supply 1 to the enclosing expression.
                                        ] += 1
                                        # Update liveness['safe_hold_activations'] to its current value plus 1.
                                        liveness["safe_hold_activations"] += 1
                                        # Set (branch, plan0, physical_obligations, zone_states,
                                        # authoritative_state_identity, zone_observations) to fallback_authority.
                                        (branch, plan0, physical_obligations,
                                         # Include zone_states in this tuple.
                                         zone_states,
                                         # Include authoritative_state_identity in this tuple.
                                         authoritative_state_identity,
                                         # Evaluate fallback_authority as part of the enclosing expression.
                                         zone_observations) = fallback_authority
                                        # Set authoritative_state_identity to decision_identity.
                                        authoritative_state_identity = (
                                            # Evaluate decision_identity as part of the enclosing expression.
                                            decision_identity)
                                        # Set transition_rejected to True.
                                        transition_rejected = True
                                    # Run this branch when plan0.graph_status equals the text 'EXECUTABLE' and
                                    # plan0.ready_vehicle_ids.
                                    elif (plan0.graph_status == "EXECUTABLE" and
                                            # Evaluate plan0.ready_vehicle_ids as part of the enclosing expression.
                                            plan0.ready_vehicle_ids):
                                        # Update liveness['executable_plans'] to its current value plus 1.
                                        liveness["executable_plans"] += 1
                                        # Append a dictionary containing event, timestamp, ready_vehicle_ids,
                                        # blocked_vehicle_ids to diagnostics.
                                        diagnostics.append({
                                            "event": "PLAN_EXECUTABLE",
                                            # Store now under 'timestamp'.
                                            "timestamp": now,
                                            "ready_vehicle_ids":
                                                # Evaluate plan0.ready_vehicle_ids as part of the enclosing expression.
                                                plan0.ready_vehicle_ids,
                                            "blocked_vehicle_ids":
                                                # Evaluate plan0.blocked_vehicle_ids as part of the enclosing
                                                # expression.
                                                plan0.blocked_vehicle_ids})
                                        # Display the text 'PLAN_EXECUTABLE VEHICLE_READY=' plus the result of
                                        # repr(plan0.ready_vehicle_ids).
                                        print("PLAN_EXECUTABLE VEHICLE_READY=" +
                                              # Evaluate the result of repr(plan0.ready_vehicle_ids) as part of the
                                              # enclosing expression.
                                              repr(plan0.ready_vehicle_ids))
                                    # Run this alternative branch when the preceding branch does not apply.
                                    else:
                                        # Update liveness['non_executable_negotiation_outcomes'] to its current
                                        # value plus 1.
                                        liveness[
                                            "non_executable_negotiation_outcomes"
                                        # Supply 1 to the enclosing expression.
                                        ] += 1
                                        # Update liveness['safe_hold_activations'] to its current value plus 1.
                                        liveness["safe_hold_activations"] += 1
                                        # Append a dictionary containing event, timestamp, graph_status,
                                        # blocked_vehicle_ids to diagnostics.
                                        diagnostics.append({
                                            "event": "PLAN_NON_EXECUTABLE",
                                            # Store now under 'timestamp'.
                                            "timestamp": now,
                                            # Store plan0.graph_status under 'graph_status'.
                                            "graph_status": plan0.graph_status,
                                            "blocked_vehicle_ids":
                                                # Evaluate plan0.blocked_vehicle_ids as part of the enclosing
                                                # expression.
                                                plan0.blocked_vehicle_ids})
                                        # Display the text 'PLAN_NON_EXECUTABLE' plus plan0.graph_status.
                                        print("PLAN_NON_EXECUTABLE " +
                                              # Evaluate plan0.graph_status as part of the enclosing expression.
                                              plan0.graph_status)
                                        # Display the text 'SAFE_HOLD_ACTIVE VEHICLE_BLOCKED=' plus the result of
                                        # repr(plan0.blocked_vehicle_ids).
                                        print("SAFE_HOLD_ACTIVE VEHICLE_BLOCKED=" +
                                              # Evaluate the result of repr(plan0.blocked_vehicle_ids) as part of the
                                              # enclosing expression.
                                              repr(plan0.blocked_vehicle_ids))
                        # Run this alternative branch when the preceding branch does not apply.
                        else:
                            # Set enumerator to the result of JointNegotiationBranchEnumerator(self.planner).
                            enumerator = JointNegotiationBranchEnumerator(self.planner)
                            # Set possible to the result of enumerator.enumerate().
                            possible = enumerator.enumerate(
                                # Supply scenario_id as specification.scenario_id.
                                scenario_id=specification.scenario_id,
                                # Supply source_snapshot_id as source_id.
                                # Supply original_edges as edges.
                                source_snapshot_id=source_id, original_edges=edges,
                                # Supply active_vehicle_ids as a tuple built from the sorted values from states.
                                # Supply timestamp as now.
                                active_vehicle_ids=tuple(sorted(states)), timestamp=now,
                                # Supply regulatory_profile as specification.regulatory_profile.
                                regulatory_profile=specification.regulatory_profile,
                                # Supply negotiation_status as specification.expected_negotiation_status.
                                negotiation_status=specification.expected_negotiation_status,
                                # Supply movement_path_by_vehicle as movements.
                                movement_path_by_vehicle=movements)
                            # Set executable to a tuple built from a lazy sequence of item for item in possible;
                            # retain entries satisfying item.graph_executable.
                            executable = tuple(item for item in possible
                                               # Evaluate item.graph_executable as part of the enclosing expression.
                                               if item.graph_executable)
                            # Run this branch when executable.
                            if executable:
                                # Set factor_contexts to the result of self._proposer_contexts(enumerator, states,
                                # edges, specification, source_id).
                                factor_contexts = self._proposer_contexts(
                                    # Supply specification to self._proposer_contexts.
                                    enumerator, states, edges, specification,
                                    # Supply source_id to self._proposer_contexts.
                                    source_id)
                                # Set branch to the result of self.action_provider.select_joint_actions(possible,
                                # factor_contexts).
                                branch = self.action_provider.select_joint_actions(
                                    # Supply factor_contexts to self.action_provider.select_joint_actions.
                                    possible, factor_contexts)
                                # Run this branch when branch is the same object as None and the requested
                                # attribute of self.action_provider.
                                if (branch is None and getattr(
                                        # Supply self.action_provider to getattr.
                                        self.action_provider,
                                        # Supply the text 'allows_unresolved_coordination' to the enclosing
                                        # expression.
                                        "allows_unresolved_coordination", False)):
                                    # Set unresolved_reason to the text 'NO_EXECUTABLE_KEEP_REGULATORY_BRANCH'.
                                    unresolved_reason = (
                                        "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
                            # Run this branch when the requested attribute of self.action_provider.
                            elif getattr(self.action_provider,
                                         # Supply the text 'allows_unresolved_coordination' to the enclosing
                                         # expression.
                                         "allows_unresolved_coordination", False):
                                # Set unresolved_reason to the text 'NO_EXECUTABLE_KEEP_REGULATORY_BRANCH'.
                                unresolved_reason = (
                                    "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
                        # Run this branch when branch is a different object from None and the negation of
                        # transition_rejected.
                        if branch is not None and not transition_rejected:
                            # Run this branch when event_driven.
                            if event_driven:
                                # Set authoritative_state_identity to decision_identity.
                                authoritative_state_identity = decision_identity
                            # Run this branch when plan0 is the same object as None.
                            if plan0 is None:
                                # Set plan0 to branch.execution_plan.
                                plan0 = branch.execution_plan
                            # Set execution_graph to physical_obligations.physical_execution_graph when
                            # physical_obligations is a different object from None, otherwise
                            # branch.effective_precedence_graph.
                            execution_graph = (
                                # Evaluate physical_obligations.physical_execution_graph when physical_obligations
                                # is a different object from None, otherwise branch.effective_precedence_graph as
                                # part of the enclosing expression.
                                physical_obligations.physical_execution_graph
                                # Evaluate physical_obligations is a different object from None as part of the
                                # enclosing expression.
                                if physical_obligations is not None else
                                # Evaluate branch.effective_precedence_graph as part of the enclosing expression.
                                branch.effective_precedence_graph)
                            # Set zone_states to the result of PhysicalBranchReplayRunner._zone_definitions(self,
                            # states, movements, execution_graph).
                            zone_states = PhysicalBranchReplayRunner._zone_definitions(
                                # Supply movements to PhysicalBranchReplayRunner._zone_definitions.
                                self, states, movements,
                                # Supply execution_graph to PhysicalBranchReplayRunner._zone_definitions.
                                execution_graph)
                            # Iterate over encoded_graphs, binding each item to encoded.
                            for encoded in encoded_graphs:
                                # Append a tuple containing a tuple built from encoded.node_features.shape, a
                                # tuple built from encoded.edge_features.shape, a tuple... to encoded_shapes.
                                encoded_shapes.append((
                                    # Include a tuple built from encoded.node_features.shape in this tuple.
                                    tuple(encoded.node_features.shape),
                                    # Include a tuple built from encoded.edge_features.shape in this tuple.
                                    tuple(encoded.edge_features.shape),
                                    # Include a tuple built from encoded.edge_index.shape in this tuple.
                                    tuple(encoded.edge_index.shape)))
                            # Run this branch when the requested attribute of self.action_provider.
                            if getattr(self.action_provider,
                                       # Supply the text 'uses_mappo_behavior_policy' to the enclosing expression.
                                       "uses_mappo_behavior_policy", False):
                                # Set shape to encoded_shapes at 0 when encoded_shapes, otherwise a tuple
                                # containing a tuple containing 0, 0, a tuple containing 0, 0, a tuple containing
                                # 2, 0.
                                shape = (encoded_shapes[0] if encoded_shapes
                                         # Evaluate a tuple containing a tuple containing 0, 0, a tuple containing
                                         # 0, 0, a tuple containing 2, 0 as part of the enclosing expression.
                                         else ((0, 0), (0, 0), (2, 0)))
                                # Set factors to the result of
                                # self.action_provider.coupled_factor_records(batch_id, shape).
                                factors = self.action_provider.coupled_factor_records(
                                    # Supply batch_id to self.action_provider.coupled_factor_records.
                                    batch_id, shape)
                            # Run this alternative branch when the preceding branch does not apply.
                            else:
                                # Set factors to the result of self._factor_records(branch, batch_id, a tuple
                                # built from encoded_shapes).
                                factors = self._factor_records(
                                    # Supply a tuple built from encoded_shapes to self._factor_records.
                                    branch, batch_id, tuple(encoded_shapes))
                            # Append a tuple containing batch_id, now, source_id, factors, branch, plan0 to
                            # batches.
                            batches.append((batch_id, now, source_id, factors,
                                            # Include branch in this tuple.
                                            branch, plan0))

                # Run this branch when branch is a different object from None.
                if branch is not None:
                    # Run this branch when zone_observations is the same object as None.
                    if zone_observations is None:
                        # Set zone_observations to the result of PhysicalBranchReplayRunner._observe_zones(self,
                        # states, movements, zone_states, now, entry_events, clear_events, cleared).
                        zone_observations = (
                            # Evaluate the result of PhysicalBranchReplayRunner._observe_zones(self, states,
                            # movements, zone_states, now, entry_events, clear_events, cleared) as part of the
                            # enclosing expression.
                            PhysicalBranchReplayRunner._observe_zones(
                                # Supply zone_states to PhysicalBranchReplayRunner._observe_zones.
                                self, states, movements, zone_states, now,
                                # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                                entry_events, clear_events, cleared))
                    # Set plan to the result of self.planner.plan().
                    plan = self.planner.plan(
                        # Supply source_snapshot_id as branch.source_snapshot_id.
                        source_snapshot_id=branch.source_snapshot_id,
                        # Supply effective_coordination_graph as branch.effective_precedence_graph.
                        effective_coordination_graph=branch.effective_precedence_graph,
                        # Supply active_vehicle_ids as a tuple built from the sorted values from states.
                        active_vehicle_ids=tuple(sorted(states)),
                        # Supply movement_path_by_vehicle as movements.
                        # Supply timestamp as now.
                        movement_path_by_vehicle=movements, timestamp=now,
                        # Supply source_protocol_state as branch.policy_status when whether branch exposes the
                        # requested attribute, otherwise branch.branch_status.
                        source_protocol_state=(
                            # Evaluate branch.policy_status when whether branch exposes the requested attribute,
                            # otherwise branch.branch_status as part of the enclosing expression.
                            branch.policy_status if hasattr(branch, "policy_status")
                            # Evaluate branch.branch_status as part of the enclosing expression.
                            else branch.branch_status),
                        # Supply cleared_vehicle_zones as a tuple built from the sorted values from cleared.
                        cleared_vehicle_zones=tuple(sorted(cleared)),
                        # Supply physical_obligation_set as physical_obligations.
                        physical_obligation_set=physical_obligations)
                    # Update plan_count to its current value plus 1.
                    plan_count += 1
                    # Set step_records to the result of PhysicalBranchReplayRunner._apply_control(plan, states,
                    # zone_observations, now, commands, command_audit, command_mode, SIM_TIME_STEP).
                    step_records = PhysicalBranchReplayRunner._apply_control(
                        # Supply zone_observations to PhysicalBranchReplayRunner._apply_control.
                        plan, states, zone_observations, now, commands,
                        # Supply command_audit to PhysicalBranchReplayRunner._apply_control.
                        command_audit, command_mode, SIM_TIME_STEP)
                    # Extend constraints with step_records.
                    constraints.extend(step_records)
            # Set completion_status to the result of self._terminal_coordination_status(branch,
            # negotiation_context_observed, unresolved_reason).
            completion_status = self._terminal_coordination_status(
                # Supply negotiation_context_observed to self._terminal_coordination_status.
                branch, negotiation_context_observed, unresolved_reason)
            # Set completed_ids to a set of item at 0 for item in completion_events.
            completed_ids = {item[0] for item in completion_events}
            # Set unfinished_vehicle_ids to a tuple built from the sorted values from a set built from movements
            # minus completed_ids.
            unfinished_vehicle_ids = tuple(sorted(
                # Supply a set built from movements minus completed_ids to sorted.
                set(movements) - completed_ids))
            # Run this branch when event_driven and unfinished_vehicle_ids.
            if event_driven and unfinished_vehicle_ids:
                # Set completion_status to the text 'EPISODE_ENDED_UNFINISHED_VEHICLES'.
                completion_status = "EPISODE_ENDED_UNFINISHED_VEHICLES"
            # Set demand_records to the result of ledger.finalize_episode(EPISODE_DURATION_SECONDS).
            demand_records = ledger.finalize_episode(EPISODE_DURATION_SECONDS)
            # Set measures to the result of measure_vehicle_travel_times(demand_records,
            # EPISODE_DURATION_SECONDS).
            measures = measure_vehicle_travel_times(
                # Supply EPISODE_DURATION_SECONDS to measure_vehicle_travel_times.
                demand_records, EPISODE_DURATION_SECONDS)
            # Set team_time to the result of total_team_travel_time_seconds(measures).
            team_time = total_team_travel_time_seconds(measures)
            # Set reward to the result of raw_team_reward(team_time).
            reward = raw_team_reward(team_time)
            # Run this branch when the requested attribute of self.action_provider.
            if getattr(self.action_provider,
                       # Supply the text 'uses_mappo_behavior_policy' to the enclosing expression.
                       "uses_mappo_behavior_policy", False):
                # Call self.action_provider.finalize_episode with the supplied arguments.
                self.action_provider.finalize_episode(episode_id, reward)
            # Set final_batches to an empty list.
            final_batches = []
            # Iterate over batches, binding each item to (batch_id, timestamp, source_id, factors, batch_branch,
            # batch_plan).
            for (batch_id, timestamp, source_id, factors, batch_branch,
                 # Include batch_plan in this tuple.
                 batch_plan) in batches:
                # Set factor_ids to a tuple built from a lazy sequence of item.decision_event_id for item in
                # factors.
                factor_ids = tuple(item.decision_event_id for item in factors)
                # Set proposer to a tuple built from a lazy sequence of item for item in factors; retain entries
                # satisfying item.role equals the text 'PROPOSER'.
                proposer = tuple(item for item in factors if item.role == "PROPOSER")
                # Set responder to a tuple built from a lazy sequence of item for item in factors; retain entries
                # satisfying item.role equals the text 'RESPONDER'.
                responder = tuple(item for item in factors if item.role == "RESPONDER")
                # Append the result of CoupledNegotiationDecisionBatch(batch_id, episode_id,
                # specification.scenario_id, timestamp, source_id, a tuple built from a lazy...) to final_batches.
                final_batches.append(CoupledNegotiationDecisionBatch(
                    # Supply specification.scenario_id to CoupledNegotiationDecisionBatch.
                    batch_id, episode_id, specification.scenario_id, timestamp,
                    # Supply a tuple built from a lazy sequence of item.decision_event_id for item in proposer to
                    # CoupledNegotiationDecisionBatch.
                    source_id, tuple(item.decision_event_id for item in proposer),
                    # Supply a tuple built from a lazy sequence of item.decision_event_id for item in proposer to
                    # CoupledNegotiationDecisionBatch.
                    tuple(item.decision_event_id for item in proposer),
                    # Supply batch_branch.proposer_assignment.proposals_created to
                    # CoupledNegotiationDecisionBatch.
                    batch_branch.proposer_assignment.proposals_created,
                    # Supply a tuple built from a lazy sequence of item.decision_event_id for item in responder to
                    # CoupledNegotiationDecisionBatch.
                    tuple(item.decision_event_id for item in responder),
                    # Supply a tuple built from a lazy sequence of item.decision_event_id for item in responder to
                    # CoupledNegotiationDecisionBatch.
                    tuple(item.decision_event_id for item in responder),
                    # Supply a tuple containing source_id, the text 'PROTOCOL_RESOLUTION' to
                    # CoupledNegotiationDecisionBatch.
                    (source_id, "PROTOCOL_RESOLUTION"),
                    # Supply a tuple containing source_id, batch_branch.effective_precedence_graph to
                    # CoupledNegotiationDecisionBatch.
                    (source_id, batch_branch.effective_precedence_graph),
                    # Supply EPISODE_DURATION_SECONDS to CoupledNegotiationDecisionBatch.
                    batch_plan.plan_id, 0.0, EPISODE_DURATION_SECONDS, None,
                    # Supply factors to CoupledNegotiationDecisionBatch.
                    "EPISODE_TERMINATED", reward, factors,
                    # Supply a tuple built from encoded_shapes to CoupledNegotiationDecisionBatch.
                    tuple(encoded_shapes),
                    # Supply a tuple containing the sum of a lazy sequence of shape[0][0] for shape in
                    # encoded_shapes, encoded_shapes[0][0] at 1 when... when the requested attribute of
                    # self.action_provider, otherwise a tuple containing 0, 0 to CoupledNegotiationDecisionBatch.
                    ((sum(shape[0][0] for shape in encoded_shapes),
                      # Include encoded_shapes[0][0] at 1 when encoded_shapes, otherwise 0 in this tuple.
                      encoded_shapes[0][0][1] if encoded_shapes else 0)
                     # Evaluate the requested attribute of self.action_provider as part of the enclosing
                     # expression.
                     if getattr(self.action_provider,
                                # Supply the text 'runtime_critic_enabled' to the enclosing expression.
                                "runtime_critic_enabled", True)
                     # Evaluate a tuple containing 0, 0 as part of the enclosing expression.
                     else (0, 0)),
                    # Store 1 under 'joint_physical_consequences'.
                    {"joint_physical_consequences": 1,
                     "reward_definition": "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1"}))
            # Set factors to a tuple built from a lazy sequence of item for batch in final_batches.
            factors = tuple(item for batch in final_batches
                            # Evaluate batch.policy_factors as part of the enclosing expression.
                            for item in batch.policy_factors)
            # Return the result of CoupledNegotiationEpisodeRecord(episode_id, specification.scenario_id,
            # scenario_manifest_id, a tuple built from final_batches,...) to the caller.
            return CoupledNegotiationEpisodeRecord(
                # Supply specification.scenario_id to CoupledNegotiationEpisodeRecord.
                episode_id, specification.scenario_id, scenario_manifest_id,
                # Supply a tuple built from final_batches to CoupledNegotiationEpisodeRecord.
                tuple(final_batches), len(factors),
                # Supply the sum of a lazy sequence of item.role equals the text 'PROPOSER' for item in factors to
                # CoupledNegotiationEpisodeRecord.
                sum(item.role == "PROPOSER" for item in factors),
                # Supply the sum of a lazy sequence of item.role equals the text 'RESPONDER' for item in factors
                # to CoupledNegotiationEpisodeRecord.
                sum(item.role == "RESPONDER" for item in factors),
                # Supply the sum of a lazy sequence of the number of entries in item.policy_factors is greater
                # than 1 for item in final_batches to CoupledNegotiationEpisodeRecord.
                sum(len(item.policy_factors) > 1 for item in final_batches),
                # Supply environment.current_time to CoupledNegotiationEpisodeRecord.
                environment.step_count, environment.current_time,
                # Supply the number of entries in specification.movement_path_ids to
                # CoupledNegotiationEpisodeRecord.
                perf_counter() - started, len(specification.movement_path_ids),
                # Supply the number of entries in completion_events to CoupledNegotiationEpisodeRecord.
                len(completion_events),
                # Supply the sum of a lazy sequence of item at 2 equals the text 'PRECEDENCE_SPEED_CAP' for item
                # in commands to CoupledNegotiationEpisodeRecord.
                sum(item[2] == "PRECEDENCE_SPEED_CAP" for item in commands),
                # Supply the number of entries in native_events to CoupledNegotiationEpisodeRecord.
                plan_count, len(native_events), team_time, reward, reward, 0, 0,
                # Supply completion_status to CoupledNegotiationEpisodeRecord.
                completion_status,
                # Store True under 'collision_free'.
                # Store True under 'blocked_zone_invariant'.
                {"collision_free": True, "blocked_zone_invariant": True,
                 # Store True under 'safe_sumo_speed_mode'.
                 # Store True under 'reward_reconciled'.
                 "safe_sumo_speed_mode": True, "reward_reconciled": True},
                # Store self.action_provider.selection_rule under 'action_provider'.
                {"action_provider": self.action_provider.selection_rule,
                 # Store False under 'outcome_data_used'.
                 # Store True under 'fresh_sumo_process'.
                 "outcome_data_used": False, "fresh_sumo_process": True,
                 # Store True under 'fresh_ldm_state'.
                 # Store True under 'fresh_protocol_bus'.
                 "fresh_ldm_state": True, "fresh_protocol_bus": True,
                 # Store True under 'fresh_demand_ledger'.
                 # Store 0 under 'optimizer_instances'.
                 "fresh_demand_ledger": True, "optimizer_instances": 0,
                 # Store 0 under 'backward_calls'.
                 # Store 0 under 'parameter_updates'.
                 "backward_calls": 0, "parameter_updates": 0,
                 # Store unresolved_reason under 'unresolved_coordination_reason'.
                 "unresolved_coordination_reason": unresolved_reason,
                 # Store 0 under 'fabricated_negotiation_branches'.
                 "fabricated_negotiation_branches": 0,
                 # Store 0 under 'vehicle_id_priority_decisions'.
                 "vehicle_id_priority_decisions": 0,
                 # Store the requested attribute of self.action_provider under 'neural_actor_calls'.
                 "neural_actor_calls": getattr(
                     # Supply self.action_provider to getattr.
                     self.action_provider, "neural_actor_calls", None),
                 # Store event_driven under 'event_driven_renegotiation'.
                 "event_driven_renegotiation": event_driven,
                 # Store a dictionary containing scheduled_vehicles, completed_vehicles, unfinished_vehicles,
                 # unfinished_vehicle_ids,... under 'liveness_metrics'.
                 "liveness_metrics": {
                     # Evaluate liveness as part of the enclosing expression.
                     **liveness,
                     # Store the number of entries in movements under 'scheduled_vehicles'.
                     "scheduled_vehicles": len(movements),
                     # Store the number of entries in completion_events under 'completed_vehicles'.
                     "completed_vehicles": len(completion_events),
                     # Store the number of entries in unfinished_vehicle_ids under 'unfinished_vehicles'.
                     "unfinished_vehicles": len(unfinished_vehicle_ids),
                     # Store unfinished_vehicle_ids under 'unfinished_vehicle_ids'.
                     "unfinished_vehicle_ids": unfinished_vehicle_ids,
                     "all_scheduled_vehicles_completed":
                         # Evaluate the negation of unfinished_vehicle_ids as part of the enclosing expression.
                         not unfinished_vehicle_ids},
                 # Store a tuple built from diagnostics under 'liveness_diagnostics'.
                 "liveness_diagnostics": tuple(diagnostics)})
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Call environment.close with the supplied arguments.
            environment.close()
