# global_verification_server/global_verification.py
# Global Verification Server
# Verification is based on cosine similarity between common embeddings.

import os
import pickle
import time

import numpy as np

try:
    from global_verification_server.reward_system import (
        calculate_verification_reward
    )
except ImportError:
    # Allows this file to be executed directly.
    from reward_system import calculate_verification_reward


class GlobalVerificationServer:

    def __init__(
        self,
        db_path=None,
        database_path=None,
        similarity_threshold=0.70
    ):
        self.similarity_threshold = float(
            similarity_threshold
        )

        # Support both parameter names.
        if database_path is not None:
            db_path = database_path

        if db_path is None:
            base_dir = os.path.dirname(
                os.path.abspath(__file__)
            )

            db_path = os.path.join(
                base_dir,
                "database",
                "global_verification_db.pkl"
            )

        self.db_path = db_path

        self.global_db = None
        self.records = []

        self.embedding_version = None
        self.embedding_length = None

        self.load_global_db()

    # ======================================================
    # LOAD GLOBAL VERIFICATION DATABASE
    # ======================================================

    def load_global_db(self):

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                "Global verification DB not found:\n"
                f"{self.db_path}"
            )

        with open(self.db_path, "rb") as file:
            self.global_db = pickle.load(file)

        if not isinstance(self.global_db, dict):
            raise ValueError(
                "Invalid global DB format. "
                "Expected a dictionary."
            )

        self.records = self.global_db.get(
            "records",
            []
        )

        self.embedding_version = self.global_db.get(
            "embedding_version"
        )

        self.embedding_length = self.global_db.get(
            "embedding_length"
        )

        if not isinstance(self.records, list):
            raise ValueError(
                "Invalid database format. "
                "'records' must be a list."
            )

        if not self.records:
            raise ValueError(
                "Global verification database "
                "contains no records."
            )

        print("Global Verification DB loaded")
        print("DB Path:", self.db_path)

        print(
            "Embedding Version:",
            self.embedding_version
        )

        print(
            "Embedding Length:",
            self.embedding_length
        )

        print(
            "Records in DB:",
            len(self.records)
        )

        print(
            "Classes in DB:",
            self.global_db.get(
                "total_classes",
                "unknown"
            )
        )

    # ======================================================
    # NORMALIZE EMBEDDING
    # ======================================================

    @staticmethod
    def normalize_embedding(embedding):

        try:
            vector = np.asarray(
                embedding,
                dtype=np.float32
            ).reshape(-1)

        except (TypeError, ValueError):
            return None

        if vector.size == 0:
            return None

        if not np.all(
            np.isfinite(vector)
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
        embedding_1,
        embedding_2
    ):

        vector_1 = (
            GlobalVerificationServer
            .normalize_embedding(
                embedding_1
            )
        )

        vector_2 = (
            GlobalVerificationServer
            .normalize_embedding(
                embedding_2
            )
        )

        if vector_1 is None:
            return None

        if vector_2 is None:
            return None

        if vector_1.shape != vector_2.shape:
            return None

        similarity = float(
            np.dot(
                vector_1,
                vector_2
            )
        )

        return similarity

    # ======================================================
    # CREATE ERROR RESULT
    # ======================================================

    def create_error_result(
        self,
        knowledge_package,
        reason,
        start_time
    ):

        verification_time = (
            time.perf_counter()
            - start_time
        )

        vehicle_id = knowledge_package.get(
            "vehicle_id"
        )

        return {
            "status": "ERROR",

            "vehicle_id": vehicle_id,

            "sign_id": knowledge_package.get(
                "sign_id"
            ),

            "target_vehicle": vehicle_id,

            "reason": reason,

            "similarity": 0.0,

            "threshold": (
                self.similarity_threshold
            ),

            # No RL reward is created for technical errors.
            "reward": 0.0,

            "reward_type": "NONE",

            "reward_reason": reason,

            "verification_time": round(
                verification_time,
                4
            ),

            "next_step": "STOP"
        }

    # ======================================================
    # VERIFY KNOWLEDGE PACKAGE
    # ======================================================

    def verify_knowledge_package(
        self,
        knowledge_package
    ):

        start_time = time.perf_counter()

        if not isinstance(
            knowledge_package,
            dict
        ):
            raise ValueError(
                "Knowledge package must be "
                "a dictionary."
            )

        vehicle_id = knowledge_package.get(
            "vehicle_id"
        )

        sign_id = knowledge_package.get(
            "sign_id"
        )

        # ==================================================
        # VALIDATE EMBEDDING
        # ==================================================

        if "embedding" not in knowledge_package:
            return self.create_error_result(
                knowledge_package=knowledge_package,
                reason="MISSING_EMBEDDING",
                start_time=start_time
            )

        query_embedding = (
            self.normalize_embedding(
                knowledge_package[
                    "embedding"
                ]
            )
        )

        if query_embedding is None:
            return self.create_error_result(
                knowledge_package=knowledge_package,
                reason=(
                    "INVALID_OR_EMPTY_EMBEDDING"
                ),
                start_time=start_time
            )

        # ==================================================
        # VALIDATE EMBEDDING VERSION
        # ==================================================

        query_embedding_version = (
            knowledge_package.get(
                "embedding_version"
            )
        )

        if query_embedding_version is None:
            return self.create_error_result(
                knowledge_package=knowledge_package,
                reason=(
                    "MISSING_EMBEDDING_VERSION"
                ),
                start_time=start_time
            )

        if (
            self.embedding_version is not None
            and query_embedding_version
            != self.embedding_version
        ):
            result = self.create_error_result(
                knowledge_package=knowledge_package,
                reason=(
                    "EMBEDDING_VERSION_MISMATCH"
                ),
                start_time=start_time
            )

            result[
                "query_embedding_version"
            ] = query_embedding_version

            result[
                "database_embedding_version"
            ] = self.embedding_version

            return result

        # ==================================================
        # VALIDATE EMBEDDING LENGTH
        # ==================================================

        query_embedding_length = len(
            query_embedding
        )

        if (
            self.embedding_length is not None
            and query_embedding_length
            != int(self.embedding_length)
        ):
            result = self.create_error_result(
                knowledge_package=knowledge_package,
                reason=(
                    "EMBEDDING_LENGTH_MISMATCH"
                ),
                start_time=start_time
            )

            result[
                "query_embedding_length"
            ] = query_embedding_length

            result[
                "database_embedding_length"
            ] = int(
                self.embedding_length
            )

            return result

        # ==================================================
        # FIND BEST DATABASE MATCH
        # ==================================================

        best_similarity = -1.0
        best_match = None

        checked_records = 0
        skipped_records = 0

        for record in self.records:

            if not isinstance(record, dict):
                skipped_records += 1
                continue

            record_embedding_version = (
                record.get(
                    "embedding_version"
                )
            )

            if (
                record_embedding_version
                != query_embedding_version
            ):
                skipped_records += 1
                continue

            db_embedding = record.get(
                "embedding"
            )

            if db_embedding is None:
                skipped_records += 1
                continue

            similarity = self.cosine_similarity(
                query_embedding,
                db_embedding
            )

            if similarity is None:
                skipped_records += 1
                continue

            checked_records += 1

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = record

        verification_time = (
            time.perf_counter()
            - start_time
        )

        # ==================================================
        # NO COMPATIBLE DATABASE RECORD
        # ==================================================

        if best_match is None:

            reward_result = (
                calculate_verification_reward(
                    similarity=0.0,
                    verified_class_id=None
                )
            )

            return {
                "status": "REJECTED",

                "vehicle_id": vehicle_id,

                "sign_id": sign_id,

                "target_vehicle": vehicle_id,

                "reason": (
                    "NO_COMPATIBLE_RECORD_IN_GLOBAL_DB"
                ),

                "verified_class_id": None,

                "verified_class_name": None,

                "category": None,

                "similarity": 0.0,

                "threshold": (
                    self.similarity_threshold
                ),

                "reward": float(
                    reward_result["reward"]
                ),

                "reward_type": (
                    reward_result[
                        "reward_type"
                    ]
                ),

                "reward_reason": (
                    reward_result[
                        "reason"
                    ]
                ),

                "records_checked": (
                    checked_records
                ),

                "records_skipped": (
                    skipped_records
                ),

                "verification_time": round(
                    verification_time,
                    4
                ),

                "next_step": (
                    "SEND_REWARD_TO_SOURCE_VEHICLE"
                )
            }

        best_similarity = float(
            best_similarity
        )

        # ==================================================
        # ACCEPTED KNOWLEDGE
        # ==================================================

        if (
            best_similarity
            >= self.similarity_threshold
        ):

            verified_class_id = (
                best_match.get(
                    "class_id"
                )
            )

            reward_result = (
                calculate_verification_reward(
                    similarity=best_similarity,
                    verified_class_id=(
                        verified_class_id
                    )
                )
            )

            return {
                "status": "ACCEPTED",

                "vehicle_id": vehicle_id,

                "sign_id": sign_id,

                # Reward must return to this vehicle.
                "target_vehicle": vehicle_id,

                "verified_class_id": (
                    verified_class_id
                ),

                "verified_class_name": (
                    best_match.get(
                        "class_name"
                    )
                ),

                "category": (
                    best_match.get(
                        "category"
                    )
                ),

                "knowledge_id": (
                    best_match.get(
                        "knowledge_id"
                    )
                ),

                "matched_source_image": (
                    best_match.get(
                        "source_image"
                    )
                ),

                "similarity": round(
                    best_similarity,
                    4
                ),

                "threshold": (
                    self.similarity_threshold
                ),

                "embedding_version": (
                    query_embedding_version
                ),

                "reward": float(
                    reward_result["reward"]
                ),

                "reward_type": (
                    reward_result[
                        "reward_type"
                    ]
                ),

                "reward_reason": (
                    reward_result[
                        "reason"
                    ]
                ),

                "records_checked": (
                    checked_records
                ),

                "records_skipped": (
                    skipped_records
                ),

                "verification_time": round(
                    verification_time,
                    4
                ),

                "next_step": (
                    "SEND_REWARD_AND_ADD_TO_BROADCAST"
                )
            }

        # ==================================================
        # REJECTED KNOWLEDGE
        # ==================================================

        reward_result = (
            calculate_verification_reward(
                similarity=best_similarity,
                verified_class_id=None
            )
        )

        return {
            "status": "REJECTED",

            "vehicle_id": vehicle_id,

            "sign_id": sign_id,

            # Reward must return to this vehicle.
            "target_vehicle": vehicle_id,

            "verified_class_id": None,

            "verified_class_name": None,

            "category": None,

            "best_candidate_class_id": (
                best_match.get(
                    "class_id"
                )
            ),

            "best_candidate_class_name": (
                best_match.get(
                    "class_name"
                )
            ),

            "best_candidate_category": (
                best_match.get(
                    "category"
                )
            ),

            "best_candidate_knowledge_id": (
                best_match.get(
                    "knowledge_id"
                )
            ),

            "similarity": round(
                best_similarity,
                4
            ),

            "threshold": (
                self.similarity_threshold
            ),

            "embedding_version": (
                query_embedding_version
            ),

            "reason": (
                "SIMILARITY_BELOW_THRESHOLD"
            ),

            "reward": float(
                reward_result["reward"]
            ),

            "reward_type": (
                reward_result[
                    "reward_type"
                ]
            ),

            "reward_reason": (
                reward_result[
                    "reason"
                ]
            ),

            "records_checked": (
                checked_records
            ),

            "records_skipped": (
                skipped_records
            ),

            "verification_time": round(
                verification_time,
                4
            ),

            "next_step": (
                "SEND_REWARD_TO_SOURCE_VEHICLE"
            )
        }


