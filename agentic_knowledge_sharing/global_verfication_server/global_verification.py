# ==============================
# GLOBAL VERIFICATION SERVER
# ==============================
# This file does 4 things:
# 1. Verify shared knowledge package (YOLO + Embedding)
# 2. Generate RL reward feedback
# 3. Save verified samples for future YOLO retraining
# 4. Maintain embedding database for similarity matching

import os
import json
import shutil
import numpy as np
from ultralytics import YOLO
from sklearn.metrics.pairwise import cosine_similarity


# ==============================
# LOAD GLOBAL MODEL
# ==============================

global_model = YOLO("models/global_all_best.pt")


# ==============================
# VERIFIED DATASET PATHS
# ==============================

verified_dataset_dir = "global_Verfication_server/verified_dataset"

verified_images_dir = os.path.join(verified_dataset_dir, "images")
verified_labels_dir = os.path.join(verified_dataset_dir, "labels")

os.makedirs(verified_images_dir, exist_ok=True)
os.makedirs(verified_labels_dir, exist_ok=True)


# ==============================
# VERIFIED KNOWLEDGE FILE
# ==============================

verified_knowledge_path = "global_Verfication_server/verified_knowledge.json"


# ==============================
# EMBEDDING SIMILARITY THRESHOLD
# ==============================

EMBEDDING_SIMILARITY_THRESHOLD = 0.75  # 75% similarity = match
YOLO_CONFIDENCE_THRESHOLD = 0.70


# ==============================
# CLASS NAMES
# ==============================

CLASS_NAMES = {
    0: "speed limit 20",
    1: "speed limit 30",
    2: "speed limit 50",
    3: "speed limit 60",
    4: "speed limit 70",
    5: "speed limit 80",
    6: "restriction ends 80",
    7: "speed limit 100",
    8: "speed limit 120",
    9: "no overtaking",
    10: "no overtaking trucks",
    11: "priority at next intersection",
    12: "priority road",
    13: "give way",
    14: "stop",
    15: "no traffic both ways",
    16: "no trucks",
    17: "no entry",
    18: "danger",
    19: "bend left",
    20: "bend right",
    21: "bend",
    22: "uneven road",
    23: "slippery road",
    24: "road narrows",
    25: "construction",
    26: "traffic signal",
    27: "pedestrian crossing",
    28: "school crossing",
    29: "cycles crossing",
    30: "snow",
    31: "animals",
    32: "restriction ends",
    33: "go right",
    34: "go left",
    35: "go straight",
    36: "go right or straight",
    37: "go left or straight",
    38: "keep right",
    39: "keep left",
    40: "roundabout",
    41: "restriction ends overtaking",
    42: "restriction ends overtaking trucks"
}


# ==============================
# CLASS CATEGORIES
# ==============================

PROHIBITORY = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 15, 16]
MANDATORY = [33, 34, 35, 36, 37, 38, 39, 40]
DANGER = [11, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
OTHER = [6, 12, 13, 14, 17, 32, 41, 42]


def get_category(class_id):
    if class_id in PROHIBITORY:
        return "prohibitory"
    if class_id in MANDATORY:
        return "mandatory"
    if class_id in DANGER:
        return "danger"
    if class_id in OTHER:
        return "other"
    return "unknown"


def get_global_score(category):
    if category == "danger":
        return 9
    if category in ["prohibitory", "mandatory"]:
        return 7
    if category == "other":
        return 5
    return 0


# ==============================
# EMBEDDING DATABASE FUNCTIONS
# ==============================

def load_embedding_database():
    """Load all verified embeddings for similarity matching"""
    knowledge_data = load_verified_knowledge()
    
    embeddings_db = []
    for record in knowledge_data:
        if "embedding" in record and record["embedding"]:
            embeddings_db.append({
                "embedding": np.array(record["embedding"]),
                "class_id": record["global_class_id"],
                "sign_name": record["sign_name"],
                "category": record["category"],
                "global_score": record["global_score"],
                "global_confidence": record.get("global_confidence", 1.0)
            })
    
    return embeddings_db


def find_similar_embedding(query_embedding, embeddings_db, threshold=EMBEDDING_SIMILARITY_THRESHOLD):
    """Find the most similar embedding in the database"""
    if not embeddings_db or query_embedding is None:
        return None, 0.0
    
    query_embedding = np.array(query_embedding).reshape(1, -1)
    
    best_match = None
    best_similarity = 0.0
    
    for record in embeddings_db:
        known_embedding = record["embedding"].reshape(1, -1)
        similarity = cosine_similarity(query_embedding, known_embedding)[0][0]
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = record
    
    if best_similarity >= threshold:
        return best_match, best_similarity
    
    return None, best_similarity


# ==============================
# YOLO VERIFICATION (FULL IMAGE)
# ==============================

def verify_with_yolo(package):
    """Verify using YOLO on the full image"""
    image_path = package["image_path"]
    vehicle_bbox = package.get("bbox")  # Vehicle A's bounding box
    
    results = global_model(image_path)
    
    best_confidence = 0.0
    best_class_id = None
    best_bbox = None
    
    from shared.iou_utils import calculate_iou
    
    for result in results:
        for box in result.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            global_bbox = box.xyxy[0].tolist()
            
            # If we have vehicle's bbox, check IoU overlap
            if vehicle_bbox:
                iou = calculate_iou(vehicle_bbox, global_bbox)
                # Only consider if overlap > 30% (same sign)
                if iou < 0.30:
                    continue
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_class_id = class_id
                best_bbox = global_bbox
    
    if best_class_id is None:
        return {
            "success": False,
            "reason": "YOLO could not identify sign",
            "confidence": 0
        }
    
    category = get_category(best_class_id)
    sign_name = CLASS_NAMES.get(best_class_id, "unknown")
    global_score = get_global_score(category)
    
    if best_confidence >= YOLO_CONFIDENCE_THRESHOLD:
        return {
            "success": True,
            "verification_status": "VERIFIED",
            "global_class_id": best_class_id,
            "sign_name": sign_name,
            "category": category,
            "global_confidence": round(best_confidence, 4),
            "global_score": global_score,
            "method": "YOLO"
        }
    else:
        return {
            "success": False,
            "reason": f"Low YOLO confidence: {best_confidence:.2f} < {YOLO_CONFIDENCE_THRESHOLD}",
            "confidence": best_confidence,
            "global_class_id": best_class_id,
            "sign_name": sign_name,
            "category": category,
            "global_score": 0
        }


# ==============================
# EMBEDDING VERIFICATION
# ==============================

def verify_with_embedding(package, embeddings_db):
    """Verify using embedding similarity against known database"""
    query_embedding = package.get("embedding")
    
    if query_embedding is None:
        return {
            "success": False,
            "reason": "No embedding provided in package"
        }
    
    best_match, similarity = find_similar_embedding(query_embedding, embeddings_db)
    
    if best_match:
        return {
            "success": True,
            "verification_status": "VERIFIED",
            "global_class_id": best_match["class_id"],
            "sign_name": best_match["sign_name"],
            "category": best_match["category"],
            "global_confidence": round(similarity, 4),
            "global_score": best_match["global_score"],
            "method": "EMBEDDING",
            "similarity": similarity
        }
    else:
        return {
            "success": False,
            "reason": f"No matching embedding found (best similarity: {similarity:.2f})",
            "similarity": similarity
        }


# ==============================
# HYBRID VERIFICATION (YOLO + EMBEDDING)
# ==============================

def verify_knowledge_package(package):
    """
    Hybrid verification using both YOLO and Embedding similarity
    
    Strategy:
    1. Try YOLO verification first (works well for images)
    2. If YOLO fails, try embedding similarity against verified database
    3. Return best available result
    """
    
    # Load embedding database
    embeddings_db = load_embedding_database()
    
    # METHOD 1: YOLO Verification (Primary)
    yolo_result = verify_with_yolo(package)
    
    if yolo_result["success"]:
        print(f"  ✓ YOLO verification successful: {yolo_result['sign_name']} (conf={yolo_result['global_confidence']})")
        
        # Update package with YOLO results
        package["verification_status"] = yolo_result["verification_status"]
        package["global_class_id"] = yolo_result["global_class_id"]
        package["sign_name"] = yolo_result["sign_name"]
        package["category"] = yolo_result["category"]
        package["global_confidence"] = yolo_result["global_confidence"]
        package["global_score"] = yolo_result["global_score"]
        package["use_for_training"] = True
        package["method"] = "YOLO"
        package["reason"] = f"Verified by YOLO (conf={yolo_result['global_confidence']})"
        
        # Save to database
        update_verified_knowledge_file(package)
        save_verified_training_sample(package)
        
        return package
    
    print(f"  ✗ YOLO verification failed: {yolo_result.get('reason', 'Unknown')}")
    
    # METHOD 2: Embedding Verification (Backup)
    embedding_result = verify_with_embedding(package, embeddings_db)
    
    if embedding_result["success"]:
        print(f"  ✓ Embedding verification successful: {embedding_result['sign_name']} (sim={embedding_result['similarity']:.2f})")
        
        # Update package with embedding results
        package["verification_status"] = embedding_result["verification_status"]
        package["global_class_id"] = embedding_result["global_class_id"]
        package["sign_name"] = embedding_result["sign_name"]
        package["category"] = embedding_result["category"]
        package["global_confidence"] = embedding_result["global_confidence"]
        package["global_score"] = embedding_result["global_score"]
        package["use_for_training"] = True
        package["method"] = "EMBEDDING"
        package["reason"] = f"Verified by embedding similarity (sim={embedding_result['similarity']:.2f})"
        
        # Save to database
        update_verified_knowledge_file(package)
        save_verified_training_sample(package)
        
        return package
    
    print(f"  ✗ Embedding verification failed: {embedding_result.get('reason', 'Unknown')}")
    
    # METHOD 3: Both Failed - REJECT
    package["verification_status"] = "REJECTED"
    package["global_score"] = 0
    package["use_for_training"] = False
    package["method"] = "NONE"
    package["reason"] = f"Verification failed: YOLO - {yolo_result.get('reason', 'N/A')}, Embedding - {embedding_result.get('reason', 'N/A')}"
    
    return package


# ==============================
# RL REWARD
# ==============================

def get_rl_reward(verified_package):
    if verified_package["verification_status"] == "REJECTED":
        return -5
    return verified_package["global_score"]


# ==============================
# LOAD / SAVE VERIFIED KNOWLEDGE
# ==============================

def load_verified_knowledge():
    if os.path.exists(verified_knowledge_path):
        if os.path.getsize(verified_knowledge_path) == 0:
            return []
        with open(verified_knowledge_path, "r") as f:
            return json.load(f)
    return []


def save_verified_knowledge(data):
    with open(verified_knowledge_path, "w") as f:
        json.dump(data, f, indent=4)


# ==============================
# SAVE VERIFIED SAMPLE
# ==============================

def save_verified_training_sample(verified_package):
    if verified_package["verification_status"] != "VERIFIED":
        return
    
    if verified_package["use_for_training"] is not True:
        return
    
    cropped_sign_path = verified_package["cropped_sign_path"]
    class_id = verified_package["global_class_id"]
    package_id = verified_package["package_id"]
    
    image_filename = f"{package_id}.jpg"
    label_filename = f"{package_id}.txt"
    
    saved_image_path = os.path.join(verified_images_dir, image_filename)
    saved_label_path = os.path.join(verified_labels_dir, label_filename)
    
    # Copy cropped sign image
    shutil.copy(cropped_sign_path, saved_image_path)
    
    # YOLO format: class_id x_center y_center width height
    x_center = 0.5
    y_center = 0.5
    width = 1.0
    height = 1.0
    
    with open(saved_label_path, "w") as f:
        f.write(f"{class_id} {x_center} {y_center} {width} {height}")
    
    print(f"  ✓ Saved training sample: {package_id}.jpg")


# ==============================
# UPDATE VERIFIED KNOWLEDGE JSON
# ==============================

def update_verified_knowledge_file(verified_package):
    if verified_package["verification_status"] != "VERIFIED":
        return
    
    knowledge_data = load_verified_knowledge()
    
    # Check if already exists (avoid duplicates)
    for existing in knowledge_data:
        if existing.get("package_id") == verified_package["package_id"]:
            print(f"  ⚠ Package {verified_package['package_id']} already in database, skipping")
            return
    
    record = {
        "package_id": verified_package["package_id"],
        "vehicle_id": verified_package["vehicle_id"],
        "timestamp": verified_package.get("timestamp", 0),
        "global_class_id": verified_package["global_class_id"],
        "sign_name": verified_package["sign_name"],
        "category": verified_package["category"],
        "color": verified_package["color"],
        "shape": verified_package["shape"],
        "importance_score": verified_package["importance_score"],
        "global_confidence": verified_package["global_confidence"],
        "global_score": verified_package["global_score"],
        "cropped_sign_path": verified_package["cropped_sign_path"],
        "embedding": verified_package["embedding"],
        "method": verified_package.get("method", "UNKNOWN"),
        "use_for_training": verified_package["use_for_training"]
    }
    
    knowledge_data.append(record)
    save_verified_knowledge(knowledge_data)
    print(f"  ✓ Added to verified knowledge database")


# ==============================
# SIMULATED SEND TO GLOBAL SERVER
# ==============================

def send_to_global_server(package):
    print("\n" + "=" * 60)
    print("KNOWLEDGE PACKAGE SENT TO GLOBAL VERIFICATION SERVER")
    print("=" * 60)
    print(f"  Package ID: {package['package_id']}")
    print(f"  Vehicle: {package['vehicle_id']}")
    print(f"  Sign: {package['color']} {package['shape']}")
    print(f"  Importance: {package['importance_score']}")
    print("-" * 60)
    
    verified_package = verify_knowledge_package(package)
    
    rl_reward = get_rl_reward(verified_package)
    
    print("-" * 60)
    print("VERIFICATION RESULT:")
    print(f"  Status: {verified_package['verification_status']}")
    print(f"  Method: {verified_package.get('method', 'N/A')}")
    print(f"  RL Reward: {rl_reward}")
    if verified_package['verification_status'] == 'VERIFIED':
        print(f"  Sign: {verified_package.get('sign_name', 'Unknown')}")
        print(f"  Category: {verified_package.get('category', 'Unknown')}")
        print(f"  Global Score: {verified_package['global_score']}")
    print(f"  Reason: {verified_package['reason']}")
    print("=" * 60)
    
    return verified_package, rl_reward