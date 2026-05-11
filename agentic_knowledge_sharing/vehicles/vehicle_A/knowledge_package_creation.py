import time


# ==============================
# KNOWLEDGE PACKAGE CREATION
# ==============================
# Created only when agent decides SHARE.
# Embedding is included for global verification.

def create_knowledge_package(item):
    package = {
        "package_id": f"{item['vehicle_id']}_{item['sign_number']}_{int(time.time())}",

        "vehicle_id": item["vehicle_id"],
        "timestamp": item["timestamp"],

        "knowledge_type": item["knowledge_type"],
        "importance_score": item["importance_score"],

        "color": item["color"],
        "shape": item["shape"],
        "cropped_sign_path": item["cropped_sign_path"],

        # Used by global model to verify/identify sign
        "embedding": item["embedding"],

        "detector_confidence": item["detector_confidence"],
        "vehicle_confidence": item["vehicle_A_confidence"],

        "bbox": item["generic_bbox"],
        "image_path": item["image_path"],

        "status": "PENDING_GLOBAL_VERIFICATION"
    }

    return package