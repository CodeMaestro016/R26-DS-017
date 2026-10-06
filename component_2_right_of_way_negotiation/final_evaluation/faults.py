"""Bounded message faults at the real controller interface, not network claims."""
from dataclasses import replace
from conflict import MapPathManager, ConflictZoneManager
from negotiation_execution import (DecentralizedEgoExecutionController, EgoExecutionContext,
    EgoCoordinationCommitment, ExecutionStateMessage)

def evaluate_faults():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    def state(path_id):
        path = paths.paths[path_id]
        return {"position": tuple(path.centerline_geometry[0]),
            "lane_id": path.incoming_lane_id, "lane_position": 30., "lane_length": 150.,
            "length": 5., "width": 1.8, "speed": 0., "heading_radians": 0.}
    own_path, peer_path = "N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT"
    message = ExecutionStateMessage("peer", peer_path, state(peer_path), 1.)
    context = EgoExecutionContext("ego", state(own_path), own_path, 1.,
        (EgoCoordinationCommitment("ego", "peer", ("fault_test",)),), (message,), True, 1.)
    variants = {
        "missing_required_coordination": replace(context, coordination_complete=False),
        "stale_coordination": replace(context, coordination_timestamp=.5),
        "missing_clearance": replace(context, peer_messages=()),
        "stale_clearance": replace(context, peer_messages=(replace(message, timestamp=.5),))}
    results = []
    for name, fault in variants.items():
        controller = DecentralizedEgoExecutionController(paths, zones)
        decision = controller.decide(fault)
        # Repeated fault remains held; simulated attempted entry is rejected.
        blocked_entry_rejected = False
        attempted = dict(fault.ego_state, lane_id=paths.paths[own_path].outgoing_lane_id,
                         lane_position=1.)
        try:
            controller.decide(replace(fault, ego_state=attempted))
        except RuntimeError as error:
            blocked_entry_rejected = str(error) == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"
        results.append({"fault": name, "permission": decision.permission,
            "reason": decision.reason, "blocked_entry_rejected": blocked_entry_rejected,
            "passed": decision.permission == "SAFE_HOLD" and blocked_entry_rejected,
            "scope": "Controlled controller-message test; no packet network or physical collision injection"})
    return results
