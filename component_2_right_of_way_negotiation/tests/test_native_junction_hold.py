"""Native request withdrawal keeps the safety caps and permission boundary."""
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import NativeJunctionHold from negotiation_execution.native_hold for the operations below.
from negotiation_execution.native_hold import NativeJunctionHold


# Check native stop is retained until explicit current permission using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_native_stop_is_retained_until_explicit_current_permission():
    # Set calls to an empty list.
    calls=[]
    # Set api to the result of SimpleNamespace().
    api=SimpleNamespace(getLaneIndex=lambda _:0,
                        # Declare a, kw as input parameters.
                        setStop=lambda *a,**kw:calls.append((a,kw)))
    # Set paths to the result of SimpleNamespace().
    paths=SimpleNamespace(paths={'N':SimpleNamespace(incoming_lane_id='n_in_0')})
    # Set context to the result of SimpleNamespace().
    context=SimpleNamespace(ego_id='N1',movement_path_id='N',
        # Supply ego_state as a dictionary built from the supplied values.
        # Supply lane_id as the text 'n_in_0'.
        # Supply road_id as the text 'n_in'.
        # Supply lane_length as 292.8.
        ego_state=dict(lane_id='n_in_0',road_id='n_in',lane_length=292.8))
    # Set held to the result of SimpleNamespace().
    held=SimpleNamespace(permission='SAFE_HOLD',blocked_zones=(('JUNCTION_ENTRY',10,'E1'),))
    # Set adapter to the result of NativeJunctionHold().
    adapter=NativeJunctionHold()
    # Require the result of adapter.synchronize(context, held, paths, api) equals the text
    # 'NATIVE_HOLD_INSTALLED'; otherwise raise AssertionError.
    assert adapter.synchronize(context,held,paths,api)=='NATIVE_HOLD_INSTALLED'
    # Require calls[0][1] at 'pos' is less than 292.8; otherwise raise AssertionError.
    assert calls[0][1]['pos'] < 292.8
    # Iterate over the integer range defined by 20, binding each item to _.
    for _ in range(20):
        # Require the result of adapter.synchronize(context, held, paths, api) is the same object as None;
        # otherwise raise AssertionError.
        assert adapter.synchronize(context,held,paths,api) is None
    # Require the number of entries in calls equals 1; otherwise raise AssertionError.
    assert len(calls)==1
    # Set permitted to the result of SimpleNamespace().
    permitted=SimpleNamespace(permission='PERMITTED',blocked_zones=())
    # Require the result of adapter.synchronize(context, permitted, paths, api) equals the text
    # 'NATIVE_HOLD_RELEASED_AFTER_PERMISSION'; otherwise raise AssertionError.
    assert adapter.synchronize(context,permitted,paths,api)=='NATIVE_HOLD_RELEASED_AFTER_PERMISSION'
    # Require the number of entries in calls equals 2 and calls[1][1] at 'duration' equals 0; otherwise raise
    # AssertionError.
    assert len(calls)==2 and calls[1][1]['duration']==0
    # Require calls[0] at 0 equals calls[1] at 0 and calls[0][1] at 'pos' equals calls[1][1] at 'pos'; otherwise
    # raise AssertionError.
    assert calls[0][0]==calls[1][0] and calls[0][1]['pos']==calls[1][1]['pos']
    # Require adapter.stop is the same object as None; otherwise raise AssertionError.
    assert adapter.stop is None


# Check native hold is never inserted inside a junction using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_native_hold_is_never_inserted_inside_a_junction():
    # Set paths to the result of SimpleNamespace().
    paths=SimpleNamespace(paths={'N':SimpleNamespace(incoming_lane_id='n_in_0')})
    # Set context to the result of SimpleNamespace().
    context=SimpleNamespace(ego_id='N1',movement_path_id='N',ego_state={'lane_id':':center_1_0'})
    # Set held to the result of SimpleNamespace().
    held=SimpleNamespace(permission='SAFE_HOLD',blocked_zones=(('JUNCTION_ENTRY',0,''),))
    # Require the result of NativeJunctionHold().synchronize(context, held, paths, the result of
    # SimpleNamespace()) is the same object as None; otherwise raise AssertionError.
    assert NativeJunctionHold().synchronize(context,held,paths,SimpleNamespace()) is None
