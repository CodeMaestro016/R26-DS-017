"""Measured isolated-route timing and exact simulator-step scheduling."""

from config import SIM_TIME_STEP


class DeterministicNegotiationScenarioScheduler:
    SYNCHRONIZATION_METHOD = "ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT"

    @staticmethod
    def derive(calibrations):
        records = tuple(sorted(calibrations, key=lambda item: item.movement_path_id))
        if not records:
            raise ValueError("CALIBRATION_RECORDS_REQUIRED")
        target = max(item.departure_to_event_steps for item in records)
        steps = tuple(target - item.departure_to_event_steps for item in records)
        if any(step < 0 for step in steps):
            raise AssertionError("NEGATIVE_SCHEDULED_SPAWN_STEP")
        for step, item in zip(steps, records):
            if step + item.departure_to_event_steps != target:
                raise AssertionError("SYNCHRONIZATION_EQUATION_FAILED")
        return target, steps, tuple(step * SIM_TIME_STEP for step in steps)


def verify_reproducible(first, second):
    return (first.movement_path_id == second.movement_path_id and
            first.departure_to_event_steps == second.departure_to_event_steps and
            first.actual_departure_step == second.actual_departure_step and
            first.synchronization_event_step == second.synchronization_event_step)
