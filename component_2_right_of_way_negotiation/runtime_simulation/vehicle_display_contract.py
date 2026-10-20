"""Measured permission/motion explanation; never supplies control inputs."""
# Import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
from config import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS

# Set VERSION to the text 'VEHICLE_STATE_CONSISTENCY_V1'.
VERSION = "VEHICLE_STATE_CONSISTENCY_V1"


# Explain decision using the inputs and processing steps below.
# Input decision: the supplied decision.
# Input speed: the supplied speed.
# Input now: the time used for this operation.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def explain_decision(decision, speed, now):
    # Set motion to the text 'STOPPED' when speed is at most 0, otherwise the text 'CREEPING' when speed is less
    # than STOPPED_SPEED_THRESHOLD_MPS, otherwise the text 'MOVING'.
    motion = 'STOPPED' if speed <= 0 else 'CREEPING' if speed < STOPPED_SPEED_THRESHOLD_MPS else 'MOVING'
    # Run this branch when decision is the same object as None.
    if decision is None:
        # Return a dictionary built from the supplied values to the caller.
        return dict(state_timestamp=now, motion_state=motion, entry_permission=None)
    # Set allowed to decision.permission equals the text 'PERMITTED'.
    allowed = decision.permission == 'PERMITTED'
    # Set blocked to a tuple built from a lazy sequence of a dictionary built from the supplied values for (z, d,
    # p) in decision.blocked_zones.
    blocked = tuple(dict(zone_id=z, distance_m=float(d), priority_vehicle_id=p)
                    # Evaluate decision.blocked_zones as part of the enclosing expression.
                    for z,d,p in decision.blocked_zones)
    # Set label to the text 'READY / GO' when allowed, otherwise the text 'ENTRY HELD / APPROACHING STOP' when
    # speed is greater than 0, otherwise the text 'ENTRY HELD / STOPPED'.
    label = ('READY / GO' if allowed else
             # Evaluate the text 'ENTRY HELD / APPROACHING STOP' when speed is greater than 0, otherwise the text
             # 'ENTRY HELD / STOPPED' as part of the enclosing expression.
             'ENTRY HELD / APPROACHING STOP' if speed > 0 else 'ENTRY HELD / STOPPED')
    # Return a dictionary built from the supplied values to the caller.
    return dict(state_timestamp=now, motion_state=motion, permission_label=label,
        # Supply entry_permission as a dictionary built from the supplied values.
        # Supply authorized as allowed.
        # Supply permission as decision.permission.
        entry_permission=dict(authorized=allowed, permission=decision.permission,
            # Supply reason as decision.reason.
            # Supply timestamp as now.
            # Supply blocked_zones as blocked.
            reason=decision.reason, timestamp=now, blocked_zones=blocked,
            # Supply blocking_vehicle_ids as a tuple built from the sorted values from a set of r at
            # 'priority_vehicle_id' for r in blocked; retain entries satisfying r at 'priority_vehicle_id'.
            blocking_vehicle_ids=tuple(sorted({r['priority_vehicle_id'] for r in blocked if r['priority_vehicle_id']})),
            # Supply distance_to_stop_m as the minimum of a lazy sequence of r at 'distance_m' for r in blocked.
            # Supply default as None.
            distance_to_stop_m=min((r['distance_m'] for r in blocked),default=None),
            # Supply shield_rejection_reason as decision.shield_rejection_reason.
            shield_rejection_reason=decision.shield_rejection_reason,
            # Supply fallback_pairs as decision.fallback_pairs.
            fallback_pairs=decision.fallback_pairs),
        # Supply speed_command as a dictionary built from the supplied values.
        # Supply requested_mps as decision.requested_speed_mps.
        speed_command=dict(requested_mps=decision.requested_speed_mps,
            # Supply issued_at as now.
            # Supply applies_to_next_step_at as now plus SIM_TIME_STEP.
            issued_at=now, applies_to_next_step_at=now+SIM_TIME_STEP,
            # Supply observed_speed_mps as a floating-point number built from speed.
            observed_speed_mps=float(speed)))


# Explain mappo using the inputs and processing steps below.
# Input local_status: the supplied local status.
# Input current_receipt: the supplied current receipt.
# Input last_event_time: the supplied last event time.
# Input now: the time used for this operation.
# Input factors: the supplied factors.
# Output: a dictionary built from the supplied values.
# Processing: select branches using the stated conditions.
def explain_mappo(local_status, current_receipt, last_event_time, now, factors):
    # Run this branch when current_receipt.
    if current_receipt:
        # Set status to the text 'DECISION_APPLIED'.
        status='DECISION_APPLIED'
    # Run this branch when last_event_time is a different object from None.
    elif last_event_time is not None:
        # Set status to the text 'DECISION_EXPIRED'.
        status='DECISION_EXPIRED'
    # Run this branch when local_status belongs to a set containing the text 'NO_ACTIVE_CONFLICT', the text
    # 'REGULATORY_ORDER_RESOLVED'.
    elif local_status in {'NO_ACTIVE_CONFLICT','REGULATORY_ORDER_RESOLVED'}:
        # Set status to the text 'NOT_REQUIRED'.
        status='NOT_REQUIRED'
    # Run this branch when local_status and the result of local_status.startswith(the text
    # 'NEGOTIATION_REQUIRED_').
    elif local_status and (local_status.startswith('NEGOTIATION_REQUIRED_')):
        # Set status to the text 'ELIGIBLE'.
        status='ELIGIBLE'
    # Run this branch when local_status.
    elif local_status:
        # Set status to the text 'BLOCKED'.
        status='BLOCKED'
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set status to the text 'NOT_YET_APPLICABLE'.
        status='NOT_YET_APPLICABLE'
    # Return a dictionary built from the supplied values to the caller.
    return dict(status=status, current_receipt=bool(current_receipt),
        # Supply local_actor_action_count as the number of entries in factors when current_receipt, otherwise 0.
        local_actor_action_count=len(factors) if current_receipt else 0,
        # Supply last_event_timestamp as last_event_time.
        last_event_timestamp=last_event_time,
        # Supply event_age_seconds as None when last_event_time is the same object as None, otherwise the maximum
        # of 0.0, now minus last_event_time.
        event_age_seconds=None if last_event_time is None else max(0.,now-last_event_time),
        # Supply source_status as local_status.
        # Supply actions as factors when current_receipt, otherwise an empty tuple.
        source_status=local_status, actions=factors if current_receipt else ())
