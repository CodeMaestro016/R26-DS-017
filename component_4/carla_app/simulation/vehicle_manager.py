import math
import threading
import time

import carla

from carla_app.config import simulation_config as _config
from carla_app.config.simulation_config import VEHICLE_BLUEPRINT


# ============================================================
# DRIVER SETTINGS
# ============================================================

TARGET_SPEED_KMH = getattr(_config, "TARGET_SPEED_KMH", 10.0)
START_NEAR_X = getattr(_config, "START_NEAR_X", None)
START_NEAR_Y = getattr(_config, "START_NEAR_Y", None)
VEHICLE_COLORS = getattr(_config, "VEHICLE_COLORS", {})

DRIVER_HZ = 20                 # control updates per second
LOOKAHEAD_MIN_M = 5.0          # how far ahead the driver aims
LOOKAHEAD_PER_MPS = 0.6        # extra look-ahead per m/s of speed
MAX_STEER_ANGLE_DEG = 70.0     # Tesla Model 3 wheel angle at steer = 1
SPEED_GAIN = 0.25              # throttle change per m/s of speed error
MAX_THROTTLE = 0.6


class SimpleDriver:
    """
    Minimal lane-following driver.

    20 times per second:
      1. Find a road point a few metres ahead in the car's lane
         (at junctions, choose the straightest road).
      2. Steer towards it.
      3. Use throttle / brake to hold TARGET_SPEED_KMH.

    Uses only apply_control(): no Traffic Manager, no
    set_autopilot().
    """

    def __init__(self, world, vehicle, target_speed_kmh=TARGET_SPEED_KMH, route=None):
        self.world = world
        self.vehicle = vehicle
        self.map = world.get_map()
        self.target_speed_mps = float(target_speed_kmh) / 3.6

    
        self.route = list(route or [])
        self._route_index = 0

        self._running = False
        self._thread = None
        self.last_error = None

    # --------------------------------------------------------
    # START / STOP
    # --------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="SimpleDriver", daemon=True
        )
        self._thread.start()
        print(
            "[SimpleDriver] Started. Target speed: {:.0f} km/h".format(
                self.target_speed_mps * 3.6
            )
        )

    def stop(self, brake=True):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        if brake:
            try:
                self.vehicle.apply_control(
                    carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0, hand_brake=True)
                )
            except Exception:
                pass
        print("[SimpleDriver] Stopped.")

    # --------------------------------------------------------
    # CONTROL LOOP
    # --------------------------------------------------------

    def _loop(self):
        period = 1.0 / DRIVER_HZ
        while self._running:
            started = time.time()
            try:
                self.vehicle.apply_control(self._compute_control())
                self.last_error = None
            except Exception as error:
                # Print each new error once, keep trying.
                if str(error) != self.last_error:
                    print("[SimpleDriver] Control error: {}".format(error))
                self.last_error = str(error)
            time.sleep(max(0.0, period - (time.time() - started)))

    def _compute_control(self):
        transform = self.vehicle.get_transform()
        location = transform.location
        yaw = transform.rotation.yaw

        velocity = self.vehicle.get_velocity()
        speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2)

        # 1. Target point ahead in the lane
        target = self._target_waypoint(location, yaw, speed)
        if target is None:
            # End of road: stop.
            return carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0)

        # 2. Steering: angle between car heading and target
        target_loc = target.transform.location
        dx = target_loc.x - location.x
        dy = target_loc.y - location.y
        target_heading = math.degrees(math.atan2(dy, dx))
        angle = _wrap_degrees(target_heading - yaw)
        steer = _clamp(angle / MAX_STEER_ANGLE_DEG, -1.0, 1.0)

        # Slow down a little in sharp turns.
        desired = self.target_speed_mps
        if abs(angle) > 20.0:
            desired *= 0.6

        # 3. Throttle / brake to hold the speed
        
        error = desired - speed
        if error >= 0:
            throttle = _clamp(0.2 + SPEED_GAIN * error, 0.0, MAX_THROTTLE)
            brake = 0.0
        elif error > -1.0:
            throttle = 0.0
            brake = 0.0
        else:
            throttle = 0.0
            brake = _clamp(-0.15 * error, 0.0, 0.4)

        return carla.VehicleControl(
            throttle=throttle, steer=steer, brake=brake, hand_brake=False
        )

    def _route_target(self, location, lookahead):
        """
        Next point on the given route, `lookahead` metres ahead of
        the car. None when there is no route or it has ended.
        """
        if not self.route:
            return None

        start = max(0, self._route_index - 5)
        end = min(len(self.route), self._route_index + 30)
        best_index, best_offset = None, None
        for i in range(start, end):
            point = self.route[i].transform.location
            offset = math.hypot(point.x - location.x, point.y - location.y)
            if best_offset is None or offset < best_offset:
                best_index, best_offset = i, offset

        if best_index is None or best_offset > 10.0:
            return None

        self._route_index = max(self._route_index, best_index)

        # Route points are ~2 m apart.
        target_index = self._route_index + max(1, int(round(lookahead / 2.0)))
        if target_index >= len(self.route):
            return None
        return self.route[target_index]

    def _target_waypoint(self, location, yaw, speed):
        lookahead = LOOKAHEAD_MIN_M + LOOKAHEAD_PER_MPS * speed

        # 1) Follow the sign route while it lasts.
        on_route = self._route_target(location, lookahead)
        if on_route is not None:
            return on_route

        # 2) Otherwise: straightest road ahead.
        current = self.map.get_waypoint(
            location, project_to_road=True, lane_type=carla.LaneType.Driving
        )
        if current is None:
            return None

        options = current.next(lookahead)
        if not options:
            return None

        # At junctions, keep going as straight as possible.
        return min(
            options,
            key=lambda wp: abs(_wrap_degrees(wp.transform.rotation.yaw - yaw)),
        )


def _wrap_degrees(angle):
    """Wrap an angle to the range [-180, 180)."""
    return (angle + 180.0) % 360.0 - 180.0


def _clamp(value, low, high):
    return max(low, min(high, value))


class VehicleManager:
    """
    Manages the ego vehicle used in the CARLA simulation.
    """

    def __init__(self, world):
        self.world = world
        self.vehicle = None
        self.driver = None

    def _default_spawn_point(self):
        """
        The map spawn point closest to START_NEAR_X/Y, so every
        run starts in the same place with the correct heading.
        """
        spawn_points = self.world.get_map().get_spawn_points()

        if not spawn_points:
            raise RuntimeError(
                "No vehicle spawn points were found."
            )

        if START_NEAR_X is None or START_NEAR_Y is None:
            return spawn_points[0]

        def distance(point):
            return math.hypot(
                point.location.x - START_NEAR_X,
                point.location.y - START_NEAR_Y,
            )

        best = min(spawn_points, key=distance)

        if distance(best) > 5.0:
            print(
                "[VehicleManager] No spawn point near the configured "
                "start ({:.1f}, {:.1f}). Using spawn point 0.".format(
                    START_NEAR_X, START_NEAR_Y
                )
            )
            return spawn_points[0]

        return best

    def spawn_vehicle(self, spawn_point=None, vehicle_id=None):
        """
        Spawn the configured ego vehicle.

        Args:
            spawn_point (carla.Transform, optional):
                Vehicle spawn position and rotation.
                If None, the fixed start point is used.
            vehicle_id (str, optional):
                "Vehicle_A" / "Vehicle_B" / "Vehicle_C" - sets the
                paint colour from VEHICLE_COLORS.

        Returns:
            carla.Vehicle: Spawned ego vehicle.
        """

        if self.world is None:
            raise RuntimeError(
                "CARLA world is not available."
            )

        blueprint_library = self.world.get_blueprint_library()

        vehicle_blueprint = blueprint_library.find(
            VEHICLE_BLUEPRINT
        )

        color = VEHICLE_COLORS.get(vehicle_id)
        if color is not None:
            if vehicle_blueprint.has_attribute("color"):
                vehicle_blueprint.set_attribute(
                    "color", "{},{},{}".format(*color)
                )
                print("[VehicleManager] {} colour: RGB{}".format(vehicle_id, color))
            else:
                print("[VehicleManager] {} has no colour option.".format(VEHICLE_BLUEPRINT))

        if spawn_point is None:
            spawn_point = self._default_spawn_point()

        self.vehicle = self.world.try_spawn_actor(
            vehicle_blueprint,
            spawn_point
        )

        if self.vehicle is None:
            raise RuntimeError(
                "Failed to spawn the ego vehicle. The spawn point may "
                "be blocked by a leftover actor from a previous run."
            )

        print(
            "[VehicleManager] Spawned at x={:.1f}, y={:.1f}, yaw={:.1f}".format(
                spawn_point.location.x,
                spawn_point.location.y,
                spawn_point.rotation.yaw,
            )
        )

        return self.vehicle

    def get_vehicle(self):
        """
        Return the currently spawned ego vehicle.
        """

        if self.vehicle is None:
            raise RuntimeError(
                "Ego vehicle has not been spawned yet."
            )

        return self.vehicle

    # --------------------------------------------------------
    # SIMPLE DRIVER (replaces autopilot)
    # --------------------------------------------------------

    def start_driving(self, target_speed_kmh=TARGET_SPEED_KMH, route=None):
        """
        Start the simple waypoint driver.

        route: optional list of waypoints to follow (the
        traffic-sign route), so the car passes every sign.
        """
        vehicle = self.get_vehicle()

        if self.driver is None:
            self.driver = SimpleDriver(
                self.world, vehicle,
                target_speed_kmh=target_speed_kmh,
                route=route,
            )
            if route:
                print("[VehicleManager] Driver follows the sign route "
                      "({} points).".format(len(route)))

        self.driver.start()

    def stop_driving(self):
        """
        Stop the driver and brake.
        """
        if self.driver is not None:
            self.driver.stop(brake=True)
            self.driver = None

    def set_headlights(self, on=True):
        """
        Turn the headlights on (night / rain) or off.
        Uses only set_light_state() - no Traffic Manager.
        """
        vehicle = self.get_vehicle()
        try:
            if on:
                state = carla.VehicleLightState(
                    carla.VehicleLightState.Position
                    | carla.VehicleLightState.LowBeam
                )
            else:
                state = carla.VehicleLightState.NONE
            vehicle.set_light_state(state)
            print("[VehicleManager] Headlights {}.".format("on" if on else "off"))
        except Exception as error:
            print("[VehicleManager] Could not set headlights: {}".format(error))

    def set_autopilot(self, enabled=True):
        """
        Enable or disable CARLA autopilot.

        WARNING: this crashed CARLA in this setup. Kept only for
        reference - use start_driving() instead.
        """

        vehicle = self.get_vehicle()

        vehicle.set_autopilot(enabled)

    def set_manual_control(
        self,
        throttle=0.0,
        steer=0.0,
        brake=0.0
    ):
        """
        Apply basic vehicle control.
        """

        vehicle = self.get_vehicle()

        control = carla.VehicleControl()

        control.throttle = max(
            0.0,
            min(1.0, throttle)
        )

        control.steer = max(
            -1.0,
            min(1.0, steer)
        )

        control.brake = max(
            0.0,
            min(1.0, brake)
        )

        vehicle.apply_control(control)

    def stop(self):
        """
        Stop the ego vehicle.
        """

        self.stop_driving()

        if self.vehicle is None:
            return

        control = carla.VehicleControl()

        control.throttle = 0.0
        control.brake = 1.0

        self.vehicle.apply_control(control)

    def get_transform(self):
        """
        Return the current vehicle transform.
        """

        return self.get_vehicle().get_transform()

    def get_location(self):
        """
        Return the current vehicle location.
        """

        return self.get_vehicle().get_location()

    def get_velocity(self):
        """
        Return the current vehicle velocity.
        """

        return self.get_vehicle().get_velocity()

    def destroy(self):
        """
        Stop driving, then destroy the ego vehicle.
        """

        self.stop_driving()

        if self.vehicle is not None:
            self.vehicle.destroy()
            self.vehicle = None