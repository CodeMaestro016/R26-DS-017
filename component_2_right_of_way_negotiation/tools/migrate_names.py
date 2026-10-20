"""One-time, audited source-only naming migration. Never edits results."""
# Import csv for use in this module.
import csv
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import re for use in this module.
import re
# Import shutil for use in this module.
import shutil
# Import subprocess for use in this module.
import subprocess
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Set WORKSPACE to BASE.parent.
WORKSPACE = BASE.parent
# Set OUT to BASE joined with the path segment 'results/naming_migration'.
OUT = BASE / "results/naming_migration"
# Set TOKENS to a dictionary containing run_panel_demo, run_panel_validation, run_final_evaluation, panel_demo,...
TOKENS = {"run_panel_demo":"run_runtime_simulation", "run_panel_validation":"run_targeted_validation",
    "run_final_evaluation":"run_post_training_evaluation", "panel_demo":"runtime_simulation",
    "panel_validation":"targeted_validation", "final_evaluation":"post_training_evaluation",
    "PANEL_VALIDATION_REPORT":"TARGETED_VALIDATION_REPORT",
    "PANEL_EVALUATION_REPORT":"POST_TRAINING_EVALUATION_REPORT"}
# Set LABELS to a dictionary containing Panel Demo, Panel Validation, Final Evaluation, Scalability Validation,
# PANEL DEMO SUMMARY.
LABELS = {"Panel Demo":"Runtime Simulation", "Panel Validation":"Targeted Validation",
    "Final Evaluation":"Post-Training Evaluation", "Scalability Validation":"Scalability Evaluation",
    "PANEL DEMO SUMMARY":"RUNTIME SIMULATION SUMMARY"}
# Set PATTERN to the result of re.compile(the result of '|'.join(the result of map(re.escape, TOKENS))).
PATTERN = re.compile("|".join(map(re.escape,TOKENS)))

# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(path.read_bytes()).
def sha(path):
    # Return the hexadecimal digest from hashlib.sha256(path.read_bytes()) to the caller.
    return hashlib.sha256(path.read_bytes()).hexdigest()

# Category using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def category(path):
    # Set parts to path.relative_to(WORKSPACE).parts.
    parts = path.relative_to(WORKSPACE).parts
    # Run this branch when the text 'results' belongs to parts.
    if "results" in parts:
        # Return the text 'F immutable historical evidence/archive' to the caller.
        return "F immutable historical evidence/archive"
    # Run this branch when the text 'tests' belongs to parts.
    if "tests" in parts:
        # Return the text 'B active test' to the caller.
        return "B active test"
    # Run this branch when the text 'socialmind_drive_showcase' belongs to parts and path.suffix equals the text
    # '.py'.
    if "socialmind_drive_showcase" in parts and path.suffix==".py":
        # Return the text 'D active showcase/UI' to the caller.
        return "D active showcase/UI"
    # Run this branch when path.suffix equals the text '.md'.
    if path.suffix==".md":
        # Return the text 'C active documentation' to the caller.
        return "C active documentation"
    # Run this branch when path.suffix does not belong to a set containing the text '.py'.
    if path.suffix not in {".py"}:
        # Return the text 'E generated current-path reference' to the caller.
        return "E generated current-path reference"
    # Return the text 'A active source/import' to the caller.
    return "A active source/import"

# Active files using the inputs and processing steps below.
# Output: a list of p for p in candidates; retain entries satisfying p differs from the result of Path(__file__).
# Processing: iterate over the relevant records.
def active_files():
    # Set candidates to a list containing WORKSPACE joined with the path segment 'README.md'.
    candidates = [WORKSPACE/"README.md"]
    # Iterate over a tuple containing BASE, WORKSPACE joined with the path segment 'socialmind_drive_showcase', binding
    # each item to folder.
    for folder in (BASE,WORKSPACE/"socialmind_drive_showcase"):
        # Update candidates to its current value plus a list of p for p in the result of folder.rglob(the text
        # '*'); retain entries satisfying whether p is an existing file and p.suffix belongs to a set containing
        # '.py', '.md',...
        candidates += [p for p in folder.rglob("*") if p.is_file() and p.suffix in {".py",".md",".json",".toml",".txt",".ini",".cfg"}
            # Evaluate the negation of a set built from p.relative_to(folder).parts intersected with a set
            # containing the text 'results', the text '__pycache__', the text '.pytest_cache', the text '.git',
            # the text '.venv' as part of the enclosing expression.
            and not set(p.relative_to(folder).parts)&{"results","__pycache__",".pytest_cache",".git",".venv"}]
    # Return a list of p for p in candidates; retain entries satisfying p differs from the result of
    # Path(__file__) to the caller.
    return [p for p in candidates if p != Path(__file__) ]

# Audit using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def audit():
    # Create the directory requested by OUT.
    OUT.mkdir(parents=True,exist_ok=True)
    # Set inventory to an empty dictionary.
    inventory = {}
    # Set counts to an empty dictionary.
    counts = {}
    # Enter the result of (OUT / 'occurrences.csv').open(the text 'x') as handle and run the enclosed operations
    # within that context.
    with (OUT/"occurrences.csv").open("x",newline="",encoding="utf-8") as handle:
        # Set writer to the result of csv.writer(handle).
        writer = csv.writer(handle)
        # Call writer.writerow with the supplied arguments.
        writer.writerow(["category","path","line","term"])
        # Set files to the result of active_files() plus a list built from the result of (BASE /
        # 'results').rglob(the text '*').
        files = active_files()+list((BASE/"results").rglob("*"))
        # Iterate over files, binding each item to p.
        for p in files:
            # Run this branch when the negation of whether p is an existing file or OUT belongs to p.parents.
            if not p.is_file() or OUT in p.parents:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set group to the result of category(p).
            group = category(p)
            # Run this branch when the result of group.startswith(the text 'F').
            if group.startswith("F"):
                # Set inventory[str(p.relative_to(BASE))] to the result of sha(p).
                inventory[str(p.relative_to(BASE))]=sha(p)
            # Run this branch when p.suffix does not belong to a set containing the text '.py', the text '.md',
            # the text '.json', the text '.jsonl', the text '.txt', the text '.html',...
            if p.suffix not in {".py",".md",".json",".jsonl",".txt",".html",".csv",".toml",".ini",".cfg"}:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Enter the result of p.open() as source and run the enclosed operations within that context.
            with p.open(encoding="utf-8-sig",errors="replace") as source:
                # Iterate over index/value pairs from source, binding each item to (line_number, line).
                for line_number,line in enumerate(source,1):
                    # Iterate over the result of PATTERN.finditer(line), binding each item to hit.
                    for hit in PATTERN.finditer(line):
                        # Call writer.writerow with the supplied arguments.
                        writer.writerow([group,str(p.relative_to(WORKSPACE)),line_number,hit.group()])
                        # Set counts[group] to group from counts; use 0 if absent plus 1.
                        counts[group]=counts.get(group,0)+1
    # Write the supplied text to (OUT / 'historical_inventory.json').
    (OUT/"historical_inventory.json").write_text(json.dumps(inventory,indent=2))
    # Set before to a dictionary of a string built from the result of p.relative_to(WORKSPACE) mapped to the
    # result of sha(p) for p in the result of active_files().
    before={str(p.relative_to(WORKSPACE)):sha(p) for p in active_files()}
    # Write the supplied text to (OUT / 'active_inventory.json').
    (OUT/"active_inventory.json").write_text(json.dumps(before,indent=2))
    # Write the supplied text to (OUT / 'occurrence_counts.json').
    (OUT/"occurrence_counts.json").write_text(json.dumps(counts,indent=2))
    # Complete pre-migration runtime, separate from every existing archive.
    # Set frozen to OUT joined with the path segment 'pre_migration_runtime'.
    frozen = OUT/"pre_migration_runtime"
    # Iterate over the result of BASE.rglob(the text '*'), binding each item to p.
    for p in BASE.rglob("*"):
        # Run this branch when the negation of whether p is an existing file or a set built from
        # p.relative_to(BASE).parts intersected with a set containing the text 'results', the text '__pycache__',
        # the text '.pytest_cache', the text '.git'.
        if not p.is_file() or set(p.relative_to(BASE).parts)&{"results","__pycache__",".pytest_cache",".git"}:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Run this branch when p.suffix does not belong to a set containing the text '.py', the text '.json', the
        # text '.xml', the text '.onnx', the text '.npz'.
        if p.suffix not in {".py",".json",".xml",".onnx",".npz"}:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set target to frozen divided by the result of p.relative_to(BASE).
        target=frozen/p.relative_to(BASE)
        # Create the directory requested by target.parent.
        target.parent.mkdir(parents=True,exist_ok=True)
        # Call shutil.copy2 with the supplied arguments.
        shutil.copy2(p,target)
    # Set policy to the result of Path(the text 'results/final_mappo_selection_v2/selected_policy.pt').
    policy=Path("results/final_mappo_selection_v2/selected_policy.pt")
    # Create the directory requested by (frozen / policy).parent.
    (frozen/policy).parent.mkdir(parents=True,exist_ok=True)
    # Call shutil.copy2 with the supplied arguments.
    shutil.copy2(BASE/policy,frozen/policy)
    # Set saved to a dictionary of a string built from the result of p.relative_to(frozen) mapped to the result of
    # sha(p) for p in the result of frozen.rglob(the text '*'); retain entries satisfying whether p is an existing
    # file.
    saved={str(p.relative_to(frozen)):sha(p) for p in frozen.rglob("*") if p.is_file()}
    # Write the supplied text to (OUT / 'runtime_inventory.json').
    (OUT/"runtime_inventory.json").write_text(json.dumps(saved,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({"occurrences":counts,"historical_files":len(inventory),"archived_runtime_files":len(saved)},indent=2),flush=True)

# Renamed using the inputs and processing steps below.
# Input text: the supplied text.
# Output: text.
# Processing: iterate over the relevant records.
def renamed(text):
    # Iterate over key/value pairs from TOKENS, binding each item to (old, new).
    for old,new in TOKENS.items():
        # Set text to the result of text.replace(old, new).
        text=text.replace(old,new)
    # Iterate over key/value pairs from LABELS, binding each item to (old, new).
    for old,new in LABELS.items():
        # Set text to the result of text.replace(old, new).
        text=text.replace(old,new)
    # Iterate over the result of {'PANEL_VALIDATION_GUIDE': 'TARGETED_VALIDATION_GUIDE',
    # 'FINAL_EVALUATION_GUIDE':...(), binding each item to (old, new).
    for old,new in {"PANEL_VALIDATION_GUIDE":"TARGETED_VALIDATION_GUIDE","FINAL_EVALUATION_GUIDE":"POST_TRAINING_EVALUATION_GUIDE","FINAL_EVALUATION_SCOPE":"POST_TRAINING_EVALUATION_SCOPE"}.items():
        # Set text to the result of text.replace(old, new).
        text=text.replace(old,new)
    # Return text to the caller.
    return text

# Move using the inputs and processing steps below.
# Input old: the supplied old.
# Input new: the supplied new.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def move(old,new):
    # Set (src, dst) to a tuple containing WORKSPACE divided by old, WORKSPACE divided by new.
    src,dst=WORKSPACE/old,WORKSPACE/new
    # Run this branch when the negation of whether src exists.
    if not src.exists():
        # Return no value to the caller.
        return
    # Set indexed to the result of subprocess.run(['git', 'ls-files', '--', str(src)], cwd=WORKSPACE,
    # capture_output=True,...().
    indexed=subprocess.run(["git","ls-files","--",str(src)],cwd=WORKSPACE,capture_output=True,text=True,check=True).stdout.strip()
    # Run this branch when indexed.
    if indexed:
        # Call subprocess.run with the supplied arguments.
        subprocess.run(["git","mv",str(src),str(dst)],cwd=WORKSPACE,check=True)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Call src.rename with the supplied arguments.
        src.rename(dst)

# Migrate using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def migrate():
    # Run this branch when the negation of whether (OUT / 'historical_inventory.json') exists.
    if not (OUT/"historical_inventory.json").exists():
        # Raise RuntimeError with the text 'AUDIT_FIRST' to stop this execution path.
        raise RuntimeError("AUDIT_FIRST")
    # Set edits to an empty list.
    edits=[]
    # Iterate over the result of active_files(), binding each item to path.
    for path in active_files():
        # Immutable/generated audit JSONs and scenario definitions are not edited.
        # Run this branch when path.suffix does not belong to a set containing the text '.py', the text '.md', the
        # text '.txt', the text '.toml', the text '.ini', the text '.cfg'.
        if path.suffix not in {".py",".md",".txt",".toml",".ini",".cfg"}:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set old to the bytes read from path.
        old=path.read_bytes()
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set text to the result of old.decode(the text 'utf-8-sig').
            text=old.decode("utf-8-sig")
        # Handle UnicodeDecodeError using the recovery steps below.
        except UnicodeDecodeError:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set updated to the result of renamed(text).
        updated=renamed(text)
        # Run this branch when updated differs from text.
        if updated!=text:
            # Write the supplied bytes to path.
            path.write_bytes(updated.encode("utf-8"))
            # Append a string built from the result of path.relative_to(WORKSPACE) to edits.
            edits.append(str(path.relative_to(WORKSPACE)))
    # Set moves to an empty list.
    moves=[]
    # Set prefix to the text 'component_2_right_of_way_negotiation/'.
    prefix="component_2_right_of_way_negotiation/"
    # Set pairs to a list of a tuple containing prefix plus old, prefix plus new for (old, new) in a tuple
    # containing a tuple containing the text 'panel_demo', the text 'runtime_simulation', a tuple containing the
    # text...
    pairs=[(prefix+old,prefix+new) for old,new in (
        # Include a tuple containing the text 'final_evaluation', the text 'post_training_evaluation' in this
        # tuple.
        ("panel_demo","runtime_simulation"),("panel_validation","targeted_validation"),("final_evaluation","post_training_evaluation"),
        # Include a tuple containing the text 'run_final_evaluation.py', the text
        # 'run_post_training_evaluation.py' in this tuple.
        ("run_panel_demo.py","run_runtime_simulation.py"),("run_panel_validation.py","run_targeted_validation.py"),("run_final_evaluation.py","run_post_training_evaluation.py"),
        # Include a tuple containing the text 'tests/test_final_evaluation.py', the text
        # 'tests/test_post_training_evaluation.py' in this tuple.
        ("tests/test_panel_demo.py","tests/test_runtime_simulation.py"),("tests/test_panel_validation.py","tests/test_targeted_validation.py"),("tests/test_final_evaluation.py","tests/test_post_training_evaluation.py"),
        # Include a tuple containing the text 'docs/FINAL_EVALUATION_GUIDE.md', the text
        # 'docs/POST_TRAINING_EVALUATION_GUIDE.md' in this tuple.
        ("docs/PANEL_VALIDATION_GUIDE.md","docs/TARGETED_VALIDATION_GUIDE.md"),("docs/FINAL_EVALUATION_GUIDE.md","docs/POST_TRAINING_EVALUATION_GUIDE.md"),("docs/FINAL_EVALUATION_SCOPE.md","docs/POST_TRAINING_EVALUATION_SCOPE.md"))]
    # Update pairs to its current value plus a list of a tuple containing the text 'socialmind_drive_showcase/'
    # plus old, the text 'socialmind_drive_showcase/' plus new for (old, new) in a tuple containing a tuple
    # containing the text 'pages/component2_panel_validation.py', the text...
    pairs += [("socialmind_drive_showcase/"+old,"socialmind_drive_showcase/"+new) for old,new in (
        # Include a tuple containing the text 'pages/component2_panel_validation.py', the text
        # 'pages/component2_targeted_validation.py' in this tuple.
        ("pages/component2_panel_validation.py","pages/component2_targeted_validation.py"),
        # Include a tuple containing the text 'services/panel_validation_reader.py', the text
        # 'services/targeted_validation_reader.py' in this tuple.
        ("services/panel_validation_reader.py","services/targeted_validation_reader.py"),
        # Include a tuple containing the text 'tests/test_panel_validation_reader.py', the text
        # 'tests/test_targeted_validation_reader.py' in this tuple.
        ("tests/test_panel_validation_reader.py","tests/test_targeted_validation_reader.py"))]
    # Iterate over pairs, binding each item to (old, new).
    for old,new in pairs:
        # Run this branch when whether (WORKSPACE / old) exists.
        if (WORKSPACE/old).exists():
            # Call move with the supplied arguments.
            # Append a list containing old, new to moves.
            move(old,new);moves.append([old,new])
    # Write the supplied text to (OUT / 'migration_files.json').
    (OUT/"migration_files.json").write_text(json.dumps(dict(renames=moves,edited=edits),indent=2))
    # Display formatted text built from the embedded values.
    print(f"Renamed {len(moves)} paths; migrated {len(edits)} active text files.",flush=True)

# Run this branch when __name__ equals the text '__main__'.
if __name__=="__main__":
    # Import sys for use in this module.
    import sys
    # Call {'audit': audit, 'migrate': migrate}[sys.argv[1]] with the supplied arguments.
    {"audit":audit,"migrate":migrate}[sys.argv[1]]()
