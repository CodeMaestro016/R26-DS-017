"""Native request withdrawal keeps the safety caps and permission boundary."""
from types import SimpleNamespace
from negotiation_execution.native_hold import NativeJunctionHold


def test_native_stop_is_retained_until_explicit_current_permission():
    calls=[]
    api=SimpleNamespace(getLaneIndex=lambda _:0,
                        setStop=lambda *a,**kw:calls.append((a,kw)))
    paths=SimpleNamespace(paths={'N':SimpleNamespace(incoming_lane_id='n_in_0')})
    context=SimpleNamespace(ego_id='N1',movement_path_id='N',
        ego_state=dict(lane_id='n_in_0',road_id='n_in',lane_length=292.8))
    held=SimpleNamespace(permission='SAFE_HOLD',blocked_zones=(('JUNCTION_ENTRY',10,'E1'),))
    adapter=NativeJunctionHold()
    assert adapter.synchronize(context,held,paths,api)=='NATIVE_HOLD_INSTALLED'
    assert calls[0][1]['pos'] < 292.8
    for _ in range(20):
        assert adapter.synchronize(context,held,paths,api) is None
    assert len(calls)==1
    permitted=SimpleNamespace(permission='PERMITTED',blocked_zones=())
    assert adapter.synchronize(context,permitted,paths,api)=='NATIVE_HOLD_RELEASED_AFTER_PERMISSION'
    assert len(calls)==2 and calls[1][1]['duration']==0
    assert calls[0][0]==calls[1][0] and calls[0][1]['pos']==calls[1][1]['pos']
    assert adapter.stop is None


def test_native_hold_is_never_inserted_inside_a_junction():
    paths=SimpleNamespace(paths={'N':SimpleNamespace(incoming_lane_id='n_in_0')})
    context=SimpleNamespace(ego_id='N1',movement_path_id='N',ego_state={'lane_id':':center_1_0'})
    held=SimpleNamespace(permission='SAFE_HOLD',blocked_zones=(('JUNCTION_ENTRY',0,''),))
    assert NativeJunctionHold().synchronize(context,held,paths,SimpleNamespace()) is None
