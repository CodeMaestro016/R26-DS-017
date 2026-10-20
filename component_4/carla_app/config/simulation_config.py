
# ============================================================
# CARLA SERVER CONNECTION
# ============================================================

CARLA_HOST = "127.0.0.1"

CARLA_PORT = 2000


# Maximum time allowed when connecting to CARLA.

CARLA_TIMEOUT_SECONDS = 20.0


# ============================================================
# MAP CONFIGURATION
# ============================================================

# CARLA map used for the whole project.

MAP_NAME = "Town01"


# ============================================================
# WEATHER CONFIGURATION
# ============================================================.

WEATHER = {
    "cloudiness": 0.0,
    "precipitation": 0.0,
    "precipitation_deposits": 0.0,
    "wind_intensity": 0.0,

    "sun_azimuth_angle": 0.0,
    "sun_altitude_angle": 70.0,

    "fog_density": 0.0,
    "fog_distance": 0.0,
    "fog_falloff": 0.0,

    "wetness": 0.0,

    "scattering_intensity": 1.0,
    "mie_scattering_scale": 0.0,
    "rayleigh_scattering_scale": 0.0331,
}


# ============================================================
# WEATHER PER VEHICLE
# ============================================================

# Which weather each vehicle drives in. Change freely, e.g.
# all "sunny" for a fair comparison between vehicles.

VEHICLE_WEATHER = {
    "Vehicle_A": "sunny",
    "Vehicle_B": "night",
    "Vehicle_C": "rainy",
}


# Weather presets.
#   "carla"           -> CARLA weather values (missing ones use WEATHER)
#   "headlights"      -> turn on the car's headlights
#   "sign_brightness" -> how bright the roadside signs look (1.0 = normal)
#   "sign_headlight_glow" -> signs light up in the headlights when close
#   "sign_blur"       -> blur on the signs (rain on the lens), pixels

WEATHER_PRESETS = {
    "sunny": {
        "carla": dict(WEATHER),
        "headlights": False,
        "sign_brightness": 1.0,
        "sign_headlight_glow": False,
        "sign_blur": 0,
    },
    "night": {
        "carla": dict(
            WEATHER,
            sun_altitude_angle=-30.0,
            cloudiness=10.0,
        ),
        "headlights": True,
        "sign_brightness": 0.25,
        "sign_headlight_glow": True,
        "sign_blur": 0,
    },
    "rainy": {
        # Tuned for CARLA "-quality-level=Low":
        #   cloudiness above ~60 turns the sky black,
        #   precipitation_deposits (puddles) shows as speckles.
        "carla": dict(
            WEATHER,
            cloudiness=50.0,
            precipitation=80.0,
            precipitation_deposits=0.0,
            wetness=80.0,
            wind_intensity=40.0,
            sun_altitude_angle=45.0,
            fog_density=8.0,
            fog_distance=50.0,
        ),
        "headlights": True,
        "sign_brightness": 0.75,
        "sign_headlight_glow": False,
        "sign_blur": 2,
    },
}


# ============================================================
# SIMULATION MODE
# ============================================================


SYNCHRONOUS_MODE = False   


# Simulation time step.

FIXED_DELTA_SECONDS = 0.05


# ============================================================
# VEHICLE CONFIGURATION
# ============================================================

# Vehicle used as Vehicle A in the CARLA demonstration.

VEHICLE_BLUEPRINT = "vehicle.tesla.model3"


# Paint colour of each vehicle (R, G, B), so it is always
# clear on the video which vehicle is running.

VEHICLE_COLORS = {
    "Vehicle_A": (0, 90, 255),     # blue
    "Vehicle_B": (220, 20, 20),    # red
    "Vehicle_C": (255, 200, 0),    # yellow
}


# Automatically place the vehicle at a suitable spawn point.

AUTO_SPAWN_VEHICLE = True


# Initial vehicle speed in meters per second.
#
# The vehicle movement controller will use this value later.

INITIAL_SPEED_MPS = 8.0


# ============================================================
# SIMPLE DRIVER (replaces CARLA autopilot)
# ============================================================

USE_SIMPLE_DRIVER = True

# Driving speed. 10 km/h gives YOLOv8 many frames of each sign.

TARGET_SPEED_KMH = 10.0


# ============================================================
# FIXED START POINT (Town01)
# ============================================================


START_NEAR_X = 335.49
START_NEAR_Y = 273.74


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

# Resolution of the camera stream.

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720


# Horizontal field of view.

CAMERA_FOV = 90.0


# Camera frame rate.

CAMERA_FPS = 20


# Camera sensor blueprint.

CAMERA_BLUEPRINT = "sensor.camera.rgb"


# ============================================================
# CAMERA POSITION
# ============================================================

# Camera mounted at the front of the ego vehicle.
#
# CARLA uses meters for these values.

CAMERA_LOCATION = {
    "x": 2.0,
    "y": 0.0,
    "z": 1.5,
}


# Camera rotation.

CAMERA_ROTATION = {
    "pitch": 0.0,
    "yaw": 0.0,
    "roll": 0.0,
}


# ============================================================
# SIMULATION CONTROL
# ============================================================


AUTO_START_SIMULATION = False




# ============================================================
# STREAMING CONFIGURATION
# ============================================================

# Python web server used to communicate with the local
# Windows browser.

SERVER_HOST = "0.0.0.0"

SERVER_PORT = 8010


# MJPEG video endpoint.

VIDEO_ENDPOINT = "/video_feed"


# Processing command endpoint.

PROCESS_ENDPOINT = "/process"


# WebSocket endpoint for status/events.

WEBSOCKET_ENDPOINT = "/ws"


# ============================================================
# STREAMING SETTINGS
# ============================================================

# Maximum number of frames kept in the streaming buffer.

FRAME_BUFFER_SIZE = 2


# JPEG quality for browser streaming.

JPEG_QUALITY = 80


# ============================================================
# RESEARCH PIPELINE SETTINGS
# ============================================================

# Vehicle identifier used by the research pipeline.

VEHICLE_ID = "vehicle_A"


# The CARLA simulation provides camera frames.

ENABLE_ML_PIPELINE = True


# ============================================================
# ML SERVICE (vehicle pipelines, "main" env)
# ============================================================

# run_simulation.py starts component_4/ml_service.py by itself
# with this Python (the "main" conda env) and stops it on exit.

ML_SERVICE_AUTOSTART = True

ML_SERVICE_PYTHON = "/venv/main/bin/python"

ML_SERVICE_URL = "http://127.0.0.1:8020"

# Folder of ml_service.py (component_4, next to carla_app).
import os as _os
ML_SERVICE_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "component_4",
)

# Front-camera frames per second sent to the pipeline.
DETECTION_FPS = 2.0

# The website shows a result this long after it is produced, so
# it appears in step with the (slightly delayed) video.
DISPLAY_DELAY_SECONDS = 1.0


# ============================================================
# DEBUGGING
# ============================================================

DEBUG = True


# Print CARLA connection information during startup.

PRINT_CARLA_STATUS = True


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

CONFIG_SUMMARY = {
    "carla_host": CARLA_HOST,
    "carla_port": CARLA_PORT,
    "map": MAP_NAME,
    "vehicle": VEHICLE_BLUEPRINT,
    "camera": {
        "width": CAMERA_WIDTH,
        "height": CAMERA_HEIGHT,
        "fov": CAMERA_FOV,
        "fps": CAMERA_FPS,
    },
    "server": {
        "host": SERVER_HOST,
        "port": SERVER_PORT,
        "video_endpoint": VIDEO_ENDPOINT,
        "process_endpoint": PROCESS_ENDPOINT,
        "websocket_endpoint": WEBSOCKET_ENDPOINT,
    },
    "vehicle_id": VEHICLE_ID,
}