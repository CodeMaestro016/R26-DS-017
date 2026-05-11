import cv2
import numpy as np
from PIL import Image

import torch
import torchvision.transforms as transforms
import torchvision.models as models

import os
import time


# ==============================
# EMBEDDING MODEL
# ==============================
# Used to create visual embedding.

embedding_model = models.resnet18(
    weights=models.ResNet18_Weights.DEFAULT
)

embedding_model = torch.nn.Sequential(
    *list(embedding_model.children())[:-1]
)

embedding_model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])


# ==============================
# CREATE CROPPED SIGN FOLDER
# ==============================

cropped_sign_folder = "shared/cropped_signs"

os.makedirs(cropped_sign_folder, exist_ok=True)


# ==============================
# CROP SIGN REGION
# ==============================

def crop_sign_region(image_path, bbox):

    image = Image.open(image_path).convert("RGB")

    x1, y1, x2, y2 = bbox
    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

    cropped_sign = image.crop((x1, y1, x2, y2))

    return cropped_sign


# ==============================
# SAVE CROPPED SIGN IMAGE
# ==============================

def save_cropped_sign(cropped_sign):

    filename = f"sign_{int(time.time() * 1000)}.png"

    save_path = os.path.join(
        cropped_sign_folder,
        filename
    )

    cropped_sign.save(save_path)

    return save_path


# ==============================
# EXTRACT DOMINANT COLOR
# ==============================

def extract_dominant_color(cropped_sign):

    img = np.array(cropped_sign)

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    red1 = cv2.inRange(
        hsv,
        (0, 70, 50),
        (10, 255, 255)
    )

    red2 = cv2.inRange(
        hsv,
        (170, 70, 50),
        (180, 255, 255)
    )

    red = red1 + red2

    blue = cv2.inRange(
        hsv,
        (90, 70, 50),
        (130, 255, 255)
    )

    yellow = cv2.inRange(
        hsv,
        (20, 70, 50),
        (35, 255, 255)
    )

    green = cv2.inRange(
        hsv,
        (35, 40, 40),
        (85, 255, 255)
    )

    white = cv2.inRange(
        hsv,
        (0, 0, 200),
        (180, 40, 255)
    )

    black = cv2.inRange(
        hsv,
        (0, 0, 0),
        (180, 255, 50)
    )

    colors = {
        "red": cv2.countNonZero(red),
        "blue": cv2.countNonZero(blue),
        "yellow": cv2.countNonZero(yellow),
        "green": cv2.countNonZero(green),
        "white": cv2.countNonZero(white),
        "black": cv2.countNonZero(black),
    }

    dominant_color = max(colors, key=colors.get)

    if colors[dominant_color] == 0:
        return "unknown"

    return dominant_color


# ==============================
# EXTRACT SHAPE
# ==============================

def extract_shape(cropped_sign):

    img = np.array(cropped_sign)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2GRAY
    )

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edges = cv2.Canny(
        blurred,
        50,
        150
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) == 0:
        return "unknown"

    largest = max(
        contours,
        key=cv2.contourArea
    )

    perimeter = cv2.arcLength(
        largest,
        True
    )

    approx = cv2.approxPolyDP(
        largest,
        0.04 * perimeter,
        True
    )

    vertices = len(approx)

    x, y, w, h = cv2.boundingRect(approx)

    aspect_ratio = w / float(h)

    if vertices == 3:
        return "triangle"

    elif vertices == 4:

        if 0.85 <= aspect_ratio <= 1.15:
            return "square"

        return "rectangle"

    elif vertices == 5:
        return "pentagon"

    elif vertices == 8:
        return "octagon"

    elif vertices >= 10:
        return "star_or_complex"

    elif vertices >= 6:
        return "circle"

    return "unknown"


# ==============================
# EXTRACT EMBEDDING
# ==============================

def extract_embedding(cropped_sign):

    img_tensor = transform(
        cropped_sign
    ).unsqueeze(0)

    with torch.no_grad():

        embedding = embedding_model(
            img_tensor
        )

    embedding = embedding.squeeze().numpy()

    return embedding.tolist()


# ==============================
# MAIN FEATURE EXTRACTION
# ==============================

def extract_sign_features(image_path, bbox):

    cropped_sign = crop_sign_region(
        image_path,
        bbox
    )

    # Save cropped sign image
    cropped_sign_path = save_cropped_sign(
        cropped_sign
    )

    color = extract_dominant_color(
        cropped_sign
    )

    shape = extract_shape(
        cropped_sign
    )

    embedding = extract_embedding(
        cropped_sign
    )

    return {
        "color": color,
        "shape": shape,
        "embedding": embedding,
        "cropped_sign_path": cropped_sign_path
    }