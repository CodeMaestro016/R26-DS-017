# vehicles/vehicle_A/src/importance_score.py

from PIL import Image


# ============================================================
# FINAL DATA-DRIVEN WEIGHTS
# ============================================================

VISUAL_WEIGHT = 0.83
NOVELTY_WEIGHT = 0.17


# ============================================================
# VISUAL PROMINENCE
# ============================================================

def calculate_visual_prominence(bbox, image_width, image_height):

    x1, y1, x2, y2 = bbox

    bbox_width = x2 - x1
    bbox_height = y2 - y1

    bbox_area = bbox_width * bbox_height
    image_area = image_width * image_height

    if image_area == 0:
        return 0.0

    visual_prominence = bbox_area / image_area

    return round(visual_prominence, 6)


# ============================================================
# IMPORTANCE SCORE
# ============================================================

def calculate_importance_score(visual_prominence, novelty_value):
   

    importance_score = (
        VISUAL_WEIGHT * visual_prominence
        + NOVELTY_WEIGHT * novelty_value
    )

    return round(importance_score, 4)


# ============================================================
# ADD IMPORTANCE SCORES
# ============================================================

def add_importance_scores(image_path, detections):


    image = Image.open(image_path).convert("RGB")

    image_width, image_height = image.size

    importance_candidates = []

    for item in detections:

        knowledge_type = item.get("knowledge_type")

        # ----------------------------------------------------
        # KNOWN signs do not require importance evaluation
        # ----------------------------------------------------

        if knowledge_type == "KNOWN":
            continue

        # ----------------------------------------------------
        # Calculate Visual Prominence
        # ----------------------------------------------------

        visual_prominence = calculate_visual_prominence(
            item["generic_bbox"],
            image_width,
            image_height
        )

        # ----------------------------------------------------
        # Get Novelty
        # ----------------------------------------------------

        novelty_value = item.get("novelty_value", 0.0)

        # ----------------------------------------------------
        # Calculate Importance Score
        # ----------------------------------------------------

        importance_score = calculate_importance_score(
            visual_prominence,
            novelty_value
        )

        # ----------------------------------------------------
        # Store results
        # ----------------------------------------------------

        item["visual_prominence"] = visual_prominence
        item["importance_score"] = importance_score
        item["next_step"] = "SEND_TO_RL_AGENT"

        importance_candidates.append(item)

    return importance_candidates