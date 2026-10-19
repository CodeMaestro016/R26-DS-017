"""Post-training measurements; no policy inputs, rewards, or permissions."""
from statistics import mean, median
from itertools import combinations
import json
import numpy as np
from config import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS, DEADLOCK_DURATION_SECONDS
from traffic_accounting.demand_ledger import VehicleDemandLedger
from traffic_accounting.models import DemandScheduleSource
from negotiation_objective.accounting import interval_vehicle_exposures, team_interval_cost_seconds

def statistics(values):
    values = list(values)
    return {"mean": mean(values) if values else None,
        "median": median(values) if values else None,
        "p95": float(np.percentile(values, 95, method="linear")) if values else None,
        "maximum": max(values) if values else None}

def inversion_rate(arrivals, services, conflicts):
    pairs = [(a, b) for a, b in conflicts if a in arrivals and b in arrivals
             and a in services and b in services]
    inverted = sum(((arrivals[a], a) < (arrivals[b], b)) !=
                   ((services[a], a) < (services[b], b)) for a, b in pairs)
    return (inverted / len(pairs) if pairs else None), inverted, len(pairs)

class Telemetry:
    def __init__(self, schedule, proposed=True):
        self.schedule = schedule
        self.proposed = proposed
        self.arrivals, self.services, self.departures, self.completions = {}, {}, {}, {}
        self.waits, self.stopped_since, self.movements = {}, {}, {}
        self.inference_ns, self.execution_ns = [], []
        self.emergency_events, self.emergency_prior, self.emergency_evidence = 0, set(), []
        self.collisions, self.collision_evidence, self.deadlock_observed = 0, [], False
        self.conflicts = []
        self.ledger = VehicleDemandLedger()
        self.now = 0.
        self.trace_path = None
        for approach, rows in schedule.items():
            for row in rows:
                ego = f"PANEL_AV_{approach}_{row.sequence_index + 1:02d}"
                self.waits[ego] = 0.
                self.movements[ego] = row.movement_path_id
                self.ledger.register_scheduled_vehicle(ego, row.scheduled_departure_seconds,
                    DemandScheduleSource.PERIODIC_SPAWN_SCHEDULE,
                    provenance={"clock": "EXOGENOUS_FROZEN_FINAL_EVALUATION"})

    def observe(self, now, states, lifecycle, movements, paths, zones, traci):
        if self.trace_path:
            self._trace({"event": "PHYSICAL_STATE", "timestamp": now,
                "states": states, "movements": movements})
        if traci.simulation.getStartingTeleportIDList():
            raise RuntimeError("EVALUATION_TELEPORT_OBSERVED")
        dt = now - self.now
        self.now = now
        for ego in lifecycle.departed_vehicle_ids:
            if ego in self.waits:
                self.departures[ego] = now
                self.ledger.record_actual_departure(ego, now)
        for ego in lifecycle.arrived_vehicle_ids:
            if ego in self.waits:
                self.completions[ego] = now
                self.ledger.record_service_completion(ego, now)
        braking = set()
        for ego, state in states.items():
            path = paths.paths[movements[ego]]
            if state["lane_id"] == path.incoming_lane_id:
                self.arrivals.setdefault(ego, now)  # Entry to existing incoming lane.
                if state["speed"] < STOPPED_SPEED_THRESHOLD_MPS:
                    self.waits[ego] += dt
                    self.stopped_since.setdefault(ego, now - dt)
                    if now - self.stopped_since[ego] >= DEADLOCK_DURATION_SECONDS:
                        self.deadlock_observed = True
                else:
                    self.stopped_since.pop(ego, None)
            elif ego in self.arrivals:
                self.services.setdefault(ego, now)  # Front bumper leaves incoming lane.
            if state.get("accel", 0.) < -state["comfortable_deceleration_mps2"] - 1e-6:
                braking.add(ego)
                if ego not in self.emergency_prior:
                    self.emergency_evidence.append({"vehicle_id": ego, "timestamp": now,
                        "acceleration_mps2": state["accel"],
                        "comfortable_deceleration_mps2": state["comfortable_deceleration_mps2"]})
        self.emergency_events += len(braking - self.emergency_prior)
        self.emergency_prior = braking
        collisions = tuple(traci.simulation.getCollisions())
        self.collisions += len(collisions)
        self.collision_evidence.extend({"timestamp": now, "collider": c.collider,
            "victim": c.victim, "type": c.type} for c in collisions)
        self.conflicts = [(a, b) for a, b in combinations(sorted(self.movements), 2)
            if self.movements[a][0] != self.movements[b][0] and zones.zone_record(
                self.movements[a], 1.8, self.movements[b], 1.8) is not None]

    def inference(self, ns):
        if self.proposed:
            self.inference_ns.append(ns)

    def execution(self, ns, decision):
        self.execution_ns.append(ns)

    def _trace(self, record):
        from .models import normalize_nonfinite
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalize_nonfinite(record), default=str, allow_nan=False) + "\n")

    def coordination_trace(self, now, snapshots, observations):
        if self.trace_path:
            self._trace({"event": "COORDINATION_SOURCE", "timestamp": now,
                "snapshots": snapshots, "local_evidence": {
                    s["ego_id"]: dict(
                        conflict=observations.get_ldm(s["ego_id"]).get_current_conflict_graph(),
                        regulatory=observations.get_ldm(s["ego_id"]).get_current_regulatory_assessment(),
                        temporal=observations.get_ldm(s["ego_id"]).get_current_temporal_assessment()) for s in snapshots}})

    def decision_trace(self, context, decision, admission_state):
        if self.trace_path:
            self._trace({"event": "EGO_DECISION", "timestamp": context.timestamp,
                "ego_id": context.ego_id, "ego_state": dict(context.ego_state),
                "coordination_epoch": context.coordination_epoch,
                "coordination_complete": context.coordination_complete,
                "commitments": [vars(c) for c in context.commitments],
                "mandatory_commitments": [vars(c) for c in context.mandatory_commitments],
                "peer_messages": [dict(sender_id=m.sender_id, state=dict(m.state),
                    timestamp=m.timestamp, movement_path_id=m.movement_path_id,
                    queue_arrival_seconds=m.queue_arrival_seconds,
                    admission_state=m.admission_state,
                    coordination_epoch=m.coordination_epoch) for m in context.peer_messages],
                "decision": vars(decision), "admission_state": admission_state})

    def failure_trace(self, context, error, admission_state):
        if self.trace_path:
            self._trace({"event": "EXECUTION_ERROR", "timestamp": context.timestamp,
                "ego_id": context.ego_id, "ego_state": dict(context.ego_state),
                "coordination_epoch": context.coordination_epoch,
                "error": error, "admission_state": admission_state})

    def result(self, runtime, aborted=False):
        end = runtime.get("actual_simulation_time_seconds", self.now)
        records = self.ledger.finalize_episode(end)
        exposure = team_interval_cost_seconds(interval_vehicle_exposures(records, 0., end))
        travel = [self.completions[v] - self.ledger.get_vehicle_record(v).scheduled_spawn_time
                  for v in self.completions]
        travel_stats = statistics([] if aborted else travel)
        # Waiting is censored observed incoming-lane wait; unspawned demand N/A.
        waits = [self.waits[v] for v in self.departures]
        wait_stats = statistics(waits)
        approaches = {a: statistics(self.waits[v] for v in self.departures if
                                    self.movements[v][0] == a)["mean"] for a in "NESW"}
        known = [x for x in approaches.values() if x is not None]
        gap = max(known) - min(known) if len(known) == 4 else None
        rate, inversions, eligible = inversion_rate(self.arrivals, self.services, self.conflicts)
        m = runtime.get("metrics", {})
        completed = len(self.completions)
        scheduled = len(self.waits)
        result = {**m, "collision_count": max(self.collisions, int(bool(m.get("collisions")))),
            "blocked_zone_violation_count": m.get("blocked_zone_violations", 0),
            "total_team_travel_time_seconds": None if aborted else exposure,
            "traffic_exposure_censored": completed < scheduled,
            "throughput_vehicles_per_minute": completed * 60. / end if end > 0 and not aborted else None,
            "completion_rate": completed / scheduled, "total_vehicles_scheduled": scheduled,
            "total_vehicles_spawned": len(self.departures), "total_vehicles_completed": completed,
            "unfinished_vehicles": scheduled - completed,
            "episode_completion_time_seconds": end if completed == scheduled else None,
            "observed_simulation_time_seconds": end,
            "timeout": not aborted and completed < scheduled,
            "deadlock_observed": self.deadlock_observed,
            "per_approach_mean_waiting_time_seconds": approaches,
            "approach_waiting_time_gap_seconds": gap,
            "conflicting_pair_fcfs_inversion_rate": rate,
            "fcfs_inversion_count": inversions, "fcfs_eligible_pair_count": eligible,
            "native_emergency_braking_events": self.emergency_events,
            "native_emergency_braking_evidence": self.emergency_evidence,
            "collision_evidence": self.collision_evidence,
            "timing_label": "HARDWARE-DEPENDENT RUNTIME MEASUREMENTS",
            "mappo_inference_call_count": len(self.inference_ns),
            "mappo_inference_fraction_exceeding_40ms": (
                sum(x > 40_000_000 for x in self.inference_ns) / len(self.inference_ns)
                if self.inference_ns else None)}
        for name, summary in (("travel_time", travel_stats), ("waiting_time", wait_stats)):
            for stat, value in summary.items():
                result[f"{stat}_{name}_seconds"] = value
        for name, values in (("mappo_inference", self.inference_ns), ("ego_execution", self.execution_ns)):
            for stat, value in statistics(x / 1e6 for x in values).items():
                result[f"{name}_{stat}_ms"] = value
        result["collision_free_episode"] = result["collision_count"] == 0
        result["unsafe_episode"] = bool(result["collision_count"] or result["blocked_zone_violation_count"])
        result["vehicle_measurements"] = {ego: {"movement_path_id": self.movements[ego],
            "scheduled_departure_seconds": self.ledger.get_vehicle_record(ego).scheduled_spawn_time,
            "actual_departure_seconds": self.departures.get(ego),
            "completion_seconds": self.completions.get(ego),
            "queue_arrival_seconds": self.arrivals.get(ego), "service_seconds": self.services.get(ego),
            "observed_wait_seconds": self.waits[ego] if ego in self.departures else None}
            for ego in self.waits}
        return result
