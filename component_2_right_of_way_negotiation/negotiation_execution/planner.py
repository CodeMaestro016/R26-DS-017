"""Convert protocol-authoritative precedence into zone permissions."""

# Import RegulatoryPrecedenceGraphBuilder from negotiation_learning.precedence_graph for the operations below.
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import ConflictZoneExecutionConstraint, ConflictZoneExecutionPlan, VehicleConflictZonePermission from .models
# for the operations below.
from .models import (ConflictZoneExecutionConstraint,
                     ConflictZoneExecutionPlan, VehicleConflictZonePermission)


# Define ExecutionSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ExecutionSemanticError(ValueError):
    # Keep this block syntactically valid without performing an operation.
    pass


# Define ConflictZoneExecutionPlanner to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class ConflictZoneExecutionPlanner:
    # Set EDGE_DIRECTION to the text 'YIELDING_TO_PRIORITY'.
    EDGE_DIRECTION = "YIELDING_TO_PRIORITY"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input conflict_zone_manager: the supplied conflict zone manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, conflict_zone_manager):
        # Set self.paths to path_manager.
        self.paths = path_manager
        # Set self.zones to conflict_zone_manager.
        self.zones = conflict_zone_manager

    # Return an execution plan or a precise non-executable classification.
    # Input kwargs: the supplied kwargs.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def classify_plan(self, **kwargs):
        """Return an execution plan or a precise non-executable classification."""
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Return a tuple containing the result of self.plan(), None to the caller.
            return self.plan(**kwargs), None
        # Handle ExecutionSemanticError as error using the recovery steps below.
        except ExecutionSemanticError as error:
            # Run this branch when error.args equals a tuple containing the text
            # 'EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED'.
            if error.args == ("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED",):
                # Return a tuple containing None, error.args at 0 to the caller.
                return None, error.args[0]
            # Re-raise the active exception.
            raise

    # Plan using the inputs and processing steps below.
    # Input source_snapshot_id: the supplied source snapshot id.
    # Input effective_coordination_graph: the supplied effective coordination graph.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input movement_path_by_vehicle: the supplied movement path by vehicle.
    # Input timestamp: the supplied timestamp.
    # Input source_protocol_state: the supplied source protocol state.
    # Input cleared_vehicle_zones: the supplied cleared vehicle zones.
    # Input physical_obligation_set: the supplied physical obligation set.
    # Output: the result of ConflictZoneExecutionPlan(plan_id, source_snapshot_id, graph, active, a tuple built
    # from constraints, a tuple built from...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def plan(self, *, source_snapshot_id, effective_coordination_graph,
             # Declare active_vehicle_ids, movement_path_by_vehicle, timestamp as input parameters.
             active_vehicle_ids, movement_path_by_vehicle, timestamp,
             # Declare source_protocol_state, cleared_vehicle_zones as input parameters.
             source_protocol_state, cleared_vehicle_zones=(),
             # Declare physical_obligation_set as input parameter.
             physical_obligation_set=None):
        # Set graph to a tuple built from the sorted values from a lazy sequence of a tuple built from edge for
        # edge in effective_coordination_graph.
        graph = tuple(sorted(tuple(edge) for edge in effective_coordination_graph))
        # Set active to a tuple built from the sorted values from active_vehicle_ids.
        active = tuple(sorted(active_vehicle_ids))
        # Set physical_graph to physical_obligation_set.physical_execution_graph when physical_obligation_set is a
        # different object from None, otherwise graph.
        physical_graph = (physical_obligation_set.physical_execution_graph
                          # Evaluate physical_obligation_set is a different object from None as part of the
                          # enclosing expression.
                          if physical_obligation_set is not None else graph)
        # Set edge_dicts to a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
        # priority_vehicle_id for (a, b) in physical_graph.
        edge_dicts = tuple({"yielding_vehicle_id": a, "priority_vehicle_id": b}
                           # Evaluate physical_graph as part of the enclosing expression.
                           for a, b in physical_graph)
        # Set analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(active, edge_dicts).
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(active, edge_dicts)
        # Set cleared to a set built from a lazy sequence of a tuple built from item for item in
        # cleared_vehicle_zones.
        cleared = set(tuple(item) for item in cleared_vehicle_zones)
        # Set constraints to an empty list.
        constraints = []
        # Run this branch when physical_obligation_set is the same object as None.
        if physical_obligation_set is None:
            # Set obligation_rows to a tuple built from a lazy sequence of a tuple containing yielding, priority,
            # None for (yielding, priority) in graph.
            obligation_rows = tuple((yielding, priority, None)
                                    # Evaluate a tuple containing yielding, priority as part of the enclosing
                                    # expression.
                                    for yielding, priority in graph)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set obligation_rows to a tuple built from a lazy sequence of a tuple containing
            # item.yielding_vehicle_id, item.priority_vehicle_id, item.conflict_zone_id for item in
            # physical_obligation_set.execution_constraints.
            obligation_rows = tuple(
                # Evaluate a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id,
                # item.conflict_zone_id as part of the enclosing expression.
                (item.yielding_vehicle_id, item.priority_vehicle_id,
                 # Include item.conflict_zone_id in this tuple.
                 item.conflict_zone_id)
                # Evaluate physical_obligation_set.execution_constraints as part of the enclosing expression.
                for item in physical_obligation_set.execution_constraints)
        # Iterate over obligation_rows, binding each item to (yielding, priority, mapped_zone_id).
        for yielding, priority, mapped_zone_id in obligation_rows:
            # Run this branch when yielding does not belong to active or priority does not belong to active.
            if yielding not in active or priority not in active:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set first to movement_path_by_vehicle at yielding.
            first = movement_path_by_vehicle[yielding]
            # Set second to movement_path_by_vehicle at priority.
            second = movement_path_by_vehicle[priority]
            # Set relation to the result of self.zones.relationship(first, second).
            relation = self.zones.relationship(first, second)
            # Run this branch when mapped_zone_id is the same object as None.
            if mapped_zone_id is None:
                # Run this branch when the negation of relation.coordinated_conflict or the negation of
                # relation.conflict_zone_id.
                if not relation.coordinated_conflict or not relation.conflict_zone_id:
                    # Raise ExecutionSemanticError with the text 'EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED' to
                    # stop this execution path.
                    raise ExecutionSemanticError("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED")
                # Set zone_id to relation.conflict_zone_id.
                zone_id = relation.conflict_zone_id
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set authoritative_zone_ids to a tuple built from the requested attribute of relation or a tuple
                # containing relation.conflict_zone_id when relation.conflict_zone_id, otherwise an empty tuple.
                authoritative_zone_ids = tuple(getattr(
                    # Supply relation to getattr.
                    relation, "conflict_zone_ids", ()) or
                    # Evaluate a tuple containing relation.conflict_zone_id when relation.conflict_zone_id,
                    # otherwise an empty tuple as part of the enclosing expression.
                    ((relation.conflict_zone_id,)
                     # Evaluate relation.conflict_zone_id as part of the enclosing expression.
                     if relation.conflict_zone_id else ()))
                # Run this branch when the negation of relation.coordinated_conflict or mapped_zone_id does not
                # belong to authoritative_zone_ids.
                if (not relation.coordinated_conflict or
                        # Evaluate mapped_zone_id does not belong to authoritative_zone_ids as part of the
                        # enclosing expression.
                        mapped_zone_id not in authoritative_zone_ids):
                    # Raise ExecutionSemanticError with the text 'EXECUTION_RELEVANT_EDGE_CONSTRAINT_BUILD_FAILED'
                    # to stop this execution path.
                    raise ExecutionSemanticError(
                        "EXECUTION_RELEVANT_EDGE_CONSTRAINT_BUILD_FAILED")
                # Set zone_id to mapped_zone_id.
                zone_id = mapped_zone_id
            # Set status to the text 'ALREADY_CLEARED' when a tuple containing priority, zone_id belongs to
            # cleared, otherwise the text 'BLOCKED_BY_PRECEDENCE'.
            status = ("ALREADY_CLEARED" if
                      # Evaluate a tuple containing priority, zone_id belongs to cleared as part of the enclosing
                      # expression.
                      (priority, zone_id) in cleared else
                      "BLOCKED_BY_PRECEDENCE")
            # Append the result of ConflictZoneExecutionConstraint(yielding, priority, zone_id, a tuple containing
            # yielding, priority, source_protocol_state,...) to constraints.
            constraints.append(ConflictZoneExecutionConstraint(
                # Supply yielding to ConflictZoneExecutionConstraint.
                yielding, priority, zone_id,
                # Supply source_protocol_state to ConflictZoneExecutionConstraint.
                (yielding, priority), source_protocol_state, source_snapshot_id,
                # Store the text 'CONFLICT_ZONE_MANAGER' under 'zone_source'.
                status, {"zone_source": "CONFLICT_ZONE_MANAGER",
                         "route_metadata_class": "SIMULATOR_EXECUTION_METADATA"}))
        # Call constraints.sort with the supplied arguments.
        constraints.sort(key=lambda item: (item.yielding_vehicle_id,
                                            # Include item.priority_vehicle_id in this tuple.
                                            item.priority_vehicle_id,
                                            # Include item.conflict_zone_id in this tuple.
                                            item.conflict_zone_id))
        # Set permissions to an empty list.
        permissions = []
        # Iterate over active, binding each item to vehicle.
        for vehicle in active:
            # Set applicable to a list of item for item in constraints; retain entries satisfying
            # item.yielding_vehicle_id equals vehicle.
            applicable = [item for item in constraints
                          # Evaluate item.yielding_vehicle_id equals vehicle as part of the enclosing expression.
                          if item.yielding_vehicle_id == vehicle]
            # Iterate over the sorted values from a set of item.conflict_zone_id for item in applicable, binding
            # each item to zone_id.
            for zone_id in sorted({item.conflict_zone_id for item in applicable}):
                # Set zone_items to a list of item for item in applicable; retain entries satisfying
                # item.conflict_zone_id equals zone_id.
                zone_items = [item for item in applicable if item.conflict_zone_id == zone_id]
                # Set blockers to a tuple built from the sorted values from a lazy sequence of
                # item.priority_vehicle_id for item in zone_items; retain entries satisfying
                # item.constraint_status differs from 'ALREADY_CLEARED'.
                blockers = tuple(sorted(item.priority_vehicle_id for item in zone_items
                                        # Evaluate item.constraint_status differs from the text 'ALREADY_CLEARED'
                                        # as part of the enclosing expression.
                                        if item.constraint_status != "ALREADY_CLEARED"))
                # Append the result of VehicleConflictZonePermission(vehicle, zone_id, the text
                # 'BLOCKED_BY_PRECEDENCE' when blockers, otherwise the text...) to permissions.
                permissions.append(VehicleConflictZonePermission(
                    # Supply vehicle to VehicleConflictZonePermission.
                    vehicle, zone_id,
                    # Supply the text 'BLOCKED_BY_PRECEDENCE' when blockers, otherwise the text 'PERMITTED' to
                    # VehicleConflictZonePermission.
                    "BLOCKED_BY_PRECEDENCE" if blockers else "PERMITTED",
                    # Supply a floating-point number built from timestamp to VehicleConflictZonePermission.
                    blockers, graph, float(timestamp),
                    # Store the text 'COMPLETE_EFFECTIVE_GRAPH' under 'permission_source'.
                    {"permission_source": "COMPLETE_EFFECTIVE_GRAPH"}))
        # Set blocked to a tuple built from the sorted values from a set of item.vehicle_id for item in
        # permissions; retain entries satisfying item.permission_status equals 'BLOCKED_BY_PRECEDENCE'.
        blocked = tuple(sorted({item.vehicle_id for item in permissions
                                # Evaluate item.permission_status equals the text 'BLOCKED_BY_PRECEDENCE' as part
                                # of the enclosing expression.
                                if item.permission_status == "BLOCKED_BY_PRECEDENCE"}))
        # Set ready to a tuple built from a lazy sequence of vehicle for vehicle in active; retain entries
        # satisfying vehicle does not belong to blocked.
        ready = tuple(vehicle for vehicle in active if vehicle not in blocked)
        # Set graph_status to the text 'EXECUTION_BLOCKED_PRECEDENCE_CYCLE' when analysis at 'cycle_detected',
        # otherwise the text 'EXECUTABLE'.
        graph_status = ("EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
                        # Evaluate analysis at 'cycle_detected' as part of the enclosing expression.
                        if analysis["cycle_detected"] else "EXECUTABLE")
        # Run this branch when graph_status differs from the text 'EXECUTABLE'.
        if graph_status != "EXECUTABLE":
            # Set ready to an empty tuple.
            ready = ()
        # Set plan_id to a tuple containing the text 'EXECUTION_PLAN_V1', source_snapshot_id, graph, a tuple built
        # from a lazy sequence of a tuple...
        plan_id = ("EXECUTION_PLAN_V1", source_snapshot_id, graph,
                   # Include a tuple built from a lazy sequence of a tuple containing item.vehicle_id,
                   # item.conflict_zone_id, item.permission_status for item in permissions in this tuple.
                   tuple((item.vehicle_id, item.conflict_zone_id,
                          # Include item.permission_status in this tuple.
                          item.permission_status) for item in permissions))
        # Return the result of ConflictZoneExecutionPlan(plan_id, source_snapshot_id, graph, active, a tuple built
        # from constraints, a tuple built from...) to the caller.
        return ConflictZoneExecutionPlan(
            # Supply source_snapshot_id to ConflictZoneExecutionPlan.
            plan_id, source_snapshot_id, graph, active, tuple(constraints),
            # Supply a tuple built from permissions to ConflictZoneExecutionPlan.
            tuple(permissions), ready, blocked, graph_status,
            # Store self.EDGE_DIRECTION under 'edge_direction'.
            {"edge_direction": self.EDGE_DIRECTION,
             # Store the result of repr(physical_graph) under 'physical_execution_graph'.
             "physical_execution_graph": repr(physical_graph),
             # Store the result of repr(graph) under 'source_effective_coordination_graph'.
             "source_effective_coordination_graph": repr(graph),
             "ready_definition": "NO_ACTIVE_OUTGOING_PRECEDENCE_OBLIGATION",
             "vehicle_iteration_order_consumed": "False"})
