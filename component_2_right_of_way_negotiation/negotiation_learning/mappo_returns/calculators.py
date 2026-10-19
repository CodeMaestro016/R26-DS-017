"""Exact return, centralized target, and Monte Carlo advantage calculations."""

import math

from negotiation_objective.models import REWARD_DEFINITION_ID

from .models import (
    ADVANTAGE_DEFINITION_STATUS, RETURN_DEFINITION_ID, RETURN_UNITS,
    CentralizedBatchValueTarget, JointBatchAdvantageRecord,
    JointBatchReturnRecord,
)


class ReturnSemanticError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class EpisodicTeamReturnCalculator:
    """Validate one canonical chain and calculate undiscounted suffix sums."""

    def compute(self, team_objective_records, terminal_batch_id, episode_identity):
        outgoing = {}
        record_by_source = {}
        objective_ids_seen = set()
        for record in team_objective_records:
            if record.objective_interval_id in objective_ids_seen:
                raise ReturnSemanticError("OBJECTIVE_INTERVAL_DUPLICATED")
            objective_ids_seen.add(record.objective_interval_id)
            if record.source_batch_id in outgoing:
                raise ReturnSemanticError("OBJECTIVE_SUCCESSOR_AMBIGUOUS")
            outgoing[record.source_batch_id] = record.successor_batch_id
            record_by_source[record.source_batch_id] = record
        if terminal_batch_id in outgoing:
            raise ReturnSemanticError("EPISODE_TERMINATION_HAS_OUTGOING_REWARD")
        if not outgoing:
            raise ReturnSemanticError("TRUNCATED_ROLLOUT_BOOTSTRAP_REQUIRES_RESEARCH_DECISION")

        all_successors = set(outgoing.values())
        starts = set(outgoing) - all_successors
        if len(starts) != 1:
            if not starts:
                raise ReturnSemanticError("OBJECTIVE_TIMELINE_CYCLE")
            raise ReturnSemanticError("OBJECTIVE_TIMELINE_DISCONNECTED")
        chain, seen = [], set()
        current = next(iter(starts))
        while current != terminal_batch_id:
            if current in seen:
                raise ReturnSemanticError("OBJECTIVE_TIMELINE_CYCLE")
            seen.add(current)
            record = record_by_source.get(current)
            if record is None:
                raise ReturnSemanticError("OBJECTIVE_SUCCESSOR_MISSING")
            chain.append(record)
            current = record.successor_batch_id
        if len(seen) != len(outgoing):
            raise ReturnSemanticError("OBJECTIVE_TIMELINE_DISCONNECTED")

        suffix, objective_ids, results = 0.0, (), {}
        for record in reversed(chain):
            suffix = record.team_reward + suffix
            objective_ids = (record.objective_interval_id,) + objective_ids
            return_id = ("RETURN", record.source_batch_id, terminal_batch_id,
                         RETURN_DEFINITION_ID)
            results[record.source_batch_id] = JointBatchReturnRecord(
                return_id, record.source_batch_id, terminal_batch_id,
                objective_ids, suffix, RETURN_DEFINITION_ID,
                REWARD_DEFINITION_ID, RETURN_UNITS, episode_identity,
                {"bootstrap": "NONE_COMPLETE_EPISODE", "discount": "NONE"},
            )
        return results


class CentralizedAdvantageCalculator:
    @staticmethod
    def value_target(return_record, critic_values_at_collection):
        values = tuple(float(value) for value in critic_values_at_collection)
        if not values or any(not math.isfinite(value) for value in values):
            raise ReturnSemanticError("FINITE_BATCH_CRITIC_VALUE_REQUIRED")
        if any(value != values[0] for value in values[1:]):
            raise ReturnSemanticError("INCONSISTENT_BATCH_CRITIC_VALUE")
        value = values[0]
        target = return_record.undiscounted_team_return
        error = value - target
        target_id = ("CRITIC_TARGET", return_record.batch_id,
                     return_record.return_record_id)
        return CentralizedBatchValueTarget(
            target_id, return_record.batch_id, return_record.return_record_id,
            target, value, target, error, error ** 2, RETURN_UNITS,
            {"target": "EXACT_COMPLETE_EPISODE_RETURN"},
        )

    @staticmethod
    def advantage(return_record, value_target):
        if value_target.return_record_id != return_record.return_record_id:
            raise ReturnSemanticError("RETURN_VALUE_TARGET_IDENTITY_MISMATCH")
        advantage = (return_record.undiscounted_team_return -
                     value_target.critic_value_at_collection)
        advantage_id = ("ADVANTAGE", return_record.batch_id,
                        value_target.critic_target_id)
        return JointBatchAdvantageRecord(
            advantage_id, return_record.batch_id, return_record.return_record_id,
            value_target.critic_target_id, return_record.undiscounted_team_return,
            value_target.critic_value_at_collection, advantage,
            ADVANTAGE_DEFINITION_STATUS, RETURN_UNITS,
            {"normalization": "NONE", "clipping": "NONE", "gae": "NONE"},
        )
