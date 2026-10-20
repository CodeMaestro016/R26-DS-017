# ============================================================
# CARLA VIDEO STREAM
# ============================================================

import threading
import time

import cv2
import numpy as np

from carla_app.config import simulation_config as _config


# ============================================================
# STREAM SETTINGS
# ============================================================
# Values in simulation_config.py are used if present,
# otherwise these defaults.

# Width of the streamed video (height keeps 16:9).
STREAM_WIDTH = getattr(_config, "STREAM_WIDTH", 960)

# JPEG quality (lower = smaller frames = smoother over SSH).
STREAM_JPEG_QUALITY = getattr(_config, "STREAM_JPEG_QUALITY", 65)

# Maximum frames per second encoded for the browser.
STREAM_FPS = getattr(_config, "STREAM_FPS", 12)


# ============================================================
# "CAMERA OFF" PICTURE
# ============================================================

def _make_placeholder_jpeg():
    width = int(STREAM_WIDTH or 960)
    height = int(round(width * 9 / 16.0))
    image = np.full((height, width, 3), 32, dtype=np.uint8)

    lines = [
        ("CAMERA OFF", 1.4, 3, (235, 235, 235)),
        ("Select a vehicle and press Start", 0.8, 2, (190, 190, 190)),
    ]
    y = int(height * 0.45)
    for text, scale, thickness, color in lines:
        (text_w, text_h), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness
        )
        x = (width - text_w) // 2
        cv2.putText(
            image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
            scale, color, thickness, cv2.LINE_AA,
        )
        y += text_h + 30

    success, encoded = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80]
    )
    return encoded.tobytes() if success else None


class VideoStream:
    """
    Thread-safe container for the latest display frame,
    stored both as an image and as ready-to-send JPEG bytes.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._frame = None
        self._jpeg = None
        self._frame_id = 0
        self._frame_timestamp = None
        self._last_encode_time = 0.0
        self._min_interval = 1.0 / float(max(1, STREAM_FPS))
        self._placeholder_jpeg = _make_placeholder_jpeg()

    # --------------------------------------------------------
    # UPDATE (called from the camera thread)
    # --------------------------------------------------------

    def update_frame(self, frame):
        """
        Store the newest display frame and encode it to JPEG.

        Frames arriving faster than STREAM_FPS are skipped,
        so no CPU is wasted on frames nobody will see.
        """
        if frame is None:
            return

        now = time.time()
        if now - self._last_encode_time < self._min_interval:
            return
        self._last_encode_time = now

        height, width = frame.shape[:2]
        if STREAM_WIDTH and width > STREAM_WIDTH:
            new_height = int(round(height * STREAM_WIDTH / float(width)))
            frame = cv2.resize(
                frame,
                (int(STREAM_WIDTH), new_height),
                interpolation=cv2.INTER_AREA,
            )

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, int(STREAM_JPEG_QUALITY)],
        )
        if not success:
            return

        with self._lock:
            self._frame = frame
            self._jpeg = encoded.tobytes()
            self._frame_id += 1
            self._frame_timestamp = now

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    def get_jpeg(self):
        """
        Return (jpeg_bytes, frame_id) for the latest frame.
        frame_id increases by 1 for every new frame, so the
        server can tell whether a frame is new.

        When no camera is running, the "CAMERA OFF" picture
        is returned instead.
        """
        with self._lock:
            if self._jpeg is None:
                return self._placeholder_jpeg, self._frame_id
            return self._jpeg, self._frame_id

    def get_frame(self):
        """Copy of the latest display frame (as an image)."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def encode_jpeg(self, quality=None):
        """Kept for older code: latest JPEG bytes (already encoded)."""
        with self._lock:
            return self._jpeg

    def has_frame(self):
        with self._lock:
            return self._jpeg is not None

    def get_frame_timestamp(self):
        with self._lock:
            return self._frame_timestamp

    def get_frame_id(self):
        with self._lock:
            return self._frame_id

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    def clear(self):
        """
        Called when cameras are destroyed (Stop). The frame id is
        increased so the server immediately sends the
        "CAMERA OFF" picture.
        """
        with self._lock:
            self._frame = None
            self._jpeg = None
            self._frame_timestamp = None
            self._frame_id += 1


# ============================================================
# GLOBAL SHARED VIDEO STREAM
# ============================================================

video_stream = VideoStream()


def get_video_stream():
    return video_stream