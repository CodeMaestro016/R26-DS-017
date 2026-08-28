from dataclasses import FrozenInstanceError

import pytest

from experimentation import (CandidateEvidenceRecord, ScenarioRole,
    assess_negotiation_execution_layer_readiness,
    assess_step_5j_2_design_completion, assess_step_5j_3_training_readiness,
    build_design, deterministic_semantic_partition)


@pytest.fixture(scope="module")
def design():
    return build_design()


def test_real_catalogue_and_deterministic_identity(design):
    second = build_design()
    assert design["catalogue"].scenario_count == 108
    assert design["catalogue"].catalogue_id == second["catalogue"].catalogue_id
    assert design["catalogue"].catalogue_generation_provenance["source"] == (
        "REAL_SUMO_NEGOTIATION_INFRASTRUCTURE")


def test_semantic_signatures_exclude_outcomes(design):
    fields = set(design["signatures"][0].__dataclass_fields__)
    assert not fields & {"reward", "travel_time", "actor_logits", "critic_value"}
    assert {"movement_path_ids", "regulatory_scc_structure",
            "equivalence_group_id"} <= fields


def test_partition_is_deterministic_nonoverlapping_and_frozen(design):
    manifests = design["manifests"]
    sets = [set(manifests[role].scenario_ids) for role in ScenarioRole]
    assert all(not sets[a] & sets[b] for a in range(3) for b in range(a + 1, 3))
    assert sum(map(len, sets)) == 108
    assert all(manifests[role].frozen_status == "FROZEN_BEFORE_PILOT_EXECUTION"
               for role in ScenarioRole)
    assert deterministic_semantic_partition(design["signatures"]) == {
        role: manifests[role].scenario_ids for role in ScenarioRole}


def test_each_role_has_real_learnable_negotiation(design):
    by_id = {item.scenario_id: item for item in design["signatures"]}
    for role in ScenarioRole:
        role_items = [by_id[item] for item in design["manifests"][role].scenario_ids]
        assert any(item.multi_action_proposer_capable and
                   item.multi_action_responder_capable for item in role_items)


def test_held_out_isolation(design):
    assert not design["manifests"][ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection
    assert "HELD_OUT_EXCLUDED" in design["selection_rule"]


def test_candidate_provenance_and_no_selection(design):
    assert design["evidence"]
    assert all(item.candidate_only and not item.selected and
               item.primary_source_reference for item in design["evidence"])
    assert all(not item.project_selected for item in design["provisional"].assignments)
    with pytest.raises(ValueError, match="NUMERIC_CANDIDATE_WITHOUT_PROVENANCE"):
        CandidateEvidenceRecord(("bad",), "x", 1.0, "x", "", "", "", "",
                                True, False, {})


def test_aggregation_candidates_have_no_role_weights(design):
    values = {item.candidate_value for item in design["evidence"]
              if item.choice_id == "multi_policy_factor_aggregation"}
    assert values == {"PER_POLICY_FACTOR_EMPIRICAL_MEAN",
                      "PER_JOINT_BATCH_NESTED_MEAN"}
    assert not any("weight" in item.choice_id for item in design["evidence"])


def test_seed_and_budget_are_not_arbitrary(design):
    assert design["seed_manifest"].seed_values == ()
    assert design["seed_manifest"].provenance["outcome_inputs"] == "0"
    assert all(plan.replication_design_status ==
               "REQUIRES_PILOT_VARIANCE_ESTIMATE" for plan in design["plans"])
    assert all(plan.training_budget_status ==
               "REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT"
               for plan in design["plans"])


def test_design_freeze_and_readiness_boundary(design):
    assert design["freeze"].freeze_status == "FROZEN_BEFORE_PILOT_RESULTS"
    with pytest.raises(FrozenInstanceError):
        design["freeze"].freeze_status = "CHANGED"
    assert assess_step_5j_2_design_completion(design) == "CONTROLLED_PILOT_DESIGN_FROZEN"
    assert assess_step_5j_3_training_readiness(design) == (
        False, ("NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE",))
    assert assess_negotiation_execution_layer_readiness(design) == (
        "READY_TO_IMPLEMENT_NEGOTIATION_TRAFFIC_COUPLING")


def test_no_gamma_optimizer_or_execution_in_design(design):
    assert not any(item.choice_id == "gamma" for item in design["evidence"])
    assert all(plan.execution_status == "NOT_EXECUTED_STEP_5J_2"
               for plan in design["plans"])
