from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from utils.agent_explainer import (
    FEATURE_DISPLAY_NAMES,
    IntegratedGradientsAgentExplainer,
)


@dataclass
class EvidenceItem:
    feature: str
    label: str
    state_value: float
    attribution: float
    absolute_share: float


@dataclass
class SituationExplanationResult:
    action_id: int
    action_name: str
    action_probability: float
    action_probabilities: dict[str, float]
    maximum_occlusion: str | None
    dominant_evidence_group: str
    group_contributions: dict[str, float]
    top_supporting_evidence: list[EvidenceItem]
    top_opposing_evidence: list[EvidenceItem]
    situation_summary: str

    def to_dict(self) -> dict:
        return asdict(self)


class SituationAwareExplanationAgent:
    def __init__(
        self,
        policy_checkpoint: str | Path = "outputs/phase7/learned_agent_policy_best.pt",
        device: str = "cpu",
        integration_steps: int = 32,
    ) -> None:
        self.explainer = IntegratedGradientsAgentExplainer(
            checkpoint_path=policy_checkpoint,
            device=device,
            integration_steps=integration_steps,
        )
        self.state_features = list(self.explainer.state_features)

    def _make_item(
        self,
        feature: str,
        attribution: float,
        state: Mapping[str, float],
        absolute_share: float,
    ) -> EvidenceItem:
        return EvidenceItem(
            feature=feature,
            label=FEATURE_DISPLAY_NAMES[feature],
            state_value=float(state[feature]),
            attribution=float(attribution),
            absolute_share=float(absolute_share),
        )

    @staticmethod
    def _format_evidence_item(item: EvidenceItem) -> str:
        return (
            f"{item.label} "
            f"(value={item.state_value:.3f}, "
            f"attribution={item.attribution:+.3f})"
        )

    def explain(
        self,
        state: Mapping[str, float],
        *,
        maximum_occlusion: str | None = None,
    ) -> SituationExplanationResult:
        result = self.explainer.explain(
            state,
            maximum_occlusion=maximum_occlusion,
        )

        supporting = [
            self._make_item(
                feature,
                attribution,
                state,
                result.normalized_absolute_contributions[feature],
            )
            for feature, attribution in result.top_supporting_features
        ]

        opposing = [
            self._make_item(
                feature,
                attribution,
                state,
                result.normalized_absolute_contributions[feature],
            )
            for feature, attribution in result.top_opposing_features
        ]

        dominant_group = max(
            result.group_absolute_contributions,
            key=result.group_absolute_contributions.get,
        )

        sentences = [
            f"Decision: {result.action_name} "
            f"(policy probability {result.action_probability:.3f})."
        ]

        if maximum_occlusion is not None:
            occ = str(maximum_occlusion).strip()
            if occ and occ.lower() != "nan":
                sentences.append(f"Observed maximum occlusion: {occ}.")

        if supporting:
            rendered = [
                self._format_evidence_item(item)
                for item in supporting
            ]
            if len(rendered) == 1:
                joined = rendered[0]
            elif len(rendered) == 2:
                joined = f"{rendered[0]} and {rendered[1]}"
            else:
                joined = (
                    f"{rendered[0]}, {rendered[1]}, and {rendered[2]}"
                )
            sentences.append(
                "The strongest local evidence supporting this decision was "
                f"{joined}."
            )

        if opposing:
            sentences.append(
                "The strongest local evidence opposing the selected decision was "
                f"{self._format_evidence_item(opposing[0])}."
            )

        sentences.append(
            f"The dominant attribution group was {dominant_group}."
        )
        sentences.append(
            "This explanation describes the learned policy's local model evidence "
            "for the current situation; it is not a causal claim about pedestrian behaviour."
        )

        return SituationExplanationResult(
            action_id=result.action_id,
            action_name=result.action_name,
            action_probability=result.action_probability,
            action_probabilities=result.action_probabilities,
            maximum_occlusion=maximum_occlusion,
            dominant_evidence_group=dominant_group,
            group_contributions=result.group_absolute_contributions,
            top_supporting_evidence=supporting,
            top_opposing_evidence=opposing,
            situation_summary=" ".join(sentences),
        )
