"""Audit immutable collision location against true SUMO junction geometry."""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from shapely.geometry import Point,Polygon
from audit_counterfactual_reproduction import body

BASE=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    out=BASE/'results/offline_counterfactual/central_presentation_v1'
    raw=BASE/'results/offline_counterfactual/v1'
    replay=read(raw/'replay.json');receipt=read(raw/'receipt.json')
    assert sha(raw/'replay.json')==receipt['replay_sha256']
    manifest=read(raw/'manifest.json')
    assert all(sha(BASE/p)==v for p,v in manifest['assets'].items())
    approved=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    assert all(sha(BASE/p)==v for p,v in approved.items())
    policy_sha=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')
    assert policy_sha==read(BASE/'results/offline_counterfactual/v2_reproduction/reproduction_audit.json')['policy_sha256']
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/p)==v['sha256'] for p,v in historical.items())
    node=ET.parse(BASE/'networks/intersection.net.xml').getroot().find("./junction[@id='center']")
    center=[float(node.get('x')),float(node.get('y'))]
    polygon=Polygon([tuple(map(float,p.split(','))) for p in node.get('shape').split()])
    event=replay['collision_events'][0];position=event['position']
    assert polygon.contains(Point(position))
    frame=replay['frames'][-1];before=replay['frames'][-2]
    vs={v['id']:v for v in frame['vehicles']}
    overlap=body(vs[event['collider']]).intersection(body(vs[event['victim']]))
    assert overlap.area>0 and polygon.contains(overlap)
    native=ET.parse(raw/'sumo_collisions.xml').getroot().find('collision')
    assert native.get('collider')==event['collider'] and native.get('victim')==event['victim']
    browser=read(out/'receipt.json');assert browser['status']=='PASS' and not browser['page_errors']
    protected=read(out/'protected_terminal.json')['run_metrics']
    assert protected['collisions']==0 and protected['total_vehicles_completed']==6
    result=dict(junction_center=center,collision_reference=position,
        distance_from_junction_center_m=math.dist(center,position),reference_inside_junction=True,
        body_overlap_m2=overlap.area,entire_overlap_inside_junction=True,
        sumo_collision_time=float(native.get('time')),snapshot_time=frame['simulation_time'],
        previous_sample_time=before['simulation_time'],
        note='No recorded sample at 24.24 s; native move-stage XML is 24.24 and the collision-bearing step-ending snapshot is 24.28. No interpolation or post-impact motion claimed.',
        raw_trace_sha256=sha(raw/'replay.json'),historical_files_unchanged=len(historical),
        selected_e5_policy_sha256=policy_sha,
        protected_source_identity_unchanged=approved,protected_metrics=protected,
        website_source_hashes={p:sha(BASE.parent/'socialmind_drive_showcase'/p) for p in ['app.py','pages/counterfactual_replay.py','pages/component2_live_view.py','services/counterfactual_reader.py','ui/theme.py']})
    (out/'geometry_integrity_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['protected_metrics','website_source_hashes','protected_source_identity_unchanged']}))

if __name__=='__main__':main()
