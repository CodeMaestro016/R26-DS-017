"""Shared real-SUMO evidence loader for Step 5J.2B.1 validators."""

# Import json for use in this module.
import json

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import ScenarioRole, build_design from experimentation for the operations below.
from experimentation import ScenarioRole, build_design
# Import ConflictZoneExecutionPlanner from negotiation_execution for the operations below.
from negotiation_execution import ConflictZoneExecutionPlanner
# Import JointNegotiationBranchEnumerator, NegotiationStatus from negotiation_learning for the operations below.
from negotiation_learning import JointNegotiationBranchEnumerator, NegotiationStatus

# Set EXPECTED_FREEZE_ID to a tuple containing the text 'EXPERIMENTAL_DESIGN_FREEZE_V1', the text...
EXPECTED_FREEZE_ID = ("EXPERIMENTAL_DESIGN_FREEZE_V1",
                      "588b2a4e03565cd3a1a76fc65682297692e4d1c891dea2087b97569e860d5aa8")


# As tuple using the inputs and processing steps below.
# Input value: the supplied value.
# Output: a tuple built from a lazy sequence of the result of as_tuple(item) when whether item has type list,
# otherwise item for item in value.
def as_tuple(value):
    # Return a tuple built from a lazy sequence of the result of as_tuple(item) when whether item has type list,
    # otherwise item for item in value to the caller.
    return tuple(as_tuple(item) if isinstance(item, list) else item for item in value)


# Real training evidence using the inputs and processing steps below.
# Output: a dictionary containing design, payload, scenario_id, timestamp, source_snapshot_id, movements,
# edges,...
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def real_training_evidence():
    # Set design to the result of build_design().
    design = build_design()
    # Run this branch when design['freeze'].freeze_id differs from EXPECTED_FREEZE_ID.
    if design["freeze"].freeze_id != EXPECTED_FREEZE_ID:
        # Raise RuntimeError with the text 'FROZEN_STEP_5J_2_DESIGN_MUTATED' to stop this execution path.
        raise RuntimeError("FROZEN_STEP_5J_2_DESIGN_MUTATED")
    # Enter the result of open(the text 'results/negotiation_scenario_catalogue.json') as stream and run the
    # enclosed operations within that context.
    with open("results/negotiation_scenario_catalogue.json", encoding="utf-8") as stream:
        # Set payload to the decoded data produced by json.load from stream.
        payload = json.load(stream)
    # Set training_ids to a set built from design['manifests'][ScenarioRole.TRAINING].scenario_ids.
    training_ids = set(design["manifests"][ScenarioRole.TRAINING].scenario_ids)
    # Set traces to the sorted values from a lazy sequence of item for item in payload at 'protocol_traces';
    # retain entries satisfying the result of as_tuple(item['scenario_id']) belongs to training_ids.
    traces = sorted((item for item in payload["protocol_traces"]
                     # Evaluate the result of as_tuple(item at 'scenario_id') belongs to training_ids as part of
                     # the enclosing expression.
                     if as_tuple(item["scenario_id"]) in training_ids),
                    # Declare item as input parameter.
                    key=lambda item: (as_tuple(item["scenario_id"]), item["timestamps"][0]))
    # Set inspected to an empty list.
    inspected = []
    # Iterate over traces, binding each item to trace.
    for trace in traces:
        # Set scenario_id to the result of as_tuple(trace at 'scenario_id').
        scenario_id = as_tuple(trace["scenario_id"])
        # Set timestamp to a floating-point number built from trace['timestamps'] at 0.
        timestamp = float(trace["timestamps"][0])
        # Set key to a tuple containing scenario_id, timestamp.
        key = (scenario_id, timestamp)
        # Run this branch when key belongs to inspected.
        if key in inspected:
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Append key to inspected.
        inspected.append(key)
        # Set specification to the next item from a lazy sequence of item for item in payload at
        # 'scenario_specifications'; retain entries satisfying the result of as_tuple(item['scenario_id']) equals
        # scenario_id.
        specification = next(item for item in payload["scenario_specifications"]
                             # Evaluate the result of as_tuple(item at 'scenario_id') equals scenario_id as part
                             # of the enclosing expression.
                             if as_tuple(item["scenario_id"]) == scenario_id)
        # Set movements to a dictionary of formatted text built from the embedded values mapped to path for
        # (index, path) in index/value pairs from specification at 'movement_path_ids'.
        movements = {f"SCENARIO_AV_{index}": path for index, path in
                     # Evaluate index/value pairs from specification at 'movement_path_ids' as part of the
                     # enclosing expression.
                     enumerate(specification["movement_path_ids"])}
        # Set graph to a tuple built from a lazy sequence of a tuple built from item for item in trace at
        # 'original_precedence_graph'.
        graph = tuple(tuple(item) for item in trace["original_precedence_graph"])
        # Set edges to a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
        # priority_vehicle_id, timestamp, regulatory_profile,... for (yielding, priority) in graph.
        edges = tuple({
            # Store yielding under 'yielding_vehicle_id'.
            # Store priority under 'priority_vehicle_id'.
            "yielding_vehicle_id": yielding, "priority_vehicle_id": priority,
            # Store timestamp under 'timestamp'.
            "timestamp": timestamp,
            "regulatory_profile": "DE_STVO_UNCONTROLLED_4WAY_V1",
            # Store an empty tuple under 'applicable_rule_ids'.
            # Store an empty tuple under 'source_sections'.
            "applicable_rule_ids": (), "source_sections": (),
            # Store an empty tuple under 'shared_conflict_zone_ids'.
            "shared_conflict_zone_ids": (),
            # Store a dictionary containing source under 'hard_constraint_evidence'.
            # Store the text 'REAL_SUMO_SCENARIO_SNAPSHOT' under 'source'.
            "hard_constraint_evidence": {"source": "REAL_SUMO_SCENARIO_SNAPSHOT"},
        # Evaluate a tuple containing yielding, priority as part of the enclosing expression.
        } for yielding, priority in graph)
        # Set paths to the result of MapPathManager().
        paths = MapPathManager()
        # Set planner to the result of ConflictZoneExecutionPlanner(paths, the result of
        # ConflictZoneManager(paths)).
        planner = ConflictZoneExecutionPlanner(paths, ConflictZoneManager(paths))
        # Set joint_snapshot_id to a tuple containing scenario_id, timestamp, the text
        # 'JOINT_NEGOTIATION_CONTEXT'.
        joint_snapshot_id = (scenario_id, timestamp, "JOINT_NEGOTIATION_CONTEXT")
        # Set enumerator to the result of JointNegotiationBranchEnumerator(planner).
        enumerator = JointNegotiationBranchEnumerator(planner)
        # Set branches to the result of enumerator.enumerate().
        branches = enumerator.enumerate(
            # Supply scenario_id as scenario_id.
            # Supply source_snapshot_id as joint_snapshot_id.
            scenario_id=scenario_id, source_snapshot_id=joint_snapshot_id,
            # Supply original_edges as edges.
            # Supply active_vehicle_ids as a tuple built from the sorted values from movements.
            original_edges=edges, active_vehicle_ids=tuple(sorted(movements)),
            # Supply timestamp as timestamp.
            # Supply regulatory_profile as the text 'DE_STVO_UNCONTROLLED_4WAY_V1'.
            timestamp=timestamp, regulatory_profile="DE_STVO_UNCONTROLLED_4WAY_V1",
            # Supply negotiation_status as NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value.
            negotiation_status=NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value,
            # Supply movement_path_by_vehicle as movements.
            movement_path_by_vehicle=movements)
        # Set executable to a tuple built from a lazy sequence of item for item in branches; retain entries
        # satisfying item.graph_executable.
        executable = tuple(item for item in branches if item.graph_executable)
        # Run this branch when executable.
        if executable:
            # Return a dictionary containing design, payload, scenario_id, timestamp, source_snapshot_id,
            # movements, edges,... to the caller.
            return {"design": design, "payload": payload, "scenario_id": scenario_id,
                    # Store timestamp under 'timestamp'.
                    # Store joint_snapshot_id under 'source_snapshot_id'.
                    "timestamp": timestamp, "source_snapshot_id": joint_snapshot_id,
                    # Store movements under 'movements'.
                    # Store edges under 'edges'.
                    # Store branches under 'branches'.
                    "movements": movements, "edges": edges, "branches": branches,
                    # Store executable under 'executable'.
                    # Store a tuple built from inspected under 'inspected'.
                    "executable": executable, "inspected": tuple(inspected),
                    # Store enumerator under 'enumerator'.
                    "enumerator": enumerator}
    # Raise RuntimeError with the text 'NEGOTIATION_ACTION_SPACE_CANNOT_RESOLVE_PRECEDENCE_CYCLE' to stop this
    # execution path.
    raise RuntimeError("NEGOTIATION_ACTION_SPACE_CANNOT_RESOLVE_PRECEDENCE_CYCLE")
