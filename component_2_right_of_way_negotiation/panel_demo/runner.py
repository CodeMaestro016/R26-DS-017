"""One-process qualitative panel runtime composed from existing science layers."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from itertools import combinations
from types import SimpleNamespace
from time import perf_counter_ns

import traci

from config import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP
from conflict import (ConflictGraphManager, ConflictZoneOccupancyAssessor,
                      ConflictZoneManager, MapPathManager)
from conflict_entry_monitor import ConflictEntryMonitor
from environment import SUMOEnv
from negotiation_execution import (EgoExecutionContext, EgoCoordinationCommitment,
    ExecutionStateMessage, DecentralizedEgoExecutionController,
    ConflictZoneExecutionPlan)
from negotiation_execution.replay import PhysicalBranchReplayRunner
from negotiation_learning import (GraphTensorEncoder, NegotiationEnvironment,
                                  V2VPrecedenceClaimBus)
from negotiation_scenarios.runner import derive_existing_route_id
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_training.final_selection import _load_bundle
from observation import ObservationManager
from predictor import IntentionPredictor
from traffic_rules import TrafficRuleEngine

from .reporting import write_panel_outputs
from .schedule import (ADMISSION_ORDER, ADMISSION_WAVES,
                       INITIAL_ADMISSION_SECONDS,
                       build_default_schedule, validate_schedule,
                       validate_presentation_schedule)
from .visualization import PanelDemoVisualizer
from .inference import (PanelDeterministicInferenceProvider,
                        PRESENTATION_SELECTION_RULE)
from .browser_state import BrowserStatePublisher
from .queue_heads import select_queue_heads, approach_queue_depth


POLICY_PATH = Path("results/final_mappo_selection_v2/selected_policy.pt")
NEGOTIABLE = {"NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
              "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"}
BLOCKED = {"NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED",
           "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
           "SOURCE_SNAPSHOT_MISMATCH", "REGULATORY_PROFILE_MISMATCH"}


@dataclass
class _Authority:
    state_identity: tuple
    source_snapshot_id: tuple
    original_graph: tuple
    effective_graph: tuple
    status: str
    outcome: object
    obligations: object
    initial_plan: object
    zone_states: dict
    member_ids: tuple
    commitment_inboxes: dict


def _display_plan(decisions, now, source_id=()):
    """Aggregate returned ego decisions for audit/UI ONLY, never for control."""
    ready = tuple(d.ego_id for d in decisions if d.permission == "PERMITTED")
    blocked = tuple(d.ego_id for d in decisions if d.blocked_zones)
    return ConflictZoneExecutionPlan(("EGO_DECISION_AUDIT", now), source_id,
        (), tuple(d.ego_id for d in decisions), (), (), ready, blocked,
        "EXECUTABLE" if ready else "LOCAL_SAFE_HOLD",
        {"permission_source": "RETURNED_EGO_DECISIONS_DISPLAY_ONLY"})


def _deliver_pair_commitments(effective, member_ids, agreement_id):
    """Transport protocol pair agreements; do not compute permissions here."""
    inboxes = {ego: [] for ego in member_ids}
    for yielding, priority in effective:
        message = EgoCoordinationCommitment(yielding, priority, agreement_id)
        for receiver in (yielding, priority):
            inboxes[receiver].append(message)
    return {ego: tuple(rows) for ego, rows in inboxes.items()}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _edge_union(snapshots):
    values = {}
    for snapshot in snapshots:
        for edge in snapshot["joint_precedence_edges"]:
            key = (edge["yielding_vehicle_id"], edge["priority_vehicle_id"])
            values[key] = edge
    return tuple(values[key] for key in sorted(values))


def _dynamic_status(snapshots, original_graph):
    """Conservatively consolidate actual ego-local snapshot classifications."""
    statuses = {item["negotiation_status"] for item in snapshots}
    for status in ("SOURCE_SNAPSHOT_MISMATCH",
                   "REGULATORY_PROFILE_MISMATCH",
                   "COMMUNICATED_PRECEDENCE_DISAGREEMENT",
                   "NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED"):
        if status in statuses:
            return status
    if "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" in statuses:
        return "NEGOTIATION_REQUIRED_REGULATORY_CYCLE"
    if "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE" in statuses:
        return "NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE"
    if original_graph:
        return "REGULATORY_ORDER_RESOLVED"
    return "NO_ACTIVE_CONFLICT"


def _reconsider_authority_if_safe(helper, authority, identity,
                                  zone_observations):
    """Release stale authority at a safe, event-driven progress boundary."""
    if authority is None:
        return None, ()
    reasons = helper._plan_invalidation_reasons(
        authority.state_identity, identity)
    occupied = any(observation["state"] == "CURRENTLY_OCCUPYING"
                   for observation in zone_observations.values())
    old_participants = set(authority.state_identity[0])
    new_participants = set(identity[0])
    participant_departed = bool(old_participants - new_participants)
    old_nonexec = (authority.initial_plan.graph_status != "EXECUTABLE" or
                   not authority.initial_plan.ready_vehicle_ids)
    prior_ready_relevant = bool(
        set(authority.initial_plan.ready_vehicle_ids) & new_participants)
    cleared_without_prior_ready = (
        "CONFLICT_ZONE_CLEARED" in reasons and not prior_ready_relevant)
    safe_progress_boundary = (old_nonexec or participant_departed or
                              cleared_without_prior_ready)
    if not reasons or occupied or not safe_progress_boundary:
        return authority, ()
    return None, reasons


def _print_banner():
    print("=" * 60)
    print("FINAL LIVE PANEL DEMONSTRATION")
    print("Multi-Agent Right-of-Way Negotiation")
    print("=" * 60)
    print("Mode: QUALITATIVE_PRESENTATION_ONLY")
    print("Selected policy: E5")
    print("Policy source: selected_policy.pt")
    print("Decentralized actors: ENABLED")
    print("Centralized critic: DISABLED")
    print("Training: DISABLED")
    print("Held-out evaluation: NOT USED")
    print("GUI: BLUE approaching; YELLOW negotiating; GREEN ready; RED blocked")
    print("=" * 60)


def _presentation_timeline(event_records, diagnostics):
    events = [{"timestamp": item["timestamp"],
               "event": item["status"],
               "mappo_invocation": item["mappo_invocation"],
               "participants": item.get("participants", ()),
               "original_graph": item.get("original_regulatory_graph", ()),
               "proposer_actions": item.get("proposer_actions", ()),
               "responder_actions": item.get("responder_actions", ()),
               "effective_graph": item.get("effective_coordination_graph", ()),
               "ready": item.get("ready_vehicle_ids", ()),
               "blocked": item.get("blocked_vehicle_ids", ()),
               "policy_factors": item.get("policy_factor_diagnostics", ())}
              for item in event_records]
    events.extend({"timestamp": item["timestamp"],
                   "event": item["event"],
                   "reasons": item.get("reasons", ())}
                  for item in diagnostics
                  if item["event"] in {"PLAN_INVALIDATED",
                                       "MAPPO_INVOCATION_BLOCKED"})
    return tuple(sorted(events, key=lambda item: item["timestamp"])[-12:])


def _print_event(number, now, participants, status, original, outcome, plan,
                 completed, scheduled, factor_diagnostics=()):
    print("-" * 60)
    print(f"TIME: {now:.2f} s   EVENT #{number}")
    print("Active participants: " + repr(participants))
    print("Status: " + status)
    print("Original precedence: " + repr(original))
    if outcome is None:
        print("MAPPO_INVOCATION = NOT_REQUIRED" if status ==
              "REGULATORY_ORDER_RESOLVED" else "MAPPO_INVOCATION = BLOCKED")
    else:
        print("MAPPO_INVOCATION = AUTHORIZED")
        print("PROPOSER: " + repr(
            outcome.proposer_assignment.claim_action_assignments))
        print("RESPONDER: " + repr(
            outcome.responder_assignment.response_action_assignments))
        print("Effective graph: " + repr(outcome.effective_precedence_graph))
        print("SEMANTIC_SELECTION_RULE = " + PRESENTATION_SELECTION_RULE)
        for factor in factor_diagnostics:
            print("POLICY_FACTOR " + repr(factor))
    print("READY: " + repr(plan.ready_vehicle_ids))
    print("BLOCKED: " + repr(plan.blocked_vehicle_ids))
    print(f"Completed: {completed}/{scheduled}")
    print("-" * 60)


def run_panel_demo(*, duration_seconds=220.0, use_gui=False, gui_delay_ms=0,
                   output_dir="results/panel_demo", schedule=None,
                   environment_factory=SUMOEnv, web_live=False,
                   presentation_delay_ms=0,
                   browser_state_path="results/panel_demo/runtime/live_state.json",
                   scenario_id="default_panel", admission_waves=None,
                   admission_mode="ROLLING_WAVES",
                   stop_request_path=None, presentation_run_id=None,
                   runtime_observer=None, provider_factory=None,
                   persist_presentation=True, return_failed_result=False):
    """Shared control loop; optional evaluation hooks observe, never grant entry.

    Default arguments retain the qualitative presentation contract. A separate
    quantitative wrapper supplies a predeclared semantic provider and telemetry.
    """
    if duration_seconds <= 0:
        raise ValueError("PANEL_DURATION_MUST_BE_POSITIVE")
    if admission_mode not in {"ROLLING_WAVES", "INDEPENDENT_DEMAND"}:
        raise ValueError("UNKNOWN_PANEL_ADMISSION_MODE")
    if schedule is None:
        schedule = validate_schedule(build_default_schedule())
    else:
        schedule = validate_presentation_schedule(schedule,
            allow_repeated_movements=admission_mode == "INDEPENDENT_DEMAND")
    admission_waves = tuple(admission_waves or ADMISSION_WAVES)
    scheduled_count = sum(len(rows) for rows in schedule.values())
    policy_hash_before = _sha256(POLICY_PATH)
    _, bundle = _load_bundle(POLICY_PATH)
    for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
        module.eval()
    provider = PanelDeterministicInferenceProvider(bundle, sampling_seed=0)
    if provider_factory is not None:
        provider = provider_factory(bundle)
    paths = MapPathManager()
    zones = ConflictZoneManager(paths)
    # Reuse geometry/audit utilities without constructing a training runtime
    # or a centralized execution planner.
    helper = SimpleNamespace(paths=paths, zones=zones,
        _decision_state_identity=CoupledNegotiationTrainingEnvironment._decision_state_identity,
        _plan_invalidation_reasons=CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    ego_controllers = {}
    observations = ObservationManager()
    predictor, entry_monitor = IntentionPredictor(), ConflictEntryMonitor()
    graph_manager = ConflictGraphManager(paths, zones)
    occupancy = ConflictZoneOccupancyAssessor(paths, zones)
    rules, negotiation = TrafficRuleEngine(paths), NegotiationEnvironment()
    claim_bus, encoder = V2VPrecedenceClaimBus(), GraphTensorEncoder()
    visualizer = PanelDemoVisualizer(traci, use_gui, gui_delay_ms)
    browser = (BrowserStatePublisher(
        browser_state_path, traci,
        presentation_delay_ms=presentation_delay_ms) if web_live else None)
    map_state = browser.map_snapshot(paths) if browser else None
    environment = environment_factory(use_gui=use_gui)
    queues = {key: list(value) for key, value in schedule.items()}
    slots = {key: None for key in schedule}
    movements, vehicle_approaches = {}, {}
    completed_ids, spawned_ids = [], []
    submitted_ids, departures, demand_times = [], {}, {}
    constrained_ids, prior_hold_ids = set(), set()
    authority = None
    cleared, entry_events, clear_events = set(), [], []
    last_attempt_identity = None
    last_blocked_invocation = None
    next_admission_wave = 0
    starts = closes = 0
    metrics = {"presentation_vehicles_scheduled": scheduled_count,
               "presentation_vehicles_completed": 0,
               "unfinished_vehicles": scheduled_count, "negotiation_events": 0,
               "mappo_decision_epochs": 0, "rule_resolved_events": 0,
               "renegotiation_events": 0, "safe_hold_activations": 0,
               "collisions": 0, "blocked_zone_violations": 0,
               "maximum_negotiation_participants": 0}
    metrics.update({"total_vehicles_scheduled": scheduled_count,
        "total_vehicles_spawned": 0, "total_vehicles_completed": 0,
        "current_active_vehicle_count": 0, "maximum_simultaneous_active_vehicles": 0,
        "current_moving_vehicle_count": 0, "maximum_simultaneously_moving_vehicles": 0,
        "per_approach_queue_depth": dict.fromkeys("NESW", 0),
        "maximum_per_approach_queue_depth": dict.fromkeys("NESW", 0),
        "current_negotiation_participants": (), "negotiation_event_count": 0,
        "centralized_critic_runtime_calls": 0, "decentralized_execution": True,
        "centralized_critic_used_for_action": provider.runtime_critic_enabled,
        "centralized_execution_graph_used_for_control": False,
        "selected_policy_hash_unchanged": True})
    metrics["maximum_approaches_with_multiple_queued_vehicles"] = 0
    metrics["native_emergency_stop_events"] = 0
    diagnostics, event_records = [], []
    latest_policy_factors = ()
    stopped_by_user = False
    failure = None
    started_at = datetime.now(timezone.utc).isoformat()
    stop_request = Path(stop_request_path) if stop_request_path else None
    _print_banner()
    try:
        environment.start(); starts += 1
        visualizer.configure_camera(paths, show_queues=admission_mode == "INDEPENDENT_DEMAND")
        max_steps = int(round(float(duration_seconds) / SIM_TIME_STEP))
        while environment.step_count < max_steps:
            if stop_request is not None and stop_request.is_file():
                stopped_by_user = True
                diagnostics.append({"event": "PRESENTATION_STOP_REQUESTED",
                                    "timestamp": environment.current_time})
                print(f"USER_STOPPED_AT {environment.current_time:.2f} s")
                break
            wave_ready = all(vehicle_id is None
                             for vehicle_id in slots.values())
            wave_approaches = (set(admission_waves[next_admission_wave])
                               if wave_ready and next_admission_wave <
                               len(admission_waves) else set())
            admitted_this_step = False
            for approach in ADMISSION_ORDER:
                initial_pending = (bool(queues[approach]) and
                                   queues[approach][0].sequence_index == 0)
                release_time = (INITIAL_ADMISSION_SECONDS[approach]
                                if initial_pending else 0.0)
                independent_due = (admission_mode == "INDEPENDENT_DEMAND" and
                    bool(queues[approach]) and environment.current_time >=
                    queues[approach][0].scheduled_departure_seconds)
                rolling_due = (admission_mode == "ROLLING_WAVES" and
                    approach in wave_approaches and slots[approach] is None)
                if ((independent_due or rolling_due) and
                        queues[approach] and
                        environment.current_time >= release_time):
                    demand = queues[approach].pop(0)
                    vehicle_id = f"PANEL_AV_{approach}_{demand.sequence_index + 1:02d}"
                    route = derive_existing_route_id(paths,
                                                     demand.movement_path_id)
                    traci.vehicle.add(vehicle_id, route, AV_TYPE_ID,
                                      departSpeed="max", departLane="free",
                                      departPos="base")
                    traci.vehicle.setSpeedMode(vehicle_id,
                                               SAFE_SUMO_SPEED_MODE)
                    observations.get_or_create_ldm(vehicle_id)
                    slots[approach] = vehicle_id
                    movements[vehicle_id] = demand.movement_path_id
                    vehicle_approaches[vehicle_id] = approach
                    submitted_ids.append(vehicle_id)
                    demand_times[vehicle_id] = (demand.scheduled_departure_seconds
                        if admission_mode == "INDEPENDENT_DEMAND" else environment.current_time)
                    admitted_this_step = True
                    print(f"VEHICLE_ADMITTED {vehicle_id} "
                          f"{demand.movement_path_id}")
            if admitted_this_step:
                next_admission_wave += 1
            states = environment.step(); now = environment.current_time
            if runtime_observer is not None:
                runtime_observer.observe(now, states, environment.lifecycle_events,
                                         movements, paths, zones, traci)
            for vehicle_id in environment.lifecycle_events.departed_vehicle_ids:
                if vehicle_id in vehicle_approaches:
                    spawned_ids.append(vehicle_id)
                    departures[vehicle_id] = now
            for vehicle_id in environment.lifecycle_events.arrived_vehicle_ids:
                if vehicle_id in vehicle_approaches:
                    approach = vehicle_approaches[vehicle_id]
                    if slots[approach] == vehicle_id:
                        slots[approach] = None
                    completed_ids.append(vehicle_id)
                    print(f"VEHICLE_COMPLETED {vehicle_id}")
            collisions = tuple(sorted(
                traci.simulation.getCollidingVehiclesIDList()))
            if collisions:
                metrics["collisions"] += len(collisions)
                raise RuntimeError("PANEL_DEMO_COLLISION_OBSERVED")

            frontline_ids = select_queue_heads(states, paths, movements)
            queue_heads = tuple(ego for ego in frontline_ids
                if observations.is_in_approach_zone(states[ego]["position"]))
            depths = approach_queue_depth(states, paths, movements)
            metrics["maximum_approaches_with_multiple_queued_vehicles"] = max(
                metrics["maximum_approaches_with_multiple_queued_vehicles"],
                sum(depth > 1 for depth in depths.values()))
            metrics["native_emergency_stop_events"] += len(
                traci.simulation.getEmergencyStoppingVehiclesIDList())
            metrics["current_active_vehicle_count"] = len(states)
            metrics["current_moving_vehicle_count"] = sum(s["speed"] > 0 for s in states.values())
            for current, maximum in (("current_active_vehicle_count", "maximum_simultaneous_active_vehicles"),
                                     ("current_moving_vehicle_count", "maximum_simultaneously_moving_vehicles")):
                metrics[maximum] = max(metrics[maximum], metrics[current])
            metrics["per_approach_queue_depth"] = depths
            for approach in depths:
                metrics["maximum_per_approach_queue_depth"][approach] = max(
                    metrics["maximum_per_approach_queue_depth"][approach], depths[approach])
            metrics["total_vehicles_spawned"] = len(spawned_ids)
            metrics["total_vehicles_completed"] = len(completed_ids)
            metrics["current_negotiation_participants"] = queue_heads

            snapshots = PhysicalBranchReplayRunner._pipeline_step(
                states, now, observations, entry_monitor, predictor,
                graph_manager, occupancy, rules, negotiation, claim_bus,
                encoder, negotiation_eligible_ids=queue_heads)
            edges = _edge_union(snapshots)
            original = tuple(sorted((x["yielding_vehicle_id"],
                                     x["priority_vehicle_id"]) for x in edges))
            edge_identity = helper._decision_state_identity(states, edges, cleared)
            identity = (queue_heads, edge_identity[1], edge_identity[2])
            participants = queue_heads
            participant_approaches = [vehicle_approaches[x]
                                      for x in participants]
            if len(participants) > 4 or len(set(participant_approaches)) != len(
                    participant_approaches):
                raise RuntimeError("PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED")
            metrics["maximum_negotiation_participants"] = max(
                metrics["maximum_negotiation_participants"], len(participants))
            status = _dynamic_status(snapshots, original)

            zone_observations = None
            if authority is not None:
                zone_observations = PhysicalBranchReplayRunner._observe_zones(
                    helper, states, movements, authority.zone_states, now,
                    entry_events, clear_events, cleared)
                authority, reasons = _reconsider_authority_if_safe(
                    helper, authority, identity, zone_observations)
                if reasons:
                    diagnostics.append({"event": "PLAN_INVALIDATED",
                                        "timestamp": now,
                                        "reasons": reasons})
                    print("PLAN_INVALIDATED " + ",".join(reasons))
                    print("RENEGOTIATION_REQUIRED")
                    metrics["renegotiation_events"] += 1
                    zone_observations = None

            if original and authority is None and identity != last_attempt_identity:
                source_id = (("PANEL_DEMO",), now,
                             "CONTINUOUS_JOINT_NEGOTIATION_CONTEXT")
                outcome = None
                batch_id = (("PANEL_DEMO_ONE_PROCESS",), now)
                invocation_block_reason = None
                if status in NEGOTIABLE:
                    encoded = tuple(observations.get_ldm(x["ego_id"]).
                                    current_encoded_graph_observation
                                    for x in snapshots)
                    if any(len(item.node_ids) > 4 for item in encoded):
                        raise RuntimeError("PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED")
                    factors = provider._eligible_factors(
                        participants, edges, status)
                    encoded_egos = {item.ego_id for item in encoded}
                    required_egos = ({claim.ego_id for claim, _ in factors} |
                                     {claim.counterparty_id
                                      for claim, _ in factors})
                    missing_egos = tuple(sorted(required_egos - encoded_egos))
                    if not factors:
                        invocation_block_reason = "NO_ELIGIBLE_PROPOSER_FACTORS"
                    elif missing_egos:
                        invocation_block_reason = "RESPONDER_CONTEXT_INCOMPLETE"
                    else:
                        inference_started = perf_counter_ns()
                        outcome = provider.select_joint_actions(
                            scenario_id=("PANEL_DEMO_PRESENTATION_ONLY",),
                            episode_id=("PANEL_DEMO_ONE_PROCESS",),
                            batch_id=batch_id,
                            source_snapshot_id=source_id,
                            original_edges=edges,
                            active_vehicle_ids=participants, timestamp=now,
                            regulatory_profile=
                                "DE_STVO_UNCONTROLLED_4WAY_V1",
                            negotiation_status=status,
                            encoded_graphs=encoded)
                        if runtime_observer is not None:
                            runtime_observer.inference(perf_counter_ns() - inference_started)
                        if outcome is not None:
                            if getattr(provider, "uses_mappo_behavior_policy", True):
                                metrics["mappo_decision_epochs"] += 1
                    if invocation_block_reason:
                        signature = (identity, invocation_block_reason,
                                     missing_egos)
                        if signature != last_blocked_invocation:
                            print("MAPPO_INVOCATION = BLOCKED")
                            print("Reason: " + invocation_block_reason)
                            if missing_egos:
                                print("Missing encoded egos: " +
                                      repr(missing_egos))
                            diagnostics.append({
                                "event": "MAPPO_INVOCATION_BLOCKED",
                                "timestamp": now,
                                "reason": invocation_block_reason,
                                "missing_encoded_egos": missing_egos})
                            last_blocked_invocation = signature
                elif status == "REGULATORY_ORDER_RESOLVED":
                    metrics["rule_resolved_events"] += 1
                    print("TRAFFIC_RULE_ORDER_ALREADY_RESOLVED")
                if invocation_block_reason:
                    # Do not freeze an incomplete authority or mark the live
                    # state attempted; retry when every required local actor
                    # context exists.
                    outcome = None
                    # Ego controllers below safe-hold until coordination arrives.
                else:
                    last_attempt_identity = identity
                if not invocation_block_reason:
                    last_blocked_invocation = None
                    effective = (outcome.effective_precedence_graph
                                 if outcome is not None else original)
                    inboxes = _deliver_pair_commitments(effective, participants, source_id)
                    zone_states = PhysicalBranchReplayRunner._zone_definitions(
                        helper, states, movements,
                        tuple(edge for edge in combinations(participants, 2) if zones.zone_record(
                            movements[edge[0]], states[edge[0]]["width"],
                            movements[edge[1]], states[edge[1]]["width"]) is not None))
                    # Only ego controllers determine permissions; this placeholder
                    # is event bookkeeping, never a control plan.
                    plan = _display_plan((), now, source_id)
                    authority = _Authority(identity, source_id, original, effective,
                        status, outcome, None, plan, zone_states, participants, inboxes)
                    metrics["negotiation_events"] += 1
                    factor_diagnostics = (provider.factor_diagnostics(batch_id)
                                          if outcome is not None else ())
                    latest_policy_factors = factor_diagnostics
                    event_records.append({
                        "event_number": metrics["negotiation_events"],
                        "timestamp": now, "status": status,
                        "participants": participants,
                        "mappo_invocation": ("AUTHORIZED" if outcome is not None
                                             else "NOT_REQUIRED" if status ==
                                             "REGULATORY_ORDER_RESOLVED" else
                                             "BLOCKED"),
                        "proposer_actions": (outcome.proposer_assignment.
                            claim_action_assignments if outcome else ()),
                        "responder_actions": (outcome.responder_assignment.
                            response_action_assignments if outcome else ()),
                        "original_regulatory_graph": original,
                        "effective_coordination_graph": effective,
                        "ready_vehicle_ids": plan.ready_vehicle_ids,
                        "blocked_vehicle_ids": plan.blocked_vehicle_ids})
                    event_records[-1]["policy_factor_diagnostics"] = (
                        factor_diagnostics)

            if authority is not None:
                if zone_observations is None:
                    zone_observations = PhysicalBranchReplayRunner._observe_zones(
                        helper, states, movements, authority.zone_states, now,
                        entry_events, clear_events, cleared)
            else:
                zone_observations = {}
            decisions, control_records = [], []
            # Same-step ideal V2V: each sender announces its own state/path.
            # Full perception remains in the LDM; only pair-relevant messages
            # and pair commitments cross the execution-controller boundary.
            controlled = set(queue_heads) | (set(authority.member_ids) & set(states)
                                             if authority else set())
            messages = {ego: ExecutionStateMessage(ego, movements[ego],
                states[ego], now) for ego in controlled}
            for ego, state in sorted(states.items()):
                own_snapshot = next((s for s in snapshots if s["ego_id"] == ego), None)
                complete = (authority is not None and ego in authority.member_ids
                            and authority.status not in BLOCKED and
                            not (getattr(provider, "rules_only", False) and
                                 authority.status in NEGOTIABLE))
                if authority is None and not original:
                    complete = (own_snapshot is not None and
                        own_snapshot["negotiation_status"] in
                        {"NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"})
                inbox = authority.commitment_inboxes.get(ego, ()) if authority else ()
                peer_ids = {c.priority_vehicle_id for c in inbox if c.yielding_vehicle_id == ego}
                peer_ids.update(peer for peer in controlled if peer != ego and
                    vehicle_approaches[peer] != vehicle_approaches[ego])
                context = EgoExecutionContext(ego, state, movements[ego], now,
                    inbox, tuple(messages[peer] for peer in sorted(peer_ids) if peer in messages),
                    complete, now if complete else None, ego in controlled)
                if ego not in ego_controllers:
                    ego_controllers[ego] = DecentralizedEgoExecutionController(paths, zones)
                ego_controller = ego_controllers[ego]
                try:
                    execution_started = perf_counter_ns()
                    decision = ego_controller.decide(context)
                    decision = ego_controller.constrain(context, decision,
                        traci.vehicle, SIM_TIME_STEP)
                    if runtime_observer is not None:
                        runtime_observer.execution(perf_counter_ns() - execution_started,
                                                   decision)
                except RuntimeError as error:
                    if str(error) == "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE":
                        metrics["blocked_zone_violations"] += 1
                    raise
                decisions.append(decision)
                control_records.extend(decision.speed_constraints)
                if decision.requested_speed_mps is not None:
                    traci.vehicle.setSpeed(ego, decision.requested_speed_mps)
                    constrained_ids.add(ego)
                elif ego in constrained_ids:
                    traci.vehicle.setSpeed(ego, -1.0)
                    constrained_ids.discard(ego)
            held = {d.ego_id for d in decisions if d.permission == "SAFE_HOLD"}
            metrics["safe_hold_activations"] += len(held - prior_hold_ids)
            prior_hold_ids = held
            plan = _display_plan(decisions, now,
                authority.source_snapshot_id if authority else ())
            if authority:
                authority.initial_plan = plan
            if event_records and event_records[-1]["timestamp"] == now:
                event_records[-1]["ready_vehicle_ids"] = plan.ready_vehicle_ids
                event_records[-1]["blocked_vehicle_ids"] = plan.blocked_vehicle_ids
                _print_event(metrics["negotiation_events"], now, participants,
                    status, original, authority.outcome if authority else None,
                    plan, len(completed_ids), scheduled_count, latest_policy_factors)
            metrics["negotiation_event_count"] = metrics["negotiation_events"]
            metrics["centralized_critic_runtime_calls"] = provider.runtime_critic_calls
            visualizer.update(states, participants if authority else (),
                              plan.ready_vehicle_ids, plan.blocked_vehicle_ids)
            if browser:
                browser.publish(
                    simulation_time=now, map_state=map_state, running=True,
                    status=(authority.status if authority else status),
                    participants=participants,
                    ready=plan.ready_vehicle_ids,
                    blocked=plan.blocked_vehicle_ids,
                    original_graph=(authority.original_graph
                                    if authority else original),
                    effective_graph=(authority.effective_graph
                                     if authority else original),
                    mappo_invocation=("AUTHORIZED" if authority and
                                      authority.outcome else "NOT_REQUIRED"),
                    completed=len(completed_ids), scheduled=scheduled_count,
                    scenario_id=scenario_id, scientific_states=states,
                    observations=observations, snapshots=snapshots, plan=plan,
                    control_records=control_records,
                    policy_factors=latest_policy_factors,
                    events=_presentation_timeline(event_records, diagnostics),
                    run_metrics=metrics)
                browser.pace()
            if len(completed_ids) == scheduled_count:
                break
        metrics["presentation_vehicles_completed"] = len(completed_ids)
        metrics["unfinished_vehicles"] = scheduled_count - len(completed_ids)
    except Exception as error:
        failure = error
        diagnostics.append({"event": "PRESENTATION_FAILED",
            "timestamp": environment.current_time, "error": str(error)})
    finally:
        metrics["presentation_vehicles_completed"] = len(completed_ids)
        metrics["unfinished_vehicles"] = scheduled_count - len(completed_ids)
        if browser:
            browser.publish(
                simulation_time=environment.current_time, map_state=map_state,
                running=False,
                status=("FAILED" if failure else "USER_STOPPED" if stopped_by_user
                        else "FINISHED" if len(completed_ids) == scheduled_count else "INCOMPLETE"),
                completed=len(completed_ids),
                scheduled=scheduled_count, scenario_id=scenario_id,
                run_metrics=metrics, force=True)
        environment.close(); closes += 1

    policy_hash_after = _sha256(POLICY_PATH)
    metrics["selected_policy_hash_unchanged"] = policy_hash_before == policy_hash_after
    result = {"evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
        "presentation_run_id": presentation_run_id,
        "run_status": ("FAILED" if failure else "USER_STOPPED" if stopped_by_user else "COMPLETED"
                       if len(completed_ids) == scheduled_count else "INCOMPLETE"),
        "started_at_utc": started_at,
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        "actual_simulation_time_seconds": float(environment.current_time),
        "quantitative_model_selection_evidence": False,
        "validation_evidence": False, "held_out_evidence": False,
        "selected_candidate_id": "E5",
        "presentation_scenario_id": scenario_id,
        "inference_mode": "DETERMINISTIC_MASKED_ARGMAX_PRESENTATION_ONLY",
        "selected_policy_weights": "E5",
        "quantitative_evidence": False,
        "presentation_semantic_selection_rule": PRESENTATION_SELECTION_RULE,
        "selected_policy_path": str(POLICY_PATH).replace("\\", "/"),
        "policy_sha256_before": policy_hash_before,
        "policy_sha256_after": policy_hash_after,
        "policy_hash_unchanged": policy_hash_before == policy_hash_after,
        "selected_policy_modified": policy_hash_before != policy_hash_after,
        "centralized_critic_used_for_action": False,
        "decentralized_execution": True,
        "centralized_execution_graph_used_for_control": False,
        "centralized_critic_calls": provider.runtime_critic_calls,
        "training_operations": 0, "backward_calls": 0,
        "optimizer_steps": 0, "parameter_updates": 0,
        "route_truth_actor_leakage": 0, "held_out_scenarios_consumed": 0,
        "sumo_start_count": starts, "sumo_close_count": closes,
        "simulation_step_seconds": SIM_TIME_STEP,
        "presentation_duration_seconds": float(duration_seconds),
        "presentation_schedule": {key: [x.movement_path_id for x in value]
                                  for key, value in schedule.items()},
        "schedule_source": "PREDECLARED_PRESENTATION_" + admission_mode,
        "actual_departure_seconds": departures,
        "scheduled_departure_seconds": demand_times,
        "insertion_delay_seconds": {ego: departures[ego] - demand_times[ego]
                                   for ego in departures},
        "pending_insertion_vehicle_ids": tuple(ego for ego in submitted_ids
                                              if ego not in departures),
        "mappo_demo_case_source":
            "EXISTING_TRAINING_SIDE_ILLUSTRATIVE_CASE",
        "mappo_demo_case_identifier": (
            "TRAINING_MANIFEST_ROUTE_STRUCTURE",
            ("E_IN_0_STRAIGHT", "N_IN_0_STRAIGHT",
             "S_IN_0_RIGHT", "W_IN_0_LEFT")),
        "training_demo_case_search": False,
        "validation_or_held_out_search": False,
        "spawned_vehicle_ids": spawned_ids,
        "completed_vehicle_ids": completed_ids,
        "metrics": metrics, "events": event_records,
        "diagnostics": diagnostics}
    if browser:
        result["presentation_vehicle_history"] = (
            browser.presentation_vehicle_history())
    if not result["policy_hash_unchanged"]:
        raise RuntimeError("SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO")
    result["runtime_error"] = str(failure) if failure else None
    if persist_presentation:
        write_panel_outputs(result, output_dir)
    if failure is not None and not return_failed_result:
        raise failure
    return result
