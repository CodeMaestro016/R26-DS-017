"""Physical queue-front selection, independent of vehicle IDs and policy."""


# One front per incoming lane; retain a leader until its rear clears.
# Input states: the supplied states.
# Input paths: the supplied paths.
# Input movement_by_vehicle: the supplied movement by vehicle.
# Output: a tuple built from the sorted values from a lazy sequence of max(rows) at 1 for rows in values from
# candidates.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def select_queue_heads(states, paths, movement_by_vehicle):
    """One front per incoming lane; retain a leader until its rear clears.

    Internal-lane occupants and vehicles still straddling the outgoing lane
    block their incoming followers from becoming negotiators.
    """
    # Set candidates to an empty dictionary.
    candidates = {}
    # Iterate over key/value pairs from states, binding each item to (vehicle_id, state).
    for vehicle_id, state in states.items():
        # Set path to paths.paths at movement_by_vehicle[vehicle_id].
        path = paths.paths[movement_by_vehicle[vehicle_id]]
        # Set lane to state at 'lane_id'.
        lane = state["lane_id"]
        # Run this branch when lane equals path.incoming_lane_id.
        if lane == path.incoming_lane_id:
            # Set rank to a tuple containing 0, a floating-point number built from state at 'lane_position'.
            rank = (0, float(state["lane_position"]))
        # Run this branch when lane belongs to path.internal_lane_ids.
        elif lane in path.internal_lane_ids:
            # Set rank to a tuple containing 1, a floating-point number built from state at 'lane_position'.
            rank = (1, float(state["lane_position"]))
        # Run this branch when lane equals path.outgoing_lane_id and state at 'lane_position' is at most state at
        # 'length'.
        elif lane == path.outgoing_lane_id and state["lane_position"] <= state["length"]:
            # Set rank to a tuple containing 2, a floating-point number built from state at 'lane_position'.
            rank = (2, float(state["lane_position"]))
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Append a tuple containing rank, vehicle_id to candidates.setdefault(path.incoming_lane_id, []).
        candidates.setdefault(path.incoming_lane_id, []).append((rank, vehicle_id))
    # Return a tuple built from the sorted values from a lazy sequence of max(rows) at 1 for rows in values from
    # candidates to the caller.
    return tuple(sorted(max(rows)[1] for rows in candidates.values()))


# Approach queue depth using the inputs and processing steps below.
# Input states: the supplied states.
# Input paths: the supplied paths.
# Input movements: the supplied movements.
# Output: counts.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def approach_queue_depth(states, paths, movements):
    # Set counts to a dictionary of approach mapped to 0 for approach in the text 'NESW'.
    counts = {approach: 0 for approach in "NESW"}
    # Iterate over key/value pairs from states, binding each item to (vehicle_id, state).
    for vehicle_id, state in states.items():
        # Set path to paths.paths at movements[vehicle_id].
        path = paths.paths[movements[vehicle_id]]
        # Run this branch when state at 'lane_id' equals path.incoming_lane_id.
        if state["lane_id"] == path.incoming_lane_id:
            # Update counts[path.path_id[0]] to its current value plus 1.
            counts[path.path_id[0]] += 1
    # Return counts to the caller.
    return counts
