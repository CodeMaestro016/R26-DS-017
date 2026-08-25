# vehicles/vehicle_B/src/knowledge_package.py
# Knowledge Package Creation
# This step runs only after RL agent decides SHARE

import time
import numpy as np


class KnowledgePackageCreator:
    """
    Creates a knowledge package after RL decision = SHARE.

    Important:
        - Raw image is NOT shared.
        - Cropped image is NOT shared.
        - Class label is NOT shared as final knowledge.
        - Only embedding and minimum metadata are shared.

    The global verification model will verify the embedding
    using cosine similarity.
    """

    def __init__(self, vehicle_id="Vehicle_B"):
        self.vehicle_id = vehicle_id

    def create_package(self, sign_id, embedding):
        """
        Create knowledge package using extracted embedding.

        Args:
            sign_id:
                Local sign identifier.

            embedding:
                128-dimensional embedding extracted from CNN/embedding model.

        Returns:
            knowledge_package dictionary.
        """

        if embedding is None:
            raise ValueError("Embedding is missing. Cannot create knowledge package.")

        embedding = np.array(embedding).flatten()

        if embedding.size == 0:
            raise ValueError("Embedding is empty. Cannot create knowledge package.")

        knowledge_package = {
            "vehicle_id": self.vehicle_id,
            "sign_id": sign_id,
            "embedding": embedding.tolist(),
            "timestamp": time.time()
        }

        return knowledge_package

    def print_package_summary(self, knowledge_package):
        """
        Print safe package summary without printing full embedding.
        """

        print("Knowledge Package Created")
        print("Vehicle ID :", knowledge_package["vehicle_id"])
        print("Sign ID    :", knowledge_package["sign_id"])
        print("Embedding  : included")
        print("Embedding Length:", len(knowledge_package["embedding"]))
        print("Timestamp  :", knowledge_package["timestamp"])