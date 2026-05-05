#!/usr/bin/env python3
"""
SUMO TraCI Control Script: Multi-Vehicle Dynamic Priority Intent Negotiation
"""

import os
import sys
import time
import traci

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
PRIORITY_SPEED = 13.9
YIELDING_SPEED = 2.0
MAX_ACCELERATION = 2.0
MAX_WAITING_TIME = 5.0
STEP_LENGTH = 0.1
MAX_INITIAL_WAIT_TIME = 2.0

# Priority intent calculation weights
URGENCY_WEIGHT = 0.35
SPEED_WEIGHT = 0.25
ACCELERATION_WEIGHT = 0.20
WAITING_WEIGHT = 0.20

# Vehicle tracking variables
vehicle_states = {}
current_priority_vehicle = None
current_yielding_vehicles = set()
vehicles_cleared_intersection = set()
simulation_start_time = None
first_decision_time = None

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
        return min(acceleration / MAX_ACCELERATION, 1.0)
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

def apply_multi_vehicle_priority_logic(vehicles_in_approach):
    """Apply multi-vehicle priority intent-based logic to determine right-of-way."""
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
    
    # If no current priority vehicle, assign one based on priority intent
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
        
        # Proceed with priority assignment
        if len(available_vehicles) >= 1:
            print(f"  [DETECTED] {len(available_vehicles)} vehicles detected near intersection at {current_time:.1f}s")
            
            if first_decision_time is None:
                first_decision_time = current_time
            
            # Calculate priority intent for each vehicle
            priority_intents = {}
            entry_times = {}
            for vehicle_id in available_vehicles:
                intent = calculate_priority_intent(vehicle_id)
                priority_intents[vehicle_id] = intent
                vehicle_states[vehicle_id]['priority_intent'] = intent
                
                if vehicle_id in vehicle_states:
                    entry_times[vehicle_id] = vehicle_states[vehicle_id]['entry_time']
                
                print(f"    {vehicle_id} priority_intent: {intent:.3f}")
            
            # Find vehicle with highest priority intent
            highest_intent_vehicle = max(priority_intents, key=priority_intents.get)
            highest_intent = priority_intents[highest_intent_vehicle]
            
            # Check for tie
            tie_threshold = 0.05
            tied_vehicles = []
            for vehicle_id, intent in priority_intents.items():
                if abs(intent - highest_intent) <= tie_threshold:
                    tied_vehicles.append(vehicle_id)
            
            # Determine priority vehicle
            if len(tied_vehicles) == 1:
                selected_priority = highest_intent_vehicle
                decision_reason = f"highest dynamic priority_intent ({highest_intent:.3f})"
            else:
                selected_priority = min(tied_vehicles, key=lambda v: entry_times[v])
                earliest_time = entry_times[selected_priority]
                decision_reason = f"tie in priority_intent ({highest_intent:.3f}), arrival order tie-breaker (entered at {earliest_time:.1f}s)"
            
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
            
            # Print all priority intents for comparison
            intents_str = ', '.join([f'{v}: {priority_intents[v]:.3f}' for v in sorted(available_vehicles)])
            print(f"  [COMPARISON] Priority intents: {intents_str}")

def control_vehicle_speeds():
    """Control vehicle speeds based on multi-vehicle priority intent-based assignments."""
    try:
        all_vehicles = traci.vehicle.getIDList()
        
        for vehicle_id in all_vehicles:
            distance = calculate_distance_to_intersection(vehicle_id)
            
            if vehicle_id in vehicles_cleared_intersection:
                set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = False
                vehicle_states[vehicle_id]['is_normal'] = True
                continue
            
            if vehicle_id == current_priority_vehicle:
                set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                vehicle_states[vehicle_id]['is_yielding'] = False
                vehicle_states[vehicle_id]['has_priority'] = True
                vehicle_states[vehicle_id]['is_normal'] = False
                
            else:
                if distance <= CONTROL_ZONE_RADIUS:
                    set_vehicle_speed(vehicle_id, YIELDING_SPEED)
                    vehicle_states[vehicle_id]['is_yielding'] = True
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = False
                else:
                    set_vehicle_speed(vehicle_id, PRIORITY_SPEED)
                    vehicle_states[vehicle_id]['is_yielding'] = False
                    vehicle_states[vehicle_id]['has_priority'] = False
                    vehicle_states[vehicle_id]['is_normal'] = True
                    
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
    """Print comprehensive current simulation status with priority intent values for four vehicles."""
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
    """Print a comprehensive final summary with crossing order and statistics for four vehicles."""
    current_time = traci.simulation.getTime()
    
    print("\n" + "="*60)
    print("MULTI-VEHICLE DYNAMIC PRIORITY INTENT SIMULATION SUMMARY")
    print("="*60)
    
    completed_count = 0
    for vehicle_id in EXPECTED_VEHICLES:
        if vehicle_id in vehicles_cleared_intersection:
            print(f"  {vehicle_id} completed: True")
            completed_count += 1
        else:
            print(f"  {vehicle_id} completed: False")
    
    print(f"  Total simulation time: {current_time:.1f}s")
    
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
    
    print("\n  Priority Intent Statistics:")
    for vehicle_id in EXPECTED_VEHICLES:
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
    
    print("="*60)

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
    """Main simulation loop with multi-vehicle dynamic priority intent-based control logic."""
    global simulation_start_time
    
    print("=== Starting Multi-Vehicle Dynamic Priority Intent Simulation ===")
    print("Intersection: Unsignalized four-way intersection")
    print("Control Logic: Multi-Vehicle Dynamic Priority Intent-Based Right-of-Way")
    print(f"Control Zone Radius: {CONTROL_ZONE_RADIUS}m")
    print(f"Approach Zone Radius: {APPROACH_ZONE_RADIUS}m")
    print(f"Clear Distance: {CLEAR_DISTANCE}m")
    print(f"Priority Vehicle Speed: {PRIORITY_SPEED}m/s")
    print(f"Yielding Vehicle Speed: {YIELDING_SPEED}m/s")
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
            
            # Check which vehicles are in approach zone
            vehicles_in_approach = check_vehicles_in_approach_zone()
            
            # Apply multi-vehicle priority intent logic to determine right-of-way
            apply_multi_vehicle_priority_logic(vehicles_in_approach)
            
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
        try:
            traci.close()
            print("TraCI connection closed.")
        except:
            pass

def main():
    """Main function to run multi-vehicle dynamic priority intent simulation."""
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
