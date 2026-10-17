from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn


ACTION_NAMES = {
    0: "OBSERVE_MORE",
    1: "COMMIT_NOT_CROSSING",
    2: "COMMIT_CROSSING",
}


class AgentPolicyMLP(nn.Module):
    """Small learned policy network for evidence-aware intent commitment."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim_1: int = 64,
        hidden_dim_2: int = 32,
        dropout: float = 0.20,
    ) -> None:
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim_1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim_1, hidden_dim_2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim_2, 3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass
class AgentPolicyPrediction:
    action_id: int
    action_name: str
    action_probabilities: dict[str, float]


class LearnedAgentPolicy:
    """Runtime wrapper around the learned Phase-7 policy."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str | torch.device = "cpu",
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.device = torch.device(device)

        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device,
            weights_only=False,
        )

        self.state_features = list(checkpoint["state_features"])
        self.mean = np.asarray(checkpoint["normalization_mean"], dtype=np.float32)
        self.std = np.asarray(checkpoint["normalization_std"], dtype=np.float32)

        architecture = checkpoint["architecture"]

        self.model = AgentPolicyMLP(
            input_dim=len(self.state_features),
            hidden_dim_1=int(architecture["hidden_dim_1"]),
            hidden_dim_2=int(architecture["hidden_dim_2"]),
            dropout=float(architecture["dropout"]),
        ).to(self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.std

    @torch.no_grad()
    def predict_array(
        self,
        state_values: Sequence[float] | np.ndarray,
    ) -> AgentPolicyPrediction:
        x = np.asarray(state_values, dtype=np.float32)

        if x.shape != (len(self.state_features),):
            raise ValueError(
                f"Expected state shape ({len(self.state_features)},), got {x.shape}."
            )

        x = self._normalize(x)

        tensor = torch.from_numpy(x).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()

        action_id = int(np.argmax(probabilities))

        return AgentPolicyPrediction(
            action_id=action_id,
            action_name=ACTION_NAMES[action_id],
            action_probabilities={
                ACTION_NAMES[index]: float(probabilities[index])
                for index in range(3)
            },
        )

    def predict_dict(
        self,
        state: dict[str, float],
    ) -> AgentPolicyPrediction:
        missing = [name for name in self.state_features if name not in state]

        if missing:
            raise KeyError(
                f"Missing agent-state features: {missing}"
            )

        values = [float(state[name]) for name in self.state_features]
        return self.predict_array(values)
