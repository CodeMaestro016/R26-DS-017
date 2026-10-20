"""Step 5J.3B.3A physical-projection semantic tests."""

# Import inspect for use in this module.
import inspect
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper, NONCONFLICTING, PHYSICAL_RELEVANT
# from negotiation_execution for the operations below.
from negotiation_execution import (
    ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper,
    NONCONFLICTING, PHYSICAL_RELEVANT)
# Import MAPPOBehaviorActionProvider from negotiation_training for the operations below.
from negotiation_training import MAPPOBehaviorActionProvider


# Apply pytest.fixture as a decorator to configure the following definition.
@pytest.fixture
# Mapping using the inputs and processing steps below.
# Output: a tuple containing zones, the result of CoordinationToPhysicalExecutionMapper(zones), paths.
def mapping():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Return a tuple containing zones, the result of CoordinationToPhysicalExecutionMapper(zones), paths to the
    # caller.
    return zones, CoordinationToPhysicalExecutionMapper(zones), paths


# Check authoritative nonconflicting blocker edge is retained without constraint using the setup, calls, and
# assertions below.
# Input mapping: the supplied mapping.
# Output: no explicit value; normal completion returns None.
def test_authoritative_nonconflicting_blocker_edge_is_retained_without_constraint(mapping):
    # Set (zones, mapper, _) to mapping.
    zones, mapper, _ = mapping
    # Set relationship to the result of zones.relationship(the text 'S_IN_0_RIGHT', the text 'E_IN_0_LEFT').
    relationship = zones.relationship('S_IN_0_RIGHT', 'E_IN_0_LEFT')
    # Require the negation of relationship.coordinated_conflict; otherwise raise AssertionError.
    assert not relationship.coordinated_conflict
    # Require the negation of relationship.physical_overlap; otherwise raise AssertionError.
    assert not relationship.physical_overlap
    # Require relationship.conflict_zone_id is the same object as None; otherwise raise AssertionError.
    assert relationship.conflict_zone_id is None
    # Set result to the result of mapper.map(a tuple containing a tuple containing the text 'C', the text 'A', a
    # tuple containing the text...).
    result = mapper.map((('C', 'A'),), ('A', 'C'), {
        'C': 'S_IN_0_RIGHT', 'A': 'E_IN_0_LEFT'})
    # Require result.source_effective_coordination_graph equals a tuple containing a tuple containing the text
    # 'C', the text 'A'; otherwise raise AssertionError.
    assert result.source_effective_coordination_graph == (('C', 'A'),)
    # Require result.nonphysical_coordination_edges equals a tuple containing a tuple containing the text 'C', the
    # text 'A'; otherwise raise AssertionError.
    assert result.nonphysical_coordination_edges == (('C', 'A'),)
    # Require result.physical_execution_graph equals an empty tuple; otherwise raise AssertionError.
    assert result.physical_execution_graph == ()
    # Require result.execution_constraints equals an empty tuple; otherwise raise AssertionError.
    assert result.execution_constraints == ()
    # Set interpretation to result.edge_interpretations at 0.
    interpretation = result.edge_interpretations[0]
    # Require interpretation.execution_relevance equals NONCONFLICTING; otherwise raise AssertionError.
    assert interpretation.execution_relevance == NONCONFLICTING
    # Require interpretation.execution_constraint_count equals 0; otherwise raise AssertionError.
    assert interpretation.execution_constraint_count == 0
    # Require interpretation.conflict_zone_ids equals an empty tuple; otherwise raise AssertionError.
    assert interpretation.conflict_zone_ids == ()


# Check real conflicting edge maps to authoritative zone using the setup, calls, and assertions below.
# Input mapping: the supplied mapping.
# Output: no explicit value; normal completion returns None.
def test_real_conflicting_edge_maps_to_authoritative_zone(mapping):
    # Set (zones, mapper, _) to mapping.
    zones, mapper, _ = mapping
    # Set relationship to the result of zones.relationship(the text 'E_IN_0_LEFT', the text 'N_IN_0_LEFT').
    relationship = zones.relationship('E_IN_0_LEFT', 'N_IN_0_LEFT')
    # Set result to the result of mapper.map(a tuple containing a tuple containing the text 'A', the text 'B', a
    # tuple containing the text...).
    result = mapper.map((('A', 'B'),), ('A', 'B'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT'})
    # Set interpretation to result.edge_interpretations at 0.
    interpretation = result.edge_interpretations[0]
    # Require interpretation.execution_relevance equals PHYSICAL_RELEVANT; otherwise raise AssertionError.
    assert interpretation.execution_relevance == PHYSICAL_RELEVANT
    # Require interpretation.conflict_zone_ids equals a tuple containing relationship.conflict_zone_id; otherwise
    # raise AssertionError.
    assert interpretation.conflict_zone_ids == (relationship.conflict_zone_id,)
    # Require result.physical_execution_graph equals a tuple containing a tuple containing the text 'A', the text
    # 'B'; otherwise raise AssertionError.
    assert result.physical_execution_graph == (('A', 'B'),)
    # Require the number of entries in result.execution_constraints equals 1; otherwise raise AssertionError.
    assert len(result.execution_constraints) == 1


# Check mapper represents multiple authoritative zones without new thresholds using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_mapper_represents_multiple_authoritative_zones_without_new_thresholds():
    # Set relation to the result of SimpleNamespace().
    relation = SimpleNamespace(
        # Supply coordinated_conflict as True.
        # Supply physical_overlap as True.
        coordinated_conflict=True, physical_overlap=True,
        # Supply conflict_zone_id as the text 'CZ_A'.
        # Supply conflict_zone_ids as a tuple containing the text 'CZ_A', the text 'CZ_B'.
        conflict_zone_id='CZ_A', conflict_zone_ids=('CZ_A', 'CZ_B'),
        # Supply conflict_type as the text 'CROSSING'.
        conflict_type='CROSSING')
    # Set mapper to the result of CoordinationToPhysicalExecutionMapper(the result of SimpleNamespace()).
    mapper = CoordinationToPhysicalExecutionMapper(SimpleNamespace(
        # Declare first, second as input parameters.
        relationship=lambda first, second: relation))
    # Set result to the result of mapper.map(a tuple containing a tuple containing the text 'A', the text 'B', a
    # tuple containing the text...).
    result = mapper.map((('A', 'B'),), ('A', 'B'), {'A': 'P1', 'B': 'P2'})
    # Require result.edge_interpretations[0].conflict_zone_ids equals a tuple containing the text 'CZ_A', the text
    # 'CZ_B'; otherwise raise AssertionError.
    assert result.edge_interpretations[0].conflict_zone_ids == ('CZ_A', 'CZ_B')
    # Require result.edge_interpretations[0].execution_constraint_count equals 2; otherwise raise AssertionError.
    assert result.edge_interpretations[0].execution_constraint_count == 2
    # Require the number of entries in result.execution_constraints equals 2; otherwise raise AssertionError.
    assert len(result.execution_constraints) == 2


# Check missing or unresolved mapping is hard failure using the setup, calls, and assertions below.
# Input mapping: the supplied mapping.
# Output: no explicit value; normal completion returns None.
def test_missing_or_unresolved_mapping_is_hard_failure(mapping):
    # Set (_, mapper, _) to mapping.
    _, mapper, _ = mapping
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match=
                       'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED'):
        # Call mapper.map with the supplied arguments.
        mapper.map((('A', 'B'),), ('A', 'B'), {'A': 'E_IN_0_LEFT'})
    # Set unresolved to the result of CoordinationToPhysicalExecutionMapper(the result of SimpleNamespace()).
    unresolved = CoordinationToPhysicalExecutionMapper(SimpleNamespace(
        # Declare a, b as input parameters.
        relationship=lambda a, b: SimpleNamespace(
            # Supply coordinated_conflict as False.
            # Supply physical_overlap as True.
            coordinated_conflict=False, physical_overlap=True,
            # Supply conflict_zone_id as None.
            # Supply conflict_type as the text 'UNKNOWN'.
            conflict_zone_id=None, conflict_type='UNKNOWN')))
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError, match=
                       'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED'):
        # Call unresolved.map with the supplied arguments.
        unresolved.map((('A', 'B'),), ('A', 'B'), {'A': 'P1', 'B': 'P2'})


# Check coordination cycle and physical cycle are separate using the setup, calls, and assertions below.
# Input mapping: the supplied mapping.
# Output: no explicit value; normal completion returns None.
def test_coordination_cycle_and_physical_cycle_are_separate(mapping):
    # Set (_, mapper, _) to mapping.
    _, mapper, _ = mapping
    # Set edges to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text
    # 'B', the text 'C', a tuple...
    edges = (('A', 'B'), ('B', 'C'), ('C', 'A'))
    # Set mixed to the result of mapper.map(edges, a tuple containing the text 'A', the text 'B', the text 'C', a
    # dictionary containing A, B, C).
    mixed = mapper.map(edges, ('A', 'B', 'C'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'})
    # Require mixed.source_effective_coordination_graph equals edges; otherwise raise AssertionError.
    assert mixed.source_effective_coordination_graph == edges
    # Require mixed.coordination_cycle_detected; otherwise raise AssertionError.
    assert mixed.coordination_cycle_detected
    # Require the negation of mixed.physical_execution_cycle_detected; otherwise raise AssertionError.
    assert not mixed.physical_execution_cycle_detected
    # Require mixed.physical_execution_graph equals a tuple containing a tuple containing the text 'A', the text
    # 'B', a tuple containing the text 'B', the text 'C'; otherwise raise AssertionError.
    assert mixed.physical_execution_graph == (('A', 'B'), ('B', 'C'))
    # Set genuine to the result of mapper.map(edges, a tuple containing the text 'A', the text 'B', the text 'C',
    # a dictionary containing A, B, C).
    genuine = mapper.map(edges, ('A', 'B', 'C'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_LEFT'})
    # Require genuine.coordination_cycle_detected; otherwise raise AssertionError.
    assert genuine.coordination_cycle_detected
    # Require genuine.physical_execution_cycle_detected; otherwise raise AssertionError.
    assert genuine.physical_execution_cycle_detected


# Check ready set is derived only from physical obligations using the setup, calls, and assertions below.
# Input mapping: the supplied mapping.
# Output: no explicit value; normal completion returns None.
def test_ready_set_is_derived_only_from_physical_obligations(mapping):
    # Set (zones, mapper, paths) to mapping.
    zones, mapper, paths = mapping
    # Set movements to a dictionary containing A, B, C.
    movements = {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT',
                 'C': 'S_IN_0_RIGHT'}
    # Set coordination to a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the
    # text 'B', the text 'C', a tuple...
    coordination = (('A', 'B'), ('B', 'C'), ('C', 'A'))
    # Set obligations to the result of mapper.map(coordination, a tuple built from movements, movements).
    obligations = mapper.map(coordination, tuple(movements), movements)
    # Set plan to the result of ConflictZoneExecutionPlanner(paths, zones).plan().
    plan = ConflictZoneExecutionPlanner(paths, zones).plan(
        # Supply source_snapshot_id as a tuple containing the text 'TEST'.
        source_snapshot_id=('TEST',),
        # Supply effective_coordination_graph as coordination.
        effective_coordination_graph=coordination,
        # Supply active_vehicle_ids as a tuple built from movements.
        active_vehicle_ids=tuple(movements),
        # Supply movement_path_by_vehicle as movements.
        # Supply timestamp as 0.
        movement_path_by_vehicle=movements, timestamp=0,
        # Supply source_protocol_state as the text 'TEST'.
        source_protocol_state='TEST',
        # Supply physical_obligation_set as obligations.
        physical_obligation_set=obligations)
    # Require plan.effective_coordination_graph equals coordination; otherwise raise AssertionError.
    assert plan.effective_coordination_graph == coordination
    # Require plan.graph_status equals the text 'EXECUTABLE'; otherwise raise AssertionError.
    assert plan.graph_status == 'EXECUTABLE'
    # Require plan.ready_vehicle_ids equals a tuple containing the text 'C'; otherwise raise AssertionError.
    assert plan.ready_vehicle_ids == ('C',)
    # Require a tuple containing the text 'C', the text 'A' does not belong to a tuple built from a lazy sequence
    # of item.source_precedence_edge for item in plan.constraints; otherwise raise AssertionError.
    assert ('C', 'A') not in tuple(item.source_precedence_edge
                                   # Evaluate plan.constraints as part of the enclosing expression.
                                   for item in plan.constraints)


# Check policy provider interface contains no environment truth or planner using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_policy_provider_interface_contains_no_environment_truth_or_planner():
    # Set parameters to inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions).parameters.
    parameters = inspect.signature(
        # Supply MAPPOBehaviorActionProvider.select_joint_actions to inspect.signature.
        MAPPOBehaviorActionProvider.select_joint_actions).parameters
    # Set forbidden to a set containing the text 'movement_path_by_vehicle', the text 'planner', the text
    # 'route_id', the text...
    forbidden = {'movement_path_by_vehicle', 'planner', 'route_id',
                 'ground_truth_route', 'actual_movement_path'}
    # Require the result of forbidden.isdisjoint(parameters); otherwise raise AssertionError.
    assert forbidden.isdisjoint(parameters)
    # Set source to the result of inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions).
    source = inspect.getsource(MAPPOBehaviorActionProvider.select_joint_actions)
    # Require the text 'ConflictZone' does not belong to source; otherwise raise AssertionError.
    assert 'ConflictZone' not in source
    # Require the text 'graph_executable' does not belong to source; otherwise raise AssertionError.
    assert 'graph_executable' not in source
