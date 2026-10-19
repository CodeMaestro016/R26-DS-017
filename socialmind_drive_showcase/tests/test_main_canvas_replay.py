from socialmind_drive_showcase.services import main_canvas_replay as replay
from socialmind_drive_showcase.services.counterfactual_reader import load_evidence


def test_main_replay_clock_authentic_positions_and_hold():
    state={};replay.start(state,now=10)
    initial=replay.payload(state,now=10)
    assert len(initial['vehicles'])==6 and initial['simulation_time']==1.6
    final=replay.payload(state,now=100)
    assert final['simulation_time']==24.28 and not state['active']
    assert final['collision_count']==1 and final['mappo_calls']==0
    assert sum(v['collision_involved'] for v in final['vehicles'])==2
    for actual,raw in zip(final['vehicles'],load_evidence()['frames'][-1]['vehicles']):
        for key in ['front_bumper_x','front_bumper_y','angle_degrees','speed_mps','length_m','width_m']:
            assert actual[key]==raw[key]
    assert replay.payload(state,now=1000)['vehicles']==final['vehicles']
    replay.stop(state);assert state['index'] is None and not state['active']
    replay.start(state,now=200);assert replay.payload(state,now=200)['simulation_time']==1.6


def test_scenario_five_default_never_launches_unsafe_runtime(monkeypatch):
    from socialmind_drive_showcase.pages import component2_live_view as page
    monkeypatch.setitem(page.SELECTED_SCENARIO,'id','final_coordination_failure')
    called=[]
    monkeypatch.setattr(page,'_start_main_replay',lambda:called.append('replay'))
    monkeypatch.setattr(page,'_run_protected_scenario',lambda:called.append('protected'))
    page._run_selected_scenario()
    assert called==['replay']
    for scenario in page.VIVA_SCENARIO_IDS:
        if scenario!='final_coordination_failure':
            monkeypatch.setitem(page.SELECTED_SCENARIO,'id',scenario)
            page._run_selected_scenario()
    assert called==['replay']+['protected']*4
