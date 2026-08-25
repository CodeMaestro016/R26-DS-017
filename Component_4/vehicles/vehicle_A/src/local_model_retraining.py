# ==========================================================
# vehicles/vehicle_A/src/local_model_retraining.py
#
# Vehicle A - Local CNN Retraining
#
# IMPORTANT:
# - Existing model is ALREADY a 43-class model.
# - No 12 -> 43 expansion is performed.
# - Existing MobileNetV2 architecture is preserved.
# - Only the final 43-class classification layer is trained.
# - Only classes present in the new batch are updated.
# - Other class weights are protected using gradient masking.
#
# IMPORTANT MAPPING:
# - GTSRB class IDs are used externally by the research system.
# - CNN output indices may NOT equal GTSRB class IDs.
# - vehicle_A_class_mapping.json defines the mapping.
# ==========================================================

import json
import os
import shutil
import time
from datetime import datetime

import numpy as np
import tensorflow as tf


# ==========================================================
# PATHS
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VEHICLE_A_DIR = os.path.dirname(
    CURRENT_DIR
)

MODEL_DIR = os.path.join(
    VEHICLE_A_DIR,
    "models"
)

ACTIVE_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "vehicle_A_cnn_prohibitory_best.keras"
)

CLASS_MAPPING_PATH = os.path.join(
    MODEL_DIR,
    "vehicle_A_class_mapping.json"
)

BATCH_TRAINING_DIR = os.path.join(
    VEHICLE_A_DIR,
    "data",
    "batch_training"
)

TRAINING_HISTORY_PATH = os.path.join(
    MODEL_DIR,
    "local_retraining_history.json"
)

TEMP_UPDATED_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "vehicle_A_cnn_prohibitory_updating.keras"
)


# ==========================================================
# CONFIGURATION
# ==========================================================

IMG_SIZE = 96

TOTAL_GTSRB_CLASSES = 43

BATCH_SIZE = 8

EPOCHS = 30

LEARNING_RATE = 0.0005

RANDOM_SEED = 42

MINIMUM_TOTAL_IMAGES = 1

DELETE_BATCH_FOLDERS_AFTER_SUCCESS = True

SUPPORTED_IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".ppm",
    ".bmp"
)


# ==========================================================
# EXPECTED VEHICLE A MODEL ARCHITECTURE
# ==========================================================

EXPECTED_EMBEDDING_SIZE = 128

EXPECTED_OUTPUT_CLASSES = 43


# ==========================================================
# GTSRB CLASS MAPPING
# ==========================================================

CLASS_ID_TO_NAME = {

    0: "speed_limit_20",
    1: "speed_limit_30",
    2: "speed_limit_50",
    3: "speed_limit_60",
    4: "speed_limit_70",
    5: "speed_limit_80",
    6: "restriction_ends_80",
    7: "speed_limit_100",
    8: "speed_limit_120",
    9: "no_overtaking",
    10: "no_overtaking_trucks",
    11: "priority_at_next_intersection",
    12: "priority_road",
    13: "give_way",
    14: "stop",
    15: "no_traffic_both_ways",
    16: "no_trucks",
    17: "no_entry",
    18: "danger",
    19: "bend_left",
    20: "bend_right",
    21: "bend",
    22: "uneven_road",
    23: "slippery_road",
    24: "road_narrows",
    25: "construction",
    26: "traffic_signal",
    27: "pedestrian_crossing",
    28: "school_crossing",
    29: "cycles_crossing",
    30: "snow",
    31: "animals",
    32: "restriction_ends",
    33: "go_right",
    34: "go_left",
    35: "go_straight",
    36: "go_right_or_straight",
    37: "go_left_or_straight",
    38: "keep_right",
    39: "keep_left",
    40: "roundabout",
    41: "restriction_ends_overtaking",
    42: "restriction_ends_overtaking_trucks"
}


# ==========================================================
# VEHICLE A LOCAL MODEL RETRAINER
# ==========================================================

class VehicleALocalModelRetrainer:

    def __init__(
        self,
        active_model_path=ACTIVE_MODEL_PATH,
        mapping_path=CLASS_MAPPING_PATH,
        batch_training_dir=BATCH_TRAINING_DIR
    ):

        self.active_model_path = os.path.abspath(
            active_model_path
        )

        self.mapping_path = os.path.abspath(
            mapping_path
        )

        self.batch_training_dir = os.path.abspath(
            batch_training_dir
        )

        self.model = None

        self.classification_layer = None

        self.image_paths = []

        self.labels = []

        self.active_class_ids = []

        self.class_counts = {}

        self.processed_class_directories = []

        # --------------------------------------------------
        # Mapping dictionaries
        #
        # output_to_gtsrb:
        # CNN output index -> GTSRB class ID
        #
        # gtsrb_to_output:
        # GTSRB class ID -> CNN output index
        # --------------------------------------------------

        self.output_to_gtsrb = {}

        self.gtsrb_to_output = {}

        self.optimizer = tf.keras.optimizers.Adam(
            learning_rate=LEARNING_RATE
        )

        self.loss_function = (
            tf.keras.losses.SparseCategoricalCrossentropy()
        )

        os.makedirs(
            MODEL_DIR,
            exist_ok=True
        )

        os.makedirs(
            self.batch_training_dir,
            exist_ok=True
        )

        tf.random.set_seed(
            RANDOM_SEED
        )

        np.random.seed(
            RANDOM_SEED
        )


    # ======================================================
    # MODEL LOADING
    # ======================================================

    def load_current_model(self):

        print("\n" + "=" * 60)
        print("Loading Existing Vehicle A CNN")
        print("=" * 60)

        if not os.path.exists(
            self.active_model_path
        ):

            raise FileNotFoundError(
                "Active CNN model was not found:\n"
                f"{self.active_model_path}"
            )

        self.model = tf.keras.models.load_model(
            self.active_model_path,
            compile=False
        )

        print(
            "Model loaded successfully."
        )

        print(
            "Model input shape:",
            self.model.input_shape
        )

        print(
            "Model output shape:",
            self.model.output_shape
        )

        # --------------------------------------------------
        # CHECK OUTPUT COUNT
        # --------------------------------------------------

        output_count = int(
            self.model.output_shape[-1]
        )

        if output_count != EXPECTED_OUTPUT_CLASSES:

            raise ValueError(
                "\nVehicle A model must already have "
                "43 output classes.\n"
                f"Found: {output_count}\n"
                "Do NOT use a 12-class model with this "
                "retraining script."
            )

        # --------------------------------------------------
        # CHECK INPUT SIZE
        # --------------------------------------------------

        input_shape = self.model.input_shape

        if (
            input_shape[1] != IMG_SIZE
            or input_shape[2] != IMG_SIZE
            or input_shape[3] != 3
        ):

            raise ValueError(
                "\nUnexpected Vehicle A input shape.\n"
                f"Expected: (None, {IMG_SIZE}, {IMG_SIZE}, 3)\n"
                f"Found: {input_shape}"
            )

        # --------------------------------------------------
        # FIND FINAL CLASSIFICATION LAYER
        # --------------------------------------------------

        self.classification_layer = (
            self.find_final_classification_layer()
        )

        print(
            "Classification layer:",
            self.classification_layer.name
        )

        print(
            "Classification outputs:",
            self.classification_layer.units
        )

        # --------------------------------------------------
        # CHECK EMBEDDING LAYER
        # --------------------------------------------------

        embedding_layer = None

        for layer in self.model.layers:

            if layer.name == "embedding_layer":

                embedding_layer = layer

                break

        if embedding_layer is not None:

            print(
                "Embedding layer found:",
                embedding_layer.name
            )

            print(
                "Expected embedding size:",
                EXPECTED_EMBEDDING_SIZE
            )

        else:

            print(
                "WARNING: embedding_layer "
                "was not found by name."
            )

        # --------------------------------------------------
        # PRINT ARCHITECTURE
        # --------------------------------------------------

        print("\nVehicle A model architecture:")

        for index, layer in enumerate(
            self.model.layers
        ):

            print(
                f"{index:02d} | "
                f"{layer.name} | "
                f"{layer.__class__.__name__}"
            )

        return {
            "status": "MODEL_LOADED",
            "model_path": self.active_model_path,
            "output_classes": output_count,
            "input_shape": str(
                self.model.input_shape
            ),
            "classification_layer": (
                self.classification_layer.name
            )
        }


    # ======================================================
    # FIND FINAL CLASSIFICATION LAYER
    # ======================================================

    def find_final_classification_layer(self):

        if self.model is None:

            raise ValueError(
                "Model has not been loaded."
            )

        final_layer = self.model.layers[-1]

        if not isinstance(
            final_layer,
            tf.keras.layers.Dense
        ):

            raise ValueError(
                "Final Vehicle A layer must be Dense.\n"
                f"Found: {type(final_layer)}"
            )

        if int(
            final_layer.units
        ) != TOTAL_GTSRB_CLASSES:

            raise ValueError(
                "Final classification layer must "
                f"have {TOTAL_GTSRB_CLASSES} outputs.\n"
                f"Found: {final_layer.units}"
            )

        return final_layer


    # ======================================================
    # CLASS MAPPING
    #
    # IMPORTANT:
    # The existing model uses a non-identity mapping.
    #
    # Example:
    #
    # CNN output 2 -> GTSRB class 10
    # CNN output 12 -> GTSRB class 2
    #
    # Therefore we create both directions.
    # ======================================================

    def load_existing_class_mapping(self):

        print("\n" + "=" * 60)
        print("Loading Vehicle A Class Mapping")
        print("=" * 60)

        if not os.path.exists(
            self.mapping_path
        ):

            raise FileNotFoundError(
                "Class mapping was not found:\n"
                f"{self.mapping_path}"
            )

        try:

            with open(
                self.mapping_path,
                "r",
                encoding="utf-8"
            ) as file:

                mapping = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError
        ) as error:

            raise ValueError(
                "Class mapping could not be loaded."
            ) from error

        if not isinstance(
            mapping,
            dict
        ):

            raise ValueError(
                "Invalid class mapping structure."
            )

        # --------------------------------------------------
        # Mapping must contain exactly 43 outputs
        # --------------------------------------------------

        if len(mapping) != TOTAL_GTSRB_CLASSES:

            raise ValueError(
                "\nClass mapping must contain "
                f"{TOTAL_GTSRB_CLASSES} classes.\n"
                f"Found: {len(mapping)}"
            )

        self.output_to_gtsrb = {}

        self.gtsrb_to_output = {}

        # --------------------------------------------------
        # Read mapping
        # --------------------------------------------------

        for output_index in range(
            TOTAL_GTSRB_CLASSES
        ):

            key = str(
                output_index
            )

            if key not in mapping:

                raise ValueError(
                    "Missing output index in mapping: "
                    f"{output_index}"
                )

            information = mapping[key]

            if not isinstance(
                information,
                dict
            ):

                raise ValueError(
                    f"Invalid mapping for output "
                    f"{output_index}"
                )

            if "original_class_id" not in information:

                raise ValueError(
                    f"Mapping for output "
                    f"{output_index} does not contain "
                    "'original_class_id'."
                )

            original_class_id = int(
                information[
                    "original_class_id"
                ]
            )

            if not (
                0 <= original_class_id
                < TOTAL_GTSRB_CLASSES
            ):

                raise ValueError(
                    "Invalid GTSRB class ID: "
                    f"{original_class_id}"
                )

            # --------------------------------------------------
            # CNN output -> GTSRB class
            # --------------------------------------------------

            self.output_to_gtsrb[
                output_index
            ] = original_class_id

            # --------------------------------------------------
            # GTSRB class -> CNN output
            # --------------------------------------------------

            if original_class_id in (
                self.gtsrb_to_output
            ):

                raise ValueError(
                    "Duplicate GTSRB class ID in mapping: "
                    f"{original_class_id}"
                )

            self.gtsrb_to_output[
                original_class_id
            ] = output_index

        # --------------------------------------------------
        # Ensure all 43 GTSRB classes exist
        # --------------------------------------------------

        if len(
            self.output_to_gtsrb
        ) != TOTAL_GTSRB_CLASSES:

            raise ValueError(
                "CNN output mapping is incomplete."
            )

        if len(
            self.gtsrb_to_output
        ) != TOTAL_GTSRB_CLASSES:

            raise ValueError(
                "GTSRB-to-CNN mapping is incomplete."
            )

        # --------------------------------------------------
        # Verify every GTSRB class is represented
        # --------------------------------------------------

        expected_classes = set(
            range(
                TOTAL_GTSRB_CLASSES
            )
        )

        actual_classes = set(
            self.gtsrb_to_output.keys()
        )

        if actual_classes != expected_classes:

            missing = (
                expected_classes
                - actual_classes
            )

            extra = (
                actual_classes
                - expected_classes
            )

            raise ValueError(
                "\nInvalid GTSRB class mapping.\n"
                f"Missing: {sorted(missing)}\n"
                f"Extra: {sorted(extra)}"
            )

        # --------------------------------------------------
        # Print mapping
        # --------------------------------------------------

        print(
            "\n43-class CNN mapping verified successfully."
        )

        print(
            "\nCNN output -> GTSRB class:"
        )

        for output_index in range(
            TOTAL_GTSRB_CLASSES
        ):

            gtsrb_class = (
                self.output_to_gtsrb[
                    output_index
                ]
            )

            print(
                f"  Output {output_index:02d}"
                f" -> GTSRB {gtsrb_class:02d}"
                f" ({CLASS_ID_TO_NAME[gtsrb_class]})"
            )

        print(
            "\nGTSRB class -> CNN output:"
        )

        for gtsrb_class in range(
            TOTAL_GTSRB_CLASSES
        ):

            output_index = (
                self.gtsrb_to_output[
                    gtsrb_class
                ]
            )

            print(
                f"  GTSRB {gtsrb_class:02d}"
                f" ({CLASS_ID_TO_NAME[gtsrb_class]})"
                f" -> Output {output_index:02d}"
            )

        return mapping


    # ======================================================
    # BATCH DATA COLLECTION
    # ======================================================

    def collect_batch_images(self):

        print("\n" + "=" * 60)
        print("Collecting Local Batch Training Images")
        print("=" * 60)

        image_paths = []

        labels = []

        class_counts = {}

        processed_directories = []

        skipped_folders = []

        if not os.path.exists(
            self.batch_training_dir
        ):

            os.makedirs(
                self.batch_training_dir,
                exist_ok=True
            )

        for folder_name in sorted(
            os.listdir(
                self.batch_training_dir
            )
        ):

            folder_path = os.path.join(
                self.batch_training_dir,
                folder_name
            )

            if not os.path.isdir(
                folder_path
            ):

                continue

            # --------------------------------------------------
            # Only class_0 ... class_42
            # --------------------------------------------------

            if not folder_name.startswith(
                "class_"
            ):

                skipped_folders.append(
                    folder_name
                )

                continue

            try:

                class_id = int(
                    folder_name.replace(
                        "class_",
                        "",
                        1
                    )
                )

            except ValueError:

                skipped_folders.append(
                    folder_name
                )

                continue

            if not (
                0 <= class_id
                < TOTAL_GTSRB_CLASSES
            ):

                skipped_folders.append(
                    folder_name
                )

                continue

            # --------------------------------------------------
            # Verify mapping exists
            # --------------------------------------------------

            if class_id not in (
                self.gtsrb_to_output
            ):

                raise ValueError(
                    "GTSRB class does not exist "
                    "in CNN mapping: "
                    f"{class_id}"
                )

            class_images = []

            for image_filename in sorted(
                os.listdir(
                    folder_path
                )
            ):

                if not image_filename.lower().endswith(
                    SUPPORTED_IMAGE_EXTENSIONS
                ):

                    continue

                image_path = os.path.join(
                    folder_path,
                    image_filename
                )

                if os.path.isfile(
                    image_path
                ):

                    class_images.append(
                        image_path
                    )

            if not class_images:

                continue

            class_counts[class_id] = len(
                class_images
            )

            processed_directories.append(
                folder_path
            )

            # --------------------------------------------------
            # Convert GTSRB class ID to CNN output index
            # --------------------------------------------------

            output_index = (
                self.gtsrb_to_output[
                    class_id
                ]
            )

            for image_path in class_images:

                image_paths.append(
                    image_path
                )

                labels.append(
                    output_index
                )

            print(
                f"  GTSRB class {class_id:02d}"
                f" ({CLASS_ID_TO_NAME[class_id]})"
                f" -> CNN output {output_index:02d}"
                f" | {len(class_images)} images"
            )

        self.image_paths = image_paths

        self.labels = labels

        self.class_counts = class_counts

        self.active_class_ids = sorted(
            class_counts.keys()
        )

        self.processed_class_directories = (
            processed_directories
        )

        print(
            "\nTotal batch images:",
            len(image_paths)
        )

        print(
            "Active GTSRB classes:",
            self.active_class_ids
        )

        if skipped_folders:

            print(
                "Skipped folders:",
                skipped_folders
            )

        return {
            "total_images": len(
                image_paths
            ),
            "active_class_ids": (
                self.active_class_ids
            ),
            "class_counts": (
                class_counts
            ),
            "skipped_folders": (
                skipped_folders
            )
        }


    # ======================================================
    # IMAGE LOADING
    # ======================================================

    @staticmethod
    def load_and_prepare_image(
        image_path,
        label
    ):

        image_data = tf.io.read_file(
            image_path
        )

        image = tf.io.decode_image(
            image_data,
            channels=3,
            expand_animations=False
        )

        image.set_shape(
            [None, None, 3]
        )

        image = tf.image.resize(
            image,
            [
                IMG_SIZE,
                IMG_SIZE
            ]
        )

        image = tf.cast(
            image,
            tf.float32
        )

        image = image / 255.0

        return (
            image,
            tf.cast(
                label,
                tf.int32
            )
        )


    # ======================================================
    # DATA AUGMENTATION
    # ======================================================

    @staticmethod
    def augment_image(
        image,
        label
    ):

        image = tf.image.random_brightness(
            image,
            max_delta=0.05
        )

        image = tf.image.random_contrast(
            image,
            lower=0.95,
            upper=1.05
        )

        image = tf.clip_by_value(
            image,
            0.0,
            1.0
        )

        return image, label


    # ======================================================
    # CREATE DATASET
    # ======================================================

    def create_dataset(self):

        if not self.image_paths:

            raise ValueError(
                "No batch-training images found."
            )

        image_paths = np.asarray(
            self.image_paths
        )

        labels = np.asarray(
            self.labels,
            dtype=np.int32
        )

        dataset = (
            tf.data.Dataset
            .from_tensor_slices(
                (
                    image_paths,
                    labels
                )
            )
        )

        dataset = dataset.shuffle(
            buffer_size=max(
                len(image_paths),
                1
            ),
            seed=RANDOM_SEED,
            reshuffle_each_iteration=True
        )

        dataset = dataset.map(
            self.load_and_prepare_image,
            num_parallel_calls=(
                tf.data.AUTOTUNE
            )
        )

        dataset = dataset.map(
            self.augment_image,
            num_parallel_calls=(
                tf.data.AUTOTUNE
            )
        )

        dataset = dataset.batch(
            BATCH_SIZE
        )

        dataset = dataset.prefetch(
            tf.data.AUTOTUNE
        )

        return dataset


    # ======================================================
    # FREEZE ALL BUT FINAL CLASSIFICATION LAYER
    # ======================================================

    def freeze_feature_layers(self):

        if self.model is None:

            raise ValueError(
                "Model is not loaded."
            )

        if self.classification_layer is None:

            self.classification_layer = (
                self.find_final_classification_layer()
            )

        # --------------------------------------------------
        # Freeze EVERYTHING
        # --------------------------------------------------

        for layer in self.model.layers:

            layer.trainable = False

        # --------------------------------------------------
        # Train ONLY final Dense(43)
        # --------------------------------------------------

        self.classification_layer.trainable = True

        trainable_variables = (
            self.model.trainable_variables
        )

        print("\nTrainable variables:")

        for variable in trainable_variables:

            print(
                " ",
                variable.name,
                variable.shape
            )

        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------

        if len(trainable_variables) != 2:

            raise ValueError(
                "\nExpected exactly 2 trainable "
                "variables for final Dense layer "
                "(kernel + bias).\n"
                f"Found: {len(trainable_variables)}"
            )

        return {
            "trainable_layers": [
                self.classification_layer.name
            ],
            "trainable_variable_count": len(
                trainable_variables
            )
        }


    # ======================================================
    # CLASS MASK
    #
    # IMPORTANT:
    # active_class_ids contains GTSRB IDs.
    #
    # The gradient mask must use CNN output indices.
    # ======================================================

    def create_class_mask(self):

        mask = np.zeros(
            TOTAL_GTSRB_CLASSES,
            dtype=np.float32
        )

        print(
            "\nRetraining mask:"
        )

        print(
            "Active GTSRB classes:",
            self.active_class_ids
        )

        print(
            "Updating CNN outputs:"
        )

        for gtsrb_class_id in (
            self.active_class_ids
        ):

            if gtsrb_class_id not in (
                self.gtsrb_to_output
            ):

                raise ValueError(
                    "GTSRB class not found in mapping: "
                    f"{gtsrb_class_id}"
                )

            output_index = (
                self.gtsrb_to_output[
                    gtsrb_class_id
                ]
            )

            mask[output_index] = 1.0

            print(
                f"  GTSRB class "
                f"{gtsrb_class_id:02d}"
                f" ({CLASS_ID_TO_NAME[gtsrb_class_id]})"
                f" -> CNN output "
                f"{output_index:02d}"
            )

        return tf.constant(
            mask,
            dtype=tf.float32
        )


    # ======================================================
    # MASK FINAL CLASSIFICATION GRADIENTS
    # ======================================================

    @staticmethod
    def mask_final_layer_gradients(
        gradients,
        class_mask
    ):

        if len(gradients) != 2:

            raise ValueError(
                "Expected kernel and bias gradients."
            )

        kernel_gradient = gradients[0]

        bias_gradient = gradients[1]

        # --------------------------------------------------
        # Kernel:
        #
        # [128, 43]
        #
        # Bias:
        #
        # [43]
        # --------------------------------------------------

        kernel_mask = tf.reshape(
            class_mask,
            [
                1,
                TOTAL_GTSRB_CLASSES
            ]
        )

        if kernel_gradient is not None:

            kernel_gradient = (
                kernel_gradient
                * kernel_mask
            )

        if bias_gradient is not None:

            bias_gradient = (
                bias_gradient
                * class_mask
            )

        return [
            kernel_gradient,
            bias_gradient
        ]


    # ======================================================
    # TRAIN ONE BATCH
    # ======================================================

    def train_one_batch(
        self,
        images,
        labels,
        class_mask
    ):

        with tf.GradientTape() as tape:

            predictions = self.model(
                images,
                training=True
            )

            loss = self.loss_function(
                labels,
                predictions
            )

        trainable_variables = (
            self.model.trainable_variables
        )

        gradients = tape.gradient(
            loss,
            trainable_variables
        )

        # --------------------------------------------------
        # Protect classes NOT present in batch
        # --------------------------------------------------

        masked_gradients = (
            self.mask_final_layer_gradients(
                gradients,
                class_mask
            )
        )

        gradient_pairs = []

        for gradient, variable in zip(
            masked_gradients,
            trainable_variables
        ):

            if gradient is not None:

                gradient_pairs.append(
                    (
                        gradient,
                        variable
                    )
                )

        if not gradient_pairs:

            raise ValueError(
                "No valid gradients were produced."
            )

        self.optimizer.apply_gradients(
            gradient_pairs
        )

        predicted_classes = tf.argmax(
            predictions,
            axis=1,
            output_type=tf.int32
        )

        accuracy = tf.reduce_mean(
            tf.cast(
                tf.equal(
                    predicted_classes,
                    labels
                ),
                tf.float32
            )
        )

        return (
            float(
                loss.numpy()
            ),
            float(
                accuracy.numpy()
            )
        )


    # ======================================================
    # BACKUP MODEL
    # ======================================================

    def get_next_backup_model_path(self):

        version = 1

        while True:

            backup_path = os.path.join(
                MODEL_DIR,
                (
                    "vehicle_A_cnn_prohibitory_"
                    f"past_{version}.keras"
                )
            )

            if not os.path.exists(
                backup_path
            ):

                return backup_path

            version += 1


    # ======================================================
    # BACKUP MAPPING
    # ======================================================

    def get_mapping_backup_path(
        self,
        model_backup_path
    ):

        filename = os.path.basename(
            model_backup_path
        )

        version = filename.replace(
            "vehicle_A_cnn_prohibitory_past_",
            ""
        ).replace(
            ".keras",
            ""
        )

        return os.path.join(
            MODEL_DIR,
            (
                "vehicle_A_class_mapping_"
                f"past_{version}.json"
            )
        )


    # ======================================================
    # SAVE TEMPORARY MODEL
    # ======================================================

    def save_temporary_updated_model(self):

        if os.path.exists(
            TEMP_UPDATED_MODEL_PATH
        ):

            os.remove(
                TEMP_UPDATED_MODEL_PATH
            )

        print(
            "\nSaving temporary updated model..."
        )

        self.model.save(
            TEMP_UPDATED_MODEL_PATH
        )

        print(
            "Temporary model saved:"
        )

        print(
            TEMP_UPDATED_MODEL_PATH
        )

        return TEMP_UPDATED_MODEL_PATH


    # ======================================================
    # VERIFY SAVED MODEL
    # ======================================================

    @staticmethod
    def verify_saved_model(
        model_path
    ):

        if not os.path.exists(
            model_path
        ):

            return {
                "verified": False,
                "reason": "MODEL_NOT_FOUND"
            }

        try:

            verified_model = (
                tf.keras.models.load_model(
                    model_path,
                    compile=False
                )
            )

        except Exception as error:

            return {
                "verified": False,
                "reason": "MODEL_RELOAD_FAILED",
                "error": str(error)
            }

        # --------------------------------------------------
        # Verify input
        # --------------------------------------------------

        input_shape = (
            verified_model.input_shape
        )

        expected_input = (
            None,
            IMG_SIZE,
            IMG_SIZE,
            3
        )

        if tuple(input_shape) != expected_input:

            return {
                "verified": False,
                "reason": "INVALID_INPUT_SHAPE",
                "input_shape": str(
                    input_shape
                )
            }

        # --------------------------------------------------
        # Verify output
        # --------------------------------------------------

        output_count = int(
            verified_model.output_shape[-1]
        )

        if output_count != TOTAL_GTSRB_CLASSES:

            return {
                "verified": False,
                "reason": "INVALID_OUTPUT_COUNT",
                "output_count": output_count
            }

        # --------------------------------------------------
        # Verify final layer
        # --------------------------------------------------

        final_layer = (
            verified_model.layers[-1]
        )

        if not isinstance(
            final_layer,
            tf.keras.layers.Dense
        ):

            return {
                "verified": False,
                "reason": "FINAL_LAYER_NOT_DENSE"
            }

        if int(
            final_layer.units
        ) != TOTAL_GTSRB_CLASSES:

            return {
                "verified": False,
                "reason": "INVALID_FINAL_LAYER_UNITS",
                "units": int(
                    final_layer.units
                )
            }

        return {
            "verified": True,
            "input_shape": str(
                input_shape
            ),
            "output_count": output_count,
            "final_layer": final_layer.name
        }


    # ======================================================
    # BACKUP CURRENT MODEL + MAPPING
    # ======================================================

    def backup_current_files(self):

        print(
            "\nCreating backup..."
        )

        backup_model_path = (
            self.get_next_backup_model_path()
        )

        shutil.copy2(
            self.active_model_path,
            backup_model_path
        )

        backup_mapping_path = None

        if os.path.exists(
            self.mapping_path
        ):

            backup_mapping_path = (
                self.get_mapping_backup_path(
                    backup_model_path
                )
            )

            shutil.copy2(
                self.mapping_path,
                backup_mapping_path
            )

        print(
            "Previous model backup:"
        )

        print(
            backup_model_path
        )

        if backup_mapping_path:

            print(
                "Previous mapping backup:"
            )

            print(
                backup_mapping_path
            )

        return {
            "backup_model_path": (
                backup_model_path
            ),
            "backup_mapping_path": (
                backup_mapping_path
            )
        }


    # ======================================================
    # ACTIVATE UPDATED MODEL
    # ======================================================

    def activate_updated_model(self):

        if not os.path.exists(
            TEMP_UPDATED_MODEL_PATH
        ):

            raise FileNotFoundError(
                "Temporary updated model not found."
            )

        print(
            "\nActivating updated model..."
        )

        os.replace(
            TEMP_UPDATED_MODEL_PATH,
            self.active_model_path
        )

        print(
            "Updated model activated."
        )

        return self.active_model_path


    # ======================================================
    # CLEANUP
    # ======================================================

    def delete_processed_class_folders(self):

        deleted_folders = []

        failed_folders = []

        for class_directory in (
            self.processed_class_directories
        ):

            if not os.path.exists(
                class_directory
            ):

                continue

            try:

                shutil.rmtree(
                    class_directory
                )

                deleted_folders.append(
                    class_directory
                )

            except OSError as error:

                failed_folders.append(
                    {
                        "folder": (
                            class_directory
                        ),
                        "error": str(
                            error
                        )
                    }
                )

        os.makedirs(
            self.batch_training_dir,
            exist_ok=True
        )

        return {
            "deleted_folder_count": len(
                deleted_folders
            ),
            "deleted_folders": (
                deleted_folders
            ),
            "failed_folders": (
                failed_folders
            )
        }


    # ======================================================
    # TRAINING HISTORY
    # ======================================================

    def save_training_history(
        self,
        epoch_history,
        training_time,
        backup_result,
        cleanup_result
    ):

        record = {

            "vehicle_id": "Vehicle_A",

            "training_date": (
                datetime.now().isoformat()
            ),

            "active_model": (
                self.active_model_path
            ),

            "model_type": (
                "MobileNetV2_43_Class"
            ),

            "model_output_classes": (
                TOTAL_GTSRB_CLASSES
            ),

            # --------------------------------------------------
            # Research-level GTSRB IDs
            # --------------------------------------------------

            "updated_gtsrb_class_ids": (
                self.active_class_ids
            ),

            # --------------------------------------------------
            # Internal CNN output indices
            # --------------------------------------------------

            "updated_cnn_output_indices": {
                str(class_id):
                    self.gtsrb_to_output[class_id]
                for class_id in (
                    self.active_class_ids
                )
            },

            "class_counts": {
                str(class_id): count
                for class_id, count
                in self.class_counts.items()
            },

            "total_images": len(
                self.image_paths
            ),

            "epochs": EPOCHS,

            "batch_size": BATCH_SIZE,

            "learning_rate": (
                LEARNING_RATE
            ),

            "training_time_seconds": round(
                training_time,
                4
            ),

            "previous_model_backup": (
                backup_result
            ),

            "batch_cleanup": (
                cleanup_result
            ),

            "epoch_history": (
                epoch_history
            )
        }

        history = []

        if os.path.exists(
            TRAINING_HISTORY_PATH
        ):

            try:

                with open(
                    TRAINING_HISTORY_PATH,
                    "r",
                    encoding="utf-8"
                ) as file:

                    history = json.load(
                        file
                    )

            except (
                OSError,
                json.JSONDecodeError
            ):

                history = []

        if not isinstance(
            history,
            list
        ):

            history = []

        history.append(
            record
        )

        with open(
            TRAINING_HISTORY_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                history,
                file,
                indent=4
            )


    # ======================================================
    # MAIN RETRAINING
    # ======================================================

    def retrain(self):

        print("\n")
        print("=" * 60)
        print("Vehicle A Local CNN Retraining")
        print("=" * 60)

        # --------------------------------------------------
        # STEP 1
        # Load current 43-class model
        # --------------------------------------------------

        model_result = (
            self.load_current_model()
        )

        print(
            "\nActive Model:",
            model_result[
                "model_path"
            ]
        )

        print(
            "Current Outputs:",
            model_result[
                "output_classes"
            ]
        )

        # --------------------------------------------------
        # STEP 2
        # Load mapping
        # --------------------------------------------------

        self.load_existing_class_mapping()

        # --------------------------------------------------
        # STEP 3
        # Collect new images
        # --------------------------------------------------

        batch_result = (
            self.collect_batch_images()
        )

        print(
            "\nBatch Images:",
            batch_result[
                "total_images"
            ]
        )

        print(
            "Active GTSRB Classes:",
            batch_result[
                "active_class_ids"
            ]
        )

        # --------------------------------------------------
        # STEP 4
        # Stop if no images
        # --------------------------------------------------

        if (
            batch_result[
                "total_images"
            ]
            < MINIMUM_TOTAL_IMAGES
        ):

            print(
                "\nNo batch images found."
            )

            return {
                "status": "TRAINING_SKIPPED",
                "reason": "NO_BATCH_IMAGES"
            }

        # --------------------------------------------------
        # IMPORTANT:
        #
        # NO MODEL EXPANSION
        # --------------------------------------------------

        print(
            "\nModel expansion:"
        )

        print(
            "NOT REQUIRED"
        )

        print(
            "Existing model already has 43 classes."
        )

        # --------------------------------------------------
        # STEP 5
        # Freeze feature extractor
        # --------------------------------------------------

        layer_result = (
            self.freeze_feature_layers()
        )

        print(
            "\nTrainable layers:",
            layer_result[
                "trainable_layers"
            ]
        )

        # --------------------------------------------------
        # STEP 6
        # Create dataset
        # --------------------------------------------------

        dataset = (
            self.create_dataset()
        )

        # --------------------------------------------------
        # STEP 7
        # Create class mask
        # --------------------------------------------------

        class_mask = (
            self.create_class_mask()
        )

        # --------------------------------------------------
        # STEP 8
        # Training
        # --------------------------------------------------

        epoch_history = []

        start_time = (
            time.perf_counter()
        )

        print("\n")
        print("=" * 60)
        print("Starting Local Retraining")
        print("=" * 60)

        for epoch in range(
            EPOCHS
        ):

            losses = []

            accuracies = []

            for images, labels in dataset:

                loss, accuracy = (
                    self.train_one_batch(
                        images,
                        labels,
                        class_mask
                    )
                )

                losses.append(
                    loss
                )

                accuracies.append(
                    accuracy
                )

            average_loss = float(
                np.mean(
                    losses
                )
            )

            average_accuracy = float(
                np.mean(
                    accuracies
                )
            )

            epoch_history.append(
                {
                    "epoch": epoch + 1,
                    "loss": round(
                        average_loss,
                        6
                    ),
                    "accuracy": round(
                        average_accuracy,
                        6
                    )
                }
            )

            print(
                f"Epoch {epoch + 1}/{EPOCHS} "
                f"- loss: {average_loss:.4f} "
                f"- accuracy: {average_accuracy:.4f}"
            )

        training_time = (
            time.perf_counter()
            - start_time
        )

        # --------------------------------------------------
        # STEP 9
        # Save temporary model
        # --------------------------------------------------

        temporary_model = (
            self.save_temporary_updated_model()
        )

        # --------------------------------------------------
        # STEP 10
        # Verify temporary model
        # --------------------------------------------------

        print(
            "\nVerifying temporary model..."
        )

        verification = (
            self.verify_saved_model(
                temporary_model
            )
        )

        print(
            "Temporary verification:",
            verification
        )

        if not verification.get(
            "verified",
            False
        ):

            print(
                "\nTemporary model verification FAILED."
            )

            return {
                "status": (
                    "MODEL_VERIFICATION_FAILED"
                ),
                "batch_folders_deleted": False,
                "verification": verification
            }

        # --------------------------------------------------
        # STEP 11
        # Backup current model
        # --------------------------------------------------

        backup_result = (
            self.backup_current_files()
        )

        # --------------------------------------------------
        # STEP 12
        # Activate updated model
        # --------------------------------------------------

        self.activate_updated_model()

        # --------------------------------------------------
        # STEP 13
        # Verify active model
        # --------------------------------------------------

        print(
            "\nVerifying active model..."
        )

        final_verification = (
            self.verify_saved_model(
                self.active_model_path
            )
        )

        print(
            "Active model verification:",
            final_verification
        )

        if not final_verification.get(
            "verified",
            False
        ):

            print(
                "\nACTIVE MODEL VERIFICATION FAILED."
            )

            print(
                "Restoring previous model..."
            )

            shutil.copy2(
                backup_result[
                    "backup_model_path"
                ],
                self.active_model_path
            )

            return {
                "status": (
                    "ACTIVE_MODEL_VERIFICATION_FAILED"
                ),
                "backup_model": (
                    backup_result[
                        "backup_model_path"
                    ]
                ),
                "batch_folders_deleted": False,
                "verification": final_verification
            }

        # --------------------------------------------------
        # STEP 14
        # Cleanup
        # --------------------------------------------------

        cleanup_result = {
            "deleted_folder_count": 0,
            "deleted_folders": [],
            "failed_folders": []
        }

        if DELETE_BATCH_FOLDERS_AFTER_SUCCESS:

            cleanup_result = (
                self.delete_processed_class_folders()
            )

        # --------------------------------------------------
        # STEP 15
        # Save history
        # --------------------------------------------------

        self.save_training_history(
            epoch_history=(
                epoch_history
            ),
            training_time=(
                training_time
            ),
            backup_result=(
                backup_result
            ),
            cleanup_result=(
                cleanup_result
            )
        )

        # --------------------------------------------------
        # COMPLETE
        # --------------------------------------------------

        print("\n")
        print("=" * 60)
        print("LOCAL RETRAINING COMPLETED")
        print("=" * 60)

        print(
            "Updated GTSRB Classes:",
            self.active_class_ids
        )

        print(
            "Updated CNN Outputs:",
            [
                self.gtsrb_to_output[
                    class_id
                ]
                for class_id in (
                    self.active_class_ids
                )
            ]
        )

        print(
            "Total Images:",
            len(
                self.image_paths
            )
        )

        print(
            "Active Model:",
            self.active_model_path
        )

        print(
            "Previous Model:",
            backup_result[
                "backup_model_path"
            ]
        )

        print(
            "Deleted Folders:",
            cleanup_result[
                "deleted_folder_count"
            ]
        )

        print(
            "=" * 60
        )

        return {
            "status": (
                "LOCAL_RETRAINING_COMPLETED"
            ),
            "active_model": (
                self.active_model_path
            ),
            "previous_model_backup": (
                backup_result[
                    "backup_model_path"
                ]
            ),
            "updated_gtsrb_class_ids": (
                self.active_class_ids
            ),
            "updated_cnn_output_indices": {
                str(class_id):
                    self.gtsrb_to_output[class_id]
                for class_id in (
                    self.active_class_ids
                )
            },
            "total_images": len(
                self.image_paths
            ),
            "model_expanded": False,
            "model_output_classes": 43,
            "batch_cleanup": (
                cleanup_result
            )
        }


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    retrainer = (
        VehicleALocalModelRetrainer()
    )

    try:

        result = retrainer.retrain()

        print(
            "\nStatus:",
            result.get(
                "status"
            )
        )

        if (
            result.get(
                "status"
            )
            == "LOCAL_RETRAINING_COMPLETED"
        ):

            print(
                "Updated GTSRB Classes:",
                result.get(
                    "updated_gtsrb_class_ids"
                )
            )

            print(
                "Updated CNN Outputs:",
                result.get(
                    "updated_cnn_output_indices"
                )
            )

            print(
                "Active Model:",
                result.get(
                    "active_model"
                )
            )

            print(
                "Previous Model:",
                result.get(
                    "previous_model_backup"
                )
            )

    except Exception as error:

        print(
            "\nStatus: LOCAL_RETRAINING_FAILED"
        )

        print(
            "Error:",
            error
        )

        import traceback

        traceback.print_exc()