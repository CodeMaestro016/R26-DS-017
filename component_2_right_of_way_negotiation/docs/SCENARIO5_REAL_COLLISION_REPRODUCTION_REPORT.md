# Scenario 5: real SUMO collision reproduction and presentation

## Confirmed causes and implementation

The normal Scenario 5 Run button intentionally launches only the protected method. Selecting Scenario 5 does not launch an unsafe experiment. Its protected vehicles have entry stops, regulatory decisions, ego-local safety and native SUMO avoidance. The preserved rules-only baseline removes MAPPO but retains safety: it deadlocks safely rather than colliding. Its absence of collisions is an authentic result.

Repository inspection also confirmed that a separate counterfactual had already executed successfully in `results/offline_counterfactual/v1/`. Its XML recorded a real collision, and its trace reached the website through the read-only counterfactual API and comparison dialog. Thus missing collision opportunities or missing collision logging were not the current cause. The event was accessible through a separate replay rather than the normal Run button. This separation remains intentional.

The current revision adds the exact requested warning and native collision outcome label, Restart, timestamp-based 0.5×/1×/2× playback and Back to protected scenario. Navigation to the event derives its frame index from actual collision-bearing frames, including disabling that control when none exists. No collision time is hardcoded into the player. Recorded timestamps must strictly increase. The original vehicle colors and protected launch command remain unchanged. Browser rendering and fetch latency may slow wall-clock playback; samples and their ordering are never synthesized or skipped to invent motion.

## Three-mode results

All modes use `final_coordination_failure`: the same six IDs, legal routes, frozen schedule, road geometry, vehicle type, initial departure-speed policy, seed 42 and 0.04 s integration step. The observation budget is 220 s, with early termination on completion or first collision; these unequal observed durations must not be treated as equal exposure.

| Mode | MAPPO / regulatory coordination / protection | Completed | Actual collisions | Deadlock observed | Mean wait (s) | Throughput (vehicles/min) | Observed end (s) |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| A. Protected proposed system | Enabled / enabled / retained | 6/6 | 0 | No | 5.0333 | 5.5935 | 64.36, complete |
| B. Preserved rules-only safe baseline | Disabled / enabled / retained | 1/6 | 0 | Yes; safe holds | 162.9533 | 0.2727 | 220, incomplete |
| C. Isolated offline counterfactual | Disabled / disabled / specified avoidance removed | 0/6 | **1** | No before cutoff | 0 before cutoff | 0 before cutoff | 24.28, first detection |

A made one genuine MAPPO negotiation call; its accepted execution used safety fallback. This is not evidence of direct learned-policy acceptance. B is preserved executed evidence, not a new rerun or collision experiment. A fresh A rerun reproduced the earlier complete metrics, schedule, actual departures, simulation completion time and checkpoint hash exactly; wall time was 47.50 s. C's zero completions are measured only until the first collision, not a full-horizon failure rate.

## Isolated simulation and retained physical constraints

`offline_counterfactual/run.py` owns a separate SUMO process and labeled TraCI connection. It does not import the protected runner or offer an unsafe option through the website launcher. The frozen protocol remains `ISOLATED_UNCOORDINATED_COUNTERFACTUAL_V1`; this revision adds only a new, exclusive output-folder option for reproducibility. Existing runs cannot be overwritten.

Speed mode 38 removes native safe-follow-speed and junction-priority enforcement while retaining acceleration, deceleration and speed-limit checks. No MAPPO, regulatory execution, entry authority, shield or explicit junction stops are installed. Desired speed is bounded by the real lane and vehicle limits. Original dimensions 5 × 1.8 m, acceleration 2 m/s², comfortable deceleration 4.5 m/s², emergency deceleration 7 m/s², type minGap 2.5 m and maximum speed 13.89 m/s remain unchanged. Safe SUMO insertion remains active. Retaining braking parameters does not mean autonomous collision-prevention braking remains active under this speed command and mode.

Only the isolated process enables junction collision detection with `collision.mingap-factor=0`, so events require body overlap rather than a minGap infringement. `collision.action=warn` records without removal; teleporting is disabled. The runner stops on first detection. Neither post-impact trajectories nor rigid-body crash response are claimed.

## Fixed demand and physical conflict evidence

The first four vehicles are N-straight, E-straight, S-right and W-left, scheduled at 0 s. N-left and E-right follow at 1.5 s. Actual SUMO departures are 0.04 s and 1.56 s respectively, identical across the protected and isolated traces. No alternate movement combination, schedule tuning or high-conflict variant was needed.

The new `v2_reproduction/reproduction_audit.json` evaluates oriented physical body distances for **all 15 vehicle pairs** at common recorded samples. It retains routes, speeds, positions, closest sampled separation and any sampled overlap. This is measured trajectory analysis through the first collision, not a prediction of unobserved future conflicts or a new statutory priority oracle. Legal route definitions come from the unchanged network/route assets. Concurrent conflicting occupancy requires right-of-way resolution; the unsafe experiment deliberately provides none. The A/B executions remain the evidence of actual rule/safety intervention.

The detected pair is **PANEL_AV_N_02**, legal north-to-east left turn, and **PANEL_AV_W_01**, legal west-to-north left turn. Both occupy the central turning conflict region. Their speeds in the detection snapshot are **10.954368 and 8.999868 m/s**. The collision reference point is **(299.878894, 301.801844) m**, derived by SUMO from `:center_2_0` at longitudinal position 5.693641 m. This reference is not claimed to be the exact rigid-body contact point.

| Recorded snapshot (s) | Body separation (m) | Body overlap (m²) | Native collision reports in snapshot |
| ---: | ---: | ---: | ---: |
| 23.68 | 9.7861 | 0 | 0 |
| 23.80 | 7.7441 | 0 | 0 |
| 23.92 | 5.7200 | 0 | 0 |
| 24.04 | 3.5553 | 0 | 0 |
| 24.16 | 1.6302 | 0 | 0 |
| 24.28 | 0 | **0.114383** | **1** |

SUMO XML timestamps the move-stage event **24.24 s**; TraCI exposes it in the step-ending snapshot **24.28 s**. Both clocks are explicitly labeled in the viewer. These data establish actual body overlap plus an independent simulator event, not merely close drawn markers, an emergency stop or a predicted geometric conflict. No post-event evidence exists because of the declared first-collision termination.

## Executed verification and evidence

- A new genuine SUMO run is retained separately in `results/offline_counterfactual/v2_reproduction/`. All 203 recorded frames, native event contents, actual departures and outcomes exactly reproduce v1. Native XML and simulator logs are stored separately from replay JSON.
- A fresh protected six-vehicle run is in `results/final_demonstrations/v1/timestamp_replay_protected_v2/`: 6/6, zero collisions, zero unauthorized entries. Its complete runtime metrics match the earlier protected run.
- **165 tests passed** across website, runtime, mandatory fallback and native junction-hold tests. Tests verify XML/hash agreement, physical overlap, read-only launcher separation, original A/B results, strict frame ordering and event navigation from actual recorded data.
- `tools/audit_counterfactual_reproduction.py` verifies the identical reproduction, protected metrics, four approved controller source identities, selected E5 checkpoint hash and **2,334 historical files**. It writes only the new reproduction audit; earlier verification receipts are preserved.
- Actual local Chromium verifies the new warnings, collision marker/IDs/time, Play/Pause, Restart, speed selection and measured slower playback. Desktop/laptop sidebar wheel, native scrollbar dragging, focus, live updates, independent right scrolling and Run/Stop are exercised. `browser_timestamp_v9` passed these checks with zero page errors and no remaining owned processes. The earlier v8 test-script failure reading a temporarily absent telemetry node is preserved; its wait was corrected without changing production telemetry.

The final expanded rehearsal **`results/offline_counterfactual/v1/browser_timestamp_v10/receipt.json` passed** all the above plus starting Scenario 1 after closing the replay, observing its real live vehicles, stopping it and reloading. No offline player remained visible in the normal scenario. It recorded zero page errors and zero remaining owned processes. At 0.5×, 0.72 recorded seconds advanced over 1.71 wall seconds including browser/fetch overhead. The actual collision screenshot was visually inspected; its marker is on authentic recorded vehicle positions. The warning is at the top of the scrollable dialog.

## Presentation and reproduction commands

From the repository root, start the existing application (use an unused port):

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8099
```

Open `http://127.0.0.1:8099/component/right-of-way/live`. Select Scenario 5. **Run Scenario** runs A safely. Expand **Recorded comparison** to see B and select **View offline unsafe counterfactual** for C. Play or Restart, choose speed, then **Jump to recorded event**. **Back to protected scenario** closes only the viewer. Other normal scenarios retain the protected execution path.

To reproduce C again, choose a fresh evidence name; the viewer continues reading the original verified v1 evidence:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B component_2_right_of_way_negotiation/offline_counterfactual/run.py --confirm-offline-unsafe --evidence-version reproduction_03
```

This educational case removes coordination **and** specified low-level avoidance together. It does not establish that removing MAPPO alone causes collisions, that collisions are inevitable without rules, or that the protected method is universally collision-free. No model, scientific controller, protected rule, original demand or historical result was changed.
