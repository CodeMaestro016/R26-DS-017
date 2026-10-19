"""Authentic offline evidence cannot execute or replace protected control."""
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon

from socialmind_drive_showcase.services.counterfactual_reader import ROOT,load_evidence,recorded_frame


def test_replay_matches_native_xml_and_frozen_six_vehicle_demand():
    evidence=load_evidence()
    native=ET.parse(ROOT/'sumo_collisions.xml').getroot().findall('collision')
    assert evidence['scheduled']==evidence['spawned']==6
    assert evidence['collision_count']==len(native)==1
    event=evidence['documented_collision_events'][0]
    assert event['sumo_event_time']==24.24 and event['traci_detection_time']==24.28
    assert event['collider']=='PANEL_AV_N_02' and event['victim']=='PANEL_AV_W_01'
    assert evidence['frames'][-1]['collisions']
    assert hashlib.sha256((ROOT/'replay.json').read_bytes()).hexdigest()==evidence['provenance']['replay_sha256']
    for frame in evidence['frames']:
        for vehicle in frame['vehicles']:
            assert vehicle['length_m']==5 and vehicle['width_m']==1.8
            assert vehicle['accel_limit']==2 and vehicle['decel_limit']==4.5


def test_simulator_collision_has_actual_body_overlap():
    evidence=load_evidence();frame=evidence['frames'][-1]
    event=frame['collisions'][0];vehicles={v['id']:v for v in frame['vehicles']}
    def footprint(v):
        angle=math.radians(v['angle_degrees']);forward=(math.sin(angle),math.cos(angle));side=(math.cos(angle),-math.sin(angle))
        x,y=v['front_bumper_x'],v['front_bumper_y'];length=v['length_m'];width=v['width_m']/2
        return Polygon([(x-forward[0]*back+side[0]*lateral,y-forward[1]*back+side[1]*lateral)
                        for back,lateral in [(0,-width),(0,width),(length,width),(length,-width)]])
    assert footprint(vehicles[event['collider']]).intersection(footprint(vehicles[event['victim']])).area>0


def test_readonly_api_never_launches_or_changes_live_state(monkeypatch):
    from socialmind_drive_showcase import app as site
    def forbidden(*args,**kwargs):raise AssertionError('Replay attempted control')
    monkeypatch.setattr(site.LAUNCHER,'launch',forbidden)
    monkeypatch.setattr(site.LAUNCHER,'request_stop',forbidden)
    result=site.counterfactual_frame_api(999999)
    assert result['index']==result['total_frames']-1
    assert 'recorded-collision-marker' in result['rendered_svg']
    assert 'c2-synchronized-frame' not in result['rendered_svg']
    assert 'onclick=' not in result['rendered_svg']
    assert not recorded_frame(0)['frame']['collisions']


def test_current_primary_and_rules_only_results_remain_distinct():
    from socialmind_drive_showcase.config import COMPONENT2_ROOT
    comparison=json.loads((COMPONENT2_ROOT/'results/final_demonstrations/v1/comparison.json').read_text())
    primary,baseline=comparison['modes']
    assert primary['completed']==6 and primary['mappo_calls']==1 and primary['collisions']==0
    assert baseline['completed']==1 and baseline['mappo_calls']==0 and baseline['collisions']==0
    assert baseline['status']=='INCOMPLETE'


def test_replay_timeline_and_event_navigation_come_from_actual_frames():
    evidence=load_evidence();response=recorded_frame(0)
    assert response['timeline']==[f['simulation_time'] for f in evidence['frames']]
    assert all(b>a for a,b in zip(response['timeline'],response['timeline'][1:]))
    event_index=response['collision_frame_index']
    assert evidence['frames'][event_index]['collisions']==evidence['collision_events']
    assert response['timeline'][event_index]==evidence['documented_collision_events'][0]['traci_detection_time']


def test_collision_is_inside_real_junction_and_cameras_share_actual_frames():
    from shapely.geometry import Point
    from socialmind_drive_showcase.services.counterfactual_reader import junction_evidence
    from socialmind_drive_showcase import app as site
    junction=junction_evidence()
    assert junction['center']==[300.,300.]
    assert 1.80<junction['distance_from_center_m']<1.81
    assert Polygon(junction['polygon']).contains(Point(junction['collision_reference']))
    first=recorded_frame(0)['first_full_demand_frame_index']
    assert len(recorded_frame(first)['frame']['vehicles'])==6
    final=site.counterfactual_frame_api(99999)
    for svg in [final['rendered_svg'],final['overview_svg']]:
        assert svg.count('class="offline-car"')==6
        assert 'recorded-collision-marker' in svg
        assert 'recorded-route' in svg
        assert 'onclick=' not in svg
