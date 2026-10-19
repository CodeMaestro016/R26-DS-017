# Live traffic deadlock: reproduced diagnosis and correction approval boundary

16 October 2026. **Diagnosis completed; substantive runtime correction requires
approval under Phase 5 of the supplied task. No production implementation has
been changed.** These are bounded diagnostic runs, not final quantitative results.

## A. Architecture and root cause

Canonical execution: `socialmind_drive_showcase/config.py` configures
`services/component_launcher.py`, which starts `run_runtime_simulation.py` in
Component 2. That entry point selects the existing immutable scenario and calls
`runtime_simulation/runner.py:run_runtime_simulation`. Compatibility aliases
delegate to the same runtime; they are not alternate control implementations.

SUMOEnv steps real SUMO. ObservationManager builds each ego's sensor/LDM state;
ConflictEntryMonitor and IntentionPredictor supply the unchanged deployed ONNX
intention interface. `negotiation_execution/replay.py:_pipeline_step` calls local
conflict geometry, occupancy and rules, publishes same-step precedence claims,
assembles connected ego-local graphs and encodes actor observations.
Physical queue heads are limited to one per approach and at most four total.
Followers retain SUMO car-following and the existing ego-owned entry gate.

`TrafficRuleEngine.assess_ldm` assesses spatially conflicting candidate paths.
`RegulatoryPrecedenceGraphBuilder` converts the resulting pair assessment into
directed yield claims. `JointLocalPrecedenceGraphAssembler.assemble` merges
claims; opposing non-voluntary claims produce
`COMMUNICATED_PRECEDENCE_DISAGREEMENT`. `NegotiationEnvironment.classify_status`
prioritizes that disagreement above a graph cycle. `_dynamic_status` consolidates
the local classifications. Inference is allowed only for the two explicitly
negotiable statuses, using the original E5 masked actor and presentation argmax.

Runtime pair commitments go to each DecentralizedEgoExecutionController.
Coordination is incomplete when authority is blocked. Each ego independently
returns SAFE_HOLD, and `constrain` uses native SUMO stopping constraints/speed
mode 31. No centralized graph grants movement. Requested speed limits persist
until permission changes; the runtime contains an explicit native-speed release
(`setSpeed(..., -1.0)`). Release is never reached in the reproduced deadlocks
because valid coordination does not emerge.

### Exact reproduced failure path

The dense case first becomes blocked at **15.76 simulated seconds** with three
in-range heads; the fourth joins at 16.80 s and the same disagreement persists.
Default rolling traffic first completes two rule-resolved vehicles, then the
second wave becomes blocked at **65.24 s**; the fourth head joins at 68.44 s.
These are first blocked-decision timestamps, not assertions that every vehicle
was already stationary at those instants.

The decisive pair is N straight / S right. At the first blocked event the
operational target prediction is **UNKNOWN / NOT_AVAILABLE**, with LEFT,
RIGHT and STRAIGHT candidates. It is not a confident wrong LEFT prediction.
Only the LEFT candidate physically conflicts in each ego's oncoming pair:

| Local source | Own movement | Conflict-conditioned target candidate | Emitted edge | Adopted rule | Zone |
|---|---|---|---|---|---|
| N | STRAIGHT | S LEFT | S yields to N | DE-STVO-9-3 | CZ_022 |
| S | RIGHT | N LEFT | N yields to S | DE-STVO-9-4 | CZ_017 |

Observation ages are zero. The local candidate sets include nonconflicting
alternatives, but rule aggregation receives only the conflicting subset.
Each conditional priority claim is then represented as a mandatory pair edge.
Reconciliation treats the opposing edges as a contradictory mandatory pair
without resolving their incompatible movement premises. The two directions
refer to different hypothetical physical conflicts, not demonstrated mutual
mandatory obligations for the actual straight/right movements.

This is a **conditional-claim representation/reconciliation limitation**.
It is not evidence that the actor failed to choose an action: inference is
correctly prohibited by the current categorical safety contract. There is an
actual directed graph cycle, but its conditional premises do not establish a
legally negotiable mandatory cycle. Treating it as an ordinary voluntary cycle
would silently weaken the contract.

`baseline_analysis.json` retains the exact original local/joint edges, candidate
assessments, conflict zones and regulatory source timestamps. `timeline.jsonl`
retains physical samples, changed ego decisions, delivered endpoint commitments,
sender-owned messages, epochs, reasons, requested speed constraints and actual
SUMO speeds. Sampling is event-driven for decisions and once per simulated
second for physical state; accounting still runs every step.

### Hypotheses checked

Confirmed: conditional conflict premises collapse into incompatible mandatory
claims; categorical disagreement blocks MAPPO; local coordination remains
incomplete; ego controllers consequently hold; SUMO obeys the speed constraints.
The default final state is four active vehicles with speed exactly zero. Its
sampled all-stationary interval starts at 76 s and reaches 15 s at 91 s,
matching the reported recording closely.

Dense final state: 16 active, zero moving, four queued per approach. The sampled
strict all-zero-speed interval does not reach 15 seconds continuously within
this 55-second reproduction (followers can still settle). Individual sustained
stop flags and persistent blocked heads establish the liveness failure; do not
mislabel the simple telemetry stop flag as a formal global deadlock certificate.

Not supported as the primary cause: missing model assets, failed MAPPO loading,
stale source timestamps, missing encoded actors, follower negotiation beyond
four, occupied-zone rejection, collision, invalid route or stuck speed-release
code. Valid rule-resolved and MAPPO-eligible cases actually complete. Authority
invalidation occurs at participant changes; those changes re-enter the same
blocked classification rather than repeatedly destroying a valid moving plan.
Future protocol tests must still cover other possible invalidation defects.

### Historical successes

The retained `results/panel_demo/congested_ego_local_verification/latest_panel_demo.json`
reports 16/16 at 82.76 s using the same E5 hash, deterministic presentation argmax
and the same movement schedule. These agreements do not prove equivalent source
semantics. The retained pre-repair snapshot lacks the current strict admission,
mandatory-removal retention and unordered-pair guards, while the current runtime
opts into V2 rule/reconciliation behavior. Its old ego controller permits an
unordered approaching physical pair where current strict admission refuses it.

The successful presentation record does not itself bind every source file to a
complete matching snapshot. Therefore the exact causal code revision behind
that individual success is not proven here. It is unsafe to restore old behavior
or claim the old success validates the present safety boundary. No historical
record has been altered or replayed into a current frozen study.

## B. Changes made and proposed correction

Added diagnostic utilities only:
`tools/diagnose_live_deadlock.py`, `tools/summarize_live_deadlock.py`,
`tools/verify_deadlock_evidence.py`, this report and new diagnostic artifacts
under `results/live_deadlock_investigation/20261016/`.
No controller, rule, actor, model, scenario, website, existing assertion or
historical evidence changed. Integrity verification confirms all **151 protected
scientific source/model assets and 2,334 historical evidence files unchanged**.

**No liveness fix is implemented or claimed.** Ordinary telemetry defects found
below remain recorded rather than being presented as a traffic correction.

Proposed versioned correction, subject to approval:

1. Preserve candidate movement premises in communicated regulatory claims,
   distinguishing a potential conditional obligation from a confirmed mandatory
   obligation. Do not simply delete opposing edges or call them waivable.
2. Add explicit sender-authored intended-movement declarations to the adopted
   cooperative same-step V2V protocol. Each sender announces its own intention;
   receivers validate sender identity, map/lane compatibility, source epoch,
   freshness and agreement consistency. Do not read another vehicle's simulator
   route centrally or put simulator truth into actor observations.
3. Reconcile each local pair against validated shared premises, then independently
   recompute applicable original rules and physical conflicts. Missing, stale,
   incompatible or untrusted declarations remain unresolved/safe-held. Genuine
   mandatory obligations survive and remain non-waivable. Only existing eligible
   voluntary/unresolved interactions may reach the original masked E5 actors.
4. Keep ego-local final permissions, occupancy shields, admission gates, trained
   action semantics, maximum four actors, deployed models and native SUMO safety.
   Version the new protocol/runtime and store all new diagnostics separately.

This changes what information is admitted as regulatory evidence and introduces
an explicit trust/communication assumption. Existing execution messages already
carry sender-owned path metadata, but silently repurposing that metadata as
authoritative regulatory input would still change the scientific contract.
Hence it needs approval, not a disguised UI or threshold repair. Liveness is
not promised for missing messages, dishonest declarations or genuine mandatory
deadlocks; safe holding remains required. A design that preserves prediction-only
regulatory reasoning would instead require a separately reviewed conditional
claim protocol and may retain these liveness limitations.

Safety/evaluation implications: changed regulatory inputs change actor graphs
and eligibility despite unchanged tensor shapes/weights. All existing results
remain historical evidence of their original implementations. Corrected-runtime
performance requires separately identified reruns before new claims; do not merge
outputs into old manifests or automatically run the 165-episode matrix. No
retraining, checkpoint modification, arbitrary priority or timed release proposed.

Required tests before acceptance: conditional/nonconflicting candidate relations;
true mandatory and voluntary cycles; all rule-resolved cases; contradictory,
missing/stale/wrong-sender/wrong-lane declarations; declaration changes during
admission; every masked action and mandatory-removal rejection; endpoint order
agreement; actual pair clearance; followers; genuine safety-blocked execution;
all eight existing scenarios; dense full discharge; repeated launch/stop/relaunch;
browser/API statuses and failed launch. No expected-failure weakening.

## C. Real verification

Interpreter: `C:\R26-DS-017\venv\Scripts\python.exe`; existing real SUMO and
current frozen E5/ONNX assets. Runs use presentation argmax, not scientific
stochastic sampling. All are explicitly DIAGNOSTIC_NOT_FINAL.

| Scenario | Scheduled / spawned / completed | MAPPO calls | Simulation seconds | Wall seconds | Result |
|---|---|---:|---:|---:|---|
| rule_resolved_two | 2 / 2 / 2 | 0 | 49.48 | 8.34 | Completed |
| congested_four_approach | 16 / 16 / 0 | 0 | 55 | 101.52 | Incomplete, blocked |
| default_panel | 12 / 6 / 2 | 0 | 105 | 59.01 | Incomplete, blocked |
| four_way_simultaneous | 4 / 4 / 0 | 0 | 55 | 26.98 | Incomplete, blocked |
| multiple_left_turns | 3 / 3 / 3 | 2 | 53.60 | 14.52 | Completed with safety fallback |
| mixed_manoeuvres | 4 / 4 / 0 | 0 | 55 | 34.02 | Incomplete, blocked |
| regulatory_cycle | 4 / 4 / 0 | 0 | 55 | 33.75 | Incomplete, blocked |
| yield_negotiation_demo | 6 / 6 / 2 | 0 | 55 | 12.16 | Budget ended while second wave moving |

Every run: zero recorded collisions/blocked-zone violations, unchanged E5 hash,
ego-local execution, zero critic calls/training operations. Dense peak active
and moving counts are both 16; four-current-negotiator maximum is respected.
The dense maximum observed incoming wait is 32.84 s; default 33.36 s. Default
throughput is 1.142857 vehicles/minute for this censored diagnostic; dense zero.
Complete metric sets, waits, safe holds, rule events and timing are in each
`receipt.json` and consolidated `verification.json`.

The multiple-left-turn trace proves actual masked proposer relinquishment and
responder acceptance, followed by independent ego permissions and real arrival
events for all three vehicles. Both epochs require the existing safety fallback;
accepted-direct count is zero. This is not evidence of direct MAPPO robustness.
The yield demo's 55-second horizon does not reach its expected second-wave
interaction; it is neither a demonstrated deadlock nor a PASS.

Commands executed from workspace root (PowerShell):

```powershell
$projectPython = 'C:\R26-DS-017\venv\Scripts\python.exe'
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario rule_resolved_two --duration 65
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario congested_four_approach --duration 55
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario default_panel --duration 105
foreach ($scenarioId in @('four_way_simultaneous','multiple_left_turns','mixed_manoeuvres','regulatory_cycle','yield_negotiation_demo')) {
    & $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario $scenarioId --duration 55
    if ($LASTEXITCODE -ne 0) { break }
}
& $projectPython -B component_2_right_of_way_negotiation/tools/summarize_live_deadlock.py
& $projectPython -B component_2_right_of_way_negotiation/tools/verify_deadlock_evidence.py
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests/test_runtime_v2_safety.py socialmind_drive_showcase/tests/test_final_readiness.py -q -p no:cacheprovider
```

Focused existing tests: **42 passed in 6.34 s**. These include mandatory-rule,
stale/missing coordination, fallback and launch/telemetry guards; passing them
does not validate dense liveness. An initial diagnostic invocation used the
nonexistent scenario ID `simple_rule_resolved` and failed before SUMO started;
its source-hash-only directory is retained. No retry overwrote its evidence.
The summary utility was run once during the batch and again after all runs;
the final summary reflects all eight completed diagnostic receipts.

## D. Website and startup findings

Actual browser-state JSON was produced by each real SUMO reproduction, using
real positions/speeds. Default and dense final JSON contain zero moving vehicles
and INCOMPLETE status. No animation or inference receipt was fabricated.

Confirmed independent display defect: the runtime's regular `browser.publish`
call emits AUTHORIZED when an outcome exists and NOT_REQUIRED otherwise,
including blocked regulatory disagreement. The event log correctly says BLOCKED.
Thus the side panel can falsely say MAPPO NOT REQUIRED. Fixing it requires
consistent categorical mapping: AUTHORIZED for inference, BLOCKED for prohibited
or incomplete inference, NOT_REQUIRED only for supported no-conflict/rule-resolved
states. Keep the existing interface/design. A blocked process can also honestly
be RUNNING; that label describes process lifecycle, not traffic progress. Add
separate measurable liveness/reason telemetry, never a timeout movement grant.

The first-frame message is generated when an existing live-state file predates
the new launch's start timestamp. It is an intentional stale-frame guard.
Every diagnostic run here produced its first real physical frame at 0.04 s and
continued updating. This does not prove every reported intermittent startup is
normal: if waiting persists, inspect the unique owned launch log and FAILED
state. Previous missing-SUMO finalizer masking is documented in readiness reports;
no evidence links it to these successfully started stalls.

No interactive browser was available in the preceding readiness check; this task
does not claim click/visual verification. Real launcher stop/relaunch and HTTP
startup receipts from readiness remain historical only, not rerun here. The
current task stops at the Phase 5 scientific-change gate. Post-correction website,
lifecycle and deliberately safety-blocked end-to-end tests remain required.

## E. Status and launch command

| Area | Status | Basis |
|---|---|---|
| Runtime implementation | PARTIAL | Real executable runs; conditional-claim limitation unresolved |
| Negotiation behavior | PARTIAL | Genuine eligible inference verified; unresolved conditional claims block others |
| Congested demonstration | FAIL | 0/16 completed in bounded reproduction |
| Safety verification | PARTIAL | No observed safety violations; broader guarantees/new protocol untested |
| Website integration | PARTIAL | Real telemetry works; blocked inference mislabeled; interactive/lifecycle checks pending |

Verified existing launch command from the workspace root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/live`. This starts the existing
application; it is **not** a corrected congested demonstration. Until the approved
correction passes real tests, only the specifically verified rule-resolved and
multiple-left-turn cases have completion evidence here. Scientific and cleanup
approval gates remain separate; no cleanup or package rebuild was performed.
