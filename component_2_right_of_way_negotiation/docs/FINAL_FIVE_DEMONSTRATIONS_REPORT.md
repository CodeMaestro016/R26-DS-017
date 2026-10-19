# Final queue correction and five qualitative demonstrations

17 October 2026. Implemented directly in the original Component 2 and shared SOCIALMIND DRIVE application. Evidence: `results/final_demonstrations/v1/`. This is a separately versioned qualitative runtime revision, **not a replacement for frozen scientific evaluation**.

## 1. Actual cause

Non-negotiating followers correctly lacked intersection-entry authority, but also received a persistent TraCI speed request equal to `min(previous native speed, native stop speed)`. After a queue stopped, this repeated request could pin a follower to its preceding low speed even when SUMO permitted acceleration toward its leader.

The first measured incorrect condition was W02 at 31.72 s: follower speed and repeated request **0.01138 m/s**, leader speed **0.56 m/s**, bumper gap **2.59879 m**, stop-line distance **7.51019 m**, and both native follow/stop queries permitting **0.09138 m/s**. The native speed query used by the cap still returned 0.01138 m/s. This is a measured acceleration-feedback restriction, not an inference from website appearance.

## 2. Correction and safety

Version: **`NATIVE_FOLLOWING_PROTECTED_ENTRY_V2`**, exported as `queue_following_protocol`.

For an incoming, strict-admission follower with reason `FOLLOWER_AWAITING_NEGOTIATED_ADMISSION`, the ego controller returns no TraCI speed cap. The existing runner releases an earlier cap with `setSpeed(-1)` when needed. **Its entry permission remains SAFE_HOLD**, and its blocked entry boundary remains recorded.

The unchanged per-ego native stop adapter installs/retains the stop at the incoming lane end minus 0.001 m **before the next simulation step**. SUMO controls following, acceleration and braking up to that stop. Stop installation errors abort the run rather than allowing another step without protection. The stop is released only after explicit current `PERMITTED` entry authority. A promoted head without valid coordination still receives its existing held-head speed constraint. Intrusion across a held boundary remains a hard safety failure.

No time threshold grants permission. Queue-head selection is unchanged: an internal occupant or outgoing vehicle whose rear has not cleared retains its physical head position. No centralized controller, extra policy calls or participant expansion is introduced.

## 3. Identical-demand before/after measurements

Both dense runs used the original 16-vehicle schedule, four vehicles per approach, 1.5-second demand headway, identical vehicle parameters, network, E5 checkpoint, 0.04-second integration step and **360-second budget**. The auditor compares schedule and departure declarations directly.

| Measurement | Before | After |
| --- | ---: | ---: |
| Completed trips | 16/16 | 16/16 |
| Completion time, simulation seconds | 115.36 | 97.92 |
| Available-gap standing, vehicle-seconds | 30.96 | 0.36 |
| Longest available-gap standing interval, seconds | 5.64 | 0.12 |
| Mean waiting time, seconds | 23.4125 | 15.5575 |
| Maximum waiting time, seconds | 52.80 | 35.96 |
| Approach mean-wait gap, seconds | 9.91 | 9.76 |
| Throughput, vehicles/minute | 8.3218 | 9.8039 |
| Genuine MAPPO epochs | 11 | 9 |
| Collisions / blocked-zone violations / unauthorized entries | 0 / 0 / 0 | 0 / 0 / 0 |

Available-gap standing is an **observational diagnostic**: non-head incoming vehicle below 0.1 m/s, leader above 0.5 m/s, actual gap at least measured minGap, not already stopped at its native boundary, and SUMO follow/stop queries allowing at least half of that vehicle's physical acceleration step beyond current speed. It never controls motion. Both files are rescored with this same definition. The initial logger's raw `avoidable_standing_sample` flag used a speed criterion that missed small permitted acceleration increments; the comparison uses the stored native measurements, not that flag.

Samples are 0.12 s apart; **0.12 s residual delay is at sampling resolution**, not a claim of zero reaction time. Intervals ending at promotion/opportunity loss are distinguished from observed motion responses in `verification.json`.

| Approach | Before available-gap standing, vehicle-s | After, vehicle-s | After moving-follower samples | Minimum sampled incoming follower gap, m |
| --- | ---: | ---: | ---: | ---: |
| N | 0.00 | 0.12 | 797 | 2.50117 |
| E | 9.00 | 0.00 | 763 | 2.50100 |
| S | 7.44 | 0.12 | 678 | 2.50100 |
| W | 14.52 | 0.12 | 846 | 2.50134 |

The frozen minGap is 2.5 m. Sampled gaps do not prove continuous geometric safety by themselves; the full-step SUMO collision/entry checks also passed. All 4,136 post-initialization sampled follower decisions in the corrected trace used native advancement without a TraCI cap.

## 4–5. Exactly five final options and fixed movements

The original `scenario_catalog.json` is byte-identical. `final_demonstrations.json` defines the final menu and two additive qualitative definitions. Legacy scientific scenarios remain available through the catalogue/CLI and evaluation/replay paths.

1. **Rule-Based Right-of-Way (2 Vehicles)**: existing north-left/east-left conflict. Rules resolve it; no MAPPO expected.
2. **Four-Vehicle MAPPO Negotiation — Worst-Case Stress**: one simultaneous left turn per N/E/S/W approach. The verified regulatory-cycle starting structure previously negotiated among only three vehicles after one cleared, so this single legal four-left-turn candidate was declared before running. It was not changed after results. “Worst-case” is the requested presentation label for this bounded stress case, **not a proven global worst case**.
3. **Mixed Manoeuvre Coordination (4 Vehicles)**: unchanged north straight, east left, south right, west straight. Genuine heterogeneous physical conflicts; MAPPO conditional on eligibility.
4. **Congested Four-Way Traffic (16 Vehicles)**: original four-wave movement set spanning all 12 legal movements, independent 1.5-second per-approach demand and unchanged geometry/physics.
5. **Coordination Failure Stress Test (6–7 Vehicles)**: **exactly six** vehicles. First wave: N/E straight, S right, W left at 0 s; second N-left and E-right at 1.5 s. Same frozen demand for protected and rules-only modes.

`verification.json` lists each movement and its actual geometry-derived conflict-zone pairs. No collision geometry or mandatory rule was modified.

## 6–7. Actual results and MAPPO attribution

All primary runs scheduled and spawned the stated number, completed every trip, and had **zero collisions, blocked-zone violations and observed unauthorized entries**, maximum participants ≤4 and zero centralized critic runtime calls.

| Final scenario | Completed / scheduled | E5 epochs | Simulated completion, s | Mean / max wait, s | Approach gap, s | Throughput, veh/min | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1. Rule-based | 2/2 | 0 | 50.64 | 0.20 / 0.40 | N/A | 2.3697 | PASS |
| 2. Four-agent stress | 4/4 | 3 | 59.80 | 5.70 / 12.04 | 12.04 | 4.0134 | PASS |
| 3. Mixed manoeuvres | 4/4 | 0 | 58.96 | 3.83 / 8.72 | 8.72 | 4.0706 | PASS |
| 4. Dense traffic | 16/16 | 9 | 97.92 | 15.56 / 35.96 | 9.76 | 9.8039 | PASS |
| 5. Protected six-vehicle stress | 6/6 | 1 | 64.36 | 5.03 / 12.16 | 11.24 | 5.5935 | PASS |

Scenario 2 had real E5 actor factors with valid masks at 15.76, 16.84 and 25.32 s. **The 16.84 s event included E01, N01, S01 and W01 together.** Participant identities, selected mask indices and resulting runtime events are retained. The unchanged safety layer corrected all three outcomes through the existing decentralized fallback; **directly accepted uncorrected MAPPO outcomes = 0**. Dense traffic similarly used nine real MAPPO epochs with safety fallback. This demonstrates the integrated protected system, not learned-policy superiority or autonomous acceptance of every proposed action.

The dense trace independently records leader IDs/positions, follower position and speed, measured bumper gap, stopping-line distance, native follow/stop speeds, speed mode, prior applied restriction, denied/permitted entry, physical promotions, conflict entry times and trip completion times. Thus 16/16 completion is not the sole queue-following acceptance criterion.

## 8–9. Honest failure comparison and limitations

Scenario 5 B uses the **existing `RulesOnlyProvider`**, with the new runtime revision and identical demand, integration step and 220-second budget. It is an additional qualitative no-negotiation comparison, **not an overwrite or rerun of the frozen official baseline**. Both methods retain native safety, traffic rules, entry stops and the shield.

| Mode | Spawned | Completed | E5 calls | Collisions / zone violations / unauthorized entries | Mean / max wait, s | Throughput, veh/min | Outcome |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Protected | 6 | 6 | 1 | 0 / 0 / 0 | 5.03 / 12.16 | 5.5935 | Complete at 64.36 s |
| Rules-only/no-negotiation | 6 | 1 | 0 | 0 / 0 / 0 | 162.95 / 197.80 | 0.2727 | INCOMPLETE at 220 s; five held; safe degradation |

The incomplete baseline has **no fabricated total completion time**. Waiting values include unfinished vehicles' observed/censored waits. Throughput divides completions by each run's actual elapsed simulation time, so the completed protected run ends naturally before the common budget. Safe-hold activations are separately recorded; ordinary safe holds are not automatically classified as failure events.

The optional unsafe uncoordinated simulation/replay is **not implemented or deployed**. No collision occurred or is animated. The educational counterfactual removes negotiation using the existing rules-only provider while retaining safety, showing safe loss of progression rather than inventing a collision.

The unchanged `deadlock_observed` flag remains true for dense traffic because individual stopped incoming waits can exceed 15 seconds despite eventual completion. It is also true in the unfinished baseline. This flag alone is not a proof of global permanent gridlock. The four-agent label is not a universal worst-case claim, and the measurements are deterministic qualitative regression observations, not a statistically generalizable performance study.

## 10. Preserved research artifacts

The final audit verifies **2,334 historical files unchanged**, the original scenario catalogue unchanged and all four versioned execution source identities against their preserved snapshots. The E5 checkpoint remains `2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`; existing tensor-equality tests pass. Intention-model weights, mandatory rules, native stop adapter, fallback ordering, queue-head selection, physics, network and collision geometry are unchanged. Prior source identities/results remain preserved; the new controller/runner revision has its own identity and source snapshots. No training, seven-load scalability study or old 165-episode suite is run.

## 11. Tests and actual browser checks

The integrated existing runtime, strict dense/safety, source-integrity and website regression set passed **230 tests in 180.03 s**. It includes two focused additions: native following retains a denied entry and installed stop; a promoted uncoordinated head retains its speed constraint. The final website-only checks passed **101 tests in 2.79 s** after preserving the comparison panel's client-local expanded state and fitting the recorded comparison text within the existing sidebar.

The initial diagnostic attempt failed at 0.16 s because the new logger could not serialize a mapping proxy. It is preserved under `before/`; the corrected `before_v1/` is the complete baseline. This is a logger failure, not a scientific passing run.

**Browser functional checks: PASS. Full-session automatic shutdown: PARTIAL.** Local Chromium 156.0.8078.4 performed all five real live launches and verified exact menu options/order, actual body fills and computed card border colors, matching IDs/timestamps, genuine Scenario 2 MAPPO outlines, stop/idle clearance and fresh run identities. `browser_v4/receipt.json` contains **494 DOM samples**, all five case records, zero page errors and zero remaining owned processes after cleanup. Actual screenshots were inspected. Browser checks stop cases around 20 simulation seconds; the separate full SUMO runs above establish scientific completion and safety.

After five launches in one session, automatic Windows CTRL+BREAK shutdown timed out; the log contains Python Proactor connection-reset errors, and the harness forcibly cleaned up its owned server. This remains an unresolved environment/lifecycle limitation, not a passing shutdown test. No scientific behavior was changed to hide it. Earlier failed attempts (`browser_v1/`, `browser_v2/`) are retained; the second attempt also exposed a cleanup race in the diagnostic harness, which was fixed.

The final isolated Scenario 5 browser check (`browser_v5/receipt.json`) **passed**, with **90 DOM samples**, a readable, persistent comparison panel, protected launch, stop/idle clearance, clean server shutdown, zero page errors and no owned process leftovers. It includes the final display formatting; it does not erase or supersede the failed full-session shutdown result. No native desktop-window close or successful multi-run automatic shutdown is claimed.

## 12. Changed implementation

- `negotiation_execution/ego_controller.py`: remove only the redundant non-negotiating incoming-follower TraCI cap; entry remains held.
- `runtime_simulation/runner.py`: export the new queue-following version; existing command-release/control ordering remains intact.
- `runtime_simulation/scenarios.py` and new `final_demonstrations.json`: additive scenario loading and fixed five-option presentation metadata.
- Shared `services/scenario_reader.py` and `pages/component2_live_view.py`: exact five-item menu, counts, purpose/expected MAPPO/mode, protected-only launch, recorded rules-only comparison, persistent client-local expansion state. Existing colors/layout/theme are retained.
- Focused tests, diagnostic/browser tools and this separate evidence/report family. No unrelated component or repository-root cleanup.

## 13. Start and present

From the original repository root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8098
```

Open `http://127.0.0.1:8098/component/right-of-way/live`. Select scenarios 1 through 5 and click **Run Scenario**. Every launch uses the protected primary method. **Stop** is available while a process runs; it is correctly disabled after completion. A new launch resets prior current vehicles/highlights; historical events remain available.

For 2, observe real timestamped MAPPO outlines and the four-participant event. For 4, observe followers moving within their lanes while entry remains held, successive physical heads and later crossings. For 5, expand **Recorded comparison** and scroll the sidebar as needed to inspect measured protected completion versus the safely held unfinished baseline. That panel does not launch an unsafe mode or replay fabricated movement.
