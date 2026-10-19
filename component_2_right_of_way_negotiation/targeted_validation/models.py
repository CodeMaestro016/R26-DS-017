"""Immutable compact design and checksum-verified recorded evidence."""
import json
import platform
from pathlib import Path
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
from post_training_evaluation.models import (digest, file_hash, write_json, POLICY,
    EXPECTED_POLICY_HASH, CONTROLLER_VERSION, SHIELD_VERSION)
from post_training_evaluation.scenarios import source_identities, sumo_version
from .cases import frozen_cases

ROOT = Path("results/targeted_validation/v2")
V1_ROOT = Path("results/panel_validation/v1")  # Immutable historical location.
EVIDENCE = "TARGETED_PANEL_VALIDATION"
PROTOCOL = "TARGETED_PANEL_VALIDATION_V2"
SCOPE = "One selected unsignalized four-way SUMO intersection; AV-only, one incoming lane per approach, 12 legal movements, ideal same-step messages, <=4 physical queue-head negotiators; up to 16 total traffic vehicles."
METRIC_DEFINITIONS = {
    "completion": "Vehicles leaving the network / scheduled vehicles; unfinished trips remain visible.",
    "safety": "Observed simulator collisions and blocked-zone entry invariant violations.",
    "waiting": "Observed time below the existing 0.5 m/s threshold on incoming lanes, including followers. Unfinished waits are lower bounds; unspawned demand is N/A.",
    "TTT": "Sum of scheduled-demand time until network exit or the actual evaluator stop; unfinished demand is censored, so early-stop exposure is not full-budget travel time.",
    "throughput": "Completed vehicles per observed simulated minute; compare alongside stop time and completion.",
    "approach_gap": "Largest minus smallest N/E/S/W mean incoming wait; N/A unless all approaches are observed. No combined fairness score.",
    "inversion": "Fraction of physically conflicting, different-approach served pairs whose service order differs from arrival order; N/A without eligible served pairs.",
    "fallback_rate": "MAPPO epochs requiring safety fallback / MAPPO epochs; N/A with no MAPPO epochs. A fallback is not direct MAPPO success.",
    "scalability": "Measured maximum live/moving vehicles, incoming queue depth per approach, and simultaneous negotiating participants.",
    "architecture": "Runtime guard counts training, backward, optimizer, parameter changes, critic calls and centralized execution attempts; checks unchanged E5 and <=4 negotiators.",
}

def panel_sources():
    base = Path(__file__).resolve().parents[1]
    paths = list((base / "targeted_validation").glob("*.py"))
    return {str(p.relative_to(base)).replace("\\", "/"): file_hash(p) for p in sorted(paths)}

def design():
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    return dict(protocol_id=PROTOCOL, evidence_classification=EVIDENCE, schema_version=1,
        scope=SCOPE, cases=frozen_cases(), traffic_episode_count=7,
        validation_version="PANEL_VALIDATION_V2", parent_evidence="PANEL_VALIDATION_V1 remains immutable; critical V1 results are historical evidence, not newly executed V2 episodes.",
        nominal_design_rationale="Predeclared three initial left turns and West offset 6 s, continuous 1.5-s demand, all 12 movements. Avoid the known initial N-straight/S-right reciprocal claim condition; no guarantees of PASS or MAPPO invocation.",
        maximum_simulated_seconds=750., source_identities=source_identities(),
        panel_source_identities=panel_sources(), policy_sha256=file_hash(POLICY),
        controller_version=CONTROLLER_VERSION, shield_version=SHIELD_VERSION,
        inference_mode="SEEDED_STOCHASTIC_MASKED_SAMPLE", python_version=platform.python_version(),
        sumo_version=sumo_version(), metric_definitions=METRIC_DEFINITIONS,
        early_stop=dict(deadlock_duration_seconds=DEADLOCK_DURATION_SECONDS,
            stopped_speed_threshold_mps=STOPPED_SPEED_THRESHOLD_MPS,
            rule="Existing telemetry deadlock AND all scheduled demand spawned AND every active vehicle incoming/stopped AND stable held decisions/coordination for the existing duration; no admitted/clearing vehicle or future demand."),
        action_seed_derivation="Existing SHA256(protocol_id, scenario_id, demand_seed=None, method) modulo 2**31; SUMO seed=0.",
        data_provenance="Real-world trajectory data supports the intention-model component, while right-of-way system validation in this study is simulation-based.")

def prepare(root=ROOT):
    root = Path(root)
    legacy = Path("results/panel_validation").resolve()
    if root.resolve() == legacy or legacy in root.resolve().parents:
        raise RuntimeError("PANEL_V1_READ_ONLY: use archived replay or the separate V2 root")
    current = json.loads(json.dumps(design()))
    path = root / "manifest.json"
    if path.exists():
        saved = read_checked_manifest(root)
        if saved["manifest"] != current:
            raise RuntimeError("PANEL_MANIFEST_CHANGED: restore frozen sources or choose a NEW --output-root version")
        return saved
    frozen = dict(manifest=current, manifest_hash=digest(current))
    write_json(path, frozen, exclusive=True)
    return frozen

def read_checked_manifest(root=ROOT):
    saved = json.loads((Path(root) / "manifest.json").read_text(encoding="utf-8"))
    if saved["manifest_hash"] != digest(saved["manifest"]):
        raise RuntimeError("PANEL_MANIFEST_CHECKSUM_MISMATCH")
    return saved

def records(root=ROOT, suite="panel"):
    frozen = read_checked_manifest(root)
    values = []
    for path in sorted((Path(root) / "runs").glob("*/result.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["suite"] != suite:
            continue
        if digest(record) != json.loads(path.with_name("result.sha256.json").read_text())["result_hash"]:
            raise RuntimeError("PANEL_RESULT_CHECKSUM_MISMATCH")
        provenance = json.loads(path.with_name("provenance.json").read_text())
        if digest(provenance) != json.loads(path.with_name("provenance.sha256.json").read_text())["provenance_hash"]:
            raise RuntimeError("PANEL_PROVENANCE_CHECKSUM_MISMATCH")
        if record["manifest_hash"] != frozen["manifest_hash"] or provenance["manifest_hash"] != frozen["manifest_hash"]:
            raise RuntimeError("PANEL_RESULT_MANIFEST_MISMATCH")
        if digest(provenance["schedule"]) != record["schedule_hash"] or record["schedule_hash"] != provenance["schedule_hash"]:
            raise RuntimeError("PANEL_DEMAND_CHECKSUM_MISMATCH")
        for name, expected in record.get("artifact_sha256", {}).items():
            if Path(name).name != name or file_hash(path.parent / name) != expected:
                raise RuntimeError("PANEL_ARTIFACT_CHECKSUM_MISMATCH")
        values.append(record)
    return values

def latest(root=ROOT):
    root = Path(root)
    return root / "latest"  # Do not overwrite the global latest report containing V1.
