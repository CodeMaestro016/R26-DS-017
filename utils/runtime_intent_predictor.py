"""
Runtime Intent Predictor.

Loads the frozen final deployment configuration:

- Reliability-only Transformer
- Temperature scaling
- Validation-derived decision threshold
- MC Dropout configuration

Input:
    (30, 525)

Output:
    crossing / not-crossing prediction
    calibrated probability
    confidence
    predictive entropy
    mutual information
    probability variance
"""

from pathlib import Path
import json
import math

import numpy as np

from utils.uncertainty_estimator import (
    MCDropoutUncertaintyEstimator
)


class RuntimeIntentPredictor:

    CLASS_NAMES = {
        0: "not-crossing",
        1: "crossing"
    }

    def __init__(
        self,
        deployment_config_path=(
            "outputs/phase6/final_test/"
            "uncertainty_deployment_config.json"
        ),
        device=None,
        random_seed=42
    ):
        self.deployment_config_path = Path(
            deployment_config_path
        )

        if not self.deployment_config_path.exists():
            raise FileNotFoundError(
                "Deployment configuration not found: "
                f"{self.deployment_config_path}"
            )

        self.config = self._load_config()

        self.temperature = float(
            self.config["temperature"]
        )

        self.decision_threshold = float(
            self.config["decision_threshold"]
        )

        self.mc_samples = int(
            self.config["mc_samples"]
        )

        self.input_dimension = int(
            self.config.get(
                "input_dimension",
                525
            )
        )

        self.sequence_length = int(
            self.config.get(
                "sequence_length",
                30
            )
        )

        self.random_seed = int(
            random_seed
        )

        checkpoint_path = self.config[
            "checkpoint"
        ]

        self.estimator = (
            MCDropoutUncertaintyEstimator(
                checkpoint_path=checkpoint_path,
                device=device,
                number_of_samples=
                    self.mc_samples,
                random_seed=
                    self.random_seed
            )
        )

        if (
            self.estimator.input_dimension
            != self.input_dimension
        ):
            raise ValueError(
                "Deployment configuration and "
                "checkpoint input dimensions do not match."
            )

        if (
            self.estimator.sequence_length
            != self.sequence_length
        ):
            raise ValueError(
                "Deployment configuration and "
                "checkpoint sequence lengths do not match."
            )

    def _load_config(self):

        with open(
            self.deployment_config_path,
            "r",
            encoding="utf-8"
        ) as input_file:

            config = json.load(
                input_file
            )

        required_keys = [
            "checkpoint",
            "temperature",
            "mc_samples",
            "decision_threshold"
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in config
        ]

        if missing_keys:
            raise KeyError(
                "Missing deployment configuration "
                f"keys: {missing_keys}"
            )

        temperature = float(
            config["temperature"]
        )

        if (
            not math.isfinite(temperature)
            or temperature <= 0
        ):
            raise ValueError(
                f"Invalid temperature: {temperature}"
            )

        return config

    @staticmethod
    def _stable_sigmoid(values):

        values = np.asarray(
            values,
            dtype=np.float64
        )

        result = np.empty_like(
            values
        )

        positive_mask = values >= 0

        result[positive_mask] = (
            1.0
            / (
                1.0
                + np.exp(
                    -values[positive_mask]
                )
            )
        )

        negative_exp = np.exp(
            values[~positive_mask]
        )

        result[~positive_mask] = (
            negative_exp
            / (
                1.0
                + negative_exp
            )
        )

        return result

    def _apply_temperature(
        self,
        probability_samples
    ):
        """
        Convert binary probabilities to log-odds,
        divide by temperature and convert back.
        """

        probability_samples = np.asarray(
            probability_samples,
            dtype=np.float64
        )

        if (
            probability_samples.ndim != 2
            or probability_samples.shape[1] != 2
        ):
            raise ValueError(
                "Expected MC probability samples "
                "with shape (samples, 2)."
            )

        epsilon = 1e-7

        crossing_probability = np.clip(
            probability_samples[:, 1],
            epsilon,
            1.0 - epsilon
        )

        log_odds = (
            np.log(
                crossing_probability
            )
            - np.log1p(
                -crossing_probability
            )
        )

        calibrated_crossing = (
            self._stable_sigmoid(
                log_odds
                / self.temperature
            )
        )

        calibrated_probabilities = np.column_stack(
            [
                1.0 - calibrated_crossing,
                calibrated_crossing
            ]
        )

        return calibrated_probabilities.astype(
            np.float32
        )

    @staticmethod
    def _entropy(probabilities):

        probabilities = np.clip(
            probabilities,
            1e-8,
            1.0
        )

        return float(
            -np.sum(
                probabilities
                * np.log(
                    probabilities
                )
            )
        )

    def _validate_sequence(
        self,
        feature_sequence
    ):

        feature_sequence = np.asarray(
            feature_sequence,
            dtype=np.float32
        )

        expected_shape = (
            self.sequence_length,
            self.input_dimension
        )

        if feature_sequence.shape != expected_shape:
            raise ValueError(
                f"Expected runtime input shape "
                f"{expected_shape}, but received "
                f"{feature_sequence.shape}."
            )

        if not np.isfinite(
            feature_sequence
        ).all():
            raise ValueError(
                "Runtime sequence contains NaN "
                "or infinite values."
            )

        return feature_sequence

    def predict(
        self,
        feature_sequence,
        random_seed=None
    ):

        feature_sequence = (
            self._validate_sequence(
                feature_sequence
            )
        )

        if random_seed is None:
            random_seed = self.random_seed

        self.estimator.random_seed = int(
            random_seed
        )

        uncertainty_result = (
            self.estimator.estimate_single(
                feature_sequence=
                    feature_sequence,

                number_of_samples=
                    self.mc_samples,

                return_samples=True
            )
        )

        calibrated_samples = (
            self._apply_temperature(
                uncertainty_result[
                    "probability_samples"
                ]
            )
        )

        mean_probabilities = np.mean(
            calibrated_samples,
            axis=0
        )

        crossing_probability = float(
            mean_probabilities[1]
        )

        predicted_class_id = int(
            crossing_probability
            >= self.decision_threshold
        )

        predicted_class_name = (
            self.CLASS_NAMES[
                predicted_class_id
            ]
        )

        confidence = float(
            mean_probabilities[
                predicted_class_id
            ]
        )

        predictive_entropy = (
            self._entropy(
                mean_probabilities
            )
        )

        normalized_entropy = float(
            predictive_entropy
            / np.log(2.0)
        )

        sample_entropies = np.asarray(
            [
                self._entropy(sample)
                for sample
                in calibrated_samples
            ],
            dtype=np.float32
        )

        expected_entropy = float(
            np.mean(
                sample_entropies
            )
        )

        mutual_information = float(
            max(
                predictive_entropy
                - expected_entropy,
                0.0
            )
        )

        crossing_samples = (
            calibrated_samples[:, 1]
        )

        return {
            "predicted_class_id":
                predicted_class_id,

            "predicted_intent":
                predicted_class_name,

            "not_crossing_probability":
                float(
                    mean_probabilities[0]
                ),

            "crossing_probability":
                crossing_probability,

            "decision_threshold":
                self.decision_threshold,

            "confidence":
                confidence,

            "predictive_entropy":
                predictive_entropy,

            "normalized_entropy":
                normalized_entropy,

            "expected_entropy":
                expected_entropy,

            "mutual_information":
                mutual_information,

            "crossing_probability_variance":
                float(
                    np.var(
                        crossing_samples
                    )
                ),

            "crossing_probability_std":
                float(
                    np.std(
                        crossing_samples
                    )
                ),

            "crossing_probability_min":
                float(
                    np.min(
                        crossing_samples
                    )
                ),

            "crossing_probability_max":
                float(
                    np.max(
                        crossing_samples
                    )
                ),

            "temperature":
                self.temperature,

            "mc_samples":
                self.mc_samples
        }