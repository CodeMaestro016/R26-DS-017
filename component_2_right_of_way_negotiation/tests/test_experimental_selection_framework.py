from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from experimentation import (
    CandidateSetDefinition, ChoiceClassification, ExperimentManifest,
    ExperimentRunRecord, ExperimentalChoice, ExperimentalChoiceRegistry,
    ExperimentalFrameworkError, MetricDirection, ScenarioRole, SeedManifest,
    SelectionDecisionRecord, SelectionMetricRecord, ValidityGateResult,
    assess_final_training_readiness, assess_step_5j_2_readiness,
    build_metric_manifest, build_project_choice_registry, create_configuration,
    create_scenario_manifest, create_selection_decision, deterministic_run_id,
    valid_runs_for_comparison,
)


def test_all_choice_classifications_are_categorical():
    assert {item.value for item in ChoiceClassification} == {
        "MATHEMATICALLY_FIXED", "PHYSICALLY_DERIVED", "REGULATORY_FIXED",
        "SCHEMA_DERIVED", "PROJECT_SEMANTIC_REQUIREMENT",
        "RESEARCH_SUPPORTED_METHOD", "ARCHITECTURE_CHOICE_REQUIRES_ABLATION",
        "REQUIRES_EXPERIMENTAL_SELECTION", "OPTIONAL_FUTURE_ABLATION",
        "NOT_APPLICABLE_TO_BASELINE",
    }


def test_registry_contains_fixed_schema_regulatory_and_empirical_choices():
    registry = build_project_choice_registry()
    assert registry.get("reward_definition").classification is ChoiceClassification.MATHEMATICALLY_FIXED
    assert registry.get("regulatory_rules").classification is ChoiceClassification.REGULATORY_FIXED
    assert registry.get("node_input_dimension").classification is ChoiceClassification.SCHEMA_DERIVED
    assert registry.get("claim_direction").classification is ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT
    assert registry.get("learning_rate").classification is ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION
    assert registry.get("gnn_hidden_dimension").classification is ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION
    assert registry.get("gae_estimator").classification is ChoiceClassification.OPTIONAL_FUTURE_ABLATION
    assert registry.selected_empirical_value_count == 0


def test_reward_gamma_claim_masks_and_route_exclusion_are_not_tunable():
    registry = build_project_choice_registry()
    assert registry.get("reward_definition").current_status == "FIXED_BASELINE"
    assert "gamma" not in {item.choice_id for item in registry.all()}
    for key in ("claim_direction", "hard_action_masks", "route_truth_exclusion"):
        assert registry.get(key).classification not in {
            ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
            ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
        }


def test_duplicate_choice_conflict_and_identical_idempotence():
    choice = build_project_choice_registry().get("learning_rate")
    registry = ExperimentalChoiceRegistry((choice, choice))
    assert len(registry.all()) == 1
    conflict = ExperimentalChoice(
        choice.choice_id, "different", choice.component, choice.classification,
        choice.current_status, choice.mathematical_or_research_basis,
        choice.candidate_generation_status, choice.selection_method_status,
        None, choice.selected_value_status, (), (), {},
    )
    with pytest.raises(ExperimentalFrameworkError, match="CONFLICTING_EXPERIMENTAL_CHOICE"):
        registry.register(conflict)


def test_candidate_sets_start_empty_without_numerical_values():
    definition = CandidateSetDefinition(
        "learning_rate", (), None, "NOT_YET_DEFINED",
        "STEP_5J_2_CONTROLLED_PILOT_DESIGN",
    )
    assert definition.candidate_values == ()
    assert definition.status == "CANDIDATE_VALUES_NOT_YET_SELECTED"


def scenario(role):
    return create_scenario_manifest(
        manifest_id=(role.value,), purpose=role,
        scenario_ids=(("network", "demand-A"), ("network", "demand-B")),
        scenario_generation_source="EXISTING_DETERMINISTIC_DEMAND",
        demand_schedule_identity=("schedule",),
        intersection_network_identity="intersection.net.xml",
        vehicle_type_identity="AV", regulatory_profile="DE_STVO",
        perception_configuration_identity="CURRENT_SENSOR_PROFILE",
        intention_model_identity="CURRENT_ONNX_MODELS",
        randomization_provenance={}, frozen_status="FRAMEWORK_CONTRACT_ONLY",
    )


def test_scenario_roles_and_heldout_isolation():
    training, validation, heldout = map(scenario, ScenarioRole)
    assert not training.used_for_parameter_selection
    assert validation.used_for_parameter_selection
    assert not heldout.used_for_parameter_selection
    assert heldout.scenario_ids == tuple(sorted(heldout.scenario_ids, key=repr))


def test_seed_manifest_has_no_default_seed():
    seed = SeedManifest(("SEEDS",), "NOT_SELECTED", (), "REPLICATION", "UNRESOLVED", {})
    assert seed.seed_values == ()


def test_partial_configuration_is_deterministic_and_strict_mode_rejects():
    registry = build_project_choice_registry()
    kwargs = dict(architecture_identity="UNRESOLVED", training_method_identity="UNRESOLVED",
                  regulatory_profile="DE_STVO", semantic_schema_versions=("NODE_V1",))
    first = create_configuration(registry, {}, **kwargs)
    second = create_configuration(registry, {}, **kwargs)
    assert first.configuration_id == second.configuration_id
    assert first.unresolved_choices
    with pytest.raises(ExperimentalFrameworkError, match="EXPERIMENTAL_CHOICE_UNRESOLVED"):
        create_configuration(registry, {}, require_resolved=True, **kwargs)


def test_configuration_identity_is_assignment_order_invariant():
    registry = build_project_choice_registry()
    kwargs = dict(architecture_identity="DECLARED", training_method_identity="DECLARED",
                  regulatory_profile="DE_STVO", semantic_schema_versions=())
    a = create_configuration(registry, {"learning_rate": "A", "optimizer_family": "B"}, **kwargs)
    b = create_configuration(registry, {"optimizer_family": "B", "learning_rate": "A"}, **kwargs)
    assert a.configuration_id == b.configuration_id


def test_metric_manifest_has_one_physical_primary_and_no_composite():
    metrics = build_metric_manifest()
    assert metrics.primary_selection_metric == "TOTAL_TEAM_TRAVEL_TIME_SECONDS"
    assert metrics.primary_direction is MetricDirection.LOWER_IS_BETTER
    assert "THROUGHPUT" in metrics.secondary_diagnostics
    assert "TRAVEL_TIME_VARIANCE" in metrics.secondary_diagnostics
    assert not metrics.weighted_composite_score


def gates(passed=True):
    return tuple(ValidityGateResult(gate, passed, ("evidence",), "VALIDATOR", {})
                 for gate in build_metric_manifest().hard_validity_gates)


def run(role, passed=True):
    identity = deterministic_run_id(("EXP",), ("CFG",), (role.value,), None, role)
    return ExperimentRunRecord(
        identity, ("EXP",), ("CFG",), (role.value,), None, role,
        "NOT_EXECUTED_STEP_5J_1", "SYNTHETIC_SCHEMA_VALIDATION", {}, {}, (),
        gates(passed), (), None, "UNCOMMITTED_WORKTREE", {},
    )


def test_invalid_and_nonvalidation_runs_are_excluded_from_comparison():
    valid, invalid, training = run(ScenarioRole.VALIDATION), run(ScenarioRole.VALIDATION, False), run(ScenarioRole.TRAINING)
    assert valid_runs_for_comparison((invalid, training, valid)) == (valid,)


def decision(heldout=False):
    return dict(
        selection_id=("SELECT",), experiment_id=("EXP",), choice_id="learning_rate",
        candidate_configuration_ids=(), eligible_configuration_ids=(),
        rejected_configuration_ids=(), primary_metric_id="TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        comparison_method="NOT_SELECTED", selected_configuration_id=None,
        selected_value=None, evidence_run_ids=(), validation_manifest_id=("VALIDATION",),
        held_out_test_used=heldout, decision_status="FRAMEWORK_READY_NO_SELECTION_RUN",
        provenance={},
    )


def test_selection_record_has_no_choice_and_rejects_heldout_leakage():
    selected = create_selection_decision(**decision())
    assert selected.selected_configuration_id is None and selected.selected_value is None
    with pytest.raises(ExperimentalFrameworkError, match="HELD_OUT_TEST_LEAKAGE_IN_SELECTION"):
        create_selection_decision(**decision(True))


def test_step5j2_ready_but_final_training_blocked():
    assert assess_step_5j_2_readiness() == "READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS"
    ready, blockers = assess_final_training_readiness()
    assert not ready
    assert {"ARCHITECTURE_CHOICES_UNRESOLVED", "OPTIMIZER_UNRESOLVED",
            "MULTI_FACTOR_AGGREGATION_UNRESOLVED", "SAFETY_SHIELD_NOT_IMPLEMENTED"}.issubset(blockers)


def test_manifest_run_metric_and_selection_records_are_immutable():
    source = {"revision": "dirty"}
    manifest = ExperimentManifest(
        ("EXP",), "ARCHITECTURE_STUDY", "question", "hypothesis", (), (),
        ("TRAIN",), ("VALID",), ("TEST",), ("REPLICATION",), ("METRICS",),
        ("GATES",), ("SELECTION",), "PYTHON_PROJECT", source, {}, {},
    )
    source["revision"] = "changed"
    assert manifest.code_revision_metadata["revision"] == "dirty"
    with pytest.raises(FrozenInstanceError):
        manifest.experiment_family = "changed"
    metric = SelectionMetricRecord(("RUN",), "TOTAL_TEAM_TRAVEL_TIME_SECONDS", 1.0,
                                   "vehicle-seconds", MetricDirection.LOWER_IS_BETTER,
                                   "EPISODE", ("VALID",), {})
    assert metric.direction is MetricDirection.LOWER_IS_BETTER


def test_no_training_optimizer_defaults_or_numerical_candidates_in_framework():
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("experimentation").glob("*.py"))
    forbidden = ("torch.optim", "optimizer(", ".backward(", ".step(",
                 "learning_rate =", "clip_epsilon =", "gamma =", "seed =",
                 "train_split", "validation_split", "test_split")
    assert not any(item in source for item in forbidden)

