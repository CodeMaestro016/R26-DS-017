from nicegui import ui
from socialmind_drive_showcase.config import SHOWCASE_ROOT
from socialmind_drive_showcase.ui.reusable import card_image_or_fallback


def component_card(component):
    card_class = "component-card live" if component.live else "component-card"
    with ui.element("article").classes(card_class):
        card_image_or_fallback(
            SHOWCASE_ROOT / "assets" / "images" / component.image_name,
            component.icon)
        with ui.element("div").classes("component-card-body"):
            with ui.row().classes("justify-between items-start w-full"):
                ui.label(component.number).classes("component-number")
                ui.label(component.status).classes("badge-live" if component.live else "badge-reserved")
            ui.icon(component.icon, size="30px").classes("text-cyan-5")
            ui.label(component.pillar).classes("eyebrow mt-3")
            ui.label(component.title).classes("component-title")
            ui.label(component.description).classes("component-description")
            with ui.row().classes("mt-4 gap-0"):
                for label in component.labels:
                    ui.label(label).classes("chip")
            ui.button("Explore Component", icon="arrow_forward",
                      on_click=lambda: ui.navigate.to(f"/component/{component.slug}")) \
                .props("flat no-caps").classes("mt-5 text-cyan-6 font-bold")


def metric_card(label, value, icon="analytics"):
    with ui.element("div").classes("metric-card"):
        ui.icon(icon, size="22px").classes("text-cyan-7")
        ui.label(str(value)).classes("metric-value")
        ui.label(label).classes("metric-label")
