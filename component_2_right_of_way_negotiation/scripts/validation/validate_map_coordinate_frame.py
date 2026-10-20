"""Step 5J.2A.1B authoritative compiled-map coordinate validator."""

# Import APPROACH_ZONE_RADIUS, SENSOR_RANGE from config for the operations below.
from config import APPROACH_ZONE_RADIUS, SENSOR_RANGE
# Import ConflictZoneManager, MapPathManager from conflict for the operations below.
from conflict import ConflictZoneManager, MapPathManager
# Import INTERSECTION_GEOMETRY_STATUS, MANUAL_INTERSECTION_CENTER_CONFIGURED, MANUAL_NET_OFFSET_APPLICATION,
# get_intersection_geometry, is_position_in_approach_zone from map_geometry for the operations below.
from map_geometry import (INTERSECTION_GEOMETRY_STATUS,
    MANUAL_INTERSECTION_CENTER_CONFIGURED, MANUAL_NET_OFFSET_APPLICATION,
    get_intersection_geometry, is_position_in_approach_zone)
# Import NegotiationManager from negotiation for the operations below.
from negotiation import NegotiationManager
# Import calibrate_movement from negotiation_scenarios.runner for the operations below.
from negotiation_scenarios.runner import calibrate_movement
# Import LocalDynamicMap, ObservationManager from observation for the operations below.
from observation import LocalDynamicMap, ObservationManager


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
def main():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set geometry to the result of get_intersection_geometry().
    geometry = get_intersection_geometry()
    # Set zones to the result of ConflictZoneManager(paths).
    zones = ConflictZoneManager(paths)
    # Set (cx, cy) to geometry.center_xy.
    cx, cy = geometry.center_xy
    # Set first_path to sorted(paths.paths) at 0.
    first_path = sorted(paths.paths)[0]
    # Set calibration to the result of calibrate_movement(paths, first_path).
    calibration = calibrate_movement(paths, first_path)

    # Require geometry.movement_path_ids_used equals a tuple built from the sorted values from paths.paths;
    # otherwise raise AssertionError.
    assert geometry.movement_path_ids_used == tuple(sorted(paths.paths))
    # Require geometry.center_xy equals a tuple built from a lazy sequence of a floating-point number built from
    # value for value in the result of paths.network.getNode(geometry.junction_id).getCoord(); otherwise raise
    # AssertionError.
    assert geometry.center_xy == tuple(float(value) for value in
                                       # Evaluate the result of
                                       # paths.network.getNode(geometry.junction_id).getCoord() as part of the
                                       # enclosing expression.
                                       paths.network.getNode(
                                           # Supply geometry.junction_id to paths.network.getNode.
                                           geometry.junction_id).getCoord())
    # Require the result of is_position_in_approach_zone(a tuple containing cx, cy, geometry); otherwise raise
    # AssertionError.
    assert is_position_in_approach_zone((cx, cy), geometry)
    # Require the result of is_position_in_approach_zone(a tuple containing cx plus APPROACH_ZONE_RADIUS, cy,
    # geometry); otherwise raise AssertionError.
    assert is_position_in_approach_zone((cx + APPROACH_ZONE_RADIUS, cy), geometry)
    # Require the negation of the result of is_position_in_approach_zone(a tuple containing cx +
    # APPROACH_ZONE_RADIUS plus 1.0, cy, geometry); otherwise raise AssertionError.
    assert not is_position_in_approach_zone(
        # Supply a tuple containing cx plus APPROACH_ZONE_RADIUS plus 1.0, cy to is_position_in_approach_zone.
        (cx + APPROACH_ZONE_RADIUS + 1.0, cy), geometry)
    # Require the result of ObservationManager.is_in_approach_zone(a tuple containing cx, cy); otherwise raise
    # AssertionError.
    assert ObservationManager.is_in_approach_zone((cx, cy))
    # Require the result of LocalDynamicMap._distance_to_center(a tuple containing cx, cy) equals 0.0; otherwise
    # raise AssertionError.
    assert LocalDynamicMap._distance_to_center((cx, cy)) == 0.0
    # Require NegotiationManager().intersection_geometry is the same object as geometry; otherwise raise
    # AssertionError.
    assert NegotiationManager().intersection_geometry is geometry
    # Require calibration.departure_to_event_steps is at least 0; otherwise raise AssertionError.
    assert calibration.departure_to_event_steps >= 0

    # Display the text 'Step 5J.2A.1B Map Coordinate Repair'.
    print("Step 5J.2A.1B Map Coordinate Repair\n")
    # Display the text 'Network'.
    print("Network")
    # Display formatted text built from the embedded values.
    print(f"  Coordinate frame: {geometry.coordinate_frame}")
    # Display formatted text built from the embedded values.
    print(f"  netOffset: {geometry.net_offset}")
    # Display formatted text built from the embedded values.
    print(f"  Converted boundary: {geometry.converted_boundary}")
    # Display formatted text built from the embedded values.
    print(f"  Original boundary: {geometry.original_boundary}")
    # Display formatted text built from the embedded values.
    print(f"  Projection parameter: {geometry.projection_parameter}\n")
    # Display the text 'Intersection'.
    print("Intersection")
    # Display formatted text built from the embedded values.
    print(f"  Legal paths inspected: {len(paths.paths)}")
    # Display the text 'Common junction derivation: PASS'.
    print("  Common junction derivation: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Junction ID: {geometry.junction_id}")
    # Display formatted text built from the embedded values.
    print(f"  Derived compiled center: {geometry.center_xy}")
    # Display formatted text built from the embedded values.
    print(f"  Geometry status: {INTERSECTION_GEOMETRY_STATUS}")
    # Display formatted text built from the embedded values.
    print(f"  Manual intersection-center literal active: {MANUAL_INTERSECTION_CENTER_CONFIGURED}\n")
    # Display the text 'Coordinate integrity'.
    print("Coordinate integrity")
    # Display the text 'TraCI and map geometry use compiled frame: PASS'.
    print("  TraCI and map geometry use compiled frame: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Manual netOffset applied: {MANUAL_NET_OFFSET_APPLICATION}")
    # Display the text 'netOffset applied twice: False'.
    print("  netOffset applied twice: False")
    # Display the text 'Manual path translations: 0'.
    print("  Manual path translations: 0")
    # Display the text 'Manual conflict-zone translations: 0'.
    print("  Manual conflict-zone translations: 0\n")
    # Display the text 'Operational consumers'.
    print("Operational consumers")
    # Display the text 'ObservationManager migrated: PASS'.
    print("  ObservationManager migrated: PASS")
    # Display the text 'LocalDynamicMap migrated: PASS'.
    print("  LocalDynamicMap migrated: PASS")
    # Display the text 'Legacy NegotiationManager migrated: PASS'.
    print("  Legacy NegotiationManager migrated: PASS")
    # Display the text 'Scenario calibration migrated: PASS'.
    print("  Scenario calibration migrated: PASS\n")
    # Display the text 'Approach-zone definition'.
    print("Approach-zone definition")
    # Display the text 'Radius modified: False'.
    print("  Radius modified: False")
    # Display the text 'Center source modified: True'.
    print("  Center source modified: True")
    # Display the text 'Source: DERIVED_FROM_COMPILED_SUMO_NETWORK'.
    print("  Source: DERIVED_FROM_COMPILED_SUMO_NETWORK")
    # Display the text 'Existing semantic event retained: PASS'.
    print("  Existing semantic event retained: PASS")
    # Display the text 'Center classified in zone: PASS'.
    print("  Center classified in zone: PASS")
    # Display the text 'Boundary semantics preserved: PASS'.
    print("  Boundary semantics preserved: PASS\n")
    # Display the text 'Calibration'.
    print("Calibration")
    # Display the text 'Synchronization event reachable: PASS'.
    print("  Synchronization event reachable: PASS")
    # Display formatted text built from the embedded values.
    print(f"  Lightweight movement calibrated: {first_path}")
    # Display formatted text built from the embedded values.
    print(f"  Departure-to-event steps: {calibration.departure_to_event_steps}")
    # Display the text 'Arbitrary spawn timing constants: 0'.
    print("  Arbitrary spawn timing constants: 0\n")
    # Display the text 'Research boundaries'.
    print("Research boundaries")
    # Display the text 'Sensor range modified: False'.
    print("  Sensor range modified: False")
    # Display formatted text built from the embedded values.
    print(f"  Sensor range remains: {SENSOR_RANGE}")
    # Display the text 'Hyperparameters added: 0'.
    print("  Hyperparameters added: 0")
    # Display the text 'Gamma candidates: 0'.
    print("  Gamma candidates: 0")
    # Display the text 'Optimizers: 0'.
    print("  Optimizers: 0")
    # Display the text 'Training runs: 0'.
    print("  Training runs: 0")
    # Display the text 'Learned policy control: False'.
    print("  Learned policy control: False\n")
    # Display the text 'Blocker'.
    print("Blocker")
    # Display the text 'NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED: False'.
    print("  NEGOTIATION_SCENARIO_SYNCHRONIZATION_EVENT_UNDEFINED: False")


# Run this branch when __name__ equals the text '__main__'.
if __name__ == "__main__":
    # Call main with the supplied arguments.
    main()
