"""Presentation cannot grant permission or remove scientific vehicles."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from runtime_simulation.intersection_presentation import IntersectionPresentation


GEOMETRY = dict(presentation_lanes={'n':'incoming','i':'internal','o':'outgoing'},
                presentation_region=(-50,-50,50,50))


def physical(lane='n', position=20., speed=10.):
    return dict(lane_id=lane,lane_position=position,lane_length=100.,speed=speed,
                length=5.,comfortable_deceleration_mps2=4.5)


def vehicle(x=0.,y=30.,ego='ego'):
    return dict(id=ego,front_bumper_x=x,front_bumper_y=y,
                angle_degrees=0.,length_m=5.,width_m=2.)


@pytest.mark.parametrize('position,permission,pending,expected',[
    (20.,'SAFE_HOLD',False,'APPROACHING'),
    (70.,'BLOCKED_BY_PRECEDENCE',False,'APPROACHING'),
    (96.,'SAFE_HOLD',False,'BLOCKED'),
    (96.,'PERMITTED',False,'READY'),
    (96.,'SAFE_HOLD',True,'NEGOTIATING'),
    (20.,'NATIVE_FOLLOWING',False,'APPROACHING')])
def test_colors_preserve_input_permission(position,permission,pending,expected):
    p=IntersectionPresentation();s=physical(position=position);v=vehicle()
    d=SimpleNamespace(permission=permission);before=deepcopy((s,v,d))
    row=p.classify(v,s,d,GEOMETRY,pending=pending)
    assert row['display_state']==expected
    assert (s,v,d)==before


def test_braking_stage_latches_while_speed_falls():
    p=IntersectionPresentation();d=SimpleNamespace(permission='SAFE_HOLD')
    assert p.classify(vehicle(),physical(position=88.,speed=10.),d,GEOMETRY)['display_state']=='BLOCKED'
    assert p.classify(vehicle(),physical(position=89.,speed=.1),d,GEOMETRY)['display_state']=='BLOCKED'


@pytest.mark.parametrize('lane,pos,y,clear,visible',[
    ('n',20.,30.,False,True),('i',10.,0.,False,True),
    ('o',4.,60.,False,True),('o',6.,20.,True,True),
    ('o',60.,60.,True,False),('o',51.,51.,True,True)])
def test_visibility_requires_rear_clear_and_whole_body_exit(lane,pos,y,clear,visible):
    row=IntersectionPresentation().classify(vehicle(y=y),physical(lane,pos),None,GEOMETRY)
    assert row['intersection_rear_cleared']==clear
    assert row['presentation_visible']==visible


def test_removed_vehicle_cannot_reappear_but_new_run_can_reuse_id():
    p=IntersectionPresentation();p.reset_for(('first','dense'))
    assert not p.classify(vehicle(y=60.),physical('o',60.),None,GEOMETRY)['presentation_visible']
    assert not p.classify(vehicle(),physical(),None,GEOMETRY)['presentation_visible']
    assert p.classify(vehicle(ego='new'),physical(),None,GEOMETRY)['presentation_visible']
    p.reset_for(('second','dense'))
    assert p.classify(vehicle(),physical(),None,GEOMETRY)['presentation_visible']


def test_unknown_geometry_does_not_hide_vehicle():
    assert IntersectionPresentation().classify(vehicle(y=900),None,None,{})['presentation_visible']


def test_terminal_atomic_write_retries_transient_windows_lock(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from runtime_simulation.browser_state import BrowserStatePublisher
    replace=Path.replace;attempts=[]
    def transient(path,target):
        attempts.append(path)
        if len(attempts)<3:raise PermissionError('Reader lock')
        return replace(path,target)
    monkeypatch.setattr(Path,'replace',transient)
    publisher=BrowserStatePublisher(tmp_path/'live.json',SimpleNamespace(vehicle=SimpleNamespace(getIDList=lambda:())))
    publisher.publish(simulation_time=10.,map_state={},running=False,status='FINISHED',
        completed=1,scheduled=1,force=True)
    assert len(attempts)==3
    assert json.loads((tmp_path/'live.json').read_text())['status']=='FINISHED'


@pytest.mark.parametrize('manoeuvre',['LEFT','RIGHT','STRAIGHT'])
@pytest.mark.parametrize('approach',['N','E','S','W'])
def test_every_legal_movement_uses_its_actual_lane_boundary(approach,manoeuvre):
    from conflict.map_path_manager import MapPathManager
    from runtime_simulation.browser_state import BrowserStatePublisher
    paths=MapPathManager();geometry=BrowserStatePublisher.map_snapshot(paths)
    path=paths.paths[f'{approach}_IN_0_{manoeuvre}']
    lane=paths.network.getLane(path.incoming_lane_id)
    s=physical();s.update(lane_id=path.incoming_lane_id,lane_length=lane.getLength(),
                          lane_position=lane.getLength()-80.)
    p=IntersectionPresentation();held=SimpleNamespace(permission='SAFE_HOLD')
    assert p.classify(vehicle(),s,held,geometry)['display_state']=='APPROACHING'
    s['lane_position']=lane.getLength()-2.
    assert p.classify(vehicle(),s,held,geometry)['display_state']=='BLOCKED'
    s.update(lane_id=path.internal_lane_ids[0],lane_position=1.)
    assert p.classify(vehicle(),s,held,geometry)['presentation_visible']
    s.update(lane_id=path.outgoing_lane_id,lane_position=4.)
    assert not p.classify(vehicle(),s,held,geometry)['intersection_rear_cleared']


def test_publisher_keeps_science_after_display_exit(tmp_path):
    import json
    from runtime_simulation.browser_state import BrowserStatePublisher
    api=SimpleNamespace(getIDList=lambda:('ego',),getPosition=lambda _:(0.,60.),
        getAngle=lambda _:0.,getLength=lambda _:5.,getWidth=lambda _:2.,getSpeed=lambda _:10.)
    publisher=BrowserStatePublisher(tmp_path/'live.json',SimpleNamespace(vehicle=api))
    s=physical('o',60.);s.update(position=(0.,60.),angle_degrees=0.,width=2.)
    publisher.publish(simulation_time=1.,map_state=GEOMETRY,running=True,status='EXECUTING',
        scientific_states={'ego':s},completed=0,scheduled=1,run_id='one',force=True)
    row=json.loads((tmp_path/'live.json').read_text())
    assert not row['vehicles'] and row['active_sumo_vehicles']==1
    assert len(row['scientific_vehicles'])==1 and row['completed']==0
    assert not row['completed_vehicles']
    assert publisher.presentation_vehicle_history()['final_snapshots'][0]['id']=='ego'
    publisher.publish(simulation_time=2.,map_state=GEOMETRY,running=False,status='INCOMPLETE',
        completed=0,scheduled=1,force=True)
    final=json.loads((tmp_path/'live.json').read_text())
    assert final['run_id']=='one'
    assert final['intersection_cleared_vehicle_ids']==['ego']
    assert not final['vehicles']
    assert publisher.presentation_vehicle_history()['final_snapshots'][0]['id']=='ego'
