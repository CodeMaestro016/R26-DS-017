"""Real launcher/live-frame checks; does not claim unavailable browser clicks."""
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
# Import psutil for use in this module.
import psutil

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(BASE.parent))
# Import COMPONENT2, COMPONENT2_LIVE_STATE_PATH from socialmind_drive_showcase.config for the operations below.
from socialmind_drive_showcase.config import COMPONENT2,COMPONENT2_LIVE_STATE_PATH
# Import ComponentLauncher from socialmind_drive_showcase.services.component_launcher for the operations below.
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
# Import read_live_state from socialmind_drive_showcase.services.live_state_reader for the operations below.
from socialmind_drive_showcase.services.live_state_reader import read_live_state
# Import probe_showcase_readiness as prior for use in this module.
import probe_showcase_readiness as prior


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Set root to BASE joined with the path segment 'results/live_deadlock_investigation/20261016/showcase_approved_v1'.
    root=BASE/'results/live_deadlock_investigation/20261016/showcase_approved_v1'
    # Create the directory requested by root.
    root.mkdir(parents=True,exist_ok=False)
    # Set launcher to the result of ComponentLauncher(COMPONENT2).
    launcher=ComponentLauncher(COMPONENT2)
    # Set receipts to an empty list.
    receipts=[]
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Iterate over a list containing the text 'four_way_simultaneous', the text 'congested_four_approach',
        # binding each item to scenario.
        for scenario in ['four_way_simultaneous','congested_four_approach']:
            # Set launcher.component to the result of replace(COMPONENT2).
            launcher.component=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+
                # Evaluate a tuple containing the text '--output-dir', a string built from root divided by
                # scenario as part of the enclosing expression.
                ('--output-dir',str(root/scenario)))
            # Require the result of launcher.launch(a tuple containing the text '--scenario', scenario); otherwise
            # raise AssertionError.
            assert launcher.launch(('--scenario',scenario))
            # Require the negation of the result of launcher.launch(a tuple containing the text '--scenario',
            # scenario); otherwise raise AssertionError.
            assert not launcher.launch(('--scenario',scenario))
            # Set deadline to the monotonic clock time plus 240.
            deadline=time.monotonic()+240
            # Set frame to None.
            frame=None
            # Set observed_inference to False.
            observed_inference=False
            # Repeat the following steps while the monotonic clock time is less than deadline.
            while time.monotonic()<deadline:
                # Set state to the result of read_live_state(COMPONENT2_LIVE_STATE_PATH).
                state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
                # Run this branch when 'available' from state; use None if absent.
                if state.get('available'):
                    # Set frame to state at 'payload'.
                    frame=state['payload']
                    # Require frame at 'scenario_id' equals scenario; otherwise raise AssertionError.
                    assert frame['scenario_id']==scenario
                    # Update observed_inference to its current value combined with a Boolean built from
                    # 'mappo_decision_epochs' from frame.get('run_metrics', {}); use 0 if absent.
                    observed_inference |= bool(frame.get('run_metrics',{}).get('mappo_decision_epochs',0))
                    # Require the number of entries in 'participants' from frame; use an empty tuple if absent is
                    # at most 4; otherwise raise AssertionError.
                    assert len(frame.get('participants',()))<=4
                    # Run this branch when scenario equals the text 'four_way_simultaneous' and 'completed' from
                    # frame; use None if absent equals 4.
                    if scenario=='four_way_simultaneous' and frame.get('completed')==4:
                        # Leave the nearest enclosing loop immediately.
                        break
                    # Run this branch when scenario equals the text 'congested_four_approach' and 'completed' from
                    # frame; use 0 if absent is at least 5.
                    if scenario=='congested_four_approach' and frame.get('completed',0)>=5:
                        # Leave the nearest enclosing loop immediately.
                        break
                # Run this branch when launcher.status equals the text 'FAILED'.
                # Raise RuntimeError with launcher.error to stop this execution path.
                if launcher.status=='FAILED':raise RuntimeError(launcher.error)
                # Pause execution for 0.1.
                time.sleep(.1)
            # Require frame; otherwise raise AssertionError.
            assert frame
            # Set owned to an empty list.
            owned=[]
            # Run this branch when launcher._process and the result of launcher._process.poll() is the same object
            # as None.
            if launcher._process and launcher._process.poll() is None:
                # Set process to the result of psutil.Process(launcher._process.pid).
                process=psutil.Process(launcher._process.pid)
                # Set owned to a list of a tuple containing p.pid, the result of p.create_time() for p in a list
                # containing process plus the result of process.children().
                owned=[(p.pid,p.create_time()) for p in [process]+process.children(recursive=True)]
            # Run this branch when launcher.running.
            # Require the result of launcher.request_stop(); otherwise raise AssertionError.
            if launcher.running:assert launcher.request_stop()
            # Call launcher._worker.join with the supplied arguments.
            launcher._worker.join(15)
            # Require launcher.status equals the text 'READY' and the negation of launcher.stop_forced; otherwise
            # raise AssertionError.
            assert launcher.status=='READY' and not launcher.stop_forced
            # Iterate over owned, binding each item to (pid, created).
            for pid,created in owned:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                # Require the result of psutil.Process(pid).create_time() differs from created; otherwise raise
                # AssertionError.
                try:assert psutil.Process(pid).create_time()!=created
                # Handle psutil.NoSuchProcess using the recovery steps below.
                # Keep this block syntactically valid without performing an operation.
                except psutil.NoSuchProcess:pass
            # Run this branch when scenario equals the text 'four_way_simultaneous'.
            # Require frame at 'completed' equals 4; otherwise raise AssertionError.
            if scenario=='four_way_simultaneous':assert frame['completed']==4
            # Require observed_inference and frame at 'completed' is at least 5; otherwise raise AssertionError.
            else:assert observed_inference and frame['completed']>=5
            # Append a dictionary built from the supplied values to receipts.
            receipts.append(dict(scenario=scenario,run_id=launcher.run_id,frame=frame,
                # Supply observed_real_inference as observed_inference.
                # Supply exit_code as launcher.exit_code.
                observed_real_inference=observed_inference,exit_code=launcher.exit_code,
                # Supply duplicate_refused as True.
                # Supply owned_processes_cleaned as True.
                # Supply stop_forced as launcher.stop_forced.
                duplicate_refused=True,owned_processes_cleaned=True,stop_forced=launcher.stop_forced))
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call launcher.shutdown with the supplied arguments.
        launcher.shutdown(1)
        # Write the supplied text to (root / 'launcher_live_frames.json').
        (root/'launcher_live_frames.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    # Require the number of entries in receipts equals 2 and receipts[0] at 'run_id' differs from receipts[1] at
    # 'run_id'; otherwise raise AssertionError.
    assert len(receipts)==2 and receipts[0]['run_id']!=receipts[1]['run_id']
    # Set prior.OUT to root.
    prior.OUT=root
    # Call prior.http_checks with the supplied arguments.
    prior.http_checks()
    # Write the supplied text to (root / 'browser_availability.json').
    (root/'browser_availability.json').write_text(json.dumps(dict(connected_browsers=[],
        # Supply encoding as the text 'utf-8'.
        # Supply indent as 2.
        # Supply interactive_visual_test as the text 'UNAVAILABLE'.
        # Supply http_and_actual_live_frames_verified as True.
        interactive_visual_test='UNAVAILABLE',http_and_actual_live_frames_verified=True),indent=2),encoding='utf-8')
    # Display the text 'Four-way completion, dense progress/MAPPO, same-instance...'.
    print('Four-way completion, dense progress/MAPPO, same-instance restart and HTTP verified.')


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
