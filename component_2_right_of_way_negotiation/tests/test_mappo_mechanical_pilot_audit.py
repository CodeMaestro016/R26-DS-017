"""Step 5J.3B hard configuration-gate tests."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json

# Import build_design from experimentation for the operations below.
from experimentation import build_design
# Import FROZEN_PILOT_CANDIDATE, RESOLVED_MECHANICAL_REFERENCE, build_mechanical_pilot_configuration_audit from
# negotiation_training.optimizer_contract for the operations below.
from negotiation_training.optimizer_contract import (
    FROZEN_PILOT_CANDIDATE, RESOLVED_MECHANICAL_REFERENCE,
    build_mechanical_pilot_configuration_audit)


# Check audit preserves frozen design and loads provisional reference using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_audit_preserves_frozen_design_and_loads_provisional_reference():
    # Set before to build_design()['freeze'].freeze_id.
    before = build_design()["freeze"].freeze_id
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set after to build_design()['freeze'].freeze_id.
    after = build_design()["freeze"].freeze_id
    # Require before equals after; equals audit.frozen_design_id; otherwise raise AssertionError.
    assert before == after == audit.frozen_design_id
    # Require audit.provisional_configuration_id equals a tuple containing the text 'PROVISIONAL_REFERENCE_V1';
    # otherwise raise AssertionError.
    assert audit.provisional_configuration_id == ("PROVISIONAL_REFERENCE_V1",)
    # Set frozen to a dictionary of item.choice_id mapped to item for item in audit.runtime_choices; retain
    # entries satisfying item.classification equals FROZEN_PILOT_CANDIDATE.
    frozen = {item.choice_id: item for item in audit.runtime_choices
              # Evaluate item.classification equals FROZEN_PILOT_CANDIDATE as part of the enclosing expression.
              if item.classification == FROZEN_PILOT_CANDIDATE}
    # Require frozen['gnn_hidden_dimension'].value equals 64; otherwise raise AssertionError.
    assert frozen["gnn_hidden_dimension"].value == 64
    # Require frozen['ppo_clip_epsilon'].value equals 0.2; otherwise raise AssertionError.
    assert frozen["ppo_clip_epsilon"].value == 0.2
    # Require frozen['learning_rate'].value equals 0.0005; otherwise raise AssertionError.
    assert frozen["learning_rate"].value == 0.0005
    # Require frozen['ppo_update_epochs'].value equals 5; otherwise raise AssertionError.
    assert frozen["ppo_update_epochs"].value == 5
    # Require whether every item is true in a lazy sequence of item.provenance at 'project_selected' is the same
    # object as False for item in values from frozen; otherwise raise AssertionError.
    assert all(item.provenance["project_selected"] is False
               # Evaluate values from frozen as part of the enclosing expression.
               for item in frozen.values())


# Check architecture contract resolves without promoting test depth using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_architecture_contract_resolves_without_promoting_test_depth():
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set choices to a dictionary of item.choice_id mapped to item for item in audit.runtime_choices.
    choices = {item.choice_id: item for item in audit.runtime_choices}
    # Iterate over a tuple containing the text 'gnn_message_passing_layers', the text
    # 'neural_initialization_policy', the text..., binding each item to name.
    for name in ("gnn_message_passing_layers", "neural_initialization_policy",
                 "frozen_gnn_parameter_source",
                 "proposer_actor_head_architecture",
                 "responder_actor_head_architecture",
                 "centralized_critic_architecture"):
        # Require choices[name].classification equals RESOLVED_MECHANICAL_REFERENCE; otherwise raise
        # AssertionError.
        assert choices[name].classification == RESOLVED_MECHANICAL_REFERENCE
        # Require choices[name].value is a different object from None; otherwise raise AssertionError.
        assert choices[name].value is not None
        # Require choices[name].provenance at 'project_selected' is the same object as False; otherwise raise
        # AssertionError.
        assert choices[name].provenance["project_selected"] is False
    # Require choices['gnn_message_passing_layers'].value equals 3; otherwise raise AssertionError.
    assert choices["gnn_message_passing_layers"].value == 3


# Check adam internals are explicitly resolved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_adam_internals_are_explicitly_resolved():
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Set choices to a dictionary of item.choice_id mapped to item for item in audit.runtime_choices.
    choices = {item.choice_id: item for item in audit.runtime_choices}
    # Iterate over a tuple containing the text 'adam_beta1', the text 'adam_beta2', the text 'adam_epsilon', the
    # text 'weight_decay', the text..., binding each item to name.
    for name in ("adam_beta1", "adam_beta2", "adam_epsilon", "weight_decay",
                 "adam_amsgrad", "optimizer_parameter_grouping"):
        # Require choices[name].classification equals RESOLVED_MECHANICAL_REFERENCE; otherwise raise
        # AssertionError.
        assert choices[name].classification == RESOLVED_MECHANICAL_REFERENCE
    # Require audit.silent_default_count equals 0; otherwise raise AssertionError.
    assert audit.silent_default_count == 0


# Check complete configuration still performs no behavior or optimization using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_complete_configuration_still_performs_no_behavior_or_optimization():
    # Set audit to the result of build_mechanical_pilot_configuration_audit().
    audit = build_mechanical_pilot_configuration_audit()
    # Require audit.status equals the text 'MECHANICAL_PILOT_CONFIGURATION_COMPLETE'; otherwise raise
    # AssertionError.
    assert audit.status == "MECHANICAL_PILOT_CONFIGURATION_COMPLETE"
    # Require audit.next_blocker equals the text 'NONE'; otherwise raise AssertionError.
    assert audit.next_blocker == "NONE"
    # Require audit.optimizer_instances equals 0; otherwise raise AssertionError.
    assert audit.optimizer_instances == 0
    # Require audit.backward_calls equals 0; otherwise raise AssertionError.
    assert audit.backward_calls == 0
    # Require audit.parameter_updates equals 0; otherwise raise AssertionError.
    assert audit.parameter_updates == 0
    # Require audit.provenance at 'models_constructed' equals 0; otherwise raise AssertionError.
    assert audit.provenance["models_constructed"] == 0
    # Require audit.provenance at 'behavior_policy_samples' equals 0; otherwise raise AssertionError.
    assert audit.provenance["behavior_policy_samples"] == 0
    # Require audit.provenance at 'rl_seeds_instantiated' equals 0; otherwise raise AssertionError.
    assert audit.provenance["rl_seeds_instantiated"] == 0


# Check audit implementation constructs no torch objects using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_audit_implementation_constructs_no_torch_objects():
    # Set source to the result of inspect.getsource(the result of __import__(the text
    # 'negotiation_training.optimizer_contract')).
    source = inspect.getsource(__import__(
        # Supply fromlist as a list containing the text 'x'.
        "negotiation_training.optimizer_contract", fromlist=["x"]))
    # Require the text 'import torch' does not belong to source; otherwise raise AssertionError.
    assert "import torch" not in source
    # Require the text 'torch.optim' does not belong to source; otherwise raise AssertionError.
    assert "torch.optim" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
    # Require the text 'optimizer.step' does not belong to source; otherwise raise AssertionError.
    assert "optimizer.step" not in source


# Check artifact reports zero training activity using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_artifact_reports_zero_training_activity():
    # Set payload to the decoded data produced by json.load from the result of open(the text
    # 'results/mappo_mechanical_pilot.json').
    payload = json.load(open("results/mappo_mechanical_pilot.json",
                             # Supply encoding as the text 'utf-8'.
                             encoding="utf-8"))
    # Require payload at 'status' equals the text 'MECHANICAL_PILOT_CONFIGURATION_COMPLETE'; otherwise raise
    # AssertionError.
    assert payload["status"] == "MECHANICAL_PILOT_CONFIGURATION_COMPLETE"
    # Require payload at 'policy_integration_executed' is the same object as False; otherwise raise
    # AssertionError.
    assert payload["policy_integration_executed"] is False
    # Require payload at 'training_manifest_passes' equals 0; otherwise raise AssertionError.
    assert payload["training_manifest_passes"] == 0
    # Require payload at 'ppo_eligible_proposer_factors' equals 0; otherwise raise AssertionError.
    assert payload["ppo_eligible_proposer_factors"] == 0
    # Require payload at 'ppo_eligible_responder_factors' equals 0; otherwise raise AssertionError.
    assert payload["ppo_eligible_responder_factors"] == 0
    # Require payload at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert payload["optimizer_instances"] == 0
    # Require payload at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert payload["backward_calls"] == 0
    # Require payload at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert payload["parameter_updates"] == 0
    # Require payload at 'mappo_pilot_runs' equals 0; otherwise raise AssertionError.
    assert payload["mappo_pilot_runs"] == 0
