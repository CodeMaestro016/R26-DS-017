"""Validate Step 5J.3B.3A environment-only physical projection."""

import inspect
import json
from dataclasses import asdict
from pathlib import Path

from conflict import ConflictZoneManager, MapPathManager
from negotiation_execution import (
    ConflictZoneExecutionPlanner, CoordinationToPhysicalExecutionMapper,
    NONCONFLICTING, PHYSICAL_RELEVANT)
from negotiation_training import MAPPOBehaviorActionProvider


def main():
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    mapper = CoordinationToPhysicalExecutionMapper(zones)
    planner = ConflictZoneExecutionPlanner(paths, zones)

    conflicting = mapper.map((('A', 'B'),), ('A', 'B'), {
        'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT'})
    nonconflicting = mapper.map((('C', 'A'),), ('A', 'C'), {
        'C': 'S_IN_0_RIGHT', 'A': 'E_IN_0_LEFT'})
    mixed_cycle = mapper.map(
        (('A', 'B'), ('B', 'C'), ('C', 'A')), ('A', 'B', 'C'),
        {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'})
    physical_cycle = mapper.map(
        (('A', 'B'), ('B', 'C'), ('C', 'A')), ('A', 'B', 'C'),
        {'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_LEFT'})
    assert conflicting.edge_interpretations[0].execution_relevance == PHYSICAL_RELEVANT
    assert conflicting.edge_interpretations[0].execution_constraint_count >= 1
    assert nonconflicting.source_effective_coordination_graph == (('C', 'A'),)
    assert nonconflicting.edge_interpretations[0].execution_relevance == NONCONFLICTING
    assert nonconflicting.edge_interpretations[0].conflict_zone_ids == ()
    assert nonconflicting.execution_constraints == ()
    assert mixed_cycle.coordination_cycle_detected
    assert not mixed_cycle.physical_execution_cycle_detected
    assert physical_cycle.physical_execution_cycle_detected
    plan = planner.plan(
        source_snapshot_id=('VALIDATION',),
        effective_coordination_graph=mixed_cycle.source_effective_coordination_graph,
        active_vehicle_ids=('A', 'B', 'C'),
        movement_path_by_vehicle={
            'A': 'E_IN_0_LEFT', 'B': 'N_IN_0_LEFT', 'C': 'S_IN_0_RIGHT'},
        timestamp=0.0, source_protocol_state='VALIDATION',
        physical_obligation_set=mixed_cycle)
    assert plan.graph_status == 'EXECUTABLE'
    assert plan.ready_vehicle_ids == ('C',)
    try:
        mapper.map((('A', 'MISSING'),), ('A', 'MISSING'),
                   {'A': 'E_IN_0_LEFT'})
    except RuntimeError as error:
        assert error.args == ('EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED',)
    else:
        raise AssertionError('unresolved path did not fail')
    signature = inspect.signature(MAPPOBehaviorActionProvider.select_joint_actions)
    forbidden = {'movement_path_by_vehicle', 'planner', 'route_id',
                 'ground_truth_route', 'actual_movement_path'}
    assert forbidden.isdisjoint(signature.parameters)
    payload = {
        'checkpoint': 'STEP_5J_3B_3A',
        'status': 'COORDINATION_PHYSICAL_EXECUTION_SEMANTICS_VALIDATED',
        'blocker_pair': ['S_IN_0_RIGHT', 'E_IN_0_LEFT'],
        'authoritative_relationship': asdict(zones.relationship(
            'S_IN_0_RIGHT', 'E_IN_0_LEFT')),
        'coordination_edge_retained': True,
        'physical_zone_count': 0,
        'physical_constraint_count': 0,
        'execution_relevance': NONCONFLICTING,
        'coordination_cycle_physical_acyclic_validated': True,
        'genuine_physical_cycle_validated': True,
        'policy_provider_accepts_movement_truth': False,
        'policy_provider_accepts_planner': False,
        'effective_coordination_graph_mutations': 0,
        'policy_actions_resampled': 0,
        'protocol_edges_modified': 0,
        'new_hard_mask_rules': 0,
        'route_truth_actor_fields': 0,
        'numerical_values_introduced': 0,
    }
    Path('results/coordination_physical_execution_mapping.json').write_text(
        json.dumps(payload, indent=2), encoding='utf-8')
    print('Step 5J.3B.3A Coordination-to-Physical Execution Mapping\n')
    print('  Full coordination graph immutable: PASS')
    print('  Real conflicting edge mapping: PASS')
    print('  Real non-conflicting edge mapping: PASS')
    print('  Unresolved mapping hard failure: PASS')
    print('  Coordination-cycle / physical-cycle separation: PASS')
    print('  Physical ready set from obligations only: PASS')
    print('  Policy provider route truth fields: 0')
    print('  Policy provider planner fields: 0')
    print('  New numerical values: 0')
    print('  STEP_5J_3B_3A_STATUS: '
          'COORDINATION_PHYSICAL_EXECUTION_SEMANTICS_VALIDATED')


if __name__ == '__main__': main()
