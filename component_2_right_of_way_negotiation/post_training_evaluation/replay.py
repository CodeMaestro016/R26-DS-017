"""Replay the archived method and exact demand after provenance verification."""
# Import json for use in this module.
import json
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import platform for use in this module.
import platform
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import ROOT, digest, file_hash from .models for the operations below.
from .models import ROOT, digest, file_hash
# Import Scenario, restore_schedule, prepare from .scenarios for the operations below.
from .scenarios import Scenario, restore_schedule, prepare
# Import run_episode from .runner for the operations below.
from .runner import run_episode

# Set DIAGNOSTIC_SOURCE_SNAPSHOT to Path(__file__).resolve().parents at 1 joined with the path segment
# 'results/repair_diagnostics/v2_code_snapshot'.
DIAGNOSTIC_SOURCE_SNAPSHOT = Path(__file__).resolve().parents[1] / "results/repair_diagnostics/v2_code_snapshot"
# Set DIAGNOSTIC_SOURCE_ARCHIVE_ROOT to DIAGNOSTIC_SOURCE_SNAPSHOT.parent joined with the path segment 'code_snapshots'.
DIAGNOSTIC_SOURCE_ARCHIVE_ROOT = DIAGNOSTIC_SOURCE_SNAPSHOT.parent / "code_snapshots"


# Run the measured code, not changed live code, after verifying its copy.
# Input run_id: the supplied run id.
# Input root: the base directory used to resolve files.
# Input frozen: the supplied frozen.
# Input gui: the supplied gui.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _replay_archived_diagnostic(run_id, root, frozen, gui):
    """Run the measured code, not changed live code, after verifying its copy."""
    # Set versioned to DIAGNOSTIC_SOURCE_ARCHIVE_ROOT divided by a string built from 'manifest_hash' from frozen;
    # use the text 'UNKNOWN' if absent.
    versioned = DIAGNOSTIC_SOURCE_ARCHIVE_ROOT / str(frozen.get("manifest_hash", "UNKNOWN"))
    # Set snapshot to the result of (versioned if versioned.is_dir() else DIAGNOSTIC_SOURCE_SNAPSHOT).resolve().
    snapshot = (versioned if versioned.is_dir() else DIAGNOSTIC_SOURCE_SNAPSHOT).resolve()
    # Set inventory_path to snapshot joined with the path segment 'snapshot_inventory.json'.
    inventory_path = snapshot / "snapshot_inventory.json"
    # Run this branch when the negation of whether inventory_path is an existing file.
    if not inventory_path.is_file():
        # Raise RuntimeError with the text 'DIAGNOSTIC_REPLAY_CODE_MISMATCH: archived source copy missing' to stop
        # this execution path.
        raise RuntimeError("DIAGNOSTIC_REPLAY_CODE_MISMATCH: archived source copy missing")
    # Set inventory to the decoded data produced by json.loads from the text read from inventory_path.
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    # Iterate over key/value pairs from inventory, binding each item to (relative, expected).
    for relative, expected in inventory.items():
        # Set path to the result of (snapshot / relative).resolve().
        path = (snapshot / relative).resolve()
        # Run this branch when the negation of the result of path.is_relative_to(snapshot) or the negation of
        # whether path is an existing file or the result of file_hash(path) differs from the result of
        # expected.lower().
        if not path.is_relative_to(snapshot) or not path.is_file() or file_hash(path) != expected.lower():
            # Raise RuntimeError with the text 'DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH' to stop this execution path.
            raise RuntimeError("DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH")
    # Iterate over key/value pairs from frozen['manifest']['source_identities'], binding each item to (relative,
    # expected).
    for relative, expected in frozen["manifest"]["source_identities"].items():
        # Run this branch when the result of file_hash(snapshot divided by relative) differs from expected.
        if file_hash(snapshot / relative) != expected:
            # Raise RuntimeError with the text 'DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH' to stop this execution path.
            raise RuntimeError("DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH")
    # Set command to a list containing sys.executable, the text '-B', a string built from snapshot divided by the
    # text 'run_final_evaluation.py',...
    command = [sys.executable, "-B", str(snapshot / "run_final_evaluation.py"),
        # Include a string built from the result of Path(root).resolve() in this list.
        "--replay", run_id, "--output-root", str(Path(root).resolve())]
    # Run this branch when gui.
    if gui:
        # Append the text '--gui' to command.
        command.append("--gui")
    # Display the text 'Replaying verified archived diagnostic source:'.
    print("Replaying verified archived diagnostic source:", snapshot)
    # Call subprocess.run with the supplied arguments.
    subprocess.run(command, check=True)

# Replay using the inputs and processing steps below.
# Input run_id: the supplied run id.
# Input gui: the supplied gui.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def replay(run_id, *, gui=False, root=ROOT):
    # Run this branch when the negation of run_id or Path(run_id).name differs from run_id or whether any item is
    # true in a lazy sequence of c does not belong to '0123456789TZ_abcdef' for c in run_id.
    if not run_id or Path(run_id).name != run_id or any(c not in "0123456789TZ_abcdef" for c in run_id):
        # Raise ValueError with the text 'INVALID_RUN_ID' to stop this execution path.
        raise ValueError("INVALID_RUN_ID")
    # Set identity to the result of Path(root) joined with the path segment 'diagnostic_identity.json' when whether
    # (Path(root) / 'diagnostic_identity.json') exists, otherwise the text 'manifest.json'.
    identity = Path(root) / ("diagnostic_identity.json" if (Path(root)/"diagnostic_identity.json").exists() else "manifest.json")
    # Run this branch when whether identity is an existing file.
    if identity.is_file():
        # Set saved to the decoded data produced by json.loads from the text read from identity.
        saved = json.loads(identity.read_text())
        # Run this branch when whether any item is true in a lazy sequence of the result of k.startswith(the text
        # 'panel_demo/') for k in saved['manifest'] at 'source_identities'.
        if any(k.startswith("panel_demo/") for k in saved["manifest"]["source_identities"]):
            # Import replay as archived_replay from historical_replay for the operations below.
            from historical_replay import replay as archived_replay
            # Return the result of archived_replay(root, run_id) to the caller.
            return archived_replay(root,run_id,kind="post_training",gui=gui)
    # Set diagnostic_path to the result of Path(root) joined with the path segment 'diagnostic_identity.json'.
    diagnostic_path = Path(root) / "diagnostic_identity.json"
    # Run this branch when whether diagnostic_path exists.
    if diagnostic_path.exists():
        # Import source_identities, sumo_version from .scenarios for the operations below.
        from .scenarios import source_identities, sumo_version
        # Set frozen to the decoded data produced by json.loads from the text read from diagnostic_path.
        frozen = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        # Run this branch when 'sumo_version' from frozen['manifest']; use None if absent differs from the result
        # of sumo_version() or 'python_version' from frozen['manifest']; use None if absent differs from the
        # result of platform.python_version().
        if (frozen["manifest"].get("sumo_version") != sumo_version() or
                # Evaluate 'python_version' from frozen['manifest']; use None if absent differs from the result of
                # platform.python_version() as part of the enclosing expression.
                frozen["manifest"].get("python_version") != platform.python_version()):
            # Raise RuntimeError with the text 'DIAGNOSTIC_REPLAY_ENVIRONMENT_MISMATCH' to stop this execution
            # path.
            raise RuntimeError("DIAGNOSTIC_REPLAY_ENVIRONMENT_MISMATCH")
        # Run this branch when the result of source_identities() differs from frozen['manifest'] at
        # 'source_identities'.
        if source_identities() != frozen["manifest"]["source_identities"]:
            # Run this branch when frozen at 'manifest_hash' differs from the result of digest(frozen at
            # 'manifest').
            if frozen["manifest_hash"] != digest(frozen["manifest"]):
                # Raise RuntimeError with the text 'DIAGNOSTIC_IDENTITY_MISMATCH' to stop this execution path.
                raise RuntimeError("DIAGNOSTIC_IDENTITY_MISMATCH")
            # Return the result of _replay_archived_diagnostic(run_id, root, frozen, gui) to the caller.
            return _replay_archived_diagnostic(run_id,root,frozen,gui)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set frozen to the result of prepare(root).
        frozen = prepare(root)
    # Set directory to the result of Path(root) joined with the path segment 'runs' divided by run_id.
    directory = Path(root) / "runs" / run_id
    # Set provenance to the decoded data produced by json.loads from the text read from (directory /
    # 'provenance.json').
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    # Set checksum to the decoded data produced by json.loads from the text read from (directory /
    # 'provenance.sha256.json').
    checksum = json.loads((directory / "provenance.sha256.json").read_text(encoding="utf-8"))
    # Run this branch when checksum at 'provenance_hash' differs from the result of digest(provenance).
    if checksum["provenance_hash"] != digest(provenance):
        # Raise RuntimeError with the text 'REPLAY_PROVENANCE_MISMATCH' to stop this execution path.
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    # Run this branch when provenance at 'manifest_hash' differs from frozen at 'manifest_hash' or the result of
    # digest(provenance at 'schedule') differs from provenance at 'schedule_hash'.
    if provenance["manifest_hash"] != frozen["manifest_hash"] or digest(provenance["schedule"]) != provenance["schedule_hash"]:
        # Raise RuntimeError with the text 'REPLAY_PROVENANCE_MISMATCH' to stop this execution path.
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    # Run this branch when the text 'policy_action_seed' belongs to provenance.
    if "policy_action_seed" in provenance:
        # Set expected_seed to an integer built from digest((frozen['manifest']['protocol_id'],
        # provenance['scenario']['scenario_id'],... sliced by :16 modulo 2 raised to the power 31.
        expected_seed = int(digest((frozen["manifest"]["protocol_id"],
            # Include provenance['scenario'] at 'scenario_id' in this tuple.
            provenance["scenario"]["scenario_id"], provenance["seed"], provenance["method"]))[:16],16) % (2**31)
        # Run this branch when expected_seed differs from provenance at 'policy_action_seed'.
        if expected_seed != provenance["policy_action_seed"]:
            # Raise RuntimeError with the text 'REPLAY_POLICY_ACTION_SEED_MISMATCH' to stop this execution path.
            raise RuntimeError("REPLAY_POLICY_ACTION_SEED_MISMATCH")
    # Return the result of run_episode(the result of Scenario(), provenance at 'seed', provenance at 'method',
    # frozen) to the caller.
    return run_episode(Scenario(**provenance["scenario"]), provenance["seed"],
        # Supply root as root.
        # Supply suite as the text 'replay'.
        # Supply gui as gui.
        provenance["method"], frozen, root=root, suite="replay", gui=gui,
        # Supply schedule as the result of restore_schedule(provenance at 'schedule').
        # Supply replay_of as run_id.
        schedule=restore_schedule(provenance["schedule"]), replay_of=run_id)
