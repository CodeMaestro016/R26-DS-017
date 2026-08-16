"""
Monte Carlo Dropout Uncertainty Estimator.

Final proposed model:
    Reliability-only Transformer

Input shape:
    (batch, 30, 525)

Uncertainty outputs:
    - Mean class probabilities
    - Confidence
    - Predictive entropy
    - Normalized predictive entropy
    - Expected entropy
    - Mutual information
    - Crossing probability variance
    - Variation ratio
"""

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from models.transformer_intent_model import (
    TransformerIntentModel
)


class MCDropoutUncertaintyEstimator:

    def __init__(
        self,
        checkpoint_path=(
            "outputs/phase5/"
            "reliability_only_transformer_best.pt"
        ),
        device=None,
        number_of_samples=30,
        random_seed=42
    ):

        if number_of_samples < 2:
            raise ValueError(
                "number_of_samples must be at least 2."
            )

        self.checkpoint_path = Path(
            checkpoint_path
        )

        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found: "
                f"{self.checkpoint_path}"
            )

        self.device = torch.device(
            device
            if device is not None
            else (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        self.number_of_samples = int(
            number_of_samples
        )

        self.random_seed = int(
            random_seed
        )

        self.epsilon = 1e-8

        self.checkpoint = (
            self._load_checkpoint()
        )

        self.model = self._create_model()

        self.feature_mean = (
            self._checkpoint_tensor_to_numpy(
                self.checkpoint["feature_mean"]
            )
        )

        self.feature_standard_deviation = (
            self._checkpoint_tensor_to_numpy(
                self.checkpoint[
                    "feature_standard_deviation"
                ]
            )
        )

        self.input_dimension = int(
            self.checkpoint[
                "input_dimension"
            ]
        )

        self.sequence_length = int(
            self.checkpoint[
                "sequence_length"
            ]
        )

        self.num_classes = int(
            self.checkpoint[
                "num_classes"
            ]
        )

        self.class_names = (
            self.checkpoint.get(
                "class_names",
                [
                    "not-crossing",
                    "crossing"
                ]
            )
        )

        if (
            len(self.feature_mean)
            != self.input_dimension
        ):
            raise ValueError(
                "Checkpoint normalization mean "
                "dimension does not match "
                "model input dimension."
            )

        if (
            len(
                self.feature_standard_deviation
            )
            != self.input_dimension
        ):
            raise ValueError(
                "Checkpoint normalization standard "
                "deviation dimension does not match "
                "model input dimension."
            )

    def _load_checkpoint(self):

        try:

            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=False
            )

        except TypeError:

            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device
            )

        required_keys = [
            "model_state_dict",
            "input_dimension",
            "sequence_length",
            "num_classes",
            "model_configuration",
            "feature_mean",
            "feature_standard_deviation"
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in checkpoint
        ]

        if missing_keys:
            raise KeyError(
                "Missing checkpoint keys: "
                f"{missing_keys}"
            )

        return checkpoint

    @staticmethod
    def _checkpoint_tensor_to_numpy(
        value
    ):

        if isinstance(value, torch.Tensor):

            value = (
                value
                .detach()
                .cpu()
                .numpy()
            )

        return np.asarray(
            value,
            dtype=np.float32
        ).reshape(-1)

    def _create_model(self):

        configuration = self.checkpoint[
            "model_configuration"
        ]

        model = TransformerIntentModel(
            input_dim=int(
                self.checkpoint[
                    "input_dimension"
                ]
            ),

            sequence_length=int(
                self.checkpoint[
                    "sequence_length"
                ]
            ),

            num_classes=int(
                self.checkpoint[
                    "num_classes"
                ]
            ),

            d_model=int(
                configuration["d_model"]
            ),

            num_heads=int(
                configuration["num_heads"]
            ),

            num_layers=int(
                configuration["num_layers"]
            ),

            dim_feedforward=int(
                configuration[
                    "dim_feedforward"
                ]
            ),

            dropout=float(
                configuration["dropout"]
            )
        )

        model.load_state_dict(
            self.checkpoint[
                "model_state_dict"
            ]
        )

        model.to(
            self.device
        )

        model.eval()

        return model

    def _validate_features(
        self,
        features
    ):

        features = np.asarray(
            features,
            dtype=np.float32
        )

        if features.ndim == 2:

            features = np.expand_dims(
                features,
                axis=0
            )

        if features.ndim != 3:

            raise ValueError(
                "Expected features with shape "
                "(batch, sequence, dimension) "
                "or (sequence, dimension). "
                f"Received {features.shape}."
            )

        if (
            features.shape[1]
            != self.sequence_length
        ):

            raise ValueError(
                f"Expected sequence length "
                f"{self.sequence_length}, "
                f"received {features.shape[1]}."
            )

        if (
            features.shape[2]
            != self.input_dimension
        ):

            raise ValueError(
                f"Expected input dimension "
                f"{self.input_dimension}, "
                f"received {features.shape[2]}."
            )

        if not np.isfinite(
            features
        ).all():

            raise ValueError(
                "NaN or infinite values were "
                "detected in input features."
            )

        return features

    def _normalize_features(
        self,
        features
    ):

        mean = self.feature_mean.reshape(
            1,
            1,
            -1
        )

        standard_deviation = (
            self.feature_standard_deviation
            .reshape(
                1,
                1,
                -1
            )
        )

        normalized = (
            features - mean
        ) / standard_deviation

        return normalized.astype(
            np.float32,
            copy=False
        )

    def _enable_mc_dropout(self):
        """
        Keep the full model in evaluation mode,
        but activate stochastic Dropout and
        MultiheadAttention dropout.
        """

        self.model.eval()

        dropout_types = (
            nn.Dropout,
            nn.Dropout1d,
            nn.Dropout2d,
            nn.Dropout3d,
            nn.AlphaDropout
        )

        activated_modules = 0

        for module in self.model.modules():

            if isinstance(
                module,
                dropout_types
            ):

                module.train()
                activated_modules += 1

            elif isinstance(
                module,
                nn.MultiheadAttention
            ):

                module.train()
                activated_modules += 1

        if activated_modules == 0:

            raise RuntimeError(
                "No stochastic dropout-related "
                "modules were activated."
            )

        return activated_modules

    def _deterministic_prediction(
        self,
        input_tensor
    ):

        self.model.eval()

        with torch.no_grad():

            logits = self.model(
                input_tensor
            )

            probabilities = torch.softmax(
                logits,
                dim=1
            )

        return (
            probabilities
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

    def _mc_predictions(
        self,
        input_tensor,
        number_of_samples
    ):

        torch.manual_seed(
            self.random_seed
        )

        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(
                self.random_seed
            )

        activated_modules = (
            self._enable_mc_dropout()
        )

        probability_samples = []

        with torch.no_grad():

            for _ in range(
                number_of_samples
            ):

                logits = self.model(
                    input_tensor
                )

                probabilities = torch.softmax(
                    logits,
                    dim=1
                )

                probability_samples.append(
                    probabilities
                    .detach()
                    .cpu()
                    .numpy()
                )

        self.model.eval()

        probability_samples = np.stack(
            probability_samples,
            axis=0
        ).astype(
            np.float32
        )

        return (
            probability_samples,
            activated_modules
        )

    def estimate_batch(
        self,
        features,
        number_of_samples=None,
        return_samples=False
    ):

        features = self._validate_features(
            features
        )

        normalized_features = (
            self._normalize_features(
                features
            )
        )

        input_tensor = torch.from_numpy(
            np.ascontiguousarray(
                normalized_features,
                dtype=np.float32
            )
        ).to(
            self.device
        )

        if number_of_samples is None:
            number_of_samples = (
                self.number_of_samples
            )

        number_of_samples = int(
            number_of_samples
        )

        if number_of_samples < 2:
            raise ValueError(
                "number_of_samples must be "
                "at least 2."
            )

        deterministic_probabilities = (
            self._deterministic_prediction(
                input_tensor
            )
        )

        (
            probability_samples,
            activated_modules
        ) = self._mc_predictions(
            input_tensor=input_tensor,
            number_of_samples=
                number_of_samples
        )

        # Shape:
        # (MC samples, batch, classes)
        mean_probabilities = np.mean(
            probability_samples,
            axis=0
        )

        probability_variances = np.var(
            probability_samples,
            axis=0
        )

        probability_standard_deviations = (
            np.std(
                probability_samples,
                axis=0
            )
        )

        predicted_class_ids = np.argmax(
            mean_probabilities,
            axis=1
        ).astype(
            np.int64
        )

        confidence = np.max(
            mean_probabilities,
            axis=1
        )

        clipped_mean = np.clip(
            mean_probabilities,
            self.epsilon,
            1.0
        )

        predictive_entropy = -np.sum(
            clipped_mean
            * np.log(
                clipped_mean
            ),
            axis=1
        )

        normalized_predictive_entropy = (
            predictive_entropy
            / np.log(
                float(self.num_classes)
            )
        )

        clipped_samples = np.clip(
            probability_samples,
            self.epsilon,
            1.0
        )

        sample_entropies = -np.sum(
            clipped_samples
            * np.log(
                clipped_samples
            ),
            axis=2
        )

        expected_entropy = np.mean(
            sample_entropies,
            axis=0
        )

        mutual_information = (
            predictive_entropy
            - expected_entropy
        )

        mutual_information = np.clip(
            mutual_information,
            0.0,
            None
        )

        sample_class_predictions = (
            np.argmax(
                probability_samples,
                axis=2
            )
        )

        variation_ratios = []

        for batch_index in range(
            features.shape[0]
        ):

            class_counts = np.bincount(
                sample_class_predictions[
                    :,
                    batch_index
                ],
                minlength=self.num_classes
            )

            modal_count = np.max(
                class_counts
            )

            variation_ratio = (
                1.0
                - (
                    modal_count
                    / number_of_samples
                )
            )

            variation_ratios.append(
                variation_ratio
            )

        variation_ratios = np.asarray(
            variation_ratios,
            dtype=np.float32
        )

        crossing_probability_samples = (
            probability_samples[
                :,
                :,
                1
            ]
        )

        results = {
            "number_of_samples":
                number_of_samples,

            "activated_stochastic_modules":
                activated_modules,

            "deterministic_probabilities":
                deterministic_probabilities,

            "mean_probabilities":
                mean_probabilities.astype(
                    np.float32
                ),

            "probability_variances":
                probability_variances.astype(
                    np.float32
                ),

            "probability_standard_deviations":
                probability_standard_deviations
                .astype(
                    np.float32
                ),

            "predicted_class_ids":
                predicted_class_ids,

            "predicted_class_names":
                np.asarray(
                    [
                        self.class_names[
                            class_id
                        ]
                        for class_id
                        in predicted_class_ids
                    ],
                    dtype=object
                ),

            "confidence":
                confidence.astype(
                    np.float32
                ),

            "predictive_entropy":
                predictive_entropy.astype(
                    np.float32
                ),

            "normalized_predictive_entropy":
                normalized_predictive_entropy
                .astype(
                    np.float32
                ),

            "expected_entropy":
                expected_entropy.astype(
                    np.float32
                ),

            "mutual_information":
                mutual_information.astype(
                    np.float32
                ),

            "variation_ratio":
                variation_ratios,

            "crossing_probability_mean":
                np.mean(
                    crossing_probability_samples,
                    axis=0
                ).astype(
                    np.float32
                ),

            "crossing_probability_variance":
                np.var(
                    crossing_probability_samples,
                    axis=0
                ).astype(
                    np.float32
                ),

            "crossing_probability_std":
                np.std(
                    crossing_probability_samples,
                    axis=0
                ).astype(
                    np.float32
                ),

            "crossing_probability_min":
                np.min(
                    crossing_probability_samples,
                    axis=0
                ).astype(
                    np.float32
                ),

            "crossing_probability_max":
                np.max(
                    crossing_probability_samples,
                    axis=0
                ).astype(
                    np.float32
                )
        }

        if return_samples:

            results[
                "probability_samples"
            ] = probability_samples

        return results

    def estimate_single(
        self,
        feature_sequence,
        number_of_samples=None,
        return_samples=True
    ):

        results = self.estimate_batch(
            features=feature_sequence,
            number_of_samples=
                number_of_samples,
            return_samples=
                return_samples
        )

        single_result = {
            "number_of_samples":
                results[
                    "number_of_samples"
                ],

            "activated_stochastic_modules":
                results[
                    "activated_stochastic_modules"
                ],

            "deterministic_probabilities":
                results[
                    "deterministic_probabilities"
                ][0],

            "mean_probabilities":
                results[
                    "mean_probabilities"
                ][0],

            "probability_variances":
                results[
                    "probability_variances"
                ][0],

            "probability_standard_deviations":
                results[
                    "probability_standard_deviations"
                ][0],

            "predicted_class_id":
                int(
                    results[
                        "predicted_class_ids"
                    ][0]
                ),

            "predicted_class_name":
                str(
                    results[
                        "predicted_class_names"
                    ][0]
                ),

            "confidence":
                float(
                    results["confidence"][0]
                ),

            "predictive_entropy":
                float(
                    results[
                        "predictive_entropy"
                    ][0]
                ),

            "normalized_predictive_entropy":
                float(
                    results[
                        "normalized_predictive_entropy"
                    ][0]
                ),

            "expected_entropy":
                float(
                    results[
                        "expected_entropy"
                    ][0]
                ),

            "mutual_information":
                float(
                    results[
                        "mutual_information"
                    ][0]
                ),

            "variation_ratio":
                float(
                    results[
                        "variation_ratio"
                    ][0]
                ),

            "crossing_probability_mean":
                float(
                    results[
                        "crossing_probability_mean"
                    ][0]
                ),

            "crossing_probability_variance":
                float(
                    results[
                        "crossing_probability_variance"
                    ][0]
                ),

            "crossing_probability_std":
                float(
                    results[
                        "crossing_probability_std"
                    ][0]
                ),

            "crossing_probability_min":
                float(
                    results[
                        "crossing_probability_min"
                    ][0]
                ),

            "crossing_probability_max":
                float(
                    results[
                        "crossing_probability_max"
                    ][0]
                )
        }

        if return_samples:

            single_result[
                "probability_samples"
            ] = results[
                "probability_samples"
            ][
                :,
                0,
                :
            ]

        return single_result