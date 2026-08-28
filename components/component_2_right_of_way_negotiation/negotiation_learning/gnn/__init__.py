"""CPU-only edge-aware MPNN forward-pass components."""

from .encoder import EdgeAwareMPNNEncoder
from .models import GNNEncodingOutput, TorchGraphObservation, to_torch_graph
from .schemas import ARCHITECTURE_HYPERPARAMETER_REGISTRY

__all__ = [
    "ARCHITECTURE_HYPERPARAMETER_REGISTRY", "EdgeAwareMPNNEncoder",
    "GNNEncodingOutput", "TorchGraphObservation", "to_torch_graph",
]
