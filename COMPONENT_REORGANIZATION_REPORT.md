# Component Reorganization Report

## Purpose

The Component 2 SUMO and MAPPO implementation was moved from the workspace root to `components/component_2_right_of_way_negotiation/`. The overall `socialmind_drive_showcase/` remains independent at the workspace root.

## Relocation

All tracked Component 2 source modules, packages, tests, models, networks, experiments, research inputs, results, documentation, and scripts were moved with Git history. The detailed research README moved with the component. Still-imported diagnostic and legacy visualization modules remain at the Component 2 root to preserve their imports and bytes; `panel_demo.zip` is preserved in `archive/generated/`.

The untracked historical showcase ZIP was moved to `workspace_archive/`; the active showcase directory was not moved.

## Runtime path changes

- Component 2 `PROJECT_ROOT` remains `Path(__file__).resolve().parent` and therefore resolves to the relocated component root.
- GUI launches receive `--gui-settings-file` with the component-root-resolved `gui/panel_real_world.xml` path.
- Headless launches receive no GUI settings option.
- The showcase Component 2 working directory and result JSON path now resolve through `COMPONENT2_ROOT`.

No algorithm, policy, reward, traffic rule, vehicle physics, observation, perception, or historical result content was changed.

## Before and after

Before, Component 2 entry points, modules, packages, resources, and evidence were mixed at the workspace root. Afterward, the workspace root contains repository infrastructure, the group showcase, `components/`, the workspace documentation, and a workspace-level archive; Component 2 is self-contained beneath `components/component_2_right_of_way_negotiation/`.

Moved Component 2 directories: `archive/`, `conflict/`, `docs/`, `experimentation/`, `map_geometry/`, `models/`, `negotiation_execution/`, `negotiation_learning/`, `negotiation_objective/`, `negotiation_scenarios/`, `negotiation_training/`, `networks/`, `panel_demo/`, `research_inputs/`, `results/`, `scripts/`, `tests/`, `traffic_accounting/`, and `traffic_rules/`.

Moved Component 2 root files: `config.py`, `conflict_entry_monitor.py`, `debug_conflict_evidence.py`, `debug_dashboard.html`, `debug_dashboard.py`, `debug_evidence.py`, `environment.py`, `evaluation.py`, `intersection.sumocfg`, `joint_negotiation_validation.py`, `main.py`, `ml_runtime_capability.py`, `negotiation.py`, `observation.py`, `perception_interface.py`, `predictor.py`, `requirements.txt`, `requirements-training.txt`, `risk_assessment.py`, `run_panel_demo.py`, `run_project.bat`, `run_research_demo.py`, `run_selected_mappo_demo.py`, `sumo_debug_overlay.py`, and the detailed research `README.md`.

## Validation

- Component 2 tests from its root: 638 passed.
- Component 2 and showcase suites together from the Component 2 root: 657 passed.
- Both demo entry-point `--help` commands passed.
- Headless panel regression completed all 12 scheduled vehicles with zero unfinished vehicles, collisions, and blocked-zone violations; one MAPPO decision epoch and two rule-resolved events occurred; the participant maximum was four.
- SUMO 1.26 GUI started and exited successfully with `gui/panel_real_world.xml`; the installed distribution contains the native `real world` scheme.
- Showcase routes `/`, `/components`, `/component/right-of-way`, and `/about` returned HTTP 200.
- Selected-policy SHA-256 before and after: `2AB2029FDD66F96C3BA0ACF5E76487C96740161E898539F93C726228097EAF57`.
