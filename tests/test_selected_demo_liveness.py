"""Focused contracts for event-driven selected-policy re-negotiation."""

import inspect
from pathlib import Path

from conflict import ConflictZoneManager, MapPathManager
from negotiation_execution import ConflictZoneExecutionPlanner
from negotiation_learning.claim_semantics import (
    InfeasibilityReason, NegotiationClaimBuilder, PolicyAuthority)
from negotiation_learning.models import NegotiationStatus
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle, file_sha256)
from negotiation_training.mappo_provider import MAPPOBehaviorActionProvider


def _edge(yielding, priority):
    return {"yielding_vehicle_id": yielding,
            "priority_vehicle_id": priority}


def _planner():
    paths = MapPathManager()
    return ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))


def test_executable_acyclic_plan_has_ready_vehicle_without_state_invalidation():
    plan = _planner().plan(
        source_snapshot_id=("s",),
        effective_coordination_graph=(("A", "B"),),
        active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT",
                                  "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="TEST")
    identity = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    assert plan.graph_status == "EXECUTABLE"
    assert plan.ready_vehicle_ids == ("B",)
    assert CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        identity, identity) == ()


def test_non_executable_cycle_releases_nobody_and_can_be_invalidated_by_change():
    plan = _planner().plan(
        source_snapshot_id=("s",),
        effective_coordination_graph=(("A", "B"), ("B", "A")),
        active_vehicle_ids=("A", "B"),
        movement_path_by_vehicle={"A": "E_IN_0_LEFT",
                                  "B": "W_IN_0_LEFT"},
        timestamp=1.0, source_protocol_state="TEST")
    old = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        {"A": {}, "B": {}}, (_edge("A", "B"), _edge("B", "A")), ())
    changed = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    assert plan.graph_status == "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
    assert plan.ready_vehicle_ids == ()
    assert "RELEVANT_PRECEDENCE_GRAPH_CHANGED" in (
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
            old, changed))
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    assert "SAFE_HOLD_ACTIVE" in source
    assert "_apply_control" in source
    assert "material_change and safe_authority_transition" in source
    assert "NEW_BLOCK_NOT_SAFE_TO_ACTIVATE" in source


def test_conflict_zone_clear_invalidates_old_authority_without_timeout():
    old = (("A", "B"), (("A", "B"),), ())
    new = (("A", "B"), (("A", "B"),), (("B", "CZ"),))
    assert CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        old, new) == ("CONFLICT_ZONE_CLEARED",)
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    assert "RETRY_AFTER" not in source


def test_participant_change_rebuilds_decision_identity():
    old = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        {"A": {}, "B": {}}, (_edge("A", "B"),), ())
    new = CoupledNegotiationTrainingEnvironment._decision_state_identity(
        {"A": {}, "B": {}, "C": {}},
        (_edge("A", "B"), _edge("C", "B")), ())
    reasons = CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons(
        old, new)
    assert "ACTIVE_PARTICIPANT_SET_CHANGED" in reasons
    assert "RELEVANT_PRECEDENCE_GRAPH_CHANGED" in reasons


def test_communicated_disagreement_remains_policy_not_authorized():
    graph = {"joint_precedence_edges": (_edge("A", "B"), _edge("B", "A"))}
    claims = NegotiationClaimBuilder().build(
        "A", graph,
        NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
        True, True)
    assert claims.policy_authority is PolicyAuthority.POLICY_NOT_AUTHORIZED
    assert claims.policy_authority_reason is (
        InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT)
    assert all(not any(mask.feasibility) for mask in claims.action_masks)


def test_original_regulatory_graph_semantics_are_not_mutated_by_liveness_fix():
    import negotiation_learning.protocol.state_machine as protocol
    source = inspect.getsource(protocol.ClaimRelinquishmentProtocol)
    assert "effective = tuple(edge for edge in original" in source
    assert "without mutating regulatory truth" in source
    environment_source = inspect.getsource(
        CoupledNegotiationTrainingEnvironment.run_episode)
    assert "original_edges=edges" in environment_source
    assert "effective_coordination_graph=branch.effective_precedence_graph" in (
        environment_source)


def test_selected_e5_checkpoint_bytes_are_unchanged_by_loading():
    path = Path("results/final_mappo_selection_v2/selected_policy.pt")
    before = file_sha256(path)
    _load_bundle(path)
    assert file_sha256(path) == before


def test_liveness_identity_has_no_route_truth_or_actor_input_change():
    source = inspect.getsource(
        CoupledNegotiationTrainingEnvironment._decision_state_identity).lower()
    assert "route" not in source and "movement" not in source
    parameters = inspect.signature(
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    assert not {"route_id", "ground_truth_route",
                "movement_path_by_vehicle"} & set(parameters)


def test_no_direct_semantic_action_to_speed_mapping_was_added():
    provider_source = inspect.getsource(
        MAPPOBehaviorActionProvider.select_joint_actions).lower()
    environment_source = inspect.getsource(
        CoupledNegotiationTrainingEnvironment.run_episode).lower()
    assert "setspeed" not in provider_source
    assert "selected_semantic_action" not in environment_source
    assert "_apply_control" in environment_source


def test_hard_safety_checks_remain_and_capability_is_final_provider_only():
    environment_source = inspect.getsource(
        CoupledNegotiationTrainingEnvironment.run_episode)
    assert "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" in environment_source
    assert "blocked_zone_invariant" in environment_source
    assert FinalSelectionInferenceProvider.supports_event_driven_renegotiation
    assert not hasattr(MAPPOBehaviorActionProvider,
                       "supports_event_driven_renegotiation")
