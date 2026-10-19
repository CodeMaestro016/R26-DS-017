# Final SOCIALMIND DRIVE live correction

16–17 October 2026 (evidence partition retains its 16 October start date). New execution protocols:
`MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1` and
`NATIVE_EXPLICIT_JUNCTION_HOLD_V1`.

The unchanged deterministic dense scenario now completes **16/16 actual trips
in 115.36 simulated seconds**, within its original 360-second budget. The
70-second diagnostic cut completes **7/16**, rather than the earlier 5/16.
All fifteen final scenario/fault diagnostics record zero collisions,
blocked-zone violations and independently observed unauthorized junction entries.
These are finite, deterministic presentation diagnostics, not a new frozen
research evaluation or a universal safety/progress guarantee.

See [the measured tables](FINAL_LIVE_CORRECTION_RESULTS.md) and
`results/final_live_correction/20261016/verification.json` for complete metrics,
per-event actions, crossings, transitions, fault outcomes and integrity checks.

## 1. Color and timestamp correction

The earlier overlay incorrectly turned recently involved vehicles yellow even
after inference had completed, masking actual red/green permission. The prior
task removed that overlay. This task found an additional synchronization issue:
the NiceGUI road refreshed at 150 ms while vehicle cards independently fetched
the API at 350 ms. They could show different simulator frames.

Each SVG now carries the exact run ID, simulator timestamp and vehicle/card
state used to render it. The API returns SVG and state from one publisher
snapshot. The card updater consumes that SVG's embedded frame, including when
NiceGUI replaces the road. A cached frame prevents a mutation feedback loop.
Navigation cancels polling and pending requests. Stale API frames clear the
road/cards rather than continuing to present active permissions.

Local Chromium additionally reproduced an idle-state defect: the API could
repaint a previous run while the page said IDLE. The page and API now share an
explicit empty idle presentation frame, with no old actor event or vehicle data.
The browser also measured 16 px of overflow from a `100vw` root inside NiceGUI's
padded content. It now uses its actual content width, and the existing camera
controls remain in normal flow so they do not cover status text. Columns,
geometry, controls and colors were retained; the website was not redesigned.

The existing palette, geometry, layout and theme are retained:

| Body | Meaning |
|---|---|
| Blue | Approaching without a current final entry decision |
| Yellow | Actual negotiation pending, if published and observable |
| Green | Current entry permission or an existing valid admission lock |
| Red | Current protected entry hold; motion toward the boundary remains legal |

Strict admission can hold a vehicle immediately after spawn; distance alone
does not justify recoloring it blue. No artificial blue or yellow phases were
inserted into these runs. Red and green transitions were measured against
actual ego decisions; the full dense run contains 20 observed held-to-ready
transitions. A moving red vehicle is explicitly labeled as approaching its stop.

## 2. Why yellow is not reliably visible

Inference is synchronous. The normal runtime publishes its completed decision
after inference and local execution reasoning; it does not emit a separate
pending vehicle frame. Adding a genuine inference-start event would not require
changing actor semantics, but it would not ensure that a browser refresh catches
the short interval. We did not add a delay or pretend that a completed event was
still pending.

Actual factor start/completion wall-clock timestamps, exact actor input snapshots,
masks and selected actions are recorded in
`results/vehicle_state_consistency/20261016/http_synchronized_v1/regulatory_cycle/actor_inputs_and_actions.jsonl`.
The existing bounded acknowledgment remains clearly labeled **RECENT MAPPO
DECISION**, now with its actual simulator timestamp. Vehicle receipts separately
show local execution, safety fallback, execution held or decision expired.
The final card explicitly separates direct MAPPO outcomes from fallback epochs.
Completed-event acknowledgments reset immediately when the run or scenario changes.

## 3. Two causes of the remaining dense failure

The first cause was the documented mixed cycle:

```text
E02 yields to W03   mandatory turning obligation
W03 yields to N02   previous pair fallback
N02 yields to S02   mandatory turning obligation
S02 yields to E02   previous pair fallback
```

Independent pair ordering could contradict the mandatory partial order. The new
fallback resolves this algorithmic cycle, but the fallback-only real run still
completed only 6/16 over 360 seconds. N02 had local permission yet remained
physically stopped by native SUMO junction logic.

The second cause was an execution integration mismatch. The controller's speed
cap held a vehicle at the boundary but did not withdraw its native approach
request. Native right-before-left logic could therefore continue waiting for a
vehicle that the negotiated execution layer was holding. A separate planned-stop
experiment completed 16/16; the integrated production correction independently
reproduced that completion.

This interpretation is supported by the retained fallback-only and planned-stop
experiments and native-junction traces. SUMO's
[1.26 link implementation](https://github.com/eclipse-sumo/sumo/blob/v1_26_0/src/microsim/MSLink.cpp)
also distinguishes approaching requests that will pass from those that will not.
No native junction-priority safety bit was disabled.

## 4. Authorized mandatory-aware fallback

`negotiation_execution/mandatory_fallback.py` implements a legal extension of
retained constraints independently inside each ego controller. It receives no
global permission list, critic output, other actor observations or hidden routes.

The ideal authenticated same-step transport carries each endpoint's own
incident accepted commitments, mandatory obligations, epoch, fresh physical
message, queue-arrival metadata and real MAPPO receipt. Both endpoints must
attest each constraint. Every affected ego must receive the complete matching
transcript for at most four participants. This extends the existing ideal V2V
assumption; it is not cryptographic authentication or Byzantine robustness.

Each ego checks freshness, membership, duplicate senders, receipt and epoch
agreement, physical-message consistency, paired constraint evidence and fallback
eligibility. It also retains its existing physical oncoming turning shield.
The ego derives a deterministic order respecting all mandatory and non-waived
constraints. Arrival/ID ordering only resolves the remaining incomparable choices.
Only the already eligible waived/unordered pairs use that supplementary order.

A cycle in retained constraints, missing receipt, stale/missing endpoint evidence,
or unsafe physical clearance causes SAFE_HOLD. Waiting time never grants entry.
The runtime transports messages, not a precomputed order or shared ready list.
Each ego independently generates its own permission and native stopping request.

## 5. Native stop/release correction

`negotiation_execution/native_hold.py` exposes an ego's held junction entry to
SUMO as a planned local stop. The stop is placed 1 mm outside the entry, a fixed
numerical boundary offset declared before the planned-stop experiment. Existing speed constraints remain active.
The stop is removed only after that same ego has valid current permission.
No stop is inserted into an already entered junction.

The administrative stop duration is much longer than the demonstration budgets;
expiry does not create permission, and independent speed constraints remain in
force. There is no waiting-time release. Failure to install a stop fails the run
rather than weakening the safety mode or forcing movement.

The full dense run records 20 actual local stop installations and 20 releases
after permission. SUMO retains acceleration, braking, car-following, occupancy
and native right-of-way checks. Vehicle dimensions, scenario demand, map,
speed mode 31 and the existing admission/clearance lock are unchanged.

## 6. Real MAPPO contribution

Four-way simultaneous remains rule-resolved: **4/4 completed, zero MAPPO calls**.
Regulatory cycle completes 4/4 with one genuine invocation; multiple left turns
completes 3/3 with three; rolling traffic completes 12/12 with one.

Dense traffic produces **11 genuine E5 invocations**. Each recorded event has
actual local graph/regulatory observations, factor identities, feasible masks,
policy probabilities, selected actions, accepted responses and effective graph.
The audit links each dense event to one actual authorized junction crossing
under its source epoch and separately records participants' actual completions.

The policy relinquishes represented claims, and responders accept the waivers.
That changes accepted coordination evidence and enables the supplementary
execution path. The safety layer then preserves mandatory obligations and uses
fallback ordering where required. All eleven dense events are classified
`MAPPO_WITH_SAFETY_FALLBACK`: **zero direct outcomes accepted without shield
correction, eleven fallback epochs**. This is genuine learned negotiation with
safety fallback, not proof that E5 alone solved dense discharge.

The policy, observation dimensions, action meanings, model parameters and
deterministic masked-argmax presentation rule were not changed or retrained.

## 7. Before and after, with the same demand and budgets

| Dense budget | Completion before → after | Mean wait s | Max wait s | Approach gap s | Throughput/min |
|---|---|---|---|---|---|
| 70 s | 5/16 → 7/16 | 29.953 → 21.197 | 45.600 → 42.440 | 8.250 → 5.630 | 4.286 → 6.000 |
| 360 s | 5/16 → 16/16 | 229.327 → 23.413 | 335.600 → 52.800 | 80.750 → 9.910 | 0.833 → 8.322 |

The audit verifies identical presentation schedules, scheduled departures,
simulation step and maximum duration in each comparison. The 360-second budget
run ends naturally when all vehicles complete at 115.36 seconds. Throughput uses
the existing actual episode duration. Incomplete-run waits are observed and
censored, not completed-trip estimates. These single deterministic runs do not
establish a statistically significant performance improvement.

Full dense run: 16 scheduled, 16 spawned, maximum 16 simultaneously active,
16 completed, zero unfinished. Per-approach mean waits: N 18.59 s, E 22.99 s,
S 28.50 s, W 23.57 s. The fairness measure is the existing maximum-minus-minimum
approach mean, 9.91 s; it is not a Jain fairness index.

The existing `deadlock_observed` flag remains **true** because it triggers when
any individual incoming vehicle waits for 15 seconds. That can occur in a fully
completed episode. It was not redefined to produce PASS. The final run has no
unresolved persistent dependency cycle and no observed interval where all active
vehicles are stationary at the sampled publisher resolution. Individual waiting
alarms and complete intersection gridlock are different measurements.

## 8. Faults, mandatory constraints and safety

Missing, stale, invalid, incorrectly authored and contradictory movement
declarations each preserve entry holds, produce zero MAPPO calls and complete
0/4 within the 45-second negative-test horizon. These failures were not removed
from evidence or reported as successful discharge.

The stale-commitment case and the synthetic mandatory-constraint-cycle case each
complete one already admitted trip while the remaining three are held. Existing
clearance permission is not revoked inside the junction. Both retain zero unsafe
entries/collisions/blocked-zone violations.

A genuine retained mandatory or non-waived cycle is tested by the local ordering
regressions and fails closed. The real-SUMO negative injection supplies a
contradictory mandatory transcript and verifies that no new order forces release.
It is explicitly synthetic. Under this project's adopted oncoming turning
obligations, precedence descends from left to right/straight and right to straight;
we did not invent an invalid route family and call it a genuine legal cycle.
The regulatory-cycle scenario tests the distinct, legally negotiable cycle.

Physical occupied-zone holds and mandatory holds remain in the genuine scenarios;
the dense audit includes 196 sampled mandatory-hold vehicle frames. Safety tests
retain the hard blocked-entry failure and fresh-communication requirements.

## 9. NiceGUI lifecycle correction

The installed NiceGUI is 3.16.0. Its lifecycle dispatcher passes `App` to a
handler exposing one parameter. Registering `LAUNCHER.shutdown(grace_seconds=5)`
therefore supplied an App where a number was expected. `app.py` now registers a
zero-argument wrapper and explicitly supplies numeric `grace_seconds=5.0`.

Shared module refreshables could revisit another client's stale targets. The
new `services/client_lifecycle.py` captures the initiating client before NiceGUI
defers its refresh response, restores that client context when executing, filters
targets by owner, and refuses refresh for disconnected/deleted clients.
Page timers deactivate on disconnect, reactivate on reconnect and cancel on
deletion using a zero-argument lifecycle wrapper. Page preferences are client
local. The simulator remains a deliberately shared single-instance launcher.

The installed-framework client harness verifies two independent clients, six
navigation steps, automatic deletion, reconnect/close/reopen, actual SUMO
stop/relaunch and real lifespan shutdown with the registered callback. Its final
receipt contains no lifecycle errors and confirms the process closed. It also
asserts that live refresh targets do not accumulate and new clients reset their
own preferences.

A separately owned real server returned six HTTP routes successfully. A Windows
isolated **Ctrl+Break console event** triggered shutdown with no deleted-client
warning, shutdown TypeError or unhandled traceback. All tracked owned process
identities exited. This tests safe console interruption; it is not a literal
keyboard Ctrl+C browser rehearsal. No unrelated application was terminated.

Earlier harness failures, including deferred-context and callback-signature
failures found during implementation, remain in their separate logs. Final
passing receipts are `client_lifecycle_v10/receipt.json`,
`server_shutdown_v2/receipt.json` and
`server_shutdown_synchronized_v1/receipt.json` under the new evidence root.

## 10. Synchronized checks and tests

The final synchronized server check matches **105 frames** across independently
recorded actual SUMO position/speed and ego decision, published backend state,
real HTTP API and server-rendered SVG/card data. Timestamps, IDs, permissions,
colors and genuine MAPPO event metadata agree. It records actual E5 actor inputs
and actions at 23.24 seconds. SVG is XML-validated, including corrected escaping.

Executed checks:

- 122 integrated focused tests: website, legal fallback, native stop ownership,
  declaration reconciliation, display and existing execution safety.
- 51 strict discharge/integrity tests, including a fresh real 16-vehicle run
  with forbidden critic, backward, optimizer and centralized-planner calls and
  exact actor-state checks. The original complete-discharge assertions remain;
  the two recovered expected-failure markers were removed after observing 16/16.
- 100 final complete showcase regressions, including same-frame API/SVG moving-red,
  permission/event timestamp validation, cross-run acknowledgment reset and an
  idle API that cannot read a previous runtime; see `local_browser_final_website_tests.log`.
- Fourteen predeclared production scenario/fault diagnostics, plus the separate
  synthetic mandatory-cycle negative, synchronized HTTP and client/server
  lifecycle checks. Interim failed/partial experiments remain separately labeled.

The in-app Browser connection was unavailable. Following the user's explicit
local-testing instruction, Playwright and Chromium were installed in an isolated
temporary environment; the research environment and requirements were unchanged.
Actual local headless Chromium 156.0.8078.4 verified **186 DOM frames**, including
**124 matching HTTP/DOM frames**, correct rendered car fills/card borders/current
permissions and four held-to-ready transitions. E01 becomes green at 23.24 s
with a real current MAPPO receipt and valid permission. The browser records
2,176 moving-red vehicle samples without equating red with stationary.

Two real browser contexts kept separate scenario preferences. Actual clicks
launched SUMO, navigated away/back, reloaded, closed/reopened a tab, stopped and
relaunched with a new run ID, then closed both clients. Console interruption
while the second runtime was active left no tracked owned process. There were
zero page errors, failed requests or deleted-client/shutdown tracebacks.
`local_browser_v4/receipt.json`, `dom_frames.json`, `idle.png` and
`live_negotiation.png` retain the evidence. Screenshots were visually inspected.
The failed overflow/idle attempts remain in `local_browser_v1` through `v3`.
The obsolete layout assertion was corrected to the browser-proven content width;
no scientific assertion or algorithm was changed for this browser continuation.

## 11. Scientific integrity and fresh evaluation

E5 SHA256 remains
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
All **2,334** inventoried historical evidence files retain their original hashes.
The **147** unchanged protected source/model files include the original training,
intention, rule, map, inference and physical parameter assets. The four inventory
differences are the earlier approved browser/runner/replay/controller revisions;
this task adds separately versioned fallback and stop adapters.

Original execution source and relevant test versions are retained under the new evidence root.
`approved_source_identity.json` freezes the four new execution source identities;
naming equivalence still checks the original naming-period sources and verifies
both approved scientific implementations separately. Historical assertions were
not weakened to compare the new algorithm with an old naming-only algorithm.

Because control behavior changed, old quantitative results remain measurements
of the earlier protocol. Claims about the corrected protocol require a separately
versioned, newly approved evaluation matrix: prior panel validation, operational
scalability boundaries, safety/communication negatives and final comparative
evaluation. No frozen table was substituted, no manifest was re-frozen, no model
was trained, and neither the old 165-episode suite nor the seven-load scalability
study was run by this task.

## 12. Scope and changed files

Production: `negotiation_execution/{mandatory_fallback,native_hold,ego_controller}.py`,
`runtime_simulation/runner.py`, and the existing showcase `app.py`,
`services/client_lifecycle.py`, `pages/{component2_live_view,component2_inspector,
component2_results,component_detail}.py`, plus the two scoped live-view CSS rules
in `ui/theme.py`.

Diagnostics/tests/reports stay inside the existing Component 2 and showcase
structures. The source identity guard and original strict discharge tests were
updated as described above. No unrelated research component, root probe folder,
project copy, ZIP archive or repository-cleanup action was introduced.

## 13. Acceptance and remaining limits

| Acceptance | Measured result |
|---|---|
| A: colors and synchronized presentation | PASS for measured simulator/API/SVG and real Chromium DOM/color agreement; no fabricated pending phases |
| B: four-way scenario | PASS: 4/4, rules resolved, no forced MAPPO, zero observed safety failures |
| C: genuine MAPPO | PASS for learned actions/accepted waivers with safety fallback; no direct-policy-success claim |
| D: original dense scenario | PASS: 16/16 in full budget, 7/16 at 70 s, no observed safety failures |
| E: website lifecycle | PASS for actual two-client Chromium navigation/reconnect and owned-server shutdown; safe isolated Ctrl+Break was used rather than typing literal Ctrl+C |

The local browser rehearsal is complete. Genuine pending yellow is not stretched
or fabricated, and no artificial blue approach phase is inserted when strict
admission already holds entry. The native desktop window and literal keyboard
Ctrl+C were not separately rehearsed. Performance and safety robustness beyond
these deterministic diagnostics require fresh scientific evaluation.

## 14. Run the corrected website

From `C:\Users\Iresha Nethmini\Documents\R26-DS-017`:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/live`. Stop and restart an
already running old showcase process so it loads the corrected code. If that
process must remain open, add `--port 8098` and use the corresponding URL.

Use Four-Way Arrival to demonstrate rules without unnecessary inference;
Regulatory Cycle for real negotiation; and Congested Four-Approach Queues for
the original 16-vehicle progressive discharge. Native desktop mode remains
available by omitting `--server-only`. Use the existing configured Python/SUMO
environment; this task did not require dependency upgrades.
