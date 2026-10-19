# Scalability / Operational Boundary — SCALABILITY_VALIDATION_V1

This separate study has seven scientific cases, exactly one deterministic
episode per load: SV-04, SV-08, SV-12, SV-16, SV-24, SV-32 and SV-40.
It preserves the panel V1/V2 evidence and previous diagnostics. It is a
targeted simulation observation, not a statistical universal capacity estimate.

## Audit before implementation

The reusable runtime is `post_training_evaluation.runner.run_episode`, which calls the
existing independent-demand `runtime_simulation.runner.run_runtime_simulation`. No negotiation
or vehicle-control algorithm is copied. `PanelDemand`, existing legal route IDs,
physical `select_queue_heads`, runtime integrity guards and `Telemetry` provide
the demand representation, <=4 queue-head negotiators, guarded inference and
per-vehicle travel/wait measurements. Followers retain native SUMO car-following.

Original PV-04B schedules four vehicles per approach at 1.5-second spacing;
PV-04A uses its separate predeclared movement mix with West offset six seconds.
Neither schedule nor recorded result is replaced. The study uses its own
symmetric arrival family, declared before any study episode, without selecting
an easier schedule after results. Prior panel failures are not evidence of a
specific capacity threshold for this new family.

The SUMO network has four 292.8-metre incoming lanes. The unchanged AV type
has length 5 metres and minGap 2.5 metres. The static jam-storage estimate is
floor((292.8+2.5)/(5+2.5)) = 39 vehicles per incoming lane, versus at most ten
requested here. All 40 vehicles should fit geometrically on the incoming lanes;
dynamic insertion at `departSpeed=max` is not guaranteed by that estimate.
The runtime submits due demand, then observes SUMO's actual departure events;
it does not wait for negotiation success to submit the next scheduled follower.

The deadlock early stop remains the existing evaluator criterion: telemetry
has observed a 15-second stop, all scheduled demand is physically spawned,
all active vehicles are incoming/stopped/held, and positions, decisions and
coordination remain exactly unchanged for the existing 15 seconds. Moving,
creeping, admitted or clearing traffic prevents that early stop. No position
tolerance or weaker deadlock definition is introduced. Pending insertion can
prevent early termination; the hard budget still bounds the episode.

## Frozen design

The 40-vehicle template consists of ten rounds ordered N, E, S, W. Round i
departs at 1.5*i seconds, from 0 through 13.5 seconds. All cases use an exact
prefix of that ordered template. Each approach cycles LEFT, STRAIGHT, RIGHT,
with initial phase offsets N=0, E=1, S=2, W=1. Thus the first round contains
N-left, E-straight, S-right, W-straight; every tested load has mixed movements,
and three rounds cover all twelve legal movements. Offsets specify traffic
demand only, not physical GO/STOP winners.

| Load | Vehicles per approach | Last requested departure (s) |
|---|---|---|
| 4 | 1 | 0 |
| 8 | 2 | 1.5 |
| 12 | 3 | 3 |
| 16 | 4 | 4.5 |
| 24 | 6 | 7.5 |
| 32 | 8 | 10.5 |
| 40 | 10 | 13.5 |

Every episode has the same 180-second hard budget: seven scientific episodes,
at most 1,260 simulated seconds in total. A separate SV-04 plumbing preflight
is labeled PREFLIGHT_NOT_SCIENTIFIC_RESULT and excluded from the seven points;
including preflight, there are at most eight initial launches and 1,440
simulated seconds. Replay is explicitly additional diagnostic evidence.

The unmodified scientific sampler uses masked stochastic sampling with one
fixed common seed across loads, not multi-seed testing or presentation argmax.
The shared scenario identity is `scalability_prefix_family`, so the existing
seed derivation SHA256(protocol_id, scenario_id, None, PROPOSED_MAPPO) modulo
2**31 yields the same action seed at every load. A fixed seed does not ensure
identical trajectories or matched random draws after different events.
SUMO seed stays zero. All physical parameters, safety settings, perception,
rules, ego execution and E5 weights are unchanged.

## Insertion and classifications

Raw delay is observed physical departure minus requested departure. Because
submission/observation is quantized to 0.04-second simulation steps, the delayed
vehicle count excludes delays <=0.08 seconds, frozen before execution.
Mean/max insertion delay retain all raw observed delays. Never-spawned demand
is reported separately with a lower bound on its outstanding requested delay;
it is not assigned a fabricated actual departure or waiting time.
Completion among scheduled and among spawned, plus unfinished spawned count,
are separate metrics. Original scheduled-demand team travel exposure is retained
and explicitly distinguished from physical spawned departure-to-exit/stop
exposure. Waits are incoming-lane measurements and are censored if unfinished.

NETWORK_CAPACITY_LIMIT requires pending due demand and continuously full static
storage on every affected approach for the existing 15-second duration, with
no observed SAFE_HOLD or BLOCKED_BY_PRECEDENCE on those approaches. The recorded
storage duration and held approaches accompany the verdict. This is deliberately
conservative: pending insertion alone cannot demonstrate a network-only limit.
Controller-related backpressure is labeled separately; indeterminate insertion
is labeled INSERTION_CAUSE_NOT_ESTABLISHED and does not claim a MAPPO failure.
This family does not exceed estimated static storage even at 40 vehicles.

Classification precedence: invalid integrity -> INVALID_EXPERIMENT;
observed collision/blocked-zone violation -> UNSAFE_FAILURE; other runtime
error -> INVALID_EXPERIMENT; full scheduled completion -> PASS;
demonstrated primary capacity limitation -> NETWORK_CAPACITY_LIMIT;
otherwise safe incomplete discharge -> SAFE_DEGRADATION. Capacity attribution
is not inferred just from the classification or number of requested vehicles.

## Evidence and interruption

The manifest freezes the full ordered template, each prefix, spacing,
movements, budget, metrics, classifications, sources, Python/SUMO versions,
geometry and E5 hash. Changed sources or demand are refused on resume/replay.
Attempt claims are created exclusively before scientific launches. Completed
raw records and separate normalized `study_result.json` files are checksummed;
the original runtime result is not rewritten. Reports validate result,
provenance and trace/log hashes. Each completed case is persisted and reported
before the next case starts. A completed raw result interrupted before study
normalization is recoverable without launching SUMO. An attempt without a
complete raw record is retained as INVALID_EXPERIMENT on resume, and is never
silently retried. Other unattempted cases can continue. Do not run two study
commands concurrently.

Root CLI files are part of the existing shared source-identity scanner. Adding
this new CLI therefore changes the current whole-project identity set; old
manifests remain immutable historical evidence, and their strict current-source
replay checks may reject the expanded checkout. This does not alter operational
files. Original V1 replay continues through its existing archived runtime;
reproducing V2 with its original frozen environment requires its original
source set. Never rewrite an old manifest to bypass that check.

The read-only HTML/Markdown report and seven measured-point PNG plots use
recorded scientific evidence only. Missing loads remain NOT_RUN/N/A. Invalid
runs remain visible in the table and are excluded from numerical trend plots.
There is no interpolation, confidence interval, or assumed capacity between
observed points. The existing showcase and panel reports are unchanged.

## PowerShell commands

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"

# Freeze / validate the same immutable version.
& $projectPython -B run_scalability_validation.py --prepare

# One plumbing check; reuses its recorded receipt on repeated invocation.
& $projectPython -B run_scalability_validation.py --preflight

# Explicitly start the seven scientific loads in ascending order.
& $projectPython -B run_scalability_validation.py --run

# Resume: same command; completed cases are reused and interrupted attempts retained.
& $projectPython -B run_scalability_validation.py --run

# Rebuild/open report without simulation.
& $projectPython -B run_scalability_validation.py --report-only
Start-Process "results\scalability_validation\v1\latest\SCALABILITY_REPORT.html"

# Replay recorded scientific SV-04 (additional diagnostic, not another scientific result).
& $projectPython -B run_scalability_validation.py --replay SV-04 --gui

# Select/replay the smallest recorded degraded or unsafe scientific case.
$studySummary = Get-Content "results\scalability_validation\v1\latest\scalability_summary.json" -Raw | ConvertFrom-Json
$firstDegraded = $studySummary.rows | Where-Object { $_.classification -in @('SAFE_DEGRADATION','UNSAFE_FAILURE','NETWORK_CAPACITY_LIMIT') } | Sort-Object count | Select-Object -First 1
if ($null -ne $firstDegraded) {
    & $projectPython -B run_scalability_validation.py --replay $firstDegraded.case_id --run-id $firstDegraded.run_id --gui
}
```

Before scientific runs exist, replay the recorded preflight by supplying its
exact run ID (the ordinary SV-04 replay defaults to scientific evidence):

```powershell
$preflightReceipt = Get-Content "results\scalability_validation\v1\preflight\latest.json" -Raw | ConvertFrom-Json
& $projectPython -B run_scalability_validation.py --replay SV-04 --run-id $preflightReceipt.run_id --gui
```

The old 165-episode suite is never invoked by these commands. Do not edit
sources after freezing, select alternate schedules from results, retrain,
or create another output root to retry a failed scientific load.

## Files

Created: `scalability_validation/__init__.py`, `cases.py`, `models.py`,
`metrics.py`, `runner.py`, `reporting.py`; `run_scalability_validation.py`;
`tests/test_scalability_validation.py`; this guide. No existing source file is
modified. New evidence is confined to `results/scalability_validation/`.
Pre-edit SHA-256 inventories cover 1,068 prior evidence files and 92 existing
evaluation/control/network source/input files under its separate audit folder.

## Implementation verification — 9 October 2026

The focused test selection passed **68 tests in 22.13 seconds**, including
existing panel V1/V2 contracts and the existing runtime guard and per-vehicle
measurement tests. No existing tests were deleted or weakened.

```powershell
& $projectPython -B -m pytest tests/test_scalability_validation.py tests/test_targeted_validation.py tests/test_panel_dense_v2.py tests/test_post_training_evaluation.py::test_integrity_guards_all_runtime_operations_and_tensor_updates tests/test_post_training_evaluation.py::test_waiting_approach_gap_and_emergency_evidence_only_incoming_period -q
```

Frozen manifest:
`828d74f1968a86c3a37e2a470ceac83a6d8a2cdc1929bbb3caf0feb066447348`.
One SV-04 preflight was executed, run
`20261009T070359876230Z_e099dfe0`. It took **24.7666 seconds wall time**,
with **38.08 simulated seconds**, four scheduled/spawned, zero completed,
and DEADLOCK_CONFIRMED termination. Its traffic classification is
SAFE_DEGRADATION, not a successful operating-point result. It had zero MAPPO
inference calls; this preflight checks runtime plumbing and guard binding,
not successful MAPPO negotiation. No scientific load result is inferred from it.

Collisions, blocked-zone violations and native emergency-braking events were
zero. All four vehicles spawned with raw delay 0.04 seconds, below the frozen
two-step delayed-insertion tolerance; no demand remained unspawned. Maximum
physical queue-head participants was four. Training, backward, optimizer,
parameter-update, critic and global-execution counters were zero; execution
remained decentralized and the E5 hash was unchanged:
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

The conservative projection is **8770.80 seconds / 146.18 minutes**, using
max(preflight wall/sim ratio, preserved PV-04A wall/sim ratio * 40/16) * 1260.
This is a planning estimate, not a measured full-study runtime; deadlock early
stops could substantially shorten it. It exceeds the requested 45-minute
automatic-start limit, so **the seven scientific episodes were not started**.
The report shows all seven loads as NOT_RUN; its charts display no invented
points. The marked preflight receipt is shown separately. No replay or old
165-episode study was executed. Use the explicit `--run` command above when
ready; no additional approval or schedule redesign is required by this guide.
