"""Baseline semantic actions composed by the existing agreement protocol."""
from types import SimpleNamespace
from panel_demo.inference import PanelDeterministicInferenceProvider

def fcfs_action(role, claim, arrivals, mask):
    """Relinquish only one's authorized claim; never remove an outgoing duty."""
    if role == "RESPONDER":
        preferred = 0  # Explicit acceptance, existing protocol checks still apply.
    else:
        yielding, priority = claim
        rank = lambda ego: (arrivals.get(ego, float("inf")), ego)
        preferred = int(rank(yielding) < rank(priority))
    return preferred if mask[preferred] else next(i for i, allowed in enumerate(mask) if allowed)

class FCFSProvider(PanelDeterministicInferenceProvider):
    uses_mappo_behavior_policy = False
    selection_rule = "AUTHORIZED_CLAIM_FCFS_EXPLICIT_ACCEPTANCE"

    def __init__(self, bundle, arrivals):
        super().__init__(bundle, sampling_seed=0)
        self.arrivals = arrivals

    def _context(self, role, graph, timestamp, subject, mask, regulatory_profile, protocol=None):
        # Symbolic metadata only. No baseline GNN or learned actor forward.
        return SimpleNamespace(decision_role=role, ego_id=subject.ego_id,
            claim_identity=subject.claim_identity, proposal_id=subject.proposal_id,
            action_feasibility_mask=tuple(mask)), None

    def _sample(self, context, batch_id, episode_id, scenario_id, critic_sample_id):
        role = context.decision_role.value
        names = ("KEEP_CLAIM", "RELINQUISH_CLAIM") if role == "PROPOSER" else (
            "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")
        index = fcfs_action(role, context.claim_identity, self.arrivals,
                            context.action_feasibility_mask)
        return SimpleNamespace(joint_batch_id=batch_id, selected_semantic_action=names[index],
            behavior_policy_log_probability=0., decision_role=role, ego_id=context.ego_id,
            claim_identity=context.claim_identity, proposal_id=context.proposal_id,
            action_names=names, hard_action_mask=context.action_feasibility_mask,
            behavior_probability_vector=tuple(float(i == index) for i in range(2)),
            selected_action_index=index)

class RulesOnlyProvider(FCFSProvider):
    rules_only = True
    selection_rule = "NO_NEGOTIATION_UNRESOLVED_SAFE_HOLD"

    def select_joint_actions(self, **kwargs):
        return None
