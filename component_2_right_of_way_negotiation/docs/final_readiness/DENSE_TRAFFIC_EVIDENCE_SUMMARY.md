# Dense traffic evidence — 16 October 2026

Historical presentation success, scientific targeted validation and the extended
final matrix are different evidence families. Every available historical
congested artifact found by the audit is listed; some are duplicate summaries
of the same episode and are not independent replications. N/A means the record
does not supply that metric. Older 16/16 successes do not guarantee current
behavior; the preserved later qualitative latest record is 0/16 and INCOMPLETE.
New short lifecycle checks are USER_STOPPED, not performance experiments.

| Scenario | Purpose | Scheduled | Spawned | Completed | Completion % | Peak active | Peak moving | MAPPO epochs | Collisions | Blocked violations | Execution mode | Status | Evidence path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY | COMPLETED | results/panel_demo/congested_ego_local_verification/latest_panel_demo.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | N/A | COMPLETED | results/panel_demo/congested_ego_local_verification/presentation_runs/run_20261005T161504_498435Z.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | N/A | COMPLETED | results/panel_demo/congested_ego_local_verification/presentation_runs/run_20261005T162245_486707Z.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY | COMPLETED | results/panel_demo/decentralized_congested_check/latest_panel_demo.json |
| congested_four_approach | Qualitative historical presentation | 16 | N/A | 16 | 100.0 | N/A | N/A | 6 | 0 | 0 | N/A | COMPLETED | results/panel_demo/decentralized_congested_check/presentation_runs/run_20261005T155920_021037Z.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 0 | 0.0 | 16 | 16 | 0 | 0 | 0 | DETERMINISTIC_MASKED_ARGMAX_OF_SELECTED_E5_PRESENTATION_ONLY | INCOMPLETE | results/panel_demo/latest_panel_demo.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | N/A | COMPLETED | results/panel_demo/presentation_runs/run_0403a64d70f5480f92e9ef1a8b2d1038.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 0 | 0.0 | 16 | 16 | 0 | 0 | 0 | N/A | INCOMPLETE | results/panel_demo/presentation_runs/run_2a593ebebc6a491e925ca400332cc00e.json |
| congested_four_approach | Qualitative historical presentation | 16 | 16 | 16 | 100.0 | 16 | 16 | 6 | 0 | 0 | N/A | COMPLETED | results/panel_demo/presentation_runs/run_c969e7879b574995987d31da7f4cbb54.json |
| congested_four_approach | Targeted scientific v1 | 16 | 16 | 0 | 0.0 | 16 | 16 | 0 | 0 | 0 | Seeded stochastic; ego-local | SAFE_DEGRADATION / DEADLOCK_CONFIRMED | results/panel_validation/v1/runs/20261008T171632326120Z_c654aaee/result.json |
| nominal_dense_continuous_16 | Targeted scientific v2 | 16 | 16 | 1 | 6.25 | 16 | 16 | 2 | 0 | 0 | Seeded stochastic; ego-local | SAFE_DEGRADATION / HARD_TIME_BUDGET | results/panel_validation/v2/runs/20261008T175551068657Z_095c9470/result.json |
| congested_four_approach | Targeted scientific v2 | 16 | 16 | 0 | 0.0 | 16 | 16 | 0 | 0 | 0 | Seeded stochastic; ego-local | SAFE_DEGRADATION / DEADLOCK_CONFIRMED | results/panel_validation/v2/runs/20261009T063641943419Z_b034cc09/result.json |


## Scientific interpretation

PV-04A nominal scientific evidence records 1/16 completion (6.25%), two MAPPO
invocations, two safety-fallback outcomes, zero collisions/blocked-zone violations
and a hard 180-second timeout. PV-04B critical records 0/16, zero MAPPO calls,
confirmed deadlock and zero observed safety violations. The V1 critical result
remains separately preserved. These are severe liveness limitations, not PASS.

Peak active/moving counts of 16 and queues of up to four per approach verify
traffic beyond four vehicles. Maximum encoded negotiation participation remains
four physical queue heads; native following does not mean every traffic vehicle
is a simultaneous MAPPO node. The congested schedule contains four vehicles
per approach and all twelve legal movement classes, verified from its existing
catalog and audit. No route, schedule, spacing or budget was changed here.

The existing dense/repair source traces document COMMUNICATED_PRECEDENCE_DISAGREEMENT
and held queue heads under incompatible local intention premises, while mandatory
claim conflicts remain outside MAPPO authorization. Nominal trace decisions
later show unresolved local precedence/zone obligations. This supports observed
safe holding and stalled discharge, not a proof that every underlying forecast
was correct. Generic MISSING_OR_STALE_LOCAL_COORDINATION labels alone do not
prove old messages. Consult PANEL_DENSE_V2_AUDIT.md and REPAIR_V2_AUDIT.md for the
timestamped analyses; no new causal claim is inferred merely from counts.

Zero observed collisions/violations is bounded safety evidence, not universal
safety or a liveness guarantee. No-completion trip statistics remain N/A;
unfinished waiting/exposure statistics are censored. Fairness is limited by
served-pair availability and incomplete discharge, not established by a small
approach-wait gap. V1 and V2, presentation argmax and scientific stochastic
sampling, and different reviewed runtime versions must not be pooled as one
performance study. The incomplete 34/165 V1 matrix establishes no universal
congestion or intersection-generalization claim.
