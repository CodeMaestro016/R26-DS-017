"""Inference-only decentralized provider for the research demonstration."""

# Import replace from dataclasses for the operations below.
from dataclasses import replace
# Import hashlib for use in this module.
import hashlib

# Import SAMPLING_IDENTITY, reconstruct_demo_bundle from .demo_policy for the operations below.
from .demo_policy import SAMPLING_IDENTITY, reconstruct_demo_bundle
# Import MAPPOBehaviorActionProvider from .mappo_provider for the operations below.
from .mappo_provider import MAPPOBehaviorActionProvider
# Import parameter_hash from .rollout for the operations below.
from .rollout import parameter_hash


# Define DemonstrationMAPPOActionProvider to group the state and operations declared below.
# Base classes: MAPPOBehaviorActionProvider.
# Instances expose the attributes and methods implemented in this class.
class DemonstrationMAPPOActionProvider(MAPPOBehaviorActionProvider):
    # Set selection_rule to the text 'RESEARCH_PROTOTYPE_DEMONSTRATION_STOCHASTIC_MASKED_POLICY'.
    selection_rule = "RESEARCH_PROTOTYPE_DEMONSTRATION_STOCHASTIC_MASKED_POLICY"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input demo_policy_payload: the supplied demo policy payload.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, demo_policy_payload):
        # Set (bundle, hashes) to the result of reconstruct_demo_bundle(demo_policy_payload).
        bundle, hashes = reconstruct_demo_bundle(demo_policy_payload)
        # Set seed to the result of int.from_bytes(hashlib.sha256(repr(SAMPLING_IDENTITY).encode()).digest()
        # sliced by :8, the text 'big') modulo 2 raised to the power 31.
        seed = int.from_bytes(hashlib.sha256(
            # Supply the result of repr(SAMPLING_IDENTITY).encode() to hashlib.sha256.
            repr(SAMPLING_IDENTITY).encode()).digest()[:8], "big") % (2 ** 31)
        # Call super().__init__ with the supplied arguments.
        super().__init__(bundle=bundle, sampling_seed=seed,
                         # Supply runtime_critic_enabled as False.
                         runtime_critic_enabled=False)
        # Set self.demo_policy_identity to demo_policy_payload at 'demo_policy_identity'.
        self.demo_policy_identity = demo_policy_payload["demo_policy_identity"]
        # Set self.demo_parameter_hashes to hashes.
        self.demo_parameter_hashes = hashes
        # Set self.actor_route_truth_fields_consumed to 0.
        self.actor_route_truth_fields_consumed = 0
        # Set self.ego_local_observation_used to True.
        self.ego_local_observation_used = True
        # Set self.hard_action_mask_applied to True.
        self.hard_action_mask_applied = True
        # Set self.optimizer_instances to 0.
        self.optimizer_instances = 0
        # Set self.backward_calls to 0.
        self.backward_calls = 0
        # Set self.parameter_updates to 0.
        self.parameter_updates = 0

    # Sample using the inputs and processing steps below.
    # Input args: the supplied args.
    # Input kwargs: the supplied kwargs.
    # Output: the result of replace(sample).
    def _sample(self, *args, **kwargs):
        # Set sample to the result of super()._sample(the unpacked values from args).
        sample = super()._sample(*args, **kwargs)
        # Return the result of replace(sample) to the caller.
        return replace(sample, ppo_update_eligible=False,
                       # Supply provenance as a dictionary containing demonstration_inference_only.
                       provenance={**dict(sample.provenance),
                                   # Store True under 'demonstration_inference_only'.
                                   "demonstration_inference_only": True})

    # Coupled factor records using the inputs and processing steps below.
    # Input batch_id: the supplied batch id.
    # Input shape: the supplied shape.
    # Output: a tuple built from a lazy sequence of the result of replace(item) for item in the result of
    # super().coupled_factor_records(batch_id, shape).
    def coupled_factor_records(self, batch_id, shape):
        # Return a tuple built from a lazy sequence of the result of replace(item) for item in the result of
        # super().coupled_factor_records(batch_id, shape) to the caller.
        return tuple(replace(
            # Supply ppo_update_eligible as False.
            item, ppo_update_eligible=False,
            # Supply provenance as a dictionary containing demonstration_inference_only.
            provenance={**dict(item.provenance),
                        # Store True under 'demonstration_inference_only'.
                        "demonstration_inference_only": True})
            # Evaluate the result of super().coupled_factor_records(batch_id, shape) as part of the enclosing
            # expression.
            for item in super().coupled_factor_records(batch_id, shape))

    # Finalize episode using the inputs and processing steps below.
    # Input episode_id: the supplied episode id.
    # Input reward: the supplied reward.
    # Output: None.
    def finalize_episode(self, episode_id, reward):
        # Return/advantage and critic-target construction are training concerns.
        # Return None to the caller.
        return None

    # Inference parameter hashes using the inputs and processing steps below.
    # Output: a dictionary containing gnn, proposer, responder.
    def inference_parameter_hashes(self):
        # Return a dictionary containing gnn, proposer, responder to the caller.
        return {"gnn": parameter_hash(self.bundle.gnn),
                # Store the result of parameter_hash(self.bundle.proposer_actor) under 'proposer'.
                "proposer": parameter_hash(self.bundle.proposer_actor),
                # Store the result of parameter_hash(self.bundle.responder_actor) under 'responder'.
                "responder": parameter_hash(self.bundle.responder_actor)}
