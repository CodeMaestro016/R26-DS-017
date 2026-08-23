# -*- coding: utf-8 -*-
"""
Clean Rule-Based Agent
Mental state + TTC -> AV action

Per-frame pipeline
-------------------
    Current frame
          |
    Detect all pedestrians
          |
    For each pedestrian:
          |-- Extract 36 features
          |-- Predict mental state
          |-- Calculate TTC
          |
    Compare all pedestrians
          |
    Select pedestrian with minimum TTC (highest risk)
          |
    Take AV action

Why "minimum TTC wins" is a scientifically grounded selection rule
--------------------------------------------------------------------
Time-to-Collision (TTC) is the standard surrogate safety measure for how
much reaction/braking time remains before an unsafe traffic event: the
smaller the TTC, the less time is left, and therefore the higher the
immediate risk. This was first formalised by Hayward (1972), "Near miss
determination through use of a scale of danger", Highway Research
Record 384, 24-34, and later extended and validated by Minderhoud &
Bovy (2001), "Extended time-to-collision measures for road traffic
safety assessment", Accident Analysis & Prevention, 33, 89-97.

When several road users are tracked at once, forward-collision-warning
/ AEB "threat assessment" algorithms evaluate TTC per target and act on
whichever target is most critical -- i.e. the one with the smallest
TTC -- rather than an average across targets or a fixed target. This
per-target evaluation + worst-case selection approach is exactly the
methodology used to evaluate collision-warning/avoidance algorithms in
Lee & Peng (2005), "Evaluation of automotive forward collision warning
and collision avoidance algorithms", Vehicle System Dynamics, 43(10),
735-751.

The specific TTC thresholds used below are also empirically grounded:
Haus, Sherony & Gabler (2019), "Estimated benefit of automated
emergency braking systems for vehicle-pedestrian crashes in the United
States", Traffic Injury Prevention, 20(sup1), S171-S176, modelled a
range of pedestrian-AEB configurations against real-world crash data
and found that braking triggered at TTC of about 1.5 s with near-zero
system latency gave the largest reduction in pedestrian fatality risk
(roughly 84-87%) among the configurations tested. That is why
TTC_EMERGENCY is set to 1.5 s below. TTC_WARNING is set above that
value to leave a reaction buffer before the emergency threshold is
reached, consistent with the graded TTC criticality scale used
throughout this literature (also see Kusano & Gabler, 2012, "Safety
benefits of forward collision warning, brake assist, and autonomous
braking systems in rear-end collisions", IEEE Transactions on
Intelligent Transportation Systems, 13, 1546-1555).

In short: among several detected pedestrians, prioritising the one
with the minimum TTC is not an arbitrary heuristic -- it is the same
"most-critical-target" rule used in published AEB / FCW threat
assessment work, applied here across pedestrians instead of vehicles.
"""

import numpy as np
import json
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


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
# Empirically the strongest pedestrian-AEB configuration in real-world
# crash data (Haus, Sherony & Gabler, 2019) -- see module docstring.
TTC_EMERGENCY = 1.5


# ══════════════════════════════════════════════════════════════
# ENSEMBLE MODEL LOADER
# (implements the "Predict mental state" step of the per-pedestrian loop)
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
        scaler.pkl
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

    lstm_path   = os.path.join(model_dir, 'lstm_mental_state_best.keras')
    gru_path    = os.path.join(model_dir, 'gru_mental_state_best.keras')
    scaler_path = os.path.join(model_dir, 'scaler.joblib')

    for path, name in [
        (lstm_path,   'lstm_mental_state_best.h5'),
        (gru_path,    'gru_mental_state_best.h5'),
        (scaler_path, 'scaler.pkl'),
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
# (implements "Calculate TTC" + the single-pedestrian action mapping)
# ══════════════════════════════════════════════════════════════

class RuleBasedAgent:
    """
    Simple AV decision agent for a SINGLE pedestrian.

    Input:
        F                 : 36 feature vector
        mental_state      : 0-5 predicted mental state
        vehicle_speed_kmh : current AV speed in km/h

    Output:
        action, reason, TTC

    Used inside `MultiPedestrianAVController` below, once per detected
    pedestrian, per frame.
    """

    def compute_ttc(self, pixel_distance, pixel_speed):
        print(f"pixel_distance={pixel_distance}, pixel_speed={pixel_speed}") 

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
        Main decision logic for one pedestrian.
        """

        state_name = LABELS.get(mental_state, "Unknown")

        # Image-space TTC
        # F[32] is normalised vehicle distance, so convert back to pixels
        pixel_distance = float(F[F_VEHICLE_DISTANCE]) * 1920.0
        pixel_speed    = float(F[F_CURRENT_SPEED])  * 1920.0

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


# ══════════════════════════════════════════════════════════════
# STEP 1 — DETECT ALL PEDESTRIANS  (pluggable interfaces)
# ══════════════════════════════════════════════════════════════

@dataclass
class PedestrianObservation:
    """
    One pedestrian's data for the current frame, ready for the
    decision pipeline.

    ped_id       : stable track ID for this pedestrian (from your
                   detector/tracker, e.g. a DeepSORT track id or a
                   SUMO TraCI person id).
    F            : (36,) raw feature vector for the CURRENT frame,
                   used for TTC (see the F_* indices above).
    sequence     : (30, 36) raw feature history for the ensemble
                   LSTM/GRU mental-state classifier. Optional if
                   `mental_state` is supplied directly.
    mental_state : precomputed mental state (0-5). Skips the ensemble
                   call. Useful for testing, or when another module
                   already ran the classifier for this frame.
    confidence   : confidence of `mental_state`, if supplied directly.
    """
    ped_id: str
    F: np.ndarray
    sequence: Optional[np.ndarray] = None
    mental_state: Optional[int] = None
    confidence: Optional[float] = None


def detect_pedestrians(frame):
    """
    STEP: "Detect all pedestrians" for the current frame.

    This is a pluggable interface, not an implementation — pedestrian
    detection/tracking (e.g. YOLOv8 + DeepSORT on camera frames, or
    `traci.person.getIDList()` in the SUMO demo) belongs to the
    project's perception module, not this decision-agent file.

    Wire your detector/tracker here so it returns a list of
    `PedestrianObservation` (using `extract_features()` below to fill
    in `F` / `sequence` for each track). Left as a stub so the
    integration point is explicit.
    """
    raise NotImplementedError(
        "Plug in your pedestrian detector/tracker here, e.g. "
        "YOLO+DeepSORT for camera frames, or traci.person.getIDList() "
        "for the SUMO demo. It should return one PedestrianObservation "
        "per detected pedestrian."
    )


def extract_features(pedestrian_track):
    """
    STEP: "Extract 36 features" for ONE detected pedestrian.

    Pluggable interface for the project's pose/kinematics/gaze feature
    extraction pipeline (the F_* indices at the top of this file
    define what each of the 36 values must mean). Replace this stub
    with that pipeline.
    """
    raise NotImplementedError(
        "Plug in the project's 36-feature extraction pipeline here "
        "(pose estimation, step/gait kinematics, gaze, vehicle "
        "distance, etc. — see the F_* indices at the top of this file)."
    )


# ══════════════════════════════════════════════════════════════
# FRAME-LEVEL CONTROLLER
# implements: per-pedestrian loop -> compare -> select min TTC
#             -> take AV action
# ══════════════════════════════════════════════════════════════

class MultiPedestrianAVController:
    """
    Orchestrates one full decision frame across every currently
    visible pedestrian, following the pipeline described in the
    module docstring (detect -> per-pedestrian state/TTC -> compare
    -> select minimum TTC -> act).
    """

    def __init__(self, agent: Optional[RuleBasedAgent] = None):
        self.agent = agent or RuleBasedAgent()

    # ---- per-pedestrian step: predict mental state + calculate TTC ----
    def _evaluate_pedestrian(self, ped: PedestrianObservation, vehicle_speed_kmh: float) -> Dict[str, Any]:
        if ped.mental_state is not None:
            mental_state = ped.mental_state
            confidence   = ped.confidence if ped.confidence is not None else 1.0
        else:
            if ped.sequence is None:
                raise ValueError(
                    f"Pedestrian '{ped.ped_id}': supply either `sequence` "
                    f"(30,36) to run the ensemble, or a precomputed `mental_state`."
                )
            mental_state, confidence, _probs, _detail = predict_mental_state(ped.sequence)

        result = self.agent.decide(
            ped.F, mental_state, confidence=confidence,
            vehicle_speed_kmh=vehicle_speed_kmh
        )
        result["pedestrian_id"] = ped.ped_id
        return result

    # ---- compare all pedestrians + select minimum TTC (highest risk) ----
    @staticmethod
    def _select_critical_pedestrian(results: Dict[str, Dict[str, Any]]):
        """
        See the module docstring for the literature behind "minimum
        finite TTC = highest risk" (Hayward, 1972; Minderhoud & Bovy,
        2001; Lee & Peng, 2005; Haus, Sherony & Gabler, 2019).

        Fallback: if NO pedestrian currently has a finite TTC (e.g.
        everyone is static or moving away from the vehicle's path),
        TTC alone cannot rank risk, so the pedestrian in the most
        urgent mental state is chosen instead — Jaywalk/Aggressive/
        Committed pedestrians are the ones most likely to enter the
        road unexpectedly even with no current closing speed.
        """
        finite_ttc = {pid: r for pid, r in results.items() if np.isfinite(r["ttc"])}

        if finite_ttc:
            critical_id = min(finite_ttc, key=lambda pid: finite_ttc[pid]["ttc"])
        else:
            severity_rank = {5: 0, 4: 1, 2: 2, 3: 3, 1: 4, 0: 5}  # lower = more urgent
            critical_id = min(
                results,
                key=lambda pid: severity_rank.get(results[pid]["mental_state"], 6)
            )

        return critical_id, results[critical_id]

    # ---- full per-frame pipeline ----
    def process_frame(self, pedestrians: List[PedestrianObservation],
                       vehicle_speed_kmh: float = 0.0) -> Dict[str, Any]:
        """
        Run the full pipeline for ONE frame:

            for each pedestrian: predict mental state + calculate TTC
            -> compare all pedestrians
            -> select minimum TTC (highest risk)
            -> take AV action

        `pedestrians` is the output of STEP 1 (`detect_pedestrians` +
        `extract_features`), i.e. a list of `PedestrianObservation`.
        """
        if not pedestrians:
            return {
                "action": "MAINTAIN",
                "reason": "No pedestrians detected in current frame.",
                "critical_pedestrian_id": None,
                "critical_result": None,
                "ranking": [],
                "all_results": {},
            }

        # -- for each pedestrian: predict mental state + calculate TTC --
        all_results = {
            ped.ped_id: self._evaluate_pedestrian(ped, vehicle_speed_kmh)
            for ped in pedestrians
        }

        # -- compare all pedestrians (ascending TTC; infinite/safe last) --
        ranking = sorted(
            all_results.values(),
            key=lambda r: r["ttc"] if np.isfinite(r["ttc"]) else float("inf")
        )

        # -- select pedestrian with minimum TTC (highest risk) --
        critical_id, critical_result = self._select_critical_pedestrian(all_results)

        # -- take AV action, driven by the selected highest-risk pedestrian --
        return {
            "action": critical_result["action"],
            "reason": f"[{critical_id}] {critical_result['reason']}",
            "critical_pedestrian_id": critical_id,
            "critical_result": critical_result,
            "ranking": ranking,
            "all_results": all_results,
        }


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    def make_F(speed=5.0, vehicle_dist=0.5):
        F = np.zeros(36, dtype=np.float32)
        F[F_CURRENT_SPEED]    = speed
        F[F_VEHICLE_DISTANCE] = vehicle_dist
        return F

    # Same scenarios as before, now treated as pedestrians who are all
    # visible in the SAME frame at once, to exercise the full pipeline:
    #   detect -> per-pedestrian (features / mental state / TTC)
    #   -> compare -> select min-TTC -> take AV action
    scenarios = [
        ("Waiting - safe",       make_F(speed=0.0, vehicle_dist=0.8), 0, 0.95),
        ("Waiting - warning",    make_F(speed=0.0, vehicle_dist=0.3), 0, 0.95),
        ("Waiting - emergency",  make_F(speed=0.0, vehicle_dist=0.1), 0, 0.95),
        ("Hesitant - far",       make_F(speed=2.0, vehicle_dist=0.8), 1, 0.80),
        ("Hesitant - warning",   make_F(speed=5.0, vehicle_dist=0.25),1, 0.78),
        ("Hesitant - emergency", make_F(speed=8.0, vehicle_dist=0.05),1, 0.76),
        ("Committed - far",      make_F(speed=4.0, vehicle_dist=0.8), 2, 0.90),
        ("Committed - close",    make_F(speed=4.0, vehicle_dist=0.2), 2, 0.90),
        ("Distracted",           make_F(speed=3.0, vehicle_dist=0.3), 3, 0.72),
        ("Aggressive",           make_F(speed=8.0, vehicle_dist=0.2), 4, 0.85),
        ("Jaywalk",              make_F(speed=6.0, vehicle_dist=0.15),5, 0.70),
    ]

    pedestrians_this_frame = [
        PedestrianObservation(ped_id=name, F=F, mental_state=state, confidence=conf)
        for name, F, state, conf in scenarios
    ]

    controller = MultiPedestrianAVController()

    print("\n===================================================")
    print("MULTI-PEDESTRIAN FRAME PIPELINE — SELF TEST")
    print("(detect -> per-pedestrian state/TTC -> compare -> select min-TTC -> act)")
    print("===================================================")

    frame_decision = controller.process_frame(pedestrians_this_frame, vehicle_speed_kmh=45.0)

    print(f"\n{'Pedestrian':<20}{'State':<12}{'TTC':>10}  {'Level':<8}{'Action'}")
    print("-" * 70)
    for r in frame_decision["ranking"]:
        ttc_text = f"{r['ttc']:.2f}s" if np.isfinite(r["ttc"]) else "N/A"
        print(f"{r['pedestrian_id']:<20}{r['state_name']:<12}{ttc_text:>10}  {r['ttc_level']:<8}{r['action']}")

    print("\n---------------------------------------------------")
    print(f"CRITICAL PEDESTRIAN : {frame_decision['critical_pedestrian_id']}")
    print(f"FINAL AV ACTION     : {frame_decision['action']}")
    print(f"REASON              : {frame_decision['reason']}")
    print("---------------------------------------------------\n")