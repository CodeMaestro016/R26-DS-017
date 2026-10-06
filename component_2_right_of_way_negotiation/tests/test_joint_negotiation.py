"""Step 5J.2B.1 joint factor composition tests."""

from dataclasses import FrozenInstanceError

import pytest

from joint_negotiation_validation import real_training_evidence
from negotiation_learning import JointNegotiationBranchEnumerator
from negotiation_learning.protocol import ClaimRelinquishmentProtocol


def synthetic_edges(count):
    return tuple({"yielding_vehicle_id": f"V{i}",
                  "priority_vehicle_id": f"V{i + 1}", "timestamp": 1.0,
                  "applicable_rule_ids": (), "source_sections": (),
                  "shared_conflict_zone_ids": (), "hard_constraint_evidence": {}}
                 for i in range(count))


@pytest.mark.parametrize("count,proposer_count,branch_count", ((2, 4, 9), (3, 8, 27)))
def test_two_and_three_claim_cartesian_products(count, proposer_count, branch_count):
    edges = synthetic_edges(count)
    branches = JointNegotiationBranchEnumerator().enumerate(
        scenario_id=("SYNTHETIC_UNIT_TEST",), source_snapshot_id=("S",),
        original_edges=edges,
        active_vehicle_ids=tuple(f"V{i}" for i in range(count + 1)),
        timestamp=1.0, regulatory_profile="PROFILE",
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE")
    assert len({item.proposer_assignment.claim_action_assignments
                for item in branches}) == proposer_count
    assert len(branches) == branch_count


@pytest.fixture(scope="module")
def evidence(): return real_training_evidence()


def test_real_sumo_snapshot_has_cartesian_proposer_and_responder_products(evidence):
    branches = evidence["branches"]
    proposer = {item.proposer_assignment.claim_action_assignments for item in branches}
    assert len(proposer) == 16  # 2^4 actual source-graph claim factors
    assert len(branches) == 81  # sum over proposer branches: (KEEP + REL*2)^4
    assert max(len(item.responder_assignment.proposal_ids) for item in branches) == 4


def test_keep_creates_no_proposal_and_relinquish_creates_one_per_factor(evidence):
    branches = evidence["branches"]
    keep = next(item for item in branches if not item.proposer_assignment.proposals_created)
    assert keep.branch_status == "JOINT_BRANCH_NO_PROPOSALS"
    assert keep.original_precedence_graph == keep.effective_precedence_graph
    all_relinquish = [item for item in branches if len(
        item.proposer_assignment.proposals_created) == 4]
    assert all_relinquish
    assert all(len(item.responder_assignment.proposal_ids) == 4
               for item in all_relinquish)


def test_partial_and_complete_cycle_removal_are_classified_from_graph(evidence):
    partial = next(item for item in evidence["branches"] if
                   item.branch_status == "JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC")
    complete = evidence["executable"][0]
    assert partial.completed_agreement_ids and partial.cycle_detected
    assert not complete.cycle_detected
    assert complete.graph_executable
    assert complete.execution_plan.graph_status == "EXECUTABLE"
    assert complete.execution_plan.ready_vehicle_ids


def test_agreements_only_remove_their_exact_claims(evidence):
    for branch in evidence["branches"]:
        removed = set(branch.original_precedence_graph) - set(branch.effective_precedence_graph)
        agreed = {(item[1], item[2]) for item in branch.completed_agreement_ids}
        assert removed == agreed


def test_reject_all_preserves_graph_and_has_no_side_effect(evidence):
    rejected = [item for item in evidence["branches"]
                if item.proposer_assignment.proposals_created and
                not item.completed_agreement_ids]
    assert len(rejected) == 15
    assert all(item.original_precedence_graph == item.effective_precedence_graph
               for item in rejected)


def test_factor_order_and_branch_identity_are_deterministic(evidence):
    reordered = evidence["enumerator"].enumerate(
        scenario_id=evidence["scenario_id"],
        source_snapshot_id=evidence["source_snapshot_id"],
        original_edges=tuple(reversed(evidence["edges"])),
        active_vehicle_ids=tuple(reversed(tuple(evidence["movements"]))),
        timestamp=evidence["timestamp"], regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        movement_path_by_vehicle=evidence["movements"])
    assert [item.branch_id for item in reordered] == [
        item.branch_id for item in evidence["branches"]]
    assert [item.effective_precedence_graph for item in reordered] == [
        item.effective_precedence_graph for item in evidence["branches"]]


def test_complete_joint_message_order_is_invariant(evidence):
    branch = evidence["executable"][0]
    protocol = ClaimRelinquishmentProtocol()
    args = (evidence["edges"], branch.protocol_messages, evidence["timestamp"],
            "DE_STVO_UNCONTROLLED_4WAY_V1")
    first = protocol.evaluate_all_claims(*args)
    second = protocol.evaluate_all_claims(
        evidence["edges"], tuple(reversed(branch.protocol_messages)),
        evidence["timestamp"], "DE_STVO_UNCONTROLLED_4WAY_V1")
    assert first == second


def test_joint_records_are_immutable_and_no_heuristic_metadata(evidence):
    branch = evidence["branches"][0]
    with pytest.raises(FrozenInstanceError):
        branch.branch_status = "OTHER"
    assert branch.action_source == "DETERMINISTIC_JOINT_BRANCH_ENUMERATION"
    assert branch.provenance["automatic_edge_removal"] is False
    assert branch.provenance["winner_heuristic"] is False
    assert branch.provenance["joint_protocol_evaluations"] == 1


def test_mask_denial_removes_all_infeasible_joint_branches(evidence):
    result = JointNegotiationBranchEnumerator().enumerate(
        scenario_id=evidence["scenario_id"],
        source_snapshot_id=evidence["source_snapshot_id"],
        original_edges=evidence["edges"],
        active_vehicle_ids=tuple(evidence["movements"]),
        timestamp=evidence["timestamp"], regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
        negotiation_status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        explicit_coordination_permitted=False)
    assert result == ()


def test_frozen_design_and_partition_non_use(evidence):
    assert evidence["design"]["freeze"].freeze_id[0] == "EXPERIMENTAL_DESIGN_FREEZE_V1"
    assert len(evidence["inspected"]) == 1
    assert all(item.scenario_id == evidence["scenario_id"] for item in evidence["branches"])
