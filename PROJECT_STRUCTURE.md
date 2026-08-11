# Project structure

```text
updated_sumo_intention_project/
|-- main.py
|-- config.py
|-- environment.py
|-- observation.py
|-- perception_interface.py
|-- conflict_entry_monitor.py
|-- conflict/
|   |-- map_path_manager.py
|   |-- conflict_zone_manager.py
|   |-- conflict_graph_manager.py
|   |-- occupancy_assessor.py
|   |-- validation.py
|   `-- models.py
|-- predictor.py
|-- risk_assessment.py
|-- negotiation.py
|-- evaluation.py
|-- intersection.sumocfg
|-- requirements.txt
|-- run_project.bat
|-- README.md
|-- PROJECT_STRUCTURE.md
|-- VALIDATION_REPORT.md
|-- models/
|   `-- intention/                 # ONNX models, locked scalers and policy
|-- networks/                      # SUMO network, routes and build scripts
|-- tests/
|   |-- test_feature_builder.py
|   |-- test_model_bundle.py
|   |-- test_observation.py
|   |-- test_shadow_evaluation.py
|   |-- test_event_eligibility.py
|   `-- test_evaluation_eligibility.py
`-- results/
    |-- shadow_prediction_events.csv
    `-- shadow_confusion_matrices.csv
```

`intersection.net.xml` is generated inside `networks/` by the build script.
The two result CSV files are generated when the simulation finishes.
