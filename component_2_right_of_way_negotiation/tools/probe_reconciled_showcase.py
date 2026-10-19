"""Real launcher/live-frame checks; does not claim unavailable browser clicks."""
import json
from dataclasses import replace
from pathlib import Path
import sys
import time
import psutil

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent))
from socialmind_drive_showcase.config import COMPONENT2,COMPONENT2_LIVE_STATE_PATH
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.live_state_reader import read_live_state
import probe_showcase_readiness as prior


def main():
    root=BASE/'results/live_deadlock_investigation/20261016/showcase_approved_v1'
    root.mkdir(parents=True,exist_ok=False)
    launcher=ComponentLauncher(COMPONENT2)
    receipts=[]
    try:
        for scenario in ['four_way_simultaneous','congested_four_approach']:
            launcher.component=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+
                ('--output-dir',str(root/scenario)))
            assert launcher.launch(('--scenario',scenario))
            assert not launcher.launch(('--scenario',scenario))
            deadline=time.monotonic()+240
            frame=None
            observed_inference=False
            while time.monotonic()<deadline:
                state=read_live_state(COMPONENT2_LIVE_STATE_PATH,started_after=launcher.started_at)
                if state.get('available'):
                    frame=state['payload']
                    assert frame['scenario_id']==scenario
                    observed_inference |= bool(frame.get('run_metrics',{}).get('mappo_decision_epochs',0))
                    assert len(frame.get('participants',()))<=4
                    if scenario=='four_way_simultaneous' and frame.get('completed')==4:
                        break
                    if scenario=='congested_four_approach' and frame.get('completed',0)>=5:
                        break
                if launcher.status=='FAILED':raise RuntimeError(launcher.error)
                time.sleep(.1)
            assert frame
            owned=[]
            if launcher._process and launcher._process.poll() is None:
                process=psutil.Process(launcher._process.pid)
                owned=[(p.pid,p.create_time()) for p in [process]+process.children(recursive=True)]
            if launcher.running:assert launcher.request_stop()
            launcher._worker.join(15)
            assert launcher.status=='READY' and not launcher.stop_forced
            for pid,created in owned:
                try:assert psutil.Process(pid).create_time()!=created
                except psutil.NoSuchProcess:pass
            if scenario=='four_way_simultaneous':assert frame['completed']==4
            else:assert observed_inference and frame['completed']>=5
            receipts.append(dict(scenario=scenario,run_id=launcher.run_id,frame=frame,
                observed_real_inference=observed_inference,exit_code=launcher.exit_code,
                duplicate_refused=True,owned_processes_cleaned=True,stop_forced=launcher.stop_forced))
    finally:
        launcher.shutdown(1)
        (root/'launcher_live_frames.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    assert len(receipts)==2 and receipts[0]['run_id']!=receipts[1]['run_id']
    prior.OUT=root
    prior.http_checks()
    (root/'browser_availability.json').write_text(json.dumps(dict(connected_browsers=[],
        interactive_visual_test='UNAVAILABLE',http_and_actual_live_frames_verified=True),indent=2),encoding='utf-8')
    print('Four-way completion, dense progress/MAPPO, same-instance restart and HTTP verified.')


if __name__=='__main__':main()
