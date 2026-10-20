"""Typed values for auditable regulatory assessments."""

# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import Optional, Tuple from typing for the operations below.
from typing import Optional, Tuple


# Define RegulatoryStatus to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class RegulatoryStatus(str, Enum):
    # Set EGO_MUST_YIELD to the text 'EGO_MUST_YIELD'.
    EGO_MUST_YIELD = "EGO_MUST_YIELD"
    # Set EGO_HAS_PRECEDENCE_UNDER_RULE to the text 'EGO_HAS_PRECEDENCE_UNDER_RULE'.
    EGO_HAS_PRECEDENCE_UNDER_RULE = "EGO_HAS_PRECEDENCE_UNDER_RULE"
    # Set NO_PAIRWISE_PRECEDENCE_RULE to the text 'NO_PAIRWISE_PRECEDENCE_RULE'.
    NO_PAIRWISE_PRECEDENCE_RULE = "NO_PAIRWISE_PRECEDENCE_RULE"
    # Set UNRESOLVED_DUE_TO_TARGET_MANOEUVRE to the text 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE'.
    UNRESOLVED_DUE_TO_TARGET_MANOEUVRE = "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"
    # Set REGULATORY_INPUT_UNRESOLVED to the text 'REGULATORY_INPUT_UNRESOLVED'.
    REGULATORY_INPUT_UNRESOLVED = "REGULATORY_INPUT_UNRESOLVED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define RuleRecord to group the state and operations declared below.
# Declared fields: rule_id, jurisdiction, instrument, section, paragraph, scope, predicate_id, effect_id,
# source_snapshot, implementation_status.
# Construction and attribute behavior follow the declared decorators and base classes.
class RuleRecord:
    # Declare rule_id as str for this data structure.
    rule_id: str
    # Declare jurisdiction as str for this data structure.
    jurisdiction: str
    # Declare instrument as str for this data structure.
    instrument: str
    # Declare section as str for this data structure.
    section: str
    # Declare paragraph as str for this data structure.
    paragraph: str
    # Declare scope as str for this data structure.
    scope: str
    # Declare predicate_id as str for this data structure.
    predicate_id: str
    # Declare effect_id as str for this data structure.
    effect_id: str
    # Declare source_snapshot as str for this data structure.
    source_snapshot: str
    # Declare implementation_status as str for this data structure.
    implementation_status: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define RegulatoryAssessment to group the state and operations declared below.
# Declared fields: ego_id, target_id, timestamp, regulatory_profile, ego_path_id, candidate_assessments,
# regulatory_status, applicable_rule_ids, source_sections, mandatory_yield, yield_behavior_constraint_source,....
# Construction and attribute behavior follow the declared decorators and base classes.
class RegulatoryAssessment:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare target_id as str for this data structure.
    target_id: str
    # Declare timestamp as float for this data structure.
    timestamp: float
    # Declare regulatory_profile as str for this data structure.
    regulatory_profile: str
    # Declare ego_path_id as Optional[str] for this data structure.
    ego_path_id: Optional[str]
    # Declare candidate_assessments as Tuple[dict, ...] for this data structure.
    candidate_assessments: Tuple[dict, ...]
    # Declare regulatory_status as str for this data structure.
    regulatory_status: str
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare mandatory_yield as bool for this data structure.
    mandatory_yield: bool
    # Declare yield_behavior_constraint_source as Optional[str] for this data structure.
    yield_behavior_constraint_source: Optional[str]
    # Declare priority_relinquishment_requires_explicit_coordination as bool for this data structure.
    priority_relinquishment_requires_explicit_coordination: bool
    # Set safe_to_enter to False; declare its type as bool.
    safe_to_enter: bool = False
    # Set control_action to None; declare its type as Optional[str].
    control_action: Optional[str] = None

    # To dict using the inputs and processing steps below.
    # Output: the result of asdict(self).
    def to_dict(self):
        # Return the result of asdict(self) to the caller.
        return asdict(self)
