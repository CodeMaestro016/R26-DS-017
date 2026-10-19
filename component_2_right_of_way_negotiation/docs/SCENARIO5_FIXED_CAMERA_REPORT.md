# Scenario 5 fixed-camera correction

The replay previously computed camera extent from every vehicle's position on each frame. Distant arrivals expanded the camera, and approaching traffic narrowed it. The collision banner also appeared only at impact, changing the space available for the SVG. Both causes have been removed.

Scenario 5 now calls the existing common intersection renderer at a constant **1.0×** zoom and uses its standard camera bounds. Its camera no longer depends on vehicle positions, spawning, disappearance or collision. A fixed 56 px event-banner area exists from start to finish, preventing an impact-time canvas resize. The impact marker uses exactly the same fixed world-to-SVG transform as the road and recorded vehicle bodies.

The ordinary Run Scenario action, main canvas, Stop and Restart behavior remain. Original recorded positions, orientations, vehicle dimensions, colors and physical proportions are unchanged. The genuine collision still pauses at the 24.28 s recorded snapshot, showing the native SUMO event at 24.24 s. Its verified location remains 1.805909 m from the real junction center. No new simulation or coordinate alteration was needed. Scenarios 1–4 and all scientific controller/model files are unchanged.

With the standard fixed crop, distant vehicles start outside the visible area and enter it naturally, as in the protected viewer. All six remain loaded and represented in the recorded vehicle panel. Showing the entire 600 m approach network at once would require a different scale; the replay no longer does that.

Actual local Chromium verification passed at desktop 1600×1000 and laptop 1280×720. Through the full approach and collision hold, **976 measured samples** confirmed unchanged SVG road polygon, fixed 1.0× zoom, unchanged rendered body length, constant screen position/bounds and constant SVG-to-screen scale. The collision bodies, marker and cards were visually inspected in both screenshots. Recorded positions advance without camera-induced movement; no interpolation or synthetic positions were added. Playback remains limited to the saved sample cadence.

Stop, restart, collision hold, original single-canvas/no-modal flow and sidebar retention passed with zero page errors. **109 website regression tests passed in 2.76 s**. Full Scenario 2/4 scientific reruns were not repeated for this camera-only change; the previous completed live runs remain preserved. The browser rehearsal checked the protected secondary launch and stopped it, rather than claiming a new full six-vehicle scientific result.

Evidence: `results/offline_counterfactual/fixed_camera_v1/receipt.json` and `fixed_camera_samples.json`.

- [Desktop impact](../results/offline_counterfactual/fixed_camera_v1/main_canvas_collision_desktop.png)
- [Laptop impact](../results/offline_counterfactual/fixed_camera_v1/main_canvas_collision_laptop.png)
- [Before impact](../results/offline_counterfactual/fixed_camera_v1/before_impact.png)

The updated original application is running at **http://127.0.0.1:8100/component/right-of-way/live**. Refresh the page, select Scenario 5, then click Run Scenario. Its camera stays fixed throughout. Stop clears the replay; Run or Restart replay repeats it. No other page, viewer or window is involved.
