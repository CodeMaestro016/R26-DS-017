"""Verify measured acceptance and produce separate diagnostic comparisons."""
from collections import Counter
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/final_live_correction/20261016'
RUNS=BASE/'results/vehicle_state_consistency/20261016'
POLICY_HASH='2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory):
    receipt=read(directory/'receipt.json');runtime=read(directory/'runtime_result.json')
    metrics=receipt['metrics']
    assert receipt['policy_hash']==POLICY_HASH and runtime['policy_hash_unchanged']
    assert metrics['collision_count']==metrics['blocked_zone_violation_count']==receipt['unauthorized_entries']==0
    assert receipt['stats']['wrong_permission_color']==receipt['stats']['highlight_overrides']==0
    assert metrics['maximum_negotiation_participants']<=4
    assert runtime['decentralized_execution'] and not runtime['centralized_execution_graph_used_for_control']
    assert all(runtime[k]==0 for k in ('centralized_critic_calls','training_operations','backward_calls','optimizer_steps','parameter_updates'))
    assert runtime['supplementary_fallback_protocol']=='MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1'
    assert runtime['native_junction_hold_protocol']=='NATIVE_EXPLICIT_JUNCTION_HOLD_V1'
    transitions=[];prior={};since=None;maximum=0;mandatory_holds=0
    for line in (directory/'synchronized_frames.jsonl').open(encoding='utf-8'):
        frame=json.loads(line);now=frame['timestamp'];vehicles=frame['rows']
        stopped=bool(vehicles) and all(r['vehicle']['speed_mps']<.5 for r in vehicles)
        if stopped:
            since=now if since is None else since;maximum=max(maximum,now-since)
        else:since=None
        for row in vehicles:
            vehicle=row['vehicle'];ego=vehicle['id'];decision=row['decision']
            if prior.get(ego)=='BLOCKED' and vehicle['display_state']=='READY':
                assert decision['permission']=='PERMITTED'
                transitions.append(dict(ego_id=ego,timestamp=now,
                    current_mappo_receipt=vehicle['negotiation']['current_receipt'],
                    last_event_timestamp=vehicle['negotiation']['last_event_timestamp'],
                    reason=decision['reason']))
            prior[ego]=vehicle['display_state']
            priorities={c['priority_vehicle_id'] for c in decision['mandatory']
                        if c['yielding_vehicle_id']==ego}
            if priorities.intersection(z[2] for z in decision['blocked_zones']):mandatory_holds+=1
    event_proof=[]
    for event in runtime['events']:
        if event['mappo_invocation']!='AUTHORIZED':continue
        assert len(event['participants'])<=4
        for factor in event['policy_factor_diagnostics']:
            assert factor['ego_id'] in event['participants']
            assert factor['hard_action_mask'][factor['selected_action_index']]
            assert factor['selected_action']==factor['action_names'][factor['selected_action_index']]
        crossings=[entry for entry in receipt['entries'] if entry['prior_decision']['coordination_epoch']
                   and entry['prior_decision']['coordination_epoch'][1]==event['timestamp']]
        # Source epoch timestamp is also recorded explicitly below; retain raw
        # evidence where an episode uses a differently shaped snapshot identity.
        event_proof.append(dict(timestamp=event['timestamp'],participants=event['participants'],
            proposer_actions=event['proposer_actions'],responder_actions=event['responder_actions'],
            original=event['original_regulatory_graph'],effective=event['effective_coordination_graph'],
            execution_outcome=event.get('execution_outcome'),crossings=crossings,
            completed_participants=[v for v in event['participants'] if v in runtime['completed_vehicle_ids']]))
    native=Counter(d['event'] for d in runtime['diagnostics'] if d.get('event','').startswith('NATIVE_HOLD_'))
    return dict(scenario=receipt['scenario'],fault=receipt['injected_fault'],
        evidence_directory=directory.relative_to(BASE).as_posix(),metrics=metrics,
        unauthorized_entries=receipt['unauthorized_entries'],wall_seconds=receipt['wall_seconds'],
        observed_all_active_stationary_max_seconds=round(maximum,3),
        stationary_sampling_interval_seconds=.16,mandatory_hold_vehicle_samples=mandatory_holds,
        held_to_ready_transitions=transitions,real_mappo_events=event_proof,
        native_stop_events=dict(native),source_hashes=receipt['source_hashes'])


def main():
    paths=sorted((RUNS/'final_corrected_native_v1_220').glob('*/receipt.json'))
    paths += [RUNS/f'final_corrected_native_v1_{h}/congested_four_approach/receipt.json' for h in (70,360)]
    paths += sorted((RUNS/'final_corrected_native_v1_45').glob('*/receipt.json'))
    assert len(paths)==14
    records=[audit(p.parent) for p in paths]
    full=next(r for r in records if r['scenario']=='congested_four_approach' and r['metrics']['total_vehicles_completed']==16)
    assert full['metrics']['total_vehicles_spawned']==16
    assert len({r['source_hashes']['runtime_simulation/runner.py'] for r in records})==1
    assert len({r['source_hashes']['negotiation_execution/ego_controller.py'] for r in records})==1
    old70=read(RUNS/'after_v1/congested_four_approach/receipt.json')
    old360=read(BASE/'results/live_deadlock_investigation/20261016/reconciled_release_fix_v1/congested_four_approach/receipt.json')
    comparisons=[]
    for horizon,before in [(70,old70),(360,old360)]:
        after=next(r for r in records if r['scenario']=='congested_four_approach'
                   and f'_{horizon}/' in r['evidence_directory'])
        prior_runtime=read((RUNS/'after_v1/congested_four_approach' if horizon==70 else
            BASE/'results/live_deadlock_investigation/20261016/reconciled_release_fix_v1/congested_four_approach')/'runtime_result.json')
        current_runtime=read(BASE/after['evidence_directory']/'runtime_result.json')
        for key in ('presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds'):
            assert prior_runtime[key]==current_runtime[key],key
        comparisons.append(dict(horizon=horizon,before=before['metrics'],after=after['metrics']))
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    changed_history=[p for p,h in historical.items() if sha(BASE/p)!=h['sha256']]
    assert not changed_history, changed_history
    protected=read(BASE/'results/final_readiness/20261016/protected_source_inventory.json')
    changed_sources=[p for p,h in protected.items() if sha(BASE/p)!=h]
    assert set(p.replace('\\','/') for p in changed_sources)=={
        'runtime_simulation/browser_state.py','runtime_simulation/runner.py',
        'negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    identity=read(OUT/'approved_source_identity.json')
    assert all(sha(BASE/p)==h and sha(OUT/'source_after'/p)==h for p,h in identity.items())
    ui_identity=read(OUT/'showcase_source_identity_local_browser_v1.json')
    assert all(sha(BASE.parent/'socialmind_drive_showcase'/p)==h and
        sha(OUT/'source_after_local_browser_v1/socialmind_drive_showcase'/p)==h
        for p,h in ui_identity.items())
    server=read(OUT/'server_shutdown_synchronized_v1/receipt.json')
    clients=read(OUT/'client_lifecycle_v10/receipt.json')
    assert clients['shutdown_process_closed'] and not clients['lifecycle_errors']
    assert clients['no_accumulated_live_targets'] and clients['new_client_preferences_reset']
    assert server['matched_independent_simulator_frames']==server['matched_http_svg_frames']
    assert not server['remaining_owned_pids'] and not server['unhandled_traceback']
    browser=read(OUT/'local_browser_v4/receipt.json')
    assert 'failure' not in browser and not browser['page_errors'] and not browser['failed_requests']
    assert not browser['remaining_owned_processes']
    assert browser['navigate_reload_close_reopen'] and browser['stop_relaunch']
    assert browser['independent_browser_preferences'] and browser['shutdown_while_runtime_active']
    assert browser['matching_http_dom_frames']>=3 and browser['moving_red_samples']>0
    assert any(t['permission']['authorized'] and t['negotiation']['current_receipt']
               for t in browser['held_to_ready_transitions'])
    actors=RUNS/'http_synchronized_v1/regulatory_cycle/actor_inputs_and_actions.jsonl'
    inputs=[json.loads(line) for line in actors.open(encoding='utf-8')]
    assert len(inputs)==6
    for row in inputs:
        factor=row['actual_factor'];snapshot=factor['actor_observation_snapshot']
        assert factor['hard_action_mask'][factor['selected_action_index']]
        assert snapshot['source_timestamp']==23.24
        assert not factor['ppo_update_eligible']
    negative=audit(RUNS/'negative_mandatory_cycle_v1/regulatory_cycle__mandatory_constraint_cycle')
    assert any('RETAINED_MANDATORY_OR_COMMITMENT_CYCLE' in line for line in
        (BASE/negative['evidence_directory']/'timeline.jsonl').open(encoding='utf-8'))
    report=dict(classification='QUALITATIVE_DIAGNOSTIC_NOT_FROZEN_FINAL_EVALUATION',
        records=records,comparisons=comparisons,synthetic_mandatory_cycle=negative,
        unchanged_historical_files=len(historical),unchanged_protected_sources=len(protected)-len(changed_sources),
        intentional_changes_since_original_inventory=changed_sources,checkpoint_sha256=POLICY_HASH,
        synchronized_server=server,client_lifecycle=clients,local_chromium=browser,
        actual_actor_input_factors=len(inputs),verified_showcase_source_identity=ui_identity)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# Final live correction: measured diagnostic results','',
        'These are new deterministic presentation diagnostics, not a replacement for the frozen final evaluation.','',
        '| Scenario / fault | Spawned | Completed | MAPPO | Fallback epochs | Mean wait s | Max wait s | Approach gap s | Throughput / min | All-active stopped max s |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in records+[negative]:
        m=r['metrics'];label=r['scenario']+(' / '+r['fault'] if r['fault'] else '')
        if r['scenario']=='congested_four_approach':label+=' / '+('70 s' if '_70/' in r['evidence_directory'] else '360 s budget')
        gap=m['approach_waiting_time_gap_seconds']
        gap_label=f'{gap:.3f}' if gap is not None else 'N/A'
        lines.append(f"| {label} | {m['total_vehicles_spawned']} | {m['total_vehicles_completed']} | {m['mappo_inference_call_count']} | {m.get('fallback_activations',0)} | {m['mean_waiting_time_seconds']:.3f} | {m['maximum_waiting_time_seconds']:.3f} | {gap_label} | {m['throughput_vehicles_per_minute']:.3f} | {r['observed_all_active_stationary_max_seconds']:.2f} |")
    lines += ['', 'All rows: zero observed collisions, blocked-zone violations and unauthorized entries.',
        'The mandatory-cycle row is injected contradictory constraint evidence, not a newly invented legal movement scenario.',
        'Stationary duration is sampled at the existing 0.16-second publisher interval. The unchanged `deadlock_observed` metric flags any individual incoming vehicle stopped for 15 seconds; it can be true in a completed, progressing episode.', '',
        '| Dense budget | Completion before → after | Mean wait before → after s | Max wait before → after s | Approach gap before → after s | Throughput before → after / min |',
        '|---|---|---|---|---|---|']
    for c in comparisons:
        b,a=c['before'],c['after']
        lines.append(f"| {c['horizon']} s | {b['total_vehicles_completed']}/16 → {a['total_vehicles_completed']}/16 | {b['mean_waiting_time_seconds']:.3f} → {a['mean_waiting_time_seconds']:.3f} | {b['maximum_waiting_time_seconds']:.3f} → {a['maximum_waiting_time_seconds']:.3f} | {b['approach_waiting_time_gap_seconds']:.3f} → {a['approach_waiting_time_gap_seconds']:.3f} | {b['throughput_vehicles_per_minute']:.3f} → {a['throughput_vehicles_per_minute']:.3f} |")
    lines+=['',f"Integrity: {len(historical)} historical files unchanged; {len(protected)-len(changed_sources)} protected source/model files unchanged. The four listed source differences include the earlier approved revisions.",
        f"Synchronized actual-simulator/publisher/HTTP/SVG frames: {server['matched_http_svg_frames']}. Local Chromium additionally verified {browser['sampled_dom_frames']} actual DOM frames, including {browser['matching_http_dom_frames']} matching HTTP/DOM frames.",
        'Dense full run per-approach mean waits: '+json.dumps(full['metrics']['per_approach_mean_waiting_time_seconds']),
        'Detailed metrics, sampled transitions, per-event MAPPO evidence and timestamps: `results/final_live_correction/20261016/verification.json`.']
    (BASE/'docs/FINAL_LIVE_CORRECTION_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(real_cases=len(records),dense_completed=full['metrics']['total_vehicles_completed'],historical_unchanged=len(historical),http_frames=server['matched_http_svg_frames'])))


if __name__=='__main__':main()
