"""Local authority, queue promotion, and real SUMO presentation acceptance."""

from dataclasses import fields, replace
from hashlib import sha256
from types import SimpleNamespace
from pathlib import Path
import contextlib
import io
import shutil
from functools import wraps

import pytest
import torch

from negotiation_execution import (EgoExecutionContext, EgoCoordinationCommitment,
    ExecutionStateMessage, DecentralizedEgoExecutionController,
    ConflictZoneExecutionPlanner)
from runtime_simulation.queue_heads import select_queue_heads, approach_queue_depth
from runtime_simulation.scenarios import get_scenario
from runtime_simulation.schedule import validate_presentation_schedule
from runtime_simulation.runner import run_runtime_simulation, POLICY_PATH, _deliver_pair_commitments
from runtime_simulation import runner as panel_runner
from negotiation_learning import GraphTensorEncoder
from config import SAFE_SUMO_SPEED_MODE


def state(progress=-20.0, lane="n_in_0", lane_position=10.0):
    return {"progress": progress, "width": 1.8, "length": 5.0,
            "lane_id": lane, "lane_position": lane_position,
            "speed": 4.0, "comfortable_deceleration_mps2": 4.5}


@pytest.fixture
def controller():
    paths = SimpleNamespace(paths={p: SimpleNamespace(
        incoming_lane_id=p.lower() + "_in_0", outgoing_lane_id=p.lower() + "_out_0",
        internal_lane_ids=(":" + p,), path_id=p) for p in "NESW"},
        resolve_front_bumper_path_progress=lambda s, p: (s["progress"], None, None))
    zones = SimpleNamespace(zone_record=lambda *args: {
        "zone_id": "CZ", "first_path_distance_interval": (0.0, 10.0),
        "second_path_distance_interval": (0.0, 10.0)})
    return DecentralizedEgoExecutionController(paths, zones)


def context(ego="arbitrary_ego", peer="arbitrary_peer", owed=True):
    commitment = EgoCoordinationCommitment(ego if owed else peer,
        peer if owed else ego, ("agreement",))
    return EgoExecutionContext(ego, state(), "N", 1.0, (commitment,),
        (ExecutionStateMessage(peer, "E", state(lane="e_in_0"), 1.0),), True, 1.0)


def test_context_cannot_accept_global_graph_or_unrelated_commitments(controller):
    names = {f.name for f in fields(EgoExecutionContext)}
    assert not names & {"effective_graph", "ready_vehicle_ids", "critic", "actor_observations"}
    with pytest.raises(ValueError, match="NONLOCAL_EXECUTION_COMMITMENT"):
        replace(context(), commitments=(EgoCoordinationCommitment("X", "Y", ()),))
    inboxes = _deliver_pair_commitments((("A", "B"), ("B", "C")), ("A", "B", "C"), ())
    assert len(inboxes["A"]) == 1
    assert all("A" in (c.yielding_vehicle_id, c.priority_vehicle_id) for c in inboxes["A"])


def test_yielding_ego_derives_own_blocked_zone_and_native_stopping_request(controller):
    own = context()
    decision = controller.decide(own)
    assert decision.ego_id == own.ego_id
    assert decision.permission == "BLOCKED_BY_PRECEDENCE"
    assert decision.blocked_zones == (("CZ", 20.0, "arbitrary_peer"),)
    api = SimpleNamespace(getSpeedMode=lambda ego: 31,
        getActionStepLength=lambda ego: .04,
        getStopSpeed=lambda ego, speed, distance: 2.0,
        getSpeedWithoutTraCI=lambda ego: 4.0)
    constrained = controller.constrain(own, decision, api, .04)
    assert constrained.requested_speed_mps == 2.0 < own.ego_state["speed"]
    assert constrained.speed_constraints[0].vehicle_id == own.ego_id
    assert constrained.speed_constraints[0].speed_mode == SAFE_SUMO_SPEED_MODE == 31


def test_priority_ego_proceeds_without_consuming_other_decisions(controller):
    decision = controller.decide(context(owed=False))
    assert decision.permission == "PERMITTED"
    assert not decision.blocked_zones
    assert decision.decentralized_execution
    assert not decision.centralized_execution_graph_used_for_control


def test_follower_advancement_uses_native_stop_without_granting_entry(controller):
    own=replace(context(),strict_admission=True,negotiation_eligible=False,
        ego_state=dict(state(),road_id='n_in',lane_length=100.))
    held=controller.decide(own)
    calls=[]
    api=SimpleNamespace(getSpeedMode=lambda _:31,getLaneIndex=lambda _:0,
        setStop=lambda *a,**kw:calls.append((a,kw)))
    following=controller.constrain(own,held,api,.04)
    assert following.permission=='SAFE_HOLD'
    assert following.blocked_zones==held.blocked_zones
    assert following.requested_speed_mps is None and not following.speed_constraints
    assert controller.native_hold.synchronize(own,following,controller.paths,api)=='NATIVE_HOLD_INSTALLED'
    assert calls[0][1]['pos']==99.999 and calls[0][1]['duration']>360
    # Physical intrusion is still a hard error even for an ineligible follower.
    with pytest.raises(RuntimeError,match='BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE'):
        controller.decide(replace(own,ego_state=state(progress=1.,lane=':N')))


def test_promoted_head_without_coordination_retains_speed_constraint(controller):
    own=replace(context(),strict_admission=True,negotiation_eligible=True,coordination_complete=False)
    held=controller.decide(own)
    api=SimpleNamespace(getSpeedMode=lambda _:31,getActionStepLength=lambda _:.04,
        getStopSpeed=lambda *args:2.,getSpeedWithoutTraCI=lambda _:4.)
    decision=controller.constrain(own,held,api,.04)
    assert decision.permission=='SAFE_HOLD' and decision.requested_speed_mps==2.
    assert decision.speed_constraints


@pytest.mark.parametrize("change", ["missing_coordination", "stale_coordination",
                                   "missing_clearance", "stale_clearance"])
def test_missing_or_stale_local_information_safe_holds(controller, change):
    own = context()
    updates = {"missing_coordination": {"coordination_complete": False},
               "stale_coordination": {"coordination_timestamp": .96},
               "missing_clearance": {"peer_messages": ()},
               "stale_clearance": {"peer_messages": (
                   replace(own.peer_messages[0], timestamp=.96),)}}
    decision = controller.decide(replace(own, **updates[change]))
    assert decision.permission == "SAFE_HOLD"
    assert decision.blocked_zones[0][1] == 20.0


def test_observed_priority_clearance_releases_ego(controller):
    own = context()
    cleared = replace(own.peer_messages[0], state=state(progress=16.0))
    assert controller.decide(replace(own, peer_messages=(cleared,))).permission == "PERMITTED"


def test_blocked_entry_is_a_hard_safety_failure(controller):
    own = context()
    assert controller.decide(own).blocked_zones
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        controller.decide(replace(own, ego_state=state(progress=1.0, lane=":N")))


def test_missing_context_junction_hold_cannot_be_crossed(controller):
    own = replace(context(), coordination_complete=False)
    assert controller.decide(own).permission == "SAFE_HOLD"
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        controller.decide(replace(own, ego_state=state(progress=1.0, lane=":N")))


def test_prior_blocked_entry_is_detected_even_if_clearance_message_is_lost(controller):
    own = context()
    controller.decide(own)
    with pytest.raises(RuntimeError, match="BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE"):
        controller.decide(replace(own, peer_messages=(),
            ego_state=state(progress=1.0, lane=":N")))


def test_controller_instance_cannot_control_a_different_ego(controller):
    controller.decide(context())
    with pytest.raises(ValueError, match="EXECUTION_CONTROLLER_EGO_MISMATCH"):
        controller.decide(context(ego="other_ego"))


def test_native_follower_has_no_speed_request(controller):
    own = replace(context(), negotiation_eligible=False, coordination_complete=False)
    decision = controller.decide(own)
    assert decision.permission == "NATIVE_FOLLOWING"
    assert decision.requested_speed_mps is None and not decision.blocked_zones


def test_frontline_selection_uses_physics_and_promotes_after_rear_clears(controller):
    movements = {"rear": "N", "front": "N", "east": "E"}
    states = {"rear": state(lane_position=30), "front": state(lane_position=60),
              "east": state(lane="e_in_0", lane_position=40)}
    assert select_queue_heads(states, controller.paths, movements) == ("east", "front")
    states["front"] = state(lane=":N", lane_position=2)
    assert "rear" not in select_queue_heads(states, controller.paths, movements)
    states["front"] = state(lane="n_out_0", lane_position=4)
    assert "rear" not in select_queue_heads(states, controller.paths, movements)
    states["front"] = state(lane="n_out_0", lane_position=6)
    assert select_queue_heads(states, controller.paths, movements) == ("east", "rear")


def test_dense_schedule_has_16_safe_demand_requests_and_all_12_movements():
    scenario = get_scenario("congested_four_approach")
    schedule = validate_presentation_schedule(scenario.schedule(), allow_repeated_movements=True)
    assert scenario.vehicle_count == 16
    assert all(len(schedule[a]) == 4 for a in "NESW")
    assert len({d.movement_path_id for rows in schedule.values() for d in rows}) == 12
    assert scenario.admission_mode == "INDEPENDENT_DEMAND"
    assert [d.scheduled_departure_seconds for d in schedule["N"]] == [0, 1.5, 3, 4.5]


def test_many_live_vehicles_do_not_expand_frontline(controller):
    states, movements = {}, {}
    for approach in "NESW":
        for index in range(4):
            vehicle = f"random_{approach}_{index}"
            movements[vehicle] = approach
            states[vehicle] = state(lane=approach.lower() + "_in_0", lane_position=10 * index)
    assert len(states) == 16
    assert len(select_queue_heads(states, controller.paths, movements)) == 4
    assert approach_queue_depth(states, controller.paths, movements) == dict.fromkeys("NESW", 4)


def _fixture_errors_are_not_known_liveness_failures(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AssertionError as error:
            # xfail(raises=AssertionError) must never consume safety, policy,
            # simulator or live-state contract failures in fixture setup.
            raise RuntimeError("DENSE_FIXTURE_CONTRACT_BREACH:" + str(error)) from error
    return checked


@pytest.fixture(scope="module")
@_fixture_errors_are_not_known_liveness_failures
def congested_run(tmp_path_factory):
    if not shutil.which("sumo"):
        pytest.skip("Real SUMO executable is required for presentation integration")
    root = tmp_path_factory.mktemp("congested_ego_execution")
    scenario = get_scenario("congested_four_approach")
    before = sha256(POLICY_PATH.read_bytes()).hexdigest()
    forbidden_calls = []
    def forbidden(*args, **kwargs):
        forbidden_calls.append(True)
        raise AssertionError("Training, critic or global permission calculation invoked")
    with pytest.MonkeyPatch.context() as patch:
        original_load = panel_runner._load_bundle
        loaded_modules = []
        def guarded_load(path):
            payload, bundle = original_load(path)
            patch.setattr(bundle.centralized_critic, "forward", forbidden)
            for module in (bundle.gnn, bundle.proposer_actor, bundle.responder_actor):
                loaded_modules.append((module, {key: value.clone() for key, value in module.state_dict().items()}))
            return payload, bundle
        original_encode = GraphTensorEncoder.encode
        def bounded_encode(self, observation):
            encoded = original_encode(self, observation)
            assert len(encoded.node_ids) <= 4
            return encoded
        patch.setattr(panel_runner, "_load_bundle", guarded_load)
        patch.setattr(GraphTensorEncoder, "encode", bounded_encode)
        patch.setattr(torch.Tensor, "backward", forbidden)
        patch.setattr(torch.autograd, "backward", forbidden)
        patch.setattr(torch.optim.Adam, "step", forbidden)
        patch.setattr(ConflictZoneExecutionPlanner, "plan", forbidden)
        with contextlib.redirect_stdout(io.StringIO()):
            result = run_runtime_simulation(duration_seconds=360,
                schedule=scenario.schedule(), admission_waves=scenario.admission_waves,
                admission_mode=scenario.admission_mode, scenario_id=scenario.scenario_id,
                output_dir=root, web_live=True, browser_state_path=root / "live_state.json")
        for module, original in loaded_modules:
            assert not module.training
            assert all(torch.equal(original[key], value) for key, value in module.state_dict().items())
    assert not forbidden_calls
    assert sha256(POLICY_PATH.read_bytes()).hexdigest() == before
    # These checks are outside expected-failure test bodies: unsafe behavior,
    # execution/integrity regressions and corrupt live output must always fail.
    import json
    live = json.loads((root / "live_state.json").read_text())
    metrics = result["metrics"]
    assert metrics["collisions"] == metrics["blocked_zone_violations"] == 0
    assert metrics["maximum_negotiation_participants"] <= 4
    assert metrics["centralized_critic_runtime_calls"] == 0
    assert result["policy_hash_unchanged"] and result["decentralized_execution"]
    assert not result["centralized_execution_graph_used_for_control"]
    assert all(result[k] == 0 for k in ("training_operations", "backward_calls", "optimizer_steps", "parameter_updates"))
    assert live["run_metrics"] == json.loads(json.dumps(metrics))
    assert live["completed"] == metrics["total_vehicles_completed"]
    assert metrics["total_vehicles_scheduled"] == metrics["total_vehicles_spawned"] == 16
    assert metrics["maximum_simultaneous_active_vehicles"] >= 10
    assert metrics["maximum_simultaneously_moving_vehicles"] > 4
    assert all(metrics["maximum_per_approach_queue_depth"][a] > 1 for a in "NESW")
    assert metrics["maximum_approaches_with_multiple_queued_vehicles"] == 4
    assert len(result["actual_departure_seconds"]) == 16
    assert not result["pending_insertion_vehicle_ids"]
    if result["run_status"] != "COMPLETED":
        assert result["run_status"] == "INCOMPLETE"
        if result.get("movement_declaration_protocol") == "CONDITIONAL_CLAIM_RECONCILIATION_V1":
            # Approved reconciliation fixes the old zero-discharge condition.
            # Keep partial progress distinct from the unchanged 16/16 test below.
            assert 5 <= metrics["total_vehicles_completed"] < 16
            assert metrics["current_active_vehicle_count"] == 16 - metrics["total_vehicles_completed"]
            assert len(set(result["completed_vehicle_ids"])) == metrics["total_vehicles_completed"]
            assert metrics["mappo_decision_epochs"] > 0
            assert any(e["status"] == "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" for e in result["events"])
        else:
            assert metrics["total_vehicles_completed"] == 0 and metrics["current_active_vehicle_count"] == 16
            assert result["events"] and all(e["status"] == "COMMUNICATED_PRECEDENCE_DISAGREEMENT" for e in result["events"])
    return result, root


def test_real_congested_run_has_safe_dense_traffic_and_complete_discharge(congested_run):
    result, _ = congested_run
    metrics = result["metrics"]
    assert result["run_status"] == "COMPLETED"
    assert metrics["total_vehicles_scheduled"] == metrics["total_vehicles_spawned"] == 16
    assert metrics["total_vehicles_completed"] == 16
    assert metrics["maximum_simultaneous_active_vehicles"] >= 10
    assert metrics["maximum_simultaneously_moving_vehicles"] > 4
    assert all(metrics["maximum_per_approach_queue_depth"][a] > 1 for a in "NESW")
    assert metrics["maximum_approaches_with_multiple_queued_vehicles"] == 4
    assert metrics["maximum_negotiation_participants"] <= 4
    assert metrics["collisions"] == metrics["blocked_zone_violations"] == 0
    assert metrics["centralized_critic_runtime_calls"] == 0
    assert result["policy_hash_unchanged"]
    assert result["decentralized_execution"]
    assert not result["centralized_execution_graph_used_for_control"]
    assert all(result[k] == 0 for k in ("training_operations", "backward_calls",
        "optimizer_steps", "parameter_updates", "held_out_scenarios_consumed"))
    assert len(result["actual_departure_seconds"]) == 16
    assert not result["pending_insertion_vehicle_ids"]
    for ego, departure in result["actual_departure_seconds"].items():
        assert departure >= result["scheduled_departure_seconds"][ego]


def test_live_state_exports_measured_counts_and_execution_flags(congested_run):
    import json
    result, root = congested_run
    live = json.loads((root / "live_state.json").read_text())
    assert live["run_metrics"] == json.loads(json.dumps(result["metrics"]))
    assert live["run_metrics"]["decentralized_execution"]
    assert live["run_metrics"]["current_active_vehicle_count"] == 0
    assert live["completed"] == 16
    assert not live["participants"] and not live["vehicles"]


def test_dense_safety_and_decentralized_integrity_are_not_expected_failures(congested_run):
    result, _ = congested_run
    m = result["metrics"]
    assert m["collisions"] == m["blocked_zone_violations"] == 0
    assert m["maximum_negotiation_participants"] <= 4
    assert result["policy_hash_unchanged"] and result["decentralized_execution"]
    assert not result["centralized_execution_graph_used_for_control"]
    assert m["centralized_critic_runtime_calls"] == 0


def test_dense_live_state_preserves_actual_progress_even_when_incomplete(congested_run):
    import json
    result, root = congested_run
    live = json.loads((root / "live_state.json").read_text())
    assert live["run_metrics"] == json.loads(json.dumps(result["metrics"]))
    assert live["completed"] == result["metrics"]["total_vehicles_completed"]
    assert live["run_metrics"]["current_active_vehicle_count"] == result["metrics"]["current_active_vehicle_count"]
