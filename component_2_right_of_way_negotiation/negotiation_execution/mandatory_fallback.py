"""Endpoint-authored, ego-reconstructed ordering; never a shared permission plan."""
# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import math for use in this module.
import math
# Import same_instant from negotiation_learning.v2v_claim_bus for the operations below.
from negotiation_learning.v2v_claim_bus import same_instant

# Set VERSION to the text 'MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1'.
VERSION = "MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EndpointEvidence to group the state and operations declared below.
# Declared fields: sender_id, timestamp, epoch, members, commitments, mandatory, eligible_peers, mappo_receipt,
# arrival.
# Construction and attribute behavior follow the declared decorators and base classes.
class EndpointEvidence:
    # Declare sender_id as str for this data structure.
    sender_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare epoch as tuple for this data structure.
    epoch: tuple
    # Declare members as tuple for this data structure.
    members: tuple
    # Declare commitments as tuple for this data structure.
    commitments: tuple
    # Declare mandatory as tuple for this data structure.
    mandatory: tuple
    # Declare eligible_peers as tuple for this data structure.
    eligible_peers: tuple
    # Declare mappo_receipt as bool for this data structure.
    mappo_receipt: bool
    # Declare arrival as float | None for this data structure.
    arrival: float | None


# Validate endpoint evidence and retained constraints, then derive an ego-local order; invalid evidence or a cycle
# returns a failure reason.
# Input ego: the ego vehicle used in this calculation.
# Input now: the time used for this operation.
# Input epoch: the supplied epoch.
# Input evidence: the supplied evidence.
# Input physical_messages: the supplied physical messages.
# Input paths: the supplied paths.
# Input zones: the supplied zones.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def legal_order(ego, now, epoch, evidence, physical_messages, paths, zones=None):
    """Validate a same-step endpoint transcript and derive an ego-local order.

    Transport authenticates authors; both endpoints must attest every constraint.
    Only waived/incomparable eligible pairs may use the resulting tie order.
    A cycle in retained constraints fails closed, regardless of time waited.
    """
    # Set rows to a dictionary of r.sender_id mapped to r for r in evidence.
    rows = {r.sender_id: r for r in evidence}
    # Run this branch when the number of entries in rows differs from the number of entries in evidence or ego
    # does not belong to rows.
    if len(rows) != len(evidence) or ego not in rows:
        # Return a tuple containing None, the text 'MISSING_OR_DUPLICATE_ENDPOINT_EVIDENCE' to the caller.
        return None, "MISSING_OR_DUPLICATE_ENDPOINT_EVIDENCE"
    # Set members to rows[ego].members.
    members = rows[ego].members
    # Run this branch when the number of entries in members is greater than 4 or a set built from members differs
    # from a set built from rows.
    if len(members) > 4 or set(members) != set(rows):
        # Return a tuple containing None, the text 'INCOMPLETE_ENDPOINT_EVIDENCE' to the caller.
        return None, "INCOMPLETE_ENDPOINT_EVIDENCE"
    # Set physical to a dictionary of m.sender_id mapped to m for m in physical_messages.
    physical = {m.sender_id: m for m in physical_messages}
    # Run this branch when a set built from physical differs from a set built from rows.
    if set(physical) != set(rows):
        # Return a tuple containing None, the text 'INCOMPLETE_ENDPOINT_PHYSICS' to the caller.
        return None, "INCOMPLETE_ENDPOINT_PHYSICS"
    # Set constraints to an empty set.
    constraints = set()
    # Iterate over key/value pairs from rows, binding each item to (sender, row).
    for sender, row in rows.items():
        # Run this branch when the negation of row.mappo_receipt or row.members differs from members or row.epoch
        # differs from epoch or the negation of the result of same_instant(row.timestamp, now) or row.arrival is
        # the same object as None or the negation of whether row.arrival contains finite numeric values or
        # row.arrival is greater than now.
        if (not row.mappo_receipt or row.members != members or row.epoch != epoch
                # Evaluate the negation of the result of same_instant(row.timestamp, now) as part of the enclosing
                # expression.
                or not same_instant(row.timestamp, now)
                # Evaluate the negation of whether row.arrival contains finite numeric values as part of the
                # enclosing expression.
                or row.arrival is None or not math.isfinite(row.arrival)
                # Evaluate row.arrival is greater than now as part of the enclosing expression.
                or row.arrival > now):
            # Return a tuple containing None, the text 'INVALID_ENDPOINT_RECEIPT' to the caller.
            return None, "INVALID_ENDPOINT_RECEIPT"
        # Set msg to physical at sender.
        msg = physical[sender]
        # Run this branch when msg.coordination_epoch differs from epoch or the negation of the result of
        # same_instant(msg.timestamp, now) or msg.queue_arrival_seconds differs from row.arrival.
        if (msg.coordination_epoch != epoch or not same_instant(msg.timestamp, now)
                # Evaluate msg.queue_arrival_seconds differs from row.arrival as part of the enclosing expression.
                or msg.queue_arrival_seconds != row.arrival):
            # Return a tuple containing None, the text 'ENDPOINT_PHYSICS_MISMATCH' to the caller.
            return None, "ENDPOINT_PHYSICS_MISMATCH"
        # Iterate over a tuple containing the text 'commitments', the text 'mandatory', binding each item to name.
        for name in ("commitments", "mandatory"):
            # Iterate over the requested attribute of row, binding each item to c.
            for c in getattr(row, name):
                # Set (a, b) to a tuple containing c.yielding_vehicle_id, c.priority_vehicle_id.
                a, b = c.yielding_vehicle_id, c.priority_vehicle_id
                # Run this branch when sender does not belong to a tuple containing a, b or a equals b or a does
                # not belong to rows or b does not belong to rows or c.agreement_id differs from epoch or c does
                # not belong to the requested attribute of rows at b if sender == a else a.
                if (sender not in (a, b) or a == b or a not in rows or b not in rows
                        # Evaluate c.agreement_id differs from epoch as part of the enclosing expression.
                        or c.agreement_id != epoch
                        # Evaluate c does not belong to the requested attribute of rows at b if sender == a else a
                        # as part of the enclosing expression.
                        or c not in getattr(rows[b if sender == a else a], name)):
                    # Return a tuple containing None, the text 'UNAUTHENTICATED_PAIR_CONSTRAINT' to the caller.
                    return None, "UNAUTHENTICATED_PAIR_CONSTRAINT"
                # Add a tuple containing a, b to constraints.
                constraints.add((a, b))
        # Iterate over row.eligible_peers, binding each item to peer.
        for peer in row.eligible_peers:
            # Run this branch when peer does not belong to rows or sender does not belong to
            # rows[peer].eligible_peers.
            if peer not in rows or sender not in rows[peer].eligible_peers:
                # Return a tuple containing None, the text 'ASYMMETRIC_FALLBACK_EVIDENCE' to the caller.
                return None, "ASYMMETRIC_FALLBACK_EVIDENCE"
    # Preserve the controller's independent oncoming turning shield as well.
    # Iterate over members, binding each item to a.
    for a in members:
        # Iterate over members, binding each item to b.
        for b in members:
            # Run this branch when a equals b.
            if a == b:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set (pa, pb) to a tuple containing paths.paths at physical[a].movement_path_id, paths.paths at
            # physical[b].movement_path_id.
            pa, pb = paths.paths[physical[a].movement_path_id], paths.paths[physical[b].movement_path_id]
            # Run this branch when zones is a different object from None and the result of
            # zones.zone_record(pa.path_id, physical[a].state at 'width', pb.path_id, physical[b].state at
            # 'width') is the same object as None.
            if zones is not None and zones.zone_record(pa.path_id, physical[a].state["width"],
                    # Supply physical[b].state at 'width' to zones.zone_record.
                    pb.path_id, physical[b].state["width"]) is None:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when the result of paths.approach_relation(pa.path_id, pb.path_id) equals the text
            # 'ONCOMING'.
            if paths.approach_relation(pa.path_id, pb.path_id) == "ONCOMING":
                # Run this branch when pa.manoeuvre belongs to a set containing 'LEFT', 'RIGHT' and pb.manoeuvre
                # equals the text 'STRAIGHT' or pa.manoeuvre equals the text 'LEFT' and pb.manoeuvre equals the
                # text 'RIGHT'.
                if ((pa.manoeuvre in {"LEFT", "RIGHT"} and pb.manoeuvre == "STRAIGHT")
                        # Evaluate pa.manoeuvre equals the text 'LEFT' and pb.manoeuvre equals the text 'RIGHT' as
                        # part of the enclosing expression.
                        or (pa.manoeuvre == "LEFT" and pb.manoeuvre == "RIGHT")):
                    # Add a tuple containing a, b to constraints.
                    constraints.add((a, b))
    # Set (remaining, ordered) to a tuple containing a set built from members, an empty list.
    remaining, ordered = set(members), []
    # Repeat the following steps while remaining.
    while remaining:
        # Set ready to a list of a for a in remaining; retain entries satisfying the negation of whether any item
        # is true in a lazy sequence of x == a and y in...
        ready = [a for a in remaining if not any(x == a and y in remaining for x, y in constraints)]
        # Run this branch when the negation of ready.
        if not ready:
            # Return a tuple containing None, the text 'RETAINED_MANDATORY_OR_COMMITMENT_CYCLE' to the caller.
            return None, "RETAINED_MANDATORY_OR_COMMITMENT_CYCLE"
        # Stable numerical ordering, no waiting-time threshold or learned-action change.
        # Set chosen to the minimum of ready.
        chosen = min(ready, key=lambda a: (rows[a].arrival, a))
        # Append chosen to ordered.
        ordered.append(chosen)
        # Remove chosen from remaining.
        remaining.remove(chosen)
    # Return a tuple containing a tuple built from ordered, None to the caller.
    return tuple(ordered), None
