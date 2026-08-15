"""Exhaustive deterministic composition of one joint negotiation epoch.

This classifies policy-factor combinations. It never selects a branch,
breaks a cycle, assigns reward, or controls a vehicle.
"""

from dataclasses import dataclass
from itertools import product
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from .claim_semantics import NegotiationClaimBuilder
from .models import NegotiationAction
from .precedence_graph import RegulatoryPrecedenceGraphBuilder
from .protocol import (ClaimRelinquishmentProtocol,
                       NegotiationResponseAction,
                       NegotiationResponseCandidateBuilder, ProposalResponse)

ACTION_SOURCE = "DETERMINISTIC_JOINT_BRANCH_ENUMERATION"


def _frozen(value): return MappingProxyType(dict(value))
def claim_id(claim): return (claim.yielding_vehicle_id, claim.priority_vehicle_id)


@dataclass(frozen=True)
class JointProposerActionAssignment:
    source_snapshot_id: tuple
    claim_action_assignments: Tuple[tuple, ...]
    eligible_claim_ids: Tuple[tuple, ...]
    hard_action_masks: Tuple[tuple, ...]
    proposals_created: Tuple[tuple, ...]
    action_source: str
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance", _frozen(self.provenance))


@dataclass(frozen=True)
class JointResponderActionAssignment:
    source_snapshot_id: tuple
    proposal_ids: Tuple[tuple, ...]
    response_action_assignments: Tuple[tuple, ...]
    hard_response_masks: Tuple[tuple, ...]
    action_source: str
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance", _frozen(self.provenance))


@dataclass(frozen=True)
class JointNegotiationBranchResult:
    branch_id: tuple
    scenario_id: tuple
    source_snapshot_id: tuple
    proposer_assignment: JointProposerActionAssignment
    responder_assignment: JointResponderActionAssignment
    protocol_messages: tuple
    completed_agreement_ids: Tuple[tuple, ...]
    rejected_proposal_ids: Tuple[tuple, ...]
    pending_proposal_ids: Tuple[tuple, ...]
    original_precedence_graph: Tuple[tuple, ...]
    effective_precedence_graph: Tuple[tuple, ...]
    strongly_connected_components: Tuple[tuple, ...]
    cycle_detected: bool
    graph_executable: bool
    branch_status: str
    execution_plan_id: Optional[tuple]
    execution_plan: object
    action_source: str
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance", _frozen(self.provenance))


class JointNegotiationBranchEnumerator:
    """Enumerate all hard-feasible proposer and responder products."""

    def __init__(self, planner=None):
        self.protocol = ClaimRelinquishmentProtocol()
        self.planner = planner

    def eligible_factors(self, *, active_vehicle_ids, original_edges,
                         negotiation_status, explicit_coordination_permitted=True,
                         source_consistent=True):
        factors = {}
        graph = {"joint_precedence_edges": tuple(original_edges)}
        for ego_id in sorted(active_vehicle_ids):
            claim_set = NegotiationClaimBuilder().build(
                ego_id, graph, negotiation_status,
                explicit_coordination_permitted, source_consistent)
            for mask in claim_set.action_masks:
                factors[claim_id(mask.claim)] = (mask.claim, mask)
        return tuple(factors[key] for key in sorted(factors))

    def enumerate(self, *, scenario_id, source_snapshot_id, original_edges,
                  active_vehicle_ids, timestamp, regulatory_profile,
                  negotiation_status, movement_path_by_vehicle=None,
                  explicit_coordination_permitted=True, source_consistent=True):
        original_edges = tuple(original_edges)
        factors = self.eligible_factors(
            active_vehicle_ids=active_vehicle_ids, original_edges=original_edges,
            negotiation_status=negotiation_status,
            explicit_coordination_permitted=explicit_coordination_permitted,
            source_consistent=source_consistent)
        feasible = [tuple(action for action, allowed in zip(
            mask.action_names, mask.feasibility) if allowed)
            for _, mask in factors]
        if any(not actions for actions in feasible):
            return ()
        results = []
        for proposer_actions in product(*feasible):
            proposals, proposer_pairs = [], []
            for (claim, mask), action in zip(factors, proposer_actions):
                cid = claim_id(claim)
                proposer_pairs.append((cid, action.value))
                if action is NegotiationAction.RELINQUISH_CLAIM:
                    proposals.append(self.protocol.create_proposal(
                        claim, timestamp, regulatory_profile, mask.policy_authority))
            proposals.sort(key=lambda item: item.proposal_id)
            proposer = JointProposerActionAssignment(
                source_snapshot_id, tuple(proposer_pairs),
                tuple(claim_id(item[0]) for item in factors),
                tuple((claim_id(claim), tuple(mask.feasibility)) for claim, mask in factors),
                tuple(item.proposal_id for item in proposals), ACTION_SOURCE,
                {"phase": "JOINT_PROPOSER_DECISION_EVENT", "source_graph_immutable": True})
            candidates = tuple(NegotiationResponseCandidateBuilder.build(
                proposal.receiver_id, proposal, original_edges, timestamp,
                regulatory_profile, source_consistent, True) for proposal in proposals)
            spaces = [tuple(action for action, allowed in zip(
                candidate.available_response_actions, candidate.action_feasibility_mask)
                if allowed) for candidate in candidates]
            response_products = product(*spaces) if spaces else [()]
            for response_actions in response_products:
                responses, response_pairs = [], []
                for proposal, action in zip(proposals, response_actions):
                    semantic = (ProposalResponse.ACCEPT if action is
                                NegotiationResponseAction.ACCEPT_RELINQUISHMENT
                                else ProposalResponse.REJECT)
                    responses.append(self.protocol.create_response(
                        proposal, proposal.receiver_id, semantic, timestamp,
                        regulatory_profile))
                    response_pairs.append((proposal.proposal_id, action.value))
                responder = JointResponderActionAssignment(
                    source_snapshot_id, tuple(item.proposal_id for item in proposals),
                    tuple(response_pairs),
                    tuple((item.proposal_id, tuple(item.action_feasibility_mask))
                          for item in candidates), ACTION_SOURCE,
                    {"phase": "JOINT_RESPONDER_DECISION_EVENT",
                     "all_proposals_created_before_responses": True})
                messages = tuple(proposals + responses)
                snapshot = self.protocol.evaluate_all_claims(
                    original_edges, messages, timestamp, regulatory_profile,
                    True, source_consistent)
                graph = snapshot.effective_coordination_graph
                analysis = RegulatoryPrecedenceGraphBuilder.analyse(
                    tuple(sorted(active_vehicle_ids)), tuple(
                        {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                        for a, b in graph))
                cyclic = bool(analysis["cycle_detected"])
                blocked = bool(snapshot.blocked_protocol_items)
                disagreement = bool(snapshot.protocol_disagreements)
                if disagreement: status = "JOINT_BRANCH_PROTOCOL_DISAGREEMENT"
                elif blocked: status = "JOINT_BRANCH_PROTOCOL_BLOCKED"
                elif not proposals: status = "JOINT_BRANCH_NO_PROPOSALS"
                elif snapshot.completed_agreements and cyclic:
                    status = "JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC"
                elif not snapshot.completed_agreements:
                    status = "JOINT_BRANCH_PROPOSALS_REJECTED"
                else: status = "JOINT_BRANCH_EXECUTABLE_ACYCLIC"
                plan = None
                if not cyclic and not blocked and not disagreement and self.planner:
                    plan = self.planner.plan(
                        source_snapshot_id=source_snapshot_id,
                        effective_coordination_graph=graph,
                        active_vehicle_ids=active_vehicle_ids,
                        movement_path_by_vehicle=movement_path_by_vehicle,
                        timestamp=timestamp, source_protocol_state=status,
                        cleared_vehicle_zones=())
                executable = bool(plan and plan.graph_status == "EXECUTABLE")
                branch_id = ("JOINT_NEGOTIATION_BRANCH_V1", source_snapshot_id,
                             tuple(proposer_pairs), tuple(response_pairs), regulatory_profile)
                results.append(JointNegotiationBranchResult(
                    branch_id, scenario_id, source_snapshot_id, proposer, responder,
                    messages, tuple(item.proposal_id for item in snapshot.completed_agreements),
                    tuple(item.proposal_id for item in snapshot.rejected_proposals),
                    tuple(item.proposal_id for item in snapshot.pending_proposals),
                    snapshot.original_regulatory_precedence_graph, graph,
                    tuple(tuple(item) for item in analysis["strongly_connected_components"]),
                    cyclic, executable, status, plan.plan_id if plan else None, plan,
                    ACTION_SOURCE, {"joint_protocol_evaluations": 1,
                                    "automatic_edge_removal": False,
                                    "winner_heuristic": False}))
        return tuple(sorted(results, key=lambda item: item.branch_id))
