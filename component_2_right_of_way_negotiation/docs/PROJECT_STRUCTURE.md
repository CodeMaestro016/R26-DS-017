# Project Structure

## Runtime entry points

| File | Purpose | Input | Output | Method | Phase |
|---|---|---|---|---|---|
| `run_selected_mappo_demo.py` | Final selected E5 demonstration | Frozen selected policy and training-role demo scenarios | Console summary and SUMO run | Learned semantic policy plus rule execution | Runtime |
| `main.py` | Normal/legacy SUMO application | SUMO configuration and ONNX models | Simulation, logs and optional dashboard | Rule control with learned intention shadow inference | Runtime |
| `run_research_demo.py` | Earlier frozen prototype demonstration | Historical demo policy/checkpoint | Historical demo evidence | Learned semantic policy plus deterministic execution | Reproducibility |
| `run_project.bat` | Windows convenience launcher | Repository and SUMO installation | GUI selected-policy demo | Command wrapper | Runtime |

## Core root modules

| Module | Purpose | Main input | Main output | Nature | Phase |
|---|---|---|---|---|---|
| `config.py` | Runtime constants and paths | Environment/project assets | Configuration | Rule/configuration | Both |
| `environment.py` | Base SUMO/TraCI lifecycle | SUMO configuration | Vehicle states and lifecycle events | Simulation | Both |
| `observation.py` | Per-AV LDM management | Ego-local states | Local graph-ready observations | Mathematical/data | Both |
| `perception_interface.py` | Sensor/perception contract | SUMO states and reference sensors | Ego-local detections | Mathematical | Both |
| `predictor.py` | Two-stage intention inference | Causal 48x6 feature window | Calibrated intention/UNKNOWN | Learned ONNX | Both |
| `conflict_entry_monitor.py` | Conflict approach/entry events | LDM and conflict geometry | Eligibility/event state | Rule-based | Both |
| `evaluation.py` | Evidence and performance accounting | Episode events/results | Metrics | Mathematical | Both |
| `negotiation.py`, `risk_assessment.py` | Legacy negotiation/risk compatibility | Vehicle states | Legacy decisions/estimates | Rule/mathematical | Runtime |
| `debug_evidence.py`, `debug_conflict_evidence.py`, `debug_dashboard.py`, `sumo_debug_overlay.py` | Runtime-linked read-only visualization/evidence | Simulation observations | Diagnostic payload/UI | Visualization | Runtime/diagnostics |

## Domain packages

| Folder | Purpose | Input | Output | Nature | Phase |
|---|---|---|---|---|---|
| `conflict/` | Paths, conflict zones, graphs and occupancy | Geometry, states, intentions | Spatial/temporal conflict graph | Mathematical/rule | Both |
| `map_geometry/` | Reference geometry and transforms | SUMO coordinates | Validated geometry | Mathematical | Both |
| `traffic_rules/` | German regulatory precedence | Movements and regulatory context | Original precedence edges | Rule-based | Both |
| `traffic_accounting/` | Demand, completion and censoring | Spawn/completion events | Demand-aware records | Mathematical | Both |
| `negotiation_learning/` | Claims, protocol, graph encoding, GNN and MAPPO interfaces | Local graphs/claims | Semantic actions | Mixed learned/protocol | Both |
| `negotiation_execution/` | Physical mapping, planning, control and replay | Effective coordination graph | Obligations and SUMO constraints | Deterministic | Both |
| `negotiation_training/` | Rollout, PPO, experiments and final selection | Frozen manifests/policy samples | Checkpoints/evidence | Learned/training | Training/inference |
| `negotiation_objective/` | Team TTT objective and reward | Demand-ledger records | Censored TTT/reward | Mathematical | Training/evaluation |
| `negotiation_scenarios/` | Frozen scenario catalogue and runners | Specifications/manifests | Reproducible episodes | Experimental | Both |
| `experimentation/` | Frozen design and selection contracts | Catalogue/protocol | Disjoint manifests/identities | Experimental | Training/evaluation |

## Supporting folders

- `scripts/validation/`: scientific-contract validators; run as `python -m scripts.validation.<module>`.
- `scripts/experiments/`: explicit experiment orchestration, not normal runtime.
- `scripts/diagnostics/`: environment and capability checks.
- `models/intention/`: ONNX models, contracts, verification and preprocessing provenance.
- `models/notebook/`: model-development notebook retained as provenance.
- `networks/`: SUMO network, routes, netconvert sources and rebuild commands.
- `results/`: scientific evidence, checkpoints, manifests and reports; intentionally retained.
- `research_inputs/`: explicit research protocol inputs.
- `tests/`: unit, contract, integration and evidence-regression tests.
- `docs/`: architecture, research basis, evidence and audit documents.

## Layering invariants

`A -> B` means A yields to B. MAPPO selects only semantic claim/response actions. The deterministic protocol produces the effective coordination graph, then the physical mapper/planner derives obligations and SUMO constraints. Runtime learned actors remain decentralized and do not consume ground-truth routes.
