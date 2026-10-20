# vehicles/vehicle_C/src/batch_training_storage.py
# Save verified cropped traffic-sign images for later
# Vehicle C CNN batch training.

import os
import time
import uuid

import cv2


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VEHICLE_C_DIR = os.path.dirname(
    CURRENT_DIR
)

BATCH_TRAINING_DIR = os.path.join(
    VEHICLE_C_DIR,
    "data",
    "batch_training"
)


# ==========================================================
# BATCH TRAINING STORAGE
# ==========================================================

class BatchTrainingStorage:
    """
    Save cropped traffic-sign images using the verified
    class ID received from Vehicle C's temporary database.

    Folder structure:

        vehicles/vehicle_C/data/batch_training/
            class_0/
            class_1/
            class_2/
            ...

    If the class folder already exists, it is reused.
    Every new crop gets a unique filename.
    """

    def __init__(
        self,
        base_directory=BATCH_TRAINING_DIR
    ):
        self.base_directory = os.path.abspath(
            base_directory
        )

        self.create_base_directory()

    # ======================================================
    # CREATE BASE DIRECTORY
    # ======================================================

    def create_base_directory(self):
        """
        Create the main batch-training folder if missing.
        """

        os.makedirs(
            self.base_directory,
            exist_ok=True
        )

    # ======================================================
    # CLEAN CLASS NAME
    # ======================================================

    @staticmethod
    def clean_class_name(
        class_name
    ):
        """
        Convert the class name into a safe filename value.
        """

        if class_name is None:
            return "unknown"

        safe_name = str(
            class_name
        ).strip().lower()

        safe_name = safe_name.replace(
            " ",
            "_"
        )

        safe_name = safe_name.replace(
            "/",
            "_"
        )

        safe_name = safe_name.replace(
            "\\",
            "_"
        )

        return safe_name or "unknown"

    # ======================================================
    # CREATE OR GET CLASS DIRECTORY
    # ======================================================

    def get_class_directory(
        self,
        class_id
    ):
        """
        Create class_<class_id> only when it does not exist.

        If it already exists, reuse the same folder.
        """

        if class_id is None:
            return None

        try:
            class_id = int(
                class_id
            )

        except (
            TypeError,
            ValueError
        ):
            return None

        class_directory = os.path.join(
            self.base_directory,
            f"class_{class_id}"
        )

        os.makedirs(
            class_directory,
            exist_ok=True
        )

        return class_directory

    # ======================================================
    # GENERATE UNIQUE IMAGE NAME
    # ======================================================

    @staticmethod
    def generate_image_filename(
        class_id,
        class_name
    ):
        """
        Generate a unique image filename so existing images
        are never overwritten.
        """

        timestamp = int(
            time.time() * 1000
        )

        unique_id = uuid.uuid4().hex[:8]

        safe_class_name = (
            BatchTrainingStorage
            .clean_class_name(
                class_name
            )
        )

        return (
            f"vehicle_C_"
            f"class_{class_id}_"
            f"{safe_class_name}_"
            f"{timestamp}_"
            f"{unique_id}.png"
        )

    # ======================================================
    # SAVE CROPPED IMAGE
    # ======================================================

    def save_crop(
        self,
        cropped_sign,
        class_id,
        class_name=None,
        category=None,
        source="temp_db_match"
    ):
        """
        Save one cropped traffic-sign image into its verified
        class folder.

        Example:

            batch_training/class_33/image.png
        """

        if cropped_sign is None:
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "MISSING_CROPPED_SIGN"
            }

        if not hasattr(
            cropped_sign,
            "size"
        ):
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "INVALID_CROPPED_SIGN"
            }

        if cropped_sign.size == 0:
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "EMPTY_CROPPED_SIGN"
            }

        try:
            class_id = int(
                class_id
            )

        except (
            TypeError,
            ValueError
        ):
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "INVALID_CLASS_ID"
            }

        class_directory = (
            self.get_class_directory(
                class_id
            )
        )

        if class_directory is None:
            return {
                "status": "FAILED",
                "saved": False,
                "reason": (
                    "CLASS_DIRECTORY_CREATION_FAILED"
                )
            }

        image_filename = (
            self.generate_image_filename(
                class_id=class_id,
                class_name=class_name
            )
        )

        image_path = os.path.join(
            class_directory,
            image_filename
        )

        try:
            image_saved = cv2.imwrite(
                image_path,
                cropped_sign
            )

        except cv2.error as error:
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "OPENCV_SAVE_ERROR",
                "error": str(error)
            }

        if not image_saved:
            return {
                "status": "FAILED",
                "saved": False,
                "reason": "IMAGE_SAVE_FAILED"
            }

        return {
            "status": (
                "SAVED_FOR_BATCH_TRAINING"
            ),

            "saved": True,

            "vehicle_id": "Vehicle_C",

            "class_id": class_id,

            "class_name": class_name,

            "category": category,

            "source": source,

            "class_directory": (
                class_directory
            ),

            "image_filename": (
                image_filename
            ),

            "image_path": (
                image_path
            )
        }

    # ======================================================
    # COUNT IMAGES IN CLASS
    # ======================================================

    def count_class_images(
        self,
        class_id
    ):
        """
        Count stored images for one class.
        """

        class_directory = (
            self.get_class_directory(
                class_id
            )
        )

        if class_directory is None:
            return 0

        valid_extensions = {
            ".png",
            ".jpg",
            ".jpeg"
        }

        image_count = 0

        for filename in os.listdir(
            class_directory
        ):
            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension in valid_extensions:
                image_count += 1

        return image_count