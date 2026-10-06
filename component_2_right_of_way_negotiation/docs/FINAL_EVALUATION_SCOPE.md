# Frozen final system evaluation scope

This is a separate post-training SUMO evaluation of the current ego-local
execution system. The 16-vehicle panel demonstration remains
`QUALITATIVE_PRESENTATION_ONLY`; it is not relabelled as validation evidence.

The operational domain is one existing unsignalized four-way intersection,
AV-only traffic, one incoming lane/stream per N/E/S/W approach, the existing
12 legal movements and `DE_STVO_UNCONTROLLED_4WAY_V1` rules. Perception,
intention models, conflict geometry, ideal same-step coordination, speed mode
31 and native vehicle physics are unchanged. At most one physical queue head
per approach participates, with no more than four encoded negotiation nodes.
Followers remain under native car-following even when total traffic exceeds
four vehicles. The selected canonical E5 checkpoint and CTDE training history
are frozen. Evaluation uses the same deterministic masked-argmax inference
configuration as the panel runtime; results do not retrospectively change the
historical stochastic policy-selection experiment.

Out of scope: roundabouts, T-junctions, signals, pedestrians/cyclists, mixed
HDV/CAV traffic, real packet networks, CARLA, real vehicle deployment, and
more than four simultaneous negotiation participants. inD is intention-model
training provenance only. No new real-data pipeline or real-world validation
is performed.

## Predeclared matrix

| Family | Vehicles | Per-approach demand headway (s) | Fixed budget (s) | Seeds |
|---|---:|---:|---:|---|
| rule_resolved_two | 2 | simultaneous | 180 | deterministic, once |
| regulatory_cycle | 4 | simultaneous | 180 | deterministic, once |
| multiple_left_turns | 3 | simultaneous | 180 | deterministic, once |
| mixed_manoeuvres | 4 | simultaneous | 180 | deterministic, once |
| four_way_simultaneous | 4 | simultaneous | 180 | deterministic, once |
| normal | 8 | 2.00 | 240 | all ten |
| congested | 12 | 1.75 | 300 | all ten |
| dense | 16 | 1.50 | 360 | all ten |
| stress | 24 | 1.00 | 480 | all ten |
| extreme_stress | 32 | 0.75 | 600 | all ten |

Seeds: `101,202,303,404,505,606,707,808,909,1010`.
All continuous cases represent four approaches. Each approach uses shuffled
blocks of its three existing legal movements, with counts differing by at
most one. `random.Random(seed)` affects movement order only, in fixed NESW
generation order. There is no arrival jitter. Identical generated demand is
shared by all three methods. Functional cases intentionally include the
existing two- and three-approach controls; they are not forced into four-car
cases. No training, validation, or held-out result is used to tune demand.

Three methods × (five functional episodes + five demand families × ten seeds)
= **165 final episodes**, with a maximum **62,100 simulated seconds /
1,552,500 simulation steps** before early completion. Budgets are resource
choices fixed before measurements, not performance-tuned limits. No failed
case gets an increased duration.

`--prepare` freezes a canonical JSON manifest with SHA-256, policy identity,
source/model/map/config hashes, simulator/Python identities, seeds, budgets,
method definitions, classifications and statistics. It refuses mismatches.
Each episode checks frozen source identities before and after execution.
The code includes reporting in this freeze; finish edits before preparation.

## Methods and safety

`PROPOSED_MAPPO`: existing rules, frozen E5 masked argmax only at authorized
ambiguity/cycles, existing explicit negotiation protocol, ego-local execution.

`RULE_PLUS_FCFS`: existing symbolic claim masks and the same explicit
proposal/acceptance protocol. A later priority holder relinquishes only its
authorized incoming claim to an earlier counterparty; permitted responses
accept. Existing mandatory outgoing obligations and nonnegotiable relations
cannot be removed by an FCFS decision. No GNN or actor forward determines
baseline actions. Equal arrival times use vehicle ID for reproducibility,
not as a traffic-law rule.

`RULES_ONLY`: no negotiated outcome. Rules still resolve executable cases;
unresolved coordination leads to ego-local safe holding. Timeouts and deadlock
are retained. All methods use the identical map, geometry, native safety and
physical execution. Evaluation alone supplies `--time-to-teleport -1` and a
fixed SUMO seed 0 to prevent deadlocks being hidden by automatic teleporting.
No vehicle is manually repositioned or overlapped. SUMO controls safe insertion.

Classification priority: **INVALID_EXPERIMENT** for integrity/nonfinite or
unexplained execution errors; otherwise **UNSAFE_FAILURE** for any collision
or blocked-zone violation; otherwise **SAFE_DEGRADATION** for unfinished
demand/timeout; otherwise **PASS**. A safe efficiency regression is not unsafe.
Long stopped periods are separately labelled `deadlock_observed` using the
existing threshold, and are not claimed as a proof of permanent deadlock.

Actor/GNN evaluation mode, backward/autograd calls, all installed optimizer
step implementations, runtime critic forward and centralized planner control
are guarded. Actor/GNN tensors are compared exactly before/after; checkpoint
SHA-256 must remain
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
Every integrity failure stays visible and is excluded from performance means.
Finite simulation evidence is reported as “0 collisions observed in N
evaluation episodes,” never as a zero collision probability.

## Measurement definitions

- **TTT / total team traffic exposure** reuses
  `negotiation_objective.accounting.interval_vehicle_exposures`: sum of elapsed
  scheduled-demand-to-network-exit time, censored at the budget for unfinished
  or unspawned demand. It includes insertion waiting. This preserves the
  existing objective without changing reward or retraining.
- **Mean/median/p95/max travel time** describes completed trips from scheduled
  demand to network exit. Unfinished trips are excluded from these summaries;
  completion and censored TTT are always shown alongside. Aborted travel/TTT
  values are N/A. Actual insertion and completion clocks are also archived.
- **Waiting** accumulates the simulation interval when the observed speed is
  below existing `STOPPED_SPEED_THRESHOLD_MPS` (0.5 m/s) and the front bumper
  remains on its incoming lane. This includes followers; excludes internal
  and outgoing stopped time. Sampling resolution is 0.04 s. Unfinished waits
  are observed lower bounds; unspawned vehicles have N/A waiting, not zero.
- **Approach fairness gap** is max minus min of N/E/S/W mean observed wait.
  It is N/A unless all four approaches have spawned observations. Smaller
  means more equal average waiting, not a guarantee of individual fairness.
- **FCFS inversions** compare incoming-lane entry order with front-bumper
  incoming-lane exit order, only for geometrically conflicting pairs from
  different approaches with both service timestamps. Same-stream pairs cannot
  overtake and are excluded; nonconflicting concurrent movements are excluded.
  Both orders use `(timestamp, vehicle_id)` to break ties consistently.
  The eligible-pair denominator is stored; unresolved/unserved pairs are
  excluded and low completion must be considered alongside this metric.
- **Throughput** is completed network exits per observed simulated minute.
  **Completion** divides network exits by all scheduled demand.
- **Native braking** counts contiguous per-vehicle periods where observed
  deceleration exceeds its configured comfortable deceleration, with initial
  timestamp/acceleration evidence. SUMO warning logs and emergency-stopping
  API event counts remain separately archived. These are intervention evidence,
  not collisions, not learned braking actions and not equivalent APIs.
- **Timing** uses `perf_counter_ns` around complete joint MAPPO inference and
  each ego decision plus native constraint calculation. Summaries are hardware
  dependent. The fraction of joint calls above 40 ms is not a universal
  real-time feasibility claim. Baseline/no-call inference values are N/A.
- **Liveness/scalability** retains scheduled/spawned/completed/unfinished counts,
  time budget and completion time, maximum active/moving traffic, incoming
  depths, negotiators, event counts, safe holds and long stopped periods.

Percentiles use linear interpolation. Across repeated episode metrics:
mean, median, sample SD and deterministic percentile bootstrap 95% CI of the
mean (2,000 resamples, seed 260826). A deterministic single functional episode
has no SD/CI. No p-values are reported. Pairwise comparisons use identical
scenario/seed demand. Relative difference is `100*(MAPPO-baseline)/baseline`;
zero baseline gives N/A. Completion differences use percentage points.
No weighted fairness score or ambiguous global order-displacement metric is
introduced.

Controlled robustness checks exercise missing/stale coordination and
missing/stale clearance directly at the existing controller interface. They
check SAFE_HOLD and rejection of attempted blocked-zone entry. They are
bounded fail-safe tests, not physical fault episodes or packet-network studies.
