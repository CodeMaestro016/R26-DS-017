"""Build deterministic scenario specifications from discoveries and timings."""

# Import AV_TYPE_ID, SENSOR_CONFIGURATION_SUMMARY, SUMO_NETWORK_FILE from config for the operations below.
from config import AV_TYPE_ID, SENSOR_CONFIGURATION_SUMMARY, SUMO_NETWORK_FILE
# Import RegulatoryContext from traffic_rules for the operations below.
from traffic_rules import RegulatoryContext

# Import DeterministicNegotiationScenarioScheduler from .calibration for the operations below.
from .calibration import DeterministicNegotiationScenarioScheduler
# Import NegotiationScenarioSpecification from .models for the operations below.
from .models import NegotiationScenarioSpecification


# Network identity using the inputs and processing steps below.
# Output: formatted text built from the embedded values.
def network_identity():
    # Set path to the result of SUMO_NETWORK_FILE.resolve().
    path = SUMO_NETWORK_FILE.resolve()
    # Return formatted text built from the embedded values to the caller.
    return f"{path.name}:{path.stat().st_size}"


# Build specifications using the inputs and processing steps below.
# Input discoveries: the supplied discoveries.
# Input calibrations: the supplied calibrations.
# Input path_manager: the supplied path manager.
# Output: a tuple built from the sorted values from specs.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def build_specifications(discoveries, calibrations, path_manager):
    # Set by_path to a dictionary of item.movement_path_id mapped to item for item in calibrations.
    by_path = {item.movement_path_id: item for item in calibrations}
    # Set specs to an empty list.
    specs = []
    # Iterate over discoveries, binding each item to record.
    for record in discoveries:
        # Run this branch when record.discovery_result differs from the text 'RETAINED'.
        if record.discovery_result != "RETAINED":
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set timing to a tuple built from a lazy sequence of by_path at path_id for path_id in
        # record.movement_path_ids.
        timing = tuple(by_path[path_id] for path_id in record.movement_path_ids)
        # Set (_, steps, times) to the result of DeterministicNegotiationScenarioScheduler.derive(timing).
        _, steps, times = DeterministicNegotiationScenarioScheduler.derive(timing)
        # Set family to the text 'REGULATORY_CYCLE' when the result of record.negotiation_status.endswith(the text
        # 'REGULATORY_CYCLE'), otherwise the text 'UNRESOLVED_PRECEDENCE'.
        family = ("REGULATORY_CYCLE" if record.negotiation_status.endswith("REGULATORY_CYCLE")
                  # Supply the text 'UNRESOLVED_PRECEDENCE' to the enclosing expression.
                  else "UNRESOLVED_PRECEDENCE")
        # Set identity to a tuple containing the text 'NEGOTIATION_SCENARIO_V1', the result of network_identity(),
        # family, a tuple built from the...
        identity = ("NEGOTIATION_SCENARIO_V1", network_identity(), family,
                    # Include a tuple built from the sorted values from record.movement_path_ids in this tuple.
                    tuple(sorted(record.movement_path_ids)),
                    # Include DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD in this tuple.
                    DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD,
                    # Include RegulatoryContext().profile_id in this tuple.
                    AV_TYPE_ID, RegulatoryContext().profile_id)
        # Set paths to a tuple built from a lazy sequence of path_manager.paths at path_id for path_id in
        # record.movement_path_ids.
        paths = tuple(path_manager.paths[path_id] for path_id in record.movement_path_ids)
        # Append the result of NegotiationScenarioSpecification(identity, family, record.movement_path_ids, a
        # tuple built from a lazy sequence of...) to specs.
        specs.append(NegotiationScenarioSpecification(
            # Supply record.movement_path_ids to NegotiationScenarioSpecification.
            identity, family, record.movement_path_ids,
            # Supply a tuple built from a lazy sequence of path.incoming_lane_id for path in paths to
            # NegotiationScenarioSpecification.
            tuple(path.incoming_lane_id for path in paths),
            # Supply a tuple built from a lazy sequence of formatted text built from the embedded values for index
            # in the integer range defined by the number of entries in paths to NegotiationScenarioSpecification.
            tuple(f"PARTICIPANT_{index}" for index in range(len(paths))),
            # Supply record.strongly_connected_components to NegotiationScenarioSpecification.
            record.strongly_connected_components, record.negotiation_status,
            # Supply DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD to
            # NegotiationScenarioSpecification.
            DeterministicNegotiationScenarioScheduler.SYNCHRONIZATION_METHOD,
            # Supply the result of network_identity() to NegotiationScenarioSpecification.
            steps, times, network_identity(), AV_TYPE_ID,
            # Supply RegulatoryContext().profile_id to NegotiationScenarioSpecification.
            RegulatoryContext().profile_id,
            # Supply the result of repr(a tuple built from the sorted values from key/value pairs from
            # SENSOR_CONFIGURATION_SUMMARY) to NegotiationScenarioSpecification.
            repr(tuple(sorted(SENSOR_CONFIGURATION_SUMMARY.items()))),
            "ONNX_INTENTION_DEPLOYMENT_MANIFEST", "EXHAUSTIVE_MAP_RULE_ENUMERATION",
            # Store the result of repr(record.candidate_id) under 'discovery_candidate_id'.
            {"discovery_candidate_id": repr(record.candidate_id),
             "timing_basis": "MEASURED_ISOLATED_SIMULATOR_STEPS"},
        ))
    # Return a tuple built from the sorted values from specs to the caller.
    return tuple(sorted(specs, key=lambda item: repr(item.scenario_id)))
