"""Scientific-boundary tests for the bounded final MAPPO selection study."""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experimentation import ScenarioRole, build_design
from negotiation_training.architecture_contract import (
    build_mechanical_pilot_architecture_contract,
)
from negotiation_training.final_selection import (
    CANDIDATE_EPOCHS, PROTOCOL_ID, REPLICATION_COUNT, UPDATE_HORIZON,
    DeterministicNoNegotiationRegulatoryBaseline,
    _baseline_summary, _eligible, _episode_record,
    _hard_safety_failure_record, _summary, baseline, report,
    build_protocol, candidate_configurations, candidate_runtime_audit,
    file_sha256, heldout, prepare, select, smoke,
)
from negotiation_training.environment import CoupledNegotiationTrainingEnvironment
from negotiation_execution.replay import PhysicalReplayError
from negotiation_training.optimizer_contract import (
    build_mechanical_pilot_configuration_audit,
)


def test_candidate_set_and_bounded_resource_protocol_are_exact():
    protocol = build_protocol()
    assert CANDIDATE_EPOCHS == {"E5": 5, "E10": 10, "E15": 15}
    assert protocol["candidate_ids"] == ["E5", "E10", "E15"]
    assert REPLICATION_COUNT == protocol["replication_count_n"] == 3
    assert UPDATE_HORIZON == protocol["update_horizon_h"] == 2
    assert protocol["adaptive_early_stopping"] is False
    assert protocol["adaptive_horizon_extension"] is False
    assert protocol["bad_seed_replacement"] is False
    assert protocol["globally_optimal_claim"] is False


def test_only_ppo_epochs_differ_and_reference_values_remain_fixed():
    candidates = candidate_configurations()
    differing = {key for key in candidates[0].__dict__
                 if len({getattr(x, key) for x in candidates}) > 1}
    assert differing == {"candidate_id", "ppo_update_epochs"}
    for candidate in candidates:
        assert candidate.learning_rate == 0.0005
        assert candidate.ppo_clip_epsilon == 0.2
        assert candidate.gnn_hidden_dimension == 64
        assert candidate.gnn_training_mode == "FROZEN_GNN"


def test_historical_contracts_are_unchanged_by_candidate_audit():
    architecture_before = build_mechanical_pilot_architecture_contract()
    historical_before = build_mechanical_pilot_configuration_audit()
    candidate = candidate_configurations()[2]
    audit = candidate_runtime_audit(candidate)
    historical_after = build_mechanical_pilot_configuration_audit()
    architecture_after = build_mechanical_pilot_architecture_contract()
    assert historical_before == historical_after
    assert architecture_before == architecture_after
    historical_epochs = next(x.value for x in historical_after.runtime_choices
                             if x.choice_id == "ppo_update_epochs")
    candidate_epochs = next(x.value for x in audit.runtime_choices
                            if x.choice_id == "ppo_update_epochs")
    assert historical_epochs == 5
    assert candidate_epochs == 15


def test_all_candidates_share_manifests_and_replication_identities():
    protocol = build_protocol()
    assert all(protocol["manifests"][role]["scenario_count"] == 36
               for role in ("TRAINING", "VALIDATION", "HELD_OUT_TEST"))
    design = build_design()
    sets = [set(design["manifests"][role].scenario_ids)
            for role in ScenarioRole]
    assert not any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3))
    assert protocol["replication_identities"] == [
        ["FINAL_MAPPO_CANONICAL_REPLICATION_V2", i] for i in range(3)]


def test_prepare_and_smoke_do_not_consume_held_out_or_create_selection(tmp_path):
    protocol = prepare(tmp_path)
    result = smoke(tmp_path)
    assert protocol["held_out_used_for_selection"] is False
    assert result["status"] == "SMOKE_TEST_ONLY"
    assert result["held_out_scenarios_consumed"] == 0
    assert not (tmp_path / "selected_configuration.json").exists()
    assert not (tmp_path / "selected_policy.pt").exists()


def _validation_payload(means, eligible):
    candidates = {}
    for key in CANDIDATE_EPOCHS:
        candidates[key] = {"candidate_id": key, "eligible": eligible[key],
            "hard_gate_result": "ELIGIBLE" if eligible[key] else "INELIGIBLE",
            "summary": {"mean": means[key]}}
    return {"protocol_id": PROTOCOL_ID, "data_role": "VALIDATION",
            "held_out_consumed": False, "candidates": candidates}


def _selection_fixture(root, means, eligible):
    (root / "comparison").mkdir(parents=True)
    (root / "comparison" / "candidate_validation_summary.json").write_text(
        json.dumps(_validation_payload(means, eligible)), encoding="utf-8")
    for candidate in CANDIDATE_EPOCHS:
        directory = root / "training" / candidate
        directory.mkdir(parents=True)
        for index in range(3):
            (directory / f"replication_{index}_state_2.pt").write_bytes(
                f"{candidate}-{index}".encode())


def test_selection_applies_hard_gates_before_lower_validation_ttt(tmp_path):
    _selection_fixture(tmp_path, {"E5": 100, "E10": 1, "E15": 90},
                       {"E5": True, "E10": False, "E15": True})
    result = select(tmp_path)
    assert result["selected_candidate_id"] == "E15"
    assert result["selection_data_role"] == "VALIDATION"
    assert result["held_out_used_for_selection"] is False


def test_exact_tie_retains_e5_and_selected_policy_is_byte_identical(tmp_path):
    _selection_fixture(tmp_path, {"E5": 10, "E10": 10, "E15": 20},
                       {key: True for key in CANDIDATE_EPOCHS})
    result = select(tmp_path)
    assert result["selected_candidate_id"] == "E5"
    source = tmp_path / "training" / "E5" / "replication_0_state_2.pt"
    assert file_sha256(tmp_path / "selected_policy.pt") == file_sha256(source)
    assert result["demo_replication_selected_by_performance"] is False


def test_held_out_refuses_before_frozen_selection(tmp_path):
    with pytest.raises(RuntimeError, match="HELD_OUT_LOCKED"):
        heldout(tmp_path)


def test_baseline_is_nonlearned_nonreward_and_has_no_id_priority():
    baseline = DeterministicNoNegotiationRegulatoryBaseline()
    assert baseline.neural_actor_calls == 0
    assert baseline.reward_used_for_selection is False
    assert baseline.future_outcome_used_for_selection is False
    assert baseline.vehicle_id_priority_rule is False
    source = inspect.getsource(baseline.select_joint_actions)
    assert "KEEP_CLAIM" in source
    assert "REJECT_RELINQUISHMENT" in source
    assert "min(" not in source and "sorted(" not in source


def test_baseline_keeps_only_unique_executable_no_negotiation_branch():
    keep = SimpleNamespace(
        proposer_assignment=SimpleNamespace(
            claim_action_assignments=(("claim", "KEEP_CLAIM"),)),
        responder_assignment=SimpleNamespace(response_action_assignments=()),
        graph_executable=True)
    relinquish = SimpleNamespace(
        proposer_assignment=SimpleNamespace(
            claim_action_assignments=(("claim", "RELINQUISH_CLAIM"),)),
        responder_assignment=SimpleNamespace(response_action_assignments=()),
        graph_executable=True)
    baseline = DeterministicNoNegotiationRegulatoryBaseline()
    assert baseline.select_joint_actions((relinquish, keep), ()) is keep
    assert baseline.select_joint_actions((relinquish,), ()) is None


def test_only_opted_in_baseline_can_finish_an_observed_unresolved_context():
    baseline_environment = CoupledNegotiationTrainingEnvironment(
        DeterministicNoNegotiationRegulatoryBaseline())
    assert baseline_environment._terminal_coordination_status(
        None, True, "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH") == (
            "UNRESOLVED_COORDINATION_BASELINE")

    ordinary_provider = SimpleNamespace(selection_rule="STRICT_PROVIDER")
    ordinary_environment = CoupledNegotiationTrainingEnvironment(
        ordinary_provider)
    with pytest.raises(PhysicalReplayError, match=
                       "SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED"):
        ordinary_environment._terminal_coordination_status(
            None, True, "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
    with pytest.raises(PhysicalReplayError, match=
                       "SEMANTIC_NEGOTIATION_EVENT_NOT_OBSERVED"):
        baseline_environment._terminal_coordination_status(None, False, None)


def test_unresolved_episode_record_is_explicit_even_when_all_vehicles_complete():
    episode = SimpleNamespace(
        scenario_id=("HELD_OUT", 1), team_travel_time_seconds=42.0,
        scheduled_vehicle_count=2, completed_vehicle_count=2,
        episode_completion_status="UNRESOLVED_COORDINATION_BASELINE",
        simulation_duration_seconds=10.0, collision_count=0,
        blocked_zone_entry_violation_count=0,
        native_sumo_safety_intervention_count=1, joint_decision_batches=(),
        proposer_factor_count=0, responder_factor_count=0,
        hard_validity_gate_results={"collision_free": True,
                                    "blocked_zone_invariant": True},
        provenance={
            "unresolved_coordination_reason":
                "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH",
            "neural_actor_calls": 0, "fabricated_negotiation_branches": 0,
            "vehicle_id_priority_decisions": 0},
        sumo_step_count=100, wall_clock_runtime_seconds=2.0)
    record = _episode_record(episode, "BASELINE")
    assert record["unresolved_coordination_case"] is True
    assert record["unresolved_coordination_reason"] == (
        "NO_EXECUTABLE_KEEP_REGULATORY_BRANCH")
    assert record["learned_proposer_actions"] == 0
    assert record["learned_responder_actions"] == 0
    assert record["neural_actor_calls"] == 0
    assert record["fabricated_negotiation_branches"] == 0
    assert record["vehicle_id_priority_decisions"] == 0
    assert _summary([record])["unresolved_coordination_cases"] == 1


def test_unresolved_status_does_not_relax_collision_or_blocked_zone_gates():
    base = {"collisions": 0, "blocked_zone_violations": 0,
            "hard_mask_violations": 0, "regulatory_invariant_violations": 0,
            "protocol_invariant_failures": 0,
            "route_truth_actor_fields_consumed": 0,
            "hard_validity_gate_results": {"collision_free": True,
                                            "blocked_zone_invariant": True},
            "total_team_travel_time_seconds": 1.0}
    assert not _eligible([{**base, "collisions": 1}])
    assert not _eligible([{**base, "blocked_zone_violations": 1}])
    source = inspect.getsource(CoupledNegotiationTrainingEnvironment.run_episode)
    assert "PHYSICAL_CAUSAL_BRANCH_COLLISION_OBSERVED" in source


def test_blocked_zone_exception_becomes_factual_failed_baseline_record_only():
    error = PhysicalReplayError(
        "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
        ("SCENARIO_AV_2", "CZ_7", 23.32))
    record = _hard_safety_failure_record(("HELD_OUT", 4), error)
    assert record["status"] == "HARD_SAFETY_FAILURE"
    assert record["hard_validity_eligible"] is False
    assert record["safety_failure_type"] == (
        "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE")
    assert record["total_team_travel_time_seconds"] is None
    assert record["safety_failure_provenance"] == {
        "exception_type": "PhysicalReplayError",
        "failure_message": "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
        "raw_evidence": ["SCENARIO_AV_2", "CZ_7", 23.32],
        "vehicle_id": "SCENARIO_AV_2", "conflict_zone_id": "CZ_7",
        "simulation_time": 23.32}


def _successful_baseline_episode(scenario_id):
    return SimpleNamespace(
        scenario_id=scenario_id, team_travel_time_seconds=20.0,
        scheduled_vehicle_count=2, completed_vehicle_count=2,
        episode_completion_status="COMPLETE",
        simulation_duration_seconds=10.0, collision_count=0,
        blocked_zone_entry_violation_count=0,
        native_sumo_safety_intervention_count=2, joint_decision_batches=(),
        proposer_factor_count=0, responder_factor_count=0,
        hard_validity_gate_results={"collision_free": True,
                                    "blocked_zone_invariant": True},
        provenance={"unresolved_coordination_reason": None,
                    "neural_actor_calls": 0,
                    "fabricated_negotiation_branches": 0,
                    "vehicle_id_priority_decisions": 0},
        sumo_step_count=100, wall_clock_runtime_seconds=1.0)


def test_baseline_records_failure_continues_and_atomically_accounts_for_36(
        tmp_path, monkeypatch):
    import negotiation_training.final_selection as module
    (tmp_path / "selected_configuration.json").write_text("{}")
    calls = []

    class FakeEnvironment:
        def __init__(self, provider):
            assert provider.allows_unresolved_coordination

        def run_episode(self, specification, manifest_id):
            del manifest_id
            calls.append(specification)
            if len(calls) == 1:
                raise PhysicalReplayError(
                    "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE",
                    ("SCENARIO_AV_0", "CZ", 5.0))
            return _successful_baseline_episode(specification)

    monkeypatch.setattr(module, "CoupledNegotiationTrainingEnvironment",
                        FakeEnvironment)
    monkeypatch.setattr(module, "_specification", lambda payload, sid: sid)
    result = baseline(tmp_path)
    assert len(calls) == len(result["scenario_results"]) == 36
    assert result["scenario_results"][0]["status"] == "HARD_SAFETY_FAILURE"
    assert result["scenario_results"][0][
        "total_team_travel_time_seconds"] is None
    assert result["summary"]["scenario_count"] == 36
    assert result["summary"]["completed_episode_count"] == 35
    assert result["summary"]["hard_safety_failure_count"] == 1
    assert result["summary"]["blocked_zone_failure_count"] == 1
    assert result["summary"]["safety_eligible"] is False
    assert result["summary"]["native_sumo_safety_interventions"] == 70
    assert len(list((tmp_path / "held_out" /
                     "baseline_scenario_records").glob("*.json"))) == 36


def test_report_prioritizes_safety_and_uses_only_completed_matched_subset(
        tmp_path):
    (tmp_path / "comparison").mkdir()
    (tmp_path / "held_out").mkdir()
    validation = _validation_payload(
        {"E5": 1, "E10": 2, "E15": 3},
        {key: True for key in CANDIDATE_EPOCHS})
    (tmp_path / "comparison" / "candidate_validation_summary.json").write_text(
        json.dumps(validation))
    (tmp_path / "selected_configuration.json").write_text(json.dumps({
        "selected_candidate_id": "E5"}))
    learned = {"scenario_id": ["S", 1],
               "total_team_travel_time_seconds": 10.0,
               "completed_vehicles": 2, "collisions": 0,
               "blocked_zone_violations": 0,
               "native_sumo_safety_interventions": 0}
    (tmp_path / "held_out" / "selected_mappo_results.json").write_text(
        json.dumps({"replications": [{"scenario_results": [learned]}]}))
    failed = _hard_safety_failure_record(
        ("S", 1), PhysicalReplayError(
            "BLOCKED_VEHICLE_ENTERED_CONFLICT_ZONE", ("V", "Z", 1.0)))
    (tmp_path / "held_out" / "baseline_results.json").write_text(json.dumps({
        "scenario_results": [failed],
        "summary": _baseline_summary([failed])}))
    report(tmp_path)
    comparison = json.loads((tmp_path / "comparison" /
        "held_out_mappo_vs_baseline.json").read_text())
    assert comparison["baseline_safety_eligible"] is False
    assert comparison["overall_mean_difference"] is None
    assert comparison["matched_completed_scenario_count"] == 0
    assert comparison["efficiency_comparison_scope"] == (
        "DESCRIPTIVE_MATCHED_COMPLETED_SCENARIO_SUBSET_ONLY")
    conclusion = comparison["truthful_conclusion"]
    assert "failed the predefined hard safety-validity gate" in conclusion
    assert "reduced total team travel time" not in conclusion


def test_runner_source_does_not_promote_historical_demo_checkpoint():
    import negotiation_training.final_selection as module
    source = inspect.getsource(module)
    assert "replication_0_state_2.pt" in source
    assert "mappo_extended_resume" not in source
    assert "mappo_demo_policy.pt" not in source
    assert "ground_truth_route_id" not in source
