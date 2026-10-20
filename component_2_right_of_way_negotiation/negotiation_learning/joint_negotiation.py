"""Exhaustive deterministic composition of one joint negotiation epoch.

This classifies policy-factor combinations. It never selects a branch,
breaks a cycle, assigns reward, or controls a vehicle.
"""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import product from itertools for the operations below.
from itertools import product
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple

# Import NegotiationClaimBuilder from .claim_semantics for the operations below.
from .claim_semantics import NegotiationClaimBuilder
# Import NegotiationAction from .models for the operations below.
from .models import NegotiationAction
# Import RegulatoryPrecedenceGraphBuilder from .precedence_graph for the operations below.
from .precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import ClaimRelinquishmentProtocol, NegotiationResponseAction, NegotiationResponseCandidateBuilder,
# ProposalResponse from .protocol for the operations below.
from .protocol import (ClaimRelinquishmentProtocol,
                       NegotiationResponseAction,
                       NegotiationResponseCandidateBuilder, ProposalResponse)

# Set ACTION_SOURCE to the text 'DETERMINISTIC_JOINT_BRANCH_ENUMERATION'.
ACTION_SOURCE = "DETERMINISTIC_JOINT_BRANCH_ENUMERATION"


# Frozen using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of MappingProxyType(a dictionary built from value).
# Return the result of MappingProxyType(a dictionary built from value) to the caller.
def _frozen(value): return MappingProxyType(dict(value))
# Claim id using the inputs and processing steps below.
# Input claim: the supplied claim.
# Output: a tuple containing claim.yielding_vehicle_id, claim.priority_vehicle_id.
# Return a tuple containing claim.yielding_vehicle_id, claim.priority_vehicle_id to the caller.
def claim_id(claim): return (claim.yielding_vehicle_id, claim.priority_vehicle_id)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointProposerActionAssignment to group the state and operations declared below.
# Declared fields: source_snapshot_id, claim_action_assignments, eligible_claim_ids, hard_action_masks,
# proposals_created, action_source, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class JointProposerActionAssignment:
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare claim_action_assignments as Tuple[tuple, ...] for this data structure.
    claim_action_assignments: Tuple[tuple, ...]
    # Declare eligible_claim_ids as Tuple[tuple, ...] for this data structure.
    eligible_claim_ids: Tuple[tuple, ...]
    # Declare hard_action_masks as Tuple[tuple, ...] for this data structure.
    hard_action_masks: Tuple[tuple, ...]
    # Declare proposals_created as Tuple[tuple, ...] for this data structure.
    proposals_created: Tuple[tuple, ...]
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _frozen(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointResponderActionAssignment to group the state and operations declared below.
# Declared fields: source_snapshot_id, proposal_ids, response_action_assignments, hard_response_masks,
# action_source, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class JointResponderActionAssignment:
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare proposal_ids as Tuple[tuple, ...] for this data structure.
    proposal_ids: Tuple[tuple, ...]
    # Declare response_action_assignments as Tuple[tuple, ...] for this data structure.
    response_action_assignments: Tuple[tuple, ...]
    # Declare hard_response_masks as Tuple[tuple, ...] for this data structure.
    hard_response_masks: Tuple[tuple, ...]
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _frozen(self.provenance))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define JointNegotiationBranchResult to group the state and operations declared below.
# Declared fields: branch_id, scenario_id, source_snapshot_id, proposer_assignment, responder_assignment,
# protocol_messages, completed_agreement_ids, rejected_proposal_ids, pending_proposal_ids,
# original_precedence_graph,....
# Construction and attribute behavior follow the declared decorators and base classes.
class JointNegotiationBranchResult:
    # Declare branch_id as tuple for this data structure.
    branch_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare proposer_assignment as JointProposerActionAssignment for this data structure.
    proposer_assignment: JointProposerActionAssignment
    # Declare responder_assignment as JointResponderActionAssignment for this data structure.
    responder_assignment: JointResponderActionAssignment
    # Declare protocol_messages as tuple for this data structure.
    protocol_messages: tuple
    # Declare completed_agreement_ids as Tuple[tuple, ...] for this data structure.
    completed_agreement_ids: Tuple[tuple, ...]
    # Declare rejected_proposal_ids as Tuple[tuple, ...] for this data structure.
    rejected_proposal_ids: Tuple[tuple, ...]
    # Declare pending_proposal_ids as Tuple[tuple, ...] for this data structure.
    pending_proposal_ids: Tuple[tuple, ...]
    # Declare original_precedence_graph as Tuple[tuple, ...] for this data structure.
    original_precedence_graph: Tuple[tuple, ...]
    # Declare effective_precedence_graph as Tuple[tuple, ...] for this data structure.
    effective_precedence_graph: Tuple[tuple, ...]
    # Declare strongly_connected_components as Tuple[tuple, ...] for this data structure.
    strongly_connected_components: Tuple[tuple, ...]
    # Declare cycle_detected as bool for this data structure.
    cycle_detected: bool
    # Declare graph_executable as bool for this data structure.
    graph_executable: bool
    # Declare branch_status as str for this data structure.
    branch_status: str
    # Declare execution_plan_id as Optional[tuple] for this data structure.
    execution_plan_id: Optional[tuple]
    # Declare execution_plan as object for this data structure.
    execution_plan: object
    # Declare action_source as str for this data structure.
    action_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", _frozen(self.provenance))


# Enumerate all hard-feasible proposer and responder products.
# Instances expose the attributes and methods implemented in this class.
class JointNegotiationBranchEnumerator:
    """Enumerate all hard-feasible proposer and responder products."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input planner: the supplied planner.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, planner=None):
        # Set self.protocol to the result of ClaimRelinquishmentProtocol().
        self.protocol = ClaimRelinquishmentProtocol()
        # Set self.planner to planner.
        self.planner = planner

    # Eligible factors using the inputs and processing steps below.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input original_edges: the supplied original edges.
    # Input negotiation_status: the supplied negotiation status.
    # Input explicit_coordination_permitted: the supplied explicit coordination permitted.
    # Input source_consistent: the supplied source consistent.
    # Output: a tuple built from a lazy sequence of factors at key for key in the sorted values from factors.
    # Processing: iterate over the relevant records.
    def eligible_factors(self, *, active_vehicle_ids, original_edges,
                         # Declare negotiation_status, explicit_coordination_permitted as input parameters.
                         negotiation_status, explicit_coordination_permitted=True,
                         # Declare source_consistent as input parameter.
                         source_consistent=True):
        # Set factors to an empty dictionary.
        factors = {}
        # Set graph to a dictionary containing joint_precedence_edges.
        graph = {"joint_precedence_edges": tuple(original_edges)}
        # Iterate over the sorted values from active_vehicle_ids, binding each item to ego_id.
        for ego_id in sorted(active_vehicle_ids):
            # Set claim_set to the result of NegotiationClaimBuilder().build(ego_id, graph, negotiation_status,
            # explicit_coordination_permitted, source_consistent).
            claim_set = NegotiationClaimBuilder().build(
                # Supply negotiation_status to NegotiationClaimBuilder().build.
                ego_id, graph, negotiation_status,
                # Supply explicit_coordination_permitted to NegotiationClaimBuilder().build.
                explicit_coordination_permitted, source_consistent)
            # Iterate over claim_set.action_masks, binding each item to mask.
            for mask in claim_set.action_masks:
                # Set factors[claim_id(mask.claim)] to a tuple containing mask.claim, mask.
                factors[claim_id(mask.claim)] = (mask.claim, mask)
        # Return a tuple built from a lazy sequence of factors at key for key in the sorted values from factors to
        # the caller.
        return tuple(factors[key] for key in sorted(factors))

    # Enumerate using the inputs and processing steps below.
    # Input scenario_id: the supplied scenario id.
    # Input source_snapshot_id: the supplied source snapshot id.
    # Input original_edges: the supplied original edges.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input timestamp: the supplied timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input negotiation_status: the supplied negotiation status.
    # Input movement_path_by_vehicle: the supplied movement path by vehicle.
    # Input explicit_coordination_permitted: the supplied explicit coordination permitted.
    # Input source_consistent: the supplied source consistent.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def enumerate(self, *, scenario_id, source_snapshot_id, original_edges,
                  # Declare active_vehicle_ids, timestamp, regulatory_profile as input parameters.
                  active_vehicle_ids, timestamp, regulatory_profile,
                  # Declare negotiation_status, movement_path_by_vehicle as input parameters.
                  negotiation_status, movement_path_by_vehicle=None,
                  # Declare explicit_coordination_permitted, source_consistent as input parameters.
                  explicit_coordination_permitted=True, source_consistent=True):
        # Set original_edges to a tuple built from original_edges.
        original_edges = tuple(original_edges)
        # Set factors to the result of self.eligible_factors().
        factors = self.eligible_factors(
            # Supply active_vehicle_ids as active_vehicle_ids.
            # Supply original_edges as original_edges.
            active_vehicle_ids=active_vehicle_ids, original_edges=original_edges,
            # Supply negotiation_status as negotiation_status.
            negotiation_status=negotiation_status,
            # Supply explicit_coordination_permitted as explicit_coordination_permitted.
            explicit_coordination_permitted=explicit_coordination_permitted,
            # Supply source_consistent as source_consistent.
            source_consistent=source_consistent)
        # Set feasible to a list of a tuple built from a lazy sequence of action for (action, allowed) in
        # corresponding items paired from mask.action_names, mask.feasibility; retain entries satisfying allowed
        # for (_, mask) in factors.
        feasible = [tuple(action for action, allowed in zip(
            # Supply mask.action_names to zip.
            mask.action_names, mask.feasibility) if allowed)
            # Evaluate a tuple containing _, mask as part of the enclosing expression.
            for _, mask in factors]
        # Run this branch when whether any item is true in a lazy sequence of the negation of actions for actions
        # in feasible.
        if any(not actions for actions in feasible):
            # Return an empty tuple to the caller.
            return ()
        # Set results to an empty list.
        results = []
        # Iterate over the result of product(the unpacked values from feasible), binding each item to
        # proposer_actions.
        for proposer_actions in product(*feasible):
            # Set (proposals, proposer_pairs) to a tuple containing an empty list, an empty list.
            proposals, proposer_pairs = [], []
            # Iterate over corresponding items paired from factors, proposer_actions, binding each item to
            # ((claim, mask), action).
            for (claim, mask), action in zip(factors, proposer_actions):
                # Set cid to the result of claim_id(claim).
                cid = claim_id(claim)
                # Append a tuple containing cid, action.value to proposer_pairs.
                proposer_pairs.append((cid, action.value))
                # Run this branch when action is the same object as NegotiationAction.RELINQUISH_CLAIM.
                if action is NegotiationAction.RELINQUISH_CLAIM:
                    # Append the result of self.protocol.create_proposal(claim, timestamp, regulatory_profile,
                    # mask.policy_authority) to proposals.
                    proposals.append(self.protocol.create_proposal(
                        # Supply mask.policy_authority to self.protocol.create_proposal.
                        claim, timestamp, regulatory_profile, mask.policy_authority))
            # Call proposals.sort with the supplied arguments.
            proposals.sort(key=lambda item: item.proposal_id)
            # Set proposer to the result of JointProposerActionAssignment(source_snapshot_id, a tuple built from
            # proposer_pairs, a tuple built from a lazy sequence of the...).
            proposer = JointProposerActionAssignment(
                # Supply a tuple built from proposer_pairs to JointProposerActionAssignment.
                source_snapshot_id, tuple(proposer_pairs),
                # Supply a tuple built from a lazy sequence of the result of claim_id(item at 0) for item in
                # factors to JointProposerActionAssignment.
                tuple(claim_id(item[0]) for item in factors),
                # Supply a tuple built from a lazy sequence of a tuple containing the result of claim_id(claim), a
                # tuple built from mask.feasibility for (claim, mask) in factors to JointProposerActionAssignment.
                tuple((claim_id(claim), tuple(mask.feasibility)) for claim, mask in factors),
                # Supply a tuple built from a lazy sequence of item.proposal_id for item in proposals to
                # JointProposerActionAssignment.
                tuple(item.proposal_id for item in proposals), ACTION_SOURCE,
                # Store the text 'JOINT_PROPOSER_DECISION_EVENT' under 'phase'.
                # Store True under 'source_graph_immutable'.
                {"phase": "JOINT_PROPOSER_DECISION_EVENT", "source_graph_immutable": True})
            # Set candidates to a tuple built from a lazy sequence of the result of
            # NegotiationResponseCandidateBuilder.build(proposal.receiver_id, proposal, original_edges, timestamp,
            # regulatory_profile,...) for proposal in proposals.
            candidates = tuple(NegotiationResponseCandidateBuilder.build(
                # Supply proposal.receiver_id to NegotiationResponseCandidateBuilder.build.
                proposal.receiver_id, proposal, original_edges, timestamp,
                # Supply regulatory_profile to NegotiationResponseCandidateBuilder.build.
                regulatory_profile, source_consistent, True) for proposal in proposals)
            # Set spaces to a list of a tuple built from a lazy sequence of action for (action, allowed) in
            # corresponding items paired from candidate.available_response_actions,
            # candidate.action_feasibility_mask; retain entries satisfying allowed for candidate in candidates.
            spaces = [tuple(action for action, allowed in zip(
                # Supply candidate.available_response_actions to zip.
                candidate.available_response_actions, candidate.action_feasibility_mask)
                # Evaluate candidates as part of the enclosing expression.
                if allowed) for candidate in candidates]
            # Set response_products to the result of product(the unpacked values from spaces) when spaces,
            # otherwise a list containing an empty tuple.
            response_products = product(*spaces) if spaces else [()]
            # Iterate over response_products, binding each item to response_actions.
            for response_actions in response_products:
                # Set (responses, response_pairs) to a tuple containing an empty list, an empty list.
                responses, response_pairs = [], []
                # Iterate over corresponding items paired from proposals, response_actions, binding each item to
                # (proposal, action).
                for proposal, action in zip(proposals, response_actions):
                    # Set semantic to ProposalResponse.ACCEPT when action is the same object as
                    # NegotiationResponseAction.ACCEPT_RELINQUISHMENT, otherwise ProposalResponse.REJECT.
                    semantic = (ProposalResponse.ACCEPT if action is
                                # Evaluate NegotiationResponseAction.ACCEPT_RELINQUISHMENT as part of the
                                # enclosing expression.
                                NegotiationResponseAction.ACCEPT_RELINQUISHMENT
                                # Evaluate ProposalResponse.REJECT as part of the enclosing expression.
                                else ProposalResponse.REJECT)
                    # Append the result of self.protocol.create_response(proposal, proposal.receiver_id, semantic,
                    # timestamp, regulatory_profile) to responses.
                    responses.append(self.protocol.create_response(
                        # Supply proposal.receiver_id to self.protocol.create_response.
                        proposal, proposal.receiver_id, semantic, timestamp,
                        # Supply regulatory_profile to self.protocol.create_response.
                        regulatory_profile))
                    # Append a tuple containing proposal.proposal_id, action.value to response_pairs.
                    response_pairs.append((proposal.proposal_id, action.value))
                # Set responder to the result of JointResponderActionAssignment(source_snapshot_id, a tuple built
                # from a lazy sequence of item.proposal_id for item in...).
                responder = JointResponderActionAssignment(
                    # Supply a tuple built from a lazy sequence of item.proposal_id for item in proposals to
                    # JointResponderActionAssignment.
                    source_snapshot_id, tuple(item.proposal_id for item in proposals),
                    # Supply a tuple built from response_pairs to JointResponderActionAssignment.
                    tuple(response_pairs),
                    # Supply a tuple built from a lazy sequence of a tuple containing item.proposal_id, a tuple
                    # built from item.action_feasibility_mask for item in candidates to
                    # JointResponderActionAssignment.
                    tuple((item.proposal_id, tuple(item.action_feasibility_mask))
                          # Supply ACTION_SOURCE to JointResponderActionAssignment.
                          for item in candidates), ACTION_SOURCE,
                    # Store the text 'JOINT_RESPONDER_DECISION_EVENT' under 'phase'.
                    {"phase": "JOINT_RESPONDER_DECISION_EVENT",
                     # Store True under 'all_proposals_created_before_responses'.
                     "all_proposals_created_before_responses": True})
                # Set messages to a tuple built from proposals plus responses.
                messages = tuple(proposals + responses)
                # Set snapshot to the result of self.protocol.evaluate_all_claims(original_edges, messages,
                # timestamp, regulatory_profile, True, source_consistent).
                snapshot = self.protocol.evaluate_all_claims(
                    # Supply regulatory_profile to self.protocol.evaluate_all_claims.
                    original_edges, messages, timestamp, regulatory_profile,
                    # Supply source_consistent to self.protocol.evaluate_all_claims.
                    True, source_consistent)
                # Set graph to snapshot.effective_coordination_graph.
                graph = snapshot.effective_coordination_graph
                # Set analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(a tuple built from the
                # sorted values from active_vehicle_ids, a tuple built from a lazy sequence...).
                analysis = RegulatoryPrecedenceGraphBuilder.analyse(
                    # Supply a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
                    # priority_vehicle_id for (a, b) in graph to RegulatoryPrecedenceGraphBuilder.analyse.
                    tuple(sorted(active_vehicle_ids)), tuple(
                        # Store a under 'yielding_vehicle_id'.
                        # Store b under 'priority_vehicle_id'.
                        {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                        # Evaluate graph as part of the enclosing expression.
                        for a, b in graph))
                # Set cyclic to a Boolean built from analysis at 'cycle_detected'.
                cyclic = bool(analysis["cycle_detected"])
                # Set blocked to a Boolean built from snapshot.blocked_protocol_items.
                blocked = bool(snapshot.blocked_protocol_items)
                # Set disagreement to a Boolean built from snapshot.protocol_disagreements.
                disagreement = bool(snapshot.protocol_disagreements)
                # Run this branch when disagreement.
                # Set status to the text 'JOINT_BRANCH_PROTOCOL_DISAGREEMENT'.
                if disagreement: status = "JOINT_BRANCH_PROTOCOL_DISAGREEMENT"
                # Run this branch when blocked.
                # Set status to the text 'JOINT_BRANCH_PROTOCOL_BLOCKED'.
                elif blocked: status = "JOINT_BRANCH_PROTOCOL_BLOCKED"
                # Run this branch when the negation of proposals.
                # Set status to the text 'JOINT_BRANCH_NO_PROPOSALS'.
                elif not proposals: status = "JOINT_BRANCH_NO_PROPOSALS"
                # Run this branch when snapshot.completed_agreements and cyclic.
                elif snapshot.completed_agreements and cyclic:
                    # Set status to the text 'JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC'.
                    status = "JOINT_BRANCH_PARTIALLY_ACCEPTED_STILL_CYCLIC"
                # Run this branch when the negation of snapshot.completed_agreements.
                elif not snapshot.completed_agreements:
                    # Set status to the text 'JOINT_BRANCH_PROPOSALS_REJECTED'.
                    status = "JOINT_BRANCH_PROPOSALS_REJECTED"
                # Set status to the text 'JOINT_BRANCH_EXECUTABLE_ACYCLIC'.
                else: status = "JOINT_BRANCH_EXECUTABLE_ACYCLIC"
                # Set plan to None.
                plan = None
                # Set physical_execution_status to None.
                physical_execution_status = None
                # Run this branch when the negation of cyclic and the negation of blocked and the negation of
                # disagreement and self.planner.
                if not cyclic and not blocked and not disagreement and self.planner:
                    # Set plan_arguments to a dictionary built from the supplied values.
                    plan_arguments = dict(
                        # Supply source_snapshot_id as source_snapshot_id.
                        source_snapshot_id=source_snapshot_id,
                        # Supply effective_coordination_graph as graph.
                        effective_coordination_graph=graph,
                        # Supply active_vehicle_ids as active_vehicle_ids.
                        active_vehicle_ids=active_vehicle_ids,
                        # Supply movement_path_by_vehicle as movement_path_by_vehicle.
                        movement_path_by_vehicle=movement_path_by_vehicle,
                        # Supply timestamp as timestamp.
                        # Supply source_protocol_state as status.
                        timestamp=timestamp, source_protocol_state=status,
                        # Supply cleared_vehicle_zones as an empty tuple.
                        cleared_vehicle_zones=())
                    # Run this branch when whether self.planner exposes the requested attribute.
                    if hasattr(self.planner, "classify_plan"):
                        # Set (plan, physical_execution_status) to the result of self.planner.classify_plan().
                        plan, physical_execution_status = (
                            # Supply the unpacked keyword arguments as plan_arguments.
                            self.planner.classify_plan(**plan_arguments))
                    # Run this alternative branch when the preceding branch does not apply.
                    else:
                        # Set plan to the result of self.planner.plan().
                        plan = self.planner.plan(**plan_arguments)
                # Set executable to a Boolean built from plan and plan.graph_status equals the text 'EXECUTABLE'.
                executable = bool(plan and plan.graph_status == "EXECUTABLE")
                # Run this branch when physical_execution_status.
                if physical_execution_status:
                    # Set status to the text 'JOINT_BRANCH_PHYSICAL_EXECUTION_UNORDERED'.
                    status = "JOINT_BRANCH_PHYSICAL_EXECUTION_UNORDERED"
                # Set branch_id to a tuple containing the text 'JOINT_NEGOTIATION_BRANCH_V1', source_snapshot_id,
                # a tuple built from proposer_pairs, a tuple...
                branch_id = ("JOINT_NEGOTIATION_BRANCH_V1", source_snapshot_id,
                             # Include a tuple built from proposer_pairs in this tuple.
                             tuple(proposer_pairs), tuple(response_pairs), regulatory_profile)
                # Append the result of JointNegotiationBranchResult(branch_id, scenario_id, source_snapshot_id,
                # proposer, responder, messages, a tuple built from a...) to results.
                results.append(JointNegotiationBranchResult(
                    # Supply source_snapshot_id to JointNegotiationBranchResult.
                    branch_id, scenario_id, source_snapshot_id, proposer, responder,
                    # Supply a tuple built from a lazy sequence of item.proposal_id for item in
                    # snapshot.completed_agreements to JointNegotiationBranchResult.
                    messages, tuple(item.proposal_id for item in snapshot.completed_agreements),
                    # Supply a tuple built from a lazy sequence of item.proposal_id for item in
                    # snapshot.rejected_proposals to JointNegotiationBranchResult.
                    tuple(item.proposal_id for item in snapshot.rejected_proposals),
                    # Supply a tuple built from a lazy sequence of item.proposal_id for item in
                    # snapshot.pending_proposals to JointNegotiationBranchResult.
                    tuple(item.proposal_id for item in snapshot.pending_proposals),
                    # Supply snapshot.original_regulatory_precedence_graph to JointNegotiationBranchResult.
                    snapshot.original_regulatory_precedence_graph, graph,
                    # Supply a tuple built from a lazy sequence of a tuple built from item for item in analysis at
                    # 'strongly_connected_components' to JointNegotiationBranchResult.
                    tuple(tuple(item) for item in analysis["strongly_connected_components"]),
                    # Supply plan.plan_id when plan, otherwise None to JointNegotiationBranchResult.
                    cyclic, executable, status, plan.plan_id if plan else None, plan,
                    # Store 1 under 'joint_protocol_evaluations'.
                    ACTION_SOURCE, {"joint_protocol_evaluations": 1,
                                    # Store False under 'automatic_edge_removal'.
                                    "automatic_edge_removal": False,
                                    # Store False under 'winner_heuristic'.
                                    "winner_heuristic": False,
                                    "physical_execution_status":
                                        # Evaluate physical_execution_status as part of the enclosing expression.
                                        physical_execution_status}))
        # Return a tuple built from the sorted values from results to the caller.
        return tuple(sorted(results, key=lambda item: item.branch_id))
