"""Predeclared real-SUMO cases, separate from frozen scientific evaluations."""
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
JOBS = [("rule_resolved_two", 220, None), ("four_way_simultaneous", 220, None),
        ("regulatory_cycle", 220, None), ("multiple_left_turns", 220, None),
        ("mixed_manoeuvres", 220, None), ("default_panel", 220, None),
        ("congested_four_approach", 70, None),
        ("congested_four_approach", 360, None)]
JOBS += [("regulatory_cycle", 45, f) for f in (
    "missing_declaration", "stale_declaration", "invalid_declaration",
    "incorrect_declaration", "contradictory_declaration", "stale_commitment")]


def main():
    for scenario, duration, fault in JOBS:
        command = [sys.executable, "-B", str(BASE / "tools/diagnose_vehicle_states.py"),
            "--scenario", scenario, "--duration", str(duration), "--version",
            "final_corrected_native_v1_" + str(duration), "--command-trace",
            "--native-junction-trace"]
        if fault:
            command += ["--fault", fault]
        print("START", scenario, duration, fault, flush=True)
        subprocess.run(command, cwd=BASE.parent, check=True)
    print("ALL PREDECLARED DIAGNOSTIC JOBS FINISHED", flush=True)


if __name__ == "__main__":
    main()
