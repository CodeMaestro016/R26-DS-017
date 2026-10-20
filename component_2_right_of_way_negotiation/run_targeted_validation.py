"""Reproducible Targeted Validation; no training or extended evaluation launch."""
# Import argparse for use in this module.
import argparse
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path

# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main(argv=None):
    # Call os.chdir with the supplied arguments.
    os.chdir(Path(__file__).resolve().parent)
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser(description=__doc__)
    # Set group to the result of parser.add_mutually_exclusive_group().
    group = parser.add_mutually_exclusive_group(required=True)
    # Iterate over a tuple containing the text 'prepare', the text 'preflight', the text 'run', the text
    # 'report-only', binding each item to mode.
    for mode in ("prepare", "preflight", "run", "report-only"):
        # Call group.add_argument with the supplied arguments.
        group.add_argument("--" + mode, action="store_true")
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--replay", choices=("PV-01", "PV-02", "PV-03", "PV-04", "PV-04A", "PV-04B", "PV-05", "PV-06"))
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--case", choices=("PV-01", "PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05", "PV-06"))
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--output-root", type=Path, default=Path("results/targeted_validation/v2"))
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--run-id")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--method", choices=("PROPOSED_MAPPO", "RULES_ONLY"), default="PROPOSED_MAPPO")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui", action="store_true")
    # Set args to the result of parser.parse_args(argv).
    args = parser.parse_args(argv)
    # Run this branch when args.gui or args.run_id and the negation of args.replay.
    if (args.gui or args.run_id) and not args.replay:
        # Call parser.error with the supplied arguments.
        parser.error("--gui/--run-id require --replay")
    # Import prepare from targeted_validation.models for the operations below.
    from targeted_validation.models import prepare
    # Import preflight, run, replay, run_case from targeted_validation.runner for the operations below.
    from targeted_validation.runner import preflight, run, replay, run_case
    # Import report from targeted_validation.reporting for the operations below.
    from targeted_validation.reporting import report
    # Run this branch when args.prepare.
    if args.prepare:
        # Display the text 'Frozen panel manifest:'.
        print("Frozen panel manifest:", prepare(args.output_root)["manifest_hash"])
    # Run this branch when args.preflight.
    elif args.preflight:
        # Call preflight with the supplied arguments.
        preflight(args.output_root)
    # Run this branch when args.run.
    elif args.run:
        # Call run with the supplied arguments.
        run(args.output_root)
    # Run this branch when args.case.
    elif args.case:
        # Call run_case with the supplied arguments.
        run_case(args.case, args.output_root)
    # Run this branch when args.report_only.
    elif args.report_only:
        # Call report with the supplied arguments.
        report(args.output_root)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Call replay with the supplied arguments.
        replay(args.replay, args.output_root, run_id=args.run_id, method=args.method, gui=args.gui)

# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
