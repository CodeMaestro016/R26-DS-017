"""Presentation cannot grant permission or remove scientific vehicles."""
# Import deepcopy from copy for the operations below.
from copy import deepcopy
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest
# Import IntersectionPresentation from runtime_simulation.intersection_presentation for the operations below.
from runtime_simulation.intersection_presentation import IntersectionPresentation


# Set GEOMETRY to a dictionary built from the supplied values.
GEOMETRY = dict(presentation_lanes={'n':'incoming','i':'internal','o':'outgoing'},
                # Supply presentation_region as a tuple containing the negative of 50, the negative of 50, 50, 50.
                presentation_region=(-50,-50,50,50))


# Physical using the inputs and processing steps below.
# Input lane: the supplied lane.
# Input position: the supplied position.
# Input speed: the supplied speed.
# Output: a dictionary built from the supplied values.
def physical(lane='n', position=20., speed=10.):
    # Return a dictionary built from the supplied values to the caller.
    return dict(lane_id=lane,lane_position=position,lane_length=100.,speed=speed,
                # Supply length as 5.0.
                # Supply comfortable_deceleration_mps2 as 4.5.
                length=5.,comfortable_deceleration_mps2=4.5)


# Vehicle using the inputs and processing steps below.
# Input x: the supplied x.
# Input y: the supplied y.
# Input ego: the ego vehicle used in this calculation.
# Output: a dictionary built from the supplied values.
def vehicle(x=0.,y=30.,ego='ego'):
    # Return a dictionary built from the supplied values to the caller.
    return dict(id=ego,front_bumper_x=x,front_bumper_y=y,
                # Supply angle_degrees as 0.0.
                # Supply length_m as 5.0.
                # Supply width_m as 2.0.
                angle_degrees=0.,length_m=5.,width_m=2.)


# Apply 'position,permission,pending,expected' as a decorator to configure the following definition.
@pytest.mark.parametrize('position,permission,pending,expected',[
    # Include a tuple containing 20.0, the text 'SAFE_HOLD', False, the text 'APPROACHING' in this list.
    (20.,'SAFE_HOLD',False,'APPROACHING'),
    # Include a tuple containing 70.0, the text 'BLOCKED_BY_PRECEDENCE', False, the text 'APPROACHING' in this
    # list.
    (70.,'BLOCKED_BY_PRECEDENCE',False,'APPROACHING'),
    # Include a tuple containing 96.0, the text 'SAFE_HOLD', False, the text 'BLOCKED' in this list.
    (96.,'SAFE_HOLD',False,'BLOCKED'),
    # Include a tuple containing 96.0, the text 'PERMITTED', False, the text 'READY' in this list.
    (96.,'PERMITTED',False,'READY'),
    # Include a tuple containing 96.0, the text 'SAFE_HOLD', True, the text 'NEGOTIATING' in this list.
    (96.,'SAFE_HOLD',True,'NEGOTIATING'),
    # Include a tuple containing 20.0, the text 'NATIVE_FOLLOWING', False, the text 'APPROACHING' in this list.
    (20.,'NATIVE_FOLLOWING',False,'APPROACHING')])
# Check colors preserve input permission using the setup, calls, and assertions below.
# Input position: the supplied position.
# Input permission: the supplied permission.
# Input pending: the supplied pending.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
def test_colors_preserve_input_permission(position,permission,pending,expected):
    # Set p to the result of IntersectionPresentation().
    # Set s to the result of physical().
    # Set v to the result of vehicle().
    p=IntersectionPresentation();s=physical(position=position);v=vehicle()
    # Set d to the result of SimpleNamespace().
    # Set before to the result of deepcopy(a tuple containing s, v, d).
    d=SimpleNamespace(permission=permission);before=deepcopy((s,v,d))
    # Set row to the result of p.classify(v, s, d, GEOMETRY).
    row=p.classify(v,s,d,GEOMETRY,pending=pending)
    # Require row at 'display_state' equals expected; otherwise raise AssertionError.
    assert row['display_state']==expected
    # Require a tuple containing s, v, d equals before; otherwise raise AssertionError.
    assert (s,v,d)==before


# Check braking stage latches while speed falls using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_braking_stage_latches_while_speed_falls():
    # Set p to the result of IntersectionPresentation().
    # Set d to the result of SimpleNamespace().
    p=IntersectionPresentation();d=SimpleNamespace(permission='SAFE_HOLD')
    # Require p.classify(vehicle(), physical(position=88.0, speed=10.0), d, GEOMETRY) at 'display_state' equals
    # the text 'BLOCKED'; otherwise raise AssertionError.
    assert p.classify(vehicle(),physical(position=88.,speed=10.),d,GEOMETRY)['display_state']=='BLOCKED'
    # Require p.classify(vehicle(), physical(position=89.0, speed=0.1), d, GEOMETRY) at 'display_state' equals the
    # text 'BLOCKED'; otherwise raise AssertionError.
    assert p.classify(vehicle(),physical(position=89.,speed=.1),d,GEOMETRY)['display_state']=='BLOCKED'


# Apply pytest.mark.parametrize('lane,pos,y,clear,visible', [('n', 20.0, 30.0, False, True), ('i', 10.0,... as a
# decorator to configure the following definition.
@pytest.mark.parametrize('lane,pos,y,clear,visible',[
    # Include a tuple containing the text 'n', 20.0, 30.0, False, True in this list.
    ('n',20.,30.,False,True),('i',10.,0.,False,True),
    # Include a tuple containing the text 'o', 4.0, 60.0, False, True in this list.
    ('o',4.,60.,False,True),('o',6.,20.,True,True),
    # Include a tuple containing the text 'o', 60.0, 60.0, True, False in this list.
    ('o',60.,60.,True,False),('o',51.,51.,True,True)])
# Check visibility requires rear clear and whole body exit using the setup, calls, and assertions below.
# Input lane: the supplied lane.
# Input pos: the supplied pos.
# Input y: the supplied y.
# Input clear: the supplied clear.
# Input visible: the supplied visible.
# Output: no explicit value; normal completion returns None.
def test_visibility_requires_rear_clear_and_whole_body_exit(lane,pos,y,clear,visible):
    # Set row to the result of IntersectionPresentation().classify(the result of vehicle(), the result of
    # physical(lane, pos), None, GEOMETRY).
    row=IntersectionPresentation().classify(vehicle(y=y),physical(lane,pos),None,GEOMETRY)
    # Require row at 'intersection_rear_cleared' equals clear; otherwise raise AssertionError.
    assert row['intersection_rear_cleared']==clear
    # Require row at 'presentation_visible' equals visible; otherwise raise AssertionError.
    assert row['presentation_visible']==visible


# Check removed vehicle cannot reappear but new run can reuse id using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_removed_vehicle_cannot_reappear_but_new_run_can_reuse_id():
    # Set p to the result of IntersectionPresentation().
    # Call p.reset_for with the supplied arguments.
    p=IntersectionPresentation();p.reset_for(('first','dense'))
    # Require the negation of p.classify(vehicle(y=60.0), physical('o', 60.0), None, GEOMETRY) at
    # 'presentation_visible'; otherwise raise AssertionError.
    assert not p.classify(vehicle(y=60.),physical('o',60.),None,GEOMETRY)['presentation_visible']
    # Require the negation of p.classify(vehicle(), physical(), None, GEOMETRY) at 'presentation_visible';
    # otherwise raise AssertionError.
    assert not p.classify(vehicle(),physical(),None,GEOMETRY)['presentation_visible']
    # Require p.classify(vehicle(ego='new'), physical(), None, GEOMETRY) at 'presentation_visible'; otherwise
    # raise AssertionError.
    assert p.classify(vehicle(ego='new'),physical(),None,GEOMETRY)['presentation_visible']
    # Call p.reset_for with the supplied arguments.
    p.reset_for(('second','dense'))
    # Require p.classify(vehicle(), physical(), None, GEOMETRY) at 'presentation_visible'; otherwise raise
    # AssertionError.
    assert p.classify(vehicle(),physical(),None,GEOMETRY)['presentation_visible']


# Check unknown geometry does not hide vehicle using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_unknown_geometry_does_not_hide_vehicle():
    # Require IntersectionPresentation().classify(vehicle(y=900), None, None, {}) at 'presentation_visible';
    # otherwise raise AssertionError.
    assert IntersectionPresentation().classify(vehicle(y=900),None,None,{})['presentation_visible']


# Check terminal atomic write retries transient windows lock using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_terminal_atomic_write_retries_transient_windows_lock(tmp_path,monkeypatch):
    # Import json for use in this module.
    import json
    # Import Path from pathlib for the operations below.
    from pathlib import Path
    # Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
    from runtime_simulation.browser_state import BrowserStatePublisher
    # Set replace to Path.replace.
    # Set attempts to an empty list.
    replace=Path.replace;attempts=[]
    # Transient using the inputs and processing steps below.
    # Input path: the path or path object supplied by the caller.
    # Input target: the supplied target.
    # Output: the result of replace(path, target).
    # Processing: select branches using the stated conditions.
    def transient(path,target):
        # Append path to attempts.
        attempts.append(path)
        # Run this branch when the number of entries in attempts is less than 3.
        # Raise PermissionError with the text 'Reader lock' to stop this execution path.
        if len(attempts)<3:raise PermissionError('Reader lock')
        # Return the result of replace(path, target) to the caller.
        return replace(path,target)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(Path,'replace',transient)
    # Set publisher to the result of BrowserStatePublisher(tmp_path joined with the path segment 'live.json', the result of
    # SimpleNamespace()).
    publisher=BrowserStatePublisher(tmp_path/'live.json',SimpleNamespace(vehicle=SimpleNamespace(getIDList=lambda:())))
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=10.,map_state={},running=False,status='FINISHED',
        # Supply completed as 1.
        # Supply scheduled as 1.
        # Supply force as True.
        completed=1,scheduled=1,force=True)
    # Require the number of entries in attempts equals 3; otherwise raise AssertionError.
    assert len(attempts)==3
    # Require json.loads((tmp_path / 'live.json').read_text()) at 'status' equals the text 'FINISHED'; otherwise
    # raise AssertionError.
    assert json.loads((tmp_path/'live.json').read_text())['status']=='FINISHED'


# Apply pytest.mark.parametrize('manoeuvre', ['LEFT', 'RIGHT', 'STRAIGHT']) as a decorator to configure the
# following definition.
@pytest.mark.parametrize('manoeuvre',['LEFT','RIGHT','STRAIGHT'])
# Apply pytest.mark.parametrize('approach', ['N', 'E', 'S', 'W']) as a decorator to configure the following
# definition.
@pytest.mark.parametrize('approach',['N','E','S','W'])
# Check every legal movement uses its actual lane boundary using the setup, calls, and assertions below.
# Input approach: the supplied approach.
# Input manoeuvre: the supplied manoeuvre.
# Output: no explicit value; normal completion returns None.
def test_every_legal_movement_uses_its_actual_lane_boundary(approach,manoeuvre):
    # Import MapPathManager from conflict.map_path_manager for the operations below.
    from conflict.map_path_manager import MapPathManager
    # Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
    from runtime_simulation.browser_state import BrowserStatePublisher
    # Set paths to the result of MapPathManager().
    # Set geometry to the result of BrowserStatePublisher.map_snapshot(paths).
    paths=MapPathManager();geometry=BrowserStatePublisher.map_snapshot(paths)
    # Set path to paths.paths at f'{approach}_IN_0_{manoeuvre}'.
    path=paths.paths[f'{approach}_IN_0_{manoeuvre}']
    # Set lane to the result of paths.network.getLane(path.incoming_lane_id).
    lane=paths.network.getLane(path.incoming_lane_id)
    # Set s to the result of physical().
    # Update s with the supplied entries.
    s=physical();s.update(lane_id=path.incoming_lane_id,lane_length=lane.getLength(),
                          # Supply lane_position as the result of lane.getLength() minus 80.0.
                          lane_position=lane.getLength()-80.)
    # Set p to the result of IntersectionPresentation().
    # Set held to the result of SimpleNamespace().
    p=IntersectionPresentation();held=SimpleNamespace(permission='SAFE_HOLD')
    # Require p.classify(vehicle(), s, held, geometry) at 'display_state' equals the text 'APPROACHING'; otherwise
    # raise AssertionError.
    assert p.classify(vehicle(),s,held,geometry)['display_state']=='APPROACHING'
    # Set s['lane_position'] to the result of lane.getLength() minus 2.0.
    s['lane_position']=lane.getLength()-2.
    # Require p.classify(vehicle(), s, held, geometry) at 'display_state' equals the text 'BLOCKED'; otherwise
    # raise AssertionError.
    assert p.classify(vehicle(),s,held,geometry)['display_state']=='BLOCKED'
    # Update s with the supplied entries.
    s.update(lane_id=path.internal_lane_ids[0],lane_position=1.)
    # Require p.classify(vehicle(), s, held, geometry) at 'presentation_visible'; otherwise raise AssertionError.
    assert p.classify(vehicle(),s,held,geometry)['presentation_visible']
    # Update s with the supplied entries.
    s.update(lane_id=path.outgoing_lane_id,lane_position=4.)
    # Require the negation of p.classify(vehicle(), s, held, geometry) at 'intersection_rear_cleared'; otherwise
    # raise AssertionError.
    assert not p.classify(vehicle(),s,held,geometry)['intersection_rear_cleared']


# Check publisher keeps science after display exit using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_publisher_keeps_science_after_display_exit(tmp_path):
    # Import json for use in this module.
    import json
    # Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
    from runtime_simulation.browser_state import BrowserStatePublisher
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getIDList=lambda:('ego',),getPosition=lambda _:(0.,60.),
        # Declare _, _, _, _ as input parameters.
        getAngle=lambda _:0.,getLength=lambda _:5.,getWidth=lambda _:2.,getSpeed=lambda _:10.)
    # Set publisher to the result of BrowserStatePublisher(tmp_path joined with the path segment 'live.json', the result of
    # SimpleNamespace()).
    publisher=BrowserStatePublisher(tmp_path/'live.json',SimpleNamespace(vehicle=api))
    # Set s to the result of physical(the text 'o', 60.0).
    # Update s with the supplied entries.
    s=physical('o',60.);s.update(position=(0.,60.),angle_degrees=0.,width=2.)
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=1.,map_state=GEOMETRY,running=True,status='EXECUTING',
        # Store s under 'ego'.
        scientific_states={'ego':s},completed=0,scheduled=1,run_id='one',force=True)
    # Set row to the decoded data produced by json.loads from the text read from (tmp_path / 'live.json').
    row=json.loads((tmp_path/'live.json').read_text())
    # Require the negation of row at 'vehicles' and row at 'active_sumo_vehicles' equals 1; otherwise raise
    # AssertionError.
    assert not row['vehicles'] and row['active_sumo_vehicles']==1
    # Require the number of entries in row at 'scientific_vehicles' equals 1 and row at 'completed' equals 0;
    # otherwise raise AssertionError.
    assert len(row['scientific_vehicles'])==1 and row['completed']==0
    # Require the negation of row at 'completed_vehicles'; otherwise raise AssertionError.
    assert not row['completed_vehicles']
    # Require publisher.presentation_vehicle_history()['final_snapshots'][0] at 'id' equals the text 'ego';
    # otherwise raise AssertionError.
    assert publisher.presentation_vehicle_history()['final_snapshots'][0]['id']=='ego'
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=2.,map_state=GEOMETRY,running=False,status='INCOMPLETE',
        # Supply completed as 0.
        # Supply scheduled as 1.
        # Supply force as True.
        completed=0,scheduled=1,force=True)
    # Set final to the decoded data produced by json.loads from the text read from (tmp_path / 'live.json').
    final=json.loads((tmp_path/'live.json').read_text())
    # Require final at 'run_id' equals the text 'one'; otherwise raise AssertionError.
    assert final['run_id']=='one'
    # Require final at 'intersection_cleared_vehicle_ids' equals a list containing the text 'ego'; otherwise raise
    # AssertionError.
    assert final['intersection_cleared_vehicle_ids']==['ego']
    # Require the negation of final at 'vehicles'; otherwise raise AssertionError.
    assert not final['vehicles']
    # Require publisher.presentation_vehicle_history()['final_snapshots'][0] at 'id' equals the text 'ego';
    # otherwise raise AssertionError.
    assert publisher.presentation_vehicle_history()['final_snapshots'][0]['id']=='ego'
