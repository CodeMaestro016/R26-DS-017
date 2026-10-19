"""Physical speed is separate from entry permission and event history."""
from types import SimpleNamespace
from runtime_simulation.vehicle_display_contract import explain_decision,explain_mappo


def test_red_vehicle_can_legally_approach_its_stopping_boundary():
    d=SimpleNamespace(permission='BLOCKED_BY_PRECEDENCE',reason='UNRESOLVED_LOCAL_ZONE_OBLIGATION',
        blocked_zones=(('JUNCTION_ENTRY',25.,'peer'),),shield_rejection_reason=None,
        fallback_pairs=(),requested_speed_mps=8.)
    row=explain_decision(d,8.4,10.)
    assert row['entry_permission']['authorized'] is False
    assert row['motion_state']=='MOVING'
    assert row['permission_label']=='ENTRY HELD / APPROACHING STOP'
    assert row['entry_permission']['blocking_vehicle_ids']==('peer',)
    assert row['speed_command']['applies_to_next_step_at']>row['state_timestamp']
    assert row['speed_command']['observed_speed_mps']==8.4


def test_missing_local_actor_factor_does_not_mean_no_negotiation_required():
    row=explain_mappo('NEGOTIATION_REQUIRED_REGULATORY_CYCLE',True,10.,12.,())
    assert row['status']=='DECISION_APPLIED'
    assert row['local_actor_action_count']==0
    assert row['current_receipt']
    assert explain_mappo('COMMUNICATED_PRECEDENCE_DISAGREEMENT',False,None,12.,())['status']=='BLOCKED'
    assert explain_mappo('REGULATORY_ORDER_RESOLVED',False,None,12.,())['status']=='NOT_REQUIRED'


def test_expired_agreement_actions_are_not_exposed_as_current():
    old=({'selected_action':'RELINQUISH_CLAIM'},)
    row=explain_mappo('NO_ACTIVE_CONFLICT',False,10.,30.,old)
    assert row['status']=='DECISION_EXPIRED'
    assert row['actions']==()
    assert row['event_age_seconds']==20.


def test_terminal_frame_keeps_current_physics_and_dates_previous_permission(tmp_path):
    import json
    from runtime_simulation.browser_state import BrowserStatePublisher
    measured={'x':1.,'speed':8.4}
    api=SimpleNamespace(getIDList=lambda:('ego',),getPosition=lambda _:(measured['x'],2.),
        getAngle=lambda _:90.,getLength=lambda _:5.,getWidth=lambda _:1.8,getSpeed=lambda _:measured['speed'])
    d=SimpleNamespace(ego_id='ego',permission='SAFE_HOLD',reason='MISSING_OR_STALE_LOCAL_COORDINATION',
        blocked_zones=(('JUNCTION_ENTRY',20.,''),),shield_rejection_reason=None,fallback_pairs=(),requested_speed_mps=8.)
    publisher=BrowserStatePublisher(tmp_path/'frame.json',SimpleNamespace(vehicle=api))
    publisher.publish(simulation_time=1.,map_state={},running=True,status='EXECUTING',
        participants=('ego',),blocked=('ego',),mappo_invocation='AUTHORIZED',execution_decisions=(d,),force=True)
    measured.update(x=2.,speed=.8)
    publisher.publish(simulation_time=2.,map_state={},running=False,status='INCOMPLETE',force=True)
    row=json.loads((tmp_path/'frame.json').read_text())['vehicles'][0]
    assert row['front_bumper_x']==2. and row['speed_mps']==.8
    assert row['entry_permission']['timestamp']==1. and row['state_timestamp']==2.
    assert row['permission_evidence_current'] is False
    assert row['negotiation']['status']=='DECISION_EXPIRED'
    assert row['display_state']=='BLOCKED'
    assert row['permission_label'].startswith('LAST REPORTED:')


def test_run_inference_counter_is_not_a_truncated_timeline_count(tmp_path):
    import json
    from runtime_simulation.browser_state import BrowserStatePublisher
    publisher=BrowserStatePublisher(tmp_path/'frame.json',SimpleNamespace(vehicle=SimpleNamespace(getIDList=lambda:())))
    publisher.publish(simulation_time=1,map_state={},running=True,status='EXECUTING',
        events=({'timestamp':1,'mappo_invocation':'AUTHORIZED'},),run_metrics={'mappo_decision_epochs':1},force=True)
    publisher.publish(simulation_time=10,map_state={},running=True,status='REGULATORY_ORDER_RESOLVED',
        events=(),run_metrics={'mappo_decision_epochs':5},force=True)
    payload=json.loads((tmp_path/'frame.json').read_text())
    assert payload['run_negotiation_summary']['mappo_authorized_events']==5
    assert payload['last_mappo_event']['timestamp']==1
