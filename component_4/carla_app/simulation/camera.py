# ============================================================
# CARLA CAMERA MANAGER - Chase view + Model input preview
# ============================================================

import threading

import carla
import cv2
import numpy as np

from carla_app.config.simulation_config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FOV,
    CAMERA_FPS,
)
from carla_app.streaming.video_stream import get_video_stream


# ============================================================
# CAMERA PLACEMENT
# ============================================================

# Chase camera: 6.5 m behind, 2.8 m up, looking slightly down.
CHASE_LOCATION = carla.Location(x=-6.5, y=0.0, z=2.8)
CHASE_ROTATION = carla.Rotation(pitch=-12.0, yaw=0.0, roll=0.0)

# Front camera: on the bonnet, looking straight ahead.
FRONT_LOCATION = carla.Location(x=1.5, y=0.0, z=1.6)
FRONT_ROTATION = carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)


# ============================================================
# MODEL INPUT PREVIEW (picture-in-picture)
# ============================================================

PIP_WIDTH = 360          # width of the small preview box
PIP_MARGIN = 16          # gap from the left and bottom edges
PIP_LABEL = "MODEL INPUT: FRONT RGB"
PIP_LABEL_HEIGHT = 24    # black bar above the preview
PIP_BORDER = 2           # white border thickness


class Camera:
    """
    Manages the chase camera (website view) and the front
    camera (ML input + small preview).
    """

    def __init__(
        self,
        world,
        vehicle,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fov=CAMERA_FOV,
        sign_manager=None,
    ):
        self.world = world
        self.vehicle = vehicle
        self.width = width
        self.height = height
        self.fov = fov

        # TrafficSignManager that draws the roadside signs into
        # both camera images (None = no signs).
        self.sign_manager = sign_manager

        self.chase_cam = None
        self.front_cam = None

        self.front_frame = None
        self.front_transform = None
        self.front_frame_number = None
        self.frame_lock = threading.Lock()

        self.video_stream = get_video_stream()

    # ============================================================
    # CREATE CAMERAS
    # ============================================================

    def _make_blueprint(self):
        blueprint_library = self.world.get_blueprint_library()
        camera_bp = blueprint_library.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", str(self.width))
        camera_bp.set_attribute("image_size_y", str(self.height))
        camera_bp.set_attribute("fov", str(self.fov))

        # Limit rendering to CAMERA_FPS instead of "as fast as
        # possible", which wastes GPU/CPU and causes lag.
        camera_bp.set_attribute("sensor_tick", str(1.0 / float(CAMERA_FPS)))
        return camera_bp

    def create_camera(self):
        """
        Spawn and start both cameras.
        """
        if self.world is None:
            raise RuntimeError("CARLA world is not available.")
        if self.vehicle is None:
            raise RuntimeError("Vehicle must be spawned first.")

        camera_bp = self._make_blueprint()

        # --------------------------------------------------------
        # 1. Front camera (ML input)
        # --------------------------------------------------------
        self.front_cam = self.world.spawn_actor(
            camera_bp,
            carla.Transform(FRONT_LOCATION, FRONT_ROTATION),
            attach_to=self.vehicle,
        )
        self.front_cam.listen(self._process_front_image)
        print("[OK] Front camera created (model input).")

        # --------------------------------------------------------
        # 2. Chase camera (website view)
        # --------------------------------------------------------
        self.chase_cam = self.world.spawn_actor(
            camera_bp,
            carla.Transform(CHASE_LOCATION, CHASE_ROTATION),
            attach_to=self.vehicle,
        )
        self.chase_cam.listen(self._process_chase_image)
        print("[OK] Chase camera created (website view).")

        print("[OK] Camera FPS: {}".format(CAMERA_FPS))
        return self.front_cam

    # ============================================================
    # IMAGE HELPERS
    # ============================================================

    @staticmethod
    def _to_bgr(image):
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((image.height, image.width, 4))
        return array[:, :, :3].copy()

    @staticmethod
    def _draw_preview(display, preview):
        """
        Draw the small model-input box in the bottom-left corner
        of the display frame.
        """
        display_h, display_w = display.shape[:2]
        preview_h, preview_w = preview.shape[:2]

        box_w = min(PIP_WIDTH, display_w - 2 * PIP_MARGIN)
        box_h = int(preview_h * box_w / float(preview_w))
        small = cv2.resize(preview, (box_w, box_h), interpolation=cv2.INTER_AREA)

        x1 = PIP_MARGIN
        y2 = display_h - PIP_MARGIN
        y1 = y2 - box_h
        label_y1 = y1 - PIP_LABEL_HEIGHT

        if label_y1 < 0:
            return display

        # White border around label + preview
        cv2.rectangle(
            display,
            (x1 - PIP_BORDER, label_y1 - PIP_BORDER),
            (x1 + box_w + PIP_BORDER - 1, y2 + PIP_BORDER - 1),
            (255, 255, 255),
            thickness=-1,
        )

        # Black label bar
        cv2.rectangle(
            display,
            (x1, label_y1),
            (x1 + box_w - 1, y1 - 1),
            (0, 0, 0),
            thickness=-1,
        )
        cv2.putText(
            display,
            PIP_LABEL,
            (x1 + 8, y1 - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Preview image
        display[y1:y2, x1:x1 + box_w] = small
        return display

    # ============================================================
    # IMAGE CALLBACKS
    # ============================================================

    def _draw_signs(self, bgr, image):
        """Draw roadside signs using the camera pose of this image."""
        if self.sign_manager is None:
            return bgr
        try:
            return self.sign_manager.draw_signs(bgr, image.transform, self.fov)
        except Exception as e:
            print("[ERROR] Drawing signs: {}".format(e))
            return bgr

    def _process_front_image(self, image):
        """Store the front frame (with roadside signs) for the ML pipeline."""
        try:
            bgr = self._to_bgr(image)
            bgr = self._draw_signs(bgr, image)
            with self.frame_lock:
                self.front_frame = bgr
                # Camera position for this exact frame (used to know
                # where each roadside sign is in it).
                self.front_transform = image.transform
                self.front_frame_number = image.frame
        except Exception as e:
            print("[ERROR] Front camera: {}".format(e))

    def _process_chase_image(self, image):
        """Build the website frame: chase view + model preview."""
        try:
            display = self._to_bgr(image)
            display = self._draw_signs(display, image)

            with self.frame_lock:
                front = self.front_frame

            if front is not None:
                display = self._draw_preview(display, front)

            self.video_stream.update_frame(display)
        except Exception as e:
            print("[ERROR] Chase camera: {}".format(e))

    # ============================================================
    # GET LATEST FRAME (for ML pipeline - front view only)
    # ============================================================

    def get_latest_frame(self):
        """
        Return the latest front frame in RGB order (unchanged
        behaviour from the previous version).
        """
        with self.frame_lock:
            if self.front_frame is None:
                return None
            return cv2.cvtColor(self.front_frame.copy(), cv2.COLOR_BGR2RGB)

    def get_front_frame_bgr(self):
        """
        Return the latest clean front frame in BGR order
        (what OpenCV / YOLO expect).
        """
        with self.frame_lock:
            if self.front_frame is None:
                return None
            return self.front_frame.copy()

    def get_front_frame_with_pose(self):
        """
        (frame_bgr, camera_transform, frame_number) of the latest
        front frame, or (None, None, None).
        """
        with self.frame_lock:
            if self.front_frame is None:
                return None, None, None
            return self.front_frame.copy(), self.front_transform, self.front_frame_number

    # ============================================================
    # DESTROY
    # ============================================================

    def destroy(self):
        for cam in [self.chase_cam, self.front_cam]:
            if cam is not None:
                try:
                    cam.stop()
                except Exception:
                    pass
                try:
                    cam.destroy()
                except Exception:
                    pass
        self.chase_cam = None
        self.front_cam = None
        self.front_frame = None
        self.video_stream.clear()
        print("[INFO] CARLA cameras destroyed.")


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

CameraManager = Camera