"""Failure-isolated, display-only SUMO panel styling."""

# Import time for use in this module.
import time


# Define PanelDemoVisualizer to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class PanelDemoVisualizer:
    # Set PANEL_VIEW_HALF_EXTENT_METERS to 135.0.
    PANEL_VIEW_HALF_EXTENT_METERS = 135.0
    # Set PANEL_FOCUSED_ZOOM to 2000.0.
    PANEL_FOCUSED_ZOOM = 2000.0
    # Set BLUE to a tuple containing 30, 100, 255, 255.
    BLUE = (30, 100, 255, 255)
    # Set YELLOW to a tuple containing 255, 210, 0, 255.
    YELLOW = (255, 210, 0, 255)
    # Set GREEN to a tuple containing 30, 200, 80, 255.
    GREEN = (30, 200, 80, 255)
    # Set RED to a tuple containing 230, 45, 45, 255.
    RED = (230, 45, 45, 255)
    # Set GRAY to a tuple containing 145, 145, 145, 255.
    GRAY = (145, 145, 145, 255)

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input traci_module: the supplied traci module.
    # Input enabled: the supplied enabled.
    # Input delay_ms: the supplied delay ms.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, traci_module, enabled=False, delay_ms=0):
        # Set self.traci to traci_module.
        self.traci = traci_module
        # Set self.enabled to a Boolean built from enabled.
        self.enabled = bool(enabled)
        # Set self.delay_seconds to the maximum of 0, an integer built from delay_ms divided by 1000.0.
        self.delay_seconds = max(0, int(delay_ms)) / 1000.0

    # Configure camera using the inputs and processing steps below.
    # Input path_manager: the supplied path manager.
    # Input show_queues: the supplied show queues.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def configure_camera(self, path_manager, *, show_queues=False):
        # Run this branch when the negation of self.enabled.
        if not self.enabled:
            # Return no value to the caller.
            return
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set view to self.traci.gui.getIDList() at 0.
            view = self.traci.gui.getIDList()[0]
            # Set center to the result of self._intersection_center(path_manager).
            center = self._intersection_center(path_manager)
            # Call self.traci.gui.setOffset with the supplied arguments.
            self.traci.gui.setOffset(view, *center)
            # Call self.traci.gui.setZoom with the supplied arguments.
            self.traci.gui.setZoom(view, 800.0 if show_queues else self.PANEL_FOCUSED_ZOOM)
        # Handle Exception using the recovery steps below.
        except Exception:
            # Keep this block syntactically valid without performing an operation.
            pass

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Derive the junction center from the 12 internal path geometries.
    # Input path_manager: the supplied path manager.
    # Output: a tuple containing the minimum of xs plus the maximum of xs divided by 2.0, the minimum of ys plus
    # the maximum of ys divided...
    # Processing: select branches using the stated conditions.
    def _intersection_center(path_manager):
        """Derive the junction center from the 12 internal path geometries."""
        # Set points to a tuple built from a lazy sequence of point for path in values from path_manager.paths.
        points = tuple(point for path in path_manager.paths.values()
                       # Evaluate path.centerline_geometry as part of the enclosing expression.
                       for point in path.centerline_geometry)
        # Run this branch when the negation of points.
        if not points:
            # Raise ValueError with the text 'PANEL_CAMERA_PATH_GEOMETRY_UNAVAILABLE' to stop this execution path.
            raise ValueError("PANEL_CAMERA_PATH_GEOMETRY_UNAVAILABLE")
        # Set (xs, ys) to corresponding items paired from the unpacked values from points.
        xs, ys = zip(*points)
        # Return a tuple containing the minimum of xs plus the maximum of xs divided by 2.0, the minimum of ys
        # plus the maximum of ys divided... to the caller.
        return ((min(xs) + max(xs)) / 2.0,
                # Include the minimum of ys plus the maximum of ys divided by 2.0 in this tuple.
                (min(ys) + max(ys)) / 2.0)

    # Update using the inputs and processing steps below.
    # Input active_ids: the supplied active ids.
    # Input negotiating: the supplied negotiating.
    # Input ready: the supplied ready.
    # Input blocked: the supplied blocked.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def update(self, active_ids, negotiating=(), ready=(), blocked=()):
        # Run this branch when the negation of self.enabled.
        if not self.enabled:
            # Return no value to the caller.
            return
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set active to a set built from the identifiers reported by self.traci.vehicle.getIDList.
            active = set(self.traci.vehicle.getIDList())
            # Set (negotiating, ready, blocked) to the result of map(set, a tuple containing negotiating, ready,
            # blocked).
            negotiating, ready, blocked = map(set,
                                              # Supply a tuple containing negotiating, ready, blocked to map.
                                              (negotiating, ready, blocked))
            # Iterate over a set built from active_ids intersected with active, binding each item to vehicle_id.
            for vehicle_id in set(active_ids) & active:
                # Set color to self.RED when vehicle_id belongs to blocked, otherwise self.GREEN when vehicle_id
                # belongs to ready, otherwise self.YELLOW when vehicle_id belongs to negotiating, otherwise
                # self.BLUE.
                color = (self.RED if vehicle_id in blocked else
                         # Evaluate self.GREEN when vehicle_id belongs to ready, otherwise self.YELLOW when
                         # vehicle_id belongs to negotiating, otherwise self.BLUE as part of the enclosing
                         # expression.
                         self.GREEN if vehicle_id in ready else
                         # Evaluate self.YELLOW when vehicle_id belongs to negotiating, otherwise self.BLUE as
                         # part of the enclosing expression.
                         self.YELLOW if vehicle_id in negotiating else self.BLUE)
                # Call self.traci.vehicle.setColor with the supplied arguments.
                self.traci.vehicle.setColor(vehicle_id, color)
        # Handle Exception using the recovery steps below.
        except Exception:
            # Keep this block syntactically valid without performing an operation.
            pass
        # Run this branch when self.delay_seconds.
        if self.delay_seconds:
            # Pause execution for self.delay_seconds.
            time.sleep(self.delay_seconds)
