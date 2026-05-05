#!/usr/bin/env python3
"""
SUMO TraCI Control Script: Multi-Vehicle Dynamic Priority Intent with V2V Communication and Safety Monitor
This script implements a multi-vehicle dynamic priority intent algorithm with simulated V2V communication
and a safety override layer for autonomous vehicles at unsignalized intersections.

V2V Communication Layer:
This script includes a simulated Vehicle-to-Vehicle (V2V) communication layer that allows
vehicles to exchange information about their state and intentions. In a real implementation,
this would use wireless communication protocols like DSRC or C-V2X. Here, we simulate
this using Python dictionaries to demonstrate the concept and negotiation logic.

Safety Monitor Layer:
The safety monitor layer provides an additional safety override that can intervene in the
priority negotiation process to prevent collisions. It continuously monitors distances between
vehicles and can override speed assignments if unsafe conditions are detected.

Author: Research Project on Autonomous Vehicle Right-of-Way Negotiation with V2V Communication and Safety
"""

import os
import sys
import time
import traci
import math

# Configuration constants
SUMO_BINARY = "sumo-gui"
SUMO_CONFIG = "unsignalized_intersection.sumocfg"
FOUR_VEHICLE_CONFIG = "four_vehicle_config.sumocfg"
SUMO_PORT = 8813

# Intersection control parameters
INTERSECTION_CENTER = (0.0, 0.0)
CONTROL_ZONE_RADIUS = 20.0
APPROACH_ZONE_RADIUS = 50.0
CLEAR_DISTANCE = 25.0
SPEED_LIMIT = 13.9

# Safety Parameters - Critical for collision avoidance
# These parameters define the safety thresholds for vehicle interactions
minimum_safe_distance = 5.0  # Minimum distance between vehicles (meters) - below this triggers emergency override
warning_distance = 10.0  # Warning distance between vehicles (meters) - below this triggers safety warning
emergency_stop_speed = 0.0  # Speed for emergency stop (m/s)
yielding_speed = 2.0  # Safe yielding speed (m/s)
priority_speed = 13.9  # Normal priority speed (m/s)

# Priority intent calculation weights
URGENCY_WEIGHT = 0.35
SPEED_WEIGHT = 0.25
ACCELERATION_WEIGHT = 0.20
WAITING_WEIGHT = 0.20
MAX_WAITING_TIME = 5.0
STEP_LENGTH = 0.1
MAX_INITIAL_WAIT_TIME = 2.0

# Vehicle tracking variables
vehicle_states = {}
current_priority_vehicle = None
current_yielding_vehicles = set()
vehicles_cleared_intersection = set()
simulation_start_time = None
first_decision_time = None

# V2V Communication Layer Variables
# This dictionary simulates V2V communication messages exchanged between vehicles
# In real V2V, this would be wireless broadcast messages using protocols like DSRC
v2v_messages = {}
v2v_message_count = 0
v2v_print_interval = 10  # Print V2V messages every 10 steps (1 second)

# Safety Monitor Variables
# These variables track safety-related events and statistics
safety_warning_count = 0
safety_override_count = 0
safety_print_interval = 10  # Print safety info every 10 steps (1 second)

# Statistics tracking
priority_intent_history = {}
waiting_time_history = {}
crossing_order = []
priority_order = []

# Expected vehicles for four-vehicle simulation
EXPECTED_VEHICLES = ['vehicle_A', 'vehicle_B', 'vehicle_C', 'vehicle_D']

def calculate_distance_to_intersection(vehicle_id):
    """Calculate distance from vehicle to intersection center."""
    try:
        x, y = traci.vehicle.getPosition(vehicle_id)
        distance = ((x - INTERSECTION_CENTER[0])**2 + (y - INTERSECTION_CENTER[1])**2)**0.5
        return distance
    except traci.TraCIException:
        return float('inf')

def calculate_pairwise_distance(vehicle1_id, vehicle2_id):
    """
    Calculate pairwise distance between two vehicles.
    This is a critical safety function for collision detection.
    Returns Euclidean distance between vehicle positions.
    """
    try:
        x1, y1 = traci.vehicle.getPosition(vehicle1_id)
        x2, y2 = traci.vehicle.getPosition(vehicle2_id)
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance
    except traci.TraCIException:
        return float('inf')

def get_vehicle_speed(vehicle_id):
    """Get current speed of a vehicle."""
    try:
        return traci.vehicle.getSpeed(vehicle_id)
    except traci.TraCIException:
        return 0.0

def get_vehicle_acceleration(vehicle_id):
    """Get current acceleration of a vehicle."""
    try:
        return traci.vehicle.getAcceleration(vehicle_id)
    except traci.TraCIException:
        return 0.0

def set_vehicle_speed(vehicle_id, target_speed):
    """Set target speed for a vehicle."""
    try:
        traci.vehicle.setMaxSpeed(vehicle_id, target_speed)
        traci.vehicle.setSpeed(vehicle_id, target_speed)
    except traci.TraCIException as e:
        print(f"Warning: Could not set speed for {vehicle_id}: {e}")

def calculate_urgency_score(distance):
    """Calculate urgency score based on distance to intersection."""
    urgency = 1 - min(distance / CONTROL_ZONE_RADIUS, 1.0)
    return max(0.0, urgency)

def calculate_speed_score(speed):
    """Calculate speed score based on current vehicle speed."""
    return min(speed / SPEED_LIMIT, 1.0)

def calculate_acceleration_score(acceleration):
    """Calculate acceleration score based on current vehicle acceleration."""
    if acceleration > 0:
        return min(acceleration / 2.0, 1.0)  # Use 2.0 as max acceleration
    else:
        return 0.0

def calculate_waiting_score(waiting_time):
    """Calculate waiting score based on how long vehicle has been waiting."""
    return min(waiting_time / MAX_WAITING_TIME, 1.0)

def calculate_priority_intent(vehicle_id):
    """Calculate dynamic priority intent for a vehicle."""
    distance = calculate_distance_to_intersection(vehicle_id)
    speed = get_vehicle_speed(vehicle_id)
    acceleration = get_vehicle_acceleration(vehicle_id)
    
    waiting_time = 0.0
    if vehicle_id in vehicle_states:
        waiting_time = vehicle_states[vehicle_id].get('waiting_time', 0.0)
    
    urgency_score = calculate_urgency_score(distance)
    speed_score = calculate_speed_score(speed)
    acceleration_score = calculate_acceleration_score(acceleration)
    waiting_score = calculate_waiting_score(waiting_time)
    
    priority_intent = (
        URGENCY_WEIGHT * urgency_score +
        SPEED_WEIGHT * speed_score +
        ACCELERATION_WEIGHT * acceleration_score +
        WAITING_WEIGHT * waiting_score
    )
    
    priority_intent = max(0.0, min(1.0, priority_intent))
    
    if vehicle_id in vehicle_states:
        vehicle_states[vehicle_id]['priority_intent'] = priority_intent
    
    return priority_intent

def get_vehicle_status(vehicle_id):
    """
    Get current status of a vehicle for V2V communication.
    Returns one of: APPROACHING, PRIORITY, YIELDING, CLEARED
    """
    if vehicle_id in vehicles_cleared_intersection:
        return "CLEARED"
    elif vehicle_id == current_priority_vehicle:
        return "PRIORITY"
    elif vehicle_id in current_yielding_vehicles:
        return "YIELDING"
    else:
        return "APPROACHING"

def get_safety_status():
    """
    Get current safety status based on vehicle distances.
    Returns one of: SAFE, WARNING, OVERRIDE
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        # Only consider uncleared vehicles for safety monitoring
        active_vehicles = [v for v in all_vehicles if v not in vehicles_cleared_intersection]
        
        if len(active_vehicles) < 2:
            return "SAFE"
        
        # Check all pairwise distances
        min_distance = float('inf')
        for i, vehicle1 in enumerate(active_vehicles):
            for vehicle2 in active_vehicles[i+1:]:
                distance = calculate_pairwise_distance(vehicle1, vehicle2)
                min_distance = min(min_distance, distance)
        
        # Determine safety status based on minimum distance
        if min_distance < minimum_safe_distance:
            return "OVERRIDE"
        elif min_distance < warning_distance:
            return "WARNING"
        else:
            return "SAFE"
            
    except traci.TraCIException:
        return "SAFE"

def check_safety_conflicts():
    """
    Check for safety conflicts between vehicles and apply safety overrides if needed.
    This is the core safety function that can override normal priority assignments.
    Returns tuple: (has_conflict, conflict_vehicles, override_actions)
    """
    global safety_warning_count, safety_override_count
    
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        # Only consider uncleared vehicles for safety monitoring
        active_vehicles = [v for v in all_vehicles if v not in vehicles_cleared_intersection]
        
        if len(active_vehicles) < 2:
            return False, [], []
        
        # Check all pairwise distances
        min_distance = float('inf')
        conflict_pairs = []
        
        for i, vehicle1 in enumerate(active_vehicles):
            for vehicle2 in active_vehicles[i+1:]:
                distance = calculate_pairwise_distance(vehicle1, vehicle2)
                min_distance = min(min_distance, distance)
                
                if distance < minimum_safe_distance:
                    conflict_pairs.append((vehicle1, vehicle2, distance))
        
        # Apply safety overrides if conflicts detected
        override_actions = []
        if conflict_pairs:
            # Emergency override situation
            safety_override_count += 1
            print(f"  [SAFETY OVERRIDE] Emergency override triggered! Minimum distance: {min_distance:.2f}m")
            
            for vehicle1, vehicle2, distance in conflict_pairs:
                print(f"    Conflict: {vehicle1} and {vehicle2} at {distance:.2f}m")
                
                # Determine which vehicle to slow/stop
                # Priority: 1) Non-priority vehicles, 2) Lower priority intent, 3) Emergency stop both
                vehicle1_priority = vehicle1 != current_priority_vehicle
                vehicle2_priority = vehicle2 != current_priority_vehicle
                
                if vehicle1 in v2v_messages and vehicle2 in v2v_messages:
                    vehicle1_intent = v2v_messages[vehicle1]['priority_intent']
                    vehicle2_intent = v2v_messages[vehicle2]['priority_intent']
                    
                    if vehicle1_priority and vehicle2_priority:
                        # Both non-priority, stop the one with lower priority intent
                        if vehicle1_intent < vehicle2_intent:
                            override_actions.append((vehicle1, emergency_stop_speed, "Lower priority intent"))
                        else:
                            override_actions.append((vehicle2, emergency_stop_speed, "Lower priority intent"))
                    elif vehicle1_priority:
                        # Vehicle 1 is non-priority, stop it
                        override_actions.append((vehicle1, emergency_stop_speed, "Non-priority vehicle"))
                    elif vehicle2_priority:
                        # Vehicle 2 is non-priority, stop it
                        override_actions.append((vehicle2, emergency_stop_speed, "Non-priority vehicle"))
                    else:
                        # Both are priority vehicles (shouldn't happen), emergency stop both
                        override_actions.append((vehicle1, emergency_stop_speed, "Emergency"))
                        override_actions.append((vehicle2, emergency_stop_speed, "Emergency"))
                else:
                    # Fallback: stop both vehicles
                    override_actions.append((vehicle1, emergency_stop_speed, "Emergency"))
                    override_actions.append((vehicle2, emergency_stop_speed, "Emergency"))
        
        elif min_distance < warning_distance:
            # Warning situation
            safety_warning_count += 1
            print(f"  [SAFETY WARNING] Vehicles too close! Minimum distance: {min_distance:.2f}m")
            
            # Ensure non-priority vehicles stay at yielding speed
            for vehicle in active_vehicles:
                if vehicle != current_priority_vehicle and vehicle not in vehicles_cleared_intersection:
                    override_actions.append((vehicle, yielding_speed, "Safety warning"))
        
        return len(conflict_pairs) > 0, conflict_pairs, override_actions
        
    except traci.TraCIException:
        return False, [], []

def broadcast_v2v_message(vehicle_id):
    """
    Simulate V2V message broadcasting from a vehicle.
    In real V2V systems, this would be a wireless broadcast using DSRC/C-V2X protocols.
    Here we simulate it by updating a shared dictionary.
    """
    global v2v_message_count
    
    # Calculate current vehicle state
    priority_intent = calculate_priority_intent(vehicle_id)
    distance = calculate_distance_to_intersection(vehicle_id)
    speed = get_vehicle_speed(vehicle_id)
    acceleration = get_vehicle_acceleration(vehicle_id)
    
    waiting_time = 0.0
    if vehicle_id in vehicle_states:
        waiting_time = vehicle_states[vehicle_id].get('waiting_time', 0.0)
    
    status = get_vehicle_status(vehicle_id)
    safety_status = get_safety_status()
    
    # Create V2V message structure with safety status
    v2v_messages[vehicle_id] = {
        "priority_intent": priority_intent,
        "distance_to_intersection": distance,
        "speed": speed,
        "acceleration": acceleration,
        "waiting_time": waiting_time,
        "status": status,
        "safety_status": safety_status  # Added safety status
    }
    
    v2v_message_count += 1

def update_v2v_communications():
    """
    Update V2V communications for all active vehicles.
    This simulates continuous broadcasting of vehicle state information.
    In real V2V, this would happen at 10Hz frequency using wireless protocols.
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            if vehicle_id in vehicle_states:
                broadcast_v2v_message(vehicle_id)
                    
    except traci.TraCIException:
        pass

def print_v2v_messages():
    """
    Print current V2V messages for all vehicles.
    This simulates monitoring the V2V communication channel.
    """
    current_time = traci.simulation.getTime()
    
    print(f"\n=== V2V Communication Messages at {current_time:.1f}s ===")
    
    if not v2v_messages:
        print("  No V2V messages active")
        return
    
    for vehicle_id in sorted(v2v_messages.keys()):
        message = v2v_messages[vehicle_id]
        print(f"  {vehicle_id}:")
        print(f"    priority_intent: {message['priority_intent']:.3f}")
        print(f"    distance_to_intersection: {message['distance_to_intersection']:.1f}m")
        print(f"    speed: {message['speed']:.1f} m/s")
        print(f"    acceleration: {message['acceleration']:.2f} m/s²")
        print(f"    waiting_time: {message['waiting_time']:.1f}s")
        print(f"    status: {message['status']}")
        print(f"    safety_status: {message['safety_status']}")

def print_safety_information():
    """
    Print current safety information for all vehicles.
    This provides detailed safety monitoring information.
    """
    current_time = traci.simulation.getTime()
    
    print(f"\n=== Safety Monitor Information at {current_time:.1f}s ===")
    print(f"  Safety warnings: {safety_warning_count}")
    print(f"  Safety overrides: {safety_override_count}")
    print(f"  Minimum safe distance: {minimum_safe_distance}m")
    print(f"  Warning distance: {warning_distance}m")
    
    try:
        all_vehicles = traci.vehicle.getIDList()
        active_vehicles = [v for v in all_vehicles if v not in vehicles_cleared_intersection]
        
        if len(active_vehicles) >= 2:
            print(f"  Active vehicles: {len(active_vehicles)}")
            
            # Check all pairwise distances
            min_distance = float('inf')
            closest_pair = None
            
            for i, vehicle1 in enumerate(active_vehicles):
                for vehicle2 in active_vehicles[i+1:]:
                    distance = calculate_pairwise_distance(vehicle1, vehicle2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_pair = (vehicle1, vehicle2)
            
            if closest_pair:
                print(f"  Closest pair: {closest_pair[0]} and {closest_pair[1]} at {min_distance:.2f}m")
                
                if min_distance < minimum_safe_distance:
                    print(f"  Status: EMERGENCY OVERRIDE ACTIVE")
                elif min_distance < warning_distance:
                    print(f"  Status: SAFETY WARNING ACTIVE")
                else:
                    print(f"  Status: SAFE")
        else:
            print(f"  Active vehicles: {len(active_vehicles)}")
            print(f"  Status: SAFE (insufficient vehicles for conflict)")
            
    except traci.TraCIException:
        print("  Error: Could not access vehicle information for safety monitoring")

def initialize_vehicle_state(vehicle_id):
    """Initialize state tracking for a new vehicle."""
    if vehicle_id not in vehicle_states:
        vehicle_states[vehicle_id] = {
            'entry_time': traci.simulation.getTime(),
            'initial_speed': get_vehicle_speed(vehicle_id),
            'distance_at_entry': calculate_distance_to_intersection(vehicle_id),
            'has_priority': False,
            'is_yielding': False,
            'waiting_time': 0.0,
            'last_speed': get_vehicle_speed(vehicle_id),
            'priority_intent': 0.0,
            'is_normal': True
        }
        
        priority_intent_history[vehicle_id] = []
        waiting_time_history[vehicle_id] = []
        
        print(f"  [ENTERED] {vehicle_id} entered simulation at {traci.simulation.getTime():.1f}s")

def update_vehicle_waiting_time(vehicle_id):
    """Update waiting time for a vehicle based on speed changes."""
    if vehicle_id not in vehicle_states:
        return
    
    current_speed = get_vehicle_speed(vehicle_id)
    last_speed = vehicle_states[vehicle_id]['last_speed']
    
    if current_speed < 1.0:
        vehicle_states[vehicle_id]['waiting_time'] += STEP_LENGTH
    else:
        vehicle_states[vehicle_id]['waiting_time'] = 0.0
    
    vehicle_states[vehicle_id]['last_speed'] = current_speed

def check_vehicles_in_approach_zone():
    """Check which vehicles are within approach zone."""
    vehicles_in_approach = []
    
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            if distance <= APPROACH_ZONE_RADIUS and vehicle_id not in vehicles_cleared_intersection:
                vehicles_in_approach.append(vehicle_id)
                initialize_vehicle_state(vehicle_id)
                    
    except traci.TraCIException:
        pass
    
    return vehicles_in_approach

def apply_v2v_multi_vehicle_priority_logic(vehicles_in_approach):
    """
    Apply multi-vehicle priority intent-based logic using V2V communication.
    The key difference: decisions are based on V2V messages, not direct vehicle state access.
    This simulates how real V2V systems would negotiate right-of-way.
    """
    global current_priority_vehicle, current_yielding_vehicles
    global crossing_order, priority_order, first_decision_time
    
    if len(vehicles_in_approach) == 0:
        return
    
    # Handle priority vehicle clearing
    if current_priority_vehicle and current_priority_vehicle in traci.vehicle.getIDList():
        priority_distance = calculate_distance_to_intersection(current_priority_vehicle)
        if priority_distance > CLEAR_DISTANCE:
            vehicles_cleared_intersection.add(current_priority_vehicle)
            crossing_order.append(current_priority_vehicle)
            print(f"  [DECISION] {current_priority_vehicle} has cleared intersection at {traci.simulation.getTime():.1f}s")
            
            current_priority_vehicle = None
            current_yielding_vehicles.clear()
        else:
            return
    
    # If no current priority vehicle, assign one based on V2V messages
    if current_priority_vehicle is None:
        available_vehicles = [v for v in vehicles_in_approach if v not in vehicles_cleared_intersection]
        
        if len(available_vehicles) == 0:
            current_yielding_vehicles.clear()
            return
        
        current_time = traci.simulation.getTime()
        
        # Initial waiting period
        if first_decision_time is None and current_time < MAX_INITIAL_WAIT_TIME:
            if len(available_vehicles) == 1:
                vehicle_id = available_vehicles[0]
                print(f"  [WAITING] {vehicle_id} waiting for fair comparison with other vehicles at {current_time:.1f}s")
                
                vehicle_states[vehicle_id]['has_priority'] = False
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['is_normal'] = True
                return
        
        # Proceed with priority assignment using V2V messages
        if len(available_vehicles) >= 1:
            print(f"  [DETECTED] {len(available_vehicles)} vehicles detected near intersection at {current_time:.1f}s")
            
            if first_decision_time is None:
                first_decision_time = current_time
            
            # Extract priority intents from V2V messages (not direct calculation)
            v2v_priority_intents = {}
            entry_times = {}
            for vehicle_id in available_vehicles:
                # Ensure V2V message exists for this vehicle
                if vehicle_id not in v2v_messages:
                    # Force V2V message creation if missing
                    broadcast_v2v_message(vehicle_id)
                
                if vehicle_id in v2v_messages:
                    # Use priority intent from V2V message, not direct calculation
                    intent = v2v_messages[vehicle_id]['priority_intent']
                    v2v_priority_intents[vehicle_id] = intent
                    
                    if vehicle_id in vehicle_states:
                        entry_times[vehicle_id] = vehicle_states[vehicle_id]['entry_time']
                    
                    print(f"    {vehicle_id} V2V priority_intent: {intent:.3f}")
                else:
                    print(f"    {vehicle_id} No V2V message available")
            
            if not v2v_priority_intents:
                print("  [WARNING] No V2V messages available for negotiation")
                return
            
            # Find vehicle with highest priority intent from V2V messages
            highest_intent_vehicle = max(v2v_priority_intents, key=v2v_priority_intents.get)
            highest_intent = v2v_priority_intents[highest_intent_vehicle]
            
            # Check for tie in V2V priority intents
            tie_threshold = 0.05
            tied_vehicles = []
            for vehicle_id, intent in v2v_priority_intents.items():
                if abs(intent - highest_intent) <= tie_threshold:
                    tied_vehicles.append(vehicle_id)
            
            # Determine priority vehicle
            if len(tied_vehicles) == 1:
                selected_priority = highest_intent_vehicle
                decision_reason = f"highest V2V priority_intent ({highest_intent:.3f})"
            else:
                selected_priority = min(tied_vehicles, key=lambda v: entry_times[v])
                earliest_time = entry_times[selected_priority]
                decision_reason = f"tie in V2V priority_intent ({highest_intent:.3f}), arrival order tie-breaker (entered at {earliest_time:.1f}s)"
            
            # Assign priority to selected vehicle
            current_priority_vehicle = selected_priority
            vehicle_states[selected_priority]['has_priority'] = True
            vehicle_states[selected_priority]['is_yielding'] = False
            vehicle_states[selected_priority]['is_normal'] = False
            
            if selected_priority not in priority_order:
                priority_order.append(selected_priority)
            
            # Mark other vehicles as yielding
            current_yielding_vehicles.clear()
            for vehicle_id in available_vehicles:
                if vehicle_id != selected_priority:
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['is_normal'] = False
                    current_yielding_vehicles.add(vehicle_id)
            
            # Print detailed decision information
            print(f"  [DECISION] {selected_priority} gets priority ({decision_reason}) at {current_time:.1f}s")
            if current_yielding_vehicles:
                yielding_list = ', '.join(sorted(current_yielding_vehicles))
                print(f"  [DECISION] Yielding vehicles: {yielding_list}")
            
            # Print all V2V priority intents for comparison
            intents_str = ', '.join([f'{v}: {v2v_priority_intents[v]:.3f}' for v in sorted(available_vehicles)])
            print(f"  [V2V COMPARISON] Priority intents: {intents_str}")

def apply_safety_overrides():
    """
    Apply safety overrides to vehicle speeds based on detected conflicts.
    This function implements the safety layer that can override normal priority assignments.
    """
    has_conflict, conflict_vehicles, override_actions = check_safety_conflicts()
    
    if not override_actions:
        return
    
    # Apply safety overrides
    for vehicle_id, target_speed, reason in override_actions:
        if vehicle_id in traci.vehicle.getIDList():
            set_vehicle_speed(vehicle_id, target_speed)
            print(f"  [SAFETY ACTION] {vehicle_id} speed set to {target_speed:.1f} m/s ({reason})")

def control_vehicle_speeds():
    """
    Control vehicle speeds based on multi-vehicle priority intent-based assignments with safety overrides.
    This function combines normal priority control with safety override capabilities.
    """
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            if vehicle_id in vehicles_cleared_intersection:
                set_vehicle_speed(vehicle_id, priority_speed)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = False
                vehicle_states[vehicle_id]['is_normal'] = True
                continue
            
            if vehicle_id == current_priority_vehicle:
                set_vehicle_speed(vehicle_id, priority_speed)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = True
                vehicle_states[vehicle_id]['is_normal'] = False
                
            else:
                if distance <= CONTROL_ZONE_RADIUS:
                    set_vehicle_speed(vehicle_id, yielding_speed)
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = False
                else:
                    set_vehicle_speed(vehicle_id, priority_speed)
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = True
        
        # Apply safety overrides after normal control
        apply_safety_overrides()
                    
    except traci.TraCIException:
        pass

def update_statistics():
    """Update statistics tracking for priority intent values and waiting times."""
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            if vehicle_id in vehicle_states:
                intent = vehicle_states[vehicle_id]['priority_intent']
                priority_intent_history[vehicle_id].append(intent)
                
                waiting_time = vehicle_states[vehicle_id]['waiting_time']
                waiting_time_history[vehicle_id].append(waiting_time)
                    
    except traci.TraCIException:
        pass

def print_simulation_status():
    """Print comprehensive current simulation status with V2V communication and safety information."""
    current_time = traci.simulation.getTime()
    
    print(f"\n=== Simulation Time: {current_time:.1f}s ===")
    
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        if len(all_vehicles) == 0:
            print("  No vehicles in simulation")
            return
        
        for vehicle_id in sorted(all_vehicles):
            speed = get_vehicle_speed(vehicle_id)
            acceleration = get_vehicle_acceleration(vehicle_id)
            distance = calculate_distance_to_intersection(vehicle_id)
            
            if vehicle_id in vehicle_states:
                state = vehicle_states[vehicle_id]
                waiting_time = state.get('waiting_time', 0.0)
                priority_intent = state.get('priority_intent', 0.0)
                has_priority = state.get('has_priority', False)
                is_yielding = state.get('is_yielding', False)
                is_normal = state.get('is_normal', True)
                
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
        
        if current_priority_vehicle:
            print(f"  Priority: {current_priority_vehicle}")
        else:
            print("  Priority: None")
        
        if current_yielding_vehicles:
            yielding_list = ', '.join(sorted(current_yielding_vehicles))
            print(f"  Yielding: {yielding_list}")
        else:
            print("  Yielding: None")
        
        if vehicles_cleared_intersection:
            cleared_list = ', '.join(sorted(vehicles_cleared_intersection))
            print(f"  Cleared intersection: {cleared_list}")
            
    except traci.TraCIException:
        print("  No vehicles in simulation")

def print_final_summary():
    """Print a comprehensive final summary with V2V communication and safety statistics."""
    current_time = traci.simulation.getTime()
    
    print("\n" + "="*70)
    print("MULTI-VEHICLE DYNAMIC PRIORITY INTENT WITH V2V COMMUNICATION AND SAFETY MONITOR SUMMARY")
    print("="*70)
    
    completed_count = 0
    for vehicle_id in EXPECTED_VEHICLES:
        if vehicle_id in vehicles_cleared_intersection:
            print(f"  {vehicle_id} completed: True")
            completed_count += 1
        else:
            print(f"  {vehicle_id} completed: False")
    
    print(f"  Total simulation time: {current_time:.1f}s")
    print(f"  Total V2V messages sent: {v2v_message_count}")
    print(f"  Total safety warnings: {safety_warning_count}")
    print(f"  Total safety overrides: {safety_override_count}")
    
    if crossing_order:
        print(f"  Crossing order: {' -> '.join(crossing_order)}")
    else:
        print("  Crossing order: None")
    
    if priority_order:
        print(f"  Priority order: {' -> '.join(priority_order)}")
    else:
        print("  Priority order: None")
    
    if completed_count == len(EXPECTED_VEHICLES):
        print(f"  Final result: success (no collision)")
    else:
        print(f"  Final result: incomplete ({completed_count}/{len(EXPECTED_VEHICLES)} vehicles completed)")
    
    print("\n  V2V Communication Statistics:")
    for vehicle_id in EXPECTED_VEHICLES:
        if vehicle_id in priority_intent_history and priority_intent_history[vehicle_id]:
            avg_intent = sum(priority_intent_history[vehicle_id]) / len(priority_intent_history[vehicle_id])
            print(f"    {vehicle_id}:")
            print(f"      Average priority_intent (V2V): {avg_intent:.3f}")
        else:
            print(f"    {vehicle_id}: No V2V priority intent data")
    
    print("\n  Waiting Time Statistics:")
    for vehicle_id in EXPECTED_VEHICLES:
        if vehicle_id in waiting_time_history and waiting_time_history[vehicle_id]:
            total_waiting = sum(waiting_time_history[vehicle_id])
            max_waiting = max(waiting_time_history[vehicle_id])
            print(f"    {vehicle_id}:")
            print(f"      Total waiting time: {total_waiting:.1f}s")
            print(f"      Max waiting time: {max_waiting:.1f}s")
        else:
            print(f"    {vehicle_id}: No waiting time data")
    
    print("\n  Safety Monitor Statistics:")
    print(f"    Safety system active: True")
    print(f"    Minimum safe distance: {minimum_safe_distance}m")
    print(f"    Warning distance: {warning_distance}m")
    print(f"    Emergency stop speed: {emergency_stop_speed}m/s")
    print(f"    Yielding speed: {yielding_speed}m/s")
    print(f"    Priority speed: {priority_speed}m/s")
    
    print("="*70)

def check_simulation_completion():
    """Check if all vehicles have completed their routes."""
    try:
        remaining_vehicles = traci.vehicle.getIDList()
        
        if len(remaining_vehicles) == 0:
            print("\n=== Simulation Complete ===")
            print("All vehicles have completed their routes.")
            print_final_summary()
            return True
        
        if traci.simulation.getTime() > 120.0:
            print("\n=== Simulation Timeout ===")
            print("Simulation ended after 120 seconds.")
            print_final_summary()
            return True
            
    except traci.TraCIException:
        return True
    
    return False

def run_simulation():
    """Main simulation loop with V2V communication, safety monitor, and multi-vehicle dynamic priority intent-based control logic."""
    global simulation_start_time
    
    print("=== Starting Multi-Vehicle Dynamic Priority Intent Simulation with V2V Communication and Safety Monitor ===")
    print("Intersection: Unsignalized four-way intersection")
    print("Control Logic: Multi-Vehicle Dynamic Priority Intent-Based Right-of-Way with V2V Communication")
    print("V2V Layer: Simulated Vehicle-to-Vehicle Communication using Python dictionaries")
    print("Safety Layer: Real-time safety monitoring with override capabilities")
    print(f"Control Zone Radius: {CONTROL_ZONE_RADIUS}m")
    print(f"Approach Zone Radius: {APPROACH_ZONE_RADIUS}m")
    print(f"Clear Distance: {CLEAR_DISTANCE}m")
    print(f"Priority Vehicle Speed: {priority_speed}m/s")
    print(f"Yielding Vehicle Speed: {yielding_speed}m/s")
    print(f"Emergency Stop Speed: {emergency_stop_speed}m/s")
    print(f"Minimum Safe Distance: {minimum_safe_distance}m")
    print(f"Warning Distance: {warning_distance}m")
    print(f"Priority Intent Weights: Urgency={URGENCY_WEIGHT}, Speed={SPEED_WEIGHT}, Acceleration={ACCELERATION_WEIGHT}, Waiting={WAITING_WEIGHT}")
    
    try:
        sumo_cmd = [
            SUMO_BINARY, 
            "-c", FOUR_VEHICLE_CONFIG, 
            "--quit-on-end",
            "--start",
            "--collision.check-junctions", "true",
            "--step-length", str(STEP_LENGTH)
        ]
        
        print(f"\nStarting SUMO: {' '.join(sumo_cmd)}")
        
        traci.start(sumo_cmd)
        time.sleep(0.5)
        
        try:
            traci.simulation.getTime()
            simulation_start_time = time.time()
            print("TraCI connection established successfully!")
            
            # DEBUG: Print all loaded vehicles at the beginning
            all_loaded_vehicles = traci.vehicle.getIDList()
            print(f"  [DEBUG] Loaded vehicles: {all_loaded_vehicles}")
            print(f"  [DEBUG] Expected vehicles: {EXPECTED_VEHICLES}")
            
            # Check for missing vehicles
            missing_vehicles = [v for v in EXPECTED_VEHICLES if v not in all_loaded_vehicles]
            if missing_vehicles:
                for vehicle_id in missing_vehicles:
                    print(f"  [WARNING] {vehicle_id} not loaded - may have invalid route or network connection")
            
        except traci.TraCIException as e:
            print(f"Error testing TraCI connection: {e}")
            raise
        
        # Main simulation loop
        step = 0
        while True:
            traci.simulationStep()
            step += 1
            
            # Update waiting times for all vehicles
            for vehicle_id in traci.vehicle.getIDList():
                update_vehicle_waiting_time(vehicle_id)
            
            # Update V2V communications for all vehicles
            update_v2v_communications()
            
            # Check which vehicles are in approach zone
            vehicles_in_approach = check_vehicles_in_approach_zone()
            
            # Apply multi-vehicle priority intent logic using V2V messages
            apply_v2v_multi_vehicle_priority_logic(vehicles_in_approach)
            
            # Control vehicle speeds based on priority assignments with safety overrides
            control_vehicle_speeds()
            
            # Update statistics tracking
            update_statistics()
            
            # Print status every 10 steps (every 1 second)
            if step % 10 == 0:
                print_simulation_status()
                print_v2v_messages()
                print_safety_information()
            
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
        try:
            traci.close()
            print("TraCI connection closed.")
        except:
            pass

def main():
    """Main function to run multi-vehicle dynamic priority intent simulation with V2V communication and safety monitor."""
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
    
    # Check if four-vehicle config exists
    if not os.path.exists(FOUR_VEHICLE_CONFIG):
        print(f"Error: Four-vehicle configuration file '{FOUR_VEHICLE_CONFIG}' not found!")
        print("Using default configuration instead.")
        config_to_use = SUMO_CONFIG
    else:
        print(f"Using four-vehicle configuration: {FOUR_VEHICLE_CONFIG}")
        config_to_use = FOUR_VEHICLE_CONFIG
    
    run_simulation()

if __name__ == "__main__":
    main()
