"""Replay the archived method and exact demand after provenance verification."""
import json
import subprocess
import sys
import platform
from pathlib import Path
from .models import ROOT, digest, file_hash
from .scenarios import Scenario, restore_schedule, prepare
from .runner import run_episode

DIAGNOSTIC_SOURCE_SNAPSHOT = Path(__file__).resolve().parents[1] / "results/repair_diagnostics/v2_code_snapshot"
DIAGNOSTIC_SOURCE_ARCHIVE_ROOT = DIAGNOSTIC_SOURCE_SNAPSHOT.parent / "code_snapshots"


def _replay_archived_diagnostic(run_id, root, frozen, gui):
    """Run the measured code, not changed live code, after verifying its copy."""
    versioned = DIAGNOSTIC_SOURCE_ARCHIVE_ROOT / str(frozen.get("manifest_hash", "UNKNOWN"))
    snapshot = (versioned if versioned.is_dir() else DIAGNOSTIC_SOURCE_SNAPSHOT).resolve()
    inventory_path = snapshot / "snapshot_inventory.json"
    if not inventory_path.is_file():
        raise RuntimeError("DIAGNOSTIC_REPLAY_CODE_MISMATCH: archived source copy missing")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    for relative, expected in inventory.items():
        path = (snapshot / relative).resolve()
        if not path.is_relative_to(snapshot) or not path.is_file() or file_hash(path) != expected.lower():
            raise RuntimeError("DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH")
    for relative, expected in frozen["manifest"]["source_identities"].items():
        if file_hash(snapshot / relative) != expected:
            raise RuntimeError("DIAGNOSTIC_SOURCE_SNAPSHOT_MISMATCH")
    command = [sys.executable, "-B", str(snapshot / "run_final_evaluation.py"),
        "--replay", run_id, "--output-root", str(Path(root).resolve())]
    if gui:
        command.append("--gui")
    print("Replaying verified archived diagnostic source:", snapshot)
    subprocess.run(command, check=True)

def replay(run_id, *, gui=False, root=ROOT):
    if not run_id or Path(run_id).name != run_id or any(c not in "0123456789TZ_abcdef" for c in run_id):
        raise ValueError("INVALID_RUN_ID")
    identity = Path(root) / ("diagnostic_identity.json" if (Path(root)/"diagnostic_identity.json").exists() else "manifest.json")
    if identity.is_file():
        saved = json.loads(identity.read_text())
        if any(k.startswith("panel_demo/") for k in saved["manifest"]["source_identities"]):
            from historical_replay import replay as archived_replay
            return archived_replay(root,run_id,kind="post_training",gui=gui)
    diagnostic_path = Path(root) / "diagnostic_identity.json"
    if diagnostic_path.exists():
        from .scenarios import source_identities, sumo_version
        frozen = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        if (frozen["manifest"].get("sumo_version") != sumo_version() or
                frozen["manifest"].get("python_version") != platform.python_version()):
            raise RuntimeError("DIAGNOSTIC_REPLAY_ENVIRONMENT_MISMATCH")
        if source_identities() != frozen["manifest"]["source_identities"]:
            if frozen["manifest_hash"] != digest(frozen["manifest"]):
                raise RuntimeError("DIAGNOSTIC_IDENTITY_MISMATCH")
            return _replay_archived_diagnostic(run_id,root,frozen,gui)
    else:
        frozen = prepare(root)
    directory = Path(root) / "runs" / run_id
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    checksum = json.loads((directory / "provenance.sha256.json").read_text(encoding="utf-8"))
    if checksum["provenance_hash"] != digest(provenance):
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    if provenance["manifest_hash"] != frozen["manifest_hash"] or digest(provenance["schedule"]) != provenance["schedule_hash"]:
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    if "policy_action_seed" in provenance:
        expected_seed = int(digest((frozen["manifest"]["protocol_id"],
            provenance["scenario"]["scenario_id"], provenance["seed"], provenance["method"]))[:16],16) % (2**31)
        if expected_seed != provenance["policy_action_seed"]:
            raise RuntimeError("REPLAY_POLICY_ACTION_SEED_MISMATCH")
    return run_episode(Scenario(**provenance["scenario"]), provenance["seed"],
        provenance["method"], frozen, root=root, suite="replay", gui=gui,
        schedule=restore_schedule(provenance["schedule"]), replay_of=run_id)
