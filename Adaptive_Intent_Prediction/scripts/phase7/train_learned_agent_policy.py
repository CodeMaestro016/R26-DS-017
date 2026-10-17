from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, TensorDataset

from utils.learned_agent_policy import ACTION_NAMES, AgentPolicyMLP


TRAIN_CSV = Path("outputs/phase7/agent_policy_train.csv")
DEV_CSV = Path("outputs/phase7/agent_policy_dev.csv")
MANIFEST = Path("outputs/phase7/agent_state_manifest.json")
OUT = Path("outputs/phase7")

CHECKPOINT = OUT / "learned_agent_policy_best.pt"
DEV_PREDICTIONS = OUT / "agent_policy_dev_predictions.csv"
METRICS_JSON = OUT / "agent_policy_dev_metrics.json"
TRAIN_HISTORY = OUT / "agent_policy_training_history.csv"

SEED = 42
BATCH_SIZE = 64
MAX_EPOCHS = 250
PATIENCE = 30
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
HIDDEN_1 = 64
HIDDEN_2 = 32
DROPOUT = 0.20


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def standardize_fit(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0).astype(np.float32)
    std = x.std(axis=0).astype(np.float32)

    # Constant features are left numerically stable.
    std[std < 1e-8] = 1.0

    return ((x - mean) / std).astype(np.float32), mean, std


def standardize_apply(
    x: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    return ((x - mean) / std).astype(np.float32)


def selective_metrics(
    frame: pd.DataFrame,
    predicted_actions: np.ndarray,
) -> dict:
    true_intent = frame["true_intent"].to_numpy(dtype=np.int64)
    frozen_prediction = frame["frozen_intent_prediction"].to_numpy(dtype=np.int64)
    frozen_correct = frame["frozen_prediction_correct"].to_numpy(dtype=np.int64) == 1

    commits = predicted_actions != 0

    committed_intent = np.full(len(frame), -1, dtype=np.int64)
    committed_intent[predicted_actions == 1] = 0
    committed_intent[predicted_actions == 2] = 1

    commit_correct = commits & (committed_intent == true_intent)
    commit_wrong = commits & (committed_intent != true_intent)

    errors = ~frozen_correct
    correct_base = frozen_correct

    coverage = float(commits.mean())

    if commits.any():
        committed_accuracy = float(commit_correct[commits].mean())
    else:
        committed_accuracy = float("nan")

    if errors.any():
        error_capture_recall = float((predicted_actions[errors] == 0).mean())
    else:
        error_capture_recall = float("nan")

    if correct_base.any():
        unnecessary_deferral_rate = float(
            (predicted_actions[correct_base] == 0).mean()
        )
    else:
        unnecessary_deferral_rate = float("nan")

    baseline_accuracy = float(
        (frozen_prediction == true_intent).mean()
    )

    return {
        "baseline_frozen_intent_accuracy": baseline_accuracy,
        "agent_commit_coverage": coverage,
        "agent_deferral_rate": float((predicted_actions == 0).mean()),
        "agent_committed_accuracy": committed_accuracy,
        "agent_unsafe_commit_rate_overall": float(commit_wrong.mean()),
        "agent_error_capture_recall": error_capture_recall,
        "agent_unnecessary_deferral_rate": unnecessary_deferral_rate,
        "agent_correct_commit_rate_overall": float(commit_correct.mean()),
    }


def main() -> None:
    seed_everything(SEED)

    print("=" * 88)
    print("PHASE 7.2 - TRAIN NON-RULE-BASED LEARNED AGENT POLICY")
    print("=" * 88)

    for path in (TRAIN_CSV, DEV_CSV, MANIFEST):
        if not path.exists():
            raise FileNotFoundError(
                f"Required Phase-7.1 output not found: {path}"
            )

    train_df = pd.read_csv(TRAIN_CSV)
    dev_df = pd.read_csv(DEV_CSV)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    state_features = list(manifest["state_features"])

    missing_train = [c for c in state_features if c not in train_df.columns]
    missing_dev = [c for c in state_features if c not in dev_df.columns]

    if missing_train or missing_dev:
        raise KeyError(
            f"Missing state features. train={missing_train}, dev={missing_dev}"
        )

    train_pedestrians = set(train_df["pedestrian_id"].astype(str))
    dev_pedestrians = set(dev_df["pedestrian_id"].astype(str))
    overlap = train_pedestrians & dev_pedestrians

    if overlap:
        raise RuntimeError(
            f"Pedestrian leakage detected: {sorted(overlap)}"
        )

    x_train_raw = train_df[state_features].to_numpy(dtype=np.float32)
    x_dev_raw = dev_df[state_features].to_numpy(dtype=np.float32)

    y_train = train_df["agent_action"].to_numpy(dtype=np.int64)
    y_dev = dev_df["agent_action"].to_numpy(dtype=np.int64)

    x_train, mean, std = standardize_fit(x_train_raw)
    x_dev = standardize_apply(x_dev_raw, mean, std)

    classes = np.array([0, 1, 2], dtype=np.int64)

    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train,
    ).astype(np.float32)

    print("State features :", len(state_features))
    print("Train rows     :", len(train_df))
    print("Dev rows       :", len(dev_df))
    print("Train peds     :", len(train_pedestrians))
    print("Dev peds       :", len(dev_pedestrians))
    print("Ped overlap    :", len(overlap))
    print()
    print("Training action distribution:")
    for action_id in classes:
        count = int((y_train == action_id).sum())
        print(
            f"  {ACTION_NAMES[int(action_id)]:24s}: "
            f"{count:4d} | class weight {class_weights[action_id]:.4f}"
        )

    train_dataset = TensorDataset(
        torch.from_numpy(x_train),
        torch.from_numpy(y_train),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    device = torch.device("cpu")

    model = AgentPolicyMLP(
        input_dim=len(state_features),
        hidden_dim_1=HIDDEN_1,
        hidden_dim_2=HIDDEN_2,
        dropout=DROPOUT,
    ).to(device)

    criterion = nn.CrossEntropyLoss(
        weight=torch.from_numpy(class_weights).to(device)
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    x_dev_tensor = torch.from_numpy(x_dev).to(device)

    best_macro_f1 = -np.inf
    best_epoch = -1
    best_state = None
    epochs_without_improvement = 0
    history = []

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()

        losses = []

        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad(set_to_none=True)

            logits = model(batch_x)
            loss = criterion(logits, batch_y)

            loss.backward()
            optimizer.step()

            losses.append(float(loss.item()))

        model.eval()

        with torch.no_grad():
            dev_logits = model(x_dev_tensor)
            dev_pred = dev_logits.argmax(dim=1).cpu().numpy()

        dev_accuracy = accuracy_score(y_dev, dev_pred)
        dev_macro_f1 = f1_score(
            y_dev,
            dev_pred,
            average="macro",
            zero_division=0,
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": float(np.mean(losses)),
                "dev_accuracy": float(dev_accuracy),
                "dev_macro_f1": float(dev_macro_f1),
            }
        )

        if dev_macro_f1 > best_macro_f1 + 1e-6:
            best_macro_f1 = float(dev_macro_f1)
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if epoch == 1 or epoch % 10 == 0:
            print(
                f"Epoch {epoch:03d} | "
                f"loss {np.mean(losses):.6f} | "
                f"dev acc {dev_accuracy:.6f} | "
                f"dev macro-F1 {dev_macro_f1:.6f}"
            )

        if epochs_without_improvement >= PATIENCE:
            print(
                f"Early stopping at epoch {epoch}; "
                f"best epoch = {best_epoch}"
            )
            break

    if best_state is None:
        raise RuntimeError("No best model state was selected.")

    model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():
        dev_logits = model(x_dev_tensor)
        dev_prob = torch.softmax(dev_logits, dim=1).cpu().numpy()
        dev_pred = dev_prob.argmax(axis=1)

    dev_accuracy = float(accuracy_score(y_dev, dev_pred))
    dev_macro_f1 = float(
        f1_score(
            y_dev,
            dev_pred,
            average="macro",
            zero_division=0,
        )
    )

    report = classification_report(
        y_dev,
        dev_pred,
        labels=[0, 1, 2],
        target_names=[
            ACTION_NAMES[0],
            ACTION_NAMES[1],
            ACTION_NAMES[2],
        ],
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(
        y_dev,
        dev_pred,
        labels=[0, 1, 2],
    )

    select_metrics = selective_metrics(
        dev_df,
        dev_pred,
    )

    checkpoint = {
        "phase": "7.2",
        "policy_type": "learned_supervised_selective_agent",
        "model_state_dict": model.state_dict(),
        "state_features": state_features,
        "normalization_mean": mean.tolist(),
        "normalization_std": std.tolist(),
        "architecture": {
            "input_dim": len(state_features),
            "hidden_dim_1": HIDDEN_1,
            "hidden_dim_2": HIDDEN_2,
            "dropout": DROPOUT,
        },
        "action_mapping": ACTION_NAMES,
        "best_epoch": best_epoch,
        "best_dev_macro_f1": best_macro_f1,
        "class_weights": class_weights.tolist(),
        "seed": SEED,
        "official_test_used": False,
    }

    torch.save(checkpoint, CHECKPOINT)

    prediction_frame = dev_df.copy()
    prediction_frame["agent_predicted_action"] = dev_pred
    prediction_frame["agent_predicted_action_name"] = [
        ACTION_NAMES[int(value)] for value in dev_pred
    ]

    for action_id in (0, 1, 2):
        prediction_frame[
            f"agent_probability_{ACTION_NAMES[action_id].lower()}"
        ] = dev_prob[:, action_id]

    prediction_frame.to_csv(
        DEV_PREDICTIONS,
        index=False,
    )

    pd.DataFrame(history).to_csv(
        TRAIN_HISTORY,
        index=False,
    )

    metrics_payload = {
        "best_epoch": best_epoch,
        "action_accuracy": dev_accuracy,
        "action_macro_f1": dev_macro_f1,
        "confusion_matrix_action_order_0_1_2": cm.tolist(),
        "classification_report": report,
        "selective_metrics": select_metrics,
        "official_test_used": False,
    }

    METRICS_JSON.write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 88)
    print("BEST DEV RESULT")
    print("-" * 88)
    print("Best epoch       :", best_epoch)
    print("Action accuracy  :", f"{dev_accuracy:.6f}")
    print("Action macro-F1  :", f"{dev_macro_f1:.6f}")
    print()
    print("Confusion matrix [rows=true, cols=pred] order:")
    print("0 OBSERVE_MORE, 1 COMMIT_NOT_CROSSING, 2 COMMIT_CROSSING")
    print(cm)

    print()
    print("-" * 88)
    print("SELECTIVE POLICY METRICS ON AGENT DEV")
    print("-" * 88)
    for key, value in select_metrics.items():
        if isinstance(value, float) and np.isfinite(value):
            print(f"{key:38s}: {value:.6f}")
        else:
            print(f"{key:38s}: {value}")

    print()
    print("-" * 88)
    print("OUTPUTS")
    print("-" * 88)
    print(CHECKPOINT)
    print(DEV_PREDICTIONS)
    print(METRICS_JSON)
    print(TRAIN_HISTORY)
    print()
    print(
        "NOTE: The policy uses learned softmax argmax actions. "
        "No manually coded confidence/probability threshold is used."
    )
    print(
        "OBSERVE_MORE means defer the current intent commitment and "
        "re-evaluate when the next rolling observation window arrives."
    )
    print("Status: PASSED")
    print("=" * 88)


if __name__ == "__main__":
    main()
