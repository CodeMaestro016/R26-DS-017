# Review and run the repair candidate

V1 is preserved diagnostic evidence. Do not resume its full evaluation.
No V2 final manifest is frozen during repair. Fresh final seeds remain unrun.
Review the audit and four diagnostic results before authorizing preparation.
Current validation is **not accepted**: three targeted cases deadlock and two
existing dense-discharge tests fail. The preparation command below is provided
for use only after further repair, passing regression checks and your review.

Use the installed environment and SUMO on PATH:

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
```

Focused repair checks:

```powershell
& $projectPython -B -m pytest tests/test_runtime_v2_safety.py tests/test_v2v_joint_graph.py tests/test_traffic_rules.py tests/test_post_training_evaluation.py -q
```

Complete Component 2 tests (the dense integration test reaches its original
360-second simulation budget and can take several minutes):

```powershell
& $projectPython -B -m pytest tests -q
```

Showcase tests:

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& $projectPython -B -m pytest socialmind_drive_showcase/tests -q
Set-Location component_2_right_of_way_negotiation
```

Only the four targeted regressions, all PROPOSED_MAPPO:

```powershell
& $projectPython -B run_post_training_evaluation.py --diagnostics --output-root "results\post_training_evaluation\v2_candidate\diagnostics_next"
```

This uses 180-second functional budgets and 240-second normal budgets with
old diagnostic demand seeds 404 and 606. It creates a diagnostic identity,
not a final manifest. Repeat runs remain separate immutable evidence; the
report retains every result rather than selecting favorable attempts.
Code changes require a separate `--output-root` for diagnostic identity.
The first four cases remain under `diagnostics/`; the revised four are under
`diagnostics_followup/`. Both identities are preserved. The unused `diagnostics_next/`
root above is necessary for another run because reporting code subsequently
changed to show an event-weighted fallback rate. No new simulation is needed
to view the recorded results.

Rebuild/view the targeted report without simulation:

```powershell
& $projectPython -B run_post_training_evaluation.py --diagnostic-report --output-root "results\post_training_evaluation\v2_candidate\diagnostics_followup"
Get-Content "results\post_training_evaluation\v2_candidate\diagnostics_followup\latest\diagnostic_report.md"
```

Full scalar metrics are in `diagnostic_metrics.csv`; source identities,
integrity counters, vehicle measurements and exact action seeds are in
`diagnostic_report.json`. Every immutable run stores its execution trace,
warnings, runtime log, result, provenance and checksums.

Verify preserved V1 checksums, both measured runtime archives and diagnostic
integrity records, then view the validation receipt:

```powershell
& $projectPython -B results/repair_diagnostics/verify_repair_evidence.py
Get-Content "results\repair_diagnostics\validation_summary.json"
```

Saved test outputs are `focused_tests.log`, `component2_full_tests.log` and
`showcase_tests.log` in `results/repair_diagnostics/`. The receipt states
`ready_for_post_training_evaluation=false` while the liveness regressions remain.

Replay commands for each recorded diagnostic are printed in the targeted
report. They preserve the stored demand, method, action seed and budget,
verify the code identity, and create a new REPLAY_NOT_FINAL record. The CLI
automatically launches the verified archived runtime when live code differs:

```powershell
$diagnosticReport = Get-Content "results\post_training_evaluation\v2_candidate\diagnostics_followup\latest\diagnostic_report.json" -Raw | ConvertFrom-Json
$diagnosticReport.runs | Select-Object scenario_id, seed, classification, run_id, replay_command
# Copy the exact command for the desired case from the table/report.
```

Exact commands for the four revised cases (omit `--gui` for headless replay):

```powershell
& $projectPython -B run_post_training_evaluation.py --replay 20261006T192946172004Z_6b805454 --gui --output-root "results\post_training_evaluation\v2_candidate\diagnostics_followup"
& $projectPython -B run_post_training_evaluation.py --replay 20261006T193004008860Z_88cadbf8 --gui --output-root "results\post_training_evaluation\v2_candidate\diagnostics_followup"
& $projectPython -B run_post_training_evaluation.py --replay 20261006T193211774863Z_646190d8 --gui --output-root "results\post_training_evaluation\v2_candidate\diagnostics_followup"
& $projectPython -B run_post_training_evaluation.py --replay 20261006T193745936845Z_d4d3fe57 --gui --output-root "results\post_training_evaluation\v2_candidate\diagnostics_followup"
```

Only after the diagnostic results are reviewed and accepted, explicitly
prepare the separate V2 final manifest:

```powershell
& $projectPython -B run_post_training_evaluation.py --prepare --output-root "results\post_training_evaluation\v2_candidate"
```

This freezes the current code, configuration/model assets, unchanged E5
checkpoint, corrected runtime versions, stochastic inference rule, fresh
ten-seed list and fixed budgets. Preparation has not been run automatically.
The full 165-episode V2 suite is not run as part of this repair.
