"""Configuration for the SUMO intention-prediction shadow deployment."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Simulation timing
# ---------------------------------------------------------------------------
# The ONNX models were trained from genuine 25 Hz position observations.
SIM_TIME_STEP = 0.04
MODEL_SAMPLE_INTERVAL_SECONDS = 0.04
MODEL_HISTORY_LENGTH = 50
MODEL_OBSERVATION_WINDOW_SECONDS = 2.0

EPISODE_DURATION_SECONDS = 200.0
EPISODE_STEPS = int(round(EPISODE_DURATION_SECONDS / SIM_TIME_STEP))

INITIAL_VEHICLE_COUNT = 8
SPAWN_INTERVAL_SECONDS = 10.0
SPAWN_BATCH_SIZE = 1
CONTROL_UPDATE_INTERVAL_SECONDS = 0.20
DASHBOARD_UPDATE_INTERVAL_SECONDS = 1.0
CONSOLE_LOG_INTERVAL_SECONDS = 5.0

SUMO_CONFIG = PROJECT_ROOT / "intersection.sumocfg"
SUMO_NETWORK_FILE = PROJECT_ROOT / "networks" / "intersection.net.xml"
USE_SUMO_GUI = True

# Keep SUMO's normal safety checks enabled while the independent project
# safety shield is not yet implemented.
SAFE_SUMO_SPEED_MODE = 31

# ---------------------------------------------------------------------------
# Fully autonomous traffic
# ---------------------------------------------------------------------------
AV_TYPE_ID = "AV"
MAX_APPROACH_SPEED = 13.89

ROUTE_IDS = (
    "route_w_straight",
    "route_e_straight",
    "route_s_straight",
    "route_n_straight",
    "route_w_left",
    "route_e_left",
    "route_s_left",
    "route_n_left",
    "route_w_right",
    "route_e_right",
    "route_s_right",
    "route_n_right",
)

# ---------------------------------------------------------------------------
# Decentralized observation and LDM
# ---------------------------------------------------------------------------
OBSERVATION_SAFETY_MARGIN = 35.0
PRIMARY_PREDICTION_LEAD_TIME_SECONDS = 1.0
SECONDARY_PREDICTION_LEAD_TIME_SECONDS = 0.5
REQUIRED_CONTEXT_SECONDS = (
    MODEL_OBSERVATION_WINDOW_SECONDS
    + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
)
# Backwards-compatible name used by older experiment scripts.
REQUIRED_PREDICTION_CONTEXT_SECONDS = REQUIRED_CONTEXT_SECONDS
APPROACH_ZONE_RADIUS = (
    MAX_APPROACH_SPEED * REQUIRED_CONTEXT_SECONDS
    + OBSERVATION_SAFETY_MARGIN
)
# Experiment-specific conservative closing-speed bound. This is not a
# universal real-world sensor specification.
MAX_CLOSING_SPEED_MPS = 2.0 * MAX_APPROACH_SPEED
SENSOR_RANGE = (
    MAX_CLOSING_SPEED_MPS * REQUIRED_CONTEXT_SECONDS
    + OBSERVATION_SAFETY_MARGIN
)
# A fused surround-perception object list; narrower values model directional
# sensor coverage centred on the ego vehicle's forward direction.
SENSOR_FOV_DEGREES = 360.0
IDEAL_BASELINE_PROFILE = "IDEAL_BASELINE"
GEOMETRIC_SENSOR_PROFILE = "GEOMETRIC_SENSOR"
REALISTIC_OBJECT_SENSOR_PROFILE = "REALISTIC_OBJECT_SENSOR"
PERCEPTION_PROFILES = frozenset({
    IDEAL_BASELINE_PROFILE,
    GEOMETRIC_SENSOR_PROFILE,
    REALISTIC_OBJECT_SENSOR_PROFILE,
})
DEFAULT_PERCEPTION_PROFILE = GEOMETRIC_SENSOR_PROFILE
EVENT_ARMING_ETA_SECONDS = (
    MODEL_OBSERVATION_WINDOW_SECONDS
    + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
)
INTERSECTION_CENTER = (300.0, 100.0)

TRACK_TIMEOUT_SECONDS = 5.0
CONFIDENCE_DECAY_RATE_PER_SECOND = 0.1
CONFIDENCE_OBSERVED_BOOST = 0.3
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0

# The history validator rejects low-rate histories and missing observations.
SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS = 1e-4
MIN_APPROACH_DISPLACEMENT_METERS = 0.05

# ---------------------------------------------------------------------------
# TensorFlow-free intention inference
# ---------------------------------------------------------------------------
MODEL_DIRECTORY = PROJECT_ROOT / "models" / "intention"
SHADOW_MODE = True

# The two GRUs are sequential horizon models, not simultaneous ensemble
# members. Each ego-target approach event may trigger each stage only once.
# Deterministic crossing-approach schedule used to validate prediction
# eligibility. Set False to restore the normal cyclic traffic schedule.
VALIDATION_SCENARIO_ENABLED = True
VALIDATION_SPAWN_SCHEDULE = (
    (0.0, "route_w_left"),
    (0.0, "route_s_straight"),
    (6.0, "route_e_right"),
    (6.0, "route_n_left"),
    (12.0, "route_w_straight"),
    (12.0, "route_s_right"),
    (18.0, "route_e_left"),
    (18.0, "route_n_straight"),
    (24.0, "route_w_right"),
    (24.0, "route_s_left"),
    (30.0, "route_e_straight"),
    (30.0, "route_n_right"),
)

# Every incoming edge ends at the common junction entry. The remaining
# distance on the current incoming lane is therefore route-independent and
# does not expose the target vehicle's future SUMO route.
INCOMING_EDGE_IDS = frozenset(
    {"w_in", "e_in", "s_in", "n_in"}
)
MIN_ETA_SPEED_MPS = 0.5
CONFLICT_TRIGGER_TOLERANCE_SECONDS = max(
    0.08,
    2.0 * SIM_TIME_STEP,
)

# ---------------------------------------------------------------------------
# Provisional risk and legacy negotiation
# ---------------------------------------------------------------------------
# This stage deliberately retains the existing rule-based controller. These
# values are not the final map-aware conflict model.
URGENCY_WEIGHT = 0.65
SAFETY_WEIGHT = 0.35
TIMING_RISK_DECAY_SECONDS = 2.0
TIMING_RISK_WEIGHT = 0.7
CONFIDENCE_RISK_WEIGHT = 0.3

# ---------------------------------------------------------------------------
# Evaluation and dashboard
# ---------------------------------------------------------------------------
OUTPUT_DIR = PROJECT_ROOT / "results"
DEADLOCK_DURATION_SECONDS = 15.0
STOPPED_SPEED_THRESHOLD_MPS = 0.5

DASHBOARD_ENABLED = True
DASHBOARD_API_URL = "http://localhost:8000/simulation/update"
DASHBOARD_TIMEOUT_SECONDS = 0.1
