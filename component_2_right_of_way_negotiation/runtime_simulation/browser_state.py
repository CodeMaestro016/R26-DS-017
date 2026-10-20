"""Atomic, display-only state export for the local browser showcase."""

# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import time for use in this module.
import time
# Import explain_decision, explain_mappo, VERSION from .vehicle_display_contract for the operations below.
from .vehicle_display_contract import explain_decision, explain_mappo, VERSION
# Import IntersectionPresentation from .intersection_presentation for the operations below.
from .intersection_presentation import IntersectionPresentation


# Describe existing eligibility without changing any control decision.
# Input status: the supplied status.
# Input has_outcome: the supplied has outcome.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def displayed_mappo_invocation(status, has_outcome=False):
    """Describe existing eligibility without changing any control decision."""
    # Run this branch when has_outcome.
    if has_outcome:
        # Return the text 'AUTHORIZED' to the caller.
        return "AUTHORIZED"
    # Run this branch when status belongs to a set containing the text 'NO_ACTIVE_CONFLICT', the text
    # 'REGULATORY_ORDER_RESOLVED'.
    if status in {"NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"}:
        # Return the text 'NOT_REQUIRED' to the caller.
        return "NOT_REQUIRED"
    # Return the text 'BLOCKED' to the caller.
    return "BLOCKED"


# Measure stationary blocked heads; never classify legal permission.
# Instances expose the attributes and methods implemented in this class.
class TrafficProgressTelemetry:
    """Measure stationary blocked heads; never classify legal permission."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self._signature to None.
        self._signature = None
        # Set self._since to None.
        self._since = None

    # Observe using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Input states: the supplied states.
    # Input participants: the supplied participants.
    # Input blocked: the supplied blocked.
    # Input status: the supplied status.
    # Input original_graph: the supplied original graph.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def observe(self, now, states, participants, blocked, status, original_graph):
        # Import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
        from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
        # Set heads to a tuple built from the sorted values from participants.
        heads = tuple(sorted(participants))
        # Set signature to a tuple containing heads, status, a tuple built from the sorted values from a lazy
        # sequence of tuple(e) for e in original_graph.
        signature = (heads, status, tuple(sorted(tuple(e) for e in original_graph)))
        # Set stationary_blocked to a Boolean built from heads and the result of set(heads).issubset(blocked) and
        # whether every item is true in a lazy sequence of ego in states and states[ego]['speed'] <
        # STOPPED_SPEED_THRESHOLD_MPS for ego in heads.
        stationary_blocked = bool(heads) and set(heads).issubset(blocked) and all(
            # Evaluate ego belongs to states and states[ego] at 'speed' is less than STOPPED_SPEED_THRESHOLD_MPS
            # as part of the enclosing expression.
            ego in states and states[ego]["speed"] < STOPPED_SPEED_THRESHOLD_MPS
            # Evaluate heads as part of the enclosing expression.
            for ego in heads)
        # Run this branch when the negation of stationary_blocked.
        if not stationary_blocked:
            # Set (self._signature, self._since) to a tuple containing None, None.
            self._signature, self._since = None, None
            # Return a dictionary containing status, blocked_seconds, reason, display_only to the caller.
            return {"status": "PROGRESS_OR_TRANSIENT_WAIT", "blocked_seconds": 0.0,
                    # Store status under 'reason'.
                    # Store True under 'display_only'.
                    "reason": status, "display_only": True}
        # Run this branch when signature differs from self._signature.
        if signature != self._signature:
            # Set (self._signature, self._since) to a tuple containing signature, now.
            self._signature, self._since = signature, now
        # Set elapsed to the maximum of 0.0, now minus self._since.
        elapsed = max(0.0, now - self._since)
        # Return a dictionary containing status, blocked_seconds, reason, display_only, threshold_seconds,... to
        # the caller.
        return {"status": ("PERSISTENT_BLOCKAGE" if elapsed >= DEADLOCK_DURATION_SECONDS
                           # Supply the text 'TEMPORARY_HOLD' to the enclosing expression.
                           else "TEMPORARY_HOLD"),
                # Store elapsed under 'blocked_seconds'.
                # Store status under 'reason'.
                # Store True under 'display_only'.
                "blocked_seconds": elapsed, "reason": status, "display_only": True,
                # Store DEADLOCK_DURATION_SECONDS under 'threshold_seconds'.
                "threshold_seconds": DEADLOCK_DURATION_SECONDS,
                # Store STOPPED_SPEED_THRESHOLD_MPS under 'stationary_speed_threshold_mps'.
                "stationary_speed_threshold_mps": STOPPED_SPEED_THRESHOLD_MPS,
                # Store heads under 'participant_ids'.
                "participant_ids": heads}


# Publish compact snapshots; never returns data to simulation control.
# Instances expose the attributes and methods implemented in this class.
class BrowserStatePublisher:
    """Publish compact snapshots; never returns data to simulation control."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path: the path or path object supplied by the caller.
    # Input traci_module: the supplied traci module.
    # Input frequency_hz: the supplied frequency hz.
    # Input presentation_delay_ms: the supplied presentation delay ms.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path, traci_module, *, frequency_hz=8.0,
                 # Declare presentation_delay_ms as input parameter.
                 presentation_delay_ms=0):
        # Set self.path to the result of Path(path).
        self.path = Path(path)
        # Set self.traci to traci_module.
        self.traci = traci_module
        # Set self.interval to 1.0 divided by a floating-point number built from frequency_hz.
        self.interval = 1.0 / float(frequency_hz)
        # Set self.presentation_delay_seconds to the maximum of 0, an integer built from presentation_delay_ms
        # divided by 1000.0.
        self.presentation_delay_seconds = max(
            # Supply an integer built from presentation_delay_ms to max.
            0, int(presentation_delay_ms)) / 1000.0
        # Set self._last_simulation_time to a floating-point number built from the text '-inf'.
        self._last_simulation_time = float("-inf")
        # Set self._last_payload to None.
        self._last_payload = None
        # Set self._last_inspectable_vehicles to an empty tuple.
        self._last_inspectable_vehicles = ()
        # Set self._last_vehicle_by_id to an empty dictionary.
        self._last_vehicle_by_id = {}
        # Set self._completed_vehicle_by_id to an empty dictionary.
        self._completed_vehicle_by_id = {}
        # Set self._vehicle_traces to an empty dictionary.
        self._vehicle_traces = {}
        # Set self._last_mappo_participant_ids to an empty set.
        self._last_mappo_participant_ids = set()
        # Set self._progress to the result of TrafficProgressTelemetry().
        self._progress = TrafficProgressTelemetry()
        # Set self._mappo_times to an empty dictionary.
        self._mappo_times = {}
        # Set self._last_authorized_event to None.
        self._last_authorized_event = None
        # Set self._presentation to the result of IntersectionPresentation().
        self._presentation = IntersectionPresentation()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Map snapshot using the inputs and processing steps below.
    # Input path_manager: the supplied path manager.
    # Output: a dictionary containing bounds, presentation_lanes, presentation_region.
    # Processing: iterate over the relevant records.
    def map_snapshot(path_manager):
        # Set geometries to a tuple built from a lazy sequence of a tuple built from a lazy sequence of (float(x),
        # float(y)) for (x, y) in path.centerline_geometry for path in values from path_manager.paths.
        geometries = tuple(tuple((float(x), float(y)) for x, y in
                                 # Evaluate path.centerline_geometry as part of the enclosing expression.
                                 path.centerline_geometry)
                           # Evaluate values from path_manager.paths as part of the enclosing expression.
                           for path in path_manager.paths.values())
        # Set points to a tuple built from a lazy sequence of point for geometry in geometries.
        points = tuple(point for geometry in geometries for point in geometry)
        # Set (xs, ys) to corresponding items paired from the unpacked values from points.
        xs, ys = zip(*points)
        # Set junction to the result of path_manager.network.getNode('center').getShape().
        junction = path_manager.network.getNode('center').getShape()
        # Set cx to the sum of a lazy sequence of p at 0 for p in junction divided by the number of entries in
        # junction.
        cx = sum(p[0] for p in junction) / len(junction)
        # Set cy to the sum of a lazy sequence of p at 1 for p in junction divided by the number of entries in
        # junction.
        cy = sum(p[1] for p in junction) / len(junction)
        # Fixed overview boundary, shared across scenarios and camera zooms.
        # Set radius to the maximum of a lazy sequence of (x - cx) ** 2 plus (y - cy) ** 2 raised to the power 0.5
        # for (x, y) in junction.
        radius = max(((x-cx)**2+(y-cy)**2)**.5 for x,y in junction)
        # Cover the largest supported overview (dense view at minimum zoom),
        # so zooming out cannot reveal a body excluded by a smaller crop.
        # Set extent to radius multiplied by 3.2 multiplied by 1.5 divided by 0.55.
        extent = radius * 3.2 * 1.5 / 0.55
        # Set lanes to an empty dictionary.
        lanes = {}
        # Iterate over values from path_manager.paths, binding each item to path.
        for path in path_manager.paths.values():
            # Set lanes[path.incoming_lane_id] to the text 'incoming'.
            lanes[path.incoming_lane_id] = 'incoming'
            # Set lanes[path.outgoing_lane_id] to the text 'outgoing'.
            lanes[path.outgoing_lane_id] = 'outgoing'
            # Update lanes with the supplied entries.
            lanes.update({lane:'internal' for lane in path.internal_lane_ids})
        # Return a dictionary containing bounds, presentation_lanes, presentation_region to the caller.
        return {"bounds": {"min_x": min(xs), "max_x": max(xs),
                           # Store the minimum of ys under 'min_y'.
                           # Store the maximum of ys under 'max_y'.
                           "min_y": min(ys), "max_y": max(ys)},
                # Store lanes under 'presentation_lanes'.
                'presentation_lanes':lanes,
                # Store a tuple containing cx minus extent, cy minus extent, cx plus extent, cy plus extent under
                # 'presentation_region'.
                'presentation_region':(cx-extent,cy-extent,cx+extent,cy+extent)}

    # Pace using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def pace(self):
        # Run this branch when self.presentation_delay_seconds.
        if self.presentation_delay_seconds:
            # Pause execution for self.presentation_delay_seconds.
            time.sleep(self.presentation_delay_seconds)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Prediction summary using the inputs and processing steps below.
    # Input prediction: the supplied prediction.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _prediction_summary(prediction):
        # Run this branch when the negation of prediction.
        if not prediction:
            # Return None to the caller.
            return None
        # Set (stage_name, stage) to the next item from a lazy sequence of a tuple containing name, name from
        # prediction; use None if absent for name in a tuple containing the text 'secondary', the text 'primary';
        # retain entries satisfying name from prediction; use None if absent.
        stage_name, stage = next(((name, prediction.get(name))
                                  # Evaluate a tuple containing the text 'secondary', the text 'primary' as part
                                  # of the enclosing expression.
                                  for name in ("secondary", "primary")
                                  # Evaluate name from prediction; use None if absent as part of the enclosing
                                  # expression.
                                  if prediction.get(name)), (None, None))
        # Return a dictionary containing label, confidence, stage, status to the caller.
        return {"label": prediction.get("fused_label") or (
                    # Evaluate 'label' from stage; use None if absent when stage, otherwise the text 'UNKNOWN' as
                    # part of the enclosing expression.
                    stage.get("label") if stage else "UNKNOWN"),
                # Store 'confidence' from stage; use None if absent when stage, otherwise None under 'confidence'.
                "confidence": (stage.get("confidence") if stage else None),
                # Store the result of stage_name.upper() when stage_name, otherwise the text 'WAITING' under
                # 'stage'.
                "stage": stage_name.upper() if stage_name else "WAITING",
                # Store 'status' from prediction; use the text 'WAITING_FOR_CONTEXT' if absent under 'status'.
                "status": prediction.get("status", "WAITING_FOR_CONTEXT")}

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Vehicle evidence using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input state: the state read or updated by this operation.
    # Input observations: the supplied observations.
    # Input snapshots: the supplied snapshots.
    # Input plan: the supplied plan.
    # Input control_records: the supplied control records.
    # Input policy_factors: the supplied policy factors.
    # Output: a dictionary containing speed_mps, acceleration_mps2, local_perception, ldm,
    # local_intention_predictions,...
    def _vehicle_evidence(cls, vehicle_id, state, observations, snapshots,
                          # Declare plan, control_records, policy_factors as input parameters.
                          plan, control_records, policy_factors):
        # Set ldm to the result of observations.get_ldm(vehicle_id) when observations, otherwise None.
        ldm = observations.get_ldm(vehicle_id) if observations else None
        # Set tracks to the requested attribute of ldm when ldm, otherwise an empty dictionary.
        tracks = getattr(ldm, "tracks", {}) if ldm else {}
        # Set local_targets to a dictionary of key mapped to value for (key, value) in key/value pairs from
        # tracks; retain entries satisfying key differs from vehicle_id.
        local_targets = {key: value for key, value in tracks.items()
                         # Evaluate key differs from vehicle_id as part of the enclosing expression.
                         if key != vehicle_id}
        # Set observed to a tuple built from the sorted values from a lazy sequence of key for (key, value) in
        # key/value pairs from local_targets; retain entries satisfying 'is_observed' from value; use None if
        # absent.
        observed = tuple(sorted(key for key, value in local_targets.items()
                                # Evaluate 'is_observed' from value; use None if absent as part of the enclosing
                                # expression.
                                if value.get("is_observed")))
        # Set propagated to a tuple built from the sorted values from a set built from local_targets minus a set
        # built from observed.
        propagated = tuple(sorted(set(local_targets) - set(observed)))
        # Set predictions to a tuple built from a lazy sequence of a dictionary containing target_id for (key,
        # value) in the sorted values from key/value pairs from local_targets; retain entries satisfying the
        # result of cls._prediction_summary(value.get('intention_prediction')) is a...
        predictions = tuple({"target_id": key,
                             # Evaluate the result of cls._prediction_summary('intention_prediction' from value;
                             # use None if absent) as part of the enclosing expression.
                             **cls._prediction_summary(value.get(
                                 "intention_prediction"))}
                            # Evaluate the sorted values from key/value pairs from local_targets as part of the
                            # enclosing expression.
                            for key, value in sorted(local_targets.items())
                            # Evaluate the result of cls._prediction_summary('intention_prediction' from value;
                            # use None if absent) is a different object from None as part of the enclosing
                            # expression.
                            if cls._prediction_summary(value.get(
                                # Supply None to the enclosing expression.
                                "intention_prediction")) is not None)
        # Set graph to the requested attribute of ldm when ldm, otherwise None.
        graph = getattr(ldm, "current_conflict_graph", None) if ldm else None
        # Set graph_edges to a tuple built from 'edges' from graph; use an empty tuple if absent when whether
        # graph has type dict, otherwise an empty tuple.
        graph_edges = tuple(graph.get("edges", ())) if isinstance(graph, dict) else ()
        # Set conflict_partners to a tuple built from the sorted values from a set of 'target_track_id' from edge;
        # use None if absent for edge in graph_edges; retain entries satisfying 'target_track_id' from edge; use
        # None if absent.
        conflict_partners = tuple(sorted({edge.get("target_track_id")
                                          # Evaluate graph_edges as part of the enclosing expression.
                                          for edge in graph_edges
                                          # Evaluate 'target_track_id' from edge; use None if absent as part of
                                          # the enclosing expression.
                                          if edge.get("target_track_id")}))
        # Set snapshot to the next item from a lazy sequence of item for item in snapshots; retain entries
        # satisfying 'ego_id' from item; use None if absent equals vehicle_id.
        snapshot = next((item for item in snapshots
                         # Evaluate 'ego_id' from item; use None if absent equals vehicle_id as part of the
                         # enclosing expression.
                         if item.get("ego_id") == vehicle_id), None)
        # Set local_precedence to a tuple built from a lazy sequence of a tuple containing edge at
        # 'yielding_vehicle_id', edge at 'priority_vehicle_id' for edge in 'joint_precedence_edges' from (snapshot
        # or {}); use an empty tuple if absent.
        local_precedence = tuple((edge["yielding_vehicle_id"],
                                  # Include edge at 'priority_vehicle_id' in this tuple.
                                  edge["priority_vehicle_id"])
                                 # Evaluate 'joint_precedence_edges' from (snapshot or {}); use an empty tuple if
                                 # absent as part of the enclosing expression.
                                 for edge in (snapshot or {}).get(
                                     # Supply an empty tuple to (snapshot or {}).get.
                                     "joint_precedence_edges", ()))
        # Set encoded to the requested attribute of ldm.
        encoded = getattr(ldm, "current_encoded_graph_observation", None)
        # Set gnn to a dictionary containing encoded when encoded is a different object from None, otherwise a
        # dictionary containing encoded.
        gnn = ({"encoded": True, **encoded.dashboard_summary()}
               # Store False under 'encoded'.
               if encoded is not None else {"encoded": False})
        # Set factors to a tuple built from a lazy sequence of factor for factor in policy_factors; retain entries
        # satisfying 'ego_id' from factor; use None if absent equals vehicle_id.
        factors = tuple(factor for factor in policy_factors
                        # Evaluate 'ego_id' from factor; use None if absent equals vehicle_id as part of the
                        # enclosing expression.
                        if factor.get("ego_id") == vehicle_id)
        # Set constraints to a tuple built from a lazy sequence of record for record in control_records; retain
        # entries satisfying the requested attribute of record equals vehicle_id.
        constraints = tuple(record for record in control_records
                            # Evaluate the requested attribute of record equals vehicle_id as part of the
                            # enclosing expression.
                            if getattr(record, "vehicle_id", None) == vehicle_id)
        # Set cap to the minimum of a lazy sequence of a floating-point number built from
        # record.requested_speed_cap_mps for record... when constraints, otherwise None.
        cap = (min(float(record.requested_speed_cap_mps)
                   # Evaluate constraints as part of the enclosing expression.
                   for record in constraints) if constraints else None)
        # Set planner_state to the text 'READY' when vehicle_id belongs to plan.ready_vehicle_ids, otherwise the
        # text 'BLOCKED' when vehicle_id belongs to plan.blocked_vehicle_ids, otherwise the text 'NOT_APPLICABLE'.
        planner_state = ("READY" if vehicle_id in plan.ready_vehicle_ids else
                         # Evaluate the text 'BLOCKED' when vehicle_id belongs to plan.blocked_vehicle_ids,
                         # otherwise the text 'NOT_APPLICABLE' as part of the enclosing expression.
                         "BLOCKED" if vehicle_id in plan.blocked_vehicle_ids else
                         "NOT_APPLICABLE")
        # Return a dictionary containing speed_mps, acceleration_mps2, local_perception, ldm,
        # local_intention_predictions,... to the caller.
        return {
            # Store a floating-point number built from state at 'speed' under 'speed_mps'.
            "speed_mps": float(state["speed"]),
            # Store a floating-point number built from state at 'accel' under 'acceleration_mps2'.
            "acceleration_mps2": float(state["accel"]),
            # Store a dictionary containing observed_vehicle_ids, observed_vehicle_count under 'local_perception'.
            # Store observed under 'observed_vehicle_ids'.
            "local_perception": {"observed_vehicle_ids": observed,
                                 # Store the number of entries in observed under 'observed_vehicle_count'.
                                 "observed_vehicle_count": len(observed)},
            # Store a dictionary containing track_count, tracked_vehicle_ids, propagated_vehicle_ids,
            # history_lengths under 'ldm'.
            # Store the number of entries in local_targets under 'track_count'.
            "ldm": {"track_count": len(local_targets),
                    # Store a tuple built from the sorted values from local_targets under 'tracked_vehicle_ids'.
                    "tracked_vehicle_ids": tuple(sorted(local_targets)),
                    # Store propagated under 'propagated_vehicle_ids'.
                    "propagated_vehicle_ids": propagated,
                    # Store a dictionary of key mapped to the number of entries in 'position_history' from value;
                    # use an empty tuple if absent for (key, value) in the sorted values from key/value pairs from
                    # local_targets under 'history_lengths'.
                    "history_lengths": {key: len(value.get(
                        # Supply an empty tuple to value.get.
                        "position_history", ()))
                        # Evaluate the sorted values from key/value pairs from local_targets as part of the
                        # enclosing expression.
                        for key, value in sorted(local_targets.items())}},
            # These are ego-local target predictions, never route truth.
            # Store predictions under 'local_intention_predictions'.
            "local_intention_predictions": predictions,
            # Store a dictionary containing relevant, partners under 'conflict'.
            # Store a Boolean built from conflict_partners under 'relevant'.
            "conflict": {"relevant": bool(conflict_partners),
                         # Store conflict_partners under 'partners'.
                         "partners": conflict_partners},
            # Store local_precedence under 'local_precedence_edges'.
            "local_precedence_edges": local_precedence,
            # Store gnn under 'gnn'.
            "gnn": gnn,
            # Store a dictionary containing factors under 'negotiation'.
            # Store factors under 'factors'.
            "negotiation": {"factors": factors},
            # Store a dictionary containing state under 'planner'.
            # Store planner_state under 'state'.
            "planner": {"state": planner_state},
            # Store a dictionary containing speed_constraint_active, speed_cap_mps, source under 'control'.
            # Store a Boolean built from constraints under 'speed_constraint_active'.
            "control": {"speed_constraint_active": bool(constraints),
                        # Store cap under 'speed_cap_mps'.
                        "speed_cap_mps": cap,
                        # Store the text 'DETERMINISTIC_PRECEDENCE_CONTROLLER' when constraints, otherwise the
                        # text 'SUMO_NATIVE' under 'source'.
                        "source": ("DETERMINISTIC_PRECEDENCE_CONTROLLER"
                                   # Evaluate constraints as part of the enclosing expression.
                                   if constraints else "SUMO_NATIVE")}}

    # Publish using the inputs and processing steps below.
    # Input simulation_time: the supplied simulation time.
    # Input map_state: the supplied map state.
    # Input running: the supplied running.
    # Input status: the supplied status.
    # Input participants: the supplied participants.
    # Input ready: the supplied ready.
    # Input blocked: the supplied blocked.
    # Input original_graph: the supplied original graph.
    # Input effective_graph: the supplied effective graph.
    # Input mappo_invocation: the supplied mappo invocation.
    # Input completed: the supplied completed.
    # Input scheduled: the supplied scheduled.
    # Input scenario_id: the supplied scenario id.
    # Input scientific_states: the supplied scientific states.
    # Input observations: the supplied observations.
    # Input snapshots: the supplied snapshots.
    # Input plan: the supplied plan.
    # Input control_records: the supplied control records.
    # Input policy_factors: the supplied policy factors.
    # Input events: the supplied events.
    # Input run_metrics: the supplied run metrics.
    # Input execution_decisions: the supplied execution decisions.
    # Input coordination_participants: the supplied coordination participants.
    # Input coordination_timestamp: the supplied coordination timestamp.
    # Input run_id: the supplied run id.
    # Input force: the supplied force.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def publish(self, *, simulation_time, map_state, running, status,
                # Declare participants, ready, blocked, original_graph as input parameters.
                participants=(), ready=(), blocked=(), original_graph=(),
                # Declare effective_graph, mappo_invocation as input parameters.
                effective_graph=(), mappo_invocation="NOT_REQUIRED",
                # Declare completed, scheduled, scenario_id as input parameters.
                completed=0, scheduled=12, scenario_id="default_panel",
                # Declare scientific_states, observations, snapshots as input parameters.
                scientific_states=None, observations=None, snapshots=(),
                # Declare plan, control_records, policy_factors, events as input parameters.
                plan=None, control_records=(), policy_factors=(), events=(),
                # Declare run_metrics as input parameter.
                run_metrics=None,
                # Declare execution_decisions, coordination_participants as input parameters.
                execution_decisions=(), coordination_participants=None,
                # Declare coordination_timestamp, run_id as input parameters.
                coordination_timestamp=None, run_id=None,
                # Declare force as input parameter.
                force=False):
        # Set now to a floating-point number built from simulation_time.
        now = float(simulation_time)
        # The existing final publisher call omits run_id. Preserve identity and
        # presentation tombstones through shutdown; this is not a new run.
        # Run this branch when force and the negation of running and run_id is the same object as None and
        # self._last_payload is a different object from None.
        if force and not running and run_id is None and self._last_payload is not None:
            # Set run_id to 'run_id' from self._last_payload; use None if absent.
            run_id = self._last_payload.get('run_id')
        # Set identity to a tuple containing run_id, scenario_id.
        identity = (run_id, scenario_id)
        # Run this branch when self._presentation.run is a different object from None and self._presentation.run
        # differs from identity.
        if self._presentation.run is not None and self._presentation.run != identity:
            # Clear the stored entries in self._last_vehicle_by_id.
            self._last_vehicle_by_id.clear()
            # Clear the stored entries in self._completed_vehicle_by_id.
            self._completed_vehicle_by_id.clear()
            # Clear the stored entries in self._vehicle_traces.
            self._vehicle_traces.clear()
            # Clear the stored entries in self._mappo_times.
            self._mappo_times.clear()
            # Clear the stored entries in self._last_mappo_participant_ids.
            self._last_mappo_participant_ids.clear()
            # Set self._last_authorized_event to None.
            self._last_authorized_event = None
            # Set self._last_payload to None.
            self._last_payload = None
            # Set self._last_simulation_time to a floating-point number built from the text '-inf'.
            self._last_simulation_time = float('-inf')
        # Call self._presentation.reset_for with the supplied arguments.
        self._presentation.reset_for((run_id, scenario_id))
        # Run this branch when the negation of force and now minus self._last_simulation_time is less than
        # self.interval.
        if not force and now - self._last_simulation_time < self.interval:
            # Return None to the caller.
            return None
        # Set self._last_simulation_time to now.
        self._last_simulation_time = now
        # Set (ready_set, blocked_set) to a tuple containing a set built from ready, a set built from blocked.
        ready_set, blocked_set = set(ready), set(blocked)
        # Set participant_set to a set built from participants.
        participant_set = set(participants)
        # Set receipts to a set built from coordination_participants when coordination_participants is a different
        # object from None, otherwise participants.
        receipts = set(coordination_participants if coordination_participants is not None else participants)
        # Set decision_by_id to a dictionary of d.ego_id mapped to d for d in execution_decisions.
        decision_by_id = {d.ego_id:d for d in execution_decisions}
        # Run this branch when mappo_invocation equals the text 'AUTHORIZED'.
        if mappo_invocation == "AUTHORIZED":
            # Update self._last_mappo_participant_ids with the supplied entries.
            self._last_mappo_participant_ids.update(receipts)
            # Iterate over receipts, binding each item to ego.
            for ego in receipts:
                # Set self._mappo_times[ego] to coordination_timestamp when coordination_timestamp is a different
                # object from None, otherwise now.
                self._mappo_times[ego] = coordination_timestamp if coordination_timestamp is not None else now
        # Set vehicles to an empty list.
        vehicles = []
        # Iterate over the sorted values from the identifiers reported by self.traci.vehicle.getIDList, binding
        # each item to vehicle_id.
        for vehicle_id in sorted(self.traci.vehicle.getIDList()):
            # Set state_record to vehicle_id from (scientific_states or {}); use None if absent.
            state_record = ((scientific_states or {}).get(vehicle_id))
            # Set (x, y) to state_record at 'position' when state_record, otherwise the SUMO position of vehicle
            # vehicle_id.
            x, y = (state_record["position"] if state_record else
                    # Evaluate the SUMO position of vehicle vehicle_id as part of the enclosing expression.
                    self.traci.vehicle.getPosition(vehicle_id))
            # Set angle to a floating-point number built from state_record at 'angle_degrees' when state_record,
            # otherwise a floating-point number built from the result of self.traci.vehicle.getAngle(vehicle_id).
            angle = (float(state_record["angle_degrees"]) if state_record else
                     # Evaluate a floating-point number built from the result of
                     # self.traci.vehicle.getAngle(vehicle_id) as part of the enclosing expression.
                     float(self.traci.vehicle.getAngle(vehicle_id)))
            # Body color is the physical permission state. Negotiation is a
            # separate presentation attribute and can never mask a plan.
            # Set state to the text 'BLOCKED' when vehicle_id belongs to blocked_set, otherwise the text 'READY'
            # when vehicle_id belongs to ready_set, otherwise the text 'NEGOTIATING' when status == 'NEGOTIATING'
            # and vehicle_id in participant_set, otherwise the text 'APPROACHING'.
            state = ("BLOCKED" if vehicle_id in blocked_set else
                     # Evaluate the text 'READY' when vehicle_id belongs to ready_set, otherwise the text
                     # 'NEGOTIATING' when status equals 'NEGOTIATING' and vehicle_id belongs to participant_set,
                     # otherwise the text 'APPROACHING' as part of the enclosing expression.
                     "READY" if vehicle_id in ready_set else
                     # Evaluate the text 'NEGOTIATING' when status equals the text 'NEGOTIATING' and vehicle_id
                     # belongs to participant_set, otherwise the text 'APPROACHING' as part of the enclosing
                     # expression.
                     "NEGOTIATING" if status == 'NEGOTIATING' and vehicle_id in participant_set else
                     "APPROACHING")
            # Set negotiation_involvement to a Boolean built from vehicle_id belongs to
            # self._last_mappo_participant_ids.
            negotiation_involvement = bool(
                # Supply vehicle_id belongs to self._last_mappo_participant_ids to bool.
                vehicle_id in self._last_mappo_participant_ids)
            # Set vehicle to a dictionary containing id, front_bumper_x, front_bumper_y, angle_degrees, length_m,
            # width_m, speed_mps,...
            vehicle = {"id": vehicle_id,
                             # Store a floating-point number built from x under 'front_bumper_x'.
                             "front_bumper_x": float(x),
                             # Store a floating-point number built from y under 'front_bumper_y'.
                             "front_bumper_y": float(y),
                             # Store angle under 'angle_degrees'.
                             "angle_degrees": angle,
                             # Store a floating-point number built from state_record at 'length' when
                             # state_record, otherwise the result of self.traci.vehicle.getLength(vehicle_id)
                             # under 'length_m'.
                             "length_m": float(state_record["length"] if
                                 # Evaluate the result of self.traci.vehicle.getLength(vehicle_id) as part of the
                                 # enclosing expression.
                                 state_record else self.traci.vehicle.getLength(vehicle_id)),
                             # Store a floating-point number built from state_record at 'width' when state_record,
                             # otherwise the result of self.traci.vehicle.getWidth(vehicle_id) under 'width_m'.
                             "width_m": float(state_record["width"] if
                                 # Evaluate the result of self.traci.vehicle.getWidth(vehicle_id) as part of the
                                 # enclosing expression.
                                 state_record else self.traci.vehicle.getWidth(vehicle_id)),
                             # Store a floating-point number built from state_record at 'speed' when state_record,
                             # otherwise the SUMO speed of vehicle vehicle_id under 'speed_mps'.
                             "speed_mps": float(state_record["speed"] if
                                 # Evaluate the SUMO speed of vehicle vehicle_id as part of the enclosing
                                 # expression.
                                 state_record else self.traci.vehicle.getSpeed(vehicle_id)),
                             # Store state under 'display_state'.
                             "display_state": state,
                             # Store state when state differs from the text 'NEGOTIATING', otherwise the text
                             # 'APPROACHING' under 'execution_state'.
                             "execution_state": (state if state != "NEGOTIATING"
                                                 # Supply the text 'APPROACHING' to the enclosing expression.
                                                 else "APPROACHING"),
                             # Store negotiation_involvement under 'negotiation_involvement'.
                             "negotiation_involvement": negotiation_involvement}
            # Run this branch when state_record is a different object from None and plan is a different object
            # from None.
            if state_record is not None and plan is not None:
                # Update vehicle with the supplied entries.
                vehicle.update(self._vehicle_evidence(
                    # Supply state_record to self._vehicle_evidence.
                    vehicle_id, state_record, observations, snapshots, plan,
                    # Supply control_records to self._vehicle_evidence.
                    control_records, policy_factors))
            # Update vehicle with the supplied entries.
            vehicle.update(explain_decision(decision_by_id.get(vehicle_id),vehicle['speed_mps'],now))
            # Set own_snapshot to the next item from a lazy sequence of s for s in snapshots; retain entries
            # satisfying 'ego_id' from s; use None if absent equals vehicle_id.
            own_snapshot = next((s for s in snapshots if s.get('ego_id')==vehicle_id),None)
            # Set has_receipt to mappo_invocation equals the text 'AUTHORIZED' and vehicle_id belongs to receipts.
            has_receipt = mappo_invocation=='AUTHORIZED' and vehicle_id in receipts
            # Set factors to 'factors' from vehicle.get('negotiation', {}); use an empty tuple if absent when
            # has_receipt, otherwise an empty tuple.
            factors = vehicle.get('negotiation',{}).get('factors',()) if has_receipt else ()
            # Set vehicle['negotiation'] to a dictionary containing factors.
            vehicle['negotiation'] = {'factors':factors,
                # Evaluate the result of explain_mappo('negotiation_status' from (own_snapshot or {}); use None if
                # absent, has_receipt, vehicle_id from...) as part of the enclosing expression.
                **explain_mappo((own_snapshot or {}).get('negotiation_status'),has_receipt,
                    # Supply vehicle_id from self._mappo_times; use None if absent to explain_mappo.
                    self._mappo_times.get(vehicle_id),now,factors)}
            # Run this branch when vehicle['negotiation'] at 'status' equals the text 'ELIGIBLE' and
            # mappo_invocation equals the text 'BLOCKED'.
            if vehicle['negotiation']['status']=='ELIGIBLE' and mappo_invocation=='BLOCKED':
                # Set vehicle['negotiation']['status'] to the text 'BLOCKED'.
                vehicle['negotiation']['status']='BLOCKED'
                # Set vehicle['negotiation']['locally_eligible'] to True.
                vehicle['negotiation']['locally_eligible']=True
            # Set decision to vehicle_id from decision_by_id; use None if absent.
            decision = decision_by_id.get(vehicle_id)
            # Run this branch when state_record is a different object from None and 'presentation_lanes' from
            # map_state; use None if absent.
            if state_record is not None and map_state.get('presentation_lanes'):
                # Update vehicle with the supplied entries.
                vehicle.update(self._presentation.classify(vehicle, state_record, decision, map_state,
                    # Supply pending as status equals the text 'NEGOTIATING' and vehicle_id belongs to
                    # participant_set and the negation of has_receipt.
                    pending=status == 'NEGOTIATING' and vehicle_id in participant_set and not has_receipt))
                # Run this branch when vehicle at 'display_state' equals the text 'APPROACHING'.
                if vehicle['display_state'] == 'APPROACHING':
                    # Set vehicle['permission_label'] to the text 'APPROACHING'.
                    vehicle['permission_label'] = 'APPROACHING'
            # Run this branch when has_receipt and decision is a different object from None.
            if has_receipt and decision is not None:
                # Set vehicle['negotiation']['execution_status'] to the text 'SAFETY_FALLBACK' when
                # decision.fallback_pairs, otherwise the text 'SHIELD_REJECTION' when
                # decision.shield_rejection_reason, otherwise the text 'ENTRY_HELD' when decision.permission
                # differs from 'PERMITTED', otherwise the text 'LOCAL_EXECUTION'.
                vehicle['negotiation']['execution_status'] = (
                    # Evaluate the text 'SAFETY_FALLBACK' when decision.fallback_pairs, otherwise the text
                    # 'SHIELD_REJECTION' when decision.shield_rejection_reason, otherwise the text 'ENTRY_HELD'
                    # when decision.permission differs from 'PERMITTED', otherwise the text 'LOCAL_EXECUTION' as
                    # part of the enclosing expression.
                    'SAFETY_FALLBACK' if decision.fallback_pairs else
                    # Evaluate the text 'SHIELD_REJECTION' when decision.shield_rejection_reason, otherwise the
                    # text 'ENTRY_HELD' when decision.permission differs from the text 'PERMITTED', otherwise the
                    # text 'LOCAL_EXECUTION' as part of the enclosing expression.
                    'SHIELD_REJECTION' if decision.shield_rejection_reason else
                    # Evaluate the text 'ENTRY_HELD' when decision.permission differs from the text 'PERMITTED',
                    # otherwise the text 'LOCAL_EXECUTION' as part of the enclosing expression.
                    'ENTRY_HELD' if decision.permission!='PERMITTED' else 'LOCAL_EXECUTION')
                # Run this branch when decision.permission equals the text 'SAFE_HOLD'.
                if decision.permission=='SAFE_HOLD':
                    # Set vehicle['negotiation']['status'] to the text 'BLOCKED'.
                    vehicle['negotiation']['status']='BLOCKED'
                    # Set vehicle['negotiation']['reason'] to the text 'OUTCOME_RECEIVED_BUT_EXECUTION_HELD'.
                    vehicle['negotiation']['reason']='OUTCOME_RECEIVED_BUT_EXECUTION_HELD'
            # Append vehicle to vehicles.
            vehicles.append(vehicle)
        # Set current_ids to a set of item at 'id' for item in vehicles.
        current_ids = {item["id"] for item in vehicles}
        # Set departed_ids to a set built from self._last_vehicle_by_id minus current_ids when scientific_states
        # is a different object from None, otherwise an empty set.
        departed_ids = (set(self._last_vehicle_by_id) - current_ids
                        # Evaluate scientific_states is a different object from None as part of the enclosing
                        # expression.
                        if scientific_states is not None else set())
        # Iterate over departed_ids, binding each item to vehicle_id.
        for vehicle_id in departed_ids:
            # Set final to a dictionary built from self._last_vehicle_by_id at vehicle_id.
            final = dict(self._last_vehicle_by_id[vehicle_id])
            # Set final['display_state'] to the text 'CLEARED'.
            final["display_state"] = "CLEARED"
            # Set self._completed_vehicle_by_id[vehicle_id] to final.
            self._completed_vehicle_by_id[vehicle_id] = final
            # Call self._trace with the supplied arguments.
            self._trace(vehicle_id, now, "COMPLETED", "Vehicle left simulation")
        # Iterate over vehicles when scientific_states is a different object from None, otherwise an empty tuple,
        # binding each item to vehicle.
        for vehicle in (vehicles if scientific_states is not None else ()):
            # Set vehicle_id to vehicle at 'id'.
            vehicle_id = vehicle["id"]
            # Set previous to vehicle_id from self._last_vehicle_by_id; use None if absent.
            previous = self._last_vehicle_by_id.get(vehicle_id)
            # Run this branch when previous is the same object as None.
            if previous is None:
                # Call self._trace with the supplied arguments.
                self._trace(vehicle_id, now, "FIRST_OBSERVED", "Runtime state available")
            # Call self._record_meaningful_transitions with the supplied arguments.
            self._record_meaningful_transitions(vehicle_id, previous, vehicle, now)
            # Set self._last_vehicle_by_id[vehicle_id] to a dictionary built from vehicle.
            self._last_vehicle_by_id[vehicle_id] = dict(vehicle)
        # Run this branch when force and status equals the text 'FINISHED' and an integer built from completed is
        # at least an integer built from scheduled.
        if (force and status == "FINISHED" and int(completed) >= int(scheduled)):
            # Iterate over key/value pairs from self._last_vehicle_by_id, binding each item to (vehicle_id,
            # vehicle).
            for vehicle_id, vehicle in self._last_vehicle_by_id.items():
                # Run this branch when vehicle_id does not belong to self._completed_vehicle_by_id.
                if vehicle_id not in self._completed_vehicle_by_id:
                    # Set final to a dictionary built from vehicle.
                    # Set final['display_state'] to the text 'CLEARED'.
                    final = dict(vehicle); final["display_state"] = "CLEARED"
                    # Set self._completed_vehicle_by_id[vehicle_id] to final.
                    self._completed_vehicle_by_id[vehicle_id] = final
        # Set meaningful_events to tuple(events) sliced by -12:.
        meaningful_events = tuple(events)[-12:]
        # Set authorized_events to a tuple built from a lazy sequence of item for item in meaningful_events;
        # retain entries satisfying 'mappo_invocation' from item; use None if absent equals the text 'AUTHORIZED'.
        authorized_events = tuple(item for item in meaningful_events
                                  # Evaluate 'mappo_invocation' from item; use None if absent equals the text
                                  # 'AUTHORIZED' as part of the enclosing expression.
                                  if item.get("mappo_invocation") == "AUTHORIZED")
        # Run this branch when authorized_events.
        if authorized_events:
            # Set self._last_authorized_event to authorized_events at -1.
            self._last_authorized_event = authorized_events[-1]
        # Set rule_events to a tuple built from a lazy sequence of item for item in meaningful_events; retain
        # entries satisfying 'event' from item; use None if absent equals the text 'REGULATORY_ORDER_RESOLVED'.
        rule_events = tuple(item for item in meaningful_events
                            # Evaluate 'event' from item; use None if absent equals the text
                            # 'REGULATORY_ORDER_RESOLVED' as part of the enclosing expression.
                            if item.get("event") == "REGULATORY_ORDER_RESOLVED")
        # Set renegotiations to a tuple built from a lazy sequence of item for item in meaningful_events; retain
        # entries satisfying 'event' from item; use None if absent equals the text 'PLAN_INVALIDATED'.
        renegotiations = tuple(item for item in meaningful_events
                               # Evaluate 'event' from item; use None if absent equals the text 'PLAN_INVALIDATED'
                               # as part of the enclosing expression.
                               if item.get("event") == "PLAN_INVALIDATED")
        # Set payload to a dictionary containing schema, vehicle_state_contract, run_id, display_only, running,
        # scenario_id,...
        payload = {"schema": "PANEL_DEMO_BROWSER_STATE_V3",
                   # Store VERSION under 'vehicle_state_contract'.
                   # Store run_id under 'run_id'.
                   "vehicle_state_contract": VERSION, "run_id": run_id,
                   # Store True under 'display_only'.
                   # Store a Boolean built from running under 'running'.
                   "display_only": True, "running": bool(running),
                   # Store a string built from scenario_id under 'scenario_id'.
                   "scenario_id": str(scenario_id),
                   # Store now under 'simulation_time'.
                   # Store status under 'status'.
                   "simulation_time": now, "status": status,
                   # Store a tuple built from participants under 'participants'.
                   # Store a tuple built from ready under 'ready'.
                   "participants": tuple(participants), "ready": tuple(ready),
                   # Store a tuple built from blocked under 'blocked'.
                   "blocked": tuple(blocked),
                   # Store a tuple built from original_graph under 'original_graph'.
                   "original_graph": tuple(original_graph),
                   # Store a tuple built from effective_graph under 'effective_graph'.
                   "effective_graph": tuple(effective_graph),
                   # Store mappo_invocation under 'mappo_invocation'.
                   "mappo_invocation": mappo_invocation,
                   # Store an integer built from completed under 'completed'.
                   # Store an integer built from scheduled under 'scheduled'.
                   "completed": int(completed), "scheduled": int(scheduled),
                   # Store a list of v for v in vehicles; retain entries satisfying 'presentation_visible' from v;
                   # use True if absent under 'vehicles'.
                   "vehicles": [v for v in vehicles if v.get('presentation_visible', True)],
                   # Store the number of entries in vehicles under 'active_sumo_vehicles'.
                   "active_sumo_vehicles": len(vehicles),
                   # Store vehicles under 'scientific_vehicles'.
                   "scientific_vehicles": vehicles,
                   # Store a tuple built from the sorted values from self._presentation.exited under
                   # 'intersection_cleared_vehicle_ids'.
                   "intersection_cleared_vehicle_ids": tuple(sorted(self._presentation.exited)),
                   # Store a tuple built from a lazy sequence of self._completed_vehicle_by_id at key for key in
                   # the sorted values from self._completed_vehicle_by_id under 'completed_vehicles'.
                   "completed_vehicles": tuple(
                       # Evaluate self._completed_vehicle_by_id at key as part of the enclosing expression.
                       self._completed_vehicle_by_id[key]
                       # Evaluate the sorted values from self._completed_vehicle_by_id as part of the enclosing
                       # expression.
                       for key in sorted(self._completed_vehicle_by_id)),
                   # Store meaningful_events under 'events'.
                   "events": meaningful_events,
                   # Store authorized_events under 'negotiation_events'.
                   "negotiation_events": authorized_events,
                   # Store self._last_authorized_event under 'last_mappo_event'.
                   "last_mappo_event": self._last_authorized_event,
                   # Store a dictionary containing mappo_authorized_events, mappo_negotiation_observed,
                   # rule_resolved_events,... under 'run_negotiation_summary'.
                   "run_negotiation_summary": {
                       # Store 'mappo_decision_epochs' from (run_metrics or {}); use the number of entries in
                       # authorized_events if absent under 'mappo_authorized_events'.
                       "mappo_authorized_events": (run_metrics or {}).get('mappo_decision_epochs',len(authorized_events)),
                       # Store a Boolean built from 'mappo_decision_epochs' from (run_metrics or {}); use 0 if
                       # absent or self._last_authorized_event under 'mappo_negotiation_observed'.
                       "mappo_negotiation_observed": bool((run_metrics or {}).get('mappo_decision_epochs',0) or self._last_authorized_event),
                       # Store 'rule_resolved_events' from (run_metrics or {}); use the number of entries in
                       # rule_events if absent under 'rule_resolved_events'.
                       "rule_resolved_events": (run_metrics or {}).get('rule_resolved_events',len(rule_events)),
                       # Store the number of entries in renegotiations under 'renegotiation_events'.
                       "renegotiation_events": len(renegotiations)},
                   # Store a dictionary built from run_metrics or an empty dictionary under 'run_metrics'.
                   "run_metrics": dict(run_metrics or {}),
                   # Evaluate map_state as part of the enclosing expression.
                   **map_state}
        # Run this branch when scientific_states is a different object from None.
        if scientific_states is not None:
            # Set payload['traffic_progress'] to the result of self._progress.observe(now, scientific_states,
            # participants, blocked_set, status, original_graph).
            payload["traffic_progress"] = self._progress.observe(now,
                # Supply scientific_states to self._progress.observe.
                scientific_states, participants, blocked_set, status, original_graph)
        # Run this branch when vehicles and whether any item is true in a lazy sequence of 'planner' belongs to
        # item for item in vehicles.
        if vehicles and any("planner" in item for item in vehicles):
            # Set self._last_inspectable_vehicles to a tuple built from vehicles.
            self._last_inspectable_vehicles = tuple(vehicles)
        # Run this branch when force and the negation of running and scientific_states is the same object as None
        # and self._last_payload is a different object from None.
        if force and not running and scientific_states is None and self._last_payload is not None:
            # Set previous_by_id to a dictionary of v at 'id' mapped to v for v in self._last_payload at
            # 'vehicles'.
            previous_by_id = {v['id']:v for v in self._last_payload['vehicles']}
            # Update previous_by_id with the supplied entries.
            previous_by_id.update(self._last_vehicle_by_id)
            # Run this branch when the text 'traffic_progress' belongs to self._last_payload.
            if "traffic_progress" in self._last_payload:
                # Set payload['traffic_progress'] to self._last_payload at 'traffic_progress'.
                payload["traffic_progress"] = self._last_payload["traffic_progress"]
            # Set payload['vehicles'] to an empty tuple when status equals the text 'FINISHED' and an integer
            # built from completed is at least an integer built from scheduled, otherwise a tuple built from a
            # lazy sequence of a dictionary built from previous_by_id.get(v['id'], {}) for v in vehicles.
            payload["vehicles"] = (() if status == "FINISHED" and
                                   # Evaluate an integer built from completed is at least an integer built from
                                   # scheduled as part of the enclosing expression.
                                   int(completed) >= int(scheduled) else
                                   # Supply the unpacked keyword arguments as v.
                                   tuple(dict(previous_by_id.get(v['id'],{}),**v)
                                         # Evaluate vehicles as part of the enclosing expression.
                                         for v in vehicles))
            # Iterate over payload at 'vehicles', binding each item to vehicle.
            for vehicle in payload['vehicles']:
                # Terminal physical readings are current; prior permission
                # evidence remains explicitly dated, never silently refreshed.
                # Set previous to vehicle['id'] from previous_by_id; use an empty dictionary if absent.
                previous = previous_by_id.get(vehicle['id'],{})
                # Iterate over a tuple containing the text 'entry_permission', the text 'permission_label', the
                # text 'negotiation', the text..., binding each item to field.
                for field in ('entry_permission','permission_label','negotiation','speed_command','display_state','execution_state'):
                    # Run this branch when field belongs to previous.
                    # Set vehicle[field] to previous at field.
                    if field in previous:vehicle[field]=previous[field]
                # Set vehicle['permission_evidence_current'] to False.
                vehicle['permission_evidence_current'] = False
                # Run this branch when 'current_receipt' from vehicle.get('negotiation', {}); use None if absent.
                if vehicle.get('negotiation',{}).get('current_receipt'):
                    # Set vehicle['negotiation'] to a dictionary built from vehicle at 'negotiation'.
                    vehicle['negotiation'] = dict(vehicle['negotiation'],status='DECISION_EXPIRED',
                        # Supply current_receipt as False.
                        # Supply factors as an empty tuple.
                        # Supply actions as an empty tuple.
                        # Supply local_actor_action_count as 0.
                        current_receipt=False,factors=(),actions=(),local_actor_action_count=0)
                # Run this branch when 'entry_permission' from vehicle; use None if absent.
                if vehicle.get('entry_permission'):
                    # Set vehicle['permission_label'] to the text 'LAST REPORTED: READY / GO' when
                    # vehicle['entry_permission'] at 'authorized', otherwise the text 'LAST REPORTED: ENTRY HELD
                    # /' plus vehicle at 'motion_state'.
                    vehicle['permission_label'] = ('LAST REPORTED: READY / GO' if vehicle['entry_permission']['authorized']
                        # Evaluate the text 'LAST REPORTED: ENTRY HELD /' plus vehicle at 'motion_state' as part
                        # of the enclosing expression.
                        else 'LAST REPORTED: ENTRY HELD / '+vehicle['motion_state'])
            # Set payload['events'] to self._last_payload at 'events'.
            payload["events"] = self._last_payload["events"]
            # Set payload['negotiation_events'] to self._last_payload at 'negotiation_events'.
            payload["negotiation_events"] = self._last_payload[
                "negotiation_events"]
            # Set payload['last_mappo_event'] to self._last_payload at 'last_mappo_event'.
            payload["last_mappo_event"] = self._last_payload[
                "last_mappo_event"]
            # Set payload['run_negotiation_summary'] to self._last_payload at 'run_negotiation_summary'.
            payload["run_negotiation_summary"] = self._last_payload[
                "run_negotiation_summary"]
            # Set payload['run_metrics'] to a dictionary built from run_metrics or self._last_payload at
            # 'run_metrics'.
            payload["run_metrics"] = dict(run_metrics or
                                           # Evaluate self._last_payload at 'run_metrics' as part of the enclosing
                                           # expression.
                                           self._last_payload["run_metrics"])
            # Iterate over a tuple containing the text 'participants', the text 'ready', the text 'blocked', the
            # text 'original_graph', the text..., binding each item to key.
            for key in ("participants", "ready", "blocked", "original_graph",
                        "effective_graph", "mappo_invocation"):
                # Set payload[key] to self._last_payload at key.
                payload[key] = self._last_payload[key]
            # Run this branch when status equals the text 'FINISHED' and an integer built from completed is at
            # least an integer built from scheduled.
            if status == "FINISHED" and int(completed) >= int(scheduled):
                # Iterate over a tuple containing the text 'participants', the text 'ready', the text 'blocked',
                # binding each item to key.
                for key in ("participants", "ready", "blocked"):
                    # Set payload[key] to an empty tuple.
                    payload[key] = ()
                # Set payload['mappo_invocation'] to the text 'NOT_REQUIRED'.
                payload["mappo_invocation"] = "NOT_REQUIRED"
        # Set payload['vehicles'] to a tuple built from a lazy sequence of v for v in payload at 'vehicles';
        # retain entries satisfying v['id'] does not belong to self._presentation.exited and
        # 'presentation_visible' from...
        payload['vehicles'] = tuple(v for v in payload['vehicles']
            # Evaluate v at 'id' does not belong to self._presentation.exited and 'presentation_visible' from v;
            # use True if absent as part of the enclosing expression.
            if v['id'] not in self._presentation.exited and v.get('presentation_visible', True))
        # Set self._last_payload to payload.
        self._last_payload = payload
        # Create the directory requested by self.path.parent.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Set temporary to the result of self.path.with_suffix(self.path.suffix plus the text '.tmp').
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        # Iterate over the integer range defined by 10 when force and the negation of running, otherwise 1,
        # binding each item to attempt.
        for attempt in range(10 if force and not running else 1):
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Write the supplied text to temporary.
                temporary.write_text(json.dumps(payload, separators=(",", ":")),
                                     # Supply encoding as the text 'utf-8'.
                                     encoding="utf-8")
                # Call temporary.replace with the supplied arguments.
                temporary.replace(self.path)
                # Leave the nearest enclosing loop immediately.
                break
            # Handle OSError using the recovery steps below.
            except OSError:
                # Hot frames never delay control. After simulation ends, give
                # Windows readers a bounded chance to release the destination.
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Call temporary.unlink with the supplied arguments.
                    temporary.unlink(missing_ok=True)
                # Handle OSError using the recovery steps below.
                except OSError:
                    # Keep this block syntactically valid without performing an operation.
                    pass
                # Run this branch when force and the negation of running and attempt is less than 9.
                if force and not running and attempt < 9:
                    # Pause execution for 0.02.
                    time.sleep(0.02)
        # Return None to the caller.
        return None

    # Trace using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input timestamp: the supplied timestamp.
    # Input stage: the supplied stage.
    # Input value: the supplied value.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _trace(self, vehicle_id, timestamp, stage, value):
        # Set trace to the result of self._vehicle_traces.setdefault(vehicle_id, an empty list).
        trace = self._vehicle_traces.setdefault(vehicle_id, [])
        # Set record to a dictionary containing timestamp, stage, value.
        record = {"timestamp": float(timestamp), "stage": stage,
                  # Store value under 'value'.
                  "value": value}
        # Run this branch when the negation of trace or a tuple containing trace[-1] at 'stage', trace[-1] at
        # 'value' differs from a tuple containing stage, value.
        if not trace or (trace[-1]["stage"], trace[-1]["value"]) != (stage, value):
            # Append record to trace.
            trace.append(record)

    # Record meaningful transitions using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input previous: the supplied previous.
    # Input current: the supplied current.
    # Input now: the time used for this operation.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _record_meaningful_transitions(self, vehicle_id, previous, current, now):
        # Set fields to a tuple containing a tuple containing the text 'planner', the text 'PLANNER', a tuple
        # containing the text 'control', the text...
        fields = (("planner", "PLANNER"), ("control", "CONTROL"),
                  # Include a tuple containing the text 'local_precedence_edges', the text 'PRECEDENCE' in this
                  # tuple.
                  ("conflict", "CONFLICT"), ("local_precedence_edges", "PRECEDENCE"),
                  # Include a tuple containing the text 'negotiation', the text 'MAPPO' in this tuple.
                  ("gnn", "GNN"), ("negotiation", "MAPPO"))
        # Iterate over fields, binding each item to (key, stage).
        for key, stage in fields:
            # Set value to key from current; use None if absent.
            value = current.get(key)
            # Set previous_value to key from previous; use None if absent when previous, otherwise None.
            previous_value = previous.get(key) if previous else None
            # Run this branch when key equals the text 'negotiation' and value.
            if key == 'negotiation' and value:
                # Elapsed display age is not a new inference/commitment event.
                # Set value to a dictionary of k mapped to v for (k, v) in key/value pairs from value; retain
                # entries satisfying k differs from the text 'event_age_seconds'.
                value = {k:v for k,v in value.items() if k!='event_age_seconds'}
                # Run this branch when previous_value.
                if previous_value:
                    # Set previous_value to a dictionary of k mapped to v for (k, v) in key/value pairs from
                    # previous_value; retain entries satisfying k differs from the text 'event_age_seconds'.
                    previous_value = {k:v for k,v in previous_value.items() if k!='event_age_seconds'}
            # Run this branch when value and previous_value differs from value.
            if value and previous_value != value:
                # Call self._trace with the supplied arguments.
                self._trace(vehicle_id, now, stage, value)
        # Set predictions to 'local_intention_predictions' from current; use None if absent.
        predictions = current.get("local_intention_predictions")
        # Run this branch when predictions and previous is the same object as None or
        # 'local_intention_predictions' from previous; use None if absent differs from predictions.
        if predictions and (previous is None or
                            # Evaluate 'local_intention_predictions' from previous; use None if absent differs
                            # from predictions as part of the enclosing expression.
                            previous.get("local_intention_predictions") != predictions):
            # Call self._trace with the supplied arguments.
            self._trace(vehicle_id, now, "INTENTION", predictions)

    # Presentation vehicle history using the inputs and processing steps below.
    # Output: a dictionary containing final_snapshots, process_traces.
    def presentation_vehicle_history(self):
        # Set final to a dictionary built from self._completed_vehicle_by_id.
        final = dict(self._completed_vehicle_by_id)
        # Update final with the supplied entries.
        final.update(self._last_vehicle_by_id)
        # Return a dictionary containing final_snapshots, process_traces to the caller.
        return {"final_snapshots": tuple(final[key] for key in sorted(final)),
                # Store a dictionary of key mapped to a tuple built from value for (key, value) in the sorted
                # values from key/value pairs from self._vehicle_traces under 'process_traces'.
                "process_traces": {key: tuple(value)
                                   # Evaluate the sorted values from key/value pairs from self._vehicle_traces as
                                   # part of the enclosing expression.
                                   for key, value in sorted(self._vehicle_traces.items())}}
