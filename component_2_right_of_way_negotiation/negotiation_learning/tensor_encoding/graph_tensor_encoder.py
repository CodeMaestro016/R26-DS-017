"""Convert semantic joint graphs to finite, masked NumPy arrays."""

# Import math for use in this module.
import math

# Import numpy as np for use in this module.
import numpy as np

# Import EncodedGraphObservation from .models for the operations below.
from .models import EncodedGraphObservation
# Import CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA, EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA,
# RELATIVE_APPROACH_CATEGORIES from .schemas for the operations below.
from .schemas import (
    CATEGORICAL_ENCODING_METADATA, EDGE_NUMERIC_SCHEMA,
    EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA,
    RELATIVE_APPROACH_CATEGORIES,
)


# Deterministic validation failure for invalid semantic input.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class GraphTensorEncodingError(ValueError):
    """Deterministic validation failure for invalid semantic input."""


# Stateless NumPy encoder with no learned parameters or normalization.
# Instances expose the attributes and methods implemented in this class.
class GraphTensorEncoder:
    """Stateless NumPy encoder with no learned parameters or normalization."""

    # Set NORMALIZATION_STATUS to the text 'NOT_FITTED_TRAINING_STATISTICS_REQUIRED'.
    NORMALIZATION_STATUS = "NOT_FITTED_TRAINING_STATISTICS_REQUIRED"
    # Set TENSOR_BACKEND to the text 'NUMPY'.
    TENSOR_BACKEND = "NUMPY"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Empty totals using the inputs and processing steps below.
    # Output: a dictionary containing encoded_graph_observations_built, maximum_encoded_nodes,...
    def _empty_totals():
        # Return a dictionary containing encoded_graph_observations_built, maximum_encoded_nodes,... to the
        # caller.
        return {
            # Store 0 under 'encoded_graph_observations_built'.
            "encoded_graph_observations_built": 0,
            # Store 0 under 'maximum_encoded_nodes'.
            "maximum_encoded_nodes": 0,
            # Store 0 under 'maximum_encoded_directed_edges'.
            "maximum_encoded_directed_edges": 0,
            # Store 0 under 'encoded_graphs_with_zero_edges'.
            "encoded_graphs_with_zero_edges": 0,
            # Store 0 under 'encoded_graphs_with_communicated_only_participants'.
            "encoded_graphs_with_communicated_only_participants": 0,
            # Store 0 under 'missing_node_scalar_values_masked'.
            "missing_node_scalar_values_masked": 0,
            # Store 0 under 'missing_edge_scalar_values_masked'.
            "missing_edge_scalar_values_masked": 0,
            # Store 0 under 'nonfinite_available_feature_errors'.
            "nonfinite_available_feature_errors": 0,
            # Store 0 under 'route_truth_fields_consumed'.
            "route_truth_fields_consumed": 0,
            # Store 0 under 'arbitrary_ordinal_categorical_encodings'.
            "arbitrary_ordinal_categorical_encodings": 0,
            # Store 0 under 'tensorflow_dependencies_introduced'.
            "tensorflow_dependencies_introduced": 0,
            # Store 0 under 'pytorch_dependencies_introduced'.
            "pytorch_dependencies_introduced": 0,
            # Store 0 under 'control_actions_issued_by_tensor_encoder'.
            "control_actions_issued_by_tensor_encoder": 0,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Scalar using the inputs and processing steps below.
    # Input value: the supplied value.
    # Input field: the supplied field.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _scalar(value, field):
        # Run this branch when value is the same object as None.
        if value is None:
            # Return a tuple containing 0.0, False to the caller.
            return 0.0, False
        # Run this branch when whether value has type a tuple containing bool, np.bool_.
        if isinstance(value, (bool, np.bool_)):
            # Return a tuple containing a floating-point number built from a Boolean built from value, True to the
            # caller.
            return float(bool(value)), True
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set numeric to a floating-point number built from value.
            numeric = float(value)
        # Handle (TypeError, ValueError) as error using the recovery steps below.
        except (TypeError, ValueError) as error:
            # Raise GraphTensorEncodingError with formatted text built from the embedded values to stop this
            # execution path.
            raise GraphTensorEncodingError(
                # Supply formatted text built from the embedded values to GraphTensorEncodingError.
                f"INVALID_AVAILABLE_FEATURE:{field}"
            # Evaluate error as part of the enclosing expression.
            ) from error
        # Run this branch when the negation of whether numeric contains finite numeric values.
        if not math.isfinite(numeric):
            # Raise GraphTensorEncodingError with formatted text built from the embedded values to stop this
            # execution path.
            raise GraphTensorEncodingError(
                # Supply formatted text built from the embedded values to GraphTensorEncodingError.
                f"NONFINITE_AVAILABLE_FEATURE:{field}"
            )
        # Return a tuple containing numeric, True to the caller.
        return numeric, True

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Categorical using the inputs and processing steps below.
    # Input values: the supplied values.
    # Input categories: the supplied categories.
    # Input field: the supplied field.
    # Input multi: the supplied multi.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _categorical(values, categories, field, multi):
        # Run this branch when values is the same object as None or values equals an empty tuple or values equals
        # an empty list.
        if values is None or values == () or values == []:
            # Return a tuple containing a list containing 0.0 multiplied by the number of entries in categories, a
            # list containing False... to the caller.
            return [0.0] * len(categories), [False] * len(categories)
        # Set members to a tuple containing values when whether values has type str, otherwise a tuple built from
        # values.
        members = (values,) if isinstance(values, str) else tuple(values)
        # Set unknown to a set built from members minus a set built from categories.
        unknown = set(members) - set(categories)
        # Run this branch when unknown or the negation of multi and the number of entries in set(members) differs
        # from 1.
        if unknown or (not multi and len(set(members)) != 1):
            # Raise GraphTensorEncodingError with formatted text built from the embedded values to stop this
            # execution path.
            raise GraphTensorEncodingError(
                # Supply formatted text built from the embedded values to GraphTensorEncodingError.
                f"UNKNOWN_OR_INVALID_CATEGORY:{field}:{sorted(unknown)}"
            )
        # Return a tuple containing a list of a floating-point number built from category belongs to members for
        # category in categories, a... to the caller.
        return (
            # Include a list of a floating-point number built from category belongs to members for category in
            # categories in this tuple.
            [float(category in members) for category in categories],
            # Include a list containing True multiplied by the number of entries in categories in this tuple.
            [True] * len(categories),
        )

    # Encode using the inputs and processing steps below.
    # Input graph_observation: the supplied graph observation.
    # Output: encoded.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def encode(self, graph_observation):
        # Set observation to the result of graph_observation.to_dict() when whether graph_observation exposes the
        # requested attribute, otherwise graph_observation.
        observation = (
            # Evaluate the result of graph_observation.to_dict() when whether graph_observation exposes the
            # requested attribute, otherwise graph_observation as part of the enclosing expression.
            graph_observation.to_dict()
            # Evaluate whether graph_observation exposes the requested attribute as part of the enclosing
            # expression.
            if hasattr(graph_observation, "to_dict") else graph_observation
        )
        # Set original_node_ids to a tuple built from 'node_ids' from observation; use an empty tuple if absent.
        original_node_ids = tuple(observation.get("node_ids", ()))
        # Set original_node_features to a tuple built from 'node_features' from observation; use an empty tuple if
        # absent.
        original_node_features = tuple(observation.get("node_features", ()))
        # Run this branch when the number of entries in original_node_ids differs from the number of entries in
        # original_node_features.
        if len(original_node_ids) != len(original_node_features):
            # Raise GraphTensorEncodingError with the text 'NODE_ID_FEATURE_COUNT_MISMATCH' to stop this execution
            # path.
            raise GraphTensorEncodingError("NODE_ID_FEATURE_COUNT_MISMATCH")
        # Set features_by_id to a dictionary built from corresponding items paired from original_node_ids,
        # original_node_features.
        features_by_id = dict(zip(original_node_ids, original_node_features))
        # Set node_ids to a tuple built from the sorted values from original_node_ids.
        node_ids = tuple(sorted(original_node_ids))
        # Set (node_rows, node_masks) to a tuple containing an empty list, an empty list.
        node_rows, node_masks = [], []
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Iterate over node_ids, binding each item to node_id.
            for node_id in node_ids:
                # Set (row, mask) to corresponding items paired from the unpacked values from a lazy sequence of
                # the result of...
                row, mask = zip(*(
                    # Evaluate the result of self._scalar(field from features_by_id[node_id]; use None if absent,
                    # field) as part of the enclosing expression.
                    self._scalar(features_by_id[node_id].get(field), field)
                    # Evaluate NODE_NUMERIC_SCHEMA as part of the enclosing expression.
                    for field in NODE_NUMERIC_SCHEMA
                ))
                # Append row to node_rows.
                node_rows.append(row)
                # Append mask to node_masks.
                node_masks.append(mask)

            # Set semantic_edges to a tuple built from 'edge_features' from observation; use an empty tuple if
            # absent.
            semantic_edges = tuple(observation.get("edge_features", ()))
            # Set semantic_edges to a tuple built from the sorted values from semantic_edges.
            semantic_edges = tuple(sorted(semantic_edges, key=lambda item: (
                # Include item at 'yielding_vehicle_id' in this tuple.
                item["yielding_vehicle_id"], item["priority_vehicle_id"]
            )))
            # Set node_index to a dictionary of node_id mapped to index for (index, node_id) in index/value pairs
            # from node_ids.
            node_index = {node_id: index for index, node_id in enumerate(node_ids)}
            # Set (edge_indices, edge_rows, edge_masks, edge_identifiers) to a tuple containing an empty list, an
            # empty list, an empty list, an empty list.
            edge_indices, edge_rows, edge_masks, edge_identifiers = [], [], [], []
            # Iterate over semantic_edges, binding each item to edge.
            for edge in semantic_edges:
                # Set (yielding, priority) to a tuple containing edge at 'yielding_vehicle_id', edge at
                # 'priority_vehicle_id'.
                yielding, priority = (
                    # Include edge at 'yielding_vehicle_id' in this tuple.
                    edge["yielding_vehicle_id"], edge["priority_vehicle_id"]
                )
                # Run this branch when yielding does not belong to node_index or priority does not belong to
                # node_index.
                if yielding not in node_index or priority not in node_index:
                    # Raise GraphTensorEncodingError with the text 'EDGE_ENDPOINT_NOT_IN_NODE_IDS' to stop this
                    # execution path.
                    raise GraphTensorEncodingError("EDGE_ENDPOINT_NOT_IN_NODE_IDS")
                # Append a tuple containing node_index at yielding, node_index at priority to edge_indices.
                edge_indices.append((node_index[yielding], node_index[priority]))
                # Set (origin_values, origin_mask) to the result of self._categorical('edge_origin' from edge; use
                # None if absent, EDGE_ORIGIN_CATEGORIES, the text 'edge_origin').
                origin_values, origin_mask = self._categorical(
                    # Supply 'edge_origin' from edge; use None if absent to self._categorical.
                    edge.get("edge_origin"), EDGE_ORIGIN_CATEGORIES,
                    # Supply multi as False.
                    "edge_origin", multi=False,
                )
                # Set (relation_values, relation_mask) to the result of self._categorical('relative_approaches'
                # from edge; use None if absent, RELATIVE_APPROACH_CATEGORIES, the text...).
                relation_values, relation_mask = self._categorical(
                    # Supply 'relative_approaches' from edge; use None if absent to self._categorical.
                    edge.get("relative_approaches"), RELATIVE_APPROACH_CATEGORIES,
                    # Supply multi as True.
                    "relative_approaches", multi=True,
                )
                # Set physical to 'physical_reachability_evidence' from edge; use None if absent.
                physical = edge.get("physical_reachability_evidence")
                # Set temporal to 'temporal_conflict_possible' from physical; use None if absent when whether
                # physical has type dict, otherwise None.
                temporal = (
                    # Evaluate 'temporal_conflict_possible' from physical; use None if absent when whether
                    # physical has type dict, otherwise None as part of the enclosing expression.
                    physical.get("temporal_conflict_possible")
                    # Evaluate whether physical has type dict as part of the enclosing expression.
                    if isinstance(physical, dict) else None
                )
                # Set (temporal_value, temporal_mask) to the result of self._scalar(temporal, the text
                # 'temporal_conflict_possible').
                temporal_value, temporal_mask = self._scalar(
                    # Supply temporal to self._scalar.
                    temporal, "temporal_conflict_possible"
                )
                # Append a tuple built from origin_values plus relation_values plus a list containing a
                # floating-point number built from physical is not None, temporal_value to edge_rows.
                edge_rows.append(tuple(origin_values + relation_values + [
                    # Include a floating-point number built from physical is a different object from None in this
                    # list.
                    float(physical is not None), temporal_value,
                ]))
                # Append a tuple built from origin_mask plus relation_mask plus a list containing True,
                # temporal_mask to edge_masks.
                edge_masks.append(tuple(origin_mask + relation_mask + [
                    # Include temporal_mask in this list.
                    True, temporal_mask,
                ]))
                # Append a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
                # source_sections,... to edge_identifiers.
                edge_identifiers.append({
                    # Store yielding under 'yielding_vehicle_id'.
                    "yielding_vehicle_id": yielding,
                    # Store priority under 'priority_vehicle_id'.
                    "priority_vehicle_id": priority,
                    # Store a tuple built from 'applicable_rule_ids' from edge; use an empty tuple if absent under
                    # 'applicable_rule_ids'.
                    "applicable_rule_ids": tuple(edge.get("applicable_rule_ids", ())),
                    # Store a tuple built from 'source_sections' from edge; use an empty tuple if absent under
                    # 'source_sections'.
                    "source_sections": tuple(edge.get("source_sections", ())),
                    # Store 'regulatory_profile' from edge; use None if absent under 'regulatory_profile'.
                    "regulatory_profile": edge.get("regulatory_profile"),
                    # Store a tuple built from 'shared_conflict_zone_ids' from edge; use an empty tuple if absent
                    # under 'shared_conflict_zone_ids'.
                    "shared_conflict_zone_ids": tuple(edge.get("shared_conflict_zone_ids", ())),
                    # Store a tuple built from 'target_candidate_path_ids' from edge; use an empty tuple if absent
                    # under 'target_candidate_path_ids'.
                    "target_candidate_path_ids": tuple(edge.get("target_candidate_path_ids", ())),
                    # Store a tuple built from 'conflict_types' from edge; use an empty tuple if absent under
                    # 'conflict_types'.
                    "conflict_types": tuple(edge.get("conflict_types", ())),
                    # Store physical under 'deferred_physical_reachability_evidence'.
                    "deferred_physical_reachability_evidence": physical,
                })
        # Handle GraphTensorEncodingError as error using the recovery steps below.
        except GraphTensorEncodingError as error:
            # Run this branch when the result of str(error).startswith(the text 'NONFINITE_AVAILABLE_FEATURE').
            if str(error).startswith("NONFINITE_AVAILABLE_FEATURE"):
                # Update self._totals['nonfinite_available_feature_errors'] to its current value plus 1.
                self._totals["nonfinite_available_feature_errors"] += 1
            # Re-raise the active exception.
            raise

        # Set node_array to the result of np.asarray(node_rows, dtype=np.float32).reshape(the number of entries in
        # node_ids, the number of entries in NODE_NUMERIC_SCHEMA).
        node_array = np.asarray(node_rows, dtype=np.float32).reshape(
            # Supply the number of entries in NODE_NUMERIC_SCHEMA to np.asarray(node_rows,
            # dtype=np.float32).reshape.
            len(node_ids), len(NODE_NUMERIC_SCHEMA)
        )
        # Set node_mask to the result of np.asarray(node_masks, dtype=np.bool_).reshape(node_array.shape).
        node_mask = np.asarray(node_masks, dtype=np.bool_).reshape(node_array.shape)
        # Set edge_array to the result of np.asarray(edge_rows, dtype=np.float32).reshape(the number of entries in
        # edge_rows, the number of entries in EDGE_NUMERIC_SCHEMA).
        edge_array = np.asarray(edge_rows, dtype=np.float32).reshape(
            # Supply the number of entries in EDGE_NUMERIC_SCHEMA to np.asarray(edge_rows,
            # dtype=np.float32).reshape.
            len(edge_rows), len(EDGE_NUMERIC_SCHEMA)
        )
        # Set edge_mask to the result of np.asarray(edge_masks, dtype=np.bool_).reshape(edge_array.shape).
        edge_mask = np.asarray(edge_masks, dtype=np.bool_).reshape(edge_array.shape)
        # Set edge_index to np.asarray(edge_indices, dtype=np.int64).reshape(-1, 2).T.
        edge_index = np.asarray(edge_indices, dtype=np.int64).reshape(-1, 2).T
        # Run this branch when the negation of whether every item is true in a lazy sequence of the result of
        # np.isfinite(array).all() for array in a tuple containing node_array, edge_array.
        if not all(np.isfinite(array).all() for array in (node_array, edge_array)):
            # Update self._totals['nonfinite_available_feature_errors'] to its current value plus 1.
            self._totals["nonfinite_available_feature_errors"] += 1
            # Raise GraphTensorEncodingError with the text 'NONFINITE_AVAILABLE_FEATURE' to stop this execution
            # path.
            raise GraphTensorEncodingError("NONFINITE_AVAILABLE_FEATURE")

        # Set metadata to 'metadata' from observation; use an empty dictionary if absent.
        metadata = observation.get("metadata", {})
        # Set encoded to the result of EncodedGraphObservation(observation at 'ego_id', node_ids, node_array,
        # node_mask, edge_index, edge_array, edge_mask,...).
        encoded = EncodedGraphObservation(
            # Supply observation at 'ego_id' to EncodedGraphObservation.
            observation["ego_id"], node_ids, node_array, node_mask,
            # Supply NODE_NUMERIC_SCHEMA to EncodedGraphObservation.
            edge_index, edge_array, edge_mask, NODE_NUMERIC_SCHEMA,
            # Supply a dictionary built from CATEGORICAL_ENCODING_METADATA to EncodedGraphObservation.
            EDGE_NUMERIC_SCHEMA, dict(CATEGORICAL_ENCODING_METADATA),
            # Supply a dictionary built from 'hard_constraint_evidence' from observation; use an empty dictionary
            # if absent to EncodedGraphObservation.
            dict(observation.get("hard_constraint_evidence", {})),
            # Store a tuple built from edge_identifiers under 'edge_identifiers'.
            {"edge_identifiers": tuple(edge_identifiers)},
            # Supply 'graph_scope' from metadata; use the text 'JOINT_LOCAL_V2V' if absent to
            # EncodedGraphObservation.
            metadata.get("graph_scope", "JOINT_LOCAL_V2V"),
            # Supply 'communication_model' from metadata; use the text 'IDEAL_SAME_STEP_V2V' if absent to
            # EncodedGraphObservation.
            metadata.get("communication_model", "IDEAL_SAME_STEP_V2V"),
            # Supply self.NORMALIZATION_STATUS to EncodedGraphObservation.
            self.NORMALIZATION_STATUS, self.TENSOR_BACKEND,
        )
        # Call self._count with the supplied arguments.
        self._count(encoded, original_node_features)
        # Return encoded to the caller.
        return encoded

    # Count using the inputs and processing steps below.
    # Input encoded: the supplied encoded.
    # Input semantic_nodes: the supplied semantic nodes.
    # Output: no explicit value; normal completion returns None.
    def _count(self, encoded, semantic_nodes):
        # Set (node_count, edge_count) to a tuple containing encoded.node_features.shape at 0,
        # encoded.edge_features.shape at 0.
        node_count, edge_count = encoded.node_features.shape[0], encoded.edge_features.shape[0]
        # Update self._totals['encoded_graph_observations_built'] to its current value plus 1.
        self._totals["encoded_graph_observations_built"] += 1
        # Set self._totals['maximum_encoded_nodes'] to the maximum of self._totals at 'maximum_encoded_nodes',
        # node_count.
        self._totals["maximum_encoded_nodes"] = max(
            # Supply self._totals at 'maximum_encoded_nodes' to max.
            self._totals["maximum_encoded_nodes"], node_count
        )
        # Set self._totals['maximum_encoded_directed_edges'] to the maximum of self._totals at
        # 'maximum_encoded_directed_edges', edge_count.
        self._totals["maximum_encoded_directed_edges"] = max(
            # Supply self._totals at 'maximum_encoded_directed_edges' to max.
            self._totals["maximum_encoded_directed_edges"], edge_count
        )
        # Update self._totals['encoded_graphs_with_zero_edges'] to its current value plus edge_count equals 0.
        self._totals["encoded_graphs_with_zero_edges"] += edge_count == 0
        # Update self._totals['encoded_graphs_with_communicated_only_participants'] to its current value plus
        # whether any item is true in a lazy sequence of whether every item is true in a lazy sequence of
        # node.get(field) is None for field in NODE_NUMERIC_SCHEMA[1:] for node in semantic_nodes.
        self._totals["encoded_graphs_with_communicated_only_participants"] += any(
            # Evaluate whether every item is true in a lazy sequence of field from node; use None if absent is the
            # same object as None for field in NODE_NUMERIC_SCHEMA sliced by 1: as part of the enclosing
            # expression.
            all(node.get(field) is None for field in NODE_NUMERIC_SCHEMA[1:])
            # Evaluate semantic_nodes as part of the enclosing expression.
            for node in semantic_nodes
        )
        # Update self._totals['missing_node_scalar_values_masked'] to its current value plus an integer built from
        # encoded.node_feature_mask.size minus the result of encoded.node_feature_mask.sum().
        self._totals["missing_node_scalar_values_masked"] += int(
            # Supply encoded.node_feature_mask.size minus the result of encoded.node_feature_mask.sum() to int.
            encoded.node_feature_mask.size - encoded.node_feature_mask.sum()
        )
        # Update self._totals['missing_edge_scalar_values_masked'] to its current value plus an integer built from
        # encoded.edge_feature_mask.size minus the result of encoded.edge_feature_mask.sum().
        self._totals["missing_edge_scalar_values_masked"] += int(
            # Supply encoded.edge_feature_mask.size minus the result of encoded.edge_feature_mask.sum() to int.
            encoded.edge_feature_mask.size - encoded.edge_feature_mask.sum()
        )

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary containing numpy_tensor_backend_confirmed, node_feature_dimension,
    # edge_feature_dimension.
    def validation_summary(self):
        # Return a dictionary containing numpy_tensor_backend_confirmed, node_feature_dimension,
        # edge_feature_dimension to the caller.
        return {
            # Evaluate self._totals as part of the enclosing expression.
            **self._totals,
            # Store True under 'numpy_tensor_backend_confirmed'.
            "numpy_tensor_backend_confirmed": True,
            # Store the number of entries in NODE_NUMERIC_SCHEMA under 'node_feature_dimension'.
            "node_feature_dimension": len(NODE_NUMERIC_SCHEMA),
            # Store the number of entries in EDGE_NUMERIC_SCHEMA under 'edge_feature_dimension'.
            "edge_feature_dimension": len(EDGE_NUMERIC_SCHEMA),
        }

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()
