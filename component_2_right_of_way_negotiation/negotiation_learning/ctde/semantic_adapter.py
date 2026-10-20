"""CPU PyTorch adapter for immutable NumPy policy semantic encodings."""

# Import torch for use in this module.
import torch


# Semantic encoding to torch using the inputs and processing steps below.
# Input encoded: the supplied encoded.
# Output: a tensor built from the result of encoded.model_input.copy().
def semantic_encoding_to_torch(encoded):
    # Return a tensor built from the result of encoded.model_input.copy() to the caller.
    return torch.as_tensor(
        # Supply dtype as torch.float32.
        # Supply device as the text 'cpu'.
        encoded.model_input.copy(), dtype=torch.float32, device="cpu"
    )
