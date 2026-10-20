"""Separate qualitative demonstration audit; never writes frozen evaluations."""
# Import hashlib for use in this module.
import hashlib
# Import combinations from itertools for the operations below.
from itertools import combinations
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import sys for use in this module.
import sys

# Set BASE to Path(__file__).resolve().parents at 1.
# Call sys.path.insert with the supplied arguments.
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
# Set OUT to BASE joined with the path segment 'results/final_demonstrations/v1'.
OUT=BASE/'results/final_demonstrations/v1'


# Read using the inputs and processing steps below.
# Input p: the supplied p.
# Output: the decoded data produced by json.loads from the text read from p.
# Return the decoded data produced by json.loads from the text read from p to the caller.
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
# Sha using the inputs and processing steps below.
# Input p: the supplied p.
# Output: the hexadecimal digest from hashlib.sha256(p.read_bytes()).
# Return the hexadecimal digest from hashlib.sha256(p.read_bytes()) to the caller.
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


# Queue measurement using the inputs and processing steps below.
# Input directory: the supplied directory.
# Output: a dictionary built from the supplied values.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def queue_measurement(directory):
    # Set acceleration to an empty dictionary.
    acceleration={}
    # Iterate over the result of (directory / 'timeline.jsonl').open(), binding each item to line.
    for line in (directory/'timeline.jsonl').open():
        # Set row to the decoded data produced by json.loads from line.
        row=json.loads(line)
        # Iterate over key/value pairs from row.get('states', {}), binding each item to (ego, s).
        # Set acceleration[ego] to s at 'max_acceleration_mps2'.
        for ego,s in row.get('states',{}).items():acceleration[ego]=s['max_acceleration_mps2']
    # Set intervals to a dictionary of a mapped to 0.0 for a in the text 'NESW'.
    # Set maxima to a dictionary of a mapped to 0.0 for a in the text 'NESW'.
    intervals={a:0. for a in 'NESW'};maxima={a:0. for a in 'NESW'}
    # Set starts to an empty dictionary.
    # Set episodes to an empty list.
    # Set first to None.
    # Set native_samples to 0.
    # Set following_samples to 0.
    starts={};episodes=[];first=None;native_samples=0;following_samples=0
    # Set moving_followers to a dictionary of a mapped to 0 for a in the text 'NESW'.
    # Set minimum_gap to a dictionary of a mapped to None for a in the text 'NESW'.
    moving_followers={a:0 for a in 'NESW'};minimum_gap={a:None for a in 'NESW'}
    # Iterate over the result of (directory / 'queue_timeseries.jsonl').open(), binding each item to line.
    for line in (directory/'queue_timeseries.jsonl').open():
        # Set frame to the decoded data produced by json.loads from line.
        # Set now to frame at 'time'.
        # Set present to an empty set.
        frame=json.loads(line);now=frame['time'];present=set()
        # Iterate over frame at 'vehicles', binding each item to v.
        for v in frame['vehicles']:
            # Set ego to v at 'id'.
            # Add ego to present.
            ego=v['id'];present.add(ego)
            # Set increment to acceleration at ego multiplied by 0.04 divided by 2.
            increment=acceleration[ego]*.04/2
            # Set available to a Boolean built from the negation of v at 'queue_head' and v at
            # 'distance_to_stop_m' is a different object from None and v at 'leader_speed' is a different object
            # from None and v at 'leader_speed' is greater than 0.5 and v at 'native_follow_speed_mps' is greater
            # than v['speed'] plus increment and v at 'native_stop_speed_mps' is greater than v['speed'] plus
            # increment and v at 'bumper_gap_m' is at least v at 'min_gap_m' and the negation of
            # v['native_stop_state'] intersected with 1.
            available=bool(not v['queue_head'] and v['distance_to_stop_m'] is not None
                # Evaluate v at 'leader_speed' is a different object from None as part of the enclosing
                # expression.
                and v['leader_speed'] is not None and v['leader_speed']>.5
                # Evaluate v at 'native_follow_speed_mps' is greater than v at 'speed' plus increment as part of
                # the enclosing expression.
                and v['native_follow_speed_mps']>v['speed']+increment
                # Evaluate v at 'native_stop_speed_mps' is greater than v at 'speed' plus increment as part of the
                # enclosing expression.
                and v['native_stop_speed_mps']>v['speed']+increment
                # Evaluate v at 'bumper_gap_m' is at least v at 'min_gap_m' as part of the enclosing expression.
                and v['bumper_gap_m']>=v['min_gap_m'] and not v['native_stop_state']&1)
            # Set delayed to available and v at 'speed' is less than 0.1.
            delayed=available and v['speed']<.1
            # Run this branch when v at 'distance_to_stop_m' is a different object from None and the negation of v
            # at 'queue_head' and v at 'previous_step_decision'.
            if v['distance_to_stop_m'] is not None and not v['queue_head'] and v['previous_step_decision']:
                # Update following_samples to its current value plus 1.
                following_samples+=1
                # Update native_samples to its current value plus v at 'movement_authority' equals the text
                # 'SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP'.
                native_samples+=v['movement_authority']=='SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP'
                # Update moving_followers[v['approach']] to its current value plus v at 'speed' is greater than
                # 0.5.
                moving_followers[v['approach']]+=v['speed']>.5
                # Run this branch when v at 'bumper_gap_m' is a different object from None.
                if v['bumper_gap_m'] is not None:
                    # Set previous to minimum_gap at v['approach'].
                    previous=minimum_gap[v['approach']]
                    # Set minimum_gap[v['approach']] to the minimum of previous, v at 'bumper_gap_m' when previous
                    # is a different object from None, otherwise v at 'bumper_gap_m'.
                    minimum_gap[v['approach']]=min(previous,v['bumper_gap_m']) if previous is not None else v['bumper_gap_m']
            # Run this branch when delayed.
            if delayed:
                # Run this branch when first is the same object as None.
                # Set first to a dictionary built from the supplied values.
                if first is None:first=dict(time=now,vehicle=v)
                # Call starts.setdefault with the supplied arguments.
                starts.setdefault(ego,(now,v['approach'],v['leader_id']))
                # Update intervals[v['approach']] to its current value plus 0.12.
                intervals[v['approach']]+=.12
                # Set maxima[v['approach']] to the maximum of maxima at v['approach'], now minus starts[ego] at 0
                # plus 0.12.
                maxima[v['approach']]=max(maxima[v['approach']],now-starts[ego][0]+.12)
            # Run this branch when ego belongs to starts.
            elif ego in starts:
                # Set (start, approach, leader) to the result of starts.pop(ego).
                start,approach,leader=starts.pop(ego)
                # Append a dictionary built from the supplied values to episodes.
                episodes.append(dict(follower=ego,leader=leader,approach=approach,start=start,end=now,
                    # Supply delay_seconds as the rounded value of now minus start.
                    # Supply response_observed as v at 'speed' is at least 0.1.
                    delay_seconds=round(now-start,4),response_observed=v['speed']>=.1,
                    # Supply ended_by_promotion_or_opportunity_loss as v at 'speed' is less than 0.1.
                    ended_by_promotion_or_opportunity_loss=v['speed']<.1))
        # Iterate over a set built from starts minus present, binding each item to ego.
        for ego in set(starts)-present:
            # Set (start, approach, leader) to the result of starts.pop(ego).
            start,approach,leader=starts.pop(ego)
            # Append a dictionary built from the supplied values to episodes.
            episodes.append(dict(follower=ego,leader=leader,approach=approach,start=start,end=now,
                # Supply delay_seconds as the rounded value of now minus start.
                # Supply response_observed as False.
                # Supply ended_by_departure as True.
                delay_seconds=round(now-start,4),response_observed=False,ended_by_departure=True))
    # Return a dictionary built from the supplied values to the caller.
    return dict(total_available_gap_standing_vehicle_seconds=round(sum(intervals.values()),4),
        # Supply per_approach_available_gap_standing_seconds as a dictionary of a mapped to the rounded value of v
        # for (a, v) in key/value pairs from intervals.
        per_approach_available_gap_standing_seconds={a:round(v,4) for a,v in intervals.items()},
        # Supply per_approach_longest_available_gap_standing_seconds as a dictionary of a mapped to the rounded
        # value of v for (a, v) in key/value pairs from maxima.
        per_approach_longest_available_gap_standing_seconds={a:round(v,4) for a,v in maxima.items()},
        # Supply maximum_available_gap_standing_seconds as the rounded value of the maximum of values from maxima.
        maximum_available_gap_standing_seconds=round(max(maxima.values()),4),
        # Supply native_follower_samples as native_samples.
        # Supply follower_samples as following_samples.
        native_follower_samples=native_samples,follower_samples=following_samples,
        # Supply moving_follower_samples_by_approach as moving_followers.
        # Supply minimum_incoming_follower_bumper_gap_m as minimum_gap.
        moving_follower_samples_by_approach=moving_followers,minimum_incoming_follower_bumper_gap_m=minimum_gap,
        # Supply first_incorrect_condition as first.
        # Supply episodes as episodes.
        first_incorrect_condition=first,episodes=episodes,
        # Supply sampling_seconds as 0.12.
        # Supply definition as the text 'Stopped <0.1 m/s, moving leader >0.5 m/s; native follow and...'.
        sampling_seconds=.12,definition='Stopped <0.1 m/s, moving leader >0.5 m/s; native follow and entry-stop speeds permit at least half an actual acceleration step; gap >= measured minGap; not already at native stop. Diagnostic only, never grants authority.')


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Import get_scenario from runtime_simulation.scenarios for the operations below.
    from runtime_simulation.scenarios import get_scenario
    # Import MapPathManager, ConflictZoneManager from conflict for the operations below.
    from conflict import MapPathManager,ConflictZoneManager
    # Set menu to the result of read(BASE joined with the path segment 'runtime_simulation/final_demonstrations.json').
    menu=read(BASE/'runtime_simulation/final_demonstrations.json')
    # Set rows to an empty list.
    # Set receipts to an empty dictionary.
    # Set geometry to an empty list.
    # Set paths to the result of MapPathManager().
    # Set zones to the result of ConflictZoneManager(paths).
    rows=[];receipts={};geometry=[];paths=MapPathManager();zones=ConflictZoneManager(paths)
    # Iterate over menu, binding each item to item.
    for item in menu:
        # Set sid to item at 'scenario_id'.
        # Set directory to OUT joined with the path segment 'after_v1' divided by sid plus the text '__proposed'.
        sid=item['scenario_id'];directory=OUT/'after_v1'/(sid+'__proposed')
        # Set receipt to the result of read(directory joined with the path segment 'receipt.json').
        # Set run to the result of read(directory joined with the path segment 'runtime_result.json').
        # Set m to receipt at 'metrics'.
        receipt=read(directory/'receipt.json');run=read(directory/'runtime_result.json');m=receipt['metrics']
        # Set receipts[sid] to receipt.
        receipts[sid]=receipt
        # Require m at 'collisions' equals m at 'blocked_zone_violations'; equals receipt at
        # 'unauthorized_entries'; equals 0; otherwise raise AssertionError.
        assert m['collisions']==m['blocked_zone_violations']==receipt['unauthorized_entries']==0
        # Require m at 'maximum_negotiation_participants' is at most 4 and m at 'centralized_critic_runtime_calls'
        # equals 0; otherwise raise AssertionError.
        assert m['maximum_negotiation_participants']<=4 and m['centralized_critic_runtime_calls']==0
        # Require run at 'policy_hash_unchanged' and the negation of run at
        # 'centralized_execution_graph_used_for_control'; otherwise raise AssertionError.
        assert run['policy_hash_unchanged'] and not run['centralized_execution_graph_used_for_control']
        # Require run at 'training_operations' equals run at 'parameter_updates'; equals run at 'optimizer_steps';
        # equals 0; otherwise raise AssertionError.
        assert run['training_operations']==run['parameter_updates']==run['optimizer_steps']==0
        # Require receipt at 'status' equals the text 'COMPLETED'; otherwise raise AssertionError with a tuple
        # containing sid, receipt at 'status', 'runtime_error' from run; use None if absent.
        assert receipt['status']=='COMPLETED',(sid,receipt['status'],run.get('runtime_error'))
        # Set authorized to a list of e for e in run at 'events'; retain entries satisfying 'mappo_invocation'
        # from e; use None if absent equals the text 'AUTHORIZED'.
        authorized=[e for e in run['events'] if e.get('mappo_invocation')=='AUTHORIZED']
        # Run this branch when sid equals the text 'rule_resolved_two'.
        # Require m at 'mappo_decision_epochs' equals 0; otherwise raise AssertionError.
        if sid=='rule_resolved_two':assert m['mappo_decision_epochs']==0
        # Run this branch when sid equals the text 'final_four_agent_stress'.
        if sid=='final_four_agent_stress':
            # Require whether any item is true in a lazy sequence of the number of entries in e['participants']
            # equals 4 for e in authorized; otherwise raise AssertionError.
            assert any(len(e['participants'])==4 for e in authorized)
            # Require receipt at 'genuine_actor_factors' and whether every item is true in a lazy sequence of
            # f['mask'] at f['index'] for f in receipt at 'genuine_actor_factors'; otherwise raise AssertionError.
            assert receipt['genuine_actor_factors'] and all(f['mask'][f['index']] for f in receipt['genuine_actor_factors'])
        # Set row to a dictionary built from the supplied values.
        row=dict(scenario=sid,label=item['final_label'],mode='PROPOSED_MAPPO_RULES_SAFETY',
            # Supply status as receipt at 'status'.
            # Supply scheduled as m at 'total_vehicles_scheduled'.
            # Supply spawned as m at 'total_vehicles_spawned'.
            status=receipt['status'],scheduled=m['total_vehicles_scheduled'],spawned=m['total_vehicles_spawned'],
            # Supply completed as m at 'total_vehicles_completed'.
            # Supply mappo_calls as m at 'mappo_decision_epochs'.
            completed=m['total_vehicles_completed'],mappo_calls=m['mappo_decision_epochs'],
            # Supply collisions as m at 'collisions'.
            # Supply blocked_zone_violations as m at 'blocked_zone_violations'.
            # Supply unauthorized_entries as receipt at 'unauthorized_entries'.
            collisions=m['collisions'],blocked_zone_violations=m['blocked_zone_violations'],unauthorized_entries=receipt['unauthorized_entries'],
            # Supply mean_wait_seconds as m at 'mean_waiting_time_seconds'.
            # Supply max_wait_seconds as m at 'maximum_waiting_time_seconds'.
            mean_wait_seconds=m['mean_waiting_time_seconds'],max_wait_seconds=m['maximum_waiting_time_seconds'],
            # Supply approach_wait_gap_seconds as m at 'approach_waiting_time_gap_seconds'.
            # Supply throughput as m at 'throughput_vehicles_per_minute'.
            approach_wait_gap_seconds=m['approach_waiting_time_gap_seconds'],throughput=m['throughput_vehicles_per_minute'],
            # Supply completion_time_seconds as run at 'actual_simulation_time_seconds'.
            # Supply wall_seconds as receipt at 'wall_seconds'.
            completion_time_seconds=run['actual_simulation_time_seconds'],wall_seconds=receipt['wall_seconds'],
            # Supply deadlock_observed as m at 'deadlock_observed'.
            # Supply safe_hold_activations as 'safe_hold_activations' from m; use None if absent.
            deadlock_observed=m['deadlock_observed'],safe_hold_activations=m.get('safe_hold_activations'),
            # Supply mappo_outcomes_accepted as 'mappo_outcomes_accepted' from run['metrics']; use 0 if absent.
            mappo_outcomes_accepted=run['metrics'].get('mappo_outcomes_accepted',0),
            # Supply safety_fallback_epochs as 'fallback_activations' from run['metrics']; use 0 if absent.
            safety_fallback_epochs=run['metrics'].get('fallback_activations',0),
            # Supply rule_resolved_outcomes as 'rule_resolved_events' from run['metrics']; use 0 if absent.
            rule_resolved_outcomes=run['metrics'].get('rule_resolved_events',0),
            # Supply participant_events as a list of a dictionary built from the supplied values for e in
            # authorized.
            # Supply time as e at 'timestamp'.
            # Supply ids as e at 'participants'.
            # Supply outcome as 'execution_outcome' from e; use None if absent.
            participant_events=[dict(time=e['timestamp'],ids=e['participants'],outcome=e.get('execution_outcome')) for e in authorized])
        # Append row to rows.
        rows.append(row)
        # Set movements to a list of d.movement_path_id for demands in values from get_scenario(sid).schedule().
        movements=[d.movement_path_id for demands in get_scenario(sid).schedule().values() for d in demands]
        # Set pairs to an empty list.
        pairs=[]
        # Iterate over the result of combinations(movements, 2), binding each item to (a, b).
        for a,b in combinations(movements,2):
            # Run this branch when a at 0 equals b at 0.
            # Skip the rest of this loop iteration and process the next item.
            if a[0]==b[0]:continue
            # Set z to the result of zones.zone_record(a, 1.8, b, 1.8).
            z=zones.zone_record(a,1.8,b,1.8)
            # Run this branch when z.
            # Append a dictionary built from the supplied values to pairs.
            if z:pairs.append(dict(first=a,second=b,zone=z['zone_id']))
        # Require pairs; otherwise raise AssertionError with sid.
        assert pairs,sid
        # Append a dictionary built from the supplied values to geometry.
        geometry.append(dict(scenario=sid,movements=movements,physical_conflict_pairs=pairs))
    # Set baseline_dir to OUT joined with the path segment 'after_v1/final_coordination_failure__rules-only'.
    baseline_dir=OUT/'after_v1/final_coordination_failure__rules-only'
    # Set baseline to the result of read(baseline_dir joined with the path segment 'receipt.json').
    # Set brun to the result of read(baseline_dir joined with the path segment 'runtime_result.json').
    # Set bm to baseline at 'metrics'.
    baseline=read(baseline_dir/'receipt.json');brun=read(baseline_dir/'runtime_result.json');bm=baseline['metrics']
    # Require baseline at 'status' belongs to a set containing the text 'COMPLETED', the text 'INCOMPLETE';
    # otherwise raise AssertionError with 'runtime_error' from brun; use None if absent.
    assert baseline['status'] in {'COMPLETED','INCOMPLETE'},brun.get('runtime_error')
    # Require bm at 'mappo_decision_epochs' equals 0 and the negation of baseline at 'genuine_actor_factors';
    # otherwise raise AssertionError.
    assert bm['mappo_decision_epochs']==0 and not baseline['genuine_actor_factors']
    # Require bm at 'collisions' equals bm at 'blocked_zone_violations'; equals baseline at
    # 'unauthorized_entries'; equals 0; otherwise raise AssertionError.
    assert bm['collisions']==bm['blocked_zone_violations']==baseline['unauthorized_entries']==0
    # Set protected to the result of read(OUT joined with the path segment
    # 'after_v1/final_coordination_failure__proposed/runtime_result.json').
    protected=read(OUT/'after_v1/final_coordination_failure__proposed/runtime_result.json')
    # Iterate over a list containing the text 'presentation_schedule', the text 'scheduled_departure_seconds', the
    # text..., binding each item to key.
    for key in ['presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds']:
        # Require protected at key equals brun at key; otherwise raise AssertionError with key.
        assert protected[key]==brun[key],key
    # Set comparison to a dictionary built from rows at -1.
    comparison=dict(rows[-1],mode='EXISTING_RULES_ONLY_PROVIDER_ADDITIONAL_QUALITATIVE_COMPARISON',status=baseline['status'],
        # Supply completed as bm at 'total_vehicles_completed'.
        # Supply spawned as bm at 'total_vehicles_spawned'.
        # Supply mappo_calls as 0.
        completed=bm['total_vehicles_completed'],spawned=bm['total_vehicles_spawned'],mappo_calls=0,
        # Supply mean_wait_seconds as bm at 'mean_waiting_time_seconds'.
        # Supply max_wait_seconds as bm at 'maximum_waiting_time_seconds'.
        mean_wait_seconds=bm['mean_waiting_time_seconds'],max_wait_seconds=bm['maximum_waiting_time_seconds'],
        # Supply throughput as bm at 'throughput_vehicles_per_minute'.
        # Supply completion_time_seconds as None when baseline at 'status' differs from the text 'COMPLETED',
        # otherwise brun at 'actual_simulation_time_seconds'.
        throughput=bm['throughput_vehicles_per_minute'],completion_time_seconds=None if baseline['status']!='COMPLETED' else brun['actual_simulation_time_seconds'],
        # Supply observed_duration_seconds as brun at 'actual_simulation_time_seconds'.
        # Supply safe_degradation_observed as baseline at 'status' equals the text 'INCOMPLETE'.
        observed_duration_seconds=brun['actual_simulation_time_seconds'],safe_degradation_observed=baseline['status']=='INCOMPLETE',
        # Supply safe_hold_activations as brun['metrics'] at 'safe_hold_activations'.
        # Supply participant_events as an empty list.
        safe_hold_activations=brun['metrics']['safe_hold_activations'],participant_events=[],
        # Supply rule_resolved_outcomes as 'rule_resolved_events' from brun['metrics']; use 0 if absent.
        rule_resolved_outcomes=brun['metrics'].get('rule_resolved_events',0),
        # Supply safety_fallback_epochs as 0.
        # Supply mappo_outcomes_accepted as 0.
        # Supply deadlock_observed as bm at 'deadlock_observed'.
        safety_fallback_epochs=0,mappo_outcomes_accepted=0,deadlock_observed=bm['deadlock_observed'],
        # Supply approach_wait_gap_seconds as bm at 'approach_waiting_time_gap_seconds'.
        # Supply wall_seconds as baseline at 'wall_seconds'.
        approach_wait_gap_seconds=bm['approach_waiting_time_gap_seconds'],wall_seconds=baseline['wall_seconds'])
    # Write the supplied text to (OUT / 'comparison.json').
    (OUT/'comparison.json').write_text(json.dumps(dict(classification='QUALITATIVE_ADDITIONAL_NO_NEGOTIATION_COMPARISON',
        # Supply indent as 2.
        # Supply same_demand as True.
        # Supply safety_enabled_both as True.
        # Supply unsafe_uncoordinated_mode_deployed as False.
        # Supply modes as a list containing rows at -1, comparison.
        same_demand=True,safety_enabled_both=True,unsafe_uncoordinated_mode_deployed=False,modes=[rows[-1],comparison]),indent=2))
    # Set before to the result of queue_measurement(OUT joined with the path segment
    # 'before_v1/congested_four_approach__proposed').
    before=queue_measurement(OUT/'before_v1/congested_four_approach__proposed')
    # Set after to the result of queue_measurement(OUT joined with the path segment
    # 'after_v1/congested_four_approach__proposed').
    after=queue_measurement(OUT/'after_v1/congested_four_approach__proposed')
    # Set old to the result of read(OUT joined with the path segment
    # 'before_v1/congested_four_approach__proposed/runtime_result.json').
    old=read(OUT/'before_v1/congested_four_approach__proposed/runtime_result.json')
    # Set new to the result of read(OUT joined with the path segment
    # 'after_v1/congested_four_approach__proposed/runtime_result.json').
    new=read(OUT/'after_v1/congested_four_approach__proposed/runtime_result.json')
    # Iterate over a list containing the text 'presentation_schedule', the text 'scheduled_departure_seconds', the
    # text..., binding each item to k.
    for k in ['presentation_schedule','scheduled_departure_seconds','simulation_step_seconds','presentation_duration_seconds']:
        # Require old at k equals new at k; otherwise raise AssertionError with k.
        assert old[k]==new[k],k
    # Require after at 'total_available_gap_standing_vehicle_seconds' is less than before at
    # 'total_available_gap_standing_vehicle_seconds'; otherwise raise AssertionError.
    assert after['total_available_gap_standing_vehicle_seconds']<before['total_available_gap_standing_vehicle_seconds']
    # Set historic to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historic=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v at 'sha256'
    # for (p, v) in key/value pairs from historic; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v['sha256'] for p,v in historic.items())
    # Set identity to the result of read(OUT joined with the path segment 'approved_source_identity.json').
    identity=read(OUT/'approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals s for (p, s) in
    # key/value pairs from identity; otherwise raise AssertionError.
    assert all(sha(BASE/p)==s for p,s in identity.items())
    # Require the result of sha(BASE joined with the path segment 'runtime_simulation/scenario_catalog.json') equals
    # read(OUT / 'before_v1/congested_four_approach__proposed/source_hashes.json') at
    # 'runtime_simulation/scenario_catalog.json'; otherwise raise AssertionError.
    assert sha(BASE/'runtime_simulation/scenario_catalog.json')==read(OUT/'before_v1/congested_four_approach__proposed/source_hashes.json')['runtime_simulation/scenario_catalog.json']
    # Set evidence to a dictionary built from the supplied values.
    evidence=dict(classification='QUALITATIVE_PRESENTATION_ONLY_NOT_FROZEN_EVALUATION',
        # Supply rows as rows.
        # Supply comparison as comparison.
        # Supply queue_before as before.
        # Supply queue_after as after.
        rows=rows,comparison=comparison,queue_before=before,queue_after=after,
        # Supply geometry as geometry.
        # Supply historical_files_unchanged as the number of entries in historic.
        # Supply source_identity as identity.
        geometry=geometry,historical_files_unchanged=len(historic),source_identity=identity,
        # Supply policy_sha256 as new at 'policy_sha256_after'.
        policy_sha256=new['policy_sha256_after'])
    # Set full_browser to the result of read(OUT joined with the path segment 'browser_v4/receipt.json').
    full_browser=read(OUT/'browser_v4/receipt.json')
    # Set final_browser to the result of read(OUT joined with the path segment 'browser_v5/receipt.json').
    final_browser=read(OUT/'browser_v5/receipt.json')
    # Require the number of entries in full_browser at 'cases' equals 5 and the negation of full_browser at
    # 'page_errors'; otherwise raise AssertionError.
    assert len(full_browser['cases'])==5 and not full_browser['page_errors']
    # Require full_browser['cases'][1] at 'outline_seen'; otherwise raise AssertionError.
    assert full_browser['cases'][1]['outline_seen']
    # Require the negation of full_browser at 'remaining_owned_processes'; otherwise raise AssertionError.
    assert not full_browser['remaining_owned_processes']
    # Require the text 'TimeoutExpired' belongs to 'failure' from full_browser; use the text '' if absent;
    # otherwise raise AssertionError.
    assert 'TimeoutExpired' in full_browser.get('failure','')
    # Require the negation of 'failure' from final_browser; use None if absent and the negation of final_browser
    # at 'page_errors' and the negation of final_browser at 'remaining_owned_processes'; otherwise raise
    # AssertionError.
    assert not final_browser.get('failure') and not final_browser['page_errors'] and not final_browser['remaining_owned_processes']
    # Set evidence['browser'] to a dictionary built from the supplied values.
    evidence['browser']=dict(five_scenario_functional_checks='PASS',
        # Supply full_session_shutdown as the text 'PARTIAL_WINDOWS_TIMEOUT_FORCED_CLEANUP'.
        full_session_shutdown='PARTIAL_WINDOWS_TIMEOUT_FORCED_CLEANUP',
        # Supply full_session_frames as full_browser at 'dom_samples'.
        # Supply full_session_receipt as the text 'browser_v4/receipt.json'.
        full_session_frames=full_browser['dom_samples'],full_session_receipt='browser_v4/receipt.json',
        # Supply final_comparison_panel_and_single_scenario_shutdown as the text 'PASS'.
        final_comparison_panel_and_single_scenario_shutdown='PASS',
        # Supply final_comparison_frames as final_browser at 'dom_samples'.
        # Supply final_comparison_receipt as the text 'browser_v5/receipt.json'.
        final_comparison_frames=final_browser['dom_samples'],final_comparison_receipt='browser_v5/receipt.json',
        # Supply page_errors as an empty list.
        # Supply remaining_owned_processes as an empty list.
        page_errors=[],remaining_owned_processes=[])
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(evidence,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps(dict(scenarios=rows,comparison=comparison,
        # Supply queue_before as a dictionary of k mapped to v for (k, v) in key/value pairs from before; retain
        # entries satisfying k does not belong to a set containing the text 'episodes', the text...
        queue_before={k:v for k,v in before.items() if k not in {'episodes','first_incorrect_condition'}},
        # Supply queue_after as a dictionary of k mapped to v for (k, v) in key/value pairs from after; retain
        # entries satisfying k does not belong to a set containing the text 'episodes', the text...
        queue_after={k:v for k,v in after.items() if k not in {'episodes','first_incorrect_condition'}})))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
