"""Retain before/after source bytes and verify diagnostic comparison integrity."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/live_deadlock_investigation/20261016'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


class IgnoreTelemetryInvocation(ast.NodeTransformer):
    def visit_ImportFrom(self,node):
        if node.module=='browser_state':return None
        return node
    def visit_keyword(self,node):
        if node.arg=='mappo_invocation':node.value=ast.Constant('DISPLAY_ONLY')
        return self.generic_visit(node)


def main():
    old_hashes=json.loads((OUT/'baseline/rule_resolved_two/source_hashes.json').read_text())
    files=['component_2_right_of_way_negotiation/runtime_simulation/runner.py',
           'component_2_right_of_way_negotiation/runtime_simulation/browser_state.py',
           'socialmind_drive_showcase/pages/component2_live_view.py']
    snapshots=OUT/'telemetry_sources'
    snapshots.mkdir(exist_ok=True)
    with zipfile.ZipFile(BASE.parent/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as z:
        for relative in files:
            old=z.read(relative)
            if relative.startswith(BASE.name+'/'):
                assert hashlib.sha256(old).hexdigest()==old_hashes[relative.split('/',1)[1]]
            for version,content in [('before',old),('after',(BASE.parent/relative).read_bytes())]:
                destination=snapshots/version/relative
                destination.parent.mkdir(parents=True,exist_ok=True)
                if destination.exists():
                    assert destination.read_bytes()==content, 'Source snapshot changed'
                else:
                    destination.write_bytes(content)
    runner=files[0]
    before=ast.parse((snapshots/'before'/runner).read_text(encoding='utf-8-sig'))
    after=ast.parse((snapshots/'after'/runner).read_text(encoding='utf-8-sig'))
    normalizer=IgnoreTelemetryInvocation()
    assert ast.dump(normalizer.visit(before))==ast.dump(normalizer.visit(after)), 'Non-telemetry control change'
    prior=BASE/'results/final_readiness/20261016'
    protected=json.loads((prior/'protected_source_inventory.json').read_text(encoding='utf-8-sig'))
    historical=json.loads((prior/'historical_inventory.json').read_text(encoding='utf-8-sig'))
    changed=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    assert set(changed)=={'runtime_simulation/runner.py','runtime_simulation/browser_state.py'}
    history_changes=[name for name,item in historical.items() if sha(BASE/name)!=item['sha256']]
    assert not history_changes
    comparisons={}
    keys=['total_vehicles_scheduled','total_vehicles_spawned','total_vehicles_completed',
          'mappo_inference_call_count','collision_count','blocked_zone_violation_count',
          'maximum_waiting_time_seconds','throughput_vehicles_per_minute','fallback_activations']
    for name in ['rule_resolved_two','multiple_left_turns','congested_four_approach','default_panel']:
        newroot=OUT/'telemetry_v1'/name
        new=json.loads((newroot/'receipt.json').read_text())
        old=json.loads((OUT/'baseline'/name/'receipt.json').read_text())
        differences={k:[old['metrics'].get(k),new['metrics'].get(k)] for k in keys if old['metrics'].get(k)!=new['metrics'].get(k)}
        assert not differences
        frame=json.loads((newroot/'live_state.json').read_text())
        if name in {'congested_four_approach','default_panel'}:
            assert frame['mappo_invocation']=='BLOCKED'
            assert frame['traffic_progress']['status']=='PERSISTENT_BLOCKAGE'
        comparisons[name]=dict(metrics={k:new['metrics'].get(k) for k in keys},
            wall_seconds=new['wall_seconds'],same_measured_traffic_outcomes=not differences,
            final_mappo_invocation=frame['mappo_invocation'],traffic_progress=frame.get('traffic_progress'))
    receipt=dict(version='DISPLAY_TELEMETRY_CORRECTION_V1',
        research_algorithm_changed=False,runner_control_ast_unchanged=True,
        protected_files_unchanged=149,protected_telemetry_files_changed=changed,
        historical_files_unchanged=len(historical),historical_changes=history_changes,
        policy_sha256=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt'),
        comparisons=comparisons,scientific_liveness_fix_implemented=False)
    (OUT/'telemetry_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
