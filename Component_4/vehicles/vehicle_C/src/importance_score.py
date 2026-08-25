# vehicles/vehicle_A/src/importance_score.py
#
# Importance Score Calculation
# -----------------------------------------
# The Importance Score combines Visual Prominence
# and Novelty for RARE/NEW traffic-sign knowledge.
#
# The score is used as one state feature for the
# RL sharing agent. It is NOT the final SHARE/IGNORE decision.
#
# The weights were selected using a data-driven
# exhaustive weight-search experiment on the validation dataset.
# Final selected weights:
#     Visual Prominence = 0.83
#     Novelty            = 0.17
#
# Importance Score:
#     I = 0.83 * Visual + 0.17 * Novelty


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
    """
    Calculates how visually prominent a detected traffic sign is.

    Visual prominence is calculated as:

        bounding box area / full image area

    A larger value means the traffic sign occupies more
    space in the image.

    Returns:
        float: Visual prominence value.
    """

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
    """
    Calculates the Importance Score for RARE/NEW knowledge.

    The Importance Score combines:

        Visual Prominence
        Novelty

    using the data-driven weights selected from the
    validation dataset.

    Formula:

        Importance =
            0.83 * Visual Prominence
            + 0.17 * Novelty

    The Importance Score is NOT the final sharing decision.
    It is used as one state feature for the RL sharing agent.

    Args:
        visual_prominence (float):
            Normalized visual prominence of the traffic sign.

        novelty_value (float):
            Normalized novelty value of the traffic sign.

    Returns:
        float: Importance Score.
    """

    importance_score = (
        VISUAL_WEIGHT * visual_prominence
        + NOVELTY_WEIGHT * novelty_value
    )

    return round(importance_score, 4)


# ============================================================
# ADD IMPORTANCE SCORES
# ============================================================

def add_importance_scores(image_path, detections):
    """
    Adds Importance Scores only for RARE and NEW
    traffic-sign detections.

    KNOWN signs are ignored because they do not require
    knowledge-sharing evaluation.

    Input:
        image_path:
            Path to the original image.

        detections:
            List of detected sign dictionaries.

    Output:
        importance_candidates:
            List of RARE/NEW detections containing
            visual prominence and importance score.
    """

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