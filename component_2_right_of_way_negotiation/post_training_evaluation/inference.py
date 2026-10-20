"""Scientific evaluation retains the selected policy's stochastic sampling."""
# Import FinalSelectionInferenceProvider from negotiation_training.final_selection for the operations below.
from negotiation_training.final_selection import FinalSelectionInferenceProvider

# Set SCIENTIFIC_SELECTION_RULE to the text 'SEEDED_STOCHASTIC_MASKED_SAMPLE'.
SCIENTIFIC_SELECTION_RULE = "SEEDED_STOCHASTIC_MASKED_SAMPLE"


# Define ScientificEvaluationProvider to group the state and operations declared below.
# Base classes: FinalSelectionInferenceProvider.
# Instances expose the attributes and methods implemented in this class.
class ScientificEvaluationProvider(FinalSelectionInferenceProvider):
    # Set selection_rule to SCIENTIFIC_SELECTION_RULE.
    selection_rule = SCIENTIFIC_SELECTION_RULE

    # Factor diagnostics using the inputs and processing steps below.
    # Input batch_id: the supplied batch id.
    # Output: a tuple built from a lazy sequence of a dictionary containing decision_role, ego_id, claim_identity,
    # proposal_id, action_names, hard_action_mask,... for item in self.pending_factors;...
    def factor_diagnostics(self, batch_id):
        # Return a tuple built from a lazy sequence of a dictionary containing decision_role, ego_id,
        # claim_identity, proposal_id, action_names, hard_action_mask,... for item in self.pending_factors; retain
        # entries satisfying item.joint_batch_id equals batch_id to the caller.
        return tuple({
            # Store item.decision_role under 'decision_role'.
            "decision_role": item.decision_role,
            # Store item.ego_id under 'ego_id'.
            "ego_id": item.ego_id,
            # Store item.claim_identity under 'claim_identity'.
            "claim_identity": item.claim_identity,
            # Store item.proposal_id under 'proposal_id'.
            "proposal_id": item.proposal_id,
            # Store item.action_names under 'action_names'.
            "action_names": item.action_names,
            # Store item.hard_action_mask under 'hard_action_mask'.
            "hard_action_mask": item.hard_action_mask,
            # Store item.behavior_probability_vector under 'masked_probabilities'.
            "masked_probabilities": item.behavior_probability_vector,
            # Store item.selected_semantic_action under 'selected_action'.
            "selected_action": item.selected_semantic_action,
            # Store item.selected_action_index under 'selected_action_index'.
            "selected_action_index": item.selected_action_index,
            # Store self.selection_rule under 'selection_rule'.
            "selection_rule": self.selection_rule,
        # Evaluate item.joint_batch_id equals batch_id as part of the enclosing expression.
        } for item in self.pending_factors if item.joint_batch_id == batch_id)
