"""First offline mechanical MAPPO PPO update over the frozen rollout."""

import hashlib
import json
import math
from pathlib import Path

import torch

from experimentation import ScenarioRole, build_design
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance)

from .adam_contract import (
    audit_parameter_membership, build_mechanical_adam_optimization_contract)
from .architecture_contract import build_mechanical_pilot_architecture_contract
from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
from .optimizer_contract import build_mechanical_pilot_configuration_audit
from .rollout import parameter_hash


ROLLOUT_PATH = Path("results/mappo_behavior_rollout.json")
UPDATE_PATH = Path("results/mappo_mechanical_ppo_update.json")


def _tuple(value):
    return tuple(_tuple(item) if isinstance(item, list) else item for item in value)


def _finite(*values):
    return all(torch.isfinite(value).all().item() for value in values)


def _gradient_diagnostics(module):
    gradients = tuple(parameter.grad.detach() for parameter in module.parameters()
                      if parameter.requires_grad and parameter.grad is not None)
    if not gradients:
        return {"parameter_tensor_count": 0, "nonzero_element_count": 0,
                "l2_norm": 0.0, "finite": True}
    squared = sum(torch.sum(value.to(torch.float64) ** 2) for value in gradients)
    return {
        "parameter_tensor_count": len(gradients),
        "nonzero_element_count": sum(int(torch.count_nonzero(value).item())
                                     for value in gradients),
        "l2_norm": float(torch.sqrt(squared).item()),
        "finite": all(torch.isfinite(value).all().item() for value in gradients),
    }


def _context(snapshot):
    provenance = PolicyDecisionProvenance(
        snapshot["provenance"]["local_observation_identity"],
        snapshot["provenance"]["local_graph_identity"],
        snapshot["provenance"]["local_mpnn_identity"],
        snapshot["provenance"]["semantic_subject_identity"],
        snapshot["provenance"]["hard_mask_identity"])
    protocol = snapshot["protocol_representation"]
    return NegotiationPolicyDecisionContext(
        snapshot["ego_id"], NegotiationDecisionRole(snapshot["decision_role"]),
        snapshot["counterparty_id"], tuple(snapshot["claim_identity"]),
        _tuple(snapshot["proposal_id"]) if snapshot["proposal_id"] else None,
        snapshot["provenance"]["local_observation_identity"],
        float(snapshot["source_timestamp"]),
        torch.tensor(snapshot["ego_embedding"], dtype=torch.float32),
        torch.tensor(snapshot["graph_embedding"], dtype=torch.float32),
        torch.tensor(snapshot["subject_representation"], dtype=torch.float32),
        (torch.tensor(protocol, dtype=torch.float32) if protocol is not None
         else None), tuple(snapshot["action_names"]),
        torch.tensor(snapshot["hard_action_mask"], dtype=torch.bool),
        provenance, snapshot["provenance"]["regulatory_profile"],
        snapshot["provenance"]["communication_model"])


class MechanicalMAPPOTrainer:
    def __init__(self, rollout_path=ROLLOUT_PATH, *, rollout_payload=None,
                 bundle=None, output_path=UPDATE_PATH):
        self.rollout_path = Path(rollout_path)
        if rollout_payload is None:
            self.rollout_bytes = self.rollout_path.read_bytes()
            self.rollout = json.loads(self.rollout_bytes)
        else:
            self.rollout = rollout_payload
            self.rollout_bytes = json.dumps(
                rollout_payload, sort_keys=True).encode()
        self.output_path = Path(output_path) if output_path is not None else None
        self.design = build_design()
        self.architecture = build_mechanical_pilot_architecture_contract()
        self.optimization = build_mechanical_adam_optimization_contract()
        self.configuration = build_mechanical_pilot_configuration_audit()
        self.bundle = bundle or build_mechanical_mappo_behavior_policy_bundle()
        self.actor_optimizer = None
        self.critic_optimizer = None
        self._validate_source()

    def _validate_source(self):
        source = self.rollout
        manifest = self.design["manifests"][ScenarioRole.TRAINING]
        identities = (
            source.get("checkpoint") == "STEP_5J_3B_3",
            source.get("status") == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
            source.get("step_5j_3b_4_readiness") ==
                "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
            _tuple(source["frozen_design_id"]) == self.design["freeze"].freeze_id,
            _tuple(source["architecture_contract_id"]) ==
                self.architecture.contract_id,
            _tuple(source["optimization_contract_id"]) ==
                self.optimization.contract_id,
            _tuple(source["training_manifest_id"]) == manifest.manifest_id,
            source.get("profiling_ppo_samples_reused") == 0,
        )
        if not all(identities):
            raise RuntimeError("MECHANICAL_PPO_ROLLOUT_IDENTITY_MISMATCH")
        factors = source["policy_factors"]
        critics = source["critic_samples"]
        if (len(factors) != source["total_ppo_sample_count"] or
                len(critics) != source["critic_sample_count"] or
                any(item["behavior_policy_source"] != "MAPPO_BEHAVIOR_POLICY"
                    or not item["ppo_update_eligible"] for item in factors) or
                any(not item["hard_action_mask"][item["selected_action_index"]]
                    for item in factors)):
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        actual_hashes = {"gnn": parameter_hash(self.bundle.gnn),
                         "proposer": parameter_hash(self.bundle.proposer_actor),
                         "responder": parameter_hash(self.bundle.responder_actor),
                         "critic": parameter_hash(self.bundle.centralized_critic)}
        if actual_hashes != source["initial_parameter_hashes"]:
            raise RuntimeError(
                "MECHANICAL_PPO_INITIAL_PARAMETER_IDENTITY_MISMATCH")
        if any(parameter.requires_grad for parameter in self.bundle.gnn.parameters()):
            raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")

    def _actor_quantities(self):
        log_probabilities, entropies = [], []
        for item in self.rollout["policy_factors"]:
            context = _context(item["actor_observation_snapshot"])
            if tuple(context.action_feasibility_mask.tolist()) != tuple(
                    item["hard_action_mask"]):
                raise RuntimeError("PPO_HARD_MASK_CHANGED_DURING_UPDATE")
            _, distribution = self.bundle.policy.distribution_for(context)
            log_probabilities.append(distribution.evaluate_action_index(
                item["selected_action_index"]))
            entropies.append(distribution.entropy)
        current = torch.stack(log_probabilities)
        old = torch.tensor([item["behavior_policy_log_probability"]
                            for item in self.rollout["policy_factors"]],
                           dtype=current.dtype)
        advantages = torch.tensor([item["advantage"] for item in
                                   self.rollout["policy_factors"]],
                                  dtype=current.dtype)
        ratios = torch.exp(current - old)
        epsilon = float(next(item.value for item in
            self.configuration.runtime_choices
            if item.choice_id == "ppo_clip_epsilon"))
        unclipped = ratios * advantages
        clipped = torch.clamp(ratios, 1.0 - epsilon, 1.0 + epsilon) * advantages
        surrogate = torch.minimum(unclipped, clipped)
        loss = -torch.mean(surrogate)
        entropy = torch.mean(torch.stack(entropies))
        if not _finite(current, ratios, unclipped, clipped, loss, entropy):
            raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
        return current, old, ratios, unclipped, clipped, loss, entropy, epsilon

    def _critic_quantities(self):
        inputs = torch.tensor([item["centralized_input"] for item in
                               self.rollout["critic_samples"]],
                              dtype=torch.float32)
        targets = torch.tensor([item["target_return"] for item in
                                self.rollout["critic_samples"]],
                               dtype=torch.float32)
        predictions = self.bundle.centralized_critic(inputs).squeeze(-1)
        errors = predictions - targets
        loss = torch.mean(errors ** 2)
        if not _finite(predictions, targets, errors, loss):
            raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
        return predictions, targets, errors, loss

    def _construct_optimizers(self):
        membership = audit_parameter_membership(
            self.bundle.proposer_actor, self.bundle.responder_actor,
            self.bundle.centralized_critic, self.bundle.gnn)
        if membership["duplicate_trainable_parameter_membership"]:
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        adam = dict(
            lr=self.optimization.learning_rate,
            betas=(self.optimization.beta1, self.optimization.beta2),
            eps=self.optimization.epsilon,
            weight_decay=self.optimization.weight_decay,
            amsgrad=self.optimization.amsgrad,
            foreach=False, maximize=False, capturable=False,
            differentiable=False, fused=False)
        actor_parameters = (list(self.bundle.proposer_actor.parameters()) +
                            list(self.bundle.responder_actor.parameters()))
        critic_parameters = list(self.bundle.centralized_critic.parameters())
        self.actor_optimizer = torch.optim.Adam(actor_parameters, **adam)
        self.critic_optimizer = torch.optim.Adam(critic_parameters, **adam)
        return membership, adam

    def run(self):
        factors = self.rollout["policy_factors"]
        behavior_logprob_hash = hashlib.sha256(repr(tuple(
            item["behavior_policy_log_probability"] for item in factors
        )).encode()).hexdigest()
        pre = self._actor_quantities()
        if not torch.equal(pre[2], torch.ones_like(pre[2])):
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        membership, adam = self._construct_optimizers()
        epochs = int(next(item.value for item in
            self.configuration.runtime_choices
            if item.choice_id == "ppo_update_epochs"))
        initial_hashes = dict(self.bundle.initial_parameter_hashes)
        diagnostics = []
        actor_steps = critic_steps = actor_backward = critic_backward = 0
        for epoch in range(1, epochs + 1):
            self.actor_optimizer.zero_grad(set_to_none=True)
            current, old, ratios, unclipped, clipped, actor_loss, entropy, epsilon = (
                self._actor_quantities())
            actor_loss.backward(); actor_backward += 1
            proposer_grad = _gradient_diagnostics(self.bundle.proposer_actor)
            responder_grad = _gradient_diagnostics(self.bundle.responder_actor)
            if not proposer_grad["finite"] or not responder_grad["finite"]:
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            self.actor_optimizer.step(); actor_steps += 1

            self.critic_optimizer.zero_grad(set_to_none=True)
            predictions, targets, errors, critic_loss = self._critic_quantities()
            critic_loss.backward(); critic_backward += 1
            critic_grad = _gradient_diagnostics(self.bundle.centralized_critic)
            if not critic_grad["finite"]:
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            self.critic_optimizer.step(); critic_steps += 1
            hashes = {"gnn": parameter_hash(self.bundle.gnn),
                      "proposer": parameter_hash(self.bundle.proposer_actor),
                      "responder": parameter_hash(self.bundle.responder_actor),
                      "critic": parameter_hash(self.bundle.centralized_critic)}
            if hashes["gnn"] != initial_hashes["gnn"]:
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            parameters = tuple(self.bundle.proposer_actor.parameters()) + tuple(
                self.bundle.responder_actor.parameters()) + tuple(
                self.bundle.centralized_critic.parameters())
            if not all(torch.isfinite(item).all().item() for item in parameters):
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            outside = int(torch.count_nonzero(
                (ratios < 1.0 - epsilon) | (ratios > 1.0 + epsilon)).item())
            diagnostics.append({
                "epoch": epoch, "actor_loss": float(actor_loss.item()),
                "critic_loss": float(critic_loss.item()),
                "ratio_minimum": float(ratios.min().item()),
                "ratio_mean": float(ratios.mean().item()),
                "ratio_maximum": float(ratios.max().item()),
                "clipped_factor_count": outside,
                "clipped_fraction": outside / len(factors),
                "mean_policy_entropy_diagnostic_only": float(entropy.item()),
                "critic_mean_prediction": float(predictions.mean().item()),
                "critic_mean_target": float(targets.mean().item()),
                "critic_mean_absolute_error": float(errors.abs().mean().item()),
                "proposer_gradient": proposer_grad,
                "responder_gradient": responder_grad,
                "critic_gradient": critic_grad,
                "parameter_hashes_after_epoch": hashes})

        final_hashes = diagnostics[-1]["parameter_hashes_after_epoch"]
        proposer_changed = final_hashes["proposer"] != initial_hashes["proposer"]
        responder_changed = final_hashes["responder"] != initial_hashes["responder"]
        critic_changed = final_hashes["critic"] != initial_hashes["critic"]
        if ((diagnostics[-1]["proposer_gradient"]["nonzero_element_count"] and
             not proposer_changed) or
            (diagnostics[-1]["responder_gradient"]["nonzero_element_count"] and
             not responder_changed)):
            raise RuntimeError("MECHANICAL_MAPPO_PARAMETER_UPDATE_NOT_OBSERVED")
        if diagnostics[-1]["critic_gradient"]["nonzero_element_count"] and not critic_changed:
            raise RuntimeError("MECHANICAL_MAPPO_CRITIC_UPDATE_NOT_OBSERVED")
        after_logprob_hash = hashlib.sha256(repr(tuple(
            item["behavior_policy_log_probability"] for item in factors
        )).encode()).hexdigest()
        if after_logprob_hash != behavior_logprob_hash:
            raise RuntimeError("PPO_BEHAVIOR_PROBABILITY_MUTATED")
        post_policy = ("POST_MECHANICAL_UPDATE_POLICY_V1",
                       final_hashes["proposer"], final_hashes["responder"])
        result = {
            "checkpoint": "STEP_5J_3B_4",
            "status": "FIRST_MECHANICAL_MAPPO_PPO_UPDATE_VALIDATED",
            "step_5j_3c_readiness":
                "READY_FOR_CONTROLLED_MAPPO_PILOT_EXPERIMENTS",
            "source_rollout_identity": self.rollout["behavior_rollout_identity"],
            "source_rollout_sha256": hashlib.sha256(
                self.rollout_bytes).hexdigest(),
            "frozen_design_id": self.rollout["frozen_design_id"],
            "architecture_contract_id": self.rollout["architecture_contract_id"],
            "optimization_contract_id": self.rollout["optimization_contract_id"],
            "training_manifest_id": self.rollout["training_manifest_id"],
            "sample_counts": {
                "actor": len(factors),
                "proposer": sum(x["decision_role"] == "PROPOSER" for x in factors),
                "responder": sum(x["decision_role"] == "RESPONDER" for x in factors),
                "critic": len(self.rollout["critic_samples"])},
            "optimizer_configuration": {**adam, "betas": list(adam["betas"]),
                "family": "ADAM", "instances": 2, "silent_defaults": 0},
            "ppo_configuration": {
                "full_batch": True, "epochs": epochs,
                "clip_epsilon": epsilon,
                "actor_aggregation": "PER_POLICY_FACTOR_EMPIRICAL_MEAN",
                "advantage": "RAW_MONTE_CARLO_ADVANTAGE",
                "entropy_term": "NONE", "gradient_clipping": "NONE",
                "value_loss_mixing_coefficient": "NONE_SEPARATE_OPTIMIZERS"},
            "parameter_membership": {key: list(value) if isinstance(value, tuple)
                                     else value for key, value in membership.items()},
            "initial_parameter_hashes": initial_hashes,
            "epoch_diagnostics": diagnostics,
            "final_parameter_hashes": final_hashes,
            "post_update_policy_identity": list(post_policy),
            "behavior_policy_parameter_identity_preserved": True,
            "initial_critic_identity": initial_hashes["critic"],
            "post_update_critic_identity": final_hashes["critic"],
            "actor_optimizer_steps": actor_steps,
            "critic_optimizer_steps": critic_steps,
            "total_optimizer_steps": actor_steps + critic_steps,
            "actor_backward_calls": actor_backward,
            "critic_backward_calls": critic_backward,
            "total_backward_calls": actor_backward + critic_backward,
            "gnn_optimizer_membership": 0,
            "gnn_hash_unchanged": final_hashes["gnn"] == initial_hashes["gnn"],
            "proposer_parameter_changed": proposer_changed,
            "responder_parameter_changed": responder_changed,
            "critic_parameter_changed": critic_changed,
            "behavior_log_probabilities_immutable": True,
            "actions_resampled": 0, "new_sumo_rollouts": 0,
            "new_training_environment_episodes": 0,
            "validation_runs": 0, "held_out_runs": 0,
            "profiling_ppo_samples_used": 0,
            "new_reward_terms": 0, "new_hyperparameter_candidates": 0,
            "new_selected_hyperparameters": 0,
            "final_training_budget_selected": False,
            "replication_count_selected": False,
            "main_learned_actions": 0,
            "mechanical_update_only": True, "final_model": False,
            "final_selection_eligible": False, "model_checkpoint_saved": False}
        if self.output_path is not None:
            self.output_path.write_text(json.dumps(result, indent=2),
                                        encoding="utf-8")
        return result
