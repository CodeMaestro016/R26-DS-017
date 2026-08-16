from __future__ import annotations

import torch
from torch import nn


class LearnedOcclusionEstimator(nn.Module):
    """
    Supervised three-class occlusion estimator.

    Classes:
        0 -> none
        1 -> part
        2 -> full
    """

    def __init__(
        self,
        input_dim: int = 518,
        hidden1: int = 128,
        hidden2: int = 64,
        dropout: float = 0.20,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(
                input_dim,
                hidden1,
            ),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(
                hidden1,
                hidden2,
            ),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(
                hidden2,
                3,
            ),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        return self.network(x)
