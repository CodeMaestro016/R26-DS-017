# SOCIALMIND DRIVE — Unified Research Showcase

A completely independent, local-only NiceGUI presentation layer for:

**SOCIALMIND DRIVE**  
*Agentic AI for Robust and Socially-Aware Autonomous Driving*

The showcase presents four independently developed research components under one professional visual umbrella. It does not claim that the four research algorithms form one connected live pipeline. Component 2 is currently connected to its existing local SUMO panel demonstration; Components 1, 3 and 4 have presentation pages and reserved adapter spaces.

## Independence and scientific boundary

This folder does not import or reuse the repository's old `debug_dashboard.py`, `debug_dashboard.html`, `sumo_debug_overlay.py`, or other debug UI. It consumes Component 2's existing qualitative result JSON and launches the existing `run_panel_demo.py`; it does not reproduce or modify scientific logic.

## Install and run

From the repository root:

```powershell
python -m pip install -r socialmind_drive_showcase\requirements.txt
python socialmind_drive_showcase\app.py
```

The server listens only on `127.0.0.1:8088`. On Windows it searches common Chrome installation paths and opens `chrome.exe --app=http://127.0.0.1:8088`. If Chrome is unavailable, it opens the system default browser instead. A different local port may be selected with `--port`.

## Pages

- Home: full project hero, research vision and four research pillars.
- Components: overview of all independent research components.
- Component details: objective, focus, visual space and integration status.
- Component 2: live SUMO launch, architecture flow, MAPPO semantics, runtime status, metrics and latest authorized event.
- About: project overview, four research directions, SLIIT institution details, the four-member research team, and project supervision.

## Component 2 launch

The button invokes this predefined command asynchronously from `components/component_2_right_of_way_negotiation/`:

```powershell
python run_panel_demo.py --gui --gui-delay-ms 10
```

Only one instance can be launched at a time. No browser input is accepted as a command or path. Results are refreshed from `results/panel_demo/latest_panel_demo.json`.

Component 2 metrics are clearly classified as **QUALITATIVE PRESENTATION ONLY**. They are not validation, held-out evaluation, model-selection evidence, or replacement quantitative research evidence.

## Visual assets

The UI uses styled gradient/icon fallbacks when files are missing. Add these later if desired:

- `assets/images/home_page.png`
- `assets/images/socialmind_hero.jpg`
- `assets/images/component_1.jpg`
- `assets/images/component_2.png`
- `assets/images/component_3.png`
- `assets/images/component_4.png`
- `assets/logos/socialmind_logo.png`
- `assets/logos/sliit_logo.png`

Optional team portraits live under `assets/team/`; see its README for exact filenames. When a portrait is absent, the page displays initials rather than a broken image.

See `assets/images/README.md` for recommended formats.

## Future component integration

Each component definition in `config.py` has optional `launch_command`, `working_directory`, `result_path`, `image_name`, and `live` fields. Components 1, 3 and 4 intentionally leave runtime fields disabled. A future group member can add a predefined adapter without changing the other pages or inventing a fake command.

## Structure

```text
socialmind_drive_showcase/
  app.py, config.py, requirements.txt
  pages/       route/page builders
  ui/          theme and reusable presentation components
  services/    safe launch, result, browser and folder adapters
  data/        central component access
  assets/      optional local images, logos and icons
  tests/       independent showcase boundary tests
```
