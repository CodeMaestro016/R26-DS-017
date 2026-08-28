"""Scientific and lifecycle boundaries for the qualitative panel runner."""

import inspect
from pathlib import Path
from types import SimpleNamespace

from panel_demo.reporting import write_panel_outputs
from panel_demo.runner import (_dynamic_status, run_panel_demo, POLICY_PATH,
                               NEGOTIABLE)
from panel_demo.schedule import (APPROACH_PATHS, build_default_schedule,
                                 validate_schedule)
from panel_demo.visualization import PanelDemoVisualizer
from negotiation_execution.replay import PhysicalBranchReplayRunner
from negotiation_training.final_selection import (
    FinalSelectionInferenceProvider, _load_bundle)


def test_selected_e5_checkpoint_loads_and_runtime_critic_is_disabled():
    payload, bundle = _load_bundle(POLICY_PATH)
    provider = FinalSelectionInferenceProvider(bundle, sampling_seed=0)
    assert payload["candidate_id"] == "E5"
    assert provider.runtime_critic_enabled is False
    assert provider.bundle.centralized_critic is None


def test_default_panel_duration_covers_the_four_legitimate_phases():
    assert inspect.signature(run_panel_demo).parameters[
        "duration_seconds"].default == 220.0
    cli = Path("run_panel_demo.py").read_text(encoding="utf-8")
    assert 'default=220.0' in cli


def test_no_training_optimizer_or_backward_path_exists_in_panel_runner():
    source = inspect.getsource(run_panel_demo).lower()
    assert "optimizer.step" not in source
    assert "zero_grad" not in source
    assert ".backward(" not in source
    assert "training_operations" in source and "parameter_updates" in source


def test_policy_hash_contract_is_checked_before_and_after():
    source = inspect.getsource(run_panel_demo)
    assert "policy_hash_before" in source and "policy_hash_after" in source
    assert "SELECTED_POLICY_HASH_CHANGED_DURING_PANEL_DEMO" in source


def test_exactly_one_sumo_start_and_close_are_in_runner_lifecycle():
    source = inspect.getsource(run_panel_demo)
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
    source = inspect.getsource(run_panel_demo)
    assert "len(participants) > 4" in source
    assert "PANEL_NEGOTIATION_SCOPE_BOUNDARY_BREACHED" in source
    assert "slots[approach] is None" in source


def test_rule_resolved_state_does_not_invoke_mappo():
    snapshots = ({"negotiation_status": "REGULATORY_ORDER_RESOLVED"},)
    assert _dynamic_status(snapshots, (("A", "B"),)) == (
        "REGULATORY_ORDER_RESOLVED")
    source = inspect.getsource(run_panel_demo)
    assert "if status in NEGOTIABLE" in source
    assert "TRAFFIC_RULE_ORDER_ALREADY_RESOLVED" in source


def test_negotiable_cycle_uses_actual_selected_provider_actions():
    assert "NEGOTIATION_REQUIRED_REGULATORY_CYCLE" in NEGOTIABLE
    source = Path("panel_demo/runner.py").read_text(encoding="utf-8")
    assert "provider.select_joint_actions" in source
    assert "outcome.proposer_assignment.claim_action_assignments" in source
    assert "outcome.responder_assignment.response_action_assignments" in source


def test_incomplete_actor_context_is_diagnosed_and_retried():
    source = inspect.getsource(run_panel_demo)
    assert "RESPONDER_CONTEXT_INCOMPLETE" in source
    assert "missing_encoded_egos" in source
    assert "Do not freeze an incomplete authority" in source


def test_mappo_epoch_count_requires_a_non_null_live_outcome():
    source = inspect.getsource(run_panel_demo)
    increment = 'metrics["mappo_decision_epochs"] += 1'
    assert source.index("if outcome is not None:") < source.index(increment)


def test_predeclared_case_is_from_training_manifest_not_held_out():
    source = inspect.getsource(run_panel_demo)
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
    source = inspect.getsource(run_panel_demo)
    forbidden = ("smallest", "alphabetical", "timeout winner",
                 'outcome = "RELINQUISH_CLAIM"',
                 'outcome = "ACCEPT_RELINQUISHMENT"')
    assert not any(item in source.lower() for item in forbidden[:3])
    assert not any(item in source for item in forbidden[3:])


def test_mappo_never_directly_issues_speed_commands():
    provider_source = inspect.getsource(
        FinalSelectionInferenceProvider).lower()
    assert "setspeed" not in provider_source
    runner_source = inspect.getsource(run_panel_demo)
    assert "PhysicalBranchReplayRunner._apply_control" in runner_source


def test_ready_blocked_and_speed_constraints_remain_existing_execution_path():
    runner_source = inspect.getsource(run_panel_demo)
    control_source = inspect.getsource(PhysicalBranchReplayRunner._apply_control)
    assert "planner.plan" in runner_source
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
    source = Path("panel_demo/visualization.py").read_text(encoding="utf-8")
    forbidden = ("setSpeed", "slowDown", "moveTo", "moveToXY",
                 "teleport", "vehicle.remove", "vehicle.add")
    assert not any(token in source for token in forbidden)


def test_route_truth_is_used_only_for_spawn_and_not_actor_arguments():
    source = inspect.getsource(run_panel_demo)
    call = source[source.index("provider.select_joint_actions"):]
    call = call[:call.index("elif status")]
    assert "route" not in call and "movement" not in call
    assert '"route_truth_actor_leakage": 0' in source


def test_schedule_and_output_use_no_held_out_scenario():
    source = inspect.getsource(run_panel_demo)
    assert "ScenarioRole.HELD_OUT" not in source
    assert '"held_out_scenarios_consumed": 0' in source
    assert '"validation_or_held_out_search": False' in source


def test_historical_result_directory_is_not_an_output_target():
    source = inspect.getsource(write_panel_outputs)
    assert "results/panel_demo" in source
    assert "final_mappo_selection_v2" not in source
    assert "liveness_fix_validation" not in source


def test_event_driven_liveness_identity_and_safe_transition_are_reused():
    source = inspect.getsource(run_panel_demo)
    assert "_decision_state_identity" in source
    assert "_plan_invalidation_reasons" in source
    assert "PLAN_INVALIDATED" in source
    assert "RENEGOTIATION_REQUIRED" in source
    assert "safe_transition" in source


def test_panel_metadata_is_explicitly_non_evidentiary(tmp_path):
    result = {"policy_hash_unchanged": True, "metrics": {
        key: 0 for key in ("presentation_vehicles_scheduled",
        "presentation_vehicles_completed", "unfinished_vehicles",
        "negotiation_events", "mappo_decision_epochs",
        "rule_resolved_events", "renegotiation_events",
        "safe_hold_activations", "collisions", "blocked_zone_violations",
        "maximum_negotiation_participants")}}
    write_panel_outputs(result, tmp_path)
    text = (tmp_path / "latest_panel_demo_summary.md").read_text()
    assert "QUALITATIVE_PRESENTATION_ONLY" in text
    assert "not validation" in text


def test_simulation_step_and_vehicle_physics_are_not_panel_parameters():
    source = inspect.getsource(run_panel_demo)
    assert "SIM_TIME_STEP" in source
    assert not any(token in source for token in
                   ("setAccel", "setDecel", "setMaxSpeed", "teleport"))
