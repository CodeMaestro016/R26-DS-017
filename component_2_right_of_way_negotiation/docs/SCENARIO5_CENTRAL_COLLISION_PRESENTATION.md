# Scenario 5: directly accessible central collision demonstration

## Why it was difficult to see

The existing collision was genuine. The normal Run Scenario action correctly launched the protected method, while the unsafe recording was behind the Recorded comparison expansion. The old dialog placed long evidence text above its animation. Its compact camera also excluded distant initial arrivals, although those vehicles existed in the recording. These were presentation and discoverability problems, not missing collision evidence.

The coordinate transform was verified: SUMO front-bumper positions are converted to geometric body centers using recorded orientation and length, then mapped with one uniform scale and inverted Y. Bodies retain their true 5 × 1.8 m dimensions. The native event was already present in the last sample, and vehicles had not disappeared. No coordinate offset, collision relocation or fabricated frame was needed.

## Location verified against the original SUMO network

The true junction is `junction[@id='center']` in `networks/intersection.net.xml`, with declared center **(300.000000, 300.000000) m**. Its polygon, rather than the drawing's apparent center, defines the central junction area.

The existing collision reference is **(299.878893839, 301.801843602) m**, **1.805908931 m from that center**. It lies inside the actual junction polygon. The two oriented vehicle footprints have **0.114382928 m²** of physical overlap, and that entire overlap also lies inside the junction polygon. This satisfies the central-junction requirement; **no new demand or counterfactual run was necessary**.

SUMO's native XML records **24.24 s**, collider **PANEL_AV_N_02**, victim **PANEL_AV_W_01**, legal left turns `N_IN_0_LEFT` and `W_IN_0_LEFT`. Speeds are approximately 10.954368 and 8.999868 m/s. XML independently records vehicle fronts/backs and the junction collision. The collision reference is not claimed to be a rigid-body contact point.

There is no saved trajectory snapshot at exactly 24.24 s. The preceding saved snapshot is **24.16 s**, with 1.630242 m body separation, and the collision-bearing step-ending snapshot is **24.28 s**. The viewer explicitly distinguishes the native move-stage event time from its snapshot time. It never interpolates a nonexistent 24.24 s frame or invents post-impact motion.

## Website corrections

Selecting Scenario 5 now exposes **PLAY PROTECTED SYSTEM** and **PLAY UNCOORDINATED COLLISION REPLAY**, outside the comparison expansion. Run Scenario still launches the original protected method. The rules-only comparison remains secondary.

The replay opens and plays in one action. It starts at **frame 13, 1.60 s**, the first recorded sample containing all six vehicles; earlier spawn samples remain accessible with the slider. The original demand schedules four vehicles at 0 s and two followers at 1.5 s, so six simultaneous bodies cannot truthfully be displayed at time zero.

Two synchronized cameras show the same actual sample: a fixed full-approach overview and a fixed enlarged central-junction detail. Both use the existing road and vehicle renderer. Dashed paths are the recorded front-bumper trajectories through the recorded cutoff, not predicted routes. The overview keeps distant arrivals visible; the central detail makes the colliding bodies clear without enlarging or moving them independently of the road.

The warning **OFFLINE UNCOORDINATED COUNTERFACTUAL — SAFETY INTERVENTIONS NOT APPLIED** stays above the cameras. Controls include Play/Pause, Restart, recorded-frame slider, 0.5×/1×/2× speed and Jump to recorded event. Playback follows timestamp differences; fetch/render overhead can slow wall-clock playback. Restart resumes from the six-vehicle sample. At the actual collision-bearing frame it pauses automatically and retains that frame until restart, scrubbing or exit. The status shows **ACTUAL SUMO COLLISION DETECTED**, native count, real IDs and both timestamps. A thin unfilled circle annotates the real reference position without replacing the vehicle bodies. Back to protected scenario closes the viewer without changing the live controller.

Long assumptions, provenance and the three-mode table are below the cameras in a secondary expansion. Sidebar text now explicitly describes the separate collision replay.

## Genuine comparison

Same frozen six-vehicle demand, geometry, vehicle type, initial departure-speed policy, seed 42 and 0.04 s integration step. Budget 220 s, with completion/first-collision early termination.

| Mode | Spawned | Completed | Collisions | MAPPO epochs | Observation end | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protected MAPPO + rules + ego-local safety | 6 | 6 | 0 | 1 | 64.36 s | Complete |
| Existing rules-only, safety retained | 6 | 1 | 0 | 0 | 220 s | Safe deadlock |
| Recorded uncoordinated counterfactual | 6 | 0 before cutoff | **1** | 0 | 24.28 s | First collision detected |

The browser rehearsal ran the protected case to completion and saved its actual terminal publisher. It confirmed zero blocked-zone violations, at most four negotiation participants and zero centralized critic calls. Its one real MAPPO epoch contributes alongside rules and safety; these results do not isolate MAPPO as the sole cause of safety. The rules-only row is preserved previously executed evidence, not a new rerun or collision experiment.

The unsafe recording's own process omits MAPPO, regulatory execution, entry authority, safety shield, explicit junction stops, native safe-follow-speed and junction-priority enforcement. Speed mode 38 retains acceleration/deceleration and speed-limit enforcement; the original vehicle dimensions and physical limits remain unchanged. Native safe insertion remains. Junction collision checking is enabled, minGap expansion is zero for physical-body detection, action is warn, and teleporting is disabled. Declared braking parameters do not restore autonomous collision avoidance under this configuration. None of these settings enters the protected launcher.

## Browser and automated evidence

Actual local headed Chromium 156.0.8078.4 exercised the direct action without opening Recorded comparison, observed six recorded vehicles and changing real positions, played through approach to collision, and verified frame **202 / 24.28 s / paused**. The two colliding bodies had visible bounding boxes inside the central camera. The collision remained unchanged over a hold interval. Restart, laptop controls, exit, protected completion and selection of Scenario 1 were tested. Sidebar scroll position survived updates. No browser page errors occurred.

Evidence directory: `results/offline_counterfactual/central_presentation_v1/`.

- [Six approaching](../results/offline_counterfactual/central_presentation_v1/six_approaching.png)
- [Before impact, 23.80 s](../results/offline_counterfactual/central_presentation_v1/before_impact.png)
- [Authentic impact, desktop](../results/offline_counterfactual/central_presentation_v1/authentic_impact.png)
- [Authentic impact, laptop](../results/offline_counterfactual/central_presentation_v1/laptop_impact.png)
- [Protected comparison in progress](../results/offline_counterfactual/central_presentation_v1/protected_comparison.png)

These screenshots were actually opened and visually inspected: both colliding vehicle bodies, their central-junction location and the annotation are visible, not just a collision message. The full-network overview necessarily shows physically small distant vehicles; the synchronized detail preserves physical proportions while enlarging the junction.

`receipt.json` records the browser PASS, initial/impact frames and protected metrics. `protected_terminal.json` records 6/6 completion at 64.36 s. `geometry_integrity_audit.json` verifies location, footprints, native XML, raw trace checksum, original network/demand assets, the four protected controller identities, E5 checksum and **2,334 historical files unchanged**.

The website/runtime/native-hold/mandatory-fallback regression set passed **166 tests**. After the final sidebar wording and evidence-table cleanup, the website subset passed **107 tests**; this overlaps the larger set. Geometry tests verify the real junction polygon, six-vehicle start, authentic collision and synchronized cameras. No retraining or scientific controller changes occurred. The other four scenario definitions and original recorded experiments remain unchanged.

## Presenting Scenario 5

The updated original application is running at **http://127.0.0.1:8099/component/right-of-way/live**. Use this refreshed server rather than an older application process that may still hold previously imported page code.

1. Select Scenario 5.
2. Click **PLAY UNCOORDINATED COLLISION REPLAY**. It starts automatically with six recorded vehicles.
3. Watch the central detail as vehicles converge. Use 0.5× near impact or Jump to recorded event.
4. The genuine collision pauses with its IDs and native time visible. Use Restart to repeat.
5. Click Back to protected scenario, then **PLAY PROTECTED SYSTEM** for the safe live comparison. The ordinary Run Scenario button remains protected as well.
6. Expand Recorded comparison for the rules-only safe-degradation result, or the replay's evidence expansion for the three-mode table.

To start the presentation later, from the repository root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8099
```

The replay ends at the first detected collision; no post-impact dynamics are claimed. One deterministic educational case removing coordination **and** specified safety interventions does not prove collisions inevitable without MAPPO, nor universal collision freedom for the protected method. This task did not run another unsafe experiment because the original central collision already satisfies the spatial requirement.
