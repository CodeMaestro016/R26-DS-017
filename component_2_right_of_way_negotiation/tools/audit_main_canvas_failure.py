"""Final audit for main-canvas integration; historical receipts stay untouched."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    root=BASE/'results/offline_counterfactual';out=root/'main_canvas_v2'
    history=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/p)==v['sha256'] for p,v in history.items())
    protected=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    assert all(sha(BASE/p)==v for p,v in protected.items())
    native=read(root/'v1/receipt.json')
    assert sha(root/'v1/replay.json')==native['replay_sha256']
    geometry=read(root/'central_presentation_v1/geometry_integrity_audit.json')
    policy=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')
    assert policy==geometry['selected_e5_policy_sha256']
    for name in ['main_canvas_v1','main_canvas_v2']:
        browser=read(root/name/'receipt.json')
        assert browser['status']=='PASS' and not browser['page_errors']
        assert browser['no_modal_or_navigation'] and browser['same_main_canvas']
    science={}
    for name,expected in [('scenario2',4),('scenario4',16)]:
        terminal=read(root/'main_canvas_v1'/f'{name}_terminal.json')
        metrics=terminal['run_metrics']
        assert metrics['total_vehicles_completed']==expected and metrics['collisions']==0
        assert metrics['centralized_critic_runtime_calls']==0 and metrics['mappo_decision_epochs']>0
        science[name]=dict(simulation_time=terminal['simulation_time'],metrics=metrics)
    result=dict(historical_files_unchanged=len(history),protected_source_identities_unchanged=protected,
        checkpoint_sha256=policy,raw_replay_sha256=native['replay_sha256'],new_unsafe_experiment=False,
        collision_distance_from_junction_center_m=geometry['distance_from_junction_center_m'],
        collision_body_overlap_m2=geometry['body_overlap_m2'],browser_status='PASS',scientific_runs=science,
        website_source_hashes={p:sha(BASE.parent/'socialmind_drive_showcase'/p) for p in ['pages/component2_live_view.py','pages/component2_inspector.py','services/main_canvas_replay.py','ui/theme.py']})
    (out/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['scientific_runs','website_source_hashes','protected_source_identities_unchanged']}))

if __name__=='__main__':main()
