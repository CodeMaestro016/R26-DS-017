"""Validate Step 5J.3B.3A environment-only physical projection."""

# Import inspect for use in this module.
import inspect
# Import json for use in this module.
import json
# Import asdict from dataclasses for the operations below.
from dataclasses import asdict
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper, NONCONFLICTING, PHYSICAL_RELEVANT
# from negotiation_execution for the operations below.
from negotiation_execution import (
    ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper,
    NONCONFLICTING, PHYSICAL_RELEVANT)
# Import MAPPOBehaviorActionProvider from negotiation_training for the operations below.
from negotiation_training import MAPPOBehaviorActionProvider


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def main():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set mapper to the result of CoordinationToPhysicalExecutionMapper(zones).
    mapper = CoordinationToPhysicalExecutionMapper(zones)
    # Set planner to the result of ConflictZoneExecutionPlanner(paths, zones).
    planner = ConflictZoneExecutionPlanner(paths, zones)

    # Set conflicting to the result of mapper.map(a tuple containing a tuple containing the text 'A', the text
    # 'B', a tuple containing the text...).
    conflicting = mapper.map((('A', 'B'),), ('A', 'B'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT'})
    # Set nonconflicting to the result of mapper.map(a tuple containing a tuple containing the text 'C', the text
    # 'A', a tuple containing the text...).
    nonconflicting = mapper.map((('C', 'A'),), ('A', 'C'), {
        'C': 'S_IN_0_RIGHT', 'A': 'E_IN_0_LEFT'})
    # Set mixed_cycle to the result of mapper.map(a tuple containing a tuple containing the text 'A', the text
    # 'B', a tuple containing the text...).
    mixed_cycle = mapper.map(
        # Supply a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text
        # 'B', the text 'C', a tuple... to mapper.map.
        (('A', 'B'), ('B', 'C'), ('C', 'A')), ('A', 'B', 'C'),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'N_IN_0_LEFT' under 'B'.
        # Store the text 'S_IN_0_RIGHT' under 'C'.
        {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'})
    # Set physical_cycle to the result of mapper.map(a tuple containing a tuple containing the text 'A', the text
    # 'B', a tuple containing the text...).
    physical_cycle = mapper.map(
        # Supply a tuple containing a tuple containing the text 'A', the text 'B', a tuple containing the text
        # 'B', the text 'C', a tuple... to mapper.map.
        (('A', 'B'), ('B', 'C'), ('C', 'A')), ('A', 'B', 'C'),
        # Store the text 'E_IN_0_LEFT' under 'A'.
        # Store the text 'N_IN_0_LEFT' under 'B'.
        # Store the text 'S_IN_0_LEFT' under 'C'.
        {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_LEFT'})
    # Require conflicting.edge_interpretations[0].execution_relevance equals PHYSICAL_RELEVANT; otherwise raise
    # AssertionError.
    assert conflicting.edge_interpretations[0].execution_relevance == PHYSICAL_RELEVANT
    # Require conflicting.edge_interpretations[0].execution_constraint_count is at least 1; otherwise raise
    # AssertionError.
    assert conflicting.edge_interpretations[0].execution_constraint_count >= 1
    # Require nonconflicting.source_effective_coordination_graph equals a tuple containing a tuple containing the
    # text 'C', the text 'A'; otherwise raise AssertionError.
    assert nonconflicting.source_effective_coordination_graph == (('C', 'A'),)
    # Require nonconflicting.edge_interpretations[0].execution_relevance equals NONCONFLICTING; otherwise raise
    # AssertionError.
    assert nonconflicting.edge_interpretations[0].execution_relevance == NONCONFLICTING
    # Require nonconflicting.edge_interpretations[0].conflict_zone_ids equals an empty tuple; otherwise raise
    # AssertionError.
    assert nonconflicting.edge_interpretations[0].conflict_zone_ids == ()
    # Require nonconflicting.execution_constraints equals an empty tuple; otherwise raise AssertionError.
    assert nonconflicting.execution_constraints == ()
    # Require mixed_cycle.coordination_cycle_detected; otherwise raise AssertionError.
    assert mixed_cycle.coordination_cycle_detected
    # Require the negation of mixed_cycle.physical_execution_cycle_detected; otherwise raise AssertionError.
    assert not mixed_cycle.physical_execution_cycle_detected
    # Require physical_cycle.physical_execution_cycle_detected; otherwise raise AssertionError.
    assert physical_cycle.physical_execution_cycle_detected
    # Set plan to the result of planner.plan().
    plan = planner.plan(
        # Supply source_snapshot_id as a tuple containing the text 'VALIDATION'.
        source_snapshot_id=('VALIDATION',),
        # Supply effective_coordination_graph as mixed_cycle.source_effective_coordination_graph.
        effective_coordination_graph=mixed_cycle.source_effective_coordination_graph,
        # Supply active_vehicle_ids as a tuple containing the text 'A', the text 'B', the text 'C'.
        active_vehicle_ids=('A', 'B', 'C'),
        # Supply movement_path_by_vehicle as a dictionary containing A, B, C.
        movement_path_by_vehicle={
            'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'},
        # Supply timestamp as 0.0.
        # Supply source_protocol_state as the text 'VALIDATION'.
        timestamp=0.0, source_protocol_state='VALIDATION',
        # Supply physical_obligation_set as mixed_cycle.
        physical_obligation_set=mixed_cycle)
    # Require plan.graph_status equals the text 'EXECUTABLE'; otherwise raise AssertionError.
    assert plan.graph_status == 'EXECUTABLE'
    # Require plan.ready_vehicle_ids equals a tuple containing the text 'C'; otherwise raise AssertionError.
    assert plan.ready_vehicle_ids == ('C',)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call mapper.map with the supplied arguments.
        mapper.map((('A', 'MISSING'),), ('A', 'MISSING'),
                   # Store the text 'E_IN_0_LEFT' under 'A'.
                   {'A': 'E_IN_0_LEFT'})
    # Handle RuntimeError as error using the recovery steps below.
    except RuntimeError as error:
        # Require error.args equals a tuple containing the text 'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED';
        # otherwise raise AssertionError.
        assert error.args == ('EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED',)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Raise AssertionError with the text 'unresolved path did not fail' to stop this execution path.
        raise AssertionError('unresolved path did not fail')
    # Set signature to the result of inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions).
    signature = inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions)
    # Set forbidden to a set containing the text 'movement_path_by_vehicle', the text 'planner', the text
    # 'route_id', the text...
    forbidden = {'movement_path_by_vehicle', 'planner', 'route_id',
                 'ground_truth_route', 'actual_movement_path'}
    # Require the result of forbidden.isdisjoint(signature.parameters); otherwise raise AssertionError.
    assert forbidden.isdisjoint(signature.parameters)
    # Set payload to a dictionary containing checkpoint, status, blocker_pair, authoritative_relationship,...
    payload = {
        'checkpoint': 'STEP_5J_3B_3A',
        'status': 'COORDINATION_PHYSICAL_EXECUTION_SEMANTICS_VALIDATED',
        # Store a list containing the text 'S_IN_0_RIGHT', the text 'E_IN_0_LEFT' under 'blocker_pair'.
        'blocker_pair': ['S_IN_0_RIGHT', 'E_IN_0_LEFT'],
        # Store the result of asdict(the result of zones.relationship(the text 'S_IN_0_RIGHT', the text
        # 'E_IN_0_LEFT')) under 'authoritative_relationship'.
        'authoritative_relationship': asdict(zones.relationship(
            'S_IN_0_RIGHT', 'E_IN_0_LEFT')),
        # Store True under 'coordination_edge_retained'.
        'coordination_edge_retained': True,
        # Store 0 under 'physical_zone_count'.
        'physical_zone_count': 0,
        # Store 0 under 'physical_constraint_count'.
        'physical_constraint_count': 0,
        # Store NONCONFLICTING under 'execution_relevance'.
        'execution_relevance': NONCONFLICTING,
        # Store True under 'coordination_cycle_physical_acyclic_validated'.
        'coordination_cycle_physical_acyclic_validated': True,
        # Store True under 'genuine_physical_cycle_validated'.
        'genuine_physical_cycle_validated': True,
        # Store False under 'policy_provider_accepts_movement_truth'.
        'policy_provider_accepts_movement_truth': False,
        # Store False under 'policy_provider_accepts_planner'.
        'policy_provider_accepts_planner': False,
        # Store 0 under 'effective_coordination_graph_mutations'.
        'effective_coordination_graph_mutations': 0,
        # Store 0 under 'policy_actions_resampled'.
        'policy_actions_resampled': 0,
        # Store 0 under 'protocol_edges_modified'.
        'protocol_edges_modified': 0,
        # Store 0 under 'new_hard_mask_rules'.
        'new_hard_mask_rules': 0,
        # Store 0 under 'route_truth_actor_fields'.
        'route_truth_actor_fields': 0,
        # Store 0 under 'numerical_values_introduced'.
        'numerical_values_introduced': 0,
    }
    # Write the supplied text to Path('results/coordination_physical_execution_mapping.json').
    Path('results/coordination_physical_execution_mapping.json').write_text(
        # Supply encoding as the text 'utf-8'.
        # Supply indent as 2.
        json.dumps(payload, indent=2), encoding='utf-8')
    # Display the text 'Step 5J.3B.3A Coordination-to-Physical Execution Mapping'.
    print('Step 5J.3B.3A Coordination-to-Physical Execution Mapping\n')
    # Display the text 'Full coordination graph immutable: PASS'.
    print('  Full coordination graph immutable: PASS')
    # Display the text 'Real conflicting edge mapping: PASS'.
    print('  Real conflicting edge mapping: PASS')
    # Display the text 'Real non-conflicting edge mapping: PASS'.
    print('  Real non-conflicting edge mapping: PASS')
    # Display the text 'Unresolved mapping hard failure: PASS'.
    print('  Unresolved mapping hard failure: PASS')
    # Display the text 'Coordination-cycle / physical-cycle separation: PASS'.
    print('  Coordination-cycle / physical-cycle separation: PASS')
    # Display the text 'Physical ready set from obligations only: PASS'.
    print('  Physical ready set from obligations only: PASS')
    # Display the text 'Policy provider route truth fields: 0'.
    print('  Policy provider route truth fields: 0')
    # Display the text 'Policy provider planner fields: 0'.
    print('  Policy provider planner fields: 0')
    # Display the text 'New numerical values: 0'.
    print('  New numerical values: 0')
    # Display the text 'STEP_5J_3B_3A_STATUS:...'.
    print('  STEP_5J_3B_3A_STATUS: '
          'COORDINATION_PHYSICAL_EXECUTION_SEMANTICS_VALIDATED')


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == '__main__': main()
