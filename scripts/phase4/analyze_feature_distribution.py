"""
Phase 4

Analyze Feature Distribution

This script:
1. Loads extracted features
2. Computes descriptive statistics
3. Learns motion clusters using K-Means
4. Saves statistics and trained clustering model
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans


# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

FEATURE_FILE = "datasets/processed/features/train_features.npz"

OUTPUT_DIR = "outputs/phase4"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------
# Helper
# ---------------------------------------------------

def summarize(name, values):

    return {

        "feature": name,

        "min": float(np.min(values)),

        "max": float(np.max(values)),

        "mean": float(np.mean(values)),

        "median": float(np.median(values)),

        "std": float(np.std(values))

    }


# ---------------------------------------------------
# Main
# ---------------------------------------------------

def main():

    print("=" * 60)
    print("Loading Feature Dataset")
    print("=" * 60)

    data = np.load(FEATURE_FILE)

    X = data["X"]

    print(f"Dataset Shape : {X.shape}")

    # ------------------------------------------------
    # Feature Split
    # ------------------------------------------------

    spatial = X[:, :, 512:518]

    motion = X[:, :, 518:522]

    # ------------------------------------------------
    # Flatten
    # ------------------------------------------------

    center_x = spatial[:, :, 0].reshape(-1)

    center_y = spatial[:, :, 1].reshape(-1)

    width = spatial[:, :, 2].reshape(-1)

    height = spatial[:, :, 3].reshape(-1)

    area = spatial[:, :, 4].reshape(-1)

    aspect_ratio = spatial[:, :, 5].reshape(-1)

    dx = motion[:, :, 0].reshape(-1)

    dy = motion[:, :, 1].reshape(-1)

    speed = motion[:, :, 2].reshape(-1)

    direction = motion[:, :, 3].reshape(-1)

    # ------------------------------------------------
    # Statistics
    # ------------------------------------------------

    statistics = [

        summarize("center_x", center_x),

        summarize("center_y", center_y),

        summarize("width", width),

        summarize("height", height),

        summarize("area", area),

        summarize("aspect_ratio", aspect_ratio),

        summarize("dx", dx),

        summarize("dy", dy),

        summarize("speed", speed),

        summarize("direction", direction)

    ]

    df = pd.DataFrame(statistics)

    csv_path = os.path.join(

        OUTPUT_DIR,

        "feature_statistics.csv"

    )

    df.to_csv(

        csv_path,

        index=False

    )

    print(f"\nStatistics saved -> {csv_path}")

    # ------------------------------------------------
    # Motion Clustering
    # ------------------------------------------------

    print("\nTraining Motion K-Means...")

    speed_data = speed.reshape(-1, 1)

    kmeans = KMeans(

        n_clusters=3,

        random_state=42,

        n_init=20

    )

    kmeans.fit(speed_data)

    centers = np.sort(

        kmeans.cluster_centers_.flatten()

    )

    print("\nMotion Cluster Centers")

    print("----------------------")

    print(f"Cluster 1 : {centers[0]:.6f}")

    print(f"Cluster 2 : {centers[1]:.6f}")

    print(f"Cluster 3 : {centers[2]:.6f}")

    model_path = os.path.join(

        OUTPUT_DIR,

        "motion_kmeans.pkl"

    )

    joblib.dump(

        kmeans,

        model_path

    )
    

    print(f"\nMotion model saved -> {model_path}")
    

    print("\nAnalysis Completed Successfully.")


if __name__ == "__main__":

    main()