"""Environment-only coordination-to-physical execution projection."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder


PHYSICAL_RELEVANT = "PHYSICAL_CONFLICT_EXECUTION_RELEVANT"
NONCONFLICTING = "PHYSICALLY_NONCONFLICTING_NO_EXECUTION_CONSTRAINT"
UNRESOLVED = "PHYSICAL_RELATIONSHIP_UNRESOLVED"


@dataclass(frozen=True)
class CoordinationEdgePhysicalInterpretation:
    yielding_vehicle_id: str
    priority_vehicle_id: str
    yielding_movement_path_id: str
    priority_movement_path_id: str
    coordination_edge_present: bool
    physical_relationship_status: str
    conflict_zone_ids: Tuple[str, ...]
    execution_constraint_count: int
    execution_relevance: str
    mapping_source: str
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class PhysicalExecutionObligation:
    yielding_vehicle_id: str
    priority_vehicle_id: str
    conflict_zone_id: str
    source_coordination_edge: tuple


@dataclass(frozen=True)
class PhysicalExecutionObligationSet:
    source_effective_coordination_graph: Tuple[tuple, ...]
    edge_interpretations: Tuple[CoordinationEdgePhysicalInterpretation, ...]
    active_execution_edges: Tuple[tuple, ...]
    nonphysical_coordination_edges: Tuple[tuple, ...]
    execution_constraints: Tuple[PhysicalExecutionObligation, ...]
    physical_execution_graph: Tuple[tuple, ...]
    coordination_cycle_detected: bool
    physical_execution_cycle_detected: bool
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


class CoordinationToPhysicalExecutionMapper:
    """Project hidden simulator movement realization after policy sampling."""

    def __init__(self, conflict_zone_manager):
        self.zones = conflict_zone_manager

    def map(self, effective_coordination_graph, active_vehicle_ids,
            movement_path_by_vehicle):
        coordination = tuple(sorted(tuple(edge)
                                    for edge in effective_coordination_graph))
        interpretations, obligations = [], []
        for yielding, priority in coordination:
            if (yielding not in movement_path_by_vehicle or
                    priority not in movement_path_by_vehicle):
                raise RuntimeError("EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            first = movement_path_by_vehicle[yielding]
            second = movement_path_by_vehicle[priority]
            try:
                relationship = self.zones.relationship(first, second)
            except (KeyError, TypeError, ValueError):
                raise RuntimeError(
                    "EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            if (relationship.coordinated_conflict and
                    relationship.conflict_zone_id):
                zone_ids = tuple(getattr(
                    relationship, "conflict_zone_ids", ()) or
                    (relationship.conflict_zone_id,))
                relevance = PHYSICAL_RELEVANT
                status = relationship.conflict_type
            elif (not relationship.coordinated_conflict and
                  not relationship.physical_overlap and
                  relationship.conflict_zone_id is None and
                  relationship.conflict_type == "NO_CONFLICT"):
                zone_ids = ()
                relevance = NONCONFLICTING
                status = "AUTHORITATIVE_MAP_NO_CONFLICT"
            else:
                raise RuntimeError(
                    "EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            for zone_id in zone_ids:
                obligations.append(PhysicalExecutionObligation(
                    yielding, priority, zone_id, (yielding, priority)))
            interpretations.append(CoordinationEdgePhysicalInterpretation(
                yielding, priority, first, second, True, status, zone_ids,
                len(zone_ids), relevance,
                "CONFLICT_ZONE_MANAGER_AUTHORITATIVE_MAP_RELATIONSHIP",
                {"environment_transition_only": True,
                 "actor_information": False, "numerical_thresholds": 0}))
        physical = tuple(sorted({item.source_coordination_edge
                                 for item in obligations}))
        coordination_analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            tuple(sorted(active_vehicle_ids)), tuple(
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                for a, b in coordination))
        physical_analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            tuple(sorted(active_vehicle_ids)), tuple(
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                for a, b in physical))
        nonphysical = tuple((item.yielding_vehicle_id, item.priority_vehicle_id)
                            for item in interpretations
                            if item.execution_relevance == NONCONFLICTING)
        return PhysicalExecutionObligationSet(
            coordination, tuple(interpretations), physical, nonphysical,
            tuple(obligations), physical,
            bool(coordination_analysis["cycle_detected"]),
            bool(physical_analysis["cycle_detected"]),
            {"policy_edges_removed": 0, "protocol_edges_modified": 0,
             "policy_actions_resampled": 0,
             "simulation_execution_mapping":
                 "AUTHORITATIVE_ENVIRONMENT_TRAJECTORY",
             "actor_information": "EGO_LOCAL_PARTIAL_OBSERVATION",
             "future_deployment_mapping":
                 "CONSERVATIVE_FEASIBLE_PATH_CONFLICT_SET"})
