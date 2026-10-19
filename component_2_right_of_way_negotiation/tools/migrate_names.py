"""One-time, audited source-only naming migration. Never edits results."""
import csv
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WORKSPACE = BASE.parent
OUT = BASE / "results/naming_migration"
TOKENS = {"run_panel_demo":"run_runtime_simulation", "run_panel_validation":"run_targeted_validation",
    "run_final_evaluation":"run_post_training_evaluation", "panel_demo":"runtime_simulation",
    "panel_validation":"targeted_validation", "final_evaluation":"post_training_evaluation",
    "PANEL_VALIDATION_REPORT":"TARGETED_VALIDATION_REPORT",
    "PANEL_EVALUATION_REPORT":"POST_TRAINING_EVALUATION_REPORT"}
LABELS = {"Panel Demo":"Runtime Simulation", "Panel Validation":"Targeted Validation",
    "Final Evaluation":"Post-Training Evaluation", "Scalability Validation":"Scalability Evaluation",
    "PANEL DEMO SUMMARY":"RUNTIME SIMULATION SUMMARY"}
PATTERN = re.compile("|".join(map(re.escape,TOKENS)))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def category(path):
    parts = path.relative_to(WORKSPACE).parts
    if "results" in parts:
        return "F immutable historical evidence/archive"
    if "tests" in parts:
        return "B active test"
    if "socialmind_drive_showcase" in parts and path.suffix==".py":
        return "D active showcase/UI"
    if path.suffix==".md":
        return "C active documentation"
    if path.suffix not in {".py"}:
        return "E generated current-path reference"
    return "A active source/import"

def active_files():
    candidates = [WORKSPACE/"README.md"]
    for folder in (BASE,WORKSPACE/"socialmind_drive_showcase"):
        candidates += [p for p in folder.rglob("*") if p.is_file() and p.suffix in {".py",".md",".json",".toml",".txt",".ini",".cfg"}
            and not set(p.relative_to(folder).parts)&{"results","__pycache__",".pytest_cache",".git",".venv"}]
    return [p for p in candidates if p != Path(__file__) ]

def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    inventory = {}
    counts = {}
    with (OUT/"occurrences.csv").open("x",newline="",encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category","path","line","term"])
        files = active_files()+list((BASE/"results").rglob("*"))
        for p in files:
            if not p.is_file() or OUT in p.parents:
                continue
            group = category(p)
            if group.startswith("F"):
                inventory[str(p.relative_to(BASE))]=sha(p)
            if p.suffix not in {".py",".md",".json",".jsonl",".txt",".html",".csv",".toml",".ini",".cfg"}:
                continue
            with p.open(encoding="utf-8-sig",errors="replace") as source:
                for line_number,line in enumerate(source,1):
                    for hit in PATTERN.finditer(line):
                        writer.writerow([group,str(p.relative_to(WORKSPACE)),line_number,hit.group()])
                        counts[group]=counts.get(group,0)+1
    (OUT/"historical_inventory.json").write_text(json.dumps(inventory,indent=2))
    before={str(p.relative_to(WORKSPACE)):sha(p) for p in active_files()}
    (OUT/"active_inventory.json").write_text(json.dumps(before,indent=2))
    (OUT/"occurrence_counts.json").write_text(json.dumps(counts,indent=2))
    # Complete pre-migration runtime, separate from every existing archive.
    frozen = OUT/"pre_migration_runtime"
    for p in BASE.rglob("*"):
        if not p.is_file() or set(p.relative_to(BASE).parts)&{"results","__pycache__",".pytest_cache",".git"}:
            continue
        if p.suffix not in {".py",".json",".xml",".onnx",".npz"}:
            continue
        target=frozen/p.relative_to(BASE)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
    policy=Path("results/final_mappo_selection_v2/selected_policy.pt")
    (frozen/policy).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(BASE/policy,frozen/policy)
    saved={str(p.relative_to(frozen)):sha(p) for p in frozen.rglob("*") if p.is_file()}
    (OUT/"runtime_inventory.json").write_text(json.dumps(saved,indent=2))
    print(json.dumps({"occurrences":counts,"historical_files":len(inventory),"archived_runtime_files":len(saved)},indent=2),flush=True)

def renamed(text):
    for old,new in TOKENS.items():
        text=text.replace(old,new)
    for old,new in LABELS.items():
        text=text.replace(old,new)
    for old,new in {"PANEL_VALIDATION_GUIDE":"TARGETED_VALIDATION_GUIDE","FINAL_EVALUATION_GUIDE":"POST_TRAINING_EVALUATION_GUIDE","FINAL_EVALUATION_SCOPE":"POST_TRAINING_EVALUATION_SCOPE"}.items():
        text=text.replace(old,new)
    return text

def move(old,new):
    src,dst=WORKSPACE/old,WORKSPACE/new
    if not src.exists():
        return
    indexed=subprocess.run(["git","ls-files","--",str(src)],cwd=WORKSPACE,capture_output=True,text=True,check=True).stdout.strip()
    if indexed:
        subprocess.run(["git","mv",str(src),str(dst)],cwd=WORKSPACE,check=True)
    else:
        src.rename(dst)

def migrate():
    if not (OUT/"historical_inventory.json").exists():
        raise RuntimeError("AUDIT_FIRST")
    edits=[]
    for path in active_files():
        # Immutable/generated audit JSONs and scenario definitions are not edited.
        if path.suffix not in {".py",".md",".txt",".toml",".ini",".cfg"}:
            continue
        old=path.read_bytes()
        try:
            text=old.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        updated=renamed(text)
        if updated!=text:
            path.write_bytes(updated.encode("utf-8"))
            edits.append(str(path.relative_to(WORKSPACE)))
    moves=[]
    prefix="component_2_right_of_way_negotiation/"
    pairs=[(prefix+old,prefix+new) for old,new in (
        ("panel_demo","runtime_simulation"),("panel_validation","targeted_validation"),("final_evaluation","post_training_evaluation"),
        ("run_panel_demo.py","run_runtime_simulation.py"),("run_panel_validation.py","run_targeted_validation.py"),("run_final_evaluation.py","run_post_training_evaluation.py"),
        ("tests/test_panel_demo.py","tests/test_runtime_simulation.py"),("tests/test_panel_validation.py","tests/test_targeted_validation.py"),("tests/test_final_evaluation.py","tests/test_post_training_evaluation.py"),
        ("docs/PANEL_VALIDATION_GUIDE.md","docs/TARGETED_VALIDATION_GUIDE.md"),("docs/FINAL_EVALUATION_GUIDE.md","docs/POST_TRAINING_EVALUATION_GUIDE.md"),("docs/FINAL_EVALUATION_SCOPE.md","docs/POST_TRAINING_EVALUATION_SCOPE.md"))]
    pairs += [("socialmind_drive_showcase/"+old,"socialmind_drive_showcase/"+new) for old,new in (
        ("pages/component2_panel_validation.py","pages/component2_targeted_validation.py"),
        ("services/panel_validation_reader.py","services/targeted_validation_reader.py"),
        ("tests/test_panel_validation_reader.py","tests/test_targeted_validation_reader.py"))]
    for old,new in pairs:
        if (WORKSPACE/old).exists():
            move(old,new);moves.append([old,new])
    (OUT/"migration_files.json").write_text(json.dumps(dict(renames=moves,edited=edits),indent=2))
    print(f"Renamed {len(moves)} paths; migrated {len(edits)} active text files.",flush=True)

if __name__=="__main__":
    import sys
    {"audit":audit,"migrate":migrate}[sys.argv[1]]()
