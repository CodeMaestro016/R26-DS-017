"""Component 3 -- Proactive Social Compliance Modeling (live CARLA demo).

Split into its own file (mirroring pages/component2_results.py's split for
Component 2) since this is a substantial, self-contained piece: a native
scenario picker, live video, and prediction HUD that talk directly to
web_launcher.py and carla_live_demo.py over HTTP (see
services/carla_bridge.py) -- no iframe, no separate standalone page.

Scenario cards are labelled "Scenario 1", "Scenario 2", etc. rather than
by behavior name -- deliberately blind, so watching the live prediction
is the only way to tell what's happening, matching the labelling already
used in the standalone index.html.
"""

import time

from nicegui import run, ui

from socialmind_drive_showcase.config import COMPONENT3_LAUNCHER_URL, SHOWCASE_ROOT
from socialmind_drive_showcase.services.carla_bridge import (fetch_launcher_status,
    fetch_live_state, fetch_scenarios, launch_scenario, stop_scenario, stream_image_url)
from socialmind_drive_showcase.services.live_demo_status import is_live_demo_reachable
from socialmind_drive_showcase.ui.reusable import image_or_fallback, section_heading


# Component 3's Theory-of-Mind pipeline: CARLA sensor data through to the
# vehicle's action. None of this runs locally -- it describes what's
# happening on the other end of COMPONENT3_LAUNCHER_URL / STREAM_URL.
#
# NOTE: pose input comes from a SEPARATE, dedicated pedestrian-tracking
# camera, not the ego/dashboard camera this page's own video feed shows.
# The dashboard camera stays fixed forward the whole scenario (that's
# the only feed ever streamed here); the tracking camera continuously
# aims at the pedestrian instead, purely to keep MediaPipe's input
# centered and well-framed, and is never displayed anywhere. Also added
# the rule-based override stage: a small set of explainable safety-net
# rules (e.g. sustained near-zero motion -> Waiting, crossing far from
# any marked crosswalk -> Jaywalk) that catch specific, well-understood
# cases where the ensemble's own prediction is unreliable, before the
# TTC-based agent acts on it -- itself a neuro-symbolic pattern worth
# surfacing, not just an implementation detail.
COMPONENT3_FLOW = ("CARLA Simulation", "Pedestrian-Tracking Camera", "MediaPipe Pose Landmarks",
        "36-Feature Motion Encoding", "LSTM + GRU Ensemble", "Mental-State Prediction",
        "Rule-Based Safety Overrides", "Rule-Based Agent", "Vehicle Action (Maintain / Slow / Stop)")
COMPONENT3_STATES = ("Waiting", "Hesitant", "Committed", "Distracted", "Aggressive", "Jaywalk")

# Live-demo panel styling: matches index.html's own dark navy/cyan theme
# exactly (same hex values, same JetBrains Mono / Inter fonts) so the
# instrument-panel part of this page looks identical to the standalone
# site instead of the showcase's own light theme. Kept self-contained
# here (not in ui/theme.py) so this whole feature lives in one file.
_CARLA_PANEL_CSS = """
.carla-live-panel { background:#0a1420; border:1px solid #1c2e3f; border-radius:18px; padding:28px; color:#e6ecf1; font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; }
.carla-scenario-card { background:#10202f; border:1px solid #1c2e3f; border-radius:10px; padding:16px 18px; min-width:220px; flex:1 1 220px; box-shadow:0 1px 0 rgba(0,0,0,.2),0 4px 12px rgba(0,0,0,.18); transition:border-color .15s ease; }
.carla-scenario-card .font-bold { color:#fff; }
.carla-scenario-card.active { border-color:#3fb8d6; }
.carla-video-frame { position:relative; width:100%; aspect-ratio:16/9; border-radius:10px; overflow:hidden; background:#050c14; border:1px solid #1c2e3f; }
.carla-video-frame img { width:100%; height:100%; object-fit:cover; display:block; }
.carla-no-signal { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#7c8fa0; font-family:'JetBrains Mono',ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }
.carla-stat { background:#10202f; border:1px solid #1c2e3f; border-radius:7px; padding:10px 14px; min-width:110px; }
.carla-stat .carla-stat-label { font-size:.62rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#7c8fa0; }
.carla-stat .carla-stat-value { font-family:'JetBrains Mono',ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace; font-size:1rem; font-weight:600; color:#fff; }
.carla-log { background:#0b1a28; color:#c8d6e0; border-radius:8px; padding:14px 16px; font-family:'JetBrains Mono',ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace; font-size:.75rem; max-height:160px; overflow-y:auto; border:1px solid #1c2e3f; }
.carla-live-panel .text-red-7 { color:#d6685f !important; }
.carla-live-panel .text-blue-grey-6 { color:#7c8fa0 !important; }
.carla-live-panel .metric-label { color:#7c8fa0; }
.carla-run-btn { color:#9fc4d2 !important; border-color:#1c2e3f !important; }
.carla-run-btn:hover { color:#3fb8d6 !important; border-color:#3fb8d6 !important; }
.carla-stop-btn { color:#d6685f !important; border-color:#d6685f !important; }
"""


def _inject_carla_styles():
    ui.add_head_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&'
        'family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">')
    ui.add_css(_CARLA_PANEL_CSS)


def component3_page(component):
    _inject_carla_styles()
    image = SHOWCASE_ROOT / "assets" / "images" / component.image_name
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            with ui.row().classes("w-full gap-10 items-center"):
                with ui.column().classes("grow min-w-[320px]"):
                    section_heading(
                        "RESEARCH OBJECTIVE",
                        "Anticipating pedestrian intent before it becomes unambiguous",
                        "Models the likely mental state of pedestrians and other road users -- "
                        "whether they are waiting, hesitant, committed to crossing, distracted, "
                        "moving aggressively, or jaywalking -- so the ego vehicle can reason about "
                        "their expectations and respond before intent becomes visually unambiguous.")
                    with ui.row().classes("mt-6 gap-3"):
                        ui.button("Check Connection", icon="refresh",
                                  on_click=_component3_status.refresh).props("outline no-caps")
                with ui.element("div").classes("grow min-w-[320px]"):
                    image_or_fallback(image, "psychology", "Live pedestrian-intent perception")
            _component3_status()
            with ui.element("div").classes("info-grid mt-10"):
                for label, value, icon in (
                        ("LIVE DEMO", "Available", "play_circle"),
                        ("MENTAL STATES MODELED", "6", "psychology"),
                        ("PREDICTION WINDOW", "30 frames", "timeline"),
                        ("EXECUTION", "Rule-Based Agent", "device_hub"),
                        ("PERCEPTION", "Pose-Based", "visibility")):
                    with ui.element("div").classes("info-card"):
                        ui.icon(icon).classes("text-cyan-7")
                        ui.label(label).classes("metric-label")
                        ui.label(value).classes("font-bold text-xl mt-1")
    with ui.element("section").classes("section section-dark w-full"):
        with ui.column().classes("page-shell"):
            section_heading(
                "SYSTEM OVERVIEW",
                "From onboard perception to a socially-aware driving decision",
                "A dedicated pedestrian-tracking camera -- separate from the fixed, forward-facing "
                "camera this page's own video shows -- feeds a pose-based motion encoder and a "
                "temporal ensemble classifier. A small layer of explainable, rule-based overrides "
                "then catches specific cases the ensemble is known to get wrong before a "
                "rule-based Theory-of-Mind agent decides the vehicle's action.")
            with ui.element("div").classes("architecture-flow"):
                for node in COMPONENT3_FLOW:
                    ui.label(node).classes("flow-node")
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            section_heading("LIVE DEMONSTRATION",
                             "Run a scenario and watch the prediction pipeline live")
            _live_demo_panel()


@ui.refreshable
def _component3_status():
    reachable = is_live_demo_reachable(COMPONENT3_LAUNCHER_URL)
    color = "text-green-7" if reachable else "text-red-7"
    text = "REACHABLE" if reachable else "NOT REACHABLE"
    with ui.row().classes("items-center mt-5 gap-2"):
        ui.icon("circle", size="12px").classes(color)
        ui.label(f"CONNECTION · {text}").classes("font-bold tracking-wider")
        ui.label(COMPONENT3_LAUNCHER_URL).classes("text-blue-grey-6 text-sm")
        if not reachable:
            ui.label("Start web_launcher.py and your SSH tunnel, then check again.").classes("text-red-7 text-sm")


def _live_demo_panel():
    """Native scenario picker + live video + prediction HUD, built with this
    app's own components -- talks to web_launcher.py and carla_live_demo.py
    directly over HTTP (see services/carla_bridge.py) rather than loading
    the standalone index.html in an iframe. Matches index.html's own dark
    navy/cyan theme AND layout (two-column split, HUD/confidence bar
    overlaid directly on the video, 4-stat grid, progress bar) -- see
    .carla-* in ui/theme.py -- since this panel IS the live simulator
    view, not general page content."""
    state = {"scenario_id": None, "scenarios": None, "scenarios_error": None, "video_started": False}

    with ui.element("div").classes("carla-live-panel mt-6").style("width:100%;"):
        with ui.row().classes("carla-live-grid no-wrap").style("align-items:flex-start; width:100%;"):
            # ---- LEFT: scenario picker ----
            with ui.column().classes("carla-scenario-panel gap-4") \
                    .style("flex:0 0 320px; align-items:stretch;"):
                ui.label("SCENARIO SUITE").classes("carla-hud-label")
                ui.label("Choose a behavior to run").classes("font-bold").style("color:#fff;")
                card_list = ui.column().classes("gap-4 w-full").style("align-items:stretch;")

            # ---- RIGHT: video + HUD + stats + log ----
            with ui.column().classes("carla-stage grow") \
                    .style("flex:1 1 0%; min-width:0; align-items:stretch;"):
                error_label = ui.label("").classes("carla-error-text text-sm")
                error_label.visible = False

                with ui.element("div").classes("carla-video-frame"):
                    no_signal = ui.label("No signal -- select a scenario to begin").classes("carla-no-signal")
                    video_html = ui.html("")

                    with ui.element("div").classes("carla-hud-readout") as hud_readout:
                        with ui.element("div").classes("carla-hud-chip"):
                            ui.label("Predicted").classes("carla-hud-label")
                            pred_value = ui.label("--").classes("carla-hud-value")
                    hud_readout.visible = False

                    with ui.element("div").classes("carla-confidence-wrap") as conf_wrap:
                        ui.label("CONF").classes("carla-confidence-label")
                        with ui.element("div").classes("carla-confidence-bar"):
                            conf_fill = ui.element("div").classes("carla-confidence-fill")
                        conf_pct_label = ui.label("0%").classes("carla-confidence-label")
                    conf_wrap.visible = False

                with ui.element("div").classes("carla-decision-row"):
                    def _stat(label_text):
                        with ui.element("div").classes("carla-stat"):
                            ui.label(label_text).classes("carla-stat-label")
                            value_label = ui.label("--").classes("carla-stat-value")
                        return value_label

                    action_value = _stat("Action")
                    ttc_value = _stat("Time to collision")
                    dist_value = _stat("Distance")
                    elapsed_value = _stat("Elapsed")

                with ui.element("div").classes("carla-progress"):
                    progress_fill = ui.element("div").classes("carla-progress-fill")

                message_label = ui.label("Waiting to start.").classes("carla-message-line")

                ui.label("Event log").classes("carla-log-heading")
                log_panel = ui.column().classes("carla-log gap-1")

        def show_video():
            # carla_live_demo.py takes a few seconds after launch to connect
            # to CARLA, spawn the vehicle, and start its own dashboard server
            # on port 8093 -- if the browser requests the stream before that's
            # ready it gets ERR_CONNECTION_RESET. Retry with a fresh
            # cache-busting timestamp instead of giving up on the first
            # failure (matches index.html's own retry behavior, which this
            # native panel was missing).
            base_url = stream_image_url()
            initial_url = stream_image_url(time.time())
            onerror_js = (
                "const img=this; const tries=parseInt(img.dataset.tries||'0'); "
                "if (tries < 40 && document.body.contains(img)) { "
                "img.dataset.tries = tries + 1; "
                "setTimeout(() => { if (document.body.contains(img)) { "
                "img.src = img.dataset.base + '?_=' + Date.now(); } }, 1500); }"
            )
            video_html.set_content(
                f'<img src="{initial_url}" data-base="{base_url}" data-tries="0" '
                f'onerror="{onerror_js}" '
                f'style="width:100%;height:100%;object-fit:cover;display:block;">')
            no_signal.visible = False
            hud_readout.visible = True
            conf_wrap.visible = True

        def hide_video():
            video_html.set_content("")
            no_signal.visible = True
            hud_readout.visible = False
            conf_wrap.visible = False

        def reset_idle():
            state["scenario_id"] = None
            state["video_started"] = False
            hide_video()
            message_label.set_text("Waiting to start.")
            progress_fill.style(replace="width:0%")
            render_buttons.refresh()

        async def do_run(scenario_id):
            error_label.visible = False
            # Offloaded to a worker thread -- web_launcher.py's /api/launch can
            # block for up to ~90s the first time (waiting for the pose/ensemble
            # model servers to come up). Calling it directly here would freeze
            # this ENTIRE app (all pages, all users) for that whole window,
            # since NiceGUI's event handlers run on the single shared event loop.
            ok, error = await run.io_bound(launch_scenario, scenario_id)
            if not ok:
                error_label.set_text(error or "Could not launch scenario.")
                error_label.visible = True
                return
            state["scenario_id"] = scenario_id
            # Deliberately NOT calling show_video() here -- /api/launch only
            # confirms the scenario PROCESS was spawned, not that CARLA has
            # connected and the camera is attached yet. Starting the video
            # connection this early means its first several retry attempts
            # are guaranteed to fail (nothing is serving frames yet), each
            # one burning 1.5s of retry budget against the scenario's fixed
            # ~16s runtime -- on a slower-to-start run that can eat enough
            # of the window that video never gets a real chance to connect
            # at all, even though /state polling (independent of this) keeps
            # working the whole time. poll() below starts the video once
            # /state actually confirms the camera is running.
            render_buttons.refresh()

        async def do_stop():
            await run.io_bound(stop_scenario)
            reset_idle()

        @ui.refreshable
        def render_buttons():
            # Renders purely from cached state["scenarios"] -- no network
            # call here. It used to call fetch_scenarios() directly, which
            # made every do_run/do_stop/reset_idle refresh a blocking
            # urllib call on the shared event loop (same class of bug as
            # poll() had before it was offloaded). The scenario LIST itself
            # never changes at runtime anyway -- only which card is
            # "active" does, and that only needs state["scenario_id"].
            if state["scenarios_error"]:
                ui.label(f"Could not load scenario list: {state['scenarios_error']}") \
                    .classes("carla-error-text text-sm")
                ui.button("Retry", on_click=load_scenarios).props("outline no-caps dense").classes("carla-run-btn")
                return
            if state["scenarios"] is None:
                ui.label("Loading scenarios...").classes("carla-muted-text text-sm")
                return
            for index, scenario in enumerate(state["scenarios"]):
                is_active = scenario["id"] == state["scenario_id"]
                card_classes = "carla-scenario-card active" if is_active else "carla-scenario-card"
                with ui.element("div").classes(card_classes) \
                        .style("flex:0 0 auto; align-self:stretch; height:auto; width:100%;"):
                    # Deliberately generic -- see module docstring. scenario["behavior"]
                    # and scenario["true_state"] exist in the data but are never shown here.
                    ui.label(f"Scenario {index + 1}").classes("font-bold")
                    ui.label(scenario["description"]).classes("text-xs carla-muted-text")
                    if is_active:
                        ui.button("Stop", on_click=do_stop) \
                            .props("outline no-caps dense").classes("carla-stop-btn")
                    else:
                        ui.button("Run scenario", on_click=lambda sid=scenario["id"]: do_run(sid)) \
                            .props("outline no-caps dense").classes("carla-run-btn")

        async def load_scenarios():
            # The one place this panel actually fetches the scenario list --
            # offloaded for the same reason as everything else here (a slow
            # tunnel shouldn't be able to stall the whole app).
            scenarios, error = await run.io_bound(fetch_scenarios)
            state["scenarios"] = scenarios if not error else None
            state["scenarios_error"] = error
            render_buttons.refresh()

        with card_list:
            render_buttons()
        ui.timer(0.01, load_scenarios, once=True)

        async def poll():
            # Offloaded to a worker thread for the same reason as do_run/do_stop
            # above -- these are blocking urllib calls (up to a few seconds each
            # if the SSH tunnel is slow), and this runs every 1.5s on a shared
            # timer. Calling them directly would stall the ENTIRE app's event
            # loop (every page, every open tab) for that whole window each tick,
            # not just this one panel -- easily enough to make a websocket look
            # dead and get dropped on a slow or flaky tunnel.
            status, _ = await run.io_bound(fetch_launcher_status)
            if status is not None:
                if not status.get("demo_running") and state["scenario_id"]:
                    reset_idle()
                if status.get("last_launch_error"):
                    error_label.set_text(status["last_launch_error"])
                    error_label.visible = True

            if not state["scenario_id"]:
                return

            live, _ = await run.io_bound(fetch_live_state)
            if live is None:
                return

            # Start the video connection the moment /state confirms the
            # camera is actually attached -- carla_live_demo.py sets
            # phase="running" right after camera.listen(), well before the
            # scenario's own pedestrian/vehicle logic even begins. Waiting
            # for this (instead of starting on launch, see do_run() above)
            # means the first connection attempt lands right when it's
            # actually likely to succeed, rather than burning retries on
            # attempts guaranteed to fail before a frame exists.
            #
            # Re-checking state["scenario_id"] here (not just at the top of
            # poll()) guards a real race: if do_stop()/reset_idle() runs
            # concurrently while this fetch_live_state() call is in flight,
            # state gets cleared mid-poll, and without this check we'd
            # resume with a stale, already-obsolete `live` payload and
            # incorrectly re-trigger the video right after hide_video()
            # just cleared it.
            if (state["scenario_id"] and not state["video_started"]
                    and live.get("phase") in ("running", "finished")):
                show_video()
                state["video_started"] = True

            pred_value.set_text(live.get("predicted_label") or "--")

            action = live.get("action")
            action_value.set_text(action or "--")
            action_value.classes(replace=f"carla-stat-value action-{action}" if action else "carla-stat-value")

            confidence = live.get("confidence")
            conf_pct = round(confidence * 100) if confidence is not None else 0
            conf_fill.style(replace=f"width:{conf_pct}%")
            conf_pct_label.set_text(f"{conf_pct}%")

            ttc = live.get("ttc_s")
            ttc_value.set_text(f"{ttc:.1f}s" if ttc is not None else "--")
            distance = live.get("distance_m")
            dist_value.set_text(f"{distance:.1f}m" if distance is not None else "--")
            elapsed = live.get("elapsed_s") or 0.0
            elapsed_value.set_text(f"{elapsed:.1f}s")

            duration = live.get("duration_s")
            progress_pct = min(100, (elapsed / duration) * 100) if duration else 0
            progress_fill.style(replace=f"width:{progress_pct}%")

            message_label.set_text(live.get("message") or "")

            log_panel.clear()
            with log_panel:
                for entry in reversed(live.get("log", [])[-10:]):
                    with ui.row().classes("carla-log-line gap-2"):
                        ui.label(entry.get("message", ""))

            if live.get("finished"):
                reset_idle()

        ui.timer(1.5, poll)