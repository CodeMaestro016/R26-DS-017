"""Focused, read-only browser viewer for the real Component 2 SUMO run."""

from dataclasses import dataclass
import html
from functools import lru_cache
import json
import math
import re
import time
import xml.etree.ElementTree as ET

from nicegui import ui
from socialmind_drive_showcase.services.client_lifecycle import client_refreshable, page_timer, ClientLocalState

from socialmind_drive_showcase.config import (
    COMPONENT2_LIVE_STATE_PATH, COMPONENT2_ROOT)
from socialmind_drive_showcase.services.live_state_reader import (
    read_live_state, runtime_status_label, discharge_label)
from socialmind_drive_showcase.services.scenario_reader import read_scenario_catalog, read_final_demonstrations
from socialmind_drive_showcase.ui.theme import apply_theme
from socialmind_drive_showcase.pages.component_detail import LAUNCHER
from socialmind_drive_showcase.pages.component2_inspector import (
    stable_inspector_html, stable_inspector_script)


NETWORK_PATH = COMPONENT2_ROOT / "networks" / "intersection.net.xml"
SUMO_DEFAULT_LANE_WIDTH_METERS = 3.2
CAMERA_JUNCTION_RADIUS_MULTIPLIER = 3.2
CAMERA_ZOOM_MIN = 0.55
CAMERA_ZOOM_MAX = 1.80
CAMERA_ZOOM_STEP = 0.20
CAMERA_ZOOM = ClientLocalState(factor=1.0)
NEGOTIATION_VISUAL_HOLD_SECONDS = 1.75
SCENARIO_CATALOG = read_scenario_catalog()
SCENARIO_BY_ID = {item["scenario_id"]: item for item in SCENARIO_CATALOG}
VIVA_SCENARIOS = read_final_demonstrations()
VIVA_SCENARIO_IDS = tuple(item['scenario_id'] for item in VIVA_SCENARIOS)
SELECTABLE_SCENARIOS = VIVA_SCENARIOS
VIVA_LABELS = {
    "default_panel": "Default Rolling Traffic Presentation",
    "congested_four_approach": "5. Congested Four-Approach Queues (16 vehicles)",
    "yield_negotiation_demo": "MAIN DEMO — YIELD + NEGOTIATION",
    "rule_resolved_two": "1. Rule-Resolved Conflict",
    "four_way_simultaneous": "2. Four-Way Arrival",
    "regulatory_cycle": "3. Regulatory Cycle",
    "mixed_manoeuvres": "4. Mixed Manoeuvres"}
VIVA_PURPOSES = {
    "default_panel": "Existing rolling traffic across all 12 legal movements. Qualitative presentation only.",
    "congested_four_approach": "16 active traffic vehicles with up to four queue-head negotiators; ego-local execution. Qualitative presentation only.",
    "yield_negotiation_demo": "Rules resolve a simple yield first; a second wave then requires real MAPPO negotiation.",
    "rule_resolved_two": "Rules resolve this two-vehicle conflict without MAPPO.",
    "four_way_simultaneous": "Four AVs arrive together in a multi-relationship stress case.",
    "regulatory_cycle": "An unresolved regulatory cycle requires real semantic negotiation.",
    "mixed_manoeuvres": "Left, straight and right movements trigger conflict re-evaluation."}
VIVA_LABELS.update({item['scenario_id']:item['final_label'] for item in VIVA_SCENARIOS})
VIVA_PURPOSES.update({item['scenario_id']:item['demonstrates'] for item in VIVA_SCENARIOS})
FINAL_DEMONSTRATION_BY_ID = {item['scenario_id']:item for item in VIVA_SCENARIOS}
DEFAULT_SCENARIO_ID = "rule_resolved_two"
SELECTED_SCENARIO = ClientLocalState(id=DEFAULT_SCENARIO_ID)
SELECTED_VEHICLE = ClientLocalState(id=None)
DISPLAY_FROZEN = ClientLocalState(value=False)
COMPARISON_OPEN = ClientLocalState(value=False)
REPLAY_STATE = ClientLocalState(mode='default',active=False,index=None,started=None,origin=0.)


class NegotiationVisualHold:
    """Wall-clock display overlay; never writes to runtime or simulation."""

    def __init__(self, duration_seconds=NEGOTIATION_VISUAL_HOLD_SECONDS):
        self.duration_seconds = float(duration_seconds)
        self._event_identity = None
        self._participant_ids = frozenset()
        self._expires_at = 0.0
        self._run_identity = None

    def apply(self, payload, *, now=None):
        current_time = time.monotonic() if now is None else float(now)
        run_identity = (payload.get('run_id'), payload.get('scenario_id'))
        if run_identity != self._run_identity:
            self._run_identity = run_identity
            self._event_identity = None
            self._participant_ids = frozenset()
            self._expires_at = 0.0
        if payload.get("last_mappo_event") or payload.get("mappo_invocation") == "AUTHORIZED":
            event = payload.get("last_mappo_event") or {}
            identity = (payload.get("run_id"), payload.get("scenario_id"),
                        event.get("timestamp", payload.get("simulation_time")),
                        tuple(event.get("participants", payload.get("participants", ()))))
            if identity != self._event_identity:
                self._event_identity = identity
                self._participant_ids = frozenset(event.get("participants", payload.get("participants", ())))
                self._expires_at = current_time + self.duration_seconds
        active = bool(self._participant_ids and current_time < self._expires_at)
        result = dict(payload)
        result['vehicles'] = tuple({k:value for k,value in v.items()
            if k not in {'recent_mappo_event','recent_mappo_timestamp'}}
            for v in payload.get('vehicles', ()))
        result["negotiation_visual_hold"] = active
        if not active:
            return result
        result["vehicles"] = tuple(
            dict(vehicle, recent_mappo_event=True,
                 recent_mappo_timestamp=self._event_identity[2])
            if vehicle.get("id") in self._participant_ids else dict(vehicle)
            for vehicle in payload.get("vehicles", ()))
        return result


NEGOTIATION_HOLD = NegotiationVisualHold()


def apply_live_display_state(state):
    """Apply the one shared road/card presentation state to an API frame."""
    result = dict(state)
    if state.get("available") and state.get("payload") is not None:
        result["payload"] = NEGOTIATION_HOLD.apply(state["payload"])
    return result


def idle_display_state(scenario_id=DEFAULT_SCENARIO_ID):
    """Explicit UI idle frame; never reuse a previous scientific runtime."""
    scenario_id=scenario_id if scenario_id in SCENARIO_BY_ID else DEFAULT_SCENARIO_ID
    return apply_live_display_state(dict(available=True,stale=False,message='',payload=dict(
        schema='SHOWCASE_IDLE_PRESENTATION_V1',display_only=True,run_id=None,running=False,
        simulation_time=0.0,status='NO SCENARIO RUNNING',scenario_id=scenario_id,vehicles=(),
        completed=0,scheduled=SCENARIO_BY_ID[scenario_id]['vehicle_count'],participants=(),
        ready=(),blocked=(),effective_graph=(),events=(),last_mappo_event=None,
        run_metrics={},run_negotiation_summary={},mappo_invocation='NOT_REQUIRED')))


@dataclass(frozen=True)
class WorldTransform:
    scale: float
    offset_x: float
    offset_y: float
    min_x: float
    max_y: float

    def point(self, x, y):
        return (self.offset_x + (float(x) - self.min_x) * self.scale,
                self.offset_y + (self.max_y - float(y)) * self.scale)


def build_world_transform(width, height, world_bounds):
    min_x, min_y, max_x, max_y = map(float, world_bounds)
    world_width, world_height = max_x - min_x, max_y - min_y
    if world_width <= 0 or world_height <= 0:
        raise ValueError("LIVE_VIEW_WORLD_BOUNDS_INVALID")
    scale = min(float(width) / world_width, float(height) / world_height)
    drawn_width, drawn_height = world_width * scale, world_height * scale
    return WorldTransform(scale, (float(width) - drawn_width) / 2.0,
                          (float(height) - drawn_height) / 2.0,
                          min_x, max_y)


def vehicle_geometric_center(front_x, front_y, angle_degrees, length_m):
    radians = math.radians(float(angle_degrees))
    return (float(front_x) - 0.5 * float(length_m) * math.sin(radians),
            float(front_y) - 0.5 * float(length_m) * math.cos(radians))


def svg_vehicle_rotation(angle_degrees):
    """Convert SUMO clockwise-from-north to SVG clockwise-from-east."""
    return (float(angle_degrees) - 90.0) % 360.0


def short_vehicle_label(vehicle_id):
    match = re.fullmatch(r"PANEL_AV_([NESW])_(\d+)", str(vehicle_id))
    return f"{match.group(1)}{match.group(2)}" if match else str(vehicle_id)


@lru_cache(maxsize=1)
def authoritative_road_geometry():
    root = ET.parse(NETWORK_PATH).getroot()
    location = root.find("location")
    bounds = tuple(float(value) for value in
                   location.attrib["convBoundary"].split(","))
    lanes = []
    for lane in root.findall("./edge/lane"):
        if lane.attrib["id"].startswith(":"):
            continue
        lanes.append({
            "id": lane.attrib["id"],
            "width_m": float(lane.attrib.get(
                "width", SUMO_DEFAULT_LANE_WIDTH_METERS)),
            "shape": tuple(
                tuple(float(value) for value in point.split(","))
                for point in lane.attrib["shape"].split())})
    junction = root.find("./junction[@id='center']")
    junction_shape = tuple(
        tuple(float(value) for value in point.split(","))
        for point in junction.attrib["shape"].split())
    center = (sum(point[0] for point in junction_shape) / len(junction_shape),
              sum(point[1] for point in junction_shape) / len(junction_shape))
    junction_radius = max(math.dist(center, point) for point in junction_shape)
    return {"network_bounds": bounds, "lanes": tuple(lanes),
            "junction": junction_shape, "center": center,
            "camera_half_extent_m":
                junction_radius * CAMERA_JUNCTION_RADIUS_MULTIPLIER}


def render_sumo_style_svg(payload, *, width=1100, height=700,
                          zoom_factor=None):
    geometry = authoritative_road_geometry()
    center_x, center_y = geometry["center"]
    zoom = CAMERA_ZOOM["factor"] if zoom_factor is None else float(zoom_factor)
    half_extent = geometry["camera_half_extent_m"] / zoom
    if payload.get("scenario_id") == "congested_four_approach":
        half_extent *= 1.5  # Keep queued followers visible; display geometry only.
    camera_bounds = (center_x - half_extent, center_y - half_extent,
                     center_x + half_extent, center_y + half_extent)
    transform = build_world_transform(width, height, camera_bounds)

    lane_shapes = []
    for lane in geometry["lanes"]:
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in
                          (transform.point(*pair) for pair in lane["shape"]))
        lane_width = lane["width_m"] * transform.scale
        lane_shapes.append((points, lane_width))
    boundaries = "".join(
        f'<polyline points="{points}" stroke-width="{lane_width + 2:.2f}"/>'
        for points, lane_width in lane_shapes)
    asphalt = "".join(
        f'<polyline points="{points}" stroke-width="{lane_width:.2f}"/>'
        for points, lane_width in lane_shapes)
    junction_points = " ".join(
        f"{x:.2f},{y:.2f}" for x, y in
        (transform.point(*pair) for pair in geometry["junction"]))

    colors = {"APPROACHING": "#2684ff", "NEGOTIATING": "#ffd21f",
              "READY": "#20c86b", "BLOCKED": "#ef3f45",
              "CLEARED": "#9aa3ad"}
    vehicles = []
    for vehicle in payload.get("vehicles", ()):
        front_x = float(vehicle["front_bumper_x"])
        front_y = float(vehicle["front_bumper_y"])
        angle = float(vehicle["angle_degrees"])
        length_m = float(vehicle["length_m"])
        width_m = float(vehicle["width_m"])
        center = vehicle_geometric_center(
            front_x, front_y, angle, length_m)
        x, y = transform.point(*center)
        body_length = length_m * transform.scale
        body_width = width_m * transform.scale
        rotation = svg_vehicle_rotation(angle)
        color = colors.get(vehicle.get("display_state"), "#9aa3ad")
        full_id = html.escape(str(vehicle["id"]))
        label = html.escape(short_vehicle_label(vehicle["id"]))
        label_x, label_y = x + body_width / 2.0 + 4.0, y - 4.0
        acknowledgement = (
            f'<rect class="mappo-decision-outline" x="{-body_length/2-3:.2f}" '
            f'y="{-body_width/2-3:.2f}" width="{body_length+6:.2f}" '
            f'height="{body_width+6:.2f}" rx="4" fill="none" stroke="#ffd21f" stroke-width="3">'
            f'<title>MAPPO decision received at {vehicle.get("recent_mappo_timestamp")}s</title></rect>'
            if vehicle.get('recent_mappo_event') else '')
        vehicles.append(
            f'<g class="sumo-car" data-vehicle-id="{full_id}" '
            f'onclick="window.selectComponent2Vehicle &amp;&amp; '
            f'window.selectComponent2Vehicle(\'{full_id}\')" '
            f'transform="translate({x:.2f} {y:.2f}) '
            f'rotate({rotation:.2f})"><title>{full_id}</title>'
            f'<rect x="{-body_length / 2:.2f}" y="{-body_width / 2:.2f}" '
            f'width="{body_length:.2f}" height="{body_width:.2f}" rx="2" '
            f'fill="{color}" stroke="#ffffff" stroke-width="1"/>'
            + acknowledgement +
            f'<path d="M{body_length * .18:.2f},{-body_width * .35:.2f} '
            f'L{body_length * .38:.2f},0 L{body_length * .18:.2f},'
            f'{body_width * .35:.2f} Z" fill="#d9f2ff" opacity=".9"/>'
            f'<rect x="{-body_length * .32:.2f}" y="{-body_width * .32:.2f}" '
            f'width="{body_length * .28:.2f}" height="{body_width * .64:.2f}" '
            f'rx="1" fill="#142a38" opacity=".72"/>'
            f'<circle cx="{body_length * .42:.2f}" cy="{-body_width * .3:.2f}" r="1" fill="#fff5a8"/>'
            f'<circle cx="{body_length * .42:.2f}" cy="{body_width * .3:.2f}" r="1" fill="#fff5a8"/></g>'
            f'<g class="sumo-car-label"><title>{full_id}</title>'
            f'<rect x="{label_x - 2:.2f}" y="{label_y - 9:.2f}" '
            f'width="{len(label) * 6 + 4}" height="11" rx="2"/>'
            f'<text x="{label_x:.2f}" y="{label_y:.2f}">{label}</text></g>')
    frame_fields = ('id', 'display_state', 'permission_label', 'entry_permission',
                    'movement','collision_involved',
                    'negotiation', 'speed_mps', 'motion_state', 'local_intention_predictions',
                    'display_stage', 'recent_mappo_event', 'recent_mappo_timestamp',
                    'intersection_rear_cleared', 'presentation_visible')
    frame = {'simulation_time': payload.get('simulation_time'), 'run_id': payload.get('run_id'),
             'replay_mode':payload.get('replay_mode',False),
             'browser_owned_frame':payload.get('browser_owned_frame',False),
             'replay_events':payload.get('replay_events',[]),
             'scenario_id':payload.get('scenario_id'),
             'vehicles': [{k: v[k] for k in frame_fields if k in v}
                          for v in payload.get('vehicles', ())]}
    return (f'<svg class="sumo-live-canvas" data-zoom="{zoom}" '
            f'data-scenario="{html.escape(str(payload.get("scenario_id", "")))}" viewBox="0 0 {width} {height}" '
            'preserveAspectRatio="xMidYMid meet" '
            'role="img" aria-label="Live top-down SUMO intersection">'
            '<metadata class="c2-synchronized-frame">' + html.escape(json.dumps(frame)) + '</metadata>'
            '<rect width="100%" height="100%" fill="#57964c"/>'
            '<g class="sumo-road-boundaries">' + boundaries + '</g>'
            '<g class="sumo-road-asphalt">' + asphalt + '</g>'
            f'<polygon class="sumo-junction" points="{junction_points}"/>'
            '<g class="sumo-live-vehicles">' + "".join(vehicles) + '</g></svg>')


def set_camera_zoom(factor):
    """Set display scale only; SUMO state and coordinates are untouched."""
    CAMERA_ZOOM["factor"] = max(
        CAMERA_ZOOM_MIN, min(CAMERA_ZOOM_MAX, float(factor)))
    return CAMERA_ZOOM["factor"]


def _zoom_in():
    set_camera_zoom(CAMERA_ZOOM["factor"] + CAMERA_ZOOM_STEP)
    live_view_panel.refresh()


def _zoom_out():
    set_camera_zoom(CAMERA_ZOOM["factor"] - CAMERA_ZOOM_STEP)
    live_view_panel.refresh()


def _reset_zoom():
    set_camera_zoom(1.0)
    live_view_panel.refresh()


def _camera_controls():
    with ui.row().classes("camera-controls items-center"):
        ui.button("Zoom Out", icon="remove", on_click=_zoom_out).props(
            "outline dense no-caps")
        ui.button("Reset", icon="center_focus_strong", on_click=_reset_zoom).props(
            "flat dense no-caps")
        ui.button("Zoom In", icon="add", on_click=_zoom_in).props(
            "outline dense no-caps")
        ui.label(f'{CAMERA_ZOOM["factor"]:.1f}×').classes("camera-zoom-value")


@client_refreshable
def live_view_panel():
    if REPLAY_STATE['mode']=='replay' and REPLAY_STATE['index'] is not None:
        _main_canvas_replay_panel()
        return
    state = (idle_display_state(SELECTED_SCENARIO['id']) if LAUNCHER.status=='READY' or REPLAY_STATE['mode']=='prepared' else
        apply_live_display_state(read_live_state(COMPONENT2_LIVE_STATE_PATH,
            started_after=LAUNCHER.started_at)))
    if not state["available"] and LAUNCHER.status != "READY":
        with ui.column().classes("live-view-empty items-center justify-center"):
            ui.icon("traffic", size="64px")
            ui.label(state["message"]).classes("text-xl")
            ui.label(LAUNCHER.status).classes("live-view-status")
            if LAUNCHER.error:
                ui.label(LAUNCHER.error).classes("text-red-5")
        return
    payload = dict(state.get("payload", {}))
    if REPLAY_STATE['mode']=='prepared':payload['browser_owned_frame']=True
    run_summary = payload.get("run_negotiation_summary", {})
    scenario = SCENARIO_BY_ID.get(payload.get("scenario_id"), {})
    with ui.row().classes("viva-live-header w-full items-center justify-between"):
        ui.label(f'{scenario.get("display_name", "LIVE SIMULATION")} · '
                 f'{payload.get("simulation_time", 0):.1f} s').classes(
                     "live-view-time")
        ui.label(runtime_status_label(LAUNCHER.status, state)).classes("live-view-status")
    with ui.column().classes("live-canvas-column w-full grow min-w-0"):
        metrics = payload.get("run_metrics", {}) if LAUNCHER.status != "READY" else {}
        with ui.row().classes("gap-3 flex-wrap"):
            ui.label(f'Active vehicles: {metrics.get("current_active_vehicle_count", "N/A")}')
            ui.label(f'Intersection display: {len(payload.get("vehicles", ()))}')
            ui.label(f'Moving vehicles: {metrics.get("current_moving_vehicle_count", "N/A")}')
            depths = metrics.get("per_approach_queue_depth", {})
            ui.label("Queue depth: " + " / ".join(f'{a}: {depths.get(a, "N/A")}' for a in "NESW"))
            participant_count = len(payload["participants"]) if "participants" in payload else "N/A"
            ui.label(f'Current negotiation participants: {participant_count}')
            ui.label(f'Max simultaneous active vehicles: {metrics.get("maximum_simultaneous_active_vehicles", "N/A")}')
            ui.label(f'Collisions: {metrics.get("collisions", "N/A")}')
            ui.label("Execution: Ego-local decentralized" if metrics.get(
                "decentralized_execution") else "Execution: awaiting runtime evidence")
        _camera_controls()
        ui.html(render_sumo_style_svg(payload), sanitize=False).classes(
            "sumo-canvas-host w-full grow min-h-0")
    with ui.row().classes("live-view-legend w-full justify-center gap-6"):
        for color, label in (("blue", "Approaching"),
                             ("yellow", "Negotiating (inference pending)"),
                             ("green", "Ready / Go"),
                             ("red", "Entry held (may approach stop)")):
            ui.label(f"● {label}").classes(f"text-{color}-5")
        ui.label('Yellow outline: MAPPO decision received (timestamped, temporary)').classes('text-yellow-5')
    _current_event_banner(payload)
    if run_summary.get("mappo_negotiation_observed"):
        ui.label("✓ MAPPO NEGOTIATION OBSERVED IN THIS RUN").classes("mappo-observed-badge")
        ui.button("Show Negotiation Result", on_click=lambda:
                  _show_negotiation_dialog(payload.get("last_mappo_event"))).props(
                      "flat dense no-caps")
    if not payload.get("running") and LAUNCHER.status == "FINISHED":
        _simple_final_result(payload, scenario)
    if state.get("stale"):
        ui.label(state["message"]).classes("text-amber-4")


def _main_canvas_replay_panel():
    from socialmind_drive_showcase.services.main_canvas_replay import payload as replay_payload,LABEL
    payload=replay_payload(REPLAY_STATE)
    ui.label(LABEL).classes('text-amber-4 font-bold main-replay-label')
    ui.label(f"Recorded time {payload['simulation_time']:.2f} s · Spawned {payload['spawned']}/{payload['scheduled']} · Completed {payload['completed']} before cutoff · MAPPO: DISABLED · Collisions: {payload['collision_count']}").classes('live-view-time')
    ui.label('Coordination and specified protective interventions omitted in the isolated recording. This is not a trained MAPPO failure.').classes('text-xs')
    ui.label(payload['status']).classes('live-view-status')
    event_text='Recorded SUMO trajectories · fixed standard camera · waiting for the recorded event'
    if payload['collisions']:
        event=payload['replay_events'][0]
        event_text=f"ACTUAL SUMO COLLISION DETECTED · {event['collider']} / {event['victim']} · SUMO {event['sumo_event_time']:.2f} s · snapshot {event['traci_detection_time']:.2f} s · count {payload['collision_count']}"
    ui.label(event_text).classes('current-event-banner main-replay-event'+(' main-replay-collision' if payload['collisions'] else ''))
    geometry=authoritative_road_geometry();cx,cy=geometry['center']
    extent=geometry['camera_half_extent_m']
    svg=render_sumo_style_svg(payload,zoom_factor=1.0)
    for vehicle in payload['vehicles']:
        if vehicle['collision_involved']:
            svg=svg.replace(f'class="sumo-car" data-vehicle-id="{vehicle["id"]}"',f'class="sumo-car collision-involved" data-vehicle-id="{vehicle["id"]}"')
    transform=build_world_transform(1100,700,(cx-extent,cy-extent,cx+extent,cy+extent))
    for event in payload['collisions']:
        x,y=transform.point(*event['position'])
        svg=svg.replace('</svg>',f'<circle class="recorded-collision-marker" cx="{x}" cy="{y}" r="18" stroke="#ff4b4b" stroke-width="2" fill="none"/></svg>')
    ui.html(svg,sanitize=False).classes('sumo-canvas-host main-replay-canvas w-full grow min-h-0')


def _current_event_banner(payload):
    status = payload.get("status", "NO SCENARIO RUNNING")
    invocation = payload.get("mappo_invocation", "NOT_REQUIRED")
    progress = payload.get("traffic_progress", {})
    if progress.get("status") == "PERSISTENT_BLOCKAGE":
        title = "PERSISTENT TRAFFIC BLOCKAGE"
        message = (f'{progress.get("blocked_seconds", 0):.1f}s — '
                   f'{progress.get("reason", "UNRESOLVED").replace("_", " ")}')
    elif payload.get("negotiation_visual_hold"):
        title, message = "RECENT MAPPO DECISION", "RECORDED EVENT — CURRENT PERMISSIONS UNCHANGED"
        event_time = (payload.get("last_mappo_event") or {}).get("timestamp")
        if event_time is not None:
            message += f" · decision received at {event_time:.2f} s"
    elif invocation == "AUTHORIZED":
        title, message = "NEGOTIATION COMPLETE", "EGO-LOCAL EXECUTION — READY / BLOCKED"
    elif status == "REGULATORY_ORDER_RESOLVED":
        edge = next(iter(payload.get("original_graph", ())), None)
        message = (f'{short_vehicle_label(edge[0])} YIELDS TO '
                   f'{short_vehicle_label(edge[1])}' if edge else
                   "REAL PRECEDENCE ORDER RESOLVED")
        title = "TRAFFIC RULE APPLIED"
    elif invocation == "BLOCKED":
        title, message = "MAPPO BLOCKED", status.replace("_", " ")
    elif payload.get("ready") or payload.get("blocked"):
        title, message = "EGO-LOCAL EXECUTION — READY / BLOCKED", "CURRENT EXECUTION PERMISSION"
    else:
        title, message = status.replace("_", " "), "MAPPO NOT REQUIRED"
    with ui.row().classes("current-event-banner w-full items-center justify-between"):
        ui.label(f"{title} — {message}").classes("current-event-title")
        ui.label("READY: " + ", ".join(map(short_vehicle_label,
            payload.get("ready", ())))).classes("current-planner")
        ui.label("BLOCKED: " + ", ".join(map(short_vehicle_label,
            payload.get("blocked", ())))).classes("current-planner")


def _show_negotiation_dialog(event):
    if not event:
        return
    with ui.dialog() as dialog, ui.card().classes("negotiation-result-dialog"):
        ui.label("MAPPO NEGOTIATION RESULT").classes("text-xl font-bold")
        ui.label(f'{event.get("event", "NEGOTIATION")} · '
                 f'{event.get("timestamp", 0):.2f} s')
        ui.label("Original: " + _action_text(event.get("original_graph", ())))
        ui.label("Actions: " + _action_text(event.get("proposer_actions", ())))
        ui.label("Responses: " + _action_text(event.get("responder_actions", ())))
        ui.label("Result graph: " + _action_text(event.get("effective_graph", ())))
        ui.label("READY: " + _action_text(event.get("ready", ())))
        ui.label("BLOCKED: " + _action_text(event.get("blocked", ())))
        ui.button("Close", on_click=dialog.close).props("flat")
    dialog.open()


def _simple_final_result(payload, scenario):
    metrics = payload.get("run_metrics", {})
    summary = payload.get("run_negotiation_summary", {})
    with ui.card().classes("simple-final-result"):
        ui.label(discharge_label(payload)).classes("text-xl font-bold")
        ui.label(scenario.get("display_name", payload.get("scenario_id")))
        ui.label(f'Vehicles: {payload.get("completed", 0)} / '
                 f'{payload.get("scheduled", 0)} completed')
        ui.label("MAPPO used: " + ("YES" if summary.get(
            "mappo_negotiation_observed") else "NO"))
        ui.label(f'Negotiation events: {summary.get("mappo_authorized_events", 0)}')
        ui.label(f'Direct MAPPO execution outcomes: {metrics.get("mappo_outcomes_accepted", 0)} · '
                 f'Safety fallback epochs: {metrics.get("fallback_activations", 0)}')
        ui.label(f'Collisions: {metrics.get("collisions", 0)}')
        ui.label(f'Blocked-zone violations: {metrics.get("blocked_zone_violations", 0)}')
        if summary.get("mappo_negotiation_observed"):
            ui.label("MAPPO negotiation observed; completion and safety are reported separately.").classes(
                "final-main-result")
            ui.button("View Negotiation Details", on_click=lambda:
                      _show_negotiation_dialog(payload.get("last_mappo_event"))).props(
                          "flat dense no-caps")
        else:
            ui.label("Main result: Traffic rules supplied local execution obligations").classes(
                "final-main-result")


def component2_live_view_page():
    apply_theme()
    ui.add_body_html(stable_inspector_script())
    with ui.column().classes("dedicated-live-view w-full min-h-screen"):
        with ui.row().classes("live-view-header w-full items-center justify-between"):
            ui.label("SOCIALMIND DRIVE — LIVE SUMO SIMULATION").classes("text-xl font-bold main-simulation-title")
            with ui.row().classes("items-center gap-2"):
                ui.button("Technical Details", icon="data_object",
                          on_click=_show_technical_details).props(
                              "outline dense no-caps")
                ui.button("Back to Component 2", on_click=lambda: ui.navigate.to(
                    "/component/right-of-way")).props("flat no-caps")
        with ui.row().classes("live-view-workspace w-full items-stretch no-wrap"):
            _scenario_sidebar()
            with ui.column().classes("live-view-main grow min-w-0"):
                live_view_panel()
            ui.html(stable_inspector_html(), sanitize=False).classes(
                "stable-inspector-host")
        page_timer(0.15, live_view_panel.refresh)


def _show_technical_details():
    """Expose retained runtime evidence without crowding the VIVA surface."""
    state = read_live_state(COMPONENT2_LIVE_STATE_PATH)
    payload = state.get("payload", {}) if state.get("available") else {}
    with ui.dialog() as dialog, ui.card().classes("technical-details-dialog"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("TECHNICAL DETAILS").classes("text-xl font-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round")
        ui.label("Read-only live publisher output; it never feeds back into SUMO.")
        ui.code(json.dumps(payload, indent=2, default=str), language="json").classes(
            "technical-json w-full")
    dialog.open()


def _refresh_live_unless_frozen():
    """Technical-view helper; it has no connection to simulation control."""
    if not DISPLAY_FROZEN["value"]:
        live_view_panel.refresh()


def _select_scenario(event):
    from socialmind_drive_showcase.services.main_canvas_replay import stop
    stop(REPLAY_STATE)
    SELECTED_SCENARIO["id"] = event.value
    _scenario_details.refresh()


@client_refreshable
def _scenario_details():
    scenario = SCENARIO_BY_ID[SELECTED_SCENARIO["id"]]
    with ui.row().classes("gap-2"):
        ui.label(scenario.get("verified_tag", "STRESS CASE")).classes(
            "scenario-tag verified-scenario-tag")
    ui.label('Protected live execution and a separately recorded uncoordinated collision replay use the same six-vehicle demand. The secondary rules-only baseline retains safety.' if scenario['scenario_id']=='final_coordination_failure' else VIVA_PURPOSES[scenario["scenario_id"]]).classes(
        "scenario-description")
    final=FINAL_DEMONSTRATION_BY_ID.get(scenario['scenario_id'],{})
    ui.label(f"{scenario.get('vehicle_count')} vehicles · MAPPO: {final.get('mappo_expectation', 'Conditional')}").classes('scenario-description')
    ui.label(final.get('demo_kind','QUALITATIVE PRESENTATION')).classes('scenario-description')
    if scenario['scenario_id']=='final_coordination_failure':
        ui.label('Run Scenario plays the offline uncoordinated failure in the main canvas. No live unsafe simulator is launched.').classes('scenario-description')
        ui.button('Protected six-vehicle comparison',on_click=_run_protected_scenario).props('outline no-caps').classes('w-full whitespace-normal')
        ui.button('Restart replay',on_click=_start_main_replay).props('outline no-caps').classes('w-full')
        comparison_path=COMPONENT2_ROOT/'results/final_demonstrations/v1/comparison.json'
        if comparison_path.is_file():
            with ui.expansion('Recorded comparison',
                    value=COMPARISON_OPEN['value'],
                    on_value_change=lambda e:COMPARISON_OPEN.__setitem__('value',e.value)).classes('w-full min-w-0'):
                comparison=json.loads(comparison_path.read_text(encoding='utf-8'))
                for note in ('QUALITATIVE ONLY', 'Identical demand; safety enabled in A and B.', 'Run Scenario always uses the protected primary.'):
                    ui.label(note).classes('scenario-description w-full whitespace-normal break-words')
                for row in comparison['modes']:
                    title='A. Protected primary' if row['mode']=='PROPOSED_MAPPO_RULES_SAFETY' else 'B. Rules-only baseline'
                    for line in (title, f"{row['status']} · {row['completed']}/{row['scheduled']} trips",
                            f"MAPPO: {row['mappo_calls']} · collisions: {row['collisions']}",
                            f"Zone violations: {row['blocked_zone_violations']}",
                            f"Mean wait: {row['mean_wait_seconds']:.2f} s",
                            f"Throughput: {row['throughput']:.2f}/min"):
                        ui.label(line).classes('scenario-description w-full whitespace-normal break-words')
                from socialmind_drive_showcase.services.counterfactual_reader import load_evidence
                try:
                    offline=load_evidence()
                    ui.label('C. Isolated uncoordinated counterfactual').classes('scenario-description w-full break-words')
                    ui.label(f"OFFLINE ONLY · actual SUMO collisions: {offline['collision_count']}").classes('scenario-description w-full break-words')
                    ui.label('Default Run Scenario plays C in the main canvas. The protected comparison action launches A.').classes('scenario-description')
                except (OSError,ValueError,StopIteration):
                    ui.label('Offline counterfactual evidence unavailable; no outcome assumed.').classes('scenario-description')
        else:
            ui.label('Comparison evidence has not been recorded yet. No failure outcome is assumed.').classes('scenario-description')


def _run_selected_scenario():
    if SELECTED_SCENARIO['id']=='final_coordination_failure':
        _start_main_replay()
    else:
        _run_protected_scenario()


def _start_main_replay():
    if LAUNCHER.running:
        ui.notify('Stop the protected simulation before replay.',type='warning');return
    from socialmind_drive_showcase.services.main_canvas_replay import start
    try:start(REPLAY_STATE)
    except (OSError,ValueError,StopIteration) as error:
        ui.notify(str(error),type='warning')


def _run_protected_scenario():
    from socialmind_drive_showcase.services.main_canvas_replay import stop
    stop(REPLAY_STATE)
    REPLAY_STATE['mode']='protected'
    scenario_id = SELECTED_SCENARIO["id"]
    if LAUNCHER.launch(("--scenario", scenario_id)):
        global NEGOTIATION_HOLD
        NEGOTIATION_HOLD = NegotiationVisualHold()
        ui.notify(f"Launching {SCENARIO_BY_ID[scenario_id]['display_name']}",
                  type="positive")
    else:
        ui.notify(LAUNCHER.error or "A Component 2 simulation is already running.",
                  type="warning")


def _stop_current_scenario():
    if REPLAY_STATE['mode']=='replay':
        from socialmind_drive_showcase.services.main_canvas_replay import stop
        stop(REPLAY_STATE)
        return
    if LAUNCHER.request_stop():
        ui.notify("STOP REQUESTED — waiting for graceful SUMO cleanup",
                  type="warning")
    else:
        ui.notify("No running Component 2 scenario to stop.", type="warning")


@client_refreshable
def _scenario_sidebar():
    with ui.column().classes("scenario-sidebar"):
        ui.label("DEMO SCENARIOS").classes("scenario-sidebar-title")
        selector=ui.radio({item["scenario_id"]: VIVA_LABELS[item["scenario_id"]]
                  for item in SELECTABLE_SCENARIOS},
                 value=SELECTED_SCENARIO["id"],
                 on_change=_select_scenario).props(
                     "dense color=cyan" + (" disable" if LAUNCHER.running else ""))
        ui.separator().classes("my-2")
        _scenario_details()
        run_button=ui.button("Run Scenario", icon="play_arrow",
                  on_click=_run_selected_scenario).props(
                      "unelevated no-caps" + (" disable" if LAUNCHER.running else "")).classes("btn-primary w-full")
        stop_button=ui.button("Stop", icon="stop",
                  on_click=_stop_current_scenario).props(
                      "outline no-caps color=negative" +
                      (" disable" if not LAUNCHER.running or
                       LAUNCHER.status == "STOPPING" else "")).classes("w-full")
        status_label=ui.label("STOPPING SCENARIO..." if LAUNCHER.status == "STOPPING" else
                 "FAILED — see launch error" if LAUNCHER.status == "FAILED" else
                 "SIMULATION CURRENTLY RUNNING" if LAUNCHER.running else
                 "IDLE — press RUN to start").classes("scenario-run-state")
        error_label=ui.label(LAUNCHER.error or '').classes('text-red-5')
        last_state=None
        def update_controls():
            nonlocal last_state
            state=(LAUNCHER.status,LAUNCHER.running,LAUNCHER.error,REPLAY_STATE['mode'],REPLAY_STATE['active'])
            if state==last_state:return
            last_state=state
            selector.set_enabled(not LAUNCHER.running)
            run_button.set_enabled(not LAUNCHER.running and not REPLAY_STATE['active'])
            stop_button.set_enabled(REPLAY_STATE['mode']=='replay' or (LAUNCHER.running and LAUNCHER.status!='STOPPING'))
            status_label.set_text(('OFFLINE REPLAY PLAYING' if REPLAY_STATE['active'] else 'OFFLINE REPLAY PAUSED') if REPLAY_STATE['mode']=='replay' else 'STOPPING SCENARIO...' if LAUNCHER.status=='STOPPING' else
                'FAILED — see launch error' if LAUNCHER.status=='FAILED' else
                'SIMULATION CURRENTLY RUNNING' if LAUNCHER.running else 'IDLE — press RUN to start')
            error_label.set_text(LAUNCHER.error or '')
            error_label.set_visibility(bool(LAUNCHER.error))
        update_controls()
        page_timer(.5,update_controls)


def select_vehicle(vehicle_id):
    SELECTED_VEHICLE["id"] = str(vehicle_id)


def _motion_label(acceleration):
    # UI-only 0.05 m/s² deadband; it never enters runtime decisions.
    return ("ACCELERATING" if acceleration > 0.05 else
            "DECELERATING / BRAKING" if acceleration < -0.05 else
            "CRUISING")


def _vehicle_inspector(payload):
    vehicles = payload.get("vehicles", ())
    active_ids = {vehicle["id"] for vehicle in vehicles}
    if SELECTED_VEHICLE["id"] not in active_ids:
        SELECTED_VEHICLE["id"] = next(iter(active_ids), None)
    with ui.column().classes("vehicle-inspector"):
        ui.label("VEHICLE INSPECTOR").classes("vehicle-inspector-title")
        for vehicle in vehicles:
            ui.button(
                f'{short_vehicle_label(vehicle["id"])} · '
                f'{vehicle.get("display_state", "APPROACHING")}',
                on_click=lambda item=vehicle: select_vehicle(item["id"])
            ).props("flat dense no-caps").classes("vehicle-summary-card")
        selected = next((vehicle for vehicle in vehicles
                         if vehicle["id"] == SELECTED_VEHICLE["id"]), None)
        if selected is None:
            ui.label("No vehicles currently in the intersection area.").classes("inspector-empty")
            return
        ui.separator()
        ui.label(short_vehicle_label(selected["id"])).classes("selected-vehicle-name")
        ui.label(selected["id"]).classes("selected-vehicle-id")
        speed = selected.get("speed_mps")
        acceleration = selected.get("acceleration_mps2")
        _pipeline_row("SUMO", f'{speed:.2f} m/s' if speed is not None else "NOT AVAILABLE")
        _pipeline_row("MOTION", _motion_label(acceleration)
                      if acceleration is not None else "NOT AVAILABLE")
        _pipeline_row("ACCELERATION", f'{acceleration:.2f} m/s²'
                      if acceleration is not None else "NOT AVAILABLE")
        perception = selected.get("local_perception", {})
        _pipeline_row("PERCEPTION", f'{perception.get("observed_vehicle_count", 0)} ego-local observations')
        ldm = selected.get("ldm", {})
        _pipeline_row("LDM", f'{ldm.get("track_count", 0)} target tracks')
        predictions = selected.get("local_intention_predictions", ())
        prediction_text = (", ".join(
            f'{short_vehicle_label(item["target_id"])}: {item["label"]} '
            f'({item["confidence"]:.0%})' if item.get("confidence") is not None
            else f'{short_vehicle_label(item["target_id"])}: {item["label"]}'
            for item in predictions) or "WAITING FOR CONTEXT")
        _pipeline_row("INTENTION · EGO-LOCAL TARGETS", prediction_text)
        conflict = selected.get("conflict", {})
        _pipeline_row("CONFLICT", ", ".join(map(short_vehicle_label,
            conflict.get("partners", ()))) or "NOT CONFLICT-RELEVANT")
        edges = selected.get("local_precedence_edges", ())
        _pipeline_row("PRECEDENCE", "; ".join(
            f'{short_vehicle_label(a)} → {short_vehicle_label(b)} (yields)'
            for a, b in edges) or "NOT AVAILABLE")
        gnn = selected.get("gnn", {})
        _pipeline_row("GNN ENCODING", "AVAILABLE" if gnn.get("encoded") else
                      "WAITING FOR CONTEXT")
        factors = selected.get("negotiation", {}).get("factors", ())
        _pipeline_row("MAPPO SEMANTIC", "; ".join(
            f'{item["decision_role"]}: {item["selected_action"]}'
            for item in factors) or ("NOT REQUIRED" if payload.get(
                "mappo_invocation") == "NOT_REQUIRED" else
                "WAITING FOR COMPLETE LOCAL CONTEXT"))
        _pipeline_row("EGO-LOCAL EXECUTION", selected.get("planner", {}).get(
            "state", "NOT AVAILABLE"))
        control = selected.get("control", {})
        _pipeline_row("DETERMINISTIC CONTROL",
                      (f'SPEED CAP {control["speed_cap_mps"]:.2f} m/s'
                       if control.get("speed_constraint_active") else
                       "SUMO NATIVE / NO PRECEDENCE CAP"))


def _pipeline_row(stage, value):
    with ui.column().classes("pipeline-stage"):
        ui.label(stage).classes("pipeline-stage-name")
        ui.label(value).classes("pipeline-stage-value")


def _event_timeline(events):
    with ui.row().classes("event-timeline w-full no-wrap"):
        ui.label("EVENTS").classes("event-timeline-title")
        for event in events[-6:]:
            with ui.column().classes("event-timeline-item"):
                ui.label(f'{event.get("timestamp", 0):.2f} s').classes("event-time")
                ui.label(event.get("event", "EVENT")).classes("event-name")
                if event.get("mappo_invocation"):
                    ui.label(f'MAPPO {event["mappo_invocation"]}').classes("event-mappo")


def _action_text(actions):
    return "; ".join(str(item) for item in actions) or "NOT AVAILABLE"


def _negotiation_event_cards(events):
    if not events:
        return
    ui.label("NEGOTIATION EVENTS").classes("negotiation-events-title")
    last_index = len(events) - 1
    for index, event in enumerate(events):
        title = f'MAPPO NEGOTIATION — {event.get("timestamp", 0):.2f} s'
        with ui.expansion(title, value=(LAST_MAPPO_EXPANDED["value"] and
                                       index == last_index)).classes(
                                           "negotiation-event-card"):
            ui.label(f'Status: {event.get("event", "NOT AVAILABLE")}')
            ui.label("Participants: " + ", ".join(
                short_vehicle_label(item) for item in event.get(
                    "participants", ())))
            ui.label("Original graph: " + _action_text(event.get(
                "original_graph", ())))
            ui.label("Proposer actions: " + _action_text(event.get(
                "proposer_actions", ())))
            ui.label("Responder actions: " + _action_text(event.get(
                "responder_actions", ())))
            ui.label("Effective graph: " + _action_text(event.get(
                "effective_graph", ())))
            ui.label("Planner READY: " + _action_text(event.get("ready", ())))
            ui.label("Planner BLOCKED: " + _action_text(event.get("blocked", ())))


@client_refreshable
def _run_summary_panel():
    runs = read_presentation_runs(COMPONENT2_PRESENTATION_RUNS_PATH, limit=1)
    if not runs:
        ui.label("No qualitative presentation run summary is available yet.")
        return
    run = runs[0]; metrics = run.get("metrics", {})
    ui.label("RUN SUMMARY").classes("text-xl font-bold")
    ui.label("QUALITATIVE PRESENTATION RUN — not validation, held-out, or model-selection evidence")
    scenario = SCENARIO_BY_ID.get(run.get("scenario_id"), {})
    ui.label(f'Scenario: {scenario.get("display_name", run.get("scenario_id"))}')
    ui.label(f'Status: {run.get("run_status", "FAILED")}').classes("run-status")
    ui.label(f'Simulation time: {run.get("simulation_time_seconds", 0):.2f} s')
    for key, label in (("presentation_vehicles_scheduled", "Scheduled"),
                       ("presentation_vehicles_completed", "Completed"),
                       ("unfinished_vehicles", "Unfinished"),
                       ("collisions", "Collisions"),
                       ("blocked_zone_violations", "Blocked-zone violations"),
                       ("negotiation_events", "Negotiation events"),
                       ("mappo_decision_epochs", "MAPPO-authorized events"),
                       ("rule_resolved_events", "Rule-resolved events"),
                       ("renegotiation_events", "Re-negotiations")):
        ui.label(f'{label}: {metrics.get(key, "NOT AVAILABLE")}')
    ui.label("FINAL PER-VEHICLE PROCESS").classes("text-lg font-bold mt-4")
    for vehicle in run.get("vehicles", ()):
        with ui.expansion(short_vehicle_label(vehicle["id"]),
                          caption=vehicle.get("display_state", "FINAL")):
            ui.label(f'Actual speed: {vehicle.get("speed_mps", "NOT AVAILABLE")} m/s')
            ui.label(f'Actual acceleration: {vehicle.get("acceleration_mps2", "NOT AVAILABLE")} m/s²')
            ui.label(f'Planner: {vehicle.get("planner", {}).get("state", "NOT AVAILABLE")}')
            factors = vehicle.get("negotiation", {}).get("factors", ())
            ui.label("MAPPO: " + ("; ".join(
                f'{x.get("decision_role")}: {x.get("selected_action")}'
                for x in factors) or "NO MAPPO INVOCATION"))
    timeline = run.get("event_timeline", ())
    _event_timeline(timeline)
    _negotiation_event_cards(tuple(item for item in timeline
                                   if item.get("mappo_invocation") ==
                                   "AUTHORIZED"))


@client_refreshable
def _run_history_panel():
    ui.label("RUN HISTORY").classes("text-xl font-bold")
    ui.label("QUALITATIVE PRESENTATION RUNS ONLY")
    runs = read_presentation_runs(COMPONENT2_PRESENTATION_RUNS_PATH)
    if not runs:
        ui.label("No presentation runs recorded yet.")
    for index, run in enumerate(runs, 1):
        scenario = SCENARIO_BY_ID.get(run.get("scenario_id"), {})
        title = (f'#{index} {scenario.get("display_name", run.get("scenario_id"))}'
                 f' — {run.get("run_status")}')
        with ui.expansion(title):
            ui.label(f'Run ID: {run.get("run_id")}')
            ui.label(f'Simulation: {run.get("simulation_time_seconds", 0):.2f} s')
            metrics = run.get("metrics", {})
            ui.label(f'Completed: {metrics.get("presentation_vehicles_completed")} / '
                     f'{metrics.get("presentation_vehicles_scheduled")}')
