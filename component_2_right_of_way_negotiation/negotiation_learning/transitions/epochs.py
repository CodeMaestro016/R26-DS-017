"""Semantic decision-epoch detection, independent of simulation frame rate."""

# Import DecisionEpochReason, NegotiationDecisionEpoch from .models for the operations below.
from .models import DecisionEpochReason, NegotiationDecisionEpoch


# Define DecisionEpochSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class DecisionEpochSemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Define NegotiationDecisionEpochTracker to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationDecisionEpochTracker:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self._active to an empty dictionary.
        self._active = {}
        # Set self._generation to an empty dictionary.
        self._generation = {}

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Subject key using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input ego_id: the identifier of the ego vehicle.
    # Input claim_identity: the supplied claim identity.
    # Input proposal_id: the supplied proposal id.
    # Output: a tuple containing role.value, ego_id, proposal_id when proposal_id is a different object from None,
    # otherwise claim_identity.
    def subject_key(role, ego_id, claim_identity, proposal_id):
        # Return a tuple containing role.value, ego_id, proposal_id when proposal_id is a different object from
        # None, otherwise claim_identity to the caller.
        return (role.value, ego_id, proposal_id if proposal_id is not None else claim_identity)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Signature using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input ego_id: the identifier of the ego vehicle.
    # Input claim_identity: the supplied claim identity.
    # Input proposal_id: the supplied proposal id.
    # Input negotiation_status: the supplied negotiation status.
    # Input protocol_state: the supplied protocol state.
    # Input policy_authority: the supplied policy authority.
    # Input hard_mask: the supplied hard mask.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input lifecycle_identity: the supplied lifecycle identity.
    # Output: common plus a tuple containing proposal_id, protocol_state.value when protocol_state, otherwise None
    # when proposal_id is a different object from None, otherwise common.
    def signature(role, ego_id, claim_identity, proposal_id, negotiation_status,
                  # Declare protocol_state, policy_authority, hard_mask, regulatory_profile as input parameters.
                  protocol_state, policy_authority, hard_mask, regulatory_profile,
                  # Declare lifecycle_identity as input parameter.
                  lifecycle_identity):
        # Set common to a tuple containing ego_id, role.value, claim_identity, lifecycle_identity,
        # negotiation_status, policy_authority, a tuple...
        common = (ego_id, role.value, claim_identity, lifecycle_identity,
                  # Include negotiation_status in this tuple.
                  negotiation_status, policy_authority, tuple(hard_mask), regulatory_profile)
        # Return common plus a tuple containing proposal_id, protocol_state.value when protocol_state, otherwise
        # None when proposal_id is a different object from None, otherwise common to the caller.
        return (common + (proposal_id, protocol_state.value if protocol_state else None)
                # Evaluate proposal_id is a different object from None as part of the enclosing expression.
                if proposal_id is not None else common)

    # Emit using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input role: the supplied role.
    # Input counterparty_id: the supplied counterparty id.
    # Input claim_identity: the supplied claim identity.
    # Input lifecycle_identity: the supplied lifecycle identity.
    # Input proposal_id: the supplied proposal id.
    # Input parent_decision_event_id: the supplied parent decision event id.
    # Input timestamp: the supplied timestamp.
    # Input reason: the supplied reason.
    # Input negotiation_status: the supplied negotiation status.
    # Input protocol_state: the supplied protocol state.
    # Input policy_authority: the supplied policy authority.
    # Input action_names: the supplied action names.
    # Input hard_mask: the supplied hard mask.
    # Input actor_snapshot: the supplied actor snapshot.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input communication_model: the supplied communication model.
    # Input provenance: the supplied provenance.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def emit(self, *, ego_id, role, counterparty_id, claim_identity,
             # Declare lifecycle_identity, proposal_id, parent_decision_event_id as input parameters.
             lifecycle_identity, proposal_id, parent_decision_event_id,
             # Declare timestamp, reason, negotiation_status, protocol_state as input parameters.
             timestamp, reason, negotiation_status, protocol_state,
             # Declare policy_authority, action_names, hard_mask, actor_snapshot as input parameters.
             policy_authority, action_names, hard_mask, actor_snapshot,
             # Declare regulatory_profile, communication_model, provenance as input parameters.
             regulatory_profile, communication_model, provenance):
        # Set key to the result of self.subject_key(role, ego_id, claim_identity, proposal_id).
        key = self.subject_key(role, ego_id, claim_identity, proposal_id)
        # Set signature to the result of self.signature(role, ego_id, claim_identity, proposal_id,
        # negotiation_status, protocol_state, policy_authority,...).
        signature = self.signature(
            # Supply negotiation_status to self.signature.
            role, ego_id, claim_identity, proposal_id, negotiation_status,
            # Supply regulatory_profile to self.signature.
            protocol_state, policy_authority, hard_mask, regulatory_profile,
            # Supply lifecycle_identity to self.signature.
            lifecycle_identity,
        )
        # Run this branch when key from self._active; use None if absent equals signature.
        if self._active.get(key) == signature:
            # Return None to the caller.
            return None
        # Set generation to key from self._generation; use 0 if absent.
        generation = self._generation.get(key, 0)
        # Run this branch when key does not belong to self._active and generation.
        if key not in self._active and generation:
            # Set reason to DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED.
            reason = DecisionEpochReason.NEGOTIATION_SUBJECT_REENTERED
        # Set event_id to a tuple containing a floating-point number built from timestamp, ego_id, role.value,
        # claim_identity, proposal_id,...
        event_id = (float(timestamp), ego_id, role.value, claim_identity,
                    # Include lifecycle_identity in this tuple.
                    proposal_id, lifecycle_identity, signature)
        # Set epoch to the result of NegotiationDecisionEpoch(event_id, ego_id, role, counterparty_id,
        # claim_identity, lifecycle_identity, proposal_id,...).
        epoch = NegotiationDecisionEpoch(
            # Supply counterparty_id to NegotiationDecisionEpoch.
            event_id, ego_id, role, counterparty_id, claim_identity,
            # Supply parent_decision_event_id to NegotiationDecisionEpoch.
            lifecycle_identity, proposal_id, parent_decision_event_id,
            # Supply negotiation_status to NegotiationDecisionEpoch.
            float(timestamp), reason, negotiation_status, protocol_state,
            # Supply a tuple built from action_names to NegotiationDecisionEpoch.
            policy_authority, tuple(action_names), tuple(hard_mask),
            # Supply actor_snapshot.snapshot_id to NegotiationDecisionEpoch.
            actor_snapshot.snapshot_id, regulatory_profile, communication_model,
            # Supply provenance to NegotiationDecisionEpoch.
            signature, provenance,
        )
        # Set self._active[key] to signature.
        self._active[key] = signature
        # Set self._generation[key] to generation plus 1.
        self._generation[key] = generation + 1
        # Return epoch to the caller.
        return epoch

    # Close subject using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input ego_id: the identifier of the ego vehicle.
    # Input claim_identity: the supplied claim identity.
    # Input proposal_id: the supplied proposal id.
    # Output: the result of self._active.pop(the result of self.subject_key(role, ego_id, claim_identity,
    # proposal_id), None) is a different object from None.
    def close_subject(self, role, ego_id, claim_identity, proposal_id=None):
        # Return the result of self._active.pop(the result of self.subject_key(role, ego_id, claim_identity,
        # proposal_id), None) is a different object from None to the caller.
        return self._active.pop(self.subject_key(
            # Supply claim_identity to self.subject_key.
            role, ego_id, claim_identity, proposal_id), None) is not None

