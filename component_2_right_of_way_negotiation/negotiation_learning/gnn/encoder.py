"""CPU-only edge-aware MPNN encoder; no policy, training, or control."""

# Import torch for use in this module.
import torch
# Import nn from torch for the operations below.
from torch import nn

# Import EdgeAwareMessagePassingLayer from .message_passing for the operations below.
from .message_passing import EdgeAwareMessagePassingLayer
# Import GNNEncodingOutput from .models for the operations below.
from .models import GNNEncodingOutput


# Encode directed yielding->priority graphs using incoming SUM messages.
# Base classes: nn.Module.
# Instances expose the attributes and methods implemented in this class.
class EdgeAwareMPNNEncoder(nn.Module):
    """Encode directed yielding->priority graphs using incoming SUM messages."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input node_input_dim: the supplied node input dim.
    # Input edge_input_dim: the supplied edge input dim.
    # Input hidden_dim: the hidden representation size.
    # Input num_message_passing_layers: the supplied num message passing layers.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def __init__(self, node_input_dim, edge_input_dim, hidden_dim,
                 # Declare num_message_passing_layers as input parameter.
                 num_message_passing_layers):
        # Call super().__init__ with the supplied arguments.
        super().__init__()
        # Iterate over a tuple containing a tuple containing the text 'node_input_dim', node_input_dim, a tuple
        # containing the text..., binding each item to (name, value).
        for name, value in (
            # Include a tuple containing the text 'node_input_dim', node_input_dim in this tuple.
            ("node_input_dim", node_input_dim),
            # Include a tuple containing the text 'edge_input_dim', edge_input_dim in this tuple.
            ("edge_input_dim", edge_input_dim),
            # Include a tuple containing the text 'hidden_dim', hidden_dim in this tuple.
            ("hidden_dim", hidden_dim),
            # Include a tuple containing the text 'num_message_passing_layers', num_message_passing_layers in this
            # tuple.
            ("num_message_passing_layers", num_message_passing_layers),
        ):
            # Run this branch when the negation of whether value has type int or value is at most 0.
            if not isinstance(value, int) or value <= 0:
                # Raise ValueError with formatted text built from the embedded values to stop this execution path.
                raise ValueError(f"{name} must be an explicit positive integer")
        # Set self.node_input_dim to node_input_dim.
        self.node_input_dim = node_input_dim
        # Set self.edge_input_dim to edge_input_dim.
        self.edge_input_dim = edge_input_dim
        # Set self.hidden_dim to hidden_dim.
        self.hidden_dim = hidden_dim
        # Set self.num_message_passing_layers to num_message_passing_layers.
        self.num_message_passing_layers = num_message_passing_layers
        # Set self.node_projection to the result of nn.Sequential(the result of nn.Linear(2 multiplied by
        # node_input_dim, hidden_dim), the result of nn.ReLU()).
        self.node_projection = nn.Sequential(
            # Supply the result of nn.Linear(2 multiplied by node_input_dim, hidden_dim) to nn.Sequential.
            nn.Linear(2 * node_input_dim, hidden_dim), nn.ReLU(),
        )
        # Set self.edge_projection to the result of nn.Sequential(the result of nn.Linear(2 multiplied by
        # edge_input_dim, hidden_dim), the result of nn.ReLU()).
        self.edge_projection = nn.Sequential(
            # Supply the result of nn.Linear(2 multiplied by edge_input_dim, hidden_dim) to nn.Sequential.
            nn.Linear(2 * edge_input_dim, hidden_dim), nn.ReLU(),
        )
        # Set self.layers to the result of nn.ModuleList(a lazy sequence of the result of
        # EdgeAwareMessagePassingLayer(hidden_dim) for _ in the integer...).
        self.layers = nn.ModuleList(
            # Evaluate the result of EdgeAwareMessagePassingLayer(hidden_dim) as part of the enclosing expression.
            EdgeAwareMessagePassingLayer(hidden_dim)
            # Evaluate the integer range defined by num_message_passing_layers as part of the enclosing
            # expression.
            for _ in range(num_message_passing_layers)
        )
        # Call self.to with the supplied arguments.
        self.to(torch.device("cpu"))

    # Forward using the inputs and processing steps below.
    # Input graph: the supplied graph.
    # Output: the result of GNNEncodingOutput(node_states, node_states at ego_index, graph_embedding,
    # graph.node_ids, ego_index,...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def forward(self, graph):
        # Run this branch when graph.device differs from the text 'cpu' or graph.node_features.device.type differs
        # from the text 'cpu'.
        if graph.device != "cpu" or graph.node_features.device.type != "cpu":
            # Raise ValueError with the text 'CPU_DEVICE_REQUIRED' to stop this execution path.
            raise ValueError("CPU_DEVICE_REQUIRED")
        # Run this branch when graph.node_features.ndim differs from 2 or graph.node_features.shape at 1 differs
        # from self.node_input_dim.
        if graph.node_features.ndim != 2 or graph.node_features.shape[1] != self.node_input_dim:
            # Raise ValueError with the text 'NODE_INPUT_DIMENSION_MISMATCH' to stop this execution path.
            raise ValueError("NODE_INPUT_DIMENSION_MISMATCH")
        # Run this branch when graph.edge_features.ndim differs from 2 or graph.edge_features.shape at 1 differs
        # from self.edge_input_dim.
        if graph.edge_features.ndim != 2 or graph.edge_features.shape[1] != self.edge_input_dim:
            # Raise ValueError with the text 'EDGE_INPUT_DIMENSION_MISMATCH' to stop this execution path.
            raise ValueError("EDGE_INPUT_DIMENSION_MISMATCH")
        # Run this branch when graph.edge_index.shape differs from a tuple containing 2, graph.edge_features.shape
        # at 0.
        if graph.edge_index.shape != (2, graph.edge_features.shape[0]):
            # Raise ValueError with the text 'EDGE_INDEX_SHAPE_MISMATCH' to stop this execution path.
            raise ValueError("EDGE_INDEX_SHAPE_MISMATCH")
        # Run this branch when graph.node_features.shape at 0 is less than 1.
        if graph.node_features.shape[0] < 1:
            # Raise ValueError with the text 'AT_LEAST_ONE_NODE_REQUIRED' to stop this execution path.
            raise ValueError("AT_LEAST_ONE_NODE_REQUIRED")
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set ego_index to the result of graph.node_ids.index(graph.ego_id).
            ego_index = graph.node_ids.index(graph.ego_id)
        # Handle ValueError as error using the recovery steps below.
        except ValueError as error:
            # Raise ValueError with the text 'EGO_ID_NOT_IN_NODE_IDS' to stop this execution path.
            raise ValueError("EGO_ID_NOT_IN_NODE_IDS") from error

        # Set node_input to the tensors concatenated by torch.cat.
        node_input = torch.cat((
            # Include the result of graph.node_feature_mask.to(torch.float32) in this tuple.
            graph.node_features, graph.node_feature_mask.to(torch.float32),
        # Supply dim as the negative of 1.
        ), dim=-1)
        # Set edge_input to the tensors concatenated by torch.cat.
        edge_input = torch.cat((
            # Include the result of graph.edge_feature_mask.to(torch.float32) in this tuple.
            graph.edge_features, graph.edge_feature_mask.to(torch.float32),
        # Supply dim as the negative of 1.
        ), dim=-1)
        # Set node_states to the result of self.node_projection(node_input).
        node_states = self.node_projection(node_input)
        # Set edge_states to the result of self.edge_projection(edge_input).
        edge_states = self.edge_projection(edge_input)
        # Iterate over self.layers, binding each item to layer.
        for layer in self.layers:
            # Set node_states to the result of layer(node_states, edge_states, graph.edge_index).
            node_states = layer(node_states, edge_states, graph.edge_index)
        # Set graph_embedding to the result of node_states.mean().
        graph_embedding = node_states.mean(dim=0)
        # Return the result of GNNEncodingOutput(node_states, node_states at ego_index, graph_embedding,
        # graph.node_ids, ego_index,...) to the caller.
        return GNNEncodingOutput(
            # Supply node_states at ego_index to GNNEncodingOutput.
            node_states, node_states[ego_index], graph_embedding,
            # Supply node_states.device.type to GNNEncodingOutput.
            graph.node_ids, ego_index, node_states.device.type,
            # Supply self.num_message_passing_layers to GNNEncodingOutput.
            str(node_states.dtype), self.num_message_passing_layers,
        )
