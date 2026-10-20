"""Short qualitative lifecycle/HTTP probes, never quantitative evaluation."""
# Import json for use in this module.
import json
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import urlopen from urllib.request for the operations below.
from urllib.request import urlopen
# Import psutil for use in this module.
import psutil

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set WORKSPACE to BASE.parent.
WORKSPACE=BASE.parent
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(WORKSPACE))
# Import COMPONENT2, COMPONENT2_LIVE_STATE_PATH from socialmind_drive_showcase.config for the operations below.
from socialmind_drive_showcase.config import COMPONENT2,COMPONENT2_LIVE_STATE_PATH
# Import ComponentLauncher from socialmind_drive_showcase.services.component_launcher for the operations below.
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
# Import read_live_state from socialmind_drive_showcase.services.live_state_reader for the operations below.
from socialmind_drive_showcase.services.live_state_reader import read_live_state

# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'

# Launch checks using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def launch_checks():
    # Set probes to an empty list.
    probes=[]
    # Iterate over index/value pairs from a list containing the text 'congested_four_approach', the text
    # 'default_panel', binding each item to (index, scenario).
    for index,scenario in enumerate(['congested_four_approach','default_panel'],1):
        # Set output to OUT divided by formatted text built from the embedded values.
        output=OUT/f'qualitative_launch_probe_{index}'
        # Set model to the result of replace(COMPONENT2).
        model=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(output)))
        # Set launcher to the result of ComponentLauncher(model).
        launcher=ComponentLauncher(model)
        # Set started to the monotonic clock time.
        # Set owned to an empty list.
        # Set frame to None.
        started=time.monotonic();owned=[];frame=None
        # Set accepted to the result of launcher.launch(a tuple containing the text '--scenario', scenario).
        accepted=launcher.launch(('--scenario',scenario))
        # Set duplicate_refused to the negation of the result of launcher.launch(a tuple containing the text
        # '--scenario', scenario).
        duplicate_refused=not launcher.launch(('--scenario',scenario))
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set deadline to the monotonic clock time plus 30.
            deadline=time.monotonic()+30
            # Repeat the following steps while the monotonic clock time is less than deadline and launcher.status
            # differs from the text 'FAILED'.
            while time.monotonic()<deadline and launcher.status!='FAILED':
                # Set state to the result of read_live_state(COMPONENT2_LIVE_STATE_PATH).
                state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
                # Run this branch when 'available' from state; use None if absent and 'simulation_time' from
                # state['payload']; use 0 if absent is at least 2.
                if state.get('available') and state['payload'].get('simulation_time',0)>=2:
                    # Set frame to state at 'payload'.
                    # Leave the nearest enclosing loop immediately.
                    frame=state['payload'];break
                # Pause execution for 0.1.
                time.sleep(.1)
            # Set process to launcher._process.
            process=launcher._process
            # Run this branch when process is a different object from None and the result of process.poll() is the
            # same object as None.
            if process is not None and process.poll() is None:
                # Set processes to a list containing the result of psutil.Process(process.pid) plus the result of
                # psutil.Process(process.pid).children().
                processes=[psutil.Process(process.pid)]+psutil.Process(process.pid).children(recursive=True)
                # Set owned to a list of a tuple containing p.pid, the result of p.create_time() for p in
                # processes.
                owned=[(p.pid,p.create_time()) for p in processes]
            # Set stop_accepted to the result of launcher.request_stop().
            stop_accepted=launcher.request_stop()
            # Run this branch when launcher._worker is a different object from None.
            # Call launcher._worker.join with the supplied arguments.
            if launcher._worker is not None:launcher._worker.join(12)
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Call launcher.shutdown with the supplied arguments.
            launcher.shutdown(1)
        # Set alive to an empty list.
        alive=[]
        # Iterate over owned, binding each item to (pid, born).
        for pid,born in owned:
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set candidate to the result of psutil.Process(pid).
                candidate=psutil.Process(pid)
                # Run this branch when the result of candidate.create_time() equals born and the result of
                # candidate.is_running().
                # Append pid to alive.
                if candidate.create_time()==born and candidate.is_running():alive.append(pid)
            # Handle psutil.NoSuchProcess using the recovery steps below.
            # Keep this block syntactically valid without performing an operation.
            except psutil.NoSuchProcess:pass
        # Set saved to output joined with the path segment 'latest_runtime_simulation.json'.
        saved=output/'latest_runtime_simulation.json'
        # Set raw to the decoded data produced by json.loads from the text read from saved when whether saved is
        # an existing file, otherwise None.
        raw=json.loads(saved.read_text()) if saved.is_file() else None
        # Set probe to a dictionary built from the supplied values.
        probe=dict(evidence_classification='QUALITATIVE_LIFECYCLE_CHECK_NOT_VALIDATION',scenario=scenario,
            # Supply launch_accepted as accepted.
            # Supply duplicate_refused as duplicate_refused.
            # Supply stop_accepted as stop_accepted.
            launch_accepted=accepted,duplicate_refused=duplicate_refused,stop_accepted=stop_accepted,
            # Supply actual_frame as frame.
            # Supply process_exit_code as launcher.exit_code.
            # Supply status as launcher.status.
            actual_frame=frame,process_exit_code=launcher.exit_code,status=launcher.status,
            # Supply stop_forced as launcher.stop_forced.
            # Supply error as launcher.error.
            # Supply remaining_owned_pids as alive.
            stop_forced=launcher.stop_forced,error=launcher.error,remaining_owned_pids=alive,
            # Supply wall_seconds as the monotonic clock time minus started.
            # Supply run_id as launcher.run_id.
            # Supply log_path as a string built from launcher.log_path.
            wall_seconds=time.monotonic()-started,run_id=launcher.run_id,log_path=str(launcher.log_path),
            # Supply saved_result as a string built from saved when raw, otherwise None.
            # Supply run_status as 'run_status' from raw; use None if absent when raw, otherwise None.
            saved_result=str(saved) if raw else None,run_status=raw.get('run_status') if raw else None)
        # Append probe to probes.
        probes.append(probe)
        # Display the serialized data produced by json.dumps.
        print(json.dumps({k:v for k,v in probe.items() if k!='actual_frame'}),flush=True)
        # Require accepted and duplicate_refused and frame and the negation of alive and launcher.status equals
        # the text 'READY'; otherwise raise AssertionError.
        assert accepted and duplicate_refused and frame and not alive and launcher.status=='READY'
        # Require frame at 'scenario_id' equals scenario; otherwise raise AssertionError.
        assert frame['scenario_id']==scenario
        # Require the number of entries in 'participants' from frame; use an empty tuple if absent is at most 4;
        # otherwise raise AssertionError.
        assert len(frame.get('participants',()))<=4
        # Require frame['run_metrics'] at 'decentralized_execution'; otherwise raise AssertionError.
        assert frame['run_metrics']['decentralized_execution']
    # Write the supplied text to (OUT / 'qualitative_launch_checks.json').
    (OUT/'qualitative_launch_checks.json').write_text(json.dumps(probes,indent=2))

# Http checks using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def http_checks():
    # Set port to 8099.
    port=8099
    # Set routes to a list containing the text '/', the text '/components', the text '/component/right-of-way',
    # the text...
    routes=['/','/components','/component/right-of-way','/component/right-of-way/live','/component/right-of-way/evaluation','/api/component2/live-state']
    # Enter the result of (OUT / 'showcase_http_server.log').open(the text 'w') as log and run the enclosed
    # operations within that context.
    with (OUT/'showcase_http_server.log').open('w',encoding='utf-8') as log:
        # Set process to the result of subprocess.Popen(a list containing sys.executable, the text '-B', a string
        # built from WORKSPACE divided by...).
        process=subprocess.Popen([sys.executable,'-B',str(WORKSPACE/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],
            # Supply cwd as WORKSPACE.
            # Supply stdout as log.
            # Supply stderr as subprocess.STDOUT.
            cwd=WORKSPACE,stdout=log,stderr=subprocess.STDOUT,
            # Supply creationflags as the requested attribute of subprocess.
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        # Set responses to an empty list.
        responses=[]
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set deadline to the monotonic clock time plus 30.
            deadline=time.monotonic()+30
            # Repeat the following steps while the monotonic clock time is less than deadline.
            while time.monotonic()<deadline:
                # Run this branch when the result of process.poll() is a different object from None.
                # Raise RuntimeError with the text 'Showcase startup failed; inspect showcase_http_server.log' to
                # stop this execution path.
                if process.poll() is not None:raise RuntimeError('Showcase startup failed; inspect showcase_http_server.log')
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Enter the result of urlopen(formatted text built from the embedded values) as response and
                    # run the enclosed operations within that context.
                    # Call response.read with the supplied arguments.
                    with urlopen(f'http://127.0.0.1:{port}/',timeout=2) as response:response.read()
                    # Leave the nearest enclosing loop immediately.
                    break
                # Handle OSError using the recovery steps below.
                # Pause execution for 0.2.
                except OSError:time.sleep(.2)
            # Iterate over routes, binding each item to route.
            for route in routes:
                # Enter the result of urlopen(formatted text built from the embedded values plus route) as
                # response and run the enclosed operations within that context.
                with urlopen(f'http://127.0.0.1:{port}'+route,timeout=15) as response:
                    # Set body to the result of response.read().decode().
                    body=response.read().decode()
                    # Append a dictionary built from the supplied values to responses.
                    responses.append(dict(route=route,status=response.status,bytes=len(body.encode()),
                        # Supply has_final_count as the text '34/165' belongs to body.
                        # Supply has_smoke_label as the text 'SMOKE_NOT_FINAL' belongs to body.
                        has_final_count='34/165' in body,has_smoke_label='SMOKE_NOT_FINAL' in body))
            # Display the serialized data produced by json.dumps.
            print(json.dumps(responses,indent=2),flush=True)
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Run this branch when the result of process.poll() is the same object as None.
            if process.poll() is None:
                # Call process.terminate with the supplied arguments.
                process.terminate()
                # Call process.wait with the supplied arguments.
                process.wait(timeout=10)
    # Write the supplied text to (OUT / 'http_checks.json').
    (OUT/'http_checks.json').write_text(json.dumps(dict(responses=responses,visual_browser_check='UNAVAILABLE: no connected browser'),indent=2))

# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Call launch_checks with the supplied arguments.
    launch_checks()
    # Call http_checks with the supplied arguments.
    http_checks()
