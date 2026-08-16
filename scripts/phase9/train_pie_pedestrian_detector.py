from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from ultralytics import YOLO


DATA_YAML = Path(
    "datasets/processed/yolo_pedestrian/data.yaml"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "outputs"
    / "phase9"
    / "yolo_pedestrian"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune a one-class PIE pedestrian detector."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="Pretrained Ultralytics detector checkpoint.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=960,
        help="Training image size. 960 is the V1 default for small PIE pedestrians.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=-1,
        help="Ultralytics auto-batch by default. Use an integer to force a batch size.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Windows-safe default.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="yolo11n_pie_occlusion_v1",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a short 1-epoch, 2%%-dataset GPU smoke test.",
    )
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Allow training without CUDA. Not recommended for the full dataset.",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Path to a prior last.pt checkpoint to resume.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 108)
    print("PHASE 9.5B - PIE OCCLUSION-AWARE PEDESTRIAN DETECTOR FINE-TUNING")
    print("=" * 108)

    if not DATA_YAML.exists():
        raise FileNotFoundError(
            f"Missing dataset YAML: {DATA_YAML}. Run Phase 9.5A first."
        )

    cuda_available = bool(torch.cuda.is_available())

    print("PyTorch        :", torch.__version__)
    print("CUDA available :", cuda_available)

    if cuda_available:
        print("GPU             :", torch.cuda.get_device_name(0))
        props = torch.cuda.get_device_properties(0)
        print("GPU VRAM GiB    :", f"{props.total_memory / (1024**3):.2f}")
    elif not args.allow_cpu:
        raise RuntimeError(
            "CUDA is not available in this environment. "
            "Use the separate GPU training environment, or pass --allow-cpu "
            "only for a deliberately slow CPU run."
        )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    if args.resume is not None:
        if not args.resume.exists():
            raise FileNotFoundError(f"Resume checkpoint not found: {args.resume}")

        model = YOLO(str(args.resume))
        print("Resuming from   :", args.resume)

        results = model.train(resume=True)
        print("Resume call completed.")
        print(results)
        return

    model = YOLO(args.model)

    smoke = bool(args.smoke)

    epochs = 1 if smoke else int(args.epochs)
    fraction = 0.02 if smoke else 1.0
    name = f"{args.name}_smoke" if smoke else args.name

    # A 4 GB laptop GPU is memory-constrained. AMP is kept on and auto-batch
    # is the default. imgsz=960 is selected to retain more detail for small
    # pedestrians; reduce to 768 if the smoke test OOMs.
    train_args = dict(
        data=str(DATA_YAML),
        epochs=epochs,
        patience=int(args.patience),
        imgsz=int(args.imgsz),
        batch=args.batch,
        device=0 if cuda_available else "cpu",
        workers=int(args.workers),
        amp=True,
        cache=False,
        fraction=fraction,
        pretrained=True,
        val=True,
        plots=True,
        save=True,
        save_period=5 if not smoke else -1,
        project=str(OUTPUT_ROOT),
        name=name,
        exist_ok=False,
        seed=42,
        deterministic=True,
        close_mosaic=5 if not smoke else 0,
        verbose=True,
    )

    config_path = OUTPUT_ROOT / f"{name}_requested_config.json"
    config_path.write_text(
        json.dumps(
            {
                "model": args.model,
                "data": str(DATA_YAML),
                "cuda_available": cuda_available,
                "gpu": (
                    torch.cuda.get_device_name(0)
                    if cuda_available else None
                ),
                "smoke": smoke,
                **train_args,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("Training configuration:")
    for key, value in train_args.items():
        print(f"  {key}: {value}")

    print()
    print("Starting training...")
    results = model.train(**train_args)

    print()
    print("-" * 108)
    print("TRAINING COMPLETED")
    print("-" * 108)
    print("Requested config:", config_path)
    print("Ultralytics save directory:", getattr(results, "save_dir", "see console output"))
    print("=" * 108)


if __name__ == "__main__":
    main()
