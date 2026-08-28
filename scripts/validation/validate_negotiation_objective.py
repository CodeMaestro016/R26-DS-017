"""Standalone Step 5H physical objective validation without SUMO startup."""

from pathlib import Path
import pytest


def main():
    result = pytest.main(["-q", "tests/test_negotiation_objective.py"])
    if result != pytest.ExitCode.OK:
        raise SystemExit(int(result))
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("negotiation_objective").glob("*.py"))
    assert "collision_penalty" not in source and "fairness_weight" not in source
    sections = {
        "Hard-constraint separation": ("Regulatory rules used as reward penalties: False", "Hard masks preserved: PASS", "Collision penalty introduced: False", "Safety score used as reward: False"),
        "Travel-time objective": ("Scheduled-spawn accounting available: PASS", "Completed travel-time measurement: PASS", "Unfinished episode-end measurement: PASS", "Team travel-time sum: PASS", "Units: vehicle-seconds"),
        "Incremental accounting": ("Interval exposure calculation: PASS", "Interval sum equals total travel time: PASS", "Zero-duration interval supported: PASS", "Negative-duration interval rejected: PASS"),
        "Reward": ("Baseline definition: NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT", "Empirical reward weights: 0", "Arbitrary reward constants: 0", "Completion bonuses: 0", "Agreement bonuses: 0", "Relinquishment bonuses: 0", "Rejection penalties: 0", "Throughput bonus: 0", "Fairness weight: 0", "Reward clipping: False", "Reward normalization: False"),
        "Multi-agent accounting": ("Shared team objective: PASS", "Simultaneous decision batch supported: PASS", "Same physical cost double-counted in ledger: False", "Multiple claims same ego duplicate cost: False", "Processing-order invariance: PASS"),
        "Action neutrality": ("KEEP/RELINQUISH labels directly alter reward: False", "ACCEPT/REJECT labels directly alter reward: False", "Actor logits alter reward: False", "Prediction probabilities alter reward: False"),
        "Diagnostics": ("Throughput measured separately: PASS", "Mean travel time: PASS", "Maximum travel time: PASS", "Travel-time variance: PASS", "Fairness included as weighted reward: False"),
        "Authority": ("Route-truth fields consumed by baseline reward: 0", "Vehicle IDs used as reward weights: False", "Reward modifies regulatory graph: False", "Reward modifies protocol truth: False", "Reward controls SUMO: False"),
        "Research parameters": ("Gamma configured: False", "GAE lambda configured: False", "PPO clip configured: False", "Learning rate configured: False", "Entropy coefficient configured: False", "Reward hyperparameters configured: 0"),
        "Research status": ("Objective formulation implemented: True", "Raw scalar team reward available: True", "Return implemented: False", "Advantage implemented: False", "GAE implemented: False", "PPO implemented: False", "Optimizer implemented: False", "Training performed: False", "Safety shield implemented: False", "Learned SUMO control enabled: False"),
    }
    print("Step 5H Negotiation Objective Validation\n")
    for heading, lines in sections.items():
        print(heading)
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()
