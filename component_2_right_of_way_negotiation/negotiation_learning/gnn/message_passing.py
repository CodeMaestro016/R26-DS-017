"""Explicit directed edge-aware message passing using plain PyTorch."""

import torch
from torch import nn


class EdgeAwareMessagePassingLayer(nn.Module):
    """Aggregate source/target/edge messages at each priority target node."""

    def __init__(self, hidden_dim):
        super().__init__()
        self.message_function = nn.Sequential(
            nn.Linear(3 * hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.update_function = nn.Sequential(
            nn.Linear(2 * hidden_dim, hidden_dim), nn.ReLU(),
        )

    def forward(self, node_states, edge_states, edge_index):
        node_count = node_states.shape[0]
        aggregated = node_states.new_zeros((node_count, node_states.shape[1]))
        if edge_index.shape[1] > 0:
            source, target = edge_index[0], edge_index[1]
            messages = self.message_function(torch.cat((
                node_states[source], node_states[target], edge_states,
            ), dim=-1))
            # SUM is permutation invariant. For a node with no incoming edge,
            # the additive identity is the zero vector; this is not imputation.
            aggregated.index_add_(0, target, messages)
        return self.update_function(torch.cat((node_states, aggregated), dim=-1))
