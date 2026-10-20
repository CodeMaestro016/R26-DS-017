"""Exercise the exact registered app shutdown method on a live owned runtime."""
# Import json for use in this module.
import json
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
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

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Set out to BASE joined with the path segment 'results/final_readiness/20261016'.
    out=BASE/'results/final_readiness/20261016'
    # Set model to the result of replace(COMPONENT2).
    model=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(out/'shutdown_probe')))
    # Set launcher to the result of ComponentLauncher(model).
    # Require the result of launcher.launch(a tuple containing the text '--scenario', the text 'default_panel');
    # otherwise raise AssertionError.
    launcher=ComponentLauncher(model);assert launcher.launch(('--scenario','default_panel'))
    # Set frame to None.
    # Set started to the monotonic clock time.
    frame=None;started=time.monotonic()
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Repeat the following steps while the monotonic clock time minus started is less than 30 and
        # launcher.status differs from the text 'FAILED'.
        while time.monotonic()-started<30 and launcher.status!='FAILED':
            # Set state to the result of read_live_state(COMPONENT2_LIVE_STATE_PATH).
            state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
            # Run this branch when 'available' from state; use None if absent and 'simulation_time' from
            # state['payload']; use 0 if absent is at least 1.
            if state.get('available') and state['payload'].get('simulation_time',0)>=1:
                # Set frame to state at 'payload'.
                # Leave the nearest enclosing loop immediately.
                frame=state['payload'];break
            # Pause execution for 0.1.
            time.sleep(.1)
        # Set process to launcher._process.
        process=launcher._process
        # Set owner to the result of psutil.Process(process.pid).
        owner=psutil.Process(process.pid)
        # Set identities to a list of a tuple containing p.pid, the result of p.create_time() for p in a list
        # containing owner plus the result of owner.children().
        identities=[(p.pid,p.create_time()) for p in [owner]+owner.children(recursive=True)]
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call launcher.shutdown with the supplied arguments.
        launcher.shutdown(5)
    # Set remaining to an empty list.
    remaining=[]
    # Iterate over identities, binding each item to (pid, born).
    for pid,born in identities:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set p to the result of psutil.Process(pid).
            p=psutil.Process(pid)
            # Run this branch when the result of p.is_running() and the result of p.create_time() equals born.
            # Append pid to remaining.
            if p.is_running() and p.create_time()==born:remaining.append(pid)
        # Handle psutil.NoSuchProcess using the recovery steps below.
        # Keep this block syntactically valid without performing an operation.
        except psutil.NoSuchProcess:pass
    # Set result to a dictionary built from the supplied values.
    result=dict(evidence_classification='QUALITATIVE_SHUTDOWN_CHECK_NOT_VALIDATION',
        # Supply real_frame as frame is a different object from None.
        # Supply observed_simulation_time as 'simulation_time' from frame; use None if absent when frame,
        # otherwise None.
        real_frame=frame is not None,observed_simulation_time=frame.get('simulation_time') if frame else None,
        # Supply status as launcher.status.
        # Supply exit_code as launcher.exit_code.
        # Supply forced as launcher.stop_forced.
        status=launcher.status,exit_code=launcher.exit_code,forced=launcher.stop_forced,
        # Supply remaining_owned_pids as remaining.
        # Supply wall_seconds as the monotonic clock time minus started.
        remaining_owned_pids=remaining,wall_seconds=time.monotonic()-started,
        # Supply relaunch_refused as the negation of the result of launcher.launch().
        # Supply log_path as a string built from launcher.log_path.
        relaunch_refused=not launcher.launch(),log_path=str(launcher.log_path))
    # Write the supplied text to (out / 'shutdown_check.json').
    # Display the serialized data produced by json.dumps.
    (out/'shutdown_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    # Require frame and launcher.status equals the text 'READY' and the negation of remaining and result at
    # 'relaunch_refused'; otherwise raise AssertionError.
    assert frame and launcher.status=='READY' and not remaining and result['relaunch_refused']

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
