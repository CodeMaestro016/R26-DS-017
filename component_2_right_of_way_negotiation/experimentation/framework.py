"""Auditable Step 5J.1 registries and readiness gates; no training."""

# Import * from .models for the operations below.
from .models import *


# Define ExperimentalFrameworkError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ExperimentalFrameworkError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Define ExperimentalChoiceRegistry to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class ExperimentalChoiceRegistry:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input choices: the supplied choices.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def __init__(self, choices=()):
        # Set self._choices to an empty dictionary.
        self._choices = {}
        # Iterate over choices, binding each item to choice.
        for choice in choices:
            # Call self.register with the supplied arguments.
            self.register(choice)

    # Register using the inputs and processing steps below.
    # Input choice: the supplied choice.
    # Output: choice.
    # Processing: select branches using the stated conditions.
    def register(self, choice):
        # Set prior to choice.choice_id from self._choices; use None if absent.
        prior = self._choices.get(choice.choice_id)
        # Run this branch when prior is a different object from None and prior differs from choice.
        if prior is not None and prior != choice:
            # Raise ExperimentalFrameworkError with the text 'CONFLICTING_EXPERIMENTAL_CHOICE' to stop this
            # execution path.
            raise ExperimentalFrameworkError("CONFLICTING_EXPERIMENTAL_CHOICE")
        # Set self._choices[choice.choice_id] to choice.
        self._choices[choice.choice_id] = choice
        # Return choice to the caller.
        return choice

    # Get using the inputs and processing steps below.
    # Input choice_id: the supplied choice id.
    # Output: self._choices at choice_id.
    def get(self, choice_id):
        # Return self._choices at choice_id to the caller.
        return self._choices[choice_id]

    # All using the inputs and processing steps below.
    # Output: a tuple built from a lazy sequence of self._choices at key for key in the sorted values from
    # self._choices.
    def all(self):
        # Return a tuple built from a lazy sequence of self._choices at key for key in the sorted values from
        # self._choices to the caller.
        return tuple(self._choices[key] for key in sorted(self._choices))

    # By classification using the inputs and processing steps below.
    # Input classification: the supplied classification.
    # Output: a tuple built from a lazy sequence of item for item in the result of self.all(); retain entries
    # satisfying item.classification is the same object as classification.
    def by_classification(self, classification):
        # Return a tuple built from a lazy sequence of item for item in the result of self.all(); retain entries
        # satisfying item.classification is the same object as classification to the caller.
        return tuple(item for item in self.all() if item.classification is classification)

    # Apply property as a decorator to configure the following definition.
    @property
    # Selected empirical value count using the inputs and processing steps below.
    # Output: the sum of a lazy sequence of item.selected_value is a different object from None for item in the
    # result of self.all(); retain entries satisfying item.classification belongs to a set...
    def selected_empirical_value_count(self):
        # Return the sum of a lazy sequence of item.selected_value is a different object from None for item in the
        # result of self.all(); retain entries satisfying item.classification belongs to a set containing... to
        # the caller.
        return sum(item.selected_value is not None for item in self.all()
                   # Evaluate item.classification belongs to a set containing
                   # ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,... as part of the enclosing expression.
                   if item.classification in {
                       # Include ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION in this set.
                       ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                       # Include ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION in this set.
                       ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                       # Include ChoiceClassification.OPTIONAL_FUTURE_ABLATION in this set.
                       ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                   })


# Choice using the inputs and processing steps below.
# Input choice_id: the supplied choice id.
# Input name: the supplied name.
# Input component: the supplied component.
# Input classification: the supplied classification.
# Input basis: the supplied basis.
# Input dependencies: the supplied dependencies.
# Output: the result of ExperimentalChoice(choice_id, name, component, classification, the text
# 'REQUIRES_EXPERIMENTAL_SELECTION' when...).
def _choice(choice_id, name, component, classification, basis, dependencies=()):
    # Set unresolved to classification belongs to a set containing
    # ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,...
    unresolved = classification in {
        # Include ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION in this set.
        ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
        # Include ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION in this set.
        ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
        # Include ChoiceClassification.OPTIONAL_FUTURE_ABLATION in this set.
        ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
    }
    # Return the result of ExperimentalChoice(choice_id, name, component, classification, the text
    # 'REQUIRES_EXPERIMENTAL_SELECTION' when...) to the caller.
    return ExperimentalChoice(
        # Supply classification to ExperimentalChoice.
        choice_id, name, component, classification,
        # Supply the text 'REQUIRES_EXPERIMENTAL_SELECTION' when unresolved, otherwise the text 'FIXED_BASELINE'
        # to ExperimentalChoice.
        "REQUIRES_EXPERIMENTAL_SELECTION" if unresolved else "FIXED_BASELINE",
        # Supply the text 'CANDIDATE_VALUES_NOT_YET_SELECTED' when unresolved, otherwise the text 'NOT_APPLICABLE'
        # to ExperimentalChoice.
        basis, "CANDIDATE_VALUES_NOT_YET_SELECTED" if unresolved else "NOT_APPLICABLE",
        # Supply the text 'SELECTION_PROTOCOL_NOT_YET_DEFINED' when unresolved, otherwise the text 'NOT_TUNABLE'
        # to ExperimentalChoice.
        "SELECTION_PROTOCOL_NOT_YET_DEFINED" if unresolved else "NOT_TUNABLE",
        # Supply the text 'NOT_SELECTED' when unresolved, otherwise the text 'FIXED_NOT_EMPIRICAL' to
        # ExperimentalChoice.
        None, "NOT_SELECTED" if unresolved else "FIXED_NOT_EMPIRICAL", (),
        # Store the text 'STEP_5J_1' under 'checkpoint'.
        tuple(dependencies), {"checkpoint": "STEP_5J_1"},
    )


# Build project choice registry using the inputs and processing steps below.
# Output: the result of ExperimentalChoiceRegistry(choices).
def build_project_choice_registry():
    # Set fixed to a tuple containing the result of _choice(the text 'reward_definition', the text 'Negative team
    # vehicle-time exposure', the...
    fixed = (
        # Include the result of _choice(the text 'reward_definition', the text 'Negative team vehicle-time
        # exposure', the text...) in this tuple.
        _choice("reward_definition", "Negative team vehicle-time exposure", "OBJECTIVE", ChoiceClassification.MATHEMATICALLY_FIXED, "STEP_5H_OBJECTIVE"),
        # Include the result of _choice(the text 'return_definition', the text 'Exact undiscounted episodic suffix
        # return', the text...) in this tuple.
        _choice("return_definition", "Exact undiscounted episodic suffix return", "RETURN", ChoiceClassification.MATHEMATICALLY_FIXED, "OBJECTIVE_PRESERVATION"),
        # Include the result of _choice(the text 'advantage_baseline', the text 'Monte Carlo return minus
        # centralized value', the text...) in this tuple.
        _choice("advantage_baseline", "Monte Carlo return minus centralized value", "ADVANTAGE", ChoiceClassification.MATHEMATICALLY_FIXED, "STEP_5I_BASELINE"),
        # Include the result of _choice(the text 'regulatory_rules', the text 'German StVO constraints', the text
        # 'AUTHORITY',...) in this tuple.
        _choice("regulatory_rules", "German StVO constraints", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "LEGAL_ODD"),
        # Include the result of _choice(the text 'hard_action_masks', the text 'Hard Boolean feasibility masks',
        # the text 'AUTHORITY',...) in this tuple.
        _choice("hard_action_masks", "Hard Boolean feasibility masks", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "INVALID_ACTION_EXCLUSION"),
        # Include the result of _choice(the text 'claim_ownership', the text 'Precedence claim ownership', the
        # text 'AUTHORITY',...) in this tuple.
        _choice("claim_ownership", "Precedence claim ownership", "AUTHORITY", ChoiceClassification.REGULATORY_FIXED, "CLAIM_SEMANTICS"),
        # Include the result of _choice(the text 'protocol_consistency', the text 'Agreement protocol
        # consistency', the text...) in this tuple.
        _choice("protocol_consistency", "Agreement protocol consistency", "AUTHORITY", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "DETERMINISTIC_PROTOCOL"),
        # Include the result of _choice(the text 'claim_direction', the text 'Yielding to priority edge
        # direction', the text 'GRAPH',...) in this tuple.
        _choice("claim_direction", "Yielding to priority edge direction", "GRAPH", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "VALIDATED_EDGE_SEMANTICS"),
        # Include the result of _choice(the text 'action_vocabularies', the text 'Role-specific semantic action
        # vocabularies', the text...) in this tuple.
        _choice("action_vocabularies", "Role-specific semantic action vocabularies", "POLICY", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "VALIDATED_PROTOCOL_ACTIONS"),
        # Include the result of _choice(the text 'route_truth_exclusion', the text 'Operational route-truth
        # exclusion', the text...) in this tuple.
        _choice("route_truth_exclusion", "Operational route-truth exclusion", "OBSERVATION", ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT, "ANTI_LEAKAGE_REQUIREMENT"),
        # Include the result of _choice(the text 'node_input_dimension', the text 'Node input dimension', the text
        # 'GNN',...) in this tuple.
        _choice("node_input_dimension", "Node input dimension", "GNN", ChoiceClassification.SCHEMA_DERIVED, "NODE_NUMERIC_SCHEMA"),
        # Include the result of _choice(the text 'edge_input_dimension', the text 'Edge input dimension', the text
        # 'GNN',...) in this tuple.
        _choice("edge_input_dimension", "Edge input dimension", "GNN", ChoiceClassification.SCHEMA_DERIVED, "EDGE_NUMERIC_SCHEMA"),
        # Include the result of _choice(the text 'claim_semantic_dimension', the text 'Claim semantic dimension',
        # the text 'POLICY',...) in this tuple.
        _choice("claim_semantic_dimension", "Claim semantic dimension", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "STEP_5F_1_SCHEMA"),
        # Include the result of _choice(the text 'protocol_state_dimension', the text 'Protocol-state dimension',
        # the text 'POLICY',...) in this tuple.
        _choice("protocol_state_dimension", "Protocol-state dimension", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "PROTOCOL_STATE_ENUM"),
        # Include the result of _choice(the text 'role_action_count', the text 'Two actions per role', the text
        # 'POLICY',...) in this tuple.
        _choice("role_action_count", "Two actions per role", "POLICY", ChoiceClassification.SCHEMA_DERIVED, "ACTION_VOCABULARIES"),
    )
    # Set architecture to a tuple containing the text 'gnn_hidden_dimension', the text
    # 'gnn_message_passing_layers', the text...
    architecture = (
        "gnn_hidden_dimension", "gnn_message_passing_layers",
        "actor_head_architecture", "responder_head_architecture",
        "centralized_critic_architecture", "parameter_sharing_strategy",
        "gnn_training_mode", "neural_initialization_policy",
    )
    # Set empirical to a tuple containing the text 'ppo_clip_epsilon', the text 'learning_rate', the text
    # 'optimizer_family', the text...
    empirical = (
        "ppo_clip_epsilon", "learning_rate", "optimizer_family",
        "minibatch_construction", "ppo_update_epochs", "advantage_normalization",
        "entropy_regularization", "value_loss_handling", "gradient_clipping",
        "weight_decay", "multi_policy_factor_aggregation",
        "training_scenario_composition", "replication_protocol",
        "early_stopping_policy", "checkpoint_selection_rule", "training_budget",
        "statistical_comparison_method", "tie_breaking_rule",
    )
    # Set choices to a list built from fixed.
    choices = list(fixed)
    # Extend choices with a lazy sequence of the result of _choice(item, the result of item.replace('_', '
    # ').title(), the text 'ARCHITECTURE',...) for item in architecture.
    choices.extend(_choice(item, item.replace("_", " ").title(), "ARCHITECTURE",
                           # Supply ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION to _choice.
                           ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                           "COMPATIBLE_ALTERNATIVES_REQUIRE_PROJECT_ABLATION")
                   # Evaluate architecture as part of the enclosing expression.
                   for item in architecture)
    # Extend choices with a lazy sequence of the result of _choice(item, the result of item.replace('_', '
    # ').title(), the text 'TRAINING_METHOD',...) for item in empirical.
    choices.extend(_choice(item, item.replace("_", " ").title(), "TRAINING_METHOD",
                           # Supply ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION to _choice.
                           ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                           "METHOD_SUPPORTED_NUMERICAL_OR_DESIGN_CHOICE_PROJECT_SPECIFIC")
                   # Evaluate empirical as part of the enclosing expression.
                   for item in empirical)
    # Extend choices with a tuple containing the result of _choice(the text 'gae_estimator', the text 'Generalized
    # advantage estimation', the text...
    choices.extend((
        # Include the result of _choice(the text 'gae_estimator', the text 'Generalized advantage estimation', the
        # text 'ESTIMATOR',...) in this tuple.
        _choice("gae_estimator", "Generalized advantage estimation", "ESTIMATOR",
                # Supply ChoiceClassification.OPTIONAL_FUTURE_ABLATION to _choice.
                ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                "BASELINE_USES_EXACT_MONTE_CARLO_ADVANTAGE"),
        # Include the result of _choice(the text 'gae_lambda', the text 'GAE lambda', the text 'ESTIMATOR',...) in
        # this tuple.
        _choice("gae_lambda", "GAE lambda", "ESTIMATOR",
                # Supply ChoiceClassification.OPTIONAL_FUTURE_ABLATION to _choice.
                ChoiceClassification.OPTIONAL_FUTURE_ABLATION,
                # Supply a tuple containing the text 'gae_estimator' to _choice.
                "ONLY_APPLICABLE_IF_GAE_ABLATION_ENABLED", ("gae_estimator",)),
    ))
    # Return the result of ExperimentalChoiceRegistry(choices) to the caller.
    return ExperimentalChoiceRegistry(choices)


# Set HARD_VALIDITY_GATES to a tuple containing the text 'HARD_ACTION_MASK_INVARIANT', the text
# 'REGULATORY_INVARIANT', the text 'PROTOCOL_INVARIANT', the...
HARD_VALIDITY_GATES = (
    "HARD_ACTION_MASK_INVARIANT", "REGULATORY_INVARIANT",
    "PROTOCOL_INVARIANT", "ROUTE_TRUTH_LEAKAGE_ABSENT",
    "FINITE_NETWORK_OUTPUTS", "VALID_ACTION_PROBABILITIES",
    "FINITE_TRAINING_QUANTITIES", "CAUSAL_TRANSITION_INTEGRITY",
    "OBJECTIVE_ACCOUNTING_NO_DOUBLE_COUNT",
)


# Build metric manifest using the inputs and processing steps below.
# Output: the result of ExperimentMetricManifest(a tuple containing the text 'STEP_5J_1_METRICS', the text
# 'TOTAL_TEAM_TRAVEL_TIME_SECONDS',...).
def build_metric_manifest():
    # Return the result of ExperimentMetricManifest(a tuple containing the text 'STEP_5J_1_METRICS', the text
    # 'TOTAL_TEAM_TRAVEL_TIME_SECONDS',...) to the caller.
    return ExperimentMetricManifest(
        # Supply a tuple containing the text 'STEP_5J_1_METRICS' to ExperimentMetricManifest.
        ("STEP_5J_1_METRICS",), "TOTAL_TEAM_TRAVEL_TIME_SECONDS",
        # Supply MetricDirection.LOWER_IS_BETTER to ExperimentMetricManifest.
        MetricDirection.LOWER_IS_BETTER, "RAW_SHARED_TEAM_REWARD",
        # Supply a tuple containing the text 'THROUGHPUT', the text 'MEAN_TRAVEL_TIME', the text
        # 'MAXIMUM_TRAVEL_TIME', the text... to ExperimentMetricManifest.
        ("THROUGHPUT", "MEAN_TRAVEL_TIME", "MAXIMUM_TRAVEL_TIME",
         "TRAVEL_TIME_VARIANCE", "COLLISION_COUNT", "MODEL_COMPLEXITY",
         # Supply HARD_VALIDITY_GATES to ExperimentMetricManifest.
         "TRAINING_STABILITY"), HARD_VALIDITY_GATES, False,
    )


# Create scenario manifest using the inputs and processing steps below.
# Input manifest_id: the supplied manifest id.
# Input purpose: the supplied purpose.
# Input scenario_ids: the supplied scenario ids.
# Input scenario_generation_source: the supplied scenario generation source.
# Input demand_schedule_identity: the supplied demand schedule identity.
# Input intersection_network_identity: the supplied intersection network identity.
# Input vehicle_type_identity: the supplied vehicle type identity.
# Input regulatory_profile: the supplied regulatory profile.
# Input perception_configuration_identity: the supplied perception configuration identity.
# Input intention_model_identity: the supplied intention model identity.
# Input randomization_provenance: the supplied randomization provenance.
# Input frozen_status: the supplied frozen status.
# Output: the result of ScenarioManifest(manifest_id, role, a tuple built from scenario_ids,
# scenario_generation_source,...).
def create_scenario_manifest(*, manifest_id, purpose, scenario_ids,
                             # Declare scenario_generation_source, demand_schedule_identity as input parameters.
                             scenario_generation_source, demand_schedule_identity,
                             # Declare intersection_network_identity, vehicle_type_identity as input parameters.
                             intersection_network_identity, vehicle_type_identity,
                             # Declare regulatory_profile, perception_configuration_identity as input parameters.
                             regulatory_profile, perception_configuration_identity,
                             # Declare intention_model_identity, randomization_provenance as input parameters.
                             intention_model_identity, randomization_provenance,
                             # Declare frozen_status as input parameter.
                             frozen_status):
    # Set role to purpose when whether purpose has type ScenarioRole, otherwise the result of
    # ScenarioRole(purpose).
    role = purpose if isinstance(purpose, ScenarioRole) else ScenarioRole(purpose)
    # Return the result of ScenarioManifest(manifest_id, role, a tuple built from scenario_ids,
    # scenario_generation_source,...) to the caller.
    return ScenarioManifest(
        # Supply scenario_generation_source to ScenarioManifest.
        manifest_id, role, tuple(scenario_ids), scenario_generation_source,
        # Supply intersection_network_identity to ScenarioManifest.
        demand_schedule_identity, intersection_network_identity,
        # Supply vehicle_type_identity to ScenarioManifest.
        vehicle_type_identity, regulatory_profile,
        # Supply perception_configuration_identity to ScenarioManifest.
        perception_configuration_identity, intention_model_identity,
        # Supply randomization_provenance to ScenarioManifest.
        randomization_provenance, frozen_status,
        # Supply role is the same object as ScenarioRole.VALIDATION to ScenarioManifest.
        role is ScenarioRole.VALIDATION,
    )


# Create configuration using the inputs and processing steps below.
# Input registry: the supplied registry.
# Input assignments: the supplied assignments.
# Input architecture_identity: the supplied architecture identity.
# Input training_method_identity: the supplied training method identity.
# Input regulatory_profile: the supplied regulatory profile.
# Input semantic_schema_versions: the supplied semantic schema versions.
# Input require_resolved: the supplied require resolved.
# Output: the result of ExperimentalConfiguration(identity, assignments, unresolved, fixed, architecture_identity,
# training_method_identity, the...).
# Processing: select branches using the stated conditions.
def create_configuration(registry, assignments, *, architecture_identity,
                         # Declare training_method_identity, regulatory_profile as input parameters.
                         training_method_identity, regulatory_profile,
                         # Declare semantic_schema_versions, require_resolved as input parameters.
                         semantic_schema_versions, require_resolved=False):
    # Set assignments to a dictionary built from assignments.
    assignments = dict(assignments)
    # Set unknown to a set built from assignments minus a set of item.choice_id for item in the result of
    # registry.all().
    unknown = set(assignments) - {item.choice_id for item in registry.all()}
    # Run this branch when unknown.
    if unknown:
        # Raise ExperimentalFrameworkError with the text 'UNREGISTERED_EXPERIMENTAL_CHOICE' to stop this execution
        # path.
        raise ExperimentalFrameworkError("UNREGISTERED_EXPERIMENTAL_CHOICE")
    # Set empirical to a tuple built from a lazy sequence of item.choice_id for item in the result of
    # registry.all(); retain entries satisfying item.classification belongs to a set containing...
    empirical = tuple(item.choice_id for item in registry.all()
                      # Evaluate item.classification belongs to a set containing
                      # ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,... as part of the enclosing
                      # expression.
                      if item.classification in {
                          # Include ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION in this set.
                          ChoiceClassification.REQUIRES_EXPERIMENTAL_SELECTION,
                          # Include ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION in this set.
                          ChoiceClassification.ARCHITECTURE_CHOICE_REQUIRES_ABLATION,
                      })
    # Set unresolved to a tuple built from the sorted values from a set built from empirical minus a set built
    # from assignments.
    unresolved = tuple(sorted(set(empirical) - set(assignments)))
    # Run this branch when require_resolved and unresolved.
    if require_resolved and unresolved:
        # Raise ExperimentalFrameworkError with the text 'EXPERIMENTAL_CHOICE_UNRESOLVED' to stop this execution
        # path.
        raise ExperimentalFrameworkError("EXPERIMENTAL_CHOICE_UNRESOLVED")
    # Set fixed to a tuple built from a lazy sequence of item.choice_id for item in the result of registry.all();
    # retain entries satisfying item.classification belongs to a set containing...
    fixed = tuple(item.choice_id for item in registry.all()
                  # Evaluate item.classification belongs to a set containing
                  # ChoiceClassification.MATHEMATICALLY_FIXED, ChoiceClassification.REGULATORY_FIXED,... as part
                  # of the enclosing expression.
                  if item.classification in {
                      # Include ChoiceClassification.MATHEMATICALLY_FIXED in this set.
                      ChoiceClassification.MATHEMATICALLY_FIXED,
                      # Include ChoiceClassification.REGULATORY_FIXED in this set.
                      ChoiceClassification.REGULATORY_FIXED,
                      # Include ChoiceClassification.SCHEMA_DERIVED in this set.
                      ChoiceClassification.SCHEMA_DERIVED,
                      # Include ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT in this set.
                      ChoiceClassification.PROJECT_SEMANTIC_REQUIREMENT,
                  })
    # Set identity to a tuple containing the text 'CONFIGURATION', a tuple built from the sorted values from
    # key/value pairs from assignments,...
    identity = ("CONFIGURATION", tuple(sorted(assignments.items(), key=lambda x: x[0])),
                # Include training_method_identity in this tuple.
                fixed, architecture_identity, training_method_identity,
                "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1",
                # Include regulatory_profile in this tuple.
                "EXACT_UNDISCOUNTED_TEAM_RETURN_V1", regulatory_profile,
                # Include a tuple built from semantic_schema_versions in this tuple.
                tuple(semantic_schema_versions))
    # Return the result of ExperimentalConfiguration(identity, assignments, unresolved, fixed,
    # architecture_identity, training_method_identity, the...) to the caller.
    return ExperimentalConfiguration(
        # Supply architecture_identity to ExperimentalConfiguration.
        identity, assignments, unresolved, fixed, architecture_identity,
        # Supply training_method_identity to ExperimentalConfiguration.
        training_method_identity, "NEGATIVE_TEAM_TRAVEL_TIME_INCREMENT_V1",
        # Supply regulatory_profile to ExperimentalConfiguration.
        "EXACT_UNDISCOUNTED_TEAM_RETURN_V1", regulatory_profile,
        # Store the text 'FORBIDDEN' under 'silent_defaults'.
        tuple(semantic_schema_versions), {"silent_defaults": "FORBIDDEN"},
    )


# Deterministic run id using the inputs and processing steps below.
# Input experiment_id: the supplied experiment id.
# Input configuration_id: the supplied configuration id.
# Input scenario_manifest_id: the supplied scenario manifest id.
# Input seed_identity: the supplied seed identity.
# Input run_role: the supplied run role.
# Output: a tuple containing the text 'RUN', experiment_id, configuration_id, scenario_manifest_id, seed_identity,
# role.
def deterministic_run_id(experiment_id, configuration_id, scenario_manifest_id,
                         # Declare seed_identity, run_role as input parameters.
                         seed_identity, run_role):
    # Set role to run_role.value when whether run_role has type ScenarioRole, otherwise
    # ScenarioRole(run_role).value.
    role = run_role.value if isinstance(run_role, ScenarioRole) else ScenarioRole(run_role).value
    # Return a tuple containing the text 'RUN', experiment_id, configuration_id, scenario_manifest_id,
    # seed_identity, role to the caller.
    return ("RUN", experiment_id, configuration_id, scenario_manifest_id,
            # Include seed_identity in this tuple.
            seed_identity, role)


# Create selection decision using the inputs and processing steps below.
# Input kwargs: the supplied kwargs.
# Output: decision.
# Processing: select branches using the stated conditions.
def create_selection_decision(**kwargs):
    # Set decision to the result of SelectionDecisionRecord().
    decision = SelectionDecisionRecord(**kwargs)
    # Run this branch when decision.held_out_test_used.
    if decision.held_out_test_used:
        # Raise ExperimentalFrameworkError with the text 'HELD_OUT_TEST_LEAKAGE_IN_SELECTION' to stop this
        # execution path.
        raise ExperimentalFrameworkError("HELD_OUT_TEST_LEAKAGE_IN_SELECTION")
    # Run this branch when decision.selected_configuration_id is a different object from None or
    # decision.selected_value is a different object from None.
    if decision.selected_configuration_id is not None or decision.selected_value is not None:
        # Raise ExperimentalFrameworkError with the text 'STEP_5J_1_SELECTION_NOT_PERMITTED' to stop this
        # execution path.
        raise ExperimentalFrameworkError("STEP_5J_1_SELECTION_NOT_PERMITTED")
    # Return decision to the caller.
    return decision


# Valid runs for comparison using the inputs and processing steps below.
# Input run_records: the supplied run records.
# Output: a tuple built from a lazy sequence of run for run in run_records; retain entries satisfying run.run_role
# is the same object as ScenarioRole.VALIDATION and whether every item is...
def valid_runs_for_comparison(run_records):
    # Return a tuple built from a lazy sequence of run for run in run_records; retain entries satisfying
    # run.run_role is the same object as ScenarioRole.VALIDATION and whether every item is... to the caller.
    return tuple(run for run in run_records
                 # Evaluate run.run_role is the same object as ScenarioRole.VALIDATION and whether every item is
                 # true in a lazy sequence of result.passed for result in run.validity_gate_results as part of the
                 # enclosing expression.
                 if run.run_role is ScenarioRole.VALIDATION and
                 # Evaluate whether every item is true in a lazy sequence of result.passed for result in
                 # run.validity_gate_results as part of the enclosing expression.
                 all(result.passed for result in run.validity_gate_results))


# Assess step 5j 2 readiness using the inputs and processing steps below.
# Output: the text 'READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS' when whether every item is true in required,
# otherwise the text 'EXPERIMENTAL_FRAMEWORK_INCOMPLETE'.
def assess_step_5j_2_readiness():
    # Set registry to the result of build_project_choice_registry().
    registry = build_project_choice_registry()
    # Set required to a tuple containing the result of registry.all(), a tuple built from ScenarioRole,
    # CandidateSetDefinition,...
    required = (registry.all(), tuple(ScenarioRole), CandidateSetDefinition,
                # Include build_metric_manifest().hard_validity_gates in this tuple.
                build_metric_manifest().hard_validity_gates, SeedManifest,
                # Include SelectionDecisionRecord in this tuple.
                ExperimentRunRecord, SelectionDecisionRecord, ExperimentManifest)
    # Return the text 'READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS' when whether every item is true in required,
    # otherwise the text 'EXPERIMENTAL_FRAMEWORK_INCOMPLETE' to the caller.
    return ("READY_TO_DEFINE_CONTROLLED_PILOT_EXPERIMENTS"
            # Evaluate whether every item is true in required as part of the enclosing expression.
            if all(required) else "EXPERIMENTAL_FRAMEWORK_INCOMPLETE")


# Assess final training readiness using the inputs and processing steps below.
# Output: a tuple containing False, blockers.
def assess_final_training_readiness():
    # Set blockers to a tuple containing the text 'ARCHITECTURE_CHOICES_UNRESOLVED', the text
    # 'OPTIMIZER_UNRESOLVED', the text...
    blockers = (
        "ARCHITECTURE_CHOICES_UNRESOLVED", "OPTIMIZER_UNRESOLVED",
        "LEARNING_RATE_UNRESOLVED", "PPO_CLIP_UNRESOLVED",
        "MULTI_FACTOR_AGGREGATION_UNRESOLVED", "TRAINING_BUDGET_UNRESOLVED",
        "REPLICATION_DESIGN_UNRESOLVED", "SCENARIO_MANIFESTS_UNRESOLVED",
        "SELECTION_RULE_UNRESOLVED", "SAFETY_SHIELD_NOT_IMPLEMENTED",
    )
    # Return a tuple containing False, blockers to the caller.
    return False, blockers

