"""Run from Component 2; no training or UI-based scientific computation."""
import argparse
from pathlib import Path
import os

def main(argv=None):
    os.chdir(Path(__file__).resolve().parent)
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--diagnostics", action="store_true")
    modes.add_argument("--diagnostic-report", action="store_true")
    modes.add_argument("--suite", choices=("smoke", "final"))
    modes.add_argument("--report-only", action="store_true")
    modes.add_argument("--replay", metavar="RUN_ID")
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("results/post_training_evaluation/v2_candidate"))
    args = parser.parse_args(argv)
    if args.gui and not args.replay:
        parser.error("--gui requires --replay RUN_ID")
    from post_training_evaluation.scenarios import prepare
    if args.diagnostics or args.diagnostic_report:
        from post_training_evaluation.diagnostics import DIAGNOSTIC_ROOT, run_diagnostics, report_diagnostics
        root = DIAGNOSTIC_ROOT if args.output_root == Path("results/post_training_evaluation/v2_candidate") else args.output_root
        (run_diagnostics if args.diagnostics else report_diagnostics)(root)
    elif args.prepare:
        frozen = prepare(args.output_root)
        print("Frozen manifest:", frozen["manifest_hash"], "Final episodes: 165; smoke: 9")
    elif args.suite:
        from post_training_evaluation.runner import run_suite
        run_suite(args.suite, args.output_root)
    elif args.report_only:
        from post_training_evaluation.reporting import report
        report(args.output_root)
    else:
        from post_training_evaluation.replay import replay
        replay(args.replay, gui=args.gui, root=args.output_root)

if __name__ == "__main__":
    main()
