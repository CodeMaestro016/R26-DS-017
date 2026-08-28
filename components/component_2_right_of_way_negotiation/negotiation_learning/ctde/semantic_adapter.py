"""CPU PyTorch adapter for immutable NumPy policy semantic encodings."""

import torch


def semantic_encoding_to_torch(encoded):
    return torch.as_tensor(
        encoded.model_input.copy(), dtype=torch.float32, device="cpu"
    )
