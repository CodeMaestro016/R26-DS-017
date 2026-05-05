#!/usr/bin/env python3
"""
Simple test script to verify TraCI connection works
"""

import os
import sys
import traci
import time

def test_traci_connection():
    """Test basic TraCI connection with headless SUMO"""
    print("=== Testing TraCI Connection ===")
    
    # Configuration
    SUMO_BINARY = "sumo"  # Use headless version for testing
    SUMO_CONFIG = "unsignalized_intersection.sumocfg"
    SUMO_PORT = 8813
    
    try:
        # Simple SUMO command for testing
        sumo_cmd = [
            SUMO_BINARY,
            "-c", SUMO_CONFIG,
            "--quit-on-end",
            "--start",
            "--step-length", "0.1"
        ]
        
        print(f"Starting SUMO: {' '.join(sumo_cmd)}")
        
        # Start TraCI
        traci.start(sumo_cmd)
        print("✓ TraCI started successfully")
        
        # Test basic operations
        current_time = traci.simulation.getCurrentTime()
        print(f"✓ Current simulation time: {current_time}")
        
        # Get network information
        edges = traci.edge.getIDList()
        print(f"✓ Network has {len(edges)} edges")
        
        # Run a few simulation steps
        for step in range(5):
            traci.simulationStep()
            vehicles = traci.vehicle.getIDList()
            print(f"  Step {step+1}: {len(vehicles)} vehicles")
        
        print("✓ Basic TraCI operations working!")
        return True
        
    except Exception as e:
        print(f"✗ TraCI connection failed: {e}")
        return False
    finally:
        try:
            traci.close()
            print("✓ TraCI connection closed")
        except:
            pass

def test_gui_connection():
    """Test TraCI connection with SUMO-GUI"""
    print("\n=== Testing TraCI Connection with GUI ===")
    
    # Configuration
    SUMO_BINARY = "sumo-gui"
    SUMO_CONFIG = "unsignalized_intersection.sumocfg"
    SUMO_PORT = 8813
    
    try:
        # SUMO-GUI command
        sumo_cmd = [
            SUMO_BINARY,
            "-c", SUMO_CONFIG,
            "--quit-on-end",
            "--start",
            "--step-length", "0.1"
        ]
        
        print(f"Starting SUMO-GUI: {' '.join(sumo_cmd)}")
        print("Note: GUI window should open...")
        
        # Start TraCI
        traci.start(sumo_cmd)
        print("✓ TraCI with GUI started successfully")
        
        # Test basic operations
        current_time = traci.simulation.getCurrentTime()
        print(f"✓ Current simulation time: {current_time}")
        
        # Run a few steps
        for step in range(3):
            traci.simulationStep()
            vehicles = traci.vehicle.getIDList()
            print(f"  Step {step+1}: {len(vehicles)} vehicles")
            time.sleep(0.5)  # Slow down so we can see GUI
        
        print("✓ GUI TraCI operations working!")
        return True
        
    except Exception as e:
        print(f"✗ GUI TraCI connection failed: {e}")
        return False
    finally:
        try:
            traci.close()
            print("✓ TraCI connection closed")
        except:
            pass

if __name__ == "__main__":
    # Check if config file exists
    if not os.path.exists("unsignalized_intersection.sumocfg"):
        print("Error: Configuration file not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Test headless first
    if test_traci_connection():
        print("\n=== Connection Test Successful ===")
        print("You can now run the main simulation script.")
        
        # Ask if user wants to test GUI
        response = input("\nTest GUI connection? (y/n): ").lower().strip()
        if response == 'y':
            test_gui_connection()
    else:
        print("\n=== Connection Test Failed ===")
        print("Please check SUMO installation and configuration.")
