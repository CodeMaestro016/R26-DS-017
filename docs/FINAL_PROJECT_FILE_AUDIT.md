# Final Project File Audit

Audit date: 2026-08-18  
Scope: the 767 non-`.git` files present before this audit. Git database internals were not project files and were excluded. The two audit outputs are not included in the counts. This was a read-only cleanup audit: files deleted = 0; moved = 0; renamed = 0; source modifications = 0.

## 1. Repository overview

The repository contains two final executable paths sharing a common intersection stack:

- `main.py`: autonomous SUMO run with perception, LDM/history, two-stage ONNX intention inference, conflict/reachability reasoning, German-StVO rule reasoning, negotiation observations, and evaluation outputs.
- `run_research_demo.py`: three-scenario, inference-only MAPPO research demonstration using the frozen demo policy and a selected evidence checkpoint.

The principal packages are `conflict`, `map_geometry`, `traffic_rules`, `traffic_accounting`, `negotiation_learning`, `negotiation_execution`, `negotiation_objective`, `negotiation_scenarios`, `experimentation`, and `negotiation_training`. There are 49 retained test files, 33 historical/validation entry-point files, 47 evidence files, 20 protected model/checkpoint files, and 269 documentation/source-snapshot files.

The worktree already had user changes in `environment.py` and `negotiation_training/environment.py`; this audit did not alter them.

## 2. Final runtime dependency graph

```text
run_project.bat
  -> main.py
     -> config.py -> intersection.sumocfg -> networks/intersection.net.xml
                                      \-> networks/intersection.rou.xml
     -> environment.py -> SUMO/TraCI
     -> perception_interface.py -> observation.py (LDM/history)
     -> predictor.py -> models/intention/{feature specification, policy, 2 ONNX models}
     -> conflict/* + map_geometry/*
     -> traffic_rules/* -> traffic_rules/profiles/de_stvo_uncontrolled_4way_v1.json
     -> negotiation_learning/* + negotiation.py
     -> negotiation_objective/* + traffic_accounting/*
     -> evaluation.py -> results/*.csv

run_research_demo.py
  -> results/negotiation_scenario_catalogue.json
  -> experimentation/* + negotiation_scenarios/*
  -> negotiation_execution/replay.py -> SUMO runtime chain above
  -> negotiation_training/demo_policy.py
       -> results/mappo_demo_policy.pt
       -> results/mappo_extended_resume/replication_0_state_2.pt
  -> negotiation_training/demo_provider.py -> MAPPO/GNN/semantic/protocol stack
  -> results/final_research_prototype_demo.{json,summary.md}
```

Important dynamic references checked:

- `config.py` anchors `SUMO_CONFIG`, `SUMO_NETWORK_FILE`, `MODEL_DIRECTORY`, and `OUTPUT_DIR` to the project root.
- `predictor.py` loads both ONNX files plus `feature_specification.json` and `robust_calibration_and_unknown_policy.json`.
- MAPPO loaders use `torch.load`; `demo_policy.py` names the demo policy and replication-0/state-2 source explicitly.
- Research validators/loaders reference scenario catalogues, architecture/optimizer/profile artifacts, rollout/update evidence, selection protocol, resource-budget input, and checkpoint directory.
- Package `__init__.py` exports were inspected. In particular, `negotiation_training/__init__.py` eagerly imports all training modules, making them import-time dependencies of the demo unless that package is refactored.

## 3. Entry points

| Path | Purpose | Role | Retain? |
|---|---|---|---|
| `main.py` | Full SUMO/ONNX shadow-system run | Final runtime | Yes |
| `run_project.bat` | Windows launcher for `main.py` | Final runtime | Yes |
| `run_research_demo.py` | Frozen three-scenario MAPPO demonstration | Final runtime/demo | Yes |
| `check_ml_runtime.py` | Reports optional NumPy/PyTorch/ONNX capability | Historical validation utility | Yes, archive |
| `validate_gnn_forward.py` | Explicitly untrained, test-only GNN forward gate | Research validation | Yes, archive |
| `validate_controlled_pilot_design.py`, `validate_experimental_selection_framework.py` | Frozen experimental/pilot design gates | Research methodology | Yes, archive |
| `validate_negotiation_scenario_coverage.py`, `validate_map_coordinate_frame.py` | Scenario and compiled-map validation | Research/SUMO validation | Yes, archive |
| `validate_discrete_sumo_braking_semantics.py`, `validate_identical_condition_branch_replay.py`, `validate_negotiation_traffic_coupling.py`, `validate_coordination_physical_execution_mapping.py` | Physical coupling/control evidence | Research validation | Yes, archive |
| `validate_ctde_interfaces.py`, `validate_multiagent_negotiation_protocol.py`, `validate_negotiation_protocol.py`, `validate_policy_semantic_encoding.py`, `validate_negotiation_transitions.py`, `validate_mappo_policy_interface.py`, `validate_mappo_returns.py` | Negotiation/MAPPO interface and mathematics gates | Research validation | Yes, archive |
| `validate_demand_ledger.py`, `validate_negotiation_objective.py`, `validate_joint_negotiation_cycle_resolution.py` | Accounting, objective, and joint-cycle gates | Research validation | Yes, archive |
| `validate_coupled_mappo_environment_profile.py`, `validate_mappo_architecture_contract.py`, `validate_mappo_optimizer_contract.py`, `validate_mappo_mechanical_pilot.py`, `validate_mappo_behavior_rollout.py`, `validate_mappo_mechanical_ppo_update.py` | Mechanical MAPPO construction/profile/training evidence runners | Historical experimentation/reproducibility | Yes, archive |
| `validate_mappo_closed_loop_pilot.py`, `validate_mappo_pilot_evidence_review.py`, `validate_mappo_extended_learning_curve.py`, `validate_mappo_extended_evidence_review.py`, `validate_mappo_predeclared_selection_protocol.py`, `validate_mappo_training_resource_budget.py` | Pilot, extended tranche, selection, and budget evidence | Historical experimentation/reproducibility | Yes, archive |

No other non-test Python file has a `__main__` guard. A few test modules have standalone guards, but their role remains test validation.

## 4. KEEP_FINAL_RUNTIME

| Path | Purpose | Referenced by |
|---|---|---|
| `main.py`; `run_project.bat`; `config.py`; `environment.py`; `evaluation.py` | Main orchestration, launch, configuration, SUMO lifecycle, metrics | Final SUMO run |
| `perception_interface.py`; `observation.py`; `predictor.py`; `conflict_entry_monitor.py`; `risk_assessment.py` | Perception/LDM, ONNX inference, event timing, legacy baseline risk | `main.py`, replay, tests |
| `negotiation.py` | Rule-based negotiation baseline | `main.py`, coordinate tests |
| `conflict/*.py` (7 source files) | Map paths, zones, occupancy, graph, models, catalogue output | Both runtime modes |
| `map_geometry/*.py` (3 source files) | Authoritative compiled-network geometry | Conflict/observation/scenarios |
| `traffic_rules/*.py`; `traffic_rules/profiles/*.json` (5 files) | StVO rule engine and reviewed runtime catalogue | Main/replay/tests |
| `traffic_accounting/*.py` (3 files) | Demand and lifecycle accounting | Main/replay/objective |
| `negotiation_objective/*.py` (4 files) | Team objective and ledger | Replay/training/evidence |
| `negotiation_learning/**/*.py` (43 files) | Claims, V2V, joint graphs, tensor/GNN, CTDE, MAPPO interfaces, protocol, transitions, returns | Main and demo policy stack |
| `negotiation_execution/*.py` (7 files) | Constraints, planning, physical mapping and replay | Demo/training/validators |
| `negotiation_scenarios/*.py` (8 files) | Scenario catalogue, calibration, readiness, runner | Demo/experimental design |
| `experimentation/*.py` (5 files) | Frozen design/manifests used to select demo scenarios | `run_research_demo.py` |
| `negotiation_training/*.py` (24 files) | Demo loading/provider plus eagerly exported training contracts and reproducibility pipeline | Demo and historical runners |
| `run_research_demo.py` | Final learned-policy demonstration | User/demo tests |
| `ml_runtime_capability.py` | Optional neural dependency detection without eager imports | Runtime/tests |

File count: **122**.

## 5. KEEP_SUMO_INFRASTRUCTURE

| Path | Purpose | Referenced by |
|---|---|---|
| `intersection.sumocfg` | Runtime SUMO configuration; net=`networks/intersection.net.xml`, routes=`networks/intersection.rou.xml`, no additional-files | `config.py`, `environment.py` |
| `networks/intersection.net.xml` | Compiled runtime network | `.sumocfg`, geometry/conflict code |
| `networks/intersection.rou.xml` | Runtime vehicle types/routes | `.sumocfg`, scenario route derivation |
| `networks/intersection.nod.xml` | Rebuild source nodes | build scripts/netconvert provenance |
| `networks/intersection.edg.xml` | Rebuild source edges | build scripts/netconvert provenance |
| `networks/intersection.con.xml` | Rebuild source connections | build scripts/netconvert provenance |
| `networks/build_network.bat`; `networks/build_network.sh` | Reproducible Windows/POSIX netconvert commands | Network rebuild |

File count: **8**. The generated `.net.xml` comment records these three build inputs, but runtime needs only the compiled network and route file.

## 6. KEEP_ML_MODELS

| Path | Purpose | Required for |
|---|---|---|
| `models/intention/primary_1.0s_gru.onnx`; `secondary_0.5s_gru.onnx` | Two-stage intention models | Main runtime |
| `models/intention/feature_specification.json`; `robust_calibration_and_unknown_policy.json` | Input contract/calibration/unknown policy loaded by predictor | Main runtime |
| `models/intention/deployment_manifest_onnx.json`; `onnx_deployment_quality_checks.csv`; `onnx_export_verification.csv`; `README_SUMO_DEPLOYMENT.txt`; `requirements_sumo_cpu.txt` | Deployment identity, QA and reproducibility | Model provenance |
| `models/intention/training_only_scalers.npz` | Training preprocessing provenance; not loaded by inference | Historical reproducibility |
| `results/mappo_demo_policy.pt` | Frozen inference payload | Final MAPPO demo |
| `results/mappo_extended_resume/replication_0_state_2.pt` | Explicit selected source checkpoint | Demo verification/reconstruction |
| Other eight `results/mappo_extended_resume/*.pt` checkpoints | Resume/evidence states across replications 0–2 | Training evidence/reproducibility |

File count: **20**. No trained model is a deletion candidate.

## 7. KEEP_RESEARCH_EVIDENCE

| Path | Purpose | Referenced by |
|---|---|---|
| `research_inputs/mappo_selection_external_inputs.json` | External selection/resource decision input | Resource-budget resolver |
| `results/*.json` (25 files) | Frozen design, profiles, contracts, rollout/update/pilot/selection/demo evidence | Validators, tests, thesis claims |
| `results/*.csv` (6 files) | Conflict catalogues and prediction/evaluation records | Main evaluation, README, analysis |
| `results/step_*.txt` (12 files) | Captured milestone execution/pytest/validation output | Historical evidence |
| `results/*summary.md` (2 files) | Human-readable scenario/demo evidence | Researchers/tests |
| `results/.gitkeep` | Retains output directory in clean clones | Repository layout |

File count: **47**. Progress/blocker artifacts and byte-identical captured outputs remain protected because they record experiment history.

## 8. KEEP_TESTS

| Path | Purpose | Referenced by |
|---|---|---|
| `tests/__init__.py`; `tests/test_*.py` (49 files total) | Final regression suite covering startup, models, perception, rules, conflicts, negotiation, execution, MAPPO, evidence, and demo | `pytest`, validation workflow |

File count: **49**. Compiled copies under `tests/__pycache__` are excluded here and listed for deletion.

## 9. KEEP_DOCUMENTATION

| Path | Purpose | Referenced by |
|---|---|---|
| `README.md`; `PROJECT_STRUCTURE.md`; `VALIDATION_REPORT.md` | Setup, architecture, scope and validation history | Researchers/users |
| `requirements.txt`; `requirements-training.txt`; `.gitignore` | Runtime/training environment and repository hygiene | Setup/version control |
| `docs/research_basis/*.md` | Map-frame and learning research basis | Thesis/provenance |
| `docs/regulatory_sources/StVO.pdf` | Official-law source artifact | Regulatory provenance |
| `docs/regulatory_sources/BJNR036710013.xml`; 257 adjacent `*.jpg` assets | Complete XML/image source bundle | Regulatory provenance |
| `docs/regulatory_sources/de_stvo/2026-08-11/BJNR036710013.xml`; `SOURCE.md` | Dated, cited source snapshot and acquisition metadata | Rule profile/tests |

File count: **269**. The two XML files are byte-identical, but neither is marked for deletion: the dated copy is the canonical cited snapshot, while the top-level copy is co-located with the 257 relative image references and therefore preserves a self-resolving source bundle.

## 10. ARCHIVE_HISTORICAL

| Path | Why historical | Needed for runtime? | Why retain |
|---|---|---|---|
| `check_ml_runtime.py` | Environment capability checkpoint | No | Reproduces dependency diagnosis |
| `joint_negotiation_validation.py` | Shared Step 5J evidence helper | No | Validators/tests still reference it |
| `validate_*.py` (31 files) | Stage-specific validation/training/evidence runners | No, except manual validation | Reproduces research gates and generated evidence |

File count: **33**. These should move only in a later, import-aware archival change; several tests import validator/helper modules by their present root paths.

## 11. DELETE_CANDIDATE

| Path | Reason | Evidence that deletion is safe |
|---|---|---|
| `.pytest_cache/` (5 files) | Generated pytest state | Git-ignored; pytest recreates it; no source reference |
| `**/__pycache__/**/*.pyc` (213 files in 21 cache directories) | Generated CPython/pytest bytecode, including stale bytecode for removed `run_visual_research_demo.py`, `demo_visualization.py`, and `test_visual_research_demo.py` | Git-ignored; interpreter/test runner recreates it; source is authoritative |
| `conflict.zip` | Obsolete duplicate snapshot of an earlier `conflict/` tree, including generated bytecode and omitting current `occupancy_assessor.py` | Not referenced anywhere; live directory is canonical and more complete; ZIP contents were enumerated |

File count: **219**. No deletion was performed.

## 12. UNKNOWN_REQUIRES_REVIEW

None. File count: **0**.

## 13. Duplicate files

| Files | Finding | Canonical decision |
|---|---|---|
| Two `BJNR036710013.xml` copies | Exact SHA-256 duplicate | Keep both for now: dated citation vs co-located image bundle |
| `results/step_5j_2b_{2,3,4}_main_output.txt`; `step_5j_3a_main_output.txt` | Exact duplicate captures | Keep as milestone-specific evidence; metadata context differs by filename |
| `conflict.zip` vs `conflict/` | Near-duplicate archive; ZIP is older/incomplete and embeds caches | Live `conflict/` is canonical; ZIP is deletion candidate |
| Cache bytecode with no matching source | Stale generated copies | Delete with their cache directories; never treat as canonical source |

No `(1)`, `(2)`, `copy_of`, `.bak`, `.tmp`, editor swap, or empty scratch file was found. `results/.gitkeep` is intentionally empty.

## 14. Recommended final project folder structure

```text
project/
  main.py, run_research_demo.py, config.py, requirements*.txt
  runtime modules and packages/
  models/intention/
  networks/ + intersection.sumocfg
  tests/
  docs/
    research_basis/
    regulatory_sources/
    archive/validators/        # future move only after fixing imports/tests
  research_inputs/
  results/
    final/                     # final demo and summaries
    evidence/                  # contracts, profiles, training/validation records
    checkpoints/               # protected .pt states
```

This is a recommendation, not a performed move. Preserve current paths until code, tests, documentation, and evidence hashes are updated atomically.

## 15. Proposed cleanup actions

1. In a separately authorized cleanup, remove only the 21 `__pycache__` directories, `.pytest_cache`, and `conflict.zip`.
2. Run the full test suite and both final entry points after cleanup; cache regeneration is expected.
3. Optionally refactor `negotiation_training/__init__.py` to avoid eager wildcard imports. Only then reassess which training-analysis modules can move to an archive.
4. If reorganizing evidence, preserve filenames, hashes, scenario split definitions, model/checkpoint identities, and update every loader/test/document reference together.
5. Do not deduplicate regulatory XML or milestone output captures without first defining an archival provenance policy.

Final file-level counts (sum = 767): KEEP_FINAL_RUNTIME 122; KEEP_SUMO_INFRASTRUCTURE 8; KEEP_ML_MODELS 20; KEEP_RESEARCH_EVIDENCE 47; KEEP_TESTS 49; KEEP_DOCUMENTATION 269; ARCHIVE_HISTORICAL 33; DELETE_CANDIDATE 219; UNKNOWN_REQUIRES_REVIEW 0.
