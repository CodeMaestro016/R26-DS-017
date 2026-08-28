from nicegui import ui

from socialmind_drive_showcase.config import (COMPONENT2, COMPONENT_BY_SLUG,
    PROJECT_ROOT, SHOWCASE_ROOT)
from socialmind_drive_showcase.pages.component2_results import results_panel
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.folder_service import open_predefined_folder
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import image_or_fallback, section_heading


LAUNCHER = ComponentLauncher(COMPONENT2)
FLOW = ("SUMO", "Ego-local Perception", "Local Dynamic Map", "Intention Prediction",
        "Conflict & Temporal Reasoning", "Traffic Rules", "Precedence Graph",
        "V2V Claim Exchange", "Joint-local Graph", "MAPPO Negotiation",
        "Effective Coordination Graph", "Execution Planner", "SUMO Physical Control")


def component_detail_page(slug):
    component = COMPONENT_BY_SLUG.get(slug)
    if component is None:
        ui.navigate.to("/components")
        return
    with page_layout("live" if component.live else "components"):
        _detail_hero(component)
        if component.live:
            _component2_page(component)
        else:
            _reserved_component_page(component)


def _detail_hero(component):
    with ui.element("section").classes("detail-hero w-full"):
        with ui.column().classes("page-shell"):
            ui.label(f"COMPONENT {component.number} · {component.pillar}").classes("detail-number")
            ui.label(component.title).classes("detail-title")
            ui.label(component.description).classes("hero-description")
            with ui.row().classes("mt-5 gap-2"):
                for label in component.labels:
                    ui.label(label).classes("chip")


def _reserved_component_page(component):
    image = SHOWCASE_ROOT / "assets" / "images" / component.image_name
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            with ui.row().classes("w-full gap-10 items-stretch"):
                with ui.column().classes("grow min-w-[300px]"):
                    section_heading("RESEARCH OBJECTIVE", component.title, component.description)
                    ui.label("Research focus").classes("text-lg font-bold mt-7")
                    with ui.row().classes("gap-1"):
                        for label in component.labels:
                            ui.label(label).classes("chip")
                    ui.label("Integration status").classes("text-lg font-bold mt-7")
                    ui.label("Presentation module prepared; live runtime will be connected separately.").classes("section-copy")
                with ui.element("div").classes("grow min-w-[300px]"):
                    image_or_fallback(image, component.icon, f"Component {component.number} visual space")
            with ui.element("div").classes("reserved-panel w-full mt-12"):
                ui.icon("extension", size="48px").classes("text-cyan-7")
                ui.label("LIVE MODULE INTEGRATION SPACE").classes("font-extrabold tracking-widest mt-3")
                ui.label("Live local integration pending. A launch adapter, result source and project location can be connected here later without changing this presentation page.").classes("max-w-2xl")


def _component2_page(component):
    image = SHOWCASE_ROOT / "assets" / "images" / component.image_name
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            with ui.row().classes("w-full gap-10 items-center"):
                with ui.column().classes("grow min-w-[320px]"):
                    section_heading("RESEARCH OBJECTIVE", "Safe, rule-respecting intersection coordination",
                        "Enable autonomous vehicles to establish a safe, rule-respecting and executable order for crossing complex unsignalized intersections using decentralized local reasoning and learned negotiation.")
                    with ui.row().classes("mt-6 gap-3"):
                        ui.button("Run Live SUMO Demo", icon="play_arrow", on_click=_launch_demo).props("unelevated no-caps").classes("btn-primary px-6")
                        ui.button("Refresh Results", icon="refresh", on_click=results_panel.refresh).props("outline no-caps")
                with ui.element("div").classes("grow min-w-[320px]"):
                    image_or_fallback(image, "traffic", "Live intersection negotiation")
            _launcher_status()
            with ui.element("div").classes("info-grid mt-10"):
                for label, value, icon in (("LIVE DEMO", "Available", "play_circle"),
                    ("SELECTED POLICY", "E5", "model_training"),
                    ("EXECUTION", "Decentralized", "device_hub"),
                    ("TRAINING DURING DEMO", "Disabled", "lock"),
                    ("CRITIC AT RUNTIME", "Disabled", "memory")):
                    with ui.element("div").classes("info-card"):
                        ui.icon(icon).classes("text-cyan-7")
                        ui.label(label).classes("metric-label")
                        ui.label(value).classes("font-bold text-xl mt-1")
    with ui.element("section").classes("section section-dark w-full"):
        with ui.column().classes("page-shell"):
            section_heading("SYSTEM OVERVIEW", "From local perception to deterministic physical execution",
                            "MAPPO acts only at the semantic negotiation layer; the physical planner remains deterministic.")
            with ui.element("div").classes("architecture-flow"):
                for node in FLOW:
                    ui.label(node).classes("flow-node")
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            section_heading("TECHNOLOGY", "Operational research stack")
            with ui.row().classes("gap-1 mt-3"):
                for item in ("SUMO", "Python", "ONNX Runtime", "GRU Intention Prediction", "Graph Representation", "MAPPO", "TraCI", "German StVO Rule Profile"):
                    ui.label(item).classes("chip")
            ui.separator().classes("my-12")
            section_heading("MAPPO SEMANTICS", "Learned coordination, deterministic control")
            with ui.row().classes("w-full gap-6 mt-5"):
                _semantic_card("PROPOSER", "KEEP_CLAIM", "RELINQUISH_CLAIM", "record_voice_over")
                _semantic_card("RESPONDER", "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT", "forum")
            with ui.element("div").classes("disclaimer mt-6"):
                ui.label("MAPPO does not directly output speed, braking, acceleration or steering. Physical execution remains handled by the deterministic planner and SUMO control layer.")
            ui.separator().classes("my-12")
            section_heading("LATEST LIVE RESULTS", "Qualitative panel demonstration evidence")
            with ui.row().classes("gap-3 mb-6"):
                ui.button("Refresh Latest Results", icon="refresh", on_click=results_panel.refresh).props("outline no-caps")
                ui.button("Open Panel Results Folder", icon="folder_open", on_click=lambda: _open_folder(PROJECT_ROOT / "results" / "panel_demo")).props("flat no-caps")
                ui.button("Open Technical Project Folder", icon="source", on_click=lambda: _open_folder(PROJECT_ROOT)).props("flat no-caps")
            results_panel()


def _semantic_card(role, first, second, icon):
    with ui.element("div").classes("info-card grow min-w-[280px]"):
        ui.icon(icon, size="30px").classes("text-cyan-7")
        ui.label(role).classes("eyebrow mt-3")
        ui.label(first).classes("action-card mt-3 font-bold")
        ui.label(second).classes("action-card mt-2 font-bold")


@ui.refreshable
def _launcher_status():
    colors = {"READY": "text-blue-7", "LAUNCHING": "text-amber-8", "RUNNING": "text-green-7", "FINISHED": "text-teal-7", "FAILED": "text-red-7"}
    with ui.row().classes("items-center mt-5 gap-2"):
        ui.icon("circle", size="12px").classes(colors.get(LAUNCHER.status, "text-grey"))
        ui.label(f"DEMO STATUS · {LAUNCHER.status}").classes("font-bold tracking-wider")
        if LAUNCHER.error:
            ui.label(LAUNCHER.error).classes("text-red-7")


def _launch_demo():
    if LAUNCHER.launch():
        ui.notify("Launching the existing Component 2 SUMO demonstration…", type="positive")
    else:
        ui.notify(LAUNCHER.error or "The demonstration is already running.", type="warning")
    _launcher_status.refresh()
    ui.timer(1.0, _launcher_status.refresh, once=False)


def _open_folder(path):
    try:
        open_predefined_folder(path)
    except OSError as error:
        ui.notify(f"Folder could not be opened: {error}", type="negative")
