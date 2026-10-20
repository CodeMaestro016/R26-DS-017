# -*- coding: utf-8 -*-
"""
ensemble_server.py

Runs UNDER THE INSTANCE'S NORMAL PYTHON (3.12, not the CARLA venv) --
same reasoning as pose_server.py. Your trained .keras files use the
Keras 3 native format (a zip archive), which the old TensorFlow 2.11
bundled in the Python 3.7 CARLA venv cannot read at all (it only
understands the older .h5/HDF5 format). Rather than fight that
version gap, this loads your real models under a modern TensorFlow
here, and exposes prediction as a tiny local HTTP endpoint.

carla_live_demo.py (running in the 3.7 CARLA venv) POSTs each RAW
(30, 36) feature sequence here and gets back the ensemble's mental
state prediction -- scaling AND inference both happen here, since
your scaler.pkl was saved with a NumPy version too new for the
CARLA venv's Python 3.7 to unpickle at all (confirmed by actually
hitting that error) -- same reasoning as the model files themselves.

Run this BEFORE carla_live_demo.py, in its own terminal:

    pip3 install tensorflow
    python3 ensemble_server.py --model-dir models

Leave it running the whole time you're using carla_live_demo.py.
"""

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import joblib

PORT = 8092

LABELS = {
    0: 'Waiting',
    1: 'Hesitant',
    2: 'Committed',
    3: 'Distracted',
    4: 'Aggressive',
    5: 'Jaywalk',
}

_lstm_model = None
_gru_model = None
_scaler = None


def load_models(model_dir):
    global _lstm_model, _gru_model, _scaler
    from tensorflow import keras

    lstm_path = os.path.join(model_dir, 'lstm_mental_state_best.keras')
    gru_path = os.path.join(model_dir, 'gru_mental_state_best.keras')
    scaler_path = os.path.join(model_dir, 'scaler.pkl')

    for path, name in [(lstm_path, 'lstm_mental_state_best.keras'),
                        (gru_path, 'gru_mental_state_best.keras'),
                        (scaler_path, 'scaler.pkl')]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing: {name}\nExpected at: {path}")

    print("Loading LSTM...")
    _lstm_model = keras.models.load_model(lstm_path)
    print("Loading GRU...")
    _gru_model = keras.models.load_model(gru_path)
    print("Loading scaler...")
    _scaler = joblib.load(scaler_path)
    print("Ensemble ready.")

    # ---- Diagnostic: what does the scaler actually expect? ----
    # Prints the TRAINING-TIME statistics for the motion features most
    # likely to be affected if CARLA's tick rate (20Hz) doesn't match
    # PIE's video frame rate (30fps) -- your recovered feature formulas
    # compute speed as distance/gap where gap is a FRAME count, not
    # seconds, so a frame-rate mismatch would silently inflate every
    # speed-based feature by a fixed ratio without CARLA doing anything
    # behaviorally wrong. Compare these numbers directly against the
    # "Raw features" line already printed in carla_live_demo.py's
    # decision blocks -- if live values are consistently several times
    # larger than what's shown here, that's hard confirmation of a
    # scale mismatch, not a guess.
    feature_names = ['current_speed', 'avg_speed', 'max_speed', 'acceleration',
                      'deceleration', 'speed_variance', 'step_frequency']
    print("\n" + "=" * 60)
    print("SCALER DIAGNOSTIC -- what the model was actually trained to expect")
    print("=" * 60)
    print(f"Scaler type: {type(_scaler).__name__}")
    if hasattr(_scaler, 'mean_'):
        print("(StandardScaler -- values below are TRAINING MEAN / STD DEV per feature)")
        for i, name in enumerate(feature_names):
            print(f"  [{i}] {name:<18} mean={_scaler.mean_[i]:.4f}  std={_scaler.scale_[i]:.4f}")
    elif hasattr(_scaler, 'data_min_'):
        print("(MinMaxScaler -- values below are TRAINING MIN / MAX per feature)")
        for i, name in enumerate(feature_names):
            print(f"  [{i}] {name:<18} min={_scaler.data_min_[i]:.4f}  max={_scaler.data_max_[i]:.4f}")
    else:
        print(f"(Unrecognized scaler type -- inspect manually: {dir(_scaler)})")
    print("=" * 60 + "\n")


class PredictHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/predict':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body.decode('utf-8'))
            seq_raw = np.array(payload['sequence'], dtype=np.float32)  # (30, 36) RAW, unscaled
            seq_scaled = _scaler.transform(seq_raw)
            seq_in = seq_scaled[np.newaxis, ...]

            lstm_probs = _lstm_model.predict(seq_in, verbose=0)[0]
            gru_probs = _gru_model.predict(seq_in, verbose=0)[0]
            probs = (lstm_probs + gru_probs) / 2.0
            mental_state = int(np.argmax(probs))
            confidence = float(probs[mental_state])

            response = {
                'mental_state': mental_state,
                'state_name': LABELS[mental_state],
                'confidence': confidence,
                'probs': probs.tolist(),
            }
            out = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(out)))
            self.end_headers()
            self.wfile.write(out)

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', default='models')
    args = parser.parse_args()

    load_models(args.model_dir)

    server = ThreadingHTTPServer(('127.0.0.1', PORT), PredictHandler)
    print(f"Ensemble server listening on http://127.0.0.1:{PORT}/predict")
    print("Leave this running. Start carla_live_demo.py in a different terminal.")
    server.serve_forever()
