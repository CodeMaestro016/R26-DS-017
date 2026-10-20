# ============================================================
# component_4/ml_service.py
# ============================================================

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""   # same as the vehicle pipelines

import sys
import time
import queue
import threading
import traceback
import importlib.util
import multiprocessing as mp

import base64
import json

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, Request, Query
from starlette.concurrency import run_in_threadpool


COMPONENT_4_DIR = os.path.dirname(os.path.abspath(__file__))
VEHICLES_DIR = os.path.join(COMPONENT_4_DIR, "vehicles")
os.chdir(COMPONENT_4_DIR)
if COMPONENT_4_DIR not in sys.path:
    sys.path.insert(0, COMPONENT_4_DIR)

HOST = "127.0.0.1"
PORT = 8020

YOLO_CONFIDENCE = 0.25

# Ignore YOLO boxes smaller than this (pixels, width AND height).
# Far-away signs are tiny and blurry; a sign is processed once,
# as soon as it is big enough for the CNN to read it properly.
MIN_SIGN_SIZE_PX = 40

# The cropped sign is sent back (in memory, never saved to disk)
# for the website, at most this many pixels wide/high.
CROP_PREVIEW_MAX_PX = 160

# All three vehicles use the same YOLO file (identical checksum).
YOLO_MODEL_PATH = os.path.join(
    COMPONENT_4_DIR, "vehicles", "vehicle_A", "models",
    "generic_traffic_sign_detector_best.pt",
)

VEHICLES = {
    "Vehicle_A": {"folder": "vehicle_A", "retrainer": "VehicleALocalModelRetrainer"},
    "Vehicle_B": {"folder": "vehicle_B", "retrainer": "VehicleBLocalModelRetrainer"},
    "Vehicle_C": {"folder": "vehicle_C", "retrainer": "VehicleCLocalModelRetrainer"},
}


def vehicle_id_from(text):
    """'Vehicle_A', 'Vehicle A', 'A' -> 'Vehicle_A'."""
    if not text:
        return None
    vehicle_id = "Vehicle_" + str(text).strip()[-1].upper()
    return vehicle_id if vehicle_id in VEHICLES else None


def vehicle_dir(vehicle_id):
    return os.path.join(VEHICLES_DIR, VEHICLES[vehicle_id]["folder"])


# ============================================================
# YOLO WORKER PROCESS (old carla_sim/core/yolo_worker_process.py)
# ============================================================

def yolo_worker(frame_queue, result_queue, model_path, conf_threshold):
    """
    Runs in its own process. Loads YOLO once, then: frame in ->
    detections out. Exits when it receives None.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    from ultralytics import YOLO

    model = YOLO(model_path)
    model.to("cpu")
    print("[YOLO worker] Ready.")

    while True:
        try:
            frame = frame_queue.get(timeout=0.5)
        except Exception:
            continue
        if frame is None:
            break

        try:
            results = model(frame, conf=conf_threshold, verbose=False)
        except Exception as error:
            print("[YOLO worker] Inference error:", error)
            result_queue.put([])
            continue

        detections = []
        if results and results[0].boxes is not None:
            h, w = frame.shape[:2]
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1, y1 = max(0, min(x1, w - 1)), max(0, min(y1, h - 1))
                x2, y2 = max(0, min(x2, w)), max(0, min(y2, h))
                if x2 <= x1 or y2 <= y1:
                    continue
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "yolo_confidence": float(box.conf[0]),
                    "cropped_sign": crop,
                    "visual_prominence": (x2 - x1) * (y2 - y1) / float(w * h),
                })
        result_queue.put(detections)

    print("[YOLO worker] Exiting.")


yolo = {"process": None, "frames": None, "results": None}


def start_yolo_worker():
    # "spawn" = a completely fresh Python for YOLO, sharing
    # nothing with TensorFlow in this process.
    ctx = mp.get_context("spawn")
    yolo["frames"] = ctx.Queue(maxsize=2)
    yolo["results"] = ctx.Queue(maxsize=2)
    yolo["process"] = ctx.Process(
        target=yolo_worker,
        args=(yolo["frames"], yolo["results"], YOLO_MODEL_PATH, YOLO_CONFIDENCE),
        daemon=True,
    )
    yolo["process"].start()
    print("[ML] YOLO worker process started.")


def run_yolo(frame):
    """Send one frame to the YOLO process and wait for detections."""
    if yolo["process"] is None or not yolo["process"].is_alive():
        raise RuntimeError("YOLO worker process is not running.")
    while True:                       # drop any old, unread result
        try:
            yolo["results"].get_nowait()
        except queue.Empty:
            break
    yolo["frames"].put(frame, timeout=2.0)
    return yolo["results"].get(timeout=15.0)


# ============================================================
# NEW-SIGN CHECK (same idea as the old SignTracker)
# ============================================================
# The same physical sign is visible in several frames. A detection
# whose box centre is within 80 px of a sign seen in the last
# 2 seconds is the same sign, and is not processed again.

class SignTracker:
    def __init__(self, match_distance_pixels=80, max_missed_seconds=2.0):
        self.match_distance_pixels = match_distance_pixels
        self.max_missed_seconds = max_missed_seconds
        self.tracked = []

    def is_new_sign(self, bbox):
        now = time.time()
        self.tracked = [s for s in self.tracked if now - s["last_seen"] <= self.max_missed_seconds]
        cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0
        for sign in self.tracked:
            if ((cx - sign["x"]) ** 2 + (cy - sign["y"]) ** 2) ** 0.5 <= self.match_distance_pixels:
                sign["x"], sign["y"], sign["last_seen"] = cx, cy, now
                return False
        self.tracked.append({"x": cx, "y": cy, "last_seen": now})
        return True

    def reset(self):
        self.tracked = []


# ============================================================
# KEEP VEHICLES A / B / C SEPARATE
# ============================================================
# All three vehicles import "from src.xxx import ...", and the
# pipeline imports src.rl_agent / src.importance_score while it
# runs. Python remembers imports by name, so without this,
# Vehicle B could end up using Vehicle A's src modules.

_saved_src_modules = {}


def _is_vehicle_src(name, module):
    if name.startswith("vehicle_main_"):
        return False
    if name == "src" or name.startswith("src."):
        return True
    path = getattr(module, "__file__", None)
    return bool(path) and os.path.abspath(path).startswith(VEHICLES_DIR + os.sep)


def use_vehicle(vehicle_id):
    """Point `src` and sys.path at this vehicle only."""
    for name in [n for n, m in list(sys.modules.items()) if _is_vehicle_src(n, m)]:
        del sys.modules[name]
    sys.modules.update(_saved_src_modules.get(vehicle_id, {}))

    all_paths = set()
    for vid in VEHICLES:
        all_paths.update({vehicle_dir(vid), os.path.join(vehicle_dir(vid), "src")})
    sys.path[:] = [p for p in sys.path if p not in all_paths]
    sys.path.insert(0, os.path.join(vehicle_dir(vehicle_id), "src"))
    sys.path.insert(0, vehicle_dir(vehicle_id))
    importlib.invalidate_caches()


def save_vehicle(vehicle_id):
    _saved_src_modules[vehicle_id] = {
        n: m for n, m in list(sys.modules.items()) if _is_vehicle_src(n, m)
    }


# ============================================================
# STATE
# ============================================================

app = FastAPI(title="Component 4 ML Service")
lock = threading.Lock()
tracker = SignTracker()

state = {
    "active_vehicle": None,
    "processed_sign_ids": set(),   # roadside signs already processed this run
    "pipelines": {},      # vehicle_id -> main module
    "loads": 0,
    "sign_counter": 0,
    "frames": 0,
    "retraining": {},
    "last_error": None,
}


def get_pipeline(vehicle_id):
    """Load the vehicle's main.py once, then reuse."""
    use_vehicle(vehicle_id)
    if vehicle_id in state["pipelines"]:
        return state["pipelines"][vehicle_id]

    state["loads"] += 1
    name = "vehicle_main_{}_{}".format(VEHICLES[vehicle_id]["folder"], state["loads"])
    spec = importlib.util.spec_from_file_location(name, os.path.join(vehicle_dir(vehicle_id), "main.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    module.initialize_pipeline()

    save_vehicle(vehicle_id)
    state["pipelines"][vehicle_id] = module
    return module


def json_safe(value):
    """Remove images/arrays so the result can be sent as JSON."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items() if not isinstance(v, np.ndarray)}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "yolo_worker_alive": bool(yolo["process"] and yolo["process"].is_alive()),
        "active_vehicle": state["active_vehicle"],
        "loaded_vehicles": list(state["pipelines"].keys()),
        "frames_processed": state["frames"],
        "signs_processed": state["sign_counter"],
        "retraining": state["retraining"],
        "last_error": state["last_error"],
    }


@app.post("/load")
def load(vehicle: str = Query(...)):
    """Start pressed: load (first time only) and select a vehicle."""
    vehicle_id = vehicle_id_from(vehicle)
    if vehicle_id is None:
        return {"success": False, "message": "Unknown vehicle: {}".format(vehicle)}
    if state["retraining"].get(vehicle_id) == "running":
        return {"success": False, "message": "{} is retraining.".format(vehicle_id)}

    started = time.time()
    with lock:
        try:
            get_pipeline(vehicle_id)
        except Exception as error:
            traceback.print_exc()
            state["last_error"] = str(error)
            return {"success": False, "message": "Failed to load {}: {}".format(vehicle_id, error)}
        state["active_vehicle"] = vehicle_id
        state["sign_counter"] = 0
        state["frames"] = 0
        state["processed_sign_ids"] = set()
        tracker.reset()

    seconds = round(time.time() - started, 1)
    print("[ML] Active vehicle: {} ({} s)".format(vehicle_id, seconds))
    return {"success": True, "vehicle": vehicle_id, "seconds": seconds,
            "message": "{} pipeline ready.".format(vehicle_id.replace("_", " "))}


@app.post("/unload")
def unload():
    """Stop pressed."""
    with lock:
        state["active_vehicle"] = None
        state["processed_sign_ids"] = set()
        tracker.reset()
    return {"success": True}


def crop_to_jpeg_b64(crop):
    """Small JPEG of the cropped sign, as text (nothing saved)."""
    if crop is None or crop.size == 0:
        return None
    h, w = crop.shape[:2]
    scale = CROP_PREVIEW_MAX_PX / float(max(h, w))
    if scale < 1.0:
        crop = cv2.resize(crop, (max(1, int(w * scale)), max(1, int(h * scale))),
                          interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(encoded.tobytes()).decode("ascii") if ok else None


def match_roadside_sign(bbox, sign_boxes):
    """
    Which roadside sign (from the simulation) is this YOLO box on?
    Returns the sign dict, or None if it is not one of our signs.
    """
    cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0
    best, best_distance = None, None
    for sign in sign_boxes:
        x1, y1, x2, y2 = sign["bbox"]
        pad_x, pad_y = (x2 - x1) * 0.3 + 5, (y2 - y1) * 0.3 + 5
        if x1 - pad_x <= cx <= x2 + pad_x and y1 - pad_y <= cy <= y2 + pad_y:
            distance = abs(cx - (x1 + x2) / 2.0) + abs(cy - (y1 + y2) / 2.0)
            if best is None or distance < best_distance:
                best, best_distance = sign, distance
    return best


def handle_frame(jpeg_bytes, frame_number, sign_boxes=None):
    vehicle_id = state["active_vehicle"]
    if vehicle_id is None:
        return {"success": False, "message": "No vehicle selected.", "detections": [], "results": []}

    frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return {"success": False, "message": "Bad image.", "detections": [], "results": []}

    with lock:
        module = get_pipeline(vehicle_id)
        state["frames"] += 1

        # 1. YOLO (separate process)
        try:
            signs = run_yolo(frame)
        except Exception as error:
            state["last_error"] = "YOLO: {}".format(error)
            return {"success": False, "message": state["last_error"],
                    "detections": [], "results": []}

        detections, results = [], []
        for sign in signs:
            x1, y1, x2, y2 = sign["bbox"]
            box = {
                "bbox": [int(v) for v in sign["bbox"]],
                "yolo_confidence": round(float(sign.get("yolo_confidence", 0.0)), 4),
                "is_new": False,
                "reason": "",
                "sign_id": None,
            }
            detections.append(box)

            # 2a. Too small (far away): wait until it is bigger.
            if (x2 - x1) < MIN_SIGN_SIZE_PX or (y2 - y1) < MIN_SIGN_SIZE_PX:
                box["reason"] = "too_small"
                continue

            # 2b. Same sign as before?
            roadside = match_roadside_sign(sign["bbox"], sign_boxes or [])
            if roadside is not None:
                # One of our roadside signs: process it once, then
                # never again until the car has passed it.
                box["sign_id"] = roadside["id"]
                if roadside["id"] in state["processed_sign_ids"]:
                    box["reason"] = "already_processed"
                    continue
                state["processed_sign_ids"].add(roadside["id"])
            elif not tracker.is_new_sign(sign["bbox"]):
                # Something else YOLO found: old pixel tracker.
                box["reason"] = "same_as_previous_frame"
                continue

            box["is_new"] = True
            box["reason"] = "processed"

            # 3. The vehicle's own pipeline
            state["sign_counter"] += 1
            number = state["sign_counter"]
            print("[ML] Sign #{} -> {}".format(number, vehicle_id))

            # Re-read the broadcast queue file so packages that were
            # already broadcast are not written back into it.
            queue = getattr(module, "broadcast_queue", None)
            if queue is not None and hasattr(queue, "load_queue"):
                queue.load_queue()

            try:
                result = module.process_detected_sign(sign, number, frame_number)
            except Exception as error:
                traceback.print_exc()
                result = {"status": "ERROR", "error": str(error), "steps": []}

            results.append({
                "sign_number": number,
                "bbox": [int(v) for v in sign["bbox"]],
                "yolo_confidence": box["yolo_confidence"],
                "sign_id": box["sign_id"],
                "placed_sign": roadside["name"] if roadside else None,
                "crop_jpeg": crop_to_jpeg_b64(sign.get("cropped_sign")),
                "result": json_safe(result) if isinstance(result, dict) else None,
            })

        save_vehicle(vehicle_id)

    return {"success": True, "vehicle": vehicle_id, "frame_number": frame_number,
            "detections": detections, "results": results}


@app.post("/process_frame")
async def process_frame(request: Request, frame_number: int = Query(0)):
    """
    Body = one JPEG front-camera frame.
    Header X-Sign-Boxes = JSON list of where each roadside sign is
    in this frame (from the simulation), used only to skip signs
    that were already processed.
    """
    body = await request.body()
    try:
        sign_boxes = json.loads(request.headers.get("X-Sign-Boxes", "[]"))
    except ValueError:
        sign_boxes = []
    return await run_in_threadpool(handle_frame, body, frame_number, sign_boxes)


@app.post("/test_image")
def test_image(path: str = Query(...)):
    """Testing without CARLA: run on an image file."""
    full = path if os.path.isabs(path) else os.path.join(COMPONENT_4_DIR, path)
    if not os.path.exists(full):
        return {"success": False, "message": "File not found: " + full}
    tracker.reset()
    state["processed_sign_ids"] = set()
    with open(full, "rb") as f:
        return handle_frame(f.read(), 0)


@app.post("/broadcast")
def broadcast():
    from global_verification_server.broadcast_knowledge import KnowledgeBroadcastService
    with lock:
        try:
            result = KnowledgeBroadcastService().broadcast_all_to_all_vehicles()
        except Exception as error:
            traceback.print_exc()
            return {"success": False, "message": "Broadcast error: {}".format(error)}
    return {"success": True, "message": "Broadcast sent", "result": json_safe(result)}


def _retrain(vehicle_id):
    try:
        with lock:
            use_vehicle(vehicle_id)
            path = os.path.join(vehicle_dir(vehicle_id), "src", "local_model_retraining.py")
            spec = importlib.util.spec_from_file_location("vehicle_main_retrain_{}".format(time.time()), path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = getattr(module, VEHICLES[vehicle_id]["retrainer"])().retrain()

            # The CNN changed: load it fresh next time.
            state["pipelines"].pop(vehicle_id, None)
            _saved_src_modules.pop(vehicle_id, None)
            if state["active_vehicle"] == vehicle_id:
                state["active_vehicle"] = None

        result = result or {}
        status = result.get("status", "UNKNOWN")
        details = []
        if result.get("reason"):
            details.append(str(result["reason"]))
        if result.get("total_images") is not None:
            details.append("{} images".format(result["total_images"]))
        state["retraining"][vehicle_id] = "done: {}{}".format(
            status, " ({})".format(", ".join(details)) if details else "")
        print("[ML] {} retraining: {}".format(vehicle_id, status))
    except Exception as error:
        traceback.print_exc()
        state["retraining"][vehicle_id] = "failed: {}".format(error)


@app.post("/retrain")
def retrain(vehicle: str = Query(...)):
    vehicle_id = vehicle_id_from(vehicle)
    if vehicle_id is None:
        return {"success": False, "message": "Unknown vehicle: {}".format(vehicle)}
    if state["retraining"].get(vehicle_id) == "running":
        return {"success": False, "message": "{} is already retraining.".format(vehicle_id)}
    state["retraining"][vehicle_id] = "running"
    threading.Thread(target=_retrain, args=(vehicle_id,), daemon=True).start()
    return {"success": True, "message": "{} retraining started.".format(vehicle_id.replace("_", " "))}


if __name__ == "__main__":
    print("=" * 60)
    print("Component 4 ML Service  ->  http://{}:{}".format(HOST, PORT))
    print("Folder: " + COMPONENT_4_DIR)
    print("=" * 60)

    # YOLO first - before any TensorFlow is loaded in this process.
    start_yolo_worker()

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")