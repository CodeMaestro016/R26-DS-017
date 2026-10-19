"""Read archived aggregate outputs only; never import simulation/evaluation code."""
import json
import hashlib
from collections import Counter
from pathlib import Path
from socialmind_drive_showcase.config import COMPONENT2_ROOT

EVALUATION_ROOT = COMPONENT2_ROOT / "results/post_training_evaluation/v2_candidate/latest"

def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def verify_archive(root):
    """Verify metadata and counts only; never calculate scientific statistics."""
    path = Path(root) / "manifest.json"
    if not path.is_file():
        return {"available":False, "message":"No adjacent frozen manifest; archived episode verification unavailable."}
    try:
        frozen = json.loads(path.read_text(encoding="utf-8"))
        manifest = frozen["manifest"]
        if _digest(manifest) != frozen["manifest_hash"]:
            raise ValueError("Manifest checksum mismatch")
        expected = {(s["scenario_id"],seed,method) for s in manifest["scenarios"]
            for seed in (manifest["seeds"] if s["continuous"] else (None,))
            for method in manifest["methods"]}
        verified, problems, seen = [], [], set()
        for result_path in sorted((Path(root)/"runs").glob("*/result.json")):
            try:
                record = json.loads(result_path.read_text(encoding="utf-8"))
                if record["suite"] != "final":
                    continue
                provenance = json.loads(result_path.with_name("provenance.json").read_text())
                checks = ((_digest(record),json.loads(result_path.with_name("result.sha256.json").read_text())["result_hash"]),
                    (_digest(provenance),json.loads(result_path.with_name("provenance.sha256.json").read_text())["provenance_hash"]))
                if any(a != b for a,b in checks) or record["manifest_hash"] != frozen["manifest_hash"] or provenance["manifest_hash"] != frozen["manifest_hash"]:
                    raise ValueError("Episode/provenance/manifest checksum mismatch")
                if _digest(provenance["schedule"]) != record["schedule_hash"] or provenance["schedule_hash"] != record["schedule_hash"]:
                    raise ValueError("Demand checksum mismatch")
                for name, expected_hash in record.get("artifact_sha256", {}).items():
                    if Path(name).name != name:
                        raise ValueError("Invalid artifact path")
                    with result_path.with_name(name).open("rb") as artifact:
                        if hashlib.file_digest(artifact,"sha256").hexdigest() != expected_hash:
                            raise ValueError("Artifact checksum mismatch")
                key = (record["scenario_id"],record["seed"],record["method"])
                if key not in expected or key in seen:
                    raise ValueError("Unexpected or duplicate final episode key")
                seen.add(key)
                verified.append(record)
            except (OSError,ValueError,TypeError,KeyError) as error:
                problems.append(str(result_path)+": "+str(error))
        unfinished = [str(directory) for directory in (Path(root)/"runs").glob("*")
            if directory.is_dir() and not (directory/"result.json").is_file()]
        if unfinished:
            problems.append("Unfinished archive directories retained: " + str(unfinished))
        return {"available":True, "protocol_id":manifest["protocol_id"],
            "manifest_hash":frozen["manifest_hash"], "expected":len(expected),
            "verified":len(verified), "missing":len(expected-seen),
            "complete":seen==expected and not problems,
            "classification_counts":dict(Counter(r["classification"] for r in verified)),
            "verification_errors":problems, "runs":verified,
            "unfinished_archive_directories":unfinished,
            "source_root":str(root), "interpretation":"Checksum-verified archived records; not an accepted V2 study or proof of runtime generalization."}
    except (OSError,ValueError,TypeError,KeyError) as error:
        return {"available":False, "message":"Archive verification unavailable: "+str(error)}

def read_evaluation(path=None):
    target = Path(path) if path is not None else EVALUATION_ROOT / "aggregate.json"
    if path is None and not target.is_file():
        target = COMPONENT2_ROOT / "results/final_evaluation/v2_candidate/latest/aggregate.json"
    if path is None and not target.is_file():
        target = COMPONENT2_ROOT / "results/final_evaluation/latest/aggregate.json"
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("groups"), list):
            raise ValueError("Unsupported evaluation aggregate")
        verification = verify_archive(target.parent.parent)
        return {"available": True, "payload": payload, "verification":verification,
            "source_path":str(target), "plots_root":target.parent/"plots"}
    except (OSError, ValueError, TypeError) as error:
        return {"available": False, "message": "Quantitative evaluation outputs are not available: " + str(error)}
