# Multi-Agent Negotiation for Right-of-Way in Complex Intersections

This final-year research project evaluates decentralized MAPPO negotiation for autonomous-vehicle right-of-way while preserving deterministic traffic-rule and physical-safety layers.

The active live runtime now uses the approved
`CONDITIONAL_CLAIM_RECONCILIATION_V1` movement-declaration protocol with unchanged
E5 weights. [Implementation and assumptions](docs/APPROVED_RECONCILIATION_IMPLEMENTATION_REPORT.md)
and [measured verification](docs/APPROVED_RECONCILIATION_VERIFICATION.md) document
4/4 four-way and 12/12 rolling completion. The dense scenario remains partial:
5/16 completed, followed by a genuine mandatory/fallback dependency cycle.
These new diagnostics are separate from frozen historical studies; no completed
final evaluation or 16/16 dense success is claimed for this revision.

## Active implementation structure

| Package | Purpose |
|---|---|
| `runtime_simulation/` | Continuous SUMO runtime simulation and telemetry |
| `targeted_validation/` | Reproducible scenario-based validation |
| `post_training_evaluation/` | Extended post-training evaluation and baseline comparison |
| `scalability_validation/` | Traffic-load and operational-boundary evaluation |

See [naming migration and compatibility](docs/NAMING_MIGRATION.md) for preferred
commands and preserved historical paths. The extended 165-episode study is not
represented as completed. Old package/script names remain thin compatibility
aliases; historical evidence retains its original names and values.

Final viva preparation is documented in
[FINAL_VIVA_RUNBOOK.md](docs/final_readiness/FINAL_VIVA_RUNBOOK.md).
The [preflight](docs/final_readiness/FINAL_EVALUATION_PREFLIGHT.md) verifies
34/165 legacy final episodes; the current V2 final study remains blocked by
acceptance review. Older successful 16-vehicle presentations do not override
the targeted 1/16 and 0/16 dense liveness results. Broader scalability is unrun.

## Final demonstration

Install the Python dependencies, install SUMO separately, and run from this Component 2 directory:

```powershell
python run_selected_mappo_demo.py --gui
```

From the workspace root, enter the component directory first:

```powershell
cd component_2_right_of_way_negotiation
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

- `run_post_training_evaluation.py` performs the separate frozen post-training evaluation
  of the current ego-local runtime. See [scope and metric definitions](docs/POST_TRAINING_EVALUATION_SCOPE.md)
  and [Windows commands and report guide](docs/POST_TRAINING_EVALUATION_GUIDE.md).
  Prepare first, run the smoke suite, then explicitly launch the 165-episode
  final suite. No retraining or held-out tuning is performed.

- `run_selected_mappo_demo.py` is the final validation-selected E5 MAPPO research demonstration. It loads the frozen canonical-replication-0 selected policy and performs inference only.
- `main.py` is the normal/legacy SUMO control-facing application. Its learned intention prediction can be shadow-only; it is not a substitute for the final selected MAPPO demo.
- `run_research_demo.py` is retained for reproducibility of the earlier frozen research-prototype demonstration.
- `run_runtime_simulation.py` is a one-process, continuous qualitative SUMO visualization for a live panel. It is presentation-only and does not replace validation, held-out evaluation, or model-selection evidence.
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
python run_runtime_simulation.py --gui
```

Optional presentation controls are `--duration` and `--gui-delay-ms`. The latter changes display pacing only; the simulation step remains 0.04 seconds. New qualitative output is written only under `results/runtime_simulation/`.

For a comfortably paced viva display:

```powershell
python run_runtime_simulation.py --gui --gui-delay-ms 10
```

GUI launches load `gui/panel_real_world.xml` at SUMO startup. Headless launches do not receive GUI settings.

GUI mode immediately centers on the intersection using the movement-path geometry and applies a focused view that retains all four approaches. Camera, colors, and playback delay are display-only and do not affect simulation timestamps or control.

The default duration is 220 seconds so all four predeclared continuous phases can finish without changing vehicle speed. The sequence includes ordinary rule-resolved traffic, one training-manifest route structure evaluated by the live selected-E5 actors, and continuing traffic that covers all 12 legal movements. A MAPPO epoch is counted only when authorized live semantic actions are actually returned.

## Congested queue-head presentation (ego-local execution)

From this component directory:

```powershell
python run_runtime_simulation.py --scenario congested_four_approach --gui --gui-delay-ms 10
```

The new scenario schedules 16 traffic vehicles (four per approach) with 1.5-second
demand headways and a 360-second simulation budget. SUMO may delay unsafe
insertions; actual departures and insertion delays are recorded separately.
The run can finish at its fixed budget, on user Stop, or when all vehicles
complete; full discharge is not guaranteed. All twelve legal movements
are represented. A wider display camera keeps queued followers visible.

Only the physically front-most eligible vehicle on each incoming lane enters
negotiation. A leader remains the queue front until its rear clears the junction;
then its follower is promoted automatically. Total live traffic can exceed four,
but each negotiation event and each actor graph remain bounded to four nodes.
Trailing traffic retains SUMO's native car-following without repeated speed
overrides. The same frozen E5 role-specific actors serve successive queue heads.

The panel runtime uses `DecentralizedEgoExecutionController`: each ego receives
only its own state/path, pair commitments involving that ego, and fresh
sender-owned physical-state/path announcements on an ideal same-step V2V
channel. Execution messages do not enter actor observations. Each ego computes
its own zone obligation and SUMO-native stopping-speed request. Missing/stale
coordination or clearance safe-holds at junction admission. Already entered
zones continue clearing; entering a previously blocked zone is a hard failure.
The effective graph and aggregated READY/BLOCKED labels are audit/UI artifacts,
not physical permission inputs. Speed mode remains 31.

For a headless web/showcase presentation:

```powershell
python run_runtime_simulation.py --scenario congested_four_approach --web-live --presentation-delay-ms 10
```

Or start `python socialmind_drive_showcase\app.py` from the repository root,
open Component 2's live view, select **Congested Four-Approach Queues**, and
press **Run Scenario**. The UI shows active/moving traffic, approach depths,
current participants, peak active traffic, collisions, and execution mode.

Use `--output-dir results/runtime_simulation/congested_ego_local_verification` to keep
new qualitative results separate. These runs are not original validation,
held-out evaluation, or evidence of policy performance on >4-node graphs.
Historical training, selection, and physical evidence-replay paths are retained
for reproducibility; this new execution mode belongs to the panel runtime.

## Research limitations

Scenario 5 also has a clearly separated, read-only unsafe counterfactual replay.
Its authentic SUMO collision and the stable-sidebar scroll verification are
documented in [Scenario 5 counterfactual and sidebar report](docs/SCENARIO5_COUNTERFACTUAL_AND_SIDEBAR_REPORT.md).
The ordinary Run button retains the protected primary method.

The final live selector now contains exactly five qualitative demonstrations.
See [Final queue-following and five-scenario report](docs/FINAL_FIVE_DEMONSTRATIONS_REPORT.md)
for the separately versioned native-following correction, identical-demand
before/after measurements, actual E5 usage and protected/rules-only comparison.
The scientific scenario catalogue and prior evaluations remain preserved.

The live website uses a presentation-only approach/entry/clearance lifecycle.
Blue approach bodies, current red/green permissions, timestamped yellow MAPPO
outlines and removal of scene-exited vehicles are documented in
[Live presentation lifecycle verification](docs/LIVE_PRESENTATION_LIFECYCLE_REPORT.md).
SUMO active/completed counts and scientific control remain separate from the
current display list.

- Model selection is a bounded one-factor comparison of E5, E10 and E15 with three canonical replications and two PPO update cycles, not a global hyperparameter search.
- The selected configuration is E5; demo replication 0 is canonical, not performance-selected.
- The held-out deterministic no-negotiation baseline can fail predefined hard safety-validity gates. Aborted scenarios have no fabricated travel-time value.
- Simulator and scenario coverage bound external validity; the results are not universal across intersections, populations, sensors, or jurisdictions.
- SUMO-native safety interventions remain evidence and are not learned-policy actions.
