"""Deterministic, claim-targeted negotiation semantics for Step 5E.

The edge invariant is ``yielding_vehicle_id -> priority_vehicle_id``.  This
module contains no learned feasibility logic and no vehicle-control behavior.
"""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from .models import NegotiationAction, NegotiationStatus


class ClaimRole(str, Enum):
    EGO_IS_PRIORITY = "EGO_IS_PRIORITY"
    EGO_IS_YIELDING = "EGO_IS_YIELDING"


class PolicyAuthority(str, Enum):
    POLICY_AUTHORIZED = "POLICY_AUTHORIZED"
    POLICY_NOT_REQUIRED = "POLICY_NOT_REQUIRED"
    POLICY_NOT_AUTHORIZED = "POLICY_NOT_AUTHORIZED"


class InfeasibilityReason(str, Enum):
    NO_EXISTING_EGO_PRECEDENCE_CLAIM = "NO_EXISTING_EGO_PRECEDENCE_CLAIM"
    POLICY_NOT_REQUIRED = "POLICY_NOT_REQUIRED"
    REGULATORY_INPUT_UNRESOLVED = "REGULATORY_INPUT_UNRESOLVED"
    SOURCE_SNAPSHOT_MISMATCH = "SOURCE_SNAPSHOT_MISMATCH"
    REGULATORY_PROFILE_MISMATCH = "REGULATORY_PROFILE_MISMATCH"
    COMMUNICATED_PRECEDENCE_DISAGREEMENT = "COMMUNICATED_PRECEDENCE_DISAGREEMENT"
    EXPLICIT_COORDINATION_NOT_PERMITTED = "EXPLICIT_COORDINATION_NOT_PERMITTED"


@dataclass(frozen=True)
class PrecedenceClaim:
    ego_id: str
    counterparty_id: str
    yielding_vehicle_id: str
    priority_vehicle_id: str
    claim_role: ClaimRole
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    shared_conflict_zone_ids: Tuple[str, ...]
    source_snapshot_timestamp: Optional[float]
    hard_constraint_evidence: Mapping


@dataclass(frozen=True)
class MandatoryYieldObligation:
    ego_id: str
    counterparty_id: str
    yielding_vehicle_id: str
    priority_vehicle_id: str
    claim_role: ClaimRole
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    shared_conflict_zone_ids: Tuple[str, ...]
    source_snapshot_timestamp: Optional[float]
    hard_constraint_evidence: Mapping


@dataclass(frozen=True)
class NegotiationActionCandidate:
    ego_id: str
    counterparty_id: str
    yielding_vehicle_id: str
    priority_vehicle_id: str
    action_name: NegotiationAction
    is_feasible: bool
    infeasibility_reason: Optional[InfeasibilityReason]
    applicable_rule_ids: Tuple[str, ...]
    source_sections: Tuple[str, ...]
    source_snapshot_timestamp: Optional[float]


@dataclass(frozen=True)
class ClaimActionMask:
    claim: PrecedenceClaim
    action_names: Tuple[NegotiationAction, ...]
    feasibility: Tuple[bool, ...]
    infeasibility_reasons: Tuple[Optional[InfeasibilityReason], ...]
    policy_authority: PolicyAuthority

    def __post_init__(self):
        if not all(type(value) is bool for value in self.feasibility):
            raise TypeError("ACTION_FEASIBILITY_MUST_BE_EXACT_BOOLEAN")


@dataclass(frozen=True)
class EgoClaimSet:
    ego_id: str
    mandatory_yield_obligations: Tuple[MandatoryYieldObligation, ...]
    ego_precedence_claims: Tuple[PrecedenceClaim, ...]
    action_masks: Tuple[ClaimActionMask, ...]
    action_candidates: Tuple[NegotiationActionCandidate, ...]
    policy_authority: PolicyAuthority
    policy_authority_reason: Optional[InfeasibilityReason]
    protocol_completion_status: str = "ACTION_PROTOCOL_INCOMPLETE"


class NegotiationClaimBuilder:
    """Partition graph edges by ego role and create claim-specific masks.

    Invalid-action masking follows Huang and Ontanon, *A Closer Look at
    Invalid Action Masking in Policy Gradient Algorithms* (2020),
    arXiv:2006.14171.  Only deterministic symbolic evidence is consulted.
    """

    ACTIONS = (NegotiationAction.KEEP_CLAIM, NegotiationAction.RELINQUISH_CLAIM)
    NEGOTIABLE = frozenset({
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value,
    })
    NOT_REQUIRED = frozenset({
        NegotiationStatus.NO_ACTIVE_CONFLICT.value,
        NegotiationStatus.REGULATORY_ORDER_RESOLVED.value,
    })
    BLOCKED_REASONS = {
        NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value:
            InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH,
        NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value:
            InfeasibilityReason.REGULATORY_PROFILE_MISMATCH,
        NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value:
            InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
        NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value:
            InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED,
    }

    def build(self, ego_id, joint_precedence_graph, negotiation_status,
              explicit_coordination_permitted, source_snapshot_consistent=True):
        edges = joint_precedence_graph.get(
            "joint_precedence_edges",
            joint_precedence_graph.get("precedence_edges", ()),
        )
        obligations, claims = [], []
        for edge in edges:
            yielding = edge["yielding_vehicle_id"]
            priority = edge["priority_vehicle_id"]
            if yielding == ego_id:
                obligations.append(self._obligation(ego_id, priority, edge))
            if priority == ego_id:
                claims.append(self._claim(ego_id, yielding, edge))
        obligations.sort(key=lambda item: (item.yielding_vehicle_id, item.priority_vehicle_id))
        claims.sort(key=lambda item: (item.yielding_vehicle_id, item.priority_vehicle_id))

        authority, reason = self._authority(
            negotiation_status, explicit_coordination_permitted,
            source_snapshot_consistent,
        )
        masks, candidates = [], []
        for claim in claims:
            feasible = authority is PolicyAuthority.POLICY_AUTHORIZED
            reasons = (None, None) if feasible else (reason, reason)
            mask = ClaimActionMask(
                claim, self.ACTIONS, (feasible, feasible), reasons, authority,
            )
            masks.append(mask)
            candidates.extend(
                NegotiationActionCandidate(
                    claim.ego_id, claim.counterparty_id,
                    claim.yielding_vehicle_id, claim.priority_vehicle_id,
                    action, allowed, blocked_reason,
                    claim.applicable_rule_ids, claim.source_sections,
                    claim.source_snapshot_timestamp,
                )
                for action, allowed, blocked_reason in zip(
                    mask.action_names, mask.feasibility,
                    mask.infeasibility_reasons,
                )
            )
        return EgoClaimSet(
            ego_id, tuple(obligations), tuple(claims), tuple(masks),
            tuple(candidates), authority, reason,
        )

    @classmethod
    def _authority(cls, status, explicit_permission, source_consistent):
        status = status.value if isinstance(status, NegotiationStatus) else status
        if not source_consistent:
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH)
        if status in cls.BLOCKED_REASONS:
            return PolicyAuthority.POLICY_NOT_AUTHORIZED, cls.BLOCKED_REASONS[status]
        if status in cls.NOT_REQUIRED:
            return (PolicyAuthority.POLICY_NOT_REQUIRED,
                    InfeasibilityReason.POLICY_NOT_REQUIRED)
        if status not in cls.NEGOTIABLE:
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED)
        if not explicit_permission:
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED)
        return PolicyAuthority.POLICY_AUTHORIZED, None

    @staticmethod
    def _common(edge):
        return {
            "applicable_rule_ids": tuple(edge.get("applicable_rule_ids", ())),
            "source_sections": tuple(edge.get("source_sections", ())),
            "shared_conflict_zone_ids": tuple(edge.get("shared_conflict_zone_ids", ())),
            "source_snapshot_timestamp": edge.get("timestamp"),
            "hard_constraint_evidence": MappingProxyType(dict(
                edge.get("hard_constraint_evidence", {})
            )),
        }

    @classmethod
    def _claim(cls, ego_id, counterparty_id, edge):
        return PrecedenceClaim(
            ego_id, counterparty_id, edge["yielding_vehicle_id"],
            edge["priority_vehicle_id"], ClaimRole.EGO_IS_PRIORITY,
            **cls._common(edge),
        )

    @classmethod
    def _obligation(cls, ego_id, counterparty_id, edge):
        return MandatoryYieldObligation(
            ego_id, counterparty_id, edge["yielding_vehicle_id"],
            edge["priority_vehicle_id"], ClaimRole.EGO_IS_YIELDING,
            **cls._common(edge),
        )
