"""
PP1 Professional Multi-Vehicle V2V Decision Demo
Shows multiple vehicles making decisions using LSTM model, local awareness, and V2V communication.
"""

import os
import sys
import argparse
import time
import csv
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traci
from observed_behavior_numpy_predictor import load_observed_behavior_numpy_predictor
from local_awareness import create_local_awareness
from v2v_action_decision import create_v2v_action_decision


class PP1ProfessionalV2VDemo:
    """Professional multi-vehicle V2V decision demo."""
    
    # RGBA color definitions
    COLORS = {
        'GO': (0, 200, 0, 255),
        'YIELD': (255, 165, 0, 255),
        'WAIT': (0, 100, 255, 255),
        'RISK': (255, 0, 0, 255),
        'UNKNOWN': (160, 160, 160, 255)
    }
    
    def safe_float(self, value, default=0.0):
        """Safely convert value to float with default."""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def safe_text(self, value, default="-"):
        """Safely convert value to text with default."""
        try:
            if value is None:
                return default
            return str(value)
        except (ValueError, TypeError):
            return default
    
    def __init__(self, scenario: int = 1, validate_only: bool = False, nogui: bool = False, 
                 keep_open_seconds: int = 10, center_x: float = 0, center_y: float = 0,
                 allow_identity_scaler: bool = False, allow_default_labels: bool = False, max_steps: int = 600, save_csv: bool = False):
        """
        Initialize professional PP1 demo with NumPy-only LSTM predictor.
        
        Args:
            scenario: Scenario number (1 or 2)
            validate_only: Only validate config files without running simulation
            nogui: Run without GUI
            keep_open_seconds: Keep SUMO GUI open for N seconds after simulation completes
            center_x: Center X coordinate for camera
            center_y: Center Y coordinate for camera
            allow_identity_scaler: Allow identity scaler fallback
            allow_default_labels: Allow default label classes fallback
            max_steps: Maximum simulation steps
            save_csv: Save CSV log file (default: False, JSON only)
        """
        self.scenario = scenario
        self.scenario_name = f"SCENARIO_{scenario}"
        self.validate_only = validate_only
        self.nogui = nogui
        self.keep_open_seconds = keep_open_seconds
        self.center_x = center_x
        self.center_y = center_y
        self.allow_identity_scaler = allow_identity_scaler
        self.allow_default_labels = allow_default_labels
        self.max_steps = max_steps
        self.save_csv = save_csv
        
        # Initialize all attributes first
        self.predictor = None
        self.awareness = None
        self.decision_maker = None
        self.sumo_binary = "sumo" if nogui else "sumo-gui"
        self.runtime_mode = "NUMPY_EXACT_LSTM"
        
        # Statistics tracking
        self.stats = {
            'total_vehicles_processed': 0,
            'lstm_predictions': 0,
            'buffering_rows': 0,
            'total_steps': 0,
            'action_distribution': defaultdict(int),
            'model_prediction_distribution': defaultdict(int),
            'zone_distribution': defaultdict(int),
            'collision_events': 0,
            'per_vehicle_actions': defaultdict(lambda: defaultdict(int)),
            'start_time': None,
            'end_time': None
        }
        
        # Snapshot storage for critical time steps
        self.critical_snapshots = []
        
        self.csv_data = []
        self.csv_file_path = None
        self.vehicle_actions = {}
        self.last_awareness_table_time = -1
        
        # Fairness-time tracking
        self.fairness_tracking = {
            'per_vehicle': defaultdict(lambda: {
                'waiting_time': 0.0,
                'decision_zone_entry_time': None,
                'first_decision_time': None,
                'decision_delay': 0.0,
                'GO': 0,
                'WAIT': 0,
                'YIELD': 0,
                'MAINTAIN_30KMH': 0,
                'starvation_risk': False
            }),
            'step_length': 0.1  # SUMO simulation step length in seconds
        }
        
        # Print startup information
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"[PP1] Project root: {project_root}")
        print(f"[PP1] Scenario: {self.scenario_name}")
        
        # Validate configuration files first
        if validate_only:
            self._validate_config()
            print("[PP1] Validation complete. Exiting without starting simulation.")
            sys.exit(0)
        
        # Initialize NumPy-only LSTM predictor
        self._initialize_numpy_predictor()
        
        # Initialize components
        self.awareness = create_local_awareness()
        self.decision_maker = create_v2v_action_decision()
    
    def _initialize_numpy_predictor(self):
        """Initialize NumPy-only LSTM predictor with exact trained weights."""
        try:
            print(f"[PP1] Loading NumPy-only LSTM predictor...")
            self.predictor = load_observed_behavior_numpy_predictor(
                allow_identity_scaler=self.allow_identity_scaler,
                allow_default_labels=self.allow_default_labels
            )
            print(f"[PP1] Model runtime: {self.runtime_mode}")
            print(f"[PP1] Loaded exact trained LSTM weights from .npz")
            print(f"[PP1] TensorFlow not used")
            print(f"[PP1] TFLite not used")
            print(f"[PP1] Mock model not used")
            print(f"[PP1] ✓ Loaded NumPy-only observed behavior predictor")
            
        except Exception as e:
            print(f"[PP1] ✗ Failed to load NumPy predictor: {e}")
            sys.exit(1)
    
    def _validate_config(self):
        """Validate configuration files with comprehensive diagnostics."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Determine config files
        sumocfg_file = os.path.join(project_root, "configs", f"pp1_scenario_{self.scenario}_fixed.sumocfg")
        route_file = os.path.join(project_root, "configs", f"pp1_scenario_{self.scenario}_fixed.rou.xml")
        net_file = os.path.join(project_root, "configs", "unsignalized_intersection.net.xml")
        
        # Check if files exist
        missing_files = []
        if not os.path.exists(sumocfg_file):
            missing_files.append(f"✗ SUMO config file: {sumocfg_file}")
        if not os.path.exists(route_file):
            missing_files.append(f"✗ Route file: {route_file}")
        if not os.path.exists(net_file):
            missing_files.append(f"✗ Network file: {net_file}")
        
        if missing_files:
            print("\n" + "="*80)
            print("PP1 CONFIGURATION VALIDATION FAILED")
            print("="*80)
            for file in missing_files:
                print(f"  ❌ {file}")
            print("\n" + "="*80)
            print("Please check that all required files exist.")
            print("="*80)
            return
        
        # Analyze route file
        vehicle_count, route_edges = self._analyze_route_file(route_file)
        network_edges = self._get_network_edge_ids(net_file)
        
        # Print validation results
        print("\n" + "="*80)
        print("PP1 CONFIGURATION VALIDATION PASSED")
        print("="*80)
        print(f"Project root: {project_root}")
        print(f"Scenario: {self.scenario_name}")
        print(f"SUMO config: {sumocfg_file}")
        print(f"Network file: {net_file}")
        print(f"Route file: {route_file}")
        print(f"Files exist: ✓ All files found")
        print(f"Vehicles in route file: {vehicle_count}")
        print(f"First few vehicle IDs: {self._get_vehicle_ids(route_file)[:3]}")
        print(f"First few network edges: {network_edges[:5]}")
        print(f"Route edges used: {route_edges}")
        print("="*80)
        
        # Test SUMO config
        try:
            import subprocess
            result = subprocess.run(['sumo', '-c', sumocfg_file, '--no-step-log', 'true'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"[PP1] ⚠ WARNING: SUMO config test failed:")
                print(f"[PP1] Error output: {result.stderr}")
            else:
                print("[PP1] ✓ SUMO configuration test passed")
        except Exception as e:
            print(f"[PP1] ⚠ Could not test SUMO config: {e}")
    
    def _analyze_route_file(self, route_file: str) -> tuple:
        """Analyze route file and return vehicle count and edge list."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(route_file)
            root = tree.getroot()
            
            vehicles = root.findall('vehicle')
            vehicle_count = len(vehicles)
            
            route_edges = set()
            for vehicle in vehicles:
                route = vehicle.find('route')
                if route is not None:
                    edges = route.get('edges', '')
                    route_edges.update(edges.split())
            
            return vehicle_count, list(route_edges)
        except Exception as e:
            print(f"[PP1] ⚠ Error analyzing route file: {e}")
            return 0, []
    
    def _get_vehicle_ids(self, route_file: str) -> list:
        """Get vehicle IDs from route file."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(route_file)
            root = tree.getroot()
            
            vehicles = root.findall('vehicle')
            return [v.get('id') for v in vehicles[:5]]
        except Exception:
            return []
    
    def _get_network_edge_ids(self, net_file: str) -> list:
        """Extract edge IDs from network file."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(net_file)
            root = tree.getroot()
            
            edges = root.findall('edge')
            edge_ids = [edge.get('id') for edge in edges]
            return edge_ids
        except Exception as e:
            print(f"[PP1] ⚠ Error parsing network file: {e}")
            return []
    
    def setup_csv_logging(self):
        """Setup CSV logging for demo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "outputs/pp1_demo_logs"
        os.makedirs(output_dir, exist_ok=True)
        
        self.csv_file_path = os.path.join(output_dir, f"pp1_observed_behavior_demo_{self.scenario}_{timestamp}.csv")
        self.json_file_path = os.path.join(output_dir, f"pp1_summary_{self.scenario}_{timestamp}.json")
        
        # CSV headers
        self.csv_headers = [
            'time', 'scenario', 'vehicle_id', 'stage', 'zone', 'nearest_vehicle_id',
            'conflict_vehicle_ids', 'merge_conflict', 'crossing_conflict', 'right_side_vehicle_present',
            'min_eta_gap', 'model_decision', 'model_confidence', 'final_decision',
            'applied_action', 'decision_reason', 'runtime_mode', 'collision_count'
        ]
        
        if self.save_csv:
            print(f"[PP1] CSV logging enabled: {self.csv_file_path}")
        else:
            print(f"[PP1] CSV logging disabled (use --save-csv to enable)")
        print(f"[PP1] JSON summary path: {self.json_file_path}")
    
    def log_to_csv(self, row_data):
        """Log data to CSV file."""
        if self.csv_file_path:
            self.csv_data.append(row_data)
    
    def write_csv_file(self):
        """Write accumulated CSV data to file."""
        if self.csv_file_path and self.csv_data:
            with open(self.csv_file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
                writer.writerows(self.csv_data)
            print(f"[PP1] CSV log written: {len(self.csv_data)} records")
    
    def write_json_summary(self):
        """Write JSON summary file with comprehensive simulation data."""
        import json
        
        if not self.json_file_path:
            return
        
        # 1. Simulation summary
        simulation_summary = {
            "scenario": self.scenario_name,
            "total_simulation_time": getattr(self, 'last_sim_time', 0.0),
            "total_steps_processed": self.stats['total_steps'],
            "total_unique_vehicles": len(self.stats.get('unique_vehicles', set())),
            "total_vehicles_processed": self.stats['total_steps'],
            "total_predictions_made": self.stats['lstm_predictions'],
            "total_buffering_rows": self.stats['buffering_rows'],
            "total_collisions": self.stats['collision_events'],
            "csv_log_path": self.csv_file_path
        }
        
        # 2. Zone counts
        zone_counts = {}
        for zone, count in self.stats['zone_distribution'].items():
            zone_counts[zone] = count
        
        # 3. Threshold monitoring summary
        threshold_rows = self.stats.get('threshold_monitoring_rows', 0)
        threshold_monitoring_summary = {
            "threshold_rows_collected": threshold_rows,
            "neutral_monitoring_rows": threshold_rows,
            "local_awareness_rows_collected": threshold_rows,
            "final_decisions_made_here": 0
        }
        
        # 4. Decision stage summary
        final_decisions = sum(self.stats['action_distribution'].values())
        decision_stage_summary = {
            "final_decision_events": final_decisions,
            "GO count": self.stats['action_distribution'].get('GO', 0),
            "YIELD count": self.stats['action_distribution'].get('YIELD', 0),
            "WAIT count": self.stats['action_distribution'].get('WAIT', 0)
        }
        
        # 5. Final decision snapshot
        final_decision_snapshot = {
            "critical_time": 0.0,
            "vehicles": []
        }
        
        if self.critical_snapshots:
            best_snapshot = None
            for snapshot in self.critical_snapshots:
                has_decision_final = any(
                    data.get('stage') == 'DECISION_FINAL' 
                    for data in snapshot['vehicles'].values()
                )
                if has_decision_final:
                    best_snapshot = snapshot
                    break
            
            if not best_snapshot:
                best_snapshot = self.critical_snapshots[0]
            
            final_decision_snapshot["critical_time"] = best_snapshot['time']
            
            # Sort vehicles by ID
            for vehicle_id in sorted(best_snapshot['vehicles'].keys()):
                data = best_snapshot['vehicles'][vehicle_id]
                vehicle_data = {
                    "vehicle_id": vehicle_id,
                    "stage": data.get('stage', 'UNKNOWN'),
                    "zone": data.get('zone', 'UNKNOWN'),
                    "nearest_vehicle_id": data.get('nearest_vehicle_id', None),
                    "conflict_vehicle_ids": data.get('conflict_vehicle_ids', '[]'),
                    "merge_conflict": data.get('merge_conflict', 0),
                    "crossing_conflict": data.get('crossing_conflict', 0),
                    "right_side_vehicle_present": data.get('right_side_vehicle_present', 0),
                    "min_eta_gap": data.get('min_eta_gap', 0.0),
                    "model_decision": data.get('model_decision', 'UNKNOWN'),
                    "model_confidence": data.get('model_confidence', 0.0),
                    "final_decision": data.get('final_decision', 'UNKNOWN'),
                    "applied_action": data.get('applied_action', 'UNKNOWN'),
                    "decision_reason": data.get('decision_reason', 'unknown')
                }
                final_decision_snapshot["vehicles"].append(vehicle_data)
        
        # 6. Model prediction distribution
        model_prediction_distribution = {}
        for label, count in self.stats['model_prediction_distribution'].items():
            model_prediction_distribution[label] = count
        
        # 7. Per-vehicle action counts
        per_vehicle_action_counts = {}
        for vehicle_id, actions in self.stats['per_vehicle_actions'].items():
            per_vehicle_action_counts[vehicle_id] = dict(actions)
        
        # 8. Fairness-time summary
        fairness_time_summary = {
            "average_waiting_time": 0.0,
            "maximum_waiting_time": 0.0,
            "vehicle_with_max_waiting": None,
            "overall_starvation_risk": False,
            "per_vehicle": {}
        }
        
        total_waiting_time = 0.0
        max_waiting_time = 0.0
        vehicle_with_max_waiting = None
        overall_starvation_risk = False
        vehicle_count = 0
        
        # Calculate fairness metrics for JSON
        for vehicle_id in sorted(self.fairness_tracking['per_vehicle'].keys()):
            vehicle_fairness = self.fairness_tracking['per_vehicle'][vehicle_id]
            waiting_time = vehicle_fairness['waiting_time']
            decision_delay = vehicle_fairness['decision_delay']
            
            # Only include vehicles that actually participated in DECISION_FINAL
            if waiting_time > 0 or vehicle_fairness['GO'] > 0 or vehicle_fairness['WAIT'] > 0 or vehicle_fairness['YIELD'] > 0:
                total_waiting_time += waiting_time
                vehicle_count += 1
                
                if waiting_time > max_waiting_time:
                    max_waiting_time = waiting_time
                    vehicle_with_max_waiting = vehicle_id
                
                if vehicle_fairness['starvation_risk']:
                    overall_starvation_risk = True
            
            # Add per-vehicle data to JSON
            fairness_time_summary["per_vehicle"][vehicle_id] = {
                "waiting_time": round(waiting_time, 1),
                "decision_delay": round(decision_delay, 1),
                "GO": vehicle_fairness['GO'],
                "WAIT": vehicle_fairness['WAIT'],
                "YIELD": vehicle_fairness['YIELD'],
                "MAINTAIN_30KMH": vehicle_fairness['MAINTAIN_30KMH'],
                "starvation_risk": vehicle_fairness['starvation_risk']
            }
        
        # Calculate summary statistics
        fairness_time_summary["average_waiting_time"] = round(total_waiting_time / vehicle_count, 1) if vehicle_count > 0 else 0.0
        fairness_time_summary["maximum_waiting_time"] = round(max_waiting_time, 1)
        fairness_time_summary["vehicle_with_max_waiting"] = vehicle_with_max_waiting
        fairness_time_summary["overall_starvation_risk"] = overall_starvation_risk
        
        # 9. Runtime note
        runtime_note = {
            "tensorflow_used": False,
            "tflite_used": False,
            "mock_model_used": False,
            "runtime_mode": self.runtime_mode,
            "scaler_fallback": False,
            "label_encoder_fallback": False
        }
        
        # Combine all sections
        json_data = {
            "simulation_summary": simulation_summary,
            "zone_counts": zone_counts,
            "threshold_monitoring_summary": threshold_monitoring_summary,
            "decision_stage_summary": decision_stage_summary,
            "final_decision_snapshot": final_decision_snapshot,
            "model_prediction_distribution": model_prediction_distribution,
            "per_vehicle_action_counts": per_vehicle_action_counts,
            "fairness_time_summary": fairness_time_summary,
            "runtime_note": runtime_note
        }
        
        # Write JSON file
        try:
            with open(self.json_file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=2)
            print(f"[PP1] JSON summary written: {self.json_file_path}")
        except Exception as e:
            print(f"[PP1] Error writing JSON summary: {e}")
    
    def _determine_stage_and_action(self, zone: str, model_label: str, awareness: dict, ready: bool) -> tuple:
        """
        Determine stage and action based on zone, model prediction, and research logic.
        
        Args:
            zone: Vehicle zone (OUTSIDE, THRESHOLD, DECISION)
            model_label: LSTM model prediction
            awareness: Local awareness data
            ready: Whether model is ready
            
        Returns:
            tuple: (stage, model_decision, final_decision, applied_action, reason)
        """
        conflict_count = self.safe_float(awareness.get('conflict_count', 0))
        min_eta_gap = self.safe_float(awareness.get('min_eta_gap', 0))
        right_side_vehicle_present = self.safe_float(awareness.get('right_side_vehicle_present', 0))
        
        # Handle model not ready
        if not ready:
            return 'OUTSIDE_CONTEXT', 'NEUTRAL', 'WAIT', 'WAIT', 'model_not_ready'
        
        # Zone-based decision logic
        if zone == 'DECISION':
            # DECISION_FINAL stage
            stage = 'DECISION_FINAL'
            model_decision = model_label
            
            # Map model prediction to final action
            if model_label == 'GO':
                final_decision = 'GO'
                applied_action = 'GO'
                reason = 'decision_final_go'
            elif model_label == 'YIELD':
                final_decision = 'YIELD'
                applied_action = 'YIELD'
                reason = 'decision_final_yield'
            else:  # NEUTRAL
                final_decision = 'WAIT'
                applied_action = 'WAIT'
                reason = 'decision_final_wait'
                
        elif zone == 'THRESHOLD':
            # THRESHOLD_MONITORING stage - neutral monitoring only
            stage = 'THRESHOLD_MONITORING'
            model_decision = 'NEUTRAL'
            final_decision = 'NEUTRAL'
            applied_action = 'MAINTAIN_30KMH'
            reason = 'threshold_awareness_collection'
            
        else:  # OUTSIDE zone
            # OUTSIDE_CONTEXT stage - collect trajectory context only
            stage = 'OUTSIDE_CONTEXT'
            model_decision = 'NEUTRAL'
            final_decision = 'NEUTRAL'
            applied_action = 'MAINTAIN_30KMH'
            reason = 'outside_context'
        
        return stage, model_decision, final_decision, applied_action, reason
    
    def apply_vehicle_action(self, vehicle_id: str, action: str, acceleration: float):
        """
        Apply action to vehicle with proper speed control and wait timeout.
        
        Args:
            vehicle_id: Vehicle identifier
            action: Final action (GO/YIELD/WAIT/RISK)
            acceleration: Acceleration value
        """
        try:
            # Check if vehicle still exists
            if vehicle_id not in traci.vehicle.getIDList():
                return
            
            # Set vehicle color using RGBA tuple
            color = self.COLORS.get(action, self.COLORS['UNKNOWN'])
            try:
                traci.vehicle.setColor(vehicle_id, color)
            except Exception as e:
                print(f"[PP1] ⚠ Error setting color for {vehicle_id}: {e}")
            
            # Get waiting time for timeout logic
            waiting_time = getattr(self, f'_waiting_time_{vehicle_id}', 0)
            last_action = getattr(self, f'_last_action_{vehicle_id}', None)
            
            # Update waiting time
            if action in ['WAIT', 'YIELD']:
                if last_action in ['WAIT', 'YIELD']:
                    waiting_time += 0.1
                else:
                    waiting_time = 0.1
            else:
                waiting_time = 0
            
            # Store waiting time and last action
            setattr(self, f'_waiting_time_{vehicle_id}', waiting_time)
            setattr(self, f'_last_action_{vehicle_id}', action)
            
            # Apply speed control with timeout
            if action == "GO":
                target_speed = 5.0
                traci.vehicle.setSpeed(vehicle_id, target_speed)
                
            elif action == "YIELD":
                if waiting_time > 5.0:
                    # Creep after 5 seconds of yielding
                    target_speed = 1.5
                    traci.vehicle.setSpeed(vehicle_id, target_speed)
                    print(f"[PP1] {vehicle_id} creeping after yield timeout")
                else:
                    target_speed = 2.5
                    traci.vehicle.setSpeed(vehicle_id, target_speed)
                    
            elif action == "WAIT":
                if waiting_time > 5.0:
                    # Creep after 5 seconds of waiting
                    target_speed = 1.5
                    traci.vehicle.setSpeed(vehicle_id, target_speed)
                    print(f"[PP1] {vehicle_id} creeping after wait timeout")
                else:
                    target_speed = 1.0
                    traci.vehicle.setSpeed(vehicle_id, target_speed)
                    
            elif action == "MAINTAIN_30KMH":
                # Maintain 30 km/h = 8.33 m/s for threshold monitoring
                target_speed = 8.33
                traci.vehicle.setSpeed(vehicle_id, target_speed)
                
            elif action == "RISK":
                target_speed = 1.0
                traci.vehicle.setSpeed(vehicle_id, target_speed)
            else:
                target_speed = traci.vehicle.getSpeed(vehicle_id)
                traci.vehicle.setSpeed(vehicle_id, target_speed)
            
            # Update statistics
            self.vehicle_actions[vehicle_id] = action
            self.stats['per_vehicle_actions'][vehicle_id][action] += 1
                
        except Exception as e:
            print(f"[PP1] ⚠ Error applying action to {vehicle_id}: {e}")
    
    def make_zone_based_decision(self, vehicle_id: str, model_label: str, confidence: float, awareness: dict) -> tuple:
        """
        Make zone-based decision with proper logic.
        
        Returns:
            tuple: (final_action, reason)
        """
        zone = awareness.get('ego_zone', 'OUTSIDE')
        conflict_count = awareness.get('conflict_count', 0)
        min_eta_gap = awareness.get('min_eta_gap', 100.0)
        right_side_vehicle_present = awareness.get('right_side_vehicle_present', 0)
        
        if zone == 'OUTSIDE':
            return 'WAIT', 'outside_decision_zone'
        
        elif zone == 'THRESHOLD':
            # Monitoring stage - mostly WAIT unless high risk
            if conflict_count > 0 and min_eta_gap <= 1.0:
                return 'YIELD', 'threshold_high_risk_conflict'
            else:
                return 'WAIT', 'threshold_monitoring'
        
        elif zone == 'DECISION':
            # Full decision logic
            if conflict_count > 0 and min_eta_gap <= 1.0:
                return 'YIELD', 'safety_override_close_conflict'
            elif right_side_vehicle_present == 1:
                return 'WAIT', 'safety_override_right_side_vehicle'
            elif model_label == 'GO':
                return 'GO', 'model_go_no_high_risk'
            elif model_label == 'YIELD':
                return 'YIELD', 'model_yield'
            else:
                return 'WAIT', 'model_neutral_wait'
        
        return 'WAIT', 'unknown_zone_logic'
    
    def print_awareness_table(self, sim_time: float, all_vehicle_data: list):
        """Print local awareness table every 1 second."""
        if int(sim_time) <= self.last_awareness_table_time:
            return
        
        self.last_awareness_table_time = int(sim_time)
        
        print(f"\nLOCAL AWARENESS TABLE at t={sim_time:04.1f}s")
        print("-" * 140)
        print(f"{'Vehicle':<12} | {'Stage':<20} | {'Zone':<9} | {'Nearest':<12} | {'Conflict Vehicles':<18} | {'Merge':<6} | {'Crossing':<9} | {'Right-side':<10} | {'ETA Gap':<8} | {'Model Decision':<15} | {'Final Decision':<15} | {'Applied Action':<15} | {'Reason'}")
        print("-" * 140)
        
        for data in all_vehicle_data:
            vehicle_id = data['vehicle_id']
            stage = data.get('stage', 'UNKNOWN')
            zone = data['zone']
            nearest = data.get('nearest_vehicle_id', 'None')
            conflict_vehicles = data.get('conflict_vehicle_ids', '[]')
            merge_conflict = data.get('merge_conflict', 0)
            crossing_conflict = data.get('crossing_conflict', 0)
            right_side = data.get('right_side_vehicle_present', 0)
            eta_gap = f"{data.get('min_eta_gap', 0.0):.1f}"
            model_decision = data.get('model_decision', 'UNKNOWN')
            final_decision = data.get('final_decision', 'UNKNOWN')
            applied_action = data.get('applied_action', 'UNKNOWN')
            reason = data.get('decision_reason', 'unknown')
            
            print(f"{vehicle_id:<12} | {stage:<20} | {zone:<9} | {nearest:<12} | {conflict_vehicles:<18} | {merge_conflict:<6} | {crossing_conflict:<9} | {right_side:<10} | {eta_gap:<8} | {model_decision:<15} | {final_decision:<15} | {applied_action:<15} | {reason}")
        print()
    
    def print_local_awareness_table(self, sim_time: float, vehicle_data_list: list):
        """Print local awareness table for all vehicles."""
        if not vehicle_data_list:
            return
        
        print(f"LOCAL AWARENESS TABLE at t={sim_time:.1f}s")
        print("-" * 110)
        print(f"{'vehicle_id':<12} | {'zone':<9} | {'buffer_len':<10} | {'nearest':<12} | {'speed':<6} | {'dist':<6} | {'eta':<6} | {'nearby':<7} | {'eta_gap':<9} | {'conflict':<9} | {'right_side':<11} | {'model':<16} | {'action':<7} | {'reason'}")
        print("-" * 110)
        
        for data in vehicle_data_list:
            # Use safe_float and safe_text to prevent None formatting errors
            vehicle_id = self.safe_text(data.get('vehicle_id'))
            zone = self.safe_text(data.get('zone'))
            buffer_len = self.safe_float(data.get('buffer_len'))
            nearest = self.safe_text(data.get('nearest_vehicle_id'))
            speed = self.safe_float(data.get('ego_speed'))
            dist = self.safe_float(data.get('ego_distance_to_intersection'))
            eta = self.safe_float(data.get('ego_eta'))
            nearby = self.safe_float(data.get('context_vehicle_count'))
            eta_gap = self.safe_float(data.get('min_eta_gap'))
            conflict = self.safe_float(data.get('conflict_count'))
            right_side = self.safe_float(data.get('right_side_vehicle_present'))
            action = self.safe_text(data.get('applied_action'))
            reason = self.safe_text(data.get('decision_reason'))
            
            # Create clean model display
            model_label = self.safe_text(data.get('model_prediction'))
            model_confidence = self.safe_float(data.get('model_confidence'))
            
            if model_label == "BUFFERING":
                model_display = "BUFFERING(0.00)"
            elif model_label == "UNKNOWN":
                model_display = "UNKNOWN(0.00)"
            else:
                model_display = f"{model_label}({model_confidence:.2f})"
            
            # Ensure single-line display
            model_display = str(model_display).replace("\n", "").strip()
            
            print(f"{vehicle_id:<12} | {zone:<9} | {buffer_len:<10} | {nearest:<12} | {speed:<6.1f} | {dist:<6.1f} | {eta:<6.1f} | {nearby:<7} | {eta_gap:<9.2f} | {conflict:<9} | {right_side:<11} | {model_display[:16]:<16} | {action:<7} | {reason}")
        
        print("-" * 110)
        print()
    
    def process_vehicle(self, vehicle_id: str, sim_time: float, all_vehicle_ids: list) -> dict:
        """
        Process a single vehicle through the prediction pipeline.
        
        Returns:
            dict: Vehicle data for awareness table
        """
        try:
            # Get basic vehicle state
            vehicle_state = self.awareness.get_vehicle_state(vehicle_id)
            
            # Build local awareness
            awareness = self.awareness.build_local_awareness(vehicle_id, all_vehicle_ids)
            zone = awareness.get('ego_zone', 'OUTSIDE')
            
            # Update model sequence buffer for ALL active vehicles every step
            model_label = 'UNKNOWN'
            confidence = 0.0
            probabilities = {'GO': 0.0, 'NEUTRAL': 0.0, 'YIELD': 0.0}
            buffer_len = 0
            ready = False
            
            # Always update sequence buffer and get prediction
            try:
                prediction = self.predictor.predict(vehicle_id, vehicle_state, awareness)
                model_label = prediction['label']
                confidence = prediction['confidence']
                probabilities = prediction['probabilities']
                ready = prediction['ready']
                buffer_len = self.predictor.get_sequence_length(vehicle_id)
                
                # Update statistics
                self.stats['lstm_predictions'] += 1
                if not ready:
                    self.stats['buffering_rows'] += 1
                self.stats['model_prediction_distribution'][model_label] += 1
                
            except Exception as e:
                print(f"[PP1] ⚠ Prediction failed for {vehicle_id}: {e}")
                buffer_len = self.predictor.get_sequence_length(vehicle_id) if hasattr(self.predictor, 'get_sequence_length') else 0
            
            # Determine zone
            zone = awareness.get('ego_zone', 'OUTSIDE')
            self.stats['zone_distribution'][zone] += 1
            
            # Determine stage and action using new workflow
            stage, model_decision, final_decision, applied_action, reason = self._determine_stage_and_action(zone, model_label, awareness, ready)
            
            # Update statistics based on stage
            if stage == 'DECISION_FINAL':
                self.stats['action_distribution'][applied_action] += 1
                self.stats['per_vehicle_actions'][vehicle_id][applied_action] += 1
                
                # Track fairness metrics for DECISION_FINAL stage
                vehicle_fairness = self.fairness_tracking['per_vehicle'][vehicle_id]
                
                # Track decision zone entry time
                if vehicle_fairness['decision_zone_entry_time'] is None:
                    vehicle_fairness['decision_zone_entry_time'] = sim_time
                
                # Track first decision time
                if vehicle_fairness['first_decision_time'] is None:
                    vehicle_fairness['first_decision_time'] = sim_time
                    vehicle_fairness['decision_delay'] = sim_time - vehicle_fairness['decision_zone_entry_time']
                
                # Count actions and track waiting time (WAIT and YIELD in DECISION_FINAL only)
                vehicle_fairness[applied_action] += 1
                if applied_action in ['WAIT', 'YIELD']:
                    vehicle_fairness['waiting_time'] += self.fairness_tracking['step_length']
                
                # Check for starvation risk (> 8 seconds total waiting)
                if vehicle_fairness['waiting_time'] > 8.0:
                    vehicle_fairness['starvation_risk'] = True
                    
            elif stage == 'THRESHOLD_MONITORING':
                self.stats['threshold_monitoring_rows'] = self.stats.get('threshold_monitoring_rows', 0) + 1
                # MAINTAIN_30KMH in THRESHOLD_MONITORING is not unfair waiting
                self.fairness_tracking['per_vehicle'][vehicle_id]['MAINTAIN_30KMH'] += 1
            # OUTSIDE_CONTEXT doesn't count as decision
            
            # Apply vehicle action (color and speed)
            self.apply_vehicle_action(vehicle_id, applied_action, -2.0)
            
            # Prepare vehicle data for CSV and table
            vehicle_data = {
                'vehicle_id': vehicle_id,
                'stage': stage,
                'zone': zone,
                'nearest_vehicle_id': awareness.get('nearest_vehicle_id', None),
                'conflict_vehicle_ids': str(awareness.get('conflict_vehicle_ids', [])),
                'merge_conflict': awareness.get('merge_conflict', 0),
                'crossing_conflict': awareness.get('crossing_conflict', 0),
                'right_side_vehicle_present': awareness.get('right_side_vehicle_present', 0),
                'min_eta_gap': awareness.get('min_eta_gap', 0.0),
                'model_decision': model_decision,
                'model_confidence': confidence,
                'final_decision': final_decision,
                'applied_action': applied_action,
                'decision_reason': reason
            }
            
            # Log to CSV
            csv_row = vehicle_data.copy()
            csv_row.update({
                'time': round(sim_time, 1),
                'scenario': self.scenario_name,
                'runtime_mode': self.runtime_mode,
                'collision_count': self.stats['collision_events']
            })
            self.log_to_csv(csv_row)
            
            # Collect critical snapshots for final display
            if stage in ['THRESHOLD_MONITORING', 'DECISION_FINAL']:
                # Store vehicle data for potential snapshot
                if not hasattr(self, '_current_snapshot_data'):
                    self._current_snapshot_data = {}
                self._current_snapshot_data[vehicle_id] = vehicle_data.copy()
                
                # Check if we have enough vehicles for a critical snapshot
                if len(self._current_snapshot_data) >= 3:
                    # Count different applied actions
                    applied_actions = set()
                    has_decision_final = False
                    
                    for vid, data in self._current_snapshot_data.items():
                        applied_actions.add(data.get('applied_action', 'UNKNOWN'))
                        if data.get('stage') == 'DECISION_FINAL':
                            has_decision_final = True
                    
                    # Check if conditions are met for critical snapshot
                    if has_decision_final and len(applied_actions) >= 2:
                        # Store this critical snapshot
                        snapshot = {
                            'time': sim_time,
                            'vehicles': self._current_snapshot_data.copy()
                        }
                        self.critical_snapshots.append(snapshot)
                        
                        # Keep only the best snapshot (limit storage)
                        if len(self.critical_snapshots) > 5:
                            self.critical_snapshots.pop(0)
            
            # Reset snapshot data at each time step
            if not hasattr(self, '_last_snapshot_time') or sim_time > self._last_snapshot_time:
                self._current_snapshot_data = {}
                self._last_snapshot_time = sim_time
            
            # Print professional terminal log for DECISION zone only
            if zone == 'DECISION':
                # Use safe_float and safe_text to prevent None formatting errors
                nearest = self.safe_text(vehicle_data.get('nearest_vehicle_id'))
                conflict = self.safe_float(awareness.get('conflict_count', 0))
                eta_gap = self.safe_float(awareness.get('min_eta_gap', 0))
                right_side = self.safe_float(awareness.get('right_side_vehicle_present', 0))
                action = self.safe_text(vehicle_data.get('applied_action'))
                reason = self.safe_text(vehicle_data.get('decision_reason'))
                
                # Format model display based on prediction type
                if model_label == "BUFFERING":
                    model_display = "BUFFERING(0.00)"
                elif model_label == "UNKNOWN":
                    model_display = "UNKNOWN(0.00)"
                else:
                    model_display = f'{model_label}({confidence:.2f})'
                
                log_msg = f"veh={vehicle_id} | zone={zone} | nearest={nearest} | model={model_display} | conflict={conflict} | eta_gap={eta_gap:.2f} | right_side={right_side} | action={action} | reason={reason}"
                print(f"[PP1] t={sim_time:04.1f}s | scenario={self.scenario_name} | {log_msg}")
            
            return vehicle_data
            
        except Exception as e:
            print(f"[PP1] Error processing {vehicle_id}: {e}")
            return {}
    
    def run_simulation(self):
        """Run SUMO simulation with professional multi-vehicle processing."""
        # Determine config file
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sumocfg_file = os.path.join(project_root, "configs", f"pp1_scenario_{self.scenario}_fixed.sumocfg")
        net_file = os.path.join(project_root, "configs", "unsignalized_intersection.net.xml")
        sumocfg_abs = os.path.abspath(sumocfg_file)
        
        if not os.path.exists(sumocfg_file):
            print(f"[PP1] ✗ Config file not found: {sumocfg_file}")
            sys.exit(1)
        
        # Print startup information
        print(f"\n[PP1] SUMO config: {sumocfg_file}")
        print(f"[PP1] Absolute config path: {sumocfg_abs}")
        print(f"[PP1] SUMO binary: {self.sumo_binary}")
        print(f"[PP1] Network file: {net_file}")
        print(f"[PP1] Route file: {sumocfg_file.replace('.sumocfg', '.rou.xml')}")
        print(f"[PP1] Model runtime: {self.runtime_mode}")
        print(f"[PP1] CSV path: {self.csv_file_path}")
        
        # Validate route file and network
        route_file = sumocfg_file.replace('.sumocfg', '.rou.xml')
        print(f"\n[VALIDATION] Route file path: {route_file}")
        
        # Check route file exists and parse it
        if os.path.exists(route_file):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(route_file)
                root = tree.getroot()
                
                # Get vehicles
                vehicles = root.findall('vehicle')
                vehicle_ids = [v.get('id') for v in vehicles]
                print(f"[VALIDATION] Number of vehicles in route file: {len(vehicle_ids)}")
                print(f"[VALIDATION] Vehicle IDs: {vehicle_ids}")
                
                # Get routes
                routes = root.findall('route')
                route_edges = [r.get('edges') for r in routes]
                print(f"[VALIDATION] Route edges: {route_edges}")
                
                # Get vehicle details
                for v in vehicles:
                    vid = v.get('id')
                    depart = v.get('depart')
                    departPos = v.get('departPos')
                    departSpeed = v.get('departSpeed')
                    route = v.find('route')
                    edges = route.get('edges') if route is not None else 'No route'
                    print(f"[VALIDATION] {vid}: depart={depart}, pos={departPos}, speed={departSpeed}, route={edges}")
                    
            except Exception as e:
                print(f"[VALIDATION] Error parsing route file: {e}")
        else:
            print(f"[VALIDATION] Route file does not exist: {route_file}")
        
        # Check network file and get edge IDs
        if os.path.exists(net_file):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(net_file)
                root = tree.getroot()
                
                # Get edges
                edges = root.findall('edge')
                edge_ids = [edge.get('id') for edge in edges if not edge.get('id', '').startswith(':')]
                print(f"[VALIDATION] Network edge IDs (first 10): {edge_ids[:10]}")
                print(f"[VALIDATION] Total network edges: {len(edge_ids)}")
                
            except Exception as e:
                print(f"[VALIDATION] Error parsing network file: {e}")
        else:
            print(f"[VALIDATION] Network file does not exist: {net_file}")
        
        # Start SUMO with stable options
        sumo_cmd = [
            self.sumo_binary,
            "-c", sumocfg_abs,
            "--start",
            "--step-length", "0.2",
            "--delay", "300",
            "--no-step-log", "true",
            "--duration-log.disable", "true",
            "--no-warnings", "true",
            "--collision.check-junctions", "true",
            "--collision.action", "warn"
        ]
        
        print(f"[PP1] Starting SUMO simulation...")
        print(f"[PP1] Command: {' '.join(sumo_cmd)}")
        
        try:
            traci.start(sumo_cmd)
        except Exception as e:
            print(f"[PP1] ✗ Failed to start SUMO: {e}")
            print(f"[PP1] Try running manually: {self.sumo_binary} -c \"{sumocfg_abs}\"")
            sys.exit(1)
        
        self.stats['start_time'] = time.time()
        
        try:
            step = 0
            vehicles_seen = set()
            last_sim_time = 0.0
            
            while traci.simulation.getMinExpectedNumber() > 0 and step < self.max_steps:
                # Update simulation
                traci.simulationStep()
                sim_time = traci.simulation.getTime()
                last_sim_time = sim_time
                self.last_sim_time = sim_time
                
                # Process all vehicles at this step
                all_vehicle_ids = traci.vehicle.getIDList()
                vehicle_data_list = []
                
                for vehicle_id in all_vehicle_ids:
                    vehicle_data = self.process_vehicle(vehicle_id, sim_time, all_vehicle_ids)
                    if vehicle_data:
                        vehicle_data_list.append(vehicle_data)
                        # Track unique vehicles
                        if 'unique_vehicles' not in self.stats:
                            self.stats['unique_vehicles'] = set()
                        self.stats['unique_vehicles'].add(vehicle_id)
                
                # Print local awareness table every 1 second
                if int(sim_time) > int(self.stats.get('last_table_time', -1)):
                    self.print_local_awareness_table(sim_time, vehicle_data_list)
                    self.stats['last_table_time'] = sim_time
                
                # Check for collisions
                collision_count = traci.simulation.getCollidingVehiclesIDList()
                if collision_count:
                    self.stats['collision_events'] += len(collision_count)
                    print(f"[PP1] ⚠ COLLISION detected: {collision_count}")
                
                # Debug prints every 1 second
                if int(sim_time) > int(self.stats.get('last_debug_time', -1)):
                    expected = traci.simulation.getMinExpectedNumber()
                    print(f"[DEBUG] t={sim_time:.1f}s, active vehicles={len(all_vehicle_ids)}, expected vehicles={expected}")
                    if all_vehicle_ids:
                        print(f"[DEBUG] Active vehicle IDs: {all_vehicle_ids}")
                    else:
                        print("[DEBUG] No vehicles inserted. Check route file, depart times, and route edge IDs.")
                    self.stats['last_debug_time'] = sim_time
                
                step += 1
                self.stats['total_steps'] += 1
            
            self.stats['end_time'] = time.time()
            
        except Exception as e:
            print(f"[PP1] Demo error: {e}")
        finally:
            try:
                traci.close()
            except:
                pass
        
        # Write JSON always, CSV only if requested
        self.write_json_summary()
        if self.save_csv:
            self.write_csv_file()
        
        # Print multi-vehicle summary
        self.print_multi_vehicle_summary()
    
    def _print_fairness_summary(self):
        """Print fairness-time summary with waiting time and decision delay metrics."""
        print(f"\nFAIRNESS-TIME SUMMARY")
        print("="*80)
        print(f"{'Vehicle':<12} | {'Waiting Time':<12} | {'Decision Delay':<14} | {'GO':<4} | {'WAIT':<4} | {'YIELD':<5} | {'Starvation Risk'}")
        print("-" * 80)
        
        total_waiting_time = 0.0
        max_waiting_time = 0.0
        vehicle_with_max_waiting = None
        vehicle_count = 0
        overall_starvation_risk = False
        
        # Sort vehicles by ID for consistent display
        for vehicle_id in sorted(self.fairness_tracking['per_vehicle'].keys()):
            vehicle_fairness = self.fairness_tracking['per_vehicle'][vehicle_id]
            waiting_time = vehicle_fairness['waiting_time']
            decision_delay = vehicle_fairness['decision_delay']
            go_count = vehicle_fairness['GO']
            wait_count = vehicle_fairness['WAIT']
            yield_count = vehicle_fairness['YIELD']
            starvation_risk = vehicle_fairness['starvation_risk']
            
            # Track statistics
            if waiting_time > 0 or go_count > 0 or wait_count > 0 or yield_count > 0:
                total_waiting_time += waiting_time
                vehicle_count += 1
                
                if waiting_time > max_waiting_time:
                    max_waiting_time = waiting_time
                    vehicle_with_max_waiting = vehicle_id
                
                if starvation_risk:
                    overall_starvation_risk = True
            
            # Format waiting time and decision delay
            waiting_str = f"{waiting_time:.1f}s" if waiting_time > 0 else "0.0s"
            delay_str = f"{decision_delay:.1f}s" if decision_delay > 0 else "0.0s"
            risk_str = "YES" if starvation_risk else "NO"
            
            print(f"{vehicle_id:<12} | {waiting_str:<12} | {delay_str:<14} | {go_count:<4} | {wait_count:<4} | {yield_count:<5} | {risk_str}")
        
        # Calculate and display summary statistics
        average_waiting_time = total_waiting_time / vehicle_count if vehicle_count > 0 else 0.0
        max_waiting_str = f"{max_waiting_time:.1f}s" if max_waiting_time > 0 else "0.0s"
        overall_risk_str = "YES" if overall_starvation_risk else "NO"
        
        print("-" * 80)
        print(f"Average waiting time: {average_waiting_time:.1f}s")
        print(f"Maximum waiting time: {max_waiting_str}")
        print(f"Vehicle with max waiting: {vehicle_with_max_waiting or 'None'}")
        print(f"Overall starvation risk: {overall_risk_str}")
    
    def print_multi_vehicle_summary(self):
        """Print comprehensive multi-vehicle decision summary."""
        print("\n" + "="*80)
        print("MULTI-VEHICLE DECISION SUMMARY")
        print("="*80)
        
        # Calculate total time
        total_time = 0.0
        if self.stats['end_time'] and self.stats['start_time']:
            total_time = self.stats['end_time'] - self.stats['start_time']
        
        print(f"Scenario: {self.scenario_name}")
        print(f"Total simulation time: {getattr(self, 'last_sim_time', 0.0):.1f} seconds")
        print(f"Total steps processed: {self.stats['total_steps']}")
        print(f"Total unique vehicles: {len(self.stats.get('unique_vehicles', set()))}")
        print(f"Total vehicles processed: {self.stats['total_steps']}")
        print(f"Total predictions made: {self.stats['lstm_predictions']}")
        print(f"Total buffering rows: {self.stats['buffering_rows']}")
        print(f"Total collisions: {self.stats['collision_events']}")
        print(f"CSV log path: {self.csv_file_path}")
        
        print(f"\nZone counts:")
        for zone, count in sorted(self.stats['zone_distribution'].items()):
            print(f"  {zone}: {count}")
        
        print(f"\nTHRESHOLD MONITORING SUMMARY:")
        threshold_rows = self.stats.get('threshold_monitoring_rows', 0)
        print(f"  threshold rows collected: {threshold_rows}")
        print(f"  neutral monitoring rows: {threshold_rows}")
        print(f"  local awareness rows collected: {threshold_rows}")
        print(f"  final decisions made here = 0")
        
        print(f"\nDECISION STAGE SUMMARY:")
        final_decisions = sum(self.stats['action_distribution'].values())
        print(f"  final decision events: {final_decisions}")
        go_count = self.stats['action_distribution'].get('GO', 0)
        yield_count = self.stats['action_distribution'].get('YIELD', 0)
        wait_count = self.stats['action_distribution'].get('WAIT', 0)
        print(f"  GO count: {go_count}")
        print(f"  YIELD count: {yield_count}")
        print(f"  WAIT count: {wait_count}")
        
        print(f"\nPER-VEHICLE FINAL DECISION SNAPSHOT:")
        print(f"{'Vehicle':<12} | {'Stage':<20} | {'Zone':<9} | {'Conflict Vehicles':<18} | {'Merge':<6} | {'Crossing':<9} | {'Right-side':<10} | {'ETA Gap':<8} | {'Model Decision':<15} | {'Final Decision':<15} | {'Applied Action':<15} | {'Reason'}")
        print("-" * 140)
        
        # Display the best critical snapshot
        if self.critical_snapshots:
            # Select the best snapshot (prefer one with DECISION_FINAL vehicles)
            best_snapshot = None
            for snapshot in self.critical_snapshots:
                has_decision_final = any(
                    data.get('stage') == 'DECISION_FINAL' 
                    for data in snapshot['vehicles'].values()
                )
                if has_decision_final:
                    best_snapshot = snapshot
                    break
            
            if not best_snapshot:
                best_snapshot = self.critical_snapshots[0]
            
            print(f"Critical moment at t={best_snapshot['time']:.1f}s:")
            
            # Sort vehicles by ID
            for vehicle_id in sorted(best_snapshot['vehicles'].keys()):
                data = best_snapshot['vehicles'][vehicle_id]
                
                # Format model decision with confidence
                model_decision = data.get('model_decision', 'UNKNOWN')
                confidence = data.get('model_confidence', 0.0)
                if model_decision != 'NEUTRAL' and confidence > 0:
                    model_display = f"{model_decision}({confidence:.2f})"
                else:
                    model_display = model_decision
                
                # Extract and format data
                stage = data.get('stage', 'UNKNOWN')
                zone = data.get('zone', 'UNKNOWN')
                conflict_vehicles = data.get('conflict_vehicle_ids', '[]')
                merge_conflict = data.get('merge_conflict', 0)
                crossing_conflict = data.get('crossing_conflict', 0)
                right_side = data.get('right_side_vehicle_present', 0)
                eta_gap = f"{data.get('min_eta_gap', 0.0):.2f}"
                final_decision = data.get('final_decision', 'UNKNOWN')
                applied_action = data.get('applied_action', 'UNKNOWN')
                reason = data.get('decision_reason', 'unknown')
                
                print(f"{vehicle_id:<12} | {stage:<20} | {zone:<9} | {conflict_vehicles:<18} | {merge_conflict:<6} | {crossing_conflict:<9} | {right_side:<10} | {eta_gap:<8} | {model_display:<15} | {final_decision:<15} | {applied_action:<15} | {reason}")
        else:
            print("No critical snapshot captured during simulation.")
        
        print(f"\nInterpretation:")
        print(f"- THRESHOLD_MONITORING rows are awareness collection only.")
        print(f"- DECISION_FINAL rows are final decisions.")
        print(f"- Applied action is the action sent to SUMO.")
        
        print(f"\nModel prediction distribution:")
        for label, count in sorted(self.stats['model_prediction_distribution'].items()):
            print(f"  {label}: {count}")
        
        print(f"\nPer-vehicle action counts:")
        for vehicle_id, actions in sorted(self.stats['per_vehicle_actions'].items()):
            action_str = ", ".join([f"{action}={count}" for action, count in sorted(actions.items())])
            print(f"  {vehicle_id}: {action_str}")
        
        # Fairness-time summary
        self._print_fairness_summary()
        
        print(f"\nRuntime note:")
        print(f"  TensorFlow not used.")
        print(f"  TFLite not used.")
        print(f"  Mock model not used.")
        print(f"  NumPy exact LSTM weights used.")
        print(f"  Scaler fallback: {'YES' if self.predictor.allow_identity_scaler else 'NO'}")
        print(f"  Label encoder fallback: {'YES' if self.predictor.allow_default_labels else 'NO'}")
        
        print("="*80)
    
    def run(self):
        """Run complete professional PP1 demo."""
        print(f"[PP1] Starting PP1 Professional Multi-Vehicle V2V Decision Demo - {self.scenario_name}")
        
        # Setup logging
        self.setup_csv_logging()
        
        # Run simulation
        try:
            self.run_simulation()
        except KeyboardInterrupt:
            print("\n[PP1] Demo interrupted by user")
        except Exception as e:
            print(f"[PP1] Demo error: {e}")
        finally:
            # Write CSV log
            self.write_csv_file()
            
            # Keep GUI open for viewing
            if not self.nogui and self.stats['total_vehicles_processed'] > 0 and self.keep_open_seconds > 0:
                print(f"[PP1] Keeping SUMO GUI open for {self.keep_open_seconds} seconds for final viewing")
                time.sleep(self.keep_open_seconds)


def main():
    """Main entry point for professional PP1 demo."""
    parser = argparse.ArgumentParser(description="PP1 Professional Multi-Vehicle V2V Decision Demo")
    parser.add_argument("--scenario", type=int, choices=[1, 2], default=1,
                       help="Scenario to run (1=Safe GO, 2=Conflict YIELD/WAIT)")
    parser.add_argument("--validate-only", action="store_true", default=False,
                       help="Only validate config files without running simulation")
    parser.add_argument("--nogui", action="store_true", default=False,
                       help="Run without GUI")
    parser.add_argument("--keep-open-seconds", type=int, default=10,
                       help="Keep SUMO GUI open for N seconds after simulation completes")
    parser.add_argument("--center-x", type=float, default=0,
                       help="Center X coordinate for camera")
    parser.add_argument("--center-y", type=float, default=0,
                       help="Center Y coordinate for camera")
    parser.add_argument("--allow-identity-scaler", action="store_true", default=False,
                       help="Allow identity scaler fallback")
    parser.add_argument("--allow-default-labels", action="store_true", default=False,
                       help="Allow default label classes fallback")
    parser.add_argument("--max-steps", type=int, default=600,
                       help="Maximum simulation steps")
    parser.add_argument("--save-csv", action="store_true", default=False,
                       help="Save CSV log file (default: JSON only)")
    
    args = parser.parse_args()
    
    # Create and run demo
    demo = PP1ProfessionalV2VDemo(scenario=args.scenario, 
                                   validate_only=args.validate_only,
                                   nogui=args.nogui,
                                   keep_open_seconds=args.keep_open_seconds,
                                   center_x=args.center_x,
                                   center_y=args.center_y,
                                   allow_identity_scaler=args.allow_identity_scaler,
                                   allow_default_labels=args.allow_default_labels,
                                   max_steps=args.max_steps,
                                   save_csv=args.save_csv)
    demo.run()


if __name__ == "__main__":
    main()
