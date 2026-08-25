# vehicles/vehicle_A/src/detection.py
# Step 1: Traffic Sign Detection and Cropping - Vehicle A

import os
import cv2
import time
from ultralytics import YOLO


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

MODEL_PATH = "vehicles/vehicle_A/models/generic_traffic_sign_detector_best.pt"
RAW_DIR = "vehicles/vehicle_A/data/raw"
CROPPED_DIR = "vehicles/vehicle_A/data/cropped"


# ==========================================================
# LOAD YOLO MODEL
# ==========================================================

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

    image = cv2.imread(image_path)

    if image is None:
        print("Cannot load image.")
        return []

    # Get original road image size
    image_height, image_width = image.shape[:2]
    image_area = image_width * image_height

    # Run YOLO detection
    results = model(image, conf=conf_threshold, verbose=False)

    detected_signs = []

    for result in results:

        if result.boxes is None:
            continue

        for idx, box in enumerate(result.boxes):

            # Get bounding box coordinates from YOLO
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            # Crop detected traffic sign from road image
            cropped_sign = image[y1:y2, x1:x2]

            # Ignore invalid crop
            if cropped_sign.size == 0:
                continue

            # Calculate visual prominence from YOLO bounding box
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            bbox_area = bbox_width * bbox_height

            visual_prominence = bbox_area / image_area

            # ==================================================
            # MAIN PIPELINE - STORE SIGN DATA IN MEMORY
            #
            # cropped_sign:
            #     Goes to CNN classifier.
            #
            # bbox:
            #     Kept for future reference.
            #
            # visual_prominence:
            #     Used later for importance score / RL agent.
            # ==================================================

            detected_signs.append({
                "cropped_sign": cropped_sign,
                "bbox": [x1, y1, x2, y2],
                "visual_prominence": visual_prominence
            })

            # ==================================================
            # DEBUG ONLY - SAVE CROPPED IMAGE
            #
            # This is only to check whether YOLO detection works.
            # Keep this commented in the main pipeline.
            #
            # If needed for debugging, uncomment this block.
            # ==================================================
            
            timestamp = int(time.time() * 1000)
            filename = f"sign_{timestamp}_{idx}.png"

            cropped_path = os.path.join(CROPPED_DIR, filename)

            os.makedirs(CROPPED_DIR, exist_ok=True)
            cv2.imwrite(cropped_path, cropped_sign)

            print("Saved debug crop:", cropped_path)
            

    return detected_signs


# ==========================================================
# PROCESS ALL RAW IMAGES
# ==========================================================

def process_all_images():
    """
    Run YOLO detection for all images inside vehicle_A/data/raw.

    Output:
        List of detected sign objects stored in memory.
    """

    os.makedirs(RAW_DIR, exist_ok=True)

    image_files = [
        file for file in os.listdir(RAW_DIR)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not image_files:
        print("No raw images found.")
        return []

    all_detected_signs = []

    for image_file in image_files:
        image_path = os.path.join(RAW_DIR, image_file)

        detected_signs = detect_and_crop(image_path)
        all_detected_signs.extend(detected_signs)

    return all_detected_signs


# ==========================================================
# RUN STEP 1 ONLY
# ==========================================================

if __name__ == "__main__":

    print("=" * 45)
    print("Step 1: Traffic Sign Detection")
    print("=" * 45)

    detected_signs = process_all_images()

    print(f"Detected signs: {len(detected_signs)}")
    print("=" * 45)