PP1 PROFESSIONAL V2V DEMO - USAGE GUIDE
=============================================

OVERVIEW
--------
The PP1 Professional V2V Demo implements a multi-vehicle autonomous vehicle negotiation system
at unsignalized intersections using LSTM-based intent prediction and SUMO simulation.

KEY FEATURES
------------
- LSTM-based vehicle intent prediction (NUMPY_EXACT_LSTM)
- Three-stage decision workflow: OUTSIDE_CONTEXT → THRESHOLD_MONITORING → DECISION_FINAL
- Real-time local awareness table with conflict detection
- JSON summary output for research analysis
- Optional CSV logging for detailed step-by-step data

HOW TO RUN SCENARIO 2
-------------------------

Basic Command (JSON summary only):
python scripts/run_pp1_professional_v2v_demo.py --scenario 2 --keep-open-seconds 30

Optional CSV Command:
python scripts/run_pp1_professional_v2v_demo.py --scenario 2 --keep-open-seconds 30 --save-csv

COMMAND LINE ARGUMENTS
----------------------
--scenario [1|2]     : Scenario to run (1=Safe GO, 2=Conflict YIELD/WAIT)
--keep-open-seconds N : Keep SUMO GUI open for N seconds after simulation completes
--save-csv          : Save CSV log file (default: JSON only)
--nogui              : Run without GUI
--validate-only       : Only validate config files without running simulation
--center-x X         : Center X coordinate for camera
--center-y Y         : Center Y coordinate for camera
--allow-identity-scaler : Allow identity scaler fallback
--allow-default-labels : Allow default label classes fallback
--max-steps N        : Maximum simulation steps

JSON OUTPUT EXPLANATION
---------------------

JSON Summary File: outputs/pp1_demo_logs/pp1_summary_<scenario>_<timestamp>.json

Key Sections:
1. simulation_summary
   - scenario: SCENARIO_1 or SCENARIO_2
   - total_simulation_time: Total simulation duration in seconds
   - total_unique_vehicles: Number of unique vehicles processed
   - total_predictions_made: LSTM model prediction count
   - csv_log_path: Path to CSV file (if saved)

2. zone_counts
   - OUTSIDE: Vehicles collecting trajectory context
   - THRESHOLD: Vehicles in awareness collection stage
   - DECISION: Vehicles in final decision stage

3. threshold_monitoring_summary
   - threshold_rows_collected: Number of threshold monitoring events
   - neutral_monitoring_rows: Awareness collection events
   - final_decisions_made_here: Always 0 (no final decisions in threshold stage)

4. decision_stage_summary
   - final_decision_events: Total final decision count
   - GO count: Vehicles proceeding through intersection
   - YIELD count: Vehicles yielding to others
   - WAIT count: Vehicles waiting for clearance

5. final_decision_snapshot
   - critical_time: Timestamp of key decision moment
   - vehicles: Detailed vehicle data including stage, zone, conflicts, model decisions

6. model_prediction_distribution
   - BUFFERING: LSTM model building sequence
   - GO: Model predicts proceed
   - NEUTRAL: Model predicts wait/monitor
   - YIELD: Model predicts yield

7. per_vehicle_action_counts
   - GO: Vehicle proceeds actions
   - YIELD: Vehicle yielding actions
   - WAIT: Vehicle waiting actions
   - MAINTAIN_30KMH: Threshold monitoring speed

8. runtime_note
   - tensorflow_used: false (not used)
   - tflite_used: false (not used)
   - mock_model_used: false (not used)
   - runtime_mode: NUMPY_EXACT_LSTM
   - scaler_fallback: false (using trained scaler)
   - label_encoder_fallback: false (using trained encoder)

STAGE EXPLANATIONS
------------------

THRESHOLD MONITORING STAGE:
- Purpose: Awareness collection and neutral monitoring
- Vehicle Behavior: Maintain 30 km/h (8.33 m/s)
- Model Decision: Always NEUTRAL (no final decisions)
- Applied Action: MAINTAIN_30KMH
- Reason: threshold_awareness_collection
- Final Decisions: 0 (no final decisions made here)

DECISION FINAL STAGE:
- Purpose: Final intersection negotiation decisions
- Vehicle Behavior: Based on LSTM model prediction and conflict analysis
- Model Decision: GO/NEUTRAL/YIELD from LSTM
- Model-to-Action Mapping:
  * GO → GO (proceed through intersection)
  * YIELD → YIELD (yield to other vehicles)
  * NEUTRAL → WAIT (wait for clearance)
- Applied Action: Final decision sent to SUMO
- Reason: decision_final_go, decision_final_yield, decision_final_wait

RUNTIME NOTE
-----------
The demo uses NUMPY_EXACT_LSTM runtime mode:
- No TensorFlow dependency
- No TFLite optimization
- No mock model fallback
- Uses exact NumPy implementation of trained LSTM weights
- Preserves original model architecture and weights

FILE STRUCTURE
-------------
Important Files:
- scripts/run_pp1_professional_v2v_demo.py: Main demo script
- scripts/observed_behavior_numpy_predictor.py: LSTM predictor
- configs/pp1_scenario_2_fixed.sumocfg: Scenario configuration
- configs/pp1_scenario_2_fixed.rou.xml: Vehicle routes
- configs/unsignalized_intersection.net.xml: Road network
- models/observed_behavior/v2v_lstm_observed_behavior_weights.npz: LSTM weights
- models/observed_behavior/feature_scaler_observed_behavior.pkl: Feature scaler
- models/observed_behavior/label_encoder_observed_behavior.pkl: Label encoder

Output Files:
- outputs/pp1_demo_logs/pp1_summary_<scenario>_<timestamp>.json: Summary data
- outputs/pp1_demo_logs/pp1_observed_behavior_demo_<scenario>_<timestamp>.csv: Detailed logs (optional)

TROUBLESHOOTING
---------------
1. If vehicles don't appear: Check route file and departure times
2. If simulation stops early: Check network file validity
3. If model predictions are BUFFERING: Allow more simulation steps
4. If JSON file not created: Check outputs folder permissions

RESEARCH NOTES
------------
- Threshold stage provides situational awareness without final decisions
- Decision stage implements LSTM-assisted right-of-way negotiation
- Applied actions align with SUMO vehicle control system
- Model confidence scores indicate prediction reliability
- Local awareness table shows real-time conflict detection

For detailed analysis, use the JSON summary file which contains all simulation metrics
and the critical decision snapshot with complete vehicle state information.
