"""One-process qualitative panel runtime composed from existing science layers."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import datetime, timezone from datetime for the operations below.
from datetime import datetime, timezone
# Import hashlib for use in this module.
import hashlib
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import combinations from itertools for the operations below.
from itertools import combinations
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import perf_counter_ns from time for the operations below.
from time import perf_counter_ns

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP from config for the operations below.
from config import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP
# Import ConflictGraphManager, ConflictZoneOccupancyAssessor, ConflictZoneManager, MapPathManager from conflict
# for the operations below.
from conflict import (ConflictGraphManager, ConflictZoneOccupancyAssessor,
                      ConflictZoneManager, MapPathManager)
# Import ConflictEntryMonitor from conflict_entry_monitor for the operations below.
from conflict_entry_monitor import ConflictEntryMonitor
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import EgoExecutionContext, EgoCoordinationCommitment, ExecutionStateMessage,
# DecentralizedEgoExecutionController, ConflictZoneExecutionPlan from negotiation_execution for the operations
# below.
from negotiation_execution import (EgoExecutionContext, EgoCoordinationCommitment,
    ExecutionStateMessage, DecentralizedEgoExecutionController,
    ConflictZoneExecutionPlan)
# Import PhysicalBranchReplayRunner from negotiation_execution.replay for the operations below.
from negotiation_execution.replay import PhysicalBranchReplayRunner
# Import GraphTensorEncoder, NegotiationEnvironment, V2VPrecedenceClaimBus from negotiation_learning for the
# operations below.
from negotiation_learning import (GraphTensorEncoder, NegotiationEnvironment,
                                  V2VPrecedenceClaimBus)
# Import JointLocalPrecedenceGraphAssembler from negotiation_learning.joint_graph_assembler for the operations
# below.
from negotiation_learning.joint_graph_assembler import JointLocalPrecedenceGraphAssembler
# Import MovementDeclarationBus, PROTOCOL_VERSION from negotiation_learning.movement_declarations for the
# operations below.
from negotiation_learning.movement_declarations import MovementDeclarationBus, PROTOCOL_VERSION
# Import EndpointEvidence, VERSION as FALLBACK_VERSION from negotiation_execution.mandatory_fallback for the
# operations below.
from negotiation_execution.mandatory_fallback import EndpointEvidence, VERSION as FALLBACK_VERSION
# Import VERSION as NATIVE_HOLD_VERSION from negotiation_execution.native_hold for the operations below.
from negotiation_execution.native_hold import VERSION as NATIVE_HOLD_VERSION
# Import derive_existing_route_id from negotiation_scenarios.runner for the operations below.
from negotiation_scenarios.runner import derive_existing_route_id
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
# Import _load_bundle from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import _load_bundle
# Import ObservationManager from observation for the operations below.
from observation import ObservationManager
# Import IntentionPredictor from predictor for the operations below.
from predictor import IntentionPredictor
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine

# Import write_panel_outputs from .reporting for the operations below.
from .reporting import write_panel_outputs
# Import ADMISSION_ORDER, ADMISSION_WAVES, INITIAL_ADMISSION_SECONDS, build_default_schedule, validate_schedule,
# validate_presentation_schedule from .schedule for the operations below.
from .schedule import (ADMISSION_ORDER, ADMISSION_WAVES,
                       INITIAL_ADMISSION_SECONDS,
                       build_default_schedule, validate_schedule,
                       validate_presentation_schedule)
# Import PanelDemoVisualizer from .visualization for the operations below.
from .visualization import PanelDemoVisualizer
# Import PanelDeterministicInferenceProvider, PRESENTATION_SELECTION_RULE from .inference for the operations
# below.
from .inference import (PanelDeterministicInferenceProvider,
                        PRESENTATION_SELECTION_RULE)
# Import BrowserStatePublisher, displayed_mappo_invocation from .browser_state for the operations below.
from .browser_state import BrowserStatePublisher, displayed_mappo_invocation
# Import select_queue_heads, approach_queue_depth from .queue_heads for the operations below.
from .queue_heads import select_queue_heads, approach_queue_depth


# Set POLICY_PATH to the result of Path(the text 'results/final_mappo_selection_v2/selected_policy.pt').
POLICY_PATH = Path("results/final_mappo_selection_v2/selected_policy.pt")
# Set SAFE_RUNTIME_OPTIONS to a tuple containing the text '--time-to-teleport', the text '-1'.
SAFE_RUNTIME_OPTIONS = ("--time-to-teleport", "-1")
# Set NEGOTIABLE to a set containing the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE', the text
# 'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE'.
NEGOTIABLE = {"NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
              "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"}
# Set BLOCKED to a set containing the text 'NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED', the text...
BLOCKED = {"NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED",
           "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
           "SOURCE_SNAPSHOT_MISMATCH", "REGULATORY_PROFILE_MISMATCH"}


# Apply dataclass as a decorator to configure the following definition.
@dataclass
# Define _Authority to group the state and operations declared below.
# Declared fields: state_identity, source_snapshot_id, original_graph, effective_graph, status, outcome,
# obligations, initial_plan, zone_states, member_ids, commitment_inboxes, fallback_pairs, mandatory_inboxes,
# shield_recorded.
# Construction and attribute behavior follow the declared decorators and base classes.
class _Authority:
    # Declare state_identity as tuple for this data structure.
    state_identity: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare original_graph as tuple for this data structure.
    original_graph: tuple
    # Declare effective_graph as tuple for this data structure.
    effective_graph: tuple
    # Declare status as str for this data structure.
    status: str
    # Declare outcome as object for this data structure.
    outcome: object
    # Declare obligations as object for this data structure.
    obligations: object
    # Declare initial_plan as object for this data structure.
    initial_plan: object
    # Declare zone_states as dict for this data structure.
    zone_states: dict
    # Declare member_ids as tuple for this data structure.
    member_ids: tuple
    # Declare commitment_inboxes as dict for this data structure.
    commitment_inboxes: dict
    # Set fallback_pairs to an empty tuple; declare its type as tuple.
    fallback_pairs: tuple = ()
    # Set mandatory_inboxes to None; declare its type as object.
    mandatory_inboxes: object = None
    # Set shield_recorded to False; declare its type as bool.
    shield_recorded: bool = False


# Aggregate returned ego decisions for audit/UI ONLY, never for control.
# Input decisions: the supplied decisions.
# Input now: the time used for this operation.
# Input source_id: the supplied source id.
# Output: the result of ConflictZoneExecutionPlan(a tuple containing the text 'EGO_DECISION_AUDIT', now,
# source_id, an empty tuple, a tuple built...).
def _display_plan(decisions, now, source_id=()):
    """Aggregate returned ego decisions for audit/UI ONLY, never for control."""
    # Set ready to a tuple built from a lazy sequence of d.ego_id for d in decisions; retain entries satisfying
    # d.permission equals the text 'PERMITTED'.
    ready = tuple(d.ego_id for d in decisions if d.permission == "PERMITTED")
    # Set blocked to a tuple built from a lazy sequence of d.ego_id for d in decisions; retain entries satisfying
    # d.blocked_zones.
    blocked = tuple(d.ego_id for d in decisions if d.blocked_zones)
    # Return the result of ConflictZoneExecutionPlan(a tuple containing the text 'EGO_DECISION_AUDIT', now,
    # source_id, an empty tuple, a tuple built...) to the caller.
    return ConflictZoneExecutionPlan(("EGO_DECISION_AUDIT", now), source_id,
        # Supply a tuple built from a lazy sequence of d.ego_id for d in decisions to ConflictZoneExecutionPlan.
        (), tuple(d.ego_id for d in decisions), (), (), ready, blocked,
        # Supply the text 'EXECUTABLE' when ready, otherwise the text 'LOCAL_SAFE_HOLD' to
        # ConflictZoneExecutionPlan.
        "EXECUTABLE" if ready else "LOCAL_SAFE_HOLD",
        # Store the text 'RETURNED_EGO_DECISIONS_DISPLAY_ONLY' under 'permission_source'.
        {"permission_source": "RETURNED_EGO_DECISIONS_DISPLAY_ONLY"})


# Transport protocol pair agreements; do not compute permissions here.
# Input effective: the supplied effective.
# Input member_ids: the supplied member ids.
# Input agreement_id: the supplied agreement id.
# Output: a dictionary of ego mapped to a tuple built from rows for (ego, rows) in key/value pairs from inboxes.
# Processing: iterate over the relevant records.
def _deliver_pair_commitments(effective, member_ids, agreement_id):
    """Transport protocol pair agreements; do not compute permissions here."""
    # Set inboxes to a dictionary of ego mapped to an empty list for ego in member_ids.
    inboxes = {ego: [] for ego in member_ids}
    # Iterate over effective, binding each item to (yielding, priority).
    for yielding, priority in effective:
        # Set message to the result of EgoCoordinationCommitment(yielding, priority, agreement_id).
        message = EgoCoordinationCommitment(yielding, priority, agreement_id)
        # Iterate over a tuple containing yielding, priority, binding each item to receiver.
        for receiver in (yielding, priority):
            # Append message to inboxes[receiver].
            inboxes[receiver].append(message)
    # Return a dictionary of ego mapped to a tuple built from rows for (ego, rows) in key/value pairs from inboxes
    # to the caller.
    return {ego: tuple(rows) for ego, rows in inboxes.items()}


# Transport valid unresolved pair evidence; never choose a winner.
# Input participants: the supplied participants.
# Input edges: the supplied edges.
# Input snapshots: the supplied snapshots.
# Input mandatory: the supplied mandatory.
# Output: a tuple built from a lazy sequence of pair for pair in the result of combinations(participants, 2);
# retain entries satisfying frozenset(pair) does not belong to protected and...
def _eligible_fallback_pairs(participants, edges, snapshots, mandatory):
    """Transport valid unresolved pair evidence; never choose a winner."""
    # Set uncertain to a set of an immutable set built from a tuple containing r at 'ego_id', r at 'target_id' for
    # snapshot in snapshots; retain entries satisfying 'regulatory_status' from r; use None if absent equals the
    # text...
    uncertain = {frozenset((r["ego_id"],r["target_id"]))
        # Evaluate 'unresolved_relations' from snapshot; use an empty tuple if absent as part of the enclosing
        # expression.
        for snapshot in snapshots for r in snapshot.get("unresolved_relations", ())
        # Evaluate 'regulatory_status' from r; use None if absent equals the text
        # 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE' and 'shared_conflict_zone_ids' from r; use None if absent and
        # 'candidate_assessments' from r.get('regulatory_evidence', {}); use None if absent as part of the
        # enclosing expression.
        if r.get("regulatory_status") == "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"
        # Evaluate 'shared_conflict_zone_ids' from r; use None if absent as part of the enclosing expression.
        and r.get("shared_conflict_zone_ids")
        # Evaluate 'candidate_assessments' from r.get('regulatory_evidence', {}); use None if absent as part of
        # the enclosing expression.
        and r.get("regulatory_evidence", {}).get("candidate_assessments")}
    # Set protected to a set of an immutable set built from pair for pair in mandatory.
    protected = {frozenset(pair) for pair in mandatory}
    # Set eligible_edges to a set of an immutable set built from a tuple containing e at 'yielding_vehicle_id', e
    # at 'priority_vehicle_id' for e in edges; retain entries satisfying 'applicable_rule_ids' from e; use None if
    # absent and whether every item is true in a...
    eligible_edges = {frozenset((e["yielding_vehicle_id"],e["priority_vehicle_id"]))
        # Evaluate 'applicable_rule_ids' from e; use None if absent and whether every item is true in a lazy
        # sequence of the result of rule.startswith(('DE-STVO-8', 'DE-STVO-11-3')) for rule in e at
        # 'applicable_rule_ids' as part of the enclosing expression.
        for e in edges if e.get("applicable_rule_ids") and
        # Evaluate whether every item is true in a lazy sequence of the result of rule.startswith(a tuple
        # containing 'DE-STVO-8', 'DE-STVO-11-3') for rule in e at 'applicable_rule_ids' as part of the enclosing
        # expression.
        all(rule.startswith(("DE-STVO-8", "DE-STVO-11-3")) for rule in e["applicable_rule_ids"])}
    # Return a tuple built from a lazy sequence of pair for pair in the result of combinations(participants, 2);
    # retain entries satisfying frozenset(pair) does not belong to protected and frozenset(pair) belongs to
    # uncertain... to the caller.
    return tuple(pair for pair in combinations(participants,2)
        # Evaluate an immutable set built from pair does not belong to protected and an immutable set built from
        # pair belongs to uncertain combined with eligible_edges as part of the enclosing expression.
        if frozenset(pair) not in protected and frozenset(pair) in uncertain | eligible_edges)


# Sha256 using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()).
def _sha256(path):
    # Return the hexadecimal digest from hashlib.sha256(Path(path).read_bytes()) to the caller.
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Edge union using the inputs and processing steps below.
# Input snapshots: the supplied snapshots.
# Output: a tuple built from a lazy sequence of values at key for key in the sorted values from values.
# Processing: iterate over the relevant records.
def _edge_union(snapshots):
    # Set values to an empty dictionary.
    values = {}
    # Iterate over snapshots, binding each item to snapshot.
    for snapshot in snapshots:
        # Iterate over snapshot at 'joint_precedence_edges', binding each item to edge.
        for edge in snapshot["joint_precedence_edges"]:
            # Set key to a tuple containing edge at 'yielding_vehicle_id', edge at 'priority_vehicle_id'.
            key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            # Set values[key] to edge.
            values[key] = edge
    # Return a tuple built from a lazy sequence of values at key for key in the sorted values from values to the
    # caller.
    return tuple(values[key] for key in sorted(values))


# Conservatively consolidate actual ego-local snapshot classifications.
# Input snapshots: the supplied snapshots.
# Input original_graph: the supplied original graph.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _dynamic_status(snapshots, original_graph):
    """Conservatively consolidate actual ego-local snapshot classifications."""
    # Set statuses to a set of item at 'negotiation_status' for item in snapshots.
    statuses = {item["negotiation_status"] for item in snapshots}
    # Iterate over a tuple containing the text 'SOURCE_SNAPSHOT_MISMATCH', the text 'REGULATORY_PROFILE_MISMATCH',
    # the text..., binding each item to status.
    for status in ("SOURCE_SNAPSHOT_MISMATCH",
                   "REGULATORY_PROFILE_MISMATCH",
                   "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
                   "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED"):
        # Run this branch when status belongs to statuses.
        if status in statuses:
            # Return status to the caller.
            return status
    # Run this branch when the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE' belongs to statuses.
    if "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" in statuses:
        # Return the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE' to the caller.
        return "NEGOTIATION_REQUIRED_REGULATORY_CYCLE"
    # Run this branch when the text 'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE' belongs to statuses.
    if "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE" in statuses:
        # Return the text 'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE' to the caller.
        return "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"
    # Run this branch when original_graph.
    if original_graph:
        # Return the text 'REGULATORY_ORDER_RESOLVED' to the caller.
        return "REGULATORY_ORDER_RESOLVED"
    # Return the text 'NO_ACTIVE_CONFLICT' to the caller.
    return "NO_ACTIVE_CONFLICT"


# Release stale authority at a safe, event-driven progress boundary.
# Input helper: the supplied helper.
# Input authority: the supplied authority.
# Input identity: the supplied identity.
# Input zone_observations: the supplied zone observations.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _reconsider_authority_if_safe(helper, authority, identity,
                                  # Declare zone_observations as input parameter.
                                  zone_observations):
    """Release stale authority at a safe, event-driven progress boundary."""
    # Run this branch when authority is the same object as None.
    if authority is None:
        # Return a tuple containing None, an empty tuple to the caller.
        return None, ()
    # Set reasons to the result of helper._plan_invalidation_reasons(authority.state_identity, identity).
    reasons = helper._plan_invalidation_reasons(
        # Supply authority.state_identity to helper._plan_invalidation_reasons.
        authority.state_identity, identity)
    # Set occupied to whether any item is true in a lazy sequence of observation at 'state' equals the text
    # 'CURRENTLY_OCCUPYING' for observation in values from zone_observations.
    occupied = any(observation["state"] == "CURRENTLY_OCCUPYING"
                   # Evaluate values from zone_observations as part of the enclosing expression.
                   for observation in zone_observations.values())
    # Set old_participants to a set built from authority.state_identity at 0.
    old_participants = set(authority.state_identity[0])
    # Set new_participants to a set built from identity at 0.
    new_participants = set(identity[0])
    # Set participant_departed to a Boolean built from old_participants minus new_participants.
    participant_departed = bool(old_participants - new_participants)
    # Set old_nonexec to authority.initial_plan.graph_status differs from the text 'EXECUTABLE' or the negation of
    # authority.initial_plan.ready_vehicle_ids.
    old_nonexec = (authority.initial_plan.graph_status != "EXECUTABLE" or
                   # Evaluate the negation of authority.initial_plan.ready_vehicle_ids as part of the enclosing
                   # expression.
                   not authority.initial_plan.ready_vehicle_ids)
    # Set prior_ready_relevant to a Boolean built from a set built from authority.initial_plan.ready_vehicle_ids
    # intersected with new_participants.
    prior_ready_relevant = bool(
        # Supply a set built from authority.initial_plan.ready_vehicle_ids intersected with new_participants to
        # bool.
        set(authority.initial_plan.ready_vehicle_ids) & new_participants)
    # Set cleared_without_prior_ready to the text 'CONFLICT_ZONE_CLEARED' belongs to reasons and the negation of
    # prior_ready_relevant.
    cleared_without_prior_ready = (
        # Evaluate the text 'CONFLICT_ZONE_CLEARED' belongs to reasons and the negation of prior_ready_relevant as
        # part of the enclosing expression.
        "CONFLICT_ZONE_CLEARED" in reasons and not prior_ready_relevant)
    # Set safe_progress_boundary to old_nonexec or participant_departed or cleared_without_prior_ready.
    safe_progress_boundary = (old_nonexec or participant_departed or
                              # Evaluate cleared_without_prior_ready as part of the enclosing expression.
                              cleared_without_prior_ready)
    # Run this branch when the negation of reasons or occupied or the negation of safe_progress_boundary.
    if not reasons or occupied or not safe_progress_boundary:
        # Return a tuple containing authority, an empty tuple to the caller.
        return authority, ()
    # Return a tuple containing None, reasons to the caller.
    return None, reasons


# Print banner using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def _print_banner():
    # Display the text '=' multiplied by 60.
    print("=" * 60)
    # Display the text 'RUNTIME SIMULATION'.
    print("RUNTIME SIMULATION")
    # Display the text 'Multi-Agent Right-of-Way Negotiation'.
    print("Multi-Agent Right-of-Way Negotiation")
    # Display the text '=' multiplied by 60.
    print("=" * 60)
    # Display the text 'Mode: QUALITATIVE_PRESENTATION_ONLY'.
    print("Mode: QUALITATIVE_PRESENTATION_ONLY")
    # Display the text 'Selected policy: E5'.
    print("Selected policy: E5")
    # Display the text 'Policy source: selected_policy.pt'.
    print("Policy source: selected_policy.pt")
    # Display the text 'Decentralized actors: ENABLED'.
    print("Decentralized actors: ENABLED")
    # Display the text 'Centralized critic: DISABLED'.
    print("Centralized critic: DISABLED")
    # Display the text 'Training: DISABLED'.
    print("Training: DISABLED")
    # Display the text 'Held-out evaluation: NOT USED'.
    print("Held-out evaluation: NOT USED")
    # Display the text 'GUI: BLUE approaching; YELLOW negotiating; GREEN ready; RED...'.
    print("GUI: BLUE approaching; YELLOW negotiating; GREEN ready; RED blocked")
    # Display the text '=' multiplied by 60.
    print("=" * 60)


# Presentation timeline using the inputs and processing steps below.
# Input event_records: the supplied event records.
# Input diagnostics: the supplied diagnostics.
# Output: a tuple built from sorted(events, key=lambda item: item['timestamp']) sliced by -12:.
def _presentation_timeline(event_records, diagnostics):
    # Set events to a list of a dictionary containing timestamp, event, mappo_invocation, participants,
    # original_graph, proposer_actions,... for item in event_records.
    events = [{"timestamp": item["timestamp"],
               # Store item at 'status' under 'event'.
               "event": item["status"],
               # Store item at 'mappo_invocation' under 'mappo_invocation'.
               "mappo_invocation": item["mappo_invocation"],
               # Store 'participants' from item; use an empty tuple if absent under 'participants'.
               "participants": item.get("participants", ()),
               # Store 'original_regulatory_graph' from item; use an empty tuple if absent under 'original_graph'.
               "original_graph": item.get("original_regulatory_graph", ()),
               # Store 'proposer_actions' from item; use an empty tuple if absent under 'proposer_actions'.
               "proposer_actions": item.get("proposer_actions", ()),
               # Store 'responder_actions' from item; use an empty tuple if absent under 'responder_actions'.
               "responder_actions": item.get("responder_actions", ()),
               # Store 'effective_coordination_graph' from item; use an empty tuple if absent under
               # 'effective_graph'.
               "effective_graph": item.get("effective_coordination_graph", ()),
               # Store 'ready_vehicle_ids' from item; use an empty tuple if absent under 'ready'.
               "ready": item.get("ready_vehicle_ids", ()),
               # Store 'blocked_vehicle_ids' from item; use an empty tuple if absent under 'blocked'.
               "blocked": item.get("blocked_vehicle_ids", ()),
               # Store 'policy_factor_diagnostics' from item; use an empty tuple if absent under 'policy_factors'.
               "policy_factors": item.get("policy_factor_diagnostics", ())}
              # Evaluate event_records as part of the enclosing expression.
              for item in event_records]
    # Extend events with a lazy sequence of a dictionary containing timestamp, event, reasons for item in
    # diagnostics; retain entries satisfying item at 'event' belongs to a set containing the text
    # 'PLAN_INVALIDATED', the text...
    events.extend({"timestamp": item["timestamp"],
                   # Store item at 'event' under 'event'.
                   "event": item["event"],
                   # Store 'reasons' from item; use an empty tuple if absent under 'reasons'.
                   "reasons": item.get("reasons", ())}
                  # Evaluate diagnostics as part of the enclosing expression.
                  for item in diagnostics
                  # Evaluate item at 'event' belongs to a set containing the text 'PLAN_INVALIDATED', the text
                  # 'MAPPO_INVOCATION_BLOCKED' as part of the enclosing expression.
                  if item["event"] in {"PLAN_INVALIDATED",
                                       "MAPPO_INVOCATION_BLOCKED"})
    # Return a tuple built from sorted(events, key=lambda item: item['timestamp']) sliced by -12: to the caller.
    return tuple(sorted(events, key=lambda item: item["timestamp"])[-12:])


# Print event using the inputs and processing steps below.
# Input number: the supplied number.
# Input now: the time used for this operation.
# Input participants: the supplied participants.
# Input status: the supplied status.
# Input original: the supplied original.
# Input outcome: the supplied outcome.
# Input plan: the supplied plan.
# Input completed: the supplied completed.
# Input scheduled: the supplied scheduled.
# Input factor_diagnostics: the supplied factor diagnostics.
# Input selection_rule: the supplied selection rule.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _print_event(number, now, participants, status, original, outcome, plan,
                 # Declare completed, scheduled, factor_diagnostics as input parameters.
                 completed, scheduled, factor_diagnostics=(),
                 # Declare selection_rule as input parameter.
                 selection_rule=PRESENTATION_SELECTION_RULE):
    # Display the text '-' multiplied by 60.
    print("-" * 60)
    # Display formatted text built from the embedded values.
    print(f"TIME: {now:.2f} s   EVENT #{number}")
    # Display the text 'Active participants:' plus the result of repr(participants).
    print("Active participants: " + repr(participants))
    # Display the text 'Status:' plus status.
    print("Status: " + status)
    # Display the text 'Original precedence:' plus the result of repr(original).
    print("Original precedence: " + repr(original))
    # Run this branch when outcome is the same object as None.
    if outcome is None:
        # Display the text 'MAPPO_INVOCATION = NOT_REQUIRED' when status equals the text
        # 'REGULATORY_ORDER_RESOLVED', otherwise the text 'MAPPO_INVOCATION = BLOCKED'.
        print("MAPPO_INVOCATION = NOT_REQUIRED" if status ==
              # Supply the text 'MAPPO_INVOCATION = BLOCKED' to the enclosing expression.
              "REGULATORY_ORDER_RESOLVED" else "MAPPO_INVOCATION = BLOCKED")
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Display the text 'MAPPO_INVOCATION = AUTHORIZED'.
        print("MAPPO_INVOCATION = AUTHORIZED")
        # Display the text 'PROPOSER:' plus the result of
        # repr(outcome.proposer_assignment.claim_action_assignments).
        print("PROPOSER: " + repr(
            # Supply outcome.proposer_assignment.claim_action_assignments to repr.
            outcome.proposer_assignment.claim_action_assignments))
        # Display the text 'RESPONDER:' plus the result of
        # repr(outcome.responder_assignment.response_action_assignments).
        print("RESPONDER: " + repr(
            # Supply outcome.responder_assignment.response_action_assignments to repr.
            outcome.responder_assignment.response_action_assignments))
        # Display the text 'Effective graph:' plus the result of repr(outcome.effective_precedence_graph).
        print("Effective graph: " + repr(outcome.effective_precedence_graph))
        # Display the text 'SEMANTIC_SELECTION_RULE =' plus selection_rule.
        print("SEMANTIC_SELECTION_RULE = " + selection_rule)
        # Iterate over factor_diagnostics, binding each item to factor.
        for factor in factor_diagnostics:
            # Display the text 'POLICY_FACTOR' plus the result of repr(factor).
            print("POLICY_FACTOR " + repr(factor))
    # Display the text 'READY:' plus the result of repr(plan.ready_vehicle_ids).
    print("READY: " + repr(plan.ready_vehicle_ids))
    # Display the text 'BLOCKED:' plus the result of repr(plan.blocked_vehicle_ids).
    print("BLOCKED: " + repr(plan.blocked_vehicle_ids))
    # Display formatted text built from the embedded values.
    print(f"Completed: {completed}/{scheduled}")
    # Display the text '-' multiplied by 60.
    print("-" * 60)


# Shared control loop; optional evaluation hooks observe, never grant entry.
# Input duration_seconds: the supplied duration seconds.
# Input use_gui: the supplied use gui.
# Input gui_delay_ms: the supplied gui delay ms.
# Input output_dir: the supplied output dir.
# Input schedule: the supplied schedule.
# Input environment_factory: the supplied environment factory.
# Input web_live: the supplied web live.
# Input presentation_delay_ms: the supplied presentation delay ms.
# Input browser_state_path: the supplied browser state path.
# Input scenario_id: the supplied scenario id.
# Input admission_waves: the supplied admission waves.
# Input admission_mode: the supplied admission mode.
# Input stop_request_path: the supplied stop request path.
# Input presentation_run_id: the supplied presentation run id.
# Input runtime_observer: the supplied runtime observer.
# Input provider_factory: the supplied provider factory.
# Input persist_presentation: the supplied persist presentation.
# Input return_failed_result: the supplied return failed result.
# Input movement_protocol_enabled: the supplied movement protocol enabled.
# Input movement_protocol_factory: the supplied movement protocol factory.
# Output: result.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def run_runtime_simulation(*, duration_seconds=220.0, use_gui=False, gui_delay_ms=0,
                   # Declare output_dir, schedule as input parameters.
                   output_dir="results/runtime_simulation", schedule=None,
                   # Declare environment_factory, web_live as input parameters.
                   environment_factory=SUMOEnv, web_live=False,
                   # Declare presentation_delay_ms as input parameter.
                   presentation_delay_ms=0,
                   # Declare browser_state_path as input parameter.
                   browser_state_path="results/runtime_simulation/runtime/live_state.json",
                   # Declare scenario_id, admission_waves as input parameters.
                   scenario_id="default_panel", admission_waves=None,
                   # Declare admission_mode as input parameter.
                   admission_mode="ROLLING_WAVES",
                   # Declare stop_request_path, presentation_run_id as input parameters.
                   stop_request_path=None, presentation_run_id=None,
                   # Declare runtime_observer, provider_factory as input parameters.
                   runtime_observer=None, provider_factory=None,
                   # Declare persist_presentation, return_failed_result as input parameters.
                   persist_presentation=True, return_failed_result=False,
                   # Declare movement_protocol_enabled, movement_protocol_factory as input parameters.
                   movement_protocol_enabled=True, movement_protocol_factory=None):
    """Shared control loop; optional evaluation hooks observe, never grant entry.

    Default arguments retain the qualitative presentation contract. A separate
    quantitative wrapper supplies a predeclared semantic provider and telemetry.
    """
    # Run this branch when duration_seconds is at most 0.
    if duration_seconds <= 0:
        # Raise ValueError with the text 'PANEL_DURATION_MUST_BE_POSITIVE' to stop this execution path.
        raise ValueError("PANEL_DURATION_MUST_BE_POSITIVE")
    # Run this branch when admission_mode does not belong to a set containing the text 'ROLLING_WAVES', the text
    # 'INDEPENDENT_DEMAND'.
    if admission_mode not in {"ROLLING_WAVES", "INDEPENDENT_DEMAND"}:
        # Raise ValueError with the text 'UNKNOWN_PANEL_ADMISSION_MODE' to stop this execution path.
        raise ValueError("UNKNOWN_PANEL_ADMISSION_MODE")
    # Run this branch when schedule is the same object as None.
    if schedule is None:
        # Set schedule to the result of validate_schedule(the result of build_default_schedule()).
        schedule = validate_schedule(build_default_schedule())
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set schedule to the result of validate_presentation_schedule(schedule).
        schedule = validate_presentation_schedule(schedule,
            # Supply allow_repeated_movements as admission_mode equals the text 'INDEPENDENT_DEMAND'.
            allow_repeated_movements=admission_mode == "INDEPENDENT_DEMAND")
    # Set admission_waves to a tuple built from admission_waves or ADMISSION_WAVES.
    admission_waves = tuple(admission_waves or ADMISSION_WAVES)
    # Set scheduled_count to the sum of a lazy sequence of the number of entries in rows for rows in values from
    # schedule.
    scheduled_count = sum(len(rows) for rows in schedule.values())
    # Set policy_hash_before to the result of _sha256(POLICY_PATH).
    policy_hash_before = _sha256(POLICY_PATH)
    # Set (_, bundle) to the result of _load_bundle(POLICY_PATH).
    _, bundle = _load_bundle(POLICY_PATH)
    # Iterate over a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor, binding each item
    # to module.
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        # Call module.eval with the supplied arguments.
        module.eval()
    # Set provider to the result of PanelDeterministicInferenceProvider(bundle).
    provider = PanelDeterministicInferenceProvider(bundle, sampling_seed=0)
    # Run this branch when provider_factory is a different object from None.
    if provider_factory is not None:
        # Set provider to the result of provider_factory(bundle).
        provider = provider_factory(bundle)
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set movement_protocol to the result of movement_protocol_factory or MovementDeclarationBus(paths) when
    # movement_protocol_enabled, otherwise None.
    movement_protocol = ((movement_protocol_factory or MovementDeclarationBus)(paths)
                         # Evaluate movement_protocol_enabled as part of the enclosing expression.
                         if movement_protocol_enabled else None)
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Reuse geometry/audit utilities without constructing a training runtime
    # or a centralized execution planner.
    # Set helper to the result of SimpleNamespace().
    helper = SimpleNamespace(paths=paths, zones=zones,
        # Supply _decision_state_identity as CoupledNegotiationTrainingEnvironment._decision_state_identity.
        _decision_state_identity=CoupledNegotiationTrainingEnvironment._decision_state_identity,
        # Supply _plan_invalidation_reasons as CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons.
        _plan_invalidation_reasons=CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    # Set ego_controllers to an empty dictionary.
    ego_controllers = {}
    # Set observations to the result of ObservationManager().
    observations = ObservationManager()
    # Set (predictor, entry_monitor) to a tuple containing the result of IntentionPredictor(), the result of
    # ConflictEntryMonitor().
    predictor, entry_monitor = IntentionPredictor(), ConflictEntryMonitor()
    # Set graph_manager to the result of ConflictGraphManager(paths, zones).
    graph_manager = ConflictGraphManager(paths, zones)
    # Set occupancy to the result of ConflictZoneOccupancyAssessor(paths, zones).
    occupancy = ConflictZoneOccupancyAssessor(paths, zones)
    # Set rules to the result of TrafficRuleEngine(paths).
    rules = TrafficRuleEngine(paths, runtime_v2=True)
    # Set negotiation to the result of NegotiationEnvironment().
    negotiation = NegotiationEnvironment(joint_assembler=JointLocalPrecedenceGraphAssembler(runtime_v2=True))
    # Set (claim_bus, encoder) to a tuple containing the result of V2VPrecedenceClaimBus(), the result of
    # GraphTensorEncoder().
    claim_bus, encoder = V2VPrecedenceClaimBus(), GraphTensorEncoder()
    # Set visualizer to the result of PanelDemoVisualizer(traci, use_gui, gui_delay_ms).
    visualizer = PanelDemoVisualizer(traci, use_gui, gui_delay_ms)
    # Set browser to the result of BrowserStatePublisher(browser_state_path, traci) when web_live, otherwise None.
    browser = (BrowserStatePublisher(
        # Supply browser_state_path to BrowserStatePublisher.
        browser_state_path, traci,
        # Supply presentation_delay_ms as presentation_delay_ms.
        presentation_delay_ms=presentation_delay_ms) if web_live else None)
    # Set map_state to the result of browser.map_snapshot(paths) when browser, otherwise None.
    map_state = browser.map_snapshot(paths) if browser else None
    # Set environment to the result of SUMOEnv() when environment_factory is the same object as SUMOEnv, otherwise
    # the result of environment_factory().
    environment = (SUMOEnv(use_gui=use_gui, extra_options=SAFE_RUNTIME_OPTIONS)
        # Supply use_gui as use_gui.
        if environment_factory is SUMOEnv else environment_factory(use_gui=use_gui))
    # Set queues to a dictionary of key mapped to a list built from value for (key, value) in key/value pairs from
    # schedule.
    queues = {key: list(value) for key, value in schedule.items()}
    # Set slots to a dictionary of key mapped to None for key in schedule.
    slots = {key: None for key in schedule}
    # Set (movements, vehicle_approaches) to a tuple containing an empty dictionary, an empty dictionary.
    movements, vehicle_approaches = {}, {}
    # Set (completed_ids, spawned_ids) to a tuple containing an empty list, an empty list.
    completed_ids, spawned_ids = [], []
    # Set (submitted_ids, departures, demand_times) to a tuple containing an empty list, an empty dictionary, an
    # empty dictionary.
    submitted_ids, departures, demand_times = [], {}, {}
    # Set (constrained_ids, prior_hold_ids) to a tuple containing an empty set, an empty set.
    constrained_ids, prior_hold_ids = set(), set()
    # Set authority to None.
    authority = None
    # Set (cleared, entry_events, clear_events) to a tuple containing an empty set, an empty list, an empty list.
    cleared, entry_events, clear_events = set(), [], []
    # Set last_attempt_identity to None.
    last_attempt_identity = None
    # Set last_blocked_invocation to None.
    last_blocked_invocation = None
    # Set next_admission_wave to 0.
    next_admission_wave = 0
    # Set starts and closes to 0.
    starts = closes = 0
    # Set metrics to a dictionary containing presentation_vehicles_scheduled, presentation_vehicles_completed,
    # unfinished_vehicles,...
    metrics = {"presentation_vehicles_scheduled": scheduled_count,
               # Store 0 under 'presentation_vehicles_completed'.
               "presentation_vehicles_completed": 0,
               # Store scheduled_count under 'unfinished_vehicles'.
               # Store 0 under 'negotiation_events'.
               "unfinished_vehicles": scheduled_count, "negotiation_events": 0,
               # Store 0 under 'mappo_decision_epochs'.
               # Store 0 under 'rule_resolved_events'.
               "mappo_decision_epochs": 0, "rule_resolved_events": 0,
               # Store 0 under 'renegotiation_events'.
               # Store 0 under 'safe_hold_activations'.
               "renegotiation_events": 0, "safe_hold_activations": 0,
               # Store 0 under 'collisions'.
               # Store 0 under 'blocked_zone_violations'.
               "collisions": 0, "blocked_zone_violations": 0,
               # Store 0 under 'maximum_negotiation_participants'.
               "maximum_negotiation_participants": 0}
    # Update metrics with the supplied entries.
    metrics.update({"total_vehicles_scheduled": scheduled_count,
        # Store 0 under 'total_vehicles_spawned'.
        # Store 0 under 'total_vehicles_completed'.
        "total_vehicles_spawned": 0, "total_vehicles_completed": 0,
        # Store 0 under 'current_active_vehicle_count'.
        # Store 0 under 'maximum_simultaneous_active_vehicles'.
        "current_active_vehicle_count": 0, "maximum_simultaneous_active_vehicles": 0,
        # Store 0 under 'current_moving_vehicle_count'.
        # Store 0 under 'maximum_simultaneously_moving_vehicles'.
        "current_moving_vehicle_count": 0, "maximum_simultaneously_moving_vehicles": 0,
        # Store the result of dict.fromkeys(the text 'NESW', 0) under 'per_approach_queue_depth'.
        "per_approach_queue_depth": dict.fromkeys("NESW", 0),
        # Store the result of dict.fromkeys(the text 'NESW', 0) under 'maximum_per_approach_queue_depth'.
        "maximum_per_approach_queue_depth": dict.fromkeys("NESW", 0),
        # Store an empty tuple under 'current_negotiation_participants'.
        # Store 0 under 'negotiation_event_count'.
        "current_negotiation_participants": (), "negotiation_event_count": 0,
        # Store 0 under 'centralized_critic_runtime_calls'.
        # Store True under 'decentralized_execution'.
        "centralized_critic_runtime_calls": 0, "decentralized_execution": True,
        # Store provider.runtime_critic_enabled under 'centralized_critic_used_for_action'.
        "centralized_critic_used_for_action": provider.runtime_critic_enabled,
        # Store False under 'centralized_execution_graph_used_for_control'.
        "centralized_execution_graph_used_for_control": False,
        # Store True under 'selected_policy_hash_unchanged'.
        "selected_policy_hash_unchanged": True})
    # Set metrics['maximum_approaches_with_multiple_queued_vehicles'] to 0.
    metrics["maximum_approaches_with_multiple_queued_vehicles"] = 0
    # Set metrics['native_emergency_stop_events'] to 0.
    metrics["native_emergency_stop_events"] = 0
    # Update metrics with the supplied entries.
    metrics.update(mappo_negotiation_events=0, mappo_outcomes_accepted=0,
        # Supply mappo_outcomes_rejected_by_shield as 0.
        # Supply fallback_activations as 0.
        mappo_outcomes_rejected_by_shield=0, fallback_activations=0,
        # Supply mappo_outcomes_rejected_by_safety_shield as 0.
        # Supply fallback_rate as 0.0.
        mappo_outcomes_rejected_by_safety_shield=0, fallback_rate=0.0)
    # Set (diagnostics, event_records) to a tuple containing an empty list, an empty list.
    diagnostics, event_records = [], []
    # Set latest_policy_factors to an empty tuple.
    latest_policy_factors = ()
    # Set queue_arrivals to an empty dictionary.
    queue_arrivals = {}
    # Set stopped_by_user to False.
    stopped_by_user = False
    # Set failure to None.
    failure = None
    # Set started_at to the result of datetime.now(timezone.utc).isoformat().
    started_at = datetime.now(timezone.utc).isoformat()
    # Set stop_request to the result of Path(stop_request_path) when stop_request_path, otherwise None.
    stop_request = Path(stop_request_path) if stop_request_path else None
    # Call _print_banner with the supplied arguments.
    _print_banner()
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call environment.start with the supplied arguments.
        # Update starts to its current value plus 1.
        environment.start(); starts += 1
        # Call visualizer.configure_camera with the supplied arguments.
        visualizer.configure_camera(paths, show_queues=admission_mode == "INDEPENDENT_DEMAND")
        # Set max_steps to an integer built from the rounded value of a floating-point number built from
        # duration_seconds divided by SIM_TIME_STEP.
        max_steps = int(round(float(duration_seconds) / SIM_TIME_STEP))
        # Repeat the following steps while environment.step_count is less than max_steps.
        while environment.step_count < max_steps:
            # Run this branch when stop_request is a different object from None and whether stop_request is an
            # existing file.
            if stop_request is not None and stop_request.is_file():
                # Set stopped_by_user to True.
                stopped_by_user = True
                # Append a dictionary containing event, timestamp to diagnostics.
                diagnostics.append({"event": "PRESENTATION_STOP_REQUESTED",
                                    # Store environment.current_time under 'timestamp'.
                                    "timestamp": environment.current_time})
                # Display formatted text built from the embedded values.
                print(f"USER_STOPPED_AT {environment.current_time:.2f} s")
                # Leave the nearest enclosing loop immediately.
                break
            # Set wave_ready to whether every item is true in a lazy sequence of vehicle_id is the same object as
            # None for vehicle_id in values from slots.
            wave_ready = all(vehicle_id is None
                             # Evaluate values from slots as part of the enclosing expression.
                             for vehicle_id in slots.values())
            # Set wave_approaches to a set built from admission_waves at next_admission_wave when wave_ready and
            # next_admission_wave is less than the number of entries in admission_waves, otherwise an empty set.
            wave_approaches = (set(admission_waves[next_admission_wave])
                               # Evaluate wave_ready and next_admission_wave is less than the number of entries in
                               # admission_waves as part of the enclosing expression.
                               if wave_ready and next_admission_wave <
                               # Evaluate the number of entries in admission_waves as part of the enclosing
                               # expression.
                               len(admission_waves) else set())
            # Set admitted_this_step to False.
            admitted_this_step = False
            # Iterate over ADMISSION_ORDER, binding each item to approach.
            for approach in ADMISSION_ORDER:
                # Set initial_pending to a Boolean built from queues at approach and
                # queues[approach][0].sequence_index equals 0.
                initial_pending = (bool(queues[approach]) and
                                   # Evaluate queues[approach][0].sequence_index equals 0 as part of the enclosing
                                   # expression.
                                   queues[approach][0].sequence_index == 0)
                # Set release_time to INITIAL_ADMISSION_SECONDS at approach when initial_pending, otherwise 0.0.
                release_time = (INITIAL_ADMISSION_SECONDS[approach]
                                # Evaluate initial_pending as part of the enclosing expression.
                                if initial_pending else 0.0)
                # Set independent_due to admission_mode equals the text 'INDEPENDENT_DEMAND' and a Boolean built
                # from queues at approach and environment.current_time is at least
                # queues[approach][0].scheduled_departure_seconds.
                independent_due = (admission_mode == "INDEPENDENT_DEMAND" and
                    # Evaluate environment.current_time is at least
                    # queues[approach][0].scheduled_departure_seconds as part of the enclosing expression.
                    bool(queues[approach]) and environment.current_time >=
                    # Evaluate queues[approach][0].scheduled_departure_seconds as part of the enclosing
                    # expression.
                    queues[approach][0].scheduled_departure_seconds)
                # Set rolling_due to admission_mode equals the text 'ROLLING_WAVES' and approach belongs to
                # wave_approaches and slots at approach is the same object as None.
                rolling_due = (admission_mode == "ROLLING_WAVES" and
                    # Evaluate approach belongs to wave_approaches as part of the enclosing expression.
                    approach in wave_approaches and slots[approach] is None)
                # Run this branch when independent_due or rolling_due and queues at approach and
                # environment.current_time is at least release_time.
                if ((independent_due or rolling_due) and
                        # Evaluate queues at approach as part of the enclosing expression.
                        queues[approach] and
                        # Evaluate environment.current_time is at least release_time as part of the enclosing
                        # expression.
                        environment.current_time >= release_time):
                    # Set demand to the result of queues[approach].pop(0).
                    demand = queues[approach].pop(0)
                    # Set vehicle_id to formatted text built from the embedded values.
                    vehicle_id = f"PANEL_AV_{approach}_{demand.sequence_index + 1:02d}"
                    # Set route to the result of derive_existing_route_id(paths, demand.movement_path_id).
                    route = derive_existing_route_id(paths,
                                                     # Supply demand.movement_path_id to derive_existing_route_id.
                                                     demand.movement_path_id)
                    # Add vehicle_id to traci.vehicle.
                    traci.vehicle.add(vehicle_id, route, AV_TYPE_ID,
                                      # Supply departSpeed as the text 'max'.
                                      # Supply departLane as the text 'free'.
                                      departSpeed="max", departLane="free",
                                      # Supply departPos as the text 'base'.
                                      departPos="base")
                    # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
                    traci.vehicle.setSpeedMode(vehicle_id,
                                               # Supply SAFE_SUMO_SPEED_MODE to traci.vehicle.setSpeedMode.
                                               SAFE_SUMO_SPEED_MODE)
                    # Call observations.get_or_create_ldm with the supplied arguments.
                    observations.get_or_create_ldm(vehicle_id)
                    # Set slots[approach] to vehicle_id.
                    slots[approach] = vehicle_id
                    # Set movements[vehicle_id] to demand.movement_path_id.
                    movements[vehicle_id] = demand.movement_path_id
                    # Set vehicle_approaches[vehicle_id] to approach.
                    vehicle_approaches[vehicle_id] = approach
                    # Append vehicle_id to submitted_ids.
                    submitted_ids.append(vehicle_id)
                    # Set demand_times[vehicle_id] to demand.scheduled_departure_seconds when admission_mode
                    # equals the text 'INDEPENDENT_DEMAND', otherwise environment.current_time.
                    demand_times[vehicle_id] = (demand.scheduled_departure_seconds
                        # Evaluate admission_mode equals the text 'INDEPENDENT_DEMAND' as part of the enclosing
                        # expression.
                        if admission_mode == "INDEPENDENT_DEMAND" else environment.current_time)
                    # Set admitted_this_step to True.
                    admitted_this_step = True
                    # Display formatted text built from the embedded values.
                    print(f"VEHICLE_ADMITTED {vehicle_id} "
                          # Evaluate {demand.movement_path_id} as part of the enclosing expression.
                          f"{demand.movement_path_id}")
            # Run this branch when admitted_this_step.
            if admitted_this_step:
                # Update next_admission_wave to its current value plus 1.
                next_admission_wave += 1
            # Set states to the result of environment.step().
            # Set now to environment.current_time.
            states = environment.step(); now = environment.current_time
            # Run this branch when runtime_observer is a different object from None.
            if runtime_observer is not None:
                # Call runtime_observer.observe with the supplied arguments.
                runtime_observer.observe(now, states, environment.lifecycle_events,
                                         # Supply movements to runtime_observer.observe.
                                         movements, paths, zones, traci)
            # Iterate over environment.lifecycle_events.departed_vehicle_ids, binding each item to vehicle_id.
            for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                # Run this branch when vehicle_id belongs to vehicle_approaches.
                if vehicle_id in vehicle_approaches:
                    # Append vehicle_id to spawned_ids.
                    spawned_ids.append(vehicle_id)
                    # Set departures[vehicle_id] to now.
                    departures[vehicle_id] = now
            # Iterate over environment.lifecycle_events.arrived_vehicle_ids, binding each item to vehicle_id.
            for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                # Run this branch when vehicle_id belongs to vehicle_approaches.
                if vehicle_id in vehicle_approaches:
                    # Set approach to vehicle_approaches at vehicle_id.
                    approach = vehicle_approaches[vehicle_id]
                    # Run this branch when slots at approach equals vehicle_id.
                    if slots[approach] == vehicle_id:
                        # Set slots[approach] to None.
                        slots[approach] = None
                    # Append vehicle_id to completed_ids.
                    completed_ids.append(vehicle_id)
                    # Display formatted text built from the embedded values.
                    print(f"VEHICLE_COMPLETED {vehicle_id}")
            # Set collisions to a tuple built from the sorted values from the result of
            # traci.simulation.getCollidingVehiclesIDList().
            collisions = tuple(sorted(
                # Supply the result of traci.simulation.getCollidingVehiclesIDList() to sorted.
                traci.simulation.getCollidingVehiclesIDList()))
            # Run this branch when collisions.
            if collisions:
                # Update metrics['collisions'] to its current value plus the number of entries in collisions.
                metrics["collisions"] += len(collisions)
                # Raise RuntimeError with the text 'PANEL_DEMO_COLLISION_OBSERVED' to stop this execution path.
                raise RuntimeError("PANEL_DEMO_COLLISION_OBSERVED")

            # Set frontline_ids to the result of select_queue_heads(states, paths, movements).
            frontline_ids = select_queue_heads(states, paths, movements)
            # Set queue_heads to a tuple built from a lazy sequence of ego for ego in frontline_ids; retain
            # entries satisfying the result of observations.is_in_approach_zone(states[ego] at 'position').
            queue_heads = tuple(ego for ego in frontline_ids
                # Evaluate the result of observations.is_in_approach_zone(states[ego] at 'position') as part of
                # the enclosing expression.
                if observations.is_in_approach_zone(states[ego]["position"]))
            # Iterate over key/value pairs from states, binding each item to (ego, state).
            for ego, state in states.items():
                # Run this branch when state at 'lane_id' equals paths.paths[movements[ego]].incoming_lane_id.
                if state["lane_id"] == paths.paths[movements[ego]].incoming_lane_id:
                    # Call queue_arrivals.setdefault with the supplied arguments.
                    queue_arrivals.setdefault(ego, now)
            # Set depths to the result of approach_queue_depth(states, paths, movements).
            depths = approach_queue_depth(states, paths, movements)
            # Set metrics['maximum_approaches_with_multiple_queued_vehicles'] to the maximum of metrics at
            # 'maximum_approaches_with_multiple_queued_vehicles', the sum of a lazy sequence of...
            metrics["maximum_approaches_with_multiple_queued_vehicles"] = max(
                # Supply metrics at 'maximum_approaches_with_multiple_queued_vehicles' to max.
                metrics["maximum_approaches_with_multiple_queued_vehicles"],
                # Supply the sum of a lazy sequence of depth is greater than 1 for depth in values from depths to
                # max.
                sum(depth > 1 for depth in depths.values()))
            # Update metrics['native_emergency_stop_events'] to its current value plus the number of entries in
            # the result of traci.simulation.getEmergencyStoppingVehiclesIDList().
            metrics["native_emergency_stop_events"] += len(
                # Supply the result of traci.simulation.getEmergencyStoppingVehiclesIDList() to len.
                traci.simulation.getEmergencyStoppingVehiclesIDList())
            # Set metrics['current_active_vehicle_count'] to the number of entries in states.
            metrics["current_active_vehicle_count"] = len(states)
            # Set metrics['current_moving_vehicle_count'] to the sum of a lazy sequence of s at 'speed' is greater
            # than 0 for s in values from states.
            metrics["current_moving_vehicle_count"] = sum(s["speed"] > 0 for s in states.values())
            # Iterate over a tuple containing a tuple containing the text 'current_active_vehicle_count', the
            # text..., binding each item to (current, maximum).
            for current, maximum in (("current_active_vehicle_count", "maximum_simultaneous_active_vehicles"),
                                     # Include a tuple containing the text 'current_moving_vehicle_count', the
                                     # text 'maximum_simultaneously_moving_vehicles' in this tuple.
                                     ("current_moving_vehicle_count", "maximum_simultaneously_moving_vehicles")):
                # Set metrics[maximum] to the maximum of metrics at maximum, metrics at current.
                metrics[maximum] = max(metrics[maximum], metrics[current])
            # Set metrics['per_approach_queue_depth'] to depths.
            metrics["per_approach_queue_depth"] = depths
            # Iterate over depths, binding each item to approach.
            for approach in depths:
                # Set metrics['maximum_per_approach_queue_depth'][approach] to the maximum of
                # metrics['maximum_per_approach_queue_depth'] at approach, depths at approach.
                metrics["maximum_per_approach_queue_depth"][approach] = max(
                    # Supply metrics['maximum_per_approach_queue_depth'] at approach to max.
                    metrics["maximum_per_approach_queue_depth"][approach], depths[approach])
            # Set metrics['total_vehicles_spawned'] to the number of entries in spawned_ids.
            metrics["total_vehicles_spawned"] = len(spawned_ids)
            # Set metrics['total_vehicles_completed'] to the number of entries in completed_ids.
            metrics["total_vehicles_completed"] = len(completed_ids)
            # Set metrics['current_negotiation_participants'] to queue_heads.
            metrics["current_negotiation_participants"] = queue_heads

            # Set snapshots to the result of PhysicalBranchReplayRunner._pipeline_step(states, now, observations,
            # entry_monitor, predictor, graph_manager, occupancy, rules,...).
            snapshots = PhysicalBranchReplayRunner._pipeline_step(
                # Supply entry_monitor to PhysicalBranchReplayRunner._pipeline_step.
                states, now, observations, entry_monitor, predictor,
                # Supply graph_manager to PhysicalBranchReplayRunner._pipeline_step.
                graph_manager, occupancy, rules, negotiation, claim_bus,
                # Supply negotiation_eligible_ids as queue_heads.
                # Supply movement_protocol as movement_protocol.
                encoder, negotiation_eligible_ids=queue_heads, movement_protocol=movement_protocol)
            # Set edges to the result of _edge_union(snapshots).
            edges = _edge_union(snapshots)
            # Set original to a tuple built from the sorted values from a lazy sequence of a tuple containing
            # x['yielding_vehicle_id'], x['priority_vehicle_id'] for x in edges.
            original = tuple(sorted((x["yielding_vehicle_id"],
                                     # Include x at 'priority_vehicle_id' in this tuple.
                                     x["priority_vehicle_id"]) for x in edges))
            # Set edge_identity to the result of helper._decision_state_identity(states, edges, cleared).
            edge_identity = helper._decision_state_identity(states, edges, cleared)
            # Set identity to a tuple containing queue_heads, edge_identity at 1, edge_identity at 2.
            identity = (queue_heads, edge_identity[1], edge_identity[2])
            # Set participants to queue_heads.
            participants = queue_heads
            # Set participant_approaches to a list of vehicle_approaches at x for x in participants.
            participant_approaches = [vehicle_approaches[x]
                                      # Evaluate participants as part of the enclosing expression.
                                      for x in participants]
            # Run this branch when the number of entries in participants is greater than 4 or the number of
            # entries in a set built from participant_approaches differs from the number of entries in
            # participant_approaches.
            if len(participants) > 4 or len(set(participant_approaches)) != len(
                    # Supply participant_approaches to len.
                    participant_approaches):
                # Raise RuntimeError with the text 'PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED' to stop this
                # execution path.
                raise RuntimeError("PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED")
            # Set metrics['maximum_negotiation_participants'] to the maximum of metrics at
            # 'maximum_negotiation_participants', the number of entries in participants.
            metrics["maximum_negotiation_participants"] = max(
                # Supply metrics at 'maximum_negotiation_participants' to max.
                metrics["maximum_negotiation_participants"], len(participants))
            # Set status to the result of _dynamic_status(snapshots, original).
            status = _dynamic_status(snapshots, original)
            # Run this branch when authority is a different object from None and status belongs to BLOCKED and
            # status differs from authority.status.
            if authority is not None and status in BLOCKED and status != authority.status:
                # Set authority to None.
                authority = None
                # Set last_attempt_identity to None.
                last_attempt_identity = None
            # Run this branch when authority is a different object from None and authority.status belongs to
            # BLOCKED and status differs from authority.status.
            if authority is not None and authority.status in BLOCKED and status != authority.status:
                # Set authority to None.
                authority = None
                # Set last_attempt_identity to None.
                last_attempt_identity = None

            # Set zone_observations to None.
            zone_observations = None
            # Run this branch when authority is a different object from None.
            if authority is not None:
                # Set zone_observations to the result of PhysicalBranchReplayRunner._observe_zones(helper, states,
                # movements, authority.zone_states, now, entry_events, clear_events, cleared).
                zone_observations = PhysicalBranchReplayRunner._observe_zones(
                    # Supply authority.zone_states to PhysicalBranchReplayRunner._observe_zones.
                    helper, states, movements, authority.zone_states, now,
                    # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                    entry_events, clear_events, cleared)
                # Set (authority, reasons) to the result of _reconsider_authority_if_safe(helper, authority,
                # identity, zone_observations).
                authority, reasons = _reconsider_authority_if_safe(
                    # Supply zone_observations to _reconsider_authority_if_safe.
                    helper, authority, identity, zone_observations)
                # Run this branch when reasons.
                if reasons:
                    # Append a dictionary containing event, timestamp, reasons to diagnostics.
                    diagnostics.append({"event": "PLAN_INVALIDATED",
                                        # Store now under 'timestamp'.
                                        "timestamp": now,
                                        # Store reasons under 'reasons'.
                                        "reasons": reasons})
                    # Display the text 'PLAN_INVALIDATED' plus the result of ','.join(reasons).
                    print("PLAN_INVALIDATED " + ",".join(reasons))
                    # Display the text 'RENEGOTIATION_REQUIRED'.
                    print("RENEGOTIATION_REQUIRED")
                    # Update metrics['renegotiation_events'] to its current value plus 1.
                    metrics["renegotiation_events"] += 1
                    # Set zone_observations to None.
                    zone_observations = None

            # Run this branch when original and authority is the same object as None and identity differs from
            # last_attempt_identity.
            if original and authority is None and identity != last_attempt_identity:
                # Set source_id to a tuple containing a tuple containing the text 'PANEL_DEMO', now, the text
                # 'CONTINUOUS_JOINT_NEGOTIATION_CONTEXT'.
                source_id = (("PANEL_DEMO",), now,
                             "CONTINUOUS_JOINT_NEGOTIATION_CONTEXT")
                # Set outcome to None.
                outcome = None
                # Set batch_id to a tuple containing a tuple containing the text 'PANEL_DEMO_ONE_PROCESS', now.
                batch_id = (("PANEL_DEMO_ONE_PROCESS",), now)
                # Set invocation_block_reason to None.
                invocation_block_reason = None
                # Run this branch when status belongs to NEGOTIABLE.
                if status in NEGOTIABLE:
                    # Set encoded to a tuple built from a lazy sequence of
                    # observations.get_ldm(x['ego_id']).current_encoded_graph_observation for x in snapshots.
                    encoded = tuple(observations.get_ldm(x["ego_id"]).
                                    current_encoded_graph_observation
                                    # Evaluate snapshots as part of the enclosing expression.
                                    for x in snapshots)
                    # Run this branch when whether any item is true in a lazy sequence of the number of entries in
                    # item.node_ids is greater than 4 for item in encoded.
                    if any(len(item.node_ids) > 4 for item in encoded):
                        # Raise RuntimeError with the text 'PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED' to stop
                        # this execution path.
                        raise RuntimeError("PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED")
                    # Set factors to the result of provider._eligible_factors(participants, edges, status).
                    factors = provider._eligible_factors(
                        # Supply participants to provider._eligible_factors.
                        participants, edges, status)
                    # Set encoded_egos to a set of item.ego_id for item in encoded.
                    encoded_egos = {item.ego_id for item in encoded}
                    # Set required_egos to a set of claim.ego_id for (claim, _) in factors combined with a set of
                    # claim.counterparty_id for (claim, _) in factors.
                    required_egos = ({claim.ego_id for claim, _ in factors} |
                                     # Evaluate a set of claim.counterparty_id for (claim, _) in factors as part
                                     # of the enclosing expression.
                                     {claim.counterparty_id
                                      # Evaluate a tuple containing claim, _ as part of the enclosing expression.
                                      for claim, _ in factors})
                    # Set missing_egos to a tuple built from the sorted values from required_egos minus
                    # encoded_egos.
                    missing_egos = tuple(sorted(required_egos - encoded_egos))
                    # Run this branch when the negation of factors.
                    if not factors:
                        # Set invocation_block_reason to the text 'NO_ELIGIBLE_PROPOSER_FACTORS'.
                        invocation_block_reason = "NO_ELIGIBLE_PROPOSER_FACTORS"
                    # Run this branch when missing_egos.
                    elif missing_egos:
                        # Set invocation_block_reason to the text 'RESPONDER_CONTEXT_INCOMPLETE'.
                        invocation_block_reason = "RESPONDER_CONTEXT_INCOMPLETE"
                    # Run this alternative branch when the preceding branch does not apply.
                    else:
                        # Set inference_started to the result of perf_counter_ns().
                        inference_started = perf_counter_ns()
                        # Set outcome to the result of provider.select_joint_actions().
                        outcome = provider.select_joint_actions(
                            # Supply scenario_id as a tuple containing the text 'PANEL_DEMO_PRESENTATION_ONLY'.
                            scenario_id=("PANEL_DEMO_PRESENTATION_ONLY",),
                            # Supply episode_id as a tuple containing the text 'PANEL_DEMO_ONE_PROCESS'.
                            episode_id=("PANEL_DEMO_ONE_PROCESS",),
                            # Supply batch_id as batch_id.
                            batch_id=batch_id,
                            # Supply source_snapshot_id as source_id.
                            source_snapshot_id=source_id,
                            # Supply original_edges as edges.
                            original_edges=edges,
                            # Supply active_vehicle_ids as participants.
                            # Supply timestamp as now.
                            active_vehicle_ids=participants, timestamp=now,
                            # Supply regulatory_profile as the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
                            regulatory_profile=
                                "DE_STVO_UNCONTROLLED_4WAY_V1",
                            # Supply negotiation_status as status.
                            negotiation_status=status,
                            # Supply encoded_graphs as encoded.
                            encoded_graphs=encoded)
                        # Run this branch when runtime_observer is a different object from None.
                        if runtime_observer is not None:
                            # Call runtime_observer.inference with the supplied arguments.
                            runtime_observer.inference(perf_counter_ns() - inference_started)
                        # Run this branch when outcome is a different object from None.
                        if outcome is not None:
                            # Run this branch when the requested attribute of provider.
                            if getattr(provider, "uses_mappo_behavior_policy", True):
                                # Update metrics['mappo_decision_epochs'] to its current value plus 1.
                                metrics["mappo_decision_epochs"] += 1
                    # Run this branch when invocation_block_reason.
                    if invocation_block_reason:
                        # Set signature to a tuple containing identity, invocation_block_reason, missing_egos.
                        signature = (identity, invocation_block_reason,
                                     # Include missing_egos in this tuple.
                                     missing_egos)
                        # Run this branch when signature differs from last_blocked_invocation.
                        if signature != last_blocked_invocation:
                            # Display the text 'MAPPO_INVOCATION = BLOCKED'.
                            print("MAPPO_INVOCATION = BLOCKED")
                            # Display the text 'Reason:' plus invocation_block_reason.
                            print("Reason: " + invocation_block_reason)
                            # Run this branch when missing_egos.
                            if missing_egos:
                                # Display the text 'Missing encoded egos:' plus the result of repr(missing_egos).
                                print("Missing encoded egos: " +
                                      # Evaluate the result of repr(missing_egos) as part of the enclosing
                                      # expression.
                                      repr(missing_egos))
                            # Append a dictionary containing event, timestamp, reason, missing_encoded_egos to
                            # diagnostics.
                            diagnostics.append({
                                "event": "MAPPO_INVOCATION_BLOCKED",
                                # Store now under 'timestamp'.
                                "timestamp": now,
                                # Store invocation_block_reason under 'reason'.
                                "reason": invocation_block_reason,
                                # Store missing_egos under 'missing_encoded_egos'.
                                "missing_encoded_egos": missing_egos})
                            # Set last_blocked_invocation to signature.
                            last_blocked_invocation = signature
                # Run this branch when status equals the text 'REGULATORY_ORDER_RESOLVED'.
                elif status == "REGULATORY_ORDER_RESOLVED":
                    # Update metrics['rule_resolved_events'] to its current value plus 1.
                    metrics["rule_resolved_events"] += 1
                    # Display the text 'TRAFFIC_RULE_ORDER_ALREADY_RESOLVED'.
                    print("TRAFFIC_RULE_ORDER_ALREADY_RESOLVED")
                # Run this branch when invocation_block_reason.
                if invocation_block_reason:
                    # Do not freeze an incomplete authority or mark the live
                    # state attempted; retry when every required local actor
                    # context exists.
                    # Set outcome to None.
                    outcome = None
                    # Ego controllers below safe-hold until coordination arrives.
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Set last_attempt_identity to identity.
                    last_attempt_identity = identity
                # Run this branch when the negation of invocation_block_reason.
                if not invocation_block_reason:
                    # Set last_blocked_invocation to None.
                    last_blocked_invocation = None
                    # Set effective to outcome.effective_precedence_graph when outcome is a different object from
                    # None, otherwise original.
                    effective = (outcome.effective_precedence_graph
                                 # Evaluate outcome is a different object from None as part of the enclosing
                                 # expression.
                                 if outcome is not None else original)
                    # Set inboxes to the result of _deliver_pair_commitments(effective, participants, source_id).
                    inboxes = _deliver_pair_commitments(effective, participants, source_id)
                    # Set zone_states to the result of PhysicalBranchReplayRunner._zone_definitions(helper,
                    # states, movements, a tuple built from a lazy sequence of edge for edge in the result of...).
                    zone_states = PhysicalBranchReplayRunner._zone_definitions(
                        # Supply movements to PhysicalBranchReplayRunner._zone_definitions.
                        helper, states, movements,
                        # Supply a tuple built from a lazy sequence of edge for edge in the result of
                        # combinations(participants, 2); retain entries satisfying the result of
                        # zones.zone_record(movements[edge[0]], states[edge[0]]['width'],... to
                        # PhysicalBranchReplayRunner._zone_definitions.
                        tuple(edge for edge in combinations(participants, 2) if zones.zone_record(
                            # Supply states[edge[0]] at 'width' to zones.zone_record.
                            movements[edge[0]], states[edge[0]]["width"],
                            # Supply states[edge[1]] at 'width' to zones.zone_record.
                            movements[edge[1]], states[edge[1]]["width"]) is not None))
                    # Only ego controllers determine permissions; this placeholder
                    # is event bookkeeping, never a control plan.
                    # Set plan to the result of _display_plan(an empty tuple, now, source_id).
                    plan = _display_plan((), now, source_id)
                    # Set authority to the result of _Authority(identity, source_id, original, effective, status,
                    # outcome, None, plan, zone_states,...).
                    authority = _Authority(identity, source_id, original, effective,
                        # Supply participants to _Authority.
                        status, outcome, None, plan, zone_states, participants, inboxes)
                    # Section 9 turning obligations are not waiver claims. Section
                    # 8 cycle claims retain the trained, explicitly accepted
                    # voluntary waiver protocol under section 11(3).
                    # Set mandatory to a tuple built from a lazy sequence of a tuple containing e at
                    # 'yielding_vehicle_id', e at 'priority_vehicle_id' for e in edges; retain entries satisfying
                    # whether any item is true in a lazy sequence of '9-' in rule for rule in...
                    mandatory = tuple((e["yielding_vehicle_id"], e["priority_vehicle_id"])
                        # Evaluate whether any item is true in a lazy sequence of the text '9-' belongs to rule
                        # for rule in 'applicable_rule_ids' from e; use an empty tuple if absent as part of the
                        # enclosing expression.
                        for e in edges if any("9-" in rule for rule in e.get("applicable_rule_ids", ())))
                    # Set authority.mandatory_inboxes to the result of _deliver_pair_commitments(mandatory,
                    # participants, source_id).
                    authority.mandatory_inboxes = _deliver_pair_commitments(mandatory, participants, source_id)
                    # Set authority.fallback_pairs to the result of _eligible_fallback_pairs(participants, edges,
                    # snapshots, mandatory).
                    authority.fallback_pairs = _eligible_fallback_pairs(participants, edges, snapshots, mandatory)
                    # Update metrics['negotiation_events'] to its current value plus 1.
                    metrics["negotiation_events"] += 1
                    # Set factor_diagnostics to the result of provider.factor_diagnostics(batch_id) when outcome
                    # is a different object from None, otherwise an empty tuple.
                    factor_diagnostics = (provider.factor_diagnostics(batch_id)
                                          # Evaluate outcome is a different object from None as part of the
                                          # enclosing expression.
                                          if outcome is not None else ())
                    # Set latest_policy_factors to factor_diagnostics.
                    latest_policy_factors = factor_diagnostics
                    # Append a dictionary containing event_number, timestamp, status, participants,
                    # mappo_invocation, proposer_actions,... to event_records.
                    event_records.append({
                        # Store metrics at 'negotiation_events' under 'event_number'.
                        "event_number": metrics["negotiation_events"],
                        # Store now under 'timestamp'.
                        # Store status under 'status'.
                        "timestamp": now, "status": status,
                        # Store participants under 'participants'.
                        "participants": participants,
                        # Store the text 'AUTHORIZED' when outcome is a different object from None, otherwise the
                        # text 'NOT_REQUIRED' when status equals the text 'REGULATORY_ORDER_RESOLVED', otherwise
                        # the text 'BLOCKED' under 'mappo_invocation'.
                        "mappo_invocation": ("AUTHORIZED" if outcome is not None
                                             # Evaluate the text 'NOT_REQUIRED' when status equals the text
                                             # 'REGULATORY_ORDER_RESOLVED', otherwise the text 'BLOCKED' as part of
                                             # the enclosing expression.
                                             else "NOT_REQUIRED" if status ==
                                             # Supply the text 'REGULATORY_ORDER_RESOLVED' to the enclosing
                                             # expression.
                                             "REGULATORY_ORDER_RESOLVED" else
                                             "BLOCKED"),
                        # Store outcome.proposer_assignment.claim_action_assignments when outcome, otherwise an
                        # empty tuple under 'proposer_actions'.
                        "proposer_actions": (outcome.proposer_assignment.
                            # Evaluate outcome as part of the enclosing expression.
                            claim_action_assignments if outcome else ()),
                        # Store outcome.responder_assignment.response_action_assignments when outcome, otherwise
                        # an empty tuple under 'responder_actions'.
                        "responder_actions": (outcome.responder_assignment.
                            # Evaluate outcome as part of the enclosing expression.
                            response_action_assignments if outcome else ()),
                        # Store original under 'original_regulatory_graph'.
                        "original_regulatory_graph": original,
                        # Store effective under 'effective_coordination_graph'.
                        "effective_coordination_graph": effective,
                        # Store plan.ready_vehicle_ids under 'ready_vehicle_ids'.
                        "ready_vehicle_ids": plan.ready_vehicle_ids,
                        # Store plan.blocked_vehicle_ids under 'blocked_vehicle_ids'.
                        "blocked_vehicle_ids": plan.blocked_vehicle_ids})
                    # Set event_records[-1]['policy_factor_diagnostics'] to factor_diagnostics.
                    event_records[-1]["policy_factor_diagnostics"] = (
                        # Evaluate factor_diagnostics as part of the enclosing expression.
                        factor_diagnostics)
                    # Run this branch when runtime_observer is a different object from None and whether
                    # runtime_observer exposes the requested attribute.
                    if runtime_observer is not None and hasattr(runtime_observer, "coordination_trace"):
                        # Call runtime_observer.coordination_trace with the supplied arguments.
                        runtime_observer.coordination_trace(now, snapshots, observations)

            # Run this branch when authority is a different object from None.
            if authority is not None:
                # Run this branch when zone_observations is the same object as None.
                if zone_observations is None:
                    # Set zone_observations to the result of PhysicalBranchReplayRunner._observe_zones(helper,
                    # states, movements, authority.zone_states, now, entry_events, clear_events, cleared).
                    zone_observations = PhysicalBranchReplayRunner._observe_zones(
                        # Supply authority.zone_states to PhysicalBranchReplayRunner._observe_zones.
                        helper, states, movements, authority.zone_states, now,
                        # Supply entry_events to PhysicalBranchReplayRunner._observe_zones.
                        entry_events, clear_events, cleared)
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set zone_observations to an empty dictionary.
                zone_observations = {}
            # Set (decisions, control_records) to a tuple containing an empty list, an empty list.
            decisions, control_records = [], []
            # Same-step ideal V2V: each sender announces its own state/path.
            # Full perception remains in the LDM; only pair-relevant messages
            # and pair commitments cross the execution-controller boundary.
            # Set controlled to a set built from queue_heads combined with a set built from authority.member_ids
            # intersected with a set built from states when authority, otherwise an empty set.
            controlled = set(queue_heads) | (set(authority.member_ids) & set(states)
                                             # Evaluate authority as part of the enclosing expression.
                                             if authority else set())
            # Update controlled with the supplied entries.
            controlled.update(ego for ego, controller in ego_controllers.items() if ego in states and
                # Evaluate controller.admission_state belongs to a set containing the text 'COMMITTED_TO_ENTER',
                # the text 'IN_CONFLICT_ZONE' as part of the enclosing expression.
                controller.admission_state in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE"})
            # Set messages to a dictionary of ego mapped to the result of ExecutionStateMessage(ego, movements at
            # ego, states at ego, now, ego from queue_arrivals; use None if absent,...) for ego in controlled.
            messages = {ego: ExecutionStateMessage(ego, movements[ego],
                # Supply ego from queue_arrivals; use None if absent to ExecutionStateMessage.
                states[ego], now, queue_arrivals.get(ego),
                # Supply ego_controllers[ego].admission_state when ego belongs to ego_controllers, otherwise the
                # text 'APPROACHING' to ExecutionStateMessage.
                ego_controllers[ego].admission_state if ego in ego_controllers else "APPROACHING",
                # Supply authority.source_snapshot_id when authority, otherwise an empty tuple to
                # ExecutionStateMessage.
                authority.source_snapshot_id if authority else ()) for ego in controlled}
            # Ideal authenticated transport: each sender attests only its own
            # incident agreements, receipt and queue metadata. No permissions or
            # precomputed order cross this boundary; each ego reconstructs it.
            # Set endpoint_evidence to an empty tuple.
            endpoint_evidence = ()
            # Run this branch when authority and authority.outcome and the requested attribute of provider.
            if authority and authority.outcome and getattr(provider, "uses_mappo_behavior_policy", True):
                # Set endpoint_evidence to a tuple built from a lazy sequence of the result of
                # EndpointEvidence(sender, now, authority.source_snapshot_id, a tuple built from
                # sorted(authority.member_ids),...) for sender in the sorted values from authority.member_ids;
                # retain entries satisfying sender belongs to messages.
                endpoint_evidence = tuple(EndpointEvidence(sender, now,
                    # Supply a tuple built from the sorted values from authority.member_ids to EndpointEvidence.
                    authority.source_snapshot_id, tuple(sorted(authority.member_ids)),
                    # Supply sender from authority.commitment_inboxes; use an empty tuple if absent to
                    # EndpointEvidence.
                    authority.commitment_inboxes.get(sender, ()),
                    # Supply sender from authority.mandatory_inboxes; use an empty tuple if absent to
                    # EndpointEvidence.
                    authority.mandatory_inboxes.get(sender, ()),
                    # Supply a tuple built from the sorted values from a lazy sequence of peer for pair in
                    # authority.fallback_pairs; retain entries satisfying sender in pair and peer != sender to
                    # EndpointEvidence.
                    tuple(sorted(peer for pair in authority.fallback_pairs for peer in pair
                        # Evaluate sender belongs to pair and peer differs from sender as part of the enclosing
                        # expression.
                        if sender in pair and peer != sender)), True, queue_arrivals.get(sender))
                    # Evaluate the sorted values from authority.member_ids as part of the enclosing expression.
                    for sender in sorted(authority.member_ids) if sender in messages)
            # Iterate over the sorted values from key/value pairs from states, binding each item to (ego, state).
            for ego, state in sorted(states.items()):
                # Set own_snapshot to the next item from a lazy sequence of s for s in snapshots; retain entries
                # satisfying s at 'ego_id' equals ego.
                own_snapshot = next((s for s in snapshots if s["ego_id"] == ego), None)
                # Set complete to authority is a different object from None and ego belongs to
                # authority.member_ids and authority.status does not belong to BLOCKED and the negation of the
                # requested attribute of provider and authority.status belongs to NEGOTIABLE.
                complete = (authority is not None and ego in authority.member_ids
                            # Evaluate authority.status does not belong to BLOCKED as part of the enclosing
                            # expression.
                            and authority.status not in BLOCKED and
                            # Evaluate the negation of the requested attribute of provider and authority.status
                            # belongs to NEGOTIABLE as part of the enclosing expression.
                            not (getattr(provider, "rules_only", False) and
                                 # Evaluate authority.status belongs to NEGOTIABLE as part of the enclosing
                                 # expression.
                                 authority.status in NEGOTIABLE))
                # Run this branch when authority is the same object as None and the negation of original.
                if authority is None and not original:
                    # Set complete to own_snapshot is a different object from None and own_snapshot at
                    # 'negotiation_status' belongs to a set containing the text 'NO_ACTIVE_CONFLICT', the text
                    # 'REGULATORY_ORDER_RESOLVED'.
                    complete = (own_snapshot is not None and
                        # Evaluate own_snapshot at 'negotiation_status' belongs to a set containing the text
                        # 'NO_ACTIVE_CONFLICT', the text 'REGULATORY_ORDER_RESOLVED' as part of the enclosing
                        # expression.
                        own_snapshot["negotiation_status"] in
                        # Evaluate a set containing the text 'NO_ACTIVE_CONFLICT', the text
                        # 'REGULATORY_ORDER_RESOLVED' as part of the enclosing expression.
                        {"NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"})
                # Run this branch when own_snapshot and 'movement_declaration_errors' from own_snapshot; use None
                # if absent.
                if own_snapshot and own_snapshot.get("movement_declaration_errors"):
                    # Set complete to False.
                    complete = False
                # Set inbox to ego from authority.commitment_inboxes; use an empty tuple if absent when authority,
                # otherwise an empty tuple.
                inbox = authority.commitment_inboxes.get(ego, ()) if authority else ()
                # Set peer_ids to a set of c.priority_vehicle_id for c in inbox; retain entries satisfying
                # c.yielding_vehicle_id equals ego.
                peer_ids = {c.priority_vehicle_id for c in inbox if c.yielding_vehicle_id == ego}
                # Update peer_ids with the supplied entries.
                peer_ids.update(peer for peer in controlled if peer != ego and
                    # Evaluate vehicle_approaches at peer differs from vehicle_approaches at ego as part of the
                    # enclosing expression.
                    vehicle_approaches[peer] != vehicle_approaches[ego])
                # Set context to the result of EgoExecutionContext(ego, state, movements at ego, now, inbox, a
                # tuple built from a lazy sequence of messages at peer...).
                context = EgoExecutionContext(ego, state, movements[ego], now,
                    # Supply a tuple built from a lazy sequence of messages at peer for peer in the sorted values
                    # from peer_ids; retain entries satisfying peer belongs to messages to EgoExecutionContext.
                    inbox, tuple(messages[peer] for peer in sorted(peer_ids) if peer in messages),
                    # Supply now when complete, otherwise None to EgoExecutionContext.
                    complete, now if complete else None, ego in controlled,
                    # Supply strict_admission as True.
                    strict_admission=True,
                    # Supply coordination_epoch as authority.source_snapshot_id when authority, otherwise an empty
                    # tuple.
                    coordination_epoch=authority.source_snapshot_id if authority else (),
                    # Supply mappo_receipt as a Boolean built from authority and authority.outcome and the
                    # requested attribute of provider.
                    mappo_receipt=bool(authority and authority.outcome and
                        # Evaluate the requested attribute of provider as part of the enclosing expression.
                        getattr(provider, "uses_mappo_behavior_policy", True)),
                    # Supply fallback_peer_ids as a tuple built from a lazy sequence of peer for pair in
                    # authority.fallback_pairs; retain entries satisfying ego in pair and peer != ego when
                    # authority, otherwise an empty tuple.
                    fallback_peer_ids=tuple(peer for pair in authority.fallback_pairs for peer in pair if ego in pair and peer != ego) if authority else (),
                    # Supply mandatory_commitments as ego from authority.mandatory_inboxes; use an empty tuple if
                    # absent when authority, otherwise an empty tuple.
                    mandatory_commitments=authority.mandatory_inboxes.get(ego, ()) if authority else (),
                    # Supply queue_arrival_seconds as ego from queue_arrivals; use None if absent.
                    queue_arrival_seconds=queue_arrivals.get(ego),
                    # Supply fallback_endpoint_evidence as endpoint_evidence when ego belongs to controlled,
                    # otherwise an empty tuple.
                    fallback_endpoint_evidence=endpoint_evidence if ego in controlled else (),
                    # Supply own_execution_message as ego from messages; use None if absent.
                    # Supply mandatory_aware_fallback as True.
                    own_execution_message=messages.get(ego), mandatory_aware_fallback=True)
                # Run this branch when ego does not belong to ego_controllers.
                if ego not in ego_controllers:
                    # Set ego_controllers[ego] to the result of DecentralizedEgoExecutionController(paths, zones).
                    ego_controllers[ego] = DecentralizedEgoExecutionController(paths, zones)
                # Set ego_controller to ego_controllers at ego.
                ego_controller = ego_controllers[ego]
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Set execution_started to the result of perf_counter_ns().
                    execution_started = perf_counter_ns()
                    # Set decision to the result of ego_controller.decide(context).
                    decision = ego_controller.decide(context)
                    # Set decision to the result of ego_controller.constrain(context, decision, traci.vehicle,
                    # SIM_TIME_STEP).
                    decision = ego_controller.constrain(context, decision,
                        # Supply traci.vehicle to ego_controller.constrain.
                        traci.vehicle, SIM_TIME_STEP)
                    # Run this branch when runtime_observer is a different object from None.
                    if runtime_observer is not None:
                        # Call runtime_observer.execution with the supplied arguments.
                        runtime_observer.execution(perf_counter_ns() - execution_started,
                                                   # Supply decision to runtime_observer.execution.
                                                   decision)
                        # Run this branch when whether runtime_observer exposes the requested attribute.
                        if hasattr(runtime_observer, "decision_trace"):
                            # Call runtime_observer.decision_trace with the supplied arguments.
                            runtime_observer.decision_trace(context, decision, ego_controller.admission_state)
                # Handle RuntimeError as error using the recovery steps below.
                except RuntimeError as error:
                    # Run this branch when runtime_observer is a different object from None and whether
                    # runtime_observer exposes the requested attribute.
                    if runtime_observer is not None and hasattr(runtime_observer, "failure_trace"):
                        # Call runtime_observer.failure_trace with the supplied arguments.
                        runtime_observer.failure_trace(context, str(error), ego_controller.admission_state)
                    # Run this branch when a string built from error equals the text
                    # 'BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'.
                    if str(error) == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE":
                        # Update metrics['blocked_zone_violations'] to its current value plus 1.
                        metrics["blocked_zone_violations"] += 1
                    # Re-raise the active exception.
                    raise
                # Append decision to decisions.
                decisions.append(decision)
                # Extend control_records with decision.speed_constraints.
                control_records.extend(decision.speed_constraints)
                # Set native_event to the result of ego_controller.native_hold.synchronize(context, decision,
                # paths, traci.vehicle).
                native_event = ego_controller.native_hold.synchronize(context, decision, paths, traci.vehicle)
                # Run this branch when native_event.
                if native_event:
                    # Append a dictionary built from the supplied values to diagnostics.
                    diagnostics.append(dict(event=native_event, ego_id=ego, timestamp=now,
                        # Supply permission as decision.permission.
                        # Supply protocol as NATIVE_HOLD_VERSION.
                        permission=decision.permission, protocol=NATIVE_HOLD_VERSION))
                # Run this branch when decision.requested_speed_mps is a different object from None.
                if decision.requested_speed_mps is not None:
                    # Request the specified SUMO speed using traci.vehicle.setSpeed.
                    traci.vehicle.setSpeed(ego, decision.requested_speed_mps)
                    # Add ego to constrained_ids.
                    constrained_ids.add(ego)
                # Run this branch when ego belongs to constrained_ids.
                elif ego in constrained_ids:
                    # Request the specified SUMO speed using traci.vehicle.setSpeed.
                    traci.vehicle.setSpeed(ego, -1.0)
                    # Discard ego from constrained_ids if present.
                    constrained_ids.discard(ego)
            # Set held to a set of d.ego_id for d in decisions; retain entries satisfying d.permission equals the
            # text 'SAFE_HOLD'.
            held = {d.ego_id for d in decisions if d.permission == "SAFE_HOLD"}
            # Update metrics['safe_hold_activations'] to its current value plus the number of entries in held
            # minus prior_hold_ids.
            metrics["safe_hold_activations"] += len(held - prior_hold_ids)
            # Set prior_hold_ids to held.
            prior_hold_ids = held
            # Set plan to the result of _display_plan(decisions, now, authority.source_snapshot_id when authority,
            # otherwise an empty tuple).
            plan = _display_plan(decisions, now,
                # Supply authority.source_snapshot_id when authority, otherwise an empty tuple to _display_plan.
                authority.source_snapshot_id if authority else ())
            # Run this branch when authority.
            if authority:
                # Set authority.initial_plan to plan.
                authority.initial_plan = plan
                # Run this branch when authority.outcome is a different object from None and the negation of
                # authority.shield_recorded and the requested attribute of provider.
                if authority.outcome is not None and not authority.shield_recorded and getattr(provider, "uses_mappo_behavior_policy", True):
                    # Set rejected to whether any item is true in a lazy sequence of d.shield_rejection_reason or
                    # d.permission equals 'SAFE_HOLD' or d.reason belongs to {'UNORDERED_PHYSICAL_CONFLICT',
                    # 'MANDATORY_PRECEDENCE_REMOVED', 'RECIPROCAL_PHYSICAL_COMMITMENT'} for d in decisions; retain
                    # entries satisfying d.ego_id belongs to authority.member_ids.
                    rejected = any(d.shield_rejection_reason or d.permission == "SAFE_HOLD" or d.reason in {
                        "UNORDERED_PHYSICAL_CONFLICT", "MANDATORY_PRECEDENCE_REMOVED",
                        # Evaluate d.ego_id belongs to authority.member_ids as part of the enclosing expression.
                        "RECIPROCAL_PHYSICAL_COMMITMENT"} for d in decisions if d.ego_id in authority.member_ids)
                    # Set fallback to whether any item is true in a lazy sequence of d.fallback_pairs for d in
                    # decisions.
                    fallback = any(d.fallback_pairs for d in decisions)
                    # Set metrics['mappo_negotiation_events'] to 'mappo_negotiation_events' from metrics; use 0 if
                    # absent plus 1.
                    metrics["mappo_negotiation_events"] = metrics.get("mappo_negotiation_events", 0) + 1
                    # Set key to the text 'mappo_outcomes_rejected_by_shield' when rejected, otherwise the text
                    # 'mappo_outcomes_accepted'.
                    key = "mappo_outcomes_rejected_by_shield" if rejected else "mappo_outcomes_accepted"
                    # Set metrics[key] to key from metrics; use 0 if absent plus 1.
                    metrics[key] = metrics.get(key, 0) + 1
                    # Set metrics['mappo_outcomes_rejected_by_safety_shield'] to
                    # 'mappo_outcomes_rejected_by_shield' from metrics; use 0 if absent.
                    metrics["mappo_outcomes_rejected_by_safety_shield"] = metrics.get("mappo_outcomes_rejected_by_shield", 0)
                    # Set metrics['fallback_activations'] to 'fallback_activations' from metrics; use 0 if absent
                    # plus an integer built from fallback.
                    metrics["fallback_activations"] = metrics.get("fallback_activations", 0) + int(fallback)
                    # Set metrics['fallback_rate'] to metrics at 'fallback_activations' divided by metrics at
                    # 'mappo_negotiation_events'.
                    metrics["fallback_rate"] = metrics["fallback_activations"] / metrics["mappo_negotiation_events"]
                    # Set event_records[-1]['execution_outcome'] to the text 'MAPPO_WITH_SAFETY_FALLBACK' when
                    # fallback, otherwise the text 'RULE_RESOLVED' when rejected and plan.ready_vehicle_ids,
                    # otherwise the text 'SAFE_HOLD' when rejected, otherwise the text 'MAPPO_DIRECT'.
                    event_records[-1]["execution_outcome"] = ("MAPPO_WITH_SAFETY_FALLBACK" if fallback else "RULE_RESOLVED" if rejected and plan.ready_vehicle_ids else "SAFE_HOLD" if rejected else "MAPPO_DIRECT")
                    # Set authority.shield_recorded to True.
                    authority.shield_recorded = True
                # Run this branch when authority.outcome is the same object as None and event_records and
                # event_records[-1] at 'timestamp' equals now.
                elif authority.outcome is None and event_records and event_records[-1]["timestamp"] == now:
                    # Set event_records[-1]['execution_outcome'] to the text 'RULE_RESOLVED' when
                    # plan.ready_vehicle_ids, otherwise the text 'SAFE_HOLD'.
                    event_records[-1]["execution_outcome"] = "RULE_RESOLVED" if plan.ready_vehicle_ids else "SAFE_HOLD"
            # Run this branch when event_records and event_records[-1] at 'timestamp' equals now.
            if event_records and event_records[-1]["timestamp"] == now:
                # Set event_records[-1]['ready_vehicle_ids'] to plan.ready_vehicle_ids.
                event_records[-1]["ready_vehicle_ids"] = plan.ready_vehicle_ids
                # Set event_records[-1]['blocked_vehicle_ids'] to plan.blocked_vehicle_ids.
                event_records[-1]["blocked_vehicle_ids"] = plan.blocked_vehicle_ids
                # Call _print_event with the supplied arguments.
                _print_event(metrics["negotiation_events"], now, participants,
                    # Supply authority.outcome when authority, otherwise None to _print_event.
                    status, original, authority.outcome if authority else None,
                    # Supply latest_policy_factors to _print_event.
                    plan, len(completed_ids), scheduled_count, latest_policy_factors,
                    # Supply selection_rule as the requested attribute of provider.
                    selection_rule=getattr(provider, "selection_rule", PRESENTATION_SELECTION_RULE))
            # Set metrics['negotiation_event_count'] to metrics at 'negotiation_events'.
            metrics["negotiation_event_count"] = metrics["negotiation_events"]
            # Set metrics['centralized_critic_runtime_calls'] to provider.runtime_critic_calls.
            metrics["centralized_critic_runtime_calls"] = provider.runtime_critic_calls
            # Update visualizer with the supplied entries.
            visualizer.update(states, participants if authority else (),
                              # Supply plan.blocked_vehicle_ids to visualizer.update.
                              plan.ready_vehicle_ids, plan.blocked_vehicle_ids)
            # Run this branch when browser.
            if browser:
                # Call browser.publish with the supplied arguments.
                browser.publish(
                    # Supply simulation_time as now.
                    # Supply map_state as map_state.
                    # Supply running as True.
                    simulation_time=now, map_state=map_state, running=True,
                    # Supply status as authority.status when authority, otherwise status.
                    status=(authority.status if authority else status),
                    # Supply participants as participants.
                    participants=participants,
                    # Supply ready as plan.ready_vehicle_ids.
                    ready=plan.ready_vehicle_ids,
                    # Supply blocked as plan.blocked_vehicle_ids.
                    blocked=plan.blocked_vehicle_ids,
                    # Supply original_graph as authority.original_graph when authority, otherwise original.
                    original_graph=(authority.original_graph
                                    # Evaluate authority as part of the enclosing expression.
                                    if authority else original),
                    # Supply effective_graph as authority.effective_graph when authority, otherwise original.
                    effective_graph=(authority.effective_graph
                                     # Evaluate authority as part of the enclosing expression.
                                     if authority else original),
                    # Supply mappo_invocation as the result of displayed_mappo_invocation(authority.status when
                    # authority, otherwise status, a Boolean built from authority and...).
                    mappo_invocation=displayed_mappo_invocation(
                        # Supply authority.status when authority, otherwise status to displayed_mappo_invocation.
                        authority.status if authority else status,
                        # Supply a Boolean built from authority and authority.outcome to
                        # displayed_mappo_invocation.
                        bool(authority and authority.outcome)),
                    # Supply completed as the number of entries in completed_ids.
                    # Supply scheduled as scheduled_count.
                    completed=len(completed_ids), scheduled=scheduled_count,
                    # Supply scenario_id as scenario_id.
                    # Supply scientific_states as states.
                    scenario_id=scenario_id, scientific_states=states,
                    # Supply observations as observations.
                    # Supply snapshots as snapshots.
                    # Supply plan as plan.
                    observations=observations, snapshots=snapshots, plan=plan,
                    # Supply control_records as control_records.
                    control_records=control_records,
                    # Supply policy_factors as latest_policy_factors when authority and authority.outcome,
                    # otherwise an empty tuple.
                    policy_factors=latest_policy_factors if authority and authority.outcome else (),
                    # Supply execution_decisions as decisions.
                    execution_decisions=decisions,
                    # Supply coordination_participants as authority.member_ids when authority, otherwise an empty
                    # tuple.
                    coordination_participants=authority.member_ids if authority else (),
                    # Supply coordination_timestamp as authority.source_snapshot_id at 1 when authority and
                    # authority.outcome, otherwise None.
                    coordination_timestamp=authority.source_snapshot_id[1] if authority and authority.outcome else None,
                    # Supply run_id as presentation_run_id.
                    run_id=presentation_run_id,
                    # Supply events as the result of _presentation_timeline(event_records, diagnostics).
                    events=_presentation_timeline(event_records, diagnostics),
                    # Supply run_metrics as metrics.
                    run_metrics=metrics)
                # Call browser.pace with the supplied arguments.
                browser.pace()
            # Run this branch when the number of entries in completed_ids equals scheduled_count.
            if len(completed_ids) == scheduled_count:
                # Leave the nearest enclosing loop immediately.
                break
        # Set metrics['presentation_vehicles_completed'] to the number of entries in completed_ids.
        metrics["presentation_vehicles_completed"] = len(completed_ids)
        # Set metrics['unfinished_vehicles'] to scheduled_count minus the number of entries in completed_ids.
        metrics["unfinished_vehicles"] = scheduled_count - len(completed_ids)
    # Handle Exception as error using the recovery steps below.
    except Exception as error:
        # Set failure to error.
        failure = error
        # Append a dictionary containing event, timestamp, error to diagnostics.
        diagnostics.append({"event": "PRESENTATION_FAILED",
            # Store environment.current_time under 'timestamp'.
            # Store a string built from error under 'error'.
            "timestamp": environment.current_time, "error": str(error)})
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Set metrics['presentation_vehicles_completed'] to the number of entries in completed_ids.
        metrics["presentation_vehicles_completed"] = len(completed_ids)
        # Set metrics['unfinished_vehicles'] to scheduled_count minus the number of entries in completed_ids.
        metrics["unfinished_vehicles"] = scheduled_count - len(completed_ids)
        # Run this branch when browser.
        if browser:
            # Call browser.publish with the supplied arguments.
            browser.publish(
                # Supply simulation_time as environment.current_time.
                # Supply map_state as map_state.
                simulation_time=environment.current_time, map_state=map_state,
                # Supply running as False.
                running=False,
                # Supply status as the text 'FAILED' when failure, otherwise the text 'USER_STOPPED' when
                # stopped_by_user, otherwise the text 'FINISHED' when len(completed_ids) equals scheduled_count,
                # otherwise the text 'INCOMPLETE'.
                status=("FAILED" if failure else "USER_STOPPED" if stopped_by_user
                        # Evaluate the text 'FINISHED' when the number of entries in completed_ids equals
                        # scheduled_count, otherwise the text 'INCOMPLETE' as part of the enclosing expression.
                        else "FINISHED" if len(completed_ids) == scheduled_count else "INCOMPLETE"),
                # Supply completed as the number of entries in completed_ids.
                completed=len(completed_ids),
                # Supply scheduled as scheduled_count.
                # Supply scenario_id as scenario_id.
                scheduled=scheduled_count, scenario_id=scenario_id,
                # Supply run_metrics as metrics.
                # Supply force as True.
                run_metrics=metrics, force=True)
        # Call environment.close with the supplied arguments.
        # Update closes to its current value plus 1.
        environment.close(); closes += 1

    # Set policy_hash_after to the result of _sha256(POLICY_PATH).
    policy_hash_after = _sha256(POLICY_PATH)
    # Set metrics['selected_policy_hash_unchanged'] to policy_hash_before equals policy_hash_after.
    metrics["selected_policy_hash_unchanged"] = policy_hash_before == policy_hash_after
    # Set result to a dictionary containing evidence_classification, movement_declaration_protocol,...
    result = {"evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
        # Store PROTOCOL_VERSION when movement_protocol, otherwise the text 'DISABLED_LEGACY' under
        # 'movement_declaration_protocol'.
        "movement_declaration_protocol": PROTOCOL_VERSION if movement_protocol else "DISABLED_LEGACY",
        # Store FALLBACK_VERSION under 'supplementary_fallback_protocol'.
        "supplementary_fallback_protocol": FALLBACK_VERSION,
        # Store NATIVE_HOLD_VERSION under 'native_junction_hold_protocol'.
        "native_junction_hold_protocol": NATIVE_HOLD_VERSION,
        "queue_following_protocol": "NATIVE_FOLLOWING_PROTECTED_ENTRY_V2",
        "execution_version": "EGO_ADMISSION_CCR_V1_NATIVE_RELEASE",
        # Store presentation_run_id under 'presentation_run_id'.
        "presentation_run_id": presentation_run_id,
        # Store the text 'FAILED' when failure, otherwise the text 'USER_STOPPED' when stopped_by_user, otherwise
        # the text 'COMPLETED' when len(completed_ids) equals scheduled_count, otherwise the text 'INCOMPLETE'
        # under 'run_status'.
        "run_status": ("FAILED" if failure else "USER_STOPPED" if stopped_by_user else "COMPLETED"
                       # Evaluate the number of entries in completed_ids equals scheduled_count as part of the
                       # enclosing expression.
                       if len(completed_ids) == scheduled_count else "INCOMPLETE"),
        # Store started_at under 'started_at_utc'.
        "started_at_utc": started_at,
        # Store the result of datetime.now(timezone.utc).isoformat() under 'ended_at_utc'.
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        # Store a floating-point number built from environment.current_time under
        # 'actual_simulation_time_seconds'.
        "actual_simulation_time_seconds": float(environment.current_time),
        # Store False under 'quantitative_model_selection_evidence'.
        "quantitative_model_selection_evidence": False,
        # Store False under 'validation_evidence'.
        # Store False under 'held_out_evidence'.
        "validation_evidence": False, "held_out_evidence": False,
        "selected_candidate_id": "E5",
        # Store scenario_id under 'presentation_scenario_id'.
        "presentation_scenario_id": scenario_id,
        "inference_mode": "DETERMINISTIC_MASKED_ARGMAX_PRESENTATION_ONLY",
        "selected_policy_weights": "E5",
        # Store False under 'quantitative_evidence'.
        "quantitative_evidence": False,
        # Store the requested attribute of provider under 'presentation_semantic_selection_rule'.
        "presentation_semantic_selection_rule": getattr(provider, "selection_rule", PRESENTATION_SELECTION_RULE),
        # Store the result of str(POLICY_PATH).replace(the text '\\', the text '/') under 'selected_policy_path'.
        "selected_policy_path": str(POLICY_PATH).replace("\\", "/"),
        # Store policy_hash_before under 'policy_sha256_before'.
        "policy_sha256_before": policy_hash_before,
        # Store policy_hash_after under 'policy_sha256_after'.
        "policy_sha256_after": policy_hash_after,
        # Store policy_hash_before equals policy_hash_after under 'policy_hash_unchanged'.
        "policy_hash_unchanged": policy_hash_before == policy_hash_after,
        # Store policy_hash_before differs from policy_hash_after under 'selected_policy_modified'.
        "selected_policy_modified": policy_hash_before != policy_hash_after,
        # Store False under 'centralized_critic_used_for_action'.
        "centralized_critic_used_for_action": False,
        # Store True under 'decentralized_execution'.
        "decentralized_execution": True,
        # Store False under 'centralized_execution_graph_used_for_control'.
        "centralized_execution_graph_used_for_control": False,
        # Store provider.runtime_critic_calls under 'centralized_critic_calls'.
        "centralized_critic_calls": provider.runtime_critic_calls,
        # Store 0 under 'training_operations'.
        # Store 0 under 'backward_calls'.
        "training_operations": 0, "backward_calls": 0,
        # Store 0 under 'optimizer_steps'.
        # Store 0 under 'parameter_updates'.
        "optimizer_steps": 0, "parameter_updates": 0,
        # Store 0 under 'route_truth_actor_leakage'.
        # Store 0 under 'held_out_scenarios_consumed'.
        "route_truth_actor_leakage": 0, "held_out_scenarios_consumed": 0,
        # Store starts under 'sumo_start_count'.
        # Store closes under 'sumo_close_count'.
        "sumo_start_count": starts, "sumo_close_count": closes,
        # Store SIM_TIME_STEP under 'simulation_step_seconds'.
        "simulation_step_seconds": SIM_TIME_STEP,
        # Store a floating-point number built from duration_seconds under 'presentation_duration_seconds'.
        "presentation_duration_seconds": float(duration_seconds),
        # Store a dictionary of key mapped to a list of x.movement_path_id for x in value for (key, value) in
        # key/value pairs from schedule under 'presentation_schedule'.
        "presentation_schedule": {key: [x.movement_path_id for x in value]
                                  # Evaluate key/value pairs from schedule as part of the enclosing expression.
                                  for key, value in schedule.items()},
        # Store the text 'PREDECLARED_PRESENTATION_' plus admission_mode under 'schedule_source'.
        "schedule_source": "PREDECLARED_PRESENTATION_" + admission_mode,
        # Store departures under 'actual_departure_seconds'.
        "actual_departure_seconds": departures,
        # Store demand_times under 'scheduled_departure_seconds'.
        "scheduled_departure_seconds": demand_times,
        # Store a dictionary of ego mapped to departures at ego minus demand_times at ego for ego in departures
        # under 'insertion_delay_seconds'.
        "insertion_delay_seconds": {ego: departures[ego] - demand_times[ego]
                                   # Evaluate departures as part of the enclosing expression.
                                   for ego in departures},
        # Store a tuple built from a lazy sequence of ego for ego in submitted_ids; retain entries satisfying ego
        # does not belong to departures under 'pending_insertion_vehicle_ids'.
        "pending_insertion_vehicle_ids": tuple(ego for ego in submitted_ids
                                              # Evaluate ego does not belong to departures as part of the enclosing
                                              # expression.
                                              if ego not in departures),
        "mappo_demo_case_source":
            "EXISTING_TRAINING_SIDE_ILLUSTRATIVE_CASE",
        # Store a tuple containing the text 'TRAINING_MANIFEST_ROUTE_STRUCTURE', a tuple containing the text
        # 'E_IN_0_STRAIGHT', the text... under 'mappo_demo_case_identifier'.
        "mappo_demo_case_identifier": (
            "TRAINING_MANIFEST_ROUTE_STRUCTURE",
            # Include a tuple containing the text 'E_IN_0_STRAIGHT', the text 'N_IN_0_STRAIGHT', the text
            # 'S_IN_0_RIGHT', the text 'W_IN_0_LEFT' in this tuple.
            ("E_IN_0_STRAIGHT", "N_IN_0_STRAIGHT",
             "S_IN_0_RIGHT", "W_IN_0_LEFT")),
        # Store False under 'training_demo_case_search'.
        "training_demo_case_search": False,
        # Store False under 'validation_or_held_out_search'.
        "validation_or_held_out_search": False,
        # Store spawned_ids under 'spawned_vehicle_ids'.
        "spawned_vehicle_ids": spawned_ids,
        # Store completed_ids under 'completed_vehicle_ids'.
        "completed_vehicle_ids": completed_ids,
        # Store metrics under 'metrics'.
        # Store event_records under 'events'.
        "metrics": metrics, "events": event_records,
        # Store diagnostics under 'diagnostics'.
        "diagnostics": diagnostics}
    # Run this branch when browser.
    if browser:
        # Set result['presentation_vehicle_history'] to the result of browser.presentation_vehicle_history().
        result["presentation_vehicle_history"] = (
            # Evaluate the result of browser.presentation_vehicle_history() as part of the enclosing expression.
            browser.presentation_vehicle_history())
    # Run this branch when the negation of result at 'policy_hash_unchanged'.
    if not result["policy_hash_unchanged"]:
        # Raise RuntimeError with the text 'SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO' to stop this execution
        # path.
        raise RuntimeError("SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO")
    # Set result['runtime_error'] to a string built from failure when failure, otherwise None.
    result["runtime_error"] = str(failure) if failure else None
    # Run this branch when persist_presentation.
    if persist_presentation:
        # Call write_panel_outputs with the supplied arguments.
        write_panel_outputs(result, output_dir)
    # Run this branch when failure is a different object from None and the negation of return_failed_result.
    if failure is not None and not return_failed_result:
        # Raise failure to stop this execution path.
        raise failure
    # Return result to the caller.
    return result

# Backward-compatible callable alias; the operational implementation is shared.
# Set run_panel_demo to run_runtime_simulation.
run_panel_demo = run_runtime_simulation
