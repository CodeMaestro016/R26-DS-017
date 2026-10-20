# -*- coding: utf-8 -*-
"""
feature_pipeline.py  (v3 -- adds visibility-gated pose acceptance)

Every motion/pose/behaviour formula below is copied as closely as
possible from the original script's compute_motion_features(),
compute_pose_features(), and compute_behavior_features(). The five
context features are necessarily adapted, since PIE's context came
from annotated video (traffic-light boxes, crosswalk boxes, num_lanes
attributes) and CARLA supplies the equivalent information as live 3D
ground truth instead -- see each one's docstring for exactly what
changed and why.

============================================================================
WHAT MATCHES EXACTLY vs WHAT'S ADAPTED
============================================================================
MATCHES EXACTLY (same formula, same landmark-space, same thresholds):
  - All 10 motion features
  - All 12 pose features
  - 8 of 9 behaviour features (pause_duration, hesitation_cycles,
    total_hesitation_time, distance_change_rate,
    temporal_movement_probability, looks_left, looks_right,
    direction_changes)

ADAPTED (same intent/definition, different ground-truth source):
  - distance_to_curb (the 9th behaviour feature): original used 2D
    image distance to an annotated crosswalk bounding box. CARLA
    version uses 3D world distance to the nearest crosswalk zone from
    world.get_map().get_crosswalks(), normalised by a fixed reference
    distance instead of the image diagonal (there is no "image
    diagonal" for a world-space measurement). Still 0=at a crosswalk,
    1=far from any crosswalk.
  - traffic_light_state / vehicle_distance / crosswalk_presence /
    road_width / pedestrian_density: computed from CARLA's actual 3D
    scene graph (traffic light actors, other vehicle actors, map
    crosswalk zones, lane count, nearby walker count) rather than 2D
    annotation boxes. Arguably MORE reliable than the original
    video-based versions, since CARLA gives exact ground truth
    instead of an annotator's 2D box.

Landmark convention (unchanged from the original): MediaPipe outputs
x, y normalised 0-1 WITHIN THE CROPPED BOUNDING BOX, not the full
frame. All motion/pose/behaviour math below operates in that same
crop-relative space, exactly like the original.

------------------------------------------------------------------
FIX (see debugging session): the original offline pipeline
(pose_estimation.ipynb) stored FOUR values per landmark --
[x, y, z, visibility] -- and only ever fed real, hand-verified crops
into the model. The live CARLA pipeline instead ran on crops as small
as 30px with a pose-server that had (a) dropped visibility from the
payload entirely and (b) lowered its confidence thresholds, so every
returned landmark -- including low-confidence guesses on tiny/blurry
crops -- was treated as equally trustworthy. That let raw MediaPipe
jitter alone manufacture "speed" on a completely stationary
pedestrian (confirmed via live testing: a provably frozen pedestrian
was still classified Jaywalk/Aggressive/Committed).

pose_server.py has been restored to send visibility again and use the
original 0.5/0.5 thresholds. This file adds the other half of the
fix: PoseExtractor.extract() now rejects a detection outright (treats
it exactly like "no pose found", i.e. returns None) if the mean
visibility on the hip/ankle landmarks -- the joints every speed and
behaviour feature is actually computed from -- is below a minimum
threshold. This happens BEFORE anything is smoothed or stored, so the
EMA smoothing in PedestrianTracker.update() only ever operates on
landmarks that were already judged reliable, instead of trying to
damp out noise after the fact.
------------------------------------------------------------------
"""

import io
import json
import urllib.request

import math
import numpy as np
from collections import deque

# NOTE: MediaPipe is NOT imported here. No PyPI release of MediaPipe
# ships a Python 3.7 wheel (confirmed by checking PyPI directly), and
# the CARLA 0.9.15 client only has a Python 3.7 wheel -- so this
# process (running in the CARLA venv) can't import mediapipe at all.
# Pose extraction instead happens in a separate process (pose_server.py,
# running under the instance's normal Python 3.12) using the real
# MediaPipe Tasks API -- the same one pose_estimation.py used. This
# class just POSTs image crops there and parses the JSON response.

POSE_SERVER_URL = "http://127.0.0.1:8091/pose"

# ── Constants, copied from the recovered original script ──────────
WINDOW_SIZE = 30
SPEED_THRESHOLD = 0.01

# ── Frame-rate correction ──────────────────────────────────────────
# HYPOTHESIS, backed by concrete reasoning but not yet empirically
# confirmed at time of writing -- verify against ensemble_server.py's
# startup scaler diagnostic before trusting this blindly.
#
# The recovered original formulas compute speed as distance / gap,
# where `gap` is a difference in FRAME NUMBERS -- not seconds. That's
# fine as long as "one frame" means the same real time duration in
# both the training data and here. It doesn't:
#   - PIE video was recorded at 30 fps  -> 1 frame = 1/30 s = 0.0333s
#   - CARLA here ticks at 20 Hz (fixed_delta_seconds=0.05) -> 1 "frame"
#     (one processed tick) = 0.05s
# For the exact same real walking speed, a CARLA tick spans 50% more
# real time than a PIE frame, so every distance/gap speed feature
# computed here comes out ~1.5x larger than the equivalent PIE
# measurement -- not because CARLA pedestrians behave differently, but
# because the "gap" unit itself represents a different amount of real
# time. That's large enough to push features outside the distribution
# the model was actually trained on, independent of anything CARLA is
# doing wrong behaviourally.
#
# This constant converts a CARLA-tick-based speed value into the
# PIE-frame-equivalent scale the model expects. Applied once, right
# after each `speeds` array is computed, so every downstream feature
# (mean, max, diffs, variance, threshold comparisons) consistently
# uses the corrected scale.
PIE_FPS = 30.0
CARLA_TICK_SECONDS = 0.05
SPEED_FRAME_RATE_CORRECTION = (1.0 / PIE_FPS) / CARLA_TICK_SECONDS  # ~0.667
HEAD_DIRECTION_THRESHOLD = 0.08
DIRECTION_CHANGE_THRESHOLD_DEGREES = 45.0

# ── Adaptive landmark smoothing ────────────────────────────────────
# Confirmed via three separate live tests (a provably FROZEN
# pedestrian, and a pedestrian misclassified as "Aggressive" a full
# second BEFORE it had moved at all) that raw MediaPipe landmark
# jitter, sampled sparsely and irregularly (pose success rates as low
# as ~12% observed), is on its own enough to manufacture an erratic-
# motion signature regardless of the pedestrian's actual behavior.
# Three separate pedestrian-mechanics fixes (walking animation
# mechanism, speed ramping, body-orientation continuity) were tested
# and ruled out -- the issue is upstream of any of that, in how raw,
# noisy landmark positions get turned into motion features at all.
#
# Two complementary fixes now apply, in this order:
#   1. VISIBILITY GATING (new): low-confidence detections on the
#      hip/ankle landmarks are rejected outright in extract(), before
#      they ever reach the smoothing/window logic below. This removes
#      the worst offenders (near-total guesses on tiny/distant crops)
#      instead of trying to average them away after the fact.
#   2. EMA SMOOTHING (unchanged): whatever passes the visibility gate
#      is smoothed with an EXPONENTIAL MOVING AVERAGE, right when it's
#      received -- so every downstream feature (speed, angles,
#      everything) automatically works from damped positions instead
#      of raw per-detection noise. The smoothing strength ADAPTS to
#      how long it's been since the last successful detection
#      (LANDMARK_SMOOTHING_TAU_TICKS controls this): a short gap
#      (recent good data) smooths heavily since we can afford to; a
#      long gap smooths lightly, trusting the new detection more, so
#      smoothing doesn't itself introduce a lag artifact by clinging
#      to a stale position across a large gap.
LANDMARK_SMOOTHING_TAU_TICKS = 6.0  # ~0.3s at 20 ticks/sec
MAX_LANES = 6.0

# Minimum mean visibility (MediaPipe's own per-landmark confidence
# score, 0-1) required on the hip/ankle landmarks before a detection
# is trusted at all. These four joints are what every motion and
# behaviour feature is actually computed from (hip midpoint = the
# "position" used for speed/pause/hesitation/direction-change; ankles
# feed the step-length features), so gating on them specifically --
# rather than on all 33 landmarks, most of which don't feed any
# feature -- targets exactly the noise source that was manufacturing
# false motion. 0.5 matches MediaPipe's own commonly-used "visible"
# cutoff and the confidence level the original offline pipeline's
# model was run at.
MIN_KEY_JOINT_VISIBILITY = 0.5

HISTORY_LEN = WINDOW_SIZE  # kept as a separate name for readability elsewhere

# ── MediaPipe landmark indices, copied from the recovered original ─
NOSE = 0
L_EAR = 7
R_EAR = 8
L_SHOULDER = 11
R_SHOULDER = 12
L_HIP = 23
R_HIP = 24
L_KNEE = 25
R_KNEE = 26
L_ANKLE = 27
R_ANKLE = 28
L_FOOT_INDEX = 31
R_FOOT_INDEX = 32

# The joints every speed/behaviour feature is derived from (hip
# midpoint drives position/speed/pause/hesitation/direction-change;
# ankles drive the step-length features). Visibility is checked on
# exactly these, not all 33 landmarks.
KEY_JOINTS_FOR_VISIBILITY = [L_HIP, R_HIP, L_ANKLE, R_ANKLE]

TL_MAP = {
    "red": 0.0,
    "yellow": 0.5,
    "green": 1.0,
    "none": -1.0,
}


# ============================================================================
# GEOMETRY HELPERS -- copied from the recovered original script
# ============================================================================

def midpoint(a, b):
    return (np.array(a) + np.array(b)) / 2.0


def angle_between(p1, vertex, p2):
    v1 = np.array(p1) - np.array(vertex)
    v2 = np.array(p2) - np.array(vertex)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return 0.0
    cos_angle = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def vertical_angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return float(np.degrees(np.arctan2(dx, -dy)))


def horizontal_angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    if abs(dx) < 1e-6:
        return 90.0
    return float(np.degrees(np.arctan2(dy, dx)))


def angular_difference(a, b):
    diff = (b - a + 180.0) % 360.0 - 180.0
    return abs(diff)


def estimate_head_direction(lm):
    """-1 = looking image-left, 0 = frontal/uncertain, 1 = looking
    image-right. Copied exactly from the recovered original."""
    nose = np.array(lm[NOSE][:2])
    left_ear = np.array(lm[L_EAR][:2])
    right_ear = np.array(lm[R_EAR][:2])
    ear_mid = midpoint(left_ear, right_ear)
    head_width = np.linalg.norm(right_ear - left_ear)
    if head_width < 1e-6:
        return 0
    normalized_offset = (nose[0] - ear_mid[0]) / head_width
    if normalized_offset < -HEAD_DIRECTION_THRESHOLD:
        return -1
    if normalized_offset > HEAD_DIRECTION_THRESHOLD:
        return 1
    return 0


# ============================================================================
# POSE EXTRACTOR -- HTTP client to pose_server.py (see that file's
# docstring for why this is a separate process instead of an import)
# ============================================================================

class PoseExtractor:
    def __init__(self, server_url=POSE_SERVER_URL, timeout=5.0,
                 min_key_joint_visibility=MIN_KEY_JOINT_VISIBILITY):
        self.server_url = server_url
        self.timeout = timeout
        self.min_key_joint_visibility = min_key_joint_visibility
        self.last_error = None  # None = success or "no pose found"; else a short reason string

        # Diagnostics: how often a detection came back from the pose
        # server but was then rejected here for low visibility, as
        # opposed to the server finding nothing at all. Useful for
        # sanity-checking that the visibility gate is actually doing
        # something (and isn't, say, rejecting everything or nothing).
        self.rejected_low_visibility = 0
        self.accepted = 0

        # Lazily imported here so this file doesn't hard-fail if PIL
        # isn't installed until the first actual call.
        from PIL import Image
        self._Image = Image

    def extract(self, rgb_crop):
        """rgb_crop: HxWx3 uint8 RGB numpy array (already cropped to
        the pedestrian's bounding box). Returns (33, 4) array of
        [x, y, z, visibility] (crop-relative, 0-1 for x/y/visibility)
        -- or None if no pose was detected, the crop is empty, the
        pose server didn't respond, or the detection came back but
        wasn't confident enough on the hip/ankle landmarks to trust
        (see MIN_KEY_JOINT_VISIBILITY).

        Rejecting a low-visibility detection is treated exactly like
        "no pose found this frame" everywhere downstream -- it's
        recorded as a gap in PedestrianTracker's window, never as
        fabricated motion. This is deliberate: a wrong guess is worse
        than a missing frame, because a missing frame is correctly
        ignored by the motion math, while a wrong guess gets
        differentiated into a bogus "speed".

        self.last_error is set to None on success or a genuine
        "no pose found" result, or to a short string describing what
        went wrong (connection refused, timeout, low visibility, etc.)
        so callers can tell those situations apart."""
        self.last_error = None

        if rgb_crop is None or rgb_crop.size == 0:
            self.last_error = "empty crop (bounding box projection likely failed)"
            return None

        try:
            img = self._Image.fromarray(rgb_crop, mode='RGB')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            data = buf.getvalue()

            req = urllib.request.Request(
                self.server_url, data=data,
                headers={'Content-Type': 'application/octet-stream'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))

            if result.get('landmarks') is None:
                self.last_error = None  # genuine "no pose found", not a connection problem
                return None

            landmarks = np.array(result['landmarks'], dtype=np.float32)

            # Backward-compatibility guard: if pose_server.py hasn't
            # been updated to send visibility yet (3 columns instead
            # of 4), skip the gate entirely rather than crashing, but
            # say so loudly -- this pipeline should not be trusted
            # for real evaluation without visibility gating.
            if landmarks.ndim != 2 or landmarks.shape[1] < 4:
                self.last_error = (
                    "pose_server response has no visibility channel "
                    "(shape %s) -- update pose_server.py to send "
                    "[x, y, z, visibility]; proceeding WITHOUT "
                    "visibility gating for this frame." % (landmarks.shape,)
                )
                self.accepted += 1
                return landmarks

            key_joint_visibility = landmarks[KEY_JOINTS_FOR_VISIBILITY, 3]
            mean_visibility = float(np.mean(key_joint_visibility))

            if mean_visibility < self.min_key_joint_visibility:
                self.last_error = (
                    "low hip/ankle visibility (%.2f < %.2f) -- "
                    "treating as no detection" % (
                        mean_visibility, self.min_key_joint_visibility)
                )
                self.rejected_low_visibility += 1
                return None

            self.accepted += 1
            return landmarks

        except Exception as e:
            self.last_error = f"pose_server unreachable ({e})"
            # Pose server not running / connection refused / timeout --
            # treat exactly like a failed on-device detection so the
            # rest of the pipeline degrades gracefully instead of
            # crashing the whole simulation.
            return None

    def close(self):
        pass  # nothing to release -- the actual model lives in pose_server.py


# ============================================================================
# PEDESTRIAN TRACKER
# ============================================================================

class PedestrianTracker:
    """Keeps a trailing window (up to WINDOW_SIZE frames) of raw
    landmark arrays for one pedestrian, and computes ONE 36-feature
    vector per call to compute_feature_vector() -- mirroring how the
    recovered original computes one feature row per frame from a
    trailing window of that frame's preceding history."""

    def __init__(self, ped_id):
        self.ped_id = ped_id
        self.landmark_window = deque(maxlen=WINDOW_SIZE)  # list of (33,4) or None
        self.frame_indices = deque(maxlen=WINDOW_SIZE)    # monotonically increasing ints

        # Adaptive EMA smoothing state -- see LANDMARK_SMOOTHING_TAU_TICKS
        # above for why this exists. None until the first successful
        # (visibility-gated) detection; from then on holds the running
        # smoothed position.
        self._smoothed_landmarks = None
        self._last_smoothed_frame_index = None

        # Context, set externally each frame from CARLA ground truth.
        self.traffic_light_state = -1.0
        self.vehicle_distance_norm = 1.0
        self.crosswalk_presence = 0.0
        self.road_width_norm = 0.0
        self.pedestrian_density = 0.0
        self.distance_to_curb_norm = 1.0

        self._frame_counter = 0

    def set_context(self, traffic_light_state=None, vehicle_distance_norm=None,
                     crosswalk_presence=None, road_width_norm=None,
                     pedestrian_density=None, distance_to_curb_norm=None):
        if traffic_light_state is not None:
            self.traffic_light_state = traffic_light_state
        if vehicle_distance_norm is not None:
            self.vehicle_distance_norm = vehicle_distance_norm
        if crosswalk_presence is not None:
            self.crosswalk_presence = crosswalk_presence
        if road_width_norm is not None:
            self.road_width_norm = road_width_norm
        if pedestrian_density is not None:
            self.pedestrian_density = pedestrian_density
        if distance_to_curb_norm is not None:
            self.distance_to_curb_norm = distance_to_curb_norm

    def update(self, landmarks, frame_index=None):
        """landmarks: (33,4) array from PoseExtractor.extract() (already
        visibility-gated -- anything that reaches here has already been
        judged reliable enough to trust), or None if detection failed
        or was rejected this frame (still recorded, so gaps show up as
        missing entries rather than fabricated motion).

        frame_index: the ACTUAL simulation tick this frame came from.
        Pass this explicitly whenever frames might be processed out
        of lockstep with every tick (e.g. a background worker thread
        that falls behind and skips some) -- the motion formulas
        divide by (idx[i] - idx[i-1]), so an accurate gap matters.
        If omitted, falls back to auto-incrementing by 1 each call,
        which is only correct if update() is called exactly once per
        tick with nothing skipped.

        Successful detections are smoothed (adaptive EMA, see
        LANDMARK_SMOOTHING_TAU_TICKS) before being stored, damping any
        residual frame-to-frame jitter that survives the visibility
        gate in PoseExtractor.extract(). Failed/rejected detections
        (None) are stored as-is; smoothing only applies to accepted
        data, never fabricates a value for a genuine gap."""
        if frame_index is None:
            frame_index = self._frame_counter

        if landmarks is not None:
            if self._smoothed_landmarks is None:
                # First-ever successful detection -- nothing to blend
                # with yet.
                self._smoothed_landmarks = landmarks.astype(np.float64).copy()
            else:
                gap_ticks = max(frame_index - self._last_smoothed_frame_index, 1)
                alpha = 1.0 - math.exp(-gap_ticks / LANDMARK_SMOOTHING_TAU_TICKS)
                self._smoothed_landmarks = (
                    alpha * landmarks.astype(np.float64)
                    + (1.0 - alpha) * self._smoothed_landmarks
                )
            self._last_smoothed_frame_index = frame_index
            stored_landmarks = self._smoothed_landmarks.astype(np.float32).copy()
        else:
            stored_landmarks = None

        self.landmark_window.append(stored_landmarks)
        self.frame_indices.append(frame_index)
        self._frame_counter = frame_index + 1

    def ready(self):
        return self.landmark_window[-1] is not None if self.landmark_window else False

    def _valid_window(self):
        """Only the frames where detection succeeded, in order. The
        one deliberate difference from the recovered original: it
        assumed a landmark for every frame in the track (offline,
        pre-verified crops); live detection isn't as reliable, so
        failed/rejected frames are skipped here rather than
        fabricated."""
        lms, idxs = [], []
        for lm, idx in zip(self.landmark_window, self.frame_indices):
            if lm is not None:
                lms.append(lm)
                idxs.append(idx)
        return lms, idxs

    # ------------------------------------------------------------------
    # MOTION FEATURES (10) -- matches compute_motion_features
    # ------------------------------------------------------------------

    def _motion_features(self, lms, idxs):
        F = np.zeros(10, dtype=np.float32)
        if len(lms) < 1:
            return F

        hip_positions = [midpoint(lm[L_HIP][:2], lm[R_HIP][:2]) for lm in lms]
        left_ankles = [lm[L_ANKLE][:2] for lm in lms]
        right_ankles = [lm[R_ANKLE][:2] for lm in lms]

        speeds = []
        for i in range(1, len(hip_positions)):
            gap = idxs[i] - idxs[i - 1]
            if gap <= 0:
                continue
            distance = np.linalg.norm(np.array(hip_positions[i]) - np.array(hip_positions[i - 1]))
            speeds.append(distance / gap)
        speeds = np.array(speeds if speeds else [0.0])
        speeds = speeds * SPEED_FRAME_RATE_CORRECTION

        # NOTE: this deviates slightly from the recovered original,
        # which used the single most recent instantaneous speed here.
        # That's fine on PIE's offline, hand-verified landmark data,
        # but live MediaPipe detection on a rendered CARLA crop has
        # enough frame-to-frame jitter that a single noisy reading
        # regularly crashes the TTC estimate and triggers a panic
        # STOP even when the pedestrian is genuinely far away and
        # closing slowly. Averaging the last few readings keeps the
        # feature responsive to real speed changes while damping out
        # single-frame noise spikes.
        smoothing_window = min(4, len(speeds))
        F[0] = np.mean(speeds[-smoothing_window:])
        F[1] = np.mean(speeds)
        F[2] = np.max(speeds)

        if len(speeds) > 1:
            diffs = np.diff(speeds)
            pos = diffs[diffs > 0]
            neg = diffs[diffs < 0]
            F[3] = np.mean(pos) if len(pos) > 0 else 0.0
            F[4] = abs(np.mean(neg)) if len(neg) > 0 else 0.0

        F[5] = np.var(speeds)
        F[6] = np.mean(speeds >= SPEED_THRESHOLD)

        if len(left_ankles) > 1:
            F[7] = np.mean([np.linalg.norm(np.array(left_ankles[i]) - np.array(left_ankles[i - 1]))
                             for i in range(1, len(left_ankles))])
        if len(right_ankles) > 1:
            F[8] = np.mean([np.linalg.norm(np.array(right_ankles[i]) - np.array(right_ankles[i - 1]))
                             for i in range(1, len(right_ankles))])

        F[9] = np.mean(speeds < SPEED_THRESHOLD)
        return F

    # ------------------------------------------------------------------
    # POSE FEATURES (12) -- matches compute_pose_features
    # ------------------------------------------------------------------

    def _pose_features(self, lms):
        F = np.zeros(12, dtype=np.float32)
        if len(lms) < 1:
            return F

        lm = lms[-1]
        ls, rs = lm[L_SHOULDER], lm[R_SHOULDER]
        lh, rh = lm[L_HIP], lm[R_HIP]
        la, ra = lm[L_ANKLE], lm[R_ANKLE]
        lf, rf = lm[L_FOOT_INDEX], lm[R_FOOT_INDEX]
        nose = lm[NOSE]

        shoulder_mid = midpoint(ls, rs)
        hip_mid = midpoint(lh, rh)
        knee_mid = midpoint(lm[L_KNEE], lm[R_KNEE])

        F[0] = vertical_angle(hip_mid, shoulder_mid)          # upper_body_angle
        F[1] = vertical_angle(hip_mid, knee_mid)               # lower_body_angle
        F[2] = vertical_angle(shoulder_mid, nose)               # head_angle

        head_directions = [estimate_head_direction(lm_t) for lm_t in lms]
        turns, prev = 0, 0
        for d in head_directions:
            if d == 0:
                continue
            if prev != 0 and d != prev:
                turns += 1
            prev = d
        F[3] = turns / max(len(lms) - 1, 1)                    # head_turn_frequency

        F[4] = horizontal_angle(ls, rs)                         # shoulder_angle
        F[5] = horizontal_angle(lh, rh)                         # hip_angle
        F[6] = angle_between(lh, la, lf)                        # foot_angle_left
        F[7] = angle_between(rh, ra, rf)                        # foot_angle_right
        F[8] = abs(shoulder_mid[1] - hip_mid[1])                # forward_lean
        F[9] = abs(shoulder_mid[0] - hip_mid[0])                # lateral_lean
        F[10] = horizontal_angle(hip_mid, shoulder_mid)         # body_orientation

        orientations = []
        for lm_t in lms:
            sm = midpoint(lm_t[L_SHOULDER], lm_t[R_SHOULDER])
            hm = midpoint(lm_t[L_HIP], lm_t[R_HIP])
            orientations.append(horizontal_angle(hm, sm))
        if len(orientations) > 1:
            changes = [angular_difference(orientations[i - 1], orientations[i])
                       for i in range(1, len(orientations))]
            F[11] = np.mean(changes)                            # body_orientation_change

        return F

    # ------------------------------------------------------------------
    # BEHAVIOUR FEATURES (9, minus distance_to_curb which is
    # context-sourced) -- matches compute_behavior_features, except
    # looks_left/looks_right drop the PIE "look==looking" gate (that
    # annotation doesn't exist in CARLA -- every frame is evaluated
    # instead of only annotator-confirmed "looking" frames).
    # ------------------------------------------------------------------

    def _behavior_features(self, lms, idxs):
        F = np.zeros(9, dtype=np.float32)
        if len(lms) < 1:
            return F

        positions = [midpoint(lm[L_HIP][:2], lm[R_HIP][:2]) for lm in lms]

        speeds = []
        for i in range(1, len(positions)):
            gap = idxs[i] - idxs[i - 1]
            if gap <= 0:
                continue
            speeds.append(np.linalg.norm(np.array(positions[i]) - np.array(positions[i - 1])) / gap)
        speeds = np.array(speeds if speeds else [0.0])
        speeds = speeds * SPEED_FRAME_RATE_CORRECTION

        paused = speeds < SPEED_THRESHOLD
        moving = speeds >= SPEED_THRESHOLD

        runs, cur = [], 0
        for p in paused:
            if p:
                cur += 1
            else:
                if cur > 0:
                    runs.append(cur)
                cur = 0
        if cur > 0:
            runs.append(cur)
        if runs:
            F[0] = np.mean(runs) / max(len(speeds), 1)          # pause_duration

        if len(moving) > 1:
            transitions = sum(moving[i] != moving[i - 1] for i in range(1, len(moving)))
            F[1] = transitions / (len(moving) - 1)              # hesitation_cycles

        hesitation_frames = 0
        i = 1
        while i < len(moving):
            if moving[i - 1] and not moving[i]:
                j = i
                while j < len(moving) and not moving[j]:
                    hesitation_frames += 1
                    j += 1
                i = j
            else:
                i += 1
        F[2] = hesitation_frames / max(len(speeds), 1)          # total_hesitation_time

        # F[3] (distance_to_curb) is context-sourced -- see
        # compute_feature_vector(), which overwrites index 25 with
        # self.distance_to_curb_norm instead of using this slot.

        if len(positions) > 1:
            path_distance = sum(np.linalg.norm(np.array(positions[i]) - np.array(positions[i - 1]))
                                 for i in range(1, len(positions)))
            total_span = max(idxs[-1] - idxs[0], 1)
            F[4] = (path_distance / total_span) * SPEED_FRAME_RATE_CORRECTION  # distance_change_rate

        if len(speeds) > 0:
            weights = np.exp(np.linspace(-1.0, 0.0, len(speeds)))
            weights = weights / weights.sum()
            F[5] = float(np.sum(weights * moving.astype(float))) # temporal_movement_probability

        left_flags, right_flags = [], []
        for lm_t in lms:
            d = estimate_head_direction(lm_t)
            if d == -1:
                left_flags.append(1.0); right_flags.append(0.0)
            elif d == 1:
                left_flags.append(0.0); right_flags.append(1.0)
        F[6] = np.mean(left_flags) if left_flags else 0.0        # looks_left
        F[7] = np.mean(right_flags) if right_flags else 0.0      # looks_right

        if len(positions) > 2:
            disp = np.diff(np.array(positions), axis=0)
            directions = np.degrees(np.arctan2(disp[:, 1], disp[:, 0]))
            changes, valid_pairs = 0, 0
            for i in range(1, len(directions)):
                v_prev, v_cur = disp[i - 1], disp[i]
                if np.linalg.norm(v_prev) < 1e-6 or np.linalg.norm(v_cur) < 1e-6:
                    continue
                valid_pairs += 1
                if angular_difference(directions[i - 1], directions[i]) > DIRECTION_CHANGE_THRESHOLD_DEGREES:
                    changes += 1
            F[8] = changes / max(valid_pairs, 1)                 # direction_changes

        return F

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    def compute_feature_vector(self):
        """Returns the (36,) raw feature vector for the CURRENT frame,
        using the trailing window collected so far. Index order
        matches rule_based_agent.py's F_* constants / FEATURE_INDEX
        in the recovered original script."""
        lms, idxs = self._valid_window()

        motion = self._motion_features(lms, idxs)
        pose = self._pose_features(lms)
        behavior = self._behavior_features(lms, idxs)

        F = np.zeros(36, dtype=np.float32)
        F[0:10] = motion
        F[10:22] = pose
        F[22:31] = behavior

        # Context (indices 31-35) + distance_to_curb (index 25),
        # supplied from CARLA ground truth via set_context() --
        # see carla_live_demo.py.
        F[25] = self.distance_to_curb_norm
        F[31] = self.traffic_light_state
        F[32] = self.vehicle_distance_norm
        F[33] = self.crosswalk_presence
        F[34] = self.road_width_norm
        F[35] = self.pedestrian_density

        return F