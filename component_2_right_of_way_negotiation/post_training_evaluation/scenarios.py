"""Predeclared demand, independently generated without selection/held-out data."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import random
import platform
import shutil
import subprocess

from config import SUMO_CONFIG, SUMO_NETWORK_FILE, SIM_TIME_STEP, STOPPED_SPEED_THRESHOLD_MPS
from runtime_simulation.scenarios import get_scenario
from runtime_simulation.schedule import PanelDemand, APPROACH_PATHS
from .models import SEEDS, METHODS, POLICY, EXPECTED_POLICY_HASH, ROOT, digest, file_hash, write_json, CONTROLLER_VERSION, SHIELD_VERSION

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    vehicle_count: int
    headway_seconds: float
    budget_seconds: float
    continuous: bool

FUNCTIONAL = tuple(Scenario(name, get_scenario(name).vehicle_count, 0., 180., False)
    for name in ("rule_resolved_two", "regulatory_cycle", "multiple_left_turns",
                 "mixed_manoeuvres", "four_way_simultaneous"))
CONTINUOUS = tuple(Scenario(name, count, headway, budget, True)
    for name, count, headway, budget in (
        ("normal", 8, 2., 240.), ("congested", 12, 1.75, 300.),
        ("dense", 16, 1.5, 360.), ("stress", 24, 1., 480.),
        ("extreme_stress", 32, .75, 600.)))
SCENARIOS = FUNCTIONAL + CONTINUOUS
SMOKE_BUDGET_SECONDS = 90.

def demand(scenario, seed):
    if not scenario.continuous:
        return get_scenario(scenario.scenario_id).schedule()
    rng = random.Random(seed)
    result = {}
    for approach in "NESW":
        # Balanced shuffled blocks: each legal movement once per three vehicles.
        choices = []
        while len(choices) < scenario.vehicle_count // 4:
            block = list(APPROACH_PATHS[approach])
            rng.shuffle(block)
            choices.extend(block)
        result[approach] = tuple(PanelDemand(approach, path, index,
            index * scenario.headway_seconds)
            for index, path in enumerate(choices[:scenario.vehicle_count // 4]))
    return result

def schedule_payload(schedule):
    return {a: [asdict(x) for x in rows] for a, rows in schedule.items()}

def restore_schedule(payload):
    return {a: tuple(PanelDemand(**x) for x in rows) for a, rows in payload.items()}

def source_identities():
    # Freeze the complete operational Python code, model assets, and SUMO inputs.
    root = Path(__file__).resolve().parents[1]
    paths = list(root.glob("*.py"))
    for directory in ("post_training_evaluation", "runtime_simulation", "negotiation_execution",
        "negotiation_learning", "negotiation_training", "conflict", "traffic_rules",
        "traffic_accounting", "negotiation_objective", "perception",
        "experimentation", "map_geometry", "negotiation_scenarios", "gui"):
        paths.extend((root / directory).rglob("*.py"))
    paths.extend((root / "networks").glob("*.xml"))
    paths.extend((root / "models").rglob("*.onnx"))
    paths.extend((root / "models" / "intention").glob("*.json"))
    paths.extend((root / "models" / "intention").glob("*.npz"))
    paths.extend((root / "traffic_rules" / "profiles").glob("*.json"))
    paths += [SUMO_CONFIG, SUMO_NETWORK_FILE, root / "runtime_simulation/scenario_catalog.json"]
    return {str(p.relative_to(root)).replace("\\", "/"): file_hash(p)
            for p in sorted(set(paths)) if p.is_file()}

def sumo_version():
    binary = shutil.which("sumo")
    if not binary:
        raise RuntimeError("SUMO_NOT_ON_PATH")
    return subprocess.check_output([binary, "--version"], text=True).splitlines()[0]

def manifest():
    if file_hash(POLICY) != EXPECTED_POLICY_HASH:
        raise RuntimeError("FROZEN_E5_CHECKPOINT_MISMATCH")
    identities = source_identities()
    return {"protocol_id": "FINAL_EGO_LOCAL_EVALUATION_V2",
        "code_and_configuration_sha256": digest(identities),
        "controller_version": CONTROLLER_VERSION,
        "shield_version": SHIELD_VERSION,
        "functional_regression_cases": ["multiple_left_turns", "four_way_simultaneous"],
        "scope": "One unsignalized four-way intersection; AV-only; one incoming lane/approach; 12 legal movements; ideal same-step V2V; <=4 queue-head negotiators.",
        "out_of_scope": ["roundabouts", "T-junctions", "signals", "pedestrians/cyclists", "mixed HDV/CAV", "packet networks", "CARLA", "real deployment", ">4 negotiation graphs"],
        "evidence": "Post-training SUMO system evaluation; no real-world validation; inD is intention-model training provenance only.",
        "methods": METHODS, "seeds": SEEDS, "scenarios": [asdict(x) for x in SCENARIOS],
        "demand_generator": "random.Random(seed), NESW order, independently shuffled blocks of all three existing legal movements per approach; no arrival jitter",
        "policy_selection": "Frozen E5 seeded stochastic masked sample; panel argmax is presentation only",
        "policy_action_seed_derivation": "SHA256(protocol_id,scenario_id,demand_seed,method) first 8 bytes modulo 2**31",
        "policy_sha256": file_hash(POLICY), "simulation_step_seconds": SIM_TIME_STEP,
        "waiting_speed_threshold_mps": STOPPED_SPEED_THRESHOLD_MPS,
        "classification": {"PASS": "integrity valid, safe, complete within budget",
            "SAFE_DEGRADATION": "integrity valid, safe, unfinished/timeout",
            "UNSAFE_FAILURE": "collision or blocked-zone violation",
            "INVALID_EXPERIMENT": "integrity breach, unsupported graph, nonfinite metrics or unexplained abort"},
        "statistics": "Sample standard deviation; percentile paired bootstrap 95% CI of mean, 2000 resamples, seed 260826; n=1 CI N/A; no p-values",
        "budgets": "Resource choices frozen before measurement; never extended after a result",
        "smoke_budget_seconds": SMOKE_BUDGET_SECONDS,
        "sumo_options": {"time_to_teleport": -1, "seed": 0},
        "sumo_version": sumo_version(), "python_version": platform.python_version(),
        "source_identities": identities}

def prepare(root=ROOT):
    from .models import protect_v1
    protect_v1(root)
    current = json.loads(json.dumps(manifest()))
    path = Path(root) / "manifest.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["manifest_hash"] != digest(saved["manifest"]) or saved["manifest"] != json.loads(json.dumps(current)):
            raise RuntimeError("FROZEN_MANIFEST_MISMATCH: restore frozen code/config; use a separate output root for a new protocol")
        return saved
    frozen = {"manifest_hash": digest(current), "manifest": current}
    write_json(path, frozen, exclusive=True)
    return frozen
