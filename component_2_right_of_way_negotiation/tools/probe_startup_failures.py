"""Real prerequisite-failure checks; no simulator stepping or model alteration."""
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import patch from unittest.mock for the operations below.
from unittest.mock import patch

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(BASE.parent))
# Import COMPONENT2 from socialmind_drive_showcase.config for the operations below.
from socialmind_drive_showcase.config import COMPONENT2
# Import ComponentLauncher from socialmind_drive_showcase.services.component_launcher for the operations below.
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher

# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set checks to an empty list.
    checks=[]
    # Set absent to OUT joined with the path segment 'missing_asset_working_directory'.
    # Create the directory requested by absent.
    absent=OUT/'missing_asset_working_directory';absent.mkdir(exist_ok=True)
    # Set cmd to a tuple containing the text '{python}', a string built from BASE joined with the path segment
    # 'run_runtime_simulation.py', the text...
    cmd=('{python}',str(BASE/'run_runtime_simulation.py'),'--web-live')
    # Set missing_asset to the result of replace(COMPONENT2).
    missing_asset=replace(COMPONENT2,working_directory=absent,launch_command=cmd)
    # Set launcher to the result of ComponentLauncher(missing_asset).
    launcher=ComponentLauncher(missing_asset)
    # Require the negation of the result of launcher.launch(a tuple containing the text '--scenario', the text
    # 'congested_four_approach'); otherwise raise AssertionError.
    assert not launcher.launch(('--scenario','congested_four_approach'))
    # Require launcher.status equals the text 'FAILED' and the text 'selected_policy.pt' belongs to
    # launcher.error; otherwise raise AssertionError.
    assert launcher.status=='FAILED' and 'selected_policy.pt' in launcher.error
    # Append a dictionary built from the supplied values to checks.
    checks.append(dict(check='MISSING_MODEL_ASSET',status=launcher.status,exit_code=launcher.exit_code,error=launcher.error,process_started=False))
    # Set env to a dictionary built from os.environ.
    # Set env['PATH'] to a string built from the result of Path(os.environ at 'SystemRoot') joined with the path segment
    # 'System32'.
    # Remove the requested entry from env.
    env=dict(os.environ);env['PATH']=str(Path(os.environ['SystemRoot'])/'System32');env.pop('SUMO_HOME',None)
    # Set output to OUT joined with the path segment 'missing_sumo_startup'.
    output=OUT/'missing_sumo_startup'
    # Set missing_sumo to the result of replace(COMPONENT2).
    missing_sumo=replace(COMPONENT2,launch_command=COMPONENT2.launch_command+('--output-dir',str(output)))
    # Set launcher to the result of ComponentLauncher(missing_sumo).
    launcher=ComponentLauncher(missing_sumo)
    # Enter the result of patch.dict(os.environ, env) and run the enclosed operations within that context.
    with patch.dict(os.environ,env,clear=True):
        # Require the negation of the result of launcher.launch(a tuple containing the text '--scenario', the text
        # 'congested_four_approach'); otherwise raise AssertionError.
        assert not launcher.launch(('--scenario','congested_four_approach'))
    # Require launcher.status equals the text 'FAILED' and the text 'not on PATH' belongs to launcher.error;
    # otherwise raise AssertionError.
    assert launcher.status=='FAILED' and 'not on PATH' in launcher.error
    # Append a dictionary built from the supplied values to checks.
    checks.append(dict(check='SUMO_ABSENT_FROM_PATH',status=launcher.status,exit_code=launcher.exit_code,error=launcher.error,process_started=False))
    # Write the supplied text to (OUT / 'startup_failure_checks.json').
    (OUT/'startup_failure_checks.json').write_text(json.dumps(dict(evidence_classification='PRESENTATION_PREREQUISITE_CHECK_NOT_VALIDATION',checks=checks),indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps(checks,indent=2))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
