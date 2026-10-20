"""Approved protocol: real map premises and fail-closed communication."""
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import copy for use in this module.
import copy

# Import pytest for use in this module.
import pytest
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import MovementDeclarationBus from negotiation_learning.movement_declarations for the operations below.
from negotiation_learning.movement_declarations import MovementDeclarationBus
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine


# Apply pytest.fixture as a decorator to configure the following definition.
@pytest.fixture
# Pair using the inputs and processing steps below.
# Output: a tuple containing paths, bus, first, second, graph.
# Processing: iterate over the relevant records.
def pair():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set bus to the result of MovementDeclarationBus(paths).
    bus = MovementDeclarationBus(paths)
    # Set n to a dictionary containing lane_id, self_planned_manoeuvre.
    n = {'lane_id':'n_in_0','self_planned_manoeuvre':'STRAIGHT'}
    # Set s to a dictionary containing lane_id, self_planned_manoeuvre.
    s = {'lane_id':'s_in_0','self_planned_manoeuvre':'RIGHT'}
    # Set first to the result of SimpleNamespace().
    first = SimpleNamespace(ego_id='N',tracks={'N':n,'S':dict(s)})
    # Set second to the result of SimpleNamespace().
    second = SimpleNamespace(ego_id='S',tracks={'S':s,'N':dict(n)})
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(1.0)
    # Iterate over a list containing first, second, binding each item to own.
    # Call bus.publish with the supplied arguments.
    for own in [first,second]:bus.publish(own.ego_id,bus.author(own,1.0))
    # Set graph to a dictionary containing ego_id, ego_path_id, edges.
    graph = {'ego_id':'N','ego_path_id':'N_IN_0_STRAIGHT','edges':({
        # Store the text 'S' under 'target_track_id'.
        # Store a dictionary containing LEFT under 'spatially_conflicting_candidate_paths'.
        # Store the text 'S_IN_0_LEFT' under 'LEFT'.
        'target_track_id':'S', 'spatially_conflicting_candidate_paths':{'LEFT':'S_IN_0_LEFT'},
        # Store a dictionary containing LEFT, RIGHT, STRAIGHT under 'target_candidate_paths'.
        # Store the text 'S_IN_0_LEFT' under 'LEFT'.
        # Store the text 'S_IN_0_RIGHT' under 'RIGHT'.
        # Store the text 'S_IN_0_STRAIGHT' under 'STRAIGHT'.
        'target_candidate_paths':{'LEFT':'S_IN_0_LEFT','RIGHT':'S_IN_0_RIGHT','STRAIGHT':'S_IN_0_STRAIGHT'}},)}
    # Return a tuple containing paths, bus, first, second, graph to the caller.
    return paths,bus,first,second,graph


# Check unknown conditional left claim is absent for declared nonconflicting right using the setup, calls, and
# assertions below.
# Input pair: the supplied pair.
# Output: no explicit value; normal completion returns None.
def test_unknown_conditional_left_claim_is_absent_for_declared_nonconflicting_right(pair):
    # Set (paths, bus, n, s, graph) to pair.
    paths,bus,n,s,graph=pair
    # Set original to the result of copy.deepcopy(graph).
    original=copy.deepcopy(graph)
    # Set reconciled to the result of bus.reconcile(n, graph, 1).
    reconciled=bus.reconcile(n,graph,1)
    # Require reconciled at 'edges' equals an empty tuple; otherwise raise AssertionError.
    assert reconciled['edges']==()
    # Require the negation of reconciled at 'movement_declaration_errors'; otherwise raise AssertionError.
    assert not reconciled['movement_declaration_errors']
    # Require graph equals original; otherwise raise AssertionError.
    assert graph==original
    # Require n.tracks['S'] at 'self_planned_manoeuvre' equals the text 'RIGHT'; otherwise raise AssertionError.
    assert n.tracks['S']['self_planned_manoeuvre']=='RIGHT'  # receiver does not consume this field


# Check declared physical left conflict retains mandatory rule using the setup, calls, and assertions below.
# Input pair: the supplied pair.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_declared_physical_left_conflict_retains_mandatory_rule(pair):
    # Set (paths, bus, n, s, graph) to pair.
    paths,bus,n,s,graph=pair
    # Set s.tracks['S']['self_planned_manoeuvre'] to the text 'LEFT'.
    s.tracks['S']['self_planned_manoeuvre']='LEFT'
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(2)
    # Iterate over a list containing n, s, binding each item to own.
    # Call bus.publish with the supplied arguments.
    for own in [n,s]:bus.publish(own.ego_id,bus.author(own,2))
    # Set reconciled to the result of bus.reconcile(n, graph, 2).
    reconciled=bus.reconcile(n,graph,2)
    # Require reconciled['edges'][0] at 'conditional_candidate_paths' equals a dictionary containing LEFT;
    # otherwise raise AssertionError.
    assert reconciled['edges'][0]['conditional_candidate_paths']=={'LEFT':'S_IN_0_LEFT'}
    # Set n.get_current_conflict_graph to a callback that returns reconciled.
    n.get_current_conflict_graph=lambda:reconciled
    # Set rule to TrafficRuleEngine(paths, runtime_v2=True).assess_ldm(n, 2)['assessments'] at 0.
    rule=TrafficRuleEngine(paths,runtime_v2=True).assess_ldm(n,2)['assessments'][0]
    # Require rule at 'regulatory_status' equals the text 'EGO_HAS_PRECEDENCE_UNDER_RULE'; otherwise raise
    # AssertionError.
    assert rule['regulatory_status']=='EGO_HAS_PRECEDENCE_UNDER_RULE'
    # Require rule at 'applicable_rule_ids' equals a tuple containing the text 'DE-STVO-9-3'; otherwise raise
    # AssertionError.
    assert rule['applicable_rule_ids']==('DE-STVO-9-3',)


# Apply 'failure,expected' as a decorator to configure the following definition.
@pytest.mark.parametrize('failure,expected',[
    # Include a tuple containing the text 'missing', the text 'MISSING_MOVEMENT_DECLARATION' in this list.
    ('missing','MISSING_MOVEMENT_DECLARATION'),
    # Include a tuple containing the text 'stale', the text 'STALE_MOVEMENT_DECLARATION' in this list.
    ('stale','STALE_MOVEMENT_DECLARATION'),
    # Include a tuple containing the text 'contradictory', the text 'CONTRADICTORY_MOVEMENT_DECLARATIONS' in this
    # list.
    ('contradictory','CONTRADICTORY_MOVEMENT_DECLARATIONS'),
    # Include a tuple containing the text 'invalid', the text 'INVALID_MOVEMENT_DECLARATION' in this list.
    ('invalid','INVALID_MOVEMENT_DECLARATION'),
    # Include a tuple containing the text 'untrusted', the text 'UNTRUSTED_MOVEMENT_DECLARATION' in this list.
    ('untrusted','UNTRUSTED_MOVEMENT_DECLARATION'),
    # Include a tuple containing the text 'lane', the text 'DECLARATION_LANE_MISMATCH' in this list.
    ('lane','DECLARATION_LANE_MISMATCH'),
])
# Check communication failure preserves unknown conflict and marks incomplete using the setup, calls, and
# assertions below.
# Input pair: the supplied pair.
# Input failure: the supplied failure.
# Input expected: the supplied expected.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_communication_failure_preserves_unknown_conflict_and_marks_incomplete(pair,failure,expected):
    # Set (paths, bus, n, s, graph) to pair.
    paths,bus,n,s,graph=pair
    # Set message to bus.messages['S'] at 0.
    message=bus.messages['S'][0]
    # Run this branch when failure equals the text 'missing'.
    # Remove the requested entry from bus.messages.
    if failure=='missing':bus.messages.pop('S')
    # Run this branch when failure equals the text 'stale'.
    # Set bus.messages['S'] to a list containing the result of replace(message).
    elif failure=='stale':bus.messages['S']=[replace(message,timestamp=0)]
    # Run this branch when failure equals the text 'contradictory'.
    # Append the result of replace(message) to bus.messages['S'].
    elif failure=='contradictory':bus.messages['S'].append(replace(message,manoeuvre='LEFT'))
    # Run this branch when failure equals the text 'invalid'.
    # Set bus.messages['S'] to a list containing the result of replace(message).
    elif failure=='invalid':bus.messages['S']=[replace(message,manoeuvre='REVERSE')]
    # Run this branch when failure equals the text 'untrusted'.
    # Set bus.messages['S'] to a list containing the result of replace(message).
    elif failure=='untrusted':bus.messages['S']=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
    # Run this branch when failure equals the text 'lane'.
    # Set n.tracks['S']['lane_id'] to the text 'e_in_0'.
    elif failure=='lane':n.tracks['S']['lane_id']='e_in_0'
    # Set result to the result of bus.reconcile(n, graph, 1).
    result=bus.reconcile(n,graph,1)
    # Require result at 'edges'; otherwise raise AssertionError.
    assert result['edges']
    # Require result['edges'][0] at 'claim_premise_status' equals the text 'UNRESOLVED_DECLARATION'; otherwise
    # raise AssertionError.
    assert result['edges'][0]['claim_premise_status']=='UNRESOLVED_DECLARATION'
    # Require expected belongs to a set of e at 'reason' for e in result at 'movement_declaration_errors';
    # otherwise raise AssertionError.
    assert expected in {e['reason'] for e in result['movement_declaration_errors']}


# Check sender binding and navigation payload cannot be forged using the setup, calls, and assertions below.
# Input pair: the supplied pair.
# Output: no explicit value; normal completion returns None.
def test_sender_binding_and_navigation_payload_cannot_be_forged(pair):
    # Set (paths, bus, n, s, graph) to pair.
    paths,bus,n,s,graph=pair
    # Set message to bus.messages['S'] at 0.
    message=bus.messages['S'][0]
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    # Call bus.publish with the supplied arguments.
    with pytest.raises(ValueError,match='SENDER_MISMATCH'):bus.publish('N',message)
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError,match='NOT_SENDER_AUTHORED'):
        # Call bus.publish with the supplied arguments.
        bus.publish('S',replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT'))


# Check message expires each step and target private route is irrelevant using the setup, calls, and assertions
# below.
# Input pair: the supplied pair.
# Output: no explicit value; normal completion returns None.
def test_message_expires_each_step_and_target_private_route_is_irrelevant(pair):
    # Set (paths, bus, n, s, graph) to pair.
    paths,bus,n,s,graph=pair
    # Set n.tracks['S']['route_id'] to the text 'secret_wrong_left'.
    n.tracks['S']['route_id']='secret_wrong_left'
    # Set n.tracks['S']['self_planned_manoeuvre'] to the text 'LEFT'.
    n.tracks['S']['self_planned_manoeuvre']='LEFT'
    # Require the negation of bus.reconcile(n, graph, 1) at 'edges'; otherwise raise AssertionError.
    assert not bus.reconcile(n,graph,1)['edges']
    # Call bus.begin_step with the supplied arguments.
    bus.begin_step(2)
    # Require bus.reconcile(n, graph, 2) at 'movement_declaration_errors'; otherwise raise AssertionError.
    assert bus.reconcile(n,graph,2)['movement_declaration_errors']


# Check native release can accelerate after previous unconstrained speed was zero using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_native_release_can_accelerate_after_previous_unconstrained_speed_was_zero():
    # Import DecentralizedEgoExecutionController, EgoExecutionContext, EgoExecutionDecision from
    # negotiation_execution for the operations below.
    from negotiation_execution import DecentralizedEgoExecutionController, EgoExecutionContext, EgoExecutionDecision
    # Set path to the result of SimpleNamespace().
    path=SimpleNamespace(incoming_lane_id='n_in_0')
    # Set paths to the result of SimpleNamespace().
    paths=SimpleNamespace(paths={'N':path},resolve_front_bumper_path_progress=lambda *a:(-.001,None,None))
    # Set controller to the result of DecentralizedEgoExecutionController(paths, None).
    controller=DecentralizedEgoExecutionController(paths,None)
    # Set own to the result of EgoExecutionContext(the text 'N', a dictionary containing speed,
    # max_acceleration_mps2,...).
    own=EgoExecutionContext('N',{'speed':0.,'max_acceleration_mps2':2.,
        # Store 4.5 under 'comfortable_deceleration_mps2'.
        'comfortable_deceleration_mps2':4.5},'N',1.,strict_admission=True)
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getSpeedMode=lambda _:31,getSpeedWithoutTraCI=lambda _:0.,getActionStepLength=lambda _:.04)
    # Call controller.constrain with the supplied arguments.
    controller.constrain(own,EgoExecutionDecision('N','PERMITTED','LOCALLY_SAFE'),api,.04)
    # Require controller.admission_state equals the text 'COMMITTED_TO_ENTER'; otherwise raise AssertionError.
    assert controller.admission_state=='COMMITTED_TO_ENTER'
