from nicegui import ui
from socialmind_drive_showcase.config import PROJECT_TITLE, PROJECT_SUBTITLE


def footer():
    with ui.element("footer").classes("footer w-full"):
        with ui.row().classes("page-shell items-center justify-between w-full"):
            with ui.column().classes("gap-1"):
                ui.label(PROJECT_TITLE).classes("text-white font-bold")
                ui.label(PROJECT_SUBTITLE).classes("text-sm")
            ui.label("Unified Research Showcase · Local presentation layer").classes("text-xs")

