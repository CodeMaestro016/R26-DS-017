from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from utils.unified_runtime_pipeline import UnifiedRuntimePipeline

TEST_FEATURES = Path("datasets/processed/features/test_reliability_enriched_features.npz")
TEST_METADATA = Path("datasets/processed/metadata/test.csv")
PHASE7_TEST = Path("outputs/phase7/final_test/test_agent_predictions.csv")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-index", type=int, default=28)
    parser.add_argument("--explanation-steps", type=int, default=32)
    return parser.parse_args()


def main():
    args = parse_args()
    for path in (TEST_FEATURES, TEST_METADATA):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    metadata = pd.read_csv(TEST_METADATA).reset_index(drop=True)
    with np.load(TEST_FEATURES, allow_pickle=True) as payload:
        X = payload["X"].astype(np.float32, copy=False)
        y = payload["y"].astype(np.int64, copy=False)

    index = int(args.sequence_index)
    if not 0 <= index < len(X):
        raise IndexError(f"sequence-index must be in [0, {len(X)-1}]")

    row = metadata.iloc[index]
    maximum_occlusion = None
    if PHASE7_TEST.exists():
        phase7 = pd.read_csv(PHASE7_TEST).reset_index(drop=True)
        if len(phase7) == len(X):
            maximum_occlusion = str(phase7.iloc[index].get("maximum_occlusion", ""))

    pipeline = UnifiedRuntimePipeline(explanation_steps=args.explanation_steps)

    print("=" * 96)
    print("PHASE 9.1 - UNIFIED RUNTIME PIPELINE SMOKE TEST")
    print("=" * 96)
    print("Sequence index :", index)
    print("Sequence ID    :", row.get("sequence_id", "unknown"))
    print("Video          :", row.get("video", "unknown"))
    print("Pedestrian     :", row.get("pedestrian_id", "unknown"))
    print("Max occlusion  :", maximum_occlusion)
    print("Ground truth   :", "CROSSING" if int(y[index]) == 1 else "NOT_CROSSING", "(diagnostic only)")

    result = pipeline.predict(X[index], maximum_occlusion=maximum_occlusion)

    print("\n" + "-" * 96)
    print("INTENT + UNCERTAINTY")
    print("-" * 96)
    print("Feature shape       :", result.feature_shape)
    print("Frozen intent       :", result.intent_prediction)
    print("P(crossing)         :", f"{result.p_crossing:.6f}")
    print("Confidence          :", f"{result.confidence:.6f}")
    print("Normalized entropy  :", f"{result.normalized_predictive_entropy:.6f}")
    print("Mutual information  :", f"{result.mutual_information:.6f}")
    print("Crossing variance   :", f"{result.crossing_probability_variance:.8f}")

    print("\n" + "-" * 96)
    print("OBSERVATION STATE")
    print("-" * 96)
    print("Reliability mean    :", result.observation_reliability_mean)
    print("Reliability last    :", result.observation_reliability_last)
    print("Mean speed          :", f"{result.mean_speed:.6f}")
    print("Last speed          :", f"{result.last_speed:.6f}")

    print("\n" + "-" * 96)
    print("LEARNED DECISION AGENT")
    print("-" * 96)
    print("Agent action        :", result.agent_action_name)
    print("Action probability  :", f"{result.agent_action_probability:.6f}")
    print("Action probabilities:", result.agent_action_probabilities)
    print("Committed intent    :", result.committed_intent)

    print("\n" + "-" * 96)
    print("SITUATION-AWARE EXPLANATION AGENT")
    print("-" * 96)
    print("Dominant group      :", result.dominant_explanation_group)
    print("Explanation         :", result.explanation)

    print("\n" + "-" * 96)
    print("DOWNSTREAM AV INTERFACE")
    print("-" * 96)
    print("Signal              :", result.av_interface_signal)
    print("NOTE                : intent interface only; no brake/steering command is produced.")

    output_dir = Path("outputs/phase9")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"unified_runtime_sequence_{index}.json"
    output_path.write_text(json.dumps(result.to_dict(), indent=2, default=str), encoding="utf-8")

    print("\nOUTPUT:", output_path)
    print("Status: PASSED")
    print("=" * 96)


if __name__ == "__main__":
    main()
