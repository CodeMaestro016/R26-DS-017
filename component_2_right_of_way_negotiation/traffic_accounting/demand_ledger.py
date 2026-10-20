"""Deterministic three-clock ledger; no reward or policy behavior."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Import DemandScheduleSource, VehicleDemandRecord, VehicleDemandStatus from .models for the operations below.
from .models import DemandScheduleSource, VehicleDemandRecord, VehicleDemandStatus


# Define DemandLedgerSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class DemandLedgerSemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Define VehicleDemandLedger to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class VehicleDemandLedger:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Call self.reset with the supplied arguments.
        self.reset()

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._records to an empty dictionary.
        self._records = {}
        # Set self._episode_end_time to None.
        self._episode_end_time = None
        # Set self._accounting_errors to 0.
        self._accounting_errors = 0

    # Register scheduled vehicle using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input scheduled_spawn_time: the supplied scheduled spawn time.
    # Input schedule_source: the supplied schedule source.
    # Input route_metadata: the supplied route metadata.
    # Input provenance: the supplied provenance.
    # Output: record.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def register_scheduled_vehicle(self, vehicle_id, scheduled_spawn_time,
                                   # Declare schedule_source, route_metadata as input parameters.
                                   schedule_source, route_metadata=None,
                                   # Declare provenance as input parameter.
                                   provenance=None):
        # Run this branch when vehicle_id belongs to self._records.
        if vehicle_id in self._records:
            # Raise DemandLedgerSemanticError with the text 'DUPLICATE_SCHEDULED_VEHICLE' to stop this execution
            # path.
            raise DemandLedgerSemanticError("DUPLICATE_SCHEDULED_VEHICLE")
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set source to schedule_source when whether schedule_source has type DemandScheduleSource, otherwise
            # the result of DemandScheduleSource(schedule_source).
            source = (schedule_source if isinstance(schedule_source, DemandScheduleSource)
                      # Evaluate the result of DemandScheduleSource(schedule_source) as part of the enclosing
                      # expression.
                      else DemandScheduleSource(schedule_source))
        # Handle (TypeError, ValueError) as error using the recovery steps below.
        except (TypeError, ValueError) as error:
            # Raise DemandLedgerSemanticError with the text 'UNSUPPORTED_SCHEDULE_SOURCE' to stop this execution
            # path.
            raise DemandLedgerSemanticError("UNSUPPORTED_SCHEDULE_SOURCE") from error
        # Set record to the result of VehicleDemandRecord(vehicle_id, a floating-point number built from
        # scheduled_spawn_time, None, None, route_metadata...).
        record = VehicleDemandRecord(
            # Supply a floating-point number built from scheduled_spawn_time to VehicleDemandRecord.
            vehicle_id, float(scheduled_spawn_time), None, None,
            # Supply route_metadata or an empty dictionary to VehicleDemandRecord.
            route_metadata or {}, source,
            # Supply VehicleDemandStatus.SCHEDULED_WAITING_FOR_DEPARTURE to VehicleDemandRecord.
            VehicleDemandStatus.SCHEDULED_WAITING_FOR_DEPARTURE,
            # Store the text 'EXOGENOUS_DEMAND_CLOCK' under 'clock'.
            provenance or {"clock": "EXOGENOUS_DEMAND_CLOCK"},
        )
        # Set self._records[vehicle_id] to record.
        self._records[vehicle_id] = record
        # Return record to the caller.
        return record

    # Record actual departure using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input actual_departure_time: the supplied actual departure time.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def record_actual_departure(self, vehicle_id, actual_departure_time):
        # Set record to the result of self._require(vehicle_id, the text 'DEPARTURE_WITHOUT_SCHEDULE_RECORD').
        record = self._require(vehicle_id, "DEPARTURE_WITHOUT_SCHEDULE_RECORD")
        # Set timestamp to a floating-point number built from actual_departure_time.
        timestamp = float(actual_departure_time)
        # Run this branch when record.actual_departure_time is a different object from None.
        if record.actual_departure_time is not None:
            # Run this branch when timestamp equals record.actual_departure_time.
            if timestamp == record.actual_departure_time:
                # Return record to the caller.
                return record
            # Raise DemandLedgerSemanticError with the text 'CONFLICTING_DEPARTURE_EVENT' to stop this execution
            # path.
            raise DemandLedgerSemanticError("CONFLICTING_DEPARTURE_EVENT")
        # Run this branch when timestamp is less than record.scheduled_spawn_time.
        if timestamp < record.scheduled_spawn_time:
            # Raise DemandLedgerSemanticError with the text 'DEPARTURE_PRECEDES_SCHEDULE' to stop this execution
            # path.
            raise DemandLedgerSemanticError("DEPARTURE_PRECEDES_SCHEDULE")
        # Set updated to the result of replace(record).
        updated = replace(
            # Supply actual_departure_time as timestamp.
            record, actual_departure_time=timestamp,
            # Supply completion_status as VehicleDemandStatus.ACTIVE_IN_NETWORK.
            completion_status=VehicleDemandStatus.ACTIVE_IN_NETWORK,
        )
        # Set self._records[vehicle_id] to updated.
        self._records[vehicle_id] = updated
        # Return updated to the caller.
        return updated

    # Record service completion using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input completion_time: the supplied completion time.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def record_service_completion(self, vehicle_id, completion_time):
        # Set record to the result of self._require(vehicle_id, the text 'ARRIVAL_WITHOUT_SCHEDULE_RECORD').
        record = self._require(vehicle_id, "ARRIVAL_WITHOUT_SCHEDULE_RECORD")
        # Set timestamp to a floating-point number built from completion_time.
        timestamp = float(completion_time)
        # Run this branch when record.service_completion_time is a different object from None.
        if record.service_completion_time is not None:
            # Run this branch when timestamp equals record.service_completion_time.
            if timestamp == record.service_completion_time:
                # Return record to the caller.
                return record
            # Raise DemandLedgerSemanticError with the text 'CONFLICTING_SERVICE_COMPLETION_EVENT' to stop this
            # execution path.
            raise DemandLedgerSemanticError("CONFLICTING_SERVICE_COMPLETION_EVENT")
        # Run this branch when record.actual_departure_time is the same object as None.
        if record.actual_departure_time is None:
            # Raise DemandLedgerSemanticError with the text 'ARRIVAL_WITHOUT_DEPARTURE_RECORD' to stop this
            # execution path.
            raise DemandLedgerSemanticError("ARRIVAL_WITHOUT_DEPARTURE_RECORD")
        # Run this branch when timestamp is less than record.actual_departure_time.
        if timestamp < record.actual_departure_time:
            # Raise DemandLedgerSemanticError with the text 'ARRIVAL_PRECEDES_DEPARTURE' to stop this execution
            # path.
            raise DemandLedgerSemanticError("ARRIVAL_PRECEDES_DEPARTURE")
        # Set updated to the result of replace(record).
        updated = replace(
            # Supply service_completion_time as timestamp.
            record, service_completion_time=timestamp,
            # Supply completion_status as VehicleDemandStatus.SERVICE_COMPLETED.
            completion_status=VehicleDemandStatus.SERVICE_COMPLETED,
        )
        # Set self._records[vehicle_id] to updated.
        self._records[vehicle_id] = updated
        # Return updated to the caller.
        return updated

    # Record lifecycle events using the inputs and processing steps below.
    # Input events: the supplied events.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def record_lifecycle_events(self, events):
        # Iterate over events.departed_vehicle_ids, binding each item to vehicle_id.
        for vehicle_id in events.departed_vehicle_ids:
            # Run this branch when the result of vehicle_id.startswith(the text 'AV_').
            if vehicle_id.startswith("AV_"):
                # Call self.record_actual_departure with the supplied arguments.
                self.record_actual_departure(vehicle_id, events.timestamp)
        # Iterate over events.arrived_vehicle_ids, binding each item to vehicle_id.
        for vehicle_id in events.arrived_vehicle_ids:
            # Run this branch when the result of vehicle_id.startswith(the text 'AV_').
            if vehicle_id.startswith("AV_"):
                # Call self.record_service_completion with the supplied arguments.
                self.record_service_completion(vehicle_id, events.timestamp)

    # Finalize episode using the inputs and processing steps below.
    # Input episode_end_time: the supplied episode end time.
    # Output: the result of self.get_all_records().
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def finalize_episode(self, episode_end_time):
        # Set end to a floating-point number built from episode_end_time.
        end = float(episode_end_time)
        # Run this branch when self._episode_end_time is a different object from None and end differs from
        # self._episode_end_time.
        if self._episode_end_time is not None and end != self._episode_end_time:
            # Raise DemandLedgerSemanticError with the text 'CONFLICTING_EPISODE_FINALIZATION_TIME' to stop this
            # execution path.
            raise DemandLedgerSemanticError("CONFLICTING_EPISODE_FINALIZATION_TIME")
        # Iterate over a tuple built from key/value pairs from self._records, binding each item to (vehicle_id,
        # record).
        for vehicle_id, record in tuple(self._records.items()):
            # Run this branch when record.service_completion_time is a different object from None.
            if record.service_completion_time is not None:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set status to VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END when
            # record.actual_departure_time is the same object as None, otherwise
            # VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END.
            status = (VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END
                      # Evaluate record.actual_departure_time is the same object as None as part of the enclosing
                      # expression.
                      if record.actual_departure_time is None else
                      # Evaluate VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END as part of the
                      # enclosing expression.
                      VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END)
            # Set self._records[vehicle_id] to the result of replace(record).
            self._records[vehicle_id] = replace(record, completion_status=status)
        # Set self._episode_end_time to end.
        self._episode_end_time = end
        # Return the result of self.get_all_records() to the caller.
        return self.get_all_records()

    # Get vehicle record using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Output: vehicle_id from self._records; use None if absent.
    def get_vehicle_record(self, vehicle_id):
        # Return vehicle_id from self._records; use None if absent to the caller.
        return self._records.get(vehicle_id)

    # Get all records using the inputs and processing steps below.
    # Output: a tuple built from a lazy sequence of self._records at key for key in the sorted values from
    # self._records.
    def get_all_records(self):
        # Return a tuple built from a lazy sequence of self._records at key for key in the sorted values from
        # self._records to the caller.
        return tuple(self._records[key] for key in sorted(self._records))

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary containing scheduled_vehicles, actual_departures_recorded,
    # service_completions_recorded,...
    def validation_summary(self):
        # Set records to the result of self.get_all_records().
        records = self.get_all_records()
        # Set count to a callback that returns the sum of a lazy sequence of item.completion_status is the same
        # object as status for item in records.
        count = lambda status: sum(item.completion_status is status for item in records)
        # Return a dictionary containing scheduled_vehicles, actual_departures_recorded,
        # service_completions_recorded,... to the caller.
        return {
            # Store the number of entries in records under 'scheduled_vehicles'.
            "scheduled_vehicles": len(records),
            # Store the sum of a lazy sequence of item.actual_departure_time is a different object from None for
            # item in records under 'actual_departures_recorded'.
            "actual_departures_recorded": sum(item.actual_departure_time is not None for item in records),
            # Store the sum of a lazy sequence of item.service_completion_time is a different object from None for
            # item in records under 'service_completions_recorded'.
            "service_completions_recorded": sum(item.service_completion_time is not None for item in records),
            # Store the result of count(VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END) under
            # 'scheduled_not_departed_at_episode_end'.
            "scheduled_not_departed_at_episode_end": count(VehicleDemandStatus.SCHEDULED_NOT_DEPARTED_AT_EPISODE_END),
            # Store the result of count(VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END) under
            # 'departed_not_completed_at_episode_end'.
            "departed_not_completed_at_episode_end": count(VehicleDemandStatus.DEPARTED_NOT_COMPLETED_AT_EPISODE_END),
            # Store the result of count(VehicleDemandStatus.SERVICE_COMPLETED) under 'completed_services'.
            "completed_services": count(VehicleDemandStatus.SERVICE_COMPLETED),
            # Store self._accounting_errors under 'accounting_errors'.
            "accounting_errors": self._accounting_errors,
        }

    # Require using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input code: the supplied code.
    # Output: record.
    # Processing: select branches using the stated conditions.
    def _require(self, vehicle_id, code):
        # Set record to vehicle_id from self._records; use None if absent.
        record = self._records.get(vehicle_id)
        # Run this branch when record is the same object as None.
        if record is None:
            # Update self._accounting_errors to its current value plus 1.
            self._accounting_errors += 1
            # Raise DemandLedgerSemanticError with code to stop this execution path.
            raise DemandLedgerSemanticError(code)
        # Return record to the caller.
        return record


# Set demand_ledger to the result of VehicleDemandLedger().
demand_ledger = VehicleDemandLedger()

