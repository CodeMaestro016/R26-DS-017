# -*- coding: utf-8 -*-
"""
Clean Rule-Based Agent
Mental state + TTC → AV action
"""

import numpy as np
import json
import os


# ── Feature Indices ────────────────────────────────────────────
F_CURRENT_SPEED        = 0
F_AVG_SPEED            = 1
F_MAX_SPEED            = 2
F_ACCELERATION         = 3
F_DECELERATION         = 4
F_SPEED_VARIANCE       = 5
F_STEP_FREQUENCY       = 6
F_LEFT_STEP_LENGTH     = 7
F_RIGHT_STEP_LENGTH    = 8
F_PAUSE_BETWEEN_STEPS  = 9
F_UPPER_BODY_ANGLE     = 10
F_LOWER_BODY_ANGLE     = 11
F_HEAD_ANGLE           = 12
F_HEAD_TURN_FREQUENCY  = 13
F_SHOULDER_ANGLE       = 14
F_HIP_ANGLE            = 15
F_FOOT_ANGLE_LEFT      = 16
F_FOOT_ANGLE_RIGHT     = 17
F_FORWARD_LEAN         = 18
F_LATERAL_LEAN         = 19
F_BODY_ORIENTATION     = 20
F_BODY_ORIENT_CHANGE   = 21
F_PAUSE_DURATION       = 22
F_HESITATION_CYCLES    = 23
F_TOTAL_HESITATION     = 24
F_DISTANCE_TO_CURB     = 25
F_DISTANCE_CHANGE_RATE = 26
F_MOVEMENT_PROBABILITY = 27
F_LOOKS_LEFT           = 28
F_LOOKS_RIGHT          = 29
F_DIRECTION_CHANGES    = 30
F_TRAFFIC_LIGHT        = 31
F_VEHICLE_DISTANCE     = 32
F_CROSSWALK            = 33
F_ROAD_WIDTH           = 34
F_PED_DENSITY          = 35


LABELS = {
    0: 'Waiting',
    1: 'Hesitant',
    2: 'Committed',
    3: 'Distracted',
    4: 'Aggressive',
    5: 'Jaywalk'
}


TTC_WARNING   = 2.5
TTC_EMERGENCY = 1.5


# ══════════════════════════════════════════════════════════════
# ENSEMBLE MODEL LOADER
# ══════════════════════════════════════════════════════════════

_lstm_model    = None
_gru_model     = None
_scaler        = None
_models_loaded = False


def load_ensemble(model_dir=None):
    """
    Load LSTM + GRU + scaler from model_dir.
    Call ONCE before simulation loop.

    Expected files:
        lstm_mental_state_best.h5
        gru_mental_state_best.h5
        feature_scaler.pkl
    """
    global _lstm_model, _gru_model, _scaler, _models_loaded

    from tensorflow import keras
    import joblib

    if model_dir is None:
        # Default to the sibling `models/` folder next to `sumo_demo/scripts`.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.abspath(os.path.join(base_dir, '..', 'models'))

    print('Loading ensemble models...')
    print(f'  Model directory: {model_dir}')

    lstm_path   = os.path.join(model_dir, 'lstm_mental_state_best.h5')
    gru_path    = os.path.join(model_dir, 'gru_mental_state_best.h5')
    scaler_path = os.path.join(model_dir, 'feature_scaler.pkl')

    for path, name in [
        (lstm_path,   'lstm_mental_state_best.h5'),
        (gru_path,    'gru_mental_state_best.h5'),
        (scaler_path, 'feature_scaler.pkl'),
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f'Missing: {name}\n'
                f'Expected at: {path}\n'
                f'Place the files into the `sumo_demo/models/` folder or pass `model_dir` to `load_ensemble()`.'
            )

    _lstm_model = keras.models.load_model(lstm_path)
    print('  LSTM loaded')
    _gru_model  = keras.models.load_model(gru_path)
    print('  GRU loaded')
    _scaler     = joblib.load(scaler_path)
    print('  Scaler loaded')

    _models_loaded = True
    print('Ensemble ready.\n')


def predict_mental_state(sequence_36_raw):
    """
    Run ensemble on ONE pedestrian's RAW feature sequence.

    Args:
        sequence_36_raw : np.array (30, 36) — raw unscaled

    Returns:
        mental_state : int
        confidence   : float
        probs        : np.array(6)
        detail       : dict
    """
    if not _models_loaded:
        raise RuntimeError('Models not loaded. Call load_ensemble() first.')

    seq_2d     = sequence_36_raw.reshape(-1, 36)
    seq_scaled = _scaler.transform(seq_2d)
    seq_in     = seq_scaled[np.newaxis, ...]

    lstm_probs = _lstm_model.predict(seq_in, verbose=0)[0]
    gru_probs  = _gru_model.predict(seq_in, verbose=0)[0]

    # Equal-weight average ensemble.
    # Sources: Dietterich (2000); Lakshminarayanan et al. (NeurIPS 2017)
    probs        = (lstm_probs + gru_probs) / 2.0
    mental_state = int(np.argmax(probs))
    confidence   = float(probs[mental_state])

    return mental_state, confidence, probs, {
        'lstm':     lstm_probs.tolist(),
        'gru':      gru_probs.tolist(),
        'ensemble': probs.tolist(),
    }


def predict_from_scaled_sequence(sequence_scaled):
    """Same as predict_mental_state() but for pre-scaled input."""
    if not _models_loaded:
        raise RuntimeError('Models not loaded. Call load_ensemble() first.')

    seq_in = sequence_scaled[np.newaxis, ...]

    lstm_probs = _lstm_model.predict(seq_in, verbose=0)[0]
    gru_probs  = _gru_model.predict(seq_in, verbose=0)[0]

    probs        = (lstm_probs + gru_probs) / 2.0
    mental_state = int(np.argmax(probs))
    confidence   = float(probs[mental_state])

    return mental_state, confidence, probs, {
        'lstm':     lstm_probs.tolist(),
        'gru':      gru_probs.tolist(),
        'ensemble': probs.tolist(),
    }


# ══════════════════════════════════════════════════════════════
# RULE-BASED AGENT
# ══════════════════════════════════════════════════════════════

class RuleBasedAgent:
    """
    Simple AV decision agent.

    Input:
        F                 : 36 feature vector
        mental_state      : 0-5 predicted mental state
        vehicle_speed_kmh : current AV speed in km/h

    Output:
        action, reason, TTC
    """

    # def __init__(self, frame_width_metres=20.0):
    #     self.frame_width_metres = frame_width_metres

    

    def compute_ttc(self, pixel_distance, pixel_speed):

        if pixel_speed <= 0:
            return np.inf

        ttc_frames = pixel_distance / pixel_speed
        return ttc_frames / 30.0  # FPS

    def get_ttc_level(self, ttc):
        if not np.isfinite(ttc):
            return "safe"
        if ttc < TTC_EMERGENCY:
            return "high"
        elif ttc < TTC_WARNING:
            return "medium"
        else:
            return "low"

    def decide(self, F, mental_state, confidence=1.0, vehicle_speed_kmh=0.0):
        """
        Main decision logic.
        """

        state_name = LABELS.get(mental_state, "Unknown")

        # Image-space TTC
        # F[32] is normalised vehicle distance, so convert back to pixels
        pixel_distance = float(F[F_VEHICLE_DISTANCE]) * 1920.0
        pixel_speed    = float(F[F_CURRENT_SPEED])  # already px/frame

        ttc       = self.compute_ttc(pixel_distance, pixel_speed)
        ttc_level = self.get_ttc_level(ttc)

        # -------- Rule-based action mapping --------

        if mental_state == 0:
            if ttc_level == "high":
                action = "SLOW_DOWN"
                reason = "Pedestrian is waiting but proximity is critical. Sudden step-off risk."
            elif ttc_level == "medium":
                action = "SLOW_DOWN"
                reason = "Pedestrian is waiting but within gap acceptance range."
            else:
                action = "MAINTAIN"
                reason = "Pedestrian is waiting, crossing risk is low."

        elif mental_state == 1:
            if ttc_level == "high":
                action = "STOP"
                reason = "Pedestrian is hesitant and TTC is very low."
            elif ttc_level == "medium":
                action = "SLOW_DOWN"
                reason = "Pedestrian is hesitant and may enter the road."
            else:
                action = "MAINTAIN"
                reason = "Pedestrian is hesitant but still far enough."

        elif mental_state == 2:
            if ttc_level == "high":
                action = "STOP"
                reason = "Pedestrian is committed and TTC is critical."
            elif ttc_level == "medium":
                action = "SLOW_DOWN"
                reason = "Pedestrian is committed and approaching conflict zone."
            else:
                action = "SLOW_DOWN"
                reason = "Pedestrian is committed, but TTC is currently low risk."

        elif mental_state == 3:
            if ttc_level == "high":
                action = "STOP"
                reason = "Pedestrian is distracted and very close."
            else:
                action = "SLOW_DOWN"
                reason = "Pedestrian is distracted, so AV should be cautious."

        elif mental_state == 4:
            if ttc_level == "high":
                action = "STOP"
                reason = "Pedestrian is aggressive and very close."
            else:
                action = "SLOW_DOWN"
                reason = "Pedestrian movement is aggressive. may step into the road."

        elif mental_state == 5:
            if ttc_level == "high":
                action = "STOP"
                reason = "Pedestrian is jaywalking and very close."
            else:
                action = "SLOW_DOWN"
                reason = "Pedestrian is jaywalking, so AV should reduce speed."

        else:
            action = "SLOW_DOWN"
            reason = "Unpredictable, so AV chooses safe action."

        return {
            "action":       action,
            "reason":       reason,
            "mental_state": mental_state,
            "state_name":   state_name,
            "confidence":   confidence,
            "pixel_distance": pixel_distance,
            "pixel_speed": pixel_speed,
            "ttc":          ttc,
            "ttc_level":    ttc_level,
        }


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    agent = RuleBasedAgent()

    def make_F(speed=5.0, vehicle_dist=0.5):
        F = np.zeros(36, dtype=np.float32)
        F[F_CURRENT_SPEED]    = speed
        F[F_VEHICLE_DISTANCE] = vehicle_dist
        return F

    scenarios = [
        ("Waiting - safe",       make_F(speed=0.0, vehicle_dist=0.8), 0, 0.95, 50.0),
        ("Waiting - warning",    make_F(speed=0.0, vehicle_dist=0.3), 0, 0.95, 50.0),
        ("Waiting - emergency",  make_F(speed=0.0, vehicle_dist=0.1), 0, 0.95, 50.0),
        ("Hesitant - far",       make_F(speed=2.0, vehicle_dist=0.8), 1, 0.80, 40.0),
        ("Hesitant - warning",   make_F(speed=5.0, vehicle_dist=0.25),1, 0.78, 40.0),
        ("Hesitant - emergency", make_F(speed=8.0, vehicle_dist=0.05),1, 0.76, 40.0),
        ("Committed - far",      make_F(speed=4.0, vehicle_dist=0.8), 2, 0.90, 50.0),
        ("Committed - close",    make_F(speed=4.0, vehicle_dist=0.2), 2, 0.90, 50.0),
        ("Distracted",           make_F(speed=3.0, vehicle_dist=0.3), 3, 0.72, 40.0),
        ("Aggressive",           make_F(speed=8.0, vehicle_dist=0.2), 4, 0.85, 50.0),
        ("Jaywalk",              make_F(speed=6.0, vehicle_dist=0.15),5, 0.70, 45.0),
    ]

    print("\n===================================================")
    print("RULE-BASED AGENT SELF TEST")
    print("===================================================")

    for name, F, state, conf, av_spd in scenarios:

        result = agent.decide(F, state, confidence=conf,
                              vehicle_speed_kmh=av_spd)

        ttc_text = (
            f"{result['ttc']:.2f} s"
            if np.isfinite(result["ttc"])
            else "N/A"
        )

        print("\n---------------------------------------------------")
        print(f"Scenario     : {name}")
        print(f"State        : {result['state_name']} ({result['mental_state']})")
        print(f"Confidence   : {result['confidence']:.2f}")
        print(f"Pixel dist   : {result['pixel_distance']:.2f} px")
        print(f"Pixel speed  : {result['pixel_speed']:.2f} px/frame")
        print(f"TTC          : {ttc_text}")
        print(f"TTC level    : {result['ttc_level']}")
        print(f"Action       : {result['action']}")
        print(f"Reason       : {result['reason']}")