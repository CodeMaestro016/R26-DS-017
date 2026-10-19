"""Read-only research audit; writes a separate readiness evidence family only."""
import hashlib
import importlib.metadata
import json
import platform
import shutil
import sys
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/final_readiness/20261016'

def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''): value.update(chunk)
    return value.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def verify_run(path,frozen):
    raw=read(path); errors=[]
    for name,key in [('result','result_hash'),('provenance','provenance_hash')]:
        try:
            value=read(path.with_name(name+'.json'))
            if digest(value)!=read(path.with_name(name+'.sha256.json'))[key]: errors.append(name+'_checksum')
        except (OSError,ValueError,KeyError) as exc: errors.append(name+':'+str(exc))
    try:
        provenance=read(path.with_name('provenance.json'))
        if raw['manifest_hash']!=frozen['manifest_hash'] or provenance['manifest_hash']!=frozen['manifest_hash']: errors.append('manifest_identity')
        if digest(provenance['schedule'])!=raw['schedule_hash'] or provenance['schedule_hash']!=raw['schedule_hash']: errors.append('schedule_hash')
        for name,expected in raw.get('artifact_sha256',{}).items():
            if Path(name).name!=name or sha(path.parent/name)!=expected: errors.append('artifact:'+name)
    except (OSError,ValueError,KeyError) as exc: errors.append('artifacts:'+str(exc))
    return raw,errors

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Inventory immutable results before any test or UI work.
    inventory={}
    for path in (BASE/'results').rglob('*'):
        if path.is_file() and OUT.parent not in path.parents and '__pycache__' not in path.parts:
            inventory[str(path.relative_to(BASE))]=dict(sha256=sha(path),bytes=path.stat().st_size)
    (OUT/'historical_inventory.json').write_text(json.dumps(inventory,indent=2))
    protected={}
    for folder in ['runtime_simulation','post_training_evaluation','targeted_validation','scalability_validation','negotiation_execution','negotiation_learning','negotiation_training','traffic_rules','conflict','networks','models']:
        for path in (BASE/folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                protected[str(path.relative_to(BASE))]=sha(path)
    protected['config.py']=sha(BASE/'config.py')
    (OUT/'protected_source_inventory.json').write_text(json.dumps(protected,indent=2))
    families=[]
    roots=['results/final_evaluation','results/final_evaluation_development','results/final_evaluation/v2_candidate',
        'results/post_training_evaluation/v2_candidate','results/panel_validation/v1','results/panel_validation/v2',
        'results/targeted_validation/v2','results/scalability_validation/v1','results/scalability_validation/v2']
    for relative in roots:
        root=BASE/relative;manifest=root/'manifest.json'
        if not manifest.exists():
            families.append(dict(root=relative,manifest_present=False));continue
        frozen=read(manifest);m=frozen['manifest'];runs=[]
        for path in sorted((root/'runs').glob('*/result.json')):
            raw,errors=verify_run(path,frozen)
            runs.append(dict(path=str(path.relative_to(BASE)),run_id=raw['run_id'],suite=raw['suite'],method=raw['method'],
                scenario_id=raw['scenario_id'],seed=raw.get('seed'),classification=raw['classification'],verification_errors=errors,
                metrics=raw['metrics'],integrity=raw.get('integrity',{}),wall_clock_seconds=raw.get('wall_clock_seconds'),
                error=raw.get('error'),schedule_hash=raw['schedule_hash']))
        by_suite={suite:dict(recorded=sum(r['suite']==suite for r in runs),verified=sum(r['suite']==suite and not r['verification_errors'] for r in runs),
            outcomes=dict(Counter(r['classification'] for r in runs if r['suite']==suite and not r['verification_errors']))) for suite in sorted({r['suite'] for r in runs})}
        current_bad=[name for name,expected in m.get('source_identities',{}).items() if not (BASE/name).is_file() or sha(BASE/name)!=expected]
        expected=set()
        if m.get('scenarios') and m.get('methods') and m.get('seeds'):
            for scenario in m['scenarios']:
                for seed in m['seeds'] if scenario.get('continuous') else [None]:
                    for method in m['methods']: expected.add((scenario['scenario_id'],seed,method))
        actual={(r['scenario_id'],r['seed'],r['method']) for r in runs if r['suite']=='final' and not r['verification_errors']}
        families.append(dict(root=relative,manifest_present=True,manifest_hash=frozen['manifest_hash'],manifest_checksum_valid=digest(m)==frozen['manifest_hash'],
            protocol_id=m.get('protocol_id'),policy_sha256=m.get('policy_sha256'),inference_mode=m.get('inference_mode'),seeds=m.get('seeds'),
            current_source_mismatches=current_bad,suites=by_suite,expected_final_episodes=len(expected) or None,
            verified_final_keys=len(actual),missing_final_keys=sorted(expected-actual,key=str),runs=runs))
    presentations=[]
    for relative in ['results/panel_demo','results/runtime_simulation']:
        root=BASE/relative
        paths=list(root.glob('**/run_*.json'))+list(root.glob('**/latest*demo.json'))+list(root.glob('**/latest*simulation.json'))
        for path in sorted(set(paths)):
            try: raw=read(path)
            except (OSError,ValueError): continue
            if raw.get('presentation_scenario_id',raw.get('scenario_id'))!='congested_four_approach': continue
            presentations.append(dict(path=str(path.relative_to(BASE)),bytes=path.stat().st_size,record=raw))
    packages={}
    for name in ['pytest','torch','numpy','nicegui','pywebview','traci','sumolib','onnxruntime','shapely','matplotlib','psutil']:
        try: packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: packages[name]=None
    gates={}
    gate=BASE/'results/repair_diagnostics/validation_summary.json'
    if gate.exists():
        raw=read(gate)
        gates={k:v for k,v in raw.items() if k not in ['diagnostic_batches','diagnostics','runs','cases'] and not isinstance(v,list)}
    policy=BASE/'results/final_mappo_selection_v2/selected_policy.pt'
    result=dict(python=sys.executable,python_version=platform.python_version(),packages=packages,sumo=shutil.which('sumo'),
        policy_sha256=sha(policy),historical_files=len(inventory),historical_bytes=sum(v['bytes'] for v in inventory.values()),
        disk_free_bytes=shutil.disk_usage(BASE).free,repair_gate_summary=gates,families=families,presentations=presentations)
    (OUT/'initial_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['families','presentations']},indent=2))
    for family in families: print(json.dumps({k:v for k,v in family.items() if k not in ['runs','missing_final_keys','current_source_mismatches']}))
    print('Congested presentation artifacts:',len(presentations))

if __name__=='__main__':main()
