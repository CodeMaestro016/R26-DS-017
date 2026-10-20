"""Verify and report actual approved-protocol diagnostics; never regenerate studies."""
# Import Counter from collections for the operations below.
from collections import Counter
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import re for use in this module.
import re

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/live_deadlock_investigation/20261016'.
OUT=BASE/'results/live_deadlock_investigation/20261016'
# Set DOC to BASE joined with the path segment 'docs/APPROVED_RECONCILIATION_VERIFICATION.md'.
DOC=BASE/'docs/APPROVED_RECONCILIATION_VERIFICATION.md'


# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
# Return the decoded data produced by json.loads from the text read from path to the caller.
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
# Read log using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the result of content.decode(the text 'utf-16' when the result of content.startswith(a tuple containing
# b'\xff\xfe',...).
def read_log(path):
    # Set content to the bytes read from path.
    content=path.read_bytes()
    # Return the result of content.decode(the text 'utf-16' when the result of content.startswith(a tuple
    # containing b'\xff\xfe',...) to the caller.
    return content.decode('utf-16' if content.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace')
# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from h.
# Processing: iterate over the relevant records.
def sha(path):
    # Set h to the result of hashlib.sha256().
    h=hashlib.sha256()
    # Enter the result of path.open(the text 'rb') as f and run the enclosed operations within that context.
    with path.open('rb') as f:
        # Iterate over the result of iter(a callback that returns the result of f.read(1024 multiplied by 1024),
        # b''), binding each item to block.
        # Update h with the supplied entries.
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    # Return the hexadecimal digest from h to the caller.
    return h.hexdigest()


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set records to an empty dictionary.
    records={}
    # Iterate over a list containing the text 'reconciled_release_fix_v1', the text 'reconciled_final_faults_v1',
    # binding each item to folder.
    for folder in ['reconciled_release_fix_v1','reconciled_final_faults_v1']:
        # Iterate over the sorted values from the result of (OUT / folder).iterdir(), binding each item to
        # directory.
        for directory in sorted((OUT/folder).iterdir()):
            # Set record to the result of read(directory joined with the path segment 'receipt.json').
            record=read(directory/'receipt.json')
            # Set result to the result of read(directory joined with the path segment 'runtime_result.json').
            result=read(directory/'runtime_result.json')
            # Set actions to 0.
            actions=0
            # Iterate over result at 'events', binding each item to event.
            for event in result['events']:
                # Iterate over 'policy_factor_diagnostics' from event; use an empty list if absent, binding each
                # item to factor.
                for factor in event.get('policy_factor_diagnostics',[]):
                    # Require factor at 'ego_id' belongs to event at 'participants'; otherwise raise
                    # AssertionError.
                    assert factor['ego_id'] in event['participants']
                    # Require factor['hard_action_mask'] at factor['selected_action_index']; otherwise raise
                    # AssertionError.
                    assert factor['hard_action_mask'][factor['selected_action_index']]
                    # Require factor['action_names'] at factor['selected_action_index'] equals factor at
                    # 'selected_action'; otherwise raise AssertionError.
                    assert factor['action_names'][factor['selected_action_index']]==factor['selected_action']
                    # Update actions to its current value plus 1.
                    actions+=1
            # Require result at 'policy_hash_unchanged' and result at 'centralized_critic_calls' equals 0;
            # otherwise raise AssertionError.
            assert result['policy_hash_unchanged'] and result['centralized_critic_calls']==0
            # Require result at 'decentralized_execution' and the negation of result at
            # 'centralized_execution_graph_used_for_control'; otherwise raise AssertionError.
            assert result['decentralized_execution'] and not result['centralized_execution_graph_used_for_control']
            # Require result at 'training_operations' equals 0; otherwise raise AssertionError.
            assert result['training_operations']==0
            # Set m to record at 'metrics'.
            m=record['metrics']
            # Require m at 'collision_count' equals 0 and m at 'blocked_zone_violation_count' equals 0; otherwise
            # raise AssertionError.
            assert m['collision_count']==0 and m['blocked_zone_violation_count']==0
            # Run this branch when 'injected_fault' from record; use None if absent.
            if record.get('injected_fault'):
                # Require m at 'total_vehicles_completed' equals 0 and m at 'mappo_inference_call_count' equals 0;
                # otherwise raise AssertionError.
                assert m['total_vehicles_completed']==0 and m['mappo_inference_call_count']==0
            # Set records[directory.name] to a dictionary built from the supplied values.
            records[directory.name]=dict(receipt=record,sim_seconds=result['actual_simulation_time_seconds'],
                # Supply policy_sha256 as result at 'policy_sha256_after'.
                # Supply verified_masked_actions as actions.
                policy_sha256=result['policy_sha256_after'],verified_masked_actions=actions,
                # Supply execution_outcomes as a dictionary built from the result of Counter(a lazy sequence of
                # 'execution_outcome' from e; use 'UNAVAILABLE' if absent for e in result at...).
                execution_outcomes=dict(Counter(e.get('execution_outcome','UNAVAILABLE') for e in result['events'])),
                # Supply result_path as a string built from the result of (directory /
                # 'runtime_result.json').relative_to(BASE).
                result_path=str((directory/'runtime_result.json').relative_to(BASE)))
    # Require the number of entries in records equals 13; otherwise raise AssertionError.
    assert len(records)==13
    # Set prior to BASE joined with the path segment 'results/final_readiness/20261016'.
    prior=BASE/'results/final_readiness/20261016'
    # Set historical to the result of read(prior joined with the path segment 'historical_inventory.json').
    historical=read(prior/'historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / name) equals item at
    # 'sha256' for (name, item) in key/value pairs from historical; otherwise raise AssertionError.
    assert all(sha(BASE/name)==item['sha256'] for name,item in historical.items())
    # Set protected to the result of read(prior joined with the path segment 'protected_source_inventory.json').
    protected=read(prior/'protected_source_inventory.json')
    # Set changes to a list of the result of name.replace(the text '\\', the text '/') for (name, h) in key/value
    # pairs from protected; retain entries satisfying the result of sha(BASE divided by name) differs from h.
    changes=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    # Require a set built from changes equals a set containing the text 'runtime_simulation/browser_state.py', the
    # text 'runtime_simulation/runner.py', the text...; otherwise raise AssertionError.
    assert set(changes)=={'runtime_simulation/browser_state.py','runtime_simulation/runner.py',
        'negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    # Set identity to the result of read(OUT joined with the path segment 'approved_source_versions/identity.json').
    identity=read(OUT/'approved_source_versions/identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / name) equals h for (name,
    # h) in key/value pairs from identity['current']; otherwise raise AssertionError.
    assert all(sha(BASE/name)==h for name,h in identity['current'].items())
    # Iterate over a list containing the text 'reconciled_release_fix_v1', the text 'reconciled_final_faults_v1',
    # binding each item to folder.
    for folder in ['reconciled_release_fix_v1','reconciled_final_faults_v1']:
        # Iterate over the result of (OUT / folder).iterdir(), binding each item to directory.
        for directory in (OUT/folder).iterdir():
            # Set measured to the result of read(directory joined with the path segment 'source_hashes.json').
            measured=read(directory/'source_hashes.json')
            # Require whether every item is true in a lazy sequence of name from measured; use None if absent
            # equals h for (name, h) in key/value pairs from identity['current']; otherwise raise AssertionError
            # with the text 'Mixed production source versions'.
            assert all(measured.get(name)==h for name,h in identity['current'].items()), 'Mixed production source versions'
    # Set testlog to the result of read_log(OUT joined with the path segment 'approved_full_tests.log').
    testlog=read_log(OUT/'approved_full_tests.log')
    # Set summary to the result of re.findall(the text '\\d+ passed[^\\r\\n]*', testlog).
    summary=re.findall(r'\d+ passed[^\r\n]*',testlog)
    # Run this branch when the negation of summary.
    # Raise RuntimeError with the text 'Full test suite has not completed; do not publish final report' to stop
    # this execution path.
    if not summary:raise RuntimeError('Full test suite has not completed; do not publish final report')
    # Set recheck to the result of read_log(OUT joined with the path segment 'approved_dense_fixture_recheck.log').
    recheck=read_log(OUT/'approved_dense_fixture_recheck.log')
    # Set recheck_summary to the result of re.findall(the text '\\d+ passed[^\\r\\n]*', recheck).
    recheck_summary=re.findall(r'\d+ passed[^\r\n]*',recheck)
    # Run this branch when the negation of recheck_summary.
    # Raise RuntimeError with the text 'Affected real fixture recheck has not completed' to stop this execution
    # path.
    if not recheck_summary:raise RuntimeError('Affected real fixture recheck has not completed')
    # Require the negation of the result of re.search(the text '\\b(?:FAILED|ERROR)\\b', recheck); otherwise raise
    # AssertionError.
    assert not re.search(r'\b(?:FAILED|ERROR)\b',recheck)
    # Require the text '2 xfailed' belongs to recheck_summary at -1; otherwise raise AssertionError.
    assert '2 xfailed' in recheck_summary[-1]
    # Set errors to the result of re.findall(the text '^ERROR ([^\\r\\n]+)', testlog, re.MULTILINE).
    errors=re.findall(r'^ERROR ([^\r\n]+)',testlog,re.MULTILINE)
    # Require the number of entries in errors equals 4 and whether every item is true in a lazy sequence of
    # 'test_ego_execution_and_dense_traffic.py::' belongs to e for e in errors; otherwise raise AssertionError.
    assert len(errors)==4 and all('test_ego_execution_and_dense_traffic.py::' in e for e in errors)
    # Require the text '965 passed, 4 errors' belongs to summary at -1; otherwise raise AssertionError.
    assert '965 passed, 4 errors' in summary[-1]
    # Set website to the result of read(OUT joined with the path segment 'showcase_approved_v1/launcher_live_frames.json').
    website=read(OUT/'showcase_approved_v1/launcher_live_frames.json')
    # Require the number of entries in website equals 2 and whether every item is true in a lazy sequence of r at
    # 'owned_processes_cleaned' for r in website; otherwise raise AssertionError.
    assert len(website)==2 and all(r['owned_processes_cleaned'] for r in website)
    # Require website[0]['frame'] at 'completed' equals 4 and website[1] at 'observed_real_inference'; otherwise
    # raise AssertionError.
    assert website[0]['frame']['completed']==4 and website[1]['observed_real_inference']
    # Set http to the result of read(OUT joined with the path segment 'showcase_approved_v1/http_checks.json').
    http=read(OUT/'showcase_approved_v1/http_checks.json')
    # Require whether every item is true in a lazy sequence of r at 'status' equals 200 for r in http at
    # 'responses'; otherwise raise AssertionError.
    assert all(r['status']==200 for r in http['responses'])
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(protocol=identity['protocol'],historical_files_unchanged=len(historical),
        # Supply protected_files_unchanged as the number of entries in protected minus the number of entries in
        # changes.
        # Supply changed_protected_sources as changes.
        protected_files_unchanged=len(protected)-len(changes),changed_protected_sources=changes,
        # Supply model_integrity_verified as True.
        # Supply initial_full_test_summary as summary at -1.
        model_integrity_verified=True,initial_full_test_summary=summary[-1],
        # Supply affected_module_recheck as recheck_summary at -1.
        # Supply combined_coverage as the text '967 passed, 2 existing strict xfails across full run and...'.
        # Supply scenarios as records.
        affected_module_recheck=recheck_summary[-1],combined_coverage='967 passed, 2 existing strict xfails across full run and affected-module recheck',scenarios=records,
        # Supply browser_interactive_verification as the text 'UNAVAILABLE; discovery returned []'.
        browser_interactive_verification='UNAVAILABLE; discovery returned []',
        # Supply website_launcher_and_http_verified as True.
        # Supply additional_fallback_design_implemented as False.
        website_launcher_and_http_verified=True,additional_fallback_design_implemented=False)
    # Write the supplied text to (OUT / 'approved_verification.json').
    (OUT/'approved_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Set lines to a list containing the text '# Approved reconciliation: measured verification', the text '', the
    # text...
    lines=['# Approved reconciliation: measured verification','',
        'Diagnostic/presentation evidence only. Original frozen scientific results are unchanged.','',
        '| Scenario / injected fault | Scheduled | Spawned | Completed | Completion % | MAPPO | Mean wait s | Max wait s | Throughput/min | Collisions | Violations | Wall s | Outcome |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    # Iterate over key/value pairs from records, binding each item to (name, item).
    for name,item in records.items():
        # Set r to item at 'receipt'.
        # Set m to r at 'metrics'.
        r=item['receipt'];m=r['metrics']
        # Set outcome to the text 'PASS' when r at 'run_status' equals the text 'COMPLETED', otherwise the text
        # 'SAFE_DEGRADATION'.
        outcome=('PASS' if r['run_status']=='COMPLETED' else 'SAFE_DEGRADATION')
        # Set values to a list containing name, m at 'total_vehicles_scheduled', m at 'total_vehicles_spawned', m
        # at 'total_vehicles_completed', the...
        values=[name,m['total_vehicles_scheduled'],m['total_vehicles_spawned'],m['total_vehicles_completed'],
            # Include the rounded value of m at 'completion_rate' multiplied by 100 in this list.
            round(m['completion_rate']*100,2),m['mappo_inference_call_count'],
            # Include the rounded value of m at 'maximum_waiting_time_seconds' in this list.
            round(m['mean_waiting_time_seconds'],3),round(m['maximum_waiting_time_seconds'],3),
            # Include the rounded value of m at 'throughput_vehicles_per_minute' in this list.
            round(m['throughput_vehicles_per_minute'],6),m['collision_count'],m['blocked_zone_violation_count'],
            # Include the rounded value of r at 'wall_seconds' in this list.
            round(r['wall_seconds'],2),outcome]
        # Append the text '|' plus the result of ' | '.join(the result of map(str, values)) plus the text '|' to
        # lines.
        lines.append('| '+' | '.join(map(str,values))+' |')
    # Update lines to its current value plus a list containing the text '', formatted text built from the embedded
    # values, formatted text built from the embedded values,...
    lines+=['',f"Initial full active run: **{summary[-1]}**. All four setup errors were the version-specific assumption that an incomplete run completes zero trips.",
        # Include formatted text built from the embedded values in this list.
        f"After making that fixture expectation version-aware, the real affected module was rerun: **{recheck_summary[-1]}**. All safety/integrity checks and original strict completion assertions remain active.",
        "Combined final coverage: **967 passed, two existing strict xfails** across the full run and affected-module rerun; a second entire full-suite execution was not performed.",
        # Include formatted text built from the embedded values in this list.
        f"Historical files verified unchanged: **{len(historical)}**. Unchanged protected source/model assets: **{len(protected)-len(changes)}/{len(protected)}**; four source paths changed across telemetry and this approved task.",
        # Include the text 'E5 SHA-256: `' plus the result of sha(BASE divided by
        # 'results/final_mappo_selection_v2/selected_policy.pt') plus the text '`.' in this list.
        'E5 SHA-256: `'+sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')+'`.',
        '', 'All original MAPPO action diagnostics above were checked for participant identity, valid selected action indices and permitted boolean masks. Actor dimensions/classes and trained weights remain unchanged.',
        'Every passing run completed its actual scheduled vehicles with zero observed collisions and violations. Fault cases intentionally safe-hold; their SAFE_DEGRADATION is not a discharge PASS.',
        'Dense traffic remains incomplete because mandatory obligations and the existing pair fallback create a later cycle. See APPROVED_RECONCILIATION_IMPLEMENTATION_REPORT.md for exact dependencies and the additional approval boundary.',
        '', 'Website: actual four-way completion, dense progress/MAPPO, same-instance restart, duplicate refusal, cooperative owned-process stop and six HTTP 200 routes verified. Interactive browser verification unavailable (no connected browser).',
        '', 'Exact commands and output roots are retained in tools/diagnose_live_deadlock.py, tools/probe_reconciled_showcase.py and the implementation report. No formal evaluation matrix, training or package rebuild was performed.', '']
    # Write the supplied text to DOC.
    DOC.write_text('\n'.join(lines),encoding='utf-8')
    # Display summary at -1.
    # Display recheck_summary at -1.
    # Display the text 'Verified scenarios:'.
    # Display the text 'Report:'.
    print(summary[-1]);print(recheck_summary[-1]);print('Verified scenarios:',len(records));print('Report:',DOC)


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
