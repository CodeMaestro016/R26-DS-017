from nicegui import ui
import httpx

from socialmind_drive_showcase.config import COMPONENT_BY_SLUG, SHOWCASE_ROOT
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import image_or_fallback, section_heading


# ============================================================
# CARLA FASTAPI CONNECTION
# ============================================================

CARLA_API = "https://circulation-islamic-presents-wealth.trycloudflare.com"


# ============================================================
# COMPONENT 4 PAGE
# ============================================================

def component_4_page():

    component = COMPONENT_BY_SLUG["federated-learning"]

    image = (
        SHOWCASE_ROOT
        / "assets"
        / "images"
        / component.image_name
    )

    with page_layout("components"):

        _detail_hero(component)

        with ui.element("section").classes("section w-full"):
            with ui.column().classes("page-shell"):
                image_or_fallback(
                    image,
                    component.icon,
                    f"Component {component.number} visual space",
                )

        _research_content(component, image)


# ============================================================
# HERO
# ============================================================

def _detail_hero(component):

    with ui.element("section").classes("detail-hero w-full"):

        with ui.column().classes("page-shell"):

            ui.label(
                f"COMPONENT {component.number} · {component.pillar}"
            ).classes("detail-number")

            ui.label(
                component.title
            ).classes("detail-title")

            ui.label(
                "A live CARLA simulation where three autonomous vehicles "
                "independently detect road signs, classify them with their "
                "own CNN models, and use reinforcement learning to decide "
                "what is worth sharing. Verified knowledge is broadcast "
                "across the fleet so vehicles benefit from what others have "
                "learned, without exchanging raw sensor data."
            ).classes("hero-description")

            with ui.row().classes("mt-5 gap-2"):

                for label in component.labels:

                    ui.label(label).classes("chip")


# ============================================================
# STATUS -> CHIP DISPLAY HELPERS
# ============================================================

def _status_display(status):
    mapping = {
        "KNOWN_SIGN_IGNORED": ("Already known", "chip-gray"),
        "MATCH_FOUND": ("Matched (training)", "chip-blue"),
        "IGNORED_BY_RL": ("RL: not shared", "chip-amber"),
        "ACCEPTED": ("Shared & verified", "chip-green"),
        "VERIFIED": ("Shared & verified", "chip-green"),
        "COMPLETED": ("Completed", "chip-gray"),
        "REJECTED": ("Rejected", "chip-red"),
        "ERROR": ("Error", "chip-red"),
    }
    return mapping.get(status, (status or "Unknown", "chip-gray"))


def _step_line(step):
    """
    One short, readable line per pipeline step, e.g.:
    "Step 2 - CNN Classification: RARE - stop (74%)"
    """
    name = step.get("name", f"Step {step.get('step', '?')}")
    status = step.get("status", "")

    details = []

    if "class_name" in step and step.get("class_name"):
        details.append(str(step["class_name"]))

    if "confidence" in step and isinstance(step.get("confidence"), (int, float)):
        details.append(f"{round(step['confidence'] * 100)}%")

    if "similarity" in step and isinstance(step.get("similarity"), (int, float)):
        details.append(f"similarity {round(step['similarity'] * 100)}%")

    if "importance_score" in step:
        details.append(f"score {step['importance_score']}")

    if "decision" in step:
        details.append(str(step["decision"]))

    if "reward" in step and step.get("reward") is not None:
        details.append(f"reward {step['reward']}")

    if "shape" in step:
        details.append(f"shape: {step['shape']}")

    detail_text = " · ".join(details)

    return f"Step {step.get('step', '?')} - {name}: {status}" + (
        f" ({detail_text})" if detail_text else ""
    )


# ============================================================
# MAIN RESEARCH CONTENT
# ============================================================

def _research_content(component, image):

    # No vehicle selected by default - Start stays disabled
    # until the user explicitly picks one, so there's never
    # ambiguity about which vehicle is actually running.
    selected_vehicle = {"value": None}
    vehicle_buttons = {}
    start_button = None

    status_label = None
    connection_label = None
    pipeline_label = None
    message_label = None

    def call_carla(action, vehicle=None):
        try:
            params = {"action": action}
            if vehicle:
                params["vehicle"] = vehicle
            response = httpx.post(f"{CARLA_API}/process", params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            ui.notify(f"CARLA API error: {e}", type="negative")
            return None

    def get_status():
        try:
            response = httpx.get(f"{CARLA_API}/status", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "connected": False, "running": False,
                "vehicle": selected_vehicle["value"],
                "pipeline_status": "offline", "message": str(e),
            }

    def get_latest_detection():
        try:
            response = httpx.get(f"{CARLA_API}/latest_detection", timeout=5.0)
            response.raise_for_status()
            return response.json().get("latest")
        except Exception:
            return None

    def get_pipeline_history():
        try:
            response = httpx.get(f"{CARLA_API}/pipeline_history", timeout=5.0)
            response.raise_for_status()
            return response.json().get("history", [])
        except Exception:
            return []

    def refresh_status():
        state = get_status()

        if connection_label:
            if state.get("connected"):
                connection_label.set_text("● CARLA CONNECTED")
                connection_label.classes(remove="text-red-600", add="text-green-600")
            else:
                connection_label.set_text("● CARLA OFFLINE")
                connection_label.classes(remove="text-green-600", add="text-red-600")

        if status_label:
            if state.get("running"):
                status_label.set_text("RUNNING")
                status_label.classes(remove="text-gray-600", add="text-green-600")
            else:
                status_label.set_text("STOPPED")
                status_label.classes(remove="text-green-600", add="text-gray-600")

        if pipeline_label:
            pipeline_label.set_text(f"Pipeline: {state.get('pipeline_status', 'unknown')}")

        if message_label:
            message_label.set_text(state.get("message", ""))

        render_latest_card.refresh()

    # --------------------------------------------------------
    # Latest detection card (with full step breakdown)
    # --------------------------------------------------------

    @ui.refreshable
    def render_latest_card():

        latest = get_latest_detection()

        if not latest:
            ui.label("No signs detected yet.").classes("section-copy")
            return

        friendly_status, chip_class = _status_display(latest.get("status"))

        with ui.card().classes("w-full mt-2 pipeline-card"):

            with ui.row().classes("items-center justify-between w-full"):
                ui.label(
                    f"Sign #{latest.get('sign_number', '-')} · "
                    f"{latest.get('class_name') or 'Unknown sign'}"
                ).classes("font-bold text-lg")
                ui.label(friendly_status).classes(f"chip {chip_class}")

            ui.separator().classes("my-2")

            ui.label("Pipeline steps").classes("font-bold text-sm mt-1")

            steps = latest.get("steps", [])
            if not steps:
                ui.label("No step detail recorded.").classes("section-copy")
            else:
                for step in steps:
                    ui.label(_step_line(step)).classes("section-copy")

    # --------------------------------------------------------
    # History dialog
    # --------------------------------------------------------

    history_dialog = ui.dialog()

    def open_history():
        history_dialog.clear()
        with history_dialog, ui.card().classes("w-full max-w-2xl"):
            ui.label("Detection History").classes("text-xl font-extrabold mb-2")
            ui.label(
                "All signs processed since the last Start."
            ).classes("section-copy mb-3")

            history = get_pipeline_history()

            if not history:
                ui.label("No detections recorded yet.").classes("section-copy")
            else:
                with ui.column().classes("w-full gap-2").style("max-height: 60vh; overflow-y: auto;"):
                    for entry in history:
                        friendly_status, chip_class = _status_display(entry.get("status"))
                        with ui.expansion(
                            f"Sign #{entry.get('sign_number', '-')} · "
                            f"{entry.get('class_name') or 'Unknown sign'} - {friendly_status}"
                        ).classes("w-full"):
                            for step in entry.get("steps", []):
                                ui.label(_step_line(step)).classes("section-copy")

            ui.button("Close", on_click=history_dialog.close).classes("mt-3")
        history_dialog.open()

    # --------------------------------------------------------
    # Select vehicle / Start / Stop / Broadcast
    # --------------------------------------------------------

    def select_vehicle(vehicle):
        selected_vehicle["value"] = vehicle

        # Highlight the selected button, un-highlight the others
        for v_id, button in vehicle_buttons.items():
            if v_id == vehicle:
                button.props(remove="outline")
            else:
                button.props("outline")

        if start_button:
            start_button.props(remove="disable")

        ui.notify(f"{vehicle.replace('_', ' ')} selected", type="info")
        refresh_status()

    def start_simulation():
        vehicle = selected_vehicle["value"]

        if not vehicle:
            ui.notify("Select a vehicle first.", type="warning")
            return

        result = call_carla("start", vehicle)
        if result and result.get("success"):
            ui.notify(f"{vehicle.replace('_', ' ')} simulation started", type="positive")
        refresh_status()

    def stop_simulation():
        result = call_carla("stop")
        if result and result.get("success"):
            ui.notify("Simulation stopped", type="warning")
        refresh_status()

    def broadcast_knowledge():
        result = call_carla("broadcast")
        if result and result.get("success"):
            ui.notify("Knowledge broadcast triggered", type="positive")
        elif result:
            ui.notify(result.get("message", "Broadcast failed"), type="negative")
        refresh_status()

    # ========================================================
    # PAGE
    # ========================================================

    with ui.element("section").classes("section w-full"):

        with ui.column().classes("page-shell"):

            with ui.column().classes("w-full"):

                ui.label("RESEARCH OBJECTIVE").classes(
                    "text-2xl font-extrabold tracking-widest text-cyan-700"
                )

                ui.label(
                    "Design and validate an agentic knowledge-sharing framework "
                    "that enables vehicles to intelligently share knowledge from "
                    "rare or new road scenarios."
                ).classes("text-2xl font-bold mt-2")

                ui.label("Integration status").classes("text-lg font-bold mt-7 mb-2")

                with ui.card().classes("w-full p-4 gap-1"):
                    connection_label = ui.label("Checking CARLA...").classes("font-bold text-lg")
                    pipeline_label = ui.label("Pipeline: checking...").classes("section-copy mt-1")
                    message_label = ui.label("Connecting to CARLA...").classes("section-copy")

            ui.label("VEHICLE SELECTION").classes("text-xl font-extrabold tracking-wide mt-10")

            with ui.row().classes("gap-3 w-full mt-4"):
                for vehicle in ("Vehicle A", "Vehicle B", "Vehicle C"):
                    vehicle_id = vehicle.replace(" ", "_")
                    btn = ui.button(
                        vehicle, icon="directions_car",
                        on_click=lambda v=vehicle_id: select_vehicle(v),
                    ).props("outline no-caps").classes("btn-primary")
                    vehicle_buttons[vehicle_id] = btn

            ui.label("Select a vehicle above to enable Start.").classes(
                "section-copy mt-1 text-sm italic"
            )

            ui.label("SIMULATION CONTROL").classes("text-xl font-extrabold tracking-wide mt-8")

            with ui.row().classes("gap-3 w-full mt-4"):
                start_button = ui.button(
                    "Start", icon="play_arrow", on_click=start_simulation,
                ).props("unelevated no-caps disable").classes("btn-primary")

                ui.button(
                    "Stop", icon="stop", on_click=stop_simulation,
                ).props("outline no-caps")

                ui.button(
                    "Broadcast", icon="campaign", on_click=broadcast_knowledge,
                ).props("outline no-caps")

            with ui.row().classes("w-full mt-8 gap-6 items-start no-wrap"):

                with ui.element("div").classes("reserved-panel w-3/4"):

                    ui.icon("directions_car", size="48px").classes("text-cyan-7")
                    ui.label("LIVE CARLA SIMULATION").classes("font-extrabold tracking-widest mt-3")
                    status_label = ui.label("STOPPED").classes("font-bold text-lg text-gray-600 mt-2")
                    ui.label("LIVE CAMERA FEED").classes("font-bold tracking-wide mt-6")

                    ui.html(
                        f"""
                        <div style="
                            width:100%;
                            max-width:1280px;
                            margin-top:12px;
                            background:#111;
                            border-radius:12px;
                            overflow:hidden;
                        ">
                            <img
                                src="{CARLA_API}/video_feed"
                                style="
                                    width:100%;
                                    height:auto;
                                    display:block;
                                "
                            />
                        </div>
                        """
                    )

                    message_label = ui.label("Waiting for simulation...").classes("section-copy mt-4")

                with ui.column().classes("w-1/4 gap-2"):

                    ui.button(
                        "History", icon="history", on_click=open_history,
                    ).props("outline no-caps").classes("w-full")

                    ui.label("LATEST DETECTION").classes("text-lg font-extrabold tracking-wide mt-4")
                    ui.label(
                        "The most recently processed sign, with its full "
                        "pipeline breakdown. Use History to see everything "
                        "since Start."
                    ).classes("section-copy mt-1 mb-2")

                    render_latest_card()

    ui.timer(2.0, refresh_status)
    refresh_status()