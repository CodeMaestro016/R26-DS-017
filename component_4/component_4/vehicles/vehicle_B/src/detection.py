# vehicles/vehicle_B/src/detection.py
# Vehicle B - Traffic Sign Detection
#
# Supports:
#   1. Offline image detection (used by run_offline_test in main.py)
#   2. Live frame detection (not used in the live pipeline -
#      detection is shared in carla_sim/run_simulation.py - but
#      kept here for standalone testing consistency with Vehicle A)
#
# IMPORTANT:
# YOLO is loaded lazily so PyTorch/CUDA initialization happens
# only when detection is actually required.

import os
import cv2
from ultralytics import YOLO


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VEHICLE_B_DIR = os.path.dirname(
    CURRENT_DIR
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        VEHICLE_B_DIR
    )
)

MODEL_PATH = os.path.join(
    VEHICLE_B_DIR,
    "models",
    "generic_traffic_sign_detector_best.pt"
)

RAW_DIR = os.path.join(
    VEHICLE_B_DIR,
    "data",
    "raw"
)

CROPPED_DIR = os.path.join(
    VEHICLE_B_DIR,
    "data",
    "cropped"
)


# ==========================================================
# YOLO CONFIGURATION
# ==========================================================

DEFAULT_CONFIDENCE = 0.25

_model = None


# ==========================================================
# YOLO MODEL LOADER
# ==========================================================

def get_model():
    """
    Lazy-load the YOLO traffic-sign detector.

    The model is loaded only when detection is required.
    """
    global _model

    if _model is None:

        print("=" * 60)
        print("Loading Vehicle B YOLO model...")
        print("Model:", MODEL_PATH)
        print("=" * 60)

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "YOLO model not found:\n"
                f"{MODEL_PATH}"
            )

        _model = YOLO(MODEL_PATH)

        # ======================================================
        # CRITICAL FIX: Force YOLO to use CPU
        # This avoids the segfault caused by TensorFlow/PyTorch
        # GPU conflict when both frameworks are loaded.
        # (Same fix applied to Vehicle A's detection.py.)
        # ======================================================
        _model.to('cpu')
        print("YOLO model loaded successfully (CPU).")

    return _model


# ==========================================================
# LIVE FRAME DETECTION
# ==========================================================

def detect_frame(
    frame,
    conf_threshold=DEFAULT_CONFIDENCE
):
    """
    Run YOLO on one frame.

    Parameters
    ----------
    frame:
        NumPy BGR image.

    conf_threshold:
        YOLO confidence threshold.

    Returns
    -------
    list
        List of detected traffic signs.

    Each item contains:

        cropped_sign
        bbox
        visual_prominence
        yolo_confidence
        yolo_class_id
    """

    if frame is None:
        return []

    if not hasattr(frame, "shape"):
        print(
            "Invalid frame supplied to detect_frame()."
        )
        return []

    if len(frame.shape) != 3:
        print(
            "Invalid frame dimensions:",
            frame.shape
        )
        return []

    image = frame.copy()

    image_height, image_width = (
        image.shape[:2]
    )

    if image_height <= 0 or image_width <= 0:
        return []

    image_area = (
        image_width * image_height
    )

    model = get_model()

    # ======================================================
    # YOLO INFERENCE
    # ======================================================

    results = model(
        image,
        conf=conf_threshold,
        verbose=False
    )

    detected_signs = []

    for result in results:

        if result.boxes is None:
            continue

        if len(result.boxes) == 0:
            continue

        for box in result.boxes:

            # ------------------------------------------------
            # Bounding box
            # ------------------------------------------------

            coordinates = (
                box.xyxy[0]
                .detach()
                .cpu()
                .tolist()
            )

            x1, y1, x2, y2 = map(
                int,
                coordinates
            )

            # ------------------------------------------------
            # Safety clamp
            # ------------------------------------------------

            x1 = max(
                0,
                min(
                    x1,
                    image_width - 1
                )
            )

            y1 = max(
                0,
                min(
                    y1,
                    image_height - 1
                )
            )

            x2 = max(
                0,
                min(
                    x2,
                    image_width
                )
            )

            y2 = max(
                0,
                min(
                    y2,
                    image_height
                )
            )

            if x2 <= x1:
                continue

            if y2 <= y1:
                continue

            # ------------------------------------------------
            # Crop
            # ------------------------------------------------

            cropped_sign = image[
                y1:y2,
                x1:x2
            ]

            if cropped_sign.size == 0:
                continue

            # ------------------------------------------------
            # Confidence
            # ------------------------------------------------

            confidence = float(
                box.conf[0]
                .detach()
                .cpu()
                .item()
            )

            # ------------------------------------------------
            # YOLO class
            # ------------------------------------------------

            yolo_class_id = None

            if box.cls is not None:
                yolo_class_id = int(
                    box.cls[0]
                    .detach()
                    .cpu()
                    .item()
                )

            # ------------------------------------------------
            # Visual prominence
            # ------------------------------------------------

            bbox_width = x2 - x1
            bbox_height = y2 - y1

            bbox_area = (
                bbox_width *
                bbox_height
            )

            visual_prominence = (
                bbox_area /
                image_area
            )

            # ------------------------------------------------
            # Store everything in memory
            # ------------------------------------------------

            detected_signs.append({

                "cropped_sign":
                    cropped_sign,

                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ],

                "visual_prominence":
                    float(
                        visual_prominence
                    ),

                "yolo_confidence":
                    confidence,

                "yolo_class_id":
                    yolo_class_id
            })

    return detected_signs


# ==========================================================
# OFFLINE IMAGE DETECTION
# ==========================================================

def detect_and_crop(
    image_path,
    conf_threshold=DEFAULT_CONFIDENCE,
    save_debug_crop=False
):
    """
    Detect signs in one image file.

    This function is retained for your
    existing offline/testing workflow.
    """

    image = cv2.imread(
        image_path
    )

    if image is None:

        print(
            "Cannot load image:",
            image_path
        )

        return []

    detected_signs = detect_frame(
        image,
        conf_threshold
    )

    if save_debug_crop:

        os.makedirs(
            CROPPED_DIR,
            exist_ok=True
        )

        base_name = os.path.splitext(
            os.path.basename(
                image_path
            )
        )[0]

        for index, sign in enumerate(
            detected_signs,
            start=1
        ):

            crop_path = os.path.join(
                CROPPED_DIR,
                f"{base_name}_sign_{index}.jpg"
            )

            cv2.imwrite(
                crop_path,
                sign["cropped_sign"]
            )

            print(
                "Saved debug crop:",
                crop_path
            )

    return detected_signs


# ==========================================================
# PROCESS ALL RAW IMAGES
# ==========================================================

def process_all_images(
    conf_threshold=DEFAULT_CONFIDENCE,
    save_debug_crop=True
):
    """
    Offline testing only.

    Processes images from:

        vehicle_B/data/raw
    """

    os.makedirs(
        RAW_DIR,
        exist_ok=True
    )

    image_files = [
        file
        for file in os.listdir(
            RAW_DIR
        )
        if file.lower().endswith(
            (
                ".jpg",
                ".jpeg",
                ".png"
            )
        )
    ]

    if not image_files:

        print(
            "No raw images found."
        )

        return []

    all_detected_signs = []

    for image_file in image_files:

        image_path = os.path.join(
            RAW_DIR,
            image_file
        )

        detected_signs = (
            detect_and_crop(
                image_path,
                conf_threshold,
                save_debug_crop
            )
        )

        all_detected_signs.extend(
            detected_signs
        )

    return all_detected_signs


# ==========================================================
# SIMPLE TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Vehicle B - YOLO Detection Test")
    print("=" * 60)

    signs = process_all_images()

    print(
        f"Total detected signs: {len(signs)}"
    )

    print("=" * 60)