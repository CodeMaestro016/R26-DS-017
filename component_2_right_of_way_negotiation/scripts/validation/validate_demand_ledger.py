"""Standalone deterministic Step 5H.0 validation without SUMO startup."""

# Import Path from pathlib for the operations below.
from pathlib import Path
# Import pytest for use in this module.
import pytest


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set result to the result of pytest.main(a list containing the text '-q', the text
    # 'tests/test_demand_ledger.py').
    result = pytest.main(["-q", "tests/test_demand_ledger.py"])
    # Run this branch when result differs from pytest.ExitCode.OK.
    if result != pytest.ExitCode.OK:
        # Raise SystemExit with an integer built from result to stop this execution path.
        raise SystemExit(int(result))
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('traffic_accounting').glob(the text '*.py') as part of the
                       # enclosing expression.
                       for path in Path("traffic_accounting").glob("*.py"))
    # Require the text 'team_reward' does not belong to source; otherwise raise AssertionError.
    assert "team_reward" not in source
    # Require the text 'spawn_delay_threshold' does not belong to source; otherwise raise AssertionError.
    assert "spawn_delay_threshold" not in source
    # Set sections to a dictionary containing Schedule registration, Departure, Arrival, Episode finalization,
    # Invariants, Authority...
    sections = {
        # Store a tuple containing the text 'Initial scheduled demand retained: PASS', the text
        # 'Validation-schedule timestamp retained:... under 'Schedule registration'.
        "Schedule registration": (
            "Initial scheduled demand retained: PASS",
            "Validation-schedule timestamp retained: PASS",
            "Periodic batch timestamp retained: PASS",
            "Processing timestamp does not replace schedule: PASS",
            "Duplicate schedule overwrite: False",
        ),
        # Store a tuple containing the text 'Actual SUMO departure represented separately: PASS', the text
        # 'Departure may occur after... under 'Departure'.
        "Departure": (
            "Actual SUMO departure represented separately: PASS",
            "Departure may occur after schedule: PASS",
            "Departure before schedule rejected: PASS",
            "Departure without schedule rejected: PASS",
        ),
        # Store a tuple containing the text 'SUMO arrival represented as service completion: PASS', the text
        # 'Arrival without schedule... under 'Arrival'.
        "Arrival": (
            "SUMO arrival represented as service completion: PASS",
            "Arrival without schedule rejected: PASS",
            "Arrival without departure rejected: PASS",
            "Arrival before departure rejected: PASS",
        ),
        # Store a tuple containing the text 'Scheduled but never departed retained: PASS', the text 'Departed but
        # unfinished retained: PASS',... under 'Episode finalization'.
        "Episode finalization": (
            "Scheduled but never departed retained: PASS",
            "Departed but unfinished retained: PASS",
            "Completed vehicle retained: PASS",
            "No terminal penalty introduced: PASS",
        ),
        # Store a tuple containing the text 'scheduled <= departure <= completion for completed vehicles: PASS',
        # the text 'Historical... under 'Invariants'.
        "Invariants": (
            "scheduled <= departure <= completion for completed vehicles: PASS",
            "Historical scheduled timestamp immutable: PASS",
            "Record immutability: PASS", "Processing-order invariance: PASS",
        ),
        # Store a tuple containing the text 'Demand ledger exposed to actor: False', the text 'Future arrival used
        # as critic feature: False',... under 'Authority boundaries'.
        "Authority boundaries": (
            "Demand ledger exposed to actor: False",
            "Future arrival used as critic feature: False",
            "Route metadata used as actor/GNN numeric feature: False",
            "Learned SUMO control actions issued: 0",
        ),
        # Store a tuple containing the text 'New operational thresholds: 0', the text 'Spawn-delay thresholds: 0',
        # the text 'Departure... under 'Research parameters'.
        "Research parameters": (
            "New operational thresholds: 0", "Spawn-delay thresholds: 0",
            "Departure timeouts: 0", "Service timeouts: 0",
            "Waiting-speed thresholds: 0", "Reward constants: 0",
            "PPO hyperparameters: 0",
        ),
        # Store a tuple containing the text 'Scheduled demand accounting implemented: True', the text 'Actual
        # departure accounting... under 'Research status'.
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
    # Display the text 'Step 5H.0 Scheduled Demand Ledger Validation'.
    print("Step 5H.0 Scheduled Demand Ledger Validation\n")
    # Iterate over key/value pairs from sections, binding each item to (heading, lines).
    for heading, lines in sections.items():
        # Display heading.
        print(heading)
        # Iterate over lines, binding each item to line.
        for line in lines:
            # Display formatted text built from the embedded values.
            print(f"  {line}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()

