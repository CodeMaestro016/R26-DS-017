"""Auditable Step 5J.1 registries and readiness gates; no training."""

from .models import *


class ExperimentalFrameworkError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ExperimentalChoiceRegistry:
    def __init__(self, choices=()):
        self._choices = {}
        for choice in choices:
            self.register(choice)

    def register(self, choice):
        prior = self._choices.get(choice.choice_id)
        if prior is not None and prior != choice:
            raise ExperimentalFrameworkError("CONFLICTING_EXPERIMENTAL_CHOICE")
        self._choices[choice.choice_id] = choice
        return choice

    def get(self, choice_id):
        return self._choices[choice_id]

    def all(self):
        return tuple(self._choices[key] for key in sorted(self._choices))

    def by_classification(self, classification):
        return tuple(item for item in self.all() if item.classification is classification)

    @property
    def selected_empirical_value_count(self):
        return sum(item.selected_value is not None for item in self.all()
                   if item.classification in {
                       ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                       ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                       ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                   })


def _choice(choice_id, name, component, classification, basis, dependencies=()):
    unresolved = classification in {
        ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
        ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
        ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
    }
    return ExperimentalChoice(
        choice_id, name, component, classification,
        "REQUIRES_EXPERIMENTAL_SELECTION" if unresolved else "FIXED_BASELINE",
        basis, "CANDIDATE_VALUES_NOT_YET_SELECTED" if unresolved else "NOT_APPLICABLE",
        "SELECTION_PROTOCOL_NOT_YET_DEFINED" if unresolved else "NOT_TUNABLE",
        None, "NOT_SELECTED" if unresolved else "FIXED_NOT_EMPIRICAL", (),
        tuple(dependencies), {"checkpoint": "STEP_5J_1"},
    )


def build_project_choice_registry():
    fixed = (
        _choice("reward_definition", "Negative team vehicle-time exposure", "OBJECTIVE", ChoiceClassification.MATHEMATICALLY_FIXED, "STEP_5H_OBJECTIVE"),
        _choice("return_definition", "Exact undiscounted episodic suffix return", "RETURN", ChoiceClassification.MATHEMATICALLY_FIXED, "OBJECTIVE_PRESERVATION"),
        _choice("advantage_baseline", "Monte Carlo return minus centralized value", "ADVANTAGE", ChoiceClassification.MATHEMATICALLY_FIXED, "STEP_5I_BASELINE"),
        _choice("regulatory_rules", "German StVO constraints", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "LEGAL_ODD"),
        _choice("hard_action_masks", "Hard Boolean feasibility masks", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "INVALID_ACTION_EXCLUSION"),
        _choice("claim_ownership", "Precedence claim ownership", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "CLAIM_SEMANTICS"),
        _choice("protocol_consistency", "Agreement protocol consistency", "AUTHORITY", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "DETERMINISTIC_PROTOCOL"),
        _choice("claim_direction", "Yielding to priority edge direction", "GRAPH", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "VALIDATED_EDGE_SEMANTICS"),
        _choice("action_vocabularies", "Role-specific semantic action vocabularies", "POLICY", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "VALIDATED_PROTOCOL_ACTIONS"),
        _choice("route_truth_exclusion", "Operational route-truth exclusion", "OBSERVATION", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "ANTI_LEAKAGE_REQUIREMENT"),
        _choice("node_input_dimension", "Node input dimension", "GNN", ChoiceClassification.SCHEMA_DERIVED, "NODE_NUMERIC_SCHEMA"),
        _choice("edge_input_dimension", "Edge input dimension", "GNN", ChoiceClassification.SCHEMA_DERIVED, "EDGE_NUMERIC_SCHEMA"),
        _choice("claim_semantic_dimension", "Claim semantic dimension", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "STEP_5F_1_SCHEMA"),
        _choice("protocol_state_dimension", "Protocol-state dimension", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "PROTOCOL_STATE_ENUM"),
        _choice("role_action_count", "Two actions per role", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "ACTION_VOCABULARIES"),
    )
    architecture = (
        "gnn_hidden_dimension", "gnn_message_passing_layers",
        "actor_head_architecture", "responder_head_architecture",
        "centralized_critic_architecture", "parameter_sharing_strategy",
        "gnn_training_mode", "neural_initialization_policy",
    )
    empirical = (
        "ppo_clip_epsilon", "learning_rate", "optimizer_family",
        "minibatch_construction", "ppo_update_epochs", "advantage_normalization",
        "entropy_regularization", "value_loss_handling", "gradient_clipping",
        "weight_decay", "multi_policy_factor_aggregation",
        "training_scenario_composition", "replication_protocol",
        "early_stopping_policy", "checkpoint_selection_rule", "training_budget",
        "statistical_comparison_method", "tie_breaking_rule",
    )
    choices = list(fixed)
    choices.extend(_choice(item, item.replace("_", " ").title(), "ARCHITECTURE",
                           ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                           "COMPATIBLE_ALTERNATIVES_REQUIRE_PROJECT_ABLATION")
                   for item in architecture)
    choices.extend(_choice(item, item.replace("_", " ").title(), "TRAINING_METHOD",
                           ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                           "METHOD_SUPPORTED_NUMERICAL_OR_DESIGN_CHOICE_PROJECT_SPECIFIC")
                   for item in empirical)
    choices.extend((
        _choice("gae_estimator", "Generalized advantage estimation", "ESTIMATOR",
                ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                "BASELINE_USES_EXACT_MONTE_CARLO_ADVANTAGE"),
        _choice("gae_lambda", "GAE lambda", "ESTIMATOR",
                ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                "ONLY_APPLICABLE_IF_GAE_ABLATION_ENABLED", ("gae_estimator",)),
    ))
    return ExperimentalChoiceRegistry(choices)


HARD_VALIDITY_GATES = (
    "HARD_ACTION_MASK_INVARIANT", "REGULATORY_INVARIANT",
    "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
    "FINITE_NETWORK_OUTPUTS", "VALID_ACTION_PROBABILITIES",
    "FINITE_TRAINING_QUANTITIES", "CAUSAL_TRANSITION_INTEGRITY",
    "OBJECTIVE_ACCOUNTING_NO_DOUBLE_COUNT",
)


def build_metric_manifest():
    return ExperimentMetricManifest(
        ("STEP_5J_1_METRICS",), "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        MetricDirection.LOWER_IS_BETTER, "RAW_SHARED_TEAM_REWARD",
        ("THROUGHPUT", "MEAN_TRAVEL_TIME", "MAXIMUM_TRAVEL_TIME",
         "TRAVEL_TIME_VARIANCE", "COLLISION_COUNT", "MODEL_COMPLEXITY",
         "TRAINING_STABILITY"), HARD_VALIDITY_GATES, False,
    )


def create_scenario_manifest(*, manifest_id, purpose, scenario_ids,
                             scenario_generation_source, demand_schedule_identity,
                             intersection_network_identity, vehicle_type_identity,
                             regulatory_profile, perception_configuration_identity,
                             intention_model_identity, randomization_provenance,
                             frozen_status):
    role = purpose if isinstance(purpose, ScenarioRole) else ScenarioRole(purpose)
    return ScenarioManifest(
        manifest_id, role, tuple(scenario_ids), scenario_generation_source,
        demand_schedule_identity, intersection_network_identity,
        vehicle_type_identity, regulatory_profile,
        perception_configuration_identity, intention_model_identity,
        randomization_provenance, frozen_status,
        role is ScenarioRole.VALIDATION,
    )


def create_configuration(registry, assignments, *, architecture_identity,
                         training_method_identity, regulatory_profile,
                         semantic_schema_versions, require_resolved=False):
    assignments = dict(assignments)
    unknown = set(assignments) - {item.choice_id for item in registry.all()}
    if unknown:
        raise ExperimentalFrameworkError("UNREGISTERED_EXPERIMENTAL_CHOICE")
    empirical = tuple(item.choice_id for item in registry.all()
                      if item.classification in {
                          ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                          ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                      })
    unresolved = tuple(sorted(set(empirical) - set(assignments)))
    if require_resolved and unresolved:
        raise ExperimentalFrameworkError("EXPERIMENTAL_CHOICE_UNRESOLVED")
    fixed = tuple(item.choice_id for item in registry.all()
                  if item.classification in {
                      ChoiceClassification.MATHEMATICALLY_FIXED,
                      ChoiceClassification.REGULATORY_FIXED,
                      ChoiceClassification.SCHEMA_DERIVED,
                      ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT,
                  })
    identity = ("CONFIGURATION", tuple(sorted(assignments.items(), key=lambda x: x[0])),
                fixed, architecture_identity, training_method_identity,
                "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1",
                "EXACT_UNDISCOUNTED_TEAM_RETURN_V1", regulatory_profile,
                tuple(semantic_schema_versions))
    return ExperimentalConfiguration(
        identity, assignments, unresolved, fixed, architecture_identity,
        training_method_identity, "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1",
        "EXACT_UNDISCOUNTED_TEAM_RETURN_V1", regulatory_profile,
        tuple(semantic_schema_versions), {"silent_defaults": "FORBIDDEN"},
    )


def deterministic_run_id(experiment_id, configuration_id, scenario_manifest_id,
                         seed_identity, run_role):
    role = run_role.value if isinstance(run_role, ScenarioRole) else ScenarioRole(run_role).value
    return ("RUN", experiment_id, configuration_id, scenario_manifest_id,
            seed_identity, role)


def create_selection_decision(**kwargs):
    decision = SelectionDecisionRecord(**kwargs)
    if decision.held_out_test_used:
        raise ExperimentalFrameworkError("HELD_OUT_TEST_LEAKAGE_IN_SELECTION")
    if decision.selected_configuration_id is not None or decision.selected_value is not None:
        raise ExperimentalFrameworkError("STEP_5J_1_SELECTION_NOT_PERMITTED")
    return decision


def valid_runs_for_comparison(run_records):
    return tuple(run for run in run_records
                 if run.run_role is ScenarioRole.VALIDATION and
                 all(result.passed for result in run.validity_gate_results))


def assess_step_5j_2_readiness():
    registry = build_project_choice_registry()
    required = (registry.all(), tuple(ScenarioRole), CandidateSetDefinition,
                build_metric_manifest().hard_validity_gates, SeedManifest,
                ExperimentRunRecord, SelectionDecisionRecord, ExperimentManifest)
    return ("READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS"
            if all(required) else "EXPERIMENTAL_FRAMEWORK_INCOMPLETE")


def assess_final_training_readiness():
    blockers = (
        "ARCHITECTURE_CHOICES_UNRESOLVED", "OPTIMIZER_UNRESOLVED",
        "LEARNING_RATE_UNRESOLVED", "PPO_CLIP_UNRESOLVED",
        "MULTI_FACTOR_AGGREGATION_UNRESOLVED", "TRAINING_BUDGET_UNRESOLVED",
        "REPLICATION_DESIGN_UNRESOLVED", "SCENARIO_MANIFESTS_UNRESOLVED",
        "SELECTION_RULE_UNRESOLVED", "SAFETY_SHIELD_NOT_IMPLEMENTED",
    )
    return False, blockers

