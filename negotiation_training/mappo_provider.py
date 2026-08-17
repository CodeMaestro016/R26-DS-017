"""Real stochastic MAPPO behavior provider; collection only, no optimizer."""

import hashlib
from dataclasses import dataclass, replace
from types import MappingProxyType

import torch

from experimentation import ScenarioRole, build_design
from negotiation_learning.claim_semantics import NegotiationClaimBuilder
from negotiation_learning.ctde import (
    CentralizedCriticInputBuilder, CentralizedNegotiationCritic,
    DecentralizedNegotiationActor, DecentralizedNegotiationResponseActor)
from negotiation_learning.gnn import EdgeAwareMPNNEncoder, to_torch_graph
from negotiation_learning.joint_negotiation import (
    JointNegotiationBranchResult, JointProposerActionAssignment,
    JointResponderActionAssignment)
from negotiation_learning.mappo_interface import (
    NegotiationDecisionRole, NegotiationPolicyContextBuilder,
    RoleAwareNegotiationPolicy)
from negotiation_learning.models import NegotiationAction
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
from negotiation_learning.protocol import (
    ClaimRelinquishmentProtocol, NegotiationResponseAction,
    NegotiationResponseCandidateBuilder, ProposalResponse)
from negotiation_learning.semantic_encoding import NegotiationSemanticFeatureEncoder
from negotiation_learning.mappo_returns import (
    CentralizedAdvantageCalculator, EpisodicTeamReturnCalculator)
from negotiation_objective.models import (
    REWARD_DEFINITION_ID, TeamObjectiveRecord)

from .adam_contract import build_mechanical_adam_optimization_contract
from .architecture_contract import (
    apply_explicit_mechanical_initialization,
    build_mechanical_pilot_architecture_contract,
    deterministic_initialization_seed)
from .rollout import (
    MAPPOBehaviorRolloutIdentity, MAPPOCriticSample, MAPPOPolicyFactorSample,
    evaluate_policy_factor_sample, parameter_hash, tensor_snapshot)


BEHAVIOR_SOURCE = "MAPPO_BEHAVIOR_POLICY"
BEHAVIOR_RULE = "STOCHASTIC_MASKED_ROLE_POLICY_NO_BRANCH_ENUMERATION"


@dataclass(frozen=True)
class MechanicalMAPPOBehaviorPolicyBundle:
    gnn: object
    proposer_actor: object
    responder_actor: object
    centralized_critic: object
    policy: object
    architecture_contract_id: tuple
    optimization_contract_id: tuple
    behavior_rollout_identity: MAPPOBehaviorRolloutIdentity
    component_seeds: MappingProxyType
    initial_parameter_hashes: MappingProxyType
    policy_parameter_identity: tuple


def build_behavior_rollout_identity():
    design = build_design()
    architecture = build_mechanical_pilot_architecture_contract()
    optimization = build_mechanical_adam_optimization_contract()
    manifest = design["manifests"][ScenarioRole.TRAINING]
    fields = (design["freeze"].freeze_id, architecture.contract_id,
              optimization.contract_id, manifest.manifest_id, "STEP_5J_3B_3")
    digest = hashlib.sha256(repr(fields).encode()).hexdigest()
    return MAPPOBehaviorRolloutIdentity(
        ("MAPPO_BEHAVIOR_ROLLOUT_V1", digest), design["freeze"].freeze_id,
        architecture.contract_id, optimization.contract_id,
        manifest.manifest_id)


def build_mechanical_mappo_behavior_policy_bundle():
    identity = build_behavior_rollout_identity()
    architecture = build_mechanical_pilot_architecture_contract()
    components = {
        "gnn": EdgeAwareMPNNEncoder(
            8, 9, architecture.gnn_hidden_dimension,
            architecture.gnn_message_passing_layers),
        "proposer": DecentralizedNegotiationActor(
            architecture.proposer_input_dimension, 2),
        "responder": DecentralizedNegotiationResponseActor(
            architecture.responder_input_dimension, 2),
        "critic": CentralizedNegotiationCritic(
            architecture.critic_input_dimension),
    }
    labels = {
        "gnn": "MODEL_INITIALIZATION_GNN",
        "proposer": "MODEL_INITIALIZATION_PROPOSER",
        "responder": "MODEL_INITIALIZATION_RESPONDER",
        "critic": "MODEL_INITIALIZATION_CRITIC",
        "sampling": "POLICY_ACTION_SAMPLING",
    }
    seeds = {name: deterministic_initialization_seed(
        architecture.contract_id, (identity.rollout_id, label))
        for name, label in labels.items()}
    for name, module in components.items():
        apply_explicit_mechanical_initialization(module, seeds[name])
    for parameter in components["gnn"].parameters():
        parameter.requires_grad_(False)
    hashes = {name: parameter_hash(module) for name, module in components.items()}
    policy_identity = ("MAPPO_POLICY_PARAMETERS_V1", hashes["proposer"],
                       hashes["responder"])
    policy = RoleAwareNegotiationPolicy(
        components["proposer"], components["responder"])
    return MechanicalMAPPOBehaviorPolicyBundle(
        components["gnn"], components["proposer"], components["responder"],
        components["critic"], policy, architecture.contract_id,
        identity.optimization_contract_id, identity,
        MappingProxyType(seeds), MappingProxyType(hashes), policy_identity)


class MAPPOBehaviorActionProvider:
    """Sample current role factors and compose one actual protocol outcome."""

    selection_rule = BEHAVIOR_RULE
    outcome_data_used = False
    uses_mappo_behavior_policy = True

    def __init__(self, bundle=None):
        self.bundle = bundle or build_mechanical_mappo_behavior_policy_bundle()
        self.generator = torch.Generator(device="cpu")
        self.generator.manual_seed(self.bundle.component_seeds["sampling"])
        self.protocol = ClaimRelinquishmentProtocol()
        self.semantic = NegotiationSemanticFeatureEncoder()
        self.pending_factors = []
        self.pending_critics = []
        self.final_factors = []
        self.final_critics = []
        self.batch_metadata = []
        self.joint_protocol_evaluations = 0
        self.manual_graph_edits = 0
        self.branch_enumerator_action_selections = 0

    @staticmethod
    def _eligible_factors(active_vehicle_ids, original_edges,
                          negotiation_status):
        graph = {"joint_precedence_edges": tuple(original_edges)}
        values = {}
        for ego_id in sorted(active_vehicle_ids):
            claim_set = NegotiationClaimBuilder().build(
                ego_id, graph, negotiation_status, True, True)
            for mask in claim_set.action_masks:
                key = (mask.claim.yielding_vehicle_id,
                       mask.claim.priority_vehicle_id)
                values[key] = (mask.claim, mask)
        return tuple(values[key] for key in sorted(values))

    def _context(self, role, graph, timestamp, subject, mask,
                 regulatory_profile, protocol=None):
        with torch.no_grad():
            encoded = self.bundle.gnn(to_torch_graph(graph))
        return NegotiationPolicyContextBuilder.build(
            role, ("LOCAL_GRAPH", graph.ego_id, float(timestamp)), timestamp,
            encoded, subject, mask, regulatory_profile,
            graph.communication_model, protocol), encoded

    def _sample(self, context, batch_id, episode_id, scenario_id,
                critic_sample_id):
        with torch.no_grad():
            decision = self.bundle.policy.select_action(
                context, generator=self.generator)
        event_id = (batch_id, context.decision_role.value, context.ego_id,
                    context.claim_identity, context.proposal_id)
        return MAPPOPolicyFactorSample(
            event_id, batch_id, episode_id, scenario_id, context.ego_id,
            context.decision_role.value, context.claim_identity,
            context.proposal_id, context.action_names,
            tuple(bool(x) for x in context.action_feasibility_mask.tolist()),
            decision.selected_action_index, decision.selected_semantic_action,
            float(decision.action_log_probability.item()),
            tuple(float(x) for x in decision.action_probabilities.tolist()),
            tensor_snapshot(context), critic_sample_id, None, None, None,
            BEHAVIOR_SOURCE, self.bundle.policy_parameter_identity, True,
            {"stochastic_masked_sample": True, "argmax_used": False,
             "future_outcome_fields": 0, "route_truth_actor_fields": 0})

    def select_joint_actions(self, *, scenario_id, episode_id, batch_id,
                             source_snapshot_id, original_edges,
                             active_vehicle_ids, timestamp, regulatory_profile,
                             negotiation_status, movement_path_by_vehicle,
                             encoded_graphs, planner):
        """The learned seam accepts no candidate branches or future outcomes."""
        factors = self._eligible_factors(
            active_vehicle_ids, original_edges, negotiation_status)
        encoded_by_ego = {graph.ego_id: graph for graph in encoded_graphs}
        required_local_egos = {claim.ego_id for claim, _ in factors} | {
            claim.counterparty_id for claim, _ in factors}
        if not factors or not required_local_egos <= set(encoded_by_ego):
            return None

        # One centralized sample from current per-agent graph representations.
        with torch.no_grad():
            graph_outputs = [self.bundle.gnn(to_torch_graph(encoded_by_ego[ego]))
                             for ego in sorted(encoded_by_ego)]
            central = CentralizedCriticInputBuilder.build(torch.stack(
                [item.graph_embedding for item in graph_outputs], dim=0))
            critic_value = float(self.bundle.centralized_critic(central).item())
        critic_id = (batch_id, "CENTRALIZED_CRITIC_SAMPLE")
        self.pending_critics.append(MAPPOCriticSample(
            critic_id, batch_id, tuple(float(x) for x in central.tolist()),
            critic_value, None, None, None))

        proposals, proposer_pairs, proposer_masks = [], [], []
        proposer_samples = []
        for claim, mask in factors:
            graph = encoded_by_ego[claim.ego_id]
            subject = self.semantic.encode_claim(
                graph, claim.ego_id,
                (claim.yielding_vehicle_id, claim.priority_vehicle_id))
            context, _ = self._context(
                NegotiationDecisionRole.PROPOSER, graph, timestamp, subject,
                mask.feasibility, regulatory_profile)
            sample = self._sample(
                context, batch_id, episode_id, scenario_id, critic_id)
            proposer_samples.append(sample)
            claim_identity = (claim.yielding_vehicle_id,
                              claim.priority_vehicle_id)
            proposer_pairs.append((claim_identity,
                                   sample.selected_semantic_action))
            proposer_masks.append((claim_identity, tuple(mask.feasibility)))
            if sample.selected_semantic_action == "RELINQUISH_CLAIM":
                proposals.append(self.protocol.create_proposal(
                    claim, timestamp, regulatory_profile, mask.policy_authority))
        proposals.sort(key=lambda item: item.proposal_id)

        # The proposal set is complete before any response context is built.
        responses, response_pairs, response_masks = [], [], []
        responder_samples = []
        for proposal in proposals:
            candidate = NegotiationResponseCandidateBuilder.build(
                proposal.receiver_id, proposal, original_edges, timestamp,
                regulatory_profile, True, True)
            graph = encoded_by_ego[proposal.receiver_id]
            subject = self.semantic.encode_proposal(
                graph, proposal.receiver_id, proposal)
            protocol = self.semantic.encode_protocol_state(
                candidate.protocol_state, True)
            context, _ = self._context(
                NegotiationDecisionRole.RESPONDER, graph, timestamp, subject,
                candidate.action_feasibility_mask, regulatory_profile,
                protocol)
            sample = self._sample(
                context, batch_id, episode_id, scenario_id, critic_id)
            responder_samples.append(sample)
            action = sample.selected_semantic_action
            semantic = (ProposalResponse.ACCEPT if action ==
                        "ACCEPT_RELINQUISHMENT" else ProposalResponse.REJECT)
            responses.append(self.protocol.create_response(
                proposal, proposal.receiver_id, semantic, timestamp,
                regulatory_profile))
            response_pairs.append((proposal.proposal_id, action))
            response_masks.append((proposal.proposal_id,
                                   tuple(candidate.action_feasibility_mask)))

        messages = tuple(proposals + responses)
        protocol_snapshot = self.protocol.evaluate_all_claims(
            original_edges, messages, timestamp, regulatory_profile, True, True)
        self.joint_protocol_evaluations += 1
        graph = protocol_snapshot.effective_coordination_graph
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            tuple(sorted(active_vehicle_ids)), tuple(
                {"yielding_vehicle_id": a, "priority_vehicle_id": b}
                for a, b in graph))
        cyclic = bool(analysis["cycle_detected"])
        if protocol_snapshot.protocol_disagreements:
            status = "JOINT_POLICY_PROTOCOL_DISAGREEMENT"
        elif protocol_snapshot.blocked_protocol_items:
            status = "JOINT_POLICY_PROTOCOL_BLOCKED"
        elif cyclic:
            status = "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
        else:
            status = "JOINT_POLICY_EXECUTABLE_ACYCLIC"
        plan, physical_status = planner.classify_plan(
            source_snapshot_id=source_snapshot_id,
            effective_coordination_graph=graph,
            active_vehicle_ids=active_vehicle_ids,
            movement_path_by_vehicle=movement_path_by_vehicle,
            timestamp=timestamp, source_protocol_state=status,
            cleared_vehicle_zones=())
        if plan is None:
            raise RuntimeError((physical_status, tuple(graph),
                                tuple(sorted(movement_path_by_vehicle.items()))))
        proposer_assignment = JointProposerActionAssignment(
            source_snapshot_id, tuple(proposer_pairs),
            tuple((claim.yielding_vehicle_id, claim.priority_vehicle_id)
                  for claim, _ in factors), tuple(proposer_masks),
            tuple(item.proposal_id for item in proposals), BEHAVIOR_SOURCE,
            {"all_proposer_actions_before_responder_contexts": True})
        responder_assignment = JointResponderActionAssignment(
            source_snapshot_id, tuple(item.proposal_id for item in proposals),
            tuple(response_pairs), tuple(response_masks), BEHAVIOR_SOURCE,
            {"all_proposals_frozen_before_responses": True})
        branch_id = ("MAPPO_POLICY_OUTCOME_V1", source_snapshot_id,
                     tuple(proposer_pairs), tuple(response_pairs))
        branch = JointNegotiationBranchResult(
            branch_id, scenario_id, source_snapshot_id, proposer_assignment,
            responder_assignment, messages,
            tuple(item.proposal_id for item in
                  protocol_snapshot.completed_agreements),
            tuple(item.proposal_id for item in
                  protocol_snapshot.rejected_proposals),
            tuple(item.proposal_id for item in
                  protocol_snapshot.pending_proposals),
            protocol_snapshot.original_regulatory_precedence_graph, graph,
            tuple(tuple(x) for x in analysis["strongly_connected_components"]),
            cyclic, plan.graph_status == "EXECUTABLE", status, plan.plan_id,
            plan, BEHAVIOR_SOURCE,
            {"joint_protocol_evaluations": 1, "manual_graph_edits": 0,
             "branch_enumerator_action_selection": 0,
             "future_outcome_action_selection_fields": 0})
        samples = tuple(proposer_samples + responder_samples)
        self.pending_factors.extend(samples)
        self.batch_metadata.append({
            "batch_id": batch_id, "episode_id": episode_id,
            "scenario_id": scenario_id,
            "proposer_count": len(proposer_samples),
            "responder_count": len(responder_samples),
            "proposal_count": len(proposals), "cycle_detected": cyclic,
            "graph_executable": branch.graph_executable,
            "effective_graph": tuple(graph),
            "proposer_trace": tuple((x.selected_semantic_action,
                                      x.behavior_policy_log_probability)
                                     for x in proposer_samples),
            "responder_trace": tuple((x.selected_semantic_action,
                                       x.behavior_policy_log_probability)
                                      for x in responder_samples)})
        return branch

    def coupled_factor_records(self, batch_id, shape):
        from .models import CoupledPolicyFactorRecord

        return tuple(CoupledPolicyFactorRecord(
            item.decision_event_id, batch_id, item.ego_id, item.decision_role,
            item.claim_identity, item.proposal_id, item.action_names,
            item.hard_action_mask, item.selected_semantic_action,
            BEHAVIOR_SOURCE, True, shape[0],
            (len(item.actor_observation_snapshot.subject_representation),),
            ((len(item.actor_observation_snapshot.protocol_representation),)
             if item.actor_observation_snapshot.protocol_representation is not None
             else None), None, None,
            {"behavior_log_probability": item.behavior_policy_log_probability,
             "route_truth_policy_leakage": 0})
            for item in self.pending_factors if item.joint_batch_id == batch_id)

    def finalize_episode(self, episode_id, reward):
        episode_factors = [x for x in self.pending_factors
                           if x.episode_id == episode_id]
        batch_ids = tuple(dict.fromkeys(x.joint_batch_id for x in episode_factors))
        if not batch_ids:
            return
        terminal = (episode_id, "EPISODE_TERMINATION")
        records = []
        for index, batch_id in enumerate(batch_ids):
            successor = batch_ids[index + 1] if index + 1 < len(batch_ids) else terminal
            batch_reward = reward if index == len(batch_ids) - 1 else 0.0
            records.append(TeamObjectiveRecord(
                (batch_id, successor, "STEP_5H_INTERVAL"), batch_id,
                successor, -batch_reward, batch_reward, REWARD_DEFINITION_ID,
                "negative vehicle-seconds", {"new_reward_terms": "0"}))
        returns = EpisodicTeamReturnCalculator().compute(
            records, terminal, repr(episode_id))
        for critic in [x for x in self.pending_critics
                       if x.joint_batch_id in batch_ids]:
            return_record = returns[critic.joint_batch_id]
            target = CentralizedAdvantageCalculator.value_target(
                return_record, (critic.value_at_collection,))
            advantage = CentralizedAdvantageCalculator.advantage(
                return_record, target)
            self.final_critics.append(replace(
                critic, return_record_id=return_record.return_record_id,
                target_return=return_record.undiscounted_team_return,
                value_error=target.value_error))
            for factor in [x for x in episode_factors
                           if x.joint_batch_id == critic.joint_batch_id]:
                self.final_factors.append(replace(
                    factor, return_record_id=return_record.return_record_id,
                    advantage_record_id=advantage.advantage_record_id,
                    advantage=advantage.advantage))

    def replay_all(self):
        return tuple(evaluate_policy_factor_sample(
            self.bundle.policy, sample) for sample in self.final_factors)

    def final_parameter_hashes(self):
        return {"gnn": parameter_hash(self.bundle.gnn),
                "proposer": parameter_hash(self.bundle.proposer_actor),
                "responder": parameter_hash(self.bundle.responder_actor),
                "critic": parameter_hash(self.bundle.centralized_critic)}
