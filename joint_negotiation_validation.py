"""Shared real-SUMO evidence loader for Step 5J.2B.1 validators."""

import json

from conflict import ConflictZoneManager, MapPathManager
from experimentation import ScenarioRole, build_design
from negotiation_execution import ConflictZoneExecutionPlanner
from negotiation_learning import JointNegotiationBranchEnumerator, NegotiationStatus

EXPECTED_FREEZE_ID = ("EXPERIMENTAL_DESIGN_FREEZE_V1",
                      "588b2a4e03565cd3a1a76fc65682297692e4d1c891dea2087b97569e860d5aa8")


def as_tuple(value):
    return tuple(as_tuple(item) if isinstance(item, list) else item for item in value)


def real_training_evidence():
    design = build_design()
    if design["freeze"].freeze_id != EXPECTED_FREEZE_ID:
        raise RuntimeError("FROZEN_STEP_5J_2_DESIGN_MUTATED")
    with open("results/negotiation_scenario_catalogue.json", encoding="utf-8") as stream:
        payload = json.load(stream)
    training_ids = set(design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    traces = sorted((item for item in payload["protocol_traces"]
                     if as_tuple(item["scenario_id"]) in training_ids),
                    key=lambda item: (as_tuple(item["scenario_id"]), item["timestamps"][0]))
    inspected = []
    for trace in traces:
        scenario_id = as_tuple(trace["scenario_id"])
        timestamp = float(trace["timestamps"][0])
        key = (scenario_id, timestamp)
        if key in inspected:
            continue
        inspected.append(key)
        specification = next(item for item in payload["scenario_specifications"]
                             if as_tuple(item["scenario_id"]) == scenario_id)
        movements = {f"SCENARIO_AV_{index}": path for index, path in
                     enumerate(specification["movement_path_ids"])}
        graph = tuple(tuple(item) for item in trace["original_precedence_graph"])
        edges = tuple({
            "yielding_vehicle_id": yielding, "priority_vehicle_id": priority,
            "timestamp": timestamp,
            "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
            "applicable_rule_ids": (), "source_sections": (),
            "shared_conflict_zone_ids": (),
            "hard_constraint_evidence": {"source": "REAL_SUMO_SCENARIO_SNAPSHOT"},
        } for yielding, priority in graph)
        paths = MapPathManager()
        planner = ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))
        joint_snapshot_id = (scenario_id, timestamp, "JOINT_NEGOTIATION_CONTEXT")
        enumerator = JointNegotiationBranchEnumerator(planner)
        branches = enumerator.enumerate(
            scenario_id=scenario_id, source_snapshot_id=joint_snapshot_id,
            original_edges=edges, active_vehicle_ids=tuple(sorted(movements)),
            timestamp=timestamp, regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
            negotiation_status=NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
            movement_path_by_vehicle=movements)
        executable = tuple(item for item in branches if item.graph_executable)
        if executable:
            return {"design": design, "payload": payload, "scenario_id": scenario_id,
                    "timestamp": timestamp, "source_snapshot_id": joint_snapshot_id,
                    "movements": movements, "edges": edges, "branches": branches,
                    "executable": executable, "inspected": tuple(inspected),
                    "enumerator": enumerator}
    raise RuntimeError("NEGOTIATION_ACTION_SPACE_CANNOT_RESOLVE_PRECEDENCE_CYCLE")
