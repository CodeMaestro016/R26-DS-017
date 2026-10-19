"""Supplement the cleanup inventory with exact archive comparisons."""
import json
from pathlib import Path
from audit_file_organization import ROOT, OUT, digest


def main():
    data = json.loads((OUT / 'pre_cleanup_audit.json').read_text(encoding='utf-8'))
    a = data['archives']
    comparisons = {}
    for name, prefix, folder in [('.demo_probe_b7b08c60.zip', '.demo_probe_b7b08c60/', '.demo_probe_b7b08c60'),
                                 ('.presentation_probe_20261016.zip', '.presentation_probe_20261016/', '.presentation_probe_20261016')]:
        different = [i['path'] for i in a[name]['entries']
                     if not (ROOT / i['path']).is_file() or digest(ROOT / i['path']) != i['sha256']]
        comparisons[name] = dict(files=a[name]['files'], mismatches=different,
                                 wrapper=prefix, matching_probe=folder)
    comparisons['deliverables.zip'] = dict(mismatches=[i['path'] for i in a['deliverables.zip']['entries']
        if not (ROOT / i['path']).is_file() or digest(ROOT / i['path']) != i['sha256']])
    original = a['R26-DS-017.zip']['entries']
    comparisons['R26-DS-017.zip'] = dict(
        missing=[i['path'] for i in original if not (ROOT / i['path']).is_file()],
        changed=[i['path'] for i in original if (ROOT / i['path']).is_file() and digest(ROOT / i['path']) != i['sha256']],
        omitted_root_items=[n for n in data['trees'] if n not in {'component_2_right_of_way_negotiation','socialmind_drive_showcase'}])
    savings = sum(data['trees'][n]['bytes'] for n in ['.demo_probe_b7b08c60','.presentation_probe_20261016',
        '.demo_probe_b7b08c60.zip','.presentation_probe_20261016.zip','deliverables.zip','.pytest_cache'])
    moved = data['trees']['R26-DS-017.zip']['bytes'] + sum(v['bytes'] for n,v in a.items()
        if n.startswith('deliverables') and 'PRESENTATION_' in n)
    result = dict(comparisons=comparisons, deletion_bytes=savings, external_move_bytes=moved,
                  active_workspace_reduction_bytes=savings+moved,
                  initial_workspace_bytes=sum(v['bytes'] for v in data['trees'].values()),
                  optional_partial_probe_bytes=data['probes']['component_2_right_of_way_negotiation/results/final_readiness/20261016/package_import_probe']['bytes'])
    with (OUT / 'archive_comparisons.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
