# global_verification_server/broadcast_knowledge.py
# Broadcast accepted knowledge to Vehicle A, Vehicle B, and Vehicle C.
#
# Running this file directly will:
# 1. Create each vehicle's local temporary database if missing.
# 2. Read pending accepted packages from broadcast_queue.pkl.
# 3. Save them into each vehicle's received_knowledge.pkl.
# 4. Delete successfully delivered packages from the
#    global broadcast queue.
# 5. Keep failed packages in the queue for retry.

import os
import pickle
import time
from datetime import datetime, timezone

import numpy as np

try:
    from global_verification_server.broadcast_queue import (
        BroadcastQueue
    )
except ImportError:
    from broadcast_queue import (
        BroadcastQueue
    )


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    CURRENT_DIR
)

GLOBAL_BROADCAST_QUEUE_PATH = os.path.join(
    CURRENT_DIR,
    "database",
    "broadcast_queue.pkl"
)

# Vehicle paths
VEHICLES = ["Vehicle_A", "Vehicle_B", "Vehicle_C"]

VEHICLE_TEMP_DB_PATHS = {
    "Vehicle_A": os.path.join(
        PROJECT_ROOT,
        "vehicles",
        "vehicle_A",
        "database",
        "received_knowledge.pkl"
    ),
    "Vehicle_B": os.path.join(
        PROJECT_ROOT,
        "vehicles",
        "vehicle_B",
        "database",
        "received_knowledge.pkl"
    ),
    "Vehicle_C": os.path.join(
        PROJECT_ROOT,
        "vehicles",
        "vehicle_C",
        "database",
        "received_knowledge.pkl"
    )
}


# ==========================================================
# VEHICLE BROADCAST RECEIVER
# ==========================================================

class VehicleBroadcastReceiver:
    """
    Receives verified knowledge from the global broadcast
    server and stores it in a vehicle's local temporary DB.
    """

    def __init__(
        self,
        vehicle_id,
        database_path
    ):
        self.vehicle_id = vehicle_id
        self.database_path = os.path.abspath(
            database_path
        )

        self.records = []

        self.create_database_directory()
        self.load_database()

    # ======================================================
    # CREATE DATABASE DIRECTORY
    # ======================================================

    def create_database_directory(self):
        """
        Create the vehicle's database directory.
        """

        database_directory = os.path.dirname(
            self.database_path
        )

        os.makedirs(
            database_directory,
            exist_ok=True
        )

    # ======================================================
    # CREATE EMPTY DATABASE
    # ======================================================

    def create_empty_database(self):
        """
        Create an empty vehicle temporary database.
        """

        self.records = []

        self.save_database()

        return {
            "status": "DATABASE_CREATED",
            "vehicle_id": self.vehicle_id,
            "database_path": self.database_path,
            "total_records": 0
        }

    # ======================================================
    # LOAD VEHICLE DATABASE
    # ======================================================

    def load_database(self):
        """
        Load the vehicle's local temporary database.

        If the database does not exist, create it.
        """

        if not os.path.exists(
            self.database_path
        ):
            self.create_empty_database()
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
            self.create_empty_database()
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

        if not isinstance(
            records,
            list
        ):
            records = []

        self.records = [
            record
            for record in records
            if isinstance(record, dict)
        ]

    # ======================================================
    # SAVE VEHICLE DATABASE
    # ======================================================

    def save_database(self):
        """
        Save the vehicle's temporary knowledge database.
        """

        database = {
            "database_name": (
                f"{self.vehicle_id.lower()}_received_knowledge"
            ),

            "database_version": "1.0",

            "vehicle_id": self.vehicle_id,

            "total_records": len(
                self.records
            ),

            "updated_at": (
                self.current_time_iso()
            ),

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
    # CURRENT TIME
    # ======================================================

    @staticmethod
    def current_time_iso():
        return datetime.now(
            timezone.utc
        ).isoformat()

    # ======================================================
    # VALIDATE EMBEDDING
    # ======================================================

    @staticmethod
    def validate_embedding(
        embedding
    ):
        """
        Validate and normalize a received embedding.
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
            np.isfinite(vector)
        ):
            return None

        norm = np.linalg.norm(
            vector
        )

        if norm < 1e-12:
            return None

        vector = vector / norm

        return vector.tolist()

    # ======================================================
    # CHECK DUPLICATE QUEUE ID
    # ======================================================

    def queue_id_exists(
        self,
        queue_id
    ):
        """
        Check whether this broadcast package was already
        received by this vehicle.
        """

        return any(
            (
                isinstance(record, dict)
                and record.get(
                    "queue_id"
                ) == queue_id
            )
            for record in self.records
        )

    # ======================================================
    # RECEIVE ONE KNOWLEDGE PACKAGE
    # ======================================================

    def receive_knowledge(
        self,
        broadcast_record
    ):
        """
        Save one broadcast package into the vehicle's
        local temporary database.
        """

        if not isinstance(
            broadcast_record,
            dict
        ):
            return {
                "status": "FAILED",
                "stored": False,
                "reason": (
                    "INVALID_BROADCAST_RECORD"
                )
            }

        queue_id = broadcast_record.get(
            "queue_id"
        )

        if queue_id is None:
            return {
                "status": "FAILED",
                "stored": False,
                "reason": "MISSING_QUEUE_ID"
            }

        if self.queue_id_exists(
            queue_id
        ):
            return {
                "status": "ALREADY_RECEIVED",
                "stored": True,
                "queue_id": queue_id,
                "vehicle_id": self.vehicle_id,
                "database_path": (
                    self.database_path
                )
            }

        embedding = self.validate_embedding(
            broadcast_record.get(
                "embedding"
            )
        )

        if embedding is None:
            return {
                "status": "FAILED",
                "stored": False,
                "reason": "INVALID_EMBEDDING",
                "queue_id": queue_id
            }

        verified_class_id = (
            broadcast_record.get(
                "verified_class_id"
            )
        )

        if verified_class_id is None:
            return {
                "status": "FAILED",
                "stored": False,
                "reason": (
                    "MISSING_VERIFIED_CLASS_ID"
                ),
                "queue_id": queue_id
            }

        received_record = {
            "queue_id": queue_id,

            "knowledge_status": (
                "RECEIVED_FROM_GLOBAL_BROADCAST"
            ),

            "target_vehicle": self.vehicle_id,

            "source_vehicle": (
                broadcast_record.get(
                    "source_vehicle"
                )
            ),

            "sign_id": (
                broadcast_record.get(
                    "sign_id"
                )
            ),

            "verified_class_id": int(
                verified_class_id
            ),

            "verified_class_name": (
                broadcast_record.get(
                    "verified_class_name"
                )
            ),

            "category": (
                broadcast_record.get(
                    "category"
                )
            ),

            "embedding_version": (
                broadcast_record.get(
                    "embedding_version"
                )
            ),

            "embedding_length": len(
                embedding
            ),

            "embedding": embedding,

            "similarity": float(
                broadcast_record.get(
                    "similarity",
                    0.0
                )
            ),

            "reward": float(
                broadcast_record.get(
                    "reward",
                    0.0
                )
            ),

            "broadcast_attempts": int(
                broadcast_record.get(
                    "broadcast_attempts",
                    0
                )
            ),

            "global_queue_created_at": (
                broadcast_record.get(
                    "created_at"
                )
            ),

            "received_at": (
                self.current_time_iso()
            ),

            "received_timestamp": (
                time.time()
            )
        }

        self.records.append(
            received_record
        )

        try:
            self.save_database()

        except OSError as error:
            self.records = [
                record
                for record in self.records
                if record.get(
                    "queue_id"
                ) != queue_id
            ]

            return {
                "status": "FAILED",
                "stored": False,
                "reason": (
                    f"{self.vehicle_id}_TEMP_DB_SAVE_FAILED"
                ),
                "error": str(error),
                "queue_id": queue_id
            }

        return {
            "status": (
                f"STORED_IN_{self.vehicle_id}_TEMP_DB"
            ),

            "stored": True,

            "queue_id": queue_id,

            "vehicle_id": self.vehicle_id,

            "verified_class_id": int(
                verified_class_id
            ),

            "verified_class_name": (
                broadcast_record.get(
                    "verified_class_name"
                )
            ),

            "category": (
                broadcast_record.get(
                    "category"
                )
            ),

            "total_vehicle_records": len(
                self.records
            ),

            "database_path": (
                self.database_path
            )
        }

    # ======================================================
    # GET ALL LOCAL RECORDS
    # ======================================================

    def get_all_records(self):
        return list(
            self.records
        )

    # ======================================================
    # GET RECORDS BY CLASS
    # ======================================================

    def get_records_by_class(
        self,
        class_id
    ):
        class_id = int(
            class_id
        )

        return [
            record
            for record in self.records
            if record.get(
                "verified_class_id"
            ) == class_id
        ]

    # ======================================================
    # CLEAR VEHICLE TEMP DATABASE
    # ======================================================

    def clear_vehicle_temp_database(self):
        """
        Clear the vehicle's temporary knowledge after it has
        finished using the broadcast knowledge.
        """

        removed_records = len(
            self.records
        )

        self.records = []

        self.save_database()

        return {
            "status": (
                f"{self.vehicle_id}_TEMP_DB_CLEARED"
            ),

            "vehicle_id": self.vehicle_id,

            "removed_records": (
                removed_records
            ),

            "remaining_records": 0,

            "database_path": (
                self.database_path
            )
        }


# ==========================================================
# KNOWLEDGE BROADCAST SERVICE
# ==========================================================

class KnowledgeBroadcastService:
    """
    Broadcast pending accepted knowledge from the global
    queue to all vehicles (Vehicle A, B, C).

    Successful packages are removed from the global queue.

    Failed packages remain in the queue for retry.
    """

    def __init__(
        self,
        queue_path=GLOBAL_BROADCAST_QUEUE_PATH,
        vehicle_paths=VEHICLE_TEMP_DB_PATHS
    ):
        self.broadcast_queue = (
            BroadcastQueue(
                database_path=queue_path
            )
        )

        self.vehicle_receivers = {}

        for vehicle_id, db_path in vehicle_paths.items():
            self.vehicle_receivers[vehicle_id] = (
                VehicleBroadcastReceiver(
                    vehicle_id=vehicle_id,
                    database_path=db_path
                )
            )

    # ======================================================
    # BROADCAST ONE PACKAGE TO ONE VEHICLE
    # ======================================================

    def broadcast_one_to_vehicle(
        self,
        broadcast_record,
        vehicle_id
    ):
        if not isinstance(
            broadcast_record,
            dict
        ):
            return {
                "status": "BROADCAST_FAILED",
                "success": False,
                "reason": (
                    "INVALID_BROADCAST_RECORD"
                )
            }

        queue_id = broadcast_record.get(
            "queue_id"
        )

        if queue_id is None:
            return {
                "status": "BROADCAST_FAILED",
                "success": False,
                "reason": "MISSING_QUEUE_ID"
            }

        receiver = self.vehicle_receivers.get(
            vehicle_id
        )

        if receiver is None:
            return {
                "status": "BROADCAST_FAILED",
                "success": False,
                "reason": "INVALID_VEHICLE_ID",
                "queue_id": queue_id,
                "vehicle_id": vehicle_id
            }

        self.broadcast_queue.record_broadcast_attempt(
            queue_id=queue_id
        )

        self.broadcast_queue.load_queue()

        updated_record = next(
            (
                record
                for record
                in self.broadcast_queue.records
                if record.get(
                    "queue_id"
                ) == queue_id
            ),
            broadcast_record
        )

        receive_result = (
            receiver.receive_knowledge(
                broadcast_record=(
                    updated_record
                )
            )
        )

        if not receive_result.get(
            "stored",
            False
        ):
            return {
                "status": (
                    "BROADCAST_FAILED"
                ),

                "success": False,

                "queue_id": queue_id,

                "target_vehicle": vehicle_id,

                "reason": (
                    receive_result.get(
                        "reason",
                        "VEHICLE_STORAGE_FAILED"
                    )
                ),

                "queue_action": (
                    "KEEP_FOR_RETRY"
                )
            }

        return {
            "status": (
                "BROADCAST_COMPLETED"
            ),

            "success": True,

            "queue_id": queue_id,

            "target_vehicle": vehicle_id,

            "verified_class_id": (
                receive_result.get(
                    "verified_class_id"
                )
            ),

            "verified_class_name": (
                receive_result.get(
                    "verified_class_name"
                )
            ),

            "category": (
                receive_result.get(
                    "category"
                )
            ),

            "vehicle_temp_db": (
                receive_result.get(
                    "database_path"
                )
            ),

            "queue_action": (
                "DELETE_DURING_CLEANUP"
            )
        }

    # ======================================================
    # BROADCAST ONE PACKAGE TO ALL VEHICLES
    # ======================================================

    def broadcast_one_to_all_vehicles(
        self,
        broadcast_record
    ):
        results = {}

        for vehicle_id in VEHICLES:
            result = self.broadcast_one_to_vehicle(
                broadcast_record=broadcast_record,
                vehicle_id=vehicle_id
            )

            results[vehicle_id] = result

        all_successful = all(
            result.get("success", False)
            for result in results.values()
        )

        return {
            "status": (
                "BROADCAST_TO_ALL_VEHICLES_COMPLETED"
            ),

            "queue_id": broadcast_record.get(
                "queue_id"
            ),

            "all_successful": all_successful,

            "results": results
        }

    # ======================================================
    # CLEAN SUCCESSFUL QUEUE RECORDS
    # ======================================================

    def clean_broadcast_queue(
        self,
        successful_queue_ids
    ):
        """
        Delete successfully delivered records from the
        global broadcast queue.
        """

        cleanup_result = (
            self.broadcast_queue
            .delete_successful_records(
                queue_ids=(
                    successful_queue_ids
                )
            )
        )

        return {
            "status": (
                "BROADCAST_QUEUE_CLEANED"
            ),

            "deleted_records": (
                cleanup_result.get(
                    "deleted_records",
                    0
                )
            ),

            "remaining_records": (
                cleanup_result.get(
                    "remaining_records",
                    0
                )
            )
        }

    # ======================================================
    # BROADCAST ALL PACKAGES
    # ======================================================

    def broadcast_all_to_all_vehicles(self):
        """
        Broadcast all pending packages to all vehicles.
        """

        pending_packages = (
            self.broadcast_queue
            .get_pending_packages()
        )

        package_results = []
        successful_queue_ids = []

        for broadcast_record in list(
            pending_packages
        ):
            result = (
                self.broadcast_one_to_all_vehicles(
                    broadcast_record
                )
            )

            package_results.append(result)

            if result.get(
                "all_successful",
                False
            ):
                queue_id = broadcast_record.get(
                    "queue_id"
                )

                if queue_id is not None:
                    successful_queue_ids.append(
                        queue_id
                    )

        cleanup_result = (
            self.clean_broadcast_queue(
                successful_queue_ids=(
                    successful_queue_ids
                )
            )
        )

        total_packages = len(
            pending_packages
        )

        successful_packages = len(
            successful_queue_ids
        )

        failed_packages = (
            total_packages
            - successful_packages
        )

        return {
            "status": (
                "BROADCAST_PROCESS_COMPLETED"
            ),

            "target_vehicles": VEHICLES,

            "pending_packages_found": (
                total_packages
            ),

            "successful_packages": (
                successful_packages
            ),

            "failed_packages": failed_packages,

            "queue_records_deleted": (
                cleanup_result.get(
                    "deleted_records",
                    0
                )
            ),

            "remaining_queue_records": (
                cleanup_result.get(
                    "remaining_records",
                    0
                )
            ),

            "results": package_results
        }

    # ======================================================
    # GET VEHICLE RECEIVER
    # ======================================================

    def get_vehicle_receiver(
        self,
        vehicle_id
    ):
        return self.vehicle_receivers.get(
            vehicle_id
        )

    # ======================================================
    # CLEAR VEHICLE TEMP DATABASE
    # ======================================================

    def clear_vehicle_temp_database(
        self,
        vehicle_id
    ):
        receiver = self.vehicle_receivers.get(
            vehicle_id
        )

        if receiver is None:
            return {
                "status": "FAILED",
                "reason": "INVALID_VEHICLE_ID",
                "vehicle_id": vehicle_id
            }

        return receiver.clear_vehicle_temp_database()

    # ======================================================
    # CLEAR ALL VEHICLE TEMP DATABASES
    # ======================================================

    def clear_all_vehicle_temp_databases(self):
        results = {}

        for vehicle_id in VEHICLES:
            results[vehicle_id] = (
                self.clear_vehicle_temp_database(
                    vehicle_id
                )
            )

        return {
            "status": "ALL_VEHICLE_DATABASES_CLEARED",
            "results": results
        }


# ==========================================================
# RUN DIRECTLY
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Knowledge Broadcast Service")
    print("=" * 60)

    broadcast_service = (
        KnowledgeBroadcastService()
    )

    print("Target Vehicles:", VEHICLES)

    for vehicle_id in VEHICLES:
        db_path = VEHICLE_TEMP_DB_PATHS[vehicle_id]
        print(f"{vehicle_id} Local DB : {db_path}")
        print(f"  Database Exists : {os.path.exists(db_path)}")

    broadcast_result = (
        broadcast_service
        .broadcast_all_to_all_vehicles()
    )

    print("=" * 60)
    print("Broadcast Result")
    print("=" * 60)

    print(
        "Broadcast Status      :",
        broadcast_result.get(
            "status"
        )
    )

    print(
        "Packages Found        :",
        broadcast_result.get(
            "pending_packages_found",
            0
        )
    )

    print(
        "Successful Packages   :",
        broadcast_result.get(
            "successful_packages",
            0
        )
    )

    print(
        "Failed Packages       :",
        broadcast_result.get(
            "failed_packages",
            0
        )
    )

    print(
        "Queue Deleted         :",
        broadcast_result.get(
            "queue_records_deleted",
            0
        )
    )

    print(
        "Queue Remaining       :",
        broadcast_result.get(
            "remaining_queue_records",
            0
        )
    )

    print("=" * 60)
    print("Vehicle Database Records")
    print("=" * 60)

    for vehicle_id in VEHICLES:
        receiver = broadcast_service.get_vehicle_receiver(
            vehicle_id
        )
        if receiver:
            print(
                f"{vehicle_id} Records: {len(receiver.records)}"
            )

    print("=" * 60)