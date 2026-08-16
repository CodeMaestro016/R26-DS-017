"""
Train Bayesian ablation models and the Gated Fusion Transformer.

Experiments
-----------
1. Intention-only Transformer:
       522 original + 2 intention probabilities = 524

2. Reliability-only Transformer:
       522 original + 3 reliability probabilities = 525

3. Gated Fusion Transformer:
       visual branch   = 522 features
       Bayesian branch = 5 features

The test split is not used.
"""

from __future__ import annotations

import argparse
import gc
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import Dataset

from models.gated_fusion_intent_model import (
    GatedFusionIntentModel
)

from scripts.phase5.train_transformers import (
    TrainingConfig,
    ModelSpecification,
    calculate_class_weights,
    calculate_metrics,
    calculate_training_normalizer,
    create_data_loader,
    load_feature_file,
    set_random_seed,
    train_model,
    validate_label_alignment,
    validate_split_isolation
)


FEATURE_DIR = Path(
    "datasets/processed/features"
)

OUTPUT_DIR = Path(
    "outputs/phase5"
)


# =====================================================================
# Gated Fusion Dataset
# =====================================================================

class GatedFusionDataset(Dataset):

    def __init__(
        self,
        visual_features,
        bayesian_features,
        labels,
        visual_mean,
        visual_standard_deviation
    ):

        if (
            visual_features.shape[:2]
            != bayesian_features.shape[:2]
        ):
            raise ValueError(
                "Visual and Bayesian feature arrays "
                "are not aligned."
            )

        if len(visual_features) != len(labels):
            raise ValueError(
                "Feature and label counts do not match."
            )

        self.visual_features = torch.from_numpy(
            np.ascontiguousarray(
                visual_features,
                dtype=np.float32
            )
        )

        self.bayesian_features = torch.from_numpy(
            np.ascontiguousarray(
                bayesian_features,
                dtype=np.float32
            )
        )

        self.labels = torch.from_numpy(
            np.ascontiguousarray(
                labels,
                dtype=np.int64
            )
        )

        self.visual_mean = torch.from_numpy(
            visual_mean.astype(
                np.float32,
                copy=False
            )
        ).view(1, -1)

        self.visual_standard_deviation = (
            torch.from_numpy(
                visual_standard_deviation.astype(
                    np.float32,
                    copy=False
                )
            ).view(1, -1)
        )

    def __len__(self):

        return len(self.labels)

    def __getitem__(self, index):

        visual_sequence = (
            self.visual_features[index]
        )

        visual_sequence = (
            visual_sequence
            - self.visual_mean
        ) / self.visual_standard_deviation

        # Bayesian values are probabilities in [0, 1].
        # The Bayesian branch already contains LayerNorm,
        # therefore they remain in their probability scale.
        bayesian_sequence = (
            self.bayesian_features[index]
        )

        label = self.labels[index]

        return (
            visual_sequence,
            bayesian_sequence,
            label
        )


# =====================================================================
# Gated Fusion Epoch
# =====================================================================

def run_gated_epoch(
    model,
    data_loader,
    loss_function,
    device,
    optimizer,
    gradient_clip_norm
):

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_samples = 0
    total_gate_value = 0.0

    all_labels = []
    all_predictions = []
    all_positive_probabilities = []

    for (
        visual_sequences,
        bayesian_sequences,
        labels
    ) in data_loader:

        visual_sequences = visual_sequences.to(
            device,
            non_blocking=True
        )

        bayesian_sequences = bayesian_sequences.to(
            device,
            non_blocking=True
        )

        labels = labels.to(
            device,
            non_blocking=True
        )

        if is_training:
            optimizer.zero_grad(
                set_to_none=True
            )

        with torch.set_grad_enabled(
            is_training
        ):

            diagnostics = model(
                visual_features=visual_sequences,
                bayesian_features=bayesian_sequences,
                return_diagnostics=True
            )

            logits = diagnostics["logits"]

            loss = loss_function(
                logits,
                labels
            )

            if is_training:

                loss.backward()

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_norm=gradient_clip_norm
                )

                optimizer.step()

        probabilities = torch.softmax(
            logits,
            dim=1
        )

        predictions = torch.argmax(
            probabilities,
            dim=1
        )

        positive_probabilities = (
            probabilities[:, 1]
        )

        fusion_gate = diagnostics[
            "fusion_gate"
        ]

        batch_size = labels.shape[0]

        total_loss += (
            float(loss.item())
            * batch_size
        )

        total_gate_value += (
            float(fusion_gate.mean().item())
            * batch_size
        )

        total_samples += batch_size

        all_labels.append(
            labels.detach().cpu().numpy()
        )

        all_predictions.append(
            predictions.detach().cpu().numpy()
        )

        all_positive_probabilities.append(
            positive_probabilities
            .detach()
            .cpu()
            .numpy()
        )

    labels_array = np.concatenate(
        all_labels
    )

    predictions_array = np.concatenate(
        all_predictions
    )

    probabilities_array = np.concatenate(
        all_positive_probabilities
    )

    metrics = calculate_metrics(
        labels=labels_array,
        predictions=predictions_array,
        positive_probabilities=
            probabilities_array
    )

    metrics["loss"] = (
        total_loss
        / total_samples
    )

    metrics["gate_mean"] = (
        total_gate_value
        / total_samples
    )

    return metrics


# =====================================================================
# Gated Checkpoint
# =====================================================================

def save_gated_checkpoint(
    path,
    model,
    configuration,
    visual_mean,
    visual_standard_deviation,
    class_weights,
    epoch,
    validation_metrics
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    state_dictionary = {
        name: parameter.detach().cpu()
        for name, parameter
        in model.state_dict().items()
    }

    checkpoint = {
        "model_name":
            "gated_fusion",

        "model_state_dict":
            state_dictionary,

        "visual_input_dimension":
            522,

        "bayesian_input_dimension":
            5,

        "sequence_length":
            configuration.sequence_length,

        "num_classes":
            configuration.num_classes,

        "model_configuration": {
            "d_model":
                configuration.d_model,

            "num_heads":
                configuration.num_heads,

            "num_layers":
                configuration.num_layers,

            "dim_feedforward":
                configuration.dim_feedforward,

            "bayesian_hidden_dim":
                32,

            "dropout":
                configuration.dropout
        },

        "training_configuration":
            asdict(configuration),

        "visual_feature_mean":
            torch.from_numpy(
                visual_mean
            ),

        "visual_feature_standard_deviation":
            torch.from_numpy(
                visual_standard_deviation
            ),

        "bayesian_features_normalized":
            False,

        "class_weights":
            class_weights.detach().cpu(),

        "best_epoch":
            int(epoch),

        "best_validation_metrics":
            validation_metrics,

        "class_names": [
            "not-crossing",
            "crossing"
        ]
    }

    torch.save(
        checkpoint,
        path
    )


# =====================================================================
# Gated Training
# =====================================================================

def train_gated_model(
    configuration,
    device
):

    print()
    print("=" * 78)
    print("TRAINING GATED FUSION TRANSFORMER")
    print("=" * 78)

    train_visual, train_labels = (
        load_feature_file(
            path=(
                FEATURE_DIR
                / "train_features.npz"
            ),
            expected_input_dimension=522,
            sequence_length=
                configuration.sequence_length
        )
    )

    val_visual, val_labels = (
        load_feature_file(
            path=(
                FEATURE_DIR
                / "val_features.npz"
            ),
            expected_input_dimension=522,
            sequence_length=
                configuration.sequence_length
        )
    )

    train_bayesian, train_bayesian_labels = (
        load_feature_file(
            path=(
                FEATURE_DIR
                / "train_bayesian_features.npz"
            ),
            expected_input_dimension=5,
            sequence_length=
                configuration.sequence_length
        )
    )

    val_bayesian, val_bayesian_labels = (
        load_feature_file(
            path=(
                FEATURE_DIR
                / "val_bayesian_features.npz"
            ),
            expected_input_dimension=5,
            sequence_length=
                configuration.sequence_length
        )
    )

    if not np.array_equal(
        train_labels,
        train_bayesian_labels
    ):
        raise ValueError(
            "Train visual and Bayesian labels "
            "are not aligned."
        )

    if not np.array_equal(
        val_labels,
        val_bayesian_labels
    ):
        raise ValueError(
            "Validation visual and Bayesian labels "
            "are not aligned."
        )

    print(
        "Train visual shape    :",
        train_visual.shape
    )

    print(
        "Train Bayesian shape  :",
        train_bayesian.shape
    )

    print(
        "Validation visual     :",
        val_visual.shape
    )

    print(
        "Validation Bayesian   :",
        val_bayesian.shape
    )

    visual_mean, visual_std = (
        calculate_training_normalizer(
            train_visual
        )
    )

    train_dataset = GatedFusionDataset(
        visual_features=train_visual,
        bayesian_features=train_bayesian,
        labels=train_labels,
        visual_mean=visual_mean,
        visual_standard_deviation=visual_std
    )

    validation_dataset = GatedFusionDataset(
        visual_features=val_visual,
        bayesian_features=val_bayesian,
        labels=val_labels,
        visual_mean=visual_mean,
        visual_standard_deviation=visual_std
    )

    pin_memory = (
        device.type == "cuda"
    )

    train_loader = create_data_loader(
        dataset=train_dataset,
        batch_size=configuration.batch_size,
        shuffle=True,
        seed=configuration.random_seed,
        num_workers=configuration.num_workers,
        pin_memory=pin_memory
    )

    validation_loader = create_data_loader(
        dataset=validation_dataset,
        batch_size=configuration.batch_size,
        shuffle=False,
        seed=configuration.random_seed,
        num_workers=configuration.num_workers,
        pin_memory=pin_memory
    )

    class_weights = calculate_class_weights(
        training_labels=train_labels,
        device=device
    )

    model = GatedFusionIntentModel(
        visual_input_dim=522,
        bayesian_input_dim=5,
        sequence_length=
            configuration.sequence_length,
        num_classes=
            configuration.num_classes,
        d_model=
            configuration.d_model,
        num_heads=
            configuration.num_heads,
        num_layers=
            configuration.num_layers,
        dim_feedforward=
            configuration.dim_feedforward,
        bayesian_hidden_dim=32,
        dropout=
            configuration.dropout
    ).to(device)

    loss_function = nn.CrossEntropyLoss(
        weight=class_weights
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=configuration.learning_rate,
        weight_decay=
            configuration.weight_decay
    )

    scheduler = (
        torch.optim.lr_scheduler
        .ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=
                configuration.scheduler_factor,
            patience=
                configuration.scheduler_patience
        )
    )

    print(
        "Trainable parameters:",
        f"{model.count_trainable_parameters():,}"
    )

    print(
        "Device:",
        device
    )

    checkpoint_path = (
        OUTPUT_DIR
        / "gated_fusion_transformer_best.pt"
    )

    history_path = (
        OUTPUT_DIR
        / "gated_fusion_training_history.csv"
    )

    summary_path = (
        OUTPUT_DIR
        / "gated_fusion_training_summary.json"
    )

    history = []

    best_average_precision = (
        -float("inf")
    )

    best_epoch = 0
    best_validation_metrics = None

    epochs_without_improvement = 0

    for epoch in range(
        1,
        configuration.maximum_epochs + 1
    ):

        training_metrics = run_gated_epoch(
            model=model,
            data_loader=train_loader,
            loss_function=loss_function,
            device=device,
            optimizer=optimizer,
            gradient_clip_norm=
                configuration.gradient_clip_norm
        )

        validation_metrics = run_gated_epoch(
            model=model,
            data_loader=validation_loader,
            loss_function=loss_function,
            device=device,
            optimizer=None,
            gradient_clip_norm=
                configuration.gradient_clip_norm
        )

        scheduler.step(
            validation_metrics["loss"]
        )

        learning_rate = (
            optimizer.param_groups[0]["lr"]
        )

        history_row = {
            "epoch": epoch,
            "learning_rate":
                learning_rate
        }

        for name, value in (
            training_metrics.items()
        ):
            history_row[
                f"train_{name}"
            ] = value

        for name, value in (
            validation_metrics.items()
        ):
            history_row[
                f"val_{name}"
            ] = value

        history.append(
            history_row
        )

        print(
            f"Epoch {epoch:02d}/"
            f"{configuration.maximum_epochs:02d} | "
            f"LR {learning_rate:.2e} | "
            f"Train Loss "
            f"{training_metrics['loss']:.4f} | "
            f"Val Loss "
            f"{validation_metrics['loss']:.4f} | "
            f"Val F1 "
            f"{validation_metrics['f1']:.4f} | "
            f"Val Recall "
            f"{validation_metrics['recall']:.4f} | "
            f"Val ROC-AUC "
            f"{validation_metrics['roc_auc']:.4f} | "
            f"Val AP "
            f"{validation_metrics['average_precision']:.4f} | "
            f"Gate "
            f"{validation_metrics['gate_mean']:.4f}"
        )

        current_average_precision = (
            validation_metrics[
                "average_precision"
            ]
        )

        improvement = (
            current_average_precision
            - best_average_precision
        )

        if (
            improvement
            > configuration.minimum_improvement
        ):

            best_average_precision = (
                current_average_precision
            )

            best_epoch = epoch

            best_validation_metrics = (
                validation_metrics.copy()
            )

            epochs_without_improvement = 0

            save_gated_checkpoint(
                path=checkpoint_path,
                model=model,
                configuration=configuration,
                visual_mean=visual_mean,
                visual_standard_deviation=
                    visual_std,
                class_weights=class_weights,
                epoch=epoch,
                validation_metrics=
                    validation_metrics
            )

            print(
                "  Best checkpoint updated."
            )

        else:

            epochs_without_improvement += 1

            print(
                "  No validation AP improvement "
                f"({epochs_without_improvement}/"
                f"{configuration.early_stopping_patience})."
            )

        if (
            epochs_without_improvement
            >= configuration.early_stopping_patience
        ):

            print()
            print(
                "Early stopping activated."
            )

            break

    pd.DataFrame(
        history
    ).to_csv(
        history_path,
        index=False
    )

    summary = {
        "model_name":
            "gated_fusion",

        "best_epoch":
            best_epoch,

        "best_validation_average_precision":
            best_average_precision,

        "best_validation_metrics":
            best_validation_metrics,

        "checkpoint_path":
            str(checkpoint_path),

        "history_path":
            str(history_path),

        "training_configuration":
            asdict(configuration)
    }

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            summary,
            output_file,
            indent=4
        )

    print()
    print("-" * 78)
    print("GATED FUSION TRAINING COMPLETE")
    print("-" * 78)

    print(
        "Best epoch:",
        best_epoch
    )

    for name, value in (
        best_validation_metrics.items()
    ):

        print(
            f"  {name:20}: "
            f"{value:.6f}"
        )

    print(
        "Checkpoint:",
        checkpoint_path
    )

    del model
    del optimizer
    del scheduler
    del train_loader
    del validation_loader
    del train_dataset
    del validation_dataset

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return summary


# =====================================================================
# Main
# =====================================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run only two epochs."
    )

    arguments = parser.parse_args()

    if arguments.smoke_test:

        configuration = TrainingConfig(
            maximum_epochs=2,
            early_stopping_patience=2
        )

    else:

        configuration = TrainingConfig(
            maximum_epochs=40,
            early_stopping_patience=7
        )

    print("=" * 78)
    print("PHASE 5.3 - ABLATION AND GATED TRAINING")
    print("=" * 78)

    print(
        "Mode:",
        (
            "SMOKE TEST"
            if arguments.smoke_test
            else "FULL TRAINING"
        )
    )

    set_random_seed(
        configuration.random_seed
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device:",
        device
    )

    validate_label_alignment()
    validate_split_isolation()

    ablation_specifications = [

        ModelSpecification(
            name="intention_only",

            train_path=(
                FEATURE_DIR
                / (
                    "train_intention_"
                    "enriched_features.npz"
                )
            ),

            validation_path=(
                FEATURE_DIR
                / (
                    "val_intention_"
                    "enriched_features.npz"
                )
            ),

            input_dimension=524,

            checkpoint_path=(
                OUTPUT_DIR
                / (
                    "intention_only_"
                    "transformer_best.pt"
                )
            ),

            history_path=(
                OUTPUT_DIR
                / (
                    "intention_only_"
                    "training_history.csv"
                )
            ),

            summary_path=(
                OUTPUT_DIR
                / (
                    "intention_only_"
                    "training_summary.json"
                )
            )
        ),

        ModelSpecification(
            name="reliability_only",

            train_path=(
                FEATURE_DIR
                / (
                    "train_reliability_"
                    "enriched_features.npz"
                )
            ),

            validation_path=(
                FEATURE_DIR
                / (
                    "val_reliability_"
                    "enriched_features.npz"
                )
            ),

            input_dimension=525,

            checkpoint_path=(
                OUTPUT_DIR
                / (
                    "reliability_only_"
                    "transformer_best.pt"
                )
            ),

            history_path=(
                OUTPUT_DIR
                / (
                    "reliability_only_"
                    "training_history.csv"
                )
            ),

            summary_path=(
                OUTPUT_DIR
                / (
                    "reliability_only_"
                    "training_summary.json"
                )
            )
        )
    ]

    summaries = []

    for specification in ablation_specifications:

        set_random_seed(
            configuration.random_seed
        )

        summary = train_model(
            specification=specification,
            configuration=configuration,
            device=device
        )

        summaries.append(
            summary
        )

    set_random_seed(
        configuration.random_seed
    )

    gated_summary = train_gated_model(
        configuration=configuration,
        device=device
    )

    summaries.append(
        gated_summary
    )

    combined_path = (
        OUTPUT_DIR
        / (
            "ablation_and_gated_"
            "training_summary.json"
        )
    )

    with open(
        combined_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        json.dump(
            summaries,
            output_file,
            indent=4
        )

    print()
    print("=" * 78)
    print("PHASE 5.3 TRAINING COMPLETE")
    print("=" * 78)

    print(
        "Combined summary:",
        combined_path
    )

    print(
        "The test split has not been used."
    )


if __name__ == "__main__":
    main()