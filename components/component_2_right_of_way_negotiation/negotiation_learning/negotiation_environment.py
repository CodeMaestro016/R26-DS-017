"""Construct immutable local negotiation snapshots without taking actions."""

import math

from .models import NegotiationAction, NegotiationProblemSnapshot, NegotiationStatus
from .claim_semantics import NegotiationClaimBuilder
from .observation_builder import GraphObservationBuilder
from .precedence_graph import RegulatoryPrecedenceGraphBuilder
from .joint_graph_assembler import JointLocalPrecedenceGraphAssembler


class NegotiationEnvironment:
    """Not a Gym environment: this class constructs shadow evidence only."""

    def __init__(self, precedence_builder=None, observation_builder=None,
                 joint_assembler=None):
        self.precedence_builder = precedence_builder or RegulatoryPrecedenceGraphBuilder()
        self.observation_builder = observation_builder or GraphObservationBuilder()
        self.joint_assembler = joint_assembler or JointLocalPrecedenceGraphAssembler()
        self._totals = self._empty_totals()

    @staticmethod
    def _empty_totals():
        return {
            "local_precedence_claims_published": 0,
            "joint_local_negotiation_snapshots_built": 0,
            "snapshots_with_active_conflict_participants": 0,
            "messages_received_by_local_agents": 0,
            "messages_adopted_into_connected_components": 0,
            "unconnected_messages_ignored": 0,
            "duplicate_claims_merged": 0,
            "communicated_precedence_disagreements": 0,
            "joint_precedence_edges": 0,
            "joint_graphs_with_expanded_participant_sets": 0,
            "regulatory_order_resolved_snapshots": 0,
            "regulatory_cycle_snapshots": 0,
            "unresolved_precedence_snapshots": 0,
            "no_active_conflict_snapshots": 0,
            "strongly_connected_cyclic_components_observed": 0,
            "maximum_local_participants_before_v2v_expansion": 0,
            "maximum_joint_participants_after_v2v_expansion": 0,
            "source_snapshot_mismatches": 0,
            "regulatory_profile_mismatches": 0,
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

    def build_local_claims(self, ldm, current_time):
        local_graph = self.precedence_builder.build(ldm)
        messages = self.precedence_builder.claim_messages(
            ldm, local_graph, current_time
        )
        self._totals["local_precedence_claims_published"] += len(messages)
        return local_graph, messages

    def build_snapshot(self, ldm, current_time, current_step_messages=(),
                       local_graph=None):
        conflict = ldm.get_current_conflict_graph() or {}
        temporal = ldm.get_current_temporal_assessment() or {}
        regulatory = ldm.get_current_regulatory_assessment() or {}
        timestamps = (
            conflict.get("timestamp"), temporal.get("timestamp"),
            regulatory.get("timestamp"),
        )
        consistent = self._timestamps_match(timestamps)
        local_graph = local_graph or self.precedence_builder.build(ldm)
        graph = self.joint_assembler.assemble(
            ldm.ego_id, current_time, local_graph, current_step_messages
        )
        consistent = consistent and not graph["source_snapshot_mismatches"]
        active = len(graph["joint_node_ids"]) > 1
        status = self.classify_status(graph, consistent, active)
        observation = self.observation_builder.build(ldm, current_time, graph)
        claim_set = NegotiationClaimBuilder().build(
            ldm.ego_id, graph, status.value,
            status in {
                NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
                NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE,
            }, consistent,
        )
        action_evidence = {
            "mask_scope": "CLAIM_LEVEL",
            "mask_type": "BOOLEAN_DETERMINISTIC",
            "policy_authority": claim_set.policy_authority.value,
            "policy_authority_reason": (
                claim_set.policy_authority_reason.value
                if claim_set.policy_authority_reason else None
            ),
            "mandatory_yield_obligations": tuple(
                (item.yielding_vehicle_id, item.priority_vehicle_id)
                for item in claim_set.mandatory_yield_obligations
            ),
            "ego_precedence_claims": tuple(
                (item.yielding_vehicle_id, item.priority_vehicle_id)
                for item in claim_set.ego_precedence_claims
            ),
            "protocol_completion_status": claim_set.protocol_completion_status,
        }
        snapshot = NegotiationProblemSnapshot(
            ldm.ego_id, float(current_time), graph["joint_node_ids"],
            graph["local_node_ids"], graph["local_precedence_edges"],
            graph["communicated_precedence_edges"], graph["joint_precedence_edges"],
            graph["joint_precedence_edges"], graph["received_claim_count"],
            len(graph["adopted_communicated_claims"]),
            len(graph["ignored_unconnected_claims"]),
            graph["duplicate_claims_merged"],
            graph["communicated_disagreements"],
            graph["regulatory_profile_mismatches"], graph["communication_model"],
            graph["unresolved_relations"],
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
        if graph.get("regulatory_profile_mismatches"):
            return NegotiationStatus.REGULATORY_PROFILE_MISMATCH
        if graph.get("communicated_disagreements"):
            return NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT
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
        self._totals["joint_local_negotiation_snapshots_built"] += 1
        self._totals["snapshots_with_active_conflict_participants"] += len(snapshot.participant_ids) > 1
        self._totals["messages_received_by_local_agents"] += snapshot.messages_received
        self._totals["messages_adopted_into_connected_components"] += snapshot.messages_adopted
        self._totals["unconnected_messages_ignored"] += snapshot.messages_ignored_unconnected
        self._totals["duplicate_claims_merged"] += snapshot.duplicate_claims_merged
        self._totals["communicated_precedence_disagreements"] += len(snapshot.communicated_disagreements)
        self._totals["joint_precedence_edges"] += len(snapshot.joint_precedence_edges)
        self._totals["joint_graphs_with_expanded_participant_sets"] += (
            len(snapshot.participant_ids) > len(snapshot.local_participant_ids)
        )
        self._totals["strongly_connected_cyclic_components_observed"] += len(
            snapshot.strongly_connected_components
        )
        self._totals["maximum_local_participants_before_v2v_expansion"] = max(
            self._totals["maximum_local_participants_before_v2v_expansion"],
            len(snapshot.local_participant_ids),
        )
        self._totals["maximum_joint_participants_after_v2v_expansion"] = max(
            self._totals["maximum_joint_participants_after_v2v_expansion"],
            len(snapshot.participant_ids),
        )
        self._totals["regulatory_profile_mismatches"] += len(snapshot.regulatory_profile_mismatches)
        mapping = {
            NegotiationStatus.REGULATORY_ORDER_RESOLVED.value: "regulatory_order_resolved_snapshots",
            NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value: "regulatory_cycle_snapshots",
            NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value: "unresolved_precedence_snapshots",
            NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value: "unresolved_precedence_snapshots",
            NegotiationStatus.NO_ACTIVE_CONFLICT.value: "no_active_conflict_snapshots",
            NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value: "source_snapshot_mismatches",
            NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value: "unresolved_precedence_snapshots",
            NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value: "unresolved_precedence_snapshots",
        }
        self._totals[mapping[snapshot.negotiation_status]] += 1

    def validation_summary(self):
        return dict(self._totals)

    def reset(self):
        self._totals = self._empty_totals()
