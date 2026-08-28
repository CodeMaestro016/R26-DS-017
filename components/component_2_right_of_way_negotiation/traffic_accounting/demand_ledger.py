"""Deterministic three-clock ledger; no reward or policy behavior."""

from dataclasses import replace

from .models import DemandScheduleSource, VehicleDemandRecord, VehicleDemandStatus


class DemandLedgerSemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class VehicleDemandLedger:
    def __init__(self):
        self.reset()

    def reset(self):
        self._records = {}
        self._episode_end_time = None
        self._accounting_errors = 0

    def register_scheduled_vehicle(self, vehicle_id, scheduled_spawn_time,
                                   schedule_source, route_metadata=None,
                                   provenance=None):
        if vehicle_id in self._records:
            raise DemandLedgerSemanticError("DUPLICATE_SCHEDULED_VEHICLE")
        try:
            source = (schedule_source if isinstance(schedule_source, DemandScheduleSource)
                      else DemandScheduleSource(schedule_source))
        except (TypeError, ValueError) as error:
            raise DemandLedgerSemanticError("UNSUPPORTED_SCHEDULE_SOURCE") from error
        record = VehicleDemandRecord(
            vehicle_id, float(scheduled_spawn_time), None, None,
            route_metadata or {}, source,
            VehicleDemandStatus.SCHEDULED_WAITING_FOR_DEPARTURE,
            provenance or {"clock": "EXOGENOUS_DEMAND_CLOCK"},
        )
        self._records[vehicle_id] = record
        return record

    def record_actual_departure(self, vehicle_id, actual_departure_time):
        record = self._require(vehicle_id, "DEPARTURE_WITHOUT_SCHEDULE_RECORD")
        timestamp = float(actual_departure_time)
        if record.actual_departure_time is not None:
            if timestamp == record.actual_departure_time:
                return record
            raise DemandLedgerSemanticError("CONFLICTING_DEPARTURE_EVENT")
        if timestamp < record.scheduled_spawn_time:
            raise DemandLedgerSemanticError("DEPARTURE_PRECEDES_SCHEDULE")
        updated = replace(
            record, actual_departure_time=timestamp,
            completion_status=VehicleDemandStatus.ACTIVE_IN_NETWORK,
        )
        self._records[vehicle_id] = updated
        return updated

    def record_service_completion(self, vehicle_id, completion_time):
        record = self._require(vehicle_id, "ARRIVAL_WITHOUT_SCHEDULE_RECORD")
        timestamp = float(completion_time)
        if record.service_completion_time is not None:
            if timestamp == record.service_completion_time:
                return record
            raise DemandLedgerSemanticError("CONFLICTING_SERVICE_COMPLETION_EVENT")
        if record.actual_departure_time is None:
            raise DemandLedgerSemanticError("ARRIVAL_WITHOUT_DEPARTURE_RECORD")
        if timestamp < record.actual_departure_time:
            raise DemandLedgerSemanticError("ARRIVAL_PRECEDES_DEPARTURE")
        updated = replace(
            record, service_completion_time=timestamp,
            completion_status=VehicleDemandStatus.SERVICE_COMPLETED,
        )
        self._records[vehicle_id] = updated
        return updated

    def record_lifecycle_events(self, events):
        for vehicle_id in events.departed_vehicle_ids:
            if vehicle_id.startswith("AV_"):
                self.record_actual_departure(vehicle_id, events.timestamp)
        for vehicle_id in events.arrived_vehicle_ids:
            if vehicle_id.startswith("AV_"):
                self.record_service_completion(vehicle_id, events.timestamp)

    def finalize_episode(self, episode_end_time):
        end = float(episode_end_time)
        if self._episode_end_time is not None and end != self._episode_end_time:
            raise DemandLedgerSemanticError("CONFLICTING_EPISODE_FINALIZATION_TIME")
        for vehicle_id, record in tuple(self._records.items()):
            if record.service_completion_time is not None:
                continue
            status = (VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END
                      if record.actual_departure_time is None else
                      VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END)
            self._records[vehicle_id] = replace(record, completion_status=status)
        self._episode_end_time = end
        return self.get_all_records()

    def get_vehicle_record(self, vehicle_id):
        return self._records.get(vehicle_id)

    def get_all_records(self):
        return tuple(self._records[key] for key in sorted(self._records))

    def validation_summary(self):
        records = self.get_all_records()
        count = lambda status: sum(item.completion_status is status for item in records)
        return {
            "scheduled_vehicles": len(records),
            "actual_departures_recorded": sum(item.actual_departure_time is not None for item in records),
            "service_completions_recorded": sum(item.service_completion_time is not None for item in records),
            "scheduled_not_departed_at_episode_end": count(VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END),
            "departed_not_completed_at_episode_end": count(VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END),
            "completed_services": count(VehicleDemandStatus.SERVICE_COMPLETED),
            "accounting_errors": self._accounting_errors,
        }

    def _require(self, vehicle_id, code):
        record = self._records.get(vehicle_id)
        if record is None:
            self._accounting_errors += 1
            raise DemandLedgerSemanticError(code)
        return record


demand_ledger = VehicleDemandLedger()

