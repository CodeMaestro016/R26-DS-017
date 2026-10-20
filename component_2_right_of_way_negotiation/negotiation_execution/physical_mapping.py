"""Environment-only coordination-to-physical execution projection."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple

# Import RegulatoryPrecedenceGraphBuilder from negotiation_learning.precedence_graph for the operations below.
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder


# Set PHYSICAL_RELEVANT to the text 'PHYSICAL_CONFLICT_EXECUTION_RELEVANT'.
PHYSICAL_RELEVANT = "PHYSICAL_CONFLICT_EXECUTION_RELEVANT"
# Set NONCONFLICTING to the text 'PHYSICALLY_NONCONFLICTING_NO_EXECUTION_CONSTRAINT'.
NONCONFLICTING = "PHYSICALLY_NONCONFLICTING_NO_EXECUTION_CONSTRAINT"
# Set UNRESOLVED to the text 'PHYSICAL_RELATIONSHIP_UNRESOLVED'.
UNRESOLVED = "PHYSICAL_RELATIONSHIP_UNRESOLVED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define CoordinationEdgePhysicalInterpretation to group the state and operations declared below.
# Declared fields: yielding_vehicle_id, priority_vehicle_id, yielding_movement_path_id, priority_movement_path_id,
# coordination_edge_present, physical_relationship_status, conflict_zone_ids, execution_constraint_count,....
# Construction and attribute behavior follow the declared decorators and base classes.
class CoordinationEdgePhysicalInterpretation:
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare yielding_movement_path_id as str for this data structure.
    yielding_movement_path_id: str
    # Declare priority_movement_path_id as str for this data structure.
    priority_movement_path_id: str
    # Declare coordination_edge_present as bool for this data structure.
    coordination_edge_present: bool
    # Declare physical_relationship_status as str for this data structure.
    physical_relationship_status: str
    # Declare conflict_zone_ids as Tuple[str, ...] for this data structure.
    conflict_zone_ids: Tuple[str, ...]
    # Declare execution_constraint_count as int for this data structure.
    execution_constraint_count: int
    # Declare execution_relevance as str for this data structure.
    execution_relevance: str
    # Declare mapping_source as str for this data structure.
    mapping_source: str
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PhysicalExecutionObligation to group the state and operations declared below.
# Declared fields: yielding_vehicle_id, priority_vehicle_id, conflict_zone_id, source_coordination_edge.
# Construction and attribute behavior follow the declared decorators and base classes.
class PhysicalExecutionObligation:
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare conflict_zone_id as str for this data structure.
    conflict_zone_id: str
    # Declare source_coordination_edge as tuple for this data structure.
    source_coordination_edge: tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PhysicalExecutionObligationSet to group the state and operations declared below.
# Declared fields: source_effective_coordination_graph, edge_interpretations, active_execution_edges,
# nonphysical_coordination_edges, execution_constraints, physical_execution_graph,
# coordination_cycle_detected,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PhysicalExecutionObligationSet:
    # Declare source_effective_coordination_graph as Tuple[tuple, ...] for this data structure.
    source_effective_coordination_graph: Tuple[tuple, ...]
    # Declare edge_interpretations as Tuple[CoordinationEdgePhysicalInterpretation, ...] for this data structure.
    edge_interpretations: Tuple[CoordinationEdgePhysicalInterpretation, ...]
    # Declare active_execution_edges as Tuple[tuple, ...] for this data structure.
    active_execution_edges: Tuple[tuple, ...]
    # Declare nonphysical_coordination_edges as Tuple[tuple, ...] for this data structure.
    nonphysical_coordination_edges: Tuple[tuple, ...]
    # Declare execution_constraints as Tuple[PhysicalExecutionObligation, ...] for this data structure.
    execution_constraints: Tuple[PhysicalExecutionObligation, ...]
    # Declare physical_execution_graph as Tuple[tuple, ...] for this data structure.
    physical_execution_graph: Tuple[tuple, ...]
    # Declare coordination_cycle_detected as bool for this data structure.
    coordination_cycle_detected: bool
    # Declare physical_execution_cycle_detected as bool for this data structure.
    physical_execution_cycle_detected: bool
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Project hidden simulator movement realization after policy sampling.
# Instances expose the attributes and methods implemented in this class.
class CoordinationToPhysicalExecutionMapper:
    """Project hidden simulator movement realization after policy sampling."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input conflict_zone_manager: the supplied conflict zone manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, conflict_zone_manager):
        # Set self.zones to conflict_zone_manager.
        self.zones = conflict_zone_manager

    # Map using the inputs and processing steps below.
    # Input effective_coordination_graph: the supplied effective coordination graph.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input movement_path_by_vehicle: the supplied movement path by vehicle.
    # Output: the result of PhysicalExecutionObligationSet(coordination, a tuple built from interpretations,
    # physical, nonphysical, a tuple built from...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def map(self, effective_coordination_graph, active_vehicle_ids,
            # Declare movement_path_by_vehicle as input parameter.
            movement_path_by_vehicle):
        # Set coordination to a tuple built from the sorted values from a lazy sequence of a tuple built from edge
        # for edge in effective_coordination_graph.
        coordination = tuple(sorted(tuple(edge)
                                    # Evaluate effective_coordination_graph as part of the enclosing expression.
                                    for edge in effective_coordination_graph))
        # Set (interpretations, obligations) to a tuple containing an empty list, an empty list.
        interpretations, obligations = [], []
        # Iterate over coordination, binding each item to (yielding, priority).
        for yielding, priority in coordination:
            # Run this branch when yielding does not belong to movement_path_by_vehicle or priority does not
            # belong to movement_path_by_vehicle.
            if (yielding not in movement_path_by_vehicle or
                    # Evaluate priority does not belong to movement_path_by_vehicle as part of the enclosing
                    # expression.
                    priority not in movement_path_by_vehicle):
                # Raise RuntimeError with the text 'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED' to stop this
                # execution path.
                raise RuntimeError("EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            # Set first to movement_path_by_vehicle at yielding.
            first = movement_path_by_vehicle[yielding]
            # Set second to movement_path_by_vehicle at priority.
            second = movement_path_by_vehicle[priority]
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set relationship to the result of self.zones.relationship(first, second).
                relationship = self.zones.relationship(first, second)
            # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
            except (KeyError, TypeError, ValueError):
                # Raise RuntimeError with the text 'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED' to stop this
                # execution path.
                raise RuntimeError(
                    "EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            # Run this branch when relationship.coordinated_conflict and relationship.conflict_zone_id.
            if (relationship.coordinated_conflict and
                    # Evaluate relationship.conflict_zone_id as part of the enclosing expression.
                    relationship.conflict_zone_id):
                # Set zone_ids to a tuple built from the requested attribute of relationship or a tuple containing
                # relationship.conflict_zone_id.
                zone_ids = tuple(getattr(
                    # Supply relationship to getattr.
                    relationship, "conflict_zone_ids", ()) or
                    # Evaluate a tuple containing relationship.conflict_zone_id as part of the enclosing
                    # expression.
                    (relationship.conflict_zone_id,))
                # Set relevance to PHYSICAL_RELEVANT.
                relevance = PHYSICAL_RELEVANT
                # Set status to relationship.conflict_type.
                status = relationship.conflict_type
            # Run this branch when the negation of relationship.coordinated_conflict and the negation of
            # relationship.physical_overlap and relationship.conflict_zone_id is the same object as None and
            # relationship.conflict_type equals the text 'NO_CONFLICT'.
            elif (not relationship.coordinated_conflict and
                  # Evaluate the negation of relationship.physical_overlap as part of the enclosing expression.
                  not relationship.physical_overlap and
                  # Evaluate relationship.conflict_zone_id is the same object as None as part of the enclosing
                  # expression.
                  relationship.conflict_zone_id is None and
                  # Evaluate relationship.conflict_type equals the text 'NO_CONFLICT' as part of the enclosing
                  # expression.
                  relationship.conflict_type == "NO_CONFLICT"):
                # Set zone_ids to an empty tuple.
                zone_ids = ()
                # Set relevance to NONCONFLICTING.
                relevance = NONCONFLICTING
                # Set status to the text 'AUTHORITATIVE_MAP_NO_CONFLICT'.
                status = "AUTHORITATIVE_MAP_NO_CONFLICT"
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Raise RuntimeError with the text 'EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED' to stop this
                # execution path.
                raise RuntimeError(
                    "EXECUTION_EDGE_PHYSICAL_RELATIONSHIP_UNRESOLVED")
            # Iterate over zone_ids, binding each item to zone_id.
            for zone_id in zone_ids:
                # Append the result of PhysicalExecutionObligation(yielding, priority, zone_id, a tuple containing
                # yielding, priority) to obligations.
                obligations.append(PhysicalExecutionObligation(
                    # Supply a tuple containing yielding, priority to PhysicalExecutionObligation.
                    yielding, priority, zone_id, (yielding, priority)))
            # Append the result of CoordinationEdgePhysicalInterpretation(yielding, priority, first, second, True,
            # status, zone_ids, the number of entries in zone_ids,...) to interpretations.
            interpretations.append(CoordinationEdgePhysicalInterpretation(
                # Supply yielding to CoordinationEdgePhysicalInterpretation.
                yielding, priority, first, second, True, status, zone_ids,
                # Supply the number of entries in zone_ids to CoordinationEdgePhysicalInterpretation.
                len(zone_ids), relevance,
                "CONFLICT_ZONE_MANAGER_AUTHORITATIVE_MAP_RELATIONSHIP",
                # Store True under 'environment_transition_only'.
                {"environment_transition_only": True,
                 # Store False under 'actor_information'.
                 # Store 0 under 'numerical_thresholds'.
                 "actor_information": False, "numerical_thresholds": 0}))
        # Set physical to a tuple built from the sorted values from a set of item.source_coordination_edge for
        # item in obligations.
        physical = tuple(sorted({item.source_coordination_edge
                                 # Evaluate obligations as part of the enclosing expression.
                                 for item in obligations}))
        # Set coordination_analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(a tuple built from
        # the sorted values from active_vehicle_ids, a tuple built from a lazy sequence...).
        coordination_analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            # Supply a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
            # priority_vehicle_id for (a, b) in coordination to RegulatoryPrecedenceGraphBuilder.analyse.
            tuple(sorted(active_vehicle_ids)), tuple(
                # Store a under 'yielding_vehicle_id'.
                # Store b under 'priority_vehicle_id'.
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                # Evaluate coordination as part of the enclosing expression.
                for a, b in coordination))
        # Set physical_analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(a tuple built from the
        # sorted values from active_vehicle_ids, a tuple built from a lazy sequence...).
        physical_analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            # Supply a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
            # priority_vehicle_id for (a, b) in physical to RegulatoryPrecedenceGraphBuilder.analyse.
            tuple(sorted(active_vehicle_ids)), tuple(
                # Store a under 'yielding_vehicle_id'.
                # Store b under 'priority_vehicle_id'.
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                # Evaluate physical as part of the enclosing expression.
                for a, b in physical))
        # Set nonphysical to a tuple built from a lazy sequence of a tuple containing item.yielding_vehicle_id,
        # item.priority_vehicle_id for item in interpretations; retain entries satisfying item.execution_relevance
        # equals NONCONFLICTING.
        nonphysical = tuple((item.yielding_vehicle_id, item.priority_vehicle_id)
                            # Evaluate interpretations as part of the enclosing expression.
                            for item in interpretations
                            # Evaluate item.execution_relevance equals NONCONFLICTING as part of the enclosing
                            # expression.
                            if item.execution_relevance == NONCONFLICTING)
        # Return the result of PhysicalExecutionObligationSet(coordination, a tuple built from interpretations,
        # physical, nonphysical, a tuple built from...) to the caller.
        return PhysicalExecutionObligationSet(
            # Supply a tuple built from interpretations to PhysicalExecutionObligationSet.
            coordination, tuple(interpretations), physical, nonphysical,
            # Supply a tuple built from obligations to PhysicalExecutionObligationSet.
            tuple(obligations), physical,
            # Supply a Boolean built from coordination_analysis at 'cycle_detected' to
            # PhysicalExecutionObligationSet.
            bool(coordination_analysis["cycle_detected"]),
            # Supply a Boolean built from physical_analysis at 'cycle_detected' to PhysicalExecutionObligationSet.
            bool(physical_analysis["cycle_detected"]),
            # Store 0 under 'policy_edges_removed'.
            # Store 0 under 'protocol_edges_modified'.
            {"policy_edges_removed": 0, "protocol_edges_modified": 0,
             # Store 0 under 'policy_actions_resampled'.
             "policy_actions_resampled": 0,
             "simulation_execution_mapping":
                 "AUTHORITATIVE_ENVIRONMENT_TRAJECTORY",
             "actor_information": "EGO_LOCAL_PARTIAL_OBSERVATION",
             "future_deployment_mapping":
                 "CONSERVATIVE_FEASIBLE_PATH_CONFLICT_SET"})
