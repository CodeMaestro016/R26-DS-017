# -*- coding: utf-8 -*-
"""
ensemble_server.py

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
            if not os.path.exists('live_raw_sequence.npy'):
                np.save('live_raw_sequence.npy', seq_raw)
                print('LIVE FEATURES SAVED', flush=True)
            seq_raw[:, 34] = 0.0  # Temporary feature 34 test
            seq_scaled = _scaler.transform(seq_raw)
            seq_in = seq_scaled[np.newaxis, ...]

            lstm_probs = _lstm_model.predict(seq_in, verbose=0)[0]
            gru_probs = _gru_model.predict(seq_in, verbose=0)[0]
            probs = (0.40 * lstm_probs) + (0.60 * gru_probs)
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
