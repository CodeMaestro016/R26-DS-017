"""Run the validation-selected canonical-replication-0 MAPPO demo."""

# Import argparse for use in this module.
import argparse
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import atomic_write_json from negotiation_training.controlled_pilot for the operations below.
from negotiation_training.controlled_pilot import atomic_write_json
# Import run_selected_demo from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import run_selected_demo


# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main(argv=None):
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser()
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui", action="store_true")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--liveness-report", type=Path,
                        # Supply help as the text 'Write new runtime-only liveness evidence.'.
                        help="Write new runtime-only liveness evidence.")
    # Set args to the result of parser.parse_args(argv).
    args = parser.parse_args(argv)
    # Set result to the result of run_selected_demo().
    result = run_selected_demo(use_gui=args.gui)
    # Display the text 'Selected candidate:' plus result at 'selected_candidate_id'.
    print("Selected candidate: " + result["selected_candidate_id"])
    # Display the text 'Demo replication rule: CANONICAL_REPLICATION_0'.
    print("Demo replication rule: CANONICAL_REPLICATION_0")
    # Display the text 'Training operations: 0'.
    print("Training operations: 0")
    # Display the text 'Held-out scenarios used: 0'.
    print("Held-out scenarios used: 0")
    # Display formatted text built from the embedded values.
    print(f"Demo scenarios completed: {len(result['scenario_results'])}")
    # Iterate over result at 'scenario_results', binding each item to record.
    for record in result["scenario_results"]:
        # Set metrics to record at 'liveness_metrics'.
        metrics = record["liveness_metrics"]
        # Display formatted text built from the embedded values.
        print(f"{record['scenario_id']}: completed "
              # Evaluate {metrics['completed_vehicles']} as part of the enclosing expression.
              f"{metrics['completed_vehicles']}/{metrics['scheduled_vehicles']}; "
              # Evaluate {metrics['negotiation_decision_epochs']} as part of the enclosing expression.
              f"decision epochs={metrics['negotiation_decision_epochs']}; "
              # Evaluate {metrics['renegotiation_events']} as part of the enclosing expression.
              f"renegotiations={metrics['renegotiation_events']}; "
              # Evaluate {metrics['all_scheduled_vehicles_completed']} as part of the enclosing expression.
              f"all completed={metrics['all_scheduled_vehicles_completed']}")
    # Run this branch when args.liveness_report.
    if args.liveness_report:
        # Call atomic_write_json with the supplied arguments.
        atomic_write_json(args.liveness_report, result)
        # Display formatted text built from the embedded values.
        print(f"Liveness report: {args.liveness_report}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
