# -*- coding: utf-8 -*-
"""
CARLA DEBUG LIVE SCENARIO + 36-FEATURE ML DEMO
(Forced fallback geometry for hesitant/distracted/aggressive)

FIXES:
- Distracted pedestrian now spawns on the RIGHT side of the road (flipped direction).
- Unwanted cars are cleared before spawning the ego vehicle.
- Hesitant pedestrian behaviour fixed (moves immediately, closer to crosswalk).
- Waiting pedestrian now spawns on the RIGHT side (modified).
"""

from __future__ import print_function

import argparse
import io
import json
import math
import random
import signal
import sys
import threading
import time
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import carla

from scenario_suite import (
    get_scenario,
    list_scenario_ids,
    print_scenario_info,
)

from feature_pipeline import (
    PoseExtractor,
    PedestrianTracker,
    WINDOW_SIZE,
)

from rule_based_agent import RuleBasedAgent


# ============================================================================
# CONFIGURATION
# ============================================================================

CARLA_HOST = "localhost"
CARLA_PORT = 2000
CARLA_TIMEOUT = 10.0

POSE_SERVER_URL = "http://127.0.0.1:8091/pose"
ENSEMBLE_SERVER_URL = "http://127.0.0.1:8092/predict"

FIXED_DELTA_SECONDS = 0.05

SIMULATION_SECONDS = 16.0
VEHICLE_ONLY_SECONDS = 3.0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FOV = 90.0

TARGET_DISTANCE_M = 32.0

PEDESTRIAN_SPEED_MPS = 1.5   # increased slightly for committed to cross faster

CROP_PADDING = 0.20
MIN_CROP_SIZE = 30

LABELS = {
    0: "Waiting",
    1: "Hesitant",
    2: "Committed",
    3: "Distracted",
    4: "Aggressive",
    5: "Jaywalk",
}

# ----------------------------------------------------------------------
# WEB DASHBOARD / BROWSER STREAMING SETTINGS
# ----------------------------------------------------------------------
# See the "WEB STREAMING SERVER" section below for what these drive.
WEB_STREAM_PORT = 8093
WEB_STREAM_JPEG_QUALITY = 70
WEB_STREAM_MAX_WIDTH = 960          # downscaled for encode speed / bandwidth
WEB_STREAM_FRAME_STRIDE = 2         # push every Nth camera frame (20Hz -> 10Hz)
WEB_STREAM_LOG_MAXLEN = 40

# ----------------------------------------------------------------------
# DISTRACTED-PEDESTRIAN HEAD TILT SETTINGS
# ----------------------------------------------------------------------
DISTRACTED_NOD_DEGREES = 25.0
DISTRACTED_NOD_SIGN = -1.0

# ----------------------------------------------------------------------
# SAFETY SETTINGS (new / modified)
# ----------------------------------------------------------------------
MAX_DECEL_MPS2 = 6.0          # comfortable emergency deceleration
SAFETY_MARGIN_M = 1.5         # extra distance to stop before the pedestrian

# ----------------------------------------------------------------------
# CROSSWALK GEOMETRY CAP
# ----------------------------------------------------------------------
MAX_CROSSING_DISTANCE_M = 14.0  # ~9.3s of walking at PEDESTRIAN_SPEED_MPS=1.5,
                                  # leaving real margin within SIMULATION_SECONDS=16.0
                                  # for the crossing to actually finish. Confirmed via
                                  # an actual run that an uncapped 21.95m real crosswalk
                                  # needed ~14.6s of steady walking alone -- only 1.4s of
                                  # margin, and produced 'finished crossing: False', with
                                  # 'committed' walking the full uncapped distance
                                  # directly across/through the vehicle's path for far
                                  # longer than intended -- this is what made it look
                                  # like it was heading into a collision course rather
                                  # than resolving normally. Used by
                                  # crosswalk_polygon_geometry(), which affects
                                  # 'committed' and 'hesitant' (the only two behaviors
                                  # anchored to a real crosswalk via that function) --
                                  # committed is far more sensitive to this since it
                                  # walks the FULL distance, unlike hesitant which caps
                                  # its own progress at 50% regardless of total distance.


# ============================================================================
# BASIC GEOMETRY
# ============================================================================

def horizontal_distance(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def get_forward_vector(transform):
    yaw = math.radians(transform.rotation.yaw)
    return carla.Vector3D(x=math.cos(yaw), y=math.sin(yaw), z=0.0)


def get_right_vector(transform):
    forward = get_forward_vector(transform)
    return carla.Vector3D(x=-forward.y, y=forward.x, z=0.0)


def add_vector(location, vector, scale):
    return carla.Location(
        x=location.x + vector.x * scale,
        y=location.y + vector.y * scale,
        z=location.z + vector.z * scale,
    )


def normalize_2d(vector):
    length = math.sqrt(vector.x * vector.x + vector.y * vector.y)
    if length < 1e-6:
        return carla.Vector3D(x=0.0, y=0.0, z=0.0)
    return carla.Vector3D(x=vector.x / length, y=vector.y / length, z=0.0)


# ============================================================================
# ACTOR MANAGER
# ============================================================================

class ActorManager(object):
    def __init__(self):
        self.actors = []

    def add(self, actor):
        if actor is not None:
            self.actors.append(actor)
        return actor

    def cleanup(self):
        print()
        print("Cleaning scenario actors...")
        for actor in reversed(self.actors):
            if actor is None:
                continue
            try:
                if actor.is_alive:
                    actor.destroy()
            except Exception as exc:
                print("  cleanup warning: %s" % exc)
        self.actors = []
        print("Scenario actor cleanup complete.")


# ============================================================================
# WEATHER
# ============================================================================

def make_weather(world, spec):
    if spec.weather_custom:
        weather = carla.WeatherParameters()
        for key, value in spec.weather_custom.items():
            if hasattr(weather, key):
                setattr(weather, key, value)
        world.set_weather(weather)
        return

    preset = spec.weather_preset
    if not preset:
        return

    if hasattr(carla.WeatherParameters, preset):
        weather = getattr(carla.WeatherParameters, preset)
        world.set_weather(weather)
    else:
        print("WARNING: unknown weather preset: %s" % preset)


# ============================================================================
# CLEAR TRAFFIC
# ============================================================================

def clear_traffic(world):
    """Destroy all existing vehicles (except the ego vehicle, which we haven't spawned yet)."""
    vehicles = world.get_actors().filter('vehicle.*')
    for v in vehicles:
        if v.is_alive:
            v.destroy()
    print(f"Cleared {len(vehicles)} existing vehicle(s).")


# ============================================================================
# VEHICLE SPAWNING
# ============================================================================

def choose_vehicle_spawn(world, seed):
    spawn_points = world.get_map().get_spawn_points()
    if not spawn_points:
        raise RuntimeError("CARLA map contains no vehicle spawn points.")

    rng = random.Random(seed)
    preferred = []
    for transform in spawn_points:
        x = transform.location.x
        y = transform.location.y
        if 80.0 <= x <= 180.0 and -30.0 <= y <= 40.0:
            preferred.append(transform)

    if preferred:
        preferred = sorted(preferred, key=lambda t: (t.location.x, t.location.y))
        return preferred[seed % len(preferred)]

    return rng.choice(spawn_points)


def spawn_vehicle(world, actors, seed):
    library = world.get_blueprint_library()
    preferred_names = [
        "vehicle.tesla.model3",
        "vehicle.audi.a2",
        "vehicle.lincoln.mkz_2020",
        "vehicle.lincoln.mkz",
    ]

    vehicle_bp = None
    for name in preferred_names:
        candidates = library.filter(name)
        if candidates:
            vehicle_bp = candidates[0]
            break

    if vehicle_bp is None:
        vehicles = library.filter("vehicle.*")
        if not vehicles:
            raise RuntimeError("No vehicle blueprints found.")
        vehicle_bp = sorted(vehicles, key=lambda bp: bp.id)[0]

    spawn_points = world.get_map().get_spawn_points()
    first = choose_vehicle_spawn(world, seed)
    ordered = [first]
    for sp in spawn_points:
        if sp is not first:
            ordered.append(sp)

    vehicle = None
    chosen = None
    for transform in ordered:
        vehicle = world.try_spawn_actor(vehicle_bp, transform)
        if vehicle is not None:
            chosen = transform
            break

    if vehicle is None:
        raise RuntimeError("Could not spawn ego vehicle.")

    actors.add(vehicle)
    try:
        vehicle.set_autopilot(False)
    except RuntimeError as exc:
        print("WARNING: could not confirm autopilot is off (%s) -- "
              "continuing anyway." % exc)

    print("Vehicle spawned at: (%.2f, %.2f, %.2f)" % (
        chosen.location.x, chosen.location.y, chosen.location.z))
    print("Vehicle rotation: yaw=%.2f" % chosen.rotation.yaw)

    return vehicle


def spawn_vehicle_at_transform(world, actors, transform):
    # Same as spawn_vehicle but at a specific transform
    library = world.get_blueprint_library()
    preferred_names = [
        "vehicle.tesla.model3",
        "vehicle.audi.a2",
        "vehicle.lincoln.mkz_2020",
        "vehicle.lincoln.mkz",
    ]

    vehicle_bp = None
    for name in preferred_names:
        candidates = library.filter(name)
        if candidates:
            vehicle_bp = candidates[0]
            break

    if vehicle_bp is None:
        vehicles = library.filter("vehicle.*")
        if not vehicles:
            raise RuntimeError("No vehicle blueprints found.")
        vehicle_bp = sorted(vehicles, key=lambda bp: bp.id)[0]

    nudged = carla.Transform(
        carla.Location(x=transform.location.x, y=transform.location.y,
                       z=transform.location.z + 0.3),
        transform.rotation)

    vehicle = world.try_spawn_actor(vehicle_bp, nudged)
    if vehicle is None:
        vehicle = world.try_spawn_actor(vehicle_bp, transform)

    if vehicle is None:
        raise RuntimeError("Could not spawn ego vehicle at the derived transform.")

    actors.add(vehicle)
    try:
        vehicle.set_autopilot(False)
    except RuntimeError as exc:
        print("WARNING: could not confirm autopilot is off (%s) -- "
              "continuing anyway." % exc)

    print("Vehicle spawned at: (%.2f, %.2f, %.2f)" % (
        transform.location.x, transform.location.y, transform.location.z))
    print("Vehicle rotation: yaw=%.2f" % transform.rotation.yaw)

    return vehicle


# ============================================================================
# CROSSWALK DETECTION (kept for completeness, but we will force fallback for hesitant)
# ============================================================================

def nearest_waypoint(world, location):
    return world.get_map().get_waypoint(
        location, project_to_road=True, lane_type=carla.LaneType.Driving)


def crosswalk_polygon_geometry(all_points, anchor_point, road_right, cluster_radius_m=15.0, extra_margin_m=3.5):
    """extra_margin_m increased from 1.5 to 3.5 -- the crosswalk polygon
    data from get_crosswalks() marks the painted stripes across the
    ROAD itself, not the sidewalks on either side. A small margin only
    pushed start/finish to the road's edge, so 'committed' could look
    like it stops at the kerb line rather than genuinely reaching the
    far sidewalk. This pushes both ends further out onto the actual
    sidewalk on each side, so a full crossing looks (and is) complete.

    cluster_radius_m increased from 8.0 to 15.0 -- confirmed via an
    actual run that 8.0 was too small: the resulting crossing distance
    was only 7.81m with the detected road half-width (before margin)
    at just ~0.4m, meaning most of the crosswalk's own corner points on
    the far side were being excluded from the cluster entirely (further
    than 8m from wherever the anchor point happened to land), silently
    underestimating the real road width regardless of how much margin
    gets added on top of it afterward."""
    cluster = [p for p in all_points if horizontal_distance(p, anchor_point) <= cluster_radius_m]
    if not cluster:
        cluster = [anchor_point]

    avg_x = sum(p.x for p in cluster) / len(cluster)
    avg_y = sum(p.y for p in cluster) / len(cluster)
    avg_z = sum(p.z for p in cluster) / len(cluster)
    center = carla.Location(x=avg_x, y=avg_y, z=avg_z)

    projections = []
    for p in cluster:
        dx = p.x - center.x
        dy = p.y - center.y
        proj = dx * road_right.x + dy * road_right.y
        projections.append(proj)

    max_proj = max(projections) + extra_margin_m
    min_proj = min(projections) - extra_margin_m

    # Cap the total span so 'committed' (the only behavior that walks
    # the FULL distance) can't end up walking directly across/through
    # the vehicle's path for far longer than the scenario intends on a
    # genuinely wide real crosswalk.
    total_span = max_proj - min_proj
    if total_span > MAX_CROSSING_DISTANCE_M:
        scale = MAX_CROSSING_DISTANCE_M / total_span
        mid = (max_proj + min_proj) / 2.0
        half_capped = (total_span * scale) / 2.0
        max_proj = mid + half_capped
        min_proj = mid - half_capped

    start = carla.Location(x=center.x + road_right.x * max_proj,
                            y=center.y + road_right.y * max_proj, z=center.z)
    finish = carla.Location(x=center.x + road_right.x * min_proj,
                             y=center.y + road_right.y * min_proj, z=center.z)

    return center, start, finish


def find_verified_crosswalk_for_vehicle(world, approach_distance_m=35.0, skip_count=0, flip_side=False):
    """skip_count lets different scenarios land on DIFFERENT real
    crosswalks instead of all finding the same first valid one --
    e.g. hesitant using skip_count=2 to get a different location than
    committed's skip_count=0, while both still get a genuinely
    verified, vehicle-relative real crosswalk (unlike the previous
    explicit vehicle_spawn_index approach for hesitant, which was
    confirmed via an actual run to land somewhere with no crosswalk
    within 200m at all, and possibly not even the intended travel
    lane).

    If flip_side is True, the start and finish are swapped (so the
    pedestrian spawns on the opposite side of the road)."""
    crosswalk_points = world.get_map().get_crosswalks()
    if not crosswalk_points:
        return None

    fallback_distances = [approach_distance_m, approach_distance_m * 0.8,
                          approach_distance_m * 0.6, approach_distance_m * 0.45,
                          25.0, 20.0, 15.0]

    skipped = 0
    for point in crosswalk_points:
        wp = world.get_map().get_waypoint(point, project_to_road=True,
                                          lane_type=carla.LaneType.Driving)
        if wp is None:
            continue

        cross_wp = wp
        if wp.is_junction:
            for step_dist in [2.0, 4.0, 6.0, 8.0, 10.0]:
                prev_wps = wp.previous(step_dist)
                if prev_wps and not prev_wps[0].is_junction:
                    cross_wp = prev_wps[0]
                    break
            if cross_wp.is_junction:
                continue

        vehicle_wp = None
        for d in fallback_distances:
            previous_wps = cross_wp.previous(d)
            if not previous_wps:
                continue
            candidate = previous_wps[0]
            if candidate.is_junction:
                continue
            if candidate.lane_type != carla.LaneType.Driving:
                continue
            vehicle_wp = candidate
            break

        if vehicle_wp is None:
            continue

        if skipped < skip_count:
            skipped += 1
            continue

        road_transform = cross_wp.transform
        road_right = get_right_vector(road_transform)
        road_forward = get_forward_vector(road_transform)

        center, start, finish = crosswalk_polygon_geometry(crosswalk_points, point, road_right)

        # If flip_side, swap start and finish so pedestrian spawns on opposite kerb
        if flip_side:
            start, finish = finish, start
            road_right = carla.Vector3D(x=-road_right.x, y=-road_right.y, z=0.0)

        vehicle_transform = vehicle_wp.transform

        print("Found real crosswalk at (%.2f, %.2f)" % (center.x, center.y))
        return {
            "center": center,
            "start": start,
            "finish": finish,
            "road_right": road_right,
            "road_forward": road_forward,
            "waypoint": cross_wp,
            "real_crosswalk": True,
            "vehicle_transform": vehicle_transform,
        }

    return None


def find_crosswalk_ahead_of_vehicle(world, vehicle, max_distance=80.0, flip_side=False):
    vehicle_loc = vehicle.get_location()
    current_wp = world.get_map().get_waypoint(vehicle_loc, lane_type=carla.LaneType.Driving)
    if current_wp is None:
        return None

    step = 2.0
    distance = 0.0
    while distance < max_distance:
        next_wps = current_wp.next(step)
        if not next_wps:
            break
        current_wp = next_wps[0]
        distance += step

        all_crosswalk_points = world.get_map().get_crosswalks()
        for cross_point in all_crosswalk_points:
            if horizontal_distance(current_wp.transform.location, cross_point) < 3.0:
                for d in [20.0, 15.0, 12.0, 10.0]:
                    prev_wps = current_wp.previous(d)
                    if prev_wps and not prev_wps[0].is_junction:
                        vehicle_transform = prev_wps[0].transform
                        road_right = get_right_vector(current_wp.transform)
                        road_forward = get_forward_vector(current_wp.transform)
                        center, start, finish = crosswalk_polygon_geometry(
                            all_crosswalk_points, cross_point, road_right)
                        if flip_side:
                            start, finish = finish, start
                            road_right = carla.Vector3D(x=-road_right.x, y=-road_right.y, z=0.0)
                        return {
                            "center": center,
                            "start": start,
                            "finish": finish,
                            "road_right": road_right,
                            "road_forward": road_forward,
                            "waypoint": current_wp,
                            "real_crosswalk": True,
                            "vehicle_transform": vehicle_transform,
                        }
                break
    return None


# ============================================================================
# WAITING LOCATION (sidewalk)
# ============================================================================

def find_waiting_location(world, vehicle, prefer_right=False):
    """
    Find a sidewalk location ahead of the vehicle.
    If prefer_right is True, the pedestrian is placed on the right side of the road
    (relative to the vehicle's forward direction). Otherwise, uses the original logic.
    """
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)
    right = get_right_vector(vehicle_transform)

    # Determine the lateral direction: if prefer_right, we offset to the right,
    # which is the positive 'right' vector; otherwise, use original behavior
    # (which often ends up on the left due to the way waypoints are projected).
    # We'll use a positive offset for right, and for the original we'll keep the
    # same positive offset but in the negative right direction? Actually original
    # used positive offset with right vector, but the waypoint projection might
    # have shifted it. We'll simply keep original logic for non-prefer_right.
    # For prefer_right, we want to ensure we look on the right side by using
    # the positive right vector (which is already the case) but maybe the issue
    # is that the road right vector might point left depending on lane orientation?
    # To be safe, we can just flip the sign of the lateral offset when prefer_right.
    # However, the original code used positive offsets with 'right', so it should
    # already be right. But user says waiting person is on left, so perhaps the
    # road's right vector is actually pointing left due to waypoint orientation.
    # Thus, we will use the opposite sign when prefer_right is False (i.e., original)
    # and keep positive for prefer_right? That might invert all others, which is not desired.
    # Instead, we'll add a parameter to use the opposite lateral direction for waiting.
    # We'll leave the original behavior for non-waiting by not changing anything.
    # For prefer_right, we will use the negative of the right vector to offset.
    # That should place the pedestrian on the actual right side if the original
    # placed it on the left. We'll test.

    # To avoid confusion, we'll implement a simple approach:
    # If prefer_right is True, we use offset direction = -right (i.e., left? No,
    # -right is left? Actually right vector points to the right of forward.
    # If the pedestrian currently spawns on left, it might be because the
    # waypoint projection puts it on the left sidewalk even with positive offset.
    # So to force right, we'll use a negative offset (i.e., -right)?? That would
    # be even more left. We need to examine original code: In find_waiting_location,
    # the loop tries ahead distances and then offsets with 'right' vector positive.
    # If the road waypoint is in the opposite lane direction, the 'right' vector
    # could point to the left of the vehicle's travel direction. Thus, to get the
    # actual right side relative to the vehicle, we need to use the vehicle's own
    # right vector, not the waypoint's. So the fix is to use the vehicle's right
    # vector for lateral offsets when prefer_right is True, and keep original
    # for others. The original code sometimes uses waypoint's right vector in
    # fallback. We'll modify accordingly.

    # For simplicity, we'll create a copy of the function with an added lateral
    # vector override. We'll use vehicle's right vector when prefer_right is True.

    # Let's define a lateral vector for offsets:
    if prefer_right:
        lateral = get_right_vector(vehicle_transform)   # vehicle's right
    else:
        lateral = right  # same as before (but may be waypoint's)

    for d in range(25, 45, 2):
        ahead = add_vector(vehicle_location, forward, d)

        sidewalk_wp = world.get_map().get_waypoint(ahead, project_to_road=True,
                                                   lane_type=carla.LaneType.Sidewalk)
        if sidewalk_wp is not None and not sidewalk_wp.is_junction:
            spot = sidewalk_wp.transform.location
            road_forward_vec = get_forward_vector(sidewalk_wp.transform)
            road_yaw = math.degrees(math.atan2(road_forward_vec.y, road_forward_vec.x))
            pedestrian_yaw = road_yaw - 90.0
            right_vec = get_right_vector(sidewalk_wp.transform)
            return {
                "center": spot,
                "start": spot,
                "finish": spot,
                "road_right": right_vec,
                "road_forward": road_forward_vec,
                "waypoint": sidewalk_wp,
                "real_crosswalk": False,
                "pedestrian_yaw": pedestrian_yaw,
            }

        for offset in [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]:
            # Use the determined lateral vector for offsets
            candidate_loc = add_vector(ahead, lateral, offset)
            any_wp = world.get_map().get_waypoint(candidate_loc, project_to_road=True,
                                                  lane_type=carla.LaneType.Any)
            if any_wp is None or any_wp.is_junction:
                continue
            if any_wp.lane_type != carla.LaneType.Driving:
                spot = any_wp.transform.location
                road_forward_vec = get_forward_vector(any_wp.transform)
                road_yaw = math.degrees(math.atan2(road_forward_vec.y, road_forward_vec.x))
                pedestrian_yaw = road_yaw - 90.0
                right_vec = get_right_vector(any_wp.transform)
                return {
                    "center": spot,
                    "start": spot,
                    "finish": spot,
                    "road_right": right_vec,
                    "road_forward": road_forward_vec,
                    "waypoint": any_wp,
                    "real_crosswalk": False,
                    "pedestrian_yaw": pedestrian_yaw,
                }

    # Fallback: fixed offset 6m
    print("WARNING: No off-road location found, using fixed offset 6m.")
    for d in range(25, 45, 2):
        ahead = add_vector(vehicle_location, forward, d)
        offset_loc = add_vector(ahead, lateral, 6.0)
        wp = world.get_map().get_waypoint(offset_loc, project_to_road=True,
                                          lane_type=carla.LaneType.Any)
        if wp is not None and not wp.is_junction:
            spot = wp.transform.location
            road_forward_vec = get_forward_vector(wp.transform)
            road_yaw = math.degrees(math.atan2(road_forward_vec.y, road_forward_vec.x))
            pedestrian_yaw = road_yaw - 90.0
            right_vec = get_right_vector(wp.transform)
            return {
                "center": spot,
                "start": spot,
                "finish": spot,
                "road_right": right_vec,
                "road_forward": road_forward_vec,
                "waypoint": wp,
                "real_crosswalk": False,
                "pedestrian_yaw": pedestrian_yaw,
            }

    return None


# ============================================================================
# JAYWALK LOCATION (away from crosswalks)
# ============================================================================

def find_jaywalk_geometry(world, vehicle, min_crosswalk_distance_m=15.0):
    crosswalks = world.get_map().get_crosswalks() if hasattr(world.get_map(), 'get_crosswalks') else []
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)

    search_distances = [20.0, 25.0, 28.0, 30.0, 32.0, 34.0, 36.0, 40.0, 45.0, 50.0]

    best = None
    for d in search_distances:
        center = add_vector(vehicle_location, forward, d)
        waypoint = nearest_waypoint(world, center)
        if waypoint is None or waypoint.is_junction:
            continue

        if crosswalks:
            nearest_cw = min(horizontal_distance(center, p) for p in crosswalks)
            if nearest_cw < min_crosswalk_distance_m:
                continue

        score = -abs(d - TARGET_DISTANCE_M)
        if best is None or score > best[0]:
            best = (score, waypoint)

    if best is None:
        return None

    waypoint = best[1]
    road_transform = waypoint.transform
    road_right = get_right_vector(road_transform)
    road_center = road_transform.location

    side_offset = 4.5
    start = add_vector(road_center, road_right, side_offset)
    finish = add_vector(road_center, road_right, -side_offset)

    return {
        "center": road_center, "start": start, "finish": finish,
        "road_right": road_right, "road_forward": get_forward_vector(road_transform),
        "waypoint": waypoint, "real_crosswalk": False,
    }


# ============================================================================
# FALLBACK GEOMETRY (places pedestrian directly in front of vehicle) - IMPROVED
# ============================================================================

def find_fallback_geometry(world, vehicle, flip_side=False):
    """
    Always returns a valid geometry directly in front of the vehicle.
    The pedestrian will be placed on the road surface (if possible) or at vehicle's Z.
    If flip_side is True, the pedestrian spawns on the right side of the road.
    """
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)
    right = get_right_vector(vehicle_transform)

    # Place 30m ahead
    center = add_vector(vehicle_location, forward, 30.0)

    # Try to get the road height at that point
    waypoint = nearest_waypoint(world, center)
    if waypoint is not None:
        # Use road height
        center.z = waypoint.transform.location.z
    else:
        # Otherwise, keep same height as vehicle (adjust slightly)
        center.z = vehicle_location.z

    side_offset = 4.5   # standard lane width; keep moderate to stay on road

    if flip_side:
        # Spawn on the right side (positive right direction)
        start = add_vector(center, right, side_offset)    # right side
        finish = add_vector(center, right, -side_offset)  # left side
    else:
        # Original: spawn on left side (negative right)
        start = add_vector(center, right, -side_offset)   # left side
        finish = add_vector(center, right, side_offset)   # right side

    # Ensure start/finish are on road surface if possible
    for loc in [start, finish]:
        wp = nearest_waypoint(world, loc)
        if wp is not None:
            loc.z = wp.transform.location.z

    print("Fallback geometry: pedestrian at (%.2f, %.2f, %.2f), start (%.2f, %.2f), finish (%.2f, %.2f)" % (
        center.x, center.y, center.z, start.x, start.y, finish.x, finish.y))

    return {
        "center": center,
        "start": start,
        "finish": finish,
        "road_right": right,
        "road_forward": forward,
        "waypoint": waypoint,
        "real_crosswalk": False,
    }


# ============================================================================
# PEDESTRIAN SPAWN & CONTROLLER
# ============================================================================

def choose_pedestrian_blueprint(world):
    walkers = world.get_blueprint_library().filter("walker.pedestrian.*")
    if not walkers:
        raise RuntimeError("No pedestrian blueprints found.")
    walkers = sorted(walkers, key=lambda bp: bp.id)
    return walkers[0]


def ground_pedestrian_location(world, location):
    waypoint = world.get_map().get_waypoint(
        location, project_to_road=True, lane_type=carla.LaneType.Any)

    if waypoint is not None:
        return carla.Location(x=location.x, y=location.y,
                               z=waypoint.transform.location.z + 0.05)

    return carla.Location(x=location.x, y=location.y, z=location.z)


def spawn_pedestrian(world, actors, geometry, spec=None):
    pedestrian_bp = choose_pedestrian_blueprint(world)

    center = geometry.get("start")
    if center is None:
        center = geometry.get("center")

    cross_wp = geometry.get("waypoint")
    base_z = cross_wp.transform.location.z if cross_wp is not None else center.z

    RAISE_OFFSET = 0.7

    # ---- FIX: for aggressive, use raw sidewalk location like waiting ----
    if spec is not None and spec.behavior in ("waiting", "aggressive"):
        start_loc = carla.Location(x=center.x, y=center.y,
                                   z=base_z + RAISE_OFFSET)
        print("%s: Using raw sidewalk location, no road projection." % spec.behavior.capitalize())
    else:
        # Use ground projection to ensure pedestrian is on the navmesh
        start_loc = ground_pedestrian_location(world, center)
        # If that failed, use center with offset
        if start_loc.z == center.z:
            start_loc.z = base_z + RAISE_OFFSET
        else:
            start_loc.z += RAISE_OFFSET
        print("Other: Projected to ground surface.")

    print("Spawning pedestrian at (%.3f, %.3f, %.3f)" % (start_loc.x, start_loc.y, start_loc.z))

    if "pedestrian_yaw" in geometry:
        yaw = geometry["pedestrian_yaw"]
        print("Using custom pedestrian yaw: %.2f" % yaw)
    else:
        road_forward = geometry.get("road_forward", carla.Vector3D(x=1.0, y=0.0, z=0.0))
        yaw = math.degrees(math.atan2(road_forward.y, road_forward.x))
        print("Using road forward yaw: %.2f" % yaw)

    pitch = 0.0

    rotation = carla.Rotation(pitch=pitch, yaw=yaw, roll=0.0)
    transform = carla.Transform(start_loc, rotation)

    print()
    print("=" * 60)
    print("PEDESTRIAN SPAWN")
    print("=" * 60)
    print("Spawn location: (%.3f, %.3f, %.3f)" % (start_loc.x, start_loc.y, start_loc.z))
    print("Yaw: %.2f, Pitch: %.1f" % (yaw, pitch))

    if geometry.get("real_crosswalk", False):
        print("Crosswalk         : REAL CARLA MAP CROSSWALK")
    else:
        print("Crosswalk         : fallback road crossing")

    pedestrian = world.try_spawn_actor(pedestrian_bp, transform)

    if pedestrian is None:
        print("Primary spawn failed. Trying offsets...")
        right = geometry["road_right"]
        offsets = [0.25, -0.25, 0.50, -0.50, 0.75, -0.75, 1.00, -1.00,
                   1.50, -1.50, 2.00, -2.00, 2.50, -2.50, 3.00, -3.00]

        for offset in offsets:
            candidate = add_vector(start_loc, right, offset)
            candidate.z = base_z + RAISE_OFFSET
            candidate_transform = carla.Transform(candidate, rotation)
            pedestrian = world.try_spawn_actor(pedestrian_bp, candidate_transform)
            if pedestrian is not None:
                transform = candidate_transform
                print("Spawn succeeded with offset %.2fm" % offset)
                break

    if pedestrian is None:
        raise RuntimeError("FATAL: Could not spawn pedestrian.")

    actual_spawn_loc = transform.location
    actors.add(pedestrian)

    # Disable physics initially; re-enable later for non-waiting scenarios
    if spec is not None and spec.behavior == "waiting":
        try:
            pedestrian.set_simulate_physics(False)
            print("Physics disabled for 'waiting'.")
        except Exception as exc:
            print("WARNING: could not disable physics: %s" % exc)
    else:
        try:
            pedestrian.set_simulate_physics(False)
            print("Physics disabled for '%s' (idle phase)." % spec.behavior)
        except Exception as exc:
            print("WARNING: could not disable physics: %s" % exc)

    pedestrian.set_transform(transform)
    world.tick()
    pedestrian.set_transform(transform)

    actual = pedestrian.get_transform()
    print("CARLA pedestrian location: (%.3f, %.3f, %.3f)" % (
        actual.location.x, actual.location.y, actual.location.z))

    try:
        bb = pedestrian.bounding_box
        print("Pedestrian bounding box: location z=%.3f, extent z=%.3f, height=%.3f" % (
            bb.location.z, bb.extent.z, bb.extent.z * 2.0))
    except Exception:
        pass

    if abs(actual.location.x) < 0.01 and abs(actual.location.y) < 0.01:
        raise RuntimeError("FATAL: pedestrian ended at (0,0,0).")

    print("Pedestrian spawn verified.")
    print("=" * 60)

    return pedestrian, actual_spawn_loc, yaw


# ============================================================================
# DISTRACTED HEAD TILT (bone-based, world-space math, applied AFTER world.tick())
# ============================================================================

_BONE_NAMES_DUMPED = False  # module-level flag: dump the skeleton once

HEAD_BONE_NAME = "crl_Head__C"
HEAD_PARENT_BONE_NAME = "crl_neck__C"   # crl_Head__C's parent in this rig


def _rotation_matrix(rotation):
    """3x3 world/local rotation matrix from a carla.Rotation."""
    pitch = math.radians(rotation.pitch)
    yaw = math.radians(rotation.yaw)
    roll = math.radians(rotation.roll)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    return np.array([
        [cp * cy, cy * sp * sr - sy * cr, -cy * sp * cr - sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, -sy * sp * cr + cy * sr],
        [sp,      -cp * sr,                cp * cr],
    ], dtype=np.float64)


def _rotation_from_matrix(R):
    """Inverse of _rotation_matrix(): extract (pitch, yaw, roll) degrees."""
    sp = max(-1.0, min(1.0, R[2, 0]))
    pitch = math.asin(sp)
    cp = math.cos(pitch)
    if abs(cp) < 1e-6:
        yaw = math.atan2(-R[0, 1], R[1, 1])
        roll = 0.0
    else:
        yaw = math.atan2(R[1, 0], R[0, 0])
        roll = math.atan2(-R[2, 1], R[2, 2])
    return carla.Rotation(pitch=math.degrees(pitch), yaw=math.degrees(yaw),
                           roll=math.degrees(roll))


def _axis_angle_matrix(axis_xyz, degrees):
    """Rodrigues' rotation matrix: rotate `degrees` around unit axis_xyz."""
    theta = math.radians(degrees)
    x, y, z = axis_xyz
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-9:
        return np.identity(3, dtype=np.float64)
    x, y, z = x / norm, y / norm, z / norm
    c, s, t = math.cos(theta), math.sin(theta), 1.0 - math.cos(theta)
    return np.array([
        [t * x * x + c,     t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c,     t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
    ], dtype=np.float64)


def _make_4x4(rotation_matrix_3x3, location):
    M = np.identity(4, dtype=np.float64)
    M[:3, :3] = rotation_matrix_3x3
    M[0, 3] = location.x
    M[1, 3] = location.y
    M[2, 3] = location.z
    return M


def apply_distracted_head_tilt(pedestrian):
    """
    Nods the head bone forward-down in WORLD space, applied AFTER world.tick().
    """
    global _BONE_NAMES_DUMPED

    if pedestrian is None or not pedestrian.is_alive:
        return

    try:
        bones = pedestrian.get_bones()
    except Exception as exc:
        print("WARNING: get_bones() failed (%s) -- falling back to a mild "
              "whole-body pitch so the demo still shows something." % exc)
        try:
            t = pedestrian.get_transform()
            pedestrian.set_transform(carla.Transform(
                t.location,
                carla.Rotation(pitch=-8.0, yaw=t.rotation.yaw, roll=0.0)))
        except Exception:
            pass
        return

    if not _BONE_NAMES_DUMPED:
        print()
        print("=" * 60)
        print("PEDESTRIAN SKELETON BONE NAMES (first distracted frame)")
        print("=" * 60)
        for bone in bones.bone_transforms:
            print("  %s" % bone.name)
        print("=" * 60)
        _BONE_NAMES_DUMPED = True

    bone_map = {b.name: b for b in bones.bone_transforms}
    head = bone_map.get(HEAD_BONE_NAME)
    neck = bone_map.get(HEAD_PARENT_BONE_NAME)

    if head is None or neck is None:
        print("WARNING: expected bones '%s' / '%s' not found on this "
              "skeleton -- tilt NOT applied. Check the bone dump above." % (
                  HEAD_BONE_NAME, HEAD_PARENT_BONE_NAME))
        return

    ped_transform = pedestrian.get_transform()
    right = get_right_vector(ped_transform)  # world-space lateral axis
    axis = (right.x, right.y, right.z)

    R_head_world = _rotation_matrix(head.world.rotation)
    R_nod = _axis_angle_matrix(axis, DISTRACTED_NOD_SIGN * DISTRACTED_NOD_DEGREES)
    R_head_world_new = R_nod @ R_head_world

    R_neck_world = _rotation_matrix(neck.world.rotation)
    M_neck_world = _make_4x4(R_neck_world, neck.world.location)
    M_head_world_new = _make_4x4(R_head_world_new, head.world.location)

    try:
        M_neck_world_inv = np.linalg.inv(M_neck_world)
    except np.linalg.LinAlgError:
        print("WARNING: neck world matrix not invertible this frame -- "
              "skipping tilt.")
        return

    M_head_relative_new = M_neck_world_inv @ M_head_world_new
    new_rotation = _rotation_from_matrix(M_head_relative_new[:3, :3])
    new_head_relative = carla.Transform(head.relative.location, new_rotation)

    if random.random() < 0.02:
        print("  HEAD nod: local pitch %.2f -> %.2f  (yaw %.2f, roll %.2f)" % (
            head.relative.rotation.pitch, new_rotation.pitch,
            new_rotation.yaw, new_rotation.roll))

    try:
        pedestrian.set_bones(carla.WalkerBoneControlIn(
            [(HEAD_BONE_NAME, new_head_relative)]))
        pedestrian.show_pose()
    except Exception as exc:
        print("WARNING: could not apply distracted head tilt: %s" % exc)


# ============================================================================
# PEDESTRIAN CONTROLLER (full behavior suite) - MODIFIED FOR AGGRESSIVE & COMMITTED
# ============================================================================

class PedestrianController(object):
    ARRIVE_RADIUS_M = 1.0
    MAX_ACCEL_MPS2 = 3.0   # <-- AGGRESSIVE FIX: increased acceleration for snappy movements

    def __init__(self, pedestrian, spec, geometry, start_override=None, start_yaw=None):
        self.pedestrian = pedestrian
        self.spec = spec
        if start_override is not None:
            self.start = start_override
        else:
            self.start = geometry["start"]
        self.finish = geometry["finish"]
        self.finished = False
        self.started = False
        if start_yaw is not None:
            self.base_yaw = start_yaw
        else:
            dx = self.finish.x - self.start.x
            dy = self.finish.y - self.start.y
            self.base_yaw = math.degrees(math.atan2(dy, dx))
        self.time = 0.0
        self.start_crossing_distance = 25.0
        self.crossing_started = False
        self._current_speed = 0.0
        self._target_speed = 0.0

        cross_dx = self.finish.x - self.start.x
        cross_dy = self.finish.y - self.start.y
        cross_dist = math.hypot(cross_dx, cross_dy) or 1.0
        self.crossing_direction = carla.Vector3D(
            x=cross_dx / cross_dist, y=cross_dy / cross_dist, z=0.0)

        # ---- Store road directions for aggressive pacing ----
        self.road_forward = geometry.get("road_forward", carla.Vector3D(x=1, y=0, z=0))
        self.road_right = geometry.get("road_right", carla.Vector3D(x=0, y=1, z=0))

        self.phase = None
        self.phase_until_tick = 0
        self._progress_fraction = 0.0
        self._current_target = self.finish

    def _point_along_path(self, fraction):
        fraction = max(0.0, min(1.0, fraction))
        return carla.Location(
            x=self.start.x + (self.finish.x - self.start.x) * fraction,
            y=self.start.y + (self.finish.y - self.start.y) * fraction,
            z=self.start.z)

    def _side_jitter(self, point, lateral_m):
        perp_x = -self.crossing_direction.y
        perp_y = self.crossing_direction.x
        return carla.Location(x=point.x + perp_x * lateral_m,
                               y=point.y + perp_y * lateral_m, z=point.z)

    def start_behavior(self):
        print()
        print("Pedestrian controller started.")
        print("Behavior: %s" % self.spec.behavior)
        if self.spec.behavior == "waiting":
            print("Pedestrian will idle (physics disabled).")
        elif self.spec.behavior == "committed":
            print("Pedestrian will cross comfortably and directly.")
            # ---- FIX: start crossing immediately for committed ----
            self.crossing_started = True
            try:
                self.pedestrian.set_simulate_physics(True)
                print("Physics enabled immediately for committed.")
            except Exception as exc:
                print("WARNING: could not enable physics: %s" % exc)
            self._current_speed = 0.0
            # Set initial target speed
            self._target_speed = PEDESTRIAN_SPEED_MPS
        elif self.spec.behavior == "hesitant":
            print("Pedestrian will hesitate at the kerb.")
            # ---- NEW: start hesitant motion immediately, not wait for vehicle ----
            self.crossing_started = True
            try:
                self.pedestrian.set_simulate_physics(True)
                print("Physics enabled immediately for hesitant.")
            except Exception as exc:
                print("WARNING: could not enable physics: %s" % exc)
            self._current_speed = 0.0
            # The _update_hesitant will manage speed and direction
        elif self.spec.behavior == "distracted":
            print("Pedestrian will cross with irregular pace, wandering, and a "
                  "head-down 'looking at phone' pose.")
        elif self.spec.behavior == "aggressive":
            print("Pedestrian will stay on the sidewalk and act aggressively "
                  "(pacing, lunging, erratic).")
        elif self.spec.behavior == "jaywalk":
            print("Pedestrian will cross quickly and directly, away from crosswalk.")
        else:
            print("WARNING: behavior '%s' not implemented." % self.spec.behavior)
        self.started = True

    def _ramp_speed(self, delta_time):
        max_step = self.MAX_ACCEL_MPS2 * delta_time
        diff = self._target_speed - self._current_speed
        if diff > max_step:
            self._current_speed += max_step
        elif diff < -max_step:
            self._current_speed -= max_step
        else:
            self._current_speed = self._target_speed

    def _idle(self, delta_time):
        self._target_speed = 0.0
        self._ramp_speed(delta_time)
        self.pedestrian.apply_control(carla.WalkerControl(
            direction=self.crossing_direction, speed=self._current_speed))

    def update(self, vehicle_location, delta_time=0.05):
        if not self.started:
            return
        if not self.pedestrian.is_alive:
            return

        self.time += delta_time

        # ---- AGGRESSIVE: stay on sidewalk, never cross ----
        if self.spec.behavior == "aggressive":
            # Re-enable physics if not already
            if not self.crossing_started:
                try:
                    self.pedestrian.set_simulate_physics(True)
                    self.crossing_started = True
                except Exception:
                    pass
            # Update aggressive behaviour each frame
            tick_index = int(self.time / delta_time)
            self._update_aggressive(tick_index)
            target = self._current_target
            current = self.pedestrian.get_transform().location
            dx = target.x - current.x
            dy = target.y - current.y
            dist_to_target = math.hypot(dx, dy)

            if dist_to_target < 0.15:
                self._target_speed = 0.0
                self._ramp_speed(delta_time)
                return

            self._ramp_speed(delta_time)
            direction = carla.Vector3D(x=dx / dist_to_target, y=dy / dist_to_target, z=0.0)
            self.pedestrian.apply_control(carla.WalkerControl(
                direction=direction, speed=self._current_speed))
            return

        # ====== Original logic for other behaviours ======
        if self.spec.behavior == "waiting":
            return

        # ---- For committed and hesitant, crossing_started is already True ----
        # For distracted and jaywalk, wait until vehicle is close enough
        if not self.crossing_started:
            dist = horizontal_distance(vehicle_location, self.start)
            if dist > self.start_crossing_distance:
                return
            else:
                self.crossing_started = True
                print("Pedestrian started crossing at t=%.2f" % self.time)
                try:
                    self.pedestrian.set_simulate_physics(True)
                    print("Physics re‑enabled for crossing.")
                except Exception as exc:
                    print("WARNING: could not enable physics: %s" % exc)
                self._current_speed = 0.0

        if self.finished:
            self._idle(delta_time)
            return

        tick_index = int(self.time / delta_time)

        if self.spec.behavior in ("committed", "jaywalk"):
            target = self.finish
            # For committed, ensure speed is set each frame
            self._target_speed = PEDESTRIAN_SPEED_MPS if self.spec.behavior == "committed" else 2.0
        else:
            if self.spec.behavior == "hesitant":
                self._update_hesitant(tick_index)
            elif self.spec.behavior == "distracted":
                self._update_distracted(tick_index)
            target = self._current_target

        current = self.pedestrian.get_transform().location
        dx = target.x - current.x
        dy = target.y - current.y
        dist_to_target = math.hypot(dx, dy)

        checks_arrival = self.spec.behavior in ("committed", "jaywalk")
        if checks_arrival and horizontal_distance(current, self.finish) < self.ARRIVE_RADIUS_M:
            self.finished = True
            print("Pedestrian completed crossing.")
            self._idle(delta_time)
            return

        if dist_to_target < 0.15:
            self._target_speed = 0.0
            self._ramp_speed(delta_time)
            return

        self._ramp_speed(delta_time)
        direction = carla.Vector3D(x=dx / dist_to_target, y=dy / dist_to_target, z=0.0)
        self.pedestrian.apply_control(carla.WalkerControl(
            direction=direction, speed=self._current_speed))

    # MODIFIED: Increase MAX_HESITANT_PROGRESS to 0.50 so hesitation occurs in the middle
    # RAISED to 0.65 -- 0.50 combined with the kerb-side start was reading as
    # "still at the kerb" rather than "hesitating near the crosswalk". Still
    # capped well short of 1.0, so this remains a hesitation, not a crossing.
    MAX_HESITANT_PROGRESS = 0.65
    MAX_DISTRACTED_PROGRESS = 0.48

    # ========================================================================
    # FIXED _update_hesitant – starts moving immediately (no initial pause)
    # ========================================================================
    def _update_hesitant(self, tick_index):
        # If phase is None, start immediately with a stepping phase
        if self.phase is None:
            self.phase = 'stepping'
            self._progress_fraction = 0.02   # small step forward
            self._current_target = self._point_along_path(self._progress_fraction)
            self._target_speed = 0.5
            self.phase_until_tick = tick_index + random.randint(10, 18)
            return

        if tick_index < self.phase_until_tick:
            return

        if self.phase == 'paused':
            # End pause, take a tentative step forward (never backward --
            # "hesitant" is long pauses + small forward steps, capped at
            # MAX_HESITANT_PROGRESS so it still lingers near the crosswalk
            # rather than crossing all the way).
            current = self._progress_fraction
            self._progress_fraction = min(self.MAX_HESITANT_PROGRESS,
                                           current + random.uniform(0.02, 0.05))
            self._current_target = self._point_along_path(self._progress_fraction)
            self._target_speed = 0.5
            self.phase = 'stepping'
            self.phase_until_tick = tick_index + random.randint(10, 18)
        elif self.phase == 'stepping':
            # After a step, pause
            self.phase = 'paused'
            self.phase_until_tick = tick_index + random.randint(30, 60)
            self._target_speed = 0.0

    def _update_distracted(self, tick_index):
        if tick_index < self.phase_until_tick:
            return
        current = self._progress_fraction
        if self.phase in (None, 'paused'):
            self.phase = 'walking'
            self.phase_until_tick = tick_index + random.randint(18, 38)
            self._progress_fraction = min(self.MAX_DISTRACTED_PROGRESS,
                                           current + random.uniform(0.035, 0.075))
            base_target = self._point_along_path(self._progress_fraction)
            if random.random() < 0.70:
                self._current_target = self._side_jitter(base_target, random.uniform(-0.65, 0.65))
            else:
                self._current_target = base_target
            self._target_speed = random.uniform(0.65, 1.15)
            return
        if self.phase == 'walking':
            if random.random() < 0.60:
                self.phase = 'micro_pause'
                self.phase_until_tick = tick_index + random.randint(6, 16)
                self._target_speed = random.uniform(0.0, 0.08)
            else:
                self.phase = 'walking_fast'
                self.phase_until_tick = tick_index + random.randint(12, 28)
                self._target_speed = random.uniform(1.05, 1.45)
            return
        if self.phase == 'micro_pause':
            self.phase = 'walking'
            self.phase_until_tick = tick_index + random.randint(16, 34)
            self._progress_fraction = min(self.MAX_DISTRACTED_PROGRESS,
                                           current + random.uniform(0.025, 0.065))
            base_target = self._point_along_path(self._progress_fraction)
            self._current_target = self._side_jitter(base_target, random.uniform(-0.45, 0.45))
            self._target_speed = random.uniform(0.55, 1.05)
            return
        # walking_fast
        self.phase = 'walking'
        self.phase_until_tick = tick_index + random.randint(14, 32)
        self._progress_fraction = min(self.MAX_DISTRACTED_PROGRESS,
                                       current + random.uniform(0.03, 0.08))
        base_target = self._point_along_path(self._progress_fraction)
        self._current_target = self._side_jitter(base_target, random.uniform(-0.70, 0.70))
        self._target_speed = random.uniform(0.70, 1.30)

    # <-- AGGRESSIVE FIX: extremely aggressive pacing, lunges, sprints -->
    def _update_aggressive(self, tick_index):
        if tick_index < self.phase_until_tick:
            return

        # ---- Extreme lateral pacing along the sidewalk ----
        # Wider range: ±6 meters along the sidewalk
        pace = random.uniform(-6.0, 6.0)

        # ---- Large lunges toward the road ----
        # 40% chance of a big lunge toward the road (up to 2.5m)
        if random.random() < 0.4:
            lunge = random.uniform(0.8, 2.5)   # toward road
        else:
            lunge = 0.0
        # 20% chance of a backward retreat (away from road)
        if random.random() < 0.2:
            lunge = -random.uniform(0.5, 1.5)  # away from road

        # ---- Compute target relative to start ----
        target = carla.Location(
            x=self.start.x + self.road_forward.x * pace + self.road_right.x * lunge,
            y=self.start.y + self.road_forward.y * pace + self.road_right.y * lunge,
            z=self.start.z   # keep same height
        )

        self._current_target = target

        # ---- Sprint speed – even faster (4–6 m/s) ----
        self._target_speed = random.uniform(4.0, 6.0)

        # ---- Very frequent changes (every 2–6 ticks) ----
        self.phase_until_tick = tick_index + random.randint(2, 6)


# ============================================================================
# WEB STREAMING SERVER (feeds the browser dashboard)
# ============================================================================
#
# This file already grabs one RGB frame per tick from the ego camera purely
# to crop the pedestrian for pose estimation. This section reuses those SAME
# frames -- no extra CARLA sensor, no extra simulation cost beyond
# JPEG-encoding a frame already sitting in memory -- and exposes them, plus
# the live prediction/decision state, as a tiny local HTTP endpoint that a
# plain web page can embed directly. This is what lets web_launcher.py /
# index.html show this scenario running in a browser tab instead of you
# watching the CARLA window + this terminal.
#
# Two things are served, kept dependency-free beyond Pillow:
#   GET /stream.mjpg  -> a standard multipart JPEG stream. Works directly
#                        in a plain <img src="..."> tag, no video codec
#                        or JS library needed on the browser side.
#   GET /state        -> JSON with the current scenario/prediction status
#                        (see _SharedDashboardState for the exact fields).
#
# Pillow is required for JPEG encoding. If it isn't installed in this venv,
# streaming is silently disabled and the demo still runs exactly as before
# (prints to the terminal, /state still responds, only the video is
# missing). pip install pillow into THIS SAME venv to enable it.
# ----------------------------------------------------------------------

try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


class _SharedDashboardState(object):
    """Thread-safe box the sim loop writes into and the HTTP handler reads
    from. One instance per process (module-level singleton: SHARED)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._jpeg_bytes = None
        self._log = deque(maxlen=WEB_STREAM_LOG_MAXLEN)
        self._status = {
            "phase": "idle",     # idle -> starting -> running -> finished / error
            "message": "Waiting to start.",
            "scenario_id": None,
            "behavior": None,
            "true_state": None,
            "true_label": None,
            "elapsed_s": 0.0,
            "duration_s": SIMULATION_SECONDS,
            "distance_m": None,
            "predicted_state": None,
            "predicted_label": None,
            "confidence": None,
            "action": None,
            "ttc_s": None,
            "finished": False,
            "correct": None,
            "closest_approach_m": None,
        }

    def log_event(self, message):
        with self._lock:
            self._log.append({"t": time.time(), "message": message})

    def update_status(self, **kwargs):
        with self._lock:
            self._status.update(kwargs)

    def set_frame_from_carla_image(self, image):
        if not _PIL_AVAILABLE:
            return
        try:
            arr = np.frombuffer(image.raw_data, dtype=np.uint8)
            arr = arr.reshape((image.height, image.width, 4))  # BGRA
            rgb = arr[:, :, [2, 1, 0]]
            pil_img = _PILImage.fromarray(rgb)
            if pil_img.width > WEB_STREAM_MAX_WIDTH:
                scale = WEB_STREAM_MAX_WIDTH / float(pil_img.width)
                new_size = (WEB_STREAM_MAX_WIDTH, max(1, int(pil_img.height * scale)))
                pil_img = pil_img.resize(new_size)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=WEB_STREAM_JPEG_QUALITY)
            with self._lock:
                self._jpeg_bytes = buf.getvalue()
        except Exception:
            # Never let a dashboard-only encoding hiccup affect the sim.
            pass

    def get_frame(self):
        with self._lock:
            return self._jpeg_bytes

    def get_status(self):
        with self._lock:
            payload = dict(self._status)
            payload["log"] = list(self._log)
            return payload


SHARED = _SharedDashboardState()

# Lets web_launcher.py ask this process to wind down cleanly (restore CARLA's
# world settings, stop the vehicle) instead of a hard kill -- see the
# SIGTERM handler below and its use in the main simulation loop's condition.
_STOP_REQUESTED = threading.Event()


def _handle_sigterm(_signum, _frame):
    _STOP_REQUESTED.set()


signal.signal(signal.SIGTERM, _handle_sigterm)


class _DashboardHandler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")

    def do_GET(self):
        if self.path.startswith("/state"):
            payload = json.dumps(SHARED.get_status()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self._cors()
            self.end_headers()
            self.wfile.write(payload)

        elif self.path.startswith("/frame.jpg"):
            data = SHARED.get_frame()
            if data is None:
                self.send_response(503)
                self._cors()
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)

        elif self.path.startswith("/stream.mjpg"):
            boundary = "carlaframe"
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=%s" % boundary)
            self._cors()
            self.end_headers()
            last_sent = None
            try:
                while True:
                    data = SHARED.get_frame()
                    if data is not None and data is not last_sent:
                        last_sent = data
                        self.wfile.write(("--%s\r\n" % boundary).encode("ascii"))
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii"))
                        self.wfile.write(data)
                        self.wfile.write(b"\r\n")
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass  # browser tab closed / navigated away -- not an error

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def log_message(self, format, *args):
        pass  # keep the console focused on scenario output, not HTTP noise


def start_web_stream_server():
    server = ThreadingHTTPServer(("0.0.0.0", WEB_STREAM_PORT), _DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("Dashboard stream  : http://0.0.0.0:%d/stream.mjpg  (state: /state)" % WEB_STREAM_PORT)
    if not _PIL_AVAILABLE:
        print("  WARNING: Pillow not installed in this venv -- video stream "
              "disabled, /state JSON still works. pip install pillow to enable it.")
    return server


# ============================================================================
# CAMERA SENSOR, PROJECTION, CROP
# ============================================================================

class CameraBuffer(object):
    def __init__(self):
        self.last_image = None
        self.frame = None

    def callback(self, image):
        self.last_image = image
        self.frame = image.frame
        # Reuse this same frame for the browser dashboard (see the
        # "WEB STREAMING SERVER" section above) -- throttled to every
        # Nth tick so JPEG-encoding a 1280x720 frame at 20Hz doesn't
        # compete with the simulation's own tick budget.
        if image.frame % WEB_STREAM_FRAME_STRIDE == 0:
            SHARED.set_frame_from_carla_image(image)


def attach_camera(world, actors, vehicle):
    bp = world.get_blueprint_library().find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", str(CAMERA_WIDTH))
    bp.set_attribute("image_size_y", str(CAMERA_HEIGHT))
    bp.set_attribute("fov", str(CAMERA_FOV))

    transform = carla.Transform(
        carla.Location(x=1.6, y=0.0, z=1.45),
        carla.Rotation(pitch=-2.0, yaw=0.0, roll=0.0))

    camera = world.spawn_actor(bp, transform, attach_to=vehicle)
    actors.add(camera)
    return camera


CAMERA_LOCAL_X = 1.6
CAMERA_LOCAL_Z = 1.45
CAMERA_MAX_YAW_DEG = 180.0
CAMERA_MAX_PITCH_DEG = 45.0
CAMERA_MAX_YAW_RATE_DEG_PER_TICK = 4.0    # ~80 deg/sec at 20Hz -- fast enough to
                                            # keep up with a normal crossing, slow
                                            # enough that a close/lateral pass
                                            # (waiting, jaywalk) doesn't whip-pan
CAMERA_MAX_PITCH_RATE_DEG_PER_TICK = 3.0


def aim_camera_yaw(vehicle, target_location, distance_m=None):
    # NOTE: aim_camera_yaw / aim_camera_pitch / pedestrian_is_ahead below
    # are currently UNUSED -- the RGB camera stays fixed facing forward
    # for the whole scenario now (main loop no longer calls these). Left
    # in place in case pedestrian-tracking is wanted again later.
    vt = vehicle.get_transform()
    dx = target_location.x - vt.location.x
    dy = target_location.y - vt.location.y
    world_yaw = math.degrees(math.atan2(dy, dx))
    relative_yaw = (world_yaw - vt.rotation.yaw + 180.0) % 360.0 - 180.0
    return max(-CAMERA_MAX_YAW_DEG, min(CAMERA_MAX_YAW_DEG, relative_yaw))


def aim_camera_pitch(vehicle, target_actor):
    vt = vehicle.get_transform()
    fwd = vt.get_forward_vector()
    cam_x = vt.location.x + fwd.x * CAMERA_LOCAL_X
    cam_y = vt.location.y + fwd.y * CAMERA_LOCAL_X
    cam_z = vt.location.z + CAMERA_LOCAL_Z

    target_transform = target_actor.get_transform()
    bbox = target_actor.bounding_box
    target_x = target_transform.location.x + bbox.location.x
    target_y = target_transform.location.y + bbox.location.y
    target_z = target_transform.location.z + bbox.location.z

    horizontal_dist = math.hypot(target_x - cam_x, target_y - cam_y)
    vertical_diff = target_z - cam_z

    if horizontal_dist < 0.5:
        return -2.0

    pitch = math.degrees(math.atan2(vertical_diff, horizontal_dist))
    return max(-CAMERA_MAX_PITCH_DEG, min(CAMERA_MAX_PITCH_DEG, pitch))


def pedestrian_is_ahead(vehicle, ped_location):
    """True while the pedestrian is still in front of the vehicle (dot
    product of the vehicle's forward vector with the vector toward the
    pedestrian). Positive while ahead, negative once the vehicle has
    driven past them. Read this ONCE per tick and latch it (see the main
    loop) rather than branching on it directly every tick -- right at the
    pass point this can flicker across zero for a tick or two (steering
    wobble, lateral offset in scenarios like waiting/jaywalk where the
    pedestrian isn't directly in the driving lane), which would otherwise
    make the camera snap back and forth between tracking and forward-look.
    """
    vt = vehicle.get_transform()
    fwd = vt.get_forward_vector()
    to_ped_x = ped_location.x - vt.location.x
    to_ped_y = ped_location.y - vt.location.y
    return (fwd.x * to_ped_x + fwd.y * to_ped_y) > 0.0


def _step_toward(current, target, max_step):
    """Move `current` toward `target` by at most `max_step` (degrees).

    Used to rate-limit the RGB camera's yaw/pitch so it pans smoothly
    instead of snapping straight to the freshly computed aim angle every
    tick. Matters most on a close/lateral pass -- waiting (pedestrian
    stays fixed at the kerb, close to the driving lane) and jaywalk
    (crosses close to the vehicle, off any crosswalk) both swing the raw
    target angle much faster than committed/hesitant, where the
    pedestrian stays roughly ahead the whole time. Also smooths the
    transition at the exact moment tracking starts or stops (see
    ped_has_passed) instead of snapping straight to forward-look.
    """
    diff = target - current
    if diff > max_step:
        diff = max_step
    elif diff < -max_step:
        diff = -max_step
    return current + diff


# ============================================================================
# SPECTATOR CAMERA – ALWAYS STRAIGHT AHEAD (FIXED)
# ============================================================================

def position_spectator(world, vehicle, pedestrian=None):
    """
    Places the spectator camera behind and slightly above the vehicle,
    always looking straight ahead in the vehicle's forward direction.
    The pedestrian argument is ignored – the camera never rotates toward it.
    """
    spectator = world.get_spectator()
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)

    camera_location = carla.Location(
        x=vehicle_location.x + forward.x * 1.2,
        y=vehicle_location.y + forward.y * 1.2,
        z=vehicle_location.z + 1.55)

    # Always look straight ahead (vehicle's yaw)
    yaw = vehicle_transform.rotation.yaw

    spectator.set_transform(carla.Transform(
        camera_location, carla.Rotation(pitch=-2.0, yaw=yaw, roll=0.0)))


# ============================================================================
# PROJECTION & CROP
# ============================================================================

def build_camera_matrix(width, height, fov):
    focal = width / (2.0 * math.tan(math.radians(fov) / 2.0))
    return np.array([
        [focal, 0.0, width / 2.0],
        [0.0, focal, height / 2.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)


def world_to_camera(location, camera_transform):
    world_matrix = np.array(camera_transform.get_matrix(), dtype=np.float32)
    inv = np.linalg.inv(world_matrix)
    point = np.array([location.x, location.y, location.z, 1.0], dtype=np.float32)
    return np.dot(inv, point)


def project_point(location, camera):
    transform = camera.get_transform()
    point = world_to_camera(location, transform)
    x, y, z = point[0], point[1], point[2]

    if x <= 0.1:
        return None

    K = build_camera_matrix(CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FOV)
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]

    u = fx * y / x + cx
    v = fy * (-z) / x + cy

    return (float(u), float(v), float(x))


def pedestrian_crop(image, pedestrian, camera):
    if image is None:
        return None

    try:
        bbox = pedestrian.bounding_box
        verts = bbox.get_world_vertices(pedestrian.get_transform())
    except Exception:
        verts = None

    points = []
    if verts:
        for v in verts:
            projected = project_point(v, camera)
            if projected is not None:
                points.append(projected)

    if len(points) < 6:
        location = pedestrian.get_location()
        try:
            bb = pedestrian.bounding_box
            half_height = bb.extent.z
            center_z = location.z + bb.location.z
            sample_heights = [center_z - half_height, center_z - half_height * 0.5,
                              center_z, center_z + half_height * 0.5, center_z + half_height]
        except Exception:
            sample_heights = [location.z, location.z + 0.5, location.z + 1.0,
                               location.z + 1.5, location.z + 1.8]
        points = []
        for z in sample_heights:
            p = carla.Location(x=location.x, y=location.y, z=z)
            projected = project_point(p, camera)
            if projected is not None:
                points.append(projected)
        if len(points) < 2:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        height = max(ymax - ymin, MIN_CROP_SIZE)
        width = max(height * 0.45, MIN_CROP_SIZE)
        xmin -= width * CROP_PADDING
        xmax += width * CROP_PADDING
    else:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)

        box_area_fraction = ((x1 - x0) * (y1 - y0)) / float(CAMERA_WIDTH * CAMERA_HEIGHT)
        if box_area_fraction > 0.5:
            return None

        pad_x = (x1 - x0) * CROP_PADDING
        pad_y = (y1 - y0) * CROP_PADDING
        xmin, xmax = x0 - pad_x, x1 + pad_x
        ymin, ymax = y0 - pad_y, y1 + pad_y

    xmin = int(max(0, math.floor(xmin)))
    ymin = int(max(0, math.floor(ymin)))
    xmax = int(min(CAMERA_WIDTH - 1, math.ceil(xmax)))
    ymax = int(min(CAMERA_HEIGHT - 1, math.ceil(ymax)))

    if xmax <= xmin or ymax <= ymin:
        return None

    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = array.reshape((image.height, image.width, 4))
    rgb = array[:, :, :3][:, :, ::-1]
    crop = rgb[ymin:ymax, xmin:xmax]

    if crop.size == 0:
        return None

    return crop


# ============================================================================
# CONTEXT FEATURES
# ============================================================================

def get_crosswalk_context(crosswalks, pedestrian_location):
    if not crosswalks:
        return 0.0, 1.0

    nearest = float("inf")
    for point in crosswalks:
        d = horizontal_distance(pedestrian_location, point)
        nearest = min(nearest, d)

    presence = 1.0 if nearest < 5.0 else 0.0
    distance_norm = min(nearest / 30.0, 1.0)

    return (presence, distance_norm)


def get_context(world, vehicle, pedestrian, crosswalks, spec=None):
    ploc = pedestrian.get_location()
    vloc = vehicle.get_location()

    crosswalk_presence, distance_to_curb = get_crosswalk_context(crosswalks, ploc)
    vehicle_distance = horizontal_distance(ploc, vloc)
    vehicle_distance_norm = min(vehicle_distance / 50.0, 1.0)

    waypoint = world.get_map().get_waypoint(
        ploc, project_to_road=True, lane_type=carla.LaneType.Driving)

    lane_count = 2.0
    if waypoint is not None:
        count = 1
        MAX_LANE_WALK = 8
        try:
            left = waypoint.get_left_lane()
            steps = 0
            while left is not None and steps < MAX_LANE_WALK:
                if left.lane_type != carla.LaneType.Driving:
                    break
                count += 1
                left = left.get_left_lane()
                steps += 1
        except Exception:
            pass

        try:
            right = waypoint.get_right_lane()
            steps = 0
            while right is not None and steps < MAX_LANE_WALK:
                if right.lane_type != carla.LaneType.Driving:
                    break
                count += 1
                right = right.get_right_lane()
                steps += 1
        except Exception:
            pass

        lane_count = float(count)

    road_width_norm = min(lane_count / 6.0, 1.0)

    walkers = world.get_actors().filter("walker.pedestrian.*")
    nearby = 0
    for walker in walkers:
        if not walker.is_alive:
            continue
        if walker.id == pedestrian.id:
            continue
        if horizontal_distance(walker.get_location(), ploc) < 20.0:
            nearby += 1

    pedestrian_density = min(nearby / 10.0, 1.0)

    traffic_light_state = -1.0
    try:
        traffic_light = vehicle.get_traffic_light()
        if traffic_light is not None:
            state = traffic_light.get_state()
            if state == carla.TrafficLightState.Red:
                traffic_light_state = 0.0
            elif state == carla.TrafficLightState.Yellow:
                traffic_light_state = 0.5
            elif state == carla.TrafficLightState.Green:
                traffic_light_state = 1.0
    except Exception:
        pass

    if spec is not None and spec.behavior == "waiting":
        distance_to_curb = 1.0
        crosswalk_presence = 0.0

    return {
        "traffic_light_state": traffic_light_state,
        "vehicle_distance_norm": vehicle_distance_norm,
        "crosswalk_presence": crosswalk_presence,
        "road_width_norm": road_width_norm,
        "pedestrian_density": pedestrian_density,
        "distance_to_curb_norm": distance_to_curb,
    }


# ============================================================================
# ENSEMBLE & LIVE ML
# ============================================================================

def ensemble_predict(sequence):
    sequence = np.asarray(sequence, dtype=np.float32)
    if sequence.shape != (WINDOW_SIZE, 36):
        raise ValueError("Expected sequence shape (30,36), got %s" % (sequence.shape,))

    payload = json.dumps({"sequence": sequence.tolist()}).encode("utf-8")
    request = urllib.request.Request(
        ENSEMBLE_SERVER_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")

    with urllib.request.urlopen(request, timeout=5.0) as response:
        result = json.loads(response.read().decode("utf-8"))

    if "error" in result:
        raise RuntimeError(result["error"])

    return result


class LiveML(object):
    def __init__(self):
        self.pose = PoseExtractor(POSE_SERVER_URL, timeout=3.0)
        self.tracker = PedestrianTracker(ped_id=-1)
        self.features = []
        self.last_prediction = None
        self.last_prediction_frame = -1
        self.pose_ok = 0
        self.pose_fail = 0

    def process(self, crop, frame_index, context):
        landmarks = None
        if crop is not None:
            landmarks = self.pose.extract(crop)

        if landmarks is not None:
            self.pose_ok += 1
        else:
            self.pose_fail += 1

        self.tracker.set_context(**context)
        self.tracker.update(landmarks, frame_index=frame_index)

        feature_vector = self.tracker.compute_feature_vector()
        self.features.append(feature_vector)

        if len(self.features) > WINDOW_SIZE:
            self.features = self.features[-WINDOW_SIZE:]

        if len(self.features) == WINDOW_SIZE and landmarks is not None:
            try:
                result = ensemble_predict(np.stack(self.features, axis=0))
                self.last_prediction = result
                self.last_prediction_frame = frame_index
            except Exception as exc:
                print("\nENSEMBLE ERROR: %s" % exc)

        return (feature_vector, landmarks)

    def close(self):
        self.pose.close()


# ============================================================================
# STATUS
# ============================================================================

def print_live_status(elapsed, frame_index, vehicle, pedestrian, spec, live_ml, last_print):
    if elapsed - last_print < 1.0:
        return last_print

    if not pedestrian.is_alive:
        return elapsed

    d = horizontal_distance(vehicle.get_location(), pedestrian.get_location())
    prediction = live_ml.last_prediction

    if prediction is None:
        prediction_text = "warming up"
        confidence_text = "-"
    else:
        state = prediction.get("mental_state", -1)
        prediction_text = LABELS.get(state, str(state))
        confidence_text = "%.2f" % (prediction.get("confidence", 0.0))

    print("[t=%5.1fs] frame=%4d distance=%6.2fm GT=%-10s ML=%-10s conf=%s pose=%d/%d buffer=%d/30" % (
        elapsed, frame_index, d, spec.behavior, prediction_text, confidence_text,
        live_ml.pose_ok, (live_ml.pose_ok + live_ml.pose_fail), len(live_ml.features)))

    return elapsed


# ============================================================================
# MAIN SCENARIO
# ============================================================================

def run_scenario(client, world, spec, seed):
    actors = ActorManager()
    live_ml = LiveML()
    original_settings = world.get_settings()

    print()
    print("=" * 72)
    print("CARLA LIVE SCENARIO-SUITE + ML DEMO")
    print("=" * 72)

    print_scenario_info(spec)
    print("CARLA map        : %s" % world.get_map().name)
    print("Scenario seed    : %d" % seed)

    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
    world.apply_settings(settings)

    print()
    print("Synchronous mode : ON")
    print("Fixed timestep   : %.3fs" % FIXED_DELTA_SECONDS)

    try:
        # ---- Clear existing vehicles ----
        clear_traffic(world)

        make_weather(world, spec)

        # -------- Spawn vehicle --------
        geometry = None

        # Force fallback geometry for distracted and aggressive to guarantee
        # pedestrian spawn -- hesitant now uses the same robust crosswalk-
        # first placement as committed instead (see below), since the old
        # explicit-vehicle_spawn_index approach for hesitant was confirmed
        # via an actual run to land somewhere with no real crosswalk within
        # 200m and a driven path that ended up in the wrong lane entirely.
        use_fallback_only = spec.behavior in ("distracted", "aggressive")

        if spec.behavior in ("committed", "hesitant"):
            warmup_distance_m = (spec.ego_cruise_kmh / 3.6) * VEHICLE_ONLY_SECONDS
            # skip_count picks a DIFFERENT real crosswalk per behavior, so
            # hesitant doesn't land on the exact same crossing as committed.
            skip_count = 0 if spec.behavior == "committed" else 2
            print("Looking for a real crosswalk to position vehicle "
                  "(skip_count=%d)..." % skip_count)
            geometry = find_verified_crosswalk_for_vehicle(
                world, approach_distance_m=TARGET_DISTANCE_M + warmup_distance_m,
                skip_count=skip_count)

        # --- Spawn vehicle ---
        all_spawn_points = world.get_map().get_spawn_points()
        if not all_spawn_points:
            raise RuntimeError("No vehicle spawn points available.")

        if geometry is not None:
            print()
            print("REAL CARLA CROSSWALK FOUND -- placing vehicle behind it.")
            vehicle = spawn_vehicle_at_transform(world, actors, geometry["vehicle_transform"])
        elif spec.vehicle_spawn_index is not None:
            idx = spec.vehicle_spawn_index % len(all_spawn_points)
            vehicle_transform = all_spawn_points[idx]
            print(f"Using explicit spawn index {idx} (original {spec.vehicle_spawn_index})")
            vehicle = spawn_vehicle_at_transform(world, actors, vehicle_transform)
            geometry = None  # will be set after warm-up
        else:
            vehicle = spawn_vehicle(world, actors, seed)

        world.tick()

        camera_buffer = CameraBuffer()
        camera = attach_camera(world, actors, vehicle)
        camera.listen(camera_buffer.callback)

        SHARED.update_status(phase="running", message="Vehicle driving toward pedestrian.")
        SHARED.log_event("Vehicle spawned, camera attached.")

        # -------- Warm-up drive --------
        print()
        print("Vehicle will drive alone for %.1fs." % VEHICLE_ONLY_SECONDS)
        vehicle_ticks = int(VEHICLE_ONLY_SECONDS / FIXED_DELTA_SECONDS)

        for warmup_i in range(vehicle_ticks):
            if warmup_i == 0 or warmup_i == vehicle_ticks - 1:
                print("[warmup %d/%d] tick..." % (warmup_i, vehicle_ticks), flush=True)
            steer = compute_steer(world, vehicle)
            drive_vehicle(vehicle, spec.ego_cruise_kmh, action='MAINTAIN', steer=steer)
            position_spectator(world, vehicle)
            world.tick()
        print("Warm-up drive complete.", flush=True)

        # -------- Determine geometry based on scenario --------
        if spec.behavior == "waiting":
            print("Finding a waiting location on the RIGHT sidewalk...")
            # <-- MODIFIED: pass prefer_right=True to place on the right side
            geometry = find_waiting_location(world, vehicle, prefer_right=True)
            if geometry is None:
                print("WARNING: Could not find right sidewalk, using fallback geometry.")
                # If fallback, we still want right side, so flip_side=True for right
                geometry = find_fallback_geometry(world, vehicle, flip_side=True)

        elif spec.behavior == "aggressive":
            print("Finding a sidewalk location for aggressive pedestrian (will NOT cross)...")
            geometry = find_waiting_location(world, vehicle)
            if geometry is None:
                print("WARNING: Could not find sidewalk, using fallback (but will stay near start).")
                geometry = find_fallback_geometry(world, vehicle)
            else:
                # Shift the spawn point closer to the road (toward the driving lane)
                shift_toward_road = -1.5   # meters (negative road_right moves toward road)
                road_right = geometry["road_right"]
                start = geometry["start"]
                center = geometry["center"]
                # shift start and center
                new_start = carla.Location(
                    x=start.x + road_right.x * shift_toward_road,
                    y=start.y + road_right.y * shift_toward_road,
                    z=start.z
                )
                new_center = carla.Location(
                    x=center.x + road_right.x * shift_toward_road,
                    y=center.y + road_right.y * shift_toward_road,
                    z=center.z
                )
                # update geometry
                geometry["start"] = new_start
                geometry["center"] = new_center
                geometry["finish"] = new_start  # keep finish same as start for aggressive
                print("Shifted aggressive spawn toward the road by %.2fm" % abs(shift_toward_road))

        elif spec.behavior == "jaywalk":
            print("Finding a jaywalk location (away from crosswalks)...")
            geometry = find_jaywalk_geometry(world, vehicle)
            if geometry is None:
                print("WARNING: No suitable jaywalk location, using fallback.")
                geometry = find_fallback_geometry(world, vehicle)

        elif spec.behavior == "hesitant":
            # geometry was already found (and used to place the vehicle)
            # BEFORE the warm-up drive, same as committed -- searching
            # again here would risk picking a DIFFERENT crosswalk than
            # the one the vehicle is actually positioned behind, putting
            # the vehicle's real driven path and the pedestrian's
            # location out of sync exactly like the earlier bug this
            # replaced. Only search now as a genuine last resort, if for
            # some reason geometry wasn't already found.
            if geometry is None:
                print("Finding a real crosswalk near which the hesitant pedestrian will linger...")
                geometry = find_crosswalk_ahead_of_vehicle(world, vehicle, max_distance=200.0)
            if geometry is None:
                print("WARNING: Still no real crosswalk found ahead of THIS vehicle -- "
                      "using generic fallback geometry (still relative to the vehicle, "
                      "just not tied to an actual marked crossing).")
                geometry = find_fallback_geometry(world, vehicle)
            else:
                # geometry["start"]/["finish"] span the full crosswalk width
                # (one kerb to the other). "start" is offset in the POSITIVE
                # road_right direction from the crosswalk centre (see
                # crosswalk_polygon_geometry above) -- for a vehicle
                # travelling forward, positive road_right (a +90 degree
                # rotation of forward) points to the vehicle's RIGHT-hand
                # side. So "start" is already the right-hand kerb: the
                # pedestrian spawns there and lingers, with _update_hesitant's
                # tentative steps advancing (forward only -- no backward
                # steps) toward "finish" (the far kerb), capped at
                # MAX_HESITANT_PROGRESS so it stays a hesitation near the
                # crosswalk, not an actual crossing. (Deliberately NOT
                # collapsing finish to start -- that would remove any
                # distance to interpolate along, and the tentative steps
                # would never move at all.)
                print("Hesitant pedestrian anchored at the RIGHT-hand kerb, "
                      "near this crosswalk -- tentative steps lean toward "
                      "the crossing but stay capped well short of it.")

                # ---- NEW: shift spawn point closer to road centre ----
                shift_toward_centre = 3.0  # meters inward -- was 2.0, moved in further
                                            # so the pedestrian starts visibly closer
                                            # to the crosswalk instead of just at the kerb
                road_right = geometry["road_right"]
                start = geometry["start"]
                new_start = carla.Location(
                    x=start.x - road_right.x * shift_toward_centre,
                    y=start.y - road_right.y * shift_toward_centre,
                    z=start.z
                )
                geometry["start"] = new_start
                # Also shift center if present
                if "center" in geometry:
                    center = geometry["center"]
                    geometry["center"] = carla.Location(
                        x=center.x - road_right.x * shift_toward_centre,
                        y=center.y - road_right.y * shift_toward_centre,
                        z=center.z
                    )
                print("Moved hesitant spawn closer to road centre by %.2fm" % shift_toward_centre)

        elif use_fallback_only:   # distracted, aggressive
            print("Forcing fallback geometry for behaviour: %s" % spec.behavior)
            # For distracted, flip side so pedestrian appears on the right
            flip = (spec.behavior == "distracted")
            geometry = find_fallback_geometry(world, vehicle, flip_side=flip)

        else:  # committed and others
            if geometry is None:
                print("Trying to find a crosswalk ahead of the vehicle after warm-up...")
                geometry = find_crosswalk_ahead_of_vehicle(world, vehicle)
                if geometry is not None:
                    print("Found crosswalk after warm-up drive.")
            if geometry is None:
                geometry = find_verified_crosswalk_for_vehicle(
                    world, approach_distance_m=TARGET_DISTANCE_M)
            if geometry is None:
                print("No crosswalk found, using fallback geometry.")
                geometry = find_fallback_geometry(world, vehicle)

        # Ensure geometry is always valid
        if geometry is None:
            geometry = find_fallback_geometry(world, vehicle)

        waypoint = geometry.get("waypoint")

        print()
        print("Scenario geometry:")
        print("  real_crosswalk: %s" % geometry.get("real_crosswalk", False))
        print("  crossing start: (%.2f, %.2f, %.2f)" % (
            geometry["start"].x, geometry["start"].y, geometry["start"].z))
        print("  crossing end  : (%.2f, %.2f, %.2f)" % (
            geometry["finish"].x, geometry["finish"].y, geometry["finish"].z))
        print("  crossing distance: %.2fm" % horizontal_distance(geometry["start"], geometry["finish"]))

        # -------- Spawn pedestrian --------
        print()
        print("Spawning scenario pedestrian...", flush=True)
        pedestrian, actual_spawn_loc, spawn_yaw = spawn_pedestrian(world, actors, geometry, spec)
        print("Pedestrian spawn call returned.", flush=True)

        position_spectator(world, vehicle, pedestrian)
        actual = pedestrian.get_location()
        print("Verified pedestrian location: (%.2f, %.2f, %.2f)" % (actual.x, actual.y, actual.z))

        controller = PedestrianController(pedestrian, spec, geometry,
                                          start_override=actual_spawn_loc,
                                          start_yaw=spawn_yaw)
        controller.start_behavior()

        # ---- Camera stays fixed facing forward -- never aims at the
        # pedestrian, at any point in the scenario ----
        camera_yaw_state = 0.0
        camera_pitch_state = -2.0
        camera.set_transform(carla.Transform(
            carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
            carla.Rotation(pitch=camera_pitch_state, yaw=camera_yaw_state, roll=0.0)))

        print("Caching crosswalk data...", flush=True)
        cached_crosswalks = world.get_map().get_crosswalks() if hasattr(world.get_map(), 'get_crosswalks') else []
        print("Cached %d crosswalk point(s)." % len(cached_crosswalks), flush=True)

        agent = RuleBasedAgent()
        current_action = 'MAINTAIN'
        previous_web_action = None  # only used to avoid spamming the dashboard log
        distance_history = deque(maxlen=15)
        ped_distance_m = None

        # ------------------------------------------------------------------
        # SAFETY: dynamic stopping distance (replaces old HARD_STOP_DISTANCE_M)
        # ------------------------------------------------------------------
        # We compute required stopping distance from current speed.
        # If actual distance < required + margin, force STOP.
        # ------------------------------------------------------------------

        print()
        print("=" * 72)
        print("LIVE ML PIPELINE")
        print("=" * 72)
        print("Pose server      : %s" % POSE_SERVER_URL)
        print("Ensemble server  : %s" % ENSEMBLE_SERVER_URL)
        print("Feature shape    : 36")
        print("Temporal window  : 30 frames")
        print("=" * 72)

        frame_index = 0
        closest_distance = float("inf")
        closest_time = 0.0
        last_print = -1.0

        while (frame_index < int(SIMULATION_SECONDS / FIXED_DELTA_SECONDS)
               and not _STOP_REQUESTED.is_set()):
            elapsed = frame_index * FIXED_DELTA_SECONDS

            steer = compute_steer(world, vehicle)
            effective_action = current_action

            # ---- DYNAMIC SAFETY FLOOR ----
            if ped_distance_m is not None:
                velocity = vehicle.get_velocity()
                speed_ms = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
                # stopping distance = v² / (2 * a) + margin
                stopping_dist = (speed_ms**2) / (2 * MAX_DECEL_MPS2) + SAFETY_MARGIN_M
                if ped_distance_m < stopping_dist and effective_action != 'STOP':
                    if frame_index % 10 == 0:
                        print(f"[t={elapsed:5.1f}s] SAFETY: forcing STOP (model said {current_action}, "
                              f"distance={ped_distance_m:.2f}m < stopping_dist={stopping_dist:.2f}m)")
                    effective_action = 'STOP'

            drive_vehicle(vehicle, spec.ego_cruise_kmh, action=effective_action, steer=steer)
            controller.update(vehicle.get_location(), FIXED_DELTA_SECONDS)

            # Spectator always straight ahead
            position_spectator(world, vehicle, pedestrian)

            # The RGB camera (used for ML + the website video feed) stays
            # fixed, facing forward, for the whole scenario -- it never
            # pans toward the pedestrian, during approach or after passing.
            camera.set_transform(carla.Transform(
                carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
                carla.Rotation(pitch=camera_pitch_state, yaw=camera_yaw_state, roll=0.0)))

            world.tick()

            # ---- FIX: apply distracted head-down pose AFTER world.tick() ----
            if spec.behavior == "distracted":
                apply_distracted_head_tilt(pedestrian)

            ped_distance_m = None
            if vehicle.is_alive and pedestrian.is_alive:
                d = horizontal_distance(vehicle.get_location(), pedestrian.get_location())
                ped_distance_m = d
                distance_history.append((frame_index, d))
                if d < closest_distance:
                    closest_distance = d
                    closest_time = elapsed

            if frame_index % 4 == 0:  # ~5Hz -- plenty for a UI readout
                SHARED.update_status(elapsed_s=elapsed, distance_m=ped_distance_m)

            image = camera_buffer.last_image
            closing_speed_ms = None
            if len(distance_history) >= 2:
                oldest_i, oldest_d = distance_history[0]
                newest_i, newest_d = distance_history[-1]
                dt = (newest_i - oldest_i) * FIXED_DELTA_SECONDS
                if dt > 0:
                    closing_speed_ms = (oldest_d - newest_d) / dt

            if image is not None:
                try:
                    crop = pedestrian_crop(image, pedestrian, camera)
                    context = get_context(world, vehicle, pedestrian, cached_crosswalks, spec=spec)
                    feature_vector, landmarks = live_ml.process(crop, frame_index, context)

                    if live_ml.last_prediction_frame == frame_index and live_ml.last_prediction:
                        pred = live_ml.last_prediction
                        mental_state = pred.get('mental_state', -1)
                        confidence = pred.get('confidence', 0.0)

                        velocity = vehicle.get_velocity()
                        vehicle_speed_kmh = math.sqrt(velocity.x ** 2 + velocity.y ** 2) * 3.6

                        decision = agent.decide(
                            feature_vector, mental_state, confidence=confidence,
                            vehicle_speed_kmh=vehicle_speed_kmh, distance_m=ped_distance_m,
                            closing_speed_ms=closing_speed_ms,
                        )
                        current_action = decision['action']
                        ttc_str = "%.2fs" % decision['ttc'] if np.isfinite(decision['ttc']) else "inf"
                        print("\n[t=%5.1fs] DECISION: state=%s conf=%.2f ttc=%s action=%s reason=%s" % (
                            elapsed, LABELS.get(mental_state, '?'), confidence,
                            ttc_str, current_action, decision.get('reason', '')))
                        print("  Raw features: speed=%.4f avg_speed=%.4f step_freq=%.3f "
                              "pause_dur=%.3f hesitation=%.3f move_prob=%.3f" % (
                            feature_vector[0], feature_vector[1], feature_vector[6],
                            feature_vector[22], feature_vector[23], feature_vector[27]))

                        SHARED.update_status(
                            predicted_state=mental_state,
                            predicted_label=LABELS.get(mental_state, '?'),
                            confidence=confidence,
                            action=current_action,
                            ttc_s=(decision['ttc'] if np.isfinite(decision['ttc']) else None),
                            message="Predicted %s (%.0f%% conf) -> %s" % (
                                LABELS.get(mental_state, '?'), confidence * 100, current_action),
                        )
                        if current_action != previous_web_action:
                            SHARED.log_event("Decision: %s (%s)" % (
                                current_action, decision.get('reason', '')))
                            previous_web_action = current_action
                except Exception as exc:
                    print("\nML frame error: %s" % exc)

            last_print = print_live_status(
                elapsed, frame_index, vehicle, pedestrian, spec, live_ml, last_print)

            frame_index += 1

        vehicle.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
        world.tick()

        print()
        print("=" * 72)
        print("SCENARIO RESULT: %s" % spec.id)
        print("=" * 72)
        print("Ground truth state : %d (%s)" % (spec.true_state, LABELS.get(spec.true_state, "?")))
        print("Scenario behaviour : %s" % spec.behavior)
        print("Pedestrian finished crossing: %s" % getattr(controller, "finished", "N/A"))

        correct = None
        if live_ml.last_prediction:
            prediction = live_ml.last_prediction
            state = prediction.get("mental_state", -1)
            confidence = prediction.get("confidence", 0.0)

            print()
            print("LIVE MODEL RESULT")
            print("Predicted state    : %d (%s)" % (state, LABELS.get(state, "?")))
            print("Confidence         : %.4f" % confidence)

            probs = prediction.get("probs")
            if probs:
                print()
                print("Class probabilities:")
                for i, p in enumerate(probs):
                    print("  %-10s : %.4f" % (LABELS[i], p))

            correct = state == spec.true_state
            print()
            print("Prediction correct : %s" % ("YES" if correct else "NO"))
        else:
            print()
            print("LIVE MODEL RESULT")
            print("No prediction produced.")
            print("Pose successes     : %d" % live_ml.pose_ok)
            print("Pose failures      : %d" % live_ml.pose_fail)
            print("Feature vectors    : %d" % len(live_ml.features))

        print()
        print("Pose diagnostic breakdown:")
        print("  accepted (visibility OK)   : %d" % live_ml.pose.accepted)
        print("  rejected (low visibility)  : %d" % live_ml.pose.rejected_low_visibility)
        print("  no detection / other fail  : %d" % (
            live_ml.pose_fail - live_ml.pose.rejected_low_visibility))

        print()
        final_effective_action = current_action
        if ped_distance_m is not None:
            velocity = vehicle.get_velocity()
            speed_ms = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
            stopping_dist = (speed_ms**2) / (2 * MAX_DECEL_MPS2) + SAFETY_MARGIN_M
            if ped_distance_m < stopping_dist:
                final_effective_action = 'STOP'
        print("Final model action  : %s" % current_action)
        print("Final applied action: %s%s" % (
            final_effective_action,
            "  (safety floor overrode the model)" if final_effective_action != current_action else ""))
        if closest_distance != float("inf"):
            print("Closest approach   : %.2fm at t=%.2fs" % (closest_distance, closest_time))

        print("=" * 72)

        stopped_early = _STOP_REQUESTED.is_set()
        SHARED.update_status(
            phase="finished",
            finished=True,
            action=final_effective_action,
            correct=correct,
            closest_approach_m=(closest_distance if closest_distance != float("inf") else None),
            message="Scenario stopped early." if stopped_early else "Scenario complete.",
        )
        SHARED.log_event("Scenario '%s' stopped early." % spec.id if stopped_early
                          else "Scenario '%s' finished." % spec.id)

    finally:
        try:
            if "camera" in locals():
                camera.stop()
        except Exception:
            pass

        try:
            live_ml.close()
        except Exception:
            pass

        actors.cleanup()

        try:
            world.apply_settings(original_settings)
        except Exception as exc:
            print("WARNING: could not restore world settings: %s" % exc)

        print("CARLA scenario finished.")


# ============================================================================
# VEHICLE CONTROL (steering, driving)
# ============================================================================

ACTION_SPEED_FACTOR = {
    'MAINTAIN': 1.0,
    'SLOW_DOWN': 0.5,
    'STOP': 0.0,
}


def compute_steer(world, vehicle, lookahead_m=6.0, gain=1.5):
    vt = vehicle.get_transform()
    wp = world.get_map().get_waypoint(vt.location, lane_type=carla.LaneType.Driving)
    if wp is None:
        return 0.0
    next_wps = wp.next(lookahead_m)
    if not next_wps:
        return 0.0
    target_loc = next_wps[0].transform.location

    forward = vt.get_forward_vector()
    to_target_x = target_loc.x - vt.location.x
    to_target_y = target_loc.y - vt.location.y
    dot = forward.x * to_target_x + forward.y * to_target_y
    cross = forward.x * to_target_y - forward.y * to_target_x
    angle = math.atan2(cross, dot)

    steer = gain * angle / math.radians(45.0)
    return max(-1.0, min(1.0, steer))


def drive_vehicle(vehicle, target_kmh, action='MAINTAIN', steer=0.0):
    target_speed_ms = (target_kmh / 3.6) * ACTION_SPEED_FACTOR.get(action, 1.0)
    velocity = vehicle.get_velocity()
    current_speed_ms = math.sqrt(velocity.x ** 2 + velocity.y ** 2)

    control = carla.VehicleControl()
    control.steer = steer
    if current_speed_ms < target_speed_ms:
        control.throttle = 0.5
        control.brake = 0.0
    elif action == 'STOP':
        control.throttle = 0.0
        control.brake = 1.0
    else:
        control.throttle = 0.0
        control.brake = 0.3

    vehicle.apply_control(control)
    return target_kmh / 3.6


# ============================================================================
# ARGUMENTS & MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=list_scenario_ids())
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--host", default=CARLA_HOST)
    parser.add_argument("--port", type=int, default=CARLA_PORT)
    return parser.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    start_web_stream_server()

    try:
        spec = get_scenario(args.scenario)
    except Exception as exc:
        print("ERROR loading scenario: %s" % exc)
        SHARED.update_status(phase="error", message="Unknown scenario: %s" % exc)
        return 1

    SHARED.update_status(
        phase="starting",
        message="Connecting to CARLA...",
        scenario_id=spec.id,
        behavior=spec.behavior,
        true_state=spec.true_state,
        true_label=LABELS.get(spec.true_state),
        elapsed_s=0.0,
        duration_s=SIMULATION_SECONDS,
        distance_m=None,
        predicted_state=None,
        predicted_label=None,
        confidence=None,
        action=None,
        ttc_s=None,
        finished=False,
        correct=None,
        closest_approach_m=None,
    )
    SHARED.log_event("Loaded scenario '%s' (%s)" % (spec.id, spec.behavior))

    print()
    print("=" * 72)
    print("CARLA LIVE SCENARIO-SUITE DEMO")
    print("=" * 72)
    print("Scenario ID       : %s" % spec.id)
    print("True state        : %d" % spec.true_state)
    print("Behaviour         : %s" % spec.behavior)
    print("Description       : %s" % spec.description)
    print("Weather           : %s" % spec.weather_preset)
    print("Scenario seed     : %d" % args.seed)

    print()
    print("Connecting to CARLA...")
    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(CARLA_TIMEOUT)
        world = client.get_world()
    except Exception as exc:
        message = "Could not connect to CARLA at %s:%d -- %s" % (args.host, args.port, exc)
        print("ERROR: %s" % message)
        SHARED.update_status(phase="error", message=message)
        SHARED.log_event(message)
        return 1

    print("Connected to CARLA.")
    print("Map: %s" % world.get_map().name)
    print("Waiting for CARLA world to settle...")
    time.sleep(1.0)

    try:
        run_scenario(client, world, spec, args.seed)
    except Exception as exc:
        message = "Scenario crashed: %s" % exc
        print("ERROR: %s" % message)
        SHARED.update_status(phase="error", message=message, finished=True)
        SHARED.log_event(message)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())