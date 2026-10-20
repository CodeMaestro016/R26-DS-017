# -*- coding: utf-8 -*-
"""
pose_server.py
Runs UNDER THE INSTANCE'S NORMAL PYTHON (3.12, not the CARLA venv).
Exists purely to bridge a Python version gap: the CARLA 0.9.15 client
wheel only supports Python 3.7, but MediaPipe no longer publishes ANY
Python 3.7 wheel (confirmed by checking PyPI directly -- not even an
old one with the legacy Solutions API). Rather than fight that, this
runs MediaPipe in its own process on whatever Python the instance
already has, using the exact same Tasks API + model as the original
pose_estimation.py, and exposes it as a tiny local HTTP endpoint.
carla_live_demo.py (running in the 3.7 CARLA venv) POSTs each
pedestrian crop here and gets back the landmarks as JSON -- same
data, same model, just crossing a process boundary instead of an
in-process import.

Run this FIRST, in its own terminal tab, BEFORE starting CARLA or
carla_live_demo.py:
    python3 pose_server.py
Leave it running the whole time you're using carla_live_demo.py.

------------------------------------------------------------------
FIX (see conversation history / debugging session):
The original offline pipeline (pose_estimation.ipynb) saved FOUR
values per landmark -- [x, y, z, visibility] -- and used detection
thresholds of 0.5/0.5. This server had drifted to only sending
[x, y, z] (dropping visibility entirely) and had lowered both
thresholds to 0.3 "to see if 0.5 was too strict" without that ever
being verified. Both changes made the live pipeline silently feed
low-confidence, unfiltered landmark jitter into the motion/behaviour
features, which is what caused a genuinely stationary pedestrian to
be classified as Jaywalk/Aggressive/Committed. Both are restored to
match the original exactly:
  - min_pose_detection_confidence / min_tracking_confidence -> 0.5
  - landmarks payload now includes lm.visibility as a 4th value,
    so feature_pipeline.py can gate on it before trusting a
    detection enough to feed it into the speed/behaviour math.
------------------------------------------------------------------
"""
import io
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import numpy as np
from PIL import Image
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "/tmp/pose_landmarker_full.task"
PORT = 8091

if not os.path.exists(MODEL_PATH):
    print("Downloading MediaPipe pose model (same one pose_estimation.py used)...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_full/"
        "float16/latest/pose_landmarker_full.task",
        MODEL_PATH,
    )

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)

# Restored to match the original pose_estimation.ipynb exactly (0.5/0.5).
# These are the thresholds the training data was actually generated
# with -- treat any future change to these as something to verify
# against a live A/B test, not something to tweak casually.
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
detector = vision.PoseLandmarker.create_from_options(options)
print("MediaPipe pose model ready.")


class PoseHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/pose':
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            img = Image.open(io.BytesIO(body)).convert('RGB')
            rgb_array = np.array(img)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)
            result = detector.detect(mp_image)
            if result.pose_landmarks:
                # Restored 4th value (visibility) -- matches the
                # original offline pipeline's saved format exactly
                # ([x, y, z, visibility] per landmark). Downstream,
                # feature_pipeline.py uses this to reject detections
                # on joints (hips/ankles) that MediaPipe itself isn't
                # confident about, instead of treating every returned
                # landmark as equally trustworthy.
                landmarks = [
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in result.pose_landmarks[0]
                ]
                response = {'landmarks': landmarks}
            else:
                response = {'landmarks': None}
            payload = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            error_payload = json.dumps({'error': str(e)}).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(error_payload)))
            self.end_headers()
            self.wfile.write(error_payload)

    def log_message(self, format, *args):
        pass  # keep the console quiet -- this gets called once per frame


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), PoseHandler)
    print(f"Pose server listening on http://127.0.0.1:{PORT}/pose")
    print("Leave this running. Start carla_live_demo.py in a different terminal.")
    server.serve_forever()