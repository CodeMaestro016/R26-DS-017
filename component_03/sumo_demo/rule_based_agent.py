# -*- coding: utf-8 -*-
"""
rule_based_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rule-Based Decision Agent for Autonomous Vehicle
ENSEMBLE VERSION: LSTM + GRU 

INPUTS:
  F              : np.array (36,) — extracted features
  mental_state   : int (0-5)     — from ensemble model
  vehicle_speed  : float         — current AV speed in km/h

OUTPUT:
  action         : str           — MAINTAIN/SLOW_DOWN/BRAKE/EVASIVE
  reason         : str           — human-readable explanation
  risk_score     : float (0-1)   — calibrated road-entry risk score

DECISION PRIORITY:
  1. Traffic light (F[31]) — overrides everything
  2. Risk score - behavioural decision
    

4 ACTIONS:
  MAINTAIN   → keep speed, low risk
  SLOW_DOWN  → reduce speed, medium risk
  BRAKE      → hard deceleration toward stop
  EVASIVE    → steer away + max brake (cannot stop in time)

ENSEMBLE METHOD:
  Simple average of LSTM + GRU  probabilities.
  Equal weights chosen because accuracy-based weighting is
  counterbalanced by overfitting penalties, resulting in
  weights statistically indistinguishable from uniform averaging.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import numpy as np
import json
import os
from dataclasses import dataclass

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

LABEL_NAMES = {
    0: 'Waiting', 1: 'Hesitant',   2: 'Committed',
    3: 'Distracted', 4: 'Aggressive', 5: 'Jaywalk'
}

ACTIONS = {
    'MAINTAIN':  'Keep current speed — situation is safe',
    'SLOW_DOWN': 'Reduce speed — monitoring pedestrian',
    'BRAKE':     'Hard deceleration to stop — high risk',
    'EVASIVE':   'Steer away + maximum brake — cannot stop in time',
}


# ══════════════════════════════════════════════════════════════
# ENSEMBLE MODEL LOADER
# ══════════════════════════════════════════════════════════════

_lstm_model        = None
_gru_model         = None
_scaler            = None
_models_loaded     = False


def load_ensemble(model_dir=None):
    """
    Load LSTM + GRU + scaler from model_dir.
    Call ONCE at the start of run_demo.py before simulation loop.

    Expected files in model_dir:
        lstm_mental_state_best.h5
        gru_mental_state_best.h5
        feature_scaler.pkl
    """
    global _lstm_model, _gru_model
    global _scaler, _models_loaded

    import tensorflow as tf
    from tensorflow import keras
    import joblib

    if model_dir is None:
        model_dir = os.path.dirname(os.path.abspath(__file__))

    print('Loading ensemble models...')
    print(f'  Model directory: {model_dir}')

    lstm_path        = os.path.join(model_dir, 'lstm_mental_state_best.h5')
    gru_path         = os.path.join(model_dir, 'gru_mental_state_best.h5')
    scaler_path      = os.path.join(model_dir, 'feature_scaler.pkl')

    for path, name in [
        (lstm_path,        'lstm_mental_state_best.h5'),
        (gru_path,         'gru_mental_state_best.h5'),
        (scaler_path,      'feature_scaler.pkl'),
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f'Missing: {name}\n'
                f'Expected at: {path}\n'
                f'Copy it from Google Drive → sumo_demo/ folder.'
            )

    _lstm_model        = keras.models.load_model(lstm_path)
    print('  LSTM loaded')
    _gru_model         = keras.models.load_model(gru_path)
    print('  GRU loaded')

    _scaler            = joblib.load(scaler_path)
    print('  Scaler loaded')

    _models_loaded = True
    print('Ensemble ready.\n')


def predict_mental_state(sequence_36_raw):
    """
    Run ensemble on ONE pedestrian's RAW feature sequence.


    Args:
        sequence_36_raw: np.array (30, 36) — raw unscaled features

    Returns:
        mental_state : int         — predicted class 0-5
        confidence   : float       — highest averaged probability
        probs        : np.array(6) — all 6 averaged probabilities
        detail       : dict        — individual model outputs
    """
    if not _models_loaded:
        raise RuntimeError('Models not loaded. Call load_ensemble() first.')

    seq_2d     = sequence_36_raw.reshape(-1, 36)
    seq_scaled = _scaler.transform(seq_2d)
    seq_in     = seq_scaled[np.newaxis, ...]         # (1, 30, 36)

    lstm_probs        = _lstm_model.predict(seq_in, verbose=0)[0]
    gru_probs         = _gru_model.predict(seq_in, verbose=0)[0]
  

    # Simple average — equal weights
    probs        = (lstm_probs + gru_probs) / 2.0
    mental_state = int(np.argmax(probs))
    confidence   = float(probs[mental_state])

    return mental_state, confidence, probs, {
        'lstm':        lstm_probs.tolist(),
        'gru':         gru_probs.tolist(),
        'ensemble':    probs.tolist(),
    }


def predict_from_scaled_sequence(sequence_scaled):
    """
    Same as predict_mental_state() but accepts ALREADY-SCALED
    features (e.g. from X_test.npy which is pre-scaled).

    Args:
        sequence_scaled: np.array (30, 36) — pre-scaled features

    Returns:
        same as predict_mental_state()
    """
    if not _models_loaded:
        raise RuntimeError('Models not loaded. Call load_ensemble() first.')

    seq_in = sequence_scaled[np.newaxis, ...]        # (1, 30, 36)

    lstm_probs        = _lstm_model.predict(seq_in, verbose=0)[0]
    gru_probs         = _gru_model.predict(seq_in, verbose=0)[0]

    # Simple average
    probs        = (lstm_probs + gru_probs ) / 2.0
    mental_state = int(np.argmax(probs))
    confidence   = float(probs[mental_state])

    return mental_state, confidence, probs, {
        'lstm':        lstm_probs.tolist(),
        'gru':         gru_probs.tolist(),
        'ensemble':    probs.tolist(),
    }


# ══════════════════════════════════════════════════════════════
# DECISION OUTPUT DATACLASS
# ══════════════════════════════════════════════════════════════

@dataclass
class AgentDecision:
    action:       str
    reason:       str
    risk_score:   float
    mental_state: int
    state_name:   str
    confidence:   float
    traffic_light:str
    dist_metres:  float
    stop_dist_m:  float
    can_stop:     bool

    def summary(self):
        return '\n'.join([
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'ACTION         : {self.action}',
            f'REASON         : {self.reason}',
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            f'Mental state   : {self.state_name} ({self.mental_state})',
            f'Confidence     : {self.confidence:.1%}',
            f'Risk score     : {self.risk_score:.3f}',
            f'Traffic light  : {self.traffic_light}',
            f'Distance       : {self.dist_metres:.1f} m',
            f'Stop distance  : {self.stop_dist_m:.1f} m',
            f'Can stop       : {"YES" if self.can_stop else "NO — EVASIVE"}',
            f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
        ])


# ══════════════════════════════════════════════════════════════
# RULE-BASED AGENT
# ══════════════════════════════════════════════════════════════

class RuleBasedAgent:
    """
    Rule-based decision agent for AV pedestrian response.

    DECISION PIPELINE:
      1. Traffic light — overrides all else
      2. Risk + Physics — data-driven behavioural decision


    RISK THRESHOLDS:
      Auto-calibrated from your data using percentiles:
        medium = np.percentile(risk_scores, 33)  → SLOW DOWN
        high   = np.percentile(risk_scores, 66)  → BRAKE/EVASIVE
    """

    def __init__(self,
                k_distance = 0.3391,
                k_speed    = 6.6076,
                k_accel    = 3.0079,
                k_lean     = 20.4451,
                k_variance = 134.815,
                # ── Decision thresholds ───────────────────────────────
                medium_risk_threshold = 0.30,
                high_risk_threshold   = 0.60,
                emergency_decel       = 8.0,
                frame_width_metres    = 20.0,
                # ── Auto-calibration — pass UNSCALED data here ────────
                X_data = None,
                y_data = None):

        self.emergency_decel    = emergency_decel
        self.frame_width_metres = frame_width_metres

        # Store k values
        self.k_distance = k_distance
        self.k_speed    = k_speed
        self.k_accel    = k_accel
        self.k_lean     = k_lean
        self.k_variance = k_variance

        if X_data is not None and y_data is not None:
            medium, high = self._calibrate(X_data, y_data)
            self.medium_risk_threshold = medium
            self.high_risk_threshold   = high
            self._thresholds_source    = 'calibrated from unscaled data'
        else:
            self.medium_risk_threshold = medium_risk_threshold if medium_risk_threshold is not None else 0.35
            self.high_risk_threshold   = high_risk_threshold   if high_risk_threshold   is not None else 0.70
            self._thresholds_source    = 'provided' if medium_risk_threshold else 'default fallback'

        print('RuleBasedAgent initialised.')
        print(f'  Thresholds source     : {self._thresholds_source}')
        print(f'  Medium risk threshold : {self.medium_risk_threshold:.3f}  (→ SLOW DOWN)')
        print(f'  High risk threshold   : {self.high_risk_threshold:.3f}  (→ BRAKE/EVASIVE)')
        print(f'  Emergency decel       : {self.emergency_decel} m/s²  (ISO 22179)')
        print(f'  k_distance            : {self.k_distance}')
        print(f'  k_speed               : {self.k_speed}')
        print(f'  k_accel               : {self.k_accel}')
        print(f'  k_lean                : {self.k_lean}')
        print(f'  k_variance            : {self.k_variance}')

    def _calibrate(self, X_data, y_data):
        """Compute P33 and P66 thresholds from UNSCALED data."""
        print('  Calibrating thresholds from data...')
        n = len(X_data)

        # X_data must be UNSCALED — pass X_test_raw from run_demo.py
        risk_scores = np.array([
            self.compute_risk(X_data[i, -1, :])   # ← no mental_state
            for i in range(n)
        ])

        medium = float(np.percentile(risk_scores, 33))
        high   = float(np.percentile(risk_scores, 66))

        state_names = ['Waiting','Hesitant','Committed',
                    'Distracted','Aggressive','Jaywalk']
        print(f'  Risk scores — n={n}  '
            f'min={risk_scores.min():.3f}  '
            f'mean={risk_scores.mean():.3f}  '
            f'max={risk_scores.max():.3f}')
        print(f'  Per-class mean risk:')
        for i, name in enumerate(state_names):
            mask = y_data == i
            if mask.sum() > 0:
                print(f'    {name:<12} n={mask.sum():4d}  '
                    f'mean={risk_scores[mask].mean():.3f}')
        print(f'  Thresholds → P33={medium:.3f}  P66={high:.3f}')
        return medium, high
    
    def stopping_distance(self, speed_kmh):
        """s = v² / (2a)  — ISO 22179 AEB standard"""
        v = speed_kmh / 3.6
        return (v ** 2) / (2.0 * self.emergency_decel)

    def dist_to_metres(self, F32):
        return float(F32) * self.frame_width_metres

    def decode_traffic_light(self, F31):
        if F31 == 0.0: return 'red'
        if F31 == 0.5: return 'yellow'
        if F31 == 1.0: return 'green'
        return 'none'

    def compute_risk(self, F, probs=None):

        dist_change  = float(F[F_DISTANCE_CHANGE_RATE])
        speed        = float(F[F_CURRENT_SPEED])
        acceleration = float(F[F_ACCELERATION])
        fwd_lean     = float(F[F_FORWARD_LEAN])
        speed_var    = float(F[F_SPEED_VARIANCE])
        vehicle_dist = float(F[F_VEHICLE_DISTANCE])
        hesit        = float(F[F_HESITATION_CYCLES])

        # ── Scale parameters computed from PIE training data ──
        # Generated by compute_scale_params(X_train)
        # At x=k_mean → probability = 1 - exp(-1) = 0.63
        # i.e. average behaviour maps to 63% risk contribution
        k_distance = self.k_distance
        k_speed    = self.k_speed
        k_accel    = self.k_accel
        k_lean     = self.k_lean
        k_variance = self.k_variance

        # ── Probability functions ──
        p_distance = np.exp(-vehicle_dist / k_distance)
        p_toward   = (np.clip(dist_change, -1.0, 1.0) + 1.0) / 2.0
        p_speed    = 1.0 - np.exp(-speed    / k_speed)
        p_accel    = 1.0 - np.exp(-np.abs(acceleration) / k_accel)
        p_lean     = 1.0 - np.exp(-fwd_lean / k_lean)
        p_variance = 1.0 - np.exp(-speed_var / k_variance)
        p_hesit    = float(np.clip(hesit, 0.0, 1.0))

       
        W = 1.0 / 7.0
        p_kinematic = W * (p_distance + p_toward + p_speed +
                        p_accel + p_lean + p_variance + p_hesit)

        if probs is not None:
            # Crossing probability from LSTM+GRU ensemble
            # crossing states = Committed(2) + Aggressive(4) + Jaywalk(5)
            p_model = float(probs[2] + probs[4] + probs[5])
            risk = 0.5 * p_kinematic + 0.5 * p_model
        else:
            risk = p_kinematic

        return float(np.clip(risk, 0.0, 1.0))

    def decide(self, F, mental_state, confidence, probs=None,
               vehicle_speed_kmh=50.0):
        """
        Make AV action decision. Returns AgentDecision.

        Decision pipeline:
          1. Traffic light — legal override
          2. Risk + Physics — no confidence threshold
        """
        tl_raw     = float(F[F_TRAFFIC_LIGHT])
        tl_str     = self.decode_traffic_light(tl_raw)
        dist_m     = self.dist_to_metres(float(F[F_VEHICLE_DISTANCE]))
        stop_m     = self.stopping_distance(vehicle_speed_kmh)
        can_stop   = dist_m >= stop_m
        state_name = LABEL_NAMES.get(mental_state, 'Unknown')
        risk = self.compute_risk(F, probs=probs)

        def make(action, reason):
            return AgentDecision(
                action=action, reason=reason,
                risk_score=risk, mental_state=mental_state,
                state_name=state_name, confidence=confidence,
                traffic_light=tl_str, dist_metres=dist_m,
                stop_dist_m=stop_m, can_stop=can_stop,
            )

        # ── PRIORITY 1: Traffic light ──────────────────────────
        if tl_str == 'red':
            return make('BRAKE',
                'Traffic light RED — legal obligation to stop.')

        if tl_str == 'yellow':
            if can_stop:
                return make('SLOW_DOWN',
                    f'Traffic light YELLOW — {dist_m:.1f}m available, '
                    f'need {stop_m:.1f}m to stop. Slowing down.')
            else:
                return make('BRAKE',
                    f'Traffic light YELLOW — dilemma zone. '
                    f'Only {dist_m:.1f}m but need {stop_m:.1f}m to stop. '
                    f'Braking hard now to avoid running red.')

        # ── PRIORITY 2: Risk  ─────────────────────────
        # it combines mental state prediction AND kinematic features.
        if risk >= self.high_risk_threshold:
            if not can_stop:
                return make('EVASIVE',
                    f'CRITICAL: {state_name} — high risk {risk:.2f}. '
                    f'Distance {dist_m:.1f}m < stop distance {stop_m:.1f}m '
                    f'at {vehicle_speed_kmh:.0f} km/h. '
                    'Cannot stop — evasive manoeuvre.')
            else:
                return make('BRAKE',
                    f'{state_name} — high crossing risk {risk:.2f}. '
                    f'Distance {dist_m:.1f}m sufficient. '
                    'Applying emergency brake.')

        if risk >= self.medium_risk_threshold:
            return make('SLOW_DOWN',
                f'{state_name} — medium crossing risk {risk:.2f}. '
                'Reducing speed and monitoring.')

        return make('MAINTAIN',
            f'{state_name} — low crossing risk {risk:.2f}. '
            'Safe to maintain current speed.')


# ══════════════════════════════════════════════════════════════
# FULL PIPELINE HELPER
# ══════════════════════════════════════════════════════════════

def run_pipeline(sequence_36_raw, F_last_frame,
                 vehicle_speed_kmh, agent):
    """
    Full pipeline: raw features → ensemble → agent decision.

    Args:
        sequence_36_raw  : np.array (30, 36) — raw unscaled features
        F_last_frame     : np.array (36,) — most recent frame features
        vehicle_speed_kmh: float — current AV speed
        agent            : RuleBasedAgent instance

    Returns:
        decision : AgentDecision
        detail   : dict with mental_state, confidence, probs,
                   individual model outputs
    """
    mental_state, confidence, probs, model_detail = \
        predict_mental_state(sequence_36_raw)

    decision = agent.decide(
        F                 = F_last_frame,
        mental_state      = mental_state,
        confidence        = confidence,
        vehicle_speed_kmh = vehicle_speed_kmh,
    )

    return decision, {
        'mental_state': mental_state,
        'state_name':   LABEL_NAMES[mental_state],
        'confidence':   confidence,
        'probs':        probs.tolist(),
        'models':       model_detail,
    }


# ══════════════════════════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':

    
    agent = RuleBasedAgent()

    def make_F(traffic_light=-1.0, vehicle_dist=0.5, crosswalk=0.0,
               speed=5.0, speed_var=20.0, dist_change=0.01,
               pause=0.1, hesit=0.2, looks_l=0.0, looks_r=0.0,
               head_turns=0.1, fwd_lean=5.0, move_prob=0.3):
        F = np.zeros(36, dtype=np.float32)
        F[F_CURRENT_SPEED]        = speed
        F[F_SPEED_VARIANCE]       = speed_var
        F[F_DISTANCE_CHANGE_RATE] = dist_change
        F[F_PAUSE_DURATION]       = pause
        F[F_HESITATION_CYCLES]    = hesit
        F[F_HEAD_TURN_FREQUENCY]  = head_turns
        F[F_LOOKS_LEFT]           = looks_l
        F[F_LOOKS_RIGHT]          = looks_r
        F[F_FORWARD_LEAN]         = fwd_lean
        F[F_MOVEMENT_PROBABILITY] = move_prob
        F[F_TRAFFIC_LIGHT]        = traffic_light
        F[F_VEHICLE_DISTANCE]     = vehicle_dist
        F[F_CROSSWALK]            = crosswalk
        return F

    scenarios = [
        ('1. RED LIGHT',
         make_F(traffic_light=0.0, vehicle_dist=0.8),
         0, 0.92, 50.0),
        ('2. COMMITTED — enough distance',
         make_F(vehicle_dist=0.6, crosswalk=1.0,
                speed=15.0, dist_change=0.02),
         2, 0.88, 40.0),
        ('3. AGGRESSIVE toward road — too close',
         make_F(vehicle_dist=0.15, speed=20.0,
                speed_var=400.0, dist_change=0.05),
         4, 0.79, 60.0),
        ('4. AGGRESSIVE away from road',
         make_F(vehicle_dist=0.5, speed=18.0,
                speed_var=350.0, dist_change=-0.03),
         4, 0.75, 50.0),
        ('5. JAYWALK — low confidence, high risk',
         make_F(traffic_light=1.0, vehicle_dist=0.4,
                speed=10.0, dist_change=0.02, head_turns=0.4),
         5, 0.52, 45.0),
        ('6. WAITING at crosswalk',
         make_F(traffic_light=1.0, vehicle_dist=0.7,
                crosswalk=1.0, speed=0.5, pause=0.8),
         0, 0.91, 50.0),
        ('7. DISTRACTED drifting toward road',
         make_F(vehicle_dist=0.5, speed=3.0, dist_change=0.01),
         3, 0.72, 40.0),
        ('8. HESITANT approaching crosswalk',
         make_F(traffic_light=1.0, vehicle_dist=0.5,
                crosswalk=1.0, speed=4.0, hesit=0.6,
                dist_change=0.01, head_turns=0.3),
         1, 0.76, 40.0),
        ('9. YELLOW LIGHT — can stop',
         make_F(traffic_light=0.5, vehicle_dist=0.8),
         0, 0.90, 50.0),
        ('10. YELLOW LIGHT — dilemma zone',
         make_F(traffic_light=0.5, vehicle_dist=0.2),
         0, 0.90, 80.0),
    ]

    print('\n' + '='*55)
    print('SCENARIO TESTS')
    print('='*55)

    for name, F, state, conf, speed in scenarios:
        print(f'\n{"─"*55}')
        print(f'SCENARIO : {name}')
        print(f'  Speed={speed}km/h | '
              f'State={LABEL_NAMES[state]} | Conf={conf:.0%}')
        d = agent.decide(F, state, conf, speed)
        print(d.summary())

    config = {
        'medium_risk_threshold': agent.medium_risk_threshold,
        'high_risk_threshold':   agent.high_risk_threshold,
        'confidence_threshold':  'removed',
        'emergency_decel_ms2':   agent.emergency_decel,
        'frame_width_metres':    agent.frame_width_metres,
        'ensemble_method':       'simple average — equal weights',
        'ensemble_rationale':    (
            'Equal weights chosen because accuracy-based weighting '
            'is counterbalanced by overfitting penalties '
            '(LSTM gap=14.2%, GRU gap=14.1%, Transformer gap=10.6%), '
            'resulting in weights statistically indistinguishable '
            'from uniform averaging.'
        ),
        'ensemble_models': [
            'lstm_mental_state_best.h5',
            'gru_mental_state_best.h5',
        ],
        'actions':     list(ACTIONS.keys()),
        'label_names': LABEL_NAMES,
    }
    with open('agent_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print('\n✅ agent_config.json saved.')