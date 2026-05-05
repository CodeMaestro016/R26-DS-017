#!/usr/bin/env python3
"""
Simple test script for multi-vehicle simulation
"""

import os
import sys
import time
import traci

# Configuration constants
SUMO_BINARY = "sumo-gui"
SUMO_CONFIG = "unsignalized_intersection.sumocfg"
FOUR_VEHICLE_CONFIG = "four_vehicle_config.sumocfg"

def main():
    """Main function to test multi-vehicle simulation."""
    try:
        import traci
    except ImportError:
        print("Error: traci module not found!")
        sys.exit(1)
    
    # Check if configuration file exists
    if not os.path.exists(SUMO_CONFIG):
        print(f"Error: Configuration file '{SUMO_CONFIG}' not found!")
        sys.exit(1)
    
    # Check if four-vehicle config exists
    if not os.path.exists(FOUR_VEHICLE_CONFIG):
        print(f"Error: Four-vehicle configuration file '{FOUR_VEHICLE_CONFIG}' not found!")
        print("Using default configuration instead.")
        FOUR_VEHICLE_CONFIG = SUMO_CONFIG
    else:
        print(f"Using four-vehicle configuration: {FOUR_VEHICLE_CONFIG}")
    
    print("Starting SUMO with four-vehicle configuration...")
    
    try:
        sumo_cmd = [
            SUMO_BINARY, 
            "-c", FOUR_VEHICLE_CONFIG, 
            "--quit-on-end",
            "--start",
            "--collision.check-junctions", "true",
            "--step-length", "0.1"
        ]
        
        print(f"Starting SUMO: {' '.join(sumo_cmd)}")
        
        traci.start(sumo_cmd)
        time.sleep(0.5)
        
        try:
            traci.simulation.getTime()
            print("TraCI connection established successfully!")
            
            # DEBUG: Print all loaded vehicles at the beginning
            all_loaded_vehicles = traci.vehicle.getIDList()
            expected_vehicles = ['vehicle_A', 'vehicle_B', 'vehicle_C', 'vehicle_D']
            print(f"  [DEBUG] Loaded vehicles: {all_loaded_vehicles}")
            print(f"  [DEBUG] Expected vehicles: {expected_vehicles}")
            
            # Check for missing vehicles
            missing_vehicles = [v for v in expected_vehicles if v not in all_loaded_vehicles]
            if missing_vehicles:
                for vehicle_id in missing_vehicles:
                    print(f"  [WARNING] {vehicle_id} not loaded - may have invalid route or network connection")
            
        except traci.TraCIException as e:
            print(f"Error testing TraCI connection: {e}")
            raise
        
        # Run for a few steps to test
        for step in range(50):
            traci.simulationStep()
            current_time = traci.simulation.getTime()
            all_vehicles = traci.vehicle.getIDList()
            print(f"Step {step+1} at {current_time:.1f}s - Vehicles: {all_vehicles}")
            
            # Check if simulation should end
            if len(all_vehicles) == 0:
                print("All vehicles completed!")
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

if __name__ == "__main__":
    main()
