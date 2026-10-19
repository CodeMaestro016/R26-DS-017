# Paper tables

SMOKE_NOT_FINAL

| Scenario | Method | n | Classifications | TTT (vehicle s) | Travel mean (s) | Throughput (veh/min) | Completion | Wait mean (s) | Wait p95 (s) | Wait max (s) | Approach gap (s) | FCFS inversion rate | Max live | Max negotiators |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rule_resolved_two | PROPOSED_MAPPO | 1.000 | {'PASS': 1} | 93.520 | 46.760 | 2.459 | 1.000 | 0.000 | 0.000 | 0.000 | N/A | 1.000 | 2.000 | 2.000 |
| rule_resolved_two | RULE_PLUS_FCFS | 1.000 | {'PASS': 1} | 93.520 | 46.760 | 2.459 | 1.000 | 0.000 | 0.000 | 0.000 | N/A | 1.000 | 2.000 | 2.000 |
| rule_resolved_two | RULES_ONLY | 1.000 | {'PASS': 1} | 93.520 | 46.760 | 2.459 | 1.000 | 0.000 | 0.000 | 0.000 | N/A | 1.000 | 2.000 | 2.000 |
| regulatory_cycle | PROPOSED_MAPPO | 1.000 | {'PASS': 1} | 194.720 | 48.680 | 4.591 | 1.000 | 1.680 | 4.016 | 4.400 | 4.400 | 0.333 | 4.000 | 4.000 |
| regulatory_cycle | RULE_PLUS_FCFS | 1.000 | {'PASS': 1} | 195.720 | 48.930 | 4.491 | 1.000 | 2.030 | 5.330 | 5.960 | 5.960 | 0.333 | 4.000 | 4.000 |
| regulatory_cycle | RULES_ONLY | 1.000 | {'SAFE_DEGRADATION': 1} | 360.000 | N/A | 0.000 | 0.000 | 67.830 | 67.840 | 67.840 | 0.040 | N/A | 4.000 | 4.000 |
| normal | PROPOSED_MAPPO | 1.000 | {'SAFE_DEGRADATION': 1} | 712.000 | N/A | 0.000 | 0.000 | 64.855 | 67.840 | 67.840 | 2.820 | N/A | 8.000 | 4.000 |
| normal | RULE_PLUS_FCFS | 1.000 | {'SAFE_DEGRADATION': 1} | 712.000 | N/A | 0.000 | 0.000 | 64.855 | 67.840 | 67.840 | 2.820 | N/A | 8.000 | 4.000 |
| normal | RULES_ONLY | 1.000 | {'SAFE_DEGRADATION': 1} | 712.000 | N/A | 0.000 | 0.000 | 64.855 | 67.840 | 67.840 | 2.820 | N/A | 8.000 | 4.000 |

## Per-approach mean stopped wait (s)

| Scenario | Method | N | E | S | W |
| --- | --- | --- | --- | --- | --- |
| rule_resolved_two | PROPOSED_MAPPO | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | 0.480 | 1.840 | 0.000 | 4.400 |
| regulatory_cycle | RULE_PLUS_FCFS | 0.400 | 1.760 | 0.000 | 5.960 |
| regulatory_cycle | RULES_ONLY | 67.840 | 67.840 | 67.800 | 67.840 |
| normal | PROPOSED_MAPPO | 64.800 | 65.980 | 65.480 | 63.160 |
| normal | RULE_PLUS_FCFS | 64.800 | 65.980 | 65.480 | 63.160 |
| normal | RULES_ONLY | 64.800 | 65.980 | 65.480 | 63.160 |

## All statistics (across per-episode values)

| Scenario | Method | Metric | n | Mean | Median | Sample SD | 95% CI of mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rule_resolved_two | PROPOSED_MAPPO | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | total_team_travel_time_seconds | 1.000 | 93.520 | 93.520 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mean_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | median_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | p95_travel_time_seconds | 1.000 | 48.596 | 48.596 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | maximum_travel_time_seconds | 1.000 | 48.800 | 48.800 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | throughput_vehicles_per_minute | 1.000 | 2.459 | 2.459 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | completion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mean_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | median_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | p95_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | maximum_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | approach_waiting_time_gap_seconds | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | conflicting_pair_fcfs_inversion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | maximum_simultaneous_active_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | maximum_simultaneously_moving_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | maximum_negotiation_participants | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | rule_resolved_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | safe_hold_activations | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | ego_execution_mean_ms | 1.000 | 0.182 | 0.182 | N/A | N/A |
| rule_resolved_two | PROPOSED_MAPPO | ego_execution_p95_ms | 1.000 | 0.633 | 0.633 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | total_team_travel_time_seconds | 1.000 | 93.520 | 93.520 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mean_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | median_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | p95_travel_time_seconds | 1.000 | 48.596 | 48.596 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_travel_time_seconds | 1.000 | 48.800 | 48.800 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | throughput_vehicles_per_minute | 1.000 | 2.459 | 2.459 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | completion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mean_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | median_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | p95_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | conflicting_pair_fcfs_inversion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_simultaneous_active_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_simultaneously_moving_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_negotiation_participants | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | rule_resolved_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | safe_hold_activations | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | ego_execution_mean_ms | 1.000 | 0.191 | 0.191 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | ego_execution_p95_ms | 1.000 | 0.674 | 0.674 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | total_team_travel_time_seconds | 1.000 | 93.520 | 93.520 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mean_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | median_travel_time_seconds | 1.000 | 46.760 | 46.760 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | p95_travel_time_seconds | 1.000 | 48.596 | 48.596 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | maximum_travel_time_seconds | 1.000 | 48.800 | 48.800 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | throughput_vehicles_per_minute | 1.000 | 2.459 | 2.459 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | completion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mean_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | median_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | p95_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | maximum_waiting_time_seconds | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | approach_waiting_time_gap_seconds | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | conflicting_pair_fcfs_inversion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | maximum_simultaneous_active_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | maximum_simultaneously_moving_vehicles | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | maximum_negotiation_participants | 1.000 | 2.000 | 2.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | rule_resolved_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | safe_hold_activations | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| rule_resolved_two | RULES_ONLY | ego_execution_mean_ms | 1.000 | 0.198 | 0.198 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | ego_execution_p95_ms | 1.000 | 0.671 | 0.671 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | total_team_travel_time_seconds | 1.000 | 194.720 | 194.720 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mean_travel_time_seconds | 1.000 | 48.680 | 48.680 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | median_travel_time_seconds | 1.000 | 48.960 | 48.960 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | p95_travel_time_seconds | 1.000 | 51.926 | 51.926 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | maximum_travel_time_seconds | 1.000 | 52.280 | 52.280 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | throughput_vehicles_per_minute | 1.000 | 4.591 | 4.591 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | completion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mean_waiting_time_seconds | 1.000 | 1.680 | 1.680 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | median_waiting_time_seconds | 1.000 | 1.160 | 1.160 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | p95_waiting_time_seconds | 1.000 | 4.016 | 4.016 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | maximum_waiting_time_seconds | 1.000 | 4.400 | 4.400 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | approach_waiting_time_gap_seconds | 1.000 | 4.400 | 4.400 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | conflicting_pair_fcfs_inversion_rate | 1.000 | 0.333 | 0.333 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | maximum_simultaneous_active_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | maximum_simultaneously_moving_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | negotiation_events | 1.000 | 3.000 | 3.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_decision_epochs | 1.000 | 2.000 | 2.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | rule_resolved_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | safe_hold_activations | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_inference_mean_ms | 1.000 | 13.946 | 13.946 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_inference_median_ms | 1.000 | 13.946 | 13.946 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_inference_p95_ms | 1.000 | 18.993 | 18.993 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_inference_maximum_ms | 1.000 | 19.553 | 19.553 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | mappo_inference_fraction_exceeding_40ms | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | ego_execution_mean_ms | 1.000 | 0.214 | 0.214 | N/A | N/A |
| regulatory_cycle | PROPOSED_MAPPO | ego_execution_p95_ms | 1.000 | 0.758 | 0.758 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | total_team_travel_time_seconds | 1.000 | 195.720 | 195.720 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mean_travel_time_seconds | 1.000 | 48.930 | 48.930 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | median_travel_time_seconds | 1.000 | 48.880 | 48.880 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | p95_travel_time_seconds | 1.000 | 52.900 | 52.900 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_travel_time_seconds | 1.000 | 53.440 | 53.440 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | throughput_vehicles_per_minute | 1.000 | 4.491 | 4.491 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | completion_rate | 1.000 | 1.000 | 1.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mean_waiting_time_seconds | 1.000 | 2.030 | 2.030 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | median_waiting_time_seconds | 1.000 | 1.080 | 1.080 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | p95_waiting_time_seconds | 1.000 | 5.330 | 5.330 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_waiting_time_seconds | 1.000 | 5.960 | 5.960 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds | 1.000 | 5.960 | 5.960 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | conflicting_pair_fcfs_inversion_rate | 1.000 | 0.333 | 0.333 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_simultaneous_active_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_simultaneously_moving_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | negotiation_events | 1.000 | 3.000 | 3.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | rule_resolved_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | safe_hold_activations | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | ego_execution_mean_ms | 1.000 | 0.264 | 0.264 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | ego_execution_p95_ms | 1.000 | 1.008 | 1.008 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | total_team_travel_time_seconds | 1.000 | 360.000 | 360.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mean_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | median_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | p95_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | throughput_vehicles_per_minute | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | completion_rate | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mean_waiting_time_seconds | 1.000 | 67.830 | 67.830 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | median_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | p95_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | approach_waiting_time_gap_seconds | 1.000 | 0.040 | 0.040 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | conflicting_pair_fcfs_inversion_rate | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_simultaneous_active_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_simultaneously_moving_vehicles | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | rule_resolved_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | safe_hold_activations | 1.000 | 4.000 | 4.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| regulatory_cycle | RULES_ONLY | ego_execution_mean_ms | 1.000 | 0.361 | 0.361 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | ego_execution_p95_ms | 1.000 | 0.703 | 0.703 | N/A | N/A |
| normal | PROPOSED_MAPPO | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | total_team_travel_time_seconds | 1.000 | 712.000 | 712.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | mean_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | median_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | p95_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | maximum_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | throughput_vehicles_per_minute | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | completion_rate | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | mean_waiting_time_seconds | 1.000 | 64.855 | 64.855 | N/A | N/A |
| normal | PROPOSED_MAPPO | median_waiting_time_seconds | 1.000 | 65.960 | 65.960 | N/A | N/A |
| normal | PROPOSED_MAPPO | p95_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | PROPOSED_MAPPO | maximum_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | PROPOSED_MAPPO | approach_waiting_time_gap_seconds | 1.000 | 2.820 | 2.820 | N/A | N/A |
| normal | PROPOSED_MAPPO | conflicting_pair_fcfs_inversion_rate | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | maximum_simultaneous_active_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | maximum_simultaneously_moving_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | rule_resolved_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | safe_hold_activations | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | PROPOSED_MAPPO | ego_execution_mean_ms | 1.000 | 0.221 | 0.221 | N/A | N/A |
| normal | PROPOSED_MAPPO | ego_execution_p95_ms | 1.000 | 0.638 | 0.638 | N/A | N/A |
| normal | RULE_PLUS_FCFS | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | total_team_travel_time_seconds | 1.000 | 712.000 | 712.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | mean_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | median_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | p95_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | throughput_vehicles_per_minute | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | completion_rate | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | mean_waiting_time_seconds | 1.000 | 64.855 | 64.855 | N/A | N/A |
| normal | RULE_PLUS_FCFS | median_waiting_time_seconds | 1.000 | 65.960 | 65.960 | N/A | N/A |
| normal | RULE_PLUS_FCFS | p95_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds | 1.000 | 2.820 | 2.820 | N/A | N/A |
| normal | RULE_PLUS_FCFS | conflicting_pair_fcfs_inversion_rate | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_simultaneous_active_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_simultaneously_moving_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | rule_resolved_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | safe_hold_activations | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULE_PLUS_FCFS | ego_execution_mean_ms | 1.000 | 0.222 | 0.222 | N/A | N/A |
| normal | RULE_PLUS_FCFS | ego_execution_p95_ms | 1.000 | 0.640 | 0.640 | N/A | N/A |
| normal | RULES_ONLY | collision_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | blocked_zone_violation_count | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | unsafe_episode | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | total_team_travel_time_seconds | 1.000 | 712.000 | 712.000 | N/A | N/A |
| normal | RULES_ONLY | mean_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | median_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | p95_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | maximum_travel_time_seconds | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | throughput_vehicles_per_minute | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | completion_rate | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | mean_waiting_time_seconds | 1.000 | 64.855 | 64.855 | N/A | N/A |
| normal | RULES_ONLY | median_waiting_time_seconds | 1.000 | 65.960 | 65.960 | N/A | N/A |
| normal | RULES_ONLY | p95_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | RULES_ONLY | maximum_waiting_time_seconds | 1.000 | 67.840 | 67.840 | N/A | N/A |
| normal | RULES_ONLY | approach_waiting_time_gap_seconds | 1.000 | 2.820 | 2.820 | N/A | N/A |
| normal | RULES_ONLY | conflicting_pair_fcfs_inversion_rate | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | maximum_simultaneous_active_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | RULES_ONLY | maximum_simultaneously_moving_vehicles | 1.000 | 8.000 | 8.000 | N/A | N/A |
| normal | RULES_ONLY | maximum_negotiation_participants | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | RULES_ONLY | negotiation_events | 1.000 | 1.000 | 1.000 | N/A | N/A |
| normal | RULES_ONLY | mappo_decision_epochs | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | rule_resolved_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | safe_hold_activations | 1.000 | 4.000 | 4.000 | N/A | N/A |
| normal | RULES_ONLY | native_emergency_braking_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | native_emergency_stop_events | 1.000 | 0.000 | 0.000 | N/A | N/A |
| normal | RULES_ONLY | mappo_inference_mean_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | mappo_inference_median_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | mappo_inference_p95_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | mappo_inference_maximum_ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | mappo_inference_fraction_exceeding_40ms | 0.000 | N/A | N/A | N/A | N/A |
| normal | RULES_ONLY | ego_execution_mean_ms | 1.000 | 0.225 | 0.225 | N/A | N/A |
| normal | RULES_ONLY | ego_execution_p95_ms | 1.000 | 0.648 | 0.648 | N/A | N/A |

## Paired differences (proposed minus baseline)

| Scenario | Baseline | Metric | Paired n | Mean difference | 95% CI |
| --- | --- | --- | --- | --- | --- |
| rule_resolved_two | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 1.000 | 0.000 | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 1.000 | 0.000 | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | total_team_travel_time_seconds (%) | 1.000 | 0.000 | N/A |
| rule_resolved_two | RULES_ONLY | throughput_vehicles_per_minute (%) | 1.000 | 0.000 | N/A |
| rule_resolved_two | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| rule_resolved_two | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 1.000 | -0.511 | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 1.000 | 2.219 | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 1.000 | -26.174 | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 1.000 | -26.174 | N/A |
| regulatory_cycle | RULES_ONLY | total_team_travel_time_seconds (%) | 1.000 | -45.911 | N/A |
| regulatory_cycle | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| regulatory_cycle | RULES_ONLY | maximum_waiting_time_seconds (%) | 1.000 | -93.514 | N/A |
| regulatory_cycle | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 1.000 | 10900.000 | N/A |
| multiple_left_turns | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| multiple_left_turns | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 1.000 | 0.000 | N/A |
| normal | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 1.000 | 0.000 | N/A |
| normal | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 1.000 | 0.000 | N/A |
| normal | RULES_ONLY | total_team_travel_time_seconds (%) | 1.000 | 0.000 | N/A |
| normal | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| normal | RULES_ONLY | maximum_waiting_time_seconds (%) | 1.000 | 0.000 | N/A |
| normal | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 1.000 | 0.000 | N/A |
| congested | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| congested | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| congested | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| congested | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| congested | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| congested | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| congested | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| congested | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| dense | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| dense | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| dense | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| dense | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| dense | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| dense | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| dense | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| dense | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| stress | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| stress | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| stress | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| stress | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| stress | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| stress | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| stress | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| stress | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULE_PLUS_FCFS | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULE_PLUS_FCFS | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| extreme_stress | RULE_PLUS_FCFS | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULE_PLUS_FCFS | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULES_ONLY | total_team_travel_time_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULES_ONLY | throughput_vehicles_per_minute (%) | 0.000 | N/A | N/A |
| extreme_stress | RULES_ONLY | maximum_waiting_time_seconds (%) | 0.000 | N/A | N/A |
| extreme_stress | RULES_ONLY | approach_waiting_time_gap_seconds (%) | 0.000 | N/A | N/A |
| rule_resolved_two | RULE_PLUS_FCFS | completion (percentage points) | 1.000 | 0.000 | N/A |
| rule_resolved_two | RULES_ONLY | completion (percentage points) | 1.000 | 0.000 | N/A |
| regulatory_cycle | RULE_PLUS_FCFS | completion (percentage points) | 1.000 | 0.000 | N/A |
| regulatory_cycle | RULES_ONLY | completion (percentage points) | 1.000 | 100.000 | N/A |
| multiple_left_turns | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| multiple_left_turns | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| mixed_manoeuvres | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| four_way_simultaneous | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| normal | RULE_PLUS_FCFS | completion (percentage points) | 1.000 | 0.000 | N/A |
| normal | RULES_ONLY | completion (percentage points) | 1.000 | 0.000 | N/A |
| congested | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| congested | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| dense | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| dense | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| stress | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| stress | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |
| extreme_stress | RULE_PLUS_FCFS | completion (percentage points) | 0.000 | N/A | N/A |
| extreme_stress | RULES_ONLY | completion (percentage points) | 0.000 | N/A | N/A |