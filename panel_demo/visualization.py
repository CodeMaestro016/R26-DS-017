"""Failure-isolated, display-only SUMO panel styling."""

import time


class PanelDemoVisualizer:
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
            boundary = path_manager.network.getBoundary()
            center = ((boundary[0] + boundary[2]) / 2.0,
                      (boundary[1] + boundary[3]) / 2.0)
            self.traci.gui.setOffset(view, *center)
            self.traci.gui.setZoom(view, 900.0)
        except Exception:
            return

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
