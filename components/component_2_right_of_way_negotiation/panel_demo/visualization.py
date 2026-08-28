"""Failure-isolated, display-only SUMO panel styling."""

import time


class PanelDemoVisualizer:
    PANEL_VIEW_HALF_EXTENT_METERS = 135.0
    PANEL_FOCUSED_ZOOM = 2000.0
    BLUE = (30, 100, 255, 255)
    YELLOW = (255, 210, 0, 255)
    GREEN = (30, 200, 80, 255)
    RED = (230, 45, 45, 255)
    GRAY = (145, 145, 145, 255)

    def __init__(self, traci_module, enabled=False, delay_ms=0):
        self.traci = traci_module
        self.enabled = bool(enabled)
        self.delay_seconds = max(0, int(delay_ms)) / 1000.0

    def configure_camera(self, path_manager):
        if not self.enabled:
            return
        try:
            view = self.traci.gui.getIDList()[0]
            center = self._intersection_center(path_manager)
            self.traci.gui.setOffset(view, *center)
            self.traci.gui.setZoom(view, self.PANEL_FOCUSED_ZOOM)
        except Exception:
            pass

    @staticmethod
    def _intersection_center(path_manager):
        """Derive the junction center from the 12 internal path geometries."""
        points = tuple(point for path in path_manager.paths.values()
                       for point in path.centerline_geometry)
        if not points:
            raise ValueError("PANEL_CAMERA_PATH_GEOMETRY_UNAVAILABLE")
        xs, ys = zip(*points)
        return ((min(xs) + max(xs)) / 2.0,
                (min(ys) + max(ys)) / 2.0)

    def update(self, active_ids, negotiating=(), ready=(), blocked=()):
        if not self.enabled:
            return
        try:
            active = set(self.traci.vehicle.getIDList())
            negotiating, ready, blocked = map(set,
                                              (negotiating, ready, blocked))
            for vehicle_id in set(active_ids) & active:
                color = (self.RED if vehicle_id in blocked else
                         self.GREEN if vehicle_id in ready else
                         self.YELLOW if vehicle_id in negotiating else self.BLUE)
                self.traci.vehicle.setColor(vehicle_id, color)
        except Exception:
            pass
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
