"""Read-only cleanup audit; writes a new receipt, never moves or removes inputs."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import zipfile for use in this module.
import zipfile
# Import Counter from collections for the operations below.
from collections import Counter
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set ROOT to Path(__file__).resolve().parents at 2.
ROOT = Path(__file__).resolve().parents[2]
# Set BASE to ROOT joined with the path segment 'component_2_right_of_way_negotiation'.
BASE = ROOT / 'component_2_right_of_way_negotiation'
# Set OUT to BASE joined with the path segment 'results/file_organization/20261016'.
OUT = BASE / 'results/file_organization/20261016'


# Digest using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from h.
# Processing: iterate over the relevant records.
def digest(path):
    # Set h to the result of hashlib.sha256().
    h = hashlib.sha256()
    # Enter the result of path.open(the text 'rb') as stream and run the enclosed operations within that context.
    with path.open('rb') as stream:
        # Iterate over the result of iter(a callback that returns the result of stream.read(1024 multiplied by
        # 1024), b''), binding each item to block.
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # Update h with the supplied entries.
            h.update(block)
    # Return the hexadecimal digest from h to the caller.
    return h.hexdigest()


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True, exist_ok=True)
    # Set trees to an empty dictionary.
    trees = {}
    # Iterate over the result of ROOT.iterdir(), binding each item to child.
    for child in ROOT.iterdir():
        # Run this branch when whether child is an existing directory.
        if child.is_dir():
            # Set count and size to 0.
            count = size = 0
            # Iterate over the result of os.walk(child), binding each item to (folder, dirs, names).
            for folder, dirs, names in os.walk(child):
                # Iterate over names, binding each item to name.
                for name in names:
                    # Set p to the result of Path(folder) divided by name.
                    p = Path(folder) / name
                    # Run this branch when whether p is an existing file.
                    if p.is_file():
                        # Update count to its current value plus 1.
                        count += 1
                        # Update size to its current value plus p.stat().st_size.
                        size += p.stat().st_size
            # Set trees[child.name] to a dictionary built from the supplied values.
            trees[child.name] = dict(files=count, bytes=size)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set trees[child.name] to a dictionary built from the supplied values.
            trees[child.name] = dict(files=1, bytes=child.stat().st_size)
    # Set final to ROOT joined with the path segment 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'.
    final = ROOT / 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip'
    # Set final_hashes to an empty dictionary.
    final_hashes = {}
    # Set archives to an empty dictionary.
    archives = {}
    # Iterate over the sorted values from a list built from the result of ROOT.glob('*.zip') plus a list built
    # from the result of (ROOT / 'deliverables').glob('*.zip'), binding each item to path.
    for path in sorted(list(ROOT.glob('*.zip')) + list((ROOT / 'deliverables').glob('*.zip'))):
        # Enter the result of zipfile.ZipFile(path) as z and run the enclosed operations within that context.
        with zipfile.ZipFile(path) as z:
            # Set entries to an empty list.
            entries = []
            # Iterate over the result of z.infolist(), binding each item to i.
            for i in z.infolist():
                # Run this branch when whether i is an existing directory.
                if i.is_dir():
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Set name to the result of i.filename.replace(the text '\\', the text '/').
                name = i.filename.replace('\\', '/')
                # Set h to the hexadecimal digest from hashlib.sha256(z.read(i)).
                h = hashlib.sha256(z.read(i)).hexdigest()
                # Append a dictionary built from the supplied values to entries.
                entries.append(dict(path=name, bytes=i.file_size, sha256=h))
            # Run this branch when path equals final.
            if path == final:
                # Set final_hashes to a dictionary of i at 'path' mapped to i at 'sha256' for i in entries.
                final_hashes = {i['path']: i['sha256'] for i in entries}
            # Set archives[str(path.relative_to(ROOT))] to a dictionary built from the supplied values.
            archives[str(path.relative_to(ROOT))] = dict(
                # Supply bytes as path.stat().st_size.
                # Supply sha256 as the result of digest(path).
                # Supply crc_error as the result of z.testzip().
                bytes=path.stat().st_size, sha256=digest(path), crc_error=z.testzip(),
                # Supply files as the number of entries in entries.
                # Supply uncompressed_bytes as the sum of a lazy sequence of i at 'bytes' for i in entries.
                files=len(entries), uncompressed_bytes=sum(i['bytes'] for i in entries),
                # Supply top_levels as a dictionary built from the result of Counter(a lazy sequence of
                # i['path'].split('/') at 0 for i in entries).
                # Supply entries as entries.
                top_levels=dict(Counter(i['path'].split('/')[0] for i in entries)), entries=entries)
    # Set probes to an empty dictionary.
    probes = {}
    # Iterate over a list containing the text '.demo_probe_b7b08c60', the text '.presentation_probe_20261016', the
    # text..., binding each item to relative.
    for relative in ['.demo_probe_b7b08c60', '.presentation_probe_20261016',
                     'component_2_right_of_way_negotiation/results/final_readiness/20261016/package_import_probe']:
        # Set folder to ROOT divided by relative.
        folder = ROOT / relative
        # Set entries to an empty list.
        entries = []
        # Iterate over the result of folder.rglob(the text '*'), binding each item to p.
        for p in folder.rglob('*'):
            # Run this branch when the negation of whether p is an existing file.
            if not p.is_file():
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set name to the result of p.relative_to(folder).as_posix().
            name = p.relative_to(folder).as_posix()
            # Set h to the result of digest(p).
            h = digest(p)
            # Set canonical to ROOT divided by name.
            canonical = ROOT / name
            # Set matches to an empty list.
            matches = []
            # Run this branch when whether canonical is an existing file and the result of digest(canonical)
            # equals h.
            if canonical.is_file() and digest(canonical) == h:
                # Append the text 'canonical' to matches.
                matches.append('canonical')
            # Iterate over key/value pairs from archives, binding each item to (archive_name, archive).
            for archive_name, archive in archives.items():
                # Iterate over archive at 'entries', binding each item to item.
                for item in archive['entries']:
                    # Run this branch when item at 'path' equals name and item at 'sha256' equals h.
                    if item['path'] == name and item['sha256'] == h:
                        # Append archive_name to matches.
                        matches.append(archive_name)
                        # Leave the nearest enclosing loop immediately.
                        break
            # Set generated to the text '__pycache__' belongs to p.parts or the text '.pytest_cache' belongs to
            # p.parts.
            generated = '__pycache__' in p.parts or '.pytest_cache' in p.parts
            # Append a dictionary built from the supplied values to entries.
            entries.append(dict(path=name, bytes=p.stat().st_size, sha256=h,
                                # Supply matches as matches.
                                # Supply generated_cache as generated.
                                matches=matches, generated_cache=generated))
        # Set probes[relative] to a dictionary built from the supplied values.
        probes[relative] = dict(files=len(entries), bytes=sum(i['bytes'] for i in entries),
                               # Supply unique_noncache as a list of i for i in entries; retain entries satisfying
                               # the negation of i at 'matches' and the negation of i at 'generated_cache'.
                               unique_noncache=[i for i in entries if not i['matches'] and not i['generated_cache']],
                               # Supply entries as entries.
                               entries=entries)
    # Set receipt to a dictionary built from the supplied values.
    receipt = dict(root=str(ROOT), trees=trees, archives=archives, probes=probes,
                   # Supply final_sha256 as the result of digest(final).
                   # Supply final_entries as the number of entries in final_hashes.
                   final_sha256=digest(final), final_entries=len(final_hashes),
                   # Supply backup_verified as False.
                   # Supply cleanup_executed as False.
                   backup_verified=False, cleanup_executed=False)
    # Set target to OUT joined with the path segment 'pre_cleanup_audit.json'.
    target = OUT / 'pre_cleanup_audit.json'
    # Enter the result of target.open(the text 'x') as stream and run the enclosed operations within that context.
    with target.open('x', encoding='utf-8') as stream:
        # Call json.dump with the supplied arguments.
        json.dump(receipt, stream, indent=2)
    # Display the serialized data produced by json.dumps.
    print(json.dumps(dict(trees=trees,
        # Supply archives as a dictionary of k mapped to a dictionary of a mapped to b for (a, b) in key/value
        # pairs from v; retain entries satisfying a differs from the text 'entries' for (k, v) in key/value pairs
        # from archives.
        archives={k: {a: b for a, b in v.items() if a != 'entries'} for k, v in archives.items()},
        # Supply indent as 2.
        # Supply probes as a dictionary of k mapped to a dictionary of a mapped to b for (a, b) in key/value pairs
        # from v; retain entries satisfying a differs from the text 'entries' for (k, v) in key/value pairs from
        # probes.
        probes={k: {a: b for a, b in v.items() if a != 'entries'} for k, v in probes.items()}), indent=2))


# Run this branch when __name__ equals the text '__main__'.
if __name__ == '__main__':
    # Call main with the supplied arguments.
    main()
