"""Ideal deterministic current-step V2V claim exchange."""

import math

from .message_models import PrecedenceClaimMessage


def same_instant(*values):
    """Compare one simulation instant using only machine-level ULP error."""
    if not values or any(value is None for value in values):
        return False
    numbers = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in numbers):
        return False
    tolerance = math.ulp(max(1.0, *(abs(value) for value in numbers))) * 8
    return all(abs(value - numbers[0]) <= tolerance for value in numbers[1:])


class V2VPrecedenceClaimBus:
    """Two-phase, same-step broadcast store with no range, delay, or loss."""

    def __init__(self):
        self._timestamp = None
        self._messages = []
        self._frozen = False
        self._messages_created = 0

    def begin_step(self, current_time):
        self._timestamp = float(current_time)
        self._messages = []
        self._frozen = False

    def publish(self, message):
        if self._timestamp is None or self._frozen:
            raise RuntimeError("V2V publication requires an open current step")
        if not isinstance(message, PrecedenceClaimMessage):
            raise TypeError("Only immutable PrecedenceClaimMessage values are accepted")
        if not same_instant(message.timestamp, self._timestamp):
            raise ValueError("Claim does not belong to the open simulation step")
        self._messages.append(message)
        self._messages_created += 1

    def freeze_step(self, current_time):
        if not same_instant(current_time, self._timestamp):
            raise ValueError("Cannot freeze a different simulation step")
        self._messages = sorted(self._messages, key=lambda item: (
            item.yielding_vehicle_id, item.priority_vehicle_id,
            item.sender_id, item.applicable_rule_ids,
        ))
        self._frozen = True

    def current_messages(self, current_time, receiver_id=None):
        if not self._frozen or not same_instant(current_time, self._timestamp):
            raise RuntimeError("No frozen claim set exists for this simulation step")
        return tuple(message for message in self._messages
                     if receiver_id is None or message.sender_id != receiver_id)

    def validation_summary(self):
        return {"current_step_v2v_messages_created": self._messages_created}

    def reset(self):
        self._timestamp = None
        self._messages = []
        self._frozen = False
        self._messages_created = 0
