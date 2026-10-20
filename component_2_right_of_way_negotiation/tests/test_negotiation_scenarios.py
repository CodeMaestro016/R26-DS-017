# Import FrozenInstanceError from dataclasses for the operations below.
from dataclasses import FrozenInstanceError

# Import pytest for use in this module.
import pytest

# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import RegulatoryPrecedenceGraphBuilder from negotiation_learning.precedence_graph for the operations below.
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
# Import DeterministicNegotiationScenarioScheduler, MovementTimingCalibrationRecord,
# NegotiationScenarioEnumerator, validate_synchronization_event_geometry from negotiation_scenarios for the
# operations below.
from negotiation_scenarios import (
    DeterministicNegotiationScenarioScheduler,
    MovementTimingCalibrationRecord,
    NegotiationScenarioEnumerator,
    validate_synchronization_event_geometry,
)
# Import TrafficRuleEngine from traffic_rules for the operations below.
from traffic_rules import TrafficRuleEngine


# Apply pytest.fixture(scope='module') as a decorator to configure the following definition.
@pytest.fixture(scope="module")
# Discovery using the inputs and processing steps below.
# Output: a tuple containing paths, the result of enumerator.enumerate(), the result of enumerator.enumerate().
def discovery():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set enumerator to the result of NegotiationScenarioEnumerator(paths, the result of
    # ConflictZoneManager(paths), the result of TrafficRuleEngine(paths)).
    enumerator = NegotiationScenarioEnumerator(
        # Supply the result of ConflictZoneManager(paths) to NegotiationScenarioEnumerator.
        paths, ConflictZoneManager(paths), TrafficRuleEngine(paths))
    # Return a tuple containing paths, the result of enumerator.enumerate(), the result of enumerator.enumerate()
    # to the caller.
    return paths, enumerator.enumerate(), enumerator.enumerate()


# Check deterministic exhaustive map enumeration using the setup, calls, and assertions below.
# Input discovery: the supplied discovery.
# Output: no explicit value; normal completion returns None.
def test_deterministic_exhaustive_map_enumeration(discovery):
    # Set (paths, first, second) to discovery.
    paths, first, second = discovery
    # Require the number of entries in paths.paths equals 12; otherwise raise AssertionError.
    assert len(paths.paths) == 12
    # Require first equals second; otherwise raise AssertionError.
    assert first == second
    # Require whether every item is true in a lazy sequence of a set built from item.movement_path_ids is at most
    # a set built from paths.paths for item in first; otherwise raise AssertionError.
    assert all(set(item.movement_path_ids) <= set(paths.paths) for item in first)
    # Require the number of entries in a set of item.candidate_id for item in first equals the number of entries
    # in first; otherwise raise AssertionError.
    assert len({item.candidate_id for item in first}) == len(first)


# Check cycle classification is reconstructed by graph algorithm using the setup, calls, and assertions below.
# Input discovery: the supplied discovery.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_cycle_classification_is_reconstructed_by_graph_algorithm(discovery):
    # Set (_, records, _) to discovery.
    _, records, _ = discovery
    # Set cycles to a list of item for item in records; retain entries satisfying item.discovery_result equals the
    # text 'RETAINED'.
    cycles = [item for item in records if item.discovery_result == "RETAINED"]
    # Require cycles; otherwise raise AssertionError.
    assert cycles
    # Iterate over cycles, binding each item to item.
    for item in cycles:
        # Set edges to a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
        # priority_vehicle_id for (a, b) in item.regulatory_edges.
        edges = tuple({"yielding_vehicle_id": a, "priority_vehicle_id": b}
                      # Evaluate item.regulatory_edges as part of the enclosing expression.
                      for a, b in item.regulatory_edges)
        # Set analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(item.movement_path_ids, edges).
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            # Supply item.movement_path_ids to RegulatoryPrecedenceGraphBuilder.analyse.
            item.movement_path_ids, edges)
        # Require analysis at 'cycle_detected'; otherwise raise AssertionError.
        assert analysis["cycle_detected"]
        # Require analysis at 'strongly_connected_components' equals item.strongly_connected_components; otherwise
        # raise AssertionError.
        assert analysis["strongly_connected_components"] == item.strongly_connected_components


# Calibration using the inputs and processing steps below.
# Input path_id: the supplied path id.
# Input steps: the supplied steps.
# Output: the result of MovementTimingCalibrationRecord(path_id, the text 'route', 0.04, 0, 1, 1 plus steps,
# steps, steps multiplied by 0.04, the text...).
def _calibration(path_id, steps):
    # Return the result of MovementTimingCalibrationRecord(path_id, the text 'route', 0.04, 0, 1, 1 plus steps,
    # steps, steps multiplied by 0.04, the text...) to the caller.
    return MovementTimingCalibrationRecord(
        # Supply steps multiplied by 0.04 to MovementTimingCalibrationRecord.
        path_id, "route", 0.04, 0, 1, 1 + steps, steps, steps * 0.04,
        # Store the text 'test' under 'source'.
        "AV", "network", {"source": "test"})


# Check exact synchronization equation has no margin using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_exact_synchronization_equation_has_no_margin():
    # Set records to a tuple containing the result of _calibration(the text 'B', 3), the result of
    # _calibration(the text 'A', 5).
    records = (_calibration("B", 3), _calibration("A", 5))
    # Set (target, spawn_steps, spawn_times) to the result of
    # DeterministicNegotiationScenarioScheduler.derive(records).
    target, spawn_steps, spawn_times = DeterministicNegotiationScenarioScheduler.derive(records)
    # Require target equals 5; otherwise raise AssertionError.
    assert target == 5
    # Require spawn_steps equals a tuple containing 0, 2; otherwise raise AssertionError.
    assert spawn_steps == (0, 2)
    # Require spawn_times equals a tuple containing 0.0, 0.08; otherwise raise AssertionError.
    assert spawn_times == (0.0, 0.08)
    # Iterate over corresponding items paired from spawn_steps, the sorted values from records, binding each item
    # to (spawn, record).
    for spawn, record in zip(spawn_steps, sorted(records, key=lambda x: x.movement_path_id)):
        # Require spawn plus record.departure_to_event_steps equals target; otherwise raise AssertionError.
        assert spawn + record.departure_to_event_steps == target


# Check calibration record is immutable and integer timed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_calibration_record_is_immutable_and_integer_timed():
    # Set record to the result of _calibration(the text 'A', 5).
    record = _calibration("A", 5)
    # Enter the result of pytest.raises(FrozenInstanceError) and run the enclosed operations within that context.
    with pytest.raises(FrozenInstanceError):
        # Set record.departure_to_event_steps to 7.
        record.departure_to_event_steps = 7
    # Enter the result of pytest.raises(TypeError) and run the enclosed operations within that context.
    with pytest.raises(TypeError):
        # Call MovementTimingCalibrationRecord with the supplied arguments.
        MovementTimingCalibrationRecord(
            # Supply an empty dictionary to MovementTimingCalibrationRecord.
            "A", "route", .04, 0, 1, 2, 1.0, .04, "AV", "network", {})


# Check existing approach event uses compiled geometry using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_existing_approach_event_uses_compiled_geometry():
    # Set result to the result of validate_synchronization_event_geometry(the result of MapPathManager()).
    result = validate_synchronization_event_geometry(MapPathManager())
    # Require result at 'event' equals the text 'ObservationManager.is_in_approach_zone(position)'; otherwise
    # raise AssertionError.
    assert result["event"] == "ObservationManager.is_in_approach_zone(position)"
    # Require result at 'status' equals the text 'PASS'; otherwise raise AssertionError.
    assert result["status"] == "PASS"
    # Require result at 'centers_match'; otherwise raise AssertionError.
    assert result["centers_match"]
