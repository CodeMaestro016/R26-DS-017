# Scenario 5 isolated counterfactual and stable sidebar

Implemented in the original Component 2 and shared SOCIALMIND DRIVE application. New evidence is separate under `results/offline_counterfactual/v1/`. The earlier protected/rules-only results and five-scenario study remain untouched.

## 1. Why Scenario 5 previously had no collisions

The protected primary combines real E5 negotiation, mandatory traffic-rule processing, ego-local entry authority, safety correction, explicit junction-entry stops and SUMO native following/junction avoidance. The existing rules-only provider removes negotiation, **not these protections**. When regulatory coordination remains unresolved, entry stays held. Its 1/6 completion and safely held remainder are valid safe degradation, not a failed attempt to animate a collision.

The fixed six-vehicle demand is N/E straight, S right and W left at 0 s, followed by N-left and E-right at 1.5 s. Native safe insertion gives actual departures of 0.04 s for the first four and 1.56 s for the followers. The new counterfactual uses exactly that demand, route/network files, AV type and seed 42; no alternate high-conflict candidate or collision search was needed.

## 2. Exactly what the isolated counterfactual excludes

`offline_counterfactual/run.py` is a standalone command with its own SUMO process and labeled TraCI connection. It never invokes protected execution. It requires `--confirm-offline-unsafe`; the normal runtime CLI and protected launch button have no unsafe mode.

Protocol **`ISOLATED_UNCOORDINATED_COUNTERFACTUAL_V1`** is frozen in `offline_counterfactual/protocol.json`. It excludes MAPPO, traffic-rule execution, entry authorization, shield, explicit junction stops and native safe-following/junction-priority enforcement. SUMO speed mode **38** retains acceleration/deceleration and speed-limit enforcement while removing the named avoidance gates. Desired speed is bounded by the actual vehicle maximum and actual lane allowed speed; trajectories are simulated by SUMO, never assigned or interpolated to force contact.

The original 5.0 m × 1.8 m dimensions, 2.0 m/s² acceleration, 4.5 m/s² comfortable deceleration, 7.0 m/s² emergency limit, 2.5 m type minGap, network, legal routes, type definitions, 0.04 s integration step and native safe insertion are retained. Junction collision checks are explicitly enabled **only in this separate process**. `collision.mingap-factor=0` checks physical-body overlap instead of treating a minimum-gap infringement as a physical collision; this is a disclosed detection setting, not a changed vehicle footprint or road geometry. Protected collision/safety settings are not changed.

## 3. Actual outcome

| Mode | Scheduled / spawned | Completed | MAPPO events | Actual collisions | Termination |
| --- | ---: | ---: | ---: | ---: | --- |
| A. Protected primary | 6 / 6 | 6 | 1 | 0 | Complete at 64.36 s |
| B. Preserved rules-only baseline | 6 / 6 | 1 | 0 | 0 | Incomplete at 220 s; safe holds |
| C. Isolated unsafe counterfactual | 6 / 6 | 0 | 0 | **1** | Stopped at first detection, 24.28 s |

SUMO's native collision XML records a **junction collision at 24.24 s**, involving **PANEL_AV_N_02** and **PANEL_AV_W_01**, both legal left turns (`N_IN_0_LEFT`, `W_IN_0_LEFT`). TraCI reports that collision in the step-ending snapshot at **24.28 s**. Both clocks are displayed explicitly.

SUMO collision reference position: **(299.878894, 301.801844) m**, derived using the simulator's collision lane `:center_2_0`, longitudinal position 5.693641 m and its own `convert2D`. This is the simulator's collision reference location, **not a claimed rigid-body contact point**. Collider/victim speeds were approximately 10.95437 and 8.99987 m/s.

No deadlock was observed before that cutoff. Observed waiting time and throughput in C are 0 s and 0 completed vehicles/minute **until the collision cutoff**. They are not full-horizon performance estimates. There is no total trip-completion time for C. The simulation stops at the first collision; no crash-response dynamics or continued passage through overlapping vehicles is presented. No artificial collision event or alternate tuned demand was inserted.

## 4. Evidence and provenance

- `sumo_collisions.xml`: SUMO's own native event record, including time, IDs, lane/position, vehicle fronts/backs and speeds.
- `replay.json`: sampled actual SUMO positions, dimensions, orientations, speeds and native collision reports, ending at detection.
- `manifest.json`, `protocol.json`, `receipt.json`: exact command, SUMO 1.26.0 version, seed, protocol, demand, asset hashes, trace SHA256 and assumptions.
- `sumo.log`: simulator log, preserved separately from protected output.
- `verification.json`: protected-source/historical integrity and browser evidence audit.

Trace SHA256: `fe7314076f2ee490cf07eb84165944b95c46ab558353ced83f587f732014bbd9`. Tests verify agreement with SUMO XML and **positive intersection of the two recorded 5.0 × 1.8 m body polygons**, so this is neither a predicted conflict nor merely a minimum-gap near miss.

## 5. Website separation

Scenario 5 clearly separates **A. Protected primary**, **B. Rules-only baseline**, and **C. Isolated uncoordinated counterfactual**. **Run Scenario always launches A**. C is available only as a recorded-evidence viewer; opening it does not launch SUMO, change live cards or alter protected controls.

Select Scenario 5, expand **Recorded comparison**, then choose **View offline unsafe counterfactual**. The dialog displays:

> OFFLINE UNSAFE COUNTERFACTUAL — NOT THE PROPOSED SYSTEM

It identifies exclusions, seed, counts, actual event times, IDs, movements, collision reference position and provenance. Play/pause, the recorded-frame slider and **Jump to recorded event** navigate actual samples. The marker annotates the recorded reference location. Blue replay bodies identify recorded vehicles, not protected entry permission. Offline SVG metadata and vehicle classes are separated from live inspector metadata, and live-selection click handlers are removed.

The replay endpoint is GET-only, reads fixed validated evidence paths, clamps frame indices and never calls the launcher or imports simulator control. It cannot select arbitrary evaluation files or execute the counterfactual.

## 6–7. Sidebar cause and correction

The 0.5-second timer refreshed `_scenario_sidebar`, replacing its entire DOM subtree. CSS already allowed overflow, but reconstruction discarded native scroll/focus and expansion state during normal telemetry updates.

The sidebar now mounts once. Only selection changes refresh scenario details. A client-owned timer updates the existing radio/button enabled states, status label and error visibility **in place and only when launcher state changes**. Central telemetry continues refreshing independently. Expansion state stays client-local.

Scoped CSS adds a zero-minimum grid row, zero sidebar minimum height, nonshrinking children, contained overscroll, stable visible native scrollbar and horizontal overflow prevention. This keeps comparison content within its own scroll region; it does not enlarge the webpage because the description is long. The existing layout, colors and grid remain intact. Right-side card scrolling remains independent.

The populated-card test also exposed an existing `.viva-inspector { overflow:hidden }` override. It now allows contained vertical scrolling while still preventing horizontal overflow. The final laptop test moved that panel from **0 to 270.4 px** with the left sidebar unchanged.

## 8–9. Executed verification

The real protected six-vehicle verification run reproduced **6/6 at 64.36 s, one MAPPO event, zero collisions, zero blocked-zone violations and zero unauthorized entries**. Its complete runtime metrics, schedule and actual departures match the earlier protected result exactly. The prior rules-only result remains 1/6, zero MAPPO and zero collisions; it was not overwritten or relabeled as a collision.

The selected research integrity, runtime/safety, presentation and website regression set passed **224 tests in 31.53 s**. The website-only run passed **105 tests**, including native collision provenance, actual body overlap, unchanged A/B results and a read-only replay API whose launcher methods are forbidden during the test.

Actual headed Chromium 156.0.8078.4 checked **1600×1000** desktop and **1280×720** laptop viewports. Wheel down/up, incremental touchpad-like wheel events and actual native scrollbar-thumb dragging all changed measured `scrollTop`. The same native DOM sidebar remained stable while repeated telemetry/status updates ran, with retained bottom positions. Desktop example: **680 → 680 px** over the hold interval; drag **210.4 → 673.6 px**. Laptop: **1207.2 → 1207.2 px** retained; drag **210.4 → 1196 px**. Running checks also retained **696.8** and **1223.2 px** respectively. Tests covered collapse/expand, Scenario 1 → 5 switching, focus retention, accessible Run/Stop, browser reload, and central canvas isolation. Browser screenshots were visually inspected, including the genuine collision replay.

Headless attempts did not deliver native scrollbar drags and are preserved as failed attempts; the final native-drag verification uses headed Chromium in an offscreen window. One early retention test also used a full-page screenshot that resized the viewport during measurement; final retention tests avoid that interference. These failures are not silently reported as passing runs.

The authoritative final browser receipt is **`browser_scroll_v7/receipt.json`**. It verifies actual replay Play/Pause progression as well as the jump-to-collision view, populated right-panel scrolling, all five sidebar retention/drag stages, zero page errors and zero remaining owned processes. The extended `v6` test that exposed the right-panel overflow defect remains preserved.

## 10. Scientific integrity

All **2,334 historical files**, the four approved protected execution source identities, E5 checkpoint, original vehicle/network assets and earlier A/B comparisons pass the final audit. No retraining, policy edits, mandatory-rule weakening, protected physics/safety changes, official evaluation overwrite or unrelated component changes occur. New evidence is explicitly educational and stored outside official evaluation families.

## 11. Limits and startup

This is a deterministic educational counterfactual, not an official baseline or an estimate of real-world collision probability. It removes several safeguards together, so the collision cannot be attributed solely to removing MAPPO. SUMO does not provide a rigid-body crash-response model here; playback ends at detection. Physical touchpad hardware was not driven; its browser wheel-input behavior was tested with small incremental wheel events. Previous multi-run Windows shutdown limitations are not declared universally resolved by a single current rehearsal.

Run the existing main application from the repository root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only --port 8098
```

Open `http://127.0.0.1:8098/component/right-of-way/live`. Scenario 5's normal Run button remains protected. The unsafe evidence is viewed only through its separately labeled offline replay button.
