"""Typed CPU tensor adapter and immutable MPNN output."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Tuple from typing for the operations below.
from typing import Tuple

# Import torch for use in this module.
import torch


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define TorchGraphObservation to group the state and operations declared below.
# Declared fields: ego_id, node_ids, node_features, node_feature_mask, edge_index, edge_features,
# edge_feature_mask, normalization_status, device.
# Construction and attribute behavior follow the declared decorators and base classes.
class TorchGraphObservation:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare node_ids as Tuple[str, ...] for this data structure.
    node_ids: Tuple[str, ...]
    # Declare node_features as torch.Tensor for this data structure.
    node_features: torch.Tensor
    # Declare node_feature_mask as torch.Tensor for this data structure.
    node_feature_mask: torch.Tensor
    # Declare edge_index as torch.Tensor for this data structure.
    edge_index: torch.Tensor
    # Declare edge_features as torch.Tensor for this data structure.
    edge_features: torch.Tensor
    # Declare edge_feature_mask as torch.Tensor for this data structure.
    edge_feature_mask: torch.Tensor
    # Declare normalization_status as str for this data structure.
    normalization_status: str
    # Set device to the text 'cpu'; declare its type as str.
    device: str = "cpu"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define GNNEncodingOutput to group the state and operations declared below.
# Declared fields: node_embeddings, ego_embedding, graph_embedding, node_ids, ego_node_index, device, dtype,
# message_passing_layers.
# Construction and attribute behavior follow the declared decorators and base classes.
class GNNEncodingOutput:
    # Declare node_embeddings as torch.Tensor for this data structure.
    node_embeddings: torch.Tensor
    # Declare ego_embedding as torch.Tensor for this data structure.
    ego_embedding: torch.Tensor
    # Declare graph_embedding as torch.Tensor for this data structure.
    graph_embedding: torch.Tensor
    # Declare node_ids as Tuple[str, ...] for this data structure.
    node_ids: Tuple[str, ...]
    # Declare ego_node_index as int for this data structure.
    ego_node_index: int
    # Declare device as str for this data structure.
    device: str
    # Declare dtype as str for this data structure.
    dtype: str
    # Declare message_passing_layers as int for this data structure.
    message_passing_layers: int


# Copy one NumPy graph to CPU tensors without changing its semantics.
# Input encoded: the supplied encoded.
# Output: the result of TorchGraphObservation().
def to_torch_graph(encoded):
    """Copy one NumPy graph to CPU tensors without changing its semantics."""
    # Set device to the result of torch.device(the text 'cpu').
    device = torch.device("cpu")
    # Return the result of TorchGraphObservation() to the caller.
    return TorchGraphObservation(
        # Supply ego_id as encoded.ego_id.
        ego_id=encoded.ego_id,
        # Supply node_ids as a tuple built from encoded.node_ids.
        node_ids=tuple(encoded.node_ids),
        # Supply node_features as a tensor built from the result of encoded.node_features.copy().
        node_features=torch.as_tensor(
            # Supply dtype as torch.float32.
            # Supply device as device.
            encoded.node_features.copy(), dtype=torch.float32, device=device
        ),
        # Supply node_feature_mask as a tensor built from the result of encoded.node_feature_mask.copy().
        node_feature_mask=torch.as_tensor(
            # Supply dtype as torch.bool.
            # Supply device as device.
            encoded.node_feature_mask.copy(), dtype=torch.bool, device=device
        ),
        # Supply edge_index as a tensor built from the result of encoded.edge_index.copy().
        edge_index=torch.as_tensor(
            # Supply dtype as torch.long.
            # Supply device as device.
            encoded.edge_index.copy(), dtype=torch.long, device=device
        ),
        # Supply edge_features as a tensor built from the result of encoded.edge_features.copy().
        edge_features=torch.as_tensor(
            # Supply dtype as torch.float32.
            # Supply device as device.
            encoded.edge_features.copy(), dtype=torch.float32, device=device
        ),
        # Supply edge_feature_mask as a tensor built from the result of encoded.edge_feature_mask.copy().
        edge_feature_mask=torch.as_tensor(
            # Supply dtype as torch.bool.
            # Supply device as device.
            encoded.edge_feature_mask.copy(), dtype=torch.bool, device=device
        ),
        # Supply normalization_status as encoded.normalization_status.
        normalization_status=encoded.normalization_status,
    )
