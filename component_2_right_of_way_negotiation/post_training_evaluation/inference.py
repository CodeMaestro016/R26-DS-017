"""Scientific evaluation retains the selected policy's stochastic sampling."""
from negotiation_training.final_selection import FinalSelectionInferenceProvider

SCIENTIFIC_SELECTION_RULE = "SEEDED_STOCHASTIC_MASKED_SAMPLE"


class ScientificEvaluationProvider(FinalSelectionInferenceProvider):
    selection_rule = SCIENTIFIC_SELECTION_RULE

    def factor_diagnostics(self, batch_id):
        return tuple({
            "decision_role": item.decision_role,
            "ego_id": item.ego_id,
            "claim_identity": item.claim_identity,
            "proposal_id": item.proposal_id,
            "action_names": item.action_names,
            "hard_action_mask": item.hard_action_mask,
            "masked_probabilities": item.behavior_probability_vector,
            "selected_action": item.selected_semantic_action,
            "selected_action_index": item.selected_action_index,
            "selection_rule": self.selection_rule,
        } for item in self.pending_factors if item.joint_batch_id == batch_id)
