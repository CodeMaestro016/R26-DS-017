"""Step 5J.2B.1 joint factor composition tests."""

# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest

# Import real_training_evidence from joint_negotiation_validation for the operations below.
from joint_negotiation_validation import real_training_evidence
# Import JointNegotiationBranchEnumerator from negotiation_learning for the operations below.
from negotiation_learning import JointNegotiationBranchEnumerator
# Import ClaimRelinquishmentProtocol from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import ClaimRelinquishmentProtocol


# Synthetic edges using the inputs and processing steps below.
# Input count: the supplied count.
# Output: a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id, priority_vehicle_id,
# timestamp, applicable_rule_ids,... for i in the integer range defined by count.
def synthetic_edges(count):
    # Return a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
    # priority_vehicle_id, timestamp, applicable_rule_ids,... for i in the integer range defined by count to the
    # caller.
    return tuple({"yielding_vehicle_id": f"V{i}",
                  # Store formatted text built from the embedded values under 'priority_vehicle_id'.
                  # Store 1.0 under 'timestamp'.
                  "priority_vehicle_id": f"V{i + 1}", "timestamp": 1.0,
                  # Store an empty tuple under 'applicable_rule_ids'.
                  # Store an empty tuple under 'source_sections'.
                  "applicable_rule_ids": (), "source_sections": (),
                  # Store an empty tuple under 'shared_conflict_zone_ids'.
                  # Store an empty dictionary under 'hard_constraint_evidence'.
                  "shared_conflict_zone_ids": (), "hard_constraint_evidence": {}}
                 # Evaluate the integer range defined by count as part of the enclosing expression.
                 for i in range(count))


# Apply pytest.mark.parametrize('count,proposer_count,branch_count', ((2, 4, 9), (3, 8, 27))) as a decorator to
# configure the following definition.
@pytest.mark.parametrize("count,proposer_count,branch_count", ((2, 4, 9), (3, 8, 27)))
# Check two and three claim cartesian products using the setup, calls, and assertions below.
# Input count: the supplied count.
# Input proposer_count: the supplied proposer count.
# Input branch_count: the supplied branch count.
# Output: no explicit value; normal completion returns None.
def test_two_and_three_claim_cartesian_products(count, proposer_count, branch_count):
    # Set edges to the result of synthetic_edges(count).
    edges = synthetic_edges(count)
    # Set branches to the result of JointNegotiationBranchEnumerator().enumerate().
    branches = JointNegotiationBranchEnumerator().enumerate(
        # Supply scenario_id as a tuple containing the text 'SYNTHETIC_UNIT_TEST'.
        # Supply source_snapshot_id as a tuple containing the text 'S'.
        scenario_id=("SYNTHETIC_UNIT_TEST",), source_snapshot_id=("S",),
        # Supply original_edges as edges.
        original_edges=edges,
        # Supply active_vehicle_ids as a tuple built from a lazy sequence of formatted text built from the
        # embedded values for i in the integer range defined by count plus 1.
        active_vehicle_ids=tuple(f"V{i}" for i in range(count + 1)),
        # Supply timestamp as 1.0.
        # Supply regulatory_profile as the text 'PROFILE'.
        timestamp=1.0, regulatory_profile="PROFILE",
        # Supply negotiation_status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE")
    # Require the number of entries in a set of item.proposer_assignment.claim_action_assignments for item in
    # branches equals proposer_count; otherwise raise AssertionError.
    assert len({item.proposer_assignment.claim_action_assignments
                # Evaluate proposer_count as part of the enclosing expression.
                for item in branches}) == proposer_count
    # Require the number of entries in branches equals branch_count; otherwise raise AssertionError.
    assert len(branches) == branch_count


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Evidence using the inputs and processing steps below.
# Output: the result of real_training_evidence().
# Return the result of real_training_evidence() to the caller.
def evidence(): return real_training_evidence()


# Check real sumo snapshot has cartesian proposer and responder products using the setup, calls, and assertions
# below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_real_sumo_snapshot_has_cartesian_proposer_and_responder_products(evidence):
    # Set branches to evidence at 'branches'.
    branches = evidence["branches"]
    # Set proposer to a set of item.proposer_assignment.claim_action_assignments for item in branches.
    proposer = {item.proposer_assignment.claim_action_assignments for item in branches}
    # Require the number of entries in proposer equals 16; otherwise raise AssertionError.
    assert len(proposer) == 16  # 2^4 actual source-graph claim factors
    # Require the number of entries in branches equals 81; otherwise raise AssertionError.
    assert len(branches) == 81  # sum over proposer branches: (KEEP + REL*2)^4
    # Require the maximum of a lazy sequence of the number of entries in item.responder_assignment.proposal_ids
    # for item in... equals 4; otherwise raise AssertionError.
    assert max(len(item.responder_assignment.proposal_ids) for item in branches) == 4


# Check keep creates no proposal and relinquish creates one per factor using the setup, calls, and assertions
# below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_keep_creates_no_proposal_and_relinquish_creates_one_per_factor(evidence):
    # Set branches to evidence at 'branches'.
    branches = evidence["branches"]
    # Set keep to the next item from a lazy sequence of item for item in branches; retain entries satisfying the
    # negation of item.proposer_assignment.proposals_created.
    keep = next(item for item in branches if not item.proposer_assignment.proposals_created)
    # Require keep.branch_status equals the text 'JOINT_BRANCH_NO_PROPOSALS'; otherwise raise AssertionError.
    assert keep.branch_status == "JOINT_BRANCH_NO_PROPOSALS"
    # Require keep.original_precedence_graph equals keep.effective_precedence_graph; otherwise raise
    # AssertionError.
    assert keep.original_precedence_graph == keep.effective_precedence_graph
    # Set all_relinquish to a list of item for item in branches; retain entries satisfying the number of entries
    # in item.proposer_assignment.proposals_created equals 4.
    all_relinquish = [item for item in branches if len(
        # Supply item.proposer_assignment.proposals_created to len.
        item.proposer_assignment.proposals_created) == 4]
    # Require all_relinquish; otherwise raise AssertionError.
    assert all_relinquish
    # Require whether every item is true in a lazy sequence of the number of entries in
    # item.responder_assignment.proposal_ids equals 4 for item in all_relinquish; otherwise raise AssertionError.
    assert all(len(item.responder_assignment.proposal_ids) == 4
               # Evaluate all_relinquish as part of the enclosing expression.
               for item in all_relinquish)


# Check partial and complete cycle removal are classified from graph using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_partial_and_complete_cycle_removal_are_classified_from_graph(evidence):
    # Set partial to the next item from a lazy sequence of item for item in evidence at 'branches'; retain entries
    # satisfying item.branch_status equals the text 'JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC'.
    partial = next(item for item in evidence["branches"] if
                   # Evaluate item.branch_status equals the text 'JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC' as
                   # part of the enclosing expression.
                   item.branch_status == "JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC")
    # Set complete to evidence['executable'] at 0.
    complete = evidence["executable"][0]
    # Require partial.completed_agreement_ids and partial.cycle_detected; otherwise raise AssertionError.
    assert partial.completed_agreement_ids and partial.cycle_detected
    # Require the negation of complete.cycle_detected; otherwise raise AssertionError.
    assert not complete.cycle_detected
    # Require complete.graph_executable; otherwise raise AssertionError.
    assert complete.graph_executable
    # Require complete.execution_plan.graph_status equals the text 'EXECUTABLE'; otherwise raise AssertionError.
    assert complete.execution_plan.graph_status == "EXECUTABLE"
    # Require complete.execution_plan.ready_vehicle_ids; otherwise raise AssertionError.
    assert complete.execution_plan.ready_vehicle_ids


# Check agreements only remove their exact claims using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_agreements_only_remove_their_exact_claims(evidence):
    # Iterate over evidence at 'branches', binding each item to branch.
    for branch in evidence["branches"]:
        # Set removed to a set built from branch.original_precedence_graph minus a set built from
        # branch.effective_precedence_graph.
        removed = set(branch.original_precedence_graph) - set(branch.effective_precedence_graph)
        # Set agreed to a set of a tuple containing item at 1, item at 2 for item in
        # branch.completed_agreement_ids.
        agreed = {(item[1], item[2]) for item in branch.completed_agreement_ids}
        # Require removed equals agreed; otherwise raise AssertionError.
        assert removed == agreed


# Check reject all preserves graph and has no side effect using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_reject_all_preserves_graph_and_has_no_side_effect(evidence):
    # Set rejected to a list of item for item in evidence at 'branches'; retain entries satisfying
    # item.proposer_assignment.proposals_created and the negation of...
    rejected = [item for item in evidence["branches"]
                # Evaluate item.proposer_assignment.proposals_created and the negation of
                # item.completed_agreement_ids as part of the enclosing expression.
                if item.proposer_assignment.proposals_created and
                # Evaluate the negation of item.completed_agreement_ids as part of the enclosing expression.
                not item.completed_agreement_ids]
    # Require the number of entries in rejected equals 15; otherwise raise AssertionError.
    assert len(rejected) == 15
    # Require whether every item is true in a lazy sequence of item.original_precedence_graph equals
    # item.effective_precedence_graph for item in rejected; otherwise raise AssertionError.
    assert all(item.original_precedence_graph == item.effective_precedence_graph
               # Evaluate rejected as part of the enclosing expression.
               for item in rejected)


# Check factor order and branch identity are deterministic using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_factor_order_and_branch_identity_are_deterministic(evidence):
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
    # Require a list of item.branch_id for item in reordered equals a list of item.branch_id for item in evidence
    # at 'branches'; otherwise raise AssertionError.
    assert [item.branch_id for item in reordered] == [
        # Evaluate evidence at 'branches' as part of the enclosing expression.
        item.branch_id for item in evidence["branches"]]
    # Require a list of item.effective_precedence_graph for item in reordered equals a list of
    # item.effective_precedence_graph for item in evidence at 'branches'; otherwise raise AssertionError.
    assert [item.effective_precedence_graph for item in reordered] == [
        # Evaluate item.effective_precedence_graph as part of the enclosing expression.
        item.effective_precedence_graph for item in evidence["branches"]]


# Check complete joint message order is invariant using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_complete_joint_message_order_is_invariant(evidence):
    # Set branch to evidence['executable'] at 0.
    branch = evidence["executable"][0]
    # Set protocol to the result of ClaimRelinquishmentProtocol().
    protocol = ClaimRelinquishmentProtocol()
    # Set args to a tuple containing evidence at 'edges', branch.protocol_messages, evidence at 'timestamp', the
    # text...
    args = (evidence["edges"], branch.protocol_messages, evidence["timestamp"],
            "DE_STVO_UNCONTROLLED_4WAY_V1")
    # Set first to the result of protocol.evaluate_all_claims(the unpacked values from args).
    first = protocol.evaluate_all_claims(*args)
    # Set second to the result of protocol.evaluate_all_claims(evidence at 'edges', a tuple built from the reverse
    # traversal of branch.protocol_messages,...).
    second = protocol.evaluate_all_claims(
        # Supply a tuple built from the reverse traversal of branch.protocol_messages to
        # protocol.evaluate_all_claims.
        evidence["edges"], tuple(reversed(branch.protocol_messages)),
        # Supply evidence at 'timestamp' to protocol.evaluate_all_claims.
        evidence["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
    # Require first equals second; otherwise raise AssertionError.
    assert first == second


# Check joint records are immutable and no heuristic metadata using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_joint_records_are_immutable_and_no_heuristic_metadata(evidence):
    # Set branch to evidence['branches'] at 0.
    branch = evidence["branches"][0]
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set branch.branch_status to the text 'OTHER'.
        branch.branch_status = "OTHER"
    # Require branch.action_source equals the text 'DETERMINISTIC_JOINT_BRANCH_ENUMERATION'; otherwise raise
    # AssertionError.
    assert branch.action_source == "DETERMINISTIC_JOINT_BRANCH_ENUMERATION"
    # Require branch.provenance at 'automatic_edge_removal' is the same object as False; otherwise raise
    # AssertionError.
    assert branch.provenance["automatic_edge_removal"] is False
    # Require branch.provenance at 'winner_heuristic' is the same object as False; otherwise raise AssertionError.
    assert branch.provenance["winner_heuristic"] is False
    # Require branch.provenance at 'joint_protocol_evaluations' equals 1; otherwise raise AssertionError.
    assert branch.provenance["joint_protocol_evaluations"] == 1


# Check mask denial removes all infeasible joint branches using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_mask_denial_removes_all_infeasible_joint_branches(evidence):
    # Set result to the result of JointNegotiationBranchEnumerator().enumerate().
    result = JointNegotiationBranchEnumerator().enumerate(
        # Supply scenario_id as evidence at 'scenario_id'.
        scenario_id=evidence["scenario_id"],
        # Supply source_snapshot_id as evidence at 'source_snapshot_id'.
        source_snapshot_id=evidence["source_snapshot_id"],
        # Supply original_edges as evidence at 'edges'.
        original_edges=evidence["edges"],
        # Supply active_vehicle_ids as a tuple built from evidence at 'movements'.
        active_vehicle_ids=tuple(evidence["movements"]),
        # Supply timestamp as evidence at 'timestamp'.
        # Supply regulatory_profile as the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
        timestamp=evidence["timestamp"], regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
        # Supply negotiation_status as the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE'.
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        # Supply explicit_coordination_permitted as False.
        explicit_coordination_permitted=False)
    # Require result equals an empty tuple; otherwise raise AssertionError.
    assert result == ()


# Check frozen design and partition non use using the setup, calls, and assertions below.
# Input evidence: the supplied evidence.
# Output: no explicit value; normal completion returns None.
def test_frozen_design_and_partition_non_use(evidence):
    # Require evidence['design']['freeze'].freeze_id at 0 equals the text 'EXPERIMENTAL_DESIGN_FREEZE_V1';
    # otherwise raise AssertionError.
    assert evidence["design"]["freeze"].freeze_id[0] == "EXPERIMENTAL_DESIGN_FREEZE_V1"
    # Require the number of entries in evidence at 'inspected' equals 1; otherwise raise AssertionError.
    assert len(evidence["inspected"]) == 1
    # Require whether every item is true in a lazy sequence of item.scenario_id equals evidence at 'scenario_id'
    # for item in evidence at 'branches'; otherwise raise AssertionError.
    assert all(item.scenario_id == evidence["scenario_id"] for item in evidence["branches"])
