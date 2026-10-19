"""Atomic, display-only state export for the local browser showcase."""

import json
from pathlib import Path
import time
from .vehicle_display_contract import explain_decision, explain_mappo, VERSION
from .intersection_presentation import IntersectionPresentation


def displayed_mappo_invocation(status, has_outcome=False):
    """Describe existing eligibility without changing any control decision."""
    if has_outcome:
        return "AUTHORIZED"
    if status in {"NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"}:
        return "NOT_REQUIRED"
    return "BLOCKED"


class TrafficProgressTelemetry:
    """Measure stationary blocked heads; never classify legal permission."""

    def __init__(self):
        self._signature = None
        self._since = None

    def observe(self, now, states, participants, blocked, status, original_graph):
        from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
        heads = tuple(sorted(participants))
        signature = (heads, status, tuple(sorted(tuple(e) for e in original_graph)))
        stationary_blocked = bool(heads) and set(heads).issubset(blocked) and all(
            ego in states and states[ego]["speed"] < STOPPED_SPEED_THRESHOLD_MPS
            for ego in heads)
        if not stationary_blocked:
            self._signature, self._since = None, None
            return {"status": "PROGRESS_OR_TRANSIENT_WAIT", "blocked_seconds": 0.0,
                    "reason": status, "display_only": True}
        if signature != self._signature:
            self._signature, self._since = signature, now
        elapsed = max(0.0, now - self._since)
        return {"status": ("PERSISTENT_BLOCKAGE" if elapsed >= DEADLOCK_DURATION_SECONDS
                           else "TEMPORARY_HOLD"),
                "blocked_seconds": elapsed, "reason": status, "display_only": True,
                "threshold_seconds": DEADLOCK_DURATION_SECONDS,
                "stationary_speed_threshold_mps": STOPPED_SPEED_THRESHOLD_MPS,
                "participant_ids": heads}


class BrowserStatePublisher:
    """Publish compact snapshots; never returns data to simulation control."""

    def __init__(self, path, traci_module, *, frequency_hz=8.0,
                 presentation_delay_ms=0):
        self.path = Path(path)
        self.traci = traci_module
        self.interval = 1.0 / float(frequency_hz)
        self.presentation_delay_seconds = max(
            0, int(presentation_delay_ms)) / 1000.0
        self._last_simulation_time = float("-inf")
        self._last_payload = None
        self._last_inspectable_vehicles = ()
        self._last_vehicle_by_id = {}
        self._completed_vehicle_by_id = {}
        self._vehicle_traces = {}
        self._last_mappo_participant_ids = set()
        self._progress = TrafficProgressTelemetry()
        self._mappo_times = {}
        self._last_authorized_event = None
        self._presentation = IntersectionPresentation()

    @staticmethod
    def map_snapshot(path_manager):
        geometries = tuple(tuple((float(x), float(y)) for x, y in
                                 path.centerline_geometry)
                           for path in path_manager.paths.values())
        points = tuple(point for geometry in geometries for point in geometry)
        xs, ys = zip(*points)
        junction = path_manager.network.getNode('center').getShape()
        cx = sum(p[0] for p in junction) / len(junction)
        cy = sum(p[1] for p in junction) / len(junction)
        # Fixed overview boundary, shared across scenarios and camera zooms.
        radius = max(((x-cx)**2+(y-cy)**2)**.5 for x,y in junction)
        # Cover the largest supported overview (dense view at minimum zoom),
        # so zooming out cannot reveal a body excluded by a smaller crop.
        extent = radius * 3.2 * 1.5 / 0.55
        lanes = {}
        for path in path_manager.paths.values():
            lanes[path.incoming_lane_id] = 'incoming'
            lanes[path.outgoing_lane_id] = 'outgoing'
            lanes.update({lane:'internal' for lane in path.internal_lane_ids})
        return {"bounds": {"min_x": min(xs), "max_x": max(xs),
                           "min_y": min(ys), "max_y": max(ys)},
                'presentation_lanes':lanes,
                'presentation_region':(cx-extent,cy-extent,cx+extent,cy+extent)}

    def pace(self):
        if self.presentation_delay_seconds:
            time.sleep(self.presentation_delay_seconds)

    @staticmethod
    def _prediction_summary(prediction):
        if not prediction:
            return None
        stage_name, stage = next(((name, prediction.get(name))
                                  for name in ("secondary", "primary")
                                  if prediction.get(name)), (None, None))
        return {"label": prediction.get("fused_label") or (
                    stage.get("label") if stage else "UNKNOWN"),
                "confidence": (stage.get("confidence") if stage else None),
                "stage": stage_name.upper() if stage_name else "WAITING",
                "status": prediction.get("status", "WAITING_FOR_CONTEXT")}

    @classmethod
    def _vehicle_evidence(cls, vehicle_id, state, observations, snapshots,
                          plan, control_records, policy_factors):
        ldm = observations.get_ldm(vehicle_id) if observations else None
        tracks = getattr(ldm, "tracks", {}) if ldm else {}
        local_targets = {key: value for key, value in tracks.items()
                         if key != vehicle_id}
        observed = tuple(sorted(key for key, value in local_targets.items()
                                if value.get("is_observed")))
        propagated = tuple(sorted(set(local_targets) - set(observed)))
        predictions = tuple({"target_id": key,
                             **cls._prediction_summary(value.get(
                                 "intention_prediction"))}
                            for key, value in sorted(local_targets.items())
                            if cls._prediction_summary(value.get(
                                "intention_prediction")) is not None)
        graph = getattr(ldm, "current_conflict_graph", None) if ldm else None
        graph_edges = tuple(graph.get("edges", ())) if isinstance(graph, dict) else ()
        conflict_partners = tuple(sorted({edge.get("target_track_id")
                                          for edge in graph_edges
                                          if edge.get("target_track_id")}))
        snapshot = next((item for item in snapshots
                         if item.get("ego_id") == vehicle_id), None)
        local_precedence = tuple((edge["yielding_vehicle_id"],
                                  edge["priority_vehicle_id"])
                                 for edge in (snapshot or {}).get(
                                     "joint_precedence_edges", ()))
        encoded = getattr(ldm, "current_encoded_graph_observation", None)
        gnn = ({"encoded": True, **encoded.dashboard_summary()}
               if encoded is not None else {"encoded": False})
        factors = tuple(factor for factor in policy_factors
                        if factor.get("ego_id") == vehicle_id)
        constraints = tuple(record for record in control_records
                            if getattr(record, "vehicle_id", None) == vehicle_id)
        cap = (min(float(record.requested_speed_cap_mps)
                   for record in constraints) if constraints else None)
        planner_state = ("READY" if vehicle_id in plan.ready_vehicle_ids else
                         "BLOCKED" if vehicle_id in plan.blocked_vehicle_ids else
                         "NOT_APPLICABLE")
        return {
            "speed_mps": float(state["speed"]),
            "acceleration_mps2": float(state["accel"]),
            "local_perception": {"observed_vehicle_ids": observed,
                                 "observed_vehicle_count": len(observed)},
            "ldm": {"track_count": len(local_targets),
                    "tracked_vehicle_ids": tuple(sorted(local_targets)),
                    "propagated_vehicle_ids": propagated,
                    "history_lengths": {key: len(value.get(
                        "position_history", ()))
                        for key, value in sorted(local_targets.items())}},
            # These are ego-local target predictions, never route truth.
            "local_intention_predictions": predictions,
            "conflict": {"relevant": bool(conflict_partners),
                         "partners": conflict_partners},
            "local_precedence_edges": local_precedence,
            "gnn": gnn,
            "negotiation": {"factors": factors},
            "planner": {"state": planner_state},
            "control": {"speed_constraint_active": bool(constraints),
                        "speed_cap_mps": cap,
                        "source": ("DETERMINISTIC_PRECEDENCE_CONTROLLER"
                                   if constraints else "SUMO_NATIVE")}}

    def publish(self, *, simulation_time, map_state, running, status,
                participants=(), ready=(), blocked=(), original_graph=(),
                effective_graph=(), mappo_invocation="NOT_REQUIRED",
                completed=0, scheduled=12, scenario_id="default_panel",
                scientific_states=None, observations=None, snapshots=(),
                plan=None, control_records=(), policy_factors=(), events=(),
                run_metrics=None,
                execution_decisions=(), coordination_participants=None,
                coordination_timestamp=None, run_id=None,
                force=False):
        now = float(simulation_time)
        # The existing final publisher call omits run_id. Preserve identity and
        # presentation tombstones through shutdown; this is not a new run.
        if force and not running and run_id is None and self._last_payload is not None:
            run_id = self._last_payload.get('run_id')
        identity = (run_id, scenario_id)
        if self._presentation.run is not None and self._presentation.run != identity:
            self._last_vehicle_by_id.clear()
            self._completed_vehicle_by_id.clear()
            self._vehicle_traces.clear()
            self._mappo_times.clear()
            self._last_mappo_participant_ids.clear()
            self._last_authorized_event = None
            self._last_payload = None
            self._last_simulation_time = float('-inf')
        self._presentation.reset_for((run_id, scenario_id))
        if not force and now - self._last_simulation_time < self.interval:
            return None
        self._last_simulation_time = now
        ready_set, blocked_set = set(ready), set(blocked)
        participant_set = set(participants)
        receipts = set(coordination_participants if coordination_participants is not None else participants)
        decision_by_id = {d.ego_id:d for d in execution_decisions}
        if mappo_invocation == "AUTHORIZED":
            self._last_mappo_participant_ids.update(receipts)
            for ego in receipts:
                self._mappo_times[ego] = coordination_timestamp if coordination_timestamp is not None else now
        vehicles = []
        for vehicle_id in sorted(self.traci.vehicle.getIDList()):
            state_record = ((scientific_states or {}).get(vehicle_id))
            x, y = (state_record["position"] if state_record else
                    self.traci.vehicle.getPosition(vehicle_id))
            angle = (float(state_record["angle_degrees"]) if state_record else
                     float(self.traci.vehicle.getAngle(vehicle_id)))
            # Body color is the physical permission state. Negotiation is a
            # separate presentation attribute and can never mask a plan.
            state = ("BLOCKED" if vehicle_id in blocked_set else
                     "READY" if vehicle_id in ready_set else
                     "NEGOTIATING" if status == 'NEGOTIATING' and vehicle_id in participant_set else
                     "APPROACHING")
            negotiation_involvement = bool(
                vehicle_id in self._last_mappo_participant_ids)
            vehicle = {"id": vehicle_id,
                             "front_bumper_x": float(x),
                             "front_bumper_y": float(y),
                             "angle_degrees": angle,
                             "length_m": float(state_record["length"] if
                                 state_record else self.traci.vehicle.getLength(vehicle_id)),
                             "width_m": float(state_record["width"] if
                                 state_record else self.traci.vehicle.getWidth(vehicle_id)),
                             "speed_mps": float(state_record["speed"] if
                                 state_record else self.traci.vehicle.getSpeed(vehicle_id)),
                             "display_state": state,
                             "execution_state": (state if state != "NEGOTIATING"
                                                 else "APPROACHING"),
                             "negotiation_involvement": negotiation_involvement}
            if state_record is not None and plan is not None:
                vehicle.update(self._vehicle_evidence(
                    vehicle_id, state_record, observations, snapshots, plan,
                    control_records, policy_factors))
            vehicle.update(explain_decision(decision_by_id.get(vehicle_id),vehicle['speed_mps'],now))
            own_snapshot = next((s for s in snapshots if s.get('ego_id')==vehicle_id),None)
            has_receipt = mappo_invocation=='AUTHORIZED' and vehicle_id in receipts
            factors = vehicle.get('negotiation',{}).get('factors',()) if has_receipt else ()
            vehicle['negotiation'] = {'factors':factors,
                **explain_mappo((own_snapshot or {}).get('negotiation_status'),has_receipt,
                    self._mappo_times.get(vehicle_id),now,factors)}
            if vehicle['negotiation']['status']=='ELIGIBLE' and mappo_invocation=='BLOCKED':
                vehicle['negotiation']['status']='BLOCKED'
                vehicle['negotiation']['locally_eligible']=True
            decision = decision_by_id.get(vehicle_id)
            if state_record is not None and map_state.get('presentation_lanes'):
                vehicle.update(self._presentation.classify(vehicle, state_record, decision, map_state,
                    pending=status == 'NEGOTIATING' and vehicle_id in participant_set and not has_receipt))
                if vehicle['display_state'] == 'APPROACHING':
                    vehicle['permission_label'] = 'APPROACHING'
            if has_receipt and decision is not None:
                vehicle['negotiation']['execution_status'] = (
                    'SAFETY_FALLBACK' if decision.fallback_pairs else
                    'SHIELD_REJECTION' if decision.shield_rejection_reason else
                    'ENTRY_HELD' if decision.permission!='PERMITTED' else 'LOCAL_EXECUTION')
                if decision.permission=='SAFE_HOLD':
                    vehicle['negotiation']['status']='BLOCKED'
                    vehicle['negotiation']['reason']='OUTCOME_RECEIVED_BUT_EXECUTION_HELD'
            vehicles.append(vehicle)
        current_ids = {item["id"] for item in vehicles}
        departed_ids = (set(self._last_vehicle_by_id) - current_ids
                        if scientific_states is not None else set())
        for vehicle_id in departed_ids:
            final = dict(self._last_vehicle_by_id[vehicle_id])
            final["display_state"] = "CLEARED"
            self._completed_vehicle_by_id[vehicle_id] = final
            self._trace(vehicle_id, now, "COMPLETED", "Vehicle left simulation")
        for vehicle in (vehicles if scientific_states is not None else ()):
            vehicle_id = vehicle["id"]
            previous = self._last_vehicle_by_id.get(vehicle_id)
            if previous is None:
                self._trace(vehicle_id, now, "FIRST_OBSERVED", "Runtime state available")
            self._record_meaningful_transitions(vehicle_id, previous, vehicle, now)
            self._last_vehicle_by_id[vehicle_id] = dict(vehicle)
        if (force and status == "FINISHED" and int(completed) >= int(scheduled)):
            for vehicle_id, vehicle in self._last_vehicle_by_id.items():
                if vehicle_id not in self._completed_vehicle_by_id:
                    final = dict(vehicle); final["display_state"] = "CLEARED"
                    self._completed_vehicle_by_id[vehicle_id] = final
        meaningful_events = tuple(events)[-12:]
        authorized_events = tuple(item for item in meaningful_events
                                  if item.get("mappo_invocation") == "AUTHORIZED")
        if authorized_events:
            self._last_authorized_event = authorized_events[-1]
        rule_events = tuple(item for item in meaningful_events
                            if item.get("event") == "REGULATORY_ORDER_RESOLVED")
        renegotiations = tuple(item for item in meaningful_events
                               if item.get("event") == "PLAN_INVALIDATED")
        payload = {"schema": "PANEL_DEMO_BROWSER_STATE_V3",
                   "vehicle_state_contract": VERSION, "run_id": run_id,
                   "display_only": True, "running": bool(running),
                   "scenario_id": str(scenario_id),
                   "simulation_time": now, "status": status,
                   "participants": tuple(participants), "ready": tuple(ready),
                   "blocked": tuple(blocked),
                   "original_graph": tuple(original_graph),
                   "effective_graph": tuple(effective_graph),
                   "mappo_invocation": mappo_invocation,
                   "completed": int(completed), "scheduled": int(scheduled),
                   "vehicles": [v for v in vehicles if v.get('presentation_visible', True)],
                   "active_sumo_vehicles": len(vehicles),
                   "scientific_vehicles": vehicles,
                   "intersection_cleared_vehicle_ids": tuple(sorted(self._presentation.exited)),
                   "completed_vehicles": tuple(
                       self._completed_vehicle_by_id[key]
                       for key in sorted(self._completed_vehicle_by_id)),
                   "events": meaningful_events,
                   "negotiation_events": authorized_events,
                   "last_mappo_event": self._last_authorized_event,
                   "run_negotiation_summary": {
                       "mappo_authorized_events": (run_metrics or {}).get('mappo_decision_epochs',len(authorized_events)),
                       "mappo_negotiation_observed": bool((run_metrics or {}).get('mappo_decision_epochs',0) or self._last_authorized_event),
                       "rule_resolved_events": (run_metrics or {}).get('rule_resolved_events',len(rule_events)),
                       "renegotiation_events": len(renegotiations)},
                   "run_metrics": dict(run_metrics or {}),
                   **map_state}
        if scientific_states is not None:
            payload["traffic_progress"] = self._progress.observe(now,
                scientific_states, participants, blocked_set, status, original_graph)
        if vehicles and any("planner" in item for item in vehicles):
            self._last_inspectable_vehicles = tuple(vehicles)
        if force and not running and scientific_states is None and self._last_payload is not None:
            previous_by_id = {v['id']:v for v in self._last_payload['vehicles']}
            previous_by_id.update(self._last_vehicle_by_id)
            if "traffic_progress" in self._last_payload:
                payload["traffic_progress"] = self._last_payload["traffic_progress"]
            payload["vehicles"] = (() if status == "FINISHED" and
                                   int(completed) >= int(scheduled) else
                                   tuple(dict(previous_by_id.get(v['id'],{}),**v)
                                         for v in vehicles))
            for vehicle in payload['vehicles']:
                # Terminal physical readings are current; prior permission
                # evidence remains explicitly dated, never silently refreshed.
                previous = previous_by_id.get(vehicle['id'],{})
                for field in ('entry_permission','permission_label','negotiation','speed_command','display_state','execution_state'):
                    if field in previous:vehicle[field]=previous[field]
                vehicle['permission_evidence_current'] = False
                if vehicle.get('negotiation',{}).get('current_receipt'):
                    vehicle['negotiation'] = dict(vehicle['negotiation'],status='DECISION_EXPIRED',
                        current_receipt=False,factors=(),actions=(),local_actor_action_count=0)
                if vehicle.get('entry_permission'):
                    vehicle['permission_label'] = ('LAST REPORTED: READY / GO' if vehicle['entry_permission']['authorized']
                        else 'LAST REPORTED: ENTRY HELD / '+vehicle['motion_state'])
            payload["events"] = self._last_payload["events"]
            payload["negotiation_events"] = self._last_payload[
                "negotiation_events"]
            payload["last_mappo_event"] = self._last_payload[
                "last_mappo_event"]
            payload["run_negotiation_summary"] = self._last_payload[
                "run_negotiation_summary"]
            payload["run_metrics"] = dict(run_metrics or
                                           self._last_payload["run_metrics"])
            for key in ("participants", "ready", "blocked", "original_graph",
                        "effective_graph", "mappo_invocation"):
                payload[key] = self._last_payload[key]
            if status == "FINISHED" and int(completed) >= int(scheduled):
                for key in ("participants", "ready", "blocked"):
                    payload[key] = ()
                payload["mappo_invocation"] = "NOT_REQUIRED"
        payload['vehicles'] = tuple(v for v in payload['vehicles']
            if v['id'] not in self._presentation.exited and v.get('presentation_visible', True))
        self._last_payload = payload
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        for attempt in range(10 if force and not running else 1):
            try:
                temporary.write_text(json.dumps(payload, separators=(",", ":")),
                                     encoding="utf-8")
                temporary.replace(self.path)
                break
            except OSError:
                # Hot frames never delay control. After simulation ends, give
                # Windows readers a bounded chance to release the destination.
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                if force and not running and attempt < 9:
                    time.sleep(0.02)
        return None

    def _trace(self, vehicle_id, timestamp, stage, value):
        trace = self._vehicle_traces.setdefault(vehicle_id, [])
        record = {"timestamp": float(timestamp), "stage": stage,
                  "value": value}
        if not trace or (trace[-1]["stage"], trace[-1]["value"]) != (stage, value):
            trace.append(record)

    def _record_meaningful_transitions(self, vehicle_id, previous, current, now):
        fields = (("planner", "PLANNER"), ("control", "CONTROL"),
                  ("conflict", "CONFLICT"), ("local_precedence_edges", "PRECEDENCE"),
                  ("gnn", "GNN"), ("negotiation", "MAPPO"))
        for key, stage in fields:
            value = current.get(key)
            previous_value = previous.get(key) if previous else None
            if key == 'negotiation' and value:
                # Elapsed display age is not a new inference/commitment event.
                value = {k:v for k,v in value.items() if k!='event_age_seconds'}
                if previous_value:
                    previous_value = {k:v for k,v in previous_value.items() if k!='event_age_seconds'}
            if value and previous_value != value:
                self._trace(vehicle_id, now, stage, value)
        predictions = current.get("local_intention_predictions")
        if predictions and (previous is None or
                            previous.get("local_intention_predictions") != predictions):
            self._trace(vehicle_id, now, "INTENTION", predictions)

    def presentation_vehicle_history(self):
        final = dict(self._completed_vehicle_by_id)
        final.update(self._last_vehicle_by_id)
        return {"final_snapshots": tuple(final[key] for key in sorted(final)),
                "process_traces": {key: tuple(value)
                                   for key, value in sorted(self._vehicle_traces.items())}}
