"""Telemetry regressions: display status must not grant movement authority."""
import pytest

from runtime_simulation.browser_state import (
    TrafficProgressTelemetry, displayed_mappo_invocation,
)
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS


@pytest.mark.parametrize('status', [
    'COMMUNICATED_PRECEDENCE_DISAGREEMENT',
    'NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED',
    'SOURCE_SNAPSHOT_MISMATCH', 'REGULATORY_PROFILE_MISMATCH',
    'NEGOTIATION_REQUIRED_REGULATORY_CYCLE',
    'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE',
])
def test_unexecuted_inference_is_blocked_not_not_required(status):
    assert displayed_mappo_invocation(status) == 'BLOCKED'


@pytest.mark.parametrize('status', ['NO_ACTIVE_CONFLICT','REGULATORY_ORDER_RESOLVED'])
def test_only_supported_resolutions_need_no_inference(status):
    assert displayed_mappo_invocation(status) == 'NOT_REQUIRED'


def test_actual_inference_receipt_remains_authorized():
    assert displayed_mappo_invocation('NEGOTIATION_REQUIRED_REGULATORY_CYCLE', True) == 'AUTHORIZED'


def test_blockage_uses_heads_and_existing_duration_not_moving_followers():
    tracker = TrafficProgressTelemetry()
    states = {'N': {'speed':0.0}, 'S': {'speed':0.0}, 'follower':{'speed':8.0}}
    args = (states, ('N','S'), {'N','S'}, 'COMMUNICATED_PRECEDENCE_DISAGREEMENT', (('N','S'),('S','N')))
    assert tracker.observe(10, *args)['status'] == 'TEMPORARY_HOLD'
    assert tracker.observe(10+DEADLOCK_DURATION_SECONDS-0.01,*args)['status'] == 'TEMPORARY_HOLD'
    observed = tracker.observe(10+DEADLOCK_DURATION_SECONDS,*args)
    assert observed['status'] == 'PERSISTENT_BLOCKAGE'
    assert observed['display_only']
    assert states['follower']['speed'] == 8.0
    states['N']['speed'] = STOPPED_SPEED_THRESHOLD_MPS
    assert tracker.observe(26,*args)['status'] == 'PROGRESS_OR_TRANSIENT_WAIT'
    states['N']['speed'] = 0
    assert tracker.observe(27,*args)['blocked_seconds'] == 0


def test_changed_dependencies_or_missing_head_reset_blockage_clock():
    tracker = TrafficProgressTelemetry()
    states = {'N':{'speed':0},'S':{'speed':0}}
    tracker.observe(1, states, ('N','S'), {'N','S'}, 'BLOCKED', (('N','S'),))
    assert tracker.observe(20, states, ('N','S'), {'N','S'}, 'BLOCKED', (('S','N'),))['status'] == 'TEMPORARY_HOLD'
    del states['N']
    assert tracker.observe(40, states, ('N','S'), {'N','S'}, 'BLOCKED', (('S','N'),))['status'] == 'PROGRESS_OR_TRANSIENT_WAIT'
