"""Observer-only stopping and presentation semantics; no vehicle mutations."""
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
from post_training_evaluation.metrics import Telemetry
from .models import panel_sources

STOP_PREFIX = "PANEL_EVALUATOR_STOP:"

class PanelTelemetry(Telemetry):
    def __init__(self, schedule, proposed=True, *, budget_seconds, expected_panel_sources):
        super().__init__(schedule, proposed)
        self.budget = budget_seconds
        self.expected_panel_sources = expected_panel_sources
        self.termination_reason = None
        self.deadlock_cause = None
        self.held_since = None
        self.frame_decisions = {}
        self.last_statuses = {}
        self.max_active = self.max_moving = 0
        self.max_depth = dict.fromkeys("NESW", 0)

    def coordination_trace(self, now, snapshots, observations):
        self.last_statuses = {s["ego_id"]: s.get("negotiation_status") for s in snapshots}
        super().coordination_trace(now, snapshots, observations)

    def decision_trace(self, context, decision, admission_state):
        self.frame_decisions[context.ego_id] = (decision.permission, decision.reason, admission_state)
        super().decision_trace(context, decision, admission_state)

    def observe(self, now, states, lifecycle, movements, paths, zones, traci):
        super().observe(now, states, lifecycle, movements, paths, zones, traci)
        self.max_active = max(self.max_active, len(states))
        self.max_moving = max(self.max_moving, sum(s["speed"] >= STOPPED_SPEED_THRESHOLD_MPS for s in states.values()))
        for a in "NESW":
            depth = sum(movements[v][0] == a and s["lane_id"] == paths.paths[movements[v]].incoming_lane_id for v, s in states.items())
            self.max_depth[a] = max(self.max_depth[a], depth)
        reason = None
        if self.collisions:
            reason = "UNSAFE_FAILURE"
        elif len(self.completions) == len(self.waits):
            reason = "ALL_COMPLETED"
        else:
            signature = tuple(sorted((v, s["lane_id"], s.get("lane_position"),
                s.get("position"), self.frame_decisions.get(v), self.last_statuses.get(v))
                for v, s in states.items()))
            all_blocked = bool(states) and all(
                s["speed"] < STOPPED_SPEED_THRESHOLD_MPS and
                s["lane_id"] == paths.paths[movements[v]].incoming_lane_id and
                self.frame_decisions.get(v, (None,))[0] in {"SAFE_HOLD", "BLOCKED_BY_PRECEDENCE"} and
                self.frame_decisions[v][2] not in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE", "CLEARED"}
                for v, s in states.items())
            stationary = len(self.departures) == len(self.waits) and all_blocked and not lifecycle.arrived_vehicle_ids
            if not stationary or signature != getattr(self, "held_signature", None):
                self.held_since = now if stationary else None
                self.held_signature = signature
            if (self.deadlock_observed and self.held_since is not None and
                    now - self.held_since >= DEADLOCK_DURATION_SECONDS):
                reason = "DEADLOCK_CONFIRMED"
                self.deadlock_cause = dict(statuses=self.last_statuses, decisions=self.frame_decisions,
                    existing_threshold_seconds=DEADLOCK_DURATION_SECONDS,
                    stable_all_held_since=self.held_since, confirmed_at=now)
        self.frame_decisions = {}
        if reason:
            self.termination_reason = reason
            raise RuntimeError(STOP_PREFIX + reason)

    def finalize_runtime(self, runtime, error):
        warnings = self.trace_path.with_name("sumo_warnings.log") if self.trace_path else None
        self.emergency_warning_count = sum("emergency braking" in line.lower() for line in warnings.read_text(encoding="utf-8", errors="replace").splitlines()) if warnings and warnings.is_file() else 0
        if error == STOP_PREFIX + str(self.termination_reason):
            error = None  # Only the exact observer-owned stop token is handled.
        m = runtime.get("metrics", {})
        if m.get("blocked_zone_violations", 0):
            self.termination_reason = "UNSAFE_FAILURE"
        if self.termination_reason is None and not error:
            self.termination_reason = "ALL_COMPLETED" if len(self.completions) == len(self.waits) else "HARD_TIME_BUDGET"
        if panel_sources() != self.expected_panel_sources:
            error = "EVALUATION_INTEGRITY_BREACH:PANEL_SOURCES_CHANGED"
        return runtime, error

    def result(self, runtime, aborted=False):
        m = super().result(runtime, aborted)
        m.update(termination_reason=self.termination_reason, deadlock_cause=self.deadlock_cause,
            emergency_braking_warning_count=getattr(self, "emergency_warning_count", None),
            timeout=self.termination_reason == "HARD_TIME_BUDGET" and bool(m["unfinished_vehicles"]),
            deadlock_observed=self.deadlock_observed,
            maximum_simultaneous_active_vehicles=max(self.max_active, m.get("maximum_simultaneous_active_vehicles", 0)),
            maximum_simultaneously_moving_vehicles=max(self.max_moving, m.get("maximum_simultaneously_moving_vehicles", 0)),
            maximum_per_approach_queue_depth=self.max_depth)
        events = m.get("mappo_negotiation_events", 0)
        m["fallback_rate"] = m.get("fallback_activations", 0) / events if events else None
        return m
