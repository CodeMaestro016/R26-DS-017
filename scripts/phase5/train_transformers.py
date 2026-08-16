"""
Train Baseline and Bayesian-Enriched Transformer models.

Models
------
1. Baseline Transformer
   Input shape: (batch, 30, 522)

2. Bayesian-Enriched Transformer
   Input shape: (batch, 30, 527)

Important research rules
------------------------
- Normalization statistics are calculated from training data only.
- Validation data is not used for parameter training.
- Test data is not evaluated during training.
- The same architecture and training settings are used for both models.
- Training stops using validation Average Precision.
"""

from __future__ import annotations

import gc
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    precision_recall_fscore_support,
    roc_auc_score
)

from torch.utils.data import (
    DataLoader,
    Dataset
)

from models.transformer_intent_model import (
    TransformerIntentModel
)


# =====================================================================
# Paths
# =====================================================================

FEATURE_DIR = Path(
    "datasets/processed/features"
)

METADATA_DIR = Path(
    "datasets/processed/metadata"
)

OUTPUT_DIR = Path(
    "outputs/phase5"
)


# =====================================================================
# Training configuration
# =====================================================================

@dataclass
class TrainingConfig:

    sequence_length: int = 30
    num_classes: int = 2

    d_model: int = 128
    num_heads: int = 4
    num_layers: int = 2
    dim_feedforward: int = 256
    dropout: float = 0.2

    batch_size: int = 64
    maximum_epochs: int = 40

    learning_rate: float = 1e-4
    weight_decay: float = 1e-4

    gradient_clip_norm: float = 1.0

    scheduler_factor: float = 0.5
    scheduler_patience: int = 3

    early_stopping_patience: int = 7
    minimum_improvement: float = 1e-5

    random_seed: int = 42

    # Zero is safer for Windows.
    num_workers: int = 0


@dataclass
class ModelSpecification:

    name: str

    train_path: Path
    validation_path: Path

    input_dimension: int

    checkpoint_path: Path
    history_path: Path
    summary_path: Path


CONFIG = TrainingConfig()


MODEL_SPECIFICATIONS = [

    ModelSpecification(
        name="baseline",

        train_path=(
            FEATURE_DIR
            / "train_features.npz"
        ),

        validation_path=(
            FEATURE_DIR
            / "val_features.npz"
        ),

        input_dimension=522,

        checkpoint_path=(
            OUTPUT_DIR
            / "baseline_transformer_best.pt"
        ),

        history_path=(
            OUTPUT_DIR
            / "baseline_training_history.csv"
        ),

        summary_path=(
            OUTPUT_DIR
            / "baseline_training_summary.json"
        )
    ),

    ModelSpecification(
        name="enriched",

        train_path=(
            FEATURE_DIR
            / "train_enriched_features.npz"
        ),

        validation_path=(
            FEATURE_DIR
            / "val_enriched_features.npz"
        ),

        input_dimension=527,

        checkpoint_path=(
            OUTPUT_DIR
            / "enriched_transformer_best.pt"
        ),

        history_path=(
            OUTPUT_DIR
            / "enriched_training_history.csv"
        ),

        summary_path=(
            OUTPUT_DIR
            / "enriched_training_summary.json"
        )
    )
]


# =====================================================================
# Reproducibility
# =====================================================================

def set_random_seed(seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # Reproducible execution.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# =====================================================================
# Dataset
# =====================================================================

class NormalizedSequenceDataset(Dataset):

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        feature_mean: np.ndarray,
        feature_standard_deviation: np.ndarray
    ):

        self.features = torch.from_numpy(
            np.ascontiguousarray(
                features,
                dtype=np.float32
            )
        )

        self.labels = torch.from_numpy(
            np.ascontiguousarray(
                labels,
                dtype=np.int64
            )
        )

        self.feature_mean = torch.from_numpy(
            feature_mean.astype(
                np.float32,
                copy=False
            )
        ).view(1, -1)

        self.feature_standard_deviation = (
            torch.from_numpy(
                feature_standard_deviation.astype(
                    np.float32,
                    copy=False
                )
            ).view(1, -1)
        )

    def __len__(self) -> int:

        return len(self.labels)

    def __getitem__(self, index: int):

        feature_sequence = self.features[index]

        normalized_sequence = (
            feature_sequence
            - self.feature_mean
        ) / self.feature_standard_deviation

        label = self.labels[index]

        return normalized_sequence, label


# =====================================================================
# Input validation
# =====================================================================

def load_feature_file(
    path: Path,
    expected_input_dimension: int,
    sequence_length: int
):

    if not path.exists():

        raise FileNotFoundError(
            f"Feature file was not found: {path}"
        )

    with np.load(
        path,
        allow_pickle=True
    ) as data:

        if "X" not in data.files:

            raise KeyError(
                f"'X' key was not found in {path}"
            )

        if "y" not in data.files:

            raise KeyError(
                f"'y' key was not found in {path}"
            )

        features = data["X"].astype(
            np.float32,
            copy=False
        )

        labels = data["y"].astype(
            np.int64,
            copy=False
        )

    if features.ndim != 3:

        raise ValueError(
            f"{path}: expected a three-dimensional "
            f"array, but received {features.shape}."
        )

    if features.shape[1] != sequence_length:

        raise ValueError(
            f"{path}: expected sequence length "
            f"{sequence_length}, but received "
            f"{features.shape[1]}."
        )

    if features.shape[2] != expected_input_dimension:

        raise ValueError(
            f"{path}: expected input dimension "
            f"{expected_input_dimension}, but received "
            f"{features.shape[2]}."
        )

    if len(features) != len(labels):

        raise ValueError(
            f"{path}: feature and label counts "
            "do not match."
        )

    if not np.isfinite(features).all():

        raise ValueError(
            f"{path}: NaN or infinite feature "
            "values were detected."
        )

    label_states = set(
        np.unique(labels).tolist()
    )

    if not label_states.issubset({0, 1}):

        raise ValueError(
            f"{path}: unsupported label states "
            f"were found: {label_states}"
        )

    return features, labels


def validate_label_alignment() -> None:
    """
    Confirm that baseline and enriched datasets
    contain the same sequences and labels.
    """

    pairs = [
        (
            FEATURE_DIR / "train_features.npz",
            FEATURE_DIR / "train_enriched_features.npz",
            "train"
        ),
        (
            FEATURE_DIR / "val_features.npz",
            FEATURE_DIR / "val_enriched_features.npz",
            "validation"
        ),
        (
            FEATURE_DIR / "test_features.npz",
            FEATURE_DIR / "test_enriched_features.npz",
            "test"
        )
    ]

    for baseline_path, enriched_path, split_name in pairs:

        with np.load(
            baseline_path,
            allow_pickle=True
        ) as baseline_data:

            baseline_labels = baseline_data["y"]

        with np.load(
            enriched_path,
            allow_pickle=True
        ) as enriched_data:

            enriched_labels = enriched_data["y"]

        if not np.array_equal(
            baseline_labels,
            enriched_labels
        ):

            raise ValueError(
                f"Baseline and enriched labels do not "
                f"match for the {split_name} split."
            )


def load_pedestrian_groups(
    split_name: str
) -> set[str]:

    metadata_path = (
        METADATA_DIR
        / f"{split_name}.csv"
    )

    if not metadata_path.exists():

        raise FileNotFoundError(
            f"Metadata file was not found: "
            f"{metadata_path}"
        )

    metadata = pd.read_csv(
        metadata_path,
        dtype={
            "video": str,
            "pedestrian_id": str
        }
    )

    groups = set(
        (
            metadata["video"].astype(str)
            + "::"
            + metadata[
                "pedestrian_id"
            ].astype(str)
        ).tolist()
    )

    return groups


def validate_split_isolation() -> None:
    """
    Ensure that the same pedestrian does not occur
    across train, validation and test splits.
    """

    train_groups = load_pedestrian_groups(
        "train"
    )

    validation_groups = load_pedestrian_groups(
        "val"
    )

    test_groups = load_pedestrian_groups(
        "test"
    )

    train_validation_overlap = (
        train_groups
        & validation_groups
    )

    train_test_overlap = (
        train_groups
        & test_groups
    )

    validation_test_overlap = (
        validation_groups
        & test_groups
    )

    if train_validation_overlap:

        raise ValueError(
            "Pedestrian leakage was detected between "
            "train and validation splits. Examples: "
            f"{list(train_validation_overlap)[:10]}"
        )

    if train_test_overlap:

        raise ValueError(
            "Pedestrian leakage was detected between "
            "train and test splits. Examples: "
            f"{list(train_test_overlap)[:10]}"
        )

    if validation_test_overlap:

        raise ValueError(
            "Pedestrian leakage was detected between "
            "validation and test splits. Examples: "
            f"{list(validation_test_overlap)[:10]}"
        )

    print()
    print("Split isolation check passed.")

    print(
        "Train pedestrian groups      :",
        len(train_groups)
    )

    print(
        "Validation pedestrian groups :",
        len(validation_groups)
    )

    print(
        "Test pedestrian groups       :",
        len(test_groups)
    )


# =====================================================================
# Normalization
# =====================================================================

def calculate_training_normalizer(
    training_features: np.ndarray
):

    print()
    print(
        "Calculating training-only "
        "normalization statistics..."
    )

    feature_mean = np.mean(
        training_features,
        axis=(0, 1),
        dtype=np.float64
    ).astype(
        np.float32
    )

    feature_standard_deviation = np.std(
        training_features,
        axis=(0, 1),
        dtype=np.float64
    ).astype(
        np.float32
    )

    near_constant_mask = (
        feature_standard_deviation < 1e-6
    )

    near_constant_count = int(
        near_constant_mask.sum()
    )

    # Prevent division by zero.
    feature_standard_deviation[
        near_constant_mask
    ] = 1.0

    print(
        "Near-constant feature dimensions:",
        near_constant_count
    )

    return (
        feature_mean,
        feature_standard_deviation
    )


# =====================================================================
# Class imbalance
# =====================================================================

def calculate_class_weights(
    training_labels: np.ndarray,
    device: torch.device
):

    class_counts = np.bincount(
        training_labels,
        minlength=2
    ).astype(
        np.float64
    )

    if np.any(class_counts == 0):

        raise ValueError(
            "At least one class has zero training "
            f"samples: {class_counts.tolist()}"
        )

    total_samples = float(
        class_counts.sum()
    )

    number_of_classes = len(
        class_counts
    )

    class_weights = (
        total_samples
        / (
            number_of_classes
            * class_counts
        )
    ).astype(
        np.float32
    )

    print()
    print(
        "Training class counts:",
        class_counts.astype(int).tolist()
    )

    print(
        "Automatic class weights:",
        class_weights.tolist()
    )

    return torch.tensor(
        class_weights,
        dtype=torch.float32,
        device=device
    )


# =====================================================================
# Metrics
# =====================================================================

def calculate_metrics(
    labels: np.ndarray,
    predictions: np.ndarray,
    positive_probabilities: np.ndarray
):

    accuracy = accuracy_score(
        labels,
        predictions
    )

    precision, recall, f1_score, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="binary",
            pos_label=1,
            zero_division=0
        )
    )

    unique_labels = np.unique(
        labels
    )

    if len(unique_labels) == 2:

        roc_auc = roc_auc_score(
            labels,
            positive_probabilities
        )

        average_precision = (
            average_precision_score(
                labels,
                positive_probabilities
            )
        )

    else:

        roc_auc = float("nan")
        average_precision = float("nan")

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1_score),
        "roc_auc": float(roc_auc),
        "average_precision":
            float(average_precision)
    }


# =====================================================================
# Train / validation epoch
# =====================================================================

def run_epoch(
    model: nn.Module,
    data_loader: DataLoader,
    loss_function: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    gradient_clip_norm: float
):

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_samples = 0

    all_labels = []
    all_predictions = []
    all_positive_probabilities = []

    for feature_sequences, labels in data_loader:

        feature_sequences = feature_sequences.to(
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

            logits = model(
                feature_sequences
            )

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

        batch_size = labels.shape[0]

        total_loss += (
            float(loss.item())
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

    return metrics


# =====================================================================
# DataLoaders
# =====================================================================

def create_data_loader(
    dataset: Dataset,
    batch_size: int,
    shuffle: bool,
    seed: int,
    num_workers: int,
    pin_memory: bool
):

    generator = torch.Generator()

    generator.manual_seed(
        seed
    )

    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        generator=generator,
        drop_last=False
    )


# =====================================================================
# Checkpoint
# =====================================================================

def save_best_checkpoint(
    path: Path,
    model: nn.Module,
    model_specification: ModelSpecification,
    configuration: TrainingConfig,
    feature_mean: np.ndarray,
    feature_standard_deviation: np.ndarray,
    class_weights: torch.Tensor,
    epoch: int,
    validation_metrics: dict
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cpu_state_dictionary = {
        name: parameter.detach().cpu()
        for name, parameter
        in model.state_dict().items()
    }

    checkpoint = {
        "model_name":
            model_specification.name,

        "model_state_dict":
            cpu_state_dictionary,

        "input_dimension":
            model_specification.input_dimension,

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

            "dropout":
                configuration.dropout
        },

        "training_configuration":
            asdict(configuration),

        "feature_mean":
            torch.from_numpy(
                feature_mean
            ),

        "feature_standard_deviation":
            torch.from_numpy(
                feature_standard_deviation
            ),

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
# Model training
# =====================================================================

def train_model(
    specification: ModelSpecification,
    configuration: TrainingConfig,
    device: torch.device
):

    print()
    print("=" * 78)
    print(
        f"TRAINING {specification.name.upper()} "
        "TRANSFORMER"
    )
    print("=" * 78)

    training_features, training_labels = (
        load_feature_file(
            path=specification.train_path,
            expected_input_dimension=
                specification.input_dimension,
            sequence_length=
                configuration.sequence_length
        )
    )

    validation_features, validation_labels = (
        load_feature_file(
            path=specification.validation_path,
            expected_input_dimension=
                specification.input_dimension,
            sequence_length=
                configuration.sequence_length
        )
    )

    print(
        "Training shape   :",
        training_features.shape
    )

    print(
        "Validation shape :",
        validation_features.shape
    )

    feature_mean, feature_standard_deviation = (
        calculate_training_normalizer(
            training_features
        )
    )

    training_dataset = (
        NormalizedSequenceDataset(
            features=training_features,
            labels=training_labels,
            feature_mean=feature_mean,
            feature_standard_deviation=
                feature_standard_deviation
        )
    )

    validation_dataset = (
        NormalizedSequenceDataset(
            features=validation_features,
            labels=validation_labels,
            feature_mean=feature_mean,
            feature_standard_deviation=
                feature_standard_deviation
        )
    )

    pin_memory = (
        device.type == "cuda"
    )

    training_loader = create_data_loader(
        dataset=training_dataset,
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
        training_labels=training_labels,
        device=device
    )

    model = TransformerIntentModel(
        input_dim=
            specification.input_dimension,

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

        training_metrics = run_epoch(
            model=model,
            data_loader=training_loader,
            loss_function=loss_function,
            device=device,
            optimizer=optimizer,
            gradient_clip_norm=
                configuration.gradient_clip_norm
        )

        validation_metrics = run_epoch(
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

        current_learning_rate = (
            optimizer.param_groups[0]["lr"]
        )

        history_row = {
            "epoch": epoch,
            "learning_rate":
                current_learning_rate
        }

        for metric_name, metric_value in (
            training_metrics.items()
        ):

            history_row[
                f"train_{metric_name}"
            ] = metric_value

        for metric_name, metric_value in (
            validation_metrics.items()
        ):

            history_row[
                f"val_{metric_name}"
            ] = metric_value

        history.append(
            history_row
        )

        print(
            f"Epoch {epoch:02d}/"
            f"{configuration.maximum_epochs:02d} | "
            f"LR {current_learning_rate:.2e} | "
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
            f"{validation_metrics['average_precision']:.4f}"
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

            save_best_checkpoint(
                path=
                    specification.checkpoint_path,

                model=model,

                model_specification=
                    specification,

                configuration=
                    configuration,

                feature_mean=
                    feature_mean,

                feature_standard_deviation=
                    feature_standard_deviation,

                class_weights=
                    class_weights,

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

    history_dataframe = pd.DataFrame(
        history
    )

    specification.history_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    history_dataframe.to_csv(
        specification.history_path,
        index=False
    )

    summary = {
        "model_name":
            specification.name,

        "input_dimension":
            specification.input_dimension,

        "best_epoch":
            best_epoch,

        "best_validation_average_precision":
            best_average_precision,

        "best_validation_metrics":
            best_validation_metrics,

        "checkpoint_path":
            str(specification.checkpoint_path),

        "history_path":
            str(specification.history_path),

        "training_configuration":
            asdict(configuration)
    }

    with open(
        specification.summary_path,
        "w",
        encoding="utf-8"
    ) as summary_file:

        json.dump(
            summary,
            summary_file,
            indent=4
        )

    print()
    print("-" * 78)
    print(
        f"{specification.name.upper()} "
        "TRAINING COMPLETE"
    )
    print("-" * 78)

    print(
        "Best epoch:",
        best_epoch
    )

    print(
        "Best validation metrics:"
    )

    for metric_name, metric_value in (
        best_validation_metrics.items()
    ):

        print(
            f"  {metric_name:20}: "
            f"{metric_value:.6f}"
        )

    print(
        "Checkpoint:",
        specification.checkpoint_path
    )

    print(
        "History:",
        specification.history_path
    )

    # Release model-specific memory before training
    # the next Transformer.
    del model
    del optimizer
    del scheduler
    del loss_function

    del training_dataset
    del validation_dataset

    del training_loader
    del validation_loader

    del training_features
    del validation_features

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return summary


# =====================================================================
# Main
# =====================================================================

def main():

    print("=" * 78)
    print("PHASE 5.2 - TRANSFORMER TRAINING")
    print("=" * 78)

    set_random_seed(
        CONFIG.random_seed
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "PyTorch version:",
        torch.__version__
    )

    print(
        "Selected device:",
        device
    )

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    validate_label_alignment()

    print()
    print(
        "Baseline/enriched label "
        "alignment check passed."
    )

    validate_split_isolation()

    summaries = []

    for specification in MODEL_SPECIFICATIONS:

        # Reset the seed before each model to make
        # the comparison more reproducible.
        set_random_seed(
            CONFIG.random_seed
        )

        summary = train_model(
            specification=specification,
            configuration=CONFIG,
            device=device
        )

        summaries.append(
            summary
        )

    combined_summary_path = (
        OUTPUT_DIR
        / "transformer_training_summary.json"
    )

    with open(
        combined_summary_path,
        "w",
        encoding="utf-8"
    ) as summary_file:

        json.dump(
            summaries,
            summary_file,
            indent=4
        )

    print()
    print("=" * 78)
    print("PHASE 5.2 TRAINING COMPLETE")
    print("=" * 78)

    print(
        "Baseline checkpoint:",
        MODEL_SPECIFICATIONS[
            0
        ].checkpoint_path
    )

    print(
        "Enriched checkpoint:",
        MODEL_SPECIFICATIONS[
            1
        ].checkpoint_path
    )

    print(
        "Combined summary:",
        combined_summary_path
    )

    print()
    print(
        "The test split has not been used."
    )


if __name__ == "__main__":
    main()