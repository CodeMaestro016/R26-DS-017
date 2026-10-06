# Run and review the final evaluation

Use the existing environment on this machine. SUMO must remain on PATH.
The optional plot dependency is listed in `requirements-evaluation.txt`.

```powershell
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
& "C:\R26-DS-017\venv\Scripts\python.exe" -m pip install -r requirements-evaluation.txt
```

Focused verification, including the retained real SUMO dense acceptance test:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B -m pytest tests/test_final_evaluation.py tests/test_panel_demo.py tests/test_ego_execution_and_dense_traffic.py -q
```

Full Component 2 and showcase verification:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B -m pytest tests -q
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& "C:\R26-DS-017\venv\Scripts\python.exe" -B -m pytest socialmind_drive_showcase/tests -q
cd component_2_right_of_way_negotiation
```

Prepare verifies and freezes the protocol before any demand run:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --prepare
```

Smoke runs nine plumbing episodes: all three methods on the rule control,
regulatory cycle and normal 8-vehicle seed 101, plus four bounded message-fault
checks. Its report is visibly **SMOKE_NOT_FINAL**. It never fills the final matrix.
Each smoke episode has a separately frozen 90-second simulation budget; this
does not change any final-study budget or establish final liveness performance.

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --suite smoke
```

The final command runs the predeclared 165 episodes. This is a substantial CPU
workload: up to 1,552,500 simulation steps, potentially several hours on this
machine. It is deliberately not launched automatically as part of installation
or UI startup. Episodes finish early only when every scheduled vehicle exits.

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --suite final
```

The same command resumes by retaining every already recorded episode, including
failures and degradation. It does not rerun failed cases or select favorable
results. Smoke, final and replay records are isolated by their suite field.
Incomplete final matrices are explicitly labelled. Code/config changes after
preparation cause a manifest mismatch. Restore the frozen sources to resume;
an intentionally new protocol requires a separate `--output-root`, preserving
the previous archive. Do not edit manifests to bypass the freeze.

Reports can be rebuilt from verified archived records without simulation:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --report-only
Start-Process -FilePath "results\final_evaluation\latest\PANEL_EVALUATION_REPORT.html"
```

The readable HTML and Markdown reports, full statistical `PAPER_TABLES.md`,
six PNG/SVG figures, provenance and copied raw runs appear under
`results/final_evaluation/latest/`. Canonical immutable run archives live under
`results/final_evaluation/runs/RUN_ID/`. Archive JSON/CSV are reproducibility
details, not the main panel presentation. SUMO warning logs are retained there.

Every report episode supplies its exact replay command. Replace `RUN_ID` with
the listed immutable ID, including a safe-degradation or failed case:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --replay RUN_ID --gui
```

Replay verifies the manifest and saved demand, retains the original method,
seed, budget and physics, and records a fresh `REPLAY_NOT_FINAL` result. It
does not overwrite the original or enter final statistics. GUI timing can
change wall-clock measurements; simulation demand/control are identical.

Start the showcase from the repository root:

```powershell
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& "C:\R26-DS-017\venv\Scripts\python.exe" -B socialmind_drive_showcase\app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/evaluation` for **Quantitative
Evaluation**, or use the link on Component 2's detail page. It reads only
backend aggregates/plots, with no run, edit or recompute scientific controls.
The existing live page and qualitative disclaimer remain separate. Omit
`--server-only` to use the desktop window.

## Implementation inventory

Created under Component 2:

- `final_evaluation/__init__.py`, `models.py`, `scenarios.py`, `baselines.py`,
  `metrics.py`, `runner.py`, `aggregation.py`, `reporting.py`, `replay.py`,
  `integrity.py`, `faults.py`.
- `run_final_evaluation.py`, `requirements-evaluation.txt`.
- `tests/test_final_evaluation.py`.
- `docs/FINAL_EVALUATION_SCOPE.md`, `docs/FINAL_EVALUATION_GUIDE.md`.

Modified under Component 2:

- `panel_demo/runner.py`: optional semantic-provider and read-only telemetry
  hooks, performance timing, optional presentation persistence and failed-result
  return. Both wrappers call this same loop; no copied negotiation/controller.
- `environment.py`: optional extra SUMO CLI arguments, default empty; evaluation
  disables teleporting and retains warning logs uniformly across methods.
- `README.md`: evaluation entry point and documentation links.

Showcase additions:

- `services/evaluation_reader.py`, `pages/component2_evaluation.py`,
  `tests/test_evaluation_reader.py`.

Showcase modifications:

- `app.py`: read-only route.
- `pages/component_detail.py`: evaluation link.
- `pages/component2_live_view.py`: correct ego-local execution wording.
- `tests/test_showcase.py`: retain the inspector regression check with the
  requested ego-local execution label.
- `README.md`: separate evaluation page.

Root `README.md` gains Windows launch/evaluation instructions. The E5 checkpoint,
selected configuration, validation/held-out artifacts, reward and existing
presentation scenario catalogue are preserved. Generated development preflight
artifacts use a separate directory and never enter the official matrix.

All metric definitions and research limitations are in
[FINAL_EVALUATION_SCOPE.md](FINAL_EVALUATION_SCOPE.md). No result here validates
real vehicles or intersection types outside the frozen domain.

## Verification recorded on this machine

- Full Component 2: **704 passed**, including existing real SUMO dense-traffic
  acceptance and the final evaluation contracts.
- Showcase: **74 passed**; quantitative and qualitative live routes returned
  HTTP 200. The quantitative page displayed archived smoke/degradation labels.
- Official smoke: **9 episodes; 5 PASS; 4 SAFE_DEGRADATION; 0 collisions observed;
  0 blocked-zone violations**. No unsafe or invalid episodes were observed.
- All nine integrity gates passed: unchanged checkpoint and actor/GNN tensors,
  evaluation mode, zero training/backward/optimizer/parameter-update/critic
  operations, zero centralized planner control calls, and unchanged frozen
  sources. Four controlled message-fault checks passed.
- Manifest SHA-256:
  `061324320e90e8a6387f9913ea6ce9cec4df86a819ab6cedc3304a51955eddf0`.
- `--prepare` re-verification and `--report-only` archive regeneration passed.
  Six standalone PNG and SVG plot pairs were generated; plot readability was
  inspected. The temporary verification server was stopped.

Smoke degradation is retained: rules-only did not complete the regulatory
cycle, and all three methods did not discharge the normal seed-101 demand
within the separate 90-second smoke budget. Completed-trip summaries for the
zero-completion cases are N/A. These are plumbing observations, not final
performance conclusions. The earlier 16-vehicle presentation remains separate.

An exact observed safe-degradation replay command, run from Component 2:

```powershell
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_final_evaluation.py --replay 20261006T155722766240Z_28f646e3 --gui
```

The **final 165-episode study has not been run**. Development preflight measured
approximately 112 wall seconds for a 180-s rules-only case and 262 wall seconds
for a 240-s normal-demand case. The maximum final budget is 62,100 simulated
seconds: roughly 11–19 wall hours if those slower-case rates persisted across
the complete matrix, with early completion reducing time and denser traffic
potentially increasing it. This is a workload estimate, not a runtime guarantee.
Launch the explicit `--suite final` command above when that CPU time is available.
