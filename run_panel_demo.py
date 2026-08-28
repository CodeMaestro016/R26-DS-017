"""Launch the one-process qualitative live SUMO panel demonstration."""

import argparse

from panel_demo import run_panel_demo


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Presentation duration in simulation seconds.")
    parser.add_argument("--gui-delay-ms", type=int, default=0,
                        help="Display delay only; simulation timing is unchanged.")
    args = parser.parse_args(argv)
    result = run_panel_demo(duration_seconds=args.duration, use_gui=args.gui,
                            gui_delay_ms=args.gui_delay_ms)
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
