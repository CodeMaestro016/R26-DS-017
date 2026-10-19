"""Scientific and lifecycle boundaries for the qualitative panel runner."""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from runtime_simulation.reporting import write_panel_outputs
from runtime_simulation.runner import (_dynamic_status,
                               _presentation_timeline,
                               _reconsider_authority_if_safe,
                               run_runtime_simulation, POLICY_PATH, NEGOTIABLE)
from runtime_simulation.schedule import (APPROACH_PATHS, build_default_schedule,
                                 validate_presentation_schedule,
                                 validate_schedule)
from runtime_simulation.visualization import PanelDemoVisualizer
from runtime_simulation.inference import (PanelDeterministicInferenceProvider,
                                  PRESENTATION_SELECTION_RULE)
from runtime_simulation.browser_state import BrowserStatePublisher
from runtime_simulation.scenarios import SCENARIOS, get_scenario
from negotiation_execution.replay import PhysicalBranchReplayRunner
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle)


def test_selected_e5_checkpoint_loads_and_runtime_critic_is_disabled():
    payload, bundle = _load_bundle(POLICY_PATH)
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    assert payload["candidate_id"] == "E5"
    assert provider.runtime_critic_enabled is False
    assert provider.bundle.centralized_critic is None


def test_default_panel_duration_covers_the_four_legitimate_phases():
    assert inspect.signature(run_runtime_simulation).parameters[
        "duration_seconds"].default == 220.0
    cli = Path("run_runtime_simulation.py").read_text(encoding="utf-8")
    assert get_scenario("default_panel").recommended_duration_seconds == 220.0
    assert "scenario.recommended_duration_seconds" in cli


def test_presentation_scenario_catalog_is_unique_qualitative_and_schedule_only():
    assert len({item.scenario_id for item in SCENARIOS}) == len(SCENARIOS)
    assert all(item.evidence_classification ==
               "QUALITATIVE_PRESENTATION_ONLY" for item in SCENARIOS)
    assert all("HELD_OUT" not in item.source_type and
               "VALIDATION" not in item.source_type for item in SCENARIOS)
    forbidden = ("action", "ready", "blocked", "winner", "edge")
    fields = set(SCENARIOS[0].__dataclass_fields__)
    assert not fields.intersection(forbidden)


def test_scenario_selection_changes_only_legal_schedule_and_admission_waves():
    scenario = get_scenario("regulatory_cycle")
    schedule = scenario.schedule()
    assert scenario.vehicle_count == 4
    assert scenario.admission_waves == (("N", "E", "S", "W"),)
    assert {item.movement_path_id for rows in schedule.values()
            for item in rows} == {
        "N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT",
        "S_IN_0_RIGHT", "W_IN_0_LEFT"}
    assert "--scenario" in Path("run_runtime_simulation.py").read_text(
        encoding="utf-8")


def test_main_demo_reuses_rule_then_verified_negotiation_route_waves():
    scenario = get_scenario("yield_negotiation_demo")
    assert scenario.evidence_classification == "QUALITATIVE_PRESENTATION_ONLY"
    assert scenario.movement_waves == (
        ("N_IN_0_LEFT", "E_IN_0_LEFT"),
        ("N_IN_0_STRAIGHT", "E_IN_0_STRAIGHT",
         "S_IN_0_RIGHT", "W_IN_0_LEFT"))
    assert scenario.admission_waves == (("N", "E"), ("N", "E", "S", "W"))
    schedule = validate_presentation_schedule(scenario.schedule())
    assert sum(map(len, schedule.values())) == 6
    raw = Path("runtime_simulation/scenario_catalog.json").read_text(encoding="utf-8").lower()
    for forbidden in ("mappo_action", "winner", "ready_vehicle_ids",
                      "blocked_vehicle_ids", "effective_graph"):
        assert forbidden not in raw


def test_panel_argmax_selects_highest_probability_feasible_semantic_action(
        monkeypatch):
    class Distribution:
        probabilities = torch.tensor([0.1, 0.9])

        @staticmethod
        def evaluate_action_index(index):
            assert index == 1
            return torch.tensor(-0.1053605)

    policy = SimpleNamespace(distribution_for=lambda context: (None,
                                                                Distribution()))
    provider = object.__new__(PanelDeterministicInferenceProvider)
    provider.bundle = SimpleNamespace(policy=policy)
    provider.policy_parameter_identity = ("FROZEN_E5",)
    context = SimpleNamespace(
        decision_role=SimpleNamespace(value="PROPOSER"), ego_id="N02",
        claim_identity=("S01", "N02"), proposal_id=None,
        action_names=("KEEP_CLAIM", "RELINQUISH_CLAIM"),
        action_feasibility_mask=torch.tensor([True, True]))
    monkeypatch.setattr("runtime_simulation.inference.tensor_snapshot",
                        lambda value: ("DISPLAY_ONLY_SNAPSHOT",))
    sample = provider._sample(context, ("B",), ("E",), ("S",), None)
    assert sample.selected_semantic_action == "RELINQUISH_CLAIM"
    assert sample.behavior_probability_vector == pytest.approx((0.1, 0.9))
    assert sample.provenance["argmax_used"] is True
    assert sample.provenance["selection_rule"] == PRESENTATION_SELECTION_RULE


def test_browser_state_publisher_is_atomic_display_only_and_returns_nothing(
        tmp_path):
    vehicle = SimpleNamespace(
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    target = tmp_path / "runtime" / "live_state.json"
    publisher = BrowserStatePublisher(
        target, SimpleNamespace(vehicle=vehicle), frequency_hz=10)
    result = publisher.publish(
        simulation_time=1.0,
        map_state={"bounds": {"min_x": 0, "max_x": 10,
                              "min_y": 0, "max_y": 10}},
        running=True, status="NEGOTIATING", participants=("DYNAMIC_AV",),
        ready=(), blocked=(), force=True)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert result is None and payload["display_only"] is True
    assert payload["vehicles"][0]["display_state"] == "NEGOTIATING"
    assert payload["vehicles"][0]["front_bumper_x"] == 4.0
    assert payload["vehicles"][0]["length_m"] == 4.8
    assert payload["vehicles"][0]["width_m"] == 1.8
    assert "paths" not in payload
    assert not target.with_suffix(".json.tmp").exists()


@pytest.mark.parametrize("ready,blocked,expected", (
    (("DYNAMIC_AV",), (), "READY"),
    ((), ("DYNAMIC_AV",), "BLOCKED")))
def test_planner_permission_color_precedes_mappo_participation(
        tmp_path, ready, blocked, expected):
    vehicle = SimpleNamespace(
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    target = tmp_path / "live_state.json"
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    publisher.publish(
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        participants=("DYNAMIC_AV",), ready=ready, blocked=blocked,
        mappo_invocation="AUTHORIZED", force=True)
    item = json.loads(target.read_text(encoding="utf-8"))["vehicles"][0]
    assert item["display_state"] == expected
    assert item["execution_state"] == expected
    assert item["negotiation_involvement"] is True


def test_latest_mappo_participation_survives_later_execution_frame(tmp_path):
    vehicle = SimpleNamespace(
        getIDList=lambda: ("DYNAMIC_AV",), getPosition=lambda _: (4.0, 5.0),
        getAngle=lambda _: 90.0, getSpeed=lambda _: 2.5,
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    target = tmp_path / "live_state.json"
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    publisher.publish(
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        status="NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
        participants=("DYNAMIC_AV",), ready=("DYNAMIC_AV",),
        mappo_invocation="AUTHORIZED", force=True)
    publisher.publish(
        simulation_time=2.0, map_state={"bounds": {}}, running=True,
        status="EXECUTING", participants=(), ready=("DYNAMIC_AV",),
        mappo_invocation="NOT_REQUIRED", force=True)
    item = json.loads(target.read_text(encoding="utf-8"))["vehicles"][0]
    assert item["display_state"] == "READY"
    assert item["negotiation_involvement"] is True


def test_vehicle_explainability_uses_real_ego_local_runtime_outputs_only():
    prediction = {"primary": {"label": "LEFT", "confidence": 0.91},
                  "secondary": None, "fused_label": "LEFT",
                  "status": "MODEL_EVALUABLE"}
    ldm = SimpleNamespace(
        tracks={"E01": {}, "N01": {
            "is_observed": True, "position_history": (1, 2, 3),
            "intention_prediction": prediction}},
        current_conflict_graph={"edges": ({"target_track_id": "N01"},)},
        current_encoded_graph_observation=SimpleNamespace(
            dashboard_summary=lambda: {"node_count": 2,
                                       "node_feature_dimension": 8}))
    observations = SimpleNamespace(get_ldm=lambda vehicle_id: ldm)
    plan = SimpleNamespace(ready_vehicle_ids=(), blocked_vehicle_ids=("E01",))
    constraint = SimpleNamespace(vehicle_id="E01",
                                 requested_speed_cap_mps=2.4)
    evidence = BrowserStatePublisher._vehicle_evidence(
        "E01", {"speed": 3.2, "accel": -1.1}, observations,
        ({"ego_id": "E01", "joint_precedence_edges": (
            {"yielding_vehicle_id": "E01",
             "priority_vehicle_id": "N01"},)},), plan, (constraint,),
        ({"ego_id": "E01", "decision_role": "PROPOSER",
          "selected_action": "RELINQUISH_CLAIM"},))
    assert evidence["speed_mps"] == 3.2
    assert evidence["acceleration_mps2"] == -1.1
    assert evidence["local_perception"]["observed_vehicle_ids"] == ("N01",)
    assert evidence["local_intention_predictions"][0]["label"] == "LEFT"
    assert evidence["planner"]["state"] == "BLOCKED"
    assert evidence["control"]["speed_cap_mps"] == 2.4
    assert "route" not in json.dumps(evidence).lower()


def test_finished_browser_frame_preserves_last_inspectable_evidence(tmp_path):
    vehicle = SimpleNamespace(
        getIDList=lambda: ("E01",), getPosition=lambda _: (1.0, 2.0),
        getAngle=lambda _: 90.0, getSpeed=lambda _: 3.0,
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    target = tmp_path / "live_state.json"
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    plan = SimpleNamespace(ready_vehicle_ids=("E01",), blocked_vehicle_ids=())
    publisher.publish(
        simulation_time=1.0, map_state={"bounds": {}}, running=True,
        status="READY", ready=("E01",), scientific_states={"E01": {
            "position": (1.0, 2.0), "angle_degrees": 90.0, "length": 4.8,
            "width": 1.8, "speed": 3.0, "accel": 0.2}}, plan=plan,
        events=({"event": "PLAN_INVALIDATED"},), force=True)
    publisher.publish(
        simulation_time=2.0, map_state={"bounds": {}}, running=False,
        status="FINISHED", completed=1, scheduled=1, force=True)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["running"] is False and payload["status"] == "FINISHED"
    assert payload["vehicles"] == []
    assert payload["completed_vehicles"][0]["acceleration_mps2"] == 0.2
    assert payload["events"] == [{"event": "PLAN_INVALIDATED"}]


def test_publisher_retains_completed_vehicle_final_snapshot_and_trace(tmp_path):
    vehicle_ids = ["E01"]
    vehicle = SimpleNamespace(
        getIDList=lambda: tuple(vehicle_ids), getPosition=lambda _: (1.0, 2.0),
        getAngle=lambda _: 90.0, getSpeed=lambda _: 3.0,
        getLength=lambda _: 4.8, getWidth=lambda _: 1.8)
    target = tmp_path / "live.json"
    publisher = BrowserStatePublisher(target, SimpleNamespace(vehicle=vehicle))
    plan = SimpleNamespace(ready_vehicle_ids=("E01",), blocked_vehicle_ids=())
    state = {"E01": {"position": (1.0, 2.0), "angle_degrees": 90.0,
                     "length": 4.8, "width": 1.8, "speed": 3.0,
                     "accel": -0.2}}
    publisher.publish(simulation_time=1, map_state={"bounds": {}}, running=True,
                      status="READY", scientific_states=state, plan=plan,
                      force=True)
    vehicle_ids.clear()
    publisher.publish(simulation_time=2, map_state={"bounds": {}}, running=True,
                      status="NO_ACTIVE_CONFLICT", scientific_states={}, plan=plan,
                      force=True)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["completed_vehicles"][0]["id"] == "E01"
    assert payload["completed_vehicles"][0]["display_state"] == "CLEARED"
    history = publisher.presentation_vehicle_history()
    assert history["process_traces"]["E01"][-1]["stage"] == "COMPLETED"


def test_presentation_summary_writer_distinguishes_stopped_from_completed(tmp_path):
    from runtime_simulation.reporting import write_presentation_run_summary
    base = {"presentation_scenario_id": "regulatory_cycle",
            "started_at_utc": "start", "ended_at_utc": "end",
            "actual_simulation_time_seconds": 12.5,
            "policy_hash_unchanged": True, "events": [], "diagnostics": [],
            "presentation_vehicle_history": {"final_snapshots": (),
                                               "process_traces": {}},
            "metrics": {key: 0 for key in (
                "presentation_vehicles_scheduled",
                "presentation_vehicles_completed", "unfinished_vehicles",
                "collisions", "blocked_zone_violations", "negotiation_events",
                "mappo_decision_epochs", "rule_resolved_events",
                "renegotiation_events")}}
    stopped = dict(base, presentation_run_id="stopped",
                   run_status="USER_STOPPED")
    target = write_presentation_run_summary(stopped, tmp_path)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["run_status"] == "USER_STOPPED"
    assert payload["metrics"]["presentation_vehicles_completed"] == 0
    assert payload["evidence_classification"] == "QUALITATIVE_PRESENTATION_ONLY"
    assert payload["validation_evidence"] is False


def test_live_timeline_retains_real_mappo_event_evidence_after_later_rule_event():
    authorized = {"timestamp": 10.0, "status": "NEGOTIATION_REQUIRED_REGULATORY_CYCLE",
                  "mappo_invocation": "AUTHORIZED", "participants": ("E01", "N01"),
                  "original_regulatory_graph": (("E01", "N01"),),
                  "proposer_actions": (("edge", "RELINQUISH_CLAIM"),),
                  "responder_actions": (("proposal", "ACCEPT_RELINQUISHMENT"),),
                  "effective_coordination_graph": (),
                  "ready_vehicle_ids": ("E01",), "blocked_vehicle_ids": ("N01",),
                  "policy_factor_diagnostics": ({"ego_id": "E01"},)}
    later_rule = dict(authorized, timestamp=20.0,
                      status="REGULATORY_ORDER_RESOLVED",
                      mappo_invocation="NOT_REQUIRED",
                      proposer_actions=(), responder_actions=())
    timeline = _presentation_timeline((authorized, later_rule), ())
    assert timeline[-1]["mappo_invocation"] == "NOT_REQUIRED"
    saved = timeline[0]
    assert saved["mappo_invocation"] == "AUTHORIZED"
    assert saved["original_graph"] == (("E01", "N01"),)
    assert saved["proposer_actions"] and saved["responder_actions"]
    assert saved["ready"] == ("E01",) and saved["blocked"] == ("N01",)


def test_verified_mappo_tags_are_backed_by_current_presentation_audit_only():
    audit_path = Path("runtime_simulation/scenario_audit_current.json")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["validation_or_held_out_consumed"] == 0
    observed = {item["scenario_id"]: item for item in audit["scenarios"]}
    for scenario in SCENARIOS:
        if scenario.verified_tag == "MAPPO NEGOTIATION":
            assert observed[scenario.scenario_id]["mappo_authorized_events"] >= 1
    assert observed["rule_resolved_two"]["mappo_authorized_events"] == 0


def test_scenario_inputs_cannot_set_scientific_outcomes():
    raw = Path("runtime_simulation/scenario_catalog.json").read_text(encoding="utf-8").lower()
    for forbidden in ("negotiation_status", "mappo_action", "effective_graph",
                      "ready_vehicle_ids", "blocked_vehicle_ids", "winner"):
        assert forbidden not in raw


def test_no_training_optimizer_or_backward_path_exists_in_panel_runner():
    source = inspect.getsource(run_runtime_simulation).lower()
    assert "optimizer.step" not in source
    assert "zero_grad" not in source
    assert ".backward(" not in source
    assert "training_operations" in source and "parameter_updates" in source


def test_policy_hash_contract_is_checked_before_and_after():
    source = inspect.getsource(run_runtime_simulation)
    assert "policy_hash_before" in source and "policy_hash_after" in source
    assert "SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO" in source


def test_exactly_one_sumo_start_and_close_are_in_runner_lifecycle():
    source = inspect.getsource(run_runtime_simulation)
    assert source.count("environment.start()") == 1
    assert source.count("environment.close()") == 1
    assert '"sumo_start_count": starts' in source
    assert '"sumo_close_count": closes' in source


def test_schedule_uses_all_12_routes_with_one_rolling_slot_per_approach():
    schedule = validate_schedule(build_default_schedule())
    assert schedule.keys() == APPROACH_PATHS.keys()
    assert sum(map(len, schedule.values())) == 12
    assert all(len(rows) == 3 for rows in schedule.values())
    assert all(len({item.approach for item in rows}) == 1
               for rows in schedule.values())


def test_negotiation_scope_is_bounded_to_four_and_unique_approaches():
    source = inspect.getsource(run_runtime_simulation)
    assert "len(participants) > 4" in source
    assert "PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED" in source
    assert "slots[approach] is None" in source


def test_rule_resolved_state_does_not_invoke_mappo():
    snapshots = ({"negotiation_status": "REGULATORY_ORDER_RESOLVED"},)
    assert _dynamic_status(snapshots, (("A", "B"),)) == (
        "REGULATORY_ORDER_RESOLVED")
    source = inspect.getsource(run_runtime_simulation)
    assert "if status in NEGOTIABLE" in source
    assert "TRAFFIC_RULE_ORDER_ALREADY_RESOLVED" in source


def test_negotiable_cycle_uses_actual_selected_provider_actions():
    assert "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" in NEGOTIABLE
    source = Path("runtime_simulation/runner.py").read_text(encoding="utf-8")
    assert "provider.select_joint_actions" in source
    assert "outcome.proposer_assignment.claim_action_assignments" in source
    assert "outcome.responder_assignment.response_action_assignments" in source


def test_incomplete_actor_context_is_diagnosed_and_retried():
    source = inspect.getsource(run_runtime_simulation)
    assert "RESPONDER_CONTEXT_INCOMPLETE" in source
    assert "missing_encoded_egos" in source
    assert "Do not freeze an incomplete authority" in source


def test_mappo_epoch_count_requires_a_non_null_live_outcome():
    source = inspect.getsource(run_runtime_simulation)
    increment = 'metrics["mappo_decision_epochs"] += 1'
    assert source.index("if outcome is not None:") < source.index(increment)


def test_predeclared_case_is_from_training_manifest_not_held_out():
    source = inspect.getsource(run_runtime_simulation)
    assert "EXISTING_TRAINING_SIDE_ILLUSTRATIVE_CASE" in source
    expected = {"E_IN_0_STRAIGHT", "N_IN_0_STRAIGHT",
                "S_IN_0_RIGHT", "W_IN_0_LEFT"}
    schedule = build_default_schedule()
    actual = {schedule[approach][index].movement_path_id
              for approach, index in (("E", 1), ("N", 1),
                                      ("S", 0), ("W", 0))}
    assert actual == expected


def test_disagreement_is_conservatively_classified_and_not_policy_authorized():
    snapshots = ({"negotiation_status":
                  "COMMUNICATED_PRECEDENCE_DISAGREEMENT"},)
    assert _dynamic_status(snapshots, (("A", "B"),)) == (
        "COMMUNICATED_PRECEDENCE_DISAGREEMENT")
    assert "COMMUNICATED_PRECEDENCE_DISAGREEMENT" not in NEGOTIABLE


def test_no_hard_coded_winner_or_semantic_action_exists():
    source = inspect.getsource(run_runtime_simulation)
    forbidden = ("smallest", "alphabetical", "timeout winner",
                 'outcome = "RELINQUISH_CLAIM"',
                 'outcome = "ACCEPT_RELINQUISHMENT"')
    assert not any(item in source.lower() for item in forbidden[:3])
    assert not any(item in source for item in forbidden[3:])


def test_mappo_never_directly_issues_speed_commands():
    provider_source = inspect.getsource(
        FinalSelectionInferenceProvider).lower()
    assert "setspeed" not in provider_source
    runner_source = inspect.getsource(run_runtime_simulation)
    assert "ego_controller.constrain" in runner_source
    assert "PhysicalBranchReplayRunner._apply_control" not in runner_source


def test_ready_blocked_are_audit_of_ego_execution_with_native_speed_constraints():
    runner_source = inspect.getsource(run_runtime_simulation)
    control_source = inspect.getsource(PhysicalBranchReplayRunner._apply_control)
    assert "planner.plan" not in runner_source
    assert "ego_controller.decide(context)" in runner_source
    assert "ready_vehicle_ids" in runner_source
    assert "blocked_vehicle_ids" in runner_source
    assert "PRECEDENCE_SPEED_CAP" in control_source
    assert "RELEASE_TO_SUMO" in control_source


def test_visualization_is_failure_isolated_and_has_no_return_to_control():
    source = inspect.getsource(PanelDemoVisualizer.update)
    assert "setColor" in source and "except Exception" in source
    assert "return plan" not in source and "setSpeed" not in source


class _FakeGUI:
    def __init__(self, fail_schema=False):
        self.calls = []
        self.fail_schema = fail_schema

    def getIDList(self):
        self.calls.append(("getIDList",))
        return ("View #0",)

    def setBoundary(self, *args):
        self.calls.append(("setBoundary",) + args)

    def setOffset(self, *args):
        self.calls.append(("setOffset",) + args)

    def setZoom(self, *args):
        self.calls.append(("setZoom",) + args)

    def setSchema(self, *args):
        self.calls.append(("setSchema",) + args)
        if self.fail_schema:
            raise RuntimeError("unsupported scheme")


class _FakeVehicle:
    def __init__(self):
        self.colors = {}

    def getIDList(self):
        return tuple("ABCD")

    def setColor(self, vehicle_id, color):
        self.colors[vehicle_id] = color


def _visual_path_manager():
    paths = {
        name: SimpleNamespace(centerline_geometry=geometry)
        for name, geometry in {
            "N": ((300.0, 307.0), (300.0, 293.0)),
            "E": ((307.0, 300.0), (293.0, 300.0)),
        }.items()}
    return SimpleNamespace(paths=paths)


def test_camera_uses_intersection_geometry_and_focused_zoom():
    gui = _FakeGUI()
    visualizer = PanelDemoVisualizer(
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=True)
    visualizer.configure_camera(_visual_path_manager())
    assert ("setOffset", "View #0", 300.0, 300.0) in gui.calls
    assert ("setZoom", "View #0", 2000.0) in gui.calls
    assert not any(call[0] == "getBoundary" for call in gui.calls)


def test_camera_is_gui_only_and_headless_invokes_no_gui_api():
    gui = _FakeGUI()
    visualizer = PanelDemoVisualizer(
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=False)
    visualizer.configure_camera(_visual_path_manager())
    visualizer.update(("A",), ("A",), (), ())
    assert gui.calls == []


def test_unsafe_programmatic_schema_selection_is_not_used():
    gui = _FakeGUI(fail_schema=True)
    visualizer = PanelDemoVisualizer(
        SimpleNamespace(gui=gui, vehicle=_FakeVehicle()), enabled=True)
    visualizer.configure_camera(_visual_path_manager())
    assert any(call[0] == "setZoom" for call in gui.calls)
    assert not any(call[0] == "setSchema" for call in gui.calls)


def test_vehicle_color_legend_and_blocked_precedence_are_preserved():
    vehicle = _FakeVehicle()
    visualizer = PanelDemoVisualizer(
        SimpleNamespace(gui=_FakeGUI(), vehicle=vehicle), enabled=True)
    visualizer.update(tuple("ABCD"), negotiating=("B", "D"),
                      ready=("C", "D"), blocked=("D",))
    assert vehicle.colors == {
        "A": PanelDemoVisualizer.BLUE,
        "B": PanelDemoVisualizer.YELLOW,
        "C": PanelDemoVisualizer.GREEN,
        "D": PanelDemoVisualizer.RED}


def test_visualization_contains_no_vehicle_motion_or_lifecycle_calls():
    source = Path("runtime_simulation/visualization.py").read_text(encoding="utf-8")
    forbidden = ("setSpeed", "slowDown", "moveTo", "moveToXY",
                 "teleport", "vehicle.remove", "vehicle.add")
    assert not any(token in source for token in forbidden)


def test_route_truth_is_used_only_for_spawn_and_not_actor_arguments():
    source = inspect.getsource(run_runtime_simulation)
    call = source[source.index("provider.select_joint_actions"):]
    call = call[:call.index("elif status")]
    assert "route" not in call and "movement" not in call
    assert '"route_truth_actor_leakage": 0' in source


def test_schedule_and_output_use_no_held_out_scenario():
    source = inspect.getsource(run_runtime_simulation)
    assert "ScenarioRole.HELD_OUT" not in source
    assert '"held_out_scenarios_consumed": 0' in source
    assert '"validation_or_held_out_search": False' in source


def test_historical_result_directory_is_not_an_output_target():
    source = inspect.getsource(write_panel_outputs)
    assert "results/runtime_simulation" in source
    assert "final_mappo_selection_v2" not in source
    assert "liveness_fix_validation" not in source


def test_s01_clear_releases_stale_authority_when_physically_safe():
    helper = SimpleNamespace(_plan_invalidation_reasons=
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    old_identity = (
        ("PANEL_AV_E_02", "PANEL_AV_N_02", "PANEL_AV_S_01",
         "PANEL_AV_W_01"),
        (("PANEL_AV_N_02", "PANEL_AV_W_01"),
         ("PANEL_AV_S_01", "PANEL_AV_N_02")), ())
    new_identity = (
        ("PANEL_AV_E_02", "PANEL_AV_N_02", "PANEL_AV_W_01"),
        (("PANEL_AV_N_02", "PANEL_AV_W_01"),),
        (("PANEL_AV_S_01", "CZ_1"),))
    authority = SimpleNamespace(
        state_identity=old_identity,
        effective_graph=old_identity[1],
        initial_plan=SimpleNamespace(
            graph_status="EXECUTABLE",
            ready_vehicle_ids=("PANEL_AV_E_02", "PANEL_AV_S_01",
                               "PANEL_AV_W_01"),
            blocked_vehicle_ids=("PANEL_AV_N_02",)))
    safe_zones = {"CZ_1": {"state": "CLEARED"}}

    reconsidered, reasons = _reconsider_authority_if_safe(
        helper, authority, new_identity, safe_zones)

    assert reconsidered is None
    assert reasons == (
        "ACTIVE_PARTICIPANT_SET_CHANGED",
        "RELEVANT_PRECEDENCE_GRAPH_CHANGED",
        "CONFLICT_ZONE_CLEARED")
    assert reconsidered is None and new_identity != old_identity


def test_state_change_defers_while_occupied_then_reconsiders_when_clear():
    helper = SimpleNamespace(_plan_invalidation_reasons=
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    authority = SimpleNamespace(
        state_identity=(("OLD",), (), ()),
        initial_plan=SimpleNamespace(
            graph_status="EXECUTABLE", ready_vehicle_ids=("OLD",)))

    retained, reasons = _reconsider_authority_if_safe(
        helper, authority, (("NEW",), (), ()),
        {"CZ_1": {"state": "CURRENTLY_OCCUPYING"}})
    assert retained is authority
    assert reasons == ()

    reconsidered, reasons = _reconsider_authority_if_safe(
        helper, retained, (("NEW",), (), ()),
        {"CZ_1": {"state": "CLEARED"}})
    assert reconsidered is None
    assert reasons == ("ACTIVE_PARTICIPANT_SET_CHANGED",)


def test_graph_churn_alone_does_not_resample_executable_authority():
    helper = SimpleNamespace(_plan_invalidation_reasons=
        CoupledNegotiationTrainingEnvironment._plan_invalidation_reasons)
    old_identity = (("A", "B"), (("A", "B"),), ())
    new_identity = (("A", "B"), (("B", "A"),), ())
    authority = SimpleNamespace(
        state_identity=old_identity,
        initial_plan=SimpleNamespace(
            graph_status="EXECUTABLE", ready_vehicle_ids=("A",)))

    retained, reasons = _reconsider_authority_if_safe(
        helper, authority, new_identity,
        {"CZ_1": {"state": "BEFORE_ZONE"}})

    assert retained is authority
    assert reasons == ()


def test_panel_metadata_is_explicitly_non_evidentiary(tmp_path):
    result = {"policy_hash_unchanged": True, "metrics": {
        key: 0 for key in ("presentation_vehicles_scheduled",
        "presentation_vehicles_completed", "unfinished_vehicles",
        "negotiation_events", "mappo_decision_epochs",
        "rule_resolved_events", "renegotiation_events",
        "safe_hold_activations", "collisions", "blocked_zone_violations",
        "maximum_negotiation_participants")}}
    write_panel_outputs(result, tmp_path)
    text = (tmp_path / "latest_runtime_simulation_summary.md").read_text()
    assert "QUALITATIVE_PRESENTATION_ONLY" in text
    assert "not validation" in text


def test_simulation_step_and_vehicle_physics_are_not_panel_parameters():
    source = inspect.getsource(run_runtime_simulation)
    assert "SIM_TIME_STEP" in source
    assert not any(token in source for token in
                   ("setAccel", "setDecel", "setMaxSpeed", "teleport"))
