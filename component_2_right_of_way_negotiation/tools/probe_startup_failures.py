"""Real prerequisite-failure checks; no simulator stepping or model alteration."""
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent))
from socialmind_drive_showcase.config import COMPONENT2
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher

OUT=BASE/'results/final_readiness/20261016'

def main():
    checks=[]
    absent=OUT/'missing_asset_working_directory';absent.mkdir(exist_ok=True)
    cmd=('{python}',str(BASE/'run_runtime_simulation.py'),'--web-live')
    missing_asset=replace(COMPONENT2,working_directory=absent,launch_command=cmd)
    launcher=ComponentLauncher(missing_asset)
    assert not launcher.launch(('--scenario','congested_four_approach'))
    assert launcher.status=='FAILED' and 'selected_policy.pt' in launcher.error
    checks.append(dict(check='MISSING_MODEL_ASSET',status=launcher.status,exit_code=launcher.exit_code,error=launcher.error,process_started=False))
    env=dict(os.environ);env['PATH']=str(Path(os.environ['SystemRoot'])/'System32');env.pop('SUMO_HOME',None)
    output=OUT/'missing_sumo_startup'
    missing_sumo=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(output)))
    launcher=ComponentLauncher(missing_sumo)
    with patch.dict(os.environ,env,clear=True):
        assert not launcher.launch(('--scenario','congested_four_approach'))
    assert launcher.status=='FAILED' and 'not on PATH' in launcher.error
    checks.append(dict(check='SUMO_ABSENT_FROM_PATH',status=launcher.status,exit_code=launcher.exit_code,error=launcher.error,process_started=False))
    (OUT/'startup_failure_checks.json').write_text(json.dumps(dict(evidence_classification='PRESENTATION_PREREQUISITE_CHECK_NOT_VALIDATION',checks=checks),indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
