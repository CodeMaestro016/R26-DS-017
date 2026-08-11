# Multi-Agent Right-of-Way — ONNX Shadow Integration

This project is the corrected prediction-integration checkpoint for:

> Multi-Agent Negotiation for Right-of-Way in Complex Intersections

It runs the trained two-stage GRU intention predictor inside the SUMO/TraCI
application using CPU-only ONNX Runtime. TensorFlow is not required.

## What this checkpoint does

- Uses only autonomous vehicles.
- Gives every AV a separate Local Dynamic Map.
- Samples SUMO at 0.04 seconds to satisfy the trained model contract.
- Keeps 50 genuine position samples per ego-target pair.
- Recreates the locked 48x6 causal feature sequence.
- Loads both ONNX GRUs with `CPUExecutionProvider`.
- Applies the stored training-only scalers and UNKNOWN thresholds.
- Stores predictions separately in every ego AV's LDM.
- Logs primary, secondary and fused shadow predictions.
- Sends intention predictions to the optional dashboard payload.
- Keeps the prediction output out of vehicle control.

## Why predictions are shadow-only

The current negotiation manager is still the original rule-based baseline and
the current risk module is only a provisional centre-arrival metric. The project
does not yet contain:

- lane-path conflict zones;
- an explicit vehicle-to-vehicle negotiation protocol;
- a distributed crossing scheduler;
- an independent safety shield.

Using learned predictions for control before these modules exist would mix a
verified prediction model with unverified decision logic.

## First-time setup on Windows

1. Install SUMO and set the `SUMO_HOME` environment variable.
2. Open a terminal in this project directory.
3. Create and activate a Python virtual environment.
4. Install the CPU requirements:

   ```powershell
   pip install -r requirements.txt
   ```

5. Build the expanded four-way network:

   ```powershell
   networks\build_network.bat
   ```

6. Run the tests:

   ```powershell
   python -m unittest discover -s tests -v
   ```

7. Start the project:

   ```powershell
   python main.py
   ```

   Alternatively:

   ```powershell
   run_project.bat
   ```

## Deterministic eligibility validation

`VALIDATION_SCENARIO_ENABLED = True` in `config.py` selects a deterministic
schedule of crossing approaches, balanced across LEFT, RIGHT and STRAIGHT.
It retains SUMO safety checks and shadow-only inference. Run it on Windows:

```powershell
cd "C:\Users\Iresha Nethmini\Documents\updated_sumo_intention_project_complete\updated_sumo_intention_project"
python -m py_compile *.py tests\*.py
python -m unittest discover -s tests -v
python main.py
```

To return to normal cyclic traffic, set
`VALIDATION_SCENARIO_ENABLED = False` in `config.py` and run `python main.py`.

## Expected startup messages

The runtime should report that:

- both intention models loaded using `CPUExecutionProvider`;
- SUMO started with 0.04-second steps;
- shadow predictions are being produced.

The prediction log is written to:

```text
results/shadow_prediction_events.csv
```

The log contains the SUMO route-derived manoeuvre label for evaluation only.
That field is deliberately isolated from preprocessing, inference, risk and
control. At the end of the run, the console reports:

- `Shadow_Coverage`: the proportion of predictions not rejected as UNKNOWN;
- `Shadow_Accepted_Accuracy`: accuracy among accepted predictions.

These are the first useful measurements of cross-domain performance. The high
accuracy measured on held-out inD data must not be assumed to transfer to SUMO.

## Important research notes

### Reference perception profile

The virtual object sensor uses a Bosch corner-radar reference profile: a
nominal maximum range of 160 m and an individual horizontal FOV of 150 degrees,
with four overlapping units assumed. The interface consumes one fused
360-degree object list. That is complete surround coverage, not one radar's FOV
and not `4 x 150 degrees` because overlapping coverage cannot be added.

The project's minimum observation distance is separately derived as 118.34 m
from closing speed, required context time, and a provisional 35 m conservative
margin. That margin is neither an ASAM OSI value nor a Bosch specification; it
still needs justification through processing/stopping distance, braking,
uncertainty, and sensitivity analysis. "Up to 160 m" does not imply perfect
detection of every object at that distance. None of these reference values are
universal AV-sensor or ASAM/ISO requirements.

Source: [Bosch Mobility corner radar sensor for heavy commercial vehicles](https://www.bosch-mobility.com/en/solutions/sensors/corner-radar-sensor-cv/).

The perception profiles are:

- `IDEAL_BASELINE`: 160 m limit, no FOV filtering or occlusion, exact simulator values; unrealistic upper-performance baseline.
- `GEOMETRIC_SENSOR`: 160 m limit, fused 360-degree FOV (150 degrees per reference radar), dynamic vehicle occlusion, exact values for visible targets; geometric visibility experiment.
- `REALISTIC_OBJECT_SENSOR`: currently the same range, fused FOV, and occlusion as the geometric profile. Noise, missed detections, and latency are not implemented; it remains a future error-model placeholder.

### Sampling

The models require exactly 50 genuine observations separated by 0.04 seconds.
The history validator rejects 0.5-second observations. It does not interpolate
low-rate positions.

### Route truth

SUMO's route ID is retained for debugging and later evaluation only. It is not
used by the ONNX predictor. A surrounding vehicle's true future route must not
be exposed to the agent's decision pipeline because that would bypass the
intention model.

### Network

The source network provides all 12 approach/maneuver combinations:

- four straight routes;
- four left-turn routes;
- four right-turn routes.

The included source files must be compiled with `netconvert` before the first
run.

### Generalization

The GRUs were trained using the inD Bendplatz cohort. This synthetic SUMO cross
is a deployment and robustness test, not proof that the original test accuracy
transfers unchanged to a new map.

## Intention-aware local conflict graph

Conflict detection now runs in shadow/read-only mode after prediction. At
startup, `MapPathManager` reads the compiled SUMO network and discovers legal
LEFT, RIGHT, and STRAIGHT connection paths for each incoming lane.
`ConflictZoneManager` precomputes stable path-pair relationships and uses
Shapely swept envelopes based on each vehicle's actual width. It adds no fixed
safety or uncertainty buffer. `ConflictGraphManager` then independently builds
an ego-centred graph from each AV's own LDM.

Path IDs include the exact incoming lane (for example,
`W_IN_0_STRAIGHT`) so multi-lane approaches cannot overwrite movements with
the same manoeuvre. Duplicate IDs fail initialization explicitly.

Topology and occupied geometry are separate. Lane connectivity identifies
SAME_PATH, DIVERGING, MERGING, or POTENTIAL_CROSSING relationships. A
POTENTIAL_CROSSING becomes CROSSING, and a coordinated zone ID is assigned,
only when the actual width-buffered envelopes have a non-empty intersection:
`Z_ij = P_i intersection P_j`. Centreline intersection is not required.
SAME_PATH and DIVERGING relationships receive no high-level conflict-zone ID.
Flat buffer end caps stop at map-path endpoints and round joins form continuous
offsets around bends; neither adds metres beyond half the physical width.

The static manager retains each complete Polygon, MultiPolygon, or
GeometryCollection and distance-along-path intervals for both paths. Runtime
decisions use LDM widths; the startup catalogue uses the explicit 1.8 m width
of the project's SUMO AV type. Startup writes network-derived validation data
to `results/conflict_map_paths.csv` and
`results/conflict_zone_catalogue.csv`. `CONFLICT_DEBUG_OUTPUT` optionally
prints one startup summary and is disabled by default.

An ego obtains only its own navigation manoeuvre. A target path comes from its
current lane plus the authoritative fused intention result. UNKNOWN, unavailable,
or map-infeasible predictions conservatively retain every legal movement from
the target lane. Target route ID, route index, and ground-truth manoeuvre are
not consumed. When valid manoeuvre probabilities are available, the reported
spatial-conflict probability is exactly the probability mass of map-conflicting
classes; it is not collision risk and has no additional threshold or weight.

The operational graph contains only CROSSING and MERGING relationships.
DIVERGING and SAME_PATH relationships remain map diagnostics for later
lane-following/safety layers. This module makes no TTC, arrival-time,
right-of-way, priority, negotiation, or control decision.

The design adopts conflict-zone/local-distributed reasoning from Liu et al.,
“Distributed Conflict Resolution for Connected Autonomous Vehicles” (2018),
DOI `10.1109/TIV.2017.2788209`; graph representation principles from Chen et
al., “Conflict-Free Cooperation Method for Connected and Automated Vehicles at
Unsignalized Intersections” (2022), DOI `10.1109/TITS.2022.3182403`; and broad
architectural support from Zhong, Nejad, and Lee, “Autonomous and
Semi-Autonomous Intersection Management: A Survey” (2020). The intention-aware,
ego-local integration is project-specific; it is not claimed as those papers'
exact method or as a globally novel first implementation.

`ConflictEntryMonitor` remains separate and controls prediction timing and
eligibility. The conflict graph performs only spatial path-conflict detection.

When covariance-backed tracking is added later, envelopes can be expanded by
statistically derived position uncertainty rather than a guessed distance.

Existing safety score, collision, throughput, and travel-time outputs do not
validate this graph: it remains shadow-only. Geometry is validated separately
through actual-map and synthetic envelope-intersection tests.

## Future stages

Temporal zone-entry/exit reasoning, arrival-time overlap, risk assessment,
right-of-way negotiation, scheduling, and an independent safety shield remain
future work. The shadow conflict graph is not connected to vehicle control.
