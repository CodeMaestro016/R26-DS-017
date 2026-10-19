"""Audit new isolated evidence against retained protected/historical results."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/offline_counterfactual/v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    historic=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/p)==value['sha256'] for p,value in historic.items())
    approved=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    assert all(sha(BASE/p)==value for p,value in approved.items())
    previous=read(BASE/'results/final_demonstrations/v1/after_v1/final_coordination_failure__proposed/runtime_result.json')
    current=read(BASE/'results/final_demonstrations/v1/sidebar_counterfactual_protected_v1/final_coordination_failure__proposed/runtime_result.json')
    for key in ['presentation_schedule','scheduled_departure_seconds','actual_departure_seconds','metrics','actual_simulation_time_seconds','policy_sha256_after']:
        assert previous[key]==current[key],key
    comparison=read(BASE/'results/final_demonstrations/v1/comparison.json')
    primary,rules=comparison['modes'];assert primary['completed']==6 and rules['completed']==1
    assert primary['collisions']==rules['collisions']==0
    native=read(OUT/'receipt.json');manifest=read(OUT/'manifest.json')
    assert native['departure_times']==current['actual_departure_seconds']
    assert native['replay_sha256']==sha(OUT/'replay.json')
    assert native['manifest_sha256']==sha(OUT/'manifest.json')
    assert all(sha(BASE/p)==value for p,value in manifest['assets'].items())
    collisions=ET.parse(OUT/'sumo_collisions.xml').getroot().findall('collision')
    assert len(collisions)==native['collision_count']==1
    collision=dict(native['collision_events'][0],sumo_event_time=float(collisions[0].get('time')))
    browser=read(OUT/'browser_scroll_v7/receipt.json')
    assert not browser.get('failure') and not browser['page_errors'] and not browser['remaining_owned_processes']
    assert len(browser['scroll_checks'])==5 and browser['headed']
    assert browser['independent_right_panel_scroll']['after']>browser['independent_right_panel_scroll']['before']['top']
    for row in browser['scroll_checks']:
        assert row['after_updates']['stable']
        assert abs(row['after_updates']['top']-row['bottom']['top'])<=2
        assert row['dragged']['top']>row['incremental']['top']+20
    source_paths=['offline_counterfactual/run.py','offline_counterfactual/protocol.json']
    source={p:sha(BASE/p) for p in source_paths}
    for p in ['app.py','pages/component2_live_view.py','pages/counterfactual_replay.py','services/counterfactual_reader.py','ui/theme.py']:
        source['socialmind_drive_showcase/'+p]=sha(BASE.parent/'socialmind_drive_showcase'/p)
    result=dict(classification='EDUCATIONAL_COUNTERFACTUAL_AND_PRESENTATION_VERIFICATION',
        historical_files_unchanged=len(historic),protected_source_identity_unchanged=approved,
        protected_metrics_identical=True,protected_completed=6,rules_only_preserved_completed=1,
        policy_sha256=current['policy_sha256_after'],counterfactual=native,
        actual_collision=collision,source_identity=source,
        browser=dict(status='PASS',receipt='browser_scroll_v7/receipt.json',viewports=['1600x1000','1280x720'],
            scroll_checks=5,retention_during_repeated_updates=True,native_scrollbar_drag_verified=True,
            page_errors=[],remaining_owned_processes=[],shutdown_timeout=browser.get('shutdown_timeout',False)))
    (OUT/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(historical_files_unchanged=len(historic),protected_completed=6,
        collisions=native['collision_count'],event_time=collision['sumo_event_time'],browser=result['browser'])))


if __name__=='__main__':main()
