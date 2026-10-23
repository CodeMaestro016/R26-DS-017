# SOCIALMIND DRIVE

**Agentic AI for Robust and Socially-Aware Autonomous Driving**

This repository brings together four independently developed research components. They explore pedestrian intent, right-of-way negotiation, social reasoning, and collaborative learning for autonomous vehicles. The components are not one connected end-to-end pipeline; each has its own code, dependencies, data, and runtime requirements.

## Research components

| # | Component | Directory | What it explores |
|---|---|---|---|
| 1 | Adaptive Intent Prediction in Occluded Urban Scenarios | [`Adaptive_Intent_Prediction/`](./Adaptive_Intent_Prediction/) | Predicting pedestrian crossing intent from visual, motion, and spatial cues when observations are occluded or incomplete. The pipeline includes tracking, feature extraction, Bayesian reliability, deep fusion/transformer models, calibration, and explanations. |
| 2 | Multi-Agent Negotiation for Right-of-Way in Complex Intersections | [`component_2_right_of_way_negotiation/`](./component_2_right_of_way_negotiation/) | Decentralized vehicle negotiation in SUMO, combining local perception, traffic rules, conflict reasoning, graph models, and MAPPO semantic actions. See its [README](./component_2_right_of_way_negotiation/README.md) for current implementation and evidence notes. |
| 3 | Proactive Social Compliance Modeling using Agentic Theory of Mind | [`component_3/`](./component_3/) | CARLA pedestrian scenarios and reasoning about road-user behavior. The demo code extracts pose and motion features, predicts six behavior states (Waiting, Hesitant, Committed, Distracted, Aggressive, Jaywalk), and uses a rule-based driving agent. |
| 4 | Collective Learning Between Autonomous Vehicles using Agentic Knowledge Sharing | [`component_4/`](./component_4/) | CARLA traffic-sign perception with per-vehicle model pipelines. Vehicles can decide whether to share learned sign embeddings; a global verification/broadcast service supports checking and distributing knowledge. |

## Repository layout

```text
Adaptive_Intent_Prediction/          Component 1: pedestrian intent research
component_2_right_of_way_negotiation/ Component 2: SUMO right-of-way negotiation
component_3/                         Component 3: CARLA social-compliance demo
component_4/                         Component 4: CARLA and knowledge-sharing code
socialmind_drive_showcase/           Local NiceGUI showcase for the four components
```

The showcase is a presentation layer. Its live Component 2 view launches the existing Component 2 runtime; it does not combine the four research implementations. Components 1 and 4 have showcase pages, and Component 3 has standalone CARLA demo code.

## Run the showcase

From the repository root, on Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r socialmind_drive_showcase\requirements.txt
python socialmind_drive_showcase\app.py
```

This opens the local desktop showcase. To run its localhost server without the desktop window:

```powershell
python socialmind_drive_showcase\app.py --server-only
```

Then open `http://127.0.0.1:8088` in a browser. See the [showcase README](./socialmind_drive_showcase/README.md) for page details and Component 2 live-view behavior.

## Component-specific setup

The showcase environment is only for the showcase. Research components have separate dependencies and external requirements; use a separate virtual environment for each component where dependency versions differ.

### Component 1

Use Python 3.11 and follow the setup in [`Adaptive_Intent_Prediction/requirements.txt`](./Adaptive_Intent_Prediction/requirements.txt). Install the matching CPU or CUDA PyTorch build before the remaining requirements. The main script groups are:

| Scripts | Role |
|---|---|
| `scripts/phase1/` | Dataset preparation and sequence creation |
| `scripts/phase2/` | Occlusion generation and validation |
| `scripts/phase3/` | Visual, motion, spatial, and sequence feature extraction |
| `scripts/phase4/` | Bayesian features and network training |
| `scripts/phase5/` | Gated-fusion and transformer training/evaluation |
| `scripts/phase6/` | Calibration and uncertainty evaluation |
| `scripts/phase7/` | Learned agent policy preparation and evaluation |
| `scripts/phase8/` | Decision explanations |
| `scripts/phase9/` | PIE/YOLO detection and runtime pipeline |

Run phase scripts from inside `Adaptive_Intent_Prediction`, for example:

```powershell
cd Adaptive_Intent_Prediction
python scripts\phase1\parse_annotations.py
```

Data and pretrained weights are local prerequisites and are not included in Git. CARLA is installed separately, with a Python client version matching the simulator. For the external-video demo, check its options with `python scripts\phase9\run_external_video_demo.py --help` and provide the required video and model assets.

### Component 2

Install its Python requirements and install SUMO separately. From the repository root, launch the selected-policy demonstration with:

```powershell
cd component_2_right_of_way_negotiation
python run_selected_mappo_demo.py --gui
```

The live showcase scenario is a qualitative presentation runtime; its metrics do not replace the component's validation or evaluation results. Follow the [Component 2 README](./component_2_right_of_way_negotiation/README.md) for SUMO setup, other entry points, and current research-status notes.

### Component 3

The standalone demo is under `component_3/carla_sim/`. It requires a compatible CARLA simulator, Python client, model files, and supporting vision/ML packages. From that directory, the web launcher entry point is:

```powershell
python web_launcher.py
```

Its child-process configuration currently points to the Linux interpreter `/workspace/carla_venv/bin/python3`. Update that setting for the target machine before launching scenarios. This component does not currently have a dedicated requirements file.

### Component 4

The vehicle knowledge-sharing service is under `component_4/component_4/` (`ml_service.py`); the CARLA client is under `component_4/carla_app/`. The service requirements are in [`component_4/component_4/requirements.txt`](./component_4/component_4/requirements.txt). A compatible CARLA installation and local model/database assets are also needed. The checked-in `component_4/component_4/main_demo.py` is empty, so there is no complete one-command orchestrator documented here. The service entry point is `ml_service.py`; it starts a local API and expects its model assets to be configured.

## Data, models, and reproducibility

Datasets, simulator installations, pretrained model weights, and generated results may be excluded from Git or stored in component-specific locations. Check the relevant component's configuration and documentation before running an experiment. Do not treat showcase output as quantitative research evidence unless the corresponding component evaluation protocol says it is.

Use each component's own documentation for its evaluation commands, assumptions, and limitations. Component 2's README includes detailed evidence-status notes; Components 3 and 4 currently have no standalone README, and their external simulator/model setup must be configured locally.
