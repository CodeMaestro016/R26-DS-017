"""Capture named source versions; never rewrite old science or package bytes."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import zipfile for use in this module.
import zipfile

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/live_deadlock_investigation/20261016/approved_source_v...'.
OUT=BASE/'results/live_deadlock_investigation/20261016/approved_source_versions'
# Set FILES to a list containing the text 'runtime_simulation/runner.py', the text
# 'negotiation_execution/replay.py', the text...
FILES=['runtime_simulation/runner.py','negotiation_execution/replay.py',
       'negotiation_execution/ego_controller.py','negotiation_learning/movement_declarations.py']


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=False)
    # Set receipt to a dictionary containing protocol, current, naming_period.
    receipt={'protocol':'CONDITIONAL_CLAIM_RECONCILIATION_V1','current':{},'naming_period':{}}
    # Enter the result of zipfile.ZipFile(BASE.parent joined with the path segment
    # 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as archive and run the enclosed operations
    # within that context.
    with zipfile.ZipFile(BASE.parent/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as archive:
        # Iterate over FILES, binding each item to name.
        for name in FILES:
            # Set current to the bytes read from (BASE / name).
            current=(BASE/name).read_bytes()
            # Set receipt['current'][name] to the hexadecimal digest from hashlib.sha256(current).
            receipt['current'][name]=hashlib.sha256(current).hexdigest()
            # Set destination to OUT joined with the path segment 'current' divided by name.
            destination=OUT/'current'/name
            # Create the directory requested by destination.parent.
            destination.parent.mkdir(parents=True,exist_ok=True)
            # Write the supplied bytes to destination.
            destination.write_bytes(current)
            # Set key to BASE.name plus the text '/' plus name.
            key=BASE.name+'/'+name
            # Run this branch when key belongs to the result of archive.namelist().
            if key in archive.namelist():
                # Set old to the result of archive.read(key).
                old=archive.read(key)
                # Set destination to OUT joined with the path segment 'naming_period' divided by name.
                destination=OUT/'naming_period'/name
                # Create the directory requested by destination.parent.
                destination.parent.mkdir(parents=True,exist_ok=True)
                # Write the supplied bytes to destination.
                destination.write_bytes(old)
                # Set receipt['naming_period'][name] to the hexadecimal digest from hashlib.sha256(old).
                receipt['naming_period'][name]=hashlib.sha256(old).hexdigest()
    # Write the supplied text to (OUT / 'identity.json').
    (OUT/'identity.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt,indent=2))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
