"""Owned real-server HTTP/frame and Windows console-interrupt verification."""
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import argparse for use in this module.
import argparse
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import signal for use in this module.
import signal
# Import socket for use in this module.
import socket
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import urllib.request for use in this module.
import urllib.request
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(BASE.parent))
# Set OUT to BASE joined with the path segment 'results/final_live_correction/20261016/server_shutdown_synchro...'.
OUT=BASE/'results/final_live_correction/20261016/server_shutdown_synchronized_v1'


# Serve using the inputs and processing steps below.
# Input port: the supplied port.
# Output: no explicit value; normal completion returns None.
def serve(port):
    # Import replace from dataclasses for the operations below.
    from dataclasses import replace
    # Import socialmind_drive_showcase.app as site for use in this module.
    import socialmind_drive_showcase.app as site
    # Import component2_live_view as view from socialmind_drive_showcase.pages for the operations below.
    from socialmind_drive_showcase.pages import component2_live_view as view
    # Import build_app, LAUNCHER from socialmind_drive_showcase.app for the operations below.
    from socialmind_drive_showcase.app import build_app, LAUNCHER
    # Import app, ui from nicegui for the operations below.
    from nicegui import app, ui
    # Set private_state to BASE joined with the path segment
    # 'results/vehicle_state_consistency/20261016/http_synchronized_v...'.
    private_state=BASE/'results/vehicle_state_consistency/20261016/http_synchronized_v1/regulatory_cycle/live_state.json'
    # Set site.COMPONENT2_LIVE_STATE_PATH to private_state.
    site.COMPONENT2_LIVE_STATE_PATH=private_state
    # Set view.COMPONENT2_LIVE_STATE_PATH to private_state.
    view.COMPONENT2_LIVE_STATE_PATH=private_state
    # Set LAUNCHER.component to the result of replace(LAUNCHER.component).
    LAUNCHER.component=replace(LAUNCHER.component,launch_command=('{python}',
        # Include a string built from BASE joined with the path segment 'tools/diagnose_vehicle_states.py' in this tuple.
        str(BASE/'tools/diagnose_vehicle_states.py'),'--duration','220','--version',
        'http_synchronized_v1','--command-trace','--native-junction-trace'))
    # Apply app.post('/__diagnostic/launch') as a decorator to configure the following definition.
    @app.post('/__diagnostic/launch')
    # Launch using the inputs and processing steps below.
    # Output: a dictionary containing launched.
    def launch():
        # Return a dictionary containing launched to the caller.
        return {'launched':LAUNCHER.launch(('--scenario','regulatory_cycle'))}
    # Apply app.get('/__diagnostic/owned-process') as a decorator to configure the following definition.
    @app.get('/__diagnostic/owned-process')
    # Owned using the inputs and processing steps below.
    # Output: a dictionary containing pid, status.
    def owned():
        # Return a dictionary containing pid, status to the caller.
        return {'pid':LAUNCHER._process.pid if LAUNCHER._process else None,'status':LAUNCHER.status}
    # Call build_app with the supplied arguments.
    build_app()
    # Call ui.run with the supplied arguments.
    ui.run(host='127.0.0.1',port=port,reload=False,show=False)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Import psutil for use in this module.
    import psutil
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=False)
    # Enter the result of socket.socket() as available and run the enclosed operations within that context.
    with socket.socket() as available:
        # Call available.bind with the supplied arguments.
        # Set port to available.getsockname() at 1.
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    # Set url to formatted text built from the embedded values.
    url=f'http://127.0.0.1:{port}'
    # Get using the inputs and processing steps below.
    # Input path: the path or path object supplied by the caller.
    # Output: the decoded data produced by json.loads from the result of urllib.request.urlopen(url + path,
    # timeout=15).read().
    def get(path):
        # Return the decoded data produced by json.loads from the result of urllib.request.urlopen(url + path,
        # timeout=15).read() to the caller.
        return json.loads(urllib.request.urlopen(url+path,timeout=15).read())
    # Enter the result of (OUT / 'server.log').open(the text 'w') as log and run the enclosed operations within
    # that context.
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        # Set process to the result of subprocess.Popen(a list containing sys.executable, the text '-B', a string
        # built from the result of...).
        process=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--serve',str(port)],
            # Supply cwd as BASE.parent.
            # Supply stdout as log.
            # Supply stderr as subprocess.STDOUT.
            cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,
            # Supply creationflags as subprocess.CREATE_NEW_PROCESS_GROUP.
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set deadline to the monotonic clock time plus 45.
            deadline=time.monotonic()+45
            # Repeat the following steps while True.
            while True:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                # Call get with the supplied arguments.
                # Leave the nearest enclosing loop immediately.
                try: get('/__diagnostic/owned-process');break
                # Handle (OSError, ValueError) using the recovery steps below.
                except (OSError,ValueError):
                    # Run this branch when the monotonic clock time is greater than deadline or the result of
                    # process.poll() is a different object from None.
                    # Re-raise the active exception.
                    if time.monotonic()>deadline or process.poll() is not None:raise
                    # Pause execution for 0.2.
                    time.sleep(.2)
            # Set routes to an empty dictionary.
            routes={}
            # Iterate over a list containing the text '/', the text '/components', the text
            # '/component/right-of-way', the text..., binding each item to path.
            for path in ['/','/components','/component/right-of-way',
                         '/component/right-of-way/live','/component/right-of-way/evaluation','/about']:
                # Set routes[path] to urllib.request.urlopen(url + path, timeout=20).status.
                routes[path]=urllib.request.urlopen(url+path,timeout=20).status
            # Set request to the result of urllib.request.Request(url plus the text '/__diagnostic/launch').
            request=urllib.request.Request(url+'/__diagnostic/launch',method='POST')
            # Require json.loads(urllib.request.urlopen(request, timeout=10).read()) at 'launched'; otherwise
            # raise AssertionError.
            assert json.loads(urllib.request.urlopen(request,timeout=10).read())['launched']
            # Set frames to an empty list.
            # Set deadline to the monotonic clock time plus 100.
            frames=[];deadline=time.monotonic()+100
            # Repeat the following steps while the monotonic clock time is less than deadline.
            while time.monotonic()<deadline:
                # Set frame to '/api/component2/live-state' from get; use None if absent.
                frame=get('/api/component2/live-state')
                # Run this branch when 'available' from frame; use None if absent and the negation of 'stale' from
                # frame; use None if absent.
                if frame.get('available') and not frame.get('stale'):
                    # Set payload to frame at 'payload'.
                    payload=frame['payload']
                    # Set svg to the result of ET.fromstring(frame at 'rendered_svg').
                    svg=ET.fromstring(frame['rendered_svg'])
                    # Set metadata to the next item from a lazy sequence of e for e in the result of svg.iter();
                    # retain entries satisfying 'class' from e.attrib; use None if absent equals the text
                    # 'c2-synchronized-frame'.
                    metadata=next(e for e in svg.iter() if e.attrib.get('class')=='c2-synchronized-frame')
                    # Set rendered to the decoded data produced by json.loads from metadata.text.
                    rendered=json.loads(metadata.text)
                    # Require rendered at 'simulation_time' equals payload at 'simulation_time'; otherwise raise
                    # AssertionError.
                    assert rendered['simulation_time']==payload['simulation_time']
                    # Require a list of a tuple containing v at 'id', v at 'display_state' for v in rendered at
                    # 'vehicles' equals a list of a tuple containing v at 'id', v at 'display_state' for v in
                    # payload at 'vehicles'; otherwise raise AssertionError.
                    assert [(v['id'],v['display_state']) for v in rendered['vehicles']]==[
                        # Evaluate a tuple containing v at 'id', v at 'display_state' as part of the enclosing
                        # expression.
                        (v['id'],v['display_state']) for v in payload['vehicles']]
                    # Set colors to a dictionary containing READY, BLOCKED, APPROACHING, NEGOTIATING, CLEARED.
                    colors={'READY':'#20c86b','BLOCKED':'#ef3f45','APPROACHING':'#2684ff','NEGOTIATING':'#ffd21f','CLEARED':'#9aa3ad'}
                    # Iterate over payload at 'vehicles', binding each item to v.
                    for v in payload['vehicles']:
                        # Set car to the next item from a lazy sequence of e for e in the result of svg.iter();
                        # retain entries satisfying 'data-vehicle-id' from e.attrib; use None if absent equals v
                        # at 'id'.
                        car=next(e for e in svg.iter() if e.attrib.get('data-vehicle-id')==v['id'])
                        # Require the result of next(iter(car)).tag.endswith(the text 'title'); otherwise raise
                        # AssertionError.
                        assert next(iter(car)).tag.endswith('title')
                        # Set body to the next item from a lazy sequence of e for e in car; retain entries
                        # satisfying the result of e.tag.endswith(the text 'rect').
                        body=next(e for e in car if e.tag.endswith('rect'))
                        # Require body.attrib at 'fill' equals colors at v['display_state']; otherwise raise
                        # AssertionError.
                        assert body.attrib['fill']==colors[v['display_state']]
                    # Append frame to frames.
                    frames.append(frame)
                    # Run this branch when 'simulation_time' from payload; use 0 if absent is at least 25 and
                    # 'last_mappo_event' from payload; use None if absent.
                    # Leave the nearest enclosing loop immediately.
                    if payload.get('simulation_time',0)>=25 and payload.get('last_mappo_event'):break
                # Pause execution for 0.15.
                time.sleep(.15)
            # Require frames and 'last_mappo_event' from frames[-1]['payload']; use None if absent; otherwise
            # raise AssertionError.
            assert frames and frames[-1]['payload'].get('last_mappo_event')
            # Set identities to a list of a tuple containing p.pid, the result of p.create_time() for p in a list
            # containing the result of psutil.Process(process.pid) plus the result of
            # psutil.Process(process.pid).children().
            identities=[(p.pid,p.create_time()) for p in [psutil.Process(process.pid)]+
                        # Supply recursive as True.
                        psutil.Process(process.pid).children(recursive=True)]
            # Call process.send_signal with the supplied arguments.
            process.send_signal(signal.CTRL_BREAK_EVENT)
            # Set code to the result of process.wait().
            code=process.wait(timeout=30)
            # Set remaining to an empty list.
            remaining=[]
            # Iterate over identities, binding each item to (pid, born).
            for pid,born in identities:
                # Attempt the enclosed operations and route matching exceptions to the handlers below.
                try:
                    # Set p to the result of psutil.Process(pid).
                    p=psutil.Process(pid)
                    # Run this branch when the result of p.is_running() and the result of p.create_time() equals
                    # born.
                    # Append pid to remaining.
                    if p.is_running() and p.create_time()==born:remaining.append(pid)
                # Handle psutil.NoSuchProcess using the recovery steps below.
                # Keep this block syntactically valid without performing an operation.
                except psutil.NoSuchProcess:pass
        # Run these cleanup steps whether the preceding operations succeed or raise an exception.
        finally:
            # Run this branch when the result of process.poll() is the same object as None.
            if process.poll() is None:
                # Import ComponentLauncher from socialmind_drive_showcase.services.component_launcher for the
                # operations below.
                from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
                # Call ComponentLauncher._terminate_owned_tree with the supplied arguments.
                ComponentLauncher._terminate_owned_tree(process)
    # Match HTTP frames to independent same-timestamp simulator/decision samples.
    # Set raw to BASE joined with the path segment 'results/vehicle_state_consistency/20261016/http_synchronized_v...'.
    raw=BASE/'results/vehicle_state_consistency/20261016/http_synchronized_v1/regulatory_cycle/synchronized_frames.jsonl'
    # Set samples to a dictionary of r at 'timestamp' mapped to r for r in a lazy sequence of the decoded data
    # produced by json.loads from line for line in the result of raw.read_text(encoding='utf-8').splitlines().
    samples={r['timestamp']:r for r in (json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines())}
    # Set matched_physical to 0.
    matched_physical=0
    # Iterate over frames, binding each item to frame.
    for frame in frames:
        # Set payload to frame at 'payload'.
        # Set sample to samples at payload['simulation_time'].
        payload=frame['payload'];sample=samples[payload['simulation_time']]
        # Set rows to a dictionary of r['vehicle'] at 'id' mapped to r for r in sample at 'rows'.
        rows={r['vehicle']['id']:r for r in sample['rows']}
        # Iterate over payload at 'vehicles', binding each item to vehicle.
        for vehicle in payload['vehicles']:
            # Set observed to rows[vehicle['id']] at 'decision'.
            observed=rows[vehicle['id']]['decision']
            # Require observed at 'timestamp' equals vehicle at 'state_timestamp'; equals payload at
            # 'simulation_time'; otherwise raise AssertionError.
            assert observed['timestamp']==vehicle['state_timestamp']==payload['simulation_time']
            # Require observed at 'physical_speed' equals vehicle at 'speed_mps'; otherwise raise AssertionError.
            assert observed['physical_speed']==vehicle['speed_mps']
            # Require observed at 'front_bumper_position' equals a list containing vehicle at 'front_bumper_x',
            # vehicle at 'front_bumper_y'; otherwise raise AssertionError.
            assert observed['front_bumper_position']==[vehicle['front_bumper_x'],vehicle['front_bumper_y']]
            # Require rows[vehicle['id']]['vehicle'] at 'entry_permission' equals vehicle at 'entry_permission';
            # otherwise raise AssertionError.
            assert rows[vehicle['id']]['vehicle']['entry_permission']==vehicle['entry_permission']
        # Update matched_physical to its current value plus 1.
        matched_physical+=1
    # Set text to the text read from (OUT / 'server.log').
    text=(OUT/'server.log').read_text(encoding='utf-8')
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(routes=routes,matched_http_svg_frames=len(frames),
        # Supply last_simulation_time as frames[-1]['payload'] at 'simulation_time'.
        last_simulation_time=frames[-1]['payload']['simulation_time'],
        # Supply matched_independent_simulator_frames as matched_physical.
        matched_independent_simulator_frames=matched_physical,
        # Supply last_mappo_event as frames[-1]['payload'] at 'last_mappo_event'.
        last_mappo_event=frames[-1]['payload']['last_mappo_event'],
        # Supply interruption as the text 'ISOLATED_WINDOWS_CTRL_BREAK_CONSOLE_EVENT'.
        # Supply exit_code as code.
        interruption='ISOLATED_WINDOWS_CTRL_BREAK_CONSOLE_EVENT',exit_code=code,
        # Supply remaining_owned_pids as remaining.
        # Supply deleted_client_warning as the text 'Client has been deleted' belongs to text.
        remaining_owned_pids=remaining,deleted_client_warning='Client has been deleted' in text,
        # Supply shutdown_typeerror as the text 'TypeError' belongs to text.
        # Supply unhandled_traceback as the text 'Traceback' belongs to text.
        shutdown_typeerror='TypeError' in text,unhandled_traceback='Traceback' in text,
        # Supply interactive_browser_verified as False.
        interactive_browser_verified=False)
    # Write the supplied text to (OUT / 'http_frames.json').
    (OUT/'http_frames.json').write_text(json.dumps(frames,indent=2),encoding='utf-8')
    # Write the supplied text to (OUT / 'receipt.json').
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt))
    # Require the negation of remaining and the negation of receipt at 'deleted_client_warning' and the negation
    # of receipt at 'shutdown_typeerror'; otherwise raise AssertionError.
    assert not remaining and not receipt['deleted_client_warning'] and not receipt['shutdown_typeerror']
    # Require the negation of receipt at 'unhandled_traceback'; otherwise raise AssertionError.
    assert not receipt['unhandled_traceback']


# Run this branch when __name__ equals the text '__main__'.
if __name__=='__main__':
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--serve',type=int)
    # Set args to the result of parser.parse_args().
    args=parser.parse_args()
    # Evaluate the result of serve(args.serve) when args.serve, otherwise the result of main().
    serve(args.serve) if args.serve else main()
