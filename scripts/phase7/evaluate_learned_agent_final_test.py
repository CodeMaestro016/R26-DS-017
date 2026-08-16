from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from scripts.phase7._calibrated_state_utils import (
    calibrate_probability,
    confidence_from_probability,
    decision_margin_uncertainty,
    load_deployment_temperature_and_threshold,
    normalized_binary_entropy,
)
from utils.learned_agent_policy import ACTION_NAMES, LearnedAgentPolicy


TEST_META = Path("datasets/processed/metadata/test.csv")
TEST_FEATURES = Path(
    "datasets/processed/features/test_reliability_enriched_features.npz"
)
TEST_PREDICTIONS = Path(
    "outputs/phase6/final_test/test_uncertainty_predictions.csv"
)
CHECKPOINT = Path(
    "outputs/phase7/learned_agent_policy_best.pt"
)
OUT = Path("outputs/phase7/final_test")


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


def selective_metrics(frame, actions):
    y = frame["true_intent"].to_numpy(dtype=np.int64)
    frozen = frame[
        "frozen_intent_prediction"
    ].to_numpy(dtype=np.int64)

    frozen_correct = (
        frame["frozen_prediction_correct"]
        .to_numpy(dtype=np.int64)
        == 1
    )

    commits = actions != 0

    committed_intent = np.full(
        len(frame),
        -1,
        dtype=np.int64,
    )

    committed_intent[actions == 1] = 0
    committed_intent[actions == 2] = 1

    correct_commit = commits & (committed_intent == y)
    wrong_commit = commits & (committed_intent != y)

    errors = ~frozen_correct

    committed_accuracy = (
        float(correct_commit[commits].mean())
        if commits.any()
        else float("nan")
    )

    error_capture = (
        float((actions[errors] == 0).mean())
        if errors.any()
        else float("nan")
    )

    unnecessary_deferral = (
        float((actions[frozen_correct] == 0).mean())
        if frozen_correct.any()
        else float("nan")
    )

    return {
        "n_samples": int(len(frame)),
        "baseline_frozen_intent_accuracy": float(
            (frozen == y).mean()
        ),
        "agent_commit_coverage": float(commits.mean()),
        "agent_deferral_rate": float((actions == 0).mean()),
        "agent_committed_accuracy": committed_accuracy,
        "agent_unsafe_commit_rate_overall": float(
            wrong_commit.mean()
        ),
        "agent_error_capture_recall": error_capture,
        "agent_unnecessary_deferral_rate": unnecessary_deferral,
        "agent_correct_commit_rate_overall": float(
            correct_commit.mean()
        ),
    }


def main():
    print("=" * 92)
    print("PHASE 7.3 V2 - DEPLOYMENT-ALIGNED HELD-OUT AGENT TEST")
    print("=" * 92)

    for path in (
        TEST_META,
        TEST_FEATURES,
        TEST_PREDICTIONS,
        CHECKPOINT,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    (
        temperature,
        mc_threshold,
        temperature_source,
        threshold_source,
    ) = load_deployment_temperature_and_threshold()

    print("Frozen temperature :", f"{temperature:.10f}")
    print("Frozen MC threshold:", f"{mc_threshold:.10f}")

    metadata = pd.read_csv(TEST_META).reset_index(drop=True)
    pred = pd.read_csv(TEST_PREDICTIONS).reset_index(drop=True)

    with np.load(TEST_FEATURES, allow_pickle=True) as payload:
        X = payload["X"].astype(np.float32, copy=False)
        y_npz = payload["y"].astype(np.int64, copy=False)

    n = len(metadata)

    if X.shape != (n, 30, 525):
        raise ValueError(
            f"Expected test shape ({n}, 30, 525), got {X.shape}"
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
        raise ValueError("Test labels are not aligned.")

    calibrated_p, calibrated_col = numeric(
        pred,
        [
            "calibrated_mc_crossing_probability",
            "calibrated_mc_mean_crossing_probability",
        ],
        required=False,
    )

    raw_p_col = None

    if calibrated_p is None:
        raw_p, raw_p_col = numeric(
            pred,
            [
                "uncalibrated_mc_crossing_probability",
                "mc_crossing_probability",
                "mc_mean_crossing_probability",
            ],
        )

        calibrated_p = calibrate_probability(
            raw_p,
            temperature,
        )

        calibrated_col = (
            f"derived from {raw_p_col} using T={temperature:.10f}"
        )

    # Recompute probability-derived state features consistently with validation.
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

    y_hat = (
        calibrated_p >= mc_threshold
    ).astype(np.int64)

    # Validate against the existing final Phase-6 prediction column if present.
    prediction_id_col = first_col(
        pred,
        ["prediction_id", "predicted_label", "y_pred"],
    )

    if prediction_id_col is not None:
        csv_y_hat = parse_binary(
            pred[prediction_id_col].tolist()
        )

        mismatch_count = int(
            (csv_y_hat != y_hat).sum()
        )

        print(
            "Phase-6 prediction consistency mismatches:",
            mismatch_count,
        )

        if mismatch_count:
            raise ValueError(
                "Reconstructed calibrated decisions do not match "
                "Phase-6 final prediction_id. Check deployment config."
            )

    correct = y_hat == y

    reliability = X[:, :, 522:525]
    rel_mean = reliability.mean(axis=1)
    rel_last = reliability[:, -1, :]
    speed = X[:, :, 520]

    oracle_action = np.zeros(n, dtype=np.int64)
    oracle_action[correct & (y == 0)] = 1
    oracle_action[correct & (y == 1)] = 2

    ped_col = first_col(
        metadata,
        ["pedestrian_id", "id", "pedestrian"],
    )

    if ped_col is None:
        ped_col = first_col(pred, ["pedestrian_id"])

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
        pred[max_occ_col].astype(str).str.lower()
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

            "oracle_agent_action": oracle_action,
            "oracle_agent_action_name": [
                ACTION_NAMES[int(value)]
                for value in oracle_action
            ],
        }
    )

    agent = LearnedAgentPolicy(
        CHECKPOINT,
        device="cpu",
    )

    actions = []
    probability_rows = []

    for _, row in state.iterrows():
        result = agent.predict_dict(
            {
                name: float(row[name])
                for name in agent.state_features
            }
        )

        actions.append(result.action_id)
        probability_rows.append(
            result.action_probabilities
        )

    actions = np.asarray(
        actions,
        dtype=np.int64,
    )

    action_accuracy = float(
        accuracy_score(
            oracle_action,
            actions,
        )
    )

    action_macro_f1 = float(
        f1_score(
            oracle_action,
            actions,
            average="macro",
            zero_division=0,
        )
    )

    cm = confusion_matrix(
        oracle_action,
        actions,
        labels=[0, 1, 2],
    )

    overall = selective_metrics(
        state,
        actions,
    )

    state["agent_predicted_action"] = actions
    state["agent_predicted_action_name"] = [
        ACTION_NAMES[int(value)]
        for value in actions
    ]

    for action_id in (0, 1, 2):
        name = ACTION_NAMES[action_id]

        state[
            f"agent_probability_{name.lower()}"
        ] = [
            row[name]
            for row in probability_rows
        ]

    rows = []

    for group_name in ("all", "low", "medium", "high"):
        if group_name == "all":
            mask = np.ones(n, dtype=bool)
        else:
            mask = (
                state["maximum_occlusion"]
                .astype(str)
                .str.lower()
                .eq(group_name)
                .to_numpy()
            )

        if not mask.any():
            continue

        rows.append(
            {
                "occlusion_group": group_name,
                **selective_metrics(
                    state.loc[mask].reset_index(drop=True),
                    actions[mask],
                ),
            }
        )

    by_occ = pd.DataFrame(rows)

    OUT.mkdir(parents=True, exist_ok=True)

    prediction_output = OUT / "test_agent_predictions.csv"
    metrics_output = OUT / "test_agent_metrics.json"
    occ_output = OUT / "test_agent_metrics_by_occlusion.csv"

    state.to_csv(prediction_output, index=False)
    by_occ.to_csv(occ_output, index=False)

    summary = {
        "phase": "7.3-v2",
        "evaluation_split": "official held-out test",
        "policy_tuned_on_test": False,
        "temperature": temperature,
        "mc_threshold": mc_threshold,
        "temperature_source": temperature_source,
        "threshold_source": threshold_source,
        "calibrated_probability_source": calibrated_col,
        "action_accuracy_vs_oracle": action_accuracy,
        "action_macro_f1_vs_oracle": action_macro_f1,
        "action_confusion_matrix_order_0_1_2": cm.tolist(),
        "selective_metrics": overall,
    }

    metrics_output.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 92)
    print("TEST STATE ALIGNMENT")
    print("-" * 92)
    print("P(crossing) source :", calibrated_col)
    print("MI source          :", mi_col)
    print("Variance source    :", variance_col)
    print("Variation source   :", variation_col)
    print("Frozen test accuracy:", f"{correct.mean():.6f}")

    print()
    print("-" * 92)
    print("AGENT ACTION QUALITY")
    print("-" * 92)
    print("Action accuracy :", f"{action_accuracy:.6f}")
    print("Action macro-F1 :", f"{action_macro_f1:.6f}")
    print("Confusion matrix order [OBSERVE, COMMIT_NC, COMMIT_CROSSING]:")
    print(cm)

    print()
    print("-" * 92)
    print("SELECTIVE POLICY METRICS - HELD-OUT TEST")
    print("-" * 92)

    for key, value in overall.items():
        if isinstance(value, float):
            print(f"{key:40s}: {value:.6f}")
        else:
            print(f"{key:40s}: {value}")

    print()
    print("-" * 92)
    print("BY OCCLUSION")
    print("-" * 92)
    print(by_occ.to_string(index=False))

    print()
    print("Outputs:")
    print(prediction_output)
    print(metrics_output)
    print(occ_output)
    print()
    print("Status: PASSED")
    print("=" * 92)


if __name__ == "__main__":
    main()
