"""TensorFlow-free two-stage intention inference for SUMO."""

# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import numpy as np for use in this module.
import numpy as np

# Import MIN_APPROACH_DISPLACEMENT_METERS, MODEL_DIRECTORY, MODEL_HISTORY_LENGTH, MODEL_SAMPLE_INTERVAL_SECONDS,
# PRIMARY_PREDICTION_LEAD_TIME_SECONDS,... from config for the operations below.
from config import (
    MIN_APPROACH_DISPLACEMENT_METERS,
    MODEL_DIRECTORY,
    MODEL_HISTORY_LENGTH,
    MODEL_SAMPLE_INTERVAL_SECONDS,
    PRIMARY_PREDICTION_LEAD_TIME_SECONDS,
    SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS,
    SECONDARY_PREDICTION_LEAD_TIME_SECONDS,
)


# Set CLASS_LABELS to a tuple containing the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT'.
CLASS_LABELS = ("LEFT", "RIGHT", "STRAIGHT")
# Set UNKNOWN_LABEL to the text 'UNKNOWN'.
UNKNOWN_LABEL = "UNKNOWN"
# Set FEATURE_DIAGNOSTIC_NAMES to a tuple containing the text 'speed', the text 'acceleration_magnitude', the text
# 'longitudinal_velocity', the text...
FEATURE_DIAGNOSTIC_NAMES = (
    "speed",
    "acceleration_magnitude",
    "longitudinal_velocity",
    "lateral_velocity",
    "longitudinal_acceleration",
    "lateral_acceleration",
)


# Raised when a SUMO history violates the trained-model contract.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class PredictionContractError(ValueError):
    """Raised when a SUMO history violates the trained-model contract."""


# Load the two ONNX GRUs and run CPU-only shadow inference.
# Instances expose the attributes and methods implemented in this class.
class IntentionPredictor:
    """Load the two ONNX GRUs and run CPU-only shadow inference."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input model_directory: the supplied model directory.
    # Output: no explicit value; normal completion returns None.
    # Processing: handle the specified errors.
    def __init__(self, model_directory=MODEL_DIRECTORY):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Import onnxruntime as ort for use in this module.
            import onnxruntime as ort
        # Handle ImportError as error using the recovery steps below.
        except ImportError as error:
            # Raise RuntimeError with the text 'onnxruntime is required. Run: pip install -r requirements.txt' to
            # stop this execution path.
            raise RuntimeError(
                "onnxruntime is required. Run: "
                "pip install -r requirements.txt"
            # Evaluate error as part of the enclosing expression.
            ) from error

        # Set self.model_directory to the result of Path(model_directory).
        self.model_directory = Path(model_directory)
        # Call self._require_files with the supplied arguments.
        self._require_files()

        # Enter the result of (self.model_directory / 'feature_specification.json').open(the text 'r') as handle
        # and run the enclosed operations within that context.
        with (
            # Evaluate self.model_directory joined with the path segment 'feature_specification.json' as part of the
            # enclosing expression.
            self.model_directory
            # Supply the text 'feature_specification.json' to the enclosing expression.
            / "feature_specification.json"
        # Supply encoding as the text 'utf-8'.
        ).open("r", encoding="utf-8") as handle:
            # Set self.feature_specification to the decoded data produced by json.load from handle.
            self.feature_specification = json.load(handle)
        # Call self._validate_feature_contract with the supplied arguments.
        self._validate_feature_contract()

        # Enter the result of (self.model_directory / 'robust_calibration_and_unknown_policy.json').open(the text
        # 'r') as handle and run the enclosed operations within that context.
        with (
            # Evaluate self.model_directory joined with the path segment 'robust_calibration_and_unknown_policy.json' as
            # part of the enclosing expression.
            self.model_directory
            # Supply the text 'robust_calibration_and_unknown_policy.json' to the enclosing expression.
            / "robust_calibration_and_unknown_policy.json"
        # Supply encoding as the text 'utf-8'.
        ).open("r", encoding="utf-8") as handle:
            # Set self.policy to the decoded data produced by json.load from handle.
            self.policy = json.load(handle)

        # Set scaler_path to self.model_directory joined with the path segment 'training_only_scalers.npz'.
        scaler_path = (
            # Evaluate self.model_directory joined with the path segment 'training_only_scalers.npz' as part of the
            # enclosing expression.
            self.model_directory / "training_only_scalers.npz"
        )
        # Enter the decoded data produced by np.load from scaler_path as scaler_data and run the enclosed
        # operations within that context.
        with np.load(scaler_path) as scaler_data:
            # Set self.primary_mean to the result of scaler_data['primary_mean'].astype(np.float32).
            self.primary_mean = scaler_data[
                "primary_mean"
            # Supply np.float32 to scaler_data['primary_mean'].astype.
            ].astype(np.float32)
            # Set self.primary_standard_deviation to the result of
            # scaler_data['primary_standard_deviation'].astype(np.float32).
            self.primary_standard_deviation = scaler_data[
                "primary_standard_deviation"
            # Supply np.float32 to scaler_data['primary_standard_deviation'].astype.
            ].astype(np.float32)
            # Set self.secondary_mean to the result of scaler_data['secondary_mean'].astype(np.float32).
            self.secondary_mean = scaler_data[
                "secondary_mean"
            # Supply np.float32 to scaler_data['secondary_mean'].astype.
            ].astype(np.float32)
            # Set self.secondary_standard_deviation to the result of
            # scaler_data['secondary_standard_deviation'].astype(np.float32).
            self.secondary_standard_deviation = scaler_data[
                "secondary_standard_deviation"
            # Supply np.float32 to scaler_data['secondary_standard_deviation'].astype.
            ].astype(np.float32)

        # Set providers to a list containing the text 'CPUExecutionProvider'.
        providers = ["CPUExecutionProvider"]
        # Set self.primary_session to the result of ort.InferenceSession(a string built from self.model_directory
        # joined with the path segment 'primary_1.0s_gru.onnx').
        self.primary_session = ort.InferenceSession(
            # Supply a string built from self.model_directory joined with the path segment 'primary_1.0s_gru.onnx' to
            # ort.InferenceSession.
            str(self.model_directory / "primary_1.0s_gru.onnx"),
            # Supply providers as providers.
            providers=providers,
        )
        # Set self.secondary_session to the result of ort.InferenceSession(a string built from
        # self.model_directory joined with the path segment 'secondary_0.5s_gru.onnx').
        self.secondary_session = ort.InferenceSession(
            # Supply a string built from self.model_directory joined with the path segment 'secondary_0.5s_gru.onnx' to
            # ort.InferenceSession.
            str(self.model_directory / "secondary_0.5s_gru.onnx"),
            # Supply providers as providers.
            providers=providers,
        )

        # Set self.primary_input_name to self.primary_session.get_inputs()[0].name.
        self.primary_input_name = (
            # Evaluate self.primary_session.get_inputs()[0].name as part of the enclosing expression.
            self.primary_session.get_inputs()[0].name
        )
        # Set self.primary_output_name to self.primary_session.get_outputs()[0].name.
        self.primary_output_name = (
            # Evaluate self.primary_session.get_outputs()[0].name as part of the enclosing expression.
            self.primary_session.get_outputs()[0].name
        )
        # Set self.secondary_input_name to self.secondary_session.get_inputs()[0].name.
        self.secondary_input_name = (
            # Evaluate self.secondary_session.get_inputs()[0].name as part of the enclosing expression.
            self.secondary_session.get_inputs()[0].name
        )
        # Set self.secondary_output_name to self.secondary_session.get_outputs()[0].name.
        self.secondary_output_name = (
            # Evaluate self.secondary_session.get_outputs()[0].name as part of the enclosing expression.
            self.secondary_session.get_outputs()[0].name
        )

        # Set self.primary_threshold to a floating-point number built from self.policy['primary_1.0s'] at
        # 'unknown_threshold'.
        self.primary_threshold = float(
            # Supply self.policy['primary_1.0s'] at 'unknown_threshold' to float.
            self.policy["primary_1.0s"]["unknown_threshold"]
        )
        # Set self.secondary_threshold to a floating-point number built from self.policy['secondary_0.5s'] at
        # 'unknown_threshold'.
        self.secondary_threshold = float(
            # Supply self.policy['secondary_0.5s'] at 'unknown_threshold' to float.
            self.policy["secondary_0.5s"][
                "unknown_threshold"
            ]
        )

        # Display the text 'Loaded TensorFlow-free intention models with...'.
        print(
            "Loaded TensorFlow-free intention models with "
            "CPUExecutionProvider."
        )

    # Validate feature contract using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _validate_feature_contract(self):
        # Set expected_contract to a dictionary containing position_history_shape, frame_interval_seconds,
        # causal_sequence_shape,...
        expected_contract = {
            # Store a list containing MODEL_HISTORY_LENGTH, 2 under 'position_history_shape'.
            "position_history_shape": [MODEL_HISTORY_LENGTH, 2],
            # Store MODEL_SAMPLE_INTERVAL_SECONDS under 'frame_interval_seconds'.
            "frame_interval_seconds": (
                # Evaluate MODEL_SAMPLE_INTERVAL_SECONDS as part of the enclosing expression.
                MODEL_SAMPLE_INTERVAL_SECONDS
            ),
            # Store a list containing 48, 6 under 'causal_sequence_shape'.
            "causal_sequence_shape": [48, 6],
            # Store the text 'position_at_frame_10_minus_position_at_frame_0' under
            # 'approach_direction_estimation'.
            "approach_direction_estimation": (
                "position_at_frame_10_minus_position_at_frame_0"
            ),
        }
        # Set mismatches to a dictionary of key mapped to a dictionary containing bundle, runtime for (key,
        # expected_value) in key/value pairs from expected_contract; retain entries satisfying key from
        # self.feature_specification; use None if absent differs from expected_value.
        mismatches = {
            # Evaluate a dictionary containing bundle, runtime as part of the enclosing expression.
            key: {
                # Store key from self.feature_specification; use None if absent under 'bundle'.
                "bundle": self.feature_specification.get(key),
                # Store expected_value under 'runtime'.
                "runtime": expected_value,
            }
            # Evaluate key/value pairs from expected_contract as part of the enclosing expression.
            for key, expected_value in expected_contract.items()
            # Evaluate key from self.feature_specification; use None if absent differs from expected_value as part
            # of the enclosing expression.
            if self.feature_specification.get(key) != expected_value
        }
        # Run this branch when mismatches.
        if mismatches:
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                "The runtime preprocessing contract does not match the "
                # Evaluate {mismatches} as part of the enclosing expression.
                f"deployed model bundle: {mismatches}"
            )

    # Require files using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _require_files(self):
        # Set required_files to a tuple containing the text 'primary_1.0s_gru.onnx', the text
        # 'secondary_0.5s_gru.onnx', the text...
        required_files = (
            "primary_1.0s_gru.onnx",
            "secondary_0.5s_gru.onnx",
            "training_only_scalers.npz",
            "feature_specification.json",
            "robust_calibration_and_unknown_policy.json",
        )
        # Set missing to a list of name for name in required_files; retain entries satisfying the negation of
        # whether (self.model_directory / name) is an existing file.
        missing = [
            # Evaluate name as part of the enclosing expression.
            name
            # Evaluate required_files as part of the enclosing expression.
            for name in required_files
            # Evaluate the negation of whether (self.model_directory / name) is an existing file as part of the
            # enclosing expression.
            if not (self.model_directory / name).is_file()
        ]
        # Run this branch when missing.
        if missing:
            # Raise FileNotFoundError with formatted text built from the embedded values to stop this execution
            # path.
            raise FileNotFoundError(
                # Supply formatted text built from the embedded values to FileNotFoundError.
                f"Missing intention deployment files: {missing}"
            )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # History arrays using the inputs and processing steps below.
    # Input position_history: the supplied position history.
    # Output: a tuple containing timestamps, positions.
    # Processing: select branches using the stated conditions.
    def _history_arrays(position_history):
        # Run this branch when the number of entries in position_history differs from MODEL_HISTORY_LENGTH.
        if len(position_history) != MODEL_HISTORY_LENGTH:
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                # Supply formatted text built from the embedded values to PredictionContractError.
                f"Expected {MODEL_HISTORY_LENGTH} genuine samples; "
                # Evaluate {len(position_history)} as part of the enclosing expression.
                f"received {len(position_history)}."
            )

        # Set timestamps to the result of np.asarray(a list of sample at 'timestamp' for sample in
        # position_history).
        timestamps = np.asarray(
            # Supply a list of sample at 'timestamp' for sample in position_history to np.asarray.
            [sample["timestamp"] for sample in position_history],
            # Supply dtype as np.float64.
            dtype=np.float64,
        )
        # Set positions to the result of np.asarray(a list of sample at 'position' for sample in
        # position_history).
        positions = np.asarray(
            # Supply a list of sample at 'position' for sample in position_history to np.asarray.
            [sample["position"] for sample in position_history],
            # Supply dtype as np.float64.
            dtype=np.float64,
        )

        # Run this branch when positions.shape differs from a tuple containing MODEL_HISTORY_LENGTH, 2.
        if positions.shape != (MODEL_HISTORY_LENGTH, 2):
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                # Supply formatted text built from the embedded values to PredictionContractError.
                f"Expected position shape (50, 2); got "
                # Evaluate {positions.shape} as part of the enclosing expression.
                f"{positions.shape}."
            )
        # Run this branch when the negation of the result of np.all(whether positions contains finite numeric
        # values).
        if not np.all(np.isfinite(positions)):
            # Raise PredictionContractError with the text 'Position history contains NaN or infinite values.' to
            # stop this execution path.
            raise PredictionContractError(
                "Position history contains NaN or infinite values."
            )

        # Set intervals to the result of np.diff(timestamps).
        intervals = np.diff(timestamps)
        # Run this branch when the negation of the result of np.allclose(intervals,
        # MODEL_SAMPLE_INTERVAL_SECONDS).
        if not np.allclose(
            # Supply intervals to np.allclose.
            intervals,
            # Supply MODEL_SAMPLE_INTERVAL_SECONDS to np.allclose.
            MODEL_SAMPLE_INTERVAL_SECONDS,
            # Supply rtol as 0.0.
            rtol=0.0,
            # Supply atol as SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS.
            atol=SAMPLE_TIME_ABSOLUTE_TOLERANCE_SECONDS,
        ):
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                "History is not 25 Hz genuine data. "
                # Evaluate {intervals.min():.6f} as part of the enclosing expression.
                f"Interval range is {intervals.min():.6f} to "
                # Evaluate {intervals.max():.6f} as part of the enclosing expression.
                f"{intervals.max():.6f} seconds."
            )

        # Return a tuple containing timestamps, positions to the caller.
        return timestamps, positions

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Reproduce the locked 50-position to 48x6 feature builder.
    # Input position_history: the supplied position history.
    # Output: the result of features.astype(np.float32).
    # Processing: select branches using the stated conditions.
    def build_causal_features(position_history):
        """Reproduce the locked 50-position to 48x6 feature builder."""
        # Set (_, positions) to the result of IntentionPredictor._history_arrays(position_history).
        _, positions = IntentionPredictor._history_arrays(
            # Supply position_history to IntentionPredictor._history_arrays.
            position_history
        )
        # Set dt to MODEL_SAMPLE_INTERVAL_SECONDS.
        dt = MODEL_SAMPLE_INTERVAL_SECONDS

        # Set approach_vector to positions at 10 minus positions at 0.
        approach_vector = positions[10] - positions[0]
        # Set approach_displacement to a floating-point number built from the result of
        # np.linalg.norm(approach_vector).
        approach_displacement = float(
            # Supply the result of np.linalg.norm(approach_vector) to float.
            np.linalg.norm(approach_vector)
        )
        # Run this branch when approach_displacement is less than MIN_APPROACH_DISPLACEMENT_METERS.
        if approach_displacement < MIN_APPROACH_DISPLACEMENT_METERS:
            # Raise PredictionContractError with the text 'The vehicle did not move enough to estimate an
            # approach...' to stop this execution path.
            raise PredictionContractError(
                "The vehicle did not move enough to estimate an "
                "approach direction."
            )

        # Set longitudinal_axis to approach_vector divided by approach_displacement.
        longitudinal_axis = approach_vector / approach_displacement
        # Set lateral_axis to the result of np.asarray(a list containing the negative of longitudinal_axis at 1,
        # longitudinal_axis at 0).
        lateral_axis = np.asarray(
            # Supply a list containing the negative of longitudinal_axis at 1, longitudinal_axis at 0 to
            # np.asarray.
            [-longitudinal_axis[1], longitudinal_axis[0]],
            # Supply dtype as np.float64.
            dtype=np.float64,
        )

        # Set velocity to the result of np.diff(positions) divided by dt.
        velocity = np.diff(positions, axis=0) / dt
        # Set acceleration to the result of np.diff(velocity) divided by dt.
        acceleration = np.diff(velocity, axis=0) / dt
        # Set aligned_velocity to velocity sliced by 1:.
        aligned_velocity = velocity[1:]

        # Set features to the result of np.column_stack(a tuple containing the result of
        # np.linalg.norm(aligned_velocity), the result of...).
        features = np.column_stack(
            # Supply a tuple containing the result of np.linalg.norm(aligned_velocity), the result of
            # np.linalg.norm(acceleration),... to np.column_stack.
            (
                # Supply axis as 1.
                np.linalg.norm(aligned_velocity, axis=1),
                # Supply axis as 1.
                np.linalg.norm(acceleration, axis=1),
                # Include aligned_velocity matrix-multiplied by longitudinal_axis in this tuple.
                aligned_velocity @ longitudinal_axis,
                # Include aligned_velocity matrix-multiplied by lateral_axis in this tuple.
                aligned_velocity @ lateral_axis,
                # Include acceleration matrix-multiplied by longitudinal_axis in this tuple.
                acceleration @ longitudinal_axis,
                # Include acceleration matrix-multiplied by lateral_axis in this tuple.
                acceleration @ lateral_axis,
            )
        )

        # Run this branch when features.shape differs from a tuple containing 48, 6.
        if features.shape != (48, 6):
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                # Supply formatted text built from the embedded values to PredictionContractError.
                f"Expected causal feature shape (48, 6); got "
                # Evaluate {features.shape} as part of the enclosing expression.
                f"{features.shape}."
            )
        # Run this branch when the negation of the result of np.all(whether features contains finite numeric
        # values).
        if not np.all(np.isfinite(features)):
            # Raise PredictionContractError with the text 'Causal features contain NaN or infinite values.' to
            # stop this execution path.
            raise PredictionContractError(
                "Causal features contain NaN or infinite values."
            )
        # Return the result of features.astype(np.float32) to the caller.
        return features.astype(np.float32)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Scale using the inputs and processing steps below.
    # Input features: the supplied features.
    # Input mean: the supplied mean.
    # Input standard_deviation: the supplied standard deviation.
    # Output: the result of scaled[np.newaxis, ...].astype(np.float32).
    # Processing: select branches using the stated conditions.
    def _scale(features, mean, standard_deviation):
        # Set scaled to features minus mean divided by standard_deviation.
        scaled = (features - mean) / standard_deviation
        # Run this branch when the negation of the result of np.all(whether scaled contains finite numeric
        # values).
        if not np.all(np.isfinite(scaled)):
            # Raise PredictionContractError with the text 'Scaled features contain NaN or infinite values.' to
            # stop this execution path.
            raise PredictionContractError(
                "Scaled features contain NaN or infinite values."
            )
        # Return the result of scaled[np.newaxis, ...].astype(np.float32) to the caller.
        return scaled[np.newaxis, ...].astype(np.float32)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Probability record using the inputs and processing steps below.
    # Input probabilities: the supplied probabilities.
    # Input threshold: the supplied threshold.
    # Output: a dictionary containing probabilities, predicted_class, label, confidence, threshold, accepted.
    # Processing: select branches using the stated conditions.
    def _probability_record(probabilities, threshold):
        # Set vector to the result of np.asarray(probabilities).
        vector = np.asarray(probabilities, dtype=np.float64)
        # Run this branch when vector.shape differs from a tuple containing 3 or the negation of the result of
        # np.all(whether vector contains finite numeric values).
        if vector.shape != (3,) or not np.all(np.isfinite(vector)):
            # Raise PredictionContractError with formatted text built from the embedded values to stop this
            # execution path.
            raise PredictionContractError(
                # Supply formatted text built from the embedded values to PredictionContractError.
                f"Invalid model output shape or values: {vector}."
            )

        # Set total to a floating-point number built from the result of vector.sum().
        total = float(vector.sum())
        # Run this branch when total is at most 0.0.
        if total <= 0.0:
            # Raise PredictionContractError with the text 'Model probability sum is not positive.' to stop this
            # execution path.
            raise PredictionContractError(
                "Model probability sum is not positive."
            )
        # Set vector to vector divided by total.
        vector = vector / total

        # Set class_index to an integer built from the result of np.argmax(vector).
        class_index = int(np.argmax(vector))
        # Set confidence to a floating-point number built from vector at class_index.
        confidence = float(vector[class_index])
        # Set accepted to confidence is at least threshold.
        accepted = confidence >= threshold
        # Set label to CLASS_LABELS at class_index when accepted, otherwise UNKNOWN_LABEL.
        label = CLASS_LABELS[class_index] if accepted else UNKNOWN_LABEL

        # Return a dictionary containing probabilities, predicted_class, label, confidence, threshold, accepted to
        # the caller.
        return {
            # Store a dictionary of class_label mapped to a floating-point number built from vector at index for
            # (index, class_label) in index/value pairs from CLASS_LABELS under 'probabilities'.
            "probabilities": {
                # Evaluate a floating-point number built from vector at index as part of the enclosing expression.
                class_label: float(vector[index])
                # Evaluate index/value pairs from CLASS_LABELS as part of the enclosing expression.
                for index, class_label in enumerate(CLASS_LABELS)
            },
            # Store CLASS_LABELS at class_index under 'predicted_class'.
            "predicted_class": CLASS_LABELS[class_index],
            # Store label under 'label'.
            "label": label,
            # Store confidence under 'confidence'.
            "confidence": confidence,
            # Store a floating-point number built from threshold under 'threshold'.
            "threshold": float(threshold),
            # Store a Boolean built from accepted under 'accepted'.
            "accepted": bool(accepted),
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Fuse chronologically separate stage results conservatively.
    # Input primary: the supplied primary.
    # Input secondary: the supplied secondary.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def fuse_stage_results(primary, secondary):
        """Fuse chronologically separate stage results conservatively."""
        # Run this branch when primary is the same object as None and secondary is the same object as None.
        if primary is None and secondary is None:
            # Return a tuple containing UNKNOWN_LABEL, the text 'BOTH_STAGES_MISSING' to the caller.
            return UNKNOWN_LABEL, "BOTH_STAGES_MISSING"
        # Run this branch when primary is the same object as None.
        if primary is None:
            # Return a tuple containing UNKNOWN_LABEL, the text 'PRIMARY_MISSING' to the caller.
            return UNKNOWN_LABEL, "PRIMARY_MISSING"
        # Run this branch when secondary is the same object as None.
        if secondary is None:
            # Return a tuple containing UNKNOWN_LABEL, the text 'SECONDARY_MISSING' to the caller.
            return UNKNOWN_LABEL, "SECONDARY_MISSING"

        # Run this branch when primary at 'accepted' and secondary at 'accepted'.
        if primary["accepted"] and secondary["accepted"]:
            # Run this branch when primary at 'label' equals secondary at 'label'.
            if primary["label"] == secondary["label"]:
                # Return a tuple containing primary at 'label', the text 'CONFIRMED_AGREEMENT' to the caller.
                return (
                    # Include primary at 'label' in this tuple.
                    primary["label"],
                    "CONFIRMED_AGREEMENT",
                )
            # Return a tuple containing UNKNOWN_LABEL, the text 'HORIZON_DISAGREEMENT' to the caller.
            return UNKNOWN_LABEL, "HORIZON_DISAGREEMENT"

        # Run this branch when the negation of primary at 'accepted' and secondary at 'accepted'.
        if not primary["accepted"] and secondary["accepted"]:
            # Return a tuple containing secondary at 'label', the text 'SECONDARY_RECOVERY' to the caller.
            return secondary["label"], "SECONDARY_RECOVERY"

        # Run this branch when primary at 'accepted' and the negation of secondary at 'accepted'.
        if primary["accepted"] and not secondary["accepted"]:
            # Return a tuple containing UNKNOWN_LABEL, the text 'SECONDARY_UNCERTAIN' to the caller.
            return UNKNOWN_LABEL, "SECONDARY_UNCERTAIN"

        # Return a tuple containing UNKNOWN_LABEL, the text 'BOTH_UNCERTAIN' to the caller.
        return UNKNOWN_LABEL, "BOTH_UNCERTAIN"

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Feature diagnostics using the inputs and processing steps below.
    # Input features: the supplied features.
    # Input scaled_features: the supplied scaled features.
    # Output: a dictionary containing maximum_absolute_z_score, raw_feature_means,
    # maximum_absolute_z_score_by_feature.
    def _feature_diagnostics(features, scaled_features):
        # Return a dictionary containing maximum_absolute_z_score, raw_feature_means,
        # maximum_absolute_z_score_by_feature to the caller.
        return {
            # Store a floating-point number built from the result of np.max(the result of np.abs(scaled_features))
            # under 'maximum_absolute_z_score'.
            "maximum_absolute_z_score": float(
                # Supply the result of np.max(the result of np.abs(scaled_features)) to float.
                np.max(np.abs(scaled_features))
            ),
            # Store a dictionary of name mapped to a floating-point number built from the result of features[:,
            # index].mean() for (index, name) in index/value pairs from FEATURE_DIAGNOSTIC_NAMES under
            # 'raw_feature_means'.
            "raw_feature_means": {
                # Evaluate a floating-point number built from the result of features[:, index].mean() as part of
                # the enclosing expression.
                name: float(features[:, index].mean())
                # Evaluate index/value pairs from FEATURE_DIAGNOSTIC_NAMES as part of the enclosing expression.
                for index, name in enumerate(FEATURE_DIAGNOSTIC_NAMES)
            },
            # Store a dictionary of name mapped to a floating-point number built from the result of np.max(the
            # result of np.abs(scaled_features[:, index])) for (index, name) in index/value pairs from
            # FEATURE_DIAGNOSTIC_NAMES under 'maximum_absolute_z_score_by_feature'.
            "maximum_absolute_z_score_by_feature": {
                # Evaluate a floating-point number built from the result of np.max(the result of
                # np.abs(scaled_features at (:, index))) as part of the enclosing expression.
                name: float(
                    # Supply the result of np.max(the result of np.abs(scaled_features at (:, index))) to float.
                    np.max(np.abs(scaled_features[:, index]))
                )
                # Evaluate index/value pairs from FEATURE_DIAGNOSTIC_NAMES as part of the enclosing expression.
                for index, name in enumerate(FEATURE_DIAGNOSTIC_NAMES)
            },
        }

    # Run exactly one model at its own temporal trigger.
    # Input position_history: the supplied position history.
    # Input stage: the supplied stage.
    # Output: result.
    # Processing: select branches using the stated conditions.
    def predict_stage(self, position_history, stage):
        """Run exactly one model at its own temporal trigger."""
        # Set features to the result of self.build_causal_features(position_history).
        features = self.build_causal_features(position_history)

        # Run this branch when stage equals the text 'primary'.
        if stage == "primary":
            # Set mean to self.primary_mean.
            mean = self.primary_mean
            # Set standard_deviation to self.primary_standard_deviation.
            standard_deviation = self.primary_standard_deviation
            # Set session to self.primary_session.
            session = self.primary_session
            # Set input_name to self.primary_input_name.
            input_name = self.primary_input_name
            # Set output_name to self.primary_output_name.
            output_name = self.primary_output_name
            # Set threshold to self.primary_threshold.
            threshold = self.primary_threshold
            # Set lead_time_seconds to PRIMARY_PREDICTION_LEAD_TIME_SECONDS.
            lead_time_seconds = (
                # Evaluate PRIMARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing expression.
                PRIMARY_PREDICTION_LEAD_TIME_SECONDS
            )
        # Run this branch when stage equals the text 'secondary'.
        elif stage == "secondary":
            # Set mean to self.secondary_mean.
            mean = self.secondary_mean
            # Set standard_deviation to self.secondary_standard_deviation.
            standard_deviation = self.secondary_standard_deviation
            # Set session to self.secondary_session.
            session = self.secondary_session
            # Set input_name to self.secondary_input_name.
            input_name = self.secondary_input_name
            # Set output_name to self.secondary_output_name.
            output_name = self.secondary_output_name
            # Set threshold to self.secondary_threshold.
            threshold = self.secondary_threshold
            # Set lead_time_seconds to SECONDARY_PREDICTION_LEAD_TIME_SECONDS.
            lead_time_seconds = (
                # Evaluate SECONDARY_PREDICTION_LEAD_TIME_SECONDS as part of the enclosing expression.
                SECONDARY_PREDICTION_LEAD_TIME_SECONDS
            )
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Raise ValueError with the text "stage must be either 'primary' or 'secondary'" to stop this
            # execution path.
            raise ValueError(
                "stage must be either 'primary' or 'secondary'"
            )

        # Set model_input to the result of self._scale(features, mean, standard_deviation).
        model_input = self._scale(
            # Supply features to self._scale.
            features,
            # Supply mean to self._scale.
            mean,
            # Supply standard_deviation to self._scale.
            standard_deviation,
        )
        # Set probabilities to session.run([output_name], {input_name: model_input})[0] at 0.
        probabilities = session.run(
            # Supply a list containing output_name to session.run.
            [output_name],
            # Store model_input under input_name.
            {input_name: model_input},
        # Supply 0 to the enclosing expression.
        )[0][0]
        # Set result to the result of self._probability_record(probabilities, threshold).
        result = self._probability_record(
            # Supply probabilities to self._probability_record.
            probabilities,
            # Supply threshold to self._probability_record.
            threshold,
        )
        # Update result with the supplied entries.
        result.update(
            # Supply a dictionary containing stage, lead_time_seconds, feature_diagnostics to result.update.
            {
                # Store stage under 'stage'.
                "stage": stage,
                # Store lead_time_seconds under 'lead_time_seconds'.
                "lead_time_seconds": lead_time_seconds,
                # Store the result of self._feature_diagnostics(features, model_input at 0) under
                # 'feature_diagnostics'.
                "feature_diagnostics": self._feature_diagnostics(
                    # Supply features to self._feature_diagnostics.
                    features,
                    # Supply model_input at 0 to self._feature_diagnostics.
                    model_input[0],
                ),
            }
        )
        # Return result to the caller.
        return result
