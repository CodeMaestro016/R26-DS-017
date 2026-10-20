"""Predeclared demand, independently generated without selection/held-out data."""
# Import dataclass, asdict from dataclasses for the operations below.
from dataclasses import dataclass, asdict
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import json for use in this module.
import json
# Import random for use in this module.
import random
# Import platform for use in this module.
import platform
# Import shutil for use in this module.
import shutil
# Import subprocess for use in this module.
import subprocess

# Import SUMO_CONFIG, SUMO_NETWORK_FILE, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS from config for the operations
# below.
from config import SUMO_CONFIG, SUMO_NETWORK_FILE, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import PanelDemand, APPROACH_PATHS from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import PanelDemand, APPROACH_PATHS
# Import SEEDS, METHODS, POLICY, EXPECTED_POLICY_HASH, ROOT, digest, file_hash, write_json, CONTROLLER_VERSION,
# SHIELD_VERSION from .models for the operations below.
from .models import SEEDS, METHODS, POLICY, EXPECTED_POLICY_HASH, ROOT, digest, file_hash, write_json, CONTROLLER_VERSION, SHIELD_VERSION

# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define Scenario to group the state and operations declared below.
# Declared fields: scenario_id, vehicle_count, headway_seconds, budget_seconds, continuous.
# Construction and attribute behavior follow the declared decorators and base classes.
class Scenario:
    # Declare scenario_id as str for this data structure.
    scenario_id: str
    # Declare vehicle_count as int for this data structure.
    vehicle_count: int
    # Declare headway_seconds as float for this data structure.
    headway_seconds: float
    # Declare budget_seconds as float for this data structure.
    budget_seconds: float
    # Declare continuous as bool for this data structure.
    continuous: bool

# Set FUNCTIONAL to a tuple built from a lazy sequence of the result of Scenario(name,
# get_scenario(name).vehicle_count, 0.0, 180.0, False) for name in a tuple containing the text
# 'rule_resolved_two', the text 'regulatory_cycle', the text 'multiple_left_turns', the text...
FUNCTIONAL = tuple(Scenario(name, get_scenario(name).vehicle_count, 0., 180., False)
    # Evaluate a tuple containing the text 'rule_resolved_two', the text 'regulatory_cycle', the text
    # 'multiple_left_turns', the text... as part of the enclosing expression.
    for name in ("rule_resolved_two", "regulatory_cycle", "multiple_left_turns",
                 "mixed_manoeuvres", "four_way_simultaneous"))
# Set CONTINUOUS to a tuple built from a lazy sequence of the result of Scenario(name, count, headway, budget,
# True) for (name, count, headway, budget) in a tuple containing a tuple containing 'normal', 8, 2.0, 240.0, a
# tuple containing 'congested', 12, 1.75, 300.0, a tuple...
CONTINUOUS = tuple(Scenario(name, count, headway, budget, True)
    # Evaluate a tuple containing a tuple containing the text 'normal', 8, 2.0, 240.0, a tuple containing the text
    # 'congested', 12, 1.75,... as part of the enclosing expression.
    for name, count, headway, budget in (
        # Include a tuple containing the text 'congested', 12, 1.75, 300.0 in this tuple.
        ("normal", 8, 2., 240.), ("congested", 12, 1.75, 300.),
        # Include a tuple containing the text 'dense', 16, 1.5, 360.0 in this tuple.
        ("dense", 16, 1.5, 360.), ("stress", 24, 1., 480.),
        # Include a tuple containing the text 'extreme_stress', 32, 0.75, 600.0 in this tuple.
        ("extreme_stress", 32, .75, 600.)))
# Set SCENARIOS to FUNCTIONAL plus CONTINUOUS.
SCENARIOS = FUNCTIONAL + CONTINUOUS
# Set SMOKE_BUDGET_SECONDS to 90.0.
SMOKE_BUDGET_SECONDS = 90.

# Demand using the inputs and processing steps below.
# Input scenario: the supplied scenario.
# Input seed: the random seed supplied to this operation.
# Output: return the value selected by the matching return branch below.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def demand(scenario, seed):
    # Run this branch when the negation of scenario.continuous.
    if not scenario.continuous:
        # Return the result of get_scenario(scenario.scenario_id).schedule() to the caller.
        return get_scenario(scenario.scenario_id).schedule()
    # Set rng to the result of random.Random(seed).
    rng = random.Random(seed)
    # Set result to an empty dictionary.
    result = {}
    # Iterate over the text 'NESW', binding each item to approach.
    for approach in "NESW":
        # Balanced shuffled blocks: each legal movement once per three vehicles.
        # Set choices to an empty list.
        choices = []
        # Repeat the following steps while the number of entries in choices is less than scenario.vehicle_count
        # integer-divided by 4.
        while len(choices) < scenario.vehicle_count // 4:
            # Set block to a list built from APPROACH_PATHS at approach.
            block = list(APPROACH_PATHS[approach])
            # Call rng.shuffle with the supplied arguments.
            rng.shuffle(block)
            # Extend choices with block.
            choices.extend(block)
        # Set result[approach] to a tuple built from a lazy sequence of the result of PanelDemand(approach, path,
        # index, index multiplied by scenario.headway_seconds) for (index, path) in index/value pairs from choices
        # sliced by :scenario.vehicle_count // 4.
        result[approach] = tuple(PanelDemand(approach, path, index,
            # Supply index multiplied by scenario.headway_seconds to PanelDemand.
            index * scenario.headway_seconds)
            # Evaluate index/value pairs from choices sliced by :scenario.vehicle_count // 4 as part of the
            # enclosing expression.
            for index, path in enumerate(choices[:scenario.vehicle_count // 4]))
    # Return result to the caller.
    return result

# Schedule payload using the inputs and processing steps below.
# Input schedule: the supplied schedule.
# Output: a dictionary of a mapped to a list of the result of asdict(x) for x in rows for (a, rows) in key/value
# pairs from schedule.
def schedule_payload(schedule):
    # Return a dictionary of a mapped to a list of the result of asdict(x) for x in rows for (a, rows) in
    # key/value pairs from schedule to the caller.
    return {a: [asdict(x) for x in rows] for a, rows in schedule.items()}

# Restore schedule using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: a dictionary of a mapped to a tuple built from a lazy sequence of the result of PanelDemand() for x in
# rows for (a, rows) in key/value pairs from payload.
def restore_schedule(payload):
    # Return a dictionary of a mapped to a tuple built from a lazy sequence of the result of PanelDemand() for x
    # in rows for (a, rows) in key/value pairs from payload to the caller.
    return {a: tuple(PanelDemand(**x) for x in rows) for a, rows in payload.items()}

# Source identities using the inputs and processing steps below.
# Output: a dictionary of the result of str(p.relative_to(root)).replace(the text '\\', the text '/') mapped to
# the result of file_hash(p) for p in the sorted values from a set built from paths;...
# Processing: iterate over the relevant records.
def source_identities():
    # Freeze the complete operational Python code, model assets, and SUMO inputs.
    # Set root to Path(__file__).resolve().parents at 1.
    root = Path(__file__).resolve().parents[1]
    # Set paths to a list built from the result of root.glob(the text '*.py').
    paths = list(root.glob("*.py"))
    # Iterate over a tuple containing the text 'post_training_evaluation', the text 'runtime_simulation', the text
    # 'negotiation_execution', the..., binding each item to directory.
    for directory in ("post_training_evaluation", "runtime_simulation", "negotiation_execution",
        "negotiation_learning", "negotiation_training", "conflict", "traffic_rules",
        "traffic_accounting", "negotiation_objective", "perception",
        "experimentation", "map_geometry", "negotiation_scenarios", "gui"):
        # Extend paths with the result of (root / directory).rglob(the text '*.py').
        paths.extend((root / directory).rglob("*.py"))
    # Extend paths with the result of (root / 'networks').glob(the text '*.xml').
    paths.extend((root / "networks").glob("*.xml"))
    # Extend paths with the result of (root / 'models').rglob(the text '*.onnx').
    paths.extend((root / "models").rglob("*.onnx"))
    # Extend paths with the result of (root / 'models' / 'intention').glob(the text '*.json').
    paths.extend((root / "models" / "intention").glob("*.json"))
    # Extend paths with the result of (root / 'models' / 'intention').glob(the text '*.npz').
    paths.extend((root / "models" / "intention").glob("*.npz"))
    # Extend paths with the result of (root / 'traffic_rules' / 'profiles').glob(the text '*.json').
    paths.extend((root / "traffic_rules" / "profiles").glob("*.json"))
    # Update paths to its current value plus a list containing SUMO_CONFIG, SUMO_NETWORK_FILE, root divided by the
    # text 'runtime_simulation/scenario_catalog.json'.
    paths += [SUMO_CONFIG, SUMO_NETWORK_FILE, root / "runtime_simulation/scenario_catalog.json"]
    # Return a dictionary of the result of str(p.relative_to(root)).replace(the text '\\', the text '/') mapped to
    # the result of file_hash(p) for p in the sorted values from a set built from paths; retain entries satisfying
    # whether p is an existing file to the caller.
    return {str(p.relative_to(root)).replace("\\", "/"): file_hash(p)
            # Evaluate the sorted values from a set built from paths as part of the enclosing expression.
            for p in sorted(set(paths)) if p.is_file()}

# Sumo version using the inputs and processing steps below.
# Output: subprocess.check_output([binary, '--version'], text=True).splitlines() at 0.
# Processing: select branches using the stated conditions.
def sumo_version():
    # Set binary to the result of shutil.which(the text 'sumo').
    binary = shutil.which("sumo")
    # Run this branch when the negation of binary.
    if not binary:
        # Raise RuntimeError with the text 'SUMO_NOT_ON_PATH' to stop this execution path.
        raise RuntimeError("SUMO_NOT_ON_PATH")
    # Return subprocess.check_output([binary, '--version'], text=True).splitlines() at 0 to the caller.
    return subprocess.check_output([binary, "--version"], text=True).splitlines()[0]

# Manifest using the inputs and processing steps below.
# Output: a dictionary containing protocol_id, code_and_configuration_sha256, controller_version,
# shield_version,...
# Processing: select branches using the stated conditions.
def manifest():
    # Run this branch when the result of file_hash(POLICY) differs from EXPECTED_POLICY_HASH.
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        # Raise RuntimeError with the text 'FROZEN_E5_CHECKPOINT_MISMATCH' to stop this execution path.
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    # Set identities to the result of source_identities().
    identities = source_identities()
    # Return a dictionary containing protocol_id, code_and_configuration_sha256, controller_version,
    # shield_version,... to the caller.
    return {"protocol_id": "FINAL_EGO_LOCAL_EVALUATION_V2",
        # Store the result of digest(identities) under 'code_and_configuration_sha256'.
        "code_and_configuration_sha256": digest(identities),
        # Store CONTROLLER_VERSION under 'controller_version'.
        "controller_version": CONTROLLER_VERSION,
        # Store SHIELD_VERSION under 'shield_version'.
        "shield_version": SHIELD_VERSION,
        # Store a list containing the text 'multiple_left_turns', the text 'four_way_simultaneous' under
        # 'functional_regression_cases'.
        "functional_regression_cases": ["multiple_left_turns", "four_way_simultaneous"],
        "scope": "One unsignalized four-way intersection; AV-only; one incoming lane/approach; 12 legal movements; ideal same-step V2V; <=4 queue-head negotiators.",
        # Store a list containing the text 'roundabouts', the text 'T-junctions', the text 'signals', the text
        # 'pedestrians/cyclists', the... under 'out_of_scope'.
        "out_of_scope": ["roundabouts", "T-junctions", "signals", "pedestrians/cyclists", "mixed HDV/CAV", "packet networks", "CARLA", "real deployment", ">4 negotiation graphs"],
        "evidence": "Post-training SUMO system evaluation; no real-world validation; inD is intention-model training provenance only.",
        # Store METHODS under 'methods'.
        # Store SEEDS under 'seeds'.
        # Store a list of the result of asdict(x) for x in SCENARIOS under 'scenarios'.
        "methods": METHODS, "seeds": SEEDS, "scenarios": [asdict(x) for x in SCENARIOS],
        "demand_generator": "random.Random(seed), NESW order, independently shuffled blocks of all three existing legal movements per approach; no arrival jitter",
        "policy_selection": "Frozen E5 seeded stochastic masked sample; panel argmax is presentation only",
        "policy_action_seed_derivation": "SHA256(protocol_id,scenario_id,demand_seed,method) first 8 bytes modulo 2**31",
        # Store the result of file_hash(POLICY) under 'policy_sha256'.
        # Store SIM_TIME_STEP under 'simulation_step_seconds'.
        "policy_sha256": file_hash(POLICY), "simulation_step_seconds": SIM_TIME_STEP,
        # Store STOPPED_SPEED_THRESHOLD_MPS under 'waiting_speed_threshold_mps'.
        "waiting_speed_threshold_mps": STOPPED_SPEED_THRESHOLD_MPS,
        # Store a dictionary containing PASS, SAFE_DEGRADATION, UNSAFE_FAILURE, INVALID_EXPERIMENT under
        # 'classification'.
        # Store the text 'integrity valid, safe, complete within budget' under 'PASS'.
        "classification": {"PASS": "integrity valid, safe, complete within budget",
            "SAFE_DEGRADATION": "integrity valid, safe, unfinished/timeout",
            "UNSAFE_FAILURE": "collision or blocked-zone violation",
            "INVALID_EXPERIMENT": "integrity breach, unsupported graph, nonfinite metrics or unexplained abort"},
        "statistics": "Sample standard deviation; percentile paired bootstrap 95% CI of mean, 2000 resamples, seed 260826; n=1 CI N/A; no p-values",
        "budgets": "Resource choices frozen before measurement; never extended after a result",
        # Store SMOKE_BUDGET_SECONDS under 'smoke_budget_seconds'.
        "smoke_budget_seconds": SMOKE_BUDGET_SECONDS,
        # Store a dictionary containing time_to_teleport, seed under 'sumo_options'.
        # Store the negative of 1 under 'time_to_teleport'.
        # Store 0 under 'seed'.
        "sumo_options": {"time_to_teleport": -1, "seed": 0},
        # Store the result of sumo_version() under 'sumo_version'.
        # Store the result of platform.python_version() under 'python_version'.
        "sumo_version": sumo_version(), "python_version": platform.python_version(),
        # Store identities under 'source_identities'.
        "source_identities": identities}

# Prepare using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def prepare(root=ROOT):
    # Import protect_v1 from .models for the operations below.
    from .models import protect_v1
    # Call protect_v1 with the supplied arguments.
    protect_v1(root)
    # Set current to the decoded data produced by json.loads from the serialized data produced by json.dumps.
    current = json.loads(json.dumps(manifest()))
    # Set path to the result of Path(root) joined with the path segment 'manifest.json'.
    path = Path(root) / "manifest.json"
    # Run this branch when whether path exists.
    if path.exists():
        # Set saved to the decoded data produced by json.loads from the text read from path.
        saved = json.loads(path.read_text(encoding="utf-8"))
        # Run this branch when saved at 'manifest_hash' differs from the result of digest(saved at 'manifest') or
        # saved at 'manifest' differs from the decoded data produced by json.loads from the serialized data
        # produced by json.dumps.
        if saved["manifest_hash"] != digest(saved["manifest"]) or saved["manifest"] != json.loads(json.dumps(current)):
            # Raise RuntimeError with the text 'FROZEN_MANIFEST_MISMATCH: restore frozen code/config; use a...' to
            # stop this execution path.
            raise RuntimeError("FROZEN_MANIFEST_MISMATCH: restore frozen code/config; use a separate output root for a new protocol")
        # Return saved to the caller.
        return saved
    # Set frozen to a dictionary containing manifest_hash, manifest.
    frozen = {"manifest_hash": digest(current), "manifest": current}
    # Call write_json with the supplied arguments.
    write_json(path, frozen, exclusive=True)
    # Return frozen to the caller.
    return frozen
