from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from utils.agent_explainer import (
    FEATURE_DISPLAY_NAMES,
    FEATURE_GROUPS,
    IntegratedGradientsAgentExplainer,
)

CHECKPOINT = Path("outputs/phase7/learned_agent_policy_best.pt")
TEST_PREDICTIONS = Path(
    "outputs/phase7/final_test/test_agent_predictions.csv"
)
OUT = Path("outputs/phase8")
INTEGRATION_STEPS = 64


def main() -> None:
    print("=" * 92)
    print("PHASE 8.1 - SITUATION-AWARE EXPLANATION EVIDENCE")
    print("=" * 92)

    for path in (CHECKPOINT, TEST_PREDICTIONS):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    frame = pd.read_csv(TEST_PREDICTIONS).reset_index(drop=True)

    explainer = IntegratedGradientsAgentExplainer(
        checkpoint_path=CHECKPOINT,
        device="cpu",
        integration_steps=INTEGRATION_STEPS,
    )

    missing = [
        name for name in explainer.state_features
        if name not in frame.columns
    ]
    if missing:
        raise KeyError(
            f"Final-test file is missing state features: {missing}"
        )

    rows = []
    group_totals = {group: [] for group in FEATURE_GROUPS}
    feature_totals = {
        feature: [] for feature in explainer.state_features
    }

    for _, row in frame.iterrows():
        state = {
            name: float(row[name])
            for name in explainer.state_features
        }

        result = explainer.explain(
            state,
            maximum_occlusion=row.get(
                "maximum_occlusion",
                None,
            ),
        )

        output = {
            "source_index": int(
                row.get("source_index", row.name)
            ),
            "sequence_id": row.get("sequence_id", row.name),
            "video": row.get("video", "unknown"),
            "pedestrian_id": row.get("pedestrian_id", "unknown"),
            "maximum_occlusion": row.get(
                "maximum_occlusion",
                "unknown",
            ),
            "true_intent": int(row.get("true_intent", -1)),
            "frozen_intent_prediction": int(
                row.get("frozen_intent_prediction", -1)
            ),
            "agent_action": result.action_id,
            "agent_action_name": result.action_name,
            "agent_action_probability": result.action_probability,
            "explanation_text": result.explanation_text,
        }

        for action_name, probability in (
            result.action_probabilities.items()
        ):
            output[
                f"policy_probability_{action_name.lower()}"
            ] = probability

        for feature, attribution in (
            result.feature_attributions.items()
        ):
            output[f"ig_{feature}"] = attribution

            share = (
                result.normalized_absolute_contributions[
                    feature
                ]
            )
            output[
                f"ig_abs_share_{feature}"
            ] = share
            feature_totals[feature].append(share)

        for group_name, contribution in (
            result.group_absolute_contributions.items()
        ):
            output[
                f"group_abs_share_{group_name}"
            ] = contribution
            group_totals[group_name].append(contribution)

        for rank in range(3):
            if rank < len(result.top_supporting_features):
                feature, value = (
                    result.top_supporting_features[rank]
                )
                output[
                    f"support_{rank + 1}_feature"
                ] = feature
                output[
                    f"support_{rank + 1}_label"
                ] = FEATURE_DISPLAY_NAMES[feature]
                output[
                    f"support_{rank + 1}_attribution"
                ] = value
            else:
                output[
                    f"support_{rank + 1}_feature"
                ] = ""
                output[
                    f"support_{rank + 1}_label"
                ] = ""
                output[
                    f"support_{rank + 1}_attribution"
                ] = np.nan

        if result.top_opposing_features:
            feature, value = result.top_opposing_features[0]
            output["strongest_opposing_feature"] = feature
            output[
                "strongest_opposing_label"
            ] = FEATURE_DISPLAY_NAMES[feature]
            output[
                "strongest_opposing_attribution"
            ] = value
        else:
            output["strongest_opposing_feature"] = ""
            output["strongest_opposing_label"] = ""
            output["strongest_opposing_attribution"] = np.nan

        rows.append(output)

    explanations = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)

    explanation_path = OUT / "test_situation_explanations.csv"
    summary_path = OUT / "explanation_summary.json"

    explanations.to_csv(explanation_path, index=False)

    mean_groups = {
        group: float(np.mean(values))
        for group, values in group_totals.items()
    }

    mean_features = {
        feature: float(np.mean(values))
        for feature, values in feature_totals.items()
    }

    sorted_features = sorted(
        mean_features.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    summary = {
        "phase": "8.1",
        "method": "Integrated Gradients on learned Phase-7 policy logits",
        "baseline": (
            "zero in normalized policy-input space "
            "(Phase-7 training-feature mean)"
        ),
        "integration_steps": INTEGRATION_STEPS,
        "n_explanations": int(len(explanations)),
        "mean_absolute_group_attribution_share": mean_groups,
        "top_mean_absolute_features": [
            {
                "feature": feature,
                "display_name": FEATURE_DISPLAY_NAMES[feature],
                "mean_absolute_share": value,
            }
            for feature, value in sorted_features[:10]
        ],
        "interpretation": (
            "Local post-hoc attributions for the learned agent; "
            "not causal effects."
        ),
    }

    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(
        "Explained held-out test samples:",
        len(explanations),
    )
    print(
        "Integrated-Gradients steps      :",
        INTEGRATION_STEPS,
    )

    print()
    print("-" * 92)
    print("MEAN ABSOLUTE ATTRIBUTION SHARE BY EVIDENCE GROUP")
    print("-" * 92)

    for group, value in sorted(
        mean_groups.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"{group:15s}: {value:.6f}")

    print()
    print("-" * 92)
    print("TOP GLOBAL POLICY FEATURES")
    print("-" * 92)

    for feature, value in sorted_features[:10]:
        print(
            f"{FEATURE_DISPLAY_NAMES[feature]:42s}: "
            f"{value:.6f}"
        )

    print()
    print("-" * 92)
    print("EXAMPLE SITUATION EXPLANATIONS")
    print("-" * 92)

    for action_name in (
        "OBSERVE_MORE",
        "COMMIT_NOT_CROSSING",
        "COMMIT_CROSSING",
    ):
        subset = explanations[
            explanations["agent_action_name"] == action_name
        ]
        if subset.empty:
            continue

        example = subset.iloc[0]

        print()
        print(
            f"[{action_name}] "
            f"sequence={example['sequence_id']} "
            f"pedestrian={example['pedestrian_id']} "
            f"occlusion={example['maximum_occlusion']}"
        )
        print(example["explanation_text"])

    print()
    print("-" * 92)
    print("OUTPUTS")
    print("-" * 92)
    print(explanation_path)
    print(summary_path)
    print()
    print(
        "NOTE: The renderer verbalizes only actual model attributions "
        "and observed metadata. It does not invent unsupported gaze, "
        "road-context, or causal claims."
    )
    print("Status: PASSED")
    print("=" * 92)


if __name__ == "__main__":
    main()
