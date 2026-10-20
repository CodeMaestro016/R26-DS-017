"""Immutable compact design and checksum-verified recorded evidence."""
# Import json for use in this module.
import json
# Import platform for use in this module.
import platform
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS from config for the operations below.
from config import DEADLOCK_DURATION_SECONDS, STOPPED_SPEED_THRESHOLD_MPS
# Import digest, file_hash, write_json, POLICY, EXPECTED_POLICY_HASH, CONTROLLER_VERSION, SHIELD_VERSION from
# post_training_evaluation.models for the operations below.
from post_training_evaluation.models import (digest, file_hash, write_json, POLICY,
    EXPECTED_POLICY_HASH, CONTROLLER_VERSION, SHIELD_VERSION)
# Import source_identities, sumo_version from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import source_identities, sumo_version
# Import frozen_cases from .cases for the operations below.
from .cases import frozen_cases

# Set ROOT to the result of Path(the text 'results/targeted_validation/v2').
ROOT = Path("results/targeted_validation/v2")
# Set V1_ROOT to the result of Path(the text 'results/panel_validation/v1').
V1_ROOT = Path("results/panel_validation/v1")  # Immutable historical location.
# Set EVIDENCE to the text 'TARGETED_PANEL_VALIDATION'.
EVIDENCE = "TARGETED_PANEL_VALIDATION"
# Set PROTOCOL to the text 'TARGETED_PANEL_VALIDATION_V2'.
PROTOCOL = "TARGETED_PANEL_VALIDATION_V2"
# Set SCOPE to the text 'One selected unsignalized four-way SUMO intersection;...'.
SCOPE = "One selected unsignalized four-way SUMO intersection; AV-only, one incoming lane per approach, 12 legal movements, ideal same-step messages, <=4 physical queue-head negotiators; up to 16 total traffic vehicles."
# Set METRIC_DEFINITIONS to a dictionary containing completion, safety, waiting, TTT, throughput, approach_gap,
# inversion, fallback_rate,...
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

# Panel sources using the inputs and processing steps below.
# Output: a dictionary of the result of str(p.relative_to(base)).replace(the text '\\', the text '/') mapped to
# the result of file_hash(p) for p in the sorted values from paths.
def panel_sources():
    # Set base to Path(__file__).resolve().parents at 1.
    base = Path(__file__).resolve().parents[1]
    # Set paths to a list built from the result of (base / 'targeted_validation').glob(the text '*.py').
    paths = list((base / "targeted_validation").glob("*.py"))
    # Return a dictionary of the result of str(p.relative_to(base)).replace(the text '\\', the text '/') mapped to
    # the result of file_hash(p) for p in the sorted values from paths to the caller.
    return {str(p.relative_to(base)).replace("\\", "/"): file_hash(p) for p in sorted(paths)}

# Design using the inputs and processing steps below.
# Output: a dictionary built from the supplied values.
# Processing: select branches using the stated conditions.
def design():
    # Run this branch when the result of file_hash(POLICY) differs from EXPECTED_POLICY_HASH.
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        # Raise RuntimeError with the text 'FROZEN_E5_CHECKPOINT_MISMATCH' to stop this execution path.
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    # Return a dictionary built from the supplied values to the caller.
    return dict(protocol_id=PROTOCOL, evidence_classification=EVIDENCE, schema_version=1,
        # Supply scope as SCOPE.
        # Supply cases as the result of frozen_cases().
        # Supply traffic_episode_count as 7.
        scope=SCOPE, cases=frozen_cases(), traffic_episode_count=7,
        # Supply validation_version as the text 'PANEL_VALIDATION_V2'.
        # Supply parent_evidence as the text 'PANEL_VALIDATION_V1 remains immutable; critical V1 results...'.
        validation_version="PANEL_VALIDATION_V2", parent_evidence="PANEL_VALIDATION_V1 remains immutable; critical V1 results are historical evidence, not newly executed V2 episodes.",
        # Supply nominal_design_rationale as the text 'Predeclared three initial left turns and West offset 6
        # s,...'.
        nominal_design_rationale="Predeclared three initial left turns and West offset 6 s, continuous 1.5-s demand, all 12 movements. Avoid the known initial N-straight/S-right reciprocal claim condition; no guarantees of PASS or MAPPO invocation.",
        # Supply maximum_simulated_seconds as 750.0.
        # Supply source_identities as the result of source_identities().
        maximum_simulated_seconds=750., source_identities=source_identities(),
        # Supply panel_source_identities as the result of panel_sources().
        # Supply policy_sha256 as the result of file_hash(POLICY).
        panel_source_identities=panel_sources(), policy_sha256=file_hash(POLICY),
        # Supply controller_version as CONTROLLER_VERSION.
        # Supply shield_version as SHIELD_VERSION.
        controller_version=CONTROLLER_VERSION, shield_version=SHIELD_VERSION,
        # Supply inference_mode as the text 'SEEDED_STOCHASTIC_MASKED_SAMPLE'.
        # Supply python_version as the result of platform.python_version().
        inference_mode="SEEDED_STOCHASTIC_MASKED_SAMPLE", python_version=platform.python_version(),
        # Supply sumo_version as the result of sumo_version().
        # Supply metric_definitions as METRIC_DEFINITIONS.
        sumo_version=sumo_version(), metric_definitions=METRIC_DEFINITIONS,
        # Supply early_stop as a dictionary built from the supplied values.
        # Supply deadlock_duration_seconds as DEADLOCK_DURATION_SECONDS.
        early_stop=dict(deadlock_duration_seconds=DEADLOCK_DURATION_SECONDS,
            # Supply stopped_speed_threshold_mps as STOPPED_SPEED_THRESHOLD_MPS.
            stopped_speed_threshold_mps=STOPPED_SPEED_THRESHOLD_MPS,
            # Supply rule as the text 'Existing telemetry deadlock AND all scheduled demand spawned...'.
            rule="Existing telemetry deadlock AND all scheduled demand spawned AND every active vehicle incoming/stopped AND stable held decisions/coordination for the existing duration; no admitted/clearing vehicle or future demand."),
        # Supply action_seed_derivation as the text 'Existing SHA256(protocol_id, scenario_id,
        # demand_seed=None,...'.
        action_seed_derivation="Existing SHA256(protocol_id, scenario_id, demand_seed=None, method) modulo 2**31; SUMO seed=0.",
        # Supply data_provenance as the text 'Real-world trajectory data supports the intention-model...'.
        data_provenance="Real-world trajectory data supports the intention-model component, while right-of-way system validation in this study is simulation-based.")

# Prepare using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def prepare(root=ROOT):
    # Set root to the result of Path(root).
    root = Path(root)
    # Set legacy to the result of Path('results/panel_validation').resolve().
    legacy = Path("results/panel_validation").resolve()
    # Run this branch when the result of root.resolve() equals legacy or legacy belongs to root.resolve().parents.
    if root.resolve() == legacy or legacy in root.resolve().parents:
        # Raise RuntimeError with the text 'PANEL_V1_READ_ONLY: use archived replay or the separate V2 root' to
        # stop this execution path.
        raise RuntimeError("PANEL_V1_READ_ONLY: use archived replay or the separate V2 root")
    # Set current to the decoded data produced by json.loads from the serialized data produced by json.dumps.
    current = json.loads(json.dumps(design()))
    # Set path to root joined with the path segment 'manifest.json'.
    path = root / "manifest.json"
    # Run this branch when whether path exists.
    if path.exists():
        # Set saved to the result of read_checked_manifest(root).
        saved = read_checked_manifest(root)
        # Run this branch when saved at 'manifest' differs from current.
        if saved["manifest"] != current:
            # Raise RuntimeError with the text 'PANEL_MANIFEST_CHANGED: restore frozen sources or choose a...' to
            # stop this execution path.
            raise RuntimeError("PANEL_MANIFEST_CHANGED: restore frozen sources or choose a NEW --output-root version")
        # Return saved to the caller.
        return saved
    # Set frozen to a dictionary built from the supplied values.
    frozen = dict(manifest=current, manifest_hash=digest(current))
    # Call write_json with the supplied arguments.
    write_json(path, frozen, exclusive=True)
    # Return frozen to the caller.
    return frozen

# Read checked manifest using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: saved.
# Processing: select branches using the stated conditions.
def read_checked_manifest(root=ROOT):
    # Set saved to the decoded data produced by json.loads from the text read from (Path(root) / 'manifest.json').
    saved = json.loads((Path(root) / "manifest.json").read_text(encoding="utf-8"))
    # Run this branch when saved at 'manifest_hash' differs from the result of digest(saved at 'manifest').
    if saved["manifest_hash"] != digest(saved["manifest"]):
        # Raise RuntimeError with the text 'PANEL_MANIFEST_CHECKSUM_MISMATCH' to stop this execution path.
        raise RuntimeError("PANEL_MANIFEST_CHECKSUM_MISMATCH")
    # Return saved to the caller.
    return saved

# Records using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Output: values.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def records(root=ROOT, suite="panel"):
    # Set frozen to the result of read_checked_manifest(root).
    frozen = read_checked_manifest(root)
    # Set values to an empty list.
    values = []
    # Iterate over the sorted values from the result of (Path(root) / 'runs').glob(the text '*/result.json'),
    # binding each item to path.
    for path in sorted((Path(root) / "runs").glob("*/result.json")):
        # Set record to the decoded data produced by json.loads from the text read from path.
        record = json.loads(path.read_text(encoding="utf-8"))
        # Run this branch when record at 'suite' differs from suite.
        if record["suite"] != suite:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Run this branch when the result of digest(record) differs from
        # json.loads(path.with_name('result.sha256.json').read_text()) at 'result_hash'.
        if digest(record) != json.loads(path.with_name("result.sha256.json").read_text())["result_hash"]:
            # Raise RuntimeError with the text 'PANEL_RESULT_CHECKSUM_MISMATCH' to stop this execution path.
            raise RuntimeError("PANEL_RESULT_CHECKSUM_MISMATCH")
        # Set provenance to the decoded data produced by json.loads from the text read from
        # path.with_name('provenance.json').
        provenance = json.loads(path.with_name("provenance.json").read_text())
        # Run this branch when the result of digest(provenance) differs from
        # json.loads(path.with_name('provenance.sha256.json').read_text()) at 'provenance_hash'.
        if digest(provenance) != json.loads(path.with_name("provenance.sha256.json").read_text())["provenance_hash"]:
            # Raise RuntimeError with the text 'PANEL_PROVENANCE_CHECKSUM_MISMATCH' to stop this execution path.
            raise RuntimeError("PANEL_PROVENANCE_CHECKSUM_MISMATCH")
        # Run this branch when record at 'manifest_hash' differs from frozen at 'manifest_hash' or provenance at
        # 'manifest_hash' differs from frozen at 'manifest_hash'.
        if record["manifest_hash"] != frozen["manifest_hash"] or provenance["manifest_hash"] != frozen["manifest_hash"]:
            # Raise RuntimeError with the text 'PANEL_RESULT_MANIFEST_MISMATCH' to stop this execution path.
            raise RuntimeError("PANEL_RESULT_MANIFEST_MISMATCH")
        # Run this branch when the result of digest(provenance at 'schedule') differs from record at
        # 'schedule_hash' or record at 'schedule_hash' differs from provenance at 'schedule_hash'.
        if digest(provenance["schedule"]) != record["schedule_hash"] or record["schedule_hash"] != provenance["schedule_hash"]:
            # Raise RuntimeError with the text 'PANEL_DEMAND_CHECKSUM_MISMATCH' to stop this execution path.
            raise RuntimeError("PANEL_DEMAND_CHECKSUM_MISMATCH")
        # Iterate over key/value pairs from record.get('artifact_sha256', {}), binding each item to (name,
        # expected).
        for name, expected in record.get("artifact_sha256", {}).items():
            # Run this branch when Path(name).name differs from name or the result of file_hash(path.parent
            # divided by name) differs from expected.
            if Path(name).name != name or file_hash(path.parent / name) != expected:
                # Raise RuntimeError with the text 'PANEL_ARTIFACT_CHECKSUM_MISMATCH' to stop this execution path.
                raise RuntimeError("PANEL_ARTIFACT_CHECKSUM_MISMATCH")
        # Append record to values.
        values.append(record)
    # Return values to the caller.
    return values

# Latest using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: root joined with the path segment 'latest'.
def latest(root=ROOT):
    # Set root to the result of Path(root).
    root = Path(root)
    # Return root joined with the path segment 'latest' to the caller.
    return root / "latest"  # Do not overwrite the global latest report containing V1.
