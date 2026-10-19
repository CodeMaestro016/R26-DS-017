"""Small, frozen scalability study; never invokes the final 165-episode suite."""
import argparse
from pathlib import Path
from scalability_validation.v2.cases import BY_ID

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare",action="store_true")
    group.add_argument("--preflight",action="store_true")
    group.add_argument("--run",action="store_true")
    group.add_argument("--report-only",action="store_true")
    group.add_argument("--replay",choices=BY_ID)
    parser.add_argument("--run-id")
    parser.add_argument("--gui",action="store_true")
    parser.add_argument("--version",choices=("v1","v2"),default="v2",
                        help="V2 staggered study by default; V1 is read-only historical evidence.")
    parser.add_argument("--output-root",type=Path)
    args = parser.parse_args()
    if args.version == "v1":
        if not args.report_only:
            parser.error("SCALABILITY_VALIDATION_V1 is historical/read-only; no prepare, preflight, run or replay launches through this CLI.")
        parser.error("Preserve V1 reports unchanged; open results/scalability_validation/v1/latest/SCALABILITY_REPORT.html directly.")
    from scalability_validation.v2.models import ROOT, prepare
    from scalability_validation.v2.runner import preflight, run, replay
    args.output_root = args.output_root or ROOT
    if args.prepare:
        print("Frozen manifest:",prepare(args.output_root)["manifest_hash"])
    elif args.preflight:
        preflight(args.output_root)
    elif args.run:
        run(args.output_root)
    elif args.replay:
        replay(args.replay,args.output_root,run_id=args.run_id,gui=args.gui)
    else:
        from scalability_validation.v2.reporting import report
        report(args.output_root)

if __name__ == "__main__":
    main()
