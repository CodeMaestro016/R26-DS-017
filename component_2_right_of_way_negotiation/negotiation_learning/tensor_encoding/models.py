"""Immutable encoded graph output backed by read-only NumPy arrays."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Tuple from typing for the operations below.
from typing import Tuple

# Import numpy as np for use in this module.
import numpy as np


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EncodedGraphObservation to group the state and operations declared below.
# Declared fields: ego_id, node_ids, node_features, node_feature_mask, edge_index, edge_features,
# edge_feature_mask, node_feature_names, edge_feature_names, categorical_encoding_metadata,
# hard_constraint_metadata,....
# Construction and attribute behavior follow the declared decorators and base classes.
class EncodedGraphObservation:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare node_ids as Tuple[str, ...] for this data structure.
    node_ids: Tuple[str, ...]
    # Declare node_features as np.ndarray for this data structure.
    node_features: np.ndarray
    # Declare node_feature_mask as np.ndarray for this data structure.
    node_feature_mask: np.ndarray
    # Declare edge_index as np.ndarray for this data structure.
    edge_index: np.ndarray
    # Declare edge_features as np.ndarray for this data structure.
    edge_features: np.ndarray
    # Declare edge_feature_mask as np.ndarray for this data structure.
    edge_feature_mask: np.ndarray
    # Declare node_feature_names as Tuple[str, ...] for this data structure.
    node_feature_names: Tuple[str, ...]
    # Declare edge_feature_names as Tuple[str, ...] for this data structure.
    edge_feature_names: Tuple[str, ...]
    # Declare categorical_encoding_metadata as dict for this data structure.
    categorical_encoding_metadata: dict
    # Declare hard_constraint_metadata as dict for this data structure.
    hard_constraint_metadata: dict
    # Declare identifier_metadata as dict for this data structure.
    identifier_metadata: dict
    # Declare source_graph_scope as str for this data structure.
    source_graph_scope: str
    # Declare communication_model as str for this data structure.
    communication_model: str
    # Declare normalization_status as str for this data structure.
    normalization_status: str
    # Declare tensor_backend as str for this data structure.
    tensor_backend: str

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __post_init__(self):
        # Iterate over a tuple containing self.node_features, self.node_feature_mask, self.edge_index,
        # self.edge_features, self.edge_feature_mask, binding each item to array.
        for array in (
            # Include self.node_feature_mask in this tuple.
            self.node_features, self.node_feature_mask, self.edge_index,
            # Include self.edge_feature_mask in this tuple.
            self.edge_features, self.edge_feature_mask,
        ):
            # Call array.setflags with the supplied arguments.
            array.setflags(write=False)

    # Dashboard summary using the inputs and processing steps below.
    # Output: a dictionary containing node_count, edge_count, node_feature_dimension, edge_feature_dimension,...
    def dashboard_summary(self):
        # Return a dictionary containing node_count, edge_count, node_feature_dimension,
        # edge_feature_dimension,... to the caller.
        return {
            # Store an integer built from self.node_features.shape at 0 under 'node_count'.
            "node_count": int(self.node_features.shape[0]),
            # Store an integer built from self.edge_features.shape at 0 under 'edge_count'.
            "edge_count": int(self.edge_features.shape[0]),
            # Store an integer built from self.node_features.shape at 1 under 'node_feature_dimension'.
            "node_feature_dimension": int(self.node_features.shape[1]),
            # Store an integer built from self.edge_features.shape at 1 under 'edge_feature_dimension'.
            "edge_feature_dimension": int(self.edge_features.shape[1]),
            # Store an integer built from self.node_feature_mask.size minus the result of
            # self.node_feature_mask.sum() under 'missing_node_feature_count'.
            "missing_node_feature_count": int(
                # Supply self.node_feature_mask.size minus the result of self.node_feature_mask.sum() to int.
                self.node_feature_mask.size - self.node_feature_mask.sum()
            ),
            # Store an integer built from self.edge_feature_mask.size minus the result of
            # self.edge_feature_mask.sum() under 'missing_edge_feature_count'.
            "missing_edge_feature_count": int(
                # Supply self.edge_feature_mask.size minus the result of self.edge_feature_mask.sum() to int.
                self.edge_feature_mask.size - self.edge_feature_mask.sum()
            ),
            # Store self.tensor_backend under 'tensor_backend'.
            "tensor_backend": self.tensor_backend,
            # Store self.normalization_status under 'normalization_status'.
            "normalization_status": self.normalization_status,
            # Store self.source_graph_scope under 'source_graph_scope'.
            "source_graph_scope": self.source_graph_scope,
            # Store self.communication_model under 'communication_model'.
            "communication_model": self.communication_model,
        }
