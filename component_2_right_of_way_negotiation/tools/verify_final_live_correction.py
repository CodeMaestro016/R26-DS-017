"""Predeclared real-SUMO cases, separate from frozen scientific evaluations."""
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Set JOBS to a list containing a tuple containing the text 'rule_resolved_two', 220, None, a tuple containing the
# text...
JOBS = [("rule_resolved_two", 220, None), ("four_way_simultaneous", 220, None),
        # Include a tuple containing the text 'multiple_left_turns', 220, None in this list.
        ("regulatory_cycle", 220, None), ("multiple_left_turns", 220, None),
        # Include a tuple containing the text 'mixed_manoeuvres', 220, None in this list.
        ("mixed_manoeuvres", 220, None), ("default_panel", 220, None),
        # Include a tuple containing the text 'congested_four_approach', 70, None in this list.
        ("congested_four_approach", 70, None),
        # Include a tuple containing the text 'congested_four_approach', 360, None in this list.
        ("congested_four_approach", 360, None)]
# Update JOBS to its current value plus a list of a tuple containing the text 'regulatory_cycle', 45, f for f in a
# tuple containing the text 'missing_declaration', the text 'stale_declaration', the text 'invalid_declaration',
# the text...
JOBS += [("regulatory_cycle", 45, f) for f in (
    "missing_declaration", "stale_declaration", "invalid_declaration",
    "incorrect_declaration", "contradictory_declaration", "stale_commitment")]


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Iterate over JOBS, binding each item to (scenario, duration, fault).
    for scenario, duration, fault in JOBS:
        # Set command to a list containing sys.executable, the text '-B', a string built from BASE divided by the
        # text...
        command = [sys.executable, "-B", str(BASE / "tools/diagnose_vehicle_states.py"),
            # Include a string built from duration in this list.
            "--scenario", scenario, "--duration", str(duration), "--version",
            # Include the text 'final_corrected_native_v1_' plus a string built from duration in this list.
            "final_corrected_native_v1_" + str(duration), "--command-trace",
            "--native-junction-trace"]
        # Run this branch when fault.
        if fault:
            # Update command to its current value plus a list containing the text '--fault', fault.
            command += ["--fault", fault]
        # Display the text 'START'.
        print("START", scenario, duration, fault, flush=True)
        # Call subprocess.run with the supplied arguments.
        subprocess.run(command, cwd=BASE.parent, check=True)
    # Display the text 'ALL PREDECLARED DIAGNOSTIC JOBS FINISHED'.
    print("ALL PREDECLARED DIAGNOSTIC JOBS FINISHED", flush=True)


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
