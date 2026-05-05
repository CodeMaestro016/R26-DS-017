#!/usr/bin/env python3
"""
SUMO TraCI Control Script: First-Come-First-Serve (FCFS) Baseline
This script implements a proper FCFS right-of-way negotiation algorithm
for autonomous vehicles at unsignalized intersections.

Author: Research Project on Autonomous Vehicle Right-of-Way Negotiation
"""

import os
import sys
import time
import traci  # SUMO's Traffic Control Interface library

# Configuration constants
SUMO_BINARY = "sumo-gui"  # Use sumo-gui for visualization, change to "sumo" for headless
SUMO_CONFIG = "unsignalized_intersection.sumocfg"  # Main configuration file
SUMO_PORT = 8813  # TraCI server port (must match config file)

# Intersection control parameters
INTERSECTION_CENTER = (0.0, 0.0)  # Center coordinates of intersection
CONTROL_ZONE_RADIUS = 20.0  # Distance from center to trigger control (meters)
INTERSECTION_CLEAR_DISTANCE = 25.0  # Distance beyond which vehicle is considered clear
PRIORITY_VEHICLE_SPEED = 13.9  # Speed for priority vehicle (m/s)
YIELDING_VEHICLE_SPEED = 2.0  # Reduced speed for yielding vehicle (m/s)
STOP_SPEED = 0.5  # Near-stop speed for yielding vehicle (m/s)

# Vehicle tracking variables
vehicle_states = {}  # Dictionary to store state information for each vehicle
current_priority_vehicle = None  # ID of vehicle that currently has priority (persistent)
current_yielding_vehicle = None  # ID of vehicle that is currently yielding
vehicles_cleared_intersection = set()  # Set of vehicles that have cleared the intersection
simulation_start_time = None  # Track when simulation started


def calculate_distance_to_intersection(vehicle_id):
    """
    Calculate the distance from a vehicle to the intersection center.
    
    Args:
        vehicle_id (str): ID of the vehicle
        
    Returns:
        float: Distance in meters from vehicle to intersection center
    """
    try:
        # Get vehicle position (x, y coordinates)
        x, y = traci.vehicle.getPosition(vehicle_id)
        
        # Calculate Euclidean distance to intersection center
        distance = ((x - INTERSECTION_CENTER[0])**2 + 
                   (y - INTERSECTION_CENTER[1])**2)**0.5
        
        return distance
    except traci.TraCIException:
        # Vehicle may have departed or doesn't exist
        return float('inf')


def get_vehicle_speed(vehicle_id):
    """
    Get the current speed of a vehicle.
    
    Args:
        vehicle_id (str): ID of the vehicle
        
    Returns:
        float: Current speed in m/s
    """
    try:
        return traci.vehicle.getSpeed(vehicle_id)
    except traci.TraCIException:
        return 0.0


def set_vehicle_speed(vehicle_id, target_speed):
    """
    Set the target speed for a vehicle.
    
    Args:
        vehicle_id (str): ID of the vehicle
        target_speed (float): Target speed in m/s
    """
    try:
        # Use TraCI to set the vehicle's maximum speed
        traci.vehicle.setMaxSpeed(vehicle_id, target_speed)
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    except traci.TraCIException as e:
        print(f"Warning: Could not set speed for {vehicle_id}: {e}")


def check_vehicles_in_control_zone():
    """
    Check which vehicles are within the intersection control zone.
    IMPORTANT: Excludes vehicles that have already cleared the intersection.
    
    Returns:
        list: Vehicle IDs that are within the control zone and haven't cleared yet
    """
    vehicles_in_zone = []
    
    # Get all vehicles currently in simulation
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Check if vehicle is within control zone AND hasn't cleared intersection yet
            if distance <= CONTROL_ZONE_RADIUS and vehicle_id not in vehicles_cleared_intersection:
                vehicles_in_zone.append(vehicle_id)
                
                # Initialize vehicle state if not already tracked
                if vehicle_id not in vehicle_states:
                    vehicle_states[vehicle_id] = {
                        'entry_time': traci.simulation.getTime(),
                        'initial_speed': get_vehicle_speed(vehicle_id),
                        'distance_at_entry': distance,
                        'has_priority': False,
                        'is_yielding': False
                    }
                    
    except traci.TraCIException:
        pass
    
    return vehicles_in_zone


def check_vehicles_cleared_intersection():
    """
    Check which vehicles have cleared the intersection (moved beyond clear distance).
    
    Returns:
        list: Vehicle IDs that have cleared the intersection
    """
    cleared_vehicles = []
    
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Check if vehicle has moved beyond the intersection
            if distance > INTERSECTION_CLEAR_DISTANCE:
                cleared_vehicles.append(vehicle_id)
                vehicles_cleared_intersection.add(vehicle_id)
                
    except traci.TraCIException:
        pass
    
    return cleared_vehicles


def apply_fcfs_logic(vehicles_in_zone):
    """
    Apply First-Come-First-Serve logic to determine right-of-way.
    IMPORTANT: Cleared vehicles can never get priority again.
    
    Args:
        vehicles_in_zone (list): Vehicle IDs in the control zone (excluding cleared vehicles)
    """
    global current_priority_vehicle, current_yielding_vehicle
    
    # If no vehicles in zone, don't change priority assignments
    if len(vehicles_in_zone) == 0:
        return
    
    # If we already have a priority vehicle that's still active, don't change it
    if current_priority_vehicle and current_priority_vehicle in traci.vehicle.getIDList():
        # Check if priority vehicle has cleared the intersection
        priority_distance = calculate_distance_to_intersection(current_priority_vehicle)
        if priority_distance > INTERSECTION_CLEAR_DISTANCE:
            # Priority vehicle has cleared - add to cleared set and remove priority
            vehicles_cleared_intersection.add(current_priority_vehicle)
            print(f"  [FCFS] {current_priority_vehicle} has cleared intersection at {traci.simulation.getTime():.1f}s")
            current_priority_vehicle = None
            current_yielding_vehicle = None  # Reset yielding vehicle when priority clears
        else:
            # Priority vehicle is still in the intersection area, keep priority
            return
    
    # If no current priority vehicle, assign one based on FCFS
    if current_priority_vehicle is None:
        # Filter out any vehicles that might have already cleared (double-check)
        available_vehicles = [v for v in vehicles_in_zone if v not in vehicles_cleared_intersection]
        
        if len(available_vehicles) == 0:
            # No available vehicles for priority assignment
            current_yielding_vehicle = None  # Clear yielding vehicle when no priority
            return
        
        if len(available_vehicles) == 1:
            # Only one vehicle available for priority
            vehicle_id = available_vehicles[0]
            current_priority_vehicle = vehicle_id
            current_yielding_vehicle = None  # No yielding vehicle when only one vehicle
            vehicle_states[vehicle_id]['has_priority'] = True
            vehicle_states[vehicle_id]['is_yielding'] = False
            print(f"  [FCFS] {vehicle_id} gets priority (only vehicle in zone) at {traci.simulation.getTime():.1f}s")
            
        elif len(available_vehicles) >= 2:
            # Multiple vehicles available, choose the one that entered first
            earliest_vehicle = None
            earliest_time = float('inf')
            
            for vehicle_id in available_vehicles:
                if vehicle_id in vehicle_states:
                    entry_time = vehicle_states[vehicle_id]['entry_time']
                    if entry_time < earliest_time:
                        earliest_time = entry_time
                        earliest_vehicle = vehicle_id
            
            if earliest_vehicle:
                current_priority_vehicle = earliest_vehicle
                vehicle_states[earliest_vehicle]['has_priority'] = True
                vehicle_states[earliest_vehicle]['is_yielding'] = False
                
                # Mark other vehicles as yielding and find the yielding vehicle
                current_yielding_vehicle = None
                for vehicle_id in available_vehicles:
                    if vehicle_id != earliest_vehicle:
                        vehicle_states[vehicle_id]['has_priority'] = False
                        vehicle_states[vehicle_id]['is_yielding'] = True
                        current_yielding_vehicle = vehicle_id  # Set yielding vehicle
                
                print(f"  [FCFS] {current_priority_vehicle} gets priority (arrived first at {earliest_time:.1f}s) at {traci.simulation.getTime():.1f}s")


def control_vehicle_speeds():
    """
    Control vehicle speeds based on priority assignments.
    IMPORTANT: Cleared vehicles cannot be marked as yielding.
    This function ensures yielding vehicles actually slow down.
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Skip vehicles that have already cleared the intersection
            if vehicle_id in vehicles_cleared_intersection:
                # Cleared vehicles get normal speed and are not yielding
                set_vehicle_speed(vehicle_id, PRIORITY_VEHICLE_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = False
                continue
            
            # Check if this is the priority vehicle
            if vehicle_id == current_priority_vehicle:
                # Priority vehicle gets normal speed
                set_vehicle_speed(vehicle_id, PRIORITY_VEHICLE_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                
            else:
                # This is not the priority vehicle and hasn't cleared yet
                if distance <= CONTROL_ZONE_RADIUS:
                    # Vehicle is in control zone but not priority - make it yield
                    if distance < 5.0:
                        # Very close to intersection, make it stop
                        set_vehicle_speed(vehicle_id, STOP_SPEED)
                    else:
                        # Approaching intersection, slow down
                        set_vehicle_speed(vehicle_id, YIELDING_VEHICLE_SPEED)
                    
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['has_priority'] = False
                    
                else:
                    # Vehicle is outside control zone, allow normal speed
                    set_vehicle_speed(vehicle_id, PRIORITY_VEHICLE_SPEED)
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['has_priority'] = False
                    
    except traci.TraCIException:
        pass


def print_simulation_status():
    """
    Print comprehensive current simulation status and vehicle information.
    Shows cleared vehicles with [CLEARED] status instead of [PRIORITY].
    """
    current_time = traci.simulation.getTime()
    
    print(f"\n=== Simulation Time: {current_time:.1f}s ===")
    
    # Print information about all vehicles
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        if len(all_vehicles) == 0:
            print("  No vehicles in simulation")
            return
        
        for vehicle_id in all_vehicles:
            speed = get_vehicle_speed(vehicle_id)
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Get vehicle state information
            state = vehicle_states.get(vehicle_id, {})
            has_priority = state.get('has_priority', False)
            is_yielding = state.get('is_yielding', False)
            
            # Print vehicle status - check if cleared first
            status = ""
            if vehicle_id in vehicles_cleared_intersection:
                status = " [CLEARED]"
            elif has_priority:
                status = " [PRIORITY]"
            elif is_yielding:
                status = " [YIELDING]"
            
            print(f"  {vehicle_id}: speed={speed:.1f}m/s, distance={distance:.1f}m{status}")
        
        # Print priority assignment (only if not cleared)
        if current_priority_vehicle and current_priority_vehicle not in vehicles_cleared_intersection:
            print(f"  Priority: {current_priority_vehicle}")
        else:
            print("  Priority: None")
        
        # Print yielding vehicles (only if not cleared)
        yielding_vehicles = []
        for vehicle_id in all_vehicles:
            if (vehicle_id in vehicle_states and 
                vehicle_states[vehicle_id].get('is_yielding', False) and 
                vehicle_id not in vehicles_cleared_intersection):
                yielding_vehicles.append(vehicle_id)
        
        if yielding_vehicles:
            print(f"  Yielding: {', '.join(yielding_vehicles)}")
        elif current_yielding_vehicle is None:
            print("  Yielding: None")
        
        # Print cleared vehicles
        if vehicles_cleared_intersection:
            print(f"  Cleared intersection: {', '.join(vehicles_cleared_intersection)}")
            
    except traci.TraCIException:
        print("  No vehicles in simulation")


def print_final_summary():
    """
    Print a comprehensive final summary of the simulation results.
    """
    current_time = traci.simulation.getTime()
    
    print("\n" + "="*50)
    print("FINAL SIMULATION SUMMARY")
    print("="*50)
    
    # Check completion status for each expected vehicle
    expected_vehicles = ['vehicle_A', 'vehicle_B']
    
    for vehicle_id in expected_vehicles:
        if vehicle_id in vehicles_cleared_intersection:
            print(f"  {vehicle_id} completed: True")
        else:
            print(f"  {vehicle_id} completed: False")
    
    print(f"  Total simulation time: {current_time:.1f}s")
    
    # Determine FCFS result
    if len(vehicles_cleared_intersection) == len(expected_vehicles):
        print(f"  FCFS baseline result: success (no collision)")
    else:
        print(f"  FCFS baseline result: incomplete (some vehicles didn't complete)")
    
    print("="*50)


def check_simulation_completion():
    """
    Check if all vehicles have completed their routes.
    
    Returns:
        bool: True if simulation should end, False otherwise
    """
    try:
        # Check if there are still vehicles in simulation
        remaining_vehicles = traci.vehicle.getIDList()
        
        if len(remaining_vehicles) == 0:
            print("\n=== Simulation Complete ===")
            print("All vehicles have completed their routes.")
            print_final_summary()
            return True
        
        # End simulation after reasonable time (60 seconds)
        if traci.simulation.getTime() > 60.0:
            print("\n=== Simulation Timeout ===")
            print("Simulation ended after 60 seconds.")
            print_final_summary()
            return True
            
    except traci.TraCIException:
        return True
    
    return False


def run_simulation():
    """
    Main simulation loop with proper FCFS control logic.
    """
    global simulation_start_time
    
    print("=== Starting FCFS Baseline Simulation ===")
    print("Intersection: Unsignalized four-way intersection")
    print("Control Logic: First-Come-First-Serve (FCFS)")
    print(f"Control Zone Radius: {CONTROL_ZONE_RADIUS}m")
    print(f"Intersection Clear Distance: {INTERSECTION_CLEAR_DISTANCE}m")
    print(f"Priority Vehicle Speed: {PRIORITY_VEHICLE_SPEED}m/s")
    print(f"Yielding Vehicle Speed: {YIELDING_VEHICLE_SPEED}m/s")
    
    # Start SUMO with TraCI
    try:
        # Command to start SUMO with TraCI - use more robust parameters
        sumo_cmd = [
            SUMO_BINARY, 
            "-c", SUMO_CONFIG, 
            "--quit-on-end",  # Automatically close when simulation ends
            "--start",        # Start simulation immediately
            "--collision.check-junctions", "true",  # Enable collision checking
            "--step-length", "0.1"  # Fixed step length
        ]
        
        print(f"\nStarting SUMO: {' '.join(sumo_cmd)}")
        
        # Use sumolib to check if we can find SUMO first
        try:
            import sumolib
        except ImportError:
            print("Warning: sumolib not available, continuing with traci.start...")
        
        # Start TraCI connection
        traci.start(sumo_cmd)
        
        # Give SUMO a moment to initialize
        time.sleep(0.5)
        
        # Test the connection
        try:
            traci.simulation.getTime()  # Use the non-deprecated method
            simulation_start_time = time.time()
            print("TraCI connection established successfully!")
        except traci.TraCIException as e:
            print(f"Error testing TraCI connection: {e}")
            raise
        
        # Main simulation loop
        step = 0
        while True:
            # Perform one simulation step
            traci.simulationStep()
            step += 1
            
            # Print status every 10 steps (every 1 second)
            if step % 10 == 0:
                print_simulation_status()
            
            # Check which vehicles are in the control zone
            vehicles_in_zone = check_vehicles_in_control_zone()
            
            # Check which vehicles have cleared the intersection
            check_vehicles_cleared_intersection()
            
            # Apply FCFS logic to determine priority
            apply_fcfs_logic(vehicles_in_zone)
            
            # Control vehicle speeds based on priority
            control_vehicle_speeds()
            
            # Check if simulation should end
            if check_simulation_completion():
                break
                
    except traci.TraCIException as e:
        print(f"TraCI Error: {e}")
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Always close TraCI connection
        try:
            traci.close()
            print("TraCI connection closed.")
        except:
            pass


def main():
    """
    Main function to run the FCFS baseline simulation.
    """
    # Check if SUMO is installed and available
    try:
        import traci
    except ImportError:
        print("Error: traci module not found!")
        print("Please install SUMO and ensure traci is in your Python path.")
        sys.exit(1)
    
    # Check if configuration file exists
    if not os.path.exists(SUMO_CONFIG):
        print(f"Error: Configuration file '{SUMO_CONFIG}' not found!")
        print("Please ensure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Run the simulation
    run_simulation()


if __name__ == "__main__":
    main()
