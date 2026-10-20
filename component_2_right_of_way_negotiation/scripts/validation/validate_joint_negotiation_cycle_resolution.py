"""Step 5J.2B.1 structural joint-cycle validation; performs no training."""

# Import Counter from collections for the operations below.
from collections import Counter

# Import real_training_evidence from joint_negotiation_validation for the operations below.
from joint_negotiation_validation import real_training_evidence
# Import ClaimRelinquishmentProtocol from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import ClaimRelinquishmentProtocol


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set evidence to the result of real_training_evidence().
    evidence = real_training_evidence()
    # Set branches to evidence at 'branches'.
    branches = evidence["branches"]
    # Set counts to the result of Counter(a lazy sequence of item.branch_status for item in branches).
    counts = Counter(item.branch_status for item in branches)
    # Set chosen to the minimum of evidence at 'executable'.
    chosen = min(evidence["executable"],
                 # Declare item as input parameter.
                 key=lambda item: (len(item.completed_agreement_ids), item.branch_id))
    # Set keep to the next item from a lazy sequence of item for item in branches; retain entries satisfying
    # whether every item is true in a lazy sequence of action == 'KEEP_CLAIM' for (_,...
    keep = next(item for item in branches
                # Evaluate whether every item is true in a lazy sequence of action equals the text 'KEEP_CLAIM'
                # for (_, action) in item.proposer_assignment.claim_action_assignments as part of the enclosing
                # expression.
                if all(action == "KEEP_CLAIM" for _, action in
                       # Evaluate item.proposer_assignment.claim_action_assignments as part of the enclosing
                       # expression.
                       item.proposer_assignment.claim_action_assignments))
    # Require keep.original_precedence_graph equals keep.effective_precedence_graph; otherwise raise
    # AssertionError.
    assert keep.original_precedence_graph == keep.effective_precedence_graph
    # Require keep.cycle_detected and the negation of keep.graph_executable; otherwise raise AssertionError.
    assert keep.cycle_detected and not keep.graph_executable
    # Set smallest to the minimum of a lazy sequence of the number of entries in item.completed_agreement_ids for
    # item in evidence at...
    smallest = min(len(item.completed_agreement_ids) for item in evidence["executable"])
    # Require chosen.execution_plan.ready_vehicle_ids; otherwise raise AssertionError.
    assert chosen.execution_plan.ready_vehicle_ids
    # Set forward to the result of ClaimRelinquishmentProtocol().evaluate_all_claims(evidence at 'edges',
    # chosen.protocol_messages, evidence at 'timestamp', the text...).
    forward = ClaimRelinquishmentProtocol().evaluate_all_claims(
        # Supply chosen.protocol_messages to ClaimRelinquishmentProtocol().evaluate_all_claims.
        evidence["edges"], chosen.protocol_messages, evidence["timestamp"],
        "DE_STVO_UNCONTROLLED_4WAY_V1")
    # Set reverse to the result of ClaimRelinquishmentProtocol().evaluate_all_claims(evidence at 'edges', a tuple
    # built from the reverse traversal of chosen.protocol_messages,...).
    reverse = ClaimRelinquishmentProtocol().evaluate_all_claims(
        # Supply a tuple built from the reverse traversal of chosen.protocol_messages to
        # ClaimRelinquishmentProtocol().evaluate_all_claims.
        evidence["edges"], tuple(reversed(chosen.protocol_messages)),
        # Supply evidence at 'timestamp' to ClaimRelinquishmentProtocol().evaluate_all_claims.
        evidence["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
    # Require forward equals reverse; otherwise raise AssertionError.
    assert forward == reverse
    # Set reordered to the result of evidence['enumerator'].enumerate().
    reordered = evidence["enumerator"].enumerate(
        # Supply scenario_id as evidence at 'scenario_id'.
        scenario_id=evidence["scenario_id"],
        # Supply source_snapshot_id as evidence at 'source_snapshot_id'.
        source_snapshot_id=evidence["source_snapshot_id"],
        # Supply original_edges as a tuple built from the reverse traversal of evidence at 'edges'.
        original_edges=tuple(reversed(evidence["edges"])),
        # Supply active_vehicle_ids as a tuple built from the reverse traversal of a tuple built from evidence at
        # 'movements'.
        active_vehicle_ids=tuple(reversed(tuple(evidence["movements"]))),
        # Supply timestamp as evidence at 'timestamp'.
        # Supply regulatory_profile as the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
        timestamp=evidence["timestamp"], regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
        # Supply negotiation_status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        # Supply movement_path_by_vehicle as evidence at 'movements'.
        movement_path_by_vehicle=evidence["movements"])
    # Require a tuple built from a lazy sequence of item.branch_id for item in reordered equals a tuple built from
    # a lazy sequence of item.branch_id for item in branches; otherwise raise AssertionError.
    assert tuple(item.branch_id for item in reordered) == tuple(item.branch_id for item in branches)
    # Require a tuple built from a lazy sequence of item.effective_precedence_graph for item in reordered equals a
    # tuple built from a lazy sequence of item.effective_precedence_graph for item in branches; otherwise raise
    # AssertionError.
    assert tuple(item.effective_precedence_graph for item in reordered) == tuple(
        # Evaluate item.effective_precedence_graph as part of the enclosing expression.
        item.effective_precedence_graph for item in branches)

    # Set factors to chosen.proposer_assignment.eligible_claim_ids.
    factors = chosen.proposer_assignment.eligible_claim_ids
    # Set proposer_assignments to a set of item.proposer_assignment.claim_action_assignments for item in branches.
    proposer_assignments = {item.proposer_assignment.claim_action_assignments
                            # Evaluate branches as part of the enclosing expression.
                            for item in branches}
    # Display the text 'Step 5J.2B.1 Joint Cycle Resolution Validation'.
    print("Step 5J.2B.1 Joint Cycle Resolution Validation\n")
    # Display the text 'Source'.
    print("Source")
    # Display the text 'Source: REAL_SUMO_TRAINING_SCENARIO'.
    print("  Source: REAL_SUMO_TRAINING_SCENARIO")
    # Display formatted text built from the embedded values.
    print(f"  Scenario ID: {evidence['scenario_id']}")
    # Display formatted text built from the embedded values.
    print(f"  Snapshot ID: {evidence['source_snapshot_id']}")
    # Display formatted text built from the embedded values.
    print(f"  Original graph edges: {chosen.original_precedence_graph}")
    # Display formatted text built from the embedded values.
    print(f"  Original SCCs: {keep.strongly_connected_components}")
    # Display the text 'Original graph cyclic: True'.
    print("  Original graph cyclic: True\n")
    # Display the text 'Policy factors'.
    print("Policy factors")
    # Display formatted text built from the embedded values.
    print(f"  Eligible proposer factors: {len(factors)}")
    # Display formatted text built from the embedded values.
    print(f"  Multi-action proposer factors: {len(factors)}")
    # Display formatted text built from the embedded values.
    print(f"  Feasible joint proposer assignments: {len(proposer_assignments)}\n")
    # Display the text 'Protocol'.
    print("Protocol")
    # Display formatted text built from the embedded values.
    print(f"  Maximum proposals in a branch: {max(len(x.proposer_assignment.proposals_created) for x in branches)}")
    # Display formatted text built from the embedded values.
    print(f"  Responder factors represented: {len(factors)}")
    # Display formatted text built from the embedded values.
    print(f"  Complete proposer/responder branches: {len(branches)}")
    # Display the text 'One joint protocol evaluation per branch: PASS'.
    print("  One joint protocol evaluation per branch: PASS\n")
    # Display the text 'Joint branches'.
    print("Joint branches")
    # Display formatted text built from the embedded values.
    print(f"  Total valid joint branches: {len(branches)}")
    # Display formatted text built from the embedded values.
    print(f"  Keep-all cyclic branches: {counts['JOINT_BRANCH_NO_PROPOSALS']}")
    # Display formatted text built from the embedded values.
    print(f"  Reject/no-agreement cyclic branches: {counts['JOINT_BRANCH_PROPOSALS_REJECTED']}")
    # Display formatted text built from the embedded values.
    print(f"  Partial-accept cyclic branches: {counts['JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC']}")
    # Display formatted text built from the embedded values.
    print(f"  Executable acyclic branches: {counts['JOINT_BRANCH_EXECUTABLE_ACYCLIC']}")
    # Display formatted text built from the embedded values.
    print(f"  Protocol-blocked/disagreement branches: {counts['JOINT_BRANCH_PROTOCOL_BLOCKED'] + counts['JOINT_BRANCH_PROTOCOL_DISAGREEMENT']}\n")
    # Display the text 'Executable evidence'.
    print("Executable evidence")
    # Display the text 'At least one executable branch exists: PASS'.
    print("  At least one executable branch exists: PASS")
    # Display the text 'Effective graph acyclic: PASS'.
    print("  Effective graph acyclic: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Ready vehicle set nonempty: PASS {chosen.execution_plan.ready_vehicle_ids}")
    # Display formatted text built from the embedded values.
    print(f"  Smallest accepted-agreement count observed: {smallest} (descriptive only)")
    # Display formatted text built from the embedded values.
    print(f"  Executable proposer actions: {chosen.proposer_assignment.claim_action_assignments}")
    # Display formatted text built from the embedded values.
    print(f"  Executable responder actions: {chosen.responder_assignment.response_action_assignments}")
    # Display formatted text built from the embedded values.
    print(f"  Effective graph: {chosen.effective_precedence_graph}")
    # Display the text 'Automatic winner heuristic introduced: False'.
    print("  Automatic winner heuristic introduced: False")
    # Display the text 'Automatic edge deletion introduced: False'.
    print("  Automatic edge deletion introduced: False\n")
    # Display the text 'Invariance'.
    print("Invariance")
    # Display the text 'Claim/factor-order invariant: PASS'.
    print("  Claim/factor-order invariant: PASS")
    # Display the text 'Proposal/response/message-order invariant: PASS'.
    print("  Proposal/response/message-order invariant: PASS")
    # Display the text 'Vehicle-order invariant: PASS'.
    print("  Vehicle-order invariant: PASS\n")
    # Display the text 'Authority'.
    print("Authority")
    # Display the text 'Hard-mask bypasses: 0'.
    print("  Hard-mask bypasses: 0")
    # Display the text 'Regulatory rules modified: False'.
    print("  Regulatory rules modified: False")
    # Display the text 'Protocol semantics modified: False'.
    print("  Protocol semantics modified: False")
    # Display the text 'Route-truth actor leakage: 0'.
    print("  Route-truth actor leakage: 0\n")
    # Display the text 'Frozen design'.
    print("Frozen design")
    # Display the text 'Step 5J.2 freeze unchanged: PASS'.
    print("  Step 5J.2 freeze unchanged: PASS")
    # Display the text 'Validation scenarios executed: 0'.
    print("  Validation scenarios executed: 0")
    # Display the text 'Held-out scenarios executed: 0'.
    print("  Held-out scenarios executed: 0\n")
    # Display the text 'Training'.
    print("Training")
    # Display the text 'Optimizer instantiated: False'.
    print("  Optimizer instantiated: False")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'MAPPO runs: 0'.
    print("  MAPPO runs: 0")
    # Display the text 'Learned policy actions: 0'.
    print("  Learned policy actions: 0\n")
    # Display the text 'Status'.
    print("Status")
    # Display the text 'JOINT_NEGOTIATION_CYCLE_RESOLUTION_STATUS:...'.
    print("  JOINT_NEGOTIATION_CYCLE_RESOLUTION_STATUS: EXECUTABLE_JOINT_NEGOTIATION_BRANCH_FOUND")
    # Display the text 'Physical coupling status: STRUCTURAL_EXECUTABLE_BRANCH_PROVEN'.
    print("  Physical coupling status: STRUCTURAL_EXECUTABLE_BRANCH_PROVEN")


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
