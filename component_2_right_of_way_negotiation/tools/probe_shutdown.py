"""Exercise the exact registered app shutdown method on a live owned runtime."""
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
import psutil
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent))
from socialmind_drive_showcase.config import COMPONENT2,COMPONENT2_LIVE_STATE_PATH
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.live_state_reader import read_live_state

def main():
    out=BASE/'results/final_readiness/20261016'
    model=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(out/'shutdown_probe')))
    launcher=ComponentLauncher(model);assert launcher.launch(('--scenario','default_panel'))
    frame=None;started=time.monotonic()
    try:
        while time.monotonic()-started<30 and launcher.status!='FAILED':
            state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
            if state.get('available') and state['payload'].get('simulation_time',0)>=1:
                frame=state['payload'];break
            time.sleep(.1)
        process=launcher._process
        owner=psutil.Process(process.pid)
        identities=[(p.pid,p.create_time()) for p in [owner]+owner.children(recursive=True)]
    finally:
        launcher.shutdown(5)
    remaining=[]
    for pid,born in identities:
        try:
            p=psutil.Process(pid)
            if p.is_running() and p.create_time()==born:remaining.append(pid)
        except psutil.NoSuchProcess:pass
    result=dict(evidence_classification='QUALITATIVE_SHUTDOWN_CHECK_NOT_VALIDATION',
        real_frame=frame is not None,observed_simulation_time=frame.get('simulation_time') if frame else None,
        status=launcher.status,exit_code=launcher.exit_code,forced=launcher.stop_forced,
        remaining_owned_pids=remaining,wall_seconds=time.monotonic()-started,
        relaunch_refused=not launcher.launch(),log_path=str(launcher.log_path))
    (out/'shutdown_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    assert frame and launcher.status=='READY' and not remaining and result['relaunch_refused']

if __name__=='__main__':main()
