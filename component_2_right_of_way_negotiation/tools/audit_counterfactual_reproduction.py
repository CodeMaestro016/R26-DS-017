"""Read-only trajectory analysis and independently versioned reproduction audit."""
# Import hashlib for use in this module.
import hashlib
# Import itertools for use in this module.
import itertools
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import Polygon from shapely.geometry for the operations below.
from shapely.geometry import Polygon

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set ROOT to BASE joined with the path segment 'results/offline_counterfactual'.
ROOT=BASE/'results/offline_counterfactual'

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
# Body using the inputs and processing steps below.
# Input v: the supplied v.
# Output: the result of Polygon(a list of a tuple containing v['front_bumper_x'] - f[0] * b plus s[0] * w,
# v['front_bumper_y'] -...).
def body(v):
    # Set a to the result of math.radians(v at 'angle_degrees').
    # Set f to a tuple containing the result of math.sin(a), the result of math.cos(a).
    # Set s to a tuple containing the result of math.cos(a), the negative of the result of math.sin(a).
    a=math.radians(v['angle_degrees']);f=(math.sin(a),math.cos(a));s=(math.cos(a),-math.sin(a))
    # Return the result of Polygon(a list of a tuple containing v['front_bumper_x'] - f[0] * b plus s[0] * w,
    # v['front_bumper_y'] -...) to the caller.
    return Polygon([(v['front_bumper_x']-f[0]*b+s[0]*w,v['front_bumper_y']-f[1]*b+s[1]*w)
                    # Evaluate a list containing a tuple containing 0, the negative of 0.9, a tuple containing 0,
                    # 0.9, a tuple containing 5, 0.9, a tuple... as part of the enclosing expression.
                    for b,w in [(0,-.9),(0,.9),(5,.9),(5,-.9)]])

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set out to ROOT joined with the path segment 'v2_reproduction'.
    # Set original to the result of read(ROOT joined with the path segment 'v1/replay.json').
    # Set repeat to the result of read(out joined with the path segment 'replay.json').
    out=ROOT/'v2_reproduction';original=read(ROOT/'v1/replay.json');repeat=read(out/'replay.json')
    # Iterate over a list containing the text 'frames', the text 'collision_events', the text 'departure_times',
    # the text 'completion_times',..., binding each item to key.
    for key in ['frames','collision_events','departure_times','completion_times','scheduled','spawned',
                'completed','simulation_time','deadlock_observed','mean_waiting_seconds','seed']:
        # Require original at key equals repeat at key; otherwise raise AssertionError with key.
        assert original[key]==repeat[key],key
    # Require the result of read(ROOT joined with the path segment 'v1/manifest.json') equals the result of read(out
    # joined with the path segment 'manifest.json'); otherwise raise AssertionError.
    assert read(ROOT/'v1/manifest.json')==read(out/'manifest.json')
    # Set historical to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v at 'sha256'
    # for (p, v) in key/value pairs from historical; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v['sha256'] for p,v in historical.items())
    # Set protected to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/approved_source_identity.json').
    protected=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v for (p, v) in
    # key/value pairs from protected; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v for p,v in protected.items())
    # Set previous to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/after_v1/final_coordination_fa...').
    previous=read(BASE/'results/final_demonstrations/v1/after_v1/final_coordination_failure__proposed/runtime_result.json')
    # Set current to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/timestamp_replay_protected_v2/...').
    current=read(BASE/'results/final_demonstrations/v1/timestamp_replay_protected_v2/final_coordination_failure__proposed/runtime_result.json')
    # Iterate over a list containing the text 'metrics', the text 'presentation_schedule', the text
    # 'actual_departure_seconds', the text..., binding each item to key.
    for key in ['metrics','presentation_schedule','actual_departure_seconds','actual_simulation_time_seconds','policy_sha256_after']:
        # Require previous at key equals current at key; otherwise raise AssertionError with key.
        assert previous[key]==current[key],key
    # Set ids to the sorted values from repeat at 'departure_times'.
    # Set pairs to an empty list.
    ids=sorted(repeat['departure_times']);pairs=[]
    # Iterate over the result of itertools.combinations(ids, 2), binding each item to (a, b).
    for a,b in itertools.combinations(ids,2):
        # Set samples to an empty list.
        samples=[]
        # Iterate over repeat at 'frames', binding each item to frame.
        for frame in repeat['frames']:
            # Set vs to a dictionary of v at 'id' mapped to v for v in frame at 'vehicles'.
            vs={v['id']:v for v in frame['vehicles']}
            # Run this branch when a belongs to vs and b belongs to vs.
            if a in vs and b in vs:
                # Set (pa, pb) to a tuple containing the result of body(vs at a), the result of body(vs at b).
                # Append a dictionary built from the supplied values to samples.
                pa,pb=body(vs[a]),body(vs[b]);samples.append(dict(time=frame['simulation_time'],
                    # Supply gap_m as the result of pa.distance(pb).
                    # Supply overlap_m2 as pa.intersection(pb).area.
                    gap_m=pa.distance(pb),overlap_m2=pa.intersection(pb).area,
                    # Supply movements as a list containing vs[a] at 'movement', vs[b] at 'movement'.
                    movements=[vs[a]['movement'],vs[b]['movement']],
                    # Supply front_positions as a list of a list containing vs[v] at 'front_bumper_x', vs[v] at
                    # 'front_bumper_y' for v in a list containing a, b.
                    front_positions=[[vs[v]['front_bumper_x'],vs[v]['front_bumper_y']] for v in [a,b]],
                    # Supply speeds_mps as a list containing vs[a] at 'speed_mps', vs[b] at 'speed_mps'.
                    speeds_mps=[vs[a]['speed_mps'],vs[b]['speed_mps']]))
        # Set closest to the minimum of samples.
        closest=min(samples,key=lambda s:s['gap_m'])
        # Set overlaps to a list of s for s in samples; retain entries satisfying s at 'overlap_m2' is greater
        # than 0.
        overlaps=[s for s in samples if s['overlap_m2']>0]
        # Append a dictionary built from the supplied values to pairs.
        pairs.append(dict(ids=[a,b],closest_sample=closest,first_sampled_overlap=overlaps[0] if overlaps else None))
    # Set event to repeat['collision_events'] at 0.
    # Set timeline to an empty list.
    event=repeat['collision_events'][0];timeline=[]
    # Iterate over repeat['frames'] sliced by -6:, binding each item to frame.
    for frame in repeat['frames'][-6:]:
        # Set vs to a dictionary of v at 'id' mapped to v for v in frame at 'vehicles'.
        vs={v['id']:v for v in frame['vehicles']}
        # Set (a, b) to a tuple containing vs at event['collider'], vs at event['victim'].
        a,b=vs[event['collider']],vs[event['victim']]
        # Append a dictionary built from the supplied values to timeline.
        timeline.append(dict(time=frame['simulation_time'],vehicles=[a,b],
            # Supply body_gap_m as the result of body(a).distance(the result of body(b)).
            # Supply body_overlap_m2 as body(a).intersection(body(b)).area.
            body_gap_m=body(a).distance(body(b)),body_overlap_m2=body(a).intersection(body(b)).area,
            # Supply native_collision_count as the number of entries in frame at 'collisions'.
            native_collision_count=len(frame['collisions'])))
    # Set result to a dictionary built from the supplied values.
    result=dict(classification='EDUCATIONAL_REPRODUCTION_NOT_OFFICIAL_EVALUATION',
        # Supply identical_frames_and_native_events as True.
        # Supply historical_files_unchanged as the number of entries in historical.
        identical_frames_and_native_events=True,historical_files_unchanged=len(historical),
        # Supply protected_metrics_identical as True.
        # Supply policy_sha256 as current at 'policy_sha256_after'.
        protected_metrics_identical=True,policy_sha256=current['policy_sha256_after'],
        # Supply note as the text 'Pair distances use actual sampled oriented bodies, not...'.
        note='Pair distances use actual sampled oriented bodies, not predictions or statutory precedence. No post-impact frames were generated: run stops on first detection.',
        # Supply all_15_vehicle_pairs as pairs.
        # Supply collision_timeline as timeline.
        all_15_vehicle_pairs=pairs,collision_timeline=timeline)
    # Write the supplied text to (out / 'reproduction_audit.json').
    (out/'reproduction_audit.json').write_text(json.dumps(result,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in ['all_15_vehicle_pairs','collision_timeline']}))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
