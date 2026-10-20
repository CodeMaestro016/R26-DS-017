"""Ego-owned physical execution using pair commitments and fresh V2V state.

The ideal same-step channel transports each sender's OWN execution metadata.
These messages never enter an actor observation. No global graph, critic, or
another ego's private observation is an input to this controller.
"""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping from typing for the operations below.
from typing import Mapping
# Import math for use in this module.
import math

# Import ConflictZoneOccupancyAssessor from conflict for the operations below.
from conflict import ConflictZoneOccupancyAssessor
# Import same_instant from negotiation_learning.v2v_claim_bus for the operations below.
from negotiation_learning.v2v_claim_bus import same_instant
# Import build_sumo_native_speed_constraint from .controller for the operations below.
from .controller import build_sumo_native_speed_constraint


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ExecutionStateMessage to group the state and operations declared below.
# Declared fields: sender_id, movement_path_id, state, timestamp, queue_arrival_seconds, admission_state,
# coordination_epoch.
# Construction and attribute behavior follow the declared decorators and base classes.
class ExecutionStateMessage:
    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare movement_path_id as str for this data structure.
    movement_path_id: str
    # Declare state as Mapping for this data structure.
    state: Mapping
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Set queue_arrival_seconds to None; declare its type as float | None.
    queue_arrival_seconds: float | None = None

    # Set admission_state to the text 'APPROACHING'; declare its type as str.
    admission_state: str = "APPROACHING"
    # Set coordination_epoch to an empty tuple; declare its type as tuple.
    coordination_epoch: tuple = ()

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Sender-owned physical metadata only; private actor observations and
        # simulator route truth are not transported by this execution channel.
        # Set physical_fields to a set containing the text 'position', the text 'heading_radians', the text
        # 'lane_id', the text 'lane_position', the text...
        physical_fields = {"position", "heading_radians", "lane_id", "lane_position",
            "lane_length", "road_id", "length", "width", "speed", "progress"}
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "state", MappingProxyType({
            # Evaluate key belongs to physical_fields as part of the enclosing expression.
            key: value for key, value in self.state.items() if key in physical_fields}))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EgoCoordinationCommitment to group the state and operations declared below.
# Declared fields: yielding_vehicle_id, priority_vehicle_id, agreement_id.
# Construction and attribute behavior follow the declared decorators and base classes.
class EgoCoordinationCommitment:
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare agreement_id as tuple for this data structure.
    agreement_id: tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EgoExecutionContext to group the state and operations declared below.
# Declared fields: ego_id, ego_state, movement_path_id, timestamp, commitments, peer_messages,
# coordination_complete, coordination_timestamp, negotiation_eligible, strict_admission, coordination_epoch,
# mappo_receipt,....
# Construction and attribute behavior follow the declared decorators and base classes.
class EgoExecutionContext:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare ego_state as Mapping for this data structure.
    ego_state: Mapping
    # Declare movement_path_id as str for this data structure.
    movement_path_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Set commitments to an empty tuple; declare its type as tuple.
    commitments: tuple = ()
    # Set peer_messages to an empty tuple; declare its type as tuple.
    peer_messages: tuple = ()
    # Set coordination_complete to False; declare its type as bool.
    coordination_complete: bool = False
    # Set coordination_timestamp to None; declare its type as float | None.
    coordination_timestamp: float | None = None
    # Set negotiation_eligible to True; declare its type as bool.
    negotiation_eligible: bool = True
    # Set strict_admission to False; declare its type as bool.
    strict_admission: bool = False
    # Set coordination_epoch to an empty tuple; declare its type as tuple.
    coordination_epoch: tuple = ()
    # Set mappo_receipt to False; declare its type as bool.
    mappo_receipt: bool = False
    # Set fallback_peer_ids to an empty tuple; declare its type as tuple.
    fallback_peer_ids: tuple = ()
    # Set mandatory_commitments to an empty tuple; declare its type as tuple.
    mandatory_commitments: tuple = ()
    # Set queue_arrival_seconds to None; declare its type as float | None.
    queue_arrival_seconds: float | None = None
    # Set fallback_endpoint_evidence to an empty tuple; declare its type as tuple.
    fallback_endpoint_evidence: tuple = ()
    # Set own_execution_message to None; declare its type as object.
    own_execution_message: object = None
    # Set mandatory_aware_fallback to False; declare its type as bool.
    mandatory_aware_fallback: bool = False

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "ego_state", MappingProxyType(dict(self.ego_state)))
        # Run this branch when whether any item is true in a lazy sequence of self.ego_id does not belong to a
        # tuple containing c.yielding_vehicle_id, c.priority_vehicle_id for c in self.commitments plus
        # self.mandatory_commitments.
        if any(self.ego_id not in (c.yielding_vehicle_id, c.priority_vehicle_id)
               # Evaluate self.commitments plus self.mandatory_commitments as part of the enclosing expression.
               for c in self.commitments + self.mandatory_commitments):
            # Raise ValueError with the text 'NONLOCAL_EXECUTION_COMMITMENT' to stop this execution path.
            raise ValueError("NONLOCAL_EXECUTION_COMMITMENT")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EgoExecutionDecision to group the state and operations declared below.
# Declared fields: ego_id, permission, reason, blocked_zones, speed_constraints, requested_speed_mps,
# decentralized_execution, centralized_execution_graph_used_for_control, shield_rejection_reason, fallback_pairs.
# Construction and attribute behavior follow the declared decorators and base classes.
class EgoExecutionDecision:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare permission as str for this data structure.
    permission: str
    # Declare reason as str for this data structure.
    reason: str
    # Set blocked_zones to an empty tuple; declare its type as tuple.
    blocked_zones: tuple = ()  # (zone_id, distance_to_entry, priority_id)
    # Set speed_constraints to an empty tuple; declare its type as tuple.
    speed_constraints: tuple = ()
    # Set requested_speed_mps to None; declare its type as float | None.
    requested_speed_mps: float | None = None
    # Set decentralized_execution to True; declare its type as bool.
    decentralized_execution: bool = True
    # Set centralized_execution_graph_used_for_control to False; declare its type as bool.
    centralized_execution_graph_used_for_control: bool = False
    # Set shield_rejection_reason to None; declare its type as str | None.
    shield_rejection_reason: str | None = None
    # Set fallback_pairs to an empty tuple; declare its type as tuple.
    fallback_pairs: tuple = ()


# Define DecentralizedEgoExecutionController to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class DecentralizedEgoExecutionController:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input zone_manager: the supplied zone manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, zone_manager):
        # Set (self.paths, self.zones) to a tuple containing path_manager, zone_manager.
        self.paths, self.zones = path_manager, zone_manager
        # Set self._previous_blocked_zones to an empty set.
        self._previous_blocked_zones = set()
        # Set self._blocked_entry_progress to an empty dictionary.
        self._blocked_entry_progress = {}
        # Set self._ego_id to None.
        self._ego_id = None
        # Set self.admission_state to the text 'APPROACHING'.
        self.admission_state = "APPROACHING"
        # Set self._clearance_certificates to an empty set.
        self._clearance_certificates = set()
        # Import NativeJunctionHold from .native_hold for the operations below.
        from .native_hold import NativeJunctionHold
        # Set self.native_hold to the result of NativeJunctionHold().
        self.native_hold = NativeJunctionHold()

    # Return only this ego's permission, before any TraCI mutation.
    # Input context: the supplied context.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def decide(self, context):
        """Return only this ego's permission, before any TraCI mutation."""
        # Set ego to context.ego_id.
        ego = context.ego_id
        # Run this branch when self._ego_id is a different object from None and self._ego_id differs from ego.
        if self._ego_id is not None and self._ego_id != ego:
            # Raise ValueError with the text 'EXECUTION_CONTROLLER_EGO_MISMATCH' to stop this execution path.
            raise ValueError("EXECUTION_CONTROLLER_EGO_MISMATCH")
        # Set self._ego_id to ego.
        self._ego_id = ego
        # Run this branch when the negation of context.negotiation_eligible and the negation of
        # context.strict_admission.
        if not context.negotiation_eligible and not context.strict_admission:
            # Return the result of EgoExecutionDecision(ego, the text 'NATIVE_FOLLOWING', the text 'FOLLOWER') to
            # the caller.
            return EgoExecutionDecision(ego, "NATIVE_FOLLOWING", "FOLLOWER")
        # Set path to self.paths.paths at context.movement_path_id.
        path = self.paths.paths[context.movement_path_id]
        # Set (progress, _, error) to the result of
        # self.paths.resolve_front_bumper_path_progress(context.ego_state, path).
        progress, _, error = self.paths.resolve_front_bumper_path_progress(
            # Supply context.ego_state to self.paths.resolve_front_bumper_path_progress.
            context.ego_state, path)
        # Run this branch when error.
        if error:
            # Return the result of EgoExecutionDecision(ego, the text 'SAFE_HOLD', error, a tuple containing a
            # tuple containing the text...) to the caller.
            return EgoExecutionDecision(ego, "SAFE_HOLD", error,
                                        # Supply a tuple containing a tuple containing the text 'JUNCTION_ENTRY',
                                        # 0.0, the text '' to EgoExecutionDecision.
                                        (("JUNCTION_ENTRY", 0.0, ""),))
        # Run this branch when whether any item is true in a lazy sequence of progress is at least entry for entry
        # in values from self._blocked_entry_progress.
        if any(progress >= entry for entry in self._blocked_entry_progress.values()):
            # Raise RuntimeError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this execution
            # path.
            raise RuntimeError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
        # An ego whose rear has cleared the junction no longer needs permission.
        # Run this branch when context.ego_state at 'lane_id' equals path.outgoing_lane_id and context.ego_state
        # at 'lane_position' is greater than context.ego_state at 'length'.
        if (context.ego_state["lane_id"] == path.outgoing_lane_id and
                # Evaluate context.ego_state at 'lane_position' is greater than context.ego_state at 'length' as
                # part of the enclosing expression.
                context.ego_state["lane_position"] > context.ego_state["length"]):
            # Set self.admission_state to the text 'CLEARED'.
            self.admission_state = "CLEARED"
            # Return the result of EgoExecutionDecision(ego, the text 'PERMITTED', the text 'JUNCTION_CLEARED') to
            # the caller.
            return EgoExecutionDecision(ego, "PERMITTED", "JUNCTION_CLEARED")
        # Run this branch when self.admission_state belongs to a set containing the text 'COMMITTED_TO_ENTER', the
        # text 'IN_CONFLICT_ZONE'.
        if self.admission_state in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE"}:
            # Run this branch when progress is at least 0.
            if progress >= 0:
                # Set self.admission_state to the text 'IN_CONFLICT_ZONE'.
                self.admission_state = "IN_CONFLICT_ZONE"
            # Return the result of EgoExecutionDecision(ego, the text 'PERMITTED', the text
            # 'VALID_ADMISSION_LOCK') to the caller.
            return EgoExecutionDecision(ego, "PERMITTED", "VALID_ADMISSION_LOCK")
        # Hold using the inputs and processing steps below.
        # Input reason: the supplied reason.
        # Output: the result of EgoExecutionDecision(ego, the text 'SAFE_HOLD', reason, a tuple containing a tuple
        # containing the text...).
        def hold(reason):
            # Set self.admission_state to the text 'HELD_BEFORE_ZONE'.
            self.admission_state = "HELD_BEFORE_ZONE"
            # Set self._previous_blocked_zones to a set containing the text 'JUNCTION_ENTRY'.
            self._previous_blocked_zones = {"JUNCTION_ENTRY"}
            # Set self._blocked_entry_progress to a dictionary containing JUNCTION_ENTRY.
            self._blocked_entry_progress = {"JUNCTION_ENTRY": 0.0}
            # Return the result of EgoExecutionDecision(ego, the text 'SAFE_HOLD', reason, a tuple containing a
            # tuple containing the text...) to the caller.
            return EgoExecutionDecision(ego, "SAFE_HOLD", reason,
                # Supply a tuple containing a tuple containing the text 'JUNCTION_ENTRY', the maximum of 0.0, the
                # negative of progress, the text '' to EgoExecutionDecision.
                (("JUNCTION_ENTRY", max(0.0, -progress), ""),))
        # Run this branch when the negation of context.negotiation_eligible.
        if not context.negotiation_eligible:
            # Return the result of hold(the text 'FOLLOWER_AWAITING_NEGOTIATED_ADMISSION') to the caller.
            return hold("FOLLOWER_AWAITING_NEGOTIATED_ADMISSION")
        # Run this branch when the negation of context.coordination_complete or the negation of the result of
        # same_instant(context.timestamp, context.coordination_timestamp).
        if not context.coordination_complete or not same_instant(
                # Supply context.coordination_timestamp to same_instant.
                context.timestamp, context.coordination_timestamp):
            # Return the result of hold(the text 'MISSING_OR_STALE_LOCAL_COORDINATION') to the caller.
            return hold("MISSING_OR_STALE_LOCAL_COORDINATION")
        # Set peers to a dictionary of m.sender_id mapped to m for m in context.peer_messages.
        peers = {m.sender_id: m for m in context.peer_messages}
        # Run this branch when context.strict_admission and whether any item is true in a lazy sequence of
        # c.agreement_id differs from context.coordination_epoch for c in context.commitments.
        if context.strict_admission and any(c.agreement_id != context.coordination_epoch
                # Evaluate context.commitments as part of the enclosing expression.
                for c in context.commitments):
            # Return the result of hold(the text 'COORDINATION_EPOCH_MISMATCH') to the caller.
            return hold("COORDINATION_EPOCH_MISMATCH")
        # Set owed to a set of c.priority_vehicle_id for c in context.commitments; retain entries satisfying
        # c.yielding_vehicle_id equals ego.
        owed = {c.priority_vehicle_id for c in context.commitments
                # Evaluate c.yielding_vehicle_id equals ego as part of the enclosing expression.
                if c.yielding_vehicle_id == ego}
        # Set required_peers to a set of c.priority_vehicle_id when c.yielding_vehicle_id equals ego, otherwise
        # c.yielding_vehicle_id for c in context.commitments.
        required_peers = {c.priority_vehicle_id if c.yielding_vehicle_id == ego
                          # Evaluate c.yielding_vehicle_id as part of the enclosing expression.
                          else c.yielding_vehicle_id for c in context.commitments}
        # Run this branch when the negation of the result of required_peers.issubset(a set built from peers
        # combined with self._clearance_certificates).
        if not required_peers.issubset(set(peers) | self._clearance_certificates):
            # Return the result of hold(the text 'MISSING_PRIORITY_CLEARANCE') to the caller.
            return hold("MISSING_PRIORITY_CLEARANCE")
        # Set blocked to an empty list.
        blocked = []
        # Set fallback_pairs to an empty list.
        fallback_pairs = []
        # Set rejection to None.
        rejection = None
        # Set supplementary_order to None.
        supplementary_order = None
        # Run this branch when context.mandatory_aware_fallback and context.mappo_receipt.
        if context.mandatory_aware_fallback and context.mappo_receipt:
            # Import legal_order from .mandatory_fallback for the operations below.
            from .mandatory_fallback import legal_order
            # Run this branch when the negation of context.fallback_endpoint_evidence or
            # context.own_execution_message is the same object as None.
            if not context.fallback_endpoint_evidence or context.own_execution_message is None:
                # Return the result of hold(the text 'MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE') to the caller.
                return hold("MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE")
            # Set (supplementary_order, error) to the result of legal_order(ego, context.timestamp,
            # context.coordination_epoch, context.fallback_endpoint_evidence, a tuple...).
            supplementary_order, error = legal_order(ego, context.timestamp,
                # Supply context.fallback_endpoint_evidence to legal_order.
                context.coordination_epoch, context.fallback_endpoint_evidence,
                # Supply a tuple containing context.own_execution_message plus a tuple built from a lazy sequence
                # of m for m in context.peer_messages; retain entries satisfying m.sender_id belongs to
                # {r.sender_id for r in context.fallback_endpoint_evidence} to legal_order.
                (context.own_execution_message,) + tuple(m for m in context.peer_messages
                    # Evaluate m.sender_id belongs to a set of r.sender_id for r in
                    # context.fallback_endpoint_evidence as part of the enclosing expression.
                    if m.sender_id in {r.sender_id for r in context.fallback_endpoint_evidence}),
                # Supply self.paths to legal_order.
                self.paths, self.zones)
            # Run this branch when error.
            if error:
                # Return the result of hold(error) to the caller.
                return hold(error)
        # Iterate over key/value pairs from peers, binding each item to (peer_id, message).
        for peer_id, message in peers.items():
            # Run this branch when the negation of the result of same_instant(message.timestamp,
            # context.timestamp).
            if not same_instant(message.timestamp, context.timestamp):
                # Return the result of hold(the text 'STALE_PEER_CLEARANCE') to the caller.
                return hold("STALE_PEER_CLEARANCE")
            # Run this branch when context.strict_admission and message.coordination_epoch differs from
            # context.coordination_epoch.
            if context.strict_admission and message.coordination_epoch != context.coordination_epoch:
                # Return the result of hold(the text 'PEER_COORDINATION_EPOCH_MISMATCH') to the caller.
                return hold("PEER_COORDINATION_EPOCH_MISMATCH")
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set record to the result of self.zones.zone_record(context.movement_path_id, context.ego_state
                # at 'width', message.movement_path_id, message.state...).
                record = self.zones.zone_record(context.movement_path_id,
                    # Supply context.ego_state at 'width' to self.zones.zone_record.
                    context.ego_state["width"], message.movement_path_id,
                    # Supply message.state at 'width' to self.zones.zone_record.
                    message.state["width"])
            # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
            except (KeyError, TypeError, ValueError):
                # Return the result of hold(the text 'UNRESOLVED_PHYSICAL_RELATIONSHIP') to the caller.
                return hold("UNRESOLVED_PHYSICAL_RELATIONSHIP")
            # Run this branch when record is the same object as None.
            if record is None:
                # Skip the rest of this loop iteration and process the next item.
                continue  # Authoritative static map: physically nonconflicting.
            # Set (peer_progress, _, error) to the result of
            # self.paths.resolve_front_bumper_path_progress(message.state, self.paths.paths at
            # message.movement_path_id).
            peer_progress, _, error = self.paths.resolve_front_bumper_path_progress(
                # Supply self.paths.paths at message.movement_path_id to
                # self.paths.resolve_front_bumper_path_progress.
                message.state, self.paths.paths[message.movement_path_id])
            # Run this branch when error.
            if error:
                # Return the result of hold(the text 'UNRESOLVED_PEER_CLEARANCE') to the caller.
                return hold("UNRESOLVED_PEER_CLEARANCE")
            # Set own_interval to record at 'first_path_distance_interval'.
            own_interval = record["first_path_distance_interval"]
            # Set peer_interval to record at 'second_path_distance_interval'.
            peer_interval = record["second_path_distance_interval"]
            # Set (own_status, error) to the result of ConflictZoneOccupancyAssessor.occupancy_state(progress,
            # own_interval, context.ego_state at 'length').
            own_status, error = ConflictZoneOccupancyAssessor.occupancy_state(
                # Supply context.ego_state at 'length' to ConflictZoneOccupancyAssessor.occupancy_state.
                progress, own_interval, context.ego_state["length"])
            # Set (peer_status, peer_error) to the result of
            # ConflictZoneOccupancyAssessor.occupancy_state(peer_progress, peer_interval, message.state at
            # 'length').
            peer_status, peer_error = ConflictZoneOccupancyAssessor.occupancy_state(
                # Supply message.state at 'length' to ConflictZoneOccupancyAssessor.occupancy_state.
                peer_progress, peer_interval, message.state["length"])
            # Run this branch when error or peer_error.
            if error or peer_error:
                # Return the result of hold(the text 'UNRESOLVED_ZONE_OCCUPANCY') to the caller.
                return hold("UNRESOLVED_ZONE_OCCUPANCY")
            # Run this branch when own_status equals the text 'CLEARED_ZONE'.
            if own_status == "CLEARED_ZONE":
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when peer_status equals the text 'CLEARED_ZONE'.
            if peer_status == "CLEARED_ZONE":
                # Add peer_id to self._clearance_certificates.
                self._clearance_certificates.add(peer_id)
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set own_yields to peer_id belongs to owed.
            own_yields = peer_id in owed
            # Set peer_yields to whether any item is true in a lazy sequence of c.yielding_vehicle_id equals
            # peer_id and c.priority_vehicle_id equals ego for c in context.commitments.
            peer_yields = any(c.yielding_vehicle_id == peer_id and
                # Evaluate c.priority_vehicle_id equals ego as part of the enclosing expression.
                c.priority_vehicle_id == ego for c in context.commitments)
            # Mandatory obligations survive protocol claim removal. This is an
            # execution rejection, not a change to trained RELINQUISH semantics.
            # Set mandatory_own to whether any item is true in a lazy sequence of c.yielding_vehicle_id equals ego
            # and c.priority_vehicle_id equals peer_id for c in context.mandatory_commitments.
            mandatory_own = any(c.yielding_vehicle_id == ego and
                # Evaluate c.priority_vehicle_id equals peer_id as part of the enclosing expression.
                c.priority_vehicle_id == peer_id for c in context.mandatory_commitments)
            # Set mandatory_peer to whether any item is true in a lazy sequence of c.yielding_vehicle_id equals
            # peer_id and c.priority_vehicle_id equals ego for c in context.mandatory_commitments.
            mandatory_peer = any(c.yielding_vehicle_id == peer_id and
                # Evaluate context.mandatory_commitments as part of the enclosing expression.
                c.priority_vehicle_id == ego for c in context.mandatory_commitments)
            # Run this branch when context.strict_admission and whether self.paths exposes the requested
            # attribute.
            if context.strict_admission and hasattr(self.paths, "approach_relation"):
                # Set own_path to self.paths.paths at context.movement_path_id.
                own_path = self.paths.paths[context.movement_path_id]
                # Set peer_path to self.paths.paths at message.movement_path_id.
                peer_path = self.paths.paths[message.movement_path_id]
                # Run this branch when the result of self.paths.approach_relation(own_path.path_id,
                # peer_path.path_id) equals the text 'ONCOMING'.
                if self.paths.approach_relation(own_path.path_id, peer_path.path_id) == "ONCOMING":
                    # Sender-declared own movement is already legitimate
                    # execution metadata; it never enters an actor observation.
                    # Update mandatory_own to its current value combined with own_path.manoeuvre belongs to a set
                    # containing 'LEFT', 'RIGHT' and peer_path.manoeuvre equals the text 'STRAIGHT' or
                    # own_path.manoeuvre equals the text 'LEFT' and peer_path.manoeuvre equals the text 'RIGHT'.
                    mandatory_own |= (own_path.manoeuvre in {"LEFT", "RIGHT"} and peer_path.manoeuvre == "STRAIGHT") or (own_path.manoeuvre == "LEFT" and peer_path.manoeuvre == "RIGHT")
                    # Update mandatory_peer to its current value combined with peer_path.manoeuvre belongs to a
                    # set containing 'LEFT', 'RIGHT' and own_path.manoeuvre equals the text 'STRAIGHT' or
                    # peer_path.manoeuvre equals the text 'LEFT' and own_path.manoeuvre equals the text 'RIGHT'.
                    mandatory_peer |= (peer_path.manoeuvre in {"LEFT", "RIGHT"} and own_path.manoeuvre == "STRAIGHT") or (peer_path.manoeuvre == "LEFT" and own_path.manoeuvre == "RIGHT")
            # Run this branch when mandatory_own and mandatory_peer.
            if mandatory_own and mandatory_peer:
                # Return the result of hold(the text 'MANDATORY_RULE_CONTRADICTION') to the caller.
                return hold("MANDATORY_RULE_CONTRADICTION")
            # Run this branch when mandatory_own and the negation of own_yields or mandatory_peer and the negation
            # of peer_yields.
            if mandatory_own and not own_yields or mandatory_peer and not peer_yields:
                # Reject the MAPPO removal for execution; independently retain
                # the original non-negotiable obligation, without changing the
                # protocol's saved effective graph or trained action meanings.
                # Set rejection to the text 'MANDATORY_PRECEDENCE_REMOVED'.
                rejection = "MANDATORY_PRECEDENCE_REMOVED"
                # Set (own_yields, peer_yields) to a tuple containing mandatory_own, mandatory_peer.
                own_yields, peer_yields = mandatory_own, mandatory_peer
            # Run this branch when context.strict_admission and own_yields equals peer_yields.
            if context.strict_admission and (own_yields == peer_yields):
                # Set rejection to the text 'RECIPROCAL_PHYSICAL_COMMITMENT' when own_yields, otherwise the text
                # 'UNORDERED_PHYSICAL_CONFLICT'.
                rejection = "RECIPROCAL_PHYSICAL_COMMITMENT" if own_yields else "UNORDERED_PHYSICAL_CONFLICT"
                # Set (a, b) to a tuple containing context.queue_arrival_seconds, message.queue_arrival_seconds.
                a, b = context.queue_arrival_seconds, message.queue_arrival_seconds
                # Run this branch when the negation of context.mappo_receipt or peer_id does not belong to
                # context.fallback_peer_ids or a is the same object as None or b is the same object as None or the
                # negation of whether a contains finite numeric values or the negation of whether b contains
                # finite numeric values or a is greater than context.timestamp or b is greater than
                # context.timestamp.
                if (not context.mappo_receipt or peer_id not in context.fallback_peer_ids or
                        # Evaluate the negation of whether a contains finite numeric values as part of the
                        # enclosing expression.
                        a is None or b is None or not math.isfinite(a) or
                        # Evaluate a is greater than context.timestamp as part of the enclosing expression.
                        not math.isfinite(b) or a > context.timestamp or b > context.timestamp):
                    # Return the result of hold(rejection) to the caller.
                    return hold(rejection)
                # The channel shares simulation-step timestamps. Eight ULPs
                # of max(1, |a|, |b|) accommodate representations of the same
                # instant; these are not a traffic priority time window.
                # Run this branch when context.mandatory_aware_fallback.
                if context.mandatory_aware_fallback:
                    # Run this branch when the negation of context.fallback_endpoint_evidence or
                    # context.own_execution_message is the same object as None.
                    if not context.fallback_endpoint_evidence or context.own_execution_message is None:
                        # Return the result of hold(the text 'MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE') to the
                        # caller.
                        return hold("MISSING_AUTHENTICATED_ENDPOINT_EVIDENCE")
                    # Import legal_order from .mandatory_fallback for the operations below.
                    from .mandatory_fallback import legal_order
                    # Run this branch when supplementary_order is the same object as None.
                    if supplementary_order is None:
                        # Set (supplementary_order, error) to the result of legal_order(ego, context.timestamp,
                        # context.coordination_epoch, context.fallback_endpoint_evidence, a tuple...).
                        supplementary_order, error = legal_order(ego, context.timestamp,
                            # Supply context.fallback_endpoint_evidence to legal_order.
                            context.coordination_epoch, context.fallback_endpoint_evidence,
                            # Supply a tuple containing context.own_execution_message plus a tuple built from a
                            # lazy sequence of m for m in context.peer_messages; retain entries satisfying
                            # m.sender_id belongs to {r.sender_id for r in context.fallback_endpoint_evidence} to
                            # legal_order.
                            (context.own_execution_message,) + tuple(
                                # Evaluate context.peer_messages as part of the enclosing expression.
                                m for m in context.peer_messages
                                # Evaluate m.sender_id belongs to a set of r.sender_id for r in
                                # context.fallback_endpoint_evidence as part of the enclosing expression.
                                if m.sender_id in {r.sender_id for r in context.fallback_endpoint_evidence}),
                            # Supply self.paths to legal_order.
                            self.paths, self.zones)
                        # Run this branch when error.
                        if error:
                            # Return the result of hold(error) to the caller.
                            return hold(error)
                    # Set own_yields to the result of supplementary_order.index(ego) is greater than the result of
                    # supplementary_order.index(peer_id).
                    own_yields = supplementary_order.index(ego) > supplementary_order.index(peer_id)
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Set own_yields to ego is greater than peer_id when the result of same_instant(a, b),
                    # otherwise a is greater than b.
                    own_yields = ego > peer_id if same_instant(a,b) else a > b
                # Set peer_yields to the negation of own_yields.
                peer_yields = not own_yields
                # Append a tuple containing ego, peer_id when own_yields, otherwise a tuple containing peer_id,
                # ego to fallback_pairs.
                fallback_pairs.append((ego, peer_id) if own_yields else (peer_id, ego))
            # Run this branch when message.admission_state belongs to a set containing the text
            # 'COMMITTED_TO_ENTER', the text 'IN_CONFLICT_ZONE'.
            if message.admission_state in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE"}:
                # Set own_yields to True.
                own_yields = True
            # Set unresolved to own_yields and peer_status differs from the text 'CLEARED_ZONE'.
            unresolved = own_yields and peer_status != "CLEARED_ZONE"
            # Set occupied to peer_status equals the text 'CURRENTLY_OCCUPYING'.
            occupied = peer_status == "CURRENTLY_OCCUPYING"
            # Run this branch when own_status equals the text 'CURRENTLY_OCCUPYING'.
            if own_status == "CURRENTLY_OCCUPYING":
                # Run this branch when record at 'zone_id' belongs to self._previous_blocked_zones.
                if record["zone_id"] in self._previous_blocked_zones:
                    # Raise RuntimeError with the text 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE' to stop this
                    # execution path.
                    raise RuntimeError("BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
                # Permission cannot be revoked inside an already entered zone.
                # Other approaching egos independently hold for this occupant.
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when occupied and the negation of unresolved.
            if occupied and not unresolved:
                # Clearance safety is checked at junction admission. Once
                # admitted, an ego continues clearing rather than accepting
                # a newly arriving occupancy restriction mid-junction.
                # Run this branch when context.ego_state at 'lane_id' equals path.incoming_lane_id.
                if context.ego_state["lane_id"] == path.incoming_lane_id:
                    # Append a tuple containing the text 'JUNCTION_ENTRY', the maximum of 0.0, the negative of
                    # progress, peer_id to blocked.
                    blocked.append(("JUNCTION_ENTRY", max(0.0, -progress), peer_id))
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when unresolved.
            if unresolved:
                # Append a tuple containing the text 'JUNCTION_ENTRY' when context.strict_admission, otherwise
                # record at 'zone_id', the maximum of... to blocked.
                blocked.append(("JUNCTION_ENTRY" if context.strict_admission else record["zone_id"],
                                # Include the maximum of 0.0, the negative of progress when
                                # context.strict_admission, otherwise own_interval at 0 minus... in this tuple.
                                max(0.0, -progress if context.strict_admission else own_interval[0] - progress), peer_id))
        # Set self._previous_blocked_zones to a set of zone for (zone, _, _) in blocked.
        self._previous_blocked_zones = {zone for zone, _, _ in blocked}
        # Set self._blocked_entry_progress to a dictionary of zone mapped to progress plus distance for (zone,
        # distance, _) in blocked.
        self._blocked_entry_progress = {zone: progress + distance
                                       # Evaluate a tuple containing zone, distance, _ as part of the enclosing
                                       # expression.
                                       for zone, distance, _ in blocked}
        # Return the result of EgoExecutionDecision(ego, the text 'BLOCKED_BY_PRECEDENCE' when blocked, otherwise
        # the text 'PERMITTED', the text...) to the caller.
        return EgoExecutionDecision(ego,
            # Supply the text 'BLOCKED_BY_PRECEDENCE' when blocked, otherwise the text 'PERMITTED' to
            # EgoExecutionDecision.
            "BLOCKED_BY_PRECEDENCE" if blocked else "PERMITTED",
            # Supply the text 'UNRESOLVED_LOCAL_ZONE_OBLIGATION' when blocked, otherwise the text 'LOCALLY_SAFE'
            # to EgoExecutionDecision.
            "UNRESOLVED_LOCAL_ZONE_OBLIGATION" if blocked else "LOCALLY_SAFE",
            # Supply shield_rejection_reason as rejection.
            tuple(blocked), shield_rejection_reason=rejection,
            # Supply fallback_pairs as a tuple built from fallback_pairs.
            fallback_pairs=tuple(fallback_pairs))

    # Derive ego's own speed request using SUMO's native stopping model.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input vehicle_api: the supplied vehicle api.
    # Input simulation_step: the supplied simulation step.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def constrain(self, context, decision, vehicle_api, simulation_step):
        """Derive ego's own speed request using SUMO's native stopping model."""
        # Import replace from dataclasses for the operations below.
        from dataclasses import replace
        # Import SAFE_SUMO_SPEED_MODE from config for the operations below.
        from config import SAFE_SUMO_SPEED_MODE
        # Run this branch when decision.ego_id differs from context.ego_id.
        if decision.ego_id != context.ego_id:
            # Raise ValueError with the text 'EXECUTION_DECISION_EGO_MISMATCH' to stop this execution path.
            raise ValueError("EXECUTION_DECISION_EGO_MISMATCH")
        # Run this branch when the result of vehicle_api.getSpeedMode(context.ego_id) differs from
        # SAFE_SUMO_SPEED_MODE.
        if vehicle_api.getSpeedMode(context.ego_id) != SAFE_SUMO_SPEED_MODE:
            # Raise RuntimeError with the text 'SAFE_SUMO_SPEED_MODE_CHANGED' to stop this execution path.
            raise RuntimeError("SAFE_SUMO_SPEED_MODE_CHANGED")
        # Set records to an empty list.
        records = []
        # Set state to context.ego_state.
        state = context.ego_state
        # Run this branch when context.strict_admission and the negation of context.negotiation_eligible and
        # decision.reason equals the text 'FOLLOWER_AWAITING_NEGOTIATED_ADMISSION' and state at 'lane_id' equals
        # self.paths.paths[context.movement_path_id].incoming_lane_id.
        if (context.strict_admission and not context.negotiation_eligible
                # Evaluate decision.reason equals the text 'FOLLOWER_AWAITING_NEGOTIATED_ADMISSION' as part of the
                # enclosing expression.
                and decision.reason == 'FOLLOWER_AWAITING_NEGOTIATED_ADMISSION'
                # Evaluate state at 'lane_id' equals self.paths.paths[context.movement_path_id].incoming_lane_id
                # as part of the enclosing expression.
                and state['lane_id'] == self.paths.paths[context.movement_path_id].incoming_lane_id):
            # Entry remains SAFE_HOLD. The per-ego NativeJunctionHold is
            # installed before the next simulation step and prevents entry.
            # Release any old TraCI cap: native following and the explicit
            # end-of-lane stop govern advancement, acceleration and braking.
            # Return the result of replace(decision) to the caller.
            return replace(decision, speed_constraints=(), requested_speed_mps=None)
        # Run this branch when context.strict_admission and decision.permission equals the text 'PERMITTED'.
        if context.strict_admission and decision.permission == "PERMITTED":
            # Import sumo_euler_comfortable_brake_gap from .controller for the operations below.
            from .controller import sumo_euler_comfortable_brake_gap
            # Set path to self.paths.paths at context.movement_path_id.
            path = self.paths.paths[context.movement_path_id]
            # Set (progress, _, error) to the result of self.paths.resolve_front_bumper_path_progress(state,
            # path).
            progress, _, error = self.paths.resolve_front_bumper_path_progress(state, path)
            # Run this branch when error.
            if error:
                # Raise RuntimeError with the text 'ADMISSION_PROGRESS_UNAVAILABLE' to stop this execution path.
                raise RuntimeError("ADMISSION_PROGRESS_UNAVAILABLE")
            # Include SUMO's own unconstrained speed for release from a TraCI
            # hold: even a stopped vehicle can move in the next action step.
            # getSpeedWithoutTraCI describes the preceding SUMO action and
            # can still be zero when a junction obstruction has just cleared.
            # Include the next physical acceleration step before unlocking a
            # stopped vehicle at the entry line; this is not a time margin.
            # Set release_speed to the maximum of state at 'speed', the result of
            # vehicle_api.getSpeedWithoutTraCI(context.ego_id), state at...
            release_speed = max(state["speed"], vehicle_api.getSpeedWithoutTraCI(context.ego_id),
                # Supply state at 'speed' plus the maximum of 0.0, 'max_acceleration_mps2' from state; use 0.0 if
                # absent multiplied by simulation_step to max.
                state["speed"] + max(0.0, state.get("max_acceleration_mps2", 0.0)) * simulation_step)
            # Set boundary to the result of sumo_euler_comfortable_brake_gap(release_speed, state at
            # 'comfortable_deceleration_mps2', simulation_step) plus release_speed multiplied by the result of
            # vehicle_api.getActionStepLength(context.ego_id).
            boundary = sumo_euler_comfortable_brake_gap(release_speed,
                # Supply state at 'comfortable_deceleration_mps2' to sumo_euler_comfortable_brake_gap.
                state["comfortable_deceleration_mps2"], simulation_step) + (
                # Evaluate release_speed multiplied by the result of
                # vehicle_api.getActionStepLength(context.ego_id) as part of the enclosing expression.
                release_speed * vehicle_api.getActionStepLength(context.ego_id))
            # Run this branch when self.admission_state differs from the text 'CLEARED' and the negative of
            # progress is at most boundary.
            if self.admission_state != "CLEARED" and -progress <= boundary:
                # Set self.admission_state to the text 'IN_CONFLICT_ZONE' when progress is at least 0, otherwise
                # the text 'COMMITTED_TO_ENTER'.
                self.admission_state = "IN_CONFLICT_ZONE" if progress >= 0 else "COMMITTED_TO_ENTER"
                # Clear the stored entries in self._previous_blocked_zones.
                self._previous_blocked_zones.clear()
                # Clear the stored entries in self._blocked_entry_progress.
                self._blocked_entry_progress.clear()
        # Iterate over decision.blocked_zones, binding each item to (zone_id, distance, _).
        for zone_id, distance, _ in decision.blocked_zones:
            # Append the result of build_sumo_native_speed_constraint(context.ego_id, zone_id, distance, state at
            # 'comfortable_deceleration_mps2', state at 'speed',...) to records.
            records.append(build_sumo_native_speed_constraint(context.ego_id,
                # Supply state at 'comfortable_deceleration_mps2' to build_sumo_native_speed_constraint.
                zone_id, distance, state["comfortable_deceleration_mps2"],
                # Supply simulation_step to build_sumo_native_speed_constraint.
                state["speed"], simulation_step,
                # Supply the result of vehicle_api.getActionStepLength(context.ego_id) to
                # build_sumo_native_speed_constraint.
                vehicle_api.getActionStepLength(context.ego_id),
                # Supply the result of vehicle_api.getStopSpeed(context.ego_id, state at 'speed', distance) to
                # build_sumo_native_speed_constraint.
                vehicle_api.getStopSpeed(context.ego_id, state["speed"], distance),
                # Supply the result of vehicle_api.getSpeedWithoutTraCI(context.ego_id) to
                # build_sumo_native_speed_constraint.
                vehicle_api.getSpeedWithoutTraCI(context.ego_id),
                # Supply SAFE_SUMO_SPEED_MODE to build_sumo_native_speed_constraint.
                SAFE_SUMO_SPEED_MODE))
        # Return the result of replace(decision) to the caller.
        return replace(decision, speed_constraints=tuple(records),
            # Supply requested_speed_mps as the minimum of a lazy sequence of r.requested_speed_cap_mps for r in
            # records when records, otherwise None.
            requested_speed_mps=(min(r.requested_speed_cap_mps for r in records)
                                 # Evaluate records as part of the enclosing expression.
                                 if records else None))
