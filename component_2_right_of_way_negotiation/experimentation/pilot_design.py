"""Outcome-independent frozen controlled-pilot design for Step 5J.2."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import get_intersection_geometry from map_geometry for the operations below.
from map_geometry import get_intersection_geometry
# Import create_scenario_manifest from .framework for the operations below.
from .framework import create_scenario_manifest
# Import CandidateSetDefinition, CandidateSource, ScenarioRole, SeedManifest from .models for the operations
# below.
from .models import (CandidateSetDefinition, CandidateSource, ScenarioRole,
                     SeedManifest)
# Import * from .pilot_models for the operations below.
from .pilot_models import *


# Set DESIGN_STATUS to the text 'FROZEN_STEP_5J_2'.
DESIGN_STATUS = "FROZEN_STEP_5J_2"
# Set COUPLING_STATUS to the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE'.
COUPLING_STATUS = "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE"
# Set PARTITION_METHOD to the text 'SEMANTIC_COVERAGE_BASED_DETERMINISTIC_PARTITION'.
PARTITION_METHOD = "SEMANTIC_COVERAGE_BASED_DETERMINISTIC_PARTITION"
# Set PPO_FACTOR_AGGREGATION_STATUS to the text 'REQUIRES_CONTROLLED_PILOT_ABLATION'.
PPO_FACTOR_AGGREGATION_STATUS = "REQUIRES_CONTROLLED_PILOT_ABLATION"
# Set REPLICATION_COUNT_STATUS to the text 'REQUIRES_PILOT_VARIANCE_ESTIMATE'.
REPLICATION_COUNT_STATUS = "REQUIRES_PILOT_VARIANCE_ESTIMATE"
# Set TRAINING_BUDGET_STATUS to the text 'REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT'.
TRAINING_BUDGET_STATUS = "REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT"


# Tuple using the inputs and processing steps below.
# Input value: the supplied value.
# Output: a tuple built from a lazy sequence of the result of _tuple(item) when whether item has type list,
# otherwise item for item in value.
def _tuple(value):
    # Return a tuple built from a lazy sequence of the result of _tuple(item) when whether item has type list,
    # otherwise item for item in value to the caller.
    return tuple(_tuple(item) if isinstance(item, list) else item for item in value)


# Stable id using the inputs and processing steps below.
# Input label: the supplied label.
# Input values: the supplied values.
# Output: a tuple containing label, digest.
def _stable_id(label, values):
    # Set digest to the hexadecimal digest from hashlib.sha256(repr(tuple(values)).encode('utf-8')).
    digest = hashlib.sha256(repr(tuple(values)).encode("utf-8")).hexdigest()
    # Return a tuple containing label, digest to the caller.
    return label, digest


# Load real catalogue using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: payload.
# Processing: select branches using the stated conditions.
def load_real_catalogue(path="results/negotiation_scenario_catalogue.json"):
    # Set payload to the decoded data produced by json.loads from the text read from Path(path).
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # Run this branch when 'step_5j_2_readiness' from payload; use None if absent differs from the text
    # 'READY_TO_RESUME_STEP_5J_2'.
    if payload.get("step_5j_2_readiness") != "READY_TO_RESUME_STEP_5J_2":
        # Raise ValueError with the text 'REAL_NEGOTIATION_SCENARIO_CATALOGUE_NOT_READY' to stop this execution
        # path.
        raise ValueError("REAL_NEGOTIATION_SCENARIO_CATALOGUE_NOT_READY")
    # Return payload to the caller.
    return payload


# Build catalogue manifest using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: the result of NegotiationScenarioCatalogueManifest(the result of _stable_id(the text
# 'NEGOTIATION_SCENARIO_CATALOGUE_V1', identity_fields),...).
def build_catalogue_manifest(payload):
    # Set specs to payload at 'scenario_specifications'.
    specs = payload["scenario_specifications"]
    # Set ids to a tuple built from the sorted values from a lazy sequence of the result of
    # _tuple(item['scenario_id']) for item in specs.
    ids = tuple(sorted((_tuple(item["scenario_id"]) for item in specs), key=repr))
    # Set calibration_ids to a tuple built from the sorted values from a lazy sequence of a tuple containing
    # 'MOVEMENT_TIMING', item['movement_path_id'], item['departure_to_event_steps'], item['network_identity'] for
    # item in payload at 'calibrations'.
    calibration_ids = tuple(sorted((
        # Include item at 'movement_path_id' in this tuple.
        "MOVEMENT_TIMING", item["movement_path_id"],
        # Include item at 'departure_to_event_steps' in this tuple.
        item["departure_to_event_steps"], item["network_identity"])
        # Evaluate payload at 'calibrations' as part of the enclosing expression.
        for item in payload["calibrations"]))
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Set identity_fields to a tuple containing ids, calibration_ids, geometry.network_identity,
    # geometry.junction_id, geometry.center_xy.
    identity_fields = (ids, calibration_ids, geometry.network_identity,
                       # Include geometry.junction_id in this tuple.
                       geometry.junction_id, geometry.center_xy)
    # Return the result of NegotiationScenarioCatalogueManifest(the result of _stable_id(the text
    # 'NEGOTIATION_SCENARIO_CATALOGUE_V1', identity_fields),...) to the caller.
    return NegotiationScenarioCatalogueManifest(
        # Supply the result of _stable_id(the text 'NEGOTIATION_SCENARIO_CATALOGUE_V1', identity_fields) to
        # NegotiationScenarioCatalogueManifest.
        _stable_id("NEGOTIATION_SCENARIO_CATALOGUE_V1", identity_fields),
        # Supply geometry.network_identity to NegotiationScenarioCatalogueManifest.
        geometry.network_identity,
        # Supply a tuple containing geometry.network_identity, geometry.junction_id, geometry.center_xy,
        # geometry.coordinate_frame to NegotiationScenarioCatalogueManifest.
        (geometry.network_identity, geometry.junction_id, geometry.center_xy,
         # Include geometry.coordinate_frame in this tuple.
         geometry.coordinate_frame), ids, calibration_ids,
        # Supply specs[0] at 'regulatory_profile' to NegotiationScenarioCatalogueManifest.
        specs[0]["regulatory_profile"],
        # Supply specs[0] at 'perception_configuration_identity' to NegotiationScenarioCatalogueManifest.
        specs[0]["perception_configuration_identity"],
        # Supply specs[0] at 'intention_model_identity' to NegotiationScenarioCatalogueManifest.
        specs[0]["intention_model_identity"], "STEP_5J_2A_V1", len(ids),
        # Store the text 'REAL_SUMO_NEGOTIATION_INFRASTRUCTURE' under 'source'.
        {"source": "REAL_SUMO_NEGOTIATION_INFRASTRUCTURE",
         "partition_outcomes_consumed": "0"}, "FROZEN_BEFORE_PILOT_EXECUTION")


# Build signatures using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: a tuple built from the sorted values from result.
# Processing: iterate over the relevant records.
def build_signatures(payload):
    # Set live to payload at 'live_coverage'.
    live = payload["live_coverage"]
    # Set capability to an empty dictionary.
    capability = {}
    # Iterate over live, binding each item to item.
    for item in live:
        # Set sid to the result of _tuple(item at 'scenario_id').
        sid = _tuple(item["scenario_id"])
        # Set entry to the result of capability.setdefault(sid, a list containing False multiplied by 5).
        entry = capability.setdefault(sid, [False] * 5)
        # Set proposer_masks to item at 'proposer_action_masks'.
        proposer_masks = item["proposer_action_masks"]
        # Set responder_masks to item at 'responder_action_masks'.
        responder_masks = item["responder_action_masks"]
        # Update entry[0] to its current value combined with a Boolean built from item at
        # 'proposer_decision_event_ids'.
        entry[0] |= bool(item["proposer_decision_event_ids"])
        # Update entry[1] to its current value combined with a Boolean built from item at
        # 'responder_decision_event_ids'.
        entry[1] |= bool(item["responder_decision_event_ids"])
        # Update entry[2] to its current value combined with whether any item is true in a lazy sequence of
        # whether every item is true in mask for mask in proposer_masks.
        entry[2] |= any(all(mask) for mask in proposer_masks)
        # Update entry[3] to its current value combined with whether any item is true in a lazy sequence of
        # whether every item is true in mask for mask in responder_masks.
        entry[3] |= any(all(mask) for mask in responder_masks)
        # Update entry[4] to its current value combined with the number of entries in item at
        # 'proposer_decision_event_ids' is greater than 1.
        entry[4] |= len(item["proposer_decision_event_ids"]) > 1
    # Set result to an empty list.
    result = []
    # Iterate over payload at 'scenario_specifications', binding each item to item.
    for item in payload["scenario_specifications"]:
        # Set sid to the result of _tuple(item at 'scenario_id').
        sid = _tuple(item["scenario_id"])
        # Set movements to a tuple built from item at 'movement_path_ids'.
        movements = tuple(item["movement_path_ids"])
        # Set manoeuvres to a tuple built from the sorted values from a lazy sequence of value.rsplit('_', 1) at
        # -1 for value in movements.
        manoeuvres = tuple(sorted(value.rsplit("_", 1)[-1] for value in movements))
        # Set approaches to a tuple built from item at 'approach_ids'.
        approaches = tuple(item["approach_ids"])
        # Set scc to the result of _tuple(item at 'expected_regulatory_topology').
        scc = _tuple(item["expected_regulatory_topology"])
        # Set caps to sid from capability; use a list containing False multiplied by 5 if absent.
        caps = capability.get(sid, [False] * 5)
        # Set group to a tuple containing the text 'ROTATION_EQUIVALENCE_V1', the number of entries in movements,
        # manoeuvres, a tuple built from the...
        group = ("ROTATION_EQUIVALENCE_V1", len(movements), manoeuvres,
                 # Include a tuple built from the sorted values from a lazy sequence of the number of entries in
                 # component for component in scc in this tuple.
                 tuple(sorted(len(component) for component in scc)))
        # Append the result of ScenarioCoverageSignature(sid, item at 'scenario_family', the number of entries in
        # movements, movements, approaches,...) to result.
        result.append(ScenarioCoverageSignature(
            # Supply item at 'scenario_family' to ScenarioCoverageSignature.
            sid, item["scenario_family"], len(movements), movements, approaches,
            # Supply the number of entries in a set of member for component in scc to ScenarioCoverageSignature.
            manoeuvres, scc, len({member for component in scc for member in component}),
            # Supply a tuple built from item at 'scheduled_spawn_steps' to ScenarioCoverageSignature.
            tuple(item["scheduled_spawn_steps"]),
            # Supply the sum of a lazy sequence of the number of entries in component for component in scc to
            # ScenarioCoverageSignature.
            sum(len(component) for component in scc), *caps, group))
    # Return a tuple built from the sorted values from result to the caller.
    return tuple(sorted(result, key=lambda item: repr(item.scenario_id)))


# Deterministic semantic partition using the inputs and processing steps below.
# Input signatures: the supplied signatures.
# Output: a dictionary of role mapped to a tuple built from the sorted values from values for (role, values) in
# key/value pairs from assignments.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def deterministic_semantic_partition(signatures):
    # Set roles to a tuple built from ScenarioRole.
    roles = tuple(ScenarioRole)
    # Set assignments to a dictionary of role mapped to an empty list for role in roles.
    assignments = {role: [] for role in roles}
    # Set capable to a list of item for item in signatures; retain entries satisfying
    # item.multi_action_proposer_capable and item.multi_action_responder_capable.
    capable = [item for item in signatures if item.multi_action_proposer_capable
               # Evaluate item.multi_action_responder_capable as part of the enclosing expression.
               and item.multi_action_responder_capable]
    # Run this branch when the number of entries in capable is less than the number of entries in roles.
    if len(capable) < len(roles):
        # Raise ValueError with the text 'SCENARIO_ROLE_PARTITION_INSUFFICIENT' to stop this execution path.
        raise ValueError("SCENARIO_ROLE_PARTITION_INSUFFICIENT")
    # Set used to an empty set.
    used = set()
    # Iterate over corresponding items paired from roles, capable, binding each item to (role, signature).
    for role, signature in zip(roles, capable):
        # Append signature.scenario_id to assignments[role].
        # Add signature.scenario_id to used.
        assignments[role].append(signature.scenario_id); used.add(signature.scenario_id)
    # Set remaining to a list of item for item in signatures; retain entries satisfying item.scenario_id does not
    # belong to used.
    remaining = [item for item in signatures if item.scenario_id not in used]
    # Set strata to an empty dictionary.
    strata = {}
    # Iterate over remaining, binding each item to item.
    for item in remaining:
        # Set key to a tuple containing item.scenario_family, item.participant_count, item.manoeuvre_labels,
        # item.equivalence_group_id.
        key = (item.scenario_family, item.participant_count,
               # Include item.equivalence_group_id in this tuple.
               item.manoeuvre_labels, item.equivalence_group_id)
        # Append item to strata.setdefault(key, []).
        strata.setdefault(key, []).append(item)
    # Set offset to 0.
    offset = 0
    # Iterate over the sorted values from strata, binding each item to key.
    for key in sorted(strata, key=repr):
        # Iterate over index/value pairs from the sorted values from strata at key, binding each item to
        # (position, item).
        for position, item in enumerate(sorted(strata[key], key=lambda x: repr(x.scenario_id))):
            # Append item.scenario_id to assignments[roles[(offset + position) % len(roles)]].
            assignments[roles[(offset + position) % len(roles)]].append(item.scenario_id)
        # Set offset to offset plus the number of entries in strata at key modulo the number of entries in roles.
        offset = (offset + len(strata[key])) % len(roles)
    # Return a dictionary of role mapped to a tuple built from the sorted values from values for (role, values) in
    # key/value pairs from assignments to the caller.
    return {role: tuple(sorted(values, key=repr)) for role, values in assignments.items()}


# Build scenario manifests using the inputs and processing steps below.
# Input payload: the supplied payload.
# Input catalogue: the supplied catalogue.
# Input signatures: the supplied signatures.
# Output: a dictionary of role mapped to the result of create_scenario_manifest() for role in ScenarioRole.
def build_scenario_manifests(payload, catalogue, signatures):
    # Set partition to the result of deterministic_semantic_partition(signatures).
    partition = deterministic_semantic_partition(signatures)
    # Set specs to payload at 'scenario_specifications'.
    specs = payload["scenario_specifications"]
    # Set common to a dictionary built from the supplied values.
    common = dict(
        # Supply scenario_generation_source as the text 'REAL_SUMO_NEGOTIATION_INFRASTRUCTURE'.
        scenario_generation_source="REAL_SUMO_NEGOTIATION_INFRASTRUCTURE",
        # Supply demand_schedule_identity as a tuple containing the text 'MEASURED_STEP_ALIGNMENT',
        # catalogue.catalogue_id.
        demand_schedule_identity=("MEASURED_STEP_ALIGNMENT", catalogue.catalogue_id),
        # Supply intersection_network_identity as catalogue.network_identity.
        intersection_network_identity=catalogue.network_identity,
        # Supply vehicle_type_identity as specs[0] at 'vehicle_type_identity'.
        vehicle_type_identity=specs[0]["vehicle_type_identity"],
        # Supply regulatory_profile as catalogue.regulatory_profile.
        regulatory_profile=catalogue.regulatory_profile,
        # Supply perception_configuration_identity as catalogue.perception_configuration_identity.
        perception_configuration_identity=catalogue.perception_configuration_identity,
        # Supply intention_model_identity as catalogue.intention_model_identity.
        intention_model_identity=catalogue.intention_model_identity,
        # Store the text 'NONE_DETERMINISTIC_SEMANTIC_PARTITION' under 'method'.
        randomization_provenance={"method": "NONE_DETERMINISTIC_SEMANTIC_PARTITION"},
        # Supply frozen_status as the text 'FROZEN_BEFORE_PILOT_EXECUTION'.
        frozen_status="FROZEN_BEFORE_PILOT_EXECUTION")
    # Return a dictionary of role mapped to the result of create_scenario_manifest() for role in ScenarioRole to
    # the caller.
    return {role: create_scenario_manifest(
        # Supply manifest_id as a tuple containing the text 'SCENARIO_MANIFEST_V1', role.value, the result of
        # _stable_id(the text 'CONTENT', partition at role).
        manifest_id=("SCENARIO_MANIFEST_V1", role.value,
                     # Supply purpose as role.
                     _stable_id("CONTENT", partition[role])), purpose=role,
        # Supply scenario_ids as partition at role.
        # Supply the unpacked keyword arguments as common.
        scenario_ids=partition[role], **common) for role in ScenarioRole}


# Candidate evidence records using the inputs and processing steps below.
# Output: a tuple built from records.
# Processing: iterate over the relevant records.
def candidate_evidence_records():
    # Set paper to the text 'Yu et al. (2022), The Surprising Effectiveness of PPO in...'.
    paper = "Yu et al. (2022), The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games, arXiv:2103.01955"
    # Set ppo to the text 'Schulman et al. (2017), Proximal Policy Optimization...'.
    ppo = "Schulman et al. (2017), Proximal Policy Optimization Algorithms, arXiv:1707.06347"
    # Set categorical to a dictionary containing multi_policy_factor_aggregation, parameter_sharing_strategy,
    # gnn_training_mode,...
    categorical = {
        # Store a tuple containing the text 'PER_POLICY_FACTOR_EMPIRICAL_MEAN', the text
        # 'PER_JOINT_BATCH_NESTED_MEAN' under 'multi_policy_factor_aggregation'.
        "multi_policy_factor_aggregation": ("PER_POLICY_FACTOR_EMPIRICAL_MEAN", "PER_JOINT_BATCH_NESTED_MEAN"),
        # Store a tuple containing the text 'SHARED_REPRESENTATION_ROLE_SPECIFIC_HEADS', the text
        # 'SEPARATE_ROLE_SPECIFIC_ACTORS' under 'parameter_sharing_strategy'.
        "parameter_sharing_strategy": ("SHARED_REPRESENTATION_ROLE_SPECIFIC_HEADS", "SEPARATE_ROLE_SPECIFIC_ACTORS"),
        # Store a tuple containing the text 'FROZEN_GNN', the text 'END_TO_END_GNN_POLICY_TRAINING' under
        # 'gnn_training_mode'.
        "gnn_training_mode": ("FROZEN_GNN", "END_TO_END_GNN_POLICY_TRAINING"),
        # Store a tuple containing the text 'RAW_MONTE_CARLO_ADVANTAGE', the text
        # 'NORMALIZED_MONTE_CARLO_ADVANTAGE' under 'advantage_normalization'.
        "advantage_normalization": ("RAW_MONTE_CARLO_ADVANTAGE", "NORMALIZED_MONTE_CARLO_ADVANTAGE"),
        # Store a tuple containing the text 'ADAM' under 'optimizer_family'.
        "optimizer_family": ("ADAM",),
    }
    # Set records to an empty list.
    records = []
    # Iterate over key/value pairs from categorical, binding each item to (choice, values).
    for choice, values in categorical.items():
        # Iterate over values, binding each item to value.
        for value in values:
            # Append the result of CandidateEvidenceRecord(a tuple containing the text 'CANDIDATE_EVIDENCE',
            # choice, value, choice, value, the text...) to records.
            records.append(CandidateEvidenceRecord(
                # Supply a tuple containing the text 'CANDIDATE_EVIDENCE', choice, value to
                # CandidateEvidenceRecord.
                ("CANDIDATE_EVIDENCE", choice, value), choice, value,
                # Supply paper to CandidateEvidenceRecord.
                "ARCHITECTURAL_DISCRETE_ALTERNATIVE", paper,
                "MAPPO method/implementation alternative",
                "Defines a controlled candidate without selecting it.",
                # Supply the text 'Published settings do not establish project optimality.' to the enclosing
                # expression.
                "Published settings do not establish project optimality.", True, False,
                # Store the text 'PRIMARY_PAPER_AND_OFFICIAL_IMPLEMENTATION' under 'verification'.
                {"verification": "PRIMARY_PAPER_AND_OFFICIAL_IMPLEMENTATION"}))
    # Set numerical to a dictionary containing ppo_clip_epsilon, learning_rate, ppo_update_epochs,
    # gnn_hidden_dimension.
    numerical = {
        # Store a tuple containing a tuple containing 0.2, ppo under 'ppo_clip_epsilon'.
        "ppo_clip_epsilon": ((0.2,), ppo),
        # Store a tuple containing a tuple containing 0.0005, paper under 'learning_rate'.
        "learning_rate": ((0.0005,), paper),
        # Store a tuple containing a tuple containing 5, 10, 15, paper under 'ppo_update_epochs'.
        "ppo_update_epochs": ((5, 10, 15), paper),
        # Store a tuple containing a tuple containing 64, paper under 'gnn_hidden_dimension'.
        "gnn_hidden_dimension": ((64,), paper),
    }
    # Iterate over key/value pairs from numerical, binding each item to (choice, (values, source)).
    for choice, (values, source) in numerical.items():
        # Iterate over values, binding each item to value.
        for value in values:
            # Append the result of CandidateEvidenceRecord(a tuple containing the text 'CANDIDATE_EVIDENCE',
            # choice, value, choice, value, the text...) to records.
            records.append(CandidateEvidenceRecord(
                # Supply a tuple containing the text 'CANDIDATE_EVIDENCE', choice, value to
                # CandidateEvidenceRecord.
                ("CANDIDATE_EVIDENCE", choice, value), choice, value,
                # Supply source to CandidateEvidenceRecord.
                "LITERATURE_INFORMED_SEARCH_REGION", source,
                "Reported PPO/MAPPO experimental configuration",
                "Evidence for candidate inclusion only; different environment and observation schema.",
                # Supply the text 'Not evidence of optimality for intersection negotiation.' to the enclosing
                # expression.
                "Not evidence of optimality for intersection negotiation.", True, False,
                # Store the text 'PRIMARY_SOURCE_VERIFIED' under 'verification'.
                # Store the text 'False' under 'selected'.
                {"verification": "PRIMARY_SOURCE_VERIFIED", "selected": "False"}))
    # Return a tuple built from records to the caller.
    return tuple(records)


# Build design using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: a dictionary containing payload, catalogue, signatures, manifests, evidence, candidate_sets,
# provisional,...
# Processing: iterate over the relevant records.
def build_design(path="results/negotiation_scenario_catalogue.json"):
    # Set payload to the result of load_real_catalogue(path).
    payload = load_real_catalogue(path)
    # Set catalogue to the result of build_catalogue_manifest(payload).
    catalogue = build_catalogue_manifest(payload)
    # Set signatures to the result of build_signatures(payload).
    signatures = build_signatures(payload)
    # Set manifests to the result of build_scenario_manifests(payload, catalogue, signatures).
    manifests = build_scenario_manifests(payload, catalogue, signatures)
    # Set evidence to the result of candidate_evidence_records().
    evidence = candidate_evidence_records()
    # Set grouped to an empty dictionary.
    grouped = {}
    # Iterate over evidence, binding each item to item.
    # Append item to grouped.setdefault(item.choice_id, []).
    for item in evidence: grouped.setdefault(item.choice_id, []).append(item)
    # Set candidate_sets to a tuple built from a lazy sequence of the result of CandidateSetDefinition(choice, a
    # tuple built from (item.candidate_value for item in items),...) for (choice, items) in the sorted values from
    # key/value pairs from grouped.
    candidate_sets = tuple(CandidateSetDefinition(
        # Supply a tuple built from a lazy sequence of item.candidate_value for item in items to
        # CandidateSetDefinition.
        choice, tuple(item.candidate_value for item in items),
        # Supply CandidateSource.LITERATURE_INFORMED_SEARCH_REGION to CandidateSetDefinition.
        CandidateSource.LITERATURE_INFORMED_SEARCH_REGION,
        "Candidate-only values/methods; project selection requires validation.",
        "PRIMARY_EVIDENCE_BOUNDED_CONTROLLED_PILOT", "FROZEN_CANDIDATE_SET")
        # Evaluate the sorted values from key/value pairs from grouped as part of the enclosing expression.
        for choice, items in sorted(grouped.items()))
    # Set provisional to the result of ProvisionalPilotReferenceConfiguration(a tuple containing the text
    # 'PROVISIONAL_REFERENCE_V1', a tuple built from a lazy sequence of...).
    provisional = ProvisionalPilotReferenceConfiguration(
        # Supply a tuple built from a lazy sequence of the result of ProvisionalPilotAssignment(choice,
        # items[0].candidate_value, items[0].evidence_id) for (choice, items) in the sorted values from key/value
        # pairs from grouped to ProvisionalPilotReferenceConfiguration.
        ("PROVISIONAL_REFERENCE_V1",), tuple(ProvisionalPilotAssignment(
            # Supply items[0].candidate_value to ProvisionalPilotAssignment.
            choice, items[0].candidate_value, items[0].evidence_id)
            # Evaluate the sorted values from key/value pairs from grouped as part of the enclosing expression.
            for choice, items in sorted(grouped.items())))
    # Set seed_manifest to the result of SeedManifest(a tuple containing the text 'SEED_PROTOCOL_V1', the text
    # 'SHA256_DESIGN_IDENTITY_DERIVATION',...).
    seed_manifest = SeedManifest(
        # Supply a tuple containing the text 'SEED_PROTOCOL_V1', the text 'SHA256_DESIGN_IDENTITY_DERIVATION' to
        # SeedManifest.
        ("SEED_PROTOCOL_V1", "SHA256_DESIGN_IDENTITY_DERIVATION"),
        # Supply an empty tuple to SeedManifest.
        "DETERMINISTIC_HASH_STREAM_FROM_FROZEN_DESIGN_IDENTITY", (),
        "PAIRED_CONFIGURATION_REPLICATION_IDENTIFIERS_NOT_PERFORMANCE_SELECTED",
        # Store the text '0' under 'outcome_inputs'.
        "PROCEDURE_FROZEN_VALUES_DEFERRED", {"outcome_inputs": "0"})
    # Set gates to a tuple containing the text 'HARD_ACTION_MASK_INVARIANT', the text 'REGULATORY_INVARIANT', the
    # text 'PROTOCOL_INVARIANT', the...
    gates = ("HARD_ACTION_MASK_INVARIANT", "REGULATORY_INVARIANT",
        "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
        "FINITE_NETWORK_OUTPUTS", "VALID_ACTION_PROBABILITIES",
        "FINITE_TRAINING_QUANTITIES", "CAUSAL_TRANSITION_INTEGRITY",
        "OBJECTIVE_ACCOUNTING_NO_DOUBLE_COUNT", "SCENARIO_MANIFEST_IDENTITY_VALID",
        "COUPLED_ENVIRONMENT_AUTHORITY_VALID")
    # Set families to a tuple containing a tuple containing the text 'POLICY_FACTOR_AGGREGATION_STUDY', a tuple
    # containing the text...
    families = (
        # Include a tuple containing the text 'POLICY_FACTOR_AGGREGATION_STUDY', a tuple containing the text
        # 'multi_policy_factor_aggregation' in this tuple.
        ("POLICY_FACTOR_AGGREGATION_STUDY", ("multi_policy_factor_aggregation",)),
        # Include a tuple containing the text 'ARCHITECTURE_CAPACITY_STUDY', a tuple containing the text
        # 'gnn_hidden_dimension' in this tuple.
        ("ARCHITECTURE_CAPACITY_STUDY", ("gnn_hidden_dimension",)),
        # Include a tuple containing the text 'PARAMETER_SHARING_STUDY', a tuple containing the text
        # 'parameter_sharing_strategy' in this tuple.
        ("PARAMETER_SHARING_STUDY", ("parameter_sharing_strategy",)),
        # Include a tuple containing the text 'GNN_TRAINING_MODE_STUDY', a tuple containing the text
        # 'gnn_training_mode' in this tuple.
        ("GNN_TRAINING_MODE_STUDY", ("gnn_training_mode",)),
        # Include a tuple containing the text 'PPO_OPTIMIZATION_STUDY', a tuple containing the text
        # 'ppo_clip_epsilon', the text... in this tuple.
        ("PPO_OPTIMIZATION_STUDY", ("ppo_clip_epsilon", "learning_rate", "ppo_update_epochs")),
        # Include a tuple containing the text 'ADVANTAGE_NORMALIZATION_STUDY', a tuple containing the text
        # 'advantage_normalization' in this tuple.
        ("ADVANTAGE_NORMALIZATION_STUDY", ("advantage_normalization",)),
    )
    # Set set_ids to a dictionary of item.choice_id mapped to a tuple containing the text 'CANDIDATE_SET_V1',
    # item.choice_id, a tuple built from item.candidate_values for item in candidate_sets.
    set_ids = {item.choice_id: ("CANDIDATE_SET_V1", item.choice_id,
                                # Include a tuple built from item.candidate_values in this tuple.
                                tuple(item.candidate_values)) for item in candidate_sets}
    # Set selection_rule to a tuple containing the text 'SELECTION_RULE_V1', the text
    # 'VALID_GATES_THEN_PAIRED_VALIDATION_PRIMARY_METRIC_ORDER', the text...
    selection_rule = ("SELECTION_RULE_V1", "VALID_GATES_THEN_PAIRED_VALIDATION_PRIMARY_METRIC_ORDER",
                      "EXACT_TIE_UNRESOLVED", "HELD_OUT_EXCLUDED")
    # Set plans to a tuple built from a lazy sequence of the result of PilotExperimentPlan(a tuple containing
    # 'PILOT_PLAN_V1', family, family, formatted text built from the embedded...) for (family, choices) in
    # families.
    plans = tuple(PilotExperimentPlan(
        # Supply a tuple containing the text 'PILOT_PLAN_V1', family to PilotExperimentPlan.
        ("PILOT_PLAN_V1", family), family,
        # Supply formatted text built from the embedded values to PilotExperimentPlan.
        f"Controlled comparison of {', '.join(choices)}", choices,
        # Supply a tuple built from a lazy sequence of set_ids at choice for choice in choices to
        # PilotExperimentPlan.
        tuple(set_ids[choice] for choice in choices), provisional.configuration_id,
        # Supply manifests[ScenarioRole.TRAINING].manifest_id to PilotExperimentPlan.
        manifests[ScenarioRole.TRAINING].manifest_id,
        # Supply manifests[ScenarioRole.VALIDATION].manifest_id to PilotExperimentPlan.
        manifests[ScenarioRole.VALIDATION].manifest_id,
        # Supply manifests[ScenarioRole.HELD_OUT_TEST].manifest_id to PilotExperimentPlan.
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id,
        # Supply seed_manifest.manifest_id to PilotExperimentPlan.
        seed_manifest.manifest_id, REPLICATION_COUNT_STATUS,
        # Supply TRAINING_BUDGET_STATUS to PilotExperimentPlan.
        TRAINING_BUDGET_STATUS, "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        # Supply a tuple containing the text 'THROUGHPUT', the text 'TRAVEL_TIME_VARIANCE', the text
        # 'COLLISION_COUNT', the text... to PilotExperimentPlan.
        ("THROUGHPUT", "TRAVEL_TIME_VARIANCE", "COLLISION_COUNT",
         # Supply gates to PilotExperimentPlan.
         "MODEL_PARAMETER_COUNT", "RUNTIME", "CRITIC_PREDICTION_ERROR"), gates,
        "PAIRED_CONFIGURATION_COMPARISON_WITH_UNWEIGHTED_VALIDATION_SCENARIO_REPORTING",
        # Supply selection_rule to PilotExperimentPlan.
        selection_rule, "FROZEN_BEFORE_PILOT_RESULTS", "NOT_EXECUTED_STEP_5J_2",
        # Store the text 'False' under 'held_out_performance_consumed'.
        COUPLING_STATUS, {"held_out_performance_consumed": "False"})
        # Evaluate a tuple containing family, choices as part of the enclosing expression.
        for family, choices in families)
    # Set freeze_fields to a tuple containing catalogue.catalogue_id, a tuple built from a lazy sequence of
    # manifests[role].manifest_id for role in...
    freeze_fields = (catalogue.catalogue_id,
        # Include a tuple built from a lazy sequence of manifests[role].manifest_id for role in ScenarioRole in
        # this tuple.
        tuple(manifests[role].manifest_id for role in ScenarioRole),
        # Include a tuple built from a lazy sequence of plan.pilot_plan_id for plan in plans in this tuple.
        tuple(set_ids.values()), tuple(plan.pilot_plan_id for plan in plans), selection_rule)
    # Set freeze to the result of ExperimentalDesignFreezeRecord(the result of _stable_id(the text
    # 'EXPERIMENTAL_DESIGN_FREEZE_V1', freeze_fields),...).
    freeze = ExperimentalDesignFreezeRecord(
        # Supply the result of _stable_id(the text 'EXPERIMENTAL_DESIGN_FREEZE_V1', freeze_fields) to
        # ExperimentalDesignFreezeRecord.
        _stable_id("EXPERIMENTAL_DESIGN_FREEZE_V1", freeze_fields),
        # Supply manifests[ScenarioRole.TRAINING].manifest_id to ExperimentalDesignFreezeRecord.
        catalogue.catalogue_id, manifests[ScenarioRole.TRAINING].manifest_id,
        # Supply manifests[ScenarioRole.VALIDATION].manifest_id to ExperimentalDesignFreezeRecord.
        manifests[ScenarioRole.VALIDATION].manifest_id,
        # Supply manifests[ScenarioRole.HELD_OUT_TEST].manifest_id to ExperimentalDesignFreezeRecord.
        manifests[ScenarioRole.HELD_OUT_TEST].manifest_id, tuple(set_ids.values()),
        # Supply a tuple built from a lazy sequence of plan.pilot_plan_id for plan in plans to
        # ExperimentalDesignFreezeRecord.
        tuple(plan.pilot_plan_id for plan in plans),
        # Supply a tuple containing the text 'HARD_VALIDITY_GATES_V1', gates to ExperimentalDesignFreezeRecord.
        ("STEP_5J_1_METRIC_MANIFEST",), ("HARD_VALIDITY_GATES_V1", gates),
        # Supply seed_manifest.manifest_id to ExperimentalDesignFreezeRecord.
        selection_rule, seed_manifest.manifest_id, "WORKTREE_STEP_5J_2",
        # Store the text '0' under 'pilot_results_consumed'.
        "FROZEN_BEFORE_PILOT_RESULTS", {"pilot_results_consumed": "0"})
    # Return a dictionary containing payload, catalogue, signatures, manifests, evidence, candidate_sets,
    # provisional,... to the caller.
    return {"payload": payload, "catalogue": catalogue, "signatures": signatures,
            # Store manifests under 'manifests'.
            # Store evidence under 'evidence'.
            "manifests": manifests, "evidence": evidence,
            # Store candidate_sets under 'candidate_sets'.
            # Store provisional under 'provisional'.
            "candidate_sets": candidate_sets, "provisional": provisional,
            # Store seed_manifest under 'seed_manifest'.
            # Store gates under 'gates'.
            # Store plans under 'plans'.
            "seed_manifest": seed_manifest, "gates": gates, "plans": plans,
            # Store selection_rule under 'selection_rule'.
            # Store freeze under 'freeze'.
            "selection_rule": selection_rule, "freeze": freeze}


# Assess step 5j 2 design completion using the inputs and processing steps below.
# Input design: the supplied design.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def assess_step_5j_2_design_completion(design):
    # Set ids to a list of a set built from design['manifests'][role].scenario_ids for role in ScenarioRole.
    ids = [set(design["manifests"][role].scenario_ids) for role in ScenarioRole]
    # Run this branch when whether any item is true in a lazy sequence of ids at a intersected with ids at b for a
    # in the integer range defined by 3.
    if any(ids[a] & ids[b] for a in range(3) for b in range(a + 1, 3)):
        # Return the text 'SCENARIO_ROLE_IDENTITY_LEAKAGE' to the caller.
        return "SCENARIO_ROLE_IDENTITY_LEAKAGE"
    # Run this branch when the negation of design at 'plans' or design['freeze'].freeze_status differs from the
    # text 'FROZEN_BEFORE_PILOT_RESULTS'.
    if not design["plans"] or design["freeze"].freeze_status != "FROZEN_BEFORE_PILOT_RESULTS":
        # Return the text 'SELECTION_RULE_NOT_FROZEN' to the caller.
        return "SELECTION_RULE_NOT_FROZEN"
    # Return the text 'CONTROLLED_PILOT_DESIGN_FROZEN' to the caller.
    return "CONTROLLED_PILOT_DESIGN_FROZEN"


# Assess step 5j 3 training readiness using the inputs and processing steps below.
# Input design: the supplied design.
# Output: a tuple containing False, a tuple containing COUPLING_STATUS.
def assess_step_5j_3_training_readiness(design):
    # Delete design from its containing namespace or collection.
    del design
    # Return a tuple containing False, a tuple containing COUPLING_STATUS to the caller.
    return False, (COUPLING_STATUS,)


# Assess negotiation execution layer readiness using the inputs and processing steps below.
# Input design: the supplied design.
# Output: the text 'READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING' when the result of
# assess_step_5j_2_design_completion(design) equals the text 'CONTROLLED_PILOT_DESIGN_FROZEN', otherwise the...
def assess_negotiation_execution_layer_readiness(design):
    # Return the text 'READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING' when the result of
    # assess_step_5j_2_design_completion(design) equals the text 'CONTROLLED_PILOT_DESIGN_FROZEN', otherwise the
    # text 'STEP_5J_2_DESIGN_INCOMPLETE' to the caller.
    return ("READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING"
            # Evaluate the result of assess_step_5j_2_design_completion(design) equals the text
            # 'CONTROLLED_PILOT_DESIGN_FROZEN' as part of the enclosing expression.
            if assess_step_5j_2_design_completion(design) ==
            # Supply the text 'STEP_5J_2_DESIGN_INCOMPLETE' to the enclosing expression.
            "CONTROLLED_PILOT_DESIGN_FROZEN" else "STEP_5J_2_DESIGN_INCOMPLETE")
