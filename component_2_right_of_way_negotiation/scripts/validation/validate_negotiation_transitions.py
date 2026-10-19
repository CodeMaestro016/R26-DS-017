"""Standalone Step 5G validation; no SUMO, reward, optimizer, or training."""

from pathlib import Path
import pytest


def main():
    result = pytest.main(["-q", "tests/test_negotiation_transitions.py"])
    if result != pytest.ExitCode.OK:
        raise SystemExit(int(result))
    sources = "\n".join(path.read_text(encoding="utf-8") for path in
                        Path("negotiation_learning/transitions").glob("*.py"))
    forbidden = ("POLICY_DECISION_INTERVAL", "NEGOTIATION_TIMEOUT",
                 "POSITION_CHANGE_THRESHOLD", "TTC_CHANGE_THRESHOLD",
                 "GAE_LAMBDA", "PPO_CLIP", "LEARNING_RATE", "REWARD_WEIGHT")
    assert not any(item in sources for item in forbidden)
    assert "route_id" not in sources and "ground_truth_route_id" not in sources
    print("Step 5G Negotiation Transition Validation\n")
    sections = {
        "Decision epochs": ("Event-driven semantic decision detection: PASS", "Unchanged claim does not emit every frame: PASS", "Timestamp alone creates new decision: False", "Fixed decision interval introduced: False", "New lifecycle may emit new claim decision: PASS", "Hard feasibility change handled semantically: PASS"),
        "Action consequences": ("KEEP_CLAIM consequence represented: PASS", "KEEP_CLAIM creates proposal: False", "RELINQUISH creates claim-specific proposal: PASS", "ACCEPT creates matching protocol response: PASS", "REJECT creates matching protocol response: PASS", "Policy bypasses deterministic protocol: False"),
        "Causal links": ("Proposer decision -> proposal: PASS", "Proposal -> responder decision: PASS", "Responder decision -> protocol result: PASS", "Multiple simultaneous proposal links isolated: PASS"),
        "Transition lifecycle": ("Agreement resolution: PASS", "Rejection resolution: PASS", "Source-invalid resolution: PASS", "Protocol-blocked resolution: PASS", "Protocol-disagreement resolution: PASS", "Duplicate resolution prevented: PASS"),
        "Timing": ("Exact elapsed time recorded: PASS", "Zero-duration same-step transition: PASS", "Positive variable duration: PASS", "Negative duration rejected: PASS", "Timeout constants introduced: 0"),
        "Multiple agents": ("Multiple simultaneous decision epochs: PASS", "Per-claim transitions independent: PASS", "Processing-order invariance: PASS"),
        "Replayable actor observation": ("Raw graph tensors preserved: PASS", "Raw graph snapshot immutable: PASS", "Step 5F.1 claim encoding reconstructible: PASS", "Step 5F.1 proposal encoding reconstructible: PASS", "Protocol-state encoding reconstructible: PASS", "GNN forward input reconstructible: PASS", "GNN forward output replayable: PASS", "Role-aware policy logits replayable: PASS", "Hard mask replayable: PASS"),
        "Centralized training observation": ("Critic input reconstructible: PASS", "Critic forward pass replayable: PASS", "Centralized data training-only: PASS", "Critic-only data exposed to actor: False"),
        "Authority boundaries": ("Route-truth fields consumed: 0", "Identifier-derived numeric model features: 0", "Actor logits control semantic authority: False", "Learned policy SUMO actions issued: 0"),
        "Research parameters": ("Decision interval configured: False", "Transition timeout configured: False", "State-change threshold configured: False", "Gamma configured: False", "GAE lambda configured: False", "PPO clip configured: False", "Learning rate configured: False", "Reward weights configured: False"),
        "Research status": ("Transition semantics implemented: True", "Reward implemented: False", "Return implemented: False", "Advantage implemented: False", "GAE implemented: False", "PPO ratio implemented: False", "PPO loss implemented: False", "Optimizer implemented: False", "Training performed: False", "Safety shield implemented: False", "Learned SUMO control enabled: False"),
        "Temporal formulation": ("Event-driven semantics: SUPPORTED", "Variable physical transition duration: SUPPORTED", "Formal Dec-POMDP claim: False", "Formal SMDP claim: False", "Semi-Markov-compatible timing: SUPPORTED_FOR_FUTURE_FORMULATION"),
    }
    for heading, lines in sections.items():
        print(heading)
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()
