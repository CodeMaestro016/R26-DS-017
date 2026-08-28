"""One canonical non-overlapping global objective timeline."""

from .accounting import (
    ObjectiveSemanticError, interval_vehicle_exposures, raw_team_reward,
    team_interval_cost_seconds,
)
from .models import (
    GlobalObjectiveInterval, JointNegotiationDecisionBatch,
    REWARD_DEFINITION_ID, TeamObjectiveRecord,
)


class NegotiationObjectiveLedger:
    def __init__(self):
        self.reset()

    def reset(self):
        self._batches = {}
        self._intervals = {}
        self._team_records = {}
        self._current_batch_id = None
        self._current_timestamp = None

    def create_joint_decision_batch(self, snapshot_id, timestamp, phase_identity,
                                    decision_event_ids, participating_ego_ids,
                                    subjects):
        decisions = tuple(sorted(set(decision_event_ids), key=repr))
        egos = tuple(sorted(set(participating_ego_ids)))
        semantic_subjects = tuple(sorted(set(subjects), key=repr))
        batch_id = (snapshot_id, float(timestamp), phase_identity)
        candidate = JointNegotiationDecisionBatch(
            batch_id, snapshot_id, float(timestamp), phase_identity,
            decisions, egos, semantic_subjects,
        )
        prior = self._batches.get(batch_id)
        if prior is not None and prior != candidate:
            raise ObjectiveSemanticError("CONFLICTING_JOINT_DECISION_BATCH")
        self._batches[batch_id] = candidate
        return candidate

    def begin_episode(self, initial_batch):
        if self._current_batch_id is not None:
            raise ObjectiveSemanticError("OBJECTIVE_EPISODE_ALREADY_BEGUN")
        self._batches.setdefault(initial_batch.batch_id, initial_batch)
        self._current_batch_id = initial_batch.batch_id
        self._current_timestamp = initial_batch.timestamp

    def close_objective_interval(self, successor_batch, demand_records):
        if self._current_batch_id is None:
            raise ObjectiveSemanticError("OBJECTIVE_EPISODE_NOT_BEGUN")
        if successor_batch.timestamp < self._current_timestamp:
            raise ObjectiveSemanticError("NEGATIVE_OBJECTIVE_INTERVAL_DURATION")
        self._batches.setdefault(successor_batch.batch_id, successor_batch)
        interval_id = (self._current_batch_id, successor_batch.batch_id,
                       self._current_timestamp, successor_batch.timestamp)
        if interval_id in self._intervals:
            raise ObjectiveSemanticError("DUPLICATE_OBJECTIVE_INTERVAL")
        exposures = interval_vehicle_exposures(
            demand_records, self._current_timestamp, successor_batch.timestamp,
        )
        cost = team_interval_cost_seconds(exposures)
        reward = raw_team_reward(cost)
        interval = GlobalObjectiveInterval(
            interval_id, self._current_batch_id, successor_batch.batch_id,
            self._current_timestamp, successor_batch.timestamp,
            successor_batch.timestamp - self._current_timestamp,
            exposures, cost, reward,
            {"clock": "GLOBAL_NON_OVERLAPPING_OBJECTIVE_TIMELINE"},
        )
        team = TeamObjectiveRecord(
            interval_id, self._current_batch_id, successor_batch.batch_id,
            cost, reward, REWARD_DEFINITION_ID, "negative vehicle-seconds",
            {"scope": "SHARED_COOPERATIVE_TEAM_OBJECTIVE"},
        )
        self._intervals[interval_id] = interval
        self._team_records[interval_id] = team
        self._current_batch_id = successor_batch.batch_id
        self._current_timestamp = successor_batch.timestamp
        return team

    def close_episode(self, episode_identity, episode_end_time, demand_records):
        terminal = self.create_joint_decision_batch(
            ("EPISODE_TERMINATION", episode_identity), episode_end_time,
            "EPISODE_TERMINATION_BATCH", (), (), (),
        )
        record = self.close_objective_interval(terminal, demand_records)
        return terminal, record

    def team_record_for_interval(self, objective_interval_id):
        return self._team_records[objective_interval_id]

    def get_intervals(self):
        return tuple(self._intervals.values())

    def get_team_objective_records(self):
        return tuple(self._team_records.values())
