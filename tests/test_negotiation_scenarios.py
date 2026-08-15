from dataclasses import FrozenInstanceError

import pytest

from conflict import ConflictZoneManager, MapPathManager
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder
from negotiation_scenarios import (
    DeterministicNegotiationScenarioScheduler,
    MovementTimingCalibrationRecord,
    NegotiationScenarioEnumerator,
    validate_synchronization_event_geometry,
)
from traffic_rules import TrafficRuleEngine


@pytest.fixture(scope="module")
def discovery():
    paths = MapPathManager()
    enumerator = NegotiationScenarioEnumerator(
        paths, ConflictZoneManager(paths), TrafficRuleEngine(paths))
    return paths, enumerator.enumerate(), enumerator.enumerate()


def test_deterministic_exhaustive_map_enumeration(discovery):
    paths, first, second = discovery
    assert len(paths.paths) == 12
    assert first == second
    assert all(set(item.movement_path_ids) <= set(paths.paths) for item in first)
    assert len({item.candidate_id for item in first}) == len(first)


def test_cycle_classification_is_reconstructed_by_graph_algorithm(discovery):
    _, records, _ = discovery
    cycles = [item for item in records if item.discovery_result == "RETAINED"]
    assert cycles
    for item in cycles:
        edges = tuple({"yielding_vehicle_id": a, "priority_vehicle_id": b}
                      for a, b in item.regulatory_edges)
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(
            item.movement_path_ids, edges)
        assert analysis["cycle_detected"]
        assert analysis["strongly_connected_components"] == item.strongly_connected_components


def _calibration(path_id, steps):
    return MovementTimingCalibrationRecord(
        path_id, "route", 0.04, 0, 1, 1 + steps, steps, steps * 0.04,
        "AV", "network", {"source": "test"})


def test_exact_synchronization_equation_has_no_margin():
    records = (_calibration("B", 3), _calibration("A", 5))
    target, spawn_steps, spawn_times = DeterministicNegotiationScenarioScheduler.derive(records)
    assert target == 5
    assert spawn_steps == (0, 2)
    assert spawn_times == (0.0, 0.08)
    for spawn, record in zip(spawn_steps, sorted(records, key=lambda x: x.movement_path_id)):
        assert spawn + record.departure_to_event_steps == target


def test_calibration_record_is_immutable_and_integer_timed():
    record = _calibration("A", 5)
    with pytest.raises(FrozenInstanceError):
        record.departure_to_event_steps = 7
    with pytest.raises(TypeError):
        MovementTimingCalibrationRecord(
            "A", "route", .04, 0, 1, 2, 1.0, .04, "AV", "network", {})


def test_existing_approach_event_reports_compiled_geometry_mismatch():
    result = validate_synchronization_event_geometry(MapPathManager())
    assert result["event"] == "ObservationManager.is_in_approach_zone(position)"
    assert result["status"] == "NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED"
    assert not result["centers_match"]
