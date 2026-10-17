from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from scripts.phase7._calibrated_state_utils import (
    calibrate_probability,
    confidence_from_probability,
    decision_margin_uncertainty,
    load_deployment_temperature_and_threshold,
    normalized_binary_entropy,
)


VAL_META = Path("datasets/processed/metadata/val.csv")
VAL_FEATURES = Path(
    "datasets/processed/features/val_reliability_enriched_features.npz"
)
VAL_PREDICTIONS = Path(
    "outputs/phase6/validation_uncertainty_predictions.csv"
)
OUT = Path("outputs/phase7")

ACTIONS = {
    0: "OBSERVE_MORE",
    1: "COMMIT_NOT_CROSSING",
    2: "COMMIT_CROSSING",
}


def first_col(df, names):
    lookup = {str(c).lower(): str(c) for c in df.columns}

    for name in names:
        found = lookup.get(name.lower())
        if found is not None:
            return found

    return None


def parse_binary(values):
    result = []

    for value in values:
        text = str(value).strip().lower().replace("_", "-")

        if text in {"0", "0.0", "not-crossing", "not crossing", "nc"}:
            result.append(0)
        elif text in {"1", "1.0", "crossing", "c"}:
            result.append(1)
        else:
            raise ValueError(f"Unsupported binary label value: {value!r}")

    return np.asarray(result, dtype=np.int64)


def numeric(df, names, required=True):
    col = first_col(df, names)

    if col is None:
        if required:
            raise KeyError(
                f"Missing one of {names}. "
                f"Available columns: {list(df.columns)}"
            )
        return None, None

    values = pd.to_numeric(
        df[col],
        errors="coerce",
    ).to_numpy(dtype=np.float32)

    if not np.isfinite(values).all():
        raise ValueError(
            f"Column '{col}' contains non-finite values."
        )

    return values, col


def main():
    print("=" * 88)
    print("PHASE 7.1 V3 - CALIBRATED DEPLOYMENT-ALIGNED AGENT STATE DATA")
    print("=" * 88)

    for path in (VAL_META, VAL_FEATURES, VAL_PREDICTIONS):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    (
        temperature,
        mc_threshold,
        temperature_source,
        threshold_source,
    ) = load_deployment_temperature_and_threshold()

    print("Frozen temperature :", f"{temperature:.10f}")
    print("Frozen MC threshold:", f"{mc_threshold:.10f}")
    print("Temperature source :", temperature_source)
    print("Threshold source   :", threshold_source)

    metadata = pd.read_csv(VAL_META).reset_index(drop=True)
    pred = pd.read_csv(VAL_PREDICTIONS).reset_index(drop=True)

    with np.load(VAL_FEATURES, allow_pickle=True) as payload:
        X = payload["X"].astype(np.float32, copy=False)
        y_npz = payload["y"].astype(np.int64, copy=False)

    n = len(metadata)

    if X.shape != (n, 30, 525):
        raise ValueError(
            f"Expected validation shape ({n}, 30, 525), got {X.shape}"
        )

    if len(pred) != n:
        raise ValueError(
            f"Prediction rows {len(pred)} != metadata rows {n}"
        )

    label_col = first_col(
        metadata,
        ["label", "label_id", "y", "target"],
    )

    y = (
        parse_binary(metadata[label_col].tolist())
        if label_col is not None
        else y_npz.copy()
    )

    if not np.array_equal(y, y_npz):
        raise ValueError("Validation labels are not aligned.")

    # Phase-6 validation CSV was produced before temperature calibration.
    # Therefore use its raw MC mean, then apply the frozen deployment temperature.
    raw_p, raw_p_col = numeric(
        pred,
        [
            "mc_crossing_probability",
            "uncalibrated_mc_crossing_probability",
            "mc_mean_crossing_probability",
        ],
    )

    calibrated_p = calibrate_probability(
        raw_p,
        temperature,
    )

    # Recompute all probability-derived policy features from the same
    # calibrated probability used at deployment.
    confidence = confidence_from_probability(calibrated_p)
    entropy = normalized_binary_entropy(calibrated_p)
    margin = decision_margin_uncertainty(calibrated_p)

    mi, mi_col = numeric(
        pred,
        ["mutual_information", "mutual_info", "mi"],
    )

    variance, variance_col = numeric(
        pred,
        [
            "crossing_probability_variance",
            "crossing_variance",
            "probability_variance",
            "predictive_variance",
        ],
    )

    variation_ratio, variation_col = numeric(
        pred,
        ["variation_ratio"],
        required=False,
    )

    if variation_ratio is None:
        variation_ratio = np.zeros(n, dtype=np.float32)
        variation_col = "filled_zero"

    # IMPORTANT:
    # The frozen intent prediction is reconstructed using the final calibrated
    # deployment threshold, not the old pre-calibration prediction_id column.
    y_hat = (
        calibrated_p >= mc_threshold
    ).astype(np.int64)

    correct = y_hat == y

    reliability = X[:, :, 522:525]
    rel_mean = reliability.mean(axis=1)
    rel_last = reliability[:, -1, :]
    speed = X[:, :, 520]

    action = np.zeros(n, dtype=np.int64)
    action[correct & (y == 0)] = 1
    action[correct & (y == 1)] = 2

    ped_col = first_col(
        metadata,
        ["pedestrian_id", "id", "pedestrian"],
    )

    if ped_col is None:
        ped_col = first_col(
            pred,
            ["pedestrian_id"],
        )

    if ped_col is None:
        raise KeyError("Could not locate pedestrian_id.")

    pedestrian_ids = (
        metadata[ped_col].astype(str)
        if ped_col in metadata.columns
        else pred[ped_col].astype(str)
    )

    video_col = first_col(metadata, ["video", "video_id"])
    seq_col = first_col(metadata, ["sequence_id", "seq_id"])

    videos = (
        metadata[video_col].astype(str)
        if video_col is not None
        else pred["video"].astype(str)
    )

    sequence_ids = (
        metadata[seq_col]
        if seq_col is not None
        else pred["sequence_id"]
    )

    max_occ_col = first_col(pred, ["maximum_occlusion"])

    max_occ = (
        pred[max_occ_col].astype(str)
        if max_occ_col is not None
        else pd.Series(["unknown"] * n)
    )

    state = pd.DataFrame(
        {
            "source_index": np.arange(n, dtype=np.int64),
            "sequence_id": sequence_ids,
            "video": videos,
            "pedestrian_id": pedestrian_ids,
            "maximum_occlusion": max_occ,

            "true_intent": y,
            "frozen_intent_prediction": y_hat,
            "frozen_prediction_correct": correct.astype(np.int64),

            "p_crossing": calibrated_p,
            "confidence": confidence,
            "normalized_predictive_entropy": entropy,
            "mutual_information": mi,
            "crossing_probability_variance": variance,
            "variation_ratio": variation_ratio,
            "decision_margin_uncertainty": margin,

            "reliability_low_mean": rel_mean[:, 0],
            "reliability_medium_mean": rel_mean[:, 1],
            "reliability_high_mean": rel_mean[:, 2],
            "reliability_low_last": rel_last[:, 0],
            "reliability_medium_last": rel_last[:, 1],
            "reliability_high_last": rel_last[:, 2],

            "mean_speed": speed.mean(axis=1),
            "last_speed": speed[:, -1],

            "agent_action": action,
            "agent_action_name": [
                ACTIONS[int(value)]
                for value in action
            ],
        }
    )

    splitter = GroupShuffleSplit(
        n_splits=1,
        train_size=0.75,
        random_state=42,
    )

    train_idx, dev_idx = next(
        splitter.split(
            state,
            y=state["agent_action"],
            groups=state["pedestrian_id"],
        )
    )

    train = state.iloc[train_idx].reset_index(drop=True)
    dev = state.iloc[dev_idx].reset_index(drop=True)

    overlap = (
        set(train["pedestrian_id"])
        & set(dev["pedestrian_id"])
    )

    if overlap:
        raise RuntimeError("Pedestrian leakage detected.")

    OUT.mkdir(parents=True, exist_ok=True)

    state.to_csv(
        OUT / "agent_state_validation_full.csv",
        index=False,
    )

    train.to_csv(
        OUT / "agent_policy_train.csv",
        index=False,
    )

    dev.to_csv(
        OUT / "agent_policy_dev.csv",
        index=False,
    )

    state_features = [
        "p_crossing",
        "confidence",
        "normalized_predictive_entropy",
        "mutual_information",
        "crossing_probability_variance",
        "variation_ratio",
        "decision_margin_uncertainty",
        "reliability_low_mean",
        "reliability_medium_mean",
        "reliability_high_mean",
        "reliability_low_last",
        "reliability_medium_last",
        "reliability_high_last",
        "mean_speed",
        "last_speed",
    ]

    manifest = {
        "phase": "7.1-v3",
        "policy_type": "learned_supervised_selective_agent",
        "probability_space": "temperature_calibrated_mc_mean",
        "temperature": temperature,
        "mc_threshold": mc_threshold,
        "temperature_source": temperature_source,
        "threshold_source": threshold_source,
        "raw_validation_probability_column": raw_p_col,
        "state_features": state_features,
        "actions": {
            str(key): value
            for key, value in ACTIONS.items()
        },
        "phase6_columns_used": {
            "mutual_information": mi_col,
            "variance": variance_col,
            "variation_ratio": variation_col,
        },
        "official_test_used": False,
        "rows": int(n),
        "policy_train_rows": int(len(train)),
        "policy_dev_rows": int(len(dev)),
        "policy_train_pedestrians": int(
            train["pedestrian_id"].nunique()
        ),
        "policy_dev_pedestrians": int(
            dev["pedestrian_id"].nunique()
        ),
    }

    (
        OUT / "agent_state_manifest.json"
    ).write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 88)
    print("DEPLOYMENT-ALIGNED FROZEN INTENT MODEL ON VALIDATION")
    print("-" * 88)
    print("Correct   :", int(correct.sum()))
    print("Incorrect :", int((~correct).sum()))
    print("Accuracy  :", f"{float(correct.mean()):.6f}")

    print()
    print("Action targets:")

    counts = state["agent_action_name"].value_counts()

    for action_id in (0, 1, 2):
        name = ACTIONS[action_id]
        count = int(counts.get(name, 0))
        print(
            f"  {name:24s}: "
            f"{count:4d} ({count / n:.4f})"
        )

    print()
    print(
        "Policy train:",
        len(train),
        "rows |",
        train["pedestrian_id"].nunique(),
        "pedestrians",
    )
    print(
        "Policy dev  :",
        len(dev),
        "rows |",
        dev["pedestrian_id"].nunique(),
        "pedestrians",
    )
    print("Pedestrian overlap:", len(overlap))

    print()
    print(
        "IMPORTANT: Old Phase-7.2 checkpoint must be retrained "
        "because the policy probability state is now calibrated."
    )
    print("Status: PASSED")
    print("=" * 88)


if __name__ == "__main__":
    main()
