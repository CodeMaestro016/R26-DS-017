"""Typed values for auditable regulatory assessments."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional, Tuple


class RegulatoryStatus(str, Enum):
    EGO_MUST_YIELD = "EGO_MUST_YIELD"
    EGO_HAS_PRECEDENCE_UNDER_RULE = "EGO_HAS_PRECEDENCE_UNDER_RULE"
    NO_PAIRWISE_PRECEDENCE_RULE = "NO_PAIRWISE_PRECEDENCE_RULE"
    UNRESOLVED_DUE_TO_TARGET_MANOEUVRE = "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"
    REGULATORY_INPUT_UNRESOLVED = "REGULATORY_INPUT_UNRESOLVED"


@dataclass(frozen=True)
class RuleRecord:
    rule_id: str
    jurisdiction: str
    instrument: str
    section: str
    paragraph: str
    scope: str
    predicate_id: str
    effect_id: str
    source_snapshot: str
    implementation_status: str


@dataclass(frozen=True)
class RegulatoryAssessment:
    ego_id: str
    target_id: str
    timestamp: float
    regulatory_profile: str
    ego_path_id: Optional[str]
    candidate_assessments: Tuple[dict, ...]
    regulatory_status: str
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    mandatory_yield: bool
    yield_behavior_constraint_source: Optional[str]
    priority_relinquishment_requires_explicit_coordination: bool
    safe_to_enter: bool = False
    control_action: Optional[str] = None

    def to_dict(self):
        return asdict(self)
