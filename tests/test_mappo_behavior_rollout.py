"""Step 5J.3B.3 construction, stochasticity, replay, and artifact gates."""

import inspect
import json
from pathlib import Path

import pytest
import torch

from negotiation_learning.mappo_interface import (
    MaskedCategoricalPolicy, NegotiationDecisionRole,
    NegotiationPolicyDecisionContext, PolicyDecisionProvenance)
from negotiation_training import (
    BEHAVIOR_SOURCE, MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle,
    evaluate_policy_factor_sample, tensor_snapshot)


def _context(bundle, marker=0.0):
    provenance = PolicyDecisionProvenance(
        "LOCAL_LDM", "LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
        "CLAIM_SCHEMA", "BOOLEAN_MASK")
    return NegotiationPolicyDecisionContext(
        "B", NegotiationDecisionRole.PROPOSER, "A", ("A", "B"), None,
        "LOCAL_LDM", 1.0, torch.full((64,), marker), torch.zeros(64),
        torch.zeros(34), None, ("KEEP_CLAIM", "RELINQUISH_CLAIM"),
        torch.tensor([True, True]), provenance, "RULES", "IDEAL_SAME_STEP_V2V")


def test_bundle_uses_contract_dimensions_initialization_and_frozen_gnn():
    first = build_mechanical_mappo_behavior_policy_bundle()
    second = build_mechanical_mappo_behavior_policy_bundle()
    assert first.initial_parameter_hashes == second.initial_parameter_hashes
    assert first.component_seeds == second.component_seeds
    assert not any(parameter.requires_grad for parameter in first.gnn.parameters())
    assert first.proposer_actor.logit_head.in_features == 162
    assert first.responder_actor.logit_head.in_features == 180
    assert first.centralized_critic.value_head.in_features == 64


def test_masked_policy_accepts_external_reproducible_generator():
    distribution = MaskedCategoricalPolicy(
        torch.tensor([0.1, 0.9]), torch.tensor([True, True]))
    first, second = torch.Generator(), torch.Generator()
    first.manual_seed(725); second.manual_seed(725)
    assert [distribution.sample_action_index(first).item() for _ in range(12)] == (
        [distribution.sample_action_index(second).item() for _ in range(12)])
    hard = MaskedCategoricalPolicy(
        torch.tensor([100.0, -100.0]), torch.tensor([False, True]))
    assert torch.isneginf(hard.masked_logits[0])
    assert all(hard.sample_action_index(first).item() == 1 for _ in range(8))


def test_real_context_changes_distribution_and_snapshot_is_value_copy():
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    first = _context(bundle, 0.0)
    second = _context(bundle, 1.0)
    first_probs = bundle.policy.distribution_for(first)[1].probabilities
    second_probs = bundle.policy.distribution_for(second)[1].probabilities
    assert not torch.equal(first_probs, second_probs)
    snapshot = tensor_snapshot(second)
    second.ego_embedding.fill_(9.0)
    assert snapshot.ego_embedding == (1.0,) * 64
    assert snapshot.hard_action_mask == (True, True)
    assert snapshot.provenance["route_truth_fields"] == 0


def test_exact_preupdate_replay_without_resampling():
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    provider = MAPPOBehaviorActionProvider(bundle)
    context = _context(bundle)
    sample = provider._sample(
        context, ("BATCH",), ("EPISODE",), ("SCENARIO",), ("CRITIC",))
    replay = evaluate_policy_factor_sample(bundle.policy, sample)
    assert replay[1] == sample.behavior_policy_log_probability
    assert replay[3] == 1.0
    assert sample.behavior_policy_source == BEHAVIOR_SOURCE
    assert sample.ppo_update_eligible


def test_learned_provider_has_no_branch_enumeration_or_future_selection():
    source = inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions)
    assert ".enumerate(" not in source
    assert "branches" not in inspect.signature(
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    assert "reward" not in source and "travel_time" not in source


def test_rollout_artifact_satisfies_manifest_safety_and_ppo_boundaries():
    artifact = Path("results/mappo_behavior_rollout.json")
    if not artifact.exists():
        pytest.skip("full rollout stopped at physical-unordered graph boundary")
    result = json.load(artifact.open(encoding="utf-8"))
    assert result["status"] == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED"
    assert result["training_manifest_passes"] == 1
    assert result["training_scenarios_attempted"] == 36
    assert result["validation_performance_runs"] == 0
    assert result["held_out_performance_runs"] == 0
    assert result["responder_ppo_sample_count"] > 0
    assert result["total_ppo_sample_count"] == (
        result["proposer_ppo_sample_count"] + result["responder_ppo_sample_count"])
    assert result["critic_sample_count"] == result["joint_decision_batch_count"]
    assert not result["critic_samples_duplicated_per_policy_factor"]
    assert result["collisions"] == result["blocked_zone_violations"] == 0
    assert result["manual_graph_edits"] == 0
    assert result["branch_enumerator_action_selections"] == 0
    assert result["profiling_ppo_samples_reused"] == 0
    assert result["route_truth_actor_fields"] == 0
    assert result["parameter_hashes_unchanged"]
    assert all(result["canonical_first_scenario_reproducibility"].values())
    assert all(result["policy_replay"][name] for name in (
        "finite_log_probabilities", "hard_masks_exact",
        "old_current_log_probabilities_exact",
        "importance_ratios_exactly_one"))
    assert result["optimizer_instances"] == 0
    assert result["backward_calls"] == 0
    assert result["parameter_updates"] == 0


def test_step_5j_3b_3_source_has_no_optimization_operations():
    import negotiation_training.behavior_rollout as collector
    import negotiation_training.mappo_provider as provider

    source = inspect.getsource(collector) + inspect.getsource(provider)
    assert "torch.optim.Adam(" not in source
    assert ".backward(" not in source
    assert ".step(" not in source
