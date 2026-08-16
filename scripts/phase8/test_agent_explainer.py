from __future__ import annotations

import pandas as pd

from utils.agent_explainer import (
    IntegratedGradientsAgentExplainer,
)

CHECKPOINT = "outputs/phase7/learned_agent_policy_best.pt"
TEST_CSV = "outputs/phase7/final_test/test_agent_predictions.csv"


def main() -> None:
    frame = pd.read_csv(TEST_CSV)

    explainer = IntegratedGradientsAgentExplainer(
        CHECKPOINT,
        integration_steps=32,
    )

    row = frame.iloc[0]
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

    print("=" * 80)
    print("PHASE 8.1 - EXPLAINER SMOKE TEST")
    print("=" * 80)
    print("Action:", result.action_name)
    print(
        "Action probability:",
        f"{result.action_probability:.6f}",
    )

    print("Top supporting:")
    for feature, value in result.top_supporting_features:
        print(f"  {feature:35s} {value:+.6f}")

    print("Top opposing:")
    for feature, value in result.top_opposing_features:
        print(f"  {feature:35s} {value:+.6f}")

    print()
    print(result.explanation_text)
    print()
    print("Status: PASSED")


if __name__ == "__main__":
    main()
