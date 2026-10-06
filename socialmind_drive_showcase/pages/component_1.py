from __future__ import annotations

import asyncio
import time

from nicegui import ui

from socialmind_drive_showcase.config import (
    COMPONENT_BY_SLUG,
    SHOWCASE_ROOT,
)
from socialmind_drive_showcase.pages.component_detail import (
    _detail_hero,
)
from socialmind_drive_showcase.services.component1_live import (
    component1_live,
)
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import (
    image_or_fallback,
    section_heading,
)


# ============================================================
# COMPONENT 1 PAGE
# ============================================================


def component_1_page():
    component = COMPONENT_BY_SLUG["adaptive-intent"]

    with page_layout("components"):
        _detail_hero(component)
        _component_1_live_page(component)


# ============================================================
# COMPONENT 1 CONTENT + LIVE DEMO
# ============================================================


def _component_1_live_page(component):
    image = (
        SHOWCASE_ROOT
        / "assets"
        / "images"
        / component.image_name
    )

    with ui.element("section").classes(
        "section w-full"
    ):

        with ui.column().classes(
            "page-shell"
        ):

            # ==================================================
            # RESEARCH INFORMATION
            # ==================================================

            with ui.row().classes(
                "w-full gap-10 items-stretch"
            ):

                with ui.column().classes(
                    "grow min-w-[300px]"
                ):

                    section_heading(
                        "RESEARCH OBJECTIVE",
                        component.title,
                        component.description,
                    )

                    ui.label(
                        "Research focus"
                    ).classes(
                        "text-lg font-bold mt-7"
                    )

                    with ui.row().classes(
                        "gap-1 flex-wrap"
                    ):

                        for label in component.labels:
                            ui.label(
                                label
                            ).classes(
                                "chip"
                            )

                    ui.label(
                        "Live evaluation"
                    ).classes(
                        "text-lg font-bold mt-7"
                    )

                    ui.label(
                        "Real-time CARLA evaluation using "
                        "the trained occlusion-aware pedestrian "
                        "intent prediction pipeline. The live "
                        "runtime performs pedestrian detection, "
                        "tracking, occlusion estimation, temporal "
                        "intent prediction, uncertainty estimation "
                        "and learned selective decision-making."
                    ).classes(
                        "section-copy"
                    )

                with ui.element("div").classes(
                    "grow min-w-[300px]"
                ):

                    image_or_fallback(
                        image,
                        component.icon,
                        (
                            f"Component "
                            f"{component.number} "
                            "visual space"
                        ),
                    )

            # ==================================================
            # LIVE CARLA DEMONSTRATION
            # ==================================================

            with ui.element("div").classes(
                "reserved-panel w-full mt-12"
            ):

                ui.icon(
                    "sensors",
                    size="48px",
                ).classes(
                    "text-cyan-7"
                )

                ui.label(
                    "COMPONENT 1 — LIVE CARLA DEMONSTRATION"
                ).classes(
                    "font-extrabold tracking-widest mt-3"
                )

                ui.label(
                    "Adaptive Intent Prediction in "
                    "Occluded Urban Scenarios"
                ).classes(
                    "text-lg font-semibold mt-2"
                )

                ui.label(
                    "Choose a controlled pedestrian test "
                    "scenario. The selected scenario controls "
                    "the CARLA test behaviour only; the "
                    "prediction and final learned policy "
                    "decision are produced by the actual model."
                ).classes(
                    "max-w-4xl text-center section-copy mt-3"
                )

                # ==================================================
                # STATUS
                # ==================================================

                status_label = ui.label(
                    "SELECT A TEST SCENARIO"
                ).classes(
                    "mt-6 text-lg font-bold text-cyan-8"
                )

                scenario_label = ui.label(
                    "Scenario: —"
                ).classes(
                    "text-sm opacity-70 mt-1"
                )

                # ==================================================
                # DISPLAY HELPERS
                # ==================================================

                async def show_waiting(
                    message: str,
                ):
                    safe_message = (
                        message
                        .replace("\\", "\\\\")
                        .replace('"', '\\"')
                    )

                    await ui.run_javascript(
                        f'''
                        const waiting =
                            document.getElementById(
                                "component1-waiting"
                            );

                        const frame =
                            document.getElementById(
                                "component1-live-frame"
                            );

                        if (frame) {{
                            frame.src = "about:blank";
                            frame.style.display = "none";
                        }}

                        if (waiting) {{
                            waiting.innerText =
                                "{safe_message}";

                            waiting.style.display =
                                "flex";
                        }}
                        '''
                    )

                async def show_live_stream():
                    # IMPORTANT:
                    # Use URL fragment (#) instead of query (?).
                    # The CARLA live server expects path "/".
                    # Fragments are not sent to the server.
                    stream_url = (
                        component1_live.stream_url
                        + f"/#t={int(time.time())}"
                    )

                    await ui.run_javascript(
                        f'''
                        const waiting =
                            document.getElementById(
                                "component1-waiting"
                            );

                        const frame =
                            document.getElementById(
                                "component1-live-frame"
                            );

                        if (waiting) {{
                            waiting.style.display =
                                "none";
                        }}

                        if (frame) {{
                            frame.src =
                                "{stream_url}";

                            frame.style.display =
                                "block";
                        }}
                        '''
                    )

                # ==================================================
                # START SCENARIO
                # ==================================================

                async def start_live_test(
                    scenario: str,
                ):
                    crossing_button.disable()
                    not_crossing_button.disable()

                    pretty_name = (
                        "CROSSING"
                        if scenario == "crossing"
                        else "NOT-CROSSING"
                    )

                    scenario_label.set_text(
                        f"Scenario: {pretty_name}"
                    )

                    status_label.set_text(
                        f"STARTING {pretty_name} TEST..."
                    )

                    await show_waiting(
                        "STARTING CARLA AND "
                        "LOADING THE TRAINED MODEL..."
                    )

                    try:
                        # ------------------------------------------
                        # WEBSITE -> SSH -> VAST.AI
                        # ------------------------------------------

                        ok, message = (
                            await asyncio.to_thread(
                                component1_live.start_scenario,
                                scenario,
                            )
                        )

                        if not ok:
                            raise RuntimeError(
                                message
                            )

                        status_label.set_text(
                            "REMOTE TEST STARTED — "
                            "WAITING FOR LIVE STREAM..."
                        )

                        # ------------------------------------------
                        # WAIT FOR VAST :8085
                        # THROUGH LOCAL SSH TUNNEL :8095
                        # ------------------------------------------

                        for _ in range(150):

                            ready = (
                                await asyncio.to_thread(
                                    component1_live.stream_ready
                                )
                            )

                            if ready:
                                status_label.set_text(
                                    f"{pretty_name} TEST — LIVE"
                                )

                                await show_live_stream()

                                ui.notify(
                                    (
                                        f"{pretty_name} "
                                        "CARLA test is live"
                                    ),
                                    type="positive",
                                )

                                return

                            running = (
                                await asyncio.to_thread(
                                    component1_live.is_running
                                )
                            )

                            if not running:
                                raise RuntimeError(
                                    "Remote CARLA runtime "
                                    "stopped before the live "
                                    "stream became ready. "
                                    "Check component1_live.log."
                                )

                            await asyncio.sleep(1)

                        raise RuntimeError(
                            "Timed out waiting for "
                            "the CARLA live stream."
                        )

                    except Exception as exc:
                        status_label.set_text(
                            "LIVE TEST ERROR"
                        )

                        await show_waiting(
                            f"ERROR: {exc}"
                        )

                        ui.notify(
                            str(exc),
                            type="negative",
                            timeout=8000,
                        )

                    finally:
                        crossing_button.enable()
                        not_crossing_button.enable()

                # ==================================================
                # BUTTON CALLBACKS
                # ==================================================

                async def crossing_test():
                    await start_live_test(
                        "crossing"
                    )

                async def not_crossing_test():
                    await start_live_test(
                        "not_crossing"
                    )

                async def stop_test():
                    crossing_button.disable()
                    not_crossing_button.disable()

                    status_label.set_text(
                        "STOPPING LIVE TEST..."
                    )

                    try:
                        await asyncio.to_thread(
                            component1_live.stop_scenario
                        )

                        await show_waiting(
                            "SELECT CROSSING OR "
                            "NOT-CROSSING TEST"
                        )

                        scenario_label.set_text(
                            "Scenario: —"
                        )

                        status_label.set_text(
                            "SELECT A TEST SCENARIO"
                        )

                        ui.notify(
                            "Component 1 live test stopped",
                            type="info",
                        )

                    finally:
                        crossing_button.enable()
                        not_crossing_button.enable()

                # ==================================================
                # CONTROL BUTTONS
                # ==================================================

                with ui.row().classes(
                    "w-full justify-center "
                    "gap-4 mt-6 flex-wrap"
                ):

                    crossing_button = ui.button(
                        "CROSSING TEST",
                        icon="directions_walk",
                        on_click=crossing_test,
                    ).props(
                        "unelevated"
                    ).classes(
                        "px-8 py-3"
                    )

                    not_crossing_button = ui.button(
                        "NOT-CROSSING TEST",
                        icon="person",
                        on_click=not_crossing_test,
                    ).props(
                        "outline"
                    ).classes(
                        "px-8 py-3"
                    )

                    ui.button(
                        "STOP",
                        icon="stop_circle",
                        on_click=stop_test,
                    ).props(
                        "flat color=negative"
                    ).classes(
                        "px-6 py-3"
                    )

                # ==================================================
                # LIVE DISPLAY
                # ==================================================

                ui.html(
                    '''
                    <div
                        id="component1-stream-container"
                        style="
                            width:100%;
                            margin-top:24px;
                        "
                    >

                        <div
                            id="component1-waiting"
                            style="
                                width:100%;
                                min-height:650px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                text-align:center;
                                border-radius:18px;
                                background:#07111d;
                                color:#8fa9bd;
                                font-family:
                                    Arial, sans-serif;
                                font-size:18px;
                                letter-spacing:1px;
                                padding:30px;
                                box-sizing:border-box;
                            "
                        >
                            SELECT CROSSING OR
                            NOT-CROSSING TEST
                        </div>

                        <iframe
                            id="component1-live-frame"
                            src="about:blank"
                            style="
                                display:none;
                                width:100%;
                                height:860px;
                                border:none;
                                border-radius:18px;
                                background:#07111d;
                            "
                            allow="autoplay"
                        ></iframe>

                    </div>
                    ''',
                    sanitize=False,
                ).classes(
                    "w-full"
                )

                # ==================================================
                # PIPELINE INFORMATION
                # ==================================================

                ui.label(
                    "LIVE INFERENCE PIPELINE"
                ).classes(
                    "font-bold text-cyan-8 mt-6"
                )

                ui.label(
                    "CARLA Front RGB → "
                    "Pedestrian Detection & Tracking → "
                    "Occlusion / Reliability Estimation → "
                    "30-Frame Temporal Evidence → "
                    "Transformer Intent Prediction → "
                    "Uncertainty Estimation → "
                    "Learned Agent Decision → "
                    "Vehicle Control"
                ).classes(
                    "max-w-5xl text-center "
                    "text-sm opacity-70 mt-2"
                )

                ui.label(
                    "The Crossing / Not-Crossing buttons "
                    "select only the controlled evaluation "
                    "scenario. Ground-truth intent, pedestrian "
                    "ID and bounding box are not supplied "
                    "to the prediction model."
                ).classes(
                    "max-w-4xl text-center "
                    "text-xs opacity-60 mt-3"
                )