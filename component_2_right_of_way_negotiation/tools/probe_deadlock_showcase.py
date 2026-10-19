"""Short owned launch/stop/relaunch and HTTP checks for telemetry corrections."""
import json
from dataclasses import replace
from pathlib import Path
import sys
import time
import argparse

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE.parent))
from socialmind_drive_showcase.config import COMPONENT2, COMPONENT2_LIVE_STATE_PATH
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.live_state_reader import read_live_state
import probe_showcase_readiness as previous_probe


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=BASE/'results/live_deadlock_investigation/20261016/showcase_checks')
    root=parser.parse_args().output_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    launcher = ComponentLauncher(replace(COMPONENT2, launch_command=COMPONENT2.launch_command +
        ('--output-dir',str(root/'launch_results'))))
    receipts = []
    try:
        for scenario in ['rule_resolved_two','congested_four_approach']:
            assert launcher.launch(('--scenario',scenario))
            assert not launcher.launch(('--scenario',scenario))
            deadline = time.monotonic()+40
            frame = None
            while time.monotonic()<deadline:
                state = read_live_state(COMPONENT2_LIVE_STATE_PATH, started_after=launcher.started_at)
                if state.get('available') and state['payload']['simulation_time']>=2:
                    frame=state['payload']
                    break
                if launcher.status == 'FAILED':
                    raise RuntimeError(launcher.error)
                time.sleep(.1)
            assert frame and frame['scenario_id']==scenario
            assert launcher.request_stop()
            launcher._worker.join(15)
            assert launcher.status=='READY' and not launcher.stop_forced
            assert launcher._process is None or launcher._process.poll() is not None
            receipts.append(dict(scenario=scenario,run_id=launcher.run_id,
                frame=frame,exit_code=launcher.exit_code,status=launcher.status,
                duplicate_refused=True,cooperative_stop=True))
    finally:
        launcher.shutdown(1)
        (root/'launch_stop_relaunch.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    assert len({r['run_id'] for r in receipts})==2
    previous_probe.OUT=root
    previous_probe.http_checks()
    print('Same-instance launch/stop/relaunch and six HTTP routes verified.')


if __name__=='__main__':
    main()
