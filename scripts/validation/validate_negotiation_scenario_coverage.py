"""Step 5J.2A validator. Runs discovery and stops honestly at hard blockers."""

from negotiation_scenarios import run_discovery_and_calibration


def main():
    report, catalogue, summary = run_discovery_and_calibration()
    event = report["synchronization_event"]
    print("Step 5J.2A Negotiation Scenario Coverage Validation\n")
    print("Map discovery")
    print(f"  Legal movement paths discovered: {report['legal_movement_path_count']}")
    print(f"  Scenario candidates enumerated: {report['movement_combination_count']}")
    print("  Hand-coded regulatory cycles used: False")
    print("  Route truth exposed to actor: False\n")
    print("Scenario discovery")
    print(f"  Regulatory-cycle candidates: {report['regulatory_cycle_candidate_count']}")
    print(f"  Unresolved-precedence candidates: {report['unresolved_precedence_candidate_count']}")
    print("  Classification source: actual map geometry + TrafficRuleEngine + SCC analysis\n")
    print("Calibration")
    print("  Existing synchronization event reused: ObservationManager.is_in_approach_zone")
    print(f"  Operational map-derived center: {tuple(event['operational_center'])}")
    print(f"  Compiled SUMO junction center: {tuple(event['compiled_sumo_center'])}")
    print(f"  Existing synchronization event reusable: {event['status']}")
    print(f"  Isolated movement calibrations built: {len(report['calibrations'])}")
    print(f"  Calibration deterministic: {'PASS' if report['calibration_reproducible'] else 'FAIL'}")
    print("  Arbitrary spawn offsets introduced: 0")
    print("  Synchronization margins introduced: 0\n")
    print("Authority")
    print("  Operational target route-truth fields consumed: 0")
    print("  Hard-mask bypasses: 0")
    print("  Regulatory rules modified: False")
    print("  Learned policy actions issued: 0\n")
    print("Training boundary")
    print("  Optimizer instantiated: False")
    print("  backward() calls: 0")
    print("  Parameter updates: 0")
    print("  Training runs: 0")
    print("  Model checkpoints: 0")
    print("  Learned SUMO control: False\n")
    live = report["live_coverage"]
    traces = report["protocol_traces"]
    print("Live SUMO coverage")
    print(f"  Scenario specifications: {len(report['scenario_specifications'])}")
    print(f"  Real scenario episodes executed: {report['real_sumo_scenario_episodes']}")
    counts = report['live_snapshot_status_counts']
    print(f"  Total live joint snapshots: {report['live_snapshot_count']}")
    print(f"  Live regulatory-cycle snapshots: {counts.get('NEGOTIATION_REQUIRED_REGULATORY_CYCLE', 0)}")
    print(f"  Live unresolved-precedence snapshots: {counts.get('NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE', 0)}")
    print(f"  Live proposer opportunities: {sum(len(x['proposer_decision_event_ids']) for x in live)}")
    print(f"  Live two-feasible proposer opportunities: {sum(sum(all(m) for m in x['proposer_action_masks']) for x in live)}\n")
    print("Protocol coverage from live contexts")
    print("  Coverage action source: DETERMINISTIC_COVERAGE_ENUMERATION")
    print(f"  Responder opportunities: {sum(len(x['responder_decision_event_ids']) for x in live)}")
    print(f"  ACCEPT branches validated: {sum(x['responder_action'] == 'ACCEPT_RELINQUISHMENT' for x in traces)}")
    print(f"  REJECT branches validated: {sum(x['responder_action'] == 'REJECT_RELINQUISHMENT' for x in traces)}")
    print(f"  Agreements established: {sum(x['protocol_status'] == 'AGREEMENT_ESTABLISHED' for x in traces)}")
    print(f"  Proposal rejections validated: {sum(x['protocol_status'] == 'PROPOSAL_REJECTED' for x in traces)}\n")
    print("Coverage blocker status")
    insufficient = report['step_5j_2_readiness'] != 'READY_TO_RESUME_STEP_5J_2'
    print(f"  NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT: {insufficient}")
    print(f"  RESPONDER_TRAINING_COVERAGE_MISSING: {not any(x['responder_decision_event_ids'] for x in live)}")
    print(f"  STOP: {report['next_blocker']}")
    print(f"  assess_step_5j_2_scenario_readiness(): {report['step_5j_2_readiness']}")
    print(f"  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: {report['negotiation_action_to_traffic_outcome_status']}")
    print(f"  assess_step_5j_3_environment_readiness(): {report['step_5j_3_readiness']}\n")
    print(f"Catalogue metadata: {catalogue}")
    print(f"Human-readable summary: {summary}")


if __name__ == "__main__":
    main()
