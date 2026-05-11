import os
from glob import glob

from vehicles.vehicle_A.edge_pipeline import run_vehicle_A_pipeline


# ==============================
# PROCESS ALL IMAGES IN TEST FOLDER
# ==============================

def get_all_test_images(test_folder="test/"):

    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.ppm"]
    image_paths = []

    for ext in image_extensions:
        image_paths.extend(
            glob(os.path.join(test_folder, ext))
        )

    return sorted(image_paths)


# ==============================
# PROCESS SINGLE IMAGE
# ==============================

def process_single_image(image_path):

    print(f"\n{'=' * 70}")
    print(f"PROCESSING IMAGE: {image_path}")
    print(f"{'=' * 70}")

    results = run_vehicle_A_pipeline(image_path)

    if not results["detections"]:
        print("No traffic signs detected")
        return None

    return results


# ==============================
# DISPLAY RESULTS
# ==============================

def display_results(results):

    if not results:
        return

    print("\n")
    print("=" * 70)
    print("VEHICLE A EDGE AI PIPELINE RESULTS")
    print("=" * 70)

    # =====================================================
    # STEP 1 - DETECTION
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 1 - TRAFFIC SIGN DETECTION")
    print("=" * 70)

    for item in results["detections"]:

        print("\n" + "-" * 50)

        print(f"Sign Number              : {item['sign_number']}")
        print(f"Color                    : {item['color']}")
        print(f"Shape                    : {item['shape']}")
        print(f"Cropped Sign Path        : {item['cropped_sign_path']}")

    # =====================================================
    # STEP 2 - KNOWLEDGE IDENTIFICATION
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 2 - KNOWLEDGE IDENTIFICATION")
    print("=" * 70)

    for item in results["detections"]:

        print("\n" + "-" * 50)

        print(f"Sign Number              : {item['sign_number']}")
        print(f"Identified Knowledge     : {item['knowledge_type']}")

    # =====================================================
    # STEP 3 - IMPORTANCE SCORE CALCULATION
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 3 - IMPORTANCE SCORE CALCULATION")
    print("=" * 70)

    for item in results["agent_outputs"]:

        print("\n" + "-" * 50)

        print(f"Sign Number              : {item['sign_number']}")

        if item["knowledge_type"] == "KNOWN":
            print("Importance Score         : Not Required")
        else:
            print(f"Importance Score         : {item['importance_score']}")

    # =====================================================
    # STEP 4 - RL AGENT DECISION
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 4 - RL AGENT DECISION")
    print("=" * 70)

    for item in results["agent_outputs"]:

        print("\n" + "-" * 50)

        print(f"Sign Number              : {item['sign_number']}")
        print(f"RL Agent Decision        : {item['agent_action']}")
        print(f"Next Step                : {item['next_step']}")

    # =====================================================
    # STEP 5 - KNOWLEDGE PACKAGE DETAILS
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 5 - KNOWLEDGE PACKAGE DETAILS")
    print("=" * 70)

    if len(results["knowledge_packages"]) == 0:

        print("No knowledge packages created")

    else:

        for package in results["knowledge_packages"]:

            print("\n" + "-" * 50)

            print(f"Package ID               : {package['package_id']}")
            print(f"Vehicle ID               : {package['vehicle_id']}")
            print(f"Knowledge Type           : {package['knowledge_type']}")
            print(f"Importance Score         : {package['importance_score']}")
            print(f"Color                    : {package['color']}")
            print(f"Shape                    : {package['shape']}")
            print(f"Cropped Image Path       : {package['cropped_sign_path']}")
            print(f"Bounding Box             : {package['bbox']}")
            print(f"Verification Status      : {package['status']}")
            print(f"Embedding Length         : {len(package['embedding'])}")

    # =====================================================
    # STEP 6 - GLOBAL VERIFICATION
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 6 - GLOBAL VERIFICATION")
    print("=" * 70)

    if len(results["verified_packages"]) == 0:

        print("No verified packages")

    else:

        for verified in results["verified_packages"]:

            print("\n" + "-" * 50)

            print(f"Package ID               : {verified['package_id']}")
            print(f"Verification Status      : {verified['verification_status']}")
            print(f"Class ID                 : {verified.get('global_class_id')}")
            print(f"Sign Name                : {verified.get('sign_name')}")
            print(f"Category                 : {verified.get('category')}")
            print(f"Global Confidence        : {verified.get('global_confidence')}")
           
    # =====================================================
    # STEP 7 - RL FEEDBACK
    # =====================================================

    print("\n")
    print("=" * 70)
    print("STEP 7 - RL FEEDBACK")
    print("=" * 70)

    if len(results["rl_feedbacks"]) == 0:

        print("No RL feedback generated")

    else:

        for feedback in results["rl_feedbacks"]:

            print("\n" + "-" * 50)

            print(f"Package ID               : {feedback['package_id']}")
            print(f"Sign Number              : {feedback['sign_number']}")
            print(f"Agent Action             : {feedback['agent_action']}")
            print(f"RL Reward                : {feedback['rl_reward']}")


# ==============================
# MAIN
# ==============================

def main():

    test_images = get_all_test_images()

    print(f"\nFound {len(test_images)} test images")

    total_detections = 0
    total_shares = 0

    for index, image_path in enumerate(test_images):

        print(f"\n{'#' * 70}")
        print(f"PROCESSING IMAGE {index + 1}/{len(test_images)}")
        print(f"{'#' * 70}")

        results = process_single_image(image_path)

        if results:

            total_detections += len(results["detections"])
            total_shares += len(results["knowledge_packages"])

            display_results(results)

    print("\n")
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"Total Images Processed   : {len(test_images)}")
    print(f"Total Signs Detected     : {total_detections}")
    print(f"Total Knowledge Shared   : {total_shares}")

    print("=" * 70)


if __name__ == "__main__":
    main()