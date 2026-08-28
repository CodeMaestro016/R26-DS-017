from pathlib import Path
import json

import pytest
import torch

from experimentation import ScenarioRole, build_design
from negotiation_training.demo_policy import (
    SELECTION_RULE, SOURCE_CHECKPOINT, create_demo_policy, file_sha256,
    load_demo_policy)
from negotiation_training.demo_provider import DemonstrationMAPPOActionProvider
from run_research_demo import (
    GUI_RESULT_PATH, RESULT_PATH, SCENARIO_RULE, parse_args,
    select_demo_scenarios)
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment


@pytest.fixture(scope="module")
def demo_payload(tmp_path_factory):
    path = tmp_path_factory.mktemp("demo_policy") / "demo.pt"
    return create_demo_policy(output_path=path)


def test_source_checkpoint_is_canonical_replication_zero_state_two():
    assert str(SOURCE_CHECKPOINT).replace("\\", "/") == \
        "results/mappo_extended_resume/replication_0_state_2.pt"
    source = torch.load(SOURCE_CHECKPOINT, map_location="cpu", weights_only=False)
    assert source["replication_identity"][-1] == 0
    assert source["policy_state_index"] == 2


def test_original_resume_checkpoint_is_not_mutated(tmp_path):
    before = file_sha256(SOURCE_CHECKPOINT)
    create_demo_policy(output_path=tmp_path / "demo.pt")
    assert file_sha256(SOURCE_CHECKPOINT) == before
    source = torch.load(SOURCE_CHECKPOINT, map_location="cpu", weights_only=False)
    assert source["checkpoint_type"] == "EVIDENCE_RESUME_CHECKPOINT_ONLY"
    assert source["best_model"] is False
    assert source["final_model"] is False
    assert source["selected_model"] is False
    assert source["selection_eligible"] is False


def test_demo_policy_is_provenance_selected_never_best_final_or_optimal(demo_payload):
    assert demo_payload["demo_checkpoint_selection_rule"] == SELECTION_RULE
    for field in ("performance_selected", "statistically_selected",
                  "best_model", "final_model", "optimal_model",
                  "held_out_selected"):
        assert demo_payload[field] is False


def test_demo_policy_identity_is_deterministic(tmp_path):
    first = create_demo_policy(output_path=tmp_path / "one.pt")
    second = create_demo_policy(output_path=tmp_path / "two.pt")
    assert first["demo_policy_identity"] == second["demo_policy_identity"]
    assert first["parameter_hashes"] == second["parameter_hashes"]


def test_demo_policy_contains_only_decentralized_model_states(demo_payload):
    assert "gnn_state_dict" in demo_payload
    assert "proposer_state_dict" in demo_payload
    assert "responder_state_dict" in demo_payload
    assert "critic_state_dict" not in demo_payload
    assert demo_payload["centralized_critic_included"] is False


def test_demo_provider_has_no_runtime_critic_and_preserves_hashes(demo_payload):
    provider = DemonstrationMAPPOActionProvider(demo_payload)
    assert provider.bundle.centralized_critic is None
    assert provider.runtime_critic_enabled is False
    assert provider.runtime_critic_calls == 0
    assert provider.inference_parameter_hashes() == demo_payload["parameter_hashes"]
    assert all(not parameter.requires_grad for module in (
        provider.bundle.gnn, provider.bundle.proposer_actor,
        provider.bundle.responder_actor) for parameter in module.parameters())


def test_actor_boundary_and_hard_masks_are_explicit(demo_payload):
    provider = DemonstrationMAPPOActionProvider(demo_payload)
    assert provider.actor_route_truth_fields_consumed == 0
    assert provider.ego_local_observation_used is True
    assert provider.hard_action_mask_applied is True
    assert provider.optimizer_instances == 0
    assert provider.backward_calls == 0
    assert provider.parameter_updates == 0


def test_three_scenarios_are_distinct_training_catalogue_structures():
    design = build_design()
    selected = select_demo_scenarios(design)
    ids = [item["signature"].scenario_id for item in selected]
    training = set(design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    held_out = set(design["manifests"][ScenarioRole.HELD_OUT_TEST].scenario_ids)
    assert len(selected) == len(set(ids)) == 3
    assert set(ids) <= training
    assert set(ids).isdisjoint(held_out)
    assert [item["category"] for item in selected] == [
        "REGULATORY_CYCLE_NEGOTIATION",
        "MULTI_FACTOR_MULTI_ACTION_NEGOTIATION",
        "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION"]


def test_scenario_selection_is_structural_not_performance_based():
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    selector = source[source.index("def select_demo_scenarios"):
                      source.index("def _scenario_trace")]
    assert "team_travel_time" not in selector
    assert "performance" not in SCENARIO_RULE.lower()


def test_normal_main_does_not_enable_demo_policy():
    source = Path("main.py").read_text(encoding="utf-8")
    assert "DemonstrationMAPPOActionProvider" not in source
    assert "mappo_demo_policy" not in source


def test_explicit_runner_uses_real_sumo_coupled_environment():
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    assert "DemonstrationMAPPOActionProvider" in source
    assert "CoupledNegotiationTrainingEnvironment" in source
    assert "run_episode" in source


def test_coupled_environment_defaults_to_headless():
    environment = CoupledNegotiationTrainingEnvironment(object())
    assert environment.use_gui is False


def test_research_demo_gui_cli_is_opt_in_and_uses_separate_evidence():
    assert parse_args([]).gui is False
    assert parse_args(["--gui"]).gui is True
    assert RESULT_PATH.name == "final_research_prototype_demo.json"
    assert GUI_RESULT_PATH.name == "final_research_prototype_demo_gui.json"
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    assert "DemonstrationMAPPOActionProvider(policy)" in source
    assert "provider, use_gui=use_gui" in source


def test_demo_has_no_optimizer_backward_or_parameter_update_code():
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in (
        "negotiation_training/demo_policy.py",
        "negotiation_training/demo_provider.py",
        "run_research_demo.py"))
    assert "torch.optim" not in source
    assert "optimizer.step(" not in source
    assert ".backward(" not in source
    assert "MechanicalMAPPOTrainer" not in source


def test_safety_failure_is_preserved_before_reraise():
    source = Path("run_research_demo.py").read_text(encoding="utf-8")
    failure_write = source.index("atomic_write_json(RESULT_PATH, failure)")
    failure_raise = source.index("raise\n", failure_write)
    assert failure_write < failure_raise
    assert "DEMONSTRATION_SAFETY_GATE_FAILED" in source


def test_demo_policy_loader_rejects_selection_claim(tmp_path, demo_payload):
    changed = dict(demo_payload)
    changed["best_model"] = True
    path = tmp_path / "invalid.pt"
    torch.save(changed, path)
    with pytest.raises(ValueError, match="METADATA_INVALID"):
        load_demo_policy(path)


def test_completed_demo_artifact_has_learned_actions_and_safety():
    result = json.loads(Path(
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    assert result["status"] == \
        "DECENTRALIZED_MAPPO_RESEARCH_PROTOTYPE_DEMONSTRATED"
    assert result["aggregate"]["scenario_count"] == 3
    assert result["aggregate"]["learned_proposer_actions"] >= 1
    assert result["aggregate"]["learned_responder_actions"] >= 1
    assert result["aggregate"]["collisions"] == 0
    assert result["aggregate"]["blocked_zone_violations"] == 0


def test_completed_demo_preserves_ctde_and_parameter_boundaries():
    result = json.loads(Path(
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    assert result["ctde_runtime_critic_calls"] == 0
    assert result["actor_route_truth_fields_consumed"] == 0
    assert result["parameter_hashes_before"] == result["parameter_hashes_after"]
    assert result["source_checkpoint_unchanged"] is True
    assert result["training_operations"] == result["ppo_updates"] == 0
    assert result["validation_scenarios_used"] == 0
    assert result["held_out_scenarios_used"] == 0


def test_completed_demo_contains_actual_nonphysical_edge_interpretation():
    result = json.loads(Path(
        "results/final_research_prototype_demo.json").read_text(encoding="utf-8"))
    structural = next(item for item in result["per_scenario_evidence"]
                      if item["structural_category"] ==
                      "COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION")
    assert structural["execution"]["nonphysical_interpretations_observed"] >= 1
    assert structural["execution"]["physically_executable_outcomes"] >= 1


def test_human_summary_disclaims_optimality():
    summary = Path("results/final_research_prototype_demo_summary.md").read_text(
        encoding="utf-8")
    assert "not claimed to be the statistically optimal" in summary
    assert "centralized critic was not part" in summary
    assert "HELD_OUT remained untouched" in summary
