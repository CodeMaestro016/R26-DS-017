# Calculates importance score for rare/new knowledge

from PIL import Image


def calculate_visual_prominence(bbox, image_width, image_height):
    x1, y1, x2, y2 = bbox

    bbox_area = (x2 - x1) * (y2 - y1)
    image_area = image_width * image_height

    return bbox_area / image_area


def calculate_importance_score(visual_prominence, novelty_value):
    # Initial weights. Later tune using RL experiments.
    w1 = 0.4
    w2 = 0.6

    score = (w1 * visual_prominence) + (w2 * novelty_value)

    return round(score, 4)


def add_importance_scores(image_path, detections):
    image = Image.open(image_path).convert("RGB")
    image_width, image_height = image.size

    importance_candidates = []

    for item in detections:
        if item["knowledge_type"] == "KNOWN":
            continue

        visual_prominence = calculate_visual_prominence(
            item["generic_bbox"],
            image_width,
            image_height
        )

        importance_score = calculate_importance_score(
            visual_prominence,
            item["novelty_value"]
        )

        item["visual_prominence"] = round(visual_prominence, 6)
        item["importance_score"] = importance_score
        item["next_step"] = "SEND_TO_AGENT"

        importance_candidates.append(item)

    return importance_candidates