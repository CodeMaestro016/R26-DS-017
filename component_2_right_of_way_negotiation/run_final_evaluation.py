"""Run from Component 2; no training or UI-based scientific computation."""
import argparse
from pathlib import Path
import os

def main(argv=None):
    os.chdir(Path(__file__).resolve().parent)
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--suite", choices=("smoke", "final"))
    modes.add_argument("--report-only", action="store_true")
    modes.add_argument("--replay", metavar="RUN_ID")
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("results/final_evaluation"))
    args = parser.parse_args(argv)
    if args.gui and not args.replay:
        parser.error("--gui requires --replay RUN_ID")
    from final_evaluation.scenarios import prepare
    if args.prepare:
        frozen = prepare(args.output_root)
        print("Frozen manifest:", frozen["manifest_hash"], "Final episodes: 165; smoke: 9")
    elif args.suite:
        from final_evaluation.runner import run_suite
        run_suite(args.suite, args.output_root)
    elif args.report_only:
        from final_evaluation.reporting import report
        report(args.output_root)
    else:
        from final_evaluation.replay import replay
        replay(args.replay, gui=args.gui, root=args.output_root)

if __name__ == "__main__":
    main()
