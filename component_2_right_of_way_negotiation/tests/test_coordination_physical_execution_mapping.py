"""Step 5J.3B.3A physical-projection semantic tests."""

import inspect
from types import SimpleNamespace

import pytest

from conflict import ConflictZoneManager, MapPathManager
from negotiation_execution import (
    ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper,
    NONCONFLICTING, PHYSICAL_RELEVANT)
from negotiation_training import MAPPOBehaviorActionProvider


@pytest.fixture
def mapping():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    return zones, CoordinationToPhysicalExecutionMapper(zones), paths


def test_authoritative_nonconflicting_blocker_edge_is_retained_without_constraint(mapping):
    zones, mapper, _ = mapping
    relationship = zones.relationship('S_IN_0_RIGHT', 'E_IN_0_LEFT')
    assert not relationship.coordinated_conflict
    assert not relationship.physical_overlap
    assert relationship.conflict_zone_id is None
    result = mapper.map((('C', 'A'),), ('A', 'C'), {
        'C': 'S_IN_0_RIGHT', 'A': 'E_IN_0_LEFT'})
    assert result.source_effective_coordination_graph == (('C', 'A'),)
    assert result.nonphysical_coordination_edges == (('C', 'A'),)
    assert result.physical_execution_graph == ()
    assert result.execution_constraints == ()
    interpretation = result.edge_interpretations[0]
    assert interpretation.execution_relevance == NONCONFLICTING
    assert interpretation.execution_constraint_count == 0
    assert interpretation.conflict_zone_ids == ()


def test_real_conflicting_edge_maps_to_authoritative_zone(mapping):
    zones, mapper, _ = mapping
    relationship = zones.relationship('E_IN_0_LEFT', 'N_IN_0_LEFT')
    result = mapper.map((('A', 'B'),), ('A', 'B'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT'})
    interpretation = result.edge_interpretations[0]
    assert interpretation.execution_relevance == PHYSICAL_RELEVANT
    assert interpretation.conflict_zone_ids == (relationship.conflict_zone_id,)
    assert result.physical_execution_graph == (('A', 'B'),)
    assert len(result.execution_constraints) == 1


def test_mapper_represents_multiple_authoritative_zones_without_new_thresholds():
    relation = SimpleNamespace(
        coordinated_conflict=True, physical_overlap=True,
        conflict_zone_id='CZ_A', conflict_zone_ids=('CZ_A', 'CZ_B'),
        conflict_type='CROSSING')
    mapper = CoordinationToPhysicalExecutionMapper(SimpleNamespace(
        relationship=lambda first, second: relation))
    result = mapper.map((('A', 'B'),), ('A', 'B'), {'A': 'P1', 'B': 'P2'})
    assert result.edge_interpretations[0].conflict_zone_ids == ('CZ_A', 'CZ_B')
    assert result.edge_interpretations[0].execution_constraint_count == 2
    assert len(result.execution_constraints) == 2


def test_missing_or_unresolved_mapping_is_hard_failure(mapping):
    _, mapper, _ = mapping
    with pytest.raises(RuntimeError, match=
                       'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED'):
        mapper.map((('A', 'B'),), ('A', 'B'), {'A': 'E_IN_0_LEFT'})
    unresolved = CoordinationToPhysicalExecutionMapper(SimpleNamespace(
        relationship=lambda a, b: SimpleNamespace(
            coordinated_conflict=False, physical_overlap=True,
            conflict_zone_id=None, conflict_type='UNKNOWN')))
    with pytest.raises(RuntimeError, match=
                       'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED'):
        unresolved.map((('A', 'B'),), ('A', 'B'), {'A': 'P1', 'B': 'P2'})


def test_coordination_cycle_and_physical_cycle_are_separate(mapping):
    _, mapper, _ = mapping
    edges = (('A', 'B'), ('B', 'C'), ('C', 'A'))
    mixed = mapper.map(edges, ('A', 'B', 'C'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'})
    assert mixed.source_effective_coordination_graph == edges
    assert mixed.coordination_cycle_detected
    assert not mixed.physical_execution_cycle_detected
    assert mixed.physical_execution_graph == (('A', 'B'), ('B', 'C'))
    genuine = mapper.map(edges, ('A', 'B', 'C'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_LEFT'})
    assert genuine.coordination_cycle_detected
    assert genuine.physical_execution_cycle_detected


def test_ready_set_is_derived_only_from_physical_obligations(mapping):
    zones, mapper, paths = mapping
    movements = {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT',
                 'C': 'S_IN_0_RIGHT'}
    coordination = (('A', 'B'), ('B', 'C'), ('C', 'A'))
    obligations = mapper.map(coordination, tuple(movements), movements)
    plan = ConflictZoneExecutionPlanner(paths, zones).plan(
        source_snapshot_id=('TEST',),
        effective_coordination_graph=coordination,
        active_vehicle_ids=tuple(movements),
        movement_path_by_vehicle=movements, timestamp=0,
        source_protocol_state='TEST',
        physical_obligation_set=obligations)
    assert plan.effective_coordination_graph == coordination
    assert plan.graph_status == 'EXECUTABLE'
    assert plan.ready_vehicle_ids == ('C',)
    assert ('C', 'A') not in tuple(item.source_precedence_edge
                                   for item in plan.constraints)


def test_policy_provider_interface_contains_no_environment_truth_or_planner():
    parameters = inspect.signature(
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    forbidden = {'movement_path_by_vehicle', 'planner', 'route_id',
                 'ground_truth_route', 'actual_movement_path'}
    assert forbidden.isdisjoint(parameters)
    source = inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions)
    assert 'ConflictZone' not in source
    assert 'graph_executable' not in source
