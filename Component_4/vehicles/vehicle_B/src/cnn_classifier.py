# vehicles/vehicle_B/src/cnn_classifier.py
# Step 2: CNN Classification + Knowledge Labeling - Vehicle B

import cv2
import json
import numpy as np
import tensorflow as tf


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CNN_MODEL_PATH = "vehicles/vehicle_B/models/vehicle_B_cnn_mandatory.keras"
CLASS_MAPPING_PATH = "vehicles/vehicle_B/models/vehicle_B_class_mapping.json"

IMG_SIZE = 96

KNOWN_THRESHOLD = 0.70
RARE_THRESHOLD = 0.30


# ==========================================================
# CNN CLASSIFIER
# ==========================================================

class VehicleBCNN:

    def __init__(self):
        """
        Load Vehicle B CNN model and class mapping.
        """

        self.classifier = None
        self.class_mapping = None

        try:
            self.classifier = tf.keras.models.load_model(
                CNN_MODEL_PATH,
                compile=False
            )

            with open(CLASS_MAPPING_PATH, "r") as file:
                self.class_mapping = json.load(file)

            print("Vehicle B CNN classifier loaded.")

        except Exception as e:
            print("Failed to load Vehicle B CNN classifier.")
            print(e)

    def preprocess_image(self, cropped_sign):
        """
        Prepare cropped sign image for CNN prediction.
        """

        if cropped_sign is None or cropped_sign.size == 0:
            print("Invalid cropped sign.")
            return None

        # Resize image to the CNN input size
        image = cv2.resize(cropped_sign, (IMG_SIZE, IMG_SIZE))

        # Convert OpenCV BGR format to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Normalize pixel values
        image = image.astype(np.float32) / 255.0

        # Add batch dimension
        image = np.expand_dims(image, axis=0)

        return image

    def get_status(self, confidence):
        """
        Assign KNOWN, RARE, or NEW using CNN confidence.
        """

        if confidence >= KNOWN_THRESHOLD:
            return "KNOWN"
        elif confidence >= RARE_THRESHOLD:
            return "RARE"
        else:
            return "NEW"

    def classify(self, cropped_sign):
        """
        Classify one cropped traffic sign image.
        """

        if self.classifier is None or self.class_mapping is None:
            return None

        input_image = self.preprocess_image(cropped_sign)

        if input_image is None:
            return None

        prediction = self.classifier.predict(
            input_image,
            verbose=0
        )[0]

        # Get the CNN output index and confidence
        predicted_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))

        # Get the original GTSRB class information
        mapping = self.class_mapping[str(predicted_index)]

        class_id = mapping["original_class_id"]
        class_name = mapping["class_name"]

        # Assign the knowledge status
        status = self.get_status(confidence)

        # Decide whether the sign continues in the pipeline
        if status == "KNOWN":
            action = "IGNORE"
        else:
            action = "PASS_TO_NEXT_STEP"

        return {
            "predicted_index": predicted_index,
            "class_id": class_id,
            "class_name": class_name,
            "confidence": round(confidence, 4),
            "status": status,
            "action": action
        }