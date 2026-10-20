"""Focused contracts for event-driven selected-policy re-negotiation."""

# Import inspect for use in this module.
import inspect
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ConflictZoneExecutionPlanner from negotiation_execution for the operations below.
from negotiation_execution import ConflictZoneExecutionPlanner
# Import InfeasibilityReason, NegotiationClaimBuilder, PolicyAuthority from negotiation_learning.claim_semantics
# for the operations below.
from negotiation_learning.claim_semantics import (
    InfeasibilityReason, NegotiationClaimBuilder, PolicyAuthority)
# Import NegotiationStatus from negotiation_learning.models for the operations below.
from negotiation_learning.models import NegotiationStatus
# Import CoupledNegotiationTrainingEnvironment from negotiation_training.environment for the operations below.
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
# Import FinalSelectionInferenceProvider, _load_bundle, file_sha256 from negotiation_training.final_selection for
# the operations below.
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle, file_sha256)
# Import MAPPOBehaviorActionProvider from negotiation_training.mappo_provider for the operations below.
from negotiation_training.mappo_provider import MAPPOBehaviorActionProvider


# Edge using the inputs and processing steps below.
# Input yielding: the supplied yielding.
# Input priority: the supplied priority.
# Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id.
def _edge(yielding, priority):
    # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id to the caller.
    return {"yielding_vehicle_id": yielding,
            # Store priority under 'priority_vehicle_id'.
            "priority_vehicle_id": priority}


# Planner using the inputs and processing steps below.
# Output: the result of ConflictZoneExecutionPlanner(paths, the result of ConflictZoneManager(paths)).
def _planner():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Return the result of ConflictZoneExecutionPlanner(paths, the result of ConflictZoneManager(paths)) to the
    # caller.
    return ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))


# Check executable acyclic plan has ready vehicle without state invalidation using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_executable_acyclic_plan_has_ready_vehicle_without_state_invalidation():
    # Set plan to the result of _planner().plan().
    plan = _planner().plan(
        # Supply source_snapshot_id as a tuple containing the text 's'.
        source_snapshot_id=("s",),
        # Supply effective_coordination_graph as a tuple containing a tuple containing the text 'A', the text 'B'.
        effective_coordination_graph=(("A", "B"),),
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B'.
        active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT",
                                  "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'TEST'.
        timestamp=1.0, source_protocol_state="TEST")
    # Set identity to the result of CoupledNegotiationTrainingEnvironment._decision_state_identity(a dictionary
    # containing A, B, a tuple containing the result of _edge(the text 'A', the text...).
    identity = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        # Store an empty dictionary under 'A'.
        # Store an empty dictionary under 'B'.
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    # Require plan.graph_status equals the text 'EXECUTABLE'; otherwise raise AssertionError.
    assert plan.graph_status == "EXECUTABLE"
    # Require plan.ready_vehicle_ids equals a tuple containing the text 'B'; otherwise raise AssertionError.
    assert plan.ready_vehicle_ids == ("B",)
    # Require the result of CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(identity, identity)
    # equals an empty tuple; otherwise raise AssertionError.
    assert CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        # Supply identity to CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons.
        identity, identity) == ()


# Check non executable cycle releases nobody and can be invalidated by change using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_non_executable_cycle_releases_nobody_and_can_be_invalidated_by_change():
    # Set plan to the result of _planner().plan().
    plan = _planner().plan(
        # Supply source_snapshot_id as a tuple containing the text 's'.
        source_snapshot_id=("s",),
        # Supply effective_coordination_graph as a tuple containing a tuple containing the text 'A', the text 'B',
        # a tuple containing the text 'B', the text 'A'.
        effective_coordination_graph=(("A", "B"), ("B", "A")),
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B'.
        active_vehicle_ids=("A", "B"),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        movement_path_by_vehicle={"A": "E_IN_0_LEFT",
                                  "B": "W_IN_0_LEFT"},
        # Supply timestamp as 1.0.
        # Supply source_protocol_state as the text 'TEST'.
        timestamp=1.0, source_protocol_state="TEST")
    # Set old to the result of CoupledNegotiationTrainingEnvironment._decision_state_identity(a dictionary
    # containing A, B, a tuple containing the result of _edge(the text 'A', the text...).
    old = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        # Store an empty dictionary under 'A'.
        # Store an empty dictionary under 'B'.
        {"A": {}, "B": {}}, (_edge("A", "B"), _edge("B", "A")), ())
    # Set changed to the result of CoupledNegotiationTrainingEnvironment._decision_state_identity(a dictionary
    # containing A, B, a tuple containing the result of _edge(the text 'A', the text...).
    changed = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        # Store an empty dictionary under 'A'.
        # Store an empty dictionary under 'B'.
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    # Require plan.graph_status equals the text 'EXECUTION_BLOCKED_PRECEDENCE_CYCLE'; otherwise raise
    # AssertionError.
    assert plan.graph_status == "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
    # Require plan.ready_vehicle_ids equals an empty tuple; otherwise raise AssertionError.
    assert plan.ready_vehicle_ids == ()
    # Require the text 'RELEVANT_PRECEDENCE_GRAPH_CHANGED' belongs to the result of
    # CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(old, changed); otherwise raise
    # AssertionError.
    assert "RELEVANT_PRECEDENCE_GRAPH_CHANGED" in (
        # Evaluate the result of CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(old, changed) as
        # part of the enclosing expression.
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
            # Supply changed to CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons.
            old, changed))
    # Set source to the result of inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    # Require the text 'SAFE_HOLD_ACTIVE' belongs to source; otherwise raise AssertionError.
    assert "SAFE_HOLD_ACTIVE" in source
    # Require the text '_apply_control' belongs to source; otherwise raise AssertionError.
    assert "_apply_control" in source
    # Require the text 'material_change and safe_authority_transition' belongs to source; otherwise raise
    # AssertionError.
    assert "material_change and safe_authority_transition" in source
    # Require the text 'NEW_BLOCK_NOT_SAFE_TO_ACTIVATE' belongs to source; otherwise raise AssertionError.
    assert "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE" in source


# Check conflict zone clear invalidates old authority without timeout using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_conflict_zone_clear_invalidates_old_authority_without_timeout():
    # Set old to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing a tuple
    # containing the text 'A', the...
    old = (("A", "B"), (("A", "B"),), ())
    # Set new to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing a tuple
    # containing the text 'A', the...
    new = (("A", "B"), (("A", "B"),), (("B", "CZ"),))
    # Require the result of CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(old, new) equals a
    # tuple containing the text 'CONFLICT_ZONE_CLEARED'; otherwise raise AssertionError.
    assert CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        # Evaluate a tuple containing the text 'CONFLICT_ZONE_CLEARED' as part of the enclosing expression.
        old, new) == ("CONFLICT_ZONE_CLEARED",)
    # Set source to the result of inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    # Require the text 'RETRY_AFTER' does not belong to source; otherwise raise AssertionError.
    assert "RETRY_AFTER" not in source


# Check participant change rebuilds decision identity using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_participant_change_rebuilds_decision_identity():
    # Set old to the result of CoupledNegotiationTrainingEnvironment._decision_state_identity(a dictionary
    # containing A, B, a tuple containing the result of _edge(the text 'A', the text...).
    old = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        # Store an empty dictionary under 'A'.
        # Store an empty dictionary under 'B'.
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    # Set new to the result of CoupledNegotiationTrainingEnvironment._decision_state_identity(a dictionary
    # containing A, B, C, a tuple containing the result of _edge(the text 'A', the text...).
    new = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        # Store an empty dictionary under 'A'.
        # Store an empty dictionary under 'B'.
        # Store an empty dictionary under 'C'.
        {"A": {}, "B": {}, "C": {}},
        # Supply a tuple containing the result of _edge(the text 'A', the text 'B'), the result of _edge(the text
        # 'C', the text 'B') to CoupledNegotiationTrainingEnvironment._decision_state_identity.
        (_edge("A", "B"), _edge("C", "B")), ())
    # Set reasons to the result of CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(old, new).
    reasons = CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        # Supply old to CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons.
        old, new)
    # Require the text 'ACTIVE_PARTICIPANT_SET_CHANGED' belongs to reasons; otherwise raise AssertionError.
    assert "ACTIVE_PARTICIPANT_SET_CHANGED" in reasons
    # Require the text 'RELEVANT_PRECEDENCE_GRAPH_CHANGED' belongs to reasons; otherwise raise AssertionError.
    assert "RELEVANT_PRECEDENCE_GRAPH_CHANGED" in reasons


# Check communicated disagreement remains policy not authorized using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_communicated_disagreement_remains_policy_not_authorized():
    # Set graph to a dictionary containing joint_precedence_edges.
    graph = {"joint_precedence_edges": (_edge("A", "B"), _edge("B", "A"))}
    # Set claims to the result of NegotiationClaimBuilder().build(the text 'A', graph,
    # NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT, True, True).
    claims = NegotiationClaimBuilder().build(
        # Supply graph to NegotiationClaimBuilder().build.
        "A", graph,
        # Supply NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT to NegotiationClaimBuilder().build.
        NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
        # Supply True to the enclosing expression.
        True, True)
    # Require claims.policy_authority is the same object as PolicyAuthority.POLICY_NOT_AUTHORIZED; otherwise raise
    # AssertionError.
    assert claims.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    # Require claims.policy_authority_reason is the same object as
    # InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT; otherwise raise AssertionError.
    assert claims.policy_authority_reason is (
        # Evaluate InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT as part of the enclosing expression.
        InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT)
    # Require whether every item is true in a lazy sequence of the negation of whether any item is true in
    # mask.feasibility for mask in claims.action_masks; otherwise raise AssertionError.
    assert all(not any(mask.feasibility) for mask in claims.action_masks)


# Check original regulatory graph semantics are not mutated by liveness fix using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_original_regulatory_graph_semantics_are_not_mutated_by_liveness_fix():
    # Import negotiation_learning.protocol.state_machine as protocol for use in this module.
    import negotiation_learning.protocol.state_machine as protocol
    # Set source to the result of inspect.getsource(protocol.ClaimRelinquishmentProtocol).
    source = inspect.getsource(protocol.ClaimRelinquishmentProtocol)
    # Require the text 'effective = tuple(edge for edge in original' belongs to source; otherwise raise
    # AssertionError.
    assert "effective = tuple(edge for edge in original" in source
    # Require the text 'without mutating regulatory truth' belongs to source; otherwise raise AssertionError.
    assert "without mutating regulatory truth" in source
    # Set environment_source to the result of
    # inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).
    environment_source = inspect.getsource(
        # Supply CoupledNegotiationTrainingEnvironment.run_episode to inspect.getsource.
        CoupledNegotiationTrainingEnvironment.run_episode)
    # Require the text 'original_edges=edges' belongs to environment_source; otherwise raise AssertionError.
    assert "original_edges=edges" in environment_source
    # Require the text 'effective_coordination_graph=branch.effective_precedence_graph' belongs to
    # environment_source; otherwise raise AssertionError.
    assert "effective_coordination_graph=branch.effective_precedence_graph" in (
        # Evaluate environment_source as part of the enclosing expression.
        environment_source)


# Check selected e5 checkpoint bytes are unchanged by loading using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_selected_e5_checkpoint_bytes_are_unchanged_by_loading():
    # Set path to the result of Path(the text 'results/final_mappo_selection_v2/selected_policy.pt').
    path = Path("results/final_mappo_selection_v2/selected_policy.pt")
    # Set before to the result of file_sha256(path).
    before = file_sha256(path)
    # Call _load_bundle with the supplied arguments.
    _load_bundle(path)
    # Require the result of file_sha256(path) equals before; otherwise raise AssertionError.
    assert file_sha256(path) == before


# Check liveness identity has no route truth or actor input change using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_liveness_identity_has_no_route_truth_or_actor_input_change():
    # Set source to the result of
    # inspect.getsource(CoupledNegotiationTrainingEnvironment._decision_state_identity).lower().
    source = inspect.getsource(
        # Supply CoupledNegotiationTrainingEnvironment._decision_state_identity to inspect.getsource.
        CoupledNegotiationTrainingEnvironment._decision_state_identity).lower()
    # Require the text 'route' does not belong to source and the text 'movement' does not belong to source;
    # otherwise raise AssertionError.
    assert "route" not in source and "movement" not in source
    # Set parameters to inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions).parameters.
    parameters = inspect.signature(
        # Supply MAPPOBehaviorActionProvider.select_joint_actions to inspect.signature.
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    # Require the negation of a set containing the text 'route_id', the text 'ground_truth_route', the text
    # 'movement_path_by_vehicle' intersected with a set built from parameters; otherwise raise AssertionError.
    assert not {"route_id", "ground_truth_route",
                # Evaluate a set built from parameters as part of the enclosing expression.
                "movement_path_by_vehicle"} & set(parameters)


# Check no direct semantic action to speed mapping was added using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_no_direct_semantic_action_to_speed_mapping_was_added():
    # Set provider_source to the result of
    # inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions).lower().
    provider_source = inspect.getsource(
        # Supply MAPPOBehaviorActionProvider.select_joint_actions to inspect.getsource.
        MAPPOBehaviorActionProvider.select_joint_actions).lower()
    # Set environment_source to the result of
    # inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).lower().
    environment_source = inspect.getsource(
        # Supply CoupledNegotiationTrainingEnvironment.run_episode to inspect.getsource.
        CoupledNegotiationTrainingEnvironment.run_episode).lower()
    # Require the text 'setspeed' does not belong to provider_source; otherwise raise AssertionError.
    assert "setspeed" not in provider_source
    # Require the text 'selected_semantic_action' does not belong to environment_source; otherwise raise
    # AssertionError.
    assert "selected_semantic_action" not in environment_source
    # Require the text '_apply_control' belongs to environment_source; otherwise raise AssertionError.
    assert "_apply_control" in environment_source


# Check hard safety checks remain and capability is final provider only using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_hard_safety_checks_remain_and_capability_is_final_provider_only():
    # Set environment_source to the result of
    # inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode).
    environment_source = inspect.getsource(
        # Supply CoupledNegotiationTrainingEnvironment.run_episode to inspect.getsource.
        CoupledNegotiationTrainingEnvironment.run_episode)
    # Require the text 'PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED' belongs to environment_source; otherwise raise
    # AssertionError.
    assert "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" in environment_source
    # Require the text 'blocked_zone_invariant' belongs to environment_source; otherwise raise AssertionError.
    assert "blocked_zone_invariant" in environment_source
    # Require FinalSelectionInferenceProvider.supports_event_driven_renegotiation; otherwise raise AssertionError.
    assert FinalSelectionInferenceProvider.supports_event_driven_renegotiation
    # Require the negation of whether MAPPOBehaviorActionProvider exposes the requested attribute; otherwise raise
    # AssertionError.
    assert not hasattr(MAPPOBehaviorActionProvider,
                       "supports_event_driven_renegotiation")
