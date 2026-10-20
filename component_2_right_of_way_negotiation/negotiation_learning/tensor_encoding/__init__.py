"""Deterministic NumPy-only representation for future GNN input."""

# Import GraphTensorEncoder, GraphTensorEncodingError from .graph_tensor_encoder for the operations below.
from .graph_tensor_encoder import GraphTensorEncoder, GraphTensorEncodingError
# Import EncodedGraphObservation from .models for the operations below.
from .models import EncodedGraphObservation
# Import EDGE_NUMERIC_SCHEMA, EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA, RELATIVE_APPROACH_CATEGORIES from
# .schemas for the operations below.
from .schemas import (
    EDGE_NUMERIC_SCHEMA, EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA,
    RELATIVE_APPROACH_CATEGORIES,
)

# Set __all__ to a list containing the text 'EDGE_NUMERIC_SCHEMA', the text 'EDGE_ORIGIN_CATEGORIES', the text
# 'EncodedGraphObservation', the...
__all__ = [
    "EDGE_NUMERIC_SCHEMA", "EDGE_ORIGIN_CATEGORIES",
    "EncodedGraphObservation", "GraphTensorEncoder",
    "GraphTensorEncodingError", "NODE_NUMERIC_SCHEMA",
    "RELATIVE_APPROACH_CATEGORIES",
]
