"""Expose an ego's held entry to SUMO's native junction request model.

A speed cap alone leaves a native approach request active. A planned stop
withdraws that request without disabling native right-of-way or collision safety.
"""
# Set VERSION to the text 'NATIVE_EXPLICIT_JUNCTION_HOLD_V1'.
VERSION = "NATIVE_EXPLICIT_JUNCTION_HOLD_V1"
# Set SUMO_POSITION_EPSILON_METERS to 0.001.
SUMO_POSITION_EPSILON_METERS = 0.001
# Administrative stop duration exceeds all supported demos. Speed constraints
# remain active independently; elapsed time never grants entry permission.
# Set ADMINISTRATIVE_HOLD_SECONDS to 1000000.0.
ADMINISTRATIVE_HOLD_SECONDS = 1_000_000.0


# Define NativeJunctionHold to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NativeJunctionHold:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.stop to None.
        self.stop = None

    # Synchronize using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input paths: the supplied paths.
    # Input vehicle_api: the supplied vehicle api.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def synchronize(self, context, decision, paths, vehicle_api):
        # Set ego to context.ego_id.
        ego = context.ego_id
        # Run this branch when decision.permission equals the text 'PERMITTED'.
        if decision.permission == "PERMITTED":
            # Run this branch when self.stop is a different object from None.
            if self.stop is not None:
                # Set (edge, lane_index, position) to self.stop.
                edge, lane_index, position = self.stop
                # Call vehicle_api.setStop with the supplied arguments.
                vehicle_api.setStop(ego, edge, pos=position,
                                    # Supply laneIndex as lane_index.
                                    # Supply duration as 0.
                                    laneIndex=lane_index, duration=0)
                # Set self.stop to None.
                self.stop = None
                # Return the text 'NATIVE_HOLD_RELEASED_AFTER_PERMISSION' to the caller.
                return "NATIVE_HOLD_RELEASED_AFTER_PERMISSION"
            # Return None to the caller.
            return None
        # Set path to paths.paths at context.movement_path_id.
        path = paths.paths[context.movement_path_id]
        # Run this branch when self.stop is the same object as None and context.ego_state at 'lane_id' equals
        # path.incoming_lane_id and whether any item is true in a lazy sequence of zone equals 'JUNCTION_ENTRY'
        # for (zone, _, _) in decision.blocked_zones.
        if (self.stop is None and context.ego_state['lane_id'] == path.incoming_lane_id
                # Evaluate whether any item is true in a lazy sequence of zone equals the text 'JUNCTION_ENTRY'
                # for (zone, _, _) in decision.blocked_zones as part of the enclosing expression.
                and any(zone == 'JUNCTION_ENTRY' for zone, _, _ in decision.blocked_zones)):
            # Set edge to context.ego_state at 'road_id'.
            edge = context.ego_state['road_id']
            # Set lane_index to the result of vehicle_api.getLaneIndex(ego).
            lane_index = vehicle_api.getLaneIndex(ego)
            # Set position to context.ego_state at 'lane_length' minus SUMO_POSITION_EPSILON_METERS.
            position = context.ego_state['lane_length'] - SUMO_POSITION_EPSILON_METERS
            # Call vehicle_api.setStop with the supplied arguments.
            vehicle_api.setStop(ego, edge, pos=position, laneIndex=lane_index,
                                # Supply duration as ADMINISTRATIVE_HOLD_SECONDS.
                                duration=ADMINISTRATIVE_HOLD_SECONDS)
            # Set self.stop to a tuple containing edge, lane_index, position.
            self.stop = (edge, lane_index, position)
            # Return the text 'NATIVE_HOLD_INSTALLED' to the caller.
            return "NATIVE_HOLD_INSTALLED"
        # Return None to the caller.
        return None
