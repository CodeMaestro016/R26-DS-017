"""Read-only research audit; writes a separate readiness evidence family only."""
# Import hashlib for use in this module.
import hashlib
# Import importlib.metadata for use in this module.
import importlib.metadata
# Import json for use in this module.
import json
# Import platform for use in this module.
import platform
# Import shutil for use in this module.
import shutil
# Import sys for use in this module.
import sys
# Import Counter from collections for the operations below.
from collections import Counter
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'

# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from value.
# Processing: iterate over the relevant records.
def sha(path):
    # Set value to the result of hashlib.sha256().
    value=hashlib.sha256()
    # Enter the result of path.open(the text 'rb') as handle and run the enclosed operations within that context.
    with path.open('rb') as handle:
        # Iterate over the result of iter(a callback that returns the result of handle.read(1024 multiplied by
        # 1024), b''), binding each item to chunk.
        # Update value with the supplied entries.
        for chunk in iter(lambda:handle.read(1024*1024),b''): value.update(chunk)
    # Return the hexadecimal digest from value to the caller.
    return value.hexdigest()

# Digest using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the result of hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),...().
def digest(value):
    # Return the result of hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),...() to the
    # caller.
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
def read(path):
    # Return the decoded data produced by json.loads from the text read from path to the caller.
    return json.loads(path.read_text(encoding='utf-8-sig'))

# Verify run using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Input frozen: the supplied frozen.
# Output: a tuple containing raw, errors.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def verify_run(path,frozen):
    # Set raw to the result of read(path).
    # Set errors to an empty list.
    raw=read(path); errors=[]
    # Iterate over a list containing a tuple containing the text 'result', the text 'result_hash', a tuple
    # containing the text 'provenance',..., binding each item to (name, key).
    for name,key in [('result','result_hash'),('provenance','provenance_hash')]:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set value to the result of read(the result of path.with_name(name plus the text '.json')).
            value=read(path.with_name(name+'.json'))
            # Run this branch when the result of digest(value) differs from read(path.with_name(name +
            # '.sha256.json')) at key.
            # Append name plus the text '_checksum' to errors.
            if digest(value)!=read(path.with_name(name+'.sha256.json'))[key]: errors.append(name+'_checksum')
        # Handle (OSError, ValueError, KeyError) as exc using the recovery steps below.
        # Append name plus the text ':' plus a string built from exc to errors.
        except (OSError,ValueError,KeyError) as exc: errors.append(name+':'+str(exc))
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Set provenance to the result of read(the result of path.with_name(the text 'provenance.json')).
        provenance=read(path.with_name('provenance.json'))
        # Run this branch when raw at 'manifest_hash' differs from frozen at 'manifest_hash' or provenance at
        # 'manifest_hash' differs from frozen at 'manifest_hash'.
        # Append the text 'manifest_identity' to errors.
        if raw['manifest_hash']!=frozen['manifest_hash'] or provenance['manifest_hash']!=frozen['manifest_hash']: errors.append('manifest_identity')
        # Run this branch when the result of digest(provenance at 'schedule') differs from raw at 'schedule_hash'
        # or provenance at 'schedule_hash' differs from raw at 'schedule_hash'.
        # Append the text 'schedule_hash' to errors.
        if digest(provenance['schedule'])!=raw['schedule_hash'] or provenance['schedule_hash']!=raw['schedule_hash']: errors.append('schedule_hash')
        # Iterate over key/value pairs from raw.get('artifact_sha256', {}), binding each item to (name, expected).
        for name,expected in raw.get('artifact_sha256',{}).items():
            # Run this branch when Path(name).name differs from name or the result of sha(path.parent divided by
            # name) differs from expected.
            # Append the text 'artifact:' plus name to errors.
            if Path(name).name!=name or sha(path.parent/name)!=expected: errors.append('artifact:'+name)
    # Handle (OSError, ValueError, KeyError) as exc using the recovery steps below.
    # Append the text 'artifacts:' plus a string built from exc to errors.
    except (OSError,ValueError,KeyError) as exc: errors.append('artifacts:'+str(exc))
    # Return a tuple containing raw, errors to the caller.
    return raw,errors

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=True)
    # Inventory immutable results before any test or UI work.
    # Set inventory to an empty dictionary.
    inventory={}
    # Iterate over the result of (BASE / 'results').rglob(the text '*'), binding each item to path.
    for path in (BASE/'results').rglob('*'):
        # Run this branch when whether path is an existing file and OUT.parent does not belong to path.parents and
        # the text '__pycache__' does not belong to path.parts.
        if path.is_file() and OUT.parent not in path.parents and '__pycache__' not in path.parts:
            # Set inventory[str(path.relative_to(BASE))] to a dictionary built from the supplied values.
            inventory[str(path.relative_to(BASE))]=dict(sha256=sha(path),bytes=path.stat().st_size)
    # Write the supplied text to (OUT / 'historical_inventory.json').
    (OUT/'historical_inventory.json').write_text(json.dumps(inventory,indent=2))
    # Set protected to an empty dictionary.
    protected={}
    # Iterate over a list containing the text 'runtime_simulation', the text 'post_training_evaluation', the text
    # 'targeted_validation', the..., binding each item to folder.
    for folder in ['runtime_simulation','post_training_evaluation','targeted_validation','scalability_validation','negotiation_execution','negotiation_learning','negotiation_training','traffic_rules','conflict','networks','models']:
        # Iterate over the result of (BASE / folder).rglob(the text '*'), binding each item to path.
        for path in (BASE/folder).rglob('*'):
            # Run this branch when whether path is an existing file and the text '__pycache__' does not belong to
            # path.parts.
            if path.is_file() and '__pycache__' not in path.parts:
                # Set protected[str(path.relative_to(BASE))] to the result of sha(path).
                protected[str(path.relative_to(BASE))]=sha(path)
    # Set protected['config.py'] to the result of sha(BASE joined with the path segment 'config.py').
    protected['config.py']=sha(BASE/'config.py')
    # Write the supplied text to (OUT / 'protected_source_inventory.json').
    (OUT/'protected_source_inventory.json').write_text(json.dumps(protected,indent=2))
    # Set families to an empty list.
    families=[]
    # Set roots to a list containing the text 'results/final_evaluation', the text
    # 'results/final_evaluation_development', the text...
    roots=['results/final_evaluation','results/final_evaluation_development','results/final_evaluation/v2_candidate',
        'results/post_training_evaluation/v2_candidate','results/panel_validation/v1','results/panel_validation/v2',
        'results/targeted_validation/v2','results/scalability_validation/v1','results/scalability_validation/v2']
    # Iterate over roots, binding each item to relative.
    for relative in roots:
        # Set root to BASE divided by relative.
        # Set manifest to root joined with the path segment 'manifest.json'.
        root=BASE/relative;manifest=root/'manifest.json'
        # Run this branch when the negation of whether manifest exists.
        if not manifest.exists():
            # Append a dictionary built from the supplied values to families.
            # Skip the rest of this loop iteration and process the next item.
            families.append(dict(root=relative,manifest_present=False));continue
        # Set frozen to the result of read(manifest).
        # Set m to frozen at 'manifest'.
        # Set runs to an empty list.
        frozen=read(manifest);m=frozen['manifest'];runs=[]
        # Iterate over the sorted values from the result of (root / 'runs').glob(the text '*/result.json'),
        # binding each item to path.
        for path in sorted((root/'runs').glob('*/result.json')):
            # Set (raw, errors) to the result of verify_run(path, frozen).
            raw,errors=verify_run(path,frozen)
            # Append a dictionary built from the supplied values to runs.
            runs.append(dict(path=str(path.relative_to(BASE)),run_id=raw['run_id'],suite=raw['suite'],method=raw['method'],
                # Supply scenario_id as raw at 'scenario_id'.
                # Supply seed as 'seed' from raw; use None if absent.
                # Supply classification as raw at 'classification'.
                # Supply verification_errors as errors.
                scenario_id=raw['scenario_id'],seed=raw.get('seed'),classification=raw['classification'],verification_errors=errors,
                # Supply metrics as raw at 'metrics'.
                # Supply integrity as 'integrity' from raw; use an empty dictionary if absent.
                # Supply wall_clock_seconds as 'wall_clock_seconds' from raw; use None if absent.
                metrics=raw['metrics'],integrity=raw.get('integrity',{}),wall_clock_seconds=raw.get('wall_clock_seconds'),
                # Supply error as 'error' from raw; use None if absent.
                # Supply schedule_hash as raw at 'schedule_hash'.
                error=raw.get('error'),schedule_hash=raw['schedule_hash']))
        # Set by_suite to a dictionary of suite mapped to a dictionary built from the supplied values for suite in
        # the sorted values from a set of r at 'suite' for r in runs.
        by_suite={suite:dict(recorded=sum(r['suite']==suite for r in runs),verified=sum(r['suite']==suite and not r['verification_errors'] for r in runs),
            # Supply outcomes as a dictionary built from the result of Counter(a lazy sequence of r at
            # 'classification' for r in runs; retain entries satisfying r['suite'] ==...).
            outcomes=dict(Counter(r['classification'] for r in runs if r['suite']==suite and not r['verification_errors']))) for suite in sorted({r['suite'] for r in runs})}
        # Set current_bad to a list of name for (name, expected) in key/value pairs from
        # m.get('source_identities', {}); retain entries satisfying the negation of whether (BASE / name) is an
        # existing file or the result of sha(BASE /...
        current_bad=[name for name,expected in m.get('source_identities',{}).items() if not (BASE/name).is_file() or sha(BASE/name)!=expected]
        # Set expected to an empty set.
        expected=set()
        # Run this branch when 'scenarios' from m; use None if absent and 'methods' from m; use None if absent and
        # 'seeds' from m; use None if absent.
        if m.get('scenarios') and m.get('methods') and m.get('seeds'):
            # Iterate over m at 'scenarios', binding each item to scenario.
            for scenario in m['scenarios']:
                # Iterate over m at 'seeds' when 'continuous' from scenario; use None if absent, otherwise a list
                # containing None, binding each item to seed.
                for seed in m['seeds'] if scenario.get('continuous') else [None]:
                    # Iterate over m at 'methods', binding each item to method.
                    # Add a tuple containing scenario at 'scenario_id', seed, method to expected.
                    for method in m['methods']: expected.add((scenario['scenario_id'],seed,method))
        # Set actual to a set of a tuple containing r at 'scenario_id', r at 'seed', r at 'method' for r in runs;
        # retain entries satisfying r at 'suite' equals the text 'final' and the negation of r at
        # 'verification_errors'.
        actual={(r['scenario_id'],r['seed'],r['method']) for r in runs if r['suite']=='final' and not r['verification_errors']}
        # Append a dictionary built from the supplied values to families.
        families.append(dict(root=relative,manifest_present=True,manifest_hash=frozen['manifest_hash'],manifest_checksum_valid=digest(m)==frozen['manifest_hash'],
            # Supply protocol_id as 'protocol_id' from m; use None if absent.
            # Supply policy_sha256 as 'policy_sha256' from m; use None if absent.
            # Supply inference_mode as 'inference_mode' from m; use None if absent.
            # Supply seeds as 'seeds' from m; use None if absent.
            protocol_id=m.get('protocol_id'),policy_sha256=m.get('policy_sha256'),inference_mode=m.get('inference_mode'),seeds=m.get('seeds'),
            # Supply current_source_mismatches as current_bad.
            # Supply suites as by_suite.
            # Supply expected_final_episodes as the number of entries in expected or None.
            current_source_mismatches=current_bad,suites=by_suite,expected_final_episodes=len(expected) or None,
            # Supply verified_final_keys as the number of entries in actual.
            # Supply missing_final_keys as the sorted values from expected minus actual.
            # Supply runs as runs.
            # Supply key as str.
            verified_final_keys=len(actual),missing_final_keys=sorted(expected-actual,key=str),runs=runs))
    # Set presentations to an empty list.
    presentations=[]
    # Iterate over a list containing the text 'results/panel_demo', the text 'results/runtime_simulation', binding
    # each item to relative.
    for relative in ['results/panel_demo','results/runtime_simulation']:
        # Set root to BASE divided by relative.
        root=BASE/relative
        # Set paths to a list built from the result of root.glob('**/run_*.json') plus a list built from the
        # result of root.glob('**/latest*demo.json') plus a list built from the result of root.glob(the text
        # '**/latest*simulation.json').
        paths=list(root.glob('**/run_*.json'))+list(root.glob('**/latest*demo.json'))+list(root.glob('**/latest*simulation.json'))
        # Iterate over the sorted values from a set built from paths, binding each item to path.
        for path in sorted(set(paths)):
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Set raw to the result of read(path).
            try: raw=read(path)
            # Handle (OSError, ValueError) using the recovery steps below.
            # Skip the rest of this loop iteration and process the next item.
            except (OSError,ValueError): continue
            # Run this branch when 'presentation_scenario_id' from raw; use 'scenario_id' from raw; use None if
            # absent if absent differs from the text 'congested_four_approach'.
            # Skip the rest of this loop iteration and process the next item.
            if raw.get('presentation_scenario_id',raw.get('scenario_id'))!='congested_four_approach': continue
            # Append a dictionary built from the supplied values to presentations.
            presentations.append(dict(path=str(path.relative_to(BASE)),bytes=path.stat().st_size,record=raw))
    # Set packages to an empty dictionary.
    packages={}
    # Iterate over a list containing the text 'pytest', the text 'torch', the text 'numpy', the text 'nicegui',
    # the text 'pywebview', the text..., binding each item to name.
    for name in ['pytest','torch','numpy','nicegui','pywebview','traci','sumolib','onnxruntime','shapely','matplotlib','psutil']:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        # Set packages[name] to the result of importlib.metadata.version(name).
        try: packages[name]=importlib.metadata.version(name)
        # Handle importlib.metadata.PackageNotFoundError using the recovery steps below.
        # Set packages[name] to None.
        except importlib.metadata.PackageNotFoundError: packages[name]=None
    # Set gates to an empty dictionary.
    gates={}
    # Set gate to BASE joined with the path segment 'results/repair_diagnostics/validation_summary.json'.
    gate=BASE/'results/repair_diagnostics/validation_summary.json'
    # Run this branch when whether gate exists.
    if gate.exists():
        # Set raw to the result of read(gate).
        raw=read(gate)
        # Set gates to a dictionary of k mapped to v for (k, v) in key/value pairs from raw; retain entries
        # satisfying k does not belong to a list containing 'diagnostic_batches', 'diagnostics', 'runs',...
        gates={k:v for k,v in raw.items() if k not in ['diagnostic_batches','diagnostics','runs','cases'] and not isinstance(v,list)}
    # Set policy to BASE joined with the path segment 'results/final_mappo_selection_v2/selected_policy.pt'.
    policy=BASE/'results/final_mappo_selection_v2/selected_policy.pt'
    # Set result to a dictionary built from the supplied values.
    result=dict(python=sys.executable,python_version=platform.python_version(),packages=packages,sumo=shutil.which('sumo'),
        # Supply policy_sha256 as the result of sha(policy).
        # Supply historical_files as the number of entries in inventory.
        # Supply historical_bytes as the sum of a lazy sequence of v at 'bytes' for v in values from inventory.
        policy_sha256=sha(policy),historical_files=len(inventory),historical_bytes=sum(v['bytes'] for v in inventory.values()),
        # Supply disk_free_bytes as shutil.disk_usage(BASE).free.
        # Supply repair_gate_summary as gates.
        # Supply families as families.
        # Supply presentations as presentations.
        disk_free_bytes=shutil.disk_usage(BASE).free,repair_gate_summary=gates,families=families,presentations=presentations)
    # Write the supplied text to (OUT / 'initial_audit.json').
    (OUT/'initial_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in ['families','presentations']},indent=2))
    # Iterate over families, binding each item to family.
    # Display the serialized data produced by json.dumps.
    for family in families: print(json.dumps({k:v for k,v in family.items() if k not in ['runs','missing_final_keys','current_source_mismatches']}))
    # Display the text 'Congested presentation artifacts:'.
    print('Congested presentation artifacts:',len(presentations))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
