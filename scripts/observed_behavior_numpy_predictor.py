"""
NumPy-only Observed Behavior Predictor
Uses exact trained LSTM weights without TensorFlow/TFLite dependencies.
"""

import os
import numpy as np
import pickle
import joblib
from collections import deque
from typing import Dict, List, Optional, Tuple


class ObservedBehaviorNumpyPredictor:
    """NumPy-only LSTM predictor using exact trained weights."""
    
    def __init__(self, models_dir: str = "models/observed_behavior", allow_identity_scaler: bool = False, allow_default_labels: bool = False, debug: bool = False):
        """
        Initialize NumPy-only predictor.
        
        Args:
            models_dir: Directory containing trained model artifacts
            allow_identity_scaler: Allow identity scaler fallback
            allow_default_labels: Allow default label classes fallback
            debug: Enable debug printing
        """
        self.models_dir = models_dir
        self.allow_identity_scaler = allow_identity_scaler
        self.allow_default_labels = allow_default_labels
        self.debug = debug
        self.sequence_length = 10
        self.n_features = 34
        self.lstm_units = 32
        self.dense_hidden_units = 16
        self.n_classes = 3
        
        # Model weights
        self.weights_loaded = False
        self.lstm_kernel = None
        self.lstm_recurrent_kernel = None
        self.lstm_bias = None
        self.dense1_kernel = None
        self.dense1_bias = None
        self.dense2_kernel = None
        self.dense2_bias = None
        
        # Preprocessing
        self.scaler = None
        self.label_encoder = None
        self.class_names = []
        
        # Sequence buffers per vehicle
        self.vehicle_sequences = {}
        
        # Debug flag for first successful prediction
        self.first_prediction_done = False
        
        # Load model artifacts
        self._load_model_artifacts()
    
    def _load_model_artifacts(self):
        """Load trained weights, scaler, and label encoder."""
        # Convert to absolute path
        if not os.path.isabs(self.models_dir):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.models_dir = os.path.join(project_root, self.models_dir)
        
        # Load weights
        weights_path = os.path.join(self.models_dir, "v2v_lstm_observed_behavior_weights.npz")
        if os.path.exists(weights_path):
            try:
                weights = np.load(weights_path, allow_pickle=True)
                self.lstm_kernel = weights['lstm_kernel']
                self.lstm_recurrent_kernel = weights['lstm_recurrent_kernel']
                self.lstm_bias = weights['lstm_bias']
                self.dense1_kernel = weights['dense1_kernel']
                self.dense1_bias = weights['dense1_bias']
                self.dense2_kernel = weights['dense2_kernel']
                self.dense2_bias = weights['dense2_bias']
                self.weights_loaded = True
                print(f"[NUMPY] Loaded exact LSTM weights from {weights_path}")
                print(f"[NUMPY] LSTM kernel: {self.lstm_kernel.shape}")
                print(f"[NUMPY] LSTM recurrent kernel: {self.lstm_recurrent_kernel.shape}")
                print(f"[NUMPY] LSTM bias: {self.lstm_bias.shape}")
                print(f"[NUMPY] Dense1 kernel: {self.dense1_kernel.shape}")
                print(f"[NUMPY] Dense1 bias: {self.dense1_bias.shape}")
                print(f"[NUMPY] Dense2 kernel: {self.dense2_kernel.shape}")
                print(f"[NUMPY] Dense2 bias: {self.dense2_bias.shape}")
            except Exception as e:
                print(f"[NUMPY] Error loading weights: {e}")
                raise
        else:
            raise FileNotFoundError(f"Weights file not found: {weights_path}")
        
        # Load scaler
        scaler_path = os.path.join(self.models_dir, "feature_scaler_observed_behavior.pkl")
        abs_scaler_path = os.path.abspath(scaler_path)
        
        if os.path.exists(scaler_path):
            # Print diagnostics
            file_size = os.path.getsize(scaler_path)
            print(f"[NUMPY] Loading scaler from: {abs_scaler_path}")
            print(f"[NUMPY] Scaler file size: {file_size} bytes ({file_size/1024:.2f} KB)")
            
            # Try joblib first
            try:
                self.scaler = joblib.load(scaler_path)
                print(f"[NUMPY] ✅ Loaded scaler using joblib")
                print(f"[NUMPY] Scaler type: {type(self.scaler)}")
                print(f"[NUMPY] Scaler features: {self.scaler.n_features_in_}")
            except Exception as e:
                print(f"[NUMPY] joblib.load() failed: {e}")
                
                # Try pickle as fallback
                try:
                    with open(scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                    print(f"[NUMPY] ✅ Loaded scaler using pickle")
                    print(f"[NUMPY] Scaler type: {type(self.scaler)}")
                    print(f"[NUMPY] Scaler features: {getattr(self.scaler, 'n_features_in_', 'unknown')}")
                except Exception as e2:
                    print(f"[NUMPY] pickle.load() also failed: {e2}")
                    
                    if self.allow_identity_scaler:
                        print(f"[NUMPY] WARNING: using identity scaler fallback because scaler pkl could not be loaded.")
                        # Create a simple identity scaler as fallback
                        from sklearn.preprocessing import StandardScaler
                        self.scaler = StandardScaler()
                        # Fit with dummy data to avoid issues
                        dummy_data = np.random.randn(100, 34)
                        self.scaler.fit(dummy_data)
                    else:
                        print(f"[NUMPY] ❌ Scaler file is corrupted or not a valid pickle/joblib file. Re-download it from Colab.")
                        print(f"[NUMPY] Or use --allow-identity-scaler flag to use identity scaler fallback.")
                        raise RuntimeError("Scaler file loading failed")
        else:
            raise FileNotFoundError(f"Scaler file not found: {abs_scaler_path}")
        
        # Load label encoder
        encoder_path = os.path.join(self.models_dir, "label_encoder_observed_behavior.pkl")
        abs_encoder_path = os.path.abspath(encoder_path)
        
        if os.path.exists(encoder_path):
            # Print diagnostics
            file_size = os.path.getsize(encoder_path)
            print(f"[NUMPY] Loading label encoder from: {abs_encoder_path}")
            print(f"[NUMPY] Label encoder file size: {file_size} bytes ({file_size/1024:.2f} KB)")
            
            # Try joblib first
            try:
                self.label_encoder = joblib.load(encoder_path)
                self.class_names = self.label_encoder.classes_.tolist()
                print(f"[NUMPY] ✅ Loaded label encoder using joblib")
                print(f"[NUMPY] Label encoder type: {type(self.label_encoder)}")
                print(f"[NUMPY] Classes: {self.class_names}")
            except Exception as e:
                print(f"[NUMPY] joblib.load() failed: {e}")
                
                # Try pickle as fallback
                try:
                    with open(encoder_path, 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    self.class_names = self.label_encoder.classes_.tolist()
                    print(f"[NUMPY] ✅ Loaded label encoder using pickle")
                    print(f"[NUMPY] Label encoder type: {type(self.label_encoder)}")
                    print(f"[NUMPY] Classes: {self.class_names}")
                except Exception as e2:
                    print(f"[NUMPY] pickle.load() also failed: {e2}")
                    
                    if self.allow_default_labels:
                        print(f"[NUMPY] WARNING: using default label classes because label encoder pkl could not be loaded.")
                        # Create a simple label encoder fallback
                        from sklearn.preprocessing import LabelEncoder
                        self.label_encoder = LabelEncoder()
                        self.class_names = ['GO', 'NEUTRAL', 'YIELD']
                        self.label_encoder.fit(self.class_names)
                    else:
                        print(f"[NUMPY] ❌ Label encoder file is corrupted or not a valid pickle/joblib file. Re-download it from Colab.")
                        print(f"[NUMPY] Or use --allow-default-labels flag to use default label classes.")
                        raise RuntimeError("Label encoder file loading failed")
        else:
            raise FileNotFoundError(f"Label encoder file not found: {abs_encoder_path}")
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Stable sigmoid activation function."""
        x = np.asarray(x, dtype=np.float64)
        x = np.clip(x, -50, 50)
        return 1.0 / (1.0 + np.exp(-x))
    
    def _tanh(self, x: np.ndarray) -> np.ndarray:
        """Tanh activation function."""
        return np.tanh(x)
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(x, 0)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Stable softmax activation function."""
        x = np.asarray(x, dtype=np.float64).reshape(-1)
        x = x - np.max(x)
        exp_x = np.exp(x)
        return exp_x / np.sum(exp_x)
    
    def _extract_features(self, vehicle_id: str, vehicle_state: Dict, awareness: Dict) -> np.ndarray:
        """
        Extract 34 features in the exact order used during training.
        
        Args:
            vehicle_id: Vehicle identifier
            vehicle_state: Vehicle state dictionary
            awareness: Local awareness dictionary
            
        Returns:
            Feature vector of shape (34,)
        """
        # Numerical features (1-18)
        features = []
        
        # 1. ego_speed
        features.append(vehicle_state.get('speed', 0.0))
        
        # 2. ego_acceleration
        features.append(vehicle_state.get('acceleration', 0.0))
        
        # 3. ego_signed_acceleration
        features.append(vehicle_state.get('signed_acceleration', 0.0))
        
        # 4. ego_heading_sin
        heading = vehicle_state.get('heading', 0.0)
        features.append(np.sin(np.radians(heading)))
        
        # 5. ego_heading_cos
        features.append(np.cos(np.radians(heading)))
        
        # 6. ego_distance_to_intersection
        features.append(awareness.get('ego_distance_to_intersection', 0.0))
        
        # 7. ego_eta
        features.append(awareness.get('ego_eta', 0.0))
        
        # 8. ego_dx_to_center
        features.append(vehicle_state.get('dx_to_center', 0.0))
        
        # 9. ego_dy_to_center
        features.append(vehicle_state.get('dy_to_center', 0.0))
        
        # 10. context_vehicle_count
        features.append(awareness.get('context_vehicle_count', 0))
        
        # 11. nearest_vehicle_distance
        features.append(awareness.get('nearest_vehicle_distance', 0.0))
        
        # 12. nearest_vehicle_rel_speed
        features.append(awareness.get('nearest_vehicle_rel_speed', 0.0))
        
        # 13. min_eta_gap
        features.append(awareness.get('min_eta_gap', 0.0))
        
        # 14. conflict_count
        features.append(awareness.get('conflict_count', 0))
        
        # 15. min_conflict_eta
        features.append(awareness.get('min_conflict_eta', 0.0))
        
        # 16. right_side_vehicle_present
        features.append(awareness.get('right_side_vehicle_present', 0))
        
        # 17. right_side_vehicle_eta
        features.append(awareness.get('right_side_vehicle_eta', 0.0))
        
        # 18. right_side_vehicle_distance
        features.append(awareness.get('right_side_vehicle_distance', 0.0))
        
        # One-hot categorical features (19-34)
        
        # 19-21. ego_zone (DECISION, THRESHOLD, OUTSIDE)
        zone = awareness.get('ego_zone', 'OUTSIDE')
        features.extend([1 if zone == 'DECISION' else 0,
                        1 if zone == 'THRESHOLD' else 0,
                        1 if zone == 'OUTSIDE' else 0])
        
        # 22-25. ego_approach (EAST, NORTH, SOUTH, WEST)
        approach = vehicle_state.get('approach', 'UNKNOWN')
        features.extend([1 if approach == 'EAST' else 0,
                        1 if approach == 'NORTH' else 0,
                        1 if approach == 'SOUTH' else 0,
                        1 if approach == 'WEST' else 0])
        
        # 26-29. ego_exit (EAST, NORTH, SOUTH, WEST)
        exit_dir = vehicle_state.get('exit', 'UNKNOWN')
        features.extend([1 if exit_dir == 'EAST' else 0,
                        1 if exit_dir == 'NORTH' else 0,
                        1 if exit_dir == 'SOUTH' else 0,
                        1 if exit_dir == 'WEST' else 0])
        
        # 30-33. ego_maneuver (LEFT_TURN, RIGHT_TURN, STRAIGHT, UNKNOWN)
        maneuver = vehicle_state.get('maneuver', 'UNKNOWN')
        features.extend([1 if maneuver == 'LEFT_TURN' else 0,
                        1 if maneuver == 'RIGHT_TURN' else 0,
                        1 if maneuver == 'STRAIGHT' else 0,
                        1 if maneuver == 'UNKNOWN' else 0])
        
        # 34. ego_maneuver_confidence (LOW=0, MEDIUM=1)
        confidence = vehicle_state.get('maneuver_confidence', 'LOW')
        features.append(1 if confidence == 'MEDIUM' else 0)
        
        return np.array(features, dtype=np.float32)
    
    def _lstm_forward(self, sequence: np.ndarray) -> np.ndarray:
        """
        Forward pass through LSTM layer using exact Keras implementation.
        
        Args:
            sequence: Input sequence of shape (sequence_length, n_features)
            
        Returns:
            LSTM output of shape (lstm_units,)
        """
        # Initialize hidden state and cell state
        h = np.zeros(self.lstm_units, dtype=np.float32)
        c = np.zeros(self.lstm_units, dtype=np.float32)
        
        # Process each timestep
        for t in range(sequence.shape[0]):
            x_t = sequence[t]
            
            # Compute gate inputs
            # x_t: (n_features,), lstm_kernel: (n_features, 4*lstm_units)
            # h: (lstm_units,), lstm_recurrent_kernel: (lstm_units, 4*lstm_units)
            # lstm_bias: (4*lstm_units,)
            z = np.dot(x_t, self.lstm_kernel) + np.dot(h, self.lstm_recurrent_kernel) + self.lstm_bias
            
            # Split into gates (Keras order: i, f, c, o)
            gate_size = self.lstm_units
            i = self._sigmoid(z[0:gate_size])
            f = self._sigmoid(z[gate_size:2*gate_size])
            c_bar = self._tanh(z[2*gate_size:3*gate_size])
            o = self._sigmoid(z[3*gate_size:4*gate_size])
            
            # Update cell state and hidden state
            c = f * c + i * c_bar
            h = o * self._tanh(c)
        
        # Dense layer 1: ReLU
        dense1 = self._relu(np.dot(h, self.dense1_kernel) + self.dense1_bias)
        
        # Dense layer 2: Output logits
        logits = np.dot(dense1, self.dense2_kernel) + self.dense2_bias
        
        return logits
    
    def predict(self, vehicle_id: str, vehicle_state: Dict, awareness: Dict) -> Dict:
        """
        Predict vehicle behavior using NumPy LSTM.
        
        Args:
            vehicle_id: Vehicle identifier
            vehicle_state: Vehicle state dictionary
            awareness: Local awareness dictionary
            
        Returns:
            Prediction dictionary with label, confidence, probabilities, and ready flag
        """
        if not self.weights_loaded:
            raise RuntimeError("Model weights not loaded")
        
        # Initialize sequence buffer for this vehicle
        if vehicle_id not in self.vehicle_sequences:
            self.vehicle_sequences[vehicle_id] = deque(maxlen=self.sequence_length)
        
        # Extract features
        features = self._extract_features(vehicle_id, vehicle_state, awareness)
        
        # Add to sequence buffer
        self.vehicle_sequences[vehicle_id].append(features)
        
        # Check if we have enough timesteps
        if len(self.vehicle_sequences[vehicle_id]) < self.sequence_length:
            # Not enough data yet - show BUFFERING
            return {
                "label": "BUFFERING",
                "confidence": 0.0,
                "probabilities": {"GO": 0.0, "NEUTRAL": 0.0, "YIELD": 0.0},
                "ready": False
            }
        
        # Get sequence and scale
        sequence = np.array(self.vehicle_sequences[vehicle_id], dtype=np.float32)
        sequence_scaled = self.scaler.transform(sequence)
        
        # LSTM forward pass (now includes dense layers and returns logits)
        logits = self._lstm_forward(sequence_scaled)
        
        # Softmax
        probabilities = self._softmax(logits)
        
        # Validate probabilities shape
        if probabilities.ndim != 1 or probabilities.shape[0] != 3:
            raise ValueError(f"Expected probs shape (3,), got {probabilities.shape}")
        
        # Get prediction
        pred_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[pred_idx])
        
        # Get label
        if hasattr(self.label_encoder, 'inverse_transform'):
            label = self.label_encoder.inverse_transform([pred_idx])[0]
        else:
            # Use default classes
            classes = ["GO", "NEUTRAL", "YIELD"]
            label = classes[pred_idx]
        
        # Debug print for first successful prediction
        if self.debug and not self.first_prediction_done:
            print(f"[NUMPY] First real prediction successful")
            print(f"[NUMPY] sequence shape: {sequence.shape}")
            print(f"[NUMPY] scaled sequence shape: {sequence_scaled.shape}")
            print(f"[NUMPY] logits shape: {logits.shape}")
            print(f"[NUMPY] probs shape: {probabilities.shape}")
            print(f"[NUMPY] probs: {probabilities}")
            print(f"[NUMPY] pred_idx: {pred_idx}")
            print(f"[NUMPY] label: {label}")
            self.first_prediction_done = True
        
        return {
            "label": label,
            "confidence": confidence,
            "probabilities": {
                "GO": float(probabilities[0]),
                "NEUTRAL": float(probabilities[1]),
                "YIELD": float(probabilities[2])
            },
            "ready": True
        }
    
    def reset_sequence(self, vehicle_id: str):
        """Reset sequence buffer for a vehicle."""
        if vehicle_id in self.vehicle_sequences:
            self.vehicle_sequences[vehicle_id].clear()
    
    def get_sequence_length(self, vehicle_id: str) -> int:
        """Get current sequence length for a vehicle."""
        return len(self.vehicle_sequences.get(vehicle_id, []))


def load_observed_behavior_numpy_predictor(models_dir: str = "models/observed_behavior", allow_identity_scaler: bool = False, allow_default_labels: bool = False, debug: bool = False) -> ObservedBehaviorNumpyPredictor:
    """
    Load NumPy-only observed behavior predictor.
    
    Args:
        models_dir: Directory containing trained model artifacts
        allow_identity_scaler: Allow identity scaler fallback
        allow_default_labels: Allow default label classes fallback
        debug: Enable debug printing
        
    Returns:
        Configured ObservedBehaviorNumpyPredictor instance
    """
    return ObservedBehaviorNumpyPredictor(models_dir, allow_identity_scaler, allow_default_labels, debug)
