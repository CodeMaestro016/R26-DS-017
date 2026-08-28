# SOCIALMIND DRIVE Workspace

This repository is the shared workspace for the SOCIALMIND DRIVE final-year research project. The overall presentation website and each scientific research component remain separate:

```text
R26-DS-017/
|-- socialmind_drive_showcase/
`-- components/
    `-- component_2_right_of_way_negotiation/
```

Component 2 is currently integrated. Components 1, 3, and 4 can later be added beneath `components/` without mixing their implementations.

## Run the showcase

```powershell
python socialmind_drive_showcase\app.py
```

## Run Component 2 directly

```powershell
cd components\component_2_right_of_way_negotiation
python run_panel_demo.py --gui --gui-delay-ms 10
```
