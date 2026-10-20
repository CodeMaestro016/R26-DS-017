# -*- coding: utf-8 -*-
"""
pose_server.py

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
        pass 


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), PoseHandler)
    print(f"Pose server listening on http://127.0.0.1:{PORT}/pose")
    print("Leave this running. Start carla_live_demo.py in a different terminal.")
    server.serve_forever()