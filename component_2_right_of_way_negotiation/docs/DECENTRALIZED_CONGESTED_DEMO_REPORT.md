# Ego-local execution and congested four-approach presentation

Evidence classification: **QUALITATIVE_PRESENTATION_ONLY**.

## Initial audit

`runtime_simulation/runner.py` previously stored one `slots[approach]` vehicle and
required every slot to be empty before admitting the next wave. A slot was
released only on arrival at the end of its route, preventing visible followers
on the same approach. `ConflictZoneExecutionPlanner.plan()` received the
complete effective graph and generated global READY/BLOCKED permissions for
`PhysicalBranchReplayRunner._apply_control()`.

The new dense schedule submits independent demand rather than waiting for
route completion. Physical queue-head selection is separate from the number
of live vehicles. Runtime physical permissions now come from individual ego
controllers; the graph remains negotiation/audit evidence.

## Scope and information boundary

The new execution mode is used by **all `run_runtime_simulation.py` scenarios**, including
the congested scenario and showcase launches. Historical training, selected
research-demo episodes, and frozen physical evidence-replay paths retain their
original behavior for reproducibility. The original held-out and selection
artifacts are not recomputed or overwritten.

Each controller instance is owned by one ego. Its context has no complete
effective graph, global READY/BLOCKED list, critic output, or other actor's
private observation. It accepts only ego state/path, pair commitments touching
that ego, fresh sender-owned physical-state/path announcements, and local
coordination completion/freshness. State announcements use the existing
ideal same-step V2V communication assumption; packet-loss/latency realism is
not claimed. Simulator route truth is excluded from transmitted state and the
execution channel never feeds actor observations.

Each ego projects its own and relevant communicated peer state onto static
conflict-zone geometry. An unresolved outgoing obligation holds that ego before
the relevant zone; priority clearance releases it. Occupancy admission holds
an approaching ego at junction entry. Already entered zones continue clearing:
a newly appearing occupancy restriction is not activated mid-crossing.
Entering a previously blocked zone or junction boundary is a hard failure,
including when a required clearance message disappears. Missing/stale
coordination or clearance triggers safe hold. SUMO stopping-speed feasibility
and speed mode **31** remain active.

The process transports pair commitments and applies returned ego speed
requests. READY/BLOCKED aggregation is display/audit only. Neither a global
permission plan nor a centralized execution planner is invoked by the panel
control path. The historical replay pipeline gained an optional eligible-ID
filter; its default behavior is preserved. Full sensor/LDM histories still
observe traffic, while filtered reasoning views keep followers out of actor
graphs.

## Congested demand

- 16 scheduled vehicles: four per N/E/S/W approach.
- 1.5-second demand headways; actual SUMO departures recorded independently.
- All twelve existing legal left/straight/right movement paths represented.
- At most one physical queue head per incoming lane; its rear must clear the
  junction before a follower is promoted.
- Negotiation events and encoded actor graphs bounded to four participants.
- Followers use native SUMO car-following and receive no unnecessary speed
  overrides. The frozen shared E5 role-specific actors serve successive heads.
- 360-second simulation budget; early finish on complete discharge.

No 16-participant MAPPO validation claim is made.

## Measured headless run

The saved run is `results/runtime_simulation/congested_ego_local_verification/latest_runtime_simulation.json`.
It uses the predeclared presentation schedule, not validation/held-out demand.

| Measurement | Observed value |
|---|---:|
| Scheduled / actually spawned / completed | 16 / 16 / 16 |
| Completion time | 82.76 simulation seconds |
| Maximum simultaneous active traffic | 16 |
| Maximum simultaneous moving traffic | 16 |
| Maximum incoming depth N / E / S / W | 4 / 4 / 4 / 4 |
| Approaches with multiple queued vehicles simultaneously | 4 |
| Maximum negotiation participants | 4 |
| Coordination events / authorized MAPPO epochs | 11 / 6 |
| Rule-resolved events | 5 |
| Missing-context safe-hold activations | 1 |
| Collisions / blocked-zone entry violations | 0 / 0 |
| Centralized critic runtime calls | 0 |
| Decentralized execution | true |
| Global execution graph used for control | false |
| Training / backward / optimizer / parameter-update operations | 0 / 0 / 0 / 0 |
| Held-out scenarios consumed | 0 |
| Unfinished / pending insertion vehicles | 0 / 0 |

Actual insertion delays were 0.04–0.06 simulation seconds, including the
simulation-step boundary. Vehicles were neither manually repositioned nor
overlapped. SUMO emitted a native emergency-braking warning for N01 at 26.92 s.
This is retained as a safety intervention, not reported as a learned action or
hidden by the collision-free result. SUMO's separate emergency-stopping event
API reported zero events; that metric does not count every braking warning.

Checkpoint SHA-256 **before and after**:

```text
2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57
```

## Verification

- Baseline Component 2 suite: **655 passed**.
- Final Component 2 suite: **673 passed**.
- Final showcase suite: **71 passed**.
- Real SUMO integration guards reject global planner `plan()` calls,
  centralized critic forward calls, `Tensor.backward`, autograd backward,
  and Adam optimizer steps. No guarded operation occurred.
- GNN/proposer/responder state dictionaries are compared before/after the
  real congested run; all remain unchanged and execute in evaluation mode.
- Every encoded actor graph is asserted to have at most four nodes.
- Unit tests cover ego-only context/decisions, ownership, safe stopping,
  priority permission, fresh clearance, stale/missing coordination, lost-message
  blocked-entry detection, physical head selection/promotion, dense demand,
  follower native control, and >4 live vehicles with <=4 heads.
- Actual showcase server smoke check: home and Component 2 live view returned
  HTTP 200; live-state API exposed measured counts and decentralized execution.
  The temporary verification server was stopped afterward.

## Changed and created source/documentation files

Paths in the first table are relative to `component_2_right_of_way_negotiation/`.

| File | Change and purpose |
|---|---|
| `negotiation_execution/ego_controller.py` | New immutable ego contexts, pair commitments/state messages, ego-owned permissions and native speed constraints. |
| `negotiation_execution/__init__.py` | Export the new ego-execution API. |
| `negotiation_execution/replay.py` | Optional queue-head-only reasoning views; preserve full perception and the historical default pipeline. |
| `runtime_simulation/queue_heads.py` | New physical frontline selection and incoming depth accounting. |
| `runtime_simulation/schedule.py` | Scheduled demand times and explicit support for repeated legal movements in dense demand. |
| `runtime_simulation/scenarios.py` | Scenario admission mode, headway, and recommended duration. |
| `runtime_simulation/scenario_catalog.json` | Predeclare the 16-vehicle congested schedule without hard-coded outcomes. |
| `runtime_simulation/runner.py` | Independent admission, bounded queue-head actors, pair delivery, ego execution, real departure/traffic metrics, failure/incomplete reporting, policy hashing. |
| `runtime_simulation/browser_state.py` | Clear current participants/permissions on complete discharge while retaining event history. |
| `runtime_simulation/reporting.py` | Persist expanded traffic/execution metrics in qualitative summaries. |
| `runtime_simulation/visualization.py` | Wider SUMO camera only for independent dense traffic. |
| `run_runtime_simulation.py` | Scenario-specific duration/admission mode and separate output-directory option. |
| `tests/test_ego_execution_and_dense_traffic.py` | New unit and guarded real-SUMO acceptance tests. |
| `tests/test_runtime_simulation.py` | Update existing architecture assertions for local execution; retain legacy runtime safety checks. |
| `README.md` | Correct root-relative path and document the new scenario, execution scope, and commands. |
| `docs/DECENTRALIZED_CONGESTED_DEMO_REPORT.md` | This audit, measured report, file inventory, and run instructions. |

Paths below are relative to the repository root.

| File | Change and purpose |
|---|---|
| `socialmind_drive_showcase/pages/component2_live_view.py` | Add congested picker entry, requested metrics/execution label, and enough camera extent to see followers. |
| `socialmind_drive_showcase/tests/test_showcase.py` | Preserve picker/default-page regression assertions while including the new scenario. |
| `socialmind_drive_showcase/README.md` | Correct actual web-live launch command and document congested UI fields. |

## Generated presentation-only artifacts

No original model-selection, held-out, or trained-model files are outputs.
The final verification directory contains:

- `latest_runtime_simulation.json`: full measured qualitative result.
- `latest_runtime_simulation_summary.md`: metric summary.
- `presentation_runs/latest_presentation_run.json`: latest qualitative history.
- `presentation_runs/run_20261005T161504_498435Z.json`: first saved verification summary.
- `presentation_runs/run_20261005T162245_486707Z.json`: final tested-code verification summary.

Additional generated files:

- `results/congested_ego_local_verification.log`: saved final stdout.
- `results/runtime_simulation/runtime/live_state.json`: normal showcase display snapshot.
- `results/congested_development_run.log`: development-run output.
- `results/runtime_simulation/decentralized_congested_check/latest_runtime_simulation.json`.
- `results/runtime_simulation/decentralized_congested_check/latest_runtime_simulation_summary.md`.
- `results/runtime_simulation/decentralized_congested_check/presentation_runs/latest_presentation_run.json`.
- `results/runtime_simulation/decentralized_congested_check/presentation_runs/run_20261005T155920_021037Z.json`.

Pytest also updates its normal cache and writes isolated temporary test results.
Development-run metrics are not substituted for the final verification result.

## Exact commands on this machine

The available interpreter is the existing `C:\R26-DS-017\venv\Scripts\python.exe`.

Congested SUMO GUI:

```powershell
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_runtime_simulation.py --scenario congested_four_approach --gui --gui-delay-ms 10
```

Standalone headless web-live simulation (publishes showcase state):

```powershell
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
& "C:\R26-DS-017\venv\Scripts\python.exe" -B run_runtime_simulation.py --scenario congested_four_approach --web-live --presentation-delay-ms 10
```

Showcase:

```powershell
cd "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& "C:\R26-DS-017\venv\Scripts\python.exe" -B socialmind_drive_showcase\app.py
```

Open Component 2's live view, select **Congested Four-Approach Queues**, and
press **Run Scenario**. Do not start an additional standalone simulation at the
same time. To use a browser, append `--server-only` to the showcase command,
then open `http://127.0.0.1:8088`.
