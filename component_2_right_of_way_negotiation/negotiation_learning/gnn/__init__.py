"""CPU-only edge-aware MPNN forward-pass components."""

# Import EdgeAwareMPNNEncoder from .encoder for the operations below.
from .encoder import EdgeAwareMPNNEncoder
# Import GNNEncodingOutput, TorchGraphObservation, to_torch_graph from .models for the operations below.
from .models import GNNEncodingOutput, TorchGraphObservation, to_torch_graph
# Import ARCHITECTURE_HYPERPARAMETER_REGISTRY from .schemas for the operations below.
from .schemas import ARCHITECTURE_HYPERPARAMETER_REGISTRY

# Set __all__ to a list containing the text 'ARCHITECTURE_HYPERPARAMETER_REGISTRY', the text
# 'EdgeAwareMPNNEncoder', the text...
__all__ = [
    "ARCHITECTURE_HYPERPARAMETER_REGISTRY", "EdgeAwareMPNNEncoder",
    "GNNEncodingOutput", "TorchGraphObservation", "to_torch_graph",
]
