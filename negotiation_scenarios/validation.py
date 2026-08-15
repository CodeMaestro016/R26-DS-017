"""Auditable discovery/calibration validation and metadata serialization."""

from dataclasses import fields, is_dataclass
import json
from pathlib import Path
from collections import Counter

from config import OUTPUT_DIR
from conflict import ConflictZoneManager, MapPathManager
from map_geometry import get_intersection_geometry
from traffic_rules import TrafficRuleEngine

from .catalogue import build_specifications
from .enumerator import NegotiationScenarioEnumerator
from .readiness import (COUPLING_INCOMPLETE,
    assess_step_5j_2_scenario_readiness, assess_step_5j_3_environment_readiness,
    partition_readiness)
from .runner import calibrate_movement, RealSumoNegotiationScenarioRunner
from .calibration import verify_reproducible


def _json_safe(value):
    if is_dataclass(value):
        return {item.name: _json_safe(getattr(value, item.name))
                for item in fields(value)}
    if hasattr(value, "items"):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value


def compiled_junction_center(path_manager, junction_id=None):
    junction_id = junction_id or get_intersection_geometry().junction_id
    node = path_manager.network.getNode(junction_id)
    return tuple(float(value) for value in node.getCoord())


def validate_synchronization_event_geometry(path_manager):
    geometry = get_intersection_geometry()
    compiled = compiled_junction_center(path_manager, geometry.junction_id)
    operational = geometry.center_xy
    return {
        "event": "ObservationManager.is_in_approach_zone(position)",
        "operational_center": operational,
        "compiled_sumo_center": compiled,
        "centers_match": operational == compiled,
        "status": ("PASS" if operational == compiled else
                   "NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED"),
    }


def run_discovery_and_calibration(output_directory=OUTPUT_DIR):
    paths = MapPathManager()
    discoveries = NegotiationScenarioEnumerator(
        paths, ConflictZoneManager(paths), TrafficRuleEngine(paths)).enumerate()
    event = validate_synchronization_event_geometry(paths)
    calibrations, calibration_error = [], None
    calibration_reproducible = True
    if event["centers_match"]:
        try:
            for path_id in sorted(paths.paths):
                first = calibrate_movement(paths, path_id)
                replay = calibrate_movement(paths, path_id)
                if not verify_reproducible(first, replay):
                    calibration_reproducible = False
                    raise RuntimeError("SCENARIO_CALIBRATION_NONDETERMINISTIC")
                calibrations.append(first)
        except RuntimeError as error:
            calibration_error = str(error)
    else:
        calibration_error = event["status"]
    specifications = (build_specifications(discoveries, calibrations, paths)
                      if not calibration_error else ())
    live_coverage, protocol_traces = [], []
    readiness = None
    next_blocker = calibration_error
    episodes = 0
    if specifications:
        runner = RealSumoNegotiationScenarioRunner(paths)
        for specification in specifications:
            live, traces = runner.run(specification)
            episodes += 1
            live_coverage.extend(live)
            protocol_traces.extend(traces)
            readiness = partition_readiness(specifications, live_coverage)
            max_factors = max((len(item.proposer_decision_event_ids)
                               for item in live_coverage), default=0)
            states = {item.protocol_status for item in protocol_traces}
            if (readiness.partition_ready and max_factors > 1 and
                    {"AGREEMENT_ESTABLISHED", "PROPOSAL_REJECTED"} <= states):
                break
        readiness = partition_readiness(specifications, live_coverage)
        step_5j_2 = assess_step_5j_2_scenario_readiness(
            readiness, protocol_traces)
        if step_5j_2 != "READY_TO_RESUME_STEP_5J_2":
            if not any(item.negotiation_status.endswith("REGULATORY_CYCLE")
                       for item in live_coverage):
                next_blocker = "LIVE_REGULATORY_CYCLE_NOT_REPRODUCED"
            else:
                next_blocker = (step_5j_2[1][0] if isinstance(step_5j_2, tuple)
                                and step_5j_2[1] else
                                "NEGOTIATION_TRAINING_SCENARIO_COVERAGE_INSUFFICIENT")
        else:
            next_blocker = COUPLING_INCOMPLETE
    else:
        step_5j_2 = "NOT_EVALUATED_CALIBRATION_BLOCKED"
    step_5j_3 = assess_step_5j_3_environment_readiness(step_5j_2)
    status_counts = Counter(item.negotiation_status for item in live_coverage)
    relevant_live_coverage = tuple(
        item for item in live_coverage
        if item.negotiation_status not in {
            "NO_ACTIVE_CONFLICT", "REGULATORY_ORDER_RESOLVED"})
    payload = {
        "checkpoint": "STEP_5J_2A",
        "catalogue_status": "BLOCKED" if calibration_error else "DISCOVERED",
        "legal_movement_path_count": len(paths.paths),
        "movement_combination_count": len(discoveries),
        "regulatory_cycle_candidate_count": sum(
            item.discovery_result == "RETAINED" and
            item.negotiation_status.endswith("REGULATORY_CYCLE")
            for item in discoveries),
        "unresolved_precedence_candidate_count": sum(
            item.discovery_result == "RETAINED" and
            item.negotiation_status.endswith("UNRESOLVED_PRECEDENCE")
            for item in discoveries),
        "synchronization_event": event,
        "calibration_error": calibration_error,
        "calibration_reproducible": calibration_reproducible,
        "discoveries": [_json_safe(item) for item in discoveries],
        "calibrations": [_json_safe(item) for item in calibrations],
        "scenario_specifications": [_json_safe(item) for item in specifications],
        # Preserve every negotiation-relevant record. High-volume background
        # states are retained as exact categorical counts, not duplicated
        # actor-sized records in research metadata.
        "live_coverage": [_json_safe(item) for item in relevant_live_coverage],
        "live_snapshot_count": len(live_coverage),
        "live_snapshot_status_counts": dict(sorted(status_counts.items())),
        "protocol_traces": [_json_safe(item) for item in protocol_traces],
        "real_sumo_scenario_episodes": episodes,
        "step_5j_2_readiness": _json_safe(step_5j_2),
        "step_5j_3_readiness": _json_safe(step_5j_3),
        "next_blocker": next_blocker,
        "negotiation_action_to_traffic_outcome_status": COUPLING_INCOMPLETE,
        "route_truth_policy_leakage_count": 0,
        "learned_policy_actions_issued": 0,
        "training_runs": 0,
    }
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    catalogue_path = output / "negotiation_scenario_catalogue.json"
    catalogue_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary_path = output / "negotiation_scenario_catalogue_summary.md"
    retained = [item for item in discoveries if item.discovery_result == "RETAINED"]
    lines = ["# Step 5J.2A negotiation scenario catalogue", "",
             f"- Legal movement paths: {len(paths.paths)}",
             f"- Enumerated combinations: {len(discoveries)}",
             f"- Rule-derived cycle candidates: {len(retained)}",
             f"- Synchronization status: {event['status']}", "",
             f"- Scenario specifications: {len(specifications)}",
             f"- Real SUMO episodes: {episodes}",
             f"- Next blocker: {next_blocker}"]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload, catalogue_path, summary_path
