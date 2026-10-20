"""Existing rule-based negotiation baseline.

The ONNX intention predictor is intentionally not consumed here while shadow
integration is being validated.
"""

# Import numpy as np for use in this module.
import numpy as np

# Import get_intersection_geometry from map_geometry for the operations below.
from map_geometry import get_intersection_geometry


# Define NegotiationManager to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationManager:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input intersection_geometry: the supplied intersection geometry.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, intersection_geometry=None):
        # Set self.intersection_geometry to intersection_geometry or the result of get_intersection_geometry().
        self.intersection_geometry = (
            # Evaluate intersection_geometry or the result of get_intersection_geometry() as part of the enclosing
            # expression.
            intersection_geometry or get_intersection_geometry())

    # Calculate urgency using the inputs and processing steps below.
    # Input ego_state: the supplied ego state.
    # Output: the maximum of 0.0, 1.0 minus center_distance divided by 250.0.
    def calculate_urgency(self, ego_state):
        # Set position to the result of np.asarray(ego_state at 'pos').
        position = np.asarray(ego_state["pos"], dtype=float)
        # Set center to the result of np.asarray(self.intersection_geometry.center_xy).
        center = np.asarray(self.intersection_geometry.center_xy, dtype=float)
        # Set center_distance to a floating-point number built from the result of np.linalg.norm(position minus
        # center).
        center_distance = float(np.linalg.norm(position - center))
        # Return the maximum of 0.0, 1.0 minus center_distance divided by 250.0 to the caller.
        return max(0.0, 1.0 - center_distance / 250.0)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Detect implicit yield using the inputs and processing steps below.
    # Input nearby_states: the supplied nearby states.
    # Output: the sum of a lazy sequence of 1 for state in nearby_states; retain entries satisfying 'speed' from
    # state; use state.get('vel', 0.0) if absent is less than 3.0.
    def detect_implicit_yield(nearby_states):
        # Return the sum of a lazy sequence of 1 for state in nearby_states; retain entries satisfying 'speed'
        # from state; use state.get('vel', 0.0) if absent is less than 3.0 to the caller.
        return sum(
            # Supply 1 to the enclosing expression.
            1
            # Evaluate nearby_states as part of the enclosing expression.
            for state in nearby_states
            # Evaluate 'speed' from state; use 'vel' from state; use 0.0 if absent if absent is less than 3.0 as
            # part of the enclosing expression.
            if state.get("speed", state.get("vel", 0.0)) < 3.0
        )

    # Negotiate using the inputs and processing steps below.
    # Input ego_state: the supplied ego state.
    # Input nearby_states: the supplied nearby states.
    # Input ldm: the supplied ldm.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def negotiate(self, ego_state, nearby_states, ldm=None):
        # Set urgency to the result of self.calculate_urgency(ego_state).
        urgency = self.calculate_urgency(ego_state)
        # Set yield_signals to the result of self.detect_implicit_yield(nearby_states).
        yield_signals = self.detect_implicit_yield(nearby_states)

        # Run this branch when urgency is greater than 0.6 and yield_signals equals 0.
        if urgency > 0.6 and yield_signals == 0:
            # Return the text 'ASSERT' to the caller.
            return "ASSERT"
        # Run this branch when yield_signals is at least 2 or urgency is less than 0.3 and yield_signals is at
        # least 1.
        if (
            # Evaluate yield_signals is at least 2 or urgency is less than 0.3 and yield_signals is at least 1 as
            # part of the enclosing expression.
            yield_signals >= 2
            # Evaluate urgency is less than 0.3 and yield_signals is at least 1 as part of the enclosing
            # expression.
            or (urgency < 0.3 and yield_signals >= 1)
        ):
            # Return the text 'YIELD' to the caller.
            return "YIELD"
        # Return the text 'MAINTAIN' to the caller.
        return "MAINTAIN"
