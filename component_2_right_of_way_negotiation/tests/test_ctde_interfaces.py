"""Step 5E claim semantics and untrained CTDE interface tests."""

# Import deepcopy from copy for the operations below.
from copy import deepcopy
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np
# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import InfeasibilityReason, NegotiationClaimBuilder, NegotiationStatus, PolicyAuthority from
# negotiation_learning for the operations below.
from negotiation_learning import (
    InfeasibilityReason, NegotiationClaimBuilder, NegotiationStatus,
    PolicyAuthority,
)
# Import ActorForwardInput, ActorInputProvenance, CentralizedCriticInputBuilder, CentralizedNegotiationCritic,
# DecentralizedNegotiationActor from negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    ActorForwardInput, ActorInputProvenance, CentralizedCriticInputBuilder,
    CentralizedNegotiationCritic, DecentralizedNegotiationActor,
)
# Import EdgeAwareMPNNEncoder, to_torch_graph from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
# Import EncodedGraphObservation from negotiation_learning.tensor_encoding.models for the operations below.
from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
# Import CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA from
# negotiation_learning.tensor_encoding.schemas for the operations below.
from negotiation_learning.tensor_encoding.schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
)


# Set TEST_ONLY_NON_OPERATIONAL_VALUE to 5.
TEST_ONLY_NON_OPERATIONAL_VALUE = 5


# Edge using the inputs and processing steps below.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Input probability: the supplied probability.
# Output: result.
# Processing: select branches using the stated conditions.
def edge(yielding, priority, probability=None):
    # Set result to a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
    # source_sections,...
    result = {
        # Store yielding under 'yielding_vehicle_id'.
        "yielding_vehicle_id": yielding,
        # Store priority under 'priority_vehicle_id'.
        "priority_vehicle_id": priority,
        # Store a tuple containing the text 'RULE' under 'applicable_rule_ids'.
        "applicable_rule_ids": ("RULE",),
        # Store a tuple containing the text 'SECTION' under 'source_sections'.
        "source_sections": ("SECTION",),
        # Store a tuple containing the text 'ZONE' under 'shared_conflict_zone_ids'.
        "shared_conflict_zone_ids": ("ZONE",),
        # Store 1.0 under 'timestamp'.
        "timestamp": 1.0,
        # Store a dictionary containing mandatory_regulatory_yield under 'hard_constraint_evidence'.
        # Store True under 'mandatory_regulatory_yield'.
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }
    # Run this branch when probability is a different object from None.
    if probability is not None:
        # Set result['intention_weighted_conflict_probability'] to probability.
        result["intention_weighted_conflict_probability"] = probability
    # Return result to the caller.
    return result


# Claims using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input edges: the supplied edges.
# Input status: the supplied status.
# Input permitted: the supplied permitted.
# Input consistent: the supplied consistent.
# Output: the result of NegotiationClaimBuilder().build(ego, a dictionary containing joint_precedence_edges,
# status.value, permitted, consistent).
def claims(ego, edges, status=NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
           # Declare permitted, consistent as input parameters.
           permitted=True, consistent=True):
    # Return the result of NegotiationClaimBuilder().build(ego, a dictionary containing joint_precedence_edges,
    # status.value, permitted, consistent) to the caller.
    return NegotiationClaimBuilder().build(
        # Store a tuple built from edges under 'joint_precedence_edges'.
        ego, {"joint_precedence_edges": tuple(edges)}, status.value,
        # Supply consistent to NegotiationClaimBuilder().build.
        permitted, consistent,
    )


# Claim pairs using the inputs and processing steps below.
# Input result: the supplied result.
# Output: a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in
# result.ego_precedence_claims.
def claim_pairs(result):
    # Return a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in
    # result.ego_precedence_claims to the caller.
    return {(item.yielding_vehicle_id, item.priority_vehicle_id)
            # Evaluate result.ego_precedence_claims as part of the enclosing expression.
            for item in result.ego_precedence_claims}


# Obligation pairs using the inputs and processing steps below.
# Input result: the supplied result.
# Output: a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in
# result.mandatory_yield_obligations.
def obligation_pairs(result):
    # Return a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in
    # result.mandatory_yield_obligations to the caller.
    return {(item.yielding_vehicle_id, item.priority_vehicle_id)
            # Evaluate result.mandatory_yield_obligations as part of the enclosing expression.
            for item in result.mandatory_yield_obligations}


# Check simple precedence ownership and no dummy claim using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_simple_precedence_ownership_and_no_dummy_claim():
    # Set a to the result of claims(the text 'A', a tuple containing the result of edge(the text 'A', the text
    # 'B')).
    a = claims("A", (edge("A", "B"),))
    # Set b to the result of claims(the text 'B', a tuple containing the result of edge(the text 'A', the text
    # 'B')).
    b = claims("B", (edge("A", "B"),))
    # Require the result of obligation_pairs(a) equals a set containing a tuple containing the text 'A', the text
    # 'B'; otherwise raise AssertionError.
    assert obligation_pairs(a) == {("A", "B")}
    # Require the result of claim_pairs(a) equals an empty set and a.action_candidates equals an empty tuple;
    # otherwise raise AssertionError.
    assert claim_pairs(a) == set() and a.action_candidates == ()
    # Require the result of claim_pairs(b) equals a set containing a tuple containing the text 'A', the text 'B';
    # otherwise raise AssertionError.
    assert claim_pairs(b) == {("A", "B")}
    # Require the result of obligation_pairs(b) equals an empty set; otherwise raise AssertionError.
    assert obligation_pairs(b) == set()


# Check four way cycle keeps separate obligation and claim for every ego using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_four_way_cycle_keeps_separate_obligation_and_claim_for_every_ego():
    # Set cycle to a tuple built from a lazy sequence of the result of edge(a, b) for (a, b) in a tuple containing
    # a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple containing...
    cycle = tuple(edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Set expected to a dictionary containing A, B, C, D.
    expected = {
        # Store a tuple containing a set containing a tuple containing the text 'A', the text 'B', a set
        # containing a tuple containing the... under 'A'.
        "A": ({("A", "B")}, {("D", "A")}),
        # Store a tuple containing a set containing a tuple containing the text 'B', the text 'C', a set
        # containing a tuple containing the... under 'B'.
        "B": ({("B", "C")}, {("A", "B")}),
        # Store a tuple containing a set containing a tuple containing the text 'C', the text 'D', a set
        # containing a tuple containing the... under 'C'.
        "C": ({("C", "D")}, {("B", "C")}),
        # Store a tuple containing a set containing a tuple containing the text 'D', the text 'A', a set
        # containing a tuple containing the... under 'D'.
        "D": ({("D", "A")}, {("C", "D")}),
    }
    # Iterate over key/value pairs from expected, binding each item to (ego, (obligations, owned_claims)).
    for ego, (obligations, owned_claims) in expected.items():
        # Set result to the result of claims(ego, cycle).
        result = claims(ego, cycle)
        # Require the result of obligation_pairs(result) equals obligations; otherwise raise AssertionError.
        assert obligation_pairs(result) == obligations
        # Require the result of claim_pairs(result) equals owned_claims; otherwise raise AssertionError.
        assert claim_pairs(result) == owned_claims
        # Require result.action_masks[0].feasibility equals a tuple containing True, True; otherwise raise
        # AssertionError.
        assert result.action_masks[0].feasibility == (True, True)


# Check multiple incoming claims are distinct and claim targeted using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_multiple_incoming_claims_are_distinct_and_claim_targeted():
    # Set result to the result of claims(the text 'B', a tuple containing the result of edge(the text 'A', the
    # text 'B'), the result of...).
    result = claims("B", (edge("A", "B"), edge("C", "B")))
    # Require the result of claim_pairs(result) equals a set containing a tuple containing the text 'A', the text
    # 'B', a tuple containing the text 'C', the text 'B'; otherwise raise AssertionError.
    assert claim_pairs(result) == {("A", "B"), ("C", "B")}
    # Require the number of entries in result.action_masks equals 2; otherwise raise AssertionError.
    assert len(result.action_masks) == 2
    # Require a set of a tuple containing item.counterparty_id, item.action_name.value for item in
    # result.action_candidates equals a set containing a tuple containing the text 'A', the text 'KEEP_CLAIM', a
    # tuple containing the text 'A', the text...; otherwise raise AssertionError.
    assert {(item.counterparty_id, item.action_name.value)
            # Evaluate a set containing a tuple containing the text 'A', the text 'KEEP_CLAIM', a tuple containing
            # the text 'A', the text... as part of the enclosing expression.
            for item in result.action_candidates} == {
                # Include a tuple containing the text 'A', the text 'RELINQUISH_CLAIM' in this set.
                ("A", "KEEP_CLAIM"), ("A", "RELINQUISH_CLAIM"),
                # Include a tuple containing the text 'C', the text 'RELINQUISH_CLAIM' in this set.
                ("C", "KEEP_CLAIM"), ("C", "RELINQUISH_CLAIM"),
            }


# Apply pytest.mark.parametrize('count', (0, 1, 2, 3)) as a decorator to configure the following definition.
@pytest.mark.parametrize("count", (0, 1, 2, 3))
# Check variable claim count has no padding or maximum using the setup, calls, and assertions below.
# Input count: the supplied count.
# Output: no explicit value; normal completion returns None.
def test_variable_claim_count_has_no_padding_or_maximum(count):
    # Set result to the result of claims(the text 'E', a tuple built from a lazy sequence of the result of
    # edge(f'C{i}', 'E') for i in...).
    result = claims("E", tuple(edge(f"C{i}", "E") for i in range(count)))
    # Require the number of entries in result.ego_precedence_claims equals count; otherwise raise AssertionError.
    assert len(result.ego_precedence_claims) == count
    # Require the number of entries in result.action_masks equals count; otherwise raise AssertionError.
    assert len(result.action_masks) == count


# Check claim order and mask are deterministic and invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_claim_order_and_mask_are_deterministic_and_invariant():
    # Set edges to a tuple containing the result of edge(the text 'C', the text 'B'), the result of edge(the text
    # 'A', the text 'B').
    edges = (edge("C", "B"), edge("A", "B"))
    # Set (first, second) to a tuple containing the result of claims(the text 'B', edges), the result of
    # claims(the text 'B', a tuple built from the...
    first, second = claims("B", edges), claims("B", tuple(reversed(edges)))
    # Set key to a callback that returns a tuple built from a lazy sequence of a tuple containing
    # mask.claim.counterparty_id, mask.feasibility, tuple((reason.value if reason else None for reason in... for
    # mask in result.action_masks.
    key = lambda result: tuple(
        # Evaluate a tuple containing mask.claim.counterparty_id, mask.feasibility, a tuple built from a lazy
        # sequence of reason.value when... as part of the enclosing expression.
        (mask.claim.counterparty_id, mask.feasibility,
         # Include a tuple built from a lazy sequence of reason.value when reason, otherwise None for reason in
         # mask.infeasibility_reasons in this tuple.
         tuple(reason.value if reason else None
               # Evaluate mask.infeasibility_reasons as part of the enclosing expression.
               for reason in mask.infeasibility_reasons))
        # Evaluate result.action_masks as part of the enclosing expression.
        for mask in result.action_masks
    )
    # Require the result of key(first) equals the result of key(second); otherwise raise AssertionError.
    assert key(first) == key(second)
    # Require whether every item is true in a lazy sequence of the result of type(value) is the same object as
    # bool for mask in first.action_masks; otherwise raise AssertionError.
    assert all(type(value) is bool for mask in first.action_masks
               # Evaluate mask.feasibility as part of the enclosing expression.
               for value in mask.feasibility)


# Apply 'status,reason' as a decorator to configure the following definition.
@pytest.mark.parametrize("status,reason", (
    # Include a tuple containing NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH,
    # InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH in this tuple.
    (NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH,
     # Include InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH in this tuple.
     InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH),
    # Include a tuple containing NegotiationStatus.REGULATORY_PROFILE_MISMATCH,
    # InfeasibilityReason.REGULATORY_PROFILE_MISMATCH in this tuple.
    (NegotiationStatus.REGULATORY_PROFILE_MISMATCH,
     # Include InfeasibilityReason.REGULATORY_PROFILE_MISMATCH in this tuple.
     InfeasibilityReason.REGULATORY_PROFILE_MISMATCH),
    # Include a tuple containing NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT,... in this tuple.
    (NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
     # Include InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT in this tuple.
     InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT),
    # Include a tuple containing NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED,... in this
    # tuple.
    (NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED,
     # Include InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED in this tuple.
     InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED),
))
# Check regulatory uncertainty blocks policy authority using the setup, calls, and assertions below.
# Input status: the supplied status.
# Input reason: the supplied reason.
# Output: no explicit value; normal completion returns None.
def test_regulatory_uncertainty_blocks_policy_authority(status, reason):
    # Set result to the result of claims(the text 'B', a tuple containing the result of edge(the text 'A', the
    # text 'B')).
    result = claims("B", (edge("A", "B"),), status=status)
    # Require result.policy_authority is the same object as PolicyAuthority.POLICY_NOT_AUTHORIZED; otherwise raise
    # AssertionError.
    assert result.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    # Require result.policy_authority_reason is the same object as reason; otherwise raise AssertionError.
    assert result.policy_authority_reason is reason
    # Require result.action_masks[0].feasibility equals a tuple containing False, False; otherwise raise
    # AssertionError.
    assert result.action_masks[0].feasibility == (False, False)


# Check resolved law does not invoke policy and permission is explicit using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_resolved_law_does_not_invoke_policy_and_permission_is_explicit():
    # Set resolved to the result of claims(the text 'B', a tuple containing the result of edge(the text 'A', the
    # text 'B'),...).
    resolved = claims("B", (edge("A", "B"),),
                      # Supply NegotiationStatus.REGULATORY_ORDER_RESOLVED to claims.
                      NegotiationStatus.REGULATORY_ORDER_RESOLVED)
    # Set denied to the result of claims(the text 'B', a tuple containing the result of edge(the text 'A', the
    # text 'B')).
    denied = claims("B", (edge("A", "B"),), permitted=False)
    # Require resolved.policy_authority is the same object as PolicyAuthority.POLICY_NOT_REQUIRED; otherwise raise
    # AssertionError.
    assert resolved.policy_authority is PolicyAuthority.POLICY_NOT_REQUIRED
    # Require denied.policy_authority_reason is the same object as
    # InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED; otherwise raise AssertionError.
    assert denied.policy_authority_reason is (
        # Evaluate InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED as part of the enclosing expression.
        InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED
    )


# Check prediction probability cannot change hard mask using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_prediction_probability_cannot_change_hard_mask():
    # Set (low, high) to a tuple containing the result of edge(the text 'A', the text 'B', 0.01), the result of
    # edge(the text 'A', the text 'B', 0.99).
    low, high = edge("A", "B", 0.01), edge("A", "B", 0.99)
    # Require claims('B', (low,)).action_masks equals claims('B', (high,)).action_masks; otherwise raise
    # AssertionError.
    assert claims("B", (low,)).action_masks == claims("B", (high,)).action_masks


# Provenance using the inputs and processing steps below.
# Output: the result of ActorInputProvenance(the text 'EGO_LDM', the text 'CURRENT_SAME_STEP_V2V_GRAPH', the text
# 'CURRENT_MPNN_ENCODING',...).
def provenance():
    # Return the result of ActorInputProvenance(the text 'EGO_LDM', the text 'CURRENT_SAME_STEP_V2V_GRAPH', the
    # text 'CURRENT_MPNN_ENCODING',...) to the caller.
    return ActorInputProvenance(
        "EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH", "CURRENT_MPNN_ENCODING",
        "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
    )


# Check actor outputs only claim logits and works without critic using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actor_outputs_only_claim_logits_and_works_without_critic():
    # Set node_values to a zero-filled tensor with the requested shape.
    node_values = np.zeros((1, len(NODE_NUMERIC_SCHEMA)), dtype=np.float32)
    # Set node_masks to the result of np.ones_like(node_values).
    node_masks = np.ones_like(node_values, dtype=np.bool_)
    # Set encoded to the result of EncodedGraphObservation(the text 'A', a tuple containing the text 'A',
    # node_values, node_masks, the result of np.empty(a...).
    encoded = EncodedGraphObservation(
        # Supply node_values to EncodedGraphObservation.
        "A", ("A",), node_values, node_masks,
        # Supply dtype as np.int64.
        np.empty((2, 0), dtype=np.int64),
        # Supply dtype as np.float32.
        np.empty((0, len(EDGE_NUMERIC_SCHEMA)), dtype=np.float32),
        # Supply dtype as np.bool_.
        np.empty((0, len(EDGE_NUMERIC_SCHEMA)), dtype=np.bool_),
        # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
        NODE_NUMERIC_SCHEMA, EDGE_NUMERIC_SCHEMA,
        # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
        dict(CATEGORICAL_ENCODING_METADATA), {}, {}, "JOINT_LOCAL_V2V",
        "IDEAL_SAME_STEP_V2V", "NOT_FITTED_TRAINING_STATISTICS_REQUIRED",
        "NUMPY",
    )
    # Set mpnn to the result of EdgeAwareMPNNEncoder(the number of entries in NODE_NUMERIC_SCHEMA, the number of
    # entries in EDGE_NUMERIC_SCHEMA,...).
    mpnn = EdgeAwareMPNNEncoder(
        # Supply the number of entries in NODE_NUMERIC_SCHEMA to EdgeAwareMPNNEncoder.
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA),
        # Supply TEST_ONLY_NON_OPERATIONAL_VALUE to EdgeAwareMPNNEncoder.
        TEST_ONLY_NON_OPERATIONAL_VALUE, 1,
    )
    # Set mpnn_output to the result of mpnn(the result of to_torch_graph(encoded)).
    mpnn_output = mpnn(to_torch_graph(encoded))
    # Set actor to the result of DecentralizedNegotiationActor().
    actor = DecentralizedNegotiationActor(
        # Supply input_dim as 3 multiplied by TEST_ONLY_NON_OPERATIONAL_VALUE.
        # Supply action_count as 2.
        input_dim=3 * TEST_ONLY_NON_OPERATIONAL_VALUE, action_count=2,
    )
    # Set actor_input to the result of ActorForwardInput(the text 'A', the text 'B', mpnn_output.ego_embedding,
    # mpnn_output.graph_embedding, the result...).
    actor_input = ActorForwardInput(
        # Supply mpnn_output.graph_embedding to ActorForwardInput.
        "A", "B", mpnn_output.ego_embedding, mpnn_output.graph_embedding,
        # Supply the result of torch.ones(TEST_ONLY_NON_OPERATIONAL_VALUE) to ActorForwardInput.
        torch.ones(TEST_ONLY_NON_OPERATIONAL_VALUE),
        # Supply a tensor built from a list containing True, False to ActorForwardInput.
        torch.tensor([True, False]), provenance(),
    )
    # Set output to the result of actor(actor_input).
    output = actor(actor_input)
    # Require output.unmasked_action_logits.shape equals a tuple containing 2; otherwise raise AssertionError.
    assert output.unmasked_action_logits.shape == (2,)
    # Require output.action_feasibility_mask.dtype is the same object as torch.bool; otherwise raise
    # AssertionError.
    assert output.action_feasibility_mask.dtype is torch.bool
    # Require output.masked_action_distribution_inputs equals a tuple containing output.unmasked_action_logits,
    # output.action_feasibility_mask; otherwise raise AssertionError.
    assert output.masked_action_distribution_inputs == (
        # Include output.action_feasibility_mask in this tuple.
        output.unmasked_action_logits, output.action_feasibility_mask,
    )
    # Require the negation of whether actor_input exposes the requested attribute; otherwise raise AssertionError.
    assert not hasattr(actor_input, "centralized_critic_input")


# Apply pytest.mark.parametrize('agents', (1, 2, 4)) as a decorator to configure the following definition.
@pytest.mark.parametrize("agents", (1, 2, 4))
# Check critic variable agent count scalar finite value using the setup, calls, and assertions below.
# Input agents: the supplied agents.
# Output: no explicit value; normal completion returns None.
def test_critic_variable_agent_count_scalar_finite_value(agents):
    # Set representations to the result of torch.arange(agents * TEST_ONLY_NON_OPERATIONAL_VALUE,
    # dtype=torch.float32).reshape(agents, TEST_ONLY_NON_OPERATIONAL_VALUE).
    representations = torch.arange(
        # Supply dtype as torch.float32.
        agents * TEST_ONLY_NON_OPERATIONAL_VALUE, dtype=torch.float32,
    # Supply TEST_ONLY_NON_OPERATIONAL_VALUE to torch.arange(agents * TEST_ONLY_NON_OPERATIONAL_VALUE,
    # dtype=torch.float32).reshape.
    ).reshape(agents, TEST_ONLY_NON_OPERATIONAL_VALUE)
    # Set joint to the result of CentralizedCriticInputBuilder.build(representations).
    joint = CentralizedCriticInputBuilder.build(representations)
    # Set value to the result of CentralizedNegotiationCritic(TEST_ONLY_NON_OPERATIONAL_VALUE)(joint).
    value = CentralizedNegotiationCritic(TEST_ONLY_NON_OPERATIONAL_VALUE)(joint)
    # Require joint.shape equals a tuple containing TEST_ONLY_NON_OPERATIONAL_VALUE; otherwise raise
    # AssertionError.
    assert joint.shape == (TEST_ONLY_NON_OPERATIONAL_VALUE,)
    # Require value.shape equals a tuple containing 1 and the result of torch.isfinite(value).all(); otherwise
    # raise AssertionError.
    assert value.shape == (1,) and torch.isfinite(value).all()


# Check critic sum is permutation invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_critic_sum_is_permutation_invariant():
    # Set representations to the result of torch.arange(15, dtype=torch.float32).reshape(3, 5).
    representations = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    # Set first to the result of CentralizedCriticInputBuilder.build(representations).
    first = CentralizedCriticInputBuilder.build(representations)
    # Set second to the result of CentralizedCriticInputBuilder.build(representations at [2, 0, 1]).
    second = CentralizedCriticInputBuilder.build(representations[[2, 0, 1]])
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(first, second)


# Check actor and critic contracts exclude route truth and control using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actor_and_critic_contracts_exclude_route_truth_and_control():
    # Set root to Path(__file__).parents at 1.
    root = Path(__file__).parents[1]
    # Set sources to the result of '\n'.join(((root / 'negotiation_learning' / 'ctde' / name).read_text() for name
    # in...().
    sources = "\n".join((root / "negotiation_learning" / "ctde" / name).read_text()
                         # Evaluate a tuple containing the text 'interfaces.py', the text '__init__.py' as part of
                         # the enclosing expression.
                         for name in ("interfaces.py", "__init__.py")).lower()
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text 'ground_truth',
    # the text 'future_route', the text...
    forbidden = ("route_id", "route_index", "ground_truth", "future_route",
                 "traci", "setspeed", "slowdown", "setacceleration", "reward")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to sources for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in sources for item in forbidden)


# Check no operational hyperparameters optimizer or mask magnitude using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_operational_hyperparameters_optimizer_or_mask_magnitude():
    # Set root to Path(__file__).parents at 1.
    root = Path(__file__).parents[1]
    # Set paths to a tuple containing root joined with the path segment 'negotiation_learning' joined with the path segment
    # 'claim_semantics.py', root divided by...
    paths = (root / "negotiation_learning" / "claim_semantics.py",
             # Include root joined with the path segment 'negotiation_learning' joined with the path segment 'ctde' divided by the
             # text 'interfaces.py' in this tuple.
             root / "negotiation_learning" / "ctde" / "interfaces.py")
    # Set source to the result of '\n'.join(a lazy sequence of the result of path.read_text().lower() for path in
    # paths).
    source = "\n".join(path.read_text().lower() for path in paths)
    # Set forbidden to a tuple containing the text '-1e9', the text 'adam', the text 'adamw', the text 'sgd', the
    # text 'learning_rate', the text...
    forbidden = ("-1e9", "adam", "adamw", "sgd", "learning_rate", "gamma =",
                 "gae", "clip_epsilon", "softmax(", "categorical(")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
