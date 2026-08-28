"""Immutable NumPy semantic encodings derived from validated graph schemas."""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class EncodedClaimOrProposalSemantics:
    schema_id: str
    ego_id: str
    counterparty_id: str
    claim_identity: Tuple[str, str]
    proposal_id: Optional[tuple]
    semantic_values: np.ndarray
    availability_mask: np.ndarray
    column_names: Tuple[str, ...]
    source_node_schema: Tuple[str, ...]
    source_edge_schema: Tuple[str, ...]
    source_schema_identity: tuple
    normalization_status: str
    provenance: dict

    def __post_init__(self):
        values = np.array(self.semantic_values, dtype=np.float32, copy=True)
        mask = np.array(self.availability_mask, dtype=np.bool_, copy=True)
        values.setflags(write=False); mask.setflags(write=False)
        object.__setattr__(self, "semantic_values", values)
        object.__setattr__(self, "availability_mask", mask)
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def model_input(self):
        result = np.concatenate((
            self.semantic_values,
            self.availability_mask.astype(np.float32),
        ))
        result.setflags(write=False)
        return result


@dataclass(frozen=True)
class EncodedProtocolStateSemantics:
    schema_id: str
    protocol_state: Optional[str]
    semantic_values: np.ndarray
    availability_mask: np.ndarray
    column_names: Tuple[str, ...]
    normalization_status: str
    provenance: dict

    def __post_init__(self):
        values = np.array(self.semantic_values, dtype=np.float32, copy=True)
        mask = np.array(self.availability_mask, dtype=np.bool_, copy=True)
        values.setflags(write=False); mask.setflags(write=False)
        object.__setattr__(self, "semantic_values", values)
        object.__setattr__(self, "availability_mask", mask)
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def model_input(self):
        result = np.concatenate((
            self.semantic_values,
            self.availability_mask.astype(np.float32),
        ))
        result.setflags(write=False)
        return result
