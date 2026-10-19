"""Expose an ego's held entry to SUMO's native junction request model.

A speed cap alone leaves a native approach request active. A planned stop
withdraws that request without disabling native right-of-way or collision safety.
"""
VERSION = "NATIVE_EXPLICIT_JUNCTION_HOLD_V1"
SUMO_POSITION_EPSILON_METERS = 0.001
# Administrative stop duration exceeds all supported demos. Speed constraints
# remain active independently; elapsed time never grants entry permission.
ADMINISTRATIVE_HOLD_SECONDS = 1_000_000.0


class NativeJunctionHold:
    def __init__(self):
        self.stop = None

    def synchronize(self, context, decision, paths, vehicle_api):
        ego = context.ego_id
        if decision.permission == "PERMITTED":
            if self.stop is not None:
                edge, lane_index, position = self.stop
                vehicle_api.setStop(ego, edge, pos=position,
                                    laneIndex=lane_index, duration=0)
                self.stop = None
                return "NATIVE_HOLD_RELEASED_AFTER_PERMISSION"
            return None
        path = paths.paths[context.movement_path_id]
        if (self.stop is None and context.ego_state['lane_id'] == path.incoming_lane_id
                and any(zone == 'JUNCTION_ENTRY' for zone, _, _ in decision.blocked_zones)):
            edge = context.ego_state['road_id']
            lane_index = vehicle_api.getLaneIndex(ego)
            position = context.ego_state['lane_length'] - SUMO_POSITION_EPSILON_METERS
            vehicle_api.setStop(ego, edge, pos=position, laneIndex=lane_index,
                                duration=ADMINISTRATIVE_HOLD_SECONDS)
            self.stop = (edge, lane_index, position)
            return "NATIVE_HOLD_INSTALLED"
        return None
