"""Local NiceGUI entry point for the SOCIALMIND DRIVE desktop application."""

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nicegui import app, ui

from socialmind_drive_showcase.config import COMPONENT2_LIVE_STATE_PATH, HOST, PORT
from socialmind_drive_showcase.pages.about import about_page
from socialmind_drive_showcase.pages.component_1 import component_1_page
from socialmind_drive_showcase.pages.component_4 import component_4_page
from socialmind_drive_showcase.pages.component_detail import component_detail_page
from socialmind_drive_showcase.pages.component2_live_view import (
    apply_live_display_state,
    component2_live_view_page,
    select_vehicle,
)
from socialmind_drive_showcase.pages.components import components_page
from socialmind_drive_showcase.pages.home import home_page
from socialmind_drive_showcase.services.live_state_reader import read_live_state


WINDOW_SIZE = (1400, 900)


def build_app():
    ui.page("/")(home_page)
    ui.page("/components")(components_page)
    ui.page("/component/adaptive-intent")(component_1_page)
    ui.page("/component/federated-learning")(component_4_page)
    ui.page("/component/right-of-way/live")(component2_live_view_page)
    ui.page("/component/{slug}")(component_detail_page)
    ui.page("/about")(about_page)
    return app


@app.get("/api/component2/live-state")
def component2_live_state_api():
    """Return the latest display snapshot without touching the simulation."""
    return apply_live_display_state(read_live_state(COMPONENT2_LIVE_STATE_PATH))


@app.post("/api/component2/select-vehicle")
def component2_select_vehicle_api(id: str):
    """Update display-only inspector selection; never touch SUMO."""
    select_vehicle(id)
    return {"selected_vehicle_id": id, "display_only": True}


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
    run_showcase(port=args.port, native=not (args.server_only or args.no_browser))


if __name__ in {"__main__", "__mp_main__"}:
    main()
