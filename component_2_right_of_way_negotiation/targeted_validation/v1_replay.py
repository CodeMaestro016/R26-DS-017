"""Verified archived V1 replay; original V1 evidence is never written."""
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
ARCHIVE = BASE / "results/panel_validation_archives/v1"
_launch = subprocess.run

def replay_v1(case_id, root, *, run_id=None, method="PROPOSED_MAPPO", gui=False):
    from final_evaluation.models import digest, file_hash
    from .models import records, read_checked_manifest
    from .cases import BY_ID
    import platform
    from final_evaluation.scenarios import sumo_version
    original_id = "PV-04" if case_id == "PV-04B" else case_id
    if original_id == "PV-04A":
        raise ValueError("PV04A_NOT_IN_V1")
    frozen = read_checked_manifest(root)
    if frozen["manifest"]["python_version"] != platform.python_version() or frozen["manifest"]["sumo_version"] != sumo_version():
        raise RuntimeError("V1_REPLAY_ENVIRONMENT_MISMATCH")
    inventory = json.loads((ARCHIVE / "runtime_inventory.json").read_text(encoding="utf-8-sig"))
    snapshot = (ARCHIVE / "runtime").resolve()
    for name, expected in inventory.items():
        path = (snapshot / name).resolve()
        if not path.is_relative_to(snapshot) or file_hash(path) != expected:
            raise RuntimeError("V1_REPLAY_ARCHIVE_MISMATCH")
    for name, expected in {**frozen["manifest"]["source_identities"], **frozen["manifest"]["panel_source_identities"]}.items():
        if file_hash(snapshot / name) != expected:
            raise RuntimeError("V1_REPLAY_FROZEN_SOURCE_MISMATCH")
    selected = [r for r in records(root) + records(root, "preflight") if
        r["scenario_id"] == BY_ID[original_id].scenario_id and
        (r["run_id"] == run_id if run_id else r["suite"] == "panel" and r["method"] == method)]
    if len(selected) != 1:
        raise RuntimeError("V1_REPLAY_SELECT_EXACT_RUN")
    chosen = selected[0]
    expected_seed = int(digest((frozen["manifest"]["protocol_id"], chosen["scenario_id"], None, chosen["method"]))[:16], 16) % (2**31)
    if chosen["policy_action_seed"] != expected_seed:
        raise RuntimeError("V1_REPLAY_ACTION_SEED_MISMATCH")
    output = BASE / "results/targeted_validation/replays/v1"
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(snapshot),
        str(Path(root).resolve()), str(output), original_id, chosen["run_id"]]
    if gui:
        command.append("--gui")
    return _launch(command, check=True)

def worker():
    snapshot, original, output, case_id, run_id = sys.argv[2:7]
    os.chdir(snapshot)
    sys.path.insert(0, snapshot)
    from panel_validation.runner import execute
    from panel_validation.cases import BY_ID
    from panel_validation.models import read_checked_manifest, records
    from final_evaluation.scenarios import source_identities, restore_schedule
    from final_evaluation.models import write_json
    frozen = read_checked_manifest(original)
    if source_identities() != frozen["manifest"]["source_identities"]:
        raise RuntimeError("V1_REPLAY_SOURCE_MISMATCH")
    prior = next(r for r in records(original) + records(original, "preflight") if r["run_id"] == run_id)
    provenance = json.loads((Path(original) / "runs" / run_id / "provenance.json").read_text())
    output = Path(output)
    if not (output / "manifest.json").exists():
        write_json(output / "manifest.json", frozen, exclusive=True)
    if read_checked_manifest(output) != frozen:
        raise RuntimeError("V1_REPLAY_OUTPUT_IDENTITY_MISMATCH")
    execute(BY_ID[case_id], prior["method"], frozen, output, suite="panel_replay",
        gui="--gui" in sys.argv, replay_of=run_id, schedule=restore_schedule(provenance["schedule"]))

if __name__ == "__main__":
    if len(sys.argv) < 7 or sys.argv[1] != "--worker":
        raise SystemExit("Internal archived replay worker; use run_panel_validation.py --replay")
    worker()
