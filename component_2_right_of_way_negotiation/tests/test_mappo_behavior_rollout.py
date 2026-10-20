"""Step 5J.3B.3 construction, stochasticity, replay, and artifact gates."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import MaskedCategoricalPolicy, NegotiationDecisionRole, NegotiationPolicyDecisionContext,
# PolicyDecisionProvenance from negotiation_learning.mappo_interface for the operations below.
from negotiation_learning.mappo_interface import (
    MaskedCategoricalPolicy, NegotiationDecisionRole,
    NegotiationPolicyDecisionContext, PolicyDecisionProvenance)
# Import BEHAVIOR_SOURCE, MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle,
# evaluate_policy_factor_sample, tensor_snapshot from negotiation_training for the operations below.
from negotiation_training import (
    BEHAVIOR_SOURCE, MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle,
    evaluate_policy_factor_sample, tensor_snapshot)


# Context using the inputs and processing steps below.
# Input bundle: the supplied bundle.
# Input marker: the supplied marker.
# Output: the result of NegotiationPolicyDecisionContext(the text 'B', NegotiationDecisionRole.PROPOSER, the text
# 'A', a tuple containing the text 'A',...).
def _context(bundle, marker=0.0):
    # Set provenance to the result of PolicyDecisionProvenance(the text 'LOCAL_LDM', the text 'LOCAL_GRAPH', the
    # text 'CURRENT_MPNN_OUTPUT', the text...).
    provenance = PolicyDecisionProvenance(
        "LOCAL_LDM", "LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
        "CLAIM_SCHEMA", "BOOLEAN_MASK")
    # Return the result of NegotiationPolicyDecisionContext(the text 'B', NegotiationDecisionRole.PROPOSER, the
    # text 'A', a tuple containing the text 'A',...) to the caller.
    return NegotiationPolicyDecisionContext(
        # Supply NegotiationDecisionRole.PROPOSER to NegotiationPolicyDecisionContext.
        "B", NegotiationDecisionRole.PROPOSER, "A", ("A", "B"), None,
        # Supply the result of torch.full(a tuple containing 64, marker) to NegotiationPolicyDecisionContext.
        "LOCAL_LDM", 1.0, torch.full((64,), marker), torch.zeros(64),
        # Supply a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' to
        # NegotiationPolicyDecisionContext.
        torch.zeros(34), None, ("KEEP_CLAIM", "RELINQUISH_CLAIM"),
        # Supply a tensor built from a list containing True, True to NegotiationPolicyDecisionContext.
        torch.tensor([True, True]), provenance, "RULES", "IDEAL_SAME_STEP_V2V")


# Check bundle uses contract dimensions initialization and frozen gnn using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_bundle_uses_contract_dimensions_initialization_and_frozen_gnn():
    # Set first to the result of build_mechanical_mappo_behavior_policy_bundle().
    first = build_mechanical_mappo_behavior_policy_bundle()
    # Set second to the result of build_mechanical_mappo_behavior_policy_bundle().
    second = build_mechanical_mappo_behavior_policy_bundle()
    # Require first.initial_parameter_hashes equals second.initial_parameter_hashes; otherwise raise
    # AssertionError.
    assert first.initial_parameter_hashes == second.initial_parameter_hashes
    # Require first.component_seeds equals second.component_seeds; otherwise raise AssertionError.
    assert first.component_seeds == second.component_seeds
    # Require the negation of whether any item is true in a lazy sequence of parameter.requires_grad for parameter
    # in the result of first.gnn.parameters(); otherwise raise AssertionError.
    assert not any(parameter.requires_grad for parameter in first.gnn.parameters())
    # Require first.proposer_actor.logit_head.in_features equals 162; otherwise raise AssertionError.
    assert first.proposer_actor.logit_head.in_features == 162
    # Require first.responder_actor.logit_head.in_features equals 180; otherwise raise AssertionError.
    assert first.responder_actor.logit_head.in_features == 180
    # Require first.centralized_critic.value_head.in_features equals 64; otherwise raise AssertionError.
    assert first.centralized_critic.value_head.in_features == 64


# Check masked policy accepts external reproducible generator using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_masked_policy_accepts_external_reproducible_generator():
    # Set distribution to the result of MaskedCategoricalPolicy(a tensor built from a list containing 0.1, 0.9, a
    # tensor built from a list containing True, True).
    distribution = MaskedCategoricalPolicy(
        # Supply a tensor built from a list containing True, True to MaskedCategoricalPolicy.
        torch.tensor([0.1, 0.9]), torch.tensor([True, True]))
    # Set (first, second) to a tuple containing the result of torch.Generator(), the result of torch.Generator().
    first, second = torch.Generator(), torch.Generator()
    # Call first.manual_seed with the supplied arguments.
    # Call second.manual_seed with the supplied arguments.
    first.manual_seed(725); second.manual_seed(725)
    # Require a list of the result of distribution.sample_action_index(first).item() for _ in the integer range
    # defined by 12 equals a list of the result of distribution.sample_action_index(second).item() for _ in the
    # integer range defined by 12; otherwise raise AssertionError.
    assert [distribution.sample_action_index(first).item() for _ in range(12)] == (
        # Evaluate a list of the result of distribution.sample_action_index(second).item() for _ in the integer
        # range defined by 12 as part of the enclosing expression.
        [distribution.sample_action_index(second).item() for _ in range(12)])
    # Set hard to the result of MaskedCategoricalPolicy(a tensor built from a list containing 100.0, the negative
    # of 100.0, a tensor built from a list...).
    hard = MaskedCategoricalPolicy(
        # Supply a tensor built from a list containing 100.0, the negative of 100.0 to MaskedCategoricalPolicy.
        torch.tensor([100.0, -100.0]), torch.tensor([False, True]))
    # Require the result of torch.isneginf(hard.masked_logits at 0); otherwise raise AssertionError.
    assert torch.isneginf(hard.masked_logits[0])
    # Require whether every item is true in a lazy sequence of the result of
    # hard.sample_action_index(first).item() equals 1 for _ in the integer range defined by 8; otherwise raise
    # AssertionError.
    assert all(hard.sample_action_index(first).item() == 1 for _ in range(8))


# Check real context changes distribution and snapshot is value copy using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_real_context_changes_distribution_and_snapshot_is_value_copy():
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    # Set first to the result of _context(bundle, 0.0).
    first = _context(bundle, 0.0)
    # Set second to the result of _context(bundle, 1.0).
    second = _context(bundle, 1.0)
    # Set first_probs to bundle.policy.distribution_for(first)[1].probabilities.
    first_probs = bundle.policy.distribution_for(first)[1].probabilities
    # Set second_probs to bundle.policy.distribution_for(second)[1].probabilities.
    second_probs = bundle.policy.distribution_for(second)[1].probabilities
    # Require the negation of the result of torch.equal(first_probs, second_probs); otherwise raise
    # AssertionError.
    assert not torch.equal(first_probs, second_probs)
    # Set snapshot to the result of tensor_snapshot(second).
    snapshot = tensor_snapshot(second)
    # Call second.ego_embedding.fill_ with the supplied arguments.
    second.ego_embedding.fill_(9.0)
    # Require snapshot.ego_embedding equals a tuple containing 1.0 multiplied by 64; otherwise raise
    # AssertionError.
    assert snapshot.ego_embedding == (1.0,) * 64
    # Require snapshot.hard_action_mask equals a tuple containing True, True; otherwise raise AssertionError.
    assert snapshot.hard_action_mask == (True, True)
    # Require snapshot.provenance at 'route_truth_fields' equals 0; otherwise raise AssertionError.
    assert snapshot.provenance["route_truth_fields"] == 0


# Check exact preupdate replay without resampling using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_preupdate_replay_without_resampling():
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle()
    # Set provider to the result of MAPPOBehaviorActionProvider(bundle).
    provider = MAPPOBehaviorActionProvider(bundle)
    # Set context to the result of _context(bundle).
    context = _context(bundle)
    # Set sample to the result of provider._sample(context, a tuple containing the text 'BATCH', a tuple
    # containing the text 'EPISODE', a tuple...).
    sample = provider._sample(
        # Supply a tuple containing the text 'SCENARIO' to provider._sample.
        context, ("BATCH",), ("EPISODE",), ("SCENARIO",), ("CRITIC",))
    # Set replay to the result of evaluate_policy_factor_sample(bundle.policy, sample).
    replay = evaluate_policy_factor_sample(bundle.policy, sample)
    # Require replay at 1 equals sample.behavior_policy_log_probability; otherwise raise AssertionError.
    assert replay[1] == sample.behavior_policy_log_probability
    # Require replay at 3 equals 1.0; otherwise raise AssertionError.
    assert replay[3] == 1.0
    # Require sample.behavior_policy_source equals BEHAVIOR_SOURCE; otherwise raise AssertionError.
    assert sample.behavior_policy_source == BEHAVIOR_SOURCE
    # Require sample.ppo_update_eligible; otherwise raise AssertionError.
    assert sample.ppo_update_eligible


# Check learned provider has no branch enumeration or future selection using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_learned_provider_has_no_branch_enumeration_or_future_selection():
    # Set source to the result of inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions).
    source = inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions)
    # Require the text '.enumerate(' does not belong to source; otherwise raise AssertionError.
    assert ".enumerate(" not in source
    # Require the text 'branches' does not belong to
    # inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions).parameters; otherwise raise
    # AssertionError.
    assert "branches" not in inspect.signature(
        # Supply MAPPOBehaviorActionProvider.select_joint_actions to inspect.signature.
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    # Require the text 'reward' does not belong to source and the text 'travel_time' does not belong to source;
    # otherwise raise AssertionError.
    assert "reward" not in source and "travel_time" not in source


# Check rollout artifact satisfies manifest safety and ppo boundaries using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_rollout_artifact_satisfies_manifest_safety_and_ppo_boundaries():
    # Set artifact to the result of Path(the text 'results/mappo_behavior_rollout.json').
    artifact = Path("results/mappo_behavior_rollout.json")
    # Run this branch when the negation of whether artifact exists.
    if not artifact.exists():
        # Call pytest.skip with the supplied arguments.
        pytest.skip("full rollout stopped at physical-unordered graph boundary")
    # Set result to the decoded data produced by json.load from the result of artifact.open().
    result = json.load(artifact.open(encoding="utf-8"))
    # Require result at 'status' equals the text 'REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED'; otherwise raise
    # AssertionError.
    assert result["status"] == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED"
    # Require result at 'training_manifest_passes' equals 1; otherwise raise AssertionError.
    assert result["training_manifest_passes"] == 1
    # Require result at 'training_scenarios_attempted' equals 36; otherwise raise AssertionError.
    assert result["training_scenarios_attempted"] == 36
    # Require result at 'validation_performance_runs' equals 0; otherwise raise AssertionError.
    assert result["validation_performance_runs"] == 0
    # Require result at 'held_out_performance_runs' equals 0; otherwise raise AssertionError.
    assert result["held_out_performance_runs"] == 0
    # Require result at 'responder_ppo_sample_count' is greater than 0; otherwise raise AssertionError.
    assert result["responder_ppo_sample_count"] > 0
    # Require result at 'total_ppo_sample_count' equals result at 'proposer_ppo_sample_count' plus result at
    # 'responder_ppo_sample_count'; otherwise raise AssertionError.
    assert result["total_ppo_sample_count"] == (
        # Evaluate result at 'proposer_ppo_sample_count' plus result at 'responder_ppo_sample_count' as part of
        # the enclosing expression.
        result["proposer_ppo_sample_count"] + result["responder_ppo_sample_count"])
    # Require result at 'critic_sample_count' equals result at 'joint_decision_batch_count'; otherwise raise
    # AssertionError.
    assert result["critic_sample_count"] == result["joint_decision_batch_count"]
    # Require the negation of result at 'critic_samples_duplicated_per_policy_factor'; otherwise raise
    # AssertionError.
    assert not result["critic_samples_duplicated_per_policy_factor"]
    # Require result at 'collisions' equals result at 'blocked_zone_violations'; equals 0; otherwise raise
    # AssertionError.
    assert result["collisions"] == result["blocked_zone_violations"] == 0
    # Require result at 'manual_graph_edits' equals 0; otherwise raise AssertionError.
    assert result["manual_graph_edits"] == 0
    # Require result at 'branch_enumerator_action_selections' equals 0; otherwise raise AssertionError.
    assert result["branch_enumerator_action_selections"] == 0
    # Require result at 'profiling_ppo_samples_reused' equals 0; otherwise raise AssertionError.
    assert result["profiling_ppo_samples_reused"] == 0
    # Require result at 'route_truth_actor_fields' equals 0; otherwise raise AssertionError.
    assert result["route_truth_actor_fields"] == 0
    # Require result at 'parameter_hashes_unchanged'; otherwise raise AssertionError.
    assert result["parameter_hashes_unchanged"]
    # Require whether every item is true in values from result['canonical_first_scenario_reproducibility'];
    # otherwise raise AssertionError.
    assert all(result["canonical_first_scenario_reproducibility"].values())
    # Require whether every item is true in a lazy sequence of result['policy_replay'] at name for name in a tuple
    # containing the text 'finite_log_probabilities', the text 'hard_masks_exact', the text...; otherwise raise
    # AssertionError.
    assert all(result["policy_replay"][name] for name in (
        "finite_log_probabilities", "hard_masks_exact",
        "old_current_log_probabilities_exact",
        "importance_ratios_exactly_one"))
    # Require result at 'optimizer_instances' equals 0; otherwise raise AssertionError.
    assert result["optimizer_instances"] == 0
    # Require result at 'backward_calls' equals 0; otherwise raise AssertionError.
    assert result["backward_calls"] == 0
    # Require result at 'parameter_updates' equals 0; otherwise raise AssertionError.
    assert result["parameter_updates"] == 0


# Check step 5j 3b 3 source has no optimization operations using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_step_5j_3b_3_source_has_no_optimization_operations():
    # Import negotiation_training.behavior_rollout as collector for use in this module.
    import negotiation_training.behavior_rollout as collector
    # Import negotiation_training.mappo_provider as provider for use in this module.
    import negotiation_training.mappo_provider as provider

    # Set source to the result of inspect.getsource(collector) plus the result of inspect.getsource(provider).
    source = inspect.getsource(collector) + inspect.getsource(provider)
    # Require the text 'torch.optim.Adam(' does not belong to source; otherwise raise AssertionError.
    assert "torch.optim.Adam(" not in source
    # Require the text '.backward(' does not belong to source; otherwise raise AssertionError.
    assert ".backward(" not in source
    # Require the text '.step(' does not belong to source; otherwise raise AssertionError.
    assert ".step(" not in source
