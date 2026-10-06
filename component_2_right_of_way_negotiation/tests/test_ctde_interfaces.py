"""Step 5E claim semantics and untrained CTDE interface tests."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from negotiation_learning import (
    InfeasibilityReason, NegotiationClaimBuilder, NegotiationStatus,
    PolicyAuthority,
)
from negotiation_learning.ctde import (
    ActorForwardInput, ActorInputProvenance, CentralizedCriticInputBuilder,
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


TEST_ONLY_NON_OPERATIONAL_VALUE = 5


def edge(yielding, priority, probability=None):
    result = {
        "yielding_vehicle_id": yielding,
        "priority_vehicle_id": priority,
        "applicable_rule_ids": ("RULE",),
        "source_sections": ("SECTION",),
        "shared_conflict_zone_ids": ("ZONE",),
        "timestamp": 1.0,
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    if probability is not None:
        result["intention_weighted_conflict_probability"] = probability
    return result


def claims(ego, edges, status=NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
           permitted=True, consistent=True):
    return NegotiationClaimBuilder().build(
        ego, {"joint_precedence_edges": tuple(edges)}, status.value,
        permitted, consistent,
    )


def claim_pairs(result):
    return {(item.yielding_vehicle_id, item.priority_vehicle_id)
            for item in result.ego_precedence_claims}


def obligation_pairs(result):
    return {(item.yielding_vehicle_id, item.priority_vehicle_id)
            for item in result.mandatory_yield_obligations}


def test_simple_precedence_ownership_and_no_dummy_claim():
    a = claims("A", (edge("A", "B"),))
    b = claims("B", (edge("A", "B"),))
    assert obligation_pairs(a) == {("A", "B")}
    assert claim_pairs(a) == set() and a.action_candidates == ()
    assert claim_pairs(b) == {("A", "B")}
    assert obligation_pairs(b) == set()


def test_four_way_cycle_keeps_separate_obligation_and_claim_for_every_ego():
    cycle = tuple(edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    expected = {
        "A": ({("A", "B")}, {("D", "A")}),
        "B": ({("B", "C")}, {("A", "B")}),
        "C": ({("C", "D")}, {("B", "C")}),
        "D": ({("D", "A")}, {("C", "D")}),
    }
    for ego, (obligations, owned_claims) in expected.items():
        result = claims(ego, cycle)
        assert obligation_pairs(result) == obligations
        assert claim_pairs(result) == owned_claims
        assert result.action_masks[0].feasibility == (True, True)


def test_multiple_incoming_claims_are_distinct_and_claim_targeted():
    result = claims("B", (edge("A", "B"), edge("C", "B")))
    assert claim_pairs(result) == {("A", "B"), ("C", "B")}
    assert len(result.action_masks) == 2
    assert {(item.counterparty_id, item.action_name.value)
            for item in result.action_candidates} == {
                ("A", "KEEP_CLAIM"), ("A", "RELINQUISH_CLAIM"),
                ("C", "KEEP_CLAIM"), ("C", "RELINQUISH_CLAIM"),
            }


@pytest.mark.parametrize("count", (0, 1, 2, 3))
def test_variable_claim_count_has_no_padding_or_maximum(count):
    result = claims("E", tuple(edge(f"C{i}", "E") for i in range(count)))
    assert len(result.ego_precedence_claims) == count
    assert len(result.action_masks) == count


def test_claim_order_and_mask_are_deterministic_and_invariant():
    edges = (edge("C", "B"), edge("A", "B"))
    first, second = claims("B", edges), claims("B", tuple(reversed(edges)))
    key = lambda result: tuple(
        (mask.claim.counterparty_id, mask.feasibility,
         tuple(reason.value if reason else None
               for reason in mask.infeasibility_reasons))
        for mask in result.action_masks
    )
    assert key(first) == key(second)
    assert all(type(value) is bool for mask in first.action_masks
               for value in mask.feasibility)


@pytest.mark.parametrize("status,reason", (
    (NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH,
     InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH),
    (NegotiationStatus.REGULATORY_PROFILE_MISMATCH,
     InfeasibilityReason.REGULATORY_PROFILE_MISMATCH),
    (NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
     InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT),
    (NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED,
     InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED),
))
def test_regulatory_uncertainty_blocks_policy_authority(status, reason):
    result = claims("B", (edge("A", "B"),), status=status)
    assert result.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    assert result.policy_authority_reason is reason
    assert result.action_masks[0].feasibility == (False, False)


def test_resolved_law_does_not_invoke_policy_and_permission_is_explicit():
    resolved = claims("B", (edge("A", "B"),),
                      NegotiationStatus.REGULATORY_ORDER_RESOLVED)
    denied = claims("B", (edge("A", "B"),), permitted=False)
    assert resolved.policy_authority is PolicyAuthority.POLICY_NOT_REQUIRED
    assert denied.policy_authority_reason is (
        InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED
    )


def test_prediction_probability_cannot_change_hard_mask():
    low, high = edge("A", "B", 0.01), edge("A", "B", 0.99)
    assert claims("B", (low,)).action_masks == claims("B", (high,)).action_masks


def provenance():
    return ActorInputProvenance(
        "EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH", "CURRENT_MPNN_ENCODING",
        "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
    )


def test_actor_outputs_only_claim_logits_and_works_without_critic():
    node_values = np.zeros((1, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    node_masks = np.ones_like(node_values, dtype=np.bool_)
    encoded = EncodedGraphObservation(
        "A", ("A",), node_values, node_masks,
        np.empty((2, 0), dtype=np.int64),
        np.empty((0, len(EDGE_NUMERIC_SCHEMA)), dtype=np.float32),
        np.empty((0, len(EDGE_NUMERIC_SCHEMA)), dtype=np.bool_),
        NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )
    mpnn = EdgeAwareMPNNEncoder(
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        TEST_ONLY_NON_OPERATIONAL_VALUE, 1,
    )
    mpnn_output = mpnn(to_torch_graph(encoded))
    actor = DecentralizedNegotiationActor(
        input_dim=3 * TEST_ONLY_NON_OPERATIONAL_VALUE, action_count=2,
    )
    actor_input = ActorForwardInput(
        "A", "B", mpnn_output.ego_embedding, mpnn_output.graph_embedding,
        torch.ones(TEST_ONLY_NON_OPERATIONAL_VALUE),
        torch.tensor([True, False]), provenance(),
    )
    output = actor(actor_input)
    assert output.unmasked_action_logits.shape == (2,)
    assert output.action_feasibility_mask.dtype is torch.bool
    assert output.masked_action_distribution_inputs == (
        output.unmasked_action_logits, output.action_feasibility_mask,
    )
    assert not hasattr(actor_input, "centralized_critic_input")


@pytest.mark.parametrize("agents", (1, 2, 4))
def test_critic_variable_agent_count_scalar_finite_value(agents):
    representations = torch.arange(
        agents * TEST_ONLY_NON_OPERATIONAL_VALUE, dtype=torch.float32,
    ).reshape(agents, TEST_ONLY_NON_OPERATIONAL_VALUE)
    joint = CentralizedCriticInputBuilder.build(representations)
    value = CentralizedNegotiationCritic(TEST_ONLY_NON_OPERATIONAL_VALUE)(joint)
    assert joint.shape == (TEST_ONLY_NON_OPERATIONAL_VALUE,)
    assert value.shape == (1,) and torch.isfinite(value).all()


def test_critic_sum_is_permutation_invariant():
    representations = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    first = CentralizedCriticInputBuilder.build(representations)
    second = CentralizedCriticInputBuilder.build(representations[[2, 0, 1]])
    torch.testing.assert_close(first, second)


def test_actor_and_critic_contracts_exclude_route_truth_and_control():
    root = Path(__file__).parents[1]
    sources = "\n".join((root / "negotiation_learning" / "ctde" / name).read_text()
                         for name in ("interfaces.py", "__init__.py")).lower()
    forbidden = ("route_id", "route_index", "ground_truth", "future_route",
                 "traci", "setspeed", "slowdown", "setacceleration", "reward")
    assert not any(item in sources for item in forbidden)


def test_no_operational_hyperparameters_optimizer_or_mask_magnitude():
    root = Path(__file__).parents[1]
    paths = (root / "negotiation_learning" / "claim_semantics.py",
             root / "negotiation_learning" / "ctde" / "interfaces.py")
    source = "\n".join(path.read_text().lower() for path in paths)
    forbidden = ("-1e9", "adam", "adamw", "sgd", "learning_rate", "gamma =",
                 "gae", "clip_epsilon", "softmax(", "categorical(")
    assert not any(item in source for item in forbidden)
