"""Ideal deterministic current-step V2V claim exchange."""

# Import math for use in this module.
import math

# Import PrecedenceClaimMessage from .message_models for the operations below.
from .message_models import PrecedenceClaimMessage


# Compare one simulation instant using only machine-level ULP error.
# Input values: the supplied values.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def same_instant(*values):
    """Compare one simulation instant using only machine-level ULP error."""
    # Run this branch when the negation of values or whether any item is true in a lazy sequence of value is the
    # same object as None for value in values.
    if not values or any(value is None for value in values):
        # Return False to the caller.
        return False
    # Set numbers to a tuple built from a lazy sequence of a floating-point number built from value for value in
    # values.
    numbers = tuple(float(value) for value in values)
    # Run this branch when the negation of whether every item is true in a lazy sequence of whether value contains
    # finite numeric values for value in numbers.
    if not all(math.isfinite(value) for value in numbers):
        # Return False to the caller.
        return False
    # Set tolerance to the result of math.ulp(the maximum of 1.0, the unpacked values from (abs(value) for value
    # in numbers)) multiplied by 8.
    tolerance = math.ulp(max(1.0, *(abs(value) for value in numbers))) * 8
    # Return whether every item is true in a lazy sequence of the absolute value of value - numbers[0] is at most
    # tolerance for value in numbers sliced by 1: to the caller.
    return all(abs(value - numbers[0]) <= tolerance for value in numbers[1:])


# Two-phase, same-step broadcast store with no range, delay, or loss.
# Instances expose the attributes and methods implemented in this class.
class V2VPrecedenceClaimBus:
    """Two-phase, same-step broadcast store with no range, delay, or loss."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self._timestamp to None.
        self._timestamp = None
        # Set self._messages to an empty list.
        self._messages = []
        # Set self._frozen to False.
        self._frozen = False
        # Set self._messages_created to 0.
        self._messages_created = 0

    # Begin step using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Output: no explicit value; normal completion returns None.
    def begin_step(self, current_time):
        # Set self._timestamp to a floating-point number built from current_time.
        self._timestamp = float(current_time)
        # Set self._messages to an empty list.
        self._messages = []
        # Set self._frozen to False.
        self._frozen = False

    # Publish using the inputs and processing steps below.
    # Input message: the supplied message.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def publish(self, message):
        # Run this branch when self._timestamp is the same object as None or self._frozen.
        if self._timestamp is None or self._frozen:
            # Raise RuntimeError with the text 'V2V publication requires an open current step' to stop this
            # execution path.
            raise RuntimeError("V2V publication requires an open current step")
        # Run this branch when the negation of whether message has type PrecedenceClaimMessage.
        if not isinstance(message, PrecedenceClaimMessage):
            # Raise TypeError with the text 'Only immutable PrecedenceClaimMessage values are accepted' to stop
            # this execution path.
            raise TypeError("Only immutable PrecedenceClaimMessage values are accepted")
        # Run this branch when the negation of the result of same_instant(message.timestamp, self._timestamp).
        if not same_instant(message.timestamp, self._timestamp):
            # Raise ValueError with the text 'Claim does not belong to the open simulation step' to stop this
            # execution path.
            raise ValueError("Claim does not belong to the open simulation step")
        # Append message to self._messages.
        self._messages.append(message)
        # Update self._messages_created to its current value plus 1.
        self._messages_created += 1

    # Freeze step using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def freeze_step(self, current_time):
        # Run this branch when the negation of the result of same_instant(current_time, self._timestamp).
        if not same_instant(current_time, self._timestamp):
            # Raise ValueError with the text 'Cannot freeze a different simulation step' to stop this execution
            # path.
            raise ValueError("Cannot freeze a different simulation step")
        # Set self._messages to the sorted values from self._messages.
        self._messages = sorted(self._messages, key=lambda item: (
            # Include item.yielding_vehicle_id in this tuple.
            item.yielding_vehicle_id, item.priority_vehicle_id,
            # Include item.applicable_rule_ids in this tuple.
            item.sender_id, item.applicable_rule_ids,
        ))
        # Set self._frozen to True.
        self._frozen = True

    # Current messages using the inputs and processing steps below.
    # Input current_time: the supplied current time.
    # Input receiver_id: the supplied receiver id.
    # Output: a tuple built from a lazy sequence of message for message in self._messages; retain entries
    # satisfying receiver_id is the same object as None or message.sender_id differs from receiver_id.
    # Processing: select branches using the stated conditions.
    def current_messages(self, current_time, receiver_id=None):
        # Run this branch when the negation of self._frozen or the negation of the result of
        # same_instant(current_time, self._timestamp).
        if not self._frozen or not same_instant(current_time, self._timestamp):
            # Raise RuntimeError with the text 'No frozen claim set exists for this simulation step' to stop this
            # execution path.
            raise RuntimeError("No frozen claim set exists for this simulation step")
        # Return a tuple built from a lazy sequence of message for message in self._messages; retain entries
        # satisfying receiver_id is the same object as None or message.sender_id differs from receiver_id to the
        # caller.
        return tuple(message for message in self._messages
                     # Evaluate receiver_id is the same object as None or message.sender_id differs from
                     # receiver_id as part of the enclosing expression.
                     if receiver_id is None or message.sender_id != receiver_id)

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary containing current_step_v2v_messages_created.
    def validation_summary(self):
        # Return a dictionary containing current_step_v2v_messages_created to the caller.
        return {"current_step_v2v_messages_created": self._messages_created}

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._timestamp to None.
        self._timestamp = None
        # Set self._messages to an empty list.
        self._messages = []
        # Set self._frozen to False.
        self._frozen = False
        # Set self._messages_created to 0.
        self._messages_created = 0
