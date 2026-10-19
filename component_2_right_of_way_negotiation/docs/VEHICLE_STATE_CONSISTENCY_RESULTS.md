# Vehicle-state consistency: measured results

Bounded diagnostic evidence, not a frozen scientific evaluation. Physical controllers and the approved reconciliation protocol are unchanged.

| Scenario / fault | Sim seconds | Spawned | Completed | MAPPO calls | Mean wait s | Max wait s | Throughput/min | Collision / blocked-entry / unauthorized entry | Incorrect permission colors |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| congested_four_approach | 70.0 | 16 | 5 | 5 | 29.953 | 45.6 | 4.285714 | 0 / 0 / 0 | 0 |
| default_panel | 211.52 | 12 | 12 | 1 | 1.53 | 9.88 | 3.403933 | 0 / 0 / 0 | 0 |
| four_way_simultaneous | 50.36 | 4 | 4 | 0 | 0.71 | 2.84 | 4.765687 | 0 / 0 / 0 | 0 |
| mixed_manoeuvres | 58.84 | 4 | 4 | 0 | 3.83 | 8.56 | 4.078858 | 0 / 0 / 0 | 0 |
| multiple_left_turns | 55.4 | 3 | 3 | 3 | 3.813 | 7.92 | 3.249097 | 0 / 0 / 0 | 0 |
| regulatory_cycle | 56.96 | 4 | 4 | 1 | 3.62 | 9.44 | 4.213483 | 0 / 0 / 0 | 0 |
| rule_resolved_two | 50.6 | 2 | 2 | 0 | 0.18 | 0.36 | 2.371542 | 0 / 0 / 0 | 0 |
| four_way_simultaneous__contradictory_declaration | 45.0 | 4 | 0 | 0 | 22.5 | 22.84 | 0.0 | 0 / 0 / 0 | 0 |
| four_way_simultaneous__incorrect_declaration | 45.0 | 4 | 0 | 0 | 22.5 | 22.84 | 0.0 | 0 / 0 / 0 | 0 |
| four_way_simultaneous__invalid_declaration | 45.0 | 4 | 0 | 0 | 22.5 | 22.84 | 0.0 | 0 / 0 / 0 | 0 |
| four_way_simultaneous__missing_declaration | 45.0 | 4 | 0 | 0 | 22.5 | 22.84 | 0.0 | 0 / 0 / 0 | 0 |
| four_way_simultaneous__stale_declaration | 45.0 | 4 | 0 | 0 | 22.5 | 22.84 | 0.0 | 0 / 0 / 0 | 0 |
| rule_resolved_two__stale_commitment | 45.0 | 2 | 0 | 0 | 22.16 | 22.8 | 0.0 | 0 / 0 / 0 | 0 |

Four matched before/after cases have exactly identical measured physical outcomes, waiting/throughput metrics and original negotiation event records.
Dense before/after diagnostics both use a predeclared 70-second horizon. Their censored waiting and throughput values must not be compared directly with the preceding 360-second dense study.
Incorrect recent-event color overrides fell from 104 to zero sampled vehicle-frames in dense traffic, and 69 to zero in the regulatory-cycle case. These counts are sampled vehicle-frames, not independent episodes.
Red vehicles may still move toward their stop boundary. No PERMITTED sample retained a precedence speed constraint. Extended dense waiting remains explained by current dependencies/follower gates, not removed by a timer.
All original masked actor choices were checked for allowed action indices and correct participant IDs. The four-way scenario is rule-resolved; the separate regulatory-cycle run invokes MAPPO.
Historical files verified unchanged: 2334. E5 SHA-256: `2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
See VEHICLE_STATE_CONSISTENCY_REPORT.md for the precise visual contract, scope, test receipts, startup commands and remaining scientific limitation.
