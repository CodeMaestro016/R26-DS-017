# ============================================================
# CARLA TRAFFIC-SIGN MANAGER - roadside image signs
# ============================================================

import math
import os
import random
import threading

import carla
import cv2
import numpy as np

from carla_app.config.traffic_sign_config import (
    SIGN_IMAGE_DIR,
    SIGN_FIRST_DISTANCE_METERS,
    SIGN_SPACING_METERS,
    SIGN_SIDE_OFFSET_METERS,
    SIGN_HEIGHT_METERS,
    SIGN_SIZE_METERS,
    SIGN_POLE_WIDTH_METERS,
    SIGN_ORDER,
    list_sign_files,
)
from carla_app.config import traffic_sign_config as _sign_config

SIGN_RANDOM_ORDER = getattr(_sign_config, "SIGN_RANDOM_ORDER", False)
SIGN_SIDE = getattr(_sign_config, "SIGN_SIDE", "right")
SIGN_SPACING_JITTER_METERS = getattr(_sign_config, "SIGN_SPACING_JITTER_METERS", 0.0)
SIGN_RANDOM_SEED = getattr(_sign_config, "SIGN_RANDOM_SEED", None)
SIGN_LAYOUT_MODE = getattr(_sign_config, "SIGN_LAYOUT_MODE", "random")


# Max image size kept in memory per sign (pixels).
SIGN_TEXTURE_SIZE = 384

# Pixels this close to the corner colour count as background.
BACKGROUND_TOLERANCE = 30

# Do not draw signs further than this (metres, straight line).
MAX_DRAW_DISTANCE = 120.0

# Only draw signs on the car's current stretch of the route:
# from this far ahead (along the road) ...
VISIBLE_AHEAD_METERS = 70.0
# ... to this far behind (so the chase camera still sees a
# sign the car has just passed).
VISIBLE_BEHIND_METERS = 15.0

# Do not draw signs closer than this to the camera plane (metres).
MIN_DRAW_DEPTH = 1.0

POLE_COLOR_BGR = (110, 110, 115)


# ============================================================
# IMAGE LOADING
# ============================================================

def _remove_plain_background(bgr):
    """
    Make the plain background transparent.

    Starts from the image border and removes connected pixels
    that are close to the border colour (flood fill), so white
    parts INSIDE the sign are kept.
    """
    h, w = bgr.shape[:2]
    corners = np.array([bgr[0, 0], bgr[0, w - 1], bgr[h - 1, 0], bgr[h - 1, w - 1]], dtype=np.int32)
    tol = (BACKGROUND_TOLERANCE,) * 3

    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)

    # Flood from points all around the border.
    step = max(1, min(h, w) // 40)
    seeds = (
        [(x, 0) for x in range(0, w, step)] + [(x, h - 1) for x in range(0, w, step)] +
        [(0, y) for y in range(0, h, step)] + [(w - 1, y) for y in range(0, h, step)]
    )
    background_color = np.median(corners, axis=0)
    for x, y in seeds:
        if mask[y + 1, x + 1]:
            continue
        if np.abs(bgr[y, x].astype(np.int32) - background_color).max() > BACKGROUND_TOLERANCE:
            continue
        cv2.floodFill(bgr, mask, (x, y), 0, tol, tol, flags)

    alpha = 255 - mask[1:-1, 1:-1]

    # Keep only the sign itself (the largest solid shape), so
    # specks left over from a textured background disappear.
    count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)
    if count > 2:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alpha = np.where(labels == largest, 255, 0).astype(np.uint8)

    # Trim the thin light edge left by the background, then
    # smooth the edge so it does not look jagged.
    k = max(3, (min(h, w) // 250) | 1)
    alpha = cv2.erode(alpha, np.ones((k, k), np.uint8))
    alpha = cv2.GaussianBlur(alpha, (k, k), 0)
    return np.dstack([bgr, alpha])


def _crop_to_alpha(bgra, threshold=20):
    alpha = bgra[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0:
        return bgra
    return bgra[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def load_sign_image(path):
    """
    Load one sign as a BGRA image with a transparent background,
    cropped to the sign and resized to SIGN_TEXTURE_SIZE.
    """
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if image.shape[2] == 4:
        bgra = image
        # Treat "transparent" images that are actually opaque
        # (alpha 255 everywhere) like images without alpha.
        if bgra[:, :, 3].min() > 240:
            bgra = _remove_plain_background(np.ascontiguousarray(bgra[:, :, :3]))
    else:
        bgra = _remove_plain_background(np.ascontiguousarray(image[:, :, :3]))

    bgra = _crop_to_alpha(bgra)

    h, w = bgra.shape[:2]
    scale = SIGN_TEXTURE_SIZE / float(max(h, w))
    if scale < 1.0:
        bgra = cv2.resize(bgra, (max(1, int(w * scale)), max(1, int(h * scale))),
                          interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(bgra)


# ============================================================
# CAMERA PROJECTION
# ============================================================

def _camera_intrinsics(width, height, fov_deg):
    focal = width / (2.0 * math.tan(math.radians(fov_deg) / 2.0))
    return focal, width / 2.0, height / 2.0


def _world_to_image(points_world, world_to_camera, focal, cx, cy):
    """
    points_world: (N, 3) array.
    Returns (pixels (N, 2), depth (N,)).
    CARLA camera axes: x forward, y right, z up.
    """
    ones = np.ones((points_world.shape[0], 1))
    homogeneous = np.hstack([points_world, ones])
    cam = homogeneous.dot(world_to_camera.T)
    depth = cam[:, 0]
    safe = np.where(np.abs(depth) < 1e-6, 1e-6, depth)
    u = cx + focal * cam[:, 1] / safe
    v = cy - focal * cam[:, 2] / safe
    return np.stack([u, v], axis=1), depth


def _blend_bgra(frame, bgra_patch, x0, y0):
    """Alpha-blend a BGRA patch onto a BGR frame at (x0, y0)."""
    h, w = bgra_patch.shape[:2]
    fh, fw = frame.shape[:2]
    x1, y1 = max(0, x0), max(0, y0)
    x2, y2 = min(fw, x0 + w), min(fh, y0 + h)
    if x1 >= x2 or y1 >= y2:
        return
    patch = bgra_patch[y1 - y0:y2 - y0, x1 - x0:x2 - x0]
    alpha = patch[:, :, 3:4].astype(np.float32) / 255.0
    region = frame[y1:y2, x1:x2].astype(np.float32)
    frame[y1:y2, x1:x2] = (alpha * patch[:, :, :3] + (1.0 - alpha) * region).astype(np.uint8)


# ============================================================
# BALANCED RANDOM SIDES
# ============================================================

def _balanced_sides(count, rng, max_run=2):
    """
    Random left/right sides with (almost) equal numbers on each
    side and never more than `max_run` in a row on one side.
    """
    sides = (["left", "right"] * ((count + 1) // 2))[:count]
    for _ in range(200):
        rng.shuffle(sides)
        run, longest = 1, 1
        for i in range(1, count):
            run = run + 1 if sides[i] == sides[i - 1] else 1
            longest = max(longest, run)
        if longest <= max_run:
            return sides
    # Fallback: alternate, random first side.
    first = rng.choice(("left", "right"))
    other = "right" if first == "left" else "left"
    return [first if i % 2 == 0 else other for i in range(count)]


# ============================================================
# TRAFFIC SIGN MANAGER
# ============================================================

class TrafficSignManager:
    """
    Keeps the roadside signs and draws them into camera images.
    """

    def __init__(self, world):
        self.world = world
        self.signs = []
        self._lock = threading.Lock()
        self._images = None

        # How signs look in the current weather (see set_appearance).
        self.brightness = 1.0
        self.headlight_glow = False
        self.blur = 0

        # The route the signs are placed along (the driver follows
        # the same route), and how far along it the car is.
        self.route = []              # [(distance_m, waypoint), ...]
        self._route_xy = None        # (N, 2) array of route points
        self._route_dist = None      # (N,) distance along route
        self._progress_index = 0

    # --------------------------------------------------------
    # WEATHER APPEARANCE
    # --------------------------------------------------------

    def set_appearance(self, brightness=1.0, headlight_glow=False, blur=0):
        """
        Make the drawn signs match the CARLA weather.

        brightness      1.0 = daylight, lower = darker (night).
        headlight_glow  signs light up in the headlights when the
                        car is close, like real reflective signs.
        blur            softness in pixels (rain on the lens).
        """
        self.brightness = float(brightness)
        self.headlight_glow = bool(headlight_glow)
        self.blur = int(blur)

    def _sign_brightness(self, distance):
        if not self.headlight_glow:
            return self.brightness
        # Full glow within ~6 m, fading out by ~35 m.
        glow = min(1.0, max(0.0, 1.0 - (distance - 6.0) / 29.0))
        return self.brightness + (1.0 - self.brightness) * glow

    # --------------------------------------------------------
    # IMAGES
    # --------------------------------------------------------

    def _load_images(self, vehicle_id=None):
        """Sign images in the order of this vehicle's layout.
        Each image file is read from disk only once."""
        if self._images is None:
            self._images = {}

        images = []
        for name in list_sign_files(vehicle_id):
            if name not in self._images:
                path = os.path.join(SIGN_IMAGE_DIR, name)
                bgra = load_sign_image(path)
                if bgra is None:
                    print("[TrafficSignManager] Cannot read sign image: {}".format(name))
                    continue
                self._images[name] = bgra
            images.append((name, self._images[name]))

        print("[TrafficSignManager] {} sign images for {} from {}".format(
            len(images), vehicle_id or "default layout", SIGN_IMAGE_DIR))
        return images

    # --------------------------------------------------------
    # ROUTE
    # --------------------------------------------------------

    def _route_waypoints(self, start_transform, total_length, step=2.0):
        """
        Waypoints along the road ahead of the car, choosing the
        straightest road at junctions (same rule as SimpleDriver).
        Returns a list of (distance_from_start, waypoint).
        """
        carla_map = self.world.get_map()
        waypoint = carla_map.get_waypoint(
            start_transform.location,
            project_to_road=True,
            lane_type=carla.LaneType.Driving,
        )
        if waypoint is None:
            return []

        route = [(0.0, waypoint)]
        travelled = 0.0
        while travelled < total_length:
            options = waypoint.next(step)
            if not options:
                break
            yaw = waypoint.transform.rotation.yaw
            waypoint = min(
                options,
                key=lambda wp: abs((wp.transform.rotation.yaw - yaw + 180.0) % 360.0 - 180.0),
            )
            travelled += step
            route.append((travelled, waypoint))
        return route

    # --------------------------------------------------------
    # PLACE SIGNS
    # --------------------------------------------------------

    def create_route_signs(self, vehicle, vehicle_id=None):
        """
        Place every sign image beside the road along the route
        ahead of the vehicle, in that vehicle's own sign order.
        Returns the list of placed signs.
        """
        images = list(self._load_images(vehicle_id))
        if not images:
            print("[TrafficSignManager] No sign images found in {}".format(SIGN_IMAGE_DIR))
            return []

        # Random layout: order, side and gaps.
        rng = random.Random(SIGN_RANDOM_SEED)
        fixed_layout = SIGN_LAYOUT_MODE == "fixed"

        if fixed_layout:
            # DEMO_LAYOUT: same order, sides and spacing every Start.
            sides = [_sign_config.demo_side(name, vehicle_id) for name, _ in images]
            jitter_meters = 0.0
            print("[TrafficSignManager] Fixed demo layout for {} ({} signs).".format(
                vehicle_id or "default", len(images)))
        else:
            if SIGN_RANDOM_ORDER and not SIGN_ORDER:
                rng.shuffle(images)
            if SIGN_SIDE == "random":
                sides = _balanced_sides(len(images), rng)
            else:
                sides = [SIGN_SIDE] * len(images)
            jitter_meters = SIGN_SPACING_JITTER_METERS

        targets = []
        position = SIGN_FIRST_DISTANCE_METERS
        for index in range(len(images)):
            if index > 0:
                jitter = rng.uniform(-jitter_meters, jitter_meters) if jitter_meters else 0.0
                position += max(10.0, SIGN_SPACING_METERS + jitter)
            targets.append(position)

        # Route a bit longer than the last sign, so the driver
        # keeps going smoothly after passing it.
        total = targets[-1] + 60.0
        route = self._route_waypoints(vehicle.get_transform(), total)
        if not route:
            print("[TrafficSignManager] Could not find the road ahead of the car.")
            return []

        self._set_route(route)

        placed = []
        route_index = 0
        for index, (name, bgra) in enumerate(images):
            target_distance = targets[index]

            while route_index < len(route) - 1 and (
                route[route_index][0] < target_distance or route[route_index][1].is_junction
            ):
                route_index += 1

            distance, waypoint = route[route_index]
            if distance < target_distance - 1.0 or waypoint.is_junction:
                print("[TrafficSignManager] Road ends before sign {} ({}). "
                      "Placed {} signs.".format(index + 1, name, len(placed)))
                break

            sign = self._make_sign(name, bgra, waypoint, distance, sides[index])
            sign["id"] = len(placed)
            placed.append(sign)

        with self._lock:
            self.signs = placed

        for sign in placed:
            print("[TrafficSignManager] {:>5.0f} m  {:<5}  {}".format(
                sign["distance"], sign["side"], sign["name"]))
        return placed

    # --------------------------------------------------------
    # ROUTE PROGRESS
    # --------------------------------------------------------

    def _set_route(self, route):
        with self._lock:
            self.route = route
            self._route_xy = np.array(
                [[wp.transform.location.x, wp.transform.location.y] for _, wp in route]
            )
            self._route_dist = np.array([d for d, _ in route])
            self._progress_index = 0

    def get_route_waypoints(self):
        """Waypoints of the sign route, for the driver to follow."""
        with self._lock:
            return [wp for _, wp in self.route]

    def _route_progress(self, position_xy):
        """
        Distance along the route of the point nearest to
        position_xy. Only searches a little ahead of the last
        known progress, so a route that passes the same place
        twice cannot jump ahead. Returns None if off the route.
        """
        if self._route_xy is None or len(self._route_xy) == 0:
            return None

        start = max(0, self._progress_index - 10)
        end = min(len(self._route_xy), self._progress_index + 40)
        window = self._route_xy[start:end]
        if len(window) == 0:
            return None

        offsets = np.linalg.norm(window - position_xy, axis=1)
        best = int(np.argmin(offsets))
        if offsets[best] > 15.0:
            return None

        index = start + best
        if index > self._progress_index:
            self._progress_index = index
        return float(self._route_dist[index])

    @staticmethod
    def _left_road_width(waypoint):
        """
        Width of the driving lanes to the LEFT of the car's lane
        (usually the opposite-direction lane), so left-side signs
        stand on the far sidewalk, not in the road.
        """
        width = 0.0
        current = waypoint
        own_sign = 1 if getattr(waypoint, "lane_id", 1) >= 0 else -1
        seen = set()

        for _ in range(4):
            try:
                # Lanes driving the other way are reversed, so
                # "outward" (away from our lane) is their RIGHT.
                current_sign = 1 if getattr(current, "lane_id", 1) >= 0 else -1
                if current_sign == own_sign:
                    nxt = current.get_left_lane()
                else:
                    nxt = current.get_right_lane()
            except Exception:
                nxt = None

            if nxt is None or nxt.lane_type != carla.LaneType.Driving:
                break
            key = (getattr(nxt, "road_id", 0), getattr(nxt, "lane_id", 0))
            if key in seen or getattr(nxt, "lane_id", None) == getattr(waypoint, "lane_id", None):
                break
            seen.add(key)

            width += getattr(nxt, "lane_width", 3.5) or 3.5
            current = nxt
        return width

    def _make_sign(self, name, bgra, waypoint, distance, side="right"):
        transform = waypoint.transform
        yaw = math.radians(transform.rotation.yaw)

        forward = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        right = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
        up = np.array([0.0, 0.0, 1.0])

        lane_width = getattr(waypoint, "lane_width", 3.5) or 3.5
        road = np.array([transform.location.x, transform.location.y, transform.location.z])

        if side == "left":
            sideways = -(lane_width / 2.0 + self._left_road_width(waypoint) + SIGN_SIDE_OFFSET_METERS)
        else:
            sideways = lane_width / 2.0 + SIGN_SIDE_OFFSET_METERS
        base = road + right * sideways

        h, w = bgra.shape[:2]
        panel_w = SIGN_SIZE_METERS
        panel_h = SIGN_SIZE_METERS * h / float(w)

        bottom_center = base + up * SIGN_HEIGHT_METERS
        center = bottom_center + up * (panel_h / 2.0)

        # The sign faces oncoming traffic (towards -forward). Seen
        # by the driver, the sign's left edge is on the driver's
        # left (-right) and its right edge on the driver's right.
        corners = np.array([
            center - right * panel_w / 2 + up * panel_h / 2,   # top-left
            center + right * panel_w / 2 + up * panel_h / 2,   # top-right
            center + right * panel_w / 2 - up * panel_h / 2,   # bottom-right
            center - right * panel_w / 2 - up * panel_h / 2,   # bottom-left
        ])

        pole = np.array([base, bottom_center + up * (panel_h * 0.3)])

        return {
            "name": name,
            "image": bgra,
            "corners": corners,
            "pole": pole,
            "center": center,
            "forward": forward,
            "distance": distance,
            "side": side,
        }

    # --------------------------------------------------------
    # DRAW INTO A CAMERA IMAGE
    # --------------------------------------------------------

    def draw_signs(self, frame, camera_transform, fov_deg):
        """
        Draw all visible signs into a BGR frame (modified in place).
        camera_transform is the carla.Transform of the camera when
        the image was taken (image.transform in the callback).
        """
        with self._lock:
            signs = list(self.signs)
        if not signs:
            return frame

        height, width = frame.shape[:2]
        focal, cx, cy = _camera_intrinsics(width, height, fov_deg)
        world_to_camera = np.array(camera_transform.get_inverse_matrix())

        visible = self._visible_signs(signs, camera_transform)

        for distance, sign in visible:
            self._draw_one(frame, sign, world_to_camera, focal, cx, cy,
                           self._sign_brightness(distance))
        return frame

    def _visible_signs(self, signs, camera_transform):
        """
        Signs on the camera's current stretch of the route, facing
        the camera, far ones first. [(distance, sign), ...]
        """
        cam_loc = camera_transform.location
        cam_pos = np.array([cam_loc.x, cam_loc.y, cam_loc.z])

        # How far along the route the camera is.
        progress = self._route_progress(cam_pos[:2])
        if progress is None:
            return []

        visible = []
        for sign in signs:
            ahead = sign["distance"] - progress
            if ahead > VISIBLE_AHEAD_METERS or ahead < -VISIBLE_BEHIND_METERS:
                continue
            distance = float(np.linalg.norm(sign["center"] - cam_pos))
            if distance > MAX_DRAW_DISTANCE:
                continue
            # Only the front of the sign (the car must be in front of it).
            if np.dot(cam_pos - sign["center"], -sign["forward"]) < 0:
                continue
            visible.append((distance, sign))
        visible.sort(key=lambda item: -item[0])
        return visible

    # --------------------------------------------------------
    # WHERE EACH SIGN IS ON SCREEN (for "same sign" checks)
    # --------------------------------------------------------

    def sign_screen_boxes(self, camera_transform, width, height, fov_deg):
        """
        Screen box of every visible roadside sign in this camera
        image: [{"id": 3, "name": "STOP .png", "bbox": [x1,y1,x2,y2]}]
        """
        with self._lock:
            signs = list(self.signs)
        if not signs:
            return []

        focal, cx, cy = _camera_intrinsics(width, height, fov_deg)
        world_to_camera = np.array(camera_transform.get_inverse_matrix())

        boxes = []
        for _, sign in self._visible_signs(signs, camera_transform):
            corners_px, depth = _world_to_image(sign["corners"], world_to_camera, focal, cx, cy)
            if (depth <= MIN_DRAW_DEPTH).any():
                continue
            x1, y1 = corners_px.min(axis=0)
            x2, y2 = corners_px.max(axis=0)
            if x2 < 0 or y2 < 0 or x1 >= width or y1 >= height:
                continue
            boxes.append({
                "id": sign["id"],
                "name": sign["name"],
                "bbox": [int(max(0, x1)), int(max(0, y1)),
                         int(min(width, x2)), int(min(height, y2))],
            })
        return boxes

    def _draw_one(self, frame, sign, world_to_camera, focal, cx, cy, brightness=1.0):
        height, width = frame.shape[:2]

        # Pole
        pole_px, pole_depth = _world_to_image(sign["pole"], world_to_camera, focal, cx, cy)
        if (pole_depth > MIN_DRAW_DEPTH).all():
            thickness = int(max(1, round(focal * SIGN_POLE_WIDTH_METERS / pole_depth.mean())))
            p1 = tuple(int(round(v)) for v in pole_px[0])
            p2 = tuple(int(round(v)) for v in pole_px[1])
            if max(abs(p1[0]), abs(p1[1]), abs(p2[0]), abs(p2[1])) < 10 * max(width, height):
                pole_color = tuple(int(c * brightness) for c in POLE_COLOR_BGR)
                cv2.line(frame, p1, p2, pole_color, thickness, cv2.LINE_AA)

        # Panel
        corners_px, depth = _world_to_image(sign["corners"], world_to_camera, focal, cx, cy)
        if (depth <= MIN_DRAW_DEPTH).any():
            return

        x_min, y_min = np.floor(corners_px.min(axis=0)).astype(int)
        x_max, y_max = np.ceil(corners_px.max(axis=0)).astype(int)
        box_w, box_h = x_max - x_min, y_max - y_min

        if box_w < 2 or box_h < 2:
            return
        if x_max < 0 or y_max < 0 or x_min >= width or y_min >= height:
            return
        if box_w > 2 * width or box_h > 2 * height:
            return

        image = sign["image"]
        ih, iw = image.shape[:2]
        source = np.float32([[0, 0], [iw - 1, 0], [iw - 1, ih - 1], [0, ih - 1]])
        target = np.float32(corners_px - np.array([x_min, y_min]))
        matrix = cv2.getPerspectiveTransform(source, target)

        patch = cv2.warpPerspective(
            image, matrix, (int(box_w), int(box_h)),
            flags=cv2.INTER_AREA if box_w < iw else cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

        # Weather: darker at night, softer in rain.
        if brightness < 0.999:
            patch[:, :, :3] = np.clip(patch[:, :, :3] * brightness, 0, 255).astype(np.uint8)
        if self.blur > 0 and min(patch.shape[:2]) > 4:
            k = 2 * self.blur + 1
            patch = cv2.GaussianBlur(patch, (k, k), 0)

        _blend_bgra(frame, patch, int(x_min), int(y_min))

    # --------------------------------------------------------
    # INFO / CLEANUP
    # --------------------------------------------------------

    def get_spawned_signs(self):
        with self._lock:
            return list(self.signs)

    def clear_signs(self):
        with self._lock:
            self.signs = []
            self.route = []
            self._route_xy = None
            self._route_dist = None
            self._progress_index = 0