"""Pure deterministic vehicle-time measurement and objective equations."""

from statistics import fmean, pvariance

from .models import (
    ObjectiveDiagnostics, VehicleExposureRecord, VehicleTravelTimeMeasurement,
)


class ObjectiveSemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def measure_vehicle_travel_times(demand_records, episode_end_time):
    end = float(episode_end_time)
    measurements = []
    for record in sorted(demand_records, key=lambda item: item.vehicle_id):
        service_end = (float(record.service_completion_time)
                       if record.service_completion_time is not None else end)
        if service_end < record.scheduled_spawn_time:
            raise ObjectiveSemanticError("SERVICE_END_PRECEDES_SCHEDULE")
        measurements.append(VehicleTravelTimeMeasurement(
            record.vehicle_id, record.scheduled_spawn_time,
            record.actual_departure_time, service_end,
            record.service_completion_time,
            service_end - record.scheduled_spawn_time,
            record.completion_status.value,
            {"scheduled_clock": "EXOGENOUS_DEMAND",
             "completion_clock": ("SUMO_ARRIVAL" if record.service_completion_time
                                  is not None else "EPISODE_END_CENSORING")},
        ))
    return tuple(measurements)


def total_team_travel_time_seconds(measurements):
    return sum(item.observed_travel_time_seconds for item in measurements)


def interval_vehicle_exposures(demand_records, start_timestamp, end_timestamp):
    start, end = float(start_timestamp), float(end_timestamp)
    if end < start:
        raise ObjectiveSemanticError("NEGATIVE_OBJECTIVE_INTERVAL_DURATION")
    exposures = []
    for record in sorted(demand_records, key=lambda item: item.vehicle_id):
        service_end = (float(record.service_completion_time)
                       if record.service_completion_time is not None else end)
        overlap_start = max(start, record.scheduled_spawn_time)
        overlap_end = min(end, service_end)
        exposure = max(0.0, overlap_end - overlap_start)
        exposures.append(VehicleExposureRecord(
            record.vehicle_id, start, end, exposure,
        ))
    return tuple(exposures)


def team_interval_cost_seconds(exposures):
    return sum(item.exposure_seconds for item in exposures)


def raw_team_reward(team_travel_time_increment_seconds):
    return -float(team_travel_time_increment_seconds)


def compute_objective_diagnostics(measurements):
    values = tuple(item.observed_travel_time_seconds for item in measurements)
    if not values:
        return ObjectiveDiagnostics(0, 0, 0.0, 0.0, 0.0, 0.0)
    return ObjectiveDiagnostics(
        len(values), sum(item.service_completion_time is not None for item in measurements),
        fmean(values), min(values), max(values), pvariance(values),
    )

