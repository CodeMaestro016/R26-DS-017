"""Pure-data semantic graph observation; no tensor encoding or learning."""

from .models import GraphObservation


class GraphObservationBuilder:
    """Separate hard authority from optional future learning information."""

    NODE_SCHEMA = (
        "is_ego", "speed_mps", "max_acceleration_mps2",
        "comfortable_deceleration_mps2", "max_speed_mps",
        "observation_confidence", "is_currently_observed",
        "observation_age_seconds",
    )
    EDGE_SCHEMA = (
        "yielding_vehicle_id", "priority_vehicle_id", "applicable_rule_ids",
        "source_sections", "relative_approaches", "conflict_types",
        "shared_conflict_zone_ids", "target_candidate_path_ids",
        "physical_reachability_evidence", "edge_origin",
    )

    def build(self, ldm, current_time, graph):
        node_ids = graph.get("joint_node_ids", graph.get("node_ids", ()))
        index = {node_id: position for position, node_id in enumerate(node_ids)}
        node_features = []
        for node_id in node_ids:
            track = ldm.tracks.get(node_id, {})
            last_observed = track.get("last_observed_time")
            node_features.append({
                "is_ego": node_id == ldm.ego_id,
                "speed_mps": track.get("speed"),
                "max_acceleration_mps2": track.get("max_acceleration_mps2"),
                "comfortable_deceleration_mps2": track.get("comfortable_deceleration_mps2"),
                "max_speed_mps": track.get("max_speed_mps"),
                "observation_confidence": track.get("confidence"),
                "is_currently_observed": track.get("is_observed"),
                "observation_age_seconds": (
                    None if last_observed is None
                    else max(0.0, float(current_time) - float(last_observed))
                ),
            })
        edges = graph.get("joint_precedence_edges", graph.get("precedence_edges", ()))
        return GraphObservation(
            ldm.ego_id, node_ids, tuple(node_features),
            tuple((index[item["yielding_vehicle_id"]],
                   index[item["priority_vehicle_id"]]) for item in edges),
            tuple({name: item.get(name) for name in self.EDGE_SCHEMA}
                  for item in edges),
            {
                "precedence_edges": edges,
                "unresolved_relations": graph["unresolved_relations"],
                "cycle_detected": graph["cycle_detected"],
            },
            {
                "node_feature_schema": self.NODE_SCHEMA,
                "candidate_efficiency_features_are_non_authoritative": True,
            },
            {
                "edge_direction": "YIELDING_VEHICLE_TO_PRIORITY_VEHICLE",
                "graph_scope": "JOINT_LOCAL_V2V",
                "communication_model": "IDEAL_SAME_STEP_V2V",
                "node_feature_schema": self.NODE_SCHEMA,
                "edge_feature_schema": self.EDGE_SCHEMA,
                "tensor_encoding_status": "NOT_IMPLEMENTED",
            },
        )
