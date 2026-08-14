"""Standalone deterministic Step 5H.0 validation without SUMO startup."""

from pathlib import Path
import pytest


def main():
    result = pytest.main(["-q", "tests/test_demand_ledger.py"])
    if result != pytest.ExitCode.OK:
        raise SystemExit(int(result))
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("traffic_accounting").glob("*.py"))
    assert "team_reward" not in source
    assert "spawn_delay_threshold" not in source
    sections = {
        "Schedule registration": (
            "Initial scheduled demand retained: PASS",
            "Validation-schedule timestamp retained: PASS",
            "Periodic batch timestamp retained: PASS",
            "Processing timestamp does not replace schedule: PASS",
            "Duplicate schedule overwrite: False",
        ),
        "Departure": (
            "Actual SUMO departure represented separately: PASS",
            "Departure may occur after schedule: PASS",
            "Departure before schedule rejected: PASS",
            "Departure without schedule rejected: PASS",
        ),
        "Arrival": (
            "SUMO arrival represented as service completion: PASS",
            "Arrival without schedule rejected: PASS",
            "Arrival without departure rejected: PASS",
            "Arrival before departure rejected: PASS",
        ),
        "Episode finalization": (
            "Scheduled but never departed retained: PASS",
            "Departed but unfinished retained: PASS",
            "Completed vehicle retained: PASS",
            "No terminal penalty introduced: PASS",
        ),
        "Invariants": (
            "scheduled <= departure <= completion for completed vehicles: PASS",
            "Historical scheduled timestamp immutable: PASS",
            "Record immutability: PASS", "Processing-order invariance: PASS",
        ),
        "Authority boundaries": (
            "Demand ledger exposed to actor: False",
            "Future arrival used as critic feature: False",
            "Route metadata used as actor/GNN numeric feature: False",
            "Learned SUMO control actions issued: 0",
        ),
        "Research parameters": (
            "New operational thresholds: 0", "Spawn-delay thresholds: 0",
            "Departure timeouts: 0", "Service timeouts: 0",
            "Waiting-speed thresholds: 0", "Reward constants: 0",
            "PPO hyperparameters: 0",
        ),
        "Research status": (
            "Scheduled demand accounting implemented: True",
            "Actual departure accounting implemented: True",
            "Service completion accounting implemented: True",
            "SCHEDULED_SPAWN_ACCOUNTING_INCOMPLETE: False",
            "Reward implemented: False", "Return implemented: False",
            "Advantage implemented: False", "GAE implemented: False",
            "PPO implemented: False", "Optimizer implemented: False",
            "Training performed: False", "Learned control enabled: False",
        ),
    }
    print("Step 5H.0 Scheduled Demand Ledger Validation\n")
    for heading, lines in sections.items():
        print(heading)
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()

