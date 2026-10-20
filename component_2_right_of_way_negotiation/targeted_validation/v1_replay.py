"""Verified archived V1 replay; original V1 evidence is never written."""
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Set ARCHIVE to BASE joined with the path segment 'results/panel_validation_archives/v1'.
ARCHIVE = BASE / "results/panel_validation_archives/v1"
# Set _launch to subprocess.run.
_launch = subprocess.run

# Replay v1 using the inputs and processing steps below.
# Input case_id: the supplied case id.
# Input root: the base directory used to resolve files.
# Input run_id: the supplied run id.
# Input method: the supplied method.
# Input gui: the supplied gui.
# Output: the result of _launch(command).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def replay_v1(case_id, root, *, run_id=None, method="PROPOSED_MAPPO", gui=False):
    # Import digest, file_hash from final_evaluation.models for the operations below.
    from final_evaluation.models import digest, file_hash
    # Import records, read_checked_manifest from .models for the operations below.
    from .models import records, read_checked_manifest
    # Import BY_ID from .cases for the operations below.
    from .cases import BY_ID
    # Import platform for use in this module.
    import platform
    # Import sumo_version from final_evaluation.scenarios for the operations below.
    from final_evaluation.scenarios import sumo_version
    # Set original_id to the text 'PV-04' when case_id equals the text 'PV-04B', otherwise case_id.
    original_id = "PV-04" if case_id == "PV-04B" else case_id
    # Run this branch when original_id equals the text 'PV-04A'.
    if original_id == "PV-04A":
        # Raise ValueError with the text 'PV04A_NOT_IN_V1' to stop this execution path.
        raise ValueError("PV04A_NOT_IN_V1")
    # Set frozen to the result of read_checked_manifest(root).
    frozen = read_checked_manifest(root)
    # Run this branch when frozen['manifest'] at 'python_version' differs from the result of
    # platform.python_version() or frozen['manifest'] at 'sumo_version' differs from the result of sumo_version().
    if frozen["manifest"]["python_version"] != platform.python_version() or frozen["manifest"]["sumo_version"] != sumo_version():
        # Raise RuntimeError with the text 'V1_REPLAY_ENVIRONMENT_MISMATCH' to stop this execution path.
        raise RuntimeError("V1_REPLAY_ENVIRONMENT_MISMATCH")
    # Set inventory to the decoded data produced by json.loads from the text read from (ARCHIVE /
    # 'runtime_inventory.json').
    inventory = json.loads((ARCHIVE / "runtime_inventory.json").read_text(encoding="utf-8-sig"))
    # Set snapshot to the result of (ARCHIVE / 'runtime').resolve().
    snapshot = (ARCHIVE / "runtime").resolve()
    # Iterate over key/value pairs from inventory, binding each item to (name, expected).
    for name, expected in inventory.items():
        # Set path to the result of (snapshot / name).resolve().
        path = (snapshot / name).resolve()
        # Run this branch when the negation of the result of path.is_relative_to(snapshot) or the result of
        # file_hash(path) differs from expected.
        if not path.is_relative_to(snapshot) or file_hash(path) != expected:
            # Raise RuntimeError with the text 'V1_REPLAY_ARCHIVE_MISMATCH' to stop this execution path.
            raise RuntimeError("V1_REPLAY_ARCHIVE_MISMATCH")
    # Iterate over key/value pairs from {**frozen['manifest']['source_identities'],
    # **frozen['manifest']['panel_source_identities']}, binding each item to (name, expected).
    for name, expected in {**frozen["manifest"]["source_identities"], **frozen["manifest"]["panel_source_identities"]}.items():
        # Run this branch when the result of file_hash(snapshot divided by name) differs from expected.
        if file_hash(snapshot / name) != expected:
            # Raise RuntimeError with the text 'V1_REPLAY_FROZEN_SOURCE_MISMATCH' to stop this execution path.
            raise RuntimeError("V1_REPLAY_FROZEN_SOURCE_MISMATCH")
    # Set selected to a list of r for r in the result of records(root) plus the result of records(root, the text
    # 'preflight'); retain entries satisfying r at 'scenario_id' equals BY_ID[original_id].scenario_id and
    # r['run_id'] equals run_id...
    selected = [r for r in records(root) + records(root, "preflight") if
        # Evaluate r at 'scenario_id' equals BY_ID[original_id].scenario_id and r at 'run_id' equals run_id when
        # run_id, otherwise r['suite'] equals 'panel' and r['method'] equals method as part of the enclosing
        # expression.
        r["scenario_id"] == BY_ID[original_id].scenario_id and
        # Evaluate r at 'run_id' equals run_id when run_id, otherwise r at 'suite' equals the text 'panel' and r
        # at 'method' equals method as part of the enclosing expression.
        (r["run_id"] == run_id if run_id else r["suite"] == "panel" and r["method"] == method)]
    # Run this branch when the number of entries in selected differs from 1.
    if len(selected) != 1:
        # Raise RuntimeError with the text 'V1_REPLAY_SELECT_EXACT_RUN' to stop this execution path.
        raise RuntimeError("V1_REPLAY_SELECT_EXACT_RUN")
    # Set chosen to selected at 0.
    chosen = selected[0]
    # Set expected_seed to an integer built from digest((frozen['manifest']['protocol_id'], chosen['scenario_id'],
    # None, chosen['method'])) sliced by :16 modulo 2 raised to the power 31.
    expected_seed = int(digest((frozen["manifest"]["protocol_id"], chosen["scenario_id"], None, chosen["method"]))[:16], 16) % (2**31)
    # Run this branch when chosen at 'policy_action_seed' differs from expected_seed.
    if chosen["policy_action_seed"] != expected_seed:
        # Raise RuntimeError with the text 'V1_REPLAY_ACTION_SEED_MISMATCH' to stop this execution path.
        raise RuntimeError("V1_REPLAY_ACTION_SEED_MISMATCH")
    # Set output to BASE joined with the path segment 'results/targeted_validation/replays/v1'.
    output = BASE / "results/targeted_validation/replays/v1"
    # Set command to a list containing sys.executable, the text '-B', a string built from the result of
    # Path(__file__).resolve(), the text...
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(snapshot),
        # Include a string built from the result of Path(root).resolve() in this list.
        str(Path(root).resolve()), str(output), original_id, chosen["run_id"]]
    # Run this branch when gui.
    if gui:
        # Append the text '--gui' to command.
        command.append("--gui")
    # Return the result of _launch(command) to the caller.
    return _launch(command, check=True)

# Worker using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def worker():
    # Set (snapshot, original, output, case_id, run_id) to sys.argv sliced by 2:7.
    snapshot, original, output, case_id, run_id = sys.argv[2:7]
    # Call os.chdir with the supplied arguments.
    os.chdir(snapshot)
    # Call sys.path.insert with the supplied arguments.
    sys.path.insert(0, snapshot)
    # Import execute from panel_validation.runner for the operations below.
    from panel_validation.runner import execute
    # Import BY_ID from panel_validation.cases for the operations below.
    from panel_validation.cases import BY_ID
    # Import read_checked_manifest, records from panel_validation.models for the operations below.
    from panel_validation.models import read_checked_manifest, records
    # Import source_identities, restore_schedule from final_evaluation.scenarios for the operations below.
    from final_evaluation.scenarios import source_identities, restore_schedule
    # Import write_json from final_evaluation.models for the operations below.
    from final_evaluation.models import write_json
    # Set frozen to the result of read_checked_manifest(original).
    frozen = read_checked_manifest(original)
    # Run this branch when the result of source_identities() differs from frozen['manifest'] at
    # 'source_identities'.
    if source_identities() != frozen["manifest"]["source_identities"]:
        # Raise RuntimeError with the text 'V1_REPLAY_SOURCE_MISMATCH' to stop this execution path.
        raise RuntimeError("V1_REPLAY_SOURCE_MISMATCH")
    # Set prior to the next item from a lazy sequence of r for r in the result of records(original) plus the
    # result of records(original, 'preflight'); retain entries satisfying r at 'run_id' equals run_id.
    prior = next(r for r in records(original) + records(original, "preflight") if r["run_id"] == run_id)
    # Set provenance to the decoded data produced by json.loads from the text read from (Path(original) / 'runs' /
    # run_id / 'provenance.json').
    provenance = json.loads((Path(original) / "runs" / run_id / "provenance.json").read_text())
    # Set output to the result of Path(output).
    output = Path(output)
    # Run this branch when the negation of whether (output / 'manifest.json') exists.
    if not (output / "manifest.json").exists():
        # Call write_json with the supplied arguments.
        write_json(output / "manifest.json", frozen, exclusive=True)
    # Run this branch when the result of read_checked_manifest(output) differs from frozen.
    if read_checked_manifest(output) != frozen:
        # Raise RuntimeError with the text 'V1_REPLAY_OUTPUT_IDENTITY_MISMATCH' to stop this execution path.
        raise RuntimeError("V1_REPLAY_OUTPUT_IDENTITY_MISMATCH")
    # Call execute with the supplied arguments.
    execute(BY_ID[case_id], prior["method"], frozen, output, suite="panel_replay",
        # Supply gui as the text '--gui' belongs to sys.argv.
        # Supply replay_of as run_id.
        # Supply schedule as the result of restore_schedule(provenance at 'schedule').
        gui="--gui" in sys.argv, replay_of=run_id, schedule=restore_schedule(provenance["schedule"]))

# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Run this branch when the number of entries in sys.argv is less than 7 or sys.argv at 1 differs from the text
    # '--worker'.
    if len(sys.argv) < 7 or sys.argv[1] != "--worker":
        # Raise SystemExit with the text 'Internal archived replay worker; use run_panel_validation.py...' to stop
        # this execution path.
        raise SystemExit("Internal archived replay worker; use run_panel_validation.py --replay")
    # Call worker with the supplied arguments.
    worker()
