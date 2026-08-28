"""One-process qualitative panel runtime composed from existing science layers."""

from dataclasses import dataclass
import hashlib
from pathlib import Path

import traci

from config import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP
from conflict import (ConflictGraphManager, ConflictZoneOccupancyAssessor,
                      ConflictZoneManager, MapPathManager)
from conflict_entry_monitor import ConflictEntryMonitor
from environment import SUMOEnv
from negotiation_execution import (ConflictZoneExecutionPlanner,
                                   CoordinationToPhysicalExecutionMapper)
from negotiation_execution.replay import PhysicalBranchReplayRunner
from negotiation_learning import (GraphTensorEncoder, NegotiationEnvironment,
                                  V2VPrecedenceClaimBus)
from negotiation_objective import raw_team_reward
from negotiation_scenarios.runner import derive_existing_route_id
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle)
from observation import ObservationManager
from predictor import IntentionPredictor
from traffic_rules import TrafficRuleEngine

from .reporting import write_panel_outputs
from .schedule import build_default_schedule, validate_schedule
from .visualization import PanelDemoVisualizer


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


def _print_event(number, now, participants, status, original, outcome, plan,
                 completed, scheduled):
    print("-" * 60)
    print(f"TIME: {now:.2f} s   EVENT #{number}")
    print("Active participants: " + repr(participants))
    print("Status: " + status)
    print("Original precedence: " + repr(original))
    if outcome is None:
        print("MAPPO_INVOCATION = NOT_REQUIRED" if status ==
              "REGULATORY_ORDER_RESOLVED" else "MAPPO_INVOCATION = BLOCKED")
    else:
        print("PROPOSER: " + repr(
            outcome.proposer_assignment.claim_action_assignments))
        print("RESPONDER: " + repr(
            outcome.responder_assignment.response_action_assignments))
        print("Effective graph: " + repr(outcome.effective_precedence_graph))
    print("READY: " + repr(plan.ready_vehicle_ids))
    print("BLOCKED: " + repr(plan.blocked_vehicle_ids))
    print(f"Completed: {completed}/{scheduled}")
    print("-" * 60)


def run_panel_demo(*, duration_seconds=120.0, use_gui=False, gui_delay_ms=0,
                   output_dir="results/panel_demo", schedule=None,
                   environment_factory=SUMOEnv):
    if duration_seconds <= 0:
        raise ValueError("PANEL_DURATION_MUST_BE_POSITIVE")
    schedule = validate_schedule(schedule or build_default_schedule())
    policy_hash_before = _sha256(POLICY_PATH)
    _, bundle = _load_bundle(POLICY_PATH)
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    helper = CoupledNegotiationTrainingEnvironment(provider, use_gui=use_gui)
    paths, zones = helper.paths, helper.zones
    planner = ConflictZoneExecutionPlanner(paths, zones)
    mapper = CoordinationToPhysicalExecutionMapper(zones)
    observations = ObservationManager()
    predictor, entry_monitor = IntentionPredictor(), ConflictEntryMonitor()
    graph_manager = ConflictGraphManager(paths, zones)
    occupancy = ConflictZoneOccupancyAssessor(paths, zones)
    rules, negotiation = TrafficRuleEngine(paths), NegotiationEnvironment()
    claim_bus, encoder = V2VPrecedenceClaimBus(), GraphTensorEncoder()
    visualizer = PanelDemoVisualizer(traci, use_gui, gui_delay_ms)
    environment = environment_factory(use_gui=use_gui)
    queues = {key: list(value) for key, value in schedule.items()}
    slots = {key: None for key in schedule}
    movements, vehicle_approaches = {}, {}
    completed_ids, spawned_ids = [], []
    authority = None
    cleared, entry_events, clear_events = set(), [], []
    last_attempt_identity = None
    starts = closes = 0
    metrics = {"presentation_vehicles_scheduled": 12,
               "presentation_vehicles_completed": 0,
               "unfinished_vehicles": 12, "negotiation_events": 0,
               "mappo_decision_epochs": 0, "rule_resolved_events": 0,
               "renegotiation_events": 0, "safe_hold_activations": 0,
               "collisions": 0, "blocked_zone_violations": 0,
               "maximum_negotiation_participants": 0}
    diagnostics = []
    _print_banner()
    try:
        environment.start(); starts += 1
        visualizer.configure_camera(paths)
        max_steps = int(round(float(duration_seconds) / SIM_TIME_STEP))
        while environment.step_count < max_steps:
            for approach in sorted(slots):
                if slots[approach] is None and queues[approach]:
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
                    spawned_ids.append(vehicle_id)
                    print(f"VEHICLE_ADMITTED {vehicle_id} "
                          f"{demand.movement_path_id}")
            states = environment.step(); now = environment.current_time
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

            snapshots = PhysicalBranchReplayRunner._pipeline_step(
                states, now, observations, entry_monitor, predictor,
                graph_manager, occupancy, rules, negotiation, claim_bus,
                encoder)
            edges = _edge_union(snapshots)
            original = tuple(sorted((x["yielding_vehicle_id"],
                                     x["priority_vehicle_id"]) for x in edges))
            identity = helper._decision_state_identity(states, edges, cleared)
            participants = identity[0]
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
                reasons = helper._plan_invalidation_reasons(
                    authority.state_identity, identity)
                occupied = any(x["state"] == "CURRENTLY_OCCUPYING"
                               for x in zone_observations.values())
                old_nonexec = (authority.initial_plan.graph_status !=
                               "EXECUTABLE" or
                               not authority.initial_plan.ready_vehicle_ids)
                prior_ready_relevant = bool(
                    set(authority.initial_plan.ready_vehicle_ids) &
                    set(participants))
                safe_transition = (not occupied and
                    (old_nonexec or ("CONFLICT_ZONE_CLEARED" in reasons and
                                     not prior_ready_relevant)))
                if reasons and safe_transition:
                    diagnostics.append({"event": "PLAN_INVALIDATED",
                                        "timestamp": now,
                                        "reasons": reasons})
                    print("PLAN_INVALIDATED " + ",".join(reasons))
                    print("RENEGOTIATION_REQUIRED")
                    metrics["renegotiation_events"] += 1
                    authority = None; zone_observations = None

            if original and authority is None and identity != last_attempt_identity:
                last_attempt_identity = identity
                source_id = (("PANEL_DEMO",), now,
                             "CONTINUOUS_JOINT_NEGOTIATION_CONTEXT")
                outcome = None
                if status in NEGOTIABLE:
                    encoded = tuple(observations.get_ldm(x["ego_id"]).
                                    current_encoded_graph_observation
                                    for x in snapshots)
                    outcome = provider.select_joint_actions(
                        scenario_id=("PANEL_DEMO_PRESENTATION_ONLY",),
                        episode_id=("PANEL_DEMO_ONE_PROCESS",),
                        batch_id=(("PANEL_DEMO_ONE_PROCESS",), now),
                        source_snapshot_id=source_id, original_edges=edges,
                        active_vehicle_ids=participants, timestamp=now,
                        regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
                        negotiation_status=status, encoded_graphs=encoded)
                    if outcome is not None:
                        metrics["mappo_decision_epochs"] += 1
                elif status == "REGULATORY_ORDER_RESOLVED":
                    metrics["rule_resolved_events"] += 1
                    print("TRAFFIC_RULE_ORDER_ALREADY_RESOLVED")
                effective = (outcome.effective_precedence_graph
                             if outcome is not None else original)
                obligations = mapper.map(effective, tuple(states), movements)
                plan = planner.plan(
                    source_snapshot_id=source_id,
                    effective_coordination_graph=effective,
                    active_vehicle_ids=tuple(states),
                    movement_path_by_vehicle=movements, timestamp=now,
                    source_protocol_state=(outcome.policy_status if outcome
                                           else status),
                    cleared_vehicle_zones=tuple(sorted(cleared)),
                    physical_obligation_set=obligations)
                zone_states = PhysicalBranchReplayRunner._zone_definitions(
                    helper, states, movements,
                    obligations.physical_execution_graph)
                authority = _Authority(identity, source_id, original, effective,
                                       status, outcome, obligations, plan,
                                       zone_states)
                metrics["negotiation_events"] += 1
                if plan.graph_status != "EXECUTABLE" or not plan.ready_vehicle_ids:
                    metrics["safe_hold_activations"] += 1
                    print("SAFE_HOLD_ACTIVE " + plan.graph_status)
                _print_event(metrics["negotiation_events"], now, participants,
                             status, original, outcome, plan,
                             len(completed_ids), 12)

            if authority is not None:
                if zone_observations is None:
                    zone_observations = PhysicalBranchReplayRunner._observe_zones(
                        helper, states, movements, authority.zone_states, now,
                        entry_events, clear_events, cleared)
                plan = planner.plan(
                    source_snapshot_id=authority.source_snapshot_id,
                    effective_coordination_graph=authority.effective_graph,
                    active_vehicle_ids=tuple(states),
                    movement_path_by_vehicle=movements, timestamp=now,
                    source_protocol_state=(authority.outcome.policy_status
                                           if authority.outcome else
                                           authority.status),
                    cleared_vehicle_zones=tuple(sorted(cleared)),
                    physical_obligation_set=authority.obligations)
            else:
                plan = planner.plan(
                    source_snapshot_id=(("PANEL_DEMO",), now, "NO_CONFLICT"),
                    effective_coordination_graph=(),
                    active_vehicle_ids=tuple(states),
                    movement_path_by_vehicle=movements, timestamp=now,
                    source_protocol_state="NO_ACTIVE_CONFLICT")
                zone_observations = {}
            PhysicalBranchReplayRunner._apply_control(
                plan, states, zone_observations, now, [], {}, {}, SIM_TIME_STEP)
            visualizer.update(states, participants if authority else (),
                              plan.ready_vehicle_ids, plan.blocked_vehicle_ids)
        metrics["presentation_vehicles_completed"] = len(completed_ids)
        metrics["unfinished_vehicles"] = 12 - len(completed_ids)
    finally:
        environment.close(); closes += 1

    policy_hash_after = _sha256(POLICY_PATH)
    result = {"evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
        "quantitative_model_selection_evidence": False,
        "validation_evidence": False, "held_out_evidence": False,
        "selected_candidate_id": "E5",
        "selected_policy_path": str(POLICY_PATH).replace("\\", "/"),
        "policy_sha256_before": policy_hash_before,
        "policy_sha256_after": policy_hash_after,
        "policy_hash_unchanged": policy_hash_before == policy_hash_after,
        "selected_policy_modified": policy_hash_before != policy_hash_after,
        "centralized_critic_used_for_action": False,
        "centralized_critic_calls": provider.runtime_critic_calls,
        "training_operations": 0, "backward_calls": 0,
        "optimizer_steps": 0, "parameter_updates": 0,
        "route_truth_actor_leakage": 0, "held_out_scenarios_consumed": 0,
        "sumo_start_count": starts, "sumo_close_count": closes,
        "simulation_step_seconds": SIM_TIME_STEP,
        "presentation_duration_seconds": float(duration_seconds),
        "presentation_schedule": {key: [x.movement_path_id for x in value]
                                  for key, value in schedule.items()},
        "schedule_source": "PREDECLARED_PRESENTATION_ROLLING_APPROACH_SLOTS",
        "training_demo_case_search": False,
        "validation_or_held_out_search": False,
        "spawned_vehicle_ids": spawned_ids,
        "completed_vehicle_ids": completed_ids,
        "metrics": metrics, "diagnostics": diagnostics}
    if not result["policy_hash_unchanged"]:
        raise RuntimeError("SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO")
    write_panel_outputs(result, output_dir)
    return result
