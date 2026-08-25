# vehicles/vehicle_B/src/temp_db_checker.py
# Vehicle B Temporary Database Checker
#
# Checks current RARE / NEW sign embeddings against verified
# knowledge received from the global broadcast server.

import os
import pickle

import numpy as np

try:
    from src.batch_training_storage import (
        BatchTrainingStorage
    )
except ImportError:
    from batch_training_storage import (
        BatchTrainingStorage
    )


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VEHICLE_B_DIR = os.path.dirname(
    CURRENT_DIR
)

TEMP_DB_PATH = os.path.join(
    VEHICLE_B_DIR,
    "database",
    "received_knowledge.pkl"
)

TEMP_DATABASE_NAME = (
    "vehicle_B_received_knowledge"
)

SIMILARITY_THRESHOLD = 0.70


# ==========================================================
# TEMP DB CHECKER
# ==========================================================

class TempDBChecker:
    """
    Check whether a RARE / NEW sign embedding already exists
    in Vehicle B's local temporary database.

    The temporary database contains only verified knowledge
    received from the global broadcast server.

    Current detected embeddings are not saved to the local
    temporary database.

    When a match is found:
        1. Get the verified class ID.
        2. Save the cropped image through
           BatchTrainingStorage.
        3. Stop the remaining RL pipeline.
    """

    def __init__(
        self,
        database_path=TEMP_DB_PATH,
        similarity_threshold=SIMILARITY_THRESHOLD
    ):
        self.database_path = os.path.abspath(
            database_path
        )

        self.similarity_threshold = float(
            similarity_threshold
        )

        self.temp_db = []

        self.batch_training_storage = (
            BatchTrainingStorage()
        )

        self.create_database_if_missing()
        self.load_temp_db()

    # ======================================================
    # CREATE DATABASE IF MISSING
    # ======================================================

    def create_database_if_missing(self):
        """
        Create Vehicle B's local temporary database if the
        file does not exist.
        """

        database_directory = os.path.dirname(
            self.database_path
        )

        os.makedirs(
            database_directory,
            exist_ok=True
        )

        if os.path.exists(
            self.database_path
        ):
            return

        empty_database = {
            "database_name": (
                TEMP_DATABASE_NAME
            ),

            "database_version": "1.0",

            "vehicle_id": "Vehicle_B",

            "total_records": 0,

            "records": []
        }

        with open(
            self.database_path,
            "wb"
        ) as file:
            pickle.dump(
                empty_database,
                file
            )

    # ======================================================
    # LOAD TEMP DATABASE
    # ======================================================

    def load_temp_db(self):
        """
        Load verified knowledge from:

        vehicles/vehicle_B/database/
        received_knowledge.pkl
        """

        self.create_database_if_missing()

        try:
            with open(
                self.database_path,
                "rb"
            ) as file:
                database = pickle.load(
                    file
                )

        except (
            OSError,
            EOFError,
            pickle.PickleError
        ):
            self.temp_db = []

            return {
                "status": "ERROR",

                "database_name": (
                    TEMP_DATABASE_NAME
                ),

                "records_loaded": 0,

                "database_path": (
                    self.database_path
                )
            }

        if isinstance(
            database,
            dict
        ):
            database_name = database.get(
                "database_name",
                TEMP_DATABASE_NAME
            )

            records = database.get(
                "records",
                []
            )

        elif isinstance(
            database,
            list
        ):
            database_name = (
                TEMP_DATABASE_NAME
            )

            records = database

        else:
            database_name = (
                TEMP_DATABASE_NAME
            )

            records = []

        if not isinstance(
            records,
            list
        ):
            records = []

        self.temp_db = [
            record
            for record in records
            if isinstance(
                record,
                dict
            )
        ]

        return {
            "status": "LOADED",

            "database_name": (
                database_name
            ),

            "records_loaded": len(
                self.temp_db
            ),

            "database_path": (
                self.database_path
            )
        }

    # ======================================================
    # NORMALIZE EMBEDDING
    # ======================================================

    @staticmethod
    def normalize_embedding(
        embedding
    ):
        """
        Convert an embedding to a normalized NumPy vector.
        """

        try:
            vector = np.asarray(
                embedding,
                dtype=np.float32
            ).reshape(-1)

        except (
            TypeError,
            ValueError
        ):
            return None

        if vector.size == 0:
            return None

        if not np.all(
            np.isfinite(
                vector
            )
        ):
            return None

        norm = np.linalg.norm(
            vector
        )

        if norm < 1e-12:
            return None

        return vector / norm

    # ======================================================
    # COSINE SIMILARITY
    # ======================================================

    @staticmethod
    def cosine_similarity(
        embedding_a,
        embedding_b
    ):
        """
        Calculate cosine similarity between two embeddings.
        """

        vector_a = (
            TempDBChecker
            .normalize_embedding(
                embedding_a
            )
        )

        vector_b = (
            TempDBChecker
            .normalize_embedding(
                embedding_b
            )
        )

        if (
            vector_a is None
            or vector_b is None
        ):
            return None

        if (
            vector_a.shape
            != vector_b.shape
        ):
            return None

        return float(
            np.dot(
                vector_a,
                vector_b
            )
        )

    # ======================================================
    # NORMALIZE DATABASE RECORD
    # ======================================================

    @staticmethod
    def normalize_record(
        record
    ):
        """
        Convert broadcast database fields into a consistent
        local record structure.
        """

        if not isinstance(
            record,
            dict
        ):
            return None

        class_id = record.get(
            "verified_class_id"
        )

        if class_id is None:
            class_id = record.get(
                "class_id"
            )

        class_name = record.get(
            "verified_class_name"
        )

        if class_name is None:
            class_name = record.get(
                "class_name"
            )

        return {
            "queue_id": record.get(
                "queue_id"
            ),

            "class_id": class_id,

            "class_name": class_name,

            "verified_class_id": (
                class_id
            ),

            "verified_class_name": (
                class_name
            ),

            "category": record.get(
                "category"
            ),

            "embedding_version": (
                record.get(
                    "embedding_version"
                )
            ),

            "embedding_length": (
                record.get(
                    "embedding_length"
                )
            ),

            "embedding": record.get(
                "embedding"
            ),

            "source_vehicle": (
                record.get(
                    "source_vehicle"
                )
            ),

            "target_vehicle": (
                record.get(
                    "target_vehicle"
                )
            ),

            "sign_id": record.get(
                "sign_id"
            ),

            "source": (
                "global_broadcast"
            ),

            "received_at": record.get(
                "received_at"
            )
        }

    # ======================================================
    # CHECK EMBEDDING
    # ======================================================

    def check_embedding(
        self,
        embedding,
        embedding_version=None
    ):
        """
        Compare the current sign embedding with all verified
        embeddings in Vehicle B's temporary database.
        """

        # Reload every time so newly broadcast knowledge is
        # immediately available.
        load_result = self.load_temp_db()

        if load_result.get(
            "status"
        ) == "ERROR":
            return {
                "status": "ERROR",

                "best_similarity": 0.0,

                "matched_record": None,

                "records_checked": 0,

                "records_skipped": 0,

                "message": (
                    "TEMP_DATABASE_LOAD_FAILED"
                )
            }

        query_embedding = (
            self.normalize_embedding(
                embedding
            )
        )

        if query_embedding is None:
            return {
                "status": "ERROR",

                "best_similarity": 0.0,

                "matched_record": None,

                "records_checked": 0,

                "records_skipped": 0,

                "message": (
                    "INVALID_QUERY_EMBEDDING"
                )
            }

        if not self.temp_db:
            return {
                "status": "NO_MATCH",

                "best_similarity": 0.0,

                "matched_record": None,

                "records_checked": 0,

                "records_skipped": 0
            }

        best_similarity = -1.0
        matched_record = None

        records_checked = 0
        records_skipped = 0

        for record in self.temp_db:

            normalized_record = (
                self.normalize_record(
                    record
                )
            )

            if normalized_record is None:
                records_skipped += 1
                continue

            stored_embedding = (
                normalized_record.get(
                    "embedding"
                )
            )

            if stored_embedding is None:
                records_skipped += 1
                continue

            stored_embedding_version = (
                normalized_record.get(
                    "embedding_version"
                )
            )

            if (
                embedding_version is not None
                and stored_embedding_version
                is not None
                and embedding_version
                != stored_embedding_version
            ):
                records_skipped += 1
                continue

            similarity = (
                self.cosine_similarity(
                    query_embedding,
                    stored_embedding
                )
            )

            if similarity is None:
                records_skipped += 1
                continue

            records_checked += 1

            if similarity > best_similarity:
                best_similarity = (
                    similarity
                )

                matched_record = (
                    normalized_record
                )

        if matched_record is None:
            return {
                "status": "NO_MATCH",

                "best_similarity": 0.0,

                "matched_record": None,

                "records_checked": (
                    records_checked
                ),

                "records_skipped": (
                    records_skipped
                )
            }

        if (
            best_similarity
            >= self.similarity_threshold
        ):
            return {
                "status": "MATCH_FOUND",

                "best_similarity": round(
                    best_similarity,
                    4
                ),

                "matched_record": (
                    matched_record
                ),

                "records_checked": (
                    records_checked
                ),

                "records_skipped": (
                    records_skipped
                )
            }

        return {
            "status": "NO_MATCH",

            "best_similarity": round(
                best_similarity,
                4
            ),

            "matched_record": None,

            "records_checked": (
                records_checked
            ),

            "records_skipped": (
                records_skipped
            )
        }

    # ======================================================
    # PROCESS ITEM
    # ======================================================

    def process_item(
        self,
        item
    ):
        """
        Process one RARE / NEW sign.

        Match found:
            save crop through BatchTrainingStorage;
            stop before feature extraction and RL.

        No match:
            continue to feature extraction and RL.
        """

        if not isinstance(
            item,
            dict
        ):
            return {
                "status": "ERROR",
                "similarity": 0.0,
                "action": "STOP",
                "message": "INVALID_ITEM"
            }

        embedding = item.get(
            "embedding"
        )

        cropped_sign = item.get(
            "cropped_sign"
        )

        embedding_version = item.get(
            "embedding_version"
        )

        if embedding is None:
            return {
                "status": "ERROR",
                "similarity": 0.0,
                "action": "STOP",
                "message": (
                    "MISSING_EMBEDDING"
                )
            }

        check_result = self.check_embedding(
            embedding=embedding,
            embedding_version=(
                embedding_version
            )
        )

        check_status = check_result.get(
            "status"
        )

        if check_status == "ERROR":
            return {
                "status": "ERROR",

                "similarity": 0.0,

                "action": "STOP",

                "message": check_result.get(
                    "message",
                    "TEMP_DB_CHECK_FAILED"
                )
            }

        if check_status == "MATCH_FOUND":

            matched_record = (
                check_result.get(
                    "matched_record"
                )
            )

            if not isinstance(
                matched_record,
                dict
            ):
                return {
                    "status": "ERROR",

                    "similarity": (
                        check_result.get(
                            "best_similarity",
                            0.0
                        )
                    ),

                    "action": "STOP",

                    "message": (
                        "INVALID_MATCHED_RECORD"
                    )
                }

            verified_class_id = (
                matched_record.get(
                    "verified_class_id"
                )
            )

            verified_class_name = (
                matched_record.get(
                    "verified_class_name"
                )
            )

            category = matched_record.get(
                "category"
            )

            storage_result = (
                self.batch_training_storage
                .save_crop(
                    cropped_sign=(
                        cropped_sign
                    ),

                    class_id=(
                        verified_class_id
                    ),

                    class_name=(
                        verified_class_name
                    ),

                    category=category,

                    source="temp_db_match"
                )
            )

            if not storage_result.get(
                "saved",
                False
            ):
                return {
                    "status": "ERROR",

                    "similarity": (
                        check_result.get(
                            "best_similarity",
                            0.0
                        )
                    ),

                    "action": "STOP",

                    "message": (
                        storage_result.get(
                            "reason",
                            "BATCH_TRAINING_SAVE_FAILED"
                        )
                    ),

                    "matched_record": (
                        matched_record
                    ),

                    "storage_result": (
                        storage_result
                    )
                }

            class_image_count = (
                self.batch_training_storage
                .count_class_images(
                    verified_class_id
                )
            )

            return {
                "status": "MATCH_FOUND",

                "similarity": (
                    check_result.get(
                        "best_similarity",
                        0.0
                    )
                ),

                "action": (
                    "SAVED_FOR_BATCH_TRAINING"
                ),

                "verified_class_id": (
                    verified_class_id
                ),

                "verified_class_name": (
                    verified_class_name
                ),

                "category": category,

                "matched_record": (
                    matched_record
                ),

                "saved_paths": {
                    "image_path": (
                        storage_result.get(
                            "image_path"
                        )
                    ),

                    "class_directory": (
                        storage_result.get(
                            "class_directory"
                        )
                    )
                },

                "storage_result": (
                    storage_result
                ),

                "class_image_count": (
                    class_image_count
                ),

                "records_checked": (
                    check_result.get(
                        "records_checked",
                        0
                    )
                ),

                "records_skipped": (
                    check_result.get(
                        "records_skipped",
                        0
                    )
                )
            }

        return {
            "status": "NO_MATCH",

            "similarity": (
                check_result.get(
                    "best_similarity",
                    0.0
                )
            ),

            "action": (
                "PASS_TO_NEXT_STEP"
            ),

            "matched_record": None,

            "records_checked": (
                check_result.get(
                    "records_checked",
                    0
                )
            ),

            "records_skipped": (
                check_result.get(
                    "records_skipped",
                    0
                )
            )
        }