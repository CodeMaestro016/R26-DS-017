"""CLI for the bounded final MAPPO validation-selection experiment."""

# Import argparse for use in this module.
import argparse

# Import CANDIDATE_EPOCHS, REPLICATION_COUNT, UPDATE_HORIZON, baseline, heldout, prepare, report, select, smoke,
# train, validate from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import (
    CANDIDATE_EPOCHS, REPLICATION_COUNT, UPDATE_HORIZON,
    baseline, heldout, prepare, report, select, smoke, train, validate,
)


# Set STAGES to a tuple containing the text 'prepare', the text 'smoke', the text 'train', the text 'validate',
# the text 'select', the text...
STAGES = ("prepare", "smoke", "train", "validate", "select", "heldout",
          "baseline", "report", "all")


# Parse args using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: the result of parser.parse_args(argv).
def parse_args(argv=None):
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser(
        # Supply description as the text 'Run final E5/E10/E15 MAPPO validation selection.'.
        description="Run final E5/E10/E15 MAPPO validation selection.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--stage", required=True, choices=STAGES)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--resume", action="store_true")
    # Return the result of parser.parse_args(argv) to the caller.
    return parser.parse_args(argv)


# Prepared summary using the inputs and processing steps below.
# Input protocol: the supplied protocol.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def _prepared_summary(protocol):
    # Display the text 'Final MAPPO selection protocol prepared.'.
    print("Final MAPPO selection protocol prepared.\n")
    # Display the text 'Candidates:'.
    print("Candidates:")
    # Iterate over key/value pairs from CANDIDATE_EPOCHS, binding each item to (candidate, epochs).
    for candidate, epochs in CANDIDATE_EPOCHS.items():
        # Display formatted text built from the embedded values.
        print(f"{candidate:<3} -> PPO epochs {epochs}")
    # Display formatted text built from the embedded values.
    print(f"\nReplications: {REPLICATION_COUNT}")
    # Display formatted text built from the embedded values.
    print(f"Update horizon H: {UPDATE_HORIZON}\n")
    # Set manifests to protocol at 'manifests'.
    manifests = protocol["manifests"]
    # Iterate over a tuple containing the text 'TRAINING', the text 'VALIDATION', the text 'HELD_OUT_TEST',
    # binding each item to role.
    for role in ("TRAINING", "VALIDATION", "HELD_OUT_TEST"):
        # Display formatted text built from the embedded values.
        print(f"{role.replace('_', ' ').title()} scenarios: "
              # Evaluate {manifests[role]['scenario_count']} as part of the enclosing expression.
              f"{manifests[role]['scenario_count']}")
    # Display the text 'Held-out locked: YES'.
    print("\nHeld-out locked: YES")
    # Display the text 'Ready for training: YES'.
    print("Ready for training: YES")


# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main(argv=None):
    # Set args to the result of parse_args(argv).
    args = parse_args(argv)
    # Run this branch when args.stage equals the text 'prepare'.
    if args.stage == "prepare":
        # Call _prepared_summary with the supplied arguments.
        _prepared_summary(prepare())
    # Run this branch when args.stage equals the text 'smoke'.
    elif args.stage == "smoke":
        # Set result to the result of smoke().
        result = smoke()
        # Display result at 'status'.
        print(result["status"])
        # Display the text 'NOT_MODEL_SELECTION_EVIDENCE'.
        print("NOT_MODEL_SELECTION_EVIDENCE")
        # Display the text 'Held-out scenarios consumed: 0'.
        print("Held-out scenarios consumed: 0")
    # Run this branch when args.stage equals the text 'train'.
    elif args.stage == "train":
        # Display the result of train().
        print(train(resume=args.resume))
    # Run this branch when args.stage equals the text 'validate'.
    elif args.stage == "validate":
        # Set result to the result of validate().
        result = validate(resume=args.resume)
        # Display the text 'Candidate Mean validation TTT Collisions Blocked Eligible'.
        print("Candidate   Mean validation TTT   Collisions   Blocked   Eligible")
        # Iterate over key/value pairs from result['candidates'], binding each item to (key, item).
        for key, item in result["candidates"].items():
            # Set summary to item at 'summary'.
            summary = item["summary"]
            # Display formatted text built from the embedded values.
            print(f"{key:<11} "
                  # Evaluate {summary['mean_replication_total_team_travel_time_seconds']:<21.6f} as part of the
                  # enclosing expression.
                  f"{summary['mean_replication_total_team_travel_time_seconds']:<21.6f} "
                  # Evaluate {summary['collisions']:<12} as part of the enclosing expression.
                  f"{summary['collisions']:<12} "
                  # Evaluate {summary['blocked_zone_violations']:<9} as part of the enclosing expression.
                  f"{summary['blocked_zone_violations']:<9} "
                  # Evaluate {item['eligible']} as part of the enclosing expression.
                  f"{item['eligible']}")
    # Run this branch when args.stage equals the text 'select'.
    elif args.stage == "select":
        # Set result to the result of select().
        result = select()
        # Display the text 'SELECTED_CONFIGURATION =' plus result at 'selected_candidate_id'.
        print("SELECTED_CONFIGURATION = " + result["selected_candidate_id"])
        # Display the text 'SELECTION_BASIS = VALIDATION_ONLY'.
        print("SELECTION_BASIS = VALIDATION_ONLY")
        # Display the text 'GLOBAL_OPTIMALITY_CLAIM = FALSE'.
        print("GLOBAL_OPTIMALITY_CLAIM = FALSE")
        # Display the text 'HELD_OUT_CONSUMED = FALSE'.
        print("HELD_OUT_CONSUMED = FALSE")
    # Run this branch when args.stage equals the text 'heldout'.
    elif args.stage == "heldout":
        # Display heldout(resume=args.resume) at 'status'.
        print(heldout(resume=args.resume)["status"])
    # Run this branch when args.stage equals the text 'baseline'.
    elif args.stage == "baseline":
        # Display baseline(resume=args.resume) at 'baseline_id'.
        print(baseline(resume=args.resume)["baseline_id"])
    # Run this branch when args.stage equals the text 'report'.
    elif args.stage == "report":
        # Display the result of report().
        print(report())
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set protocol to the result of prepare().
        # Call _prepared_summary with the supplied arguments.
        protocol = prepare(); _prepared_summary(protocol)
        # Call train with the supplied arguments.
        train(resume=args.resume)
        # Call validate with the supplied arguments.
        validate(resume=args.resume)
        # Call select with the supplied arguments.
        select()
        # Call heldout with the supplied arguments.
        heldout(resume=args.resume)
        # Call baseline with the supplied arguments.
        baseline(resume=args.resume)
        # Call report with the supplied arguments.
        report()


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
