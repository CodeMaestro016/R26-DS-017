"""Deterministic NumPy-only representation for future GNN input."""

from .graph_tensor_encoder import GraphTensorEncoder, GraphTensorEncodingError
from .models import EncodedGraphObservation
from .schemas import (
    EDGE_NUMERIC_SCHEMA, EDGE_ORIGIN_CATEGORIES, NODE_NUMERIC_SCHEMA,
    RELATIVE_APPROACH_CATEGORIES,
)

__all__ = [
    "EDGE_NUMERIC_SCHEMA", "EDGE_ORIGIN_CATEGORIES",
    "EncodedGraphObservation", "GraphTensorEncoder",
    "GraphTensorEncodingError", "NODE_NUMERIC_SCHEMA",
    "RELATIVE_APPROACH_CATEGORIES",
]
