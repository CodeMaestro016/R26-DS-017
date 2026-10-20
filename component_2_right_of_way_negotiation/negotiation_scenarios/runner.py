"""Dedicated real-SUMO runner for Step 5J.2A; never used by ``main.py``."""

# Import asdict from dataclasses for the operations below.
from dataclasses import asdict
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_NETWORK_FILE from config for the operations below.
from config import (AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP,
                    SUMO_NETWORK_FILE)
# Import ConflictGraphManager, ConflictZoneManager, MapPathManager, ConflictZoneOccupancyAssessor from conflict
# for the operations below.
from conflict import (ConflictGraphManager, ConflictZoneManager, MapPathManager,
                      ConflictZoneOccupancyAssessor)
# Import conflict_entry_monitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import conflict_entry_monitor
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import GraphTensorEncoder, NegotiationEnvironment, V2VPrecedenceClaimBus from negotiation_learning for the
# operations below.
from negotiation_learning import (GraphTensorEncoder, NegotiationEnvironment,
                                  V2VPrecedenceClaimBus)
# Import NegotiationClaimBuilder from negotiation_learning.claim_semantics for the operations below.
from negotiation_learning.claim_semantics import NegotiationClaimBuilder
# Import ClaimRelinquishmentProtocol, NegotiationResponseCandidateBuilder, ProposalResponse from
# negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import (ClaimRelinquishmentProtocol,
    NegotiationResponseCandidateBuilder, ProposalResponse)
# Import ObservationManager, observation_manager from observation for the operations below.
from observation import ObservationManager, observation_manager
# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine

# Import network_identity from .catalogue for the operations below.
from .catalogue import network_identity
# Import DETERMINISTIC_COVERAGE_ENUMERATION, LiveNegotiationCoverageRecord, MovementTimingCalibrationRecord,
# NegotiationScenarioProtocolTrace from .models for the operations below.
from .models import (DETERMINISTIC_COVERAGE_ENUMERATION,
    LiveNegotiationCoverageRecord, MovementTimingCalibrationRecord,
    NegotiationScenarioProtocolTrace)


# Derive SUMO route edges from discovered path lane metadata.
# Input path_manager: the supplied path manager.
# Input movement_path_id: the supplied movement path id.
# Output: a tuple containing incoming, outgoing.
def derive_route_edges(path_manager, movement_path_id):
    """Derive SUMO route edges from discovered path lane metadata."""
    # Set path to path_manager.paths at movement_path_id.
    path = path_manager.paths[movement_path_id]
    # Set incoming to the result of path_manager.network.getLane(path.incoming_lane_id).getEdge().getID().
    incoming = path_manager.network.getLane(path.incoming_lane_id).getEdge().getID()
    # Set outgoing to the result of path_manager.network.getLane(path.outgoing_lane_id).getEdge().getID().
    outgoing = path_manager.network.getLane(path.outgoing_lane_id).getEdge().getID()
    # Return a tuple containing incoming, outgoing to the caller.
    return incoming, outgoing


# Resolve, rather than name-assume, the loaded route for a map path.
# Input path_manager: the supplied path manager.
# Input movement_path_id: the supplied movement path id.
# Output: matches at 0.
# Processing: select branches using the stated conditions.
def derive_existing_route_id(path_manager, movement_path_id):
    """Resolve, rather than name-assume, the loaded route for a map path."""
    # Set required_edges to a tuple built from the result of derive_route_edges(path_manager, movement_path_id).
    required_edges = tuple(derive_route_edges(path_manager, movement_path_id))
    # Set matches to a tuple built from the sorted values from a lazy sequence of route_id for route_id in the
    # identifiers reported by traci.route.getIDList; retain entries satisfying
    # tuple(traci.route.getEdges(route_id)) equals required_edges.
    matches = tuple(sorted(
        # Evaluate the identifiers reported by traci.route.getIDList as part of the enclosing expression.
        route_id for route_id in traci.route.getIDList()
        # Evaluate a tuple built from the result of traci.route.getEdges(route_id) equals required_edges as part
        # of the enclosing expression.
        if tuple(traci.route.getEdges(route_id)) == required_edges))
    # Run this branch when the number of entries in matches differs from 1.
    if len(matches) != 1:
        # Raise RuntimeError with the text 'MOVEMENT_PATH_ROUTE_IDENTITY_UNRESOLVED' to stop this execution path.
        raise RuntimeError("MOVEMENT_PATH_ROUTE_IDENTITY_UNRESOLVED")
    # Return matches at 0 to the caller.
    return matches[0]


# Add vehicle using the inputs and processing steps below.
# Input vehicle_id: the identifier of the vehicle being processed.
# Input route_id: the supplied route id.
# Output: no explicit value; normal completion returns None.
def _add_vehicle(vehicle_id, route_id):
    # Add vehicle_id to traci.vehicle.
    traci.vehicle.add(vehicle_id, route_id, AV_TYPE_ID, departSpeed="max",
                      # Supply departLane as the text 'free'.
                      # Supply departPos as the text 'base'.
                      departLane="free", departPos="base")
    # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)


# Measure departure to the existing ObservationManager approach event.
# Input path_manager: the supplied path manager.
# Input movement_path_id: the supplied movement path id.
# Output: the result of MovementTimingCalibrationRecord(movement_path_id, the result of repr(the result of
# derive_route_edges(path_manager,...).
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def calibrate_movement(path_manager, movement_path_id):
    """Measure departure to the existing ObservationManager approach event."""
    # Set environment to the result of SUMOEnv().
    environment = SUMOEnv(use_gui=False)
    # Set route_id to the text 'CALIBRATION_ROUTE'.
    route_id = "CALIBRATION_ROUTE"
    # Set vehicle_id to the text 'CALIBRATION_AV'.
    vehicle_id = "CALIBRATION_AV"
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call environment.start with the supplied arguments.
        environment.start()
        # Add route_id to traci.route.
        traci.route.add(route_id, derive_route_edges(path_manager, movement_path_id))
        # Call _add_vehicle with the supplied arguments.
        _add_vehicle(vehicle_id, route_id)
        # Set actual_departure_step to None.
        actual_departure_step = None
        # Repeat the following steps while the result of traci.simulation.getMinExpectedNumber() is greater than
        # 0.
        while traci.simulation.getMinExpectedNumber() > 0:
            # Set states to the result of environment.step().
            states = environment.step()
            # Run this branch when vehicle_id belongs to environment.lifecycle_events.departed_vehicle_ids.
            if vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                # Set actual_departure_step to environment.step_count.
                actual_departure_step = environment.step_count
            # Set state to vehicle_id from states; use None if absent.
            state = states.get(vehicle_id)
            # Run this branch when state is a different object from None and the result of
            # ObservationManager.is_in_approach_zone(state at 'position').
            if state is not None and ObservationManager.is_in_approach_zone(
                    # Supply state at 'position' to ObservationManager.is_in_approach_zone.
                    state["position"]):
                # Run this branch when actual_departure_step is the same object as None.
                if actual_departure_step is None:
                    # Raise RuntimeError with the text 'SYNCHRONIZATION_EVENT_BEFORE_DEPARTURE' to stop this
                    # execution path.
                    raise RuntimeError("SYNCHRONIZATION_EVENT_BEFORE_DEPARTURE")
                # Set event_step to environment.step_count.
                event_step = environment.step_count
                # Set delta to event_step minus actual_departure_step.
                delta = event_step - actual_departure_step
                # Return the result of MovementTimingCalibrationRecord(movement_path_id, the result of repr(the
                # result of derive_route_edges(path_manager,...) to the caller.
                return MovementTimingCalibrationRecord(
                    # Supply the result of repr(the result of derive_route_edges(path_manager, movement_path_id))
                    # to MovementTimingCalibrationRecord.
                    movement_path_id, repr(derive_route_edges(path_manager, movement_path_id)),
                    # Supply actual_departure_step to MovementTimingCalibrationRecord.
                    SIM_TIME_STEP, 0, actual_departure_step, event_step, delta,
                    # Supply delta multiplied by SIM_TIME_STEP to MovementTimingCalibrationRecord.
                    delta * SIM_TIME_STEP, AV_TYPE_ID, network_identity(),
                    # Store the text 'ObservationManager.is_in_approach_zone(position)' under 'event'.
                    {"event": "ObservationManager.is_in_approach_zone(position)",
                     "event_semantics": "ldm.in_approach_zone",
                     "measurement_source": "REAL_SUMO_ISOLATED_ROUTE"},
                )
        # Raise RuntimeError with the text 'NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED' to stop this
        # execution path.
        raise RuntimeError("NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED")
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call environment.close with the supplied arguments.
        environment.close()


# Run a derived schedule through the same operational shadow pipeline.
# Instances expose the attributes and methods implemented in this class.
class RealSumoNegotiationScenarioRunner:
    """Run a derived schedule through the same operational shadow pipeline."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager=None):
        # Set self.paths to path_manager or the result of MapPathManager().
        self.paths = path_manager or MapPathManager()

    # Run using the inputs and processing steps below.
    # Input specification: the supplied specification.
    # Output: a tuple containing a tuple built from records, a tuple built from traces.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def run(self, specification):
        # Set zones to the result of ConflictZoneManager(self.paths).
        zones = ConflictZoneManager(self.paths)
        # Set conflict_graphs to the result of ConflictGraphManager(self.paths, zones).
        conflict_graphs = ConflictGraphManager(self.paths, zones)
        # Set occupancy to the result of ConflictZoneOccupancyAssessor(self.paths, zones).
        occupancy = ConflictZoneOccupancyAssessor(self.paths, zones)
        # Set rules to the result of TrafficRuleEngine(self.paths).
        rules = TrafficRuleEngine(self.paths)
        # Set environment_logic to the result of NegotiationEnvironment().
        environment_logic = NegotiationEnvironment()
        # Set claims to the result of V2VPrecedenceClaimBus().
        claims = V2VPrecedenceClaimBus()
        # Set encoder to the result of GraphTensorEncoder().
        encoder = GraphTensorEncoder()
        # Set predictor to the result of IntentionPredictor().
        predictor = IntentionPredictor()
        # Set environment to the result of SUMOEnv().
        environment = SUMOEnv(use_gui=False)
        # Call observation_manager.reset with the supplied arguments.
        observation_manager.reset()
        # Call conflict_entry_monitor.reset with the supplied arguments.
        conflict_entry_monitor.reset()
        # Set pending to a list built from corresponding items paired from specification.scheduled_spawn_steps,
        # specification.movement_path_ids.
        pending = list(zip(specification.scheduled_spawn_steps,
                           # Supply specification.movement_path_ids to zip.
                           specification.movement_path_ids))
        # Set (records, traces) to a tuple containing an empty list, an empty list.
        records, traces = [], []
        # Set seen_snapshots to an empty set.
        seen_snapshots = set()
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call environment.start with the supplied arguments.
            environment.start()
            # Set route_by_path to a dictionary of path_id mapped to the result of
            # derive_existing_route_id(self.paths, path_id) for path_id in specification.movement_path_ids.
            route_by_path = {
                # Evaluate the result of derive_existing_route_id(self.paths, path_id) as part of the enclosing
                # expression.
                path_id: derive_existing_route_id(self.paths, path_id)
                # Evaluate specification.movement_path_ids as part of the enclosing expression.
                for path_id in specification.movement_path_ids
            }
            # Repeat the following steps while pending or the result of traci.simulation.getMinExpectedNumber() is
            # greater than 0.
            while pending or traci.simulation.getMinExpectedNumber() > 0:
                # Set due to a list of item for item in pending; retain entries satisfying item at 0 is at most
                # environment.step_count.
                due = [item for item in pending if item[0] <= environment.step_count]
                # Iterate over due, binding each item to (_, path_id).
                for _, path_id in due:
                    # Set index to the result of specification.movement_path_ids.index(path_id).
                    index = specification.movement_path_ids.index(path_id)
                    # Set vehicle_id to formatted text built from the embedded values.
                    vehicle_id = f"SCENARIO_AV_{index}"
                    # Call _add_vehicle with the supplied arguments.
                    _add_vehicle(vehicle_id, route_by_path[path_id])
                    # Call observation_manager.get_or_create_ldm with the supplied arguments.
                    observation_manager.get_or_create_ldm(vehicle_id)
                    # Remove a tuple containing _, path_id from pending.
                    pending.remove((_, path_id))
                # Set observations to the result of environment.step().
                observations = environment.step()
                # Set now to environment.current_time.
                now = environment.current_time
                # Update observation_manager with the supplied entries.
                observation_manager.update(observations, now)
                # Set evaluation_truth to a dictionary of vehicle_id mapped to 'route_id' from state; use the text
                # '' if absent for (vehicle_id, state) in key/value pairs from observations.
                evaluation_truth = {vehicle_id: state.get("route_id", "")
                                    # Evaluate key/value pairs from observations as part of the enclosing
                                    # expression.
                                    for vehicle_id, state in observations.items()}
                # Iterate over observations, binding each item to ego_id.
                for ego_id in observations:
                    # Set ldm to the result of observation_manager.get_ldm(ego_id).
                    ldm = observation_manager.get_ldm(ego_id)
                    # Run this branch when ldm is a different object from None.
                    if ldm is not None:
                        # Call conflict_entry_monitor.update_ldm with the supplied arguments.
                        conflict_entry_monitor.update_ldm(
                            # Supply evaluation_truth to conflict_entry_monitor.update_ldm.
                            ldm, now, predictor, evaluation_truth)
                # Call claims.begin_step with the supplied arguments.
                claims.begin_step(now)
                # Set local to an empty dictionary.
                local = {}
                # Iterate over observations, binding each item to ego_id.
                for ego_id in observations:
                    # Set ldm to the result of observation_manager.get_ldm(ego_id).
                    ldm = observation_manager.get_ldm(ego_id)
                    # Run this branch when ldm is the same object as None or the negation of ldm.in_approach_zone.
                    if ldm is None or not ldm.in_approach_zone:
                        # Skip the rest of this loop iteration and process the next item.
                        continue
                    # Set ldm.current_conflict_graph to the result of conflict_graphs.build_local_graph(ldm, now).
                    ldm.current_conflict_graph = conflict_graphs.build_local_graph(ldm, now)
                    # Set ldm.current_temporal_assessment to the result of occupancy.assess_ldm(ldm, now).
                    ldm.current_temporal_assessment = occupancy.assess_ldm(ldm, now)
                    # Set ldm.current_regulatory_assessment to the result of rules.assess_ldm(ldm, now).
                    ldm.current_regulatory_assessment = rules.assess_ldm(ldm, now)
                    # Set (local[ego_id], messages) to the result of environment_logic.build_local_claims(ldm,
                    # now).
                    local[ego_id], messages = environment_logic.build_local_claims(ldm, now)
                    # Iterate over messages, binding each item to message.
                    for message in messages:
                        # Call claims.publish with the supplied arguments.
                        claims.publish(message)
                # Call claims.freeze_step with the supplied arguments.
                claims.freeze_step(now)
                # Iterate over the sorted values from local, binding each item to ego_id.
                for ego_id in sorted(local):
                    # Set ldm to the result of observation_manager.get_ldm(ego_id).
                    ldm = observation_manager.get_ldm(ego_id)
                    # Set snapshot to the result of environment_logic.build_snapshot(ldm, now, the result of
                    # claims.current_messages(now), local at ego_id).
                    snapshot = environment_logic.build_snapshot(
                        # Supply receiver_id as ego_id.
                        ldm, now, claims.current_messages(now, receiver_id=ego_id),
                        # Supply local at ego_id to environment_logic.build_snapshot.
                        local[ego_id])
                    # Set encoded to the result of encoder.encode(snapshot at 'graph_observation').
                    encoded = encoder.encode(snapshot["graph_observation"])
                    # Set ldm.current_encoded_graph_observation to encoded.
                    ldm.current_encoded_graph_observation = encoded
                    # Set snapshot_id to a tuple containing specification.scenario_id, now, ego_id.
                    snapshot_id = (specification.scenario_id, now, ego_id)
                    # Run this branch when snapshot_id belongs to seen_snapshots.
                    if snapshot_id in seen_snapshots:
                        # Skip the rest of this loop iteration and process the next item.
                        continue
                    # Add snapshot_id to seen_snapshots.
                    seen_snapshots.add(snapshot_id)
                    # Set (live, branch_traces) to the result of
                    # self._coverage_branches(specification.scenario_id, snapshot_id, snapshot, encoded).
                    live, branch_traces = self._coverage_branches(
                        # Supply specification.scenario_id to self._coverage_branches.
                        specification.scenario_id, snapshot_id, snapshot, encoded)
                    # Append live to records.
                    records.append(live)
                    # Extend traces with branch_traces.
                    traces.extend(branch_traces)
                # A real negotiation snapshot is the semantic objective of this
                # episode; stopping here avoids allowing coverage actions to
                # influence physical traffic.
                # Run this branch when whether any item is true in a lazy sequence of
                # item.proposer_decision_event_ids for item in records.
                if any(item.proposer_decision_event_ids for item in records):
                    # Leave the nearest enclosing loop immediately.
                    break
            # Return a tuple containing a tuple built from records, a tuple built from traces to the caller.
            return tuple(records), tuple(traces)
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Call environment.close with the supplied arguments.
            environment.close()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Coverage branches using the inputs and processing steps below.
    # Input scenario_id: the supplied scenario id.
    # Input snapshot_id: the supplied snapshot id.
    # Input snapshot: the supplied snapshot.
    # Input encoded: the supplied encoded.
    # Output: a tuple containing live, a tuple built from traces.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _coverage_branches(scenario_id, snapshot_id, snapshot, encoded):
        # Delete encoded from its containing namespace or collection.
        del encoded  # graph encoding was executed; protocol remains NumPy/domain-only
        # Set claim_set to the result of NegotiationClaimBuilder().build(snapshot at 'ego_id', a dictionary
        # containing joint_precedence_edges, precedence_edges, snapshot...).
        claim_set = NegotiationClaimBuilder().build(
            # Supply a dictionary containing joint_precedence_edges, precedence_edges to
            # NegotiationClaimBuilder().build.
            snapshot["ego_id"], {
                # Store snapshot at 'joint_precedence_edges' under 'joint_precedence_edges'.
                "joint_precedence_edges": snapshot["joint_precedence_edges"],
                # Store snapshot at 'joint_precedence_edges' under 'precedence_edges'.
                "precedence_edges": snapshot["joint_precedence_edges"],
            # Supply snapshot at 'negotiation_status' to NegotiationClaimBuilder().build.
            }, snapshot["negotiation_status"],
            # Supply snapshot at 'explicit_coordination_permitted_or_required' to NegotiationClaimBuilder().build.
            snapshot["explicit_coordination_permitted_or_required"],
            # Supply snapshot at 'source_snapshot_consistent' to NegotiationClaimBuilder().build.
            snapshot["source_snapshot_consistent"],
        )
        # Set (proposer_ids, responder_ids, response_masks, proposal_ids) to a tuple containing an empty list, an
        # empty list, an empty list, an empty list.
        proposer_ids, responder_ids, response_masks, proposal_ids = [], [], [], []
        # Set (outcomes, traces) to a tuple containing an empty list, an empty list.
        outcomes, traces = [], []
        # Set original to a tuple built from a lazy sequence of a tuple containing item at 'yielding_vehicle_id',
        # item at 'priority_vehicle_id' for item in snapshot at 'joint_precedence_edges'.
        original = tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                         # Evaluate snapshot at 'joint_precedence_edges' as part of the enclosing expression.
                         for item in snapshot["joint_precedence_edges"])
        # Set protocol to the result of ClaimRelinquishmentProtocol().
        protocol = ClaimRelinquishmentProtocol()
        # Iterate over index/value pairs from corresponding items paired from claim_set.ego_precedence_claims,
        # claim_set.action_masks, binding each item to (position, (claim, mask)).
        for position, (claim, mask) in enumerate(zip(
                # Supply claim_set.ego_precedence_claims to zip.
                claim_set.ego_precedence_claims, claim_set.action_masks)):
            # Set event_id to a tuple containing snapshot_id, the text 'PROPOSER', position,
            # claim.yielding_vehicle_id, claim.priority_vehicle_id.
            event_id = (snapshot_id, "PROPOSER", position, claim.yielding_vehicle_id,
                        # Include claim.priority_vehicle_id in this tuple.
                        claim.priority_vehicle_id)
            # A claim is not a decision opportunity unless the authoritative
            # Boolean mask permits at least one action in this live context.
            # Run this branch when the negation of whether any item is true in mask.feasibility.
            if not any(mask.feasibility):
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Append event_id to proposer_ids.
            proposer_ids.append(event_id)
            # Run this branch when mask.feasibility at 0.
            if mask.feasibility[0]:
                # Append the result of NegotiationScenarioProtocolTrace(a tuple containing event_id, the text
                # 'KEEP', scenario_id, snapshot_id, event_id, the text...) to traces.
                traces.append(NegotiationScenarioProtocolTrace(
                    # Supply a tuple containing event_id, the text 'KEEP' to NegotiationScenarioProtocolTrace.
                    (event_id, "KEEP"), scenario_id, snapshot_id, event_id,
                    # Supply original to NegotiationScenarioProtocolTrace.
                    "KEEP_CLAIM", None, None, None, "NO_PROPOSAL", original,
                    # Supply a tuple containing snapshot at 'timestamp' to NegotiationScenarioProtocolTrace.
                    original, (snapshot["timestamp"],),
                    # Supply DETERMINISTIC_COVERAGE_ENUMERATION to NegotiationScenarioProtocolTrace.
                    DETERMINISTIC_COVERAGE_ENUMERATION,
                    # Store the text 'LIVE_SUMO_DECISION_CONTEXT' under 'source_context'.
                    {"source_context": "LIVE_SUMO_DECISION_CONTEXT"}))
            # Run this branch when the negation of mask.feasibility at 1.
            if not mask.feasibility[1]:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set proposal to the result of protocol.create_proposal(claim, snapshot at 'timestamp', the text
            # 'DE_STVO_UNCONTROLLED_4WAY_V1', claim_set.policy_authority).
            proposal = protocol.create_proposal(
                # Supply snapshot at 'timestamp' to protocol.create_proposal.
                claim, snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1",
                # Supply claim_set.policy_authority to protocol.create_proposal.
                claim_set.policy_authority)
            # Append proposal.proposal_id to proposal_ids.
            proposal_ids.append(proposal.proposal_id)
            # Set response_candidate to the result of
            # NegotiationResponseCandidateBuilder.build(proposal.receiver_id, proposal, snapshot at
            # 'joint_precedence_edges', snapshot at 'timestamp',...).
            response_candidate = NegotiationResponseCandidateBuilder.build(
                # Supply snapshot at 'joint_precedence_edges' to NegotiationResponseCandidateBuilder.build.
                proposal.receiver_id, proposal, snapshot["joint_precedence_edges"],
                # Supply snapshot at 'timestamp' to NegotiationResponseCandidateBuilder.build.
                snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1",
                # Supply snapshot at 'source_snapshot_consistent' to NegotiationResponseCandidateBuilder.build.
                snapshot["source_snapshot_consistent"], True)
            # Set response_event to a tuple containing snapshot_id, the text 'RESPONDER', proposal.proposal_id.
            response_event = (snapshot_id, "RESPONDER", proposal.proposal_id)
            # Append response_event to responder_ids.
            responder_ids.append(response_event)
            # Append response_candidate.action_feasibility_mask to response_masks.
            response_masks.append(response_candidate.action_feasibility_mask)
            # Iterate over a tuple containing ProposalResponse.ACCEPT, ProposalResponse.REJECT, binding each item
            # to response_action.
            for response_action in (ProposalResponse.ACCEPT, ProposalResponse.REJECT):
                # Set action_position to 0 when response_action is the same object as ProposalResponse.ACCEPT,
                # otherwise 1.
                action_position = 0 if response_action is ProposalResponse.ACCEPT else 1
                # Run this branch when the negation of response_candidate.action_feasibility_mask at
                # action_position.
                if not response_candidate.action_feasibility_mask[action_position]:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set response to the result of protocol.create_response(proposal, proposal.receiver_id,
                # response_action, snapshot at 'timestamp', the text...).
                response = protocol.create_response(
                    # Supply proposal.receiver_id to protocol.create_response.
                    proposal, proposal.receiver_id, response_action,
                    # Supply snapshot at 'timestamp' to protocol.create_response.
                    snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
                # Set evaluation to the result of protocol.evaluate(snapshot at 'joint_precedence_edges', a tuple
                # containing proposal, response, snapshot at...).
                evaluation = protocol.evaluate(
                    # Supply snapshot at 'joint_precedence_edges' to protocol.evaluate.
                    snapshot["joint_precedence_edges"], (proposal, response),
                    # Supply snapshot at 'timestamp' to protocol.evaluate.
                    snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
                # Set state to evaluation.state.value.
                state = evaluation.state.value
                # Append state to outcomes.
                outcomes.append(state)
                # Append the result of NegotiationScenarioProtocolTrace(a tuple containing event_id,
                # response_action.value, scenario_id, snapshot_id, event_id, the text...) to traces.
                traces.append(NegotiationScenarioProtocolTrace(
                    # Supply a tuple containing event_id, response_action.value to
                    # NegotiationScenarioProtocolTrace.
                    (event_id, response_action.value), scenario_id, snapshot_id,
                    # Supply proposal.proposal_id to NegotiationScenarioProtocolTrace.
                    event_id, "RELINQUISH_CLAIM", proposal.proposal_id,
                    # Supply response_event to NegotiationScenarioProtocolTrace.
                    response_event,
                    # Supply the text 'ACCEPT_RELINQUISHMENT' when response_action is the same object as
                    # ProposalResponse.ACCEPT, otherwise the text 'REJECT_RELINQUISHMENT' to
                    # NegotiationScenarioProtocolTrace.
                    ("ACCEPT_RELINQUISHMENT" if response_action is ProposalResponse.ACCEPT
                     # Supply original to NegotiationScenarioProtocolTrace.
                     else "REJECT_RELINQUISHMENT"), state, original,
                    # Supply evaluation.effective_coordination_graph to NegotiationScenarioProtocolTrace.
                    evaluation.effective_coordination_graph,
                    # Supply DETERMINISTIC_COVERAGE_ENUMERATION to NegotiationScenarioProtocolTrace.
                    (snapshot["timestamp"],), DETERMINISTIC_COVERAGE_ENUMERATION,
                    # Store the text 'LIVE_SUMO_DECISION_CONTEXT' under 'source_context'.
                    {"source_context": "LIVE_SUMO_DECISION_CONTEXT",
                     "branch_isolation": "FRESH_PROTOCOL_EVALUATION"}))
        # Set eligible_masks to a tuple built from a lazy sequence of item.feasibility for item in
        # claim_set.action_masks; retain entries satisfying whether any item is true in item.feasibility.
        eligible_masks = tuple(
            # Evaluate claim_set.action_masks as part of the enclosing expression.
            item.feasibility for item in claim_set.action_masks
            # Evaluate whether any item is true in item.feasibility as part of the enclosing expression.
            if any(item.feasibility))
        # Set live to the result of LiveNegotiationCoverageRecord(scenario_id, snapshot_id, snapshot at
        # 'timestamp', snapshot at 'negotiation_status', a tuple...).
        live = LiveNegotiationCoverageRecord(
            # Supply snapshot at 'timestamp' to LiveNegotiationCoverageRecord.
            scenario_id, snapshot_id, snapshot["timestamp"],
            # Supply a tuple built from snapshot at 'participant_ids' to LiveNegotiationCoverageRecord.
            snapshot["negotiation_status"], tuple(snapshot["participant_ids"]),
            # Supply a tuple built from response_masks to LiveNegotiationCoverageRecord.
            tuple(proposer_ids), eligible_masks, tuple(responder_ids), tuple(response_masks),
            # Supply a tuple built from proposal_ids to LiveNegotiationCoverageRecord.
            tuple(proposal_ids), tuple(outcomes),
            # Store the text 'LIVE_SUMO_DECISION_CONTEXT' under 'context'.
            provenance={"context": "LIVE_SUMO_DECISION_CONTEXT",
                        "protocol_paths": "DETERMINISTIC_PROTOCOL_BRANCH_FROM_LIVE_CONTEXT",
                        "operational_route_truth_fields_consumed": "0"})
        # Return a tuple containing live, a tuple built from traces to the caller.
        return live, tuple(traces)
