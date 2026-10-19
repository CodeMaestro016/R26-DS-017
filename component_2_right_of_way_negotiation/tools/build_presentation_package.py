"""Create a new minimal presentation ZIP; never move/delete research evidence."""
import hashlib
import json
import os
import zipfile
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
WORKSPACE=BASE.parent
OUT=BASE/'results/final_readiness/20261016'
DOCS=BASE/'docs/final_readiness'
DEST=WORKSPACE/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def include_tree(files,folder,extensions=None):
    if not folder.exists():return
    for p in folder.rglob('*'):
        if p.is_file() and not set(p.relative_to(folder).parts)&{'__pycache__','.pytest_cache','tests','.git'}:
            if extensions is None or p.suffix.lower() in extensions:files.add(p)

def main():
    files={WORKSPACE/'README.md',WORKSPACE/'pytest.ini'}
    for p in BASE.iterdir():
        if p.is_file() and p.suffix.lower() in {'.py','.txt','.md','.sumocfg','.bat','.html'}:files.add(p)
    directories=['runtime_simulation','targeted_validation','post_training_evaluation','panel_demo','panel_validation','final_evaluation',
        'scalability_validation','traffic_accounting','traffic_rules','conflict','map_geometry','negotiation_execution','negotiation_learning','negotiation_training',
        'negotiation_objective','negotiation_scenarios','experimentation','networks','gui','models','research_inputs','scripts']
    extensions={'.py','.json','.xml','.onnx','.npz','.npy','.txt','.md','.sumocfg','.bat','.sh','.html'}
    for folder in directories:include_tree(files,BASE/folder,extensions)
    include_tree(files,BASE/'docs',extensions)
    include_tree(files,WORKSPACE/'socialmind_drive_showcase',{'.py','.txt','.md','.png','.jpg','.jpeg','.svg','.ico','.webp','.css','.js','.html'})
    selection=BASE/'results/final_mappo_selection_v2'
    for name in ['selected_policy.pt','selected_configuration.json','candidate_manifest.json','protocol.json','FINAL_MAPPO_SELECTION_REPORT.md']:
        files.add(selection/name)
    include_tree(files,selection/'comparison',{'.json','.csv'})
    # Original, small result/provenance records and authentic saved figures.
    # Per-step traces and complete source snapshots stay in the full archive.
    for relative in ['results/final_evaluation','results/panel_validation/v1','results/panel_validation/v2','results/scalability_validation/v1','results/scalability_validation/v2']:
        root=BASE/relative
        for name in ['manifest.json','faults.json']:
            if (root/name).is_file():files.add(root/name)
        include_tree(files,root/'latest',{'.json','.html','.md','.png','.csv'})
        for directory in (root/'runs').glob('*'):
            for name in ['result.json','result.sha256.json','provenance.json','provenance.sha256.json','study_result.json','study_result.sha256.json']:
                if (directory/name).is_file():files.add(directory/name)
    files.add(BASE/'results/panel_demo/congested_ego_local_verification/latest_panel_demo.json')
    include_tree(files,BASE/'results/panel_validation/latest',{'.json','.md','.html'})
    files.discard(DOCS/'FINAL_PACKAGE_AUDIT.md')
    inventory={str(p.relative_to(WORKSPACE)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files) if p.is_file()}
    original_size=0;largest=[]
    for root,dirs,names in os.walk(WORKSPACE):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','venv','__pycache__','.pytest_cache','deliverables','final_readiness'}
            and not d.startswith(('.presentation_probe_','.demo_probe_'))]
        for name in names:
            p=Path(root)/name
            try:size=p.stat().st_size
            except OSError:continue
            original_size+=size
            if size>20*1024**2:largest.append((str(p.relative_to(WORKSPACE)),size))
    raw_size=sum(v['bytes'] for v in inventory.values())
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
    (DOCS/'FINAL_PACKAGE_AUDIT.md').write_text(package_audit,encoding='utf-8')
    files.add(DOCS/'FINAL_PACKAGE_AUDIT.md')
    audit_path=DOCS/'FINAL_PACKAGE_AUDIT.md'
    inventory[str(audit_path.relative_to(WORKSPACE)).replace('\\','/')]=dict(bytes=audit_path.stat().st_size,sha256=sha(audit_path))
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
    DEST.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(DEST,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(files):
            if path.is_file():archive.write(path,str(path.relative_to(WORKSPACE)))
        archive.writestr('START_HERE.md',start)
    with zipfile.ZipFile(DEST) as archive:
        bad=archive.testzip()
        if bad:raise RuntimeError('ZIP verification failed: '+bad)
        for name,expected in inventory.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected['sha256']:
                raise RuntimeError('Copied scientific/source bytes mismatch: '+name)
    manifest=dict(zip_path=str(DEST),zip_bytes=DEST.stat().st_size,zip_sha256=sha(DEST),
        original_workspace_bytes=original_size,selected_uncompressed_bytes=sum(v['bytes'] for v in inventory.values()),
        copied_files=inventory,scientific_results_regenerated=False,full_archive_required_for_replay=True)
    (OUT/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in manifest.items() if k!='copied_files'},indent=2))

if __name__=='__main__':main()
