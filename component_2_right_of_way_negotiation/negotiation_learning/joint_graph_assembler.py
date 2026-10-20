"""Fixed-point assembly of one ego's connected joint precedence graph."""
# Import math for use in this module.
import math

# Import RegulatoryPrecedenceGraphBuilder from .precedence_graph for the operations below.
from .precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import same_instant from .v2v_claim_bus for the operations below.
from .v2v_claim_bus import same_instant


# Adopt only same-step claims connected to the ego's local component.
# Instances expose the attributes and methods implemented in this class.
class JointLocalPrecedenceGraphAssembler:
    """Adopt only same-step claims connected to the ego's local component."""

    # Set COMMUNICATION_MODEL to the text 'IDEAL_SAME_STEP_V2V'.
    COMMUNICATION_MODEL = "IDEAL_SAME_STEP_V2V"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input expected_profile: the supplied expected profile.
    # Input runtime_v2: the supplied runtime v2.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, expected_profile="DE_STVO_UNCONTROLLED_4WAY_V1", runtime_v2=False):
        # Set self.expected_profile to expected_profile.
        self.expected_profile = expected_profile
        # Set self.runtime_v2 to a Boolean built from runtime_v2.
        self.runtime_v2 = bool(runtime_v2)
        # Set self.analyser to RegulatoryPrecedenceGraphBuilder.
        self.analyser = RegulatoryPrecedenceGraphBuilder

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Key using the inputs and processing steps below.
    # Input item: the supplied item.
    # Output: a tuple containing item at 'yielding_vehicle_id', item at 'priority_vehicle_id'.
    def _key(item):
        # Return a tuple containing item at 'yielding_vehicle_id', item at 'priority_vehicle_id' to the caller.
        return item["yielding_vehicle_id"], item["priority_vehicle_id"]

    # Assemble using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input current_time: the supplied current time.
    # Input local_graph: the supplied local graph.
    # Input messages: the supplied messages.
    # Output: a dictionary containing ego_id, timestamp, communication_model, local_node_ids,
    # local_precedence_edges,...
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def assemble(self, ego_id, current_time, local_graph, messages):
        # Set local_nodes to a set built from local_graph at 'node_ids'.
        local_nodes = set(local_graph["node_ids"])
        # Set (valid, invalid_profile, invalid_source) to a tuple containing an empty list, an empty list, an
        # empty list.
        valid, invalid_profile, invalid_source = [], [], []
        # Iterate over messages, binding each item to message.
        for message in messages:
            # Run this branch when message.regulatory_profile differs from self.expected_profile.
            if message.regulatory_profile != self.expected_profile:
                # Append message to invalid_profile.
                invalid_profile.append(message)
            # Run this branch when the negation of the result of same_instant(current_time, message.timestamp,
            # message.source_conflict_graph_timestamp,...).
            elif not same_instant(
                    # Supply message.timestamp to same_instant.
                    current_time, message.timestamp,
                    # Supply message.source_conflict_graph_timestamp to same_instant.
                    message.source_conflict_graph_timestamp,
                    # Supply message.source_regulatory_assessment_timestamp to same_instant.
                    message.source_regulatory_assessment_timestamp):
                # Append message to invalid_source.
                invalid_source.append(message)
            # Run this branch when self.runtime_v2 and message.sender_id does not belong to a tuple containing
            # message.yielding_vehicle_id, message.priority_vehicle_id or the negation of
            # message.applicable_rule_ids or the negation of message.source_sections or the negation of
            # message.shared_conflict_zone_ids or the negation of the result of
            # set(message.applicable_rule_ids).issubset({'DE-STVO-8-1', 'DE-STVO-9-3', 'DE-STVO-9-4',
            # 'DE-STVO-11-3'}) or message.source_observation_age_seconds is the same object as None or the
            # negation of whether message.source_observation_age_seconds contains finite numeric values or
            # message.source_observation_age_seconds is less than 0 or message.negotiation_eligible_ambiguity and
            # set(message.applicable_rule_ids) differs from {'DE-STVO-11-3'}.
            elif self.runtime_v2 and (message.sender_id not in (
                    # Include message.yielding_vehicle_id in this tuple.
                    message.yielding_vehicle_id, message.priority_vehicle_id) or
                    # Evaluate the negation of message.applicable_rule_ids as part of the enclosing expression.
                    not message.applicable_rule_ids or not message.source_sections or
                    # Evaluate the negation of message.shared_conflict_zone_ids as part of the enclosing
                    # expression.
                    not message.shared_conflict_zone_ids or
                    # Evaluate the negation of the result of set(message.applicable_rule_ids).issubset(a set
                    # containing the text 'DE-STVO-8-1', the text 'DE-STVO-9-3', the text 'DE-STVO-9-4', the...)
                    # as part of the enclosing expression.
                    not set(message.applicable_rule_ids).issubset({"DE-STVO-8-1", "DE-STVO-9-3", "DE-STVO-9-4", "DE-STVO-11-3"}) or
                    # Evaluate message.source_observation_age_seconds is the same object as None as part of the
                    # enclosing expression.
                    message.source_observation_age_seconds is None or
                    # Evaluate the negation of whether message.source_observation_age_seconds contains finite
                    # numeric values as part of the enclosing expression.
                    not math.isfinite(message.source_observation_age_seconds) or
                    # Evaluate message.source_observation_age_seconds is less than 0 as part of the enclosing
                    # expression.
                    message.source_observation_age_seconds < 0 or
                    # Evaluate message.negotiation_eligible_ambiguity and a set built from
                    # message.applicable_rule_ids differs from a set containing the text 'DE-STVO-11-3' as part of
                    # the enclosing expression.
                    (message.negotiation_eligible_ambiguity and
                     # Evaluate a set built from message.applicable_rule_ids differs from a set containing the
                     # text 'DE-STVO-11-3' as part of the enclosing expression.
                     set(message.applicable_rule_ids) != {"DE-STVO-11-3"})):
                # Append message to invalid_source.
                invalid_source.append(message)
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Append message to valid.
                valid.append(message)

        # Set (adopted, relevant_nodes) to a tuple containing an empty set, a set built from local_nodes.
        adopted, relevant_nodes = set(), set(local_nodes)
        # Set changed to True.
        changed = True
        # Repeat the following steps while changed.
        while changed:
            # Set changed to False.
            changed = False
            # Iterate over index/value pairs from valid, binding each item to (position, message).
            for position, message in enumerate(valid):
                # Run this branch when position belongs to adopted.
                if position in adopted:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set endpoints to a set containing message.yielding_vehicle_id, message.priority_vehicle_id.
                endpoints = {message.yielding_vehicle_id, message.priority_vehicle_id}
                # Run this branch when endpoints intersected with relevant_nodes.
                if endpoints & relevant_nodes:
                    # Add position to adopted.
                    adopted.add(position)
                    # Set before to the number of entries in relevant_nodes.
                    before = len(relevant_nodes)
                    # Update relevant_nodes with the supplied entries.
                    relevant_nodes.update(endpoints)
                    # Set changed to True or the number of entries in relevant_nodes differs from before.
                    changed = True or len(relevant_nodes) != before

        # Set adopted_messages to a tuple built from a lazy sequence of valid at position for position in the
        # sorted values from adopted.
        adopted_messages = tuple(valid[position] for position in sorted(adopted))
        # Set profile_mismatches to a tuple built from a lazy sequence of the result of message.to_dict() for
        # message in invalid_profile; retain entries satisfying a set containing message.yielding_vehicle_id,
        # message.priority_vehicle_id intersected...
        profile_mismatches = tuple(
            # Evaluate the result of message.to_dict() as part of the enclosing expression.
            message.to_dict() for message in invalid_profile
            # Evaluate a set containing message.yielding_vehicle_id, message.priority_vehicle_id intersected with
            # relevant_nodes as part of the enclosing expression.
            if {message.yielding_vehicle_id, message.priority_vehicle_id}
            # Evaluate relevant_nodes as part of the enclosing expression.
            & relevant_nodes
        )
        # Set source_mismatches to a tuple built from a lazy sequence of the result of message.to_dict() for
        # message in invalid_source; retain entries satisfying a set containing message.yielding_vehicle_id,
        # message.priority_vehicle_id intersected...
        source_mismatches = tuple(
            # Evaluate the result of message.to_dict() as part of the enclosing expression.
            message.to_dict() for message in invalid_source
            # Evaluate a set containing message.yielding_vehicle_id, message.priority_vehicle_id intersected with
            # relevant_nodes as part of the enclosing expression.
            if {message.yielding_vehicle_id, message.priority_vehicle_id}
            # Evaluate relevant_nodes as part of the enclosing expression.
            & relevant_nodes
        )
        # Set ignored to a tuple built from a lazy sequence of the result of valid[position].to_dict() for
        # position in the integer range defined by the number of entries in valid; retain entries satisfying
        # position does not belong to adopted.
        ignored = tuple(valid[position].to_dict() for position in range(len(valid))
                        # Evaluate position does not belong to adopted as part of the enclosing expression.
                        if position not in adopted)
        # Set edge_support to an empty dictionary.
        edge_support = {}
        # Iterate over local_graph at 'precedence_edges', binding each item to edge.
        for edge in local_graph["precedence_edges"]:
            # Set normalized to a dictionary built from edge.
            normalized = dict(edge)
            # Set normalized['edge_origin'] to the text 'LOCAL'.
            normalized["edge_origin"] = "LOCAL"
            # Set normalized['supporting_sender_ids'] to a tuple containing ego_id.
            normalized["supporting_sender_ids"] = (ego_id,)
            # Set edge_support[self._key(normalized)] to normalized.
            edge_support[self._key(normalized)] = normalized
        # Set duplicate_claims to 0.
        duplicate_claims = 0
        # Set communicated_keys to an empty set.
        communicated_keys = set()
        # Iterate over adopted_messages, binding each item to message.
        for message in adopted_messages:
            # Set key to a tuple containing message.yielding_vehicle_id, message.priority_vehicle_id.
            key = (message.yielding_vehicle_id, message.priority_vehicle_id)
            # Add key to communicated_keys.
            communicated_keys.add(key)
            # Run this branch when key belongs to edge_support.
            if key in edge_support:
                # Update duplicate_claims to its current value plus 1.
                duplicate_claims += 1
                # Set edge to edge_support at key.
                edge = edge_support[key]
                # Set edge['supporting_sender_ids'] to a tuple built from the sorted values from a set built from
                # edge['supporting_sender_ids'] combined with a set containing message.sender_id.
                edge["supporting_sender_ids"] = tuple(sorted(
                    # Supply a set built from edge at 'supporting_sender_ids' combined with a set containing
                    # message.sender_id to sorted.
                    set(edge["supporting_sender_ids"]) | {message.sender_id}
                ))
                # Run this branch when edge at 'edge_origin' equals the text 'LOCAL'.
                if edge["edge_origin"] == "LOCAL":
                    # Set edge['edge_origin'] to the text 'LOCAL_AND_COMMUNICATED'.
                    edge["edge_origin"] = "LOCAL_AND_COMMUNICATED"
                # Run this branch when self.runtime_v2 and the negation of message.negotiation_eligible_ambiguity.
                if self.runtime_v2 and not message.negotiation_eligible_ambiguity:
                    # Set edge['hard_constraint_evidence'] to a dictionary built from 'hard_constraint_evidence'
                    # from edge; use an empty dictionary if absent.
                    edge["hard_constraint_evidence"] = dict(
                        # Supply 'hard_constraint_evidence' from edge; use an empty dictionary if absent to dict.
                        edge.get("hard_constraint_evidence", {}),
                        # Supply mandatory_regulatory_yield as True.
                        mandatory_regulatory_yield=True,
                        # Supply negotiation_eligible_ambiguity as False.
                        negotiation_eligible_ambiguity=False)
                # Iterate over a tuple containing a tuple containing the text 'applicable_rule_ids',
                # message.applicable_rule_ids, a tuple containing the..., binding each item to (field, values).
                for field, values in (
                    # Include a tuple containing the text 'applicable_rule_ids', message.applicable_rule_ids in
                    # this tuple.
                    ("applicable_rule_ids", message.applicable_rule_ids),
                    # Include a tuple containing the text 'source_sections', message.source_sections in this
                    # tuple.
                    ("source_sections", message.source_sections),
                    # Include a tuple containing the text 'shared_conflict_zone_ids',
                    # message.shared_conflict_zone_ids in this tuple.
                    ("shared_conflict_zone_ids", message.shared_conflict_zone_ids),
                    # Include a tuple containing the text 'conflict_types', message.conflict_types in this tuple.
                    ("conflict_types", message.conflict_types),
                    # Include a tuple containing the text 'target_candidate_path_ids',
                    # message.target_candidate_path_ids in this tuple.
                    ("target_candidate_path_ids", message.target_candidate_path_ids),
                ):
                    # Set edge[field] to a tuple built from the sorted values from a set built from
                    # edge.get(field, ()) combined with a set built from values.
                    edge[field] = tuple(sorted(
                        # Supply a set built from field from edge; use an empty tuple if absent combined with a
                        # set built from values to sorted.
                        set(edge.get(field, ())) | set(values)
                    ))
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set edge_support[key] to the result of self._message_edge(message).
                edge_support[key] = self._message_edge(message)

        # Set joint_edges to a tuple built from the sorted values from values from edge_support.
        joint_edges = tuple(sorted(edge_support.values(), key=self._key))
        # Set communicated_edges to a tuple built from a lazy sequence of edge for edge in joint_edges; retain
        # entries satisfying the result of self._key(edge) belongs to communicated_keys.
        communicated_edges = tuple(
            # Evaluate the result of self._key(edge) belongs to communicated_keys as part of the enclosing
            # expression.
            edge for edge in joint_edges if self._key(edge) in communicated_keys
        )
        # Set disagreements to an empty list.
        disagreements = []
        # Set eligible_ambiguities to an empty list.
        eligible_ambiguities = []
        # Set reconciliation_keys to a set built from edge_support when self.runtime_v2, otherwise
        # communicated_keys.
        reconciliation_keys = set(edge_support) if self.runtime_v2 else communicated_keys
        # Iterate over the sorted values from reconciliation_keys, binding each item to (first, second).
        for first, second in sorted(reconciliation_keys):
            # Run this branch when a tuple containing second, first belongs to reconciliation_keys and first is
            # less than second.
            if (second, first) in reconciliation_keys and first < second:
                # Set pair_edges to a tuple containing edge_support at (first, second), edge_support at (second,
                # first).
                pair_edges = (edge_support[(first, second)], edge_support[(second, first)])
                # Set soft_pair to self.runtime_v2 and whether every item is true in a lazy sequence of
                # 'negotiation_eligible_ambiguity' from e.get('hard_constraint_evidence', {}); use False if absent
                # for e in pair_edges.
                soft_pair = self.runtime_v2 and all(e.get("hard_constraint_evidence", {}).get(
                    # Evaluate pair_edges as part of the enclosing expression.
                    "negotiation_eligible_ambiguity", False) for e in pair_edges)
                # Run this branch when soft_pair.
                if soft_pair:
                    # Append a tuple containing first, second to eligible_ambiguities.
                    eligible_ambiguities.append((first, second))
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Append a dictionary containing diagnostic, vehicle_pair, directed_claims to disagreements.
                disagreements.append({
                    "diagnostic": "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
                    # Store a tuple containing first, second under 'vehicle_pair'.
                    "vehicle_pair": (first, second),
                    # Store a tuple containing a tuple containing first, second, a tuple containing second, first
                    # under 'directed_claims'.
                    "directed_claims": ((first, second), (second, first)),
                })
        # Set analysis to the result of self.analyser.analyse(a tuple built from the sorted values from
        # relevant_nodes, joint_edges).
        analysis = self.analyser.analyse(tuple(sorted(relevant_nodes)), joint_edges)
        # Return a dictionary containing ego_id, timestamp, communication_model, local_node_ids,
        # local_precedence_edges,... to the caller.
        return {
            # Store ego_id under 'ego_id'.
            # Store a floating-point number built from current_time under 'timestamp'.
            "ego_id": ego_id, "timestamp": float(current_time),
            # Store self.COMMUNICATION_MODEL under 'communication_model'.
            "communication_model": self.COMMUNICATION_MODEL,
            # Store local_graph at 'node_ids' under 'local_node_ids'.
            "local_node_ids": local_graph["node_ids"],
            # Store local_graph at 'precedence_edges' under 'local_precedence_edges'.
            "local_precedence_edges": local_graph["precedence_edges"],
            # Store the number of entries in messages under 'received_claim_count'.
            "received_claim_count": len(messages),
            # Store a tuple built from a lazy sequence of the result of message.to_dict() for message in
            # adopted_messages under 'adopted_communicated_claims'.
            "adopted_communicated_claims": tuple(
                # Evaluate the result of message.to_dict() as part of the enclosing expression.
                message.to_dict() for message in adopted_messages
            ),
            # Store communicated_edges under 'communicated_precedence_edges'.
            "communicated_precedence_edges": communicated_edges,
            # Store ignored under 'ignored_unconnected_claims'.
            "ignored_unconnected_claims": ignored,
            # Store a tuple built from the sorted values from relevant_nodes under 'joint_node_ids'.
            "joint_node_ids": tuple(sorted(relevant_nodes)),
            # Store joint_edges under 'joint_precedence_edges'.
            "joint_precedence_edges": joint_edges,
            # Store local_graph at 'unresolved_relations' under 'unresolved_relations'.
            "unresolved_relations": local_graph["unresolved_relations"],
            # Store a tuple built from disagreements under 'communicated_disagreements'.
            "communicated_disagreements": tuple(disagreements),
            # Store a tuple built from eligible_ambiguities under 'negotiation_eligible_ambiguities'.
            "negotiation_eligible_ambiguities": tuple(eligible_ambiguities),
            # Store profile_mismatches under 'regulatory_profile_mismatches'.
            "regulatory_profile_mismatches": profile_mismatches,
            # Store source_mismatches under 'source_snapshot_mismatches'.
            "source_snapshot_mismatches": source_mismatches,
            # Store duplicate_claims under 'duplicate_claims_merged'.
            "duplicate_claims_merged": duplicate_claims,
            # Evaluate analysis as part of the enclosing expression.
            **analysis,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Message edge using the inputs and processing steps below.
    # Input message: the supplied message.
    # Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
    # source_sections,...
    def _message_edge(message):
        # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
        # source_sections,... to the caller.
        return {
            # Store message.yielding_vehicle_id under 'yielding_vehicle_id'.
            "yielding_vehicle_id": message.yielding_vehicle_id,
            # Store message.priority_vehicle_id under 'priority_vehicle_id'.
            "priority_vehicle_id": message.priority_vehicle_id,
            # Store message.applicable_rule_ids under 'applicable_rule_ids'.
            "applicable_rule_ids": message.applicable_rule_ids,
            # Store message.source_sections under 'source_sections'.
            "source_sections": message.source_sections,
            # Store message.regulatory_profile under 'regulatory_profile'.
            "regulatory_profile": message.regulatory_profile,
            # Store message.target_candidate_path_ids under 'target_candidate_path_ids'.
            "target_candidate_path_ids": message.target_candidate_path_ids,
            # Store an empty tuple under 'relative_approaches'.
            # Store message.timestamp under 'timestamp'.
            "relative_approaches": (), "timestamp": message.timestamp,
            # Store message.shared_conflict_zone_ids under 'shared_conflict_zone_ids'.
            "shared_conflict_zone_ids": message.shared_conflict_zone_ids,
            # Store message.conflict_types under 'conflict_types'.
            "conflict_types": message.conflict_types,
            # Store True under 'spatial_conflict_possible'.
            "spatial_conflict_possible": True,
            # Store a dictionary containing mandatory_regulatory_yield, physical_candidate_conflict,
            # negotiation_eligible_ambiguity under 'hard_constraint_evidence'.
            "hard_constraint_evidence": {
                # Store the negation of message.negotiation_eligible_ambiguity under 'mandatory_regulatory_yield'.
                "mandatory_regulatory_yield": not message.negotiation_eligible_ambiguity,
                # Store True under 'physical_candidate_conflict'.
                "physical_candidate_conflict": True,
                # Store message.negotiation_eligible_ambiguity under 'negotiation_eligible_ambiguity'.
                "negotiation_eligible_ambiguity": message.negotiation_eligible_ambiguity,
            },
            # Store None under 'physical_reachability_evidence'.
            "physical_reachability_evidence": None,
            "edge_origin": "COMMUNICATED",
            # Store a tuple containing message.sender_id under 'supporting_sender_ids'.
            "supporting_sender_ids": (message.sender_id,),
            # Store message.source_observation_age_seconds under 'source_observation_age_seconds'.
            "source_observation_age_seconds": message.source_observation_age_seconds,
        }
