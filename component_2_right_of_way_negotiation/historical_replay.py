"""Replay original hashed sources in an isolated process; never rewrite history."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE=Path(__file__).resolve().parent
_launch=subprocess.run

def _read_checked(path, key):
    from post_training_evaluation.models import digest
    value=json.loads(path.read_text(encoding="utf-8"))
    checksum=json.loads(path.with_name(path.stem+".sha256.json").read_text())[key]
    if digest(value)!=checksum:
        raise RuntimeError("HISTORICAL_REPLAY_CHECKSUM_MISMATCH")
    return value

def materialize(frozen):
    """Copy only manifest-listed source keys, preserving the original source set."""
    from post_training_evaluation.models import digest,file_hash
    if digest(frozen["manifest"])!=frozen["manifest_hash"]:
        raise RuntimeError("HISTORICAL_MANIFEST_CHECKSUM_MISMATCH")
    expected=dict(frozen["manifest"]["source_identities"])
    for key in ("panel_source_identities","panel_sources","study_sources"):
        expected.update(frozen["manifest"].get(key,{}))
    candidates=[BASE/"results/naming_migration/pre_migration_runtime",
        BASE/"results/panel_validation_archives/v1/runtime",
        BASE/"results/scalability_validation_archives/v1/runtime",
        BASE/"results/repair_diagnostics/v1_code_snapshot",
        BASE/"results/repair_diagnostics/v2_code_snapshot"]
    candidates+=list((BASE/"results/repair_diagnostics/code_snapshots").glob("*"))
    destination=BASE/"results/naming_migration/replay_runtimes"/frozen["manifest_hash"]
    for name,sha in expected.items():
        path=destination/name
        if not path.resolve().is_relative_to(destination.resolve()):
            raise RuntimeError("INVALID_HISTORICAL_SOURCE_PATH")
        if path.is_file():
            if file_hash(path)!=sha:
                raise RuntimeError("HISTORICAL_RUNTIME_COPY_CHANGED")
            continue
        chosen=next((c/name for c in candidates if (c/name).is_file() and file_hash(c/name)==sha),None)
        if chosen is None:
            raise RuntimeError("EXACT_HISTORICAL_SOURCE_UNAVAILABLE:"+name)
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(chosen,path)
    policy=Path("results/final_mappo_selection_v2/selected_policy.pt")
    if file_hash(BASE/policy)!=frozen["manifest"]["policy_sha256"]:
        raise RuntimeError("HISTORICAL_POLICY_MISMATCH")
    (destination/policy).parent.mkdir(parents=True,exist_ok=True)
    if not (destination/policy).exists():
        shutil.copy2(BASE/policy,destination/policy)
    if file_hash(destination/policy)!=frozen["manifest"]["policy_sha256"]:
        raise RuntimeError("HISTORICAL_POLICY_COPY_CHANGED")
    # GUI XML is a display-only asset, absent from older Python source inventories.
    gui=Path("gui/panel_real_world.xml")
    if not (destination/gui).exists():
        (destination/gui).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(BASE/gui,destination/gui)
    return destination

def replay(root, run_id, *, kind="targeted", gui=False):
    from post_training_evaluation.models import digest,file_hash
    from post_training_evaluation.scenarios import sumo_version
    import platform
    root=Path(root).resolve()
    if Path(run_id).name!=run_id:
        raise ValueError("INVALID_RUN_ID")
    manifest=root/("diagnostic_identity.json" if (root/"diagnostic_identity.json").is_file() else "manifest.json")
    frozen=json.loads(manifest.read_text())
    if (frozen["manifest"].get("python_version")!=platform.python_version() or
        frozen["manifest"].get("sumo_version")!=sumo_version()):
        raise RuntimeError("HISTORICAL_REPLAY_ENVIRONMENT_MISMATCH")
    directory=root/"runs"/run_id
    raw=_read_checked(directory/"result.json","result_hash")
    prior=_read_checked(directory/"provenance.json","provenance_hash")
    if raw["manifest_hash"]!=frozen["manifest_hash"] or prior["manifest_hash"]!=frozen["manifest_hash"] or digest(prior["schedule"])!=raw["schedule_hash"]:
        raise RuntimeError("HISTORICAL_REPLAY_PROVENANCE_MISMATCH")
    seed=int(digest((frozen["manifest"]["protocol_id"],prior["scenario"]["scenario_id"],prior["seed"],prior["method"]))[:16],16)%(2**31)
    if prior.get("policy_action_seed")!=seed or raw.get("policy_action_seed")!=seed:
        raise RuntimeError("HISTORICAL_REPLAY_SEED_MISMATCH")
    for name,sha in raw.get("artifact_sha256",{}).items():
        if Path(name).name!=name or file_hash(directory/name)!=sha:
            raise RuntimeError("HISTORICAL_REPLAY_ARTIFACT_MISMATCH")
    snapshot=materialize(frozen)
    family="targeted_validation" if kind=="targeted" else "post_training_evaluation" if kind=="post_training" else "scalability_validation"
    output=BASE/"results"/family/"replays"/frozen["manifest_hash"]
    command=[sys.executable,"-B",str(Path(__file__).resolve()),"--worker",str(snapshot),str(root),str(output),run_id,kind]
    if gui:
        command.append("--gui")
    return _launch(command,check=True)

def worker():
    snapshot,original,output,run_id,kind=sys.argv[2:7]
    os.chdir(snapshot)
    sys.path.insert(0,snapshot)
    # These legacy imports deliberately load the original archived implementation.
    from final_evaluation.scenarios import source_identities,restore_schedule,Scenario
    from final_evaluation.models import write_json
    original,output=Path(original),Path(output)
    manifest=original/("diagnostic_identity.json" if (original/"diagnostic_identity.json").is_file() else "manifest.json")
    frozen=json.loads(manifest.read_text())
    if source_identities()!=frozen["manifest"]["source_identities"]:
        raise RuntimeError("HISTORICAL_RUNTIME_SOURCE_SET_MISMATCH")
    prior=json.loads((original/"runs"/run_id/"provenance.json").read_text())
    if not (output/"manifest.json").exists():
        write_json(output/"manifest.json",frozen,exclusive=True)
    elif json.loads((output/"manifest.json").read_text())!=frozen:
        raise RuntimeError("HISTORICAL_REPLAY_OUTPUT_MANIFEST_MISMATCH")
    if kind=="targeted":
        from panel_validation.runner import execute
        from panel_validation.cases import BY_ID
        case=next(c for c in BY_ID.values() if c.scenario_id==prior["scenario"]["scenario_id"])
        execute(case,prior["method"],frozen,output,suite="panel_replay",gui="--gui" in sys.argv,
                replay_of=run_id,schedule=restore_schedule(prior["schedule"]))
    elif kind.startswith("scalability"):
        import importlib
        prefix="scalability_validation.v2" if frozen["manifest"]["protocol_id"].endswith("V2") else "scalability_validation"
        runner=importlib.import_module(prefix+".runner")
        cases=importlib.import_module(prefix+".cases")
        count=prior["scenario"]["vehicle_count"]
        runner.execute(next(c for c in cases.CASES if c.count==count),frozen,output,
            suite="scalability_replay",gui="--gui" in sys.argv,replay_of=run_id)
    else:
        from final_evaluation.runner import run_episode
        run_episode(Scenario(**prior["scenario"]),prior["seed"],prior["method"],frozen,root=output,
            suite="replay",gui="--gui" in sys.argv,schedule=restore_schedule(prior["schedule"]),replay_of=run_id)

if __name__=="__main__":
    if len(sys.argv)<8 or sys.argv[1]!="--worker":
        raise SystemExit("Use the preferred research CLI --replay command.")
    worker()
