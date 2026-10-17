# Adaptive Intent Prediction in Occluded Urban Scenarios

Research implementation for predicting pedestrian crossing intent in urban
scenes when pedestrians are partially or temporarily occluded. The project
combines visual tracking, motion and spatial features, occlusion estimation,
Bayesian reliability modelling, deep intent prediction, uncertainty
estimation, and decision explanations.

## Repository

- Repository: `CodeMaestro016/R26-DS-017`
- Active development branch: `IT22245960/piyumal_updated`
- Recommended Python version: **3.11.x**

## Project layout

All implementation files are under [`Adaptive_Intent_Prediction/`](./Adaptive_Intent_Prediction/).

| Directory | Purpose |
| --- | --- |
| [`configs/`](./Adaptive_Intent_Prediction/configs/) | Dataset and occlusion configuration |
| [`models/`](./Adaptive_Intent_Prediction/models/) | Intent prediction and occlusion-estimation models |
| [`utils/`](./Adaptive_Intent_Prediction/utils/) | Feature extraction, tracking, mapping, inference, and explanation utilities |
| [`scripts/phase1/`](./Adaptive_Intent_Prediction/scripts/phase1/) | Dataset preparation and sequence creation |
| [`scripts/phase2/`](./Adaptive_Intent_Prediction/scripts/phase2/) | Occlusion generation and validation |
| [`scripts/phase3/`](./Adaptive_Intent_Prediction/scripts/phase3/) | Visual, motion, spatial, and sequence feature extraction |
| [`scripts/phase4/`](./Adaptive_Intent_Prediction/scripts/phase4/) | Bayesian feature generation and network training |
| [`scripts/phase5/`](./Adaptive_Intent_Prediction/scripts/phase5/) | Gated-fusion and transformer model training/evaluation |
| [`scripts/phase6/`](./Adaptive_Intent_Prediction/scripts/phase6/) | Calibration and uncertainty evaluation |
| [`scripts/phase7/`](./Adaptive_Intent_Prediction/scripts/phase7/) | Learned agent policy preparation and evaluation |
| [`scripts/phase8/`](./Adaptive_Intent_Prediction/scripts/phase8/) | Agent decision explanations |
| [`scripts/phase9/`](./Adaptive_Intent_Prediction/scripts/phase9/) | PIE/YOLO pedestrian detection and runtime pipeline |
| [`scripts/demo/`](./Adaptive_Intent_Prediction/scripts/demo/) | Runtime and held-out demonstration scripts |
| [`notebooks/`](./Adaptive_Intent_Prediction/notebooks/) | Research experiments |

## Setup

From the repository root, enter the project directory:

```powershell
cd Adaptive_Intent_Prediction
```

Create and activate a Python 3.11 virtual environment. On Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install PyTorch first. Use the command that matches the target machine:

```powershell
# NVIDIA GPU
python -m pip install torch==2.12.1 torchvision==0.27.1 `
  --index-url https://download.pytorch.org/whl/cu130

# CPU only
python -m pip install torch==2.12.1 torchvision==0.27.1 `
  --index-url https://download.pytorch.org/whl/cpu
```

Install the remaining dependencies:

```powershell
python -m pip install -r requirements.txt
```

CARLA is intentionally not pinned in `requirements.txt`. Install the CARLA
Python client separately and make sure its version matches the CARLA
simulator installed on the target machine.

## Data and model files

Datasets, generated outputs, local virtual environments, pretrained weights,
and generated archives are intentionally excluded from Git using the root
[`.gitignore`](./.gitignore). This keeps the repository lightweight and avoids
committing machine-specific or large research artifacts.

Before running data-dependent scripts, place the required local files in the
expected directories under:

- [`datasets/`](./Adaptive_Intent_Prediction/datasets/) - raw and processed data
- [`inputs/`](./Adaptive_Intent_Prediction/inputs/) - demo and runtime inputs
- [`outputs/`](./Adaptive_Intent_Prediction/outputs/) - generated results

These directories are local-only and are not supplied by this repository.
Pretrained model weights such as YOLO `.pt` files must also be downloaded or
generated locally.

## Running scripts

Run commands from inside `Adaptive_Intent_Prediction` so that the project
relative paths used by the scripts resolve correctly. For example:

```powershell
python scripts\phase1\parse_annotations.py
python scripts\phase2\generate_occlusions.py
python scripts\phase4\train_bayesian_network.py
python scripts\phase5\train_transformers.py
python scripts\phase6\calibrate_temperature.py
python scripts\phase8\explain_agent_decisions.py
```

Many scripts have configurable paths and parameters. Check a script's
`--help` output before running it when command-line options are available:

```powershell
python scripts\phase9\run_external_video_demo.py --help
python scripts\demo\generate_pie_heldout_demo.py --help
```

The `test_*.py` files are executable validation scripts for individual
pipeline components. Run the relevant phase tests after preparing that
phase's required local data and model artifacts.

## Reproducibility notes

1. Use Python 3.11.x and install the pinned versions in
   [`requirements.txt`](./Adaptive_Intent_Prediction/requirements.txt).
2. Install the correct CPU or CUDA PyTorch build before installing the
   remaining dependencies.
3. Keep datasets, generated outputs, and model weights outside Git.
4. Record the dataset version, model checkpoint, hardware, and script
   arguments when reporting experimental results.

## License and data

This repository contains research implementation code. Dataset and pretrained
model usage must follow the original licenses and terms of the respective
data/model providers.
