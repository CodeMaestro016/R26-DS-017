"""Observer-only stopping and presentation semantics; no vehicle mutations."""
# Import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
# Import Telemetry from post_training_evaluation.metrics for the operations below.
from post_training_evaluation.metrics import Telemetry
# Import panel_sources from .models for the operations below.
from .models import panel_sources

# Set STOP_PREFIX to the text 'PANEL_EVALUATOR_STOP:'.
STOP_PREFIX = "PANEL_EVALUATOR_STOP:"

# Define PanelTelemetry to group the state and operations declared below.
# Base classes: Telemetry.
# Instances expose the attributes and methods implemented in this class.
class PanelTelemetry(Telemetry):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input schedule: the supplied schedule.
    # Input proposed: the supplied proposed.
    # Input budget_seconds: the supplied budget seconds.
    # Input expected_panel_sources: the supplied expected panel sources.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, schedule, proposed=True, *, budget_seconds, expected_panel_sources):
        # Call super().__init__ with the supplied arguments.
        super().__init__(schedule, proposed)
        # Set self.budget to budget_seconds.
        self.budget = budget_seconds
        # Set self.expected_panel_sources to expected_panel_sources.
        self.expected_panel_sources = expected_panel_sources
        # Set self.termination_reason to None.
        self.termination_reason = None
        # Set self.deadlock_cause to None.
        self.deadlock_cause = None
        # Set self.held_since to None.
        self.held_since = None
        # Set self.frame_decisions to an empty dictionary.
        self.frame_decisions = {}
        # Set self.last_statuses to an empty dictionary.
        self.last_statuses = {}
        # Set self.max_active and self.max_moving to 0.
        self.max_active = self.max_moving = 0
        # Set self.max_depth to the result of dict.fromkeys(the text 'NESW', 0).
        self.max_depth = dict.fromkeys("NESW", 0)

    # Coordination trace using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Input snapshots: the supplied snapshots.
    # Input observations: the supplied observations.
    # Output: no explicit value; normal completion returns None.
    def coordination_trace(self, now, snapshots, observations):
        # Set self.last_statuses to a dictionary of s at 'ego_id' mapped to 'negotiation_status' from s; use None
        # if absent for s in snapshots.
        self.last_statuses = {s["ego_id"]: s.get("negotiation_status") for s in snapshots}
        # Call super().coordination_trace with the supplied arguments.
        super().coordination_trace(now, snapshots, observations)

    # Decision trace using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input admission_state: the supplied admission state.
    # Output: no explicit value; normal completion returns None.
    def decision_trace(self, context, decision, admission_state):
        # Set self.frame_decisions[context.ego_id] to a tuple containing decision.permission, decision.reason,
        # admission_state.
        self.frame_decisions[context.ego_id] = (decision.permission, decision.reason, admission_state)
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
        # Call super().observe with the supplied arguments.
        super().observe(now, states, lifecycle, movements, paths, zones, traci)
        # Set self.max_active to the maximum of self.max_active, the number of entries in states.
        self.max_active = max(self.max_active, len(states))
        # Set self.max_moving to the maximum of self.max_moving, the sum of a lazy sequence of s['speed'] is at
        # least...
        self.max_moving = max(self.max_moving, sum(s["speed"] >= STOPPED_SPEED_THRESHOLD_MPS for s in states.values()))
        # Iterate over the text 'NESW', binding each item to a.
        for a in "NESW":
            # Set depth to the sum of a lazy sequence of movements[v][0] equals a and s['lane_id'] equals
            # paths.paths[movements[v]].incoming_lane_id for (v, s) in key/value pairs from states.
            depth = sum(movements[v][0] == a and s["lane_id"] == paths.paths[movements[v]].incoming_lane_id for v, s in states.items())
            # Set self.max_depth[a] to the maximum of self.max_depth at a, depth.
            self.max_depth[a] = max(self.max_depth[a], depth)
        # Set reason to None.
        reason = None
        # Run this branch when self.collisions.
        if self.collisions:
            # Set reason to the text 'UNSAFE_FAILURE'.
            reason = "UNSAFE_FAILURE"
        # Run this branch when the number of entries in self.completions equals the number of entries in
        # self.waits.
        elif len(self.completions) == len(self.waits):
            # Set reason to the text 'ALL_COMPLETED'.
            reason = "ALL_COMPLETED"
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set signature to a tuple built from the sorted values from a lazy sequence of a tuple containing v,
            # s['lane_id'], s.get('lane_position'), s.get('position'), self.frame_decisions.get(v),... for (v, s)
            # in key/value pairs from states.
            signature = tuple(sorted((v, s["lane_id"], s.get("lane_position"),
                # Include v from self.frame_decisions; use None if absent in this tuple.
                s.get("position"), self.frame_decisions.get(v), self.last_statuses.get(v))
                # Evaluate key/value pairs from states as part of the enclosing expression.
                for v, s in states.items()))
            # Set all_blocked to a Boolean built from states and whether every item is true in a lazy sequence of
            # s['speed'] < STOPPED_SPEED_THRESHOLD_MPS and s['lane_id'] ==
            # paths.paths[movements[v]].incoming_lane_id and self.frame_decisions.get(v, (None,))[0] in
            # {'SAFE_HOLD', 'BLOCKED_BY_PRECEDENCE'} and self.frame_decisions[v][2] not in {'COMMITTED_TO_ENTER',
            # 'IN_CONFLICT_ZONE', 'CLEARED'} for (v, s) in key/value pairs from states.
            all_blocked = bool(states) and all(
                # Evaluate s at 'speed' is less than STOPPED_SPEED_THRESHOLD_MPS and s at 'lane_id' equals
                # paths.paths[movements[v]].incoming_lane_id and self.frame_decisions.get(v, (None,)) at 0 belongs
                # to a set containing the text 'SAFE_HOLD', the text 'BLOCKED_BY_PRECEDENCE' and
                # self.frame_decisions[v] at 2 does not belong to a set containing the text 'COMMITTED_TO_ENTER',
                # the text 'IN_CONFLICT_ZONE', the text 'CLEARED' as part of the enclosing expression.
                s["speed"] < STOPPED_SPEED_THRESHOLD_MPS and
                # Evaluate s at 'lane_id' equals paths.paths[movements[v]].incoming_lane_id as part of the
                # enclosing expression.
                s["lane_id"] == paths.paths[movements[v]].incoming_lane_id and
                # Evaluate self.frame_decisions.get(v, (None,)) at 0 belongs to a set containing the text
                # 'SAFE_HOLD', the text 'BLOCKED_BY_PRECEDENCE' as part of the enclosing expression.
                self.frame_decisions.get(v, (None,))[0] in {"SAFE_HOLD", "BLOCKED_BY_PRECEDENCE"} and
                # Evaluate self.frame_decisions[v] at 2 does not belong to a set containing the text
                # 'COMMITTED_TO_ENTER', the text 'IN_CONFLICT_ZONE', the text 'CLEARED' as part of the enclosing
                # expression.
                self.frame_decisions[v][2] not in {"COMMITTED_TO_ENTER", "IN_CONFLICT_ZONE", "CLEARED"}
                # Evaluate key/value pairs from states as part of the enclosing expression.
                for v, s in states.items())
            # Set stationary to the number of entries in self.departures equals the number of entries in
            # self.waits and all_blocked and the negation of lifecycle.arrived_vehicle_ids.
            stationary = len(self.departures) == len(self.waits) and all_blocked and not lifecycle.arrived_vehicle_ids
            # Run this branch when the negation of stationary or signature differs from the requested attribute of
            # self.
            if not stationary or signature != getattr(self, "held_signature", None):
                # Set self.held_since to now when stationary, otherwise None.
                self.held_since = now if stationary else None
                # Set self.held_signature to signature.
                self.held_signature = signature
            # Run this branch when self.deadlock_observed and self.held_since is a different object from None and
            # now minus self.held_since is at least DEADLOCK_DURATION_SECONDS.
            if (self.deadlock_observed and self.held_since is not None and
                    # Evaluate now minus self.held_since is at least DEADLOCK_DURATION_SECONDS as part of the
                    # enclosing expression.
                    now - self.held_since >= DEADLOCK_DURATION_SECONDS):
                # Set reason to the text 'DEADLOCK_CONFIRMED'.
                reason = "DEADLOCK_CONFIRMED"
                # Set self.deadlock_cause to a dictionary built from the supplied values.
                self.deadlock_cause = dict(statuses=self.last_statuses, decisions=self.frame_decisions,
                    # Supply existing_threshold_seconds as DEADLOCK_DURATION_SECONDS.
                    existing_threshold_seconds=DEADLOCK_DURATION_SECONDS,
                    # Supply stable_all_held_since as self.held_since.
                    # Supply confirmed_at as now.
                    stable_all_held_since=self.held_since, confirmed_at=now)
        # Set self.frame_decisions to an empty dictionary.
        self.frame_decisions = {}
        # Run this branch when reason.
        if reason:
            # Set self.termination_reason to reason.
            self.termination_reason = reason
            # Raise RuntimeError with STOP_PREFIX plus reason to stop this execution path.
            raise RuntimeError(STOP_PREFIX + reason)

    # Finalize runtime using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Input error: the supplied error.
    # Output: a tuple containing runtime, error.
    # Processing: select branches using the stated conditions.
    def finalize_runtime(self, runtime, error):
        # Set warnings to the result of self.trace_path.with_name(the text 'sumo_warnings.log') when
        # self.trace_path, otherwise None.
        warnings = self.trace_path.with_name("sumo_warnings.log") if self.trace_path else None
        # Set self.emergency_warning_count to the sum of a lazy sequence of 'emergency braking' belongs to
        # line.lower() for line in the result of warnings.read_text(encoding='utf-8',
        # errors='replace').splitlines() when warnings and whether warnings is an existing file, otherwise 0.
        self.emergency_warning_count = sum("emergency braking" in line.lower() for line in warnings.read_text(encoding="utf-8", errors="replace").splitlines()) if warnings and warnings.is_file() else 0
        # Run this branch when error equals STOP_PREFIX plus a string built from self.termination_reason.
        if error == STOP_PREFIX + str(self.termination_reason):
            # Set error to None.
            error = None  # Only the exact observer-owned stop token is handled.
        # Set m to 'metrics' from runtime; use an empty dictionary if absent.
        m = runtime.get("metrics", {})
        # Run this branch when 'blocked_zone_violations' from m; use 0 if absent.
        if m.get("blocked_zone_violations", 0):
            # Set self.termination_reason to the text 'UNSAFE_FAILURE'.
            self.termination_reason = "UNSAFE_FAILURE"
        # Run this branch when self.termination_reason is the same object as None and the negation of error.
        if self.termination_reason is None and not error:
            # Set self.termination_reason to the text 'ALL_COMPLETED' when the number of entries in
            # self.completions equals the number of entries in self.waits, otherwise the text 'HARD_TIME_BUDGET'.
            self.termination_reason = "ALL_COMPLETED" if len(self.completions) == len(self.waits) else "HARD_TIME_BUDGET"
        # Run this branch when the result of panel_sources() differs from self.expected_panel_sources.
        if panel_sources() != self.expected_panel_sources:
            # Set error to the text 'EVALUATION_INTEGRITY_BREACH:PANEL_SOURCES_CHANGED'.
            error = "EVALUATION_INTEGRITY_BREACH:PANEL_SOURCES_CHANGED"
        # Return a tuple containing runtime, error to the caller.
        return runtime, error

    # Result using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Input aborted: the supplied aborted.
    # Output: m.
    def result(self, runtime, aborted=False):
        # Set m to the result of super().result(runtime, aborted).
        m = super().result(runtime, aborted)
        # Update m with the supplied entries.
        m.update(termination_reason=self.termination_reason, deadlock_cause=self.deadlock_cause,
            # Supply emergency_braking_warning_count as the requested attribute of self.
            emergency_braking_warning_count=getattr(self, "emergency_warning_count", None),
            # Supply timeout as self.termination_reason equals the text 'HARD_TIME_BUDGET' and a Boolean built
            # from m at 'unfinished_vehicles'.
            timeout=self.termination_reason == "HARD_TIME_BUDGET" and bool(m["unfinished_vehicles"]),
            # Supply deadlock_observed as self.deadlock_observed.
            deadlock_observed=self.deadlock_observed,
            # Supply maximum_simultaneous_active_vehicles as the maximum of self.max_active,
            # 'maximum_simultaneous_active_vehicles' from m; use 0 if absent.
            maximum_simultaneous_active_vehicles=max(self.max_active, m.get("maximum_simultaneous_active_vehicles", 0)),
            # Supply maximum_simultaneously_moving_vehicles as the maximum of self.max_moving,
            # 'maximum_simultaneously_moving_vehicles' from m; use 0 if absent.
            maximum_simultaneously_moving_vehicles=max(self.max_moving, m.get("maximum_simultaneously_moving_vehicles", 0)),
            # Supply maximum_per_approach_queue_depth as self.max_depth.
            maximum_per_approach_queue_depth=self.max_depth)
        # Set events to 'mappo_negotiation_events' from m; use 0 if absent.
        events = m.get("mappo_negotiation_events", 0)
        # Set m['fallback_rate'] to 'fallback_activations' from m; use 0 if absent divided by events when events,
        # otherwise None.
        m["fallback_rate"] = m.get("fallback_activations", 0) / events if events else None
        # Return m to the caller.
        return m
