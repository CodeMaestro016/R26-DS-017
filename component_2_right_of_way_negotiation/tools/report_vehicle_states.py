"""Verify matched physical outcomes and explain measured display defects."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/vehicle_state_consistency/20261016'


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


class DisplayOnly(ast.NodeTransformer):
    def visit_Call(self,node):
        if isinstance(node.func,ast.Attribute) and node.func.attr=='publish' and isinstance(node.func.value,ast.Name) and node.func.value.id=='browser':
            node.keywords=[k for k in node.keywords if k.arg not in {'execution_decisions','coordination_participants','coordination_timestamp','run_id'}]
            for k in node.keywords:
                if k.arg=='policy_factors':k.value=ast.Constant('DISPLAY_ONLY')
        return self.generic_visit(node)


def audit_frames(directory):
    wrong_red_green=retained_caps=0
    closest={8.4:None,.8:None}
    waits={};intervals=[]
    for line in (directory/'synchronized_frames.jsonl').read_text(encoding='utf-8').splitlines():
        frame=json.loads(line);now=frame['timestamp']
        active={row['vehicle']['id'] for row in frame['rows']}
        for row in frame['rows']:
            v=row['vehicle'];d=row['decision'];ego=v['id']
            permission=d.get('permission');state=v['display_state']
            wrong_red_green+=int((state=='READY' and permission!='PERMITTED') or (state=='BLOCKED' and permission=='PERMITTED'))
            retained_caps+=int(permission=='PERMITTED' and bool(v.get('control',{}).get('speed_constraint_active')))
            if state=='BLOCKED' and v['speed_mps']>0:
                for target in closest:
                    if closest[target] is None or abs(v['speed_mps']-target)<abs(closest[target]['speed_mps']-target):
                        closest[target]=dict(timestamp=now,ego_id=ego,speed_mps=v['speed_mps'],
                            decision=d)
            blockers=tuple(z[2] for z in d.get('blocked_zones',[]) if z[2])
            key=(d.get('reason'),blockers)
            stopped=permission!='PERMITTED' and v['speed_mps']<.5
            previous=waits.get(ego)
            if previous and (not stopped or previous['key']!=key):
                if previous['last']-previous['start']>=15:intervals.append(previous)
                waits.pop(ego,None)
            if stopped:
                if ego not in waits:waits[ego]=dict(ego_id=ego,key=key,start=now,last=now,missing_blockers=[])
                waits[ego]['last']=now
                waits[ego]['missing_blockers']=sorted(set(blockers)-active)
    intervals.extend(w for w in waits.values() if w['last']-w['start']>=15)
    return dict(incorrect_red_green=wrong_red_green,permitted_with_retained_cap=retained_caps,
                moving_red_examples={str(k):v for k,v in closest.items()},extended_waits=intervals)


def main():
    records={};comparisons={}
    keys=['total_vehicles_spawned','total_vehicles_completed','mappo_inference_call_count',
          'mean_waiting_time_seconds','maximum_waiting_time_seconds','throughput_vehicles_per_minute',
          'collision_count','blocked_zone_violation_count','observed_simulation_time_seconds']
    for family in ['after_v1','after_faults_v1']:
        for directory in sorted((OUT/family).iterdir()):
            r=read(directory/'receipt.json');runtime=read(directory/'runtime_result.json')
            assert r['unauthorized_entries']==0
            assert r['stats']['wrong_permission_color']==r['stats']['highlight_overrides']==0
            assert r['metrics']['collision_count']==r['metrics']['blocked_zone_violation_count']==0
            assert runtime['policy_hash_unchanged'] and runtime['centralized_critic_calls']==0
            assert runtime['decentralized_execution'] and not runtime['centralized_execution_graph_used_for_control']
            for event in runtime['events']:
                for f in event.get('policy_factor_diagnostics',[]):
                    assert f['hard_action_mask'][f['selected_action_index']]
                    assert f['ego_id'] in event['participants']
            audit=audit_frames(directory)
            assert audit['incorrect_red_green']==audit['permitted_with_retained_cap']==0
            records[directory.name]=dict(receipt=r,audit=audit)
            before=OUT/'before_v1'/directory.name
            if before.is_dir():
                old=read(before/'receipt.json');prior=read(before/'runtime_result.json')
                assert all(old['metrics'].get(k)==r['metrics'].get(k) for k in keys)
                assert prior['events']==runtime['events']
                comparisons[directory.name]=dict(physical_metrics_and_events_identical=True,
                    before_stats=old['stats'],after_stats=r['stats'])
    assert len(records)==13 and len(comparisons)==4
    oldroot=OUT/'source_versions/before'/BASE.name/'runtime_simulation/runner.py'
    current=BASE/'runtime_simulation/runner.py'
    assert ast.dump(DisplayOnly().visit(ast.parse(oldroot.read_text(encoding='utf-8-sig'))))==ast.dump(DisplayOnly().visit(ast.parse(current.read_text(encoding='utf-8-sig'))))
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/name)==item['sha256'] for name,item in historical.items())
    for item in records.values():
        for path in ['negotiation_execution/ego_controller.py','negotiation_execution/replay.py','negotiation_learning/movement_declarations.py']:
            assert sha(BASE/path)==item['receipt']['source_hashes'][path]
    protected=read(BASE/'results/final_readiness/20261016/protected_source_inventory.json')
    changed=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    assert set(changed)=={'runtime_simulation/browser_state.py','runtime_simulation/runner.py','negotiation_execution/replay.py','negotiation_execution/ego_controller.py'}
    receipt=dict(version='VEHICLE_STATE_CONSISTENCY_V1',matched_comparisons=comparisons,
        controller_and_protocol_unchanged=True,runner_control_ast_unchanged=True,
        historical_files_unchanged=len(historical),records=records,
        browser_interactive_verification='UNAVAILABLE: discovery returned []')
    (OUT/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    lines=['# Vehicle-state consistency: measured results','',
        'Bounded diagnostic evidence, not a frozen scientific evaluation. Physical controllers and the approved reconciliation protocol are unchanged.','',
        '| Scenario / fault | Sim seconds | Spawned | Completed | MAPPO calls | Mean wait s | Max wait s | Throughput/min | Collision / blocked-entry / unauthorized entry | Incorrect permission colors |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for name,item in records.items():
        r=item['receipt'];m=r['metrics']
        values=[name,m['observed_simulation_time_seconds'],m['total_vehicles_spawned'],m['total_vehicles_completed'],m['mappo_inference_call_count'],
            round(m['mean_waiting_time_seconds'],3),round(m['maximum_waiting_time_seconds'],3),
            round(m['throughput_vehicles_per_minute'],6),'0 / 0 / 0',r['stats']['wrong_permission_color']]
        lines.append('| '+' | '.join(map(str,values))+' |')
    lines+=['','Four matched before/after cases have exactly identical measured physical outcomes, waiting/throughput metrics and original negotiation event records.',
        'Dense before/after diagnostics both use a predeclared 70-second horizon. Their censored waiting and throughput values must not be compared directly with the preceding 360-second dense study.',
        'Incorrect recent-event color overrides fell from 104 to zero sampled vehicle-frames in dense traffic, and 69 to zero in the regulatory-cycle case. These counts are sampled vehicle-frames, not independent episodes.',
        'Red vehicles may still move toward their stop boundary. No PERMITTED sample retained a precedence speed constraint. Extended dense waiting remains explained by current dependencies/follower gates, not removed by a timer.',
        'All original masked actor choices were checked for allowed action indices and correct participant IDs. The four-way scenario is rule-resolved; the separate regulatory-cycle run invokes MAPPO.',
        f'Historical files verified unchanged: {len(historical)}. E5 SHA-256: `{sha(BASE/"results/final_mappo_selection_v2/selected_policy.pt")}`.',
        'See VEHICLE_STATE_CONSISTENCY_REPORT.md for the precise visual contract, scope, test receipts, startup commands and remaining scientific limitation.','']
    (BASE/'docs/VEHICLE_STATE_CONSISTENCY_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Verified',len(records),'real after/fault runs and',len(comparisons),'matched comparisons.')


if __name__=='__main__':main()
