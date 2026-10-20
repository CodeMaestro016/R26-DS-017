inD two-stage intention predictor — CPU deployment bundle
==========================================================

This folder is for inference inside the Visual Studio SUMO/TraCI project.
The laptop runtime requires NumPy and CPU-only ONNX Runtime.
It does not load the original Keras model files.

Model input: scaled float32 tensor shaped (batch, 48, 6).
Position history contract: 50 genuine samples at 0.04 s intervals.
Model output: probabilities for LEFT, RIGHT and STRAIGHT.
Apply the included scalers and robust UNKNOWN policy.

Install in the SUMO Python environment with:
    pip install -r requirements_sumo_cpu.txt

Do not interpolate 0.5-second SUMO observations into artificial 25 Hz samples.
