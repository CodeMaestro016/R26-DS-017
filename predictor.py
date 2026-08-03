"""TensorFlow-free two-stage intention inference for SUMO."""

import json
from pathlib import Path

import numpy as np

from config import (
    MIN_APPROACH_DISPLACEMENT_METERS,
    MODEL_DIRECTORY,
    MODEL_HISTORY_LENGTH,
    MODEL_SAMPLE_INTERVAL_SECONDS,
    PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)


CLASS_LABELS = ("LEFT", "RIGHT", "STRAIGHT")
UNKNOWN_LABEL = "UNKNOWN"


class PredictionContractError(ValueError):
    """Raised when a SUMO history violates the trained-model contract."""


class IntentionPredictor:
    """Load the two ONNX GRUs and run CPU-only shadow inference."""

    def __init__(self, model_directory=MODEL_DIRECTORY):
        try:
            import onnxruntime as ort
        except ImportError as error:
            raise RuntimeError(
                "onnxruntime is required. Run: "
                "pip install -r requirements.txt"
            ) from error

        self.model_directory = Path(model_directory)
        self._require_files()

        with (
            self.model_directory
            / "feature_specification.json"
        ).open("r", encoding="utf-8") as handle:
            self.feature_specification = json.load(handle)
        self._validate_feature_contract()

        with (
            self.model_directory
            / "robust_calibration_and_unknown_policy.json"
        ).open("r", encoding="utf-8") as handle:
            self.policy = json.load(handle)

        scaler_path = (
            self.model_directory / "training_only_scalers.npz"
        )
        with np.load(scaler_path) as scaler_data:
            self.primary_mean = scaler_data[
                "primary_mean"
            ].astype(np.float32)
            self.primary_standard_deviation = scaler_data[
                "primary_standard_deviation"
            ].astype(np.float32)
            self.secondary_mean = scaler_data[
                "secondary_mean"
            ].astype(np.float32)
            self.secondary_standard_deviation = scaler_data[
                "secondary_standard_deviation"
            ].astype(np.float32)

        providers = ["CPUExecutionProvider"]
        self.primary_session = ort.InferenceSession(
            str(self.model_directory / "primary_1.0s_gru.onnx"),
            providers=providers,
        )
        self.secondary_session = ort.InferenceSession(
            str(self.model_directory / "secondary_0.5s_gru.onnx"),
            providers=providers,
        )

        self.primary_input_name = (
            self.primary_session.get_inputs()[0].name
        )
        self.primary_output_name = (
            self.primary_session.get_outputs()[0].name
        )
        self.secondary_input_name = (
            self.secondary_session.get_inputs()[0].name
        )
        self.secondary_output_name = (
            self.secondary_session.get_outputs()[0].name
        )

        self.primary_threshold = float(
            self.policy["primary_1.0s"]["unknown_threshold"]
        )
        self.secondary_threshold = float(
            self.policy["secondary_0.5s"][
                "unknown_threshold"
            ]
        )

        print(
            "Loaded TensorFlow-free intention models with "
            "CPUExecutionProvider."
        )

    def _validate_feature_contract(self):
        expected_contract = {
            "position_history_shape": [MODEL_HISTORY_LENGTH, 2],
            "frame_interval_seconds": (
                MODEL_SAMPLE_INTERVAL_SECONDS
            ),
            "causal_sequence_shape": [48, 6],
            "approach_direction_estimation": (
                "position_at_frame_10_minus_position_at_frame_0"
            ),
        }
        mismatches = {
            key: {
                "bundle": self.feature_specification.get(key),
                "runtime": expected_value,
            }
            for key, expected_value in expected_contract.items()
            if self.feature_specification.get(key) != expected_value
        }
        if mismatches:
            raise PredictionContractError(
                "The runtime preprocessing contract does not match the "
                f"deployed model bundle: {mismatches}"
            )

    def _require_files(self):
        required_files = (
            "primary_1.0s_gru.onnx",
            "secondary_0.5s_gru.onnx",
            "training_only_scalers.npz",
            "feature_specification.json",
            "robust_calibration_and_unknown_policy.json",
        )
        missing = [
            name
            for name in required_files
            if not (self.model_directory / name).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing intention deployment files: {missing}"
            )

    @staticmethod
    def _history_arrays(position_history):
        if len(position_history) != MODEL_HISTORY_LENGTH:
            raise PredictionContractError(
                f"Expected {MODEL_HISTORY_LENGTH} genuine samples; "
                f"received {len(position_history)}."
            )

        timestamps = np.asarray(
            [sample["timestamp"] for sample in position_history],
            dtype=np.float64,
        )
        positions = np.asarray(
            [sample["position"] for sample in position_history],
            dtype=np.float64,
        )

        if positions.shape != (MODEL_HISTORY_LENGTH, 2):
            raise PredictionContractError(
                f"Expected position shape (50, 2); got "
                f"{positions.shape}."
            )
        if not np.all(np.isfinite(positions)):
            raise PredictionContractError(
                "Position history contains NaN or infinite values."
            )

        intervals = np.diff(timestamps)
        if not np.allclose(
            intervals,
            MODEL_SAMPLE_INTERVAL_SECONDS,
            rtol=0.0,
            atol=SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS,
        ):
            raise PredictionContractError(
                "History is not 25 Hz genuine data. "
                f"Interval range is {intervals.min():.6f} to "
                f"{intervals.max():.6f} seconds."
            )

        return timestamps, positions

    @staticmethod
    def build_causal_features(position_history):
        """Reproduce the locked 50-position to 48x6 feature builder."""
        _, positions = IntentionPredictor._history_arrays(
            position_history
        )
        dt = MODEL_SAMPLE_INTERVAL_SECONDS

        approach_vector = positions[10] - positions[0]
        approach_displacement = float(
            np.linalg.norm(approach_vector)
        )
        if approach_displacement < MIN_APPROACH_DISPLACEMENT_METERS:
            raise PredictionContractError(
                "The vehicle did not move enough to estimate an "
                "approach direction."
            )

        longitudinal_axis = approach_vector / approach_displacement
        lateral_axis = np.asarray(
            [-longitudinal_axis[1], longitudinal_axis[0]],
            dtype=np.float64,
        )

        velocity = np.diff(positions, axis=0) / dt
        acceleration = np.diff(velocity, axis=0) / dt
        aligned_velocity = velocity[1:]

        features = np.column_stack(
            (
                np.linalg.norm(aligned_velocity, axis=1),
                np.linalg.norm(acceleration, axis=1),
                aligned_velocity @ longitudinal_axis,
                aligned_velocity @ lateral_axis,
                acceleration @ longitudinal_axis,
                acceleration @ lateral_axis,
            )
        )

        if features.shape != (48, 6):
            raise PredictionContractError(
                f"Expected causal feature shape (48, 6); got "
                f"{features.shape}."
            )
        if not np.all(np.isfinite(features)):
            raise PredictionContractError(
                "Causal features contain NaN or infinite values."
            )
        return features.astype(np.float32)

    @staticmethod
    def _scale(features, mean, standard_deviation):
        scaled = (features - mean) / standard_deviation
        if not np.all(np.isfinite(scaled)):
            raise PredictionContractError(
                "Scaled features contain NaN or infinite values."
            )
        return scaled[np.newaxis, ...].astype(np.float32)

    @staticmethod
    def _probability_record(probabilities, threshold):
        vector = np.asarray(probabilities, dtype=np.float64)
        if vector.shape != (3,) or not np.all(np.isfinite(vector)):
            raise PredictionContractError(
                f"Invalid model output shape or values: {vector}."
            )

        total = float(vector.sum())
        if total <= 0.0:
            raise PredictionContractError(
                "Model probability sum is not positive."
            )
        vector = vector / total

        class_index = int(np.argmax(vector))
        confidence = float(vector[class_index])
        accepted = confidence >= threshold
        label = CLASS_LABELS[class_index] if accepted else UNKNOWN_LABEL

        return {
            "probabilities": {
                class_label: float(vector[index])
                for index, class_label in enumerate(CLASS_LABELS)
            },
            "predicted_class": CLASS_LABELS[class_index],
            "label": label,
            "confidence": confidence,
            "threshold": float(threshold),
            "accepted": bool(accepted),
        }

    @staticmethod
    def fuse_stage_results(primary, secondary):
        """Fuse chronologically separate stage results conservatively."""
        if primary is None and secondary is None:
            return UNKNOWN_LABEL, "BOTH_STAGES_MISSING"
        if primary is None:
            return UNKNOWN_LABEL, "PRIMARY_MISSING"
        if secondary is None:
            return UNKNOWN_LABEL, "SECONDARY_MISSING"

        if primary["accepted"] and secondary["accepted"]:
            if primary["label"] == secondary["label"]:
                return (
                    primary["label"],
                    "CONFIRMED_AGREEMENT",
                )
            return UNKNOWN_LABEL, "HORIZON_DISAGREEMENT"

        if not primary["accepted"] and secondary["accepted"]:
            return secondary["label"], "SECONDARY_RECOVERY"

        if primary["accepted"] and not secondary["accepted"]:
            return UNKNOWN_LABEL, "SECONDARY_UNCERTAIN"

        return UNKNOWN_LABEL, "BOTH_UNCERTAIN"

    @staticmethod
    def _feature_diagnostics(features, scaled_features):
        feature_names = (
            "speed",
            "acceleration_magnitude",
            "longitudinal_velocity",
            "lateral_velocity",
            "longitudinal_acceleration",
            "lateral_acceleration",
        )
        return {
            "maximum_absolute_z_score": float(
                np.max(np.abs(scaled_features))
            ),
            "raw_feature_means": {
                name: float(features[:, index].mean())
                for index, name in enumerate(feature_names)
            },
            "maximum_absolute_z_score_by_feature": {
                name: float(
                    np.max(np.abs(scaled_features[:, index]))
                )
                for index, name in enumerate(feature_names)
            },
        }

    def predict_stage(self, position_history, stage):
        """Run exactly one model at its own temporal trigger."""
        features = self.build_causal_features(position_history)

        if stage == "primary":
            mean = self.primary_mean
            standard_deviation = self.primary_standard_deviation
            session = self.primary_session
            input_name = self.primary_input_name
            output_name = self.primary_output_name
            threshold = self.primary_threshold
            lead_time_seconds = (
                PRIMARY_PREDICTION_LEAD_TIME_SECONDS
            )
        elif stage == "secondary":
            mean = self.secondary_mean
            standard_deviation = self.secondary_standard_deviation
            session = self.secondary_session
            input_name = self.secondary_input_name
            output_name = self.secondary_output_name
            threshold = self.secondary_threshold
            lead_time_seconds = (
                SECONDARY_PREDICTION_LEAD_TIME_SECONDS
            )
        else:
            raise ValueError(
                "stage must be either 'primary' or 'secondary'"
            )

        model_input = self._scale(
            features,
            mean,
            standard_deviation,
        )
        probabilities = session.run(
            [output_name],
            {input_name: model_input},
        )[0][0]
        result = self._probability_record(
            probabilities,
            threshold,
        )
        result.update(
            {
                "stage": stage,
                "lead_time_seconds": lead_time_seconds,
                "feature_diagnostics": self._feature_diagnostics(
                    features,
                    model_input[0],
                ),
            }
        )
        return result
