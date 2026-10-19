"""Capture named source versions; never rewrite old science or package bytes."""
import hashlib
import json
from pathlib import Path
import zipfile

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/live_deadlock_investigation/20261016/approved_source_versions'
FILES=['runtime_simulation/runner.py','negotiation_execution/replay.py',
       'negotiation_execution/ego_controller.py','negotiation_learning/movement_declarations.py']


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    receipt={'protocol':'CONDITIONAL_CLAIM_RECONCILIATION_V1','current':{},'naming_period':{}}
    with zipfile.ZipFile(BASE.parent/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as archive:
        for name in FILES:
            current=(BASE/name).read_bytes()
            receipt['current'][name]=hashlib.sha256(current).hexdigest()
            destination=OUT/'current'/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(current)
            key=BASE.name+'/'+name
            if key in archive.namelist():
                old=archive.read(key)
                destination=OUT/'naming_period'/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(old)
                receipt['naming_period'][name]=hashlib.sha256(old).hexdigest()
    (OUT/'identity.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
