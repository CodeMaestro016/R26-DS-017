"""Approved cooperative conditional-claim protocol; no movement permissions."""
# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import copy for use in this module.
import copy

# Import same_instant from .v2v_claim_bus for the operations below.
from .v2v_claim_bus import same_instant

# Set PROTOCOL_VERSION to the text 'CONDITIONAL_CLAIM_RECONCILIATION_V1'.
PROTOCOL_VERSION = "CONDITIONAL_CLAIM_RECONCILIATION_V1"
# Set MANOEUVRES to an immutable set built from a set containing the text 'LEFT', the text 'RIGHT', the text
# 'STRAIGHT'.
MANOEUVRES = frozenset({"LEFT", "RIGHT", "STRAIGHT"})


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MovementDeclaration to group the state and operations declared below.
# Declared fields: sender_id, manoeuvre, path_id, lane_id, timestamp, epoch, protocol.
# Construction and attribute behavior follow the declared decorators and base classes.
class MovementDeclaration:
    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare manoeuvre as str for this data structure.
    manoeuvre: str
    # Declare path_id as str for this data structure.
    path_id: str
    # Declare lane_id as str for this data structure.
    lane_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare epoch as tuple for this data structure.
    epoch: tuple
    # Set protocol to PROTOCOL_VERSION; declare its type as str.
    protocol: str = PROTOCOL_VERSION


# Same-step sender-bound transport, matching the ideal precedence channel.
# Instances expose the attributes and methods implemented in this class.
class MovementDeclarationBus:
    """Same-step sender-bound transport, matching the ideal precedence channel.

    Authenticated sender binding is a simulation protocol assumption, not a
    cryptographic guarantee. A sender reads only its own navigation/LDM state.
    No receiver is given another vehicle's route or a global movement mapping.
    """
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input paths: the supplied paths.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, paths):
        # Set self.paths to paths.
        self.paths = paths
        # Set self.messages to an empty dictionary.
        self.messages = {}
        # Set self.timestamp to None.
        self.timestamp = None
        # Set self.epoch to an empty tuple.
        self.epoch = ()
        # Set self.authored to an empty dictionary.
        self.authored = {}

    # Begin step using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Output: no explicit value; normal completion returns None.
    def begin_step(self, now):
        # Set self.timestamp to now.
        self.timestamp = now
        # Set self.epoch to a tuple containing PROTOCOL_VERSION, now.
        self.epoch = (PROTOCOL_VERSION, now)
        # Set self.messages to an empty dictionary.
        self.messages = {}
        # Set self.authored to an empty dictionary.
        self.authored = {}

    # Author using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input now: the time used for this operation.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def author(self, ldm, now):
        # Set own to ldm.ego_id from ldm.tracks; use an empty dictionary if absent.
        own = ldm.tracks.get(ldm.ego_id, {})
        # Set manoeuvre to 'self_planned_manoeuvre' from own; use None if absent.
        manoeuvre = own.get("self_planned_manoeuvre")
        # Set path to the result of self.paths.resolve_path('lane_id' from own; use the text '' if absent,
        # manoeuvre).
        path = self.paths.resolve_path(own.get("lane_id", ""), manoeuvre)
        # Run this branch when manoeuvre does not belong to MANOEUVRES or path is the same object as None.
        if manoeuvre not in MANOEUVRES or path is None:
            # Return None to the caller.
            return None
        # Set message to the result of MovementDeclaration(ldm.ego_id, manoeuvre, path.path_id, own at 'lane_id',
        # now, self.epoch).
        message = MovementDeclaration(ldm.ego_id, manoeuvre, path.path_id,
            # Supply own at 'lane_id' to MovementDeclaration.
            own["lane_id"], now, self.epoch)
        # Set self.authored[ldm.ego_id] to message.
        self.authored[ldm.ego_id] = message
        # Return message to the caller.
        return message

    # Publish using the inputs and processing steps below.
    # Input authenticated_sender: the supplied authenticated sender.
    # Input message: the supplied message.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def publish(self, authenticated_sender, message):
        # Run this branch when message is the same object as None.
        if message is None:
            # Return no value to the caller.
            return
        # Run this branch when authenticated_sender differs from message.sender_id.
        if authenticated_sender != message.sender_id:
            # Raise ValueError with the text 'DECLARATION_SENDER_MISMATCH' to stop this execution path.
            raise ValueError("DECLARATION_SENDER_MISMATCH")
        # Run this branch when authenticated_sender from self.authored; use None if absent differs from message.
        if self.authored.get(authenticated_sender) != message:
            # Raise ValueError with the text 'DECLARATION_NOT_SENDER_AUTHORED' to stop this execution path.
            raise ValueError("DECLARATION_NOT_SENDER_AUTHORED")
        # Append message to self.messages.setdefault(authenticated_sender, []).
        self.messages.setdefault(authenticated_sender, []).append(message)

    # Validate using the inputs and processing steps below.
    # Input receiver: the supplied receiver.
    # Input sender: the supplied sender.
    # Input now: the time used for this operation.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def validate(self, receiver, sender, now):
        # Set messages to sender from self.messages; use an empty tuple if absent.
        messages = self.messages.get(sender, ())
        # Run this branch when the negation of messages.
        if not messages:
            # Return a tuple containing None, the text 'MISSING_MOVEMENT_DECLARATION' to the caller.
            return None, "MISSING_MOVEMENT_DECLARATION"
        # Run this branch when the number of entries in messages differs from 1.
        if len(messages) != 1:
            # Return a tuple containing None, the text 'CONTRADICTORY_MOVEMENT_DECLARATIONS' to the caller.
            return None, "CONTRADICTORY_MOVEMENT_DECLARATIONS"
        # Set message to messages at 0.
        message = messages[0]
        # Set track to sender from receiver.tracks; use an empty dictionary if absent.
        track = receiver.tracks.get(sender, {})
        # Set path to message.path_id from self.paths.paths; use None if absent.
        path = self.paths.paths.get(message.path_id)
        # Run this branch when message.protocol differs from PROTOCOL_VERSION or message.sender_id differs from
        # sender or message.manoeuvre does not belong to MANOEUVRES or path is the same object as None or
        # path.manoeuvre differs from message.manoeuvre.
        if (message.protocol != PROTOCOL_VERSION or message.sender_id != sender or
                # Evaluate message.manoeuvre does not belong to MANOEUVRES as part of the enclosing expression.
                message.manoeuvre not in MANOEUVRES or path is None or
                # Evaluate path.manoeuvre differs from message.manoeuvre as part of the enclosing expression.
                path.manoeuvre != message.manoeuvre):
            # Return a tuple containing None, the text 'INVALID_MOVEMENT_DECLARATION' to the caller.
            return None, "INVALID_MOVEMENT_DECLARATION"
        # Run this branch when the negation of the result of same_instant(now, message.timestamp, self.timestamp)
        # or message.epoch differs from self.epoch.
        if not same_instant(now, message.timestamp, self.timestamp) or message.epoch != self.epoch:
            # Return a tuple containing None, the text 'STALE_MOVEMENT_DECLARATION' to the caller.
            return None, "STALE_MOVEMENT_DECLARATION"
        # Run this branch when sender from self.authored; use None if absent differs from message.
        if self.authored.get(sender) != message:
            # Return a tuple containing None, the text 'UNTRUSTED_MOVEMENT_DECLARATION' to the caller.
            return None, "UNTRUSTED_MOVEMENT_DECLARATION"
        # Run this branch when 'lane_id' from track; use None if absent differs from message.lane_id or the
        # negation of the result of self.paths.lane_belongs_to_path(message.lane_id, path).
        if (track.get("lane_id") != message.lane_id or
                # Evaluate the negation of the result of self.paths.lane_belongs_to_path(message.lane_id, path) as
                # part of the enclosing expression.
                not self.paths.lane_belongs_to_path(message.lane_id, path)):
            # Return a tuple containing None, the text 'DECLARATION_LANE_MISMATCH' to the caller.
            return None, "DECLARATION_LANE_MISMATCH"
        # Return a tuple containing message, None to the caller.
        return message, None

    # Restrict only regulatory premises; retain original uncertain evidence.
    # Input ldm: the supplied ldm.
    # Input graph: the supplied graph.
    # Input now: the time used for this operation.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def reconcile(self, ldm, graph, now):
        """Restrict only regulatory premises; retain original uncertain evidence."""
        # Set result to the result of copy.deepcopy(graph).
        result = copy.deepcopy(graph)
        # Set (errors, records, edges) to a tuple containing an empty list, an empty list, an empty list.
        errors, records, edges = [], [], []
        # Validate every locally represented current actor, even when no
        # hypothetical conflict exists. Invalid information never certifies entry.
        # Set declarations to an empty dictionary.
        declarations = {}
        # Iterate over the sorted values from ldm.tracks, binding each item to sender.
        for sender in sorted(ldm.tracks):
            # Set (message, error) to the result of self.validate(ldm, sender, now).
            message, error = self.validate(ldm, sender, now)
            # Run this branch when error.
            if error:
                # Append a dictionary containing sender_id, reason to errors.
                errors.append({"sender_id": sender, "reason": error})
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set declarations[sender] to message.
                declarations[sender] = message
                # Append the result of asdict(message) to records.
                records.append(asdict(message))
        # Iterate over 'edges' from result; use an empty tuple if absent, binding each item to edge.
        for edge in result.get("edges", ()):
            # Set target to edge at 'target_track_id'.
            target = edge["target_track_id"]
            # Set message to target from declarations; use None if absent.
            message = declarations.get(target)
            # Set edge['conditional_candidate_paths'] to the result of copy.deepcopy(edge at
            # 'spatially_conflicting_candidate_paths').
            edge["conditional_candidate_paths"] = copy.deepcopy(edge["spatially_conflicting_candidate_paths"])
            # Run this branch when message is the same object as None.
            if message is None:
                # Set edge['claim_premise_status'] to the text 'UNRESOLVED_DECLARATION'.
                edge["claim_premise_status"] = "UNRESOLVED_DECLARATION"
                # Append edge to edges.
                edges.append(edge)
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set candidates to edge at 'spatially_conflicting_candidate_paths'.
            candidates = edge["spatially_conflicting_candidate_paths"]
            # Set values to message.manoeuvre from candidates; use an empty tuple if absent.
            values = candidates.get(message.manoeuvre, ())
            # Set values to a tuple containing values when whether values has type str, otherwise a tuple built
            # from values.
            values = (values,) if isinstance(values, str) else tuple(values)
            # Run this branch when message.path_id does not belong to values.
            if message.path_id not in values:
                # Map-proven nonconflict for this declared movement; no legal
                # edge is removed for a physically conflicting declared pair.
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set edge['spatially_conflicting_candidate_paths'] to a dictionary of the supplied entries.
            edge["spatially_conflicting_candidate_paths"] = {message.manoeuvre: message.path_id}
            # Set edge['target_candidate_paths'] to a dictionary of the supplied entries.
            edge["target_candidate_paths"] = {message.manoeuvre: message.path_id}
            # Set edge['claim_premise_status'] to the text 'VALIDATED_DECLARATION'.
            edge["claim_premise_status"] = "VALIDATED_DECLARATION"
            # Set edge['movement_declaration'] to the result of asdict(message).
            edge["movement_declaration"] = asdict(message)
            # Append edge to edges.
            edges.append(edge)
        # Set result['edges'] to a tuple built from edges.
        result["edges"] = tuple(edges)
        # Set result['movement_declaration_protocol'] to PROTOCOL_VERSION.
        result["movement_declaration_protocol"] = PROTOCOL_VERSION
        # Set result['movement_declarations'] to a tuple built from records.
        result["movement_declarations"] = tuple(records)
        # Set result['movement_declaration_errors'] to a tuple built from errors.
        result["movement_declaration_errors"] = tuple(errors)
        # Set ldm.current_movement_declaration_errors to a tuple built from errors.
        ldm.current_movement_declaration_errors = tuple(errors)
        # Return result to the caller.
        return result
