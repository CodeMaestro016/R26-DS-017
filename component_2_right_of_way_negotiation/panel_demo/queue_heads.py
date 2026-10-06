"""Physical queue-front selection, independent of vehicle IDs and policy."""


def select_queue_heads(states, paths, movement_by_vehicle):
    """One front per incoming lane; retain a leader until its rear clears.

    Internal-lane occupants and vehicles still straddling the outgoing lane
    block their incoming followers from becoming negotiators.
    """
    candidates = {}
    for vehicle_id, state in states.items():
        path = paths.paths[movement_by_vehicle[vehicle_id]]
        lane = state["lane_id"]
        if lane == path.incoming_lane_id:
            rank = (0, float(state["lane_position"]))
        elif lane in path.internal_lane_ids:
            rank = (1, float(state["lane_position"]))
        elif lane == path.outgoing_lane_id and state["lane_position"] <= state["length"]:
            rank = (2, float(state["lane_position"]))
        else:
            continue
        candidates.setdefault(path.incoming_lane_id, []).append((rank, vehicle_id))
    return tuple(sorted(max(rows)[1] for rows in candidates.values()))


def approach_queue_depth(states, paths, movements):
    counts = {approach: 0 for approach in "NESW"}
    for vehicle_id, state in states.items():
        path = paths.paths[movements[vehicle_id]]
        if state["lane_id"] == path.incoming_lane_id:
            counts[path.path_id[0]] += 1
    return counts
