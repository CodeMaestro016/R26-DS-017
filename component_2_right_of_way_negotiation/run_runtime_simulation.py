"""Launch the one-process qualitative live SUMO Runtime Simulation."""

# Import argparse for use in this module.
import argparse

# Import run_runtime_simulation from runtime_simulation for the operations below.
from runtime_simulation import run_runtime_simulation
# Import SCENARIO_BY_ID, get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import SCENARIO_BY_ID, get_scenario


# Main using the inputs and processing steps below.
# Input argv: the supplied argv.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main(argv=None):
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser()
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui", action="store_true")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--duration", type=float, default=None,
                        # Supply help as the text 'Presentation duration in simulation seconds.'.
                        help="Presentation duration in simulation seconds.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--gui-delay-ms", type=int, default=0,
                        # Supply help as the text 'Display delay only; simulation timing is unchanged.'.
                        help="Display delay only; simulation timing is unchanged.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--web-live", action="store_true",
                        # Supply help as the text 'Publish display-only state for the browser showcase.'.
                        help="Publish display-only state for the browser showcase.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--presentation-delay-ms", type=int, default=0,
                        # Supply help as the text 'Display pacing only; simulation decisions are unchanged.'.
                        help="Display pacing only; simulation decisions are unchanged.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--scenario", choices=tuple(SCENARIO_BY_ID),
                        # Supply default as the text 'default_panel'.
                        default="default_panel",
                        # Supply help as the text 'Predefined qualitative presentation schedule.'.
                        help="Predefined qualitative presentation schedule.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--presentation-run-id", default=None,
                        # Supply help as the text 'Presentation-only run-history identifier.'.
                        help="Presentation-only run-history identifier.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--output-dir", default="results/runtime_simulation",
                        # Supply help as the text 'Separate directory for new qualitative output.'.
                        help="Separate directory for new qualitative output.")
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument("--stop-request-path", default=None,
                        # Supply help as the text 'Owned cooperative presentation stop request.'.
                        help="Owned cooperative presentation stop request.")
    # Set args to the result of parser.parse_args(argv).
    args = parser.parse_args(argv)
    # Set scenario to the result of get_scenario(args.scenario).
    scenario = get_scenario(args.scenario)
    # Set result to the result of run_runtime_simulation().
    result = run_runtime_simulation(duration_seconds=(args.duration if args.duration is not None
                            # Supply use_gui as args.gui.
                            else scenario.recommended_duration_seconds), use_gui=args.gui,
                            # Supply gui_delay_ms as args.gui_delay_ms.
                            gui_delay_ms=args.gui_delay_ms,
                            # Supply web_live as args.web_live.
                            web_live=args.web_live,
                            # Supply presentation_delay_ms as args.presentation_delay_ms.
                            presentation_delay_ms=args.presentation_delay_ms,
                            # Supply schedule as the result of scenario.schedule().
                            schedule=scenario.schedule(),
                            # Supply admission_waves as scenario.admission_waves.
                            admission_waves=scenario.admission_waves,
                            # Supply scenario_id as scenario.scenario_id.
                            scenario_id=scenario.scenario_id,
                            # Supply output_dir as args.output_dir.
                            output_dir=args.output_dir,
                            # Supply admission_mode as scenario.admission_mode.
                            admission_mode=scenario.admission_mode,
                            # Supply presentation_run_id as args.presentation_run_id.
                            presentation_run_id=args.presentation_run_id,
                            # Supply stop_request_path as args.stop_request_path.
                            stop_request_path=args.stop_request_path)
    # Set metrics to result at 'metrics'.
    metrics = result["metrics"]
    # Display the text 'RUNTIME SIMULATION SUMMARY (PRESENTATION_ONLY)'.
    print("RUNTIME SIMULATION SUMMARY (PRESENTATION_ONLY)")
    # Iterate over key/value pairs from metrics, binding each item to (key, value).
    for key, value in metrics.items():
        # Display formatted text built from the embedded values.
        print(f"{key}: {value}")
    # Display formatted text built from the embedded values.
    print(f"Selected-policy hash unchanged: {result['policy_hash_unchanged']}")
    # Display formatted text built from the embedded values.
    print(f"Centralized critic calls: {result['centralized_critic_calls']}")
    # Display the text 'Training operations: 0'.
    print("Training operations: 0")
    # Display the text 'Held-out scenarios consumed: 0'.
    print("Held-out scenarios consumed: 0")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
