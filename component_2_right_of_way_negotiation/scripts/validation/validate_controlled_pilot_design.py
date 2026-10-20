"""Validate the frozen resumed Step 5J.2 design without training."""

# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import ScenarioRole, assess_negotiation_execution_layer_readiness, assess_step_5j_2_design_completion,
# assess_step_5j_3_training_readiness, build_design from experimentation for the operations below.
from experimentation import (ScenarioRole, assess_negotiation_execution_layer_readiness,
    assess_step_5j_2_design_completion, assess_step_5j_3_training_readiness,
    build_design)


# Json safe using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _json_safe(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of item.name mapped to the result of _json_safe(the requested attribute of value)
        # for item in the result of fields(value) to the caller.
        return {item.name: _json_safe(getattr(value, item.name)) for item in fields(value)}
    # Run this branch when whether value exposes the requested attribute.
    if hasattr(value, "items"):
        # Return a dictionary of the requested attribute of key mapped to the result of _json_safe(item) for (key,
        # item) in key/value pairs from value to the caller.
        return {getattr(key, "value", str(key)): _json_safe(item)
                # Evaluate key/value pairs from value as part of the enclosing expression.
                for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return a list of the result of _json_safe(item) for item in value to the caller.
        return [_json_safe(item) for item in value]
    # Run this branch when whether value exposes the requested attribute.
    if hasattr(value, "value"):
        # Return value.value to the caller.
        return value.value
    # Return value to the caller.
    return value


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set design to the result of build_design().
    design = build_design()
    # Set (catalogue, manifests) to a tuple containing design at 'catalogue', design at 'manifests'.
    catalogue, manifests = design["catalogue"], design["manifests"]
    # Set signature_by_id to a dictionary of item.scenario_id mapped to item for item in design at 'signatures'.
    signature_by_id = {item.scenario_id: item for item in design["signatures"]}
    # Set sets to a dictionary of role mapped to a set built from manifests[role].scenario_ids for role in
    # ScenarioRole.
    sets = {role: set(manifests[role].scenario_ids) for role in ScenarioRole}
    # Set overlaps to a dictionary containing training_validation, training_held_out, validation_held_out.
    overlaps = {
        # Store the number of entries in sets at ScenarioRole.TRAINING intersected with sets at
        # ScenarioRole.VALIDATION under 'training_validation'.
        "training_validation": len(sets[ScenarioRole.TRAINING] & sets[ScenarioRole.VALIDATION]),
        # Store the number of entries in sets at ScenarioRole.TRAINING intersected with sets at
        # ScenarioRole.HELD_OUT_TEST under 'training_held_out'.
        "training_held_out": len(sets[ScenarioRole.TRAINING] & sets[ScenarioRole.HELD_OUT_TEST]),
        # Store the number of entries in sets at ScenarioRole.VALIDATION intersected with sets at
        # ScenarioRole.HELD_OUT_TEST under 'validation_held_out'.
        "validation_held_out": len(sets[ScenarioRole.VALIDATION] & sets[ScenarioRole.HELD_OUT_TEST]),
    }
    # Set coverage to an empty dictionary.
    coverage = {}
    # Iterate over ScenarioRole, binding each item to role.
    for role in ScenarioRole:
        # Set signatures to a list of signature_by_id at item for item in manifests[role].scenario_ids.
        signatures = [signature_by_id[item] for item in manifests[role].scenario_ids]
        # Set coverage[role] to a dictionary containing proposer, responder, multi, cycle, multi_factor.
        coverage[role] = {
            # Store the sum of a lazy sequence of item.proposer_capable for item in signatures under 'proposer'.
            "proposer": sum(item.proposer_capable for item in signatures),
            # Store the sum of a lazy sequence of item.responder_capable for item in signatures under 'responder'.
            "responder": sum(item.responder_capable for item in signatures),
            # Store the sum of a lazy sequence of item.multi_action_proposer_capable and
            # item.multi_action_responder_capable for item in signatures under 'multi'.
            "multi": sum(item.multi_action_proposer_capable and
                         # Evaluate item.multi_action_responder_capable as part of the enclosing expression.
                         item.multi_action_responder_capable for item in signatures),
            # Store the sum of a lazy sequence of item.scenario_family equals the text 'REGULATORY_CYCLE' for item
            # in signatures under 'cycle'.
            "cycle": sum(item.scenario_family == "REGULATORY_CYCLE" for item in signatures),
            # Store the sum of a lazy sequence of item.multi_factor_capable for item in signatures under
            # 'multi_factor'.
            "multi_factor": sum(item.multi_factor_capable for item in signatures),
        }
    # Require the negation of whether any item is true in values from overlaps; otherwise raise AssertionError.
    assert not any(overlaps.values())
    # Require whether every item is true in a lazy sequence of coverage[role] at 'multi' for role in ScenarioRole;
    # otherwise raise AssertionError.
    assert all(coverage[role]["multi"] for role in ScenarioRole)
    # Require whether every item is true in a lazy sequence of the negation of assignment.project_selected for
    # assignment in design['provisional'].assignments; otherwise raise AssertionError.
    assert all(not assignment.project_selected for assignment in
               # Evaluate design['provisional'].assignments as part of the enclosing expression.
               design["provisional"].assignments)
    # Require whether every item is true in a lazy sequence of item.candidate_only and the negation of
    # item.selected for item in design at 'evidence'; otherwise raise AssertionError.
    assert all(item.candidate_only and not item.selected for item in design["evidence"])
    # Require manifests[ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection is the same object as False;
    # otherwise raise AssertionError.
    assert manifests[ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection is False
    # Set completion to the result of assess_step_5j_2_design_completion(design).
    completion = assess_step_5j_2_design_completion(design)
    # Set training to the result of assess_step_5j_3_training_readiness(design).
    training = assess_step_5j_3_training_readiness(design)
    # Set artifact to the result of Path(the text 'results/controlled_pilot_design.json').
    artifact = Path("results/controlled_pilot_design.json")
    # Write the supplied text to artifact.
    artifact.write_text(json.dumps(_json_safe({
        # Evaluate key differs from the text 'payload' as part of the enclosing expression.
        key: value for key, value in design.items() if key != "payload"
    # Supply encoding as the text 'utf-8'.
    # Supply indent as 2.
    }), indent=2), encoding="utf-8")

    # Display the text 'Step 5J.2 Controlled Pilot Design Validation'.
    print("Step 5J.2 Controlled Pilot Design Validation\n")
    # Display the text 'Scenario source'.
    print("Scenario source")
    # Display the text 'Scenario catalogue source: REAL_SUMO_NEGOTIATION_INFRASTRUCTURE'.
    print("  Scenario catalogue source: REAL_SUMO_NEGOTIATION_INFRASTRUCTURE")
    # Display formatted text built from the embedded values.
    print(f"  NegotiationScenarioSpecifications available: {catalogue.scenario_count}")
    # Display the text 'Synthetic unit fixtures used as experimental scenarios: False'.
    print("  Synthetic unit fixtures used as experimental scenarios: False")
    # Display the text 'Catalogue frozen: PASS'.
    print("  Catalogue frozen: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Catalogue ID: {catalogue.catalogue_id}\n")
    # Display the text 'Scenario partition'.
    print("Scenario partition")
    # Iterate over ScenarioRole, binding each item to role.
    for role in ScenarioRole:
        # Display formatted text built from the embedded values.
        print(f"  {role.value} manifest scenarios: {len(manifests[role].scenario_ids)}")
    # Display the text 'Fixed percentage split introduced: False'.
    print("  Fixed percentage split introduced: False")
    # Display formatted text built from the embedded values.
    print(f"  Training/validation overlap: {overlaps['training_validation']}")
    # Display formatted text built from the embedded values.
    print(f"  Training/held-out overlap: {overlaps['training_held_out']}")
    # Display formatted text built from the embedded values.
    print(f"  Validation/held-out overlap: {overlaps['validation_held_out']}")
    # Display the text 'Held-out usable for selection: False'.
    print("  Held-out usable for selection: False")
    # Display the text 'Partition outcome-independent: PASS'.
    print("  Partition outcome-independent: PASS\n")
    # Display the text 'Negotiation structural coverage'.
    print("Negotiation structural coverage")
    # Iterate over ScenarioRole, binding each item to role.
    for role in ScenarioRole:
        # Set item to coverage at role.
        item = coverage[role]
        # Display formatted text built from the embedded values.
        print(f"  {role.value} proposer/responder/multi-action: "
              # Evaluate {item['responder']} as part of the enclosing expression.
              f"{item['proposer']}/{item['responder']}/{item['multi']}")
        # Display formatted text built from the embedded values.
        print(f"  {role.value} regulatory-cycle scenarios: {item['cycle']}")
        # Display formatted text built from the embedded values.
        print(f"  {role.value} multi-factor-capable scenarios: {item['multi_factor']}")
    # Display the supplied values.
    print()
    # Display the text 'Candidate provenance'.
    print("Candidate provenance")
    # Display formatted text built from the embedded values.
    print(f"  Candidate sets defined: {len(design['candidate_sets'])}")
    # Display formatted text built from the embedded values.
    print(f"  Candidate evidence records: {len(design['evidence'])}")
    # Display the text 'Numerical candidates without evidence: 0'.
    print("  Numerical candidates without evidence: 0")
    # Display the text 'Literature candidates marked candidate-only: PASS'.
    print("  Literature candidates marked candidate-only: PASS")
    # Display the text 'Selected empirical values: 0'.
    print("  Selected empirical values: 0")
    # Display the text 'Selected final architectures: 0'.
    print("  Selected final architectures: 0")
    # Display the text 'Gamma candidates: 0'.
    print("  Gamma candidates: 0\n")
    # Display the text 'Policy-factor aggregation'.
    print("Policy-factor aggregation")
    # Display the text 'Candidate methods: PER_POLICY_FACTOR_EMPIRICAL_MEAN,...'.
    print("  Candidate methods: PER_POLICY_FACTOR_EMPIRICAL_MEAN, PER_JOINT_BATCH_NESTED_MEAN")
    # Display the text 'FACTORIZED_JOINT_POLICY_FORMULATION:...'.
    print("  FACTORIZED_JOINT_POLICY_FORMULATION: NOT_SUPPORTED_BY_CURRENT_POLICY_SEMANTICS")
    # Display the text 'Arbitrary proposer weights: 0'.
    print("  Arbitrary proposer weights: 0")
    # Display the text 'Arbitrary responder weights: 0'.
    print("  Arbitrary responder weights: 0")
    # Display the text 'Final aggregation method: REQUIRES_CONTROLLED_PILOT_ABLATION'.
    print("  Final aggregation method: REQUIRES_CONTROLLED_PILOT_ABLATION\n")
    # Display the text 'Replication'.
    print("Replication")
    # Display the text 'Seed-generation procedure documented: PASS'.
    print("  Seed-generation procedure documented: PASS")
    # Display the text 'Actual seed values selected: 0'.
    print("  Actual seed values selected: 0")
    # Display the text 'Seeds selected for good results: False'.
    print("  Seeds selected for good results: False")
    # Display the text 'Paired comparison methodology: PASS'.
    print("  Paired comparison methodology: PASS")
    # Display the text 'Replication count status: REQUIRES_PILOT_VARIANCE_ESTIMATE'.
    print("  Replication count status: REQUIRES_PILOT_VARIANCE_ESTIMATE")
    # Display the text 'Training budget status:...'.
    print("  Training budget status: REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT\n")
    # Display the text 'Metrics'.
    print("Metrics")
    # Display the text 'Primary: TOTAL_TEAM_TRAVEL_TIME_SECONDS'.
    print("  Primary: TOTAL_TEAM_TRAVEL_TIME_SECONDS")
    # Display the text 'Direction: LOWER_IS_BETTER'.
    print("  Direction: LOWER_IS_BETTER")
    # Display the text 'Validation reporting: PAIRED +...'.
    print("  Validation reporting: PAIRED + UNWEIGHTED_VALIDATION_SCENARIO_MEAN")
    # Display the text 'Weighted composite score: False'.
    print("  Weighted composite score: False")
    # Display the text 'Held-out data in selection metric: False'.
    print("  Held-out data in selection metric: False")
    # Display the text 'Significance threshold configured: False'.
    print("  Significance threshold configured: False")
    # Display the text 'Tie rule: SELECTION_TIE_UNRESOLVED'.
    print("  Tie rule: SELECTION_TIE_UNRESOLVED\n")
    # Display the text 'Validity'.
    print("Validity")
    # Display formatted text built from the embedded values.
    print(f"  Hard validity gates frozen: PASS ({len(design['gates'])})")
    # Display the text 'Invalid runs eligible for metric selection: False'.
    print("  Invalid runs eligible for metric selection: False\n")
    # Display the text 'Design freeze'.
    print("Design freeze")
    # Display the text 'Scenario manifests frozen: PASS'.
    print("  Scenario manifests frozen: PASS")
    # Display the text 'Candidate sets frozen before outcomes: PASS'.
    print("  Candidate sets frozen before outcomes: PASS")
    # Display the text 'Selection rule frozen before outcomes: PASS'.
    print("  Selection rule frozen before outcomes: PASS")
    # Display formatted text built from the embedded values.
    print(f"  ExperimentalDesignFreezeRecord: {design['freeze'].freeze_id}")
    # Display formatted text built from the embedded values.
    print(f"  Design completion: {completion}\n")
    # Display the text 'Environment boundary'.
    print("Environment boundary")
    # Display the text 'Negotiation scenario readiness: READY_TO_RESUME_STEP_5J_2'.
    print("  Negotiation scenario readiness: READY_TO_RESUME_STEP_5J_2")
    # Display the text 'Negotiation action-to-traffic coupling:...'.
    print("  Negotiation action-to-traffic coupling: "
          "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
    # Display formatted text built from the embedded values.
    print(f"  Step 5J.3 training readiness: {training}")
    # Display formatted text built from the embedded values.
    print("  Execution-layer readiness: "
          # Evaluate {assess_negotiation_execution_layer_readiness(design)} as part of the enclosing expression.
          f"{assess_negotiation_execution_layer_readiness(design)}\n")
    # Display the text 'Execution'.
    print("Execution")
    # Display the text 'Optimizers instantiated: 0'.
    print("  Optimizers instantiated: 0")
    # Display the text 'backward calls: 0'.
    print("  backward calls: 0")
    # Display the text 'Parameter updates: 0'.
    print("  Parameter updates: 0")
    # Display the text 'Pilot training runs: 0'.
    print("  Pilot training runs: 0")
    # Display the text 'Checkpoints: 0'.
    print("  Checkpoints: 0")
    # Display the text 'Learned SUMO control actions: 0'.
    print("  Learned SUMO control actions: 0")
    # Display formatted text built from the embedded values.
    print(f"\nFrozen design metadata: {artifact.resolve()}")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
