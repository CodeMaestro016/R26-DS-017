"""Two-phase ideal same-step transport for protocol messages, separate from claims."""

# Import ClaimRelinquishmentProposal, ClaimRelinquishmentResponse from .message_models for the operations below.
from .message_models import ClaimRelinquishmentProposal, ClaimRelinquishmentResponse
# Import same_instant from ..v2v_claim_bus for the operations below.
from ..v2v_claim_bus import same_instant


# Define NegotiationProtocolBus to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationProtocolBus:
    # Set COMMUNICATION_MODEL to the text 'IDEAL_SAME_STEP_V2V'.
    COMMUNICATION_MODEL = "IDEAL_SAME_STEP_V2V"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Call self.reset with the supplied arguments.
        self.reset()

    # Begin step using the inputs and processing steps below.
    # Input timestamp: the supplied timestamp.
    # Output: no explicit value; normal completion returns None.
    def begin_step(self, timestamp):
        # Set (self._timestamp, self._messages, self._frozen) to a tuple containing a floating-point number built
        # from timestamp, an empty set, False.
        self._timestamp, self._messages, self._frozen = float(timestamp), set(), False

    # Publish using the inputs and processing steps below.
    # Input message: the supplied message.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def publish(self, message):
        # Run this branch when self._timestamp is the same object as None or self._frozen.
        if self._timestamp is None or self._frozen:
            # Raise RuntimeError with the text 'PROTOCOL_STEP_NOT_OPEN' to stop this execution path.
            raise RuntimeError("PROTOCOL_STEP_NOT_OPEN")
        # Run this branch when the negation of whether message has type a tuple containing
        # ClaimRelinquishmentProposal, ClaimRelinquishmentResponse.
        if not isinstance(message, (ClaimRelinquishmentProposal,
                                    # Include ClaimRelinquishmentResponse in this tuple.
                                    ClaimRelinquishmentResponse)):
            # Raise TypeError with the text 'PROTOCOL_MESSAGE_REQUIRED' to stop this execution path.
            raise TypeError("PROTOCOL_MESSAGE_REQUIRED")
        # Run this branch when the negation of the result of same_instant(message.source_negotiation_timestamp,
        # self._timestamp).
        if not same_instant(message.source_negotiation_timestamp, self._timestamp):
            # Raise ValueError with the text 'SOURCE_SNAPSHOT_MISMATCH' to stop this execution path.
            raise ValueError("SOURCE_SNAPSHOT_MISMATCH")
        # Add message to self._messages.
        self._messages.add(message)

    # Freeze step using the inputs and processing steps below.
    # Input timestamp: the supplied timestamp.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def freeze_step(self, timestamp):
        # Run this branch when the negation of the result of same_instant(timestamp, self._timestamp).
        if not same_instant(timestamp, self._timestamp):
            # Raise ValueError with the text 'SOURCE_SNAPSHOT_MISMATCH' to stop this execution path.
            raise ValueError("SOURCE_SNAPSHOT_MISMATCH")
        # Set self._frozen to True.
        self._frozen = True

    # Current messages using the inputs and processing steps below.
    # Input timestamp: the supplied timestamp.
    # Output: a tuple built from the sorted values from self._messages.
    # Processing: select branches using the stated conditions.
    def current_messages(self, timestamp):
        # Run this branch when the negation of self._frozen or the negation of the result of
        # same_instant(timestamp, self._timestamp).
        if not self._frozen or not same_instant(timestamp, self._timestamp):
            # Raise RuntimeError with the text 'NO_FROZEN_PROTOCOL_SNAPSHOT' to stop this execution path.
            raise RuntimeError("NO_FROZEN_PROTOCOL_SNAPSHOT")
        # Return a tuple built from the sorted values from self._messages to the caller.
        return tuple(sorted(self._messages, key=repr))

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set (self._timestamp, self._messages, self._frozen) to a tuple containing None, an empty set, False.
        self._timestamp, self._messages, self._frozen = None, set(), False
