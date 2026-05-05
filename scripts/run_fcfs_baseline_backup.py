#!/usr/bin/env python3
"""
SUMO TraCI Control Script: First-Come-First-Serve (FCFS) Baseline
This script implements a simple FCFS right-of-way negotiation algorithm
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
CONTROL_ZONE_RADIUS = 15.0  # Distance from center to trigger control (meters)
PRIORITY_VEHICLE_SPEED = 13.9  # Speed for priority vehicle (m/s)
YIELDING_VEHICLE_SPEED = 2.0  # Reduced speed for yielding vehicle (m/s)
STOP_SPEED = 0.5  # Near-stop speed for yielding vehicle (m/s)

# Vehicle tracking variables
vehicle_states = {}  # Dictionary to store state information for each vehicle
priority_vehicle = None  # ID of vehicle that currently has priority
yielding_vehicle = None  # ID of vehicle that should yield
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
    
    Returns:
        list: Vehicle IDs that are within the control zone
    """
    vehicles_in_zone = []
    
    # Get all vehicles currently in simulation
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Check if vehicle is within control zone
            if distance <= CONTROL_ZONE_RADIUS:
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


def apply_fcfs_logic(vehicles_in_zone):
    """
    Apply First-Come-First-Serve logic to determine right-of-way.
    
    Args:
        vehicles_in_zone (list): Vehicle IDs in the control zone
    """
    global priority_vehicle, yielding_vehicle
    
    # If no vehicles in zone, reset priority assignments
    if len(vehicles_in_zone) == 0:
        priority_vehicle = None
        yielding_vehicle = None
        return
    
    # If only one vehicle in zone, it gets priority
    if len(vehicles_in_zone) == 1:
        vehicle_id = vehicles_in_zone[0]
        if priority_vehicle != vehicle_id:
            priority_vehicle = vehicle_id
            yielding_vehicle = None
            vehicle_states[vehicle_id]['has_priority'] = True
            vehicle_states[vehicle_id]['is_yielding'] = False
            print(f"  [FCFS] {vehicle_id} gets priority (only vehicle in zone)")
        return
    
    # If two vehicles in zone, apply FCFS
    if len(vehicles_in_zone) == 2:
        # Get entry times for both vehicles
        vehicle1, vehicle2 = vehicles_in_zone
        time1 = vehicle_states[vehicle1]['entry_time']
        time2 = vehicle_states[vehicle2]['entry_time']
        
        # Determine which vehicle arrived first
        if time1 <= time2:
            new_priority = vehicle1
            new_yielding = vehicle2
        else:
            new_priority = vehicle2
            new_yielding = vehicle1
        
        # Update priority assignments if changed
        if priority_vehicle != new_priority:
            priority_vehicle = new_priority
            yielding_vehicle = new_yielding
            
            # Update vehicle states
            vehicle_states[priority_vehicle]['has_priority'] = True
            vehicle_states[priority_vehicle]['is_yielding'] = False
            vehicle_states[yielding_vehicle]['has_priority'] = False
            vehicle_states[yielding_vehicle]['is_yielding'] = True
            
            print(f"  [FCFS] {priority_vehicle} gets priority (arrived at {time1:.1f}s)")
            print(f"  [FCFS] {yielding_vehicle} must yield (arrived at {time2:.1f}s)")


def control_vehicle_speeds():
    """
    Control vehicle speeds based on priority assignments.
    """
    # Control priority vehicle - allow normal speed
    if priority_vehicle and traci.vehicle.getIDCount() > 0:
        if priority_vehicle in traci.vehicle.getIDList():
            set_vehicle_speed(priority_vehicle, PRIORITY_VEHICLE_SPEED)
            vehicle_states[priority_vehicle]['is_yielding'] = False
    
    # Control yielding vehicle - reduce speed or stop
    if yielding_vehicle and traci.vehicle.getIDCount() > 0:
        if yielding_vehicle in traci.vehicle.getIDList():
            distance = calculate_distance_to_intersection(yielding_vehicle)
            
            # If very close to intersection, make it stop
            if distance < 5.0:
                set_vehicle_speed(yielding_vehicle, STOP_SPEED)
            else:
                set_vehicle_speed(yielding_vehicle, YIELDING_VEHICLE_SPEED)
            
            vehicle_states[yielding_vehicle]['is_yielding'] = True


def print_simulation_status():
    """
    Print current simulation status and vehicle information.
    """
    current_time = traci.simulation.getTime()
    
    print(f"\n=== Simulation Time: {current_time:.1f}s ===")
    
    # Print information about all vehicles
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            speed = get_vehicle_speed(vehicle_id)
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Get vehicle state information
            state = vehicle_states.get(vehicle_id, {})
            has_priority = state.get('has_priority', False)
            is_yielding = state.get('is_yielding', False)
            
            # Print vehicle status
            status = ""
            if has_priority:
                status = " [PRIORITY]"
            elif is_yielding:
                status = " [YIELDING]"
            
            print(f"  {vehicle_id}: speed={speed:.1f}m/s, distance={distance:.1f}m{status}")
        
        # Print priority assignment
        if priority_vehicle:
            print(f"  Priority: {priority_vehicle}")
        if yielding_vehicle:
            print(f"  Yielding: {yielding_vehicle}")
            
    except traci.TraCIException:
        print("  No vehicles in simulation")


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
            return True
        
        # End simulation after reasonable time (60 seconds)
        if traci.simulation.getTime() > 60.0:
            print("\n=== Simulation Timeout ===")
            print("Simulation ended after 60 seconds.")
            return True
            
    except traci.TraCIException:
        return True
    
    return False


def run_simulation():
    """
    Main simulation loop with FCFS control logic.
    """
    global simulation_start_time
    
    print("=== Starting FCFS Baseline Simulation ===")
    print("Intersection: Unsignalized four-way intersection")
    print("Control Logic: First-Come-First-Serve (FCFS)")
    print(f"Control Zone Radius: {CONTROL_ZONE_RADIUS}m")
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
            traci.simulation.getCurrentTime()
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
