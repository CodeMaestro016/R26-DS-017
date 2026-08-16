"""
Bayesian Semantic Network

Final DAG:

Motion ---------------------\
Horizontal Position ---------> Intention Tendency
Vertical Position ----------/

Occlusion -------------------> Observation Reliability

The network produces five semantic probabilities:

1. P(Intention Tendency = not-crossing)
2. P(Intention Tendency = crossing)
3. P(Observation Reliability = low)
4. P(Observation Reliability = medium)
5. P(Observation Reliability = high)
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from pgmpy.estimators import BayesianEstimator
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork


class BayesianSemanticNetwork:

    NODES = [
        "motion",
        "horizontal",
        "vertical",
        "occlusion",
        "intention_tendency",
        "observation_reliability"
    ]

    EDGES = [
        ("motion", "intention_tendency"),
        ("horizontal", "intention_tendency"),
        ("vertical", "intention_tendency"),

        ("occlusion", "observation_reliability")
    ]

    STATE_NAMES = {
        "motion": [
            "static",
            "walking",
            "fast"
        ],

        "horizontal": [
            "left",
            "center",
            "right"
        ],

        "vertical": [
            "top",
            "middle",
            "bottom"
        ],

        "occlusion": [
            "low",
            "medium",
            "high"
        ],

        "intention_tendency": [
            "not-crossing",
            "crossing"
        ],

        "observation_reliability": [
            "low",
            "medium",
            "high"
        ]
    }

    TRAINING_COLUMNS = [
        "motion",
        "horizontal",
        "vertical",
        "occlusion",
        "intention_tendency",
        "observation_reliability"
    ]

    FEATURE_NAMES = [
        "p_intention_not_crossing",
        "p_intention_crossing",
        "p_reliability_low",
        "p_reliability_medium",
        "p_reliability_high"
    ]

    def __init__(self, model=None):

        self.model = model
        self.inference_engine = None

        if self.model is not None:
            self._initialize_inference()

    def _initialize_inference(self):

        if self.model is None:
            raise RuntimeError(
                "Bayesian model is not available."
            )

        if not self.model.check_model():
            raise ValueError(
                "Invalid Bayesian Network model."
            )

        self.inference_engine = VariableElimination(
            self.model
        )

    @staticmethod
    def _normalize_text_columns(data):

        normalized = data.copy()

        for column in normalized.columns:

            normalized[column] = (
                normalized[column]
                .astype(str)
                .str.strip()
                .str.lower()
            )

        return normalized

    @classmethod
    def _validate_columns(cls, data):

        missing_columns = [
            column
            for column in cls.TRAINING_COLUMNS
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                "Missing Bayesian dataset columns: "
                f"{missing_columns}"
            )

    @classmethod
    def _validate_states(cls, data):

        for variable in cls.TRAINING_COLUMNS:

            observed_states = set(
                data[variable].dropna().unique()
            )

            allowed_states = set(
                cls.STATE_NAMES[variable]
            )

            invalid_states = (
                observed_states - allowed_states
            )

            if invalid_states:
                raise ValueError(
                    f"Invalid states found for "
                    f"'{variable}': {invalid_states}. "
                    f"Allowed states: "
                    f"{cls.STATE_NAMES[variable]}"
                )

    def fit(
        self,
        data,
        equivalent_sample_size=1.0
    ):
        """
        Fit Bayesian CPDs using only the training split.

        Parameters
        ----------
        data:
            Either a pandas DataFrame or a path to
            train_bayesian.csv.

        equivalent_sample_size:
            Strength of the symmetric BDeu prior.
            This is a smoothing hyperparameter,
            not a semantic classification threshold.
        """

        if isinstance(data, (str, Path)):

            data_path = Path(data)

            if not data_path.exists():
                raise FileNotFoundError(
                    f"Bayesian dataset not found: "
                    f"{data_path}"
                )

            data = pd.read_csv(data_path)

        elif not isinstance(data, pd.DataFrame):

            raise TypeError(
                "data must be a pandas DataFrame "
                "or a CSV file path."
            )

        self._validate_columns(data)

        training_data = data[
            self.TRAINING_COLUMNS
        ].copy()

        training_data = (
            self._normalize_text_columns(
                training_data
            )
        )

        self._validate_states(training_data)

        model = DiscreteBayesianNetwork(
            self.EDGES
        )

        model.add_nodes_from(
            self.NODES
        )

        estimator = BayesianEstimator(
            model,
            training_data,
            state_names=self.STATE_NAMES
        )

        fitted_cpds = estimator.get_parameters(
            prior_type="BDeu",
            equivalent_sample_size=float(
                equivalent_sample_size
            ),
            n_jobs=1
        )

        model.add_cpds(*fitted_cpds)

        if not model.check_model():
            raise ValueError(
                "Bayesian Network validation failed "
                "after parameter learning."
            )

        self.model = model
        self._initialize_inference()

        return self

    def save(self, output_path):

        if self.model is None:
            raise RuntimeError(
                "Cannot save an untrained model."
            )

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        joblib.dump(
            self.model,
            output_path
        )

    @classmethod
    def load(cls, model_path):

        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Bayesian model not found: "
                f"{model_path}"
            )

        model = joblib.load(
            model_path
        )

        return cls(model=model)

    @classmethod
    def _validate_evidence_value(
        cls,
        variable,
        value
    ):

        value = str(value).strip().lower()

        allowed_states = cls.STATE_NAMES[
            variable
        ]

        if value not in allowed_states:
            raise ValueError(
                f"Invalid value '{value}' for "
                f"'{variable}'. "
                f"Expected one of {allowed_states}."
            )

        return value

    @staticmethod
    def _factor_to_dictionary(
        factor,
        variable
    ):
        """
        Convert a pgmpy factor into:

        {
            state_name: probability
        }
        """

        states = factor.state_names[
            variable
        ]

        values = np.asarray(
            factor.values,
            dtype=np.float64
        ).reshape(-1)

        return {
            str(state): float(values[index])
            for index, state in enumerate(states)
        }

    def predict(
        self,
        motion,
        horizontal,
        vertical,
        occlusion
    ):
        """
        Perform Bayesian inference using observable
        semantic evidence only.

        The ground-truth intention label is never
        passed to this function.
        """

        if self.inference_engine is None:
            raise RuntimeError(
                "Bayesian model has not been trained "
                "or loaded."
            )

        motion = self._validate_evidence_value(
            "motion",
            motion
        )

        horizontal = self._validate_evidence_value(
            "horizontal",
            horizontal
        )

        vertical = self._validate_evidence_value(
            "vertical",
            vertical
        )

        occlusion = self._validate_evidence_value(
            "occlusion",
            occlusion
        )

        intention_factor = (
            self.inference_engine.query(
                variables=[
                    "intention_tendency"
                ],
                evidence={
                    "motion": motion,
                    "horizontal": horizontal,
                    "vertical": vertical
                },
                joint=True,
                show_progress=False
            )
        )

        reliability_factor = (
            self.inference_engine.query(
                variables=[
                    "observation_reliability"
                ],
                evidence={
                    "occlusion": occlusion
                },
                joint=True,
                show_progress=False
            )
        )

        intention_probabilities = (
            self._factor_to_dictionary(
                intention_factor,
                "intention_tendency"
            )
        )

        reliability_probabilities = (
            self._factor_to_dictionary(
                reliability_factor,
                "observation_reliability"
            )
        )

        feature_vector = np.asarray(
            [
                intention_probabilities[
                    "not-crossing"
                ],

                intention_probabilities[
                    "crossing"
                ],

                reliability_probabilities[
                    "low"
                ],

                reliability_probabilities[
                    "medium"
                ],

                reliability_probabilities[
                    "high"
                ]
            ],
            dtype=np.float32
        )

        return {
            "intention_tendency":
                intention_probabilities,

            "observation_reliability":
                reliability_probabilities,

            "feature_vector":
                feature_vector
        }

    def print_cpds(self):

        if self.model is None:
            raise RuntimeError(
                "Bayesian model is unavailable."
            )

        for cpd in self.model.get_cpds():

            print()
            print("-" * 70)
            print(cpd)