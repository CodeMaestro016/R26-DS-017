# Scalability study plan — not executed

Purpose: observe how the existing system changes as total scheduled traffic
increases, without claiming a statistically universal capacity threshold.
Both preserved seven-load studies have **0/7 scientific cases**; all scientific
rows remain NOT_RUN. Their separate plumbing preflights are not load-study data.

| Family | Scientific cases | Preflight completed | Scheduled | MAPPO calls | Stop | Wall seconds |
|---|---|---|---|---|---|---|
| SCALABILITY_VALIDATION_V1 | 0 | 0 | 4 | 0 | DEADLOCK_CONFIRMED | 24.637588599987794 |
| SCALABILITY_VALIDATION_V2 | 0 | 0 | 4 | 1 | DEADLOCK_CONFIRMED | 32.82720749999862 |


The existing V2 plan is the appropriate candidate for review: seven single
episodes at 4,8,12,16,24,32,40 vehicles, using exact prefixes of one deterministic
40-entry NESW round-robin stream, 0.4 seconds between entries and 1.6 seconds
per approach. Original legal movements and the fixed 180-second budget per
case stay unchanged. V1's identical initial departure times confounded load
interpretation; V2 staggered the opening but its preflight also deadlocked.
Do not tune spacing or movement order based on those outcomes.

Intersection, E5, intention models, traffic rules, geometry, vehicle physics,
speed mode 31, safety constraints, ego-local execution and <=4 queue heads
remain fixed. Followers use native SUMO car-following. Scientific inference
uses the existing masked stochastic sampler with one deterministic versioned
action seed across loads. No retraining or multi-seed search is proposed.

Record scheduled/spawned/completed counts separately, never-spawned demand,
actual departure delays, collision/blocked-zone/emergency-braking counts,
deadlock/timeout, unfinished spawned vehicles, safe holds, throughput,
average/p95/max incoming wait, per-approach mean/gap and served-pair FCFS
inversions where available. Record active/moving peaks, approach queue depths,
MAPPO calls/accepted/rejected/fallback outcomes, maximum participants, existing
hardware-dependent inference/execution timings and all integrity guard counters.
Unavailable trip metrics and no-call fallback rates remain N/A. Unfinished
exposure/wait is censored. Pending insertion alone is not negotiation failure.
NETWORK_CAPACITY_LIMIT requires the original frozen positive capacity evidence,
not just fewer spawned vehicles; otherwise retain explicit uncertain/backpressure
attribution. Preserve PASS/SAFE_DEGRADATION/UNSAFE_FAILURE/INVALID outcomes.

The existing conservative full-budget estimate is 146.18 minutes, not measured
seven-load runtime. Early deadlock stops might shorten it, larger-load costs
could increase it. Do not launch a large study without approval. Naming changed
live source hashes: the existing manifests must remain frozen. Reproduction
requires their exact archived source set, or a separately approved diagnostic
protocol/version, not editing the original manifest. A new diagnostic is not
directly comparable to the original V1 final evaluation, which used different
seeds, arrival spacing and inference. It must be labeled diagnostic and separate.

If viva time is limited, present verified historical 16-vehicle evidence and
the targeted 1/16 and 0/16 limitations, explicitly stating that broader
scalability remains future work. No threshold between unmeasured loads is known.
