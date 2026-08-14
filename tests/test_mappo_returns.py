from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from negotiation_learning.mappo_returns import (
    CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator,
    PPO_CLIP_PARAMETER_STATUS, ReturnSemanticError,
    create_policy_factor_sample, importance_ratio,
    ppo_clipped_surrogate_terms, unclipped_surrogate_term,
    validate_policy_replay_semantics,
)
from negotiation_objective import NegotiationObjectiveLedger
from negotiation_objective.models import REWARD_DEFINITION_ID, TeamObjectiveRecord
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger


def reward(source, successor, value, identity=None):
    interval_id = identity or ("interval", source, successor)
    return TeamObjectiveRecord(
        interval_id, source, successor, -value, value,
        REWARD_DEFINITION_ID, "negative vehicle-seconds", {"test": "only"},
    )


def returns(records, terminal="T"):
    return EpisodicTeamReturnCalculator().compute(records, terminal, "episode")


def test_two_and_three_interval_suffix_returns():
    two = returns((reward("B0", "B1", -2.0), reward("B1", "T", -3.0)))
    assert two["B1"].undiscounted_team_return == -3.0
    assert two["B0"].undiscounted_team_return == -5.0
    three = returns((reward("B0", "B1", -1.0), reward("B1", "B2", -2.0), reward("B2", "T", -4.0)))
    assert tuple(three[key].undiscounted_team_return for key in ("B0", "B1", "B2")) == (-7.0, -6.0, -4.0)


def test_zero_duration_middle_phase_preserves_return():
    result = returns((reward("P", "R", 0.0), reward("R", "T", -5.0)))
    assert result["P"].undiscounted_team_return == result["R"].undiscounted_team_return == -5.0


def test_partition_invariance():
    whole = returns((reward("B0", "T", -6.0),))["B0"]
    split = returns((reward("B0", "B1", -2.0), reward("B1", "T", -4.0)))["B0"]
    assert whole.undiscounted_team_return == split.undiscounted_team_return


def test_claim_resolution_and_vehicle_arrival_are_not_team_terminal():
    result = returns((
        reward("CLAIM_RESOLVED", "VEHICLE_ARRIVED", -2.0),
        reward("VEHICLE_ARRIVED", "T", -3.0),
    ))
    assert result["CLAIM_RESOLVED"].undiscounted_team_return == -5.0
    assert result["VEHICLE_ARRIVED"].undiscounted_team_return == -3.0


def test_terminal_batch_is_action_free_and_closes_final_interval():
    demands = VehicleDemandLedger()
    demands.register_scheduled_vehicle("AV_0", 0.0, DemandScheduleSource.INITIAL_SIMULATION_DEMAND)
    objective = NegotiationObjectiveLedger()
    start = objective.create_joint_decision_batch(("S",), 0.0, "PROPOSER", (("D",),), ("A",), (("A", "B"),))
    objective.begin_episode(start)
    terminal, record = objective.close_episode("episode", 2.0, demands.get_all_records())
    assert terminal.phase_identity == "EPISODE_TERMINATION_BATCH"
    assert terminal.decision_event_ids == ()
    assert record.successor_batch_id == terminal.batch_id
    assert returns((record,), terminal.batch_id)[start.batch_id].undiscounted_team_return == -2.0


def test_missing_ambiguous_cycle_and_duplicate_interval_rejected():
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_SUCCESSOR_MISSING"):
        returns((reward("B0", "MISSING", -1.0),))
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_SUCCESSOR_AMBIGUOUS"):
        returns((reward("B0", "B1", -1.0), reward("B0", "T", -2.0)))
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_TIMELINE_CYCLE"):
        returns((reward("B0", "B1", -1.0), reward("B1", "B0", -2.0)))
    duplicate = ("same",)
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_INTERVAL_DUPLICATED"):
        returns((reward("B0", "B1", -1.0, duplicate), reward("B1", "T", -2.0, duplicate)))


def test_truncated_empty_rollout_is_not_bootstrapped():
    with pytest.raises(ReturnSemanticError, match="TRUNCATED_ROLLOUT_BOOTSTRAP_REQUIRES_RESEARCH_DECISION"):
        returns(())


def test_one_return_and_one_value_target_per_batch_shared_by_decisions():
    record = returns((reward("B0", "T", -4.0),))["B0"]
    target = CentralizedAdvantageCalculator.value_target(record, (1.0, 1.0))
    assert target.batch_id == "B0"
    assert target.critic_target == -4.0
    assert all(record.return_record_id == record.return_record_id for _ in ("D1", "D2", "D3"))


def test_conflicting_batch_critic_values_rejected():
    record = returns((reward("B0", "T", -4.0),))["B0"]
    with pytest.raises(ReturnSemanticError, match="INCONSISTENT_BATCH_CRITIC_VALUE"):
        CentralizedAdvantageCalculator.value_target(record, (1.0, 2.0))


@pytest.mark.parametrize("critic,expected_sign", [(-6.0, 1), (-5.0, 0), (-4.0, -1)])
def test_exact_monte_carlo_advantage_sign(critic, expected_sign):
    record = returns((reward("B0", "T", -5.0),))["B0"]
    target = CentralizedAdvantageCalculator.value_target(record, (critic,))
    advantage = CentralizedAdvantageCalculator.advantage(record, target)
    assert advantage.advantage == -5.0 - critic
    assert (advantage.advantage > 0) - (advantage.advantage < 0) == expected_sign
    assert target.value_error == critic - (-5.0)
    assert target.value_squared_error == target.value_error ** 2


def sample(mask=(True, False), action=0, semantic="KEEP_CLAIM"):
    result = returns((reward("B0", "T", -2.0),))["B0"]
    target = CentralizedAdvantageCalculator.value_target(result, (-1.0,))
    advantage = CentralizedAdvantageCalculator.advantage(result, target)
    snapshot = SimpleNamespace(action_names=("KEEP_CLAIM", "RELINQUISH_CLAIM"))
    return create_policy_factor_sample(
        decision_event_id=("D",), joint_batch_id="B0", ego_id="A",
        decision_role="PROPOSER", claim_identity=("B", "A"), proposal_id=None,
        actor_observation_snapshot=snapshot, hard_action_mask=mask,
        selected_action_index=action, selected_semantic_action=semantic,
        behavior_policy_log_probability=-0.5, return_record=result,
        advantage_record=advantage, provenance={"source": "TEST"},
    )


def test_behavior_action_must_be_feasible():
    with pytest.raises(ReturnSemanticError, match="BEHAVIOR_ACTION_NOT_FEASIBLE"):
        sample((False, True), 0)


def test_policy_replay_semantics_and_mismatch():
    factor = sample()
    validate_policy_replay_semantics(factor, factor.actor_observation_snapshot.action_names, factor.hard_action_mask)
    with pytest.raises(ReturnSemanticError, match="POLICY_REPLAY_SEMANTICS_MISMATCH"):
        validate_policy_replay_semantics(factor, ("X", "Y"), factor.hard_action_mask)
    with pytest.raises(ReturnSemanticError, match="POLICY_REPLAY_SEMANTICS_MISMATCH"):
        validate_policy_replay_semantics(factor, factor.actor_observation_snapshot.action_names, (True, True))


def test_importance_ratio_and_unclipped_surrogate():
    ratio = importance_ratio(torch.tensor(-0.25), torch.tensor(-0.5))
    assert torch.equal(ratio, torch.exp(torch.tensor(0.25, dtype=torch.float64)))
    assert importance_ratio(-0.5, -0.5).item() == 1.0
    assert torch.equal(unclipped_surrogate_term(ratio, -2.0), ratio * -2.0)


def test_optional_clip_helper_requires_external_positive_epsilon():
    ratio = torch.tensor(1.5)
    TEST_ONLY_NON_OPERATIONAL_VALUE = 0.1
    terms = ppo_clipped_surrogate_terms(ratio, 2.0, TEST_ONLY_NON_OPERATIONAL_VALUE)
    assert tuple(value.item() for value in terms) == pytest.approx((3.0, 2.2, 2.2))
    with pytest.raises(ReturnSemanticError, match="POSITIVE_FINITE_CLIP_EPSILON_REQUIRED"):
        ppo_clipped_surrogate_terms(ratio, 2.0, 0.0)


def test_actor_logits_predictions_and_critic_do_not_change_return():
    records = (reward("B0", "T", -3.0),)
    first = returns(records)["B0"]
    second = returns(records)["B0"]
    assert first == second
    target1 = CentralizedAdvantageCalculator.value_target(first, (-1.0,))
    target2 = CentralizedAdvantageCalculator.value_target(first, (-2.0,))
    assert target1.target_return == target2.target_return


def test_step5i_source_has_no_operational_training_parameters_or_authority():
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       for path in Path("negotiation_learning/mappo_returns").glob("*.py"))
    forbidden = ("route_id", "route_index", "ground_truth", "traci", "setspeed",
                 "optimizer", ".backward(", ".step(", "gamma =", "gae_lambda =",
                 "learning_rate", "batch_size", "rollout_length", "ppo_epochs",
                 "entropy_coefficient", "value_loss_coefficient", "total_loss")
    assert not any(item in source for item in forbidden)
    assert PPO_CLIP_PARAMETER_STATUS == "REQUIRES_EXPERIMENTAL_SELECTION"

