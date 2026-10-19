"""Separate qualitative demonstration audit; never writes frozen evaluations."""
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
OUT=BASE/'results/final_demonstrations/v1'


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def queue_measurement(directory):
    acceleration={}
    for line in (directory/'timeline.jsonl').open():
        row=json.loads(line)
        for ego,s in row.get('states',{}).items():acceleration[ego]=s['max_acceleration_mps2']
    intervals={a:0. for a in 'NESW'};maxima={a:0. for a in 'NESW'}
    starts={};episodes=[];first=None;native_samples=0;following_samples=0
    moving_followers={a:0 for a in 'NESW'};minimum_gap={a:None for a in 'NESW'}
    for line in (directory/'queue_timeseries.jsonl').open():
        frame=json.loads(line);now=frame['time'];present=set()
        for v in frame['vehicles']:
            ego=v['id'];present.add(ego)
            increment=acceleration[ego]*.04/2
            available=bool(not v['queue_head'] and v['distance_to_stop_m'] is not None
                and v['leader_speed'] is not None and v['leader_speed']>.5
                and v['native_follow_speed_mps']>v['speed']+increment
                and v['native_stop_speed_mps']>v['speed']+increment
                and v['bumper_gap_m']>=v['min_gap_m'] and not v['native_stop_state']&1)
            delayed=available and v['speed']<.1
            if v['distance_to_stop_m'] is not None and not v['queue_head'] and v['previous_step_decision']:
                following_samples+=1
                native_samples+=v['movement_authority']=='SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP'
                moving_followers[v['approach']]+=v['speed']>.5
                if v['bumper_gap_m'] is not None:
                    previous=minimum_gap[v['approach']]
                    minimum_gap[v['approach']]=min(previous,v['bumper_gap_m']) if previous is not None else v['bumper_gap_m']
            if delayed:
                if first is None:first=dict(time=now,vehicle=v)
                starts.setdefault(ego,(now,v['approach'],v['leader_id']))
                intervals[v['approach']]+=.12
                maxima[v['approach']]=max(maxima[v['approach']],now-starts[ego][0]+.12)
            elif ego in starts:
                start,approach,leader=starts.pop(ego)
                episodes.append(dict(follower=ego,leader=leader,approach=approach,start=start,end=now,
                    delay_seconds=round(now-start,4),response_observed=v['speed']>=.1,
                    ended_by_promotion_or_opportunity_loss=v['speed']<.1))
        for ego in set(starts)-present:
            start,approach,leader=starts.pop(ego)
            episodes.append(dict(follower=ego,leader=leader,approach=approach,start=start,end=now,
                delay_seconds=round(now-start,4),response_observed=False,ended_by_departure=True))
    return dict(total_available_gap_standing_vehicle_seconds=round(sum(intervals.values()),4),
        per_approach_available_gap_standing_seconds={a:round(v,4) for a,v in intervals.items()},
        per_approach_longest_available_gap_standing_seconds={a:round(v,4) for a,v in maxima.items()},
        maximum_available_gap_standing_seconds=round(max(maxima.values()),4),
        native_follower_samples=native_samples,follower_samples=following_samples,
        moving_follower_samples_by_approach=moving_followers,minimum_incoming_follower_bumper_gap_m=minimum_gap,
        first_incorrect_condition=first,episodes=episodes,
        sampling_seconds=.12,definition='Stopped <0.1 m/s, moving leader >0.5 m/s; native follow and entry-stop speeds permit at least half an actual acceleration step; gap >= measured minGap; not already at native stop. Diagnostic only, never grants authority.')


def main():
    from runtime_simulation.scenarios import get_scenario
    from conflict import MapPathManager,ConflictZoneManager
    menu=read(BASE/'runtime_simulation/final_demonstrations.json')
    rows=[];receipts={};geometry=[];paths=MapPathManager();zones=ConflictZoneManager(paths)
    for item in menu:
        sid=item['scenario_id'];directory=OUT/'after_v1'/(sid+'__proposed')
        receipt=read(directory/'receipt.json');run=read(directory/'runtime_result.json');m=receipt['metrics']
        receipts[sid]=receipt
        assert m['collisions']==m['blocked_zone_violations']==receipt['unauthorized_entries']==0
        assert m['maximum_negotiation_participants']<=4 and m['centralized_critic_runtime_calls']==0
        assert run['policy_hash_unchanged'] and not run['centralized_execution_graph_used_for_control']
        assert run['training_operations']==run['parameter_updates']==run['optimizer_steps']==0
        assert receipt['status']=='COMPLETED',(sid,receipt['status'],run.get('runtime_error'))
        authorized=[e for e in run['events'] if e.get('mappo_invocation')=='AUTHORIZED']
        if sid=='rule_resolved_two':assert m['mappo_decision_epochs']==0
        if sid=='final_four_agent_stress':
            assert any(len(e['participants'])==4 for e in authorized)
            assert receipt['genuine_actor_factors'] and all(f['mask'][f['index']] for f in receipt['genuine_actor_factors'])
        row=dict(scenario=sid,label=item['final_label'],mode='PROPOSED_MAPPO_RULES_SAFETY',
            status=receipt['status'],scheduled=m['total_vehicles_scheduled'],spawned=m['total_vehicles_spawned'],
            completed=m['total_vehicles_completed'],mappo_calls=m['mappo_decision_epochs'],
            collisions=m['collisions'],blocked_zone_violations=m['blocked_zone_violations'],unauthorized_entries=receipt['unauthorized_entries'],
            mean_wait_seconds=m['mean_waiting_time_seconds'],max_wait_seconds=m['maximum_waiting_time_seconds'],
            approach_wait_gap_seconds=m['approach_waiting_time_gap_seconds'],throughput=m['throughput_vehicles_per_minute'],
            completion_time_seconds=run['actual_simulation_time_seconds'],wall_seconds=receipt['wall_seconds'],
            deadlock_observed=m['deadlock_observed'],safe_hold_activations=m.get('safe_hold_activations'),
            mappo_outcomes_accepted=run['metrics'].get('mappo_outcomes_accepted',0),
            safety_fallback_epochs=run['metrics'].get('fallback_activations',0),
            rule_resolved_outcomes=run['metrics'].get('rule_resolved_events',0),
            participant_events=[dict(time=e['timestamp'],ids=e['participants'],outcome=e.get('execution_outcome')) for e in authorized])
        rows.append(row)
        movements=[d.movement_path_id for demands in get_scenario(sid).schedule().values() for d in demands]
        pairs=[]
        for a,b in combinations(movements,2):
            if a[0]==b[0]:continue
            z=zones.zone_record(a,1.8,b,1.8)
            if z:pairs.append(dict(first=a,second=b,zone=z['zone_id']))
        assert pairs,sid
        geometry.append(dict(scenario=sid,movements=movements,physical_conflict_pairs=pairs))
    baseline_dir=OUT/'after_v1/final_coordination_failure__rules-only'
    baseline=read(baseline_dir/'receipt.json');brun=read(baseline_dir/'runtime_result.json');bm=baseline['metrics']
    assert baseline['status'] in {'COMPLETED','INCOMPLETE'},brun.get('runtime_error')
    assert bm['mappo_decision_epochs']==0 and not baseline['genuine_actor_factors']
    assert bm['collisions']==bm['blocked_zone_violations']==baseline['unauthorized_entries']==0
    protected=read(OUT/'after_v1/final_coordination_failure__proposed/runtime_result.json')
    for key in ['presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds']:
        assert protected[key]==brun[key],key
    comparison=dict(rows[-1],mode='EXISTING_RULES_ONLY_PROVIDER_ADDITIONAL_QUALITATIVE_COMPARISON',status=baseline['status'],
        completed=bm['total_vehicles_completed'],spawned=bm['total_vehicles_spawned'],mappo_calls=0,
        mean_wait_seconds=bm['mean_waiting_time_seconds'],max_wait_seconds=bm['maximum_waiting_time_seconds'],
        throughput=bm['throughput_vehicles_per_minute'],completion_time_seconds=None if baseline['status']!='COMPLETED' else brun['actual_simulation_time_seconds'],
        observed_duration_seconds=brun['actual_simulation_time_seconds'],safe_degradation_observed=baseline['status']=='INCOMPLETE',
        safe_hold_activations=brun['metrics']['safe_hold_activations'],participant_events=[],
        rule_resolved_outcomes=brun['metrics'].get('rule_resolved_events',0),
        safety_fallback_epochs=0,mappo_outcomes_accepted=0,deadlock_observed=bm['deadlock_observed'],
        approach_wait_gap_seconds=bm['approach_waiting_time_gap_seconds'],wall_seconds=baseline['wall_seconds'])
    (OUT/'comparison.json').write_text(json.dumps(dict(classification='QUALITATIVE_ADDITIONAL_NO_NEGOTIATION_COMPARISON',
        same_demand=True,safety_enabled_both=True,unsafe_uncoordinated_mode_deployed=False,modes=[rows[-1],comparison]),indent=2))
    before=queue_measurement(OUT/'before_v1/congested_four_approach__proposed')
    after=queue_measurement(OUT/'after_v1/congested_four_approach__proposed')
    old=read(OUT/'before_v1/congested_four_approach__proposed/runtime_result.json')
    new=read(OUT/'after_v1/congested_four_approach__proposed/runtime_result.json')
    for k in ['presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds']:
        assert old[k]==new[k],k
    assert after['total_available_gap_standing_vehicle_seconds']<before['total_available_gap_standing_vehicle_seconds']
    historic=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/p)==v['sha256'] for p,v in historic.items())
    identity=read(OUT/'approved_source_identity.json')
    assert all(sha(BASE/p)==s for p,s in identity.items())
    assert sha(BASE/'runtime_simulation/scenario_catalog.json')==read(OUT/'before_v1/congested_four_approach__proposed/source_hashes.json')['runtime_simulation/scenario_catalog.json']
    evidence=dict(classification='QUALITATIVE_PRESENTATION_ONLY_NOT_FROZEN_EVALUATION',
        rows=rows,comparison=comparison,queue_before=before,queue_after=after,
        geometry=geometry,historical_files_unchanged=len(historic),source_identity=identity,
        policy_sha256=new['policy_sha256_after'])
    full_browser=read(OUT/'browser_v4/receipt.json')
    final_browser=read(OUT/'browser_v5/receipt.json')
    assert len(full_browser['cases'])==5 and not full_browser['page_errors']
    assert full_browser['cases'][1]['outline_seen']
    assert not full_browser['remaining_owned_processes']
    assert 'TimeoutExpired' in full_browser.get('failure','')
    assert not final_browser.get('failure') and not final_browser['page_errors'] and not final_browser['remaining_owned_processes']
    evidence['browser']=dict(five_scenario_functional_checks='PASS',
        full_session_shutdown='PARTIAL_WINDOWS_TIMEOUT_FORCED_CLEANUP',
        full_session_frames=full_browser['dom_samples'],full_session_receipt='browser_v4/receipt.json',
        final_comparison_panel_and_single_scenario_shutdown='PASS',
        final_comparison_frames=final_browser['dom_samples'],final_comparison_receipt='browser_v5/receipt.json',
        page_errors=[],remaining_owned_processes=[])
    (OUT/'verification.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(dict(scenarios=rows,comparison=comparison,
        queue_before={k:v for k,v in before.items() if k not in {'episodes','first_incorrect_condition'}},
        queue_after={k:v for k,v in after.items() if k not in {'episodes','first_incorrect_condition'}})))


if __name__=='__main__':main()
