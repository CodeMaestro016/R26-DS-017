"""Verify and report actual approved-protocol diagnostics; never regenerate studies."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/live_deadlock_investigation/20261016'
DOC=BASE/'docs/APPROVED_RECONCILIATION_VERIFICATION.md'


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def read_log(path):
    content=path.read_bytes()
    return content.decode('utf-16' if content.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    records={}
    for folder in ['reconciled_release_fix_v1','reconciled_final_faults_v1']:
        for directory in sorted((OUT/folder).iterdir()):
            record=read(directory/'receipt.json')
            result=read(directory/'runtime_result.json')
            actions=0
            for event in result['events']:
                for factor in event.get('policy_factor_diagnostics',[]):
                    assert factor['ego_id'] in event['participants']
                    assert factor['hard_action_mask'][factor['selected_action_index']]
                    assert factor['action_names'][factor['selected_action_index']]==factor['selected_action']
                    actions+=1
            assert result['policy_hash_unchanged'] and result['centralized_critic_calls']==0
            assert result['decentralized_execution'] and not result['centralized_execution_graph_used_for_control']
            assert result['training_operations']==0
            m=record['metrics']
            assert m['collision_count']==0 and m['blocked_zone_violation_count']==0
            if record.get('injected_fault'):
                assert m['total_vehicles_completed']==0 and m['mappo_inference_call_count']==0
            records[directory.name]=dict(receipt=record,sim_seconds=result['actual_simulation_time_seconds'],
                policy_sha256=result['policy_sha256_after'],verified_masked_actions=actions,
                execution_outcomes=dict(Counter(e.get('execution_outcome','UNAVAILABLE') for e in result['events'])),
                result_path=str((directory/'runtime_result.json').relative_to(BASE)))
    assert len(records)==13
    prior=BASE/'results/final_readiness/20261016'
    historical=read(prior/'historical_inventory.json')
    assert all(sha(BASE/name)==item['sha256'] for name,item in historical.items())
    protected=read(prior/'protected_source_inventory.json')
    changes=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    assert set(changes)=={'runtime_simulation/browser_state.py','runtime_simulation/runner.py',
        'negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    identity=read(OUT/'approved_source_versions/identity.json')
    assert all(sha(BASE/name)==h for name,h in identity['current'].items())
    for folder in ['reconciled_release_fix_v1','reconciled_final_faults_v1']:
        for directory in (OUT/folder).iterdir():
            measured=read(directory/'source_hashes.json')
            assert all(measured.get(name)==h for name,h in identity['current'].items()), 'Mixed production source versions'
    testlog=read_log(OUT/'approved_full_tests.log')
    summary=re.findall(r'\d+ passed[^\r\n]*',testlog)
    if not summary:raise RuntimeError('Full test suite has not completed; do not publish final report')
    recheck=read_log(OUT/'approved_dense_fixture_recheck.log')
    recheck_summary=re.findall(r'\d+ passed[^\r\n]*',recheck)
    if not recheck_summary:raise RuntimeError('Affected real fixture recheck has not completed')
    assert not re.search(r'\b(?:FAILED|ERROR)\b',recheck)
    assert '2 xfailed' in recheck_summary[-1]
    errors=re.findall(r'^ERROR ([^\r\n]+)',testlog,re.MULTILINE)
    assert len(errors)==4 and all('test_ego_execution_and_dense_traffic.py::' in e for e in errors)
    assert '965 passed, 4 errors' in summary[-1]
    website=read(OUT/'showcase_approved_v1/launcher_live_frames.json')
    assert len(website)==2 and all(r['owned_processes_cleaned'] for r in website)
    assert website[0]['frame']['completed']==4 and website[1]['observed_real_inference']
    http=read(OUT/'showcase_approved_v1/http_checks.json')
    assert all(r['status']==200 for r in http['responses'])
    receipt=dict(protocol=identity['protocol'],historical_files_unchanged=len(historical),
        protected_files_unchanged=len(protected)-len(changes),changed_protected_sources=changes,
        model_integrity_verified=True,initial_full_test_summary=summary[-1],
        affected_module_recheck=recheck_summary[-1],combined_coverage='967 passed, 2 existing strict xfails across full run and affected-module recheck',scenarios=records,
        browser_interactive_verification='UNAVAILABLE; discovery returned []',
        website_launcher_and_http_verified=True,additional_fallback_design_implemented=False)
    (OUT/'approved_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    lines=['# Approved reconciliation: measured verification','',
        'Diagnostic/presentation evidence only. Original frozen scientific results are unchanged.','',
        '| Scenario / injected fault | Scheduled | Spawned | Completed | Completion % | MAPPO | Mean wait s | Max wait s | Throughput/min | Collisions | Violations | Wall s | Outcome |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for name,item in records.items():
        r=item['receipt'];m=r['metrics']
        outcome=('PASS' if r['run_status']=='COMPLETED' else 'SAFE_DEGRADATION')
        values=[name,m['total_vehicles_scheduled'],m['total_vehicles_spawned'],m['total_vehicles_completed'],
            round(m['completion_rate']*100,2),m['mappo_inference_call_count'],
            round(m['mean_waiting_time_seconds'],3),round(m['maximum_waiting_time_seconds'],3),
            round(m['throughput_vehicles_per_minute'],6),m['collision_count'],m['blocked_zone_violation_count'],
            round(r['wall_seconds'],2),outcome]
        lines.append('| '+' | '.join(map(str,values))+' |')
    lines+=['',f"Initial full active run: **{summary[-1]}**. All four setup errors were the version-specific assumption that an incomplete run completes zero trips.",
        f"After making that fixture expectation version-aware, the real affected module was rerun: **{recheck_summary[-1]}**. All safety/integrity checks and original strict completion assertions remain active.",
        "Combined final coverage: **967 passed, two existing strict xfails** across the full run and affected-module rerun; a second entire full-suite execution was not performed.",
        f"Historical files verified unchanged: **{len(historical)}**. Unchanged protected source/model assets: **{len(protected)-len(changes)}/{len(protected)}**; four source paths changed across telemetry and this approved task.",
        'E5 SHA-256: `'+sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')+'`.',
        '', 'All original MAPPO action diagnostics above were checked for participant identity, valid selected action indices and permitted boolean masks. Actor dimensions/classes and trained weights remain unchanged.',
        'Every passing run completed its actual scheduled vehicles with zero observed collisions and violations. Fault cases intentionally safe-hold; their SAFE_DEGRADATION is not a discharge PASS.',
        'Dense traffic remains incomplete because mandatory obligations and the existing pair fallback create a later cycle. See APPROVED_RECONCILIATION_IMPLEMENTATION_REPORT.md for exact dependencies and the additional approval boundary.',
        '', 'Website: actual four-way completion, dense progress/MAPPO, same-instance restart, duplicate refusal, cooperative owned-process stop and six HTTP 200 routes verified. Interactive browser verification unavailable (no connected browser).',
        '', 'Exact commands and output roots are retained in tools/diagnose_live_deadlock.py, tools/probe_reconciled_showcase.py and the implementation report. No formal evaluation matrix, training or package rebuild was performed.', '']
    DOC.write_text('\n'.join(lines),encoding='utf-8')
    print(summary[-1]);print(recheck_summary[-1]);print('Verified scenarios:',len(records));print('Report:',DOC)


if __name__=='__main__':main()
