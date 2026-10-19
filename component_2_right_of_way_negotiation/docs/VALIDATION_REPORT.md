# Validation report

## Checks completed in this workspace

- Every Python source and test file compiles.
- Every XML and SUMO configuration file is well formed.
- The deployment manifest confirms TensorFlow-free CPU inference.
- The runtime contract matches the bundle:
  - 50 two-dimensional position samples;
  - one genuine sample every 0.04 seconds;
  - one 48x6 causal feature sequence.
- Low-rate 0.5-second histories are rejected.
- Short histories are rejected.
- The corrected SUMO navigation-angle conversion is tested.
- Propagated tracks do not create fake model observations.
- The ONNX bundle's supplied verification report records probability parity
  with the frozen Keras models to below 0.000001.

## Checks that must run on the Windows/SUMO machine

This build workspace does not contain SUMO, TraCI or ONNX Runtime. Therefore
the following integration checks must be run after installing
`requirements.txt` and compiling the network:

```powershell
networks\build_network.bat
python -m unittest discover -s tests -v
python main.py
```

The complete live checkpoint passes when:

1. both ONNX sessions report `CPUExecutionProvider`;
2. SUMO reports 0.04-second simulation steps;
3. `results/shadow_predictions.csv` contains predictions;
4. the run completes without invalid-history messages during continuous
   visibility;
5. shadow coverage and accepted accuracy are reported.

## Scope boundary

This package completes corrected model deployment and shadow evaluation. It
does not claim that the right-of-way research system is complete. Map-aware
conflict zones, the distributed negotiation protocol, the crossing scheduler
and an independent safety shield are still required before predictions may
affect vehicle control.
