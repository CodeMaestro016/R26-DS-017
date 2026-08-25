# vehicles/vehicle_C/src/detection.py
# Step 1: Traffic Sign Detection and Cropping - Vehicle C

import os
import cv2
import time
from ultralytics import YOLO


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

# YOLO detector model used by Vehicle C
MODEL_PATH = "vehicles/vehicle_C/models/generic_traffic_sign_detector_best.pt"

# Folder containing Vehicle C road images
RAW_DIR = "vehicles/vehicle_C/data/raw"

# Optional folder for saving debug crops
CROPPED_DIR = "vehicles/vehicle_C/data/cropped"


# ==========================================================
# LOAD YOLO MODEL
# ==========================================================

# Load the trained traffic-sign detector
model = YOLO(MODEL_PATH)


# ==========================================================
# DETECTION FUNCTION
# ==========================================================

def detect_and_crop(image_path, conf_threshold=0.25):
    """
    Detect traffic signs in one road image.

    Output:
        A list of detected sign objects stored in memory.

    Each detected sign contains:
        - cropped_sign
        - bbox
        - visual_prominence
    """

    # Load the road image
    image = cv2.imread(image_path)

    if image is None:
        print("Cannot load image.")
        return []

    # Get the original image size
    image_height, image_width = image.shape[:2]
    image_area = image_width * image_height

    # Run YOLO traffic-sign detection
    results = model(
        image,
        conf=conf_threshold,
        verbose=False
    )

    detected_signs = []

    # Process every YOLO result
    for result in results:

        if result.boxes is None:
            continue

        # Process every detected bounding box
        for idx, box in enumerate(result.boxes):

            # Read bounding-box coordinates
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            # Keep coordinates inside the image
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(image_width, x2)
            y2 = min(image_height, y2)

            # Crop the detected traffic sign
            cropped_sign = image[
                y1:y2,
                x1:x2
            ]

            # Skip invalid crops
            if cropped_sign.size == 0:
                continue

            # Calculate bounding-box area
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            bbox_area = bbox_width * bbox_height

            # Calculate how much of the image is occupied by the sign
            visual_prominence = (
                bbox_area / image_area
                if image_area > 0
                else 0.0
            )

            # Store detected sign data in memory
            detected_signs.append({
                "cropped_sign": cropped_sign,
                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ],
                "visual_prominence": (
                    visual_prominence
                )
            })

            # Debug crop saving
            """
            timestamp = int(time.time() * 1000)
            filename = f"sign_{timestamp}_{idx}.png"

            cropped_path = os.path.join(CROPPED_DIR, filename)

            os.makedirs(CROPPED_DIR, exist_ok=True)
            cv2.imwrite(cropped_path, cropped_sign)

            print("Saved debug crop:", cropped_path)
            """

    # Return all detected traffic signs
    return detected_signs


# ==========================================================
# PROCESS ALL RAW IMAGES
# ==========================================================

def process_all_images():
    """
    Run YOLO detection for all images insidemvehicle_C/data/raw.
    Output:List of detected sign objects stored in memory.
    """

    # Create the raw image folder if it does not exist
    os.makedirs(RAW_DIR, exist_ok=True)

    # Find all supported road images
    image_files = [
        file for file in os.listdir(RAW_DIR)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not image_files:
        print("No raw images found.")
        return []

    all_detected_signs = []

    # Detect signs in every raw image
    for image_file in image_files:
        image_path = os.path.join(RAW_DIR, image_file)

        detected_signs = detect_and_crop(image_path)
        all_detected_signs.extend(detected_signs)

    # Return detections from all images
    return all_detected_signs


# ==========================================================
# RUN STEP 1 ONLY
# ==========================================================

if __name__ == "__main__":

    # Run Vehicle C detection as a standalone test
    print("=" * 45)
    print("Step 1: Traffic Sign Detection")
    print("=" * 45)

    detected_signs = process_all_images()

    print(f"Detected signs: {len(detected_signs)}")
    print("=" * 45)