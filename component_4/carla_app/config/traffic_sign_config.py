
# ============================================================
# COMPLETE GTSRB 43-CLASS REFERENCE
# ============================================================

TRAFFIC_SIGNS = {

    0: {
        "class_name": "speed_limit_20",
        "category": "prohibitory",
    },

    1: {
        "class_name": "speed_limit_30",
        "category": "prohibitory",
    },

    2: {
        "class_name": "speed_limit_50",
        "category": "prohibitory",
    },

    3: {
        "class_name": "speed_limit_60",
        "category": "prohibitory",
    },

    4: {
        "class_name": "speed_limit_70",
        "category": "prohibitory",
    },

    5: {
        "class_name": "speed_limit_80",
        "category": "prohibitory",
    },

    6: {
        "class_name": "restriction_ends_80",
        "category": "other",
    },

    7: {
        "class_name": "speed_limit_100",
        "category": "prohibitory",
    },

    8: {
        "class_name": "speed_limit_120",
        "category": "prohibitory",
    },

    9: {
        "class_name": "no_overtaking",
        "category": "prohibitory",
    },

    10: {
        "class_name": "no_overtaking_trucks",
        "category": "prohibitory",
    },

    11: {
        "class_name": "priority_at_next_intersection",
        "category": "danger",
    },

    12: {
        "class_name": "priority_road",
        "category": "other",
    },

    13: {
        "class_name": "give_way",
        "category": "other",
    },

    14: {
        "class_name": "stop",
        "category": "other",
    },

    15: {
        "class_name": "no_traffic_both_ways",
        "category": "prohibitory",
    },

    16: {
        "class_name": "no_trucks",
        "category": "prohibitory",
    },

    17: {
        "class_name": "no_entry",
        "category": "other",
    },

    18: {
        "class_name": "danger",
        "category": "danger",
    },

    19: {
        "class_name": "bend_left",
        "category": "danger",
    },

    20: {
        "class_name": "bend_right",
        "category": "danger",
    },

    21: {
        "class_name": "bend",
        "category": "danger",
    },

    22: {
        "class_name": "uneven_road",
        "category": "danger",
    },

    23: {
        "class_name": "slippery_road",
        "category": "danger",
    },

    24: {
        "class_name": "road_narrows",
        "category": "danger",
    },

    25: {
        "class_name": "construction",
        "category": "danger",
    },

    26: {
        "class_name": "traffic_signal",
        "category": "danger",
    },

    27: {
        "class_name": "pedestrian_crossing",
        "category": "danger",
    },

    28: {
        "class_name": "school_crossing",
        "category": "danger",
    },

    29: {
        "class_name": "cycles_crossing",
        "category": "danger",
    },

    30: {
        "class_name": "snow",
        "category": "danger",
    },

    31: {
        "class_name": "animals",
        "category": "danger",
    },

    32: {
        "class_name": "restriction_ends",
        "category": "other",
    },

    33: {
        "class_name": "go_right",
        "category": "mandatory",
    },

    34: {
        "class_name": "go_left",
        "category": "mandatory",
    },

    35: {
        "class_name": "go_straight",
        "category": "mandatory",
    },

    36: {
        "class_name": "go_right_or_straight",
        "category": "mandatory",
    },

    37: {
        "class_name": "go_left_or_straight",
        "category": "mandatory",
    },

    38: {
        "class_name": "keep_right",
        "category": "mandatory",
    },

    39: {
        "class_name": "keep_left",
        "category": "mandatory",
    },

    40: {
        "class_name": "roundabout",
        "category": "mandatory",
    },

    41: {
        "class_name": "restriction_ends_overtaking",
        "category": "other",
    },

    42: {
        "class_name": "restriction_ends_overtaking_trucks",
        "category": "other",
    },
}


# ============================================================
# TOTAL GTSRB CLASSES
# ============================================================

TOTAL_GTSRB_CLASSES = 43


# ============================================================
# SIGN IMAGES
# ============================================================
#
# Every image in this folder is placed along the road:
#
#   carla_app/assets/signs/
#
# Any file name works (spaces are fine). PNG / JPG.
# A plain white background is removed automatically when the
# image is loaded, and each sign is cropped to its edges.

import os as _os

SIGN_IMAGE_DIR = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "assets",
    "signs",
)

SIGN_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")

.

SIGN_ORDER = []


# ============================================================
# LAYOUT MODE
# ============================================================


SIGN_LAYOUT_MODE = "fixed"


# ============================================================
# DEMO LAYOUTS - one fixed order per vehicle
# (used when SIGN_LAYOUT_MODE = "fixed")
# ============================================================


DEMO_LAYOUTS = {

    # Vehicle A - prohibitory specialist
    # (no f3, f6, Pedestrian Crossing or 120 Speed Limit on this route)
    "Vehicle_A": [
        ("30 Speed limit.png",      "right"),
        ("f1.png",                  "left"),
        ("Keep Right .png",         "right"),
        ("Speed Limit 70 Sign.png", "left"),
        ("f2.png",                  "right"),
        ("STOP .png",               "left"),
        ("Roundabout .png",         "right"),
        ("f4.png",                  "left"),
        ("Yield Sign.png",          "right"),
        ("No Parking Sign.png",     "left"),
        ("f5.png",                  "right"),
        ("Right-Turn .png",         "left"),
        ("Priority Road .png",      "right"),
        ("Straight-Ahead .png",     "left"),
        ("f7.png",                  "right"),
    ],

    # Vehicle B - mandatory specialist
    "Vehicle_B": [
        ("Keep Right .png",          "left"),
        ("f3.png",                   "right"),
        ("Roundabout .png",          "left"),
        ("30 Speed limit.png",       "right"),
        ("f5.png",                   "left"),
        ("Straight-Ahead .png",      "right"),
        ("Pedestrian Crossing .png", "left"),
        ("f1.png",                   "right"),
        ("Right-Turn .png",          "left"),
        ("STOP .png",                "right"),
        ("f7.png",                   "left"),
        ("Speed Limit 70 Sign.png",  "right"),
        ("Yield Sign.png",           "left"),
        ("f2.png",                   "right"),
        ("No Parking Sign.png",      "left"),
        ("Priority Road .png",       "right"),
        ("f4.png",                   "left"),
        ("120 Speed Limit.png",      "right"),
        ("f6.png",                   "left"),
    ],

    # Vehicle C - danger specialist
    "Vehicle_C": [
        ("Pedestrian Crossing .png", "right"),
        ("f6.png",                   "left"),
        ("Yield Sign.png",           "right"),
        ("Keep Right .png",          "left"),
        ("f4.png",                   "right"),
        ("Speed Limit 70 Sign.png",  "left"),
        ("STOP .png",                "right"),
        ("f2.png",                   "left"),
        ("Priority Road .png",       "right"),
        ("Roundabout .png",          "left"),
        ("f7.png",                   "right"),
        ("30 Speed limit.png",       "left"),
        ("Straight-Ahead .png",      "right"),
        ("f1.png",                   "left"),
        ("Right-Turn .png",          "right"),
        ("120 Speed Limit.png",      "left"),
        ("f3.png",                   "right"),
        ("No Parking Sign.png",      "left"),
        ("f5.png",                   "right"),
    ],
}

# Used if a vehicle is not listed above.
DEMO_LAYOUT = DEMO_LAYOUTS["Vehicle_A"]


def demo_layout(vehicle_id=None):
    """The fixed sign layout of a vehicle (Vehicle A's by default)."""
    return DEMO_LAYOUTS.get(vehicle_id, DEMO_LAYOUT)


# ============================================================
# RANDOM LAYOUT (used when SIGN_LAYOUT_MODE = "random")
# ============================================================

# Shuffle the sign order on every Start.
SIGN_RANDOM_ORDER = True

# Which side of the road: "right", "left" or "random".
SIGN_SIDE = "random"

# Random variation of the gap between signs (+/- metres).
SIGN_SPACING_JITTER_METERS = 8.0

# None  -> a new random layout on every Start (demo).
# A number (e.g. 42) -> the same "random" layout every time,
#                       so runs can be compared fairly.
SIGN_RANDOM_SEED = None


def demo_side(name, vehicle_id=None):
    """Side of a sign in the vehicle's layout ("right" if not listed)."""
    for file_name, side in demo_layout(vehicle_id):
        if file_name == name:
            return side
    return "right"


def list_sign_files(vehicle_id=None):
    """Sign image file names in the order they appear on the road."""
    if not _os.path.isdir(SIGN_IMAGE_DIR):
        return []

    files = sorted(
        name for name in _os.listdir(SIGN_IMAGE_DIR)
        if name.lower().endswith(SIGN_IMAGE_EXTENSIONS)
    )

    if SIGN_LAYOUT_MODE == "fixed":
        layout = demo_layout(vehicle_id)
        missing = [name for name, _ in layout if name not in files]
        if missing:
            print("[Signs] Layout files not found (skipped): {}".format(missing))
        return [name for name, _ in layout if name in files]

    if SIGN_ORDER:
        return [name for name in SIGN_ORDER if name in files]

    # Mix fake signs (f1.png, f2.png, ...) between real ones.
    fakes = [n for n in files if n.lower().startswith("f") and n[1:2].isdigit()]
    reals = [n for n in files if n not in fakes]
    mixed = []
    while reals or fakes:
        if reals:
            mixed.append(reals.pop(0))
        if fakes:
            mixed.append(fakes.pop(0))
    return mixed


# ============================================================
# SIGN PLACEMENT ALONG THE ROAD
# ============================================================

# Distance from the car's start point to the first sign.
SIGN_FIRST_DISTANCE_METERS = 25.0

# Distance between consecutive signs along the road.
SIGN_SPACING_METERS = 35.0

# Sideways distance from the edge of the car's lane to the
# sign pole (positive = right-hand roadside).
SIGN_SIDE_OFFSET_METERS = 1.2

# Height of the BOTTOM of the sign above the road.
SIGN_HEIGHT_METERS = 1.8

# Width of the sign panel (height follows the image shape).
# Real signs are ~0.6-0.9 m; 0.9 m keeps them clear for YOLO.
SIGN_SIZE_METERS = 0.9

# Pole thickness.
SIGN_POLE_WIDTH_METERS = 0.07


# ============================================================
# NAMES USED BY run_simulation.py
# ============================================================

CARLA_SCENARIO_NAME = "roadside_sign_route"

CARLA_SCENARIO_SIGNS = list_sign_files()