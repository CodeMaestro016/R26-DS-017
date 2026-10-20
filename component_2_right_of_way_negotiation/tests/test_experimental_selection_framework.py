# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import pytest for use in this module.
import pytest

# Import CandidateSetDefinition, ChoiceClassification, ExperimentManifest, ExperimentRunRecord,
# ExperimentalChoice, ExperimentalChoiceRegistry, ExperimentalFrameworkError,... from experimentation for the
# operations below.
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


# Check all choice classifications are categorical using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_all_choice_classifications_are_categorical():
    # Require a set of item.value for item in ChoiceClassification equals a set containing the text
    # 'MATHEMATICALLY_FIXED', the text 'PHYSICALLY_DERIVED', the text 'REGULATORY_FIXED', the text...; otherwise
    # raise AssertionError.
    assert {item.value for item in ChoiceClassification} == {
        "MATHEMATICALLY_FIXED", "PHYSICALLY_DERIVED", "REGULATORY_FIXED",
        "SCHEMA_DERIVED", "PROJECT_SEMANTIC_REQUIREMENT",
        "RESEARCH_SUPPORTED_METHOD", "ARCHITECTURE_CHOICE_REQUIRES_ABLATION",
        "REQUIRES_EXPERIMENTAL_SELECTION", "OPTIONAL_FUTURE_ABLATION",
        "NOT_APPLICABLE_TO_BASELINE",
    }


# Check registry contains fixed schema regulatory and empirical choices using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_registry_contains_fixed_schema_regulatory_and_empirical_choices():
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Require registry.get('reward_definition').classification is the same object as
    # ChoiceClassification.MATHEMATICALLY_FIXED; otherwise raise AssertionError.
    assert registry.get("reward_definition").classification is ChoiceClassification.MATHEMATICALLY_FIXED
    # Require registry.get('regulatory_rules').classification is the same object as
    # ChoiceClassification.REGULATORY_FIXED; otherwise raise AssertionError.
    assert registry.get("regulatory_rules").classification is ChoiceClassification.REGULATORY_FIXED
    # Require registry.get('node_input_dimension').classification is the same object as
    # ChoiceClassification.SCHEMA_DERIVED; otherwise raise AssertionError.
    assert registry.get("node_input_dimension").classification is ChoiceClassification.SCHEMA_DERIVED
    # Require registry.get('claim_direction').classification is the same object as
    # ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT; otherwise raise AssertionError.
    assert registry.get("claim_direction").classification is ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT
    # Require registry.get('learning_rate').classification is the same object as
    # ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION; otherwise raise AssertionError.
    assert registry.get("learning_rate").classification is ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION
    # Require registry.get('gnn_hidden_dimension').classification is the same object as
    # ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION; otherwise raise AssertionError.
    assert registry.get("gnn_hidden_dimension").classification is ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION
    # Require registry.get('gae_estimator').classification is the same object as
    # ChoiceClassification.OPTIONAL_FUTURE_ABLATION; otherwise raise AssertionError.
    assert registry.get("gae_estimator").classification is ChoiceClassification.OPTIONAL_FUTURE_ABLATION
    # Require registry.selected_empirical_value_count equals 0; otherwise raise AssertionError.
    assert registry.selected_empirical_value_count == 0


# Check reward gamma claim masks and route exclusion are not tunable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_reward_gamma_claim_masks_and_route_exclusion_are_not_tunable():
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Require registry.get('reward_definition').current_status equals the text 'FIXED_BASELINE'; otherwise raise
    # AssertionError.
    assert registry.get("reward_definition").current_status == "FIXED_BASELINE"
    # Require the text 'gamma' does not belong to a set of item.choice_id for item in the result of
    # registry.all(); otherwise raise AssertionError.
    assert "gamma" not in {item.choice_id for item in registry.all()}
    # Iterate over a tuple containing the text 'claim_direction', the text 'hard_action_masks', the text
    # 'route_truth_exclusion', binding each item to key.
    for key in ("claim_direction", "hard_action_masks", "route_truth_exclusion"):
        # Require registry.get(key).classification does not belong to a set containing
        # ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,...; otherwise raise AssertionError.
        assert registry.get(key).classification not in {
            # Include ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION in this set.
            ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
            # Include ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION in this set.
            ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
        }


# Check duplicate choice conflict and identical idempotence using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_duplicate_choice_conflict_and_identical_idempotence():
    # Set choice to 'learning_rate' from build_project_choice_registry(); use None if absent.
    choice = build_project_choice_registry().get("learning_rate")
    # Set registry to the result of ExperimentalChoiceRegistry(a tuple containing choice, choice).
    registry = ExperimentalChoiceRegistry((choice, choice))
    # Require the number of entries in the result of registry.all() equals 1; otherwise raise AssertionError.
    assert len(registry.all()) == 1
    # Set conflict to the result of ExperimentalChoice(choice.choice_id, the text 'different', choice.component,
    # choice.classification,...).
    conflict = ExperimentalChoice(
        # Supply choice.classification to ExperimentalChoice.
        choice.choice_id, "different", choice.component, choice.classification,
        # Supply choice.mathematical_or_research_basis to ExperimentalChoice.
        choice.current_status, choice.mathematical_or_research_basis,
        # Supply choice.candidate_generation_status to ExperimentalChoice.
        choice.candidate_generation_status, choice.selection_method_status,
        # Supply choice.selected_value_status to ExperimentalChoice.
        None, choice.selected_value_status, (), (), {},
    )
    # Enter the result of pytest.raises(ExperimentalFrameworkError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExperimentalFrameworkError, match="CONFLICTING_EXPERIMENTAL_CHOICE"):
        # Call registry.register with the supplied arguments.
        registry.register(conflict)


# Check candidate sets start empty without numerical values using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_candidate_sets_start_empty_without_numerical_values():
    # Set definition to the result of CandidateSetDefinition(the text 'learning_rate', an empty tuple, None, the
    # text 'NOT_YET_DEFINED', the text...).
    definition = CandidateSetDefinition(
        # Supply an empty tuple to CandidateSetDefinition.
        "learning_rate", (), None, "NOT_YET_DEFINED",
        "STEP_5J_2_CONTROLLED_PILOT_DESIGN",
    )
    # Require definition.candidate_values equals an empty tuple; otherwise raise AssertionError.
    assert definition.candidate_values == ()
    # Require definition.status equals the text 'CANDIDATE_VALUES_NOT_YET_SELECTED'; otherwise raise
    # AssertionError.
    assert definition.status == "CANDIDATE_VALUES_NOT_YET_SELECTED"


# Scenario using the inputs and processing steps below.
# Input role: the supplied role.
# Output: the result of create_scenario_manifest().
def scenario(role):
    # Return the result of create_scenario_manifest() to the caller.
    return create_scenario_manifest(
        # Supply manifest_id as a tuple containing role.value.
        # Supply purpose as role.
        manifest_id=(role.value,), purpose=role,
        # Supply scenario_ids as a tuple containing a tuple containing the text 'network', the text 'demand-A', a
        # tuple containing the text 'network', the...
        scenario_ids=(("network", "demand-A"), ("network", "demand-B")),
        # Supply scenario_generation_source as the text 'EXISTING_DETERMINISTIC_DEMAND'.
        scenario_generation_source="EXISTING_DETERMINISTIC_DEMAND",
        # Supply demand_schedule_identity as a tuple containing the text 'schedule'.
        demand_schedule_identity=("schedule",),
        # Supply intersection_network_identity as the text 'intersection.net.xml'.
        intersection_network_identity="intersection.net.xml",
        # Supply vehicle_type_identity as the text 'AV'.
        # Supply regulatory_profile as the text 'DE_STVO'.
        vehicle_type_identity="AV", regulatory_profile="DE_STVO",
        # Supply perception_configuration_identity as the text 'CURRENT_SENSOR_PROFILE'.
        perception_configuration_identity="CURRENT_SENSOR_PROFILE",
        # Supply intention_model_identity as the text 'CURRENT_ONNX_MODELS'.
        intention_model_identity="CURRENT_ONNX_MODELS",
        # Supply randomization_provenance as an empty dictionary.
        # Supply frozen_status as the text 'FRAMEWORK_CONTRACT_ONLY'.
        randomization_provenance={}, frozen_status="FRAMEWORK_CONTRACT_ONLY",
    )


# Check scenario roles and heldout isolation using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_scenario_roles_and_heldout_isolation():
    # Set (training, validation, heldout) to the result of map(scenario, ScenarioRole).
    training, validation, heldout = map(scenario, ScenarioRole)
    # Require the negation of training.used_for_parameter_selection; otherwise raise AssertionError.
    assert not training.used_for_parameter_selection
    # Require validation.used_for_parameter_selection; otherwise raise AssertionError.
    assert validation.used_for_parameter_selection
    # Require the negation of heldout.used_for_parameter_selection; otherwise raise AssertionError.
    assert not heldout.used_for_parameter_selection
    # Require heldout.scenario_ids equals a tuple built from the sorted values from heldout.scenario_ids;
    # otherwise raise AssertionError.
    assert heldout.scenario_ids == tuple(sorted(heldout.scenario_ids, key=repr))


# Check seed manifest has no default seed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_seed_manifest_has_no_default_seed():
    # Set seed to the result of SeedManifest(a tuple containing the text 'SEEDS', the text 'NOT_SELECTED', an
    # empty tuple, the text...).
    seed = SeedManifest(("SEEDS",), "NOT_SELECTED", (), "REPLICATION", "UNRESOLVED", {})
    # Require seed.seed_values equals an empty tuple; otherwise raise AssertionError.
    assert seed.seed_values == ()


# Check partial configuration is deterministic and strict mode rejects using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_partial_configuration_is_deterministic_and_strict_mode_rejects():
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Set kwargs to a dictionary built from the supplied values.
    kwargs = dict(architecture_identity="UNRESOLVED", training_method_identity="UNRESOLVED",
                  # Supply regulatory_profile as the text 'DE_STVO'.
                  # Supply semantic_schema_versions as a tuple containing the text 'NODE_V1'.
                  regulatory_profile="DE_STVO", semantic_schema_versions=("NODE_V1",))
    # Set first to the result of create_configuration(registry, an empty dictionary).
    first = create_configuration(registry, {}, **kwargs)
    # Set second to the result of create_configuration(registry, an empty dictionary).
    second = create_configuration(registry, {}, **kwargs)
    # Require first.configuration_id equals second.configuration_id; otherwise raise AssertionError.
    assert first.configuration_id == second.configuration_id
    # Require first.unresolved_choices; otherwise raise AssertionError.
    assert first.unresolved_choices
    # Enter the result of pytest.raises(ExperimentalFrameworkError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExperimentalFrameworkError, match="EXPERIMENTAL_CHOICE_UNRESOLVED"):
        # Call create_configuration with the supplied arguments.
        create_configuration(registry, {}, require_resolved=True, **kwargs)


# Check configuration identity is assignment order invariant using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_configuration_identity_is_assignment_order_invariant():
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Set kwargs to a dictionary built from the supplied values.
    kwargs = dict(architecture_identity="DECLARED", training_method_identity="DECLARED",
                  # Supply regulatory_profile as the text 'DE_STVO'.
                  # Supply semantic_schema_versions as an empty tuple.
                  regulatory_profile="DE_STVO", semantic_schema_versions=())
    # Set a to the result of create_configuration(registry, a dictionary containing learning_rate,
    # optimizer_family).
    a = create_configuration(registry, {"learning_rate": "A", "optimizer_family": "B"}, **kwargs)
    # Set b to the result of create_configuration(registry, a dictionary containing optimizer_family,
    # learning_rate).
    b = create_configuration(registry, {"optimizer_family": "B", "learning_rate": "A"}, **kwargs)
    # Require a.configuration_id equals b.configuration_id; otherwise raise AssertionError.
    assert a.configuration_id == b.configuration_id


# Check metric manifest has one physical primary and no composite using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_metric_manifest_has_one_physical_primary_and_no_composite():
    # Set metrics to the result of build_metric_manifest().
    metrics = build_metric_manifest()
    # Require metrics.primary_selection_metric equals the text 'TOTAL_TEAM_TRAVEL_TIME_SECONDS'; otherwise raise
    # AssertionError.
    assert metrics.primary_selection_metric == "TOTAL_TEAM_TRAVEL_TIME_SECONDS"
    # Require metrics.primary_direction is the same object as MetricDirection.LOWER_IS_BETTER; otherwise raise
    # AssertionError.
    assert metrics.primary_direction is MetricDirection.LOWER_IS_BETTER
    # Require the text 'THROUGHPUT' belongs to metrics.secondary_diagnostics; otherwise raise AssertionError.
    assert "THROUGHPUT" in metrics.secondary_diagnostics
    # Require the text 'TRAVEL_TIME_VARIANCE' belongs to metrics.secondary_diagnostics; otherwise raise
    # AssertionError.
    assert "TRAVEL_TIME_VARIANCE" in metrics.secondary_diagnostics
    # Require the negation of metrics.weighted_composite_score; otherwise raise AssertionError.
    assert not metrics.weighted_composite_score


# Gates using the inputs and processing steps below.
# Input passed: the supplied passed.
# Output: a tuple built from a lazy sequence of the result of ValidityGateResult(gate, passed, a tuple containing
# 'evidence', the text 'VALIDATOR', an empty dictionary) for gate in...
def gates(passed=True):
    # Return a tuple built from a lazy sequence of the result of ValidityGateResult(gate, passed, a tuple
    # containing 'evidence', the text 'VALIDATOR', an empty dictionary) for gate in
    # build_metric_manifest().hard_validity_gates to the caller.
    return tuple(ValidityGateResult(gate, passed, ("evidence",), "VALIDATOR", {})
                 # Evaluate build_metric_manifest().hard_validity_gates as part of the enclosing expression.
                 for gate in build_metric_manifest().hard_validity_gates)


# Run using the inputs and processing steps below.
# Input role: the supplied role.
# Input passed: the supplied passed.
# Output: the result of ExperimentRunRecord(identity, a tuple containing the text 'EXP', a tuple containing the
# text 'CFG', a tuple...).
def run(role, passed=True):
    # Set identity to the result of deterministic_run_id(a tuple containing the text 'EXP', a tuple containing the
    # text 'CFG', a tuple containing...).
    identity = deterministic_run_id(("EXP",), ("CFG",), (role.value,), None, role)
    # Return the result of ExperimentRunRecord(identity, a tuple containing the text 'EXP', a tuple containing the
    # text 'CFG', a tuple...) to the caller.
    return ExperimentRunRecord(
        # Supply a tuple containing role.value to ExperimentRunRecord.
        identity, ("EXP",), ("CFG",), (role.value,), None, role,
        # Supply an empty dictionary to ExperimentRunRecord.
        "NOT_EXECUTED_STEP_5J_1", "SYNTHETIC_SCHEMA_VALIDATION", {}, {}, (),
        # Supply the result of gates(passed) to ExperimentRunRecord.
        gates(passed), (), None, "UNCOMMITTED_WORKTREE", {},
    )


# Check invalid and nonvalidation runs are excluded from comparison using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_invalid_and_nonvalidation_runs_are_excluded_from_comparison():
    # Set (valid, invalid, training) to a tuple containing the result of run(ScenarioRole.VALIDATION), the result
    # of run(ScenarioRole.VALIDATION, False), the result...
    valid, invalid, training = run(ScenarioRole.VALIDATION), run(ScenarioRole.VALIDATION, False), run(ScenarioRole.TRAINING)
    # Require the result of valid_runs_for_comparison(a tuple containing invalid, training, valid) equals a tuple
    # containing valid; otherwise raise AssertionError.
    assert valid_runs_for_comparison((invalid, training, valid)) == (valid,)


# Decision using the inputs and processing steps below.
# Input heldout: the supplied heldout.
# Output: a dictionary built from the supplied values.
def decision(heldout=False):
    # Return a dictionary built from the supplied values to the caller.
    return dict(
        # Supply selection_id as a tuple containing the text 'SELECT'.
        # Supply experiment_id as a tuple containing the text 'EXP'.
        # Supply choice_id as the text 'learning_rate'.
        selection_id=("SELECT",), experiment_id=("EXP",), choice_id="learning_rate",
        # Supply candidate_configuration_ids as an empty tuple.
        # Supply eligible_configuration_ids as an empty tuple.
        candidate_configuration_ids=(), eligible_configuration_ids=(),
        # Supply rejected_configuration_ids as an empty tuple.
        # Supply primary_metric_id as the text 'TOTAL_TEAM_TRAVEL_TIME_SECONDS'.
        rejected_configuration_ids=(), primary_metric_id="TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        # Supply comparison_method as the text 'NOT_SELECTED'.
        # Supply selected_configuration_id as None.
        comparison_method="NOT_SELECTED", selected_configuration_id=None,
        # Supply selected_value as None.
        # Supply evidence_run_ids as an empty tuple.
        # Supply validation_manifest_id as a tuple containing the text 'VALIDATION'.
        selected_value=None, evidence_run_ids=(), validation_manifest_id=("VALIDATION",),
        # Supply held_out_test_used as heldout.
        # Supply decision_status as the text 'FRAMEWORK_READY_NO_SELECTION_RUN'.
        held_out_test_used=heldout, decision_status="FRAMEWORK_READY_NO_SELECTION_RUN",
        # Supply provenance as an empty dictionary.
        provenance={},
    )


# Check selection record has no choice and rejects heldout leakage using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_selection_record_has_no_choice_and_rejects_heldout_leakage():
    # Set selected to the result of create_selection_decision().
    selected = create_selection_decision(**decision())
    # Require selected.selected_configuration_id is the same object as None and selected.selected_value is the
    # same object as None; otherwise raise AssertionError.
    assert selected.selected_configuration_id is None and selected.selected_value is None
    # Enter the result of pytest.raises(ExperimentalFrameworkError) and run the enclosed operations within that
    # context.
    with pytest.raises(ExperimentalFrameworkError, match="HELD_OUT_TEST_LEAKAGE_IN_SELECTION"):
        # Call create_selection_decision with the supplied arguments.
        create_selection_decision(**decision(True))


# Check step5j2 ready but final training blocked using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_step5j2_ready_but_final_training_blocked():
    # Require the result of assess_step_5j_2_readiness() equals the text
    # 'READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS'; otherwise raise AssertionError.
    assert assess_step_5j_2_readiness() == "READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS"
    # Set (ready, blockers) to the result of assess_final_training_readiness().
    ready, blockers = assess_final_training_readiness()
    # Require the negation of ready; otherwise raise AssertionError.
    assert not ready
    # Require the result of {'ARCHITECTURE_CHOICES_UNRESOLVED', 'OPTIMIZER_UNRESOLVED',...(blockers); otherwise
    # raise AssertionError.
    assert {"ARCHITECTURE_CHOICES_UNRESOLVED", "OPTIMIZER_UNRESOLVED",
            # Supply blockers to {'ARCHITECTURE_CHOICES_UNRESOLVED', 'OPTIMIZER_UNRESOLVED',...
            "MULTI_FACTOR_AGGREGATION_UNRESOLVED", "SAFETY_SHIELD_NOT_IMPLEMENTED"}.issubset(blockers)


# Check manifest run metric and selection records are immutable using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_manifest_run_metric_and_selection_records_are_immutable():
    # Set source to a dictionary containing revision.
    source = {"revision": "dirty"}
    # Set manifest to the result of ExperimentManifest(a tuple containing the text 'EXP', the text
    # 'ARCHITECTURE_STUDY', the text 'question', the text...).
    manifest = ExperimentManifest(
        # Supply a tuple containing the text 'EXP' to ExperimentManifest.
        ("EXP",), "ARCHITECTURE_STUDY", "question", "hypothesis", (), (),
        # Supply a tuple containing the text 'REPLICATION' to ExperimentManifest.
        ("TRAIN",), ("VALID",), ("TEST",), ("REPLICATION",), ("METRICS",),
        # Supply a tuple containing the text 'SELECTION' to ExperimentManifest.
        ("GATES",), ("SELECTION",), "PYTHON_PROJECT", source, {}, {},
    )
    # Set source['revision'] to the text 'changed'.
    source["revision"] = "changed"
    # Require manifest.code_revision_metadata at 'revision' equals the text 'dirty'; otherwise raise
    # AssertionError.
    assert manifest.code_revision_metadata["revision"] == "dirty"
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set manifest.experiment_family to the text 'changed'.
        manifest.experiment_family = "changed"
    # Set metric to the result of SelectionMetricRecord(a tuple containing the text 'RUN', the text
    # 'TOTAL_TEAM_TRAVEL_TIME_SECONDS', 1.0, the text...).
    metric = SelectionMetricRecord(("RUN",), "TOTAL_TEAM_TRAVEL_TIME_SECONDS", 1.0,
                                   # Supply MetricDirection.LOWER_IS_BETTER to SelectionMetricRecord.
                                   "vehicle-seconds", MetricDirection.LOWER_IS_BETTER,
                                   # Supply a tuple containing the text 'VALID' to SelectionMetricRecord.
                                   "EPISODE", ("VALID",), {})
    # Require metric.direction is the same object as MetricDirection.LOWER_IS_BETTER; otherwise raise
    # AssertionError.
    assert metric.direction is MetricDirection.LOWER_IS_BETTER


# Check no training optimizer defaults or numerical candidates in framework using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_no_training_optimizer_defaults_or_numerical_candidates_in_framework():
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('experimentation').glob(the text '*.py') as part of the
                       # enclosing expression.
                       for path in Path("experimentation").glob("*.py"))
    # Set forbidden to a tuple containing the text 'torch.optim', the text 'optimizer(', the text '.backward(',
    # the text '.step(', the text...
    forbidden = ("torch.optim", "optimizer(", ".backward(", ".step(",
                 "learning_rate =", "clip_epsilon =", "gamma =", "seed =",
                 "train_split", "validation_split", "test_split")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)

