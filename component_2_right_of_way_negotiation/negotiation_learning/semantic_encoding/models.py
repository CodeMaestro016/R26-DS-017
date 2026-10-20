"""Immutable NumPy semantic encodings derived from validated graph schemas."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple

# Import numpy as np for use in this module.
import numpy as np


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EncodedClaimOrProposalSemantics to group the state and operations declared below.
# Declared fields: schema_id, ego_id, counterparty_id, claim_identity, proposal_id, semantic_values,
# availability_mask, column_names, source_node_schema, source_edge_schema, source_schema_identity,
# normalization_status,....
# Construction and attribute behavior follow the declared decorators and base classes.
class EncodedClaimOrProposalSemantics:
    # Declare schema_id as str for this data structure.
    schema_id: str
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare claim_identity as Tuple[str, str] for this data structure.
    claim_identity: Tuple[str, str]
    # Declare proposal_id as Optional[tuple] for this data structure.
    proposal_id: Optional[tuple]
    # Declare semantic_values as np.ndarray for this data structure.
    semantic_values: np.ndarray
    # Declare availability_mask as np.ndarray for this data structure.
    availability_mask: np.ndarray
    # Declare column_names as Tuple[str, ...] for this data structure.
    column_names: Tuple[str, ...]
    # Declare source_node_schema as Tuple[str, ...] for this data structure.
    source_node_schema: Tuple[str, ...]
    # Declare source_edge_schema as Tuple[str, ...] for this data structure.
    source_edge_schema: Tuple[str, ...]
    # Declare source_schema_identity as tuple for this data structure.
    source_schema_identity: tuple
    # Declare normalization_status as str for this data structure.
    normalization_status: str
    # Declare provenance as dict for this data structure.
    provenance: dict

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Set values to the result of np.array(self.semantic_values).
        values = np.array(self.semantic_values, dtype=np.float32, copy=True)
        # Set mask to the result of np.array(self.availability_mask).
        mask = np.array(self.availability_mask, dtype=np.bool_, copy=True)
        # Call values.setflags with the supplied arguments.
        # Call mask.setflags with the supplied arguments.
        values.setflags(write=False); mask.setflags(write=False)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "semantic_values", values)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "availability_mask", mask)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", dict(self.provenance))

    # Apply property as a decorator to configure the following definition.
    @property
    # Model input using the inputs and processing steps below.
    # Output: result.
    def model_input(self):
        # Set result to the result of np.concatenate(a tuple containing self.semantic_values, the result of
        # self.availability_mask.astype(np.float32)).
        result = np.concatenate((
            # Include self.semantic_values in this tuple.
            self.semantic_values,
            # Include the result of self.availability_mask.astype(np.float32) in this tuple.
            self.availability_mask.astype(np.float32),
        ))
        # Call result.setflags with the supplied arguments.
        result.setflags(write=False)
        # Return result to the caller.
        return result


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EncodedProtocolStateSemantics to group the state and operations declared below.
# Declared fields: schema_id, protocol_state, semantic_values, availability_mask, column_names,
# normalization_status, provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class EncodedProtocolStateSemantics:
    # Declare schema_id as str for this data structure.
    schema_id: str
    # Declare protocol_state as Optional[str] for this data structure.
    protocol_state: Optional[str]
    # Declare semantic_values as np.ndarray for this data structure.
    semantic_values: np.ndarray
    # Declare availability_mask as np.ndarray for this data structure.
    availability_mask: np.ndarray
    # Declare column_names as Tuple[str, ...] for this data structure.
    column_names: Tuple[str, ...]
    # Declare normalization_status as str for this data structure.
    normalization_status: str
    # Declare provenance as dict for this data structure.
    provenance: dict

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Set values to the result of np.array(self.semantic_values).
        values = np.array(self.semantic_values, dtype=np.float32, copy=True)
        # Set mask to the result of np.array(self.availability_mask).
        mask = np.array(self.availability_mask, dtype=np.bool_, copy=True)
        # Call values.setflags with the supplied arguments.
        # Call mask.setflags with the supplied arguments.
        values.setflags(write=False); mask.setflags(write=False)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "semantic_values", values)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "availability_mask", mask)
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance", dict(self.provenance))

    # Apply property as a decorator to configure the following definition.
    @property
    # Model input using the inputs and processing steps below.
    # Output: result.
    def model_input(self):
        # Set result to the result of np.concatenate(a tuple containing self.semantic_values, the result of
        # self.availability_mask.astype(np.float32)).
        result = np.concatenate((
            # Include self.semantic_values in this tuple.
            self.semantic_values,
            # Include the result of self.availability_mask.astype(np.float32) in this tuple.
            self.availability_mask.astype(np.float32),
        ))
        # Call result.setflags with the supplied arguments.
        result.setflags(write=False)
        # Return result to the caller.
        return result
