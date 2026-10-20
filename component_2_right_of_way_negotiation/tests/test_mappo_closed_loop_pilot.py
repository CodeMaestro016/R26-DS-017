# Import math for use in this module.
import math

# Import pytest for use in this module.
import pytest

# Import MAPPOBehaviorActionProvider, build_mechanical_mappo_behavior_policy_bundle from
# negotiation_training.mappo_provider for the operations below.
from negotiation_training.mappo_provider import (
    MAPPOBehaviorActionProvider,
    build_mechanical_mappo_behavior_policy_bundle,
)
# Import paired_difference_summary, two_replication_sample_statistics from negotiation_training.pilot_analysis for
# the operations below.
from negotiation_training.pilot_analysis import (
    paired_difference_summary,
    two_replication_sample_statistics,
)
# Import parameter_hash from negotiation_training.rollout for the operations below.
from negotiation_training.rollout import parameter_hash


# Check two replication statistics use n minus one sample variance using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_two_replication_statistics_use_n_minus_one_sample_variance():
    # Set result to the result of two_replication_sample_statistics(a tuple containing 10.0, 14.0).
    result = two_replication_sample_statistics((10.0, 14.0))
    # Require result at 'sample_mean' equals 12.0; otherwise raise AssertionError.
    assert result["sample_mean"] == 12.0
    # Require result at 'sample_variance_n_minus_1' equals 8.0; otherwise raise AssertionError.
    assert result["sample_variance_n_minus_1"] == 8.0
    # Require result at 'sample_standard_deviation' equals the square root of 8.0; otherwise raise AssertionError.
    assert result["sample_standard_deviation"] == math.sqrt(8.0)


# Check variance probe rejects non two sample input using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_variance_probe_rejects_non_two_sample_input():
    # Enter the result of pytest.raises(ValueError) and run the enclosed operations within that context.
    with pytest.raises(ValueError, match="EXACTLY_TWO"):
        # Call two_replication_sample_statistics with the supplied arguments.
        two_replication_sample_statistics((1.0,))


# Check paired difference summary is threshold free and complete using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_paired_difference_summary_is_threshold_free_and_complete():
    # Set result to the result of paired_difference_summary(a tuple containing the negative of 2.0, 0.0, 4.0).
    result = paired_difference_summary((-2.0, 0.0, 4.0))
    # Require result equals a dictionary containing count, mean, median, minimum, maximum, negative_count,
    # zero_count, positive_count; otherwise raise AssertionError.
    assert result == {
        # Store 3 under 'count'.
        "count": 3,
        # Store the result of pytest.approx(2.0 divided by 3.0) under 'mean'.
        "mean": pytest.approx(2.0 / 3.0),
        # Store 0.0 under 'median'.
        "median": 0.0,
        # Store the negative of 2.0 under 'minimum'.
        "minimum": -2.0,
        # Store 4.0 under 'maximum'.
        "maximum": 4.0,
        # Store 1 under 'negative_count'.
        "negative_count": 1,
        # Store 1 under 'zero_count'.
        "zero_count": 1,
        # Store 1 under 'positive_count'.
        "positive_count": 1,
    }


# Check replication initialization is reproducible but identity specific using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_replication_initialization_is_reproducible_but_identity_specific():
    # Set first to the result of build_mechanical_mappo_behavior_policy_bundle().
    first = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'REPLICATION', 0.
        component_seed_identity=("REPLICATION", 0))
    # Set repeat to the result of build_mechanical_mappo_behavior_policy_bundle().
    repeat = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'REPLICATION', 0.
        component_seed_identity=("REPLICATION", 0))
    # Set second to the result of build_mechanical_mappo_behavior_policy_bundle().
    second = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'REPLICATION', 1.
        component_seed_identity=("REPLICATION", 1))
    # Require the result of parameter_hash(first.proposer_actor) equals the result of
    # parameter_hash(repeat.proposer_actor); otherwise raise AssertionError.
    assert parameter_hash(first.proposer_actor) == parameter_hash(
        # Supply repeat.proposer_actor to parameter_hash.
        repeat.proposer_actor)
    # Require the result of parameter_hash(first.proposer_actor) differs from the result of
    # parameter_hash(second.proposer_actor); otherwise raise AssertionError.
    assert parameter_hash(first.proposer_actor) != parameter_hash(
        # Supply second.proposer_actor to parameter_hash.
        second.proposer_actor)


# Check sampling seed is explicit and does not mutate parameters using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_sampling_seed_is_explicit_and_does_not_mutate_parameters():
    # Set bundle to the result of build_mechanical_mappo_behavior_policy_bundle().
    bundle = build_mechanical_mappo_behavior_policy_bundle(
        # Supply component_seed_identity as a tuple containing the text 'PILOT', 0.
        component_seed_identity=("PILOT", 0))
    # Set before to the result of parameter_hash(bundle.proposer_actor).
    before = parameter_hash(bundle.proposer_actor)
    # Set provider to the result of MAPPOBehaviorActionProvider().
    provider = MAPPOBehaviorActionProvider(bundle=bundle, sampling_seed=173)
    # Require provider.sampling_seed equals 173; otherwise raise AssertionError.
    assert provider.sampling_seed == 173
    # Require the result of parameter_hash(bundle.proposer_actor) equals before; otherwise raise AssertionError.
    assert parameter_hash(bundle.proposer_actor) == before
