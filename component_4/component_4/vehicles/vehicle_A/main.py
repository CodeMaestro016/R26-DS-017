# ==========================================================
# vehicles/vehicle_A/main.py
# ==========================================================

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
import time
import threading

import cv2


# ==========================================================
# PROJECT PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ==========================================================
# CONFIGURATION
# ==========================================================

VEHICLE_ID = "Vehicle_A"

GLOBAL_DATABASE_PATH = os.path.join(
    PROJECT_ROOT,
    "global_verification_server",
    "database",
    "global_verification_db.pkl"
)

GLOBAL_SIMILARITY_THRESHOLD = 0.70

BATCH_TRAINING_DIR = os.path.join(
    CURRENT_DIR,
    "data",
    "batch_training"
)

rl_model_path = os.path.join(
    CURRENT_DIR,
    "models",
    "dqn_rl_agent.pth"
)


# ==========================================================
# PIPELINE COMPONENTS (loaded once via initialize_pipeline)
# ==========================================================

cnn_classifier = None
embedding_extractor = None
temp_db_checker = None
feature_extractor = None
rl_agent = None
knowledge_package_creator = None
global_verification_server = None
broadcast_queue = None
embedding_version = None

_initialized = False
_init_lock = threading.Lock()


# ==========================================================
# RUNTIME STATISTICS
# ==========================================================

total_pipeline_runs = 0
statistics_lock = threading.Lock()


# ==========================================================
# STEP HEADER HELPERS
# ==========================================================

def print_step_header(step_number, step_name):
    print(f"\n========== STEP {step_number}: {step_name} ==========")


def print_step_time(start_time):
    elapsed_time = time.perf_counter() - start_time
    print(f"Step Time  : {elapsed_time:.4f} seconds")


# ==========================================================
# VERIFIED VALUE HELPER
# ==========================================================

def get_verified_value(result, direct_key, nested_key=None, default=None):
    if not isinstance(result, dict):
        return default
    if result.get(direct_key) is not None:
        return result.get(direct_key)
    matched_record = result.get("matched_record")
    if isinstance(matched_record, dict) and nested_key is not None:
        return matched_record.get(nested_key, default)
    metadata = result.get("metadata")
    if isinstance(metadata, dict) and nested_key is not None:
        return metadata.get(nested_key, default)
    return default


# ==========================================================
# SAVE CROP FOR BATCH TRAINING
# ==========================================================

def save_crop_for_batch_training(cropped_sign, class_id, class_name, sign_number):
    if cropped_sign is None:
        return None
    class_folder_name = f"class_{class_id}" if class_id is not None else "class_unknown"
    class_directory = os.path.join(BATCH_TRAINING_DIR, class_folder_name)
    os.makedirs(class_directory, exist_ok=True)
    safe_class_name = str(class_name or "unknown").replace(" ", "_")
    timestamp = int(time.time() * 1000)
    file_name = f"vehicle_A_{safe_class_name}_sign_{sign_number}_{timestamp}.jpg"
    save_path = os.path.join(class_directory, file_name)
    try:
        saved = cv2.imwrite(save_path, cropped_sign)
    except Exception as error:
        print("Crop save error:", error)
        return None
    if not saved:
        return None
    return save_path


# ==========================================================
# CREATE GLOBAL SERVER
# ==========================================================

def create_global_server():
    if not os.path.exists(GLOBAL_DATABASE_PATH):
        raise FileNotFoundError(f"Global verification database not found: {GLOBAL_DATABASE_PATH}")
    from global_verification_server.global_verification import GlobalVerificationServer
    try:
        return GlobalVerificationServer(database_path=GLOBAL_DATABASE_PATH, similarity_threshold=GLOBAL_SIMILARITY_THRESHOLD)
    except TypeError:
        return GlobalVerificationServer(similarity_threshold=GLOBAL_SIMILARITY_THRESHOLD)


# ==========================================================
# INITIALIZE PIPELINE (idempotent - safe to call more than once)
# ==========================================================

def initialize_pipeline():
    global cnn_classifier, embedding_extractor, temp_db_checker, feature_extractor
    global rl_agent, knowledge_package_creator, global_verification_server, broadcast_queue, embedding_version
    global _initialized

    with _init_lock:
        if _initialized:
            print("[Vehicle_A] Pipeline already initialized, reusing.")
            return

        print("\n" + "=" * 70)
        print("INITIALIZING VEHICLE A PIPELINE")
        print("=" * 70)

        print("\n[1/7] Loading CNN...")
        from src.cnn_classifier import VehicleACNN
        cnn_classifier = VehicleACNN()
        print("CNN ready.")

        print("\n[2/7] Loading Embedding Extractor...")
        from src.embedding_extractor import EmbeddingExtractor
        embedding_extractor = EmbeddingExtractor()
        embedding_version = embedding_extractor.get_embedding_version()
        print("Embedding version:", embedding_version)

        print("\n[3/7] Loading Temporary DB...")
        from src.temp_db_checker import TempDBChecker
        temp_db_checker = TempDBChecker()
        print("Temporary DB ready.")

        print("\n[4/7] Loading Feature Extractor...")
        from src.feature_extraction import FeatureExtractor
        feature_extractor = FeatureExtractor()
        print("Feature extractor ready.")

        print("\n[5/7] Loading RL Agent...")
        from src.rl_agent import VehicleARLAgent
        rl_agent = VehicleARLAgent(model_path=rl_model_path)
        print("RL agent ready.")

        print("\n[6/7] Loading Knowledge Package + Global...")
        from src.knowledge_package import KnowledgePackageCreator
        knowledge_package_creator = KnowledgePackageCreator(vehicle_id=VEHICLE_ID)
        global_verification_server = create_global_server()
        from global_verification_server.broadcast_queue import BroadcastQueue
        broadcast_queue = BroadcastQueue()
        print("Knowledge package ready.")
        print("Global verification ready.")
        print("Broadcast queue ready.")

        print("\n[7/7] Pipeline initialization complete.")
        print("=" * 70)

        _initialized = True


# ==========================================================
# PROCESS ONE DETECTED SIGN
# ==========================================================

def process_detected_sign(sign_data, sign_number, frame_number):
    global total_pipeline_runs

    steps = []

    if not _initialized:
        print("[Vehicle_A] ERROR: pipeline not initialized. Call initialize_pipeline() first.")
        return None

    cropped_sign = sign_data.get("cropped_sign")
    bbox = sign_data.get("bbox")
    visual_prominence = float(sign_data.get("visual_prominence", 0.0))
    yolo_confidence = float(sign_data.get("yolo_confidence", 0.0))

    print("\n" + "#" * 70)
    print(f"LIVE SIGN #{sign_number}")
    print(f"Frame Number: {frame_number}")
    print(f"YOLO Confidence: {round(yolo_confidence, 4)}")
    print(f"Bounding Box: {bbox}")
    print(f"Visual Prominence: {round(visual_prominence, 6)}")
    print("#" * 70)

    steps.append({
        "step": 1,
        "name": "YOLO Detection",
        "status": "DONE",
        "yolo_confidence": round(yolo_confidence, 4),
        "bbox": bbox,
    })

    if cropped_sign is None or cropped_sign.size == 0:
        print("INVALID CROPPED SIGN")
        return None

    # STEP 2: CNN Classification
    print_step_header(2, "CNN Classification")
    step_start_time = time.perf_counter()
    try:
        classification = cnn_classifier.classify(cropped_sign)
    except Exception as error:
        print("CNN ERROR:", error)
        return None

    if classification is None:
        print("Status: FAILED")
        return None

    predicted_class_id = classification.get("class_id")
    predicted_class_name = classification.get("class_name")
    cnn_confidence = float(classification.get("confidence", 0.0))
    classification_status = classification.get("status", "UNKNOWN")
    classification_action = classification.get("action", "CONTINUE")

    print(f"Class ID: {predicted_class_id}")
    print(f"Class Name: {predicted_class_name}")
    print(f"Confidence: {round(cnn_confidence, 4)}")
    print(f"Status: {classification_status}")
    print(f"Action: {classification_action}")
    print_step_time(step_start_time)

    steps.append({
        "step": 2,
        "name": "CNN Classification",
        "status": classification_status,
        "class_name": predicted_class_name,
        "confidence": round(cnn_confidence, 4),
    })

    if classification_action == "IGNORE":
        print("Decision: KNOWN_SIGN_IGNORED")
        return {
            "status": "KNOWN_SIGN_IGNORED", "frame_number": frame_number, "bbox": bbox,
            "class_id": predicted_class_id, "class_name": predicted_class_name,
            "cnn_confidence": cnn_confidence, "steps": steps,
        }

    # STEP 3: Embedding
    print_step_header(3, "Embedding Extraction")
    step_start_time = time.perf_counter()
    try:
        embedding = embedding_extractor.extract_embedding(cropped_sign)
    except Exception as error:
        print("Embedding ERROR:", error)
        return None

    if embedding is None:
        print("Status: FAILED")
        return None

    print(f"Status: COMPLETED")
    print(f"Embedding Version: {embedding_version}")
    print(f"Embedding Length: {len(embedding)}")
    print_step_time(step_start_time)

    steps.append({
        "step": 3,
        "name": "Embedding Extraction",
        "status": "COMPLETED",
        "embedding_length": len(embedding),
    })

    item = {
        "cropped_sign": cropped_sign,
        "bbox": bbox,
        "visual_prominence": visual_prominence,
        "yolo_confidence": yolo_confidence,
        "classification": classification,
        "embedding": embedding,
        "embedding_version": embedding_version,
        "frame_number": frame_number
    }

    # STEP 4: Temporary DB Check
    print_step_header(4, "Temporary DB Check")
    step_start_time = time.perf_counter()
    try:
        temp_db_result = temp_db_checker.process_item(item)
    except Exception as error:
        print("Temporary DB ERROR:", error)
        return None

    if temp_db_result is None:
        temp_db_result = {"status": "ERROR", "similarity": 0.0, "action": "STOP"}

    temp_status = temp_db_result.get("status", "ERROR")
    temp_similarity = float(temp_db_result.get("similarity", 0.0))
    temp_action = temp_db_result.get("action", "NONE")

    print(f"Status: {temp_status}")
    print(f"Similarity: {round(temp_similarity, 4)}")
    print(f"Action: {temp_action}")

    item["temp_db_result"] = temp_db_result

    steps.append({
        "step": 4,
        "name": "Temporary DB Check",
        "status": temp_status,
        "similarity": round(temp_similarity, 4),
    })

    if temp_status == "MATCH_FOUND":
        verified_class_id = get_verified_value(temp_db_result, "verified_class_id", "class_id", predicted_class_id)
        verified_class_name = get_verified_value(temp_db_result, "verified_class_name", "class_name", predicted_class_name)
        verified_category = get_verified_value(temp_db_result, "category", "category", "unknown")
        saved_crop_path = save_crop_for_batch_training(cropped_sign, verified_class_id, verified_class_name, sign_number)

        print(f"Verified Class ID: {verified_class_id}")
        print(f"Verified Class Name: {verified_class_name}")
        print(f"Category: {verified_category}")
        if saved_crop_path:
            print(f"Training Crop: {saved_crop_path}")
            print("Decision: SAVED_FOR_BATCH_TRAINING")
        else:
            print("Decision: MATCHED_CROP_SAVE_FAILED")
        print_step_time(step_start_time)
        return {
            "status": "MATCH_FOUND",
            "frame_number": frame_number,
            "bbox": bbox,
            "class_id": verified_class_id,
            "class_name": verified_class_name,
            "category": verified_category,
            "cnn_confidence": cnn_confidence,
            "temp_similarity": temp_similarity,
            "steps": steps,
        }

    valid_no_match_statuses = {"NO_MATCH", "EMPTY_DB"}
    if temp_status not in valid_no_match_statuses:
        print("Decision: STOPPED_TEMP_DB_ERROR")
        return None

    print("Decision: PASS_TO_NEXT_STEP")
    print_step_time(step_start_time)

    # STEP 5: Feature Extraction
    print_step_header(5, "Feature Extraction")
    step_start_time = time.perf_counter()
    try:
        features = feature_extractor.extract_all_features(cropped_sign=cropped_sign, visual_prominence=visual_prominence)
    except Exception as error:
        print("Feature extraction ERROR:", error)
        return None

    if features is None:
        print("Status: FAILED")
        return None

    item["features"] = features
    print(f"Visual Prominence: {visual_prominence:.6f}")
    print(f"Shape: {features.get('shape', 'unknown')}")
    print(f"Colors: {features.get('colors', [])}")
    print(f"Text: {features.get('text', 'unknown')}")
    print_step_time(step_start_time)

    steps.append({
        "step": 5,
        "name": "Feature Extraction",
        "status": "COMPLETED",
        "shape": features.get("shape", "unknown"),
        "colors": features.get("colors", []),
    })

    # STEP 6: Importance Score
    print_step_header(6, "Importance Score")
    step_start_time = time.perf_counter()
    from src.importance_score import calculate_importance_score
    novelty_value = max(0.0, min(1.0, 1.0 - cnn_confidence))
    importance_score = calculate_importance_score(visual_prominence=visual_prominence, novelty_value=novelty_value)

    item["novelty_value"] = round(novelty_value, 4)
    item["importance_score"] = importance_score

    print(f"CNN Confidence: {cnn_confidence:.4f}")
    print(f"Novelty Value: {item['novelty_value']}")
    print(f"Importance Score: {item['importance_score']}")
    print("Next Step: RL_AGENT")
    print_step_time(step_start_time)

    steps.append({
        "step": 6,
        "name": "Importance Score",
        "status": "COMPLETED",
        "importance_score": item["importance_score"],
    })

    # STEP 7: RL Decision
    print_step_header(7, "RL Decision")
    step_start_time = time.perf_counter()
    from src.rl_agent import build_rl_state, SHARE, IGNORE
    rl_state = build_rl_state(
        importance_score=item["importance_score"],
        label_status=classification_status,
        colors=features.get("colors", []),
        shape=features.get("shape", "unknown"),
        text_status=features.get("text", "unknown")
    )

    try:
        rl_action, rl_decision = rl_agent.get_decision(rl_state)
    except Exception as error:
        print("RL decision ERROR:", error)
        return None

    item["rl_state"] = rl_state
    item["rl_action"] = rl_action
    item["rl_decision"] = rl_decision

    print(f"State: {rl_state}")
    print(f"Action: {rl_action}")
    print(f"Decision: {rl_decision}")
    print_step_time(step_start_time)

    steps.append({
        "step": 7,
        "name": "RL Decision",
        "status": "COMPLETED",
        "decision": rl_decision,
    })

    # STEP 8: Knowledge Package
    print_step_header(8, "Knowledge Package")
    step_start_time = time.perf_counter()

    if rl_action == IGNORE:
        print("Status: NOT_CREATED")
        print("Reason: RL_AGENT_DECISION_IGNORE")
        print_step_time(step_start_time)
        return {
            "status": "IGNORED_BY_RL", "frame_number": frame_number, "bbox": bbox,
            "class_id": predicted_class_id, "class_name": predicted_class_name,
            "cnn_confidence": cnn_confidence, "rl_decision": rl_decision,
            "steps": steps,
        }

    if rl_action != SHARE:
        print("Status: NOT_CREATED")
        print("Reason: INVALID_RL_ACTION")
        return None

    try:
        knowledge_package = knowledge_package_creator.create_package(
            sign_id=f"vehicle_A_live_frame_{frame_number}_sign_{sign_number}",
            embedding=embedding
        )
    except Exception as error:
        print("Knowledge package ERROR:", error)
        return None

    if knowledge_package is None:
        print("Status: FAILED")
        return None

    knowledge_package["embedding_version"] = embedding_version
    knowledge_package["embedding_length"] = len(embedding)
    knowledge_package["predicted_class_id"] = predicted_class_id
    knowledge_package["predicted_class_name"] = predicted_class_name
    knowledge_package["cnn_confidence"] = cnn_confidence
    knowledge_package["label_status"] = classification_status
    knowledge_package["yolo_confidence"] = yolo_confidence
    knowledge_package["visual_prominence"] = visual_prominence
    knowledge_package["frame_number"] = frame_number

    item["knowledge_package"] = knowledge_package

    print(f"Status: CREATED")
    print(f"Vehicle ID: {knowledge_package.get('vehicle_id')}")
    print(f"Sign ID: {knowledge_package.get('sign_id')}")
    print(f"Embedding Version: {embedding_version}")
    print(f"Embedding Length: {len(embedding)}")
    print("Next Step: GLOBAL_VERIFICATION")
    print_step_time(step_start_time)

    steps.append({
        "step": 8,
        "name": "Knowledge Package",
        "status": "CREATED",
    })

    # STEP 9: Global Verification
    print_step_header(9, "Global Verification")
    step_start_time = time.perf_counter()

    try:
        verification_result = global_verification_server.verify_knowledge_package(knowledge_package)
    except Exception as error:
        print("Verification ERROR:", error)
        return None

    if verification_result is None:
        print("Verification returned None.")
        return None

    item["verification_result"] = verification_result
    verification_status = verification_result.get("status", "UNKNOWN")
    vehicle_id = verification_result.get("target_vehicle") or verification_result.get("vehicle_id") or knowledge_package.get("vehicle_id")
    reward = float(verification_result.get("reward", 0.0))

    print(f"Status: {verification_status}")
    print(f"Vehicle ID: {vehicle_id}")

    accepted_statuses = {"ACCEPTED", "VERIFIED", "MATCH_FOUND"}

    steps.append({
        "step": 9,
        "name": "Global Verification",
        "status": verification_status,
        "similarity": round(float(verification_result.get("similarity", 0.0)), 4),
        "reward": reward,
    })

    if verification_status in accepted_statuses:
        verified_class_id = verification_result.get("verified_class_id")
        verified_class_name = verification_result.get("verified_class_name")
        verified_category = verification_result.get("category", "unknown")

        print(f"Verified Class ID: {verified_class_id}")
        print(f"Verified Class Name: {verified_class_name}")
        print(f"Category: {verified_category}")
        print(f"Reward: {reward}")

        try:
            queue_result = broadcast_queue.add_accepted_package(knowledge_package=knowledge_package, verification_result=verification_result)
            item["broadcast_queue_result"] = queue_result
            print(f"Queue Status: {queue_result.get('status', 'UNKNOWN')}")
            print(f"Queue ID: {queue_result.get('queue_id', 'NOT_AVAILABLE')}")
            print(f"Pending Packages: {queue_result.get('pending_records', 0)}")
        except Exception as error:
            print("Queue ERROR:", error)
    else:
        print(f"Reward: {reward}")
        print("Queue Status: NOT_ADDED")

    print_step_time(step_start_time)

    # STEP 10: Local RL Training
    print_step_header(10, "Local RL Training")
    step_start_time = time.perf_counter()

    if vehicle_id != VEHICLE_ID:
        print("Status: REWARD_NOT_FOR_VEHICLE_A")
        steps.append({"step": 10, "name": "Local RL Training", "status": "NOT_FOR_THIS_VEHICLE"})
        return {
            "status": "COMPLETED", "frame_number": frame_number, "bbox": bbox,
            "verification": verification_result, "steps": steps,
            "class_name": predicted_class_name, "cnn_confidence": cnn_confidence,
        }

    if verification_status == "ERROR":
        print("Status: TRAINING_SKIPPED")
        steps.append({"step": 10, "name": "Local RL Training", "status": "SKIPPED"})
        return None

    training_status_text = "SKIPPED"
    try:
        training_result = rl_agent.receive_feedback(
            state=item["rl_state"],
            action=item["rl_action"],
            reward=reward,
            next_state=item["rl_state"],
            done=True
        )
        item["rl_training_result"] = training_result
        training_status_text = training_result.get("status", "LOCAL_RL_AGENT_UPDATED")
        print(f"Training Status: {training_status_text}")
        print(f"Action: {training_result.get('action_text', item['rl_decision'])}")
        print(f"Reward Used: {training_result.get('reward', reward)}")
        print(f"Replay Memory Size: {training_result.get('replay_memory_size', 'unknown')}")
        print(f"Training Steps: {training_result.get('training_steps', 'unknown')}")
        print("Model Saved: YES")
    except Exception as error:
        print("LOCAL RL TRAINING ERROR:", error)

    print_step_time(step_start_time)

    steps.append({
        "step": 10,
        "name": "Local RL Training",
        "status": training_status_text,
    })

    with statistics_lock:
        total_pipeline_runs += 1

    return {
        "status": verification_status,
        "vehicle_id": VEHICLE_ID,
        "frame_number": frame_number,
        "bbox": bbox,
        "yolo_confidence": yolo_confidence,
        "class_id": predicted_class_id,
        "class_name": predicted_class_name,
        "cnn_confidence": cnn_confidence,
        "importance_score": importance_score,
        "rl_action": rl_action,
        "rl_decision": rl_decision,
        "reward": reward,
        "verification": verification_result,
        "steps": steps,
    }


# ==========================================================
# OFFLINE TEST MODE (kept for standalone testing, unaffected)
# ==========================================================

def run_offline_test():
    from src.detection import process_all_images
    print("\n" + "=" * 70)
    print("OFFLINE VEHICLE A TEST")
    print("=" * 70)
    signs = process_all_images()
    print(f"Detected signs: {len(signs)}")
    print("=" * 70)


if __name__ == "__main__":
    initialize_pipeline()
    run_offline_test()