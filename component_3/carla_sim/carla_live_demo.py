# -*- coding: utf-8 -*-
"""
CARLA DEBUG LIVE SCENARIO + 36-FEATURE ML DEMO
(Forced fallback geometry for hesitant/distracted/aggressive)


"""

from __future__ import print_function

import argparse
import io
import json
import math
import random
import re
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
YOLO_SERVER_URL = "http://127.0.0.1:8094/track"
YOLO_FRAME_STRIDE = 1

FIXED_DELTA_SECONDS = 0.05

SIMULATION_SECONDS = 60.0
VEHICLE_ONLY_SECONDS = 3.0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FOV = 90.0

TARGET_DISTANCE_M = 32.0

PEDESTRIAN_SPEED_MPS = 1.5

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

WEB_STREAM_PORT = 8093
WEB_STREAM_JPEG_QUALITY = 70
WEB_STREAM_MAX_WIDTH = 960
WEB_STREAM_FRAME_STRIDE = 2
WEB_STREAM_LOG_MAXLEN = 40

DISTRACTED_NOD_DEGREES = 25.0
DISTRACTED_NOD_SIGN = -1.0

MAX_DECEL_MPS2 = 6.0
SAFETY_MARGIN_M = 1.5

MAX_CROSSING_DISTANCE_M = 14.0


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
# CLEAR STALE ACTORS
# ============================================================================

def clear_stale_actors(world):
    stale = list(world.get_actors().filter('vehicle.*'))
    stale += list(world.get_actors().filter('walker.pedestrian.*'))
    stale += list(world.get_actors().filter('sensor.camera.*'))

    cleared = 0
    for actor in stale:
        if not actor.is_alive:
            continue
        try:
            if actor.type_id.startswith('sensor.'):
                actor.stop()
        except Exception:
            pass
        try:
            actor.destroy()
            cleared += 1
        except Exception:
            pass

    print(f"Cleared {cleared} stale actor(s) from a previous run "
          f"(vehicles, pedestrians, and camera sensors).")


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
# CROSSWALK DETECTION
# ============================================================================

def nearest_waypoint(world, location):
    return world.get_map().get_waypoint(
        location, project_to_road=True, lane_type=carla.LaneType.Driving)

def crosswalk_polygon_geometry(all_points, anchor_point, road_right, cluster_radius_m=15.0, extra_margin_m=3.5):
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
# WAITING LOCATION
# ============================================================================

def find_aggressive_right_side_geometry(world, vehicle):
    """Find a right-side sidewalk point close to the kerb, with early approach visibility."""
    transform = vehicle.get_transform()
    origin = transform.location
    forward = get_forward_vector(transform)
    right = get_right_vector(transform)
    carla_map = world.get_map()
    # Search farther ahead for more approach frames, but choose the nearest
    # safe sidewalk to the road rather than a deep building-side position.
    for distance in range(38, 29, -2):
        ahead = add_vector(origin, forward, distance)
        candidates = []
        for offset in (3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0):
            probe = add_vector(ahead, right, offset)
            wp = carla_map.get_waypoint(probe, project_to_road=True,
                                        lane_type=carla.LaneType.Sidewalk)
            if wp is None or wp.is_junction:
                continue
            spot = wp.transform.location
            # Place the walker toward the ROAD-FACING edge of this sidewalk
            # instead of leaving it at the sidewalk lane centre.
            # Validate with non-projecting waypoint lookup to avoid road spawn.
            sidewalk_half = max(0.0, float(wp.lane_width) * 0.5 - 0.35)
            if sidewalk_half > 0.0:
                toward_road = carla.Location(
                    x=spot.x - right.x * sidewalk_half,
                    y=spot.y - right.y * sidewalk_half,
                    z=spot.z)
                edge_wp = carla_map.get_waypoint(
                    toward_road, project_to_road=False,
                    lane_type=carla.LaneType.Sidewalk)
                if edge_wp is not None and edge_wp.lane_id == wp.lane_id:
                    spot = toward_road
            dx, dy = spot.x - origin.x, spot.y - origin.y
            lateral = dx * right.x + dy * right.y
            if lateral < 1.8 or lateral > 8.0:
                continue
            if horizontal_distance(spot, probe) > 1.5:
                continue
            candidates.append((lateral, spot, wp))
        if candidates:
            _, spot, wp = min(candidates, key=lambda item: item[0])
            return {
                "center": spot, "start": spot, "finish": spot,
                "road_forward": forward, "road_right": right,
                "waypoint": wp, "real_crosswalk": False,
                "pedestrian_yaw": math.degrees(math.atan2(forward.y, forward.x)),
            }
    raise RuntimeError("Aggressive: no safe RIGHT-side kerb sidewalk found ahead; refusing road spawn.")


def find_waiting_location(world, vehicle, prefer_right=False):
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)
    right = get_right_vector(vehicle_transform)
    lateral = right if not prefer_right else get_right_vector(vehicle_transform)

    for d in range(25, 45, 2):
        ahead = add_vector(vehicle_location, forward, d)
        sidewalk_wp = world.get_map().get_waypoint(ahead, project_to_road=True,
                                                   lane_type=carla.LaneType.Sidewalk)
        if sidewalk_wp is not None and not sidewalk_wp.is_junction:
            spot = sidewalk_wp.transform.location
            if horizontal_distance(spot, ahead) > 10.0:
                continue
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


def place_hesitant_at_kerb(world, geometry, kerb_clearance_m=0.55):
    """Place hesitant start just outside nearest driving-lane boundary.

    Unlike the old 2m capped shift, use the actual lane width to locate the
    kerb. Keep the crossing finish unchanged so hesitant movement still points
    across the road. Only the hesitant scenario calls this function.
    """
    start = geometry.get("start")
    if start is None:
        return geometry
    road_wp = world.get_map().get_waypoint(
        start, project_to_road=True, lane_type=carla.LaneType.Driving)
    if road_wp is None:
        print("Hesitant kerb placement: no driving waypoint; keeping original start")
        return geometry
    lane_centre = road_wp.transform.location
    dx, dy = start.x - lane_centre.x, start.y - lane_centre.y
    distance = math.hypot(dx, dy)
    if distance < 0.1:
        print("Hesitant kerb placement: ambiguous side; keeping original start")
        return geometry
    target_distance = max(1.0, road_wp.lane_width * 0.5 + kerb_clearance_m)
    # Avoid moving a pedestrian that is already at the kerb, or one located
    # inside the driving lane, where the intended sidewalk side is ambiguous.
    if distance <= target_distance:
        print("Hesitant kerb placement: already near lane edge (%.2fm)" % distance)
        return geometry
    moved = carla.Location(
        x=lane_centre.x + dx / distance * target_distance,
        y=lane_centre.y + dy / distance * target_distance,
        z=start.z)
    geometry["start"] = moved
    geometry["center"] = moved
    # CARLA crosswalk points can give an almost zero-length crossing
    # (observed 0.07m). Give ONLY hesitant a real inward path so the
    # controller cannot immediately mark it complete at spawn.
    finish = geometry.get("finish")
    if finish is None or horizontal_distance(moved, finish) < 2.5:
        inward_x = (lane_centre.x - moved.x) / target_distance
        inward_y = (lane_centre.y - moved.y) / target_distance
        geometry["finish"] = carla.Location(
            x=moved.x + inward_x * 3.5,
            y=moved.y + inward_y * 3.5,
            z=moved.z)
        print("Hesitant path repaired: %.2fm toward lane centre" %
              horizontal_distance(moved, geometry["finish"]))
    print("Hesitant kerb placement: lane-centre distance %.2fm -> %.2fm (lane width %.2fm)" %
          (distance, target_distance, road_wp.lane_width))
    return geometry


def move_spawn_near_road_edge(world, geometry, target_centre_distance=2.8, max_shift=2.0):
    """Bring a roadside spawn nearer the driving lane without entering its centre.

    Only used for waiting/hesitant. Driving waypoint gives a road-centre reference;
    no assumed road_right sign, which differs by map/lane orientation.
    """
    start = geometry.get("start")
    if start is None:
        return geometry
    road_wp = world.get_map().get_waypoint(
        start, project_to_road=True, lane_type=carla.LaneType.Driving)
    if road_wp is None:
        return geometry
    road = road_wp.transform.location
    dx, dy = road.x - start.x, road.y - start.y
    distance = math.hypot(dx, dy)
    if distance <= target_centre_distance or distance > 12.0:
        return geometry
    shift = min(max_shift, distance - target_centre_distance)
    moved = carla.Location(x=start.x + dx / distance * shift,
                           y=start.y + dy / distance * shift, z=start.z)
    geometry["start"] = moved
    if "center" in geometry:
        geometry["center"] = moved
    print("Road-edge adjustment: %.2fm toward driving lane (centre distance %.2fm -> %.2fm)" %
          (shift, distance, distance - shift))
    return geometry


# ============================================================================
# JAYWALK LOCATION
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
# FALLBACK GEOMETRY
# ============================================================================

def find_fallback_geometry(world, vehicle, flip_side=False, extra_offset=0.0):
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)
    right = get_right_vector(vehicle_transform)
    center = add_vector(vehicle_location, forward, 30.0)
    waypoint = nearest_waypoint(world, center)
    if waypoint is not None:
        center.z = waypoint.transform.location.z
    else:
        center.z = vehicle_location.z
    side_offset = 4.5 + extra_offset
    if flip_side:
        start = add_vector(center, right, side_offset)
        finish = add_vector(center, right, -side_offset)
    else:
        start = add_vector(center, right, -side_offset)
        finish = add_vector(center, right, side_offset)
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
# PEDESTRIAN SPAWN
# ============================================================================

_USED_WALKER_BLUEPRINT_IDS = set()

def _walker_attribute_text(blueprint, name):
    """Normalize CARLA ActorAttribute across CARLA Python bindings.

    Some CARLA builds stringify an attribute as
    ActorAttribute(id=age,type=str,value=adult(const)) instead of adult.
    Never infer an adult from an unrecognized value.
    """
    if not blueprint.has_attribute(name):
        return None
    attr = blueprint.get_attribute(name)
    candidates = []
    try:
        candidates.append(attr.as_string())
    except (AttributeError, RuntimeError, ValueError, TypeError):
        pass
    candidates.append(str(attr))
    for value in candidates:
        value = str(value).strip().lower()
        if name == "age":
            if value in ("adult", "child", "teenager"):
                return value
            match = re.search(r"\bvalue\s*=\s*(adult|child|teenager)\s*(?:\(const\))?", value)
            if match:
                return match.group(1)
        elif name == "gender":
            if value in ("male", "female"):
                return value
            match = re.search(r"\bvalue\s*=\s*(male|female)\s*(?:\(const\))?", value)
            if match:
                return match.group(1)
        else:
            return value
    return None


def choose_pedestrian_blueprint(world, spec=None):
    """Only select a walker explicitly marked adult by the CARLA blueprint."""
    walkers = list(world.get_blueprint_library().filter("walker.pedestrian.*"))
    if not walkers:
        raise RuntimeError("CARLA has no walker.pedestrian.* blueprints")

    adults = [bp for bp in walkers if _walker_attribute_text(bp, "age") == "adult"]
    if not adults:
        ages = {}
        for bp in walkers:
            age = _walker_attribute_text(bp, "age") or "<missing>"
            ages[age] = ages.get(age, 0) + 1
        raise RuntimeError(
            "No verified adult pedestrian blueprints found; refusing to spawn a child. "
            "Available walker age values: %s. Check the installed CARLA walker assets."
            % ages)

    gender = getattr(spec, "preferred_gender", None) if spec else None
    if gender:
        matched = [bp for bp in adults if _walker_attribute_text(bp, "gender") == str(gender).lower()]
        if matched:
            adults = matched

    unused = [bp for bp in adults if bp.id not in _USED_WALKER_BLUEPRINT_IDS]
    if not unused:
        _USED_WALKER_BLUEPRINT_IDS.difference_update(bp.id for bp in adults)
        unused = adults
    chosen = random.choice(unused)
    _USED_WALKER_BLUEPRINT_IDS.add(chosen.id)
    print("Verified ADULT pedestrian: %s (age=%s, gender=%s)" % (
        chosen.id, _walker_attribute_text(chosen, "age"),
        _walker_attribute_text(chosen, "gender") or "unknown"))
    return chosen

def ground_pedestrian_location(world, location):
    waypoint = world.get_map().get_waypoint(
        location, project_to_road=True, lane_type=carla.LaneType.Any)
    if waypoint is not None:
        return carla.Location(x=location.x, y=location.y,
                               z=waypoint.transform.location.z + 0.05)
    return carla.Location(x=location.x, y=location.y, z=location.z)

def spawn_pedestrian(world, actors, geometry, spec=None):
    pedestrian_bp = choose_pedestrian_blueprint(world, spec)
    center = geometry.get("start")
    if center is None:
        center = geometry.get("center")
    cross_wp = geometry.get("waypoint")
    base_z = cross_wp.transform.location.z if cross_wp is not None else center.z
    RAISE_OFFSET = 0.7

    if spec is not None and spec.behavior in ("waiting", "aggressive"):
        start_loc = carla.Location(x=center.x, y=center.y,
                                   z=base_z + RAISE_OFFSET)
        print("%s: Using raw sidewalk location, no road projection." % spec.behavior.capitalize())
    else:
        start_loc = ground_pedestrian_location(world, center)
        if start_loc.z == center.z:
            start_loc.z = base_z + RAISE_OFFSET
        else:
            start_loc.z += RAISE_OFFSET
        print("Other: Projected to ground surface.")

    # Distracted only: begin on the building side of the pavement, not at the kerb.
    if spec is not None and spec.behavior == "distracted":
        edge = geometry.get("finish")
        if edge is not None:
            dx, dy = edge.x - center.x, edge.y - center.y
            length = math.hypot(dx, dy)
            if length > 0.1:
                start_loc.x -= (dx / length) * 1.25
                start_loc.y -= (dy / length) * 1.25
                print("Distracted: spawned 1.25m toward building, will back toward kerb.")

    print("Spawning pedestrian at (%.3f, %.3f, %.3f)" % (start_loc.x, start_loc.y, start_loc.z))
    if "pedestrian_yaw" in geometry:
        yaw = geometry["pedestrian_yaw"]
        print("Using custom pedestrian yaw: %.2f" % yaw)
    else:
        road_forward = geometry.get("road_forward", carla.Vector3D(x=1.0, y=0.0, z=0.0))
        yaw = math.degrees(math.atan2(road_forward.y, road_forward.x))
        print("Using road forward yaw: %.2f" % yaw)
    # Distracted only: face the actual start-to-finish crossing direction.
    # The road-forward vector is perpendicular to this crossing in fallback maps.
    if spec is not None and spec.behavior == "distracted":
        crossing_end = geometry.get("finish")
        if crossing_end is not None:
            dx = crossing_end.x - center.x
            dy = crossing_end.y - center.y
            if math.hypot(dx, dy) > 0.1:
                # Face the opposite side (building/pavement), not the road.
                yaw = (math.degrees(math.atan2(dy, dx)) + 180.0) % 360.0
                print("Distracted facing building/opposite direction: %.2f" % yaw)
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

    if spec is not None and spec.behavior == "waiting":
        try:
            pedestrian.set_simulate_physics(False)
            print("Physics disabled for 'waiting'.")
        except Exception as exc:
            print("WARNING: could not disable physics: %s" % exc)
    else:
        try:
            # Hesitant starts moving immediately; do not freeze its walker actor at spawn.
            pedestrian.set_simulate_physics(spec.behavior == "hesitant")
            print("Physics %s for '%s' at spawn." % (
                "enabled" if spec.behavior == "hesitant" else "disabled", spec.behavior))
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
# DISTRACTED HEAD TILT
# ============================================================================

_BONE_NAMES_DUMPED = False
HEAD_BONE_NAME = "crl_Head__C"
HEAD_PARENT_BONE_NAME = "crl_neck__C"

def _rotation_matrix(rotation):
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
    right = get_right_vector(ped_transform)
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
# PEDESTRIAN CONTROLLER – CLEANED (visually distinct behaviours)
# ============================================================================

class PedestrianController(object):
    ARRIVE_RADIUS_M = 1.0
    MAX_ACCEL_MPS2 = 3.0

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
        self.crossing_started = False

        if start_yaw is not None:
            self.base_yaw = start_yaw
        else:
            dx = self.finish.x - self.start.x
            dy = self.finish.y - self.start.y
            self.base_yaw = math.degrees(math.atan2(dy, dx))

        self.time = 0.0
        self.start_crossing_distance = 25.0

        self._current_speed = 0.0
        self._target_speed = 0.0

        cross_dx = self.finish.x - self.start.x
        cross_dy = self.finish.y - self.start.y
        cross_dist = math.hypot(cross_dx, cross_dy) or 1.0
        self.crossing_direction = carla.Vector3D(
            x=cross_dx / cross_dist, y=cross_dy / cross_dist, z=0.0)

        self.road_forward = geometry.get("road_forward", carla.Vector3D(x=1, y=0, z=0))
        self.road_right   = geometry.get("road_right",   carla.Vector3D(x=0, y=1, z=0))

        self.phase = None
        self.phase_until_tick = 0
        self._progress_fraction = 0.0
        self._current_target = self.finish

        self._agg_pace_done = False

    def _point_along_path(self, fraction):
        fraction = max(0.0, min(1.0, fraction))
        return carla.Location(
            x=self.start.x + (self.finish.x - self.start.x) * fraction,
            y=self.start.y + (self.finish.y - self.start.y) * fraction,
            z=self.start.z)

    def _side_jitter(self, point, lateral_m):
        perp_x = -self.crossing_direction.y
        perp_y =  self.crossing_direction.x
        return carla.Location(
            x=point.x + perp_x * lateral_m,
            y=point.y + perp_y * lateral_m,
            z=point.z)

    def start_behavior(self):
        print()
        print("Pedestrian controller started.")
        print("Behavior: %s" % self.spec.behavior)

        if self.spec.behavior == "waiting":
            print("Pedestrian will idle (physics disabled).")

        elif self.spec.behavior == "committed":
            print("Pedestrian will cross steadily and directly.")
            self.crossing_started = True
            self._enable_physics()
            self._current_speed = 0.0
            self._target_speed = PEDESTRIAN_SPEED_MPS

        elif self.spec.behavior == "hesitant":
            print("Pedestrian will hesitate at the kerb with long pauses.")
            self.crossing_started = True
            self._enable_physics()
            self._current_speed = 0.0
            self.phase = None

        elif self.spec.behavior == "distracted":
            print("Distracted pedestrian steps backward toward the pavement and stops; no road crossing.")

        elif self.spec.behavior == "aggressive":
            print("Pedestrian will pace agitatedly then rush across.")
            self.MAX_ACCEL_MPS2 = 3.5
            self.crossing_started = True
            self._enable_physics()
            self._current_speed = 0.0
            self.phase = "pacing"
            # Keep a brief visible pre-rush pacing segment instead of
            # immediately switching to rushing on the first simulation tick.
            self.phase_until_tick = 14  # 0.70s at 20 Hz
            self._current_target = carla.Location(
                x=self.start.x + self.road_forward.x * 0.9,
                y=self.start.y + self.road_forward.y * 0.9,
                z=self.start.z)
            self._target_speed = 1.5

        elif self.spec.behavior == "jaywalk":
            print("Pedestrian will cross quickly and directly (mid-block).")

        else:
            print("WARNING: behaviour '%s' not implemented." % self.spec.behavior)

        self.started = True

    def _enable_physics(self):
        try:
            self.pedestrian.set_simulate_physics(True)
            print("Physics enabled for %s." % self.spec.behavior)
        except Exception as exc:
            print("WARNING: could not enable physics: %s" % exc)

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
        if not self.started or not self.pedestrian.is_alive:
            return

        self.time += delta_time
        tick_index = int(self.time / delta_time)

        if self.spec.behavior == "waiting":
            return

        if not self.crossing_started:
            dist = horizontal_distance(vehicle_location, self.start)
            if dist > self.start_crossing_distance:
                return
            self.crossing_started = True
            print(("Distracted pedestrian starts backing toward kerb at t=%.2f" if self.spec.behavior == "distracted" else "Pedestrian started crossing at t=%.2f") % self.time)
            self._enable_physics()
            self._current_speed = 0.0

        if self.finished:
            if self.spec.behavior == "distracted":
                self.pedestrian.apply_control(carla.WalkerControl(
                    direction=self.crossing_direction, speed=0.0))
                self._keep_distracted_facing_building()
            else:
                self._idle(delta_time)
            return

        if self.spec.behavior == "distracted":
            self._update_distracted(tick_index)
            return

        if self.spec.behavior == "aggressive":
            self._update_aggressive(tick_index, delta_time)
            return

        if self.spec.behavior == "hesitant":
            self._update_hesitant(tick_index)
            if tick_index % 40 == 0:
                loc = self.pedestrian.get_location()
                print("[HESITANT DEBUG] t=%.1fs phase=%s progress=%.2f speed=%.2f "
                      "position=(%.2f, %.2f) target=(%.2f, %.2f)" % (
                          self.time, self.phase, self._progress_fraction,
                          self._target_speed, loc.x, loc.y,
                          self._current_target.x, self._current_target.y))
        elif self.spec.behavior == "distracted":
            self._update_distracted(tick_index)

        if self.spec.behavior in ("committed", "jaywalk"):
            target = self.finish
            self._target_speed = (PEDESTRIAN_SPEED_MPS if self.spec.behavior == "committed"
                                  else 2.0)
        else:
            target = self._current_target

        current = self.pedestrian.get_location()
        dx = target.x - current.x
        dy = target.y - current.y
        dist_to_target = math.hypot(dx, dy)

        if (self.spec.behavior != "hesitant" and
                horizontal_distance(current, self.finish) < self.ARRIVE_RADIUS_M):
            self.finished = True
            print("Pedestrian completed crossing.")
            self._idle(delta_time)
            return

        if dist_to_target < 0.15:
            self._target_speed = 0.0
            self._ramp_speed(delta_time)
            # Explicitly brake the walker at its target; the old branch returned
            # without applying control and could leave a stale WalkerControl.
            self.pedestrian.apply_control(carla.WalkerControl(
                direction=self.crossing_direction, speed=0.0))
            if self.spec.behavior == "distracted":
                self._keep_distracted_facing_building()
            return

        self._ramp_speed(delta_time)
        direction = carla.Vector3D(x=dx / dist_to_target, y=dy / dist_to_target, z=0.0)
        self.pedestrian.apply_control(carla.WalkerControl(
            direction=direction, speed=self._current_speed))
        if self.spec.behavior == "distracted":
            self._keep_distracted_facing_building()

    def _keep_distracted_facing_building(self):
        # WalkerControl turns the body toward its movement vector every tick.
        # Lock only the distracted walker's visual yaw opposite to the crossing.
        # Preserve its current location, speed command and pitch/roll.
        try:
            transform = self.pedestrian.get_transform()
            desired_yaw = (math.degrees(math.atan2(
                self.crossing_direction.y, self.crossing_direction.x)) + 180.0) % 360.0
            transform.rotation.yaw = desired_yaw
            self.pedestrian.set_transform(transform)
        except RuntimeError as exc:
            print("Distracted facing lock failed: %s" % exc)

    # Hesitant takes visible short steps near the kerb, then pauses.
    # Do not change the other pedestrian behaviours.
    MAX_HESITANT_PROGRESS = 0.08  # Keep tentative motion close to the kerb

    def _update_hesitant(self, tick_index):
        # Delay the first step until the ego camera is approaching the kerb.
        # The walker stays at the kerb while distant, then performs multiple
        # visible step/pause cycles during the camera's approach.
        if self.time < 5.0:
            self._target_speed = 0.0
            return
        current = self.pedestrian.get_location()
        distance_to_target = horizontal_distance(current, self._current_target)

        if self.phase is None:
            self.phase = "stepping"
            self._progress_fraction = min(self.MAX_HESITANT_PROGRESS, 0.04)
            self._current_target = self._point_along_path(self._progress_fraction)
        # Hesitant only: never target farther than 0.28m inward from the kerb.
        step_dx = self._current_target.x - self.start.x
        step_dy = self._current_target.y - self.start.y
        step_len = math.hypot(step_dx, step_dy)
        if step_len > 0.28:
            self._current_target = carla.Location(
                x=self.start.x + step_dx * 0.28 / step_len,
                y=self.start.y + step_dy * 0.28 / step_len,
                z=self._current_target.z)
            self._target_speed = 0.85
            return

        if self.phase == "stepping":
            # Finish a real step before starting a pause. Previously a short
            # timer ended the step before the walker had time to move visibly.
            if distance_to_target <= 0.18:
                self.phase = "paused"
                self._target_speed = 0.0
                self.phase_until_tick = tick_index + random.randint(12, 20)
            else:
                self._target_speed = 0.85
            return

        # During a pause, keep a stationary control until the timer expires.
        if tick_index < self.phase_until_tick:
            self._target_speed = 0.0
            return

        if self._progress_fraction >= self.MAX_HESITANT_PROGRESS:
            # Stay at the roadside after the last hesitant step.
            self._target_speed = 0.0
            return

        self._progress_fraction = min(self.MAX_HESITANT_PROGRESS,
                                      self._progress_fraction + 0.02)
        self._current_target = self._point_along_path(self._progress_fraction)
        # Hesitant only: never target farther than 0.28m inward from the kerb.
        step_dx = self._current_target.x - self.start.x
        step_dy = self._current_target.y - self.start.y
        step_len = math.hypot(step_dx, step_dy)
        if step_len > 0.28:
            self._current_target = carla.Location(
                x=self.start.x + step_dx * 0.28 / step_len,
                y=self.start.y + step_dy * 0.28 / step_len,
                z=self._current_target.z)
        self._target_speed = 0.85
        self.phase = "stepping"

    def _update_distracted(self, tick_index):
        # Backward walk from building-side pavement toward the original kerb.
        # Keep body yaw toward the building; stop before entering the road.
        kerb = self._distracted_kerb_target if hasattr(self, "_distracted_kerb_target") else None
        if kerb is None:
            # The scenario's original start is the pavement/road edge.
            # self.start is the actual spawn location (1.25m toward building).
            kerb = carla.Location(
                x=self.start.x + self.crossing_direction.x * 1.25,
                y=self.start.y + self.crossing_direction.y * 1.25,
                z=self.start.z)
            self._distracted_kerb_target = kerb
        current = self.pedestrian.get_location()
        dx, dy = kerb.x - current.x, kerb.y - current.y
        remaining = math.hypot(dx, dy)
        forward = self.crossing_direction
        if remaining <= 0.18:
            self.finished = True
            self.phase = "stopped_at_kerb"
            self._current_speed = self._target_speed = 0.0
            self.pedestrian.apply_control(carla.WalkerControl(direction=forward, speed=0.0))
            self._keep_distracted_facing_building()
            return
        self.phase = "backing_toward_kerb"
        self._target_speed = 0.75
        self._ramp_speed(0.05)
        # Move toward the road but cap the step so the actor stops at the kerb.
        speed = min(self._current_speed, max(0.0, (remaining - 0.12) / 0.05))
        self.pedestrian.apply_control(carla.WalkerControl(direction=forward, speed=speed))
        self._keep_distracted_facing_building()

    def _update_aggressive(self, tick_index, delta_time):
        # Agitated forward/back pacing on the same sidewalk. Never aim at
        # self.finish or steer laterally toward the road.
        current = self.pedestrian.get_location()
        if tick_index >= self.phase_until_tick or self.phase != "pacing":
            self.phase = "pacing"
            self.phase_until_tick = tick_index + random.randint(12, 24)
            self._agg_pace_sign = -getattr(self, "_agg_pace_sign", -1)
            pace = 0.85 * self._agg_pace_sign
            self._current_target = carla.Location(
                x=self.start.x + self.road_forward.x * pace,
                y=self.start.y + self.road_forward.y * pace,
                z=self.start.z)
            self._target_speed = random.uniform(1.3, 2.1)

        dx = self._current_target.x - current.x
        dy = self._current_target.y - current.y
        distance = math.hypot(dx, dy)
        if distance <= 0.15:
            self._idle(delta_time)
            return
        self._ramp_speed(delta_time)
        direction = normalize_2d(carla.Vector3D(x=dx, y=dy, z=0.0))
        self.pedestrian.apply_control(carla.WalkerControl(
            direction=direction, speed=min(self._current_speed, distance / max(delta_time, 0.01))))


# ============================================================================
# WEB STREAMING SERVER
# ============================================================================

try:
    from PIL import Image as _PILImage
    from PIL import ImageDraw as _PILDraw
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

class _SharedDashboardState(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._jpeg_bytes = None
        self._ped_head_overlay = None
        self._log = deque(maxlen=WEB_STREAM_LOG_MAXLEN)
        self._status = {
            "phase": "idle",
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

    def set_pedestrian_head_overlay(self, point, prediction):
        with self._lock:
            if point is None:
                self._ped_head_overlay = None
            else:
                if prediction is None:
                    label = "Analyzing..."
                else:
                    state = prediction.get("mental_state", -1)
                    conf = float(prediction.get("confidence", 0.0))
                    label = "%s  %.0f%%" % (LABELS.get(state, "Unknown"), conf * 100)
                self._ped_head_overlay = (float(point[0]), float(point[1]), label)

    def set_frame_from_carla_image(self, image):
        if not _PIL_AVAILABLE:
            return
        try:
            arr = np.frombuffer(image.raw_data, dtype=np.uint8)
            arr = arr.reshape((image.height, image.width, 4))
            rgb = arr[:, :, [2, 1, 0]]
            pil_img = _PILImage.fromarray(rgb)
            if pil_img.width > WEB_STREAM_MAX_WIDTH:
                scale = WEB_STREAM_MAX_WIDTH / float(pil_img.width)
                new_size = (WEB_STREAM_MAX_WIDTH, max(1, int(pil_img.height * scale)))
                pil_img = pil_img.resize(new_size)
            with self._lock:
                overlay = self._ped_head_overlay
            if overlay is not None:
                u, v, label = overlay
                scale_x = pil_img.width / float(image.width)
                scale_y = pil_img.height / float(image.height)
                x = int(u * scale_x)
                y = int(v * scale_y) - 24
                if 0 <= x < pil_img.width and -25 <= y < pil_img.height:
                    draw = _PILDraw.Draw(pil_img)
                    bounds = draw.textbbox((0, 0), label) if hasattr(draw, "textbbox") else (0, 0, len(label) * 7, 14)
                    w = bounds[2] - bounds[0] + 12
                    h = bounds[3] - bounds[1] + 10
                    x = max(0, min(x - w // 2, pil_img.width - w))
                    y = max(0, y - h)
                    draw.rectangle((x, y, x + w, y + h), fill=(15, 20, 30))
                    draw.text((x + 6, y + 4), label, fill=(255, 255, 255))
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=WEB_STREAM_JPEG_QUALITY)
            with self._lock:
                self._jpeg_bytes = buf.getvalue()
        except Exception:
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
                pass
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def log_message(self, format, *args):
        pass

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

class PoseCameraBuffer(object):
    def __init__(self):
        self.last_image = None
        self.frame = None
    def callback(self, image):
        self.last_image = image
        self.frame = image.frame

def attach_pose_tracking_camera(world, actors, vehicle, behavior=None):
    bp = world.get_blueprint_library().find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", str(CAMERA_WIDTH))
    bp.set_attribute("image_size_y", str(CAMERA_HEIGHT))
    # Narrower FOV only for Jaywalk pose detection.
    pose_fov = 65.0 if behavior in ("jaywalk", "aggressive") else CAMERA_FOV
    bp.set_attribute("fov", str(pose_fov))
    transform = carla.Transform(
        carla.Location(x=1.6, y=0.0, z=1.45),
        carla.Rotation(pitch=-2.0, yaw=0.0, roll=0.0))
    pose_camera = world.spawn_actor(bp, transform, attach_to=vehicle)
    actors.add(pose_camera)
    return pose_camera

CAMERA_LOCAL_X = 1.6
CAMERA_LOCAL_Z = 1.45
CAMERA_MAX_YAW_DEG = 180.0
CAMERA_MAX_PITCH_DEG = 45.0

def aim_camera_yaw(vehicle, target_location, distance_m=None):
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

def position_spectator(world, vehicle, pedestrian=None):
    spectator = world.get_spectator()
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    forward = get_forward_vector(vehicle_transform)
    camera_location = carla.Location(
        x=vehicle_location.x + forward.x * 1.2,
        y=vehicle_location.y + forward.y * 1.2,
        z=vehicle_location.z + 1.55)
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
    # Match the actual camera FOV so projected bounding boxes align with the image.
    camera_fov = float(camera.attributes.get("fov", CAMERA_FOV))
    K = build_camera_matrix(CAMERA_WIDTH, CAMERA_HEIGHT, camera_fov)
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

def yolo_pedestrian_crop(image, previous_track_id=None):
    if image is None:
        return None, None, None, 0
    if not _PIL_AVAILABLE:
        raise RuntimeError("Pillow required for YOLO JPEG encoding")
    arr = np.frombuffer(image.raw_data, dtype=np.uint8).reshape((image.height, image.width, 4))
    rgb = np.ascontiguousarray(arr[:, :, [2, 1, 0]])
    buf = io.BytesIO()
    _PILImage.fromarray(rgb).save(buf, format="JPEG", quality=85)
    req = urllib.request.Request(YOLO_SERVER_URL, data=buf.getvalue(),
                                 headers={"Content-Type": "image/jpeg"}, method="POST")
    with urllib.request.urlopen(req, timeout=4.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        raise RuntimeError(payload["error"])
    detections = payload.get("detections", [])
    candidates = []
    for det in detections:
        if int(det.get("class_id", 0)) != 0:
            continue
        box = det.get("bbox", det.get("box"))
        if not box or len(box) != 4:
            continue
        x0,y0,x1,y1 = [int(v) for v in box]
        x0=max(0,x0);y0=max(0,y0);x1=min(image.width,x1);y1=min(image.height,y1)
        if x1-x0 < MIN_CROP_SIZE or y1-y0 < MIN_CROP_SIZE:
            continue
        track_id = det.get("track_id", det.get("id"))
        score = float(det.get("confidence", 0.0))
        candidates.append((track_id,score,x0,y0,x1,y1))
    if not candidates:
        return None, None, None, 0
    candidates.sort(key=lambda d: (d[0] == previous_track_id and previous_track_id is not None,
                                   d[1]), reverse=True)
    track_id,score,x0,y0,x1,y1 = candidates[0]
    pad_x=int((x1-x0)*CROP_PADDING);pad_y=int((y1-y0)*CROP_PADDING)
    crop=rgb[max(0,y0-pad_y):min(image.height,y1+pad_y),
             max(0,x0-pad_x):min(image.width,x1+pad_x)]
    return crop, track_id, score, len(candidates)


class LiveML(object):
    MIN_VALID_FRAMES_FOR_PREDICTION = 6

    def __init__(self):
        self.pose = PoseExtractor(POSE_SERVER_URL, timeout=3.0)
        self.tracker = PedestrianTracker(ped_id=-1)
        self.features = []
        self.last_prediction = None
        self.last_prediction_frame = -1
        self.pose_ok = 0
        self.pose_fail = 0
        self._insufficient_data_warned = False
        self.last_crop_wh = None
        self.crop_height_history = deque(maxlen=WINDOW_SIZE)

    def process(self, crop, frame_index, context):
        landmarks = None
        if crop is not None:
            self.last_crop_wh = (crop.shape[1], crop.shape[0])
            self.crop_height_history.append(crop.shape[0])
            landmarks = self.pose.extract(crop)
        else:
            self.last_crop_wh = None

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

        valid_in_window = sum(1 for lm in self.tracker.landmark_window if lm is not None)

        if len(self.features) == WINDOW_SIZE and landmarks is not None:
            if valid_in_window >= self.MIN_VALID_FRAMES_FOR_PREDICTION:
                try:
                    result = ensemble_predict(np.stack(self.features, axis=0))
                    self.last_prediction = result
                    self.last_prediction_frame = frame_index
                except Exception as exc:
                    print("\nENSEMBLE ERROR: %s" % exc)
            elif not self._insufficient_data_warned:
                print("\n[t=%5.1fs] Skipping prediction -- only %d/%d frames in the "
                      "window have real pose data (need >= %d). Waiting for more "
                      "valid detections before trusting a classification." % (
                          frame_index * FIXED_DELTA_SECONDS, valid_in_window, WINDOW_SIZE,
                          self.MIN_VALID_FRAMES_FOR_PREDICTION))
                self._insufficient_data_warned = True

        return (feature_vector, landmarks)

    def crop_size_str(self):
        if self.last_crop_wh is None:
            latest = "none"
        else:
            latest = "%dx%d" % self.last_crop_wh
        if self.crop_height_history:
            mean_h = sum(self.crop_height_history) / len(self.crop_height_history)
            return "%s (mean h=%.0fpx over last %d crops)" % (
                latest, mean_h, len(self.crop_height_history))
        return latest

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
    print("[t=%5.1fs] frame=%4d distance=%6.2fm GT=%-10s ML=%-10s conf=%s pose=%d/%d buffer=%d/30 crop=%s" % (
        elapsed, frame_index, d, spec.behavior, prediction_text, confidence_text,
        live_ml.pose_ok, (live_ml.pose_ok + live_ml.pose_fail), len(live_ml.features),
        live_ml.crop_size_str()))
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
        clear_stale_actors(world)
        make_weather(world, spec)

        geometry = None
        use_fallback_only = spec.behavior in ("distracted",)

        if spec.behavior in ("committed", "hesitant"):
            warmup_distance_m = (spec.ego_cruise_kmh / 3.6) * VEHICLE_ONLY_SECONDS
            skip_count = 0 if spec.behavior == "committed" else 2
            print("Looking for a real crosswalk to position vehicle "
                  "(skip_count=%d)..." % skip_count)
            geometry = find_verified_crosswalk_for_vehicle(
                world, approach_distance_m=TARGET_DISTANCE_M + warmup_distance_m,
                skip_count=skip_count)

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
            geometry = None
        else:
            vehicle = spawn_vehicle(world, actors, seed)

        world.tick()

        camera_buffer = CameraBuffer()
        camera = attach_camera(world, actors, vehicle)
        camera.listen(camera_buffer.callback)

        pose_camera_buffer = PoseCameraBuffer()
        pose_camera = attach_pose_tracking_camera(world, actors, vehicle, spec.behavior)
        pose_camera.listen(pose_camera_buffer.callback)

        SHARED.update_status(phase="running", message="Vehicle driving toward pedestrian.")
        SHARED.log_event("Vehicle spawned, camera attached.")

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

        if spec.behavior == "waiting":
            print("Finding a waiting location on the RIGHT sidewalk...")
            geometry = find_waiting_location(world, vehicle, prefer_right=True)
            if geometry is None:
                print("WARNING: Could not find right sidewalk, using fallback geometry.")
                geometry = find_fallback_geometry(world, vehicle, flip_side=True, extra_offset=3.0)
            if geometry is not None:
                geometry = move_spawn_near_road_edge(world, geometry)
        elif spec.behavior == "aggressive":
            print("Aggressive: pacing on the RIGHT roadside; will not cross.")
            geometry = find_aggressive_right_side_geometry(world, vehicle)
        elif spec.behavior == "jaywalk":
            print("Finding a jaywalk location (away from crosswalks)...")
            geometry = find_jaywalk_geometry(world, vehicle)
            if geometry is None:
                print("WARNING: No suitable jaywalk location, using fallback.")
                geometry = find_fallback_geometry(world, vehicle)
            else:
                road_forward = geometry["road_forward"]
                reposition_loc = add_vector(geometry["center"], road_forward, -TARGET_DISTANCE_M)
                reposition_wp = nearest_waypoint(world, reposition_loc)
                if reposition_wp is not None:
                    current_z = vehicle.get_transform().location.z
                    new_transform = carla.Transform(
                        carla.Location(x=reposition_wp.transform.location.x,
                                       y=reposition_wp.transform.location.y,
                                       z=current_z),
                        reposition_wp.transform.rotation)
                    vehicle.set_transform(new_transform)
                    try:
                        vehicle.set_target_velocity(carla.Vector3D(x=0.0, y=0.0, z=0.0))
                        vehicle.set_target_angular_velocity(carla.Vector3D(x=0.0, y=0.0, z=0.0))
                    except Exception as exc:
                        print("WARNING: could not zero vehicle velocity after "
                              "repositioning for jaywalk: %s" % exc)
                    world.tick()
                    print("Repositioned vehicle to ~%.1fm from the jaywalk "
                          "crossing point." % TARGET_DISTANCE_M)
                else:
                    print("WARNING: could not find a clean waypoint to "
                          "reposition the vehicle for jaywalk.")
        elif spec.behavior == "hesitant":
            if geometry is None:
                print("Finding a real crosswalk near which the hesitant pedestrian will linger...")
                geometry = find_crosswalk_ahead_of_vehicle(world, vehicle, max_distance=200.0)
            if geometry is None:
                print("WARNING: Still no real crosswalk found ahead of THIS vehicle -- "
                      "using generic fallback geometry.")
                geometry = find_fallback_geometry(world, vehicle)
            if geometry is not None:
                geometry = place_hesitant_at_kerb(world, geometry)
        elif use_fallback_only:
            print("Forcing fallback geometry for behaviour: %s" % spec.behavior)
            flip = (spec.behavior == "distracted")
            geometry = find_fallback_geometry(world, vehicle, flip_side=flip)
        else:
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

        if geometry is None:
            geometry = find_fallback_geometry(world, vehicle)

        print()
        print("Scenario geometry:")
        print("  real_crosswalk: %s" % geometry.get("real_crosswalk", False))
        print("  crossing start: (%.2f, %.2f, %.2f)" % (
            geometry["start"].x, geometry["start"].y, geometry["start"].z))
        print("  crossing end  : (%.2f, %.2f, %.2f)" % (
            geometry["finish"].x, geometry["finish"].y, geometry["finish"].z))
        print("  crossing distance: %.2fm" % horizontal_distance(geometry["start"], geometry["finish"]))

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

        camera_yaw_state = 0.0
        camera_pitch_state = -2.0
        camera.set_transform(carla.Transform(
            carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
            carla.Rotation(pitch=camera_pitch_state, yaw=camera_yaw_state, roll=0.0)))

        pose_cam_yaw = aim_camera_yaw(vehicle, pedestrian.get_location())
        pose_cam_pitch = aim_camera_pitch(vehicle, pedestrian)
        pose_camera.set_transform(carla.Transform(
            carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
            carla.Rotation(pitch=pose_cam_pitch, yaw=pose_cam_yaw, roll=0.0)))

        print("Caching crosswalk data...", flush=True)
        cached_crosswalks = world.get_map().get_crosswalks() if hasattr(world.get_map(), 'get_crosswalks') else []
        print("Cached %d crosswalk point(s)." % len(cached_crosswalks), flush=True)

        agent = RuleBasedAgent()
        current_action = 'MAINTAIN'
        previous_web_action = None
        distance_history = deque(maxlen=15)
        ped_distance_m = None

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
        # Jaywalk evaluation: preserve the observed crossing-phase result,
        # rather than replacing it with a post-crossing prediction.
        jaywalk_recent_predictions = deque(maxlen=20)  # 1s at 20 Hz
        jaywalk_crossing_result = None
        yolo_track_id = None
        yolo_detections = 0
        yolo_failures = 0
        last_processed_image_frame = -1
        closest_distance = float("inf")
        closest_time = 0.0
        last_print = -1.0

        while (frame_index < int(SIMULATION_SECONDS / FIXED_DELTA_SECONDS)
               and not _STOP_REQUESTED.is_set()):
            elapsed = frame_index * FIXED_DELTA_SECONDS

            steer = compute_steer(world, vehicle)
            effective_action = current_action

            if ped_distance_m is not None:
                velocity = vehicle.get_velocity()
                speed_ms = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
                stopping_dist = (speed_ms**2) / (2 * MAX_DECEL_MPS2) + SAFETY_MARGIN_M
                if ped_distance_m < stopping_dist and effective_action != 'STOP':
                    if frame_index % 10 == 0:
                        print(f"[t={elapsed:5.1f}s] SAFETY: forcing STOP (model said {current_action}, "
                              f"distance={ped_distance_m:.2f}m < stopping_dist={stopping_dist:.2f}m)")
                    effective_action = 'STOP'

            drive_vehicle(vehicle, spec.ego_cruise_kmh, action=effective_action, steer=steer)
            controller.update(vehicle.get_location(), FIXED_DELTA_SECONDS)
            if (spec.behavior == "jaywalk" and controller.finished
                    and jaywalk_crossing_result is None
                    and jaywalk_recent_predictions):
                # Fixed pre-completion window; no use of ground-truth labels.
                counts = {}
                for _, sample in jaywalk_recent_predictions:
                    cls = sample.get("mental_state", -1)
                    counts[cls] = counts.get(cls, 0) + 1
                chosen = max(counts, key=lambda cls: counts[cls])
                matches = [sample for _, sample in jaywalk_recent_predictions
                           if sample.get("mental_state", -1) == chosen]
                jaywalk_crossing_result = dict(matches[-1])
                print("Jaywalk crossing-phase evaluation frozen: %s (%d/%d recent frames)" % (
                    LABELS.get(chosen, "?"), len(matches), len(jaywalk_recent_predictions)))

            # Distracted head-bone rotation disabled: keep natural head animation.

            position_spectator(world, vehicle, pedestrian)

            camera.set_transform(carla.Transform(
                carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
                carla.Rotation(pitch=camera_pitch_state, yaw=camera_yaw_state, roll=0.0)))

            if pedestrian.is_alive:
                pose_cam_yaw = aim_camera_yaw(vehicle, pedestrian.get_location())
                pose_cam_pitch = aim_camera_pitch(vehicle, pedestrian)
                pose_camera.set_transform(carla.Transform(
                    carla.Location(x=CAMERA_LOCAL_X, y=0.0, z=CAMERA_LOCAL_Z),
                    carla.Rotation(pitch=pose_cam_pitch, yaw=pose_cam_yaw, roll=0.0)))

            if pedestrian.is_alive:
                try:
                    ped_loc = pedestrian.get_location()
                    bb = pedestrian.bounding_box
                    head = carla.Location(x=ped_loc.x, y=ped_loc.y,
                                          z=ped_loc.z + bb.location.z + bb.extent.z + 0.25)
                    projected = project_point(head, camera)
                    if projected is not None and projected[2] > 0:
                        SHARED.set_pedestrian_head_overlay(projected, live_ml.last_prediction)
                    else:
                        SHARED.set_pedestrian_head_overlay(None, None)
                except Exception:
                    SHARED.set_pedestrian_head_overlay(None, None)
            world.tick()

            ped_distance_m = None
            if vehicle.is_alive and pedestrian.is_alive:
                d = horizontal_distance(vehicle.get_location(), pedestrian.get_location())
                ped_distance_m = d
                distance_history.append((frame_index, d))
                if d < closest_distance:
                    closest_distance = d
                    closest_time = elapsed

            if frame_index % 4 == 0:
                SHARED.update_status(elapsed_s=elapsed, distance_m=ped_distance_m)

            image = pose_camera_buffer.last_image
            closing_speed_ms = None
            if len(distance_history) >= 2:
                oldest_i, oldest_d = distance_history[0]
                newest_i, newest_d = distance_history[-1]
                dt = (newest_i - oldest_i) * FIXED_DELTA_SECONDS
                if dt > 0:
                    closing_speed_ms = (oldest_d - newest_d) / dt

            if (image is not None and image.frame != last_processed_image_frame
                    and frame_index % YOLO_FRAME_STRIDE == 0):
                last_processed_image_frame = image.frame
                try:
                    crop, detected_id, detection_conf, detected_count = yolo_pedestrian_crop(
                        image, previous_track_id=yolo_track_id)
                    if crop is not None:
                        yolo_detections += 1
                        if yolo_track_id is not None and detected_id != yolo_track_id:
                            live_ml.close()
                            live_ml = LiveML()
                        yolo_track_id = detected_id
                    if crop is None:
                        live_ml.last_prediction = None
                        SHARED.update_status(predicted_state=None, predicted_label=None,
                                             confidence=None, message="Waiting for YOLO detection")
                    context = get_context(world, vehicle, pedestrian, cached_crosswalks, spec=None)
                    feature_vector, landmarks = live_ml.process(crop, frame_index, context)

                    if live_ml.last_prediction_frame == frame_index and live_ml.last_prediction:
                        pred = live_ml.last_prediction
                        mental_state = pred.get('mental_state', -1)
                        confidence = pred.get('confidence', 0.0)
                        if spec.behavior == "jaywalk" and not controller.finished:
                            jaywalk_recent_predictions.append((frame_index, dict(pred)))

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
                        print("  Raw features: speed=%.4f avg_speed=%.4f max_speed=%.4f "
                              "accel=%.4f decel=%.4f speed_var=%.4f step_freq=%.3f "
                              "pause_dur=%.3f hesitation=%.3f move_prob=%.3f" % (
                            feature_vector[0], feature_vector[1], feature_vector[2],
                            feature_vector[3], feature_vector[4], feature_vector[5],
                            feature_vector[6], feature_vector[22], feature_vector[23],
                            feature_vector[27]))
                        print("  Context: crosswalk=%.2f dist_to_curb=%.2f vehicle_dist=%.2f road_width=%.2f" % (
                            feature_vector[33], feature_vector[25], feature_vector[32], feature_vector[34]))

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
                    yolo_failures += 1
                    if yolo_failures <= 5 or yolo_failures % 20 == 0:
                        print("\nYOLO/ML frame error: %s" % exc)

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
        if spec.behavior == "jaywalk" and jaywalk_crossing_result is not None:
            print("Evaluation source : pre-completion crossing-phase vote (last 1.0s)")
        prediction_for_result = (jaywalk_crossing_result if spec.behavior == "jaywalk"
                                 and jaywalk_crossing_result is not None
                                 else live_ml.last_prediction)
        if prediction_for_result:
            prediction = prediction_for_result
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
        print("YOLO detections     : %d" % yolo_detections)
        print("YOLO/ML errors      : %d" % yolo_failures)
        print("YOLO URL            : %s" % YOLO_SERVER_URL)
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
        stop_reason = ("External stop request (SIGTERM/UI Stop)." if stopped_early
                       else "Configured duration reached (%.1f simulation seconds)." % SIMULATION_SECONDS)
        print("SCENARIO END REASON: %s" % stop_reason, flush=True)
        SHARED.update_status(
            phase="finished",
            finished=True,
            action=final_effective_action,
            correct=correct,
            closest_approach_m=(closest_distance if closest_distance != float("inf") else None),
            message=stop_reason,
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
        SHARED.set_pedestrian_head_overlay(None, None)
        actors.cleanup()
        try:
            world.apply_settings(original_settings)
        except Exception as exc:
            print("WARNING: could not restore world settings: %s" % exc)
        print("CARLA scenario finished.")


# ============================================================================
# VEHICLE CONTROL
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
    target = max(0.0, target_kmh / 3.6 * ACTION_SPEED_FACTOR.get(action, 1.0))
    v = vehicle.get_velocity()
    speed = math.hypot(v.x, v.y)
    error = target - speed
    control = carla.VehicleControl()
    control.steer = max(-1.0, min(1.0, steer))
    if action == 'STOP':
        control.throttle = 0.0
        control.brake = 1.0
    elif error > 0.15:
        control.throttle = max(0.12, min(0.65, 0.16 + 0.10 * error))
        control.brake = 0.0
    elif error < -0.45:
        control.throttle = 0.0
        control.brake = min(0.45, 0.08 * abs(error))
    else:
        control.throttle = 0.08 if error >= 0 else 0.0
        control.brake = 0.0
    vehicle.apply_control(control)
    return target


# ============================================================================
# ARGUMENTS & MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=list_scenario_ids())
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--duration", type=float, default=60.0,
                        help="Scenario duration in simulation seconds (default: 60)")
    parser.add_argument("--host", default=CARLA_HOST)
    parser.add_argument("--port", type=int, default=CARLA_PORT)
    return parser.parse_args()

def main():
    global SIMULATION_SECONDS
    args = parse_args()
    if args.duration <= 0:
        raise ValueError("--duration must be positive")
    SIMULATION_SECONDS = args.duration
    _STOP_REQUESTED.clear()
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