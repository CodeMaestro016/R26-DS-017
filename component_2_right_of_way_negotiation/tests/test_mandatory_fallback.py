"""Legal extension, endpoint agreement, expiry, and retained-cycle regressions."""
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import pytest for use in this module.
import pytest
# Import EgoCoordinationCommitment, ExecutionStateMessage from negotiation_execution for the operations below.
from negotiation_execution import EgoCoordinationCommitment, ExecutionStateMessage
# Import EndpointEvidence, legal_order from negotiation_execution.mandatory_fallback for the operations below.
from negotiation_execution.mandatory_fallback import EndpointEvidence, legal_order


# Transcript using the inputs and processing steps below.
# Input edges: the supplied edges.
# Input commitments: the supplied commitments.
# Output: a tuple containing rows, physics, paths, epoch.
def transcript(edges=(), commitments=()):
    # Set members to a tuple containing the text 'E02', the text 'N02', the text 'S02', the text 'W03'.
    members = ("E02", "N02", "S02", "W03")
    # Set epoch to a tuple containing the text 'real_receipt', 43.6.
    epoch = ("real_receipt", 43.6)
    # Incident using the inputs and processing steps below.
    # Input rows: the supplied rows.
    # Input sender: the supplied sender.
    # Output: a tuple built from a lazy sequence of the result of EgoCoordinationCommitment(a, b, epoch) for (a,
    # b) in rows; retain entries satisfying sender belongs to a tuple containing a, b.
    def incident(rows, sender):
        # Return a tuple built from a lazy sequence of the result of EgoCoordinationCommitment(a, b, epoch) for
        # (a, b) in rows; retain entries satisfying sender belongs to a tuple containing a, b to the caller.
        return tuple(EgoCoordinationCommitment(a, b, epoch) for a, b in rows if sender in (a, b))
    # Set rows to a tuple built from a lazy sequence of the result of EndpointEvidence(a, 43.6, epoch, members,
    # the result of incident(commitments, a), the result of incident(edges,...) for a in members.
    rows = tuple(EndpointEvidence(a, 43.6, epoch, members, incident(commitments, a),
        # Supply a tuple built from a lazy sequence of b for b in members; retain entries satisfying b differs
        # from a to EndpointEvidence.
        incident(edges, a), tuple(b for b in members if b != a), True,
        # Supply 3.04 when a equals the text 'W03', otherwise 1.56 to EndpointEvidence.
        3.04 if a == "W03" else 1.56) for a in members)
    # Set physics to a tuple built from a lazy sequence of the result of ExecutionStateMessage(a, a, an empty
    # dictionary, 43.6, r.arrival) for (a, r) in corresponding items paired from members, rows.
    physics = tuple(ExecutionStateMessage(a, a, {}, 43.6, r.arrival,
        # Supply coordination_epoch as epoch.
        coordination_epoch=epoch) for a, r in zip(members, rows))
    # Set paths to the result of SimpleNamespace().
    paths = SimpleNamespace(paths={a: SimpleNamespace(path_id=a, manoeuvre="STRAIGHT") for a in members},
        # Declare a, b as input parameters.
        approach_relation=lambda a,b: "PERPENDICULAR")
    # Return a tuple containing rows, physics, paths, epoch to the caller.
    return rows, physics, paths, epoch


# Check mixed cycle gets same legal extension at every ego using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_mixed_cycle_gets_same_legal_extension_at_every_ego():
    # Set (rows, physics, paths, epoch) to the result of transcript(a tuple containing a tuple containing the text
    # 'E02', the text 'W03', a tuple containing the...).
    rows, physics, paths, epoch = transcript((("E02", "W03"), ("N02", "S02")))
    # Set orders to a list of the result of legal_order(r.sender_id, 43.6, epoch, rows, physics, paths) for r in
    # rows.
    orders = [legal_order(r.sender_id, 43.6, epoch, rows, physics, paths) for r in rows]
    # Require whether every item is true in a lazy sequence of error is the same object as None for (order, error)
    # in orders; otherwise raise AssertionError.
    assert all(error is None for order, error in orders)
    # Require the number of entries in a set of order for (order, error) in orders equals 1; otherwise raise
    # AssertionError.
    assert len({order for order, error in orders}) == 1
    # Set order to orders[0] at 0.
    order = orders[0][0]
    # Require the result of order.index(the text 'W03') is less than the result of order.index(the text 'E02');
    # otherwise raise AssertionError.
    assert order.index("W03") < order.index("E02")
    # Require the result of order.index(the text 'S02') is less than the result of order.index(the text 'N02');
    # otherwise raise AssertionError.
    assert order.index("S02") < order.index("N02")
    # Require order equals a tuple containing the text 'S02', the text 'N02', the text 'W03', the text 'E02';
    # otherwise raise AssertionError.
    assert order == ("S02", "N02", "W03", "E02")


# Check nonwaived commitment is preserved using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_nonwaived_commitment_is_preserved():
    # Set (rows, physics, paths, epoch) to the result of transcript(a tuple containing a tuple containing the text
    # 'E02', the text 'W03', a tuple containing a tuple...).
    rows, physics, paths, epoch = transcript((("E02", "W03"),), (("S02", "E02"),))
    # Set (order, error) to the result of legal_order(the text 'S02', 43.6, epoch, rows, physics, paths).
    order, error = legal_order("S02", 43.6, epoch, rows, physics, paths)
    # Require error is the same object as None and the result of order.index(the text 'W03') is less than the
    # result of order.index(the text 'E02'); is less than the result of order.index(the text 'S02'); otherwise
    # raise AssertionError.
    assert error is None and order.index("W03") < order.index("E02") < order.index("S02")


# Apply 'edges,kept' as a decorator to configure the following definition.
@pytest.mark.parametrize("edges,kept", [
    # Include a tuple containing a tuple containing a tuple containing the text 'E02', the text 'W03', a tuple
    # containing the text 'W03',... in this list.
    ((("E02", "W03"), ("W03", "E02")), ()),
    # Include a tuple containing a tuple containing a tuple containing the text 'E02', the text 'W03', a tuple
    # containing a tuple... in this list.
    ((("E02", "W03"),), (("W03", "E02"),)),
])
# Check genuine mandatory or nonwaived cycle stays held using the setup, calls, and assertions below.
# Input edges: the supplied edges.
# Input kept: the supplied kept.
# Output: no explicit value; normal completion returns None.
def test_genuine_mandatory_or_nonwaived_cycle_stays_held(edges, kept):
    # Set (rows, physics, paths, epoch) to the result of transcript(edges, kept).
    rows, physics, paths, epoch = transcript(edges, kept)
    # Set (order, error) to the result of legal_order(the text 'E02', 43.6, epoch, rows, physics, paths).
    order, error = legal_order("E02", 43.6, epoch, rows, physics, paths)
    # Require order is the same object as None and error equals the text 'RETAINED_MANDATORY_OR_COMMITMENT_CYCLE';
    # otherwise raise AssertionError.
    assert order is None and error == "RETAINED_MANDATORY_OR_COMMITMENT_CYCLE"


# Apply pytest.mark.parametrize('fault', ['missing', 'stale', 'no_mappo', 'wrong_epoch', 'asymmetric',... as a
# decorator to configure the following definition.
@pytest.mark.parametrize("fault", ["missing", "stale", "no_mappo", "wrong_epoch", "asymmetric", "duplicate", "physics"])
# Check invalid endpoint evidence never authorizes using the setup, calls, and assertions below.
# Input fault: the supplied fault.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_invalid_endpoint_evidence_never_authorizes(fault):
    # Set (rows, physics, paths, epoch) to the result of transcript(a tuple containing a tuple containing the text
    # 'E02', the text 'W03').
    rows, physics, paths, epoch = transcript((("E02", "W03"),))
    # Run this branch when fault equals the text 'missing'.
    # Set rows to rows sliced by :-1.
    if fault == "missing": rows = rows[:-1]
    # Run this branch when fault equals the text 'duplicate'.
    # Update rows to its current value plus a tuple containing rows at 0.
    elif fault == "duplicate": rows += (rows[0],)
    # Run this branch when fault equals the text 'stale'.
    # Set rows to a tuple containing the result of replace(rows at 0) plus rows sliced by 1:.
    elif fault == "stale": rows = (replace(rows[0], timestamp=40),) + rows[1:]
    # Run this branch when fault equals the text 'no_mappo'.
    # Set rows to a tuple containing the result of replace(rows at 0) plus rows sliced by 1:.
    elif fault == "no_mappo": rows = (replace(rows[0], mappo_receipt=False),) + rows[1:]
    # Run this branch when fault equals the text 'wrong_epoch'.
    # Set rows to a tuple containing the result of replace(rows at 0) plus rows sliced by 1:.
    elif fault == "wrong_epoch": rows = (replace(rows[0], epoch=("old",)),) + rows[1:]
    # Run this branch when fault equals the text 'asymmetric'.
    # Set rows to a tuple containing the result of replace(rows at 0) plus rows sliced by 1:.
    elif fault == "asymmetric": rows = (replace(rows[0], mandatory=()),) + rows[1:]
    # Run this branch when fault equals the text 'physics'.
    # Set physics to a tuple containing the result of replace(physics at 0) plus physics sliced by 1:.
    elif fault == "physics": physics = (replace(physics[0], timestamp=40),) + physics[1:]
    # Set (order, error) to the result of legal_order(the text 'E02', 43.6, epoch, rows, physics, paths).
    order, error = legal_order("E02", 43.6, epoch, rows, physics, paths)
    # Require order is the same object as None and error; otherwise raise AssertionError.
    assert order is None and error


# Check four independent controllers have compatible permissions using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_four_independent_controllers_have_compatible_permissions():
    # Import EgoExecutionContext, DecentralizedEgoExecutionController from negotiation_execution for the
    # operations below.
    from negotiation_execution import EgoExecutionContext, DecentralizedEgoExecutionController
    # Set (rows, physics, paths, epoch) to the result of transcript(a tuple containing a tuple containing the text
    # 'E02', the text 'W03', a tuple containing the...).
    rows, physics, paths, epoch = transcript((("E02", "W03"), ("N02", "S02")))
    # State using the inputs and processing steps below.
    # Input a: the supplied a.
    # Output: a dictionary built from the supplied values.
    def state(a):
        # Return a dictionary built from the supplied values to the caller.
        return dict(progress=-20, lane_id=a+'_in', lane_position=10,
                    # Supply length as 5.
                    # Supply width as 1.8.
                    # Supply speed as 0.
                    length=5, width=1.8, speed=0)
    # Iterate over key/value pairs from paths.paths, binding each item to (a, path).
    for a, path in paths.paths.items():
        # Set path.incoming_lane_id to a plus the text '_in'.
        # Set path.outgoing_lane_id to a plus the text '_out'.
        path.incoming_lane_id=a+'_in'; path.outgoing_lane_id=a+'_out'
    # Set paths.resolve_front_bumper_path_progress to a callback that returns a tuple containing s at 'progress',
    # None, None.
    paths.resolve_front_bumper_path_progress=lambda s,p:(s['progress'],None,None)
    # Set zones to the result of SimpleNamespace().
    zones=SimpleNamespace(zone_record=lambda *a:dict(zone_id='CZ',
        # Supply first_path_distance_interval as a tuple containing 0, 10.
        # Supply second_path_distance_interval as a tuple containing 0, 10.
        first_path_distance_interval=(0,10),second_path_distance_interval=(0,10)))
    # Set physics to a tuple built from a lazy sequence of the result of replace(m) for m in physics.
    physics=tuple(replace(m,state=state(m.sender_id)) for m in physics)
    # Set decisions to an empty list.
    decisions=[]
    # Iterate over rows, binding each item to row.
    for row in rows:
        # Set own to the next item from a lazy sequence of m for m in physics; retain entries satisfying
        # m.sender_id equals row.sender_id.
        own=next(m for m in physics if m.sender_id==row.sender_id)
        # Set context to the result of EgoExecutionContext(row.sender_id, the result of state(row.sender_id),
        # row.sender_id, 43.6, row.commitments, a tuple...).
        context=EgoExecutionContext(row.sender_id,state(row.sender_id),row.sender_id,43.6,
            # Supply a tuple built from a lazy sequence of m for m in physics; retain entries satisfying
            # m.sender_id differs from row.sender_id to EgoExecutionContext.
            row.commitments,tuple(m for m in physics if m.sender_id!=row.sender_id),
            # Supply strict_admission as True.
            # Supply coordination_epoch as epoch.
            # Supply mappo_receipt as True.
            True,43.6,strict_admission=True,coordination_epoch=epoch,mappo_receipt=True,
            # Supply fallback_peer_ids as row.eligible_peers.
            # Supply mandatory_commitments as row.mandatory.
            fallback_peer_ids=row.eligible_peers,mandatory_commitments=row.mandatory,
            # Supply queue_arrival_seconds as row.arrival.
            # Supply fallback_endpoint_evidence as rows.
            queue_arrival_seconds=row.arrival,fallback_endpoint_evidence=rows,
            # Supply own_execution_message as own.
            # Supply mandatory_aware_fallback as True.
            own_execution_message=own,mandatory_aware_fallback=True)
        # Set decision to the result of DecentralizedEgoExecutionController(paths, zones).decide(context).
        decision=DecentralizedEgoExecutionController(paths,zones).decide(context)
        # Append decision to decisions.
        decisions.append(decision)
    # Require a list of d.ego_id for d in decisions; retain entries satisfying d.permission equals the text
    # 'PERMITTED' equals a list containing the text 'S02'; otherwise raise AssertionError.
    assert [d.ego_id for d in decisions if d.permission=='PERMITTED']==['S02']
    # Require whether every item is true in a lazy sequence of d.permission equals the text
    # 'BLOCKED_BY_PRECEDENCE' for d in decisions; retain entries satisfying d.ego_id differs from the text 'S02';
    # otherwise raise AssertionError.
    assert all(d.permission=='BLOCKED_BY_PRECEDENCE' for d in decisions if d.ego_id!='S02')
