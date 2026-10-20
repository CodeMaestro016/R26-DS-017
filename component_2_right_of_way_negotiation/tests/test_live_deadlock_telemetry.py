"""Telemetry regressions: display status must not grant movement authority."""
# Import pytest for use in this module.
import pytest

# Import TrafficProgressTelemetry, displayed_mappo_invocation from runtime_simulation.browser_state for the
# operations below.
from runtime_simulation.browser_state import (
    TrafficProgressTelemetry, displayed_mappo_invocation,
)
# Import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS


# Apply 'status' as a decorator to configure the following definition.
@pytest.mark.parametrize('status', [
    'COMMUNICATED_PRECEDENCE_DISAGREEMENT',
    'NEGOTIATION_BLOCKED_REGULATORY_INPUT_UNRESOLVED',
    'SOURCE_SNAPSHOT_MISMATCH', 'REGULATORY_PROFILE_MISMATCH',
    'NEGOTIATION_REQUIRED_REGULATORY_CYCLE',
    'NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE',
])
# Check unexecuted inference is blocked not not required using the setup, calls, and assertions below.
# Input status: the supplied status.
# Output: no explicit value; normal completion returns None.
def test_unexecuted_inference_is_blocked_not_not_required(status):
    # Require the result of displayed_mappo_invocation(status) equals the text 'BLOCKED'; otherwise raise
    # AssertionError.
    assert displayed_mappo_invocation(status) == 'BLOCKED'


# Apply pytest.mark.parametrize('status', ['NO_ACTIVE_CONFLICT', 'REGULATORY_ORDER_RESOLVED']) as a decorator to
# configure the following definition.
@pytest.mark.parametrize('status', ['NO_ACTIVE_CONFLICT','REGULATORY_ORDER_RESOLVED'])
# Check only supported resolutions need no inference using the setup, calls, and assertions below.
# Input status: the supplied status.
# Output: no explicit value; normal completion returns None.
def test_only_supported_resolutions_need_no_inference(status):
    # Require the result of displayed_mappo_invocation(status) equals the text 'NOT_REQUIRED'; otherwise raise
    # AssertionError.
    assert displayed_mappo_invocation(status) == 'NOT_REQUIRED'


# Check actual inference receipt remains authorized using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actual_inference_receipt_remains_authorized():
    # Require the result of displayed_mappo_invocation(the text 'NEGOTIATION_REQUIRED_REGULATORY_CYCLE', True)
    # equals the text 'AUTHORIZED'; otherwise raise AssertionError.
    assert displayed_mappo_invocation('NEGOTIATION_REQUIRED_REGULATORY_CYCLE', True) == 'AUTHORIZED'


# Check blockage uses heads and existing duration not moving followers using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_blockage_uses_heads_and_existing_duration_not_moving_followers():
    # Set tracker to the result of TrafficProgressTelemetry().
    tracker = TrafficProgressTelemetry()
    # Set states to a dictionary containing N, S, follower.
    states = {'N': {'speed':0.0}, 'S': {'speed':0.0}, 'follower':{'speed':8.0}}
    # Set args to a tuple containing states, a tuple containing the text 'N', the text 'S', a set containing the
    # text 'N', the text 'S', the...
    args = (states, ('N','S'), {'N','S'}, 'COMMUNICATED_PRECEDENCE_DISAGREEMENT', (('N','S'),('S','N')))
    # Require tracker.observe(10, *args) at 'status' equals the text 'TEMPORARY_HOLD'; otherwise raise
    # AssertionError.
    assert tracker.observe(10, *args)['status'] == 'TEMPORARY_HOLD'
    # Require tracker.observe(10 + DEADLOCK_DURATION_SECONDS - 0.01, *args) at 'status' equals the text
    # 'TEMPORARY_HOLD'; otherwise raise AssertionError.
    assert tracker.observe(10+DEADLOCK_DURATION_SECONDS-0.01,*args)['status'] == 'TEMPORARY_HOLD'
    # Set observed to the result of tracker.observe(10 plus DEADLOCK_DURATION_SECONDS, the unpacked values from
    # args).
    observed = tracker.observe(10+DEADLOCK_DURATION_SECONDS,*args)
    # Require observed at 'status' equals the text 'PERSISTENT_BLOCKAGE'; otherwise raise AssertionError.
    assert observed['status'] == 'PERSISTENT_BLOCKAGE'
    # Require observed at 'display_only'; otherwise raise AssertionError.
    assert observed['display_only']
    # Require states['follower'] at 'speed' equals 8.0; otherwise raise AssertionError.
    assert states['follower']['speed'] == 8.0
    # Set states['N']['speed'] to STOPPED_SPEED_THRESHOLD_MPS.
    states['N']['speed'] = STOPPED_SPEED_THRESHOLD_MPS
    # Require tracker.observe(26, *args) at 'status' equals the text 'PROGRESS_OR_TRANSIENT_WAIT'; otherwise raise
    # AssertionError.
    assert tracker.observe(26,*args)['status'] == 'PROGRESS_OR_TRANSIENT_WAIT'
    # Set states['N']['speed'] to 0.
    states['N']['speed'] = 0
    # Require tracker.observe(27, *args) at 'blocked_seconds' equals 0; otherwise raise AssertionError.
    assert tracker.observe(27,*args)['blocked_seconds'] == 0


# Check changed dependencies or missing head reset blockage clock using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_changed_dependencies_or_missing_head_reset_blockage_clock():
    # Set tracker to the result of TrafficProgressTelemetry().
    tracker = TrafficProgressTelemetry()
    # Set states to a dictionary containing N, S.
    states = {'N':{'speed':0},'S':{'speed':0}}
    # Call tracker.observe with the supplied arguments.
    tracker.observe(1, states, ('N','S'), {'N','S'}, 'BLOCKED', (('N','S'),))
    # Require tracker.observe(20, states, ('N', 'S'), {'N', 'S'}, 'BLOCKED', (('S', 'N'),)) at 'status' equals the
    # text 'TEMPORARY_HOLD'; otherwise raise AssertionError.
    assert tracker.observe(20, states, ('N','S'), {'N','S'}, 'BLOCKED', (('S','N'),))['status'] == 'TEMPORARY_HOLD'
    # Delete states['N'] from its containing namespace or collection.
    del states['N']
    # Require tracker.observe(40, states, ('N', 'S'), {'N', 'S'}, 'BLOCKED', (('S', 'N'),)) at 'status' equals the
    # text 'PROGRESS_OR_TRANSIENT_WAIT'; otherwise raise AssertionError.
    assert tracker.observe(40, states, ('N','S'), {'N','S'}, 'BLOCKED', (('S','N'),))['status'] == 'PROGRESS_OR_TRANSIENT_WAIT'
