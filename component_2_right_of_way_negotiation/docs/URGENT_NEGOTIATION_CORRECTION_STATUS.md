# Urgent negotiation correction: implemented telemetry fixes and unresolved research gate

16 October 2026. **The traffic deadlock is not fixed.** Verified software fixes
now expose its real inference status and sustained blockage. A safe liveness
correction requires the scientific approval described below; no hidden release,
checkpoint change or rule override has been introduced.

## Actual root cause and first incorrect representation

The prior investigation reproduced eight real existing scenarios, including
16/16 spawned but 0/16 completed in congested traffic, and 2/12 completed in
default rolling traffic before four active vehicles stopped. Its full architecture,
traces and commands are in `LIVE_DEADLOCK_ROOT_CAUSE_AND_CORRECTION_PROPOSAL.md`.
Those baseline source identities were checked against the retained original VIVA
package before the display-only edits; the baseline remains applicable.

The first blocked dense decision is at 15.76 s; rolling traffic blocks at
65.24 s. The earlier representation problem is in the path from
`TrafficRuleEngine.assess_ldm/_aggregate` to
`RegulatoryPrecedenceGraphBuilder.build/_edge_record`: rules assess only the
spatially conflicting candidate subset and emit unconditional mandatory edges.
With UNKNOWN target intentions, N straight considers a hypothetical S left and
claims S must yield under adopted DE-STVO-9-3. S right considers hypothetical
N left and claims N must yield under DE-STVO-9-4. Both local candidate sets also
contain nonconflicting alternatives. These opposing claims refer to different
conditional movement premises and different conflict zones (CZ_022/CZ_017).

The joint assembler identifies reciprocal mandatory edges, and classification
returns COMMUNICATED_PRECEDENCE_DISAGREEMENT before checking negotiable cycle
eligibility. This is not a confirmed mandatory deadlock for the actual straight/
right movements. Nor is it safe to classify those represented mandatory claims
as voluntary waivers merely to invoke MAPPO. Coordination stays incomplete,
each ego independently holds, and genuine SUMO obeys the stopping limits.
The missing step is validated reconciliation of the conditional rule premises.

The deployed predictor/checkpoint loads; MAPPO genuinely runs in the eligible
multiple-left-turn case. No evidence warrants retraining or modifying weights.

## Implemented software corrections

Only these production files changed:

- `runtime_simulation/browser_state.py`: `displayed_mappo_invocation` describes
  actual existing eligibility. Without an outcome, only NO_ACTIVE_CONFLICT and
  REGULATORY_ORDER_RESOLVED yield NOT_REQUIRED; unresolved/prohibited inference
  yields BLOCKED. A real outcome remains AUTHORIZED.
- `runtime_simulation/runner.py`: the regular browser publish call uses that
  display mapping instead of labeling every missing outcome NOT_REQUIRED.
  An AST comparison against the verified baseline confirms the rest of the
  control loop is unchanged after excluding that import/display argument.
- `runtime_simulation/browser_state.py`: display-only TrafficProgressTelemetry
  tracks all current heads being blocked and below the existing 0.5 m/s stopped
  threshold, with unchanged participants/status/dependencies. After the existing
  15-second duration it reports PERSISTENT_BLOCKAGE and the underlying reason.
  Moving followers do not hide stopped heads. Progress, missing heads or changed
  dependencies reset this clock. It is an observed blockage indicator, not a
  legal deadlock proof, and never feeds control or authorizes release.
- `socialmind_drive_showcase/pages/component2_live_view.py`: the existing banner
  shows persistent blockage duration/reason and categorical MAPPO BLOCKED. No
  page structure, CSS, theme or navigation changed.

New focused regressions are in `tests/test_live_deadlock_telemetry.py`. Existing
tests/assertions are unchanged. New diagnostics and helpers remain inside
Component 2; no root probes, cleanup or presentation builds were created.

Exact before/after production sources are retained under
`results/live_deadlock_investigation/20261016/telemetry_sources/`.
`telemetry_verification.json` identifies DISPLAY_TELEMETRY_CORRECTION_V1, verifies
all 2,334 historical files unchanged and 149/151 protected assets unchanged.
The two changed protected paths are precisely the telemetry publisher and its
runtime publish call. All models, rules, geometry, controllers and inference
semantics remain unchanged. E5 SHA-256 remains
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

## Real execution after correction

Four separate diagnostic comparisons were run with original demand/scenarios,
current weights, real SUMO and unchanged decentralized control. All selected
traffic metrics match their baseline exactly; telemetry changes do not improve
traffic discharge.

| Scenario | Scheduled/spawned/completed | MAPPO | Maximum wait (s) | Throughput (vehicles/min) | Wall (s) |
|---|---|---:|---:|---:|---:|
| rule_resolved_two | 2/2/2 | 0 | 0 | 2.425222 | 8.79 |
| multiple_left_turns | 3/3/3 | 2 | 6.12 | 3.358209 | 14.11 |
| congested_four_approach | 16/16/0 | 0 | 32.84 | 0 | 106.76 |
| default_panel | 12/6/2 | 0 | 33.36 | 1.142857 | 62.15 |

All four: zero observed collisions and blocked-zone violations, unchanged E5,
zero centralized critic calls, zero training. Dense completion: **0%**; peak
active 16; maximum four current negotiators. No valid MAPPO commitment exists
in dense traffic because inference is blocked. In multiple-left-turn traffic,
the real actor generates masked relinquishment/acceptance actions in two epochs;
both use existing safety fallback, not direct accepted-MAPPO execution. Ego
decisions and SUMO arrival records verify actual 3/3 completion at 53.60 s.

Dense final telemetry now reports BLOCKED and PERSISTENT_BLOCKAGE with 31.36 s
of stationary blocked heads and reason COMMUNICATED_PRECEDENCE_DISAGREEMENT,
instead of misleading NOT_REQUIRED. The final simulation remains INCOMPLETE.
Rolling traffic likewise correctly reports persistent blockage.

The other four existing scenario baselines remain preserved separately. They
were not rerun after a display-only fix. No full scientific matrix was executed;
formal corrected-methodology results would require separate versioned evaluation.

## Website and regression checks

Final focused runtime/safety/showcase tests: **174 passed in 9.26 seconds**.
Saved log: `telemetry_final_tests.log` under the investigation evidence root.
New tests cover blocked-vs-not-required semantics, actual outcome receipt,
duration boundary, moving followers, dependency changes and missing heads.

Real lifecycle check on one ComponentLauncher instance: rule-resolved launch,
duplicate launch refusal, first real frame, cooperative stop, then dense relaunch
with a different run ID, correct fresh scenario frame and another cooperative
stop. Both processes exited; neither stop was forced. Receipt:
`showcase_checks/launch_stop_relaunch.json`. All six HTTP routes returned 200,
including live view, evaluation and live-state API; server cleanup completed.
Real browser-state positions/speeds are generated from SUMO. No interactive
browser clicks or screenshot verification are claimed.

The first-frame waiting message remains an intentional launch-timestamp freshness
guard. Both lifecycle launches delivered real frames. This does not rule out
unrelated intermittent failures; launch logs and FAILED state remain the proper
diagnostics, not forced acceptance of an older frame.

Commands executed from workspace root:

```powershell
$projectPython = 'C:\R26-DS-017\venv\Scripts\python.exe'
foreach ($scenarioId in @('rule_resolved_two','multiple_left_turns','congested_four_approach','default_panel')) {
    $durationSeconds = if ($scenarioId -eq 'default_panel') { 105 } else { 55 }
    & $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario $scenarioId --duration $durationSeconds --version telemetry_v1
    if ($LASTEXITCODE -ne 0) { break }
}
& $projectPython -B component_2_right_of_way_negotiation/tools/probe_deadlock_showcase.py
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests/test_live_deadlock_telemetry.py component_2_right_of_way_negotiation/tests/test_runtime_simulation.py component_2_right_of_way_negotiation/tests/test_runtime_v2_safety.py socialmind_drive_showcase/tests -q -p no:cacheprovider
& $projectPython -B component_2_right_of_way_negotiation/tools/verify_telemetry_correction.py
```

The integrity helper's initial assertion failed because inventory paths use
Windows backslashes; the helper was corrected to normalize comparison keys.
Its original failure log is preserved, and `telemetry_integrity_final.log`
records the successful verification. No scientific file was changed to pass it.

## Remaining blocker and concrete approval request

The safe liveness remedy proposed in the diagnosis requires a new versioned
conditional-claim reconciliation protocol. Preserve candidate premises; use
explicit sender-authored own-movement declarations with validated source,
freshness, map/lane compatibility and epoch consistency; independently rederive
the original obligations at each endpoint. Missing/conflicting declarations must
still safe-hold. Mandatory rules stay non-waivable; genuinely negotiable relations
use original E5 masks/actions and ego-local safety checks. No central route-truth
lookup, random winner, timeout release or hidden scripted policy is proposed.

Adding trusted movement information to regulatory reasoning changes the adopted
communication/information assumptions, even though execution metadata already
contains sender-owned paths. It is not authorized merely by the requirement to
preserve existing interfaces. The urgent task explicitly says: if safe correction
requires methodology changes, explain the blocker and request approval first.

**Approval needed:** implement and test that versioned cooperative reconciliation
protocol under the constraints above, including missing/stale/contradictory
message safety tests, genuine mandatory cases, all eight real scenarios,
full dense discharge verification and website lifecycle checks. This does not
authorize retraining, checkpoint changes, weakening safety, changing historical
results or automatically running the final evaluation matrix. Success is not
guaranteed before those tests; genuine residual deadlocks must remain reported.

Current status: runtime PARTIAL; negotiation PARTIAL; dense demonstration FAIL;
safety verification PARTIAL (no observed violations, no broad guarantee);
website integration PARTIAL (telemetry/lifecycle/HTTP verified, interactive
visual checks unavailable). The corrected congested demonstration is **not ready**.

To start the existing application from the workspace root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/live`. The rule-resolved and
multiple-left-turn cases have verified completion evidence. Dense/default stalls
are now exposed accurately; this command does not claim a repaired traffic policy.
The previously verified presentation ZIP remains untouched and does not include
these new telemetry corrections. No package rebuild has been performed.
