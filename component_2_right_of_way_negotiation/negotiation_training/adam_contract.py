"""Step 5J.3B.2 immutable Adam and critic-objective contract.

This module audits optimizer semantics.  It deliberately never constructs an
optimizer and never performs differentiation or a parameter update.
"""

# Import hashlib for use in this module.
import hashlib
# Import inspect for use in this module.
import inspect
# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Mapping, Tuple from typing for the operations below.
from typing import Mapping, Tuple

# Import build_design from experimentation for the operations below.
from experimentation import build_design

# Import build_mechanical_pilot_architecture_contract from .architecture_contract for the operations below.
from .architecture_contract import build_mechanical_pilot_architecture_contract


# Set ORIGINAL_ADAM_MECHANICAL_REFERENCE to the text 'ORIGINAL_ADAM_MECHANICAL_REFERENCE'.
ORIGINAL_ADAM_MECHANICAL_REFERENCE = "ORIGINAL_ADAM_MECHANICAL_REFERENCE"
# Set ADAM_PAPER_SOURCE to the text 'Kingma & Ba (2014), Adam: A Method for Stochastic...'.
ADAM_PAPER_SOURCE = (
    "Kingma & Ba (2014), Adam: A Method for Stochastic Optimization, "
    "arXiv:1412.6980"
)


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define AdamArgumentAudit to group the state and operations declared below.
# Declared fields: name, installed_default, explicit_mechanical_value, classification, semantics.
# Construction and attribute behavior follow the declared decorators and base classes.
class AdamArgumentAudit:
    # Declare name as str for this data structure.
    name: str
    # Declare installed_default as str for this data structure.
    installed_default: str
    # Declare explicit_mechanical_value as str for this data structure.
    explicit_mechanical_value: str
    # Declare classification as str for this data structure.
    classification: str
    # Declare semantics as str for this data structure.
    semantics: str


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MechanicalAdamOptimizationContract to group the state and operations declared below.
# Declared fields: contract_id, frozen_design_id, architecture_contract_id, optimizer_family, learning_rate,
# learning_rate_evidence_id, beta1, beta1_source, beta2, beta2_source, epsilon, epsilon_source, weight_decay,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MechanicalAdamOptimizationContract:
    # Declare contract_id as tuple for this data structure.
    contract_id: tuple
    # Declare frozen_design_id as tuple for this data structure.
    frozen_design_id: tuple
    # Declare architecture_contract_id as tuple for this data structure.
    architecture_contract_id: tuple
    # Declare optimizer_family as str for this data structure.
    optimizer_family: str
    # Declare learning_rate as float for this data structure.
    learning_rate: float
    # Declare learning_rate_evidence_id as tuple for this data structure.
    learning_rate_evidence_id: tuple
    # Declare beta1 as float for this data structure.
    beta1: float
    # Declare beta1_source as str for this data structure.
    beta1_source: str
    # Declare beta2 as float for this data structure.
    beta2: float
    # Declare beta2_source as str for this data structure.
    beta2_source: str
    # Declare epsilon as float for this data structure.
    epsilon: float
    # Declare epsilon_source as str for this data structure.
    epsilon_source: str
    # Declare weight_decay as float for this data structure.
    weight_decay: float
    # Declare weight_decay_semantics as str for this data structure.
    weight_decay_semantics: str
    # Declare amsgrad as bool for this data structure.
    amsgrad: bool
    # Declare amsgrad_semantics as str for this data structure.
    amsgrad_semantics: str
    # Declare actor_parameter_grouping as Tuple[str, ...] for this data structure.
    actor_parameter_grouping: Tuple[str, ...]
    # Declare critic_parameter_grouping as Tuple[str, ...] for this data structure.
    critic_parameter_grouping: Tuple[str, ...]
    # Declare frozen_parameter_exclusions as Tuple[str, ...] for this data structure.
    frozen_parameter_exclusions: Tuple[str, ...]
    # Declare critic_loss_form as str for this data structure.
    critic_loss_form: str
    # Declare critic_loss_reduction as str for this data structure.
    critic_loss_reduction: str
    # Declare critic_sample_unit as str for this data structure.
    critic_sample_unit: str
    # Declare value_loss_mixing_coefficient as str for this data structure.
    value_loss_mixing_coefficient: str
    # Declare adam_argument_audit as Tuple[AdamArgumentAudit, ...] for this data structure.
    adam_argument_audit: Tuple[AdamArgumentAudit, ...]
    # Declare torch_version as str for this data structure.
    torch_version: str
    # Declare mechanical_reference_only as bool for this data structure.
    mechanical_reference_only: bool
    # Declare project_selected as bool for this data structure.
    project_selected: bool
    # Declare final_selection_eligible as bool for this data structure.
    final_selection_eligible: bool
    # Declare unresolved_optimizer_fields as Tuple[str, ...] for this data structure.
    unresolved_optimizer_fields: Tuple[str, ...]
    # Declare provenance as Mapping for this data structure.
    provenance: Mapping

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Installed adam signature using the inputs and processing steps below.
# Output: a tuple containing torch.__version__, the result of inspect.signature(torch.optim.Adam).
def _installed_adam_signature():
    # Import torch for use in this module.
    import torch

    # Return a tuple containing torch.__version__, the result of inspect.signature(torch.optim.Adam) to the
    # caller.
    return torch.__version__, inspect.signature(torch.optim.Adam)


# Argument audit using the inputs and processing steps below.
# Input signature: the supplied signature.
# Output: a tuple built from audited.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def _argument_audit(signature):
    # Set settings to a dictionary containing params, lr, betas, eps, weight_decay, amsgrad, foreach, maximize,
    # capturable,...
    settings = {
        # Store a tuple containing the text 'ACTOR_OR_CRITIC_EXACT_PARAMETER_SET', the text 'ALGORITHM_PARAMETER',
        # the text 'Two disjoint... under 'params'.
        "params": ("ACTOR_OR_CRITIC_EXACT_PARAMETER_SET", "ALGORITHM_PARAMETER",
                   "Two disjoint logical optimizers; frozen GNN excluded."),
        # Store a tuple containing the text '0.0005', the text 'ALGORITHM_PARAMETER', the text 'Frozen Step 5J.2
        # provisional learning-rate... under 'lr'.
        "lr": ("0.0005", "ALGORITHM_PARAMETER",
               "Frozen Step 5J.2 provisional learning-rate candidate."),
        # Store a tuple containing the text '(0.9, 0.999)', the text 'ALGORITHM_PARAMETER', the text 'Original
        # Adam mechanical reference.' under 'betas'.
        "betas": ("(0.9, 0.999)", "ALGORITHM_PARAMETER",
                  "Original Adam mechanical reference."),
        # Store a tuple containing the text '1e-08', the text 'ALGORITHM_PARAMETER', the text 'Original Adam
        # numerical-stability reference.' under 'eps'.
        "eps": ("1e-08", "ALGORITHM_PARAMETER",
                "Original Adam numerical-stability reference."),
        # Store a tuple containing the text '0', the text 'ALGORITHM_PARAMETER', the text 'No additional
        # regularization.' under 'weight_decay'.
        "weight_decay": ("0", "ALGORITHM_PARAMETER",
                         "No additional regularization."),
        # Store a tuple containing the text 'False', the text 'ALGORITHM_PARAMETER', the text 'Plain Adam, not the
        # later AMSGrad variant.' under 'amsgrad'.
        "amsgrad": ("False", "ALGORITHM_PARAMETER",
                    "Plain Adam, not the later AMSGrad variant."),
        # Store a tuple containing the text 'False', the text 'MECHANICAL_IMPLEMENTATION_MODE', the text 'Explicit
        # CPU single-tensor... under 'foreach'.
        "foreach": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                    "Explicit CPU single-tensor implementation path."),
        # Store a tuple containing the text 'False', the text 'MECHANICAL_IMPLEMENTATION_MODE', the text 'The
        # defined actor and critic losses... under 'maximize'.
        "maximize": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                     "The defined actor and critic losses are minimized."),
        # Store a tuple containing the text 'False', the text 'NOT_APPLICABLE_CPU_MODE', the text 'No accelerator
        # graph capture in the CPU... under 'capturable'.
        "capturable": ("False", "NOT_APPLICABLE_CPU_MODE",
                       "No accelerator graph capture in the CPU pilot."),
        # Store a tuple containing the text 'False', the text 'MECHANICAL_IMPLEMENTATION_MODE', the text 'No
        # higher-order differentiation... under 'differentiable'.
        "differentiable": ("False", "MECHANICAL_IMPLEMENTATION_MODE",
                           "No higher-order differentiation through steps."),
        # Store a tuple containing the text 'False', the text 'NOT_APPLICABLE_CPU_MODE', the text 'Explicit
        # non-fused CPU mechanical... under 'fused'.
        "fused": ("False", "NOT_APPLICABLE_CPU_MODE",
                  "Explicit non-fused CPU mechanical implementation."),
        # Store a tuple containing the text 'False', the text 'ALGORITHM_PARAMETER', the text 'Plain Adam, never
        # AdamW.' under 'decoupled_weight_decay'.
        "decoupled_weight_decay": (
            "False", "ALGORITHM_PARAMETER", "Plain Adam, never AdamW."),
    }
    # Set audited to an empty list.
    audited = []
    # Iterate over key/value pairs from signature.parameters, binding each item to (name, parameter).
    for name, parameter in signature.parameters.items():
        # Set (value, classification, semantics) to settings at name.
        value, classification, semantics = settings[name]
        # Append the result of AdamArgumentAudit(name, the result of repr(parameter.default), value,
        # classification, semantics) to audited.
        audited.append(AdamArgumentAudit(
            # Supply the result of repr(parameter.default) to AdamArgumentAudit.
            name, repr(parameter.default), value, classification, semantics))
    # Set supported to a set built from signature.parameters.
    supported = set(signature.parameters)
    # Run this branch when the text 'decoupled_weight_decay' does not belong to supported.
    if "decoupled_weight_decay" not in supported:
        # Append the result of AdamArgumentAudit(the text 'decoupled_weight_decay', the text
        # 'NOT_SUPPORTED_INSTALLED_API', the text 'False', the...) to audited.
        audited.append(AdamArgumentAudit(
            "decoupled_weight_decay", "NOT_SUPPORTED_INSTALLED_API", "False",
            "NOT_APPLICABLE_CPU_MODE",
            "PyTorch 2.6.0 Adam has no such argument; optimizer family remains plain Adam."))
    # Set unknown to supported minus a set built from settings.
    unknown = supported - set(settings)
    # Run this branch when unknown.
    if unknown:
        # Raise ValueError with formatted text built from the embedded values to stop this execution path.
        raise ValueError(f"UNRESOLVED_ADAM_SIGNATURE_ARGUMENTS:{sorted(unknown)}")
    # Return a tuple built from audited to the caller.
    return tuple(audited)


# Build mechanical adam optimization contract using the inputs and processing steps below.
# Input profile_path: the supplied profile path.
# Output: the result of MechanicalAdamOptimizationContract(a tuple containing the text
# 'MECHANICAL_ADAM_OPTIMIZATION_CONTRACT_V1', the hexadecimal digest...).
# Processing: select branches using the stated conditions.
def build_mechanical_adam_optimization_contract(
        # Declare profile_path as input parameter.
        profile_path="results/coupled_environment_profile.json"):
    # Set design to the result of build_design().
    design = build_design()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract(profile_path).
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    # Set assignments to a dictionary of item.choice_id mapped to item for item in
    # design['provisional'].assignments.
    assignments = {item.choice_id: item for item in
                   # Evaluate design['provisional'].assignments as part of the enclosing expression.
                   design["provisional"].assignments}
    # Set learning_rate to assignments at 'learning_rate'.
    learning_rate = assignments["learning_rate"]
    # Set optimizer_family to assignments at 'optimizer_family'.
    optimizer_family = assignments["optimizer_family"]
    # Run this branch when optimizer_family.candidate_value_or_method differs from the text 'ADAM'.
    if optimizer_family.candidate_value_or_method != "ADAM":
        # Raise ValueError with the text 'FROZEN_OPTIMIZER_FAMILY_NOT_ADAM' to stop this execution path.
        raise ValueError("FROZEN_OPTIMIZER_FAMILY_NOT_ADAM")
    # Set (torch_version, signature) to the result of _installed_adam_signature().
    torch_version, signature = _installed_adam_signature()
    # Set arguments to the result of _argument_audit(signature).
    arguments = _argument_audit(signature)
    # Set identity to a tuple containing design['freeze'].freeze_id, architecture.contract_id,
    # learning_rate.candidate_evidence_id,...
    identity = (
        # Include design['freeze'].freeze_id in this tuple.
        design["freeze"].freeze_id, architecture.contract_id,
        # Include learning_rate.candidate_evidence_id in this tuple.
        learning_rate.candidate_evidence_id,
        # Include optimizer_family.candidate_evidence_id in this tuple.
        optimizer_family.candidate_evidence_id, 0.9, 0.999, 1e-8,
        # Supply the text 'PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION' to the enclosing expression.
        "PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION", False,
        "TWO_DISJOINT_ACTOR_AND_CRITIC_PARAMETER_SETS_FROZEN_GNN_EXCLUDED",
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR",
        # Include a tuple built from a lazy sequence of a tuple containing item.name,
        # item.explicit_mechanical_value for item in arguments in this tuple.
        tuple((item.name, item.explicit_mechanical_value) for item in arguments),
    )
    # Return the result of MechanicalAdamOptimizationContract(a tuple containing the text
    # 'MECHANICAL_ADAM_OPTIMIZATION_CONTRACT_V1', the hexadecimal digest...) to the caller.
    return MechanicalAdamOptimizationContract(
        # Supply a tuple containing the text 'MECHANICAL_ADAM_OPTIMIZATION_CONTRACT_V1', the hexadecimal digest
        # from... to MechanicalAdamOptimizationContract.
        ("MECHANICAL_ADAM_OPTIMIZATION_CONTRACT_V1",
         # Include the hexadecimal digest from hashlib.sha256(repr(identity).encode()) in this tuple.
         hashlib.sha256(repr(identity).encode()).hexdigest()),
        # Supply design['freeze'].freeze_id to MechanicalAdamOptimizationContract.
        design["freeze"].freeze_id, architecture.contract_id, "ADAM",
        # Supply learning_rate.candidate_value_or_method to MechanicalAdamOptimizationContract.
        learning_rate.candidate_value_or_method,
        # Supply learning_rate.candidate_evidence_id to MechanicalAdamOptimizationContract.
        learning_rate.candidate_evidence_id,
        # Supply ADAM_PAPER_SOURCE to MechanicalAdamOptimizationContract.
        0.9, ADAM_PAPER_SOURCE, 0.999, ADAM_PAPER_SOURCE, 1e-8,
        # Supply ADAM_PAPER_SOURCE to MechanicalAdamOptimizationContract.
        ADAM_PAPER_SOURCE, 0.0,
        # Supply the text 'PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION' to the enclosing expression.
        "PLAIN_ADAM_NO_ADDITIONAL_WEIGHT_REGULARIZATION", False,
        "ORIGINAL_ADAM_NOT_AMSGRAD_VARIANT",
        # Supply a tuple containing the text 'proposer_actor.*', the text 'responder_actor.*' to
        # MechanicalAdamOptimizationContract.
        ("proposer_actor.*", "responder_actor.*"),
        # Supply a tuple containing the text 'centralized_critic.*' to MechanicalAdamOptimizationContract.
        ("centralized_critic.*",), ("frozen_gnn.*",),
        "PURE_SQUARED_MONTE_CARLO_RETURN_ERROR",
        "PER_JOINT_DECISION_BATCH_EMPIRICAL_MEAN_SQUARED_ERROR",
        "CENTRALIZED_JOINT_DECISION_BATCH",
        # Supply torch_version to MechanicalAdamOptimizationContract.
        "NOT_APPLICABLE_SEPARATE_OPTIMIZERS", arguments, torch_version,
        # Supply an empty tuple to MechanicalAdamOptimizationContract.
        True, False, False, (),
        # Store ORIGINAL_ADAM_MECHANICAL_REFERENCE under 'beta_classification'.
        {"beta_classification": ORIGINAL_ADAM_MECHANICAL_REFERENCE,
         # Store ORIGINAL_ADAM_MECHANICAL_REFERENCE under 'epsilon_classification'.
         "epsilon_classification": ORIGINAL_ADAM_MECHANICAL_REFERENCE,
         "learning_rate_classification": "FROZEN_PILOT_CANDIDATE",
         # Store 0 under 'optimizer_instances'.
         # Store 0 under 'backward_calls'.
         "optimizer_instances": 0, "backward_calls": 0,
         # Store 0 under 'parameter_updates'.
         # Store 0 under 'role_specific_optimizer_weights'.
         "parameter_updates": 0, "role_specific_optimizer_weights": 0,
         # Store 0 under 'silent_adam_defaults'.
         # Store False under 'frozen_design_mutated'.
         "silent_adam_defaults": 0, "frozen_design_mutated": False,
         # Store False under 'claimed_optimal'.
         "claimed_optimal": False})


# Return exact names and reject duplicated optimizer membership.
# Input proposer_actor: the supplied proposer actor.
# Input responder_actor: the supplied responder actor.
# Input centralized_critic: the supplied centralized critic.
# Input frozen_gnn: the supplied frozen gnn.
# Output: the result of MappingProxyType(groups).
# Processing: select branches using the stated conditions.
def audit_parameter_membership(proposer_actor, responder_actor,
                               # Declare centralized_critic, frozen_gnn as input parameters.
                               centralized_critic, frozen_gnn):
    """Return exact names and reject duplicated optimizer membership."""
    # Set groups to a dictionary containing proposer, responder, critic, gnn.
    groups = {
        # Store a tuple built from a lazy sequence of formatted text built from the embedded values for (name, _)
        # in the result of proposer_actor.named_parameters() under 'proposer'.
        "proposer": tuple(f"proposer_actor.{name}" for name, _ in
                          # Evaluate the result of proposer_actor.named_parameters() as part of the enclosing
                          # expression.
                          proposer_actor.named_parameters()),
        # Store a tuple built from a lazy sequence of formatted text built from the embedded values for (name, _)
        # in the result of responder_actor.named_parameters() under 'responder'.
        "responder": tuple(f"responder_actor.{name}" for name, _ in
                           # Evaluate the result of responder_actor.named_parameters() as part of the enclosing
                           # expression.
                           responder_actor.named_parameters()),
        # Store a tuple built from a lazy sequence of formatted text built from the embedded values for (name, _)
        # in the result of centralized_critic.named_parameters() under 'critic'.
        "critic": tuple(f"centralized_critic.{name}" for name, _ in
                        # Evaluate the result of centralized_critic.named_parameters() as part of the enclosing
                        # expression.
                        centralized_critic.named_parameters()),
        # Store a tuple built from a lazy sequence of formatted text built from the embedded values for (name, _)
        # in the result of frozen_gnn.named_parameters() under 'gnn'.
        "gnn": tuple(f"frozen_gnn.{name}" for name, _ in
                     # Evaluate the result of frozen_gnn.named_parameters() as part of the enclosing expression.
                     frozen_gnn.named_parameters()),
    }
    # Set actor to a set built from groups at 'proposer' combined with a set built from groups at 'responder'.
    actor = set(groups["proposer"]) | set(groups["responder"])
    # Set (critic, gnn) to a tuple containing a set built from groups at 'critic', a set built from groups at
    # 'gnn'.
    critic, gnn = set(groups["critic"]), set(groups["gnn"])
    # Run this branch when actor intersected with critic or actor intersected with gnn or critic intersected with
    # gnn.
    if actor & critic or actor & gnn or critic & gnn:
        # Raise ValueError with the text 'DUPLICATE_OPTIMIZER_PARAMETER_MEMBERSHIP' to stop this execution path.
        raise ValueError("DUPLICATE_OPTIMIZER_PARAMETER_MEMBERSHIP")
    # Set groups['duplicate_trainable_parameter_membership'] to 0.
    groups["duplicate_trainable_parameter_membership"] = 0
    # Return the result of MappingProxyType(groups) to the caller.
    return MappingProxyType(groups)


# Explicit empirical mean over centralized joint decision batches.
# Input predicted_values: the supplied predicted values.
# Input returns: the supplied returns.
# Output: the result of torch.mean(predicted_values minus returns raised to the power 2).
# Processing: select branches using the stated conditions.
def joint_batch_critic_mean_squared_error(predicted_values, returns):
    """Explicit empirical mean over centralized joint decision batches."""
    # Import torch for use in this module.
    import torch

    # Run this branch when predicted_values.shape differs from returns.shape.
    if predicted_values.shape != returns.shape:
        # Raise ValueError with the text 'CRITIC_PREDICTION_RETURN_SHAPE_MISMATCH' to stop this execution path.
        raise ValueError("CRITIC_PREDICTION_RETURN_SHAPE_MISMATCH")
    # Run this branch when predicted_values.ndim differs from 1 or the result of predicted_values.numel() is less
    # than 1.
    if predicted_values.ndim != 1 or predicted_values.numel() < 1:
        # Raise ValueError with the text 'JOINT_DECISION_BATCH_VECTOR_REQUIRED' to stop this execution path.
        raise ValueError("JOINT_DECISION_BATCH_VECTOR_REQUIRED")
    # Return the result of torch.mean(predicted_values minus returns raised to the power 2) to the caller.
    return torch.mean((predicted_values - returns) ** 2)
