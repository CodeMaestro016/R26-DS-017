"""Step 5J.3B hard configuration-gate tests."""

import inspect
import json

from experimentation import build_design
from negotiation_training.optimizer_contract import (
    AUDIT_BLOCKED, FROZEN_PILOT_CANDIDATE,
    RESOLVED_MECHANICAL_REFERENCE,
    build_mechanical_pilot_configuration_audit)


def test_audit_preserves_frozen_design_and_loads_provisional_reference():
    before = build_design()["freeze"].freeze_id
    audit = build_mechanical_pilot_configuration_audit()
    after = build_design()["freeze"].freeze_id
    assert before == after == audit.frozen_design_id
    assert audit.provisional_configuration_id == ("PROVISIONAL_REFERENCE_V1",)
    frozen = {item.choice_id: item for item in audit.runtime_choices
              if item.classification == FROZEN_PILOT_CANDIDATE}
    assert frozen["gnn_hidden_dimension"].value == 64
    assert frozen["ppo_clip_epsilon"].value == 0.2
    assert frozen["learning_rate"].value == 0.0005
    assert frozen["ppo_update_epochs"].value == 5
    assert all(item.provenance["project_selected"] is False
               for item in frozen.values())


def test_architecture_contract_resolves_without_promoting_test_depth():
    audit = build_mechanical_pilot_configuration_audit()
    choices = {item.choice_id: item for item in audit.runtime_choices}
    for name in ("gnn_message_passing_layers", "neural_initialization_policy",
                 "frozen_gnn_parameter_source",
                 "proposer_actor_head_architecture",
                 "responder_actor_head_architecture",
                 "centralized_critic_architecture"):
        assert choices[name].classification == RESOLVED_MECHANICAL_REFERENCE
        assert choices[name].value is not None
        assert choices[name].provenance["project_selected"] is False
    assert choices["gnn_message_passing_layers"].value == 3


def test_adam_internals_are_not_silently_inherited():
    audit = build_mechanical_pilot_configuration_audit()
    unresolved = set(audit.unresolved_choice_ids)
    assert {"adam_beta1", "adam_beta2", "adam_epsilon", "weight_decay",
            "adam_amsgrad", "optimizer_parameter_grouping"} <= unresolved
    assert audit.silent_default_count == 0


def test_hard_stop_prevents_behavior_collection_and_optimization():
    audit = build_mechanical_pilot_configuration_audit()
    assert audit.status == AUDIT_BLOCKED
    assert audit.next_blocker == "ADAM_INTERNAL_PARAMETER_CONTRACT_UNRESOLVED"
    assert audit.optimizer_instances == 0
    assert audit.backward_calls == 0
    assert audit.parameter_updates == 0
    assert audit.provenance["models_constructed"] == 0
    assert audit.provenance["behavior_policy_samples"] == 0
    assert audit.provenance["rl_seeds_instantiated"] == 0


def test_audit_implementation_constructs_no_torch_objects():
    source = inspect.getsource(__import__(
        "negotiation_training.optimizer_contract", fromlist=["x"]))
    assert "import torch" not in source
    assert "torch.optim" not in source
    assert ".backward(" not in source
    assert "optimizer.step" not in source


def test_artifact_reports_zero_training_activity():
    payload = json.load(open("results/mappo_mechanical_pilot.json",
                             encoding="utf-8"))
    assert payload["status"] == AUDIT_BLOCKED
    assert payload["policy_integration_executed"] is False
    assert payload["training_manifest_passes"] == 0
    assert payload["ppo_eligible_proposer_factors"] == 0
    assert payload["ppo_eligible_responder_factors"] == 0
    assert payload["optimizer_instances"] == 0
    assert payload["backward_calls"] == 0
    assert payload["parameter_updates"] == 0
    assert payload["mappo_pilot_runs"] == 0
