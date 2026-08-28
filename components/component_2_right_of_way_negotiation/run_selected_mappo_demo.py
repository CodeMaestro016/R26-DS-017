"""Run the validation-selected canonical-replication-0 MAPPO demo."""

import argparse
from pathlib import Path

from negotiation_training.controlled_pilot import atomic_write_json
from negotiation_training.final_selection import run_selected_demo


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--liveness-report", type=Path,
                        help="Write new runtime-only liveness evidence.")
    args = parser.parse_args(argv)
    result = run_selected_demo(use_gui=args.gui)
    print("Selected candidate: " + result["selected_candidate_id"])
    print("Demo replication rule: CANONICAL_REPLICATION_0")
    print("Training operations: 0")
    print("Held-out scenarios used: 0")
    print(f"Demo scenarios completed: {len(result['scenario_results'])}")
    for record in result["scenario_results"]:
        metrics = record["liveness_metrics"]
        print(f"{record['scenario_id']}: completed "
              f"{metrics['completed_vehicles']}/{metrics['scheduled_vehicles']}; "
              f"decision epochs={metrics['negotiation_decision_epochs']}; "
              f"renegotiations={metrics['renegotiation_events']}; "
              f"all completed={metrics['all_scheduled_vehicles_completed']}")
    if args.liveness_report:
        atomic_write_json(args.liveness_report, result)
        print(f"Liveness report: {args.liveness_report}")


if __name__ == "__main__":
    main()
