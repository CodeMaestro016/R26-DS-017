# Scenario 5 failure in the existing main canvas

## Changed presentation flow

The earlier implementation used a separate dialog and an additional replay action. Although its evidence was authentic, that flow did not meet the requested normal Run Scenario behavior. Scenario 5 now uses the same center canvas, left-side Run/Stop controls and right-side vehicle panel as the other scenarios. There is no modal, new page, embedded second canvas or additional replay viewer in this flow.

Exactly five options remain. Run Scenario dispatches Scenario 5 to a client-owned recorded-data clock. Scenarios 1–4 dispatch to the original guarded live SUMO launcher. **Protected six-vehicle comparison** explicitly launches the original protected Scenario 5 on the same canvas. The former separate replay module is no longer invoked by this page.

The normal Stop button clears the replay and its impact frame. Run or **Restart replay** starts again from the first authentic six-vehicle sample. Switching scenarios clears local playback state. At impact, the clock automatically pauses and retains the collision frame, marker and vehicle cards. Closing the page disconnects its UI timers; replay never starts a SUMO process.

## Recorded trajectories and vehicle panel

`services/main_canvas_replay.py` reads the original checksum-verified v1 trace. A monotonic presentation clock selects the latest recorded sample at or before the corresponding recorded timestamp. No positions are interpolated or assigned to a simulator. The 0.15-second existing page refresh can skip some 0.12-second samples under load, but never synthesizes motion; the final collision-bearing frame is retained.

Playback begins at the first six-vehicle frame, **1.60 s**. The real schedule has four vehicles at 0 s and two at 1.5 s, so six vehicles cannot truthfully be shown at time zero. The unchanged common renderer uses original front positions, angles, body lengths and widths. A uniformly scaled camera fits the recorded approaches and tightens as traffic reaches the junction; vehicle-to-road proportions remain physical. No separate overview or detail canvas is created.

The main-canvas metadata and the existing vehicle cards use the same frame. During replay, the inspector's live polling cannot overwrite it with protected telemetry. Cards show recorded IDs, legal movements, actual speeds, sample time and **MAPPO: DISABLED**. At impact, **COLLISION INVOLVED** cards are highlighted and placed first for visibility. This is display ordering only; scientific counts and source data remain unchanged. Normal live polling resumes for protected execution.

The page header identifies recorded SUMO evidence during replay. The prominent label is **OFFLINE UNCOORDINATED FAILURE — REPLAY OF REAL SUMO DATA**. It does not describe playback as a currently running SUMO experiment or a trained MAPPO failure.

## Actual collision and central location

The original recording remains sufficient: 203 saved frames, six vehicles and one genuine SUMO collision. Native event time **24.24 s**, collision-bearing step-ending snapshot **24.28 s**, IDs **PANEL_AV_N_02 / PANEL_AV_W_01**. No saved snapshot exists at exactly 24.24 s; the viewer distinguishes these clocks rather than inventing a frame.

Collision reference: **(299.878893839, 301.801843602) m**. The network declares the true junction center at **(300, 300) m**, giving distance **1.805908931 m**. The reference and the entire measured **0.114382928 m²** body overlap lie inside the actual junction polygon. The thin marker annotates this real reference; both genuine vehicle bodies are outlined without changing their positions or dimensions. No new unsafe experiment or demand variant was necessary.

At impact the center shows **ACTUAL SUMO COLLISION DETECTED**, native count, actual IDs and both timestamps above the canvas. No post-impact dynamics are generated. The original recorded bodies are still present, so no fallback to earlier positions is needed.

## Protected isolation and comparison

| Mode | Completed | Collisions | Observation end | Meaning |
| --- | ---: | ---: | ---: | --- |
| Protected six-vehicle method | 6/6 | 0 | 64.36 s | Original executed paired result |
| Rules-only, safety retained | 1/6 | 0 | 220 s | Preserved safe-deadlock baseline |
| Recorded uncoordinated failure | 0/6 before cutoff | 1 | 24.28 s | First-collision cutoff |

The counterfactual omits MAPPO, regulatory execution, entry authority, shield, explicit entry stops and specified native safe-following/junction-priority enforcement in its original isolated experiment. Physical dimensions, acceleration/braking parameters, speed-limit enforcement and safe insertion were retained. These omissions do not enter the protected launcher. No unsafe runtime option has been introduced.

This combined intervention does not show that disabling MAPPO alone causes collisions or that the protected method guarantees universal collision freedom. The full paired protected result above was verified in the previous task. This task additionally tested that its explicit secondary action starts genuine protected execution, then stopped that rehearsal; it does not claim another full six-vehicle completion from that abbreviated check.

## Executed browser and regression verification

Local headed Chromium exercised the ordinary Scenario 5 Run action without expanding comparisons. It verified one existing canvas, one page/tab, no visible dialog, six real vehicles, timestamp progression, collision hold, two marked cards, Stop, restart and clean return after scenario changes. Actual desktop **1600×1000** and laptop **1280×720** screenshots were opened and visually inspected. The bodies, reference marker, event text and collision cards are visible in the existing layout. Sidebar scroll position survived refreshes.

The full live rehearsal then ran:

| Protected scenario | Spawned / completed | Completion time | MAPPO epochs | Collisions | Blocked-zone violations |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scenario 2 | 4/4 | 59.80 s | 3 | 0 | 0 |
| Scenario 4 | 16/16 | 97.92 s | 9 | 0 | 0 |

Both made zero centralized critic calls. Scenarios 1 and 3 retain their original execution path and definitions; they were checked by routing/runtime regressions, not rerun to completion in this task.

`results/offline_counterfactual/main_canvas_v1/receipt.json` records the full browser PASS and real Scenario 2/4 terminal metrics. After the visibility adjustment, `main_canvas_v2/receipt.json` records a presentation-only PASS with zero page errors; it explicitly marks those two full scientific runs as not repeated. The final regression set passed **168 tests in 4.76 s**, covering website, runtime, native junction hold, mandatory fallback, default dispatch, immutable replay positions, impact hold and restart.

The old launch-source test was updated to inspect the extracted protected launch function; its existing live-process guard assertion remains. No controller or model was altered to satisfy tests.

Final integrity receipt: `main_canvas_v2/verification.json`. It verifies **2,334 historical files**, all four approved protected controller identities, unchanged E5 checkpoint, unchanged raw replay, and the actual browser/scientific receipts. Earlier evidence is preserved.

Verified screenshots:

- [Six recorded vehicles in the main canvas](../results/offline_counterfactual/main_canvas_v2/six_recorded_vehicles.png)
- [Before impact](../results/offline_counterfactual/main_canvas_v2/before_impact.png)
- [Main-canvas collision, desktop](../results/offline_counterfactual/main_canvas_v2/main_canvas_collision_desktop.png)
- [Main-canvas collision, laptop](../results/offline_counterfactual/main_canvas_v2/main_canvas_collision_laptop.png)
- [Protected secondary comparison](../results/offline_counterfactual/main_canvas_v2/protected_secondary.png)
- [Scenario 2 live](../results/offline_counterfactual/main_canvas_v1/scenario2_running.png)
- [Scenario 4 live](../results/offline_counterfactual/main_canvas_v1/scenario4_running.png)

## Startup and presentation

From the repository root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8100
```

Open **http://127.0.0.1:8100/component/right-of-way/live** using this updated server rather than an older imported page process. Select Scenario 5 and click the ordinary **Run Scenario**. Watch the actual vehicles converge and the replay pause at impact. Use Stop to clear, Run/Restart replay to repeat, or Protected six-vehicle comparison for the original safe live method. Scenarios 1–4 still use Run Scenario for their original protected live execution.

The camera initially shows physically small distant vehicles because the real approaches are long. As they converge, uniform framing makes the junction and physical bodies larger. No fabricated crash response or new collision experiment is included. Playback is educational recorded evidence and does not contribute to scientific trip totals or overwrite frozen evaluation results.
