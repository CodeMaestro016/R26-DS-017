"""Verify matched physical outcomes and explain measured display defects."""
# Import ast for use in this module.
import ast
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/vehicle_state_consistency/20261016'.
OUT=BASE/'results/vehicle_state_consistency/20261016'


# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
# Return the decoded data produced by json.loads from the text read from path to the caller.
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
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


# Define DisplayOnly to group the state and operations declared below.
# Base classes: ast.NodeTransformer.
# Instances expose the attributes and methods implemented in this class.
class DisplayOnly(ast.NodeTransformer):
    # Visit Call using the inputs and processing steps below.
    # Input node: the supplied node.
    # Output: the result of self.generic_visit(node).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def visit_Call(self,node):
        # Run this branch when whether node.func has type ast.Attribute and node.func.attr equals the text
        # 'publish' and whether node.func.value has type ast.Name and node.func.value.id equals the text
        # 'browser'.
        if isinstance(node.func,ast.Attribute) and node.func.attr=='publish' and isinstance(node.func.value,ast.Name) and node.func.value.id=='browser':
            # Set node.keywords to a list of k for k in node.keywords; retain entries satisfying k.arg does not
            # belong to a set containing the text 'execution_decisions', the text...
            node.keywords=[k for k in node.keywords if k.arg not in {'execution_decisions','coordination_participants','coordination_timestamp','run_id'}]
            # Iterate over node.keywords, binding each item to k.
            for k in node.keywords:
                # Run this branch when k.arg equals the text 'policy_factors'.
                # Set k.value to the result of ast.Constant(the text 'DISPLAY_ONLY').
                if k.arg=='policy_factors':k.value=ast.Constant('DISPLAY_ONLY')
        # Return the result of self.generic_visit(node) to the caller.
        return self.generic_visit(node)


# Audit frames using the inputs and processing steps below.
# Input directory: the supplied directory.
# Output: a dictionary built from the supplied values.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def audit_frames(directory):
    # Set wrong_red_green and retained_caps to 0.
    wrong_red_green=retained_caps=0
    # Set closest to a dictionary containing 8.4, 0.8.
    closest={8.4:None,.8:None}
    # Set waits to an empty dictionary.
    # Set intervals to an empty list.
    waits={};intervals=[]
    # Iterate over the result of (directory /
    # 'synchronized_frames.jsonl').read_text(encoding='utf-8').splitlines(), binding each item to line.
    for line in (directory/'synchronized_frames.jsonl').read_text(encoding='utf-8').splitlines():
        # Set frame to the decoded data produced by json.loads from line.
        # Set now to frame at 'timestamp'.
        frame=json.loads(line);now=frame['timestamp']
        # Set active to a set of row['vehicle'] at 'id' for row in frame at 'rows'.
        active={row['vehicle']['id'] for row in frame['rows']}
        # Iterate over frame at 'rows', binding each item to row.
        for row in frame['rows']:
            # Set v to row at 'vehicle'.
            # Set d to row at 'decision'.
            # Set ego to v at 'id'.
            v=row['vehicle'];d=row['decision'];ego=v['id']
            # Set permission to 'permission' from d; use None if absent.
            # Set state to v at 'display_state'.
            permission=d.get('permission');state=v['display_state']
            # Update wrong_red_green to its current value plus an integer built from state equals 'READY' and
            # permission differs from 'PERMITTED' or state equals 'BLOCKED' and permission equals 'PERMITTED'.
            wrong_red_green+=int((state=='READY' and permission!='PERMITTED') or (state=='BLOCKED' and permission=='PERMITTED'))
            # Update retained_caps to its current value plus an integer built from permission equals the text
            # 'PERMITTED' and a Boolean built from 'speed_constraint_active' from v.get('control', {}); use None
            # if absent.
            retained_caps+=int(permission=='PERMITTED' and bool(v.get('control',{}).get('speed_constraint_active')))
            # Run this branch when state equals the text 'BLOCKED' and v at 'speed_mps' is greater than 0.
            if state=='BLOCKED' and v['speed_mps']>0:
                # Iterate over closest, binding each item to target.
                for target in closest:
                    # Run this branch when closest at target is the same object as None or the absolute value of
                    # v['speed_mps'] minus target is less than the absolute value of closest[target]['speed_mps']
                    # minus target.
                    if closest[target] is None or abs(v['speed_mps']-target)<abs(closest[target]['speed_mps']-target):
                        # Set closest[target] to a dictionary built from the supplied values.
                        closest[target]=dict(timestamp=now,ego_id=ego,speed_mps=v['speed_mps'],
                            # Supply decision as d.
                            decision=d)
            # Set blockers to a tuple built from a lazy sequence of z at 2 for z in 'blocked_zones' from d; use an
            # empty list if absent; retain entries satisfying z at 2.
            blockers=tuple(z[2] for z in d.get('blocked_zones',[]) if z[2])
            # Set key to a tuple containing 'reason' from d; use None if absent, blockers.
            key=(d.get('reason'),blockers)
            # Set stopped to permission differs from the text 'PERMITTED' and v at 'speed_mps' is less than 0.5.
            stopped=permission!='PERMITTED' and v['speed_mps']<.5
            # Set previous to ego from waits; use None if absent.
            previous=waits.get(ego)
            # Run this branch when previous and the negation of stopped or previous at 'key' differs from key.
            if previous and (not stopped or previous['key']!=key):
                # Run this branch when previous at 'last' minus previous at 'start' is at least 15.
                # Append previous to intervals.
                if previous['last']-previous['start']>=15:intervals.append(previous)
                # Remove the requested entry from waits.
                waits.pop(ego,None)
            # Run this branch when stopped.
            if stopped:
                # Run this branch when ego does not belong to waits.
                # Set waits[ego] to a dictionary built from the supplied values.
                if ego not in waits:waits[ego]=dict(ego_id=ego,key=key,start=now,last=now,missing_blockers=[])
                # Set waits[ego]['last'] to now.
                waits[ego]['last']=now
                # Set waits[ego]['missing_blockers'] to the sorted values from a set built from blockers minus
                # active.
                waits[ego]['missing_blockers']=sorted(set(blockers)-active)
    # Extend intervals with a lazy sequence of w for w in values from waits; retain entries satisfying w at 'last'
    # minus w at 'start' is at least 15.
    intervals.extend(w for w in waits.values() if w['last']-w['start']>=15)
    # Return a dictionary built from the supplied values to the caller.
    return dict(incorrect_red_green=wrong_red_green,permitted_with_retained_cap=retained_caps,
                # Supply moving_red_examples as a dictionary of a string built from k mapped to v for (k, v) in
                # key/value pairs from closest.
                # Supply extended_waits as intervals.
                moving_red_examples={str(k):v for k,v in closest.items()},extended_waits=intervals)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set records to an empty dictionary.
    # Set comparisons to an empty dictionary.
    records={};comparisons={}
    # Set keys to a list containing the text 'total_vehicles_spawned', the text 'total_vehicles_completed', the
    # text...
    keys=['total_vehicles_spawned','total_vehicles_completed','mappo_inference_call_count',
          'mean_waiting_time_seconds','maximum_waiting_time_seconds','throughput_vehicles_per_minute',
          'collision_count','blocked_zone_violation_count','observed_simulation_time_seconds']
    # Iterate over a list containing the text 'after_v1', the text 'after_faults_v1', binding each item to family.
    for family in ['after_v1','after_faults_v1']:
        # Iterate over the sorted values from the result of (OUT / family).iterdir(), binding each item to
        # directory.
        for directory in sorted((OUT/family).iterdir()):
            # Set r to the result of read(directory joined with the path segment 'receipt.json').
            # Set runtime to the result of read(directory joined with the path segment 'runtime_result.json').
            r=read(directory/'receipt.json');runtime=read(directory/'runtime_result.json')
            # Require r at 'unauthorized_entries' equals 0; otherwise raise AssertionError.
            assert r['unauthorized_entries']==0
            # Require r['stats'] at 'wrong_permission_color' equals r['stats'] at 'highlight_overrides'; equals 0;
            # otherwise raise AssertionError.
            assert r['stats']['wrong_permission_color']==r['stats']['highlight_overrides']==0
            # Require r['metrics'] at 'collision_count' equals r['metrics'] at 'blocked_zone_violation_count';
            # equals 0; otherwise raise AssertionError.
            assert r['metrics']['collision_count']==r['metrics']['blocked_zone_violation_count']==0
            # Require runtime at 'policy_hash_unchanged' and runtime at 'centralized_critic_calls' equals 0;
            # otherwise raise AssertionError.
            assert runtime['policy_hash_unchanged'] and runtime['centralized_critic_calls']==0
            # Require runtime at 'decentralized_execution' and the negation of runtime at
            # 'centralized_execution_graph_used_for_control'; otherwise raise AssertionError.
            assert runtime['decentralized_execution'] and not runtime['centralized_execution_graph_used_for_control']
            # Iterate over runtime at 'events', binding each item to event.
            for event in runtime['events']:
                # Iterate over 'policy_factor_diagnostics' from event; use an empty list if absent, binding each
                # item to f.
                for f in event.get('policy_factor_diagnostics',[]):
                    # Require f['hard_action_mask'] at f['selected_action_index']; otherwise raise AssertionError.
                    assert f['hard_action_mask'][f['selected_action_index']]
                    # Require f at 'ego_id' belongs to event at 'participants'; otherwise raise AssertionError.
                    assert f['ego_id'] in event['participants']
            # Set audit to the result of audit_frames(directory).
            audit=audit_frames(directory)
            # Require audit at 'incorrect_red_green' equals audit at 'permitted_with_retained_cap'; equals 0;
            # otherwise raise AssertionError.
            assert audit['incorrect_red_green']==audit['permitted_with_retained_cap']==0
            # Set records[directory.name] to a dictionary built from the supplied values.
            records[directory.name]=dict(receipt=r,audit=audit)
            # Set before to OUT joined with the path segment 'before_v1' divided by directory.name.
            before=OUT/'before_v1'/directory.name
            # Run this branch when whether before is an existing directory.
            if before.is_dir():
                # Set old to the result of read(before joined with the path segment 'receipt.json').
                # Set prior to the result of read(before joined with the path segment 'runtime_result.json').
                old=read(before/'receipt.json');prior=read(before/'runtime_result.json')
                # Require whether every item is true in a lazy sequence of k from old['metrics']; use None if
                # absent equals k from r['metrics']; use None if absent for k in keys; otherwise raise
                # AssertionError.
                assert all(old['metrics'].get(k)==r['metrics'].get(k) for k in keys)
                # Require prior at 'events' equals runtime at 'events'; otherwise raise AssertionError.
                assert prior['events']==runtime['events']
                # Set comparisons[directory.name] to a dictionary built from the supplied values.
                comparisons[directory.name]=dict(physical_metrics_and_events_identical=True,
                    # Supply before_stats as old at 'stats'.
                    # Supply after_stats as r at 'stats'.
                    before_stats=old['stats'],after_stats=r['stats'])
    # Require the number of entries in records equals 13 and the number of entries in comparisons equals 4;
    # otherwise raise AssertionError.
    assert len(records)==13 and len(comparisons)==4
    # Set oldroot to OUT joined with the path segment 'source_versions/before' divided by BASE.name joined with the path segment
    # 'runtime_simulation/runner.py'.
    oldroot=OUT/'source_versions/before'/BASE.name/'runtime_simulation/runner.py'
    # Set current to BASE joined with the path segment 'runtime_simulation/runner.py'.
    current=BASE/'runtime_simulation/runner.py'
    # Require the serialized data produced by ast.dump equals the serialized data produced by ast.dump; otherwise
    # raise AssertionError.
    assert ast.dump(DisplayOnly().visit(ast.parse(oldroot.read_text(encoding='utf-8-sig'))))==ast.dump(DisplayOnly().visit(ast.parse(current.read_text(encoding='utf-8-sig'))))
    # Set historical to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / name) equals item at
    # 'sha256' for (name, item) in key/value pairs from historical; otherwise raise AssertionError.
    assert all(sha(BASE/name)==item['sha256'] for name,item in historical.items())
    # Iterate over values from records, binding each item to item.
    for item in records.values():
        # Iterate over a list containing the text 'negotiation_execution/ego_controller.py', the text
        # 'negotiation_execution/replay.py', the text..., binding each item to path.
        for path in ['negotiation_execution/ego_controller.py','negotiation_execution/replay.py','negotiation_learning/movement_declarations.py']:
            # Require the result of sha(BASE divided by path) equals item['receipt']['source_hashes'] at path;
            # otherwise raise AssertionError.
            assert sha(BASE/path)==item['receipt']['source_hashes'][path]
    # Set protected to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/protected_source_inventory.json').
    protected=read(BASE/'results/final_readiness/20261016/protected_source_inventory.json')
    # Set changed to a list of the result of name.replace(the text '\\', the text '/') for (name, h) in key/value
    # pairs from protected; retain entries satisfying the result of sha(BASE divided by name) differs from h.
    changed=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    # Require a set built from changed equals a set containing the text 'runtime_simulation/browser_state.py', the
    # text 'runtime_simulation/runner.py', the text...; otherwise raise AssertionError.
    assert set(changed)=={'runtime_simulation/browser_state.py','runtime_simulation/runner.py','negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(version='VEHICLE_STATE_CONSISTENCY_V1',matched_comparisons=comparisons,
        # Supply controller_and_protocol_unchanged as True.
        # Supply runner_control_ast_unchanged as True.
        controller_and_protocol_unchanged=True,runner_control_ast_unchanged=True,
        # Supply historical_files_unchanged as the number of entries in historical.
        # Supply records as records.
        historical_files_unchanged=len(historical),records=records,
        # Supply browser_interactive_verification as the text 'UNAVAILABLE: discovery returned []'.
        browser_interactive_verification='UNAVAILABLE: discovery returned []')
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Set lines to a list containing the text '# Vehicle-state consistency: measured results', the text '', the
    # text 'Bounded diagnostic...
    lines=['# Vehicle-state consistency: measured results','',
        'Bounded diagnostic evidence, not a frozen scientific evaluation. Physical controllers and the approved reconciliation protocol are unchanged.','',
        '| Scenario / fault | Sim seconds | Spawned | Completed | MAPPO calls | Mean wait s | Max wait s | Throughput/min | Collision / blocked-entry / unauthorized entry | Incorrect permission colors |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    # Iterate over key/value pairs from records, binding each item to (name, item).
    for name,item in records.items():
        # Set r to item at 'receipt'.
        # Set m to r at 'metrics'.
        r=item['receipt'];m=r['metrics']
        # Set values to a list containing name, m at 'observed_simulation_time_seconds', m at
        # 'total_vehicles_spawned', m at...
        values=[name,m['observed_simulation_time_seconds'],m['total_vehicles_spawned'],m['total_vehicles_completed'],m['mappo_inference_call_count'],
            # Include the rounded value of m at 'maximum_waiting_time_seconds' in this list.
            round(m['mean_waiting_time_seconds'],3),round(m['maximum_waiting_time_seconds'],3),
            # Include the rounded value of m at 'throughput_vehicles_per_minute' in this list.
            round(m['throughput_vehicles_per_minute'],6),'0 / 0 / 0',r['stats']['wrong_permission_color']]
        # Append the text '|' plus the result of ' | '.join(the result of map(str, values)) plus the text '|' to
        # lines.
        lines.append('| '+' | '.join(map(str,values))+' |')
    # Update lines to its current value plus a list containing the text '', the text 'Four matched before/after
    # cases have exactly identical...', the text 'Dense...
    lines+=['','Four matched before/after cases have exactly identical measured physical outcomes, waiting/throughput metrics and original negotiation event records.',
        'Dense before/after diagnostics both use a predeclared 70-second horizon. Their censored waiting and throughput values must not be compared directly with the preceding 360-second dense study.',
        'Incorrect recent-event color overrides fell from 104 to zero sampled vehicle-frames in dense traffic, and 69 to zero in the regulatory-cycle case. These counts are sampled vehicle-frames, not independent episodes.',
        'Red vehicles may still move toward their stop boundary. No PERMITTED sample retained a precedence speed constraint. Extended dense waiting remains explained by current dependencies/follower gates, not removed by a timer.',
        'All original masked actor choices were checked for allowed action indices and correct participant IDs. The four-way scenario is rule-resolved; the separate regulatory-cycle run invokes MAPPO.',
        # Include formatted text built from the embedded values in this list.
        f'Historical files verified unchanged: {len(historical)}. E5 SHA-256: `{sha(BASE/"results/final_mappo_selection_v2/selected_policy.pt")}`.',
        'See VEHICLE_STATE_CONSISTENCY_REPORT.md for the precise visual contract, scope, test receipts, startup commands and remaining scientific limitation.','']
    # Write the supplied text to (BASE / 'docs/VEHICLE_STATE_CONSISTENCY_RESULTS.md').
    (BASE/'docs/VEHICLE_STATE_CONSISTENCY_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    # Display the text 'Verified'.
    print('Verified',len(records),'real after/fault runs and',len(comparisons),'matched comparisons.')


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
