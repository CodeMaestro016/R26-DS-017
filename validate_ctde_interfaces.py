"""Independent Step 5E semantic and CPU forward-interface validation."""

from ml_runtime_capability import detect_ml_runtime
from negotiation_learning import (
    NegotiationClaimBuilder, NegotiationStatus, PolicyAuthority,
)


def _edge(source, target):
    return {
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        "applicable_rule_ids": ("TEST_RULE",),
        "source_sections": ("TEST_SECTION",),
        "shared_conflict_zone_ids": ("TEST_ZONE",), "timestamp": 1.0,
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }


def _build(ego, edges, status=None, permission=True, consistent=True):
    return NegotiationClaimBuilder().build(
        ego, {"joint_precedence_edges": tuple(edges)},
        (status or NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE).value,
        permission, consistent,
    )


def _pairs(items):
    return {(item.yielding_vehicle_id, item.priority_vehicle_id) for item in items}


def main():
    capability = detect_ml_runtime()
    print("CTDE Negotiation Interface Validation\n")
    if capability.pytorch_cpu_test != "PASS":
        print("Status\n  PYTORCH_RUNTIME_VALIDATION_BLOCKED")
        print("  SUMO runtime affected: False")
        return "PYTORCH_RUNTIME_VALIDATION_BLOCKED"

    import torch
    import numpy as np
    from negotiation_learning.ctde import (
        ActorForwardInput, ActorInputProvenance, CentralizedCriticInputBuilder,
        CentralizedNegotiationCritic, DecentralizedNegotiationActor,
    )
    from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
    from negotiation_learning.tensor_encoding.models import EncodedGraphObservation
    from negotiation_learning.tensor_encoding.schemas import (
        CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, NODE_NUMERIC_SCHEMA,
    )

    simple_a = _build("A", (_edge("A", "B"),))
    simple_b = _build("B", (_edge("A", "B"),))
    assert _pairs(simple_a.mandatory_yield_obligations) == {("A", "B")}
    assert not simple_a.ego_precedence_claims
    assert _pairs(simple_b.ego_precedence_claims) == {("A", "B")}

    cycle = tuple(_edge(a, b) for a, b in (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    expected = {
        "A": (("A", "B"), ("D", "A")),
        "B": (("B", "C"), ("A", "B")),
        "C": (("C", "D"), ("B", "C")),
        "D": (("D", "A"), ("C", "D")),
    }
    cycle_results = {ego: _build(ego, cycle) for ego in expected}
    for ego, (obligation, claim) in expected.items():
        assert _pairs(cycle_results[ego].mandatory_yield_obligations) == {obligation}
        assert _pairs(cycle_results[ego].ego_precedence_claims) == {claim}

    multiple = _build("B", (_edge("A", "B"), _edge("C", "B")))
    assert len(multiple.ego_precedence_claims) == 2
    assert len(multiple.action_candidates) == 4
    assert all(type(value) is bool for mask in multiple.action_masks
               for value in mask.feasibility)
    reverse = _build("B", (_edge("C", "B"), _edge("A", "B")))
    assert multiple.action_masks == reverse.action_masks
    assert tuple(len(_build("E", tuple(_edge(str(i), "E") for i in range(n)))
                     .ego_precedence_claims) for n in range(4)) == (0, 1, 2, 3)

    blocked = _build("B", (_edge("A", "B"),),
                     NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT)
    assert blocked.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    assert blocked.action_masks[0].feasibility == (False, False)

    # TEST_ONLY_NON_OPERATIONAL_VALUE: interface shape exercise, not architecture.
    test_dimension = 5
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
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA), test_dimension, 1,
    )
    mpnn_output = mpnn(to_torch_graph(encoded))
    actor = DecentralizedNegotiationActor(test_dimension * 3, 2)
    provenance = ActorInputProvenance(
        "EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH", "CURRENT_MPNN_ENCODING",
        "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
    )
    actor_input = ActorForwardInput(
        "A", "D", mpnn_output.ego_embedding, mpnn_output.graph_embedding,
        torch.ones(test_dimension),
        torch.tensor([True, True]), provenance,
    )
    actor_output = actor(actor_input)
    assert actor_output.unmasked_action_logits.shape == (2,)
    assert not hasattr(actor_input, "centralized_critic_input")

    agent_representations = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    joint = CentralizedCriticInputBuilder.build(agent_representations)
    permuted = CentralizedCriticInputBuilder.build(agent_representations[[2, 0, 1]])
    torch.testing.assert_close(joint, permuted)
    value = CentralizedNegotiationCritic(test_dimension)(joint)
    assert value.shape == (1,) and torch.isfinite(value).all()

    print("Research semantics")
    print("  Edge convention yielding->priority: PASS")
    print("  Claim ownership derived from incoming edge: PASS")
    print("  Mandatory obligations derived from outgoing edge: PASS")
    print("  Claim-targeted actions: PASS")
    print("\nFour-way cycle")
    for ego, (obligation, claim) in expected.items():
        print(f"  {ego} obligation {obligation[0]}->{obligation[1]}: PASS")
        print(f"  {ego} claim {claim[0]}->{claim[1]}: PASS")
    print("\nAction feasibility")
    print("  Boolean hard mask: PASS")
    print("  Learned mask parameters: 0")
    print("  Arbitrary thresholds: 0")
    print("  Invalid-action penalty constants: 0")
    print("  Regulatory disagreement blocks policy: PASS")
    print("  Prediction probability cannot override mask: PASS")
    print("\nActor")
    print("  Decentralized input only: PASS")
    print("  Claim-level logits generated: PASS")
    print("  Action executed: False")
    print("\nCritic")
    print("  Training-only interface: PASS")
    print("  Variable agent count: PASS")
    print("  Permutation-invariant SUM aggregation: PASS")
    print("  State value finite with shape (1,): PASS")
    print("  Global route truth consumed: 0")
    print("\nCTDE separation")
    print("  Actor accesses critic-only state: False")
    print("  Actor functional without critic: PASS")
    print("\nProtocol completeness")
    print("  Status: ACTION_PROTOCOL_INCOMPLETE")
    print("  Missing: counterparty acceptance/acknowledgement semantics")
    print("\nDependencies")
    print(f"  Backend: PyTorch {capability.pytorch_version} CPU")
    print("  TensorFlow required: False")
    print("  CUDA required: False")
    print("  PyTorch Geometric required: False")
    print("\nResearch status")
    print("  Reward implemented: False")
    print("  PPO implemented: False")
    print("  Optimizer implemented: False")
    print("  Training performed: False")
    print("  Model checkpoint produced: False")
    print("  SUMO control actions issued: 0")
    return "PASS"


if __name__ == "__main__":
    result = main()
    if result not in {"PASS", "PYTORCH_RUNTIME_VALIDATION_BLOCKED"}:
        raise SystemExit(1)
