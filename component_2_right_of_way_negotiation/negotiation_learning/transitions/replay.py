"""Deterministic actor/critic reconstruction from immutable raw snapshots."""

# Import torch for use in this module.
import torch

# Import CentralizedCriticInputBuilder from ..ctde for the operations below.
from ..ctde import CentralizedCriticInputBuilder
# Import to_torch_graph from ..gnn for the operations below.
from ..gnn import to_torch_graph
# Import NegotiationPolicyContextBuilder from ..mappo_interface for the operations below.
from ..mappo_interface import NegotiationPolicyContextBuilder
# Import NegotiationSemanticFeatureEncoder from ..semantic_encoding for the operations below.
from ..semantic_encoding import NegotiationSemanticFeatureEncoder


# Actor-local replay; deliberately accepts no centralized snapshot.
# Input snapshot: the supplied snapshot.
# Input gnn_encoder: the supplied gnn encoder.
# Output: a tuple containing context, gnn_output, subject, protocol.
def reconstruct_actor_context(snapshot, gnn_encoder):
    """Actor-local replay; deliberately accepts no centralized snapshot."""
    # Set graph to snapshot.graph_observation.
    graph = snapshot.graph_observation
    # Set gnn_output to the result of gnn_encoder(the result of to_torch_graph(graph)).
    gnn_output = gnn_encoder(to_torch_graph(graph))
    # Set semantic to the result of NegotiationSemanticFeatureEncoder().
    semantic = NegotiationSemanticFeatureEncoder()
    # Set subject to the result of semantic.encode_proposal(graph, graph.ego_id, snapshot.proposal) when
    # snapshot.proposal is a different object from None, otherwise the result of semantic.encode_claim(graph,
    # graph.ego_id, snapshot.claim_identity).
    subject = (semantic.encode_proposal(graph, graph.ego_id, snapshot.proposal)
               # Evaluate snapshot.proposal is a different object from None as part of the enclosing expression.
               if snapshot.proposal is not None else
               # Evaluate the result of semantic.encode_claim(graph, graph.ego_id, snapshot.claim_identity) as
               # part of the enclosing expression.
               semantic.encode_claim(graph, graph.ego_id, snapshot.claim_identity))
    # Set protocol to the result of semantic.encode_protocol_state(snapshot.protocol_state, True) when
    # snapshot.decision_role.value equals the text 'RESPONDER', otherwise None.
    protocol = (semantic.encode_protocol_state(snapshot.protocol_state, True)
                # Evaluate snapshot.decision_role.value equals the text 'RESPONDER' as part of the enclosing
                # expression.
                if snapshot.decision_role.value == "RESPONDER" else None)
    # Set context to the result of NegotiationPolicyContextBuilder.build(snapshot.decision_role,
    # snapshot.snapshot_id, snapshot.source_snapshot_timestamp, gnn_output,...).
    context = NegotiationPolicyContextBuilder.build(
        # Supply snapshot.decision_role to NegotiationPolicyContextBuilder.build.
        snapshot.decision_role, snapshot.snapshot_id,
        # Supply snapshot.source_snapshot_timestamp to NegotiationPolicyContextBuilder.build.
        snapshot.source_snapshot_timestamp,
        # Supply snapshot.hard_action_feasibility_mask to NegotiationPolicyContextBuilder.build.
        gnn_output, subject, snapshot.hard_action_feasibility_mask,
        # Supply snapshot.communication_model to NegotiationPolicyContextBuilder.build.
        snapshot.regulatory_profile, snapshot.communication_model, protocol,
    )
    # Return a tuple containing context, gnn_output, subject, protocol to the caller.
    return context, gnn_output, subject, protocol


# Reconstruct critic input using the inputs and processing steps below.
# Input centralized_snapshot: the supplied centralized snapshot.
# Input gnn_encoder: the supplied gnn encoder.
# Output: the result of CentralizedCriticInputBuilder.build(the result of torch.stack(representations)).
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def reconstruct_critic_input(centralized_snapshot, gnn_encoder):
    # Set representations to an empty list.
    representations = []
    # Iterate over centralized_snapshot.participant_actor_snapshots, binding each item to actor_snapshot.
    for actor_snapshot in centralized_snapshot.participant_actor_snapshots:
        # Set (context, _, _, _) to the result of reconstruct_actor_context(actor_snapshot, gnn_encoder).
        context, _, _, _ = reconstruct_actor_context(actor_snapshot, gnn_encoder)
        # Append the tensors concatenated by torch.cat to representations.
        representations.append(torch.cat((
            # Include context.local_graph_embedding in this tuple.
            context.ego_embedding, context.local_graph_embedding,
            # Include context.claim_or_proposal_representation in this tuple.
            context.claim_or_proposal_representation,
            # Include context.protocol_state_representation when context.protocol_state_representation is a
            # different object from None, otherwise a zero-filled tensor with the requested shape in this tuple.
            (context.protocol_state_representation
             # Evaluate context.protocol_state_representation is a different object from None as part of the
             # enclosing expression.
             if context.protocol_state_representation is not None else
             # Supply dtype as context.ego_embedding.dtype.
             torch.zeros(0, dtype=context.ego_embedding.dtype)),
        )))
    # Set dimensions to a set of item.shape at -1 for item in representations.
    dimensions = {item.shape[-1] for item in representations}
    # Run this branch when the number of entries in dimensions differs from 1.
    if len(dimensions) != 1:
        # Raise ValueError with the text 'CENTRALIZED_PARTICIPANT_REPRESENTATION_DIMENSION_MISMATCH' to stop this
        # execution path.
        raise ValueError("CENTRALIZED_PARTICIPANT_REPRESENTATION_DIMENSION_MISMATCH")
    # Return the result of CentralizedCriticInputBuilder.build(the result of torch.stack(representations)) to the
    # caller.
    return CentralizedCriticInputBuilder.build(torch.stack(representations, dim=0))
