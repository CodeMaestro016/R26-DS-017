from nicegui import ui

from socialmind_drive_showcase.config import BRAND_LOGO_IMAGE, PROJECT_TITLE


def navbar(active=""):
    with ui.header(elevated=False).classes("nav-glass h-20"):
        with ui.row().classes("page-shell items-center justify-between w-full no-wrap"):
            with ui.row().classes("items-center gap-3 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
                if BRAND_LOGO_IMAGE.is_file():
                    ui.image(str(BRAND_LOGO_IMAGE)).classes("brand-logo")
                else:
                    ui.icon("directions_car", size="22px").classes("brand-mark")
                ui.label(PROJECT_TITLE).classes("text-white font-bold tracking-wider")
            with ui.row().classes("nav-links items-center gap-1"):
                for title, path, key in (("Home", "/", "home"), ("Components", "/components", "components"),
                                         ("Live Demo", "/component/right-of-way", "live"), ("About", "/about", "about")):
                    button = ui.button(title, on_click=lambda p=path: ui.navigate.to(p)).props("flat no-caps")
                    button.classes("text-cyan-2" if key == active else "text-blue-grey-2")
