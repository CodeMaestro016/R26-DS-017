from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from ultralytics import YOLO


DATA_YAML = Path("datasets/processed/yolo_pedestrian/data.yaml")
DEFAULT_MODEL = Path(
    "outputs/phase9/yolo_pedestrian/"
    "yolo11n_pie_occlusion_v1/weights/best.pt"
)
OUTPUT_DIR = Path("outputs/phase9/yolo_pedestrian/final_validation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=960,
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.001,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 104)
    print("PHASE 9.5B - CUSTOM PIE PEDESTRIAN DETECTOR VALIDATION")
    print("=" * 104)

    if not args.model.exists():
        raise FileNotFoundError(
            f"Detector checkpoint not found: {args.model}"
        )

    if not DATA_YAML.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found: {DATA_YAML}"
        )

    device = 0 if torch.cuda.is_available() else "cpu"

    model = YOLO(str(args.model))

    metrics = model.val(
        data=str(DATA_YAML),
        split="val",
        imgsz=int(args.imgsz),
        conf=float(args.conf),
        iou=0.7,
        device=device,
        workers=0,
        plots=True,
        project=str(OUTPUT_DIR.parent),
        name=OUTPUT_DIR.name,
        exist_ok=True,
    )

    box = metrics.box

    summary = {
        "model": str(args.model),
        "data": str(DATA_YAML),
        "imgsz": int(args.imgsz),
        "device": str(device),
        "precision": float(box.mp),
        "recall": float(box.mr),
        "map50": float(box.map50),
        "map50_95": float(box.map),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_DIR / "validation_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 104)
    print("VALIDATION SUMMARY")
    print("-" * 104)
    print("Precision :", f"{summary['precision']:.6f}")
    print("Recall    :", f"{summary['recall']:.6f}")
    print("mAP@0.50  :", f"{summary['map50']:.6f}")
    print("mAP@.50:.95:", f"{summary['map50_95']:.6f}")
    print("Saved     :", summary_path)
    print("=" * 104)


if __name__ == "__main__":
    main()
