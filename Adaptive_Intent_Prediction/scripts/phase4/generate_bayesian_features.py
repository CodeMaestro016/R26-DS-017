"""
Generate leakage-safe Bayesian semantic features.

Training:
    Uses grouped out-of-fold Bayesian inference.

Validation and Test:
    Uses a Bayesian Network fitted only on the
    complete training split.

Outputs:
    train_bayesian_features.npz
    val_bayesian_features.npz
    test_bayesian_features.npz

    train_enriched_features.npz
    val_enriched_features.npz
    test_enriched_features.npz
"""

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import (
    StratifiedGroupKFold
)

from utils.bayesian_network import (
    BayesianSemanticNetwork
)


FEATURE_DIR = Path(
    "datasets/processed/features"
)

METADATA_DIR = Path(
    "datasets/processed/metadata"
)

BAYESIAN_DATA_DIR = Path(
    "datasets/processed/bayesian"
)

FINAL_MODEL_PATH = Path(
    "outputs/phase4/"
    "bayesian_semantic_network.pkl"
)

N_SPLITS = 5
RANDOM_STATE = 42

EVIDENCE_COLUMNS = [
    "motion",
    "horizontal",
    "vertical",
    "occlusion"
]


def load_original_features(split_name):

    path = (
        FEATURE_DIR
        / f"{split_name}_features.npz"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {path}"
        )

    with np.load(
        path,
        allow_pickle=True
    ) as data:

        X = data["X"].astype(
            np.float32,
            copy=False
        )

        y = data["y"].astype(
            np.int64,
            copy=False
        )

    return X, y


def load_bayesian_data(split_name):

    path = (
        BAYESIAN_DATA_DIR
        / f"{split_name}_bayesian.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Bayesian CSV not found: {path}"
        )

    data = pd.read_csv(path)

    text_columns = [
        "motion",
        "horizontal",
        "vertical",
        "occlusion",
        "intention_tendency",
        "observation_reliability"
    ]

    for column in text_columns:

        data[column] = (
            data[column]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    return data


def build_inference_cache(
    network,
    evidence_data
):
    """
    Only 81 maximum evidence combinations exist:

        3 motion
        × 3 horizontal
        × 3 vertical
        × 3 occlusion

    Therefore inference is performed once per unique
    combination instead of once per frame.
    """

    unique_evidence = (
        evidence_data[EVIDENCE_COLUMNS]
        .drop_duplicates()
    )

    cache = {}

    for evidence in unique_evidence.itertuples(
        index=False,
        name=None
    ):

        motion = evidence[0]
        horizontal = evidence[1]
        vertical = evidence[2]
        occlusion = evidence[3]

        result = network.predict(
            motion=motion,
            horizontal=horizontal,
            vertical=vertical,
            occlusion=occlusion
        )

        cache[evidence] = (
            result["feature_vector"]
            .astype(np.float32)
        )

    return cache


def infer_rows(
    network,
    rows,
    output_array,
    filled_mask
):

    cache = build_inference_cache(
        network,
        rows
    )

    required_columns = [
        "sequence_index",
        "time_step",
        *EVIDENCE_COLUMNS
    ]

    for row in rows[
        required_columns
    ].itertuples(
        index=False,
        name=None
    ):

        sequence_index = int(row[0])
        time_step = int(row[1])

        evidence = (
            row[2],
            row[3],
            row[4],
            row[5]
        )

        output_array[
            sequence_index,
            time_step
        ] = cache[evidence]

        filled_mask[
            sequence_index,
            time_step
        ] = True


def generate_oof_train_features():

    print()
    print("=" * 70)
    print("GENERATE OOF TRAIN BAYESIAN FEATURES")
    print("=" * 70)

    X_train, y_train = (
        load_original_features("train")
    )

    train_bayesian = (
        load_bayesian_data("train")
    )

    train_metadata = pd.read_csv(
        METADATA_DIR / "train.csv",
        dtype={
            "video": str,
            "pedestrian_id": str
        }
    ).reset_index(drop=True)

    if len(train_metadata) != len(X_train):

        raise ValueError(
            "Train metadata and feature count "
            "do not match."
        )

    groups = (
        train_metadata["video"].astype(str)
        + "::"
        + train_metadata[
            "pedestrian_id"
        ].astype(str)
    ).to_numpy()

    unique_groups = np.unique(groups)

    if len(unique_groups) < N_SPLITS:

        raise ValueError(
            f"Only {len(unique_groups)} unique "
            f"pedestrian groups are available, "
            f"but {N_SPLITS} folds were requested."
        )

    output = np.zeros(
        (
            X_train.shape[0],
            X_train.shape[1],
            5
        ),
        dtype=np.float32
    )

    filled = np.zeros(
        (
            X_train.shape[0],
            X_train.shape[1]
        ),
        dtype=bool
    )

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    sequence_indices = np.arange(
        len(X_train)
    )

    for fold_number, (
        training_indices,
        held_out_indices
    ) in enumerate(
        splitter.split(
            sequence_indices,
            y_train,
            groups
        ),
        start=1
    ):

        print()
        print(
            f"Fold {fold_number}/{N_SPLITS}"
        )

        print(
            "Training sequences:",
            len(training_indices)
        )

        print(
            "Held-out sequences:",
            len(held_out_indices)
        )

        training_rows = train_bayesian[
            train_bayesian[
                "sequence_index"
            ].isin(training_indices)
        ].copy()

        held_out_rows = train_bayesian[
            train_bayesian[
                "sequence_index"
            ].isin(held_out_indices)
        ].copy()

        network = BayesianSemanticNetwork()

        network.fit(
            data=training_rows,
            equivalent_sample_size=1.0
        )

        infer_rows(
            network=network,
            rows=held_out_rows,
            output_array=output,
            filled_mask=filled
        )

    if not filled.all():

        missing_positions = np.argwhere(
            ~filled
        )

        raise ValueError(
            "Some train Bayesian features were not "
            "generated. First missing positions: "
            f"{missing_positions[:10].tolist()}"
        )

    return output


def train_final_network():

    print()
    print("=" * 70)
    print("TRAIN FINAL BAYESIAN NETWORK")
    print("=" * 70)

    train_bayesian = (
        load_bayesian_data("train")
    )

    network = BayesianSemanticNetwork()

    network.fit(
        data=train_bayesian,
        equivalent_sample_size=1.0
    )

    network.save(
        FINAL_MODEL_PATH
    )

    print(
        "Final model saved to:",
        FINAL_MODEL_PATH
    )

    return network


def generate_split_features(
    split_name,
    network
):

    print()
    print("=" * 70)
    print(
        f"GENERATE {split_name.upper()} "
        "BAYESIAN FEATURES"
    )
    print("=" * 70)

    X, _ = load_original_features(
        split_name
    )

    bayesian_data = load_bayesian_data(
        split_name
    )

    output = np.zeros(
        (
            X.shape[0],
            X.shape[1],
            5
        ),
        dtype=np.float32
    )

    filled = np.zeros(
        (
            X.shape[0],
            X.shape[1]
        ),
        dtype=bool
    )

    infer_rows(
        network=network,
        rows=bayesian_data,
        output_array=output,
        filled_mask=filled
    )

    if not filled.all():

        missing_positions = np.argwhere(
            ~filled
        )

        raise ValueError(
            f"{split_name}: missing Bayesian "
            f"features at "
            f"{missing_positions[:10].tolist()}"
        )

    return output


def save_outputs(
    split_name,
    bayesian_features
):

    X, y = load_original_features(
        split_name
    )

    if (
        X.shape[:2]
        != bayesian_features.shape[:2]
    ):

        raise ValueError(
            f"{split_name}: original and Bayesian "
            "feature shapes are not aligned."
        )

    enriched_features = np.concatenate(
        [
            X,
            bayesian_features
        ],
        axis=2
    ).astype(
        np.float32,
        copy=False
    )

    bayesian_output_path = (
        FEATURE_DIR
        / f"{split_name}_bayesian_features.npz"
    )

    enriched_output_path = (
        FEATURE_DIR
        / f"{split_name}_enriched_features.npz"
    )

    np.savez_compressed(
        bayesian_output_path,
        X=bayesian_features,
        y=y
    )

    np.savez_compressed(
        enriched_output_path,
        X=enriched_features,
        y=y
    )

    print()
    print(f"{split_name.upper()} OUTPUTS")

    print(
        "Bayesian feature shape:",
        bayesian_features.shape
    )

    print(
        "Enriched feature shape:",
        enriched_features.shape
    )

    print(
        "Bayesian output:",
        bayesian_output_path
    )

    print(
        "Enriched output:",
        enriched_output_path
    )


def main():

    print("=" * 70)
    print("GENERATE BAYESIAN SEMANTIC FEATURES")
    print("=" * 70)

    train_bayesian_features = (
        generate_oof_train_features()
    )

    final_network = train_final_network()

    val_bayesian_features = (
        generate_split_features(
            split_name="val",
            network=final_network
        )
    )

    test_bayesian_features = (
        generate_split_features(
            split_name="test",
            network=final_network
        )
    )

    save_outputs(
        split_name="train",
        bayesian_features=
            train_bayesian_features
    )

    save_outputs(
        split_name="val",
        bayesian_features=
            val_bayesian_features
    )

    save_outputs(
        split_name="test",
        bayesian_features=
            test_bayesian_features
    )

    print()
    print("=" * 70)
    print("BAYESIAN FEATURE GENERATION COMPLETE")
    print("=" * 70)

    print(
        "Final Transformer input dimension: 527"
    )


if __name__ == "__main__":
    main()