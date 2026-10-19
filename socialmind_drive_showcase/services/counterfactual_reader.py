"""Read-only isolated evidence; no simulator imports, launch or control calls."""
import hashlib
import json
import math
from functools import lru_cache
import xml.etree.ElementTree as ET
from socialmind_drive_showcase.config import COMPONENT2_ROOT

ROOT=COMPONENT2_ROOT/'results/offline_counterfactual/v1'
CLASSIFICATION='OFFLINE_UNSAFE_COUNTERFACTUAL_NOT_PROPOSED_SYSTEM'


@lru_cache(maxsize=1)
def load_evidence():
    raw=(ROOT/'replay.json').read_bytes()
    receipt=json.loads((ROOT/'receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=receipt['replay_sha256']:raise ValueError('Counterfactual trace checksum mismatch')
    value=json.loads(raw)
    if value['classification']!=CLASSIFICATION:raise ValueError('Not isolated counterfactual evidence')
    times=[frame['simulation_time'] for frame in value['frames']]
    if not times or any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError('Recorded timestamps must strictly increase')
    native=ET.parse(ROOT/'sumo_collisions.xml').getroot().findall('collision')
    if len(native)!=value['collision_count']:raise ValueError('SUMO XML and replay collision counts differ')
    native_events=[]
    for event in value['collision_events']:
        match=next(x for x in native if x.get('collider')==event['collider'] and x.get('victim')==event['victim'])
        native_events.append(dict(event,sumo_event_time=float(match.get('time')),
            traci_detection_time=event['timestamp']))
    return dict(value,documented_collision_events=native_events,
        provenance=dict(replay_sha256=receipt['replay_sha256'],
            xml_sha256=hashlib.sha256((ROOT/'sumo_collisions.xml').read_bytes()).hexdigest(),
            path='component_2_right_of_way_negotiation/results/offline_counterfactual/v1',
            protocol=value['version'],seed=value['seed']))


def recorded_frame(index=0):
    evidence=load_evidence();index=max(0,min(int(index),len(evidence['frames'])-1))
    return dict(available=True,classification=CLASSIFICATION,index=index,total_frames=len(evidence['frames']),
        frame=evidence['frames'][index],outcome=evidence['outcome'],
        collision_count=evidence['collision_count'],events=evidence['documented_collision_events'],
        timeline=[frame['simulation_time'] for frame in evidence['frames']],
        first_full_demand_frame_index=next((i for i,f in enumerate(evidence['frames']) if len(f['vehicles'])==evidence['scheduled']),0),
        collision_frame_index=next((i for i,f in enumerate(evidence['frames']) if f['collisions']),None),
        provenance=evidence['provenance'])


@lru_cache(maxsize=1)
def junction_evidence():
    """Use the actual network junction coordinates, never a drawn road center."""
    node=ET.parse(COMPONENT2_ROOT/'networks/intersection.net.xml').getroot().find("./junction[@id='center']")
    center=[float(node.get('x')),float(node.get('y'))]
    polygon=[list(map(float,p.split(','))) for p in node.get('shape').split()]
    event=load_evidence()['documented_collision_events'][0]
    return dict(center=center,polygon=polygon,collision_reference=event['position'],
                distance_from_center_m=math.dist(center,event['position']))
