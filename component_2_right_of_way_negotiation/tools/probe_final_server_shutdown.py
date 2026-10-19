"""Owned real-server HTTP/frame and Windows console-interrupt verification."""
from pathlib import Path
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent))
OUT=BASE/'results/final_live_correction/20261016/server_shutdown_synchronized_v1'


def serve(port):
    from dataclasses import replace
    import socialmind_drive_showcase.app as site
    from socialmind_drive_showcase.pages import component2_live_view as view
    from socialmind_drive_showcase.app import build_app, LAUNCHER
    from nicegui import app, ui
    private_state=BASE/'results/vehicle_state_consistency/20261016/http_synchronized_v1/regulatory_cycle/live_state.json'
    site.COMPONENT2_LIVE_STATE_PATH=private_state
    view.COMPONENT2_LIVE_STATE_PATH=private_state
    LAUNCHER.component=replace(LAUNCHER.component,launch_command=('{python}',
        str(BASE/'tools/diagnose_vehicle_states.py'),'--duration','220','--version',
        'http_synchronized_v1','--command-trace','--native-junction-trace'))
    @app.post('/__diagnostic/launch')
    def launch():
        return {'launched':LAUNCHER.launch(('--scenario','regulatory_cycle'))}
    @app.get('/__diagnostic/owned-process')
    def owned():
        return {'pid':LAUNCHER._process.pid if LAUNCHER._process else None,'status':LAUNCHER.status}
    build_app()
    ui.run(host='127.0.0.1',port=port,reload=False,show=False)


def main():
    import psutil
    OUT.mkdir(parents=True,exist_ok=False)
    with socket.socket() as available:
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    def get(path):
        return json.loads(urllib.request.urlopen(url+path,timeout=15).read())
    with (OUT/'server.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--serve',str(port)],
            cwd=BASE.parent,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            deadline=time.monotonic()+45
            while True:
                try: get('/__diagnostic/owned-process');break
                except (OSError,ValueError):
                    if time.monotonic()>deadline or process.poll() is not None:raise
                    time.sleep(.2)
            routes={}
            for path in ['/','/components','/component/right-of-way',
                         '/component/right-of-way/live','/component/right-of-way/evaluation','/about']:
                routes[path]=urllib.request.urlopen(url+path,timeout=20).status
            request=urllib.request.Request(url+'/__diagnostic/launch',method='POST')
            assert json.loads(urllib.request.urlopen(request,timeout=10).read())['launched']
            frames=[];deadline=time.monotonic()+100
            while time.monotonic()<deadline:
                frame=get('/api/component2/live-state')
                if frame.get('available') and not frame.get('stale'):
                    payload=frame['payload']
                    svg=ET.fromstring(frame['rendered_svg'])
                    metadata=next(e for e in svg.iter() if e.attrib.get('class')=='c2-synchronized-frame')
                    rendered=json.loads(metadata.text)
                    assert rendered['simulation_time']==payload['simulation_time']
                    assert [(v['id'],v['display_state']) for v in rendered['vehicles']]==[
                        (v['id'],v['display_state']) for v in payload['vehicles']]
                    colors={'READY':'#20c86b','BLOCKED':'#ef3f45','APPROACHING':'#2684ff','NEGOTIATING':'#ffd21f','CLEARED':'#9aa3ad'}
                    for v in payload['vehicles']:
                        car=next(e for e in svg.iter() if e.attrib.get('data-vehicle-id')==v['id'])
                        assert next(iter(car)).tag.endswith('title')
                        body=next(e for e in car if e.tag.endswith('rect'))
                        assert body.attrib['fill']==colors[v['display_state']]
                    frames.append(frame)
                    if payload.get('simulation_time',0)>=25 and payload.get('last_mappo_event'):break
                time.sleep(.15)
            assert frames and frames[-1]['payload'].get('last_mappo_event')
            identities=[(p.pid,p.create_time()) for p in [psutil.Process(process.pid)]+
                        psutil.Process(process.pid).children(recursive=True)]
            process.send_signal(signal.CTRL_BREAK_EVENT)
            code=process.wait(timeout=30)
            remaining=[]
            for pid,born in identities:
                try:
                    p=psutil.Process(pid)
                    if p.is_running() and p.create_time()==born:remaining.append(pid)
                except psutil.NoSuchProcess:pass
        finally:
            if process.poll() is None:
                from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
                ComponentLauncher._terminate_owned_tree(process)
    # Match HTTP frames to independent same-timestamp simulator/decision samples.
    raw=BASE/'results/vehicle_state_consistency/20261016/http_synchronized_v1/regulatory_cycle/synchronized_frames.jsonl'
    samples={r['timestamp']:r for r in (json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines())}
    matched_physical=0
    for frame in frames:
        payload=frame['payload'];sample=samples[payload['simulation_time']]
        rows={r['vehicle']['id']:r for r in sample['rows']}
        for vehicle in payload['vehicles']:
            observed=rows[vehicle['id']]['decision']
            assert observed['timestamp']==vehicle['state_timestamp']==payload['simulation_time']
            assert observed['physical_speed']==vehicle['speed_mps']
            assert observed['front_bumper_position']==[vehicle['front_bumper_x'],vehicle['front_bumper_y']]
            assert rows[vehicle['id']]['vehicle']['entry_permission']==vehicle['entry_permission']
        matched_physical+=1
    text=(OUT/'server.log').read_text(encoding='utf-8')
    receipt=dict(routes=routes,matched_http_svg_frames=len(frames),
        last_simulation_time=frames[-1]['payload']['simulation_time'],
        matched_independent_simulator_frames=matched_physical,
        last_mappo_event=frames[-1]['payload']['last_mappo_event'],
        interruption='ISOLATED_WINDOWS_CTRL_BREAK_CONSOLE_EVENT',exit_code=code,
        remaining_owned_pids=remaining,deleted_client_warning='Client has been deleted' in text,
        shutdown_typeerror='TypeError' in text,unhandled_traceback='Traceback' in text,
        interactive_browser_verified=False)
    (OUT/'http_frames.json').write_text(json.dumps(frames,indent=2),encoding='utf-8')
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))
    assert not remaining and not receipt['deleted_client_warning'] and not receipt['shutdown_typeerror']
    assert not receipt['unhandled_traceback']


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--serve',type=int)
    args=parser.parse_args()
    serve(args.serve) if args.serve else main()
