"""
run_demo.py
Proactive Social Compliance Modeling — SUMO Demo

ENSEMBLE VERSION: LSTM + GRU

Uses REAL PIE test sequences from X_test.npy.
Each run picks several random real sequences — one per SIMULATED
pedestrian — and treats them as all being visible in the SAME frame.
ONE run = ONE frame = several pedestrians = ONE AV action.

Pipeline per run (mirrors rule_based_agent.MultiPedestrianAVController):

    Current frame
          |
    Select N pedestrians (stand-ins for "detect all pedestrians",
    since this demo replays real PIE sequences instead of a live
    detector)
          |
    For each pedestrian:
          |-- features already extracted (X_test_raw, last frame)
          |-- predict mental state  (ensemble: LSTM + GRU on X_test)
          |-- calculate TTC         (rule_based_agent.RuleBasedAgent)
          |
    Compare all pedestrians
          |
    Select pedestrian with minimum TTC (highest risk)
          |
    Take AV action  (applied to the SUMO vehicle)

IMPORTANT:
  Ensemble inference → uses X_test        (scaled)
  agent.decide()     → uses X_test_raw    (unscaled — pixels/frame)
  AV speed taken from SUMO after simulation starts.
  All of the above happens once PER pedestrian, per frame.

DECISION METHOD:
  Per pedestrian : mental state + TTC rule-based agent
                   (see rule_based_agent.py for the exact TTC_WARNING /
                   TTC_EMERGENCY thresholds and the literature behind
                   them — currently 2.5s / 1.5s).
  Per frame      : the pedestrian with the MINIMUM TTC across all
                   detected pedestrians is treated as highest risk,
                   and the AV acts on that pedestrian's decision (see
                   MultiPedestrianAVController in rule_based_agent.py
                   for the rationale — this is the standard
                   "most-critical-target" selection rule used in
                   published AEB / forward-collision-warning work).

Run: python run_demo.py
"""

import os
import sys
import random
import time

import numpy as np
import joblib


# ── Project paths ────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUMO_DEMO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
ROOT_DIR = os.path.abspath(os.path.join(SUMO_DEMO_DIR, '..', '..'))


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
    MultiPedestrianAVController,
    PedestrianObservation,
    LABELS,
    F_TRAFFIC_LIGHT,
    F_VEHICLE_DISTANCE,
    F_CURRENT_SPEED,
)


# ── CONFIG ────────────────────────────────────────────────────
SUMO_CFG     = os.path.join(SUMO_DEMO_DIR, 'config', 'simulation.sumocfg')
X_TEST_FILE  = os.path.join(SUMO_DEMO_DIR, 'data', 'X_test.npy')
Y_TEST_FILE  = os.path.join(SUMO_DEMO_DIR, 'data', 'y_test.npy')
SCALER_FILE  = os.path.join(SUMO_DEMO_DIR, 'models', 'scaler.joblib')
LSTM_FILE    = os.path.join(SUMO_DEMO_DIR, 'models', 'lstm_mental_state_best.keras')
GRU_FILE     = os.path.join(SUMO_DEMO_DIR, 'models', 'gru_mental_state_best.keras')
AV_ID        = 'av_0'
AV_MAX_SPEED = 13.89    # m/s = 50 km/h fallback
NUM_PEDESTRIANS = 4  # how many pedestrians to simulate as visible in this frame


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
        LSTM_FILE,
        GRU_FILE,
        SCALER_FILE,
        X_TEST_FILE,
        Y_TEST_FILE,
        SUMO_CFG,
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        print('ERROR — missing files:')
        for f in missing:
            print(f'  ✗ {os.path.relpath(f, ROOT_DIR)}')
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


# ── Per-pedestrian result printer ─────────────────────────────
def print_pedestrian_block(ped_id, meta, decision):
    """Print one pedestrian's ensemble prediction + own (pre-comparison) decision."""
    true_name  = meta['true_name']
    idx        = meta['idx']
    probs      = meta['probs']

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

    print(f'\n{"─" * 62}')
    print(f'  {icon}  [{ped_id}]  {desc}')
    print(f'  Real PIE test sequence #{idx}')
    print(f'{"─" * 62}')

    print(f'\n  📋 Ground truth    : {true_name}')
    print(f"  📍 Distance        : {decision['pixel_distance']:.2f} px")

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

    print(f'\n  🚦 This pedestrian\'s own decision (before cross-pedestrian comparison):')
    print(f'     Action         : {ac}{BOLD}{action}{RESET}  {correct}')
    print(f"     Reason         : {decision['reason']}")
    print(f'     TTC            : {ttc_str}')
    print(f"     TTC level      : {decision['ttc_level'].upper()}")
    print(f"     Ped speed      : {decision['pixel_speed']:.2f} px/frame")


# ── Frame-level (compare + select + act) printer ──────────────
def print_frame_summary(frame_decision, meta_by_id, inference_ms, av_speed_kmh, target_speed_ms):
    print(f'\n{"═" * 62}')
    print(f'  {BOLD}FRAME SUMMARY — compare all pedestrians, act on min TTC{RESET}')
    print(f'{"═" * 62}')
    print(f'  🚗 AV speed (SUMO)     : {av_speed_kmh:.1f} km/h')

    print(f"\n  {'Pedestrian':<16}{'True state':<12}{'TTC':>9}  {'Level':<8}{'Own action'}")
    print(f'  {"-" * 58}')
    for r in frame_decision['ranking']:
        pid       = r['pedestrian_id']
        true_name = meta_by_id[pid]['true_name']
        ttc_text  = f"{r['ttc']:.2f}s" if np.isfinite(r['ttc']) else 'N/A'
        marker    = '  ⬅ CRITICAL' if pid == frame_decision['critical_pedestrian_id'] else ''
        print(f"  {pid:<16}{true_name:<12}{ttc_text:>9}  {r['ttc_level']:<8}{r['action']}{marker}")

    ac = AC.get(frame_decision['action'], '')
    print(f'\n  🚨 CRITICAL PEDESTRIAN : {frame_decision["critical_pedestrian_id"]}')
    print(f'  🚗 FINAL AV ACTION     : {ac}{BOLD}{frame_decision["action"]}{RESET}')
    print(f"  ℹ️  Reason              : {frame_decision['reason']}")
    print(f'  🎯 AV speed set        : {target_speed_ms:.2f} m/s ({target_speed_ms * 3.6:.1f} km/h)')
    print(f'\n  ⏱  Ensemble + decision + selection time: {inference_ms:.2f} ms '
          f'(across {len(meta_by_id)} pedestrians)')
    print(f'{"═" * 62}')


# ── SUMO speed mapping ────────────────────────────────────────
ACTION_SPEED = {
    'MAINTAIN':  1.0,
    'SLOW_DOWN': 0.6,
    'STOP':     0.0,
}


# ── Main run ──────────────────────────────────────────────────
def run(X_test, X_test_raw, y_test, controller):
    """
    Pick several random real test sequences (one per simulated
    pedestrian, standing in for a live detector's output), run the
    full per-pedestrian pipeline, then compare and act on the
    highest-risk (minimum TTC) pedestrian for this frame.
    """

    n_peds = min(random.randint(1, 4), len(X_test))
    indices = random.sample(range(len(X_test)), n_peds)

    print(f'\n  Simulating {n_peds} pedestrians visible in this frame')
    print(f'  (each drawn from a different real PIE test sequence,')
    print(f'   standing in for a live pedestrian detector\'s output)')
    for i, idx in enumerate(indices):
        true_name = LABELS[int(y_test[idx])]
        icon = LABEL_ICONS.get(true_name, '')
        print(f'    P{i + 1}: seq #{idx:<6} true={icon} {true_name}')

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
    _ = predict_from_scaled_sequence(X_test[indices[0]])
    _ = predict_from_scaled_sequence(X_test[indices[0]])

    # ── STEP 3: Timed — for each pedestrian: predict mental state +
    #            calculate TTC; then compare all pedestrians and
    #            select the minimum-TTC (highest risk) one ────────
    t_start = time.perf_counter()

    observations = []
    meta_by_id   = {}

    for i, idx in enumerate(indices):
        true_label = int(y_test[idx])
        true_name  = LABELS[true_label]

        seq_scaled = X_test[idx]                     # ensemble input (scaled)
        F_raw = X_test_raw[idx, -1, :].copy()         # agent input (raw, last frame)
        F_raw[F_TRAFFIC_LIGHT] = 1.0

        mental_state, confidence, probs, _detail = predict_from_scaled_sequence(seq_scaled)

        ped_id = f'P{i + 1}_seq{idx}'
        observations.append(PedestrianObservation(
            ped_id=ped_id,
            F=F_raw,
            mental_state=mental_state,
            confidence=confidence,
        ))
        meta_by_id[ped_id] = {'idx': idx, 'true_name': true_name, 'probs': probs}

    # -- compare all pedestrians -> select minimum TTC -> take AV action --
    frame_decision = controller.process_frame(observations, vehicle_speed_kmh=av_speed_kmh)

    t_end = time.perf_counter()
    inference_ms = (t_end - t_start) * 1000.0

    # ── STEP 4: Apply the selected (highest-risk) action to SUMO ──
    action          = frame_decision['action']
    speed_factor    = ACTION_SPEED.get(action, 0.6)
    target_speed_ms = av_speed_ms * speed_factor

    if AV_ID in traci.vehicle.getIDList():
        traci.vehicle.setSpeed(AV_ID, target_speed_ms)
        print(f'  SUMO AV speed set  : {target_speed_ms:.2f} m/s ({target_speed_ms * 3.6:.1f} km/h)')

    for _ in range(40):
        traci.simulationStep()

    # ── STEP 5: Print results ──────────────────────────────────
    for i, idx in enumerate(indices):
        ped_id = f'P{i + 1}_seq{idx}'
        print_pedestrian_block(ped_id, meta_by_id[ped_id], frame_decision['all_results'][ped_id])

    print_frame_summary(frame_decision, meta_by_id, inference_ms, av_speed_kmh, target_speed_ms)

    time.sleep(3)
    traci.close()


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':
    print(f'{"═" * 62}')
    print(f'  {BOLD}Proactive Social Compliance Modeling — SUMO Demo{RESET}')
    print(f'  {BOLD}Multi-Pedestrian Frame Pipeline{RESET}')
    print(f'{"═" * 62}\n')

    check_files()

    # rule_based_agent.py loads LSTM + GRU + scaler
    load_ensemble()

    X_test, X_test_raw, y_test = load_test_data()

    print('\nInitialising agent + multi-pedestrian controller...')
    agent      = RuleBasedAgent()
    controller = MultiPedestrianAVController(agent=agent)

    run(X_test, X_test_raw, y_test, controller)

    print('\n  Done. Run again for a different set of pedestrians.')