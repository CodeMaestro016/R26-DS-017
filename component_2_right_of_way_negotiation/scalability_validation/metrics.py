"""Observer measurements only; reuse stopping, guard and negotiation telemetry."""
from statistics import mean
from config import DEADLOCK_DURATION_SECONDS
from targeted_validation.metrics import PanelTelemetry, STOP_PREFIX
from .models import sources, INSERTION_TOLERANCE

def insertion_metrics(measurements, end, storage, controller_blocked, capacity_since):
    spawned = {v: row for v, row in measurements.items() if row["actual_departure_seconds"] is not None}
    pending = [v for v, row in measurements.items() if row["actual_departure_seconds"] is None]
    delays = {v: row["actual_departure_seconds"]-row["scheduled_departure_seconds"] for v, row in spawned.items()}
    pending_approaches = {measurements[v]["movement_path_id"][0] for v in pending}
    # The last schedule time must have elapsed. A blocked controller anywhere on
    # a pending stream prevents attributing its backlog to network-only capacity.
    capacity = bool(pending) and all(
        end >= measurements[v]["scheduled_departure_seconds"] for v in pending) and all(
        a not in controller_blocked and capacity_since.get(a) is not None
        and end-capacity_since[a] >= DEADLOCK_DURATION_SECONDS for a in pending_approaches)
    cause = ("DEMONSTRATED_STATIC_STORAGE_LIMIT" if capacity else
             "CONTROLLER_BACKPRESSURE_OBSERVED" if pending_approaches & set(controller_blocked) else
             "INSERTION_CAUSE_NOT_ESTABLISHED" if pending else "ALL_SPAWNED")
    completed = sum(row["completion_seconds"] is not None for row in measurements.values())
    return dict(scheduled_vehicle_count=len(measurements), successfully_spawned_vehicle_count=len(spawned),
        completed_vehicle_count=completed, insertion_delayed_vehicle_count=sum(x > INSERTION_TOLERANCE+1e-9 for x in delays.values()),
        never_spawned_before_budget=len(pending), pending_vehicle_ids=pending,
        pending_requested_demand_lower_bound_seconds={v: max(0., end-measurements[v]["scheduled_departure_seconds"]) for v in pending},
        actual_spawn_delay_seconds=delays, mean_insertion_delay_seconds=mean(delays.values()) if delays else None,
        maximum_insertion_delay_seconds=max(delays.values()) if delays else None,
        completion_rate_among_scheduled=completed/len(measurements),
        completion_rate_among_spawned=completed/len(spawned) if spawned else None,
        unfinished_spawned_vehicles=len(spawned)-completed,
        spawned_vehicle_travel_exposure_seconds=sum((row["completion_seconds"] if row["completion_seconds"] is not None else end)-row["actual_departure_seconds"] for row in spawned.values()),
        primary_network_capacity_limit_demonstrated=capacity, insertion_limitation_cause=cause,
        capacity_evidence=dict(static_storage_vehicles_per_approach=storage,
            controller_held_approaches=sorted(controller_blocked), full_storage_since=capacity_since,
            required_persistence_seconds=DEADLOCK_DURATION_SECONDS),
        unspawned_demand_interpretation="Pending insertion is not a negotiation outcome; completion and unfinished counts among spawned are separate.")

class ScalabilityTelemetry(PanelTelemetry):
    def __init__(self, schedule, proposed=True, *, expected_sources, storage):
        super().__init__(schedule, proposed, budget_seconds=180., expected_panel_sources={})
        self.expected_sources = expected_sources
        self.storage = storage
        self.controller_blocked = set()
        self.capacity_since = dict.fromkeys("NESW")

    def decision_trace(self, context, decision, admission_state):
        if decision.permission in {"SAFE_HOLD", "BLOCKED_BY_PRECEDENCE"}:
            self.controller_blocked.add(self.movements[context.ego_id][0])
        super().decision_trace(context, decision, admission_state)

    def observe(self, now, states, lifecycle, movements, paths, zones, traci):
        for a in "NESW":
            count = sum(movements[v][0] == a and s["lane_id"] == paths.paths[movements[v]].incoming_lane_id for v,s in states.items())
            if count < self.storage[a]:
                self.capacity_since[a] = None
            elif self.capacity_since[a] is None:
                self.capacity_since[a] = now
        # Read native collision and invariant monitoring; never issue vehicle commands.
        if traci.simulation.getCollisions():
            self.termination_reason = "UNSAFE_FAILURE"
        super().observe(now, states, lifecycle, movements, paths, zones, traci)

    def finalize_runtime(self, runtime, error):
        # Same exact observer-owned stop handling as PanelTelemetry, but an
        # independent study source inventory: do not modify the panel evaluator.
        warnings = self.trace_path.with_name("sumo_warnings.log") if self.trace_path else None
        self.emergency_warning_count = sum("emergency braking" in line.lower() for line in warnings.read_text(errors="replace").splitlines()) if warnings and warnings.is_file() else 0
        if error == STOP_PREFIX+str(self.termination_reason):
            error = None
        if runtime.get("metrics", {}).get("blocked_zone_violations", 0):
            self.termination_reason = "UNSAFE_FAILURE"
        if self.termination_reason is None and not error:
            self.termination_reason = "ALL_COMPLETED" if len(self.completions) == len(self.waits) else "HARD_TIME_BUDGET"
        if sources() != self.expected_sources:
            error = "EVALUATION_INTEGRITY_BREACH:SCALABILITY_SOURCES_CHANGED"
        return runtime, error

    def result(self, runtime, aborted=False):
        metrics = super().result(runtime, aborted)
        metrics.update(insertion_metrics(metrics["vehicle_measurements"], metrics["observed_simulation_time_seconds"], self.storage, self.controller_blocked, self.capacity_since))
        metrics["deadlock_detected"] = self.termination_reason == "DEADLOCK_CONFIRMED"
        return metrics
