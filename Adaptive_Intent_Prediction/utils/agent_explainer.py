from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

from utils.learned_agent_policy import ACTION_NAMES, LearnedAgentPolicy


FEATURE_DISPLAY_NAMES = {
    "p_crossing": "crossing probability",
    "confidence": "prediction confidence",
    "normalized_predictive_entropy": "predictive entropy",
    "mutual_information": "model uncertainty (mutual information)",
    "crossing_probability_variance": "crossing-probability variance",
    "variation_ratio": "MC-dropout variation ratio",
    "decision_margin_uncertainty": "decision-margin uncertainty",
    "reliability_low_mean": "mean low-reliability evidence",
    "reliability_medium_mean": "mean medium-reliability evidence",
    "reliability_high_mean": "mean high-reliability evidence",
    "reliability_low_last": "latest low-reliability evidence",
    "reliability_medium_last": "latest medium-reliability evidence",
    "reliability_high_last": "latest high-reliability evidence",
    "mean_speed": "mean pedestrian speed",
    "last_speed": "latest pedestrian speed",
}

FEATURE_GROUPS = {
    "intent": ["p_crossing"],
    "uncertainty": [
        "confidence",
        "normalized_predictive_entropy",
        "mutual_information",
        "crossing_probability_variance",
        "variation_ratio",
        "decision_margin_uncertainty",
    ],
    "reliability": [
        "reliability_low_mean",
        "reliability_medium_mean",
        "reliability_high_mean",
        "reliability_low_last",
        "reliability_medium_last",
        "reliability_high_last",
    ],
    "motion": ["mean_speed", "last_speed"],
}


@dataclass
class AgentExplanation:
    action_id: int
    action_name: str
    action_probability: float
    action_probabilities: dict[str, float]
    feature_attributions: dict[str, float]
    normalized_absolute_contributions: dict[str, float]
    group_absolute_contributions: dict[str, float]
    top_supporting_features: list[tuple[str, float]]
    top_opposing_features: list[tuple[str, float]]
    explanation_text: str


class IntegratedGradientsAgentExplainer:
    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str | torch.device = "cpu",
        integration_steps: int = 64,
    ) -> None:
        if integration_steps < 8:
            raise ValueError("integration_steps must be at least 8")

        self.policy = LearnedAgentPolicy(
            checkpoint_path=checkpoint_path,
            device=device,
        )
        self.device = self.policy.device
        self.integration_steps = int(integration_steps)
        self.state_features = list(self.policy.state_features)

        unknown = [
            f for f in self.state_features
            if f not in FEATURE_DISPLAY_NAMES
        ]
        if unknown:
            raise KeyError(
                f"Missing display names for features: {unknown}"
            )

    def _state_array(self, state: Mapping[str, float]) -> np.ndarray:
        missing = [
            name for name in self.state_features
            if name not in state
        ]
        if missing:
            raise KeyError(f"Missing policy-state features: {missing}")

        values = np.asarray(
            [float(state[name]) for name in self.state_features],
            dtype=np.float32,
        )
        if not np.isfinite(values).all():
            raise ValueError("Agent state contains non-finite values")
        return values

    def _integrated_gradients(
        self,
        normalized_input: np.ndarray,
        action_id: int,
    ) -> np.ndarray:
        x = torch.tensor(
            normalized_input,
            dtype=torch.float32,
            device=self.device,
        )
        baseline = torch.zeros_like(x)
        delta = x - baseline

        alphas = torch.linspace(
            0.0,
            1.0,
            self.integration_steps + 1,
            device=self.device,
        )

        grads = []
        self.policy.model.eval()

        for alpha in alphas:
            point = (
                baseline + alpha * delta
            ).detach().clone().requires_grad_(True)

            logits = self.policy.model(point.unsqueeze(0))
            target = logits[0, action_id]
            grad = torch.autograd.grad(
                target,
                point,
                retain_graph=False,
                create_graph=False,
            )[0]
            grads.append(grad.detach())

        stacked = torch.stack(grads, dim=0)
        avg_grad = (
            (stacked[:-1] + stacked[1:]) / 2.0
        ).mean(dim=0)

        attrs = (
            delta * avg_grad
        ).detach().cpu().numpy()

        return attrs.astype(np.float32)

    def _group_contributions(
        self,
        normalized_abs: dict[str, float],
    ) -> dict[str, float]:
        result = {
            group: float(
                sum(normalized_abs.get(feature, 0.0)
                    for feature in features)
            )
            for group, features in FEATURE_GROUPS.items()
        }

        total = sum(result.values())
        if total > 0:
            result = {
                key: float(value / total)
                for key, value in result.items()
            }
        return result

    @staticmethod
    def _top_signed(
        feature_attributions: dict[str, float],
        positive: bool,
        limit: int = 3,
    ) -> list[tuple[str, float]]:
        items = []
        for feature, value in feature_attributions.items():
            if positive and value > 0:
                items.append((feature, float(value)))
            elif (not positive) and value < 0:
                items.append((feature, float(value)))

        items.sort(
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        return items[:limit]

    def _render_text(
        self,
        action_name: str,
        action_probability: float,
        maximum_occlusion: str | None,
        top_supporting: list[tuple[str, float]],
        top_opposing: list[tuple[str, float]],
        group_contributions: dict[str, float],
    ) -> str:
        sentences = [
            (
                f"The learned decision agent selected {action_name} "
                f"with policy probability {action_probability:.3f}."
            )
        ]

        if maximum_occlusion is not None:
            occ = str(maximum_occlusion).strip()
            if occ and occ.lower() != "nan":
                sentences.append(
                    f"The sequence is labeled with {occ} maximum occlusion."
                )

        if top_supporting:
            labels = [
                FEATURE_DISPLAY_NAMES[name]
                for name, _ in top_supporting
            ]
            if len(labels) == 1:
                joined = labels[0]
            elif len(labels) == 2:
                joined = f"{labels[0]} and {labels[1]}"
            else:
                joined = f"{labels[0]}, {labels[1]}, and {labels[2]}"

            sentences.append(
                "The strongest local positive contributions to this "
                f"action came from {joined}."
            )

        if top_opposing:
            opposing = FEATURE_DISPLAY_NAMES[
                top_opposing[0][0]
            ]
            sentences.append(
                "The strongest local evidence acting against the "
                f"selected action was {opposing}."
            )

        if group_contributions:
            strongest_group = max(
                group_contributions,
                key=group_contributions.get,
            )
            sentences.append(
                "At the evidence-group level, the largest absolute "
                f"model attribution came from the {strongest_group} group."
            )

        sentences.append(
            "These are post-hoc model attributions for this situation "
            "and are not causal effects."
        )
        return " ".join(sentences)

    def explain(
        self,
        state: Mapping[str, float],
        maximum_occlusion: str | None = None,
        action_id: int | None = None,
    ) -> AgentExplanation:
        raw = self._state_array(state)
        normalized = self.policy._normalize(raw).astype(np.float32)

        with torch.no_grad():
            tensor = torch.from_numpy(
                normalized
            ).unsqueeze(0).to(self.device)
            logits = self.policy.model(tensor)
            probs = torch.softmax(
                logits,
                dim=1,
            )[0].cpu().numpy()

        if action_id is None:
            action_id = int(np.argmax(probs))

        attrs = self._integrated_gradients(
            normalized,
            action_id,
        )

        feature_attributions = {
            feature: float(value)
            for feature, value in zip(
                self.state_features,
                attrs,
            )
        }

        absolute = np.abs(attrs)
        total = float(absolute.sum())
        shares = (
            absolute / total
            if total > 0
            else np.zeros_like(absolute)
        )

        normalized_abs = {
            feature: float(value)
            for feature, value in zip(
                self.state_features,
                shares,
            )
        }

        group_contributions = self._group_contributions(
            normalized_abs
        )
        top_supporting = self._top_signed(
            feature_attributions,
            positive=True,
        )
        top_opposing = self._top_signed(
            feature_attributions,
            positive=False,
        )

        action_name = ACTION_NAMES[action_id]
        action_probability = float(probs[action_id])

        action_probabilities = {
            ACTION_NAMES[i]: float(probs[i])
            for i in range(3)
        }

        text = self._render_text(
            action_name,
            action_probability,
            maximum_occlusion,
            top_supporting,
            top_opposing,
            group_contributions,
        )

        return AgentExplanation(
            action_id=action_id,
            action_name=action_name,
            action_probability=action_probability,
            action_probabilities=action_probabilities,
            feature_attributions=feature_attributions,
            normalized_absolute_contributions=normalized_abs,
            group_absolute_contributions=group_contributions,
            top_supporting_features=top_supporting,
            top_opposing_features=top_opposing,
            explanation_text=text,
        )
