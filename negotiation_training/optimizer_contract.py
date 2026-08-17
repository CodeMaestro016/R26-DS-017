"""Step 5J.3B mechanical-pilot configuration audit; constructs no models."""

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from experimentation import build_design
from .architecture_contract import build_mechanical_pilot_architecture_contract


SCHEMA_DERIVED = "SCHEMA_DERIVED"
MATHEMATICALLY_FIXED = "MATHEMATICALLY_FIXED"
FROZEN_PILOT_CANDIDATE = "FROZEN_PILOT_CANDIDATE"
EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC = (
    "EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC")
MECHANICAL_REFERENCE_ONLY = "MECHANICAL_IMPLEMENTATION_REFERENCE_ONLY"
UNRESOLVED = "UNRESOLVED_OPERATIONAL_PARAMETER"
RESOLVED_MECHANICAL_REFERENCE = "RESOLVED_MECHANICAL_REFERENCE"
AUDIT_BLOCKED = "MECHANICAL_PILOT_CONFIGURATION_INCOMPLETE"
ARCHITECTURE_BLOCKER = "PILOT_ARCHITECTURE_CONTRACT_UNRESOLVED"


@dataclass(frozen=True)
class MechanicalPilotRuntimeChoice:
    choice_id: str
    classification: str
    value: Optional[Any]
    evidence_id: Optional[tuple]
    operationally_required: bool
    blocker_code: Optional[str]
    provenance: Mapping[str, Any]

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class MechanicalPilotConfigurationAudit:
    audit_id: tuple
    frozen_design_id: tuple
    provisional_configuration_id: tuple
    runtime_choices: Tuple[MechanicalPilotRuntimeChoice, ...]
    unresolved_choice_ids: Tuple[str, ...]
    silent_default_count: int
    optimizer_instances: int
    backward_calls: int
    parameter_updates: int
    status: str
    next_blocker: str
    provenance: Mapping[str, Any]

    def __post_init__(self):
        object.__setattr__(self, "provenance",
                           MappingProxyType(dict(self.provenance)))


def _choice(choice_id, classification, value=None, evidence_id=None,
            required=True, blocker=None, **provenance):
    return MechanicalPilotRuntimeChoice(
        choice_id, classification, value, evidence_id, required, blocker,
        provenance)


def build_mechanical_pilot_configuration_audit(
        profile_path="results/coupled_environment_profile.json"):
    design = build_design()
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    if profile.get("status") != "COUPLED_ENVIRONMENT_PROFILE_COMPLETE":
        raise ValueError("STEP_5J_3A_PROFILE_NOT_COMPLETE")
    if profile.get("step_5j_3b_readiness") != (
            "READY_TO_IMPLEMENT_FIRST_CONTROLLED_MAPPO_PILOT"):
        raise ValueError("STEP_5J_3B_NOT_READY_FOR_CONFIGURATION_AUDIT")
    provisional = design["provisional"]
    architecture = build_mechanical_pilot_architecture_contract(profile_path)
    assignments = {item.choice_id: item for item in provisional.assignments}

    def frozen(name):
        item = assignments[name]
        return _choice(name, FROZEN_PILOT_CANDIDATE,
                       item.candidate_value_or_method,
                       item.candidate_evidence_id,
                       project_selected=item.project_selected,
                       assignment_status=item.status)

    choices = [
        _choice("node_input_dimension", SCHEMA_DERIVED, 8,
                provenance_source="NODE_NUMERIC_SCHEMA"),
        _choice("edge_input_dimension", SCHEMA_DERIVED, 9,
                provenance_source="EDGE_NUMERIC_SCHEMA"),
        _choice("proposer_action_count", SCHEMA_DERIVED, 2,
                provenance_source="PROPOSER_ACTION_ORDER"),
        _choice("responder_action_count", SCHEMA_DERIVED, 2,
                provenance_source="RESPONDER_ACTION_ORDER"),
        frozen("gnn_hidden_dimension"),
        _choice("gnn_message_passing_layers", RESOLVED_MECHANICAL_REFERENCE,
                architecture.gnn_message_passing_layers,
                architecture.contract_id,
                mechanical_reference_only=True, project_selected=False),
        _choice("gnn_activation", EXPLICIT_EXISTING_ARCHITECTURE_SEMANTIC,
                "RELU", provenance_source="EdgeAwareMPNNEncoder source"),
        _choice("neural_initialization_policy", RESOLVED_MECHANICAL_REFERENCE,
                architecture.initialization_policy, architecture.contract_id,
                mechanical_reference_only=True, project_selected=False),
        _choice("frozen_gnn_parameter_source", RESOLVED_MECHANICAL_REFERENCE,
                architecture.frozen_gnn_parameter_source,
                architecture.contract_id, mechanical_reference_only=True,
                project_selected=False),
        _choice("proposer_actor_head_architecture",
                RESOLVED_MECHANICAL_REFERENCE,
                architecture.proposer_actor_head_architecture,
                architecture.contract_id, mechanical_reference_only=True,
                project_selected=False),
        _choice("responder_actor_head_architecture",
                RESOLVED_MECHANICAL_REFERENCE,
                architecture.responder_actor_head_architecture,
                architecture.contract_id, mechanical_reference_only=True,
                project_selected=False),
        _choice("centralized_critic_architecture",
                RESOLVED_MECHANICAL_REFERENCE,
                architecture.centralized_critic_architecture,
                architecture.contract_id, mechanical_reference_only=True,
                project_selected=False),
        frozen("parameter_sharing_strategy"),
        frozen("gnn_training_mode"),
        frozen("ppo_clip_epsilon"),
        frozen("learning_rate"),
        frozen("optimizer_family"),
        _choice("adam_beta1", UNRESOLVED,
                blocker="ADAM_INTERNAL_PARAMETER_CONTRACT_UNRESOLVED"),
        _choice("adam_beta2", UNRESOLVED,
                blocker="ADAM_INTERNAL_PARAMETER_CONTRACT_UNRESOLVED"),
        _choice("adam_epsilon", UNRESOLVED,
                blocker="ADAM_INTERNAL_PARAMETER_CONTRACT_UNRESOLVED"),
        _choice("weight_decay", UNRESOLVED,
                blocker="WEIGHT_DECAY_CONTRACT_UNRESOLVED"),
        _choice("adam_amsgrad", UNRESOLVED,
                blocker="ADAM_INTERNAL_PARAMETER_CONTRACT_UNRESOLVED"),
        _choice("optimizer_parameter_grouping", UNRESOLVED,
                blocker="OPTIMIZER_PARAMETER_GROUPING_UNRESOLVED"),
        _choice("minibatch_construction", MECHANICAL_REFERENCE_ONLY,
                "MECHANICAL_FULL_BATCH_NO_MINIBATCH_HYPERPARAMETER",
                final_method_selection_eligible=False),
        frozen("ppo_update_epochs"),
        frozen("advantage_normalization"),
        _choice("entropy_regularization", MECHANICAL_REFERENCE_ONLY,
                "UNRESOLVED_NOT_USED_IN_MECHANICAL_INTEGRATION",
                final_method_selection_eligible=False),
        _choice("critic_loss_form", MATHEMATICALLY_FIXED,
                "PURE_SQUARED_ERROR", provenance_source="Step 5I"),
        _choice("critic_loss_reduction", UNRESOLVED,
                blocker="CRITIC_LOSS_REDUCTION_UNRESOLVED"),
        _choice("value_loss_mixing_coefficient", MECHANICAL_REFERENCE_ONLY,
                "NOT_USED_SEPARATE_OBJECTIVES",
                final_method_selection_eligible=False),
        _choice("gradient_clipping", MECHANICAL_REFERENCE_ONLY,
                "UNRESOLVED_NOT_USED_IN_MECHANICAL_INTEGRATION",
                final_method_selection_eligible=False),
        frozen("multi_policy_factor_aggregation"),
        _choice("rollout_scope", MATHEMATICALLY_FIXED,
                "ONE_TRAINING_MANIFEST_PASS",
                provenance_source="Step 5J.3A natural structural unit"),
        _choice("discount_factor", MATHEMATICALLY_FIXED, None,
                provenance_source="Exact undiscounted Step 5I return"),
        _choice("gae_lambda", MATHEMATICALLY_FIXED, None,
                provenance_source="GAE not used in baseline"),
    ]
    unresolved = tuple(item.choice_id for item in choices
                       if item.operationally_required and
                       item.classification == UNRESOLVED)
    blockers = tuple(dict.fromkeys(item.blocker_code for item in choices
                                   if item.blocker_code))
    next_blocker = (ARCHITECTURE_BLOCKER if ARCHITECTURE_BLOCKER in blockers
                    else blockers[0] if blockers else "NONE")
    return MechanicalPilotConfigurationAudit(
        ("MECHANICAL_PILOT_CONFIGURATION_AUDIT_V1",
         design["freeze"].freeze_id), design["freeze"].freeze_id,
        provisional.configuration_id, tuple(choices), unresolved, 0, 0, 0, 0,
        AUDIT_BLOCKED if unresolved else "MECHANICAL_PILOT_CONFIGURATION_COMPLETE",
        next_blocker,
        {"models_constructed": 0, "behavior_policy_samples": 0,
         "rl_seeds_instantiated": 0, "project_selected_hyperparameters": 0,
         "validation_performance_runs": 0, "held_out_performance_runs": 0,
         "learned_main_actions": 0})
