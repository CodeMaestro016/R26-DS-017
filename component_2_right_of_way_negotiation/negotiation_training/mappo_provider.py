"""Real stochastic MAPPO behavior provider; collection only, no optimizer."""

# Import hashlib for use in this module.
import hashlib
# Import dataclass, replace from dataclasses for the operations below.
from dataclasses import dataclass, replace
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType

# Import torch for use in this module.
import torch

# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import NegotiationClaimBuilder from negotiation_learning.claim_semantics for the operations below.
from negotiation_learning.claim_semantics import NegotiationClaimBuilder
# Import CentralizedCriticInputBuilder, CentralizedNegotiationCritic, DecentralizedNegotiationActor,
# DecentralizedNegotiationResponseActor from negotiation_learning.ctde for the operations below.
from negotiation_learning.ctde import (
    CentralizedCriticInputBuilder, CentralizedNegotiationCritic,
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor)
# Import EdgeAwareMPNNEncoder, to_torch_graph from negotiation_learning.gnn for the operations below.
from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
# Import JointProposerActionAssignment, JointResponderActionAssignment from negotiation_learning.joint_negotiation
# for the operations below.
from negotiation_learning.joint_negotiation import (
    JointProposerActionAssignment, JointResponderActionAssignment)
# Import NegotiationDecisionRole, NegotiationPolicyContextBuilder, RoleAwareNegotiationPolicy from
# negotiation_learning.mappo_interface for the operations below.
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyContextBuilder,
    RoleAwareNegotiationPolicy)
# Import NegotiationAction from negotiation_learning.models for the operations below.
from negotiation_learning.models import NegotiationAction
# Import RegulatoryPrecedenceGraphBuilder from negotiation_learning.precedence_graph for the operations below.
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import ClaimRelinquishmentProtocol, NegotiationResponseAction, NegotiationResponseCandidateBuilder,
# ProposalResponse from negotiation_learning.protocol for the operations below.
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationResponseAction,
    NegotiationResponseCandidateBuilder, ProposalResponse)
# Import NegotiationSemanticFeatureEncoder from negotiation_learning.semantic_encoding for the operations below.
from negotiation_learning.semantic_encoding import NegotiationSemanticFeatureEncoder
# Import CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator from negotiation_learning.mappo_returns for
# the operations below.
from negotiation_learning.mappo_returns import (
    CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator)
# Import REWARD_DEFINITION_ID, TeamObjectiveRecord from negotiation_objective.models for the operations below.
from negotiation_objective.models import (
    REWARD_DEFINITION_ID, TeamObjectiveRecord)

# Import build_mechanical_adam_optimization_contract from .adam_contract for the operations below.
from .adam_contract import build_mechanical_adam_optimization_contract
# Import apply_explicit_mechanical_initialization, build_mechanical_pilot_architecture_contract,
# deterministic_initialization_seed from .architecture_contract for the operations below.
from .architecture_contract import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)
# Import MAPPOBehaviorRolloutIdentity, MAPPOCriticSample, MAPPOPolicyFactorSample, evaluate_policy_factor_sample,
# parameter_hash, tensor_snapshot from .rollout for the operations below.
from .rollout import (
    MAPPOBehaviorRolloutIdentity, MAPPOCriticSample, MAPPOPolicyFactorSample,
    evaluate_policy_factor_sample, parameter_hash, tensor_snapshot)


# Set BEHAVIOR_SOURCE to the text 'MAPPO_BEHAVIOR_POLICY'.
BEHAVIOR_SOURCE = "MAPPO_BEHAVIOR_POLICY"
# Set BEHAVIOR_RULE to the text 'STOCHASTIC_MASKED_ROLE_POLICY_NO_BRANCH_ENUMERATION'.
BEHAVIOR_RULE = "STOCHASTIC_MASKED_ROLE_POLICY_NO_BRANCH_ENUMERATION"


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MechanicalMAPPOBehaviorPolicyBundle to group the state and operations declared below.
# Declared fields: gnn, proposer_actor, responder_actor, centralized_critic, policy, architecture_contract_id,
# optimization_contract_id, behavior_rollout_identity, component_seeds, initial_parameter_hashes,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MechanicalMAPPOBehaviorPolicyBundle:
    # Declare gnn as object for this data structure.
    gnn: object
    # Declare proposer_actor as object for this data structure.
    proposer_actor: object
    # Declare responder_actor as object for this data structure.
    responder_actor: object
    # Declare centralized_critic as object for this data structure.
    centralized_critic: object
    # Declare policy as object for this data structure.
    policy: object
    # Declare architecture_contract_id as tuple for this data structure.
    architecture_contract_id: tuple
    # Declare optimization_contract_id as tuple for this data structure.
    optimization_contract_id: tuple
    # Declare behavior_rollout_identity as MAPPOBehaviorRolloutIdentity for this data structure.
    behavior_rollout_identity: MAPPOBehaviorRolloutIdentity
    # Declare component_seeds as MappingProxyType for this data structure.
    component_seeds: MappingProxyType
    # Declare initial_parameter_hashes as MappingProxyType for this data structure.
    initial_parameter_hashes: MappingProxyType
    # Declare policy_parameter_identity as tuple for this data structure.
    policy_parameter_identity: tuple


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define MAPPOJointPolicyOutcome to group the state and operations declared below.
# Declared fields: outcome_id, scenario_id, source_snapshot_id, proposer_assignment, responder_assignment,
# protocol_messages, completed_agreement_ids, rejected_proposal_ids, pending_proposal_ids,
# original_precedence_graph,....
# Construction and attribute behavior follow the declared decorators and base classes.
class MAPPOJointPolicyOutcome:
    # Declare outcome_id as tuple for this data structure.
    outcome_id: tuple
    # Declare scenario_id as tuple for this data structure.
    scenario_id: tuple
    # Declare source_snapshot_id as tuple for this data structure.
    source_snapshot_id: tuple
    # Declare proposer_assignment as object for this data structure.
    proposer_assignment: object
    # Declare responder_assignment as object for this data structure.
    responder_assignment: object
    # Declare protocol_messages as tuple for this data structure.
    protocol_messages: tuple
    # Declare completed_agreement_ids as tuple for this data structure.
    completed_agreement_ids: tuple
    # Declare rejected_proposal_ids as tuple for this data structure.
    rejected_proposal_ids: tuple
    # Declare pending_proposal_ids as tuple for this data structure.
    pending_proposal_ids: tuple
    # Declare original_precedence_graph as tuple for this data structure.
    original_precedence_graph: tuple
    # Declare effective_precedence_graph as tuple for this data structure.
    effective_precedence_graph: tuple
    # Declare coordination_sccs as tuple for this data structure.
    coordination_sccs: tuple
    # Declare coordination_cycle_detected as bool for this data structure.
    coordination_cycle_detected: bool
    # Declare policy_status as str for this data structure.
    policy_status: str
    # Declare behavior_source as str for this data structure.
    behavior_source: str
    # Declare provenance as MappingProxyType for this data structure.
    provenance: MappingProxyType


# Build behavior rollout identity using the inputs and processing steps below.
# Output: the result of MAPPOBehaviorRolloutIdentity(a tuple containing the text 'MAPPO_BEHAVIOR_ROLLOUT_V1',
# digest, design['freeze'].freeze_id,...).
def build_behavior_rollout_identity():
    # Set design to the result of build_design().
    design = build_design()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set optimization to the result of build_mechanical_adam_optimization_contract().
    optimization = build_mechanical_adam_optimization_contract()
    # Set manifest to design['manifests'] at ScenarioRole.TRAINING.
    manifest = design["manifests"][ScenarioRole.TRAINING]
    # Set fields to a tuple containing design['freeze'].freeze_id, architecture.contract_id,
    # optimization.contract_id, manifest.manifest_id, the...
    fields = (design["freeze"].freeze_id, architecture.contract_id,
              # Include optimization.contract_id in this tuple.
              optimization.contract_id, manifest.manifest_id, "STEP_5J_3B_3")
    # Set digest to the hexadecimal digest from hashlib.sha256(repr(fields).encode()).
    digest = hashlib.sha256(repr(fields).encode()).hexdigest()
    # Return the result of MAPPOBehaviorRolloutIdentity(a tuple containing the text 'MAPPO_BEHAVIOR_ROLLOUT_V1',
    # digest, design['freeze'].freeze_id,...) to the caller.
    return MAPPOBehaviorRolloutIdentity(
        # Supply a tuple containing the text 'MAPPO_BEHAVIOR_ROLLOUT_V1', digest to MAPPOBehaviorRolloutIdentity.
        ("MAPPO_BEHAVIOR_ROLLOUT_V1", digest), design["freeze"].freeze_id,
        # Supply architecture.contract_id to MAPPOBehaviorRolloutIdentity.
        architecture.contract_id, optimization.contract_id,
        # Supply manifest.manifest_id to MAPPOBehaviorRolloutIdentity.
        manifest.manifest_id)


# Build mechanical mappo behavior policy bundle using the inputs and processing steps below.
# Input component_seed_identity: the supplied component seed identity.
# Input behavior_rollout_identity: the supplied behavior rollout identity.
# Output: the result of MechanicalMAPPOBehaviorPolicyBundle(components at 'gnn', components at 'proposer',
# components at 'responder', components at...).
# Processing: iterate over the relevant records.
def build_mechanical_mappo_behavior_policy_bundle(
        # Declare component_seed_identity, behavior_rollout_identity as input parameters.
        component_seed_identity=None, behavior_rollout_identity=None):
    # Set identity to behavior_rollout_identity or the result of build_behavior_rollout_identity().
    identity = behavior_rollout_identity or build_behavior_rollout_identity()
    # Set architecture to the result of build_mechanical_pilot_architecture_contract().
    architecture = build_mechanical_pilot_architecture_contract()
    # Set components to a dictionary containing gnn, proposer, responder, critic.
    components = {
        # Store the result of EdgeAwareMPNNEncoder(8, 9, architecture.gnn_hidden_dimension,
        # architecture.gnn_message_passing_layers) under 'gnn'.
        "gnn": EdgeAwareMPNNEncoder(
            # Supply architecture.gnn_hidden_dimension to EdgeAwareMPNNEncoder.
            8, 9, architecture.gnn_hidden_dimension,
            # Supply architecture.gnn_message_passing_layers to EdgeAwareMPNNEncoder.
            architecture.gnn_message_passing_layers),
        # Store the result of DecentralizedNegotiationActor(architecture.proposer_input_dimension, 2) under
        # 'proposer'.
        "proposer": DecentralizedNegotiationActor(
            # Supply architecture.proposer_input_dimension to DecentralizedNegotiationActor.
            architecture.proposer_input_dimension, 2),
        # Store the result of DecentralizedNegotiationResponseActor(architecture.responder_input_dimension, 2)
        # under 'responder'.
        "responder": DecentralizedNegotiationResponseActor(
            # Supply architecture.responder_input_dimension to DecentralizedNegotiationResponseActor.
            architecture.responder_input_dimension, 2),
        # Store the result of CentralizedNegotiationCritic(architecture.critic_input_dimension) under 'critic'.
        "critic": CentralizedNegotiationCritic(
            # Supply architecture.critic_input_dimension to CentralizedNegotiationCritic.
            architecture.critic_input_dimension),
    }
    # Set labels to a dictionary containing gnn, proposer, responder, critic, sampling.
    labels = {
        "gnn": "MODEL_INITIALIZATION_GNN",
        "proposer": "MODEL_INITIALIZATION_PROPOSER",
        "responder": "MODEL_INITIALIZATION_RESPONDER",
        "critic": "MODEL_INITIALIZATION_CRITIC",
        "sampling": "POLICY_ACTION_SAMPLING",
    }
    # Set seed_scope to identity.rollout_id when component_seed_identity is the same object as None, otherwise
    # component_seed_identity.
    seed_scope = (identity.rollout_id if component_seed_identity is None
                  # Evaluate component_seed_identity as part of the enclosing expression.
                  else component_seed_identity)
    # Set seeds to a dictionary of name mapped to the result of
    # deterministic_initialization_seed(architecture.contract_id, a tuple containing seed_scope, label) for (name,
    # label) in key/value pairs from labels.
    seeds = {name: deterministic_initialization_seed(
        # Supply architecture.contract_id to deterministic_initialization_seed.
        architecture.contract_id, (seed_scope, label))
        # Evaluate key/value pairs from labels as part of the enclosing expression.
        for name, label in labels.items()}
    # Iterate over key/value pairs from components, binding each item to (name, module).
    for name, module in components.items():
        # Call apply_explicit_mechanical_initialization with the supplied arguments.
        apply_explicit_mechanical_initialization(module, seeds[name])
    # Iterate over the result of components['gnn'].parameters(), binding each item to parameter.
    for parameter in components["gnn"].parameters():
        # Call parameter.requires_grad_ with the supplied arguments.
        parameter.requires_grad_(False)
    # Set hashes to a dictionary of name mapped to the result of parameter_hash(module) for (name, module) in
    # key/value pairs from components.
    hashes = {name: parameter_hash(module) for name, module in components.items()}
    # Set policy_identity to a tuple containing the text 'MAPPO_POLICY_PARAMETERS_V1', hashes at 'proposer',
    # hashes at 'responder'.
    policy_identity = ("MAPPO_POLICY_PARAMETERS_V1", hashes["proposer"],
                       # Include hashes at 'responder' in this tuple.
                       hashes["responder"])
    # Set policy to the result of RoleAwareNegotiationPolicy(components at 'proposer', components at 'responder').
    policy = RoleAwareNegotiationPolicy(
        # Supply components at 'responder' to RoleAwareNegotiationPolicy.
        components["proposer"], components["responder"])
    # Return the result of MechanicalMAPPOBehaviorPolicyBundle(components at 'gnn', components at 'proposer',
    # components at 'responder', components at...) to the caller.
    return MechanicalMAPPOBehaviorPolicyBundle(
        # Supply components at 'responder' to MechanicalMAPPOBehaviorPolicyBundle.
        components["gnn"], components["proposer"], components["responder"],
        # Supply architecture.contract_id to MechanicalMAPPOBehaviorPolicyBundle.
        components["critic"], policy, architecture.contract_id,
        # Supply identity.optimization_contract_id to MechanicalMAPPOBehaviorPolicyBundle.
        identity.optimization_contract_id, identity,
        # Supply the result of MappingProxyType(hashes) to MechanicalMAPPOBehaviorPolicyBundle.
        MappingProxyType(seeds), MappingProxyType(hashes), policy_identity)


# Sample current role factors and compose one actual protocol outcome.
# Instances expose the attributes and methods implemented in this class.
class MAPPOBehaviorActionProvider:
    """Sample current role factors and compose one actual protocol outcome."""

    # Set selection_rule to BEHAVIOR_RULE.
    selection_rule = BEHAVIOR_RULE
    # Set outcome_data_used to False.
    outcome_data_used = False
    # Set uses_mappo_behavior_policy to True.
    uses_mappo_behavior_policy = True

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input bundle: the supplied bundle.
    # Input sampling_seed: the supplied sampling seed.
    # Input runtime_critic_enabled: the supplied runtime critic enabled.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, bundle=None, sampling_seed=None,
                 # Declare runtime_critic_enabled as input parameter.
                 runtime_critic_enabled=True):
        # Set self.bundle to bundle or the result of build_mechanical_mappo_behavior_policy_bundle().
        self.bundle = bundle or build_mechanical_mappo_behavior_policy_bundle()
        # Set self.runtime_critic_enabled to a Boolean built from runtime_critic_enabled.
        self.runtime_critic_enabled = bool(runtime_critic_enabled)
        # Set self.runtime_critic_calls to 0.
        self.runtime_critic_calls = 0
        # Set self.generator to the result of torch.Generator().
        self.generator = torch.Generator(device="cpu")
        # Set self.sampling_seed to self.bundle.component_seeds at 'sampling' when sampling_seed is the same
        # object as None, otherwise an integer built from sampling_seed.
        self.sampling_seed = (self.bundle.component_seeds["sampling"]
                              # Evaluate sampling_seed is the same object as None as part of the enclosing
                              # expression.
                              if sampling_seed is None else int(sampling_seed))
        # Call self.generator.manual_seed with the supplied arguments.
        self.generator.manual_seed(self.sampling_seed)
        # Set self.policy_parameter_identity to a tuple containing the text 'MAPPO_POLICY_PARAMETERS_V1', the
        # result of parameter_hash(self.bundle.proposer_actor), the...
        self.policy_parameter_identity = (
            "MAPPO_POLICY_PARAMETERS_V1",
            # Include the result of parameter_hash(self.bundle.proposer_actor) in this tuple.
            parameter_hash(self.bundle.proposer_actor),
            # Include the result of parameter_hash(self.bundle.responder_actor) in this tuple.
            parameter_hash(self.bundle.responder_actor))
        # Set self.protocol to the result of ClaimRelinquishmentProtocol().
        self.protocol = ClaimRelinquishmentProtocol()
        # Set self.semantic to the result of NegotiationSemanticFeatureEncoder().
        self.semantic = NegotiationSemanticFeatureEncoder()
        # Set self.pending_factors to an empty list.
        self.pending_factors = []
        # Set self.pending_critics to an empty list.
        self.pending_critics = []
        # Set self.final_factors to an empty list.
        self.final_factors = []
        # Set self.final_critics to an empty list.
        self.final_critics = []
        # Set self.batch_metadata to an empty list.
        self.batch_metadata = []
        # Set self.joint_protocol_evaluations to 0.
        self.joint_protocol_evaluations = 0
        # Set self.manual_graph_edits to 0.
        self.manual_graph_edits = 0
        # Set self.branch_enumerator_action_selections to 0.
        self.branch_enumerator_action_selections = 0

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Eligible factors using the inputs and processing steps below.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input original_edges: the supplied original edges.
    # Input negotiation_status: the supplied negotiation status.
    # Output: a tuple built from a lazy sequence of values at key for key in the sorted values from values.
    # Processing: iterate over the relevant records.
    def _eligible_factors(active_vehicle_ids, original_edges,
                          # Declare negotiation_status as input parameter.
                          negotiation_status):
        # Set graph to a dictionary containing joint_precedence_edges.
        graph = {"joint_precedence_edges": tuple(original_edges)}
        # Set values to an empty dictionary.
        values = {}
        # Iterate over the sorted values from active_vehicle_ids, binding each item to ego_id.
        for ego_id in sorted(active_vehicle_ids):
            # Set claim_set to the result of NegotiationClaimBuilder().build(ego_id, graph, negotiation_status,
            # True, True).
            claim_set = NegotiationClaimBuilder().build(
                # Supply negotiation_status to NegotiationClaimBuilder().build.
                ego_id, graph, negotiation_status, True, True)
            # Iterate over claim_set.action_masks, binding each item to mask.
            for mask in claim_set.action_masks:
                # Set key to a tuple containing mask.claim.yielding_vehicle_id, mask.claim.priority_vehicle_id.
                key = (mask.claim.yielding_vehicle_id,
                       # Include mask.claim.priority_vehicle_id in this tuple.
                       mask.claim.priority_vehicle_id)
                # Set values[key] to a tuple containing mask.claim, mask.
                values[key] = (mask.claim, mask)
        # Return a tuple built from a lazy sequence of values at key for key in the sorted values from values to
        # the caller.
        return tuple(values[key] for key in sorted(values))

    # Context using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input graph: the supplied graph.
    # Input timestamp: the supplied timestamp.
    # Input subject: the supplied subject.
    # Input mask: the supplied mask.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input protocol: the supplied protocol.
    # Output: a tuple containing the result of NegotiationPolicyContextBuilder.build(role, a tuple containing the
    # text 'LOCAL_GRAPH',...
    def _context(self, role, graph, timestamp, subject, mask,
                 # Declare regulatory_profile, protocol as input parameters.
                 regulatory_profile, protocol=None):
        # Enter the result of torch.no_grad() and run the enclosed operations within that context.
        with torch.no_grad():
            # Set encoded to the result of self.bundle.gnn(the result of to_torch_graph(graph)).
            encoded = self.bundle.gnn(to_torch_graph(graph))
        # Return a tuple containing the result of NegotiationPolicyContextBuilder.build(role, a tuple containing
        # the text 'LOCAL_GRAPH',... to the caller.
        return NegotiationPolicyContextBuilder.build(
            # Supply a tuple containing the text 'LOCAL_GRAPH', graph.ego_id, a floating-point number built from
            # timestamp to NegotiationPolicyContextBuilder.build.
            role, ("LOCAL_GRAPH", graph.ego_id, float(timestamp)), timestamp,
            # Supply regulatory_profile to NegotiationPolicyContextBuilder.build.
            encoded, subject, mask, regulatory_profile,
            # Supply graph.communication_model to NegotiationPolicyContextBuilder.build.
            graph.communication_model, protocol), encoded

    # Sample using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input batch_id: the supplied batch id.
    # Input episode_id: the supplied episode id.
    # Input scenario_id: the supplied scenario id.
    # Input critic_sample_id: the supplied critic sample id.
    # Output: the result of MAPPOPolicyFactorSample(event_id, batch_id, episode_id, scenario_id, context.ego_id,
    # context.decision_role.value,...).
    def _sample(self, context, batch_id, episode_id, scenario_id,
                # Declare critic_sample_id as input parameter.
                critic_sample_id):
        # Enter the result of torch.no_grad() and run the enclosed operations within that context.
        with torch.no_grad():
            # Set decision to the result of self.bundle.policy.select_action(context).
            decision = self.bundle.policy.select_action(
                # Supply generator as self.generator.
                context, generator=self.generator)
        # Set event_id to a tuple containing batch_id, context.decision_role.value, context.ego_id,
        # context.claim_identity, context.proposal_id.
        event_id = (batch_id, context.decision_role.value, context.ego_id,
                    # Include context.claim_identity in this tuple.
                    context.claim_identity, context.proposal_id)
        # Return the result of MAPPOPolicyFactorSample(event_id, batch_id, episode_id, scenario_id,
        # context.ego_id, context.decision_role.value,...) to the caller.
        return MAPPOPolicyFactorSample(
            # Supply context.ego_id to MAPPOPolicyFactorSample.
            event_id, batch_id, episode_id, scenario_id, context.ego_id,
            # Supply context.decision_role.value to MAPPOPolicyFactorSample.
            context.decision_role.value, context.claim_identity,
            # Supply context.action_names to MAPPOPolicyFactorSample.
            context.proposal_id, context.action_names,
            # Supply a tuple built from a lazy sequence of a Boolean built from x for x in the result of
            # context.action_feasibility_mask.tolist() to MAPPOPolicyFactorSample.
            tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
            # Supply decision.selected_semantic_action to MAPPOPolicyFactorSample.
            decision.selected_action_index, decision.selected_semantic_action,
            # Supply a floating-point number built from the result of decision.action_log_probability.item() to
            # MAPPOPolicyFactorSample.
            float(decision.action_log_probability.item()),
            # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the
            # result of decision.action_probabilities.tolist() to MAPPOPolicyFactorSample.
            tuple(float(x) for x in decision.action_probabilities.tolist()),
            # Supply the result of tensor_snapshot(context) to MAPPOPolicyFactorSample.
            tensor_snapshot(context), critic_sample_id, None, None, None,
            # Supply self.policy_parameter_identity to MAPPOPolicyFactorSample.
            BEHAVIOR_SOURCE, self.policy_parameter_identity, True,
            # Store True under 'stochastic_masked_sample'.
            # Store False under 'argmax_used'.
            {"stochastic_masked_sample": True, "argmax_used": False,
             # Store 0 under 'future_outcome_fields'.
             # Store 0 under 'route_truth_actor_fields'.
             "future_outcome_fields": 0, "route_truth_actor_fields": 0})

    # The learned seam accepts no candidate branches or future outcomes.
    # Input scenario_id: the supplied scenario id.
    # Input episode_id: the supplied episode id.
    # Input batch_id: the supplied batch id.
    # Input source_snapshot_id: the supplied source snapshot id.
    # Input original_edges: the supplied original edges.
    # Input active_vehicle_ids: the supplied active vehicle ids.
    # Input timestamp: the supplied timestamp.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input negotiation_status: the supplied negotiation status.
    # Input encoded_graphs: the supplied encoded graphs.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def select_joint_actions(self, *, scenario_id, episode_id, batch_id,
                             # Declare source_snapshot_id, original_edges as input parameters.
                             source_snapshot_id, original_edges,
                             # Declare active_vehicle_ids, timestamp, regulatory_profile as input parameters.
                             active_vehicle_ids, timestamp, regulatory_profile,
                             # Declare negotiation_status, encoded_graphs as input parameters.
                             negotiation_status, encoded_graphs):
        """The learned seam accepts no candidate branches or future outcomes."""
        # Set factors to the result of self._eligible_factors(active_vehicle_ids, original_edges,
        # negotiation_status).
        factors = self._eligible_factors(
            # Supply active_vehicle_ids to self._eligible_factors.
            active_vehicle_ids, original_edges, negotiation_status)
        # Set encoded_by_ego to a dictionary of graph.ego_id mapped to graph for graph in encoded_graphs.
        encoded_by_ego = {graph.ego_id: graph for graph in encoded_graphs}
        # Set required_local_egos to a set of claim.ego_id for (claim, _) in factors combined with a set of
        # claim.counterparty_id for (claim, _) in factors.
        required_local_egos = {claim.ego_id for claim, _ in factors} | {
            # Evaluate claim.counterparty_id as part of the enclosing expression.
            claim.counterparty_id for claim, _ in factors}
        # Run this branch when the negation of factors or the negation of required_local_egos is at most a set
        # built from encoded_by_ego.
        if not factors or not required_local_egos <= set(encoded_by_ego):
            # Return None to the caller.
            return None

        # Set critic_id to None.
        critic_id = None
        # Run this branch when self.runtime_critic_enabled.
        if self.runtime_critic_enabled:
            # Centralized value collection is a CTDE training-only concern.
            # Enter the result of torch.no_grad() and run the enclosed operations within that context.
            with torch.no_grad():
                # Set graph_outputs to a list of the result of self.bundle.gnn(the result of
                # to_torch_graph(encoded_by_ego at ego)) for ego in the sorted values from encoded_by_ego.
                graph_outputs = [
                    # Evaluate the result of self.bundle.gnn(the result of to_torch_graph(encoded_by_ego at ego))
                    # as part of the enclosing expression.
                    self.bundle.gnn(to_torch_graph(encoded_by_ego[ego]))
                    # Evaluate the sorted values from encoded_by_ego as part of the enclosing expression.
                    for ego in sorted(encoded_by_ego)]
                # Set central to the result of CentralizedCriticInputBuilder.build(the result of torch.stack(a
                # list of item.graph_embedding for item in graph_outputs)).
                central = CentralizedCriticInputBuilder.build(torch.stack(
                    # Supply dim as 0.
                    [item.graph_embedding for item in graph_outputs], dim=0))
                # Set critic_value to a floating-point number built from the result of
                # self.bundle.centralized_critic(central).item().
                critic_value = float(
                    # Supply the result of self.bundle.centralized_critic(central).item() to float.
                    self.bundle.centralized_critic(central).item())
            # Update self.runtime_critic_calls to its current value plus 1.
            self.runtime_critic_calls += 1
            # Set critic_id to a tuple containing batch_id, the text 'CENTRALIZED_CRITIC_SAMPLE'.
            critic_id = (batch_id, "CENTRALIZED_CRITIC_SAMPLE")
            # Append the result of MAPPOCriticSample(critic_id, batch_id, a tuple built from a lazy sequence of a
            # floating-point number built from x...) to self.pending_critics.
            self.pending_critics.append(MAPPOCriticSample(
                # Supply a tuple built from a lazy sequence of a floating-point number built from x for x in the
                # result of central.tolist() to MAPPOCriticSample.
                critic_id, batch_id, tuple(float(x) for x in central.tolist()),
                # Supply critic_value to MAPPOCriticSample.
                critic_value, None, None, None))

        # Set (proposals, proposer_pairs, proposer_masks) to a tuple containing an empty list, an empty list, an
        # empty list.
        proposals, proposer_pairs, proposer_masks = [], [], []
        # Set proposer_samples to an empty list.
        proposer_samples = []
        # Iterate over factors, binding each item to (claim, mask).
        for claim, mask in factors:
            # Set graph to encoded_by_ego at claim.ego_id.
            graph = encoded_by_ego[claim.ego_id]
            # Set subject to the result of self.semantic.encode_claim(graph, claim.ego_id, a tuple containing
            # claim.yielding_vehicle_id, claim.priority_vehicle_id).
            subject = self.semantic.encode_claim(
                # Supply claim.ego_id to self.semantic.encode_claim.
                graph, claim.ego_id,
                # Supply a tuple containing claim.yielding_vehicle_id, claim.priority_vehicle_id to
                # self.semantic.encode_claim.
                (claim.yielding_vehicle_id, claim.priority_vehicle_id))
            # Set (context, _) to the result of self._context(NegotiationDecisionRole.PROPOSER, graph, timestamp,
            # subject, mask.feasibility, regulatory_profile).
            context, _ = self._context(
                # Supply NegotiationDecisionRole.PROPOSER to self._context.
                NegotiationDecisionRole.PROPOSER, graph, timestamp, subject,
                # Supply regulatory_profile to self._context.
                mask.feasibility, regulatory_profile)
            # Set sample to the result of self._sample(context, batch_id, episode_id, scenario_id, critic_id).
            sample = self._sample(
                # Supply scenario_id to self._sample.
                context, batch_id, episode_id, scenario_id, critic_id)
            # Append sample to proposer_samples.
            proposer_samples.append(sample)
            # Set claim_identity to a tuple containing claim.yielding_vehicle_id, claim.priority_vehicle_id.
            claim_identity = (claim.yielding_vehicle_id,
                              # Include claim.priority_vehicle_id in this tuple.
                              claim.priority_vehicle_id)
            # Append a tuple containing claim_identity, sample.selected_semantic_action to proposer_pairs.
            proposer_pairs.append((claim_identity,
                                   # Include sample.selected_semantic_action in this tuple.
                                   sample.selected_semantic_action))
            # Append a tuple containing claim_identity, a tuple built from mask.feasibility to proposer_masks.
            proposer_masks.append((claim_identity, tuple(mask.feasibility)))
            # Run this branch when sample.selected_semantic_action equals the text 'RELINQUISH_CLAIM'.
            if sample.selected_semantic_action == "RELINQUISH_CLAIM":
                # Append the result of self.protocol.create_proposal(claim, timestamp, regulatory_profile,
                # mask.policy_authority) to proposals.
                proposals.append(self.protocol.create_proposal(
                    # Supply mask.policy_authority to self.protocol.create_proposal.
                    claim, timestamp, regulatory_profile, mask.policy_authority))
        # Call proposals.sort with the supplied arguments.
        proposals.sort(key=lambda item: item.proposal_id)

        # The proposal set is complete before any response context is built.
        # Set (responses, response_pairs, response_masks) to a tuple containing an empty list, an empty list, an
        # empty list.
        responses, response_pairs, response_masks = [], [], []
        # Set responder_samples to an empty list.
        responder_samples = []
        # Iterate over proposals, binding each item to proposal.
        for proposal in proposals:
            # Set candidate to the result of NegotiationResponseCandidateBuilder.build(proposal.receiver_id,
            # proposal, original_edges, timestamp, regulatory_profile, True, True).
            candidate = NegotiationResponseCandidateBuilder.build(
                # Supply proposal.receiver_id to NegotiationResponseCandidateBuilder.build.
                proposal.receiver_id, proposal, original_edges, timestamp,
                # Supply regulatory_profile to NegotiationResponseCandidateBuilder.build.
                regulatory_profile, True, True)
            # Set graph to encoded_by_ego at proposal.receiver_id.
            graph = encoded_by_ego[proposal.receiver_id]
            # Set subject to the result of self.semantic.encode_proposal(graph, proposal.receiver_id, proposal).
            subject = self.semantic.encode_proposal(
                # Supply proposal.receiver_id to self.semantic.encode_proposal.
                graph, proposal.receiver_id, proposal)
            # Set protocol to the result of self.semantic.encode_protocol_state(candidate.protocol_state, True).
            protocol = self.semantic.encode_protocol_state(
                # Supply candidate.protocol_state to self.semantic.encode_protocol_state.
                candidate.protocol_state, True)
            # Set (context, _) to the result of self._context(NegotiationDecisionRole.RESPONDER, graph, timestamp,
            # subject, candidate.action_feasibility_mask,...).
            context, _ = self._context(
                # Supply NegotiationDecisionRole.RESPONDER to self._context.
                NegotiationDecisionRole.RESPONDER, graph, timestamp, subject,
                # Supply candidate.action_feasibility_mask to self._context.
                candidate.action_feasibility_mask, regulatory_profile,
                # Supply protocol to self._context.
                protocol)
            # Set sample to the result of self._sample(context, batch_id, episode_id, scenario_id, critic_id).
            sample = self._sample(
                # Supply scenario_id to self._sample.
                context, batch_id, episode_id, scenario_id, critic_id)
            # Append sample to responder_samples.
            responder_samples.append(sample)
            # Set action to sample.selected_semantic_action.
            action = sample.selected_semantic_action
            # Set semantic to ProposalResponse.ACCEPT when action equals the text 'ACCEPT_RELINQUISHMENT',
            # otherwise ProposalResponse.REJECT.
            semantic = (ProposalResponse.ACCEPT if action ==
                        # Evaluate ProposalResponse.REJECT as part of the enclosing expression.
                        "ACCEPT_RELINQUISHMENT" else ProposalResponse.REJECT)
            # Append the result of self.protocol.create_response(proposal, proposal.receiver_id, semantic,
            # timestamp, regulatory_profile) to responses.
            responses.append(self.protocol.create_response(
                # Supply proposal.receiver_id to self.protocol.create_response.
                proposal, proposal.receiver_id, semantic, timestamp,
                # Supply regulatory_profile to self.protocol.create_response.
                regulatory_profile))
            # Append a tuple containing proposal.proposal_id, action to response_pairs.
            response_pairs.append((proposal.proposal_id, action))
            # Append a tuple containing proposal.proposal_id, a tuple built from candidate.action_feasibility_mask
            # to response_masks.
            response_masks.append((proposal.proposal_id,
                                   # Include a tuple built from candidate.action_feasibility_mask in this tuple.
                                   tuple(candidate.action_feasibility_mask)))

        # Set messages to a tuple built from proposals plus responses.
        messages = tuple(proposals + responses)
        # Set protocol_snapshot to the result of self.protocol.evaluate_all_claims(original_edges, messages,
        # timestamp, regulatory_profile, True, True).
        protocol_snapshot = self.protocol.evaluate_all_claims(
            # Supply regulatory_profile to self.protocol.evaluate_all_claims.
            original_edges, messages, timestamp, regulatory_profile, True, True)
        # Update self.joint_protocol_evaluations to its current value plus 1.
        self.joint_protocol_evaluations += 1
        # Set graph to protocol_snapshot.effective_coordination_graph.
        graph = protocol_snapshot.effective_coordination_graph
        # Set analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(a tuple built from the sorted
        # values from active_vehicle_ids, a tuple built from a lazy sequence...).
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            # Supply a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
            # priority_vehicle_id for (a, b) in graph to RegulatoryPrecedenceGraphBuilder.analyse.
            tuple(sorted(active_vehicle_ids)), tuple(
                # Store a under 'yielding_vehicle_id'.
                # Store b under 'priority_vehicle_id'.
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                # Evaluate graph as part of the enclosing expression.
                for a, b in graph))
        # Set cyclic to a Boolean built from analysis at 'cycle_detected'.
        cyclic = bool(analysis["cycle_detected"])
        # Run this branch when protocol_snapshot.protocol_disagreements.
        if protocol_snapshot.protocol_disagreements:
            # Set status to the text 'JOINT_POLICY_PROTOCOL_DISAGREEMENT'.
            status = "JOINT_POLICY_PROTOCOL_DISAGREEMENT"
        # Run this branch when protocol_snapshot.blocked_protocol_items.
        elif protocol_snapshot.blocked_protocol_items:
            # Set status to the text 'JOINT_POLICY_PROTOCOL_BLOCKED'.
            status = "JOINT_POLICY_PROTOCOL_BLOCKED"
        # Run this branch when cyclic.
        elif cyclic:
            # Set status to the text 'EXECUTION_BLOCKED_PRECEDENCE_CYCLE'.
            status = "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set status to the text 'JOINT_POLICY_EXECUTABLE_ACYCLIC'.
            status = "JOINT_POLICY_EXECUTABLE_ACYCLIC"
        # Set proposer_assignment to the result of JointProposerActionAssignment(source_snapshot_id, a tuple built
        # from proposer_pairs, a tuple built from a lazy sequence of a...).
        proposer_assignment = JointProposerActionAssignment(
            # Supply a tuple built from proposer_pairs to JointProposerActionAssignment.
            source_snapshot_id, tuple(proposer_pairs),
            # Supply a tuple built from a lazy sequence of a tuple containing claim.yielding_vehicle_id,
            # claim.priority_vehicle_id for (claim, _) in factors to JointProposerActionAssignment.
            tuple((claim.yielding_vehicle_id, claim.priority_vehicle_id)
                  # Supply a tuple built from proposer_masks to JointProposerActionAssignment.
                  for claim, _ in factors), tuple(proposer_masks),
            # Supply a tuple built from a lazy sequence of item.proposal_id for item in proposals to
            # JointProposerActionAssignment.
            tuple(item.proposal_id for item in proposals), BEHAVIOR_SOURCE,
            # Store True under 'all_proposer_actions_before_responder_contexts'.
            {"all_proposer_actions_before_responder_contexts": True})
        # Set responder_assignment to the result of JointResponderActionAssignment(source_snapshot_id, a tuple
        # built from a lazy sequence of item.proposal_id for item in...).
        responder_assignment = JointResponderActionAssignment(
            # Supply a tuple built from a lazy sequence of item.proposal_id for item in proposals to
            # JointResponderActionAssignment.
            source_snapshot_id, tuple(item.proposal_id for item in proposals),
            # Supply a tuple built from response_pairs to JointResponderActionAssignment.
            tuple(response_pairs), tuple(response_masks), BEHAVIOR_SOURCE,
            # Store True under 'all_proposals_frozen_before_responses'.
            {"all_proposals_frozen_before_responses": True})
        # Set outcome_id to a tuple containing the text 'MAPPO_POLICY_OUTCOME_V1', source_snapshot_id, a tuple
        # built from proposer_pairs, a tuple built...
        outcome_id = ("MAPPO_POLICY_OUTCOME_V1", source_snapshot_id,
                     # Include a tuple built from proposer_pairs in this tuple.
                     tuple(proposer_pairs), tuple(response_pairs))
        # Set outcome to the result of MAPPOJointPolicyOutcome(outcome_id, scenario_id, source_snapshot_id,
        # proposer_assignment, responder_assignment,...).
        outcome = MAPPOJointPolicyOutcome(
            # Supply proposer_assignment to MAPPOJointPolicyOutcome.
            outcome_id, scenario_id, source_snapshot_id, proposer_assignment,
            # Supply responder_assignment to MAPPOJointPolicyOutcome.
            responder_assignment, messages,
            # Supply a tuple built from a lazy sequence of item.proposal_id for item in
            # protocol_snapshot.completed_agreements to MAPPOJointPolicyOutcome.
            tuple(item.proposal_id for item in
                  # Evaluate protocol_snapshot.completed_agreements as part of the enclosing expression.
                  protocol_snapshot.completed_agreements),
            # Supply a tuple built from a lazy sequence of item.proposal_id for item in
            # protocol_snapshot.rejected_proposals to MAPPOJointPolicyOutcome.
            tuple(item.proposal_id for item in
                  # Evaluate protocol_snapshot.rejected_proposals as part of the enclosing expression.
                  protocol_snapshot.rejected_proposals),
            # Supply a tuple built from a lazy sequence of item.proposal_id for item in
            # protocol_snapshot.pending_proposals to MAPPOJointPolicyOutcome.
            tuple(item.proposal_id for item in
                  # Evaluate protocol_snapshot.pending_proposals as part of the enclosing expression.
                  protocol_snapshot.pending_proposals),
            # Supply protocol_snapshot.original_regulatory_precedence_graph to MAPPOJointPolicyOutcome.
            protocol_snapshot.original_regulatory_precedence_graph, graph,
            # Supply a tuple built from a lazy sequence of a tuple built from x for x in analysis at
            # 'strongly_connected_components' to MAPPOJointPolicyOutcome.
            tuple(tuple(x) for x in analysis["strongly_connected_components"]),
            # Supply the result of MappingProxyType(a dictionary containing joint_protocol_evaluations,
            # manual_graph_edits,...) to MAPPOJointPolicyOutcome.
            cyclic, status, BEHAVIOR_SOURCE, MappingProxyType({
                # Store 1 under 'joint_protocol_evaluations'.
                # Store 0 under 'manual_graph_edits'.
                "joint_protocol_evaluations": 1, "manual_graph_edits": 0,
                # Store 0 under 'branch_enumerator_action_selection'.
                "branch_enumerator_action_selection": 0,
                # Store 0 under 'future_outcome_action_selection_fields'.
                "future_outcome_action_selection_fields": 0,
                # Store 0 under 'movement_truth_fields'.
                # Store 0 under 'planner_fields'.
                "movement_truth_fields": 0, "planner_fields": 0}))
        # Set samples to a tuple built from proposer_samples plus responder_samples.
        samples = tuple(proposer_samples + responder_samples)
        # Extend self.pending_factors with samples.
        self.pending_factors.extend(samples)
        # Append a dictionary containing batch_id, episode_id, scenario_id, proposer_count, responder_count,
        # proposal_count,... to self.batch_metadata.
        self.batch_metadata.append({
            # Store batch_id under 'batch_id'.
            # Store episode_id under 'episode_id'.
            "batch_id": batch_id, "episode_id": episode_id,
            # Store scenario_id under 'scenario_id'.
            "scenario_id": scenario_id,
            # Store the number of entries in proposer_samples under 'proposer_count'.
            "proposer_count": len(proposer_samples),
            # Store the number of entries in responder_samples under 'responder_count'.
            "responder_count": len(responder_samples),
            # Store the number of entries in proposals under 'proposal_count'.
            # Store cyclic under 'cycle_detected'.
            "proposal_count": len(proposals), "cycle_detected": cyclic,
            # Store a tuple built from graph under 'effective_graph'.
            "effective_graph": tuple(graph),
            # Store a tuple built from a lazy sequence of a tuple containing x.selected_semantic_action,
            # x.behavior_policy_log_probability for x in proposer_samples under 'proposer_trace'.
            "proposer_trace": tuple((x.selected_semantic_action,
                                      # Include x.behavior_policy_log_probability in this tuple.
                                      x.behavior_policy_log_probability)
                                     # Evaluate proposer_samples as part of the enclosing expression.
                                     for x in proposer_samples),
            # Store a tuple built from a lazy sequence of a tuple containing x.selected_semantic_action,
            # x.behavior_policy_log_probability for x in responder_samples under 'responder_trace'.
            "responder_trace": tuple((x.selected_semantic_action,
                                       # Include x.behavior_policy_log_probability in this tuple.
                                       x.behavior_policy_log_probability)
                                      # Evaluate responder_samples as part of the enclosing expression.
                                      for x in responder_samples)})
        # Return outcome to the caller.
        return outcome

    # Record physical interpretation using the inputs and processing steps below.
    # Input batch_id: the supplied batch id.
    # Input obligation_set: the supplied obligation set.
    # Input plan: the supplied plan.
    # Output: no explicit value; normal completion returns None.
    def record_physical_interpretation(self, batch_id, obligation_set, plan):
        # Set record to the next item from a lazy sequence of item for item in self.batch_metadata; retain entries
        # satisfying item at 'batch_id' equals batch_id.
        record = next(item for item in self.batch_metadata
                      # Evaluate item at 'batch_id' equals batch_id as part of the enclosing expression.
                      if item["batch_id"] == batch_id)
        # Update record with the supplied entries.
        record.update({
            # Store the number of entries in obligation_set.source_effective_coordination_graph under
            # 'coordination_edge_count'.
            "coordination_edge_count": len(
                # Supply obligation_set.source_effective_coordination_graph to len.
                obligation_set.source_effective_coordination_graph),
            # Store the number of entries in obligation_set.physical_execution_graph under
            # 'physical_execution_edge_count'.
            "physical_execution_edge_count": len(
                # Supply obligation_set.physical_execution_graph to len.
                obligation_set.physical_execution_graph),
            # Store the number of entries in obligation_set.nonphysical_coordination_edges under
            # 'nonphysical_coordination_edge_count'.
            "nonphysical_coordination_edge_count": len(
                # Supply obligation_set.nonphysical_coordination_edges to len.
                obligation_set.nonphysical_coordination_edges),
            "coordination_cycle_detected":
                # Evaluate obligation_set.coordination_cycle_detected as part of the enclosing expression.
                obligation_set.coordination_cycle_detected,
            "physical_execution_cycle_detected":
                # Evaluate obligation_set.physical_execution_cycle_detected as part of the enclosing expression.
                obligation_set.physical_execution_cycle_detected,
            "physical_execution_graph":
                # Evaluate obligation_set.physical_execution_graph as part of the enclosing expression.
                obligation_set.physical_execution_graph,
            # Store obligation_set.edge_interpretations under 'edge_interpretations'.
            "edge_interpretations": obligation_set.edge_interpretations,
            # Store plan.graph_status equals the text 'EXECUTABLE' under 'graph_executable'.
            "graph_executable": plan.graph_status == "EXECUTABLE"})

    # Coupled factor records using the inputs and processing steps below.
    # Input batch_id: the supplied batch id.
    # Input shape: the supplied shape.
    # Output: a tuple built from a lazy sequence of the result of
    # CoupledPolicyFactorRecord(item.decision_event_id, batch_id, item.ego_id, item.decision_role,
    # item.claim_identity,...) for item in...
    def coupled_factor_records(self, batch_id, shape):
        # Import CoupledPolicyFactorRecord from .models for the operations below.
        from .models import CoupledPolicyFactorRecord

        # Return a tuple built from a lazy sequence of the result of
        # CoupledPolicyFactorRecord(item.decision_event_id, batch_id, item.ego_id, item.decision_role,
        # item.claim_identity,...) for item in self.pending_factors; retain entries satisfying item.joint_batch_id
        # equals batch_id to the caller.
        return tuple(CoupledPolicyFactorRecord(
            # Supply item.decision_event_id to CoupledPolicyFactorRecord.
            item.decision_event_id, batch_id, item.ego_id, item.decision_role,
            # Supply item.claim_identity to CoupledPolicyFactorRecord.
            item.claim_identity, item.proposal_id, item.action_names,
            # Supply item.selected_semantic_action to CoupledPolicyFactorRecord.
            item.hard_action_mask, item.selected_semantic_action,
            # Supply BEHAVIOR_SOURCE to CoupledPolicyFactorRecord.
            BEHAVIOR_SOURCE, True, shape[0],
            # Supply a tuple containing the number of entries in
            # item.actor_observation_snapshot.subject_representation to CoupledPolicyFactorRecord.
            (len(item.actor_observation_snapshot.subject_representation),),
            # Supply a tuple containing the number of entries in
            # item.actor_observation_snapshot.protocol_representation when
            # item.actor_observation_snapshot.protocol_representation is a different object from None, otherwise
            # None to CoupledPolicyFactorRecord.
            ((len(item.actor_observation_snapshot.protocol_representation),)
             # Evaluate item.actor_observation_snapshot.protocol_representation is a different object from None as
             # part of the enclosing expression.
             if item.actor_observation_snapshot.protocol_representation is not None
             # Supply None to the enclosing expression.
             else None), None, None,
            # Store item.behavior_policy_log_probability under 'behavior_log_probability'.
            {"behavior_log_probability": item.behavior_policy_log_probability,
             # Store 0 under 'route_truth_policy_leakage'.
             "route_truth_policy_leakage": 0})
            # Evaluate item.joint_batch_id equals batch_id as part of the enclosing expression.
            for item in self.pending_factors if item.joint_batch_id == batch_id)

    # Finalize episode using the inputs and processing steps below.
    # Input episode_id: the supplied episode id.
    # Input reward: the supplied reward.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def finalize_episode(self, episode_id, reward):
        # Set episode_factors to a list of x for x in self.pending_factors; retain entries satisfying x.episode_id
        # equals episode_id.
        episode_factors = [x for x in self.pending_factors
                           # Evaluate x.episode_id equals episode_id as part of the enclosing expression.
                           if x.episode_id == episode_id]
        # Set batch_ids to a tuple built from the result of dict.fromkeys(a lazy sequence of x.joint_batch_id for
        # x in episode_factors).
        batch_ids = tuple(dict.fromkeys(x.joint_batch_id for x in episode_factors))
        # Run this branch when the negation of batch_ids.
        if not batch_ids:
            # Return no value to the caller.
            return
        # Set terminal to a tuple containing episode_id, the text 'EPISODE_TERMINATION'.
        terminal = (episode_id, "EPISODE_TERMINATION")
        # Set records to an empty list.
        records = []
        # Iterate over index/value pairs from batch_ids, binding each item to (index, batch_id).
        for index, batch_id in enumerate(batch_ids):
            # Set successor to batch_ids at index + 1 when index plus 1 is less than the number of entries in
            # batch_ids, otherwise terminal.
            successor = batch_ids[index + 1] if index + 1 < len(batch_ids) else terminal
            # Set batch_reward to reward when index equals the number of entries in batch_ids minus 1, otherwise
            # 0.0.
            batch_reward = reward if index == len(batch_ids) - 1 else 0.0
            # Append the result of TeamObjectiveRecord(a tuple containing batch_id, successor, the text
            # 'STEP_5H_INTERVAL', batch_id, successor, the...) to records.
            records.append(TeamObjectiveRecord(
                # Supply a tuple containing batch_id, successor, the text 'STEP_5H_INTERVAL' to
                # TeamObjectiveRecord.
                (batch_id, successor, "STEP_5H_INTERVAL"), batch_id,
                # Supply REWARD_DEFINITION_ID to TeamObjectiveRecord.
                successor, -batch_reward, batch_reward, REWARD_DEFINITION_ID,
                # Store the text '0' under 'new_reward_terms'.
                "negative vehicle-seconds", {"new_reward_terms": "0"}))
        # Set returns to the result of EpisodicTeamReturnCalculator().compute(records, terminal, the result of
        # repr(episode_id)).
        returns = EpisodicTeamReturnCalculator().compute(
            # Supply the result of repr(episode_id) to EpisodicTeamReturnCalculator().compute.
            records, terminal, repr(episode_id))
        # Iterate over a list of x for x in self.pending_critics; retain entries satisfying x.joint_batch_id
        # belongs to batch_ids, binding each item to critic.
        for critic in [x for x in self.pending_critics
                       # Evaluate x.joint_batch_id belongs to batch_ids as part of the enclosing expression.
                       if x.joint_batch_id in batch_ids]:
            # Set return_record to returns at critic.joint_batch_id.
            return_record = returns[critic.joint_batch_id]
            # Set target to the result of CentralizedAdvantageCalculator.value_target(return_record, a tuple
            # containing critic.value_at_collection).
            target = CentralizedAdvantageCalculator.value_target(
                # Supply a tuple containing critic.value_at_collection to
                # CentralizedAdvantageCalculator.value_target.
                return_record, (critic.value_at_collection,))
            # Set advantage to the result of CentralizedAdvantageCalculator.advantage(return_record, target).
            advantage = CentralizedAdvantageCalculator.advantage(
                # Supply return_record to CentralizedAdvantageCalculator.advantage.
                return_record, target)
            # Append the result of replace(critic) to self.final_critics.
            self.final_critics.append(replace(
                # Supply return_record_id as return_record.return_record_id.
                critic, return_record_id=return_record.return_record_id,
                # Supply target_return as return_record.undiscounted_team_return.
                target_return=return_record.undiscounted_team_return,
                # Supply value_error as target.value_error.
                value_error=target.value_error))
            # Iterate over a list of x for x in episode_factors; retain entries satisfying x.joint_batch_id equals
            # critic.joint_batch_id, binding each item to factor.
            for factor in [x for x in episode_factors
                           # Evaluate x.joint_batch_id equals critic.joint_batch_id as part of the enclosing
                           # expression.
                           if x.joint_batch_id == critic.joint_batch_id]:
                # Append the result of replace(factor) to self.final_factors.
                self.final_factors.append(replace(
                    # Supply return_record_id as return_record.return_record_id.
                    factor, return_record_id=return_record.return_record_id,
                    # Supply advantage_record_id as advantage.advantage_record_id.
                    advantage_record_id=advantage.advantage_record_id,
                    # Supply advantage as advantage.advantage.
                    advantage=advantage.advantage))

    # Replay all using the inputs and processing steps below.
    # Output: a tuple built from a lazy sequence of the result of
    # evaluate_policy_factor_sample(self.bundle.policy, sample) for sample in self.final_factors.
    def replay_all(self):
        # Return a tuple built from a lazy sequence of the result of
        # evaluate_policy_factor_sample(self.bundle.policy, sample) for sample in self.final_factors to the
        # caller.
        return tuple(evaluate_policy_factor_sample(
            # Supply self.bundle.policy to evaluate_policy_factor_sample.
            self.bundle.policy, sample) for sample in self.final_factors)

    # Final parameter hashes using the inputs and processing steps below.
    # Output: a dictionary containing gnn, proposer, responder, critic.
    def final_parameter_hashes(self):
        # Return a dictionary containing gnn, proposer, responder, critic to the caller.
        return {"gnn": parameter_hash(self.bundle.gnn),
                # Store the result of parameter_hash(self.bundle.proposer_actor) under 'proposer'.
                "proposer": parameter_hash(self.bundle.proposer_actor),
                # Store the result of parameter_hash(self.bundle.responder_actor) under 'responder'.
                "responder": parameter_hash(self.bundle.responder_actor),
                # Store the result of parameter_hash(self.bundle.centralized_critic) under 'critic'.
                "critic": parameter_hash(self.bundle.centralized_critic)}
