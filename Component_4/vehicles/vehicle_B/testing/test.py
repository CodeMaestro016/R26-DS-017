# ==========================================================
# vehicles/vehicle_B/testing/test.py
#
# VEHICLE B - TESTING PIPELINE
#
# Pipeline:
#   1. Load test images from:
#        vehicles/vehicle_B/data/test/class_X/
#
#   2. YOLO detects the traffic sign in the full image.
#
#   3. Best detected sign is cropped.
#
#   4. Vehicle B CNN classifies the cropped sign.
#
#   5. CNN prediction is compared with the true class
#      obtained from the folder name.
#
# Outputs:
#   - Per-image predictions
#   - Per-class performance
#   - Overall performance
#
# CSV files are automatically versioned:
#   test0_per_image_predictions.csv
#   test0_class_summary.csv
#   test0_overall_summary.csv
#
# Next execution:
#   test1_...
#   test2_...
#   etc.
# ==========================================================


# ==========================================================
# 1. IMPORTS
# ==========================================================

import os
import sys
import csv
import json
import re

import cv2
import numpy as np
from ultralytics import YOLO


# ==========================================================
# 2. PROJECT PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# vehicles/vehicle_B
VEHICLE_B_DIR = os.path.dirname(CURRENT_DIR)

# Project root
PROJECT_ROOT = os.path.dirname(VEHICLE_B_DIR)

# Add project paths to Python path
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

if VEHICLE_B_DIR not in sys.path:
    sys.path.insert(0, VEHICLE_B_DIR)


# ==========================================================
# 3. LOCAL VEHICLE IMPORTS
# ==========================================================

from src.cnn_classifier import VehicleBCNN


# ==========================================================
# 4. PATH CONFIGURATION
# ==========================================================

# Test dataset
TEST_DIR = os.path.join(
    VEHICLE_B_DIR,
    "data",
    "test"
)

# Test result output directory
OUTPUT_DIR = os.path.join(
    VEHICLE_B_DIR,
    "data",
    "test_results"
)

# Vehicle B class mapping
MAPPING_PATH = os.path.join(
    VEHICLE_B_DIR,
    "models",
    "vehicle_B_class_mapping.json"
)

# YOLO traffic-sign detector
YOLO_MODEL_PATH = os.path.join(
    VEHICLE_B_DIR,
    "models",
    "generic_traffic_sign_detector_best.pt"
)


# ==========================================================
# 5. DETERMINE TEST RUN NUMBER
# ==========================================================

def get_next_test_id():
    """
    Find the next available test run number.

    Existing files:
        test0_...
        test1_...
        test2_...

    Next run:
        test3_...
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    existing_ids = []

    pattern = re.compile(r"^test(\d+)_")

    for filename in os.listdir(OUTPUT_DIR):

        match = pattern.match(filename)

        if match:
            existing_ids.append(
                int(match.group(1))
            )

    if existing_ids:
        return max(existing_ids) + 1

    return 0


TEST_ID = get_next_test_id()

TEST_PREFIX = f"test{TEST_ID}_"


# ==========================================================
# 6. START TEST
# ==========================================================

print("\n" + "=" * 70)
print(f"VEHICLE B - TEST RUN {TEST_ID}")
print("=" * 70)


# ==========================================================
# 7. LOAD YOLO MODEL
# ==========================================================

print("\nLoading YOLO traffic-sign detector...")

try:

    yolo_model = YOLO(
        YOLO_MODEL_PATH
    )

    print("YOLO model loaded successfully.")

except Exception as e:

    print("ERROR: Failed to load YOLO model.")
    print(f"Reason: {e}")
    sys.exit(1)


# ==========================================================
# 8. LOAD CNN MODEL
# ==========================================================

print("\nLoading Vehicle B CNN classifier...")

try:

    cnn = VehicleBCNN()

    print("CNN classifier loaded successfully.")

except Exception as e:

    print("ERROR: Failed to load CNN classifier.")
    print(f"Reason: {e}")
    sys.exit(1)


# ==========================================================
# 9. LOAD CLASS MAPPING
# ==========================================================

print("\nLoading class mapping...")

if not os.path.exists(MAPPING_PATH):

    print(
        f"ERROR: Class mapping not found:\n"
        f"{MAPPING_PATH}"
    )

    sys.exit(1)


with open(
    MAPPING_PATH,
    "r",
    encoding="utf-8"
) as f:

    mapping = json.load(f)


# ----------------------------------------------------------
# Convert mapping into:
#
# original_class_id -> class_name
# ----------------------------------------------------------

class_names = {}

for info in mapping.values():

    original_class_id = info[
        "original_class_id"
    ]

    class_name = info[
        "class_name"
    ]

    class_names[
        original_class_id
    ] = class_name


print(
    f"Loaded {len(class_names)} class mappings."
)


# ==========================================================
# 10. CHECK TEST DIRECTORY
# ==========================================================

if not os.path.exists(TEST_DIR):

    print(
        f"\nERROR: Test directory not found:\n"
        f"{TEST_DIR}"
    )

    sys.exit(1)


# ==========================================================
# 11. FIND TEST CLASS FOLDERS
# ==========================================================

class_folders = []

for folder_name in os.listdir(TEST_DIR):

    # Only accept folders such as:
    #
    # class_0
    # class_1
    # class_2
    #
    if not folder_name.startswith("class_"):
        continue

    folder_path = os.path.join(
        TEST_DIR,
        folder_name
    )

    # Make sure it is actually a directory
    if not os.path.isdir(folder_path):
        continue

    try:

        class_id = int(
            folder_name.replace(
                "class_",
                ""
            )
        )

    except ValueError:

        print(
            f"WARNING: Invalid folder name: "
            f"{folder_name}"
        )

        continue

    class_folders.append(
        (
            class_id,
            folder_name
        )
    )


# Sort by class ID
class_folders.sort(
    key=lambda x: x[0]
)


# ==========================================================
# 12. CHECK FOR TEST CLASSES
# ==========================================================

if not class_folders:

    print(
        "\nERROR: No class_X folders found."
    )

    sys.exit(1)


print(
    f"\nFound {len(class_folders)} "
    f"test classes."
)


# ==========================================================
# 13. CREATE OUTPUT DIRECTORY
# ==========================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ==========================================================
# 14. STORAGE FOR ALL RESULTS
# ==========================================================

all_results = []

true_labels = []

predicted_labels = []

all_confidences = []


# ==========================================================
# 15. PROCESS TEST DATA
# ==========================================================

for class_id, class_folder in class_folders:

    # ------------------------------------------------------
    # True class information
    # ------------------------------------------------------

    class_name = class_names.get(
        class_id,
        f"Class_{class_id}"
    )

    folder_path = os.path.join(
        TEST_DIR,
        class_folder
    )


    # ------------------------------------------------------
    # Find images
    # ------------------------------------------------------

    image_files = [
        filename
        for filename in os.listdir(folder_path)
        if filename.lower().endswith(
            (
                ".jpg",
                ".jpeg",
                ".png"
            )
        )
    ]

    image_files.sort()


    # ------------------------------------------------------
    # Skip empty folders
    # ------------------------------------------------------

    if not image_files:

        print(
            f"\nWARNING: No images found "
            f"in {class_folder}"
        )

        continue


    # ------------------------------------------------------
    # Class header
    # ------------------------------------------------------

    print("\n" + "-" * 70)

    print(
        f"Testing Class {class_id}: "
        f"{class_name}"
    )

    print(
        f"Images: {len(image_files)}"
    )

    print("-" * 70)


    # ------------------------------------------------------
    # Per-class counters
    # ------------------------------------------------------

    class_correct = 0

    class_total = 0

    class_confidences = []


    # ======================================================
    # PROCESS EACH IMAGE
    # ======================================================

    for image_file in image_files:

        image_path = os.path.join(
            folder_path,
            image_file
        )


        # --------------------------------------------------
        # Read image
        # --------------------------------------------------

        image = cv2.imread(
            image_path
        )

        if image is None:

            print(
                f"WARNING: Cannot read "
                f"{image_file}"
            )

            continue


        # ==================================================
        # STEP 1 - YOLO DETECTION
        # ==================================================

        results = yolo_model(
            image,
            conf=0.25,
            verbose=False
        )


        # --------------------------------------------------
        # Find highest-confidence detection
        # --------------------------------------------------

        best_crop = None

        best_yolo_confidence = 0.0


        for result in results:

            if result.boxes is None:
                continue


            for box in result.boxes:

                # Bounding box
                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )


                # Crop detected sign
                crop = image[
                    y1:y2,
                    x1:x2
                ]


                # Ignore invalid crop
                if crop.size == 0:
                    continue


                # YOLO confidence
                yolo_confidence = float(
                    box.conf[0]
                )


                # Keep best detection
                if (
                    yolo_confidence
                    >
                    best_yolo_confidence
                ):

                    best_yolo_confidence = (
                        yolo_confidence
                    )

                    best_crop = crop


        # --------------------------------------------------
        # No YOLO detection
        # --------------------------------------------------

        if best_crop is None:

            print(
                f"  NO DETECTION | "
                f"{image_file}"
            )

            continue


        # ==================================================
        # STEP 2 - CNN CLASSIFICATION
        # ==================================================

        result = cnn.classify(
            best_crop
        )


        # --------------------------------------------------
        # CNN classification failed
        # --------------------------------------------------

        if result is None:

            print(
                f"  CLASSIFICATION FAILED | "
                f"{image_file}"
            )

            continue


        # --------------------------------------------------
        # Get CNN prediction
        # --------------------------------------------------

        predicted_class_id = result[
            "class_id"
        ]

        predicted_class_name = result[
            "class_name"
        ]

        confidence = float(
            result["confidence"]
        )


        # ==================================================
        # STEP 3 - COMPARE PREDICTION WITH TRUE LABEL
        # ==================================================

        correct = (
            predicted_class_id
            ==
            class_id
        )


        # --------------------------------------------------
        # Update counters
        # --------------------------------------------------

        class_total += 1

        class_confidences.append(
            confidence
        )

        true_labels.append(
            class_id
        )

        predicted_labels.append(
            predicted_class_id
        )

        all_confidences.append(
            confidence
        )


        if correct:

            class_correct += 1


        # ==================================================
        # STORE RESULT
        # ==================================================

        all_results.append({

            "true_class_id":
                class_id,

            "true_class_name":
                class_name,

            "image":
                image_file,

            "pred_class_id":
                predicted_class_id,

            "pred_class_name":
                predicted_class_name,

            "confidence":
                confidence,

            "correct":
                correct

        })


        # ==================================================
        # PRINT IMAGE RESULT
        # ==================================================

        status = (
            "PASS"
            if correct
            else
            "FAIL"
        )


        print(
            f"  {status:<4} | "
            f"{image_file:<25} | "
            f"True: {class_id:<3} | "
            f"Pred: {predicted_class_id:<3} "
            f"{predicted_class_name:<20} | "
            f"Conf: {confidence:.4f}"
        )


    # ======================================================
    # CLASS STATISTICS
    # ======================================================

    if class_total > 0:

        class_accuracy = (
            class_correct
            /
            class_total
        )

        class_average_confidence = (
            np.mean(
                class_confidences
            )
        )

    else:

        class_accuracy = 0.0

        class_average_confidence = 0.0


    # ------------------------------------------------------
    # Print class result
    # ------------------------------------------------------

    print()

    print(
        f"Class {class_id} Result:"
    )

    print(
        f"  Correct       : "
        f"{class_correct}/{class_total}"
    )

    print(
        f"  Accuracy      : "
        f"{class_accuracy * 100:.2f}%"
    )

    print(
        f"  Average Conf. : "
        f"{class_average_confidence:.4f}"
    )


# ==========================================================
# 16. OVERALL STATISTICS
# ==========================================================

total_images = len(
    all_results
)

total_correct = sum(
    1
    for result in all_results
    if result["correct"]
)

total_wrong = (
    total_images
    -
    total_correct
)


if total_images > 0:

    overall_accuracy = (
        total_correct
        /
        total_images
    )

else:

    overall_accuracy = 0.0


if all_confidences:

    overall_average_confidence = (
        np.mean(
            all_confidences
        )
    )

else:

    overall_average_confidence = 0.0


# ==========================================================
# 17. PRINT OVERALL RESULTS
# ==========================================================

print("\n")

print("=" * 70)

print(
    "OVERALL TEST RESULTS"
)

print("=" * 70)

print(
    f"Total Images Tested   : "
    f"{total_images}"
)

print(
    f"Correct Predictions   : "
    f"{total_correct}"
)

print(
    f"Wrong Predictions     : "
    f"{total_wrong}"
)

print(
    f"Overall Accuracy      : "
    f"{overall_accuracy * 100:.2f}%"
)

print(
    f"Average Confidence    : "
    f"{overall_average_confidence:.4f}"
)

print("=" * 70)


# ==========================================================
# 18. PER-CLASS SUMMARY
# ==========================================================

print("\n")

print("=" * 85)

print(
    "PER-CLASS SUMMARY"
)

print("=" * 85)

print(
    f"{'ID':>4} "
    f"{'Class Name':<30} "
    f"{'Total':>7} "
    f"{'Correct':>8} "
    f"{'Wrong':>7} "
    f"{'Accuracy':>10} "
    f"{'Avg Conf':>10}"
)

print("-" * 85)


for class_id, class_folder in class_folders:

    class_name = class_names.get(
        class_id,
        f"Class_{class_id}"
    )


    # Get all results for this class
    class_results = [
        result
        for result in all_results
        if result["true_class_id"]
        ==
        class_id
    ]


    # Skip if no successful predictions
    if not class_results:
        continue


    total = len(
        class_results
    )


    correct = sum(
        1
        for result in class_results
        if result["correct"]
    )


    wrong = (
        total
        -
        correct
    )


    accuracy = (
        correct
        /
        total
    )


    confidences = [
        result["confidence"]
        for result in class_results
    ]


    average_confidence = np.mean(
        confidences
    )


    print(
        f"{class_id:>4} "
        f"{class_name:<30} "
        f"{total:>7} "
        f"{correct:>8} "
        f"{wrong:>7} "
        f"{accuracy * 100:>9.2f}% "
        f"{average_confidence:>10.4f}"
    )


print("=" * 85)


# ==========================================================
# 19. SAVE PER-IMAGE RESULTS
# ==========================================================

image_csv = os.path.join(
    OUTPUT_DIR,
    f"{TEST_PREFIX}"
    f"per_image_predictions.csv"
)


with open(
    image_csv,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)


    writer.writerow([
        "true_class_id",
        "true_class_name",
        "image",
        "pred_class_id",
        "pred_class_name",
        "confidence",
        "correct"
    ])


    for result in all_results:

        writer.writerow([

            result["true_class_id"],

            result["true_class_name"],

            result["image"],

            result["pred_class_id"],

            result["pred_class_name"],

            round(
                result["confidence"],
                4
            ),

            result["correct"]

        ])


# ==========================================================
# 20. SAVE CLASS SUMMARY
# ==========================================================

summary_csv = os.path.join(
    OUTPUT_DIR,
    f"{TEST_PREFIX}"
    f"class_summary.csv"
)


with open(
    summary_csv,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)


    writer.writerow([
        "class_id",
        "class_name",
        "total_images",
        "correct_images",
        "wrong_images",
        "accuracy",
        "avg_confidence"
    ])


    for class_id, class_folder in class_folders:

        class_name = class_names.get(
            class_id,
            f"Class_{class_id}"
        )


        class_results = [
            result
            for result in all_results
            if result["true_class_id"]
            ==
            class_id
        ]


        if not class_results:
            continue


        total = len(
            class_results
        )


        correct = sum(
            1
            for result in class_results
            if result["correct"]
        )


        wrong = (
            total
            -
            correct
        )


        accuracy = (
            correct
            /
            total
        )


        confidences = [
            result["confidence"]
            for result in class_results
        ]


        average_confidence = np.mean(
            confidences
        )


        writer.writerow([

            class_id,

            class_name,

            total,

            correct,

            wrong,

            round(
                accuracy,
                4
            ),

            round(
                average_confidence,
                4
            )

        ])


# ==========================================================
# 21. SAVE OVERALL SUMMARY
# ==========================================================

overall_csv = os.path.join(
    OUTPUT_DIR,
    f"{TEST_PREFIX}"
    f"overall_summary.csv"
)


with open(
    overall_csv,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)


    writer.writerow([
        "total_images",
        "correct",
        "wrong",
        "overall_accuracy",
        "avg_confidence"
    ])


    writer.writerow([

        total_images,

        total_correct,

        total_wrong,

        round(
            overall_accuracy,
            4
        ),

        round(
            overall_average_confidence,
            4
        )

    ])


# ==========================================================
# 22. FINAL OUTPUT
# ==========================================================

print("\n")

print("=" * 70)

print(
    "TESTING COMPLETED SUCCESSFULLY"
)

print("=" * 70)

print(
    f"Test Run ID : {TEST_ID}"
)

print(
    f"Output Dir  : {OUTPUT_DIR}"
)

print()

print(
    "Generated files:"
)

print(
    f"  1. {TEST_PREFIX}"
    f"per_image_predictions.csv"
)

print(
    f"  2. {TEST_PREFIX}"
    f"class_summary.csv"
)

print(
    f"  3. {TEST_PREFIX}"
    f"overall_summary.csv"
)

print()

print(
    f"Final Accuracy : "
    f"{overall_accuracy * 100:.2f}%"
)

print(
    f"Average Confidence : "
    f"{overall_average_confidence:.4f}"
)

print("=" * 70)