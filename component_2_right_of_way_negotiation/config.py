"""Configuration for the SUMO intention-prediction shadow deployment."""

# Import Path from pathlib for the operations below.
from pathlib import Path


# Set PROJECT_ROOT to Path(__file__).resolve().parent.
PROJECT_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Simulation timing
# ---------------------------------------------------------------------------
# The ONNX models were trained from genuine 25 Hz position observations.
# Set SIM_TIME_STEP to 0.04.
SIM_TIME_STEP = 0.04
# Set MODEL_SAMPLE_INTERVAL_SECONDS to 0.04.
MODEL_SAMPLE_INTERVAL_SECONDS = 0.04
# Set MODEL_HISTORY_LENGTH to 50.
MODEL_HISTORY_LENGTH = 50
# Set MODEL_OBSERVATION_WINDOW_SECONDS to 2.0.
MODEL_OBSERVATION_WINDOW_SECONDS = 2.0

# Set EPISODE_DURATION_SECONDS to 200.0.
EPISODE_DURATION_SECONDS = 200.0
# Set EPISODE_STEPS to an integer built from the rounded value of EPISODE_DURATION_SECONDS divided by
# SIM_TIME_STEP.
EPISODE_STEPS = int(round(EPISODE_DURATION_SECONDS / SIM_TIME_STEP))

# Set INITIAL_VEHICLE_COUNT to 8.
INITIAL_VEHICLE_COUNT = 8
# Set SPAWN_INTERVAL_SECONDS to 10.0.
SPAWN_INTERVAL_SECONDS = 10.0
# Set SPAWN_BATCH_SIZE to 1.
SPAWN_BATCH_SIZE = 1
# Set CONTROL_UPDATE_INTERVAL_SECONDS to 0.2.
CONTROL_UPDATE_INTERVAL_SECONDS = 0.20
# Set DASHBOARD_UPDATE_INTERVAL_SECONDS to 1.0.
DASHBOARD_UPDATE_INTERVAL_SECONDS = 1.0
# Set CONSOLE_LOG_INTERVAL_SECONDS to 5.0.
CONSOLE_LOG_INTERVAL_SECONDS = 5.0

# Set SUMO_CONFIG to PROJECT_ROOT joined with the path segment 'intersection.sumocfg'.
SUMO_CONFIG = PROJECT_ROOT / "intersection.sumocfg"
# Set SUMO_NETWORK_FILE to PROJECT_ROOT joined with the path segment 'networks' joined with the path segment 'intersection.net.xml'.
SUMO_NETWORK_FILE = PROJECT_ROOT / "networks" / "intersection.net.xml"
# Set GUI_SETTINGS_FILE to PROJECT_ROOT joined with the path segment 'gui' joined with the path segment 'panel_real_world.xml'.
GUI_SETTINGS_FILE = PROJECT_ROOT / "gui" / "panel_real_world.xml"
# Set USE_SUMO_GUI to True.
USE_SUMO_GUI = True

# Keep SUMO's normal safety checks enabled while the independent project
# safety shield is not yet implemented.
# Set SAFE_SUMO_SPEED_MODE to 31.
SAFE_SUMO_SPEED_MODE = 31

# ---------------------------------------------------------------------------
# Fully autonomous traffic
# ---------------------------------------------------------------------------
# Set AV_TYPE_ID to the text 'AV'.
AV_TYPE_ID = "AV"
# Set MAX_APPROACH_SPEED to 13.89.
MAX_APPROACH_SPEED = 13.89

# Set ROUTE_IDS to a tuple containing the text 'route_w_straight', the text 'route_e_straight', the text
# 'route_s_straight', the text...
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
# Provisional conservative experiment parameter. This margin is supplied by
# neither ASAM OSI nor the selected radar specification. It should be replaced
# or justified using processing distance, stopping distance, braking capability,
# uncertainty, and sensitivity testing.
# Set OBSERVATION_SAFETY_MARGIN to 35.0.
OBSERVATION_SAFETY_MARGIN = 35.0
# Set PRIMARY_PREDICTION_LEAD_TIME_SECONDS to 1.0.
PRIMARY_PREDICTION_LEAD_TIME_SECONDS = 1.0
# Set SECONDARY_PREDICTION_LEAD_TIME_SECONDS to 0.5.
SECONDARY_PREDICTION_LEAD_TIME_SECONDS = 0.5
# Set REQUIRED_CONTEXT_SECONDS to MODEL_OBSERVATION_WINDOW_SECONDS plus PRIMARY_PREDICTION_LEAD_TIME_SECONDS.
REQUIRED_CONTEXT_SECONDS = (
    # Evaluate MODEL_OBSERVATION_WINDOW_SECONDS plus PRIMARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing
    # expression.
    MODEL_OBSERVATION_WINDOW_SECONDS
    # Evaluate PRIMARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing expression.
    + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
)
# Approach-zone radius used to determine when intersection-specific reasoning
# should begin.
#
# Design:
#   R_approach = v_max * T_context + safety_margin
#
# where:
#   v_max      = 13.89 m/s (50 km/h urban approach-speed upper bound)
#   T_context  = observation window + prediction lead time
#              = 2.0 s + 1.0 s = 3.0 s
#   margin     = 35.0 m conservative experimental buffer
#
# Therefore:
#   R_approach = 13.89 * 3.0 + 35.0 ≈ 76.67 m
#
# IMPORTANT:
# The 50 km/h speed assumption is externally justified by the German StVO.
# The complete approach-zone formula and the 35 m margin are project-specific
# engineering choices; they are not claimed to be prescribed by StVO,
# Bosch, ASAM OSI, or a single research paper.
# Set REQUIRED_PREDICTION_CONTEXT_SECONDS to REQUIRED_CONTEXT_SECONDS.
REQUIRED_PREDICTION_CONTEXT_SECONDS = REQUIRED_CONTEXT_SECONDS
# Set APPROACH_ZONE_RADIUS to MAX_APPROACH_SPEED multiplied by REQUIRED_CONTEXT_SECONDS plus
# OBSERVATION_SAFETY_MARGIN.
APPROACH_ZONE_RADIUS = (
    # Evaluate MAX_APPROACH_SPEED multiplied by REQUIRED_CONTEXT_SECONDS plus OBSERVATION_SAFETY_MARGIN as part of
    # the enclosing expression.
    MAX_APPROACH_SPEED * REQUIRED_CONTEXT_SECONDS
    # Evaluate OBSERVATION_SAFETY_MARGIN as part of the enclosing expression.
    + OBSERVATION_SAFETY_MARGIN
)
# Experiment-specific conservative closing-speed bound. This is not a
# universal real-world sensor specification.
# Set MAX_CLOSING_SPEED_MPS to 2.0 multiplied by MAX_APPROACH_SPEED.
MAX_CLOSING_SPEED_MPS = 2.0 * MAX_APPROACH_SPEED
# Set MIN_REQUIRED_OBSERVATION_RANGE_METERS to MAX_CLOSING_SPEED_MPS multiplied by REQUIRED_CONTEXT_SECONDS plus
# OBSERVATION_SAFETY_MARGIN.
MIN_REQUIRED_OBSERVATION_RANGE_METERS = (
    # Evaluate MAX_CLOSING_SPEED_MPS multiplied by REQUIRED_CONTEXT_SECONDS plus OBSERVATION_SAFETY_MARGIN as part
    # of the enclosing expression.
    MAX_CLOSING_SPEED_MPS * REQUIRED_CONTEXT_SECONDS
    # Evaluate OBSERVATION_SAFETY_MARGIN as part of the enclosing expression.
    + OBSERVATION_SAFETY_MARGIN
)

# Official source (technical data: up to 160 m and +/-75 degrees horizontal):
# Bosch Mobility, "Corner radar sensor for heavy commercial vehicles",
# https://www.bosch-mobility.com/en/solutions/sensors/corner-radar-sensor-cv/
# Set REFERENCE_SENSOR_NAME to the text 'Bosch corner radar reference profile'.
REFERENCE_SENSOR_NAME = "Bosch corner radar reference profile"
# Set REFERENCE_CORNER_RADAR_RANGE_METERS to 160.0.
REFERENCE_CORNER_RADAR_RANGE_METERS = 160.0
# Set REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES to 150.0.
REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES = 150.0
# Set REFERENCE_CORNER_RADAR_COUNT to 4.
REFERENCE_CORNER_RADAR_COUNT = 4

# Four overlapping virtual corner radars feed one fused object list. Complete
# directional coverage is 360 degrees, not 4 x 150 degrees; overlaps cannot be
# added directly. The reference values are not universal AV sensor values or
# ASAM OSI/ISO requirements. "Up to 160 m" does not promise perfect detection.
# Set FUSED_SURROUND_FOV_DEGREES to 360.0.
FUSED_SURROUND_FOV_DEGREES = 360.0
# Set SENSOR_RANGE to REFERENCE_CORNER_RADAR_RANGE_METERS.
SENSOR_RANGE = REFERENCE_CORNER_RADAR_RANGE_METERS
# Set SENSOR_FOV_DEGREES to FUSED_SURROUND_FOV_DEGREES.
SENSOR_FOV_DEGREES = FUSED_SURROUND_FOV_DEGREES


# Validate selected physical capability against the project requirement.
# Input sensor_range: the supplied sensor range.
# Input required_range: the supplied required range.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def validate_sensor_range(sensor_range=SENSOR_RANGE,
                          # Declare required_range as input parameter.
                          required_range=MIN_REQUIRED_OBSERVATION_RANGE_METERS):
    """Validate selected physical capability against the project requirement."""
    # Run this branch when sensor_range is less than required_range.
    if sensor_range < required_range:
        # Raise ValueError with formatted text built from the embedded values to stop this execution path.
        raise ValueError(
            "The selected reference sensor range is shorter than the minimum "
            "observation distance required by the project. "
            # Evaluate {sensor_range:.2f} as part of the enclosing expression.
            f"Selected reference capability: {sensor_range:.2f} m. "
            # Evaluate {required_range:.2f} as part of the enclosing expression.
            f"Current required observation distance: {required_range:.2f} m."
        )


# Call validate_sensor_range with the supplied arguments.
validate_sensor_range()

# Set SENSOR_CONFIGURATION_SUMMARY to a dictionary containing reference_sensor_name,
# individual_radar_range_meters,...
SENSOR_CONFIGURATION_SUMMARY = {
    # Store REFERENCE_SENSOR_NAME under 'reference_sensor_name'.
    "reference_sensor_name": REFERENCE_SENSOR_NAME,
    # Store REFERENCE_CORNER_RADAR_RANGE_METERS under 'individual_radar_range_meters'.
    "individual_radar_range_meters": REFERENCE_CORNER_RADAR_RANGE_METERS,
    # Store REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES under 'individual_radar_horizontal_fov_degrees'.
    "individual_radar_horizontal_fov_degrees": REFERENCE_CORNER_RADAR_HORIZONTAL_FOV_DEGREES,
    # Store REFERENCE_CORNER_RADAR_COUNT under 'sensor_count'.
    "sensor_count": REFERENCE_CORNER_RADAR_COUNT,
    # Store FUSED_SURROUND_FOV_DEGREES under 'fused_fov_degrees'.
    "fused_fov_degrees": FUSED_SURROUND_FOV_DEGREES,
    # Store MIN_REQUIRED_OBSERVATION_RANGE_METERS under 'minimum_required_observation_range_meters'.
    "minimum_required_observation_range_meters": MIN_REQUIRED_OBSERVATION_RANGE_METERS,
    # Store SENSOR_RANGE under 'selected_operational_sensor_range_meters'.
    "selected_operational_sensor_range_meters": SENSOR_RANGE,
    # Store SENSOR_RANGE is at least MIN_REQUIRED_OBSERVATION_RANGE_METERS under 'range_requirement_satisfied'.
    "range_requirement_satisfied": SENSOR_RANGE >= MIN_REQUIRED_OBSERVATION_RANGE_METERS,
}
# Set IDEAL_BASELINE_PROFILE to the text 'IDEAL_BASELINE'.
IDEAL_BASELINE_PROFILE = "IDEAL_BASELINE"
# Set GEOMETRIC_SENSOR_PROFILE to the text 'GEOMETRIC_SENSOR'.
GEOMETRIC_SENSOR_PROFILE = "GEOMETRIC_SENSOR"
# Set REALISTIC_OBJECT_SENSOR_PROFILE to the text 'REALISTIC_OBJECT_SENSOR'.
REALISTIC_OBJECT_SENSOR_PROFILE = "REALISTIC_OBJECT_SENSOR"
# Set PERCEPTION_PROFILES to an immutable set built from a set containing IDEAL_BASELINE_PROFILE,
# GEOMETRIC_SENSOR_PROFILE, REALISTIC_OBJECT_SENSOR_PROFILE.
PERCEPTION_PROFILES = frozenset({
    # Include IDEAL_BASELINE_PROFILE in this set.
    IDEAL_BASELINE_PROFILE,
    # Include GEOMETRIC_SENSOR_PROFILE in this set.
    GEOMETRIC_SENSOR_PROFILE,
    # Include REALISTIC_OBJECT_SENSOR_PROFILE in this set.
    REALISTIC_OBJECT_SENSOR_PROFILE,
})
# Set DEFAULT_PERCEPTION_PROFILE to GEOMETRIC_SENSOR_PROFILE.
DEFAULT_PERCEPTION_PROFILE = GEOMETRIC_SENSOR_PROFILE
# Set EVENT_ARMING_ETA_SECONDS to MODEL_OBSERVATION_WINDOW_SECONDS plus PRIMARY_PREDICTION_LEAD_TIME_SECONDS.
EVENT_ARMING_ETA_SECONDS = (
    # Evaluate MODEL_OBSERVATION_WINDOW_SECONDS plus PRIMARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing
    # expression.
    MODEL_OBSERVATION_WINDOW_SECONDS
    # Evaluate PRIMARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing expression.
    + PRIMARY_PREDICTION_LEAD_TIME_SECONDS
)
# Operational junction coordinates are intentionally absent here. They are
# derived from the compiled SUMO network by ``map_geometry`` so source-network
# coordinates cannot become stale after net conversion.
# Set INTERSECTION_GEOMETRY_STATUS to the text 'DERIVED_FROM_COMPILED_SUMO_NETWORK'.
INTERSECTION_GEOMETRY_STATUS = "DERIVED_FROM_COMPILED_SUMO_NETWORK"
# Set MANUAL_INTERSECTION_CENTER_CONFIGURED to False.
MANUAL_INTERSECTION_CENTER_CONFIGURED = False
# Set MANUAL_NET_OFFSET_APPLICATION to False.
MANUAL_NET_OFFSET_APPLICATION = False

# Set TRACK_TIMEOUT_SECONDS to 5.0.
TRACK_TIMEOUT_SECONDS = 5.0
# Set CONFIDENCE_DECAY_RATE_PER_SECOND to 0.1.
CONFIDENCE_DECAY_RATE_PER_SECOND = 0.1
# Set CONFIDENCE_OBSERVED_BOOST to 0.3.
CONFIDENCE_OBSERVED_BOOST = 0.3
# Set MIN_CONFIDENCE to 0.1.
MIN_CONFIDENCE = 0.1
# Set MAX_CONFIDENCE to 1.0.
MAX_CONFIDENCE = 1.0

# The history validator rejects low-rate histories and missing observations.
# Set SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS to 0.0001.
SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS = 1e-4
# Set MIN_APPROACH_DISPLACEMENT_METERS to 0.05.
MIN_APPROACH_DISPLACEMENT_METERS = 0.05

# ---------------------------------------------------------------------------
# TensorFlow-free intention inference
# ---------------------------------------------------------------------------
# Set MODEL_DIRECTORY to PROJECT_ROOT joined with the path segment 'models' joined with the path segment 'intention'.
MODEL_DIRECTORY = PROJECT_ROOT / "models" / "intention"
# Set SHADOW_MODE to True.
SHADOW_MODE = True

# The two GRUs are sequential horizon models, not simultaneous ensemble
# members. Each ego-target approach event may trigger each stage only once.
# Deterministic crossing-approach schedule used to validate prediction
# eligibility. Set False to restore the normal cyclic traffic schedule.
# Set VALIDATION_SCENARIO_ENABLED to True.
VALIDATION_SCENARIO_ENABLED = True
# Set VALIDATION_SPAWN_SCHEDULE to a tuple containing a tuple containing 0.0, the text 'route_w_left', a tuple
# containing 0.0, the text 'route_s_straight', a...
VALIDATION_SPAWN_SCHEDULE = (
    # Include a tuple containing 0.0, the text 'route_w_left' in this tuple.
    (0.0, "route_w_left"),
    # Include a tuple containing 0.0, the text 'route_s_straight' in this tuple.
    (0.0, "route_s_straight"),
    # Include a tuple containing 6.0, the text 'route_e_right' in this tuple.
    (6.0, "route_e_right"),
    # Include a tuple containing 6.0, the text 'route_n_left' in this tuple.
    (6.0, "route_n_left"),
    # Include a tuple containing 12.0, the text 'route_w_straight' in this tuple.
    (12.0, "route_w_straight"),
    # Include a tuple containing 12.0, the text 'route_s_right' in this tuple.
    (12.0, "route_s_right"),
    # Include a tuple containing 18.0, the text 'route_e_left' in this tuple.
    (18.0, "route_e_left"),
    # Include a tuple containing 18.0, the text 'route_n_straight' in this tuple.
    (18.0, "route_n_straight"),
    # Include a tuple containing 24.0, the text 'route_w_right' in this tuple.
    (24.0, "route_w_right"),
    # Include a tuple containing 24.0, the text 'route_s_left' in this tuple.
    (24.0, "route_s_left"),
    # Include a tuple containing 30.0, the text 'route_e_straight' in this tuple.
    (30.0, "route_e_straight"),
    # Include a tuple containing 30.0, the text 'route_n_right' in this tuple.
    (30.0, "route_n_right"),
)

# Every incoming edge ends at the common junction entry. The remaining
# distance on the current incoming lane is therefore route-independent and
# does not expose the target vehicle's future SUMO route.
# Set INCOMING_EDGE_IDS to an immutable set built from a set containing the text 'w_in', the text 'e_in', the text
# 's_in', the text 'n_in'.
INCOMING_EDGE_IDS = frozenset(
    # Supply a set containing the text 'w_in', the text 'e_in', the text 's_in', the text 'n_in' to frozenset.
    {"w_in", "e_in", "s_in", "n_in"}
)
# Set MIN_ETA_SPEED_MPS to 0.5.
MIN_ETA_SPEED_MPS = 0.5
# Set CONFLICT_TRIGGER_TOLERANCE_SECONDS to the maximum of 0.08, 2.0 multiplied by SIM_TIME_STEP.
CONFLICT_TRIGGER_TOLERANCE_SECONDS = max(
    # Supply 0.08 to the enclosing expression.
    0.08,
    # Supply 2.0 multiplied by SIM_TIME_STEP to max.
    2.0 * SIM_TIME_STEP,
)

# ---------------------------------------------------------------------------
# Provisional risk and legacy negotiation
# ---------------------------------------------------------------------------
# This stage deliberately retains the existing rule-based controller. These
# values are not the final map-aware conflict model.
# Set URGENCY_WEIGHT to 0.65.
URGENCY_WEIGHT = 0.65
# Set SAFETY_WEIGHT to 0.35.
SAFETY_WEIGHT = 0.35
# Set TIMING_RISK_DECAY_SECONDS to 2.0.
TIMING_RISK_DECAY_SECONDS = 2.0
# Set TIMING_RISK_WEIGHT to 0.7.
TIMING_RISK_WEIGHT = 0.7
# Set CONFIDENCE_RISK_WEIGHT to 0.3.
CONFIDENCE_RISK_WEIGHT = 0.3

# ---------------------------------------------------------------------------
# Evaluation and dashboard
# ---------------------------------------------------------------------------
# Set OUTPUT_DIR to PROJECT_ROOT joined with the path segment 'results'.
OUTPUT_DIR = PROJECT_ROOT / "results"
# Logging-only switch; it does not affect conflict geometry or decisions.
# Set CONFLICT_DEBUG_OUTPUT to False.
CONFLICT_DEBUG_OUTPUT = False
# Physical width declared explicitly for the project's AV type and used only
# to build the startup/static map catalogue. Online graph decisions use each
# LDM track's actual width returned by SUMO.
# Set AV_WIDTH_METERS to 1.8.
AV_WIDTH_METERS = 1.8
# Set DEADLOCK_DURATION_SECONDS to 15.0.
DEADLOCK_DURATION_SECONDS = 15.0
# Set STOPPED_SPEED_THRESHOLD_MPS to 0.5.
STOPPED_SPEED_THRESHOLD_MPS = 0.5

# Set DASHBOARD_ENABLED to True.
DASHBOARD_ENABLED = True
# Set DASHBOARD_API_URL to the text 'http://localhost:8000/simulation/update'.
DASHBOARD_API_URL = "http://localhost:8000/simulation/update"
# Set DASHBOARD_TIMEOUT_SECONDS to 0.1.
DASHBOARD_TIMEOUT_SECONDS = 0.1

# ---------------------------------------------------------------------------
# Visualization/evidence only (never consumed by decision or control logic)
# ---------------------------------------------------------------------------
# Set VISUALIZATION_ENABLED to True.
VISUALIZATION_ENABLED = True
# Set VISUALIZATION_DEMO_EGO_ID to the text 'AV_0'.
VISUALIZATION_DEMO_EGO_ID = "AV_0"
# Set VISUALIZATION_REFRESH_INTERVAL_SECONDS to 0.2.
VISUALIZATION_REFRESH_INTERVAL_SECONDS = 0.20
# Set VISUALIZATION_SENSOR_OVERLAY_ENABLED to True.
VISUALIZATION_SENSOR_OVERLAY_ENABLED = True
# Set VISUALIZATION_SENSOR_CIRCLE_POINTS to 48.
VISUALIZATION_SENSOR_CIRCLE_POINTS = 48
# Set PERCEPTION_EVIDENCE_JSONL to OUTPUT_DIR joined with the path segment 'perception_ldm_evidence.jsonl'.
PERCEPTION_EVIDENCE_JSONL = OUTPUT_DIR / "perception_ldm_evidence.jsonl"
