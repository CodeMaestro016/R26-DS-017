"""Short qualitative lifecycle/HTTP probes, never quantitative evaluation."""
import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from urllib.request import urlopen
import psutil

BASE=Path(__file__).resolve().parents[1]
WORKSPACE=BASE.parent
sys.path.insert(0,str(WORKSPACE))
from socialmind_drive_showcase.config import COMPONENT2,COMPONENT2_LIVE_STATE_PATH
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.live_state_reader import read_live_state

OUT=BASE/'results/final_readiness/20261016'

def launch_checks():
    probes=[]
    for index,scenario in enumerate(['congested_four_approach','default_panel'],1):
        output=OUT/f'qualitative_launch_probe_{index}'
        model=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(output)))
        launcher=ComponentLauncher(model)
        started=time.monotonic();owned=[];frame=None
        accepted=launcher.launch(('--scenario',scenario))
        duplicate_refused=not launcher.launch(('--scenario',scenario))
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline and launcher.status!='FAILED':
                state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
                if state.get('available') and state['payload'].get('simulation_time',0)>=2:
                    frame=state['payload'];break
                time.sleep(.1)
            process=launcher._process
            if process is not None and process.poll() is None:
                processes=[psutil.Process(process.pid)]+psutil.Process(process.pid).children(recursive=True)
                owned=[(p.pid,p.create_time()) for p in processes]
            stop_accepted=launcher.request_stop()
            if launcher._worker is not None:launcher._worker.join(12)
        finally:
            launcher.shutdown(1)
        alive=[]
        for pid,born in owned:
            try:
                candidate=psutil.Process(pid)
                if candidate.create_time()==born and candidate.is_running():alive.append(pid)
            except psutil.NoSuchProcess:pass
        saved=output/'latest_runtime_simulation.json'
        raw=json.loads(saved.read_text()) if saved.is_file() else None
        probe=dict(evidence_classification='QUALITATIVE_LIFECYCLE_CHECK_NOT_VALIDATION',scenario=scenario,
            launch_accepted=accepted,duplicate_refused=duplicate_refused,stop_accepted=stop_accepted,
            actual_frame=frame,process_exit_code=launcher.exit_code,status=launcher.status,
            stop_forced=launcher.stop_forced,error=launcher.error,remaining_owned_pids=alive,
            wall_seconds=time.monotonic()-started,run_id=launcher.run_id,log_path=str(launcher.log_path),
            saved_result=str(saved) if raw else None,run_status=raw.get('run_status') if raw else None)
        probes.append(probe)
        print(json.dumps({k:v for k,v in probe.items() if k!='actual_frame'}),flush=True)
        assert accepted and duplicate_refused and frame and not alive and launcher.status=='READY'
        assert frame['scenario_id']==scenario
        assert len(frame.get('participants',()))<=4
        assert frame['run_metrics']['decentralized_execution']
    (OUT/'qualitative_launch_checks.json').write_text(json.dumps(probes,indent=2))

def http_checks():
    port=8099
    routes=['/','/components','/component/right-of-way','/component/right-of-way/live','/component/right-of-way/evaluation','/api/component2/live-state']
    with (OUT/'showcase_http_server.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen([sys.executable,'-B',str(WORKSPACE/'socialmind_drive_showcase/app.py'),'--server-only','--port',str(port)],
            cwd=WORKSPACE,stdout=log,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        responses=[]
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                if process.poll() is not None:raise RuntimeError('Showcase startup failed; inspect showcase_http_server.log')
                try:
                    with urlopen(f'http://127.0.0.1:{port}/',timeout=2) as response:response.read()
                    break
                except OSError:time.sleep(.2)
            for route in routes:
                with urlopen(f'http://127.0.0.1:{port}'+route,timeout=15) as response:
                    body=response.read().decode()
                    responses.append(dict(route=route,status=response.status,bytes=len(body.encode()),
                        has_final_count='34/165' in body,has_smoke_label='SMOKE_NOT_FINAL' in body))
            print(json.dumps(responses,indent=2),flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    (OUT/'http_checks.json').write_text(json.dumps(dict(responses=responses,visual_browser_check='UNAVAILABLE: no connected browser'),indent=2))

if __name__=='__main__':
    launch_checks()
    http_checks()
