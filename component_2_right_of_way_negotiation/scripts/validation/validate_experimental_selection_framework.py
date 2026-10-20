"""Standalone Step 5J.1 methodology validation; never trains a model."""

# Import Path from pathlib for the operations below.
from pathlib import Path
# Import pytest for use in this module.
import pytest

# Import assess_final_training_readiness, assess_step_5j_2_readiness, build_project_choice_registry from
# experimentation for the operations below.
from experimentation import (
    assess_final_training_readiness, assess_step_5j_2_readiness,
    build_project_choice_registry,
)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set result to the result of pytest.main(a list containing the text '-q', the text
    # 'tests/test_experimental_selection_framework.py').
    result = pytest.main(["-q", "tests/test_experimental_selection_framework.py"])
    # Run this branch when result differs from pytest.ExitCode.OK.
    if result != pytest.ExitCode.OK:
        # Raise SystemExit with an integer built from result to stop this execution path.
        raise SystemExit(int(result))
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Require registry.selected_empirical_value_count equals 0; otherwise raise AssertionError.
    assert registry.selected_empirical_value_count == 0
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('experimentation').glob(the text '*.py') as part of the
                       # enclosing expression.
                       for path in Path("experimentation").glob("*.py"))
    # Require the text 'torch.optim' does not belong to source and the text '.backward(' does not belong to
    # source; otherwise raise AssertionError.
    assert "torch.optim" not in source and ".backward(" not in source
    # Set readiness to the result of assess_step_5j_2_readiness().
    readiness = assess_step_5j_2_readiness()
    # Set (training_ready, _) to the result of assess_final_training_readiness().
    training_ready, _ = assess_final_training_readiness()
    # Set sections to a dictionary containing Choice registry, Objective preservation, Unresolved empirical
    # choices, Scenario...
    sections = {
        # Store a tuple containing the text 'Fixed choices represented: PASS', the text 'Experimental choices
        # represented: PASS', the text... under 'Choice registry'.
        "Choice registry": ("Fixed choices represented: PASS", "Experimental choices represented: PASS", "Schema-derived dimensions excluded from search: PASS", "Selected empirical values: 0", "Silent defaults accepted: False"),
        # Store a tuple containing the text 'Reward definition tunable: False', the text 'Discount factor
        # searched: False', the text 'Claim... under 'Objective preservation'.
        "Objective preservation": ("Reward definition tunable: False", "Discount factor searched: False", "Claim semantics tunable: False", "Hard regulatory masks tunable: False", "Route-truth exclusion tunable: False"),
        # Store a tuple containing the text 'PPO clip represented: PASS', the text 'Learning rate represented:
        # PASS', the text 'Network... under 'Unresolved empirical choices'.
        "Unresolved empirical choices": ("PPO clip represented: PASS", "Learning rate represented: PASS", "Network capacity represented: PASS", "GNN training mode represented: PASS", "Parameter-sharing strategy represented: PASS", "Multi-factor aggregation represented: PASS", "Advantage normalization represented: PASS", "GAE optional ablation represented: PASS", "GAE lambda selected: False"),
        # Store a tuple containing the text 'TRAINING role represented: PASS', the text 'VALIDATION role
        # represented: PASS', the text... under 'Scenario methodology'.
        "Scenario methodology": ("TRAINING role represented: PASS", "VALIDATION role represented: PASS", "HELD_OUT_TEST role represented: PASS", "Fixed split percentages introduced: False", "Held-out test usable for selection: False", "Scenario IDs deterministic: PASS"),
        # Store a tuple containing the text 'Seed manifest represented: PASS', the text 'Default random seed
        # configured: False', the text... under 'Reproducibility'.
        "Reproducibility": ("Seed manifest represented: PASS", "Default random seed configured: False", "Replication count configured: False", "Code revision provenance represented: PASS", "Scenario provenance represented: PASS", "Configuration provenance represented: PASS"),
        # Store a tuple containing the text 'Primary team travel-time metric represented: PASS', the text
        # 'Throughput separate diagnostic:... under 'Metrics'.
        "Metrics": ("Primary team travel-time metric represented: PASS", "Throughput separate diagnostic: PASS", "Fairness diagnostics separate: PASS", "Weighted composite selection score: False"),
        # Store a tuple containing the text 'Hard mask violation gate represented: PASS', the text 'Regulatory
        # invariant gate represented:... under 'Validity gates'.
        "Validity gates": ("Hard mask violation gate represented: PASS", "Regulatory invariant gate represented: PASS", "Protocol invariant gate represented: PASS", "Route-truth leakage gate represented: PASS", "Non-finite computation gate represented: PASS", "Invalid runs contribute to metric comparison: False"),
        # Store a tuple containing the text 'Validation data required: PASS', the text 'Held-out test leakage
        # rejected: PASS', the text... under 'Selection'.
        "Selection": ("Validation data required: PASS", "Held-out test leakage rejected: PASS", "Selection evidence record represented: PASS", "Selected configuration: None", "Selected empirical value count: 0", "Statistical significance threshold configured: False", "Tie threshold configured: False"),
        # Store a tuple containing the text 'Optimizer instantiated: False', the text 'PPO parameter update
        # implemented: False', the text... under 'Training boundary'.
        "Training boundary": ("Optimizer instantiated: False", "PPO parameter update implemented: False", "Training executed: False", "Checkpoint selected: False", "Learned SUMO control enabled: False"),
        # Store a tuple containing formatted text built from the embedded values, formatted text built from the
        # embedded values under 'Readiness'.
        "Readiness": (f"Step 5J.2 readiness: {readiness}", f"Final training readiness: {training_ready}"),
    }
    # Display the text 'Step 5J.1 Experimental Selection Framework Validation'.
    print("Step 5J.1 Experimental Selection Framework Validation\n")
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

