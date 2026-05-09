"""
run_demo.py
Proactive Social Compliance Modeling — SUMO Demo

ENSEMBLE VERSION: LSTM + GRU

Uses REAL PIE test sequences from X_test.npy.
Each run picks one random real sequence.
ONE run = ONE pedestrian = ONE result.



Run: python run_demo.py
"""

import os
import sys
import random
import numpy as np

# ── SUMO setup ────────────────────────────────────────────────
os.environ['SUMO_HOME'] = r'C:\Program Files (x86)\Eclipse\Sumo'
sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci

# ── Ensemble agent ────────────────────────────────────────────
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

from rule_based_agent import (
    load_ensemble,
    predict_from_scaled_sequence,
    RuleBasedAgent,
    LABEL_NAMES,
)

# ── CONFIG ────────────────────────────────────────────────────
SUMO_CFG     = 'simulation.sumocfg'
X_TEST_FILE  = 'X_test.npy'
Y_TEST_FILE  = 'y_test.npy'
AV_ID        = 'av_0'
AV_MAX_SPEED = 13.89    # m/s = 50 km/h

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
    'Hesitant':   'Pedestrian approaching slowly, looking both ways',
    'Committed':  'Pedestrian stepping onto road',
    'Distracted': 'Pedestrian head down, not looking at road',
    'Aggressive': 'Pedestrian forcing way aggressively',
    'Jaywalk':    'Pedestrian crossing outside crosswalk',
}

# Expected correct action per mental state (for accuracy check)
EXPECTED_ACTION = {
    'Waiting':    'MAINTAIN',
    'Hesitant':   'SLOW_DOWN',
    'Committed':  'BRAKE',
    'Distracted': 'SLOW_DOWN',
    'Aggressive': 'BRAKE',
    'Jaywalk':    'BRAKE',
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
    'MAINTAIN':   '\033[92m',
    'SLOW_DOWN':  '\033[93m',
    'BRAKE':      '\033[91m',
    'EVASIVE':    '\033[95m',
}
RESET = '\033[0m'
BOLD  = '\033[1m'


# ── File checks ───────────────────────────────────────────────
def check_files():
    required = [
        'lstm_mental_state_best.h5',
        'gru_mental_state_best.h5',
        'feature_scaler.pkl',
        X_TEST_FILE,
        Y_TEST_FILE,
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        print('ERROR — missing files:')
        for f in missing:
            print(f'  ✗ {f}')
        print('\nCopy them from Google Drive → sumo_demo/ folder.')
        sys.exit(1)
    print('✅ All required files found.')


def load_test_data():
    X_test = np.load(X_TEST_FILE)
    y_test = np.load(Y_TEST_FILE)
    print(f'✅ X_test : {X_test.shape}')
    print(f'✅ y_test : {y_test.shape}')
    return X_test, y_test


# ── Result printer ────────────────────────────────────────────
def print_result(true_name, probs, model_detail, decision, ped_dist, idx):
    pred_state = LABEL_NAMES[int(np.argmax(probs))]
    confidence = float(max(probs)) * 100
    action     = decision.action
    sc         = SC.get(pred_state, '')
    ac         = AC.get(action, '')
    expected   = EXPECTED_ACTION.get(true_name, '')
    correct    = '✅' if action == expected else '⚠️'
    pred_ok    = '✅' if pred_state == true_name else '⚠️'
    icon       = LABEL_ICONS.get(true_name, '')
    desc       = LABEL_DESC.get(true_name, '')

    print(f'\n{"═"*62}')
    print(f'  {icon}  {desc}')
    print(f'  (Real PIE test sequence #{idx})')
    print(f'{"═"*62}')

    print(f'\n  📋 Ground truth    : {true_name}')
    print(f'  📍 Distance        : {ped_dist:.1f} m from AV')
    print(f'  🚦 Traffic light   : {decision.traffic_light}')

    print(f'\n  🧠 Ensemble prediction:')
    print(f'     Mental state   : {sc}{BOLD}{pred_state}{RESET}  {pred_ok}')
    print(f'     Confidence     : {confidence:.1f}%')
    print(f'     Risk score     : {decision.risk_score:.3f}')
    print(f'     Can stop       : {"YES" if decision.can_stop else "NO — EVASIVE"}')

    print(f'\n  📊 Ensemble probabilities:')
    for idx_c, (name, p) in enumerate(zip(LABEL_NAMES.values(), probs)):
        filled = int(p * 30)
        bar    = '█' * filled + '░' * (30 - filled)
        sc2    = SC.get(name, '')
        pred_m = f'  ← {BOLD}predicted{RESET}' if name == pred_state else ''
        true_m = '  (true)' if name == true_name else ''
        print(f'     {sc2}{name:<13}{RESET}  {bar}  {p*100:5.1f}%{pred_m}{true_m}')

    # print(f'\n  📊 Individual model breakdown:')
    # for model_name in ['lstm', 'gru']:
    #     mp     = model_detail[model_name]
    #     mp_arr = np.array(mp)
    #     top    = LABEL_NAMES[int(np.argmax(mp_arr))]
    #     print(f'     {model_name.upper():<12} → {top:<12} ({max(mp_arr)*100:.1f}%)')

    print(f'\n  🚗 AV Decision:')
    print(f'     Action         : {ac}{BOLD}{action}{RESET}  {correct}')
    print(f'     Reason         : {decision.reason}')
    print(f'     Target speed   : {decision.target_speed_kmh:.1f} km/h')
    print(f'     Stop distance  : {decision.stop_dist_m:.1f} m needed')
    print(f'\n{"═"*62}')


# ── SUMO speed factor ─────────────────────────────────────────
ACTION_SPEED = {
    'MAINTAIN':   1.0,
    'SLOW_DOWN':  0.6,
    'BRAKE':      0.2,
    'EVASIVE':    0.0,
}


# ── Main run ──────────────────────────────────────────────────
def run(X_test, y_test, agent):
    """Pick one random real test sequence and run the full pipeline."""

    idx        = random.randint(0, len(X_test) - 1)
    seq        = X_test[idx]               # (30, 36) — already scaled
    true_label = int(y_test[idx])
    true_name  = LABEL_NAMES[true_label]
    ped_dist   = random.uniform(15.0, 60.0)

    print(f'\n  Selected sequence  : #{idx}')
    print(f'  True label         : {LABEL_ICONS.get(true_name,"")} {true_name}')
    print(f'  Pedestrian dist    : {ped_dist:.1f} m')

    # ── Ensemble inference ────────────────────────────────────
    mental_state, confidence, probs, model_detail = \
        predict_from_scaled_sequence(seq)

    # ── Build feature vector for agent ───────────────────────
    # Use last frame of the sequence as the feature vector F
    # F[31] traffic light: simulate green (1.0) for demo
    # F[32] vehicle distance: convert ped_dist to 0-1 fraction
    F = seq[-1].copy()                     # last frame (36,)
    F[31] = 1.0                            # green light
    F[32] = ped_dist / agent.frame_width_metres   # dist as fraction

    # ── Agent decision ────────────────────────────────────────
    decision = agent.decide(
        F                 = F,
        mental_state      = mental_state,
        confidence        = confidence,
        vehicle_speed_kmh = AV_MAX_SPEED * 3.6,
    )

    # Store target_speed_kmh on decision for printing
    speed_factor = ACTION_SPEED.get(decision.action, 0.6)
    decision.target_speed_kmh = AV_MAX_SPEED * 3.6 * speed_factor
    target_speed_ms = AV_MAX_SPEED * speed_factor

    # ── SUMO ─────────────────────────────────────────────────
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
        traci.vehicle.setSpeed(AV_ID, target_speed_ms)
        print(f'  SUMO AV speed set  : {target_speed_ms:.2f} m/s '
              f'({decision.target_speed_kmh:.1f} km/h)')

    for _ in range(40):
        traci.simulationStep()

    # ── Print full result ─────────────────────────────────────
    print_result(true_name, probs, model_detail, decision, ped_dist, idx)

    import time
    time.sleep(3)
    traci.close()


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':
    print(f'{"═"*62}')
    print(f'  {BOLD}Proactive Social Compliance Modeling — SUMO Demo{RESET}')
    print(f'  Ensemble: LSTM + GRU')
    print(f'{"═"*62}\n')

    # 1. Check all files exist
    check_files()

    # 2. Load ensemble models (once)
    load_ensemble()

    # 3. Load test data
    X_test, y_test = load_test_data()

    # 4. Create agent — auto-calibrates thresholds from your data
    print('\nInitialising agent...')
    agent = RuleBasedAgent(X_data=X_test, y_data=y_test)

    # 5. Run one scenario
    run(X_test, y_test, agent)

    print('\n  Done. Run again for a different sequence.')