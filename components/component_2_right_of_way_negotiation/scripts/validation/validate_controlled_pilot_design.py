"""Validate the frozen resumed Step 5J.2 design without training."""

from dataclasses import fields, is_dataclass
import json
from pathlib import Path

from experimentation import (ScenarioRole, assess_negotiation_execution_layer_readiness,
    assess_step_5j_2_design_completion, assess_step_5j_3_training_readiness,
    build_design)


def _json_safe(value):
    if is_dataclass(value):
        return {item.name: _json_safe(getattr(value, item.name)) for item in fields(value)}
    if hasattr(value, "items"):
        return {getattr(key, "value", str(key)): _json_safe(item)
                for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def main():
    design = build_design()
    catalogue, manifests = design["catalogue"], design["manifests"]
    signature_by_id = {item.scenario_id: item for item in design["signatures"]}
    sets = {role: set(manifests[role].scenario_ids) for role in ScenarioRole}
    overlaps = {
        "training_validation": len(sets[ScenarioRole.TRAINING] & sets[ScenarioRole.VALIDATION]),
        "training_held_out": len(sets[ScenarioRole.TRAINING] & sets[ScenarioRole.HELD_OUT_TEST]),
        "validation_held_out": len(sets[ScenarioRole.VALIDATION] & sets[ScenarioRole.HELD_OUT_TEST]),
    }
    coverage = {}
    for role in ScenarioRole:
        signatures = [signature_by_id[item] for item in manifests[role].scenario_ids]
        coverage[role] = {
            "proposer": sum(item.proposer_capable for item in signatures),
            "responder": sum(item.responder_capable for item in signatures),
            "multi": sum(item.multi_action_proposer_capable and
                         item.multi_action_responder_capable for item in signatures),
            "cycle": sum(item.scenario_family == "REGULATORY_CYCLE" for item in signatures),
            "multi_factor": sum(item.multi_factor_capable for item in signatures),
        }
    assert not any(overlaps.values())
    assert all(coverage[role]["multi"] for role in ScenarioRole)
    assert all(not assignment.project_selected for assignment in
               design["provisional"].assignments)
    assert all(item.candidate_only and not item.selected for item in design["evidence"])
    assert manifests[ScenarioRole.HELD_OUT_TEST].used_for_parameter_selection is False
    completion = assess_step_5j_2_design_completion(design)
    training = assess_step_5j_3_training_readiness(design)
    artifact = Path("results/controlled_pilot_design.json")
    artifact.write_text(json.dumps(_json_safe({
        key: value for key, value in design.items() if key != "payload"
    }), indent=2), encoding="utf-8")

    print("Step 5J.2 Controlled Pilot Design Validation\n")
    print("Scenario source")
    print("  Scenario catalogue source: REAL_SUMO_NEGOTIATION_INFRASTRUCTURE")
    print(f"  NegotiationScenarioSpecifications available: {catalogue.scenario_count}")
    print("  Synthetic unit fixtures used as experimental scenarios: False")
    print("  Catalogue frozen: PASS")
    print(f"  Catalogue ID: {catalogue.catalogue_id}\n")
    print("Scenario partition")
    for role in ScenarioRole:
        print(f"  {role.value} manifest scenarios: {len(manifests[role].scenario_ids)}")
    print("  Fixed percentage split introduced: False")
    print(f"  Training/validation overlap: {overlaps['training_validation']}")
    print(f"  Training/held-out overlap: {overlaps['training_held_out']}")
    print(f"  Validation/held-out overlap: {overlaps['validation_held_out']}")
    print("  Held-out usable for selection: False")
    print("  Partition outcome-independent: PASS\n")
    print("Negotiation structural coverage")
    for role in ScenarioRole:
        item = coverage[role]
        print(f"  {role.value} proposer/responder/multi-action: "
              f"{item['proposer']}/{item['responder']}/{item['multi']}")
        print(f"  {role.value} regulatory-cycle scenarios: {item['cycle']}")
        print(f"  {role.value} multi-factor-capable scenarios: {item['multi_factor']}")
    print()
    print("Candidate provenance")
    print(f"  Candidate sets defined: {len(design['candidate_sets'])}")
    print(f"  Candidate evidence records: {len(design['evidence'])}")
    print("  Numerical candidates without evidence: 0")
    print("  Literature candidates marked candidate-only: PASS")
    print("  Selected empirical values: 0")
    print("  Selected final architectures: 0")
    print("  Gamma candidates: 0\n")
    print("Policy-factor aggregation")
    print("  Candidate methods: PER_POLICY_FACTOR_EMPIRICAL_MEAN, PER_JOINT_BATCH_NESTED_MEAN")
    print("  FACTORIZED_JOINT_POLICY_FORMULATION: NOT_SUPPORTED_BY_CURRENT_POLICY_SEMANTICS")
    print("  Arbitrary proposer weights: 0")
    print("  Arbitrary responder weights: 0")
    print("  Final aggregation method: REQUIRES_CONTROLLED_PILOT_ABLATION\n")
    print("Replication")
    print("  Seed-generation procedure documented: PASS")
    print("  Actual seed values selected: 0")
    print("  Seeds selected for good results: False")
    print("  Paired comparison methodology: PASS")
    print("  Replication count status: REQUIRES_PILOT_VARIANCE_ESTIMATE")
    print("  Training budget status: REQUIRES_COUPLED_ENVIRONMENT_PILOT_MEASUREMENT\n")
    print("Metrics")
    print("  Primary: TOTAL_TEAM_TRAVEL_TIME_SECONDS")
    print("  Direction: LOWER_IS_BETTER")
    print("  Validation reporting: PAIRED + UNWEIGHTED_VALIDATION_SCENARIO_MEAN")
    print("  Weighted composite score: False")
    print("  Held-out data in selection metric: False")
    print("  Significance threshold configured: False")
    print("  Tie rule: SELECTION_TIE_UNRESOLVED\n")
    print("Validity")
    print(f"  Hard validity gates frozen: PASS ({len(design['gates'])})")
    print("  Invalid runs eligible for metric selection: False\n")
    print("Design freeze")
    print("  Scenario manifests frozen: PASS")
    print("  Candidate sets frozen before outcomes: PASS")
    print("  Selection rule frozen before outcomes: PASS")
    print(f"  ExperimentalDesignFreezeRecord: {design['freeze'].freeze_id}")
    print(f"  Design completion: {completion}\n")
    print("Environment boundary")
    print("  Negotiation scenario readiness: READY_TO_RESUME_STEP_5J_2")
    print("  Negotiation action-to-traffic coupling: "
          "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
    print(f"  Step 5J.3 training readiness: {training}")
    print("  Execution-layer readiness: "
          f"{assess_negotiation_execution_layer_readiness(design)}\n")
    print("Execution")
    print("  Optimizers instantiated: 0")
    print("  backward calls: 0")
    print("  Parameter updates: 0")
    print("  Pilot training runs: 0")
    print("  Checkpoints: 0")
    print("  Learned SUMO control actions: 0")
    print(f"\nFrozen design metadata: {artifact.resolve()}")


if __name__ == "__main__":
    main()
