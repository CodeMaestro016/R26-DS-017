"""One canonical non-overlapping global objective timeline."""

# Import ObjectiveSemanticError, interval_vehicle_exposures, raw_team_reward, team_interval_cost_seconds from
# .accounting for the operations below.
from .accounting import (
    ObjectiveSemanticError, interval_vehicle_exposures, raw_team_reward,
    team_interval_cost_seconds,
)
# Import GlobalObjectiveInterval, JointNegotiationDecisionBatch, REWARD_DEFINITION_ID, TeamObjectiveRecord from
# .models for the operations below.
from .models import (
    GlobalObjectiveInterval, JointNegotiationDecisionBatch,
    REWARD_DEFINITION_ID, TeamObjectiveRecord,
)


# Define NegotiationObjectiveLedger to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationObjectiveLedger:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Call self.reset with the supplied arguments.
        self.reset()

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._batches to an empty dictionary.
        self._batches = {}
        # Set self._intervals to an empty dictionary.
        self._intervals = {}
        # Set self._team_records to an empty dictionary.
        self._team_records = {}
        # Set self._current_batch_id to None.
        self._current_batch_id = None
        # Set self._current_timestamp to None.
        self._current_timestamp = None

    # Create joint decision batch using the inputs and processing steps below.
    # Input snapshot_id: the supplied snapshot id.
    # Input timestamp: the supplied timestamp.
    # Input phase_identity: the supplied phase identity.
    # Input decision_event_ids: the supplied decision event ids.
    # Input participating_ego_ids: the supplied participating ego ids.
    # Input subjects: the supplied subjects.
    # Output: candidate.
    # Processing: select branches using the stated conditions.
    def create_joint_decision_batch(self, snapshot_id, timestamp, phase_identity,
                                    # Declare decision_event_ids, participating_ego_ids as input parameters.
                                    decision_event_ids, participating_ego_ids,
                                    # Declare subjects as input parameter.
                                    subjects):
        # Set decisions to a tuple built from the sorted values from a set built from decision_event_ids.
        decisions = tuple(sorted(set(decision_event_ids), key=repr))
        # Set egos to a tuple built from the sorted values from a set built from participating_ego_ids.
        egos = tuple(sorted(set(participating_ego_ids)))
        # Set semantic_subjects to a tuple built from the sorted values from a set built from subjects.
        semantic_subjects = tuple(sorted(set(subjects), key=repr))
        # Set batch_id to a tuple containing snapshot_id, a floating-point number built from timestamp,
        # phase_identity.
        batch_id = (snapshot_id, float(timestamp), phase_identity)
        # Set candidate to the result of JointNegotiationDecisionBatch(batch_id, snapshot_id, a floating-point
        # number built from timestamp, phase_identity, decisions,...).
        candidate = JointNegotiationDecisionBatch(
            # Supply a floating-point number built from timestamp to JointNegotiationDecisionBatch.
            batch_id, snapshot_id, float(timestamp), phase_identity,
            # Supply semantic_subjects to JointNegotiationDecisionBatch.
            decisions, egos, semantic_subjects,
        )
        # Set prior to batch_id from self._batches; use None if absent.
        prior = self._batches.get(batch_id)
        # Run this branch when prior is a different object from None and prior differs from candidate.
        if prior is not None and prior != candidate:
            # Raise ObjectiveSemanticError with the text 'CONFLICTING_JOINT_DECISION_BATCH' to stop this execution
            # path.
            raise ObjectiveSemanticError("CONFLICTING_JOINT_DECISION_BATCH")
        # Set self._batches[batch_id] to candidate.
        self._batches[batch_id] = candidate
        # Return candidate to the caller.
        return candidate

    # Begin episode using the inputs and processing steps below.
    # Input initial_batch: the supplied initial batch.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def begin_episode(self, initial_batch):
        # Run this branch when self._current_batch_id is a different object from None.
        if self._current_batch_id is not None:
            # Raise ObjectiveSemanticError with the text 'OBJECTIVE_EPISODE_ALREADY_BEGUN' to stop this execution
            # path.
            raise ObjectiveSemanticError("OBJECTIVE_EPISODE_ALREADY_BEGUN")
        # Call self._batches.setdefault with the supplied arguments.
        self._batches.setdefault(initial_batch.batch_id, initial_batch)
        # Set self._current_batch_id to initial_batch.batch_id.
        self._current_batch_id = initial_batch.batch_id
        # Set self._current_timestamp to initial_batch.timestamp.
        self._current_timestamp = initial_batch.timestamp

    # Close objective interval using the inputs and processing steps below.
    # Input successor_batch: the supplied successor batch.
    # Input demand_records: the supplied demand records.
    # Output: team.
    # Processing: select branches using the stated conditions.
    def close_objective_interval(self, successor_batch, demand_records):
        # Run this branch when self._current_batch_id is the same object as None.
        if self._current_batch_id is None:
            # Raise ObjectiveSemanticError with the text 'OBJECTIVE_EPISODE_NOT_BEGUN' to stop this execution
            # path.
            raise ObjectiveSemanticError("OBJECTIVE_EPISODE_NOT_BEGUN")
        # Run this branch when successor_batch.timestamp is less than self._current_timestamp.
        if successor_batch.timestamp < self._current_timestamp:
            # Raise ObjectiveSemanticError with the text 'NEGATIVE_OBJECTIVE_INTERVAL_DURATION' to stop this
            # execution path.
            raise ObjectiveSemanticError("NEGATIVE_OBJECTIVE_INTERVAL_DURATION")
        # Call self._batches.setdefault with the supplied arguments.
        self._batches.setdefault(successor_batch.batch_id, successor_batch)
        # Set interval_id to a tuple containing self._current_batch_id, successor_batch.batch_id,
        # self._current_timestamp, successor_batch.timestamp.
        interval_id = (self._current_batch_id, successor_batch.batch_id,
                       # Include successor_batch.timestamp in this tuple.
                       self._current_timestamp, successor_batch.timestamp)
        # Run this branch when interval_id belongs to self._intervals.
        if interval_id in self._intervals:
            # Raise ObjectiveSemanticError with the text 'DUPLICATE_OBJECTIVE_INTERVAL' to stop this execution
            # path.
            raise ObjectiveSemanticError("DUPLICATE_OBJECTIVE_INTERVAL")
        # Set exposures to the result of interval_vehicle_exposures(demand_records, self._current_timestamp,
        # successor_batch.timestamp).
        exposures = interval_vehicle_exposures(
            # Supply successor_batch.timestamp to interval_vehicle_exposures.
            demand_records, self._current_timestamp, successor_batch.timestamp,
        )
        # Set cost to the result of team_interval_cost_seconds(exposures).
        cost = team_interval_cost_seconds(exposures)
        # Set reward to the result of raw_team_reward(cost).
        reward = raw_team_reward(cost)
        # Set interval to the result of GlobalObjectiveInterval(interval_id, self._current_batch_id,
        # successor_batch.batch_id, self._current_timestamp,...).
        interval = GlobalObjectiveInterval(
            # Supply successor_batch.batch_id to GlobalObjectiveInterval.
            interval_id, self._current_batch_id, successor_batch.batch_id,
            # Supply successor_batch.timestamp to GlobalObjectiveInterval.
            self._current_timestamp, successor_batch.timestamp,
            # Supply successor_batch.timestamp minus self._current_timestamp to GlobalObjectiveInterval.
            successor_batch.timestamp - self._current_timestamp,
            # Supply exposures to GlobalObjectiveInterval.
            exposures, cost, reward,
            # Store the text 'GLOBAL_NON_OVERLAPPING_OBJECTIVE_TIMELINE' under 'clock'.
            {"clock": "GLOBAL_NON_OVERLAPPING_OBJECTIVE_TIMELINE"},
        )
        # Set team to the result of TeamObjectiveRecord(interval_id, self._current_batch_id,
        # successor_batch.batch_id, cost, reward,...).
        team = TeamObjectiveRecord(
            # Supply successor_batch.batch_id to TeamObjectiveRecord.
            interval_id, self._current_batch_id, successor_batch.batch_id,
            # Supply REWARD_DEFINITION_ID to TeamObjectiveRecord.
            cost, reward, REWARD_DEFINITION_ID, "negative vehicle-seconds",
            # Store the text 'SHARED_COOPERATIVE_TEAM_OBJECTIVE' under 'scope'.
            {"scope": "SHARED_COOPERATIVE_TEAM_OBJECTIVE"},
        )
        # Set self._intervals[interval_id] to interval.
        self._intervals[interval_id] = interval
        # Set self._team_records[interval_id] to team.
        self._team_records[interval_id] = team
        # Set self._current_batch_id to successor_batch.batch_id.
        self._current_batch_id = successor_batch.batch_id
        # Set self._current_timestamp to successor_batch.timestamp.
        self._current_timestamp = successor_batch.timestamp
        # Return team to the caller.
        return team

    # Close episode using the inputs and processing steps below.
    # Input episode_identity: the supplied episode identity.
    # Input episode_end_time: the supplied episode end time.
    # Input demand_records: the supplied demand records.
    # Output: a tuple containing terminal, record.
    def close_episode(self, episode_identity, episode_end_time, demand_records):
        # Set terminal to the result of self.create_joint_decision_batch(a tuple containing the text
        # 'EPISODE_TERMINATION', episode_identity, episode_end_time, the text...).
        terminal = self.create_joint_decision_batch(
            # Supply a tuple containing the text 'EPISODE_TERMINATION', episode_identity to
            # self.create_joint_decision_batch.
            ("EPISODE_TERMINATION", episode_identity), episode_end_time,
            # Supply an empty tuple to self.create_joint_decision_batch.
            "EPISODE_TERMINATION_BATCH", (), (), (),
        )
        # Set record to the result of self.close_objective_interval(terminal, demand_records).
        record = self.close_objective_interval(terminal, demand_records)
        # Return a tuple containing terminal, record to the caller.
        return terminal, record

    # Team record for interval using the inputs and processing steps below.
    # Input objective_interval_id: the supplied objective interval id.
    # Output: self._team_records at objective_interval_id.
    def team_record_for_interval(self, objective_interval_id):
        # Return self._team_records at objective_interval_id to the caller.
        return self._team_records[objective_interval_id]

    # Get intervals using the inputs and processing steps below.
    # Output: a tuple built from values from self._intervals.
    def get_intervals(self):
        # Return a tuple built from values from self._intervals to the caller.
        return tuple(self._intervals.values())

    # Get team objective records using the inputs and processing steps below.
    # Output: a tuple built from values from self._team_records.
    def get_team_objective_records(self):
        # Return a tuple built from values from self._team_records to the caller.
        return tuple(self._team_records.values())
