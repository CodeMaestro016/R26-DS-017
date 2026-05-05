#!/usr/bin/env python3
"""
SUMO TraCI Control Script: Dynamic Priority Intent-Based Right-of-Way Negotiation
This script implements a dynamic priority intent algorithm for autonomous vehicles
at unsignalized intersections using real-time calculations of vehicle intentions.

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
APPROACH_ZONE_RADIUS = 50.0  # Distance from center to detect approaching vehicles (increased for better detection)
CLEAR_DISTANCE = 25.0  # Distance beyond which vehicle is considered clear
SPEED_LIMIT = 13.9  # Speed limit for vehicles (m/s)
PRIORITY_SPEED = 13.9  # Speed for priority vehicle (m/s)
YIELDING_SPEED = 2.0  # Reduced speed for yielding vehicle (m/s)
MAX_ACCELERATION = 2.0  # Maximum acceleration for scoring (m/s²)
MAX_WAITING_TIME = 5.0  # Maximum waiting time for scoring (seconds)
STEP_LENGTH = 0.1  # Simulation step length (seconds)
MAX_INITIAL_WAIT_TIME = 2.0  # Maximum time to wait for fair comparison at start (seconds)

# Priority intent calculation weights
URGENCY_WEIGHT = 0.35  # Weight for urgency score (distance-based)
SPEED_WEIGHT = 0.25  # Weight for speed score
ACCELERATION_WEIGHT = 0.20  # Weight for acceleration score
WAITING_WEIGHT = 0.20  # Weight for waiting time score

# Vehicle tracking variables
vehicle_states = {}  # Dictionary to store state information for each vehicle
current_priority_vehicle = None  # ID of vehicle that currently has priority
current_yielding_vehicle = None  # ID of vehicle that is currently yielding
vehicles_cleared_intersection = set()  # Set of vehicles that have cleared the intersection
simulation_start_time = None  # Track when simulation started
first_decision_time = None  # Track when first priority decision was made

# Statistics tracking
priority_intent_history = {}  # Track priority intent values over time
waiting_time_history = {}  # Track waiting times for each vehicle
first_priority_vehicle = None  # Track which vehicle got priority first
first_yielding_vehicle = None  # Track which vehicle yielded first


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


def get_vehicle_acceleration(vehicle_id):
    """
    Get the current acceleration of a vehicle.
    
    Args:
        vehicle_id (str): ID of the vehicle
        
    Returns:
        float: Current acceleration in m/s²
    """
    try:
        # Get vehicle acceleration from TraCI
        return traci.vehicle.getAcceleration(vehicle_id)
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


def calculate_urgency_score(distance):
    """
    Calculate urgency score based on distance to intersection.
    Higher urgency when closer to intersection.
    
    Args:
        distance (float): Distance to intersection center in meters
        
    Returns:
        float: Urgency score between 0 and 1
    """
    # Urgency = 1 - (distance / control_zone_radius), capped at [0, 1]
    urgency = 1 - min(distance / CONTROL_ZONE_RADIUS, 1.0)
    return max(0.0, urgency)


def calculate_speed_score(speed):
    """
    Calculate speed score based on current vehicle speed.
    Higher score when vehicle is moving faster.
    
    Args:
        speed (float): Current speed in m/s
        
    Returns:
        float: Speed score between 0 and 1
    """
    # Speed score = current_speed / speed_limit, capped at [0, 1]
    return min(speed / SPEED_LIMIT, 1.0)


def calculate_acceleration_score(acceleration):
    """
    Calculate acceleration score based on current vehicle acceleration.
    Higher score when vehicle is accelerating more.
    
    Args:
        acceleration (float): Current acceleration in m/s²
        
    Returns:
        float: Acceleration score between 0 and 1
    """
    if acceleration > 0:
        # Positive acceleration: score = acceleration / max_acceleration, capped at [0, 1]
        return min(acceleration / MAX_ACCELERATION, 1.0)
    else:
        # No positive acceleration: score = 0
        return 0.0


def calculate_waiting_score(waiting_time):
    """
    Calculate waiting score based on how long vehicle has been waiting.
    Higher score when vehicle has been waiting longer.
    
    Args:
        waiting_time (float): Waiting time in seconds
        
    Returns:
        float: Waiting score between 0 and 1
    """
    # Waiting score = waiting_time / max_waiting_time, capped at [0, 1]
    return min(waiting_time / MAX_WAITING_TIME, 1.0)


def calculate_priority_intent(vehicle_id):
    """
    Calculate dynamic priority intent for a vehicle.
    This is the core function that determines how strongly a vehicle wants to go first.
    
    Args:
        vehicle_id (str): ID of the vehicle
        
    Returns:
        float: Priority intent value between 0 and 1 (higher = stronger intent)
    """
    # Get current vehicle state
    distance = calculate_distance_to_intersection(vehicle_id)
    speed = get_vehicle_speed(vehicle_id)
    acceleration = get_vehicle_acceleration(vehicle_id)
    
    # Get waiting time from vehicle state
    waiting_time = 0.0
    if vehicle_id in vehicle_states:
        waiting_time = vehicle_states[vehicle_id].get('waiting_time', 0.0)
    
    # Calculate individual component scores
    urgency_score = calculate_urgency_score(distance)
    speed_score = calculate_speed_score(speed)
    acceleration_score = calculate_acceleration_score(acceleration)
    waiting_score = calculate_waiting_score(waiting_time)
    
    # Calculate weighted priority intent
    priority_intent = (
        URGENCY_WEIGHT * urgency_score +
        SPEED_WEIGHT * speed_score +
        ACCELERATION_WEIGHT * acceleration_score +
        WAITING_WEIGHT * waiting_score
    )
    
    # Ensure priority intent is within [0, 1] range
    priority_intent = max(0.0, min(1.0, priority_intent))
    
    # Update vehicle state with current priority intent
    if vehicle_id in vehicle_states:
        vehicle_states[vehicle_id]['priority_intent'] = priority_intent
    
    return priority_intent


def initialize_vehicle_state(vehicle_id):
    """
    Initialize state tracking for a new vehicle.
    
    Args:
        vehicle_id (str): ID of the vehicle to initialize
    """
    if vehicle_id not in vehicle_states:
        vehicle_states[vehicle_id] = {
            'entry_time': traci.simulation.getTime(),
            'initial_speed': get_vehicle_speed(vehicle_id),
            'distance_at_entry': calculate_distance_to_intersection(vehicle_id),
            'has_priority': False,
            'is_yielding': False,
            'waiting_time': 0.0,  # Track how long vehicle has been waiting
            'last_speed': get_vehicle_speed(vehicle_id),  # For detecting waiting
            'priority_intent': 0.0,  # Track current priority intent
            'is_normal': True  # Normal state when not in control zone
        }
        
        # Initialize statistics tracking
        priority_intent_history[vehicle_id] = []
        waiting_time_history[vehicle_id] = []


def update_vehicle_waiting_time(vehicle_id):
    """
    Update waiting time for a vehicle based on speed changes.
    Vehicle is considered "waiting" when speed is very low (< 1 m/s).
    
    Args:
        vehicle_id (str): ID of the vehicle
    """
    if vehicle_id not in vehicle_states:
        return
    
    current_speed = get_vehicle_speed(vehicle_id)
    last_speed = vehicle_states[vehicle_id]['last_speed']
    
    # Check if vehicle is waiting (speed < 1 m/s)
    if current_speed < 1.0:
        # Increment waiting time
        vehicle_states[vehicle_id]['waiting_time'] += STEP_LENGTH
    else:
        # Reset waiting time when vehicle moves normally
        vehicle_states[vehicle_id]['waiting_time'] = 0.0
    
    # Update last speed for next iteration
    vehicle_states[vehicle_id]['last_speed'] = current_speed


def check_vehicles_in_approach_zone():
    """
    Check which vehicles are within the approach zone (near intersection).
    This is used to detect when vehicles are approaching for negotiation.
    
    Returns:
        list: Vehicle IDs that are within the approach zone and haven't cleared yet
    """
    vehicles_in_approach = []
    
    # Get all vehicles currently in simulation
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Check if vehicle is within approach zone AND hasn't cleared intersection yet
            if distance <= APPROACH_ZONE_RADIUS and vehicle_id not in vehicles_cleared_intersection:
                vehicles_in_approach.append(vehicle_id)
                
                # Initialize vehicle state if not already tracked
                initialize_vehicle_state(vehicle_id)
                    
    except traci.TraCIException:
        pass
    
    return vehicles_in_approach


def apply_priority_intent_logic(vehicles_in_approach):
    """
    Apply priority intent-based logic to determine right-of-way.
    IMPORTANT: Priority is assigned based on dynamic priority intent values, NOT arrival order.
    Vehicles with higher priority intent get priority over those with lower intent.
    Arrival order is only used as a tie-breaker when priority intents are very similar.
    
    Args:
        vehicles_in_approach (list): Vehicle IDs in the approach zone
    """
    global current_priority_vehicle, current_yielding_vehicle
    global first_priority_vehicle, first_yielding_vehicle, first_decision_time
    
    # If no vehicles in approach zone, don't change assignments
    if len(vehicles_in_approach) == 0:
        return
    
    # If we already have a priority vehicle that's still active, don't change it
    if current_priority_vehicle and current_priority_vehicle in traci.vehicle.getIDList():
        # Check if priority vehicle has cleared the intersection
        priority_distance = calculate_distance_to_intersection(current_priority_vehicle)
        if priority_distance > CLEAR_DISTANCE:
            # Priority vehicle has cleared - add to cleared set and remove priority
            vehicles_cleared_intersection.add(current_priority_vehicle)
            print(f"  [DECISION] {current_priority_vehicle} has cleared intersection at {traci.simulation.getTime():.1f}s")
            
            # IMPORTANT: Release the yielding vehicle immediately after priority clears
            if current_yielding_vehicle and current_yielding_vehicle in traci.vehicle.getIDList():
                if current_yielding_vehicle not in vehicles_cleared_intersection:
                    # The yielding vehicle hasn't cleared yet, release it to continue
                    print(f"  [RELEASE] {current_yielding_vehicle} is released and can continue at {traci.simulation.getTime():.1f}s")
                    
                    # Set the yielding vehicle to normal state (no longer yielding)
                    vehicle_states[current_yielding_vehicle]['has_priority'] = False
                    vehicle_states[current_yielding_vehicle]['is_yielding'] = False
                    vehicle_states[current_yielding_vehicle]['is_normal'] = True
                    
                    # Give priority to the released vehicle so it can continue
                    current_priority_vehicle = current_yielding_vehicle
                    vehicle_states[current_yielding_vehicle]['has_priority'] = True
                    vehicle_states[current_yielding_vehicle]['is_normal'] = False
                    current_yielding_vehicle = None
                    
                    print(f"  [DECISION] {current_priority_vehicle} gets priority (released after other vehicle cleared) at {traci.simulation.getTime():.1f}s")
                else:
                    # The yielding vehicle has also cleared, no priority needed
                    current_priority_vehicle = None
                    current_yielding_vehicle = None
            else:
                # No yielding vehicle to release
                current_priority_vehicle = None
                current_yielding_vehicle = None
        else:
            # Priority vehicle is still in the intersection area, keep priority
            return
    
    # If no current priority vehicle, assign one based on priority intent
    if current_priority_vehicle is None:
        # Filter out any vehicles that might have already cleared (double-check)
        available_vehicles = [v for v in vehicles_in_approach if v not in vehicles_cleared_intersection]
        
        if len(available_vehicles) == 0:
            # No available vehicles for priority assignment
            current_yielding_vehicle = None  # Clear yielding vehicle when no priority
            return
        
        # Get current simulation time
        current_time = traci.simulation.getTime()
        
        # IMPORTANT: During initial waiting period, only assign priority when both vehicles are present
        if first_decision_time is None and current_time < MAX_INITIAL_WAIT_TIME:
            if len(available_vehicles) == 1:
                # Only one vehicle detected during initial waiting period - wait for fair comparison
                vehicle_id = available_vehicles[0]
                print(f"  [WAITING] {vehicle_id} waiting for fair comparison with other vehicles at {current_time:.1f}s")
                
                # Don't assign priority yet, let vehicle continue at normal speed
                vehicle_states[vehicle_id]['has_priority'] = False
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['is_normal'] = True
                return
        
        # After initial waiting period OR if both vehicles are detected, proceed with priority assignment
        if len(available_vehicles) >= 2:
            # Multiple vehicles available - compare priority intent values
            print(f"  [DETECTED] Both vehicles detected near intersection at {current_time:.1f}s")
            
            # Mark first decision time
            if first_decision_time is None:
                first_decision_time = current_time
            
            # Calculate priority intent for each vehicle
            priority_intents = {}
            entry_times = {}
            for vehicle_id in available_vehicles:
                intent = calculate_priority_intent(vehicle_id)
                priority_intents[vehicle_id] = intent
                vehicle_states[vehicle_id]['priority_intent'] = intent
                
                # Get entry time for tie-breaker
                if vehicle_id in vehicle_states:
                    entry_times[vehicle_id] = vehicle_states[vehicle_id]['entry_time']
                
                # Print priority intent for each vehicle
                print(f"    {vehicle_id} priority_intent: {intent:.3f}")
            
            # Find vehicle with highest priority intent
            highest_intent_vehicle = max(priority_intents, key=priority_intents.get)
            highest_intent = priority_intents[highest_intent_vehicle]
            
            # Check for tie (similar priority intents within 0.05)
            tie_threshold = 0.05
            tied_vehicles = []
            for vehicle_id, intent in priority_intents.items():
                if abs(intent - highest_intent) <= tie_threshold:
                    tied_vehicles.append(vehicle_id)
            
            # Determine priority vehicle
            if len(tied_vehicles) == 1:
                # Clear winner based on priority intent
                selected_priority = highest_intent_vehicle
                decision_reason = f"higher dynamic priority_intent ({highest_intent:.3f})"
            else:
                # Tie detected - use arrival order as tie-breaker
                selected_priority = min(tied_vehicles, key=lambda v: entry_times[v])
                earliest_time = entry_times[selected_priority]
                decision_reason = f"tie in priority_intent ({highest_intent:.3f}), arrival order tie-breaker (entered at {earliest_time:.1f}s)"
            
            # Assign priority to selected vehicle
            current_priority_vehicle = selected_priority
            vehicle_states[selected_priority]['has_priority'] = True
            vehicle_states[selected_priority]['is_yielding'] = False
            vehicle_states[selected_priority]['is_normal'] = False
            
            # Track first assignments
            if first_priority_vehicle is None:
                first_priority_vehicle = selected_priority
            
            # Mark other vehicles as yielding and find the yielding vehicle
            current_yielding_vehicle = None
            for vehicle_id in available_vehicles:
                if vehicle_id != selected_priority:
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['is_normal'] = False
                    current_yielding_vehicle = vehicle_id  # Set yielding vehicle
                    
                    # Track first yielding assignment
                    if first_yielding_vehicle is None:
                        first_yielding_vehicle = vehicle_id
            
            # Print detailed decision information
            print(f"  [DECISION] {selected_priority} gets priority ({decision_reason}) at {current_time:.1f}s")
            print(f"  [DECISION] {current_yielding_vehicle} yields to {selected_priority}")
            
            # Print all priority intents for comparison
            print(f"  [COMPARISON] Priority intents: {', '.join([f'{v}: {priority_intents[v]:.3f}' for v in available_vehicles])}")
        
        elif len(available_vehicles) == 1:
            # Only one vehicle available
            # Only use "last remaining vehicle" logic after one vehicle has already cleared
            if len(vehicles_cleared_intersection) > 0:
                # One vehicle has already cleared, allow the remaining one to continue
                vehicle_id = available_vehicles[0]
                print(f"  [CONTINUE] Only one uncleared vehicle remains after other cleared, {vehicle_id} can continue at {current_time:.1f}s")
                
                # Assign priority to the last remaining vehicle so it can continue
                current_priority_vehicle = vehicle_id
                vehicle_states[vehicle_id]['has_priority'] = True
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['is_normal'] = False
                
                print(f"  [DECISION] {vehicle_id} gets priority (last remaining vehicle) at {current_time:.1f}s")
            else:
                # No vehicles have cleared yet, but only one detected - continue waiting
                vehicle_id = available_vehicles[0]
                if current_time < MAX_INITIAL_WAIT_TIME:
                    print(f"  [WAITING] {vehicle_id} still waiting for fair comparison at {current_time:.1f}s")
                    
                    # Don't assign priority yet, let vehicle continue at normal speed
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['is_normal'] = True
                else:
                    # Wait time exceeded, allow single vehicle to proceed
                    print(f"  [TIMEOUT] Initial wait time exceeded, {vehicle_id} can proceed at {current_time:.1f}s")
                    
                    # Assign priority to proceed
                    current_priority_vehicle = vehicle_id
                    vehicle_states[vehicle_id]['has_priority'] = True
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['is_normal'] = False
                    
                    print(f"  [DECISION] {vehicle_id} gets priority (wait time exceeded) at {current_time:.1f}s")


def control_vehicle_speeds():
    """
    Control vehicle speeds based on priority intent-based assignments.
    IMPORTANT: Cleared vehicles cannot be marked as yielding.
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Skip vehicles that have already cleared the intersection
            if vehicle_id in vehicles_cleared_intersection:
                # Cleared vehicles get normal speed and are not yielding
                set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = False
                vehicle_states[vehicle_id]['is_normal'] = True
                continue
            
            # Check if this is the priority vehicle
            if vehicle_id == current_priority_vehicle:
                # Priority vehicle gets normal speed
                set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['is_normal'] = False
                
            else:
                # This is not the priority vehicle and hasn't cleared yet
                if distance <= CONTROL_ZONE_RADIUS:
                    # Vehicle is in control zone but not priority - make it yield
                    set_vehicle_speed(vehicle_id, YIELDING_SPEED)
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = False
                    
                else:
                    # Vehicle is outside control zone, allow normal speed
                    set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = True
                    
    except traci.TraCIException:
        pass


def update_statistics():
    """
    Update statistics tracking for priority intent values and waiting times.
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            # Update priority intent history
            if vehicle_id in vehicle_states:
                intent = vehicle_states[vehicle_id]['priority_intent']
                priority_intent_history[vehicle_id].append(intent)
                
                # Update waiting time history
                waiting_time = vehicle_states[vehicle_id]['waiting_time']
                waiting_time_history[vehicle_id].append(waiting_time)
                    
    except traci.TraCIException:
        pass


def print_simulation_status():
    """
    Print comprehensive current simulation status with priority intent values.
    Shows detailed information about each vehicle's state and calculated priority intent.
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
            acceleration = get_vehicle_acceleration(vehicle_id)
            distance = calculate_distance_to_intersection(vehicle_id)
            
            # Get vehicle state information
            if vehicle_id in vehicle_states:
                state = vehicle_states[vehicle_id]
                waiting_time = state.get('waiting_time', 0.0)
                priority_intent = state.get('priority_intent', 0.0)
                has_priority = state.get('has_priority', False)
                is_yielding = state.get('is_yielding', False)
                is_normal = state.get('is_normal', True)
                
                # Print vehicle status - check if cleared first
                status = ""
                if vehicle_id in vehicles_cleared_intersection:
                    status = " [CLEARED]"
                elif has_priority:
                    status = " [PRIORITY]"
                elif is_yielding:
                    status = " [YIELDING]"
                elif is_normal:
                    status = " [NORMAL]"
                
                print(f"  {vehicle_id}:")
                print(f"    Speed: {speed:.1f} m/s")
                print(f"    Acceleration: {acceleration:.2f} m/s²")
                print(f"    Distance: {distance:.1f} m")
                print(f"    Waiting time: {waiting_time:.1f} s")
                print(f"    Priority intent: {priority_intent:.3f}")
                print(f"    Status: {status}")
            
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
    Print a comprehensive final summary with priority intent statistics.
    """
    current_time = traci.simulation.getTime()
    
    print("\n" + "="*60)
    print("DYNAMIC PRIORITY INTENT SIMULATION SUMMARY")
    print("="*60)
    
    # Check completion status for each expected vehicle
    expected_vehicles = ['vehicle_A', 'vehicle_B']
    
    for vehicle_id in expected_vehicles:
        if vehicle_id in vehicles_cleared_intersection:
            print(f"  {vehicle_id} completed: True")
        else:
            print(f"  {vehicle_id} completed: False")
    
    print(f"  Total simulation time: {current_time:.1f}s")
    
    # Print first assignment information
    if first_priority_vehicle:
        print(f"  First priority vehicle: {first_priority_vehicle}")
    else:
        print(f"  First priority vehicle: None")
        
    if first_yielding_vehicle:
        print(f"  First yielding vehicle: {first_yielding_vehicle}")
    else:
        print(f"  First yielding vehicle: None")
    
    # Determine success
    if len(vehicles_cleared_intersection) == len(expected_vehicles):
        print(f"  Final result: success (no collision)")
    else:
        print(f"  Final result: incomplete (some vehicles didn't complete)")
    
    # Calculate and print priority intent statistics
    print("\n  Priority Intent Statistics:")
    for vehicle_id in expected_vehicles:
        if vehicle_id in priority_intent_history and priority_intent_history[vehicle_id]:
            avg_intent = sum(priority_intent_history[vehicle_id]) / len(priority_intent_history[vehicle_id])
            max_intent = max(priority_intent_history[vehicle_id])
            min_intent = min(priority_intent_history[vehicle_id])
            print(f"    {vehicle_id}:")
            print(f"      Average priority intent: {avg_intent:.3f}")
            print(f"      Max priority intent: {max_intent:.3f}")
            print(f"      Min priority intent: {min_intent:.3f}")
        else:
            print(f"    {vehicle_id}: No priority intent data")
    
    # Calculate and print waiting time statistics
    print("\n  Waiting Time Statistics:")
    for vehicle_id in expected_vehicles:
        if vehicle_id in waiting_time_history and waiting_time_history[vehicle_id]:
            total_waiting = sum(waiting_time_history[vehicle_id])
            max_waiting = max(waiting_time_history[vehicle_id])
            print(f"    {vehicle_id}:")
            print(f"      Total waiting time: {total_waiting:.1f}s")
            print(f"      Max waiting time: {max_waiting:.1f}s")
        else:
            print(f"    {vehicle_id}: No waiting time data")
    
    print("="*60)


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
    Main simulation loop with dynamic priority intent-based control logic.
    """
    global simulation_start_time
    
    print("=== Starting Dynamic Priority Intent Simulation ===")
    print("Intersection: Unsignalized four-way intersection")
    print("Control Logic: Dynamic Priority Intent-Based Right-of-Way")
    print(f"Control Zone Radius: {CONTROL_ZONE_RADIUS}m")
    print(f"Approach Zone Radius: {APPROACH_ZONE_RADIUS}m")
    print(f"Clear Distance: {CLEAR_DISTANCE}m")
    print(f"Priority Vehicle Speed: {PRIORITY_SPEED}m/s")
    print(f"Yielding Vehicle Speed: {YIELDING_SPEED}m/s")
    print(f"Priority Intent Weights: Urgency={URGENCY_WEIGHT}, Speed={SPEED_WEIGHT}, "
          f"Acceleration={ACCELERATION_WEIGHT}, Waiting={WAITING_WEIGHT}")
    
    # Start SUMO with TraCI
    try:
        # Command to start SUMO with TraCI - use more robust parameters
        sumo_cmd = [
            SUMO_BINARY, 
            "-c", SUMO_CONFIG, 
            "--quit-on-end",  # Automatically close when simulation ends
            "--start",        # Start simulation immediately
            "--collision.check-junctions", "true",  # Enable collision checking
            "--step-length", str(STEP_LENGTH)  # Fixed step length
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
            
            # Update waiting times for all vehicles
            for vehicle_id in traci.vehicle.getIDList():
                update_vehicle_waiting_time(vehicle_id)
            
            # Check which vehicles are in the approach zone
            vehicles_in_approach = check_vehicles_in_approach_zone()
            
            # Continuously calculate priority intent for all vehicles in approach zone
            for vehicle_id in vehicles_in_approach:
                calculate_priority_intent(vehicle_id)
            
            # Apply priority intent logic to determine right-of-way
            apply_priority_intent_logic(vehicles_in_approach)
            
            # Control vehicle speeds based on priority assignments
            control_vehicle_speeds()
            
            # Update statistics tracking
            update_statistics()
            
            # Print status every 10 steps (every 1 second)
            if step % 10 == 0:
                print_simulation_status()
            
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
    Main function to run the dynamic priority intent simulation.
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
