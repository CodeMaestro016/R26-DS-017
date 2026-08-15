"""Build deterministic scenario specifications from discoveries and timings."""

from config import AV_TYPE_ID, SENSOR_CONFIGURATION_SUMMARY, SUMO_NETWORK_FILE
from traffic_rules import RegulatoryContext

from .calibration import DeterministicNegotiationScenarioScheduler
from .models import NegotiationScenarioSpecification


def network_identity():
    path = SUMO_NETWORK_FILE.resolve()
    return f"{path.name}:{path.stat().st_size}"


def build_specifications(discoveries, calibrations, path_manager):
    by_path = {item.movement_path_id: item for item in calibrations}
    specs = []
    for record in discoveries:
        if record.discovery_result != "RETAINED":
            continue
        timing = tuple(by_path[path_id] for path_id in record.movement_path_ids)
        _, steps, times = DeterministicNegotiationScenarioScheduler.derive(timing)
        family = ("REGULATORY_CYCLE" if record.negotiation_status.endswith("REGULATORY_CYCLE")
                  else "UNRESOLVED_PRECEDENCE")
        identity = ("NEGOTIATION_SCENARIO_V1", network_identity(), family,
                    tuple(sorted(record.movement_path_ids)),
                    DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD,
                    AV_TYPE_ID, RegulatoryContext().profile_id)
        paths = tuple(path_manager.paths[path_id] for path_id in record.movement_path_ids)
        specs.append(NegotiationScenarioSpecification(
            identity, family, record.movement_path_ids,
            tuple(path.incoming_lane_id for path in paths),
            tuple(f"PARTICIPANT_{index}" for index in range(len(paths))),
            record.strongly_connected_components, record.negotiation_status,
            DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD,
            steps, times, network_identity(), AV_TYPE_ID,
            RegulatoryContext().profile_id,
            repr(tuple(sorted(SENSOR_CONFIGURATION_SUMMARY.items()))),
            "ONNX_INTENTION_DEPLOYMENT_MANIFEST", "EXHAUSTIVE_MAP_RULE_ENUMERATION",
            {"discovery_candidate_id": repr(record.candidate_id),
             "timing_basis": "MEASURED_ISOLATED_SIMULATOR_STEPS"},
        ))
    return tuple(sorted(specs, key=lambda item: repr(item.scenario_id)))
