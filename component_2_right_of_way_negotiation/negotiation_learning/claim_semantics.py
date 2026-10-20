"""Deterministic, claim-targeted negotiation semantics for Step 5E.

The edge invariant is ``yielding_vehicle_id -> priority_vehicle_id``.  This
module contains no learned feasibility logic and no vehicle-control behavior.
"""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Enum from enum for the operations below.
from enum import Enum
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Optional, Tuple from typing for the operations below.
from typing import Mapping, Optional, Tuple

# Import NegotiationAction, NegotiationStatus from .models for the operations below.
from .models import NegotiationAction, NegotiationStatus


# Define ClaimRole to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class ClaimRole(str, Enum):
    # Set EGO_IS_PRIORITY to the text 'EGO_IS_PRIORITY'.
    EGO_IS_PRIORITY = "EGO_IS_PRIORITY"
    # Set EGO_IS_YIELDING to the text 'EGO_IS_YIELDING'.
    EGO_IS_YIELDING = "EGO_IS_YIELDING"


# Define PolicyAuthority to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class PolicyAuthority(str, Enum):
    # Set POLICY_AUTHORIZED to the text 'POLICY_AUTHORIZED'.
    POLICY_AUTHORIZED = "POLICY_AUTHORIZED"
    # Set POLICY_NOT_REQUIRED to the text 'POLICY_NOT_REQUIRED'.
    POLICY_NOT_REQUIRED = "POLICY_NOT_REQUIRED"
    # Set POLICY_NOT_AUTHORIZED to the text 'POLICY_NOT_AUTHORIZED'.
    POLICY_NOT_AUTHORIZED = "POLICY_NOT_AUTHORIZED"


# Define InfeasibilityReason to group the state and operations declared below.
# Base classes: str, Enum.
# Instances expose the attributes and methods implemented in this class.
class InfeasibilityReason(str, Enum):
    # Set NO_EXISTING_EGO_PRECEDENCE_CLAIM to the text 'NO_EXISTING_EGO_PRECEDENCE_CLAIM'.
    NO_EXISTING_EGO_PRECEDENCE_CLAIM = "NO_EXISTING_EGO_PRECEDENCE_CLAIM"
    # Set POLICY_NOT_REQUIRED to the text 'POLICY_NOT_REQUIRED'.
    POLICY_NOT_REQUIRED = "POLICY_NOT_REQUIRED"
    # Set REGULATORY_INPUT_UNRESOLVED to the text 'REGULATORY_INPUT_UNRESOLVED'.
    REGULATORY_INPUT_UNRESOLVED = "REGULATORY_INPUT_UNRESOLVED"
    # Set SOURCE_SNAPSHOT_MISMATCH to the text 'SOURCE_SNAPSHOT_MISMATCH'.
    SOURCE_SNAPSHOT_MISMATCH = "SOURCE_SNAPSHOT_MISMATCH"
    # Set REGULATORY_PROFILE_MISMATCH to the text 'REGULATORY_PROFILE_MISMATCH'.
    REGULATORY_PROFILE_MISMATCH = "REGULATORY_PROFILE_MISMATCH"
    # Set COMMUNICATED_PRECEDENCE_DISAGREEMENT to the text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT'.
    COMMUNICATED_PRECEDENCE_DISAGREEMENT = "COMMUNICATED_PRECEDENCE_DISAGREEMENT"
    # Set EXPLICIT_COORDINATION_NOT_PERMITTED to the text 'EXPLICIT_COORDINATION_NOT_PERMITTED'.
    EXPLICIT_COORDINATION_NOT_PERMITTED = "EXPLICIT_COORDINATION_NOT_PERMITTED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PrecedenceClaim to group the state and operations declared below.
# Declared fields: ego_id, counterparty_id, yielding_vehicle_id, priority_vehicle_id, claim_role,
# applicable_rule_ids, source_sections, shared_conflict_zone_ids, source_snapshot_timestamp,
# hard_constraint_evidence.
# Construction and attribute behavior follow the declared decorators and base classes.
class PrecedenceClaim:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare claim_role as ClaimRole for this data structure.
    claim_role: ClaimRole
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare shared_conflict_zone_ids as Tuple[str, ...] for this data structure.
    shared_conflict_zone_ids: Tuple[str, ...]
    # Declare source_snapshot_timestamp as Optional[float] for this data structure.
    source_snapshot_timestamp: Optional[float]
    # Declare hard_constraint_evidence as Mapping for this data structure.
    hard_constraint_evidence: Mapping


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MandatoryYieldObligation to group the state and operations declared below.
# Declared fields: ego_id, counterparty_id, yielding_vehicle_id, priority_vehicle_id, claim_role,
# applicable_rule_ids, source_sections, shared_conflict_zone_ids, source_snapshot_timestamp,
# hard_constraint_evidence.
# Construction and attribute behavior follow the declared decorators and base classes.
class MandatoryYieldObligation:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare claim_role as ClaimRole for this data structure.
    claim_role: ClaimRole
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare shared_conflict_zone_ids as Tuple[str, ...] for this data structure.
    shared_conflict_zone_ids: Tuple[str, ...]
    # Declare source_snapshot_timestamp as Optional[float] for this data structure.
    source_snapshot_timestamp: Optional[float]
    # Declare hard_constraint_evidence as Mapping for this data structure.
    hard_constraint_evidence: Mapping


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define NegotiationActionCandidate to group the state and operations declared below.
# Declared fields: ego_id, counterparty_id, yielding_vehicle_id, priority_vehicle_id, action_name, is_feasible,
# infeasibility_reason, applicable_rule_ids, source_sections, source_snapshot_timestamp.
# Construction and attribute behavior follow the declared decorators and base classes.
class NegotiationActionCandidate:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare counterparty_id as str for this data structure.
    counterparty_id: str
    # Declare yielding_vehicle_id as str for this data structure.
    yielding_vehicle_id: str
    # Declare priority_vehicle_id as str for this data structure.
    priority_vehicle_id: str
    # Declare action_name as NegotiationAction for this data structure.
    action_name: NegotiationAction
    # Declare is_feasible as bool for this data structure.
    is_feasible: bool
    # Declare infeasibility_reason as Optional[InfeasibilityReason] for this data structure.
    infeasibility_reason: Optional[InfeasibilityReason]
    # Declare applicable_rule_ids as Tuple[str, ...] for this data structure.
    applicable_rule_ids: Tuple[str, ...]
    # Declare source_sections as Tuple[str, ...] for this data structure.
    source_sections: Tuple[str, ...]
    # Declare source_snapshot_timestamp as Optional[float] for this data structure.
    source_snapshot_timestamp: Optional[float]


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define ClaimActionMask to group the state and operations declared below.
# Declared fields: claim, action_names, feasibility, infeasibility_reasons, policy_authority.
# Construction and attribute behavior follow the declared decorators and base classes.
class ClaimActionMask:
    # Declare claim as PrecedenceClaim for this data structure.
    claim: PrecedenceClaim
    # Declare action_names as Tuple[NegotiationAction, ...] for this data structure.
    action_names: Tuple[NegotiationAction, ...]
    # Declare feasibility as Tuple[bool, ...] for this data structure.
    feasibility: Tuple[bool, ...]
    # Declare infeasibility_reasons as Tuple[Optional[InfeasibilityReason], ...] for this data structure.
    infeasibility_reasons: Tuple[Optional[InfeasibilityReason], ...]
    # Declare policy_authority as PolicyAuthority for this data structure.
    policy_authority: PolicyAuthority

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __post_init__(self):
        # Run this branch when the negation of whether every item is true in a lazy sequence of type(value) is the
        # same object as bool for value in self.feasibility.
        if not all(type(value) is bool for value in self.feasibility):
            # Raise TypeError with the text 'ACTION_FEASIBILITY_MUST_BE_EXACT_BOOLEAN' to stop this execution
            # path.
            raise TypeError("ACTION_FEASIBILITY_MUST_BE_EXACT_BOOLEAN")


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define EgoClaimSet to group the state and operations declared below.
# Declared fields: ego_id, mandatory_yield_obligations, ego_precedence_claims, action_masks, action_candidates,
# policy_authority, policy_authority_reason, protocol_completion_status.
# Construction and attribute behavior follow the declared decorators and base classes.
class EgoClaimSet:
    # Declare ego_id as str for this data structure.
    ego_id: str
    # Declare mandatory_yield_obligations as Tuple[MandatoryYieldObligation, ...] for this data structure.
    mandatory_yield_obligations: Tuple[MandatoryYieldObligation, ...]
    # Declare ego_precedence_claims as Tuple[PrecedenceClaim, ...] for this data structure.
    ego_precedence_claims: Tuple[PrecedenceClaim, ...]
    # Declare action_masks as Tuple[ClaimActionMask, ...] for this data structure.
    action_masks: Tuple[ClaimActionMask, ...]
    # Declare action_candidates as Tuple[NegotiationActionCandidate, ...] for this data structure.
    action_candidates: Tuple[NegotiationActionCandidate, ...]
    # Declare policy_authority as PolicyAuthority for this data structure.
    policy_authority: PolicyAuthority
    # Declare policy_authority_reason as Optional[InfeasibilityReason] for this data structure.
    policy_authority_reason: Optional[InfeasibilityReason]
    # Set protocol_completion_status to the text 'EXPLICIT_AGREEMENT_PROTOCOL_AVAILABLE_STEP_5E_1'; declare its
    # type as str.
    protocol_completion_status: str = "EXPLICIT_AGREEMENT_PROTOCOL_AVAILABLE_STEP_5E_1"


# Partition graph edges by ego role and create claim-specific masks.
# Instances expose the attributes and methods implemented in this class.
class NegotiationClaimBuilder:
    """Partition graph edges by ego role and create claim-specific masks.

    Invalid-action masking follows Huang and Ontanon, *A Closer Look at
    Invalid Action Masking in Policy Gradient Algorithms* (2020),
    arXiv:2006.14171.  Only deterministic symbolic evidence is consulted.
    """

    # Set ACTIONS to a tuple containing NegotiationAction.KEEP_CLAIM, NegotiationAction.RELINQUISH_CLAIM.
    ACTIONS = (NegotiationAction.KEEP_CLAIM, NegotiationAction.RELINQUISH_CLAIM)
    # Set NEGOTIABLE to an immutable set built from a set containing
    # NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,...
    NEGOTIABLE = frozenset({
        # Include NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value in this set.
        NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
        # Include NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value in this set.
        NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value,
    })
    # Set NOT_REQUIRED to an immutable set built from a set containing NegotiationStatus.NO_ACTIVE_CONFLICT.value,
    # NegotiationStatus.REGULATORY_ORDER_RESOLVED.value.
    NOT_REQUIRED = frozenset({
        # Include NegotiationStatus.NO_ACTIVE_CONFLICT.value in this set.
        NegotiationStatus.NO_ACTIVE_CONFLICT.value,
        # Include NegotiationStatus.REGULATORY_ORDER_RESOLVED.value in this set.
        NegotiationStatus.REGULATORY_ORDER_RESOLVED.value,
    })
    # Set BLOCKED_REASONS to a dictionary of the supplied entries.
    BLOCKED_REASONS = {
        # Store InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH under
        # NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value.
        NegotiationStatus.SOURCE_SNAPSHOT_MISMATCH.value:
            # Evaluate InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH as part of the enclosing expression.
            InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH,
        # Store InfeasibilityReason.REGULATORY_PROFILE_MISMATCH under
        # NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value.
        NegotiationStatus.REGULATORY_PROFILE_MISMATCH.value:
            # Evaluate InfeasibilityReason.REGULATORY_PROFILE_MISMATCH as part of the enclosing expression.
            InfeasibilityReason.REGULATORY_PROFILE_MISMATCH,
        # Store InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT under
        # NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value.
        NegotiationStatus.COMMUNICATED_PRECEDENCE_DISAGREEMENT.value:
            # Evaluate InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT as part of the enclosing
            # expression.
            InfeasibilityReason.COMMUNICATED_PRECEDENCE_DISAGREEMENT,
        # Store InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED under
        # NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value.
        NegotiationStatus.NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED.value:
            # Evaluate InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED as part of the enclosing expression.
            InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED,
    }

    # Build using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input joint_precedence_graph: the supplied joint precedence graph.
    # Input negotiation_status: the supplied negotiation status.
    # Input explicit_coordination_permitted: the supplied explicit coordination permitted.
    # Input source_snapshot_consistent: the supplied source snapshot consistent.
    # Output: the result of EgoClaimSet(ego_id, a tuple built from obligations, a tuple built from claims, a tuple
    # built from masks, a...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def build(self, ego_id, joint_precedence_graph, negotiation_status,
              # Declare explicit_coordination_permitted, source_snapshot_consistent as input parameters.
              explicit_coordination_permitted, source_snapshot_consistent=True):
        # Set edges to 'joint_precedence_edges' from joint_precedence_graph; use 'precedence_edges' from
        # joint_precedence_graph; use an empty tuple if absent if absent.
        edges = joint_precedence_graph.get(
            "joint_precedence_edges",
            # Supply 'precedence_edges' from joint_precedence_graph; use an empty tuple if absent to
            # joint_precedence_graph.get.
            joint_precedence_graph.get("precedence_edges", ()),
        )
        # Set (obligations, claims) to a tuple containing an empty list, an empty list.
        obligations, claims = [], []
        # Iterate over edges, binding each item to edge.
        for edge in edges:
            # Set yielding to edge at 'yielding_vehicle_id'.
            yielding = edge["yielding_vehicle_id"]
            # Set priority to edge at 'priority_vehicle_id'.
            priority = edge["priority_vehicle_id"]
            # Run this branch when yielding equals ego_id.
            if yielding == ego_id:
                # Append the result of self._obligation(ego_id, priority, edge) to obligations.
                obligations.append(self._obligation(ego_id, priority, edge))
            # Run this branch when priority equals ego_id.
            if priority == ego_id:
                # Append the result of self._claim(ego_id, yielding, edge) to claims.
                claims.append(self._claim(ego_id, yielding, edge))
        # Call obligations.sort with the supplied arguments.
        obligations.sort(key=lambda item: (item.yielding_vehicle_id, item.priority_vehicle_id))
        # Call claims.sort with the supplied arguments.
        claims.sort(key=lambda item: (item.yielding_vehicle_id, item.priority_vehicle_id))

        # Set (authority, reason) to the result of self._authority(negotiation_status,
        # explicit_coordination_permitted, source_snapshot_consistent).
        authority, reason = self._authority(
            # Supply explicit_coordination_permitted to self._authority.
            negotiation_status, explicit_coordination_permitted,
            # Supply source_snapshot_consistent to self._authority.
            source_snapshot_consistent,
        )
        # Set (masks, candidates) to a tuple containing an empty list, an empty list.
        masks, candidates = [], []
        # Iterate over claims, binding each item to claim.
        for claim in claims:
            # Set feasible to authority is the same object as PolicyAuthority.POLICY_AUTHORIZED.
            feasible = authority is PolicyAuthority.POLICY_AUTHORIZED
            # Set reasons to a tuple containing None, None when feasible, otherwise a tuple containing reason,
            # reason.
            reasons = (None, None) if feasible else (reason, reason)
            # Set mask to the result of ClaimActionMask(claim, self.ACTIONS, a tuple containing feasible,
            # feasible, reasons, authority).
            mask = ClaimActionMask(
                # Supply a tuple containing feasible, feasible to ClaimActionMask.
                claim, self.ACTIONS, (feasible, feasible), reasons, authority,
            )
            # Append mask to masks.
            masks.append(mask)
            # Extend candidates with a lazy sequence of the result of NegotiationActionCandidate(claim.ego_id,
            # claim.counterparty_id, claim.yielding_vehicle_id, claim.priority_vehicle_id,...) for (action,
            # allowed, blocked_reason) in corresponding items paired from mask.action_names, mask.feasibility,
            # mask.infeasibility_reasons.
            candidates.extend(
                # Evaluate the result of NegotiationActionCandidate(claim.ego_id, claim.counterparty_id,
                # claim.yielding_vehicle_id, claim.priority_vehicle_id,...) as part of the enclosing expression.
                NegotiationActionCandidate(
                    # Supply claim.counterparty_id to NegotiationActionCandidate.
                    claim.ego_id, claim.counterparty_id,
                    # Supply claim.yielding_vehicle_id to NegotiationActionCandidate.
                    claim.yielding_vehicle_id, claim.priority_vehicle_id,
                    # Supply blocked_reason to NegotiationActionCandidate.
                    action, allowed, blocked_reason,
                    # Supply claim.applicable_rule_ids to NegotiationActionCandidate.
                    claim.applicable_rule_ids, claim.source_sections,
                    # Supply claim.source_snapshot_timestamp to NegotiationActionCandidate.
                    claim.source_snapshot_timestamp,
                )
                # Evaluate corresponding items paired from mask.action_names, mask.feasibility,
                # mask.infeasibility_reasons as part of the enclosing expression.
                for action, allowed, blocked_reason in zip(
                    # Supply mask.action_names to zip.
                    mask.action_names, mask.feasibility,
                    # Supply mask.infeasibility_reasons to zip.
                    mask.infeasibility_reasons,
                )
            )
        # Return the result of EgoClaimSet(ego_id, a tuple built from obligations, a tuple built from claims, a
        # tuple built from masks, a...) to the caller.
        return EgoClaimSet(
            # Supply a tuple built from obligations to EgoClaimSet.
            ego_id, tuple(obligations), tuple(claims), tuple(masks),
            # Supply a tuple built from candidates to EgoClaimSet.
            tuple(candidates), authority, reason,
        )

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Authority using the inputs and processing steps below.
    # Input status: the supplied status.
    # Input explicit_permission: the supplied explicit permission.
    # Input source_consistent: the supplied source consistent.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _authority(cls, status, explicit_permission, source_consistent):
        # Set status to status.value when whether status has type NegotiationStatus, otherwise status.
        status = status.value if isinstance(status, NegotiationStatus) else status
        # Run this branch when the negation of source_consistent.
        if not source_consistent:
            # Return a tuple containing PolicyAuthority.POLICY_NOT_AUTHORIZED,
            # InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH to the caller.
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    # Include InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH in this tuple.
                    InfeasibilityReason.SOURCE_SNAPSHOT_MISMATCH)
        # Run this branch when status belongs to cls.BLOCKED_REASONS.
        if status in cls.BLOCKED_REASONS:
            # Return a tuple containing PolicyAuthority.POLICY_NOT_AUTHORIZED, cls.BLOCKED_REASONS at status to
            # the caller.
            return PolicyAuthority.POLICY_NOT_AUTHORIZED, cls.BLOCKED_REASONS[status]
        # Run this branch when status belongs to cls.NOT_REQUIRED.
        if status in cls.NOT_REQUIRED:
            # Return a tuple containing PolicyAuthority.POLICY_NOT_REQUIRED,
            # InfeasibilityReason.POLICY_NOT_REQUIRED to the caller.
            return (PolicyAuthority.POLICY_NOT_REQUIRED,
                    # Include InfeasibilityReason.POLICY_NOT_REQUIRED in this tuple.
                    InfeasibilityReason.POLICY_NOT_REQUIRED)
        # Run this branch when status does not belong to cls.NEGOTIABLE.
        if status not in cls.NEGOTIABLE:
            # Return a tuple containing PolicyAuthority.POLICY_NOT_AUTHORIZED,
            # InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED to the caller.
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    # Include InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED in this tuple.
                    InfeasibilityReason.REGULATORY_INPUT_UNRESOLVED)
        # Run this branch when the negation of explicit_permission.
        if not explicit_permission:
            # Return a tuple containing PolicyAuthority.POLICY_NOT_AUTHORIZED,
            # InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED to the caller.
            return (PolicyAuthority.POLICY_NOT_AUTHORIZED,
                    # Include InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED in this tuple.
                    InfeasibilityReason.EXPLICIT_COORDINATION_NOT_PERMITTED)
        # Return a tuple containing PolicyAuthority.POLICY_AUTHORIZED, None to the caller.
        return PolicyAuthority.POLICY_AUTHORIZED, None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Common using the inputs and processing steps below.
    # Input edge: the supplied edge.
    # Output: a dictionary containing applicable_rule_ids, source_sections, shared_conflict_zone_ids,...
    def _common(edge):
        # Return a dictionary containing applicable_rule_ids, source_sections, shared_conflict_zone_ids,... to the
        # caller.
        return {
            # Store a tuple built from 'applicable_rule_ids' from edge; use an empty tuple if absent under
            # 'applicable_rule_ids'.
            "applicable_rule_ids": tuple(edge.get("applicable_rule_ids", ())),
            # Store a tuple built from 'source_sections' from edge; use an empty tuple if absent under
            # 'source_sections'.
            "source_sections": tuple(edge.get("source_sections", ())),
            # Store a tuple built from 'shared_conflict_zone_ids' from edge; use an empty tuple if absent under
            # 'shared_conflict_zone_ids'.
            "shared_conflict_zone_ids": tuple(edge.get("shared_conflict_zone_ids", ())),
            # Store 'timestamp' from edge; use None if absent under 'source_snapshot_timestamp'.
            "source_snapshot_timestamp": edge.get("timestamp"),
            # Store the result of MappingProxyType(a dictionary built from 'hard_constraint_evidence' from edge;
            # use an empty dictionary if absent) under 'hard_constraint_evidence'.
            "hard_constraint_evidence": MappingProxyType(dict(
                # Supply 'hard_constraint_evidence' from edge; use an empty dictionary if absent to dict.
                edge.get("hard_constraint_evidence", {})
            )),
        }

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Claim using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input counterparty_id: the supplied counterparty id.
    # Input edge: the supplied edge.
    # Output: the result of PrecedenceClaim(ego_id, counterparty_id, edge at 'yielding_vehicle_id', edge at
    # 'priority_vehicle_id',...).
    def _claim(cls, ego_id, counterparty_id, edge):
        # Return the result of PrecedenceClaim(ego_id, counterparty_id, edge at 'yielding_vehicle_id', edge at
        # 'priority_vehicle_id',...) to the caller.
        return PrecedenceClaim(
            # Supply edge at 'yielding_vehicle_id' to PrecedenceClaim.
            ego_id, counterparty_id, edge["yielding_vehicle_id"],
            # Supply edge at 'priority_vehicle_id' to PrecedenceClaim.
            edge["priority_vehicle_id"], ClaimRole.EGO_IS_PRIORITY,
            # Supply the unpacked keyword arguments as the result of cls._common(edge).
            **cls._common(edge),
        )

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Obligation using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input counterparty_id: the supplied counterparty id.
    # Input edge: the supplied edge.
    # Output: the result of MandatoryYieldObligation(ego_id, counterparty_id, edge at 'yielding_vehicle_id', edge
    # at 'priority_vehicle_id',...).
    def _obligation(cls, ego_id, counterparty_id, edge):
        # Return the result of MandatoryYieldObligation(ego_id, counterparty_id, edge at 'yielding_vehicle_id',
        # edge at 'priority_vehicle_id',...) to the caller.
        return MandatoryYieldObligation(
            # Supply edge at 'yielding_vehicle_id' to MandatoryYieldObligation.
            ego_id, counterparty_id, edge["yielding_vehicle_id"],
            # Supply edge at 'priority_vehicle_id' to MandatoryYieldObligation.
            edge["priority_vehicle_id"], ClaimRole.EGO_IS_YIELDING,
            # Supply the unpacked keyword arguments as the result of cls._common(edge).
            **cls._common(edge),
        )
