# vehicles/vehicle_C/src/detection.py
# Vehicle C - Traffic Sign Detection
#
# Not used in the live pipeline (detection is shared in
# carla_sim/run_simulation.py) - kept for standalone/offline
# testing consistency with Vehicle A and Vehicle B.

import os
import cv2
from ultralytics import YOLO


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VEHICLE_C_DIR = os.path.dirname(
    CURRENT_DIR
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        VEHICLE_C_DIR
    )
)

MODEL_PATH = os.path.join(
    VEHICLE_C_DIR,
    "models",
    "generic_traffic_sign_detector_best.pt"
)

RAW_DIR = os.path.join(
    VEHICLE_C_DIR,
    "data",
    "raw"
)

CROPPED_DIR = os.path.join(
    VEHICLE_C_DIR,
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
    """
    global _model

    if _model is None:

        print("=" * 60)
        print("Loading Vehicle C YOLO model...")
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
        # (Same fix applied to Vehicle A and Vehicle B.)
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

            x1 = max(0, min(x1, image_width - 1))
            y1 = max(0, min(y1, image_height - 1))
            x2 = max(0, min(x2, image_width))
            y2 = max(0, min(y2, image_height))

            if x2 <= x1:
                continue

            if y2 <= y1:
                continue

            cropped_sign = image[
                y1:y2,
                x1:x2
            ]

            if cropped_sign.size == 0:
                continue

            confidence = float(
                box.conf[0]
                .detach()
                .cpu()
                .item()
            )

            yolo_class_id = None

            if box.cls is not None:
                yolo_class_id = int(
                    box.cls[0]
                    .detach()
                    .cpu()
                    .item()
                )

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

        vehicle_C/data/raw
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
    print("Vehicle C - YOLO Detection Test")
    print("=" * 60)

    signs = process_all_images()

    print(
        f"Total detected signs: {len(signs)}"
    )

    print("=" * 60)