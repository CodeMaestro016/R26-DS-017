"""First offline mechanical MAPPO PPO update over the frozen rollout."""

# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import math for use in this module.
import math
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import torch for use in this module.
import torch

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import NegotiationDecisionRole, NegotiationPolicyDecisionContext, PolicyDecisionProvenance from
# negotiation_learning.mappo_interface for the operations below.
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyDecisionContext,
    PolicyDecisionProvenance)

# Import audit_parameter_membership, build_mechanical_adam_optimization_contract from .adam_contract for the
# operations below.
from .adam_contract import (
    audit_parameter_membership, build_mechanical_adam_optimization_contract)
# Import build_mechanical_pilot_architecture_contract from .architecture_contract for the operations below.
from .architecture_contract import build_mechanical_pilot_architecture_contract
# Import build_mechanical_mappo_behavior_policy_bundle from .mappo_provider for the operations below.
from .mappo_provider import build_mechanical_mappo_behavior_policy_bundle
# Import build_mechanical_pilot_configuration_audit from .optimizer_contract for the operations below.
from .optimizer_contract import build_mechanical_pilot_configuration_audit
# Import parameter_hash from .rollout for the operations below.
from .rollout import parameter_hash


# Set ROLLOUT_PATH to the result of Path(the text 'results/mappo_behavior_rollout.json').
ROLLOUT_PATH = Path("results/mappo_behavior_rollout.json")
# Set UPDATE_PATH to the result of Path(the text 'results/mappo_mechanical_ppo_update.json').
UPDATE_PATH = Path("results/mappo_mechanical_ppo_update.json")


# Tuple using the inputs and processing steps below.
# Input value: the supplied value.
# Output: a tuple built from a lazy sequence of the result of _tuple(item) when whether item has type list,
# otherwise item for item in value.
def _tuple(value):
    # Return a tuple built from a lazy sequence of the result of _tuple(item) when whether item has type list,
    # otherwise item for item in value to the caller.
    return tuple(_tuple(item) if isinstance(item, list) else item for item in value)


# Finite using the inputs and processing steps below.
# Input values: the supplied values.
# Output: whether every item is true in a lazy sequence of the result of torch.isfinite(value).all().item() for
# value in values.
def _finite(*values):
    # Return whether every item is true in a lazy sequence of the result of torch.isfinite(value).all().item() for
    # value in values to the caller.
    return all(torch.isfinite(value).all().item() for value in values)


# Gradient diagnostics using the inputs and processing steps below.
# Input module: the supplied module.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _gradient_diagnostics(module):
    # Set gradients to a tuple built from a lazy sequence of parameter.grad detached from automatic
    # differentiation for parameter in the result of module.parameters(); retain entries satisfying
    # parameter.requires_grad and parameter.grad is a different object from None.
    gradients = tuple(parameter.grad.detach() for parameter in module.parameters()
                      # Evaluate parameter.requires_grad and parameter.grad is a different object from None as
                      # part of the enclosing expression.
                      if parameter.requires_grad and parameter.grad is not None)
    # Run this branch when the negation of gradients.
    if not gradients:
        # Return a dictionary containing parameter_tensor_count, nonzero_element_count, l2_norm, finite to the
        # caller.
        return {"parameter_tensor_count": 0, "nonzero_element_count": 0,
                # Store 0.0 under 'l2_norm'.
                # Store True under 'finite'.
                "l2_norm": 0.0, "finite": True}
    # Set squared to the sum of a lazy sequence of the result of torch.sum(value.to(torch.float64) raised to the
    # power 2) for value in gradients.
    squared = sum(torch.sum(value.to(torch.float64) ** 2) for value in gradients)
    # Return a dictionary containing parameter_tensor_count, nonzero_element_count, l2_norm, finite to the caller.
    return {
        # Store the number of entries in gradients under 'parameter_tensor_count'.
        "parameter_tensor_count": len(gradients),
        # Store the sum of a lazy sequence of an integer built from the result of
        # torch.count_nonzero(value).item() for value in gradients under 'nonzero_element_count'.
        "nonzero_element_count": sum(int(torch.count_nonzero(value).item())
                                     # Evaluate gradients as part of the enclosing expression.
                                     for value in gradients),
        # Store a floating-point number built from the result of torch.sqrt(squared).item() under 'l2_norm'.
        "l2_norm": float(torch.sqrt(squared).item()),
        # Store whether every item is true in a lazy sequence of the result of torch.isfinite(value).all().item()
        # for value in gradients under 'finite'.
        "finite": all(torch.isfinite(value).all().item() for value in gradients),
    }


# Context using the inputs and processing steps below.
# Input snapshot: the supplied snapshot.
# Output: the result of NegotiationPolicyDecisionContext(snapshot at 'ego_id', the result of
# NegotiationDecisionRole(snapshot at 'decision_role'),...).
def _context(snapshot):
    # Set provenance to the result of PolicyDecisionProvenance(snapshot['provenance'] at
    # 'local_observation_identity', snapshot['provenance'] at...).
    provenance = PolicyDecisionProvenance(
        # Supply snapshot['provenance'] at 'local_observation_identity' to PolicyDecisionProvenance.
        snapshot["provenance"]["local_observation_identity"],
        # Supply snapshot['provenance'] at 'local_graph_identity' to PolicyDecisionProvenance.
        snapshot["provenance"]["local_graph_identity"],
        # Supply snapshot['provenance'] at 'local_mpnn_identity' to PolicyDecisionProvenance.
        snapshot["provenance"]["local_mpnn_identity"],
        # Supply snapshot['provenance'] at 'semantic_subject_identity' to PolicyDecisionProvenance.
        snapshot["provenance"]["semantic_subject_identity"],
        # Supply snapshot['provenance'] at 'hard_mask_identity' to PolicyDecisionProvenance.
        snapshot["provenance"]["hard_mask_identity"])
    # Set protocol to snapshot at 'protocol_representation'.
    protocol = snapshot["protocol_representation"]
    # Return the result of NegotiationPolicyDecisionContext(snapshot at 'ego_id', the result of
    # NegotiationDecisionRole(snapshot at 'decision_role'),...) to the caller.
    return NegotiationPolicyDecisionContext(
        # Supply the result of NegotiationDecisionRole(snapshot at 'decision_role') to
        # NegotiationPolicyDecisionContext.
        snapshot["ego_id"], NegotiationDecisionRole(snapshot["decision_role"]),
        # Supply a tuple built from snapshot at 'claim_identity' to NegotiationPolicyDecisionContext.
        snapshot["counterparty_id"], tuple(snapshot["claim_identity"]),
        # Supply the result of _tuple(snapshot at 'proposal_id') when snapshot at 'proposal_id', otherwise None to
        # NegotiationPolicyDecisionContext.
        _tuple(snapshot["proposal_id"]) if snapshot["proposal_id"] else None,
        # Supply snapshot['provenance'] at 'local_observation_identity' to NegotiationPolicyDecisionContext.
        snapshot["provenance"]["local_observation_identity"],
        # Supply a floating-point number built from snapshot at 'source_timestamp' to
        # NegotiationPolicyDecisionContext.
        float(snapshot["source_timestamp"]),
        # Supply dtype as torch.float32.
        torch.tensor(snapshot["ego_embedding"], dtype=torch.float32),
        # Supply dtype as torch.float32.
        torch.tensor(snapshot["graph_embedding"], dtype=torch.float32),
        # Supply dtype as torch.float32.
        torch.tensor(snapshot["subject_representation"], dtype=torch.float32),
        # Supply dtype as torch.float32.
        (torch.tensor(protocol, dtype=torch.float32) if protocol is not None
         # Supply a tuple built from snapshot at 'action_names' to NegotiationPolicyDecisionContext.
         else None), tuple(snapshot["action_names"]),
        # Supply dtype as torch.bool.
        torch.tensor(snapshot["hard_action_mask"], dtype=torch.bool),
        # Supply snapshot['provenance'] at 'regulatory_profile' to NegotiationPolicyDecisionContext.
        provenance, snapshot["provenance"]["regulatory_profile"],
        # Supply snapshot['provenance'] at 'communication_model' to NegotiationPolicyDecisionContext.
        snapshot["provenance"]["communication_model"])


# Define MechanicalMAPPOTrainer to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class MechanicalMAPPOTrainer:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input rollout_path: the supplied rollout path.
    # Input rollout_payload: the supplied rollout payload.
    # Input bundle: the supplied bundle.
    # Input output_path: the supplied output path.
    # Input configuration: the supplied configuration.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, rollout_path=ROLLOUT_PATH, *, rollout_payload=None,
                 # Declare bundle, output_path, configuration as input parameters.
                 bundle=None, output_path=UPDATE_PATH, configuration=None):
        # Set self.rollout_path to the result of Path(rollout_path).
        self.rollout_path = Path(rollout_path)
        # Run this branch when rollout_payload is the same object as None.
        if rollout_payload is None:
            # Set self.rollout_bytes to the bytes read from self.rollout_path.
            self.rollout_bytes = self.rollout_path.read_bytes()
            # Set self.rollout to the decoded data produced by json.loads from self.rollout_bytes.
            self.rollout = json.loads(self.rollout_bytes)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set self.rollout to rollout_payload.
            self.rollout = rollout_payload
            # Set self.rollout_bytes to the result of json.dumps(rollout_payload, sort_keys=True).encode().
            self.rollout_bytes = json.dumps(
                # Supply sort_keys as True.
                rollout_payload, sort_keys=True).encode()
        # Set self.output_path to the result of Path(output_path) when output_path is a different object from
        # None, otherwise None.
        self.output_path = Path(output_path) if output_path is not None else None
        # Set self.design to the result of build_design().
        self.design = build_design()
        # Set self.architecture to the result of build_mechanical_pilot_architecture_contract().
        self.architecture = build_mechanical_pilot_architecture_contract()
        # Set self.optimization to the result of build_mechanical_adam_optimization_contract().
        self.optimization = build_mechanical_adam_optimization_contract()
        # Set self.configuration to configuration or the result of build_mechanical_pilot_configuration_audit().
        self.configuration = (
            # Evaluate configuration or the result of build_mechanical_pilot_configuration_audit() as part of the
            # enclosing expression.
            configuration or build_mechanical_pilot_configuration_audit()
        )
        # Set self.bundle to bundle or the result of build_mechanical_mappo_behavior_policy_bundle().
        self.bundle = bundle or build_mechanical_mappo_behavior_policy_bundle()
        # Set self.actor_optimizer to None.
        self.actor_optimizer = None
        # Set self.critic_optimizer to None.
        self.critic_optimizer = None
        # Call self._validate_source with the supplied arguments.
        self._validate_source()

    # Validate source using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _validate_source(self):
        # Set source to self.rollout.
        source = self.rollout
        # Set manifest to self.design['manifests'] at ScenarioRole.TRAINING.
        manifest = self.design["manifests"][ScenarioRole.TRAINING]
        # Set identities to a tuple containing 'checkpoint' from source; use None if absent equals the text
        # 'STEP_5J_3B_3', 'status' from source; use...
        identities = (
            # Include 'checkpoint' from source; use None if absent equals the text 'STEP_5J_3B_3' in this tuple.
            source.get("checkpoint") == "STEP_5J_3B_3",
            # Include 'status' from source; use None if absent equals the text
            # 'REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED' in this tuple.
            source.get("status") == "REAL_MAPPO_BEHAVIOR_ROLLOUT_VALIDATED",
            # Include 'step_5j_3b_4_readiness' from source; use None if absent equals the text
            # 'READY_FOR_FIRST_MECHANICAL_PPO_UPDATE' in this tuple.
            source.get("step_5j_3b_4_readiness") ==
                "READY_FOR_FIRST_MECHANICAL_PPO_UPDATE",
            # Include the result of _tuple(source at 'frozen_design_id') equals self.design['freeze'].freeze_id in
            # this tuple.
            _tuple(source["frozen_design_id"]) == self.design["freeze"].freeze_id,
            # Include the result of _tuple(source at 'architecture_contract_id') equals
            # self.architecture.contract_id in this tuple.
            _tuple(source["architecture_contract_id"]) ==
                # Evaluate self.architecture.contract_id as part of the enclosing expression.
                self.architecture.contract_id,
            # Include the result of _tuple(source at 'optimization_contract_id') equals
            # self.optimization.contract_id in this tuple.
            _tuple(source["optimization_contract_id"]) ==
                # Evaluate self.optimization.contract_id as part of the enclosing expression.
                self.optimization.contract_id,
            # Include the result of _tuple(source at 'training_manifest_id') equals manifest.manifest_id in this
            # tuple.
            _tuple(source["training_manifest_id"]) == manifest.manifest_id,
            # Include 'profiling_ppo_samples_reused' from source; use None if absent equals 0 in this tuple.
            source.get("profiling_ppo_samples_reused") == 0,
        )
        # Run this branch when the negation of whether every item is true in identities.
        if not all(identities):
            # Raise RuntimeError with the text 'MECHANICAL_PPO_ROLLOUT_IDENTITY_MISMATCH' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_ROLLOUT_IDENTITY_MISMATCH")
        # Set factors to source at 'policy_factors'.
        factors = source["policy_factors"]
        # Set critics to source at 'critic_samples'.
        critics = source["critic_samples"]
        # Run this branch when the number of entries in factors differs from source at 'total_ppo_sample_count' or
        # the number of entries in critics differs from source at 'critic_sample_count' or whether any item is
        # true in a lazy sequence of item['behavior_policy_source'] != 'MAPPO_BEHAVIOR_POLICY' or not
        # item['ppo_update_eligible'] for item in factors or whether any item is true in a lazy sequence of the
        # negation of item['hard_action_mask'][item['selected_action_index']] for item in factors.
        if (len(factors) != source["total_ppo_sample_count"] or
                # Evaluate the number of entries in critics differs from source at 'critic_sample_count' as part
                # of the enclosing expression.
                len(critics) != source["critic_sample_count"] or
                # Evaluate whether any item is true in a lazy sequence of item['behavior_policy_source'] differs
                # from 'MAPPO_BEHAVIOR_POLICY' or the negation of item['ppo_update_eligible'] for item in factors
                # as part of the enclosing expression.
                any(item["behavior_policy_source"] != "MAPPO_BEHAVIOR_POLICY"
                    # Evaluate the negation of item at 'ppo_update_eligible' as part of the enclosing expression.
                    or not item["ppo_update_eligible"] for item in factors) or
                # Evaluate whether any item is true in a lazy sequence of the negation of item['hard_action_mask']
                # at item['selected_action_index'] for item in factors as part of the enclosing expression.
                any(not item["hard_action_mask"][item["selected_action_index"]]
                    # Evaluate factors as part of the enclosing expression.
                    for item in factors)):
            # Raise RuntimeError with the text 'MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        # Set actual_hashes to a dictionary containing gnn, proposer, responder, critic.
        actual_hashes = {"gnn": parameter_hash(self.bundle.gnn),
                         # Store the result of parameter_hash(self.bundle.proposer_actor) under 'proposer'.
                         "proposer": parameter_hash(self.bundle.proposer_actor),
                         # Store the result of parameter_hash(self.bundle.responder_actor) under 'responder'.
                         "responder": parameter_hash(self.bundle.responder_actor),
                         # Store the result of parameter_hash(self.bundle.centralized_critic) under 'critic'.
                         "critic": parameter_hash(self.bundle.centralized_critic)}
        # Run this branch when actual_hashes differs from source at 'initial_parameter_hashes'.
        if actual_hashes != source["initial_parameter_hashes"]:
            # Raise RuntimeError with the text 'MECHANICAL_PPO_INITIAL_PARAMETER_IDENTITY_MISMATCH' to stop this
            # execution path.
            raise RuntimeError(
                "MECHANICAL_PPO_INITIAL_PARAMETER_IDENTITY_MISMATCH")
        # Run this branch when whether any item is true in a lazy sequence of parameter.requires_grad for
        # parameter in the result of self.bundle.gnn.parameters().
        if any(parameter.requires_grad for parameter in self.bundle.gnn.parameters()):
            # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution path.
            raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")

    # Actor quantities using the inputs and processing steps below.
    # Output: a tuple containing current, old, ratios, unclipped, clipped, loss, entropy, epsilon.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _actor_quantities(self):
        # Set (log_probabilities, entropies) to a tuple containing an empty list, an empty list.
        log_probabilities, entropies = [], []
        # Iterate over self.rollout at 'policy_factors', binding each item to item.
        for item in self.rollout["policy_factors"]:
            # Set context to the result of _context(item at 'actor_observation_snapshot').
            context = _context(item["actor_observation_snapshot"])
            # Run this branch when a tuple built from the result of context.action_feasibility_mask.tolist()
            # differs from a tuple built from item at 'hard_action_mask'.
            if tuple(context.action_feasibility_mask.tolist()) != tuple(
                    # Supply item at 'hard_action_mask' to tuple.
                    item["hard_action_mask"]):
                # Raise RuntimeError with the text 'PPO_HARD_MASK_CHANGED_DURING_UPDATE' to stop this execution
                # path.
                raise RuntimeError("PPO_HARD_MASK_CHANGED_DURING_UPDATE")
            # Set (_, distribution) to the result of self.bundle.policy.distribution_for(context).
            _, distribution = self.bundle.policy.distribution_for(context)
            # Append the result of distribution.evaluate_action_index(item at 'selected_action_index') to
            # log_probabilities.
            log_probabilities.append(distribution.evaluate_action_index(
                # Supply item at 'selected_action_index' to distribution.evaluate_action_index.
                item["selected_action_index"]))
            # Append distribution.entropy to entropies.
            entropies.append(distribution.entropy)
        # Set current to the result of torch.stack(log_probabilities).
        current = torch.stack(log_probabilities)
        # Set old to a tensor built from a list of item at 'behavior_policy_log_probability' for item in
        # self.rollout at 'policy_factors'.
        old = torch.tensor([item["behavior_policy_log_probability"]
                            # Evaluate self.rollout at 'policy_factors' as part of the enclosing expression.
                            for item in self.rollout["policy_factors"]],
                           # Supply dtype as current.dtype.
                           dtype=current.dtype)
        # Set advantages to a tensor built from a list of item at 'advantage' for item in self.rollout at
        # 'policy_factors'.
        advantages = torch.tensor([item["advantage"] for item in
                                   # Evaluate self.rollout at 'policy_factors' as part of the enclosing
                                   # expression.
                                   self.rollout["policy_factors"]],
                                  # Supply dtype as current.dtype.
                                  dtype=current.dtype)
        # Set ratios to the exponential of current minus old.
        ratios = torch.exp(current - old)
        # Set epsilon to a floating-point number built from the next item from a lazy sequence of item.value for
        # item in self.configuration.runtime_choices; retain entries satisfying item.choice_id equals
        # 'ppo_clip_epsilon'.
        epsilon = float(next(item.value for item in
            # Evaluate self.configuration.runtime_choices as part of the enclosing expression.
            self.configuration.runtime_choices
            # Evaluate item.choice_id equals the text 'ppo_clip_epsilon' as part of the enclosing expression.
            if item.choice_id == "ppo_clip_epsilon"))
        # Set unclipped to ratios multiplied by advantages.
        unclipped = ratios * advantages
        # Set clipped to ratios bounded by the supplied limits multiplied by advantages.
        clipped = torch.clamp(ratios, 1.0 - epsilon, 1.0 + epsilon) * advantages
        # Set surrogate to the result of torch.minimum(unclipped, clipped).
        surrogate = torch.minimum(unclipped, clipped)
        # Set loss to the negative of the result of torch.mean(surrogate).
        loss = -torch.mean(surrogate)
        # Set entropy to the result of torch.mean(the result of torch.stack(entropies)).
        entropy = torch.mean(torch.stack(entropies))
        # Run this branch when the negation of the result of _finite(current, ratios, unclipped, clipped, loss,
        # entropy).
        if not _finite(current, ratios, unclipped, clipped, loss, entropy):
            # Raise RuntimeError with the text 'MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
        # Return a tuple containing current, old, ratios, unclipped, clipped, loss, entropy, epsilon to the
        # caller.
        return current, old, ratios, unclipped, clipped, loss, entropy, epsilon

    # Critic quantities using the inputs and processing steps below.
    # Output: a tuple containing predictions, targets, errors, loss.
    # Processing: select branches using the stated conditions.
    def _critic_quantities(self):
        # Set inputs to a tensor built from a list of item at 'centralized_input' for item in self.rollout at
        # 'critic_samples'.
        inputs = torch.tensor([item["centralized_input"] for item in
                               # Evaluate self.rollout at 'critic_samples' as part of the enclosing expression.
                               self.rollout["critic_samples"]],
                              # Supply dtype as torch.float32.
                              dtype=torch.float32)
        # Set targets to a tensor built from a list of item at 'target_return' for item in self.rollout at
        # 'critic_samples'.
        targets = torch.tensor([item["target_return"] for item in
                                # Evaluate self.rollout at 'critic_samples' as part of the enclosing expression.
                                self.rollout["critic_samples"]],
                               # Supply dtype as torch.float32.
                               dtype=torch.float32)
        # Set predictions to the result of self.bundle.centralized_critic(inputs).squeeze(the negative of 1).
        predictions = self.bundle.centralized_critic(inputs).squeeze(-1)
        # Set errors to predictions minus targets.
        errors = predictions - targets
        # Set loss to the result of torch.mean(errors raised to the power 2).
        loss = torch.mean(errors ** 2)
        # Run this branch when the negation of the result of _finite(predictions, targets, errors, loss).
        if not _finite(predictions, targets, errors, loss):
            # Raise RuntimeError with the text 'MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
        # Return a tuple containing predictions, targets, errors, loss to the caller.
        return predictions, targets, errors, loss

    # Construct optimizers using the inputs and processing steps below.
    # Output: a tuple containing membership, adam.
    # Processing: select branches using the stated conditions.
    def _construct_optimizers(self):
        # Set membership to the result of audit_parameter_membership(self.bundle.proposer_actor,
        # self.bundle.responder_actor, self.bundle.centralized_critic,...).
        membership = audit_parameter_membership(
            # Supply self.bundle.responder_actor to audit_parameter_membership.
            self.bundle.proposer_actor, self.bundle.responder_actor,
            # Supply self.bundle.centralized_critic to audit_parameter_membership.
            self.bundle.centralized_critic, self.bundle.gnn)
        # Run this branch when membership at 'duplicate_trainable_parameter_membership'.
        if membership["duplicate_trainable_parameter_membership"]:
            # Raise RuntimeError with the text 'MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        # Set adam to a dictionary built from the supplied values.
        adam = dict(
            # Supply lr as self.optimization.learning_rate.
            lr=self.optimization.learning_rate,
            # Supply betas as a tuple containing self.optimization.beta1, self.optimization.beta2.
            betas=(self.optimization.beta1, self.optimization.beta2),
            # Supply eps as self.optimization.epsilon.
            eps=self.optimization.epsilon,
            # Supply weight_decay as self.optimization.weight_decay.
            weight_decay=self.optimization.weight_decay,
            # Supply amsgrad as self.optimization.amsgrad.
            amsgrad=self.optimization.amsgrad,
            # Supply foreach as False.
            # Supply maximize as False.
            # Supply capturable as False.
            foreach=False, maximize=False, capturable=False,
            # Supply differentiable as False.
            # Supply fused as False.
            differentiable=False, fused=False)
        # Set actor_parameters to a list built from the result of self.bundle.proposer_actor.parameters() plus a
        # list built from the result of self.bundle.responder_actor.parameters().
        actor_parameters = (list(self.bundle.proposer_actor.parameters()) +
                            # Evaluate a list built from the result of self.bundle.responder_actor.parameters() as
                            # part of the enclosing expression.
                            list(self.bundle.responder_actor.parameters()))
        # Set critic_parameters to a list built from the result of self.bundle.centralized_critic.parameters().
        critic_parameters = list(self.bundle.centralized_critic.parameters())
        # Set self.actor_optimizer to the result of torch.optim.Adam(actor_parameters).
        self.actor_optimizer = torch.optim.Adam(actor_parameters, **adam)
        # Set self.critic_optimizer to the result of torch.optim.Adam(critic_parameters).
        self.critic_optimizer = torch.optim.Adam(critic_parameters, **adam)
        # Return a tuple containing membership, adam to the caller.
        return membership, adam

    # Run using the inputs and processing steps below.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def run(self):
        # Set factors to self.rollout at 'policy_factors'.
        factors = self.rollout["policy_factors"]
        # Set behavior_logprob_hash to the result of
        # hashlib.sha256(repr(tuple((item['behavior_policy_log_probability'] for item in...().
        behavior_logprob_hash = hashlib.sha256(repr(tuple(
            # Evaluate item at 'behavior_policy_log_probability' as part of the enclosing expression.
            item["behavior_policy_log_probability"] for item in factors
        )).encode()).hexdigest()
        # Set pre to the result of self._actor_quantities().
        pre = self._actor_quantities()
        # Run this branch when the negation of the result of torch.equal(pre at 2, the result of
        # torch.ones_like(pre at 2)).
        if not torch.equal(pre[2], torch.ones_like(pre[2])):
            # Raise RuntimeError with the text 'MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID' to stop this execution
            # path.
            raise RuntimeError("MECHANICAL_PPO_SAMPLE_CONTRACT_INVALID")
        # Set (membership, adam) to the result of self._construct_optimizers().
        membership, adam = self._construct_optimizers()
        # Set epochs to an integer built from the next item from a lazy sequence of item.value for item in
        # self.configuration.runtime_choices; retain entries satisfying item.choice_id equals 'ppo_update_epochs'.
        epochs = int(next(item.value for item in
            # Evaluate self.configuration.runtime_choices as part of the enclosing expression.
            self.configuration.runtime_choices
            # Evaluate item.choice_id equals the text 'ppo_update_epochs' as part of the enclosing expression.
            if item.choice_id == "ppo_update_epochs"))
        # Each sequential update begins at the policy that generated its own
        # on-policy rollout, not necessarily at the bundle's State-0 weights.
        # Set initial_hashes to a dictionary built from self.rollout at 'initial_parameter_hashes'.
        initial_hashes = dict(self.rollout["initial_parameter_hashes"])
        # Set diagnostics to an empty list.
        diagnostics = []
        # Set actor_steps and critic_steps and actor_backward and critic_backward to 0.
        actor_steps = critic_steps = actor_backward = critic_backward = 0
        # Iterate over the integer range defined by 1, epochs plus 1, binding each item to epoch.
        for epoch in range(1, epochs + 1):
            # Clear accumulated gradients in self.actor_optimizer.
            self.actor_optimizer.zero_grad(set_to_none=True)
            # Set (current, old, ratios, unclipped, clipped, actor_loss, entropy, epsilon) to the result of
            # self._actor_quantities().
            current, old, ratios, unclipped, clipped, actor_loss, entropy, epsilon = (
                # Evaluate the result of self._actor_quantities() as part of the enclosing expression.
                self._actor_quantities())
            # Backpropagate gradients from actor_loss.
            # Update actor_backward to its current value plus 1.
            actor_loss.backward(); actor_backward += 1
            # Set proposer_grad to the result of _gradient_diagnostics(self.bundle.proposer_actor).
            proposer_grad = _gradient_diagnostics(self.bundle.proposer_actor)
            # Set responder_grad to the result of _gradient_diagnostics(self.bundle.responder_actor).
            responder_grad = _gradient_diagnostics(self.bundle.responder_actor)
            # Run this branch when the negation of proposer_grad at 'finite' or the negation of responder_grad at
            # 'finite'.
            if not proposer_grad["finite"] or not responder_grad["finite"]:
                # Raise RuntimeError with the text 'MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY' to stop this
                # execution path.
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            # Advance self.actor_optimizer using its configured step operation.
            # Update actor_steps to its current value plus 1.
            self.actor_optimizer.step(); actor_steps += 1

            # Clear accumulated gradients in self.critic_optimizer.
            self.critic_optimizer.zero_grad(set_to_none=True)
            # Set (predictions, targets, errors, critic_loss) to the result of self._critic_quantities().
            predictions, targets, errors, critic_loss = self._critic_quantities()
            # Backpropagate gradients from critic_loss.
            # Update critic_backward to its current value plus 1.
            critic_loss.backward(); critic_backward += 1
            # Set critic_grad to the result of _gradient_diagnostics(self.bundle.centralized_critic).
            critic_grad = _gradient_diagnostics(self.bundle.centralized_critic)
            # Run this branch when the negation of critic_grad at 'finite'.
            if not critic_grad["finite"]:
                # Raise RuntimeError with the text 'MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY' to stop this
                # execution path.
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            # Advance self.critic_optimizer using its configured step operation.
            # Update critic_steps to its current value plus 1.
            self.critic_optimizer.step(); critic_steps += 1
            # Set hashes to a dictionary containing gnn, proposer, responder, critic.
            hashes = {"gnn": parameter_hash(self.bundle.gnn),
                      # Store the result of parameter_hash(self.bundle.proposer_actor) under 'proposer'.
                      "proposer": parameter_hash(self.bundle.proposer_actor),
                      # Store the result of parameter_hash(self.bundle.responder_actor) under 'responder'.
                      "responder": parameter_hash(self.bundle.responder_actor),
                      # Store the result of parameter_hash(self.bundle.centralized_critic) under 'critic'.
                      "critic": parameter_hash(self.bundle.centralized_critic)}
            # Run this branch when hashes at 'gnn' differs from initial_hashes at 'gnn'.
            if hashes["gnn"] != initial_hashes["gnn"]:
                # Raise RuntimeError with the text 'FROZEN_GNN_PARAMETER_CHANGED' to stop this execution path.
                raise RuntimeError("FROZEN_GNN_PARAMETER_CHANGED")
            # Set parameters to a tuple built from the result of self.bundle.proposer_actor.parameters() plus a
            # tuple built from the result of self.bundle.responder_actor.parameters() plus a tuple built from the
            # result of self.bundle.centralized_critic.parameters().
            parameters = tuple(self.bundle.proposer_actor.parameters()) + tuple(
                # Evaluate a tuple built from the result of self.bundle.centralized_critic.parameters() as part of
                # the enclosing expression.
                self.bundle.responder_actor.parameters()) + tuple(
                # Supply the result of self.bundle.centralized_critic.parameters() to tuple.
                self.bundle.centralized_critic.parameters())
            # Run this branch when the negation of whether every item is true in a lazy sequence of the result of
            # torch.isfinite(item).all().item() for item in parameters.
            if not all(torch.isfinite(item).all().item() for item in parameters):
                # Raise RuntimeError with the text 'MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY' to stop this
                # execution path.
                raise RuntimeError("MECHANICAL_PPO_NONFINITE_TRAINING_QUANTITY")
            # Set outside to an integer built from the result of torch.count_nonzero((ratios < 1.0 - epsilon) |
            # (ratios > 1.0 + epsilon)).item().
            outside = int(torch.count_nonzero(
                # Supply ratios is less than 1.0 minus epsilon combined with ratios is greater than 1.0 plus
                # epsilon to torch.count_nonzero.
                (ratios < 1.0 - epsilon) | (ratios > 1.0 + epsilon)).item())
            # Append a dictionary containing epoch, actor_loss, critic_loss, ratio_minimum, ratio_mean,
            # ratio_maximum,... to diagnostics.
            diagnostics.append({
                # Store epoch under 'epoch'.
                # Store a floating-point number built from the result of actor_loss.item() under 'actor_loss'.
                "epoch": epoch, "actor_loss": float(actor_loss.item()),
                # Store a floating-point number built from the result of critic_loss.item() under 'critic_loss'.
                "critic_loss": float(critic_loss.item()),
                # Store a floating-point number built from the result of ratios.min().item() under
                # 'ratio_minimum'.
                "ratio_minimum": float(ratios.min().item()),
                # Store a floating-point number built from the result of ratios.mean().item() under 'ratio_mean'.
                "ratio_mean": float(ratios.mean().item()),
                # Store a floating-point number built from the result of ratios.max().item() under
                # 'ratio_maximum'.
                "ratio_maximum": float(ratios.max().item()),
                # Store outside under 'clipped_factor_count'.
                "clipped_factor_count": outside,
                # Store outside divided by the number of entries in factors under 'clipped_fraction'.
                "clipped_fraction": outside / len(factors),
                # Store a floating-point number built from the result of entropy.item() under
                # 'mean_policy_entropy_diagnostic_only'.
                "mean_policy_entropy_diagnostic_only": float(entropy.item()),
                # Store a floating-point number built from the result of predictions.mean().item() under
                # 'critic_mean_prediction'.
                "critic_mean_prediction": float(predictions.mean().item()),
                # Store a floating-point number built from the result of targets.mean().item() under
                # 'critic_mean_target'.
                "critic_mean_target": float(targets.mean().item()),
                # Store a floating-point number built from the result of errors.abs().mean().item() under
                # 'critic_mean_absolute_error'.
                "critic_mean_absolute_error": float(errors.abs().mean().item()),
                # Store proposer_grad under 'proposer_gradient'.
                "proposer_gradient": proposer_grad,
                # Store responder_grad under 'responder_gradient'.
                "responder_gradient": responder_grad,
                # Store critic_grad under 'critic_gradient'.
                "critic_gradient": critic_grad,
                # Store hashes under 'parameter_hashes_after_epoch'.
                "parameter_hashes_after_epoch": hashes})

        # Set final_hashes to diagnostics[-1] at 'parameter_hashes_after_epoch'.
        final_hashes = diagnostics[-1]["parameter_hashes_after_epoch"]
        # Set proposer_changed to final_hashes at 'proposer' differs from initial_hashes at 'proposer'.
        proposer_changed = final_hashes["proposer"] != initial_hashes["proposer"]
        # Set responder_changed to final_hashes at 'responder' differs from initial_hashes at 'responder'.
        responder_changed = final_hashes["responder"] != initial_hashes["responder"]
        # Set critic_changed to final_hashes at 'critic' differs from initial_hashes at 'critic'.
        critic_changed = final_hashes["critic"] != initial_hashes["critic"]
        # Run this branch when diagnostics[-1]['proposer_gradient'] at 'nonzero_element_count' and the negation of
        # proposer_changed or diagnostics[-1]['responder_gradient'] at 'nonzero_element_count' and the negation of
        # responder_changed.
        if ((diagnostics[-1]["proposer_gradient"]["nonzero_element_count"] and
             # Evaluate the negation of proposer_changed as part of the enclosing expression.
             not proposer_changed) or
            # Evaluate diagnostics[-1]['responder_gradient'] at 'nonzero_element_count' and the negation of
            # responder_changed as part of the enclosing expression.
            (diagnostics[-1]["responder_gradient"]["nonzero_element_count"] and
             # Evaluate the negation of responder_changed as part of the enclosing expression.
             not responder_changed)):
            # Raise RuntimeError with the text 'MECHANICAL_MAPPO_PARAMETER_UPDATE_NOT_OBSERVED' to stop this
            # execution path.
            raise RuntimeError("MECHANICAL_MAPPO_PARAMETER_UPDATE_NOT_OBSERVED")
        # Run this branch when diagnostics[-1]['critic_gradient'] at 'nonzero_element_count' and the negation of
        # critic_changed.
        if diagnostics[-1]["critic_gradient"]["nonzero_element_count"] and not critic_changed:
            # Raise RuntimeError with the text 'MECHANICAL_MAPPO_CRITIC_UPDATE_NOT_OBSERVED' to stop this
            # execution path.
            raise RuntimeError("MECHANICAL_MAPPO_CRITIC_UPDATE_NOT_OBSERVED")
        # Set after_logprob_hash to the result of
        # hashlib.sha256(repr(tuple((item['behavior_policy_log_probability'] for item in...().
        after_logprob_hash = hashlib.sha256(repr(tuple(
            # Evaluate item at 'behavior_policy_log_probability' as part of the enclosing expression.
            item["behavior_policy_log_probability"] for item in factors
        )).encode()).hexdigest()
        # Run this branch when after_logprob_hash differs from behavior_logprob_hash.
        if after_logprob_hash != behavior_logprob_hash:
            # Raise RuntimeError with the text 'PPO_BEHAVIOR_PROBABILITY_MUTATED' to stop this execution path.
            raise RuntimeError("PPO_BEHAVIOR_PROBABILITY_MUTATED")
        # Set post_policy to a tuple containing the text 'POST_MECHANICAL_UPDATE_POLICY_V1', final_hashes at
        # 'proposer', final_hashes at 'responder'.
        post_policy = ("POST_MECHANICAL_UPDATE_POLICY_V1",
                       # Include final_hashes at 'responder' in this tuple.
                       final_hashes["proposer"], final_hashes["responder"])
        # Set result to a dictionary containing checkpoint, status, step_5j_3c_readiness,
        # source_rollout_identity,...
        result = {
            "checkpoint": "STEP_5J_3B_4",
            "status": "FIRST_MECHANICAL_MAPPO_PPO_UPDATE_VALIDATED",
            "step_5j_3c_readiness":
                "READY_FOR_CONTROLLED_MAPPO_PILOT_EXPERIMENTS",
            # Store self.rollout at 'behavior_rollout_identity' under 'source_rollout_identity'.
            "source_rollout_identity": self.rollout["behavior_rollout_identity"],
            # Store the hexadecimal digest from hashlib.sha256(self.rollout_bytes) under 'source_rollout_sha256'.
            "source_rollout_sha256": hashlib.sha256(
                # Supply self.rollout_bytes to hashlib.sha256.
                self.rollout_bytes).hexdigest(),
            # Store self.rollout at 'frozen_design_id' under 'frozen_design_id'.
            "frozen_design_id": self.rollout["frozen_design_id"],
            # Store self.rollout at 'architecture_contract_id' under 'architecture_contract_id'.
            "architecture_contract_id": self.rollout["architecture_contract_id"],
            # Store self.rollout at 'optimization_contract_id' under 'optimization_contract_id'.
            "optimization_contract_id": self.rollout["optimization_contract_id"],
            # Store self.rollout at 'training_manifest_id' under 'training_manifest_id'.
            "training_manifest_id": self.rollout["training_manifest_id"],
            # Store a dictionary containing actor, proposer, responder, critic under 'sample_counts'.
            "sample_counts": {
                # Store the number of entries in factors under 'actor'.
                "actor": len(factors),
                # Store the sum of a lazy sequence of x at 'decision_role' equals the text 'PROPOSER' for x in
                # factors under 'proposer'.
                "proposer": sum(x["decision_role"] == "PROPOSER" for x in factors),
                # Store the sum of a lazy sequence of x at 'decision_role' equals the text 'RESPONDER' for x in
                # factors under 'responder'.
                "responder": sum(x["decision_role"] == "RESPONDER" for x in factors),
                # Store the number of entries in self.rollout at 'critic_samples' under 'critic'.
                "critic": len(self.rollout["critic_samples"])},
            # Store a dictionary containing betas, family, instances, silent_defaults under
            # 'optimizer_configuration'.
            # Store a list built from adam at 'betas' under 'betas'.
            "optimizer_configuration": {**adam, "betas": list(adam["betas"]),
                # Store the text 'ADAM' under 'family'.
                # Store 2 under 'instances'.
                # Store 0 under 'silent_defaults'.
                "family": "ADAM", "instances": 2, "silent_defaults": 0},
            # Store a dictionary containing full_batch, epochs, clip_epsilon, actor_aggregation, advantage,
            # entropy_term,... under 'ppo_configuration'.
            "ppo_configuration": {
                # Store True under 'full_batch'.
                # Store epochs under 'epochs'.
                "full_batch": True, "epochs": epochs,
                # Store epsilon under 'clip_epsilon'.
                "clip_epsilon": epsilon,
                "actor_aggregation": "PER_POLICY_FACTOR_EMPIRICAL_MEAN",
                "advantage": "RAW_MONTE_CARLO_ADVANTAGE",
                "entropy_term": "NONE", "gradient_clipping": "NONE",
                "value_loss_mixing_coefficient": "NONE_SEPARATE_OPTIMIZERS"},
            # Store a dictionary of key mapped to a list built from value when whether value has type tuple,
            # otherwise value for (key, value) in key/value pairs from membership under 'parameter_membership'.
            "parameter_membership": {key: list(value) if isinstance(value, tuple)
                                     # Evaluate key/value pairs from membership as part of the enclosing
                                     # expression.
                                     else value for key, value in membership.items()},
            # Store initial_hashes under 'initial_parameter_hashes'.
            "initial_parameter_hashes": initial_hashes,
            # Store diagnostics under 'epoch_diagnostics'.
            "epoch_diagnostics": diagnostics,
            # Store final_hashes under 'final_parameter_hashes'.
            "final_parameter_hashes": final_hashes,
            # Store a list built from post_policy under 'post_update_policy_identity'.
            "post_update_policy_identity": list(post_policy),
            # Store True under 'behavior_policy_parameter_identity_preserved'.
            "behavior_policy_parameter_identity_preserved": True,
            # Store initial_hashes at 'critic' under 'initial_critic_identity'.
            "initial_critic_identity": initial_hashes["critic"],
            # Store final_hashes at 'critic' under 'post_update_critic_identity'.
            "post_update_critic_identity": final_hashes["critic"],
            # Store actor_steps under 'actor_optimizer_steps'.
            "actor_optimizer_steps": actor_steps,
            # Store critic_steps under 'critic_optimizer_steps'.
            "critic_optimizer_steps": critic_steps,
            # Store actor_steps plus critic_steps under 'total_optimizer_steps'.
            "total_optimizer_steps": actor_steps + critic_steps,
            # Store actor_backward under 'actor_backward_calls'.
            "actor_backward_calls": actor_backward,
            # Store critic_backward under 'critic_backward_calls'.
            "critic_backward_calls": critic_backward,
            # Store actor_backward plus critic_backward under 'total_backward_calls'.
            "total_backward_calls": actor_backward + critic_backward,
            # Store 0 under 'gnn_optimizer_membership'.
            "gnn_optimizer_membership": 0,
            # Store final_hashes at 'gnn' equals initial_hashes at 'gnn' under 'gnn_hash_unchanged'.
            "gnn_hash_unchanged": final_hashes["gnn"] == initial_hashes["gnn"],
            # Store proposer_changed under 'proposer_parameter_changed'.
            "proposer_parameter_changed": proposer_changed,
            # Store responder_changed under 'responder_parameter_changed'.
            "responder_parameter_changed": responder_changed,
            # Store critic_changed under 'critic_parameter_changed'.
            "critic_parameter_changed": critic_changed,
            # Store True under 'behavior_log_probabilities_immutable'.
            "behavior_log_probabilities_immutable": True,
            # Store 0 under 'actions_resampled'.
            # Store 0 under 'new_sumo_rollouts'.
            "actions_resampled": 0, "new_sumo_rollouts": 0,
            # Store 0 under 'new_training_environment_episodes'.
            "new_training_environment_episodes": 0,
            # Store 0 under 'validation_runs'.
            # Store 0 under 'held_out_runs'.
            "validation_runs": 0, "held_out_runs": 0,
            # Store 0 under 'profiling_ppo_samples_used'.
            "profiling_ppo_samples_used": 0,
            # Store 0 under 'new_reward_terms'.
            # Store 0 under 'new_hyperparameter_candidates'.
            "new_reward_terms": 0, "new_hyperparameter_candidates": 0,
            # Store 0 under 'new_selected_hyperparameters'.
            "new_selected_hyperparameters": 0,
            # Store False under 'final_training_budget_selected'.
            "final_training_budget_selected": False,
            # Store False under 'replication_count_selected'.
            "replication_count_selected": False,
            # Store 0 under 'main_learned_actions'.
            "main_learned_actions": 0,
            # Store True under 'mechanical_update_only'.
            # Store False under 'final_model'.
            "mechanical_update_only": True, "final_model": False,
            # Store False under 'final_selection_eligible'.
            # Store False under 'model_checkpoint_saved'.
            "final_selection_eligible": False, "model_checkpoint_saved": False}
        # Run this branch when self.output_path is a different object from None.
        if self.output_path is not None:
            # Write the supplied text to self.output_path.
            self.output_path.write_text(json.dumps(result, indent=2),
                                        # Supply encoding as the text 'utf-8'.
                                        encoding="utf-8")
        # Return result to the caller.
        return result
