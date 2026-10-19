"""Approved cooperative conditional-claim protocol; no movement permissions."""
from dataclasses import asdict, dataclass
import copy

from .v2v_claim_bus import same_instant

PROTOCOL_VERSION = "CONDITIONAL_CLAIM_RECONCILIATION_V1"
MANOEUVRES = frozenset({"LEFT", "RIGHT", "STRAIGHT"})


@dataclass(frozen=True)
class MovementDeclaration:
    sender_id: str
    manoeuvre: str
    path_id: str
    lane_id: str
    timestamp: float
    epoch: tuple
    protocol: str = PROTOCOL_VERSION


class MovementDeclarationBus:
    """Same-step sender-bound transport, matching the ideal precedence channel.

    Authenticated sender binding is a simulation protocol assumption, not a
    cryptographic guarantee. A sender reads only its own navigation/LDM state.
    No receiver is given another vehicle's route or a global movement mapping.
    """
    def __init__(self, paths):
        self.paths = paths
        self.messages = {}
        self.timestamp = None
        self.epoch = ()
        self.authored = {}

    def begin_step(self, now):
        self.timestamp = now
        self.epoch = (PROTOCOL_VERSION, now)
        self.messages = {}
        self.authored = {}

    def author(self, ldm, now):
        own = ldm.tracks.get(ldm.ego_id, {})
        manoeuvre = own.get("self_planned_manoeuvre")
        path = self.paths.resolve_path(own.get("lane_id", ""), manoeuvre)
        if manoeuvre not in MANOEUVRES or path is None:
            return None
        message = MovementDeclaration(ldm.ego_id, manoeuvre, path.path_id,
            own["lane_id"], now, self.epoch)
        self.authored[ldm.ego_id] = message
        return message

    def publish(self, authenticated_sender, message):
        if message is None:
            return
        if authenticated_sender != message.sender_id:
            raise ValueError("DECLARATION_SENDER_MISMATCH")
        if self.authored.get(authenticated_sender) != message:
            raise ValueError("DECLARATION_NOT_SENDER_AUTHORED")
        self.messages.setdefault(authenticated_sender, []).append(message)

    def validate(self, receiver, sender, now):
        messages = self.messages.get(sender, ())
        if not messages:
            return None, "MISSING_MOVEMENT_DECLARATION"
        if len(messages) != 1:
            return None, "CONTRADICTORY_MOVEMENT_DECLARATIONS"
        message = messages[0]
        track = receiver.tracks.get(sender, {})
        path = self.paths.paths.get(message.path_id)
        if (message.protocol != PROTOCOL_VERSION or message.sender_id != sender or
                message.manoeuvre not in MANOEUVRES or path is None or
                path.manoeuvre != message.manoeuvre):
            return None, "INVALID_MOVEMENT_DECLARATION"
        if not same_instant(now, message.timestamp, self.timestamp) or message.epoch != self.epoch:
            return None, "STALE_MOVEMENT_DECLARATION"
        if self.authored.get(sender) != message:
            return None, "UNTRUSTED_MOVEMENT_DECLARATION"
        if (track.get("lane_id") != message.lane_id or
                not self.paths.lane_belongs_to_path(message.lane_id, path)):
            return None, "DECLARATION_LANE_MISMATCH"
        return message, None

    def reconcile(self, ldm, graph, now):
        """Restrict only regulatory premises; retain original uncertain evidence."""
        result = copy.deepcopy(graph)
        errors, records, edges = [], [], []
        # Validate every locally represented current actor, even when no
        # hypothetical conflict exists. Invalid information never certifies entry.
        declarations = {}
        for sender in sorted(ldm.tracks):
            message, error = self.validate(ldm, sender, now)
            if error:
                errors.append({"sender_id": sender, "reason": error})
            else:
                declarations[sender] = message
                records.append(asdict(message))
        for edge in result.get("edges", ()):
            target = edge["target_track_id"]
            message = declarations.get(target)
            edge["conditional_candidate_paths"] = copy.deepcopy(edge["spatially_conflicting_candidate_paths"])
            if message is None:
                edge["claim_premise_status"] = "UNRESOLVED_DECLARATION"
                edges.append(edge)
                continue
            candidates = edge["spatially_conflicting_candidate_paths"]
            values = candidates.get(message.manoeuvre, ())
            values = (values,) if isinstance(values, str) else tuple(values)
            if message.path_id not in values:
                # Map-proven nonconflict for this declared movement; no legal
                # edge is removed for a physically conflicting declared pair.
                continue
            edge["spatially_conflicting_candidate_paths"] = {message.manoeuvre: message.path_id}
            edge["target_candidate_paths"] = {message.manoeuvre: message.path_id}
            edge["claim_premise_status"] = "VALIDATED_DECLARATION"
            edge["movement_declaration"] = asdict(message)
            edges.append(edge)
        result["edges"] = tuple(edges)
        result["movement_declaration_protocol"] = PROTOCOL_VERSION
        result["movement_declarations"] = tuple(records)
        result["movement_declaration_errors"] = tuple(errors)
        ldm.current_movement_declaration_errors = tuple(errors)
        return result
