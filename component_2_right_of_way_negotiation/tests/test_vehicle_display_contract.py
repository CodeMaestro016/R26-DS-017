"""Physical speed is separate from entry permission and event history."""
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import explain_decision, explain_mappo from runtime_simulation.vehicle_display_contract for the operations
# below.
from runtime_simulation.vehicle_display_contract import explain_decision,explain_mappo


# Check red vehicle can legally approach its stopping boundary using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_red_vehicle_can_legally_approach_its_stopping_boundary():
    # Set d to the result of SimpleNamespace().
    d=SimpleNamespace(permission='BLOCKED_BY_PRECEDENCE',reason='UNRESOLVED_LOCAL_ZONE_OBLIGATION',
        # Supply blocked_zones as a tuple containing a tuple containing the text 'JUNCTION_ENTRY', 25.0, the text
        # 'peer'.
        # Supply shield_rejection_reason as None.
        blocked_zones=(('JUNCTION_ENTRY',25.,'peer'),),shield_rejection_reason=None,
        # Supply fallback_pairs as an empty tuple.
        # Supply requested_speed_mps as 8.0.
        fallback_pairs=(),requested_speed_mps=8.)
    # Set row to the result of explain_decision(d, 8.4, 10.0).
    row=explain_decision(d,8.4,10.)
    # Require row['entry_permission'] at 'authorized' is the same object as False; otherwise raise AssertionError.
    assert row['entry_permission']['authorized'] is False
    # Require row at 'motion_state' equals the text 'MOVING'; otherwise raise AssertionError.
    assert row['motion_state']=='MOVING'
    # Require row at 'permission_label' equals the text 'ENTRY HELD / APPROACHING STOP'; otherwise raise
    # AssertionError.
    assert row['permission_label']=='ENTRY HELD / APPROACHING STOP'
    # Require row['entry_permission'] at 'blocking_vehicle_ids' equals a tuple containing the text 'peer';
    # otherwise raise AssertionError.
    assert row['entry_permission']['blocking_vehicle_ids']==('peer',)
    # Require row['speed_command'] at 'applies_to_next_step_at' is greater than row at 'state_timestamp';
    # otherwise raise AssertionError.
    assert row['speed_command']['applies_to_next_step_at']>row['state_timestamp']
    # Require row['speed_command'] at 'observed_speed_mps' equals 8.4; otherwise raise AssertionError.
    assert row['speed_command']['observed_speed_mps']==8.4


# Check missing local actor factor does not mean no negotiation required using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_missing_local_actor_factor_does_not_mean_no_negotiation_required():
    # Set row to the result of explain_mappo(the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE', True, 10.0, 12.0,
    # an empty tuple).
    row=explain_mappo('NEGOTIATION_REQUIRED_REGULATORY_CYCLE',True,10.,12.,())
    # Require row at 'status' equals the text 'DECISION_APPLIED'; otherwise raise AssertionError.
    assert row['status']=='DECISION_APPLIED'
    # Require row at 'local_actor_action_count' equals 0; otherwise raise AssertionError.
    assert row['local_actor_action_count']==0
    # Require row at 'current_receipt'; otherwise raise AssertionError.
    assert row['current_receipt']
    # Require explain_mappo('COMMUNICATED_PRECEDENCE_DISAGREEMENT', False, None, 12.0, ()) at 'status' equals the
    # text 'BLOCKED'; otherwise raise AssertionError.
    assert explain_mappo('COMMUNICATED_PRECEDENCE_DISAGREEMENT',False,None,12.,())['status']=='BLOCKED'
    # Require explain_mappo('REGULATORY_ORDER_RESOLVED', False, None, 12.0, ()) at 'status' equals the text
    # 'NOT_REQUIRED'; otherwise raise AssertionError.
    assert explain_mappo('REGULATORY_ORDER_RESOLVED',False,None,12.,())['status']=='NOT_REQUIRED'


# Check expired agreement actions are not exposed as current using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_expired_agreement_actions_are_not_exposed_as_current():
    # Set old to a tuple containing a dictionary containing selected_action.
    old=({'selected_action':'RELINQUISH_CLAIM'},)
    # Set row to the result of explain_mappo(the text 'NO_ACTIVE_CONFLICT', False, 10.0, 30.0, old).
    row=explain_mappo('NO_ACTIVE_CONFLICT',False,10.,30.,old)
    # Require row at 'status' equals the text 'DECISION_EXPIRED'; otherwise raise AssertionError.
    assert row['status']=='DECISION_EXPIRED'
    # Require row at 'actions' equals an empty tuple; otherwise raise AssertionError.
    assert row['actions']==()
    # Require row at 'event_age_seconds' equals 20.0; otherwise raise AssertionError.
    assert row['event_age_seconds']==20.


# Check terminal frame keeps current physics and dates previous permission using the setup, calls, and assertions
# below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_terminal_frame_keeps_current_physics_and_dates_previous_permission(tmp_path):
    # Import json for use in this module.
    import json
    # Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
    from runtime_simulation.browser_state import BrowserStatePublisher
    # Set measured to a dictionary containing x, speed.
    measured={'x':1.,'speed':8.4}
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getIDList=lambda:('ego',),getPosition=lambda _:(measured['x'],2.),
        # Declare _, _, _, _ as input parameters.
        getAngle=lambda _:90.,getLength=lambda _:5.,getWidth=lambda _:1.8,getSpeed=lambda _:measured['speed'])
    # Set d to the result of SimpleNamespace().
    d=SimpleNamespace(ego_id='ego',permission='SAFE_HOLD',reason='MISSING_OR_STALE_LOCAL_COORDINATION',
        # Supply blocked_zones as a tuple containing a tuple containing the text 'JUNCTION_ENTRY', 20.0, the text
        # ''.
        # Supply shield_rejection_reason as None.
        # Supply fallback_pairs as an empty tuple.
        # Supply requested_speed_mps as 8.0.
        blocked_zones=(('JUNCTION_ENTRY',20.,''),),shield_rejection_reason=None,fallback_pairs=(),requested_speed_mps=8.)
    # Set publisher to the result of BrowserStatePublisher(tmp_path joined with the path segment 'frame.json', the result
    # of SimpleNamespace()).
    publisher=BrowserStatePublisher(tmp_path/'frame.json',SimpleNamespace(vehicle=api))
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=1.,map_state={},running=True,status='EXECUTING',
        # Supply participants as a tuple containing the text 'ego'.
        # Supply blocked as a tuple containing the text 'ego'.
        # Supply mappo_invocation as the text 'AUTHORIZED'.
        # Supply execution_decisions as a tuple containing d.
        # Supply force as True.
        participants=('ego',),blocked=('ego',),mappo_invocation='AUTHORIZED',execution_decisions=(d,),force=True)
    # Update measured with the supplied entries.
    measured.update(x=2.,speed=.8)
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=2.,map_state={},running=False,status='INCOMPLETE',force=True)
    # Set row to json.loads((tmp_path / 'frame.json').read_text())['vehicles'] at 0.
    row=json.loads((tmp_path/'frame.json').read_text())['vehicles'][0]
    # Require row at 'front_bumper_x' equals 2.0 and row at 'speed_mps' equals 0.8; otherwise raise
    # AssertionError.
    assert row['front_bumper_x']==2. and row['speed_mps']==.8
    # Require row['entry_permission'] at 'timestamp' equals 1.0 and row at 'state_timestamp' equals 2.0; otherwise
    # raise AssertionError.
    assert row['entry_permission']['timestamp']==1. and row['state_timestamp']==2.
    # Require row at 'permission_evidence_current' is the same object as False; otherwise raise AssertionError.
    assert row['permission_evidence_current'] is False
    # Require row['negotiation'] at 'status' equals the text 'DECISION_EXPIRED'; otherwise raise AssertionError.
    assert row['negotiation']['status']=='DECISION_EXPIRED'
    # Require row at 'display_state' equals the text 'BLOCKED'; otherwise raise AssertionError.
    assert row['display_state']=='BLOCKED'
    # Require the result of row['permission_label'].startswith(the text 'LAST REPORTED:'); otherwise raise
    # AssertionError.
    assert row['permission_label'].startswith('LAST REPORTED:')


# Check run inference counter is not a truncated timeline count using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_run_inference_counter_is_not_a_truncated_timeline_count(tmp_path):
    # Import json for use in this module.
    import json
    # Import BrowserStatePublisher from runtime_simulation.browser_state for the operations below.
    from runtime_simulation.browser_state import BrowserStatePublisher
    # Set publisher to the result of BrowserStatePublisher(tmp_path joined with the path segment 'frame.json', the result
    # of SimpleNamespace()).
    publisher=BrowserStatePublisher(tmp_path/'frame.json',SimpleNamespace(vehicle=SimpleNamespace(getIDList=lambda:())))
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=1,map_state={},running=True,status='EXECUTING',
        # Store 1 under 'mappo_decision_epochs'.
        # Store 1 under 'timestamp'.
        # Store the text 'AUTHORIZED' under 'mappo_invocation'.
        events=({'timestamp':1,'mappo_invocation':'AUTHORIZED'},),run_metrics={'mappo_decision_epochs':1},force=True)
    # Call publisher.publish with the supplied arguments.
    publisher.publish(simulation_time=10,map_state={},running=True,status='REGULATORY_ORDER_RESOLVED',
        # Store 5 under 'mappo_decision_epochs'.
        events=(),run_metrics={'mappo_decision_epochs':5},force=True)
    # Set payload to the decoded data produced by json.loads from the text read from (tmp_path / 'frame.json').
    payload=json.loads((tmp_path/'frame.json').read_text())
    # Require payload['run_negotiation_summary'] at 'mappo_authorized_events' equals 5; otherwise raise
    # AssertionError.
    assert payload['run_negotiation_summary']['mappo_authorized_events']==5
    # Require payload['last_mappo_event'] at 'timestamp' equals 1; otherwise raise AssertionError.
    assert payload['last_mappo_event']['timestamp']==1
