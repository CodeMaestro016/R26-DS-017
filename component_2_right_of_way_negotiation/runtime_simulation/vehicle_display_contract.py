"""Measured permission/motion explanation; never supplies control inputs."""
from config import SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS

VERSION = "VEHICLE_STATE_CONSISTENCY_V1"


def explain_decision(decision, speed, now):
    motion = 'STOPPED' if speed <= 0 else 'CREEPING' if speed < STOPPED_SPEED_THRESHOLD_MPS else 'MOVING'
    if decision is None:
        return dict(state_timestamp=now, motion_state=motion, entry_permission=None)
    allowed = decision.permission == 'PERMITTED'
    blocked = tuple(dict(zone_id=z, distance_m=float(d), priority_vehicle_id=p)
                    for z,d,p in decision.blocked_zones)
    label = ('READY / GO' if allowed else
             'ENTRY HELD / APPROACHING STOP' if speed > 0 else 'ENTRY HELD / STOPPED')
    return dict(state_timestamp=now, motion_state=motion, permission_label=label,
        entry_permission=dict(authorized=allowed, permission=decision.permission,
            reason=decision.reason, timestamp=now, blocked_zones=blocked,
            blocking_vehicle_ids=tuple(sorted({r['priority_vehicle_id'] for r in blocked if r['priority_vehicle_id']})),
            distance_to_stop_m=min((r['distance_m'] for r in blocked),default=None),
            shield_rejection_reason=decision.shield_rejection_reason,
            fallback_pairs=decision.fallback_pairs),
        speed_command=dict(requested_mps=decision.requested_speed_mps,
            issued_at=now, applies_to_next_step_at=now+SIM_TIME_STEP,
            observed_speed_mps=float(speed)))


def explain_mappo(local_status, current_receipt, last_event_time, now, factors):
    if current_receipt:
        status='DECISION_APPLIED'
    elif last_event_time is not None:
        status='DECISION_EXPIRED'
    elif local_status in {'NO_ACTIVE_CONFLICT','REGULATORY_ORDER_RESOLVED'}:
        status='NOT_REQUIRED'
    elif local_status and (local_status.startswith('NEGOTIATION_REQUIRED_')):
        status='ELIGIBLE'
    elif local_status:
        status='BLOCKED'
    else:
        status='NOT_YET_APPLICABLE'
    return dict(status=status, current_receipt=bool(current_receipt),
        local_actor_action_count=len(factors) if current_receipt else 0,
        last_event_timestamp=last_event_time,
        event_age_seconds=None if last_event_time is None else max(0.,now-last_event_time),
        source_status=local_status, actions=factors if current_receipt else ())
