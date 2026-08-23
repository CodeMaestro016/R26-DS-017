# Project Overview

## What This Repository Contains

This project is a pedestrian mental-state recognition pipeline with a SUMO-based autonomous vehicle demo. The notebooks in `component_03/notebook/` cover the data preparation and model training stages, while `component_03/sumo_demo/` contains the runnable demo that combines a trained LSTM + GRU ensemble with a rule-based decision agent.

The repository currently has a very small top-level `README.md`, so this file serves as the main project summary.

## Main Workflow

1. Extract frames and features from pedestrian data.
2. Train sequence models to classify six pedestrian mental states.
3. Save the best models and the feature scaler.
4. Run the SUMO demo to pick a real test sequence, predict the mental state, and apply an AV action through a TTC-based rule engine.

## Repository Structure

### `component_03/notebook/`

- `frame_extraction.ipynb` - frame-level extraction and preparation.
- `pose_estimation.ipynb` - pose-related feature extraction.
- `feature_extraction.ipynb` - builds the feature set used by the models.
- `mean_values.ipynb` - computes summary values used in the pipeline.
- `lstm_training.ipynb` - trains the LSTM mental-state classifier.
- `gru_training.ipynb` - trains the GRU mental-state classifier.
- `LSTM+GRU_ensemble.ipynb` - combines the trained sequence models.
- `transformer_training.ipynb` - trains a transformer-based variant.

### `component_03/sumo_demo/`

- `config/` - SUMO network and simulation configuration files.
- `data/` - test arrays used by the demo, including `X_test.npy` and `y_test.npy`.
- `models/` - trained model artifacts such as `lstm_mental_state_best.h5`, `gru_mental_state_best.h5`, and `transformer_mental_state_best.keras`.
- `scripts/` - runnable demo logic.

## Demo Logic

The demo in `component_03/sumo_demo/scripts/run_demo.py` does the following:

- loads a random real test sequence from `X_test.npy` and `y_test.npy`;
- uses the saved feature scaler to reconstruct raw features for the rule-based agent;
- loads the LSTM and GRU models as an equal-weight ensemble;
- starts SUMO and reads the current AV speed from the simulation;
- applies a rule-based TTC decision to choose `MAINTAIN`, `SLOW_DOWN`, or `STOP`.

The rule-based agent in `component_03/sumo_demo/scripts/rule_based_agent.py` uses six mental states:

- Waiting
- Hesitant
- Committed
- Distracted
- Aggressive
- Jaywalk

## Data And Model Artifacts

The demo expects the following key artifacts to exist in `component_03/sumo_demo/`:

- `data/X_test.npy`
- `data/y_test.npy`
- `models/feature_scaler.pkl`
- `models/lstm_mental_state_best.h5`
- `models/gru_mental_state_best.h5`
- `config/simulation.sumocfg`

## How To Run The Demo

From `component_03/sumo_demo/scripts/`:

```bash
python run_demo.py
```

The script is written for a Windows setup with SUMO installed at the path referenced inside the script.

## Notes

- The notebooks were not executed in this workspace, so this summary is based on the repository structure and notebook contents.
- The repo is organized around a pipeline from feature extraction to model training to simulation demo.