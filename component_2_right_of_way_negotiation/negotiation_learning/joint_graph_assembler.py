"""Fixed-point assembly of one ego's connected joint precedence graph."""

from .precedence_graph import RegulatoryPrecedenceGraphBuilder
from .v2v_claim_bus import same_instant


class JointLocalPrecedenceGraphAssembler:
    """Adopt only same-step claims connected to the ego's local component."""

    COMMUNICATION_MODEL = "IDEAL_SAME_STEP_V2V"

    def __init__(self, expected_profile="DE_STVO_UNCONTROLLED_4WAY_V1"):
        self.expected_profile = expected_profile
        self.analyser = RegulatoryPrecedenceGraphBuilder

    @staticmethod
    def _key(item):
        return item["yielding_vehicle_id"], item["priority_vehicle_id"]

    def assemble(self, ego_id, current_time, local_graph, messages):
        local_nodes = set(local_graph["node_ids"])
        valid, invalid_profile, invalid_source = [], [], []
        for message in messages:
            if message.regulatory_profile != self.expected_profile:
                invalid_profile.append(message)
            elif not same_instant(
                    current_time, message.timestamp,
                    message.source_conflict_graph_timestamp,
                    message.source_regulatory_assessment_timestamp):
                invalid_source.append(message)
            else:
                valid.append(message)

        adopted, relevant_nodes = set(), set(local_nodes)
        changed = True
        while changed:
            changed = False
            for position, message in enumerate(valid):
                if position in adopted:
                    continue
                endpoints = {message.yielding_vehicle_id, message.priority_vehicle_id}
                if endpoints & relevant_nodes:
                    adopted.add(position)
                    before = len(relevant_nodes)
                    relevant_nodes.update(endpoints)
                    changed = True or len(relevant_nodes) != before

        adopted_messages = tuple(valid[position] for position in sorted(adopted))
        profile_mismatches = tuple(
            message.to_dict() for message in invalid_profile
            if {message.yielding_vehicle_id, message.priority_vehicle_id}
            & relevant_nodes
        )
        source_mismatches = tuple(
            message.to_dict() for message in invalid_source
            if {message.yielding_vehicle_id, message.priority_vehicle_id}
            & relevant_nodes
        )
        ignored = tuple(valid[position].to_dict() for position in range(len(valid))
                        if position not in adopted)
        edge_support = {}
        for edge in local_graph["precedence_edges"]:
            normalized = dict(edge)
            normalized["edge_origin"] = "LOCAL"
            normalized["supporting_sender_ids"] = (ego_id,)
            edge_support[self._key(normalized)] = normalized
        duplicate_claims = 0
        communicated_keys = set()
        for message in adopted_messages:
            key = (message.yielding_vehicle_id, message.priority_vehicle_id)
            communicated_keys.add(key)
            if key in edge_support:
                duplicate_claims += 1
                edge = edge_support[key]
                edge["supporting_sender_ids"] = tuple(sorted(
                    set(edge["supporting_sender_ids"]) | {message.sender_id}
                ))
                if edge["edge_origin"] == "LOCAL":
                    edge["edge_origin"] = "LOCAL_AND_COMMUNICATED"
                for field, values in (
                    ("applicable_rule_ids", message.applicable_rule_ids),
                    ("source_sections", message.source_sections),
                    ("shared_conflict_zone_ids", message.shared_conflict_zone_ids),
                    ("conflict_types", message.conflict_types),
                    ("target_candidate_path_ids", message.target_candidate_path_ids),
                ):
                    edge[field] = tuple(sorted(
                        set(edge.get(field, ())) | set(values)
                    ))
            else:
                edge_support[key] = self._message_edge(message)

        joint_edges = tuple(sorted(edge_support.values(), key=self._key))
        communicated_edges = tuple(
            edge for edge in joint_edges if self._key(edge) in communicated_keys
        )
        disagreements = []
        for first, second in sorted(communicated_keys):
            if (second, first) in communicated_keys and first < second:
                disagreements.append({
                    "diagnostic": "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
                    "vehicle_pair": (first, second),
                    "directed_claims": ((first, second), (second, first)),
                })
        analysis = self.analyser.analyse(tuple(sorted(relevant_nodes)), joint_edges)
        return {
            "ego_id": ego_id, "timestamp": float(current_time),
            "communication_model": self.COMMUNICATION_MODEL,
            "local_node_ids": local_graph["node_ids"],
            "local_precedence_edges": local_graph["precedence_edges"],
            "received_claim_count": len(messages),
            "adopted_communicated_claims": tuple(
                message.to_dict() for message in adopted_messages
            ),
            "communicated_precedence_edges": communicated_edges,
            "ignored_unconnected_claims": ignored,
            "joint_node_ids": tuple(sorted(relevant_nodes)),
            "joint_precedence_edges": joint_edges,
            "unresolved_relations": local_graph["unresolved_relations"],
            "communicated_disagreements": tuple(disagreements),
            "regulatory_profile_mismatches": profile_mismatches,
            "source_snapshot_mismatches": source_mismatches,
            "duplicate_claims_merged": duplicate_claims,
            **analysis,
        }

    @staticmethod
    def _message_edge(message):
        return {
            "yielding_vehicle_id": message.yielding_vehicle_id,
            "priority_vehicle_id": message.priority_vehicle_id,
            "applicable_rule_ids": message.applicable_rule_ids,
            "source_sections": message.source_sections,
            "regulatory_profile": message.regulatory_profile,
            "target_candidate_path_ids": message.target_candidate_path_ids,
            "relative_approaches": (), "timestamp": message.timestamp,
            "shared_conflict_zone_ids": message.shared_conflict_zone_ids,
            "conflict_types": message.conflict_types,
            "spatial_conflict_possible": True,
            "hard_constraint_evidence": {
                "mandatory_regulatory_yield": True,
                "physical_candidate_conflict": True,
            },
            "physical_reachability_evidence": None,
            "edge_origin": "COMMUNICATED",
            "supporting_sender_ids": (message.sender_id,),
            "source_observation_age_seconds": message.source_observation_age_seconds,
        }
