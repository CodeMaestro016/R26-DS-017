# Vehicle A knowledge identification logic

import time
import json
import os
from ultralytics import YOLO

from shared.iou_utils import calculate_iou
from shared.feature_extraction import extract_sign_features


# ==============================
# VEHICLE INFO
# ==============================

vehicle_id = "Vehicle_A"


# ==============================
# MODEL PATHS
# ==============================

generic_model_path = "models/generic_traffic_sign_detector_best.pt"
vehicle_A_model_path = "models/vehicle_A_prohibitory_best.pt"


# ==============================
# LOAD MODELS
# ==============================

generic_detector = YOLO(generic_model_path)
vehicle_A_model = YOLO(vehicle_A_model_path)


# ==============================
# PERSISTENT FREQUENCY TABLE
# ==============================
# Stored in frequency_table_A.json

frequency_table_path = "vehicles/vehicle_A/frequency_table_A.json"


def load_frequency_table():
    """Load frequency table from JSON file"""
    if os.path.exists(frequency_table_path):
        try:
            with open(frequency_table_path, 'r') as f:
                table = json.load(f)
                return table
        except:
            return {}
    return {}


def save_frequency_table(frequency_table):
    """Save frequency table to JSON file"""
    with open(frequency_table_path, 'w') as f:
        json.dump(frequency_table, f, indent=2)


# Load frequency table at startup
frequency_table = load_frequency_table()


# ==============================
# CLASSIFY KNOWLEDGE
# ==============================

def classify_knowledge(confidence):

    if confidence >= 0.70:
        knowledge_type = "KNOWN"

    elif confidence >= 0.30:
        knowledge_type = "RARE"

    else:
        knowledge_type = "NEW"

    novelty_value = round(1 - confidence, 4)

    return knowledge_type, novelty_value


# ==============================
# IDENTIFY VEHICLE A KNOWLEDGE
# ==============================

def identify_vehicle_A_knowledge(image_path):

    outputs = []

    # Generic detector finds all traffic signs
    generic_results = generic_detector(image_path)

    # Vehicle A model finds signs it knows
    vehicle_A_results = vehicle_A_model(image_path, conf=0.10)

    vehicle_A_boxes = []

    for vr in vehicle_A_results:
        for vbox in vr.boxes:

            v_bbox = vbox.xyxy[0].tolist()
            v_bbox = [int(x) for x in v_bbox]

            vehicle_A_boxes.append({
                "bbox": v_bbox,
                "confidence": float(vbox.conf[0]),
                "class_id": int(vbox.cls[0])
            })

    for gr in generic_results:

        if len(gr.boxes) == 0:
            print("No traffic sign detected")
            return []

        for idx, gbox in enumerate(gr.boxes):

            g_bbox = gbox.xyxy[0].tolist()
            g_bbox = [int(x) for x in g_bbox]

            detector_confidence = float(gbox.conf[0])

            # Extract color, shape, embedding
            sign_features = extract_sign_features(image_path, g_bbox)

            best_iou = 0
            best_vehicle_A_confidence = 0.0
            matched_class_id = None

            # Match generic sign with Vehicle A detection
            for vb in vehicle_A_boxes:
                iou = calculate_iou(g_bbox, vb["bbox"])

                if iou > best_iou:
                    best_iou = iou
                    best_vehicle_A_confidence = vb["confidence"]
                    matched_class_id = vb["class_id"]

            if best_iou >= 0.30:
                vehicle_A_confidence = best_vehicle_A_confidence
            else:
                vehicle_A_confidence = 0.0
                matched_class_id = None

            knowledge_type, novelty_value = classify_knowledge(vehicle_A_confidence)

            sign_frequency = 0

            # Update frequency table whenever a sign is identified
            if matched_class_id is not None:
                class_key = str(matched_class_id)

                if class_key not in frequency_table:
                    frequency_table[class_key] = 0

                frequency_table[class_key] += 1
                sign_frequency = frequency_table[class_key]
                
                # Save frequency table after each update
                save_frequency_table(frequency_table)

            next_step = "IGNORE" if knowledge_type == "KNOWN" else "GO_TO_IMPORTANCE_SCORE"

            output = {
                "vehicle_id": vehicle_id,
                "image_path": image_path,
                "timestamp": time.time(),
                "sign_number": idx + 1,

                "detector_confidence": round(detector_confidence, 4),
                "generic_bbox": g_bbox,

                "vehicle_A_confidence": round(vehicle_A_confidence, 4),
                "best_iou": round(best_iou, 4),
                "matched_class_id": matched_class_id,
                "frequency": sign_frequency,

                "color": sign_features["color"],
                "shape": sign_features["shape"],
                "embedding": sign_features["embedding"],
                "cropped_sign_path": sign_features["cropped_sign_path"],

                "knowledge_type": knowledge_type,
                "novelty_value": novelty_value,
                "next_step": next_step
            }

            outputs.append(output)

    return outputs