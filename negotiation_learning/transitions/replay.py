"""Deterministic actor/critic reconstruction from immutable raw snapshots."""

import torch

from ..ctde import CentralizedCriticInputBuilder
from ..gnn import to_torch_graph
from ..mappo_interface import NegotiationPolicyContextBuilder
from ..semantic_encoding import NegotiationSemanticFeatureEncoder


def reconstruct_actor_context(snapshot, gnn_encoder):
    """Actor-local replay; deliberately accepts no centralized snapshot."""
    graph = snapshot.graph_observation
    gnn_output = gnn_encoder(to_torch_graph(graph))
    semantic = NegotiationSemanticFeatureEncoder()
    subject = (semantic.encode_proposal(graph, graph.ego_id, snapshot.proposal)
               if snapshot.proposal is not None else
               semantic.encode_claim(graph, graph.ego_id, snapshot.claim_identity))
    protocol = (semantic.encode_protocol_state(snapshot.protocol_state, True)
                if snapshot.decision_role.value == "RESPONDER" else None)
    context = NegotiationPolicyContextBuilder.build(
        snapshot.decision_role, snapshot.snapshot_id,
        snapshot.source_snapshot_timestamp,
        gnn_output, subject, snapshot.hard_action_feasibility_mask,
        snapshot.regulatory_profile, snapshot.communication_model, protocol,
    )
    return context, gnn_output, subject, protocol


def reconstruct_critic_input(centralized_snapshot, gnn_encoder):
    representations = []
    for actor_snapshot in centralized_snapshot.participant_actor_snapshots:
        context, _, _, _ = reconstruct_actor_context(actor_snapshot, gnn_encoder)
        representations.append(torch.cat((
            context.ego_embedding, context.local_graph_embedding,
            context.claim_or_proposal_representation,
            (context.protocol_state_representation
             if context.protocol_state_representation is not None else
             torch.zeros(0, dtype=context.ego_embedding.dtype)),
        )))
    dimensions = {item.shape[-1] for item in representations}
    if len(dimensions) != 1:
        raise ValueError("CENTRALIZED_PARTICIPANT_REPRESENTATION_DIMENSION_MISMATCH")
    return CentralizedCriticInputBuilder.build(torch.stack(representations, dim=0))
