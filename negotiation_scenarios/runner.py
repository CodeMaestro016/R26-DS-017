"""Dedicated real-SUMO runner for Step 5J.2A; never used by ``main.py``."""

from dataclasses import asdict
from pathlib import Path
import xml.etree.ElementTree as ET

import traci

from config import (AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP,
                    SUMO_NETWORK_FILE)
from conflict import (ConflictGraphManager, ConflictZoneManager, MapPathManager,
                      ConflictZoneOccupancyAssessor)
from conflict_entry_monitor import conflict_entry_monitor
from environment import SUMOEnv
from negotiation_learning import (GraphTensorEncoder, NegotiationEnvironment,
                                  V2VPrecedenceClaimBus)
from negotiation_learning.claim_semantics import NegotiationClaimBuilder
from negotiation_learning.protocol import (ClaimRelinquishmentProtocol,
    NegotiationResponseCandidateBuilder, ProposalResponse)
from observation import ObservationManager, observation_manager
from predictor import IntentionPredictor
from traffic_rules import TrafficRuleEngine

from .catalogue import network_identity
from .models import (DETERMINISTIC_COVERAGE_ENUMERATION,
    LiveNegotiationCoverageRecord, MovementTimingCalibrationRecord,
    NegotiationScenarioProtocolTrace)


def derive_route_edges(path_manager, movement_path_id):
    """Derive SUMO route edges from discovered path lane metadata."""
    path = path_manager.paths[movement_path_id]
    incoming = path_manager.network.getLane(path.incoming_lane_id).getEdge().getID()
    outgoing = path_manager.network.getLane(path.outgoing_lane_id).getEdge().getID()
    return incoming, outgoing


def derive_existing_route_id(path_manager, movement_path_id):
    """Resolve, rather than name-assume, the loaded route for a map path."""
    required_edges = tuple(derive_route_edges(path_manager, movement_path_id))
    matches = tuple(sorted(
        route_id for route_id in traci.route.getIDList()
        if tuple(traci.route.getEdges(route_id)) == required_edges))
    if len(matches) != 1:
        raise RuntimeError("MOVEMENT_PATH_ROUTE_IDENTITY_UNRESOLVED")
    return matches[0]


def _add_vehicle(vehicle_id, route_id):
    traci.vehicle.add(vehicle_id, route_id, AV_TYPE_ID, departSpeed="max",
                      departLane="free", departPos="base")
    traci.vehicle.setSpeedMode(vehicle_id, SAFE_SUMO_SPEED_MODE)


def calibrate_movement(path_manager, movement_path_id):
    """Measure departure to the existing ObservationManager approach event."""
    environment = SUMOEnv(use_gui=False)
    route_id = "CALIBRATION_ROUTE"
    vehicle_id = "CALIBRATION_AV"
    try:
        environment.start()
        traci.route.add(route_id, derive_route_edges(path_manager, movement_path_id))
        _add_vehicle(vehicle_id, route_id)
        actual_departure_step = None
        while traci.simulation.getMinExpectedNumber() > 0:
            states = environment.step()
            if vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                actual_departure_step = environment.step_count
            state = states.get(vehicle_id)
            if state is not None and ObservationManager.is_in_approach_zone(
                    state["position"]):
                if actual_departure_step is None:
                    raise RuntimeError("SYNCHRONIZATION_EVENT_BEFORE_DEPARTURE")
                event_step = environment.step_count
                delta = event_step - actual_departure_step
                return MovementTimingCalibrationRecord(
                    movement_path_id, repr(derive_route_edges(path_manager, movement_path_id)),
                    SIM_TIME_STEP, 0, actual_departure_step, event_step, delta,
                    delta * SIM_TIME_STEP, AV_TYPE_ID, network_identity(),
                    {"event": "ObservationManager.is_in_approach_zone(position)",
                     "event_semantics": "ldm.in_approach_zone",
                     "measurement_source": "REAL_SUMO_ISOLATED_ROUTE"},
                )
        raise RuntimeError("NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED")
    finally:
        environment.close()


class RealSumoNegotiationScenarioRunner:
    """Run a derived schedule through the same operational shadow pipeline."""

    def __init__(self, path_manager=None):
        self.paths = path_manager or MapPathManager()

    def run(self, specification):
        zones = ConflictZoneManager(self.paths)
        conflict_graphs = ConflictGraphManager(self.paths, zones)
        occupancy = ConflictZoneOccupancyAssessor(self.paths, zones)
        rules = TrafficRuleEngine(self.paths)
        environment_logic = NegotiationEnvironment()
        claims = V2VPrecedenceClaimBus()
        encoder = GraphTensorEncoder()
        predictor = IntentionPredictor()
        environment = SUMOEnv(use_gui=False)
        observation_manager.reset()
        conflict_entry_monitor.reset()
        pending = list(zip(specification.scheduled_spawn_steps,
                           specification.movement_path_ids))
        records, traces = [], []
        seen_snapshots = set()
        try:
            environment.start()
            route_by_path = {
                path_id: derive_existing_route_id(self.paths, path_id)
                for path_id in specification.movement_path_ids
            }
            while pending or traci.simulation.getMinExpectedNumber() > 0:
                due = [item for item in pending if item[0] <= environment.step_count]
                for _, path_id in due:
                    index = specification.movement_path_ids.index(path_id)
                    vehicle_id = f"SCENARIO_AV_{index}"
                    _add_vehicle(vehicle_id, route_by_path[path_id])
                    observation_manager.get_or_create_ldm(vehicle_id)
                    pending.remove((_, path_id))
                observations = environment.step()
                now = environment.current_time
                observation_manager.update(observations, now)
                evaluation_truth = {vehicle_id: state.get("route_id", "")
                                    for vehicle_id, state in observations.items()}
                for ego_id in observations:
                    ldm = observation_manager.get_ldm(ego_id)
                    if ldm is not None:
                        conflict_entry_monitor.update_ldm(
                            ldm, now, predictor, evaluation_truth)
                claims.begin_step(now)
                local = {}
                for ego_id in observations:
                    ldm = observation_manager.get_ldm(ego_id)
                    if ldm is None or not ldm.in_approach_zone:
                        continue
                    ldm.current_conflict_graph = conflict_graphs.build_local_graph(ldm, now)
                    ldm.current_temporal_assessment = occupancy.assess_ldm(ldm, now)
                    ldm.current_regulatory_assessment = rules.assess_ldm(ldm, now)
                    local[ego_id], messages = environment_logic.build_local_claims(ldm, now)
                    for message in messages:
                        claims.publish(message)
                claims.freeze_step(now)
                for ego_id in sorted(local):
                    ldm = observation_manager.get_ldm(ego_id)
                    snapshot = environment_logic.build_snapshot(
                        ldm, now, claims.current_messages(now, receiver_id=ego_id),
                        local[ego_id])
                    encoded = encoder.encode(snapshot["graph_observation"])
                    ldm.current_encoded_graph_observation = encoded
                    snapshot_id = (specification.scenario_id, now, ego_id)
                    if snapshot_id in seen_snapshots:
                        continue
                    seen_snapshots.add(snapshot_id)
                    live, branch_traces = self._coverage_branches(
                        specification.scenario_id, snapshot_id, snapshot, encoded)
                    records.append(live)
                    traces.extend(branch_traces)
                # A real negotiation snapshot is the semantic objective of this
                # episode; stopping here avoids allowing coverage actions to
                # influence physical traffic.
                if any(item.proposer_decision_event_ids for item in records):
                    break
            return tuple(records), tuple(traces)
        finally:
            environment.close()

    @staticmethod
    def _coverage_branches(scenario_id, snapshot_id, snapshot, encoded):
        del encoded  # graph encoding was executed; protocol remains NumPy/domain-only
        claim_set = NegotiationClaimBuilder().build(
            snapshot["ego_id"], {
                "joint_precedence_edges": snapshot["joint_precedence_edges"],
                "precedence_edges": snapshot["joint_precedence_edges"],
            }, snapshot["negotiation_status"],
            snapshot["explicit_coordination_permitted_or_required"],
            snapshot["source_snapshot_consistent"],
        )
        proposer_ids, responder_ids, response_masks, proposal_ids = [], [], [], []
        outcomes, traces = [], []
        original = tuple((item["yielding_vehicle_id"], item["priority_vehicle_id"])
                         for item in snapshot["joint_precedence_edges"])
        protocol = ClaimRelinquishmentProtocol()
        for position, (claim, mask) in enumerate(zip(
                claim_set.ego_precedence_claims, claim_set.action_masks)):
            event_id = (snapshot_id, "PROPOSER", position, claim.yielding_vehicle_id,
                        claim.priority_vehicle_id)
            # A claim is not a decision opportunity unless the authoritative
            # Boolean mask permits at least one action in this live context.
            if not any(mask.feasibility):
                continue
            proposer_ids.append(event_id)
            if mask.feasibility[0]:
                traces.append(NegotiationScenarioProtocolTrace(
                    (event_id, "KEEP"), scenario_id, snapshot_id, event_id,
                    "KEEP_CLAIM", None, None, None, "NO_PROPOSAL", original,
                    original, (snapshot["timestamp"],),
                    DETERMINISTIC_COVERAGE_ENUMERATION,
                    {"source_context": "LIVE_SUMO_DECISION_CONTEXT"}))
            if not mask.feasibility[1]:
                continue
            proposal = protocol.create_proposal(
                claim, snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1",
                claim_set.policy_authority)
            proposal_ids.append(proposal.proposal_id)
            response_candidate = NegotiationResponseCandidateBuilder.build(
                proposal.receiver_id, proposal, snapshot["joint_precedence_edges"],
                snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1",
                snapshot["source_snapshot_consistent"], True)
            response_event = (snapshot_id, "RESPONDER", proposal.proposal_id)
            responder_ids.append(response_event)
            response_masks.append(response_candidate.action_feasibility_mask)
            for response_action in (ProposalResponse.ACCEPT, ProposalResponse.REJECT):
                action_position = 0 if response_action is ProposalResponse.ACCEPT else 1
                if not response_candidate.action_feasibility_mask[action_position]:
                    continue
                response = protocol.create_response(
                    proposal, proposal.receiver_id, response_action,
                    snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
                evaluation = protocol.evaluate(
                    snapshot["joint_precedence_edges"], (proposal, response),
                    snapshot["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
                state = evaluation.state.value
                outcomes.append(state)
                traces.append(NegotiationScenarioProtocolTrace(
                    (event_id, response_action.value), scenario_id, snapshot_id,
                    event_id, "RELINQUISH_CLAIM", proposal.proposal_id,
                    response_event,
                    ("ACCEPT_RELINQUISHMENT" if response_action is ProposalResponse.ACCEPT
                     else "REJECT_RELINQUISHMENT"), state, original,
                    evaluation.effective_coordination_graph,
                    (snapshot["timestamp"],), DETERMINISTIC_COVERAGE_ENUMERATION,
                    {"source_context": "LIVE_SUMO_DECISION_CONTEXT",
                     "branch_isolation": "FRESH_PROTOCOL_EVALUATION"}))
        eligible_masks = tuple(
            item.feasibility for item in claim_set.action_masks
            if any(item.feasibility))
        live = LiveNegotiationCoverageRecord(
            scenario_id, snapshot_id, snapshot["timestamp"],
            snapshot["negotiation_status"], tuple(snapshot["participant_ids"]),
            tuple(proposer_ids), eligible_masks, tuple(responder_ids), tuple(response_masks),
            tuple(proposal_ids), tuple(outcomes),
            provenance={"context": "LIVE_SUMO_DECISION_CONTEXT",
                        "protocol_paths": "DETERMINISTIC_PROTOCOL_BRANCH_FROM_LIVE_CONTEXT",
                        "operational_route_truth_fields_consumed": "0"})
        return live, tuple(traces)
