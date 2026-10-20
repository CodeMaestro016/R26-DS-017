"""Step 5J.3B mechanical-pilot configuration audit; constructs no models."""

# Import json for use in this module.
import json
# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType
# Import Any, Mapping, Optional, Tuple from typing for the operations below.
from typing import Any, Mapping, Optional, Tuple

# Import build_design from experimentation for the operations below.
from experimentation import build_design
# Import build_mechanical_pilot_architecture_contract from .architecture_contract for the operations below.
from .architecture_contract import build_mechanical_pilot_architecture_contract
# Import build_mechanical_adam_optimization_contract from .adam_contract for the operations below.
from .adam_contract import build_mechanical_adam_optimization_contract


# Set SCHEMA_DERIVED to the text 'SCHEMA_DERIVED'.
SCHEMA_DERIVED = "SCHEMA_DERIVED"
# Set MATHEMATICALLY_FIXED to the text 'MATHEMATICALLY_FIXED'.
MATHEMATICALLY_FIXED = "MATHEMATICALLY_FIXED"
# Set FROZEN_PILOT_CANDIDATE to the text 'FROZEN_PILOT_CANDIDATE'.
FROZEN_PILOT_CANDIDATE = "FROZEN_PILOT_CANDIDATE"
# Set EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC to the text 'EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC'.
EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC = (
    "EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC")
# Set MECHANICAL_REFERENCE_ONLY to the text 'MECHANICAL_IMPLEMENTATION_REFERENCE_ONLY'.
MECHANICAL_REFERENCE_ONLY = "MECHANICAL_IMPLEMENTATION_REFERENCE_ONLY"
# Set UNRESOLVED to the text 'UNRESOLVED_OPERATIONAL_PARAMETER'.
UNRESOLVED = "UNRESOLVED_OPERATIONAL_PARAMETER"
# Set RESOLVED_MECHANICAL_REFERENCE to the text 'RESOLVED_MECHANICAL_REFERENCE'.
RESOLVED_MECHANICAL_REFERENCE = "RESOLVED_MECHANICAL_REFERENCE"
# Set AUDIT_BLOCKED to the text 'MECHANICAL_PILOT_CONFIGURATION_INCOMPLETE'.
AUDIT_BLOCKED = "MECHANICAL_PILOT_CONFIGURATION_INCOMPLETE"
# Set ARCHITECTURE_BLOCKER to the text 'PILOT_ARCHITECTURE_CONTRACT_UNRESOLVED'.
ARCHITECTURE_BLOCKER = "PILOT_ARCHITECTURE_CONTRACT_UNRESOLVED"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MechanicalPilotRuntimeChoice to group the state and operations declared below.
# Declared fields: choice_id, classification, value, evidence_id, operationally_required, blocker_code,
# provenance.
# Construction and attribute behavior follow the declared decorators and base classes.
class MechanicalPilotRuntimeChoice:
    # Declare choice_id as str for this data structure.
    choice_id: str
    # Declare classification as str for this data structure.
    classification: str
    # Declare value as Optional[Any] for this data structure.
    value: Optional[Any]
    # Declare evidence_id as Optional[tuple] for this data structure.
    evidence_id: Optional[tuple]
    # Declare operationally_required as bool for this data structure.
    operationally_required: bool
    # Declare blocker_code as Optional[str] for this data structure.
    blocker_code: Optional[str]
    # Declare provenance as Mapping[str, Any] for this data structure.
    provenance: Mapping[str, Any]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MechanicalPilotConfigurationAudit to group the state and operations declared below.
# Declared fields: audit_id, frozen_design_id, provisional_configuration_id, architecture_contract_id,
# optimization_contract_id, runtime_choices, unresolved_choice_ids, silent_default_count, optimizer_instances,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MechanicalPilotConfigurationAudit:
    # Declare audit_id as tuple for this data structure.
    audit_id: tuple
    # Declare frozen_design_id as tuple for this data structure.
    frozen_design_id: tuple
    # Declare provisional_configuration_id as tuple for this data structure.
    provisional_configuration_id: tuple
    # Declare architecture_contract_id as tuple for this data structure.
    architecture_contract_id: tuple
    # Declare optimization_contract_id as tuple for this data structure.
    optimization_contract_id: tuple
    # Declare runtime_choices as Tuple[MechanicalPilotRuntimeChoice, ...] for this data structure.
    runtime_choices: Tuple[MechanicalPilotRuntimeChoice, ...]
    # Declare unresolved_choice_ids as Tuple[str, ...] for this data structure.
    unresolved_choice_ids: Tuple[str, ...]
    # Declare silent_default_count as int for this data structure.
    silent_default_count: int
    # Declare optimizer_instances as int for this data structure.
    optimizer_instances: int
    # Declare backward_calls as int for this data structure.
    backward_calls: int
    # Declare parameter_updates as int for this data structure.
    parameter_updates: int
    # Declare status as str for this data structure.
    status: str
    # Declare next_blocker as str for this data structure.
    next_blocker: str
    # Declare provenance as Mapping[str, Any] for this data structure.
    provenance: Mapping[str, Any]

    # Post init using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def __post_init__(self):
        # Call object.__setattr__ with the supplied arguments.
        object.__setattr__(self, "provenance",
                           # Supply the result of MappingProxyType(a dictionary built from self.provenance) to
                           # object.__setattr__.
                           MappingProxyType(dict(self.provenance)))


# Choice using the inputs and processing steps below.
# Input choice_id: the supplied choice id.
# Input classification: the supplied classification.
# Input value: the supplied value.
# Input evidence_id: the supplied evidence id.
# Input required: the supplied required.
# Input blocker: the supplied blocker.
# Input provenance: the supplied provenance.
# Output: the result of MechanicalPilotRuntimeChoice(choice_id, classification, value, evidence_id, required,
# blocker, provenance).
def _choice(choice_id, classification, value=None, evidence_id=None,
            # Declare required, blocker, provenance as input parameters.
            required=True, blocker=None, **provenance):
    # Return the result of MechanicalPilotRuntimeChoice(choice_id, classification, value, evidence_id, required,
    # blocker, provenance) to the caller.
    return MechanicalPilotRuntimeChoice(
        # Supply classification to MechanicalPilotRuntimeChoice.
        choice_id, classification, value, evidence_id, required, blocker,
        # Supply provenance to MechanicalPilotRuntimeChoice.
        provenance)


# Build mechanical pilot configuration audit using the inputs and processing steps below.
# Input profile_path: the supplied profile path.
# Output: the result of MechanicalPilotConfigurationAudit(a tuple containing the text
# 'MECHANICAL_PILOT_CONFIGURATION_AUDIT_V2',...).
# Processing: select branches using the stated conditions.
def build_mechanical_pilot_configuration_audit(
        # Declare profile_path as input parameter.
        profile_path="results/coupled_environment_profile.json"):
    # Set design to the result of build_design().
    design = build_design()
    # Set profile to the decoded data produced by json.loads from the text read from Path(profile_path).
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    # Run this branch when 'status' from profile; use None if absent differs from the text
    # 'COUPLED_ENVIRONMENT_PROFILE_COMPLETE'.
    if profile.get("status") != "COUPLED_ENVIRONMENT_PROFILE_COMPLETE":
        # Raise ValueError with the text 'STEP_5J_3A_PROFILE_NOT_COMPLETE' to stop this execution path.
        raise ValueError("STEP_5J_3A_PROFILE_NOT_COMPLETE")
    # Run this branch when 'step_5j_3b_readiness' from profile; use None if absent differs from the text
    # 'READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT'.
    if profile.get("step_5j_3b_readiness") != (
            "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"):
        # Raise ValueError with the text 'STEP_5J_3B_NOT_READY_FOR_CONFIGURATION_AUDIT' to stop this execution
        # path.
        raise ValueError("STEP_5J_3B_NOT_READY_FOR_CONFIGURATION_AUDIT")
    # Set provisional to design at 'provisional'.
    provisional = design["provisional"]
    # Set architecture to the result of build_mechanical_pilot_architecture_contract(profile_path).
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    # Set optimization to the result of build_mechanical_adam_optimization_contract(profile_path).
    optimization = build_mechanical_adam_optimization_contract(profile_path)
    # Set assignments to a dictionary of item.choice_id mapped to item for item in provisional.assignments.
    assignments = {item.choice_id: item for item in provisional.assignments}

    # Frozen using the inputs and processing steps below.
    # Input name: the supplied name.
    # Output: the result of _choice(name, FROZEN_PILOT_CANDIDATE, item.candidate_value_or_method,
    # item.candidate_evidence_id).
    def frozen(name):
        # Set item to assignments at name.
        item = assignments[name]
        # Return the result of _choice(name, FROZEN_PILOT_CANDIDATE, item.candidate_value_or_method,
        # item.candidate_evidence_id) to the caller.
        return _choice(name, FROZEN_PILOT_CANDIDATE,
                       # Supply item.candidate_value_or_method to _choice.
                       item.candidate_value_or_method,
                       # Supply item.candidate_evidence_id to _choice.
                       item.candidate_evidence_id,
                       # Supply project_selected as item.project_selected.
                       project_selected=item.project_selected,
                       # Supply assignment_status as item.status.
                       assignment_status=item.status)

    # Set choices to a list containing the result of _choice(the text 'node_input_dimension', SCHEMA_DERIVED, 8),
    # the result of _choice(the text...
    choices = [
        # Include the result of _choice(the text 'node_input_dimension', SCHEMA_DERIVED, 8) in this list.
        _choice("node_input_dimension", SCHEMA_DERIVED, 8,
                # Supply provenance_source as the text 'NODE_NUMERIC_SCHEMA'.
                provenance_source="NODE_NUMERIC_SCHEMA"),
        # Include the result of _choice(the text 'edge_input_dimension', SCHEMA_DERIVED, 9) in this list.
        _choice("edge_input_dimension", SCHEMA_DERIVED, 9,
                # Supply provenance_source as the text 'EDGE_NUMERIC_SCHEMA'.
                provenance_source="EDGE_NUMERIC_SCHEMA"),
        # Include the result of _choice(the text 'proposer_action_count', SCHEMA_DERIVED, 2) in this list.
        _choice("proposer_action_count", SCHEMA_DERIVED, 2,
                # Supply provenance_source as the text 'PROPOSER_ACTION_ORDER'.
                provenance_source="PROPOSER_ACTION_ORDER"),
        # Include the result of _choice(the text 'responder_action_count', SCHEMA_DERIVED, 2) in this list.
        _choice("responder_action_count", SCHEMA_DERIVED, 2,
                # Supply provenance_source as the text 'RESPONDER_ACTION_ORDER'.
                provenance_source="RESPONDER_ACTION_ORDER"),
        # Include the result of frozen(the text 'gnn_hidden_dimension') in this list.
        frozen("gnn_hidden_dimension"),
        # Include the result of _choice(the text 'gnn_message_passing_layers', RESOLVED_MECHANICAL_REFERENCE,...)
        # in this list.
        _choice("gnn_message_passing_layers", RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.gnn_message_passing_layers to _choice.
                architecture.gnn_message_passing_layers,
                # Supply architecture.contract_id to _choice.
                architecture.contract_id,
                # Supply mechanical_reference_only as True.
                # Supply project_selected as False.
                mechanical_reference_only=True, project_selected=False),
        # Include the result of _choice(the text 'gnn_activation', EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC, the
        # text 'RELU') in this list.
        _choice("gnn_activation", EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC,
                # Supply provenance_source as the text 'EdgeAwareMPNNEncoder source'.
                "RELU", provenance_source="EdgeAwareMPNNEncoder source"),
        # Include the result of _choice(the text 'neural_initialization_policy',
        # RESOLVED_MECHANICAL_REFERENCE,...) in this list.
        _choice("neural_initialization_policy", RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.initialization_policy to _choice.
                architecture.initialization_policy, architecture.contract_id,
                # Supply mechanical_reference_only as True.
                # Supply project_selected as False.
                mechanical_reference_only=True, project_selected=False),
        # Include the result of _choice(the text 'frozen_gnn_parameter_source', RESOLVED_MECHANICAL_REFERENCE,...)
        # in this list.
        _choice("frozen_gnn_parameter_source", RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.frozen_gnn_parameter_source to _choice.
                architecture.frozen_gnn_parameter_source,
                # Supply mechanical_reference_only as True.
                architecture.contract_id, mechanical_reference_only=True,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of _choice(the text 'proposer_actor_head_architecture',
        # RESOLVED_MECHANICAL_REFERENCE,...) in this list.
        _choice("proposer_actor_head_architecture",
                # Supply RESOLVED_MECHANICAL_REFERENCE to _choice.
                RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.proposer_actor_head_architecture to _choice.
                architecture.proposer_actor_head_architecture,
                # Supply mechanical_reference_only as True.
                architecture.contract_id, mechanical_reference_only=True,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of _choice(the text 'responder_actor_head_architecture',
        # RESOLVED_MECHANICAL_REFERENCE,...) in this list.
        _choice("responder_actor_head_architecture",
                # Supply RESOLVED_MECHANICAL_REFERENCE to _choice.
                RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.responder_actor_head_architecture to _choice.
                architecture.responder_actor_head_architecture,
                # Supply mechanical_reference_only as True.
                architecture.contract_id, mechanical_reference_only=True,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of _choice(the text 'centralized_critic_architecture',
        # RESOLVED_MECHANICAL_REFERENCE,...) in this list.
        _choice("centralized_critic_architecture",
                # Supply RESOLVED_MECHANICAL_REFERENCE to _choice.
                RESOLVED_MECHANICAL_REFERENCE,
                # Supply architecture.centralized_critic_architecture to _choice.
                architecture.centralized_critic_architecture,
                # Supply mechanical_reference_only as True.
                architecture.contract_id, mechanical_reference_only=True,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of frozen(the text 'parameter_sharing_strategy') in this list.
        frozen("parameter_sharing_strategy"),
        # Include the result of frozen(the text 'gnn_training_mode') in this list.
        frozen("gnn_training_mode"),
        # Include the result of frozen(the text 'ppo_clip_epsilon') in this list.
        frozen("ppo_clip_epsilon"),
        # Include the result of frozen(the text 'learning_rate') in this list.
        frozen("learning_rate"),
        # Include the result of frozen(the text 'optimizer_family') in this list.
        frozen("optimizer_family"),
        # Include the result of _choice(the text 'adam_beta1', RESOLVED_MECHANICAL_REFERENCE, optimization.beta1,
        # optimization.contract_id) in this list.
        _choice("adam_beta1", RESOLVED_MECHANICAL_REFERENCE,
                # Supply optimization.contract_id to _choice.
                optimization.beta1, optimization.contract_id,
                # Supply source as optimization.beta1_source.
                # Supply project_selected as False.
                source=optimization.beta1_source, project_selected=False),
        # Include the result of _choice(the text 'adam_beta2', RESOLVED_MECHANICAL_REFERENCE, optimization.beta2,
        # optimization.contract_id) in this list.
        _choice("adam_beta2", RESOLVED_MECHANICAL_REFERENCE,
                # Supply optimization.contract_id to _choice.
                optimization.beta2, optimization.contract_id,
                # Supply source as optimization.beta2_source.
                # Supply project_selected as False.
                source=optimization.beta2_source, project_selected=False),
        # Include the result of _choice(the text 'adam_epsilon', RESOLVED_MECHANICAL_REFERENCE,
        # optimization.epsilon,...) in this list.
        _choice("adam_epsilon", RESOLVED_MECHANICAL_REFERENCE,
                # Supply optimization.contract_id to _choice.
                optimization.epsilon, optimization.contract_id,
                # Supply source as optimization.epsilon_source.
                # Supply project_selected as False.
                source=optimization.epsilon_source, project_selected=False),
        # Include the result of _choice(the text 'weight_decay', RESOLVED_MECHANICAL_REFERENCE,
        # optimization.weight_decay,...) in this list.
        _choice("weight_decay", RESOLVED_MECHANICAL_REFERENCE,
                # Supply optimization.weight_decay to _choice.
                optimization.weight_decay, optimization.contract_id,
                # Supply semantics as optimization.weight_decay_semantics.
                semantics=optimization.weight_decay_semantics,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of _choice(the text 'adam_amsgrad', RESOLVED_MECHANICAL_REFERENCE,
        # optimization.amsgrad,...) in this list.
        _choice("adam_amsgrad", RESOLVED_MECHANICAL_REFERENCE,
                # Supply optimization.contract_id to _choice.
                optimization.amsgrad, optimization.contract_id,
                # Supply semantics as optimization.amsgrad_semantics.
                semantics=optimization.amsgrad_semantics,
                # Supply project_selected as False.
                project_selected=False),
        # Include the result of _choice(the text 'optimizer_parameter_grouping', RESOLVED_MECHANICAL_REFERENCE, a
        # tuple containing...) in this list.
        _choice("optimizer_parameter_grouping", RESOLVED_MECHANICAL_REFERENCE,
                # Supply a tuple containing optimization.actor_parameter_grouping,
                # optimization.critic_parameter_grouping,... to _choice.
                (optimization.actor_parameter_grouping,
                 # Include optimization.critic_parameter_grouping in this tuple.
                 optimization.critic_parameter_grouping,
                 # Include optimization.frozen_parameter_exclusions in this tuple.
                 optimization.frozen_parameter_exclusions),
                # Supply separate_optimizers as True.
                optimization.contract_id, separate_optimizers=True,
                # Supply role_specific_optimizer_weights as 0.
                role_specific_optimizer_weights=0),
        # Include the result of _choice(the text 'minibatch_construction', MECHANICAL_REFERENCE_ONLY, the text...)
        # in this list.
        _choice("minibatch_construction", MECHANICAL_REFERENCE_ONLY,
                "MECHANICAL_FULL_BATCH_NO_MINIBATCH_HYPERPARAMETER",
                # Supply final_method_selection_eligible as False.
                final_method_selection_eligible=False),
        # Include the result of frozen(the text 'ppo_update_epochs') in this list.
        frozen("ppo_update_epochs"),
        # Include the result of frozen(the text 'advantage_normalization') in this list.
        frozen("advantage_normalization"),
        # Include the result of _choice(the text 'entropy_regularization', MECHANICAL_REFERENCE_ONLY, the text...)
        # in this list.
        _choice("entropy_regularization", MECHANICAL_REFERENCE_ONLY,
                "UNRESOLVED_NOT_USED_IN_MECHANICAL_INTEGRATION",
                # Supply final_method_selection_eligible as False.
                final_method_selection_eligible=False),
        # Include the result of _choice(the text 'critic_loss_form', MATHEMATICALLY_FIXED, the text
        # 'PURE_SQUARED_ERROR') in this list.
        _choice("critic_loss_form", MATHEMATICALLY_FIXED,
                # Supply provenance_source as the text 'Step 5I'.
                "PURE_SQUARED_ERROR", provenance_source="Step 5I"),
        # Include the result of _choice(the text 'critic_loss_reduction', MATHEMATICALLY_FIXED,
        # optimization.critic_loss_reduction,...) in this list.
        _choice("critic_loss_reduction", MATHEMATICALLY_FIXED,
                # Supply optimization.critic_loss_reduction to _choice.
                optimization.critic_loss_reduction,
                # Supply optimization.contract_id to _choice.
                optimization.contract_id,
                # Supply sample_unit as optimization.critic_sample_unit.
                sample_unit=optimization.critic_sample_unit,
                # Supply policy_factor_weighting as False.
                policy_factor_weighting=False),
        # Include the result of _choice(the text 'value_loss_mixing_coefficient', MECHANICAL_REFERENCE_ONLY, the
        # text...) in this list.
        _choice("value_loss_mixing_coefficient", MECHANICAL_REFERENCE_ONLY,
                "NOT_USED_SEPARATE_OBJECTIVES",
                # Supply final_method_selection_eligible as False.
                final_method_selection_eligible=False),
        # Include the result of _choice(the text 'gradient_clipping', MECHANICAL_REFERENCE_ONLY, the text...) in
        # this list.
        _choice("gradient_clipping", MECHANICAL_REFERENCE_ONLY,
                "UNRESOLVED_NOT_USED_IN_MECHANICAL_INTEGRATION",
                # Supply final_method_selection_eligible as False.
                final_method_selection_eligible=False),
        # Include the result of frozen(the text 'multi_policy_factor_aggregation') in this list.
        frozen("multi_policy_factor_aggregation"),
        # Include the result of _choice(the text 'rollout_scope', MATHEMATICALLY_FIXED, the text
        # 'ONE_TRAINING_MANIFEST_PASS') in this list.
        _choice("rollout_scope", MATHEMATICALLY_FIXED,
                "ONE_TRAINING_MANIFEST_PASS",
                # Supply provenance_source as the text 'Step 5J.3A natural structural unit'.
                provenance_source="Step 5J.3A natural structural unit"),
        # Include the result of _choice(the text 'discount_factor', MATHEMATICALLY_FIXED, None) in this list.
        _choice("discount_factor", MATHEMATICALLY_FIXED, None,
                # Supply provenance_source as the text 'Exact undiscounted Step 5I return'.
                provenance_source="Exact undiscounted Step 5I return"),
        # Include the result of _choice(the text 'gae_lambda', MATHEMATICALLY_FIXED, None) in this list.
        _choice("gae_lambda", MATHEMATICALLY_FIXED, None,
                # Supply provenance_source as the text 'GAE not used in baseline'.
                provenance_source="GAE not used in baseline"),
    ]
    # Set unresolved to a tuple built from a lazy sequence of item.choice_id for item in choices; retain entries
    # satisfying item.operationally_required and item.classification equals UNRESOLVED.
    unresolved = tuple(item.choice_id for item in choices
                       # Evaluate item.operationally_required and item.classification equals UNRESOLVED as part of
                       # the enclosing expression.
                       if item.operationally_required and
                       # Evaluate item.classification equals UNRESOLVED as part of the enclosing expression.
                       item.classification == UNRESOLVED)
    # Set blockers to a tuple built from the result of dict.fromkeys(a lazy sequence of item.blocker_code for item
    # in choices; retain entries satisfying...).
    blockers = tuple(dict.fromkeys(item.blocker_code for item in choices
                                   # Evaluate item.blocker_code as part of the enclosing expression.
                                   if item.blocker_code))
    # Set next_blocker to ARCHITECTURE_BLOCKER when ARCHITECTURE_BLOCKER belongs to blockers, otherwise blockers
    # at 0 when blockers, otherwise the text 'NONE'.
    next_blocker = (ARCHITECTURE_BLOCKER if ARCHITECTURE_BLOCKER in blockers
                    # Evaluate blockers at 0 when blockers, otherwise the text 'NONE' as part of the enclosing
                    # expression.
                    else blockers[0] if blockers else "NONE")
    # Return the result of MechanicalPilotConfigurationAudit(a tuple containing the text
    # 'MECHANICAL_PILOT_CONFIGURATION_AUDIT_V2',...) to the caller.
    return MechanicalPilotConfigurationAudit(
        # Supply a tuple containing the text 'MECHANICAL_PILOT_CONFIGURATION_AUDIT_V2', design['freeze'].freeze_id
        # to MechanicalPilotConfigurationAudit.
        ("MECHANICAL_PILOT_CONFIGURATION_AUDIT_V2",
         # Supply design['freeze'].freeze_id to MechanicalPilotConfigurationAudit.
         design["freeze"].freeze_id), design["freeze"].freeze_id,
        # Supply provisional.configuration_id to MechanicalPilotConfigurationAudit.
        provisional.configuration_id, architecture.contract_id,
        # Supply optimization.contract_id to MechanicalPilotConfigurationAudit.
        optimization.contract_id, tuple(choices), unresolved, 0, 0, 0, 0,
        # Supply AUDIT_BLOCKED when unresolved, otherwise the text 'MECHANICAL_PILOT_CONFIGURATION_COMPLETE' to
        # MechanicalPilotConfigurationAudit.
        AUDIT_BLOCKED if unresolved else "MECHANICAL_PILOT_CONFIGURATION_COMPLETE",
        # Supply next_blocker to MechanicalPilotConfigurationAudit.
        next_blocker,
        # Store 0 under 'models_constructed'.
        # Store 0 under 'behavior_policy_samples'.
        {"models_constructed": 0, "behavior_policy_samples": 0,
         # Store 0 under 'rl_seeds_instantiated'.
         # Store 0 under 'project_selected_hyperparameters'.
         "rl_seeds_instantiated": 0, "project_selected_hyperparameters": 0,
         # Store 0 under 'validation_performance_runs'.
         # Store 0 under 'held_out_performance_runs'.
         "validation_performance_runs": 0, "held_out_performance_runs": 0,
         # Store 0 under 'learned_main_actions'.
         "learned_main_actions": 0})
