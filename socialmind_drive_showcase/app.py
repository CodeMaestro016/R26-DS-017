"""Local-only NiceGUI entry point for the SOCIALMIND DRIVE showcase."""

import argparse
import sys
import threading
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nicegui import app, ui
from socialmind_drive_showcase.config import HOST, PORT
from socialmind_drive_showcase.pages.about import about_page
from socialmind_drive_showcase.pages.component_detail import component_detail_page
from socialmind_drive_showcase.pages.components import components_page
from socialmind_drive_showcase.pages.home import home_page
from socialmind_drive_showcase.services.browser_launcher import open_showcase


def build_app():
    ui.page("/")(home_page)
    ui.page("/components")(components_page)
    ui.page("/component/{slug}")(component_detail_page)
    ui.page("/about")(about_page)
    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description="SOCIALMIND DRIVE local showcase")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--presentation", action="store_true",
                        help="Prefer a clean Chrome app-style window")
    parser.add_argument("--no-browser", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    build_app()
    url = f"http://{HOST}:{args.port}"
    if not args.no_browser:
        threading.Timer(1.25, lambda: open_showcase(
            url, presentation=True)).start()
    ui.run(host=HOST, port=args.port, title="SOCIALMIND DRIVE",
           favicon="🚘", reload=False, show=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
