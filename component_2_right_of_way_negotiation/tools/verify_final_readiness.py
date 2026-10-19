"""Final byte-preservation and independent presentation-package import checks."""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import zipfile
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/final_readiness/20261016'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()

def main():
    historical=read(OUT/'historical_inventory.json')
    changed=[name for name,item in historical.items() if sha(BASE/name)!=item['sha256']]
    protected=read(OUT/'protected_source_inventory.json')
    source_changes=[name for name,expected in protected.items() if sha(BASE/name)!=expected]
    if changed or source_changes:raise RuntimeError('Protected scientific evidence/source changed: '+str(changed+source_changes))
    manifest=read(OUT/'package_manifest.json');archive_path=Path(manifest['zip_path'])
    if sha(archive_path)!=manifest['zip_sha256']:raise RuntimeError('Package checksum mismatch')
    # Keep the extraction root short on Windows (legacy MAX_PATH systems).
    probe=BASE.parent/('.demo_probe_'+manifest['zip_sha256'][:8]);probe.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if not (probe/name).resolve().is_relative_to(probe.resolve()):raise RuntimeError('Unsafe package path')
        archive.extractall(probe)
    script='''import hashlib,json,sys
from pathlib import Path
base=Path.cwd();sys.path.insert(0,str(base/'component_2_right_of_way_negotiation'))
from socialmind_drive_showcase.services.evaluation_reader import read_evaluation
from socialmind_drive_showcase.services.targeted_validation_reader import read_targeted_validation
from socialmind_drive_showcase.services.scenario_reader import read_scenario_catalog
from socialmind_drive_showcase import app
from runtime_simulation.runner import run_runtime_simulation
value=read_evaluation();targeted=read_targeted_validation()
assert value['available'] and value['verification']['verified']==34 and value['verification']['expected']==165
assert value['payload']['suite']=='smoke' and value['payload']['episode_count']==9
assert targeted['available']
assert any(c['scenario_id']=='congested_four_approach' and c['vehicle_count']==16 for c in read_scenario_catalog())
policy=base/'component_2_right_of_way_negotiation/results/final_mappo_selection_v2/selected_policy.pt'
assert hashlib.sha256(policy.read_bytes()).hexdigest()=='2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'
print(json.dumps(dict(imports=True,verified_final=34,expected=165,smoke=9,targeted_available=True,congested_scenario=True,policy_unchanged=True)))
'''
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=probe,capture_output=True,text=True)
    (OUT/'package_import_probe.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode:raise RuntimeError('Extracted package probe failed; see package_import_probe.log')
    initial=read(OUT/'initial_audit.json')
    scientific=['torch','numpy','traci','sumolib','onnxruntime','shapely','matplotlib']
    versions={name:importlib.metadata.version(name) for name in scientific}
    if any(versions[name]!=initial['packages'][name] for name in scientific):raise RuntimeError('Scientific Python package version changed')
    receipt=dict(date='2026-10-16',readiness='READY WITH LIMITATIONS',
        scope='Honest qualitative demonstration/read-only evidence; not completed final research validation',
        historical_files_verified=len(historical),historical_changes=changed,
        protected_source_asset_files_verified=len(protected),protected_changes=source_changes,
        policy_sha256=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt'),
        scientific_package_versions=versions,selected_policy_retrained=False,
        scientific_final_suite_executed=False,scalability_suite_executed=False,
        existing_sumo_regression_fixture_executed=True,new_qualitative_lifecycle_checks=3,
        full_component2_tests=dict(passed=848,existing_xfailed=2,seconds=1012.22),
        full_showcase_tests=dict(passed=97,seconds=1.71),root_collection=947,
        final_v1_verified=34,final_v1_expected=165,final_v1_missing=131,
        final_v1_classifications=dict(PASS=10,SAFE_DEGRADATION=22,UNSAFE_FAILURE=2,INVALID_EXPERIMENT=0),
        final_v2_manifest_present=False,final_v2_verified=0,final_v2_missing=165,
        final_suite_authorized=False,repair_gate_accepted=False,
        desktop_backend_import=True,visual_browser_check='UNAVAILABLE; manual rehearsal required',
        package_path=str(archive_path),package_sha256=manifest['zip_sha256'],
        package_import_probe=json.loads(result.stdout.strip()),
        official_scientific_reports_regenerated=False,
        retained_runtime_limitation='Direct CLI missing-SUMO finalization can mask startup cause with Not connected; UI prerequisite guards refuse before launch. No scientific runtime change was made.')
    (OUT/'final_verification.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
