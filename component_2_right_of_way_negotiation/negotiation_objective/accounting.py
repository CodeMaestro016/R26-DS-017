"""Pure deterministic vehicle-time measurement and objective equations."""

# Import fmean, pvariance from statistics for the operations below.
from statistics import fmean, pvariance

# Import ObjectiveDiagnostics, VehicleExposureRecord, VehicleTravelTimeMeasurement from .models for the operations
# below.
from .models import (
    ObjectiveDiagnostics, VehicleExposureRecord, VehicleTravelTimeMeasurement,
)


# Define ObjectiveSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ObjectiveSemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Measure vehicle travel times using the inputs and processing steps below.
# Input demand_records: the supplied demand records.
# Input episode_end_time: the supplied episode end time.
# Output: a tuple built from measurements.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def measure_vehicle_travel_times(demand_records, episode_end_time):
    # Set end to a floating-point number built from episode_end_time.
    end = float(episode_end_time)
    # Set measurements to an empty list.
    measurements = []
    # Iterate over the sorted values from demand_records, binding each item to record.
    for record in sorted(demand_records, key=lambda item: item.vehicle_id):
        # Set service_end to a floating-point number built from record.service_completion_time when
        # record.service_completion_time is a different object from None, otherwise end.
        service_end = (float(record.service_completion_time)
                       # Evaluate record.service_completion_time is a different object from None as part of the
                       # enclosing expression.
                       if record.service_completion_time is not None else end)
        # Run this branch when service_end is less than record.scheduled_spawn_time.
        if service_end < record.scheduled_spawn_time:
            # Raise ObjectiveSemanticError with the text 'SERVICE_END_PRECEDES_SCHEDULE' to stop this execution
            # path.
            raise ObjectiveSemanticError("SERVICE_END_PRECEDES_SCHEDULE")
        # Append the result of VehicleTravelTimeMeasurement(record.vehicle_id, record.scheduled_spawn_time,
        # record.actual_departure_time, service_end,...) to measurements.
        measurements.append(VehicleTravelTimeMeasurement(
            # Supply record.scheduled_spawn_time to VehicleTravelTimeMeasurement.
            record.vehicle_id, record.scheduled_spawn_time,
            # Supply record.actual_departure_time to VehicleTravelTimeMeasurement.
            record.actual_departure_time, service_end,
            # Supply record.service_completion_time to VehicleTravelTimeMeasurement.
            record.service_completion_time,
            # Supply service_end minus record.scheduled_spawn_time to VehicleTravelTimeMeasurement.
            service_end - record.scheduled_spawn_time,
            # Supply record.completion_status.value to VehicleTravelTimeMeasurement.
            record.completion_status.value,
            # Store the text 'EXOGENOUS_DEMAND' under 'scheduled_clock'.
            {"scheduled_clock": "EXOGENOUS_DEMAND",
             # Store the text 'SUMO_ARRIVAL' when record.service_completion_time is a different object from None,
             # otherwise the text 'EPISODE_END_CENSORING' under 'completion_clock'.
             "completion_clock": ("SUMO_ARRIVAL" if record.service_completion_time
                                  # Supply the text 'EPISODE_END_CENSORING' to the enclosing expression.
                                  is not None else "EPISODE_END_CENSORING")},
        ))
    # Return a tuple built from measurements to the caller.
    return tuple(measurements)


# Total team travel time seconds using the inputs and processing steps below.
# Input measurements: the supplied measurements.
# Output: the sum of a lazy sequence of item.observed_travel_time_seconds for item in measurements.
def total_team_travel_time_seconds(measurements):
    # Return the sum of a lazy sequence of item.observed_travel_time_seconds for item in measurements to the
    # caller.
    return sum(item.observed_travel_time_seconds for item in measurements)


# Interval vehicle exposures using the inputs and processing steps below.
# Input demand_records: the supplied demand records.
# Input start_timestamp: the supplied start timestamp.
# Input end_timestamp: the supplied end timestamp.
# Output: a tuple built from exposures.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def interval_vehicle_exposures(demand_records, start_timestamp, end_timestamp):
    # Set (start, end) to a tuple containing a floating-point number built from start_timestamp, a floating-point
    # number built from end_timestamp.
    start, end = float(start_timestamp), float(end_timestamp)
    # Run this branch when end is less than start.
    if end < start:
        # Raise ObjectiveSemanticError with the text 'NEGATIVE_OBJECTIVE_INTERVAL_DURATION' to stop this execution
        # path.
        raise ObjectiveSemanticError("NEGATIVE_OBJECTIVE_INTERVAL_DURATION")
    # Set exposures to an empty list.
    exposures = []
    # Iterate over the sorted values from demand_records, binding each item to record.
    for record in sorted(demand_records, key=lambda item: item.vehicle_id):
        # Set service_end to a floating-point number built from record.service_completion_time when
        # record.service_completion_time is a different object from None, otherwise end.
        service_end = (float(record.service_completion_time)
                       # Evaluate record.service_completion_time is a different object from None as part of the
                       # enclosing expression.
                       if record.service_completion_time is not None else end)
        # Set overlap_start to the maximum of start, record.scheduled_spawn_time.
        overlap_start = max(start, record.scheduled_spawn_time)
        # Set overlap_end to the minimum of end, service_end.
        overlap_end = min(end, service_end)
        # Set exposure to the maximum of 0.0, overlap_end minus overlap_start.
        exposure = max(0.0, overlap_end - overlap_start)
        # Append the result of VehicleExposureRecord(record.vehicle_id, start, end, exposure) to exposures.
        exposures.append(VehicleExposureRecord(
            # Supply record.vehicle_id to VehicleExposureRecord.
            record.vehicle_id, start, end, exposure,
        ))
    # Return a tuple built from exposures to the caller.
    return tuple(exposures)


# Team interval cost seconds using the inputs and processing steps below.
# Input exposures: the supplied exposures.
# Output: the sum of a lazy sequence of item.exposure_seconds for item in exposures.
def team_interval_cost_seconds(exposures):
    # Return the sum of a lazy sequence of item.exposure_seconds for item in exposures to the caller.
    return sum(item.exposure_seconds for item in exposures)


# Raw team reward using the inputs and processing steps below.
# Input team_travel_time_increment_seconds: the supplied team travel time increment seconds.
# Output: the negative of a floating-point number built from team_travel_time_increment_seconds.
def raw_team_reward(team_travel_time_increment_seconds):
    # Return the negative of a floating-point number built from team_travel_time_increment_seconds to the caller.
    return -float(team_travel_time_increment_seconds)


# Compute objective diagnostics using the inputs and processing steps below.
# Input measurements: the supplied measurements.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def compute_objective_diagnostics(measurements):
    # Set values to a tuple built from a lazy sequence of item.observed_travel_time_seconds for item in
    # measurements.
    values = tuple(item.observed_travel_time_seconds for item in measurements)
    # Run this branch when the negation of values.
    if not values:
        # Return the result of ObjectiveDiagnostics(0, 0, 0.0, 0.0, 0.0, 0.0) to the caller.
        return ObjectiveDiagnostics(0, 0, 0.0, 0.0, 0.0, 0.0)
    # Return the result of ObjectiveDiagnostics(the number of entries in values, the sum of a lazy sequence of
    # item.service_completion_time is a...) to the caller.
    return ObjectiveDiagnostics(
        # Supply the sum of a lazy sequence of item.service_completion_time is a different object from None for
        # item in measurements to ObjectiveDiagnostics.
        len(values), sum(item.service_completion_time is not None for item in measurements),
        # Supply the result of pvariance(values) to ObjectiveDiagnostics.
        fmean(values), min(values), max(values), pvariance(values),
    )

