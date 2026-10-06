"""Ego-owned physical execution using pair commitments and fresh V2V state.

The ideal same-step channel transports each sender's OWN execution metadata.
These messages never enter an actor observation. No global graph, critic, or
another ego's private observation is an input to this controller.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from conflict import ConflictZoneOccupancyAssessor
from negotiation_learning.v2v_claim_bus import same_instant
from .controller import build_sumo_native_speed_constraint


@dataclass(frozen=True)
class ExecutionStateMessage:
    sender_id: str
    movement_path_id: str
    state: Mapping
    timestamp: float

    def __post_init__(self):
        # Sender-owned physical metadata only; private actor observations and
        # simulator route truth are not transported by this execution channel.
        physical_fields = {"position", "heading_radians", "lane_id", "lane_position",
            "lane_length", "road_id", "length", "width", "speed", "progress"}
        object.__setattr__(self, "state", MappingProxyType({
            key: value for key, value in self.state.items() if key in physical_fields}))


@dataclass(frozen=True)
class EgoCoordinationCommitment:
    yielding_vehicle_id: str
    priority_vehicle_id: str
    agreement_id: tuple


@dataclass(frozen=True)
class EgoExecutionContext:
    ego_id: str
    ego_state: Mapping
    movement_path_id: str
    timestamp: float
    commitments: tuple = ()
    peer_messages: tuple = ()
    coordination_complete: bool = False
    coordination_timestamp: float | None = None
    negotiation_eligible: bool = True

    def __post_init__(self):
        object.__setattr__(self, "ego_state", MappingProxyType(dict(self.ego_state)))
        if any(self.ego_id not in (c.yielding_vehicle_id, c.priority_vehicle_id)
               for c in self.commitments):
            raise ValueError("NONLOCAL_EXECUTION_COMMITMENT")


@dataclass(frozen=True)
class EgoExecutionDecision:
    ego_id: str
    permission: str
    reason: str
    blocked_zones: tuple = ()  # (zone_id, distance_to_entry, priority_id)
    speed_constraints: tuple = ()
    requested_speed_mps: float | None = None
    decentralized_execution: bool = True
    centralized_execution_graph_used_for_control: bool = False


class DecentralizedEgoExecutionController:
    def __init__(self, path_manager, zone_manager):
        self.paths, self.zones = path_manager, zone_manager
        self._previous_blocked_zones = set()
        self._blocked_entry_progress = {}
        self._ego_id = None

    def decide(self, context):
        """Return only this ego's permission, before any TraCI mutation."""
        ego = context.ego_id
        if self._ego_id is not None and self._ego_id != ego:
            raise ValueError("EXECUTION_CONTROLLER_EGO_MISMATCH")
        self._ego_id = ego
        if not context.negotiation_eligible:
            return EgoExecutionDecision(ego, "NATIVE_FOLLOWING", "FOLLOWER")
        path = self.paths.paths[context.movement_path_id]
        progress, _, error = self.paths.resolve_front_bumper_path_progress(
            context.ego_state, path)
        if error:
            return EgoExecutionDecision(ego, "SAFE_HOLD", error,
                                        (("JUNCTION_ENTRY", 0.0, ""),))
        if any(progress >= entry for entry in self._blocked_entry_progress.values()):
            raise RuntimeError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
        # An ego whose rear has cleared the junction no longer needs permission.
        if (context.ego_state["lane_id"] == path.outgoing_lane_id and
                context.ego_state["lane_position"] > context.ego_state["length"]):
            return EgoExecutionDecision(ego, "PERMITTED", "JUNCTION_CLEARED")
        def hold(reason):
            self._previous_blocked_zones = {"JUNCTION_ENTRY"}
            self._blocked_entry_progress = {"JUNCTION_ENTRY": 0.0}
            return EgoExecutionDecision(ego, "SAFE_HOLD", reason,
                (("JUNCTION_ENTRY", max(0.0, -progress), ""),))
        if not context.coordination_complete or not same_instant(
                context.timestamp, context.coordination_timestamp):
            return hold("MISSING_OR_STALE_LOCAL_COORDINATION")
        peers = {m.sender_id: m for m in context.peer_messages}
        owed = {c.priority_vehicle_id for c in context.commitments
                if c.yielding_vehicle_id == ego}
        required_peers = {c.priority_vehicle_id if c.yielding_vehicle_id == ego
                          else c.yielding_vehicle_id for c in context.commitments}
        if not required_peers.issubset(peers):
            return hold("MISSING_PRIORITY_CLEARANCE")
        blocked = []
        for peer_id, message in peers.items():
            if not same_instant(message.timestamp, context.timestamp):
                return hold("STALE_PEER_CLEARANCE")
            try:
                record = self.zones.zone_record(context.movement_path_id,
                    context.ego_state["width"], message.movement_path_id,
                    message.state["width"])
            except (KeyError, TypeError, ValueError):
                return hold("UNRESOLVED_PHYSICAL_RELATIONSHIP")
            if record is None:
                continue  # Authoritative static map: physically nonconflicting.
            peer_progress, _, error = self.paths.resolve_front_bumper_path_progress(
                message.state, self.paths.paths[message.movement_path_id])
            if error:
                return hold("UNRESOLVED_PEER_CLEARANCE")
            own_interval = record["first_path_distance_interval"]
            peer_interval = record["second_path_distance_interval"]
            own_status, error = ConflictZoneOccupancyAssessor.occupancy_state(
                progress, own_interval, context.ego_state["length"])
            peer_status, peer_error = ConflictZoneOccupancyAssessor.occupancy_state(
                peer_progress, peer_interval, message.state["length"])
            if error or peer_error:
                return hold("UNRESOLVED_ZONE_OCCUPANCY")
            if own_status == "CLEARED_ZONE":
                continue
            unresolved = peer_id in owed and peer_status != "CLEARED_ZONE"
            occupied = peer_status == "CURRENTLY_OCCUPYING"
            if own_status == "CURRENTLY_OCCUPYING":
                if record["zone_id"] in self._previous_blocked_zones:
                    raise RuntimeError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
                # Permission cannot be revoked inside an already entered zone.
                # Other approaching egos independently hold for this occupant.
                continue
            if occupied and not unresolved:
                # Clearance safety is checked at junction admission. Once
                # admitted, an ego continues clearing rather than accepting
                # a newly arriving occupancy restriction mid-junction.
                if context.ego_state["lane_id"] == path.incoming_lane_id:
                    blocked.append(("JUNCTION_ENTRY", max(0.0, -progress), peer_id))
                continue
            if unresolved:
                blocked.append((record["zone_id"],
                                max(0.0, own_interval[0] - progress), peer_id))
        self._previous_blocked_zones = {zone for zone, _, _ in blocked}
        self._blocked_entry_progress = {zone: progress + distance
                                       for zone, distance, _ in blocked}
        return EgoExecutionDecision(ego,
            "BLOCKED_BY_PRECEDENCE" if blocked else "PERMITTED",
            "UNRESOLVED_LOCAL_ZONE_OBLIGATION" if blocked else "LOCALLY_SAFE",
            tuple(blocked))

    def constrain(self, context, decision, vehicle_api, simulation_step):
        """Derive ego's own speed request using SUMO's native stopping model."""
        from dataclasses import replace
        from config import SAFE_SUMO_SPEED_MODE
        if decision.ego_id != context.ego_id:
            raise ValueError("EXECUTION_DECISION_EGO_MISMATCH")
        if vehicle_api.getSpeedMode(context.ego_id) != SAFE_SUMO_SPEED_MODE:
            raise RuntimeError("SAFE_SUMO_SPEED_MODE_CHANGED")
        records = []
        state = context.ego_state
        for zone_id, distance, _ in decision.blocked_zones:
            records.append(build_sumo_native_speed_constraint(context.ego_id,
                zone_id, distance, state["comfortable_deceleration_mps2"],
                state["speed"], simulation_step,
                vehicle_api.getActionStepLength(context.ego_id),
                vehicle_api.getStopSpeed(context.ego_id, state["speed"], distance),
                vehicle_api.getSpeedWithoutTraCI(context.ego_id),
                SAFE_SUMO_SPEED_MODE))
        return replace(decision, speed_constraints=tuple(records),
            requested_speed_mps=(min(r.requested_speed_cap_mps for r in records)
                                 if records else None))
