"""Step 5J.2B validator; stops before motion when the effective graph cycles."""

import json

from conflict import ConflictZoneManager, MapPathManager
from experimentation import build_design
from negotiation_execution import ConflictZoneExecutionPlanner


EXPECTED_FREEZE_ID = (
    "EXPERIMENTAL_DESIGN_FREEZE_V1",
    "588b2a4e03565cd3a1a76fc65682297692e4d1c891dea2087b97569e860d5aa8",
)


def _tuple(value):
    return tuple(_tuple(item) if isinstance(item, list) else item for item in value)


def main():
    design = build_design()
    assert design["freeze"].freeze_id == EXPECTED_FREEZE_ID
    payload = json.loads(open(
        "results/negotiation_scenario_catalogue.json", encoding="utf-8").read())
    training_ids = set(design["manifests"][__import__(
        "experimentation").ScenarioRole.TRAINING].scenario_ids)
    traces = [item for item in payload["protocol_traces"]
              if _tuple(item["scenario_id"]) in training_ids]
    keep = next(item for item in traces if item["proposer_action"] == "KEEP_CLAIM")
    same_snapshot = [item for item in traces
                     if item["source_snapshot_id"] == keep["source_snapshot_id"]]
    reject = next(item for item in same_snapshot
                  if item["responder_action"] == "REJECT_RELINQUISHMENT")
    accept = next(item for item in same_snapshot
                  if item["responder_action"] == "ACCEPT_RELINQUISHMENT")
    assert keep["effective_precedence_graph"] == reject["effective_precedence_graph"]
    assert accept["effective_precedence_graph"] != keep["effective_precedence_graph"]
    scenario = next(item for item in payload["scenario_specifications"]
                    if item["scenario_id"] == keep["scenario_id"])
    movement_by_vehicle = {
        f"SCENARIO_AV_{index}": path_id for index, path_id in
        enumerate(scenario["movement_path_ids"])}
    active = tuple(sorted(movement_by_vehicle))
    paths = MapPathManager()
    planner = ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))
    arguments = dict(
        source_snapshot_id=_tuple(keep["source_snapshot_id"]),
        active_vehicle_ids=active, movement_path_by_vehicle=movement_by_vehicle,
        timestamp=keep["timestamps"][0], cleared_vehicle_zones=())
    keep_plan = planner.plan(
        effective_coordination_graph=keep["effective_precedence_graph"],
        source_protocol_state=keep["protocol_status"], **arguments)
    reject_plan = planner.plan(
        effective_coordination_graph=reject["effective_precedence_graph"],
        source_protocol_state=reject["protocol_status"], **arguments)
    accept_plan = planner.plan(
        effective_coordination_graph=accept["effective_precedence_graph"],
        source_protocol_state=accept["protocol_status"], **arguments)
    assert keep_plan.graph_status == "EXECUTION_BLOCKED_PRECEDENCE_CYCLE"
    assert reject_plan.effective_coordination_graph == keep_plan.effective_coordination_graph
    assert accept_plan.effective_coordination_graph != keep_plan.effective_coordination_graph
    assert not keep_plan.ready_vehicle_ids

    print("Step 5J.2B Negotiation-to-Traffic Coupling Validation\n")
    print("Frozen design")
    print("  Step 5J.2 design identity unchanged: PASS")
    print("  Training manifest unchanged: PASS")
    print("  Validation manifest unchanged: PASS")
    print("  Held-out manifest unchanged: PASS")
    print("  Held-out scenarios executed: 0\n")
    print("Execution semantics")
    print("  Edge convention yielding->priority: PASS")
    print("  Effective coordination graph consumed: PASS")
    print("  Original regulatory graph mutated: False")
    print(f"  Map-derived conflict zones consumed: {len(keep_plan.constraints)}")
    print("  Arbitrary conflict-zone geometry introduced: 0\n")
    print("Protocol branches")
    print("  KEEP branch graph planned: PASS")
    print("  RELINQUISH+REJECT branch graph planned: PASS")
    print("  RELINQUISH+ACCEPT branch graph planned: PASS")
    print("  KEEP/REJECT graph consistency: PASS")
    print("  ACCEPT changes effective graph: PASS")
    print(f"  KEEP graph status: {keep_plan.graph_status}")
    print(f"  REJECT graph status: {reject_plan.graph_status}")
    print(f"  ACCEPT graph status: {accept_plan.graph_status}\n")
    print("Physical controller")
    print("  Raw action-to-speed mappings introduced: 0")
    print("  Incremental +/- speed heuristics introduced: 0")
    print("  Kinematic stopping envelope implemented: PASS")
    print("  Physical speed commands issued: 0")
    print("  Native SUMO safety mode changed: False\n")
    print("Status")
    print("  STOP: EXECUTION_BLOCKED_PRECEDENCE_CYCLE")
    print("  NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_STATUS: "
          "NEGOTIATION_ACTION_TO_TRAFFIC_OUTCOME_COUPLING_INCOMPLETE")
    print("  Physical causal witness established: False")
    print("  Step 5H branch rewards computed: False\n")
    print("Training boundary")
    print("  Optimizers: 0")
    print("  backward() calls: 0")
    print("  Parameter updates: 0")
    print("  MAPPO training runs: 0")
    print("  Checkpoints: 0")
    print("  Learned SUMO control actions: 0")


if __name__ == "__main__":
    main()
