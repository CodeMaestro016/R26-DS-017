"""
Gated Bayesian Fusion Transformer.

Inputs
------
Visual features:
    (batch, 30, 522)

Bayesian features:
    (batch, 30, 5)

Output
------
Intent logits:
    (batch, 2)

The visual sequence is processed by a Transformer.

The Bayesian sequence is processed by a small
semantic branch.

A learned gate determines how much Bayesian
information should be fused with the visual
Transformer representation.
"""

import torch
import torch.nn as nn


class GatedFusionIntentModel(nn.Module):

    def __init__(
        self,
        visual_input_dim=522,
        bayesian_input_dim=5,
        sequence_length=30,
        num_classes=2,
        d_model=128,
        num_heads=4,
        num_layers=2,
        dim_feedforward=256,
        bayesian_hidden_dim=32,
        dropout=0.2
    ):
        super().__init__()

        if visual_input_dim <= 0:
            raise ValueError(
                "visual_input_dim must be positive."
            )

        if bayesian_input_dim <= 0:
            raise ValueError(
                "bayesian_input_dim must be positive."
            )

        if sequence_length <= 0:
            raise ValueError(
                "sequence_length must be positive."
            )

        if d_model % num_heads != 0:
            raise ValueError(
                "d_model must be divisible "
                "by num_heads."
            )

        self.visual_input_dim = (
            visual_input_dim
        )

        self.bayesian_input_dim = (
            bayesian_input_dim
        )

        self.sequence_length = (
            sequence_length
        )

        self.d_model = d_model
        self.num_classes = num_classes

        # ----------------------------------------------------------
        # Visual Transformer branch
        # ----------------------------------------------------------

        self.visual_projection = nn.Sequential(
            nn.Linear(
                visual_input_dim,
                d_model
            ),
            nn.LayerNorm(
                d_model
            ),
            nn.GELU()
        )

        self.class_token = nn.Parameter(
            torch.zeros(
                1,
                1,
                d_model
            )
        )

        self.position_embedding = nn.Parameter(
            torch.zeros(
                1,
                sequence_length + 1,
                d_model
            )
        )

        self.visual_dropout = nn.Dropout(
            dropout
        )

        encoder_layer = (
            nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=num_heads,
                dim_feedforward=
                    dim_feedforward,
                dropout=dropout,
                activation="gelu",
                batch_first=True,
                norm_first=True
            )
        )

        self.transformer_encoder = (
            nn.TransformerEncoder(
                encoder_layer=
                    encoder_layer,
                num_layers=num_layers,

                # Avoid the nested tensor warning
                # produced with norm_first=True.
                enable_nested_tensor=False
            )
        )

        self.visual_normalization = (
            nn.LayerNorm(
                d_model
            )
        )

        # ----------------------------------------------------------
        # Bayesian semantic branch
        # ----------------------------------------------------------

        self.bayesian_projection = (
            nn.Sequential(
                nn.Linear(
                    bayesian_input_dim,
                    bayesian_hidden_dim
                ),
                nn.LayerNorm(
                    bayesian_hidden_dim
                ),
                nn.GELU(),
                nn.Dropout(
                    dropout
                )
            )
        )

        # Learn which frames contain useful
        # Bayesian semantic evidence.
        self.bayesian_attention = nn.Linear(
            bayesian_hidden_dim,
            1
        )

        self.bayesian_to_visual = (
            nn.Sequential(
                nn.Linear(
                    bayesian_hidden_dim,
                    d_model
                ),
                nn.GELU()
            )
        )

        # ----------------------------------------------------------
        # Learned gated fusion
        # ----------------------------------------------------------

        self.fusion_gate = nn.Sequential(
            nn.Linear(
                d_model * 2,
                d_model
            ),
            nn.Sigmoid()
        )

        self.fusion_normalization = (
            nn.LayerNorm(
                d_model
            )
        )

        self.classifier = nn.Sequential(
            nn.Linear(
                d_model,
                d_model // 2
            ),
            nn.GELU(),
            nn.Dropout(
                dropout
            ),
            nn.Linear(
                d_model // 2,
                num_classes
            )
        )

        self._initialize_parameters()

    def _initialize_parameters(self):

        nn.init.trunc_normal_(
            self.class_token,
            std=0.02
        )

        nn.init.trunc_normal_(
            self.position_embedding,
            std=0.02
        )

        for module in self.modules():

            if isinstance(module, nn.Linear):

                nn.init.xavier_uniform_(
                    module.weight
                )

                if module.bias is not None:
                    nn.init.zeros_(
                        module.bias
                    )

    def _validate_inputs(
        self,
        visual_features,
        bayesian_features
    ):

        if visual_features.ndim != 3:
            raise ValueError(
                "Visual input must have shape "
                "(batch, sequence, features)."
            )

        if bayesian_features.ndim != 3:
            raise ValueError(
                "Bayesian input must have shape "
                "(batch, sequence, features)."
            )

        if (
            visual_features.shape[0]
            != bayesian_features.shape[0]
        ):
            raise ValueError(
                "Visual and Bayesian batch "
                "sizes do not match."
            )

        if (
            visual_features.shape[1]
            != bayesian_features.shape[1]
        ):
            raise ValueError(
                "Visual and Bayesian sequence "
                "lengths do not match."
            )

        if (
            visual_features.shape[1]
            != self.sequence_length
        ):
            raise ValueError(
                f"Expected sequence length "
                f"{self.sequence_length}, got "
                f"{visual_features.shape[1]}."
            )

        if (
            visual_features.shape[2]
            != self.visual_input_dim
        ):
            raise ValueError(
                f"Expected visual input dimension "
                f"{self.visual_input_dim}, got "
                f"{visual_features.shape[2]}."
            )

        if (
            bayesian_features.shape[2]
            != self.bayesian_input_dim
        ):
            raise ValueError(
                f"Expected Bayesian dimension "
                f"{self.bayesian_input_dim}, got "
                f"{bayesian_features.shape[2]}."
            )

    def forward(
        self,
        visual_features,
        bayesian_features,
        return_diagnostics=False
    ):

        self._validate_inputs(
            visual_features,
            bayesian_features
        )

        batch_size = (
            visual_features.shape[0]
        )

        # ----------------------------------------------------------
        # Visual branch
        # ----------------------------------------------------------

        visual_embeddings = (
            self.visual_projection(
                visual_features
            )
        )

        class_token = (
            self.class_token.expand(
                batch_size,
                -1,
                -1
            )
        )

        visual_embeddings = torch.cat(
            [
                class_token,
                visual_embeddings
            ],
            dim=1
        )

        visual_embeddings = (
            visual_embeddings
            + self.position_embedding
        )

        visual_embeddings = (
            self.visual_dropout(
                visual_embeddings
            )
        )

        encoded_visual = (
            self.transformer_encoder(
                visual_embeddings
            )
        )

        visual_representation = (
            self.visual_normalization(
                encoded_visual[:, 0, :]
            )
        )

        # ----------------------------------------------------------
        # Bayesian branch
        # ----------------------------------------------------------

        bayesian_embeddings = (
            self.bayesian_projection(
                bayesian_features
            )
        )

        attention_scores = (
            self.bayesian_attention(
                bayesian_embeddings
            )
        )

        attention_weights = torch.softmax(
            attention_scores,
            dim=1
        )

        bayesian_representation = torch.sum(
            attention_weights
            * bayesian_embeddings,
            dim=1
        )

        bayesian_representation = (
            self.bayesian_to_visual(
                bayesian_representation
            )
        )

        # ----------------------------------------------------------
        # Gated residual fusion
        # ----------------------------------------------------------

        gate_input = torch.cat(
            [
                visual_representation,
                bayesian_representation
            ],
            dim=1
        )

        fusion_gate = self.fusion_gate(
            gate_input
        )

        fused_representation = (
            visual_representation
            + (
                fusion_gate
                * bayesian_representation
            )
        )

        fused_representation = (
            self.fusion_normalization(
                fused_representation
            )
        )

        logits = self.classifier(
            fused_representation
        )

        if return_diagnostics:

            return {
                "logits": logits,

                "fusion_gate":
                    fusion_gate,

                "bayesian_attention_weights":
                    attention_weights.squeeze(-1)
            }

        return logits

    def count_trainable_parameters(self):

        return sum(
            parameter.numel()
            for parameter in self.parameters()
            if parameter.requires_grad
        )