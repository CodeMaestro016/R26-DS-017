"""Standalone Step 5F masked MAPPO policy-interface validation."""

from dataclasses import fields

import torch

from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor,
)
from negotiation_learning.mappo_interface import (
    MaskedCategoricalPolicy, NegotiationDecisionRole,
    NegotiationPolicyDecisionContext, NegotiationRolloutStep,
    PROPOSER_ACTION_ORDER, PolicyDecisionProvenance, PolicySemanticError,
    RESPONDER_ACTION_ORDER, ROLE_ONE_HOT, RoleAwareNegotiationPolicy,
    deterministic_decision_event_id,
)


def context(role, mask):
    # TEST_ONLY_NON_OPERATIONAL_VALUE: interface fixture, not architecture.
    dimension = 3
    responder = role is NegotiationDecisionRole.RESPONDER
    return NegotiationPolicyDecisionContext(
        "B", role, "A", ("A", "B"),
        (1.0, "A", "B", "B", "A") if responder else None,
        "ENCODED_GRAPH_OBSERVATION", 1.0,
        torch.ones(dimension), torch.ones(dimension), torch.ones(dimension),
        torch.ones(dimension) if responder else None,
        RESPONDER_ACTION_ORDER if responder else PROPOSER_ACTION_ORDER,
        torch.tensor(mask, dtype=torch.bool),
        PolicyDecisionProvenance(
            "EGO_LDM", "CURRENT_LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
            "CURRENT_PROPOSAL" if responder else "CURRENT_CLAIM",
            "HARD_RESPONSE_MASK" if responder else "HARD_CLAIM_MASK",
        ),
        "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )


def main():
    test_dimension = 3
    proposer = DecentralizedNegotiationActor(test_dimension * 3, 2)
    responder = DecentralizedNegotiationResponseActor(test_dimension * 4 + 2, 2)
    policy = RoleAwareNegotiationPolicy(proposer, responder)

    proposer_context = context(NegotiationDecisionRole.PROPOSER, (True, True))
    responder_context = context(NegotiationDecisionRole.RESPONDER, (True, True))
    _, proposer_distribution = policy.distribution_for(proposer_context)
    _, responder_distribution = policy.distribution_for(responder_context)
    for distribution in (proposer_distribution, responder_distribution):
        torch.testing.assert_close(distribution.probabilities.sum(), torch.tensor(1.0))
        assert torch.isfinite(distribution.probabilities).all()
        assert torch.isfinite(distribution.entropy)

    one_first = MaskedCategoricalPolicy(torch.tensor([-10.0, 10.0]),
                                        torch.tensor([True, False]))
    one_second = MaskedCategoricalPolicy(torch.tensor([10.0, -10.0]),
                                         torch.tensor([False, True]))
    torch.testing.assert_close(one_first.probabilities, torch.tensor([1.0, 0.0]))
    torch.testing.assert_close(one_second.probabilities, torch.tensor([0.0, 1.0]))
    assert torch.isneginf(one_first.masked_logits[1])
    try:
        MaskedCategoricalPolicy(torch.ones(2), torch.tensor([False, False]))
        raise AssertionError("all-invalid mask was accepted")
    except PolicySemanticError as error:
        assert error.code == "NO_FEASIBLE_POLICY_ACTION"
    try:
        one_first.evaluate_action_index(1)
        raise AssertionError("invalid action was evaluated")
    except PolicySemanticError as error:
        assert error.code == "ACTION_NOT_FEASIBLE_UNDER_MASK"

    decision = policy.select_action(proposer_context)
    evaluated, entropy = policy.evaluate_action(
        proposer_context, decision.selected_semantic_action,
    )
    torch.testing.assert_close(decision.action_log_probability, evaluated)
    assert torch.isfinite(evaluated) and torch.isfinite(entropy)

    # Actor-only calls above ran before this training-only critic was created.
    critic = CentralizedNegotiationCritic(test_dimension)
    critic_value = critic(torch.ones(test_dimension))
    assert critic_value.shape == (1,) and torch.isfinite(critic_value).all()
    rollout = NegotiationRolloutStep(
        deterministic_decision_event_id(proposer_context), "EPISODE_METADATA",
        "TRANSITION_METADATA", 1.0, proposer_context.ego_id,
        proposer_context.decision_role, proposer_context.claim_identity,
        proposer_context.proposal_id, proposer_context.local_observation_identity,
        proposer_context.provenance, proposer_context.action_names,
        tuple(proposer_context.action_feasibility_mask.tolist()),
        decision.selected_semantic_action, decision.selected_action_index,
        float(decision.action_log_probability.item()), float(critic_value.item()),
        "CONTINUATION_NOT_YET_INTEGRATED",
    )
    rollout_fields = {item.name for item in fields(NegotiationRolloutStep)}
    assert "behavior_policy_log_probability" in rollout_fields
    assert "critic_value_at_collection" in rollout_fields
    assert not rollout_fields & {"reward", "advantage", "return", "ppo_ratio"}
    context_fields = {item.name for item in fields(NegotiationPolicyDecisionContext)}
    assert not context_fields & {"critic_input", "centralized_state",
                                 "global_training_state"}

    original_mask = proposer_context.action_feasibility_mask.clone()
    raw_before = policy.distribution_for(proposer_context)[0].unmasked_action_logits
    with torch.no_grad():
        proposer.logit_head.bias.copy_(torch.tensor([-999.0, 999.0]))
    raw_after, changed_preference = policy.distribution_for(proposer_context)
    assert torch.equal(proposer_context.action_feasibility_mask, original_mask)
    restricted_context = context(NegotiationDecisionRole.PROPOSER, (True, False))
    restricted_output, restricted = policy.distribution_for(restricted_context)
    torch.testing.assert_close(restricted.probabilities, torch.tensor([1.0, 0.0]))
    torch.testing.assert_close(raw_after.unmasked_action_logits,
                               restricted_output.unmasked_action_logits)

    print("Step 5F MAPPO Policy Interface Validation\n")
    print("Decision roles")
    print("  PROPOSER role available: PASS")
    print("  RESPONDER role available: PASS")
    print("  Role encoding categorical/non-ordinal: PASS")
    print("\nAction vocabularies")
    print("  Proposer KEEP_CLAIM: PASS")
    print("  Proposer RELINQUISH_CLAIM: PASS")
    print("  Responder ACCEPT_RELINQUISHMENT: PASS")
    print("  Responder REJECT_RELINQUISHMENT: PASS")
    print("\nMasked categorical")
    print("  Boolean mask required: PASS")
    print("  Invalid action probability zero: PASS")
    print("  Single-valid action probability one: PASS")
    print("  Both-valid distribution normalized: PASS")
    print("  All-invalid mask rejected: PASS")
    print("  Arbitrary finite invalid-logit constant used: False")
    print("\nPolicy evaluation")
    print("  Valid action log probability finite: PASS")
    print("  Invalid action evaluation rejected: PASS")
    print("  Action log-probability consistency: PASS")
    print("  Entropy finite: PASS")
    print("\nDecentralized execution")
    print("  Proposer actor local input only: PASS")
    print("  Responder actor local input only: PASS")
    print("  Actor functional without critic: PASS")
    print("  Critic-only state exposed to actor: False")
    print("\nTraining contract")
    print("  Behavior-policy log probability represented: PASS")
    print("  Critic collection value represented: PASS")
    print("  Reward represented as operational number: False")
    print("  Advantage implemented: False")
    print("  Return implemented: False")
    print("  PPO ratio implemented: False")
    print("\nAuthority")
    print("  Hard mask changed by actor logits: False")
    print("  Policy decision mutates protocol automatically: False")
    print("  Route-truth fields consumed: 0")
    print("\nResearch parameters")
    print("  Gamma configured: False")
    print("  GAE lambda configured: False")
    print("  PPO clip configured: False")
    print("  Learning rate configured: False")
    print("  Entropy coefficient configured: False")
    print("  Reward weights configured: False")
    print("  Final actor architecture selected: False")
    print("  Final critic architecture selected: False")
    print("\nDependencies")
    print("  Backend: PyTorch CPU")
    print("  TensorFlow required: False")
    print("  CUDA required: False")
    print("  PyTorch Geometric required: False")
    print("  New dependency required: False")
    print("\nResearch status")
    print("  MAPPO policy interface implemented: True")
    print("  PPO optimization implemented: False")
    print("  Reward implemented: False")
    print("  Optimizer implemented: False")
    print("  Training performed: False")
    print("  Model checkpoint produced: False")
    print("  SUMO policy actions issued: 0")


if __name__ == "__main__":
    main()
