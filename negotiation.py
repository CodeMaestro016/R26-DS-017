"""Existing rule-based negotiation baseline.

The ONNX intention predictor is intentionally not consumed here while shadow
integration is being validated.
"""

import numpy as np

from config import INTERSECTION_CENTER


class NegotiationManager:
    def calculate_urgency(self, ego_state):
        position = np.asarray(ego_state["pos"], dtype=float)
        center = np.asarray(INTERSECTION_CENTER, dtype=float)
        center_distance = float(np.linalg.norm(position - center))
        return max(0.0, 1.0 - center_distance / 250.0)

    @staticmethod
    def detect_implicit_yield(nearby_states):
        return sum(
            1
            for state in nearby_states
            if state.get("speed", state.get("vel", 0.0)) < 3.0
        )

    def negotiate(self, ego_state, nearby_states, ldm=None):
        urgency = self.calculate_urgency(ego_state)
        yield_signals = self.detect_implicit_yield(nearby_states)

        if urgency > 0.6 and yield_signals == 0:
            return "ASSERT"
        if (
            yield_signals >= 2
            or (urgency < 0.3 and yield_signals >= 1)
        ):
            return "YIELD"
        return "MAINTAIN"

