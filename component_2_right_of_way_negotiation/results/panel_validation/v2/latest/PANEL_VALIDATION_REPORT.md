# Panel Validation

TARGETED_PANEL_VALIDATION

One selected unsignalized four-way SUMO intersection; AV-only, one incoming lane per approach, 12 legal movements, ideal same-step messages, <=4 physical queue-head negotiators; up to 16 total traffic vehicles.

This targeted suite validates the implementation against the specific panel feedback within the defined SUMO scope. It is not an exhaustive statistical study and is not real-world deployment validation.

Real-world trajectory data supports the intention-model component, while right-of-way system validation in this study is simulation-based.

Preflight, replays, qualitative demonstrations and comprehensive final evaluation are excluded from these panel case results.

Nominal Dense evaluates operation under continuous congested traffic within the intended operating scope; it is capability evidence only to the extent demonstrated by its actual result. Critical Dense preserves a known liveness limitation under reciprocal mandatory-precedence conditions.

V1 records retain their original run IDs, classifications, metrics and manifest identities. Historical rows are not newly executed V2 episodes. If V2 reruns a case, both records remain visible.

Comment addressed means the requested evidence was implemented and measured; it does not mean every case passed.

For a recorded dense SAFE_DEGRADATION result: Safety was maintained, but liveness/throughput degraded under dense demand. This is bounded episode evidence, not universal safety or production readiness.

Unrun cases and inapplicable metrics display NOT_RUN / N/A. No confidence intervals or statistical generalization from this small suite.

## Seven-case design / seven traffic episodes

| Case / method | Evidence version | Vehicles | Purpose | Completed | Collisions | Blocked-zone violations | Mean wait (s) | Max wait (s) | MAPPO calls | Fallbacks | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PV-01 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 2 | Rule-resolved sanity | 2/2 | 0 | 0 | 0.500 | 1.000 | 0 | 0 | PASS |
| PV-01 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 2 | Rule-resolved sanity | 2/2 | 0 | 0 | 0.500 | 1.000 | 0 | 0 | PASS |
| PV-02 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 4 | Negotiation-required cycle; paired demand | 0/4 | 0 | 0 | 15.110 | 15.120 | 0 | 0 | SAFE_DEGRADATION |
| PV-02 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 4 | Negotiation-required cycle; paired demand | 0/4 | 0 | 0 | 15.110 | 15.120 | 0 | 0 | SAFE_DEGRADATION |
| PV-02 / RULES_ONLY | PANEL_VALIDATION_V2 | 4 | Negotiation-required cycle; paired demand | 0/4 | 0 | 0 | 15.110 | 15.120 | 0 | 0 | SAFE_DEGRADATION |
| PV-02 / RULES_ONLY | PANEL_VALIDATION_V1 (preserved historical record) | 4 | Negotiation-required cycle; paired demand | 0/4 | 0 | 0 | 15.110 | 15.120 | 0 | 0 | SAFE_DEGRADATION |
| PV-03 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 3 | Selected complex manoeuvre | 3/3 | 0 | 0 | 4.240 | 8.040 | 1 | 1 | PASS |
| PV-03 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 3 | Selected complex manoeuvre | 3/3 | 0 | 0 | 3.933 | 7.440 | 2 | 1 | PASS |
| PV-04A / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 16 | Nominal dense continuous traffic: predeclared capability test | 1/16 | 0 | 0 | 141.870 | 157.840 | 2 | 2 | SAFE_DEGRADATION |
| PV-04B / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 16 | Critical dense: preserved reciprocal-precedence limitation | 0/16 | 0 | 0 | 35.790 | 41.680 | 0 | 0 | SAFE_DEGRADATION |
| PV-04B / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 16 | Critical dense: preserved reciprocal-precedence limitation | 0/16 | 0 | 0 | 35.790 | 41.680 | 0 | 0 | SAFE_DEGRADATION |
| PV-05 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 4 | Natural critical limitation case | 0/4 | 0 | 0 | 15.890 | 15.920 | 0 | 0 | SAFE_DEGRADATION |
| PV-05 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 4 | Natural critical limitation case | 0/4 | 0 | 0 | 15.890 | 15.920 | 0 | 0 | SAFE_DEGRADATION |
| PV-06 / CONTROLLED_MESSAGE_CHECKS | PANEL_VALIDATION_V2 | N/A | Controlled missing/stale coordination fail-safe | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PASS |

## SUCCESSFUL CAPABILITY EVIDENCE

| Case / method | Evidence version | Vehicles | Purpose | Completed | Collisions | Blocked-zone violations | Mean wait (s) | Max wait (s) | MAPPO calls | Fallbacks | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PV-01 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 2 | Rule-resolved sanity | 2/2 | 0 | 0 | 0.500 | 1.000 | 0 | 0 | PASS |
| PV-01 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 2 | Rule-resolved sanity | 2/2 | 0 | 0 | 0.500 | 1.000 | 0 | 0 | PASS |
| PV-03 / PROPOSED_MAPPO | PANEL_VALIDATION_V2 | 3 | Selected complex manoeuvre | 3/3 | 0 | 0 | 4.240 | 8.040 | 1 | 1 | PASS |
| PV-03 / PROPOSED_MAPPO | PANEL_VALIDATION_V1 (preserved historical record) | 3 | Selected complex manoeuvre | 3/3 | 0 | 0 | 3.933 | 7.440 | 2 | 1 | PASS |

## PV-04A Dense 16-Vehicle Validation

| Measurement | Recorded value |
| --- | --- |
| total vehicles scheduled | 16 |
| total vehicles spawned | 16 |
| total vehicles completed | 1 |
| maximum simultaneous active vehicles | 16 |
| maximum simultaneously moving vehicles | 16 |
| maximum negotiation participants | 4 |
| mean waiting time seconds | 141.870 |
| median waiting time seconds | 150.340 |
| p95 waiting time seconds | 157.840 |
| maximum waiting time seconds | 157.840 |
| approach waiting time gap seconds | 37.150 |
| conflicting pair fcfs inversion rate | N/A |
| total team travel time seconds | 2697.320 |
| mean travel time seconds | 57.320 |
| throughput vehicles per minute | 0.333 |
| completion rate | 0.062 |
| negotiation events | 2 |
| rule resolved events | 0 |
| mappo inference call count | 2 |
| mappo outcomes accepted | 0 |
| mappo outcomes rejected by safety shield | 2 |
| fallback activations | 2 |
| fallback rate | 1.000 |
| native emergency braking events | 0 |
| emergency braking warning count | 0 |
| N mean wait (s) | 116.590 |
| N maximum queue depth | 4 |
| E mean wait (s) | 150.950 |
| E maximum queue depth | 4 |
| S mean wait (s) | 153.740 |
| S maximum queue depth | 4 |
| W mean wait (s) | 146.200 |
| W maximum queue depth | 4 |
| Classification | SAFE_DEGRADATION |
| Evidence version | PANEL_VALIDATION_V2 |
| Learned negotiation evidence | Recorded invocation only; execution outcomes distinguish direct MAPPO from safety fallback. |

## PV-04B Dense 16-Vehicle Validation

| Measurement | Recorded value |
| --- | --- |
| total vehicles scheduled | 16 |
| total vehicles spawned | 16 |
| total vehicles completed | 0 |
| maximum simultaneous active vehicles | 16 |
| maximum simultaneously moving vehicles | 16 |
| maximum negotiation participants | 4 |
| mean waiting time seconds | 35.790 |
| median waiting time seconds | 35.620 |
| p95 waiting time seconds | 41.680 |
| maximum waiting time seconds | 41.680 |
| approach waiting time gap seconds | 4.710 |
| conflicting pair fcfs inversion rate | N/A |
| total team travel time seconds | 985.440 |
| mean travel time seconds | N/A |
| throughput vehicles per minute | 0.000 |
| completion rate | 0.000 |
| negotiation events | 1 |
| rule resolved events | 0 |
| mappo inference call count | 0 |
| mappo outcomes accepted | 0 |
| mappo outcomes rejected by safety shield | 0 |
| fallback activations | 0 |
| fallback rate | N/A |
| native emergency braking events | 0 |
| emergency braking warning count | 0 |
| N mean wait (s) | 35.790 |
| N maximum queue depth | 4 |
| E mean wait (s) | 37.610 |
| E maximum queue depth | 4 |
| S mean wait (s) | 36.860 |
| S maximum queue depth | 4 |
| W mean wait (s) | 32.900 |
| W maximum queue depth | 4 |
| Classification | SAFE_DEGRADATION |
| Evidence version | PANEL_VALIDATION_V2 |
| Learned negotiation evidence | No MAPPO calls were observed; this case does not demonstrate the learned negotiation layer. |

## PV-04B Dense 16-Vehicle Validation

| Measurement | Recorded value |
| --- | --- |
| total vehicles scheduled | 16 |
| total vehicles spawned | 16 |
| total vehicles completed | 0 |
| maximum simultaneous active vehicles | 16 |
| maximum simultaneously moving vehicles | 16 |
| maximum negotiation participants | 4 |
| mean waiting time seconds | 35.790 |
| median waiting time seconds | 35.620 |
| p95 waiting time seconds | 41.680 |
| maximum waiting time seconds | 41.680 |
| approach waiting time gap seconds | 4.710 |
| conflicting pair fcfs inversion rate | N/A |
| total team travel time seconds | 985.440 |
| mean travel time seconds | N/A |
| throughput vehicles per minute | 0.000 |
| completion rate | 0.000 |
| negotiation events | 1 |
| rule resolved events | 0 |
| mappo inference call count | 0 |
| mappo outcomes accepted | 0 |
| mappo outcomes rejected by safety shield | 0 |
| fallback activations | 0 |
| fallback rate | N/A |
| native emergency braking events | 0 |
| emergency braking warning count | N/A |
| N mean wait (s) | 35.790 |
| N maximum queue depth | 4 |
| E mean wait (s) | 37.610 |
| E maximum queue depth | 4 |
| S mean wait (s) | 36.860 |
| S maximum queue depth | 4 |
| W mean wait (s) | 32.900 |
| W maximum queue depth | 4 |
| Classification | SAFE_DEGRADATION |
| Evidence version | PANEL_VALIDATION_V1 (preserved historical record) |
| Learned negotiation evidence | No MAPPO calls were observed; this case does not demonstrate the learned negotiation layer. |

## Termination and negotiation

| Case | Method | Reason | Observed sim s | Timeout | Deadlock observed | Accepted | Rejected | Fallback rate | Wall s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PV-01 | PROPOSED_MAPPO | ALL_COMPLETED | 48.760 | False | False | 0 | 0 | N/A | 11.935 |
| PV-01 | PROPOSED_MAPPO | ALL_COMPLETED | 48.760 | False | False | 0 | 0 | N/A | 8.869 |
| PV-02 | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 37.280 | False | True | 0 | 0 | N/A | 26.224 |
| PV-02 | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 37.280 | False | True | 0 | 0 | N/A | 22.728 |
| PV-02 | RULES_ONLY | DEADLOCK_CONFIRMED | 37.280 | False | True | 0 | 0 | N/A | 26.004 |
| PV-02 | RULES_ONLY | DEADLOCK_CONFIRMED | 37.280 | False | True | 0 | 0 | N/A | 20.976 |
| PV-03 | PROPOSED_MAPPO | ALL_COMPLETED | 55.520 | False | False | 0 | 1 | 1.000 | 20.007 |
| PV-03 | PROPOSED_MAPPO | ALL_COMPLETED | 54.920 | False | False | 1 | 1 | 0.500 | 16.126 |
| PV-04A | PROPOSED_MAPPO | HARD_TIME_BUDGET | 180.000 | True | True | 0 | 2 | 1.000 | 501.188 |
| PV-04B | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 63.840 | False | True | 0 | 0 | N/A | 169.679 |
| PV-04B | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 63.840 | False | True | 0 | 0 | N/A | 141.891 |
| PV-05 | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 38.080 | False | True | 0 | 0 | N/A | 24.386 |
| PV-05 | PROPOSED_MAPPO | DEADLOCK_CONFIRMED | 38.080 | False | True | 0 | 0 | N/A | 19.050 |

## PANEL FEEDBACK TRACEABILITY

| Original comment | Cases | Evidence | Status |
| --- | --- | --- | --- |
| Fairness-time measurement is very important. Narrow the scope to selected complex intersections. | PV-03, PV-04A | Bounded scope, selected complex manoeuvre, nominal dense per-approach/max/p95 wait, TTT, throughput and service-order inversion | MEASURED |
| Plan how to demonstrate the implemented system. Need to address complex scenarios. | PV-02, PV-03, PV-04A, PV-04B, PV-05 | Regulatory cycle, left turns, both dense conditions and natural four-way limitation with recorded replays | MEASURED |
| 4 vehicles are not enough. Use a more congested scenario. | PV-04A, PV-04B | Nominal: 16 continuous vehicles, queues and actual progression measurements. Critical: same-scale preserved failure boundary. Both: measured live/moving and <=4 negotiators. | MEASURED |

## LIMITATION / FAILURE EVIDENCE

| Case | Method | Result | Cause |
| --- | --- | --- | --- |
| PV-02 | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 37.28, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 22.28, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-02 | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 37.28, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 22.28, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-02 | RULES_ONLY | SAFE_DEGRADATION | {"confirmed_at": 37.28, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 22.28, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-02 | RULES_ONLY | SAFE_DEGRADATION | {"confirmed_at": 37.28, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 22.28, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-04A | PROPOSED_MAPPO | SAFE_DEGRADATION | null |
| PV-04B | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 63.84, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 48.84, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-04B | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 63.84, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_E_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_02": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_03": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_04": ["SAFE_HOLD", "FOLLOWER_AWAITING_NEGOTIATED_ADMISSION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 48.84, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-05 | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 38.08, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 23.08, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |
| PV-05 | PROPOSED_MAPPO | SAFE_DEGRADATION | {"confirmed_at": 38.08, "decisions": {"PANEL_AV_E_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_N_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_S_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"], "PANEL_AV_W_01": ["SAFE_HOLD", "MISSING_OR_STALE_LOCAL_COORDINATION", "HELD_BEFORE_ZONE"]}, "existing_threshold_seconds": 15.0, "stable_all_held_since": 23.08, "statuses": {"PANEL_AV_E_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_N_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_S_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT", "PANEL_AV_W_01": "COMMUNICATED_PRECEDENCE_DISAGREEMENT"}} |

## Architecture / integrity

| Case | Method | Runtime guard values |
| --- | --- | --- |
| PV-01 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-01 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-02 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-02 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-02 | RULES_ONLY | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-02 | RULES_ONLY | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-03 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-03 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-04A | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-04B | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-04B | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-05 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |
| PV-05 | PROPOSED_MAPPO | {"backward_calls": 0, "centralized_critic_runtime_calls": 0, "centralized_execution_graph_used_for_control": false, "decentralized_execution": true, "frozen_sources_unchanged": true, "global_execution_calls": 0, "modules_in_evaluation_mode": true, "optimizer_steps": 0, "parameter_updates": 0, "policy_hash_unchanged": true, "policy_sha256_after": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "policy_sha256_before": "2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57", "state_dict_unchanged": true, "training_operations": 0, "valid": true} |

## Recorded events and exact replay

| Case | Run | Execution outcomes | Replay command |
| --- | --- | --- | --- |
| PV-01 | 20261009T063517382359Z_6e94b60d | RULE_RESOLVED | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-01 --run-id 20261009T063517382359Z_6e94b60d --gui --output-root "results\panel_validation\v2" |
| PV-01 | 20261008T171523337394Z_54c691c5 | RULE_RESOLVED | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-01 --run-id 20261008T171523337394Z_54c691c5 --gui --output-root "results\panel_validation\v1" |
| PV-02 | 20261009T063529451480Z_38673d97 | SAFE_HOLD | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-02 --run-id 20261009T063529451480Z_38673d97 --gui --output-root "results\panel_validation\v2" |
| PV-02 | 20261008T171532286342Z_5b9a74aa | SAFE_HOLD | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-02 --run-id 20261008T171532286342Z_5b9a74aa --gui --output-root "results\panel_validation\v1" |
| PV-02 | 20261009T063555768975Z_bdeef494 | SAFE_HOLD | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-02 --run-id 20261009T063555768975Z_bdeef494 --gui --output-root "results\panel_validation\v2" |
| PV-02 | 20261008T171555087321Z_954c9a9b | SAFE_HOLD | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-02 --run-id 20261008T171555087321Z_954c9a9b --gui --output-root "results\panel_validation\v1" |
| PV-03 | 20261009T063621851275Z_c2d7ed8e | MAPPO_WITH_SAFETY_FALLBACK, RULE_RESOLVED | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-03 --run-id 20261009T063621851275Z_c2d7ed8e --gui --output-root "results\panel_validation\v2" |
| PV-03 | 20261008T171616134855Z_5e39804a | MAPPO_WITH_SAFETY_FALLBACK, MAPPO_DIRECT | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-03 --run-id 20261008T171616134855Z_5e39804a --gui --output-root "results\panel_validation\v1" |
| PV-04A | 20261008T175551068657Z_095c9470 | MAPPO_WITH_SAFETY_FALLBACK, MAPPO_WITH_SAFETY_FALLBACK | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-04A --run-id 20261008T175551068657Z_095c9470 --gui --output-root "results\panel_validation\v2" |
| PV-04B | 20261009T063641943419Z_b034cc09 | SAFE_HOLD | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-04B --run-id 20261009T063641943419Z_b034cc09 --gui --output-root "results\panel_validation\v2" |
| PV-04B | 20261008T171632326120Z_c654aaee | SAFE_HOLD | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-04 --run-id 20261008T171632326120Z_c654aaee --gui --output-root "results\panel_validation\v1" |
| PV-05 | 20261009T063931819195Z_dee74d22 | SAFE_HOLD | & "C:\Users\Iresha Nethmini\Documents\R26-DS-017\.venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-05 --run-id 20261009T063931819195Z_dee74d22 --gui --output-root "results\panel_validation\v2" |
| PV-05 | 20261008T171854403586Z_81016bc6 | SAFE_HOLD | & "C:\R26-DS-017\venv\Scripts\python.exe" -B run_panel_validation.py --replay PV-05 --run-id 20261008T171854403586Z_81016bc6 --gui --output-root "results\panel_validation\v1" |

## Metric definitions

| Metric | Plain-English definition |
| --- | --- |
| TTT | Sum of scheduled-demand time until network exit or the actual evaluator stop; unfinished demand is censored, so early-stop exposure is not full-budget travel time. |
| approach_gap | Largest minus smallest N/E/S/W mean incoming wait; N/A unless all approaches are observed. No combined fairness score. |
| architecture | Runtime guard counts training, backward, optimizer, parameter changes, critic calls and centralized execution attempts; checks unchanged E5 and <=4 negotiators. |
| completion | Vehicles leaving the network / scheduled vehicles; unfinished trips remain visible. |
| fallback_rate | MAPPO epochs requiring safety fallback / MAPPO epochs; N/A with no MAPPO epochs. A fallback is not direct MAPPO success. |
| inversion | Fraction of physically conflicting, different-approach served pairs whose service order differs from arrival order; N/A without eligible served pairs. |
| safety | Observed simulator collisions and blocked-zone entry invariant violations. |
| scalability | Measured maximum live/moving vehicles, incoming queue depth per approach, and simultaneous negotiating participants. |
| throughput | Completed vehicles per observed simulated minute; compare alongside stop time and completion. |
| waiting | Observed time below the existing 0.5 m/s threshold on incoming lanes, including followers. Unfinished waits are lower bounds; unspawned demand is N/A. |

## PV-06 controlled message checks

| Fault | Permission | Attempted entry rejected | Passed |
| --- | --- | --- | --- |
| missing_required_coordination | SAFE_HOLD | True | True |
| stale_coordination | SAFE_HOLD | True | True |
| missing_clearance | SAFE_HOLD | True | True |
| stale_clearance | SAFE_HOLD | True | True |
