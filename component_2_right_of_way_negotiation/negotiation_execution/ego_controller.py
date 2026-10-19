"""Ego-owned physical execution using pair commitments and fresh V2V state.

The ideal same-step channel transports each sender's OWN execution metadata.
These messages never enter an actor observation. No global graph, critic, or
another ego's private observation is an input to this controller.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import math

from conflict import ConflictZoneOccupancyAssessor
from negotiation_learning.v2v_claim_bus import same_instant
from .controller import build_sumo_native_speed_constraint


@dataclass(frozen=True)
class ExecutionStateMessage:
    sender_id: str
    movement_path_id: str
    state: Mapping
    timestamp: float
    queue_arrival_seconds: float | None = None

    admission_state: str = "APPROACHING"
    coordination_epoch: tuple = ()

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
    strict_admission: bool = False
    coordination_epoch: tuple = ()
    mappo_receipt: bool = False
    fallback_peer_ids: tuple = ()
    mandatory_commitments: tuple = ()
    queue_arrival_seconds: float | None = None
    fallback_endpoint_evidence: tuple = ()
    own_execution_message: object = None
    mandatory_aware_fallback: bool = False

    def __post_init__(self):
        object.__setattr__(self, "ego_state", MappingProxyType(dict(self.ego_state)))
        if any(self.ego_id not in (c.yielding_vehicle_id, c.priority_vehicle_id)
               for c in self.commitments + self.mandatory_commitments):
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
    shield_rejection_reason: str | None = None
    fallback_pairs: tuple = ()


class DecentralizedEgoExecutionController:
    def __init__(self, path_manager, zone_manager):
        self.paths, self.zones = path_manager, zone_manager
        self._previous_blocked_zones = set()
        self._blocked_entry_progress = {}
        self._ego_id = None
        self.admission_state = "APPROACHING"
        self._clearance_certificates = set()
        from .native_hold import NativeJunctionHold
        self.native_hold = NativeJunctionHold()

    def decide(self, context):
        """Return only this ego's permission, before any TraCI mutation."""
        ego = context.ego_id
        if self._ego_id is not None and self._ego_id != ego:
            raise ValueError("EXECUTION_CONTROLLER_EGO_MISMATCH")
        self._ego_id = ego
        if not context.negotiation_eligible and not context.strict_admission:
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
            self.admission_state = "CLEARED"
            return EgoExecutionDecision(ego, "PERMITTED", "JUNCTION_CLEARED")
        if self.admission_state in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE"}:
            if progress >= 0:
                self.admission_state = "IN_CONFLICT_ZONE"
            return EgoExecutionDecision(ego, "PERMITTED", "VALID_ADMISSION_LOCK")
        def hold(reason):
            self.admission_state = "HELD_BEFORE_ZONE"
            self._previous_blocked_zones = {"JUNCTION_ENTRY"}
            self._blocked_entry_progress = {"JUNCTION_ENTRY": 0.0}
            return EgoExecutionDecision(ego, "SAFE_HOLD", reason,
                (("JUNCTION_ENTRY", max(0.0, -progress), ""),))
        if not context.negotiation_eligible:
            return hold("FOLLOWER_AWAITING_NEGOTIATED_ADMISSION")
        if not context.coordination_complete or not same_instant(
                context.timestamp, context.coordination_timestamp):
            return hold("MISSING_OR_STALE_LOCAL_COORDINATION")
        peers = {m.sender_id: m for m in context.peer_messages}
        if context.strict_admission and any(c.agreement_id != context.coordination_epoch
                for c in context.commitments):
            return hold("COORDINATION_EPOCH_MISMATCH")
        owed = {c.priority_vehicle_id for c in context.commitments
                if c.yielding_vehicle_id == ego}
        required_peers = {c.priority_vehicle_id if c.yielding_vehicle_id == ego
                          else c.yielding_vehicle_id for c in context.commitments}
        if not required_peers.issubset(set(peers) | self._clearance_certificates):
            return hold("MISSING_PRIORITY_CLEARANCE")
        blocked = []
        fallback_pairs = []
        rejection = None
        supplementary_order = None
        if context.mandatory_aware_fallback and context.mappo_receipt:
            from .mandatory_fallback import legal_order
            if not context.fallback_endpoint_evidence or context.own_execution_message is None:
                return hold("MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE")
            supplementary_order, error = legal_order(ego, context.timestamp,
                context.coordination_epoch, context.fallback_endpoint_evidence,
                (context.own_execution_message,) + tuple(m for m in context.peer_messages
                    if m.sender_id in {r.sender_id for r in context.fallback_endpoint_evidence}),
                self.paths, self.zones)
            if error:
                return hold(error)
        for peer_id, message in peers.items():
            if not same_instant(message.timestamp, context.timestamp):
                return hold("STALE_PEER_CLEARANCE")
            if context.strict_admission and message.coordination_epoch != context.coordination_epoch:
                return hold("PEER_COORDINATION_EPOCH_MISMATCH")
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
            if peer_status == "CLEARED_ZONE":
                self._clearance_certificates.add(peer_id)
                continue
            own_yields = peer_id in owed
            peer_yields = any(c.yielding_vehicle_id == peer_id and
                c.priority_vehicle_id == ego for c in context.commitments)
            # Mandatory obligations survive protocol claim removal. This is an
            # execution rejection, not a change to trained RELINQUISH semantics.
            mandatory_own = any(c.yielding_vehicle_id == ego and
                c.priority_vehicle_id == peer_id for c in context.mandatory_commitments)
            mandatory_peer = any(c.yielding_vehicle_id == peer_id and
                c.priority_vehicle_id == ego for c in context.mandatory_commitments)
            if context.strict_admission and hasattr(self.paths, "approach_relation"):
                own_path = self.paths.paths[context.movement_path_id]
                peer_path = self.paths.paths[message.movement_path_id]
                if self.paths.approach_relation(own_path.path_id, peer_path.path_id) == "ONCOMING":
                    # Sender-declared own movement is already legitimate
                    # execution metadata; it never enters an actor observation.
                    mandatory_own |= (own_path.manoeuvre in {"LEFT", "RIGHT"} and peer_path.manoeuvre == "STRAIGHT") or (own_path.manoeuvre == "LEFT" and peer_path.manoeuvre == "RIGHT")
                    mandatory_peer |= (peer_path.manoeuvre in {"LEFT", "RIGHT"} and own_path.manoeuvre == "STRAIGHT") or (peer_path.manoeuvre == "LEFT" and own_path.manoeuvre == "RIGHT")
            if mandatory_own and mandatory_peer:
                return hold("MANDATORY_RULE_CONTRADICTION")
            if mandatory_own and not own_yields or mandatory_peer and not peer_yields:
                # Reject the MAPPO removal for execution; independently retain
                # the original non-negotiable obligation, without changing the
                # protocol's saved effective graph or trained action meanings.
                rejection = "MANDATORY_PRECEDENCE_REMOVED"
                own_yields, peer_yields = mandatory_own, mandatory_peer
            if context.strict_admission and (own_yields == peer_yields):
                rejection = "RECIPROCAL_PHYSICAL_COMMITMENT" if own_yields else "UNORDERED_PHYSICAL_CONFLICT"
                a, b = context.queue_arrival_seconds, message.queue_arrival_seconds
                if (not context.mappo_receipt or peer_id not in context.fallback_peer_ids or
                        a is None or b is None or not math.isfinite(a) or
                        not math.isfinite(b) or a > context.timestamp or b > context.timestamp):
                    return hold(rejection)
                # The channel shares simulation-step timestamps. Eight ULPs
                # of max(1, |a|, |b|) accommodate representations of the same
                # instant; these are not a traffic priority time window.
                if context.mandatory_aware_fallback:
                    if not context.fallback_endpoint_evidence or context.own_execution_message is None:
                        return hold("MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE")
                    from .mandatory_fallback import legal_order
                    if supplementary_order is None:
                        supplementary_order, error = legal_order(ego, context.timestamp,
                            context.coordination_epoch, context.fallback_endpoint_evidence,
                            (context.own_execution_message,) + tuple(
                                m for m in context.peer_messages
                                if m.sender_id in {r.sender_id for r in context.fallback_endpoint_evidence}),
                            self.paths, self.zones)
                        if error:
                            return hold(error)
                    own_yields = supplementary_order.index(ego) > supplementary_order.index(peer_id)
                else:
                    own_yields = ego > peer_id if same_instant(a,b) else a > b
                peer_yields = not own_yields
                fallback_pairs.append((ego, peer_id) if own_yields else (peer_id, ego))
            if message.admission_state in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE"}:
                own_yields = True
            unresolved = own_yields and peer_status != "CLEARED_ZONE"
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
                blocked.append(("JUNCTION_ENTRY" if context.strict_admission else record["zone_id"],
                                max(0.0, -progress if context.strict_admission else own_interval[0] - progress), peer_id))
        self._previous_blocked_zones = {zone for zone, _, _ in blocked}
        self._blocked_entry_progress = {zone: progress + distance
                                       for zone, distance, _ in blocked}
        return EgoExecutionDecision(ego,
            "BLOCKED_BY_PRECEDENCE" if blocked else "PERMITTED",
            "UNRESOLVED_LOCAL_ZONE_OBLIGATION" if blocked else "LOCALLY_SAFE",
            tuple(blocked), shield_rejection_reason=rejection,
            fallback_pairs=tuple(fallback_pairs))

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
        if (context.strict_admission and not context.negotiation_eligible
                and decision.reason == 'FOLLOWER_AWAITING_NEGOTIATED_ADMISSION'
                and state['lane_id'] == self.paths.paths[context.movement_path_id].incoming_lane_id):
            # Entry remains SAFE_HOLD. The per-ego NativeJunctionHold is
            # installed before the next simulation step and prevents entry.
            # Release any old TraCI cap: native following and the explicit
            # end-of-lane stop govern advancement, acceleration and braking.
            return replace(decision, speed_constraints=(), requested_speed_mps=None)
        if context.strict_admission and decision.permission == "PERMITTED":
            from .controller import sumo_euler_comfortable_brake_gap
            path = self.paths.paths[context.movement_path_id]
            progress, _, error = self.paths.resolve_front_bumper_path_progress(state, path)
            if error:
                raise RuntimeError("ADMISSION_PROGRESS_UNAVAILABLE")
            # Include SUMO's own unconstrained speed for release from a TraCI
            # hold: even a stopped vehicle can move in the next action step.
            # getSpeedWithoutTraCI describes the preceding SUMO action and
            # can still be zero when a junction obstruction has just cleared.
            # Include the next physical acceleration step before unlocking a
            # stopped vehicle at the entry line; this is not a time margin.
            release_speed = max(state["speed"], vehicle_api.getSpeedWithoutTraCI(context.ego_id),
                state["speed"] + max(0.0, state.get("max_acceleration_mps2", 0.0)) * simulation_step)
            boundary = sumo_euler_comfortable_brake_gap(release_speed,
                state["comfortable_deceleration_mps2"], simulation_step) + (
                release_speed * vehicle_api.getActionStepLength(context.ego_id))
            if self.admission_state != "CLEARED" and -progress <= boundary:
                self.admission_state = "IN_CONFLICT_ZONE" if progress >= 0 else "COMMITTED_TO_ENTER"
                self._previous_blocked_zones.clear()
                self._blocked_entry_progress.clear()
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
