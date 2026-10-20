"""Step 5F role-aware masked policy and collection-contract tests."""

# Import fields from dataclasses for the operations below.
from dataclasses import fields
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor from negotiation_learning.ctde for
# the operations below.
from negotiation_learning.ctde import (
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
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


# Set TEST_ONLY_NON_OPERATIONAL_VALUE to 3.
TEST_ONLY_NON_OPERATIONAL_VALUE = 3


# Provenance using the inputs and processing steps below.
# Input role: the supplied role.
# Output: the result of PolicyDecisionProvenance(the text 'EGO_LDM_OBSERVATION', the text 'CURRENT_LOCAL_GRAPH',
# the text 'CURRENT_MPNN_OUTPUT',...).
def provenance(role):
    # Return the result of PolicyDecisionProvenance(the text 'EGO_LDM_OBSERVATION', the text
    # 'CURRENT_LOCAL_GRAPH', the text 'CURRENT_MPNN_OUTPUT',...) to the caller.
    return PolicyDecisionProvenance(
        "EGO_LDM_OBSERVATION", "CURRENT_LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
        # Supply the text 'CURRENT_CLAIM' when role is the same object as NegotiationDecisionRole.PROPOSER,
        # otherwise the text 'CURRENT_PENDING_PROPOSAL' to PolicyDecisionProvenance.
        "CURRENT_CLAIM" if role is NegotiationDecisionRole.PROPOSER
        # Supply the text 'CURRENT_PENDING_PROPOSAL' to the enclosing expression.
        else "CURRENT_PENDING_PROPOSAL",
        # Supply the text 'HARD_CLAIM_MASK' when role is the same object as NegotiationDecisionRole.PROPOSER,
        # otherwise the text 'HARD_RESPONSE_MASK' to PolicyDecisionProvenance.
        "HARD_CLAIM_MASK" if role is NegotiationDecisionRole.PROPOSER
        # Supply the text 'HARD_RESPONSE_MASK' to the enclosing expression.
        else "HARD_RESPONSE_MASK",
    )


# Context using the inputs and processing steps below.
# Input role: the supplied role.
# Input mask: the supplied mask.
# Input ego: the ego vehicle used in this calculation.
# Input claim: the supplied claim.
# Output: the result of NegotiationPolicyDecisionContext(ego, role, claim at 0, claim, a tuple containing 1.0, the
# unpacked values from claim, ego, claim...).
def context(role, mask=(True, True), ego="B", claim=("A", "B")):
    # Set d to TEST_ONLY_NON_OPERATIONAL_VALUE.
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    # Set responder to role is the same object as NegotiationDecisionRole.RESPONDER.
    responder = role is NegotiationDecisionRole.RESPONDER
    # Return the result of NegotiationPolicyDecisionContext(ego, role, claim at 0, claim, a tuple containing 1.0,
    # the unpacked values from claim, ego, claim...) to the caller.
    return NegotiationPolicyDecisionContext(
        # Supply claim at 0 to NegotiationPolicyDecisionContext.
        ego, role, claim[0], claim,
        # Supply a tuple containing 1.0, the unpacked values from claim, ego, claim at 0 when responder, otherwise
        # None to NegotiationPolicyDecisionContext.
        (1.0, *claim, ego, claim[0]) if responder else None,
        # Supply the text 'ENCODED_GRAPH_OBSERVATION' to the enclosing expression.
        "ENCODED_GRAPH_OBSERVATION", 1.0,
        # Supply the result of torch.ones(d) to NegotiationPolicyDecisionContext.
        torch.ones(d), torch.ones(d), torch.ones(d),
        # Supply the result of torch.ones(d) when responder, otherwise None to NegotiationPolicyDecisionContext.
        torch.ones(d) if responder else None,
        # Supply RESPONDER_ACTION_ORDER when responder, otherwise PROPOSER_ACTION_ORDER to
        # NegotiationPolicyDecisionContext.
        RESPONDER_ACTION_ORDER if responder else PROPOSER_ACTION_ORDER,
        # Supply dtype as torch.bool.
        torch.tensor(mask, dtype=torch.bool), provenance(role),
        "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )


# Apply pytest.fixture as a decorator to configure the following definition.
@pytest.fixture
# Policy using the inputs and processing steps below.
# Output: the result of RoleAwareNegotiationPolicy(proposer, responder).
def policy():
    # Set d to TEST_ONLY_NON_OPERATIONAL_VALUE.
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    # Set proposer to the result of DecentralizedNegotiationActor(d multiplied by 3, 2).
    proposer = DecentralizedNegotiationActor(d * 3, 2)
    # Set responder to the result of DecentralizedNegotiationResponseActor(d multiplied by 4 plus 2, 2).
    responder = DecentralizedNegotiationResponseActor(d * 4 + 2, 2)
    # Return the result of RoleAwareNegotiationPolicy(proposer, responder) to the caller.
    return RoleAwareNegotiationPolicy(proposer, responder)


# Check roles and action vocabulary orders are exact and nonordinal using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_roles_and_action_vocabulary_orders_are_exact_and_nonordinal():
    # Require a tuple built from NegotiationDecisionRole equals a tuple containing
    # NegotiationDecisionRole.PROPOSER, NegotiationDecisionRole.RESPONDER; otherwise raise AssertionError.
    assert tuple(NegotiationDecisionRole) == (
        # Include NegotiationDecisionRole.RESPONDER in this tuple.
        NegotiationDecisionRole.PROPOSER, NegotiationDecisionRole.RESPONDER,
    )
    # Require PROPOSER_ACTION_ORDER equals a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM';
    # otherwise raise AssertionError.
    assert PROPOSER_ACTION_ORDER == ("KEEP_CLAIM", "RELINQUISH_CLAIM")
    # Require RESPONDER_ACTION_ORDER equals a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text
    # 'REJECT_RELINQUISHMENT'; otherwise raise AssertionError.
    assert RESPONDER_ACTION_ORDER == (
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT",
    )
    # Require ROLE_ONE_HOT equals a dictionary of the supplied entries; otherwise raise AssertionError.
    assert ROLE_ONE_HOT == {
        # Store a tuple containing 1.0, 0.0 under NegotiationDecisionRole.PROPOSER.
        NegotiationDecisionRole.PROPOSER: (1.0, 0.0),
        # Store a tuple containing 0.0, 1.0 under NegotiationDecisionRole.RESPONDER.
        NegotiationDecisionRole.RESPONDER: (0.0, 1.0),
    }


# Apply 'mask,expected' as a decorator to configure the following definition.
@pytest.mark.parametrize("mask,expected", (
    # Include a tuple containing a tuple containing True, False, a tuple containing 1.0, 0.0 in this tuple.
    ((True, False), (1.0, 0.0)),
    # Include a tuple containing a tuple containing False, True, a tuple containing 0.0, 1.0 in this tuple.
    ((False, True), (0.0, 1.0)),
))
# Check single valid action has exact probability using the setup, calls, and assertions below.
# Input mask: the supplied mask.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_single_valid_action_has_exact_probability(mask, expected):
    # Set distribution to the result of MaskedCategoricalPolicy(a tensor built from a list containing 1000.0, the
    # negative of 1000.0, a tensor built from mask).
    distribution = MaskedCategoricalPolicy(
        # Supply a tensor built from a list containing 1000.0, the negative of 1000.0 to MaskedCategoricalPolicy.
        torch.tensor([1000.0, -1000.0]), torch.tensor(mask),
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(distribution.probabilities, torch.tensor(expected))
    # Require the result of torch.isneginf(distribution.masked_logits[~torch.tensor(mask)]).all(); otherwise raise
    # AssertionError.
    assert torch.isneginf(distribution.masked_logits[~torch.tensor(mask)]).all()


# Check both valid is normalized finite and nonnegative using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_both_valid_is_normalized_finite_and_nonnegative():
    # Set distribution to the result of MaskedCategoricalPolicy(a tensor built from a list containing 2.0, the
    # negative of 3.0, a tensor built from a list...).
    distribution = MaskedCategoricalPolicy(
        # Supply a tensor built from a list containing True, True to MaskedCategoricalPolicy.
        torch.tensor([2.0, -3.0]), torch.tensor([True, True]),
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(distribution.probabilities.sum(), torch.tensor(1.0))
    # Require the result of torch.isfinite(distribution.probabilities).all(); otherwise raise AssertionError.
    assert torch.isfinite(distribution.probabilities).all()
    # Require the result of (distribution.probabilities >= 0).all(); otherwise raise AssertionError.
    assert (distribution.probabilities >= 0).all()
    # Require whether distribution.entropy contains finite numeric values; otherwise raise AssertionError.
    assert torch.isfinite(distribution.entropy)


# Apply 'mask' as a decorator to configure the following definition.
@pytest.mark.parametrize("mask", (
    # Include a tensor built from a list containing False, False in this tuple.
    torch.tensor([False, False]), torch.tensor([0.0, 1.0]),
))
# Check all invalid and nonboolean masks are rejected using the setup, calls, and assertions below.
# Input mask: the supplied mask.
# Output: no explicit value; normal completion returns None.
def test_all_invalid_and_nonboolean_masks_are_rejected(mask):
    # Set expected to the text 'NO_FEASIBLE_POLICY_ACTION' when mask.dtype is the same object as torch.bool,
    # otherwise the text 'BOOLEAN_ACTION_MASK_REQUIRED'.
    expected = ("NO_FEASIBLE_POLICY_ACTION" if mask.dtype is torch.bool
                # Supply the text 'BOOLEAN_ACTION_MASK_REQUIRED' to the enclosing expression.
                else "BOOLEAN_ACTION_MASK_REQUIRED")
    # Enter the result of pytest.raises(PolicySemanticError) and run the enclosed operations within that context.
    with pytest.raises(PolicySemanticError, match=expected):
        # Call MaskedCategoricalPolicy with the supplied arguments.
        MaskedCategoricalPolicy(torch.ones(2), mask)


# Check invalid action evaluation rejected and valid log probability finite using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_invalid_action_evaluation_rejected_and_valid_log_probability_finite():
    # Set distribution to the result of MaskedCategoricalPolicy(a tensor built from a list containing 1.0, 2.0, a
    # tensor built from a list containing True, False).
    distribution = MaskedCategoricalPolicy(
        # Supply a tensor built from a list containing True, False to MaskedCategoricalPolicy.
        torch.tensor([1.0, 2.0]), torch.tensor([True, False]),
    )
    # Require whether the result of distribution.evaluate_action_index(0) contains finite numeric values;
    # otherwise raise AssertionError.
    assert torch.isfinite(distribution.evaluate_action_index(0))
    # Enter the result of pytest.raises(PolicySemanticError) and run the enclosed operations within that context.
    with pytest.raises(PolicySemanticError, match="ACTION_NOT_FEASIBLE_UNDER_MASK"):
        # Call distribution.evaluate_action_index with the supplied arguments.
        distribution.evaluate_action_index(1)


# Apply pytest.mark.parametrize('role', tuple(NegotiationDecisionRole)) as a decorator to configure the following
# definition.
@pytest.mark.parametrize("role", tuple(NegotiationDecisionRole))
# Check role policy works without critic and log probability is consistent using the setup, calls, and assertions
# below.
# Input policy: the supplied policy.
# Input role: the supplied role.
# Output: no explicit value; normal completion returns None.
def test_role_policy_works_without_critic_and_log_probability_is_consistent(policy, role):
    # Set current to the result of context(role).
    current = context(role)
    # Set decision to the result of policy.select_action(current).
    decision = policy.select_action(current)
    # Set (evaluated, entropy) to the result of policy.evaluate_action(current,
    # decision.selected_semantic_action).
    evaluated, entropy = policy.evaluate_action(
        # Supply decision.selected_semantic_action to policy.evaluate_action.
        current, decision.selected_semantic_action,
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(decision.action_log_probability, evaluated)
    # Require whether evaluated contains finite numeric values and whether entropy contains finite numeric values;
    # otherwise raise AssertionError.
    assert torch.isfinite(evaluated) and torch.isfinite(entropy)
    # Require decision.action_names equals current.action_names; otherwise raise AssertionError.
    assert decision.action_names == current.action_names


# Apply pytest.mark.parametrize('role', tuple(NegotiationDecisionRole)) as a decorator to configure the following
# definition.
@pytest.mark.parametrize("role", tuple(NegotiationDecisionRole))
# Check role specific one invalid distribution using the setup, calls, and assertions below.
# Input policy: the supplied policy.
# Input role: the supplied role.
# Output: no explicit value; normal completion returns None.
def test_role_specific_one_invalid_distribution(policy, role):
    # Set (output, distribution) to the result of policy.distribution_for(the result of context(role, a tuple
    # containing False, True)).
    output, distribution = policy.distribution_for(context(role, (False, True)))
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(distribution.probabilities, torch.tensor([0.0, 1.0]))
    # Require the result of output.action_feasibility_mask.tolist() equals a list containing False, True;
    # otherwise raise AssertionError.
    assert output.action_feasibility_mask.tolist() == [False, True]


# Check actor logits cannot change hard mask or protocol state using the setup, calls, and assertions below.
# Input policy: the supplied policy.
# Output: no explicit value; normal completion returns None.
def test_actor_logits_cannot_change_hard_mask_or_protocol_state(policy):
    # Set current to the result of context(NegotiationDecisionRole.PROPOSER, a tuple containing True, False).
    current = context(NegotiationDecisionRole.PROPOSER, (True, False))
    # Set before to the result of current.action_feasibility_mask.clone().
    before = current.action_feasibility_mask.clone()
    # Enter the result of torch.no_grad() and run the enclosed operations within that context.
    with torch.no_grad():
        # Call policy.proposer_actor.logit_head.bias.copy_ with the supplied arguments.
        policy.proposer_actor.logit_head.bias.copy_(torch.tensor([-999.0, 999.0]))
    # Set (_, distribution) to the result of policy.distribution_for(current).
    _, distribution = policy.distribution_for(current)
    # Require the result of torch.equal(current.action_feasibility_mask, before); otherwise raise AssertionError.
    assert torch.equal(current.action_feasibility_mask, before)
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(distribution.probabilities, torch.tensor([1.0, 0.0]))
    # Policy context/decision schemas contain no protocol bus or mutation target.
    # Require the negation of whether any item is true in a lazy sequence of 'protocol_evaluation' in item.name or
    # 'overlay' in item.name for item in the result of fields(type(current)); otherwise raise AssertionError.
    assert not any("protocol_evaluation" in item.name or "overlay" in item.name
                   # Evaluate the result of fields(the result of type(current)) as part of the enclosing
                   # expression.
                   for item in fields(type(current)))


# Check mask changes authority without changing raw logits using the setup, calls, and assertions below.
# Input policy: the supplied policy.
# Output: no explicit value; normal completion returns None.
def test_mask_changes_authority_without_changing_raw_logits(policy):
    # Set (both_output, both) to the result of policy.distribution_for(the result of
    # context(NegotiationDecisionRole.PROPOSER, a tuple containing True, True)).
    both_output, both = policy.distribution_for(
        # Supply the result of context(NegotiationDecisionRole.PROPOSER, a tuple containing True, True) to
        # policy.distribution_for.
        context(NegotiationDecisionRole.PROPOSER, (True, True))
    )
    # Set (one_output, one) to the result of policy.distribution_for(the result of
    # context(NegotiationDecisionRole.PROPOSER, a tuple containing True, False)).
    one_output, one = policy.distribution_for(
        # Supply the result of context(NegotiationDecisionRole.PROPOSER, a tuple containing True, False) to
        # policy.distribution_for.
        context(NegotiationDecisionRole.PROPOSER, (True, False))
    )
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(both_output.unmasked_action_logits,
                               # Supply one_output.unmasked_action_logits to torch.testing.assert_close.
                               one_output.unmasked_action_logits)
    # Require both.probabilities at 1 is greater than 0; otherwise raise AssertionError.
    assert both.probabilities[1] > 0
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(one.probabilities, torch.tensor([1.0, 0.0]))


# Check deterministic identity and rollout contract has no reward number using the setup, calls, and assertions
# below.
# Input policy: the supplied policy.
# Output: no explicit value; normal completion returns None.
def test_deterministic_identity_and_rollout_contract_has_no_reward_number(policy):
    # Set current to the result of context(NegotiationDecisionRole.PROPOSER).
    current = context(NegotiationDecisionRole.PROPOSER)
    # Set decision to the result of policy.select_action(current).
    decision = policy.select_action(current)
    # Set identity to the result of deterministic_decision_event_id(current).
    identity = deterministic_decision_event_id(current)
    # Set rollout to the result of NegotiationRolloutStep(identity, the text 'EPISODE_METADATA', the text
    # 'TRANSITION_METADATA', 1.0, current.ego_id,...).
    rollout = NegotiationRolloutStep(
        # Supply identity to NegotiationRolloutStep.
        identity, "EPISODE_METADATA", "TRANSITION_METADATA", 1.0,
        # Supply current.claim_identity to NegotiationRolloutStep.
        current.ego_id, current.decision_role, current.claim_identity,
        # Supply current.local_observation_identity to NegotiationRolloutStep.
        current.proposal_id, current.local_observation_identity,
        # Supply a tuple built from current.action_names to NegotiationRolloutStep.
        current.provenance, tuple(current.action_names),
        # Supply a tuple built from the result of current.action_feasibility_mask.tolist() to
        # NegotiationRolloutStep.
        tuple(current.action_feasibility_mask.tolist()),
        # Supply decision.selected_semantic_action to NegotiationRolloutStep.
        decision.selected_semantic_action, decision.selected_action_index,
        # Supply a floating-point number built from the result of decision.action_log_probability.item() to
        # NegotiationRolloutStep.
        float(decision.action_log_probability.item()),
        # Supply 0.25 to the enclosing expression.
        0.25, "CONTINUATION_NOT_YET_INTEGRATED",
    )
    # Require rollout.behavior_policy_log_probability equals a floating-point number built from the result of
    # decision.action_log_probability.item(); otherwise raise AssertionError.
    assert rollout.behavior_policy_log_probability == float(
        # Supply the result of decision.action_log_probability.item() to float.
        decision.action_log_probability.item()
    )
    # Require rollout.critic_value_at_collection equals 0.25; otherwise raise AssertionError.
    assert rollout.critic_value_at_collection == 0.25
    # Require rollout.reward_status equals the text 'NOT_IMPLEMENTED_STEP_5F'; otherwise raise AssertionError.
    assert rollout.reward_status == "NOT_IMPLEMENTED_STEP_5F"
    # Set names to a set of item.name for item in the result of fields(NegotiationRolloutStep).
    names = {item.name for item in fields(NegotiationRolloutStep)}
    # Require the negation of names intersected with a set containing the text 'reward', the text 'advantage', the
    # text 'return', the text 'ppo_ratio', the text 'loss'; otherwise raise AssertionError.
    assert not names & {"reward", "advantage", "return", "ppo_ratio", "loss"}


# Check context has no critic global or route truth fields using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_context_has_no_critic_global_or_route_truth_fields():
    # Set names to a set of item.name for item in the result of fields(NegotiationPolicyDecisionContext).
    names = {item.name for item in fields(NegotiationPolicyDecisionContext)}
    # Set forbidden to a set containing the text 'centralized_state', the text 'critic_input', the text
    # 'global_training_state', the text...
    forbidden = {"centralized_state", "critic_input", "global_training_state",
                 "route_id", "route_index", "ground_truth_route_id",
                 "future_route", "reward", "advantage", "return"}
    # Require the negation of names intersected with forbidden; otherwise raise AssertionError.
    assert not names & forbidden


# Check step5f source excludes training control and route truth using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_step5f_source_excludes_training_control_and_route_truth():
    # Set root to Path(__file__).parents at 1 joined with the path segment 'negotiation_learning' joined with the path segment
    # 'mappo_interface'.
    root = Path(__file__).parents[1] / "negotiation_learning" / "mappo_interface"
    # Set source to the result of '\n'.join(a lazy sequence of the result of path.read_text().lower() for path in
    # the result of...).
    source = "\n".join(path.read_text().lower() for path in root.glob("*.py"))
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text
    # 'ground_truth_route_id', the text 'future_route',...
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "traci", "setspeed", "slowdown",
                 "torch.optim", "adam", "ppo_ratio", "clip_epsilon",
                 "reward = 0", "advantage =", "return =")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
    # Require the text '-1e9' does not belong to source and the text '-999999' does not belong to source;
    # otherwise raise AssertionError.
    assert "-1e9" not in source and "-999999" not in source
