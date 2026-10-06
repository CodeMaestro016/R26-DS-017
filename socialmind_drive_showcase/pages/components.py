from nicegui import ui
from socialmind_drive_showcase.config import COMPONENTS, SHOWCASE_NOTE
from socialmind_drive_showcase.ui.cards import component_card
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import section_heading


def components_page():
    with page_layout("components"):
        with ui.element("section").classes("detail-hero w-full"):
            with ui.column().classes("page-shell"):
                ui.label("UNIFIED RESEARCH SHOWCASE").classes("eyebrow")
                ui.label("Four directions for socially-aware autonomous driving").classes("detail-title")
                ui.label(SHOWCASE_NOTE).classes("hero-description")
        with ui.element("section").classes("section w-full"):
            with ui.column().classes("page-shell"):
                section_heading("RESEARCH COMPONENTS", "Explore the four independent research pillars")
                with ui.element("div").classes("component-grid"):
                    for component in COMPONENTS:
                        component_card(component)

