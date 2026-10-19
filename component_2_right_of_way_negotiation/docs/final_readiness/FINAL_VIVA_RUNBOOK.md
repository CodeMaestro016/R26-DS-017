# Final viva runbook — SOCIALMIND DRIVE

## Verified environment and startup

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& "C:\R26-DS-017\venv\Scripts\Activate.ps1"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
& $projectPython --version
Get-Command sumo
sumo --version
& $projectPython -m pip check
# Install only missing declared dependencies if needed; do not retrain or upgrade models.
& $projectPython -m pip install -r socialmind_drive_showcase\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements-training.txt

# Desktop, one resizable native window:
& $projectPython -B socialmind_drive_showcase\app.py
# Alternative browser/server-only mode:
& $projectPython -B socialmind_drive_showcase\app.py --server-only
# If port 8088 is occupied, close the old app or explicitly choose a free port:
& $projectPython -B socialmind_drive_showcase\app.py --server-only --port 8099
```

The existing environment is Python 3.13.1 with SUMO 1.26.0. Use the explicit
Python path if PowerShell activation is blocked; do not change global execution
policy just for this demo. The first install commands are recovery instructions,
not permission to change frozen scientific software/configuration indiscriminately.
Desktop uses pywebview; Stop/shutdown uses psutil for the owned process tree.

## Live demonstration

1. Open http://127.0.0.1:8088/component/right-of-way and its Live View. Use the
   chosen port if different. Navigation/layout/project names are unchanged.
2. Select **Congested Four-Approach Queues (16 vehicles)** while idle. The
   existing default rolling traffic presentation is also selectable.
3. Press **Run Scenario** once. It launches the real existing SUMO runtime with
   the selected scenario, E5, original vehicle parameters and original budget.
4. Wait for a fresh frame. LAUNCHING, RUNNING, STOPPING and FAILED are process
   states, not scientific classifications. Old frames are not a new launch.
5. Show simulation time, measured active/moving counts, N/E/S/W queues, current
   participants, peak traffic, MAPPO evidence, collisions and execution mode.
   N/A means unavailable, not an invented zero. The visual negotiation highlight
   is a display overlay; it never changes SUMO stepping or driving decisions.
6. Press **Stop** once; wait for idle. Cooperative stop is attempted first;
   only this launch's owned tree is terminated if grace expires. Do not kill
   every python.exe or sumo.exe process. Switch scenarios only while idle.
7. Close the app window or stop the server with Ctrl+C. Application shutdown
   requests cleanup of the owned simulation. Confirm the process stops before
   relaunching. Per-launch logs are in results/runtime_simulation/runtime/.

Standalone existing GUI demonstration (qualitative, not quantitative):

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
& $projectPython -B run_runtime_simulation.py --scenario congested_four_approach --gui
```

The scientific schedule is unchanged; 16 scheduled vehicles do not guarantee
16 simultaneously spawned or completed. The current congested runtime can
stall. Do not rerun repeatedly until a favorable demonstration is obtained.

## Read-only quantitative evidence

Open http://127.0.0.1:8088/component/right-of-way/evaluation. It distinguishes
34 checksum-verified archived V1 final records out of 165 from the saved
nine-episode SMOKE_NOT_FINAL comparison. Final outcomes are 10 PASS,
22 SAFE_DEGRADATION and 2 UNSAFE_FAILURE. No V2 final manifest is accepted.
This is an incomplete archive, not a completed 165-episode study.

Authentic saved files (do not regenerate or edit in place):

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
Start-Process "results\final_evaluation\latest\PANEL_EVALUATION_REPORT.html"
Start-Process "results\panel_validation\v2\latest\PANEL_VALIDATION_REPORT.html"
Get-Content "docs\final_readiness\DENSE_TRAFFIC_EVIDENCE_SUMMARY.md"
Get-Content "docs\final_readiness\FINAL_EVALUATION_PREFLIGHT.md"
```

The first saved HTML report is smoke evidence. The targeted report includes
the severe nominal/critical dense liveness failures. Broader scalability is
NOT_RUN. These results must remain visible even when showing an older successful
16-vehicle presentation. Saved qualitative success and current inference differ
by purpose/mode/runtime provenance and must not be pooled into a success claim.

## Defensible explanations

MAPPO supplies trained semantic KEEP/RELINQUISH and ACCEPT/REJECT actions only
when negotiation is authorized. German-rule precedence, protected obligations
and deterministic safety checks still govern legal/physical execution. A real
actor invocation is not automatically a successful negotiation or completed trip;
separate direct MAPPO, safety fallback, rule resolution and safe holding.

Total traffic can exceed four because followers wait under native car-following.
At most one physical queue head per incoming approach is currently negotiation
eligible; after rear clearance, the next follower is promoted. This is traffic
support beyond four vehicles, not validation of a >4-node MAPPO policy graph.

Safety and liveness are different. Zero observed collisions/blocked-zone
violations in a case does not establish efficient or fair discharge. PV-04A
completed 1/16; PV-04B 0/16. Unfinished wait/exposure is censored, no-completion
trip statistics are N/A, and a small observed wait gap is not proof of fairness.
One AV-only unsignalized intersection and ideal messages limit generalization.

## Failure contingency

If startup fails, read the on-page error and owned launch log; verify Python,
SUMO PATH, model files and dependencies. Do not replace the failure with a
success label or alter safety/physics. If frames become stale, show the warning,
request Stop and wait for cleanup. If the port is busy, use a new port rather
than terminating unrelated processes. For a missing model, restore the exact
frozen artifact from the full research archive; do not train a replacement.

During a viva failure, explicitly state what failed, then show authentic saved
reports and the dense comparison. The package is for demonstration; keep the
full research archives separately. Do not launch the long final/scalability
studies during the viva or without acceptance review and explicit approval.

## Rehearsal status

Full active tests and short real launch/stop/HTTP checks passed as documented
in FINAL_TEST_VERIFICATION.md. No connected Browser was available for visual
interaction checks. Rehearse desktop window opening/closing and page clicks on
the actual presentation machine before the viva; do not claim that was visually
verified in this session.
