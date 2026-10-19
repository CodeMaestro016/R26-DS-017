"""CPU-only edge-aware MPNN encoder; no policy, training, or control."""

import torch
from torch import nn

from .message_passing import EdgeAwareMessagePassingLayer
from .models import GNNEncodingOutput


class EdgeAwareMPNNEncoder(nn.Module):
    """Encode directed yielding->priority graphs using incoming SUM messages."""

    def __init__(self, node_input_dim, edge_input_dim, hidden_dim,
                 num_message_passing_layers):
        super().__init__()
        for name, value in (
            ("node_input_dim", node_input_dim),
            ("edge_input_dim", edge_input_dim),
            ("hidden_dim", hidden_dim),
            ("num_message_passing_layers", num_message_passing_layers),
        ):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be an explicit positive integer")
        self.node_input_dim = node_input_dim
        self.edge_input_dim = edge_input_dim
        self.hidden_dim = hidden_dim
        self.num_message_passing_layers = num_message_passing_layers
        self.node_projection = nn.Sequential(
            nn.Linear(2 * node_input_dim, hidden_dim), nn.ReLU(),
        )
        self.edge_projection = nn.Sequential(
            nn.Linear(2 * edge_input_dim, hidden_dim), nn.ReLU(),
        )
        self.layers = nn.ModuleList(
            EdgeAwareMessagePassingLayer(hidden_dim)
            for _ in range(num_message_passing_layers)
        )
        self.to(torch.device("cpu"))

    def forward(self, graph):
        if graph.device != "cpu" or graph.node_features.device.type != "cpu":
            raise ValueError("CPU_DEVICE_REQUIRED")
        if graph.node_features.ndim != 2 or graph.node_features.shape[1] != self.node_input_dim:
            raise ValueError("NODE_INPUT_DIMENSION_MISMATCH")
        if graph.edge_features.ndim != 2 or graph.edge_features.shape[1] != self.edge_input_dim:
            raise ValueError("EDGE_INPUT_DIMENSION_MISMATCH")
        if graph.edge_index.shape != (2, graph.edge_features.shape[0]):
            raise ValueError("EDGE_INDEX_SHAPE_MISMATCH")
        if graph.node_features.shape[0] < 1:
            raise ValueError("AT_LEAST_ONE_NODE_REQUIRED")
        try:
            ego_index = graph.node_ids.index(graph.ego_id)
        except ValueError as error:
            raise ValueError("EGO_ID_NOT_IN_NODE_IDS") from error

        node_input = torch.cat((
            graph.node_features, graph.node_feature_mask.to(torch.float32),
        ), dim=-1)
        edge_input = torch.cat((
            graph.edge_features, graph.edge_feature_mask.to(torch.float32),
        ), dim=-1)
        node_states = self.node_projection(node_input)
        edge_states = self.edge_projection(edge_input)
        for layer in self.layers:
            node_states = layer(node_states, edge_states, graph.edge_index)
        graph_embedding = node_states.mean(dim=0)
        return GNNEncodingOutput(
            node_states, node_states[ego_index], graph_embedding,
            graph.node_ids, ego_index, node_states.device.type,
            str(node_states.dtype), self.num_message_passing_layers,
        )
