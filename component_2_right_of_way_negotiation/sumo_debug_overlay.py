"""Display-only SUMO GUI evidence overlay."""

import math


def sensor_circle_points(center, radius, point_count=48):
    """Return a closed polygonal circle using exactly the supplied radius."""
    x, y = center
    points = [
        (x + radius * math.cos(2.0 * math.pi * index / point_count),
         y + radius * math.sin(2.0 * math.pi * index / point_count))
        for index in range(point_count)
    ]
    return points + [points[0]]


class SumoDebugOverlay:
    """Passive TraCI styling; failures never escape into simulation logic."""

    POLYGON_ID = "debug_sensor_boundary"
    EGO_COLOR = (0, 210, 255, 255)
    DETECTED_COLOR = (30, 220, 90, 255)
    PROPAGATED_COLOR = (255, 155, 30, 255)
    DEFAULT_COLOR = (255, 255, 0, 255)

    def __init__(self, traci_module, enabled, ego_id, sensor_range,
                 sensor_overlay=True, point_count=48):
        self.traci = traci_module
        self.enabled = bool(enabled)
        self.ego_id = ego_id
        self.sensor_range = float(sensor_range)
        self.sensor_overlay = bool(sensor_overlay)
        self.point_count = int(point_count)
        self._styled = set()
        self._polygon_added = False

    def update(self, observations, observation_manager):
        if not self.enabled:
            return
        try:
            active = set(self.traci.vehicle.getIDList())
            for vehicle_id in self._styled & active:
                self.traci.vehicle.setColor(vehicle_id, self.DEFAULT_COLOR)
            self._styled.clear()
            if self.ego_id not in active:
                self._remove_polygon()
                return
            ldm = observation_manager.get_ldm(self.ego_id)
            if ldm is None:
                self._remove_polygon()
                return
            self._style(self.ego_id, self.EGO_COLOR, active)
            for target_id, track in ldm.tracks.items():
                if target_id == self.ego_id:
                    continue
                color = (self.DETECTED_COLOR if track.get("is_observed")
                         else self.PROPAGATED_COLOR)
                self._style(target_id, color, active)
            if self.sensor_overlay:
                state = observations.get(self.ego_id, {})
                center = state.get("position", state.get("pos"))
                if center is not None:
                    self._draw_sensor_boundary(center)
        except Exception:
            # TraCI can invalidate vehicle/polygon objects between calls. This
            # helper is presentation-only and must never stop an experiment.
            return

    def _style(self, vehicle_id, color, active):
        if vehicle_id in active:
            self.traci.vehicle.setColor(vehicle_id, color)
            self._styled.add(vehicle_id)

    def _draw_sensor_boundary(self, center):
        shape = sensor_circle_points(center, self.sensor_range, self.point_count)
        if self._polygon_added:
            self.traci.polygon.setShape(self.POLYGON_ID, shape)
        else:
            self.traci.polygon.add(
                self.POLYGON_ID, shape, (0, 210, 255, 180), fill=False, layer=10
            )
            self._polygon_added = True

    def _remove_polygon(self):
        if self._polygon_added:
            try:
                self.traci.polygon.remove(self.POLYGON_ID)
            except Exception:
                pass
            self._polygon_added = False
