import math

import pytest

from negotiation_training.mappo_provider import (
    MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle,
)
from negotiation_training.pilot_analysis import (
    paired_difference_summary,
    two_replication_sample_statistics,
)
from negotiation_training.rollout import parameter_hash


def test_two_replication_statistics_use_n_minus_one_sample_variance():
    result = two_replication_sample_statistics((10.0, 14.0))
    assert result["sample_mean"] == 12.0
    assert result["sample_variance_n_minus_1"] == 8.0
    assert result["sample_standard_deviation"] == math.sqrt(8.0)


def test_variance_probe_rejects_non_two_sample_input():
    with pytest.raises(ValueError, match="EXACTLY_TWO"):
        two_replication_sample_statistics((1.0,))


def test_paired_difference_summary_is_threshold_free_and_complete():
    result = paired_difference_summary((-2.0, 0.0, 4.0))
    assert result == {
        "count": 3,
        "mean": pytest.approx(2.0 / 3.0),
        "median": 0.0,
        "minimum": -2.0,
        "maximum": 4.0,
        "negative_count": 1,
        "zero_count": 1,
        "positive_count": 1,
    }


def test_replication_initialization_is_reproducible_but_identity_specific():
    first = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("REPLICATION", 0))
    repeat = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("REPLICATION", 0))
    second = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("REPLICATION", 1))
    assert parameter_hash(first.proposer_actor) == parameter_hash(
        repeat.proposer_actor)
    assert parameter_hash(first.proposer_actor) != parameter_hash(
        second.proposer_actor)


def test_sampling_seed_is_explicit_and_does_not_mutate_parameters():
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        component_seed_identity=("PILOT", 0))
    before = parameter_hash(bundle.proposer_actor)
    provider = MAPPOBehaviorActionProvider(bundle=bundle, sampling_seed=173)
    assert provider.sampling_seed == 173
    assert parameter_hash(bundle.proposer_actor) == before
