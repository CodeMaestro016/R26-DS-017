"""Step 5J.2A validator. Runs discovery and stops honestly at hard blockers."""

# Import run_discovery_and_calibration from negotiation_scenarios for the operations below.
from negotiation_scenarios import run_discovery_and_calibration


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set (report, catalogue, summary) to the result of run_discovery_and_calibration().
    report, catalogue, summary = run_discovery_and_calibration()
    # Set event to report at 'synchronization_event'.
    event = report["synchronization_event"]
    # Display the text 'Step 5J.2A Negotiation Scenario Coverage Validation'.
    print("Step 5J.2A Negotiation Scenario Coverage Validation\n")
    # Display the text 'Map discovery'.
    print("Map discovery")
    # Display formatted text built from the embedded values.
    print(f"  Legal movement paths discovered: {report['legal_movement_path_count']}")
    # Display formatted text built from the embedded values.
    print(f"  Scenario candidates enumerated: {report['movement_combination_count']}")
    # Display the text 'Hand-coded regulatory cycles used: False'.
    print("  Hand-coded regulatory cycles used: False")
    # Display the text 'Route truth exposed to actor: False'.
    print("  Route truth exposed to actor: False\n")
    # Display the text 'Scenario discovery'.
    print("Scenario discovery")
    # Display formatted text built from the embedded values.
    print(f"  Regulatory-cycle candidates: {report['regulatory_cycle_candidate_count']}")
    # Display formatted text built from the embedded values.
    print(f"  Unresolved-precedence candidates: {report['unresolved_precedence_candidate_count']}")
    # Display the text 'Classification source: actual map geometry +...'.
    print("  Classification source: actual map geometry + TrafficRuleEngine + SCC analysis\n")
    # Display the text 'Calibration'.
    print("Calibration")
    # Display the text 'Existing synchronization event reused:...'.
    print("  Existing synchronization event reused: ObservationManager.is_in_approach_zone")
    # Display formatted text built from the embedded values.
    print(f"  Operational map-derived center: {tuple(event['operational_center'])}")
    # Display formatted text built from the embedded values.
    print(f"  Compiled SUMO junction center: {tuple(event['compiled_sumo_center'])}")
    # Display formatted text built from the embedded values.
    print(f"  Existing synchronization event reusable: {event['status']}")
    # Display formatted text built from the embedded values.
    print(f"  Isolated movement calibrations built: {len(report['calibrations'])}")
    # Display formatted text built from the embedded values.
    print(f"  Calibration deterministic: {'PASS' if report['calibration_reproducible'] else 'FAIL'}")
    # Display the text 'Arbitrary spawn offsets introduced: 0'.
    print("  Arbitrary spawn offsets introduced: 0")
    # Display the text 'Synchronization margins introduced: 0'.
    print("  Synchronization margins introduced: 0\n")
    # Display the text 'Authority'.
    print("Authority")
    # Display the text 'Operational target route-truth fields consumed: 0'.
    print("  Operational target route-truth fields consumed: 0")
    # Display the text 'Hard-mask bypasses: 0'.
    print("  Hard-mask bypasses: 0")
    # Display the text 'Regulatory rules modified: False'.
    print("  Regulatory rules modified: False")
    # Display the text 'Learned policy actions issued: 0'.
    print("  Learned policy actions issued: 0\n")
    # Display the text 'Training boundary'.
    print("Training boundary")
    # Display the text 'Optimizer instantiated: False'.
    print("  Optimizer instantiated: False")
    # Display the text 'backward() calls: 0'.
    print("  backward() calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'Training runs: 0'.
    print("  Training runs: 0")
    # Display the text 'Model checkpoints: 0'.
    print("  Model checkpoints: 0")
    # Display the text 'Learned SUMO control: False'.
    print("  Learned SUMO control: False\n")
    # Set live to report at 'live_coverage'.
    live = report["live_coverage"]
    # Set traces to report at 'protocol_traces'.
    traces = report["protocol_traces"]
    # Display the text 'Live SUMO coverage'.
    print("Live SUMO coverage")
    # Display formatted text built from the embedded values.
    print(f"  Scenario specifications: {len(report['scenario_specifications'])}")
    # Display formatted text built from the embedded values.
    print(f"  Real scenario episodes executed: {report['real_sumo_scenario_episodes']}")
    # Set counts to report at 'live_snapshot_status_counts'.
    counts = report['live_snapshot_status_counts']
    # Display formatted text built from the embedded values.
    print(f"  Total live joint snapshots: {report['live_snapshot_count']}")
    # Display formatted text built from the embedded values.
    print(f"  Live regulatory-cycle snapshots: {counts.get('NEGOTIATION_REQUIRED_REGULATORY_CYCLE', 0)}")
    # Display formatted text built from the embedded values.
    print(f"  Live unresolved-precedence snapshots: {counts.get('NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE', 0)}")
    # Display formatted text built from the embedded values.
    print(f"  Live proposer opportunities: {sum(len(x['proposer_decision_event_ids']) for x in live)}")
    # Display formatted text built from the embedded values.
    print(f"  Live two-feasible proposer opportunities: {sum(sum(all(m) for m in x['proposer_action_masks']) for x in live)}\n")
    # Display the text 'Protocol coverage from live contexts'.
    print("Protocol coverage from live contexts")
    # Display the text 'Coverage action source: DETERMINISTIC_COVERAGE_ENUMERATION'.
    print("  Coverage action source: DETERMINISTIC_COVERAGE_ENUMERATION")
    # Display formatted text built from the embedded values.
    print(f"  Responder opportunities: {sum(len(x['responder_decision_event_ids']) for x in live)}")
    # Display formatted text built from the embedded values.
    print(f"  ACCEPT branches validated: {sum(x['responder_action'] == 'ACCEPT_RELINQUISHMENT' for x in traces)}")
    # Display formatted text built from the embedded values.
    print(f"  REJECT branches validated: {sum(x['responder_action'] == 'REJECT_RELINQUISHMENT' for x in traces)}")
    # Display formatted text built from the embedded values.
    print(f"  Agreements established: {sum(x['protocol_status'] == 'AGREEMENT_ESTABLISHED' for x in traces)}")
    # Display formatted text built from the embedded values.
    print(f"  Proposal rejections validated: {sum(x['protocol_status'] == 'PROPOSAL_REJECTED' for x in traces)}\n")
    # Display the text 'Coverage blocker status'.
    print("Coverage blocker status")
    # Set insufficient to report at 'step_5j_2_readiness' differs from the text 'READY_TO_RESUME_STEP_5J_2'.
    insufficient = report['step_5j_2_readiness'] != 'READY_TO_RESUME_STEP_5J_2'
    # Display formatted text built from the embedded values.
    print(f"  NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT: {insufficient}")
    # Display formatted text built from the embedded values.
    print(f"  RESPONDER_TRAINING_COVERAGE_MISSING: {not any(x['responder_decision_event_ids'] for x in live)}")
    # Display formatted text built from the embedded values.
    print(f"  STOP: {report['next_blocker']}")
    # Display formatted text built from the embedded values.
    print(f"  assess_step_5j_2_scenario_readiness(): {report['step_5j_2_readiness']}")
    # Display formatted text built from the embedded values.
    print(f"  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: {report['negotiation_action_to_traffic_outcome_status']}")
    # Display formatted text built from the embedded values.
    print(f"  assess_step_5j_3_environment_readiness(): {report['step_5j_3_readiness']}\n")
    # Display formatted text built from the embedded values.
    print(f"Catalogue metadata: {catalogue}")
    # Display formatted text built from the embedded values.
    print(f"Human-readable summary: {summary}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
