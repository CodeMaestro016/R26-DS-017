# Final live correction: measured diagnostic results

These are new deterministic presentation diagnostics, not a replacement for the frozen final evaluation.

| Scenario / fault | Spawned | Completed | MAPPO | Fallback epochs | Mean wait s | Max wait s | Approach gap s | Throughput / min | All-active stopped max s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default_panel | 12 | 12 | 1 | 1 | 1.517 | 10.000 | 2.853 | 3.400 | 0.00 |
| four_way_simultaneous | 4 | 4 | 0 | 0 | 0.650 | 2.600 | 2.600 | 4.762 | 0.00 |
| mixed_manoeuvres | 4 | 4 | 0 | 0 | 3.830 | 8.720 | 8.720 | 4.071 | 0.00 |
| multiple_left_turns | 3 | 3 | 3 | 3 | 3.587 | 7.600 | N/A | 3.251 | 0.00 |
| regulatory_cycle | 4 | 4 | 1 | 1 | 3.510 | 9.240 | 9.240 | 4.208 | 0.00 |
| rule_resolved_two | 2 | 2 | 0 | 0 | 0.200 | 0.400 | N/A | 2.370 | 0.00 |
| congested_four_approach / 70 s | 16 | 7 | 10 | 10 | 21.197 | 42.440 | 5.630 | 6.000 | 0.00 |
| congested_four_approach / 360 s budget | 16 | 16 | 11 | 11 | 23.413 | 52.800 | 9.910 | 8.322 | 0.00 |
| regulatory_cycle / contradictory_declaration | 4 | 0 | 0 | 0 | 22.490 | 22.800 | 1.240 | 0.000 | 21.44 |
| regulatory_cycle / incorrect_declaration | 4 | 0 | 0 | 0 | 22.490 | 22.800 | 1.240 | 0.000 | 21.44 |
| regulatory_cycle / invalid_declaration | 4 | 0 | 0 | 0 | 22.490 | 22.800 | 1.240 | 0.000 | 21.44 |
| regulatory_cycle / missing_declaration | 4 | 0 | 0 | 0 | 22.490 | 22.800 | 1.240 | 0.000 | 21.44 |
| regulatory_cycle / stale_commitment | 4 | 1 | 1 | 0 | 16.790 | 22.800 | 22.800 | 1.333 | 0.32 |
| regulatory_cycle / stale_declaration | 4 | 0 | 0 | 0 | 22.490 | 22.800 | 1.240 | 0.000 | 21.44 |
| regulatory_cycle / mandatory_constraint_cycle | 4 | 1 | 1 | 0 | 16.790 | 22.800 | 22.800 | 1.333 | 0.32 |

All rows: zero observed collisions, blocked-zone violations and unauthorized entries.
The mandatory-cycle row is injected contradictory constraint evidence, not a newly invented legal movement scenario.
Stationary duration is sampled at the existing 0.16-second publisher interval. The unchanged `deadlock_observed` metric flags any individual incoming vehicle stopped for 15 seconds; it can be true in a completed, progressing episode.

| Dense budget | Completion before → after | Mean wait before → after s | Max wait before → after s | Approach gap before → after s | Throughput before → after / min |
|---|---|---|---|---|---|
| 70 s | 5/16 → 7/16 | 29.953 → 21.197 | 45.600 → 42.440 | 8.250 → 5.630 | 4.286 → 6.000 |
| 360 s | 5/16 → 16/16 | 229.327 → 23.413 | 335.600 → 52.800 | 80.750 → 9.910 | 0.833 → 8.322 |

Integrity: 2334 historical files unchanged; 147 protected source/model files unchanged. The four listed source differences include the earlier approved revisions.
Synchronized actual-simulator/publisher/HTTP/SVG frames: 105. Local Chromium additionally verified 186 actual DOM frames, including 124 matching HTTP/DOM frames.
Dense full run per-approach mean waits: {"N": 18.589999999999996, "E": 22.99, "S": 28.5, "W": 23.57}
Detailed metrics, sampled transitions, per-event MAPPO evidence and timestamps: `results/final_live_correction/20261016/verification.json`.
