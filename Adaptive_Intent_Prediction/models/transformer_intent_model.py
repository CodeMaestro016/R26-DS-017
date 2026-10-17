"""
Transformer-based Pedestrian Intent Predictor.

Supported inputs:

Baseline:
    (batch_size, 30, 522)

Bayesian-enriched:
    (batch_size, 30, 527)

Output:
    (batch_size, 2)

Classes:
    0 = not-crossing
    1 = crossing
"""

import torch
import torch.nn as nn


class TransformerIntentModel(nn.Module):

    def __init__(
        self,
        input_dim,
        sequence_length=30,
        num_classes=2,
        d_model=128,
        num_heads=4,
        num_layers=2,
        dim_feedforward=256,
        dropout=0.2
    ):
        super().__init__()

        if input_dim <= 0:
            raise ValueError(
                "input_dim must be greater than zero."
            )

        if sequence_length <= 0:
            raise ValueError(
                "sequence_length must be greater than zero."
            )

        if d_model % num_heads != 0:
            raise ValueError(
                "d_model must be divisible by num_heads. "
                f"Received d_model={d_model}, "
                f"num_heads={num_heads}."
            )

        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.num_classes = num_classes

        # Convert the original feature vector into
        # the Transformer embedding dimension.
        self.input_projection = nn.Sequential(
            nn.Linear(
                input_dim,
                d_model
            ),
            nn.LayerNorm(
                d_model
            ),
            nn.GELU()
        )

        # Learnable classification token.
        self.class_token = nn.Parameter(
            torch.zeros(
                1,
                1,
                d_model
            )
        )

        # +1 is required for the classification token.
        self.position_embedding = nn.Parameter(
            torch.zeros(
                1,
                sequence_length + 1,
                d_model
            )
        )

        self.embedding_dropout = nn.Dropout(
            dropout
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )

        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer=encoder_layer,
            num_layers=num_layers
        )

        self.output_normalization = nn.LayerNorm(
            d_model
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

    def forward(self, features):
        """
        Parameters
        ----------
        features:
            Tensor with shape:

            (batch_size, sequence_length, input_dim)

        Returns
        -------
        logits:
            Tensor with shape:

            (batch_size, num_classes)
        """

        if features.ndim != 3:
            raise ValueError(
                "Expected input shape "
                "(batch, sequence, features), "
                f"but received {tuple(features.shape)}."
            )

        batch_size = features.shape[0]
        sequence_length = features.shape[1]
        input_dim = features.shape[2]

        if sequence_length != self.sequence_length:
            raise ValueError(
                f"Expected sequence length "
                f"{self.sequence_length}, "
                f"but received {sequence_length}."
            )

        if input_dim != self.input_dim:
            raise ValueError(
                f"Expected input dimension "
                f"{self.input_dim}, "
                f"but received {input_dim}."
            )

        embeddings = self.input_projection(
            features
        )

        class_token = self.class_token.expand(
            batch_size,
            -1,
            -1
        )

        embeddings = torch.cat(
            [
                class_token,
                embeddings
            ],
            dim=1
        )

        embeddings = (
            embeddings
            + self.position_embedding[
                :,
                :sequence_length + 1,
                :
            ]
        )

        embeddings = self.embedding_dropout(
            embeddings
        )

        encoded = self.transformer_encoder(
            embeddings
        )

        # The first token is the learnable
        # classification token.
        sequence_representation = encoded[:, 0, :]

        sequence_representation = (
            self.output_normalization(
                sequence_representation
            )
        )

        logits = self.classifier(
            sequence_representation
        )

        return logits

    def count_trainable_parameters(self):

        return sum(
            parameter.numel()
            for parameter in self.parameters()
            if parameter.requires_grad
        )