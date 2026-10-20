"""Short owned launch/stop/relaunch and HTTP checks for telemetry corrections."""
# Import json for use in this module.
import json
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import argparse for use in this module.
import argparse

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(BASE.parent))
# Import COMPONENT2, COMPONENT2_LIVE_STATE_PATH from socialmind_drive_showcase.config for the operations below.
from socialmind_drive_showcase.config import COMPONENT2, COMPONENT2_LIVE_STATE_PATH
# Import ComponentLauncher from socialmind_drive_showcase.services.component_launcher for the operations below.
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
# Import read_live_state from socialmind_drive_showcase.services.live_state_reader for the operations below.
from socialmind_drive_showcase.services.live_state_reader import read_live_state
# Import probe_showcase_readiness as previous_probe for use in this module.
import probe_showcase_readiness as previous_probe


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Set parser to the result of argparse.ArgumentParser().
    parser=argparse.ArgumentParser()
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--output-dir',type=Path,default=BASE/'results/live_deadlock_investigation/20261016/showcase_checks')
    # Set root to the result of parser.parse_args().output_dir.resolve().
    root=parser.parse_args().output_dir.resolve()
    # Create the directory requested by root.
    root.mkdir(parents=True, exist_ok=False)
    # Set launcher to the result of ComponentLauncher(the result of replace(COMPONENT2)).
    launcher = ComponentLauncher(replace(COMPONENT2, launch_command=COMPONENT2.launch_command +
        # Evaluate a tuple containing the text '--output-dir', a string built from root joined with the path segment
        # 'launch_results' as part of the enclosing expression.
        ('--output-dir',str(root/'launch_results'))))
    # Set receipts to an empty list.
    receipts = []
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Iterate over a list containing the text 'rule_resolved_two', the text 'congested_four_approach', binding
        # each item to scenario.
        for scenario in ['rule_resolved_two','congested_four_approach']:
            # Require the result of launcher.launch(a tuple containing the text '--scenario', scenario); otherwise
            # raise AssertionError.
            assert launcher.launch(('--scenario',scenario))
            # Require the negation of the result of launcher.launch(a tuple containing the text '--scenario',
            # scenario); otherwise raise AssertionError.
            assert not launcher.launch(('--scenario',scenario))
            # Set deadline to the monotonic clock time plus 40.
            deadline = time.monotonic()+40
            # Set frame to None.
            frame = None
            # Repeat the following steps while the monotonic clock time is less than deadline.
            while time.monotonic()<deadline:
                # Set state to the result of read_live_state(COMPONENT2_LIVE_STATE_PATH).
                state = read_live_state(COMPONENT2_LIVE_STATE_PATH, started_after=launcher.started_at)
                # Run this branch when 'available' from state; use None if absent and state['payload'] at
                # 'simulation_time' is at least 2.
                if state.get('available') and state['payload']['simulation_time']>=2:
                    # Set frame to state at 'payload'.
                    frame=state['payload']
                    # Leave the nearest enclosing loop immediately.
                    break
                # Run this branch when launcher.status equals the text 'FAILED'.
                if launcher.status == 'FAILED':
                    # Raise RuntimeError with launcher.error to stop this execution path.
                    raise RuntimeError(launcher.error)
                # Pause execution for 0.1.
                time.sleep(.1)
            # Require frame and frame at 'scenario_id' equals scenario; otherwise raise AssertionError.
            assert frame and frame['scenario_id']==scenario
            # Require the result of launcher.request_stop(); otherwise raise AssertionError.
            assert launcher.request_stop()
            # Call launcher._worker.join with the supplied arguments.
            launcher._worker.join(15)
            # Require launcher.status equals the text 'READY' and the negation of launcher.stop_forced; otherwise
            # raise AssertionError.
            assert launcher.status=='READY' and not launcher.stop_forced
            # Require launcher._process is the same object as None or the result of launcher._process.poll() is a
            # different object from None; otherwise raise AssertionError.
            assert launcher._process is None or launcher._process.poll() is not None
            # Append a dictionary built from the supplied values to receipts.
            receipts.append(dict(scenario=scenario,run_id=launcher.run_id,
                # Supply frame as frame.
                # Supply exit_code as launcher.exit_code.
                # Supply status as launcher.status.
                frame=frame,exit_code=launcher.exit_code,status=launcher.status,
                # Supply duplicate_refused as True.
                # Supply cooperative_stop as True.
                duplicate_refused=True,cooperative_stop=True))
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call launcher.shutdown with the supplied arguments.
        launcher.shutdown(1)
        # Write the supplied text to (root / 'launch_stop_relaunch.json').
        (root/'launch_stop_relaunch.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    # Require the number of entries in a set of r at 'run_id' for r in receipts equals 2; otherwise raise
    # AssertionError.
    assert len({r['run_id'] for r in receipts})==2
    # Set previous_probe.OUT to root.
    previous_probe.OUT=root
    # Call previous_probe.http_checks with the supplied arguments.
    previous_probe.http_checks()
    # Display the text 'Same-instance launch/stop/relaunch and six HTTP routes verified.'.
    print('Same-instance launch/stop/relaunch and six HTTP routes verified.')


# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Call main with the supplied arguments.
    main()
