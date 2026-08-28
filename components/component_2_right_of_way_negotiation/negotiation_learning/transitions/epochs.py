"""Semantic decision-epoch detection, independent of simulation frame rate."""

from .models import DecisionEpochReason, NegotiationDecisionEpoch


class DecisionEpochSemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class NegotiationDecisionEpochTracker:
    def __init__(self):
        self._active = {}
        self._generation = {}

    @staticmethod
    def subject_key(role, ego_id, claim_identity, proposal_id):
        return (role.value, ego_id, proposal_id if proposal_id is not None else claim_identity)

    @staticmethod
    def signature(role, ego_id, claim_identity, proposal_id, negotiation_status,
                  protocol_state, policy_authority, hard_mask, regulatory_profile,
                  lifecycle_identity):
        common = (ego_id, role.value, claim_identity, lifecycle_identity,
                  negotiation_status, policy_authority, tuple(hard_mask), regulatory_profile)
        return (common + (proposal_id, protocol_state.value if protocol_state else None)
                if proposal_id is not None else common)

    def emit(self, *, ego_id, role, counterparty_id, claim_identity,
             lifecycle_identity, proposal_id, parent_decision_event_id,
             timestamp, reason, negotiation_status, protocol_state,
             policy_authority, action_names, hard_mask, actor_snapshot,
             regulatory_profile, communication_model, provenance):
        key = self.subject_key(role, ego_id, claim_identity, proposal_id)
        signature = self.signature(
            role, ego_id, claim_identity, proposal_id, negotiation_status,
            protocol_state, policy_authority, hard_mask, regulatory_profile,
            lifecycle_identity,
        )
        if self._active.get(key) == signature:
            return None
        generation = self._generation.get(key, 0)
        if key not in self._active and generation:
            reason = DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED
        event_id = (float(timestamp), ego_id, role.value, claim_identity,
                    proposal_id, lifecycle_identity, signature)
        epoch = NegotiationDecisionEpoch(
            event_id, ego_id, role, counterparty_id, claim_identity,
            lifecycle_identity, proposal_id, parent_decision_event_id,
            float(timestamp), reason, negotiation_status, protocol_state,
            policy_authority, tuple(action_names), tuple(hard_mask),
            actor_snapshot.snapshot_id, regulatory_profile, communication_model,
            signature, provenance,
        )
        self._active[key] = signature
        self._generation[key] = generation + 1
        return epoch

    def close_subject(self, role, ego_id, claim_identity, proposal_id=None):
        return self._active.pop(self.subject_key(
            role, ego_id, claim_identity, proposal_id), None) is not None

