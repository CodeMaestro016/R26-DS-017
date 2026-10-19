"""Structural readiness checks, intentionally separate from PPO selection."""

from experimentation.models import ScenarioRole
from .models import ScenarioCataloguePartitionReadiness


CAUSAL_EXECUTION_PATH_PRESENT = "CAUSAL_EXECUTION_PATH_PRESENT"
COUPLING_INCOMPLETE = "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE"


def partition_readiness(specifications, coverage_records):
    relevant = tuple(sorted({item.scenario_id for item in coverage_records
                             if item.proposer_decision_event_ids}, key=repr))
    responders = tuple(sorted({item.scenario_id for item in coverage_records
                               if item.responder_decision_event_ids}, key=repr))
    multi_p = tuple(sorted({item.scenario_id for item in coverage_records
                            if any(all(mask) for mask in item.proposer_action_masks)}, key=repr))
    multi_r = tuple(sorted({item.scenario_id for item in coverage_records
                            if any(all(mask) for mask in item.responder_action_masks)}, key=repr))
    blockers = []
    if len(relevant) < len(ScenarioRole):
        blockers.append("SCENARIO_ROLE_PARTITION_INSUFFICIENT")
    if not multi_p:
        blockers.append("MULTI_ACTION_PROPOSER_COVERAGE_MISSING")
    if not responders:
        blockers.append("RESPONDER_TRAINING_COVERAGE_MISSING")
    if responders and not multi_r:
        blockers.append("RESPONDER_MULTI_ACTION_COVERAGE_MISSING")
    return ScenarioCataloguePartitionReadiness(
        relevant, tuple(role.value for role in ScenarioRole), False,
        relevant, responders, multi_p, multi_r, not blockers, tuple(blockers),
    )


def assess_step_5j_2_scenario_readiness(readiness, traces):
    states = {trace.protocol_status for trace in traces}
    required = {"AGREEMENT_ESTABLISHED", "PROPOSAL_REJECTED"}
    if readiness.partition_ready and required <= states:
        return "READY_TO_RESUME_STEP_5J_2"
    return ("NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT",
            readiness.blockers + tuple(sorted(required - states)))


def assess_step_5j_3_environment_readiness(step_5j_2_result,
                                           causality_status=COUPLING_INCOMPLETE):
    if step_5j_2_result != "READY_TO_RESUME_STEP_5J_2":
        return False, ("STEP_5J_2_SCENARIO_READINESS_INCOMPLETE",)
    if causality_status != CAUSAL_EXECUTION_PATH_PRESENT:
        return False, (COUPLING_INCOMPLETE,)
    return True, ()
