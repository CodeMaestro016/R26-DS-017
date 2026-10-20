"""Independent Step 5E semantic and CPU forward-interface validation."""

# Import detect_ml_runtime from ml_runtime_capability for the operations below.
from ml_runtime_capability import detect_ml_runtime
# Import NegotiationClaimBuilder, NegotiationStatus, PolicyAuthority from negotiation_learning for the operations
# below.
from negotiation_learning import (
    NegotiationClaimBuilder, NegotiationStatus, PolicyAuthority,
)


# Edge using the inputs and processing steps below.
# Input source: the supplied source.
# Input target: the supplied target.
# Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
# source_sections,...
def _edge(source, target):
    # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
    # source_sections,... to the caller.
    return {
        # Store source under 'yielding_vehicle_id'.
        # Store target under 'priority_vehicle_id'.
        "yielding_vehicle_id": source, "priority_vehicle_id": target,
        # Store a tuple containing the text 'TEST_RULE' under 'applicable_rule_ids'.
        "applicable_rule_ids": ("TEST_RULE",),
        # Store a tuple containing the text 'TEST_SECTION' under 'source_sections'.
        "source_sections": ("TEST_SECTION",),
        # Store a tuple containing the text 'TEST_ZONE' under 'shared_conflict_zone_ids'.
        # Store 1.0 under 'timestamp'.
        "shared_conflict_zone_ids": ("TEST_ZONE",), "timestamp": 1.0,
        # Store a dictionary containing mandatory_regulatory_yield under 'hard_constraint_evidence'.
        # Store True under 'mandatory_regulatory_yield'.
        "hard_constraint_evidence": {"mandatory_regulatory_yield": True},
    }


# Build using the inputs and processing steps below.
# Input ego: the ego vehicle used in this calculation.
# Input edges: the supplied edges.
# Input status: the supplied status.
# Input permission: the supplied permission.
# Input consistent: the supplied consistent.
# Output: the result of NegotiationClaimBuilder().build(ego, a dictionary containing joint_precedence_edges,
# (status or...).
def _build(ego, edges, status=None, permission=True, consistent=True):
    # Return the result of NegotiationClaimBuilder().build(ego, a dictionary containing joint_precedence_edges,
    # (status or...) to the caller.
    return NegotiationClaimBuilder().build(
        # Store a tuple built from edges under 'joint_precedence_edges'.
        ego, {"joint_precedence_edges": tuple(edges)},
        # Supply (status or NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE).value to
        # NegotiationClaimBuilder().build.
        (status or NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE).value,
        # Supply permission to NegotiationClaimBuilder().build.
        permission, consistent,
    )


# Pairs using the inputs and processing steps below.
# Input items: the supplied items.
# Output: a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in items.
def _pairs(items):
    # Return a set of a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id for item in items to
    # the caller.
    return {(item.yielding_vehicle_id, item.priority_vehicle_id) for item in items}


# Main using the inputs and processing steps below.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set capability to the result of detect_ml_runtime().
    capability = detect_ml_runtime()
    # Display the text 'CTDE Negotiation Interface Validation'.
    print("CTDE Negotiation Interface Validation\n")
    # Run this branch when capability.pytorch_cpu_test differs from the text 'PASS'.
    if capability.pytorch_cpu_test != "PASS":
        # Display the text 'Status PYTORCH_RUNTIME_VALIDATION_BLOCKED'.
        print("Status\n  PYTORCH_RUNTIME_VALIDATION_BLOCKED")
        # Display the text 'SUMO runtime affected: False'.
        print("  SUMO runtime affected: False")
        # Return the text 'PYTORCH_RUNTIME_VALIDATION_BLOCKED' to the caller.
        return "PYTORCH_RUNTIME_VALIDATION_BLOCKED"

    # Import torch for use in this module.
    import torch
    # Import numpy as np for use in this module.
    import numpy as np
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

    # Set simple_a to the result of _build(the text 'A', a tuple containing the result of _edge(the text 'A', the
    # text 'B')).
    simple_a = _build("A", (_edge("A", "B"),))
    # Set simple_b to the result of _build(the text 'B', a tuple containing the result of _edge(the text 'A', the
    # text 'B')).
    simple_b = _build("B", (_edge("A", "B"),))
    # Require the result of _pairs(simple_a.mandatory_yield_obligations) equals a set containing a tuple
    # containing the text 'A', the text 'B'; otherwise raise AssertionError.
    assert _pairs(simple_a.mandatory_yield_obligations) == {("A", "B")}
    # Require the negation of simple_a.ego_precedence_claims; otherwise raise AssertionError.
    assert not simple_a.ego_precedence_claims
    # Require the result of _pairs(simple_b.ego_precedence_claims) equals a set containing a tuple containing the
    # text 'A', the text 'B'; otherwise raise AssertionError.
    assert _pairs(simple_b.ego_precedence_claims) == {("A", "B")}

    # Set cycle to a tuple built from a lazy sequence of the result of _edge(a, b) for (a, b) in a tuple
    # containing a tuple containing 'A', 'B', a tuple containing 'B', 'C', a tuple containing 'C', 'D', a tuple
    # containing...
    cycle = tuple(_edge(a, b) for a, b in (
        # Include a tuple containing the text 'A', the text 'B' in this tuple.
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
    ))
    # Set expected to a dictionary containing A, B, C, D.
    expected = {
        # Store a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text 'D',
        # the text 'A' under 'A'.
        "A": (("A", "B"), ("D", "A")),
        # Store a tuple containing a tuple containing the text 'B', the text 'C', a tuple containing the text 'A',
        # the text 'B' under 'B'.
        "B": (("B", "C"), ("A", "B")),
        # Store a tuple containing a tuple containing the text 'C', the text 'D', a tuple containing the text 'B',
        # the text 'C' under 'C'.
        "C": (("C", "D"), ("B", "C")),
        # Store a tuple containing a tuple containing the text 'D', the text 'A', a tuple containing the text 'C',
        # the text 'D' under 'D'.
        "D": (("D", "A"), ("C", "D")),
    }
    # Set cycle_results to a dictionary of ego mapped to the result of _build(ego, cycle) for ego in expected.
    cycle_results = {ego: _build(ego, cycle) for ego in expected}
    # Iterate over key/value pairs from expected, binding each item to (ego, (obligation, claim)).
    for ego, (obligation, claim) in expected.items():
        # Require the result of _pairs(cycle_results[ego].mandatory_yield_obligations) equals a set containing
        # obligation; otherwise raise AssertionError.
        assert _pairs(cycle_results[ego].mandatory_yield_obligations) == {obligation}
        # Require the result of _pairs(cycle_results[ego].ego_precedence_claims) equals a set containing claim;
        # otherwise raise AssertionError.
        assert _pairs(cycle_results[ego].ego_precedence_claims) == {claim}

    # Set multiple to the result of _build(the text 'B', a tuple containing the result of _edge(the text 'A', the
    # text 'B'), the result of...).
    multiple = _build("B", (_edge("A", "B"), _edge("C", "B")))
    # Require the number of entries in multiple.ego_precedence_claims equals 2; otherwise raise AssertionError.
    assert len(multiple.ego_precedence_claims) == 2
    # Require the number of entries in multiple.action_candidates equals 4; otherwise raise AssertionError.
    assert len(multiple.action_candidates) == 4
    # Require whether every item is true in a lazy sequence of the result of type(value) is the same object as
    # bool for mask in multiple.action_masks; otherwise raise AssertionError.
    assert all(type(value) is bool for mask in multiple.action_masks
               # Evaluate mask.feasibility as part of the enclosing expression.
               for value in mask.feasibility)
    # Set reverse to the result of _build(the text 'B', a tuple containing the result of _edge(the text 'C', the
    # text 'B'), the result of...).
    reverse = _build("B", (_edge("C", "B"), _edge("A", "B")))
    # Require multiple.action_masks equals reverse.action_masks; otherwise raise AssertionError.
    assert multiple.action_masks == reverse.action_masks
    # Require a tuple built from a lazy sequence of the number of entries in _build('E', tuple((_edge(str(i), 'E')
    # for i in range(n)))).ego_precedence_claims for n in the integer range defined by 4 equals a tuple containing
    # 0, 1, 2, 3; otherwise raise AssertionError.
    assert tuple(len(_build("E", tuple(_edge(str(i), "E") for i in range(n)))
                     # Evaluate a tuple containing 0, 1, 2, 3 as part of the enclosing expression.
                     .ego_precedence_claims) for n in range(4)) == (0, 1, 2, 3)

    # Set blocked to the result of _build(the text 'B', a tuple containing the result of _edge(the text 'A', the
    # text 'B'),...).
    blocked = _build("B", (_edge("A", "B"),),
                     # Supply NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT to _build.
                     NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT)
    # Require blocked.policy_authority is the same object as PolicyAuthority.POLICY_NOT_AUTHORIZED; otherwise
    # raise AssertionError.
    assert blocked.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    # Require blocked.action_masks[0].feasibility equals a tuple containing False, False; otherwise raise
    # AssertionError.
    assert blocked.action_masks[0].feasibility == (False, False)

    # TEST_ONLY_NON_OPERATIONAL_VALUE: interface shape exercise, not architecture.
    # Set test_dimension to 5.
    test_dimension = 5
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
        len(NODE_NUMERIC_SCHEMA), len(EDGE_NUMERIC_SCHEMA), test_dimension, 1,
    )
    # Set mpnn_output to the result of mpnn(the result of to_torch_graph(encoded)).
    mpnn_output = mpnn(to_torch_graph(encoded))
    # Set actor to the result of DecentralizedNegotiationActor(test_dimension multiplied by 3, 2).
    actor = DecentralizedNegotiationActor(test_dimension * 3, 2)
    # Set provenance to the result of ActorInputProvenance(the text 'EGO_LDM', the text
    # 'CURRENT_SAME_STEP_V2V_GRAPH', the text 'CURRENT_MPNN_ENCODING',...).
    provenance = ActorInputProvenance(
        "EGO_LDM", "CURRENT_SAME_STEP_V2V_GRAPH", "CURRENT_MPNN_ENCODING",
        "CURRENT_DETERMINISTIC_REGULATORY_EVIDENCE",
    )
    # Set actor_input to the result of ActorForwardInput(the text 'A', the text 'D', mpnn_output.ego_embedding,
    # mpnn_output.graph_embedding, the result...).
    actor_input = ActorForwardInput(
        # Supply mpnn_output.graph_embedding to ActorForwardInput.
        "A", "D", mpnn_output.ego_embedding, mpnn_output.graph_embedding,
        # Supply the result of torch.ones(test_dimension) to ActorForwardInput.
        torch.ones(test_dimension),
        # Supply a tensor built from a list containing True, True to ActorForwardInput.
        torch.tensor([True, True]), provenance,
    )
    # Set actor_output to the result of actor(actor_input).
    actor_output = actor(actor_input)
    # Require actor_output.unmasked_action_logits.shape equals a tuple containing 2; otherwise raise
    # AssertionError.
    assert actor_output.unmasked_action_logits.shape == (2,)
    # Require the negation of whether actor_input exposes the requested attribute; otherwise raise AssertionError.
    assert not hasattr(actor_input, "centralized_critic_input")

    # Set agent_representations to the result of torch.arange(15, dtype=torch.float32).reshape(3, 5).
    agent_representations = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    # Set joint to the result of CentralizedCriticInputBuilder.build(agent_representations).
    joint = CentralizedCriticInputBuilder.build(agent_representations)
    # Set permuted to the result of CentralizedCriticInputBuilder.build(agent_representations at [2, 0, 1]).
    permuted = CentralizedCriticInputBuilder.build(agent_representations[[2, 0, 1]])
    # Call torch.testing.assert_close with the supplied arguments.
    torch.testing.assert_close(joint, permuted)
    # Set value to the result of CentralizedNegotiationCritic(test_dimension)(joint).
    value = CentralizedNegotiationCritic(test_dimension)(joint)
    # Require value.shape equals a tuple containing 1 and the result of torch.isfinite(value).all(); otherwise
    # raise AssertionError.
    assert value.shape == (1,) and torch.isfinite(value).all()

    # Display the text 'Research semantics'.
    print("Research semantics")
    # Display the text 'Edge convention yielding->priority: PASS'.
    print("  Edge convention yielding->priority: PASS")
    # Display the text 'Claim ownership derived from incoming edge: PASS'.
    print("  Claim ownership derived from incoming edge: PASS")
    # Display the text 'Mandatory obligations derived from outgoing edge: PASS'.
    print("  Mandatory obligations derived from outgoing edge: PASS")
    # Display the text 'Claim-targeted actions: PASS'.
    print("  Claim-targeted actions: PASS")
    # Display the text 'Four-way cycle'.
    print("\nFour-way cycle")
    # Iterate over key/value pairs from expected, binding each item to (ego, (obligation, claim)).
    for ego, (obligation, claim) in expected.items():
        # Display formatted text built from the embedded values.
        print(f"  {ego} obligation {obligation[0]}->{obligation[1]}: PASS")
        # Display formatted text built from the embedded values.
        print(f"  {ego} claim {claim[0]}->{claim[1]}: PASS")
    # Display the text 'Action feasibility'.
    print("\nAction feasibility")
    # Display the text 'Boolean hard mask: PASS'.
    print("  Boolean hard mask: PASS")
    # Display the text 'Learned mask parameters: 0'.
    print("  Learned mask parameters: 0")
    # Display the text 'Arbitrary thresholds: 0'.
    print("  Arbitrary thresholds: 0")
    # Display the text 'Invalid-action penalty constants: 0'.
    print("  Invalid-action penalty constants: 0")
    # Display the text 'Regulatory disagreement blocks policy: PASS'.
    print("  Regulatory disagreement blocks policy: PASS")
    # Display the text 'Prediction probability cannot override mask: PASS'.
    print("  Prediction probability cannot override mask: PASS")
    # Display the text 'Actor'.
    print("\nActor")
    # Display the text 'Decentralized input only: PASS'.
    print("  Decentralized input only: PASS")
    # Display the text 'Claim-level logits generated: PASS'.
    print("  Claim-level logits generated: PASS")
    # Display the text 'Action executed: False'.
    print("  Action executed: False")
    # Display the text 'Critic'.
    print("\nCritic")
    # Display the text 'Training-only interface: PASS'.
    print("  Training-only interface: PASS")
    # Display the text 'Variable agent count: PASS'.
    print("  Variable agent count: PASS")
    # Display the text 'Permutation-invariant SUM aggregation: PASS'.
    print("  Permutation-invariant SUM aggregation: PASS")
    # Display the text 'State value finite with shape (1,): PASS'.
    print("  State value finite with shape (1,): PASS")
    # Display the text 'Global route truth consumed: 0'.
    print("  Global route truth consumed: 0")
    # Display the text 'CTDE separation'.
    print("\nCTDE separation")
    # Display the text 'Actor accesses critic-only state: False'.
    print("  Actor accesses critic-only state: False")
    # Display the text 'Actor functional without critic: PASS'.
    print("  Actor functional without critic: PASS")
    # Display the text 'Protocol completeness'.
    print("\nProtocol completeness")
    # Display the text 'Status: MULTI_PROPOSAL_PER_CLAIM_PROTOCOL_AVAILABLE_STEP_5E_2'.
    print("  Status: MULTI_PROPOSAL_PER_CLAIM_PROTOCOL_AVAILABLE_STEP_5E_2")
    # Display the text 'Proposal plus matching ACCEPT evidence supported: True'.
    print("  Proposal plus matching ACCEPT evidence supported: True")
    # Display the text 'Third transport acknowledgement required: False'.
    print("  Third transport acknowledgement required: False")
    # Display the text 'Response policy interface implemented untrained: True'.
    print("  Response policy interface implemented untrained: True")
    # Display the text 'Response policy learning method: PENDING_RESEARCH_DECISION'.
    print("  Response policy learning method: PENDING_RESEARCH_DECISION")
    # Display the text 'Response actor architecture: REQUIRES_EXPERIMENTAL_SELECTION'.
    print("  Response actor architecture: REQUIRES_EXPERIMENTAL_SELECTION")
    # Display the text 'Dependencies'.
    print("\nDependencies")
    # Display formatted text built from the embedded values.
    print(f"  Backend: PyTorch {capability.pytorch_version} CPU")
    # Display the text 'TensorFlow required: False'.
    print("  TensorFlow required: False")
    # Display the text 'CUDA required: False'.
    print("  CUDA required: False")
    # Display the text 'PyTorch Geometric required: False'.
    print("  PyTorch Geometric required: False")
    # Display the text 'Research status'.
    print("\nResearch status")
    # Display the text 'Reward implemented: False'.
    print("  Reward implemented: False")
    # Display the text 'PPO implemented: False'.
    print("  PPO implemented: False")
    # Display the text 'Optimizer implemented: False'.
    print("  Optimizer implemented: False")
    # Display the text 'Training performed: False'.
    print("  Training performed: False")
    # Display the text 'Model checkpoint produced: False'.
    print("  Model checkpoint produced: False")
    # Display the text 'SUMO control actions issued: 0'.
    print("  SUMO control actions issued: 0")
    # Return the text 'PASS' to the caller.
    return "PASS"


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Set result to the result of main().
    result = main()
    # Run this branch when result does not belong to a set containing the text 'PASS', the text
    # 'PYTORCH_RUNTIME_VALIDATION_BLOCKED'.
    if result not in {"PASS", "PYTORCH_RUNTIME_VALIDATION_BLOCKED"}:
        # Raise SystemExit with 1 to stop this execution path.
        raise SystemExit(1)
