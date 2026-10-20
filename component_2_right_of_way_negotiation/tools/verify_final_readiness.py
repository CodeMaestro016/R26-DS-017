"""Final byte-preservation and independent presentation-package import checks."""
# Import hashlib for use in this module.
import hashlib
# Import importlib.metadata for use in this module.
import importlib.metadata
# Import json for use in this module.
import json
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import zipfile for use in this module.
import zipfile
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'

# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
# Return the decoded data produced by json.loads from the text read from path to the caller.
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
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
        for chunk in iter(lambda:handle.read(1024*1024),b''):value.update(chunk)
    # Return the hexadecimal digest from value to the caller.
    return value.hexdigest()

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set historical to the result of read(OUT joined with the path segment 'historical_inventory.json').
    historical=read(OUT/'historical_inventory.json')
    # Set changed to a list of name for (name, item) in key/value pairs from historical; retain entries satisfying
    # the result of sha(BASE divided by name) differs from item at 'sha256'.
    changed=[name for name,item in historical.items() if sha(BASE/name)!=item['sha256']]
    # Set protected to the result of read(OUT joined with the path segment 'protected_source_inventory.json').
    protected=read(OUT/'protected_source_inventory.json')
    # Set source_changes to a list of name for (name, expected) in key/value pairs from protected; retain entries
    # satisfying the result of sha(BASE divided by name) differs from expected.
    source_changes=[name for name,expected in protected.items() if sha(BASE/name)!=expected]
    # Run this branch when changed or source_changes.
    # Raise RuntimeError with the text 'Protected scientific evidence/source changed:' plus a string built from
    # changed plus source_changes to stop this execution path.
    if changed or source_changes:raise RuntimeError('Protected scientific evidence/source changed: '+str(changed+source_changes))
    # Set manifest to the result of read(OUT joined with the path segment 'package_manifest.json').
    # Set archive_path to the result of Path(manifest at 'zip_path').
    manifest=read(OUT/'package_manifest.json');archive_path=Path(manifest['zip_path'])
    # Run this branch when the result of sha(archive_path) differs from manifest at 'zip_sha256'.
    # Raise RuntimeError with the text 'Package checksum mismatch' to stop this execution path.
    if sha(archive_path)!=manifest['zip_sha256']:raise RuntimeError('Package checksum mismatch')
    # Keep the extraction root short on Windows (legacy MAX_PATH systems).
    # Set probe to BASE.parent joined with the path segment '.demo_probe_' plus manifest['zip_sha256'] sliced by :8.
    # Create the directory requested by probe.
    probe=BASE.parent/('.demo_probe_'+manifest['zip_sha256'][:8]);probe.mkdir(exist_ok=True)
    # Enter the result of zipfile.ZipFile(archive_path) as archive and run the enclosed operations within that
    # context.
    with zipfile.ZipFile(archive_path) as archive:
        # Iterate over the result of archive.namelist(), binding each item to name.
        for name in archive.namelist():
            # Run this branch when the negation of the result of (probe / name).resolve().is_relative_to(the
            # result of probe.resolve()).
            # Raise RuntimeError with the text 'Unsafe package path' to stop this execution path.
            if not (probe/name).resolve().is_relative_to(probe.resolve()):raise RuntimeError('Unsafe package path')
        # Call archive.extractall with the supplied arguments.
        archive.extractall(probe)
    # Set script to the text 'import hashlib,json,sys from pathlib import Path...'.
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
    # Set result to the result of subprocess.run(a list containing sys.executable, the text '-B', the text '-c',
    # script).
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=probe,capture_output=True,text=True)
    # Write the supplied text to (OUT / 'package_import_probe.log').
    (OUT/'package_import_probe.log').write_text(result.stdout+'\n'+result.stderr)
    # Run this branch when result.returncode.
    # Raise RuntimeError with the text 'Extracted package probe failed; see package_import_probe.log' to stop this
    # execution path.
    if result.returncode:raise RuntimeError('Extracted package probe failed; see package_import_probe.log')
    # Set initial to the result of read(OUT joined with the path segment 'initial_audit.json').
    initial=read(OUT/'initial_audit.json')
    # Set scientific to a list containing the text 'torch', the text 'numpy', the text 'traci', the text
    # 'sumolib', the text 'onnxruntime', the text...
    scientific=['torch','numpy','traci','sumolib','onnxruntime','shapely','matplotlib']
    # Set versions to a dictionary of name mapped to the result of importlib.metadata.version(name) for name in
    # scientific.
    versions={name:importlib.metadata.version(name) for name in scientific}
    # Run this branch when whether any item is true in a lazy sequence of versions at name differs from
    # initial['packages'] at name for name in scientific.
    # Raise RuntimeError with the text 'Scientific Python package version changed' to stop this execution path.
    if any(versions[name]!=initial['packages'][name] for name in scientific):raise RuntimeError('Scientific Python package version changed')
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(date='2026-10-16',readiness='READY WITH LIMITATIONS',
        # Supply scope as the text 'Honest qualitative demonstration/read-only evidence; not...'.
        scope='Honest qualitative demonstration/read-only evidence; not completed final research validation',
        # Supply historical_files_verified as the number of entries in historical.
        # Supply historical_changes as changed.
        historical_files_verified=len(historical),historical_changes=changed,
        # Supply protected_source_asset_files_verified as the number of entries in protected.
        # Supply protected_changes as source_changes.
        protected_source_asset_files_verified=len(protected),protected_changes=source_changes,
        # Supply policy_sha256 as the result of sha(BASE joined with the path segment
        # 'results/final_mappo_selection_v2/selected_policy.pt').
        policy_sha256=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt'),
        # Supply scientific_package_versions as versions.
        # Supply selected_policy_retrained as False.
        scientific_package_versions=versions,selected_policy_retrained=False,
        # Supply scientific_final_suite_executed as False.
        # Supply scalability_suite_executed as False.
        scientific_final_suite_executed=False,scalability_suite_executed=False,
        # Supply existing_sumo_regression_fixture_executed as True.
        # Supply new_qualitative_lifecycle_checks as 3.
        existing_sumo_regression_fixture_executed=True,new_qualitative_lifecycle_checks=3,
        # Supply full_component2_tests as a dictionary built from the supplied values.
        # Supply passed as 848.
        # Supply existing_xfailed as 2.
        # Supply seconds as 1012.22.
        full_component2_tests=dict(passed=848,existing_xfailed=2,seconds=1012.22),
        # Supply full_showcase_tests as a dictionary built from the supplied values.
        # Supply root_collection as 947.
        # Supply passed as 97.
        # Supply seconds as 1.71.
        full_showcase_tests=dict(passed=97,seconds=1.71),root_collection=947,
        # Supply final_v1_verified as 34.
        # Supply final_v1_expected as 165.
        # Supply final_v1_missing as 131.
        final_v1_verified=34,final_v1_expected=165,final_v1_missing=131,
        # Supply final_v1_classifications as a dictionary built from the supplied values.
        # Supply PASS as 10.
        # Supply SAFE_DEGRADATION as 22.
        # Supply UNSAFE_FAILURE as 2.
        # Supply INVALID_EXPERIMENT as 0.
        final_v1_classifications=dict(PASS=10,SAFE_DEGRADATION=22,UNSAFE_FAILURE=2,INVALID_EXPERIMENT=0),
        # Supply final_v2_manifest_present as False.
        # Supply final_v2_verified as 0.
        # Supply final_v2_missing as 165.
        final_v2_manifest_present=False,final_v2_verified=0,final_v2_missing=165,
        # Supply final_suite_authorized as False.
        # Supply repair_gate_accepted as False.
        final_suite_authorized=False,repair_gate_accepted=False,
        # Supply desktop_backend_import as True.
        # Supply visual_browser_check as the text 'UNAVAILABLE; manual rehearsal required'.
        desktop_backend_import=True,visual_browser_check='UNAVAILABLE; manual rehearsal required',
        # Supply package_path as a string built from archive_path.
        # Supply package_sha256 as manifest at 'zip_sha256'.
        package_path=str(archive_path),package_sha256=manifest['zip_sha256'],
        # Supply package_import_probe as the decoded data produced by json.loads from the result of
        # result.stdout.strip().
        package_import_probe=json.loads(result.stdout.strip()),
        # Supply official_scientific_reports_regenerated as False.
        official_scientific_reports_regenerated=False,
        # Supply retained_runtime_limitation as the text 'Direct CLI missing-SUMO finalization can mask startup
        # cause...'.
        retained_runtime_limitation='Direct CLI missing-SUMO finalization can mask startup cause with Not connected; UI prerequisite guards refuse before launch. No scientific runtime change was made.')
    # Write the supplied text to (OUT / 'final_verification.json').
    (OUT/'final_verification.json').write_text(json.dumps(receipt,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt,indent=2))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
