from __future__ import annotations

import dataclasses
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from utils.runtime_intent_predictor import RuntimeIntentPredictor
from utils.situation_explanation_agent import SituationAwareExplanationAgent


@dataclass
class UnifiedRuntimeResult:
    feature_shape: tuple[int, int]
    intent_prediction: str
    p_crossing: float
    confidence: float
    normalized_predictive_entropy: float
    mutual_information: float
    crossing_probability_variance: float
    variation_ratio: float
    decision_margin_uncertainty: float
    observation_reliability_mean: dict[str, float]
    observation_reliability_last: dict[str, float]
    mean_speed: float
    last_speed: float
    agent_action_id: int
    agent_action_name: str
    agent_action_probability: float
    agent_action_probabilities: dict[str, float]
    committed_intent: str
    av_interface_signal: str
    maximum_occlusion: str | None
    dominant_explanation_group: str
    explanation: str
    top_supporting_evidence: list[dict[str, Any]]
    top_opposing_evidence: list[dict[str, Any]]
    agent_state: dict[str, float]
    raw_intent_output: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UnifiedRuntimePipeline:
    """Frozen intent+uncertainty -> learned decision agent -> explanation."""

    SEQUENCE_LENGTH = 30
    FEATURE_DIMENSION = 525

    def __init__(
        self,
        intent_predictor: Any | None = None,
        explanation_agent: SituationAwareExplanationAgent | None = None,
        policy_checkpoint: str | Path = "outputs/phase7/learned_agent_policy_best.pt",
        explanation_steps: int = 32,
    ) -> None:
        self.intent_predictor = intent_predictor or RuntimeIntentPredictor()
        self.explanation_agent = explanation_agent or SituationAwareExplanationAgent(
            policy_checkpoint=policy_checkpoint,
            device="cpu",
            integration_steps=explanation_steps,
        )
        self.agent_state_features = list(self.explanation_agent.state_features)
        self.frozen_threshold = self._load_frozen_threshold()

    @staticmethod
    def _walk_for_key(obj: Any, keys: set[str]) -> float | None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if str(key).lower() in keys:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        pass
            for value in obj.values():
                found = UnifiedRuntimePipeline._walk_for_key(value, keys)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for value in obj:
                found = UnifiedRuntimePipeline._walk_for_key(value, keys)
                if found is not None:
                    return found
        return None

    def _load_frozen_threshold(self) -> float:
        candidates = [
            Path("outputs/phase6/final_test/uncertainty_deployment_config.json"),
            Path("outputs/phase6/uncertainty_deployment_config.json"),
            Path("outputs/phase6/final_test/final_uncertainty_summary.json"),
        ]
        keys = {
            "mc_threshold", "frozen_mc_threshold", "decision_threshold",
            "crossing_threshold", "calibrated_mc_threshold", "threshold",
        }
        for path in candidates:
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                value = self._walk_for_key(payload, keys)
                if value is not None:
                    if not 0.0 < value < 1.0:
                        raise ValueError(f"Invalid frozen threshold {value} in {path}")
                    return float(value)
        raise FileNotFoundError("Could not locate the frozen Phase-6 MC threshold.")

    @staticmethod
    def _validate_sequence(sequence: np.ndarray) -> np.ndarray:
        x = np.asarray(sequence, dtype=np.float32)
        if x.shape != (30, 525):
            raise ValueError(f"Expected runtime sequence shape (30, 525), got {x.shape}")
        if not np.isfinite(x).all():
            raise ValueError("Runtime sequence contains NaN or infinite values.")
        return x

    @staticmethod
    def _to_mapping(result: Any) -> dict[str, Any]:
        if isinstance(result, Mapping):
            return dict(result)
        if dataclasses.is_dataclass(result):
            return dataclasses.asdict(result)
        if hasattr(result, "_asdict"):
            return dict(result._asdict())
        if hasattr(result, "__dict__"):
            return {k: v for k, v in vars(result).items() if not k.startswith("_")}
        raise TypeError(f"Unsupported RuntimeIntentPredictor output: {type(result).__name__}")

    def _call_intent_predictor(self, sequence: np.ndarray) -> dict[str, Any]:
        method = None
        method_name = None
        for name in ("predict", "predict_sequence", "infer", "run"):
            candidate = getattr(self.intent_predictor, name, None)
            if callable(candidate):
                method = candidate
                method_name = name
                break
        if method is None:
            public = [n for n in dir(self.intent_predictor) if not n.startswith("_")]
            raise AttributeError(f"No supported predictor method found. Public attributes: {public}")

        try:
            result = method(sequence)
        except (ValueError, RuntimeError) as first_error:
            try:
                result = method(sequence[np.newaxis, ...])
            except Exception as second_error:
                raise RuntimeError(
                    f"RuntimeIntentPredictor.{method_name} failed for both (30,525) and "
                    f"(1,30,525). First: {first_error}; second: {second_error}"
                ) from second_error
        return self._to_mapping(result)

    @staticmethod
    def _scalar(mapping: Mapping[str, Any], aliases: tuple[str, ...], required: bool = True):
        lookup = {str(k).lower(): k for k in mapping}
        for alias in aliases:
            key = lookup.get(alias.lower())
            if key is None:
                continue
            value = mapping[key]
            if isinstance(value, (list, tuple, np.ndarray)):
                arr = np.asarray(value)
                if arr.size != 1:
                    continue
                value = arr.reshape(-1)[0]
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(value):
                raise ValueError(f"Non-finite runtime output in {key}")
            return value, str(key)
        if required:
            raise KeyError(f"Missing one of {aliases}. Available runtime keys: {list(mapping.keys())}")
        return None, None

    @staticmethod
    def _text(mapping: Mapping[str, Any], aliases: tuple[str, ...]):
        lookup = {str(k).lower(): k for k in mapping}
        for alias in aliases:
            key = lookup.get(alias.lower())
            if key is not None and mapping[key] is not None:
                return str(mapping[key]), str(key)
        return None, None

    @staticmethod
    def _entropy_from_probability(p: float) -> float:
        p = float(np.clip(p, 1e-7, 1.0 - 1e-7))
        h = -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))
        return float(h / math.log(2.0))

    @staticmethod
    def _margin_uncertainty(p: float) -> float:
        return float(np.clip(1.0 - 2.0 * abs(p - 0.5), 0.0, 1.0))

    def _build_agent_state(self, sequence: np.ndarray, output: Mapping[str, Any]):
        p, p_key = self._scalar(output, (
            "calibrated_mc_crossing_probability", "mc_crossing_probability",
            "mc_mean_crossing_probability", "crossing_probability", "p_crossing",
        ))
        confidence, conf_key = self._scalar(output, (
            "confidence", "predictive_confidence", "mc_confidence",
        ), required=False)
        if confidence is None:
            confidence, conf_key = max(p, 1.0 - p), "derived_from_p_crossing"

        entropy, entropy_key = self._scalar(output, (
            "normalized_predictive_entropy", "normalized_entropy",
            "predictive_entropy_normalized",
        ), required=False)
        if entropy is None:
            entropy, entropy_key = self._entropy_from_probability(p), "derived_from_p_crossing"

        mi, mi_key = self._scalar(output, ("mutual_information", "mutual_info", "mi"))
        variance, var_key = self._scalar(output, (
            "crossing_probability_variance", "crossing_variance",
            "probability_variance", "predictive_variance", "variance",
        ))
        variation, variation_key = self._scalar(output, (
            "variation_ratio", "mc_variation_ratio",
        ), required=False)
        if variation is None:
            variation, variation_key = 0.0, "filled_zero"

        margin, margin_key = self._scalar(output, (
            "decision_margin_uncertainty", "decision_margin", "margin_uncertainty",
        ), required=False)
        if margin is None:
            margin, margin_key = self._margin_uncertainty(p), "derived_from_p_crossing"

        reliability = sequence[:, 522:525]
        rel_mean = reliability.mean(axis=0)
        rel_last = reliability[-1]
        speed = sequence[:, 520]

        state = {
            "p_crossing": float(p),
            "confidence": float(confidence),
            "normalized_predictive_entropy": float(entropy),
            "mutual_information": float(mi),
            "crossing_probability_variance": float(variance),
            "variation_ratio": float(variation),
            "decision_margin_uncertainty": float(margin),
            "reliability_low_mean": float(rel_mean[0]),
            "reliability_medium_mean": float(rel_mean[1]),
            "reliability_high_mean": float(rel_mean[2]),
            "reliability_low_last": float(rel_last[0]),
            "reliability_medium_last": float(rel_last[1]),
            "reliability_high_last": float(rel_last[2]),
            "mean_speed": float(speed.mean()),
            "last_speed": float(speed[-1]),
        }
        missing = [name for name in self.agent_state_features if name not in state]
        if missing:
            raise KeyError(f"Unified state missing policy features: {missing}")
        sources = {
            "p_crossing": p_key, "confidence": conf_key,
            "normalized_predictive_entropy": entropy_key,
            "mutual_information": mi_key, "crossing_probability_variance": var_key,
            "variation_ratio": variation_key, "decision_margin_uncertainty": margin_key,
        }
        return state, sources

    def _intent_name(self, output: Mapping[str, Any], p: float) -> str:
        text, _ = self._text(output, (
            "prediction_name", "predicted_intent", "intent_name", "intent",
        ))
        if text is not None:
            normalized = text.strip().upper().replace("-", "_").replace(" ", "_")
            if normalized in {"CROSSING", "NOT_CROSSING"}:
                return normalized

        prediction_id, _ = self._scalar(output, (
            "prediction_id", "predicted_label", "prediction", "y_pred",
        ), required=False)
        if prediction_id is not None:
            return "CROSSING" if int(round(prediction_id)) == 1 else "NOT_CROSSING"
        return "CROSSING" if p >= self.frozen_threshold else "NOT_CROSSING"

    @staticmethod
    def _commitment(action_name: str) -> tuple[str, str]:
        mapping = {
            "COMMIT_CROSSING": ("CROSSING", "CROSSING_INTENT_AVAILABLE"),
            "COMMIT_NOT_CROSSING": ("NOT_CROSSING", "NOT_CROSSING_INTENT_AVAILABLE"),
            "OBSERVE_MORE": ("DEFERRED", "MORE_EVIDENCE_REQUIRED"),
        }
        if action_name not in mapping:
            raise ValueError(f"Unsupported learned-agent action: {action_name}")
        return mapping[action_name]

    def predict(self, sequence: np.ndarray, *, maximum_occlusion: str | None = None) -> UnifiedRuntimeResult:
        x = self._validate_sequence(sequence)
        raw = self._call_intent_predictor(x)
        state, sources = self._build_agent_state(x, raw)
        explanation = self.explanation_agent.explain(
            state,
            maximum_occlusion=maximum_occlusion,
        )
        intent_prediction = self._intent_name(raw, state["p_crossing"])
        committed_intent, av_signal = self._commitment(explanation.action_name)

        serializable_raw = {}
        for key, value in raw.items():
            if isinstance(value, np.generic):
                serializable_raw[str(key)] = value.item()
            elif isinstance(value, np.ndarray):
                serializable_raw[str(key)] = value.tolist()
            else:
                serializable_raw[str(key)] = value
        serializable_raw["_unified_state_sources"] = sources

        return UnifiedRuntimeResult(
            feature_shape=(30, 525),
            intent_prediction=intent_prediction,
            p_crossing=state["p_crossing"],
            confidence=state["confidence"],
            normalized_predictive_entropy=state["normalized_predictive_entropy"],
            mutual_information=state["mutual_information"],
            crossing_probability_variance=state["crossing_probability_variance"],
            variation_ratio=state["variation_ratio"],
            decision_margin_uncertainty=state["decision_margin_uncertainty"],
            observation_reliability_mean={
                "low": state["reliability_low_mean"],
                "medium": state["reliability_medium_mean"],
                "high": state["reliability_high_mean"],
            },
            observation_reliability_last={
                "low": state["reliability_low_last"],
                "medium": state["reliability_medium_last"],
                "high": state["reliability_high_last"],
            },
            mean_speed=state["mean_speed"],
            last_speed=state["last_speed"],
            agent_action_id=int(explanation.action_id),
            agent_action_name=str(explanation.action_name),
            agent_action_probability=float(explanation.action_probability),
            agent_action_probabilities=dict(explanation.action_probabilities),
            committed_intent=committed_intent,
            av_interface_signal=av_signal,
            maximum_occlusion=maximum_occlusion,
            dominant_explanation_group=str(explanation.dominant_evidence_group),
            explanation=str(explanation.situation_summary),
            top_supporting_evidence=[asdict(item) for item in explanation.top_supporting_evidence],
            top_opposing_evidence=[asdict(item) for item in explanation.top_opposing_evidence],
            agent_state={k: float(v) for k, v in state.items()},
            raw_intent_output=serializable_raw,
        )
