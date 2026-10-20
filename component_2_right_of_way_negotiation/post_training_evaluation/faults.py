"""Bounded message faults at the real controller interface, not network claims."""
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import MapPathManager, ConflictZoneManager from conflict for the operations below.
from conflict import MapPathManager, ConflictZoneManager
# Import DecentralizedEgoExecutionController, EgoExecutionContext, EgoCoordinationCommitment,
# ExecutionStateMessage from negotiation_execution for the operations below.
from negotiation_execution import (DecentralizedEgoExecutionController, EgoExecutionContext,
    EgoCoordinationCommitment, ExecutionStateMessage)

# Evaluate faults using the inputs and processing steps below.
# Output: results.
# Processing: iterate over the relevant records, then handle the specified errors.
def evaluate_faults():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # State using the inputs and processing steps below.
    # Input path_id: the supplied path id.
    # Output: a dictionary containing position, lane_id, lane_position, lane_length, length, width, speed,
    # heading_radians.
    def state(path_id):
        # Set path to paths.paths at path_id.
        path = paths.paths[path_id]
        # Return a dictionary containing position, lane_id, lane_position, lane_length, length, width, speed,
        # heading_radians to the caller.
        return {"position": tuple(path.centerline_geometry[0]),
            # Store path.incoming_lane_id under 'lane_id'.
            # Store 30.0 under 'lane_position'.
            # Store 150.0 under 'lane_length'.
            "lane_id": path.incoming_lane_id, "lane_position": 30., "lane_length": 150.,
            # Store 5.0 under 'length'.
            # Store 1.8 under 'width'.
            # Store 0.0 under 'speed'.
            # Store 0.0 under 'heading_radians'.
            "length": 5., "width": 1.8, "speed": 0., "heading_radians": 0.}
    # Set (own_path, peer_path) to a tuple containing the text 'N_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT'.
    own_path, peer_path = "N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT"
    # Set message to the result of ExecutionStateMessage(the text 'peer', peer_path, the result of
    # state(peer_path), 1.0).
    message = ExecutionStateMessage("peer", peer_path, state(peer_path), 1.)
    # Set context to the result of EgoExecutionContext(the text 'ego', the result of state(own_path), own_path,
    # 1.0, a tuple containing the result of...).
    context = EgoExecutionContext("ego", state(own_path), own_path, 1.,
        # Supply a tuple containing the result of EgoCoordinationCommitment(the text 'ego', the text 'peer', a
        # tuple containing the text... to EgoExecutionContext.
        (EgoCoordinationCommitment("ego", "peer", ("fault_test",)),), (message,), True, 1.)
    # Set variants to a dictionary containing missing_required_coordination, stale_coordination,
    # missing_clearance, stale_clearance.
    variants = {
        # Store the result of replace(context) under 'missing_required_coordination'.
        "missing_required_coordination": replace(context, coordination_complete=False),
        # Store the result of replace(context) under 'stale_coordination'.
        "stale_coordination": replace(context, coordination_timestamp=.5),
        # Store the result of replace(context) under 'missing_clearance'.
        "missing_clearance": replace(context, peer_messages=()),
        # Store the result of replace(context) under 'stale_clearance'.
        "stale_clearance": replace(context, peer_messages=(replace(message, timestamp=.5),))}
    # Set results to an empty list.
    results = []
    # Iterate over key/value pairs from variants, binding each item to (name, fault).
    for name, fault in variants.items():
        # Set controller to the result of DecentralizedEgoExecutionController(paths, zones).
        controller = DecentralizedEgoExecutionController(paths, zones)
        # Set decision to the result of controller.decide(fault).
        decision = controller.decide(fault)
        # Repeated fault remains held; simulated attempted entry is rejected.
        # Set blocked_entry_rejected to False.
        blocked_entry_rejected = False
        # Set attempted to a dictionary built from fault.ego_state.
        attempted = dict(fault.ego_state, lane_id=paths.paths[own_path].outgoing_lane_id,
                         # Supply lane_position as 1.0.
                         lane_position=1.)
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call controller.decide with the supplied arguments.
            controller.decide(replace(fault, ego_state=attempted))
        # Handle RuntimeError as error using the recovery steps below.
        except RuntimeError as error:
            # Set blocked_entry_rejected to a string built from error equals the text
            # 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'.
            blocked_entry_rejected = str(error) == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"
        # Append a dictionary containing fault, permission, reason, blocked_entry_rejected, passed, scope to
        # results.
        results.append({"fault": name, "permission": decision.permission,
            # Store decision.reason under 'reason'.
            # Store blocked_entry_rejected under 'blocked_entry_rejected'.
            "reason": decision.reason, "blocked_entry_rejected": blocked_entry_rejected,
            # Store decision.permission equals the text 'SAFE_HOLD' and blocked_entry_rejected under 'passed'.
            "passed": decision.permission == "SAFE_HOLD" and blocked_entry_rejected,
            "scope": "Controlled controller-message test; no packet network or physical collision injection"})
    # Return results to the caller.
    return results
