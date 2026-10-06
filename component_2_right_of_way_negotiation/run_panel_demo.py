"""Launch the one-process qualitative live SUMO panel demonstration."""

import argparse

from panel_demo import run_panel_demo
from panel_demo.scenarios import SCENARIO_BY_ID, get_scenario


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--duration", type=float, default=None,
                        help="Presentation duration in simulation seconds.")
    parser.add_argument("--gui-delay-ms", type=int, default=0,
                        help="Display delay only; simulation timing is unchanged.")
    parser.add_argument("--web-live", action="store_true",
                        help="Publish display-only state for the browser showcase.")
    parser.add_argument("--presentation-delay-ms", type=int, default=0,
                        help="Display pacing only; simulation decisions are unchanged.")
    parser.add_argument("--scenario", choices=tuple(SCENARIO_BY_ID),
                        default="default_panel",
                        help="Predefined qualitative presentation schedule.")
    parser.add_argument("--presentation-run-id", default=None,
                        help="Presentation-only run-history identifier.")
    parser.add_argument("--output-dir", default="results/panel_demo",
                        help="Separate directory for new qualitative output.")
    parser.add_argument("--stop-request-path", default=None,
                        help="Owned cooperative presentation stop request.")
    args = parser.parse_args(argv)
    scenario = get_scenario(args.scenario)
    result = run_panel_demo(duration_seconds=(args.duration if args.duration is not None
                            else scenario.recommended_duration_seconds), use_gui=args.gui,
                            gui_delay_ms=args.gui_delay_ms,
                            web_live=args.web_live,
                            presentation_delay_ms=args.presentation_delay_ms,
                            schedule=scenario.schedule(),
                            admission_waves=scenario.admission_waves,
                            scenario_id=scenario.scenario_id,
                            output_dir=args.output_dir,
                            admission_mode=scenario.admission_mode,
                            presentation_run_id=args.presentation_run_id,
                            stop_request_path=args.stop_request_path)
    metrics = result["metrics"]
    print("PANEL DEMO SUMMARY (PRESENTATION_ONLY)")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print(f"Selected-policy hash unchanged: {result['policy_hash_unchanged']}")
    print(f"Centralized critic calls: {result['centralized_critic_calls']}")
    print("Training operations: 0")
    print("Held-out scenarios consumed: 0")


if __name__ == "__main__":
    main()
