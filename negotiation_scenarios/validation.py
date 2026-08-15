"""Auditable discovery/calibration validation and metadata serialization."""

from dataclasses import fields, is_dataclass
import json
from pathlib import Path

from config import INTERSECTION_CENTER, OUTPUT_DIR, SUMO_NETWORK_FILE
from conflict import ConflictZoneManager, MapPathManager
from traffic_rules import TrafficRuleEngine

from .enumerator import NegotiationScenarioEnumerator
from .runner import calibrate_movement


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


def compiled_junction_center(path_manager, junction_id="center"):
    node = path_manager.network.getNode(junction_id)
    return tuple(float(value) for value in node.getCoord())


def validate_synchronization_event_geometry(path_manager):
    compiled = compiled_junction_center(path_manager)
    configured = tuple(float(value) for value in INTERSECTION_CENTER)
    return {
        "event": "ObservationManager.is_in_approach_zone(position)",
        "configured_center": configured,
        "compiled_sumo_center": compiled,
        "centers_match": configured == compiled,
        "status": ("PASS" if configured == compiled else
                   "NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED"),
    }


def run_discovery_and_calibration(output_directory=OUTPUT_DIR):
    paths = MapPathManager()
    discoveries = NegotiationScenarioEnumerator(
        paths, ConflictZoneManager(paths), TrafficRuleEngine(paths)).enumerate()
    event = validate_synchronization_event_geometry(paths)
    calibrations, calibration_error = [], None
    if event["centers_match"]:
        try:
            for path_id in sorted(paths.paths):
                calibrations.append(calibrate_movement(paths, path_id))
        except RuntimeError as error:
            calibration_error = str(error)
    else:
        calibration_error = event["status"]
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
        "discoveries": [_json_safe(item) for item in discoveries],
        "calibrations": [_json_safe(item) for item in calibrations],
        "scenario_specifications": [],
        "live_coverage": [],
        "protocol_traces": [],
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
             "Discovery is map/rule-derived. Live scenario specifications are not "
             "created while synchronization is blocked."]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload, catalogue_path, summary_path
