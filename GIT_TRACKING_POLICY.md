# Git Tracking Policy

## Track in Git

- Source code, tests, requirements, scripts, configuration, and project documentation.
- Required SUMO configuration, network, route, and source XML files.
- Traffic-rule profiles and research-input definitions.
- Required final deployment models: the selected MAPPO policy and ONNX intention models.
- Extracted final-selection manifests, candidate checkpoints, canonical tables, and lightweight scientific evidence.
- Notebooks needed for research provenance.
- NiceGUI showcase source and intentional application assets.

## Do not track

- Virtual environments, bytecode, test/tool caches, IDE state, and OS metadata.
- Secrets, local environment files, temporary files, and logs.
- Runtime-generated latest demo files, progress snapshots, GUI/liveness smoke output, and giant regeneratable traces.
- Duplicate or generated ZIP packaging when canonical extracted artifacts are retained.

## Review case-by-case

- Intermediate training checkpoints and raw datasets.
- Third-party regulatory PDFs, XML snapshots, and rendered pages.
- Large binary evidence and notebooks with large embedded outputs.
- Assets containing personal/academic contact information or third-party branding.

Do not introduce broad ignores for `results/`, `models/`, `docs/`, `networks/`, or scientific file extensions such as JSON, CSV, XML, PT, and ONNX.
