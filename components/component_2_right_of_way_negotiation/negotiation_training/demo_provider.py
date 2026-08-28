"""Inference-only decentralized provider for the research demonstration."""

from dataclasses import replace
import hashlib

from .demo_policy import SAMPLING_IDENTITY, reconstruct_demo_bundle
from .mappo_provider import MAPPOBehaviorActionProvider
from .rollout import parameter_hash


class DemonstrationMAPPOActionProvider(MAPPOBehaviorActionProvider):
    selection_rule = "RESEARCH_PROTOTYPE_DEMONSTRATION_STOCHASTIC_MASKED_POLICY"

    def __init__(self, demo_policy_payload):
        bundle, hashes = reconstruct_demo_bundle(demo_policy_payload)
        seed = int.from_bytes(hashlib.sha256(
            repr(SAMPLING_IDENTITY).encode()).digest()[:8], "big") % (2 ** 31)
        super().__init__(bundle=bundle, sampling_seed=seed,
                         runtime_critic_enabled=False)
        self.demo_policy_identity = demo_policy_payload["demo_policy_identity"]
        self.demo_parameter_hashes = hashes
        self.actor_route_truth_fields_consumed = 0
        self.ego_local_observation_used = True
        self.hard_action_mask_applied = True
        self.optimizer_instances = 0
        self.backward_calls = 0
        self.parameter_updates = 0

    def _sample(self, *args, **kwargs):
        sample = super()._sample(*args, **kwargs)
        return replace(sample, ppo_update_eligible=False,
                       provenance={**dict(sample.provenance),
                                   "demonstration_inference_only": True})

    def coupled_factor_records(self, batch_id, shape):
        return tuple(replace(
            item, ppo_update_eligible=False,
            provenance={**dict(item.provenance),
                        "demonstration_inference_only": True})
            for item in super().coupled_factor_records(batch_id, shape))

    def finalize_episode(self, episode_id, reward):
        # Return/advantage and critic-target construction are training concerns.
        return None

    def inference_parameter_hashes(self):
        return {"gnn": parameter_hash(self.bundle.gnn),
                "proposer": parameter_hash(self.bundle.proposer_actor),
                "responder": parameter_hash(self.bundle.responder_actor)}
