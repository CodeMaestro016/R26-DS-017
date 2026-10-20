# ============================================================
# component_4/test_yolo_on_carla.py
#
# STEP 1 TEST: does YOLOv8 detect our roadside signs in real
# CARLA front-camera frames?
#
# Takes frames from the running simulation (/model_frame.jpg),
# runs the SAME YOLO model and settings the pipeline uses
# (CPU, conf 0.25, like the old yolo_worker_process.py), and
# saves pictures with boxes.
#
# Run (Vast.ai, while a vehicle is driving on the website):
#   conda activate main
#   cd /workspace/IT22022974_reserch/IT22022974_reserch/component_4
#   python test_yolo_on_carla.py
#
# Options:
#   --count 30      number of frames to test (default 30)
#   --interval 1.0  seconds between frames (default 1.0)
#
# Output: component_4/yolo_test_output/
#   frame_XXX.jpg  - every frame, with boxes
#       green  box = detected (confidence >= 0.25, sent to pipeline)
#       orange box = weak     (0.05 - 0.25, would be ignored)
#   crop_XXX_N.jpg - what the CNN would receive
# ============================================================

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""   # same as the YOLO worker

import argparse
import time
import urllib.request

import cv2
import numpy as np
from ultralytics import YOLO


COMPONENT_4_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(
    COMPONENT_4_DIR, "vehicles", "vehicle_A", "models",
    "generic_traffic_sign_detector_best.pt",
)
FRAME_URL = "http://127.0.0.1:8010/model_frame.jpg"
OUTPUT_DIR = os.path.join(COMPONENT_4_DIR, "yolo_test_output")

PIPELINE_CONFIDENCE = 0.25   # what the pipeline uses
WEAK_CONFIDENCE = 0.05       # also shown, to see near-misses


def fetch_frame():
    try:
        with urllib.request.urlopen(FRAME_URL, timeout=5) as response:
            data = response.read()
    except Exception as error:
        print("  Could not get frame:", error)
        return None
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name in os.listdir(OUTPUT_DIR):
        if name.endswith(".jpg"):
            os.remove(os.path.join(OUTPUT_DIR, name))

    print("=" * 60)
    print("YOLO TEST ON CARLA FRAMES")
    print("Model :", MODEL_PATH)
    print("Frames:", FRAME_URL)
    print("Output:", OUTPUT_DIR)
    print("=" * 60)

    model = YOLO(MODEL_PATH)
    model.to("cpu")
    print("YOLO loaded (CPU).\n")

    frames_with_sign = 0
    total_detections = 0
    best_confidence = 0.0

    for index in range(1, args.count + 1):
        frame = fetch_frame()
        if frame is None:
            print("Frame %3d: no frame (is a vehicle running on the website?)" % index)
            time.sleep(args.interval)
            continue

        started = time.perf_counter()
        results = model(frame, conf=WEAK_CONFIDENCE, verbose=False)
        seconds = time.perf_counter() - started

        annotated = frame.copy()
        strong, weak = [], []

        h, w = frame.shape[:2]
        if results and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue
                confidence = float(box.conf[0])
                best_confidence = max(best_confidence, confidence)

                if confidence >= PIPELINE_CONFIDENCE:
                    strong.append((x1, y1, x2, y2, confidence))
                    color = (0, 200, 0)
                else:
                    weak.append((x1, y1, x2, y2, confidence))
                    color = (0, 140, 255)

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, "%.2f  %dx%dpx" % (confidence, x2 - x1, y2 - y1),
                            (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        for n, (x1, y1, x2, y2, _) in enumerate(strong, start=1):
            cv2.imwrite(os.path.join(OUTPUT_DIR, "crop_%03d_%d.jpg" % (index, n)),
                        frame[y1:y2, x1:x2])

        cv2.putText(annotated, "frame %d   detected: %d   weak: %d" % (index, len(strong), len(weak)),
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imwrite(os.path.join(OUTPUT_DIR, "frame_%03d.jpg" % index), annotated)

        if strong:
            frames_with_sign += 1
            total_detections += len(strong)

        print("Frame %3d: detected=%d  weak=%d  %s  (%.2fs)" % (
            index, len(strong), len(weak),
            " ".join("%.2f" % s[4] for s in strong + weak) or "-",
            seconds))

        time.sleep(args.interval)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("Frames tested            :", args.count)
    print("Frames with a detection  :", frames_with_sign)
    print("Detections (conf >= 0.25):", total_detections)
    print("Best confidence seen     : %.2f" % best_confidence)
    print("Pictures saved in        :", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
