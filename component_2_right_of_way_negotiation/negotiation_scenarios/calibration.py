"""Measured isolated-route timing and exact simulator-step scheduling."""

# Import SIM_TIME_STEP from config for the operations below.
from config import SIM_TIME_STEP


# Define DeterministicNegotiationScenarioScheduler to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class DeterministicNegotiationScenarioScheduler:
    # Set SYNCHRONIZATION_METHOD to the text 'ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT'.
    SYNCHRONIZATION_METHOD = "ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT"

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Derive using the inputs and processing steps below.
    # Input calibrations: the supplied calibrations.
    # Output: a tuple containing target, steps, a tuple built from a lazy sequence of step multiplied by
    # SIM_TIME_STEP for step in steps.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def derive(calibrations):
        # Set records to a tuple built from the sorted values from calibrations.
        records = tuple(sorted(calibrations, key=lambda item: item.movement_path_id))
        # Run this branch when the negation of records.
        if not records:
            # Raise ValueError with the text 'CALIBRATION_RECORDS_REQUIRED' to stop this execution path.
            raise ValueError("CALIBRATION_RECORDS_REQUIRED")
        # Set target to the maximum of a lazy sequence of item.departure_to_event_steps for item in records.
        target = max(item.departure_to_event_steps for item in records)
        # Set steps to a tuple built from a lazy sequence of target minus item.departure_to_event_steps for item
        # in records.
        steps = tuple(target - item.departure_to_event_steps for item in records)
        # Run this branch when whether any item is true in a lazy sequence of step is less than 0 for step in
        # steps.
        if any(step < 0 for step in steps):
            # Raise AssertionError with the text 'NEGATIVE_SCHEDULED_SPAWN_STEP' to stop this execution path.
            raise AssertionError("NEGATIVE_SCHEDULED_SPAWN_STEP")
        # Iterate over corresponding items paired from steps, records, binding each item to (step, item).
        for step, item in zip(steps, records):
            # Run this branch when step plus item.departure_to_event_steps differs from target.
            if step + item.departure_to_event_steps != target:
                # Raise AssertionError with the text 'SYNCHRONIZATION_EQUATION_FAILED' to stop this execution
                # path.
                raise AssertionError("SYNCHRONIZATION_EQUATION_FAILED")
        # Return a tuple containing target, steps, a tuple built from a lazy sequence of step multiplied by
        # SIM_TIME_STEP for step in steps to the caller.
        return target, steps, tuple(step * SIM_TIME_STEP for step in steps)


# Verify reproducible using the inputs and processing steps below.
# Input first: the supplied first.
# Input second: the supplied second.
# Output: first.movement_path_id equals second.movement_path_id and first.departure_to_event_steps equals
# second.departure_to_event_steps and first.actual_departure_step equals...
def verify_reproducible(first, second):
    # Return first.movement_path_id equals second.movement_path_id and first.departure_to_event_steps equals
    # second.departure_to_event_steps and first.actual_departure_step equals second.actual_departure_step and
    # first.synchronization_event_step equals second.synchronization_event_step to the caller.
    return (first.movement_path_id == second.movement_path_id and
            # Evaluate first.departure_to_event_steps equals second.departure_to_event_steps as part of the
            # enclosing expression.
            first.departure_to_event_steps == second.departure_to_event_steps and
            # Evaluate first.actual_departure_step equals second.actual_departure_step as part of the enclosing
            # expression.
            first.actual_departure_step == second.actual_departure_step and
            # Evaluate first.synchronization_event_step equals second.synchronization_event_step as part of the
            # enclosing expression.
            first.synchronization_event_step == second.synchronization_event_step)
