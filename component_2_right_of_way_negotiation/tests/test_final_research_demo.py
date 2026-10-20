# Import Path from pathlib for the operations below.
from pathlib import Path
# Import json for use in this module.
import json

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import SELECTION_RULE, SOURCE_CHECKPOINT, create_demo_policy, file_sha256, load_demo_policy from
# negotiation_training.demo_policy for the operations below.
from negotiation_training.demo_policy import (
    SELECTION_RULE, SOURCE_CHECKPOINT, create_demo_policy, file_sha256,
    load_demo_policy)
# Import DemonstrationMAPPOActionProvider from negotiation_training.demo_provider for the operations below.
from negotiation_training.demo_provider import DemonstrationMAPPOActionProvider
# Import GUI_RESULT_PATH, RESULT_PATH, SCENARIO_RULE, parse_args, select_demo_scenarios from run_research_demo for
# the operations below.
from run_research_demo import (
    GUI_RESULT_PATH, RESULT_PATH, SCENARIO_RULE, parse_args,
    select_demo_scenarios)
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Demo payload using the inputs and processing steps below.
# Input tmp_path_factory: the supplied tmp path factory.
# Output: the result of create_demo_policy().
def demo_payload(tmp_path_factory):
    # Set path to the result of tmp_path_factory.mktemp(the text 'demo_policy') joined with the path segment 'demo.pt'.
    path = tmp_path_factory.mktemp("demo_policy") / "demo.pt"
    # Return the result of create_demo_policy() to the caller.
    return create_demo_policy(output_path=path)


# Check source checkpoint is canonical replication zero state two using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_source_checkpoint_is_canonical_replication_zero_state_two():
    # Require the result of str(SOURCE_CHECKPOINT).replace(the text '\\', the text '/') equals the text
    # 'results/mappo_extended_resume/replication_0_state_2.pt'; otherwise raise AssertionError.
    assert str(SOURCE_CHECKPOINT).replace("\\", "/") == \
        "results/mappo_extended_resume/replication_0_state_2.pt"
    # Set source to the decoded data produced by torch.load from SOURCE_CHECKPOINT.
    source = torch.load(SOURCE_CHECKPOINT, map_location="cpu", weights_only=False)
    # Require source['replication_identity'] at -1 equals 0; otherwise raise AssertionError.
    assert source["replication_identity"][-1] == 0
    # Require source at 'policy_state_index' equals 2; otherwise raise AssertionError.
    assert source["policy_state_index"] == 2


# Check original resume checkpoint is not mutated using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_original_resume_checkpoint_is_not_mutated(tmp_path):
    # Set before to the result of file_sha256(SOURCE_CHECKPOINT).
    before = file_sha256(SOURCE_CHECKPOINT)
    # Call create_demo_policy with the supplied arguments.
    create_demo_policy(output_path=tmp_path / "demo.pt")
    # Require the result of file_sha256(SOURCE_CHECKPOINT) equals before; otherwise raise AssertionError.
    assert file_sha256(SOURCE_CHECKPOINT) == before
    # Set source to the decoded data produced by torch.load from SOURCE_CHECKPOINT.
    source = torch.load(SOURCE_CHECKPOINT, map_location="cpu", weights_only=False)
    # Require source at 'checkpoint_type' equals the text 'EVIDENCE_RESUME_CHECKPOINT_ONLY'; otherwise raise
    # AssertionError.
    assert source["checkpoint_type"] == "EVIDENCE_RESUME_CHECKPOINT_ONLY"
    # Require source at 'best_model' is the same object as False; otherwise raise AssertionError.
    assert source["best_model"] is False
    # Require source at 'final_model' is the same object as False; otherwise raise AssertionError.
    assert source["final_model"] is False
    # Require source at 'selected_model' is the same object as False; otherwise raise AssertionError.
    assert source["selected_model"] is False
    # Require source at 'selection_eligible' is the same object as False; otherwise raise AssertionError.
    assert source["selection_eligible"] is False


# Check demo policy is provenance selected never best final or optimal using the setup, calls, and assertions
# below.
# Input demo_payload: the supplied demo payload.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_demo_policy_is_provenance_selected_never_best_final_or_optimal(demo_payload):
    # Require demo_payload at 'demo_checkpoint_selection_rule' equals SELECTION_RULE; otherwise raise
    # AssertionError.
    assert demo_payload["demo_checkpoint_selection_rule"] == SELECTION_RULE
    # Iterate over a tuple containing the text 'performance_selected', the text 'statistically_selected', the text
    # 'best_model', the text..., binding each item to field.
    for field in ("performance_selected", "statistically_selected",
                  "best_model", "final_model", "optimal_model",
                  "held_out_selected"):
        # Require demo_payload at field is the same object as False; otherwise raise AssertionError.
        assert demo_payload[field] is False


# Check demo policy identity is deterministic using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_demo_policy_identity_is_deterministic(tmp_path):
    # Set first to the result of create_demo_policy().
    first = create_demo_policy(output_path=tmp_path / "one.pt")
    # Set second to the result of create_demo_policy().
    second = create_demo_policy(output_path=tmp_path / "two.pt")
    # Require first at 'demo_policy_identity' equals second at 'demo_policy_identity'; otherwise raise
    # AssertionError.
    assert first["demo_policy_identity"] == second["demo_policy_identity"]
    # Require first at 'parameter_hashes' equals second at 'parameter_hashes'; otherwise raise AssertionError.
    assert first["parameter_hashes"] == second["parameter_hashes"]


# Check demo policy contains only decentralized model states using the setup, calls, and assertions below.
# Input demo_payload: the supplied demo payload.
# Output: no explicit value; normal completion returns None.
def test_demo_policy_contains_only_decentralized_model_states(demo_payload):
    # Require the text 'gnn_state_dict' belongs to demo_payload; otherwise raise AssertionError.
    assert "gnn_state_dict" in demo_payload
    # Require the text 'proposer_state_dict' belongs to demo_payload; otherwise raise AssertionError.
    assert "proposer_state_dict" in demo_payload
    # Require the text 'responder_state_dict' belongs to demo_payload; otherwise raise AssertionError.
    assert "responder_state_dict" in demo_payload
    # Require the text 'critic_state_dict' does not belong to demo_payload; otherwise raise AssertionError.
    assert "critic_state_dict" not in demo_payload
    # Require demo_payload at 'centralized_critic_included' is the same object as False; otherwise raise
    # AssertionError.
    assert demo_payload["centralized_critic_included"] is False


# Check demo provider has no runtime critic and preserves hashes using the setup, calls, and assertions below.
# Input demo_payload: the supplied demo payload.
# Output: no explicit value; normal completion returns None.
def test_demo_provider_has_no_runtime_critic_and_preserves_hashes(demo_payload):
    # Set provider to the result of DemonstrationMAPPOActionProvider(demo_payload).
    provider = DemonstrationMAPPOActionProvider(demo_payload)
    # Require provider.bundle.centralized_critic is the same object as None; otherwise raise AssertionError.
    assert provider.bundle.centralized_critic is None
    # Require provider.runtime_critic_enabled is the same object as False; otherwise raise AssertionError.
    assert provider.runtime_critic_enabled is False
    # Require provider.runtime_critic_calls equals 0; otherwise raise AssertionError.
    assert provider.runtime_critic_calls == 0
    # Require the result of provider.inference_parameter_hashes() equals demo_payload at 'parameter_hashes';
    # otherwise raise AssertionError.
    assert provider.inference_parameter_hashes() == demo_payload["parameter_hashes"]
    # Require whether every item is true in a lazy sequence of the negation of parameter.requires_grad for module
    # in a tuple containing provider.bundle.gnn, provider.bundle.proposer_actor, provider.bundle.responder_actor;
    # otherwise raise AssertionError.
    assert all(not parameter.requires_grad for module in (
        # Include provider.bundle.proposer_actor in this tuple.
        provider.bundle.gnn, provider.bundle.proposer_actor,
        # Include provider.bundle.responder_actor in this tuple.
        provider.bundle.responder_actor) for parameter in module.parameters())


# Check actor boundary and hard masks are explicit using the setup, calls, and assertions below.
# Input demo_payload: the supplied demo payload.
# Output: no explicit value; normal completion returns None.
def test_actor_boundary_and_hard_masks_are_explicit(demo_payload):
    # Set provider to the result of DemonstrationMAPPOActionProvider(demo_payload).
    provider = DemonstrationMAPPOActionProvider(demo_payload)
    # Require provider.actor_route_truth_fields_consumed equals 0; otherwise raise AssertionError.
    assert provider.actor_route_truth_fields_consumed == 0
    # Require provider.ego_local_observation_used is the same object as True; otherwise raise AssertionError.
    assert provider.ego_local_observation_used is True
    # Require provider.hard_action_mask_applied is the same object as True; otherwise raise AssertionError.
    assert provider.hard_action_mask_applied is True
    # Require provider.optimizer_instances equals 0; otherwise raise AssertionError.
    assert provider.optimizer_instances == 0
    # Require provider.backward_calls equals 0; otherwise raise AssertionError.
    assert provider.backward_calls == 0
    # Require provider.parameter_updates equals 0; otherwise raise AssertionError.
    assert provider.parameter_updates == 0


# Check three scenarios are distinct training catalogue structures using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_three_scenarios_are_distinct_training_catalogue_structures():
    # Set design to the result of build_design().
    design = build_design()
    # Set selected to the result of select_demo_scenarios(design).
    selected = select_demo_scenarios(design)
    # Set ids to a list of item['signature'].scenario_id for item in selected.
    ids = [item["signature"].scenario_id for item in selected]
    # Set training to a set built from design['manifests'][ScenarioRole.TRAINING].scenario_ids.
    training = set(design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    # Set held_out to a set built from design['manifests'][ScenarioRole.HELD_OUT_TEST].scenario_ids.
    held_out = set(design["manifests"][ScenarioRole.HELD_OUT_TEST].scenario_ids)
    # Require the number of entries in selected equals the number of entries in a set built from ids; equals 3;
    # otherwise raise AssertionError.
    assert len(selected) == len(set(ids)) == 3
    # Require a set built from ids is at most training; otherwise raise AssertionError.
    assert set(ids) <= training
    # Require the result of set(ids).isdisjoint(held_out); otherwise raise AssertionError.
    assert set(ids).isdisjoint(held_out)
    # Require a list of item at 'category' for item in selected equals a list containing the text
    # 'REGULATORY_CYCLE_NEGOTIATION', the text 'MULTI_FACTOR_MULTI_ACTION_NEGOTIATION', the text...; otherwise
    # raise AssertionError.
    assert [item["category"] for item in selected] == [
        "REGULATORY_CYCLE_NEGOTIATION",
        "MULTI_FACTOR_MULTI_ACTION_NEGOTIATION",
        "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION"]


# Check scenario selection is structural not performance based using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_scenario_selection_is_structural_not_performance_based():
    # Set source to the text read from Path('run_research_demo.py').
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    # Set selector to source sliced by source.index('def select_demo_scenarios'):source.index('def
    # _scenario_trace').
    selector = source[source.index("def select_demo_scenarios"):
                      # Evaluate the result of source.index(the text 'def _scenario_trace') as part of the
                      # enclosing expression.
                      source.index("def _scenario_trace")]
    # Require the text 'team_travel_time' does not belong to selector; otherwise raise AssertionError.
    assert "team_travel_time" not in selector
    # Require the text 'performance' does not belong to the result of SCENARIO_RULE.lower(); otherwise raise
    # AssertionError.
    assert "performance" not in SCENARIO_RULE.lower()


# Check normal main does not enable demo policy using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_normal_main_does_not_enable_demo_policy():
    # Set source to the text read from Path('main.py').
    source = Path("main.py").read_text(encoding="utf-8")
    # Require the text 'DemonstrationMAPPOActionProvider' does not belong to source; otherwise raise
    # AssertionError.
    assert "DemonstrationMAPPOActionProvider" not in source
    # Require the text 'mappo_demo_policy' does not belong to source; otherwise raise AssertionError.
    assert "mappo_demo_policy" not in source


# Check explicit runner uses real sumo coupled environment using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_explicit_runner_uses_real_sumo_coupled_environment():
    # Set source to the text read from Path('run_research_demo.py').
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    # Require the text 'DemonstrationMAPPOActionProvider' belongs to source; otherwise raise AssertionError.
    assert "DemonstrationMAPPOActionProvider" in source
    # Require the text 'CoupledNegotiationTrainingEnvironment' belongs to source; otherwise raise AssertionError.
    assert "CoupledNegotiationTrainingEnvironment" in source
    # Require the text 'run_episode' belongs to source; otherwise raise AssertionError.
    assert "run_episode" in source


# Check coupled environment defaults to headless using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_coupled_environment_defaults_to_headless():
    # Set environment to the result of CoupledNegotiationTrainingEnvironment(the result of object()).
    environment = CoupledNegotiationTrainingEnvironment(object())
    # Require environment.use_gui is the same object as False; otherwise raise AssertionError.
    assert environment.use_gui is False


# Check research demo gui cli is opt in and uses separate evidence using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_research_demo_gui_cli_is_opt_in_and_uses_separate_evidence():
    # Require parse_args([]).gui is the same object as False; otherwise raise AssertionError.
    assert parse_args([]).gui is False
    # Require parse_args(['--gui']).gui is the same object as True; otherwise raise AssertionError.
    assert parse_args(["--gui"]).gui is True
    # Require RESULT_PATH.name equals the text 'final_research_prototype_demo.json'; otherwise raise
    # AssertionError.
    assert RESULT_PATH.name == "final_research_prototype_demo.json"
    # Require GUI_RESULT_PATH.name equals the text 'final_research_prototype_demo_gui.json'; otherwise raise
    # AssertionError.
    assert GUI_RESULT_PATH.name == "final_research_prototype_demo_gui.json"
    # Set source to the text read from Path('run_research_demo.py').
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    # Require the text 'DemonstrationMAPPOActionProvider(policy)' belongs to source; otherwise raise
    # AssertionError.
    assert "DemonstrationMAPPOActionProvider(policy)" in source
    # Require the text 'provider, use_gui=use_gui' belongs to source; otherwise raise AssertionError.
    assert "provider, use_gui=use_gui" in source


# Check demo has no optimizer backward or parameter update code using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_demo_has_no_optimizer_backward_or_parameter_update_code():
    # Set source to the result of '\n'.join(a lazy sequence of the text read from Path(path) for path in a tuple
    # containing the text...).
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in (
        "negotiation_training/demo_policy.py",
        "negotiation_training/demo_provider.py",
        "run_research_demo.py"))
    # Require the text 'torch.optim' does not belong to source; otherwise raise AssertionError.
    assert "torch.optim" not in source
    # Require the text 'optimizer.step(' does not belong to source; otherwise raise AssertionError.
    assert "optimizer.step(" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
    # Require the text 'MechanicalMAPPOTrainer' does not belong to source; otherwise raise AssertionError.
    assert "MechanicalMAPPOTrainer" not in source


# Check safety failure is preserved before reraise using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_safety_failure_is_preserved_before_reraise():
    # Set source to the text read from Path('run_research_demo.py').
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    # Set failure_write to the result of source.index(the text 'atomic_write_json(RESULT_PATH, failure)').
    failure_write = source.index("atomic_write_json(RESULT_PATH, failure)")
    # Set failure_raise to the result of source.index(the text 'raise', failure_write).
    failure_raise = source.index("raise\n", failure_write)
    # Require failure_write is less than failure_raise; otherwise raise AssertionError.
    assert failure_write < failure_raise
    # Require the text 'DEMONSTRATION_SAFETY_GATE_FAILED' belongs to source; otherwise raise AssertionError.
    assert "DEMONSTRATION_SAFETY_GATE_FAILED" in source


# Check demo policy loader rejects selection claim using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input demo_payload: the supplied demo payload.
# Output: no explicit value; normal completion returns None.
def test_demo_policy_loader_rejects_selection_claim(tmp_path, demo_payload):
    # Set changed to a dictionary built from demo_payload.
    changed = dict(demo_payload)
    # Set changed['best_model'] to True.
    changed["best_model"] = True
    # Set path to tmp_path joined with the path segment 'invalid.pt'.
    path = tmp_path / "invalid.pt"
    # Call torch.save with the supplied arguments.
    torch.save(changed, path)
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="METADATA_INVALID"):
        # Call load_demo_policy with the supplied arguments.
        load_demo_policy(path)


# Check completed demo artifact has learned actions and safety using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_completed_demo_artifact_has_learned_actions_and_safety():
    # Set result to the decoded data produced by json.loads from the text read from
    # Path('results/final_research_prototype_demo.json').
    result = json.loads(Path(
        # Supply encoding as the text 'utf-8'.
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    # Require result at 'status' equals the text 'DECENTRALIZED_MAPPO_RESEARCH_PROTOTYPE_DEMONSTRATED'; otherwise
    # raise AssertionError.
    assert result["status"] == \
        "DECENTRALIZED_MAPPO_RESEARCH_PROTOTYPE_DEMONSTRATED"
    # Require result['aggregate'] at 'scenario_count' equals 3; otherwise raise AssertionError.
    assert result["aggregate"]["scenario_count"] == 3
    # Require result['aggregate'] at 'learned_proposer_actions' is at least 1; otherwise raise AssertionError.
    assert result["aggregate"]["learned_proposer_actions"] >= 1
    # Require result['aggregate'] at 'learned_responder_actions' is at least 1; otherwise raise AssertionError.
    assert result["aggregate"]["learned_responder_actions"] >= 1
    # Require result['aggregate'] at 'collisions' equals 0; otherwise raise AssertionError.
    assert result["aggregate"]["collisions"] == 0
    # Require result['aggregate'] at 'blocked_zone_violations' equals 0; otherwise raise AssertionError.
    assert result["aggregate"]["blocked_zone_violations"] == 0


# Check completed demo preserves ctde and parameter boundaries using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_completed_demo_preserves_ctde_and_parameter_boundaries():
    # Set result to the decoded data produced by json.loads from the text read from
    # Path('results/final_research_prototype_demo.json').
    result = json.loads(Path(
        # Supply encoding as the text 'utf-8'.
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    # Require result at 'ctde_runtime_critic_calls' equals 0; otherwise raise AssertionError.
    assert result["ctde_runtime_critic_calls"] == 0
    # Require result at 'actor_route_truth_fields_consumed' equals 0; otherwise raise AssertionError.
    assert result["actor_route_truth_fields_consumed"] == 0
    # Require result at 'parameter_hashes_before' equals result at 'parameter_hashes_after'; otherwise raise
    # AssertionError.
    assert result["parameter_hashes_before"] == result["parameter_hashes_after"]
    # Require result at 'source_checkpoint_unchanged' is the same object as True; otherwise raise AssertionError.
    assert result["source_checkpoint_unchanged"] is True
    # Require result at 'training_operations' equals result at 'ppo_updates'; equals 0; otherwise raise
    # AssertionError.
    assert result["training_operations"] == result["ppo_updates"] == 0
    # Require result at 'validation_scenarios_used' equals 0; otherwise raise AssertionError.
    assert result["validation_scenarios_used"] == 0
    # Require result at 'held_out_scenarios_used' equals 0; otherwise raise AssertionError.
    assert result["held_out_scenarios_used"] == 0


# Check completed demo contains actual nonphysical edge interpretation using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_completed_demo_contains_actual_nonphysical_edge_interpretation():
    # Set result to the decoded data produced by json.loads from the text read from
    # Path('results/final_research_prototype_demo.json').
    result = json.loads(Path(
        # Supply encoding as the text 'utf-8'.
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    # Set structural to the next item from a lazy sequence of item for item in result at 'per_scenario_evidence';
    # retain entries satisfying item at 'structural_category' equals the text...
    structural = next(item for item in result["per_scenario_evidence"]
                      # Evaluate item at 'structural_category' equals the text
                      # 'COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION' as part of the enclosing
                      # expression.
                      if item["structural_category"] ==
                      "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION")
    # Require structural['execution'] at 'nonphysical_interpretations_observed' is at least 1; otherwise raise
    # AssertionError.
    assert structural["execution"]["nonphysical_interpretations_observed"] >= 1
    # Require structural['execution'] at 'physically_executable_outcomes' is at least 1; otherwise raise
    # AssertionError.
    assert structural["execution"]["physically_executable_outcomes"] >= 1


# Check human summary disclaims optimality using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_human_summary_disclaims_optimality():
    # Set summary to the text read from Path('results/final_research_prototype_demo_summary.md').
    summary = Path("results/final_research_prototype_demo_summary.md").read_text(
        # Supply encoding as the text 'utf-8'.
        encoding="utf-8")
    # Require the text 'not claimed to be the statistically optimal' belongs to summary; otherwise raise
    # AssertionError.
    assert "not claimed to be the statistically optimal" in summary
    # Require the text 'centralized critic was not part' belongs to summary; otherwise raise AssertionError.
    assert "centralized critic was not part" in summary
    # Require the text 'HELD_OUT remained untouched' belongs to summary; otherwise raise AssertionError.
    assert "HELD_OUT remained untouched" in summary
