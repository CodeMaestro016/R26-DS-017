from __future__ import annotations

import pandas as pd

from utils.learned_agent_policy import LearnedAgentPolicy


CHECKPOINT = "outputs/phase7/learned_agent_policy_best.pt"
DEV_CSV = "outputs/phase7/agent_policy_dev.csv"


def main() -> None:
    agent = LearnedAgentPolicy(CHECKPOINT)

    frame = pd.read_csv(DEV_CSV)

    print("=" * 78)
    print("PHASE 7.2 - LEARNED AGENT POLICY SMOKE TEST")
    print("=" * 78)
    print("State feature count:", len(agent.state_features))
    print()

    for index in range(min(5, len(frame))):
        row = frame.iloc[index]

        state = {
            name: float(row[name])
            for name in agent.state_features
        }

        result = agent.predict_dict(state)

        print(
            f"row={index:03d} "
            f"target={row['agent_action_name']} "
            f"pred={result.action_name} "
            f"probs={result.action_probabilities}"
        )

    print()
    print("Status: PASSED")


if __name__ == "__main__":
    main()
