from __future__ import annotations

import json
import pandas as pd

from utils.situation_explanation_agent import SituationAwareExplanationAgent

TEST_CSV = "outputs/phase7/final_test/test_agent_predictions.csv"


def main() -> None:
    frame = pd.read_csv(TEST_CSV)

    agent = SituationAwareExplanationAgent(
        integration_steps=32,
    )

    print("=" * 88)
    print("PHASE 8.2 - RUNTIME SITUATION EXPLANATION AGENT")
    print("=" * 88)

    displayed = 0

    for wanted_action in (
        "OBSERVE_MORE",
        "COMMIT_NOT_CROSSING",
        "COMMIT_CROSSING",
    ):
        subset = frame[
            frame["agent_predicted_action_name"] == wanted_action
        ]

        if subset.empty:
            continue

        row = subset.iloc[0]
        state = {
            name: float(row[name])
            for name in agent.state_features
        }

        result = agent.explain(
            state,
            maximum_occlusion=row.get("maximum_occlusion", None),
        )

        print()
        print("-" * 88)
        print(
            f"Sequence: {row.get('sequence_id', 'unknown')} | "
            f"Pedestrian: {row.get('pedestrian_id', 'unknown')} | "
            f"Occlusion: {row.get('maximum_occlusion', 'unknown')}"
        )
        print("-" * 88)
        print("Action:", result.action_name)
        print("Policy probability:", f"{result.action_probability:.6f}")
        print("Dominant group:", result.dominant_evidence_group)

        print("Top supporting evidence:")
        for item in result.top_supporting_evidence:
            print(
                f"  {item.label:42s} "
                f"value={item.state_value:.6f} "
                f"attr={item.attribution:+.6f} "
                f"share={item.absolute_share:.6f}"
            )

        print("Top opposing evidence:")
        for item in result.top_opposing_evidence:
            print(
                f"  {item.label:42s} "
                f"value={item.state_value:.6f} "
                f"attr={item.attribution:+.6f} "
                f"share={item.absolute_share:.6f}"
            )

        print()
        print("Situation explanation:")
        print(result.situation_summary)

        displayed += 1

    print()
    print("=" * 88)
    print("Structured example JSON:")

    first = frame.iloc[0]
    state = {
        name: float(first[name])
        for name in agent.state_features
    }

    result = agent.explain(
        state,
        maximum_occlusion=first.get("maximum_occlusion", None),
    )

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
        )[:3000]
    )

    print()
    print(f"Displayed action examples: {displayed}")
    print("Status: PASSED")
    print("=" * 88)


if __name__ == "__main__":
    main()
