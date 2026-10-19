# Reviewed panel V2 commands

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
& $projectPython -B -m pytest tests/test_targeted_validation.py tests/test_panel_dense_v2.py ../socialmind_drive_showcase/tests/test_targeted_validation_reader.py -q
```

The approved one-time measurement is:

```powershell
& $projectPython -B run_targeted_validation.py --prepare
& $projectPython -B run_targeted_validation.py --case PV-04A
```

After a case is recorded the one-case command refuses to repeat it. Use replay
to inspect the same demand, action seed and budget instead. The seven-episode
suite is not started automatically:

```powershell
& $projectPython -B run_targeted_validation.py --run
```

That command resumes missing V2 cases only. It does not invoke the 165-episode
study. Historical V1 records remain visible even when new V2 cases are run.

Replay nominal PV-04A, or the original critical V1 record now called PV-04B:

```powershell
& $projectPython -B run_targeted_validation.py --replay PV-04A --gui
& $projectPython -B run_targeted_validation.py --replay PV-04B --run-id 20261008T171632326120Z_c654aaee --gui --output-root "results\targeted_validation\v1"
```

V1 replay verifies the archived runtime/assets and original checksums, then
executes that version in a separate process. New replay evidence goes to
`results/targeted_validation/replays/v1/`, never to V1 itself. Omit `--gui` for
headless replay. No replay is automatically executed in this task.

Open or regenerate the updated V2 report:

```powershell
& $projectPython -B run_targeted_validation.py --report-only
Get-Content "results\targeted_validation\v2\latest\TARGETED_VALIDATION_REPORT.md"
Start-Process "results\targeted_validation\v2\latest\TARGETED_VALIDATION_REPORT.html"
```

The existing V1 report remains at
`results/panel_validation/latest/PANEL_VALIDATION_REPORT.html`. The read-only
showcase now reads the separate V2 report summary. Both dense cases are
displayed, with historical rows explicitly identified.

To run the complete production regression suite later (not run in this task):

```powershell
& $projectPython -B -m pytest tests -q -rxX
```

Two original complete-discharge assertions are strict known expected failures
for the documented critical liveness limitation. Safety, integrity and actual
live-state consistency must still pass; recovered liveness is strict XPASS.
This is transparent test accounting, not a claim the defect was repaired.
