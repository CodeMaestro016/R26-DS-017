"""Local NiceGUI entry point for the SOCIALMIND DRIVE desktop application."""

import argparse
import importlib.util
import socket
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nicegui import app, ui

from socialmind_drive_showcase.config import COMPONENT2_LIVE_STATE_PATH, HOST, PORT
from socialmind_drive_showcase.pages.about import about_page
from socialmind_drive_showcase.pages.component_1 import component_1_page
from socialmind_drive_showcase.pages.component_4 import component_4_page
from socialmind_drive_showcase.pages.component_detail import component_detail_page, LAUNCHER
from socialmind_drive_showcase.pages.component2_live_view import (
    apply_live_display_state,
    component2_live_view_page,
    select_vehicle,
    render_sumo_style_svg,
    idle_display_state,
)
from socialmind_drive_showcase.pages.components import components_page
from socialmind_drive_showcase.pages.component2_evaluation import component2_evaluation_page
from socialmind_drive_showcase.pages.home import home_page
from socialmind_drive_showcase.services.live_state_reader import read_live_state


WINDOW_SIZE = (1400, 900)
def shutdown_owned_runtime():
    """NiceGUI may inject App into parameterized lifecycle handlers."""
    LAUNCHER.shutdown(grace_seconds=5.0)


app.on_shutdown(shutdown_owned_runtime)


def build_app():
    ui.page("/")(home_page)
    ui.page("/components")(components_page)
    ui.page("/component/adaptive-intent")(component_1_page)
    ui.page("/component/federated-learning")(component_4_page)
    ui.page("/component/right-of-way/live")(component2_live_view_page)
    ui.page("/component/right-of-way/evaluation")(component2_evaluation_page)
    ui.page("/component/{slug}")(component_detail_page)
    ui.page("/about")(about_page)
    return app


@app.get("/api/component2/live-state")
def component2_live_state_api(zoom: float = 1.0, scenario: str = ''):
    """Return the latest display snapshot without touching the simulation."""
    state = (idle_display_state(scenario) if LAUNCHER.status=='READY' else
        apply_live_display_state(read_live_state(COMPONENT2_LIVE_STATE_PATH,
            started_after=LAUNCHER.started_at)))
    if state.get('available') and not state.get('stale'):
        state['rendered_svg'] = render_sumo_style_svg(state['payload'],
            zoom_factor=max(0.55, min(1.8, zoom)))
    return state


@app.post("/api/component2/select-vehicle")
def component2_select_vehicle_api(id: str):
    """Update display-only inspector selection; never touch SUMO."""
    select_vehicle(id)
    return {"selected_vehicle_id": id, "display_only": True}


@app.get('/api/component2/counterfactual/frame')
def counterfactual_frame_api(index: int = 0):
    """Read recorded evidence only. This endpoint cannot launch a simulation."""
    from socialmind_drive_showcase.services.counterfactual_reader import recorded_frame
    from socialmind_drive_showcase.pages.component2_live_view import authoritative_road_geometry,build_world_transform
    import re
    try:result=recorded_frame(index)
    except (OSError,ValueError,StopIteration) as error:return dict(available=False,message=str(error))
    frame=result['frame']
    geometry=authoritative_road_geometry()
    # Both cameras use the same real coordinates and physical dimensions.
    def render_camera(extent):
        svg=render_sumo_style_svg(dict(vehicles=frame['vehicles'],simulation_time=frame['simulation_time'],scenario_id='OFFLINE_COUNTERFACTUAL'),zoom_factor=geometry['camera_half_extent_m']/extent)
        svg=svg.replace('sumo-live-canvas','counterfactual-canvas').replace('c2-synchronized-frame','offline-synchronized-frame').replace('class="sumo-car"','class="offline-car"')
        svg=svg.replace('aria-label="Live top-down SUMO intersection"','aria-label="Recorded offline unsafe SUMO trajectory"')
        svg=re.sub(r' onclick="[^"]*"','',svg)
        cx,cy=geometry['center'];transform=build_world_transform(1100,700,(cx-extent,cy-extent,cx+extent,cy+extent))
        # Annotate recorded paths without moving any vehicle or altering its size.
        from socialmind_drive_showcase.services.counterfactual_reader import load_evidence
        paths={}
        for sample in load_evidence()['frames']:
            for v in sample['vehicles']:
                paths.setdefault(v['id'],[]).append(transform.point(v['front_bumper_x'],v['front_bumper_y']))
        routes=''.join('<polyline class="recorded-route" points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'" fill="none" stroke="#c7e5ff" stroke-width="1" stroke-dasharray="5 5" opacity=".45"/>' for points in paths.values())
        svg=svg.replace('<g class="sumo-live-vehicles">',routes+'<g class="sumo-live-vehicles">')
        for event in frame['collisions']:
            x,y=transform.point(*event['position'])
            svg=svg.replace('</svg>',f'<circle class="recorded-collision-marker" cx="{x}" cy="{y}" r="18" fill="none" stroke="#ff4b4b" stroke-width="2"><title>Actual SUMO-detected collision reference position</title></circle></svg>')
        return svg
    result['rendered_svg']=render_camera(22.)
    result['overview_svg']=render_camera(310.)
    from socialmind_drive_showcase.services.counterfactual_reader import junction_evidence
    result['junction_evidence']=junction_evidence()
    return result


def run_showcase(*, port=PORT, native=True):
    """Run one local server, optionally hosted in a native desktop window."""
    build_app()
    ui.run(
        host=HOST,
        port=port,
        title="SOCIALMIND DRIVE",
        favicon="🚘",
        native=native,
        window_size=WINDOW_SIZE if native else None,
        fullscreen=False,
        frameless=False,
        reload=False,
        show=False,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="SOCIALMIND DRIVE desktop application"
    )
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Run the localhost server without opening the desktop window",
    )
    # Retain the former headless flag as a compatibility alias for scripts.
    parser.add_argument("--no-browser", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    native = not (args.server_only or args.no_browser)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if native and importlib.util.find_spec("webview") is None:
        parser.error("Desktop dependency pywebview is missing. Install socialmind_drive_showcase/requirements.txt, or use --server-only.")
    try:
        with socket.socket() as probe:
            probe.bind((HOST, args.port))
    except OSError:
        parser.error(f"Port {args.port} is unavailable. Close the existing showcase or choose --port with a free port.")
    run_showcase(port=args.port, native=native)


if __name__ in {"__main__", "__mp_main__"}:
    main()
