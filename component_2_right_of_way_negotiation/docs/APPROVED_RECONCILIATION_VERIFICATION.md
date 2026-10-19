# Approved reconciliation: measured verification

Diagnostic/presentation evidence only. Original frozen scientific results are unchanged.

| Scenario / injected fault | Scheduled | Spawned | Completed | Completion % | MAPPO | Mean wait s | Max wait s | Throughput/min | Collisions | Violations | Wall s | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| congested_four_approach | 16 | 16 | 5 | 31.25 | 5 | 229.327 | 335.6 | 0.833333 | 0 | 0 | 972.25 | SAFE_DEGRADATION |
| default_panel | 12 | 12 | 12 | 100.0 | 1 | 1.53 | 9.88 | 3.403933 | 0 | 0 | 112.26 | PASS |
| four_way_simultaneous | 4 | 4 | 4 | 100.0 | 0 | 0.71 | 2.84 | 4.765687 | 0 | 0 | 18.16 | PASS |
| mixed_manoeuvres | 4 | 4 | 4 | 100.0 | 0 | 3.83 | 8.56 | 4.078858 | 0 | 0 | 24.04 | PASS |
| multiple_left_turns | 3 | 3 | 3 | 100.0 | 3 | 3.813 | 7.92 | 3.249097 | 0 | 0 | 19.57 | PASS |
| regulatory_cycle | 4 | 4 | 4 | 100.0 | 1 | 3.62 | 9.44 | 4.213483 | 0 | 0 | 21.57 | PASS |
| rule_resolved_two | 2 | 2 | 2 | 100.0 | 0 | 0.18 | 0.36 | 2.371542 | 0 | 0 | 12.56 | PASS |
| yield_negotiation_demo | 6 | 6 | 6 | 100.0 | 1 | 2.16 | 9.88 | 3.324714 | 0 | 0 | 38.16 | PASS |
| four_way_simultaneous__contradictory | 4 | 4 | 0 | 0.0 | 0 | 22.5 | 22.84 | 0.0 | 0 | 0 | 26.78 | SAFE_DEGRADATION |
| four_way_simultaneous__incorrect | 4 | 4 | 0 | 0.0 | 0 | 22.5 | 22.84 | 0.0 | 0 | 0 | 29.75 | SAFE_DEGRADATION |
| four_way_simultaneous__invalid | 4 | 4 | 0 | 0.0 | 0 | 22.5 | 22.84 | 0.0 | 0 | 0 | 31.79 | SAFE_DEGRADATION |
| four_way_simultaneous__missing | 4 | 4 | 0 | 0.0 | 0 | 22.5 | 22.84 | 0.0 | 0 | 0 | 34.18 | SAFE_DEGRADATION |
| four_way_simultaneous__stale | 4 | 4 | 0 | 0.0 | 0 | 22.5 | 22.84 | 0.0 | 0 | 0 | 33.43 | SAFE_DEGRADATION |

Initial full active run: **965 passed, 4 errors in 820.81s (0:13:40)**. All four setup errors were the version-specific assumption that an incomplete run completes zero trips.
After making that fixture expectation version-aware, the real affected module was rerun: **18 passed, 2 xfailed in 483.59s (0:08:03)**. All safety/integrity checks and original strict completion assertions remain active.
Combined final coverage: **967 passed, two existing strict xfails** across the full run and affected-module rerun; a second entire full-suite execution was not performed.
Historical files verified unchanged: **2334**. Unchanged protected source/model assets: **147/151**; four source paths changed across telemetry and this approved task.
E5 SHA-256: `2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

All original MAPPO action diagnostics above were checked for participant identity, valid selected action indices and permitted boolean masks. Actor dimensions/classes and trained weights remain unchanged.
Every passing run completed its actual scheduled vehicles with zero observed collisions and violations. Fault cases intentionally safe-hold; their SAFE_DEGRADATION is not a discharge PASS.
Dense traffic remains incomplete because mandatory obligations and the existing pair fallback create a later cycle. See APPROVED_RECONCILIATION_IMPLEMENTATION_REPORT.md for exact dependencies and the additional approval boundary.

Website: actual four-way completion, dense progress/MAPPO, same-instance restart, duplicate refusal, cooperative owned-process stop and six HTTP 200 routes verified. Interactive browser verification unavailable (no connected browser).

Exact commands and output roots are retained in tools/diagnose_live_deadlock.py, tools/probe_reconciled_showcase.py and the implementation report. No formal evaluation matrix, training or package rebuild was performed.
