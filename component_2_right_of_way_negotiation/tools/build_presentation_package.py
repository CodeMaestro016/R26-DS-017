"""Create a new minimal presentation ZIP; never move/delete research evidence."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import zipfile for use in this module.
import zipfile
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set WORKSPACE to BASE.parent.
WORKSPACE=BASE.parent
# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'
# Set DOCS to BASE joined with the path segment 'docs/final_readiness'.
DOCS=BASE/'docs/final_readiness'
# Set DEST to WORKSPACE joined with the path segment 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'.
DEST=WORKSPACE/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'

# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(path.read_bytes()).
# Return the hexadecimal digest from hashlib.sha256(path.read_bytes()) to the caller.
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
# Include tree using the inputs and processing steps below.
# Input files: the supplied files.
# Input folder: the supplied folder.
# Input extensions: the supplied extensions.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def include_tree(files,folder,extensions=None):
    # Run this branch when the negation of whether folder exists.
    # Return no value to the caller.
    if not folder.exists():return
    # Iterate over the result of folder.rglob(the text '*'), binding each item to p.
    for p in folder.rglob('*'):
        # Run this branch when whether p is an existing file and the negation of a set built from
        # p.relative_to(folder).parts intersected with a set containing '__pycache__', '.pytest_cache', 'tests',
        # '.git'.
        if p.is_file() and not set(p.relative_to(folder).parts)&{'__pycache__','.pytest_cache','tests','.git'}:
            # Run this branch when extensions is the same object as None or the result of p.suffix.lower() belongs
            # to extensions.
            # Add p to files.
            if extensions is None or p.suffix.lower() in extensions:files.add(p)

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Set files to a set containing WORKSPACE joined with the path segment 'README.md', WORKSPACE joined with the path segment
    # 'pytest.ini'.
    files={WORKSPACE/'README.md',WORKSPACE/'pytest.ini'}
    # Iterate over the result of BASE.iterdir(), binding each item to p.
    for p in BASE.iterdir():
        # Run this branch when whether p is an existing file and the result of p.suffix.lower() belongs to a set
        # containing the text '.py', the text '.txt', the text '.md', the text '.sumocfg', the text '.bat', the
        # text '.html'.
        # Add p to files.
        if p.is_file() and p.suffix.lower() in {'.py','.txt','.md','.sumocfg','.bat','.html'}:files.add(p)
    # Set directories to a list containing the text 'runtime_simulation', the text 'targeted_validation', the text
    # 'post_training_evaluation', the...
    directories=['runtime_simulation','targeted_validation','post_training_evaluation','panel_demo','panel_validation','final_evaluation',
        'scalability_validation','traffic_accounting','traffic_rules','conflict','map_geometry','negotiation_execution','negotiation_learning','negotiation_training',
        'negotiation_objective','negotiation_scenarios','experimentation','networks','gui','models','research_inputs','scripts']
    # Set extensions to a set containing the text '.py', the text '.json', the text '.xml', the text '.onnx', the
    # text '.npz', the text '.npy', the...
    extensions={'.py','.json','.xml','.onnx','.npz','.npy','.txt','.md','.sumocfg','.bat','.sh','.html'}
    # Iterate over directories, binding each item to folder.
    # Call include_tree with the supplied arguments.
    for folder in directories:include_tree(files,BASE/folder,extensions)
    # Call include_tree with the supplied arguments.
    include_tree(files,BASE/'docs',extensions)
    # Call include_tree with the supplied arguments.
    include_tree(files,WORKSPACE/'socialmind_drive_showcase',{'.py','.txt','.md','.png','.jpg','.jpeg','.svg','.ico','.webp','.css','.js','.html'})
    # Set selection to BASE joined with the path segment 'results/final_mappo_selection_v2'.
    selection=BASE/'results/final_mappo_selection_v2'
    # Iterate over a list containing the text 'selected_policy.pt', the text 'selected_configuration.json', the
    # text 'candidate_manifest.json',..., binding each item to name.
    for name in ['selected_policy.pt','selected_configuration.json','candidate_manifest.json','protocol.json','FINAL_MAPPO_SELECTION_REPORT.md']:
        # Add selection divided by name to files.
        files.add(selection/name)
    # Call include_tree with the supplied arguments.
    include_tree(files,selection/'comparison',{'.json','.csv'})
    # Original, small result/provenance records and authentic saved figures.
    # Per-step traces and complete source snapshots stay in the full archive.
    # Iterate over a list containing the text 'results/final_evaluation', the text 'results/panel_validation/v1',
    # the text..., binding each item to relative.
    for relative in ['results/final_evaluation','results/panel_validation/v1','results/panel_validation/v2','results/scalability_validation/v1','results/scalability_validation/v2']:
        # Set root to BASE divided by relative.
        root=BASE/relative
        # Iterate over a list containing the text 'manifest.json', the text 'faults.json', binding each item to
        # name.
        for name in ['manifest.json','faults.json']:
            # Run this branch when whether (root / name) is an existing file.
            # Add root divided by name to files.
            if (root/name).is_file():files.add(root/name)
        # Call include_tree with the supplied arguments.
        include_tree(files,root/'latest',{'.json','.html','.md','.png','.csv'})
        # Iterate over the result of (root / 'runs').glob(the text '*'), binding each item to directory.
        for directory in (root/'runs').glob('*'):
            # Iterate over a list containing the text 'result.json', the text 'result.sha256.json', the text
            # 'provenance.json', the text..., binding each item to name.
            for name in ['result.json','result.sha256.json','provenance.json','provenance.sha256.json','study_result.json','study_result.sha256.json']:
                # Run this branch when whether (directory / name) is an existing file.
                # Add directory divided by name to files.
                if (directory/name).is_file():files.add(directory/name)
    # Add BASE joined with the path segment 'results/panel_demo/congested_ego_local_verification/latest_pan...' to files.
    files.add(BASE/'results/panel_demo/congested_ego_local_verification/latest_panel_demo.json')
    # Call include_tree with the supplied arguments.
    include_tree(files,BASE/'results/panel_validation/latest',{'.json','.md','.html'})
    # Discard DOCS joined with the path segment 'FINAL_PACKAGE_AUDIT.md' from files if present.
    files.discard(DOCS/'FINAL_PACKAGE_AUDIT.md')
    # Set inventory to a dictionary of the result of str(p.relative_to(WORKSPACE)).replace(the text '\\', the text
    # '/') mapped to a dictionary built from the supplied values for p in the sorted values from files; retain
    # entries satisfying whether p is an existing file.
    inventory={str(p.relative_to(WORKSPACE)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files) if p.is_file()}
    # Set original_size to 0.
    # Set largest to an empty list.
    original_size=0;largest=[]
    # Iterate over the result of os.walk(WORKSPACE), binding each item to (root, dirs, names).
    for root,dirs,names in os.walk(WORKSPACE):
        # Set dirs[:] to a list of d for d in dirs; retain entries satisfying d does not belong to a set
        # containing '.git', '.venv', 'venv', '__pycache__',...
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','venv','__pycache__','.pytest_cache','deliverables','final_readiness'}
            # Evaluate the negation of the result of d.startswith(a tuple containing the text
            # '.presentation_probe_', the text '.demo_probe_') as part of the enclosing expression.
            and not d.startswith(('.presentation_probe_','.demo_probe_'))]
        # Iterate over names, binding each item to name.
        for name in names:
            # Set p to the result of Path(root) divided by name.
            p=Path(root)/name
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            # Set size to p.stat().st_size.
            try:size=p.stat().st_size
            # Handle OSError using the recovery steps below.
            # Skip the rest of this loop iteration and process the next item.
            except OSError:continue
            # Update original_size to its current value plus size.
            original_size+=size
            # Run this branch when size is greater than 20 multiplied by 1024 raised to the power 2.
            # Append a tuple containing a string built from the result of p.relative_to(WORKSPACE), size to
            # largest.
            if size>20*1024**2:largest.append((str(p.relative_to(WORKSPACE)),size))
    # Set raw_size to the sum of a lazy sequence of v at 'bytes' for v in values from inventory.
    raw_size=sum(v['bytes'] for v in inventory.values())
    # Set package_audit to formatted text built from the embedded values plus the result of ''.join(a lazy
    # sequence of formatted text built from the embedded values for (name, size) in...).
    package_audit=f'''# Final presentation package audit — 16 October 2026

A new additive presentation ZIP is created at
`deliverables/{DEST.name}`. No existing file, model, evidence or archive is
deleted or moved. The full original research checkout remains the authoritative
hand-in/reproducibility archive; this ZIP is an offline Component 2 presentation
bundle, not a replacement for all research/training data or archived replay code.

Original workspace size (excluding .git, virtual environments, caches and new
deliverables): {original_size/1024**3:.3f} GiB. Selected presentation files:
{len(inventory)} files, {raw_size/1024**2:.2f} MiB uncompressed before this audit
and package README. The exact compressed size and SHA-256 are in package_manifest.json.
The separate academic website's 20 MB upload limit does not apply to this local
Python/NiceGUI demonstration. Do not shrink it by removing required models.

## Included runtime files

Active Component 2 root modules; simulation, targeted/post-training/scalability
packages and thin old-name compatibility aliases; perception/LDM/conflict,
negotiation/rule/objective/training-provider source imports; compiled SUMO XML,
route/vehicle configuration and GUI settings; deployed intention ONNX models,
feature/calibration JSON/NPZ contracts; original dependency files; unchanged E5
selected_policy.pt at its original relative path and frozen selection records.
The complete showcase application/pages/services/styles and local visual assets
are included without redesigning Components 1/3/4. Their external GPU services
are not bundled or asserted operational by this Component 2 audit.

## Included read-only research evidence

Original V1 final manifest, 34 final and nine smoke result/provenance/checksum
sets, original saved smoke aggregate/reports/plots, targeted/scalability manifests
and recorded summaries/reports, selection comparison records, and authentic
older 16-vehicle presentation output. Recorded scientific values and filenames
are copied byte-for-byte. The evaluation page still shows 34/165 and a separate
SMOKE_NOT_FINAL comparison. No new performance plot is invented.

Full execution traces, complete source snapshots, training replications,
development diagnostics, cache/venv files, tests requiring those archives and
existing large project ZIPs remain in the full research archive. This bundle is
not suitable for continuing scientific evaluation or historical replay without
that archive. Missing per-step trace assets are not represented as reproduced.
Tests remain intact in the original repository and their newly executed results
are documented in FINAL_TEST_VERIFICATION.md. No test assertion is removed there.

## Dependencies and startup

Verified existing environment: Python 3.13.1; SUMO executable 1.26.0 external
to Python; Torch 2.14.0, NiceGUI 3.16.0, ONNX Runtime 1.29.0. Desktop pywebview
6.2.1 and owned-tree psutil 7.2.2 are now installed; missing scientific packages
were not replaced or upgraded. A fresh machine must install declared dependencies
and SUMO; the ZIP does not contain a portable Python interpreter or SUMO binary.
Run START_HERE.md and FINAL_VIVA_RUNBOOK.md from the extracted root. Keep the
existing sibling folder structure so relative model/config/asset paths resolve.

## Largest archive/development candidates (retained, not deleted)

| Path | MiB |
|---|---|
'''+''.join(f'| {name} | {size/1024**2:.2f} |\n' for name,size in sorted(largest,key=lambda row:row[1],reverse=True)[:15])
    # Write the supplied text to (DOCS / 'FINAL_PACKAGE_AUDIT.md').
    (DOCS/'FINAL_PACKAGE_AUDIT.md').write_text(package_audit,encoding='utf-8')
    # Add DOCS joined with the path segment 'FINAL_PACKAGE_AUDIT.md' to files.
    files.add(DOCS/'FINAL_PACKAGE_AUDIT.md')
    # Set audit_path to DOCS joined with the path segment 'FINAL_PACKAGE_AUDIT.md'.
    audit_path=DOCS/'FINAL_PACKAGE_AUDIT.md'
    # Set inventory[str(audit_path.relative_to(WORKSPACE)).replace('\\', '/')] to a dictionary built from the
    # supplied values.
    inventory[str(audit_path.relative_to(WORKSPACE)).replace('\\','/')]=dict(bytes=audit_path.stat().st_size,sha256=sha(audit_path))
    # Set start to the text '# SOCIALMIND DRIVE — Component 2 presentation bundle Keep...'.
    start=r'''# SOCIALMIND DRIVE — Component 2 presentation bundle

Keep both sibling folders. This is a presentation bundle; retain the full
research archive separately. It does not establish completed final evaluation.
The evaluation page shows 34/165 legacy final episodes and nine separate smoke
episodes. Targeted dense limitations and unexecuted scalability remain visible.

```powershell
# From the extracted root, using the existing verified environment on the viva machine:
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
sumo --version
& $projectPython -m pip install -r socialmind_drive_showcase\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements-training.txt
& $projectPython -B socialmind_drive_showcase\app.py --server-only
```

Open http://127.0.0.1:8088/component/right-of-way/live, select Congested
Four-Approach Queues (16 vehicles), then Run Scenario and Stop. Omit
--server-only for the desktop window after verifying pywebview/WebView support.
Do not continue evaluations or replay original experiments from this minimal
bundle: full traces and exact archived source sets remain in the full archive.
Read component_2_right_of_way_negotiation/docs/final_readiness/FINAL_VIVA_RUNBOOK.md.
'''
    # Create the directory requested by DEST.parent.
    DEST.parent.mkdir(parents=True,exist_ok=True)
    # Enter the result of zipfile.ZipFile(DEST, the text 'x') as archive and run the enclosed operations within
    # that context.
    with zipfile.ZipFile(DEST,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        # Iterate over the sorted values from files, binding each item to path.
        for path in sorted(files):
            # Run this branch when whether path is an existing file.
            # Call archive.write with the supplied arguments.
            if path.is_file():archive.write(path,str(path.relative_to(WORKSPACE)))
        # Call archive.writestr with the supplied arguments.
        archive.writestr('START_HERE.md',start)
    # Enter the result of zipfile.ZipFile(DEST) as archive and run the enclosed operations within that context.
    with zipfile.ZipFile(DEST) as archive:
        # Set bad to the result of archive.testzip().
        bad=archive.testzip()
        # Run this branch when bad.
        # Raise RuntimeError with the text 'ZIP verification failed:' plus bad to stop this execution path.
        if bad:raise RuntimeError('ZIP verification failed: '+bad)
        # Iterate over key/value pairs from inventory, binding each item to (name, expected).
        for name,expected in inventory.items():
            # Run this branch when the hexadecimal digest from hashlib.sha256(archive.read(name)) differs from
            # expected at 'sha256'.
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected['sha256']:
                # Raise RuntimeError with the text 'Copied scientific/source bytes mismatch:' plus name to stop
                # this execution path.
                raise RuntimeError('Copied scientific/source bytes mismatch: '+name)
    # Set manifest to a dictionary built from the supplied values.
    manifest=dict(zip_path=str(DEST),zip_bytes=DEST.stat().st_size,zip_sha256=sha(DEST),
        # Supply original_workspace_bytes as original_size.
        # Supply selected_uncompressed_bytes as the sum of a lazy sequence of v at 'bytes' for v in values from
        # inventory.
        original_workspace_bytes=original_size,selected_uncompressed_bytes=sum(v['bytes'] for v in inventory.values()),
        # Supply copied_files as inventory.
        # Supply scientific_results_regenerated as False.
        # Supply full_archive_required_for_replay as True.
        copied_files=inventory,scientific_results_regenerated=False,full_archive_required_for_replay=True)
    # Write the supplied text to (OUT / 'package_manifest.json').
    (OUT/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in manifest.items() if k!='copied_files'},indent=2))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
