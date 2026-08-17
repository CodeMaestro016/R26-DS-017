"""Convert protocol-authoritative precedence into zone permissions."""

from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
from .models import (ConflictZoneExecutionConstraint,
                     ConflictZoneExecutionPlan, VehicleConflictZonePermission)


class ExecutionSemanticError(ValueError):
    pass


class ConflictZoneExecutionPlanner:
    EDGE_DIRECTION = "YIELDING_TO_PRIORITY"

    def __init__(self, path_manager, conflict_zone_manager):
        self.paths = path_manager
        self.zones = conflict_zone_manager

    def classify_plan(self, **kwargs):
        """Return an execution plan or a precise non-executable classification."""
        try:
            return self.plan(**kwargs), None
        except ExecutionSemanticError as error:
            if error.args == ("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED",):
                return None, error.args[0]
            raise

    def plan(self, *, source_snapshot_id, effective_coordination_graph,
             active_vehicle_ids, movement_path_by_vehicle, timestamp,
             source_protocol_state, cleared_vehicle_zones=()):
        graph = tuple(sorted(tuple(edge) for edge in effective_coordination_graph))
        active = tuple(sorted(active_vehicle_ids))
        edge_dicts = tuple({"yielding_vehicle_id": a, "priority_vehicle_id": b}
                           for a, b in graph)
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(active, edge_dicts)
        cleared = set(tuple(item) for item in cleared_vehicle_zones)
        constraints = []
        for yielding, priority in graph:
            if yielding not in active or priority not in active:
                continue
            first = movement_path_by_vehicle[yielding]
            second = movement_path_by_vehicle[priority]
            relation = self.zones.relationship(first, second)
            if not relation.coordinated_conflict or not relation.conflict_zone_id:
                raise ExecutionSemanticError("EXECUTION_GRAPH_PHYSICAL_CONFLICT_UNORDERED")
            status = ("ALREADY_CLEARED" if
                      (priority, relation.conflict_zone_id) in cleared else
                      "BLOCKED_BY_PRECEDENCE")
            constraints.append(ConflictZoneExecutionConstraint(
                yielding, priority, relation.conflict_zone_id,
                (yielding, priority), source_protocol_state, source_snapshot_id,
                status, {"zone_source": "CONFLICT_ZONE_MANAGER",
                         "route_metadata_class": "SIMULATOR_EXECUTION_METADATA"}))
        constraints.sort(key=lambda item: (item.yielding_vehicle_id,
                                            item.priority_vehicle_id,
                                            item.conflict_zone_id))
        permissions = []
        for vehicle in active:
            applicable = [item for item in constraints
                          if item.yielding_vehicle_id == vehicle]
            for zone_id in sorted({item.conflict_zone_id for item in applicable}):
                zone_items = [item for item in applicable if item.conflict_zone_id == zone_id]
                blockers = tuple(sorted(item.priority_vehicle_id for item in zone_items
                                        if item.constraint_status != "ALREADY_CLEARED"))
                permissions.append(VehicleConflictZonePermission(
                    vehicle, zone_id,
                    "BLOCKED_BY_PRECEDENCE" if blockers else "PERMITTED",
                    blockers, graph, float(timestamp),
                    {"permission_source": "COMPLETE_EFFECTIVE_GRAPH"}))
        blocked = tuple(sorted({item.vehicle_id for item in permissions
                                if item.permission_status == "BLOCKED_BY_PRECEDENCE"}))
        ready = tuple(vehicle for vehicle in active if vehicle not in blocked)
        graph_status = ("EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
                        if analysis["cycle_detected"] else "EXECUTABLE")
        if graph_status != "EXECUTABLE":
            ready = ()
        plan_id = ("EXECUTION_PLAN_V1", source_snapshot_id, graph,
                   tuple((item.vehicle_id, item.conflict_zone_id,
                          item.permission_status) for item in permissions))
        return ConflictZoneExecutionPlan(
            plan_id, source_snapshot_id, graph, active, tuple(constraints),
            tuple(permissions), ready, blocked, graph_status,
            {"edge_direction": self.EDGE_DIRECTION,
             "ready_definition": "NO_ACTIVE_OUTGOING_PRECEDENCE_OBLIGATION",
             "vehicle_iteration_order_consumed": "False"})
