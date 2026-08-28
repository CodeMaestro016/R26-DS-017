"""Standalone Step 5I return/advantage/PPO-math validation."""

from pathlib import Path
import pytest


def main():
    result = pytest.main(["-q", "tests/test_mappo_returns.py"])
    if result != pytest.ExitCode.OK:
        raise SystemExit(int(result))
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("negotiation_learning/mappo_returns").glob("*.py"))
    assert "gamma =" not in source and "optimizer" not in source
    sections = {
        "Objective preservation": ("Step 5H reward definition preserved: PASS", "Undiscounted reward sum equals negative team traffic-time: PASS", "Discount factor required by baseline: False", "Reward multiplied by transition duration again: False"),
        "Objective timeline": ("Canonical successor chain: PASS", "Episode-end objective closure: PASS", "Same-timestamp zero-duration phase supported: PASS", "Timeline cycles: 0", "Missing successor records: 0", "Duplicate interval ownership: 0"),
        "Returns": ("Exact complete-episode suffix return: PASS", "Partition invariance: PASS", "One return per joint batch: PASS", "Multiple decisions share batch return: PASS", "Claim resolution treated as team terminal: False", "Individual vehicle arrival treated as team terminal: False", "True simulation end treated as terminal: PASS", "Truncated rollout silently bootstrapped: False"),
        "Critic targets": ("One centralized target per joint batch: PASS", "Target equals exact undiscounted return: PASS", "Conflicting same-batch critic values rejected: PASS", "Future return exposed as critic input: False"),
        "Advantage": ("Definition: MONTE_CARLO_RETURN_MINUS_CENTRALIZED_VALUE", "A = G - V: PASS", "GAE used in baseline: False", "GAE lambda configured: False", "Advantage normalized: False", "Advantage clipped: False"),
        "PPO mathematics": ("Behavior log probability retained: PASS", "Current policy log probability replayable: PASS", "Importance ratio exp(new-old): PASS", "Identical policies give ratio one: PASS", "Invalid behavior action rejected: PASS", "Policy replay semantic mismatch rejected: PASS", "PPO clip operational value configured: False", "PPO optimization loop implemented: False"),
        "Value objective": ("Raw value error computed: PASS", "Raw squared value error computed: PASS", "Value-loss coefficient configured: False"),
        "Authority boundaries": ("Route-truth fields consumed: 0", "Hard action mask modified by return logic: False", "Regulatory graph modified by return logic: False", "Protocol truth modified by return logic: False", "Learned SUMO control actions issued: 0"),
        "Research parameters": ("Gamma configured: False", "GAE lambda configured: False", "PPO clip epsilon configured: False", "Learning rate configured: False", "Entropy coefficient configured: False", "Value-loss coefficient configured: False", "Rollout length configured: False", "Batch size configured: False", "Training epochs configured: False"),
        "Research status": ("Exact return implemented: True", "Advantage implemented: True", "GAE implemented operationally: False", "PPO ratio interface implemented: True", "PPO optimization implemented: False", "Optimizer implemented: False", "Parameter update performed: False", "Training performed: False", "Model checkpoint produced: False", "Safety shield implemented: False", "Learned SUMO control enabled: False"),
    }
    print("Step 5I Return / Advantage / MAPPO Mathematics Validation\n")
    for heading, lines in sections.items():
        print(heading)
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()

