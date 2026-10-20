"""Construct immutable local negotiation snapshots without taking actions."""

# Import math for use in this module.
import math

# Import NegotiationAction, NegotiationProblemSnapshot, NegotiationStatus from .models for the operations below.
from .models import NegotiationAction, NegotiationProblemSnapshot, NegotiationStatus
# Import NegotiationClaimBuilder from .claim_semantics for the operations below.
from .claim_semantics import NegotiationClaimBuilder
# Import GraphObservationBuilder from .observation_builder for the operations below.
from .observation_builder import GraphObservationBuilder
# Import RegulatoryPrecedenceGraphBuilder from .precedence_graph for the operations below.
from .precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import JointLocalPrecedenceGraphAssembler from .joint_graph_assembler for the operations below.
from .joint_graph_assembler import JointLocalPrecedenceGraphAssembler


# Not a Gym environment: this class constructs shadow evidence only.
# Instances expose the attributes and methods implemented in this class.
class NegotiationEnvironment:
    """Not a Gym environment: this class constructs shadow evidence only."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input precedence_builder: the supplied precedence builder.
    # Input observation_builder: the supplied observation builder.
    # Input joint_assembler: the supplied joint assembler.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, precedence_builder=None, observation_builder=None,
                 # Declare joint_assembler as input parameter.
                 joint_assembler=None):
        # Set self.precedence_builder to precedence_builder or the result of RegulatoryPrecedenceGraphBuilder().
        self.precedence_builder = precedence_builder or RegulatoryPrecedenceGraphBuilder()
        # Set self.observation_builder to observation_builder or the result of GraphObservationBuilder().
        self.observation_builder = observation_builder or GraphObservationBuilder()
        # Set self.joint_assembler to joint_assembler or the result of JointLocalPrecedenceGraphAssembler().
        self.joint_assembler = joint_assembler or JointLocalPrecedenceGraphAssembler()
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Empty totals using the inputs and processing steps below.
    # Output: a dictionary containing local_precedence_claims_published,
    # joint_local_negotiation_snapshots_built,...
    def _empty_totals():
        # Return a dictionary containing local_precedence_claims_published,
        # joint_local_negotiation_snapshots_built,... to the caller.
        return {
            # Store 0 under 'local_precedence_claims_published'.
            "local_precedence_claims_published": 0,
            # Store 0 under 'joint_local_negotiation_snapshots_built'.
            "joint_local_negotiation_snapshots_built": 0,
            # Store 0 under 'snapshots_with_active_conflict_participants'.
            "snapshots_with_active_conflict_participants": 0,
            # Store 0 under 'messages_received_by_local_agents'.
            "messages_received_by_local_agents": 0,
            # Store 0 under 'messages_adopted_into_connected_components'.
            "messages_adopted_into_connected_components": 0,
            # Store 0 under 'unconnected_messages_ignored'.
            "unconnected_messages_ignored": 0,
            # Store 0 under 'duplicate_claims_merged'.
            "duplicate_claims_merged": 0,
            # Store 0 under 'communicated_precedence_disagreements'.
            "communicated_precedence_disagreements": 0,
            # Store 0 under 'joint_precedence_edges'.
            "joint_precedence_edges": 0,
            # Store 0 under 'joint_graphs_with_expanded_participant_sets'.
            "joint_graphs_with_expanded_participant_sets": 0,
            # Store 0 under 'regulatory_order_resolved_snapshots'.
            "regulatory_order_resolved_snapshots": 0,
            # Store 0 under 'regulatory_cycle_snapshots'.
            "regulatory_cycle_snapshots": 0,
            # Store 0 under 'unresolved_precedence_snapshots'.
            "unresolved_precedence_snapshots": 0,
            # Store 0 under 'no_active_conflict_snapshots'.
            "no_active_conflict_snapshots": 0,
            # Store 0 under 'strongly_connected_cyclic_components_observed'.
            "strongly_connected_cyclic_components_observed": 0,
            # Store 0 under 'maximum_local_participants_before_v2v_expansion'.
            "maximum_local_participants_before_v2v_expansion": 0,
            # Store 0 under 'maximum_joint_participants_after_v2v_expansion'.
            "maximum_joint_participants_after_v2v_expansion": 0,
            # Store 0 under 'source_snapshot_mismatches'.
            "source_snapshot_mismatches": 0,
            # Store 0 under 'regulatory_profile_mismatches'.
            "regulatory_profile_mismatches": 0,
            # Store 0 under 'target_route_truth_fields_consumed'.
            "target_route_truth_fields_consumed": 0,
            # Store 0 under 'control_actions_issued_by_negotiation_environment'.
            "control_actions_issued_by_negotiation_environment": 0,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Timestamps match using the inputs and processing steps below.
    # Input values: the supplied values.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _timestamps_match(values):
        # Run this branch when whether any item is true in a lazy sequence of value is the same object as None for
        # value in values.
        if any(value is None for value in values):
            # Return False to the caller.
            return False
        # Set numbers to a tuple built from a lazy sequence of a floating-point number built from value for value
        # in values.
        numbers = tuple(float(value) for value in values)
        # Run this branch when the negation of whether every item is true in a lazy sequence of whether value
        # contains finite numeric values for value in numbers.
        if not all(math.isfinite(value) for value in numbers):
            # Return False to the caller.
            return False
        # Set reference to numbers at 0.
        reference = numbers[0]
        # ULP-only tolerance handles alternate floating representation of one
        # simulation instant; this is not an operational timing threshold.
        # Set tolerance to the result of math.ulp(the maximum of 1.0, the unpacked values from (abs(value) for
        # value in numbers)) multiplied by 8.
        tolerance = math.ulp(max(1.0, *(abs(value) for value in numbers))) * 8
        # Return whether every item is true in a lazy sequence of the absolute value of value - reference is at
        # most tolerance for value in numbers sliced by 1: to the caller.
        return all(abs(value - reference) <= tolerance for value in numbers[1:])

    # Build local claims using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Output: a tuple containing local_graph, messages.
    def build_local_claims(self, ldm, current_time):
        # Set local_graph to the result of self.precedence_builder.build(ldm).
        local_graph = self.precedence_builder.build(ldm)
        # Set messages to the result of self.precedence_builder.claim_messages(ldm, local_graph, current_time).
        messages = self.precedence_builder.claim_messages(
            # Supply current_time to self.precedence_builder.claim_messages.
            ldm, local_graph, current_time
        )
        # Update self._totals['local_precedence_claims_published'] to its current value plus the number of entries
        # in messages.
        self._totals["local_precedence_claims_published"] += len(messages)
        # Return a tuple containing local_graph, messages to the caller.
        return local_graph, messages

    # Build snapshot using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Input current_step_messages: the supplied current step messages.
    # Input local_graph: the supplied local graph.
    # Output: the result of snapshot.to_dict().
    def build_snapshot(self, ldm, current_time, current_step_messages=(),
                       # Declare local_graph as input parameter.
                       local_graph=None):
        # Set conflict to the result of ldm.get_current_conflict_graph() or an empty dictionary.
        conflict = ldm.get_current_conflict_graph() or {}
        # Set temporal to the result of ldm.get_current_temporal_assessment() or an empty dictionary.
        temporal = ldm.get_current_temporal_assessment() or {}
        # Set regulatory to the result of ldm.get_current_regulatory_assessment() or an empty dictionary.
        regulatory = ldm.get_current_regulatory_assessment() or {}
        # Set timestamps to a tuple containing 'timestamp' from conflict; use None if absent, 'timestamp' from
        # temporal; use None if absent, 'timestamp'...
        timestamps = (
            # Include 'timestamp' from conflict; use None if absent in this tuple.
            conflict.get("timestamp"), temporal.get("timestamp"),
            # Include 'timestamp' from regulatory; use None if absent in this tuple.
            regulatory.get("timestamp"),
        )
        # Set consistent to the result of self._timestamps_match(timestamps).
        consistent = self._timestamps_match(timestamps)
        # Set local_graph to local_graph or the result of self.precedence_builder.build(ldm).
        local_graph = local_graph or self.precedence_builder.build(ldm)
        # Set graph to the result of self.joint_assembler.assemble(ldm.ego_id, current_time, local_graph,
        # current_step_messages).
        graph = self.joint_assembler.assemble(
            # Supply current_step_messages to self.joint_assembler.assemble.
            ldm.ego_id, current_time, local_graph, current_step_messages
        )
        # Set consistent to consistent and the negation of graph at 'source_snapshot_mismatches'.
        consistent = consistent and not graph["source_snapshot_mismatches"]
        # Set active to the number of entries in graph at 'joint_node_ids' is greater than 1.
        active = len(graph["joint_node_ids"]) > 1
        # Set status to the result of self.classify_status(graph, consistent, active).
        status = self.classify_status(graph, consistent, active)
        # Set observation to the result of self.observation_builder.build(ldm, current_time, graph).
        observation = self.observation_builder.build(ldm, current_time, graph)
        # Set claim_set to the result of NegotiationClaimBuilder().build(ldm.ego_id, graph, status.value, status
        # belongs to a set containing...).
        claim_set = NegotiationClaimBuilder().build(
            # Supply status.value to NegotiationClaimBuilder().build.
            ldm.ego_id, graph, status.value,
            # Supply status belongs to a set containing
            # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,... to NegotiationClaimBuilder().build.
            status in {
                # Include NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE in this set.
                NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
                # Include NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE in this set.
                NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE,
            # Supply consistent to NegotiationClaimBuilder().build.
            }, consistent,
        )
        # Set action_evidence to a dictionary containing mask_scope, mask_type, policy_authority,
        # policy_authority_reason,...
        action_evidence = {
            "mask_scope": "CLAIM_LEVEL",
            "mask_type": "BOOLEAN_DETERMINISTIC",
            # Store claim_set.policy_authority.value under 'policy_authority'.
            "policy_authority": claim_set.policy_authority.value,
            # Store claim_set.policy_authority_reason.value when claim_set.policy_authority_reason, otherwise None
            # under 'policy_authority_reason'.
            "policy_authority_reason": (
                # Evaluate claim_set.policy_authority_reason.value when claim_set.policy_authority_reason,
                # otherwise None as part of the enclosing expression.
                claim_set.policy_authority_reason.value
                # Evaluate claim_set.policy_authority_reason as part of the enclosing expression.
                if claim_set.policy_authority_reason else None
            ),
            # Store a tuple built from a lazy sequence of a tuple containing item.yielding_vehicle_id,
            # item.priority_vehicle_id for item in claim_set.mandatory_yield_obligations under
            # 'mandatory_yield_obligations'.
            "mandatory_yield_obligations": tuple(
                # Evaluate a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id as part of the
                # enclosing expression.
                (item.yielding_vehicle_id, item.priority_vehicle_id)
                # Evaluate claim_set.mandatory_yield_obligations as part of the enclosing expression.
                for item in claim_set.mandatory_yield_obligations
            ),
            # Store a tuple built from a lazy sequence of a tuple containing item.yielding_vehicle_id,
            # item.priority_vehicle_id for item in claim_set.ego_precedence_claims under 'ego_precedence_claims'.
            "ego_precedence_claims": tuple(
                # Evaluate a tuple containing item.yielding_vehicle_id, item.priority_vehicle_id as part of the
                # enclosing expression.
                (item.yielding_vehicle_id, item.priority_vehicle_id)
                # Evaluate claim_set.ego_precedence_claims as part of the enclosing expression.
                for item in claim_set.ego_precedence_claims
            ),
            # Store claim_set.protocol_completion_status under 'protocol_completion_status'.
            "protocol_completion_status": claim_set.protocol_completion_status,
        }
        # Set snapshot to the result of NegotiationProblemSnapshot(ldm.ego_id, a floating-point number built from
        # current_time, graph at 'joint_node_ids', graph at...).
        snapshot = NegotiationProblemSnapshot(
            # Supply graph at 'joint_node_ids' to NegotiationProblemSnapshot.
            ldm.ego_id, float(current_time), graph["joint_node_ids"],
            # Supply graph at 'local_precedence_edges' to NegotiationProblemSnapshot.
            graph["local_node_ids"], graph["local_precedence_edges"],
            # Supply graph at 'communicated_precedence_edges' to NegotiationProblemSnapshot.
            graph["communicated_precedence_edges"], graph["joint_precedence_edges"],
            # Supply graph at 'joint_precedence_edges' to NegotiationProblemSnapshot.
            graph["joint_precedence_edges"], graph["received_claim_count"],
            # Supply the number of entries in graph at 'adopted_communicated_claims' to
            # NegotiationProblemSnapshot.
            len(graph["adopted_communicated_claims"]),
            # Supply the number of entries in graph at 'ignored_unconnected_claims' to NegotiationProblemSnapshot.
            len(graph["ignored_unconnected_claims"]),
            # Supply graph at 'duplicate_claims_merged' to NegotiationProblemSnapshot.
            graph["duplicate_claims_merged"],
            # Supply graph at 'communicated_disagreements' to NegotiationProblemSnapshot.
            graph["communicated_disagreements"],
            # Supply graph at 'regulatory_profile_mismatches' to NegotiationProblemSnapshot.
            graph["regulatory_profile_mismatches"], graph["communication_model"],
            # Supply graph at 'unresolved_relations' to NegotiationProblemSnapshot.
            graph["unresolved_relations"],
            # Supply graph at 'cycle_detected' to NegotiationProblemSnapshot.
            graph["cycle_detected"], graph["cycle_members"],
            # Supply graph at 'strongly_connected_components' to NegotiationProblemSnapshot.
            graph["strongly_connected_components"],
            # Supply graph at 'yield_precedence_graph_topological_order' to NegotiationProblemSnapshot.
            graph["yield_precedence_graph_topological_order"],
            # Supply graph at 'regulatory_service_order' to NegotiationProblemSnapshot.
            graph["regulatory_service_order"], status.value,
            # Supply status belongs to a set containing
            # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,... to NegotiationProblemSnapshot.
            status in {
                # Include NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE in this set.
                NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE,
                # Include NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE in this set.
                NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE,
            },
            # Supply a tuple built from a lazy sequence of action.value for action in NegotiationAction to
            # NegotiationProblemSnapshot.
            observation.to_dict(), tuple(action.value for action in NegotiationAction),
            # Supply action_evidence to NegotiationProblemSnapshot.
            action_evidence,
            # Supply a tuple containing the text 'additional_delay_seconds', the text 'waiting_time_seconds', the
            # text... to NegotiationProblemSnapshot.
            ("additional_delay_seconds", "waiting_time_seconds",
             "successful_conflict_zone_service"),
            # Supply the unpacked values from timestamps to NegotiationProblemSnapshot.
            *timestamps, consistent,
        )
        # Call self._count with the supplied arguments.
        self._count(snapshot)
        # Return the result of snapshot.to_dict() to the caller.
        return snapshot.to_dict()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Classify structure categorically, without scores or thresholds.
    # Input graph: the supplied graph.
    # Input source_consistent: the supplied source consistent.
    # Input active: the supplied active.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def classify_status(graph, source_consistent=True, active=True):
        """Classify structure categorically, without scores or thresholds."""
        # Set unresolved_statuses to a set of item at 'regulatory_status' for item in graph at
        # 'unresolved_relations'.
        unresolved_statuses = {
            # Evaluate graph at 'unresolved_relations' as part of the enclosing expression.
            item["regulatory_status"] for item in graph["unresolved_relations"]
        }
        # Run this branch when the negation of source_consistent.
        if not source_consistent:
            # Return NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH to the caller.
            return NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH
        # Run this branch when 'regulatory_profile_mismatches' from graph; use None if absent.
        if graph.get("regulatory_profile_mismatches"):
            # Return NegotiationStatus.REGULATORY_PROFILE_MISMATCH to the caller.
            return NegotiationStatus.REGULATORY_PROFILE_MISMATCH
        # Run this branch when 'communicated_disagreements' from graph; use None if absent.
        if graph.get("communicated_disagreements"):
            # Return NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT to the caller.
            return NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT
        # Run this branch when the negation of active.
        if not active:
            # Return NegotiationStatus.NO_ACTIVE_CONFLICT to the caller.
            return NegotiationStatus.NO_ACTIVE_CONFLICT
        # Run this branch when the text 'REGULATORY_INPUT_UNRESOLVED' belongs to unresolved_statuses.
        if "REGULATORY_INPUT_UNRESOLVED" in unresolved_statuses:
            # Return NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED to the caller.
            return NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED
        # Run this branch when unresolved_statuses.
        if unresolved_statuses:
            # Return NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE to the caller.
            return NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE
        # Run this branch when graph at 'cycle_detected'.
        if graph["cycle_detected"]:
            # Return NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE to the caller.
            return NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE
        # Return NegotiationStatus.REGULATORY_ORDER_RESOLVED to the caller.
        return NegotiationStatus.REGULATORY_ORDER_RESOLVED

    # Count using the inputs and processing steps below.
    # Input snapshot: the supplied snapshot.
    # Output: no explicit value; normal completion returns None.
    def _count(self, snapshot):
        # Update self._totals['joint_local_negotiation_snapshots_built'] to its current value plus 1.
        self._totals["joint_local_negotiation_snapshots_built"] += 1
        # Update self._totals['snapshots_with_active_conflict_participants'] to its current value plus the number
        # of entries in snapshot.participant_ids is greater than 1.
        self._totals["snapshots_with_active_conflict_participants"] += len(snapshot.participant_ids) > 1
        # Update self._totals['messages_received_by_local_agents'] to its current value plus
        # snapshot.messages_received.
        self._totals["messages_received_by_local_agents"] += snapshot.messages_received
        # Update self._totals['messages_adopted_into_connected_components'] to its current value plus
        # snapshot.messages_adopted.
        self._totals["messages_adopted_into_connected_components"] += snapshot.messages_adopted
        # Update self._totals['unconnected_messages_ignored'] to its current value plus
        # snapshot.messages_ignored_unconnected.
        self._totals["unconnected_messages_ignored"] += snapshot.messages_ignored_unconnected
        # Update self._totals['duplicate_claims_merged'] to its current value plus
        # snapshot.duplicate_claims_merged.
        self._totals["duplicate_claims_merged"] += snapshot.duplicate_claims_merged
        # Update self._totals['communicated_precedence_disagreements'] to its current value plus the number of
        # entries in snapshot.communicated_disagreements.
        self._totals["communicated_precedence_disagreements"] += len(snapshot.communicated_disagreements)
        # Update self._totals['joint_precedence_edges'] to its current value plus the number of entries in
        # snapshot.joint_precedence_edges.
        self._totals["joint_precedence_edges"] += len(snapshot.joint_precedence_edges)
        # Update self._totals['joint_graphs_with_expanded_participant_sets'] to its current value plus the number
        # of entries in snapshot.participant_ids is greater than the number of entries in
        # snapshot.local_participant_ids.
        self._totals["joint_graphs_with_expanded_participant_sets"] += (
            # Evaluate the number of entries in snapshot.participant_ids is greater than the number of entries in
            # snapshot.local_participant_ids as part of the enclosing expression.
            len(snapshot.participant_ids) > len(snapshot.local_participant_ids)
        )
        # Update self._totals['strongly_connected_cyclic_components_observed'] to its current value plus the
        # number of entries in snapshot.strongly_connected_components.
        self._totals["strongly_connected_cyclic_components_observed"] += len(
            # Supply snapshot.strongly_connected_components to len.
            snapshot.strongly_connected_components
        )
        # Set self._totals['maximum_local_participants_before_v2v_expansion'] to the maximum of self._totals at
        # 'maximum_local_participants_before_v2v_expansion', the number of entries in...
        self._totals["maximum_local_participants_before_v2v_expansion"] = max(
            # Supply self._totals at 'maximum_local_participants_before_v2v_expansion' to max.
            self._totals["maximum_local_participants_before_v2v_expansion"],
            # Supply the number of entries in snapshot.local_participant_ids to max.
            len(snapshot.local_participant_ids),
        )
        # Set self._totals['maximum_joint_participants_after_v2v_expansion'] to the maximum of self._totals at
        # 'maximum_joint_participants_after_v2v_expansion', the number of entries in...
        self._totals["maximum_joint_participants_after_v2v_expansion"] = max(
            # Supply self._totals at 'maximum_joint_participants_after_v2v_expansion' to max.
            self._totals["maximum_joint_participants_after_v2v_expansion"],
            # Supply the number of entries in snapshot.participant_ids to max.
            len(snapshot.participant_ids),
        )
        # Update self._totals['regulatory_profile_mismatches'] to its current value plus the number of entries in
        # snapshot.regulatory_profile_mismatches.
        self._totals["regulatory_profile_mismatches"] += len(snapshot.regulatory_profile_mismatches)
        # Set mapping to a dictionary of the supplied entries.
        mapping = {
            # Store the text 'regulatory_order_resolved_snapshots' under
            # NegotiationStatus.REGULATORY_ORDER_RESOLVED.value.
            NegotiationStatus.REGULATORY_ORDER_RESOLVED.value: "regulatory_order_resolved_snapshots",
            # Store the text 'regulatory_cycle_snapshots' under
            # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value.
            NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value: "regulatory_cycle_snapshots",
            # Store the text 'unresolved_precedence_snapshots' under
            # NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value.
            NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value: "unresolved_precedence_snapshots",
            # Store the text 'unresolved_precedence_snapshots' under
            # NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value.
            NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value: "unresolved_precedence_snapshots",
            # Store the text 'no_active_conflict_snapshots' under NegotiationStatus.NO_ACTIVE_CONFLICT.value.
            NegotiationStatus.NO_ACTIVE_CONFLICT.value: "no_active_conflict_snapshots",
            # Store the text 'source_snapshot_mismatches' under NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value.
            NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value: "source_snapshot_mismatches",
            # Store the text 'unresolved_precedence_snapshots' under
            # NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value.
            NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value: "unresolved_precedence_snapshots",
            # Store the text 'unresolved_precedence_snapshots' under
            # NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value.
            NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value: "unresolved_precedence_snapshots",
        }
        # Update self._totals[mapping[snapshot.negotiation_status]] to its current value plus 1.
        self._totals[mapping[snapshot.negotiation_status]] += 1

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary built from self._totals.
    def validation_summary(self):
        # Return a dictionary built from self._totals to the caller.
        return dict(self._totals)

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()
