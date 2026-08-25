# global_verification_server/broadcast_queue.py
# Temporary queue for accepted knowledge packages.
#
# Only accepted knowledge is stored.
# Successfully broadcast records are deleted.
# Failed records remain for later retry.

import os
import pickle
import time
import uuid


# ==========================================================
# ACCEPTED VERIFICATION STATUSES
# ==========================================================

ACCEPTED_STATUSES = {
    "ACCEPTED",
    "VERIFIED",
    "MATCH_FOUND"
}


# ==========================================================
# BROADCAST QUEUE
# ==========================================================

class BroadcastQueue:
    """
    Global temporary broadcast queue.

    Flow:
        accepted knowledge
            -> store in queue
            -> broadcast to vehicle
            -> confirm vehicle storage
            -> delete from queue
    """

    def __init__(
        self,
        database_path=None
    ):
        if database_path is None:
            current_dir = os.path.dirname(
                os.path.abspath(__file__)
            )

            database_path = os.path.join(
                current_dir,
                "database",
                "broadcast_queue.pkl"
            )

        self.database_path = os.path.abspath(
            database_path
        )

        self.records = []

        self.create_database_directory()
        self.load_queue()

    # ======================================================
    # CREATE DATABASE DIRECTORY
    # ======================================================

    def create_database_directory(self):

        database_directory = os.path.dirname(
            self.database_path
        )

        os.makedirs(
            database_directory,
            exist_ok=True
        )

    # ======================================================
    # LOAD QUEUE
    # ======================================================

    def load_queue(self):

        if not os.path.exists(
            self.database_path
        ):
            self.records = []
            self.save_queue()
            return

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
            self.records = []
            self.save_queue()
            return

        if isinstance(database, dict):
            records = database.get(
                "records",
                []
            )

        elif isinstance(database, list):
            records = database

        else:
            records = []

        if not isinstance(records, list):
            records = []

        self.records = records

    # ======================================================
    # SAVE QUEUE
    # ======================================================

    def save_queue(self):

        database = {
            "database_name": "broadcast_queue",
            "database_version": "1.0",
            "total_records": len(
                self.records
            ),
            "updated_at": time.time(),
            "records": self.records
        }

        temporary_path = (
            self.database_path + ".tmp"
        )

        with open(
            temporary_path,
            "wb"
        ) as file:
            pickle.dump(
                database,
                file
            )

        os.replace(
            temporary_path,
            self.database_path
        )

    # ======================================================
    # CHECK DUPLICATE PACKAGE
    # ======================================================

    def package_exists(
        self,
        source_vehicle,
        sign_id
    ):

        for record in self.records:

            if not isinstance(record, dict):
                continue

            same_vehicle = (
                record.get("source_vehicle")
                == source_vehicle
            )

            same_sign = (
                record.get("sign_id")
                == sign_id
            )

            if same_vehicle and same_sign:
                return True

        return False

    # ======================================================
    # ADD ACCEPTED PACKAGE
    # ======================================================

    def add_accepted_package(
        self,
        knowledge_package,
        verification_result
    ):
        """
        Store only globally accepted knowledge.

        Rejected, unknown and error records are ignored.
        """

        if not isinstance(
            knowledge_package,
            dict
        ):
            return {
                "status": "IGNORED",
                "stored": False,
                "reason": (
                    "INVALID_KNOWLEDGE_PACKAGE"
                )
            }

        if not isinstance(
            verification_result,
            dict
        ):
            return {
                "status": "IGNORED",
                "stored": False,
                "reason": (
                    "INVALID_VERIFICATION_RESULT"
                )
            }

        verification_status = str(
            verification_result.get(
                "status",
                ""
            )
        ).upper()

        if (
            verification_status
            not in ACCEPTED_STATUSES
        ):
            return {
                "status": "IGNORED",
                "stored": False,
                "reason": (
                    "KNOWLEDGE_NOT_ACCEPTED"
                )
            }

        embedding = knowledge_package.get(
            "embedding"
        )

        if embedding is None:
            return {
                "status": "IGNORED",
                "stored": False,
                "reason": "MISSING_EMBEDDING"
            }

        verified_class_id = (
            verification_result.get(
                "verified_class_id"
            )
        )

        if verified_class_id is None:
            return {
                "status": "IGNORED",
                "stored": False,
                "reason": (
                    "MISSING_VERIFIED_CLASS_ID"
                )
            }

        source_vehicle = (
            verification_result.get(
                "target_vehicle"
            )
            or verification_result.get(
                "vehicle_id"
            )
            or knowledge_package.get(
                "vehicle_id"
            )
        )

        sign_id = (
            verification_result.get(
                "sign_id"
            )
            or knowledge_package.get(
                "sign_id"
            )
        )

        if self.package_exists(
            source_vehicle=source_vehicle,
            sign_id=sign_id
        ):
            return {
                "status": "ALREADY_STORED",
                "stored": True,
                "source_vehicle": (
                    source_vehicle
                ),
                "sign_id": sign_id,
                "pending_records": len(
                    self.records
                )
            }

        queue_id = str(
            uuid.uuid4()
        )

        record = {
            "queue_id": queue_id,

            "broadcast_status": "PENDING",

            "source_vehicle": (
                source_vehicle
            ),

            "sign_id": sign_id,

            "verified_class_id": int(
                verified_class_id
            ),

            "verified_class_name": (
                verification_result.get(
                    "verified_class_name"
                )
            ),

            "category": (
                verification_result.get(
                    "category"
                )
            ),

            "embedding_version": (
                knowledge_package.get(
                    "embedding_version"
                )
            ),

            "embedding_length": (
                knowledge_package.get(
                    "embedding_length",
                    len(embedding)
                )
            ),

            "embedding": embedding,

            "similarity": float(
                verification_result.get(
                    "similarity",
                    0.0
                )
            ),

            "reward": float(
                verification_result.get(
                    "reward",
                    0.0
                )
            ),

            "created_at": time.time(),

            "broadcast_attempts": 0
        }

        self.records.append(
            record
        )

        self.save_queue()

        return {
            "status": (
                "STORED_FOR_BROADCAST"
            ),

            "stored": True,

            "queue_id": queue_id,

            "source_vehicle": (
                source_vehicle
            ),

            "sign_id": sign_id,

            "verified_class_id": int(
                verified_class_id
            ),

            "verified_class_name": (
                verification_result.get(
                    "verified_class_name"
                )
            ),

            "category": (
                verification_result.get(
                    "category"
                )
            ),

            "pending_records": len(
                self.records
            ),

            "database_path": (
                self.database_path
            )
        }

    # ======================================================
    # GET PENDING PACKAGES
    # ======================================================

    def get_pending_packages(self):

        return [
            record
            for record in self.records
            if (
                isinstance(record, dict)
                and record.get(
                    "broadcast_status"
                ) == "PENDING"
            )
        ]

    # ======================================================
    # RECORD BROADCAST ATTEMPT
    # ======================================================

    def record_broadcast_attempt(
        self,
        queue_id
    ):

        for record in self.records:

            if not isinstance(record, dict):
                continue

            if record.get(
                "queue_id"
            ) == queue_id:

                record[
                    "broadcast_attempts"
                ] = int(
                    record.get(
                        "broadcast_attempts",
                        0
                    )
                ) + 1

                record[
                    "last_broadcast_attempt"
                ] = time.time()

                self.save_queue()

                return {
                    "status": (
                        "ATTEMPT_RECORDED"
                    ),
                    "queue_id": queue_id,
                    "broadcast_attempts": (
                        record[
                            "broadcast_attempts"
                        ]
                    )
                }

        return {
            "status": "NOT_FOUND",
            "queue_id": queue_id
        }

    # ======================================================
    # DELETE ONE RECORD
    # ======================================================

    def delete_after_broadcast(
        self,
        queue_id
    ):

        original_count = len(
            self.records
        )

        self.records = [
            record
            for record in self.records
            if record.get(
                "queue_id"
            ) != queue_id
        ]

        if len(self.records) == original_count:
            return {
                "status": "NOT_FOUND",
                "deleted": False,
                "queue_id": queue_id
            }

        self.save_queue()

        return {
            "status": (
                "DELETED_AFTER_BROADCAST"
            ),
            "deleted": True,
            "queue_id": queue_id,
            "remaining_records": len(
                self.records
            )
        }

    # ======================================================
    # DELETE MULTIPLE SUCCESSFUL RECORDS
    # ======================================================

    def delete_successful_records(
        self,
        queue_ids
    ):

        if queue_ids is None:
            queue_ids = []

        queue_ids = {
            str(queue_id)
            for queue_id in queue_ids
            if queue_id is not None
        }

        if not queue_ids:
            return {
                "status": "NOTHING_TO_DELETE",
                "deleted_records": 0,
                "remaining_records": len(
                    self.records
                )
            }

        original_count = len(
            self.records
        )

        self.records = [
            record
            for record in self.records
            if str(
                record.get(
                    "queue_id"
                )
            ) not in queue_ids
        ]

        deleted_records = (
            original_count
            - len(self.records)
        )

        if deleted_records > 0:
            self.save_queue()

        return {
            "status": (
                "SUCCESSFUL_RECORDS_DELETED"
            ),
            "deleted_records": (
                deleted_records
            ),
            "remaining_records": len(
                self.records
            )
        }

    # ======================================================
    # QUEUE SIZE
    # ======================================================

    def get_queue_size(self):

        return len(
            self.records
        )

    # ======================================================
    # CLEAR ENTIRE QUEUE
    # ======================================================

    def clear_queue(self):

        removed_records = len(
            self.records
        )

        self.records = []

        self.save_queue()

        return {
            "status": "QUEUE_CLEARED",
            "removed_records": (
                removed_records
            ),
            "remaining_records": 0
        }