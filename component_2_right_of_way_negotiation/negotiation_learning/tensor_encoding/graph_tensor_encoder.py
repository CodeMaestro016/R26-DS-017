"""Convert semantic joint graphs to finite, masked NumPy arrays."""

import math

import numpy as np

from .models import EncodedGraphObservation
from .schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA,
    EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA,
    RELATIVE_APPROACH_CATEGORIES,
)


class GraphTensorEncodingError(ValueError):
    """Deterministic validation failure for invalid semantic input."""


class GraphTensorEncoder:
    """Stateless NumPy encoder with no learned parameters or normalization."""

    NORMALIZATION_STATUS = "NOT_FITTED_TRAINING_STATISTICS_REQUIRED"
    TENSOR_BACKEND = "NUMPY"

    def __init__(self):
        self._totals = self._empty_totals()

    @staticmethod
    def _empty_totals():
        return {
            "encoded_graph_observations_built": 0,
            "maximum_encoded_nodes": 0,
            "maximum_encoded_directed_edges": 0,
            "encoded_graphs_with_zero_edges": 0,
            "encoded_graphs_with_communicated_only_participants": 0,
            "missing_node_scalar_values_masked": 0,
            "missing_edge_scalar_values_masked": 0,
            "nonfinite_available_feature_errors": 0,
            "route_truth_fields_consumed": 0,
            "arbitrary_ordinal_categorical_encodings": 0,
            "tensorflow_dependencies_introduced": 0,
            "pytorch_dependencies_introduced": 0,
            "control_actions_issued_by_tensor_encoder": 0,
        }

    @staticmethod
    def _scalar(value, field):
        if value is None:
            return 0.0, False
        if isinstance(value, (bool, np.bool_)):
            return float(bool(value)), True
        try:
            numeric = float(value)
        except (TypeError, ValueError) as error:
            raise GraphTensorEncodingError(
                f"INVALID_AVAILABLE_FEATURE:{field}"
            ) from error
        if not math.isfinite(numeric):
            raise GraphTensorEncodingError(
                f"NONFINITE_AVAILABLE_FEATURE:{field}"
            )
        return numeric, True

    @staticmethod
    def _categorical(values, categories, field, multi):
        if values is None or values == () or values == []:
            return [0.0] * len(categories), [False] * len(categories)
        members = (values,) if isinstance(values, str) else tuple(values)
        unknown = set(members) - set(categories)
        if unknown or (not multi and len(set(members)) != 1):
            raise GraphTensorEncodingError(
                f"UNKNOWN_OR_INVALID_CATEGORY:{field}:{sorted(unknown)}"
            )
        return (
            [float(category in members) for category in categories],
            [True] * len(categories),
        )

    def encode(self, graph_observation):
        observation = (
            graph_observation.to_dict()
            if hasattr(graph_observation, "to_dict") else graph_observation
        )
        original_node_ids = tuple(observation.get("node_ids", ()))
        original_node_features = tuple(observation.get("node_features", ()))
        if len(original_node_ids) != len(original_node_features):
            raise GraphTensorEncodingError("NODE_ID_FEATURE_COUNT_MISMATCH")
        features_by_id = dict(zip(original_node_ids, original_node_features))
        node_ids = tuple(sorted(original_node_ids))
        node_rows, node_masks = [], []
        try:
            for node_id in node_ids:
                row, mask = zip(*(
                    self._scalar(features_by_id[node_id].get(field), field)
                    for field in NODE_NUMERIC_SCHEMA
                ))
                node_rows.append(row)
                node_masks.append(mask)

            semantic_edges = tuple(observation.get("edge_features", ()))
            semantic_edges = tuple(sorted(semantic_edges, key=lambda item: (
                item["yielding_vehicle_id"], item["priority_vehicle_id"]
            )))
            node_index = {node_id: index for index, node_id in enumerate(node_ids)}
            edge_indices, edge_rows, edge_masks, edge_identifiers = [], [], [], []
            for edge in semantic_edges:
                yielding, priority = (
                    edge["yielding_vehicle_id"], edge["priority_vehicle_id"]
                )
                if yielding not in node_index or priority not in node_index:
                    raise GraphTensorEncodingError("EDGE_ENDPOINT_NOT_IN_NODE_IDS")
                edge_indices.append((node_index[yielding], node_index[priority]))
                origin_values, origin_mask = self._categorical(
                    edge.get("edge_origin"), EDGE_ORIGIN_CATEGORIES,
                    "edge_origin", multi=False,
                )
                relation_values, relation_mask = self._categorical(
                    edge.get("relative_approaches"), RELATIVE_APPROACH_CATEGORIES,
                    "relative_approaches", multi=True,
                )
                physical = edge.get("physical_reachability_evidence")
                temporal = (
                    physical.get("temporal_conflict_possible")
                    if isinstance(physical, dict) else None
                )
                temporal_value, temporal_mask = self._scalar(
                    temporal, "temporal_conflict_possible"
                )
                edge_rows.append(tuple(origin_values + relation_values + [
                    float(physical is not None), temporal_value,
                ]))
                edge_masks.append(tuple(origin_mask + relation_mask + [
                    True, temporal_mask,
                ]))
                edge_identifiers.append({
                    "yielding_vehicle_id": yielding,
                    "priority_vehicle_id": priority,
                    "applicable_rule_ids": tuple(edge.get("applicable_rule_ids", ())),
                    "source_sections": tuple(edge.get("source_sections", ())),
                    "regulatory_profile": edge.get("regulatory_profile"),
                    "shared_conflict_zone_ids": tuple(edge.get("shared_conflict_zone_ids", ())),
                    "target_candidate_path_ids": tuple(edge.get("target_candidate_path_ids", ())),
                    "conflict_types": tuple(edge.get("conflict_types", ())),
                    "deferred_physical_reachability_evidence": physical,
                })
        except GraphTensorEncodingError as error:
            if str(error).startswith("NONFINITE_AVAILABLE_FEATURE"):
                self._totals["nonfinite_available_feature_errors"] += 1
            raise

        node_array = np.asarray(node_rows, dtype=np.float32).reshape(
            len(node_ids), len(NODE_NUMERIC_SCHEMA)
        )
        node_mask = np.asarray(node_masks, dtype=np.bool_).reshape(node_array.shape)
        edge_array = np.asarray(edge_rows, dtype=np.float32).reshape(
            len(edge_rows), len(EDGE_NUMERIC_SCHEMA)
        )
        edge_mask = np.asarray(edge_masks, dtype=np.bool_).reshape(edge_array.shape)
        edge_index = np.asarray(edge_indices, dtype=np.int64).reshape(-1, 2).T
        if not all(np.isfinite(array).all() for array in (node_array, edge_array)):
            self._totals["nonfinite_available_feature_errors"] += 1
            raise GraphTensorEncodingError("NONFINITE_AVAILABLE_FEATURE")

        metadata = observation.get("metadata", {})
        encoded = EncodedGraphObservation(
            observation["ego_id"], node_ids, node_array, node_mask,
            edge_index, edge_array, edge_mask, NODE_NUMERIC_SCHEMA,
            EDGE_NUMERIC_SCHEMA, dict(CATEGORICAL_ENCODING_METADATA),
            dict(observation.get("hard_constraint_evidence", {})),
            {"edge_identifiers": tuple(edge_identifiers)},
            metadata.get("graph_scope", "JOINT_LOCAL_V2V"),
            metadata.get("communication_model", "IDEAL_SAME_STEP_V2V"),
            self.NORMALIZATION_STATUS, self.TENSOR_BACKEND,
        )
        self._count(encoded, original_node_features)
        return encoded

    def _count(self, encoded, semantic_nodes):
        node_count, edge_count = encoded.node_features.shape[0], encoded.edge_features.shape[0]
        self._totals["encoded_graph_observations_built"] += 1
        self._totals["maximum_encoded_nodes"] = max(
            self._totals["maximum_encoded_nodes"], node_count
        )
        self._totals["maximum_encoded_directed_edges"] = max(
            self._totals["maximum_encoded_directed_edges"], edge_count
        )
        self._totals["encoded_graphs_with_zero_edges"] += edge_count == 0
        self._totals["encoded_graphs_with_communicated_only_participants"] += any(
            all(node.get(field) is None for field in NODE_NUMERIC_SCHEMA[1:])
            for node in semantic_nodes
        )
        self._totals["missing_node_scalar_values_masked"] += int(
            encoded.node_feature_mask.size - encoded.node_feature_mask.sum()
        )
        self._totals["missing_edge_scalar_values_masked"] += int(
            encoded.edge_feature_mask.size - encoded.edge_feature_mask.sum()
        )

    def validation_summary(self):
        return {
            **self._totals,
            "numpy_tensor_backend_confirmed": True,
            "node_feature_dimension": len(NODE_NUMERIC_SCHEMA),
            "edge_feature_dimension": len(EDGE_NUMERIC_SCHEMA),
        }

    def reset(self):
        self._totals = self._empty_totals()
