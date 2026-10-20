# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace

# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch

# Import CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator, PPO_CLIP_PARAMETER_STATUS,
# ReturnSemanticError, create_policy_factor_sample, importance_ratio,... from negotiation_learning.mappo_returns
# for the operations below.
from negotiation_learning.mappo_returns import (
    CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator,
    PPO_CLIP_PARAMETER_STATUS, ReturnSemanticError,
    create_policy_factor_sample, importance_ratio,
    ppo_clipped_surrogate_terms, unclipped_surrogate_term,
    validate_policy_replay_semantics,
)
# Import NegotiationObjectiveLedger from negotiation_objective for the operations below.
from negotiation_objective import NegotiationObjectiveLedger
# Import REWARD_DEFINITION_ID, TeamObjectiveRecord from negotiation_objective.models for the operations below.
from negotiation_objective.models import REWARD_DEFINITION_ID, TeamObjectiveRecord
# Import DemandScheduleSource, VehicleDemandLedger from traffic_accounting for the operations below.
from traffic_accounting import DemandScheduleSource, VehicleDemandLedger


# Reward using the inputs and processing steps below.
# Input source: the supplied source.
# Input successor: the supplied successor.
# Input value: the supplied value.
# Input identity: the supplied identity.
# Output: the result of TeamObjectiveRecord(interval_id, source, successor, the negative of value, value,
# REWARD_DEFINITION_ID, the text...).
def reward(source, successor, value, identity=None):
    # Set interval_id to identity or a tuple containing the text 'interval', source, successor.
    interval_id = identity or ("interval", source, successor)
    # Return the result of TeamObjectiveRecord(interval_id, source, successor, the negative of value, value,
    # REWARD_DEFINITION_ID, the text...) to the caller.
    return TeamObjectiveRecord(
        # Supply interval_id to TeamObjectiveRecord.
        interval_id, source, successor, -value, value,
        # Store the text 'only' under 'test'.
        REWARD_DEFINITION_ID, "negative vehicle-seconds", {"test": "only"},
    )


# Returns using the inputs and processing steps below.
# Input records: the supplied records.
# Input terminal: the supplied terminal.
# Output: the result of EpisodicTeamReturnCalculator().compute(records, terminal, the text 'episode').
def returns(records, terminal="T"):
    # Return the result of EpisodicTeamReturnCalculator().compute(records, terminal, the text 'episode') to the
    # caller.
    return EpisodicTeamReturnCalculator().compute(records, terminal, "episode")


# Check two and three interval suffix returns using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_and_three_interval_suffix_returns():
    # Set two to the result of returns(a tuple containing the result of reward(the text 'B0', the text 'B1', the
    # negative of 2.0), the...).
    two = returns((reward("B0", "B1", -2.0), reward("B1", "T", -3.0)))
    # Require two['B1'].undiscounted_team_return equals the negative of 3.0; otherwise raise AssertionError.
    assert two["B1"].undiscounted_team_return == -3.0
    # Require two['B0'].undiscounted_team_return equals the negative of 5.0; otherwise raise AssertionError.
    assert two["B0"].undiscounted_team_return == -5.0
    # Set three to the result of returns(a tuple containing the result of reward(the text 'B0', the text 'B1', the
    # negative of 1.0), the...).
    three = returns((reward("B0", "B1", -1.0), reward("B1", "B2", -2.0), reward("B2", "T", -4.0)))
    # Require a tuple built from a lazy sequence of three[key].undiscounted_team_return for key in a tuple
    # containing 'B0', 'B1', 'B2' equals a tuple containing the negative of 7.0, the negative of 6.0, the negative
    # of 4.0; otherwise raise AssertionError.
    assert tuple(three[key].undiscounted_team_return for key in ("B0", "B1", "B2")) == (-7.0, -6.0, -4.0)


# Check zero duration middle phase preserves return using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_zero_duration_middle_phase_preserves_return():
    # Set result to the result of returns(a tuple containing the result of reward(the text 'P', the text 'R',
    # 0.0), the result of...).
    result = returns((reward("P", "R", 0.0), reward("R", "T", -5.0)))
    # Require result['P'].undiscounted_team_return equals result['R'].undiscounted_team_return; equals the
    # negative of 5.0; otherwise raise AssertionError.
    assert result["P"].undiscounted_team_return == result["R"].undiscounted_team_return == -5.0


# Check partition invariance using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_partition_invariance():
    # Set whole to returns((reward('B0', 'T', -6.0),)) at 'B0'.
    whole = returns((reward("B0", "T", -6.0),))["B0"]
    # Set split to returns((reward('B0', 'B1', -2.0), reward('B1', 'T', -4.0))) at 'B0'.
    split = returns((reward("B0", "B1", -2.0), reward("B1", "T", -4.0)))["B0"]
    # Require whole.undiscounted_team_return equals split.undiscounted_team_return; otherwise raise
    # AssertionError.
    assert whole.undiscounted_team_return == split.undiscounted_team_return


# Check claim resolution and vehicle arrival are not team terminal using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_claim_resolution_and_vehicle_arrival_are_not_team_terminal():
    # Set result to the result of returns(a tuple containing the result of reward(the text 'CLAIM_RESOLVED', the
    # text 'VEHICLE_ARRIVED',...).
    result = returns((
        # Include the result of reward(the text 'CLAIM_RESOLVED', the text 'VEHICLE_ARRIVED', the negative of 2.0)
        # in this tuple.
        reward("CLAIM_RESOLVED", "VEHICLE_ARRIVED", -2.0),
        # Include the result of reward(the text 'VEHICLE_ARRIVED', the text 'T', the negative of 3.0) in this
        # tuple.
        reward("VEHICLE_ARRIVED", "T", -3.0),
    ))
    # Require result['CLAIM_RESOLVED'].undiscounted_team_return equals the negative of 5.0; otherwise raise
    # AssertionError.
    assert result["CLAIM_RESOLVED"].undiscounted_team_return == -5.0
    # Require result['VEHICLE_ARRIVED'].undiscounted_team_return equals the negative of 3.0; otherwise raise
    # AssertionError.
    assert result["VEHICLE_ARRIVED"].undiscounted_team_return == -3.0


# Check terminal batch is action free and closes final interval using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_terminal_batch_is_action_free_and_closes_final_interval():
    # Set demands to the result of VehicleDemandLedger().
    demands = VehicleDemandLedger()
    # Call demands.register_scheduled_vehicle with the supplied arguments.
    demands.register_scheduled_vehicle("AV_0", 0.0, DemandScheduleSource.INITIAL_SIMULATION_DEMAND)
    # Set objective to the result of NegotiationObjectiveLedger().
    objective = NegotiationObjectiveLedger()
    # Set start to the result of objective.create_joint_decision_batch(a tuple containing the text 'S', 0.0, the
    # text 'PROPOSER', a tuple containing a tuple containing...).
    start = objective.create_joint_decision_batch(("S",), 0.0, "PROPOSER", (("D",),), ("A",), (("A", "B"),))
    # Call objective.begin_episode with the supplied arguments.
    objective.begin_episode(start)
    # Set (terminal, record) to the result of objective.close_episode(the text 'episode', 2.0, the result of
    # demands.get_all_records()).
    terminal, record = objective.close_episode("episode", 2.0, demands.get_all_records())
    # Require terminal.phase_identity equals the text 'EPISODE_TERMINATION_BATCH'; otherwise raise AssertionError.
    assert terminal.phase_identity == "EPISODE_TERMINATION_BATCH"
    # Require terminal.decision_event_ids equals an empty tuple; otherwise raise AssertionError.
    assert terminal.decision_event_ids == ()
    # Require record.successor_batch_id equals terminal.batch_id; otherwise raise AssertionError.
    assert record.successor_batch_id == terminal.batch_id
    # Require returns((record,), terminal.batch_id)[start.batch_id].undiscounted_team_return equals the negative
    # of 2.0; otherwise raise AssertionError.
    assert returns((record,), terminal.batch_id)[start.batch_id].undiscounted_team_return == -2.0


# Check missing ambiguous cycle and duplicate interval rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_missing_ambiguous_cycle_and_duplicate_interval_rejected():
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_SUCCESSOR_MISSING"):
        # Call returns with the supplied arguments.
        returns((reward("B0", "MISSING", -1.0),))
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_SUCCESSOR_AMBIGUOUS"):
        # Call returns with the supplied arguments.
        returns((reward("B0", "B1", -1.0), reward("B0", "T", -2.0)))
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_TIMELINE_CYCLE"):
        # Call returns with the supplied arguments.
        returns((reward("B0", "B1", -1.0), reward("B1", "B0", -2.0)))
    # Set duplicate to a tuple containing the text 'same'.
    duplicate = ("same",)
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="OBJECTIVE_INTERVAL_DUPLICATED"):
        # Call returns with the supplied arguments.
        returns((reward("B0", "B1", -1.0, duplicate), reward("B1", "T", -2.0, duplicate)))


# Check truncated empty rollout is not bootstrapped using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_truncated_empty_rollout_is_not_bootstrapped():
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="TRUNCATED_ROLLOUT_BOOTSTRAP_REQUIRES_RESEARCH_DECISION"):
        # Call returns with the supplied arguments.
        returns(())


# Check one return and one value target per batch shared by decisions using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_one_return_and_one_value_target_per_batch_shared_by_decisions():
    # Set record to returns((reward('B0', 'T', -4.0),)) at 'B0'.
    record = returns((reward("B0", "T", -4.0),))["B0"]
    # Set target to the result of CentralizedAdvantageCalculator.value_target(record, a tuple containing 1.0,
    # 1.0).
    target = CentralizedAdvantageCalculator.value_target(record, (1.0, 1.0))
    # Require target.batch_id equals the text 'B0'; otherwise raise AssertionError.
    assert target.batch_id == "B0"
    # Require target.critic_target equals the negative of 4.0; otherwise raise AssertionError.
    assert target.critic_target == -4.0
    # Require whether every item is true in a lazy sequence of record.return_record_id equals
    # record.return_record_id for _ in a tuple containing the text 'D1', the text 'D2', the text 'D3'; otherwise
    # raise AssertionError.
    assert all(record.return_record_id == record.return_record_id for _ in ("D1", "D2", "D3"))


# Check conflicting batch critic values rejected using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_conflicting_batch_critic_values_rejected():
    # Set record to returns((reward('B0', 'T', -4.0),)) at 'B0'.
    record = returns((reward("B0", "T", -4.0),))["B0"]
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="INCONSISTENT_BATCH_CRITIC_VALUE"):
        # Call CentralizedAdvantageCalculator.value_target with the supplied arguments.
        CentralizedAdvantageCalculator.value_target(record, (1.0, 2.0))


# Apply pytest.mark.parametrize('critic,expected_sign', [(-6.0, 1), (-5.0, 0), (-4.0, -1)]) as a decorator to
# configure the following definition.
@pytest.mark.parametrize("critic,expected_sign", [(-6.0, 1), (-5.0, 0), (-4.0, -1)])
# Check exact monte carlo advantage sign using the setup, calls, and assertions below.
# Input critic: the supplied critic.
# Input expected_sign: the supplied expected sign.
# Output: no explicit value; normal completion returns None.
def test_exact_monte_carlo_advantage_sign(critic, expected_sign):
    # Set record to returns((reward('B0', 'T', -5.0),)) at 'B0'.
    record = returns((reward("B0", "T", -5.0),))["B0"]
    # Set target to the result of CentralizedAdvantageCalculator.value_target(record, a tuple containing critic).
    target = CentralizedAdvantageCalculator.value_target(record, (critic,))
    # Set advantage to the result of CentralizedAdvantageCalculator.advantage(record, target).
    advantage = CentralizedAdvantageCalculator.advantage(record, target)
    # Require advantage.advantage equals the negative of 5.0 minus critic; otherwise raise AssertionError.
    assert advantage.advantage == -5.0 - critic
    # Require advantage.advantage is greater than 0 minus advantage.advantage is less than 0 equals expected_sign;
    # otherwise raise AssertionError.
    assert (advantage.advantage > 0) - (advantage.advantage < 0) == expected_sign
    # Require target.value_error equals critic minus the negative of 5.0; otherwise raise AssertionError.
    assert target.value_error == critic - (-5.0)
    # Require target.value_squared_error equals target.value_error raised to the power 2; otherwise raise
    # AssertionError.
    assert target.value_squared_error == target.value_error ** 2


# Sample using the inputs and processing steps below.
# Input mask: the supplied mask.
# Input action: the supplied action.
# Input semantic: the supplied semantic.
# Output: the result of create_policy_factor_sample().
def sample(mask=(True, False), action=0, semantic="KEEP_CLAIM"):
    # Set result to returns((reward('B0', 'T', -2.0),)) at 'B0'.
    result = returns((reward("B0", "T", -2.0),))["B0"]
    # Set target to the result of CentralizedAdvantageCalculator.value_target(result, a tuple containing the
    # negative of 1.0).
    target = CentralizedAdvantageCalculator.value_target(result, (-1.0,))
    # Set advantage to the result of CentralizedAdvantageCalculator.advantage(result, target).
    advantage = CentralizedAdvantageCalculator.advantage(result, target)
    # Set snapshot to the result of SimpleNamespace().
    snapshot = SimpleNamespace(action_names=("KEEP_CLAIM", "RELINQUISH_CLAIM"))
    # Return the result of create_policy_factor_sample() to the caller.
    return create_policy_factor_sample(
        # Supply decision_event_id as a tuple containing the text 'D'.
        # Supply joint_batch_id as the text 'B0'.
        # Supply ego_id as the text 'A'.
        decision_event_id=("D",), joint_batch_id="B0", ego_id="A",
        # Supply decision_role as the text 'PROPOSER'.
        # Supply claim_identity as a tuple containing the text 'B', the text 'A'.
        # Supply proposal_id as None.
        decision_role="PROPOSER", claim_identity=("B", "A"), proposal_id=None,
        # Supply actor_observation_snapshot as snapshot.
        # Supply hard_action_mask as mask.
        actor_observation_snapshot=snapshot, hard_action_mask=mask,
        # Supply selected_action_index as action.
        # Supply selected_semantic_action as semantic.
        selected_action_index=action, selected_semantic_action=semantic,
        # Supply behavior_policy_log_probability as the negative of 0.5.
        # Supply return_record as result.
        behavior_policy_log_probability=-0.5, return_record=result,
        # Store the text 'TEST' under 'source'.
        advantage_record=advantage, provenance={"source": "TEST"},
    )


# Check behavior action must be feasible using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_behavior_action_must_be_feasible():
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="BEHAVIOR_ACTION_NOT_FEASIBLE"):
        # Call sample with the supplied arguments.
        sample((False, True), 0)


# Check policy replay semantics and mismatch using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_policy_replay_semantics_and_mismatch():
    # Set factor to the result of sample().
    factor = sample()
    # Call validate_policy_replay_semantics with the supplied arguments.
    validate_policy_replay_semantics(factor, factor.actor_observation_snapshot.action_names, factor.hard_action_mask)
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="POLICY_REPLAY_SEMANTICS_MISMATCH"):
        # Call validate_policy_replay_semantics with the supplied arguments.
        validate_policy_replay_semantics(factor, ("X", "Y"), factor.hard_action_mask)
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="POLICY_REPLAY_SEMANTICS_MISMATCH"):
        # Call validate_policy_replay_semantics with the supplied arguments.
        validate_policy_replay_semantics(factor, factor.actor_observation_snapshot.action_names, (True, True))


# Check importance ratio and unclipped surrogate using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_importance_ratio_and_unclipped_surrogate():
    # Set ratio to the result of importance_ratio(a tensor built from the negative of 0.25, a tensor built from
    # the negative of 0.5).
    ratio = importance_ratio(torch.tensor(-0.25), torch.tensor(-0.5))
    # Require the result of torch.equal(ratio, the exponential of a tensor built from 0.25); otherwise raise
    # AssertionError.
    assert torch.equal(ratio, torch.exp(torch.tensor(0.25, dtype=torch.float64)))
    # Require the result of importance_ratio(-0.5, -0.5).item() equals 1.0; otherwise raise AssertionError.
    assert importance_ratio(-0.5, -0.5).item() == 1.0
    # Require the result of torch.equal(the result of unclipped_surrogate_term(ratio, the negative of 2.0), ratio
    # multiplied by the...); otherwise raise AssertionError.
    assert torch.equal(unclipped_surrogate_term(ratio, -2.0), ratio * -2.0)


# Check optional clip helper requires external positive epsilon using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_optional_clip_helper_requires_external_positive_epsilon():
    # Set ratio to a tensor built from 1.5.
    ratio = torch.tensor(1.5)
    # Set TEST_ONLY_NON_OPERATIONAL_VALUE to 0.1.
    TEST_ONLY_NON_OPERATIONAL_VALUE = 0.1
    # Set terms to the result of ppo_clipped_surrogate_terms(ratio, 2.0, TEST_ONLY_NON_OPERATIONAL_VALUE).
    terms = ppo_clipped_surrogate_terms(ratio, 2.0, TEST_ONLY_NON_OPERATIONAL_VALUE)
    # Require a tuple built from a lazy sequence of the result of value.item() for value in terms equals the
    # result of pytest.approx(a tuple containing 3.0, 2.2, 2.2); otherwise raise AssertionError.
    assert tuple(value.item() for value in terms) == pytest.approx((3.0, 2.2, 2.2))
    # Enter the result of pytest.raises(ReturnSemanticError) and run the enclosed operations within that context.
    with pytest.raises(ReturnSemanticError, match="POSITIVE_FINITE_CLIP_EPSILON_REQUIRED"):
        # Call ppo_clipped_surrogate_terms with the supplied arguments.
        ppo_clipped_surrogate_terms(ratio, 2.0, 0.0)


# Check actor logits predictions and critic do not change return using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actor_logits_predictions_and_critic_do_not_change_return():
    # Set records to a tuple containing the result of reward(the text 'B0', the text 'T', the negative of 3.0).
    records = (reward("B0", "T", -3.0),)
    # Set first to returns(records) at 'B0'.
    first = returns(records)["B0"]
    # Set second to returns(records) at 'B0'.
    second = returns(records)["B0"]
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Set target1 to the result of CentralizedAdvantageCalculator.value_target(first, a tuple containing the
    # negative of 1.0).
    target1 = CentralizedAdvantageCalculator.value_target(first, (-1.0,))
    # Set target2 to the result of CentralizedAdvantageCalculator.value_target(first, a tuple containing the
    # negative of 2.0).
    target2 = CentralizedAdvantageCalculator.value_target(first, (-2.0,))
    # Require target1.target_return equals target2.target_return; otherwise raise AssertionError.
    assert target1.target_return == target2.target_return


# Check step5i source has no operational training parameters or authority using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_step5i_source_has_no_operational_training_parameters_or_authority():
    # Set source to the result of '\n'.join(a lazy sequence of the result of
    # path.read_text(encoding='utf-8').lower() for path in the result...).
    source = "\n".join(path.read_text(encoding="utf-8").lower()
                       # Evaluate the result of Path('negotiation_learning/mappo_returns').glob(the text '*.py')
                       # as part of the enclosing expression.
                       for path in Path("negotiation_learning/mappo_returns").glob("*.py"))
    # Set forbidden to a tuple containing the text 'route_id', the text 'route_index', the text 'ground_truth',
    # the text 'traci', the text...
    forbidden = ("route_id", "route_index", "ground_truth", "traci", "setspeed",
                 "optimizer", ".backward(", ".step(", "gamma =", "gae_lambda =",
                 "learning_rate", "batch_size", "rollout_length", "ppo_epochs",
                 "entropy_coefficient", "value_loss_coefficient", "total_loss")
    # Require the negation of whether any item is true in a lazy sequence of item belongs to source for item in
    # forbidden; otherwise raise AssertionError.
    assert not any(item in source for item in forbidden)
    # Require PPO_CLIP_PARAMETER_STATUS equals the text 'REQUIRES_EXPERIMENTAL_SELECTION'; otherwise raise
    # AssertionError.
    assert PPO_CLIP_PARAMETER_STATUS == "REQUIRES_EXPERIMENTAL_SELECTION"

