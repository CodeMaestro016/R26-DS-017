"""Endpoint-authored, ego-reconstructed ordering; never a shared permission plan."""
from dataclasses import dataclass
import math
from negotiation_learning.v2v_claim_bus import same_instant

VERSION = "MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1"


@dataclass(frozen=True)
class EndpointEvidence:
    sender_id: str
    timestamp: float
    epoch: tuple
    members: tuple
    commitments: tuple
    mandatory: tuple
    eligible_peers: tuple
    mappo_receipt: bool
    arrival: float | None


def legal_order(ego, now, epoch, evidence, physical_messages, paths, zones=None):
    """Validate a same-step endpoint transcript and derive an ego-local order.

    Transport authenticates authors; both endpoints must attest every constraint.
    Only waived/incomparable eligible pairs may use the resulting tie order.
    A cycle in retained constraints fails closed, regardless of time waited.
    """
    rows = {r.sender_id: r for r in evidence}
    if len(rows) != len(evidence) or ego not in rows:
        return None, "MISSING_OR_DUPLICATE_ENDPOINT_EVIDENCE"
    members = rows[ego].members
    if len(members) > 4 or set(members) != set(rows):
        return None, "INCOMPLETE_ENDPOINT_EVIDENCE"
    physical = {m.sender_id: m for m in physical_messages}
    if set(physical) != set(rows):
        return None, "INCOMPLETE_ENDPOINT_PHYSICS"
    constraints = set()
    for sender, row in rows.items():
        if (not row.mappo_receipt or row.members != members or row.epoch != epoch
                or not same_instant(row.timestamp, now)
                or row.arrival is None or not math.isfinite(row.arrival)
                or row.arrival > now):
            return None, "INVALID_ENDPOINT_RECEIPT"
        msg = physical[sender]
        if (msg.coordination_epoch != epoch or not same_instant(msg.timestamp, now)
                or msg.queue_arrival_seconds != row.arrival):
            return None, "ENDPOINT_PHYSICS_MISMATCH"
        for name in ("commitments", "mandatory"):
            for c in getattr(row, name):
                a, b = c.yielding_vehicle_id, c.priority_vehicle_id
                if (sender not in (a, b) or a == b or a not in rows or b not in rows
                        or c.agreement_id != epoch
                        or c not in getattr(rows[b if sender == a else a], name)):
                    return None, "UNAUTHENTICATED_PAIR_CONSTRAINT"
                constraints.add((a, b))
        for peer in row.eligible_peers:
            if peer not in rows or sender not in rows[peer].eligible_peers:
                return None, "ASYMMETRIC_FALLBACK_EVIDENCE"
    # Preserve the controller's independent oncoming turning shield as well.
    for a in members:
        for b in members:
            if a == b:
                continue
            pa, pb = paths.paths[physical[a].movement_path_id], paths.paths[physical[b].movement_path_id]
            if zones is not None and zones.zone_record(pa.path_id, physical[a].state["width"],
                    pb.path_id, physical[b].state["width"]) is None:
                continue
            if paths.approach_relation(pa.path_id, pb.path_id) == "ONCOMING":
                if ((pa.manoeuvre in {"LEFT", "RIGHT"} and pb.manoeuvre == "STRAIGHT")
                        or (pa.manoeuvre == "LEFT" and pb.manoeuvre == "RIGHT")):
                    constraints.add((a, b))
    remaining, ordered = set(members), []
    while remaining:
        ready = [a for a in remaining if not any(x == a and y in remaining for x, y in constraints)]
        if not ready:
            return None, "RETAINED_MANDATORY_OR_COMMITMENT_CYCLE"
        # Stable numerical ordering, no waiting-time threshold or learned-action change.
        chosen = min(ready, key=lambda a: (rows[a].arrival, a))
        ordered.append(chosen)
        remaining.remove(chosen)
    return tuple(ordered), None
