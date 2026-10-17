from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import (
    DataLoader,
    TensorDataset,
)

from models.occlusion_estimator import (
    LearnedOcclusionEstimator,
)


DATA_DIR = Path(
    "datasets/processed/occlusion_estimator"
)
OUTPUT_DIR = Path(
    "outputs/phase9/occlusion_estimator"
)

CLASS_NAMES = [
    "none",
    "part",
    "full",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=12,
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=128,
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
    )

    return parser.parse_args()


def confusion_matrix(
    true: np.ndarray,
    pred: np.ndarray,
    num_classes: int = 3,
) -> np.ndarray:
    matrix = np.zeros(
        (
            num_classes,
            num_classes,
        ),
        dtype=np.int64,
    )

    for target, output in zip(
        true,
        pred,
    ):
        matrix[
            int(target),
            int(output),
        ] += 1

    return matrix


def metrics_from_cm(
    matrix: np.ndarray,
) -> dict:
    total = int(
        matrix.sum()
    )

    accuracy = (
        float(
            np.trace(matrix)
            / total
        )
        if total
        else 0.0
    )

    per_class = {}
    f1_values = []

    for index, name in enumerate(
        CLASS_NAMES
    ):
        tp = int(
            matrix[
                index,
                index,
            ]
        )
        fp = int(
            matrix[
                :,
                index,
            ].sum()
            - tp
        )
        fn = int(
            matrix[
                index,
                :,
            ].sum()
            - tp
        )

        precision = (
            tp / (tp + fp)
            if tp + fp
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else 0.0
        )

        f1 = (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
            if precision + recall
            else 0.0
        )

        f1_values.append(
            f1
        )

        per_class[name] = {
            "precision": float(
                precision
            ),
            "recall": float(
                recall
            ),
            "f1": float(f1),
            "support": int(
                matrix[
                    index,
                    :,
                ].sum()
            ),
        }

    return {
        "accuracy": accuracy,
        "macro_f1": float(
            np.mean(
                f1_values
            )
        ),
        "per_class": per_class,
    }


@torch.no_grad()
def evaluate(
    model,
    loader,
    device,
) -> tuple[
    float,
    np.ndarray,
    np.ndarray,
]:
    model.eval()

    losses = []
    targets = []
    outputs = []

    criterion = nn.CrossEntropyLoss()

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(
            device
        )
        y_batch = y_batch.to(
            device
        )

        logits = model(
            X_batch
        )

        loss = criterion(
            logits,
            y_batch,
        )

        losses.append(
            float(
                loss.item()
            )
        )

        predictions = (
            logits.argmax(
                dim=1
            )
            .detach()
            .cpu()
            .numpy()
        )

        targets.append(
            y_batch
            .detach()
            .cpu()
            .numpy()
        )

        outputs.append(
            predictions
        )

    return (
        float(
            np.mean(
                losses
            )
        ),
        np.concatenate(
            targets
        ),
        np.concatenate(
            outputs
        ),
    )


def main() -> None:
    args = parse_args()

    print("=" * 104)
    print(
        "PHASE 9.6B - TRAIN LEARNED "
        "AUTOMATIC OCCLUSION ESTIMATOR"
    )
    print("=" * 104)

    train_path = (
        DATA_DIR
        / "train_occlusion_features.npz"
    )
    val_path = (
        DATA_DIR
        / "val_occlusion_features.npz"
    )

    for path in (
        train_path,
        val_path,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing feature file: {path}"
            )

    with np.load(
        train_path
    ) as data:
        X_train = data[
            "X"
        ].astype(
            np.float32
        )
        y_train = data[
            "y"
        ].astype(
            np.int64
        )

    with np.load(
        val_path
    ) as data:
        X_val = data[
            "X"
        ].astype(
            np.float32
        )
        y_val = data[
            "y"
        ].astype(
            np.int64
        )

    mean = X_train.mean(
        axis=0
    ).astype(
        np.float32
    )

    std = X_train.std(
        axis=0
    ).astype(
        np.float32
    )

    std[
        std < 1e-6
    ] = 1.0

    X_train = (
        X_train
        - mean
    ) / std

    X_val = (
        X_val
        - mean
    ) / std

    counts = np.bincount(
        y_train,
        minlength=3,
    )

    class_weights = (
        len(y_train)
        / (
            3.0
            * np.maximum(
                counts,
                1,
            )
        )
    ).astype(
        np.float32
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device      :",
        device,
    )
    print(
        "Train shape :",
        X_train.shape,
    )
    print(
        "Val shape   :",
        X_val.shape,
    )
    print(
        "Train counts:",
        counts.tolist(),
    )
    print(
        "Class weights:",
        class_weights.tolist(),
    )

    train_dataset = TensorDataset(
        torch.from_numpy(
            X_train
        ),
        torch.from_numpy(
            y_train
        ),
    )

    val_dataset = TensorDataset(
        torch.from_numpy(
            X_val
        ),
        torch.from_numpy(
            y_val
        ),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=int(
            args.batch
        ),
        shuffle=True,
        num_workers=0,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=256,
        shuffle=False,
        num_workers=0,
    )

    model = (
        LearnedOcclusionEstimator()
        .to(device)
    )

    criterion = nn.CrossEntropyLoss(
        weight=torch.from_numpy(
            class_weights
        ).to(
            device
        )
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(
            args.lr
        ),
        weight_decay=1e-4,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = (
        OUTPUT_DIR
        / "learned_occlusion_estimator_best.pt"
    )

    best_macro_f1 = -1.0
    best_epoch = 0
    wait = 0
    history = []

    for epoch in range(
        1,
        int(args.epochs) + 1,
    ):
        model.train()

        batch_losses = []

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(
                device
            )
            y_batch = y_batch.to(
                device
            )

            optimizer.zero_grad(
                set_to_none=True
            )

            logits = model(
                X_batch
            )

            loss = criterion(
                logits,
                y_batch,
            )

            loss.backward()
            optimizer.step()

            batch_losses.append(
                float(
                    loss.item()
                )
            )

        (
            val_loss,
            val_true,
            val_pred,
        ) = evaluate(
            model,
            val_loader,
            device,
        )

        cm = confusion_matrix(
            val_true,
            val_pred,
        )

        metrics = metrics_from_cm(
            cm
        )

        train_loss = float(
            np.mean(
                batch_losses
            )
        )

        macro_f1 = float(
            metrics[
                "macro_f1"
            ]
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_accuracy": metrics[
                    "accuracy"
                ],
                "val_macro_f1": macro_f1,
            }
        )

        print(
            f"Epoch {epoch:03d} | "
            f"train loss {train_loss:.5f} | "
            f"val loss {val_loss:.5f} | "
            f"val acc {metrics['accuracy']:.4f} | "
            f"val macro-F1 {macro_f1:.4f}"
        )

        if macro_f1 > best_macro_f1:
            best_macro_f1 = (
                macro_f1
            )
            best_epoch = epoch
            wait = 0

            torch.save(
                {
                    "model_state_dict": (
                        model.state_dict()
                    ),
                    "feature_mean": mean,
                    "feature_std": std,
                    "class_names": (
                        CLASS_NAMES
                    ),
                    "input_dim": 518,
                    "best_epoch": (
                        best_epoch
                    ),
                    "best_val_macro_f1": (
                        best_macro_f1
                    ),
                },
                checkpoint_path,
            )
        else:
            wait += 1

        if wait >= int(
            args.patience
        ):
            print(
                "Early stopping at "
                f"epoch {epoch}."
            )
            break

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    (
        final_val_loss,
        val_true,
        val_pred,
    ) = evaluate(
        model,
        val_loader,
        device,
    )

    final_cm = confusion_matrix(
        val_true,
        val_pred,
    )

    final_metrics = metrics_from_cm(
        final_cm
    )

    summary = {
        "model_type": (
            "supervised 3-class MLP"
        ),
        "input_features": (
            "512 appearance + 6 spatial"
        ),
        "input_dimension": 518,
        "classes": CLASS_NAMES,
        "best_epoch": int(
            best_epoch
        ),
        "validation_loss": float(
            final_val_loss
        ),
        "validation_accuracy": float(
            final_metrics[
                "accuracy"
            ]
        ),
        "validation_macro_f1": float(
            final_metrics[
                "macro_f1"
            ]
        ),
        "validation_per_class": (
            final_metrics[
                "per_class"
            ]
        ),
        "confusion_matrix_rows_true_cols_pred": (
            final_cm.tolist()
        ),
        "checkpoint": str(
            checkpoint_path
        ),
        "important_note": (
            "No manual occlusion threshold "
            "is used at runtime; the class is "
            "the learned softmax argmax."
        ),
    }

    summary_path = (
        OUTPUT_DIR
        / "validation_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    history_path = (
        OUTPUT_DIR
        / "training_history.json"
    )

    history_path.write_text(
        json.dumps(
            history,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 104)
    print("FINAL VALIDATION")
    print("-" * 104)
    print(
        "Best epoch       :",
        best_epoch,
    )
    print(
        "Accuracy         :",
        f"{final_metrics['accuracy']:.6f}",
    )
    print(
        "Macro-F1         :",
        f"{final_metrics['macro_f1']:.6f}",
    )
    print(
        "Confusion matrix :"
    )
    print(
        final_cm
    )

    for name in CLASS_NAMES:
        values = (
            final_metrics[
                "per_class"
            ][name]
        )

        print(
            f"{name:5s} | "
            f"P={values['precision']:.4f} "
            f"R={values['recall']:.4f} "
            f"F1={values['f1']:.4f} "
            f"N={values['support']}"
        )

    print(
        "Checkpoint:",
        checkpoint_path,
    )
    print(
        "Summary   :",
        summary_path,
    )
    print(
        "Status    : PASSED"
    )
    print("=" * 104)


if __name__ == "__main__":
    main()
