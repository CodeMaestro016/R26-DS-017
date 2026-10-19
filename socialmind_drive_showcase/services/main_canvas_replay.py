"""Clock and display payload for immutable offline evidence; no runtime writes."""
import bisect
import time
from socialmind_drive_showcase.services.counterfactual_reader import load_evidence

LABEL='OFFLINE UNCOORDINATED FAILURE — REPLAY OF REAL SUMO DATA'

def start(state,now=None):
    frames=load_evidence()['frames']
    first=next(i for i,f in enumerate(frames) if len(f['vehicles'])==6)
    state['mode']='replay';state['index']=first;state['active']=True
    state['started']=time.monotonic() if now is None else now
    state['origin']=frames[first]['simulation_time']

def stop(state):
    state['active']=False;state['index']=None;state['mode']='prepared'

def payload(state,now=None):
    evidence=load_evidence();frames=evidence['frames']
    if state['active']:
        elapsed=(time.monotonic() if now is None else now)-state['started']
        index=bisect.bisect_right([f['simulation_time'] for f in frames],state['origin']+elapsed)-1
        state['index']=min(len(frames)-1,max(state['index'],index))
        if frames[state['index']]['collisions']:state['active']=False
    frame=frames[state['index']]
    involved={v for e in frame['collisions'] for v in [e['collider'],e['victim']]}
    return dict(scenario_id=evidence['scenario_id'],run_id='offline-'+str(state['started']),
        replay_mode=True,running=state['active'],simulation_time=frame['simulation_time'],
        replay_index=state['index'],replay_events=evidence['documented_collision_events'] if involved else [],
        vehicles=[dict(v,collision_involved=v['id'] in involved,
            entry_permission=dict(reason='RECORDED COUNTERFACTUAL; NO PROTECTED ENTRY AUTHORITY'),
            permission_label='COLLISION INVOLVED' if v['id'] in involved else 'RECORDED UNCOORDINATED',
            display_state='APPROACHING') for v in frame['vehicles']],
        collisions=frame['collisions'],collision_count=len(frame['collisions']),
        scheduled=evidence['scheduled'],spawned=evidence['spawned'],completed=evidence['completed'],
        mappo_calls=0,status='COLLISION PAUSED' if involved else 'RECORDED PLAYBACK')
