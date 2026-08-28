from nicegui import ui

from socialmind_drive_showcase.config import (COMPONENTS, HOME_HERO_IMAGE,
    PROJECT_DESCRIPTION, PROJECT_SUBTITLE, PROJECT_TITLE, SHOWCASE_NOTE)
from socialmind_drive_showcase.config import RESEARCH_VISION_IMAGE
from socialmind_drive_showcase.ui.cards import component_card
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import image_or_fallback, section_heading


def home_page():
    with page_layout("home"):
        with ui.element("section").classes("hero w-full"):
            with ui.element("div").classes("page-shell"):
                with ui.element("div").classes("hero-copy"):
                    ui.label("UNIFIED RESEARCH SHOWCASE").classes("eyebrow")
                    ui.label(PROJECT_TITLE).classes("hero-title")
                    ui.label(PROJECT_SUBTITLE).classes("hero-subtitle")
                    ui.label(PROJECT_DESCRIPTION).classes("hero-description")
                    with ui.row().classes("mt-9 gap-3"):
                        ui.button("Explore Research Components", icon="explore",
                                  on_click=lambda: ui.navigate.to("/components")) \
                            .props("unelevated no-caps").classes("btn-primary px-6")
                        ui.button("View Live Demonstration", icon="play_circle",
                                  on_click=lambda: ui.navigate.to("/component/right-of-way")) \
                            .props("flat no-caps").classes("btn-secondary px-6")
                with ui.element("div").classes("hero-visual"):
                    if HOME_HERO_IMAGE.is_file():
                        ui.image(str(HOME_HERO_IMAGE)).classes("hero-main-image")
                    else:
                        ui.icon("directions_car", size="110px").classes("text-cyan-3")
        with ui.element("section").classes("section w-full"):
            with ui.column().classes("page-shell"):
                section_heading("RESEARCH VISION", "Autonomous intelligence that understands shared roads",
                                SHOWCASE_NOTE)
                with ui.row().classes("w-full gap-8 mt-10 items-stretch"):
                    with ui.element("div").classes("grow min-w-[300px]"):
                        image_or_fallback(RESEARCH_VISION_IMAGE, "radar", "Autonomous-driving research visual")
                    with ui.column().classes("grow min-w-[300px] justify-center gap-5"):
                        for icon, title, copy in (("visibility", "Perceive uncertainty", "Reason from incomplete and occluded observations."),
                                                  ("hub", "Coordinate safely", "Establish executable right-of-way through rules and negotiation."),
                                                  ("groups", "Understand road users", "Study socially aware and collaborative vehicle intelligence.")):
                            with ui.row().classes("items-start gap-4 no-wrap"):
                                ui.icon(icon, size="28px").classes("text-cyan-7")
                                with ui.column().classes("gap-1"):
                                    ui.label(title).classes("font-bold text-lg")
                                    ui.label(copy).classes("text-blue-grey-6")
        with ui.element("section").classes("section section-dark w-full"):
            with ui.column().classes("page-shell"):
                section_heading("FOUR RESEARCH PILLARS", "Independent components, one presentation platform",
                                "The pillars are a conceptual research framing and do not imply a single connected runtime pipeline.")
                with ui.element("div").classes("component-grid"):
                    for component in COMPONENTS:
                        component_card(component)
