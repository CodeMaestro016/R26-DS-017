"""Immutable encoded graph output backed by read-only NumPy arrays."""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class EncodedGraphObservation:
    ego_id: str
    node_ids: Tuple[str, ...]
    node_features: np.ndarray
    node_feature_mask: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    edge_feature_mask: np.ndarray
    node_feature_names: Tuple[str, ...]
    edge_feature_names: Tuple[str, ...]
    categorical_encoding_metadata: dict
    hard_constraint_metadata: dict
    identifier_metadata: dict
    source_graph_scope: str
    communication_model: str
    normalization_status: str
    tensor_backend: str

    def __post_init__(self):
        for array in (
            self.node_features, self.node_feature_mask, self.edge_index,
            self.edge_features, self.edge_feature_mask,
        ):
            array.setflags(write=False)

    def dashboard_summary(self):
        return {
            "node_count": int(self.node_features.shape[0]),
            "edge_count": int(self.edge_features.shape[0]),
            "node_feature_dimension": int(self.node_features.shape[1]),
            "edge_feature_dimension": int(self.edge_features.shape[1]),
            "missing_node_feature_count": int(
                self.node_feature_mask.size - self.node_feature_mask.sum()
            ),
            "missing_edge_feature_count": int(
                self.edge_feature_mask.size - self.edge_feature_mask.sum()
            ),
            "tensor_backend": self.tensor_backend,
            "normalization_status": self.normalization_status,
            "source_graph_scope": self.source_graph_scope,
            "communication_model": self.communication_model,
        }
