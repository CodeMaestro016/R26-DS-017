"""Read-only trajectory analysis and independently versioned reproduction audit."""
import hashlib
import itertools
import json
import math
from pathlib import Path
from shapely.geometry import Polygon

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'results/offline_counterfactual'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def body(v):
    a=math.radians(v['angle_degrees']);f=(math.sin(a),math.cos(a));s=(math.cos(a),-math.sin(a))
    return Polygon([(v['front_bumper_x']-f[0]*b+s[0]*w,v['front_bumper_y']-f[1]*b+s[1]*w)
                    for b,w in [(0,-.9),(0,.9),(5,.9),(5,-.9)]])

def main():
    out=ROOT/'v2_reproduction';original=read(ROOT/'v1/replay.json');repeat=read(out/'replay.json')
    for key in ['frames','collision_events','departure_times','completion_times','scheduled','spawned',
                'completed','simulation_time','deadlock_observed','mean_waiting_seconds','seed']:
        assert original[key]==repeat[key],key
    assert read(ROOT/'v1/manifest.json')==read(out/'manifest.json')
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    assert all(sha(BASE/p)==v['sha256'] for p,v in historical.items())
    protected=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    assert all(sha(BASE/p)==v for p,v in protected.items())
    previous=read(BASE/'results/final_demonstrations/v1/after_v1/final_coordination_failure__proposed/runtime_result.json')
    current=read(BASE/'results/final_demonstrations/v1/timestamp_replay_protected_v2/final_coordination_failure__proposed/runtime_result.json')
    for key in ['metrics','presentation_schedule','actual_departure_seconds','actual_simulation_time_seconds','policy_sha256_after']:
        assert previous[key]==current[key],key
    ids=sorted(repeat['departure_times']);pairs=[]
    for a,b in itertools.combinations(ids,2):
        samples=[]
        for frame in repeat['frames']:
            vs={v['id']:v for v in frame['vehicles']}
            if a in vs and b in vs:
                pa,pb=body(vs[a]),body(vs[b]);samples.append(dict(time=frame['simulation_time'],
                    gap_m=pa.distance(pb),overlap_m2=pa.intersection(pb).area,
                    movements=[vs[a]['movement'],vs[b]['movement']],
                    front_positions=[[vs[v]['front_bumper_x'],vs[v]['front_bumper_y']] for v in [a,b]],
                    speeds_mps=[vs[a]['speed_mps'],vs[b]['speed_mps']]))
        closest=min(samples,key=lambda s:s['gap_m'])
        overlaps=[s for s in samples if s['overlap_m2']>0]
        pairs.append(dict(ids=[a,b],closest_sample=closest,first_sampled_overlap=overlaps[0] if overlaps else None))
    event=repeat['collision_events'][0];timeline=[]
    for frame in repeat['frames'][-6:]:
        vs={v['id']:v for v in frame['vehicles']}
        a,b=vs[event['collider']],vs[event['victim']]
        timeline.append(dict(time=frame['simulation_time'],vehicles=[a,b],
            body_gap_m=body(a).distance(body(b)),body_overlap_m2=body(a).intersection(body(b)).area,
            native_collision_count=len(frame['collisions'])))
    result=dict(classification='EDUCATIONAL_REPRODUCTION_NOT_OFFICIAL_EVALUATION',
        identical_frames_and_native_events=True,historical_files_unchanged=len(historical),
        protected_metrics_identical=True,policy_sha256=current['policy_sha256_after'],
        note='Pair distances use actual sampled oriented bodies, not predictions or statutory precedence. No post-impact frames were generated: run stops on first detection.',
        all_15_vehicle_pairs=pairs,collision_timeline=timeline)
    (out/'reproduction_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['all_15_vehicle_pairs','collision_timeline']}))

if __name__=='__main__':main()
