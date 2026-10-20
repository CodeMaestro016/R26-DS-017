"""Supplement the cleanup inventory with exact archive comparisons."""
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import ROOT, OUT, digest from audit_file_organization for the operations below.
from audit_file_organization import ROOT, OUT, digest


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set data to the decoded data produced by json.loads from the text read from (OUT /
    # 'pre_cleanup_audit.json').
    data = json.loads((OUT / 'pre_cleanup_audit.json').read_text(encoding='utf-8'))
    # Set a to data at 'archives'.
    a = data['archives']
    # Set comparisons to an empty dictionary.
    comparisons = {}
    # Iterate over a list containing a tuple containing the text '.demo_probe_b7b08c60.zip', the text
    # '.demo_probe_b7b08c60/', the text..., binding each item to (name, prefix, folder).
    for name, prefix, folder in [('.demo_probe_b7b08c60.zip', '.demo_probe_b7b08c60/', '.demo_probe_b7b08c60'),
                                 # Include a tuple containing the text '.presentation_probe_20261016.zip', the
                                 # text '.presentation_probe_20261016/', the text... in this list.
                                 ('.presentation_probe_20261016.zip', '.presentation_probe_20261016/', '.presentation_probe_20261016')]:
        # Set different to a list of i at 'path' for i in a[name] at 'entries'; retain entries satisfying the
        # negation of whether (ROOT / i['path']) is an existing file or the result of...
        different = [i['path'] for i in a[name]['entries']
                     # Evaluate the negation of whether (ROOT / i['path']) is an existing file or the result of
                     # digest(ROOT divided by i['path']) differs from i at 'sha256' as part of the enclosing
                     # expression.
                     if not (ROOT / i['path']).is_file() or digest(ROOT / i['path']) != i['sha256']]
        # Set comparisons[name] to a dictionary built from the supplied values.
        comparisons[name] = dict(files=a[name]['files'], mismatches=different,
                                 # Supply wrapper as prefix.
                                 # Supply matching_probe as folder.
                                 wrapper=prefix, matching_probe=folder)
    # Set comparisons['deliverables.zip'] to a dictionary built from the supplied values.
    comparisons['deliverables.zip'] = dict(mismatches=[i['path'] for i in a['deliverables.zip']['entries']
        # Evaluate the negation of whether (ROOT / i['path']) is an existing file or the result of digest(ROOT
        # divided by i['path']) differs from i at 'sha256' as part of the enclosing expression.
        if not (ROOT / i['path']).is_file() or digest(ROOT / i['path']) != i['sha256']])
    # Set original to a['R26-DS-017.zip'] at 'entries'.
    original = a['R26-DS-017.zip']['entries']
    # Set comparisons['R26-DS-017.zip'] to a dictionary built from the supplied values.
    comparisons['R26-DS-017.zip'] = dict(
        # Supply missing as a list of i at 'path' for i in original; retain entries satisfying the negation of
        # whether (ROOT / i['path']) is an existing file.
        missing=[i['path'] for i in original if not (ROOT / i['path']).is_file()],
        # Supply changed as a list of i at 'path' for i in original; retain entries satisfying whether (ROOT /
        # i['path']) is an existing file and the result of digest(ROOT /...
        changed=[i['path'] for i in original if (ROOT / i['path']).is_file() and digest(ROOT / i['path']) != i['sha256']],
        # Supply omitted_root_items as a list of n for n in data at 'trees'; retain entries satisfying n does not
        # belong to a set containing the text 'component_2_right_of_way_negotiation',...
        omitted_root_items=[n for n in data['trees'] if n not in {'component_2_right_of_way_negotiation','socialmind_drive_showcase'}])
    # Set savings to the sum of a lazy sequence of data['trees'][n] at 'bytes' for n in a list containing the text
    # '.demo_probe_b7b08c60', the text '.presentation_probe_20261016', the text...
    savings = sum(data['trees'][n]['bytes'] for n in ['.demo_probe_b7b08c60','.presentation_probe_20261016',
        '.demo_probe_b7b08c60.zip','.presentation_probe_20261016.zip','deliverables.zip','.pytest_cache'])
    # Set moved to data['trees']['R26-DS-017.zip'] at 'bytes' plus the sum of a lazy sequence of v at 'bytes' for
    # (n, v) in key/value pairs from a; retain entries satisfying n.startswith('deliverables') and 'PRESENTATION_'
    # in n.
    moved = data['trees']['R26-DS-017.zip']['bytes'] + sum(v['bytes'] for n,v in a.items()
        # Evaluate the result of n.startswith(the text 'deliverables') and the text 'PRESENTATION_' belongs to n
        # as part of the enclosing expression.
        if n.startswith('deliverables') and 'PRESENTATION_' in n)
    # Set result to a dictionary built from the supplied values.
    result = dict(comparisons=comparisons, deletion_bytes=savings, external_move_bytes=moved,
                  # Supply active_workspace_reduction_bytes as savings plus moved.
                  active_workspace_reduction_bytes=savings+moved,
                  # Supply initial_workspace_bytes as the sum of a lazy sequence of v at 'bytes' for v in values
                  # from data['trees'].
                  initial_workspace_bytes=sum(v['bytes'] for v in data['trees'].values()),
                  # Supply optional_partial_probe_bytes as
                  # data['probes']['component_2_right_of_way_negotiation/results/final_readiness/20261016/package_imp...
                  # at 'bytes'.
                  optional_partial_probe_bytes=data['probes']['component_2_right_of_way_negotiation/results/final_readiness/20261016/package_import_probe']['bytes'])
    # Enter the result of (OUT / 'archive_comparisons.json').open(the text 'x') as f and run the enclosed
    # operations within that context.
    with (OUT / 'archive_comparisons.json').open('x', encoding='utf-8') as f:
        # Call json.dump with the supplied arguments.
        json.dump(result, f, indent=2)
    # Display the serialized data produced by json.dumps.
    print(json.dumps(result, indent=2))


# Run this branch when __name__ equals the text '__main__'.
if __name__ == '__main__':
    # Call main with the supplied arguments.
    main()
