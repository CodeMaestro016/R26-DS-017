"""Run from Component 2; no training or UI-based scientific computation."""
# Import argparse for use in this module.
import argparse
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import os for use in this module.
import os

# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def main(argv=None):
    # Call os.chdir with the supplied arguments.
    os.chdir(Path(__file__).resolve().parent)
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser(description=__doc__)
    # Set modes to the result of parser.add_mutually_exclusive_group().
    modes = parser.add_mutually_exclusive_group(required=True)
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--prepare", action="store_true")
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--diagnostics", action="store_true")
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--diagnostic-report", action="store_true")
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--suite", choices=("smoke", "final"))
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--report-only", action="store_true")
    # Call modes.add_argument with the supplied arguments.
    modes.add_argument("--replay", metavar="RUN_ID")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui", action="store_true")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--output-root", type=Path, default=Path("results/post_training_evaluation/v2_candidate"))
    # Set args to the result of parser.parse_args(argv).
    args = parser.parse_args(argv)
    # Run this branch when args.gui and the negation of args.replay.
    if args.gui and not args.replay:
        # Call parser.error with the supplied arguments.
        parser.error("--gui requires --replay RUN_ID")
    # Import prepare from post_training_evaluation.scenarios for the operations below.
    from post_training_evaluation.scenarios import prepare
    # Run this branch when args.diagnostics or args.diagnostic_report.
    if args.diagnostics or args.diagnostic_report:
        # Import DIAGNOSTIC_ROOT, run_diagnostics, report_diagnostics from post_training_evaluation.diagnostics
        # for the operations below.
        from post_training_evaluation.diagnostics import DIAGNOSTIC_ROOT, run_diagnostics, report_diagnostics
        # Set root to DIAGNOSTIC_ROOT when args.output_root equals the result of Path(the text
        # 'results/post_training_evaluation/v2_candidate'), otherwise args.output_root.
        root = DIAGNOSTIC_ROOT if args.output_root == Path("results/post_training_evaluation/v2_candidate") else args.output_root
        # Call run_diagnostics if args.diagnostics else report_diagnostics with the supplied arguments.
        (run_diagnostics if args.diagnostics else report_diagnostics)(root)
    # Run this branch when args.prepare.
    elif args.prepare:
        # Set frozen to the result of prepare(args.output_root).
        frozen = prepare(args.output_root)
        # Display the text 'Frozen manifest:'.
        print("Frozen manifest:", frozen["manifest_hash"], "Final episodes: 165; smoke: 9")
    # Run this branch when args.suite.
    elif args.suite:
        # Import run_suite from post_training_evaluation.runner for the operations below.
        from post_training_evaluation.runner import run_suite
        # Call run_suite with the supplied arguments.
        run_suite(args.suite, args.output_root)
    # Run this branch when args.report_only.
    elif args.report_only:
        # Import report from post_training_evaluation.reporting for the operations below.
        from post_training_evaluation.reporting import report
        # Call report with the supplied arguments.
        report(args.output_root)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Import replay from post_training_evaluation.replay for the operations below.
        from post_training_evaluation.replay import replay
        # Call replay with the supplied arguments.
        replay(args.replay, gui=args.gui, root=args.output_root)

# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
