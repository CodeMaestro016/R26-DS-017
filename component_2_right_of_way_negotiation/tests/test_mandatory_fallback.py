"""Legal extension, endpoint agreement, expiry, and retained-cycle regressions."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from negotiation_execution import EgoCoordinationCommitment, ExecutionStateMessage
from negotiation_execution.mandatory_fallback import EndpointEvidence, legal_order


def transcript(edges=(), commitments=()):
    members = ("E02", "N02", "S02", "W03")
    epoch = ("real_receipt", 43.6)
    def incident(rows, sender):
        return tuple(EgoCoordinationCommitment(a, b, epoch) for a, b in rows if sender in (a, b))
    rows = tuple(EndpointEvidence(a, 43.6, epoch, members, incident(commitments, a),
        incident(edges, a), tuple(b for b in members if b != a), True,
        3.04 if a == "W03" else 1.56) for a in members)
    physics = tuple(ExecutionStateMessage(a, a, {}, 43.6, r.arrival,
        coordination_epoch=epoch) for a, r in zip(members, rows))
    paths = SimpleNamespace(paths={a: SimpleNamespace(path_id=a, manoeuvre="STRAIGHT") for a in members},
        approach_relation=lambda a,b: "PERPENDICULAR")
    return rows, physics, paths, epoch


def test_mixed_cycle_gets_same_legal_extension_at_every_ego():
    rows, physics, paths, epoch = transcript((("E02", "W03"), ("N02", "S02")))
    orders = [legal_order(r.sender_id, 43.6, epoch, rows, physics, paths) for r in rows]
    assert all(error is None for order, error in orders)
    assert len({order for order, error in orders}) == 1
    order = orders[0][0]
    assert order.index("W03") < order.index("E02")
    assert order.index("S02") < order.index("N02")
    assert order == ("S02", "N02", "W03", "E02")


def test_nonwaived_commitment_is_preserved():
    rows, physics, paths, epoch = transcript((("E02", "W03"),), (("S02", "E02"),))
    order, error = legal_order("S02", 43.6, epoch, rows, physics, paths)
    assert error is None and order.index("W03") < order.index("E02") < order.index("S02")


@pytest.mark.parametrize("edges,kept", [
    ((("E02", "W03"), ("W03", "E02")), ()),
    ((("E02", "W03"),), (("W03", "E02"),)),
])
def test_genuine_mandatory_or_nonwaived_cycle_stays_held(edges, kept):
    rows, physics, paths, epoch = transcript(edges, kept)
    order, error = legal_order("E02", 43.6, epoch, rows, physics, paths)
    assert order is None and error == "RETAINED_MANDATORY_OR_COMMITMENT_CYCLE"


@pytest.mark.parametrize("fault", ["missing", "stale", "no_mappo", "wrong_epoch", "asymmetric", "duplicate", "physics"])
def test_invalid_endpoint_evidence_never_authorizes(fault):
    rows, physics, paths, epoch = transcript((("E02", "W03"),))
    if fault == "missing": rows = rows[:-1]
    elif fault == "duplicate": rows += (rows[0],)
    elif fault == "stale": rows = (replace(rows[0], timestamp=40),) + rows[1:]
    elif fault == "no_mappo": rows = (replace(rows[0], mappo_receipt=False),) + rows[1:]
    elif fault == "wrong_epoch": rows = (replace(rows[0], epoch=("old",)),) + rows[1:]
    elif fault == "asymmetric": rows = (replace(rows[0], mandatory=()),) + rows[1:]
    elif fault == "physics": physics = (replace(physics[0], timestamp=40),) + physics[1:]
    order, error = legal_order("E02", 43.6, epoch, rows, physics, paths)
    assert order is None and error


def test_four_independent_controllers_have_compatible_permissions():
    from negotiation_execution import EgoExecutionContext, DecentralizedEgoExecutionController
    rows, physics, paths, epoch = transcript((("E02", "W03"), ("N02", "S02")))
    def state(a):
        return dict(progress=-20, lane_id=a+'_in', lane_position=10,
                    length=5, width=1.8, speed=0)
    for a, path in paths.paths.items():
        path.incoming_lane_id=a+'_in'; path.outgoing_lane_id=a+'_out'
    paths.resolve_front_bumper_path_progress=lambda s,p:(s['progress'],None,None)
    zones=SimpleNamespace(zone_record=lambda *a:dict(zone_id='CZ',
        first_path_distance_interval=(0,10),second_path_distance_interval=(0,10)))
    physics=tuple(replace(m,state=state(m.sender_id)) for m in physics)
    decisions=[]
    for row in rows:
        own=next(m for m in physics if m.sender_id==row.sender_id)
        context=EgoExecutionContext(row.sender_id,state(row.sender_id),row.sender_id,43.6,
            row.commitments,tuple(m for m in physics if m.sender_id!=row.sender_id),
            True,43.6,strict_admission=True,coordination_epoch=epoch,mappo_receipt=True,
            fallback_peer_ids=row.eligible_peers,mandatory_commitments=row.mandatory,
            queue_arrival_seconds=row.arrival,fallback_endpoint_evidence=rows,
            own_execution_message=own,mandatory_aware_fallback=True)
        decision=DecentralizedEgoExecutionController(paths,zones).decide(context)
        decisions.append(decision)
    assert [d.ego_id for d in decisions if d.permission=='PERMITTED']==['S02']
    assert all(d.permission=='BLOCKED_BY_PRECEDENCE' for d in decisions if d.ego_id!='S02')
