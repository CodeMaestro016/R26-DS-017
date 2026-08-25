# vehicles/vehicle_A/main.py
# Vehicle A Local Pipeline

import os
import sys
import time

import cv2


# ==========================================================
# PROJECT PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(CURRENT_DIR)
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ==========================================================
# LOCAL VEHICLE IMPORTS
# ==========================================================

from src.detection import process_all_images
from src.cnn_classifier import VehicleACNN
from src.feature_extraction import FeatureExtractor
from src.embedding_extractor import EmbeddingExtractor
from src.temp_db_checker import TempDBChecker
from src.importance_score import calculate_importance_score

from src.rl_agent import (
    VehicleARLAgent,
    build_rl_state,
    SHARE,
    IGNORE
)

from src.knowledge_package import (
    KnowledgePackageCreator
)


# ==========================================================
# GLOBAL SERVER IMPORTS
# ==========================================================

from global_verification_server.global_verification import (
    GlobalVerificationServer
)

from global_verification_server.broadcast_queue import (
    BroadcastQueue
)


# ==========================================================
# PATHS
# ==========================================================

GLOBAL_DATABASE_PATH = os.path.join(
    PROJECT_ROOT,
    "global_verification_server",
    "database",
    "global_verification_db.pkl"
)

BATCH_TRAINING_DIR = os.path.join(
    CURRENT_DIR,
    "data",
    "batch_training"
)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def print_step_header(
    step_number,
    step_name
):
    print(
        f"\n========== STEP {step_number}: "
        f"{step_name} =========="
    )


def print_step_time(start_time):
    elapsed_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Step Time  : "
        f"{elapsed_time:.4f} seconds"
    )


def get_verified_value(
    result,
    direct_key,
    nested_key=None,
    default=None
):
    if not isinstance(result, dict):
        return default

    if result.get(direct_key) is not None:
        return result.get(direct_key)

    matched_record = result.get(
        "matched_record"
    )

    if (
        isinstance(matched_record, dict)
        and nested_key is not None
        and matched_record.get(nested_key)
        is not None
    ):
        return matched_record.get(
            nested_key
        )

    metadata = result.get(
        "metadata"
    )

    if (
        isinstance(metadata, dict)
        and nested_key is not None
        and metadata.get(nested_key)
        is not None
    ):
        return metadata.get(
            nested_key
        )

    return default


def save_crop_for_batch_training(
    cropped_sign,
    class_id,
    class_name,
    sign_number
):
    if cropped_sign is None:
        return None

    if class_id is None:
        class_folder_name = (
            "class_unknown"
        )
    else:
        class_folder_name = (
            f"class_{class_id}"
        )

    class_directory = os.path.join(
        BATCH_TRAINING_DIR,
        class_folder_name
    )

    os.makedirs(
        class_directory,
        exist_ok=True
    )

    safe_class_name = str(
        class_name or "unknown"
    ).replace(
        " ",
        "_"
    )

    timestamp = int(
        time.time() * 1000
    )

    file_name = (
        f"vehicle_A_"
        f"{safe_class_name}_"
        f"sign_{sign_number}_"
        f"{timestamp}.jpg"
    )

    save_path = os.path.join(
        class_directory,
        file_name
    )

    saved = cv2.imwrite(
        save_path,
        cropped_sign
    )

    if not saved:
        return None

    return save_path


def create_global_server():
    if not os.path.exists(
        GLOBAL_DATABASE_PATH
    ):
        raise FileNotFoundError(
            "Global verification database "
            "was not found:\n"
            f"{GLOBAL_DATABASE_PATH}"
        )

    try:
        return GlobalVerificationServer(
            database_path=(
                GLOBAL_DATABASE_PATH
            ),
            similarity_threshold=0.70
        )

    except TypeError:
        return GlobalVerificationServer(
            similarity_threshold=0.70
        )


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def main():

    total_start_time = (
        time.perf_counter()
    )

    print("=" * 60)
    print("Vehicle A Local Pipeline")
    print("=" * 60)

    print("Global Verification DB:")
    print(GLOBAL_DATABASE_PATH)

    print("=" * 60)

    # ======================================================
    # LOAD PIPELINE COMPONENTS
    # ======================================================

    cnn_classifier = VehicleACNN()

    embedding_extractor = (
        EmbeddingExtractor()
    )

    temp_db_checker = (
        TempDBChecker()
    )

    feature_extractor = (
        FeatureExtractor()
    )

    rl_model_path = os.path.join(
        CURRENT_DIR,
        "models",
        "dqn_rl_agent.pth"
    )

    rl_agent = VehicleARLAgent(
        model_path=rl_model_path
    )

    knowledge_package_creator = (
        KnowledgePackageCreator(
            vehicle_id="Vehicle_A"
        )
    )

    global_verification_server = (
        create_global_server()
    )

    broadcast_queue = BroadcastQueue()

    embedding_version = (
        embedding_extractor
        .get_embedding_version()
    )

    print(
        "Embedding Version:",
        embedding_version
    )

    # ======================================================
    # STEP 1: YOLO DETECTION
    # ======================================================

    print_step_header(
        1,
        "YOLO Detection"
    )

    step_start_time = (
        time.perf_counter()
    )

    detected_signs = (
        process_all_images()
    )

    print(
        f"Detected Signs: "
        f"{len(detected_signs)}"
    )

    print_step_time(
        step_start_time
    )

    if not detected_signs:
        total_time = (
            time.perf_counter()
            - total_start_time
        )

        print(
            "Result     : "
            "No signs detected"
        )

        print(
            f"Total Time : "
            f"{total_time:.4f} seconds"
        )

        print("=" * 60)

        return []

    shared_knowledge_packages = []
    verification_results = []
    broadcast_queue_results = []
    rl_training_results = []

    print("\n" + "-" * 60)
    print("Processing Detected Signs")
    print("-" * 60)

    # ======================================================
    # PROCESS EACH DETECTED SIGN
    # ======================================================

    for sign_number, sign_data in enumerate(
        detected_signs,
        start=1
    ):

        cropped_sign = sign_data.get(
            "cropped_sign"
        )

        print(
            f"\nSIGN {sign_number}"
        )

        print("-" * 60)

        if (
            cropped_sign is None
            or cropped_sign.size == 0
        ):
            print(
                "Status     : "
                "INVALID_CROPPED_SIGN"
            )

            print(
                "Decision   : STOPPED"
            )

            print("-" * 60)

            continue

        # ==================================================
        # STEP 2: CNN CLASSIFICATION
        # ==================================================

        print_step_header(
            2,
            "CNN Classification"
        )

        step_start_time = (
            time.perf_counter()
        )

        classification = (
            cnn_classifier.classify(
                cropped_sign
            )
        )

        if classification is None:
            print(
                "Status     : FAILED"
            )

            print(
                "Decision   : STOPPED"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        predicted_class_id = (
            classification.get(
                "class_id"
            )
        )

        predicted_class_name = (
            classification.get(
                "class_name"
            )
        )

        cnn_confidence = float(
            classification.get(
                "confidence",
                0.0
            )
        )

        classification_status = (
            classification.get(
                "status",
                "UNKNOWN"
            )
        )

        classification_action = (
            classification.get(
                "action",
                "CONTINUE"
            )
        )

        print(
            "Class ID   :",
            predicted_class_id
        )

        print(
            "Class Name :",
            predicted_class_name
        )

        print(
            "Confidence :",
            round(
                cnn_confidence,
                4
            )
        )

        print(
            "Status     :",
            classification_status
        )

        if (
            classification_action
            == "IGNORE"
        ):
            print(
                "Decision   : "
                "KNOWN_SIGN_IGNORED"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 3: COMMON EMBEDDING EXTRACTION
        # ==================================================

        print_step_header(
            3,
            "Embedding Extraction"
        )

        step_start_time = (
            time.perf_counter()
        )

        embedding = (
            embedding_extractor
            .extract_embedding(
                cropped_sign
            )
        )

        if embedding is None:
            print(
                "Status     : FAILED"
            )

            print(
                "Decision   : STOPPED"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        print(
            "Status            : COMPLETED"
        )

        print(
            "Embedding Version :",
            embedding_version
        )

        print(
            "Embedding Length  :",
            len(embedding)
        )

        print_step_time(
            step_start_time
        )

        item = {
            "cropped_sign": cropped_sign,

            "bbox": sign_data.get(
                "bbox"
            ),

            "visual_prominence": float(
                sign_data.get(
                    "visual_prominence",
                    0.0
                )
            ),

            "classification": (
                classification
            ),

            "embedding": embedding,

            "embedding_version": (
                embedding_version
            )
        }

        # ==================================================
        # STEP 4: TEMPORARY MEMORY CHECK
        # ==================================================

        print_step_header(
            4,
            "Temporary DB Check"
        )

        step_start_time = (
            time.perf_counter()
        )

        temp_db_result = (
            temp_db_checker.process_item(
                item
            )
        )

        if temp_db_result is None:
            temp_db_result = {
                "status": "ERROR",
                "similarity": 0.0,
                "action": "STOP"
            }

        temp_status = (
            temp_db_result.get(
                "status",
                "ERROR"
            )
        )

        temp_similarity = float(
            temp_db_result.get(
                "similarity",
                0.0
            )
        )

        temp_action = (
            temp_db_result.get(
                "action",
                "NONE"
            )
        )

        print(
            "Status     :",
            temp_status
        )

        print(
            "Similarity :",
            round(
                temp_similarity,
                4
            )
        )

        print(
            "Action     :",
            temp_action
        )

        if temp_status == "MATCH_FOUND":

            verified_class_id = (
                get_verified_value(
                    temp_db_result,
                    "verified_class_id",
                    "class_id",
                    predicted_class_id
                )
            )

            verified_class_name = (
                get_verified_value(
                    temp_db_result,
                    "verified_class_name",
                    "class_name",
                    predicted_class_name
                )
            )

            verified_category = (
                get_verified_value(
                    temp_db_result,
                    "category",
                    "category",
                    "unknown"
                )
            )

            saved_crop_path = (
                save_crop_for_batch_training(
                    cropped_sign=(
                        cropped_sign
                    ),
                    class_id=(
                        verified_class_id
                    ),
                    class_name=(
                        verified_class_name
                    ),
                    sign_number=(
                        sign_number
                    )
                )
            )

            print(
                "Verified Class ID   :",
                verified_class_id
            )

            print(
                "Verified Class Name :",
                verified_class_name
            )

            print(
                "Category            :",
                verified_category
            )

            if saved_crop_path:
                print(
                    "Training Crop      :",
                    saved_crop_path
                )

                print(
                    "Decision           : "
                    "SAVED_FOR_BATCH_TRAINING"
                )

            else:
                print(
                    "Decision           : "
                    "MATCHED_BUT_CROP_SAVE_FAILED"
                )

            print(
                "Next Step           : "
                "STOP_REMAINING_PIPELINE"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        valid_no_match_statuses = {
            "NO_MATCH",
            "EMPTY_DB"
        }

        if (
            temp_status
            not in valid_no_match_statuses
        ):
            print(
                "Decision   : "
                "STOPPED_TEMP_DB_ERROR"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        print(
            "Decision   : "
            "PASS_TO_NEXT_STEP"
        )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 5: FEATURE EXTRACTION
        # ==================================================

        print_step_header(
            5,
            "Feature Extraction"
        )

        step_start_time = (
            time.perf_counter()
        )

        features = (
            feature_extractor
            .extract_all_features(
                cropped_sign=cropped_sign,
                visual_prominence=(
                    item[
                        "visual_prominence"
                    ]
                )
            )
        )

        if features is None:
            print(
                "Status     : FAILED"
            )

            print(
                "Decision   : STOPPED"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        item["features"] = features

        print(
            "Visual Prominence:",
            f"{item['visual_prominence']:.6f}"
        )

        print(
            "Shape      :",
            features.get(
                "shape",
                "unknown"
            )
        )

        print(
            "Colors     :",
            features.get(
                "colors",
                []
            )
        )

        print(
            "Text       :",
            features.get(
                "text",
                "unknown"
            )
        )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 6: IMPORTANCE SCORE
        # ==================================================

        print_step_header(
            6,
            "Importance Score"
        )

        step_start_time = (
            time.perf_counter()
        )

        item["temp_db_result"] = (
            temp_db_result
        )

        novelty_value = (
            1.0 - cnn_confidence
        )

        novelty_value = max(
            0.0,
            min(
                1.0,
                novelty_value
            )
        )

        importance_score = (
            calculate_importance_score(
                visual_prominence=(
                    item[
                        "visual_prominence"
                    ]
                ),
                novelty_value=(
                    novelty_value
                )
            )
        )

        item["novelty_value"] = round(
            novelty_value,
            4
        )

        item["importance_score"] = (
            importance_score
        )

        item["next_step"] = (
            "RL_AGENT"
        )

        print(
            "CNN Confidence  :",
            f"{cnn_confidence:.4f}"
        )

        print(
            "Novelty Value   :",
            item["novelty_value"]
        )

        print(
            "Importance Score:",
            item["importance_score"]
        )

        print(
            "Next Step       : RL_AGENT"
        )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 7: RL DECISION
        # ==================================================

        print_step_header(
            7,
            "RL Decision"
        )

        step_start_time = (
            time.perf_counter()
        )

        rl_state = build_rl_state(
            importance_score=(
                item[
                    "importance_score"
                ]
            ),

            label_status=(
                classification_status
            ),

            colors=features.get(
                "colors",
                []
            ),

            shape=features.get(
                "shape",
                "unknown"
            ),

            text_status=features.get(
                "text",
                "unknown"
            )
        )

        rl_action, rl_decision = (
            rl_agent.get_decision(
                rl_state
            )
        )

        item["rl_state"] = rl_state
        item["rl_action"] = rl_action
        item["rl_decision"] = (
            rl_decision
        )

        print(
            "State      :",
            rl_state
        )

        print(
            "Decision   :",
            rl_decision
        )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 8: KNOWLEDGE PACKAGE
        # ==================================================

        print_step_header(
            8,
            "Knowledge Package"
        )

        step_start_time = (
            time.perf_counter()
        )

        if rl_action == IGNORE:
            item["next_step"] = (
                "STOPPED_BY_RL_AGENT"
            )

            print(
                "Status           : "
                "NOT_CREATED"
            )

            print(
                "Reason           : "
                "RL_AGENT_DECISION_IGNORE"
            )

            print(
                "Next Step        : "
                "STOPPED_BY_RL_AGENT"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        if rl_action != SHARE:
            print(
                "Status           : "
                "NOT_CREATED"
            )

            print(
                "Reason           : "
                "INVALID_RL_ACTION"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        knowledge_package = (
            knowledge_package_creator
            .create_package(
                sign_id=(
                    f"vehicle_A_sign_"
                    f"{sign_number}"
                ),
                embedding=embedding
            )
        )

        if knowledge_package is None:
            print(
                "Status           : FAILED"
            )

            print(
                "Reason           : "
                "PACKAGE_CREATION_FAILED"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        knowledge_package[
            "embedding_version"
        ] = embedding_version

        knowledge_package[
            "embedding_length"
        ] = len(embedding)

        knowledge_package[
            "predicted_class_id"
        ] = predicted_class_id

        knowledge_package[
            "predicted_class_name"
        ] = predicted_class_name

        knowledge_package[
            "cnn_confidence"
        ] = cnn_confidence

        knowledge_package[
            "label_status"
        ] = classification_status

        item[
            "knowledge_package"
        ] = knowledge_package

        item["next_step"] = (
            "GLOBAL_VERIFICATION"
        )

        shared_knowledge_packages.append(
            knowledge_package
        )

        print(
            "Status            : CREATED"
        )

        print(
            "Vehicle ID        :",
            knowledge_package.get(
                "vehicle_id"
            )
        )

        print(
            "Sign ID           :",
            knowledge_package.get(
                "sign_id"
            )
        )

        print(
            "Shared Data       : "
            "embedding and metadata"
        )

        print(
            "Embedding Version :",
            embedding_version
        )

        print(
            "Embedding Length  :",
            len(embedding)
        )

        print(
            "Next Step         : "
            "GLOBAL_VERIFICATION"
        )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 9: GLOBAL VERIFICATION, REWARD AND QUEUE
        # ==================================================

        print_step_header(
            9,
            "Global Verification"
        )

        step_start_time = (
            time.perf_counter()
        )

        try:
            verification_result = (
                global_verification_server
                .verify_knowledge_package(
                    knowledge_package
                )
            )

        except Exception as error:
            print(
                "Status     : "
                "VERIFICATION_FAILED"
            )

            print(
                "Error      :",
                error
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        if verification_result is None:
            print(
                "Status     : "
                "VERIFICATION_RETURNED_NONE"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        item[
            "verification_result"
        ] = verification_result

        verification_results.append(
            verification_result
        )

        verification_status = (
            verification_result.get(
                "status",
                "UNKNOWN"
            )
        )

        vehicle_id = (
            verification_result.get(
                "target_vehicle"
            )
            or verification_result.get(
                "vehicle_id"
            )
            or knowledge_package.get(
                "vehicle_id"
            )
        )

        reward = float(
            verification_result.get(
                "reward",
                0.0
            )
        )

        print(
            "Status              :",
            verification_status
        )

        print(
            "Vehicle ID          :",
            vehicle_id
        )

        accepted_statuses = {
            "ACCEPTED",
            "VERIFIED",
            "MATCH_FOUND"
        }

        if (
            verification_status
            in accepted_statuses
        ):
            verified_class_id = (
                verification_result.get(
                    "verified_class_id"
                )
            )

            verified_class_name = (
                verification_result.get(
                    "verified_class_name"
                )
            )

            verified_category = (
                verification_result.get(
                    "category",
                    "unknown"
                )
            )

            print(
                "Verified Class ID   :",
                verified_class_id
            )

            print(
                "Verified Class Name :",
                verified_class_name
            )

            print(
                "Category            :",
                verified_category
            )

            print(
                "Reward              :",
                reward
            )

            try:
                queue_result = (
                    broadcast_queue
                    .add_accepted_package(
                        knowledge_package=(
                            knowledge_package
                        ),
                        verification_result=(
                            verification_result
                        )
                    )
                )

                item[
                    "broadcast_queue_result"
                ] = queue_result

                broadcast_queue_results.append(
                    queue_result
                )

                print(
                    "Queue Status        :",
                    queue_result.get(
                        "status",
                        "UNKNOWN"
                    )
                )

                print(
                    "Queue ID            :",
                    queue_result.get(
                        "queue_id",
                        "NOT_AVAILABLE"
                    )
                )

                print(
                    "Pending Packages    :",
                    queue_result.get(
                        "pending_records",
                        0
                    )
                )

            except Exception as error:
                print(
                    "Queue Status        : "
                    "STORE_FAILED"
                )

                print(
                    "Queue Error         :",
                    error
                )

            print(
                "Next Step           :",
                verification_result.get(
                    "next_step",
                    (
                        "SEND_REWARD_AND_"
                        "ADD_TO_BROADCAST"
                    )
                )
            )

        else:
            print(
                "Reward              :",
                reward
            )

            print(
                "Queue Status        : "
                "NOT_ADDED"
            )

            print(
                "Next Step           :",
                verification_result.get(
                    "next_step",
                    (
                        "SEND_REWARD_TO_"
                        "SOURCE_VEHICLE"
                    )
                )
            )

        print_step_time(
            step_start_time
        )

        # ==================================================
        # STEP 10: LOCAL RL TRAINING
        # ==================================================

        print_step_header(
            10,
            "Local RL Training"
        )

        step_start_time = (
            time.perf_counter()
        )

        if vehicle_id != "Vehicle_A":
            print(
                "Status              : "
                "REWARD_NOT_FOR_VEHICLE_A"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        if verification_status == "ERROR":
            print(
                "Status              : "
                "TRAINING_SKIPPED"
            )

            print(
                "Reason              : "
                "GLOBAL_VERIFICATION_ERROR"
            )

            print_step_time(
                step_start_time
            )

            print("-" * 60)

            continue

        try:
            training_result = (
                rl_agent.receive_feedback(
                    state=item["rl_state"],
                    action=item["rl_action"],
                    reward=reward,
                    next_state=(
                        item["rl_state"]
                    ),
                    done=True
                )
            )

            item[
                "rl_training_result"
            ] = training_result

            rl_training_results.append(
                training_result
            )

            print(
                "Status              :",
                training_result.get(
                    "status",
                    "LOCAL_RL_AGENT_UPDATED"
                )
            )

            print(
                "Action              :",
                training_result.get(
                    "action_text",
                    item["rl_decision"]
                )
            )

            print(
                "Reward Used         :",
                training_result.get(
                    "reward",
                    reward
                )
            )

            training_loss = (
                training_result.get(
                    "loss"
                )
            )

            if training_loss is not None:
                print(
                    "Training Loss       :",
                    training_loss
                )

            print(
                "Replay Memory Size  :",
                training_result.get(
                    "replay_memory_size",
                    "unknown"
                )
            )

            print(
                "Training Steps      :",
                training_result.get(
                    "training_steps",
                    "unknown"
                )
            )

            print(
                "Model Saved         : YES"
            )

            print(
                "Model Path          :",
                training_result.get(
                    "model_path",
                    rl_model_path
                )
            )

        except Exception as error:
            print(
                "Status              : "
                "LOCAL_RL_TRAINING_FAILED"
            )

            print(
                "Error               :",
                error
            )

        print_step_time(
            step_start_time
        )

        print("-" * 60)

    # ======================================================
    # PIPELINE SUMMARY
    # ======================================================

    total_time = (
        time.perf_counter()
        - total_start_time
    )

    print("\n" + "=" * 60)
    print("Pipeline completed.")
    print("=" * 60)

    print(
        "Detected signs             :",
        len(detected_signs)
    )

    print(
        "Knowledge packages created :",
        len(
            shared_knowledge_packages
        )
    )

    print(
        "Verification results       :",
        len(
            verification_results
        )
    )

    print(
        "Packages queued            :",
        len(
            broadcast_queue_results
        )
    )

    print(
        "Local RL updates           :",
        len(
            rl_training_results
        )
    )

    print(
        f"Total Pipeline Time        : "
        f"{total_time:.4f} seconds"
    )

    print("=" * 60)

    return verification_results


if __name__ == "__main__":
    main()