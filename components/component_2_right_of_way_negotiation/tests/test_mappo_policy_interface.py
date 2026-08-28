"""Step 5F role-aware masked policy and collection-contract tests."""

from dataclasses import fields
from pathlib import Path

import pytest
import torch

from negotiation_learning.ctde import (
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor,
)
from negotiation_learning.mappo_interface import (
    MaskedCategoricalPolicy, NegotiationDecisionRole,
    NegotiationPolicyDecisionContext, NegotiationRolloutStep,
    PROPOSER_ACTION_ORDER, PolicyDecisionProvenance, PolicySemanticError,
    RESPONDER_ACTION_ORDER, ROLE_ONE_HOT, RoleAwareNegotiationPolicy,
    deterministic_decision_event_id,
)


TEST_ONLY_NON_OPERATIONAL_VALUE = 3


def provenance(role):
    return PolicyDecisionProvenance(
        "EGO_LDM_OBSERVATION", "CURRENT_LOCAL_GRAPH", "CURRENT_MPNN_OUTPUT",
        "CURRENT_CLAIM" if role is NegotiationDecisionRole.PROPOSER
        else "CURRENT_PENDING_PROPOSAL",
        "HARD_CLAIM_MASK" if role is NegotiationDecisionRole.PROPOSER
        else "HARD_RESPONSE_MASK",
    )


def context(role, mask=(True, True), ego="B", claim=("A", "B")):
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    responder = role is NegotiationDecisionRole.RESPONDER
    return NegotiationPolicyDecisionContext(
        ego, role, claim[0], claim,
        (1.0, *claim, ego, claim[0]) if responder else None,
        "ENCODED_GRAPH_OBSERVATION", 1.0,
        torch.ones(d), torch.ones(d), torch.ones(d),
        torch.ones(d) if responder else None,
        RESPONDER_ACTION_ORDER if responder else PROPOSER_ACTION_ORDER,
        torch.tensor(mask, dtype=torch.bool), provenance(role),
        "DE_STVO_UNCONTROLLED_4WAY_V1", "IDEAL_SAME_STEP_V2V",
    )


@pytest.fixture
def policy():
    d = TEST_ONLY_NON_OPERATIONAL_VALUE
    proposer = DecentralizedNegotiationActor(d * 3, 2)
    responder = DecentralizedNegotiationResponseActor(d * 4 + 2, 2)
    return RoleAwareNegotiationPolicy(proposer, responder)


def test_roles_and_action_vocabulary_orders_are_exact_and_nonordinal():
    assert tuple(NegotiationDecisionRole) == (
        NegotiationDecisionRole.PROPOSER, NegotiationDecisionRole.RESPONDER,
    )
    assert PROPOSER_ACTION_ORDER == ("KEEP_CLAIM", "RELINQUISH_CLAIM")
    assert RESPONDER_ACTION_ORDER == (
        "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT",
    )
    assert ROLE_ONE_HOT == {
        NegotiationDecisionRole.PROPOSER: (1.0, 0.0),
        NegotiationDecisionRole.RESPONDER: (0.0, 1.0),
    }


@pytest.mark.parametrize("mask,expected", (
    ((True, False), (1.0, 0.0)),
    ((False, True), (0.0, 1.0)),
))
def test_single_valid_action_has_exact_probability(mask, expected):
    distribution = MaskedCategoricalPolicy(
        torch.tensor([1000.0, -1000.0]), torch.tensor(mask),
    )
    torch.testing.assert_close(distribution.probabilities, torch.tensor(expected))
    assert torch.isneginf(distribution.masked_logits[~torch.tensor(mask)]).all()


def test_both_valid_is_normalized_finite_and_nonnegative():
    distribution = MaskedCategoricalPolicy(
        torch.tensor([2.0, -3.0]), torch.tensor([True, True]),
    )
    torch.testing.assert_close(distribution.probabilities.sum(), torch.tensor(1.0))
    assert torch.isfinite(distribution.probabilities).all()
    assert (distribution.probabilities >= 0).all()
    assert torch.isfinite(distribution.entropy)


@pytest.mark.parametrize("mask", (
    torch.tensor([False, False]), torch.tensor([0.0, 1.0]),
))
def test_all_invalid_and_nonboolean_masks_are_rejected(mask):
    expected = ("NO_FEASIBLE_POLICY_ACTION" if mask.dtype is torch.bool
                else "BOOLEAN_ACTION_MASK_REQUIRED")
    with pytest.raises(PolicySemanticError, match=expected):
        MaskedCategoricalPolicy(torch.ones(2), mask)


def test_invalid_action_evaluation_rejected_and_valid_log_probability_finite():
    distribution = MaskedCategoricalPolicy(
        torch.tensor([1.0, 2.0]), torch.tensor([True, False]),
    )
    assert torch.isfinite(distribution.evaluate_action_index(0))
    with pytest.raises(PolicySemanticError, match="ACTION_NOT_FEASIBLE_UNDER_MASK"):
        distribution.evaluate_action_index(1)


@pytest.mark.parametrize("role", tuple(NegotiationDecisionRole))
def test_role_policy_works_without_critic_and_log_probability_is_consistent(policy, role):
    current = context(role)
    decision = policy.select_action(current)
    evaluated, entropy = policy.evaluate_action(
        current, decision.selected_semantic_action,
    )
    torch.testing.assert_close(decision.action_log_probability, evaluated)
    assert torch.isfinite(evaluated) and torch.isfinite(entropy)
    assert decision.action_names == current.action_names


@pytest.mark.parametrize("role", tuple(NegotiationDecisionRole))
def test_role_specific_one_invalid_distribution(policy, role):
    output, distribution = policy.distribution_for(context(role, (False, True)))
    torch.testing.assert_close(distribution.probabilities, torch.tensor([0.0, 1.0]))
    assert output.action_feasibility_mask.tolist() == [False, True]


def test_actor_logits_cannot_change_hard_mask_or_protocol_state(policy):
    current = context(NegotiationDecisionRole.PROPOSER, (True, False))
    before = current.action_feasibility_mask.clone()
    with torch.no_grad():
        policy.proposer_actor.logit_head.bias.copy_(torch.tensor([-999.0, 999.0]))
    _, distribution = policy.distribution_for(current)
    assert torch.equal(current.action_feasibility_mask, before)
    torch.testing.assert_close(distribution.probabilities, torch.tensor([1.0, 0.0]))
    # Policy context/decision schemas contain no protocol bus or mutation target.
    assert not any("protocol_evaluation" in item.name or "overlay" in item.name
                   for item in fields(type(current)))


def test_mask_changes_authority_without_changing_raw_logits(policy):
    both_output, both = policy.distribution_for(
        context(NegotiationDecisionRole.PROPOSER, (True, True))
    )
    one_output, one = policy.distribution_for(
        context(NegotiationDecisionRole.PROPOSER, (True, False))
    )
    torch.testing.assert_close(both_output.unmasked_action_logits,
                               one_output.unmasked_action_logits)
    assert both.probabilities[1] > 0
    torch.testing.assert_close(one.probabilities, torch.tensor([1.0, 0.0]))


def test_deterministic_identity_and_rollout_contract_has_no_reward_number(policy):
    current = context(NegotiationDecisionRole.PROPOSER)
    decision = policy.select_action(current)
    identity = deterministic_decision_event_id(current)
    rollout = NegotiationRolloutStep(
        identity, "EPISODE_METADATA", "TRANSITION_METADATA", 1.0,
        current.ego_id, current.decision_role, current.claim_identity,
        current.proposal_id, current.local_observation_identity,
        current.provenance, tuple(current.action_names),
        tuple(current.action_feasibility_mask.tolist()),
        decision.selected_semantic_action, decision.selected_action_index,
        float(decision.action_log_probability.item()),
        0.25, "CONTINUATION_NOT_YET_INTEGRATED",
    )
    assert rollout.behavior_policy_log_probability == float(
        decision.action_log_probability.item()
    )
    assert rollout.critic_value_at_collection == 0.25
    assert rollout.reward_status == "NOT_IMPLEMENTED_STEP_5F"
    names = {item.name for item in fields(NegotiationRolloutStep)}
    assert not names & {"reward", "advantage", "return", "ppo_ratio", "loss"}


def test_context_has_no_critic_global_or_route_truth_fields():
    names = {item.name for item in fields(NegotiationPolicyDecisionContext)}
    forbidden = {"centralized_state", "critic_input", "global_training_state",
                 "route_id", "route_index", "ground_truth_route_id",
                 "future_route", "reward", "advantage", "return"}
    assert not names & forbidden


def test_step5f_source_excludes_training_control_and_route_truth():
    root = Path(__file__).parents[1] / "negotiation_learning" / "mappo_interface"
    source = "\n".join(path.read_text().lower() for path in root.glob("*.py"))
    forbidden = ("route_id", "route_index", "ground_truth_route_id",
                 "future_route", "traci", "setspeed", "slowdown",
                 "torch.optim", "adam", "ppo_ratio", "clip_epsilon",
                 "reward = 0", "advantage =", "return =")
    assert not any(item in source for item in forbidden)
    assert "-1e9" not in source and "-999999" not in source
