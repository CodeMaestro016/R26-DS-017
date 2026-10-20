
import os
import sys
import time
import threading
import uvicorn
import carla


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# CONFIGURATION
# ============================================================

from carla_app.config.simulation_config import (
    CARLA_HOST,
    CARLA_PORT,
    SERVER_HOST,
    SERVER_PORT,
    USE_SIMPLE_DRIVER,
    VEHICLE_WEATHER,
    WEATHER_PRESETS,
    DETECTION_FPS,
)

import cv2

from carla_app.streaming import ml_client

from carla_app.config.traffic_sign_config import (
    CARLA_SCENARIO_NAME,
    CARLA_SCENARIO_SIGNS,
)


# ============================================================
# CARLA COMPONENTS
# ============================================================

from carla_app.simulation.carla_client import CarlaClient
from carla_app.simulation.environment import CarlaEnvironment
from carla_app.simulation.vehicle_manager import VehicleManager
from carla_app.simulation.traffic_signs import TrafficSignManager
from carla_app.simulation.camera import Camera


# ============================================================
# SHARED VIDEO STREAM
# ============================================================

from carla_app.streaming.video_stream import get_video_stream


# ============================================================
# WEB SERVER STATE
# ============================================================

try:
    from carla_app.streaming.server import (
        set_carla_connected,
        set_controller,
        update_state,
        record_pipeline_result,
        clear_pipeline_results,
    )
    SERVER_AVAILABLE = True
except Exception as _server_import_error:
    print("[WARNING] Web server state not available: {}".format(_server_import_error))
    SERVER_AVAILABLE = False


def _update_web_state(**kwargs):
    """Update the website status, ignoring errors."""
    if not SERVER_AVAILABLE:
        return
    try:
        update_state(**kwargs)
    except Exception:
        pass


# ============================================================
# SIMULATION APPLICATION
# ============================================================

class CarlaSimulation:
    """
    Main controller for the CARLA simulation.
    """

    def __init__(self):
        self.client = None
        self.environment = None
        self.world = None
        self.vehicle_manager = None
        self.traffic_sign_manager = None
        self.camera = None
        self.video_stream = None
        self.vehicle = None
        self.active_vehicle_id = None
        self.initialized = False
        self.connected = False
        self._running = False

        # Only one Start / Stop at a time.
        self._run_lock = threading.Lock()

        # Sign detection (vehicle pipelines in the ML service)
        self.ml_ready = False
        self.pipeline_vehicle_id = None
        self.detection_thread = None
        self.detection_running = False
        self.last_detections = []

    # ========================================================
    # INITIALIZE (connect + map only, nothing spawned)
    # ========================================================

    def initialize(self):
        print()
        print("=" * 60)
        print("AGENTIC FEDERATED LEARNING - CARLA")
        print("=" * 60)

        print()
        print("CARLA CONFIGURATION")
        print("-" * 60)
        print(f"Host : {CARLA_HOST}")
        print(f"Port : {CARLA_PORT}")

        print()
        print("SCENARIO CONFIGURATION")
        print("-" * 60)
        print(f"Scenario : {CARLA_SCENARIO_NAME}")
        print(f"Signs    : {len(CARLA_SCENARIO_SIGNS)} configured")

        # Shared video stream
        self.video_stream = get_video_stream()
        print()
        print("[OK] Shared VideoStream connected.")

        # CARLA client
        self.client = CarlaClient(host=CARLA_HOST, port=CARLA_PORT)
        print()
        print("Connecting to CARLA...")
        self.client.connect()
        self.connected = True
        print("[OK] CARLA client connected.")

        # Environment
        self.environment = CarlaEnvironment(self.client)
        print()
        print("Setting up CARLA environment...")
        self.world = self.environment.setup()
        print("[OK] CARLA environment configured.")
        print(f"[OK] Map: {self.world.get_map().name}")

        # Vehicle manager
        self.vehicle_manager = VehicleManager(self.world)
        print("[OK] Vehicle manager connected.")

        # Traffic sign manager
        self.traffic_sign_manager = TrafficSignManager(self.world)
        print("[OK] Traffic-sign manager connected.")

        # Web server state
        if SERVER_AVAILABLE:
            try:
                set_carla_connected(True)
            except Exception:
                pass

        # ML service (vehicle pipelines) - started automatically.
        print()
        print("Starting ML service (vehicle pipelines)...")
        self.ml_ready = ml_client.start_service()
        if not self.ml_ready:
            print("[WARNING] ML service not available - the simulation runs,")
            print("[WARNING] but signs will not be detected.")

        _update_web_state(
            running=False,
            pipeline_status="idle",
            message=(
                "CARLA connected. Select a vehicle and press Start."
                if self.ml_ready else
                "CARLA connected, but the ML service is not running - no sign detection."
            ),
        )

        self.initialized = True
        print()
        print("=" * 60)
        print("CARLA READY - waiting for Start from the website")
        print("=" * 60)

    # ========================================================
    # SPAWN VEHICLE
    # ========================================================

    def spawn_vehicle(self, spawn_point=None, vehicle_id="Vehicle_A"):
        if not self.initialized:
            raise RuntimeError("Simulation is not initialized.")

        print()
        print("Spawning ego vehicle...")
        self.vehicle = self.vehicle_manager.spawn_vehicle(
            spawn_point=spawn_point,
            vehicle_id=vehicle_id,
        )
        self.spawned_vehicle_id = vehicle_id
        print("[OK] Ego vehicle spawned.")
        return self.vehicle

    # ========================================================
    # START DRIVING
    # ========================================================

    def start_driving(self):
        # Do not call set_autopilot(), even with False, because the native
        # CARLA call previously caused a segmentation fault in this setup.
        # Our own driver follows the road with apply_control() only.
        if not USE_SIMPLE_DRIVER:
            print("[OK] Driving disabled. Vehicle stays parked.")
            return

        # Follow the same route the signs were placed along, so the
        # car passes every sign.
        route = self.traffic_sign_manager.get_route_waypoints()
        self.vehicle_manager.start_driving(route=route)
        print("[OK] Simple driver started (CARLA autopilot not used).")

    # ========================================================
    # CREATE CAMERA
    # ========================================================

    def create_camera(self):
        if self.world is None:
            raise RuntimeError("CARLA world is not available.")
        if self.vehicle is None:
            raise RuntimeError("Vehicle must be spawned first.")

        print()
        print("Creating vehicle camera...")
        self.camera = Camera(
            world=self.world,
            vehicle=self.vehicle,
            sign_manager=self.traffic_sign_manager,
        )
        self.camera.create_camera()
        print("[OK] Camera created.")
        print("[OK] Camera connected to VideoStream.")
        return self.camera

    # ========================================================
    # PLACE TRAFFIC SIGNS
    # ========================================================

    def place_traffic_signs(self):
        """
        Place every sign image beside the road along the car's
        route (follows curves and junctions like the driver).
        """
        if self.vehicle is None:
            raise RuntimeError("Vehicle must be spawned first.")

        print()
        print("Placing traffic signs along the route...")

        created = self.traffic_sign_manager.create_route_signs(
            self.vehicle, getattr(self, "spawned_vehicle_id", None)
        )

        print(f"[OK] Placed {len(created)} traffic signs.")
        return created

    # ========================================================
    # WEATHER (per vehicle)
    # ========================================================

    def apply_weather(self, vehicle_id):
        """
        Set the CARLA weather and the sign look for this vehicle.
        Returns the weather name, e.g. "night".
        """
        name = VEHICLE_WEATHER.get(vehicle_id, "sunny")
        preset = WEATHER_PRESETS.get(name) or WEATHER_PRESETS["sunny"]

        try:
            self.client.set_weather(preset["carla"])
            print(f"[OK] Weather: {name}")
        except Exception as error:
            print(f"[WARNING] Weather '{name}' not applied: {error}")

        if self.traffic_sign_manager is not None:
            self.traffic_sign_manager.set_appearance(
                brightness=preset.get("sign_brightness", 1.0),
                headlight_glow=preset.get("sign_headlight_glow", False),
                blur=preset.get("sign_blur", 0),
            )

        return name

    # ========================================================
    # START RUN  (website Start button)
    # ========================================================

    def start_run(self, vehicle_id="Vehicle_A"):
        """
        Spawn the car, cameras and signs, and start driving.
        If a run is already active, it is stopped first.
        """
        with self._run_lock:

            if not self.initialized:
                _update_web_state(
                    running=False,
                    pipeline_status="error",
                    message="CARLA is not connected.",
                )
                return False

            if self.vehicle is not None:
                print("[INFO] A run is already active. Stopping it first.")
                self._stop_run_locked(show_message=False)

            print()
            print("=" * 60)
            print(f"STARTING RUN: {vehicle_id}")
            print("=" * 60)

            _update_web_state(
                running=False,
                vehicle=vehicle_id,
                pipeline_status="starting",
                message=f"Starting {vehicle_id.replace('_', ' ')}...",
            )

            # Load the vehicle's pipeline BEFORE the car moves, so
            # the first sign is not missed (first load ~10-40 s).
            pipeline_ok = self._load_pipeline(vehicle_id)

            try:
                weather = self.apply_weather(vehicle_id)
                self.spawn_vehicle(vehicle_id=vehicle_id)

                preset = WEATHER_PRESETS.get(weather, {})
                if preset.get("headlights"):
                    self.vehicle_manager.set_headlights(True)

                self.create_camera()

                # Signs are not critical: a failure here must not
                # stop the run.
                try:
                    self.place_traffic_signs()
                except Exception as error:
                    print(f"[WARNING] Traffic signs: {error}")

                # Drive only after the sign route exists.
                self.start_driving()

            except Exception as error:
                print(f"[ERROR] Start failed: {error}")
                self._stop_run_locked(show_message=False)
                _update_web_state(
                    running=False,
                    pipeline_status="error",
                    message=f"Start failed: {error}",
                )
                return False

            self.active_vehicle_id = vehicle_id

            if pipeline_ok:
                self._start_detection_loop()

            _update_web_state(
                running=True,
                vehicle=vehicle_id,
                pipeline_status="running" if pipeline_ok else "no_detection",
                message=(
                    f"{vehicle_id.replace('_', ' ')} is driving ({weather}). "
                    + ("Sign detection active." if pipeline_ok
                       else "Sign detection NOT active (ML service problem).")
                ),
            )

            print()
            print("=" * 60)
            print(f"RUN ACTIVE: {vehicle_id}")
            print("=" * 60)
            return True

    # ========================================================
    # STOP RUN  (website Stop button)
    # ========================================================

    def stop_run(self):
        with self._run_lock:
            self._stop_run_locked(show_message=True)

    def _stop_run_locked(self, show_message=True):
        """
        Stop driving and remove cameras, signs and the car.
        Must be called with _run_lock held.
        """
        was_active = self.vehicle is not None

        if was_active:
            print()
            print("=" * 60)
            print("STOPPING RUN")
            print("=" * 60)

        # 0. Sign detection first (it reads the camera)
        self._stop_detection_loop()
        if self.pipeline_vehicle_id is not None:
            ml_client.unload()
            self.pipeline_vehicle_id = None

        # 1. Cameras first (they are attached to the car)
        if self.camera is not None:
            try:
                self.camera.destroy()
            except Exception as error:
                print(f"[WARNING] Camera cleanup: {error}")
            self.camera = None

        # 2. Traffic signs
        if self.traffic_sign_manager is not None:
            try:
                self.traffic_sign_manager.clear_signs()
            except Exception as error:
                print(f"[WARNING] Sign cleanup: {error}")

        # 3. Driver + car
        if self.vehicle_manager is not None:
            try:
                self.vehicle_manager.destroy()
            except Exception as error:
                print(f"[WARNING] Vehicle cleanup: {error}")
        self.vehicle = None
        self.active_vehicle_id = None

        # Make sure the website shows "Camera off"
        if self.video_stream is not None:
            self.video_stream.clear()

        if was_active:
            print("[OK] Run stopped. Car, cameras and signs removed.")

        if show_message:
            _update_web_state(
                running=False,
                pipeline_status="idle",
                message="Stopped. Select a vehicle and press Start.",
            )

    # ========================================================
    # SIGN DETECTION (front camera -> ML service -> website)
    # Same idea as the old carla_sim _detection_loop().
    # ========================================================

    def _load_pipeline(self, vehicle_id):
        """Load the selected vehicle's pipeline in the ML service."""
        if SERVER_AVAILABLE:
            clear_pipeline_results()

        if not self.ml_ready:
            # Maybe it was started by hand after the backend.
            self.ml_ready = ml_client.health() is not None
        if not self.ml_ready:
            print("[ML] ML service not running - no sign detection for this run.")
            return False

        _update_web_state(
            pipeline_status="loading",
            message=f"Loading {vehicle_id.replace('_', ' ')} pipeline (first time ~10-40 s)...",
        )
        print(f"[ML] Loading {vehicle_id} pipeline...")

        try:
            answer = ml_client.load(vehicle_id)
        except Exception as error:
            print(f"[ML] Could not load {vehicle_id}: {error}")
            return False

        if not answer.get("success"):
            print(f"[ML] {answer.get('message')}")
            return False

        self.pipeline_vehicle_id = vehicle_id
        print(f"[OK] {vehicle_id} pipeline ready ({answer.get('seconds')} s).")
        return True

    def _start_detection_loop(self):
        self.detection_running = True
        self.last_detections = []
        self.detection_thread = threading.Thread(
            target=self._detection_loop, name="SignDetection", daemon=True
        )
        self.detection_thread.start()
        print("[OK] Sign detection loop started ({:.0f} frames/s).".format(DETECTION_FPS))

    def _stop_detection_loop(self):
        self.detection_running = False
        if self.detection_thread is not None and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=70.0)
        self.detection_thread = None
        self.last_detections = []

    def _detection_loop(self):
        interval = 1.0 / float(DETECTION_FPS)
        vehicle_id = self.pipeline_vehicle_id
        last_frame_number = None
        last_error = None

        while self.detection_running:
            started = time.time()

            camera = self.camera
            if camera is None:
                time.sleep(0.1)
                continue

            frame, pose, frame_number = camera.get_front_frame_with_pose()
            if frame is None or frame_number == last_frame_number:
                time.sleep(0.05)
                continue
            last_frame_number = frame_number

            try:
                # Where each roadside sign is in THIS frame (only used
                # to skip signs that were already processed).
                height, width = frame.shape[:2]
                sign_boxes = self.traffic_sign_manager.sign_screen_boxes(
                    pose, width, height, camera.fov
                )

                ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                if not ok:
                    continue

                answer = ml_client.process_frame(jpeg.tobytes(), frame_number, sign_boxes)

                if not self.detection_running:
                    break

                self.last_detections = answer.get("detections", [])

                for item in answer.get("results", []):
                    result = item.get("result") or {}
                    print("[Detection] Sign #{} -> {} | {} {}".format(
                        item.get("sign_number"), vehicle_id,
                        result.get("status", "STOPPED"), result.get("class_name") or ""))
                    if SERVER_AVAILABLE:
                        record_pipeline_result(vehicle_id, item)

                last_error = None

            except Exception as error:
                message = str(error)
                if message != last_error:
                    print(f"[Detection] Error: {message}")
                last_error = message
                time.sleep(1.0)

            time.sleep(max(0.0, interval - (time.time() - started)))

        print("[Detection] Loop stopped.")

    # ========================================================
    # START WEB SERVER (in background thread)
    # ========================================================

    def start_web_server(self):
        def run_server():
            print()
            print("=" * 60)
            print("STARTING WEB SERVER")
            print("=" * 60)
            print(f"Host: {SERVER_HOST}")
            print(f"Port: {SERVER_PORT}")
            print("=" * 60)

            uvicorn.run(
                "carla_app.streaming.server:app",
                host=SERVER_HOST,
                port=SERVER_PORT,
                log_level="info"
            )

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        print(f"[OK] Web server is running on port {SERVER_PORT}")

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def shutdown(self):
        if not self.initialized and self.client is None:
            return

        print()
        print("=" * 60)
        print("SHUTTING DOWN CARLA")
        print("=" * 60)

        self._running = False

        with self._run_lock:
            self._stop_run_locked(show_message=False)

        if self.environment is not None:
            try:
                self.environment.cleanup()
            except Exception as error:
                print(f"[WARNING] Environment cleanup: {error}")
            self.environment = None

        if self.client is not None:
            try:
                self.client.disconnect()
            except Exception as error:
                print(f"[WARNING] CARLA disconnect: {error}")
            self.client = None

        self.world = None
        self.connected = False
        self.initialized = False

        if SERVER_AVAILABLE:
            try:
                set_carla_connected(False)
            except Exception:
                pass

        ml_client.stop_service()

        print()
        print("[INFO] Shutdown complete.")

    # ========================================================
    # RUN FOREVER
    # ========================================================

    def run_forever(self):
        print()
        print("[INFO] Backend is running. Use the website to Start / Stop.")
        print("[INFO] Press CTRL+C to quit.")

        self._running = True
        while self._running:
            time.sleep(1)


# ============================================================
# MAIN
# ============================================================

def main():
    simulation = CarlaSimulation()
    try:
        simulation.initialize()

        if SERVER_AVAILABLE:
            set_controller(simulation)

        simulation.start_web_server()
        simulation.run_forever()
    except KeyboardInterrupt:
        print()
        print("[INFO] Interrupted by user.")
    except Exception as error:
        print()
        print("[ERROR] Initialization failed.")
        print(f"[ERROR] {error}")
    finally:
        simulation.shutdown()


if __name__ == "__main__":
    main()