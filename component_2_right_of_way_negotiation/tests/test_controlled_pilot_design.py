# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest

# Import CandidateEvidenceRecord, ScenarioRole, assess_negotiation_execution_layer_readiness,
# assess_step_5j_2_design_completion, assess_step_5j_3_training_readiness,... from experimentation for the
# operations below.
from experimentation import (CandidateEvidenceRecord, ScenarioRole,
    assess_negotiation_execution_layer_readiness,
    assess_step_5j_2_design_completion, assess_step_5j_3_training_readiness,
    build_design, deterministic_semantic_partition)


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Design using the inputs and processing steps below.
# Output: the result of build_design().
def design():
    # Return the result of build_design() to the caller.
    return build_design()


# Check real catalogue and deterministic identity using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_real_catalogue_and_deterministic_identity(design):
    # Set second to the result of build_design().
    second = build_design()
    # Require design['catalogue'].scenario_count equals 108; otherwise raise AssertionError.
    assert design["catalogue"].scenario_count == 108
    # Require design['catalogue'].catalogue_id equals second['catalogue'].catalogue_id; otherwise raise
    # AssertionError.
    assert design["catalogue"].catalogue_id == second["catalogue"].catalogue_id
    # Require design['catalogue'].catalogue_generation_provenance at 'source' equals the text
    # 'REAL_SUMO_NEGOTIATION_INFRASTRUCTURE'; otherwise raise AssertionError.
    assert design["catalogue"].catalogue_generation_provenance["source"] == (
        "REAL_SUMO_NEGOTIATION_INFRASTRUCTURE")


# Check semantic signatures exclude outcomes using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_semantic_signatures_exclude_outcomes(design):
    # Set fields to a set built from design['signatures'][0].__dataclass_fields__.
    fields = set(design["signatures"][0].__dataclass_fields__)
    # Require the negation of fields intersected with a set containing the text 'reward', the text 'travel_time',
    # the text 'actor_logits', the text 'critic_value'; otherwise raise AssertionError.
    assert not fields & {"reward", "travel_time", "actor_logits", "critic_value"}
    # Require a set containing the text 'movement_path_ids', the text 'regulatory_scc_structure', the text
    # 'equivalence_group_id' is at most fields; otherwise raise AssertionError.
    assert {"movement_path_ids", "regulatory_scc_structure",
            # Evaluate fields as part of the enclosing expression.
            "equivalence_group_id"} <= fields


# Check partition is deterministic nonoverlapping and frozen using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_partition_is_deterministic_nonoverlapping_and_frozen(design):
    # Set manifests to design at 'manifests'.
    manifests = design["manifests"]
    # Set sets to a list of a set built from manifests[role].scenario_ids for role in ScenarioRole.
    sets = [set(manifests[role].scenario_ids) for role in ScenarioRole]
    # Require whether every item is true in a lazy sequence of the negation of sets[a] intersected with sets[b]
    # for a in the integer range defined by 3; otherwise raise AssertionError.
    assert all(not sets[a] & sets[b] for a in range(3) for b in range(a + 1, 3))
    # Require the sum of the result of map(len, sets) equals 108; otherwise raise AssertionError.
    assert sum(map(len, sets)) == 108
    # Require whether every item is true in a lazy sequence of manifests[role].frozen_status equals the text
    # 'FROZEN_BEFORE_PILOT_EXECUTION' for role in ScenarioRole; otherwise raise AssertionError.
    assert all(manifests[role].frozen_status == "FROZEN_BEFORE_PILOT_EXECUTION"
               # Evaluate ScenarioRole as part of the enclosing expression.
               for role in ScenarioRole)
    # Require the result of deterministic_semantic_partition(design at 'signatures') equals a dictionary of role
    # mapped to manifests[role].scenario_ids for role in ScenarioRole; otherwise raise AssertionError.
    assert deterministic_semantic_partition(design["signatures"]) == {
        # Evaluate manifests[role].scenario_ids as part of the enclosing expression.
        role: manifests[role].scenario_ids for role in ScenarioRole}


# Check each role has real learnable negotiation using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_each_role_has_real_learnable_negotiation(design):
    # Set by_id to a dictionary of item.scenario_id mapped to item for item in design at 'signatures'.
    by_id = {item.scenario_id: item for item in design["signatures"]}
    # Iterate over ScenarioRole, binding each item to role.
    for role in ScenarioRole:
        # Set role_items to a list of by_id at item for item in design['manifests'][role].scenario_ids.
        role_items = [by_id[item] for item in design["manifests"][role].scenario_ids]
        # Require whether any item is true in a lazy sequence of item.multi_action_proposer_capable and
        # item.multi_action_responder_capable for item in role_items; otherwise raise AssertionError.
        assert any(item.multi_action_proposer_capable and
                   # Evaluate item.multi_action_responder_capable as part of the enclosing expression.
                   item.multi_action_responder_capable for item in role_items)


# Check held out isolation using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_held_out_isolation(design):
    # Require the negation of design['manifests'][ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection;
    # otherwise raise AssertionError.
    assert not design["manifests"][ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection
    # Require the text 'HELD_OUT_EXCLUDED' belongs to design at 'selection_rule'; otherwise raise AssertionError.
    assert "HELD_OUT_EXCLUDED" in design["selection_rule"]


# Check candidate provenance and no selection using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_candidate_provenance_and_no_selection(design):
    # Require design at 'evidence'; otherwise raise AssertionError.
    assert design["evidence"]
    # Require whether every item is true in a lazy sequence of item.candidate_only and the negation of
    # item.selected and item.primary_source_reference for item in design at 'evidence'; otherwise raise
    # AssertionError.
    assert all(item.candidate_only and not item.selected and
               # Evaluate item.primary_source_reference as part of the enclosing expression.
               item.primary_source_reference for item in design["evidence"])
    # Require whether every item is true in a lazy sequence of the negation of item.project_selected for item in
    # design['provisional'].assignments; otherwise raise AssertionError.
    assert all(not item.project_selected for item in design["provisional"].assignments)
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="NUMERIC_CANDIDATE_WITHOUT_PROVENANCE"):
        # Call CandidateEvidenceRecord with the supplied arguments.
        CandidateEvidenceRecord(("bad",), "x", 1.0, "x", "", "", "", "",
                                # Supply an empty dictionary to CandidateEvidenceRecord.
                                True, False, {})


# Check aggregation candidates have no role weights using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_aggregation_candidates_have_no_role_weights(design):
    # Set values to a set of item.candidate_value for item in design at 'evidence'; retain entries satisfying
    # item.choice_id equals the text 'multi_policy_factor_aggregation'.
    values = {item.candidate_value for item in design["evidence"]
              # Evaluate item.choice_id equals the text 'multi_policy_factor_aggregation' as part of the enclosing
              # expression.
              if item.choice_id == "multi_policy_factor_aggregation"}
    # Require values equals a set containing the text 'PER_POLICY_FACTOR_EMPIRICAL_MEAN', the text
    # 'PER_JOINT_BATCH_NESTED_MEAN'; otherwise raise AssertionError.
    assert values == {"PER_POLICY_FACTOR_EMPIRICAL_MEAN",
                      "PER_JOINT_BATCH_NESTED_MEAN"}
    # Require the negation of whether any item is true in a lazy sequence of 'weight' belongs to item.choice_id
    # for item in design at 'evidence'; otherwise raise AssertionError.
    assert not any("weight" in item.choice_id for item in design["evidence"])


# Check seed and budget are not arbitrary using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_seed_and_budget_are_not_arbitrary(design):
    # Require design['seed_manifest'].seed_values equals an empty tuple; otherwise raise AssertionError.
    assert design["seed_manifest"].seed_values == ()
    # Require design['seed_manifest'].provenance at 'outcome_inputs' equals the text '0'; otherwise raise
    # AssertionError.
    assert design["seed_manifest"].provenance["outcome_inputs"] == "0"
    # Require whether every item is true in a lazy sequence of plan.replication_design_status equals the text
    # 'REQUIRES_PILOT_VARIANCE_ESTIMATE' for plan in design at 'plans'; otherwise raise AssertionError.
    assert all(plan.replication_design_status ==
               # Evaluate design at 'plans' as part of the enclosing expression.
               "REQUIRES_PILOT_VARIANCE_ESTIMATE" for plan in design["plans"])
    # Require whether every item is true in a lazy sequence of plan.training_budget_status equals the text
    # 'REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT' for plan in design at 'plans'; otherwise raise
    # AssertionError.
    assert all(plan.training_budget_status ==
               "REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT"
               # Evaluate design at 'plans' as part of the enclosing expression.
               for plan in design["plans"])


# Check design freeze and readiness boundary using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_design_freeze_and_readiness_boundary(design):
    # Require design['freeze'].freeze_status equals the text 'FROZEN_BEFORE_PILOT_RESULTS'; otherwise raise
    # AssertionError.
    assert design["freeze"].freeze_status == "FROZEN_BEFORE_PILOT_RESULTS"
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set design['freeze'].freeze_status to the text 'CHANGED'.
        design["freeze"].freeze_status = "CHANGED"
    # Require the result of assess_step_5j_2_design_completion(design) equals the text
    # 'CONTROLLED_PILOT_DESIGN_FROZEN'; otherwise raise AssertionError.
    assert assess_step_5j_2_design_completion(design) == "CONTROLLED_PILOT_DESIGN_FROZEN"
    # Require the result of assess_step_5j_3_training_readiness(design) equals a tuple containing False, a tuple
    # containing the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE'; otherwise raise
    # AssertionError.
    assert assess_step_5j_3_training_readiness(design) == (
        # Include a tuple containing the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE' in this
        # tuple.
        False, ("NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE",))
    # Require the result of assess_negotiation_execution_layer_readiness(design) equals the text
    # 'READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING'; otherwise raise AssertionError.
    assert assess_negotiation_execution_layer_readiness(design) == (
        "READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING")


# Check no gamma optimizer or execution in design using the setup, calls, and assertions below.
# Input design: the supplied design.
# Output: no explicit value; normal completion returns None.
def test_no_gamma_optimizer_or_execution_in_design(design):
    # Require the negation of whether any item is true in a lazy sequence of item.choice_id equals 'gamma' for
    # item in design at 'evidence'; otherwise raise AssertionError.
    assert not any(item.choice_id == "gamma" for item in design["evidence"])
    # Require whether every item is true in a lazy sequence of plan.execution_status equals the text
    # 'NOT_EXECUTED_STEP_5J_2' for plan in design at 'plans'; otherwise raise AssertionError.
    assert all(plan.execution_status == "NOT_EXECUTED_STEP_5J_2"
               # Evaluate design at 'plans' as part of the enclosing expression.
               for plan in design["plans"])
