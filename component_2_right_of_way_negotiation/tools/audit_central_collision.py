"""Audit immutable collision location against true SUMO junction geometry."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET
# Import Point, Polygon from shapely.geometry for the operations below.
from shapely.geometry import Point,Polygon
# Import body from audit_counterfactual_reproduction for the operations below.
from audit_counterfactual_reproduction import body

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
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

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set out to BASE joined with the path segment 'results/offline_counterfactual/central_presentation_v1'.
    out=BASE/'results/offline_counterfactual/central_presentation_v1'
    # Set raw to BASE joined with the path segment 'results/offline_counterfactual/v1'.
    raw=BASE/'results/offline_counterfactual/v1'
    # Set replay to the result of read(raw joined with the path segment 'replay.json').
    # Set receipt to the result of read(raw joined with the path segment 'receipt.json').
    replay=read(raw/'replay.json');receipt=read(raw/'receipt.json')
    # Require the result of sha(raw joined with the path segment 'replay.json') equals receipt at 'replay_sha256';
    # otherwise raise AssertionError.
    assert sha(raw/'replay.json')==receipt['replay_sha256']
    # Set manifest to the result of read(raw joined with the path segment 'manifest.json').
    manifest=read(raw/'manifest.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v for (p, v) in
    # key/value pairs from manifest['assets']; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v for p,v in manifest['assets'].items())
    # Set approved to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/approved_source_identity.json').
    approved=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v for (p, v) in
    # key/value pairs from approved; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v for p,v in approved.items())
    # Set policy_sha to the result of sha(BASE joined with the path segment
    # 'results/final_mappo_selection_v2/selected_policy.pt').
    policy_sha=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')
    # Require policy_sha equals read(BASE /
    # 'results/offline_counterfactual/v2_reproduction/reproduction_audit.json') at 'policy_sha256'; otherwise
    # raise AssertionError.
    assert policy_sha==read(BASE/'results/offline_counterfactual/v2_reproduction/reproduction_audit.json')['policy_sha256']
    # Set historical to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historical=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v at 'sha256'
    # for (p, v) in key/value pairs from historical; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v['sha256'] for p,v in historical.items())
    # Set node to the result of ET.parse(BASE / 'networks/intersection.net.xml').getroot().find(the text
    # "./junction[@id='center']").
    node=ET.parse(BASE/'networks/intersection.net.xml').getroot().find("./junction[@id='center']")
    # Set center to a list containing a floating-point number built from 'x' from node; use None if absent, a
    # floating-point number built from...
    center=[float(node.get('x')),float(node.get('y'))]
    # Set polygon to the result of Polygon(a list of a tuple built from the result of map(float, p.split(',')) for
    # p in the result of...).
    polygon=Polygon([tuple(map(float,p.split(','))) for p in node.get('shape').split()])
    # Set event to replay['collision_events'] at 0.
    # Set position to event at 'position'.
    event=replay['collision_events'][0];position=event['position']
    # Require the result of polygon.contains(the result of Point(position)); otherwise raise AssertionError.
    assert polygon.contains(Point(position))
    # Set frame to replay['frames'] at -1.
    # Set before to replay['frames'] at -2.
    frame=replay['frames'][-1];before=replay['frames'][-2]
    # Set vs to a dictionary of v at 'id' mapped to v for v in frame at 'vehicles'.
    vs={v['id']:v for v in frame['vehicles']}
    # Set overlap to the result of body(vs[event['collider']]).intersection(the result of body(vs at
    # event['victim'])).
    overlap=body(vs[event['collider']]).intersection(body(vs[event['victim']]))
    # Require overlap.area is greater than 0 and the result of polygon.contains(overlap); otherwise raise
    # AssertionError.
    assert overlap.area>0 and polygon.contains(overlap)
    # Set native to the result of ET.parse(raw / 'sumo_collisions.xml').getroot().find(the text 'collision').
    native=ET.parse(raw/'sumo_collisions.xml').getroot().find('collision')
    # Require 'collider' from native; use None if absent equals event at 'collider' and 'victim' from native; use
    # None if absent equals event at 'victim'; otherwise raise AssertionError.
    assert native.get('collider')==event['collider'] and native.get('victim')==event['victim']
    # Set browser to the result of read(out joined with the path segment 'receipt.json').
    # Require browser at 'status' equals the text 'PASS' and the negation of browser at 'page_errors'; otherwise
    # raise AssertionError.
    browser=read(out/'receipt.json');assert browser['status']=='PASS' and not browser['page_errors']
    # Set protected to read(out / 'protected_terminal.json') at 'run_metrics'.
    protected=read(out/'protected_terminal.json')['run_metrics']
    # Require protected at 'collisions' equals 0 and protected at 'total_vehicles_completed' equals 6; otherwise
    # raise AssertionError.
    assert protected['collisions']==0 and protected['total_vehicles_completed']==6
    # Set result to a dictionary built from the supplied values.
    result=dict(junction_center=center,collision_reference=position,
        # Supply distance_from_junction_center_m as the result of math.dist(center, position).
        # Supply reference_inside_junction as True.
        distance_from_junction_center_m=math.dist(center,position),reference_inside_junction=True,
        # Supply body_overlap_m2 as overlap.area.
        # Supply entire_overlap_inside_junction as True.
        body_overlap_m2=overlap.area,entire_overlap_inside_junction=True,
        # Supply sumo_collision_time as a floating-point number built from 'time' from native; use None if absent.
        # Supply snapshot_time as frame at 'simulation_time'.
        sumo_collision_time=float(native.get('time')),snapshot_time=frame['simulation_time'],
        # Supply previous_sample_time as before at 'simulation_time'.
        previous_sample_time=before['simulation_time'],
        # Supply note as the text 'No recorded sample at 24.24 s; native move-stage XML is 24.24...'.
        note='No recorded sample at 24.24 s; native move-stage XML is 24.24 and the collision-bearing step-ending snapshot is 24.28. No interpolation or post-impact motion claimed.',
        # Supply raw_trace_sha256 as the result of sha(raw joined with the path segment 'replay.json').
        # Supply historical_files_unchanged as the number of entries in historical.
        raw_trace_sha256=sha(raw/'replay.json'),historical_files_unchanged=len(historical),
        # Supply selected_e5_policy_sha256 as policy_sha.
        selected_e5_policy_sha256=policy_sha,
        # Supply protected_source_identity_unchanged as approved.
        # Supply protected_metrics as protected.
        protected_source_identity_unchanged=approved,protected_metrics=protected,
        # Supply website_source_hashes as a dictionary of p mapped to the result of sha(BASE.parent divided by
        # 'socialmind_drive_showcase' divided by p) for p in a list containing the text 'app.py', the text
        # 'pages/counterfactual_replay.py', the text 'pages/component2_live_view.py',...
        website_source_hashes={p:sha(BASE.parent/'socialmind_drive_showcase'/p) for p in ['app.py','pages/counterfactual_replay.py','pages/component2_live_view.py','services/counterfactual_reader.py','ui/theme.py']})
    # Write the supplied text to (out / 'geometry_integrity_audit.json').
    (out/'geometry_integrity_audit.json').write_text(json.dumps(result,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in ['protected_metrics','website_source_hashes','protected_source_identity_unchanged']}))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
