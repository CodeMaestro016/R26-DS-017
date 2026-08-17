"""Step 5J.3B.2 immutable Adam and critic-objective contract.

This module audits optimizer semantics.  It deliberately never constructs an
optimizer and never performs differentiation or a parameter update.
"""

import hashlib
import inspect
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from experimentation import build_design

from .architecture_contract import build_mechanical_pilot_architecture_contract


ORIGINAL_ADAM_MECHANICAL_REFERENCE = "ORIGINAL_ADAM_MECHANICAL_REFERENCE"
ADAM_PAPER_SOURCE = (
    "Kingma & Ba (2014), Adam: A Method for Stochastic Optimization, "
    "arXiv:1412.6980"
)


@dataclass(frozen=True)
class AdamArgumentAudit:
    name: str
    installed_default: str
    explicit_mechanical_value: str
    classification: str
    semantics: str


@dataclass(frozen=True)
class MechanicalAdamOptimizationContract:
    contract_id: tuple
    frozen_design_id: tuple
    architecture_contract_id: tuple
    optimizer_family: str
    learning_rate: float
    learning_rate_evidence_id: tuple
    beta1: float
    beta1_source: str
    beta2: float
    beta2_source: str
    epsilon: float
    epsilon_source: str
    weight_decay: float
    weight_decay_semantics: str
    amsgrad: bool
    amsgrad_semantics: str
    actor_parameter_grouping: Tuple[str, ...]
    critic_parameter_grouping: Tuple[str, ...]
    frozen_parameter_exclusions: Tuple[str, ...]
    critic_loss_form: str
    critic_loss_reduction: str
    critic_sample_unit: str
    value_loss_mixing_coefficient: str
    adam_argument_audit: Tuple[AdamArgumentAudit, ...]
    torch_version: str
    mechanical_reference_only: bool
    project_selected: bool
    final_selection_eligible: bool
    unresolved_optimizer_fields: Tuple[str, ...]
    provenance: Mapping

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


def _installed_adam_signature():
    import torch

    return torch.__version__, inspect.signature(torch.optim.Adam)


def _argument_audit(signature):
    settings = {
        "params": ("ACTOR_OR_CRITIC_EXACT_PARAMETER_SET", "ALGORITHM_PARAMETER",
                   "Two disjoint logical optimizers; frozen GNN excluded."),
        "lr": ("0.0005", "ALGORITHM_PARAMETER",
               "Frozen Step 5J.2 provisional learning-rate candidate."),
        "betas": ("(0.9, 0.999)", "ALGORITHM_PARAMETER",
                  "Original Adam mechanical reference."),
        "eps": ("1e-08", "ALGORITHM_PARAMETER",
                "Original Adam numerical-stability reference."),
        "weight_decay": ("0", "ALGORITHM_PARAMETER",
                         "No additional regularization."),
        "amsgrad": ("False", "ALGORITHM_PARAMETER",
                    "Plain Adam, not the later AMSGrad variant."),
        "foreach": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                    "Explicit CPU single-tensor implementation path."),
        "maximize": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                     "The defined actor and critic losses are minimized."),
        "capturable": ("False", "NOT_APPLICABLE_CPU_MODE",
                       "No accelerator graph capture in the CPU pilot."),
        "differentiable": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                           "No higher-order differentiation through steps."),
        "fused": ("False", "NOT_APPLICABLE_CPU_MODE",
                  "Explicit non-fused CPU mechanical implementation."),
        "decoupled_weight_decay": (
            "False", "ALGORITHM_PARAMETER", "Plain Adam, never AdamW."),
    }
    audited = []
    for name, parameter in signature.parameters.items():
        value, classification, semantics = settings[name]
        audited.append(AdamArgumentAudit(
            name, repr(parameter.default), value, classification, semantics))
    supported = set(signature.parameters)
    if "decoupled_weight_decay" not in supported:
        audited.append(AdamArgumentAudit(
            "decoupled_weight_decay", "NOT_SUPPORTED_INSTALLED_API", "False",
            "NOT_APPLICABLE_CPU_MODE",
            "PyTorch 2.6.0 Adam has no such argument; optimizer family remains plain Adam."))
    unknown = supported - set(settings)
    if unknown:
        raise ValueError(f"UNRESOLVED_ADAM_SIGNATURE_ARGUMENTS:{sorted(unknown)}")
    return tuple(audited)


def build_mechanical_adam_optimization_contract(
        profile_path="results/coupled_environment_profile.json"):
    design = build_design()
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    assignments = {item.choice_id: item for item in
                   design["provisional"].assignments}
    learning_rate = assignments["learning_rate"]
    optimizer_family = assignments["optimizer_family"]
    if optimizer_family.candidate_value_or_method != "ADAM":
        raise ValueError("FROZEN_OPTIMIZER_FAMILY_NOT_ADAM")
    torch_version, signature = _installed_adam_signature()
    arguments = _argument_audit(signature)
    identity = (
        design["freeze"].freeze_id, architecture.contract_id,
        learning_rate.candidate_evidence_id,
        optimizer_family.candidate_evidence_id, 0.9, 0.999, 1e-8,
        "PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION", False,
        "TWO_DISJOINT_ACTOR_AND_CRITIC_PARAMETER_SETS_FROZEN_GNN_EXCLUDED",
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR",
        tuple((item.name, item.explicit_mechanical_value) for item in arguments),
    )
    return MechanicalAdamOptimizationContract(
        ("MECHANICAL_ADAM_OPTIMIZATION_CONTRACT_V1",
         hashlib.sha256(repr(identity).encode()).hexdigest()),
        design["freeze"].freeze_id, architecture.contract_id, "ADAM",
        learning_rate.candidate_value_or_method,
        learning_rate.candidate_evidence_id,
        0.9, ADAM_PAPER_SOURCE, 0.999, ADAM_PAPER_SOURCE, 1e-8,
        ADAM_PAPER_SOURCE, 0.0,
        "PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION", False,
        "ORIGINAL_ADAM_NOT_AMSGRAD_VARIANT",
        ("proposer_actor.*", "responder_actor.*"),
        ("centralized_critic.*",), ("frozen_gnn.*",),
        "PURE_SQUARED_MONTE_CARLO_RETURN_ERROR",
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR",
        "CENTRALIZED_JOINT_DECISION_BATCH",
        "NOT_APPLICABLE_SEPARATE_OPTIMIZERS", arguments, torch_version,
        True, False, False, (),
        {"beta_classification": ORIGINAL_ADAM_MECHANICAL_REFERENCE,
         "epsilon_classification": ORIGINAL_ADAM_MECHANICAL_REFERENCE,
         "learning_rate_classification": "FROZEN_PILOT_CANDIDATE",
         "optimizer_instances": 0, "backward_calls": 0,
         "parameter_updates": 0, "role_specific_optimizer_weights": 0,
         "silent_adam_defaults": 0, "frozen_design_mutated": False,
         "claimed_optimal": False})


def audit_parameter_membership(proposer_actor, responder_actor,
                               centralized_critic, frozen_gnn):
    """Return exact names and reject duplicated optimizer membership."""
    groups = {
        "proposer": tuple(f"proposer_actor.{name}" for name, _ in
                          proposer_actor.named_parameters()),
        "responder": tuple(f"responder_actor.{name}" for name, _ in
                           responder_actor.named_parameters()),
        "critic": tuple(f"centralized_critic.{name}" for name, _ in
                        centralized_critic.named_parameters()),
        "gnn": tuple(f"frozen_gnn.{name}" for name, _ in
                     frozen_gnn.named_parameters()),
    }
    actor = set(groups["proposer"]) | set(groups["responder"])
    critic, gnn = set(groups["critic"]), set(groups["gnn"])
    if actor & critic or actor & gnn or critic & gnn:
        raise ValueError("DUPLICATE_OPTIMIZER_PARAMETER_MEMBERSHIP")
    groups["duplicate_trainable_parameter_membership"] = 0
    return MappingProxyType(groups)


def joint_batch_critic_mean_squared_error(predicted_values, returns):
    """Explicit empirical mean over centralized joint decision batches."""
    import torch

    if predicted_values.shape != returns.shape:
        raise ValueError("CRITIC_PREDICTION_RETURN_SHAPE_MISMATCH")
    if predicted_values.ndim != 1 or predicted_values.numel() < 1:
        raise ValueError("JOINT_DECISION_BATCH_VECTOR_REQUIRED")
    return torch.mean((predicted_values - returns) ** 2)
