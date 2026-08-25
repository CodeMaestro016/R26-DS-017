# vehicles/vehicle_A/src/cnn_classifier.py
# Step 2: CNN Classification + Knowledge Labeling - Vehicle A

import cv2
import json
import numpy as np
import tensorflow as tf


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CNN_MODEL_PATH = "vehicles/vehicle_A/models/vehicle_A_cnn_prohibitory_best.keras"
CLASS_MAPPING_PATH = "vehicles/vehicle_A/models/vehicle_A_class_mapping.json"

IMG_SIZE = 96

KNOWN_THRESHOLD = 0.70
RARE_THRESHOLD = 0.30


# ==========================================================
# CNN CLASSIFIER
# ==========================================================

class VehicleACNN:

    def __init__(self):
        """
        Load trained CNN model and class mapping.
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

            print("CNN classifier loaded.")

        except Exception as e:
            print("Failed to load CNN classifier.")
            print(e)

    def preprocess_image(self, cropped_sign):
        """
        Prepare cropped sign image from memory for CNN prediction.

        Input:
            cropped_sign: cropped image returned by YOLO detection

        Output:
            processed image ready for CNN model
        """

        if cropped_sign is None or cropped_sign.size == 0:
            print("Invalid cropped sign.")
            return None

        # Resize to same size used during CNN training
        image = cv2.resize(cropped_sign, (IMG_SIZE, IMG_SIZE))

        # Convert OpenCV BGR image to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Normalize pixel values
        image = image.astype(np.float32) / 255.0

        # Add batch dimension: (96, 96, 3) -> (1, 96, 96, 3)
        image = np.expand_dims(image, axis=0)

        return image

    def get_status(self, confidence):
        """
        Assign knowledge label based on CNN confidence.

        KNOWN:
            High confidence. No need to share.

        RARE:
            Medium confidence. Pass to next step.

        NEW:
            Low confidence. Pass to next step.
        """

        if confidence >= KNOWN_THRESHOLD:
            return "KNOWN"
        elif confidence >= RARE_THRESHOLD:
            return "RARE"
        else:
            return "NEW"

    def classify(self, cropped_sign):
        """
        Classify one cropped traffic sign image from memory.

        Output:
            predicted_index
            class_id
            class_name
            confidence
            status
            action
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

        # CNN output index
        predicted_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))

        # Get original GTSRB class ID from saved mapping
        mapping = self.class_mapping[str(predicted_index)]

        class_id = mapping["original_class_id"]
        class_name = mapping["class_name"]

        # Assign knowledge label
        status = self.get_status(confidence)

        # Decide next pipeline action
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