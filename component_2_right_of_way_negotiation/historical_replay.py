"""Replay original hashed sources in an isolated process; never rewrite history."""
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import shutil for use in this module.
import shutil
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parent.
BASE=Path(__file__).resolve().parent
# Set _launch to subprocess.run.
_launch=subprocess.run

# Read checked using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Input key: the supplied key.
# Output: value.
# Processing: select branches using the stated conditions.
def _read_checked(path, key):
    # Import digest from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import digest
    # Set value to the decoded data produced by json.loads from the text read from path.
    value=json.loads(path.read_text(encoding="utf-8"))
    # Set checksum to json.loads(path.with_name(path.stem + '.sha256.json').read_text()) at key.
    checksum=json.loads(path.with_name(path.stem+".sha256.json").read_text())[key]
    # Run this branch when the result of digest(value) differs from checksum.
    if digest(value)!=checksum:
        # Raise RuntimeError with the text 'HISTORICAL_REPLAY_CHECKSUM_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_REPLAY_CHECKSUM_MISMATCH")
    # Return value to the caller.
    return value

# Copy only manifest-listed source keys, preserving the original source set.
# Input frozen: the supplied frozen.
# Output: destination.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def materialize(frozen):
    """Copy only manifest-listed source keys, preserving the original source set."""
    # Import digest, file_hash from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import digest,file_hash
    # Run this branch when the result of digest(frozen at 'manifest') differs from frozen at 'manifest_hash'.
    if digest(frozen["manifest"])!=frozen["manifest_hash"]:
        # Raise RuntimeError with the text 'HISTORICAL_MANIFEST_CHECKSUM_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_MANIFEST_CHECKSUM_MISMATCH")
    # Set expected to a dictionary built from frozen['manifest'] at 'source_identities'.
    expected=dict(frozen["manifest"]["source_identities"])
    # Iterate over a tuple containing the text 'panel_source_identities', the text 'panel_sources', the text
    # 'study_sources', binding each item to key.
    for key in ("panel_source_identities","panel_sources","study_sources"):
        # Update expected with the supplied entries.
        expected.update(frozen["manifest"].get(key,{}))
    # Set candidates to a list containing BASE joined with the path segment
    # 'results/naming_migration/pre_migration_runtime', BASE joined with the path segment...
    candidates=[BASE/"results/naming_migration/pre_migration_runtime",
        # Include BASE joined with the path segment 'results/panel_validation_archives/v1/runtime' in this list.
        BASE/"results/panel_validation_archives/v1/runtime",
        # Include BASE joined with the path segment 'results/scalability_validation_archives/v1/runtime' in this list.
        BASE/"results/scalability_validation_archives/v1/runtime",
        # Include BASE joined with the path segment 'results/repair_diagnostics/v1_code_snapshot' in this list.
        BASE/"results/repair_diagnostics/v1_code_snapshot",
        # Include BASE joined with the path segment 'results/repair_diagnostics/v2_code_snapshot' in this list.
        BASE/"results/repair_diagnostics/v2_code_snapshot"]
    # Update candidates to its current value plus a list built from the result of (BASE /
    # 'results/repair_diagnostics/code_snapshots').glob(the text '*').
    candidates+=list((BASE/"results/repair_diagnostics/code_snapshots").glob("*"))
    # Set destination to BASE joined with the path segment 'results/naming_migration/replay_runtimes' divided by frozen at
    # 'manifest_hash'.
    destination=BASE/"results/naming_migration/replay_runtimes"/frozen["manifest_hash"]
    # Iterate over key/value pairs from expected, binding each item to (name, sha).
    for name,sha in expected.items():
        # Set path to destination divided by name.
        path=destination/name
        # Run this branch when the negation of the result of path.resolve().is_relative_to(the result of
        # destination.resolve()).
        if not path.resolve().is_relative_to(destination.resolve()):
            # Raise RuntimeError with the text 'INVALID_HISTORICAL_SOURCE_PATH' to stop this execution path.
            raise RuntimeError("INVALID_HISTORICAL_SOURCE_PATH")
        # Run this branch when whether path is an existing file.
        if path.is_file():
            # Run this branch when the result of file_hash(path) differs from sha.
            if file_hash(path)!=sha:
                # Raise RuntimeError with the text 'HISTORICAL_RUNTIME_COPY_CHANGED' to stop this execution path.
                raise RuntimeError("HISTORICAL_RUNTIME_COPY_CHANGED")
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set chosen to the next item from a lazy sequence of c divided by name for c in candidates; retain
        # entries satisfying whether (c / name) is an existing file and file_hash(c / name) equals sha.
        chosen=next((c/name for c in candidates if (c/name).is_file() and file_hash(c/name)==sha),None)
        # Run this branch when chosen is the same object as None.
        if chosen is None:
            # Raise RuntimeError with the text 'EXACT_HISTORICAL_SOURCE_UNAVAILABLE:' plus name to stop this
            # execution path.
            raise RuntimeError("EXACT_HISTORICAL_SOURCE_UNAVAILABLE:"+name)
        # Create the directory requested by path.parent.
        path.parent.mkdir(parents=True,exist_ok=True)
        # Call shutil.copy2 with the supplied arguments.
        shutil.copy2(chosen,path)
    # Set policy to the result of Path(the text 'results/final_mappo_selection_v2/selected_policy.pt').
    policy=Path("results/final_mappo_selection_v2/selected_policy.pt")
    # Run this branch when the result of file_hash(BASE divided by policy) differs from frozen['manifest'] at
    # 'policy_sha256'.
    if file_hash(BASE/policy)!=frozen["manifest"]["policy_sha256"]:
        # Raise RuntimeError with the text 'HISTORICAL_POLICY_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_POLICY_MISMATCH")
    # Create the directory requested by (destination / policy).parent.
    (destination/policy).parent.mkdir(parents=True,exist_ok=True)
    # Run this branch when the negation of whether (destination / policy) exists.
    if not (destination/policy).exists():
        # Call shutil.copy2 with the supplied arguments.
        shutil.copy2(BASE/policy,destination/policy)
    # Run this branch when the result of file_hash(destination divided by policy) differs from frozen['manifest']
    # at 'policy_sha256'.
    if file_hash(destination/policy)!=frozen["manifest"]["policy_sha256"]:
        # Raise RuntimeError with the text 'HISTORICAL_POLICY_COPY_CHANGED' to stop this execution path.
        raise RuntimeError("HISTORICAL_POLICY_COPY_CHANGED")
    # GUI XML is a display-only asset, absent from older Python source inventories.
    # Set gui to the result of Path(the text 'gui/panel_real_world.xml').
    gui=Path("gui/panel_real_world.xml")
    # Run this branch when the negation of whether (destination / gui) exists.
    if not (destination/gui).exists():
        # Create the directory requested by (destination / gui).parent.
        (destination/gui).parent.mkdir(parents=True,exist_ok=True)
        # Call shutil.copy2 with the supplied arguments.
        shutil.copy2(BASE/gui,destination/gui)
    # Return destination to the caller.
    return destination

# Replay using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input run_id: the supplied run id.
# Input kind: the supplied kind.
# Input gui: the supplied gui.
# Output: the result of _launch(command).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def replay(root, run_id, *, kind="targeted", gui=False):
    # Import digest, file_hash from post_training_evaluation.models for the operations below.
    from post_training_evaluation.models import digest,file_hash
    # Import sumo_version from post_training_evaluation.scenarios for the operations below.
    from post_training_evaluation.scenarios import sumo_version
    # Import platform for use in this module.
    import platform
    # Set root to the result of Path(root).resolve().
    root=Path(root).resolve()
    # Run this branch when Path(run_id).name differs from run_id.
    if Path(run_id).name!=run_id:
        # Raise ValueError with the text 'INVALID_RUN_ID' to stop this execution path.
        raise ValueError("INVALID_RUN_ID")
    # Set manifest to root joined with the path segment 'diagnostic_identity.json' when whether (root /
    # 'diagnostic_identity.json') is an existing file, otherwise the text 'manifest.json'.
    manifest=root/("diagnostic_identity.json" if (root/"diagnostic_identity.json").is_file() else "manifest.json")
    # Set frozen to the decoded data produced by json.loads from the text read from manifest.
    frozen=json.loads(manifest.read_text())
    # Run this branch when 'python_version' from frozen['manifest']; use None if absent differs from the result of
    # platform.python_version() or 'sumo_version' from frozen['manifest']; use None if absent differs from the
    # result of sumo_version().
    if (frozen["manifest"].get("python_version")!=platform.python_version() or
        # Evaluate 'sumo_version' from frozen['manifest']; use None if absent differs from the result of
        # sumo_version() as part of the enclosing expression.
        frozen["manifest"].get("sumo_version")!=sumo_version()):
        # Raise RuntimeError with the text 'HISTORICAL_REPLAY_ENVIRONMENT_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_REPLAY_ENVIRONMENT_MISMATCH")
    # Set directory to root joined with the path segment 'runs' divided by run_id.
    directory=root/"runs"/run_id
    # Set raw to the result of _read_checked(directory joined with the path segment 'result.json', the text 'result_hash').
    raw=_read_checked(directory/"result.json","result_hash")
    # Set prior to the result of _read_checked(directory joined with the path segment 'provenance.json', the text
    # 'provenance_hash').
    prior=_read_checked(directory/"provenance.json","provenance_hash")
    # Run this branch when raw at 'manifest_hash' differs from frozen at 'manifest_hash' or prior at
    # 'manifest_hash' differs from frozen at 'manifest_hash' or the result of digest(prior at 'schedule') differs
    # from raw at 'schedule_hash'.
    if raw["manifest_hash"]!=frozen["manifest_hash"] or prior["manifest_hash"]!=frozen["manifest_hash"] or digest(prior["schedule"])!=raw["schedule_hash"]:
        # Raise RuntimeError with the text 'HISTORICAL_REPLAY_PROVENANCE_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_REPLAY_PROVENANCE_MISMATCH")
    # Set seed to an integer built from digest((frozen['manifest']['protocol_id'],
    # prior['scenario']['scenario_id'], prior['seed'],... sliced by :16 modulo 2 raised to the power 31.
    seed=int(digest((frozen["manifest"]["protocol_id"],prior["scenario"]["scenario_id"],prior["seed"],prior["method"]))[:16],16)%(2**31)
    # Run this branch when 'policy_action_seed' from prior; use None if absent differs from seed or
    # 'policy_action_seed' from raw; use None if absent differs from seed.
    if prior.get("policy_action_seed")!=seed or raw.get("policy_action_seed")!=seed:
        # Raise RuntimeError with the text 'HISTORICAL_REPLAY_SEED_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_REPLAY_SEED_MISMATCH")
    # Iterate over key/value pairs from raw.get('artifact_sha256', {}), binding each item to (name, sha).
    for name,sha in raw.get("artifact_sha256",{}).items():
        # Run this branch when Path(name).name differs from name or the result of file_hash(directory divided by
        # name) differs from sha.
        if Path(name).name!=name or file_hash(directory/name)!=sha:
            # Raise RuntimeError with the text 'HISTORICAL_REPLAY_ARTIFACT_MISMATCH' to stop this execution path.
            raise RuntimeError("HISTORICAL_REPLAY_ARTIFACT_MISMATCH")
    # Set snapshot to the result of materialize(frozen).
    snapshot=materialize(frozen)
    # Set family to the text 'targeted_validation' when kind equals the text 'targeted', otherwise the text
    # 'post_training_evaluation' when kind equals the text 'post_training', otherwise the text
    # 'scalability_validation'.
    family="targeted_validation" if kind=="targeted" else "post_training_evaluation" if kind=="post_training" else "scalability_validation"
    # Set output to BASE joined with the path segment 'results' divided by family joined with the path segment 'replays' divided by frozen at
    # 'manifest_hash'.
    output=BASE/"results"/family/"replays"/frozen["manifest_hash"]
    # Set command to a list containing sys.executable, the text '-B', a string built from the result of
    # Path(__file__).resolve(), the text...
    command=[sys.executable,"-B",str(Path(__file__).resolve()),"--worker",str(snapshot),str(root),str(output),run_id,kind]
    # Run this branch when gui.
    if gui:
        # Append the text '--gui' to command.
        command.append("--gui")
    # Return the result of _launch(command) to the caller.
    return _launch(command,check=True)

# Worker using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def worker():
    # Set (snapshot, original, output, run_id, kind) to sys.argv sliced by 2:7.
    snapshot,original,output,run_id,kind=sys.argv[2:7]
    # Call os.chdir with the supplied arguments.
    os.chdir(snapshot)
    # Call sys.path.insert with the supplied arguments.
    sys.path.insert(0,snapshot)
    # These legacy imports deliberately load the original archived implementation.
    # Import source_identities, restore_schedule, Scenario from final_evaluation.scenarios for the operations
    # below.
    from final_evaluation.scenarios import source_identities,restore_schedule,Scenario
    # Import write_json from final_evaluation.models for the operations below.
    from final_evaluation.models import write_json
    # Set (original, output) to a tuple containing the result of Path(original), the result of Path(output).
    original,output=Path(original),Path(output)
    # Set manifest to original joined with the path segment 'diagnostic_identity.json' when whether (original /
    # 'diagnostic_identity.json') is an existing file, otherwise the text 'manifest.json'.
    manifest=original/("diagnostic_identity.json" if (original/"diagnostic_identity.json").is_file() else "manifest.json")
    # Set frozen to the decoded data produced by json.loads from the text read from manifest.
    frozen=json.loads(manifest.read_text())
    # Run this branch when the result of source_identities() differs from frozen['manifest'] at
    # 'source_identities'.
    if source_identities()!=frozen["manifest"]["source_identities"]:
        # Raise RuntimeError with the text 'HISTORICAL_RUNTIME_SOURCE_SET_MISMATCH' to stop this execution path.
        raise RuntimeError("HISTORICAL_RUNTIME_SOURCE_SET_MISMATCH")
    # Set prior to the decoded data produced by json.loads from the text read from (original / 'runs' / run_id /
    # 'provenance.json').
    prior=json.loads((original/"runs"/run_id/"provenance.json").read_text())
    # Run this branch when the negation of whether (output / 'manifest.json') exists.
    if not (output/"manifest.json").exists():
        # Call write_json with the supplied arguments.
        write_json(output/"manifest.json",frozen,exclusive=True)
    # Run this branch when the decoded data produced by json.loads from the text read from (output /
    # 'manifest.json') differs from frozen.
    elif json.loads((output/"manifest.json").read_text())!=frozen:
        # Raise RuntimeError with the text 'HISTORICAL_REPLAY_OUTPUT_MANIFEST_MISMATCH' to stop this execution
        # path.
        raise RuntimeError("HISTORICAL_REPLAY_OUTPUT_MANIFEST_MISMATCH")
    # Run this branch when kind equals the text 'targeted'.
    if kind=="targeted":
        # Import execute from panel_validation.runner for the operations below.
        from panel_validation.runner import execute
        # Import BY_ID from panel_validation.cases for the operations below.
        from panel_validation.cases import BY_ID
        # Set case to the next item from a lazy sequence of c for c in values from BY_ID; retain entries
        # satisfying c.scenario_id equals prior['scenario'] at 'scenario_id'.
        case=next(c for c in BY_ID.values() if c.scenario_id==prior["scenario"]["scenario_id"])
        # Call execute with the supplied arguments.
        execute(case,prior["method"],frozen,output,suite="panel_replay",gui="--gui" in sys.argv,
                # Supply replay_of as run_id.
                # Supply schedule as the result of restore_schedule(prior at 'schedule').
                replay_of=run_id,schedule=restore_schedule(prior["schedule"]))
    # Run this branch when the result of kind.startswith(the text 'scalability').
    elif kind.startswith("scalability"):
        # Import importlib for use in this module.
        import importlib
        # Set prefix to the text 'scalability_validation.v2' when the result of
        # frozen['manifest']['protocol_id'].endswith(the text 'V2'), otherwise the text 'scalability_validation'.
        prefix="scalability_validation.v2" if frozen["manifest"]["protocol_id"].endswith("V2") else "scalability_validation"
        # Set runner to the result of importlib.import_module(prefix plus the text '.runner').
        runner=importlib.import_module(prefix+".runner")
        # Set cases to the result of importlib.import_module(prefix plus the text '.cases').
        cases=importlib.import_module(prefix+".cases")
        # Set count to prior['scenario'] at 'vehicle_count'.
        count=prior["scenario"]["vehicle_count"]
        # Call runner.execute with the supplied arguments.
        runner.execute(next(c for c in cases.CASES if c.count==count),frozen,output,
            # Supply suite as the text 'scalability_replay'.
            # Supply gui as the text '--gui' belongs to sys.argv.
            # Supply replay_of as run_id.
            suite="scalability_replay",gui="--gui" in sys.argv,replay_of=run_id)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Import run_episode from final_evaluation.runner for the operations below.
        from final_evaluation.runner import run_episode
        # Call run_episode with the supplied arguments.
        run_episode(Scenario(**prior["scenario"]),prior["seed"],prior["method"],frozen,root=output,
            # Supply suite as the text 'replay'.
            # Supply gui as the text '--gui' belongs to sys.argv.
            # Supply schedule as the result of restore_schedule(prior at 'schedule').
            # Supply replay_of as run_id.
            suite="replay",gui="--gui" in sys.argv,schedule=restore_schedule(prior["schedule"]),replay_of=run_id)

# Run this branch when __name__ equals the text '__main__'.
if __name__=="__main__":
    # Run this branch when the number of entries in sys.argv is less than 8 or sys.argv at 1 differs from the text
    # '--worker'.
    if len(sys.argv)<8 or sys.argv[1]!="--worker":
        # Raise SystemExit with the text 'Use the preferred research CLI --replay command.' to stop this execution
        # path.
        raise SystemExit("Use the preferred research CLI --replay command.")
    # Call worker with the supplied arguments.
    worker()
