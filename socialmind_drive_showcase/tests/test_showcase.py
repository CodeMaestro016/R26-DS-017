import hashlib
import inspect
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from socialmind_drive_showcase import config
from socialmind_drive_showcase.pages.home import home_page
from socialmind_drive_showcase.pages.component2_live_view import (
    authoritative_road_geometry, build_world_transform,
    NegotiationVisualHold, render_sumo_style_svg, short_vehicle_label,
    svg_vehicle_rotation, set_camera_zoom, vehicle_geometric_center)
from socialmind_drive_showcase.pages.component2_inspector import (
    stable_inspector_html, stable_inspector_script)
from socialmind_drive_showcase.pages.component2_explainer import (
    DECISION_STEPS, IMPLEMENTATION_MAP, load_research_evidence)
from socialmind_drive_showcase.pages.component2_results import (
    presentation_run_status)
from socialmind_drive_showcase.services.presentation_history import read_presentation_runs
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.result_reader import read_panel_results
from socialmind_drive_showcase.services.live_state_reader import read_live_state
from socialmind_drive_showcase.services.scenario_reader import read_scenario_catalog
from socialmind_drive_showcase.ui.reusable import (image_or_fallback,
    initials_for, portrait_or_initials)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def test_app_and_home_import_successfully():
    import socialmind_drive_showcase.app as showcase_app
    assert callable(showcase_app.build_app)
    assert callable(home_page)


def test_all_four_components_exist_and_group_live_integrations_are_preserved():
    assert len(config.COMPONENTS) == 4
    assert [item.number for item in config.COMPONENTS] == ["01", "02", "03", "04"]
    assert [item.number for item in config.COMPONENTS if item.live] == ["02", "03"]
    assert config.COMPONENT2.launch_command is not None


def test_component_two_command_resolves_to_existing_entry_point():
    command = config.COMPONENT2.launch_command
    assert command == ("{python}", "run_runtime_simulation.py", "--web-live",
                       "--presentation-delay-ms", "10")
    assert (config.COMPONENT2.working_directory / command[1]).is_file()




def test_result_reader_loads_current_panel_result():
    result = read_panel_results(config.COMPONENT2.result_path)
    assert result["available"] is True
    assert "presentation_vehicles_completed" in result["metrics"]
    assert result["payload"]["evidence_classification"] == "QUALITATIVE_PRESENTATION_ONLY"


def test_missing_and_invalid_results_have_friendly_empty_state(tmp_path):
    missing = read_panel_results(tmp_path / "missing.json")
    assert missing["available"] is False and "No runtime simulation result" in missing["message"]
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert read_panel_results(bad)["available"] is False


def test_live_state_reader_handles_missing_invalid_and_stale(tmp_path):
    target = tmp_path / "live.json"
    assert read_live_state(target)["available"] is False
    target.write_text("bad", encoding="utf-8")
    assert read_live_state(target)["available"] is False
    target.write_text('{"running":true}', encoding="utf-8")
    state = read_live_state(target, stale_after_seconds=0, clock=lambda: 10**12)
    assert state["available"] is True and state["stale"] is True


def test_sumo_style_renderer_uses_runtime_xy_angle_and_network_geometry():
    payload = {"vehicles": [{"id": "DYNAMIC_AV",
                              "front_bumper_x": 300,
                              "front_bumper_y": 300,
                              "angle_degrees": 90, "length_m": 4.8,
                              "width_m": 1.8, "display_state": "READY"}]}
    svg = render_sumo_style_svg(payload)
    geometry = authoritative_road_geometry()
    assert "DYNAMIC_AV" in svg and "rotate(0.00)" in svg
    assert "#20c86b" in svg and geometry["lanes"]
    assert "#57964c" in svg and "sumo-junction" in svg
    assert "sumo-road-boundaries" in svg and "stroke-width" in svg


def test_world_transform_uses_one_uniform_scale_and_centers_viewport():
    transform = build_world_transform(1000, 600, (0, 0, 200, 200))
    assert transform.scale == 3.0
    assert transform.point(0, 200) == pytest.approx((200, 0))
    assert transform.point(200, 0) == pytest.approx((800, 600))
    x_delta = transform.point(11, 10)[0] - transform.point(10, 10)[0]
    y_delta = transform.point(10, 10)[1] - transform.point(10, 11)[1]
    assert x_delta == pytest.approx(y_delta)


@pytest.mark.parametrize("angle,expected", (
    (0, (100, 197.5)), (90, (97.5, 200)),
    (180, (100, 202.5)), (270, (102.5, 200))))
def test_front_bumper_is_converted_to_geometric_center(angle, expected):
    assert vehicle_geometric_center(100, 200, angle, 5) == pytest.approx(
        expected)


@pytest.mark.parametrize("angle,expected", (
    (0, 270), (90, 0), (180, 90), (270, 180)))
def test_sumo_cardinal_angle_conversion(angle, expected):
    assert svg_vehicle_rotation(angle) == expected


def test_labels_are_short_but_preserve_full_id_in_svg_tooltip():
    assert short_vehicle_label("PANEL_AV_E_01") == "E01"
    payload = {"vehicles": [{"id": "PANEL_AV_E_01",
                              "front_bumper_x": 300,
                              "front_bumper_y": 300,
                              "angle_degrees": 90, "length_m": 4.8,
                              "width_m": 1.8, "state": "READY"}]}
    svg = render_sumo_style_svg(payload)
    assert ">E01</text>" in svg
    assert "<title>PANEL_AV_E_01</title>" in svg


def test_detail_page_has_no_embedded_simulation_or_embedded_refresh_timer():
    source = (config.SHOWCASE_ROOT / "pages" /
              "component_detail.py").read_text(encoding="utf-8")
    assert "live_simulation_panel" not in source
    assert "LIVE INTERSECTION" not in source
    assert "ui.timer(0.15" not in source


def test_dedicated_live_route_and_read_only_api_are_registered():
    import socialmind_drive_showcase.app as showcase_app
    source = inspect.getsource(showcase_app)
    assert '"/component/right-of-way/live"' in source
    assert '"/api/component2/live-state"' in source
    api_source = inspect.getsource(showcase_app.component2_live_state_api)
    assert "read_live_state" in api_source
    assert "traci" not in api_source.lower()




def test_browser_renderer_has_no_control_calls_or_fixed_vehicle_coordinates():
    source = inspect.getsource(render_sumo_style_svg)
    for forbidden in ("setSpeed", "setAccel", "setDecel", "setMaxSpeed",
                      "changeLane", "moveTo", "moveToXY", "slowDown",
                      "setRoute"):
        assert forbidden not in source
    assert 'vehicle["front_bumper_x"]' in source
    assert 'vehicle["front_bumper_y"]' in source
    assert 'vehicle["angle_degrees"]' in source
    assert 'vehicle["length_m"]' in source and 'vehicle["width_m"]' in source
    assert "PANEL_AV_" not in source


def test_native_gui_remains_optional_not_default():
    cli = (config.COMPONENT2_ROOT / "run_runtime_simulation.py").read_text(
        encoding="utf-8")
    assert '"--gui"' in cli
    assert "--gui" not in config.COMPONENT2.launch_command


def test_sidebar_scenarios_are_unique_qualitative_and_not_held_out():
    scenarios = read_scenario_catalog()
    assert len(scenarios) >= 5
    assert len({item["scenario_id"] for item in scenarios}) == len(scenarios)
    assert all(item["evidence_classification"] ==
               "QUALITATIVE_PRESENTATION_ONLY" for item in scenarios)
    assert all("HELD_OUT" not in item["source_type"] and
               "VALIDATION" not in item["source_type"]
               for item in scenarios)


def test_scenario_sidebar_launch_uses_existing_single_process_guard():
    from socialmind_drive_showcase.pages import component2_live_view
    source = inspect.getsource(component2_live_view._run_protected_scenario)
    assert "LAUNCHER.launch" in source
    assert '("--scenario", scenario_id)' in source
    launcher = ComponentLauncher(config.COMPONENT2)
    launcher.status = "RUNNING"
    assert launcher.launch(("--scenario", "regulatory_cycle")) is False


def test_scenario_ui_has_no_policy_action_or_planner_outcome_controls():
    source = (config.SHOWCASE_ROOT / "pages" /
              "component2_live_view.py").read_text(encoding="utf-8")
    assert "KEEP_CLAIM" not in source and "RELINQUISH_CLAIM" not in source
    assert "ACCEPT_RELINQUISHMENT" not in source
    assert "ready_vehicle_ids =" not in source
    assert "blocked_vehicle_ids =" not in source


def test_missing_image_has_explicit_styled_fallback_contract():
    source = inspect.getsource(image_or_fallback)
    assert "fallback-visual" in source
    assert "if target.is_file()" in source


def test_old_dashboard_is_neither_imported_nor_referenced():
    root = config.SHOWCASE_ROOT
    source = "\n".join(path.read_text(encoding="utf-8")
                       for path in root.rglob("*.py") if "tests" not in path.parts)
    assert "debug_dashboard" not in source
    assert "sumo_debug_overlay" not in source


def test_no_arbitrary_command_input_or_shell_execution():
    source = (config.SHOWCASE_ROOT / "services" / "component_launcher.py").read_text()
    assert "shell=False" in source
    assert "user_input" not in source and "request.args" not in source
    assert "launch_command" in source


def test_duplicate_component_launch_is_prevented():
    launcher = ComponentLauncher(config.COMPONENT2)
    launcher.status = "RUNNING"
    assert launcher.launch() is False


def test_non_live_component_cannot_launch():
    launcher = ComponentLauncher(config.COMPONENTS[0])
    assert launcher.launch() is False
    assert launcher.status == "FAILED"


def test_scientific_and_old_dashboard_baseline_hashes_are_unchanged():
    expected = {
        "debug_dashboard.py": "D363EA829AF524F51307E681B2FD29051AD1C4A22C9E6EAD9383C9EBFBFE71C3",
        "debug_dashboard.html": "21E767A2592AA619550096070A19FA1B5F6AD8CA69BA3B4031BE0BAD0D2DE1AE",
        "sumo_debug_overlay.py": "F5A1E7E810372839FD52F239E1789E2CEFB3FAE912F609C433D27F09431F570A",
    }
    for relative, digest in expected.items():
        assert sha256(config.COMPONENT2_ROOT / relative) == digest


def test_local_only_host_and_predefined_port():
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 8088


def test_home_and_brand_asset_mapping_resolves():
    assert config.HOME_HERO_IMAGE.name == "home_page.png"
    assert config.HOME_HERO_IMAGE.is_file()
    assert config.RESEARCH_VISION_IMAGE.name == "socialmind_hero.jpg"
    assert config.BRAND_LOGO_IMAGE.name == "socialmind_logo.png"
    assert config.BRAND_LOGO_IMAGE.is_file()
    navbar_source = (config.SHOWCASE_ROOT / "ui" / "navbar.py").read_text()
    assert "BRAND_LOGO_IMAGE" in navbar_source


def test_component_asset_extensions_match_real_files():
    expected = {"01": "component_1.jpg", "02": "component_2.png",
                "03": "component_3.png", "04": "component_4.png"}
    assert {item.number: item.image_name for item in config.COMPONENTS} == expected
    assert all((config.SHOWCASE_ROOT / "assets" / "images" /
                item.image_name).is_file() for item in config.COMPONENTS)


def test_research_team_count_and_exact_display_order():
    assert len(config.TEAM_MEMBERS) == 4
    assert [person.name for person in config.TEAM_MEMBERS] == [
        "Avishka Piyumal", "Iresha Nethmini",
        "Dhananji Thakshila", "Imashi Hasinika"]
    assert [person.display_order for person in config.TEAM_MEMBERS] == [1, 2, 3, 4]


def test_supervision_roles_are_separate_from_student_members():
    assert len(config.SUPERVISORS) == 2
    assert [(person.name, person.role) for person in config.SUPERVISORS] == [
        ("Samadhi Rathnayake", "Supervisor"),
        ("Adya Dissanayake", "Co-Supervisor")]
    assert not ({person.name for person in config.TEAM_MEMBERS} &
                {person.name for person in config.SUPERVISORS})


def test_missing_portrait_contract_uses_initials_fallback():
    assert initials_for("Avishka Piyumal") == "AP"
    assert initials_for("Iresha Nethmini") == "IN"
    source = inspect.getsource(portrait_or_initials)
    assert "if target.is_file()" in source
    assert 'return "initials"' in source


def test_existing_component_two_launch_contract_remains_unchanged():
    assert config.COMPONENT2.launch_command == (
        "{python}", "run_runtime_simulation.py", "--web-live",
        "--presentation-delay-ms", "10")


def test_panel_layout_makes_center_dominant_and_camera_is_junction_focused():
    from socialmind_drive_showcase.pages import component2_live_view as live
    css = (config.SHOWCASE_ROOT / "ui" / "theme.py").read_text(encoding="utf-8")
    # The live root sits inside NiceGUI's padded content. Viewport width
    # overflowed it by 16 px in actual Chromium; retain full content width.
    assert "width:100%; max-width:100%; height:100vh; height:100dvh" in css
    assert "grid-template-columns:205px minmax(0,1fr) 250px" in css
    assert ".scenario-sidebar { width:205px; min-width:0; max-width:205px" in css
    assert ".stable-inspector-host { width:250px; min-width:0; max-width:250px" in css
    assert ".live-canvas-column { position:relative; display:flex; width:100%; max-width:none; align-self:stretch" in css
    assert "flex:1 1 auto; gap:8px" in css
    assert ".sumo-live-canvas { display:block; width:100%; height:100%" in css
    assert "preserveAspectRatio=\"xMidYMid meet\"" in render_sumo_style_svg(
        {"vehicles": []})
    assert live.CAMERA_JUNCTION_RADIUS_MULTIPLIER == 3.2
    geometry = authoritative_road_geometry()
    assert geometry["camera_half_extent_m"] == pytest.approx(
        max(math.dist(geometry["center"], point)
            for point in geometry["junction"]) * 3.2)


def test_zoom_changes_display_transform_only_and_reset_is_exact():
    from socialmind_drive_showcase.pages import component2_live_view as live
    payload = {"vehicles": []}
    set_camera_zoom(1.0)
    reset_svg = render_sumo_style_svg(payload)
    set_camera_zoom(1.4)
    zoomed_svg = render_sumo_style_svg(payload)
    assert zoomed_svg != reset_svg and live.CAMERA_ZOOM["factor"] == 1.4
    set_camera_zoom(0.7)
    wide_svg = render_sumo_style_svg(payload)
    assert wide_svg != reset_svg and wide_svg != zoomed_svg
    assert set_camera_zoom(1.0) == 1.0
    assert render_sumo_style_svg(payload) == reset_svg
    source = inspect.getsource(set_camera_zoom)
    assert not any(token in source for token in
                   ("traci", "simulationStep", "spawn", "admission"))


def test_recent_mappo_event_never_replaces_real_permission_color():
    hold = NegotiationVisualHold(1.75)
    vehicle = {"id": "E01", "display_state": "BLOCKED",
               "planner": {"state": "BLOCKED"}}
    authorized = {"scenario_id": "regulatory_cycle", "simulation_time": 10,
                  "mappo_invocation": "AUTHORIZED", "participants": ("E01",),
                  "last_mappo_event": {"timestamp": 10},
                  "vehicles": (vehicle,)}
    during = hold.apply(authorized, now=100.0)
    assert during["vehicles"][0]["display_state"] == "BLOCKED"
    assert during["vehicles"][0]["recent_mappo_event"] is True
    assert during["vehicles"][0]["planner"]["state"] == "BLOCKED"
    after = hold.apply(dict(authorized, mappo_invocation="NOT_REQUIRED"),
                       now=101.76)
    assert after["vehicles"][0]["display_state"] == "BLOCKED"
    assert after["negotiation_visual_hold"] is False


def test_visual_hold_cannot_start_without_real_authorized_event():
    hold = NegotiationVisualHold(1.75)
    payload = {"mappo_invocation": "NOT_REQUIRED", "participants": ("E01",),
               "vehicles": ({"id": "E01", "display_state": "READY"},)}
    result = hold.apply(payload, now=50.0)
    assert result["vehicles"][0]["display_state"] == "READY"
    assert result["negotiation_visual_hold"] is False


def test_completed_event_outline_keeps_body_permission_and_expires():
    import xml.etree.ElementTree as ET
    hold=NegotiationVisualHold(1.75)
    vehicle=dict(id='E01',front_bumper_x=300,front_bumper_y=300,
        angle_degrees=90,length_m=5,width_m=2,display_state='READY')
    payload=dict(run_id='one',scenario_id='regulatory_cycle',simulation_time=10,
        mappo_invocation='NOT_REQUIRED',last_mappo_event=dict(timestamp=10,participants=['E01']),
        vehicles=[vehicle,dict(vehicle,id='N01',display_state='APPROACHING')])
    displayed=hold.apply(payload,now=100)
    root=ET.fromstring(render_sumo_style_svg(displayed))
    cars=[g for g in root.iter() if g.attrib.get('class')=='sumo-car']
    assert cars[0][1].attrib['fill']=='#20c86b'
    outlines=[node for node in root.iter() if node.attrib.get('class')=='mappo-decision-outline']
    assert len(outlines)==1 and 'MAPPO decision received at 10s' in ''.join(outlines[0].itertext())
    assert displayed['vehicles'][1]['display_state']=='APPROACHING'
    expired=hold.apply(displayed,now=102)
    assert all('recent_mappo_event' not in v for v in expired['vehicles'])
    assert 'mappo-decision-outline' not in render_sumo_style_svg(expired)


def test_completed_acknowledgment_cannot_leak_into_a_new_run():
    hold=NegotiationVisualHold(1.75)
    first=dict(run_id='old',scenario_id='regulatory_cycle',simulation_time=23.24,
        mappo_invocation='AUTHORIZED',participants=['E01'],
        last_mappo_event=dict(timestamp=23.24,participants=['E01']),
        vehicles=[dict(id='E01',display_state='BLOCKED')])
    assert hold.apply(first,now=100)['negotiation_visual_hold']
    new=dict(first,run_id='new',simulation_time=0,mappo_invocation='NOT_REQUIRED',last_mappo_event=None)
    result=hold.apply(new,now=100.1)
    assert not result['negotiation_visual_hold']
    assert 'recent_mappo_event' not in result['vehicles'][0]
    assert result['vehicles'][0]['display_state']=='BLOCKED'


@pytest.mark.parametrize("state,color", (
    ("APPROACHING", "#2684ff"), ("NEGOTIATING", "#ffd21f"),
    ("READY", "#20c86b"), ("BLOCKED", "#ef3f45")))
def test_renderer_uses_exact_current_display_state_color(state, color):
    payload = {"vehicles": [{"id": "E01", "front_bumper_x": 300,
                              "front_bumper_y": 300, "angle_degrees": 90,
                              "length_m": 4.8, "width_m": 1.8,
                              "display_state": state}]}
    assert color in render_sumo_style_svg(payload)


def test_api_svg_carries_same_frame_permission_and_motion(monkeypatch):
    import xml.etree.ElementTree as ET
    from socialmind_drive_showcase import app as site
    monkeypatch.setattr(site.LAUNCHER,'status','RUNNING')
    vehicle=dict(id='E01',front_bumper_x=320,front_bumper_y=301.6,
        angle_degrees=270,length_m=5,width_m=1.8,display_state='BLOCKED',
        speed_mps=3.5,motion_state='MOVING',permission_label='ENTRY HELD / APPROACHING STOP',
        entry_permission=dict(authorized=False,timestamp=25),
        negotiation=dict(status='DECISION_EXPIRED',last_event_timestamp=23.24))
    payload=dict(run_id='current-run',simulation_time=25,vehicles=[vehicle],
        mappo_invocation='NOT_REQUIRED')
    monkeypatch.setattr(site,'read_live_state',lambda *a,**kw:dict(available=True,stale=False,payload=payload))
    result=site.component2_live_state_api()
    svg=ET.fromstring(result['rendered_svg'])
    metadata=next(e for e in svg if e.attrib.get('class')=='c2-synchronized-frame')
    frame=json.loads(metadata.text)
    assert frame['simulation_time']==result['payload']['simulation_time']==25
    assert frame['run_id']=='current-run'
    rendered=frame['vehicles'][0]
    assert rendered['entry_permission']==vehicle['entry_permission']
    assert rendered['display_state']=='BLOCKED' and rendered['motion_state']=='MOVING'
    assert rendered['negotiation']['last_event_timestamp']==23.24
    assert '#ef3f45' in result['rendered_svg']


def test_idle_api_never_reads_or_displays_the_previous_run(monkeypatch):
    from socialmind_drive_showcase import app as site
    monkeypatch.setattr(site.LAUNCHER,'status','READY')
    def forbidden(*a,**kw):raise AssertionError('IDLE must not read a previous runtime frame')
    monkeypatch.setattr(site,'read_live_state',forbidden)
    state=site.component2_live_state_api(scenario='congested_four_approach')
    assert state['payload']['schema']=='SHOWCASE_IDLE_PRESENTATION_V1'
    assert state['payload']['run_id'] is None and not state['payload']['vehicles']
    assert state['payload']['scenario_id']=='congested_four_approach'
    assert state['payload']['run_negotiation_summary']=={}
    assert not state['payload']['negotiation_visual_hold']


def test_component_page_only_opens_view_and_never_starts_sumo():
    from socialmind_drive_showcase.pages import component_detail
    page_source = inspect.getsource(component_detail._component2_page)
    assert 'on_click=_open_live_view' in page_source
    assert 'on_click=_launch_demo' not in page_source


def test_selecting_scenario_does_not_launch_and_only_run_click_launches(
        monkeypatch):
    from socialmind_drive_showcase.pages import component2_live_view as live
    calls = []
    fake = SimpleNamespace(running=False, status="READY", error=None,
                           launch=lambda args=(): calls.append(args) or True)
    monkeypatch.setattr(live, "LAUNCHER", fake)
    monkeypatch.setattr(live._scenario_details, "refresh", lambda: None)
    live._select_scenario(SimpleNamespace(value="regulatory_cycle"))
    assert calls == []
    live._run_selected_scenario()
    assert calls == [("--scenario", "regulatory_cycle")]


def test_vehicle_inspector_separates_mappo_planner_control_and_real_motion():
    from socialmind_drive_showcase.pages import component2_live_view as live
    source = inspect.getsource(live._vehicle_inspector)
    assert '"MAPPO SEMANTIC"' in source
    assert '"EGO-LOCAL EXECUTION"' in source
    assert '"DETERMINISTIC CONTROL"' in source
    assert '"ACCELERATION"' in source and '"SUMO"' in source
    assert "MAPPO speed" not in source and "MAPPO acceleration" not in source
    assert "for vehicle in vehicles" in source


def test_vehicle_click_selection_is_display_only_and_exact():
    from socialmind_drive_showcase.pages import component2_live_view as live
    live.select_vehicle("PANEL_AV_E_01")
    assert live.SELECTED_VEHICLE["id"] == "PANEL_AV_E_01"
    svg_source = inspect.getsource(render_sumo_style_svg)
    assert "data-vehicle-id" in svg_source
    assert "selectComponent2Vehicle" in svg_source


def test_viva_inspector_is_persistent_but_has_no_scroll_heavy_controls():
    source = stable_inspector_html() + stable_inspector_script()
    assert 'id="c2-inspector"' in source and "dataset.ready" in source
    assert "AUTO FOLLOW" not in source and "COMPLETED VEHICLES" not in source
    assert "<details" not in source and "c2-viva-cards" in source


def test_viva_vehicle_cards_show_only_simple_causal_fields():
    source = stable_inspector_html() + stable_inspector_script()
    for field in ("Intention:", "Rule:", "MAPPO:", "Speed:"):
        assert field in source
    assert "Planner:" not in source
    assert "GNN" not in source and "LDM" not in source
    assert "INTENTION → RULE / GRAPH → MAPPO IF NEEDED → PLANNER → SUMO MOTION" in source


def test_road_and_cards_share_the_server_display_state_model():
    import socialmind_drive_showcase.app as showcase_app
    from socialmind_drive_showcase.pages import component2_live_view as live
    api_source = inspect.getsource(showcase_app.component2_live_state_api)
    cards = stable_inspector_script()
    assert "apply_live_display_state" in api_source
    assert "v.display_state" in cards
    assert "Date.now" not in cards and "holdUntil" not in cards
    state = {"available": True, "payload": {
        "scenario_id": "regulatory_cycle", "simulation_time": 10,
        "mappo_invocation": "AUTHORIZED", "participants": ("E01",),
        "last_mappo_event": {"timestamp": 10},
        "vehicles": ({"id": "E01", "display_state": "READY",
                      "planner": {"state": "READY"}},)}}
    hold = live.NEGOTIATION_HOLD
    hold._event_identity = None
    displayed = live.apply_live_display_state(state)
    assert displayed["payload"]["vehicles"][0]["display_state"] == "READY"
    assert displayed["payload"]["vehicles"][0]["recent_mappo_event"] is True
    assert displayed["payload"]["vehicles"][0]["planner"]["state"] == "READY"


def test_presentation_history_distinguishes_statuses_and_skips_invalid(tmp_path):
    root = tmp_path / "presentation_runs"; root.mkdir()
    for index, status in enumerate(("COMPLETED", "USER_STOPPED", "FAILED")):
        (root / f"run_{index}.json").write_text(json.dumps({
            "evidence_classification": "QUALITATIVE_PRESENTATION_ONLY",
            "run_status": status}), encoding="utf-8")
    (root / "run_bad.json").write_text("bad", encoding="utf-8")
    assert {item["run_status"] for item in read_presentation_runs(root)} == {
        "COMPLETED", "USER_STOPPED", "FAILED"}


def test_launcher_stop_is_cooperative_owned_and_has_no_broad_kill(tmp_path):
    component = SimpleNamespace(live=True, launch_command=("{python}", "x.py"),
                                working_directory=tmp_path)
    launcher = ComponentLauncher(component)
    launcher.status = "RUNNING"
    launcher._stop_request_path = tmp_path / "owned.request"
    assert launcher.request_stop(grace_seconds=0.1) is True
    assert launcher.status == "STOPPING"
    assert launcher._stop_request_path.read_text() == "STOP_REQUESTED\n"
    source = inspect.getsource(ComponentLauncher)
    assert "taskkill" not in source.lower() and "kill /im" not in source.lower()
    assert "owner.children(recursive=True)" in source


def test_event_timeline_uses_meaningful_published_events_not_simulation_steps():
    from socialmind_drive_showcase.pages import component2_live_view as live
    source = inspect.getsource(live._event_timeline)
    assert "events[-6:]" in source
    assert "simulation_step" not in source


def test_current_mappo_and_persistent_run_history_are_separate():
    from socialmind_drive_showcase.pages import component2_live_view as live
    source = (config.SHOWCASE_ROOT / "pages" /
              "component2_live_view.py").read_text(encoding="utf-8")
    assert "RECENT MAPPO DECISION" in source
    assert "mappo_negotiation_observed" in source
    cards = inspect.getsource(live._negotiation_event_cards)
    for field in ("original_graph", "proposer_actions", "responder_actions",
                  "effective_graph", "ready", "blocked"):
        assert field in cards


def test_freeze_view_only_suppresses_browser_refresh():
    from socialmind_drive_showcase.pages import component2_live_view as live
    source = inspect.getsource(live._refresh_live_unless_frozen)
    assert "live_view_panel.refresh" in source
    for forbidden in ("traci", "simulationStep", "setSpeed", "terminate"):
        assert forbidden not in source


def test_verified_scenario_tags_match_current_real_pipeline_audit():
    scenarios = {item["scenario_id"]: item for item in read_scenario_catalog()}
    assert scenarios["rule_resolved_two"]["verified_tag"] == "BASELINE"
    assert scenarios["four_way_simultaneous"]["verified_tag"] == "STRESS"
    assert scenarios["regulatory_cycle"]["verified_tag"] == "MAPPO NEGOTIATION"
    assert scenarios["mixed_manoeuvres"]["verified_tag"] == "RE-NEGOTIATION"
    assert scenarios["multiple_left_turns"]["verified_tag"] == "LIVENESS"


def test_final_menu_has_exactly_five_scenarios_and_preserves_research_catalogue():
    from socialmind_drive_showcase.pages import component2_live_view as live
    assert live.VIVA_SCENARIO_IDS == (
        "rule_resolved_two", "final_four_agent_stress", "mixed_manoeuvres",
        "congested_four_approach", "final_coordination_failure")
    assert len(live.VIVA_SCENARIOS) == len(live.SELECTABLE_SCENARIOS) == 5
    assert live.DEFAULT_SCENARIO_ID == "rule_resolved_two"
    assert all(key in live.SCENARIO_BY_ID for key in ('default_panel','yield_negotiation_demo','regulatory_cycle','four_way_simultaneous'))
    assert [v['vehicle_count'] for v in live.VIVA_SCENARIOS]==[2,4,4,16,6]
    page_source = inspect.getsource(live.component2_live_view_page)
    assert "RUN HISTORY" not in page_source and "ui.tabs" not in page_source
    assert "live_view_panel()" in page_source


def test_live_ui_has_no_visible_viva_labels():
    source = (config.SHOWCASE_ROOT / "pages" /
              "component2_live_view.py").read_text(encoding="utf-8")
    for visible in ('"VIVA MODE"', '"VIVA SCENARIOS"', '"VIVA DEMO"'):
        assert visible not in source
    assert '"PRESENTATION MODE"' not in source


def test_component_live_navigation_is_same_tab_and_never_starts_browser():
    from socialmind_drive_showcase.pages import component_detail, component2_live_view
    open_source = inspect.getsource(component_detail._open_live_view)
    assert 'ui.navigate.to("/component/right-of-way/live")' in open_source
    assert "open_showcase" not in open_source and "window.open" not in open_source
    detail_source = inspect.getsource(component_detail._component2_page)
    assert detail_source.count("on_click=_open_live_view") == 1
    assert "LAUNCHER.launch" not in open_source
    back_source = inspect.getsource(component2_live_view.component2_live_view_page)
    assert 'ui.navigate.to(' in back_source
    assert '"/component/right-of-way"' in back_source


def test_camera_toolbar_has_no_fullscreen_workaround():
    from socialmind_drive_showcase.pages import component2_live_view as live
    source = inspect.getsource(live._camera_controls)
    assert '"Full Screen"' not in source and "requestFullscreen" not in source
    assert '"Zoom Out"' in source and '"Reset"' in source and '"Zoom In"' in source
    assert not any(token in source for token in
                   ("traci", "simulationStep", "setSpeed"))


def test_desktop_launcher_uses_one_native_resizable_window(monkeypatch):
    from socialmind_drive_showcase import app as showcase_app
    calls = []
    monkeypatch.setattr(showcase_app, "build_app", lambda: calls.append("build"))
    monkeypatch.setattr(showcase_app.ui, "run", lambda **kwargs: calls.append(kwargs))
    showcase_app.run_showcase(port=8099, native=True)
    assert calls[0] == "build"
    assert calls[1] == {
        "host": "127.0.0.1", "port": 8099,
        "title": "SOCIALMIND DRIVE", "favicon": "🚘",
        "native": True, "window_size": (1400, 900),
        "fullscreen": False, "frameless": False,
        "reload": False, "show": False,
    }


def test_application_has_no_external_browser_launch_path():
    from socialmind_drive_showcase import app as showcase_app
    source = inspect.getsource(showcase_app)
    assert "open_showcase" not in source
    assert "webbrowser" not in source
    assert "chrome" not in source.lower()
    assert "threading.Timer" not in source


def test_server_only_mode_uses_same_backend_without_native_window(monkeypatch):
    from socialmind_drive_showcase import app as showcase_app
    calls = []
    monkeypatch.setattr(showcase_app, "build_app", lambda: None)
    monkeypatch.setattr(showcase_app.ui, "run", lambda **kwargs: calls.append(kwargs))
    showcase_app.run_showcase(port=8088, native=False)
    assert calls[0]["native"] is False
    assert calls[0]["window_size"] is None
    assert calls[0]["show"] is False


def test_component_two_explainer_uses_stable_structured_evidence():
    evidence = load_research_evidence()
    assert evidence["validation"] == {
        "E5": 15817.906666666666,
        "E10": 16579.066666666666,
        "E15": 16942.56,
    }
    assert evidence["selected"] == "E5"
    assert evidence["held_out_used_for_selection"] is False
    assert evidence["globally_optimal_claim"] is False
    assert evidence["runtime"]["engine"] == "onnxruntime"
    assert evidence["runtime"]["execution_provider"] == "CPUExecutionProvider"
    assert evidence["runtime"]["tensorflow_required"] is False
    assert evidence["verification_passed"] is True
    assert evidence["models_retrained"] is False


def test_component_two_decision_flow_and_implementation_map_are_complete():
    assert len(DECISION_STEPS) == 10
    assert [item[1] for item in DECISION_STEPS] == [
        "OBSERVE", "REMEMBER", "PREDICT", "FIND PHYSICAL CONFLICTS",
        "CHECK TIMING / REACHABILITY", "APPLY TRAFFIC RULES",
        "BUILD PRECEDENCE GRAPH", "NEGOTIATE IF NEEDED", "PLAN", "EXECUTE",
    ]
    locations = {(item[0], item[1], item[2]) for item in IMPLEMENTATION_MAP}
    assert ("Physical controller", "negotiation_execution/controller.py",
            "build_sumo_native_speed_constraint()") in locations
    assert ("Execution planner", "negotiation_execution/planner.py",
            "ConflictZoneExecutionPlanner") in locations


def test_component_two_explainer_preserves_scientific_boundaries():
    from socialmind_drive_showcase.pages import component2_explainer
    source = inspect.getsource(component2_explainer)
    assert "NO TARGET ROUTE TRUTH" in source
    assert "does not directly output speed, acceleration, braking or steering" in source
    assert "A → B means A YIELDS TO B" in source
    assert "NO NUMERIC PRIORITY SCORE IS USED" in source
    assert "MAPPO decides semantic claims; the planner decides permission" in source
    assert "latest_runtime_simulation" not in inspect.getsource(load_research_evidence)


def test_component_two_detail_orders_explainer_after_system_overview():
    from socialmind_drive_showcase.pages import component_detail
    source = inspect.getsource(component_detail._component2_page)
    assert source.index("SYSTEM OVERVIEW") < source.index(
        "component2_explanation_sections()")
    assert "ACTOR EXECUTION" in source
    assert "PHYSICAL SAFETY" in source
    assert 'ui.navigate.to("/component/right-of-way/live")' in inspect.getsource(
        component_detail._open_live_view)


def test_panel_result_status_never_treats_partial_run_as_scientific_failure():
    partial = presentation_run_status({"run_status": "USER_STOPPED"})
    assert partial == {
        "status": "USER_STOPPED",
        "finished": False,
        "title": "PARTIAL PRESENTATION RUN — USER_STOPPED",
    }
    finished = presentation_run_status({"run_status": "FINISHED"})
    assert finished["finished"] is True
    assert finished["title"] == "SCENARIO COMPLETE"


def test_component_two_explainer_css_is_responsive_and_scoped():
    from socialmind_drive_showcase.ui import theme
    assert ".c2-decision-flow" in theme.CSS
    assert ".c2-evidence-layout" in theme.CSS
    assert ".c2-partial-run-banner" in theme.CSS
    assert "@media(max-width:700px)" in theme.CSS
