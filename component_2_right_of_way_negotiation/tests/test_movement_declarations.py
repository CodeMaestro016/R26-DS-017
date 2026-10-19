"""Approved protocol: real map premises and fail-closed communication."""
from dataclasses import replace
from types import SimpleNamespace
import copy

import pytest
from conflict import MapPathManager
from negotiation_learning.movement_declarations import MovementDeclarationBus
from traffic_rules import TrafficRuleEngine


@pytest.fixture
def pair():
    paths = MapPathManager()
    bus = MovementDeclarationBus(paths)
    n = {'lane_id':'n_in_0','self_planned_manoeuvre':'STRAIGHT'}
    s = {'lane_id':'s_in_0','self_planned_manoeuvre':'RIGHT'}
    first = SimpleNamespace(ego_id='N',tracks={'N':n,'S':dict(s)})
    second = SimpleNamespace(ego_id='S',tracks={'S':s,'N':dict(n)})
    bus.begin_step(1.0)
    for own in [first,second]:bus.publish(own.ego_id,bus.author(own,1.0))
    graph = {'ego_id':'N','ego_path_id':'N_IN_0_STRAIGHT','edges':({
        'target_track_id':'S', 'spatially_conflicting_candidate_paths':{'LEFT':'S_IN_0_LEFT'},
        'target_candidate_paths':{'LEFT':'S_IN_0_LEFT','RIGHT':'S_IN_0_RIGHT','STRAIGHT':'S_IN_0_STRAIGHT'}},)}
    return paths,bus,first,second,graph


def test_unknown_conditional_left_claim_is_absent_for_declared_nonconflicting_right(pair):
    paths,bus,n,s,graph=pair
    original=copy.deepcopy(graph)
    reconciled=bus.reconcile(n,graph,1)
    assert reconciled['edges']==()
    assert not reconciled['movement_declaration_errors']
    assert graph==original
    assert n.tracks['S']['self_planned_manoeuvre']=='RIGHT'  # receiver does not consume this field


def test_declared_physical_left_conflict_retains_mandatory_rule(pair):
    paths,bus,n,s,graph=pair
    s.tracks['S']['self_planned_manoeuvre']='LEFT'
    bus.begin_step(2)
    for own in [n,s]:bus.publish(own.ego_id,bus.author(own,2))
    reconciled=bus.reconcile(n,graph,2)
    assert reconciled['edges'][0]['conditional_candidate_paths']=={'LEFT':'S_IN_0_LEFT'}
    n.get_current_conflict_graph=lambda:reconciled
    rule=TrafficRuleEngine(paths,runtime_v2=True).assess_ldm(n,2)['assessments'][0]
    assert rule['regulatory_status']=='EGO_HAS_PRECEDENCE_UNDER_RULE'
    assert rule['applicable_rule_ids']==('DE-STVO-9-3',)


@pytest.mark.parametrize('failure,expected',[
    ('missing','MISSING_MOVEMENT_DECLARATION'),
    ('stale','STALE_MOVEMENT_DECLARATION'),
    ('contradictory','CONTRADICTORY_MOVEMENT_DECLARATIONS'),
    ('invalid','INVALID_MOVEMENT_DECLARATION'),
    ('untrusted','UNTRUSTED_MOVEMENT_DECLARATION'),
    ('lane','DECLARATION_LANE_MISMATCH'),
])
def test_communication_failure_preserves_unknown_conflict_and_marks_incomplete(pair,failure,expected):
    paths,bus,n,s,graph=pair
    message=bus.messages['S'][0]
    if failure=='missing':bus.messages.pop('S')
    elif failure=='stale':bus.messages['S']=[replace(message,timestamp=0)]
    elif failure=='contradictory':bus.messages['S'].append(replace(message,manoeuvre='LEFT'))
    elif failure=='invalid':bus.messages['S']=[replace(message,manoeuvre='REVERSE')]
    elif failure=='untrusted':bus.messages['S']=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
    elif failure=='lane':n.tracks['S']['lane_id']='e_in_0'
    result=bus.reconcile(n,graph,1)
    assert result['edges']
    assert result['edges'][0]['claim_premise_status']=='UNRESOLVED_DECLARATION'
    assert expected in {e['reason'] for e in result['movement_declaration_errors']}


def test_sender_binding_and_navigation_payload_cannot_be_forged(pair):
    paths,bus,n,s,graph=pair
    message=bus.messages['S'][0]
    with pytest.raises(ValueError,match='SENDER_MISMATCH'):bus.publish('N',message)
    with pytest.raises(ValueError,match='NOT_SENDER_AUTHORED'):
        bus.publish('S',replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT'))


def test_message_expires_each_step_and_target_private_route_is_irrelevant(pair):
    paths,bus,n,s,graph=pair
    n.tracks['S']['route_id']='secret_wrong_left'
    n.tracks['S']['self_planned_manoeuvre']='LEFT'
    assert not bus.reconcile(n,graph,1)['edges']
    bus.begin_step(2)
    assert bus.reconcile(n,graph,2)['movement_declaration_errors']


def test_native_release_can_accelerate_after_previous_unconstrained_speed_was_zero():
    from negotiation_execution import DecentralizedEgoExecutionController, EgoExecutionContext, EgoExecutionDecision
    path=SimpleNamespace(incoming_lane_id='n_in_0')
    paths=SimpleNamespace(paths={'N':path},resolve_front_bumper_path_progress=lambda *a:(-.001,None,None))
    controller=DecentralizedEgoExecutionController(paths,None)
    own=EgoExecutionContext('N',{'speed':0.,'max_acceleration_mps2':2.,
        'comfortable_deceleration_mps2':4.5},'N',1.,strict_admission=True)
    api=SimpleNamespace(getSpeedMode=lambda _:31,getSpeedWithoutTraCI=lambda _:0.,getActionStepLength=lambda _:.04)
    controller.constrain(own,EgoExecutionDecision('N','PERMITTED','LOCALLY_SAFE'),api,.04)
    assert controller.admission_state=='COMMITTED_TO_ENTER'
