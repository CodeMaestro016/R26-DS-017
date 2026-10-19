# Live vehicle presentation correction — 17 October 2026

This change applies directly to the original working Component 2 and SOCIALMIND DRIVE folders. It changes presentation data and rendering, not the research algorithm. Verification artifacts are under `results/presentation_lifecycle/20261017/`; no scientific evaluation table or archive is replaced.

## 1. Causes

The publisher assigned red from blocked-set membership before considering approach geometry. That set includes future admission obligations and queue followers, so it overstated active entry holds. The viewer already tracked recent completed MAPPO events, but the SVG renderer never drew that attribute. Finally, current cards followed SUMO's active-trip list; a vehicle could remain listed long after leaving the intersection.

## 2. Implementation

`runtime_simulation/intersection_presentation.py` supplies a read-only presentation lifecycle. `browser_state.py` applies it to the shared `vehicles` collection. The complete active scientific collection remains available separately as `scientific_vehicles`, with `active_sumo_vehicles` and unchanged runtime metrics. The SVG and cards use the same exported display collection and synchronized frame metadata. Current selection is local to each browser and is discarded when its vehicle disappears or the run changes.

The main application still launches the original runtime and selected E5 checkpoint. No alternate project or presentation copy is used.

## 3. Color contract

| Body/card color | Meaning |
| --- | --- |
| Blue | Ordinary approach, including a future yielding or admission obligation. |
| Red | Actual controller hold after reaching the movement's entry-control stage; braking is allowed. |
| Green | Current real controller permission. |
| Yellow | Actual pending negotiation, only if such a state is genuinely published. |

The incoming boundary is the actual SUMO incoming-lane end for each legal movement. The entry-control envelope uses the vehicle's measured speed and comfortable deceleration, the existing SUMO Euler brake-gap calculation, one simulation step of travel and the vehicle's own length. The stage latches for that vehicle/run as braking reduces speed. Internal/outgoing lanes identify crossing and clearance geometrically. Unknown geometry never removes a vehicle. Display classification never writes permission, speed, policy input or simulation state.

## 4. Genuine MAPPO acknowledgment

Inference is synchronous: the existing publisher runs after inference completes, so the browser cannot observe its pending interval without introducing runtime instrumentation or another publication phase. This task does not fabricate a pending state or invoke extra inference.

Actual completed events instead receive a yellow outline and the card label **“MAPPO decision received”**, with the genuine simulation timestamp. Only recorded participants receive it. Bodies retain their current permission color. The acknowledgment expires after 1.75 monotonic wall-clock seconds; repeated reads of the same event do not extend it. Run/scenario identity resets the overlay. History remains available without renewing commitments.

## 5. Clearance definition

A vehicle must be on a network-derived outgoing lane with front-bumper lane position greater than its full length, so its rear has cleared the internal junction. Its entire body must then leave the fixed overview footprint: the network junction center and radius, expanded to cover the largest supported dense overview at minimum zoom (`radius × 3.2 × 1.5 / 0.55`). Width is included conservatively. The footprint contains the internal movement/conflict area and does not change with camera zoom or scenario selection.

Crossing vehicles remain visible even if outside a camera crop. Exited IDs remain suppressed until the next run, preventing flicker or reappearance.

## 6. Display removal versus trip completion

Filtering occurs only in the display publisher. It never removes a SUMO vehicle, changes its route, deletes historical data or increments completed trips. `intersection_cleared_vehicle_ids` identifies display exits; SUMO completion and global active counts remain separate. Both the road and current cards consume the filtered `vehicles` collection. An empty panel reads **“No vehicles currently in the intersection area.”**

Shutdown preserves run identity even though the existing final publisher call omits it. Terminal atomic-file replacement also retries transient Windows reader locks for at most 180 ms; normal hot-frame publication does not wait.

## 7. Automated verification

**180 focused tests passed in 34.18 s**, plus **20 strict scientific/dense tests in 130.71 s** (200 checks across the two runs). Counts and receipts are recorded in the evidence directory. Focused tests cover all 12 legal movements, future holds, near-entry holds, permission preservation, pending/completed negotiation distinction, acknowledgment expiry, rear clearance, display exits before trip completion, retained history, run resets and terminal publication. Existing scientific regressions separately forbid critic execution, training, parameter updates and centralized control.

## 8. Real simulator verification

The instrumented original 16-vehicle dense scenario completed **16/16 at 115.36 simulation seconds**, with **11 MAPPO decision epochs**, **0 collisions**, **0 blocked-zone violations**, **0 observed unauthorized entries**, at most **4 participants**, and **0 critic runtime calls**. Across **721 published frames**, permission/color mismatches and body-color overrides were both **0**. Instrumented wall time was **272.68 s** while other checks ran concurrently. The E5 hash remains `2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

Mean waiting time remains 23.4125 s, maximum waiting time 52.8 s, approach waiting gap 9.91 s and throughput 8.321775 vehicles/minute, matching the previous corrected run. These are regression comparisons, not new statistical evaluation claims.

The existing `deadlock_observed` telemetry remains true because it flags individual incoming waits of 15 seconds. It is not rewritten as a global-gridlock detector; all 16 trips complete.

## 9. Browser verification

Local Playwright/Chromium runs the real main application and SUMO backend, comparing actual SVG fills, computed card borders, vehicle IDs, permissions and timestamps against HTTP telemetry. The rehearsal covers the full dense scenario, four-way simultaneous rule-resolved case, a genuinely eligible regulatory cycle, selection disposal, two independent tabs, navigation, reload, stop/relaunch and owned-process shutdown. Screenshots and complete DOM receipts are retained. Earlier failed attempts are retained separately, including the terminal identity and Windows final-frame publication failures corrected during this task.

The full scenario checks recorded **1,501 DOM frames**, including **841 matching HTTP/DOM frames**, with no browser page errors and no remaining owned processes. Vehicle bodies and actual computed card border colors matched throughout.

| Real browser scenario | Trips completed | Real MAPPO epochs | Completed-event outline | Display exit before SUMO trip completion |
| --- | --- | --- | --- | --- |
| Original dense queues | 16/16 | 11 | Observed | Observed |
| Four-way simultaneous | 4/4 | 0 | None, as required | Observed |
| Regulatory cycle | 4/4 | 1 | Observed on actual participants | Observed |

All three had zero collisions and blocked-zone violations. The original `browser_v4/receipt.json` is retained with its continuation failure: after all scenario assertions passed, the old harness tried to click the correctly disabled Stop button on a finished run. Stop/relaunch and owned-process shutdown are checked separately on an active run in `browser_lifecycle_v1/receipt.json`. `verification.json` audits both records without rewriting the failed receipt or disguising it as a complete passing harness run. Screenshots alone do not establish a passing rehearsal.

The separate active-run lifecycle rehearsal **passed**, recording **208 DOM frames** and **137 matching HTTP/DOM frames**. It verified independent two-tab preferences, navigation, reload, tab close/reopen, stop/relaunch and shutdown with a live runtime. Page errors and remaining owned processes were both zero. All **2,334 historical files** and the four approved scientific runtime source files passed the final hash audit.

## 10. Limits and launch

No observable live inference-pending interval is claimed. The supported acknowledgment is an actual completed-event outline. This is local headless Chromium verification, not a new native-desktop-window close test. No training, seven-load scalability study or 165-episode evaluation suite is run.

From the original repository root in PowerShell:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8098
```

Open `http://127.0.0.1:8098/component/right-of-way/live`. An already running application must be restarted to load the corrected Python renderer and publisher.
