"""Baseline semantic actions composed by the existing agreement protocol."""
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import PanelDeterministicInferenceProvider from runtime_simulation.inference for the operations below.
from runtime_simulation.inference import PanelDeterministicInferenceProvider

# Relinquish only one's authorized claim; never remove an outgoing duty.
# Input role: the supplied role.
# Input claim: the supplied claim.
# Input arrivals: the supplied arrivals.
# Input mask: the supplied mask.
# Output: preferred when mask at preferred, otherwise the next item from a lazy sequence of i for (i, allowed) in
# index/value pairs from mask; retain entries satisfying allowed.
# Processing: select branches using the stated conditions.
def fcfs_action(role, claim, arrivals, mask):
    """Relinquish only one's authorized claim; never remove an outgoing duty."""
    # Run this branch when role equals the text 'RESPONDER'.
    if role == "RESPONDER":
        # Set preferred to 0.
        preferred = 0  # Explicit acceptance, existing protocol checks still apply.
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set (yielding, priority) to claim.
        yielding, priority = claim
        # Set rank to a callback that returns a tuple containing ego from arrivals; use a floating-point number
        # built from 'inf' if absent, ego.
        rank = lambda ego: (arrivals.get(ego, float("inf")), ego)
        # Set preferred to an integer built from the result of rank(yielding) is less than the result of
        # rank(priority).
        preferred = int(rank(yielding) < rank(priority))
    # Return preferred when mask at preferred, otherwise the next item from a lazy sequence of i for (i, allowed)
    # in index/value pairs from mask; retain entries satisfying allowed to the caller.
    return preferred if mask[preferred] else next(i for i, allowed in enumerate(mask) if allowed)

# Define FCFSProvider to group the state and operations declared below.
# Base classes: PanelDeterministicInferenceProvider.
# Instances expose the attributes and methods implemented in this class.
class FCFSProvider(PanelDeterministicInferenceProvider):
    # Set uses_mappo_behavior_policy to False.
    uses_mappo_behavior_policy = False
    # Set selection_rule to the text 'AUTHORIZED_CLAIM_FCFS_EXPLICIT_ACCEPTANCE'.
    selection_rule = "AUTHORIZED_CLAIM_FCFS_EXPLICIT_ACCEPTANCE"

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input bundle: the supplied bundle.
    # Input arrivals: the supplied arrivals.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, bundle, arrivals):
        # Call super().__init__ with the supplied arguments.
        super().__init__(bundle, sampling_seed=0)
        # Set self.arrivals to arrivals.
        self.arrivals = arrivals

    # Context using the inputs and processing steps below.
    # Input role: the supplied role.
    # Input graph: the supplied graph.
    # Input timestamp: the supplied timestamp.
    # Input subject: the supplied subject.
    # Input mask: the supplied mask.
    # Input regulatory_profile: the supplied regulatory profile.
    # Input protocol: the supplied protocol.
    # Output: a tuple containing the result of SimpleNamespace(), None.
    def _context(self, role, graph, timestamp, subject, mask, regulatory_profile, protocol=None):
        # Symbolic metadata only. No baseline GNN or learned actor forward.
        # Return a tuple containing the result of SimpleNamespace(), None to the caller.
        return SimpleNamespace(decision_role=role, ego_id=subject.ego_id,
            # Supply claim_identity as subject.claim_identity.
            # Supply proposal_id as subject.proposal_id.
            claim_identity=subject.claim_identity, proposal_id=subject.proposal_id,
            # Supply action_feasibility_mask as a tuple built from mask.
            action_feasibility_mask=tuple(mask)), None

    # Sample using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input batch_id: the supplied batch id.
    # Input episode_id: the supplied episode id.
    # Input scenario_id: the supplied scenario id.
    # Input critic_sample_id: the supplied critic sample id.
    # Output: the result of SimpleNamespace().
    def _sample(self, context, batch_id, episode_id, scenario_id, critic_sample_id):
        # Set role to context.decision_role.value.
        role = context.decision_role.value
        # Set names to a tuple containing the text 'KEEP_CLAIM', the text 'RELINQUISH_CLAIM' when role equals the
        # text 'PROPOSER', otherwise a tuple containing the text 'ACCEPT_RELINQUISHMENT', the text
        # 'REJECT_RELINQUISHMENT'.
        names = ("KEEP_CLAIM", "RELINQUISH_CLAIM") if role == "PROPOSER" else (
            "ACCEPT_RELINQUISHMENT", "REJECT_RELINQUISHMENT")
        # Set index to the result of fcfs_action(role, context.claim_identity, self.arrivals,
        # context.action_feasibility_mask).
        index = fcfs_action(role, context.claim_identity, self.arrivals,
                            # Supply context.action_feasibility_mask to fcfs_action.
                            context.action_feasibility_mask)
        # Return the result of SimpleNamespace() to the caller.
        return SimpleNamespace(joint_batch_id=batch_id, selected_semantic_action=names[index],
            # Supply behavior_policy_log_probability as 0.0.
            # Supply decision_role as role.
            # Supply ego_id as context.ego_id.
            behavior_policy_log_probability=0., decision_role=role, ego_id=context.ego_id,
            # Supply claim_identity as context.claim_identity.
            # Supply proposal_id as context.proposal_id.
            claim_identity=context.claim_identity, proposal_id=context.proposal_id,
            # Supply action_names as names.
            # Supply hard_action_mask as context.action_feasibility_mask.
            action_names=names, hard_action_mask=context.action_feasibility_mask,
            # Supply behavior_probability_vector as a tuple built from a lazy sequence of a floating-point number
            # built from i equals index for i in the integer range defined by 2.
            behavior_probability_vector=tuple(float(i == index) for i in range(2)),
            # Supply selected_action_index as index.
            selected_action_index=index)

# Define RulesOnlyProvider to group the state and operations declared below.
# Base classes: FCFSProvider.
# Instances expose the attributes and methods implemented in this class.
class RulesOnlyProvider(FCFSProvider):
    # Set rules_only to True.
    rules_only = True
    # Set selection_rule to the text 'NO_NEGOTIATION_UNRESOLVED_SAFE_HOLD'.
    selection_rule = "NO_NEGOTIATION_UNRESOLVED_SAFE_HOLD"

    # Select joint actions using the inputs and processing steps below.
    # Input kwargs: the supplied kwargs.
    # Output: None.
    def select_joint_actions(self, **kwargs):
        # Return None to the caller.
        return None
