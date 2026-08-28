"""Two-phase ideal same-step transport for protocol messages, separate from claims."""

from .message_models import ClaimRelinquishmentProposal, ClaimRelinquishmentResponse
from ..v2v_claim_bus import same_instant


class NegotiationProtocolBus:
    COMMUNICATION_MODEL = "IDEAL_SAME_STEP_V2V"

    def __init__(self):
        self.reset()

    def begin_step(self, timestamp):
        self._timestamp, self._messages, self._frozen = float(timestamp), set(), False

    def publish(self, message):
        if self._timestamp is None or self._frozen:
            raise RuntimeError("PROTOCOL_STEP_NOT_OPEN")
        if not isinstance(message, (ClaimRelinquishmentProposal,
                                    ClaimRelinquishmentResponse)):
            raise TypeError("PROTOCOL_MESSAGE_REQUIRED")
        if not same_instant(message.source_negotiation_timestamp, self._timestamp):
            raise ValueError("SOURCE_SNAPSHOT_MISMATCH")
        self._messages.add(message)

    def freeze_step(self, timestamp):
        if not same_instant(timestamp, self._timestamp):
            raise ValueError("SOURCE_SNAPSHOT_MISMATCH")
        self._frozen = True

    def current_messages(self, timestamp):
        if not self._frozen or not same_instant(timestamp, self._timestamp):
            raise RuntimeError("NO_FROZEN_PROTOCOL_SNAPSHOT")
        return tuple(sorted(self._messages, key=repr))

    def reset(self):
        self._timestamp, self._messages, self._frozen = None, set(), False
