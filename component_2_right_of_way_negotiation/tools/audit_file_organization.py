"""Read-only cleanup audit; writes a new receipt, never moves or removes inputs."""
import hashlib
import json
import os
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'component_2_right_of_way_negotiation'
OUT = BASE / 'results/file_organization/20261016'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    trees = {}
    for child in ROOT.iterdir():
        if child.is_dir():
            count = size = 0
            for folder, dirs, names in os.walk(child):
                for name in names:
                    p = Path(folder) / name
                    if p.is_file():
                        count += 1
                        size += p.stat().st_size
            trees[child.name] = dict(files=count, bytes=size)
        else:
            trees[child.name] = dict(files=1, bytes=child.stat().st_size)
    final = ROOT / 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'
    final_hashes = {}
    archives = {}
    for path in sorted(list(ROOT.glob('*.zip')) + list((ROOT / 'deliverables').glob('*.zip'))):
        with zipfile.ZipFile(path) as z:
            entries = []
            for i in z.infolist():
                if i.is_dir():
                    continue
                name = i.filename.replace('\\', '/')
                h = hashlib.sha256(z.read(i)).hexdigest()
                entries.append(dict(path=name, bytes=i.file_size, sha256=h))
            if path == final:
                final_hashes = {i['path']: i['sha256'] for i in entries}
            archives[str(path.relative_to(ROOT))] = dict(
                bytes=path.stat().st_size, sha256=digest(path), crc_error=z.testzip(),
                files=len(entries), uncompressed_bytes=sum(i['bytes'] for i in entries),
                top_levels=dict(Counter(i['path'].split('/')[0] for i in entries)), entries=entries)
    probes = {}
    for relative in ['.demo_probe_b7b08c60', '.presentation_probe_20261016',
                     'component_2_right_of_way_negotiation/results/final_readiness/20261016/package_import_probe']:
        folder = ROOT / relative
        entries = []
        for p in folder.rglob('*'):
            if not p.is_file():
                continue
            name = p.relative_to(folder).as_posix()
            h = digest(p)
            canonical = ROOT / name
            matches = []
            if canonical.is_file() and digest(canonical) == h:
                matches.append('canonical')
            for archive_name, archive in archives.items():
                for item in archive['entries']:
                    if item['path'] == name and item['sha256'] == h:
                        matches.append(archive_name)
                        break
            generated = '__pycache__' in p.parts or '.pytest_cache' in p.parts
            entries.append(dict(path=name, bytes=p.stat().st_size, sha256=h,
                                matches=matches, generated_cache=generated))
        probes[relative] = dict(files=len(entries), bytes=sum(i['bytes'] for i in entries),
                               unique_noncache=[i for i in entries if not i['matches'] and not i['generated_cache']],
                               entries=entries)
    receipt = dict(root=str(ROOT), trees=trees, archives=archives, probes=probes,
                   final_sha256=digest(final), final_entries=len(final_hashes),
                   backup_verified=False, cleanup_executed=False)
    target = OUT / 'pre_cleanup_audit.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(dict(trees=trees,
        archives={k: {a: b for a, b in v.items() if a != 'entries'} for k, v in archives.items()},
        probes={k: {a: b for a, b in v.items() if a != 'entries'} for k, v in probes.items()}), indent=2))


if __name__ == '__main__':
    main()
