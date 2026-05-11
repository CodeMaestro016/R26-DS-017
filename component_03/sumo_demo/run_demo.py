"""
run_demo.py
Proactive Social Compliance Modeling — SUMO Demo

ENSEMBLE VERSION: LSTM + GRU

Uses REAL PIE test sequences from X_test.npy.
Each run picks one random real sequence.
ONE run = ONE pedestrian = ONE result.

IMPORTANT:
  Ensemble inference → uses X_test        (scaled)
  agent.decide()     → uses X_test_raw    (unscaled — pixels/frame)
  AV speed taken from SUMO after simulation starts.

DECISION METHOD:
  Mental state + TTC rule-based agent.
  TTC >= 3.0s  → LOW/Safe
  TTC < 3.0s   → MEDIUM/Warning
  TTC < 1.5s   → HIGH/Emergency

Run: python run_demo.py
"""

import os
import sys
import random
import time

import numpy as np
import joblib


# ── SUMO setup ────────────────────────────────────────────────
os.environ['SUMO_HOME'] = r'C:\Program Files (x86)\Eclipse\Sumo'
sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci


# ── TensorFlow quiet mode ─────────────────────────────────────
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')


# ── Ensemble + rule-based agent ───────────────────────────────
from rule_based_agent import (
    load_ensemble,
    predict_from_scaled_sequence,
    RuleBasedAgent,
    LABELS,
    F_TRAFFIC_LIGHT,
    F_VEHICLE_DISTANCE,
    F_CURRENT_SPEED,
)


# ── CONFIG ────────────────────────────────────────────────────
SUMO_CFG     = 'simulation.sumocfg'
X_TEST_FILE  = 'X_test.npy'
Y_TEST_FILE  = 'y_test.npy'
SCALER_FILE  = 'feature_scaler.pkl'
AV_ID        = 'av_0'
AV_MAX_SPEED = 13.89    # m/s = 50 km/h fallback


LABEL_ICONS = {
    'Waiting':    '🧍',
    'Hesitant':   '🤔',
    'Committed':  '🚶',
    'Distracted': '📱',
    'Aggressive': '😠',
    'Jaywalk':    '⚠️',
}

LABEL_DESC = {
    'Waiting':    'Pedestrian standing still at kerb',
    'Hesitant':   'Pedestrian approaching slowly / uncertain',
    'Committed':  'Pedestrian committed to crossing',
    'Distracted': 'Pedestrian distracted / reduced awareness',
    'Aggressive': 'Pedestrian moving aggressively or unpredictably',
    'Jaywalk':    'Pedestrian crossing outside expected legal context',
}

# Expected simple behaviour. Close TTC can make Waiting/Hesitant STOP.
EXPECTED_ACTION = {
    'Waiting':    ['MAINTAIN', 'SLOW_DOWN', 'STOP'],
    'Hesitant':   ['MAINTAIN', 'SLOW_DOWN', 'STOP'],
    'Committed':  ['SLOW_DOWN', 'STOP'],
    'Distracted': ['SLOW_DOWN', 'STOP'],
    'Aggressive': ['SLOW_DOWN', 'STOP'],
    'Jaywalk':    ['SLOW_DOWN', 'STOP'],
}

# Console colours
SC = {
    'Waiting':    '\033[97m',
    'Hesitant':   '\033[33m',
    'Committed':  '\033[32m',
    'Distracted': '\033[34m',
    'Aggressive': '\033[31m',
    'Jaywalk':    '\033[35m',
}
AC = {
    'MAINTAIN':  '\033[92m',
    'SLOW_DOWN': '\033[93m',
    'STOP':     '\033[91m',
}
RESET = '\033[0m'
BOLD  = '\033[1m'


# ── File checks ───────────────────────────────────────────────
def check_files():
    required = [
        'lstm_mental_state_best.h5',
        'gru_mental_state_best.h5',
        SCALER_FILE,
        X_TEST_FILE,
        Y_TEST_FILE,
        SUMO_CFG,
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        print('ERROR — missing files:')
        for f in missing:
            print(f'  ✗ {f}')
        print('\nCopy the missing files into the sumo_demo/ folder.')
        sys.exit(1)
    print('✅ All required files found.')


def load_test_data():
    """
    Load X_test scaled for ensemble inference.
    Reconstruct raw feature values for the rule-based agent.
    """
    X_test = np.load(X_TEST_FILE)
    y_test = np.load(Y_TEST_FILE)

    print(f'✅ X_test     : {X_test.shape}  (scaled — for LSTM + GRU)')
    print(f'✅ y_test     : {y_test.shape}')

    scaler = joblib.load(SCALER_FILE)
    n, seq, feat = X_test.shape
    X_test_raw = scaler.inverse_transform(
        X_test.reshape(-1, feat)
    ).reshape(n, seq, feat)

    print(f'✅ X_test_raw : {X_test_raw.shape}  (unscaled — for agent)')
    print(f'   speed mean      : {X_test_raw[:, -1, F_CURRENT_SPEED].mean():.2f} px/frame')
    print(f'   vehicle_dist    : {X_test_raw[:, -1, F_VEHICLE_DISTANCE].mean():.4f}')

    return X_test, X_test_raw, y_test


# ── Result printer ────────────────────────────────────────────
def print_result(true_name, probs, decision, idx, inference_ms, av_speed_kmh):
    pred_id     = int(np.argmax(probs))
    pred_state  = LABELS[pred_id]
    confidence  = float(max(probs)) * 100.0
    action      = decision['action']
    sc          = SC.get(pred_state, '')
    ac          = AC.get(action, '')
    expected    = EXPECTED_ACTION.get(true_name, [])
    correct     = '✅' if action in expected else '⚠️'
    pred_ok     = '✅' if pred_state == true_name else '⚠️'
    icon        = LABEL_ICONS.get(true_name, '')
    desc        = LABEL_DESC.get(true_name, '')

    ttc_str = (
        f"{decision['ttc']:.2f} s"
        if np.isfinite(decision['ttc'])
        else 'N/A'
    )

    print(f'\n{"═" * 62}')
    print(f'  {icon}  {desc}')
    print(f'  Real PIE test sequence #{idx}')
    print(f'{"═" * 62}')

    print(f'\n  📋 Ground truth    : {true_name}')
    pixel_distance = decision['pixel_distance']
    print(f"  📍 Distance        : {pixel_distance:.2f} px")
    print(f'  🚗 AV speed        : {av_speed_kmh:.1f} km/h from SUMO')

    print(f'\n  🧠 Ensemble prediction:')
    print(f'     Mental state   : {sc}{BOLD}{pred_state}{RESET}  {pred_ok}')
    print(f'     Confidence     : {confidence:.1f}%')

    print(f'\n  📊 Ensemble probabilities:')
    for state_id, name in LABELS.items():
        p      = float(probs[state_id])
        filled = int(p * 30)
        bar    = '█' * filled + '░' * (30 - filled)
        sc2    = SC.get(name, '')
        pred_m = f'  ← {BOLD}predicted{RESET}' if name == pred_state else ''
        true_m = '  (true)' if name == true_name else ''
        print(f'     {sc2}{name:<13}{RESET}  {bar}  {p * 100:5.1f}%{pred_m}{true_m}')

    print(f'\n  🚗 AV Decision:')
    print(f'     Action         : {ac}{BOLD}{action}{RESET}  {correct}')
    print(f"     Reason         : {decision['reason']}")
    print(f'     TTC            : {ttc_str}')
    print(f"     TTC level      : {decision['ttc_level'].upper()}")
    print(f"     Ped speed      : {decision['pixel_speed']:.2f} px/frame")

    print(f'\n  ⏱  Runtime Measurement:')
    print(f'     Inference + decision time : {inference_ms:.2f} ms')
    print(f'     Pipeline                 : scaled sequence → LSTM + GRU → average → agent')

    print(f'\n{"═" * 62}')


# ── SUMO speed mapping ────────────────────────────────────────
ACTION_SPEED = {
    'MAINTAIN':  1.0,
    'SLOW_DOWN': 0.6,
    'STOP':     0.0,
}


# ── Main run ──────────────────────────────────────────────────
def run(X_test, X_test_raw, y_test, agent):
    """Pick one random real test sequence and run the full pipeline."""

    idx        = random.randint(0, len(X_test) - 1)
    true_label = int(y_test[idx])
    true_name  = LABELS[true_label]

    # Scaled sequence for ensemble
    seq_scaled = X_test[idx]

    # Raw last frame for rule-based agent
    F_raw = X_test_raw[idx, -1, :].copy()

    # Optional: set traffic light if your feature uses it.
    # This does NOT change distance/speed.
    F_raw[F_TRAFFIC_LIGHT] = 1.0

    ped_dist_px = float(F_raw[F_VEHICLE_DISTANCE]) * 1920.0

    print(f'\n  Selected sequence  : #{idx}')
    print(f'  True label         : {LABEL_ICONS.get(true_name, "")} {true_name}')
    print(f'  Pedestrian dist    : {ped_dist_px:.2f} px')
    print(f'  Ped speed raw      : {F_raw[F_CURRENT_SPEED]:.2f} px/frame')

    # ── STEP 1: Start SUMO and get real AV speed ──────────────
    sumo_cmd = [
        r'C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe',
        '-c', SUMO_CFG,
        '--start',
        '--quit-on-end', 'false',
        '--delay', '100',
        '--window-size', '1200,600',
    ]
    traci.start(sumo_cmd)

    for _ in range(20):
        traci.simulationStep()

    if AV_ID in traci.vehicle.getIDList():
        av_speed_ms  = traci.vehicle.getSpeed(AV_ID)
        av_speed_kmh = av_speed_ms * 3.6
    else:
        av_speed_ms  = AV_MAX_SPEED
        av_speed_kmh = AV_MAX_SPEED * 3.6

    print(f'  SUMO AV speed      : {av_speed_ms:.2f} m/s ({av_speed_kmh:.1f} km/h)')

    # ── STEP 2: Warm up TensorFlow ────────────────────────────
    _ = predict_from_scaled_sequence(seq_scaled)
    _ = predict_from_scaled_sequence(seq_scaled)

    # ── STEP 3: Timed prediction + decision ───────────────────
    t_start = time.perf_counter()

    mental_state, confidence, probs, model_detail = predict_from_scaled_sequence(seq_scaled)

    decision = agent.decide(
        F=F_raw,
        mental_state=mental_state,
        confidence=confidence,
        vehicle_speed_kmh=av_speed_kmh,
    )

    t_end = time.perf_counter()
    inference_ms = (t_end - t_start) * 1000.0

    # ── STEP 4: Apply action to SUMO ──────────────────────────
    action       = decision['action']
    speed_factor = ACTION_SPEED.get(action, 0.6)
    target_speed_ms = av_speed_ms * speed_factor

    if AV_ID in traci.vehicle.getIDList():
        traci.vehicle.setSpeed(AV_ID, target_speed_ms)
        print(f'  SUMO AV speed set  : {target_speed_ms:.2f} m/s ({target_speed_ms * 3.6:.1f} km/h)')

    for _ in range(40):
        traci.simulationStep()

    # ── STEP 5: Print result ──────────────────────────────────
    print_result(true_name, probs, decision, idx, inference_ms, av_speed_kmh)

    time.sleep(3)
    traci.close()


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':
    print(f'{"═" * 62}')
    print(f'  {BOLD}Proactive Social Compliance Modeling — SUMO Demo{RESET}')
    print(f'  Ensemble: LSTM + GRU')
    print(f'  Decision: Mental state + TTC rule-based agent')
    print(f'{"═" * 62}\n')

    check_files()

    # rule_based_agent.py loads LSTM + GRU + scaler
    load_ensemble()

    X_test, X_test_raw, y_test = load_test_data()

    print('\nInitialising agent...')
    agent = RuleBasedAgent()

    run(X_test, X_test_raw, y_test, agent)

    print('\n  Done. Run again for a different sequence.')
