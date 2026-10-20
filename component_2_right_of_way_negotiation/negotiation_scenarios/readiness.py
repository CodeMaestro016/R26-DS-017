"""Structural readiness checks, intentionally separate from PPO selection."""

# Import ScenarioRole from experimentation.models for the operations below.
from experimentation.models import ScenarioRole
# Import ScenarioCataloguePartitionReadiness from .models for the operations below.
from .models import ScenarioCataloguePartitionReadiness


# Set CAUSAL_EXECUTION_PATH_PRESENT to the text 'CAUSAL_EXECUTION_PATH_PRESENT'.
CAUSAL_EXECUTION_PATH_PRESENT = "CAUSAL_EXECUTION_PATH_PRESENT"
# Set COUPLING_INCOMPLETE to the text 'NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE'.
COUPLING_INCOMPLETE = "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE"


# Partition readiness using the inputs and processing steps below.
# Input specifications: the supplied specifications.
# Input coverage_records: the supplied coverage records.
# Output: the result of ScenarioCataloguePartitionReadiness(relevant, a tuple built from a lazy sequence of
# role.value for role in ScenarioRole, False,...).
# Processing: select branches using the stated conditions.
def partition_readiness(specifications, coverage_records):
    # Set relevant to a tuple built from the sorted values from a set of item.scenario_id for item in
    # coverage_records; retain entries satisfying item.proposer_decision_event_ids.
    relevant = tuple(sorted({item.scenario_id for item in coverage_records
                             # Supply key as repr.
                             if item.proposer_decision_event_ids}, key=repr))
    # Set responders to a tuple built from the sorted values from a set of item.scenario_id for item in
    # coverage_records; retain entries satisfying item.responder_decision_event_ids.
    responders = tuple(sorted({item.scenario_id for item in coverage_records
                               # Supply key as repr.
                               if item.responder_decision_event_ids}, key=repr))
    # Set multi_p to a tuple built from the sorted values from a set of item.scenario_id for item in
    # coverage_records; retain entries satisfying whether any item is true in (all(mask) for mask in
    # item.proposer_action_masks).
    multi_p = tuple(sorted({item.scenario_id for item in coverage_records
                            # Supply key as repr.
                            if any(all(mask) for mask in item.proposer_action_masks)}, key=repr))
    # Set multi_r to a tuple built from the sorted values from a set of item.scenario_id for item in
    # coverage_records; retain entries satisfying whether any item is true in (all(mask) for mask in
    # item.responder_action_masks).
    multi_r = tuple(sorted({item.scenario_id for item in coverage_records
                            # Supply key as repr.
                            if any(all(mask) for mask in item.responder_action_masks)}, key=repr))
    # Set blockers to an empty list.
    blockers = []
    # Run this branch when the number of entries in relevant is less than the number of entries in ScenarioRole.
    if len(relevant) < len(ScenarioRole):
        # Append the text 'SCENARIO_ROLE_PARTITION_INSUFFICIENT' to blockers.
        blockers.append("SCENARIO_ROLE_PARTITION_INSUFFICIENT")
    # Run this branch when the negation of multi_p.
    if not multi_p:
        # Append the text 'MULTI_ACTION_PROPOSER_COVERAGE_MISSING' to blockers.
        blockers.append("MULTI_ACTION_PROPOSER_COVERAGE_MISSING")
    # Run this branch when the negation of responders.
    if not responders:
        # Append the text 'RESPONDER_TRAINING_COVERAGE_MISSING' to blockers.
        blockers.append("RESPONDER_TRAINING_COVERAGE_MISSING")
    # Run this branch when responders and the negation of multi_r.
    if responders and not multi_r:
        # Append the text 'RESPONDER_MULTI_ACTION_COVERAGE_MISSING' to blockers.
        blockers.append("RESPONDER_MULTI_ACTION_COVERAGE_MISSING")
    # Return the result of ScenarioCataloguePartitionReadiness(relevant, a tuple built from a lazy sequence of
    # role.value for role in ScenarioRole, False,...) to the caller.
    return ScenarioCataloguePartitionReadiness(
        # Supply a tuple built from a lazy sequence of role.value for role in ScenarioRole to
        # ScenarioCataloguePartitionReadiness.
        relevant, tuple(role.value for role in ScenarioRole), False,
        # Supply a tuple built from blockers to ScenarioCataloguePartitionReadiness.
        relevant, responders, multi_p, multi_r, not blockers, tuple(blockers),
    )


# Assess step 5j 2 scenario readiness using the inputs and processing steps below.
# Input readiness: the supplied readiness.
# Input traces: the supplied traces.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def assess_step_5j_2_scenario_readiness(readiness, traces):
    # Set states to a set of trace.protocol_status for trace in traces.
    states = {trace.protocol_status for trace in traces}
    # Set required to a set containing the text 'AGREEMENT_ESTABLISHED', the text 'PROPOSAL_REJECTED'.
    required = {"AGREEMENT_ESTABLISHED", "PROPOSAL_REJECTED"}
    # Run this branch when readiness.partition_ready and required is at most states.
    if readiness.partition_ready and required <= states:
        # Return the text 'READY_TO_RESUME_STEP_5J_2' to the caller.
        return "READY_TO_RESUME_STEP_5J_2"
    # Return a tuple containing the text 'NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT', readiness.blockers
    # plus a tuple built from... to the caller.
    return ("NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT",
            # Include readiness.blockers plus a tuple built from the sorted values from required minus states in
            # this tuple.
            readiness.blockers + tuple(sorted(required - states)))


# Assess step 5j 3 environment readiness using the inputs and processing steps below.
# Input step_5j_2_result: the supplied step 5j 2 result.
# Input causality_status: the supplied causality status.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def assess_step_5j_3_environment_readiness(step_5j_2_result,
                                           # Declare causality_status as input parameter.
                                           causality_status=COUPLING_INCOMPLETE):
    # Run this branch when step_5j_2_result differs from the text 'READY_TO_RESUME_STEP_5J_2'.
    if step_5j_2_result != "READY_TO_RESUME_STEP_5J_2":
        # Return a tuple containing False, a tuple containing the text 'STEP_5J_2_SCENARIO_READINESS_INCOMPLETE'
        # to the caller.
        return False, ("STEP_5J_2_SCENARIO_READINESS_INCOMPLETE",)
    # Run this branch when causality_status differs from CAUSAL_EXECUTION_PATH_PRESENT.
    if causality_status != CAUSAL_EXECUTION_PATH_PRESENT:
        # Return a tuple containing False, a tuple containing COUPLING_INCOMPLETE to the caller.
        return False, (COUPLING_INCOMPLETE,)
    # Return a tuple containing True, an empty tuple to the caller.
    return True, ()
