# ============================================================
# CARLA WEB SERVER
# ============================================================

import asyncio
import json
import threading
import time
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from carla_app.streaming.video_stream import get_video_stream


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Agentic Federated Learning - CARLA Server",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SHARED VIDEO STREAM
# ============================================================

video_stream = get_video_stream()


# ============================================================
# SIMULATION STATE
# ============================================================

simulation_state = {
    "connected": False,
    "running": False,
    "vehicle": None,
    "current_sign": None,
    "current_class_id": None,
    "pipeline_status": "idle",
    "message": "CARLA server is waiting.",
    "timestamp": time.time(),
}


# ============================================================
# WEBSOCKET CLIENTS
# ============================================================

websocket_clients = set()
websocket_lock = threading.Lock()


# ============================================================
# STATE UPDATE
# ============================================================

def update_state(
    connected: Optional[bool] = None,
    running: Optional[bool] = None,
    vehicle: Optional[str] = None,
    current_sign: Optional[str] = None,
    current_class_id: Optional[int] = None,
    pipeline_status: Optional[str] = None,
    message: Optional[str] = None,
):
    """
    Update the shared simulation state.
    """

    if connected is not None:
        simulation_state["connected"] = connected

    if running is not None:
        simulation_state["running"] = running

    if vehicle is not None:
        simulation_state["vehicle"] = vehicle

    if current_sign is not None:
        simulation_state["current_sign"] = current_sign

    if current_class_id is not None:
        simulation_state["current_class_id"] = current_class_id

    if pipeline_status is not None:
        simulation_state["pipeline_status"] = pipeline_status

    if message is not None:
        simulation_state["message"] = message

    simulation_state["timestamp"] = time.time()


# ============================================================
# GET STATE
# ============================================================

def get_state():
    """
    Return a copy of the current simulation state.
    """

    return dict(simulation_state)


# ============================================================
# BROADCAST STATE
# ============================================================

async def broadcast_state():
    """
    Send the current state to all connected WebSocket clients.
    """

    if not websocket_clients:
        return

    message = json.dumps(get_state())

    disconnected = []

    for websocket in list(websocket_clients):

        try:
            await websocket.send_text(message)

        except Exception:
            disconnected.append(websocket)

    with websocket_lock:

        for websocket in disconnected:
            websocket_clients.discard(websocket)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    """
    Basic server information.
    """

    return {
        "name": "Agentic Federated Learning CARLA Server",
        "status": "online",
        "video_endpoint": "/video_feed",
        "process_endpoint": "/process",
        "latest_detection_endpoint": "/latest_detection",
        "pipeline_history_endpoint": "/pipeline_history",
        "status_endpoint": "/status",
        "health_endpoint": "/health",
        "websocket_endpoint": "/ws",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    """
    Health check.
    """

    return {
        "status": "ok",
        "server": "vast_ai",
        "video_stream_available": video_stream.has_frame(),
        "timestamp": time.time(),
    }


# ============================================================
# STATUS
# ============================================================

@app.get("/status")
async def status():
    """
    Return current simulation status.
    """

    return get_state()


# ============================================================
# MJPEG GENERATOR
# ============================================================

# If no new frame arrives (car stopped, camera paused), the
# last frame is re-sent this often so the connection stays
# alive and the browser keeps showing a picture.
KEEPALIVE_SECONDS = 1.0


async def mjpeg_generator():
    """
    Send JPEG frames to the browser.

    - Frames are already encoded by VideoStream (no work here).
    - Only NEW frames are sent, never the same frame twice in
      a row (except the 1-second keep-alive).
    - Always the LATEST frame: if the SSH tunnel is slow,
      older frames are skipped instead of piling up, so the
      video never falls behind.
    - async + asyncio.sleep: no server thread is blocked, and
      the loop ends by itself when the browser tab closes.
    """

    last_frame_id = -1
    last_sent_time = 0.0

    while True:

        jpeg_data, frame_id = video_stream.get_jpeg()
        now = time.time()

        if jpeg_data is None:
            await asyncio.sleep(0.05)
            continue

        is_new = frame_id != last_frame_id
        keepalive_due = (now - last_sent_time) >= KEEPALIVE_SECONDS

        if not is_new and not keepalive_due:
            await asyncio.sleep(0.01)
            continue

        last_frame_id = frame_id
        last_sent_time = now

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: "
            + str(len(jpeg_data)).encode()
            + b"\r\n\r\n"
            + jpeg_data
            + b"\r\n"
        )


# ============================================================
# VIDEO FEED
# ============================================================

@app.get("/video_feed")
async def video_feed():
    """
    Live MJPEG stream from CARLA.
    """

    return StreamingResponse(
        mjpeg_generator(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# MODEL FRAME (what YOLO sees)
# ============================================================

@app.get("/model_frame.jpg")
async def model_frame():
    
    from fastapi.responses import Response
    import cv2

    camera = getattr(_controller, "camera", None) if _controller else None
    frame = camera.get_front_frame_bgr() if camera is not None else None

    if frame is None:
        return Response(
            content=b"No front frame yet. Press Start on the website.",
            status_code=404,
            media_type="text/plain",
        )

    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        return Response(content=b"Encode failed", status_code=500, media_type="text/plain")

    return Response(
        content=encoded.tobytes(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store"},
    )


# ============================================================
# STREAM INFO (for checking video speed)
# ============================================================

@app.get("/stream_info")
async def stream_info():
    """
    Quick check: is the camera producing new frames?
    Call it twice a few seconds apart - frame_id should grow.
    """

    jpeg_data, frame_id = video_stream.get_jpeg()

    return {
        "has_frame": video_stream.has_frame(),
        "frame_id": frame_id,
        "jpeg_kb": round(len(jpeg_data) / 1024.0, 1) if jpeg_data else 0,
        "last_frame_age_seconds": (
            round(time.time() - video_stream.get_frame_timestamp(), 2)
            if video_stream.get_frame_timestamp() else None
        ),
    }


# ============================================================
# PROCESS COMMAND (supports both query params and JSON)
# ============================================================

@app.post("/process")
async def process_command(
    action: Optional[str] = Query(None),
    vehicle: Optional[str] = Query(None),
    command: Optional[dict] = None,
):
    """
    Receive commands from the Windows web page.

    Supports:
      - Query params: /process?action=start&vehicle=Vehicle_A
      - JSON body: { "action": "start", "vehicle": "Vehicle_A" }
    """

    # If JSON body is provided, use it
    if command:
        action = command.get("action")
        vehicle = command.get("vehicle")

    # If no action, use default
    if not action:
        return {
            "success": False,
            "message": "Missing 'action' parameter.",
        }

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if action == "start":

        vehicle_id = (vehicle or "Vehicle_A").replace(" ", "_")

        if _controller is None:
            return {
                "success": False,
                "action": "start",
                "message": "CARLA simulation is not ready yet.",
            }

        # Empty "Latest detection" and "History" right away.
        clear_pipeline_results()

        # Spawning takes a few seconds, so it runs in the
        # background. The website follows progress via /status
        # ("starting" -> "running", or "error").
        threading.Thread(
            target=_controller.start_run,
            args=(vehicle_id,),
            name="StartRun",
            daemon=True,
        ).start()

        await broadcast_state()

        return {
            "success": True,
            "action": "start",
            "vehicle": vehicle_id,
            "message": f"{vehicle_id} is starting.",
        }

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if action == "stop":

        if _controller is None:
            return {
                "success": False,
                "action": "stop",
                "message": "CARLA simulation is not ready yet.",
            }

        update_state(
            pipeline_status="stopping",
            message="Stopping...",
        )

        threading.Thread(
            target=_controller.stop_run,
            name="StopRun",
            daemon=True,
        ).start()

        await broadcast_state()

        return {
            "success": True,
            "action": "stop",
            "message": "Stop command received.",
        }

    # --------------------------------------------------------
    # BROADCAST (your KnowledgeBroadcastService, in the ML service)
    # --------------------------------------------------------

    if action == "broadcast":
        from carla_app.streaming import ml_client
        try:
            result = await run_in_threadpool(ml_client.broadcast)
        except Exception as error:
            update_state(pipeline_status="error", message=f"Broadcast error: {error}")
            await broadcast_state()
            return {"success": False, "action": "broadcast",
                    "message": f"Broadcast error: {error} (is the ML service running?)"}

        if result.get("success"):
            found = (result.get("result") or {}).get("pending_packages_found", 0)
            update_state(message=f"Broadcast completed. {found} package(s) found.")
        await broadcast_state()
        result["action"] = "broadcast"
        return result

    # --------------------------------------------------------
    # RETRAIN (your local_model_retraining.py, in the ML service)
    # --------------------------------------------------------

    if action == "retrain_status":
        from carla_app.streaming import ml_client
        info = await run_in_threadpool(ml_client.health)
        if info is None:
            return {"success": False, "action": "retrain_status", "retraining": {}}
        return {"success": True, "action": "retrain_status",
                "retraining": info.get("retraining", {})}

    if action == "retrain":
        from carla_app.streaming import ml_client
        vehicle_id = (vehicle or "Vehicle_A").replace(" ", "_")
        # Retraining uses the ML service fully for a few minutes,
        # so it is only allowed while no vehicle is driving.
        if get_state().get("running"):
            return {"success": False, "action": "retrain",
                    "message": "Stop the simulation first, then retrain."}
        try:
            result = await run_in_threadpool(ml_client.retrain, vehicle_id)
        except Exception as error:
            return {"success": False, "action": "retrain",
                    "message": f"Retrain error: {error} (is the ML service running?)"}
        result["action"] = "retrain"
        return result

    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    return {
        "success": False,
        "message": f"Unknown action: {action}",
    }


# ============================================================
# PIPELINE RESULTS: latest detection + history
# (same format as the old carla_sim api_server.py)
# ============================================================

MAX_PIPELINE_HISTORY = 100

latest_detection = None
pipeline_history = []
pipeline_results_lock = threading.Lock()

# Increases on every clear (every Start). A result still waiting
# for its display delay from an OLD run is then dropped.
_results_generation = 0


def _publish_pipeline_result(entry, generation):
    global latest_detection
    with pipeline_results_lock:
        if generation != _results_generation:
            return
        latest_detection = entry
        pipeline_history.insert(0, entry)
        del pipeline_history[MAX_PIPELINE_HISTORY:]


def record_pipeline_result(vehicle_label, item):
    from carla_app.config.simulation_config import DISPLAY_DELAY_SECONDS

    result = item.get("result") or {}
    verification = result.get("verification") or {}
    if not isinstance(verification, dict):
        verification = {}

    entry = {
        "sign_number": item.get("sign_number"),
        "vehicle": vehicle_label,
        "timestamp": time.time(),
        "status": result.get("status", "STOPPED"),
        "class_name": result.get("class_name"),
        "class_id": result.get("class_id"),
        "cnn_confidence": result.get("cnn_confidence"),
        "rl_decision": result.get("rl_decision"),
        "reward": result.get("reward"),
        "category": result.get("category"),
        "steps": result.get("steps", []),
        # Global verification (only when the sign was shared).
        "verification_status": verification.get("status"),
        "verified_class_id": verification.get("verified_class_id"),
        "verified_class_name": verification.get("verified_class_name"),
        "yolo_confidence": item.get("yolo_confidence"),
        "bbox": item.get("bbox"),
        "placed_sign": item.get("placed_sign"),
        # Cropped sign as base64 JPEG (in memory only).
        "crop_jpeg": item.get("crop_jpeg"),
    }

    update_state(
        current_sign=entry["class_name"],
        current_class_id=entry["class_id"],
    )

    timer = threading.Timer(DISPLAY_DELAY_SECONDS, _publish_pipeline_result,
                            args=(entry, _results_generation))
    timer.daemon = True
    timer.start()


def clear_pipeline_results():
    """Start pressed: empty "Latest detection" and "History"."""
    global latest_detection, _results_generation
    with pipeline_results_lock:
        _results_generation += 1
        latest_detection = None
        pipeline_history.clear()
    update_state(current_sign=None, current_class_id=None)
    simulation_state["current_sign"] = None
    simulation_state["current_class_id"] = None


@app.get("/latest_detection")
async def get_latest_detection():
    with pipeline_results_lock:
        return {"latest": latest_detection}


@app.get("/pipeline_history")
async def get_pipeline_history():
    with pipeline_results_lock:
        return {"history": list(pipeline_history)}


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket connection for live simulation status.
    """

    await websocket.accept()

    with websocket_lock:
        websocket_clients.add(websocket)

    try:

        # Send current state immediately
        await websocket.send_text(
            json.dumps(get_state())
        )

        while True:

            message = await websocket.receive_text()

            try:
                data = json.loads(message)

            except json.JSONDecodeError:

                await websocket.send_text(
                    json.dumps(
                        {
                            "success": False,
                            "message": "Invalid JSON.",
                        }
                    )
                )

                continue

            action = data.get("action")

            if action == "ping":

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "timestamp": time.time(),
                        }
                    )
                )

            elif action == "get_status":

                await websocket.send_text(
                    json.dumps(get_state())
                )

    except WebSocketDisconnect:

        pass

    except Exception:

        pass

    finally:

        with websocket_lock:
            websocket_clients.discard(websocket)


# ============================================================
# CARLA STATE FUNCTIONS
# ============================================================

# The CarlaSimulation object from run_simulation.py.
# Start / Stop on the website call its start_run() / stop_run().
_controller = None


def set_controller(controller):
    """
    Called by run_simulation.py after CARLA is connected.
    """

    global _controller
    _controller = controller


def set_carla_connected(connected: bool):
    """
    Called by run_simulation.py when CARLA connects/disconnects.
    """

    update_state(
        connected=connected,
        message=(
            "CARLA connected."
            if connected
            else "CARLA disconnected."
        ),
    )


def set_vehicle(vehicle: str):
    """
    Set active vehicle.
    """

    update_state(
        vehicle=vehicle,
        message=f"{vehicle} selected.",
    )


def set_detected_sign(
    class_id: int,
    class_name: str,
):
    """
    Update detected traffic sign information.
    """

    update_state(
        current_class_id=class_id,
        current_sign=class_name,
        pipeline_status="sign_detected",
        message=(
            f"Detected traffic sign: {class_name}"
        ),
    )


def set_pipeline_status(
    status: str,
    message: str,
):
    """
    Update ML pipeline status.
    """

    update_state(
        pipeline_status=status,
        message=message,
    )


# ============================================================
# SERVER START MESSAGE
# ============================================================

print("=" * 60)
print("Agentic Federated Learning - CARLA Web Server")
print("=" * 60)
print("[OK] FastAPI application loaded")
print("[OK] Shared VideoStream connected")
print("[OK] /video_feed available")
print("[OK] /stream_info available")
print("[OK] /model_frame.jpg available")
print("[OK] /process available")
print("[OK] /status available")
print("[OK] /health available")
print("[OK] /ws available")
print("[OK] /latest_detection available")
print("[OK] /pipeline_history available")
print("=" * 60)