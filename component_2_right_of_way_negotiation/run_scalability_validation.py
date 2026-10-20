"""Small, frozen scalability study; never invokes the final 165-episode suite."""
# Import argparse for use in this module.
import argparse
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import BY_ID from scalability_validation.v2.cases for the operations below.
from scalability_validation.v2.cases import BY_ID

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def main():
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser(description=__doc__)
    # Set group to the result of parser.add_mutually_exclusive_group().
    group = parser.add_mutually_exclusive_group(required=True)
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--prepare",action="store_true")
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--preflight",action="store_true")
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--run",action="store_true")
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--report-only",action="store_true")
    # Call group.add_argument with the supplied arguments.
    group.add_argument("--replay",choices=BY_ID)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--run-id")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui",action="store_true")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--version",choices=("v1","v2"),default="v2",
                        # Supply help as the text 'V2 staggered study by default; V1 is read-only historical...'.
                        help="V2 staggered study by default; V1 is read-only historical evidence.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--output-root",type=Path)
    # Set args to the result of parser.parse_args().
    args = parser.parse_args()
    # Run this branch when args.version equals the text 'v1'.
    if args.version == "v1":
        # Run this branch when the negation of args.report_only.
        if not args.report_only:
            # Call parser.error with the supplied arguments.
            parser.error("SCALABILITY_VALIDATION_V1 is historical/read-only; no prepare, preflight, run or replay launches through this CLI.")
        # Call parser.error with the supplied arguments.
        parser.error("Preserve V1 reports unchanged; open results/scalability_validation/v1/latest/SCALABILITY_REPORT.html directly.")
    # Import ROOT, prepare from scalability_validation.v2.models for the operations below.
    from scalability_validation.v2.models import ROOT, prepare
    # Import preflight, run, replay from scalability_validation.v2.runner for the operations below.
    from scalability_validation.v2.runner import preflight, run, replay
    # Set args.output_root to args.output_root or ROOT.
    args.output_root = args.output_root or ROOT
    # Run this branch when args.prepare.
    if args.prepare:
        # Display the text 'Frozen manifest:'.
        print("Frozen manifest:",prepare(args.output_root)["manifest_hash"])
    # Run this branch when args.preflight.
    elif args.preflight:
        # Call preflight with the supplied arguments.
        preflight(args.output_root)
    # Run this branch when args.run.
    elif args.run:
        # Call run with the supplied arguments.
        run(args.output_root)
    # Run this branch when args.replay.
    elif args.replay:
        # Call replay with the supplied arguments.
        replay(args.replay,args.output_root,run_id=args.run_id,gui=args.gui)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Import report from scalability_validation.v2.reporting for the operations below.
        from scalability_validation.v2.reporting import report
        # Call report with the supplied arguments.
        report(args.output_root)

# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
