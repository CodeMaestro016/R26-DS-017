"""Typed CPU tensor adapter and immutable MPNN output."""

from dataclasses import dataclass
from typing import Tuple

import torch


@dataclass(frozen=True)
class TorchGraphObservation:
    ego_id: str
    node_ids: Tuple[str, ...]
    node_features: torch.Tensor
    node_feature_mask: torch.Tensor
    edge_index: torch.Tensor
    edge_features: torch.Tensor
    edge_feature_mask: torch.Tensor
    normalization_status: str
    device: str = "cpu"


@dataclass(frozen=True)
class GNNEncodingOutput:
    node_embeddings: torch.Tensor
    ego_embedding: torch.Tensor
    graph_embedding: torch.Tensor
    node_ids: Tuple[str, ...]
    ego_node_index: int
    device: str
    dtype: str
    message_passing_layers: int


def to_torch_graph(encoded):
    """Copy one NumPy graph to CPU tensors without changing its semantics."""
    device = torch.device("cpu")
    return TorchGraphObservation(
        ego_id=encoded.ego_id,
        node_ids=tuple(encoded.node_ids),
        node_features=torch.as_tensor(
            encoded.node_features.copy(), dtype=torch.float32, device=device
        ),
        node_feature_mask=torch.as_tensor(
            encoded.node_feature_mask.copy(), dtype=torch.bool, device=device
        ),
        edge_index=torch.as_tensor(
            encoded.edge_index.copy(), dtype=torch.long, device=device
        ),
        edge_features=torch.as_tensor(
            encoded.edge_features.copy(), dtype=torch.float32, device=device
        ),
        edge_feature_mask=torch.as_tensor(
            encoded.edge_feature_mask.copy(), dtype=torch.bool, device=device
        ),
        normalization_status=encoded.normalization_status,
    )
