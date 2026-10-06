"""Replay the archived method and exact demand after provenance verification."""
import json
from pathlib import Path
from .models import ROOT, digest
from .scenarios import Scenario, restore_schedule, prepare
from .runner import run_episode

def replay(run_id, *, gui=False, root=ROOT):
    if not run_id or Path(run_id).name != run_id or any(c not in "0123456789TZ_abcdef" for c in run_id):
        raise ValueError("INVALID_RUN_ID")
    frozen = prepare(root)
    directory = Path(root) / "runs" / run_id
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    checksum = json.loads((directory / "provenance.sha256.json").read_text(encoding="utf-8"))
    if checksum["provenance_hash"] != digest(provenance):
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    if provenance["manifest_hash"] != frozen["manifest_hash"] or digest(provenance["schedule"]) != provenance["schedule_hash"]:
        raise RuntimeError("REPLAY_PROVENANCE_MISMATCH")
    return run_episode(Scenario(**provenance["scenario"]), provenance["seed"],
        provenance["method"], frozen, root=root, suite="replay", gui=gui,
        schedule=restore_schedule(provenance["schedule"]), replay_of=run_id)
