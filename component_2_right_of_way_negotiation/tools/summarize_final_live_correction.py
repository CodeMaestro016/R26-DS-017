"""Verify measured acceptance and produce separate diagnostic comparisons."""
# Import Counter from collections for the operations below.
from collections import Counter
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/final_live_correction/20261016'.
OUT=BASE/'results/final_live_correction/20261016'
# Set RUNS to BASE joined with the path segment 'results/vehicle_state_consistency/20261016'.
RUNS=BASE/'results/vehicle_state_consistency/20261016'
# Set POLICY_HASH to the text '2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'.
POLICY_HASH='2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'


# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
# Return the decoded data produced by json.loads from the text read from path to the caller.
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(path.read_bytes()).
# Return the hexadecimal digest from hashlib.sha256(path.read_bytes()) to the caller.
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


# Audit using the inputs and processing steps below.
# Input directory: the supplied directory.
# Output: a dictionary built from the supplied values.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def audit(directory):
    # Set receipt to the result of read(directory joined with the path segment 'receipt.json').
    # Set runtime to the result of read(directory joined with the path segment 'runtime_result.json').
    receipt=read(directory/'receipt.json');runtime=read(directory/'runtime_result.json')
    # Set metrics to receipt at 'metrics'.
    metrics=receipt['metrics']
    # Require receipt at 'policy_hash' equals POLICY_HASH and runtime at 'policy_hash_unchanged'; otherwise raise
    # AssertionError.
    assert receipt['policy_hash']==POLICY_HASH and runtime['policy_hash_unchanged']
    # Require metrics at 'collision_count' equals metrics at 'blocked_zone_violation_count'; equals receipt at
    # 'unauthorized_entries'; equals 0; otherwise raise AssertionError.
    assert metrics['collision_count']==metrics['blocked_zone_violation_count']==receipt['unauthorized_entries']==0
    # Require receipt['stats'] at 'wrong_permission_color' equals receipt['stats'] at 'highlight_overrides';
    # equals 0; otherwise raise AssertionError.
    assert receipt['stats']['wrong_permission_color']==receipt['stats']['highlight_overrides']==0
    # Require metrics at 'maximum_negotiation_participants' is at most 4; otherwise raise AssertionError.
    assert metrics['maximum_negotiation_participants']<=4
    # Require runtime at 'decentralized_execution' and the negation of runtime at
    # 'centralized_execution_graph_used_for_control'; otherwise raise AssertionError.
    assert runtime['decentralized_execution'] and not runtime['centralized_execution_graph_used_for_control']
    # Require whether every item is true in a lazy sequence of runtime at k equals 0 for k in a tuple containing
    # the text 'centralized_critic_calls', the text 'training_operations', the text 'backward_calls', the text...;
    # otherwise raise AssertionError.
    assert all(runtime[k]==0 for k in ('centralized_critic_calls','training_operations','backward_calls','optimizer_steps','parameter_updates'))
    # Require runtime at 'supplementary_fallback_protocol' equals the text
    # 'MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1'; otherwise raise AssertionError.
    assert runtime['supplementary_fallback_protocol']=='MANDATORY_AWARE_DECENTRALIZED_FALLBACK_V1'
    # Require runtime at 'native_junction_hold_protocol' equals the text 'NATIVE_EXPLICIT_JUNCTION_HOLD_V1';
    # otherwise raise AssertionError.
    assert runtime['native_junction_hold_protocol']=='NATIVE_EXPLICIT_JUNCTION_HOLD_V1'
    # Set transitions to an empty list.
    # Set prior to an empty dictionary.
    # Set since to None.
    # Set maximum to 0.
    # Set mandatory_holds to 0.
    transitions=[];prior={};since=None;maximum=0;mandatory_holds=0
    # Iterate over the result of (directory / 'synchronized_frames.jsonl').open(), binding each item to line.
    for line in (directory/'synchronized_frames.jsonl').open(encoding='utf-8'):
        # Set frame to the decoded data produced by json.loads from line.
        # Set now to frame at 'timestamp'.
        # Set vehicles to frame at 'rows'.
        frame=json.loads(line);now=frame['timestamp'];vehicles=frame['rows']
        # Set stopped to a Boolean built from vehicles and whether every item is true in a lazy sequence of
        # r['vehicle']['speed_mps'] is less than 0.5 for r in vehicles.
        stopped=bool(vehicles) and all(r['vehicle']['speed_mps']<.5 for r in vehicles)
        # Run this branch when stopped.
        if stopped:
            # Set since to now when since is the same object as None, otherwise since.
            # Set maximum to the maximum of maximum, now minus since.
            since=now if since is None else since;maximum=max(maximum,now-since)
        # Set since to None.
        else:since=None
        # Iterate over vehicles, binding each item to row.
        for row in vehicles:
            # Set vehicle to row at 'vehicle'.
            # Set ego to vehicle at 'id'.
            # Set decision to row at 'decision'.
            vehicle=row['vehicle'];ego=vehicle['id'];decision=row['decision']
            # Run this branch when ego from prior; use None if absent equals the text 'BLOCKED' and vehicle at
            # 'display_state' equals the text 'READY'.
            if prior.get(ego)=='BLOCKED' and vehicle['display_state']=='READY':
                # Require decision at 'permission' equals the text 'PERMITTED'; otherwise raise AssertionError.
                assert decision['permission']=='PERMITTED'
                # Append a dictionary built from the supplied values to transitions.
                transitions.append(dict(ego_id=ego,timestamp=now,
                    # Supply current_mappo_receipt as vehicle['negotiation'] at 'current_receipt'.
                    current_mappo_receipt=vehicle['negotiation']['current_receipt'],
                    # Supply last_event_timestamp as vehicle['negotiation'] at 'last_event_timestamp'.
                    last_event_timestamp=vehicle['negotiation']['last_event_timestamp'],
                    # Supply reason as decision at 'reason'.
                    reason=decision['reason']))
            # Set prior[ego] to vehicle at 'display_state'.
            prior[ego]=vehicle['display_state']
            # Set priorities to a set of c at 'priority_vehicle_id' for c in decision at 'mandatory'; retain
            # entries satisfying c at 'yielding_vehicle_id' equals ego.
            priorities={c['priority_vehicle_id'] for c in decision['mandatory']
                        # Evaluate c at 'yielding_vehicle_id' equals ego as part of the enclosing expression.
                        if c['yielding_vehicle_id']==ego}
            # Run this branch when the result of priorities.intersection(a lazy sequence of z at 2 for z in
            # decision at 'blocked_zones').
            # Update mandatory_holds to its current value plus 1.
            if priorities.intersection(z[2] for z in decision['blocked_zones']):mandatory_holds+=1
    # Set event_proof to an empty list.
    event_proof=[]
    # Iterate over runtime at 'events', binding each item to event.
    for event in runtime['events']:
        # Run this branch when event at 'mappo_invocation' differs from the text 'AUTHORIZED'.
        # Skip the rest of this loop iteration and process the next item.
        if event['mappo_invocation']!='AUTHORIZED':continue
        # Require the number of entries in event at 'participants' is at most 4; otherwise raise AssertionError.
        assert len(event['participants'])<=4
        # Iterate over event at 'policy_factor_diagnostics', binding each item to factor.
        for factor in event['policy_factor_diagnostics']:
            # Require factor at 'ego_id' belongs to event at 'participants'; otherwise raise AssertionError.
            assert factor['ego_id'] in event['participants']
            # Require factor['hard_action_mask'] at factor['selected_action_index']; otherwise raise
            # AssertionError.
            assert factor['hard_action_mask'][factor['selected_action_index']]
            # Require factor at 'selected_action' equals factor['action_names'] at
            # factor['selected_action_index']; otherwise raise AssertionError.
            assert factor['selected_action']==factor['action_names'][factor['selected_action_index']]
        # Set crossings to a list of entry for entry in receipt at 'entries'; retain entries satisfying
        # entry['prior_decision'] at 'coordination_epoch' and...
        crossings=[entry for entry in receipt['entries'] if entry['prior_decision']['coordination_epoch']
                   # Evaluate entry['prior_decision']['coordination_epoch'] at 1 equals event at 'timestamp' as
                   # part of the enclosing expression.
                   and entry['prior_decision']['coordination_epoch'][1]==event['timestamp']]
        # Source epoch timestamp is also recorded explicitly below; retain raw
        # evidence where an episode uses a differently shaped snapshot identity.
        # Append a dictionary built from the supplied values to event_proof.
        event_proof.append(dict(timestamp=event['timestamp'],participants=event['participants'],
            # Supply proposer_actions as event at 'proposer_actions'.
            # Supply responder_actions as event at 'responder_actions'.
            proposer_actions=event['proposer_actions'],responder_actions=event['responder_actions'],
            # Supply original as event at 'original_regulatory_graph'.
            # Supply effective as event at 'effective_coordination_graph'.
            original=event['original_regulatory_graph'],effective=event['effective_coordination_graph'],
            # Supply execution_outcome as 'execution_outcome' from event; use None if absent.
            # Supply crossings as crossings.
            execution_outcome=event.get('execution_outcome'),crossings=crossings,
            # Supply completed_participants as a list of v for v in event at 'participants'; retain entries
            # satisfying v belongs to runtime at 'completed_vehicle_ids'.
            completed_participants=[v for v in event['participants'] if v in runtime['completed_vehicle_ids']]))
    # Set native to the result of Counter(a lazy sequence of d at 'event' for d in runtime at 'diagnostics';
    # retain entries satisfying the...).
    native=Counter(d['event'] for d in runtime['diagnostics'] if d.get('event','').startswith('NATIVE_HOLD_'))
    # Return a dictionary built from the supplied values to the caller.
    return dict(scenario=receipt['scenario'],fault=receipt['injected_fault'],
        # Supply evidence_directory as the result of directory.relative_to(BASE).as_posix().
        # Supply metrics as metrics.
        evidence_directory=directory.relative_to(BASE).as_posix(),metrics=metrics,
        # Supply unauthorized_entries as receipt at 'unauthorized_entries'.
        # Supply wall_seconds as receipt at 'wall_seconds'.
        unauthorized_entries=receipt['unauthorized_entries'],wall_seconds=receipt['wall_seconds'],
        # Supply observed_all_active_stationary_max_seconds as the rounded value of maximum.
        observed_all_active_stationary_max_seconds=round(maximum,3),
        # Supply stationary_sampling_interval_seconds as 0.16.
        # Supply mandatory_hold_vehicle_samples as mandatory_holds.
        stationary_sampling_interval_seconds=.16,mandatory_hold_vehicle_samples=mandatory_holds,
        # Supply held_to_ready_transitions as transitions.
        # Supply real_mappo_events as event_proof.
        held_to_ready_transitions=transitions,real_mappo_events=event_proof,
        # Supply native_stop_events as a dictionary built from native.
        # Supply source_hashes as receipt at 'source_hashes'.
        native_stop_events=dict(native),source_hashes=receipt['source_hashes'])


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set paths to the sorted values from the result of (RUNS / 'final_corrected_native_v1_220').glob(the text
    # '*/receipt.json').
    paths=sorted((RUNS/'final_corrected_native_v1_220').glob('*/receipt.json'))
    # Update paths to its current value plus a list of RUNS divided by formatted text built from the embedded
    # values for h in a tuple containing 70, 360.
    paths += [RUNS/f'final_corrected_native_v1_{h}/congested_four_approach/receipt.json' for h in (70,360)]
    # Update paths to its current value plus the sorted values from the result of (RUNS /
    # 'final_corrected_native_v1_45').glob(the text '*/receipt.json').
    paths += sorted((RUNS/'final_corrected_native_v1_45').glob('*/receipt.json'))
    # Require the number of entries in paths equals 14; otherwise raise AssertionError.
    assert len(paths)==14
    # Set records to a list of the result of audit(p.parent) for p in paths.
    records=[audit(p.parent) for p in paths]
    # Set full to the next item from a lazy sequence of r for r in records; retain entries satisfying
    # r['scenario'] equals 'congested_four_approach' and...
    full=next(r for r in records if r['scenario']=='congested_four_approach' and r['metrics']['total_vehicles_completed']==16)
    # Require full['metrics'] at 'total_vehicles_spawned' equals 16; otherwise raise AssertionError.
    assert full['metrics']['total_vehicles_spawned']==16
    # Require the number of entries in a set of r['source_hashes'] at 'runtime_simulation/runner.py' for r in
    # records equals 1; otherwise raise AssertionError.
    assert len({r['source_hashes']['runtime_simulation/runner.py'] for r in records})==1
    # Require the number of entries in a set of r['source_hashes'] at 'negotiation_execution/ego_controller.py'
    # for r in records equals 1; otherwise raise AssertionError.
    assert len({r['source_hashes']['negotiation_execution/ego_controller.py'] for r in records})==1
    # Set old70 to the result of read(RUNS joined with the path segment 'after_v1/congested_four_approach/receipt.json').
    old70=read(RUNS/'after_v1/congested_four_approach/receipt.json')
    # Set old360 to the result of read(BASE joined with the path segment
    # 'results/live_deadlock_investigation/20261016/reconciled_releas...').
    old360=read(BASE/'results/live_deadlock_investigation/20261016/reconciled_release_fix_v1/congested_four_approach/receipt.json')
    # Set comparisons to an empty list.
    comparisons=[]
    # Iterate over a list containing a tuple containing 70, old70, a tuple containing 360, old360, binding each
    # item to (horizon, before).
    for horizon,before in [(70,old70),(360,old360)]:
        # Set after to the next item from a lazy sequence of r for r in records; retain entries satisfying
        # r['scenario'] equals 'congested_four_approach' and f'_{horizon}/' belongs to...
        after=next(r for r in records if r['scenario']=='congested_four_approach'
                   # Evaluate formatted text built from the embedded values belongs to r at 'evidence_directory'
                   # as part of the enclosing expression.
                   and f'_{horizon}/' in r['evidence_directory'])
        # Set prior_runtime to the result of read(RUNS joined with the path segment 'after_v1/congested_four_approach' when horizon
        # equals 70, otherwise BASE...).
        prior_runtime=read((RUNS/'after_v1/congested_four_approach' if horizon==70 else
            # Evaluate BASE joined with the path segment
            # 'results/live_deadlock_investigation/20261016/reconciled_releas...' as part of the enclosing
            # expression.
            BASE/'results/live_deadlock_investigation/20261016/reconciled_release_fix_v1/congested_four_approach')/'runtime_result.json')
        # Set current_runtime to the result of read(BASE divided by after at 'evidence_directory' divided by the
        # text 'runtime_result.json').
        current_runtime=read(BASE/after['evidence_directory']/'runtime_result.json')
        # Iterate over a tuple containing the text 'presentation_schedule', the text
        # 'scheduled_departure_seconds', the text..., binding each item to key.
        for key in ('presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds'):
            # Require prior_runtime at key equals current_runtime at key; otherwise raise AssertionError with key.
            assert prior_runtime[key]==current_runtime[key],key
        # Append a dictionary built from the supplied values to comparisons.
        comparisons.append(dict(horizon=horizon,before=before['metrics'],after=after['metrics']))
    # Set historical to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Set changed_history to a list of p for (p, h) in key/value pairs from historical; retain entries satisfying
    # the result of sha(BASE divided by p) differs from h at 'sha256'.
    changed_history=[p for p,h in historical.items() if sha(BASE/p)!=h['sha256']]
    # Require the negation of changed_history; otherwise raise AssertionError with changed_history.
    assert not changed_history, changed_history
    # Set protected to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/protected_source_inventory.json').
    protected=read(BASE/'results/final_readiness/20261016/protected_source_inventory.json')
    # Set changed_sources to a list of p for (p, h) in key/value pairs from protected; retain entries satisfying
    # the result of sha(BASE divided by p) differs from h.
    changed_sources=[p for p,h in protected.items() if sha(BASE/p)!=h]
    # Require a set built from a lazy sequence of the result of p.replace('\\', '/') for p in changed_sources
    # equals a set containing the text 'runtime_simulation/browser_state.py', the text
    # 'runtime_simulation/runner.py', the text...; otherwise raise AssertionError.
    assert set(p.replace('\\','/') for p in changed_sources)=={
        'runtime_simulation/browser_state.py','runtime_simulation/runner.py',
        'negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    # Set identity to the result of read(OUT joined with the path segment 'approved_source_identity.json').
    identity=read(OUT/'approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of sha(BASE / p) equals h and sha(OUT / 'source_after'
    # / p) equals h for (p, h) in key/value pairs from identity; otherwise raise AssertionError.
    assert all(sha(BASE/p)==h and sha(OUT/'source_after'/p)==h for p,h in identity.items())
    # Set ui_identity to the result of read(OUT joined with the path segment
    # 'showcase_source_identity_local_browser_v1.json').
    ui_identity=read(OUT/'showcase_source_identity_local_browser_v1.json')
    # Require whether every item is true in a lazy sequence of sha(BASE.parent / 'socialmind_drive_showcase' / p)
    # equals h and sha(OUT / 'source_after_local_browser_v1/socialmind_drive_showcase' / p) equals h for (p, h) in
    # key/value pairs from ui_identity; otherwise raise AssertionError.
    assert all(sha(BASE.parent/'socialmind_drive_showcase'/p)==h and
        # Evaluate the result of sha(OUT joined with the path segment 'source_after_local_browser_v1/socialmind_drive_showcase'
        # divided by p) equals h as part of the enclosing expression.
        sha(OUT/'source_after_local_browser_v1/socialmind_drive_showcase'/p)==h
        # Evaluate key/value pairs from ui_identity as part of the enclosing expression.
        for p,h in ui_identity.items())
    # Set server to the result of read(OUT joined with the path segment 'server_shutdown_synchronized_v1/receipt.json').
    server=read(OUT/'server_shutdown_synchronized_v1/receipt.json')
    # Set clients to the result of read(OUT joined with the path segment 'client_lifecycle_v10/receipt.json').
    clients=read(OUT/'client_lifecycle_v10/receipt.json')
    # Require clients at 'shutdown_process_closed' and the negation of clients at 'lifecycle_errors'; otherwise
    # raise AssertionError.
    assert clients['shutdown_process_closed'] and not clients['lifecycle_errors']
    # Require clients at 'no_accumulated_live_targets' and clients at 'new_client_preferences_reset'; otherwise
    # raise AssertionError.
    assert clients['no_accumulated_live_targets'] and clients['new_client_preferences_reset']
    # Require server at 'matched_independent_simulator_frames' equals server at 'matched_http_svg_frames';
    # otherwise raise AssertionError.
    assert server['matched_independent_simulator_frames']==server['matched_http_svg_frames']
    # Require the negation of server at 'remaining_owned_pids' and the negation of server at
    # 'unhandled_traceback'; otherwise raise AssertionError.
    assert not server['remaining_owned_pids'] and not server['unhandled_traceback']
    # Set browser to the result of read(OUT joined with the path segment 'local_browser_v4/receipt.json').
    browser=read(OUT/'local_browser_v4/receipt.json')
    # Require the text 'failure' does not belong to browser and the negation of browser at 'page_errors' and the
    # negation of browser at 'failed_requests'; otherwise raise AssertionError.
    assert 'failure' not in browser and not browser['page_errors'] and not browser['failed_requests']
    # Require the negation of browser at 'remaining_owned_processes'; otherwise raise AssertionError.
    assert not browser['remaining_owned_processes']
    # Require browser at 'navigate_reload_close_reopen' and browser at 'stop_relaunch'; otherwise raise
    # AssertionError.
    assert browser['navigate_reload_close_reopen'] and browser['stop_relaunch']
    # Require browser at 'independent_browser_preferences' and browser at 'shutdown_while_runtime_active';
    # otherwise raise AssertionError.
    assert browser['independent_browser_preferences'] and browser['shutdown_while_runtime_active']
    # Require browser at 'matching_http_dom_frames' is at least 3 and browser at 'moving_red_samples' is greater
    # than 0; otherwise raise AssertionError.
    assert browser['matching_http_dom_frames']>=3 and browser['moving_red_samples']>0
    # Require whether any item is true in a lazy sequence of t['permission'] at 'authorized' and t['negotiation']
    # at 'current_receipt' for t in browser at 'held_to_ready_transitions'; otherwise raise AssertionError.
    assert any(t['permission']['authorized'] and t['negotiation']['current_receipt']
               # Evaluate browser at 'held_to_ready_transitions' as part of the enclosing expression.
               for t in browser['held_to_ready_transitions'])
    # Set actors to RUNS joined with the path segment 'http_synchronized_v1/regulatory_cycle/actor_inputs_and_actions...'.
    actors=RUNS/'http_synchronized_v1/regulatory_cycle/actor_inputs_and_actions.jsonl'
    # Set inputs to a list of the decoded data produced by json.loads from line for line in the result of
    # actors.open().
    inputs=[json.loads(line) for line in actors.open(encoding='utf-8')]
    # Require the number of entries in inputs equals 6; otherwise raise AssertionError.
    assert len(inputs)==6
    # Iterate over inputs, binding each item to row.
    for row in inputs:
        # Set factor to row at 'actual_factor'.
        # Set snapshot to factor at 'actor_observation_snapshot'.
        factor=row['actual_factor'];snapshot=factor['actor_observation_snapshot']
        # Require factor['hard_action_mask'] at factor['selected_action_index']; otherwise raise AssertionError.
        assert factor['hard_action_mask'][factor['selected_action_index']]
        # Require snapshot at 'source_timestamp' equals 23.24; otherwise raise AssertionError.
        assert snapshot['source_timestamp']==23.24
        # Require the negation of factor at 'ppo_update_eligible'; otherwise raise AssertionError.
        assert not factor['ppo_update_eligible']
    # Set negative to the result of audit(RUNS joined with the path segment
    # 'negative_mandatory_cycle_v1/regulatory_cycle__mandatory_constr...').
    negative=audit(RUNS/'negative_mandatory_cycle_v1/regulatory_cycle__mandatory_constraint_cycle')
    # Require whether any item is true in a lazy sequence of the text 'RETAINED_MANDATORY_OR_COMMITMENT_CYCLE'
    # belongs to line for line in the result of (BASE / negative['evidence_directory'] / 'timeline.jsonl').open();
    # otherwise raise AssertionError.
    assert any('RETAINED_MANDATORY_OR_COMMITMENT_CYCLE' in line for line in
        # Supply encoding as the text 'utf-8'.
        (BASE/negative['evidence_directory']/'timeline.jsonl').open(encoding='utf-8'))
    # Set report to a dictionary built from the supplied values.
    report=dict(classification='QUALITATIVE_DIAGNOSTIC_NOT_FROZEN_FINAL_EVALUATION',
        # Supply records as records.
        # Supply comparisons as comparisons.
        # Supply synthetic_mandatory_cycle as negative.
        records=records,comparisons=comparisons,synthetic_mandatory_cycle=negative,
        # Supply unchanged_historical_files as the number of entries in historical.
        # Supply unchanged_protected_sources as the number of entries in protected minus the number of entries in
        # changed_sources.
        unchanged_historical_files=len(historical),unchanged_protected_sources=len(protected)-len(changed_sources),
        # Supply intentional_changes_since_original_inventory as changed_sources.
        # Supply checkpoint_sha256 as POLICY_HASH.
        intentional_changes_since_original_inventory=changed_sources,checkpoint_sha256=POLICY_HASH,
        # Supply synchronized_server as server.
        # Supply client_lifecycle as clients.
        # Supply local_chromium as browser.
        synchronized_server=server,client_lifecycle=clients,local_chromium=browser,
        # Supply actual_actor_input_factors as the number of entries in inputs.
        # Supply verified_showcase_source_identity as ui_identity.
        actual_actor_input_factors=len(inputs),verified_showcase_source_identity=ui_identity)
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    # Set lines to a list containing the text '# Final live correction: measured diagnostic results', the text '',
    # the text 'These are new...
    lines=['# Final live correction: measured diagnostic results','',
        'These are new deterministic presentation diagnostics, not a replacement for the frozen final evaluation.','',
        '| Scenario / fault | Spawned | Completed | MAPPO | Fallback epochs | Mean wait s | Max wait s | Approach gap s | Throughput / min | All-active stopped max s |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    # Iterate over records plus a list containing negative, binding each item to r.
    for r in records+[negative]:
        # Set m to r at 'metrics'.
        # Set label to r at 'scenario' plus the text '/' plus r at 'fault' when r at 'fault', otherwise the text
        # ''.
        m=r['metrics'];label=r['scenario']+(' / '+r['fault'] if r['fault'] else '')
        # Run this branch when r at 'scenario' equals the text 'congested_four_approach'.
        # Update label to its current value plus the text '/' plus the text '70 s' when the text '_70/' belongs to
        # r at 'evidence_directory', otherwise the text '360 s budget'.
        if r['scenario']=='congested_four_approach':label+=' / '+('70 s' if '_70/' in r['evidence_directory'] else '360 s budget')
        # Set gap to m at 'approach_waiting_time_gap_seconds'.
        gap=m['approach_waiting_time_gap_seconds']
        # Set gap_label to formatted text built from the embedded values when gap is a different object from None,
        # otherwise the text 'N/A'.
        gap_label=f'{gap:.3f}' if gap is not None else 'N/A'
        # Append formatted text built from the embedded values to lines.
        lines.append(f"| {label} | {m['total_vehicles_spawned']} | {m['total_vehicles_completed']} | {m['mappo_inference_call_count']} | {m.get('fallback_activations',0)} | {m['mean_waiting_time_seconds']:.3f} | {m['maximum_waiting_time_seconds']:.3f} | {gap_label} | {m['throughput_vehicles_per_minute']:.3f} | {r['observed_all_active_stationary_max_seconds']:.2f} |")
    # Update lines to its current value plus a list containing the text '', the text 'All rows: zero observed
    # collisions, blocked-zone violations...', the text 'The...
    lines += ['', 'All rows: zero observed collisions, blocked-zone violations and unauthorized entries.',
        'The mandatory-cycle row is injected contradictory constraint evidence, not a newly invented legal movement scenario.',
        'Stationary duration is sampled at the existing 0.16-second publisher interval. The unchanged `deadlock_observed` metric flags any individual incoming vehicle stopped for 15 seconds; it can be true in a completed, progressing episode.', '',
        '| Dense budget | Completion before → after | Mean wait before → after s | Max wait before → after s | Approach gap before → after s | Throughput before → after / min |',
        '|---|---|---|---|---|---|']
    # Iterate over comparisons, binding each item to c.
    for c in comparisons:
        # Set (b, a) to a tuple containing c at 'before', c at 'after'.
        b,a=c['before'],c['after']
        # Append formatted text built from the embedded values to lines.
        lines.append(f"| {c['horizon']} s | {b['total_vehicles_completed']}/16 → {a['total_vehicles_completed']}/16 | {b['mean_waiting_time_seconds']:.3f} → {a['mean_waiting_time_seconds']:.3f} | {b['maximum_waiting_time_seconds']:.3f} → {a['maximum_waiting_time_seconds']:.3f} | {b['approach_waiting_time_gap_seconds']:.3f} → {a['approach_waiting_time_gap_seconds']:.3f} | {b['throughput_vehicles_per_minute']:.3f} → {a['throughput_vehicles_per_minute']:.3f} |")
    # Update lines to its current value plus a list containing the text '', formatted text built from the embedded
    # values, formatted text built from the embedded values,...
    lines+=['',f"Integrity: {len(historical)} historical files unchanged; {len(protected)-len(changed_sources)} protected source/model files unchanged. The four listed source differences include the earlier approved revisions.",
        # Include formatted text built from the embedded values in this list.
        f"Synchronized actual-simulator/publisher/HTTP/SVG frames: {server['matched_http_svg_frames']}. Local Chromium additionally verified {browser['sampled_dom_frames']} actual DOM frames, including {browser['matching_http_dom_frames']} matching HTTP/DOM frames.",
        # Include the text 'Dense full run per-approach mean waits:' plus the serialized data produced by
        # json.dumps in this list.
        'Dense full run per-approach mean waits: '+json.dumps(full['metrics']['per_approach_mean_waiting_time_seconds']),
        'Detailed metrics, sampled transitions, per-event MAPPO evidence and timestamps: `results/final_live_correction/20261016/verification.json`.']
    # Write the supplied text to (BASE / 'docs/FINAL_LIVE_CORRECTION_RESULTS.md').
    (BASE/'docs/FINAL_LIVE_CORRECTION_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps(dict(real_cases=len(records),dense_completed=full['metrics']['total_vehicles_completed'],historical_unchanged=len(historical),http_frames=server['matched_http_svg_frames'])))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
