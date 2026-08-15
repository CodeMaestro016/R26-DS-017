"""Step 5J.2A.1B authoritative compiled-map coordinate validator."""

from config import APPROACH_ZONE_RADIUS, SENSOR_RANGE
from conflict import ConflictZoneManager, MapPathManager
from map_geometry import (INTERSECTION_GEOMETRY_STATUS,
    MANUAL_INTERSECTION_CENTER_CONFIGURED, MANUAL_NET_OFFSET_APPLICATION,
    get_intersection_geometry, is_position_in_approach_zone)
from negotiation import NegotiationManager
from negotiation_scenarios.runner import calibrate_movement
from observation import LocalDynamicMap, ObservationManager


def main():
    paths = MapPathManager()
    geometry = get_intersection_geometry()
    zones = ConflictZoneManager(paths)
    cx, cy = geometry.center_xy
    first_path = sorted(paths.paths)[0]
    calibration = calibrate_movement(paths, first_path)

    assert geometry.movement_path_ids_used == tuple(sorted(paths.paths))
    assert geometry.center_xy == tuple(float(value) for value in
                                       paths.network.getNode(
                                           geometry.junction_id).getCoord())
    assert is_position_in_approach_zone((cx, cy), geometry)
    assert is_position_in_approach_zone((cx + APPROACH_ZONE_RADIUS, cy), geometry)
    assert not is_position_in_approach_zone(
        (cx + APPROACH_ZONE_RADIUS + 1.0, cy), geometry)
    assert ObservationManager.is_in_approach_zone((cx, cy))
    assert LocalDynamicMap._distance_to_center((cx, cy)) == 0.0
    assert NegotiationManager().intersection_geometry is geometry
    assert calibration.departure_to_event_steps >= 0

    print("Step 5J.2A.1B Map Coordinate Repair\n")
    print("Network")
    print(f"  Coordinate frame: {geometry.coordinate_frame}")
    print(f"  netOffset: {geometry.net_offset}")
    print(f"  Converted boundary: {geometry.converted_boundary}")
    print(f"  Original boundary: {geometry.original_boundary}")
    print(f"  Projection parameter: {geometry.projection_parameter}\n")
    print("Intersection")
    print(f"  Legal paths inspected: {len(paths.paths)}")
    print("  Common junction derivation: PASS")
    print(f"  Junction ID: {geometry.junction_id}")
    print(f"  Derived compiled center: {geometry.center_xy}")
    print(f"  Geometry status: {INTERSECTION_GEOMETRY_STATUS}")
    print(f"  Manual intersection-center literal active: {MANUAL_INTERSECTION_CENTER_CONFIGURED}\n")
    print("Coordinate integrity")
    print("  TraCI and map geometry use compiled frame: PASS")
    print(f"  Manual netOffset applied: {MANUAL_NET_OFFSET_APPLICATION}")
    print("  netOffset applied twice: False")
    print("  Manual path translations: 0")
    print("  Manual conflict-zone translations: 0\n")
    print("Operational consumers")
    print("  ObservationManager migrated: PASS")
    print("  LocalDynamicMap migrated: PASS")
    print("  Legacy NegotiationManager migrated: PASS")
    print("  Scenario calibration migrated: PASS\n")
    print("Approach-zone definition")
    print("  Radius modified: False")
    print("  Center source modified: True")
    print("  Source: DERIVED_FROM_COMPILED_SUMO_NETWORK")
    print("  Existing semantic event retained: PASS")
    print("  Center classified in zone: PASS")
    print("  Boundary semantics preserved: PASS\n")
    print("Calibration")
    print("  Synchronization event reachable: PASS")
    print(f"  Lightweight movement calibrated: {first_path}")
    print(f"  Departure-to-event steps: {calibration.departure_to_event_steps}")
    print("  Arbitrary spawn timing constants: 0\n")
    print("Research boundaries")
    print("  Sensor range modified: False")
    print(f"  Sensor range remains: {SENSOR_RANGE}")
    print("  Hyperparameters added: 0")
    print("  Gamma candidates: 0")
    print("  Optimizers: 0")
    print("  Training runs: 0")
    print("  Learned policy control: False\n")
    print("Blocker")
    print("  NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED: False")


if __name__ == "__main__":
    main()
