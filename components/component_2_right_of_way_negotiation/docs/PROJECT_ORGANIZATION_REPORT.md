# Project Organization Report

Date: 2026-08-27

## Scope and safety boundary

This was a repository-organization change only. No algorithm, hyperparameter, reward, action meaning, traffic rule, scenario manifest, checkpoint, trained weight, selection artifact, or experiment result was regenerated or edited. The existing domain packages were retained because their boundaries are meaningful and a `src/` migration would add import risk without scientific value.

Protected final artifacts were hash-checked after organization:

| Artifact | SHA-256 |
|---|---|
| `results/final_mappo_selection_v2/selected_configuration.json` | `1D5D4F33203D31808D497019EC31329AADDF33A533B6DB5F43C9FFAF873A3ED1` |
| `results/final_mappo_selection_v2/selected_policy.pt` | `2AB2029FDD66F96C3BA0ACF5E76487C96740161E898539F93C726228097EAF57` |
| `results/final_mappo_selection_v2/held_out/selected_mappo_results.json` | `7F62BC26C055CF7D7E4775426631F0F4805DBBFF60DF8BCA690F44005A970944` |
| `results/final_mappo_selection_v2/held_out/baseline_results.json` | `465D81400F11DD1910C4B234C2DB62F8DDB29A7A800C7CF916116C12EF4E01BE` |

## Before and after

Before, the root contained 31 `validate_*.py` runners, a capability checker, the final-selection experiment runner, and two documentation files alongside runtime code.

After, the root exposes the final entry point and essential runtime/configuration files. Existing scientific packages remain at top level. Standalone commands are grouped under:

```text
scripts/
  diagnostics/
  experiments/
  validation/
```

Documentation now lives consistently under `docs/`, except for the reviewer-facing `README.md`.

## Folders created

- `scripts/validation/`
- `scripts/experiments/`
- `scripts/diagnostics/`
- `archive/legacy/generated/`

Each `scripts` directory has an `__init__.py`, allowing commands to run safely from the project root with `python -m ...`.

## Files moved

Documentation:

- `PROJECT_STRUCTURE.md` -> `docs/PROJECT_STRUCTURE.md`
- `VALIDATION_REPORT.md` -> `docs/VALIDATION_REPORT.md`

Diagnostics and experiments:

- `check_ml_runtime.py` -> `scripts/diagnostics/check_ml_runtime.py`
- `run_mappo_final_selection.py` -> `scripts/experiments/run_mappo_final_selection.py`

Validation runners moved from root to `scripts/validation/`:

- `validate_controlled_pilot_design.py`
- `validate_coordination_physical_execution_mapping.py`
- `validate_coupled_mappo_environment_profile.py`
- `validate_ctde_interfaces.py`
- `validate_demand_ledger.py`
- `validate_discrete_sumo_braking_semantics.py`
- `validate_experimental_selection_framework.py`
- `validate_gnn_forward.py`
- `validate_identical_condition_branch_replay.py`
- `validate_joint_negotiation_cycle_resolution.py`
- `validate_map_coordinate_frame.py`
- `validate_mappo_architecture_contract.py`
- `validate_mappo_behavior_rollout.py`
- `validate_mappo_closed_loop_pilot.py`
- `validate_mappo_extended_evidence_review.py`
- `validate_mappo_extended_learning_curve.py`
- `validate_mappo_mechanical_pilot.py`
- `validate_mappo_mechanical_ppo_update.py`
- `validate_mappo_optimizer_contract.py`
- `validate_mappo_pilot_evidence_review.py`
- `validate_mappo_policy_interface.py`
- `validate_mappo_predeclared_selection_protocol.py`
- `validate_mappo_returns.py`
- `validate_mappo_training_resource_budget.py`
- `validate_multiagent_negotiation_protocol.py`
- `validate_negotiation_objective.py`
- `validate_negotiation_protocol.py`
- `validate_negotiation_scenario_coverage.py`
- `validate_negotiation_traffic_coupling.py`
- `validate_negotiation_transitions.py`
- `validate_policy_semantic_encoding.py`

## Files archived

- `results/final_mappo_selection_v2/smoke (2).zip` -> `archive/legacy/generated/smoke (2).zip`. Inspection showed that it was a duplicate-style nested archive containing only `smoke.zip`; it was removed from active evidence storage without destructive deletion.

No source file was archived.

## Files deleted

None. Deletion of ignored cache directories and the local `.venv/` was attempted only after resolving their absolute paths within the workspace, but the execution environment rejected destructive filesystem commands. They remain ignored and are not part of Git packaging. They may be removed manually:

```powershell
Remove-Item -Recurse -Force .venv, .pytest_cache, __pycache__
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

These commands remove reproducible local environment/cache data only.

## Imports and path changes

- `tests/test_ml_runtime_capability.py` now imports `scripts.validation.validate_gnn_forward` and inspects its new path.
- `tests/test_mappo_extended_evidence_review.py` now inspects the validator under `scripts/validation/`.
- `run_project.bat` now launches `python run_selected_mappo_demo.py --gui` as the final project entry point.
- Standalone validator documentation now uses module execution, for example `python -m scripts.validation.validate_gnn_forward`.
- The completed selection experiment is available as `python -m scripts.experiments.run_mappo_final_selection`.
- No model, results, SUMO, scenario, or checkpoint path was changed.

## Requirements changes

- Retained actual runtime dependencies: NumPy, ONNX Runtime, Requests, TraCI and Shapely.
- Added `sumolib`, which is directly imported by active code and is part of the SUMO Python tooling.
- Added `pytest` to `requirements-training.txt`; PyTorch remains optional research/training infrastructure.
- No versions were invented. The existing `shapely>=2.0` constraint was preserved.

## Duplicate and suspicious-file review

- The duplicate-style `smoke (2).zip` was archived as described above.
- No duplicate/versioned Python source such as `(1)`, `_old`, `_backup`, `.bak`, or `.tmp` was found outside dependencies/caches.
- Canonical result ZIPs (`training.zip`, `validation.zip`, `held_out.zip`, `comparison.zip`, `smoke.zip`) were retained because they package final research evidence.

## Files intentionally retained

- `run_research_demo.py`: imported by final-selection code and covered by historical demonstration tests.
- Root `debug_*.py`, `debug_dashboard.html`, and `sumo_debug_overlay.py`: active runtime/test visualization dependencies, not isolated scratch files.
- `results/perception_ldm_evidence.jsonl`: large, but explicitly cited research evidence.
- `models/notebook/inD_intention_dataset_preparation.ipynb`: model-development and thesis provenance.
- All results, checkpoints, ONNX models, network XML, scenario manifests and evidence archives.
- Root core modules such as `observation.py` and `predictor.py`: heavily imported compatibility boundaries; moving them would create risk without improving the scientific package design.

## Final entry point

```powershell
python run_selected_mappo_demo.py --gui
```

`main.py` remains the normal/legacy simulation path and is intentionally distinct.

## Validation performed

- Full pytest after moves: `600 passed in 23.88s`.
- Recursive syntax compilation of active Python files: passed.
- Imports of `main`, the final demo, a moved validator and the moved experiment runner: passed.
- `python run_selected_mappo_demo.py --help`: passed.
- Selected E5 configuration and checkpoint resolution: passed.
- Both intention ONNX models loaded with `CPUExecutionProvider`: passed.
- `intersection.sumocfg` parsed and both referenced SUMO files resolved: passed.
- Inference-only `python run_selected_mappo_demo.py`: passed; three scenarios completed, zero training operations and zero held-out scenarios consumed.
