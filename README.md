# Multi-Agent Negotiation for Right-of-Way in Complex Intersections

This final-year research project evaluates decentralized MAPPO negotiation for autonomous-vehicle right-of-way while preserving deterministic traffic-rule and physical-safety layers.

## Final demonstration

Install the Python dependencies, install SUMO separately, and run from the repository root:

```powershell
python run_selected_mappo_demo.py --gui
```

`run_project.bat` performs the same GUI launch and rebuilds the SUMO network first if the compiled network is absent.

## Architecture

```text
SUMO
  -> ego-local perception
  -> per-vehicle Local Dynamic Map (LDM)
  -> CPU ONNX GRU intention prediction
  -> spatial/temporal conflict reasoning
  -> German traffic-rule precedence
  -> V2V precedence-claim exchange
  -> joint-local negotiation graph
  -> graph encoding and GNN
  -> decentralized MAPPO proposer/responder actors
  -> deterministic negotiation protocol
  -> effective coordination graph
  -> physical execution mapper and conflict-zone planner
  -> SUMO-native speed constraints
  -> safety and performance evaluation
```

The learned policy changes semantic negotiation actions only:

- Proposer: `KEEP_CLAIM` or `RELINQUISH_CLAIM`.
- Responder: `ACCEPT_RELINQUISHMENT` or `REJECT_RELINQUISHMENT`.

It does not directly select acceleration, braking, steering, or target speed. An edge `A -> B` means that A yields to B. Runtime actors use ego-local/joint-local information; route truth is not an actor input.

## Entry points

- `run_selected_mappo_demo.py` is the final validation-selected E5 MAPPO research demonstration. It loads the frozen canonical-replication-0 selected policy and performs inference only.
- `main.py` is the normal/legacy SUMO control-facing application. Its learned intention prediction can be shadow-only; it is not a substitute for the final selected MAPPO demo.
- `run_research_demo.py` is retained for reproducibility of the earlier frozen research-prototype demonstration.
- `run_panel_demo.py` is a one-process, continuous qualitative SUMO visualization for a live panel. It is presentation-only and does not replace validation, held-out evaluation, or model-selection evidence.
- `python -m scripts.experiments.run_mappo_final_selection --help` exposes the completed model-selection workflow. Do not run training stages merely to launch the demo.

## Repository layout

- Core root modules: SUMO environment, perception/LDM, intention prediction, evaluation, and legacy runtime integration.
- `conflict/`: map paths, conflict graphs, conflict zones, and occupancy reasoning.
- `traffic_rules/`: deterministic German regulatory precedence.
- `negotiation_learning/`: semantic protocol, tensor encoding, GNN and MAPPO interfaces.
- `negotiation_execution/`: coordination-to-physical mapping, planner, controller, and replay validation.
- `negotiation_training/`: rollout, PPO, controlled experiments, selection, and inference providers.
- `negotiation_objective/`: demand-aware travel-time objective and rewards.
- `negotiation_scenarios/`: frozen scenario catalogue and manifests.
- `experimentation/`: frozen experimental design and selection contracts.
- `scripts/`: validation, experiment, and diagnostic commands.
- `models/`: deployed ONNX intention models and training provenance.
- `networks/`: SUMO network, routes, source XML and rebuild scripts.
- `results/`: checkpoints and research evidence; do not treat it as disposable output.
- `tests/`: scientific-contract and regression tests.
- `docs/`: architecture, evidence, audit, and research documentation.

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for module-level details.

## Requirements

Create a virtual environment outside the repository or in the ignored `.venv/` directory, then install:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-training.txt
```

SUMO must be installed externally and `SUMO_HOME` should identify its installation. Python packages do not supply the SUMO executable or `netconvert`.

Runtime dependencies include NumPy, ONNX Runtime, TraCI/SUMO tools, Requests and Shapely. PyTorch and pytest are development/research dependencies.

## Network and model assets

`intersection.sumocfg` references `networks/intersection.net.xml` and `networks/intersection.rou.xml`. Rebuild sources and Windows/POSIX build scripts are in `networks/`.

Deployed intention assets are under `models/intention/`, including two ONNX GRUs, feature/calibration contracts, verification evidence and preprocessing provenance. Selected MAPPO artifacts and final evidence are under `results/final_mappo_selection_v2/`.

## Testing and validation

```powershell
python -m pytest -q
python -m scripts.validation.validate_gnn_forward
```

Standalone validators are retained for reproducibility; they are not final runtime entry points.

## Live panel visualization

Launch the deterministic rolling-traffic presentation with:

```powershell
python run_panel_demo.py --gui
```

Optional presentation controls are `--duration` and `--gui-delay-ms`. The latter changes display pacing only; the simulation step remains 0.04 seconds. New qualitative output is written only under `results/panel_demo/`.

For a comfortably paced viva display:

```powershell
python run_panel_demo.py --gui --gui-delay-ms 10
```

GUI mode immediately centers on the intersection using the movement-path geometry and applies a focused view that retains all four approaches. Camera, colors, and playback delay are display-only and do not affect simulation timestamps or control.

The default duration is 220 seconds so all four predeclared continuous phases can finish without changing vehicle speed. The sequence includes ordinary rule-resolved traffic, one training-manifest route structure evaluated by the live selected-E5 actors, and continuing traffic that covers all 12 legal movements. A MAPPO epoch is counted only when authorized live semantic actions are actually returned.

## Research limitations

- Model selection is a bounded one-factor comparison of E5, E10 and E15 with three canonical replications and two PPO update cycles, not a global hyperparameter search.
- The selected configuration is E5; demo replication 0 is canonical, not performance-selected.
- The held-out deterministic no-negotiation baseline can fail predefined hard safety-validity gates. Aborted scenarios have no fabricated travel-time value.
- Simulator and scenario coverage bound external validity; the results are not universal across intersections, populations, sensors, or jurisdictions.
- SUMO-native safety interventions remain evidence and are not learned-policy actions.
