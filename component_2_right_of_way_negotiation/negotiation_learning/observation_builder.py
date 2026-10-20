"""Pure-data semantic graph observation; no tensor encoding or learning."""

# Import GraphObservation from .models for the operations below.
from .models import GraphObservation


# Separate hard authority from optional future learning information.
# Instances expose the attributes and methods implemented in this class.
class GraphObservationBuilder:
    """Separate hard authority from optional future learning information."""

    # Set NODE_SCHEMA to a tuple containing the text 'is_ego', the text 'speed_mps', the text
    # 'max_acceleration_mps2', the text...
    NODE_SCHEMA = (
        "is_ego", "speed_mps", "max_acceleration_mps2",
        "comfortable_deceleration_mps2", "max_speed_mps",
        "observation_confidence", "is_currently_observed",
        "observation_age_seconds",
    )
    # Set EDGE_SCHEMA to a tuple containing the text 'yielding_vehicle_id', the text 'priority_vehicle_id', the
    # text 'applicable_rule_ids', the text...
    EDGE_SCHEMA = (
        "yielding_vehicle_id", "priority_vehicle_id", "applicable_rule_ids",
        "source_sections", "relative_approaches", "conflict_types",
        "shared_conflict_zone_ids", "target_candidate_path_ids",
        "physical_reachability_evidence", "edge_origin",
    )

    # Build using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Input graph: the supplied graph.
    # Output: the result of GraphObservation(ldm.ego_id, node_ids, a tuple built from node_features, a tuple built
    # from a lazy sequence of a...).
    # Processing: iterate over the relevant records.
    def build(self, ldm, current_time, graph):
        # Set node_ids to 'joint_node_ids' from graph; use 'node_ids' from graph; use an empty tuple if absent if
        # absent.
        node_ids = graph.get("joint_node_ids", graph.get("node_ids", ()))
        # Set index to a dictionary of node_id mapped to position for (position, node_id) in index/value pairs
        # from node_ids.
        index = {node_id: position for position, node_id in enumerate(node_ids)}
        # Set node_features to an empty list.
        node_features = []
        # Iterate over node_ids, binding each item to node_id.
        for node_id in node_ids:
            # Set track to node_id from ldm.tracks; use an empty dictionary if absent.
            track = ldm.tracks.get(node_id, {})
            # Set last_observed to 'last_observed_time' from track; use None if absent.
            last_observed = track.get("last_observed_time")
            # Append a dictionary containing is_ego, speed_mps, max_acceleration_mps2,
            # comfortable_deceleration_mps2,... to node_features.
            node_features.append({
                # Store node_id equals ldm.ego_id under 'is_ego'.
                "is_ego": node_id == ldm.ego_id,
                # Store 'speed' from track; use None if absent under 'speed_mps'.
                "speed_mps": track.get("speed"),
                # Store 'max_acceleration_mps2' from track; use None if absent under 'max_acceleration_mps2'.
                "max_acceleration_mps2": track.get("max_acceleration_mps2"),
                # Store 'comfortable_deceleration_mps2' from track; use None if absent under
                # 'comfortable_deceleration_mps2'.
                "comfortable_deceleration_mps2": track.get("comfortable_deceleration_mps2"),
                # Store 'max_speed_mps' from track; use None if absent under 'max_speed_mps'.
                "max_speed_mps": track.get("max_speed_mps"),
                # Store 'confidence' from track; use None if absent under 'observation_confidence'.
                "observation_confidence": track.get("confidence"),
                # Store 'is_observed' from track; use None if absent under 'is_currently_observed'.
                "is_currently_observed": track.get("is_observed"),
                # Store None when last_observed is the same object as None, otherwise the maximum of 0.0, a
                # floating-point number built from current_time minus a floating-point number built from... under
                # 'observation_age_seconds'.
                "observation_age_seconds": (
                    # Evaluate None when last_observed is the same object as None, otherwise the maximum of 0.0, a
                    # floating-point number built from current_time minus a floating-point number built from... as
                    # part of the enclosing expression.
                    None if last_observed is None
                    # Evaluate the maximum of 0.0, a floating-point number built from current_time minus a
                    # floating-point number built from... as part of the enclosing expression.
                    else max(0.0, float(current_time) - float(last_observed))
                ),
            })
        # Set edges to 'joint_precedence_edges' from graph; use 'precedence_edges' from graph; use an empty tuple
        # if absent if absent.
        edges = graph.get("joint_precedence_edges", graph.get("precedence_edges", ()))
        # Return the result of GraphObservation(ldm.ego_id, node_ids, a tuple built from node_features, a tuple
        # built from a lazy sequence of a...) to the caller.
        return GraphObservation(
            # Supply a tuple built from node_features to GraphObservation.
            ldm.ego_id, node_ids, tuple(node_features),
            # Supply a tuple built from a lazy sequence of a tuple containing index at
            # item['yielding_vehicle_id'], index at item['priority_vehicle_id'] for item in edges to
            # GraphObservation.
            tuple((index[item["yielding_vehicle_id"]],
                   # Include index at item['priority_vehicle_id'] in this tuple.
                   index[item["priority_vehicle_id"]]) for item in edges),
            # Supply a tuple built from a lazy sequence of a dictionary of name mapped to name from item; use None
            # if absent for name in self.EDGE_SCHEMA for item in edges to GraphObservation.
            tuple({name: item.get(name) for name in self.EDGE_SCHEMA}
                  # Evaluate edges as part of the enclosing expression.
                  for item in edges),
            # Supply a dictionary containing precedence_edges, unresolved_relations, cycle_detected to
            # GraphObservation.
            {
                # Store edges under 'precedence_edges'.
                "precedence_edges": edges,
                # Store graph at 'unresolved_relations' under 'unresolved_relations'.
                "unresolved_relations": graph["unresolved_relations"],
                # Store graph at 'cycle_detected' under 'cycle_detected'.
                "cycle_detected": graph["cycle_detected"],
            },
            # Supply a dictionary containing node_feature_schema,
            # candidate_efficiency_features_are_non_authoritative to GraphObservation.
            {
                # Store self.NODE_SCHEMA under 'node_feature_schema'.
                "node_feature_schema": self.NODE_SCHEMA,
                # Store True under 'candidate_efficiency_features_are_non_authoritative'.
                "candidate_efficiency_features_are_non_authoritative": True,
            },
            # Supply a dictionary containing edge_direction, graph_scope, communication_model,
            # node_feature_schema,... to GraphObservation.
            {
                "edge_direction": "YIELDING_VEHICLE_TO_PRIORITY_VEHICLE",
                "graph_scope": "JOINT_LOCAL_V2V",
                "communication_model": "IDEAL_SAME_STEP_V2V",
                # Store self.NODE_SCHEMA under 'node_feature_schema'.
                "node_feature_schema": self.NODE_SCHEMA,
                # Store self.EDGE_SCHEMA under 'edge_feature_schema'.
                "edge_feature_schema": self.EDGE_SCHEMA,
                "tensor_encoding_status": "NOT_IMPLEMENTED",
            },
        )
