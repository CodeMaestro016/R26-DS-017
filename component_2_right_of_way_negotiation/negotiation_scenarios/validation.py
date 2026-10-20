"""Auditable discovery/calibration validation and metadata serialization."""

# Import fields, is_dataclass from dataclasses for the operations below.
from dataclasses import fields, is_dataclass
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import Counter from collections for the operations below.
from collections import Counter

# Import OUTPUT_DIR from config for the operations below.
from config import OUTPUT_DIR
# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import get_intersection_geometry from map_geometry for the operations below.
from map_geometry import get_intersection_geometry
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine

# Import build_specifications from .catalogue for the operations below.
from .catalogue import build_specifications
# Import NegotiationScenarioEnumerator from .enumerator for the operations below.
from .enumerator import NegotiationScenarioEnumerator
# Import COUPLING_INCOMPLETE, assess_step_5j_2_scenario_readiness, assess_step_5j_3_environment_readiness,
# partition_readiness from .readiness for the operations below.
from .readiness import (COUPLING_INCOMPLETE,
    assess_step_5j_2_scenario_readiness, assess_step_5j_3_environment_readiness,
    partition_readiness)
# Import calibrate_movement, RealSumoNegotiationScenarioRunner from .runner for the operations below.
from .runner import calibrate_movement, RealSumoNegotiationScenarioRunner
# Import verify_reproducible from .calibration for the operations below.
from .calibration import verify_reproducible


# Json safe using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def _json_safe(value):
    # Run this branch when the result of is_dataclass(value).
    if is_dataclass(value):
        # Return a dictionary of item.name mapped to the result of _json_safe(the requested attribute of value)
        # for item in the result of fields(value) to the caller.
        return {item.name: _json_safe(getattr(value, item.name))
                # Evaluate the result of fields(value) as part of the enclosing expression.
                for item in fields(value)}
    # Run this branch when whether value exposes the requested attribute.
    if hasattr(value, "items"):
        # Return a dictionary of a string built from key mapped to the result of _json_safe(item) for (key, item)
        # in key/value pairs from value to the caller.
        return {str(key): _json_safe(item) for key, item in value.items()}
    # Run this branch when whether value has type dict.
    if isinstance(value, dict):
        # Return a dictionary of a string built from key mapped to the result of _json_safe(item) for (key, item)
        # in key/value pairs from value to the caller.
        return {str(key): _json_safe(item) for key, item in value.items()}
    # Run this branch when whether value has type a tuple containing tuple, list.
    if isinstance(value, (tuple, list)):
        # Return a list of the result of _json_safe(item) for item in value to the caller.
        return [_json_safe(item) for item in value]
    # Return value to the caller.
    return value


# Compiled junction center using the inputs and processing steps below.
# Input path_manager: the supplied path manager.
# Input junction_id: the supplied junction id.
# Output: a tuple built from a lazy sequence of a floating-point number built from value for value in the result
# of node.getCoord().
def compiled_junction_center(path_manager, junction_id=None):
    # Set junction_id to junction_id or get_intersection_geometry().junction_id.
    junction_id = junction_id or get_intersection_geometry().junction_id
    # Set node to the result of path_manager.network.getNode(junction_id).
    node = path_manager.network.getNode(junction_id)
    # Return a tuple built from a lazy sequence of a floating-point number built from value for value in the
    # result of node.getCoord() to the caller.
    return tuple(float(value) for value in node.getCoord())


# Validate synchronization event geometry using the inputs and processing steps below.
# Input path_manager: the supplied path manager.
# Output: a dictionary containing event, operational_center, compiled_sumo_center, centers_match, status.
def validate_synchronization_event_geometry(path_manager):
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Set compiled to the result of compiled_junction_center(path_manager, geometry.junction_id).
    compiled = compiled_junction_center(path_manager, geometry.junction_id)
    # Set operational to geometry.center_xy.
    operational = geometry.center_xy
    # Return a dictionary containing event, operational_center, compiled_sumo_center, centers_match, status to the
    # caller.
    return {
        "event": "ObservationManager.is_in_approach_zone(position)",
        # Store operational under 'operational_center'.
        "operational_center": operational,
        # Store compiled under 'compiled_sumo_center'.
        "compiled_sumo_center": compiled,
        # Store operational equals compiled under 'centers_match'.
        "centers_match": operational == compiled,
        # Store the text 'PASS' when operational equals compiled, otherwise the text
        # 'NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED' under 'status'.
        "status": ("PASS" if operational == compiled else
                   "NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED"),
    }


# Run discovery and calibration using the inputs and processing steps below.
# Input output_directory: the supplied output directory.
# Output: a tuple containing payload, catalogue_path, summary_path.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def run_discovery_and_calibration(output_directory=OUTPUT_DIR):
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set discoveries to the result of NegotiationScenarioEnumerator(paths, ConflictZoneManager(paths),
    # TrafficRuleEngine(paths)).enumerate().
    discoveries = NegotiationScenarioEnumerator(
        # Supply the result of ConflictZoneManager(paths) to NegotiationScenarioEnumerator.
        paths, ConflictZoneManager(paths), TrafficRuleEngine(paths)).enumerate()
    # Set event to the result of validate_synchronization_event_geometry(paths).
    event = validate_synchronization_event_geometry(paths)
    # Set (calibrations, calibration_error) to a tuple containing an empty list, None.
    calibrations, calibration_error = [], None
    # Set calibration_reproducible to True.
    calibration_reproducible = True
    # Run this branch when event at 'centers_match'.
    if event["centers_match"]:
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Iterate over the sorted values from paths.paths, binding each item to path_id.
            for path_id in sorted(paths.paths):
                # Set first to the result of calibrate_movement(paths, path_id).
                first = calibrate_movement(paths, path_id)
                # Set replay to the result of calibrate_movement(paths, path_id).
                replay = calibrate_movement(paths, path_id)
                # Run this branch when the negation of the result of verify_reproducible(first, replay).
                if not verify_reproducible(first, replay):
                    # Set calibration_reproducible to False.
                    calibration_reproducible = False
                    # Raise RuntimeError with the text 'SCENARIO_CALIBRATION_NONDETERMINISTIC' to stop this
                    # execution path.
                    raise RuntimeError("SCENARIO_CALIBRATION_NONDETERMINISTIC")
                # Append first to calibrations.
                calibrations.append(first)
        # Handle RuntimeError as error using the recovery steps below.
        except RuntimeError as error:
            # Set calibration_error to a string built from error.
            calibration_error = str(error)
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set calibration_error to event at 'status'.
        calibration_error = event["status"]
    # Set specifications to the result of build_specifications(discoveries, calibrations, paths) when the negation
    # of calibration_error, otherwise an empty tuple.
    specifications = (build_specifications(discoveries, calibrations, paths)
                      # Evaluate the negation of calibration_error as part of the enclosing expression.
                      if not calibration_error else ())
    # Set (live_coverage, protocol_traces) to a tuple containing an empty list, an empty list.
    live_coverage, protocol_traces = [], []
    # Set readiness to None.
    readiness = None
    # Set next_blocker to calibration_error.
    next_blocker = calibration_error
    # Set episodes to 0.
    episodes = 0
    # Run this branch when specifications.
    if specifications:
        # Set runner to the result of RealSumoNegotiationScenarioRunner(paths).
        runner = RealSumoNegotiationScenarioRunner(paths)
        # Iterate over specifications, binding each item to specification.
        for specification in specifications:
            # Set (live, traces) to the result of runner.run(specification).
            live, traces = runner.run(specification)
            # Update episodes to its current value plus 1.
            episodes += 1
            # Extend live_coverage with live.
            live_coverage.extend(live)
            # Extend protocol_traces with traces.
            protocol_traces.extend(traces)
            # Set readiness to the result of partition_readiness(specifications, live_coverage).
            readiness = partition_readiness(specifications, live_coverage)
            # Set max_factors to the maximum of a lazy sequence of the number of entries in
            # item.proposer_decision_event_ids for item in...
            max_factors = max((len(item.proposer_decision_event_ids)
                               # Supply default as 0.
                               for item in live_coverage), default=0)
            # Set states to a set of item.protocol_status for item in protocol_traces.
            states = {item.protocol_status for item in protocol_traces}
            # Run this branch when readiness.partition_ready and max_factors is greater than 1 and a set
            # containing the text 'AGREEMENT_ESTABLISHED', the text 'PROPOSAL_REJECTED' is at most states.
            if (readiness.partition_ready and max_factors > 1 and
                    # Evaluate a set containing the text 'AGREEMENT_ESTABLISHED', the text 'PROPOSAL_REJECTED' is
                    # at most states as part of the enclosing expression.
                    {"AGREEMENT_ESTABLISHED", "PROPOSAL_REJECTED"} <= states):
                # Leave the nearest enclosing loop immediately.
                break
        # Set readiness to the result of partition_readiness(specifications, live_coverage).
        readiness = partition_readiness(specifications, live_coverage)
        # Set step_5j_2 to the result of assess_step_5j_2_scenario_readiness(readiness, protocol_traces).
        step_5j_2 = assess_step_5j_2_scenario_readiness(
            # Supply protocol_traces to assess_step_5j_2_scenario_readiness.
            readiness, protocol_traces)
        # Run this branch when step_5j_2 differs from the text 'READY_TO_RESUME_STEP_5J_2'.
        if step_5j_2 != "READY_TO_RESUME_STEP_5J_2":
            # Run this branch when the negation of whether any item is true in a lazy sequence of the result of
            # item.negotiation_status.endswith('REGULATORY_CYCLE') for item in live_coverage.
            if not any(item.negotiation_status.endswith("REGULATORY_CYCLE")
                       # Evaluate live_coverage as part of the enclosing expression.
                       for item in live_coverage):
                # Set next_blocker to the text 'LIVE_REGULATORY_CYCLE_NOT_REPRODUCED'.
                next_blocker = "LIVE_REGULATORY_CYCLE_NOT_REPRODUCED"
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set next_blocker to step_5j_2[1] at 0 when whether step_5j_2 has type tuple and step_5j_2 at 1,
                # otherwise the text 'NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT'.
                next_blocker = (step_5j_2[1][0] if isinstance(step_5j_2, tuple)
                                # Evaluate step_5j_2 at 1 as part of the enclosing expression.
                                and step_5j_2[1] else
                                "NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT")
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set next_blocker to COUPLING_INCOMPLETE.
            next_blocker = COUPLING_INCOMPLETE
    # Run this alternative branch when the preceding branch does not apply.
    else:
        # Set step_5j_2 to the text 'NOT_EVALUATED_CALIBRATION_BLOCKED'.
        step_5j_2 = "NOT_EVALUATED_CALIBRATION_BLOCKED"
    # Set step_5j_3 to the result of assess_step_5j_3_environment_readiness(step_5j_2).
    step_5j_3 = assess_step_5j_3_environment_readiness(step_5j_2)
    # Set status_counts to the result of Counter(a lazy sequence of item.negotiation_status for item in
    # live_coverage).
    status_counts = Counter(item.negotiation_status for item in live_coverage)
    # Set relevant_live_coverage to a tuple built from a lazy sequence of item for item in live_coverage; retain
    # entries satisfying item.negotiation_status does not belong to a set containing 'NO_ACTIVE_CONFLICT',...
    relevant_live_coverage = tuple(
        # Evaluate live_coverage as part of the enclosing expression.
        item for item in live_coverage
        # Evaluate item.negotiation_status does not belong to a set containing the text 'NO_ACTIVE_CONFLICT', the
        # text 'REGULATORY_ORDER_RESOLVED' as part of the enclosing expression.
        if item.negotiation_status not in {
            "NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"})
    # Set payload to a dictionary containing checkpoint, catalogue_status, legal_movement_path_count,
    # movement_combination_count,...
    payload = {
        "checkpoint": "STEP_5J_2A",
        # Store the text 'BLOCKED' when calibration_error, otherwise the text 'DISCOVERED' under
        # 'catalogue_status'.
        "catalogue_status": "BLOCKED" if calibration_error else "DISCOVERED",
        # Store the number of entries in paths.paths under 'legal_movement_path_count'.
        "legal_movement_path_count": len(paths.paths),
        # Store the number of entries in discoveries under 'movement_combination_count'.
        "movement_combination_count": len(discoveries),
        # Store the sum of a lazy sequence of item.discovery_result equals 'RETAINED' and the result of
        # item.negotiation_status.endswith('REGULATORY_CYCLE') for item in discoveries under
        # 'regulatory_cycle_candidate_count'.
        "regulatory_cycle_candidate_count": sum(
            # Evaluate item.discovery_result equals the text 'RETAINED' and the result of
            # item.negotiation_status.endswith(the text 'REGULATORY_CYCLE') as part of the enclosing expression.
            item.discovery_result == "RETAINED" and
            # Evaluate the result of item.negotiation_status.endswith(the text 'REGULATORY_CYCLE') as part of the
            # enclosing expression.
            item.negotiation_status.endswith("REGULATORY_CYCLE")
            # Evaluate discoveries as part of the enclosing expression.
            for item in discoveries),
        # Store the sum of a lazy sequence of item.discovery_result equals 'RETAINED' and the result of
        # item.negotiation_status.endswith('UNRESOLVED_PRECEDENCE') for item in discoveries under
        # 'unresolved_precedence_candidate_count'.
        "unresolved_precedence_candidate_count": sum(
            # Evaluate item.discovery_result equals the text 'RETAINED' and the result of
            # item.negotiation_status.endswith(the text 'UNRESOLVED_PRECEDENCE') as part of the enclosing
            # expression.
            item.discovery_result == "RETAINED" and
            # Evaluate the result of item.negotiation_status.endswith(the text 'UNRESOLVED_PRECEDENCE') as part of
            # the enclosing expression.
            item.negotiation_status.endswith("UNRESOLVED_PRECEDENCE")
            # Evaluate discoveries as part of the enclosing expression.
            for item in discoveries),
        # Store event under 'synchronization_event'.
        "synchronization_event": event,
        # Store calibration_error under 'calibration_error'.
        "calibration_error": calibration_error,
        # Store calibration_reproducible under 'calibration_reproducible'.
        "calibration_reproducible": calibration_reproducible,
        # Store a list of the result of _json_safe(item) for item in discoveries under 'discoveries'.
        "discoveries": [_json_safe(item) for item in discoveries],
        # Store a list of the result of _json_safe(item) for item in calibrations under 'calibrations'.
        "calibrations": [_json_safe(item) for item in calibrations],
        # Store a list of the result of _json_safe(item) for item in specifications under
        # 'scenario_specifications'.
        "scenario_specifications": [_json_safe(item) for item in specifications],
        # Preserve every negotiation-relevant record. High-volume background
        # states are retained as exact categorical counts, not duplicated
        # actor-sized records in research metadata.
        # Store a list of the result of _json_safe(item) for item in relevant_live_coverage under 'live_coverage'.
        "live_coverage": [_json_safe(item) for item in relevant_live_coverage],
        # Store the number of entries in live_coverage under 'live_snapshot_count'.
        "live_snapshot_count": len(live_coverage),
        # Store a dictionary built from the sorted values from key/value pairs from status_counts under
        # 'live_snapshot_status_counts'.
        "live_snapshot_status_counts": dict(sorted(status_counts.items())),
        # Store a list of the result of _json_safe(item) for item in protocol_traces under 'protocol_traces'.
        "protocol_traces": [_json_safe(item) for item in protocol_traces],
        # Store episodes under 'real_sumo_scenario_episodes'.
        "real_sumo_scenario_episodes": episodes,
        # Store the result of _json_safe(step_5j_2) under 'step_5j_2_readiness'.
        "step_5j_2_readiness": _json_safe(step_5j_2),
        # Store the result of _json_safe(step_5j_3) under 'step_5j_3_readiness'.
        "step_5j_3_readiness": _json_safe(step_5j_3),
        # Store next_blocker under 'next_blocker'.
        "next_blocker": next_blocker,
        # Store COUPLING_INCOMPLETE under 'negotiation_action_to_traffic_outcome_status'.
        "negotiation_action_to_traffic_outcome_status": COUPLING_INCOMPLETE,
        # Store 0 under 'route_truth_policy_leakage_count'.
        "route_truth_policy_leakage_count": 0,
        # Store 0 under 'learned_policy_actions_issued'.
        "learned_policy_actions_issued": 0,
        # Store 0 under 'training_runs'.
        "training_runs": 0,
    }
    # Set output to the result of Path(output_directory).
    output = Path(output_directory)
    # Create the directory requested by output.
    output.mkdir(parents=True, exist_ok=True)
    # Set catalogue_path to output joined with the path segment 'negotiation_scenario_catalogue.json'.
    catalogue_path = output / "negotiation_scenario_catalogue.json"
    # Write the supplied text to catalogue_path.
    catalogue_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Set summary_path to output joined with the path segment 'negotiation_scenario_catalogue_summary.md'.
    summary_path = output / "negotiation_scenario_catalogue_summary.md"
    # Set retained to a list of item for item in discoveries; retain entries satisfying item.discovery_result
    # equals the text 'RETAINED'.
    retained = [item for item in discoveries if item.discovery_result == "RETAINED"]
    # Set lines to a list containing the text '# Step 5J.2A negotiation scenario catalogue', the text '',
    # formatted text built from the...
    lines = ["# Step 5J.2A negotiation scenario catalogue", "",
             # Include formatted text built from the embedded values in this list.
             f"- Legal movement paths: {len(paths.paths)}",
             # Include formatted text built from the embedded values in this list.
             f"- Enumerated combinations: {len(discoveries)}",
             # Include formatted text built from the embedded values in this list.
             f"- Rule-derived cycle candidates: {len(retained)}",
             # Include formatted text built from the embedded values in this list.
             f"- Synchronization status: {event['status']}", "",
             # Include formatted text built from the embedded values in this list.
             f"- Scenario specifications: {len(specifications)}",
             # Include formatted text built from the embedded values in this list.
             f"- Real SUMO episodes: {episodes}",
             # Include formatted text built from the embedded values in this list.
             f"- Next blocker: {next_blocker}"]
    # Write the supplied text to summary_path.
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Return a tuple containing payload, catalogue_path, summary_path to the caller.
    return payload, catalogue_path, summary_path
