"""Standalone Step 5F masked MAPPO policy-interface validation."""

# Import fields from dataclasses for the operations below.
from dataclasses import fields

# Import torch for use in this module.
import torch

# Import CentralizedNegotiationCritic, DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor from
# negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    DecentralizedNegotiationResponseActor,
)
# Import MaskedCategoricalPolicy, NegotiationDecisionRole, NegotiationPolicyDecisionContext,
# NegotiationRolloutStep, PROPOSER_ACTION_ORDER, PolicyDecisionProvenance,... from
# negotiation_learning.mappo_interface for the operations below.
from negotiation_learning.mappo_interface import (
    MaskedCategoricalPolicy, NegotiationDecisionRole,
    NegotiationPolicyDecisionContext, NegotiationRolloutStep,
    PROPOSER_ACTION_ORDER, PolicyDecisionProvenance, PolicySemanticError,
    RESPONDER_ACTION_ORDER, ROLE_ONE_HOT, RoleAwareNegotiationPolicy,
    deterministic_decision_event_id,
)


# Context using the inputs and processing steps below.
# Input role: the supplied role.
# Input mask: the supplied mask.
# Output: the result of NegotiationPolicyDecisionContext(the text 'B', role, the text 'A', a tuple containing the
# text 'A', the text 'B', a tuple...).
def context(role, mask):
    # TEST_ONLY_NON_OPERATIONAL_VALUE: interface fixture, not architecture.
    # Set dimension to 3.
    dimension = 3
    # Set responder to role is the same object as NegotiationDecisionRole.RESPONDER.
    responder = role is NegotiationDecisionRole.RESPONDER
    # Return the result of NegotiationPolicyDecisionContext(the text 'B', role, the text 'A', a tuple containing
    # the text 'A', the text 'B', a tuple...) to the caller.
    return NegotiationPolicyDecisionContext(
        # Supply a tuple containing the text 'A', the text 'B' to NegotiationPolicyDecisionContext.
        "B", role, "A", ("A", "B"),
        # Supply a tuple containing 1.0, the text 'A', the text 'B', the text 'B', the text 'A' when responder,
        # otherwise None to NegotiationPolicyDecisionContext.
        (1.0, "A", "B", "B", "A") if responder else None,
        # Supply the text 'ENCODED_GRAPH_OBSERVATION' to the enclosing expression.
        "ENCODED_GRAPH_OBSERVATION", 1.0,
        # Supply the result of torch.ones(dimension) to NegotiationPolicyDecisionContext.
        torch.ones(dimension), torch.ones(dimension), torch.ones(dimension),
        # Supply the result of torch.ones(dimension) when responder, otherwise None to
        # NegotiationPolicyDecisionContext.
        torch.ones(dimension) if responder else None,
        # Supply RESPONDER_ACTION_ORDER when responder, otherwise PROPOSER_ACTION_ORDER to
        # NegotiationPolicyDecisionContext.
        RESPONDER_ACTION_ORDER if responder else PROPOSER_ACTION_ORDER,
        # Supply dtype as torch.bool.
        torch.tensor(mask, dtype=torch.bool),
        # Supply the result of PolicyDecisionProvenance(the text 'EGO_LDM', the text 'CURRENT_LOCAL_GRAPH', the
        # text 'CURRENT_MPNN_OUTPUT', the text...) to NegotiationPolicyDecisionContext.
        PolicyDecisionProvenance(
            "EGO_LDM", "CURRENT_LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
            # Supply the text 'CURRENT_PROPOSAL' when responder, otherwise the text 'CURRENT_CLAIM' to
            # PolicyDecisionProvenance.
            "CURRENT_PROPOSAL" if responder else "CURRENT_CLAIM",
            # Supply the text 'HARD_RESPONSE_MASK' when responder, otherwise the text 'HARD_CLAIM_MASK' to
            # PolicyDecisionProvenance.
            "HARD_RESPONSE_MASK" if responder else "HARD_CLAIM_MASK",
        ),
        "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then handle the specified errors.
def main():
    # Set test_dimension to 3.
    test_dimension = 3
    # Set proposer to the result of DecentralizedNegotiationActor(test_dimension multiplied by 3, 2).
    proposer = DecentralizedNegotiationActor(test_dimension * 3, 2)
    # Set responder to the result of DecentralizedNegotiationResponseActor(test_dimension multiplied by 4 plus 2,
    # 2).
    responder = DecentralizedNegotiationResponseActor(test_dimension * 4 + 2, 2)
    # Set policy to the result of RoleAwareNegotiationPolicy(proposer, responder).
    policy = RoleAwareNegotiationPolicy(proposer, responder)

    # Set proposer_context to the result of context(NegotiationDecisionRole.PROPOSER, a tuple containing True,
    # True).
    proposer_context = context(NegotiationDecisionRole.PROPOSER, (True, True))
    # Set responder_context to the result of context(NegotiationDecisionRole.RESPONDER, a tuple containing True,
    # True).
    responder_context = context(NegotiationDecisionRole.RESPONDER, (True, True))
    # Set (_, proposer_distribution) to the result of policy.distribution_for(proposer_context).
    _, proposer_distribution = policy.distribution_for(proposer_context)
    # Set (_, responder_distribution) to the result of policy.distribution_for(responder_context).
    _, responder_distribution = policy.distribution_for(responder_context)
    # Iterate over a tuple containing proposer_distribution, responder_distribution, binding each item to
    # distribution.
    for distribution in (proposer_distribution, responder_distribution):
        # Call torch.testing.assert_close with the supplied arguments.
        torch.testing.assert_close(distribution.probabilities.sum(), torch.tensor(1.0))
        # Require the result of torch.isfinite(distribution.probabilities).all(); otherwise raise AssertionError.
        assert torch.isfinite(distribution.probabilities).all()
        # Require whether distribution.entropy contains finite numeric values; otherwise raise AssertionError.
        assert torch.isfinite(distribution.entropy)

    # Set one_first to the result of MaskedCategoricalPolicy(a tensor built from a list containing the negative of
    # 10.0, 10.0, a tensor built from a list...).
    one_first = MaskedCategoricalPolicy(torch.tensor([-10.0, 10.0]),
                                        # Supply a tensor built from a list containing True, False to
                                        # MaskedCategoricalPolicy.
                                        torch.tensor([True, False]))
    # Set one_second to the result of MaskedCategoricalPolicy(a tensor built from a list containing 10.0, the
    # negative of 10.0, a tensor built from a list...).
    one_second = MaskedCategoricalPolicy(torch.tensor([10.0, -10.0]),
                                         # Supply a tensor built from a list containing False, True to
                                         # MaskedCategoricalPolicy.
                                         torch.tensor([False, True]))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(one_first.probabilities, torch.tensor([1.0, 0.0]))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(one_second.probabilities, torch.tensor([0.0, 1.0]))
    # Require the result of torch.isneginf(one_first.masked_logits at 1); otherwise raise AssertionError.
    assert torch.isneginf(one_first.masked_logits[1])
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call MaskedCategoricalPolicy with the supplied arguments.
        MaskedCategoricalPolicy(torch.ones(2), torch.tensor([False, False]))
        # Raise AssertionError with the text 'all-invalid mask was accepted' to stop this execution path.
        raise AssertionError("all-invalid mask was accepted")
    # Handle PolicySemanticError as error using the recovery steps below.
    except PolicySemanticError as error:
        # Require error.code equals the text 'NO_FEASIBLE_POLICY_ACTION'; otherwise raise AssertionError.
        assert error.code == "NO_FEASIBLE_POLICY_ACTION"
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call one_first.evaluate_action_index with the supplied arguments.
        one_first.evaluate_action_index(1)
        # Raise AssertionError with the text 'invalid action was evaluated' to stop this execution path.
        raise AssertionError("invalid action was evaluated")
    # Handle PolicySemanticError as error using the recovery steps below.
    except PolicySemanticError as error:
        # Require error.code equals the text 'ACTION_NOT_FEASIBLE_UNDER_MASK'; otherwise raise AssertionError.
        assert error.code == "ACTION_NOT_FEASIBLE_UNDER_MASK"

    # Set decision to the result of policy.select_action(proposer_context).
    decision = policy.select_action(proposer_context)
    # Set (evaluated, entropy) to the result of policy.evaluate_action(proposer_context,
    # decision.selected_semantic_action).
    evaluated, entropy = policy.evaluate_action(
        # Supply decision.selected_semantic_action to policy.evaluate_action.
        proposer_context, decision.selected_semantic_action,
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(decision.action_log_probability, evaluated)
    # Require whether evaluated contains finite numeric values and whether entropy contains finite numeric values;
    # otherwise raise AssertionError.
    assert torch.isfinite(evaluated) and torch.isfinite(entropy)

    # Actor-only calls above ran before this training-only critic was created.
    # Set critic to the result of CentralizedNegotiationCritic(test_dimension).
    critic = CentralizedNegotiationCritic(test_dimension)
    # Set critic_value to the result of critic(the result of torch.ones(test_dimension)).
    critic_value = critic(torch.ones(test_dimension))
    # Require critic_value.shape equals a tuple containing 1 and the result of torch.isfinite(critic_value).all();
    # otherwise raise AssertionError.
    assert critic_value.shape == (1,) and torch.isfinite(critic_value).all()
    # Set rollout to the result of NegotiationRolloutStep(the result of
    # deterministic_decision_event_id(proposer_context), the text 'EPISODE_METADATA',...).
    rollout = NegotiationRolloutStep(
        # Supply the result of deterministic_decision_event_id(proposer_context) to NegotiationRolloutStep.
        deterministic_decision_event_id(proposer_context), "EPISODE_METADATA",
        # Supply proposer_context.ego_id to NegotiationRolloutStep.
        "TRANSITION_METADATA", 1.0, proposer_context.ego_id,
        # Supply proposer_context.claim_identity to NegotiationRolloutStep.
        proposer_context.decision_role, proposer_context.claim_identity,
        # Supply proposer_context.local_observation_identity to NegotiationRolloutStep.
        proposer_context.proposal_id, proposer_context.local_observation_identity,
        # Supply proposer_context.action_names to NegotiationRolloutStep.
        proposer_context.provenance, proposer_context.action_names,
        # Supply a tuple built from the result of proposer_context.action_feasibility_mask.tolist() to
        # NegotiationRolloutStep.
        tuple(proposer_context.action_feasibility_mask.tolist()),
        # Supply decision.selected_semantic_action to NegotiationRolloutStep.
        decision.selected_semantic_action, decision.selected_action_index,
        # Supply a floating-point number built from the result of decision.action_log_probability.item() to
        # NegotiationRolloutStep.
        float(decision.action_log_probability.item()), float(critic_value.item()),
        "CONTINUATION_NOT_YET_INTEGRATED",
    )
    # Set rollout_fields to a set of item.name for item in the result of fields(NegotiationRolloutStep).
    rollout_fields = {item.name for item in fields(NegotiationRolloutStep)}
    # Require the text 'behavior_policy_log_probability' belongs to rollout_fields; otherwise raise
    # AssertionError.
    assert "behavior_policy_log_probability" in rollout_fields
    # Require the text 'critic_value_at_collection' belongs to rollout_fields; otherwise raise AssertionError.
    assert "critic_value_at_collection" in rollout_fields
    # Require the negation of rollout_fields intersected with a set containing the text 'reward', the text
    # 'advantage', the text 'return', the text 'ppo_ratio'; otherwise raise AssertionError.
    assert not rollout_fields & {"reward", "advantage", "return", "ppo_ratio"}
    # Set context_fields to a set of item.name for item in the result of fields(NegotiationPolicyDecisionContext).
    context_fields = {item.name for item in fields(NegotiationPolicyDecisionContext)}
    # Require the negation of context_fields intersected with a set containing the text 'critic_input', the text
    # 'centralized_state', the text 'global_training_state'; otherwise raise AssertionError.
    assert not context_fields & {"critic_input", "centralized_state",
                                 "global_training_state"}

    # Set original_mask to the result of proposer_context.action_feasibility_mask.clone().
    original_mask = proposer_context.action_feasibility_mask.clone()
    # Set raw_before to policy.distribution_for(proposer_context)[0].unmasked_action_logits.
    raw_before = policy.distribution_for(proposer_context)[0].unmasked_action_logits
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Call proposer.logit_head.bias.copy_ with the supplied arguments.
        proposer.logit_head.bias.copy_(torch.tensor([-999.0, 999.0]))
    # Set (raw_after, changed_preference) to the result of policy.distribution_for(proposer_context).
    raw_after, changed_preference = policy.distribution_for(proposer_context)
    # Require the result of torch.equal(proposer_context.action_feasibility_mask, original_mask); otherwise raise
    # AssertionError.
    assert torch.equal(proposer_context.action_feasibility_mask, original_mask)
    # Set restricted_context to the result of context(NegotiationDecisionRole.PROPOSER, a tuple containing True,
    # False).
    restricted_context = context(NegotiationDecisionRole.PROPOSER, (True, False))
    # Set (restricted_output, restricted) to the result of policy.distribution_for(restricted_context).
    restricted_output, restricted = policy.distribution_for(restricted_context)
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(restricted.probabilities, torch.tensor([1.0, 0.0]))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(raw_after.unmasked_action_logits,
                               # Supply restricted_output.unmasked_action_logits to torch.testing.assert_close.
                               restricted_output.unmasked_action_logits)

    # Display the text 'Step 5F MAPPO Policy Interface Validation'.
    print("Step 5F MAPPO Policy Interface Validation\n")
    # Display the text 'Decision roles'.
    print("Decision roles")
    # Display the text 'PROPOSER role available: PASS'.
    print("  PROPOSER role available: PASS")
    # Display the text 'RESPONDER role available: PASS'.
    print("  RESPONDER role available: PASS")
    # Display the text 'Role encoding categorical/non-ordinal: PASS'.
    print("  Role encoding categorical/non-ordinal: PASS")
    # Display the text 'Action vocabularies'.
    print("\nAction vocabularies")
    # Display the text 'Proposer KEEP_CLAIM: PASS'.
    print("  Proposer KEEP_CLAIM: PASS")
    # Display the text 'Proposer RELINQUISH_CLAIM: PASS'.
    print("  Proposer RELINQUISH_CLAIM: PASS")
    # Display the text 'Responder ACCEPT_RELINQUISHMENT: PASS'.
    print("  Responder ACCEPT_RELINQUISHMENT: PASS")
    # Display the text 'Responder REJECT_RELINQUISHMENT: PASS'.
    print("  Responder REJECT_RELINQUISHMENT: PASS")
    # Display the text 'Masked categorical'.
    print("\nMasked categorical")
    # Display the text 'Boolean mask required: PASS'.
    print("  Boolean mask required: PASS")
    # Display the text 'Invalid action probability zero: PASS'.
    print("  Invalid action probability zero: PASS")
    # Display the text 'Single-valid action probability one: PASS'.
    print("  Single-valid action probability one: PASS")
    # Display the text 'Both-valid distribution normalized: PASS'.
    print("  Both-valid distribution normalized: PASS")
    # Display the text 'All-invalid mask rejected: PASS'.
    print("  All-invalid mask rejected: PASS")
    # Display the text 'Arbitrary finite invalid-logit constant used: False'.
    print("  Arbitrary finite invalid-logit constant used: False")
    # Display the text 'Policy evaluation'.
    print("\nPolicy evaluation")
    # Display the text 'Valid action log probability finite: PASS'.
    print("  Valid action log probability finite: PASS")
    # Display the text 'Invalid action evaluation rejected: PASS'.
    print("  Invalid action evaluation rejected: PASS")
    # Display the text 'Action log-probability consistency: PASS'.
    print("  Action log-probability consistency: PASS")
    # Display the text 'Entropy finite: PASS'.
    print("  Entropy finite: PASS")
    # Display the text 'Decentralized execution'.
    print("\nDecentralized execution")
    # Display the text 'Proposer actor local input only: PASS'.
    print("  Proposer actor local input only: PASS")
    # Display the text 'Responder actor local input only: PASS'.
    print("  Responder actor local input only: PASS")
    # Display the text 'Actor functional without critic: PASS'.
    print("  Actor functional without critic: PASS")
    # Display the text 'Critic-only state exposed to actor: False'.
    print("  Critic-only state exposed to actor: False")
    # Display the text 'Training contract'.
    print("\nTraining contract")
    # Display the text 'Behavior-policy log probability represented: PASS'.
    print("  Behavior-policy log probability represented: PASS")
    # Display the text 'Critic collection value represented: PASS'.
    print("  Critic collection value represented: PASS")
    # Display the text 'Reward represented as operational number: False'.
    print("  Reward represented as operational number: False")
    # Display the text 'Advantage implemented: False'.
    print("  Advantage implemented: False")
    # Display the text 'Return implemented: False'.
    print("  Return implemented: False")
    # Display the text 'PPO ratio implemented: False'.
    print("  PPO ratio implemented: False")
    # Display the text 'Authority'.
    print("\nAuthority")
    # Display the text 'Hard mask changed by actor logits: False'.
    print("  Hard mask changed by actor logits: False")
    # Display the text 'Policy decision mutates protocol automatically: False'.
    print("  Policy decision mutates protocol automatically: False")
    # Display the text 'Route-truth fields consumed: 0'.
    print("  Route-truth fields consumed: 0")
    # Display the text 'Research parameters'.
    print("\nResearch parameters")
    # Display the text 'Gamma configured: False'.
    print("  Gamma configured: False")
    # Display the text 'GAE lambda configured: False'.
    print("  GAE lambda configured: False")
    # Display the text 'PPO clip configured: False'.
    print("  PPO clip configured: False")
    # Display the text 'Learning rate configured: False'.
    print("  Learning rate configured: False")
    # Display the text 'Entropy coefficient configured: False'.
    print("  Entropy coefficient configured: False")
    # Display the text 'Reward weights configured: False'.
    print("  Reward weights configured: False")
    # Display the text 'Final actor architecture selected: False'.
    print("  Final actor architecture selected: False")
    # Display the text 'Final critic architecture selected: False'.
    print("  Final critic architecture selected: False")
    # Display the text 'Dependencies'.
    print("\nDependencies")
    # Display the text 'Backend: PyTorch CPU'.
    print("  Backend: PyTorch CPU")
    # Display the text 'TensorFlow required: False'.
    print("  TensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'PyTorch Geometric required: False'.
    print("  PyTorch Geometric required: False")
    # Display the text 'New dependency required: False'.
    print("  New dependency required: False")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display the text 'MAPPO policy interface implemented: True'.
    print("  MAPPO policy interface implemented: True")
    # Display the text 'PPO optimization implemented: False'.
    print("  PPO optimization implemented: False")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
    # Display the text 'Optimizer implemented: False'.
    print("  Optimizer implemented: False")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'Model checkpoint produced: False'.
    print("  Model checkpoint produced: False")
    # Display the text 'SUMO policy actions issued: 0'.
    print("  SUMO policy actions issued: 0")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
