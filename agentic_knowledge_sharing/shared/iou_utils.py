# Calculates overlap between two bounding boxes

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    intersection_width = max(0, xB - xA)
    intersection_height = max(0, yB - yA)
    intersection_area = intersection_width * intersection_height

    boxA_area = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxB_area = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])

    union_area = boxA_area + boxB_area - intersection_area

    if union_area == 0:
        return 0

    return intersection_area / union_area