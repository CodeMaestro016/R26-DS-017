"""Display-only SUMO GUI evidence overlay."""

# Import math for use in this module.
import math


# Return a closed polygonal circle using exactly the supplied radius.
# Input center: the supplied center.
# Input radius: the supplied radius.
# Input point_count: the supplied point count.
# Output: points plus a list containing points at 0.
def sensor_circle_points(center, radius, point_count=48):
    """Return a closed polygonal circle using exactly the supplied radius."""
    # Set (x, y) to center.
    x, y = center
    # Set points to a list of a tuple containing x plus radius multiplied by math.cos(2.0 * math.pi * index /
    # point_count), y plus radius multiplied by... for index in the integer range defined by point_count.
    points = [
        # Evaluate a tuple containing x plus radius multiplied by the result of math.cos(2.0 * math.pi * index /
        # point_count), y plus radius... as part of the enclosing expression.
        (x + radius * math.cos(2.0 * math.pi * index / point_count),
         # Include y plus radius multiplied by the result of math.sin(2.0 * math.pi * index divided by
         # point_count) in this tuple.
         y + radius * math.sin(2.0 * math.pi * index / point_count))
        # Evaluate the integer range defined by point_count as part of the enclosing expression.
        for index in range(point_count)
    ]
    # Return points plus a list containing points at 0 to the caller.
    return points + [points[0]]


# Passive TraCI styling; failures never escape into simulation logic.
# Instances expose the attributes and methods implemented in this class.
class SumoDebugOverlay:
    """Passive TraCI styling; failures never escape into simulation logic."""

    # Set POLYGON_ID to the text 'debug_sensor_boundary'.
    POLYGON_ID = "debug_sensor_boundary"
    # Set EGO_COLOR to a tuple containing 0, 210, 255, 255.
    EGO_COLOR = (0, 210, 255, 255)
    # Set DETECTED_COLOR to a tuple containing 30, 220, 90, 255.
    DETECTED_COLOR = (30, 220, 90, 255)
    # Set PROPAGATED_COLOR to a tuple containing 255, 155, 30, 255.
    PROPAGATED_COLOR = (255, 155, 30, 255)
    # Set DEFAULT_COLOR to a tuple containing 255, 255, 0, 255.
    DEFAULT_COLOR = (255, 255, 0, 255)

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input traci_module: the supplied traci module.
    # Input enabled: the supplied enabled.
    # Input ego_id: the identifier of the ego vehicle.
    # Input sensor_range: the supplied sensor range.
    # Input sensor_overlay: the supplied sensor overlay.
    # Input point_count: the supplied point count.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, traci_module, enabled, ego_id, sensor_range,
                 # Declare sensor_overlay, point_count as input parameters.
                 sensor_overlay=True, point_count=48):
        # Set self.traci to traci_module.
        self.traci = traci_module
        # Set self.enabled to a Boolean built from enabled.
        self.enabled = bool(enabled)
        # Set self.ego_id to ego_id.
        self.ego_id = ego_id
        # Set self.sensor_range to a floating-point number built from sensor_range.
        self.sensor_range = float(sensor_range)
        # Set self.sensor_overlay to a Boolean built from sensor_overlay.
        self.sensor_overlay = bool(sensor_overlay)
        # Set self.point_count to an integer built from point_count.
        self.point_count = int(point_count)
        # Set self._styled to an empty set.
        self._styled = set()
        # Set self._polygon_added to False.
        self._polygon_added = False

    # Update using the inputs and processing steps below.
    # Input observations: the supplied observations.
    # Input observation_manager: the supplied observation manager.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def update(self, observations, observation_manager):
        # Run this branch when the negation of self.enabled.
        if not self.enabled:
            # Return no value to the caller.
            return
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set active to a set built from the identifiers reported by self.traci.vehicle.getIDList.
            active = set(self.traci.vehicle.getIDList())
            # Iterate over self._styled intersected with active, binding each item to vehicle_id.
            for vehicle_id in self._styled & active:
                # Call self.traci.vehicle.setColor with the supplied arguments.
                self.traci.vehicle.setColor(vehicle_id, self.DEFAULT_COLOR)
            # Clear the stored entries in self._styled.
            self._styled.clear()
            # Run this branch when self.ego_id does not belong to active.
            if self.ego_id not in active:
                # Call self._remove_polygon with the supplied arguments.
                self._remove_polygon()
                # Return no value to the caller.
                return
            # Set ldm to the result of observation_manager.get_ldm(self.ego_id).
            ldm = observation_manager.get_ldm(self.ego_id)
            # Run this branch when ldm is the same object as None.
            if ldm is None:
                # Call self._remove_polygon with the supplied arguments.
                self._remove_polygon()
                # Return no value to the caller.
                return
            # Call self._style with the supplied arguments.
            self._style(self.ego_id, self.EGO_COLOR, active)
            # Iterate over key/value pairs from ldm.tracks, binding each item to (target_id, track).
            for target_id, track in ldm.tracks.items():
                # Run this branch when target_id equals self.ego_id.
                if target_id == self.ego_id:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set color to self.DETECTED_COLOR when 'is_observed' from track; use None if absent, otherwise
                # self.PROPAGATED_COLOR.
                color = (self.DETECTED_COLOR if track.get("is_observed")
                         # Evaluate self.PROPAGATED_COLOR as part of the enclosing expression.
                         else self.PROPAGATED_COLOR)
                # Call self._style with the supplied arguments.
                self._style(target_id, color, active)
            # Run this branch when self.sensor_overlay.
            if self.sensor_overlay:
                # Set state to self.ego_id from observations; use an empty dictionary if absent.
                state = observations.get(self.ego_id, {})
                # Set center to 'position' from state; use 'pos' from state; use None if absent if absent.
                center = state.get("position", state.get("pos"))
                # Run this branch when center is a different object from None.
                if center is not None:
                    # Call self._draw_sensor_boundary with the supplied arguments.
                    self._draw_sensor_boundary(center)
        # Handle Exception using the recovery steps below.
        except Exception:
            # TraCI can invalidate vehicle/polygon objects between calls. This
            # helper is presentation-only and must never stop an experiment.
            # Return no value to the caller.
            return

    # Style using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input color: the supplied color.
    # Input active: the supplied active.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _style(self, vehicle_id, color, active):
        # Run this branch when vehicle_id belongs to active.
        if vehicle_id in active:
            # Call self.traci.vehicle.setColor with the supplied arguments.
            self.traci.vehicle.setColor(vehicle_id, color)
            # Add vehicle_id to self._styled.
            self._styled.add(vehicle_id)

    # Draw sensor boundary using the inputs and processing steps below.
    # Input center: the supplied center.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _draw_sensor_boundary(self, center):
        # Set shape to the result of sensor_circle_points(center, self.sensor_range, self.point_count).
        shape = sensor_circle_points(center, self.sensor_range, self.point_count)
        # Run this branch when self._polygon_added.
        if self._polygon_added:
            # Call self.traci.polygon.setShape with the supplied arguments.
            self.traci.polygon.setShape(self.POLYGON_ID, shape)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Add self.POLYGON_ID to self.traci.polygon.
            self.traci.polygon.add(
                # Supply fill as False.
                # Supply layer as 10.
                self.POLYGON_ID, shape, (0, 210, 255, 180), fill=False, layer=10
            )
            # Set self._polygon_added to True.
            self._polygon_added = True

    # Remove polygon using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _remove_polygon(self):
        # Run this branch when self._polygon_added.
        if self._polygon_added:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Remove self.POLYGON_ID from self.traci.polygon.
                self.traci.polygon.remove(self.POLYGON_ID)
            # Handle Exception using the recovery steps below.
            except Exception:
                # Keep this block syntactically valid without performing an operation.
                pass
            # Set self._polygon_added to False.
            self._polygon_added = False
