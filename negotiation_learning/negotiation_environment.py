"""Construct immutable local negotiation snapshots without taking actions."""

import math

from .models import NegotiationAction, NegotiationProblemSnapshot, NegotiationStatus
from .observation_builder import GraphObservationBuilder
from .precedence_graph import RegulatoryPrecedenceGraphBuilder


class NegotiationEnvironment:
    """Not a Gym environment: this class constructs shadow evidence only."""

    def __init__(self, precedence_builder=None, observation_builder=None):
        self.precedence_builder = precedence_builder or RegulatoryPrecedenceGraphBuilder()
        self.observation_builder = observation_builder or GraphObservationBuilder()
        self._totals = self._empty_totals()

    @staticmethod
    def _empty_totals():
        return {
            "local_negotiation_snapshots_built": 0,
            "snapshots_with_active_conflict_participants": 0,
            "total_precedence_edges": 0,
            "regulatory_order_resolved_snapshots": 0,
            "regulatory_cycle_snapshots": 0,
            "unresolved_precedence_snapshots": 0,
            "no_active_conflict_snapshots": 0,
            "strongly_connected_cyclic_components_observed": 0,
            "maximum_participants_in_one_local_negotiation_problem": 0,
            "source_snapshot_mismatches": 0,
            "target_route_truth_fields_consumed": 0,
            "control_actions_issued_by_negotiation_environment": 0,
        }

    @staticmethod
    def _timestamps_match(values):
        if any(value is None for value in values):
            return False
        numbers = tuple(float(value) for value in values)
        if not all(math.isfinite(value) for value in numbers):
            return False
        reference = numbers[0]
        # ULP-only tolerance handles alternate floating representation of one
        # simulation instant; this is not an operational timing threshold.
        tolerance = math.ulp(max(1.0, *(abs(value) for value in numbers))) * 8
        return all(abs(value - reference) <= tolerance for value in numbers[1:])

    def build_snapshot(self, ldm, current_time):
        conflict = ldm.get_current_conflict_graph() or {}
        temporal = ldm.get_current_temporal_assessment() or {}
        regulatory = ldm.get_current_regulatory_assessment() or {}
        timestamps = (
            conflict.get("timestamp"), temporal.get("timestamp"),
            regulatory.get("timestamp"),
        )
        consistent = self._timestamps_match(timestamps)
        graph = self.precedence_builder.build(ldm)
        active = len(graph["node_ids"]) > 1
        status = self.classify_status(graph, consistent, active)
        observation = self.observation_builder.build(ldm, current_time, graph)
        ego_yields = any(
            edge["yielding_vehicle_id"] == ldm.ego_id
            for edge in graph["precedence_edges"]
        )
        action_evidence = {
            NegotiationAction.KEEP_CLAIM.value: (
                "PROHIBITED_BY_MANDATORY_YIELD" if ego_yields
                else "DEFERRED_PROTOCOL_SEMANTICS"
            ),
            NegotiationAction.RELINQUISH_CLAIM.value: "DEFERRED_PROTOCOL_SEMANTICS",
            "active_mask_status": "NOT_ACTIVATED_STEP_5A",
        }
        snapshot = NegotiationProblemSnapshot(
            ldm.ego_id, float(current_time), graph["node_ids"],
            graph["precedence_edges"], graph["unresolved_relations"],
            graph["cycle_detected"], graph["cycle_members"],
            graph["strongly_connected_components"],
            graph["yield_precedence_graph_topological_order"],
            graph["regulatory_service_order"], status.value,
            status in {
                NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
                NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE,
            },
            observation.to_dict(), tuple(action.value for action in NegotiationAction),
            action_evidence,
            ("additional_delay_seconds", "waiting_time_seconds",
             "successful_conflict_zone_service"),
            *timestamps, consistent,
        )
        self._count(snapshot)
        return snapshot.to_dict()

    @staticmethod
    def classify_status(graph, source_consistent=True, active=True):
        """Classify structure categorically, without scores or thresholds."""
        unresolved_statuses = {
            item["regulatory_status"] for item in graph["unresolved_relations"]
        }
        if not source_consistent:
            return NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH
        if not active:
            return NegotiationStatus.NO_ACTIVE_CONFLICT
        if "REGULATORY_INPUT_UNRESOLVED" in unresolved_statuses:
            return NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED
        if unresolved_statuses:
            return NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE
        if graph["cycle_detected"]:
            return NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE
        return NegotiationStatus.REGULATORY_ORDER_RESOLVED

    def _count(self, snapshot):
        self._totals["local_negotiation_snapshots_built"] += 1
        self._totals["snapshots_with_active_conflict_participants"] += len(snapshot.participant_ids) > 1
        self._totals["total_precedence_edges"] += len(snapshot.precedence_edges)
        self._totals["strongly_connected_cyclic_components_observed"] += len(
            snapshot.strongly_connected_components
        )
        self._totals["maximum_participants_in_one_local_negotiation_problem"] = max(
            self._totals["maximum_participants_in_one_local_negotiation_problem"],
            len(snapshot.participant_ids),
        )
        mapping = {
            NegotiationStatus.REGULATORY_ORDER_RESOLVED.value: "regulatory_order_resolved_snapshots",
            NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value: "regulatory_cycle_snapshots",
            NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value: "unresolved_precedence_snapshots",
            NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value: "unresolved_precedence_snapshots",
            NegotiationStatus.NO_ACTIVE_CONFLICT.value: "no_active_conflict_snapshots",
            NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value: "source_snapshot_mismatches",
        }
        self._totals[mapping[snapshot.negotiation_status]] += 1

    def validation_summary(self):
        return dict(self._totals)

    def reset(self):
        self._totals = self._empty_totals()
