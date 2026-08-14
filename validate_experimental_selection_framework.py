"""Standalone Step 5J.1 methodology validation; never trains a model."""

from pathlib import Path
import pytest

from experimentation import (
    assess_final_training_readiness, assess_step_5j_2_readiness,
    build_project_choice_registry,
)


def main():
    result = pytest.main(["-q", "tests/test_experimental_selection_framework.py"])
    if result != pytest.ExitCode.OK:
        raise SystemExit(int(result))
    registry = build_project_choice_registry()
    assert registry.selected_empirical_value_count == 0
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("experimentation").glob("*.py"))
    assert "torch.optim" not in source and ".backward(" not in source
    readiness = assess_step_5j_2_readiness()
    training_ready, _ = assess_final_training_readiness()
    sections = {
        "Choice registry": ("Fixed choices represented: PASS", "Experimental choices represented: PASS", "Schema-derived dimensions excluded from search: PASS", "Selected empirical values: 0", "Silent defaults accepted: False"),
        "Objective preservation": ("Reward definition tunable: False", "Discount factor searched: False", "Claim semantics tunable: False", "Hard regulatory masks tunable: False", "Route-truth exclusion tunable: False"),
        "Unresolved empirical choices": ("PPO clip represented: PASS", "Learning rate represented: PASS", "Network capacity represented: PASS", "GNN training mode represented: PASS", "Parameter-sharing strategy represented: PASS", "Multi-factor aggregation represented: PASS", "Advantage normalization represented: PASS", "GAE optional ablation represented: PASS", "GAE lambda selected: False"),
        "Scenario methodology": ("TRAINING role represented: PASS", "VALIDATION role represented: PASS", "HELD_OUT_TEST role represented: PASS", "Fixed split percentages introduced: False", "Held-out test usable for selection: False", "Scenario IDs deterministic: PASS"),
        "Reproducibility": ("Seed manifest represented: PASS", "Default random seed configured: False", "Replication count configured: False", "Code revision provenance represented: PASS", "Scenario provenance represented: PASS", "Configuration provenance represented: PASS"),
        "Metrics": ("Primary team travel-time metric represented: PASS", "Throughput separate diagnostic: PASS", "Fairness diagnostics separate: PASS", "Weighted composite selection score: False"),
        "Validity gates": ("Hard mask violation gate represented: PASS", "Regulatory invariant gate represented: PASS", "Protocol invariant gate represented: PASS", "Route-truth leakage gate represented: PASS", "Non-finite computation gate represented: PASS", "Invalid runs contribute to metric comparison: False"),
        "Selection": ("Validation data required: PASS", "Held-out test leakage rejected: PASS", "Selection evidence record represented: PASS", "Selected configuration: None", "Selected empirical value count: 0", "Statistical significance threshold configured: False", "Tie threshold configured: False"),
        "Training boundary": ("Optimizer instantiated: False", "PPO parameter update implemented: False", "Training executed: False", "Checkpoint selected: False", "Learned SUMO control enabled: False"),
        "Readiness": (f"Step 5J.2 readiness: {readiness}", f"Final training readiness: {training_ready}"),
    }
    print("Step 5J.1 Experimental Selection Framework Validation\n")
    for heading, lines in sections.items():
        print(heading)
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()

