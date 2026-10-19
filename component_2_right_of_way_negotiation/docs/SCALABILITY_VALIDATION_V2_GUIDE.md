# SCALABILITY_VALIDATION_V2 — staggered operational-boundary study

V1 remains historical/preflight evidence. Its four simultaneous initial
departures produced 0/4 completion, DEADLOCK_CONFIRMED and zero MAPPO calls.
Every longer prefix inherited that opening, potentially preventing additional
traffic from affecting outcomes. This limits scalability interpretation; it
does not establish that all unexecuted V1 scientific cases would behave alike.
No V1 scientific load is executed as part of this revision.

V2's objective is to measure increasing total scheduled population while
avoiding artificially identical initial four-way requested departure times.
Requested staggering does not guarantee separated junction arrival times,
negotiation eligibility or liveness. If the new preflight also fails, that
failure is retained; spacing and movement combinations will not be tuned.

## Predeclared demand

The ordered 40-entry stream repeats N, E, S, W for ten rounds. Entry k
requests departure at round(k*0.4, 10) seconds, k=0..39. Interarrival is fixed
at 0.4 seconds; per-approach headway is 1.6 seconds. The final requested
departure is 15.6 seconds. Original legal movements and sequence indices
remain identical to V1: each approach cycles LEFT, STRAIGHT, RIGHT with phase
offsets N=0, E=1, S=2, W=1. No movement search or outcome-based spacing choice
is performed. This is a new evaluation-demand family, not a controller fix.

| Entry | Legal movement | Requested departure (s) |
|---|---|---|
| N1 | N_IN_0_LEFT | 0.0 |
| E1 | E_IN_0_STRAIGHT | 0.4 |
| S1 | S_IN_0_RIGHT | 0.8 |
| W1 | W_IN_0_STRAIGHT | 1.2 |
| N2 | N_IN_0_STRAIGHT | 1.6 |
| E2 | E_IN_0_RIGHT | 2.0 |
| S2 | S_IN_0_LEFT | 2.4 |
| W2 | W_IN_0_RIGHT | 2.8 |
| N3 | N_IN_0_RIGHT | 3.2 |
| E3 | E_IN_0_LEFT | 3.6 |
| S3 | S_IN_0_STRAIGHT | 4.0 |
| W3 | W_IN_0_LEFT | 4.4 |

SV-04/08/12/16/24/32/40 expose exactly the first 4/8/12/16/24/32/40 entries,
giving 1/2/3/4/6/8/10 vehicles per approach. Total count is the only intended
independent variable within V2. Arrival spacing, geometry, physical settings,
movement sequence, rules, policy, safety and execution stay fixed across loads.

The budget stays 180 simulated seconds per episode, at most 1,260 scientific
simulated seconds for seven loads. A separate SV-04 preflight is explicitly
PREFLIGHT_NOT_SCIENTIFIC_RESULT, excluded from trends. Only one V2 preflight
is authorized for this implementation task; neither seven-load study nor the
old 165-episode study is started, regardless of the runtime projection.

## Unchanged implementation and interpretation

V2 reuses the exact `post_training_evaluation.runner.run_episode` control-loop wrapper,
scientific masked stochastic sampler, IntegrityGuard and operational runtime.
The observer module is copied byte-for-byte from V1, with imports resolving
to V2's own immutable source inventory. No operational algorithm is duplicated
or changed. V2 reporting and manifest handling are separate evaluation code.
The shared V2 scenario identity keeps one action seed across loads under the
existing protocol-based derivation; the new protocol namespace produces a V2
seed distinct from V1. This is a versioned reproducibility seed, not retraining
or a new policy. V1/V2 outcomes are not a matched-seed causal comparison.

Same E5 checkpoint SHA-256:
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
Same intersection, rules and vehicle parameters; ego-local execution, native
SUMO follower car-following, <=4 physical queue-head negotiators, zero critic
calls, zero training and no global execution graph as physical authority.

Metrics, classifications, delayed-insertion tolerance, capacity attribution
and conservative deadlock criterion are unchanged from V1. Unspawned demand
is not counted as a failed negotiation. A hard-budget result is not relabeled
DEADLOCK_CONFIRMED unless the existing exact-stationarity detector fires.
The fixed arrival interval is an exogenous demand rule, not a GO/STOP script.

The V2 manifest freezes the entire sequence, all prefixes, 0.4-second spacing,
1.6-second per-approach headway, budget and metric/classification definitions,
source identities and E5 hash. Changed schedules/sources are rejected; there
are no performance retries. V1 destinations and archived evidence are
explicitly protected from V2 writes. Existing V1 reports remain unchanged.

## Preservation and files

The pre-edit inventory covers 1,092 existing evidence files, including every
V1 scalability file, panel V1/V2 and earlier diagnostic/final-evaluation
evidence. It is stored outside those evidence families at
`results/scalability_validation/audit_v2/prior_evidence_inventory.json`.
An original V1 runtime/model snapshot contains 182 files at
`results/scalability_validation_archives/v1/runtime/`, with a SHA-256 inventory.
This preserves the original CLI and exact evaluator sources for historical
inspection. No historical simulation is replayed in this task.

Created: `scalability_validation/v2/{__init__,cases,models,metrics,runner,reporting}.py`,
`tests/test_scalability_validation_v2.py`, this guide. Modified:
`run_scalability_validation.py` dispatches V2 by default and rejects V1
launches. The original six V1 package files and original tests remain intact.
The new CLI changes the whole-project source identity; old manifests are not
rewritten to match the expanded checkout. Original V1 sources are archived.
All new evidence is under `results/scalability_validation/v2/`.

## Commands used for this task

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"

& $projectPython -B -m pytest tests/test_scalability_validation_v2.py tests/test_scalability_validation.py tests/test_targeted_validation.py tests/test_panel_dense_v2.py tests/test_post_training_evaluation.py::test_integrity_guards_all_runtime_operations_and_tensor_updates tests/test_post_training_evaluation.py::test_waiting_approach_gap_and_emergency_evidence_only_incoming_period -q
& $projectPython -B run_scalability_validation.py --version v2 --prepare
& $projectPython -B run_scalability_validation.py --version v2 --preflight

# Open V2 report without launching a simulation.
Start-Process "results\scalability_validation\v2\latest\SCALABILITY_REPORT.html"

# Historical V1 report remains available separately.
Start-Process "results\scalability_validation\v1\latest\SCALABILITY_REPORT.html"
```

Pre-run planning reference: V1 preflight took 24.77 seconds wall time; a
four-vehicle episode can take seconds to several minutes depending on early
termination. The conservative seven-load estimate was 146.18 minutes from
preserved PV-04A wall/sim time scaled by 40/16 and the 1,260-second budget.
V2 recomputes the planning estimate using its preflight and the same historical
reference. This is not measured seven-load runtime; no full study is run.

## Recorded implementation outcome — 9 October 2026

Final focused checks: **83 passed in 29.65 seconds**. Tests include the exact
first twelve V2 entries, balanced legal prefixes, unchanged V1 movements,
unchanged observer implementation, source/evidence preservation and refusal
to launch V1 or write V2 outputs into historical evidence roots.

Frozen V2 manifest:
`7b8ad8d40ccf1c0ab9996c7eca4d1c11fc8587a63c07258ac10ae4e93eedfda2`.
Only one V2 SV-04 preflight was run:
`20261009T073517867706Z_b8f9f892`.

| Preflight metric | Recorded value |
|---|---|
| Scheduled / physically spawned | 4 / 4 |
| Completed | 0 / 4 |
| Traffic classification | SAFE_DEGRADATION |
| Stop reason | DEADLOCK_CONFIRMED |
| Observed simulated time | 38.56 s |
| Wall time | 32.9929471 s |
| MAPPO inference calls | 1 |
| Collisions / blocked-zone violations | 0 / 0 |
| Native emergency braking events | 0 |
| Maximum negotiation participants | 4 |
| Never spawned / delayed insertion count | 0 / 0 |

The staggered preflight invoked MAPPO, unlike the original synchronized
preflight, but still deadlocked without completing a vehicle. It does not
establish successful operation or a scalability trend. Different protocol
seeds and timing mean this is not an isolated causal demonstration that
staggering alone changed MAPPO invocation. No spacing or movement change was
made after observing the result; no additional traffic episode was run.

Integrity was valid. Training, backward calls, optimizer steps, parameter
updates, critic runtime calls and global execution calls were all zero.
Execution remained decentralized; no global execution graph controlled
physical motion. E5 before/after SHA-256 remained
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

Projected seven-case hard-budget runtime is **8770.80 seconds / 146.18 minutes**
under the same conservative preflight/historical planning formula. No V1 or V2
scientific loads were started, irrespective of this estimate. The V2 report
lists seven NOT_RUN cases, with the marked preflight receipt separately.
All 1,092 original evidence files and 182 archived V1 runtime/assets passed
post-run SHA-256 checks. Frozen operational, panel and V2 source sets also
matched their manifest identities. The machine-readable verification receipt
is `results/scalability_validation/v2/post_implementation_verification.json`.
