"""Explicit directed edge-aware message passing using plain PyTorch."""

# Import torch for use in this module.
import torch
# Import nn from torch for the operations below.
from torch import nn


# Aggregate source/target/edge messages at each priority target node.
# Base classes: nn.Module.
# Instances expose the attributes and methods implemented in this class.
class EdgeAwareMessagePassingLayer(nn.Module):
    """Aggregate source/target/edge messages at each priority target node."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input hidden_dim: the hidden representation size.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, hidden_dim):
        # Call super().__init__ with the supplied arguments.
        super().__init__()
        # Set self.message_function to the result of nn.Sequential(the result of nn.Linear(3 multiplied by
        # hidden_dim, hidden_dim), the result of nn.ReLU()).
        self.message_function = nn.Sequential(
            # Supply the result of nn.Linear(3 multiplied by hidden_dim, hidden_dim) to nn.Sequential.
            nn.Linear(3 * hidden_dim, hidden_dim), nn.ReLU(),
        )
        # Set self.update_function to the result of nn.Sequential(the result of nn.Linear(2 multiplied by
        # hidden_dim, hidden_dim), the result of nn.ReLU()).
        self.update_function = nn.Sequential(
            # Supply the result of nn.Linear(2 multiplied by hidden_dim, hidden_dim) to nn.Sequential.
            nn.Linear(2 * hidden_dim, hidden_dim), nn.ReLU(),
        )

    # Forward using the inputs and processing steps below.
    # Input node_states: the current node representations.
    # Input edge_states: the current edge representations.
    # Input edge_index: the source and target node indices.
    # Output: the result of self.update_function(the tensors concatenated by torch.cat).
    # Processing: select branches using the stated conditions.
    def forward(self, node_states, edge_states, edge_index):
        # Set node_count to node_states.shape at 0.
        node_count = node_states.shape[0]
        # Start with a zero incoming-message vector for every node, including nodes with no incoming edges.
        # Set aggregated to a zero-filled tensor with the requested shape.
        aggregated = node_states.new_zeros((node_count, node_states.shape[1]))
        # Run this branch when edge_index.shape at 1 is greater than 0.
        if edge_index.shape[1] > 0:
            # Set (source, target) to a tuple containing edge_index at 0, edge_index at 1.
            source, target = edge_index[0], edge_index[1]
            # Set messages to the result of self.message_function(the tensors concatenated by torch.cat).
            messages = self.message_function(torch.cat((
                # Include node_states at source in this tuple.
                node_states[source], node_states[target], edge_states,
            # Supply dim as the negative of 1.
            ), dim=-1))
            # SUM is permutation invariant. For a node with no incoming edge,
            # the additive identity is the zero vector; this is not imputation.
            # Accumulate the supplied tensor values at the target indices in aggregated.
            aggregated.index_add_(0, target, messages)
        # Return the result of self.update_function(the tensors concatenated by torch.cat) to the caller.
        return self.update_function(torch.cat((node_states, aggregated), dim=-1))
