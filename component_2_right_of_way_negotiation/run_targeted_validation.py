"""Reproducible Targeted Validation; no training or extended evaluation launch."""
import argparse
import os
from pathlib import Path

def main(argv=None):
    os.chdir(Path(__file__).resolve().parent)
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for mode in ("prepare", "preflight", "run", "report-only"):
        group.add_argument("--" + mode, action="store_true")
    group.add_argument("--replay", choices=("PV-01", "PV-02", "PV-03", "PV-04", "PV-04A", "PV-04B", "PV-05", "PV-06"))
    group.add_argument("--case", choices=("PV-01", "PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05", "PV-06"))
    parser.add_argument("--output-root", type=Path, default=Path("results/targeted_validation/v2"))
    parser.add_argument("--run-id")
    parser.add_argument("--method", choices=("PROPOSED_MAPPO", "RULES_ONLY"), default="PROPOSED_MAPPO")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args(argv)
    if (args.gui or args.run_id) and not args.replay:
        parser.error("--gui/--run-id require --replay")
    from targeted_validation.models import prepare
    from targeted_validation.runner import preflight, run, replay, run_case
    from targeted_validation.reporting import report
    if args.prepare:
        print("Frozen panel manifest:", prepare(args.output_root)["manifest_hash"])
    elif args.preflight:
        preflight(args.output_root)
    elif args.run:
        run(args.output_root)
    elif args.case:
        run_case(args.case, args.output_root)
    elif args.report_only:
        report(args.output_root)
    else:
        replay(args.replay, args.output_root, run_id=args.run_id, method=args.method, gui=args.gui)

if __name__ == "__main__":
    main()
