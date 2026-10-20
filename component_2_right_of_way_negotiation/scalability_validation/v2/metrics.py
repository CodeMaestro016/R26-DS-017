"""Observer measurements only; reuse stopping, guard and negotiation telemetry."""
# Import mean from statistics for the operations below.
from statistics import mean
# Import DEADLOCK_DURATION_SECONDS from config for the operations below.
from config import DEADLOCK_DURATION_SECONDS
# Import PanelTelemetry, STOP_PREFIX from targeted_validation.metrics for the operations below.
from targeted_validation.metrics import PanelTelemetry, STOP_PREFIX
# Import sources, INSERTION_TOLERANCE from .models for the operations below.
from .models import sources, INSERTION_TOLERANCE

# Insertion metrics using the inputs and processing steps below.
# Input measurements: the supplied measurements.
# Input end: the supplied end.
# Input storage: the supplied storage.
# Input controller_blocked: the supplied controller blocked.
# Input capacity_since: the supplied capacity since.
# Output: a dictionary built from the supplied values.
def insertion_metrics(measurements, end, storage, controller_blocked, capacity_since):
    # Set spawned to a dictionary of v mapped to row for (v, row) in key/value pairs from measurements; retain
    # entries satisfying row at 'actual_departure_seconds' is a different object from None.
    spawned = {v: row for v, row in measurements.items() if row["actual_departure_seconds"] is not None}
    # Set pending to a list of v for (v, row) in key/value pairs from measurements; retain entries satisfying row
    # at 'actual_departure_seconds' is the same object as None.
    pending = [v for v, row in measurements.items() if row["actual_departure_seconds"] is None]
    # Set delays to a dictionary of v mapped to row at 'actual_departure_seconds' minus row at
    # 'scheduled_departure_seconds' for (v, row) in key/value pairs from spawned.
    delays = {v: row["actual_departure_seconds"]-row["scheduled_departure_seconds"] for v, row in spawned.items()}
    # Set pending_approaches to a set of measurements[v]['movement_path_id'] at 0 for v in pending.
    pending_approaches = {measurements[v]["movement_path_id"][0] for v in pending}
    # The last schedule time must have elapsed. A blocked controller anywhere on
    # a pending stream prevents attributing its backlog to network-only capacity.
    # Set capacity to a Boolean built from pending and whether every item is true in a lazy sequence of end is at
    # least measurements[v]['scheduled_departure_seconds'] for v in pending and whether every item is true in a
    # lazy sequence of a not in controller_blocked and capacity_since.get(a) is not None and end -
    # capacity_since[a] >= DEADLOCK_DURATION_SECONDS for a in pending_approaches.
    capacity = bool(pending) and all(
        # Evaluate whether every item is true in a lazy sequence of a does not belong to controller_blocked and
        # capacity_since.get(a) is a different object from None and end - capacity_since[a] is at least
        # DEADLOCK_DURATION_SECONDS for a in pending_approaches as part of the enclosing expression.
        end >= measurements[v]["scheduled_departure_seconds"] for v in pending) and all(
        # Evaluate a does not belong to controller_blocked and a from capacity_since; use None if absent is a
        # different object from None and end minus capacity_since at a is at least DEADLOCK_DURATION_SECONDS as
        # part of the enclosing expression.
        a not in controller_blocked and capacity_since.get(a) is not None
        # Evaluate end minus capacity_since at a is at least DEADLOCK_DURATION_SECONDS as part of the enclosing
        # expression.
        and end-capacity_since[a] >= DEADLOCK_DURATION_SECONDS for a in pending_approaches)
    # Set cause to the text 'DEMONSTRATED_STATIC_STORAGE_LIMIT' when capacity, otherwise the text
    # 'CONTROLLER_BACKPRESSURE_OBSERVED' when pending_approaches intersected with a set built from
    # controller_blocked, otherwise the text 'INSERTION_CAUSE_NOT_ESTABLISHED' when pending, otherwise the text
    # 'ALL_SPAWNED'.
    cause = ("DEMONSTRATED_STATIC_STORAGE_LIMIT" if capacity else
             # Evaluate the text 'CONTROLLER_BACKPRESSURE_OBSERVED' when pending_approaches intersected with a set
             # built from controller_blocked, otherwise the text 'INSERTION_CAUSE_NOT_ESTABLISHED' when pending,
             # otherwise the text 'ALL_SPAWNED' as part of the enclosing expression.
             "CONTROLLER_BACKPRESSURE_OBSERVED" if pending_approaches & set(controller_blocked) else
             # Evaluate the text 'INSERTION_CAUSE_NOT_ESTABLISHED' when pending, otherwise the text 'ALL_SPAWNED'
             # as part of the enclosing expression.
             "INSERTION_CAUSE_NOT_ESTABLISHED" if pending else "ALL_SPAWNED")
    # Set completed to the sum of a lazy sequence of row at 'completion_seconds' is a different object from None
    # for row in values from measurements.
    completed = sum(row["completion_seconds"] is not None for row in measurements.values())
    # Return a dictionary built from the supplied values to the caller.
    return dict(scheduled_vehicle_count=len(measurements), successfully_spawned_vehicle_count=len(spawned),
        # Supply completed_vehicle_count as completed.
        # Supply insertion_delayed_vehicle_count as the sum of a lazy sequence of x is greater than
        # INSERTION_TOLERANCE plus 1e-09 for x in values from delays.
        completed_vehicle_count=completed, insertion_delayed_vehicle_count=sum(x > INSERTION_TOLERANCE+1e-9 for x in delays.values()),
        # Supply never_spawned_before_budget as the number of entries in pending.
        # Supply pending_vehicle_ids as pending.
        never_spawned_before_budget=len(pending), pending_vehicle_ids=pending,
        # Supply pending_requested_demand_lower_bound_seconds as a dictionary of v mapped to the maximum of 0.0,
        # end minus measurements[v] at 'scheduled_departure_seconds' for v in pending.
        pending_requested_demand_lower_bound_seconds={v: max(0., end-measurements[v]["scheduled_departure_seconds"]) for v in pending},
        # Supply actual_spawn_delay_seconds as delays.
        # Supply mean_insertion_delay_seconds as the result of mean(values from delays) when delays, otherwise
        # None.
        actual_spawn_delay_seconds=delays, mean_insertion_delay_seconds=mean(delays.values()) if delays else None,
        # Supply maximum_insertion_delay_seconds as the maximum of values from delays when delays, otherwise None.
        maximum_insertion_delay_seconds=max(delays.values()) if delays else None,
        # Supply completion_rate_among_scheduled as completed divided by the number of entries in measurements.
        completion_rate_among_scheduled=completed/len(measurements),
        # Supply completion_rate_among_spawned as completed divided by the number of entries in spawned when
        # spawned, otherwise None.
        completion_rate_among_spawned=completed/len(spawned) if spawned else None,
        # Supply unfinished_spawned_vehicles as the number of entries in spawned minus completed.
        unfinished_spawned_vehicles=len(spawned)-completed,
        # Supply spawned_vehicle_travel_exposure_seconds as the sum of a lazy sequence of
        # row['completion_seconds'] when row['completion_seconds'] is not None, otherwise end minus row at
        # 'actual_departure_seconds' for row in values from spawned.
        spawned_vehicle_travel_exposure_seconds=sum((row["completion_seconds"] if row["completion_seconds"] is not None else end)-row["actual_departure_seconds"] for row in spawned.values()),
        # Supply primary_network_capacity_limit_demonstrated as capacity.
        # Supply insertion_limitation_cause as cause.
        primary_network_capacity_limit_demonstrated=capacity, insertion_limitation_cause=cause,
        # Supply capacity_evidence as a dictionary built from the supplied values.
        # Supply static_storage_vehicles_per_approach as storage.
        capacity_evidence=dict(static_storage_vehicles_per_approach=storage,
            # Supply controller_held_approaches as the sorted values from controller_blocked.
            # Supply full_storage_since as capacity_since.
            controller_held_approaches=sorted(controller_blocked), full_storage_since=capacity_since,
            # Supply required_persistence_seconds as DEADLOCK_DURATION_SECONDS.
            required_persistence_seconds=DEADLOCK_DURATION_SECONDS),
        # Supply unspawned_demand_interpretation as the text 'Pending insertion is not a negotiation outcome;
        # completion...'.
        unspawned_demand_interpretation="Pending insertion is not a negotiation outcome; completion and unfinished counts among spawned are separate.")

# Define ScalabilityTelemetry to group the state and operations declared below.
# Base classes: PanelTelemetry.
# Instances expose the attributes and methods implemented in this class.
class ScalabilityTelemetry(PanelTelemetry):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input schedule: the supplied schedule.
    # Input proposed: the supplied proposed.
    # Input expected_sources: the supplied expected sources.
    # Input storage: the supplied storage.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, schedule, proposed=True, *, expected_sources, storage):
        # Call super().__init__ with the supplied arguments.
        super().__init__(schedule, proposed, budget_seconds=180., expected_panel_sources={})
        # Set self.expected_sources to expected_sources.
        self.expected_sources = expected_sources
        # Set self.storage to storage.
        self.storage = storage
        # Set self.controller_blocked to an empty set.
        self.controller_blocked = set()
        # Set self.capacity_since to the result of dict.fromkeys(the text 'NESW').
        self.capacity_since = dict.fromkeys("NESW")

    # Decision trace using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input admission_state: the supplied admission state.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def decision_trace(self, context, decision, admission_state):
        # Run this branch when decision.permission belongs to a set containing the text 'SAFE_HOLD', the text
        # 'BLOCKED_BY_PRECEDENCE'.
        if decision.permission in {"SAFE_HOLD", "BLOCKED_BY_PRECEDENCE"}:
            # Add self.movements[context.ego_id] at 0 to self.controller_blocked.
            self.controller_blocked.add(self.movements[context.ego_id][0])
        # Call super().decision_trace with the supplied arguments.
        super().decision_trace(context, decision, admission_state)

    # Observe using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Input states: the supplied states.
    # Input lifecycle: the supplied lifecycle.
    # Input movements: the supplied movements.
    # Input paths: the supplied paths.
    # Input zones: the supplied zones.
    # Input traci: the supplied traci.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def observe(self, now, states, lifecycle, movements, paths, zones, traci):
        # Iterate over the text 'NESW', binding each item to a.
        for a in "NESW":
            # Set count to the sum of a lazy sequence of movements[v][0] equals a and s['lane_id'] equals
            # paths.paths[movements[v]].incoming_lane_id for (v, s) in key/value pairs from states.
            count = sum(movements[v][0] == a and s["lane_id"] == paths.paths[movements[v]].incoming_lane_id for v,s in states.items())
            # Run this branch when count is less than self.storage at a.
            if count < self.storage[a]:
                # Set self.capacity_since[a] to None.
                self.capacity_since[a] = None
            # Run this branch when self.capacity_since at a is the same object as None.
            elif self.capacity_since[a] is None:
                # Set self.capacity_since[a] to now.
                self.capacity_since[a] = now
        # Read native collision and invariant monitoring; never issue vehicle commands.
        # Run this branch when the result of traci.simulation.getCollisions().
        if traci.simulation.getCollisions():
            # Set self.termination_reason to the text 'UNSAFE_FAILURE'.
            self.termination_reason = "UNSAFE_FAILURE"
        # Call super().observe with the supplied arguments.
        super().observe(now, states, lifecycle, movements, paths, zones, traci)

    # Finalize runtime using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Input error: the supplied error.
    # Output: a tuple containing runtime, error.
    # Processing: select branches using the stated conditions.
    def finalize_runtime(self, runtime, error):
        # Same exact observer-owned stop handling as PanelTelemetry, but an
        # independent study source inventory: do not modify the panel evaluator.
        # Set warnings to the result of self.trace_path.with_name(the text 'sumo_warnings.log') when
        # self.trace_path, otherwise None.
        warnings = self.trace_path.with_name("sumo_warnings.log") if self.trace_path else None
        # Set self.emergency_warning_count to the sum of a lazy sequence of 'emergency braking' belongs to
        # line.lower() for line in the result of warnings.read_text(errors='replace').splitlines() when warnings
        # and whether warnings is an existing file, otherwise 0.
        self.emergency_warning_count = sum("emergency braking" in line.lower() for line in warnings.read_text(errors="replace").splitlines()) if warnings and warnings.is_file() else 0
        # Run this branch when error equals STOP_PREFIX plus a string built from self.termination_reason.
        if error == STOP_PREFIX+str(self.termination_reason):
            # Set error to None.
            error = None
        # Run this branch when 'blocked_zone_violations' from runtime.get('metrics', {}); use 0 if absent.
        if runtime.get("metrics", {}).get("blocked_zone_violations", 0):
            # Set self.termination_reason to the text 'UNSAFE_FAILURE'.
            self.termination_reason = "UNSAFE_FAILURE"
        # Run this branch when self.termination_reason is the same object as None and the negation of error.
        if self.termination_reason is None and not error:
            # Set self.termination_reason to the text 'ALL_COMPLETED' when the number of entries in
            # self.completions equals the number of entries in self.waits, otherwise the text 'HARD_TIME_BUDGET'.
            self.termination_reason = "ALL_COMPLETED" if len(self.completions) == len(self.waits) else "HARD_TIME_BUDGET"
        # Run this branch when the result of sources() differs from self.expected_sources.
        if sources() != self.expected_sources:
            # Set error to the text 'EVALUATION_INTEGRITY_BREACH:SCALABILITY_SOURCES_CHANGED'.
            error = "EVALUATION_INTEGRITY_BREACH:SCALABILITY_SOURCES_CHANGED"
        # Return a tuple containing runtime, error to the caller.
        return runtime, error

    # Result using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Input aborted: the supplied aborted.
    # Output: metrics.
    def result(self, runtime, aborted=False):
        # Set metrics to the result of super().result(runtime, aborted).
        metrics = super().result(runtime, aborted)
        # Update metrics with the supplied entries.
        metrics.update(insertion_metrics(metrics["vehicle_measurements"], metrics["observed_simulation_time_seconds"], self.storage, self.controller_blocked, self.capacity_since))
        # Set metrics['deadlock_detected'] to self.termination_reason equals the text 'DEADLOCK_CONFIRMED'.
        metrics["deadlock_detected"] = self.termination_reason == "DEADLOCK_CONFIRMED"
        # Return metrics to the caller.
        return metrics
