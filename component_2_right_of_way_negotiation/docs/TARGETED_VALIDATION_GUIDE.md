# Targeted Targeted Validation

This is a small evaluation wrapper, not an algorithm repair or replacement of
the 165-episode Post-Training Evaluation. The existing ego controller, rules, MAPPO
weights, trained KEEP/RELINQUISH semantics, physics and safety behavior are
unchanged. The scientific evaluator uses the existing seeded stochastic masked
sampler; presentation argmax remains separate.

The exact design has six cases, six traffic episodes and controlled message
checks. PV-01 reuses `rule_resolved_two` (2 vehicles, 60 s). PV-02 reuses
`regulatory_cycle` (4 vehicles, MAPPO and Rules Only on identical demand, 90 s
each). PV-03 reuses `multiple_left_turns` (3 vehicles, 90 s). PV-04 reuses the
unmodified `congested_four_approach` schedule (16 vehicles, four per approach,
all 12 movements, 1.5-s arrival headway, 180 s). PV-05 reuses
`four_way_simultaneous` (4 vehicles, 60 s). PV-06 reuses the existing controlled
missing/stale coordination and clearance checks. No random-seed matrix or FCFS
algorithm comparison is added. The maximum traffic budget is **570 simulated
seconds**, not an estimate of wall-clock runtime.

`results/panel_validation/v1/manifest.json` freezes cases, exact schedules,
methods, budgets, complete operational source identities, evaluator source
identities, unchanged E5, controller/shield versions, metric definitions and
deadlock criterion before measurement. Later definition/code changes require
a new `--output-root`, such as `results/targeted_validation/v2`. Existing records
are never overwritten. `--run` resumes only missing episodes; replays and
preflight are excluded from the six-episode evidence. Corrupted records or
changed sources are rejected rather than silently replayed under new code.

Use the project's installed Python environment with SUMO on PATH:

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
& $projectPython -B -m pytest tests/test_targeted_validation.py ../socialmind_drive_showcase/tests/test_targeted_validation_reader.py -q
& $projectPython -B run_targeted_validation.py --prepare
& $projectPython -B run_targeted_validation.py --preflight
```

Preflight runs only PV-01 plus quick fault checks, labelled
`PREFLIGHT_NOT_PANEL_CASE_EVIDENCE`. It measures actual wall time and gives a
qualified full-budget projection, including an available historical test-wall
reference for the expensive dense fixture. A two-vehicle run cannot predict
all dense costs. Preflight never automatically launches the complete suite.
If the projection exceeds approximately 30 minutes, review the recorded timing
and per-step perception/V2V/controller overhead before starting.

Run the complete compact suite manually:

```powershell
& $projectPython -B run_targeted_validation.py --run
```

Regenerate/view the report without simulation:

```powershell
& $projectPython -B run_targeted_validation.py --report-only
Get-Content "results\targeted_validation\latest\TARGETED_VALIDATION_REPORT.md"
Start-Process "results\targeted_validation\latest\TARGETED_VALIDATION_REPORT.html"
```

Replay recorded cases (SUMO GUI); all cases also accept `--run-id` to select
the exact immutable run. PV-02 supports `--method RULES_ONLY`. Omit `--gui`
for headless replay. A case must have a recorded episode; a preflight may be
replayed using its specific run ID. PV-06 reruns only message checks.

```powershell
& $projectPython -B run_targeted_validation.py --replay PV-01 --gui
& $projectPython -B run_targeted_validation.py --replay PV-02 --gui
& $projectPython -B run_targeted_validation.py --replay PV-02 --method RULES_ONLY --gui
& $projectPython -B run_targeted_validation.py --replay PV-03 --gui
& $projectPython -B run_targeted_validation.py --replay PV-04 --gui
& $projectPython -B run_targeted_validation.py --replay PV-05 --gui
& $projectPython -B run_targeted_validation.py --replay PV-06
```

Exact run replay commands are printed in the report. Replay restores the
stored schedule, method, stochastic action seed and original case budget;
source/Python/SUMO identity checks fail closed. New replay runs have separate
IDs and never replace the panel results.

Early termination is evaluator-side only. Completion and observed collisions
can end immediately; an operational blocked-zone invariant failure is preserved
as unsafe. Deadlock stopping uses the existing 15-s telemetry duration and
stopped-speed criterion, with extra conservative conditions: all scheduled
vehicles have actually spawned, no future demand remains, every active vehicle
is on an incoming lane, every execution decision is held/blocked, no vehicle
has an admission lock or is clearing, and positions/decision/status evidence
remain unchanged for the same 15 seconds. A single waiting follower cannot
terminate the episode. If the detector cannot confirm this, the frozen hard
budget remains the stop. Results retain ALL_COMPLETED, UNSAFE_FAILURE,
DEADLOCK_CONFIRMED or HARD_TIME_BUDGET; unexplained aborts are invalid and retain
their error instead of pretending the budget expired.

Metrics in plain English:

- **Completion:** vehicles that left the network, divided by scheduled demand.
- **Collisions / blocked-zone violations:** observed SUMO collisions and rejected
  entry into a prohibited conflict zone. No manufactured failures.
- **Waiting:** stopped time on incoming lanes, including followers. Mean,
  median, p95 and maximum summarize measured waits. Unfinished waits are lower
  bounds; absent observations are N/A.
- **Total team travel time (TTT):** total time all scheduled demand remains
  unfinished, including delayed insertion. Unfinished demand is censored at
  the actual stop. Early-stop TTT must not be treated as full-budget TTT or
  compared alone without completion and stop time.
- **Throughput:** completed vehicles per observed simulated minute.
- **N/E/S/W mean wait and approach gap:** each approach's mean wait, and the
  largest minus smallest of the four. No arbitrary combined fairness score.
- **FCFS inversion rate:** fraction of conflicting served pairs whose order
  differs from arrival order. It is N/A when no eligible pair was served.
- **MAPPO calls, accepted/rejected outcomes and fallbacks:** measured learned
  negotiation activity and safety-shield interventions. Fallback-resolved
  events retain MAPPO_WITH_SAFETY_FALLBACK rather than MAPPO_DIRECT.
- **Fallback rate:** fallback epochs / MAPPO epochs; N/A with no MAPPO epochs.
- **Max active/moving and queue depth:** measured traffic occupancy, moving
  vehicles and incoming-lane queue depth per approach. Negotiators remain <=4
  even when total live traffic is larger.
- **Timeout / deadlock:** hard-budget expiry and the existing observed stalled
  condition are separate. The explicit termination reason shows why evaluation
  actually stopped.
- **Architecture / integrity:** measured decentralized execution, unchanged
  checkpoint/tensors, evaluation mode, and guard counts for critic, training,
  backward, optimizer, parameter updates and global physical execution.

PASS requires valid integrity, safe execution and complete demand.
SAFE_DEGRADATION retains safe incomplete/deadlocked episodes. UNSAFE_FAILURE
retains collisions or blocked-zone violations. INVALID_EXPERIMENT retains
integrity breaches, unsupported graphs, corrupted/nonfinite evidence or
unexplained aborts. Failure does not mean the requested evaluation was omitted.

The report maps all three comments to concrete case evidence. “Comment
addressed” means implemented and measured, not necessarily passed. Unrun cases
stay NOT_RUN. The existing Component 2 showcase displays only checksum-verified
backend values in a small Targeted Validation section; it does not compute metrics
or run simulations. Existing qualitative live demonstrations remain separate.

This targeted suite validates the implementation against the specific panel
feedback within the defined SUMO scope. It is not an exhaustive statistical
study and is not real-world deployment validation. Real-world trajectory data
supports the intention-model component, while right-of-way system validation
in this study is simulation-based. The existing two dense-discharge test
failures remain a known liveness limitation; this task does not change their
assertions or the algorithm to force them to pass.

Files created: `targeted_validation/__init__.py`, `cases.py`, `models.py`,
`metrics.py`, `runner.py`, `reporting.py`; `run_targeted_validation.py`;
`tests/test_targeted_validation.py`; this guide;
`socialmind_drive_showcase/services/targeted_validation_reader.py`,
`socialmind_drive_showcase/pages/component2_targeted_validation.py`,
`socialmind_drive_showcase/tests/test_targeted_validation_reader.py`.
Files modified: `post_training_evaluation/runner.py` (optional evaluator observer,
stop normalization and replay/evidence labels; default final path unchanged),
`socialmind_drive_showcase/pages/component_detail.py` (read-only section).
Generated manifests, preflight receipts, logs, traces and reports live only
under `results/targeted_validation/`. No full final manifest or final suite is run.

Implementation verification (8 October 2026): the focused wrapper/showcase
checks passed **25 tests in 6.84 seconds**. The actual preflight took
**8.7874 seconds**, observed 48.76 simulated seconds and completed 2/2 vehicles
with PASS, zero collisions/blocked-zone violations, zero MAPPO calls and valid
runtime integrity. Controlled missing/stale message checks passed. This is
preflight evidence only; the six traffic episodes have not run automatically.
The panel report intentionally keeps unrun cases NOT_RUN and metrics N/A.
The qualified full-budget projection is 1115.09 seconds (about 18.6 minutes),
using the previous full-test wall time as a conservative dense-cost reference
rather than promising an exact runtime. Receipts are
`results/panel_validation/v1/preflight/latest.json` and
`results/panel_validation/v1/post_implementation_verification.json`.
All 337 inventoried V1 evidence files and 73 operational source files remain
unchanged. Runtime training/backward/optimizer/parameter-update and critic
calls were zero; physical execution remained decentralized.

Frozen panel manifest hash:
`47463a1bb524da477ccc47a619999359cb5250b5e18fbe24e18a5aeec96aafd7`.
Selected E5 SHA-256 before and after:
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
