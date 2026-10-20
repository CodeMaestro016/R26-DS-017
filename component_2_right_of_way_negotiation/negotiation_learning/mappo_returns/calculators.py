"""Exact return, centralized target, and Monte Carlo advantage calculations."""

# Import math for use in this module.
import math

# Import REWARD_DEFINITION_ID from negotiation_objective.models for the operations below.
from negotiation_objective.models import REWARD_DEFINITION_ID

# Import ADVANTAGE_DEFINITION_STATUS, RETURN_DEFINITION_ID, RETURN_UNITS, CentralizedBatchValueTarget,
# JointBatchAdvantageRecord, JointBatchReturnRecord from .models for the operations below.
from .models import (
    ADVANTAGE_DEFINITION_STATUS, RETURN_DEFINITION_ID, RETURN_UNITS,
    CentralizedBatchValueTarget, JointBatchAdvantageRecord,
    JointBatchReturnRecord,
)


# Define ReturnSemanticError to group the state and operations declared below.
# Base classes: ValueError.
# Instances expose the attributes and methods implemented in this class.
class ReturnSemanticError(ValueError):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input code: the supplied code.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, code):
        # Call super().__init__ with the supplied arguments.
        super().__init__(code)
        # Set self.code to code.
        self.code = code


# Validate one canonical chain and calculate undiscounted suffix sums.
# Instances expose the attributes and methods implemented in this class.
class EpisodicTeamReturnCalculator:
    """Validate one canonical chain and calculate undiscounted suffix sums."""

    # Compute using the inputs and processing steps below.
    # Input team_objective_records: the supplied team objective records.
    # Input terminal_batch_id: the supplied terminal batch id.
    # Input episode_identity: the supplied episode identity.
    # Output: results.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def compute(self, team_objective_records, terminal_batch_id, episode_identity):
        # Set outgoing to an empty dictionary.
        outgoing = {}
        # Set record_by_source to an empty dictionary.
        record_by_source = {}
        # Set objective_ids_seen to an empty set.
        objective_ids_seen = set()
        # Iterate over team_objective_records, binding each item to record.
        for record in team_objective_records:
            # Run this branch when record.objective_interval_id belongs to objective_ids_seen.
            if record.objective_interval_id in objective_ids_seen:
                # Raise ReturnSemanticError with the text 'OBJECTIVE_INTERVAL_DUPLICATED' to stop this execution
                # path.
                raise ReturnSemanticError("OBJECTIVE_INTERVAL_DUPLICATED")
            # Add record.objective_interval_id to objective_ids_seen.
            objective_ids_seen.add(record.objective_interval_id)
            # Run this branch when record.source_batch_id belongs to outgoing.
            if record.source_batch_id in outgoing:
                # Raise ReturnSemanticError with the text 'OBJECTIVE_SUCCESSOR_AMBIGUOUS' to stop this execution
                # path.
                raise ReturnSemanticError("OBJECTIVE_SUCCESSOR_AMBIGUOUS")
            # Set outgoing[record.source_batch_id] to record.successor_batch_id.
            outgoing[record.source_batch_id] = record.successor_batch_id
            # Set record_by_source[record.source_batch_id] to record.
            record_by_source[record.source_batch_id] = record
        # Run this branch when terminal_batch_id belongs to outgoing.
        if terminal_batch_id in outgoing:
            # Raise ReturnSemanticError with the text 'EPISODE_TERMINATION_HAS_OUTGOING_REWARD' to stop this
            # execution path.
            raise ReturnSemanticError("EPISODE_TERMINATION_HAS_OUTGOING_REWARD")
        # Run this branch when the negation of outgoing.
        if not outgoing:
            # Raise ReturnSemanticError with the text 'TRUNCATED_ROLLOUT_BOOTSTRAP_REQUIRES_RESEARCH_DECISION' to
            # stop this execution path.
            raise ReturnSemanticError("TRUNCATED_ROLLOUT_BOOTSTRAP_REQUIRES_RESEARCH_DECISION")

        # Set all_successors to a set built from values from outgoing.
        all_successors = set(outgoing.values())
        # Set starts to a set built from outgoing minus all_successors.
        starts = set(outgoing) - all_successors
        # Run this branch when the number of entries in starts differs from 1.
        if len(starts) != 1:
            # Run this branch when the negation of starts.
            if not starts:
                # Raise ReturnSemanticError with the text 'OBJECTIVE_TIMELINE_CYCLE' to stop this execution path.
                raise ReturnSemanticError("OBJECTIVE_TIMELINE_CYCLE")
            # Raise ReturnSemanticError with the text 'OBJECTIVE_TIMELINE_DISCONNECTED' to stop this execution
            # path.
            raise ReturnSemanticError("OBJECTIVE_TIMELINE_DISCONNECTED")
        # Set (chain, seen) to a tuple containing an empty list, an empty set.
        chain, seen = [], set()
        # Set current to the next item from the result of iter(starts).
        current = next(iter(starts))
        # Repeat the following steps while current differs from terminal_batch_id.
        while current != terminal_batch_id:
            # Run this branch when current belongs to seen.
            if current in seen:
                # Raise ReturnSemanticError with the text 'OBJECTIVE_TIMELINE_CYCLE' to stop this execution path.
                raise ReturnSemanticError("OBJECTIVE_TIMELINE_CYCLE")
            # Add current to seen.
            seen.add(current)
            # Set record to current from record_by_source; use None if absent.
            record = record_by_source.get(current)
            # Run this branch when record is the same object as None.
            if record is None:
                # Raise ReturnSemanticError with the text 'OBJECTIVE_SUCCESSOR_MISSING' to stop this execution
                # path.
                raise ReturnSemanticError("OBJECTIVE_SUCCESSOR_MISSING")
            # Append record to chain.
            chain.append(record)
            # Set current to record.successor_batch_id.
            current = record.successor_batch_id
        # Run this branch when the number of entries in seen differs from the number of entries in outgoing.
        if len(seen) != len(outgoing):
            # Raise ReturnSemanticError with the text 'OBJECTIVE_TIMELINE_DISCONNECTED' to stop this execution
            # path.
            raise ReturnSemanticError("OBJECTIVE_TIMELINE_DISCONNECTED")

        # Set (suffix, objective_ids, results) to a tuple containing 0.0, an empty tuple, an empty dictionary.
        suffix, objective_ids, results = 0.0, (), {}
        # Iterate over the reverse traversal of chain, binding each item to record.
        for record in reversed(chain):
            # Accumulate rewards backward through the validated chain to obtain an undiscounted complete-episode
            # return.
            # Set suffix to record.team_reward plus suffix.
            suffix = record.team_reward + suffix
            # Set objective_ids to a tuple containing record.objective_interval_id plus objective_ids.
            objective_ids = (record.objective_interval_id,) + objective_ids
            # Set return_id to a tuple containing the text 'RETURN', record.source_batch_id, terminal_batch_id,
            # RETURN_DEFINITION_ID.
            return_id = ("RETURN", record.source_batch_id, terminal_batch_id,
                         # Include RETURN_DEFINITION_ID in this tuple.
                         RETURN_DEFINITION_ID)
            # Set results[record.source_batch_id] to the result of JointBatchReturnRecord(return_id,
            # record.source_batch_id, terminal_batch_id, objective_ids, suffix,...).
            results[record.source_batch_id] = JointBatchReturnRecord(
                # Supply record.source_batch_id to JointBatchReturnRecord.
                return_id, record.source_batch_id, terminal_batch_id,
                # Supply RETURN_DEFINITION_ID to JointBatchReturnRecord.
                objective_ids, suffix, RETURN_DEFINITION_ID,
                # Supply REWARD_DEFINITION_ID to JointBatchReturnRecord.
                REWARD_DEFINITION_ID, RETURN_UNITS, episode_identity,
                # Store the text 'NONE_COMPLETE_EPISODE' under 'bootstrap'.
                # Store the text 'NONE' under 'discount'.
                {"bootstrap": "NONE_COMPLETE_EPISODE", "discount": "NONE"},
            )
        # Return results to the caller.
        return results


# Define CentralizedAdvantageCalculator to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class CentralizedAdvantageCalculator:
    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Value target using the inputs and processing steps below.
    # Input return_record: the supplied return record.
    # Input critic_values_at_collection: the supplied critic values at collection.
    # Output: the result of CentralizedBatchValueTarget(target_id, return_record.batch_id,
    # return_record.return_record_id, target, value, target, error,...).
    # Processing: select branches using the stated conditions.
    def value_target(return_record, critic_values_at_collection):
        # Set values to a tuple built from a lazy sequence of a floating-point number built from value for value
        # in critic_values_at_collection.
        values = tuple(float(value) for value in critic_values_at_collection)
        # Run this branch when the negation of values or whether any item is true in a lazy sequence of the
        # negation of math.isfinite(value) for value in values.
        if not values or any(not math.isfinite(value) for value in values):
            # Raise ReturnSemanticError with the text 'FINITE_BATCH_CRITIC_VALUE_REQUIRED' to stop this execution
            # path.
            raise ReturnSemanticError("FINITE_BATCH_CRITIC_VALUE_REQUIRED")
        # Run this branch when whether any item is true in a lazy sequence of value differs from values at 0 for
        # value in values sliced by 1:.
        if any(value != values[0] for value in values[1:]):
            # Raise ReturnSemanticError with the text 'INCONSISTENT_BATCH_CRITIC_VALUE' to stop this execution
            # path.
            raise ReturnSemanticError("INCONSISTENT_BATCH_CRITIC_VALUE")
        # Set value to values at 0.
        value = values[0]
        # Set target to return_record.undiscounted_team_return.
        target = return_record.undiscounted_team_return
        # Set error to value minus target.
        error = value - target
        # Set target_id to a tuple containing the text 'CRITIC_TARGET', return_record.batch_id,
        # return_record.return_record_id.
        target_id = ("CRITIC_TARGET", return_record.batch_id,
                     # Include return_record.return_record_id in this tuple.
                     return_record.return_record_id)
        # Return the result of CentralizedBatchValueTarget(target_id, return_record.batch_id,
        # return_record.return_record_id, target, value, target, error,...) to the caller.
        return CentralizedBatchValueTarget(
            # Supply return_record.return_record_id to CentralizedBatchValueTarget.
            target_id, return_record.batch_id, return_record.return_record_id,
            # Supply RETURN_UNITS to CentralizedBatchValueTarget.
            target, value, target, error, error ** 2, RETURN_UNITS,
            # Store the text 'EXACT_COMPLETE_EPISODE_RETURN' under 'target'.
            {"target": "EXACT_COMPLETE_EPISODE_RETURN"},
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Advantage using the inputs and processing steps below.
    # Input return_record: the supplied return record.
    # Input value_target: the supplied value target.
    # Output: the result of JointBatchAdvantageRecord(advantage_id, return_record.batch_id,
    # return_record.return_record_id,...).
    # Processing: select branches using the stated conditions.
    def advantage(return_record, value_target):
        # Run this branch when value_target.return_record_id differs from return_record.return_record_id.
        if value_target.return_record_id != return_record.return_record_id:
            # Raise ReturnSemanticError with the text 'RETURN_VALUE_TARGET_IDENTITY_MISMATCH' to stop this
            # execution path.
            raise ReturnSemanticError("RETURN_VALUE_TARGET_IDENTITY_MISMATCH")
        # Subtract the critic value recorded at collection from the exact team return; this implementation uses no
        # GAE or advantage normalization.
        # Set advantage to return_record.undiscounted_team_return minus value_target.critic_value_at_collection.
        advantage = (return_record.undiscounted_team_return -
                     # Evaluate value_target.critic_value_at_collection as part of the enclosing expression.
                     value_target.critic_value_at_collection)
        # Set advantage_id to a tuple containing the text 'ADVANTAGE', return_record.batch_id,
        # value_target.critic_target_id.
        advantage_id = ("ADVANTAGE", return_record.batch_id,
                        # Include value_target.critic_target_id in this tuple.
                        value_target.critic_target_id)
        # Return the result of JointBatchAdvantageRecord(advantage_id, return_record.batch_id,
        # return_record.return_record_id,...) to the caller.
        return JointBatchAdvantageRecord(
            # Supply return_record.return_record_id to JointBatchAdvantageRecord.
            advantage_id, return_record.batch_id, return_record.return_record_id,
            # Supply return_record.undiscounted_team_return to JointBatchAdvantageRecord.
            value_target.critic_target_id, return_record.undiscounted_team_return,
            # Supply value_target.critic_value_at_collection to JointBatchAdvantageRecord.
            value_target.critic_value_at_collection, advantage,
            # Supply ADVANTAGE_DEFINITION_STATUS to JointBatchAdvantageRecord.
            ADVANTAGE_DEFINITION_STATUS, RETURN_UNITS,
            # Store the text 'NONE' under 'normalization'.
            # Store the text 'NONE' under 'clipping'.
            # Store the text 'NONE' under 'gae'.
            {"normalization": "NONE", "clipping": "NONE", "gae": "NONE"},
        )
