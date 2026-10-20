"""Post-training measurements; no policy inputs, rewards, or permissions."""
# Import mean, median from statistics for the operations below.
from statistics import mean, median
# Import combinations from itertools for the operations below.
from itertools import combinations
# Import json for use in this module.
import json
# Import numpy as np for use in this module.
import numpy as np
# Import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS, DEADLOCK_DURATION_SECONDS from config for the operations
# below.
from config import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS, DEADLOCK_DURATION_SECONDS
# Import VehicleDemandLedger from traffic_accounting.demand_ledger for the operations below.
from traffic_accounting.demand_ledger import VehicleDemandLedger
# Import DemandScheduleSource from traffic_accounting.models for the operations below.
from traffic_accounting.models import DemandScheduleSource
# Import interval_vehicle_exposures, team_interval_cost_seconds from negotiation_objective.accounting for the
# operations below.
from negotiation_objective.accounting import interval_vehicle_exposures, team_interval_cost_seconds

# Statistics using the inputs and processing steps below.
# Input values: the supplied values.
# Output: a dictionary containing mean, median, p95, maximum.
def statistics(values):
    # Set values to a list built from values.
    values = list(values)
    # Return a dictionary containing mean, median, p95, maximum to the caller.
    return {"mean": mean(values) if values else None,
        # Store the result of median(values) when values, otherwise None under 'median'.
        "median": median(values) if values else None,
        # Store a floating-point number built from the result of np.percentile(values, 95) when values, otherwise
        # None under 'p95'.
        "p95": float(np.percentile(values, 95, method="linear")) if values else None,
        # Store the maximum of values when values, otherwise None under 'maximum'.
        "maximum": max(values) if values else None}

# Inversion rate using the inputs and processing steps below.
# Input arrivals: the supplied arrivals.
# Input services: the supplied services.
# Input conflicts: the supplied conflicts.
# Output: a tuple containing inverted divided by the number of entries in pairs when pairs, otherwise None,
# inverted, the number of...
def inversion_rate(arrivals, services, conflicts):
    # Set pairs to a list of a tuple containing a, b for (a, b) in conflicts; retain entries satisfying a belongs
    # to arrivals and b belongs to arrivals and a belongs to services and b...
    pairs = [(a, b) for a, b in conflicts if a in arrivals and b in arrivals
             # Evaluate a belongs to services as part of the enclosing expression.
             and a in services and b in services]
    # Set inverted to the sum of a lazy sequence of (arrivals[a], a) is less than (arrivals[b], b) differs from
    # (services[a], a) is less than (services[b], b) for (a, b) in pairs.
    inverted = sum(((arrivals[a], a) < (arrivals[b], b)) !=
                   # Evaluate a tuple containing services at a, a is less than a tuple containing services at b, b
                   # as part of the enclosing expression.
                   ((services[a], a) < (services[b], b)) for a, b in pairs)
    # Return a tuple containing inverted divided by the number of entries in pairs when pairs, otherwise None,
    # inverted, the number of... to the caller.
    return (inverted / len(pairs) if pairs else None), inverted, len(pairs)

# Define Telemetry to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class Telemetry:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input schedule: the supplied schedule.
    # Input proposed: the supplied proposed.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __init__(self, schedule, proposed=True):
        # Set self.schedule to schedule.
        self.schedule = schedule
        # Set self.proposed to proposed.
        self.proposed = proposed
        # Set (self.arrivals, self.services, self.departures, self.completions) to a tuple containing an empty
        # dictionary, an empty dictionary, an empty dictionary, an empty dictionary.
        self.arrivals, self.services, self.departures, self.completions = {}, {}, {}, {}
        # Set (self.waits, self.stopped_since, self.movements) to a tuple containing an empty dictionary, an empty
        # dictionary, an empty dictionary.
        self.waits, self.stopped_since, self.movements = {}, {}, {}
        # Set (self.inference_ns, self.execution_ns) to a tuple containing an empty list, an empty list.
        self.inference_ns, self.execution_ns = [], []
        # Set (self.emergency_events, self.emergency_prior, self.emergency_evidence) to a tuple containing 0, an
        # empty set, an empty list.
        self.emergency_events, self.emergency_prior, self.emergency_evidence = 0, set(), []
        # Set (self.collisions, self.collision_evidence, self.deadlock_observed) to a tuple containing 0, an empty
        # list, False.
        self.collisions, self.collision_evidence, self.deadlock_observed = 0, [], False
        # Set self.conflicts to an empty list.
        self.conflicts = []
        # Set self.ledger to the result of VehicleDemandLedger().
        self.ledger = VehicleDemandLedger()
        # Set self.now to 0.0.
        self.now = 0.
        # Set self.trace_path to None.
        self.trace_path = None
        # Iterate over key/value pairs from schedule, binding each item to (approach, rows).
        for approach, rows in schedule.items():
            # Iterate over rows, binding each item to row.
            for row in rows:
                # Set ego to formatted text built from the embedded values.
                ego = f"PANEL_AV_{approach}_{row.sequence_index + 1:02d}"
                # Set self.waits[ego] to 0.0.
                self.waits[ego] = 0.
                # Set self.movements[ego] to row.movement_path_id.
                self.movements[ego] = row.movement_path_id
                # Call self.ledger.register_scheduled_vehicle with the supplied arguments.
                self.ledger.register_scheduled_vehicle(ego, row.scheduled_departure_seconds,
                    # Supply DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE to
                    # self.ledger.register_scheduled_vehicle.
                    DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE,
                    # Store the text 'EXOGENOUS_FROZEN_FINAL_EVALUATION' under 'clock'.
                    provenance={"clock": "EXOGENOUS_FROZEN_FINAL_EVALUATION"})

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
        # Run this branch when self.trace_path.
        if self.trace_path:
            # Call self._trace with the supplied arguments.
            self._trace({"event": "PHYSICAL_STATE", "timestamp": now,
                # Store states under 'states'.
                # Store movements under 'movements'.
                "states": states, "movements": movements})
        # Run this branch when the result of traci.simulation.getStartingTeleportIDList().
        if traci.simulation.getStartingTeleportIDList():
            # Raise RuntimeError with the text 'EVALUATION_TELEPORT_OBSERVED' to stop this execution path.
            raise RuntimeError("EVALUATION_TELEPORT_OBSERVED")
        # Set dt to now minus self.now.
        dt = now - self.now
        # Set self.now to now.
        self.now = now
        # Iterate over lifecycle.departed_vehicle_ids, binding each item to ego.
        for ego in lifecycle.departed_vehicle_ids:
            # Run this branch when ego belongs to self.waits.
            if ego in self.waits:
                # Set self.departures[ego] to now.
                self.departures[ego] = now
                # Call self.ledger.record_actual_departure with the supplied arguments.
                self.ledger.record_actual_departure(ego, now)
        # Iterate over lifecycle.arrived_vehicle_ids, binding each item to ego.
        for ego in lifecycle.arrived_vehicle_ids:
            # Run this branch when ego belongs to self.waits.
            if ego in self.waits:
                # Set self.completions[ego] to now.
                self.completions[ego] = now
                # Call self.ledger.record_service_completion with the supplied arguments.
                self.ledger.record_service_completion(ego, now)
        # Set braking to an empty set.
        braking = set()
        # Iterate over key/value pairs from states, binding each item to (ego, state).
        for ego, state in states.items():
            # Set path to paths.paths at movements[ego].
            path = paths.paths[movements[ego]]
            # Run this branch when state at 'lane_id' equals path.incoming_lane_id.
            if state["lane_id"] == path.incoming_lane_id:
                # Call self.arrivals.setdefault with the supplied arguments.
                self.arrivals.setdefault(ego, now)  # Entry to existing incoming lane.
                # Run this branch when state at 'speed' is less than STOPPED_SPEED_THRESHOLD_MPS.
                if state["speed"] < STOPPED_SPEED_THRESHOLD_MPS:
                    # Update self.waits[ego] to its current value plus dt.
                    self.waits[ego] += dt
                    # Call self.stopped_since.setdefault with the supplied arguments.
                    self.stopped_since.setdefault(ego, now - dt)
                    # Run this branch when now minus self.stopped_since at ego is at least
                    # DEADLOCK_DURATION_SECONDS.
                    if now - self.stopped_since[ego] >= DEADLOCK_DURATION_SECONDS:
                        # Set self.deadlock_observed to True.
                        self.deadlock_observed = True
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Remove the requested entry from self.stopped_since.
                    self.stopped_since.pop(ego, None)
            # Run this branch when ego belongs to self.arrivals.
            elif ego in self.arrivals:
                # Call self.services.setdefault with the supplied arguments.
                self.services.setdefault(ego, now)  # Front bumper leaves incoming lane.
            # Run this branch when 'accel' from state; use 0.0 if absent is less than the negative of state at
            # 'comfortable_deceleration_mps2' minus 1e-06.
            if state.get("accel", 0.) < -state["comfortable_deceleration_mps2"] - 1e-6:
                # Add ego to braking.
                braking.add(ego)
                # Run this branch when ego does not belong to self.emergency_prior.
                if ego not in self.emergency_prior:
                    # Append a dictionary containing vehicle_id, timestamp, acceleration_mps2,
                    # comfortable_deceleration_mps2 to self.emergency_evidence.
                    self.emergency_evidence.append({"vehicle_id": ego, "timestamp": now,
                        # Store state at 'accel' under 'acceleration_mps2'.
                        "acceleration_mps2": state["accel"],
                        # Store state at 'comfortable_deceleration_mps2' under 'comfortable_deceleration_mps2'.
                        "comfortable_deceleration_mps2": state["comfortable_deceleration_mps2"]})
        # Update self.emergency_events to its current value plus the number of entries in braking minus
        # self.emergency_prior.
        self.emergency_events += len(braking - self.emergency_prior)
        # Set self.emergency_prior to braking.
        self.emergency_prior = braking
        # Set collisions to a tuple built from the result of traci.simulation.getCollisions().
        collisions = tuple(traci.simulation.getCollisions())
        # Update self.collisions to its current value plus the number of entries in collisions.
        self.collisions += len(collisions)
        # Extend self.collision_evidence with a lazy sequence of a dictionary containing timestamp, collider,
        # victim, type for c in collisions.
        self.collision_evidence.extend({"timestamp": now, "collider": c.collider,
            # Store c.victim under 'victim'.
            # Store c.type under 'type'.
            "victim": c.victim, "type": c.type} for c in collisions)
        # Set self.conflicts to a list of a tuple containing a, b for (a, b) in the result of combinations(the
        # sorted values from self.movements, 2); retain entries satisfying self.movements[a] at 0 differs from
        # self.movements[b] at 0 and the result of...
        self.conflicts = [(a, b) for a, b in combinations(sorted(self.movements), 2)
            # Evaluate self.movements[a] at 0 differs from self.movements[b] at 0 and the result of
            # zones.zone_record(self.movements at a, 1.8, self.movements at b, 1.8) is a different object from
            # None as part of the enclosing expression.
            if self.movements[a][0] != self.movements[b][0] and zones.zone_record(
                # Supply self.movements at a to zones.zone_record.
                self.movements[a], 1.8, self.movements[b], 1.8) is not None]

    # Inference using the inputs and processing steps below.
    # Input ns: the supplied ns.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def inference(self, ns):
        # Run this branch when self.proposed.
        if self.proposed:
            # Append ns to self.inference_ns.
            self.inference_ns.append(ns)

    # Execution using the inputs and processing steps below.
    # Input ns: the supplied ns.
    # Input decision: the supplied decision.
    # Output: no explicit value; normal completion returns None.
    def execution(self, ns, decision):
        # Append ns to self.execution_ns.
        self.execution_ns.append(ns)

    # Trace using the inputs and processing steps below.
    # Input record: the supplied record.
    # Output: no explicit value; normal completion returns None.
    def _trace(self, record):
        # Import normalize_nonfinite from .models for the operations below.
        from .models import normalize_nonfinite
        # Enter the result of self.trace_path.open(the text 'a') as handle and run the enclosed operations within
        # that context.
        with self.trace_path.open("a", encoding="utf-8") as handle:
            # Call handle.write with the supplied arguments.
            handle.write(json.dumps(normalize_nonfinite(record), default=str, allow_nan=False) + "\n")

    # Coordination trace using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Input snapshots: the supplied snapshots.
    # Input observations: the supplied observations.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def coordination_trace(self, now, snapshots, observations):
        # Run this branch when self.trace_path.
        if self.trace_path:
            # Call self._trace with the supplied arguments.
            self._trace({"event": "COORDINATION_SOURCE", "timestamp": now,
                # Store snapshots under 'snapshots'.
                # Store a dictionary of s at 'ego_id' mapped to a dictionary built from the supplied values for s
                # in snapshots under 'local_evidence'.
                "snapshots": snapshots, "local_evidence": {
                    # Evaluate a dictionary built from the supplied values as part of the enclosing expression.
                    s["ego_id"]: dict(
                        # Supply conflict as the result of
                        # observations.get_ldm(s['ego_id']).get_current_conflict_graph().
                        conflict=observations.get_ldm(s["ego_id"]).get_current_conflict_graph(),
                        # Supply regulatory as the result of
                        # observations.get_ldm(s['ego_id']).get_current_regulatory_assessment().
                        regulatory=observations.get_ldm(s["ego_id"]).get_current_regulatory_assessment(),
                        # Supply temporal as the result of
                        # observations.get_ldm(s['ego_id']).get_current_temporal_assessment().
                        temporal=observations.get_ldm(s["ego_id"]).get_current_temporal_assessment()) for s in snapshots}})

    # Decision trace using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input admission_state: the supplied admission state.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def decision_trace(self, context, decision, admission_state):
        # Run this branch when self.trace_path.
        if self.trace_path:
            # Call self._trace with the supplied arguments.
            self._trace({"event": "EGO_DECISION", "timestamp": context.timestamp,
                # Store context.ego_id under 'ego_id'.
                # Store a dictionary built from context.ego_state under 'ego_state'.
                "ego_id": context.ego_id, "ego_state": dict(context.ego_state),
                # Store context.coordination_epoch under 'coordination_epoch'.
                "coordination_epoch": context.coordination_epoch,
                # Store context.coordination_complete under 'coordination_complete'.
                "coordination_complete": context.coordination_complete,
                # Store a list of the result of vars(c) for c in context.commitments under 'commitments'.
                "commitments": [vars(c) for c in context.commitments],
                # Store a list of the result of vars(c) for c in context.mandatory_commitments under
                # 'mandatory_commitments'.
                "mandatory_commitments": [vars(c) for c in context.mandatory_commitments],
                # Store a list of a dictionary built from the supplied values for m in context.peer_messages under
                # 'peer_messages'.
                "peer_messages": [dict(sender_id=m.sender_id, state=dict(m.state),
                    # Supply timestamp as m.timestamp.
                    # Supply movement_path_id as m.movement_path_id.
                    timestamp=m.timestamp, movement_path_id=m.movement_path_id,
                    # Supply queue_arrival_seconds as m.queue_arrival_seconds.
                    queue_arrival_seconds=m.queue_arrival_seconds,
                    # Supply admission_state as m.admission_state.
                    admission_state=m.admission_state,
                    # Supply coordination_epoch as m.coordination_epoch.
                    coordination_epoch=m.coordination_epoch) for m in context.peer_messages],
                # Store the result of vars(decision) under 'decision'.
                # Store admission_state under 'admission_state'.
                "decision": vars(decision), "admission_state": admission_state})

    # Failure trace using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input error: the supplied error.
    # Input admission_state: the supplied admission state.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def failure_trace(self, context, error, admission_state):
        # Run this branch when self.trace_path.
        if self.trace_path:
            # Call self._trace with the supplied arguments.
            self._trace({"event": "EXECUTION_ERROR", "timestamp": context.timestamp,
                # Store context.ego_id under 'ego_id'.
                # Store a dictionary built from context.ego_state under 'ego_state'.
                "ego_id": context.ego_id, "ego_state": dict(context.ego_state),
                # Store context.coordination_epoch under 'coordination_epoch'.
                "coordination_epoch": context.coordination_epoch,
                # Store error under 'error'.
                # Store admission_state under 'admission_state'.
                "error": error, "admission_state": admission_state})

    # Result using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Input aborted: the supplied aborted.
    # Output: result.
    # Processing: iterate over the relevant records.
    def result(self, runtime, aborted=False):
        # Set end to 'actual_simulation_time_seconds' from runtime; use self.now if absent.
        end = runtime.get("actual_simulation_time_seconds", self.now)
        # Set records to the result of self.ledger.finalize_episode(end).
        records = self.ledger.finalize_episode(end)
        # Set exposure to the result of team_interval_cost_seconds(the result of
        # interval_vehicle_exposures(records, 0.0, end)).
        exposure = team_interval_cost_seconds(interval_vehicle_exposures(records, 0., end))
        # Set travel to a list of self.completions at v minus
        # self.ledger.get_vehicle_record(v).scheduled_spawn_time for v in self.completions.
        travel = [self.completions[v] - self.ledger.get_vehicle_record(v).scheduled_spawn_time
                  # Evaluate self.completions as part of the enclosing expression.
                  for v in self.completions]
        # Set travel_stats to the result of statistics(an empty list when aborted, otherwise travel).
        travel_stats = statistics([] if aborted else travel)
        # Waiting is censored observed incoming-lane wait; unspawned demand N/A.
        # Set waits to a list of self.waits at v for v in self.departures.
        waits = [self.waits[v] for v in self.departures]
        # Set wait_stats to the result of statistics(waits).
        wait_stats = statistics(waits)
        # Set approaches to a dictionary of a mapped to statistics((self.waits[v] for v in self.departures if
        # self.movements[v][0] == a)) at 'mean' for a in the text 'NESW'.
        approaches = {a: statistics(self.waits[v] for v in self.departures if
                                    # Evaluate self.movements[v] at 0 equals a as part of the enclosing
                                    # expression.
                                    self.movements[v][0] == a)["mean"] for a in "NESW"}
        # Set known to a list of x for x in values from approaches; retain entries satisfying x is a different
        # object from None.
        known = [x for x in approaches.values() if x is not None]
        # Set gap to the maximum of known minus the minimum of known when the number of entries in known equals 4,
        # otherwise None.
        gap = max(known) - min(known) if len(known) == 4 else None
        # Set (rate, inversions, eligible) to the result of inversion_rate(self.arrivals, self.services,
        # self.conflicts).
        rate, inversions, eligible = inversion_rate(self.arrivals, self.services, self.conflicts)
        # Set m to 'metrics' from runtime; use an empty dictionary if absent.
        m = runtime.get("metrics", {})
        # Set completed to the number of entries in self.completions.
        completed = len(self.completions)
        # Set scheduled to the number of entries in self.waits.
        scheduled = len(self.waits)
        # Set result to a dictionary containing collision_count, blocked_zone_violation_count,
        # total_team_travel_time_seconds,...
        result = {**m, "collision_count": max(self.collisions, int(bool(m.get("collisions")))),
            # Store 'blocked_zone_violations' from m; use 0 if absent under 'blocked_zone_violation_count'.
            "blocked_zone_violation_count": m.get("blocked_zone_violations", 0),
            # Store None when aborted, otherwise exposure under 'total_team_travel_time_seconds'.
            "total_team_travel_time_seconds": None if aborted else exposure,
            # Store completed is less than scheduled under 'traffic_exposure_censored'.
            "traffic_exposure_censored": completed < scheduled,
            # Store completed multiplied by 60.0 divided by end when end is greater than 0 and the negation of
            # aborted, otherwise None under 'throughput_vehicles_per_minute'.
            "throughput_vehicles_per_minute": completed * 60. / end if end > 0 and not aborted else None,
            # Store completed divided by scheduled under 'completion_rate'.
            # Store scheduled under 'total_vehicles_scheduled'.
            "completion_rate": completed / scheduled, "total_vehicles_scheduled": scheduled,
            # Store the number of entries in self.departures under 'total_vehicles_spawned'.
            # Store completed under 'total_vehicles_completed'.
            "total_vehicles_spawned": len(self.departures), "total_vehicles_completed": completed,
            # Store scheduled minus completed under 'unfinished_vehicles'.
            "unfinished_vehicles": scheduled - completed,
            # Store end when completed equals scheduled, otherwise None under 'episode_completion_time_seconds'.
            "episode_completion_time_seconds": end if completed == scheduled else None,
            # Store end under 'observed_simulation_time_seconds'.
            "observed_simulation_time_seconds": end,
            # Store the negation of aborted and completed is less than scheduled under 'timeout'.
            "timeout": not aborted and completed < scheduled,
            # Store self.deadlock_observed under 'deadlock_observed'.
            "deadlock_observed": self.deadlock_observed,
            # Store approaches under 'per_approach_mean_waiting_time_seconds'.
            "per_approach_mean_waiting_time_seconds": approaches,
            # Store gap under 'approach_waiting_time_gap_seconds'.
            "approach_waiting_time_gap_seconds": gap,
            # Store rate under 'conflicting_pair_fcfs_inversion_rate'.
            "conflicting_pair_fcfs_inversion_rate": rate,
            # Store inversions under 'fcfs_inversion_count'.
            # Store eligible under 'fcfs_eligible_pair_count'.
            "fcfs_inversion_count": inversions, "fcfs_eligible_pair_count": eligible,
            # Store self.emergency_events under 'native_emergency_braking_events'.
            "native_emergency_braking_events": self.emergency_events,
            # Store self.emergency_evidence under 'native_emergency_braking_evidence'.
            "native_emergency_braking_evidence": self.emergency_evidence,
            # Store self.collision_evidence under 'collision_evidence'.
            "collision_evidence": self.collision_evidence,
            "timing_label": "HARDWARE-DEPENDENT RUNTIME MEASUREMENTS",
            # Store the number of entries in self.inference_ns under 'mappo_inference_call_count'.
            "mappo_inference_call_count": len(self.inference_ns),
            # Store the sum of a lazy sequence of x > 40000000 for x in self.inference_ns divided by the number of
            # entries in self.inference_ns when self.inference_ns, otherwise None under
            # 'mappo_inference_fraction_exceeding_40ms'.
            "mappo_inference_fraction_exceeding_40ms": (
                # Evaluate the sum of a lazy sequence of x > 40000000 for x in self.inference_ns divided by the
                # number of entries in self.inference_ns when self.inference_ns, otherwise None as part of the
                # enclosing expression.
                sum(x > 40_000_000 for x in self.inference_ns) / len(self.inference_ns)
                # Evaluate self.inference_ns as part of the enclosing expression.
                if self.inference_ns else None)}
        # Iterate over a tuple containing a tuple containing the text 'travel_time', travel_stats, a tuple
        # containing the text 'waiting_time',..., binding each item to (name, summary).
        for name, summary in (("travel_time", travel_stats), ("waiting_time", wait_stats)):
            # Iterate over key/value pairs from summary, binding each item to (stat, value).
            for stat, value in summary.items():
                # Set result[f'{stat}_{name}_seconds'] to value.
                result[f"{stat}_{name}_seconds"] = value
        # Iterate over a tuple containing a tuple containing the text 'mappo_inference', self.inference_ns, a
        # tuple containing the text..., binding each item to (name, values).
        for name, values in (("mappo_inference", self.inference_ns), ("ego_execution", self.execution_ns)):
            # Iterate over key/value pairs from statistics((x / 1000000.0 for x in values)), binding each item to
            # (stat, value).
            for stat, value in statistics(x / 1e6 for x in values).items():
                # Set result[f'{name}_{stat}_ms'] to value.
                result[f"{name}_{stat}_ms"] = value
        # Set result['collision_free_episode'] to result at 'collision_count' equals 0.
        result["collision_free_episode"] = result["collision_count"] == 0
        # Set result['unsafe_episode'] to a Boolean built from result at 'collision_count' or result at
        # 'blocked_zone_violation_count'.
        result["unsafe_episode"] = bool(result["collision_count"] or result["blocked_zone_violation_count"])
        # Set result['vehicle_measurements'] to a dictionary of ego mapped to a dictionary containing
        # movement_path_id, scheduled_departure_seconds, actual_departure_seconds,... for ego in self.waits.
        result["vehicle_measurements"] = {ego: {"movement_path_id": self.movements[ego],
            # Store self.ledger.get_vehicle_record(ego).scheduled_spawn_time under 'scheduled_departure_seconds'.
            "scheduled_departure_seconds": self.ledger.get_vehicle_record(ego).scheduled_spawn_time,
            # Store ego from self.departures; use None if absent under 'actual_departure_seconds'.
            "actual_departure_seconds": self.departures.get(ego),
            # Store ego from self.completions; use None if absent under 'completion_seconds'.
            "completion_seconds": self.completions.get(ego),
            # Store ego from self.arrivals; use None if absent under 'queue_arrival_seconds'.
            # Store ego from self.services; use None if absent under 'service_seconds'.
            "queue_arrival_seconds": self.arrivals.get(ego), "service_seconds": self.services.get(ego),
            # Store self.waits at ego when ego belongs to self.departures, otherwise None under
            # 'observed_wait_seconds'.
            "observed_wait_seconds": self.waits[ego] if ego in self.departures else None}
            # Evaluate self.waits as part of the enclosing expression.
            for ego in self.waits}
        # Return result to the caller.
        return result
