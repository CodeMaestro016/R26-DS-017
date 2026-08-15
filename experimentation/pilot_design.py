"""Outcome-independent frozen controlled-pilot design for Step 5J.2."""

import hashlib
import json
from pathlib import Path

from map_geometry import get_intersection_geometry
from .framework import create_scenario_manifest
from .models import (CandidateSetDefinition, CandidateSource, ScenarioRole,
                     SeedManifest)
from .pilot_models import *


DESIGN_STATUS = "FROZEN_STEP_5J_2"
COUPLING_STATUS = "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE"
PARTITION_METHOD = "SEMANTIC_COVERAGE_BASED_DETERMINISTIC_PARTITION"
PPO_FACTOR_AGGREGATION_STATUS = "REQUIRES_CONTROLLED_PILOT_ABLATION"
REPLICATION_COUNT_STATUS = "REQUIRES_PILOT_VARIANCE_ESTIMATE"
TRAINING_BUDGET_STATUS = "REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT"


def _tuple(value):
    return tuple(_tuple(item) if isinstance(item, list) else item for item in value)


def _stable_id(label, values):
    digest = hashlib.sha256(repr(tuple(values)).encode("utf-8")).hexdigest()
    return label, digest


def load_real_catalogue(path="results/negotiation_scenario_catalogue.json"):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("step_5j_2_readiness") != "READY_TO_RESUME_STEP_5J_2":
        raise ValueError("REAL_NEGOTIATION_SCENARIO_CATALOGUE_NOT_READY")
    return payload


def build_catalogue_manifest(payload):
    specs = payload["scenario_specifications"]
    ids = tuple(sorted((_tuple(item["scenario_id"]) for item in specs), key=repr))
    calibration_ids = tuple(sorted((
        "MOVEMENT_TIMING", item["movement_path_id"],
        item["departure_to_event_steps"], item["network_identity"])
        for item in payload["calibrations"]))
    geometry = get_intersection_geometry()
    identity_fields = (ids, calibration_ids, geometry.network_identity,
                       geometry.junction_id, geometry.center_xy)
    return NegotiationScenarioCatalogueManifest(
        _stable_id("NEGOTIATION_SCENARIO_CATALOGUE_V1", identity_fields),
        geometry.network_identity,
        (geometry.network_identity, geometry.junction_id, geometry.center_xy,
         geometry.coordinate_frame), ids, calibration_ids,
        specs[0]["regulatory_profile"],
        specs[0]["perception_configuration_identity"],
        specs[0]["intention_model_identity"], "STEP_5J_2A_V1", len(ids),
        {"source": "REAL_SUMO_NEGOTIATION_INFRASTRUCTURE",
         "partition_outcomes_consumed": "0"}, "FROZEN_BEFORE_PILOT_EXECUTION")


def build_signatures(payload):
    live = payload["live_coverage"]
    capability = {}
    for item in live:
        sid = _tuple(item["scenario_id"])
        entry = capability.setdefault(sid, [False] * 5)
        proposer_masks = item["proposer_action_masks"]
        responder_masks = item["responder_action_masks"]
        entry[0] |= bool(item["proposer_decision_event_ids"])
        entry[1] |= bool(item["responder_decision_event_ids"])
        entry[2] |= any(all(mask) for mask in proposer_masks)
        entry[3] |= any(all(mask) for mask in responder_masks)
        entry[4] |= len(item["proposer_decision_event_ids"]) > 1
    result = []
    for item in payload["scenario_specifications"]:
        sid = _tuple(item["scenario_id"])
        movements = tuple(item["movement_path_ids"])
        manoeuvres = tuple(sorted(value.rsplit("_", 1)[-1] for value in movements))
        approaches = tuple(item["approach_ids"])
        scc = _tuple(item["expected_regulatory_topology"])
        caps = capability.get(sid, [False] * 5)
        group = ("ROTATION_EQUIVALENCE_V1", len(movements), manoeuvres,
                 tuple(sorted(len(component) for component in scc)))
        result.append(ScenarioCoverageSignature(
            sid, item["scenario_family"], len(movements), movements, approaches,
            manoeuvres, scc, len({member for component in scc for member in component}),
            tuple(item["scheduled_spawn_steps"]),
            sum(len(component) for component in scc), *caps, group))
    return tuple(sorted(result, key=lambda item: repr(item.scenario_id)))


def deterministic_semantic_partition(signatures):
    roles = tuple(ScenarioRole)
    assignments = {role: [] for role in roles}
    capable = [item for item in signatures if item.multi_action_proposer_capable
               and item.multi_action_responder_capable]
    if len(capable) < len(roles):
        raise ValueError("SCENARIO_ROLE_PARTITION_INSUFFICIENT")
    used = set()
    for role, signature in zip(roles, capable):
        assignments[role].append(signature.scenario_id); used.add(signature.scenario_id)
    remaining = [item for item in signatures if item.scenario_id not in used]
    strata = {}
    for item in remaining:
        key = (item.scenario_family, item.participant_count,
               item.manoeuvre_labels, item.equivalence_group_id)
        strata.setdefault(key, []).append(item)
    offset = 0
    for key in sorted(strata, key=repr):
        for position, item in enumerate(sorted(strata[key], key=lambda x: repr(x.scenario_id))):
            assignments[roles[(offset + position) % len(roles)]].append(item.scenario_id)
        offset = (offset + len(strata[key])) % len(roles)
    return {role: tuple(sorted(values, key=repr)) for role, values in assignments.items()}


def build_scenario_manifests(payload, catalogue, signatures):
    partition = deterministic_semantic_partition(signatures)
    specs = payload["scenario_specifications"]
    common = dict(
        scenario_generation_source="REAL_SUMO_NEGOTIATION_INFRASTRUCTURE",
        demand_schedule_identity=("MEASURED_STEP_ALIGNMENT", catalogue.catalogue_id),
        intersection_network_identity=catalogue.network_identity,
        vehicle_type_identity=specs[0]["vehicle_type_identity"],
        regulatory_profile=catalogue.regulatory_profile,
        perception_configuration_identity=catalogue.perception_configuration_identity,
        intention_model_identity=catalogue.intention_model_identity,
        randomization_provenance={"method": "NONE_DETERMINISTIC_SEMANTIC_PARTITION"},
        frozen_status="FROZEN_BEFORE_PILOT_EXECUTION")
    return {role: create_scenario_manifest(
        manifest_id=("SCENARIO_MANIFEST_V1", role.value,
                     _stable_id("CONTENT", partition[role])), purpose=role,
        scenario_ids=partition[role], **common) for role in ScenarioRole}


def candidate_evidence_records():
    paper = "Yu et al. (2022), The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games, arXiv:2103.01955"
    ppo = "Schulman et al. (2017), Proximal Policy Optimization Algorithms, arXiv:1707.06347"
    categorical = {
        "multi_policy_factor_aggregation": ("PER_POLICY_FACTOR_EMPIRICAL_MEAN", "PER_JOINT_BATCH_NESTED_MEAN"),
        "parameter_sharing_strategy": ("SHARED_REPRESENTATION_ROLE_SPECIFIC_HEADS", "SEPARATE_ROLE_SPECIFIC_ACTORS"),
        "gnn_training_mode": ("FROZEN_GNN", "END_TO_END_GNN_POLICY_TRAINING"),
        "advantage_normalization": ("RAW_MONTE_CARLO_ADVANTAGE", "NORMALIZED_MONTE_CARLO_ADVANTAGE"),
        "optimizer_family": ("ADAM",),
    }
    records = []
    for choice, values in categorical.items():
        for value in values:
            records.append(CandidateEvidenceRecord(
                ("CANDIDATE_EVIDENCE", choice, value), choice, value,
                "ARCHITECTURAL_DISCRETE_ALTERNATIVE", paper,
                "MAPPO method/implementation alternative",
                "Defines a controlled candidate without selecting it.",
                "Published settings do not establish project optimality.", True, False,
                {"verification": "PRIMARY_PAPER_AND_OFFICIAL_IMPLEMENTATION"}))
    numerical = {
        "ppo_clip_epsilon": ((0.2,), ppo),
        "learning_rate": ((0.0005,), paper),
        "ppo_update_epochs": ((5, 10, 15), paper),
        "gnn_hidden_dimension": ((64,), paper),
    }
    for choice, (values, source) in numerical.items():
        for value in values:
            records.append(CandidateEvidenceRecord(
                ("CANDIDATE_EVIDENCE", choice, value), choice, value,
                "LITERATURE_INFORMED_SEARCH_REGION", source,
                "Reported PPO/MAPPO experimental configuration",
                "Evidence for candidate inclusion only; different environment and observation schema.",
                "Not evidence of optimality for intersection negotiation.", True, False,
                {"verification": "PRIMARY_SOURCE_VERIFIED", "selected": "False"}))
    return tuple(records)


def build_design(path="results/negotiation_scenario_catalogue.json"):
    payload = load_real_catalogue(path)
    catalogue = build_catalogue_manifest(payload)
    signatures = build_signatures(payload)
    manifests = build_scenario_manifests(payload, catalogue, signatures)
    evidence = candidate_evidence_records()
    grouped = {}
    for item in evidence: grouped.setdefault(item.choice_id, []).append(item)
    candidate_sets = tuple(CandidateSetDefinition(
        choice, tuple(item.candidate_value for item in items),
        CandidateSource.LITERATURE_INFORMED_SEARCH_REGION,
        "Candidate-only values/methods; project selection requires validation.",
        "PRIMARY_EVIDENCE_BOUNDED_CONTROLLED_PILOT", "FROZEN_CANDIDATE_SET")
        for choice, items in sorted(grouped.items()))
    provisional = ProvisionalPilotReferenceConfiguration(
        ("PROVISIONAL_REFERENCE_V1",), tuple(ProvisionalPilotAssignment(
            choice, items[0].candidate_value, items[0].evidence_id)
            for choice, items in sorted(grouped.items())))
    seed_manifest = SeedManifest(
        ("SEED_PROTOCOL_V1", "SHA256_DESIGN_IDENTITY_DERIVATION"),
        "DETERMINISTIC_HASH_STREAM_FROM_FROZEN_DESIGN_IDENTITY", (),
        "PAIRED_CONFIGURATION_REPLICATION_IDENTIFIERS_NOT_PERFORMANCE_SELECTED",
        "PROCEDURE_FROZEN_VALUES_DEFERRED", {"outcome_inputs": "0"})
    gates = ("HARD_ACTION_MASK_INVARIANT", "REGULATORY_INVARIANT",
        "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
        "FINITE_NETWORK_OUTPUTS", "VALID_ACTION_PROBABILITIES",
        "FINITE_TRAINING_QUANTITIES", "CAUSAL_TRANSITION_INTEGRITY",
        "OBJECTIVE_ACCOUNTING_NO_DOUBLE_COUNT", "SCENARIO_MANIFEST_IDENTITY_VALID",
        "COUPLED_ENVIRONMENT_AUTHORITY_VALID")
    families = (
        ("POLICY_FACTOR_AGGREGATION_STUDY", ("multi_policy_factor_aggregation",)),
        ("ARCHITECTURE_CAPACITY_STUDY", ("gnn_hidden_dimension",)),
        ("PARAMETER_SHARING_STUDY", ("parameter_sharing_strategy",)),
        ("GNN_TRAINING_MODE_STUDY", ("gnn_training_mode",)),
        ("PPO_OPTIMIZATION_STUDY", ("ppo_clip_epsilon", "learning_rate", "ppo_update_epochs")),
        ("ADVANTAGE_NORMALIZATION_STUDY", ("advantage_normalization",)),
    )
    set_ids = {item.choice_id: ("CANDIDATE_SET_V1", item.choice_id,
                                tuple(item.candidate_values)) for item in candidate_sets}
    selection_rule = ("SELECTION_RULE_V1", "VALID_GATES_THEN_PAIRED_VALIDATION_PRIMARY_METRIC_ORDER",
                      "EXACT_TIE_UNRESOLVED", "HELD_OUT_EXCLUDED")
    plans = tuple(PilotExperimentPlan(
        ("PILOT_PLAN_V1", family), family,
        f"Controlled comparison of {', '.join(choices)}", choices,
        tuple(set_ids[choice] for choice in choices), provisional.configuration_id,
        manifests[ScenarioRole.TRAINING].manifest_id,
        manifests[ScenarioRole.VALIDATION].manifest_id,
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        seed_manifest.manifest_id, REPLICATION_COUNT_STATUS,
        TRAINING_BUDGET_STATUS, "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        ("THROUGHPUT", "TRAVEL_TIME_VARIANCE", "COLLISION_COUNT",
         "MODEL_PARAMETER_COUNT", "RUNTIME", "CRITIC_PREDICTION_ERROR"), gates,
        "PAIRED_CONFIGURATION_COMPARISON_WITH_UNWEIGHTED_VALIDATION_SCENARIO_REPORTING",
        selection_rule, "FROZEN_BEFORE_PILOT_RESULTS", "NOT_EXECUTED_STEP_5J_2",
        COUPLING_STATUS, {"held_out_performance_consumed": "False"})
        for family, choices in families)
    freeze_fields = (catalogue.catalogue_id,
        tuple(manifests[role].manifest_id for role in ScenarioRole),
        tuple(set_ids.values()), tuple(plan.pilot_plan_id for plan in plans), selection_rule)
    freeze = ExperimentalDesignFreezeRecord(
        _stable_id("EXPERIMENTAL_DESIGN_FREEZE_V1", freeze_fields),
        catalogue.catalogue_id, manifests[ScenarioRole.TRAINING].manifest_id,
        manifests[ScenarioRole.VALIDATION].manifest_id,
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id, tuple(set_ids.values()),
        tuple(plan.pilot_plan_id for plan in plans),
        ("STEP_5J_1_METRIC_MANIFEST",), ("HARD_VALIDITY_GATES_V1", gates),
        selection_rule, seed_manifest.manifest_id, "WORKTREE_STEP_5J_2",
        "FROZEN_BEFORE_PILOT_RESULTS", {"pilot_results_consumed": "0"})
    return {"payload": payload, "catalogue": catalogue, "signatures": signatures,
            "manifests": manifests, "evidence": evidence,
            "candidate_sets": candidate_sets, "provisional": provisional,
            "seed_manifest": seed_manifest, "gates": gates, "plans": plans,
            "selection_rule": selection_rule, "freeze": freeze}


def assess_step_5j_2_design_completion(design):
    ids = [set(design["manifests"][role].scenario_ids) for role in ScenarioRole]
    if any(ids[a] & ids[b] for a in range(3) for b in range(a + 1, 3)):
        return "SCENARIO_ROLE_IDENTITY_LEAKAGE"
    if not design["plans"] or design["freeze"].freeze_status != "FROZEN_BEFORE_PILOT_RESULTS":
        return "SELECTION_RULE_NOT_FROZEN"
    return "CONTROLLED_PILOT_DESIGN_FROZEN"


def assess_step_5j_3_training_readiness(design):
    del design
    return False, (COUPLING_STATUS,)


def assess_negotiation_execution_layer_readiness(design):
    return ("READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING"
            if assess_step_5j_2_design_completion(design) ==
            "CONTROLLED_PILOT_DESIGN_FROZEN" else "STEP_5J_2_DESIGN_INCOMPLETE")
